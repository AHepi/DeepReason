"""Standalone scratch authoring uses complete v6 provider transactions."""

from __future__ import annotations

import hashlib
import json

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import EndpointError, MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.llm.repair import SchemaExhaustedError
from deepreason.ontology import Commitment
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    SchoolExecutionPolicyV1,
    ScratchAuthoringPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
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
from tests.test_scratch_attention import _policy, _request


STAMP = "2026-07-17T00:00:00Z"


def _route(role: str) -> dict:
    return {
        "endpoint_id": f"{role}-scratch-route",
        "endpoint": f"mock://{role}-scratch",
        "model": f"offline-{role}-scratch",
        "provider": "mock",
        "family": f"offline-{role}",
        "max_tokens": 64,
    }


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


def _manifest(run_input_digest: str, *, stamp: str = STAMP):
    return compile_run_manifest(
        Config(
            N_SCHOOLS=0,
            RETRY_MAX=2,
            scratchpad={"enabled": True},
            roles={role: [_route(role)] for role in ("conjecturer", "synthesizer", "summarizer")},
        ),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=stamp,
        control_plane_policy=_control(),
        run_input_digest=run_input_digest,
    )


def _bind_v6_root(root):
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
    manifest = _manifest(run_input.run_input_digest)
    bind_run_manifest(manifest, root)
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


def test_block_link_and_guide_each_use_complete_independent_transactions(tmp_path):
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
        assert hashlib.sha256(prompt_bytes).hexdigest() == item.exposure.prompt_sha256
        assert provider.prompt_sha256 == item.exposure.prompt_sha256
    assert len(authored_effects) == 3
    assert all(event.llm is None for event in authored_effects)
    assert guide.authored_by.event_seq in {event.seq for event in provider_events}
    assert not any(event.inputs and event.inputs[0] == "dropped-call" for event in events)
    report = verify_root_report(root, allow_missing_terminal=True)
    assert report.security_valid, report.security
    assert not any(item.check == "transaction-authority" for item in report.security)


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
    manifest = _bind_v6_root(root)
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


def test_explicit_v6_manifest_must_exactly_match_bound_root(tmp_path):
    root = tmp_path / "manifest-mismatch"
    manifest = _bind_v6_root(root)
    mismatched = _manifest(manifest.run_input_digest, stamp="2026-07-17T00:00:01Z")
    service = ScratchService(root)
    with pytest.raises(ScratchAuthoringError) as caught:
        ScratchAuthoringService(service, object(), run_manifest=mismatched)
    assert caught.value.code == "SCRATCH_RUN_MANIFEST_MISMATCH"
