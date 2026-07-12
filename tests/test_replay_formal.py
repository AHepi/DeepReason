from __future__ import annotations

from deepreason.harness import Harness
from deepreason.ontology import Status
from deepreason.workloads.formal import (
    FormalClaim,
    FormalMismatchTest,
    FormalWorkloadSpec,
    FormalizationRelation,
    PinnedLeanRequest,
    register_formal_workflow,
)


def test_formal_artifacts_and_explicit_support_replay_from_event_log(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    statement = "The empty list has length zero."
    source_ref = harness.blobs.put(b"theorem empty_length : [].length = 0 := by rfl\n")
    spec = FormalWorkloadSpec(
        claim=FormalClaim(statement=statement),
        request=PinnedLeanRequest(
            toolchain_id="lean4@4.19.0",
            source_ref=source_ref,
            target_theorems=["empty_length"],
        ),
        relation=FormalizationRelation(
            informal_target=statement,
            theorem="empty_length",
            scope="Lean lists",
            counterconditions=("A nonstandard length function is intended",),
            mismatch_tests=(
                FormalMismatchTest(
                    id="custom-length",
                    case="Replace List.length with an unrelated function",
                    expected_informal="outside scope",
                    expected_formal="not represented",
                ),
            ),
        ),
        explicit_formal_dependence=True,
    )
    artifacts = register_formal_workflow(harness, spec)
    expected_dep = set(harness.state.dep)
    expected_ids = set(harness.state.artifacts)

    reopened = Harness(root)

    assert set(reopened.state.artifacts) == expected_ids
    assert set(reopened.state.dep) == expected_dep
    assert reopened.state.status[artifacts.theorem.id] == Status.ACCEPTED
    assert reopened.state.status[artifacts.relation.id] == Status.ACCEPTED
    assert reopened.state.status[artifacts.claim.id] == Status.ACCEPTED

