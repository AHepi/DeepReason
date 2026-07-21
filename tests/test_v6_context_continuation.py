"""Integrated qualification for transactional v6 context continuations."""

from __future__ import annotations

import json

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json
from deepreason.capabilities.policy import InquiryCapabilityPolicyV1
from deepreason.config import Config
from deepreason.conjecture_turn import ContextRequestV1, ConjectureTurnV6
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.ontology import Commitment, LLMCall, Problem, ProblemProvenance
from deepreason.rules.conj import conj
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    SchoolExecutionPolicyV1,
    compile_run_manifest,
)
from deepreason.scratch.models import RetrievalChannel, ScratchProvenanceV1
from deepreason.scratch.service import ScratchService
from deepreason.workflow.context_continuation import (
    ConjectureContextContinuationV1,
    ContextContinuationEligibility,
)
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction_service import InquiryTransactionService
from tests.test_v6_compact_recovery_transition import _bind_classification


STAMP = "2026-07-17T00:00:00Z"


def _route(*, context_window_tokens: int | None = None) -> dict:
    route = {
        "endpoint_id": "v6-context-conjecturer",
        "endpoint": "mock://v6-context-conjecturer",
        "model": "offline-v6-context-model",
        "provider": "mock",
        "family": "offline-v6-context-family",
        "max_tokens": 64,
        "context_window_tokens": (
            262_144 if context_window_tokens is None else context_window_tokens
        ),
    }
    return route


def _config(*, context_window_tokens: int | None = None) -> Config:
    return Config(
        N_SCHOOLS=0,
        RETRY_MAX=0,
        roles={
            "conjecturer": [
                _route(context_window_tokens=context_window_tokens)
            ]
        },
        scratchpad={
            "enabled": True,
            "max_blocks_per_pack": 4,
            "max_guides_per_pack": 0,
            "semantic_retrieval": False,
            "keyword_retrieval": True,
            "coverage_enabled": False,
            "exploratory_fraction": 0.0,
            "underexposed_fraction": 0.0,
        },
    )


def _manifest(config: Config, *, max_expansions: int = 1):
    context = ConjectureContextPolicyV1(
        mode="harness_plus_model_request",
        initial_max_blocks=1,
        initial_max_guides=0,
        max_context_expansion_requests=max_expansions,
        max_extra_blocks=max_expansions,
        permitted_retrieval_channels=("focus", "keyword"),
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )
    control = ControlPlanePolicyV3(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=context,
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
    )
    return compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2"
        ),
        run_input_digest="c" * 64,
    )


def _seed(harness: Harness):
    harness.register_commitment(
        Commitment(id="k-v6-context", eval="predicate:len(content) > 0")
    )
    problem = harness.register_problem(
        Problem(
            id="pi-v6-context",
            description="Stretch a delayed-feedback mechanism imaginatively.",
            criteria=["k-v6-context"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    scratch = ScratchService(harness)
    provenance = ScratchProvenanceV1(actor="user", origin="v6-context-test")
    focus = scratch.create_block(
        {"content": "Delayed feedback is the root imaginative fragment."},
        provenance.model_copy(update={"formal_artifact_refs": [problem.id]}),
    )
    expansion = scratch.create_block(
        {"content": "quasar-only topology is a distant speculative rival."},
        provenance,
    )
    tertiary = scratch.create_block(
        {"content": "tertiary-only material needs another bounded expansion."},
        provenance,
    )
    return problem, focus, expansion, tertiary


def _adapter(harness, manifest, responses, *, meter=None):
    pending = [json.dumps(item) for item in responses]
    prompts: list[str] = []
    route = manifest.roles["conjecturer"][0]

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        if not pending:
            raise AssertionError("unexpected extra conjecturer dispatch")
        return pending.pop(0)

    endpoint = MockEndpoint(
        complete,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=0,
        meter=meter or TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    _bind_classification(harness, manifest)
    adapter.bind_v6_authority(harness, manifest)
    return adapter, prompts


def _request(query: str) -> dict:
    return {
        "context_request": {
            "query": query,
            "desired_retrieval_channels": ["keyword"],
            "purpose": "Retrieve one more speculative scratch fragment.",
        }
    }


def _abstention() -> dict:
    return {
        "abstention": {
            "search_signal": "stuck",
            "note": "The bounded expansion is sufficient for this turn.",
        }
    }


def _run(harness, manifest, config, adapter):
    return conj(
        harness,
        "pi-v6-context",
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )


def test_granted_request_dispatches_fresh_bound_child_work(tmp_path):
    config = _config()
    manifest = _manifest(config)
    harness = Harness(tmp_path / "granted")
    _problem, focus, expansion, _tertiary = _seed(harness)
    adapter, prompts = _adapter(
        harness,
        manifest,
        [_request("quasar-only"), _abstention()],
    )

    assert _run(harness, manifest, config, adapter) == []

    parent, child = tuple(harness.workflow_state.transaction_work.values())
    assert len(prompts) == 2
    assert parent.terminal.status == child.terminal.status == "completed"
    assert parent.preparation.id != child.preparation.id
    assert parent.authorization.id != child.authorization.id
    assert parent.reservation.id != child.reservation.id
    binding = child.preparation.task_payload_value["context_continuation"]
    assert binding["parent_work_id"] == parent.preparation.id
    assert binding["parent_provider_attempt_ref"] in child.preparation.input_refs
    assert binding["request_ref"] in child.preparation.input_refs
    assert binding["decision_ref"] in child.preparation.input_refs
    assert binding["eligibility"] == "eligible"
    child_scratch = [
        item.object_ref
        for item in child.exposure.exposed_items
        if item.namespace.value == "scratch"
    ]
    assert child_scratch == [focus.id, expansion.id]
    calls = [event.llm for event in harness.log.read() if event.llm is not None]
    assert [call.work_order_id for call in calls] == [
        parent.preparation.id,
        child.preparation.id,
    ]
    assert [call.dispatch_authorization_ref for call in calls] == [
        parent.authorization.id,
        child.authorization.id,
    ]
    parent_context, child_context = [call.conjecture_context for call in calls]
    assert parent_context is not None and child_context is not None
    assert parent_context != child_context
    assert child_context.prior_selection_receipt_ref == (
        parent_context.selection_receipt_ref
    )
    assert child_context.expansion_decision_ref == binding["decision_ref"]
    assert child_context.root_block_refs == [focus.id]
    assert child_context.added_block_refs == [expansion.id]
    parent_render = harness.blobs.get(
        parent_context.rendered_context_ref
    ).decode("utf-8")
    child_render = harness.blobs.get(
        child_context.rendered_context_ref
    ).decode("utf-8")
    assert parent_render != child_render
    assert prompts[0].count(parent_render) == 1
    assert prompts[1].count(child_render) == 1
    scratch_state = ScratchService(harness).state
    assert scratch_state.attention_receipts[
        parent_context.selection_receipt_ref
    ].final_order == [focus.id]
    assert scratch_state.attention_receipts[
        child_context.selection_receipt_ref
    ].final_order == [focus.id, expansion.id]
    attention_before = dict(scratch_state.attention_receipts)
    advisory_before = dict(scratch_state.advisory_contexts)
    visibility_before = dict(scratch_state.visibility)
    coverage_before = dict(scratch_state.coverage_cycles)
    reopened = Harness(harness.root)
    assert len(reopened.workflow_state.transaction_work) == 2
    reopened_state = ScratchService(reopened).state
    assert reopened_state.attention_receipts == attention_before
    assert reopened_state.advisory_contexts == advisory_before
    assert reopened_state.visibility == visibility_before
    assert reopened_state.coverage_cycles == coverage_before


def test_limit_exhaustion_is_typed_unissued_and_does_not_dispatch(tmp_path):
    config = _config()
    manifest = _manifest(config, max_expansions=1)
    harness = Harness(tmp_path / "limit")
    _seed(harness)
    adapter, prompts = _adapter(
        harness,
        manifest,
        [_request("quasar-only"), _request("tertiary-only")],
    )

    assert _run(harness, manifest, config, adapter) == []

    parent, expanded, denied = tuple(
        harness.workflow_state.transaction_work.values()
    )
    assert len(prompts) == 2
    assert parent.terminal.status == expanded.terminal.status == "completed"
    assert denied.terminal.status == "abandoned"
    assert denied.terminal.reason_code == "context_request_limit_reached"
    assert denied.exposure is None
    assert denied.authorization is None
    assert denied.provider_attempts == {}
    binding = denied.preparation.task_payload_value["context_continuation"]
    assert binding["parent_work_id"] == expanded.preparation.id
    assert binding["expansion_index"] == 2
    assert binding["maximum_expansions"] == 1
    Harness(harness.root)


class _DenySecondReservationMeter(TokenMeter):
    def __init__(self):
        super().__init__(100_000)
        self.reserve_attempts = 0

    def reserve(self, **kwargs):
        self.reserve_attempts += 1
        if self.reserve_attempts == 2:
            raise TokenBudgetExceeded("injected child reservation denial")
        return super().reserve(**kwargs)


def test_child_budget_denial_has_no_exposure_and_no_dispatch(tmp_path):
    config = _config()
    manifest = _manifest(config)
    harness = Harness(tmp_path / "budget")
    _problem, focus, expansion, _tertiary = _seed(harness)
    meter = _DenySecondReservationMeter()
    adapter, prompts = _adapter(
        harness,
        manifest,
        [_request("quasar-only")],
        meter=meter,
    )

    assert _run(harness, manifest, config, adapter) == []

    parent, denied = tuple(harness.workflow_state.transaction_work.values())
    assert len(prompts) == 1
    assert parent.terminal.status == "completed"
    assert denied.terminal.status == "budget_denied"
    assert denied.exposure is None
    assert denied.authorization is None
    assert denied.provider_attempts == {}
    assert meter.reserve_attempts == 2
    (parent_call,) = [
        event.llm for event in harness.log.read() if event.llm is not None
    ]
    parent_context = parent_call.conjecture_context
    assert parent_context is not None
    scratch_state = ScratchService(harness).state
    assert set(scratch_state.attention_receipts) == {
        parent_context.selection_receipt_ref
    }
    assert set(scratch_state.advisory_contexts) == {
        parent_context.advisory_context_ref
    }
    assert scratch_state.visibility[focus.id].render_count == 1
    assert expansion.id not in scratch_state.visibility
    assert scratch_state.coverage_cycles == {}
    reopened_state = ScratchService(Harness(harness.root)).state
    assert reopened_state.attention_receipts == scratch_state.attention_receipts
    assert reopened_state.advisory_contexts == scratch_state.advisory_contexts
    assert reopened_state.visibility == scratch_state.visibility
    assert reopened_state.coverage_cycles == scratch_state.coverage_cycles


def test_child_request_envelope_overflow_is_unissued_and_scratch_clean(tmp_path):
    probe_config = _config()
    probe_manifest = _manifest(probe_config)
    probe = Harness(tmp_path / "envelope-probe")
    _problem, _focus, _expansion, _tertiary = _seed(probe)
    ScratchService(probe).create_block(
        {
            "content": "nebula-overflow " + ("advisory possibility " * 300),
        },
        ScratchProvenanceV1(actor="user", origin="v6-envelope-probe"),
    )
    probe_adapter, probe_prompts = _adapter(
        probe,
        probe_manifest,
        [_request("nebula-overflow"), _abstention()],
    )
    assert _run(probe, probe_manifest, probe_config, probe_adapter) == []
    assert len(probe_prompts) == 2
    parent_total = len(probe_prompts[0].encode("utf-8")) + 64
    child_total = len(probe_prompts[1].encode("utf-8")) + 64
    assert child_total > parent_total + 1000

    capacity = parent_total + 512
    config = _config(context_window_tokens=capacity)
    manifest = _manifest(config)
    harness = Harness(tmp_path / "envelope-target")
    _problem, focus, expansion, _tertiary = _seed(harness)
    large = ScratchService(harness).create_block(
        {
            "content": "nebula-overflow " + ("advisory possibility " * 300),
        },
        ScratchProvenanceV1(actor="user", origin="v6-envelope-probe"),
    )
    adapter, prompts = _adapter(
        harness,
        manifest,
        [_request("nebula-overflow")],
    )

    assert _run(harness, manifest, config, adapter) == []

    parent, denied = tuple(harness.workflow_state.transaction_work.values())
    assert len(prompts) == 1
    assert len(prompts[0].encode("utf-8")) + 64 <= capacity
    assert parent.terminal.status == "completed"
    assert denied.terminal.status == "abandoned"
    assert denied.terminal.reason_code == "request_envelope_exceeded"
    assert denied.terminal.usage_status == "exact"
    assert (denied.terminal.prompt_tokens, denied.terminal.completion_tokens) == (0, 0)
    assert denied.issued is False
    assert denied.reservation is None
    assert denied.exposure is None
    assert denied.authorization is None
    assert denied.provider_attempts == {}
    parent_call, = [
        event.llm for event in harness.log.read() if event.llm is not None
    ]
    parent_context = parent_call.conjecture_context
    assert parent_context is not None
    scratch_state = ScratchService(harness).state
    assert set(scratch_state.attention_receipts) == {
        parent_context.selection_receipt_ref
    }
    assert set(scratch_state.advisory_contexts) == {
        parent_context.advisory_context_ref
    }
    assert scratch_state.visibility[focus.id].render_count == 1
    assert expansion.id not in scratch_state.visibility
    assert large.id not in scratch_state.visibility
    assert scratch_state.coverage_cycles == {}
    assert adapter.meter.snapshot()["reserved"] == 0


def _route_lease(manifest) -> RouteLeaseRefV1:
    route = manifest.roles["conjecturer"][0]
    return RouteLeaseRefV1(
        role="conjecturer",
        seat=0,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
    )


def _manual_completed_parent(harness, manifest, request, meter):
    _bind_classification(harness, manifest)
    service = InquiryTransactionService(harness, manifest, meter)
    fence = harness._next_seq - 1
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=_route_lease(manifest),
        contract_id="conjecturer.turn.v6",
        trigger_ref="manual-context-parent",
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
        target_refs=("pi-v6-context",),
        input_refs=("k-v6-context",),
        task_payload_value={"schema": "conjecture.semantic-task.v2"},
    )
    prompt = "manual admitted parent prompt"
    authorized = service.issue(
        preparation,
        plans=(),
        prompt=prompt,
        max_tokens=8,
    )
    route = manifest.roles["conjecturer"][0]
    raw = canonical_json(
        ConjectureTurnV6(context_request=request).model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
    )
    call = LLMCall(
        role="conjecturer",
        model=route.model_id,
        endpoint=route.base_url,
        prompt_ref=harness.blobs.put(prompt.encode("utf-8")),
        raw_ref=harness.blobs.put(raw),
        tokens=2,
        prompt_tokens=1,
        completion_tokens=1,
        work_order_id=authorized.bundle.work_id,
        dispatch_authorization_ref=authorized.bundle.id,
    )
    authorized.reservation.settle(
        {"prompt_tokens": 1, "completion_tokens": 1}
    )
    provider = service.record_provider_attempt(
        authorized,
        call=call,
        outcome="provider_result",
        usage_status="exact",
    )
    source_seq = harness._next_seq - 1
    semantic_output_ref = harness.blobs.put(raw)
    admission = service.record_semantic_admission(
        provider,
        outcome="admitted",
        admitted_refs=(semantic_output_ref,),
    )
    service.terminate(
        work_id=preparation.id,
        attempt_index=preparation.attempt_index,
        status="completed",
        reason_code="semantic_admission_complete",
        usage_status="exact",
        prompt_tokens=1,
        completion_tokens=1,
        provider_attempt=provider,
        admission=admission,
    )
    return preparation, authorized, provider, admission, semantic_output_ref, source_seq


def test_unpermitted_channel_is_typed_denied_without_child_dispatch(tmp_path):
    config = _config()
    manifest = _manifest(config)
    harness = Harness(tmp_path / "channel")
    _seed(harness)
    meter = TokenMeter(100_000)
    request = ContextRequestV1(
        query="recent speculative fragment",
        desired_retrieval_channels=(RetrievalChannel.RECENT,),
        purpose="Exercise the runtime policy backstop.",
    )
    (
        parent,
        authorized,
        provider,
        admission,
        semantic_output_ref,
        source_seq,
    ) = _manual_completed_parent(harness, manifest, request, meter)
    request_ref = harness.blobs.put(
        canonical_json(
            request.model_dump(mode="json", by_alias=True, exclude_none=True)
        )
    )
    binding = ConjectureContextContinuationV1.create(
        manifest_digest=manifest.sha256,
        problem_id="pi-v6-context",
        parent_work_id=parent.id,
        parent_attempt_index=provider.attempt_index,
        parent_provider_attempt_ref=provider.id,
        parent_exposure_receipt_ref=authorized.exposure_receipt.id,
        parent_semantic_admission_ref=admission.id,
        parent_semantic_output_ref=semantic_output_ref,
        parent_provider_event_seq=source_seq,
        request_hash=request.request_hash,
        request_ref=request_ref,
        expansion_index=1,
        maximum_expansions=1,
        maximum_extra_blocks=1,
        policy_mode="harness_plus_model_request",
        permitted_retrieval_channels=("focus", "keyword"),
        desired_retrieval_channels=("recent",),
    )
    assert binding.eligibility == ContextContinuationEligibility.CHANNEL_NOT_PERMITTED
    adapter, prompts = _adapter(harness, manifest, [], meter=meter)

    assert conj(
        harness,
        "pi-v6-context",
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
        _context_expansion_index=1,
        _v6_context_continuation=binding,
        _v6_context_request=request,
    ) == []

    _parent_item, denied = tuple(harness.workflow_state.transaction_work.values())
    assert prompts == []
    assert denied.terminal.status == "abandoned"
    assert denied.terminal.reason_code == "context_channel_not_permitted"
    assert denied.exposure is None
    assert denied.authorization is None
    assert denied.provider_attempts == {}
    Harness(harness.root)
