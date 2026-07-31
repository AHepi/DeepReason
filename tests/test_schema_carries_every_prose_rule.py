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
