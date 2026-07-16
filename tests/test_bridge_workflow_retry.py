"""A3: bounded fresh-workflow retries are policy-owned and replayable."""

from __future__ import annotations

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
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.ontology.event import LLMAttempt, LLMCall


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


def _run(outcomes, policy, fence, catalog=None):
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
