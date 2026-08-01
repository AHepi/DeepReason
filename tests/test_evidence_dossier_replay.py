from __future__ import annotations

from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV1,
    RunInputProblemV1,
    attach_bound_evidence,
    bind_run_input,
    stage_attached_source,
    verify_run_input,
)
from deepreason.harness import Harness
from deepreason.ontology import Problem, ProblemProvenance


def test_attached_evidence_and_input_identity_survive_replay(tmp_path):
    root = tmp_path / "replay"
    provenance = AttachedSourceProvenanceV1(
        supplied_by="offline fixture",
        acquisition_method="pre-freeze copy",
    )
    source = stage_attached_source(
        root,
        source_id="E1",
        title="Synthetic machine profile",
        source_locator="urn:fixture:machine",
        source_class="synthetic_assumption",
        media_type="text/plain",
        content="Host-to-device bandwidth is a declared synthetic bound.",
        provenance=provenance,
    )
    dossier = EvidenceDossierV1.create(
        problem_ref="pi-replay-input",
        sources=(source,),
        total_byte_count=source.byte_count,
        creation_provenance=provenance,
    )
    run_input = RunInputManifestV1.create(
        problem=RunInputProblemV1(
            id="pi-replay-input",
            description="Replay attached input.",
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    harness = Harness(root)
    problem = harness.register_problem(
        Problem(
            id=run_input.problem.id,
            description=run_input.problem.description,
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    attached = attach_bound_evidence(
        harness,
        run_input=run_input,
        dossier=dossier,
        problem_id=problem.id,
    )

    replayed = Harness(root)
    assert verify_run_input(root)["run_input_digest"] == run_input.run_input_digest
    for artifact_ref in attached["E1"].values():
        assert replayed.state.artifacts[artifact_ref] == harness.state.artifacts[artifact_ref]
