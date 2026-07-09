"""Execution oracle (oracle.py): criticism grounded in running the candidate,
plus the sandbox-escape and determinism guards."""

from deepreason import programs
from deepreason.oracle import exec_oracle_commitment, run, run_from_spec
from deepreason.ontology import Interface, Provenance, Status
from deepreason.rules.crit import crit_program

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
