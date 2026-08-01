"""Append-only persistence and isolated replay for grounded bridge events."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from deepreason.bridge.events import BridgeAction
from deepreason.bridge.ledger import (
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV1,
)
from deepreason.bridge.models import (
    BridgeOutputV1,
    BridgeValidationReportV1,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ClaimUseV1,
    GroundingFindingV1,
    GroundingReviewV1,
)
from deepreason.harness import Harness, ReadOnlyHarnessError
from deepreason.invariants import verify_root
from deepreason.ontology import Commitment, LLMCall, Rule


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


def _records(formal_seq: int = 0):
    catalog = ClaimLedgerInputCatalogV1.create(
        problem_ref="problem-1",
        formal_seq=formal_seq,
        problem_text="What value is supported by the supplied source?",
        output_target="answer",
        items=[
            ClaimLedgerCatalogItemV1(
                handle="S1",
                kind="source",
                ref="source-1",
                excerpt="The source records a value of seven.",
            )
        ],
    )
    entry = ClaimLedgerEntryV1.create(
        claim_class="source_fact",
        claim="The source records a value of seven.",
        source_refs=["source-1"],
    )
    ledger = ClaimLedgerV1.create(
        problem_ref=catalog.problem_ref,
        formal_seq=catalog.formal_seq,
        output_target=catalog.output_target,
        entries=[entry],
    )
    ledger_report = BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        valid=True,
        findings=[],
    )
    claim_use = ClaimUseV1.create(
        span_id="span-1",
        text=entry.claim,
        rendering_mode="fact",
        ledger_entry_ids=[entry.id],
    )
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[claim_use],
        resolution="answered",
    )
    output_report = BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        valid=True,
        findings=[],
    )
    grounding = GroundingFindingV1.create(
        span_id="span-1",
        status="supported",
        ledger_entry_ids=[entry.id],
        checked_refs=["source-1"],
    )
    review = GroundingReviewV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        findings=[grounding],
        passed=True,
    )
    return {
        "catalog": catalog,
        "entry": entry,
        "ledger": ledger,
        "ledger_report": ledger_report,
        "claim_use": claim_use,
        "output": output,
        "output_report": output_report,
        "grounding": grounding,
        "review": review,
    }


def _record_complete_bridge(harness: Harness, records, *, llm=None):
    ledger_event = harness.record_bridge_event(
        BridgeAction.LEDGER_CREATED,
        records=[
            ("bridge-ledger-input-catalog", records["catalog"]),
            ("bridge-ledger-entry", records["entry"]),
            ("bridge-claim-ledger", records["ledger"]),
        ],
        llm=llm,
    )
    harness.record_bridge_event(
        BridgeAction.LEDGER_VALIDATED,
        inputs=[records["ledger"].id],
        records=[("bridge-validation-report", records["ledger_report"])],
    )
    harness.record_bridge_event(
        BridgeAction.OUTPUT_COMPOSED,
        inputs=[records["ledger"].id],
        records=[
            ("bridge-claim-use", records["claim_use"]),
            ("bridge-output", records["output"]),
        ],
    )
    harness.record_bridge_event(
        BridgeAction.OUTPUT_VALIDATED,
        inputs=[records["ledger"].id, records["output"].id],
        records=[("bridge-validation-report", records["output_report"])],
    )
    harness.record_bridge_event(
        BridgeAction.GROUNDED_REVIEWED,
        inputs=[records["ledger"].id, records["output"].id],
        records=[
            ("bridge-grounding-finding", records["grounding"]),
            ("bridge-grounding-review", records["review"]),
        ],
        finding_ref=records["review"].id,
    )
    harness.record_bridge_event(
        BridgeAction.COMPLETED,
        inputs=[
            records["ledger"].id,
            records["output"].id,
            records["output_report"].id,
            records["review"].id,
        ],
        finding_ref=records["review"].id,
    )
    return ledger_event


def _filesystem_snapshot(root: Path):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_bridge_objects_events_and_llm_accounting_replay_exactly_once(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    records = _records()
    prompt_ref = harness.blobs.put(b"bounded stage A prompt")
    raw_ref = harness.blobs.put(b'{"entries": []}')
    call = LLMCall(
        role="summarizer",
        model="scripted",
        endpoint="fixture://bridge",
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=17,
    )

    first = _record_complete_bridge(harness, records, llm=call)

    assert first.rule == Rule.BRIDGE
    assert first.inputs == []
    assert first.outputs == [
        records["catalog"].id,
        records["entry"].id,
        records["ledger"].id,
    ]
    assert first.bridge.inputs == first.inputs
    assert first.bridge.outputs == first.outputs
    assert not any(first.state_diff.model_dump(mode="json", by_alias=True).values())
    for schema, key in (
        ("bridge-ledger-input-catalog", "catalog"),
        ("bridge-ledger-entry", "entry"),
        ("bridge-claim-ledger", "ledger"),
        ("bridge-validation-report", "output_report"),
        ("bridge-output", "output"),
        ("bridge-grounding-review", "review"),
    ):
        assert harness.objects.get(records[key].id, schema=schema)[1] == records[key]

    reopened = Harness(root)
    assert reopened.bridge_state == harness.bridge_state
    assert reopened.bridge_state.event_seqs == list(range(6))
    assert reopened.bridge_state.completed_events == [5]
    assert reopened.bridge_state.failed_events == []
    assert reopened.bridge_state.ledgers[records["ledger"].id] == records["ledger"]
    assert reopened.bridge_state.outputs[records["output"].id] == records["output"]

    result = verify_root(root, meter_total=17)
    assert result["violations"] == []
    assert result["stats"]["logged_tokens"] == 17


def test_bridge_events_leave_every_formal_state_component_byte_identical(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    harness.create_artifact("formal survivor")
    before = harness.state.model_dump_json()
    commitments_before = dict(harness.commitments)
    warrants_before = dict(harness.warrants)
    records = _records(formal_seq=1)

    _record_complete_bridge(harness, records)

    assert harness.state.model_dump_json() == before
    assert harness.commitments == commitments_before
    assert harness.warrants == warrants_before
    bridge_events = [event for event in harness.log.read() if event.rule == Rule.BRIDGE]
    assert len(bridge_events) == 6
    assert all(
        not any(event.state_diff.model_dump(mode="json", by_alias=True).values())
        for event in bridge_events
    )
    reopened = Harness(root)
    assert reopened.state.model_dump_json() == before
    assert reopened.bridge_state == harness.bridge_state


def test_bridge_state_reconstructs_at_every_event_fence(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    records = _records()
    _record_complete_bridge(harness, records)

    expected_actions = [
        BridgeAction.LEDGER_CREATED,
        BridgeAction.LEDGER_VALIDATED,
        BridgeAction.OUTPUT_COMPOSED,
        BridgeAction.OUTPUT_VALIDATED,
        BridgeAction.GROUNDED_REVIEWED,
        BridgeAction.COMPLETED,
    ]
    for seq, action in enumerate(expected_actions):
        historical = Harness.at(root, seq)
        assert historical.bridge_state.event_seqs == list(range(seq + 1))
        assert historical.bridge_state.events_by_action[action] == [seq]
        assert historical.state.artifacts == {}


def test_caller_authored_id_and_explicit_output_mismatch_fail_before_writes(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    records = _records()
    fake_id = _hash("f")
    forged = records["ledger"].model_copy(update={"id": fake_id})

    with pytest.raises(ValidationError, match="canonical"):
        harness.record_bridge_event(
            BridgeAction.LEDGER_CREATED,
            records=[("bridge-claim-ledger", forged)],
        )
    assert list(harness.log.read()) == []
    assert not harness.objects._schema_path("bridge-claim-ledger", fake_id).exists()

    with pytest.raises(ValueError, match="exactly match canonical"):
        harness.record_bridge_event(
            BridgeAction.LEDGER_CREATED,
            outputs=[fake_id],
            records=[("bridge-claim-ledger", records["ledger"])],
        )
    assert list(harness.log.read()) == []
    assert not harness.objects._schema_path(
        "bridge-claim-ledger", records["ledger"].id
    ).exists()


def test_action_schema_and_lifecycle_checks_reject_malformed_bridge_events(tmp_path):
    harness = Harness(tmp_path / "run")
    records = _records()

    with pytest.raises(ValueError, match="unknown ledger"):
        harness.record_bridge_event(
            BridgeAction.OUTPUT_COMPOSED,
            inputs=[records["ledger"].id],
            records=[("bridge-output", records["output"])],
        )
    with pytest.raises(ValueError, match="requires error_code"):
        harness.record_bridge_event(BridgeAction.FAILED)
    with pytest.raises(ValueError, match="only valid for a failed"):
        harness.record_bridge_event(
            BridgeAction.COMPLETED,
            error_code="BRIDGE_TRANSPORT_FAILED",
        )

    failure = harness.record_bridge_event(
        BridgeAction.FAILED,
        error_code="BRIDGE_TRANSPORT_FAILED",
    )
    assert failure.bridge.error_code == "BRIDGE_TRANSPORT_FAILED"
    assert harness.bridge_state.failed_events == [0]
    assert harness.bridge_state.error_codes_by_event == {
        0: "BRIDGE_TRANSPORT_FAILED"
    }


def test_existing_object_outputs_are_type_checked_by_public_seam(tmp_path):
    harness = Harness(tmp_path / "run")
    formal = harness.register_commitment(
        Commitment(id=_hash("a"), eval="predicate:True")
    )

    with pytest.raises(ValueError, match="non-bridge schema"):
        harness.record_bridge_event(
            BridgeAction.LEDGER_CREATED,
            outputs=[formal.id],
        )

    assert [event.rule for event in harness.log.read()] == [Rule.REGISTER]
    assert harness.bridge_state.event_seqs == []


def test_historical_bridge_view_is_physically_read_only(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    records = _records()
    _record_complete_bridge(harness, records)
    before = _filesystem_snapshot(root)

    historical = Harness.at(root, 2)
    assert records["ledger"].id in historical.bridge_state.ledgers
    assert records["output"].id in historical.bridge_state.outputs
    assert records["review"].id not in historical.bridge_state.grounding_reviews
    with pytest.raises(ReadOnlyHarnessError):
        historical.record_bridge_event(
            BridgeAction.FAILED,
            error_code="BRIDGE_READ_ONLY",
        )

    assert _filesystem_snapshot(root) == before


def test_unresolved_completion_is_a_successful_process_event(tmp_path):
    harness = Harness(tmp_path / "run")
    entry = ClaimLedgerEntryV1.create(
        claim_class="unknown",
        claim="The requested value is not established.",
    )
    ledger = ClaimLedgerV1.create(
        problem_ref="problem-1",
        formal_seq=0,
        output_target="answer",
        entries=[entry],
    )
    use = ClaimUseV1.create(
        span_id="span-1",
        text=entry.claim,
        rendering_mode="unknown",
        ledger_entry_ids=[entry.id],
    )
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[use],
        resolution="insufficient_evidence",
        resolution_reason="No grounding was supplied.",
    )
    report = BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        valid=True,
        findings=[],
    )
    ledger_report = BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        valid=True,
        findings=[],
    )
    harness.record_bridge_event(
        BridgeAction.LEDGER_CREATED,
        records=[("bridge-claim-ledger", ledger)],
    )
    harness.record_bridge_event(
        BridgeAction.LEDGER_VALIDATED,
        inputs=[ledger.id],
        records=[("bridge-validation-report", ledger_report)],
    )
    harness.record_bridge_event(
        BridgeAction.OUTPUT_COMPOSED,
        inputs=[ledger.id],
        records=[("bridge-output", output)],
    )
    harness.record_bridge_event(
        BridgeAction.OUTPUT_VALIDATED,
        inputs=[ledger.id, output.id],
        records=[("bridge-validation-report", report)],
    )
    terminal = harness.record_bridge_event(
        BridgeAction.COMPLETED,
        inputs=[ledger.id, output.id, report.id],
    )

    assert terminal.bridge.action == BridgeAction.COMPLETED
    assert harness.bridge_state.completed_events == [4]
    assert harness.bridge_state.failed_events == []
    assert harness.bridge_state.outputs[output.id].resolution.value == "insufficient_evidence"


def test_repair_attempt_preserves_old_and_new_outputs_on_replay(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    records = _records()
    harness.record_bridge_event(
        BridgeAction.LEDGER_CREATED,
        records=[("bridge-claim-ledger", records["ledger"])],
    )
    harness.record_bridge_event(
        BridgeAction.LEDGER_VALIDATED,
        inputs=[records["ledger"].id],
        records=[("bridge-validation-report", records["ledger_report"])],
    )
    harness.record_bridge_event(
        BridgeAction.OUTPUT_COMPOSED,
        inputs=[records["ledger"].id],
        records=[("bridge-output", records["output"])],
    )
    harness.record_bridge_event(
        BridgeAction.OUTPUT_VALIDATED,
        inputs=[records["ledger"].id, records["output"].id],
        records=[("bridge-validation-report", records["output_report"])],
    )
    failed_finding = GroundingFindingV1.create(
        span_id="span-1",
        status="overstated",
        ledger_entry_ids=[records["entry"].id],
        checked_refs=["source-1"],
    )
    failed_review = GroundingReviewV1.create(
        claim_ledger_id=records["ledger"].id,
        bridge_output_id=records["output"].id,
        findings=[failed_finding],
        passed=False,
    )
    harness.record_bridge_event(
        BridgeAction.GROUNDED_REVIEWED,
        inputs=[records["ledger"].id, records["output"].id],
        records=[
            ("bridge-grounding-finding", failed_finding),
            ("bridge-grounding-review", failed_review),
        ],
    )
    repaired_use = ClaimUseV1.create(
        span_id="span-1",
        text="The supplied source records seven.",
        rendering_mode="fact",
        ledger_entry_ids=[records["entry"].id],
    )
    repaired_output = BridgeOutputV1.create(
        claim_ledger_id=records["ledger"].id,
        sections=[repaired_use],
        resolution="answered",
    )

    event = harness.record_bridge_event(
        BridgeAction.REPAIR_ATTEMPTED,
        inputs=[
            records["ledger"].id,
            records["output"].id,
            failed_review.id,
        ],
        records=[
            ("bridge-claim-use", repaired_use),
            ("bridge-output", repaired_output),
        ],
        finding_ref=failed_review.id,
    )

    assert event.bridge.action == BridgeAction.REPAIR_ATTEMPTED
    assert set(harness.bridge_state.outputs) == {
        records["output"].id,
        repaired_output.id,
    }
    reopened = Harness(root)
    assert reopened.bridge_state == harness.bridge_state
    assert reopened.bridge_state.outputs[records["output"].id] == records["output"]
    assert reopened.bridge_state.outputs[repaired_output.id] == repaired_output

    injected = ClaimUseV1.create(
        span_id="span-injected",
        text="An additional factual assertion.",
        rendering_mode="fact",
        ledger_entry_ids=[records["entry"].id],
    )
    unsafe_output = BridgeOutputV1.create(
        claim_ledger_id=records["ledger"].id,
        sections=[records["claim_use"], injected],
        resolution="answered",
    )
    with pytest.raises(ValueError, match="cannot introduce a new span"):
        harness.record_bridge_event(
            BridgeAction.REPAIR_ATTEMPTED,
            inputs=[records["ledger"].id, records["output"].id, failed_review.id],
            records=[
                ("bridge-claim-use", injected),
                ("bridge-output", unsafe_output),
            ],
            finding_ref=failed_review.id,
        )
    assert not harness.objects._schema_path(
        "bridge-output", unsafe_output.id
    ).exists()


def test_explicit_ledger_amendment_is_a_new_replayable_object(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    records = _records(formal_seq=4)
    harness.record_bridge_event(
        BridgeAction.LEDGER_CREATED,
        records=[("bridge-claim-ledger", records["ledger"])],
    )
    conjecture = ClaimLedgerEntryV1.create(
        claim_class="surviving_conjecture",
        claim="A novel explanation remains possible.",
    )
    amended = ClaimLedgerV1.create(
        problem_ref=records["ledger"].problem_ref,
        formal_seq=records["ledger"].formal_seq,
        output_target=records["ledger"].output_target,
        entries=[*records["ledger"].entries, conjecture],
    )

    amendment = harness.record_bridge_event(
        BridgeAction.LEDGER_AMENDED,
        inputs=[records["ledger"].id],
        records=[
            ("bridge-ledger-entry", conjecture),
            ("bridge-claim-ledger", amended),
        ],
    )

    assert amendment.outputs == [conjecture.id, amended.id]
    assert set(harness.bridge_state.ledgers) == {records["ledger"].id, amended.id}
    reopened = Harness(root)
    assert reopened.bridge_state == harness.bridge_state

    changed_fence = ClaimLedgerV1.create(
        problem_ref=amended.problem_ref,
        formal_seq=5,
        output_target=amended.output_target,
        entries=list(amended.entries),
    )
    with pytest.raises(ValueError, match="cannot change fixed formal_seq"):
        harness.record_bridge_event(
            BridgeAction.LEDGER_AMENDED,
            inputs=[amended.id],
            records=[("bridge-claim-ledger", changed_fence)],
        )
