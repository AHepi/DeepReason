"""Self-calibrating controller (docs/CONTROLLER_SPEC.md) — minimal core.

This is FIXED, deterministic policy execution — an implementation detail
of scheduler rules (spec §11.4: logged rules with hysteresis; a learned
controller is explicitly out of scope). Nothing here invokes an LLM,
learns during the run, or holds epistemic state: every decision is a pure
function of the log prefix and the constants below (thresholds, envelopes,
dwell), and every applied decision is itself a logged, attackable,
replayable artifact.

It is also conceptually SEPARATE from capture control (capture/): capture
watches the epistemic dynamics (generator and adjudicator surfaces); this
module watches process health (truncation, schema repair, transport). The
timeout rule below is a TRANSPORT-POLICY rule, not a capture response.

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
    {"VS_K", "PACK_TOKEN_BUDGET", "SPEC_INJECTION", "timeout:transport"}
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
    # TRANSPORT-POLICY rule (not capture): read timeout, seconds, applied
    # to every endpoint (drop events carry no role). Deterministic and
    # bounded: threshold = any fresh transport drop, step/dwell/min/max
    # fixed here, inputs replayable from the log. Widen-only in practice —
    # an unused wide timeout costs nothing, and the live failure it
    # addresses (generations outlasting a fixed wait, dropped after
    # retries) recurs until the wait is widened.
    "timeout:transport": {"min": 120, "max": 900, "step": 1.5, "dwell": 2},
}

# Transport-drop signal (process-only): the drop site (scheduler._drop)
# tags a Measure event "dropped-call" with the transport reason. A dropped
# call is process degradation upstream of all adjudication — reading its
# tag admits no outcome metric. Budget-exhaustion drops are excluded by
# the reason match.
TRANSPORT_DROP_TAG = "dropped-call"
TRANSPORT_REASONS = ("timed out", "timeout", "transport failed")

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
        self._drops_seen = 0  # transport-drop events already consumed
        self._rehydrate_process_state()

    def _policy_payload(self, artifact_id: str) -> dict | None:
        artifact = self.harness.state.artifacts.get(artifact_id)
        if (
            artifact is None
            or artifact.provenance.role.value != "controller"
            or not artifact.content_ref.startswith("inline:")
        ):
            return None
        try:
            body = json.loads(artifact.content_ref[len("inline:"):])
        except (TypeError, ValueError):
            return None
        if not isinstance(body, dict) or not isinstance(body.get("knobs"), dict):
            return None
        return body

    def _validated_policy_knobs(self, body: dict) -> dict[str, int]:
        knobs: dict[str, int] = {}
        for knob, value in body.get("knobs", {}).items():
            if knob not in GENERATOR_LEDGER or knob not in self.envelopes:
                continue
            if type(value) is not int:  # bool is not a transport limit
                continue
            envelope = self.envelopes[knob]
            if envelope["min"] <= value <= envelope["max"]:
                knobs[knob] = value
        return knobs

    def _knob_needs_apply(self, knob: str, value: int) -> bool:
        if knob == "timeout:transport":
            endpoints = [
                endpoint
                for entry in self.adapter.endpoints.values()
                for endpoint in (
                    entry if isinstance(entry, (list, tuple)) else [entry]
                )
            ]
            return any(
                hasattr(endpoint, "timeout_s")
                and endpoint.timeout_s != value
                for endpoint in endpoints
            )
        role = knob.split(":", 1)[1]
        entry = self.adapter.endpoints.get(role)
        if entry is None:
            return False
        endpoints = entry if isinstance(entry, (list, tuple)) else [entry]
        return any(getattr(endpoint, "max_tokens", None) != value for endpoint in endpoints)

    def _rehydrate_process_state(self) -> None:
        """Restore only logged, accepted controller process state on resume."""
        events = list(self.harness.log.read())
        self._drops_seen = sum(
            int(bool(event.inputs) and event.inputs[0] == TRANSPORT_DROP_TAG)
            for event in events
        )
        for event in events:
            if event.rule != Rule.REFL:
                continue
            for artifact_id in event.outputs:
                body = self._policy_payload(artifact_id)
                if body is None:
                    continue
                self._policies.append(artifact_id)
                cycle = body.get("cycle")
                if type(cycle) is not int or cycle < 0:
                    continue
                self._cycle = max(self._cycle, cycle)
                for knob in self._validated_policy_knobs(body):
                    self._last_move[knob] = max(
                        self._last_move.get(knob, -999), cycle
                    )

        accepted = next(
            (
                artifact_id
                for artifact_id in reversed(self._policies)
                if self.harness.state.status.get(artifact_id) == Status.ACCEPTED
            ),
            None,
        )
        if accepted is None:
            return
        body = self._policy_payload(accepted)
        if body is None:
            return
        changed: dict[str, int] = {}
        for knob, value in self._validated_policy_knobs(body).items():
            if self._knob_needs_apply(knob, value):
                self._apply_cap(knob, value)
                changed[knob] = value
        if changed:
            self.harness.record_measure(inputs=[
                "controller-rehydration",
                accepted,
                json.dumps(changed, sort_keys=True, separators=(",", ":")),
            ])

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
            envelope = self.envelopes[knob]
            # A compiled route may intentionally start outside this legacy
            # controller's safe envelope (for example a 7k compact website
            # cap).  The controller has no authority to normalize such a
            # setting; treating a truncation signal as a clamped 5k update
            # would perversely *shrink* it. Hold the explicit setting.
            if not envelope["min"] <= cur <= envelope["max"]:
                continue
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

    def _new_transport_drops(self) -> int:
        """Count transport-layer dropped calls not yet consumed by a prior
        step. Reads only the drop tag + reason the drop site wrote — a
        process signal (the call produced nothing to adjudicate)."""
        fresh = 0
        total = 0
        for event in self.harness.log.read():
            inputs = event.inputs or []
            if not inputs or inputs[0] != TRANSPORT_DROP_TAG:
                continue
            total += 1
            reason = inputs[1] if len(inputs) > 1 else ""
            if total > self._drops_seen and any(m in reason for m in TRANSPORT_REASONS):
                fresh += 1
        self._drops_seen = total
        return fresh

    def _current_timeout(self) -> int | None:
        for entry in self.adapter.endpoints.values():
            for e in (entry if isinstance(entry, (list, tuple)) else [entry]):
                t = getattr(e, "timeout_s", None)
                if t is not None:
                    return t
        return None

    def _propose_timeout(self, deltas: dict[str, int], evidence: dict) -> None:
        """Fresh transport drops -> widen the read timeout one envelope
        step. The signal is drop events, not truncation: a generation that
        outlasts the wait dies with no llm record at all."""
        knob = "timeout:transport"
        drops = self._new_transport_drops()
        if not drops:
            return
        evidence["transport"] = {"new_drops": drops}
        if self._cycle - self._last_move.get(knob, -999) < self.envelopes.get(
            knob, ENVELOPES[knob]
        )["dwell"]:
            return
        cur = self._current_timeout()
        if cur is None:
            return
        new = clamp(knob, round(cur * ENVELOPES[knob]["step"]))
        if new != cur:
            deltas[knob] = new

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
        evidence = dict(signals)
        self._propose_timeout(deltas, evidence)
        if not deltas:
            return None

        for knob, value in deltas.items():
            assert knob in GENERATOR_LEDGER, f"controller touched non-generator knob {knob}"
            assert knob not in TRIBUNAL_LEDGER, f"controller touched tribunal knob {knob}"
            self._apply_cap(knob, value)
            self._last_move[knob] = self._cycle
        self._emit_policy(deltas, evidence)
        return deltas

    def _apply_cap(self, knob: str, value: int) -> None:
        if knob == "timeout:transport":
            # Drop events carry no role, so the wait widens everywhere.
            for entry in self.adapter.endpoints.values():
                for e in (entry if isinstance(entry, (list, tuple)) else [entry]):
                    if hasattr(e, "timeout_s"):
                        e.timeout_s = value
            return
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
            body = self._policy_payload(aid)
            if body is None:
                continue
            for knob, value in self._validated_policy_knobs(body).items():
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
