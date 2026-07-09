"""Execution oracle (oracle.py): criticism grounded in running the candidate,
plus the sandbox-escape and determinism guards."""

import json

from deepreason import programs
from deepreason.config import Config
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.oracle import exec_oracle_commitment, run, run_from_spec
from deepreason.ontology import Interface, Provenance, Status
from deepreason.rules.crit import crit_argumentative, crit_program, execution_backed

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
