"""E3.1 formal submission binding (scripts/e31_benchmark/submission.py).

Submissions are {theorem_name: proof_body} mappings; the Lean source is
reconstructed server-side from the immutable skeleton and hash-compared on
its non-proof regions before any verification.  These tests exercise the
reconstruction/binding layer only — no Lean toolchain is invoked.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from deepreason.canonical import sha256_hex  # noqa: E402

from e31_benchmark import axiom_domains  # noqa: E402
from e31_benchmark.submission import (  # noqa: E402
    SubmissionError,
    bind_submission,
    load_skeleton,
    split_regions,
)

SEED = "20260713/axiom/0"


@pytest.fixture(scope="module")
def skeleton():
    domain = axiom_domains.generate_domain(SEED)
    targets = axiom_domains.enumerate_targets(domain)
    assert targets
    source = axiom_domains.render_lean(domain, targets)
    request = axiom_domains.pinned_request(source.encode(), targets)
    return load_skeleton(source, request)


def _plausible_submission(skeleton) -> dict[str, str]:
    """Syntactically plausible indented tactic bodies, one per target."""

    return {
        name: f"  rw [ax1]\n  simp [ax2, ax3]\n  -- close {name}\n  rfl"
        for name in skeleton.regions.theorem_names
    }


def test_proof_hole_replacement_accepted(skeleton):
    submission = _plausible_submission(skeleton)
    bound = bind_submission(skeleton, submission)

    # Every proof hole was filled with the submitted body, verbatim.
    regions = split_regions(bound.source)
    for name, body in submission.items():
        assert regions.proofs[name].startswith(body)
        assert "sorry" not in regions.proofs[name]
    assert "E31-SKELETON" not in bound.source  # no placeholder survives

    # Non-proof regions are byte-faithful to the skeleton...
    assert bound.non_proof_fingerprint == skeleton.regions.non_proof_fingerprint
    # ... and source_ref was computed only after reconstruction: it pins the
    # reconstructed bytes, and the request differs from the skeleton's in
    # source_ref alone.
    assert bound.source_ref == sha256_hex(bound.source.encode())
    assert bound.request.source_ref == bound.source_ref
    reconstructed = bound.request.model_dump(mode="json")
    original = skeleton.request.model_dump(mode="json")
    differing = {
        key for key in original if reconstructed[key] != original[key]
    }
    assert differing == {"source_ref"}
    assert bound.request.allow_sorry is False


def test_statement_rewrite_to_true_rejected(skeleton):
    """A proof body that escapes its hole to restate the target as ``True``
    lands in the non-proof region on re-parse and is rejected by the
    hash comparison before any verification."""

    submission = _plausible_submission(skeleton)
    victim = skeleton.regions.theorem_names[0]
    submission[victim] = (
        "  exact trivial\n"
        f"theorem {victim} : True := by\n"
        "  trivial"
    )
    with pytest.raises(SubmissionError):
        bind_submission(skeleton, submission)

    # Variant: rewriting a DIFFERENT theorem's statement via escape is
    # equally a non-proof mutation.
    submission = _plausible_submission(skeleton)
    submission[victim] = (
        "  exact trivial\n"
        "theorem freshly_smuggled : True := by\n"
        "  trivial"
    )
    with pytest.raises(SubmissionError, match="non-proof|escaped"):
        bind_submission(skeleton, submission)


def test_axiom_mutation_rejected(skeleton):
    """A proof body that injects or rewrites an axiom at column 0 changes
    the non-proof fingerprint and is rejected."""

    submission = _plausible_submission(skeleton)
    victim = skeleton.regions.theorem_names[-1]
    submission[victim] = (
        "  exact trivial\n"
        "axiom convenient : ∀ (α : Sort _) (a b : α), a = b"
    )
    with pytest.raises(SubmissionError, match="non-proof"):
        bind_submission(skeleton, submission)


def test_submission_keys_must_match_the_skeleton(skeleton):
    submission = _plausible_submission(skeleton)
    submission.pop(skeleton.regions.theorem_names[0])
    with pytest.raises(SubmissionError, match="missing"):
        bind_submission(skeleton, submission)
    submission = _plausible_submission(skeleton)
    submission["not_a_target"] = "  rfl"
    with pytest.raises(SubmissionError, match="unknown"):
        bind_submission(skeleton, submission)


def test_sorry_and_empty_bodies_rejected(skeleton):
    submission = _plausible_submission(skeleton)
    victim = skeleton.regions.theorem_names[0]
    for bad in ("  sorry", "   ", "  first | rfl | sorry"):
        submission[victim] = bad
        with pytest.raises(SubmissionError):
            bind_submission(skeleton, submission)


def test_mutated_skeleton_refuses_to_bind(skeleton):
    """The immutable-skeleton invariant: axioms, statements and options come
    only from bytes that hash to the pinned source_ref."""

    tampered = skeleton.source.replace("class", "structure", 1)
    with pytest.raises(SubmissionError, match="source_ref"):
        load_skeleton(tampered, skeleton.request)
