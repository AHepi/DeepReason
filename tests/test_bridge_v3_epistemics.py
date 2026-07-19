"""RunManifest-v6 bridge epistemic authority regressions."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.bridge.compose import (
    BridgeCompositionWireContractV2,
    BridgeCompositionWireV2,
    CompositionContractError,
)
from deepreason.bridge.ledger import (
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV1,
    ClaimLedgerInputCatalogV3,
    ClaimLedgerWireContractV3,
    ClaimLedgerWireReferenceError,
)
from deepreason.bridge.models import (
    BridgeOutputV1,
    ClaimClass,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ClaimUseV1,
    ProcessObservationV1,
)
from deepreason.bridge.validate import validate_bridge_output
from deepreason.storage.objects import ObjectStore


_FORMAL_SEQ = 7
_SURVIVOR_REF = "artifact-survivor"
_SURVIVOR_CLAIM = "A latent feedback loop explains the recorded pattern."


def _process_observation() -> ProcessObservationV1:
    return ProcessObservationV1.create(
        observation_kind="acceptance",
        formal_seq=_FORMAL_SEQ,
        subject_ref=_SURVIVOR_REF,
        related_refs=[],
    )


def _v3_catalog() -> tuple[ClaimLedgerInputCatalogV3, ProcessObservationV1]:
    process = _process_observation()
    catalog = ClaimLedgerInputCatalogV3.create(
        problem_ref="problem-v3",
        formal_seq=_FORMAL_SEQ,
        problem_text="What explains the recorded pattern?",
        output_target="answer",
        items=[
            ClaimLedgerCatalogItemV1(
                handle="survivor",
                kind="formal_artifact",
                ref=_SURVIVOR_REF,
                excerpt=_SURVIVOR_CLAIM,
            ),
            ClaimLedgerCatalogItemV1(
                handle="status",
                kind="process_observation",
                ref=process.id,
                excerpt=process.statement,
            ),
        ],
        process_observations=[process],
    )
    return catalog, process


def _ledger(*entries: ClaimLedgerEntryV1) -> ClaimLedgerV1:
    return ClaimLedgerV1.create(
        problem_ref="problem-v3",
        formal_seq=_FORMAL_SEQ,
        output_target="answer",
        entries=list(entries),
    )


def _entry(claim_class: ClaimClass, claim: str, **values) -> ClaimLedgerEntryV1:
    return ClaimLedgerEntryV1.create(
        claim_class=claim_class,
        claim=claim,
        **values,
    )


def _composition_wire(
    *,
    text: str,
    handles: list[str],
    include_mode: bool = False,
) -> dict:
    section = {
        "span_id": "S1",
        "text": text,
        "ledger_entry_handles": handles,
    }
    if include_mode:
        section["rendering_mode"] = "fact"
    return {"sections": [section], "resolution": "answered"}


def test_survivor_formal_artifact_cannot_become_a_recorded_observation():
    catalog, process = _v3_catalog()
    contract = ClaimLedgerWireContractV3(catalog)

    with pytest.raises(ClaimLedgerWireReferenceError) as captured:
        contract.validate_value(
            {
                "entries": [
                    {
                        "entry_key": "CLM_1",
                        "claim_class": "recorded_observation",
                        "claim": _SURVIVOR_CLAIM,
                        "formal_observation_handles": ["ART_1"],
                    }
                ]
            }
        )

    assert captured.value.pointer == "/entries/0/formal_observation_handles/0"
    assert captured.value.observed_kind == "formal_artifact"

    wire = contract.validate_value(
        {
            "entries": [
                {
                    "entry_key": "CLM_1",
                    "claim_class": "surviving_conjecture",
                    "claim": _SURVIVOR_CLAIM,
                    "formal_artifact_handles": ["ART_1"],
                }
            ]
        }
    )
    ledger = contract.compile(wire)
    substantive = [entry for entry in ledger.entries if entry.claim == _SURVIVOR_CLAIM]
    assert [entry.claim_class for entry in substantive] == [
        ClaimClass.SURVIVING_CONJECTURE
    ]
    status = [
        entry
        for entry in ledger.entries
        if entry.process_observation_refs == [process.id]
    ]
    assert len(status) == 1
    assert status[0].claim_class == ClaimClass.RECORDED_OBSERVATION
    assert status[0].claim == process.statement


def test_process_observation_only_supports_its_exact_status_statement():
    catalog, process = _v3_catalog()
    stage_a = ClaimLedgerWireContractV3(catalog)
    ledger = stage_a.compile(stage_a.validate_value({"entries": []}))

    assert [entry.claim for entry in ledger.entries] == [process.statement]
    assert ledger.uncovered_requirements is None

    composition = BridgeCompositionWireContractV2(
        ledger,
        maximum_sections=2,
        desired_length_chars=4_096,
    )
    valid = composition.validate_value(
        _composition_wire(text=process.statement, handles=["E1"])
    )
    draft = composition.compile(valid)
    assert draft.output is not None
    assert draft.output.sections[0].rendering_mode.value == "observation"

    altered = composition.validate_value(
        _composition_wire(
            text=f"{process.statement} Therefore {_SURVIVOR_CLAIM}",
            handles=["E1"],
        )
    )

    tampered_output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[
            ClaimUseV1.create(
                span_id="S1",
                text=f"{process.statement} Therefore {_SURVIVOR_CLAIM}",
                rendering_mode="observation",
                ledger_entry_ids=[ledger.entries[0].id],
            )
        ],
        resolution="answered",
    )
    report = validate_bridge_output(ledger, tampered_output)
    assert not report.valid
    finding = next(
        item
        for item in report.findings
        if item.code == "BRIDGE_PROCESS_OBSERVATION_SCOPE"
    )
    assert finding.pointer == "/sections/0/text"
    with pytest.raises(CompositionContractError) as captured:
        composition.compile(altered)
    assert captured.value.pointer == "/sections/0/text"


def test_v3_catalog_binds_process_records_and_rejects_forged_excerpts():
    process = _process_observation()
    item = ClaimLedgerCatalogItemV1(
        handle="status",
        kind="process_observation",
        ref=process.id,
        excerpt=process.statement,
    )
    values = {
        "problem_ref": "problem-v3",
        "formal_seq": _FORMAL_SEQ,
        "problem_text": "What happened?",
        "output_target": "answer",
        "items": [item],
    }

    with pytest.raises(ValidationError, match="exactly match structured"):
        ClaimLedgerInputCatalogV3.create(**values)

    forged = item.model_copy(update={"excerpt": f"{process.statement} The claim is true."})
    with pytest.raises(ValidationError, match="deterministic statement"):
        ClaimLedgerInputCatalogV3.create(
            **{**values, "items": [forged]},
            process_observations=[process],
        )


def test_process_observation_statement_is_not_caller_authored():
    with pytest.raises(ValueError, match="must be deterministic"):
        ProcessObservationV1.create(
            observation_kind="acceptance",
            formal_seq=_FORMAL_SEQ,
            subject_ref=_SURVIVOR_REF,
            related_refs=[],
            statement=f"{_SURVIVOR_CLAIM} is true.",
        )


def test_composition_v2_schema_excludes_model_authored_rendering_mode():
    fact = _entry(
        ClaimClass.SOURCE_FACT,
        "The measured input increased.",
        source_refs=["source-1"],
    )
    contract = BridgeCompositionWireContractV2(
        _ledger(fact),
        maximum_sections=2,
        desired_length_chars=4_096,
    )

    schema = BridgeCompositionWireV2.model_json_schema()
    span_schema = schema["$defs"]["CompositionSpanWireV2"]
    assert "rendering_mode" not in span_schema["properties"]
    assert "rendering_mode" not in json.dumps(contract.model_json_schema())

    with pytest.raises(ValueError, match="rendering_mode"):
        contract.validate_value(
            _composition_wire(
                text="The measured input increased.",
                handles=["E1"],
                include_mode=True,
            )
        )


def test_mixed_ledger_classes_derive_the_weakest_rendering_mode():
    fact = _entry(
        ClaimClass.SOURCE_FACT,
        "The measured input increased.",
        source_refs=["source-1"],
    )
    inference = _entry(
        ClaimClass.SUPPORTED_INFERENCE,
        "The response may follow from the measured input.",
        premise_refs=[fact.id],
    )
    assumption = _entry(
        ClaimClass.ASSUMPTION,
        "The measuring apparatus remained calibrated.",
    )
    contract = BridgeCompositionWireContractV2(
        _ledger(fact, inference, assumption),
        maximum_sections=2,
        desired_length_chars=4_096,
    )

    wire = contract.validate_value(
        _composition_wire(
            text="Conditionally, the response follows if calibration held.",
            handles=["E1", "E2", "E3"],
        )
    )
    draft = contract.compile(wire)

    assert draft.output is not None
    assert draft.output.sections[0].rendering_mode.value == "assumption"


def test_assumption_never_renders_as_fact_even_when_worded_as_certain():
    assumption = _entry(
        ClaimClass.ASSUMPTION,
        "The measuring apparatus remained calibrated.",
    )
    contract = BridgeCompositionWireContractV2(
        _ledger(assumption),
        maximum_sections=2,
        desired_length_chars=4_096,
    )
    wire = contract.validate_value(
        _composition_wire(
            text="The apparatus certainly remained calibrated.",
            handles=["E1"],
        )
    )

    draft = contract.compile(wire)

    assert draft.output is not None
    assert draft.output.sections[0].rendering_mode.value == "assumption"


def test_unknown_composition_reference_is_rejected():
    fact = _entry(
        ClaimClass.SOURCE_FACT,
        "A grounded fact.",
        source_refs=["source-1"],
    )
    contract = BridgeCompositionWireContractV2(
        _ledger(fact),
        maximum_sections=2,
        desired_length_chars=4_096,
    )

    with pytest.raises(ValidationError):
        contract.validate_value(
            _composition_wire(text="A grounded fact.", handles=["E99"])
        )


def test_v3_rejects_one_reference_in_incompatible_catalog_kinds_but_v1_is_unchanged():
    items = [
        ClaimLedgerCatalogItemV1(
            handle="source",
            kind="source",
            ref="shared-ref",
            excerpt="Source excerpt.",
        ),
        ClaimLedgerCatalogItemV1(
            handle="artifact",
            kind="formal_artifact",
            ref="shared-ref",
            excerpt="Formal artifact excerpt.",
        ),
    ]
    values = {
        "problem_ref": "problem-v3",
        "formal_seq": _FORMAL_SEQ,
        "problem_text": "What is supported?",
        "output_target": "answer",
        "items": items,
    }

    with pytest.raises(ValidationError, match="incompatible catalog kinds"):
        ClaimLedgerInputCatalogV3.create(**values)

    legacy = ClaimLedgerInputCatalogV1.create(**values)
    assert len(legacy.items) == 2


def test_v3_catalog_with_process_records_round_trips_through_object_store(tmp_path):
    catalog, process = _v3_catalog()
    store = ObjectStore(tmp_path / "objects")

    store.put("bridge-ledger-input-catalog", catalog)
    schema, restored = store.get(catalog.id)

    assert schema == "bridge-ledger-input-catalog"
    assert restored.schema_ == "bridge.catalog.v3"
    assert restored.process_observations is not None
    assert restored.process_observations[0].id == process.id
