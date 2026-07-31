"""Stage A compact-v2 namespace, schema, and Jolt regressions."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from deepreason.bridge.ledger import (
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV1,
    ClaimLedgerWireContract,
    ClaimLedgerWireContractV2,
    ClaimLedgerWireReferenceError,
    ClaimLedgerWireV1,
    build_claim_ledger_stage_a,
    render_claim_ledger_stage_a_pack,
)
from deepreason.bridge.models import ClaimClass
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import ModelControlFieldError
from deepreason.llm.packs import AllocatedPack
from deepreason.llm.repair import diagnostic_from_error, schema_at_pointer
from deepreason.storage.blobs import BlobStore


FIXTURE = Path(__file__).parent / "fixtures" / "jolt_bridge_handle_failures.json"


def _item(handle: str, kind: str, ref: str, excerpt: str):
    if kind == "scratch" and not ref.startswith("sha256:"):
        ref = "sha256:" + hashlib.sha256(ref.encode()).hexdigest()
    return ClaimLedgerCatalogItemV1(
        handle=handle,
        kind=kind,
        ref=ref,
        excerpt=excerpt,
    )


def _catalog(*items: ClaimLedgerCatalogItemV1):
    return ClaimLedgerInputCatalogV1.create(
        problem_ref="problem-private-ref",
        formal_seq=210,
        problem_text="What is justified by this bounded record?",
        output_target="a calibrated answer",
        items=list(items),
    )


def _adapter(tmp_path, responses, *, mechanism="json_text", model="offline"):
    endpoint = MockEndpoint(responses, name=f"mock://{model}", model=model)
    endpoint.output_mechanism = mechanism
    adapter = LLMAdapter(
        {"summarizer": endpoint},
        BlobStore(tmp_path / "blobs"),
        model_profile="compact",
    )
    return adapter, endpoint


def _array_branch(schema: dict) -> dict:
    if schema.get("type") == "array":
        return schema
    return next(item for item in schema["anyOf"] if item.get("type") == "array")


def test_v2_compiles_to_the_exact_v1_canonical_identity():
    catalog = _catalog(
        _item("old-source", "source", "source-real", "A bounded source."),
        _item("old-scratch", "scratch", "scratch-real", "A provisional note."),
    )
    v1 = ClaimLedgerWireContract(catalog).compile(
        ClaimLedgerWireV1.model_validate(
            {
                "entries": [
                    {
                        "entry_key": "K1",
                        "claim_class": "source_fact",
                        "claim": "The source establishes the fact.",
                        "source_handles": ["old-source"],
                        "scratch_handles": ["old-scratch"],
                    }
                ]
            }
        )
    )
    contract = ClaimLedgerWireContractV2(catalog)
    v2 = contract.compile(
        contract.validate_value(
            {
                "entries": [
                    {
                        "entry_key": "CLM_1",
                        "claim_class": "source_fact",
                        "claim": "The source establishes the fact.",
                        "source_handles": ["SRC_1"],
                        "scratch_handles": ["SCR_1"],
                    }
                ]
            }
        )
    )

    assert v2 == v1
    assert v2.id == v1.id
    assert v2.model_dump_json() == v1.model_dump_json()


def test_v2_pack_groups_aliases_hides_canonical_refs_and_is_not_prefix_clipped():
    items = [
        _item("legacy-source", "source", "SECRET-SOURCE", "Source excerpt."),
        _item("legacy-evidence", "evidence", "SECRET-EVIDENCE", "Evidence excerpt."),
        _item("legacy-event", "event", "SECRET-EVENT", "Event excerpt."),
        _item("legacy-trace", "trace", "SECRET-TRACE", "Trace excerpt."),
        _item("legacy-observation", "formal_observation", "SECRET-OBS", "Observation excerpt."),
        _item("legacy-artifact", "formal_artifact", "SECRET-ART", "Artifact excerpt."),
        _item("legacy-scratch", "scratch", "SECRET-SCRATCH", "Scratch excerpt."),
    ]
    catalog = _catalog(*items)
    contract = ClaimLedgerWireContractV2(catalog)
    pack = render_claim_ledger_stage_a_pack(catalog, contract=contract)

    assert isinstance(pack, AllocatedPack)
    for label in (
        "allowed_source_handles",
        "allowed_evidence_handles",
        "allowed_event_handles",
        "allowed_trace_handles",
        "allowed_formal_observation_handles",
        "allowed_formal_artifact_handles",
        "allowed_scratch_handles",
    ):
        assert label in pack
    for handle in ("SRC_1", "EVD_1", "EVT_1", "TRC_1", "OBS_1", "ART_1", "SCR_1"):
        assert handle in pack
    for item in items:
        assert item.handle not in pack
        assert item.ref not in pack

    other = _catalog()
    with pytest.raises(ValueError, match="contract/catalog mismatch"):
        render_claim_ledger_stage_a_pack(other, contract=contract)


def test_exact_jolt_failures_produce_local_rich_v2_diagnostics():
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
    catalog = _catalog(
        _item("legacy-observation", "formal_observation", "observation-real", "Observation."),
        _item("legacy-artifact", "formal_artifact", "artifact-real", "Formal proposal."),
        _item("legacy-scratch", "scratch", "scratch-real", "Provisional note."),
    )
    contract = ClaimLedgerWireContractV2(catalog)
    schema = contract.model_json_schema()

    for case in cases:
        value = {"entries": [case["v2_entry"]]}
        expected_pointer = case["pointer"].replace("/4/", "/0/")
        with pytest.raises(ClaimLedgerWireReferenceError) as raised:
            contract.validate_value(value)
        error = raised.value
        diagnostic = diagnostic_from_error(contract.contract_id, error, schema)
        assert error.pointer == expected_pointer
        assert diagnostic.path == expected_pointer
        assert diagnostic.rejected_handle == case["v2_entry"][expected_pointer.split("/")[-2]][0]
        assert diagnostic.received == diagnostic.rejected_handle
        assert diagnostic.omission_or_unknown_legal is True
        assert "do not invent evidence" in diagnostic.instruction
        if case["event_seq"] == 212:
            assert diagnostic.observed_handle_kind == "unknown"
            assert diagnostic.required_handle_kinds == ("event",)
            assert diagnostic.legal_handles == ()
            assert diagnostic.repair_scope == "/entries/0/event_handles"
        else:
            assert diagnostic.observed_handle_kind == "formal_artifact"
            assert diagnostic.required_handle_kinds == ("scratch",)
            assert diagnostic.legal_handles == ("SCR_1",)
            assert diagnostic.repair_scope == expected_pointer


def test_artifact_channel_accepts_art_and_scratch_never_supplies_grounding():
    catalog = _catalog(
        _item("a", "formal_artifact", "artifact-real", "Formal proposal."),
        _item("b", "scratch", "scratch-real", "Provisional note."),
    )
    contract = ClaimLedgerWireContractV2(catalog)
    wire = contract.validate_value(
        {
            "entries": [
                {
                    "entry_key": "CLM_1",
                    "claim_class": "surviving_conjecture",
                    "claim": "The formal proposal remains conjectural.",
                    "formal_artifact_handles": ["ART_1"],
                    "scratch_handles": ["SCR_1"],
                }
            ]
        }
    )
    ledger = contract.compile(wire)
    assert ledger.entries[0].formal_artifact_refs == ["artifact-real"]
    assert ledger.entries[0].scratch_refs == [catalog.items[1].ref]

    for claim_class in (
        "source_fact",
        "recorded_observation",
        "supported_inference",
        "conflict",
    ):
        with pytest.raises(ValidationError):
            contract.validate_value(
                {
                    "entries": [
                        {
                            "entry_key": "CLM_1",
                            "claim_class": claim_class,
                            "claim": "Scratch cannot establish this claim.",
                            "scratch_handles": ["SCR_1"],
                        }
                    ]
                }
            )


def test_empty_v2_catalog_yields_valid_unknown_with_optional_channels_absent(tmp_path):
    adapter, _ = _adapter(tmp_path, ['{"entries":[]}'])
    result = build_claim_ledger_stage_a(
        adapter,
        _catalog(),
        contract_version="v2",
    )

    assert result.receipt.contract_id == "bridge.claim-ledger.compact.v2"
    assert result.failure is None
    assert result.validation_report.valid
    assert result.ledger.entries[0].claim_class == ClaimClass.UNKNOWN
    dumped = result.ledger.entries[0].model_dump(mode="json", exclude_none=True)
    for channel in (
        "source_refs",
        "evidence_refs",
        "event_refs",
        "trace_refs",
        "formal_observation_refs",
        "formal_artifact_refs",
        "scratch_refs",
    ):
        assert channel not in dumped


@pytest.mark.parametrize(
    "family,mechanism",
    [
        ("glm-4", "native_json_schema"),
        ("deepseek-r1", "grammar"),
        ("qwen3", "json_text"),
        ("kimi-k2", "native_json_schema"),
    ],
)
def test_offline_compact_profiles_receive_call_local_enums(
    tmp_path, family, mechanism
):
    catalog = _catalog(
        _item("old-source", "source", "source-real", "Grounded source."),
        _item("old-artifact", "formal_artifact", "artifact-real", "Formal proposal."),
        _item("old-scratch", "scratch", "scratch-real", "Advisory scratch."),
    )
    raw = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "CLM_1",
                    "claim_class": "source_fact",
                    "claim": "The bounded source establishes the fact.",
                    "source_handles": ["SRC_1"],
                }
            ]
        }
    )
    adapter, endpoint = _adapter(
        tmp_path / family,
        [raw],
        mechanism=mechanism,
        model=family,
    )
    result = build_claim_ledger_stage_a(
        adapter,
        catalog,
        contract_version="v2",
    )

    assert result.validation_report.valid
    schema = ClaimLedgerWireContractV2(catalog).model_json_schema()
    assert schema_at_pointer(schema, "/entries/0/source_handles/0")["enum"] == [
        "SRC_1"
    ]
    assert _array_branch(
        schema_at_pointer(schema, "/entries/0/event_handles")
    )["maxItems"] == 0
    if mechanism != "json_text":
        assert endpoint.last_kwargs["response_schema"] == schema
        assert endpoint.last_kwargs["output_mechanism"].value == mechanism
    else:
        assert "response_schema" not in endpoint.last_kwargs
    assert result.receipt.llm_call.attempt_trace[0].output_mechanism == mechanism
    prompt = adapter.blobs.get(result.receipt.llm_call.prompt_ref).decode()
    assert "SRC_1" in prompt and "ART_1" in prompt and "SCR_1" in prompt


def test_local_subtree_repair_can_omit_bad_event_but_cannot_add_evidence(tmp_path):
    catalog = _catalog(
        _item("old-observation", "formal_observation", "observation-real", "Observed."),
    )
    invalid = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "CLM_1",
                    "claim_class": "recorded_observation",
                    "claim": "The formal record contains this observation.",
                    "formal_observation_handles": ["OBS_1"],
                    "event_handles": ["claim-ledger.compact.v1::on_claim"],
                }
            ]
        }
    )
    adapter, endpoint = _adapter(
        tmp_path,
        [invalid, invalid, "[]"],
        mechanism="grammar",
    )
    result = build_claim_ledger_stage_a(
        adapter,
        catalog,
        contract_version="v2",
    )

    call = result.receipt.llm_call
    assert [attempt.valid for attempt in call.attempt_trace] == [False, False, True]
    assert result.failure is None
    entry = result.ledger.entries[0]
    assert entry.event_refs == []
    assert entry.evidence_refs is None
    assert entry.formal_observation_refs == ["observation-real"]
    repair_schema = _array_branch(endpoint.last_kwargs["response_schema"])
    assert repair_schema["type"] == "array"
    assert repair_schema["maxItems"] == 0
    diagnostic = json.loads(
        adapter.blobs.get(call.attempt_trace[0].diagnostic_ref).decode()
    )
    assert diagnostic["legal_handles"] == []
    assert diagnostic["repair_scope"] == "/entries/0/event_handles"


def test_control_firewall_precedes_handle_diagnostic():
    contract = ClaimLedgerWireContractV2(_catalog())
    with pytest.raises(ModelControlFieldError) as raised:
        contract.validate_value(
            {
                "route": "other",
                "entries": [
                    {
                        "entry_key": "CLM_1",
                        "claim_class": "recorded_observation",
                        "claim": "Invalid.",
                        "event_handles": ["not-a-handle"],
                    }
                ],
            }
        )
    assert raised.value.pointer == "/route"


def test_internal_reference_diagnostic_lists_only_available_keys():
    contract = ClaimLedgerWireContractV2(_catalog())
    wire = contract.validate_value(
        {
            "entries": [
                {
                    "entry_key": "CLM_1",
                    "claim_class": "unknown",
                    "claim": "First.",
                },
                {
                    "entry_key": "CLM_2",
                    "claim_class": "supported_inference",
                    "claim": "Second.",
                    "premise_keys": ["CLM_99"],
                },
            ]
        }
    )
    with pytest.raises(ClaimLedgerWireReferenceError) as raised:
        contract.compile(wire)
    diagnostic = diagnostic_from_error(
        contract.contract_id,
        raised.value,
        contract.model_json_schema(),
    )
    assert diagnostic.path == "/entries/1/premise_keys/0"
    assert diagnostic.observed_handle_kind == "entry_key"
    assert diagnostic.required_handle_kinds == ("entry_key", "prior_entry_key")
    assert diagnostic.legal_handles == ("CLM_1",)


def test_the_epistemic_minimums_are_carried_by_the_schema_and_agree_with_the_validator():
    """`_epistemic_minimums` said in English which handles each claim class
    needs, while the schema declared all ten reference arrays independently
    optional and nullable. With reasoning off the schema is the model's only
    source of structural truth, so the rule was unenforced where it mattered.

    The fatal direction for an encoding like this is a FALSE REJECT, so this
    differential-tests schema against validator over every claim class and
    every reference channel rather than asserting the schema's shape.
    """

    import itertools

    from deepreason.bridge.ledger import ClaimLedgerEntryWireV2

    jsonschema = pytest.importorskip("jsonschema", reason="optional checker")

    schema = ClaimLedgerEntryWireV2.model_json_schema()
    sample = {
        "source_handles": ["SRC_1"],
        "evidence_handles": ["EVD_1"],
        "event_handles": ["EVT_1"],
        "trace_handles": ["TRC_1"],
        "formal_observation_handles": ["OBS_1"],
        "premise_keys": ["CLM_1"],
        "formal_artifact_handles": ["ART_1"],
        "conflict_handles": ["SRC_1", "EVD_1"],
        "source_conflict_keys": ["SC_1"],
        "scratch_handles": ["SCR_1"],
    }
    disagreements = []
    for claim_class, (name, full) in itertools.product(ClaimClass, sample.items()):
        for value in (None, [], full, full[:1]):
            for omit_empty in (False, True):
                document = {
                    "entry_key": "CLM_1",
                    "claim_class": claim_class.value,
                    "claim": "a claim",
                }
                if not (omit_empty and (value is None or value == [])):
                    document[name] = value
                try:
                    jsonschema.validate(document, schema)
                    by_schema = True
                except jsonschema.ValidationError:
                    by_schema = False
                try:
                    ClaimLedgerEntryWireV2.model_validate(document)
                    by_validator = True
                except Exception:
                    by_validator = False
                if by_schema != by_validator:
                    disagreements.append(
                        (claim_class.value, name, value, omit_empty, by_schema)
                    )

    assert disagreements == [], disagreements[:4]

    # `conflict` needs TWO conflict_handles or one source_conflict_key, and the
    # schema has to carry the count, not merely non-emptiness.
    conflict = [
        clause
        for clause in schema["allOf"]
        if clause["if"]["properties"]["claim_class"]["enum"] == ["conflict"]
    ]
    (branches,) = [clause["then"]["anyOf"] for clause in conflict]
    counts = {
        tuple(branch["required"])[0]: tuple(branch["properties"].values())[0].get(
            "minItems"
        )
        for branch in branches
    }
    assert counts == {"conflict_handles": 2, "source_conflict_keys": 1}


def test_a_claim_class_no_catalog_can_ground_is_not_advertised():
    """The inverse of a prose-only rule: catalog binding pins a channel with no
    items to `maxItems: 0`, so the grounding clause for some claim class became
    unsatisfiable while `claim_class` still offered it. The contract advertised
    more than the harness could ever accept.

    Narrowing removes only what was already unreachable — the handles such an
    entry would have to cite do not exist — and must never touch the classes
    that ground nothing, which are the run's escape hatch.
    """

    for label, items, expected in (
        (
            "source only",
            (_item("s", "source", "source-real", "A bounded source."),),
            ["source_fact", "supported_inference", "assumption", "unknown", "conflict"],
        ),
        (
            "scratch only",
            (_item("n", "scratch", "scratch-real", "A provisional note."),),
            ["supported_inference", "assumption", "unknown", "conflict"],
        ),
    ):
        schema = ClaimLedgerWireContractV2(_catalog(*items)).model_json_schema()
        entry = schema["$defs"]["ClaimLedgerEntryWireV2"]
        assert entry["properties"]["claim_class"]["enum"] == expected, label
        # Every surviving clause must still be about an advertised class.
        for clause in entry.get("allOf", []):
            named = clause["if"]["properties"]["claim_class"]["enum"]
            assert set(named) <= set(expected), (label, named)
        # `assumption` and `unknown` ground nothing, so no catalog can retire
        # them; they are how a run stays honest about what it cannot cover.
        assert {"assumption", "unknown"} <= set(expected), label

    # A catalog carrying every kind advertises every class.
    full = ClaimLedgerWireContractV2(
        _catalog(
            _item("s", "source", "source-real", "A source."),
            _item("e", "evidence", "evidence-real", "Evidence."),
            _item("a", "formal_artifact", "artifact-real", "An artifact."),
        )
    ).model_json_schema()
    advertised = full["$defs"]["ClaimLedgerEntryWireV2"]["properties"]["claim_class"]
    assert set(advertised["enum"]) == {member.value for member in ClaimClass}
