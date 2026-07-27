import pytest

from deepreason.harness import Harness
from deepreason.ontology import Commitment, Interface, Provenance
from deepreason.rules.crit import crit_program
from deepreason.skills.distill import NegativeCaseLawError, distill_capsule
from deepreason.skills.models import CapsuleDraft
from deepreason.skills.validate import DistillationSourceError, validate_distillation_source


def _source_run(tmp_path):
    harness = Harness(tmp_path / "source")
    commitment = Commitment(id="k-good", eval="predicate:'good' in content")
    harness.register_commitment(commitment)
    accepted = harness.create_artifact(
        "good constructive partition with a stable boundary",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer"),
    )
    failed = harness.create_artifact(
        "bad rival copies an unsafe boundary and loses important cases immediately",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer"),
    )
    crit_program(harness, failed.id)
    return harness, accepted, failed


def test_distillation_is_accepted_only_positive_and_deterministic(tmp_path):
    harness, accepted, failed = _source_run(tmp_path)
    seq = harness._next_seq - 1
    source = validate_distillation_source(
        harness.root,
        source_event_seq=seq,
        accepted_artifact_id=accepted.id,
        distiller_version="v1",
    )
    assert [item.id for item in source.passed_commitments] == ["k-good"]
    draft = CapsuleDraft(
        problem_signature="bounded partition problems",
        accepted_source_structure=("split work at a stable semantic boundary",),
        scope=("finite partitions",),
        source_owned_counterconditions=("the cases remain exhaustive",),
        unresolved_conditions=("unknown distribution shift",),
        overturn_conditions=("a valid input belongs to no partition",),
    )
    assert distill_capsule(source, draft) == distill_capsule(source, draft)
    with pytest.raises(DistillationSourceError, match="not accepted"):
        validate_distillation_source(
            harness.root,
            source_event_seq=seq,
            accepted_artifact_id=failed.id,
            distiller_version="v1",
        )


def test_distillation_rejects_negative_case_law_and_web_bodies(tmp_path):
    harness, accepted, _failed = _source_run(tmp_path)
    source = validate_distillation_source(
        harness.root,
        source_event_seq=harness._next_seq - 1,
        accepted_artifact_id=accepted.id,
        distiller_version="v1",
    )
    with pytest.raises(NegativeCaseLawError):
        distill_capsule(
            source,
            CapsuleDraft(
                problem_signature="x",
                accepted_source_structure=("criticism transcript: copied failure",),
                overturn_conditions=("x",),
            ),
        )
    with pytest.raises(NegativeCaseLawError):
        distill_capsule(
            source,
            CapsuleDraft(
                problem_signature="x",
                accepted_source_structure=("<script>window.bad = true</script>",),
                overturn_conditions=("x",),
            ),
        )
