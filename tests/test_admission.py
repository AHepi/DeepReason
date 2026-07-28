"""Admission v1: deterministic parsing, frozen dossiers, and run binding."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pytest

from deepreason.admission import (
    PARSER_VERSION,
    AdmissionError,
    AdmissionInput,
    admission_store,
    admit_sources,
    sniff_media_type,
)
from deepreason.admission.parse import MAX_BLOCK_BYTES, MAX_SOURCE_BYTES
from deepreason.admission.store import AdmissionStoreError
from deepreason.evidence.models import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV2,
)
from deepreason.evidence.state import load_evidence_dossier, verify_run_input


PROVENANCE = AttachedSourceProvenanceV1(
    supplied_by="tests",
    acquisition_method="fixture",
    note=None,
)

MARKDOWN = (
    "# Study of Widgets\n"
    "\n"
    "Widgets are made of parts. This paragraph describes them at length.\n"
    "It continues on a second line.\n"
    "\n"
    "## Results\n"
    "\n"
    "| metric | value |\n"
    "|--------|-------|\n"
    "| speed  | 42    |\n"
    "\n"
    "The results paragraph interprets the table.\n"
).encode("utf-8")

CSV = (
    "name,score,grade\n"
    "alpha,10,A\n"
    "beta,20,B\n"
    "gamma,,A\n"
    "delta,40,C\n"
).encode("utf-8")


def _admit(*inputs, **kwargs):
    return admit_sources(
        [AdmissionInput(locator=f"input-{i}", data=data) for i, data in enumerate(inputs)],
        problem_ref="question-" + "0" * 32,
        provenance=PROVENANCE,
        **kwargs,
    )


def test_admission_is_deterministic_across_invocations():
    first, _ = _admit(MARKDOWN, CSV)
    second, _ = _admit(MARKDOWN, CSV)
    assert first.dossier_digest == second.dossier_digest
    assert first.parser_version == PARSER_VERSION
    assert [b.id for b in first.blocks] == [b.id for b in second.blocks]


def test_media_types_are_sniffed_from_content_alone():
    assert sniff_media_type(MARKDOWN)[0] == "text/markdown"
    assert sniff_media_type(CSV)[0] == "text/csv"
    assert sniff_media_type(b"a\tb\nc\td\n")[0] == "text/tab-separated-values"
    assert sniff_media_type(b"just prose\n\nmore prose\n")[0] == "text/plain"
    media, adapter = sniff_media_type(b"%PDF-1.7 ...")
    assert media == "application/pdf" and "deepreason[admit]" in adapter
    assert sniff_media_type(b"\x00\x01\x02")[0] == "application/octet-stream"


def test_span_blocks_are_exact_byte_slices_of_the_source():
    dossier, _ = _admit(MARKDOWN)
    source_digest = hashlib.sha256(MARKDOWN).hexdigest()
    span_blocks = [b for b in dossier.blocks if b.text is None]
    assert span_blocks
    for block in span_blocks:
        assert block.source_sha256 == source_digest
        slice_text = MARKDOWN[block.span_start : block.span_end].decode("utf-8")
        assert hashlib.sha256(slice_text.encode("utf-8")).hexdigest() == block.text_sha256


def test_markdown_segmentation_yields_sections_paragraphs_and_tables():
    dossier, report = _admit(MARKDOWN)
    kinds = report.block_counts
    assert kinds.get("section") == 2
    assert kinds.get("table") == 1
    assert kinds.get("paragraph", 0) >= 2
    titles = {b.title for b in dossier.blocks if b.kind == "section"}
    assert titles == {"Study of Widgets", "Results"}
    assert report.tier_counts == {"evidence": len(dossier.blocks)}


def test_long_paragraphs_split_on_line_boundaries_within_the_ceiling():
    body = ("word " * 200 + "\n") * 20
    data = body.encode("utf-8")
    dossier, _ = _admit(data)
    paragraphs = [b for b in dossier.blocks if b.kind == "paragraph"]
    assert len(paragraphs) > 1
    for block in paragraphs:
        assert block.span_end - block.span_start <= MAX_BLOCK_BYTES
        # Splits never cut a line in half.
        assert data[block.span_end : block.span_end + 1] in {b"\n", b""}


def test_csv_projection_blocks_are_deterministic_and_span_true():
    dossier, report = _admit(CSV)
    assert report.block_counts == {"csv_schema": 1, "csv_stats": 1, "csv_sample": 1}
    stats = next(b for b in dossier.blocks if b.kind == "csv_stats")
    assert "min=10" in stats.text and "max=40" in stats.text
    assert "median=20" in stats.text
    schema = next(b for b in dossier.blocks if b.kind == "csv_schema")
    assert "dtype=int" in schema.text and "nulls=1" in schema.text
    sample = next(b for b in dossier.blocks if b.kind == "csv_sample")
    assert sample.span_start == 0 and sample.text is None
    assert CSV[sample.span_start : sample.span_end].decode("utf-8").startswith(
        "name,score,grade"
    )


def test_refusals_are_typed_and_never_silent():
    oversized = b"x" * (MAX_SOURCE_BYTES + 1)
    dossier, report = _admit(MARKDOWN, b"", b"%PDF-1.7", b"\xff\xfe\x00", oversized)
    codes = sorted(refusal["code"] for refusal in report.refusals)
    assert codes == [
        "ADMISSION_MEDIA_UNSUPPORTED",
        "ADMISSION_SOURCE_EMPTY",
        "ADMISSION_SOURCE_TOO_LARGE",
        "ADMISSION_SOURCE_UNREADABLE",
    ]
    assert len(dossier.sources) == 1
    unsupported = next(
        r for r in dossier.refusals if r.code == "ADMISSION_MEDIA_UNSUPPORTED"
    )
    assert "deepreason[admit]" in unsupported.detail


def test_every_source_refused_is_a_typed_error():
    with pytest.raises(AdmissionError) as captured:
        _admit(b"%PDF-1.7 only pdfs here")
    assert captured.value.code == "ADMISSION_MEDIA_UNSUPPORTED"


def test_block_budget_breach_refuses_unless_partial_is_acknowledged(monkeypatch):
    monkeypatch.setattr("deepreason.admission.parse.MAX_BLOCKS_PER_SOURCE", 3)
    many = ("paragraph one.\n\n" * 10).encode("utf-8")
    with pytest.raises(AdmissionError) as captured:
        _admit(many)
    assert captured.value.code == "ADMISSION_BLOCK_BUDGET_EXCEEDED"

    dossier, report = _admit(many, allow_partial=True)
    assert len(dossier.blocks) == 3
    assert report.refusals[0]["code"] == "ADMISSION_BLOCK_BUDGET_EXCEEDED"
    assert "first 3 of" in report.refusals[0]["detail"]


def test_parser_version_binds_into_the_dossier_digest():
    dossier, _ = _admit(MARKDOWN)
    other = EvidenceDossierV2.create(
        problem_ref=dossier.problem_ref,
        parser_version="admission-parser.v999",
        sources=dossier.sources,
        blocks=dossier.blocks,
        refusals=dossier.refusals,
        total_byte_count=dossier.total_byte_count,
        creation_provenance=dossier.creation_provenance,
    )
    assert other.dossier_digest != dossier.dossier_digest


def test_store_round_trips_dossiers_and_verified_source_bytes(tmp_path):
    dossier, _ = _admit(MARKDOWN, CSV)
    store = admission_store(tmp_path / "admission")
    contents = {
        hashlib.sha256(data).hexdigest(): data for data in (MARKDOWN, CSV)
    }
    store.save(dossier, contents)
    loaded = store.load(dossier.dossier_digest)
    assert loaded == dossier
    assert store.source_bytes(loaded) == contents
    assert store.list_digests() == (dossier.dossier_digest,)
    with pytest.raises(AdmissionStoreError) as captured:
        store.load("f" * 64)
    assert captured.value.code == "ADMISSION_DOSSIER_UNKNOWN"


def test_preparation_binds_an_admitted_dossier_into_run_identity(
    tmp_path, monkeypatch
):
    from tests.test_run_preparation_service import (
        _profile,
        _request,
        _service,
    )
    from deepreason.provider_profile import write_provider_profile
    from deepreason.preparation import RunPreparationError, _question_digest

    question = "What do the widget studies show?"
    problem_ref = f"question-{_question_digest(question)[:32]}"
    dossier, _ = admit_sources(
        [AdmissionInput(locator="study.md", data=MARKDOWN)],
        problem_ref=problem_ref,
        provenance=PROVENANCE,
    )
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    admission_store().save(
        dossier, {hashlib.sha256(MARKDOWN).hexdigest(): MARKDOWN}
    )

    profile_path = tmp_path / "provider.yaml"
    write_provider_profile(_profile(), profile_path)
    calls: list = []
    service = _service(tmp_path, calls)

    prepared = service.prepare(
        _request(
            profile_path,
            question=question,
            dossier_digest=dossier.dossier_digest,
        )
    )
    root = prepared.root
    bound = load_evidence_dossier(root)
    assert isinstance(bound, EvidenceDossierV2)
    assert bound.dossier_digest == dossier.dossier_digest
    report = verify_run_input(root)
    assert report["valid"] is True
    assert report["evidence_dossier_digest"] == dossier.dossier_digest
    assert report["source_count"] == 1

    # The dossier joins the request identity: the same question without it
    # prepares a different managed run.
    plain = service.prepare(_request(profile_path, question=question))
    assert plain.root != prepared.root

    # A dossier admitted for a different question is refused, typed.
    with pytest.raises(RunPreparationError) as captured:
        service.prepare(
            _request(
                profile_path,
                question="A different question entirely?",
                dossier_digest=dossier.dossier_digest,
            )
        )
    assert "ADMISSION_PROBLEM_MISMATCH" in str(captured.value)


def test_admit_cli_prints_digest_and_inspects_stored_dossier(
    tmp_path, monkeypatch, capsys
):
    from deepreason.cli.main import main

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    study = tmp_path / "study.md"
    study.write_bytes(MARKDOWN)
    data = tmp_path / "data.csv"
    data.write_bytes(CSV)

    assert main(["admit", str(study), str(data), "--problem", "What?"]) == 0
    payload = json.loads(capsys.readouterr().out)
    digest = payload["dossier_digest"]
    assert payload["sources"] == 2
    assert payload["blocks"]["csv_schema"] == 1
    assert digest in payload["next_action"]

    assert main(["admit", "--inspect", digest]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["dossier_digest"] == digest
    assert inspected["parser_version"] == PARSER_VERSION
    assert inspected["tiers"] == {"evidence": inspected["blocks"]}

    assert main(["admit", str(study)]) == 1
    assert "ADMISSION_PROBLEM_REQUIRED" in capsys.readouterr().err


def test_v2_dossier_packs_through_the_existing_run_exposure_path(tmp_path):
    """Admitted V2 dossiers ride the same retrieval exposure as V1: the
    packer selects sources, stages excerpts, and mints its receipt."""

    from deepreason.evidence.dossier import pack_dossier
    from deepreason.evidence.models import RunInputManifestV2, RunInputProblemV2
    from deepreason.storage.blobs import BlobStore

    dossier, _ = _admit(MARKDOWN)
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id=dossier.problem_ref,
            description="What do the widget studies show?",
            criteria=(),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
        brain_snapshot_digest=None,
    )
    BlobStore(tmp_path / "blobs").put(MARKDOWN)
    receipt = pack_dossier(
        root=tmp_path,
        run_input=run_input,
        dossier=dossier,
        work_order_ref="sha256:" + "a" * 64,
        query="widgets",
        state_fence="fence-0",
        maximum_sources=4,
        maximum_excerpt_bytes_per_source=2_048,
        maximum_total_excerpt_bytes=8_192,
    )
    assert receipt.selected_source_ids == tuple(
        source.id for source in dossier.sources
    )
    assert receipt.excerpts
