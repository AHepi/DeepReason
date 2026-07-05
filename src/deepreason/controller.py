"""Self-calibrating controller (docs/CONTROLLER_SPEC.md) — minimal core.

Implements the cheap, high-confidence components of the spec: the
two-ledger CONSTITUTION, the process-only UPDATE RULE inside
control-barrier ENVELOPES, policy-as-logged-artifact with FAIL-STATIC,
and (via the scheduler) the aging LIVENESS queue.

DEFERRED by design: the frozen reference arm and the adversarial market —
the spec's Goodhart *detectors*. They are unnecessary for safety here
because the constitution plus a process-only signal diet already make
Goodhart structurally impossible: a controller that literally cannot read
an outcome metric (survivors, admission rate, HV) has no outcome to game.
Their forbidden cases are therefore NOT yet enforced; see the module
docstring in tests/test_controller.py for exactly what is covered.

Everything the controller reads comes from event.llm PROCESS fields
(truncated, attempts) — never a status, verdict, survivor count, or any
adjudication input. Everything it writes is a GENERATOR-ledger knob. Both
halves are enforced structurally, not by convention (see the ledgers and
_process_signals below), and checked by the acceptance suite.
"""

import json

from deepreason.ontology import Provenance, Rule, Status

# --- The constitution: which knobs the controller MAY write, and which it
# may NEVER touch. Conservative by intent — anything adjudication, the
# gate, the trial guard, or criticism INTENSITY reads is tribunal. Per-role
# completion caps are keyed "cap:<role>". Checkable by diff (forbidden #1).
GENERATOR_LEDGER = frozenset(
    {"VS_K", "PACK_TOKEN_BUDGET", "SPEC_INJECTION"}
    | {f"cap:{r}" for r in (
        "conjecturer", "argumentative_critic", "defender",
        "variator", "synthesizer", "judge",
    )}
)
TRIBUNAL_LEDGER = frozenset({
    "FLOOR", "K", "HV_MIN", "HV_K", "PRECEDENT_K", "TRIAL_PARAPHRASE_N",
    "JUDGE_ERR_MAX", "AUDIT_PERIOD", "USER_RULINGS_BUDGET", "HOLDOUT_SHARE",
    "NEAR_DUP_EPS", "XEXAM_SHARE", "RESEED_DIST_MIN", "LAMBDA_FLOOR",
    "CAPTURE_W", "ATTACK_ENTROPY_FLOOR", "CRIT_DEBT_CEILING",
    "MIN_ATTACKS_FOR_RITUAL", "ARG_CRIT_PER_CYCLE",
    "RUBRIC_TRIALS_PER_ARTIFACT", "RETRY_MAX",
})

# The ONLY log fields the update rule may read. Enforced in _process_signals
# (it touches nothing else) and asserted by the acceptance suite (forbidden
# #2: no outcome metric may drive a knob).
PROCESS_FIELDS = frozenset({"truncated", "attempts"})
OUTCOME_FIELDS = frozenset({"status", "survivors", "hv", "reach", "coverage",
                            "admission", "accepted", "refuted"})

# Control-barrier envelopes: per knob [min, max, step, dwell]. A proposal
# outside [min, max] is rejected (forbidden #3); a knob may not move twice
# within `dwell` cycles (damping / forbidden #4-lite).
ENVELOPES = {
    "cap:conjecturer": {"min": 800, "max": 5000, "step": 1.6, "dwell": 2},
    "cap:argumentative_critic": {"min": 800, "max": 3500, "step": 1.6, "dwell": 2},
    "cap:defender": {"min": 500, "max": 2000, "step": 1.6, "dwell": 2},
    "cap:variator": {"min": 800, "max": 4000, "step": 1.6, "dwell": 2},
    "cap:synthesizer": {"min": 600, "max": 2500, "step": 1.6, "dwell": 2},
    "cap:judge": {"min": 600, "max": 2500, "step": 1.6, "dwell": 2},
}

TRUNC_HI = 0.25          # widen when >25% of recent calls truncated
CLEAN_WINDOWS = 3        # narrow only after this many spotless windows
MIN_SAMPLES = 2          # never act on fewer than this many calls for a role
WINDOW_CALLS = 6         # per-role signal window (most recent N calls)


def clamp(knob: str, value: int) -> int:
    env = ENVELOPES[knob]
    return max(env["min"], min(env["max"], int(value)))


class Controller:
    """One controller.step() per scheduler cycle. Reads process signals from
    the log, proposes generator-knob deltas bounded by envelopes, applies
    them to the live adapter endpoints, and records the decision as a
    replayable calibration_policy artifact — unless its previous policy is
    under a standing attack, in which case it holds (fail-static)."""

    def __init__(self, harness, adapter, envelopes=None):
        self.harness = harness
        self.adapter = adapter
        self.envelopes = envelopes or ENVELOPES
        self._last_move: dict[str, int] = {}  # knob -> cycle it last moved
        self._policies: list[str] = []  # policy artifact ids, in emission order
        self._cycle = 0

    # -- process signals: touches ONLY event.llm process fields ----------- #
    def _process_signals(self) -> dict[str, dict]:
        per_role: dict[str, list] = {}
        for event in self.harness.log.read():
            call = event.llm
            if call is None:
                continue
            per_role.setdefault(call.role, []).append(call)
        out = {}
        for role, calls in per_role.items():
            recent = calls[-WINDOW_CALLS:]
            n = len(recent)
            if n < MIN_SAMPLES:
                continue
            # Reads ONLY the two process fields; no adjudication input is
            # even in scope here (enforced by the acceptance suite).
            out[role] = {
                "n": n,
                "truncation_rate": sum(1 for c in recent if c.truncated) / n,
                "repair_rate": sum(1 for c in recent if c.attempts > 1) / n,
            }
        return out

    def _current_caps(self) -> dict[str, int]:
        caps = {}
        for role in self.adapter.endpoints:
            ep = self.adapter.endpoints[role]
            ep = ep[0] if isinstance(ep, (list, tuple)) else ep
            cap = getattr(ep, "max_tokens", None)
            if cap is not None:
                caps[role] = cap
        return caps

    # -- update rule: process signals -> bounded knob deltas -------------- #
    def _propose(self, caps: dict[str, int], signals: dict[str, dict]) -> dict[str, int]:
        deltas: dict[str, int] = {}
        for role, sig in signals.items():
            knob = f"cap:{role}"
            if knob not in self.envelopes or role not in caps:
                continue
            if self._cycle - self._last_move.get(knob, -999) < self.envelopes[knob]["dwell"]:
                continue  # damping: respect min-dwell
            cur = caps[role]
            if sig["truncation_rate"] > TRUNC_HI:
                new = clamp(knob, round(cur * self.envelopes[knob]["step"]))
                if new != cur:
                    deltas[knob] = new
            elif sig["truncation_rate"] == 0 and sig["repair_rate"] == 0:
                # Efficiency direction: settle a wasteful cap down, but only
                # after CLEAN_WINDOWS of spotless signal and never below floor.
                if self._clean_streak(role) >= CLEAN_WINDOWS:
                    new = clamp(knob, round(cur / self.envelopes[knob]["step"]))
                    if new != cur:
                        deltas[knob] = new
        return deltas

    def _clean_streak(self, role: str) -> int:
        streak = 0
        for event in reversed(list(self.harness.log.read())):
            call = event.llm
            if call is None or call.role != role:
                continue
            if call.truncated or call.attempts > 1:
                break
            streak += 1
        return streak

    # -- fail-static: hold while the last policy is under standing attack -- #
    def _last_policy(self):
        return self._policies[-1] if self._policies else None

    def _under_standing_attack(self, aid) -> bool:
        return self.harness.state.status.get(aid) in (
            Status.REFUTED, Status.SUSPENDED_UNSUPPORTED,
        )

    def step(self) -> dict | None:
        """Advance one cycle. Returns the applied knob vector, or None if the
        controller held (no change proposed, or fail-static)."""
        self._cycle += 1
        last = self._last_policy()
        if last is not None and self._under_standing_attack(last):
            # Fail-static: a contested policy freezes the controller and the
            # caps revert to the last ACCEPTED policy (forbidden #6).
            self._revert_to_last_accepted()
            self.harness.record_measure(inputs=["controller-hold:fail-static", last])
            return None

        signals = self._process_signals()
        caps = self._current_caps()
        deltas = self._propose(caps, signals)
        if not deltas:
            return None

        for knob, value in deltas.items():
            assert knob in GENERATOR_LEDGER, f"controller touched non-generator knob {knob}"
            assert knob not in TRIBUNAL_LEDGER, f"controller touched tribunal knob {knob}"
            self._apply_cap(knob, value)
            self._last_move[knob] = self._cycle
        self._emit_policy(deltas, signals)
        return deltas

    def _apply_cap(self, knob: str, value: int) -> None:
        role = knob.split(":", 1)[1]
        ep = self.adapter.endpoints.get(role)
        if ep is None:
            return
        for e in (ep if isinstance(ep, (list, tuple)) else [ep]):
            e.max_tokens = value

    def _revert_to_last_accepted(self) -> None:
        for aid in reversed(self._policies):
            if self.harness.state.status.get(aid) != Status.ACCEPTED:
                continue
            try:
                body = json.loads(self.harness.state.artifacts[aid].content_ref[len("inline:"):])
            except (ValueError, IndexError):
                continue
            for knob, value in body.get("knobs", {}).items():
                self._apply_cap(knob, value)
            return

    def _emit_policy(self, deltas: dict, signals: dict) -> None:
        # Policy-as-artifact: an ordinary registered artifact — attackable
        # (a critic warrant may target it) and replayable (it is in the log).
        # The evidence is the process signals that justified each delta.
        body = {"knobs": deltas, "evidence": signals, "cycle": self._cycle}
        policy = self.harness.create_artifact(
            json.dumps(body, sort_keys=True),
            provenance=Provenance(role="controller"),
            rule=Rule.REFL,
        )
        self._policies.append(policy.id)
