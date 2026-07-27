"""M1 — checks: skeleton contract, program/predicate evals, and id parity
with the parent (same skeleton => same interface, byte-for-byte)."""

import json

import pytest

from minireason.checks import (compile_checks, evaluable, evaluate,
                               forbidden_commitment_id, parse_skeleton, run_checks)

SKELETON = json.dumps({
    "claim": "bronze collapse was systemic",
    "mechanism": "interdependent trade routes propagated local failures",
    "scope": {"covers": ["eastern mediterranean"], "excludes": ["egypt proper"]},
    "forbidden": [
        {"case": "content must mention trade",
         "eval": "program:json-wf"},
        {"case": "a purely climatic account suffices",
         "eval": "rubric:std-hist"},
    ],
    "prose_notes": "n/a",
})


def test_parse_skeleton():
    assert parse_skeleton(SKELETON) is not None
    assert parse_skeleton("not json") is None
    assert parse_skeleton('{"claim": "x"}') is None  # mechanism required
    assert parse_skeleton(json.dumps({"claim": 1, "mechanism": []})) is None
    assert parse_skeleton(json.dumps({
        "claim": "x", "mechanism": "m",
        "forbidden": [{"case": "unsafe", "eval": "predicate:True"}],
    })) is None


def test_skeleton_wf_requires_forbidden_cases():
    verdict, detail = evaluate("program:skeleton_wf",
                               '{"claim": "c", "mechanism": "m", "forbidden": []}')
    assert verdict == "fail"
    assert "forbids nothing" in detail["error"]
    verdict, _ = evaluate("program:skeleton_wf", SKELETON)
    assert verdict == "pass"


def test_predicate_eval_uses_globals_for_comprehensions():
    # The parent's fix: free names inside comprehension bodies resolve via
    # globals; a locals-only namespace broke [len(w) for w in ...].
    verdict, _ = evaluate("predicate:all(len(w) > 0 for w in content.split())", "a b c")
    assert verdict == "pass"


def test_predicate_error_is_a_failed_verdict():
    verdict, detail = evaluate("predicate:undefined_name", "x")
    assert verdict == "fail" and "error" in detail
    verdict, _ = evaluate("predicate:__import__('os')", "x")
    assert verdict == "fail"  # no builtins in the sandbox


def test_rubric_not_loop_evaluable():
    assert not evaluable("rubric:std-hist")
    with pytest.raises(ValueError):
        evaluate("rubric:std-hist", "x")


def test_compile_and_run_checks():
    checks = compile_checks(SKELETON)
    ids = [c["id"] for c in checks]
    assert ids[0] == "skeleton-wf"
    assert all(i.startswith("fc:") for i in ids[1:])
    assert len(ids) == 3
    # Mechanical checks pass on the skeleton itself; the rubric one is
    # carried but not judged.
    assert run_checks(SKELETON, checks) == []
    # A content that names a canonical program it fails is refuted for free.
    bad_obj = json.loads(SKELETON)
    bad_obj["forbidden"][0] = {
        "case": "must be a website manifest",
        "eval": "program:manifest_wf",
    }
    bad = json.dumps(bad_obj)
    failures = run_checks(bad, compile_checks(bad))
    assert failures and failures[0]["eval"] == "program:manifest_wf"


def test_malformed_corpus_all_refuted():
    corpus = ["plain prose, no json",
              '{"claim": "c"}',
              '{"claim": "c", "mechanism": "m"}',  # forbids nothing
              '{"claim": "c", "mechanism": "m", "forbidden": []}']
    for text in corpus:
        failures = run_checks(text, compile_checks(text))
        assert failures, text
        assert failures[0]["commitment"] == "skeleton-wf"


def test_commitment_id_parity_with_parent():
    """Same forbidden case => the parent's fc: id, byte-for-byte (G6)."""
    pytest.importorskip("deepreason.canonical")
    from deepreason.informal.skeleton import forbidden_commitment
    from minireason.checks import ForbiddenCase

    case = ForbiddenCase(case="content must be valid JSON", eval="program:json-wf")
    assert forbidden_commitment_id(case) == forbidden_commitment(case).id


def test_canonical_lineage_program_can_refute_without_mini_registry():
    from deepreason.ontology import Budget, Commitment

    content = json.dumps({
        "claim": "unconnected",
        "mechanism": "appeared from nowhere",
        "forbidden": [{"case": "valid JSON", "eval": "program:json-wf"}],
    })
    lineage = Commitment(
        id="lineage-check",
        eval="program:lineage_ref",
        budget=Budget(extra={"endpoints": "required-source"}),
    )
    failures = run_checks(
        content,
        [lineage.model_dump(mode="json", by_alias=True)],
    )

    assert failures == [{
        "commitment": "lineage-check",
        "eval": "program:lineage_ref",
        "verdict": "fail",
        "reason": "no dependence ref into the connection lineage",
    }]


def test_artifact_id_parity_with_parent():
    parent = pytest.importorskip("deepreason.ontology.artifact")
    from minireason.log import artifact_id

    interface = parent.Interface(commitments=["skeleton-wf"], refs=[])
    expected = parent.Artifact.compute_id("inline:hello", "utf8", interface)
    assert artifact_id("inline:hello", "utf8",
                       interface.model_dump(mode="json")) == expected
