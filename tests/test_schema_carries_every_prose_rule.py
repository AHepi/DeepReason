"""Every mechanically-enforceable contract rule is carried by the schema.

Operator rule A2 (2026-07-31): with reasoning disabled the JSON Schema is the
model's only source of structural truth, so a constraint that exists only in
prose is an ambiguity in the CONTRACT, not a model failure. Measured:
`scratch.link.compact.v1` scored 11/20 then 9/20 first-pass with 18 and 22
repairs on glm-5.2 with thinking off, failing production qualification twice;
encoding one cross-field rule took it to 20/20 with zero repairs.

These tests are coverage guards rather than behaviour checks. The per-contract
differential tests live beside the contracts they belong to; what is guarded
here is that a NEW array or a NEW cross-field validator cannot be added
without its schema counterpart.
"""

from __future__ import annotations

import re
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "src" / "deepreason"


def _field_declaration(source: str, class_name: str, field_name: str) -> str | None:
    match = re.search(rf"^class {re.escape(class_name)}\b", source, re.M)
    if match is None:
        return None
    following = re.search(r"^(class |def )", source[match.end() :], re.M)
    body = source[match.end() : match.end() + following.start()] if following else source[match.end() :]
    declaration = re.search(
        rf"^\s{{4}}{re.escape(field_name)}:[^\n=]*=\s*Field\((?:[^()]*(?:\([^()]*\))?)*\)",
        body,
        re.M,
    )
    return declaration.group(0) if declaration else None


def test_every_array_whose_validator_rejects_duplicates_says_so_in_the_schema():
    """A `uniqueItems` keyword was absent from every rendered wire schema, so
    each of these arrays told the model repetition was legal while the
    validator refused it — silently costing a repair round at best.
    """

    enforced = {
        "bridge/ledger.py": {
            "ClaimLedgerEntryWireV1": (
                "source_handles", "evidence_handles", "event_handles",
                "trace_handles", "formal_observation_handles", "premise_keys",
                "formal_artifact_handles", "conflict_handles",
                "source_conflict_keys", "scratch_handles",
            ),
            "ClaimLedgerEntryWireV2": (
                "source_handles", "evidence_handles", "event_handles",
                "trace_handles", "formal_observation_handles", "premise_keys",
                "formal_artifact_handles", "conflict_handles",
                "source_conflict_keys", "scratch_handles",
            ),
            "SourceConflictWireV1": ("conflicting_handles", "scratch_handles"),
            "UncoveredRequirementWireV1": ("related_entry_keys", "scratch_handles"),
        },
        "bridge/compose.py": {
            "CompositionSpanWireV1": ("ledger_entry_handles",),
            "CompositionSpanWireV2": ("ledger_entry_handles",),
            "CompositionUnresolvedWireV1": ("ledger_entry_handles",),
        },
        "llm/wire.py": {
            "ContextRequestWireV1": (
                "requested_visible_aliases", "desired_retrieval_channels",
            ),
            "ContextRequestWireV2": (
                "requested_visible_aliases", "desired_retrieval_channels",
            ),
            "SimulationProposalWireV1": (
                "rival_predictions", "declared_assumptions", "input_aliases",
                "requested_seed_set", "requested_observables",
                "interpretation_conditions",
            ),
            "ResearchFetchProposalWireV1": ("urls",),
        },
        "capabilities/models.py": {
            "SimulationProposalDraftV1": (
                "rival_predictions", "declared_assumptions", "input_aliases",
                "requested_seed_set", "requested_observables",
                "interpretation_conditions",
            ),
            "ResearchFetchProposalDraftV1": ("urls",),
        },
        "scratch/proposals.py": {
            "ScratchQuestionDraftV1": ("related_refs",),
            "ScratchClusterSuggestionV1": ("member_refs",),
        },
        "scratch/contracts.py": {
            "ClusterGuideWireV1": ("entry_points",),
        },
    }

    missing = []
    for relative, classes in enforced.items():
        source = (SOURCE / relative).read_text()
        for class_name, fields in classes.items():
            for field_name in fields:
                declaration = _field_declaration(source, class_name, field_name)
                if declaration is None:
                    missing.append(f"{relative}:{class_name}.{field_name} NOT FOUND")
                elif "_UNIQUE_ITEMS" not in declaration:
                    missing.append(f"{relative}:{class_name}.{field_name}")

    assert missing == [], missing


def test_every_cross_field_validator_has_a_schema_encoding():
    """The named model_validators below are the cross-field rules this sweep
    encoded. Each must keep a schema counterpart on the same model, so a later
    refactor cannot quietly drop the encoding and leave the rule prose-only
    again — the exact state that failed qualification.
    """

    encoded = {
        "llm/wire.py": (
            ("ConjecturerTurnWireV4", "TURN_OUTCOME_SHAPE"),
            ("ReasoningConjecturerTurnWireV4", "TURN_OUTCOME_SHAPE"),
            ("ContextRequestWireV1", "CONTEXT_REQUEST_SELECTOR_SHAPE"),
            ("ContextRequestWireV2", "CONTEXT_REQUEST_SELECTOR_SHAPE"),
            ("AtomicConjectureCandidateWireV1", "exclusive_fields_schema"),
            ("AtomicReasoningConjectureCandidateWireV1", "exclusive_fields_schema"),
        ),
        "bridge/ledger.py": (
            ("ClaimLedgerEntryWireV1", "EPISTEMIC_MINIMUMS_SHAPE"),
        ),
        "bridge/repair.py": (("GroundingRepairWireV1", "_ACTION_SHAPE"),),
        "bridge/compose.py": (
            ("BridgeCompositionWireV1", "AMENDMENT_IS_DISTINCT_SHAPE"),
            ("BridgeCompositionWireV2", "AMENDMENT_IS_DISTINCT_SHAPE"),
        ),
        "scratch/contracts.py": (
            ("ScratchLinkWireV1", "exclusive_fields_schema"),
            ("ScratchLinkMinimalWireV1", "exclusive_fields_schema"),
        ),
    }

    unencoded = []
    for relative, expectations in encoded.items():
        source = (SOURCE / relative).read_text()
        for class_name, encoder in expectations:
            match = re.search(rf"^class {re.escape(class_name)}\b", source, re.M)
            assert match is not None, f"{relative}:{class_name}"
            following = re.search(r"^(class |def )", source[match.end() :], re.M)
            body = (
                source[match.end() : match.end() + following.start()]
                if following
                else source[match.end() :]
            )
            if "json_schema_extra" not in body or encoder not in body:
                unencoded.append(f"{relative}:{class_name} -> {encoder}")

    assert unencoded == [], unencoded


def test_alias_bearing_fields_name_their_legal_values_in_the_schema():
    """Regression (20B battery, 2026-07-31): the first failures a small model
    produced were handle and namespace violations — aliases invented in the
    right shape but outside the call-local table. `AliasTable.resolve` refuses
    anything outside it, so the legal set is known at render time and there is
    no reason to make the model infer it from the prompt.

    Binding is skipped for an empty table: an empty enum is unsatisfiable, and
    a contract with no aliases cannot be answered anyway.
    """

    import jsonschema
    import pytest

    from deepreason.llm.wire import (
        AliasTable,
        CriticWireContract,
        DefenderWireContract,
        JudgeWireContract,
        PairwiseJudgeWireContract,
        SynthesizerWireContract,
    )

    jsonschema = pytest.importorskip("jsonschema", reason="optional checker")
    aliases = AliasTable(aliases={"A1": "art-1", "B1": "art-2"})

    cases = (
        (
            "critic",
            CriticWireContract(aliases=aliases, expected_target="art-1"),
            {"attack": True, "target_alias": "A1", "cited_input_aliases": ["A1"]},
            {"attack": True, "target_alias": "A1", "cited_input_aliases": ["Z9"]},
        ),
        (
            "judge",
            JudgeWireContract(aliases),
            {"decision": "pass", "decisive_point_alias": "A1"},
            {"decision": "pass", "decisive_point_alias": "Z9"},
        ),
        (
            "pairwise",
            PairwiseJudgeWireContract(aliases),
            {"winner": "A", "decisive_point_alias": "B1"},
            {"winner": "A", "decisive_point_alias": "Z9"},
        ),
        (
            "synthesizer",
            SynthesizerWireContract(aliases),
            {"relation": "r", "depends_on": ["A1"]},
            {"relation": "r", "depends_on": ["Z9"]},
        ),
    )
    disagreements = []
    for label, contract, legal, illegal in cases:
        schema = contract.model_json_schema()
        for document, expected in ((legal, True), (illegal, False)):
            try:
                jsonschema.validate(document, schema)
                by_schema = True
            except jsonschema.ValidationError:
                by_schema = False
            try:
                contract.compile(contract.wire_model.model_validate(document))
                by_compiler = True
            except Exception:
                by_compiler = False
            if not (by_schema == by_compiler == expected):
                disagreements.append((label, document, by_schema, by_compiler, expected))

    assert disagreements == [], disagreements

    # An alias field on a nested item model must be bound too; the defender's
    # clauses are a $def, and binding only the response root missed them.
    definitions = DefenderWireContract(aliases=aliases).model_json_schema()["$defs"]
    bound = [
        definition["properties"]["item_alias"]
        for definition in definitions.values()
        if isinstance(definition, dict) and "item_alias" in definition.get("properties", {})
    ]
    assert bound and all(field.get("enum") == ["A1", "B1"] for field in bound), bound

    # `neither` needs no located point, so an empty-string default has to stay
    # legal or the encoding would forbid the verdict it exists to allow.
    pairwise = PairwiseJudgeWireContract(aliases).model_json_schema()
    assert pairwise["properties"]["decisive_point_alias"]["enum"] == ["", "A1", "B1"]

    # No aliases: leave the field open rather than emit an impossible schema.
    open_schema = JudgeWireContract(AliasTable()).model_json_schema()
    assert "enum" not in open_schema["properties"]["decisive_point_alias"]


def test_identifier_namespaces_are_patterns_not_only_prose():
    """`_visible_alias_syntax`, `_local_refs`, `_members_are_local` and
    `_https_and_unique` each enforce a namespace in Python that the schema did
    not state. `items` REPLACES the rendered subschema rather than merging, so
    every one of these restates `type: string` — `pattern` constrains only
    strings, and a bare number would otherwise slip past it.
    """

    from deepreason.capabilities.models import ResearchFetchProposalDraftV1
    from deepreason.llm.wire import (
        ContextRequestWireV1,
        ContextRequestWireV2,
        ResearchFetchProposalWireV1,
    )
    from deepreason.scratch.proposals import (
        ScratchClusterSuggestionV1,
        ScratchQuestionDraftV1,
    )

    expected = {
        (ContextRequestWireV1, "requested_visible_aliases"): r"^[ABCLG][1-9][0-9]{0,4}$",
        (ContextRequestWireV2, "requested_visible_aliases"): r"^(?:SRC|SCR)_[0-9]{3}$",
        (ScratchQuestionDraftV1, "related_refs"): r"^(?:SCR|NEW)_[0-9]{3,}$",
        (ScratchClusterSuggestionV1, "member_refs"): r"^(?:SCR|NEW)_[0-9]{3,}$",
        (ResearchFetchProposalDraftV1, "urls"): r"^https://[^\s]{1,2048}$",
        (ResearchFetchProposalWireV1, "urls"): r"^https://[^\s]{1,2048}$",
    }
    for (model, field), pattern in expected.items():
        items = model.model_json_schema()["properties"][field]["items"]
        assert items.get("pattern") == pattern, (model.__name__, field, items)
        assert items.get("type") == "string", (model.__name__, field, items)

    # The research wire model claimed to mirror its draft and did not: a
    # non-https or duplicated URL passed the wire and died in compile().
    for urls, admissible in (
        (["https://a.example/x"], True),
        (["http://a.example/x"], False),
        (["https://a.example/x", "https://a.example/x"], False),
    ):
        payload = {"request_identifier": "r", "purpose": "p", "urls": urls}
        try:
            ResearchFetchProposalWireV1.model_validate(payload)
            accepted = True
        except Exception:
            accepted = False
        assert accepted is admissible, urls
