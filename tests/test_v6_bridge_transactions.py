"""Offline qualification for transactional RunManifest-v6 bridge calls."""

from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
import json

import pytest
from pydantic import BaseModel, ConfigDict

from deepreason.application.bridge import _compiled_bridge_workflow_policy
from deepreason.bridge.compose import CompositionRequestV1
from deepreason.bridge.ledger import (
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV3,
)
from deepreason.bridge.events import BridgeAction
from deepreason.bridge.harness import BRIDGE_RESULT_NAME, _HarnessBridgeSink
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.bridge.transactional_adapter import (
    BridgeRecoveryError,
    TransactionalBridgeAdapter,
)
from deepreason.bridge.workflow import (
    BridgePersistenceBatch,
    BridgeWorkflow,
    BridgeWorkflowPolicy,
)
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import EndpointError, MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.repair import SchemaRepairError
from deepreason.llm.wire import AliasTable, WireContract
from deepreason.ontology import Problem, ProblemProvenance, Provenance
from deepreason.ontology.event import LLMCall
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    SchoolExecutionPolicyV1,
    ScratchAuthoringPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction import ContextNamespace, WorkBudgetDenied
from deepreason.workflow.transaction_service import InquiryTransactionService


STAMP = "2026-07-17T00:00:00Z"


class _Output(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    value: str


def _route(role: str) -> dict:
    return {
        "endpoint_id": f"{role}-route",
        "endpoint": f"mock://{role}",
        "model": f"offline-{role}",
        "provider": "mock",
        "family": f"offline-{role}",
        "max_tokens": 64,
    }


def _manifest(
    *,
    workflow_retry: WorkflowRetryPolicyV1 | None = None,
    run_input_digest: str = "f" * 64,
):
    control = ControlPlanePolicyV3(
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
        workflow_retry=(
            workflow_retry if workflow_retry is not None else WorkflowRetryPolicyV1()
        ),
        contract_versions=ContractVersionPolicyV3(),
        scratch_authoring=ScratchAuthoringPolicyV1(),
    )
    return compile_run_manifest(
        Config(
            N_SCHOOLS=0,
            roles={
                role: [_route(role)]
                for role in ("conjecturer", "summarizer", "thesis", "judge")
            },
            bridge={
                "mode": "grounded_two_stage",
                "grounding_review": True,
                "max_schema_repair_attempts": 0,
                "max_grounding_repair_attempts": 2,
            },
        ),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
        run_input_digest=run_input_digest,
    )


def _adapter(harness, manifest, *, budget: int, calls=None):
    calls = calls or {
        "summarizer": 1,
        "thesis": 1,
        "judge": 2,
    }
    endpoints = {}
    for role, count in calls.items():
        route = manifest.roles[role][0]
        endpoints[role] = MockEndpoint(
            ['{"value":"ok"}'] * count,
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )
    base = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(budget),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    return TransactionalBridgeAdapter(base, harness, manifest), endpoints


def _ledger_contract():
    return WireContract(
        "bridge.ledger.v3",
        _Output,
        _Output,
        aliases=AliasTable(
            {
                "SRC_1": "source-record",
                "SCR_1": "sha256:" + "a" * 64,
            }
        ),
    )


def test_v6_bridge_policy_selects_frozen_v3_v2_contract_pair():
    policy = _compiled_bridge_workflow_policy(_manifest())

    assert policy.ledger_contract_version == "v3"
    assert policy.composition_contract_version == "v2"


def test_every_v6_bridge_call_has_an_independent_complete_transaction(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "bridge-transactions")
    adapter, _endpoints = _adapter(harness, manifest, budget=100_000)
    calls = (
        (
            "summarizer",
            "bridge_ledger",
            _ledger_contract(),
        ),
        (
            "thesis",
            "bridge_compose",
            WireContract("bridge.composition.v2", _Output, _Output),
        ),
        (
            "judge",
            "bridge_review",
            WireContract("grounding-review.direct.v1", _Output, _Output),
        ),
        (
            "judge",
            "bridge_grounding_repair",
            WireContract("grounding-repair.direct.v1", _Output, _Output),
        ),
    )

    receipts = []
    for role, template_role, contract in calls:
        output, receipt = adapter.call(
            role,
            "SRC_1 exact source context\nSCR_1 imaginative scratch context",
            _Output,
            template_role=template_role,
            wire_contract=contract,
        )
        assert output.value == "ok"
        receipts.append(receipt)

    work = tuple(harness.workflow_state.transaction_work.values())
    assert len(work) == 4
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.BRIDGE_LEDGER,
        WorkflowTaskKind.BRIDGE_COMPOSITION,
        WorkflowTaskKind.BRIDGE_REVIEW,
        WorkflowTaskKind.REPAIR,
    ]
    assert len({item.preparation.id for item in work}) == 4
    for item in work:
        assert item.issued
        assert item.exposure is not None
        assert item.reservation is not None
        assert item.authorization is not None
        assert item.provider_attempts[0].outcome == "provider_result"
        assert item.admissions[0].outcome == "admitted"
        assert item.terminal is not None
        assert item.terminal.status == "completed"

    exposed = work[0].exposure.exposed_items
    assert {(item.namespace, item.alias) for item in exposed} == {
        (ContextNamespace.SOURCE, "SRC_001"),
        (ContextNamespace.SCRATCH, "SCR_001"),
    }
    persisted_calls = [event.llm for event in harness.log.read() if event.llm is not None]
    assert persisted_calls == receipts


def test_v6_bridge_budget_denial_has_no_exposure_or_dispatch(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "bridge-denied")
    adapter, endpoints = _adapter(
        harness,
        manifest,
        budget=1,
        calls={"summarizer": 1},
    )

    with pytest.raises(WorkBudgetDenied):
        adapter.call(
            "summarizer",
            "bounded bridge context",
            _Output,
            template_role="bridge_ledger",
            wire_contract=_ledger_contract(),
        )

    item = next(iter(harness.workflow_state.transaction_work.values()))
    assert not item.issued
    assert item.exposure is None
    assert item.reservation is None
    assert item.authorization is None
    assert item.provider_attempts == {}
    assert item.terminal is not None
    assert item.terminal.status == "budget_denied"
    assert endpoints["summarizer"].last_usage is None
    assert all(event.llm is None for event in harness.log.read())


def test_bridge_sink_does_not_append_transactional_call_twice(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "bridge-dedup")
    adapter, _endpoints = _adapter(
        harness,
        manifest,
        budget=100_000,
        calls={"summarizer": 1},
    )
    _output, transactional = adapter.call(
        "summarizer",
        "context",
        _Output,
        template_role="bridge_ledger",
        wire_contract=_ledger_contract(),
    )

    captured = SimpleNamespace(kwargs=None)

    def record_bridge_event(_action, **kwargs):
        captured.kwargs = kwargs

    sink = object.__new__(_HarnessBridgeSink)
    sink.harness = SimpleNamespace(record_bridge_event=record_bridge_event)
    sink._pack_written = True
    sink.failure = None
    sink.persist_bridge_batch(
        BridgePersistenceBatch(
            action=BridgeAction.GROUNDED_REVIEW_ATTEMPTED,
            llm=transactional,
        )
    )
    assert captured.kwargs["llm"] is None

    legacy = LLMCall(
        role="summarizer",
        model="legacy-model",
        endpoint="mock://legacy",
        prompt_ref=harness.blobs.put(b"legacy prompt"),
        raw_ref=harness.blobs.put(b'{"value":"legacy"}'),
        tokens=2,
    )
    sink.persist_bridge_batch(
        BridgePersistenceBatch(
            action=BridgeAction.GROUNDED_REVIEW_ATTEMPTED,
            llm=legacy,
        )
    )
    assert captured.kwargs["llm"] == legacy



def test_real_v3_v2_bridge_workflow_uses_only_transactional_calls(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "real-bridge-workflow")
    responses = {
        "summarizer": [
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "CLM_1",
                            "claim_class": "source_fact",
                            "claim": "The recorded value is seven.",
                            "source_handles": ["SRC_1"],
                        }
                    ]
                }
            )
        ],
        "thesis": [
            json.dumps(
                {
                    "sections": [
                        {
                            "span_id": "S1",
                            "text": "The value is seven.",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    "resolution": "answered",
                }
            )
        ],
        "judge": [
            json.dumps(
                {
                    "finding": "unsupported",
                    "message": "The supplied passage does not ground the span.",
                }
            ),
            json.dumps({"action": "remove_span"}),
        ],
    }
    endpoints = {}
    for role, scripted in responses.items():
        route = manifest.roles[role][0]
        endpoints[role] = MockEndpoint(
            scripted,
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )
    base = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    adapter = TransactionalBridgeAdapter(base, harness, manifest)
    catalog = ClaimLedgerInputCatalogV3.create(
        problem_ref="problem",
        formal_seq=0,
        problem_text="What conclusion is justified?",
        output_target="answer",
        items=[
            ClaimLedgerCatalogItemV1(
                handle="source",
                kind="source",
                ref="source-record",
                excerpt="The bounded source records a value of seven.",
            )
        ],
    )
    request = CompositionRequestV1(
        output_target="answer",
        formatting_profile="plain",
        desired_length_chars=4_096,
        maximum_sections=8,
    )

    result = BridgeWorkflow(
        adapter,
        adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
        policy=BridgeWorkflowPolicy(
            grounding_review=True,
            max_grounding_repair_attempts=2,
            ledger_contract_version="v3",
            composition_contract_version="v2",
        ),
    ).run(
        catalog,
        request,
        materials={"source-record": "A passage that supplies no numeric value."},
    )

    assert result.successful
    assert result.bridge_output.sections == []
    assert result.model_call_count == 4
    work = tuple(harness.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.BRIDGE_LEDGER,
        WorkflowTaskKind.BRIDGE_COMPOSITION,
        WorkflowTaskKind.BRIDGE_REVIEW,
        WorkflowTaskKind.REPAIR,
    ]
    assert len({item.preparation.id for item in work}) == 4
    assert all(item.terminal.status == "completed" for item in work)
    assert len([event for event in harness.log.read() if event.llm is not None]) == 4



def _summarizer_adapter(harness, manifest, endpoint):
    return TransactionalBridgeAdapter(
        LLMAdapter(
            {"summarizer": endpoint},
            harness.blobs,
            retry_max=0,
            meter=TokenMeter(100_000),
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
        ),
        harness,
        manifest,
    )


def test_v6_bridge_schema_failure_is_durably_terminalized(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "bridge-schema-failure")
    route = manifest.roles["summarizer"][0]
    endpoint = MockEndpoint(
        ["{not-json"],
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = _summarizer_adapter(harness, manifest, endpoint)

    with pytest.raises(SchemaRepairError) as caught:
        adapter.call(
            "summarizer",
            "bounded bridge context",
            _Output,
            template_role="bridge_ledger",
            wire_contract=_ledger_contract(),
        )

    item = next(iter(harness.workflow_state.transaction_work.values()))
    assert item.provider_attempts[0].outcome == "provider_result"
    assert item.admissions[0].outcome == "schema_exhausted"
    assert item.terminal is not None
    assert item.terminal.status == "schema_exhausted"
    assert caught.value.spend is not None
    assert len([event for event in harness.log.read() if event.llm is not None]) == 1


def test_v6_bridge_transport_failure_is_durably_terminalized(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "bridge-transport-failure")
    route = manifest.roles["summarizer"][0]

    def fail(_prompt):
        raise EndpointError("offline transport failure")

    endpoint = MockEndpoint(
        fail,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = _summarizer_adapter(harness, manifest, endpoint)

    with pytest.raises(EndpointError) as caught:
        adapter.call(
            "summarizer",
            "bounded bridge context",
            _Output,
            template_role="bridge_ledger",
            wire_contract=_ledger_contract(),
        )

    item = next(iter(harness.workflow_state.transaction_work.values()))
    assert item.provider_attempts[0].outcome == "transport_failure"
    assert item.provider_attempts[0].usage_status == "unknown"
    assert item.admissions == {}
    assert item.terminal is not None
    assert item.terminal.status == "transport_failed"
    assert item.terminal.usage_status == "unknown"
    assert caught.value.spend is not None
    assert adapter.meter.reserved == 0
    assert len([event for event in harness.log.read() if event.llm is not None]) == 1



class _InjectedBridgeAdmissionCrash(BaseException):
    pass


def _recovery_responses():
    return (
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
                    "resolution_reason": "The record supports a conjecture, not a fact.",
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


def _recovery_policy():
    return BridgeWorkflowPolicy(
        grounding_review=True,
        max_grounding_repair_attempts=2,
        ledger_contract_version="v3",
        composition_contract_version="v2",
    )


def _recovery_adapter(harness, manifest, responses, dispatches):
    queued = {role: [] for role in ("summarizer", "thesis", "judge")}
    for role, response in responses:
        queued[role].append(response)
    endpoints = {}
    for role, values in queued.items():
        route = manifest.roles[role][0]

        def dispatch(_prompt, *, role=role, values=values):
            dispatches.append(role)
            if not values:
                raise AssertionError(f"recovery dispatched already-stored {role} work")
            return values.pop(0)

        endpoints[role] = MockEndpoint(
            dispatch,
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )
    base = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    return TransactionalBridgeAdapter(base, harness, manifest)


def _bind_recovery_manifest(root, workflow_retry):
    problem_id = "problem-bridge-recovery"
    description = "Which surviving idea should be presented?"
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="offline bridge-recovery fixture",
            acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(id=problem_id, description=description),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    manifest = _manifest(
        workflow_retry=workflow_retry,
        run_input_digest=run_input.run_input_digest,
    )
    bind_run_manifest(manifest, root)
    return manifest


def _seed_recovery_problem(harness):
    problem_id = "problem-bridge-recovery"
    harness.register_problem(
        Problem(
            id=problem_id,
            description="Which surviving idea should be presented?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    harness.create_artifact(
        "A genuinely novel surviving conjecture.",
        provenance=Provenance(role="conjecturer"),
        problem_id=problem_id,
    )
    return problem_id


def _run_recovery_bridge(harness, manifest, problem_id, adapter, *, policy=None):
    return harness.build_bridge(
        problem_id,
        "answer",
        _recovery_policy() if policy is None else policy,
        run_manifest_digest=manifest.sha256,
        stage_a_adapter=adapter,
        composition_adapter=adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
    )


@pytest.mark.parametrize("crash_ordinal", range(4))
def test_v6_bridge_restart_replays_saved_provider_result_without_redispatch(
    tmp_path, monkeypatch, crash_ordinal
):
    manifest = _manifest()
    root = tmp_path / f"bridge-restart-{crash_ordinal}"
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    initial_dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _recovery_responses(),
        initial_dispatches,
    )
    original_admission = InquiryTransactionService.record_semantic_admission
    admissions = 0

    def crash_after_provider_result(self, provider_attempt, **kwargs):
        nonlocal admissions
        if admissions == crash_ordinal:
            admissions += 1
            raise _InjectedBridgeAdmissionCrash()
        admissions += 1
        return original_admission(self, provider_attempt, **kwargs)

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_provider_result,
    )
    with pytest.raises(_InjectedBridgeAdmissionCrash):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admission,
    )

    work = tuple(harness.workflow_state.transaction_work.values())
    pending = work[crash_ordinal]
    assert len(work) == crash_ordinal + 1
    assert pending.provider_attempts[pending.preparation.attempt_index].outcome == "provider_result"
    assert pending.admissions == {}
    assert pending.terminal is None
    frozen_fence = pending.preparation.formal_fence_seq

    reopened = Harness(root)
    recovery_dispatches = []
    remaining = _recovery_responses()[crash_ordinal + 1 :]
    recovered_adapter = _recovery_adapter(
        reopened,
        manifest,
        remaining,
        recovery_dispatches,
    )
    terminal = _run_recovery_bridge(reopened, manifest, problem_id, recovered_adapter)

    assert terminal.process_status == "success"
    assert terminal.formal_seq == frozen_fence
    assert recovery_dispatches == [role for role, _response in remaining]
    recovered_work = tuple(reopened.workflow_state.transaction_work.values())
    assert len(recovered_work) == 4
    assert all(item.terminal is not None for item in recovered_work)
    assert all(item.terminal.status == "completed" for item in recovered_work)
    assert all(item.preparation.formal_fence_seq == frozen_fence for item in recovered_work)
    bridge_events = [event for event in reopened.log.read() if event.bridge is not None]
    signatures = [
        (
            event.bridge.action,
            tuple(event.inputs),
            tuple(event.outputs),
            event.bridge.finding_ref,
            event.bridge.error_code,
        )
        for event in bridge_events
    ]
    assert len(signatures) == len(set(signatures))

    if crash_ordinal == 0:
        log_before = tuple(reopened.log.read())
        bridge_state_before = deepcopy(reopened.bridge_state)
        result_before = (root / BRIDGE_RESULT_NAME).read_bytes()
        again = Harness(root)
        idempotent_dispatches = []
        idempotent_adapter = _recovery_adapter(
            again,
            manifest,
            (),
            idempotent_dispatches,
        )
        repeat = _run_recovery_bridge(again, manifest, problem_id, idempotent_adapter)
        assert repeat == terminal
        assert idempotent_dispatches == []
        assert tuple(again.log.read()) == log_before
        assert again.bridge_state == bridge_state_before
        assert (root / BRIDGE_RESULT_NAME).read_bytes() == result_before

def test_v6_bridge_restart_corrupt_saved_result_fails_closed_without_redispatch(
    tmp_path, monkeypatch
):
    manifest = _manifest()
    root = tmp_path / "bridge-restart-corrupt"
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    initial_dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _recovery_responses(),
        initial_dispatches,
    )
    corrupt_raw_ref = harness.blobs.put(b"{not-json")
    original_provider = InquiryTransactionService.record_provider_attempt
    original_admission = InquiryTransactionService.record_semantic_admission

    def corrupt_provider_result(self, authorized, *, call, **kwargs):
        if kwargs["outcome"] == "provider_result":
            call = call.model_copy(update={"raw_ref": corrupt_raw_ref})
        return original_provider(self, authorized, call=call, **kwargs)

    def crash_after_provider_result(self, provider_attempt, **kwargs):
        raise _InjectedBridgeAdmissionCrash()

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_provider_attempt",
        corrupt_provider_result,
    )
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_provider_result,
    )
    with pytest.raises(_InjectedBridgeAdmissionCrash):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_provider_attempt",
        original_provider,
    )
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admission,
    )

    reopened = Harness(root)
    recovery_dispatches = []
    recovered_adapter = _recovery_adapter(
        reopened,
        manifest,
        (),
        recovery_dispatches,
    )
    terminal = _run_recovery_bridge(reopened, manifest, problem_id, recovered_adapter)

    assert terminal.process_status == "failure"
    assert terminal.error_code == "BRIDGE_RECOVERY_SCHEMA_EXHAUSTED"
    assert recovery_dispatches == []
    item = next(iter(reopened.workflow_state.transaction_work.values()))
    assert item.admissions[item.preparation.attempt_index].outcome == "schema_exhausted"
    assert item.terminal is not None
    assert item.terminal.status == "schema_exhausted"
    assert all(
        event.bridge is None or event.bridge.action != BridgeAction.COMPLETED
        for event in reopened.log.read()
    )


def test_v6_bridge_restart_missing_provider_receipt_terminalizes_without_redispatch(
    tmp_path, monkeypatch
):
    manifest = _manifest()
    root = tmp_path / "bridge-restart-missing-receipt"
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    adapter = _recovery_adapter(harness, manifest, _recovery_responses(), [])
    original_admission = InquiryTransactionService.record_semantic_admission

    def crash_after_provider_result(self, provider_attempt, **kwargs):
        raise _InjectedBridgeAdmissionCrash()

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_provider_result,
    )
    with pytest.raises(_InjectedBridgeAdmissionCrash):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admission,
    )

    reopened = Harness(root)
    recovery_dispatches = []
    recovered_adapter = _recovery_adapter(
        reopened, manifest, (), recovery_dispatches
    )

    def missing_provider_receipt(*_args, **_kwargs):
        raise BridgeRecoveryError(
            "BRIDGE_RECOVERY_PROVIDER_RECEIPT_MISSING",
            "offline fixture omits the canonical provider receipt",
        )

    monkeypatch.setattr(
        recovered_adapter, "_stored_provider_call", missing_provider_receipt
    )
    terminal = _run_recovery_bridge(reopened, manifest, problem_id, recovered_adapter)

    assert terminal.process_status == "failure"
    assert terminal.error_code == "BRIDGE_RECOVERY_PROVIDER_RECEIPT_MISSING"
    assert recovery_dispatches == []
    item = next(iter(reopened.workflow_state.transaction_work.values()))
    assert item.admissions[item.preparation.attempt_index].outcome == "rejected"
    assert item.terminal is not None
    assert item.terminal.status == "rejected"
    assert item.terminal.reason_code == "bridge_recovery_provider_receipt_invalid"


def test_v6_bridge_restart_invalid_provider_result_terminalizes_without_redispatch(
    tmp_path, monkeypatch
):
    manifest = _manifest()
    root = tmp_path / "bridge-restart-invalid-provider-result"
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    adapter = _recovery_adapter(harness, manifest, _recovery_responses(), [])
    original_admission = InquiryTransactionService.record_semantic_admission

    def crash_after_provider_result(self, provider_attempt, **kwargs):
        raise _InjectedBridgeAdmissionCrash()

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_provider_result,
    )
    with pytest.raises(_InjectedBridgeAdmissionCrash):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admission,
    )

    reopened = Harness(root)
    item = next(iter(reopened.workflow_state.transaction_work.values()))
    provider = item.provider_attempts[item.preparation.attempt_index]
    item.provider_attempts[item.preparation.attempt_index] = SimpleNamespace(
        id=provider.id,
        work_id=provider.work_id,
        attempt_index=provider.attempt_index,
        outcome="invalid",
        raw_ref=None,
        usage_status=provider.usage_status,
        prompt_tokens=provider.prompt_tokens,
        completion_tokens=provider.completion_tokens,
    )
    recovery_dispatches = []
    recovered_adapter = _recovery_adapter(
        reopened, manifest, (), recovery_dispatches
    )
    terminal = _run_recovery_bridge(reopened, manifest, problem_id, recovered_adapter)

    assert terminal.process_status == "failure"
    assert terminal.error_code == "BRIDGE_RECOVERY_PROVIDER_RESULT_INVALID"
    assert recovery_dispatches == []
    assert item.admissions[item.preparation.attempt_index].outcome == "rejected"
    assert item.terminal is not None
    assert item.terminal.status == "rejected"
    assert item.terminal.reason_code == "bridge_recovery_provider_result_invalid"


def _append_unmatched_completed_work(harness, manifest, pending, *, ordinal):
    extra_adapter, endpoints = _adapter(
        harness,
        manifest,
        budget=100_000,
        calls={"summarizer": 1},
    )
    payload = pending.preparation.task_payload_value
    extra_adapter.bind_bridge_execution(
        execution_id=payload["execution_id"],
        execution_snapshot_ref=payload["execution_snapshot_ref"],
        formal_fence_seq=pending.preparation.formal_fence_seq,
        recovery=False,
    )
    extra_adapter._ordinal = ordinal
    output, _call = extra_adapter.call(
        "summarizer",
        "extra completed work",
        _Output,
        template_role="bridge_ledger",
        wire_contract=_ledger_contract(),
    )
    assert output.value == "ok"
    assert endpoints["summarizer"].last_usage is not None


def test_v6_bridge_restart_rejects_completed_work_outside_recovery_prefix(
    tmp_path, monkeypatch
):
    manifest = _manifest()
    root = tmp_path / "bridge-restart-extra-prefix-work"
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    adapter = _recovery_adapter(harness, manifest, _recovery_responses(), [])
    original_admission = InquiryTransactionService.record_semantic_admission

    def crash_after_provider_result(self, provider_attempt, **kwargs):
        raise _InjectedBridgeAdmissionCrash()

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_provider_result,
    )
    with pytest.raises(_InjectedBridgeAdmissionCrash):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admission,
    )
    pending = next(iter(harness.workflow_state.transaction_work.values()))
    _append_unmatched_completed_work(harness, manifest, pending, ordinal=2)

    reopened = Harness(root)
    recovery_dispatches = []
    recovered_adapter = _recovery_adapter(
        reopened, manifest, (), recovery_dispatches
    )
    terminal = _run_recovery_bridge(reopened, manifest, problem_id, recovered_adapter)

    assert terminal.process_status == "failure"
    assert terminal.error_code == "BRIDGE_RECOVERY_SEQUENCE_MISMATCH"
    assert recovery_dispatches == []
    assert len(reopened.workflow_state.transaction_work) == 2
    assert all(
        event.bridge is None or event.bridge.action != BridgeAction.COMPLETED
        for event in reopened.log.read()
    )


def test_v6_bridge_restart_rejects_unconsumed_completed_work_before_completion(
    tmp_path, monkeypatch
):
    manifest = _manifest()
    root = tmp_path / "bridge-restart-extra-completed-work"
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    adapter = _recovery_adapter(harness, manifest, _recovery_responses(), [])
    original_admission = InquiryTransactionService.record_semantic_admission
    calls = 0

    def crash_after_fourth_provider_result(self, provider_attempt, **kwargs):
        nonlocal calls
        if calls == 3:
            raise _InjectedBridgeAdmissionCrash()
        calls += 1
        return original_admission(self, provider_attempt, **kwargs)

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_fourth_provider_result,
    )
    with pytest.raises(_InjectedBridgeAdmissionCrash):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admission,
    )
    pending = tuple(harness.workflow_state.transaction_work.values())[-1]
    _append_unmatched_completed_work(harness, manifest, pending, ordinal=4)

    reopened = Harness(root)
    recovery_dispatches = []
    recovered_adapter = _recovery_adapter(
        reopened, manifest, (), recovery_dispatches
    )
    with pytest.raises(BridgeRecoveryError) as error:
        _run_recovery_bridge(reopened, manifest, problem_id, recovered_adapter)

    assert error.value.code == "BRIDGE_RECOVERY_SEQUENCE_MISMATCH"
    assert recovery_dispatches == []
    assert all(
        event.bridge is None or event.bridge.action != BridgeAction.COMPLETED
        for event in reopened.log.read()
    )


def test_v6_bridge_restart_deduplicates_exact_retry_receipt(tmp_path, monkeypatch):
    retry_policy = WorkflowRetryPolicyV1(
        max_workflow_retries=1,
        retryable_error_codes=("BRIDGE_LEDGER_REPAIR_EXHAUSTED",),
    )
    root = tmp_path / "bridge-restart-retry-receipt"
    manifest = _bind_recovery_manifest(root, retry_policy)
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    initial_dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        (
            (
                "summarizer",
                json.dumps(
                    {
                        "entries": [
                            {
                                "entry_key": "CLM_1",
                                "claim_class": "source_fact",
                                "claim": "Unsupported source claim.",
                                "source_handles": ["SRC_99"],
                            }
                        ]
                    }
                ),
            ),
            *_recovery_responses(),
        ),
        initial_dispatches,
    )
    original_admission = InquiryTransactionService.record_semantic_admission

    def crash_after_retry_receipt(self, provider_attempt, **kwargs):
        item = self.harness.workflow_state.transaction_work[provider_attempt.work_id]
        if item.preparation.task_payload_value.get("ordinal") == 1:
            raise _InjectedBridgeAdmissionCrash()
        return original_admission(self, provider_attempt, **kwargs)

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_retry_receipt,
    )
    caller_policy = manifest.bridge_policy.workflow_policy(ledger_contract_version="v1")
    with pytest.raises(_InjectedBridgeAdmissionCrash):
        _run_recovery_bridge(
            harness,
            manifest,
            problem_id,
            adapter,
            policy=caller_policy,
        )
    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admission,
    )

    reopened = Harness(root)
    recovery_dispatches = []
    recovered_adapter = _recovery_adapter(
        reopened,
        manifest,
        _recovery_responses()[1:],
        recovery_dispatches,
    )
    terminal = _run_recovery_bridge(
        reopened,
        manifest,
        problem_id,
        recovered_adapter,
        policy=caller_policy,
    )

    retry_events = [
        event
        for event in reopened.log.read()
        if event.bridge is not None
        and event.bridge.action == BridgeAction.WORKFLOW_RETRY_STARTED
    ]
    assert terminal.process_status == "success"
    assert recovery_dispatches == ["thesis", "judge", "judge"]
    assert len(retry_events) == 1
    assert len(reopened.bridge_state.workflow_retries) == 1
    retry = next(iter(reopened.bridge_state.workflow_retries.values()))
    retry_event = retry_events[0]
    provider_tokens_before_retry = sum(
        event.llm.tokens
        for event in reopened.log.read()
        if event.seq < retry_event.seq
        and event.control is not None
        and event.control.action == "provider_result"
        and event.llm is not None
    )
    assert retry.prior_token_count == provider_tokens_before_retry
    assert reopened.bridge_state.cumulative_tokens_by_failure[retry.prior_failure_id] == (
        provider_tokens_before_retry
    )
    assert sum(
        call.tokens
        for call in reopened.bridge_state.calls_by_failure[retry.prior_failure_id]
    ) == provider_tokens_before_retry

    replayed = Harness(root)
    replayed_retry = next(iter(replayed.bridge_state.workflow_retries.values()))
    assert replayed_retry.prior_token_count == provider_tokens_before_retry
    assert replayed.bridge_state.cumulative_tokens_by_failure[
        replayed_retry.prior_failure_id
    ] == provider_tokens_before_retry
    assert sum(
        call.tokens
        for call in replayed.bridge_state.calls_by_failure[replayed_retry.prior_failure_id]
    ) == provider_tokens_before_retry


def test_v6_bridge_restart_missing_snapshot_fails_before_dispatch(tmp_path):
    manifest = _manifest()
    root = tmp_path / "bridge-restart-missing-snapshot"
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    dispatches = []
    adapter = _recovery_adapter(harness, manifest, (), dispatches)
    route = manifest.roles["summarizer"][0]
    fence = harness._next_seq - 1
    service = InquiryTransactionService(harness, manifest, adapter.meter)
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.BRIDGE_LEDGER,
        attempt_index=0,
        route_lease=RouteLeaseRefV1(
            role="summarizer",
            seat=0,
            endpoint_id=route.endpoint_id,
            route_sha256=route_fingerprint(route),
        ),
        contract_id="bridge.ledger.v3",
        trigger_ref="bridge:legacy-pending-work",
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
        task_payload_value={"schema": "bridge.transaction-task.v1"},
    )

    with pytest.raises(ValueError, match="BRIDGE_RECOVERY_SNAPSHOT_MISSING"):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)

    item = harness.workflow_state.transaction_work[preparation.id]
    assert not item.issued
    assert item.provider_attempts == {}
    assert dispatches == []
    assert not (root / BRIDGE_RESULT_NAME).exists()
    assert all(event.bridge is None for event in harness.log.read())