"""A3: bounded fresh-workflow retries are policy-owned and replayable."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from deepreason.bridge.events import BridgeAction
from deepreason.bridge.ledger import ClaimLedgerInputCatalogV1
from deepreason.bridge.retry import (
    BridgeWorkflowAttemptFenceV1,
    WorkflowRetryBoundaryError,
    WorkflowRetryPolicyV1,
    authorize_workflow_retry,
    run_bridge_workflow_with_retries,
)
from deepreason.bridge.workflow import BridgeWorkflowPolicy
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import EndpointLease
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.ontology.event import LLMAttempt, LLMCall
from deepreason.run_manifest import Route


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


def _catalog() -> ClaimLedgerInputCatalogV1:
    return ClaimLedgerInputCatalogV1.create(
        problem_ref="problem-retry",
        formal_seq=7,
        problem_text="What is supported?",
        output_target="answer",
        items=[],
    )


def _fence(catalog=None, **changes) -> BridgeWorkflowAttemptFenceV1:
    catalog = catalog or _catalog()
    values = {
        "manifest_digest": "a" * 64,
        "formal_seq": catalog.formal_seq,
        "catalog_id": catalog.id,
        "contract_id": "bridge.claim-ledger.compact.v2",
        "prompt_policy_digest": "b" * 64,
        "role": "summarizer",
        "seat": 0,
        "endpoint_id": "mock:retry-seat",
        "route_sha256": "c" * 64,
    }
    values.update(changes)
    return BridgeWorkflowAttemptFenceV1(**values)


def _call(fence, *, valid=False, tokens=11):
    attempt = LLMAttempt(
        prompt_ref="prompt",
        raw_ref="raw",
        diagnostic_ref="diagnostic" if not valid else "",
        contract_id=fence.contract_id,
        endpoint_id=fence.endpoint_id,
        route_sha256=fence.route_sha256,
        seat=fence.seat,
        tokens=tokens,
        valid=valid,
    )
    return LLMCall(
        role=fence.role,
        model="offline",
        endpoint="mock://retry",
        prompt_ref="prompt",
        raw_ref="raw",
        tokens=tokens,
        attempt_trace=[attempt],
    )


def _result(fence, status, number, *, code="BRIDGE_LEDGER_REPAIR_EXHAUSTED"):
    return SimpleNamespace(
        formal_seq=fence.formal_seq,
        process_status=status,
        error_code=code if status == "failure" else None,
        token_count=11,
        model_calls=[_call(fence, valid=status == "success")],
        failure_id=_hash(str(number)),
    )


class _Workflow:
    def __init__(self, result):
        self.result = result

    def run(self, _catalog, _request, *, materials=None):
        return self.result


def _run(outcomes, policy, fence, catalog=None, **bindings):
    catalog = catalog or _catalog()
    calls = []
    receipts = []

    def factory(attempt_number):
        calls.append(attempt_number)
        return _Workflow(outcomes[attempt_number - 1])

    result = run_bridge_workflow_with_retries(
        factory,
        catalog,
        object(),
        retry_policy=policy,
        attempt_fence=fence,
        failure_id_for_result=lambda item: item.failure_id,
        persist_retry=receipts.append,
        **bindings,
    )
    return result, calls, receipts


def test_no_workflow_retry_occurs_by_default():
    catalog = _catalog()
    fence = _fence(catalog)
    first = _result(fence, "failure", 1)

    result, calls, receipts = _run([first], WorkflowRetryPolicyV1(), fence, catalog)

    assert result is first
    assert calls == [1]
    assert receipts == []


def test_one_listed_retry_uses_a_fresh_workflow_and_preserves_prior_receipt():
    catalog = _catalog()
    fence = _fence(catalog)
    policy = WorkflowRetryPolicyV1(
        max_workflow_retries=1,
        retryable_error_codes=("BRIDGE_LEDGER_REPAIR_EXHAUSTED",),
    )
    first = _result(fence, "failure", 1)
    second = _result(fence, "success", 2)

    result, calls, receipts = _run([first, second], policy, fence, catalog)

    assert result is second
    assert calls == [1, 2]
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt.prior_failure_id == first.failure_id
    assert receipt.attempt_number == receipt.maximum_attempts == 2
    assert receipt.prior_token_count == first.token_count
    assert receipt.attempt_fence == fence


def test_unlisted_error_and_retry_ceiling_stop_without_an_extra_attempt():
    catalog = _catalog()
    fence = _fence(catalog)
    policy = WorkflowRetryPolicyV1(
        max_workflow_retries=1,
        retryable_error_codes=("BRIDGE_LEDGER_REPAIR_EXHAUSTED",),
    )
    unlisted = _result(fence, "failure", 1, code="BRIDGE_OTHER_FAILURE")
    result, calls, receipts = _run([unlisted], policy, fence, catalog)
    assert result is unlisted and calls == [1] and receipts == []

    first = _result(fence, "failure", 1)
    second = _result(fence, "failure", 2)
    result, calls, receipts = _run([first, second], policy, fence, catalog)
    assert result is second
    assert calls == [1, 2]
    assert len(receipts) == 1


def test_retry_fails_closed_on_catalog_contract_route_or_formal_fence_change():
    catalog = _catalog()
    fence = _fence(catalog)
    policy = WorkflowRetryPolicyV1(
        max_workflow_retries=1,
        retryable_error_codes=("BRIDGE_LEDGER_REPAIR_EXHAUSTED",),
    )

    with pytest.raises(WorkflowRetryBoundaryError, match="CATALOG_CHANGED"):
        _run(
            [_result(fence, "failure", 1)],
            policy,
            _fence(catalog, catalog_id=_hash("f")),
            catalog,
        )

    wrong_route = _fence(catalog, route_sha256="d" * 64)
    with pytest.raises(WorkflowRetryBoundaryError, match="ROUTE_CHANGED"):
        _run([_result(wrong_route, "failure", 1)], policy, fence, catalog)

    wrong_contract = _fence(catalog, contract_id="bridge.claim-ledger.compact.v1")
    with pytest.raises(WorkflowRetryBoundaryError, match="CONTRACT_CHANGED"):
        _run([_result(wrong_contract, "failure", 1)], policy, fence, catalog)

    wrong_formal = _result(fence, "failure", 1)
    wrong_formal.formal_seq = 8
    with pytest.raises(WorkflowRetryBoundaryError, match="FORMAL_FENCE_CHANGED"):
        _run([wrong_formal], policy, fence, catalog)

    with pytest.raises(WorkflowRetryBoundaryError, match="MANIFEST_CHANGED"):
        _run(
            [_result(fence, "failure", 1)],
            policy,
            fence,
            catalog,
            manifest_digest="f" * 64,
        )
    with pytest.raises(WorkflowRetryBoundaryError, match="PROMPT_POLICY_CHANGED"):
        _run(
            [_result(fence, "failure", 1)],
            policy,
            fence,
            catalog,
            prompt_policy_digest="f" * 64,
        )


def test_policy_is_frozen_bounded_and_canonical():
    with pytest.raises(ValidationError, match="listed error code"):
        WorkflowRetryPolicyV1(max_workflow_retries=1)
    with pytest.raises(ValidationError, match="sorted"):
        WorkflowRetryPolicyV1(
            max_workflow_retries=1,
            retryable_error_codes=("Z_ERROR", "A_ERROR"),
        )
    with pytest.raises(ValidationError):
        WorkflowRetryPolicyV1(max_workflow_retries=3, retryable_error_codes=("E",))

    policy = WorkflowRetryPolicyV1()
    assert WorkflowRetryPolicyV1.model_validate(policy.model_dump()) == policy
    with pytest.raises((AttributeError, ValidationError)):
        policy.max_workflow_retries = 1


def test_retry_authorization_is_a_canonical_replayable_bridge_event(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_problem(
        Problem(
            id="problem-retry",
            description="What is supported?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    invalid = "never valid"
    adapter = LLMAdapter(
        {
            "summarizer": MockEndpoint([invalid, invalid, invalid]),
            "thesis": MockEndpoint([]),
        },
        harness.blobs,
        retry_max=2,
    )
    terminal = harness.build_bridge(
        "problem-retry",
        "answer",
        {"grounding_review": False, "max_grounding_repair_attempts": 0},
        run_manifest_digest="a" * 64,
        stage_a_adapter=adapter,
    )
    failure = harness.bridge_state.failures[terminal.failure_id]
    failed_call = list(harness.log.read())[-1].llm
    attempt = failed_call.attempt_trace[-1]
    fence = BridgeWorkflowAttemptFenceV1(
        manifest_digest="a" * 64,
        formal_seq=failure.formal_seq,
        catalog_id=failure.catalog_id,
        contract_id=attempt.contract_id,
        prompt_policy_digest="b" * 64,
        role=failed_call.role,
        seat=attempt.seat,
        endpoint_id=attempt.endpoint_id,
        route_sha256=attempt.route_sha256,
    )
    policy = WorkflowRetryPolicyV1(
        max_workflow_retries=1,
        retryable_error_codes=(failure.error_code,),
    )
    retry = authorize_workflow_retry(
        policy,
        prior_failure_id=failure.id,
        error_code=failure.error_code,
        completed_retries=0,
        attempt_fence=fence,
        prior_token_count=failed_call.tokens,
    )
    formal_before = harness.state.model_dump_json()

    event = harness.record_bridge_event(
        BridgeAction.WORKFLOW_RETRY_STARTED,
        inputs=[failure.id],
        records=[("bridge-workflow-retry", retry)],
    )

    assert event.llm is None
    assert harness.bridge_state.workflow_retries[retry.id] == retry
    assert harness.state.model_dump_json() == formal_before
    reopened = Harness(harness.root)
    assert reopened.bridge_state.workflow_retries[retry.id] == retry
    assert reopened.bridge_state == harness.bridge_state


def test_production_coordinator_uses_v2_and_persists_before_fresh_attempt(
    tmp_path, monkeypatch
):
    """Exercise the v4 harness branch without constructing a live endpoint."""

    from deepreason.bridge import harness as bridge_harness

    harness = Harness(tmp_path / "run")
    harness.register_problem(
        Problem(
            id="problem-retry",
            description="What is supported?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    route = Route(
        endpoint_id="mock:bridge-v4",
        base_url="https://models.invalid/v1",
        model_id="offline-v4",
        provider="fixture",
        family="fixture",
        max_tokens=512,
    )
    retry_policy = WorkflowRetryPolicyV1(
        max_workflow_retries=2,
        retryable_error_codes=("BRIDGE_LEDGER_REPAIR_EXHAUSTED",),
    )
    effective = BridgeWorkflowPolicy(
        grounding_review=False,
        max_grounding_repair_attempts=0,
        ledger_contract_version="v2",
    )
    monkeypatch.setattr(
        bridge_harness,
        "_bound_bridge_execution",
        lambda *_args, **_kwargs: (
            effective,
            retry_policy,
            EndpointLease("summarizer", 0, route),
        ),
    )
    summarizer = MockEndpoint(
        [
            "not-json",
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "CLM_1",
                            "claim_class": "source_fact",
                            "claim": "Unsupported.",
                            "source_handles": ["SRC_99"],
                        }
                    ]
                }
            ),
            '{"entries":[]}',
        ],
        name=route.base_url,
        model=route.model_id,
    )
    thesis = MockEndpoint(
        [
            json.dumps(
                {
                    "sections": [],
                    "unresolved_items": [
                        {
                            "description": "The answer remains unsupported.",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    "resolution": "insufficient_evidence",
                    "resolution_reason": "The sealed catalog is insufficient.",
                }
            )
        ],
        name=route.base_url,
        model=route.model_id,
    )
    adapter = LLMAdapter(
        {"summarizer": summarizer, "thesis": thesis},
        harness.blobs,
        retry_max=0,
        model_profile="compact",
        leases={
            "summarizer": (EndpointLease("summarizer", 0, route),),
            "thesis": (EndpointLease("thesis", 0, route),),
        },
    )

    terminal = harness.build_bridge(
        "problem-retry",
        "answer",
        BridgeWorkflowPolicy(
            grounding_review=False, max_grounding_repair_attempts=0
        ),
        run_manifest_digest="a" * 64,
        stage_a_adapter=adapter,
        composition_adapter=adapter,
    )

    assert terminal.process_status == "success"
    retries = list(harness.bridge_state.workflow_retries.values())
    assert len(retries) == 2
    first_retry, second_retry = sorted(retries, key=lambda item: item.attempt_number)
    assert first_retry.attempt_number == 2
    assert second_retry.attempt_number == 3
    assert second_retry.prior_retry_id == first_retry.id
    assert second_retry.prior_token_count > first_retry.prior_token_count
    assert first_retry.attempt_fence.contract_id == "bridge.claim-ledger.compact.v2"
    assert all(
        retry.next_attempt_id in harness.bridge_state.retry_attempt_ids
        for retry in retries
    )
    actions = [event.bridge.action for event in harness.log.read() if event.bridge]
    failed_index = actions.index(BridgeAction.FAILED)
    retry_index = actions.index(BridgeAction.WORKFLOW_RETRY_STARTED)
    next_ledger_index = actions.index(BridgeAction.LEDGER_CREATED, retry_index + 1)
    assert failed_index < retry_index < next_ledger_index
    calls = [event.llm for event in harness.log.read() if event.llm]
    ledger_attempts = [
        attempt
        for call in calls
        if call.role == "summarizer"
        for attempt in call.attempt_trace
    ]
    assert len(ledger_attempts) == 3
    assert {attempt.contract_id for attempt in ledger_attempts} == {
        "bridge.claim-ledger.compact.v2"
    }
    assert Harness(harness.root).bridge_state == harness.bridge_state


def test_v4_bridge_route_mismatch_fails_before_provider_dispatch(tmp_path, monkeypatch):
    from deepreason.bridge import harness as bridge_harness

    harness = Harness(tmp_path / "run")
    harness.register_problem(
        Problem(
            id="problem-retry",
            description="What is supported?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    frozen_route = Route(
        endpoint_id="manifest-seat",
        base_url="https://manifest.invalid/v1",
        model_id="manifest-model",
        provider="fixture",
        family="fixture",
        max_tokens=512,
    )
    effective = BridgeWorkflowPolicy(
        grounding_review=False,
        max_grounding_repair_attempts=0,
        ledger_contract_version="v2",
    )
    monkeypatch.setattr(
        bridge_harness,
        "_bound_bridge_execution",
        lambda *_args, **_kwargs: (
            effective,
            WorkflowRetryPolicyV1(),
            EndpointLease("summarizer", 0, frozen_route),
        ),
    )
    calls = 0

    def response(_prompt):
        nonlocal calls
        calls += 1
        return '{"entries":[]}'

    runtime_route = frozen_route.model_copy(
        update={"endpoint_id": "substituted-seat"}
    )
    endpoint = MockEndpoint(
        response,
        name=runtime_route.base_url,
        model=runtime_route.model_id,
    )
    adapter = LLMAdapter(
        {"summarizer": endpoint},
        harness.blobs,
        retry_max=0,
        leases={
            "summarizer": (EndpointLease("summarizer", 0, runtime_route),),
        },
    )

    with pytest.raises(WorkflowRetryBoundaryError, match="ROUTE_CHANGED"):
        harness.build_bridge(
            "problem-retry",
            "answer",
            BridgeWorkflowPolicy(
                grounding_review=False, max_grounding_repair_attempts=0
            ),
            run_manifest_digest="a" * 64,
            stage_a_adapter=adapter,
        )

    assert calls == 0
    assert not harness.bridge_state.event_seqs
