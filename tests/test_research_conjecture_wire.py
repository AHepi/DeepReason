"""C2: research proposals ride the v6 conjecture wire under frozen authority.

The model proposes directed fetches on the turn wire only when the frozen
manifest enables research; the task payload carries a research_authority
block mirroring simulation_authority; staging binds each proposal to its
durable provider transaction; and a granted fetch executes and is consumed
inside the same cycle, so fetched material is citable before the next
turn's §4 citation checks.
"""

from __future__ import annotations

import json

import pytest

from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.models import (
    ResearchConsumptionV1,
    ResearchExecutionReceiptV1,
    ResearchFetchProposalV1,
)
from deepreason.capabilities.policy import ResearchCapabilityPolicyV1
from deepreason.capabilities.research import (
    MAXIMUM_PROPOSALS_PER_TURN,
    consumed_research_blocks,
)
from deepreason.canonical import canonical_json
from deepreason.conjecture_turn import ConjectureTurnV6
from deepreason.llm.wire import (
    AliasTable,
    ConjecturerTurnWireContractV6,
    V6WireReferenceError,
)
from deepreason.rules.conj import conj
from deepreason.scratch.service import ScratchService
from deepreason.workflow.models import CapabilityOutcome
from deepreason.workflow.profiles import compile_workflow_profile
from tests.test_v6_transaction_qualification import (
    _config,
    _live_adapter,
    _manifest,
    _seed_live_conjecture,
)


PAGE = b"<html><body><h1>Tides</h1><p>The moon pulls the sea.</p></body></html>"


def _research_policy(**updates) -> ResearchCapabilityPolicyV1:
    values = {
        "enabled": True,
        "backend_identity": "web.contained.v1",
        "maximum_requests": 3,
        "maximum_sources": 2,
        "domain_allowlist": ("example.org",),
        "maximum_response_bytes": 65_536,
    }
    values.update(updates)
    return ResearchCapabilityPolicyV1(**values)


def _patch_transport(monkeypatch, script: dict) -> list:
    calls = []

    def transport(url, timeout, maximum_bytes):
        calls.append(url)
        return script[url]

    monkeypatch.setattr(
        "deepreason.research.fetch._urllib_transport", transport
    )
    return calls


def _contract(**overrides) -> ConjecturerTurnWireContractV6:
    values = {"reasoning": False, "aliases": AliasTable({"SRC_001": "c1"})}
    values.update(overrides)
    return ConjecturerTurnWireContractV6(**values)


def _research_value(count: int = 1) -> dict:
    return {
        "research_proposals": [
            {
                "request_identifier": f"req-{index}",
                "purpose": "ground the mechanism in the published note",
                "urls": [f"https://example.org/page-{index}"],
            }
            for index in range(count)
        ]
    }


def test_research_proposals_are_hidden_and_rejected_when_disabled():
    contract = _contract()
    schema = contract.model_json_schema()
    assert "research_proposals" not in schema.get("properties", {})
    with pytest.raises(V6WireReferenceError, match="research is disabled"):
        contract.validate_value(_research_value())


def test_enabled_contract_binds_the_frozen_per_turn_ceiling():
    contract = _contract(
        research_enabled=True,
        maximum_research_proposals=MAXIMUM_PROPOSALS_PER_TURN,
    )
    schema = contract.model_json_schema()
    assert (
        schema["properties"]["research_proposals"]["maxItems"]
        == MAXIMUM_PROPOSALS_PER_TURN
    )
    wire = contract.validate_value(_research_value())
    turn = contract.compile(wire)
    assert isinstance(turn, ConjectureTurnV6)
    (draft,) = turn.research_proposals
    assert draft.urls == ("https://example.org/page-0",)
    with pytest.raises(V6WireReferenceError, match="per-turn authority"):
        contract.validate_value(
            _research_value(MAXIMUM_PROPOSALS_PER_TURN + 1)
        )


def test_enabled_contract_requires_a_coherent_ceiling():
    with pytest.raises(ValueError, match="per-turn maximum in 1..2"):
        _contract(research_enabled=True, maximum_research_proposals=0)
    with pytest.raises(ValueError, match="zero proposal maximum"):
        _contract(research_enabled=False, maximum_research_proposals=1)


def test_research_free_turn_dump_stays_byte_identical():
    """Digest-stable schema growth: a turn without research proposals dumps
    without the field at all, so stored semantic outputs never shift."""

    turn = ConjectureTurnV6(
        candidates=(
            {
                "content": "x",
                "typicality": 0.5,
                "refs": [],
                "evidence_refs": [],
            },
        )
    )
    dump = turn.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert "research_proposals" not in dump
    canonical_json(dump)  # remains canonicalizable


def test_capability_grant_carries_research_outcome_only_when_enabled():
    baseline = compile_workflow_profile(_manifest())
    assert (
        CapabilityOutcome.RESEARCH_REQUEST
        not in baseline.capability_grant().allowed_outcomes
    )
    enabled = compile_workflow_profile(_manifest(research=_research_policy()))
    assert (
        CapabilityOutcome.RESEARCH_REQUEST
        in enabled.capability_grant().allowed_outcomes
    )


def test_v6_turn_research_proposal_fetches_and_consumes_in_cycle(
    tmp_path, monkeypatch
):
    calls = _patch_transport(
        monkeypatch,
        {"https://example.org/tides": (200, "text/html", None, PAGE)},
    )
    manifest = _manifest(research=_research_policy())
    harness = ScratchService(tmp_path / "research-cycle").harness
    _seed_live_conjecture(harness)
    response = {
        "candidates": [
            {"content": "A tide-linked bounded mechanism.", "typicality": 0.4}
        ],
        "research_proposals": [
            {
                "request_identifier": "req-tides",
                "purpose": "ground the mechanism in the published tide note",
                "urls": ["https://example.org/tides"],
            }
        ],
    }
    adapter, _endpoint = _live_adapter(harness, manifest, [json.dumps(response)])

    registered = conj(
        harness,
        "pi-live-v6",
        adapter,
        _config(),
        workload_profile="text",
        run_manifest=manifest,
    )

    (artifact,) = registered
    (work,) = harness.workflow_state.transaction_work.values()
    assert work.terminal.status == "completed"
    assert work.terminal.reason_code == "semantic_admission_complete"
    assert calls == ["https://example.org/tides"]

    (proposal,) = (
        p
        for p in harness.capability_state.proposals.values()
        if isinstance(p, ResearchFetchProposalV1)
    )
    assert proposal.originating_work_order_ref == work.preparation.id
    lifecycles = [
        t.lifecycle
        for t in harness.capability_state.transitions.values()
        if t.request_ref == proposal.id
    ]
    assert lifecycles.count(CapabilityLifecycle.PROPOSED) == 1
    assert lifecycles.count(CapabilityLifecycle.CONSUMED) == 1
    (receipt,) = (
        r
        for r in harness.capability_state.receipts.values()
        if isinstance(r, ResearchExecutionReceiptV1)
    )
    assert receipt.outcome == "fetched"
    (consumption,) = (
        c
        for c in harness.capability_state.consumptions.values()
        if isinstance(c, ResearchConsumptionV1)
    )
    assert consumption.evidence_refs

    # The admitted transaction names the research proposal as an effect.
    (admission,) = work.admissions.values()
    assert artifact.id in admission.admitted_refs
    assert proposal.id in admission.admitted_refs

    # Consumed material is citable in-run before any later turn.
    assert consumed_research_blocks(harness)


def test_v6_turn_off_allowlist_research_is_a_typed_denial(
    tmp_path, monkeypatch
):
    calls = _patch_transport(monkeypatch, {})
    manifest = _manifest(research=_research_policy())
    harness = ScratchService(tmp_path / "research-denied").harness
    _seed_live_conjecture(harness)
    response = {
        "candidates": [
            {"content": "A mechanism independent of the fetch.", "typicality": 0.4}
        ],
        "research_proposals": [
            {
                "request_identifier": "req-evil",
                "purpose": "reach outside the frozen allowlist",
                "urls": ["https://evil.example.com/x"],
            }
        ],
    }
    adapter, _endpoint = _live_adapter(harness, manifest, [json.dumps(response)])

    registered = conj(
        harness,
        "pi-live-v6",
        adapter,
        _config(),
        workload_profile="text",
        run_manifest=manifest,
    )

    assert len(registered) == 1
    assert calls == []  # never dispatched
    (work,) = harness.workflow_state.transaction_work.values()
    assert work.terminal.status == "completed"
    assert work.terminal.reason_code == "semantic_admission_complete"
    denials = [
        t
        for t in harness.capability_state.transitions.values()
        if t.lifecycle == CapabilityLifecycle.DENIED
    ]
    assert len(denials) == 1
    assert denials[0].reason_code == "url_outside_frozen_allowlist"
    assert not consumed_research_blocks(harness)


def test_v6_turn_without_research_authority_rejects_the_wire_field(
    tmp_path, monkeypatch
):
    """A research-disabled manifest never exposes the field: a response that
    volunteers research_proposals is a schema violation entering the local
    repair ladder, not a silent drop."""

    calls = _patch_transport(monkeypatch, {})
    manifest = _manifest()
    harness = ScratchService(tmp_path / "research-unauthorized").harness
    _seed_live_conjecture(harness)
    response = {
        "candidates": [
            {"content": "A mechanism with no fetch authority.", "typicality": 0.4}
        ],
        "research_proposals": [
            {
                "request_identifier": "req-unauthorized",
                "purpose": "propose research without authority",
                "urls": ["https://example.org/tides"],
            }
        ],
    }
    repair = (
        '{"schema":"repair.patch.v1","op":"remove","path":"/research_proposals"}'
    )
    adapter, _endpoint = _live_adapter(
        harness, manifest, [json.dumps(response), repair]
    )

    registered = conj(
        harness,
        "pi-live-v6",
        adapter,
        _config(),
        workload_profile="text",
        run_manifest=manifest,
    )

    assert calls == []
    assert not any(
        isinstance(p, ResearchFetchProposalV1)
        for p in harness.capability_state.proposals.values()
    )
    from deepreason.workflow.models import WorkflowTaskKind

    (work,) = (
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.CONJECTURE
    )
    assert work.terminal.status == "rejected"
    assert work.terminal.reason_code == "conjecture_repair_requested"
    (repair_work,) = (
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.REPAIR
    )
    assert repair_work.terminal.status == "completed"
    assert len(registered) == 1
