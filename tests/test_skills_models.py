import pytest
from pydantic import ValidationError

from deepreason.skills.models import CapsuleDraft, SkillCapsule
from deepreason.workloads.text import AnalogyClaim, ReasoningCandidateProposal, proposal_envelope


def _capsule(label="sorting"):
    return SkillCapsule.create(
        problem_signature=label,
        accepted_source_structure=(f"partition {label} work into bounded cases",),
        scope=("finite inputs",),
        source_owned_counterconditions=("the partition remains exhaustive",),
        passed_commitments=(),
        toolchains=(),
        dependency_topology=(),
        unresolved_conditions=("cost outside the observed range",),
        overturn_conditions=("a case falls outside the partition",),
        source_artifact_id=f"artifact-{label}",
        source_event_seq=4,
        source_snapshot_digest="1" * 64,
        source_config_provenance=("run-manifest:none",),
        distiller_version="distiller-v1",
    )


def test_capsule_is_content_addressed_and_strict():
    one = _capsule()
    two = _capsule()
    assert one == two
    assert one.id == two.id
    with pytest.raises(ValidationError, match="canonical content"):
        SkillCapsule.model_validate({**one.model_dump(mode="json", by_alias=True), "id": "0" * 64})
    with pytest.raises(ValidationError):
        CapsuleDraft(
            problem_signature="x",
            accepted_source_structure=("x",),
            overturn_conditions=("x",),
            refuted_examples=("forbidden",),
        )


def test_analogy_is_explicit_refutable_content_not_created_by_citation():
    proposal = ReasoningCandidateProposal(
        claim="use the same partition boundary",
        mechanism="the current cases share the source split",
        counterconditions=("the split is not exhaustive",),
        typicality=0.4,
        optional_refs=("capsule-id",),
    )
    assert proposal_envelope(proposal).analogy is None
    with pytest.raises(ValidationError):
        AnalogyClaim(
            source_memory_refs=("capsule-id",),
            shared_structure=(),
            disanalogies=("different scale",),
            transfer_claims=("try the partition",),
            overturn_conditions=("partition misses a case",),
        )
    analogy = AnalogyClaim(
        source_memory_refs=("capsule-id",),
        shared_structure=("both problems split on one invariant",),
        disanalogies=("the current input is unbounded",),
        transfer_claims=("test a bounded partition first",),
        adopted_commitment_refs=("k-partition",),
        overturn_conditions=("the invariant does not cover every branch",),
    )
    assert proposal_envelope(proposal.model_copy(update={"analogy": analogy})).analogy == analogy
