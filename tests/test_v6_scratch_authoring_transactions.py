"""Standalone scratch authoring uses complete v6 provider transactions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import deepreason.cli.doctor as doctor_module
import deepreason.scratch.authoring as authoring_module
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
    write_production_contract_report,
)
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.llm.adapter import LLMAdapter, RequestEnvelopeExceeded
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import EndpointError, MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.llm.repair import SchemaExhaustedError
from deepreason.ontology import Commitment
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    RunManifest,
    SchoolExecutionPolicyV1,
    ScratchAuthoringPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
    RunManifestError,
    _compile_route_seat_behavioral_capability_plan,
)
from deepreason.scratch.attention import AttentionPlanner
from deepreason.scratch.authoring import ScratchAuthoringError, ScratchAuthoringService
from deepreason.scratch.models import ScratchActor, ScratchProvenanceV1
from deepreason.scratch.proposals import V6_SCRATCH_WORKSHOP_PROMPT
from deepreason.scratch.render import ScratchRenderer
from deepreason.scratch.service import ScratchService
from deepreason.verification import verify_root_report
from deepreason.workflow.models import WorkflowTaskKind
from deepreason.workflow.transaction import ContextNamespace, WorkBudgetDenied
from deepreason.workflow.transaction_service import InquiryTransactionService
from tests.test_scratch_attention import _policy, _request
from tests.test_v6_compact_recovery_transition import _exhaust


STAMP = "2026-07-17T00:00:00Z"


def _route(
    role: str,
    *,
    model_profile: str | None = None,
    context_window_tokens: int | None = None,
) -> dict:
    route = {
        "endpoint_id": f"{role}-scratch-route",
        "endpoint": f"mock://{role}-scratch",
        "model": f"offline-{role}-scratch",
        "provider": "mock",
        "family": f"offline-{role}",
        "max_tokens": 64,
        "context_window_tokens": 262_144,
    }
    if model_profile is not None:
        route["model_profile"] = model_profile
    if context_window_tokens is not None:
        route["context_window_tokens"] = context_window_tokens
    return route


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
            maximum_new_blocks_per_turn=4,
            maximum_revisions_per_turn=4,
            maximum_links_per_turn=4,
            maximum_unresolved_questions_per_turn=4,
            maximum_cluster_suggestions_per_turn=4,
            maximum_total_bytes=128 * 1024,
        ),
    )


def _manifest(
    run_input_digest: str,
    *,
    stamp: str = STAMP,
    route_profiles: dict[str, str] | None = None,
    route_capacities: dict[str, int] | None = None,
):
    route_profiles = route_profiles or {}
    route_capacities = route_capacities or {}
    return compile_run_manifest(
        Config(
            N_SCHOOLS=0,
            RETRY_MAX=2,
            scratchpad={"enabled": True},
            roles={
                role: [
                    _route(
                        role,
                        model_profile=route_profiles.get(role),
                        context_window_tokens=route_capacities.get(role),
                    )
                ]
                for role in (
                    "conjecturer",
                    "argumentative_critic",
                    "synthesizer",
                    "summarizer",
                    "thesis",
                )
            },
            bridge={
                "mode": "grounded_two_stage",
                "grounding_review": False,
                "max_grounding_repair_attempts": 0,
            },
        ),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=stamp,
        control_plane_policy=_control(),
        run_input_digest=run_input_digest,
    )


def _with_grant_ceiling(
    manifest: RunManifest,
    contract_id: str,
    repairs: int,
) -> RunManifest:
    payload = json.loads(manifest.canonical_bytes())
    grant = next(
        grant
        for grant in payload["contract_schema_repair_policy"]["grants"]
        if grant["contract_id"] == contract_id
    )
    grant["maximum_schema_repairs"] = repairs
    grant["maximum_provider_calls"] = repairs + 1
    behavioral_grant = next(
        contract["schema_repair"]
        for entry in payload["route_seat_behavioral_capability_plan"]["entries"]
        for contract in entry["contracts"]
        if contract["contract_id"] == contract_id
    )
    behavioral_grant["maximum_schema_repairs"] = repairs
    behavioral_grant["maximum_provider_calls"] = repairs + 1
    return RunManifest.model_validate(payload)


def _admitted_qualification_case(_manifest, _pair, case_index):
    return ProductionContractCaseResultV1(
        case_id=f"case-{case_index + 1:03d}",
        first_pass_valid=True,
        eventual_valid=True,
        repair_count=0,
        semantic_admission=True,
    )


def _write_qualification(root, manifest):
    policy = manifest.production_qualification_policy
    assert policy is not None
    report = run_production_contract_doctor(
        manifest,
        case_executor=_admitted_qualification_case,
    )
    return write_production_contract_report(
        report,
        root / policy.report_filename,
    )


def _bind_v6_root(
    root,
    *,
    grant_ceiling: tuple[str, int] | None = None,
    route_profiles: dict[str, str] | None = None,
    route_capacities: dict[str, int] | None = None,
    scratch_fallback: bool = True,
):
    commitment = Commitment(id="scratch-is-advisory", eval="predicate:True")
    dossier = EvidenceDossierV1.create(
        problem_ref="scratch-workshop",
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="offline fixture",
            acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id="scratch-workshop",
            description="Explore bold possibilities in advisory scratch.",
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    manifest = _manifest(
        run_input.run_input_digest,
        route_profiles=route_profiles,
        route_capacities=route_capacities,
    )
    if grant_ceiling is not None:
        manifest = _with_grant_ceiling(manifest, *grant_ceiling)
    if not scratch_fallback:
        payload = json.loads(manifest.canonical_bytes())
        plan = payload["route_seat_contract_decomposition_plan"]
        plan["entries"] = [
            entry
            for entry in plan["entries"]
            if not entry["source_contract_id"].startswith("scratch.")
        ]
        payload.pop("route_seat_behavioral_capability_plan")
        provisional = RunManifest.model_validate(payload)
        payload["route_seat_behavioral_capability_plan"] = (
            _compile_route_seat_behavioral_capability_plan(provisional).model_dump(
                mode="json", by_alias=True, exclude_none=True
            )
        )
        manifest = RunManifest.model_validate(payload)
    bind_run_manifest(manifest, root)
    _write_qualification(root, manifest)
    return manifest


def _user() -> ScratchProvenanceV1:
    return ScratchProvenanceV1(actor=ScratchActor.USER, origin="fixture")


def _context(service: ScratchService):
    first = service.create_block({"content": "first possibility"}, _user())
    second = service.create_block({"content": "contrary possibility"}, _user())
    cluster = service.create_cluster("Unresolved mechanisms", _user())
    service.add_cluster_member(cluster.id, first.id, None, _user())
    planner = AttentionPlanner(service, _policy(coverage_enabled=False))
    pack = planner.plan(_request([first.id, second.id], maximum_blocks=2))
    renderer = ScratchRenderer(service)
    rendered = renderer.render_attention_pack(pack)
    planner.commit_render(pack, context_ref="fixture:rendered")
    return renderer, rendered, first, second, cluster


def _adapter(service, manifest, responses, *, budget: int = 100_000):
    endpoints = {}
    for role, scripted in responses.items():
        route = manifest.roles[role][0]
        endpoints[role] = MockEndpoint(
            scripted,
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )
    return (
        LLMAdapter(
            endpoints,
            service.harness.blobs,
            retry_max=0,
            meter=TokenMeter(budget),
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
            transaction_authority_required=True,
        ),
        endpoints,
    )


def _root_bytes(root, *, exclude: tuple[str, ...] = ()):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in Path(root).rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() not in exclude
    }


def _authority_snapshot(service, adapter):
    meter = adapter.meter
    state = service.state
    return {
        "transaction_authority_required": adapter.transaction_authority_required,
        "authority_harness": adapter._v6_authority_harness,
        "authority_manifest": adapter._v6_authority_manifest,
        "compact_roles": frozenset(adapter._compact_recovery_roles),
        "meter_calls": (meter.calls if meter is not None else None),
        "meter_reserved": (meter.reserved if meter is not None else None),
        "event_count": service.harness._next_seq,
        "work_ids": tuple(service.harness.workflow_state.transaction_work),
        "transition_keys": tuple(
            service.harness.workflow_state.compact_recovery_by_route_seat
        ),
        "attention": tuple(state.attention_receipts),
        "advisory": tuple(state.advisory_contexts),
        "visibility": tuple(
            (object_id, value.render_count, value.last_rendered_seq)
            for object_id, value in sorted(state.visibility.items())
        ),
        "coverage": tuple(
            (cycle_id, repr(value))
            for cycle_id, value in sorted(state.coverage_cycles.items())
        ),
        "blocks": tuple(state.blocks),
        "links": tuple(state.links),
        "guides": tuple(
            (cluster_id, tuple(guide.id for guide in guides))
            for cluster_id, guides in sorted(state.guides_by_cluster.items())
        ),
    }


def _invoke(author, operation, rendered, cluster_id=None):
    if operation == "block":
        return author.author_block(rendered, task="Keep the idea provisional")
    if operation == "link":
        return author.author_link(rendered, task="Relate the provisional ideas")
    return author.author_cluster_guide(
        cluster_id,
        rendered,
        task="Guide the unresolved provisional cluster",
    )


def _assert_maximum_task_fails_before_false_exposure(tmp_path, operation: str) -> None:
    root = tmp_path / f"maximum-{operation}-task"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, _first, _second, cluster = _context(service)
    calls: list[str] = []

    def forbidden(prompt: str) -> str:
        calls.append(prompt)
        raise AssertionError("a clipped scratch request reached the provider")

    role = {
        "block": "conjecturer",
        "link": "synthesizer",
        "guide": "summarizer",
    }[operation]
    adapter, _endpoints = _adapter(service, manifest, {role: forbidden})
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    task = "x" * 16_384
    before_events = tuple(service.harness.log.read())

    with pytest.raises(ScratchAuthoringError) as caught:
        if operation == "block":
            author.author_block(rendered, task=task)
        elif operation == "link":
            author.author_link(rendered, task=task)
        else:
            author.author_cluster_guide(cluster.id, rendered, task=task)

    assert caught.value.code == "SCRATCH_CONTEXT_NOT_EXPOSED"
    assert calls == []
    assert service.harness.workflow_state.transaction_work == {}
    added = tuple(service.harness.log.read())[len(before_events):]
    assert added == ()
    assert service.harness.workflow_state.route_seat_model_classification is None
    assert adapter.meter is not None
    assert adapter.meter.reserved == 0
    assert adapter.meter.total == 0
    assert adapter.meter.calls == 0


def test_block_link_and_guide_each_use_complete_independent_transactions(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "all-operations"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, first, second, cluster = _context(service)
    prompts: dict[str, list[str]] = {
        "conjecturer": [],
        "synthesizer": [],
        "summarizer": [],
    }

    def capture(role: str, response: str):
        def respond(prompt: str) -> str:
            prompts[role].append(prompt)
            return response

        return respond

    adapter, _endpoints = _adapter(
        service,
        manifest,
        {
            "conjecturer": capture(
                "conjecturer",
                '{"content":"wild but explicitly provisional"}',
            ),
            "synthesizer": capture(
                "synthesizer",
                json.dumps(
                    {
                        "from_handle": "B1",
                        "to_handle": "B2",
                        "relation_hint": "may conflict",
                    }
                ),
            ),
            "summarizer": capture(
                "summarizer",
                '{"working_focus":"Keep both mechanisms alive"}',
            ),
        },
    )
    author = ScratchAuthoringService(service, adapter, renderer=renderer, run_manifest=manifest)

    qualification_calls = {"load": 0, "validate": 0}
    original_load = doctor_module.load_production_contract_report
    original_validate = doctor_module.validate_production_contract_qualification

    def counted_load(*args, **kwargs):
        qualification_calls["load"] += 1
        return original_load(*args, **kwargs)

    def counted_validate(*args, **kwargs):
        qualification_calls["validate"] += 1
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(doctor_module, "load_production_contract_report", counted_load)
    monkeypatch.setattr(
        doctor_module,
        "validate_production_contract_qualification",
        counted_validate,
    )

    block = author.author_block(rendered, task="Stretch beyond the obvious answer")
    link = author.author_link(rendered, task="Connect the competing possibilities")
    guide = author.author_cluster_guide(
        cluster.id, rendered, task="Keep the unresolved region navigable"
    )

    assert block.body.content == "wild but explicitly provisional"
    assert block.body.why_keep_this is None
    assert block.body.unfinished is None
    assert block.body.possible_next_move is None
    assert (link.body.from_, link.body.to) == (first.id, second.id)
    assert link.body.because is None
    assert guide.working_focus == "Keep both mechanisms alive"
    assert guide.open_threads is None
    assert guide.entry_points is None
    assert guide.local_summary is None
    work = list(service.harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.SCRATCH_AUTHORING,
        WorkflowTaskKind.SCRATCH_AUTHORING,
        WorkflowTaskKind.SCRATCH_AUTHORING,
    ]
    assert [item.terminal.status for item in work] == [
        "completed",
        "completed",
        "completed",
    ]
    assert [item.preparation.task_payload_value["operation"] for item in work] == [
        "block",
        "link",
        "guide",
    ]
    assert [item.preparation.task_payload_value["ordinal"] for item in work] == [0, 1, 2]
    assert [item.preparation.task_payload_value["role"] for item in work] == [
        "conjecturer",
        "synthesizer",
        "summarizer",
    ]
    assert [item.preparation.contract_id for item in work] == [
        "scratch.block.compact.v1",
        "scratch.link.compact.v1",
        "scratch.cluster-guide.compact.v1",
    ]
    assert all(
        item.preparation.task_payload_value["purpose"] == "imaginative_workshop"
        and item.preparation.task_payload_value["epistemic_boundary"] == "advisory_non_grounding"
        for item in work
    )
    assert all(
        item.exposure is not None
        and len(item.exposure.exposed_items) == 1
        and item.exposure.exposed_items[0].namespace == ContextNamespace.SCRATCH
        and item.exposure.exposed_items[0].alias == "SCR_001"
        for item in work
    )

    events = list(service.harness.log.read())
    provider_events = [event for event in events if event.control and event.llm]
    exposure_ids = {item.exposure.id for item in work}
    authored_effects = [
        event
        for event in events
        if event.scratch is not None
        and event.scratch.actor == ScratchActor.LLM
        and event.scratch.context_ref in exposure_ids
    ]
    assert len(provider_events) == 3
    assert all(len(values) == 1 for values in prompts.values())
    for role, values in prompts.items():
        prompt = values[0]
        assert V6_SCRATCH_WORKSHOP_PROMPT in prompt
        assert "IMAGINATIVE SCRATCH WORKSHOP" in prompt
        assert "Explore boldly." in prompt
        assert "Scratch remains advisory" in prompt
        assert "never makes it a fact, evidence, a formal claim, or support" in prompt
        assert "Do not turn uncertainty into a confident fact" in prompt
        item = next(
            candidate
            for candidate in work
            if candidate.preparation.route_lease.role == role
        )
        provider = item.provider_attempts[item.preparation.attempt_index]
        event = next(
            candidate
            for candidate in provider_events
            if candidate.llm.work_order_id == item.preparation.id
        )
        prompt_bytes = service.harness.blobs.get(event.llm.prompt_ref)
        assert prompt_bytes.decode("utf-8") == prompt
        assert prompt.count(rendered.text) == 1
        exposed = item.exposure.exposed_items[0]
        exposed_bytes = service.harness.blobs.get(exposed.object_ref)
        assert exposed_bytes.decode("utf-8") == rendered.text
        assert hashlib.sha256(exposed_bytes).hexdigest() == exposed.content_sha256
        assert hashlib.sha256(prompt_bytes).hexdigest() == item.exposure.prompt_sha256
        assert provider.prompt_sha256 == item.exposure.prompt_sha256
    assert len(authored_effects) == 3
    assert all(event.llm is None for event in authored_effects)
    assert guide.authored_by.event_seq in {event.seq for event in provider_events}
    assert not any(event.inputs and event.inputs[0] == "dropped-call" for event in events)
    assert qualification_calls == {"load": 3, "validate": 3}
    report = verify_root_report(root, allow_missing_terminal=True)
    assert report.security_valid, report.security
    assert not any(item.check == "transaction-authority" for item in report.security)


def test_scratch_authoring_uses_compact_transport_after_exact_route_transition(
    tmp_path,
):
    root = tmp_path / "compact-route-authoring"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"later advisory possibility"}']},
    )
    classification_report = run_production_contract_doctor(
        manifest,
        case_executor=_admitted_qualification_case,
    )
    service.harness.bind_model_classification(manifest, classification_report)
    _exhaust(
        InquiryTransactionService(service.harness, manifest, adapter.meter),
        role="conjecturer",
        trigger="scratch-route-transition",
    )

    block = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    ).author_block(rendered, task="Keep exploring provisionally")

    assert block.body.content == "later advisory possibility"
    authored = next(
        item
        for item in service.harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.SCRATCH_AUTHORING
    )
    call = next(
        event.llm
        for event in service.harness.log.read()
        if event.llm is not None
        and event.llm.work_order_id == authored.preparation.id
    )
    assert {attempt.model_profile for attempt in call.attempt_trace} == {
        "standard"
    }
    assert {attempt.transport_profile for attempt in call.attempt_trace} == {
        "compact"
    }
    assert authored.exposure is not None
    assert len(authored.exposure.exposed_items) == 1
    prompt = service.harness.blobs.get(call.prompt_ref).decode("utf-8")
    assert prompt.count(rendered.text) == 1
    assert endpoints["conjecturer"].last_transport_attempts == 1


def test_base_compact_scratch_route_keeps_exact_advisory_exposure(tmp_path):
    root = tmp_path / "base-compact-authoring"
    manifest = _bind_v6_root(
        root,
        route_profiles={"conjecturer": "compact"},
    )
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"compact advisory possibility"}']},
    )

    block = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    ).author_block(rendered, task="Explore provisionally in compact form")

    assert block.body.content == "compact advisory possibility"
    call = next(
        event.llm
        for event in service.harness.log.read()
        if event.llm is not None
    )
    assert {attempt.model_profile for attempt in call.attempt_trace} == {
        "compact"
    }
    assert {attempt.transport_profile for attempt in call.attempt_trace} == {
        "compact"
    }
    assert service.harness.workflow_state.compact_recovery_by_route_seat == {}
    prompt = service.harness.blobs.get(call.prompt_ref).decode("utf-8")
    assert prompt.count(rendered.text) == 1
    assert endpoints["conjecturer"].last_transport_attempts == 1


def test_maximum_length_block_task_fails_before_false_exposure(tmp_path):
    _assert_maximum_task_fails_before_false_exposure(tmp_path, "block")


def test_maximum_length_link_task_fails_before_false_exposure(tmp_path):
    _assert_maximum_task_fails_before_false_exposure(tmp_path, "link")


def test_maximum_length_guide_task_fails_before_false_exposure(tmp_path):
    _assert_maximum_task_fails_before_false_exposure(tmp_path, "guide")


def test_budget_denial_has_no_exposure_or_provider_dispatch(tmp_path):
    root = tmp_path / "budget-denied"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    calls: list[str] = []

    def respond(prompt: str) -> str:
        calls.append(prompt)
        return '{"content":"must never dispatch"}'

    adapter, _endpoints = _adapter(service, manifest, {"conjecturer": respond}, budget=1)
    author = ScratchAuthoringService(service, adapter, renderer=renderer)
    before = set(service.state.blocks)
    with pytest.raises(WorkBudgetDenied):
        author.author_block(rendered, task="Imagine without violating the meter")

    item = next(iter(service.harness.workflow_state.transaction_work.values()))
    assert item.terminal.status == "budget_denied"
    assert item.exposure is None and item.authorization is None
    assert not item.provider_attempts and calls == []
    assert set(service.state.blocks) == before
    assert adapter.meter.reserved == 0


def test_request_envelope_overflow_has_no_scratch_or_transaction_mutation(tmp_path):
    root = tmp_path / "request-envelope-overflow"
    with pytest.raises(RequestEnvelopeExceeded):
        _bind_v6_root(
            root,
            route_capacities={"conjecturer": 65},
        )

    service = ScratchService(root)
    assert service.harness.workflow_state.transaction_work == {}
    assert tuple(service.harness.log.read()) == ()
    assert service.state.attention_receipts == {}
    assert service.state.advisory_contexts == {}
    assert service.state.visibility == {}
    assert service.state.coverage_cycles == {}
    assert service.state.blocks == {}
    assert service.state.links == {}
    assert service.state.guides_by_cluster == {}


def test_schema_repair_is_fresh_work_and_never_legacy_double_logged(tmp_path):
    root = tmp_path / "repair"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {
            "conjecturer": [
                '{"content":"keep this bold thought","invented":"forbidden"}',
                json.dumps(
                    {
                        "schema": "repair.patch.v1",
                        "op": "remove",
                        "path": "/invented",
                    }
                ),
            ]
        },
    )
    block = ScratchAuthoringService(service, adapter, renderer=renderer).author_block(
        rendered, task="Preserve a speculative mechanism"
    )

    assert block.body.content == "keep this bold thought"
    work = list(service.harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.SCRATCH_AUTHORING,
        WorkflowTaskKind.REPAIR,
    ]
    assert [item.terminal.status for item in work] == ["rejected", "completed"]
    events = list(service.harness.log.read())
    assert len([event for event in events if event.control and event.llm]) == 2
    assert not any(
        event.inputs and event.inputs[0] in {"dropped-call", "scratch-call-failed"}
        for event in events
    )
    effect = next(
        event for event in events if event.scratch is not None and block.id in event.outputs
    )
    assert effect.llm is None
    assert effect.scratch.context_ref == work[-1].exposure.id


def test_transport_failure_is_typed_once_without_scratch_effect(tmp_path):
    root = tmp_path / "transport"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    calls: list[str] = []

    def fail(prompt: str) -> str:
        calls.append(prompt)
        raise EndpointError("offline transport failure")

    adapter, _endpoints = _adapter(service, manifest, {"conjecturer": fail})
    before = set(service.state.blocks)
    with pytest.raises(EndpointError) as caught:
        ScratchAuthoringService(service, adapter, renderer=renderer).author_block(
            rendered, task="Keep failure root-local"
        )

    assert caught.value.transaction_terminalized is True
    item = next(iter(service.harness.workflow_state.transaction_work.values()))
    assert item.terminal.status == "transport_failed"
    assert item.exposure is not None and len(item.provider_attempts) == 1
    assert calls and set(service.state.blocks) == before
    events = list(service.harness.log.read())
    assert len([event for event in events if event.control and event.llm]) == 1
    assert not any(event.inputs and event.inputs[0] == "dropped-call" for event in events)
    assert adapter.meter.reserved == 0


def test_schema_exhaustion_terminalizes_every_attempt_without_legacy_drop(tmp_path):
    root = tmp_path / "schema-exhausted"
    manifest = _bind_v6_root(root, scratch_fallback=False)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    invalid = '{"content":"still speculative","invented":"forbidden"}'
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": [invalid, invalid, invalid]},
    )
    before = set(service.state.blocks)

    with pytest.raises(SchemaExhaustedError) as caught:
        ScratchAuthoringService(service, adapter, renderer=renderer).author_block(
            rendered, task="Fail closed without crashing the run"
        )

    assert caught.value.transaction_terminalized is True
    work = list(service.harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.SCRATCH_AUTHORING,
        WorkflowTaskKind.REPAIR,
        WorkflowTaskKind.REPAIR,
    ]
    assert all(item.terminal is not None for item in work)
    assert work[-1].terminal.status == "schema_exhausted"
    assert set(service.state.blocks) == before
    events = list(service.harness.log.read())
    assert len([event for event in events if event.control and event.llm]) == 3
    assert not any(
        event.inputs and event.inputs[0] in {"dropped-call", "scratch-call-failed"}
        for event in events
    )


def _assert_zero_grant_prevents_scratch_repair(tmp_path, operation: str) -> None:
    contract_id = {
        "block": "scratch.block.compact.v1",
        "link": "scratch.link.compact.v1",
        "guide": "scratch.cluster-guide.compact.v1",
    }[operation]
    root = tmp_path / f"zero-grant-{operation}"
    manifest = _bind_v6_root(
        root,
        grant_ceiling=(contract_id, 0),
        scratch_fallback=False,
    )
    service = ScratchService(root)
    renderer, rendered, _first, _second, cluster = _context(service)
    role = {
        "block": "conjecturer",
        "link": "synthesizer",
        "guide": "summarizer",
    }[operation]
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {role: ["{invalid-json", '{"content":"must not dispatch"}']},
    )
    adapter.retry_max = 99
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )

    with pytest.raises(SchemaExhaustedError):
        if operation == "block":
            author.author_block(rendered, task="Respect the frozen zero grant")
        elif operation == "link":
            author.author_link(rendered, task="Respect the frozen zero grant")
        else:
            author.author_cluster_guide(
                cluster.id,
                rendered,
                task="Respect the frozen zero grant",
            )

    work = tuple(service.harness.workflow_state.transaction_work.values())
    assert len(work) == 1
    assert work[0].preparation.contract_id == contract_id
    assert work[0].terminal.status == "schema_exhausted"
    assert adapter.meter.calls == 1
    assert adapter.meter.reserved == 0


def test_zero_block_grant_prevents_config_or_adapter_retry_inflation(tmp_path):
    _assert_zero_grant_prevents_scratch_repair(tmp_path, "block")


def test_zero_link_grant_prevents_config_or_adapter_retry_inflation(tmp_path):
    _assert_zero_grant_prevents_scratch_repair(tmp_path, "link")


def test_zero_guide_grant_prevents_config_or_adapter_retry_inflation(tmp_path):
    _assert_zero_grant_prevents_scratch_repair(tmp_path, "guide")


def test_unbound_legacy_root_retains_single_scratch_event_accounting(tmp_path):
    service = ScratchService(tmp_path / "legacy")
    renderer, rendered, *_rest = _context(service)
    endpoint = MockEndpoint(['{"content":"legacy note"}'])
    adapter = LLMAdapter({"conjecturer": endpoint}, service.harness.blobs)
    block = ScratchAuthoringService(service, adapter, renderer=renderer).author_block(
        rendered, task="Preserve legacy behavior"
    )

    event = next(
        event
        for event in service.harness.log.read()
        if event.scratch is not None and block.id in event.outputs
    )
    assert event.llm is not None and event.llm.attempts == 1
    assert not any(event.control is not None for event in service.harness.log.read())


def test_harness_bound_v6_plain_adapter_without_explicit_manifest_is_transactional(
    tmp_path,
):
    root = tmp_path / "harness-bound-plain-adapter"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"contained by Harness authority"}']},
    )
    adapter.transaction_authority_required = False

    block = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
    ).author_block(rendered, task="Use the canonical Harness authority")

    assert block.body.content == "contained by Harness authority"
    assert adapter.transaction_authority_required is True
    assert adapter._v6_authority_manifest.sha256 == manifest.sha256
    assert endpoints["conjecturer"].last_transport_attempts == 1
    work = tuple(service.harness.workflow_state.transaction_work.values())
    assert len(work) == 1 and work[0].terminal.status == "completed"


def test_explicit_v6_manifest_must_exactly_match_bound_root(tmp_path):
    root = tmp_path / "manifest-mismatch"
    manifest = _bind_v6_root(root)
    mismatched = _manifest(manifest.run_input_digest, stamp="2026-07-17T00:00:01Z")
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"must not dispatch"}']},
    )
    before = _authority_snapshot(service, adapter)
    root_before = _root_bytes(root)
    with pytest.raises(RunManifestError) as caught:
        ScratchAuthoringService(
            service,
            adapter,
            renderer=renderer,
            run_manifest=mismatched,
        ).author_block(rendered, task="Reject foreign manifest authority")
    assert caught.value.code == "RUN_MANIFEST_CONFLICT"
    assert _authority_snapshot(service, adapter) == before
    assert _root_bytes(root) == root_before


@pytest.mark.parametrize("operation", ("block", "link", "guide"))
def test_missing_durable_manifest_fails_before_qualification_or_binding(
    tmp_path,
    monkeypatch,
    operation,
):
    root = tmp_path / f"missing-bound-manifest-{operation}"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, _first, _second, cluster = _context(service)
    role = {
        "block": "conjecturer",
        "link": "synthesizer",
        "guide": "summarizer",
    }[operation]
    adapter, endpoints = _adapter(
        service,
        manifest,
        {role: ['{"content":"must not dispatch"}']},
    )
    adapter.transaction_authority_required = False
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    (root / "run-manifest.json").unlink()
    qualification_calls = []
    binding_calls = []
    monkeypatch.setattr(
        authoring_module,
        "require_v6_production_qualification",
        lambda *_args, **_kwargs: qualification_calls.append("qualification"),
    )
    original_bind = adapter.bind_v6_authority

    def counted_bind(*args, **kwargs):
        binding_calls.append("bind")
        return original_bind(*args, **kwargs)

    monkeypatch.setattr(adapter, "bind_v6_authority", counted_bind)
    before = _authority_snapshot(service, adapter)
    root_before = _root_bytes(root)

    with pytest.raises(ScratchAuthoringError) as caught:
        _invoke(author, operation, rendered, cluster.id)

    assert caught.value.code == "SCRATCH_MANIFEST_MISMATCH"
    assert qualification_calls == [] and binding_calls == []
    assert _authority_snapshot(service, adapter) == before
    assert _root_bytes(root) == root_before
    assert not (root / "run-manifest.json").exists()
    assert endpoints[role].last_transport_attempts == 0


@pytest.mark.parametrize("operation", ("block", "link", "guide"))
def test_harness_bound_v6_cannot_fall_back_when_manifest_disappears(
    tmp_path,
    monkeypatch,
    operation,
):
    root = tmp_path / f"harness-bound-missing-{operation}"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, _first, _second, cluster = _context(service)
    role = {
        "block": "conjecturer",
        "link": "synthesizer",
        "guide": "summarizer",
    }[operation]
    adapter, endpoints = _adapter(
        service,
        manifest,
        {role: ['{"content":"must not use legacy dispatch"}']},
    )
    adapter.transaction_authority_required = False
    author = ScratchAuthoringService(service, adapter, renderer=renderer)
    (root / "run-manifest.json").unlink()
    qualification_calls = []
    binding_calls = []
    monkeypatch.setattr(
        authoring_module,
        "require_v6_production_qualification",
        lambda *_args, **_kwargs: qualification_calls.append("qualification"),
    )
    original_bind = adapter.bind_v6_authority

    def counted_bind(*args, **kwargs):
        binding_calls.append("bind")
        return original_bind(*args, **kwargs)

    monkeypatch.setattr(adapter, "bind_v6_authority", counted_bind)
    before = _authority_snapshot(service, adapter)

    with pytest.raises(ScratchAuthoringError) as caught:
        _invoke(author, operation, rendered, cluster.id)

    assert caught.value.code == "SCRATCH_MANIFEST_MISMATCH"
    assert qualification_calls == [] and binding_calls == []
    assert _authority_snapshot(service, adapter) == before
    assert endpoints[role].last_transport_attempts == 0


def test_release_denial_precedes_scratch_qualification_and_binding(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "release-denied"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"must not dispatch"}']},
    )
    adapter.transaction_authority_required = False
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    qualification_calls = []
    monkeypatch.setenv("DEEPREASON_DISABLE_V6_LAUNCHES", "1")
    monkeypatch.setattr(
        authoring_module,
        "require_v6_production_qualification",
        lambda *_args, **_kwargs: qualification_calls.append("qualification"),
    )
    before = _authority_snapshot(service, adapter)
    root_before = _root_bytes(root)

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        author.author_block(rendered, task="Respect central release denial")

    assert qualification_calls == []
    assert _authority_snapshot(service, adapter) == before
    assert _root_bytes(root) == root_before
    assert endpoints["conjecturer"].last_transport_attempts == 0


def test_manifest_deletion_after_preview_fails_before_transaction_issuance(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "manifest-deleted-after-preview"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"must not dispatch"}']},
    )
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    original_preview = adapter.preview_request_with_v6_classification

    def deleting_preview(*args, **kwargs):
        preview = original_preview(*args, **kwargs)
        (root / "run-manifest.json").unlink()
        return preview

    monkeypatch.setattr(
        adapter,
        "preview_request_with_v6_classification",
        deleting_preview,
    )
    before = _authority_snapshot(service, adapter)
    root_before = _root_bytes(root, exclude=("run-manifest.json",))

    with pytest.raises(ScratchAuthoringError) as caught:
        author.author_block(rendered, task="Detect manifest deletion before issue")

    assert caught.value.code == "SCRATCH_MANIFEST_MISMATCH"
    after = _authority_snapshot(service, adapter)
    assert after["event_count"] == before["event_count"]
    assert after["work_ids"] == before["work_ids"]
    assert after["meter_calls"] == before["meter_calls"]
    assert after["meter_reserved"] == before["meter_reserved"]
    assert after["attention"] == before["attention"]
    assert after["advisory"] == before["advisory"]
    assert after["visibility"] == before["visibility"]
    assert after["coverage"] == before["coverage"]
    assert after["blocks"] == before["blocks"]
    assert after["links"] == before["links"]
    assert after["guides"] == before["guides"]
    assert _root_bytes(root) == root_before
    assert endpoints["conjecturer"].last_transport_attempts == 0


def test_manifest_replacement_after_preview_preserves_conflict_error(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "manifest-replaced-after-preview"
    manifest = _bind_v6_root(root)
    foreign = _manifest(manifest.run_input_digest, stamp="2026-07-17T00:00:01Z")
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"must not dispatch"}']},
    )
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    original_preview = adapter.preview_request_with_v6_classification

    def replacing_preview(*args, **kwargs):
        preview = original_preview(*args, **kwargs)
        (root / "run-manifest.json").write_bytes(foreign.canonical_bytes() + b"\n")
        return preview

    monkeypatch.setattr(
        adapter,
        "preview_request_with_v6_classification",
        replacing_preview,
    )
    before = _authority_snapshot(service, adapter)

    with pytest.raises(RunManifestError) as caught:
        author.author_block(rendered, task="Detect manifest replacement before issue")

    assert caught.value.code == "MANIFEST_HASH_MISMATCH"
    after = _authority_snapshot(service, adapter)
    assert after["event_count"] == before["event_count"]
    assert after["work_ids"] == before["work_ids"]
    assert after["meter_calls"] == before["meter_calls"]
    assert after["meter_reserved"] == before["meter_reserved"]
    assert after["blocks"] == before["blocks"]
    assert endpoints["conjecturer"].last_transport_attempts == 0


def test_inaccessible_manifest_inspection_propagates_before_binding(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "manifest-inaccessible"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"must not dispatch"}']},
    )
    adapter.transaction_authority_required = False
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    manifest_path = root / "run-manifest.json"
    original_lstat = Path.lstat

    def inaccessible_lstat(path):
        if path == manifest_path:
            raise PermissionError("offline fixture denial")
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", inaccessible_lstat)
    before = _authority_snapshot(service, adapter)
    root_before = _root_bytes(root)

    with pytest.raises(PermissionError, match="offline fixture denial"):
        author.author_block(rendered, task="Propagate manifest inspection failure")

    assert _authority_snapshot(service, adapter) == before
    assert _root_bytes(root) == root_before
    assert endpoints["conjecturer"].last_transport_attempts == 0


@pytest.mark.parametrize(
    "variant",
    ("symlink", "nonregular", "malformed", "oversized", "digest_invalid"),
)
def test_invalid_bound_manifest_fails_before_qualification_or_binding(
    tmp_path,
    monkeypatch,
    variant,
):
    root = tmp_path / f"manifest-{variant}"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"must not dispatch"}']},
    )
    adapter.transaction_authority_required = False
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    manifest_path = root / "run-manifest.json"
    original = manifest_path.read_bytes()
    manifest_path.unlink()
    if variant == "symlink":
        target = root / "manifest-target.json"
        target.write_bytes(original)
        manifest_path.symlink_to(target)
    elif variant == "nonregular":
        manifest_path.mkdir()
    elif variant == "malformed":
        manifest_path.write_bytes(b"{")
    elif variant == "oversized":
        manifest_path.write_bytes(b" " * (4 * 1024 * 1024 + 1))
    else:
        foreign = _manifest(
            manifest.run_input_digest,
            stamp="2026-07-17T00:00:01Z",
        )
        manifest_path.write_bytes(foreign.canonical_bytes() + b"\n")
    qualification_calls = []
    monkeypatch.setattr(
        authoring_module,
        "require_v6_production_qualification",
        lambda *_args, **_kwargs: qualification_calls.append("qualification"),
    )
    before = _authority_snapshot(service, adapter)
    root_before = _root_bytes(root)

    with pytest.raises(RunManifestError):
        author.author_block(rendered, task="Reject invalid durable manifest")

    assert qualification_calls == []
    assert _authority_snapshot(service, adapter) == before
    assert _root_bytes(root) == root_before
    assert endpoints["conjecturer"].last_transport_attempts == 0


@pytest.mark.parametrize(
    "variant",
    (
        "missing",
        "malformed",
        "noncanonical",
        "symlink",
        "oversized",
        "foreign",
        "incomplete",
        "reordered",
        "unqualified",
        "repair_overclaim",
    ),
)
def test_invalid_qualification_reports_fail_before_scratch_binding(
    tmp_path,
    variant,
):
    root = tmp_path / f"qualification-{variant}"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"must not dispatch"}']},
    )
    adapter.transaction_authority_required = False
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    policy = manifest.production_qualification_policy
    assert policy is not None
    report_path = root / policy.report_filename
    canonical_report = doctor_module.load_production_contract_report(report_path)
    payload = canonical_report.model_dump(mode="json", by_alias=True)
    if variant == "missing":
        report_path.unlink()
    elif variant == "malformed":
        report_path.write_bytes(b"{")
    elif variant == "noncanonical":
        report_path.write_bytes(b" " + canonical_json(payload) + b"\n")
    elif variant == "symlink":
        target = root / "qualification-target.json"
        target.write_bytes(canonical_json(payload) + b"\n")
        report_path.unlink()
        report_path.symlink_to(target)
    elif variant == "oversized":
        report_path.write_bytes(b" " * (4 * 1024 * 1024 + 1))
    elif variant == "foreign":
        foreign = _manifest(
            manifest.run_input_digest,
            stamp="2026-07-17T00:00:01Z",
        )
        write_production_contract_report(
            run_production_contract_doctor(
                foreign,
                case_executor=_admitted_qualification_case,
            ),
            report_path,
        )
    else:
        if variant == "incomplete":
            payload["pairs"] = payload["pairs"][:-1]
        elif variant == "reordered":
            payload["pairs"] = list(reversed(payload["pairs"]))
        elif variant == "unqualified":
            payload["pairs"][0]["qualified"] = False
            payload["summary"]["qualified_pair_count"] -= 1
            payload["summary"]["qualified"] = False
        else:
            payload["pairs"][0]["cases"][0]["repair_count"] = 3
            payload["pairs"][0]["repair_count"] += 3
            payload["summary"]["repair_count"] += 3
        report_path.write_bytes(canonical_json(payload) + b"\n")
    before = _authority_snapshot(service, adapter)
    root_before = _root_bytes(root)

    with pytest.raises(RunManifestError) as caught:
        author.author_block(rendered, task="Reject invalid qualification")

    assert caught.value.code.startswith("DOCTOR_REPORT_")
    assert _authority_snapshot(service, adapter) == before
    assert _root_bytes(root) == root_before
    assert endpoints["conjecturer"].last_transport_attempts == 0


def test_historical_v6_without_qualification_policy_has_no_scratch_authority(
    tmp_path,
):
    root = tmp_path / "historical-policy-absent"
    manifest = _bind_v6_root(root)
    payload = json.loads(manifest.canonical_bytes())
    payload.pop("production_qualification_policy")
    historical = RunManifest.model_validate(payload)
    (root / "run-manifest.json").write_bytes(historical.canonical_bytes() + b"\n")
    (root / "run-manifest.sha256").write_text(historical.sha256 + "\n")
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        historical,
        {"conjecturer": ['{"content":"must not dispatch"}']},
    )
    adapter.transaction_authority_required = False
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=historical,
    )
    before = _authority_snapshot(service, adapter)
    root_before = _root_bytes(root)

    with pytest.raises(RunManifestError) as caught:
        author.author_block(rendered, task="Reject absent qualification authority")

    assert caught.value.code == "V6_PRODUCTION_QUALIFICATION_POLICY_REQUIRED"
    assert _authority_snapshot(service, adapter) == before
    assert _root_bytes(root) == root_before
    assert endpoints["conjecturer"].last_transport_attempts == 0


def test_restart_recovers_durable_scratch_result_without_redispatch(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "durable-result-recovery"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"durable provisional result"}']},
    )
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    original_call = author._call

    def crash_after_durable_provider(*args, **kwargs):
        original_call(*args, **kwargs)
        raise SystemExit("simulated process loss")

    monkeypatch.setattr(author, "_call", crash_after_durable_provider)
    with pytest.raises(SystemExit, match="simulated process loss"):
        author.author_block(rendered, task="Recover this exact durable result")
    assert endpoints["conjecturer"].last_transport_attempts == 1
    pending = tuple(service.harness.workflow_state.transaction_work.values())
    assert len(pending) == 1
    assert len(pending[0].provider_attempts) == 1
    assert pending[0].terminal is None

    restarted = ScratchService(root)
    calls = []

    def forbidden(prompt):
        calls.append(prompt)
        raise AssertionError("durable scratch result was redispatched")

    recovery_adapter, recovery_endpoints = _adapter(
        restarted,
        manifest,
        {"conjecturer": forbidden},
    )
    qualification_calls = {"load": 0, "validate": 0}
    original_load = doctor_module.load_production_contract_report
    original_validate = doctor_module.validate_production_contract_qualification

    def counted_load(*args, **kwargs):
        qualification_calls["load"] += 1
        return original_load(*args, **kwargs)

    def counted_validate(*args, **kwargs):
        qualification_calls["validate"] += 1
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(doctor_module, "load_production_contract_report", counted_load)
    monkeypatch.setattr(
        doctor_module,
        "validate_production_contract_qualification",
        counted_validate,
    )
    recovered = ScratchAuthoringService(
        restarted,
        recovery_adapter,
        renderer=ScratchRenderer(restarted),
        run_manifest=manifest,
    ).author_block(rendered, task="Recover this exact durable result")

    assert recovered.body.content == "durable provisional result"
    assert calls == []
    assert recovery_endpoints["conjecturer"].last_transport_attempts == 0
    assert qualification_calls == {"load": 1, "validate": 1}
    work = tuple(restarted.harness.workflow_state.transaction_work.values())
    assert len(work) == 1 and work[0].terminal.status == "completed"
    assert len(
        [
            event
            for event in restarted.harness.log.read()
            if event.scratch is not None and recovered.id in event.outputs
        ]
    ) == 1


def test_restart_recovers_durable_scratch_repair_without_redispatch(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "durable-repair-recovery"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {
            "conjecturer": [
                '{"content":"durable repaired result","invented":"remove"}',
                json.dumps(
                    {
                        "schema": "repair.patch.v1",
                        "op": "remove",
                        "path": "/invented",
                    }
                ),
            ]
        },
    )
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    original_call = author._call

    def crash_after_durable_repair(*args, **kwargs):
        original_call(*args, **kwargs)
        raise SystemExit("simulated repair process loss")

    monkeypatch.setattr(author, "_call", crash_after_durable_repair)
    with pytest.raises(SystemExit, match="simulated repair process loss"):
        author.author_block(rendered, task="Recover this exact repaired result")
    assert adapter.meter.calls == 2
    assert endpoints["conjecturer"].last_transport_attempts == 1

    restarted = ScratchService(root)
    calls = []

    def forbidden(prompt):
        calls.append(prompt)
        raise AssertionError("durable scratch repair was redispatched")

    recovery_adapter, recovery_endpoints = _adapter(
        restarted,
        manifest,
        {"conjecturer": forbidden},
    )
    recovered = ScratchAuthoringService(
        restarted,
        recovery_adapter,
        renderer=ScratchRenderer(restarted),
        run_manifest=manifest,
    ).author_block(rendered, task="Recover this exact repaired result")

    assert recovered.body.content == "durable repaired result"
    assert calls == []
    assert recovery_endpoints["conjecturer"].last_transport_attempts == 0
    work = tuple(restarted.harness.workflow_state.transaction_work.values())
    assert len(work) == 2
    assert [item.terminal.status for item in work] == ["rejected", "completed"]
    assert len(
        [
            event
            for event in restarted.harness.log.read()
            if event.scratch is not None and recovered.id in event.outputs
        ]
    ) == 1


def test_second_operation_durable_result_recovers_historical_ordinal_without_redispatch(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "second-operation-result-recovery"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {
            "conjecturer": [
                '{"content":"completed ordinal zero"}',
                '{"content":"durable ordinal one"}',
            ]
        },
    )
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    author.author_block(rendered, task="Complete the first operation")
    original_call = author._call

    def crash_after_second_result(*args, **kwargs):
        original_call(*args, **kwargs)
        raise SystemExit("simulated second-operation process loss")

    monkeypatch.setattr(author, "_call", crash_after_second_result)
    with pytest.raises(SystemExit, match="second-operation process loss"):
        author.author_block(rendered, task="Recover the second operation")

    initial_work = tuple(service.harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_payload_value["ordinal"] for item in initial_work] == [0, 1]
    assert initial_work[0].terminal.status == "completed"
    assert initial_work[1].terminal is None and len(initial_work[1].provider_attempts) == 1

    restarted = ScratchService(root)
    calls = []

    def forbidden(prompt):
        calls.append(prompt)
        raise AssertionError("ordinal-one durable result was redispatched")

    recovery_adapter, recovery_endpoints = _adapter(
        restarted,
        manifest,
        {"conjecturer": forbidden},
    )
    recovered = ScratchAuthoringService(
        restarted,
        recovery_adapter,
        renderer=ScratchRenderer(restarted),
        run_manifest=manifest,
    ).author_block(rendered, task="Recover the second operation")

    assert recovered.body.content == "durable ordinal one"
    assert calls == []
    assert recovery_endpoints["conjecturer"].last_transport_attempts == 0
    recovered_work = tuple(restarted.harness.workflow_state.transaction_work.values())
    assert len(recovered_work) == 2
    assert [item.terminal.status for item in recovered_work] == ["completed", "completed"]
    assert [item.preparation.task_payload_value["ordinal"] for item in recovered_work] == [0, 1]


def test_second_operation_durable_repair_recovers_without_parent_or_child_redispatch(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "second-operation-repair-recovery"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {
            "conjecturer": [
                '{"content":"completed ordinal zero"}',
                '{"content":"durable ordinal one repair","invented":"remove"}',
                json.dumps(
                    {
                        "schema": "repair.patch.v1",
                        "op": "remove",
                        "path": "/invented",
                    }
                ),
            ]
        },
    )
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    author.author_block(rendered, task="Complete the first operation")
    original_call = author._call

    def crash_after_second_repair(*args, **kwargs):
        original_call(*args, **kwargs)
        raise SystemExit("simulated second repair process loss")

    monkeypatch.setattr(author, "_call", crash_after_second_repair)
    with pytest.raises(SystemExit, match="second repair process loss"):
        author.author_block(rendered, task="Recover the second repaired operation")

    restarted = ScratchService(root)
    calls = []

    def forbidden(prompt):
        calls.append(prompt)
        raise AssertionError("durable ordinal-one repair was redispatched")

    recovery_adapter, recovery_endpoints = _adapter(
        restarted,
        manifest,
        {"conjecturer": forbidden},
    )
    recovered = ScratchAuthoringService(
        restarted,
        recovery_adapter,
        renderer=ScratchRenderer(restarted),
        run_manifest=manifest,
    ).author_block(rendered, task="Recover the second repaired operation")

    assert recovered.body.content == "durable ordinal one repair"
    assert calls == []
    assert recovery_endpoints["conjecturer"].last_transport_attempts == 0
    work = tuple(restarted.harness.workflow_state.transaction_work.values())
    assert len(work) == 3
    assert [item.terminal.status for item in work] == ["completed", "rejected", "completed"]
    assert [
        item.preparation.task_payload_value.get("ordinal")
        for item in work
        if item.preparation.task_kind == WorkflowTaskKind.SCRATCH_AUTHORING
    ] == [0, 1]


def test_repeated_completed_operation_allocates_next_durable_ordinal(tmp_path):
    root = tmp_path / "completed-operation-new-ordinal"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"first completion"}']},
    )
    task = "Repeat this as a genuinely new operation"
    first = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    ).author_block(rendered, task=task)

    restarted = ScratchService(root)
    recovery_adapter, recovery_endpoints = _adapter(
        restarted,
        manifest,
        {"conjecturer": ['{"content":"second completion"}']},
    )
    second = ScratchAuthoringService(
        restarted,
        recovery_adapter,
        renderer=ScratchRenderer(restarted),
        run_manifest=manifest,
    ).author_block(rendered, task=task)

    assert first.id != second.id
    assert recovery_endpoints["conjecturer"].last_transport_attempts == 1
    work = tuple(restarted.harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_payload_value["ordinal"] for item in work] == [0, 1]
    assert all(item.terminal.status == "completed" for item in work)


def test_ambiguous_unfinished_scratch_chains_fail_closed_before_redispatch(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "ambiguous-unfinished-chains"
    manifest = _bind_v6_root(root)
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ['{"content":"first durable result"}']},
    )
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    original_call = author._call

    def crash_after_provider(*args, **kwargs):
        original_call(*args, **kwargs)
        raise SystemExit("leave first chain unfinished")

    monkeypatch.setattr(author, "_call", crash_after_provider)
    task = "Ambiguous durable recovery must fail closed"
    with pytest.raises(SystemExit, match="leave first chain unfinished"):
        author.author_block(rendered, task=task)

    first_item = next(iter(service.harness.workflow_state.transaction_work.values()))
    second_payload = json.loads(canonical_json(first_item.preparation.task_payload_value))
    second_payload["ordinal"] = 1
    second_trigger = "scratch-authoring:" + hashlib.sha256(
        canonical_json(second_payload)
    ).hexdigest()
    transaction = InquiryTransactionService(service.harness, manifest, adapter.meter)
    transaction.prepare(
        task_kind=WorkflowTaskKind.SCRATCH_AUTHORING,
        attempt_index=0,
        route_lease=first_item.preparation.route_lease,
        contract_id=first_item.preparation.contract_id,
        trigger_ref=second_trigger,
        formal_fence_seq=service.harness._next_seq - 1,
        scratch_fence_seq=service.harness._next_seq - 1,
        target_refs=first_item.preparation.target_refs,
        input_refs=first_item.preparation.input_refs,
        task_payload_value=second_payload,
    )
    before_work = tuple(service.harness.workflow_state.transaction_work)

    restarted = ScratchService(root)
    recovery_calls = []

    def forbidden(prompt):
        recovery_calls.append(prompt)
        raise AssertionError("ambiguous recovery reached the provider")

    recovery_adapter, recovery_endpoints = _adapter(
        restarted,
        manifest,
        {"conjecturer": forbidden},
    )
    with pytest.raises(ScratchAuthoringError) as caught:
        ScratchAuthoringService(
            restarted,
            recovery_adapter,
            renderer=ScratchRenderer(restarted),
            run_manifest=manifest,
        ).author_block(rendered, task=task)

    assert caught.value.code == "SCRATCH_RECOVERY_AUTHORITY_AMBIGUOUS"
    assert tuple(restarted.harness.workflow_state.transaction_work) == before_work
    assert recovery_calls == []
    assert recovery_endpoints["conjecturer"].last_transport_attempts == 0
    assert endpoints["conjecturer"].last_transport_attempts == 1
