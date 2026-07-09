"""Execution oracle (oracle.py): criticism grounded in running the candidate,
plus the sandbox-escape and determinism guards."""

import json

from deepreason import programs
from deepreason.config import Config
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Interface, Provenance, Status, WarrantType
from deepreason.oracle import (
    counterexample_commitment,
    exec_oracle_commitment,
    property_oracle_commitment,
    run,
    run_from_spec,
    run_property,
)
from deepreason.rules.crit import (
    crit_argumentative,
    crit_argumentative_batch,
    crit_program,
    execution_backed,
)

DOUBLE = [{"in": [1], "out": 2}, {"in": [5], "out": 10}, {"in": [0], "out": 0}]


# ---- the core: a verdict from RUNNING the candidate ----

def test_correct_candidate_passes():
    verdict, detail = run("def solve(x):\n    return x * 2", "solve", DOUBLE)
    assert verdict == "pass"
    assert detail["cases_passed"] == 3


def test_wrong_candidate_is_refuted_by_execution():
    verdict, detail = run("def solve(x):\n    return x + 2", "solve", DOUBLE)
    assert verdict == "fail"
    assert detail["case"] == 0  # x=1 -> 3, expected 2
    assert detail["input"] == [1] and detail["expected"] == 2


def test_real_computation_executes():
    src = "def solve(xs):\n    return sorted(xs)"
    verdict, _ = run(src, "solve", [{"in": [[3, 1, 2]], "out": [1, 2, 3]}])
    assert verdict == "pass"


def test_missing_entry_point_fails():
    verdict, _ = run("def other(x):\n    return x", "solve", DOUBLE)
    assert verdict == "fail"


# ---- deterministic step bound (no wall-clock) ----

def test_infinite_loop_hits_step_bound_not_a_hang():
    src = "def solve(x):\n    while True:\n        y = 1"
    verdict, detail = run(src, "solve", [{"in": [0], "out": 0}], step_limit=1000)
    assert verdict == "fail"
    assert "step limit" in detail["error"]


def test_verdict_is_deterministic():
    a = run("def solve(x):\n    return x * 2", "solve", DOUBLE)
    b = run("def solve(x):\n    return x * 2", "solve", DOUBLE)
    assert a == b  # same (verdict, trace) — replay-stable (§0)


# ---- sandbox: untrusted candidate cannot escape ----

def test_import_is_blocked():
    verdict, detail = run("import os\ndef solve(x):\n    return x", "solve", DOUBLE)
    assert verdict == "fail" and "unsafe" in detail["error"]


def test_dunder_attribute_is_blocked():
    verdict, detail = run("def solve(x):\n    return ().__class__", "solve", DOUBLE)
    assert verdict == "fail" and "unsafe" in detail["error"]


def test_dunder_import_name_is_blocked():
    verdict, detail = run("def solve(x):\n    return __import__('os')", "solve", DOUBLE)
    assert verdict == "fail" and "unsafe" in detail["error"]


def test_open_is_not_in_scope():
    verdict, detail = run("def solve(x):\n    return open('/etc/passwd')", "solve", DOUBLE)
    assert verdict == "fail"  # NameError: open is not a whitelisted builtin


def test_huge_int_literal_bomb_is_blocked():
    verdict, detail = run("def solve(x):\n    return sum(range(9999999999))", "solve", DOUBLE)
    assert verdict == "fail" and "unsafe" in detail["error"]


def test_pow_bomb_is_blocked():
    verdict, detail = run("def solve(x):\n    return 9 ** 9 ** 9", "solve", DOUBLE)
    assert verdict == "fail" and "unsafe" in detail["error"]


# ---- integration: exec-oracle as a commitment refutes via crit_program ----

def test_exec_oracle_commitment_evaluates(harness):
    c = exec_oracle_commitment("solve", DOUBLE)
    verdict, _ = programs.evaluate(
        c,
        harness.create_artifact("def solve(x):\n    return x * 2", codec="code:python"),
        harness.blobs,
    )
    assert verdict == "pass"
    assert programs.evaluable(c)


def test_crit_program_refutes_wrong_code_by_running_it(harness):
    c = exec_oracle_commitment("solve", DOUBLE)
    harness.register_commitment(c)
    good = harness.create_artifact(
        "def solve(x):\n    return x * 2",
        codec="code:python",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"),
    )
    bad = harness.create_artifact(
        "def solve(x):\n    return x + 999",
        codec="code:python",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"),
    )
    assert harness.state.status[good.id] == Status.ACCEPTED
    assert harness.state.status[bad.id] == Status.ACCEPTED  # before criticism

    crit_program(harness, good.id)  # runs the code — passes, no warrant
    crit_program(harness, bad.id)   # runs the code — fails a test -> demonstrative warrant

    assert harness.state.status[good.id] == Status.ACCEPTED  # survived EXECUTION
    assert harness.state.status[bad.id] == Status.REFUTED    # refuted by reality, not a judge


def test_run_from_spec_overruns_on_malformed_spec():
    from deepreason.ontology.commitment import Budget

    verdict, _ = run_from_spec("def solve(x):\n    return x", Budget(extra={}))
    assert verdict == "overrun"  # not a wall-clock condition (§1): the spec is unusable


# ---- execution supremacy: a passing oracle verdict beats a mere argument ----

def _oracle_candidate(harness, source):
    """Register the exec-oracle commitment and a candidate carrying it."""
    c = exec_oracle_commitment("solve", DOUBLE)
    harness.register_commitment(c)
    art = harness.create_artifact(
        source,
        codec="code:python",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"),
    )
    return c, art


def _attacking_critic(harness, case="the algorithm is obviously unsound"):
    return LLMAdapter(
        {"argumentative_critic": MockEndpoint(
            [json.dumps({"attack": True, "case": case})]
        )},
        harness.blobs,
        retry_max=2,
    )


def test_execution_backed_true_only_when_passing(harness):
    _, good = _oracle_candidate(harness, "def solve(x):\n    return x * 2")
    assert execution_backed(harness, good.id) is True


def test_execution_backed_false_when_failing(harness):
    _, bad = _oracle_candidate(harness, "def solve(x):\n    return x + 999")
    # A failing exec verdict earns no protection — execution itself refutes it.
    assert execution_backed(harness, bad.id) is False


def test_execution_backed_false_without_oracle(harness):
    plain = harness.create_artifact("just some prose, no commitment")
    assert execution_backed(harness, plain.id) is False


def test_argument_cannot_refute_passing_candidate(harness):
    _, good = _oracle_candidate(harness, "def solve(x):\n    return x * 2")
    assert harness.state.status[good.id] == Status.ACCEPTED

    critic = crit_argumentative(harness, good.id, _attacking_critic(harness), Config())

    assert critic is None                                    # no warrant registered
    assert harness.state.status[good.id] == Status.ACCEPTED  # reality overrides argument
    # No argumentative warrant against a passing candidate exists on the graph.
    assert not any(w.target == good.id for w in harness.warrants.values())
    # The override is on the record for token accounting (the call still spent).
    last = list(harness.log.read())[-1]
    assert last.inputs == ["arg-crit-overridden-by-execution", good.id]
    assert last.llm is not None


def test_argument_still_refutes_failing_candidate(harness):
    _, bad = _oracle_candidate(harness, "def solve(x):\n    return x + 999")

    critic = crit_argumentative(harness, bad.id, _attacking_critic(harness), Config())

    assert critic is not None                             # not execution-backed: argument stands
    assert harness.state.status[bad.id] == Status.REFUTED


def test_execution_still_refutes_a_passing_looking_but_wrong_candidate(harness):
    # Execution supremacy protects only against ARGUMENT, never against a
    # failing test: crit_program runs the code and refutes by reality.
    _, bad = _oracle_candidate(harness, "def solve(x):\n    return x + 999")
    assert execution_backed(harness, bad.id) is False
    crit_program(harness, bad.id)
    assert harness.state.status[bad.id] == Status.REFUTED


# ---- execution supremacy also covers the pairwise preference path (§10.2) ----

def _problem(harness, *criteria):
    from deepreason.ontology import Problem, ProblemProvenance

    p = Problem(
        id="pi-x2",
        description="double the input",
        criteria=list(criteria),
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    )
    harness.register_problem(p)
    return p


def _pairwise_judge(harness, r1, r2):
    return LLMAdapter(
        {"judge": MockEndpoint([json.dumps(r1), json.dumps(r2)])},
        harness.blobs,
        retry_max=2,
    )


def test_pairwise_preference_cannot_refute_execution_backed_loser(harness):
    from deepreason.informal.trial import pairwise_discriminate

    c = exec_oracle_commitment("solve", DOUBLE)
    harness.register_commitment(c)
    p = _problem(harness, c.id)
    a = harness.create_artifact(
        "def solve(x):\n    return x * 2",
        codec="code:python", interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"), problem_id=p.id,
    )
    b = harness.create_artifact(
        "def solve(x):\n    return x + x",  # distinct source, also passes
        codec="code:python", interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"), problem_id=p.id,
    )
    assert execution_backed(harness, b.id) is True
    # Judge consistently prefers A; b would be the loser — but b passes its oracle.
    adapter = _pairwise_judge(
        harness,
        {"winner": "A", "decisive_point": "return x + x"},
        {"winner": "B", "decisive_point": "return x + x"},
    )
    critic = pairwise_discriminate(harness, p, a.id, b.id, adapter, Config())
    assert critic is None                                 # rivalry stands unresolved
    assert harness.state.status[b.id] == Status.ACCEPTED  # preference can't beat execution
    assert not any(w.target == b.id for w in harness.warrants.values())


def test_pairwise_preference_still_refutes_a_non_execution_loser(harness):
    from deepreason.informal.trial import pairwise_discriminate

    c = exec_oracle_commitment("solve", DOUBLE)
    harness.register_commitment(c)
    p = _problem(harness, c.id)
    a = harness.create_artifact(
        "def solve(x):\n    return x * 2",
        codec="code:python", interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"), problem_id=p.id,
    )
    b = harness.create_artifact(  # plain prose, carries no oracle: no protection
        "just an assertion that doubling is easy",
        provenance=Provenance(role="conjecturer"), problem_id=p.id,
    )
    assert execution_backed(harness, b.id) is False
    adapter = _pairwise_judge(
        harness,
        {"winner": "A", "decisive_point": "just an assertion"},
        {"winner": "B", "decisive_point": "just an assertion"},
    )
    critic = pairwise_discriminate(harness, p, a.id, b.id, adapter, Config())
    assert critic is not None
    assert harness.state.status[b.id] == Status.REFUTED


# ---- property oracle: reference-free execution verdicts ----

# "return the input list sorted ascending" — correctness decided by a CHECKER
# over (input, output); no expected outputs anywhere in the spec.
CHECKER = (
    "def check(inp, out):\n"
    "    xs = inp[0]\n"
    "    return isinstance(out, list) and sorted(xs) == out\n"
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
SORT_INPUTS = [[[3, 1, 2]]]  # one frozen case: solve([3, 1, 2])
GOOD_SORT = "def solve(xs):\n    return sorted(xs)"
# Passes the frozen input (len 3) but mishandles short lists — the classic
# incomplete-test-suite survivor that only a NEW input can expose.
SNEAKY_SORT = (
    "def solve(xs):\n"
    "    if len(xs) > 2:\n"
    "        return sorted(xs)\n"
    "    return xs\n"
)


def test_property_pass_and_fail_without_reference_outputs():
    assert run_property(GOOD_SORT, "solve", SORT_INPUTS, CHECKER)[0] == "pass"
    verdict, detail = run_property(
        "def solve(xs):\n    return xs", "solve", SORT_INPUTS, CHECKER
    )
    assert verdict == "fail" and detail["error"] == "property violated"


def test_unusable_checker_is_overrun_not_candidate_fault():
    verdict, detail = run_property(GOOD_SORT, "solve", SORT_INPUTS, "import os")
    assert verdict == "overrun" and "checker" in detail["error"]


def test_property_oracle_commitment_evaluates(harness):
    c = property_oracle_commitment("solve", SORT_INPUTS, CHECKER, GATE)
    art = harness.create_artifact(GOOD_SORT, codec="code:python")
    assert programs.evaluable(c)
    assert programs.evaluate(c, art, harness.blobs)[0] == "pass"


def test_property_backed_candidate_counts_as_execution_backed(harness):
    c = property_oracle_commitment("solve", SORT_INPUTS, CHECKER, GATE)
    harness.register_commitment(c)
    art = harness.create_artifact(
        SNEAKY_SORT, codec="code:python",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"),
    )
    assert execution_backed(harness, art.id) is True  # passes the frozen input


def test_counterexample_commitment_admission():
    base = property_oracle_commitment("solve", SORT_INPUTS, CHECKER, GATE)
    ok = counterexample_commitment(base, [[2, 1]])
    assert ok is not None and ok.id.startswith("prop-oracle@") and ok.id != base.id
    assert counterexample_commitment(base, [[2, 1]]).id == ok.id  # content-addressed
    assert counterexample_commitment(base, [["a", "b"]]) is None  # gate: not ints
    assert counterexample_commitment(base, [list(range(30))]) is None  # gate: too long
    assert counterexample_commitment(base, "not a list") is None
    exec_base = exec_oracle_commitment("solve", DOUBLE)
    assert counterexample_commitment(exec_base, [[2, 1]]) is None  # no checker


# ---- the counterexample loop: critics refute by proposing NEW inputs ----

def _property_candidate(harness, source):
    c = property_oracle_commitment("solve", SORT_INPUTS, CHECKER, GATE)
    harness.register_commitment(c)
    art = harness.create_artifact(
        source, codec="code:python",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"),
    )
    return c, art


WITHDRAW = json.dumps({"attack": False, "case": ""})


def _cx_critic(harness, counterexample, case="fails on short lists", retry_responses=()):
    responses = [json.dumps(
        {"attack": True, "case": case, "counterexample": counterexample}
    ), *retry_responses]
    return LLMAdapter(
        {"argumentative_critic": MockEndpoint(responses)},
        harness.blobs,
        retry_max=2,
    )


def test_counterexample_refutes_an_execution_backed_candidate(harness):
    _, sneaky = _property_candidate(harness, SNEAKY_SORT)
    assert execution_backed(harness, sneaky.id) is True  # frozen tests missed the bug

    critic = crit_argumentative(harness, sneaky.id, _cx_critic(harness, [[2, 1]]), Config())

    assert critic is not None
    assert harness.state.status[sneaky.id] == Status.REFUTED  # refuted by EXECUTION
    w = next(w for w in harness.warrants.values() if w.target == sneaky.id)
    assert w.type == WarrantType.DEMONSTRATIVE  # not an argument: a run verdict
    assert w.commitment.startswith("prop-oracle@")
    assert w.commitment in harness.commitments  # minted commitment is registered


def test_passing_counterexample_grounds_nothing_and_supremacy_holds(harness):
    _, good = _property_candidate(harness, GOOD_SORT)

    critic = crit_argumentative(
        harness, good.id,
        _cx_critic(harness, [[2, 1]], retry_responses=[WITHDRAW]), Config(),
    )

    assert critic is None  # solve([2,1]) == [1,2]: property held, argument overridden
    assert harness.state.status[good.id] == Status.ACCEPTED
    last = list(harness.log.read())[-1]
    assert last.inputs == ["arg-crit-overridden-by-execution", good.id]


def test_gate_rejected_counterexample_grounds_nothing(harness):
    _, sneaky = _property_candidate(harness, SNEAKY_SORT)
    # ["a", "b"] would break sneaky's sort, but the problem never posed string
    # inputs: the gate rejects it, so it refutes nothing and supremacy holds.
    critic = crit_argumentative(
        harness, sneaky.id,
        _cx_critic(harness, [["a", "b"]], retry_responses=[WITHDRAW]), Config(),
    )
    assert critic is None
    assert harness.state.status[sneaky.id] == Status.ACCEPTED


# ---- the counterexample RETRY: the gate's rejection reason feeds back ----

def test_retry_with_echoed_reason_grounds_the_second_counterexample(harness):
    _, sneaky = _property_candidate(harness, SNEAKY_SORT)
    good_retry = json.dumps(
        {"attack": True, "case": "short lists unsorted", "counterexample": [[2, 1]]}
    )
    # First proposal is gate-rejected (strings); the retry — with the reason
    # echoed — proposes a valid discriminating input and refutes by execution.
    critic = crit_argumentative(
        harness, sneaky.id,
        _cx_critic(harness, [["a", "b"]], retry_responses=[good_retry]), Config(),
    )
    assert critic is not None
    assert harness.state.status[sneaky.id] == Status.REFUTED
    kinds = [e.inputs[0] for e in harness.log.read() if e.inputs]
    assert "arg-crit-cx-rejected" in kinds  # the feedback round is on the record


def test_retry_pack_contains_reason_gate_and_previous_proposal(harness):
    from deepreason.llm.packs import render_cx_retry_pack

    _, sneaky = _property_candidate(harness, SNEAKY_SORT)
    pack = render_cx_retry_pack(
        [{"target": sneaky.id, "counterexample": [["a", "b"]],
          "reason": "input rejected by the admission gate"}],
        harness.state, harness.commitments, harness.blobs, token_budget=4000,
    )
    assert "input rejected by the admission gate" in pack  # the echoed verdict
    assert '[["a", "b"]]' in pack                          # what was proposed
    assert "def valid(inp):" in pack                       # the gate to satisfy
    assert "def solve" in pack                             # the code to attack


def test_cx_retry_disabled_by_config(harness):
    _, sneaky = _property_candidate(harness, SNEAKY_SORT)
    # Only ONE scripted response: with CX_RETRY_MAX=0 no retry call is made
    # (MockEndpoint would raise if one were attempted).
    critic = crit_argumentative(
        harness, sneaky.id, _cx_critic(harness, [["a", "b"]]),
        Config(CX_RETRY_MAX=0),
    )
    assert critic is None
    assert harness.state.status[sneaky.id] == Status.ACCEPTED


def test_batch_retry_grounds_counterexample(harness):
    c, sneaky = _property_candidate(harness, SNEAKY_SORT)
    good = harness.create_artifact(
        GOOD_SORT, codec="code:python",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"),
    )
    first = json.dumps({"cases": [
        {"target": sneaky.id, "attack": True, "case": "special-cased",
         "counterexample": [["a", "b"]]},  # gate-rejected: strings
        {"target": good.id, "attack": False, "case": ""},
    ]})
    second = json.dumps({"cases": [
        {"target": sneaky.id, "attack": True, "case": "special-cased",
         "counterexample": [[2, 1]]},      # valid + discriminating
    ]})
    adapter = LLMAdapter(
        {"argumentative_critic": MockEndpoint([first, second])},
        harness.blobs, retry_max=2,
    )
    critics = crit_argumentative_batch(harness, [sneaky.id, good.id], adapter, Config())
    assert harness.state.status[sneaky.id] == Status.REFUTED  # retry grounded it
    assert harness.state.status[good.id] == Status.ACCEPTED
    assert len(critics) == 1


def test_batch_counterexample_also_grounds(harness):
    c, sneaky = _property_candidate(harness, SNEAKY_SORT)
    good = harness.create_artifact(
        GOOD_SORT, codec="code:python",
        interface=Interface(commitments=[c.id]),
        provenance=Provenance(role="conjecturer"),
    )
    batch = json.dumps({"cases": [
        {"target": sneaky.id, "attack": True, "case": "short lists unsorted",
         "counterexample": [[2, 1]]},
        {"target": good.id, "attack": True, "case": "handwavy complaint"},
    ]})
    withdraw_batch = json.dumps({"cases": [
        {"target": good.id, "attack": False, "case": ""},
    ]})
    adapter = LLMAdapter(
        {"argumentative_critic": MockEndpoint([batch, withdraw_batch])},
        harness.blobs, retry_max=2,
    )
    critics = crit_argumentative_batch(harness, [sneaky.id, good.id], adapter, Config())
    assert len(critics) == 1  # counterexample grounded; bare argument overridden
    assert harness.state.status[sneaky.id] == Status.REFUTED
    assert harness.state.status[good.id] == Status.ACCEPTED


def test_crit_pack_advertises_the_counterexample_recourse(harness):
    from deepreason.llm.packs import render_crit_pack

    _, art = _property_candidate(harness, GOOD_SORT)
    pack = render_crit_pack(art.id, harness.state, harness.commitments,
                            harness.blobs, token_budget=2500)
    assert "counterexample" in pack
    # The critic can AIM: the frozen spec's entry, an example input, and the
    # admission gate source are all visible (else it proposes out-of-spec
    # inputs that ground nothing).
    assert "entry point: solve" in pack
    assert "example input" in pack
    assert "def valid(inp):" in pack
    plain = harness.create_artifact("prose with no oracle")
    pack2 = render_crit_pack(plain.id, harness.state, harness.commitments,
                             harness.blobs, token_budget=2500)
    assert "counterexample" not in pack2
