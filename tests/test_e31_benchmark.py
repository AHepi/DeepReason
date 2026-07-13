"""E3.1 benchmark-builder tests (scripts/e31_benchmark).

Covers: generator determinism (same seed = same bytes), bounded-prover
soundness spot-checks on planted targets, construction-checker correctness on
planted solutions, and holdout sealing (verifier/answer-key bytes absent from
every problem-facing file).  Zero LLM tokens, zero network.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from deepreason.canonical import sha256_hex  # noqa: E402
from deepreason.workloads.formal import PinnedLeanRequest  # noqa: E402

from e31_benchmark import axiom_domains, build_demo, constructions  # noqa: E402
from e31_benchmark.bounded_prover import (  # noqa: E402
    Budget,
    app,
    difficulty_certificate,
    prove_equation,
    var,
)
from e31_benchmark.sealed import sealing_violations  # noqa: E402

TEST_SEED = 20260713


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="module")
def demo_build(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("e31") / "demo"
    build_demo.build_benchmark(out, seed=TEST_SEED)
    return out


# --- generator determinism ----------------------------------------------------

def test_full_build_is_deterministic(demo_build, tmp_path):
    rebuilt = tmp_path / "again"
    build_demo.build_benchmark(rebuilt, seed=TEST_SEED)
    assert _tree_bytes(rebuilt) == _tree_bytes(demo_build)


def test_domain_generation_deterministic_and_seed_sensitive():
    first = axiom_domains.generate_domain("seed-a")
    second = axiom_domains.generate_domain("seed-a")
    assert first == second
    targets_first = axiom_domains.enumerate_targets(first)
    targets_second = axiom_domains.enumerate_targets(second)
    lean_first = axiom_domains.render_lean(first, targets_first)
    lean_second = axiom_domains.render_lean(second, targets_second)
    assert lean_first.encode() == lean_second.encode()
    other = axiom_domains.generate_domain("seed-b")
    assert other.axiom_strings() != first.axiom_strings()


def test_construction_generation_deterministic():
    first = constructions.generate_construction(TEST_SEED, "forbidden_words", 4)
    second = constructions.generate_construction(TEST_SEED, "forbidden_words", 4)
    assert first == second
    assert first.checker_source.encode() == second.checker_source.encode()


# --- bounded-prover soundness spot-checks --------------------------------------

_ASSOC = [
    (
        app("f", app("f", var("x"), var("y")), var("z")),
        app("f", var("x"), app("f", var("y"), var("z"))),
    )
]
_BUDGET = Budget(max_depth=4, max_nodes=2000, max_term_size=15)


def test_planted_derivable_target_proves():
    x, y, z, w = var("x"), var("y"), var("z"), var("w")
    lhs = app("f", app("f", app("f", x, y), z), w)
    rhs = app("f", x, app("f", y, app("f", z, w)))
    outcome = prove_equation(_ASSOC, lhs, rhs, _BUDGET)
    assert outcome.proved
    assert outcome.depth == 2
    # the derivation chain is replayable end to end
    assert outcome.derivation[0] == "f(f(f(#x, #y), #z), #w)"
    assert outcome.derivation[-1] == "f(#x, f(#y, f(#z, #w)))"
    assert len(outcome.derivation) == outcome.depth + 1


def test_planted_underivable_target_fails_at_budget():
    # commutativity does not follow from associativity alone
    lhs = app("f", var("x"), var("y"))
    rhs = app("f", var("y"), var("x"))
    outcome = prove_equation(_ASSOC, lhs, rhs, _BUDGET)
    assert not outcome.proved
    assert outcome.depth is None


def test_involution_exhaustive_failure_is_not_truncated():
    involution = [(app("u", app("u", var("x"))), var("x"))]
    proved = prove_equation(
        involution, app("u", app("u", app("u", var("x")))), app("u", var("x")), _BUDGET
    )
    assert proved.proved and proved.depth == 1
    refused = prove_equation(involution, app("u", var("x")), var("x"), _BUDGET)
    assert not refused.proved
    assert not refused.truncated  # the whole bounded space was searched


def test_difficulty_certificate_grades_nontriviality():
    x, y, z, w = var("x"), var("y"), var("z"), var("w")
    deep = difficulty_certificate(
        _ASSOC,
        app("f", app("f", app("f", x, y), z), w),
        app("f", x, app("f", y, app("f", z, w))),
        small=Budget(max_depth=1, max_nodes=200, max_term_size=15),
        large=_BUDGET,
    )
    assert deep["nontrivial"] and deep["depth"] == 2
    shallow = difficulty_certificate(
        _ASSOC,
        app("f", app("f", x, y), z),
        app("f", x, app("f", y, z)),
        small=Budget(max_depth=1, max_nodes=200, max_term_size=15),
        large=_BUDGET,
    )
    assert not shallow["nontrivial"] and shallow["depth"] == 1


def test_enumerated_targets_carry_valid_certificates():
    domain = axiom_domains.generate_domain(f"{TEST_SEED}/axiom/0")
    targets = axiom_domains.enumerate_targets(domain)
    assert targets, "enumerator must produce depth-graded targets"
    depths = [target.depth for target in targets]
    assert depths == sorted(depths)
    for target in targets:
        certificate = target.certificate
        assert certificate["outcome_large"]["proved"]
        assert certificate["depth"] == target.depth
        if target.depth > axiom_domains.B_SMALL.max_depth:
            assert certificate["nontrivial"]


# --- construction checkers on planted solutions --------------------------------

@pytest.mark.parametrize(
    ("family", "corrupt"),
    [
        ("sidon_residue", lambda witness, params: [witness[0]] * params["n"]),
        ("forbidden_words", lambda witness, params: "0" * params["n"]),
        ("displaced_permutation", lambda witness, params: list(range(params["n"]))),
    ],
)
def test_checker_accepts_planted_witness_and_rejects_corruption(family, corrupt):
    problem = constructions.generate_construction(TEST_SEED, family, 9)
    ok, reason = constructions.check_candidate(problem, problem.witness)
    assert ok, reason
    bad = corrupt(problem.witness, problem.params)
    ok, reason = constructions.check_candidate(problem, bad)
    assert not ok and reason


def test_sealed_checker_script_matches_in_process_checker(tmp_path):
    problem = constructions.generate_construction(TEST_SEED, "displaced_permutation", 9)
    (tmp_path / "checker.py").write_text(problem.checker_source, encoding="utf-8")

    def run(candidate) -> int:
        (tmp_path / "candidate.json").write_text(json.dumps(candidate), encoding="utf-8")
        spec = problem.check_spec
        completed = subprocess.run(  # trusted checker, pinned argv (CheckSpec)
            list(spec.argv), cwd=tmp_path, capture_output=True, timeout=30, check=False
        )
        return completed.returncode

    assert run(problem.witness) == problem.check_spec.expected_exit
    assert run(list(range(problem.params["n"]))) != problem.check_spec.expected_exit


def test_brute_force_certifies_solvability():
    for offset, family in enumerate(constructions.FAMILIES):
        problem = constructions.generate_construction(TEST_SEED, family, 3 + offset)
        brute = problem.brute_force
        assert brute["witness"] is not None
        assert brute["solutions_found"] >= 1
        assert not brute["cap_hit"]
        assert brute["search_space_size"] >= brute["solutions_found"]
        # sized so lookup fails: solutions are sparse in the enumerated space
        assert brute["solutions_found"] <= 0.05 * brute["candidates_enumerated"]


# --- holdout sealing -------------------------------------------------------------

def test_holdout_sealing_withholds_verifier_bytes(demo_build):
    holdout_manifest = json.loads((demo_build / "holdout" / "manifest.json").read_text())
    assert holdout_manifest["reveal_policy"] == "post_hoc_reveal_only"
    problem_files = _tree_bytes(demo_build / "problems")
    manifest_bytes = (demo_build / "manifest.json").read_bytes()
    assert holdout_manifest["problems"], "holdout manifest must list problems"
    for entry in holdout_manifest["problems"]:
        for name, ref in entry["sealed_refs"].items():
            blob_path = demo_build / "holdout" / "blobs" / ref[:2] / ref
            data = blob_path.read_bytes()
            assert sha256_hex(data) == ref  # content-addressed
            assert ref.encode() in manifest_bytes  # hash visible (spec 10.5)
            for rel_path, content in problem_files.items():
                assert data not in content, (
                    f"sealed {entry['id']}/{name} leaked into problems/{rel_path}"
                )
    # no problem-facing file is a checker or answer key
    assert not any(
        Path(rel).name in {"checker.py", "answer_key.json", "certificate.json"}
        for rel in problem_files
    )


def test_sealing_audit_helper_detects_a_planted_leak(demo_build, tmp_path):
    holdout_manifest = json.loads((demo_build / "holdout" / "manifest.json").read_text())
    entry = next(
        item for item in holdout_manifest["problems"] if item["class"] == "construction"
    )
    ref = entry["sealed_refs"]["checker.py"]
    sealed_bytes = (demo_build / "holdout" / "blobs" / ref[:2] / ref).read_bytes()

    from e31_benchmark.sealed import SealedProblem

    sealed = [
        SealedProblem(
            problem_id=entry["id"],
            problem_class=entry["class"],
            seed=entry["seed"],
            blobs={"checker.py": sealed_bytes, "certificate.json": b"x" * 64},
        )
    ]
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    (clean_dir / "problem.json").write_bytes(b"{}")
    assert sealing_violations(clean_dir, sealed) == []
    leaked_dir = tmp_path / "leaked"
    leaked_dir.mkdir()
    (leaked_dir / "oops.txt").write_bytes(b"prefix" + sealed_bytes)
    violations = sealing_violations(leaked_dir, sealed)
    assert violations and "checker.py" in violations[0]


def test_pinned_lean_requests_are_valid_and_pin_the_sources(demo_build):
    manifest = json.loads((demo_build / "manifest.json").read_text())
    axiom_entries = [item for item in manifest["problems"] if item["class"] == "axiom_domain"]
    assert len(axiom_entries) == 3
    for entry in axiom_entries:
        problem_dir = demo_build / "problems" / entry["id"]
        request = PinnedLeanRequest.model_validate_json(
            (problem_dir / "pinned_lean_request.json").read_text()
        )
        lean_bytes = (problem_dir / "domain.lean").read_bytes()
        assert request.source_ref == sha256_hex(lean_bytes) == entry["lean_source_sha256"]
        assert request.toolchain_id == axiom_domains.LEAN_TOOLCHAIN_ID
        assert request.allow_sorry is False
        source_text = lean_bytes.decode()
        for theorem in request.target_theorems:
            assert f"theorem {theorem} " in source_text
    assert manifest["lean_kernel_validation"]["status"] in {"pending", "validated"}


def test_build_report_records_certificates(demo_build):
    report = json.loads((demo_build / "build_report.json").read_text())
    assert report["sealing_audit"]["clean"]
    assert report["total_targets"] >= 9
    assert report["nontrivial_targets"] >= 1
    assert set(report["theorem_depth_distribution"]) >= {"1", "2", "3"}
    assert len(report["constructions"]) == 3
    for stat in report["constructions"]:
        assert stat["solvable"]
        assert 0 < stat["solution_density"] <= 0.05
