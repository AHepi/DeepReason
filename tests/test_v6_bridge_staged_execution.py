"""Focused staged-bridge execution and exact-once recovery regressions."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from deepreason.harness import Harness
from deepreason.run_manifest import WorkflowRetryPolicyV1
from deepreason.workflow.transaction_service import InquiryTransactionService
from deepreason.workflow.replay import WorkflowReplayState

from tests.test_v6_bridge_transactions import (
    _InjectedBridgeAdmissionCrash,
    _bind_recovery_manifest,
    _recovery_adapter,
    _run_recovery_bridge,
    _seed_recovery_problem,
)


def _staged_responses():
    return (
        ("summarizer", "not-json"),
        (
            "summarizer",
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "CLM_1",
                            "claim_class": "surviving_conjecture",
                            "claim": "A novel conjecture survives the formal record.",
                            "formal_artifact_handles": ["ART_1"],
                        }
                    ]
                }
            ),
        ),
        ("thesis", "not-json"),
        (
            "thesis",
            json.dumps(
                {
                    "sections": [
                        {
                            "span_id": "S1",
                            "text": "Conjecture: the surviving idea may explain the result.",
                            "ledger_entry_handles": ["E2"],
                        }
                    ],
                    "resolution": "partially_answered",
                    "resolution_reason": (
                        "The record supports a conjecture, not a fact."
                    ),
                }
            ),
        ),
        (
            "judge",
            json.dumps(
                {
                    "finding": "unsupported",
                    "message": "The supplied passage does not ground the span.",
                }
            ),
        ),
        ("judge", json.dumps({"action": "remove_span"})),
    )


def _contracts(harness):
    return tuple(
        item.preparation.contract_id
        for item in harness.workflow_state.transaction_work.values()
    )


def test_strong_bridge_exhaustion_uses_separate_staged_work_and_effects(tmp_path):
    root = tmp_path / "staged-bridge"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _staged_responses(),
        dispatches,
    )

    result = _run_recovery_bridge(harness, manifest, problem_id, adapter)

    assert result.process_status == "success"
    assert dispatches == [
        "summarizer",
        "summarizer",
        "thesis",
        "thesis",
        "judge",
        "judge",
    ]
    assert _contracts(harness) == (
        "bridge.ledger.v3",
        "bridge.ledger-batch.v1",
        "bridge.composition.v2",
        "bridge.composition-batch.v1",
        "groundingverdictwirev1.direct.v1",
        "groundingrepairwirev1.direct.v1",
    )
    items = tuple(harness.workflow_state.transaction_work.values())
    assert tuple(item.terminal.status for item in items) == (
        "schema_exhausted",
        "completed",
        "schema_exhausted",
        "completed",
        "completed",
        "completed",
    )
    transitions = tuple(
        harness.workflow_state.contract_decomposition_by_source_work.values()
    )
    assert tuple(
        (item.source_contract_id, item.atomic_contract_id, item.child_keys)
        for item in transitions
    ) == (
        (
            "bridge.ledger.v3",
            "bridge.ledger-batch.v1",
            ("catalog-batch-000",),
        ),
        (
            "bridge.composition.v2",
            "bridge.composition-batch.v1",
            ("ledger-batch-000",),
        ),
    )
    completions = tuple(
        harness.workflow_state.contract_decomposition_completion_by_transition.values()
    )
    assert len(completions) == 2
    assert all(len(item.admitted_effect_refs) == 1 for item in completions)
    for item in completions:
        for ref in item.admitted_effect_refs:
            assert harness.objects.get(ref)[1].id == ref

    restarted = Harness(root)
    assert restarted.workflow_state.contract_decomposition_by_source_work == (
        harness.workflow_state.contract_decomposition_by_source_work
    )
    assert restarted.workflow_state.contract_decomposition_completion_by_transition == (
        harness.workflow_state.contract_decomposition_completion_by_transition
    )


def test_staged_child_durable_result_recovers_without_redispatch(
    tmp_path, monkeypatch
):
    root = tmp_path / "staged-bridge-recovery"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    initial_dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _staged_responses(),
        initial_dispatches,
    )
    original = InquiryTransactionService.record_semantic_admission

    def crash_on_ledger_batch(self, provider_attempt, **kwargs):
        item = self.harness.workflow_state.transaction_work[provider_attempt.work_id]
        if item.preparation.contract_id == "bridge.ledger-batch.v1":
            raise _InjectedBridgeAdmissionCrash()
        return original(self, provider_attempt, **kwargs)

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_on_ledger_batch,
    )
    with pytest.raises(_InjectedBridgeAdmissionCrash):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)
    assert initial_dispatches == ["summarizer", "summarizer"]

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original,
    )
    remaining_dispatches = []
    restarted = Harness(root)
    restarted_adapter = _recovery_adapter(
        restarted,
        manifest,
        _staged_responses()[2:],
        remaining_dispatches,
    )
    result = _run_recovery_bridge(
        restarted,
        manifest,
        problem_id,
        restarted_adapter,
    )

    assert result.process_status == "success"
    assert remaining_dispatches == ["thesis", "thesis", "judge", "judge"]
    assert _contracts(restarted) == (
        "bridge.ledger.v3",
        "bridge.ledger-batch.v1",
        "bridge.composition.v2",
        "bridge.composition-batch.v1",
        "groundingverdictwirev1.direct.v1",
        "groundingrepairwirev1.direct.v1",
    )
    assert len(restarted.workflow_state.contract_decomposition_by_source_work) == 2
    assert (
        len(
            restarted.workflow_state.contract_decomposition_completion_by_transition
        )
        == 2
    )


@pytest.mark.parametrize(
    ("marker_seq", "effect_outputs"),
    (
        (5, {4: ("effect-ref",)}),
        (15, {}),
    ),
)
def test_replay_rejects_nonchronological_or_unreachable_staged_effect(
    marker_seq, effect_outputs
):
    state = WorkflowReplayState()
    state.transaction_calls_by_seq[10] = SimpleNamespace(work_order_id="child-work")
    state.event_inputs_by_seq[marker_seq] = (
        "contract-decomposition-effect",
        "transition-ref",
        "effect-ref",
    )
    state.event_outputs_by_seq.update(effect_outputs)
    transition = SimpleNamespace(
        child_partition="bridge_catalog_batch",
        id="transition-ref",
    )
    result = SimpleNamespace(preparation=SimpleNamespace(id="child-work"))

    with pytest.raises(ValueError):
        state._validate_contract_decomposition_effects(
            transition,
            (result,),
            ("effect-ref",),
            completion_event_seq=20,
        )
