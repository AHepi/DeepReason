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
            "judge": [MockEndpoint(judge1), MockEndpoint(judge2)],
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
            "judge": [MockEndpoint([PASS_RULING]), MockEndpoint([PASS_RULING])],
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
