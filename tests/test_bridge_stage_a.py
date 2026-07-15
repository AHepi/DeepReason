"""C7 Stage A: bounded claim-ledger wire compilation and receipts."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.bridge.ledger import (
    ClaimLedgerAmendmentRequestV1,
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV1,
    ClaimLedgerStageAResultV1,
    ClaimLedgerWireContract,
    ClaimLedgerWireReferenceError,
    ClaimLedgerWireV1,
    amend_claim_ledger_stage_a,
    build_claim_ledger_stage_a,
    render_claim_ledger_stage_a_pack,
)
from deepreason.bridge.models import ClaimClass
from deepreason.bridge.validate import validate_claim_ledger
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.storage.blobs import BlobStore
from deepreason.storage.objects import ObjectStore


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


def _catalog(*items: ClaimLedgerCatalogItemV1) -> ClaimLedgerInputCatalogV1:
    return ClaimLedgerInputCatalogV1.create(
        problem_ref="problem-private-ref",
        formal_seq=8,
        problem_text="What conclusion is justified by the bounded record?",
        output_target="a calibrated answer",
        items=list(items),
        advisory_context_ref=_hash("a"),
        retrieval_receipt_ref=_hash("b"),
    )


def _item(handle: str, kind: str, ref: str, excerpt: str):
    return ClaimLedgerCatalogItemV1(
        handle=handle,
        kind=kind,
        ref=ref,
        excerpt=excerpt,
    )


def _adapter(tmp_path, responses, *, retry_max=2):
    endpoint = MockEndpoint(responses, name="scripted-stage-a", model="scripted")
    adapter = LLMAdapter(
        {"summarizer": endpoint},
        BlobStore(tmp_path / "blobs"),
        retry_max=retry_max,
    )
    return adapter, endpoint


def test_input_catalog_is_bounded_immutable_and_caller_id_spoofing_fails():
    item = _item("S1", "source", "secret-source-ref", "A bounded excerpt.")
    catalog = _catalog(item)

    assert catalog.items == [item]
    with pytest.raises(TypeError):
        catalog.items.append(item)
    dumped = catalog.model_dump(mode="json", by_alias=True)
    with pytest.raises(ValidationError, match="canonical Stage A input catalog"):
        ClaimLedgerInputCatalogV1.model_validate({**dumped, "id": _hash("f")})
    with pytest.raises(ValidationError, match="canonical IDs are forbidden"):
        _item("a" * 64, "source", "source-1", "Excerpt")
    with pytest.raises(ValidationError, match="unique"):
        ClaimLedgerInputCatalogV1.create(
            problem_ref="p",
            formal_seq=0,
            problem_text="problem",
            output_target="answer",
            items=[item, item],
        )


def test_input_catalog_round_trips_through_the_shared_canonical_store(tmp_path):
    catalog = _catalog(
        _item("S1", "source", "source-1", "One bounded source excerpt.")
    )
    store = ObjectStore(tmp_path / "objects")

    store.put("bridge-ledger-input-catalog", catalog)

    assert store.get(catalog.id, schema="bridge-ledger-input-catalog") == (
        "bridge-ledger-input-catalog",
        catalog,
    )


def test_model_pack_exposes_only_opaque_handles_and_selected_excerpts():
    catalog = _catalog(
        _item("S1", "source", "SECRET-SOURCE-CANONICAL", "Included source text."),
        _item("B1", "scratch", _hash("c"), "Selected scratch thought."),
    )

    pack = render_claim_ledger_stage_a_pack(catalog)

    assert "S1" in pack and "B1" in pack
    assert "Included source text." in pack
    assert "Selected scratch thought." in pack
    assert "SECRET-SOURCE-CANONICAL" not in pack
    assert _hash("c") not in pack
    assert catalog.problem_ref not in pack
    assert catalog.id not in pack
    assert "Scratch handles are intellectual provenance only" in pack


def test_compiler_resolves_channels_only_through_the_closed_catalog():
    catalog = _catalog(
        _item("S1", "source", "source-real", "Source excerpt."),
        _item("E1", "evidence", "evidence-real", "Evidence excerpt."),
        _item("A1", "formal_artifact", "artifact-real", "Surviving proposal."),
        _item("B1", "scratch", _hash("d"), "Advisory idea."),
    )
    wire = ClaimLedgerWireV1.model_validate(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": "A grounded fact.",
                    "source_handles": ["S1"],
                    "scratch_handles": ["B1"],
                },
                {
                    "entry_key": "K2",
                    "claim_class": "supported_inference",
                    "claim": "An inference from the fact.",
                    "premise_keys": ["K1"],
                },
                {
                    "entry_key": "K3",
                    "claim_class": "surviving_conjecture",
                    "claim": "A novel conjectural mechanism.",
                    "formal_artifact_handles": ["A1"],
                },
            ]
        }
    )

    ledger = ClaimLedgerWireContract(catalog).compile(wire)

    fact, inference, conjecture = ledger.entries
    assert fact.source_refs == ["source-real"]
    assert fact.scratch_refs == [_hash("d")]
    assert inference.premise_refs == [fact.id]
    assert conjecture.formal_artifact_refs == ["artifact-real"]
    assert conjecture.source_refs is None
    assert validate_claim_ledger(ledger).valid


def test_scratch_only_never_structurally_grounds_a_fact():
    with pytest.raises(ValidationError, match="provenance only"):
        ClaimLedgerWireV1.model_validate(
            {
                "entries": [
                    {
                        "entry_key": "K1",
                        "claim_class": "source_fact",
                        "claim": "Unsupported factual wording.",
                        "scratch_handles": ["B1"],
                    }
                ]
            }
        )


def test_unknown_handle_and_wrong_channel_fail_without_accepting_raw_refs():
    catalog = _catalog(_item("S1", "source", "source-real", "Source excerpt."))
    contract = ClaimLedgerWireContract(catalog)
    unknown = ClaimLedgerWireV1.model_validate(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": "Claim.",
                    "source_handles": ["S9"],
                }
            ]
        }
    )
    with pytest.raises(ClaimLedgerWireReferenceError, match="unknown catalog handle"):
        contract.compile(unknown)

    wrong_kind = ClaimLedgerWireV1.model_validate(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "recorded_observation",
                    "claim": "Observation.",
                    "evidence_handles": ["S1"],
                }
            ]
        }
    )
    with pytest.raises(ClaimLedgerWireReferenceError, match="expected evidence"):
        contract.compile(wrong_kind)


def test_empty_stage_a_output_becomes_valid_unknown_and_uncovered(tmp_path):
    catalog = _catalog()
    adapter, _ = _adapter(tmp_path, ['{"entries":[]}'])

    result = build_claim_ledger_stage_a(adapter, catalog)

    assert result.validation_report.valid
    assert result.used_unknown_fallback
    assert [entry.claim_class for entry in result.ledger.entries] == [ClaimClass.UNKNOWN]
    assert result.ledger.entries[0].source_refs is None
    assert result.ledger.uncovered_requirements
    assert result.failure is None
    assert result.receipt.llm_call.attempts == 1


def test_success_returns_all_adapter_raw_and_attempt_receipts(tmp_path):
    hidden_ref = "source-hidden-from-model"
    catalog = _catalog(_item("S1", "source", hidden_ref, "Measured value is 4."))
    raw = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": "The measured value is 4.",
                    "source_handles": ["S1"],
                }
            ]
        }
    )
    adapter, endpoint = _adapter(tmp_path, [raw])

    result = build_claim_ledger_stage_a(adapter, catalog)

    call = result.receipt.llm_call
    assert call is not None
    assert call.role == "summarizer"
    assert call.attempts == 1
    assert len(call.attempt_trace) == 1
    assert call.attempt_trace[0].raw_ref == call.raw_ref
    assert adapter.blobs.get(call.raw_ref).decode() == raw
    prompt = adapter.blobs.get(call.prompt_ref).decode()
    assert "CLAIM LEDGER STAGE A" in prompt
    assert "Build exactly one claim ledger" in prompt
    assert hidden_ref not in prompt
    assert endpoint.last_kwargs == {}
    assert result.ledger.entries[0].source_refs == [hidden_ref]


def test_unknown_handle_uses_shared_bounded_repair_and_preserves_both_raws(tmp_path):
    catalog = _catalog(_item("S1", "source", "source-real", "Grounded excerpt."))
    invalid = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": "Grounded claim.",
                    "source_handles": ["S9"],
                }
            ]
        }
    )
    repaired = invalid.replace('"S9"', '"S1"')
    adapter, _ = _adapter(tmp_path, [invalid, repaired])

    result = build_claim_ledger_stage_a(adapter, catalog)

    call = result.receipt.llm_call
    assert call.attempts == 2
    assert [attempt.valid for attempt in call.attempt_trace] == [False, True]
    assert adapter.blobs.get(call.attempt_trace[0].raw_ref).decode() == invalid
    assert adapter.blobs.get(call.attempt_trace[1].raw_ref).decode() == repaired
    assert call.attempt_trace[0].diagnostic_ref
    diagnostic = json.loads(
        adapter.blobs.get(call.attempt_trace[0].diagnostic_ref).decode()
    )
    assert diagnostic["error"] == "BRIDGE_WIRE_REFERENCE_INVALID"
    assert diagnostic["path"] == "/entries/0/source_handles/0"
    assert diagnostic["repair_scope"] == "/entries/0/source_handles/0"
    assert result.ledger.entries[0].source_refs == ["source-real"]


def test_exhausted_grounding_repair_returns_unknown_without_invented_refs(tmp_path):
    catalog = _catalog(_item("B1", "scratch", _hash("e"), "Scratch-only idea."))
    scratch_fact = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": "The scratch idea is established fact.",
                    "scratch_handles": ["B1"],
                }
            ]
        }
    )
    adapter, _ = _adapter(tmp_path, [scratch_fact, scratch_fact, scratch_fact])

    result = build_claim_ledger_stage_a(adapter, catalog)

    assert result.failure is not None
    assert result.receipt.repair_exhausted
    assert result.receipt.llm_call.attempts == 3
    assert len(result.receipt.llm_call.attempt_trace) == 3
    assert result.used_unknown_fallback
    assert result.validation_report.valid
    entry = result.ledger.entries[0]
    assert entry.claim_class == ClaimClass.UNKNOWN
    assert entry.source_refs is None
    assert entry.evidence_refs is None
    assert entry.scratch_refs is None


def test_source_conflicts_use_two_non_scratch_catalog_sides():
    catalog = _catalog(
        _item("S1", "source", "left-source", "The value is 2."),
        _item("S2", "source", "right-source", "The value is 3."),
    )
    wire = ClaimLedgerWireV1.model_validate(
        {
            "source_conflicts": [
                {
                    "conflict_key": "CNew",
                    "conflicting_handles": ["S1", "S2"],
                    "description": "The sources disagree.",
                }
            ],
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "conflict",
                    "claim": "The reported value conflicts.",
                    "source_conflict_keys": ["CNew"],
                }
            ],
        }
    )

    ledger = ClaimLedgerWireContract(catalog).compile(wire)

    assert ledger.source_conflicts[0].conflicting_refs == [
        "left-source",
        "right-source",
    ]
    assert ledger.entries[0].source_conflict_refs == [ledger.source_conflicts[0].id]
    assert validate_claim_ledger(ledger).valid


def test_amendment_adds_only_new_entries_against_same_closed_catalog(tmp_path):
    catalog = _catalog(_item("S1", "source", "source-real", "Premise excerpt."))
    initial_raw = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": "The premise holds.",
                    "source_handles": ["S1"],
                }
            ]
        }
    )
    initial_adapter, _ = _adapter(tmp_path / "initial", [initial_raw])
    previous = build_claim_ledger_stage_a(initial_adapter, catalog)
    prior_dump = previous.ledger.model_dump_json()
    amendment_raw = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "K2",
                    "claim_class": "supported_inference",
                    "claim": "The conclusion follows from the premise.",
                    "premise_keys": ["P1"],
                }
            ]
        }
    )
    amendment_adapter, endpoint = _adapter(tmp_path / "amend", [amendment_raw])

    request = ClaimLedgerAmendmentRequestV1(
        requested_class="supported_inference",
        proposed_claim="The conclusion follows from the premise.",
        reason="Stage B identified an inference absent from the ledger.",
    )
    amended = amend_claim_ledger_stage_a(
        amendment_adapter, previous, request=request
    )

    assert isinstance(amended, ClaimLedgerStageAResultV1)
    assert amended.catalog.id == previous.catalog.id
    assert amended.prior_ledger == previous.ledger
    assert amended.ledger.entries[0] == previous.ledger.entries[0]
    assert amended.ledger.entries[1].premise_refs == [previous.ledger.entries[0].id]
    assert amended.amended
    assert previous.ledger.model_dump_json() == prior_dump
    assert amended.receipt.llm_call.attempts == 1
    assert endpoint.last_transport_attempts == 1


def test_failed_amendment_returns_prior_ledger_and_typed_receipt(tmp_path):
    catalog = _catalog()
    initial_adapter, _ = _adapter(tmp_path / "initial", ['{"entries":[]}'])
    previous = build_claim_ledger_stage_a(initial_adapter, catalog)
    invalid = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "K2",
                    "claim_class": "supported_inference",
                    "claim": "An invented inference.",
                }
            ]
        }
    )
    amendment_adapter, _ = _adapter(
        tmp_path / "amend", [invalid, invalid, invalid]
    )

    result = amend_claim_ledger_stage_a(
        amendment_adapter,
        previous,
        request=ClaimLedgerAmendmentRequestV1(
            requested_class="supported_inference",
            proposed_claim="An invented inference.",
            reason="Stage B requested explicit ledger adjudication.",
        ),
    )

    assert result.failure is not None
    assert result.receipt.repair_exhausted
    assert result.receipt.llm_call.attempts == 3
    assert result.ledger == previous.ledger
    assert result.prior_ledger == previous.ledger
    assert not result.amended
    assert result.validation_report.valid
