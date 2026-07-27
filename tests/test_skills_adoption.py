import pytest

from deepreason.harness import Harness
from deepreason.ontology import Commitment, Interface, Provenance, Ref, Status
from deepreason.ontology.artifact import RefRole
from deepreason.skills.adoption import (
    CapsuleDependenceError,
    adopt_commitments,
    capsule_ref,
    import_capsule,
    validate_capsule_refs,
)
from deepreason.skills.models import PassedCommitmentDefinition, SkillCapsule


def _capsule(commitment):
    return SkillCapsule.create(
        problem_signature="positive marker tests",
        accepted_source_structure=("check for the required semantic marker",),
        scope=("text claims",),
        source_owned_counterconditions=("marker semantics may differ",),
        passed_commitments=(PassedCommitmentDefinition(definition=commitment),),
        toolchains=(),
        dependency_topology=(),
        unresolved_conditions=(),
        overturn_conditions=("the marker is not necessary",),
        source_artifact_id="source-a",
        source_event_seq=7,
        source_snapshot_digest="3" * 64,
        source_config_provenance=("run-manifest:none",),
        distiller_version="v1",
    )


def test_capsule_mention_is_support_inert_and_dependence_is_rejected(tmp_path):
    harness = Harness(tmp_path / "run")
    capsule = _capsule(Commitment(id="k-marker", eval="predicate:'marker' in content"))
    imported = import_capsule(harness, capsule)
    assert capsule_ref(imported.id).role == RefRole.MENTION
    assert not [edge for edge in harness.state.dep if imported.id in edge]
    with pytest.raises(CapsuleDependenceError):
        capsule_ref(imported.id, RefRole.DEPENDENCE)
    bad = Interface(refs=[Ref(target=imported.id, role=RefRole.DEPENDENCE)])
    with pytest.raises(CapsuleDependenceError):
        validate_capsule_refs(bad, (imported.id,))


def test_adopted_commitment_binds_new_identity_and_reruns_now(tmp_path):
    harness = Harness(tmp_path / "run")
    commitment = Commitment(id="k-marker", eval="predicate:'marker' in content")
    capsule = _capsule(commitment)
    candidate = harness.create_artifact(
        "claim without required token",
        provenance=Provenance(role="conjecturer"),
    )
    result = adopt_commitments(harness, candidate, capsule, ("k-marker",))
    adopted = harness.state.artifacts[result.adopted_candidate_id]
    assert adopted.id != candidate.id
    assert adopted.interface.commitments == ["k-marker"]
    assert result.evaluations[0].verdict == "fail"
    assert harness.state.status[adopted.id] == Status.REFUTED
    assert harness.blobs.get(result.evaluations[0].trace_ref)
    assert capsule.id not in {target for source, target in harness.state.dep if source == adopted.id}
