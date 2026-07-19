"""Crash-prefix recovery for every non-conjecture v6 provider family."""

from __future__ import annotations

from copy import deepcopy
import hashlib

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.repair import (
    RepairDiagnosticEnvelopeV2,
    RepairDiagnosticV2,
)
from deepreason.ontology import LLMCall, Provenance
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    CriticismPolicyV1,
    SchoolExecutionPolicyV1,
    SchoolRoleBindingV1,
    ScratchAuthoringPolicyV1,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.scratch.render import ScratchRenderReceiptV1
from deepreason.workflow.criticism import CriticismAssignmentV1
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.nonconjecture_recovery import (
    NonConjectureRecoveryAuthorityError,
    recover_nonconjecture_admission,
)
from deepreason.workflow.transaction import (
    ContextNamespace,
    VisibleContextItemV1,
)
from deepreason.workflow.transaction_service import InquiryTransactionService


STAMP = "2026-07-18T00:00:00Z"


def _route(role: str, seat: int = 0) -> dict:
    return {
        "endpoint_id": f"{role}-{seat}-route",
        "endpoint": f"mock://{role}-{seat}",
        "model": f"offline-{role}-{seat}",
        "provider": "mock",
        "family": f"offline-{role}-{seat}",
        "max_tokens": 64,
    }


def _config() -> Config:
    return Config(
        N_SCHOOLS=3,
        RETRY_MAX=0,
        scratchpad={"enabled": True},
        roles={
            "conjecturer": [_route("conjecturer")],
            "synthesizer": [_route("synthesizer")],
            "summarizer": [_route("summarizer")],
            "thesis": [_route("thesis")],
            "judge": [_route("judge")],
            "argumentative_critic": [
                _route("argumentative_critic", seat) for seat in range(3)
            ],
        },
        bridge={
            "mode": "grounded_two_stage",
            "grounding_review": True,
            "max_schema_repair_attempts": 0,
            "max_grounding_repair_attempts": 2,
        },
    )


def _control() -> ControlPlanePolicyV3:
    return ControlPlanePolicyV3(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="disabled",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=(),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
        scratch_authoring=ScratchAuthoringPolicyV1(
            enabled=True,
            maximum_new_blocks_per_turn=2,
            maximum_revisions_per_turn=1,
            maximum_links_per_turn=2,
            maximum_unresolved_questions_per_turn=2,
            maximum_cluster_suggestions_per_turn=2,
            maximum_total_bytes=64 * 1024,
        ),
    )


def _criticism_policy() -> CriticismPolicyV1:
    return CriticismPolicyV1(
        minimum_foreign_school_coverage=2,
        bindings=tuple(
            SchoolRoleBindingV1(
                school_id=f"school-{seat}",
                role="argumentative_critic",
                seat=seat,
                endpoint_id=f"argumentative_critic-{seat}-route",
            )
            for seat in range(3)
        ),
        max_batch_size=4,
        target_eligibility="accepted_school_artifacts",
        authority="observe_only",
        allow_shared=False,
    )


def _manifest():
    config = _config()
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        criticism_policy=_criticism_policy(),
        run_input_digest="f" * 64,
    )
    return config, manifest


def _lease(manifest, role: str, seat: int = 0) -> RouteLeaseRefV1:
    route = manifest.roles[role][seat]
    return RouteLeaseRefV1(
        role=role,
        seat=seat,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
    )


def _provider_prefix(
    harness: Harness,
    manifest,
    *,
    task_kind: WorkflowTaskKind,
    role: str,
    contract_id: str,
    payload: dict,
    trigger_prefix: str,
    raw: bytes,
    seat: int = 0,
    target_refs: tuple[str, ...] = (),
    input_refs: tuple[str, ...] = (),
    items: tuple[VisibleContextItemV1, ...] = (),
    attempt_index: int = 0,
):
    service = InquiryTransactionService(harness, manifest, TokenMeter(100_000))
    trigger = trigger_prefix + hashlib.sha256(canonical_json(payload)).hexdigest()
    fence = max(0, harness._next_seq - 1)
    preparation = service.prepare(
        task_kind=task_kind,
        attempt_index=attempt_index,
        route_lease=_lease(manifest, role, seat),
        contract_id=contract_id,
        trigger_ref=trigger,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
        target_refs=target_refs,
        input_refs=input_refs,
        task_payload_value=payload,
    )
    rendered = max(1, sum(item.planned_bytes for item in items)) if items else 0
    plans = (
        (
            service.context_plan(
                preparation,
                plan_kind="combined",
                items=items,
                maximum_bytes=rendered,
                rendered_bytes=rendered,
            ),
        )
        if items
        else ()
    )
    prompt = f"authorized {task_kind.value} prompt"
    authorized = service.issue(
        preparation,
        plans=plans,
        prompt=prompt,
        max_tokens=8,
    )
    route = manifest.roles[role][seat]
    call = LLMCall(
        role=role,
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
    return preparation, provider


def _recover(root, manifest, provider):
    reopened = Harness(root)
    before_calls = tuple(event.llm for event in reopened.log.read() if event.llm)
    admission = recover_nonconjecture_admission(
        reopened,
        manifest,
        TokenMeter(100_000),
        provider,
    )
    after_calls = tuple(event.llm for event in reopened.log.read() if event.llm)
    assert after_calls == before_calls
    item = reopened.workflow_state.transaction_work[provider.work_id]
    assert item.terminal is not None
    return reopened, item, admission


def _criticism_prefix(root, manifest, *, raw=b'{"cases":[]}'):
    harness = Harness(root)
    target = harness.create_artifact(
        "one school-owned target",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    lease = _lease(manifest, "argumentative_critic", 1)
    assignment = CriticismAssignmentV1.create(
        manifest_digest=manifest.sha256,
        target_id=target.id,
        owner_school_id="school-0",
        critic_school_id="school-1",
        eligible_school_order=("school-1", "school-2"),
        order_index=0,
        seat=1,
        endpoint_id=lease.endpoint_id,
        route_sha256=lease.route_sha256,
        maximum_attempts=2,
    )
    harness.record_criticism_obligation(assignment)
    payload = {
        "schema": "criticism.semantic-task.v1",
        "critic_school_id": "school-1",
        "target_ids": [target.id],
        "assignment_refs": [assignment.id],
        "coverage_attempt_index": 0,
        "phase": "qualification",
        "caller_trigger_ref": None,
    }
    content = target.content_ref.removeprefix("inline:").encode("utf-8")
    item = VisibleContextItemV1(
        namespace=ContextNamespace.SOURCE,
        alias="SRC_001",
        object_ref=target.id,
        content_sha256=hashlib.sha256(content).hexdigest(),
        planned_bytes=64,
    )
    preparation, provider = _provider_prefix(
        harness,
        manifest,
        task_kind=WorkflowTaskKind.CRITICISM,
        role="argumentative_critic",
        seat=1,
        contract_id="batch-critic.v2",
        payload=payload,
        trigger_prefix="criticism:",
        raw=raw,
        target_refs=(target.id,),
        input_refs=(assignment.id,),
        items=(item,),
    )
    return preparation, provider, target, assignment


def test_recovered_criticism_validates_raw_but_retains_coverage_debt(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "criticism"
    preparation, provider, target, assignment = _criticism_prefix(root, manifest)

    reopened, item, admission = _recover(root, manifest, provider)

    assert item.terminal.status == "rejected"
    assert admission.outcome == "rejected"
    assert item.terminal.reason_code == "recovered_criticism_domain_unapplied"
    assert target.id in reopened.state.artifacts
    assert not any(
        schema == "criticism-attempt-v1"
        for event in reopened.log.read()
        for object_id in event.outputs
        for schema, _record in (reopened.objects.get(object_id),)
    )
    assert assignment.id in preparation.input_refs


def _bridge_prefix(root, manifest, task_kind, template_role, role, contract):
    harness = Harness(root)
    pack = b"one frozen direct bridge pack"
    pack_ref = harness.blobs.put(pack)
    item = VisibleContextItemV1(
        namespace=ContextNamespace.SOURCE,
        alias="SRC_001",
        object_ref=pack_ref,
        content_sha256=hashlib.sha256(pack).hexdigest(),
        planned_bytes=len(pack),
    )
    payload = {
        "schema": "bridge.transaction-task.v1",
        "ordinal": 0,
        "role": role,
        "seat": 0,
        "template_role": template_role,
        "contract_id": contract,
        "output_model": {
            "bridge_ledger": "ClaimLedgerV1",
            "bridge_compose": "CompositionDraftV1",
            "bridge_review": "GroundingVerdictWireV1",
            "bridge_grounding_repair": "GroundingRepairWireV1",
        }[template_role],
        "pack_sha256": hashlib.sha256(pack).hexdigest(),
    }
    return _provider_prefix(
        harness,
        manifest,
        task_kind=task_kind,
        role=role,
        contract_id=contract,
        payload=payload,
        trigger_prefix="bridge:",
        raw=b'{"value":"valid-looking but caller-owned"}',
        input_refs=(pack_ref,),
        items=(item,),
    )


@pytest.mark.parametrize(
    ("task_kind", "template_role", "role", "contract"),
    (
        (
            WorkflowTaskKind.BRIDGE_LEDGER,
            "bridge_ledger",
            "summarizer",
            "bridge.ledger.v3",
        ),
        (
            WorkflowTaskKind.BRIDGE_COMPOSITION,
            "bridge_compose",
            "thesis",
            "bridge.composition.v2",
        ),
        (
            WorkflowTaskKind.BRIDGE_REVIEW,
            "bridge_review",
            "judge",
            "groundingverdictwirev1.direct.v1",
        ),
        (
            WorkflowTaskKind.REPAIR,
            "bridge_grounding_repair",
            "judge",
            "groundingrepairwirev1.direct.v1",
        ),
    ),
)
def test_recovered_bridge_families_never_create_canonical_bridge_state(
    tmp_path, task_kind, template_role, role, contract
):
    _config_value, manifest = _manifest()
    root = tmp_path / template_role
    preparation, provider = _bridge_prefix(
        root, manifest, task_kind, template_role, role, contract
    )
    before_bridge = tuple(
        event for event in Harness(root).log.read() if event.bridge is not None
    )

    reopened, item, admission = _recover(root, manifest, provider)

    assert item.terminal.status == "rejected"
    assert admission.outcome == "rejected"
    assert tuple(
        event for event in reopened.log.read() if event.bridge is not None
    ) == before_bridge
    assert preparation.id == provider.work_id


def test_recovered_scratch_validates_wire_without_creating_scratch_object(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "scratch"
    harness = Harness(root)
    receipt = ScratchRenderReceiptV1.create(
        state_seq=0,
        attention_receipt="sha256:" + "a" * 64,
        block_handles={},
        cluster_handles={},
        link_handles={},
        guide_handles={},
    )
    receipt_bytes = canonical_json(receipt.model_dump(mode="json", by_alias=True))
    rendered_bytes = b"advisory imaginative scratch context"
    task_bytes = b"stretch this idea without claiming it is true"
    context_ref = harness.blobs.put(receipt_bytes)
    rendered_ref = harness.blobs.put(rendered_bytes)
    task_ref = harness.blobs.put(task_bytes)
    payload = {
        "schema": "scratch.authoring-task.v1",
        "operation": "block",
        "ordinal": 0,
        "purpose": "imaginative_workshop",
        "epistemic_boundary": "advisory_non_grounding",
        "role": "conjecturer",
        "seat": 0,
        "template_role": "scratch_block",
        "contract_id": "scratch.block.compact.v1",
        "output_model": "ScratchBlockBodyV1",
        "context_receipt_ref": context_ref,
        "context_receipt_hash": receipt.receipt_hash,
        "task_ref": task_ref,
        "task_sha256": hashlib.sha256(task_bytes).hexdigest(),
        "operation_payload": {},
    }
    visible = VisibleContextItemV1(
        namespace=ContextNamespace.SCRATCH,
        alias="SCR_001",
        object_ref=rendered_ref,
        content_sha256=hashlib.sha256(rendered_bytes).hexdigest(),
        planned_bytes=len(rendered_bytes),
    )
    _preparation, provider = _provider_prefix(
        harness,
        manifest,
        task_kind=WorkflowTaskKind.SCRATCH_AUTHORING,
        role="conjecturer",
        contract_id="scratch.block.compact.v1",
        payload=payload,
        trigger_prefix="scratch-authoring:",
        raw=b'{"content":"a deliberately daring provisional mechanism"}',
        input_refs=(context_ref, rendered_ref, task_ref),
        items=(visible,),
    )
    before_scratch = deepcopy(harness.scratch_state)

    reopened, item, admission = _recover(root, manifest, provider)

    assert item.terminal.status == "rejected"
    assert admission.outcome == "rejected"
    assert reopened.scratch_state == before_scratch


def _terminal_parent(harness, manifest):
    preparation, provider = _bridge_prefix(
        harness.root,
        manifest,
        WorkflowTaskKind.BRIDGE_REVIEW,
        "bridge_review",
        "judge",
        "groundingverdictwirev1.direct.v1",
    )
    harness = Harness(harness.root)
    provider = harness.workflow_state.transaction_work[preparation.id].provider_attempts[0]
    service = InquiryTransactionService(harness, manifest, TokenMeter(100_000))
    diagnostic_ref = harness.blobs.put(b"parent schema rejection")
    admission = service.record_semantic_admission(
        provider,
        outcome="rejected",
        diagnostic_refs=(diagnostic_ref,),
    )
    service.terminate(
        work_id=preparation.id,
        attempt_index=0,
        status="rejected",
        reason_code="parent_repair_requested",
        usage_status="exact",
        prompt_tokens=1,
        completion_tokens=1,
        provider_attempt=provider,
        admission=admission,
    )
    return harness, preparation, provider


def test_recovered_patch_repair_proves_scope_then_leaves_parent_unapplied(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "patch-repair"
    harness, parent, previous_provider = _terminal_parent(Harness(root), manifest)
    baseline = {"fixed": "must remain", "value": "bad"}
    baseline_bytes = canonical_json(baseline)
    baseline_ref = harness.blobs.put(baseline_bytes)
    envelope = RepairDiagnosticEnvelopeV2(
        contract=parent.contract_id,
        baseline_sha256=hashlib.sha256(baseline_bytes).hexdigest(),
        diagnostics=(
            RepairDiagnosticV2(
                path="/value",
                code="invalid_value",
                message="replace the invalid value",
            ),
        ),
        authorized_pointers=("/value",),
        frozen_subtree_hashes=(),
    )
    diagnostic_ref = harness.blobs.put(
        canonical_json(envelope.model_dump(mode="json", by_alias=True))
    )
    payload = {
        "schema": "repair.semantic-task.v1",
        "parent_work_id": parent.id,
        "previous_work_id": parent.id,
        "previous_provider_attempt_ref": previous_provider.id,
        "repair_index": 1,
        "mode": "patch",
        "contract_id": parent.contract_id,
        "authorized_pointers": ["/value"],
        "baseline_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
        "diagnostic_ref": diagnostic_ref,
    }
    _repair, provider = _provider_prefix(
        harness,
        manifest,
        task_kind=WorkflowTaskKind.REPAIR,
        role="judge",
        contract_id=parent.contract_id,
        payload=payload,
        trigger_prefix="repair:",
        raw=(
            b'{"schema":"repair.patch.v1","op":"replace",'
            b'"path":"/value","value":"good"}'
        ),
        input_refs=(parent.id, previous_provider.id, baseline_ref, diagnostic_ref),
        attempt_index=1,
    )

    reopened, item, admission = _recover(root, manifest, provider)

    assert item.terminal.status == "rejected"
    assert admission.outcome == "rejected"
    assert admission.authorized_pointers == ("/value",)
    assert reopened.workflow_state.transaction_work[parent.id].terminal.status == "rejected"


def test_invalid_stored_critic_output_terminalizes_without_scheduler_dispatch(tmp_path):
    config, manifest = _manifest()
    root = tmp_path / "scheduler-invalid"
    preparation, _provider, _target, _assignment = _criticism_prefix(
        root, manifest, raw=b"{not-json"
    )
    reopened = Harness(root)
    calls: list[str] = []

    def forbidden(prompt: str) -> str:
        calls.append(prompt)
        raise AssertionError("recovery redispatched a durable result")

    route = manifest.roles["argumentative_critic"][1]
    adapter = LLMAdapter(
        {
            "argumentative_critic": [
                MockEndpoint(forbidden, name=route.base_url, model=route.model_id)
            ]
        },
        reopened.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    Scheduler(
        reopened,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(0)

    item = reopened.workflow_state.transaction_work[preparation.id]
    assert item.terminal.status == "schema_exhausted"
    assert tuple(item.admissions.values())[0].outcome == "schema_exhausted"
    assert calls == []


def test_authority_mismatch_fails_closed_before_recovery_append(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "authority-mismatch"
    preparation, provider, _target, _assignment = _criticism_prefix(root, manifest)
    reopened = Harness(root)
    before = tuple(reopened.log.read())
    _other_config, other = _manifest()
    other = other.model_copy(update={"compiled_at": "2026-07-18T01:00:00Z"})

    with pytest.raises(NonConjectureRecoveryAuthorityError, match="manifest digest"):
        recover_nonconjecture_admission(
            reopened,
            other,
            TokenMeter(100_000),
            provider,
        )

    assert tuple(reopened.log.read()) == before
    assert reopened.workflow_state.transaction_work[preparation.id].terminal is None
