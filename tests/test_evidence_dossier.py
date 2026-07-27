from __future__ import annotations

import json

import pytest

from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV1,
    RunInputProblemV1,
    attach_bound_evidence,
    bind_run_input,
    load_evidence_dossier,
    load_run_input,
    pack_dossier,
    render_dossier_pack,
    stage_attached_source,
    verify_run_input,
)
from deepreason.evidence.state import RunInputError
from deepreason.harness import Harness
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.ontology.artifact import RefRole


def _records(tmp_path):
    root = tmp_path / "run"
    provenance = AttachedSourceProvenanceV1(
        supplied_by="offline acceptance fixture",
        acquisition_method="pre-freeze attachment",
        note="No network operation occurs during the run.",
    )
    first = stage_attached_source(
        root,
        source_id="E1",
        title="Official bandwidth documentation",
        source_locator="urn:fixture:bandwidth",
        source_class="official_hardware_documentation",
        media_type="text/plain",
        content="Bandwidth is a finite transfer ceiling.",
        provenance=provenance,
        declared_entities=("memory bandwidth",),
        declared_facets=("bandwidth",),
    )
    second = stage_attached_source(
        root,
        source_id="E2",
        title="Quantisation paper",
        source_locator="urn:fixture:quantisation",
        source_class="primary_paper",
        media_type="text/plain",
        content="Quantisation changes the numerical representation.",
        provenance=provenance,
        declared_entities=("quantisation",),
        declared_facets=("model approximation",),
    )
    dossier = EvidenceDossierV1.create(
        problem_ref="pi-evidence-dossier",
        sources=(first, second),
        total_byte_count=first.byte_count + second.byte_count,
        creation_provenance=provenance,
    )
    run_input = RunInputManifestV1.create(
        problem=RunInputProblemV1(
            id="pi-evidence-dossier",
            description="Test one frozen evidence dossier.",
            criteria=("quantify", "state assumptions"),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    return root, run_input, dossier


def test_run_input_binds_idempotently_and_verifies_every_source(tmp_path):
    root, run_input, dossier = _records(tmp_path)
    first = bind_run_input(run_input, dossier, root)
    second = bind_run_input(run_input, dossier, root)

    assert first == second
    assert load_run_input(root) == run_input
    assert load_evidence_dossier(root) == dossier
    assert verify_run_input(root) == {
        "valid": True,
        "run_input_digest": run_input.run_input_digest,
        "evidence_dossier_digest": dossier.dossier_digest,
        "source_count": 2,
        "source_bytes": dossier.total_byte_count,
    }


def test_missing_source_blob_fails_before_either_input_record_is_bound(tmp_path):
    root, run_input, dossier = _records(tmp_path)
    missing = dossier.sources[0].model_copy(
        update={"content_ref": "f" * 64, "content_sha256": "f" * 64}
    )
    bad = EvidenceDossierV1.create(
        problem_ref=dossier.problem_ref,
        sources=(missing, dossier.sources[1]),
        total_byte_count=missing.byte_count + dossier.sources[1].byte_count,
        creation_provenance=dossier.creation_provenance,
    )
    bad_input = RunInputManifestV1.create(
        problem=run_input.problem,
        evidence_dossier_digest=bad.dossier_digest,
    )

    with pytest.raises(RunInputError, match="RUN_INPUT_SOURCE_UNAVAILABLE"):
        bind_run_input(bad_input, bad, root)
    assert not (root / "run-input.json").exists()
    assert not (root / "evidence-dossier.json").exists()


def test_bound_input_conflict_and_blob_tampering_fail_closed(tmp_path):
    root, run_input, dossier = _records(tmp_path)
    bind_run_input(run_input, dossier, root)
    other = RunInputManifestV1.create(
        problem=run_input.problem.model_copy(update={"description": "Different problem bytes"}),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    with pytest.raises(RunInputError, match="RUN_INPUT_CONFLICT"):
        bind_run_input(other, dossier, root)

    source = dossier.sources[0]
    blob_path = root / "blobs" / source.content_ref[:2] / source.content_ref
    blob_path.write_bytes(b"tampered")
    with pytest.raises(RunInputError, match="RUN_INPUT_SOURCE_UNAVAILABLE"):
        verify_run_input(root)


def test_bound_input_symlink_substitution_fails_closed(tmp_path):
    root, run_input, dossier = _records(tmp_path)
    bind_run_input(run_input, dossier, root)
    original = root / "run-input.json"
    displaced = root / "displaced-run-input.json"
    original.rename(displaced)
    original.symlink_to(displaced.name)

    with pytest.raises(RunInputError, match="RUN_INPUT_FILE_UNSAFE"):
        load_run_input(root)


def test_dossier_packing_is_bounded_deterministic_and_resurfaces_underexposed_sources(
    tmp_path,
):
    root, run_input, dossier = _records(tmp_path)
    bind_run_input(run_input, dossier, root)
    kwargs = dict(
        root=root,
        run_input=run_input,
        dossier=dossier,
        work_order_ref="sha256:" + "a" * 64,
        query="compare relevant material",
        state_fence="seq:12",
        maximum_sources=1,
        maximum_excerpt_bytes_per_source=20,
        maximum_total_excerpt_bytes=20,
        exposure_counts={"E1": 7, "E2": 0},
    )
    first = pack_dossier(**kwargs)
    second = pack_dossier(**kwargs)

    assert first == second
    assert first.selected_source_ids == ("E2",)
    assert first.excluded_source_ids == ("E1",)
    assert sum(item.byte_count for item in first.excerpts) <= 20
    rendered = render_dossier_pack(
        blobs=Harness(root).blobs,
        dossier=dossier,
        receipt=first,
    )
    assert "BEGIN UNTRUSTED SOURCE DATA" in rendered
    assert "do not establish truth" in rendered
    assert "Quantisation" in rendered


def test_bound_sources_create_distinct_provenance_reliability_and_evidence_records(
    tmp_path,
):
    root, run_input, dossier = _records(tmp_path)
    bind_run_input(run_input, dossier, root)
    harness = Harness(root)
    problem = harness.register_problem(
        Problem(
            id=run_input.problem.id,
            description=run_input.problem.description,
            criteria=list(run_input.problem.criteria),
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
    assert set(attached) == {"E1", "E2"}
    for refs in attached.values():
        assert len(set(refs.values())) == 3
        evidence = harness.state.artifacts[refs["candidate_evidence_ref"]]
        assert any(
            ref.role == RefRole.DEPENDENCE
            and ref.target == refs["source_reliability_ref"]
            for ref in evidence.interface.refs
        )
        assert any(
            ref.role == RefRole.MENTION and ref.target == refs["source_record_ref"]
            for ref in evidence.interface.refs
        )
        source_record = harness.state.artifacts[refs["source_record_ref"]]
        payload = json.loads(source_record.content_ref.removeprefix("inline:"))
        assert payload["epistemic_notice"].startswith("This record preserves")
