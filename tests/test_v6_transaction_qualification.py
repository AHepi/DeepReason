"""Focused qualification of the RunManifest-v6 transactional seams."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json
from deepreason.capabilities.policy import (
    InquiryCapabilityPolicyV1,
    SimulationCapabilityPolicyV1,
    SimulationInputBindingV1,
)
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.indexes import DerivedIndexError, load_indexes, rebuild_indexes
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import EndpointError, MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.ontology import (
    Commitment,
    LLMCall,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
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
    ToolchainEntry,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.rules.conj import conj
from deepreason.scratch.attention import (
    AttentionPlanner,
    AttentionPolicyV1,
    AttentionRequestV1,
)
from deepreason.scratch.authoring import ScratchAuthoringService
from deepreason.scratch.models import RetrievalChannel
from deepreason.scratch.proposals import (
    ScratchBlockDraftBodyV1,
    ScratchNewBlockDraftV1,
    ScratchProposalLinkV1,
    ScratchProposalV1,
    V6_SCRATCH_WORKSHOP_PROMPT,
    ScratchRevisionDraftV1,
)
from deepreason.scratch.service import ScratchService
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction import WorkBudgetDenied
from deepreason.workflow.transaction_service import InquiryTransactionService


STAMP = "2026-07-17T00:00:00Z"


def _route(endpoint_id: str, seat: int = 0) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"offline-model-{seat}",
        "provider": "mock",
        "family": f"offline-family-{seat}",
        "max_tokens": 64,
    }


def _config(*, critics: bool = False) -> Config:
    roles = {"conjecturer": [_route("conjecturer-route")]}
    if critics:
        roles["argumentative_critic"] = [
            _route(f"critic-route-{seat}", seat) for seat in range(3)
        ]
    return Config(
        N_SCHOOLS=3 if critics else 0,
        roles=roles,
    )


def _control(
    *, scratch_authoring: ScratchAuthoringPolicyV1 | None = None
) -> ControlPlanePolicyV3:
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
        scratch_authoring=scratch_authoring or ScratchAuthoringPolicyV1(),
    )


def _criticism_policy() -> CriticismPolicyV1:
    return CriticismPolicyV1(
        minimum_foreign_school_coverage=2,
        bindings=tuple(
            SchoolRoleBindingV1(
                school_id=f"school-{seat}",
                role="argumentative_critic",
                seat=seat,
                endpoint_id=f"critic-route-{seat}",
            )
            for seat in range(3)
        ),
        max_batch_size=4,
        target_eligibility="accepted_school_artifacts",
        authority="observe_only",
        allow_shared=False,
    )


def _manifest(
    *,
    critics: bool = False,
    scratch_authoring: ScratchAuthoringPolicyV1 | None = None,
    simulation: SimulationCapabilityPolicyV1 | None = None,
):
    toolchains = ()
    capabilities = None
    if simulation is not None:
        capabilities = InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2", simulation=simulation
        )
        if simulation.enabled:
            version = (
                f"{sys.version_info.major}.{sys.version_info.minor}."
                f"{sys.version_info.micro}"
            )
            toolchains = (
                ToolchainEntry(
                    id=simulation.python_toolchain_identity,
                    runner="local",
                    executable=str(Path(sys.executable).resolve()),
                    version_output_sha256=hashlib.sha256(
                        version.encode("utf-8")
                    ).hexdigest(),
                    network=False,
                ),
            )
    return compile_run_manifest(
        _config(critics=critics),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(scratch_authoring=scratch_authoring),
        criticism_policy=_criticism_policy() if critics else None,
        inquiry_capability_policy=capabilities,
        run_input_digest="f" * 64,
        toolchains=toolchains,
    )


def _simulation_policy(
    *, input_catalog: tuple[SimulationInputBindingV1, ...] = ()
) -> SimulationCapabilityPolicyV1:
    return SimulationCapabilityPolicyV1(
        enabled=True,
        python_toolchain_identity="python@v6-test-runtime",
        maximum_simulation_requests=4,
        maximum_simulation_executions=4,
        maximum_proposals_per_turn=2,
        maximum_generated_code_bytes=16_384,
        maximum_input_bytes=16_384,
        maximum_output_bytes=16_384,
        maximum_wall_ms=10_000,
        maximum_memory_bytes=256 * 1024 * 1024,
        maximum_steps=50_000,
        maximum_samples=32,
        fixed_seed_set=(7,),
        maximum_follow_up_reasoning_turns=4,
        input_catalog=input_catalog,
    )


def _lease(manifest) -> RouteLeaseRefV1:
    route = manifest.roles["conjecturer"][0]
    return RouteLeaseRefV1(
        role="conjecturer",
        seat=0,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
    )


def _prepare(service: InquiryTransactionService, manifest, *, trigger: str):
    return service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=_lease(manifest),
        contract_id="conjecturer.turn.v6",
        trigger_ref=trigger,
        formal_fence_seq=0,
        scratch_fence_seq=0,
        task_payload_value={"task": trigger},
    )


def _provider_call(harness: Harness, authorized, manifest) -> LLMCall:
    route = manifest.roles["conjecturer"][0]
    prompt_ref = harness.blobs.put(b"authorized prompt")
    raw_ref = harness.blobs.put(b'{"candidates":[]}')
    return LLMCall(
        role="conjecturer",
        model=route.model_id,
        endpoint=route.base_url,
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=2,
        prompt_tokens=1,
        completion_tokens=1,
        work_order_id=authorized.bundle.work_id,
        dispatch_authorization_ref=authorized.bundle.id,
    )


def test_recovery_terminalizes_prepared_but_unissued_work(tmp_path):
    manifest = _manifest()
    root = tmp_path / "prepared"
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(1_000))
    preparation = _prepare(service, manifest, trigger="prepared-crash")

    recovered = InquiryTransactionService(
        Harness(root), manifest, TokenMeter(1_000)
    )
    assert recovered.recover_incomplete() == ()

    item = recovered.harness.workflow_state.transaction_work[preparation.id]
    assert item.exposure is None
    assert item.authorization is None
    assert item.terminal.status == "abandoned"
    assert item.terminal.reason_code == "prepared_unissued_recovery"
    assert item.terminal.usage_status == "exact"
    assert (item.terminal.prompt_tokens, item.terminal.completion_tokens) == (0, 0)


def test_reservation_before_failed_issue_append_creates_no_canonical_exposure(
    tmp_path, monkeypatch
):
    manifest = _manifest()
    root = tmp_path / "torn-issue"
    harness = Harness(root)
    meter = TokenMeter(1_000)
    service = InquiryTransactionService(harness, manifest, meter)
    preparation = _prepare(service, manifest, trigger="torn-issue")
    original_commit = harness._commit

    def fail_append(*_args, **_kwargs):
        raise OSError("injected issue append failure")

    monkeypatch.setattr(harness, "_commit", fail_append)
    with pytest.raises(OSError, match="issue append failure"):
        service.issue(preparation, plans=(), prompt="private context", max_tokens=8)
    monkeypatch.setattr(harness, "_commit", original_commit)

    assert meter.snapshot()["reserved"] == 0
    reopened = Harness(root)
    item = reopened.workflow_state.transaction_work[preparation.id]
    assert item.exposure is None
    assert item.authorization is None
    assert all(
        reopened.objects.get(object_id)[0] != "workflow-context-exposure-v2"
        for event in reopened.log.read()
        for object_id in event.outputs
    )

    InquiryTransactionService(reopened, manifest, TokenMeter(1_000)).recover_incomplete()
    assert reopened.workflow_state.transaction_work[preparation.id].terminal.status == (
        "abandoned"
    )


def test_budget_denial_is_terminal_and_never_claims_exposure(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "denied")
    meter = TokenMeter(1)
    service = InquiryTransactionService(harness, manifest, meter)
    preparation = _prepare(service, manifest, trigger="budget-denied")

    with pytest.raises(WorkBudgetDenied) as denied:
        service.issue(preparation, plans=(), prompt="bounded prompt", max_tokens=8)

    assert denied.value.terminal.status == "budget_denied"
    assert meter.snapshot() == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total": 0,
        "budget": 1,
        "calls": 0,
        "reserved": 0,
    }
    item = harness.workflow_state.transaction_work[preparation.id]
    assert item.terminal == denied.value.terminal
    assert item.exposure is None and item.authorization is None
    assert not any(event.llm is not None for event in harness.log.read())


def test_issued_without_provider_result_recovers_as_unknown_abandonment(tmp_path):
    manifest = _manifest()
    root = tmp_path / "issued"
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(1_000))
    preparation = _prepare(service, manifest, trigger="issued-crash")
    authorized = service.issue(
        preparation, plans=(), prompt="authorized prompt", max_tokens=8
    )
    # A process crash discards the live meter lease; only its durable bound remains.
    authorized.release()

    recovered = InquiryTransactionService(
        Harness(root), manifest, TokenMeter(1_000)
    )
    assert recovered.recover_incomplete() == ()
    item = recovered.harness.workflow_state.transaction_work[preparation.id]
    assert item.exposure is not None and item.authorization is not None
    assert item.provider_attempts == {}
    assert item.terminal.status == "abandoned"
    assert item.terminal.reason_code == "issued_result_unknown_recovery"
    assert item.terminal.usage_status == "unknown"
    assert item.terminal.prompt_tokens is None
    assert item.terminal.completion_tokens is None


def test_durable_provider_result_resumes_admission_without_redispatch(tmp_path):
    manifest = _manifest()
    root = tmp_path / "provider-result"
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(1_000))
    preparation = _prepare(service, manifest, trigger="result-crash")
    authorized = service.issue(
        preparation, plans=(), prompt="authorized prompt", max_tokens=8
    )
    call = _provider_call(harness, authorized, manifest)
    authorized.reservation.settle(
        {"prompt_tokens": call.prompt_tokens, "completion_tokens": call.completion_tokens}
    )
    provider = service.record_provider_attempt(
        authorized,
        call=call,
        outcome="provider_result",
        usage_status="exact",
    )

    recovered = InquiryTransactionService(
        Harness(root), manifest, TokenMeter(1_000)
    )
    before = list(recovered.harness.log.read())
    pending = recovered.recover_incomplete()
    assert pending == (provider,)
    assert recovered.harness.blobs.get(pending[0].raw_ref) == b'{"candidates":[]}'
    assert list(recovered.harness.log.read()) == before
    assert recovered.harness.workflow_state.transaction_work[preparation.id].terminal is None

    admitted_ref = "sha256:" + "a" * 64
    admission = recovered.record_semantic_admission(
        pending[0], outcome="admitted", admitted_refs=(admitted_ref,)
    )
    assert recovered.recover_incomplete() == ()
    terminal = recovered.harness.workflow_state.transaction_work[
        preparation.id
    ].terminal
    assert terminal.status == "completed"
    assert terminal.provider_attempt_ref == provider.id
    assert terminal.semantic_admission_ref == admission.id


def test_derived_indexes_bind_to_log_and_rebuild_deterministically(tmp_path):
    manifest = _manifest()
    root = tmp_path / "indexes"
    harness = Harness(root)
    artifact = harness.create_artifact("indexable", provenance=Provenance(role="user"))
    service = InquiryTransactionService(harness, manifest, TokenMeter(1_000))
    preparation = _prepare(service, manifest, trigger="index-work")
    canonical_log = (root / "log.jsonl").read_bytes()
    workflow_digest = harness.workflow_state.digest
    formal_state = harness.state.model_dump(mode="json")

    manifest_path = rebuild_indexes(root)
    first_generation = {
        path.name: path.read_bytes() for path in manifest_path.parent.iterdir()
    }
    indexes = load_indexes(root)
    assert indexes["artifacts"] == [
        {"seq": 0, "artifact_id": artifact.id}
    ]
    assert any(
        row["schema"] == "workflow-work-preparation-v1"
        and row["object_id"] == preparation.id
        for row in indexes["work-orders"]
    )
    index_manifest = json.loads(manifest_path.read_bytes())
    assert index_manifest["source_log_sha256"] == hashlib.sha256(
        canonical_log
    ).hexdigest()
    assert (root / "log.jsonl").read_bytes() == canonical_log
    assert harness.workflow_state.digest == workflow_digest
    assert harness.state.model_dump(mode="json") == formal_state

    rebuild_indexes(root)
    assert {
        path.name: path.read_bytes() for path in manifest_path.parent.iterdir()
    } == first_generation

    harness.record_measure(inputs=["log-advanced"])
    with pytest.raises(DerivedIndexError, match="do not bind"):
        load_indexes(root)
    rebuild_indexes(root)
    assert len(load_indexes(root)["event-offsets"]) == len(list(harness.log.read()))


def _attention_policy() -> AttentionPolicyV1:
    channels = tuple(
        channel for channel in RetrievalChannel if channel != RetrievalChannel.DIRECT_OPEN
    )
    return AttentionPolicyV1(
        max_blocks_per_pack=8,
        max_guides_per_pack=0,
        semantic_retrieval=False,
        keyword_retrieval=True,
        coverage_enabled=False,
        coverage_slot_every_n_packs=1,
        exploratory_fraction=0,
        underexposed_fraction=0,
        dormant_after_events=100,
        similarity_top_k=1,
        similarity_threshold=None,
        guide_max_open_threads=0,
        guide_max_entry_points=0,
        channel_priority=channels,
        per_channel_limits={channel: 8 for channel in channels},
    )


def test_scratch_proposal_write_retrieve_revise_then_fresh_formal_proposal(tmp_path):
    service = ScratchService(tmp_path / "scratch")
    author = ScratchAuthoringService(service, object())
    policy = ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=2,
        maximum_revisions_per_turn=1,
        maximum_links_per_turn=1,
        maximum_unresolved_questions_per_turn=1,
        maximum_cluster_suggestions_per_turn=1,
        maximum_total_bytes=32_768,
    )
    formal_before = service.harness.state.model_dump(mode="json")
    proposal = ScratchProposalV1(
        new_blocks=(
            ScratchNewBlockDraftV1(
                local_key="NEW_001",
                body=ScratchBlockDraftBodyV1(
                    content="Provisional mechanism from scratch",
                    unfinished="Needs a discriminating simulation",
                ),
            ),
            ScratchNewBlockDraftV1(
                local_key="NEW_002",
                body=ScratchBlockDraftBodyV1(content="Possible rival mechanism"),
            ),
        ),
        links=(
            ScratchProposalLinkV1(
                from_ref="NEW_001",
                to_ref="NEW_002",
                relation_hint="provisional rivalry",
            ),
        ),
    )
    outputs = author.admit_proposal(
        proposal,
        policy=policy,
        visible_aliases={},
        context_ref="transaction:scratch-authoring:first",
    )
    original_blocks = sorted(
        (
            block
            for block in service.state.blocks.values()
            if block.revision_of is None
        ),
        key=lambda block: block.body.content,
    )
    mechanism = next(
        block for block in original_blocks if block.body.content.startswith("Provisional")
    )
    assert mechanism.id in outputs
    assert service.harness.state.model_dump(mode="json") == formal_before

    planner = AttentionPlanner(service, _attention_policy())
    request = AttentionRequestV1(
        focus_blocks=[mechanism.id],
        maximum_blocks=2,
        maximum_cluster_guides=0,
        include_nearby=True,
        include_recent=False,
        include_loose=False,
        include_dormant=False,
        include_underexposed=False,
        include_exploratory=False,
        deterministic_seed=7,
    )
    pack = planner.plan(request)
    assert mechanism.id in pack.selection_receipt.final_order
    planner.commit_render(pack, context_ref="transaction:simulate-from-scratch")

    revision = ScratchProposalV1(
        revisions=(
            ScratchRevisionDraftV1(
                target_alias="SCR_001",
                body=ScratchBlockDraftBodyV1(
                    content="Revised mechanism after a negative simulation",
                    unfinished="Still advisory; formulate afresh",
                ),
            ),
        )
    )
    revised_outputs = author.admit_proposal(
        revision,
        policy=policy,
        visible_aliases={"SCR_001": mechanism.id},
        context_ref="transaction:scratch-authoring:revision",
    )
    revised = service.state.blocks[revised_outputs[0]]
    assert revised.revision_of == mechanism.id
    assert revised.body.content.startswith("Revised mechanism")
    assert service.harness.state.model_dump(mode="json") == formal_before

    fresh = service.harness.create_artifact(
        "Fresh formal proposal independently admitted after scratch exploration",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    scratch_ids = set(service.state.blocks) | set(service.state.links)
    assert fresh.id in service.harness.state.artifacts
    assert scratch_ids.isdisjoint(service.harness.state.artifacts)
    assert scratch_ids.isdisjoint(service.harness.commitments)
    assert scratch_ids.isdisjoint(service.harness.warrants)
    assert fresh.interface.refs == []
    assert all(
        scratch_id not in pair
        for scratch_id in scratch_ids
        for pair in (*service.harness.state.att, *service.harness.state.dep)
    )


def test_v6_critic_schema_failure_is_operational_and_leaves_coverage_debt(tmp_path):
    config = _config(critics=True)
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
    harness = Harness(tmp_path / "criticism")
    target = harness.create_artifact(
        "school-owned target",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    endpoints = {
        "conjecturer": MockEndpoint('{"candidates":[]}'),
        "argumentative_critic": [
            MockEndpoint("{not-json", name=route.base_url, model=route.model_id)
            for route in manifest.roles["argumentative_critic"]
        ],
    }
    adapter = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
        meter=TokenMeter(100_000),
    )
    scheduler = Scheduler(harness, adapter, config, run_manifest=manifest)

    scheduler._foreign_arg_crit()

    attempts = []
    debts = []
    assignments = []
    for event in harness.log.read():
        for object_id in event.outputs:
            schema, record = harness.objects.get(object_id)
            if schema == "criticism-assignment-v1" and record.target_id == target.id:
                assignments.append(record)
            elif schema == "criticism-attempt-v1" and record.target_id == target.id:
                attempts.append(record)
            elif schema == "criticism-coverage-debt-v1" and record.target_id == target.id:
                debts.append(record)
    assert len(assignments) == 2
    assert len(attempts) == 2
    assert all(attempt.outcome == "schema_failure" for attempt in attempts)
    assert all(not attempt.coverage_completed for attempt in attempts)
    assert len(debts) == 1
    assert debts[0].completed_school_ids == ()
    assert len(debts[0].outstanding_school_ids) == 2
    assert debts[0].termination_reason == "attempts_exhausted"
    assert set(debts[0].attempt_refs) == {attempt.id for attempt in attempts}
    assert not any(
        event.inputs[:1] == ["foreign-criticism-coverage.v1"]
        and event.inputs[1] == target.id
        for event in harness.log.read()
    )

def _v6_simulation_turn() -> dict:
    source = json.dumps(
        {
            "schema": "declarative-numeric.v1",
            "observables": {
                "x": {
                    "op": "div",
                    "args": [
                        {"input": "parameters.weight_bytes"},
                        {"const": 2},
                    ],
                }
            },
        }
    )
    return {
        "simulation_proposals": [
            {
                "request_identifier": "v6-transaction-discriminator",
                "hypothesis": "The scheduled transfer remains below ten units.",
                "rival_predictions": ["x is below 10", "x is at least 10"],
                "discriminating_purpose": "Separate the two bounded rivals.",
                "declared_assumptions": ["The schedule is synthetic."],
                "parameter_definitions": [
                    {"name": "one", "values_json": "{\"weight_bytes\":12}"}
                ],
                "requested_seed_set": [],
                "simulation_mode": "declarative_numeric_v1",
                "model_source": source,
                "requested_observables": ["x"],
                "interpretation_conditions": [
                    "x below 10 favors the first rival."
                ],
            }
        ]
    }


def _seed_live_conjecture(harness: Harness) -> None:
    harness.register_commitment(
        Commitment(id="k-live-v6", eval="predicate:len(content) > 0")
    )
    harness.register_problem(
        Problem(
            id="pi-live-v6",
            description="Invent one provisional mechanism.",
            criteria=["k-live-v6"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _live_adapter(harness, manifest, response, *, budget=100_000):
    route = manifest.roles["conjecturer"][0]
    endpoint = MockEndpoint(
        response,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    return (
        LLMAdapter(
            {"conjecturer": endpoint},
            harness.blobs,
            retry_max=0,
            meter=TokenMeter(budget),
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
            transaction_authority_required=True,
        ),
        endpoint,
    )


def test_live_v6_conjecture_dispatch_observes_durable_issue_authority(tmp_path):
    config = _config()
    manifest = _manifest()
    harness = Harness(tmp_path / "live-issued")
    _seed_live_conjecture(harness)
    observed = []
    serialized_policy = manifest.control_plane_policy.scratch_authoring.model_dump(
        mode="json"
    )
    assert serialized_policy["purpose"] == "imaginative_workshop"
    assert serialized_policy["epistemic_boundary"] == "advisory_non_grounding"

    def response(prompt):
        assert V6_SCRATCH_WORKSHOP_PROMPT not in prompt
        transactions = tuple(harness.workflow_state.transaction_work.values())
        assert len(transactions) == 1
        work = transactions[0]
        assert work.issued
        assert work.authorization is not None
        assert work.exposure is not None
        assert work.provider_attempts == {}
        assert work.terminal is None
        assert work.authorization.prompt_sha256 == hashlib.sha256(
            prompt.encode("utf-8")
        ).hexdigest()
        observed.append(work.authorization.id)
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": "A reversible feedback mechanism.",
                        "typicality": 0.37,
                    }
                ]
            }
        )

    adapter, _endpoint = _live_adapter(harness, manifest, response)
    Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(1)

    assert len(observed) == 1
    work, = harness.workflow_state.transaction_work.values()
    assert work.terminal.status == "completed"
    assert work.authorization.id == observed[0]
    provider_events = [
        event for event in harness.log.read() if event.llm is not None
    ]
    assert len(provider_events) == 1
    assert provider_events[0].llm.dispatch_authorization_ref == observed[0]
    assert provider_events[0].llm.work_order_id == work.preparation.id
    assert not any(
        event.inputs
        and event.inputs[0] in {"workflow-conjecture-call", "conjecture-turn-call"}
        for event in harness.log.read()
    )
    reopened = Harness(harness.root)
    assert reopened.workflow_state.transaction_work[
        work.preparation.id
    ].terminal.status == "completed"

def test_live_v6_enabled_scratch_is_a_positive_advisory_workshop(tmp_path):
    policy = ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=1,
        maximum_revisions_per_turn=0,
        maximum_links_per_turn=0,
        maximum_unresolved_questions_per_turn=1,
        maximum_cluster_suggestions_per_turn=0,
        maximum_total_bytes=32_768,
    )
    config = _config()
    manifest = _manifest(scratch_authoring=policy)
    harness = Harness(tmp_path / "live-scratch-workshop")
    _seed_live_conjecture(harness)
    captured = []

    def response(prompt):
        captured.append(prompt)
        assert V6_SCRATCH_WORKSHOP_PROMPT in prompt
        return json.dumps(
            {
                "scratch_proposal": {
                    "new_blocks": [
                        {
                            "local_key": "NEW_001",
                            "body": {
                                "content": (
                                    "Maybe the mechanism reverses under a "
                                    "counterfactual delayed feedback loop."
                                ),
                                "unfinished": "Contradicts the first intuition.",
                            },
                        }
                    ],
                    "unresolved_questions": [
                        {
                            "question": "Which observation would separate the rivals?",
                            "related_refs": ["NEW_001"],
                        }
                    ],
                }
            }
        )

    adapter, _endpoint = _live_adapter(harness, manifest, response)
    Scheduler(
        harness,

        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(1)

    assert len(captured) == 1
    work, = harness.workflow_state.transaction_work.values()
    assert work.terminal.status == "completed"
    assert ScratchService(harness).state.blocks
    assert not harness.state.artifacts


def test_v6_unbound_capability_result_is_rejected_before_exposure(tmp_path):
    config = _config()
    manifest = _manifest()
    harness = Harness(tmp_path / "capability-result-follow-up")
    _seed_live_conjecture(harness)
    prompts = []

    def response(prompt):
        prompts.append(prompt)
        work, = harness.workflow_state.transaction_work.values()
        assert work.issued
        assert work.exposure is not None
        assert [item.alias for item in work.exposure.exposed_items] == ["SIM_001"]
        return json.dumps({"abstention": {"search_signal": "stuck"}})

    adapter, _endpoint = _live_adapter(harness, manifest, response)
    result_context = json.dumps(
        {
            "schema": "simulation.result.v1",
            "observation": "The delayed rival diverged at step 4.",
        },
        sort_keys=True,
    )
    with pytest.raises(ValueError, match="requires package, context ref, and text"):
        conj(
            harness,
            "pi-live-v6",
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
            _capability_result_context=result_context,
            _simulation_follow_up_index=1,
        )

    assert prompts == []
    assert harness.workflow_state.transaction_work == {}



def test_v6_simulation_uses_transaction_origin_and_fresh_completed_follow_up(
    tmp_path,
):
    config = _config()
    sealed_value = {"weight_bytes": 12}
    sealed_input = SimulationInputBindingV1(
        alias="WEIGHT_INPUT",
        description="Frozen weight input for the simulation.",
        value=sealed_value,
        content_sha256=hashlib.sha256(canonical_json(sealed_value)).hexdigest(),
    )
    manifest = _manifest(
        simulation=_simulation_policy(input_catalog=(sealed_input,))
    )
    harness = Harness(tmp_path / "simulation-transaction-lifecycle")
    _seed_live_conjecture(harness)
    prompts = []
    first_turn = _v6_simulation_turn()
    first_turn["simulation_proposals"][0]["input_aliases"] = ["SIM_001"]
    responses = [
        first_turn,
        {"abstention": {"search_signal": "stuck"}},
    ]

    def response(prompt):
        prompts.append(prompt)
        return json.dumps(responses.pop(0))

    adapter, _endpoint = _live_adapter(harness, manifest, response)
    assert (
        conj(
            harness,
            "pi-live-v6",
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        )
        == []
    )
    proposal, = harness.capability_state.proposals.values()
    origin = harness.workflow_state.transaction_work[
        proposal.originating_work_order_ref
    ]
    assert proposal.originating_work_order_ref not in harness.workflow_state.work_orders
    assert proposal.originating_provider_attempt_ref in {
        item.id for item in origin.provider_attempts.values()
    }
    origin_admission, = origin.admissions.values()
    assert proposal.id in origin_admission.admitted_refs
    assert proposal.input_aliases == ("SIM_001",)

    scheduler = Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    scheduler.step()
    package, = harness.capability_state.result_packages.values()
    assert harness.capability_state.consumptions == {}
    scheduler.step()

    assert responses == []
    assert len(prompts) == 2
    assert "SIM_002: recorded simulation result" in prompts[1]
    follow_up = next(
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_payload_value.get("simulation_follow_up_index") == 1
    )
    payload = follow_up.preparation.task_payload_value
    assert payload["capability_result_package_ref"] == package.id
    assert payload["capability_result_context_ref"] == package.result_context_ref
    assert package.id in follow_up.preparation.input_refs
    assert package.result_context_ref in follow_up.preparation.input_refs
    sealed_plan, = (
        plan
        for plan in follow_up.plans.values()
        if plan.plan_kind == "simulation"
    )
    sealed_item, = sealed_plan.items
    result_plan, = (
        plan
        for plan in follow_up.plans.values()
        if plan.plan_kind == "simulation_result"
    )
    result_item, = result_plan.items
    assert result_item.object_ref == package.id
    assert result_item.content_sha256 == package.result_context_ref
    assert sealed_item.alias == "SIM_001"
    assert result_item.alias == "SIM_002"
    assert follow_up.terminal.status == "completed"
    consumption, = harness.capability_state.consumptions.values()
    assert consumption.follow_up_work_order_ref == follow_up.preparation.id
    assert consumption.follow_up_semantic_admission_ref in {
        item.id for item in follow_up.admissions.values()
    }
    prompt_schema = prompts[1].split("\n\n## problem", 1)[0]
    assert "SIM_001" in prompt_schema
    assert "SIM_002" not in prompt_schema

    reopened = Harness(harness.root)
    assert list(reopened.capability_state.consumptions) == [consumption.id]
    assert reopened.workflow_state.transaction_work[
        follow_up.preparation.id
    ].terminal.status == "completed"



@pytest.mark.parametrize(
    ("response", "terminal_status"),
    (
        ("{not-json", "schema_exhausted"),
        (EndpointError("offline provider unavailable"), "transport_failed"),
    ),
)
def test_live_v6_conjecture_failure_is_typed_and_replayable(
    tmp_path, response, terminal_status
):
    config = _config()
    manifest = _manifest()
    harness = Harness(tmp_path / terminal_status)
    _seed_live_conjecture(harness)

    if isinstance(response, Exception):
        def fail(_prompt):
            raise response

        response_value = fail
    else:
        response_value = response
    adapter, _endpoint = _live_adapter(harness, manifest, response_value)
    Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(1)

    work_items = tuple(harness.workflow_state.transaction_work.values())
    primary, = [
        item
        for item in work_items
        if item.preparation.task_kind == WorkflowTaskKind.CONJECTURE
    ]
    repairs = [
        item
        for item in work_items
        if item.preparation.task_kind == WorkflowTaskKind.REPAIR
    ]
    assert primary.issued
    assert primary.terminal.status == (
        "rejected" if terminal_status == "schema_exhausted" else terminal_status
    )
    assert len(primary.provider_attempts) == 1
    if terminal_status == "schema_exhausted":
        repair, = repairs
        assert repair.issued
        assert repair.terminal.status == "schema_exhausted"
    else:
        assert repairs == []
    assert len([event for event in harness.log.read() if event.llm is not None]) == (
        2 if repairs else 1
    )
    reopened = Harness(harness.root)
    assert reopened.workflow_state.transaction_work[
        primary.preparation.id
    ].terminal.status == primary.terminal.status
    assert all(
        reopened.workflow_state.transaction_work[item.preparation.id].terminal.status
        == item.terminal.status
        for item in repairs
    )


def test_live_v6_budget_denial_never_dispatches_or_exposes_context(tmp_path):
    config = _config()
    manifest = _manifest()
    harness = Harness(tmp_path / "live-denied")
    _seed_live_conjecture(harness)
    called = []

    def forbidden(_prompt):
        called.append(True)
        raise AssertionError("provider dispatch occurred without token authority")

    adapter, _endpoint = _live_adapter(harness, manifest, forbidden, budget=1)
    Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(1)

    assert called == []
    work, = harness.workflow_state.transaction_work.values()
    assert work.terminal.status == "budget_denied"
    assert work.exposure is None
    assert work.authorization is None
    assert not any(event.llm is not None for event in harness.log.read())

def test_v6_foreign_criticism_mixed_failure_and_success_are_root_local(tmp_path):
    config = _config(critics=True)
    manifest = _manifest(critics=True)
    harness = Harness(tmp_path / "criticism-mixed")
    target = harness.create_artifact(
        "school-owned target",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    calls = [0, 0, 0]
    prompts: list[list[str]] = [[], [], []]

    def response_for(seat: int):
        def respond(prompt: str) -> str:
            calls[seat] += 1
            prompts[seat].append(prompt)
            if seat == 1:
                return "{not-json"
            return json.dumps(
                {
                    "cases": [
                        {
                            "target_alias": "SRC_001",
                            "attack": False,
                            "case": "",
                            "counterexample": None,
                        }
                    ]
                }
            )

        return respond

    critic_endpoints = [
        MockEndpoint(
            response_for(seat),
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )
        for seat, route in enumerate(manifest.roles["argumentative_critic"])
    ]
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint('{"candidates":[]}'),
            "argumentative_critic": critic_endpoints,
        },
        harness.blobs,
        retry_max=2,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
        meter=TokenMeter(100_000),
    )

    Scheduler(harness, adapter, config, run_manifest=manifest)._foreign_arg_crit()

    records: dict[str, list] = {}
    for event in harness.log.read():
        for object_id in event.outputs:
            schema, record = harness.objects.get(object_id)
            records.setdefault(schema, []).append(record)
    attempts = [
        record
        for record in records["criticism-attempt-v1"]
        if record.target_id == target.id
    ]
    assert {(record.critic_school_id, record.outcome) for record in attempts} == {
        ("school-1", "schema_failure"),
        ("school-2", "completed"),
    }
    assert sum(record.coverage_completed for record in attempts) == 1

    debt, = [
        record
        for record in records["criticism-coverage-debt-v1"]
        if record.target_id == target.id
    ]
    assert debt.completed_school_ids == ("school-2",)
    assert debt.outstanding_school_ids == ("school-1",)
    assert debt.termination_reason == "attempts_exhausted"

    coverage_events = [
        event
        for event in harness.log.read()
        if event.inputs[:1] == ["foreign-criticism-coverage.v1"]
        and event.inputs[1] == target.id
    ]
    assert len(coverage_events) == 1
    assert coverage_events[0].inputs[3] == "critic:school-2"
    assert calls == [0, 2, 1]
    primary_prompts = (prompts[1][0], prompts[2][0])
    assert all("SRC_001" in prompt for prompt in primary_prompts)
    assert all("target_alias" in prompt for prompt in primary_prompts)
    assert len(prompts[1]) == 2
    assert "batch-critic.v2" in prompts[1][1]

    critic_work = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.CRITICISM
    ]
    repair_work = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.REPAIR
    ]
    assert len(critic_work) == 2
    assert {item.terminal.status for item in critic_work} == {
        "completed",
        "rejected",
    }
    repair, = repair_work
    assert repair.terminal.status == "schema_exhausted"
    work_items = [*critic_work, repair]
    assert all(item.issued and item.exposure is not None for item in work_items)
    assert all(item.preparation.contract_id == "batch-critic.v2" for item in work_items)
    assert all(len(item.provider_attempts) == 1 for item in work_items)
    assert all(len(item.admissions) == 1 for item in work_items)
    assert not any(item.outstanding for item in work_items)

    issued_ids = {item.preparation.id for item in work_items if item.issued}
    critic_calls = [
        event.llm
        for event in harness.log.read()
        if event.llm is not None and event.llm.role == "argumentative_critic"
    ]
    assert len(critic_calls) == 3
    assert all(call.work_order_id in issued_ids for call in critic_calls)
    assert all(call.dispatch_authorization_ref for call in critic_calls)


def test_v6_counterexample_retry_has_a_distinct_issued_transaction(tmp_path):
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
    sneaky_sort = (
        "def solve(xs):\n"
        "    if len(xs) > 2:\n"
        "        return sorted(xs)\n"
        "    return xs\n"
    )
    config = _config(critics=True)
    config.CX_RETRY_MAX = 1
    manifest = _manifest(critics=True)
    harness = Harness(tmp_path / "criticism-cx-retry")
    commitment = property_oracle_commitment(
        "solve",
        [[[3, 1, 2]]],
        checker,
        gate,
    )
    harness.register_commitment(commitment)
    target = harness.create_artifact(
        sneaky_sort,
        codec="code:python",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )

    primary = json.dumps(
        {
            "cases": [
                {
                    "target_alias": "SRC_001",
                    "attack": True,
                    "case": "fails on short lists",
                    "counterexample": [["wrong-domain"]],
                }
            ]
        }
    )
    retry = json.dumps(
        {
            "cases": [
                {
                    "target_alias": "SRC_001",
                    "attack": True,
                    "case": "fails on two integers",
                    "counterexample": [[2, 1]],
                }
            ]
        }
    )
    withdraw = json.dumps(
        {
            "cases": [
                {
                    "target_alias": "SRC_001",
                    "attack": False,
                    "case": "",
                    "counterexample": None,
                }
            ]
        }
    )
    responses = ([], [primary, retry], [withdraw])
    critic_endpoints = [
        MockEndpoint(
            responses[seat],
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )
        for seat, route in enumerate(manifest.roles["argumentative_critic"])
    ]
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint('{"candidates":[]}'),
            "argumentative_critic": critic_endpoints,
        },
        harness.blobs,
        retry_max=2,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
        meter=TokenMeter(100_000),
    )

    Scheduler(harness, adapter, config, run_manifest=manifest)._foreign_arg_crit()

    assert harness.state.status[target.id] == Status.REFUTED
    work_items = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.CRITICISM
    ]
    assert len(work_items) == 3
    phases = [
        item.preparation.task_payload_value["phase"]
        for item in work_items
    ]
    assert phases.count("primary") == 2
    assert phases.count("counterexample_retry:0") == 1
    assert all(item.issued for item in work_items)
    assert all(item.terminal.status == "completed" for item in work_items)
    assert all(item.preparation.contract_id == "batch-critic.v2" for item in work_items)

    authorization_ids = {item.authorization.id for item in work_items}
    assert len(authorization_ids) == 3
    critic_calls = [
        event.llm
        for event in harness.log.read()
        if event.llm is not None and event.llm.role == "argumentative_critic"
    ]
    assert len(critic_calls) == 3
    assert {call.dispatch_authorization_ref for call in critic_calls} == (
        authorization_ids
    )
    issued_ids = {item.preparation.id for item in work_items}
    assert {call.work_order_id for call in critic_calls} == issued_ids


def test_v6_criticism_budget_denial_records_debt_without_exposure_or_dispatch(
    tmp_path,
):
    config = _config(critics=True)
    manifest = _manifest(critics=True)
    harness = Harness(tmp_path / "criticism-budget-denied")
    target = harness.create_artifact(
        "school-owned target",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    called = []

    def forbidden(_prompt):
        called.append(True)
        raise AssertionError("critic provider dispatched after budget denial")

    critic_endpoints = [
        MockEndpoint(
            forbidden,
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )
        for route in manifest.roles["argumentative_critic"]
    ]
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint('{"candidates":[]}'),
            "argumentative_critic": critic_endpoints,
        },
        harness.blobs,
        retry_max=2,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
        meter=TokenMeter(1),
    )

    Scheduler(harness, adapter, config, run_manifest=manifest)._foreign_arg_crit()

    assert called == []
    attempts = []
    debts = []
    for event in harness.log.read():
        for object_id in event.outputs:
            schema, record = harness.objects.get(object_id)
            if schema == "criticism-attempt-v1" and record.target_id == target.id:
                attempts.append(record)
            if (
                schema == "criticism-coverage-debt-v1"
                and record.target_id == target.id
            ):
                debts.append(record)
    assert len(attempts) == 2
    assert all(record.outcome == "budget_denied" for record in attempts)
    assert all(not record.coverage_completed for record in attempts)
    debt, = debts
    assert debt.completed_school_ids == ()
    assert set(debt.outstanding_school_ids) == {"school-1", "school-2"}
    assert debt.termination_reason == "budget_exhausted"

    work_items = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.CRITICISM
    ]
    assert len(work_items) == 2
    assert all(item.terminal.status == "budget_denied" for item in work_items)
    assert all(not item.issued for item in work_items)
    assert all(item.exposure is None for item in work_items)
    assert all(item.authorization is None for item in work_items)
    assert not any(
        event.llm is not None and event.llm.role == "argumentative_critic"
        for event in harness.log.read()
    )
    assert not any(
        event.inputs[:1] == ["foreign-criticism-coverage.v1"]
        for event in harness.log.read()
    )


def test_v6_failed_counterexample_retry_leaves_criticism_coverage_outstanding(
    tmp_path,
):
    config = _config(critics=True)
    config.CX_RETRY_MAX = 1
    manifest = _manifest(critics=True)
    harness = Harness(tmp_path / "criticism-cx-retry-failure")
    commitment = property_oracle_commitment(
        "solve",
        [[[3, 1, 2]]],
        (
            "def check(inp, out):\n"
            "    return isinstance(out, list) and sorted(inp[0]) == out\n"
        ),
        (
            "def valid(inp):\n"
            "    return (isinstance(inp, list) and len(inp) == 1 and "
            "isinstance(inp[0], list) and "
            "all(isinstance(x, int) for x in inp[0]))\n"
        ),
    )
    harness.register_commitment(commitment)
    target = harness.create_artifact(
        (
            "def solve(xs):\n"
            "    if len(xs) > 2:\n"
            "        return sorted(xs)\n"
            "    return xs\n"
        ),
        codec="code:python",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    primary = json.dumps(
        {
            "cases": [
                {
                    "target_alias": "SRC_001",
                    "attack": True,
                    "case": "fails on short lists",
                    "counterexample": [["wrong-domain"]],
                }
            ]
        }
    )
    withdraw = json.dumps(
        {
            "cases": [
                {
                    "target_alias": "SRC_001",
                    "attack": False,
                    "case": "",
                    "counterexample": None,
                }
            ]
        }
    )
    responses = ([], [primary, "{not-json", "{not-json"], [withdraw])
    critic_endpoints = [
        MockEndpoint(
            responses[seat],
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )
        for seat, route in enumerate(manifest.roles["argumentative_critic"])
    ]
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint('{"candidates":[]}'),
            "argumentative_critic": critic_endpoints,
        },
        harness.blobs,
        retry_max=2,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
        meter=TokenMeter(100_000),
    )

    Scheduler(harness, adapter, config, run_manifest=manifest)._foreign_arg_crit()

    attempts = []
    coverage_schools = set()
    for event in harness.log.read():
        if (
            event.inputs[:1] == ["foreign-criticism-coverage.v1"]
            and event.inputs[1] == target.id
        ):
            coverage_schools.add(event.inputs[3].removeprefix("critic:"))
        for object_id in event.outputs:
            schema, record = harness.objects.get(object_id)
            if schema == "criticism-attempt-v1" and record.target_id == target.id:
                attempts.append(record)
    assert {(record.critic_school_id, record.outcome) for record in attempts} == {
        ("school-1", "schema_failure"),
        ("school-2", "completed"),
    }
    assert coverage_schools == {"school-2"}

    work_items = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.CRITICISM
    ]
    assert len(work_items) == 3
    assert sorted(item.terminal.status for item in work_items) == [
        "completed",
        "completed",
        "rejected",
    ]
    retry_work, = [
        item
        for item in work_items
        if item.preparation.task_payload_value["phase"]
        == "counterexample_retry:0"
    ]
    assert retry_work.issued
    assert retry_work.terminal.status == "rejected"
    repair_work, = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_kind == WorkflowTaskKind.REPAIR
        and item.preparation.task_payload_value["parent_work_id"]
        == retry_work.preparation.id
    ]
    assert repair_work.issued
    assert repair_work.terminal.status == "schema_exhausted"



def test_v6_restart_admits_durable_conjecture_result_without_redispatch(
    tmp_path,
    monkeypatch,
):
    config = _config()
    manifest = _manifest()
    root = tmp_path / "provider-result-restart"
    harness = Harness(root)
    _seed_live_conjecture(harness)
    source = harness.create_artifact(
        "A formal source visible through a frozen alias."
    )
    first_calls = []

    def response(prompt):
        first_calls.append(True)
        assert "SRC_001" in prompt
        assert source.id not in prompt
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": "A crash-resilient reversible mechanism.",
                        "typicality": 0.21,
                        "neighbours": ["SRC_001"],
                    }
                ]
            }
        )

    adapter, _endpoint = _live_adapter(
        harness,
        manifest,
        response,
    )
    original_register_batch = harness.register_batch

    def crash_before_semantic_effect(*args, **kwargs):
        if kwargs.get("process_inputs"):
            raise OSError(
                "injected crash after durable provider result"
            )
        return original_register_batch(*args, **kwargs)

    monkeypatch.setattr(
        harness,
        "register_batch",
        crash_before_semantic_effect,
    )
    with pytest.raises(
        OSError,
        match="after durable provider result",
    ):
        Scheduler(
            harness,
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        ).run(1)

    crashed = Harness(root)
    work, = crashed.workflow_state.transaction_work.values()
    assert work.provider_attempts
    assert work.admissions == {}
    assert work.terminal is None
    assert set(crashed.state.artifacts) == {source.id}
    assert first_calls == [True]

    restarted_calls = []

    def forbidden(_prompt):
        restarted_calls.append(True)
        raise AssertionError(
            "recovery must not redispatch a durable provider result"
        )

    recovered_adapter, _endpoint = _live_adapter(
        crashed,
        manifest,
        forbidden,
    )
    Scheduler(
        crashed,
        recovered_adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(0)

    recovered_work = crashed.workflow_state.transaction_work[
        work.preparation.id
    ]
    assert recovered_work.terminal.status == "completed"
    assert len(recovered_work.admissions) == 1
    assert len(crashed.state.artifacts) == 2
    recovered_artifact, = [
        artifact
        for artifact in crashed.state.artifacts.values()
        if artifact.id != source.id
    ]
    assert [ref.target for ref in recovered_artifact.interface.refs] == [
        source.id
    ]
    assert restarted_calls == []
    assert len(
        [
            event
            for event in crashed.log.read()
            if event.llm is not None
        ]
    ) == 1

    before = tuple(crashed.log.read())
    Scheduler(
        crashed,
        recovered_adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(0)
    assert tuple(crashed.log.read()) == before
    assert restarted_calls == []


def test_v6_restart_schema_exhaustion_uses_stored_raw_without_dispatch(
    tmp_path,
):
    config = _config()
    manifest = _manifest()
    root = tmp_path / "stored-invalid-result"
    harness = Harness(root)
    _seed_live_conjecture(harness)
    problem = harness.state.problems["pi-live-v6"]
    service = InquiryTransactionService(
        harness,
        manifest,
        TokenMeter(100_000),
    )
    simulation = manifest.inquiry_capability_policy.simulation
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=_lease(manifest),
        contract_id="conjecturer.turn.v6",
        trigger_ref="stored-invalid-result",
        formal_fence_seq=harness._next_seq - 1,
        scratch_fence_seq=harness._next_seq - 1,
        target_refs=(problem.id,),
        input_refs=tuple(problem.criteria),
        task_payload_value={
            "schema": "conjecture.semantic-task.v2",
            "problem_ref": problem.id,
            "school_id": None,
            "run_input_digest": manifest.run_input_digest,
            "allowed_outcomes": [
                "candidate_proposal",
                "context_request",
                "abstention",
            ],
            "maximum_candidates": config.VS_K,
            "simulation_authority": {
                "enabled": simulation.enabled,
                "policy_digest": simulation.digest,
                "maximum_proposals_per_turn": (
                    simulation.maximum_proposals_per_turn
                ),
                "input_aliases": [],
            },
            "scratch_authoring_enabled": False,
            "context_expansion_index": 0,
            "simulation_follow_up_index": 0,
            "capability_result_ref": None,
            "capability_result_package_ref": None,
            "capability_result_context_ref": None,
            "workload_profile": "text",
            "reasoning": False,
            "tail_weighted": False,
            "complement": False,
            "specs": [],
            "mandatory_interface": None,
            "component_spec": None,
            "theorem_interface": None,
        },
    )
    authorized = service.issue(
        preparation,
        plans=(),
        prompt="authorized prompt",
        max_tokens=8,
    )
    call = _provider_call(
        harness,
        authorized,
        manifest,
    )
    authorized.reservation.settle(
        {
            "prompt_tokens": call.prompt_tokens,
            "completion_tokens": call.completion_tokens,
        }
    )
    service.record_provider_attempt(
        authorized,
        call=call,
        outcome="provider_result",
        usage_status="exact",
    )

    reopened = Harness(root)
    called = []

    def forbidden(_prompt):
        called.append(True)
        raise AssertionError("stored schema recovery dispatched")

    adapter, _endpoint = _live_adapter(
        reopened,
        manifest,
        forbidden,
    )
    Scheduler(
        reopened,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(0)

    item = reopened.workflow_state.transaction_work[
        preparation.id
    ]
    assert item.terminal.status == "schema_exhausted"
    admission, = item.admissions.values()
    assert admission.outcome == "schema_exhausted"
    assert called == []




def test_v6_restart_reuses_scratch_effects_before_admission(
    tmp_path,
    monkeypatch,
):
    policy = ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=1,
        maximum_revisions_per_turn=0,
        maximum_links_per_turn=0,
        maximum_unresolved_questions_per_turn=0,
        maximum_cluster_suggestions_per_turn=0,
        maximum_total_bytes=32_768,
    )
    config = _config()
    manifest = _manifest(scratch_authoring=policy)
    root = tmp_path / "scratch-before-admission"
    harness = Harness(root)
    _seed_live_conjecture(harness)
    calls = []

    def response(_prompt):
        calls.append(True)
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": (
                            "A formal mechanism also survives the "
                            "admission-boundary restart."
                        ),
                        "typicality": 0.17,
                    }
                ],
                "scratch_proposal": {
                    "new_blocks": [
                        {
                            "local_key": "NEW_001",
                            "body": {
                                "content": (
                                    "A daring scratch mechanism survives "
                                    "a process restart."
                                )
                            },
                        }
                    ]
                }
            }
        )

    adapter, _endpoint = _live_adapter(
        harness,
        manifest,
        response,
    )
    original_admit = (
        InquiryTransactionService.record_semantic_admission
    )

    def crash_after_scratch(*_args, **_kwargs):
        raise OSError("injected crash after scratch effects")

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_scratch,
    )
    with pytest.raises(
        OSError,
        match="after scratch effects",
    ):
        Scheduler(
            harness,
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        ).run(1)
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admit,
    )

    reopened = Harness(root)
    work, = reopened.workflow_state.transaction_work.values()
    assert work.provider_attempts
    assert work.admissions == {}
    scratch_before = tuple(
        (
            event.seq,
            tuple(event.outputs),
        )
        for event in reopened.log.read()
        if event.scratch is not None
        and event.scratch.context_ref == work.exposure.id
    )
    assert len(scratch_before) == 1
    scratch_ids = set(reopened.scratch_state.blocks)
    formal_ids = set(reopened.state.artifacts)
    assert len(formal_ids) == 1
    provider = next(iter(work.provider_attempts.values()))
    provider_event = next(
        event
        for event in reopened.log.read()
        if event.llm is not None
        and event.llm.dispatch_authorization_ref == provider.authorization_bundle_ref
    )
    formal_call_ref = f"conjecture-call:{provider_event.seq}"
    formal_events_before = tuple(
        (
            event.seq,
            tuple(event.inputs),
            tuple(event.outputs),
        )
        for event in reopened.log.read()
        if formal_call_ref in event.inputs
    )
    assert len(formal_events_before) == 1

    recovery_calls = []

    def forbidden(_prompt):
        recovery_calls.append(True)
        raise AssertionError("scratch recovery redispatched")

    recovered_adapter, _endpoint = _live_adapter(
        reopened,
        manifest,
        forbidden,
    )
    Scheduler(
        reopened,
        recovered_adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(0)

    recovered = reopened.workflow_state.transaction_work[
        work.preparation.id
    ]
    assert recovered.terminal.status == "completed"
    assert recovery_calls == []
    assert set(reopened.scratch_state.blocks) == scratch_ids
    assert set(reopened.state.artifacts) == formal_ids
    assert tuple(
        (
            event.seq,
            tuple(event.inputs),
            tuple(event.outputs),
        )
        for event in reopened.log.read()
        if formal_call_ref in event.inputs
    ) == formal_events_before
    assert tuple(
        (
            event.seq,
            tuple(event.outputs),
        )
        for event in reopened.log.read()
        if event.scratch is not None
        and event.scratch.context_ref == work.exposure.id
    ) == scratch_before
    assert calls == [True]

def test_v6_restart_reuses_simulation_proposal_before_admission(
    tmp_path,
    monkeypatch,
):
    config = _config()
    manifest = _manifest(simulation=_simulation_policy())
    root = tmp_path / "simulation-before-admission"
    harness = Harness(root)
    _seed_live_conjecture(harness)
    dispatches = []

    def response(_prompt):
        dispatches.append(True)
        return json.dumps(_v6_simulation_turn())

    adapter, _endpoint = _live_adapter(harness, manifest, response)
    original_admit = InquiryTransactionService.record_semantic_admission

    def crash_after_proposal(*_args, **_kwargs):
        raise OSError("injected crash after simulation proposal")

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_proposal,
    )
    with pytest.raises(OSError, match="after simulation proposal"):
        conj(
            harness,
            "pi-live-v6",
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        )
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admit,
    )

    reopened = Harness(root)
    work, = reopened.workflow_state.transaction_work.values()
    provider, = work.provider_attempts.values()
    proposal, = reopened.capability_state.proposals.values()
    proposal_id = proposal.id
    assert work.admissions == {}
    assert work.terminal is None
    assert proposal.originating_work_order_ref == work.preparation.id
    assert proposal.originating_work_order_ref not in reopened.workflow_state.work_orders
    assert proposal.originating_provider_attempt_ref == provider.id

    recovery_dispatches = []

    def forbidden(_prompt):
        recovery_dispatches.append(True)
        raise AssertionError("simulation proposal recovery redispatched")

    recovered_adapter, _endpoint = _live_adapter(
        reopened,
        manifest,
        forbidden,
    )
    Scheduler(
        reopened,
        recovered_adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(0)

    recovered = reopened.workflow_state.transaction_work[work.preparation.id]
    assert recovered.terminal.status == "completed"
    admission, = recovered.admissions.values()
    assert proposal_id in admission.admitted_refs
    assert list(reopened.capability_state.proposals) == [proposal_id]
    assert recovery_dispatches == []
    assert dispatches == [True]
    assert len([event for event in reopened.log.read() if event.llm is not None]) == 1

    before = tuple(reopened.log.read())
    Scheduler(
        reopened,
        recovered_adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).run(0)
    assert tuple(reopened.log.read()) == before
    assert list(reopened.capability_state.proposals) == [proposal_id]
    assert recovery_dispatches == []
