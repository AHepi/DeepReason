"""Stage B process-observation constraints must be finitely repairable.

Live regression (run-f4fa6663e5412d64df943a5a22342baf, 2026-07-27): the
composer grouped every process-observation entry into one span.  The
single-leaf repair grant at ``/sections/0/ledger_entry_handles`` invited the
model to shrink the handles to one process entry, which deterministically
produced the coupled text violation — and the patch turn, which sees only the
baseline and the diagnostic envelope, had no way to learn the exact
harness-authored statement bytes.  Both contracts exhausted and the bridge
terminated ``BRIDGE_COMPOSITION_FAILED``.

These tests pin the convergent shape: the pack names which entries are
process observations, the coupled errors grant one-section repair authority,
the diagnostic carries the exact statement bytes, and one patch inside the
engaged preset's one-repair budget compiles a valid output.
"""

from __future__ import annotations

import json

import pytest

from deepreason.bridge.compose import (
    BridgeCompositionWireContractV2,
    CompositionContractError,
    CompositionRequestV1,
    _composition_pack,
)
from deepreason.bridge.models import (
    ClaimClass,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ProcessObservationV1,
)
from deepreason.bridge.operations import read_failure, read_status, write_failure
from deepreason.llm.repair import V6PatchRepairSession, diagnostic_from_error


_FORMAL_SEQ = 787


def _observation(subject_ref: str) -> ProcessObservationV1:
    return ProcessObservationV1.create(
        observation_kind="acceptance",
        formal_seq=_FORMAL_SEQ,
        subject_ref=subject_ref,
        related_refs=[],
    )


def _ledger_with_two_process_entries() -> tuple[
    ClaimLedgerV1, ProcessObservationV1, ProcessObservationV1
]:
    first = _observation("artifact-alpha")
    second = _observation("artifact-beta")
    entries = [
        ClaimLedgerEntryV1.create(
            claim_class=ClaimClass.RECORDED_OBSERVATION,
            claim=first.statement,
            process_observation_refs=[first.id],
        ),
        ClaimLedgerEntryV1.create(
            claim_class=ClaimClass.RECORDED_OBSERVATION,
            claim=second.statement,
            process_observation_refs=[second.id],
        ),
        ClaimLedgerEntryV1.create(
            claim_class=ClaimClass.ASSUMPTION,
            claim="The comparison assumes both logs replay deterministically.",
        ),
    ]
    ledger = ClaimLedgerV1.create(
        problem_ref="problem-live-regression",
        formal_seq=_FORMAL_SEQ,
        output_target="answer",
        entries=entries,
    )
    return ledger, first, second


def _contract(ledger: ClaimLedgerV1) -> BridgeCompositionWireContractV2:
    return BridgeCompositionWireContractV2(
        ledger,
        maximum_sections=4,
        desired_length_chars=4_096,
    )


def _grouped_wire() -> dict:
    return {
        "sections": [
            {
                "span_id": "S1",
                "text": "Both artifacts were recorded as accepted at seq 787.",
                "ledger_entry_handles": ["E1", "E2"],
            }
        ],
        "resolution": "answered",
    }


def test_grouped_process_observations_grant_one_section_repair_authority():
    ledger, first, second = _ledger_with_two_process_entries()
    contract = _contract(ledger)
    wire = contract.validate_value(_grouped_wire())

    with pytest.raises(CompositionContractError) as captured:
        contract.compile(wire)

    error = captured.value
    assert error.pointer == "/sections/0/ledger_entry_handles"
    assert error.authorized_pointers == ("/sections/0",)
    assert error.repair_scope == "/sections/0"
    assert error.instruction and "one patch" in error.instruction
    assert first.statement in error.allowed_detail
    assert second.statement in error.allowed_detail


def test_exact_text_mismatch_grants_both_leaves_and_exact_bytes():
    ledger, first, _second = _ledger_with_two_process_entries()
    contract = _contract(ledger)
    wire = contract.validate_value(
        {
            "sections": [
                {
                    "span_id": "S1",
                    "text": f"{first.statement} And more model prose.",
                    "ledger_entry_handles": ["E1"],
                }
            ],
            "resolution": "answered",
        }
    )

    with pytest.raises(CompositionContractError) as captured:
        contract.compile(wire)

    error = captured.value
    assert error.pointer == "/sections/0/text"
    assert error.authorized_pointers == (
        "/sections/0/ledger_entry_handles",
        "/sections/0/text",
    )
    assert first.statement in error.allowed_detail
    assert error.instruction and "byte-identical" in error.instruction


def test_live_shaped_session_converges_in_one_patch():
    """Replay the live failure shape offline and prove one-patch convergence."""

    ledger, first, _second = _ledger_with_two_process_entries()
    contract = _contract(ledger)
    session = V6PatchRepairSession(
        contract=contract.contract_id,
        schema=contract.model_json_schema(),
        initial_request="composition pack",
        retry_max=1,
    )

    turn0 = session.turn(0)
    raw0 = "```json\n" + json.dumps(_grouped_wire()) + "\n```"
    candidate = session.candidate_from_raw(turn0, raw0)
    with pytest.raises(CompositionContractError) as captured:
        contract.compile(contract.validate_value(candidate))
    envelope = session.note_invalid(turn0, raw0, captured.value)

    assert envelope.authorized_pointers == ("/sections/0",)
    diagnostic = envelope.diagnostics[0]
    assert first.statement in diagnostic.allowed
    assert diagnostic.instruction

    turn1 = session.turn(1)
    assert turn1.mode == "patch"
    # The patch prompt is the model's entire visible context: the exact
    # harness-authored statement must already be inside it.
    assert first.statement in turn1.request

    patch_raw = json.dumps(
        {
            "schema": "repair.patch.v1",
            "op": "replace",
            "path": "/sections/0",
            "value": {
                "span_id": "S1",
                "text": first.statement,
                "ledger_entry_handles": ["E1"],
            },
        }
    )
    repaired = session.candidate_from_raw(turn1, patch_raw)
    draft = contract.compile(contract.validate_value(repaired))

    assert draft.output is not None
    assert draft.output.sections[0].text == first.statement
    assert draft.output.sections[0].rendering_mode.value == "observation"


def test_text_mismatch_session_converges_by_patching_text():
    ledger, first, _second = _ledger_with_two_process_entries()
    contract = _contract(ledger)
    session = V6PatchRepairSession(
        contract=contract.contract_id,
        schema=contract.model_json_schema(),
        initial_request="composition pack",
        retry_max=1,
    )

    turn0 = session.turn(0)
    raw0 = json.dumps(
        {
            "sections": [
                {
                    "span_id": "S1",
                    "text": "A close paraphrase of the status statement.",
                    "ledger_entry_handles": ["E1"],
                }
            ],
            "resolution": "answered",
        }
    )
    candidate = session.candidate_from_raw(turn0, raw0)
    with pytest.raises(CompositionContractError) as captured:
        contract.compile(contract.validate_value(candidate))
    envelope = session.note_invalid(turn0, raw0, captured.value)

    assert envelope.authorized_pointers == (
        "/sections/0/ledger_entry_handles",
        "/sections/0/text",
    )
    assert first.statement in envelope.diagnostics[0].allowed

    patch_raw = json.dumps(
        {
            "schema": "repair.patch.v1",
            "op": "replace",
            "path": "/sections/0/text",
            "value": first.statement,
        }
    )
    repaired = session.candidate_from_raw(session.turn(1), patch_raw)
    draft = contract.compile(contract.validate_value(repaired))
    assert draft.output is not None
    assert draft.output.sections[0].text == first.statement


def test_v1_diagnostic_carries_instruction_and_exact_bytes():
    ledger, first, _second = _ledger_with_two_process_entries()
    contract = _contract(ledger)
    wire = contract.validate_value(_grouped_wire())
    with pytest.raises(CompositionContractError) as captured:
        contract.compile(wire)

    diagnostic = diagnostic_from_error(
        contract.contract_id,
        captured.value,
        contract.model_json_schema(),
    )
    assert diagnostic.repair_scope == "/sections/0"
    assert first.statement in diagnostic.allowed
    assert diagnostic.instruction


def test_composition_pack_marks_process_observations_only_for_v2():
    ledger, _first, _second = _ledger_with_two_process_entries()
    request = CompositionRequestV1(
        output_target="answer",
        formatting_profile="plain",
        desired_length_chars=4_096,
        maximum_sections=4,
    )

    v2_pack = _composition_pack(ledger, request, contract_version="v2")
    v2_payload = json.loads(v2_pack[v2_pack.index("\n\n") + 2 :])
    marked = [
        entry["handle"]
        for entry in v2_payload["ledger_entries"]
        if entry.get("process_observation")
    ]
    assert marked == ["E1", "E2"]
    assert "process_observation" not in v2_payload["ledger_entries"][2]
    assert "byte-identical" in v2_pack

    v1_pack = _composition_pack(ledger, request, contract_version="v1")
    assert "process_observation" not in v1_pack


def test_worker_failure_records_one_sanitized_detail_line(tmp_path):
    manifest_sha = "a" * 64
    result = write_failure(
        tmp_path,
        manifest_sha,
        "SchemaExhaustedError",
        detail=(
            "schema_exhausted: process-observation spans must reproduce the "
            "exact harness-authored status statement\nsecond line is dropped"
        ),
    )
    assert result.error_detail == (
        "schema_exhausted: process-observation spans must reproduce the "
        "exact harness-authored status statement"
    )
    status = read_status(tmp_path)
    assert status is not None and status.error_detail == result.error_detail
    stored = read_failure(tmp_path)
    assert stored is not None and stored.error_detail == result.error_detail


def test_worker_failure_detail_is_bounded_and_optional(tmp_path):
    manifest_sha = "b" * 64
    hostile = "x" * 500 + "\n key=SECRET"
    result = write_failure(tmp_path, manifest_sha, "RuntimeError", detail=hostile)
    assert result.error_detail is not None
    assert len(result.error_detail) <= 256
    assert "SECRET" not in result.error_detail

    bare = write_failure(tmp_path, manifest_sha, "RuntimeError")
    assert bare.error_detail is None
    assert write_failure(tmp_path, manifest_sha, "RuntimeError", detail="\x00\x01").error_detail is None
