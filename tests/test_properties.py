"""Proposed properties (rules/experiment.py): the system conjectures its own
ground truth — held accountable at four layers: checker_wf (mechanical
non-vacuity), the cross-family relevance trial (unanimity on 'does it follow
from the problem statement?'), the population wipeout guard at use time, and
the source-artifact att closure (refute the property => every verdict it
minted collapses and its victims reinstate)."""

import json

from tests.conftest import attack

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
    WarrantType,
)
from deepreason.oracle import (
    check_checker,
    checker_wf_commitment,
    property_oracle_commitment,
)
from deepreason.rules.crit import crit_fuzz
from deepreason.rules.experiment import active_properties, propose_properties
from deepreason.scheduler.scheduler import Scheduler

# The DELIBERATELY WEAK spec checker: permutation only — the problem statement
# demands ascending order, but nothing enforces it. This is the gap the
# property designer must close.
WEAK_CHECKER = (
    "def check(inp, out):\n"
    "    xs = inp[0]\n"
    "    return isinstance(out, list) and sorted(out) == sorted(xs)\n"
)
GATE = (
    "def valid(inp):\n"
    "    if not isinstance(inp, list) or len(inp) != 1:\n"
    "        return False\n"
    "    xs = inp[0]\n"
    "    if not isinstance(xs, list) or len(xs) > 20:\n"
    "        return False\n"
    "    for x in xs:\n"
    "        if not isinstance(x, int):\n"
    "            return False\n"
    "    return True\n"
)
FROZEN = [[[3, 1, 2]]]
DESCRIPTION = (
    "Return the input list of ints in ascending order. Every element of the "
    "input must appear in the output exactly once."
)
# The trap: a valid permutation (passes the weak spec checker on EVERY input,
# frozen or fuzzed) that ignores the problem's ordering requirement entirely.
TRAP = "def solve(xs):\n    return xs\n"
CORRECT = "def solve(xs):\n    return sorted(xs)\n"

ASCENDING_CLAIM = "the output must be in ascending order"
ASCENDING_CHECKER = (
    "def check(inp, out):\n"
    "    xs = inp[0]\n"
    "    if not isinstance(out, list) or sorted(out) != sorted(xs):\n"
    "        return False\n"
    "    for i in range(len(out) - 1):\n"
    "        if out[i] > out[i + 1]:\n"
    "            return False\n"
    "    return True\n"
)
VACUOUS_CHECKER = "def check(inp, out):\n    return True\n"

PASS_RULING = json.dumps({"verdict": "pass", "decisive_point": "ascending order"})
FAIL_RULING = json.dumps(
    {"verdict": "fail", "decisive_point": "ascending order"}
)


def _base():
    return property_oracle_commitment("solve", FROZEN, WEAK_CHECKER, GATE)


def _problem(harness, base):
    problem = Problem(
        id="pi-sort",
        description=DESCRIPTION,
        criteria=[base.id],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    )
    return harness.register_problem(problem)


def _candidate(harness, base, source):
    return harness.create_artifact(
        source, codec="code:python",
        interface=Interface(commitments=[base.id]),
        provenance=Provenance(role="conjecturer"),
    )


def _designer_adapter(harness, proposals, judge1, judge2):
    return LLMAdapter(
        {
            "property_designer": MockEndpoint(
                [json.dumps({"properties": proposals})]
            ),
            "judge": [
                MockEndpoint(
                    judge1, name="mock://judge-gemma", model="gemma-test"
                ),
                MockEndpoint(
                    judge2, name="mock://judge-qwen", model="qwen-test"
                ),
            ],
        },
        harness.blobs,
        retry_max=2,
    )


# ---- checker_wf: mechanical admission ----

def test_check_checker_accepts_real_and_rejects_vacuous_and_broken():
    assert check_checker(ASCENDING_CHECKER, FROZEN)[0] == "pass"
    v, d = check_checker(VACUOUS_CHECKER, FROZEN)
    assert v == "fail" and "vacuous" in d["error"]
    assert check_checker("import os", FROZEN)[0] == "fail"


def test_check_checker_rejects_truncated_always_raising_code():
    # The live failure: the designer's token window cut the checker mid-code.
    # `return o` parses but raises NameError unconditionally — under
    # raise=reject alone it would count as non-vacuous and then 'violate'
    # every candidate ever written (the wipeout guard quarantined all 10 kill
    # attempts). A checker must DECIDE at least once, not just crash.
    truncated = "def check(inp, out):\n    return o\n"
    v, d = check_checker(truncated, FROZEN)
    assert v == "fail" and "broken checker" in d["error"]


def test_checker_wf_commitment_derived_and_stable():
    base = _base()
    wf = checker_wf_commitment(base)
    assert wf is not None and wf.id.startswith("chk-wf@")
    assert wf.id == checker_wf_commitment(base).id


# ---- proposal pipeline: mechanical + trial adjudication on arrival ----

def test_propose_activates_trial_passed_and_refutes_vacuous(harness):
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    adapter = _designer_adapter(
        harness,
        [{"claim": ASCENDING_CLAIM, "checker": ASCENDING_CHECKER},
         {"claim": "anything goes", "checker": VACUOUS_CHECKER}],
        [PASS_RULING], [PASS_RULING],
    )
    activated = propose_properties(harness, base, problem, adapter, Config())
    assert len(activated) == 1
    props = active_properties(harness, base.id)
    assert len(props) == 1 and props[0][1] == ASCENDING_CLAIM
    # The vacuous one is REFUTED mechanically (demonstrative chk-wf warrant).
    refuted = [
        a for a in harness.state.artifacts.values()
        if a.codec == "code:python-prop"
        and harness.state.status[a.id] == Status.REFUTED
    ]
    assert len(refuted) == 1
    w = next(w for w in harness.warrants.values() if w.target == refuted[0].id)
    assert w.type == WarrantType.DEMONSTRATIVE
    assert w.commitment.startswith("chk-wf@")


def test_relevance_trial_unanimity_required(harness):
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    # Judge seat 2 rules the property does NOT follow: no activation, and the
    # located fail ruling registers an attackable case against the property.
    adapter = _designer_adapter(
        harness,
        [{"claim": ASCENDING_CLAIM, "checker": ASCENDING_CHECKER}],
        [PASS_RULING], [FAIL_RULING],
    )
    activated = propose_properties(harness, base, problem, adapter, Config())
    assert activated == []
    assert active_properties(harness, base.id) == []
    prop = next(
        a for a in harness.state.artifacts.values() if a.codec == "code:python-prop"
    )
    assert harness.state.status[prop.id] == Status.REFUTED
    w = next(w for w in harness.warrants.values() if w.target == prop.id)
    assert w.type == WarrantType.ARGUMENTATIVE  # a judged case, attackable nu


# ---- use: the conjectured property refutes the trap, with the safety net ----

def _activated_property(harness, base, problem):
    adapter = _designer_adapter(
        harness,
        [{"claim": ASCENDING_CLAIM, "checker": ASCENDING_CHECKER}],
        [PASS_RULING], [PASS_RULING],
    )
    activated = propose_properties(harness, base, problem, adapter, Config())
    assert len(activated) == 1
    return activated[0]


def test_property_refutes_trap_and_spares_correct_candidate(harness):
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    trap = _candidate(harness, base, TRAP)
    good = _candidate(harness, base, CORRECT)
    assert crit_fuzz(harness, trap.id, Config()) is None  # weak spec: blind
    prop = _activated_property(harness, base, problem)

    critic = crit_fuzz(harness, trap.id, Config())
    assert critic is not None
    assert harness.state.status[trap.id] == Status.REFUTED
    assert harness.state.status[good.id] == Status.ACCEPTED
    assert crit_fuzz(harness, good.id, Config()) is None  # no collateral
    w = next(w for w in harness.warrants.values() if w.target == trap.id)
    assert w.type == WarrantType.DEMONSTRATIVE
    kappa = harness.commitments[w.commitment]
    assert kappa.budget.extra["source_artifact"] == prop.id  # declared source


def test_refuting_the_property_reinstates_its_victims(harness):
    # THE safety net: conjectured ground truth is never unaccountable.
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    trap = _candidate(harness, base, TRAP)
    _candidate(harness, base, CORRECT)
    prop = _activated_property(harness, base, problem)
    crit_fuzz(harness, trap.id, Config())
    assert harness.state.status[trap.id] == Status.REFUTED

    attack(harness, prop.id, "the-property-is-wrong")  # ordinary criticism

    assert harness.state.status[prop.id] == Status.REFUTED
    # Source-artifact closure: the property's attacker attacks the verdict's
    # nu, the warrant carrier falls, the trap REINSTATES — automatically.
    assert harness.state.status[trap.id] == Status.ACCEPTED


def test_wipeout_guard_quarantines_population_indicting_property(harness):
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    trap = _candidate(harness, base, TRAP)  # the ONLY candidate: no support
    _activated_property(harness, base, problem)

    critic = crit_fuzz(harness, trap.id, Config())

    assert critic is None
    assert harness.state.status[trap.id] == Status.ACCEPTED  # quarantined
    last = list(harness.log.read())[-1]
    assert last.inputs[0] == "property-wipeout-quarantine"


def test_refuted_sibling_still_proves_satisfiability(harness):
    # Cold start (live run 3): the only ACCEPTED carrier was the trap itself,
    # so a valid kill deadlocked in quarantine. Satisfiability evidence does
    # not require the supporter to be accepted — a candidate refuted for
    # other reasons that PASSES the property proves real code can meet it.
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    trap = _candidate(harness, base, TRAP)
    good = _candidate(harness, base, CORRECT)
    attack(harness, good.id, "refuted-for-unrelated-reasons")
    assert harness.state.status[good.id] == Status.REFUTED
    _activated_property(harness, base, problem)

    critic = crit_fuzz(harness, trap.id, Config())

    assert critic is not None  # the refuted-but-passing sibling supports it
    assert harness.state.status[trap.id] == Status.REFUTED


# ---- promotion (the ratchet): probation -> trust, never finality ----

def test_probationary_property_is_not_promoted(harness):
    from deepreason.rules.experiment import promoted_properties

    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    _activated_property(harness, base, problem)
    assert promoted_properties(harness, base.id, Config()) == set()  # too young
    assert promoted_properties(
        harness, base.id, Config(PROP_PROBATION_EVENTS=0)
    ) == set()  # 0 disables promotion entirely


def _corroborate_by_surviving_attack(harness, prop_id: str) -> None:
    """Give the property a REAL corroboration record: attack it, then refute
    the critic (criticize-the-critic) so the property reinstates. Under the
    corroborated ratchet (intervals/boot postmortem), age alone no longer
    promotes — neglect earns no authority."""
    critic, _ = attack(harness, prop_id, "the-property-is-too-strict")
    attack(harness, critic.id, "the-critic-misread-the-problem-statement")
    assert harness.state.status[prop_id] == Status.ACCEPTED  # survived


def test_promoted_property_kills_without_population_support(harness):
    # The ratchet with teeth: the trap is the ONLY candidate (in
    # test_wipeout_guard... this exact situation quarantines), but a property
    # past probation that SURVIVED REAL CRITICISM holds the line — the
    # standard does not sink with the population.
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    trap = _candidate(harness, base, TRAP)
    prop = _activated_property(harness, base, problem)

    aged = Config(PROP_PROBATION_EVENTS=1)  # everything past probation
    from deepreason.rules.experiment import promoted_properties

    # Age alone no longer promotes: zero witnesses, zero scrutiny — the
    # intervals/boot massacre pattern stays under the wipeout guard.
    assert prop.id not in promoted_properties(harness, base.id, aged)
    assert crit_fuzz(harness, trap.id, aged) is None  # still quarantined

    _corroborate_by_surviving_attack(harness, prop.id)

    assert prop.id in promoted_properties(harness, base.id, aged)
    critic = crit_fuzz(harness, trap.id, aged)
    assert critic is not None
    assert harness.state.status[trap.id] == Status.REFUTED


def test_control_receipts_do_not_advance_property_probation(harness):
    from deepreason.run_manifest import ConjectureContextPolicyV1
    from deepreason.workflow.events import ConjectureWorkAssignmentV1
    from deepreason.workflow.models import LocalRepairPolicyV1, RouteLeaseRefV1
    from deepreason.workflow.profiles import ConjectureWorkflowProfileV1
    from deepreason.workflow.reducer import plan_conjecture_batch
    from deepreason.workflow.state import WorkflowProcessStateV1

    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    _candidate(harness, base, TRAP)
    prop = _activated_property(harness, base, problem)
    _corroborate_by_surviving_attack(harness, prop.id)

    from deepreason.rules.experiment import promoted_properties

    semantic_age = harness.semantic_event_clock() - harness.semantic_event_clock(
        prop.provenance.event_seq
    )
    probation = Config(PROP_PROBATION_EVENTS=semantic_age + 1)
    assert prop.id not in promoted_properties(harness, base.id, probation)
    formal_before = harness.state.model_copy(deep=True)
    physical_before = harness._next_seq
    semantic_before = harness.semantic_event_clock()

    context = ConjectureContextPolicyV1(
        mode="disabled",
        initial_max_blocks=0,
        initial_max_guides=0,
        max_context_expansion_requests=0,
        max_extra_blocks=0,
        permitted_retrieval_channels=(),
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )
    profile = ConjectureWorkflowProfileV1(
        manifest_digest="f" * 64,
        mode="shadow",
        workflow_profile="conjecture.shadow.v1",
        conjecturer_contract_id="conjecturer.legacy.v1",
        model_profile="standard",
        workload_profile="code",
        max_candidates=1,
        context_policy=context,
        repair_policy=LocalRepairPolicyV1.create(
            max_schema_repairs=0,
            scopes=(),
        ),
    )
    initial = WorkflowProcessStateV1.initial(
        manifest_digest=profile.manifest_digest,
        workflow_profile=profile.workflow_profile,
        formal_fence_seq=physical_before - 1,
        scratch_fence_seq=physical_before - 1,
    )
    planned = plan_conjecture_batch(
        profile,
        state=initial,
        problem_ref=problem.id,
        assignments=(
            ConjectureWorkAssignmentV1(
                route_lease=RouteLeaseRefV1(
                    seat=0,
                    endpoint_id="probation-clock-conjecturer",
                    route_sha256="a" * 64,
                ),
                contract_id=profile.conjecturer_contract_id,
                task_payload_schema_id="conjecture.semantic-ref.v1",
                task_payload_ref=problem.id,
            ),
        ),
        canonical_problem_refs=(problem.id,),
    )
    work = planned.work_orders[0]
    harness.record_control_transition(planned.decisions[0], work_order=work)
    harness.record_control_transition(planned.decisions[1])

    assert harness._next_seq == physical_before + 2
    assert harness.semantic_event_clock() == semantic_before
    assert harness.state == formal_before
    assert prop.id not in promoted_properties(harness, base.id, probation)


def test_promotion_is_trust_not_finality(harness):
    # N1 survives the ratchet: refuting a PROMOTED property still collapses
    # its verdicts via the source-artifact closure.
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    trap = _candidate(harness, base, TRAP)
    prop = _activated_property(harness, base, problem)
    _corroborate_by_surviving_attack(harness, prop.id)
    aged = Config(PROP_PROBATION_EVENTS=1)
    crit_fuzz(harness, trap.id, aged)
    assert harness.state.status[trap.id] == Status.REFUTED

    # A SECOND, better critic now refutes the promoted property outright.
    attack(harness, prop.id, "the-promoted-property-is-wrong")

    assert harness.state.status[prop.id] == Status.REFUTED
    assert harness.state.status[trap.id] == Status.ACCEPTED  # victims reinstate


def test_conj_pack_shows_active_property_claims(harness):
    from deepreason.llm.packs import render_conj_pack

    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    _activated_property(harness, base, problem)
    pack = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=3, token_budget=4000,
    )
    assert "ACTIVE PROPERTIES" in pack
    assert ASCENDING_CLAIM in pack  # candidates see the validated standard


# ---- scheduler: conjecture ground truth and kill the trap, end to end ----

def test_scheduler_conjectures_ground_truth_and_kills_the_trap(tmp_path):
    harness = Harness(tmp_path / "run")
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    trap = _candidate(harness, base, TRAP)
    conj = json.dumps({"candidates": [{"content": CORRECT, "typicality": 0.9}]})
    designs = json.dumps({"properties": [
        {"claim": ASCENDING_CLAIM, "checker": ASCENDING_CHECKER},
    ]})
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint([conj, conj]),
            "property_designer": MockEndpoint([designs]),
            "judge": [
                MockEndpoint(
                    [PASS_RULING],
                    name="mock://judge-gemma",
                    model="gemma-test",
                ),
                MockEndpoint(
                    [PASS_RULING],
                    name="mock://judge-qwen",
                    model="qwen-test",
                ),
            ],
        },
        harness.blobs,
        retry_max=2,
    )
    config = Config(VS_K=1, N_SCHOOLS=0, GEN_PROPOSE_PERIOD=0,
                    PROP_PROPOSE_PERIOD=1, PROP_MAX=1)
    scheduler = Scheduler(harness, adapter, config)
    scheduler.step()
    assert harness.state.status[trap.id] == Status.REFUTED  # same-cycle kill
    w = next(w for w in harness.warrants.values() if w.target == trap.id)
    kappa = harness.commitments[w.commitment]
    prop_id = kappa.budget.extra["source_artifact"]
    assert harness.state.artifacts[prop_id].codec == "code:python-prop"
    assert problem.id  # the property's legitimacy came from the problem statement


# ---- crash attribution (intervals/boot postmortem): a conjectured checker
# that THROWS refutes ITSELF, never the candidate ----

# Passes checker_wf's probe battery (decides on None/str/echo probes, and a
# crash counts as rejection for non-vacuity) but CRASHES on any empty-list
# output — the live bug class (`for a, b in inp` was the observed variant).
CRASHY_CHECKER = (
    "def check(inp, out):\n"
    "    if out is None or isinstance(out, (str, int, dict)):\n"
    "        return False\n"
    "    first = out[0]\n"
    "    return isinstance(first, int)\n"
)
EMPTY_RETURNER = "def solve(xs):\n    return []\n"


def _direct_property(harness, base, checker_source):
    """Register a property artifact as if it slipped in (bypassing the
    arrival probe) — isolates the fuzz-time attribution path."""
    from deepreason.ontology import Ref
    from deepreason.ontology.artifact import RefRole

    wf = checker_wf_commitment(base)
    harness.register_commitment(wf)
    return harness.create_artifact(
        f'"""crashes on empty outputs"""\n{checker_source}',
        codec="code:python-prop",
        interface=Interface(commitments=[wf.id],
                            refs=[Ref(target=base.id, role=RefRole.MENTION)]),
        provenance=Provenance(role="experimenter", event_seq=harness._next_seq),
    )


def test_fuzz_time_checker_crash_refutes_property_not_candidate(harness):
    from deepreason.ontology import Rule

    base = _base()
    harness.register_commitment(base)
    _problem(harness, base)
    victim = _candidate(harness, base, EMPTY_RETURNER)  # output [] crashes it
    prop = _direct_property(harness, base, CRASHY_CHECKER)
    assert harness.state.status[prop.id] == Status.ACCEPTED

    critic = crit_fuzz(harness, victim.id, Config())

    assert critic is None                                    # candidate spared
    assert harness.state.status[victim.id] == Status.ACCEPTED
    assert harness.state.status[prop.id] == Status.REFUTED   # checker indicted
    crash = [e for e in harness.log.read()
             if e.rule == Rule.MEASURE and e.inputs
             and e.inputs[0] == "property-checker-crash"]
    assert len(crash) == 1 and crash[0].inputs[1] == prop.id
    w = next(w for w in harness.warrants.values() if w.target == prop.id)
    assert w.type == WarrantType.DEMONSTRATIVE  # the crash is the evidence


def test_arrival_probe_refutes_crashing_checker_before_any_judge(harness):
    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    _candidate(harness, base, EMPTY_RETURNER)  # a real carrier to probe against
    judge_never_called = []  # both seats would record a consumed response
    adapter = _designer_adapter(
        harness,
        [{"claim": "outputs start with an int", "checker": CRASHY_CHECKER}],
        judge_never_called, judge_never_called,
    )
    activated = propose_properties(harness, base, problem, adapter, Config())

    assert activated == []
    prop = next(aid for aid, a in harness.state.artifacts.items()
                if a.codec == "code:python-prop")
    assert harness.state.status[prop] == Status.REFUTED  # dead on arrival


def test_standing_recrit_pool_includes_active_properties(harness):
    from deepreason.llm.adapter import LLMAdapter

    base = _base()
    harness.register_commitment(base)
    problem = _problem(harness, base)
    prop = _activated_property(harness, base, problem)
    adapter = LLMAdapter({"conjecturer": MockEndpoint([])}, harness.blobs)
    scheduler = Scheduler(harness, adapter, Config(N_SCHOOLS=0, FUZZ_N=0))
    pool = scheduler._standing_recrit_pool()
    assert prop.id in pool  # criteria face the same rotation as candidates
