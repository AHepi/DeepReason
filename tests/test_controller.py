"""Acceptance suite for the self-calibration controller (docs/
CONTROLLER_SPEC.md). Each test is one of the design's own forbidden cases
turned into a check that tries to make the bad behavior happen and fails
if it can.

Covered here (the MINIMAL controller): forbidden cases
  #1 no tribunal-ledger knob is writable by the controller,
  #2 the update rule reads no outcome metric,
  #3 no knob update escapes its control-barrier envelope,
  #5 no registered problem starves under the liveness queue,
  #6 fail-static: no new policy while the previous is under standing attack,
  #7 controller decisions are deterministic from the log (replay-stable).
NOT covered (deferred with the reference arm / market): #4 (reference-arm
divergence detection). Its absence is intentional and documented — the
process-only diet makes the Goodhart loop it guards against structurally
impossible in this build.
"""

import inspect
import json

from deepreason.config import Config
from deepreason.controller import (
    GENERATOR_LEDGER,
    OUTCOME_FIELDS,
    TRIBUNAL_LEDGER,
    Controller,
)
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.scheduler.scheduler import Scheduler


class _CapEndpoint:
    """An endpoint that reports finish_reason 'length' until its cap crosses
    `needs`, then returns a valid one-candidate conjecture. Models the real
    truncation-then-recovery the controller is meant to fix."""

    def __init__(self, needs: int):
        self.needs = needs
        self.name = "cap"
        self.model = "cap"
        self.max_tokens = 800
        self.last_finish_reason = None
        self.last_usage = None
        self.last_mean_surprisal = None

    def complete(self, prompt: str) -> str:
        if (self.max_tokens or 0) < self.needs:
            self.last_finish_reason = "length"
            self.last_usage = {"prompt_tokens": 50, "completion_tokens": self.max_tokens or 0}
            return '{"candidates": [{"content": "moon truncat'  # cut off
        self.last_finish_reason = "stop"
        self.last_usage = {"prompt_tokens": 50, "completion_tokens": 200}
        return json.dumps({"candidates": [{"content": "the moon pulls", "typicality": 0.9}]})


def _harness_with_problem(tmp_path) -> Harness:
    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    h.register_problem(
        Problem(
            id="pi-tides", description="explain the tides", criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    return h


# --- #1: the constitution partitions the knobs; ledgers are disjoint ---- #
def test_forbidden1_ledgers_are_disjoint_and_tribunal_is_untouchable():
    assert GENERATOR_LEDGER.isdisjoint(TRIBUNAL_LEDGER)
    # Everything the guard/gate/adjudication reads must be tribunal-side.
    for knob in ("TRIAL_PARAPHRASE_N", "AUDIT_PERIOD", "JUDGE_ERR_MAX",
                 "NEAR_DUP_EPS", "ARG_CRIT_PER_CYCLE", "RETRY_MAX"):
        assert knob in TRIBUNAL_LEDGER and knob not in GENERATOR_LEDGER


def test_forbidden1_apply_only_ever_touches_generator_caps(tmp_path):
    h = _harness_with_problem(tmp_path)
    adapter = LLMAdapter({"conjecturer": _CapEndpoint(needs=1500)}, h.blobs)
    c = Controller(h, adapter)
    # The apply path asserts membership; drive a real widen and confirm the
    # knob it moved is generator-ledger.
    c._cycle = 5
    c._apply_cap("cap:conjecturer", 2000)
    assert adapter.endpoints["conjecturer"].max_tokens == 2000
    assert "cap:conjecturer" in GENERATOR_LEDGER


# --- #2: the update rule reads no outcome metric ------------------------ #
def test_forbidden2_signal_reader_touches_no_outcome_field():
    src = inspect.getsource(Controller._process_signals)
    for banned in OUTCOME_FIELDS:
        assert banned not in src, f"_process_signals references outcome field {banned!r}"
    # It reads the log's llm records and only the process fields.
    assert ".truncated" in src and ".attempts" in src
    assert "status" not in src and "survivors" not in src


# --- #3: no knob update escapes its envelope ---------------------------- #
def test_forbidden3_widen_is_clamped_to_envelope_max(tmp_path):
    h = _harness_with_problem(tmp_path)
    ep = _CapEndpoint(needs=99999)  # always truncates -> controller keeps widening
    adapter = LLMAdapter({"conjecturer": ep}, h.blobs)
    c = Controller(h, adapter)
    from deepreason.controller import ENVELOPES
    cap_max = ENVELOPES["cap:conjecturer"]["max"]
    # Simulate many truncated calls and repeated controller steps.
    for _ in range(40):
        ep.complete("p")  # this alone doesn't log; drive through the adapter instead
    for cycle in range(20):
        # log a truncated conjecturer call each cycle
        h.record_measure(inputs=["tick"])  # advance seq deterministically
        from deepreason.ontology.event import LLMCall
        h._commit(  # low-level: append a Conj-like event carrying a truncated call
            __import__("deepreason.ontology", fromlist=["Rule"]).Rule.CONJ,
            inputs=["pi-tides"], outputs=[],
            llm=LLMCall(role="conjecturer", model="m", endpoint="e",
                        prompt_ref="inline:p", raw_ref="inline:r",
                        tokens=10, attempts=1, truncated=True),
        )
        c.step()
    assert ep.max_tokens <= cap_max, "controller widened a cap past its envelope max"
    assert ep.max_tokens > 800, "controller never widened despite persistent truncation"


def test_controller_does_not_normalize_an_explicit_cap_outside_its_envelope(tmp_path):
    h = _harness_with_problem(tmp_path)
    ep = _CapEndpoint(needs=99999)
    ep.max_tokens = 7000  # an explicit compiled website-route cap
    adapter = LLMAdapter({"conjecturer": ep}, h.blobs)
    c = Controller(h, adapter)
    from deepreason.ontology import Rule
    from deepreason.ontology.event import LLMCall

    for _ in range(2):
        h._commit(
            Rule.CONJ,
            inputs=["pi-tides"],
            outputs=[],
            llm=LLMCall(
                role="conjecturer", model="m", endpoint="e",
                prompt_ref="inline:p", raw_ref="inline:r", truncated=True,
            ),
        )

    assert c.step() is None
    assert ep.max_tokens == 7000
    assert not any(
        event.inputs and event.inputs[0] == "controller-update"
        for event in h.log.read()
    )


# --- #5: liveness — no registered problem starves ---------------------- #
def test_forbidden5_liveness_queue_starves_no_problem(tmp_path):
    h = Harness(tmp_path / "run")
    h.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    for i in range(4):
        h.register_problem(Problem(
            id=f"pi-{i}", description=f"problem {i}", criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        ))
    config = Config(LIVENESS_QUEUE=True, N_SCHOOLS=0)
    adapter = LLMAdapter({}, h.blobs)  # no conjecturer -> selection only
    sched = Scheduler(h, adapter, config)
    picked = set()
    for cyc in range(12):
        sched._cycles = cyc
        p = sched._select_problem()
        if p is not None:
            picked.add(p.id)
    assert picked == {"pi-0", "pi-1", "pi-2", "pi-3"}, f"a problem starved: {picked}"


# --- #6: fail-static — no policy while the last is under standing attack - #
def test_forbidden6_fail_static_holds_under_standing_attack(tmp_path):
    from deepreason.ontology import Provenance, Rule, Warrant, WarrantType

    h = _harness_with_problem(tmp_path)
    ep = _CapEndpoint(needs=99999)
    adapter = LLMAdapter({"conjecturer": ep}, h.blobs)
    c = Controller(h, adapter)
    # Emit one real policy by driving a truncated cycle.
    from deepreason.ontology.event import LLMCall
    h._commit(Rule.CONJ, inputs=["pi-tides"], outputs=[],
              llm=LLMCall(role="conjecturer", model="m", endpoint="e",
                          prompt_ref="inline:p", raw_ref="inline:r", truncated=True))
    h._commit(Rule.CONJ, inputs=["pi-tides"], outputs=[],
              llm=LLMCall(role="conjecturer", model="m", endpoint="e",
                          prompt_ref="inline:p", raw_ref="inline:r", truncated=True))
    c.step()
    policy = c._last_policy()
    assert policy is not None
    n_policies_before = sum(1 for a in h.state.artifacts.values()
                            if a.provenance.role.value == "controller"
                            and a.content_ref.startswith("inline:{"))
    # Attack the policy artifact itself: a critic warrant targeting it, with
    # its own accepted validity node -> the policy goes refuted.
    attack_nu = h.create_artifact("nu: the attack on the policy is sound",
                                  provenance=Provenance(role="critic"))
    h.create_artifact(
        "critic: this policy's signal reading is unsound",
        provenance=Provenance(role="critic"),
        warrants=[Warrant(id="w:attack:policy", target=policy,
                          type=WarrantType.ARGUMENTATIVE, validity_node=attack_nu.id)],
        rule=Rule.CRIT,
    )
    assert c._under_standing_attack(policy)
    result = c.step()  # must HOLD
    assert result is None
    n_policies_after = sum(1 for a in h.state.artifacts.values()
                           if a.provenance.role.value == "controller"
                           and a.content_ref.startswith("inline:{"))
    assert n_policies_after == n_policies_before, "emitted a policy while under attack"


def test_resume_rehydrates_only_latest_accepted_controller_policy(tmp_path):
    from deepreason.ontology import Provenance, Rule, Warrant, WarrantType

    h = _harness_with_problem(tmp_path)
    original_endpoint = _CapEndpoint(needs=99999)
    original = Controller(
        h, LLMAdapter({"conjecturer": original_endpoint}, h.blobs)
    )
    original._cycle = 1
    original._emit_policy({"cap:conjecturer": 1280}, {"test": "accepted"})
    accepted_policy = original._last_policy()
    original._cycle = 2
    original._emit_policy({"cap:conjecturer": 2048}, {"test": "refuted"})
    refuted_policy = original._last_policy()
    assert accepted_policy is not None and refuted_policy is not None

    attack_nu = h.create_artifact(
        "nu: the newer process policy is unsound",
        provenance=Provenance(role="critic"),
    )
    h.create_artifact(
        "critic: reject the newer policy",
        provenance=Provenance(role="critic"),
        warrants=[Warrant(
            id="w:attack:resume-policy",
            target=refuted_policy,
            type=WarrantType.ARGUMENTATIVE,
            validity_node=attack_nu.id,
        )],
        rule=Rule.CRIT,
    )

    resumed_endpoint = _CapEndpoint(needs=99999)
    resumed = Controller(
        Harness(h.root),
        LLMAdapter({"conjecturer": resumed_endpoint}, h.blobs),
    )

    assert resumed_endpoint.max_tokens == 1280
    assert resumed._last_policy() == refuted_policy
    rehydrations = [
        event for event in Harness(h.root).log.read()
        if event.inputs and event.inputs[0] == "controller-rehydration"
    ]
    assert len(rehydrations) == 1
    assert rehydrations[0].inputs[1] == accepted_policy


# --- #7: controller decisions are deterministic from the log ------------ #
def test_forbidden7_decisions_replay_stable(tmp_path):
    def run(root):
        h = Harness(root)
        h.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
        h.register_problem(Problem(
            id="pi-tides", description="explain the tides", criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        ))
        ep = _CapEndpoint(needs=1500)
        adapter = LLMAdapter({"conjecturer": ep}, h.blobs)
        c = Controller(h, adapter)
        from deepreason.ontology.event import LLMCall
        from deepreason.ontology import Rule
        proposals = []
        for _ in range(8):
            h._commit(Rule.CONJ, inputs=["pi-tides"], outputs=[],
                      llm=LLMCall(role="conjecturer", model="m", endpoint="e",
                                  prompt_ref="inline:p", raw_ref="inline:r",
                                  truncated=(ep.max_tokens or 0) < 1500))
            proposals.append(c.step())
            if ep.max_tokens and ep.max_tokens >= 1500:
                ep.last_finish_reason = "stop"
        return proposals

    a = run(tmp_path / "a")
    b = run(tmp_path / "b")
    assert a == b, f"controller decisions not deterministic: {a} vs {b}"
    assert any(p for p in a), "controller never acted in the determinism test"


# --- transport policy: deterministic, bounded, separate from capture ---- #
class _TimeoutEndpoint:
    def __init__(self, timeout_s: int = 300):
        self.name = "t"
        self.model = "t"
        self.max_tokens = None
        self.timeout_s = timeout_s


def _drop(h, reason):
    h.record_measure(inputs=["dropped-call", reason])


def test_transport_drops_widen_timeout_within_envelope_and_dwell(tmp_path):
    """The transport-policy rule: fresh transport drops -> one envelope
    step wider read timeout, honoring dwell and the hard max. Inputs are
    log events only — deterministic and replayable."""
    from deepreason.controller import ENVELOPES

    h = _harness_with_problem(tmp_path)
    ep = _TimeoutEndpoint(timeout_s=300)
    adapter = LLMAdapter({"conjecturer": ep}, h.blobs)
    c = Controller(h, adapter)

    _drop(h, "no complete response within escalated read timeouts (300s, 600s)")
    assert c.step() == {"timeout:transport": 450}
    assert ep.timeout_s == 450

    # Dwell: another drop on the very next cycle must NOT move the knob.
    _drop(h, "transport failed after retries: The read operation timed out")
    assert c.step() is None
    assert ep.timeout_s == 450

    # After the dwell passes, a fresh drop widens again; the envelope max
    # (900) is a hard bound.
    _drop(h, "transport failed after retries: The read operation timed out")
    assert c.step() == {"timeout:transport": 675}
    _drop(h, "transport failed after retries: The read operation timed out")
    c.step()
    _drop(h, "transport failed after retries: The read operation timed out")
    result = c.step()
    assert ep.timeout_s <= ENVELOPES["timeout:transport"]["max"]
    if result:
        assert result["timeout:transport"] <= 900


def test_non_transport_drops_do_not_move_the_timeout(tmp_path):
    """Budget-exhaustion drops share the dropped-call tag but are not
    transport failures: the timeout knob must not react to them. And with
    no drops at all, the knob never moves."""
    h = _harness_with_problem(tmp_path)
    ep = _TimeoutEndpoint(timeout_s=300)
    adapter = LLMAdapter({"conjecturer": ep}, h.blobs)
    c = Controller(h, adapter)
    _drop(h, "token budget exceeded: 100000 spent")
    assert c.step() is None
    assert ep.timeout_s == 300
    assert c.step() is None
    assert ep.timeout_s == 300


def test_transport_policy_decisions_replay_stable(tmp_path):
    """Forbidden #7 extended to the transport rule: same log prefix, same
    knob decisions, byte-for-byte."""
    def run(root):
        h = Harness(root)
        h.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
        h.register_problem(Problem(
            id="pi-tides", description="explain the tides", criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        ))
        ep = _TimeoutEndpoint(timeout_s=300)
        adapter = LLMAdapter({"conjecturer": ep}, h.blobs)
        c = Controller(h, adapter)
        proposals = []
        for i in range(6):
            if i % 2 == 0:
                _drop(h, "transport failed after retries: timed out")
            proposals.append(c.step())
        return proposals, ep.timeout_s

    a = run(tmp_path / "a")
    b = run(tmp_path / "b")
    assert a == b


def test_run_scheduler_wires_controller_by_default(tmp_path, monkeypatch):
    """ops.run_scheduler (the CLI/MCP/make path) builds the deterministic
    controller unless config explicitly opts out — live tuning must not
    depend on a research-script flag."""
    import deepreason.scheduler.scheduler as sched_mod
    from deepreason import ops

    seen = {}

    class _FakeScheduler:
        def __init__(self, harness, adapter, config, embedder=None,
                     browser_backend=None, controller=None,
                     research_backend=None, workload_profile=None,
                     run_manifest=None, stop_controller=None,
                     progress_sink=None):
            seen["controller"] = controller

        def run(self, cycles, on_cycle=None):
            return {"survivors": []}

    monkeypatch.setattr(sched_mod, "Scheduler", _FakeScheduler)
    roles = {"conjecturer": {"endpoint": "https://example.invalid", "model": "m"}}

    h = _harness_with_problem(tmp_path / "a")
    ops.run_scheduler(h, Config(roles=roles), cycles=0)
    assert isinstance(seen["controller"], Controller)

    h2 = _harness_with_problem(tmp_path / "b")
    ops.run_scheduler(h2, Config(CONTROLLER=False, roles=roles), cycles=0)
    assert seen["controller"] is None
