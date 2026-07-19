"""Crash-prefix recovery for every non-conjecture v6 provider family."""

from __future__ import annotations

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
from deepreason.llm.wire import AliasTable, BatchCriticWireContractV2
from deepreason.ontology import (
    Interface,
    LLMAttempt,
    LLMCall,
    Provenance,
    Rule,
    SchoolRouteReceiptV1,
)
from deepreason.oracle import property_oracle_commitment
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
from deepreason.scratch.models import (
    ClusterGuideV1,
    InstanceRef,
    LLMCallRef,
    ScratchActor,
    ScratchBlockBodyV1,
    ScratchProvenanceV1,
)
from deepreason.scratch.service import ScratchService
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
    call_prompt: str | None = None,
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
    recorded_prompt = prompt if call_prompt is None else call_prompt
    recorded_prompt_ref = harness.blobs.put(recorded_prompt.encode("utf-8"))
    raw_ref = harness.blobs.put(raw)
    call = LLMCall(
        role=role,
        model=route.model_id,
        endpoint=route.base_url,
        prompt_ref=recorded_prompt_ref,
        raw_ref=raw_ref,
        tokens=2,
        prompt_tokens=1,
        completion_tokens=1,
        work_order_id=authorized.bundle.work_id,
        dispatch_authorization_ref=authorized.bundle.id,
        attempt_trace=(
            [
                LLMAttempt(
                    prompt_ref=recorded_prompt_ref,
                    raw_ref=raw_ref,
                    contract_id=contract_id,
                    endpoint_id=route.endpoint_id,
                    route_sha256=route_fingerprint(route),
                    seat=seat,
                    valid=True,
                )
            ]
            if task_kind == WorkflowTaskKind.CRITICISM
            else []
        ),
        school_route=(
            SchoolRouteReceiptV1(
                school_id=payload["critic_school_id"],
                role=role,
                seat=seat,
                endpoint_id=route.endpoint_id,
                route_sha256=route_fingerprint(route),
                contract_id=contract_id,
            )
            if task_kind == WorkflowTaskKind.CRITICISM
            else None
        ),
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


def _criticism_prefix(
    root,
    manifest,
    *,
    raw=b'{"cases":[]}',
    attempt_index=0,
    phase="qualification",
    caller_trigger_ref=None,
    target_factory=None,
):
    harness = Harness(root)
    target = (
        target_factory(harness)
        if target_factory is not None
        else harness.create_artifact(
            "one school-owned target",
            provenance=Provenance(role="conjecturer", school="school-0"),
        )
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
        "coverage_attempt_index": attempt_index,
        "phase": phase,
        "caller_trigger_ref": caller_trigger_ref,
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
        attempt_index=attempt_index,
    )
    return preparation, provider, target, assignment


def test_recovered_criticism_applies_canonical_effect_exactly_once(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "criticism"
    preparation, provider, target, assignment = _criticism_prefix(
        root,
        manifest,
        raw=(
            b'{"cases":[{"target_alias":"SRC_001","attack":true,'
            b'"case":"the mechanism omits a required boundary"}]}'
        ),
    )

    reopened, item, admission = _recover(root, manifest, provider)

    assert item.terminal.status == "completed"
    assert admission.outcome == "admitted"
    critics = [
        artifact
        for artifact in reopened.state.artifacts.values()
        if artifact.provenance.role == "critic"
        and artifact.provenance.school == "school-1"
    ]
    assert len(critics) == 1
    assert critics[0].content_ref == "inline:the mechanism omits a required boundary"
    attempts = [
        record
        for event in reopened.log.read()
        for object_id in event.outputs
        for schema, record in (reopened.objects.get(object_id),)
        if schema == "criticism-attempt-v1"
    ]
    assert len(attempts) == 1
    assert attempts[0].assignment_ref == assignment.id
    assert attempts[0].coverage_completed is True
    assert sum(
        event.rule == Rule.MEASURE
        and list(event.inputs)
        == ["scrutiny", target.id, critics[0].id, f"source:{attempts[0].source_call_seq}"]
        for event in reopened.log.read()
    ) == 1
    before = tuple(reopened.log.read())
    rerecovered, repeated_item, repeated_admission = _recover(root, manifest, provider)
    assert tuple(rerecovered.log.read()) == before
    assert repeated_item.terminal == item.terminal
    assert repeated_admission == admission
    assert assignment.id in preparation.input_refs


def test_identical_critic_effects_remain_isolated_by_source_transaction(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "criticism-identical-transactions"
    raw = (
        b'{"cases":[{"target_alias":"SRC_001","attack":true,'
        b'"case":"the same criticism from two authorized attempts"}]}'
    )
    _first_preparation, first_provider, target, _assignment = _criticism_prefix(
        root,
        manifest,
        raw=raw,
        attempt_index=0,
    )
    _second_preparation, second_provider, _target, _assignment = _criticism_prefix(
        root,
        manifest,
        raw=raw,
        attempt_index=1,
    )

    first, _first_item, _first_admission = _recover(root, manifest, first_provider)
    second, _second_item, _second_admission = _recover(root, manifest, second_provider)

    critic = next(
        artifact
        for artifact in second.state.artifacts.values()
        if artifact.provenance.role == "critic"
    )
    source_seqs = {
        event.llm.work_order_id: event.seq
        for event in second.log.read()
        if event.llm is not None
        and event.llm.work_order_id
        in {first_provider.work_id, second_provider.work_id}
    }
    scrutiny = [
        event
        for event in second.log.read()
        if event.rule == Rule.MEASURE
        and list(event.inputs[:3]) == ["scrutiny", target.id, critic.id]
    ]
    assert len(scrutiny) == 2
    assert {event.inputs[3] for event in scrutiny} == {
        f"source:{source_seqs[first_provider.work_id]}",
        f"source:{source_seqs[second_provider.work_id]}",
    }
    before = tuple(second.log.read())
    repeated, _item, _admission = _recover(root, manifest, first_provider)
    assert tuple(repeated.log.read()) == before
    assert len(first.state.artifacts) == len(second.state.artifacts)


def test_counterexample_retry_recovery_uses_retry_semantics_without_coverage(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "criticism-retry-withdrawn"
    caller = "foreign-criticism:school-1:route"
    _primary, _primary_provider, _target, assignment = _criticism_prefix(
        root,
        manifest,
        raw=(
            b'{"cases":[{"target_alias":"SRC_001","attack":true,'
            b'"case":"the primary case","counterexample":["invalid"]}]}'
        ),
        phase="primary",
        caller_trigger_ref=caller,
    )
    _retry, retry_provider, _target, _assignment = _criticism_prefix(
        root,
        manifest,
        raw=(
            b'{"cases":[{"target_alias":"SRC_001","attack":false,'
            b'"case":"","counterexample":null}]}'
        ),
        phase="counterexample_retry:0",
        caller_trigger_ref=caller,
    )

    reopened, item, admission = _recover(root, manifest, retry_provider)

    assert item.terminal.status == "completed"
    assert admission.outcome == "admitted"
    assert not any(
        event.inputs[:1]
        in (["scrutiny"], ["arg-crit-overridden-by-execution"])
        for event in reopened.log.read()
    )
    assert not any(
        schema == "criticism-attempt-v1"
        and record.assignment_ref == assignment.id
        for event in reopened.log.read()
        for object_id in event.outputs
        for schema, record in (reopened.objects.get(object_id),)
    )
    before = tuple(reopened.log.read())
    repeated, _item, _admission = _recover(root, manifest, retry_provider)
    assert tuple(repeated.log.read()) == before


def test_retry_without_authoritative_predecessor_appends_no_admission(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "criticism-retry-missing-predecessor"
    preparation, provider, _target, _assignment = _criticism_prefix(
        root,
        manifest,
        raw=(
            b'{"cases":[{"target_alias":"SRC_001","attack":false,'
            b'"case":"","counterexample":null}]}'
        ),
        phase="counterexample_retry:0",
        caller_trigger_ref="missing-primary-caller",
    )
    reopened = Harness(root)
    before = tuple(reopened.log.read())

    with pytest.raises(
        NonConjectureRecoveryAuthorityError,
        match="no unique durable predecessor",
    ):
        recover_nonconjecture_admission(
            reopened,
            manifest,
            TokenMeter(100_000),
            provider,
        )

    assert tuple(reopened.log.read()) == before
    item = reopened.workflow_state.transaction_work[preparation.id]
    assert item.admissions == {}
    assert item.terminal is None


def test_grounded_counterexample_recovery_does_not_invent_override_on_repeat(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "criticism-grounded-counterexample"
    checker = (
        "def check(inp, out):\n"
        "    xs = inp[0]\n"
        "    return isinstance(out, list) and sorted(xs) == out\n"
    )
    gate = (
        "def valid(inp):\n"
        "    return (isinstance(inp, list) and len(inp) == 1 and "
        "isinstance(inp[0], list) and "
        "all(isinstance(x, int) for x in inp[0]))\n"
    )

    def target_factory(harness):
        commitment = property_oracle_commitment(
            "solve",
            [[[3, 1, 2]]],
            checker,
            gate,
        )
        harness.register_commitment(commitment)
        return harness.create_artifact(
            "def solve(xs):\n    return sorted(xs) if len(xs) > 2 else xs\n",
            codec="code:python",
            interface=Interface(commitments=[commitment.id]),
            provenance=Provenance(role="conjecturer", school="school-0"),
        )

    _preparation, provider, target, _assignment = _criticism_prefix(
        root,
        manifest,
        raw=(
            b'{"cases":[{"target_alias":"SRC_001","attack":true,'
            b'"case":"fails on two integers","counterexample":[[2,1]]}]}'
        ),
        target_factory=target_factory,
    )

    reopened, _item, _admission = _recover(root, manifest, provider)

    assert any(
        warrant.target == target.id and warrant.verdict == "fail"
        for warrant in reopened.warrants.values()
    )
    assert not any(
        event.inputs[:1] == ["arg-crit-overridden-by-execution"]
        for event in reopened.log.read()
    )
    before = tuple(reopened.log.read())
    repeated, _item, _admission = _recover(root, manifest, provider)
    assert tuple(repeated.log.read()) == before
    assert not any(
        event.inputs[:1] == ["arg-crit-overridden-by-execution"]
        for event in repeated.log.read()
    )


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


def _scratch_prefix(
    root,
    manifest,
    *,
    raw=b'{"content":"a deliberately daring provisional mechanism"}',
    provider_role="conjecturer",
    call_prompt=None,
):
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
    preparation, provider = _provider_prefix(
        harness,
        manifest,
        task_kind=WorkflowTaskKind.SCRATCH_AUTHORING,
        role=provider_role,
        contract_id="scratch.block.compact.v1",
        payload=payload,
        trigger_prefix="scratch-authoring:",
        raw=raw,
        input_refs=(context_ref, rendered_ref, task_ref),
        items=(visible,),
        call_prompt=call_prompt,
    )
    return preparation, provider


def test_recovered_scratch_applies_advisory_block_exactly_once(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "scratch"
    _preparation, provider = _scratch_prefix(root, manifest)

    reopened, item, admission = _recover(root, manifest, provider)

    assert item.terminal.status == "completed"
    assert admission.outcome == "admitted"
    assert len(reopened.scratch_state.blocks) == 1
    block = next(iter(reopened.scratch_state.blocks.values()))
    assert block.body.content == "a deliberately daring provisional mechanism"
    assert block.provenance.actor.value == "llm"
    assert block.provenance.origin == "conjecturer:scratch-block"
    assert block.id == admission.admitted_refs[0]
    before = tuple(reopened.log.read())
    rerecovered, repeated_item, repeated_admission = _recover(root, manifest, provider)
    assert tuple(rerecovered.log.read()) == before
    assert len(rerecovered.scratch_state.blocks) == 1
    assert repeated_item.terminal == item.terminal
    assert repeated_admission == admission


def test_recovery_reuses_scratch_effect_already_applied_before_admission(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "scratch-effect-before-admission"
    preparation, provider = _scratch_prefix(root, manifest)
    harness = Harness(root)
    work = harness.workflow_state.transaction_work[preparation.id]
    block = ScratchService(harness).create_block(
        ScratchBlockBodyV1(content="a deliberately daring provisional mechanism"),
        ScratchProvenanceV1(
            actor=ScratchActor.LLM,
            origin="conjecturer:scratch-block",
        ),
        context_ref=work.exposure.id,
    )
    scratch_events_before = tuple(
        event for event in harness.log.read() if event.scratch is not None
    )

    reopened, item, admission = _recover(root, manifest, provider)

    assert item.terminal.status == "completed"
    assert admission.admitted_refs == (block.id,)
    assert tuple(
        event for event in reopened.log.read() if event.scratch is not None
    ) == scratch_events_before
    assert len(reopened.scratch_state.blocks) == 1


def test_completed_guide_recovery_uses_its_historical_snapshot(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "guide-historical-snapshot"
    harness = Harness(root)
    scratch = ScratchService(harness)
    provenance = ScratchProvenanceV1(actor=ScratchActor.USER, origin="test")
    block = scratch.create_block(ScratchBlockBodyV1(content="initial member"), provenance)
    cluster = scratch.create_cluster("moving cluster", provenance)
    scratch.add_cluster_member(cluster.id, block.id, None, provenance)
    snapshot = scratch.cluster_snapshot(cluster.id)
    receipt = ScratchRenderReceiptV1.create(
        state_seq=harness._next_seq,
        attention_receipt="sha256:" + "b" * 64,
        block_handles={"B1": block.id},
        cluster_handles={"C1": cluster.id},
        link_handles={},
        guide_handles={},
    )
    receipt_bytes = canonical_json(receipt.model_dump(mode="json", by_alias=True))
    rendered_bytes = b"historical rendered cluster context"
    task_bytes = b"write a temporary guide"
    context_ref = harness.blobs.put(receipt_bytes)
    rendered_ref = harness.blobs.put(rendered_bytes)
    task_ref = harness.blobs.put(task_bytes)
    payload = {
        "schema": "scratch.authoring-task.v1",
        "operation": "guide",
        "ordinal": 0,
        "purpose": "imaginative_workshop",
        "epistemic_boundary": "advisory_non_grounding",
        "role": "summarizer",
        "seat": 0,
        "template_role": "scratch_guide",
        "contract_id": "scratch.cluster-guide.compact.v1",
        "output_model": "ClusterGuideDraftV1",
        "context_receipt_ref": context_ref,
        "context_receipt_hash": receipt.receipt_hash,
        "task_ref": task_ref,
        "task_sha256": hashlib.sha256(task_bytes).hexdigest(),
        "operation_payload": {
            "cluster_id": cluster.id,
            "cluster_snapshot": snapshot.snapshot_hash,
        },
    }
    visible = VisibleContextItemV1(
        namespace=ContextNamespace.SCRATCH,
        alias="SCR_001",
        object_ref=rendered_ref,
        content_sha256=hashlib.sha256(rendered_bytes).hexdigest(),
        planned_bytes=len(rendered_bytes),
    )
    preparation, provider = _provider_prefix(
        harness,
        manifest,
        task_kind=WorkflowTaskKind.SCRATCH_AUTHORING,
        role="summarizer",
        contract_id="scratch.cluster-guide.compact.v1",
        payload=payload,
        trigger_prefix="scratch-authoring:",
        raw=b'{"working_focus":"the historical guide"}',
        target_refs=(cluster.id,),
        input_refs=(context_ref, rendered_ref, task_ref),
        items=(visible,),
    )
    source_event = next(
        event
        for event in harness.log.read()
        if event.llm is not None and event.llm.work_order_id == provider.work_id
    )
    guide = ClusterGuideV1.create(
        cluster_id=cluster.id,
        based_on_snapshot=snapshot.snapshot_hash,
        working_focus="the historical guide",
        authored_by=LLMCallRef(
            event_seq=source_event.seq,
            model=source_event.llm.model,
            endpoint=source_event.llm.endpoint,
            prompt_ref=source_event.llm.prompt_ref,
            raw_ref=source_event.llm.raw_ref,
        ),
        instance=InstanceRef(run_id=scratch.run_id, seq=harness._next_seq),
    )
    scratch.store_guide(
        guide,
        context_ref=harness.workflow_state.transaction_work[preparation.id].exposure.id,
    )
    later = scratch.create_block(ScratchBlockBodyV1(content="later member"), provenance)
    scratch.add_cluster_member(cluster.id, later.id, None, provenance)
    assert scratch.cluster_snapshot(cluster.id).snapshot_hash != snapshot.snapshot_hash
    guide_events_before = tuple(
        event
        for event in harness.log.read()
        if event.scratch is not None and guide.id in event.outputs
    )

    reopened, item, admission = _recover(root, manifest, provider)

    assert item.terminal.status == "completed"
    assert admission.admitted_refs == (guide.id,)
    assert tuple(
        event
        for event in reopened.log.read()
        if event.scratch is not None and guide.id in event.outputs
    ) == guide_events_before


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


def test_invalid_stored_scratch_output_fails_closed_without_effect(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "scratch-invalid"
    preparation, provider = _scratch_prefix(
        root,
        manifest,
        raw=b'{"unexpected":"not a scratch block"}',
    )

    reopened, item, admission = _recover(root, manifest, provider)

    assert item.terminal.status == "schema_exhausted"
    assert admission.outcome == "schema_exhausted"
    assert reopened.scratch_state.blocks == {}
    before = tuple(reopened.log.read())
    rerecovered, repeated_item, repeated_admission = _recover(root, manifest, provider)
    assert tuple(rerecovered.log.read()) == before
    assert repeated_item.terminal == item.terminal
    assert repeated_admission == admission
    assert preparation.id == provider.work_id


def test_scheduler_recovers_valid_critic_without_provider_dispatch(tmp_path):
    config, manifest = _manifest()
    root = tmp_path / "scheduler-valid-critic"
    raw = (
        b'{"cases":[{"target_alias":"SRC_001","attack":true,'
        b'"case":"a recovered canonical criticism"}]}'
    )
    preparation, provider, target, _assignment = _criticism_prefix(
        root,
        manifest,
        raw=raw,
    )
    reopened = Harness(root)
    output = BatchCriticWireContractV2(
        AliasTable({"SRC_001": target.id}),
        expected_targets=(target.id,),
    ).parse_compile(raw.decode("utf-8"))
    admitted_ref = reopened.blobs.put(
        canonical_json(output.model_dump(mode="json", exclude_none=True))
    )
    transaction = InquiryTransactionService(
        reopened,
        manifest,
        TokenMeter(100_000),
    )
    admission = transaction.record_semantic_admission(
        provider,
        outcome="admitted",
        admitted_refs=(admitted_ref,),
    )
    transaction.terminate(
        work_id=provider.work_id,
        attempt_index=provider.attempt_index,
        status="completed",
        reason_code="critic_output_admitted",
        usage_status="exact",
        prompt_tokens=provider.prompt_tokens,
        completion_tokens=provider.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    assert not any(
        artifact.provenance.role == "critic"
        for artifact in reopened.state.artifacts.values()
    )
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
    assert item.terminal.status == "completed"
    assert len(
        [
            artifact
            for artifact in reopened.state.artifacts.values()
            if artifact.provenance.role == "critic"
        ]
    ) == 1
    assert calls == []


def test_mismatched_rendered_request_fails_before_recovery_append(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "request-mismatch"
    preparation, provider = _scratch_prefix(
        root,
        manifest,
        call_prompt="a different rendered request",
    )
    reopened = Harness(root)
    before = tuple(reopened.log.read())

    with pytest.raises(
        NonConjectureRecoveryAuthorityError,
        match="durable prompt bytes differ",
    ):
        recover_nonconjecture_admission(
            reopened,
            manifest,
            TokenMeter(100_000),
            provider,
        )

    assert tuple(reopened.log.read()) == before
    assert reopened.workflow_state.transaction_work[preparation.id].terminal is None


def test_mismatched_scratch_role_fails_before_recovery_append(tmp_path):
    _config_value, manifest = _manifest()
    root = tmp_path / "role-mismatch"
    preparation, provider = _scratch_prefix(
        root,
        manifest,
        provider_role="synthesizer",
    )
    reopened = Harness(root)
    before = tuple(reopened.log.read())

    with pytest.raises(NonConjectureRecoveryAuthorityError, match="scratch role differs"):
        recover_nonconjecture_admission(
            reopened,
            manifest,
            TokenMeter(100_000),
            provider,
        )

    assert tuple(reopened.log.read()) == before
    assert reopened.workflow_state.transaction_work[preparation.id].terminal is None


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("work_id", "sha256:" + "1" * 64, "names no replayed transaction"),
        (
            "authorization_bundle_ref",
            "sha256:" + "2" * 64,
            "provider attempt is not the replayed result",
        ),
    ),
)
def test_mismatched_work_or_transaction_identity_fails_without_append(
    tmp_path, field, value, message
):
    _config_value, manifest = _manifest()
    root = tmp_path / field
    preparation, provider = _scratch_prefix(root, manifest)
    forged = provider.model_copy(update={field: value})
    reopened = Harness(root)
    before = tuple(reopened.log.read())

    with pytest.raises(NonConjectureRecoveryAuthorityError, match=message):
        recover_nonconjecture_admission(
            reopened,
            manifest,
            TokenMeter(100_000),
            forged,
        )

    assert tuple(reopened.log.read()) == before
    assert reopened.workflow_state.transaction_work[preparation.id].terminal is None


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
