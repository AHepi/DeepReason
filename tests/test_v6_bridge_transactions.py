"""Offline qualification for transactional RunManifest-v6 bridge calls."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json

import pytest
from pydantic import BaseModel, ConfigDict, model_validator

import deepreason.application.bridge as bridge_application
from deepreason.application.bridge import (
    GroundedBridgeApplicationService,
    GroundedBridgeBuildIntentV1,
    GroundedBridgeWorkerRegistry,
    _historical_bridge_caller_policy,
    status_payload,
)
from deepreason.application.text_runs import _v6_run_result
from deepreason.canonical import canonical_json
from deepreason.bridge.compose import CompositionRequestV1
from deepreason.bridge.repair import GroundingRepairWireV1
from deepreason.bridge.review import GroundingVerdictWireV1
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
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    ProductionContractDoctorReportV1,
    ProductionContractDoctorSummaryV1,
    ProductionContractPairReportV1,
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
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import EndpointError, MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.repair import SchemaRepairError
from deepreason.llm.wire import AliasTable, DirectWireContract, WireContract
from deepreason.ontology import Problem, ProblemProvenance, Provenance
from deepreason.ontology.event import LLMCall
from deepreason.run_manifest import (
    MANIFEST_NAME,
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    RunManifest,
    RunManifestError,
    SchoolExecutionPolicyV1,
    ScratchAuthoringPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
    write_run_manifest,
)
from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record
from deepreason.runtime.terminal_authority import derive_terminal_authority
from deepreason.verification.report import verify_root_report
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction import ContextNamespace, WorkBudgetDenied
from deepreason.workflow.transaction_service import InquiryTransactionService


STAMP = "2026-07-17T00:00:00Z"


def _default_bound_input():
    problem_id = "problem-bridge-transaction"
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="offline bridge-transaction fixture",
            acquisition_method="pre-freeze construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id=problem_id,
            description="Exercise one offline transactional bridge.",
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    return run_input, dossier


class _Output(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    value: str


class _RootInvalidOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    value: str

    @model_validator(mode="after")
    def _always_invalid(self):
        raise ValueError("whole-object diagnostic")


def _route(role: str, *, model_profile: str | None = None) -> dict:
    route = {
        "endpoint_id": f"{role}-route",
        "endpoint": f"mock://{role}",
        "model": f"offline-{role}",
        "provider": "mock",
        "family": f"offline-{role}",
        "max_tokens": 64,
        "context_window_tokens": 262_144,
    }
    if model_profile is not None:
        route["model_profile"] = model_profile
    return route


def _manifest(
    *,
    workflow_retry: WorkflowRetryPolicyV1 | None = None,
    run_input_digest: str | None = None,
    route_profiles: dict[str, str] | None = None,
):
    route_profiles = route_profiles or {}
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
    if run_input_digest is None:
        run_input_digest = _default_bound_input()[0].run_input_digest
    return compile_run_manifest(
        Config(
            N_SCHOOLS=0,
            roles={
                role: [
                    _route(role, model_profile=route_profiles.get(role))
                ]
                for role in (
                    "conjecturer",
                    "argumentative_critic",
                    "summarizer",
                    "thesis",
                    "judge",
                )
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


def _admitted_qualification_case(_manifest, _pair, case_index):
    return ProductionContractCaseResultV1(
        case_id=f"case-{case_index + 1:03d}",
        first_pass_valid=True,
        eventual_valid=True,
        repair_count=0,
        semantic_admission=True,
    )


def _qualification_report(manifest):
    return run_production_contract_doctor(
        manifest,
        case_executor=_admitted_qualification_case,
    )


def _qualification_summary(pairs):
    return ProductionContractDoctorSummaryV1(
        pair_count=len(pairs),
        case_count=sum(len(item.cases) for item in pairs),
        first_pass_valid_count=sum(
            item.first_pass_valid_count for item in pairs
        ),
        eventual_valid_count=sum(item.eventual_valid_count for item in pairs),
        repair_count=sum(item.repair_count for item in pairs),
        alias_failures=sum(item.alias_failures for item in pairs),
        scope_violations=sum(item.scope_violations for item in pairs),
        semantic_admission_count=sum(
            item.semantic_admission_count for item in pairs
        ),
        qualified_pair_count=sum(item.qualified for item in pairs),
        qualified=all(item.qualified for item in pairs),
    )


def _qualification_report_with_pairs(report, pairs):
    pairs = tuple(pairs)
    return ProductionContractDoctorReportV1(
        run_manifest_sha256=report.run_manifest_sha256,
        pairs=pairs,
        summary=_qualification_summary(pairs),
    )


def _qualification_pair_with_cases(pair_report, cases):
    cases = tuple(cases)
    eventual = sum(item.eventual_valid for item in cases)
    admissions = sum(item.semantic_admission for item in cases)
    aliases = sum(item.alias_failures for item in cases)
    scopes = sum(item.scope_violations for item in cases)
    return ProductionContractPairReportV1(
        pair=pair_report.pair,
        cases=cases,
        first_pass_valid_count=sum(item.first_pass_valid for item in cases),
        eventual_valid_count=eventual,
        repair_count=sum(item.repair_count for item in cases),
        alias_failures=aliases,
        scope_violations=scopes,
        semantic_admission_count=admissions,
        qualified=bool(
            eventual >= 19
            and aliases == 0
            and scopes == 0
            and admissions == eventual
        ),
    )


def _root_bytes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _write_bridge_qualification(harness, manifest, *, report=None):
    policy = manifest.production_qualification_policy
    assert policy is not None
    target = harness.root / policy.report_filename
    try:
        target.lstat()
    except FileNotFoundError:
        write_production_contract_report(
            _qualification_report(manifest) if report is None else report,
            target,
        )
    return target


def _write_eligible_v6_run_result(root, manifest):
    harness = Harness(root)
    if harness.workflow_state.route_seat_model_classification is None:
        harness.bind_model_classification(
            manifest,
            _qualification_report(manifest),
        )
    policy = StopPolicy()
    metrics = StopMetrics(cycle=0)
    event_horizon = harness._next_seq
    event = harness.record_measure(
        inputs=[
            "run-stop",
            policy.digest,
            json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
            "completed",
            str(event_horizon),
        ]
    )
    assert event.seq == event_horizon
    stop = write_stop_record(
        root,
        reason="completed",
        policy=policy,
        metrics=metrics,
        event_seq=event_horizon,
    )
    payload = _v6_run_result(
        Path(root),
        manifest,
        {
            "state": "completed",
            "workload": "text",
            "stop": stop,
        },
    )
    assert payload["canonical_bridge_eligible"] is True
    (Path(root) / "run-result.json").write_bytes(canonical_json(payload) + b"\n")


def _write_unclassified_eligible_v6_run_result(root, manifest):
    harness = Harness(root)
    assert harness.workflow_state.route_seat_model_classification is None
    policy = StopPolicy()
    metrics = StopMetrics(cycle=0)
    event_horizon = harness._next_seq
    event = harness.record_measure(
        inputs=[
            "run-stop",
            policy.digest,
            json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
            "completed",
            str(event_horizon),
        ]
    )
    assert event.seq == event_horizon
    stop = write_stop_record(
        root,
        reason="completed",
        policy=policy,
        metrics=metrics,
        event_seq=event_horizon,
    )
    payload = _v6_run_result(
        Path(root),
        manifest,
        {
            "state": "completed",
            "workload": "text",
            "stop": stop,
        },
    )
    assert payload["canonical_bridge_eligible"] is True
    (Path(root) / "run-result.json").write_bytes(canonical_json(payload) + b"\n")


def _write_ineligible_v6_run_result(root, manifest):
    harness = Harness(root)
    if harness.workflow_state.route_seat_model_classification is None:
        harness.bind_model_classification(
            manifest,
            _qualification_report(manifest),
        )
    policy = StopPolicy()
    metrics = StopMetrics(cycle=0)
    event_horizon = harness._next_seq
    event = harness.record_measure(
        inputs=[
            "run-stop",
            policy.digest,
            json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
            "operational_failure",
            str(event_horizon),
        ]
    )
    stop = write_stop_record(
        root,
        reason="operational_failure",
        policy=policy,
        metrics=metrics,
        event_seq=event.seq,
    )
    payload = _v6_run_result(
        Path(root),
        manifest,
        {
            "state": "failed",
            "workload": "text",
            "stop": stop,
        },
    )
    assert payload["canonical_bridge_eligible"] is False
    (Path(root) / "run-result.json").write_bytes(canonical_json(payload) + b"\n")


def _scripted_application_endpoint_factory(manifest, responses, dispatches):
    queued = {role: list(values) for role, values in responses.items()}
    routes = {
        route.endpoint_id: (role, route)
        for role, role_routes in manifest.roles.items()
        for route in role_routes
    }

    def build(spec):
        role, route = routes[spec["endpoint_id"]]
        values = queued.setdefault(role, [])

        def dispatch(_prompt):
            dispatches.append(role)
            if not values:
                raise AssertionError(f"application redispatched {role} without authority")
            return values.pop(0)

        return MockEndpoint(
            dispatch,
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )

    return build


def _qualified_transactional_adapter(base, harness, manifest):
    run_input_path = harness.root / "run-input.json"
    if not run_input_path.is_file():
        run_input, dossier = _default_bound_input()
        if manifest.run_input_digest != run_input.run_input_digest:
            raise AssertionError("custom bridge manifest requires its bound run input")
        bind_run_input(run_input, dossier, harness.root)
    manifest_path = harness.root / MANIFEST_NAME
    try:
        manifest_path.lstat()
    except FileNotFoundError:
        bind_run_manifest(manifest, harness.root)
    _write_bridge_qualification(harness, manifest)
    if not (harness.root / "run-result.json").is_file():
        _write_eligible_v6_run_result(harness.root, manifest)
        harness.reload_durable_authority()
    return TransactionalBridgeAdapter(base, harness, manifest)


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
    return _qualified_transactional_adapter(base, harness, manifest), endpoints


def _unbound_bridge_adapter(harness, manifest, *, budget=None):
    endpoint = MockEndpoint(
        ['{"value":"ok"}'],
        name=manifest.roles["summarizer"][0].base_url,
        model=manifest.roles["summarizer"][0].model_id,
        max_tokens=manifest.roles["summarizer"][0].max_tokens,
    )
    base = LLMAdapter(
        {"summarizer": endpoint},
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(budget),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    return base, endpoint


def _base_adapter_authority_snapshot(base):
    return {
        "transaction_authority_required": base.transaction_authority_required,
        "authority_harness": base._v6_authority_harness,
        "authority_manifest": base._v6_authority_manifest,
        "compact_recovery_roles": frozenset(base._compact_recovery_roles),
        "base_model_profile": base.base_model_profile,
        "model_profile": base.model_profile,
        "leases": base.leases,
        "meter": base.meter.snapshot(),
    }


def _unqualified_report(report):
    pair = report.pairs[0]
    cases = list(pair.cases)
    cases[0] = cases[0].model_copy(update={"alias_failures": 1})
    changed = _qualification_pair_with_cases(pair, cases)
    return _qualification_report_with_pairs(
        report,
        (changed, *report.pairs[1:]),
    )


def _repair_overclaim_report(report):
    pair_index = next(
        index
        for index, item in enumerate(report.pairs)
        if item.pair.contract_id == "bridge.ledger.v3"
    )
    pair = report.pairs[pair_index]
    cases = list(pair.cases)
    cases[0] = ProductionContractCaseResultV1(
        case_id="case-001",
        first_pass_valid=False,
        eventual_valid=True,
        repair_count=1,
        semantic_admission=True,
    )
    pairs = list(report.pairs)
    pairs[pair_index] = _qualification_pair_with_cases(pair, cases)
    return _qualification_report_with_pairs(report, pairs)


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


def _composition_contract():
    return WireContract("bridge.composition.v2", _Output, _Output)


def _with_contract_grant(
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


def test_v6_application_supplies_only_historical_bridge_caller_projection():
    policy = _historical_bridge_caller_policy(_manifest())

    assert policy.ledger_contract_version == "v1"
    assert policy.composition_contract_version == "v1"


def test_transactional_bridge_constructor_requires_durable_manifest_before_binding(
    tmp_path,
    monkeypatch,
):
    import deepreason.cli.doctor as doctor_module

    manifest = _manifest()
    root = tmp_path / "bridge-constructor-manifest-absent"
    harness = Harness(root)
    _write_bridge_qualification(harness, manifest)
    base, endpoint = _unbound_bridge_adapter(harness, manifest, budget=None)
    report_calls = []
    bind_calls = []
    original_bind = base.bind_v6_authority

    def forbidden_report(*_args, **_kwargs):
        report_calls.append(True)
        pytest.fail("missing durable manifest reached qualification inspection")

    def counted_bind(*args, **kwargs):
        bind_calls.append(True)
        return original_bind(*args, **kwargs)

    monkeypatch.setattr(
        doctor_module,
        "load_production_contract_report",
        forbidden_report,
    )
    monkeypatch.setattr(
        doctor_module,
        "validate_production_contract_qualification",
        forbidden_report,
    )
    monkeypatch.setattr(base, "bind_v6_authority", counted_bind)
    authority_before = _base_adapter_authority_snapshot(base)
    harness_manifest_before = getattr(harness, "_workflow_manifest", None)
    replay_manifest_before = getattr(harness.workflow_state, "_run_manifest", None)
    work_before = deepcopy(harness.workflow_state.transaction_work)
    bridge_before = deepcopy(harness.bridge_state)
    log_before = tuple(harness.log.read())
    next_seq_before = harness._next_seq
    root_before = _root_bytes(root)

    with pytest.raises(ValueError, match="^BRIDGE_MANIFEST_MISMATCH$"):
        TransactionalBridgeAdapter(base, harness, manifest)

    assert report_calls == []
    assert bind_calls == []
    assert _base_adapter_authority_snapshot(base) == authority_before
    assert getattr(harness, "_workflow_manifest", None) is harness_manifest_before
    assert (
        getattr(harness.workflow_state, "_run_manifest", None)
        is replay_manifest_before
    )
    assert harness.workflow_state.transaction_work == work_before
    assert harness.bridge_state == bridge_before
    assert tuple(harness.log.read()) == log_before
    assert harness._next_seq == next_seq_before
    assert endpoint.last_transport_attempts == 0
    assert _root_bytes(root) == root_before
    assert not (root / MANIFEST_NAME).exists()


def test_transactional_bridge_constructor_propagates_inaccessible_manifest(
    tmp_path,
    monkeypatch,
):
    import deepreason.cli.doctor as doctor_module

    manifest = _manifest()
    root = tmp_path / "bridge-constructor-manifest-inaccessible"
    write_run_manifest(manifest, root / MANIFEST_NAME)
    harness = Harness(root)
    _write_bridge_qualification(harness, manifest)
    base, endpoint = _unbound_bridge_adapter(harness, manifest, budget=None)
    manifest_path = root / MANIFEST_NAME
    report_calls = []
    bind_calls = []
    original_bind = base.bind_v6_authority
    original_lstat = Path.lstat

    def forbidden_report(*_args, **_kwargs):
        report_calls.append(True)
        pytest.fail("inaccessible durable manifest reached qualification inspection")

    def counted_bind(*args, **kwargs):
        bind_calls.append(True)
        return original_bind(*args, **kwargs)

    def inaccessible(path):
        if path == manifest_path:
            raise PermissionError("bridge constructor manifest inspection denied")
        return original_lstat(path)

    monkeypatch.setattr(
        doctor_module,
        "load_production_contract_report",
        forbidden_report,
    )
    monkeypatch.setattr(
        doctor_module,
        "validate_production_contract_qualification",
        forbidden_report,
    )
    monkeypatch.setattr(base, "bind_v6_authority", counted_bind)
    authority_before = _base_adapter_authority_snapshot(base)
    root_before = _root_bytes(root)

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "lstat", inaccessible)
        with pytest.raises(
            PermissionError,
            match="bridge constructor manifest inspection denied",
        ):
            TransactionalBridgeAdapter(base, harness, manifest)

    assert report_calls == []
    assert bind_calls == []
    assert _base_adapter_authority_snapshot(base) == authority_before
    assert endpoint.last_transport_attempts == 0
    assert _root_bytes(root) == root_before


@pytest.mark.parametrize(
    ("report_case", "expected_code"),
    (
        ("missing", "DOCTOR_REPORT_MISSING"),
        ("malformed", "DOCTOR_REPORT_INVALID"),
        ("noncanonical", "DOCTOR_REPORT_NONCANONICAL"),
        ("foreign-manifest", "DOCTOR_REPORT_MANIFEST_MISMATCH"),
        ("incomplete", "DOCTOR_REPORT_PAIR_INVENTORY_MISMATCH"),
        ("unqualified", "DOCTOR_REPORT_PAIR_UNQUALIFIED"),
        ("repair-overclaim", "DOCTOR_REPORT_REPAIR_GRANT_EXCEEDED"),
    ),
)
def test_standalone_transactional_bridge_requires_exact_qualification_before_binding(
    tmp_path,
    monkeypatch,
    report_case,
    expected_code,
):
    manifest = _manifest()
    root = tmp_path / f"bridge-qualification-{report_case}"
    write_run_manifest(manifest, root / MANIFEST_NAME)
    harness = Harness(root)
    report_path = root / manifest.production_qualification_policy.report_filename
    qualified = _qualification_report(manifest)
    if report_case == "malformed":
        report_path.write_bytes(b"{not-json}\n")
    elif report_case == "noncanonical":
        report_path.write_text(
            json.dumps(
                qualified.model_dump(mode="json", by_alias=True),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    elif report_case == "foreign-manifest":
        write_production_contract_report(
            _qualification_report(
                _manifest(route_profiles={"summarizer": "compact"})
            ),
            report_path,
        )
    elif report_case == "incomplete":
        write_production_contract_report(
            _qualification_report_with_pairs(qualified, qualified.pairs[:-1]),
            report_path,
        )
    elif report_case == "unqualified":
        write_production_contract_report(_unqualified_report(qualified), report_path)
    elif report_case == "repair-overclaim":
        write_production_contract_report(
            _repair_overclaim_report(qualified),
            report_path,
        )

    base, endpoint = _unbound_bridge_adapter(harness, manifest, budget=None)
    binding_calls = []

    def forbidden_binding(*_args, **_kwargs):
        binding_calls.append(True)
        pytest.fail("qualification denial reached adapter authority binding")

    monkeypatch.setattr(base, "bind_v6_authority", forbidden_binding)
    before = _root_bytes(root)

    with pytest.raises(RunManifestError) as caught:
        TransactionalBridgeAdapter(base, harness, manifest)

    assert caught.value.code == expected_code
    assert binding_calls == []
    assert base.transaction_authority_required is False
    assert base.meter.snapshot() == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total": 0,
        "budget": None,
        "calls": 0,
        "reserved": 0,
    }
    assert endpoint.last_transport_attempts == 0
    assert tuple(harness.log.read()) == ()
    assert harness.workflow_state.transaction_work == {}
    assert _root_bytes(root) == before


def test_standalone_bridge_manifest_conflict_precedes_report_inspection_and_binding(
    tmp_path,
    monkeypatch,
):
    bound_manifest = _manifest()
    explicit_manifest = _manifest(route_profiles={"summarizer": "compact"})
    root = tmp_path / "bridge-manifest-conflict"
    write_run_manifest(bound_manifest, root / MANIFEST_NAME)
    harness = Harness(root)
    _write_bridge_qualification(
        harness,
        explicit_manifest,
        report=_qualification_report(explicit_manifest),
    )
    base, endpoint = _unbound_bridge_adapter(
        harness,
        explicit_manifest,
        budget=None,
    )
    report_calls = []
    binding_calls = []

    def forbidden_report(*_args, **_kwargs):
        report_calls.append(True)
        pytest.fail("manifest conflict reached qualification inspection")

    def forbidden_binding(*_args, **_kwargs):
        binding_calls.append(True)
        pytest.fail("manifest conflict reached adapter authority binding")

    monkeypatch.setattr(
        "deepreason.cli.doctor.load_production_contract_report",
        forbidden_report,
    )
    monkeypatch.setattr(
        "deepreason.cli.doctor.validate_production_contract_qualification",
        forbidden_report,
    )
    monkeypatch.setattr(base, "bind_v6_authority", forbidden_binding)
    before = _root_bytes(root)

    with pytest.raises(RunManifestError) as caught:
        TransactionalBridgeAdapter(base, harness, explicit_manifest)

    assert caught.value.code == "RUN_MANIFEST_CONFLICT"
    assert report_calls == []
    assert binding_calls == []
    assert base.meter.calls == 0
    assert base.meter.reserved == 0
    assert endpoint.last_transport_attempts == 0
    assert tuple(harness.log.read()) == ()
    assert harness.workflow_state.transaction_work == {}
    assert _root_bytes(root) == before


def test_matching_root_and_explicit_bridge_manifest_uses_loaded_authority(tmp_path):
    manifest = _manifest()
    root = tmp_path / "bridge-manifest-match"
    run_input, dossier = _default_bound_input()
    bind_run_input(run_input, dossier, root)
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    _write_bridge_qualification(harness, manifest)
    _write_eligible_v6_run_result(root, manifest)
    harness.reload_durable_authority()
    base, _endpoint = _unbound_bridge_adapter(harness, manifest, budget=None)

    adapter = TransactionalBridgeAdapter(base, harness, manifest)

    assert adapter.manifest == manifest
    assert adapter.manifest is not manifest
    assert adapter.source_terminal_commitment_ref == (
        harness.workflow_state.current_terminal_commitment.id
    )
    assert base.meter.calls == 0


def test_ineligible_terminal_fails_before_transactional_adapter_binding(tmp_path):
    manifest = _manifest()
    root = tmp_path / "bridge-ineligible-terminal"
    run_input, dossier = _default_bound_input()
    bind_run_input(run_input, dossier, root)
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    _write_bridge_qualification(harness, manifest)
    _write_ineligible_v6_run_result(root, manifest)
    harness.reload_durable_authority()
    base, endpoint = _unbound_bridge_adapter(harness, manifest, budget=None)
    authority_before = _base_adapter_authority_snapshot(base)
    root_before = _root_bytes(root)

    with pytest.raises(ValueError, match="BRIDGE_TERMINAL_OUTCOME_INELIGIBLE"):
        TransactionalBridgeAdapter(base, harness, manifest)

    assert _base_adapter_authority_snapshot(base) == authority_before
    assert endpoint.last_transport_attempts == 0
    assert _root_bytes(root) == root_before


def test_unclassified_terminal_fails_before_transactional_adapter_binding(tmp_path):
    manifest = _manifest()
    root = tmp_path / "bridge-unclassified-terminal"
    run_input, dossier = _default_bound_input()
    bind_run_input(run_input, dossier, root)
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    _write_bridge_qualification(harness, manifest)
    _write_unclassified_eligible_v6_run_result(root, manifest)
    harness.reload_durable_authority()
    assert harness.workflow_state.route_seat_model_classification is None
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    assert verify_root_report(root).integrity_valid
    base, endpoint = _unbound_bridge_adapter(harness, manifest, budget=None)
    authority_before = _base_adapter_authority_snapshot(base)
    log_before = tuple(harness.log.read())
    root_before = _root_bytes(root)

    with pytest.raises(
        WorkflowAuthorizationError,
        match="BRIDGE_MODEL_CLASSIFICATION_REQUIRED",
    ):
        TransactionalBridgeAdapter(base, harness, manifest)

    assert harness.workflow_state.route_seat_model_classification is None
    assert tuple(harness.log.read()) == log_before
    assert _base_adapter_authority_snapshot(base) == authority_before
    assert endpoint.last_transport_attempts == 0
    assert _root_bytes(root) == root_before


def test_historical_v6_bridge_without_qualification_policy_fails_closed(tmp_path):
    payload = json.loads(_manifest().canonical_bytes())
    payload.pop("production_qualification_policy")
    historical = RunManifest.model_validate(payload)
    root = tmp_path / "bridge-historical-no-qualification-policy"
    write_run_manifest(historical, root / MANIFEST_NAME)
    harness = Harness(root)
    base, endpoint = _unbound_bridge_adapter(harness, historical, budget=None)
    before = _root_bytes(harness.root)

    with pytest.raises(RunManifestError) as caught:
        TransactionalBridgeAdapter(base, harness, historical)

    assert caught.value.code == "V6_PRODUCTION_QUALIFICATION_POLICY_REQUIRED"
    assert base.transaction_authority_required is False
    assert base.meter.calls == 0
    assert base.meter.reserved == 0
    assert endpoint.last_transport_attempts == 0
    assert tuple(harness.log.read()) == ()
    assert harness.workflow_state.transaction_work == {}
    assert _root_bytes(harness.root) == before


def test_standalone_bridge_release_denial_precedes_qualification_inspection(
    tmp_path,
    monkeypatch,
):
    manifest = _manifest()
    root = tmp_path / "bridge-release-denied-before-qualification"
    write_run_manifest(manifest, root / MANIFEST_NAME)
    harness = Harness(root)
    base, endpoint = _unbound_bridge_adapter(harness, manifest, budget=None)
    report_calls = []

    def forbidden_report(*_args, **_kwargs):
        report_calls.append(True)
        pytest.fail("release denial reached qualification inspection")

    monkeypatch.setenv("DEEPREASON_DISABLE_V6_LAUNCHES", "1")
    monkeypatch.setattr(
        "deepreason.cli.doctor.load_production_contract_report",
        forbidden_report,
    )
    monkeypatch.setattr(
        "deepreason.cli.doctor.validate_production_contract_qualification",
        forbidden_report,
    )
    before = _root_bytes(harness.root)

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        TransactionalBridgeAdapter(base, harness, manifest)

    assert report_calls == []
    assert base.transaction_authority_required is False
    assert base.meter.calls == 0
    assert base.meter.reserved == 0
    assert endpoint.last_transport_attempts == 0
    assert tuple(harness.log.read()) == ()
    assert harness.workflow_state.transaction_work == {}
    assert _root_bytes(harness.root) == before


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
            WireContract(
                DirectWireContract(GroundingVerdictWireV1).contract_id,
                _Output,
                _Output,
            ),
        ),
        (
            "judge",
            "bridge_grounding_repair",
            WireContract(
                DirectWireContract(GroundingRepairWireV1).contract_id,
                _Output,
                _Output,
            ),
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


def test_bridge_stages_use_independent_route_seat_base_profiles(tmp_path):
    manifest = _manifest(
        route_profiles={
            "summarizer": "compact",
            "thesis": "frontier",
            "judge": "standard",
        }
    )
    harness = Harness(tmp_path / "bridge-route-profiles")
    adapter, _endpoints = _adapter(
        harness,
        manifest,
        budget=100_000,
        calls={"summarizer": 1, "thesis": 1},
    )

    _ledger, ledger_call = adapter.call(
        "summarizer",
        "SRC_1 exact source context\nSCR_1 advisory scratch context",
        _Output,
        template_role="bridge_ledger",
        wire_contract=_ledger_contract(),
    )
    _composition, composition_call = adapter.call(
        "thesis",
        "bounded validated ledger",
        _Output,
        template_role="bridge_compose",
        wire_contract=_composition_contract(),
    )

    assert {
        attempt.model_profile for attempt in ledger_call.attempt_trace
    } == {"compact"}
    assert {
        attempt.transport_profile for attempt in ledger_call.attempt_trace
    } == {"compact"}
    assert {
        attempt.model_profile for attempt in composition_call.attempt_trace
    } == {"frontier"}
    assert {
        attempt.transport_profile for attempt in composition_call.attempt_trace
    } == {"frontier"}
    assert harness.workflow_state.compact_recovery_by_route_seat == {}


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
    sink.source_terminal_commitment_ref = (
        adapter.source_terminal_commitment_ref
    )
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



def test_real_application_bridge_uses_harness_derived_v3_v2_policy(
    tmp_path,
    monkeypatch,
):
    from deepreason.cli import doctor
    from deepreason.bridge import harness as bridge_harness
    from deepreason.llm import adapter as adapter_module

    root = tmp_path / "real-application-bridge"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    _write_eligible_v6_run_result(root, manifest)
    _write_bridge_qualification(harness, manifest)
    qualification_calls = {"load": 0, "validate": 0}
    policy_calls = {"preflight": 0, "execution": 0}
    boundary_calls = []
    original_load = doctor.load_production_contract_report
    original_validate = doctor.validate_production_contract_qualification
    original_preflight = bridge_harness.preflight_bound_bridge_policy
    original_execution = bridge_harness._bound_bridge_execution
    original_bind = LLMAdapter.bind_v6_authority

    def counted_load(*args, **kwargs):
        qualification_calls["load"] += 1
        boundary_calls.append("qualification_load")
        return original_load(*args, **kwargs)

    def counted_validate(*args, **kwargs):
        qualification_calls["validate"] += 1
        boundary_calls.append("qualification_validate")
        return original_validate(*args, **kwargs)

    def counted_preflight(*args, **kwargs):
        policy_calls["preflight"] += 1
        boundary_calls.append("policy_preflight")
        return original_preflight(*args, **kwargs)

    def counted_execution(*args, **kwargs):
        policy_calls["execution"] += 1
        boundary_calls.append("execution_policy_derivation")
        return original_execution(*args, **kwargs)

    def counted_bind(*args, **kwargs):
        boundary_calls.append("transactional_authority_binding")
        return original_bind(*args, **kwargs)

    monkeypatch.setattr(doctor, "load_production_contract_report", counted_load)
    monkeypatch.setattr(
        doctor,
        "validate_production_contract_qualification",
        counted_validate,
    )
    monkeypatch.setattr(
        bridge_harness,
        "preflight_bound_bridge_policy",
        counted_preflight,
    )
    monkeypatch.setattr(
        bridge_harness,
        "_bound_bridge_execution",
        counted_execution,
    )
    monkeypatch.setattr(LLMAdapter, "bind_v6_authority", counted_bind)
    responses = {role: [] for role in ("summarizer", "thesis", "judge")}
    for role, response in _recovery_responses():
        responses[role].append(response)
    dispatches = []
    monkeypatch.setattr(
        adapter_module,
        "_endpoint_from_spec",
        _scripted_application_endpoint_factory(manifest, responses, dispatches),
    )

    result = GroundedBridgeApplicationService().build(
        GroundedBridgeBuildIntentV1(
            root=str(root),
            problem=problem_id,
            target="answer",
        )
    )

    assert result.exit_code == 0
    assert dispatches == ["summarizer", "thesis", "judge", "judge"]
    reopened = Harness(root)
    work = tuple(reopened.workflow_state.transaction_work.values())
    assert [item.preparation.task_kind for item in work] == [
        WorkflowTaskKind.BRIDGE_LEDGER,
        WorkflowTaskKind.BRIDGE_COMPOSITION,
        WorkflowTaskKind.BRIDGE_REVIEW,
        WorkflowTaskKind.REPAIR,
    ]
    contract_ids = [item.preparation.contract_id for item in work]
    assert contract_ids == [
        "bridge.ledger.v3",
        "bridge.composition.v2",
        DirectWireContract(GroundingVerdictWireV1).contract_id,
        DirectWireContract(GroundingRepairWireV1).contract_id,
    ]
    assert len({item.preparation.id for item in work}) == 4
    assert all(item.terminal.status == "completed" for item in work)
    llm_calls = [event.llm for event in reopened.log.read() if event.llm is not None]
    assert len(llm_calls) == 4
    assert [call.attempt_trace[0].contract_id for call in llm_calls] == contract_ids
    assert qualification_calls == {"load": 1, "validate": 1}
    assert policy_calls == {"preflight": 1, "execution": 1}
    assert boundary_calls[:5] == [
        "policy_preflight",
        "qualification_load",
        "qualification_validate",
        "transactional_authority_binding",
        "execution_policy_derivation",
    ]
    commitment_ref = reopened.workflow_state.current_terminal_commitment.id
    status = status_payload(root)
    assert status["source_terminal_commitment_ref"] == commitment_ref

    status_path = root / "bridge-status.json"
    canonical_status = status_path.read_bytes()
    for replacement in (None, "sha256:" + "0" * 64, "sha256:" + "f" * 64):
        payload = json.loads(canonical_status)
        if replacement is None:
            payload.pop("source_terminal_commitment_ref")
        else:
            payload["source_terminal_commitment_ref"] = replacement
        status_path.write_bytes(canonical_json(payload) + b"\n")
        before_read = _root_bytes(root)
        dispatch_count = len(dispatches)
        with pytest.raises(ValueError, match="BRIDGE_STATUS_INVALID"):
            status_payload(root)
        assert _root_bytes(root) == before_read
        assert len(dispatches) == dispatch_count
    status_path.write_bytes(canonical_status)


def test_async_application_preflights_before_binding_and_executes_v3_v2(
    tmp_path,
    monkeypatch,
):
    from deepreason.bridge import harness as bridge_harness
    from deepreason.cli import doctor
    from deepreason.llm import adapter as adapter_module

    root = tmp_path / "async-application-bridge"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    _write_eligible_v6_run_result(root, manifest)
    _write_bridge_qualification(harness, manifest)
    qualification_calls = {"load": 0, "validate": 0}
    policy_calls = {"preflight": 0, "execution": 0}
    original_load = doctor.load_production_contract_report
    original_validate = doctor.validate_production_contract_qualification
    original_preflight = bridge_harness.preflight_bound_bridge_policy
    original_execution = bridge_harness._bound_bridge_execution

    def counted_load(*args, **kwargs):
        qualification_calls["load"] += 1
        return original_load(*args, **kwargs)

    def counted_validate(*args, **kwargs):
        qualification_calls["validate"] += 1
        return original_validate(*args, **kwargs)

    def counted_preflight(*args, **kwargs):
        policy_calls["preflight"] += 1
        return original_preflight(*args, **kwargs)

    def counted_execution(*args, **kwargs):
        policy_calls["execution"] += 1
        return original_execution(*args, **kwargs)

    monkeypatch.setattr(doctor, "load_production_contract_report", counted_load)
    monkeypatch.setattr(
        doctor,
        "validate_production_contract_qualification",
        counted_validate,
    )
    monkeypatch.setattr(
        bridge_harness,
        "preflight_bound_bridge_policy",
        counted_preflight,
    )
    monkeypatch.setattr(
        bridge_harness,
        "_bound_bridge_execution",
        counted_execution,
    )
    responses = {role: [] for role in ("summarizer", "thesis", "judge")}
    for role, response in _recovery_responses():
        responses[role].append(response)
    dispatches = []
    monkeypatch.setattr(
        adapter_module,
        "_endpoint_from_spec",
        _scripted_application_endpoint_factory(manifest, responses, dispatches),
    )
    registry = GroundedBridgeWorkerRegistry()
    service = GroundedBridgeApplicationService(registry)

    started = service.start(
        GroundedBridgeBuildIntentV1(
            root=str(root),
            problem=problem_id,
            target="answer",
        )
    )
    worker = registry.threads[registry.key(root)]
    worker.join(timeout=15)

    assert started.state == "running"
    assert not worker.is_alive()
    assert dispatches == ["summarizer", "thesis", "judge", "judge"]
    assert qualification_calls == {"load": 1, "validate": 1}
    assert policy_calls == {"preflight": 2, "execution": 1}
    work = tuple(Harness(root).workflow_state.transaction_work.values())
    assert [item.preparation.contract_id for item in work] == [
        "bridge.ledger.v3",
        "bridge.composition.v2",
        DirectWireContract(GroundingVerdictWireV1).contract_id,
        DirectWireContract(GroundingRepairWireV1).contract_id,
    ]



def _summarizer_adapter(harness, manifest, endpoint):
    return _qualified_transactional_adapter(
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
    assert all(event.bridge is None for event in harness.log.read())
    assert derive_terminal_authority(
        harness.root,
        manifest=manifest,
    ).current_valid


@pytest.mark.parametrize(
    ("role", "template_role", "contract_factory", "task_kind"),
    (
        (
            "summarizer",
            "bridge_ledger",
            _ledger_contract,
            WorkflowTaskKind.BRIDGE_LEDGER,
        ),
        (
            "thesis",
            "bridge_compose",
            _composition_contract,
            WorkflowTaskKind.BRIDGE_COMPOSITION,
        ),
    ),
)
def test_bridge_runtime_uses_contract_grant_not_bridge_policy_ceiling(
    tmp_path,
    role,
    template_role,
    contract_factory,
    task_kind,
):
    contract = contract_factory()
    manifest = _with_contract_grant(_manifest(), contract.contract_id, 1)
    assert manifest.bridge_policy.max_schema_repair_attempts == 0
    grants = {
        grant.contract_id: grant.maximum_schema_repairs
        for grant in manifest.contract_schema_repair_policy.grants
    }
    assert grants["conjecturer.turn.v6"] == 2
    assert grants[contract.contract_id] == 1
    harness = Harness(tmp_path / f"bridge-grant-{role}")
    route = manifest.roles[role][0]
    endpoint = MockEndpoint(
        ["{not-json", '{"value":"repaired"}'],
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = _qualified_transactional_adapter(
        LLMAdapter(
            {role: endpoint},
            harness.blobs,
            retry_max=99,
            meter=TokenMeter(100_000),
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
        ),
        harness,
        manifest,
    )

    output, _receipt = adapter.call(
        role,
        "bounded bridge context",
        _Output,
        template_role=template_role,
        wire_contract=contract,
    )

    work = tuple(harness.workflow_state.transaction_work.values())
    assert output.value == "repaired"
    assert [item.preparation.task_kind for item in work] == [
        task_kind,
        WorkflowTaskKind.REPAIR,
    ]
    assert [item.terminal.status for item in work] == ["rejected", "completed"]
    assert len([event for event in harness.log.read() if event.llm is not None]) == 2


@pytest.mark.parametrize(
    ("wire_model", "template_role"),
    (
        (GroundingVerdictWireV1, "bridge_review"),
        (GroundingRepairWireV1, "bridge_grounding_repair"),
    ),
)
def test_grounding_direct_contracts_use_their_canonical_zero_grants(
    tmp_path,
    wire_model,
    template_role,
):
    manifest = _manifest()
    contract = DirectWireContract(wire_model)
    grant = next(
        grant
        for grant in manifest.contract_schema_repair_policy.grants
        if grant.contract_id == contract.contract_id
    )
    harness = Harness(tmp_path / contract.contract_id)
    route = manifest.roles["judge"][0]
    endpoint = MockEndpoint(
        ["{not-json", "must-not-dispatch"],
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = _qualified_transactional_adapter(
        LLMAdapter(
            {"judge": endpoint},
            harness.blobs,
            retry_max=99,
            meter=TokenMeter(100_000),
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
        ),
        harness,
        manifest,
    )

    with pytest.raises(SchemaRepairError):
        adapter.call(
            "judge",
            "bounded grounding context",
            wire_model,
            template_role=template_role,
            wire_contract=contract,
        )

    work = tuple(harness.workflow_state.transaction_work.values())
    assert grant.maximum_schema_repairs == 0
    assert len(work) == 1
    assert work[0].preparation.contract_id == contract.contract_id
    assert work[0].terminal.status == "schema_exhausted"
    assert adapter._adapter.meter.calls == 1
    assert adapter._adapter.meter.reserved == 0


def test_object_wide_bridge_diagnostic_is_schema_exhausted(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "bridge-unrepairable")
    route = manifest.roles["summarizer"][0]
    endpoint = MockEndpoint(
        '{"value":"semantically impossible"}',
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = _summarizer_adapter(harness, manifest, endpoint)

    with pytest.raises(SchemaRepairError):
        adapter.call(
            "summarizer",
            "bounded bridge context",
            _RootInvalidOutput,
            template_role="bridge_ledger",
            wire_contract=WireContract(
                "bridge.ledger.v3",
                _RootInvalidOutput,
                _RootInvalidOutput,
            ),
        )

    item = next(iter(harness.workflow_state.transaction_work.values()))
    admission = item.admissions[item.preparation.attempt_index]
    assert admission.outcome == "schema_exhausted"
    assert item.terminal.status == "schema_exhausted"
    assert adapter._adapter.meter.calls == 1
    assert adapter._adapter.meter.reserved == 0


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
    assert all(event.bridge is None for event in harness.log.read())
    assert derive_terminal_authority(
        harness.root,
        manifest=manifest,
    ).current_valid


def test_post_terminal_failed_writer_denial_preserves_existing_transaction_state(
    tmp_path,
):
    manifest = _manifest()
    harness = Harness(tmp_path / "bridge-writer-denial")
    route = manifest.roles["summarizer"][0]
    endpoint = MockEndpoint(
        ["{not-json"],
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = _summarizer_adapter(harness, manifest, endpoint)
    with pytest.raises(SchemaRepairError):
        adapter.call(
            "summarizer",
            "bounded bridge context",
            _Output,
            template_role="bridge_ledger",
            wire_contract=_ledger_contract(),
        )
    commitment = harness.workflow_state.current_terminal_commitment
    assert commitment is not None
    root_before = _root_bytes(harness.root)
    log_before = tuple(harness.log.read())
    bridge_before = deepcopy(harness.bridge_state)
    work_before = deepcopy(harness.workflow_state.transaction_work)
    reservations_before = adapter._adapter.meter.snapshot()
    provider_calls_before = endpoint.last_transport_attempts
    next_seq_before = harness._next_seq

    with pytest.raises(ValueError, match="requires exactly one bridge failure"):
        harness.record_bridge_event(
            BridgeAction.FAILED,
            inputs=[commitment.id],
            error_code="POST_TERMINAL_GENERIC_INPUT",
        )

    assert _root_bytes(harness.root) == root_before
    assert tuple(harness.log.read()) == log_before
    assert harness.bridge_state == bridge_before
    assert harness.workflow_state.transaction_work == work_before
    assert adapter._adapter.meter.snapshot() == reservations_before
    assert endpoint.last_transport_attempts == provider_calls_before
    assert harness._next_seq == next_seq_before


def test_v6_post_issuance_typed_bridge_failure_retains_terminal_authority(
    tmp_path,
):
    root = tmp_path / "bridge-post-issuance-failure"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        (("summarizer", "{not-json"),),
        dispatches,
    )

    terminal = _run_recovery_bridge(
        harness,
        manifest,
        problem_id,
        adapter,
    )

    assert terminal.process_status == "failure"
    assert terminal.failure_id in harness.bridge_state.failures
    failure_events = [
        event
        for event in harness.log.read()
        if event.bridge is not None
        and event.bridge.action == BridgeAction.FAILED
    ]
    assert len(failure_events) == 1
    assert failure_events[0].outputs.count(terminal.failure_id) == 1
    assert any(
        item.terminal is not None
        for item in harness.workflow_state.transaction_work.values()
    )
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    assert verify_root_report(root).integrity_valid



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


def _recovery_policy(manifest):
    return _historical_bridge_caller_policy(manifest)


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
    return _qualified_transactional_adapter(base, harness, manifest)


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
        _recovery_policy(manifest) if policy is None else policy,
        run_manifest_digest=manifest.sha256,
        stage_a_adapter=adapter,
        composition_adapter=adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
    )


def _bridge_authority_snapshot(harness, adapter):
    base = adapter._adapter
    replay_manifest = getattr(harness.workflow_state, "_run_manifest", None)
    return {
        "transaction_authority_required": base.transaction_authority_required,
        "authority_harness_matches": base._v6_authority_harness is harness,
        "authority_manifest_sha256": base._v6_authority_manifest.sha256,
        "adapter_manifest_sha256": adapter.manifest.sha256,
        "replay_manifest_sha256": replay_manifest.sha256,
        "ordinal": adapter._ordinal,
        "execution_id": adapter._execution_id,
        "execution_snapshot_ref": adapter._execution_snapshot_ref,
        "execution_formal_fence": adapter._execution_formal_fence,
        "meter": base.meter.snapshot(),
    }


def test_duplicate_bridge_completion_invalidates_terminal_consistency(tmp_path):
    root = tmp_path / "duplicate-bridge-completion"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _recovery_responses(),
        dispatches,
    )
    terminal = _run_recovery_bridge(harness, manifest, problem_id, adapter)
    completed = next(
        event
        for event in harness.log.read()
        if event.bridge is not None
        and event.bridge.action == BridgeAction.COMPLETED
    )
    assert terminal.terminal_event_seq == completed.seq
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    before = _root_bytes(root)
    with pytest.raises(ValueError, match="TERMINAL_BRIDGE_COMPLETION_DUPLICATED"):
        harness.record_bridge_event(
            BridgeAction.COMPLETED,
            inputs=completed.inputs,
        )

    assert _root_bytes(root) == before
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    assert verify_root_report(root).integrity_valid
    assert max(event.seq for event in harness.log.read()) == completed.seq


def test_transactional_bridge_missing_manifest_fails_before_any_mutation(tmp_path):
    from deepreason.bridge.harness import preflight_bound_bridge_policy

    root = tmp_path / "transactional-manifest-removed"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    _write_bridge_qualification(harness, manifest)
    effective = preflight_bound_bridge_policy(
        policy=_recovery_policy(manifest),
        run_manifest=manifest,
    )
    assert effective.ledger_contract_version == "v3"
    assert effective.composition_contract_version == "v2"
    dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _recovery_responses(),
        dispatches,
    )
    files_before = _root_bytes(root)
    log_before = tuple(harness.log.read())
    bridge_before = deepcopy(harness.bridge_state)
    work_before = deepcopy(harness.workflow_state.transaction_work)
    authority_before = _bridge_authority_snapshot(harness, adapter)
    next_seq_before = harness._next_seq
    expected_files = dict(files_before)
    expected_files.pop(MANIFEST_NAME)
    (root / MANIFEST_NAME).unlink()

    with pytest.raises(ValueError, match="^BRIDGE_MANIFEST_MISMATCH$"):
        harness.build_bridge(
            problem_id,
            "answer",
            _recovery_policy(manifest),
            run_manifest_digest=manifest.sha256,
            stage_a_adapter=adapter,
            composition_adapter=adapter,
            review_adapter=adapter,
            repair_adapter=adapter,
        )

    assert dispatches == []
    assert tuple(harness.log.read()) == log_before
    assert harness.bridge_state == bridge_before
    assert harness.workflow_state.transaction_work == work_before
    assert harness._next_seq == next_seq_before
    assert _bridge_authority_snapshot(harness, adapter) == authority_before
    assert _root_bytes(root) == expected_files
    assert not (root / BRIDGE_RESULT_NAME).exists()
    assert not (root / "bridge-status.json").exists()


def test_transactional_bridge_replaced_manifest_fails_before_any_mutation(tmp_path):
    from deepreason.bridge.harness import preflight_bound_bridge_policy

    root = tmp_path / "transactional-manifest-replaced"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    _write_bridge_qualification(harness, manifest)
    preflight_bound_bridge_policy(
        policy=_recovery_policy(manifest),
        run_manifest=manifest,
    )
    dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _recovery_responses(),
        dispatches,
    )
    foreign = _manifest(
        run_input_digest=manifest.run_input_digest,
        route_profiles={"summarizer": "compact"},
    )
    (root / MANIFEST_NAME).write_bytes(foreign.canonical_bytes())
    files_before = _root_bytes(root)
    log_before = tuple(harness.log.read())
    bridge_before = deepcopy(harness.bridge_state)
    work_before = deepcopy(harness.workflow_state.transaction_work)
    authority_before = _bridge_authority_snapshot(harness, adapter)
    next_seq_before = harness._next_seq

    with pytest.raises(RunManifestError) as caught:
        harness.build_bridge(
            problem_id,
            "answer",
            _recovery_policy(manifest),
            run_manifest_digest=manifest.sha256,
            stage_a_adapter=adapter,
            composition_adapter=adapter,
            review_adapter=adapter,
            repair_adapter=adapter,
        )

    assert caught.value.code == "MANIFEST_HASH_MISMATCH"
    assert dispatches == []
    assert tuple(harness.log.read()) == log_before
    assert harness.bridge_state == bridge_before
    assert harness.workflow_state.transaction_work == work_before
    assert harness._next_seq == next_seq_before
    assert _bridge_authority_snapshot(harness, adapter) == authority_before
    assert _root_bytes(root) == files_before


def test_nontransactional_manifest_absent_bridge_retains_legacy_fallback(tmp_path):
    root = tmp_path / "legacy-manifest-absent"
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    endpoint = MockEndpoint(["not-json"])
    adapter = LLMAdapter(
        {
            "summarizer": endpoint,
            "thesis": MockEndpoint([]),
        },
        harness.blobs,
        retry_max=0,
    )

    terminal = harness.build_bridge(
        problem_id,
        "answer",
        {
            "grounding_review": False,
            "max_grounding_repair_attempts": 0,
        },
        run_manifest_digest="a" * 64,
        stage_a_adapter=adapter,
    )

    assert terminal.process_status == "failure"
    assert terminal.error_code != "BRIDGE_MANIFEST_MISMATCH"
    assert endpoint.last_transport_attempts == 1
    assert len(tuple(harness.log.read())) > 2


def test_application_rejects_effective_policy_before_adapter_binding(
    tmp_path,
    monkeypatch,
):
    from deepreason.cli import doctor

    root = tmp_path / "application-invalid-effective-policy"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    _write_eligible_v6_run_result(root, manifest)
    effective_policy = manifest.bridge_policy.workflow_policy(
        ledger_contract_version="v3",
        composition_contract_version="v2",
    )
    adapter_constructions = []
    authority_bindings = []
    qualification_calls = []

    def invalid_caller_projection(_manifest):
        return effective_policy

    def forbidden_adapter(*_args, **_kwargs):
        adapter_constructions.append(True)
        pytest.fail("invalid policy reached transactional adapter construction")

    def forbidden_binding(*_args, **_kwargs):
        authority_bindings.append(True)
        pytest.fail("invalid policy reached bind_v6_authority")

    def forbidden_qualification(*_args, **_kwargs):
        qualification_calls.append(True)
        pytest.fail("invalid policy reached production qualification")

    monkeypatch.setattr(
        bridge_application,
        "_historical_bridge_caller_policy",
        invalid_caller_projection,
    )
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        forbidden_adapter,
    )
    monkeypatch.setattr(LLMAdapter, "bind_v6_authority", forbidden_binding)
    monkeypatch.setattr(
        doctor,
        "load_production_contract_report",
        forbidden_qualification,
    )
    monkeypatch.setattr(
        doctor,
        "validate_production_contract_qualification",
        forbidden_qualification,
    )
    before = _root_bytes(root)
    log_before = tuple(harness.log.read())
    work_before = deepcopy(harness.workflow_state.transaction_work)

    with pytest.raises(ValueError, match="BRIDGE_WORKFLOW_POLICY_MISMATCH"):
        GroundedBridgeApplicationService().build(
            GroundedBridgeBuildIntentV1(
                root=str(root),
                problem=problem_id,
                target="answer",
            )
        )

    assert adapter_constructions == []
    assert authority_bindings == []
    assert qualification_calls == []
    assert tuple(harness.log.read()) == log_before
    assert harness.workflow_state.transaction_work == work_before
    assert _root_bytes(root) == before


def test_application_bridge_restart_recovers_durable_result_without_redispatch(
    tmp_path,
    monkeypatch,
):
    from deepreason.cli import doctor
    from deepreason.llm import adapter as adapter_module

    root = tmp_path / "application-bridge-restart"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    _write_eligible_v6_run_result(root, manifest)
    _write_bridge_qualification(harness, manifest)
    qualification_calls = {"load": 0, "validate": 0}
    original_load = doctor.load_production_contract_report
    original_validate = doctor.validate_production_contract_qualification

    def counted_load(*args, **kwargs):
        qualification_calls["load"] += 1
        return original_load(*args, **kwargs)

    def counted_validate(*args, **kwargs):
        qualification_calls["validate"] += 1
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(doctor, "load_production_contract_report", counted_load)
    monkeypatch.setattr(
        doctor,
        "validate_production_contract_qualification",
        counted_validate,
    )
    initial_responses = {role: [] for role in ("summarizer", "thesis", "judge")}
    for role, response in _recovery_responses():
        initial_responses[role].append(response)
    initial_dispatches = []
    monkeypatch.setattr(
        adapter_module,
        "_endpoint_from_spec",
        _scripted_application_endpoint_factory(
            manifest,
            initial_responses,
            initial_dispatches,
        ),
    )
    original_admission = InquiryTransactionService.record_semantic_admission
    admissions = 0

    def crash_after_first_provider_result(self, provider_attempt, **kwargs):
        nonlocal admissions
        if admissions == 0:
            admissions += 1
            raise _InjectedBridgeAdmissionCrash()
        admissions += 1
        return original_admission(self, provider_attempt, **kwargs)

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        crash_after_first_provider_result,
    )
    intent = GroundedBridgeBuildIntentV1(
        root=str(root),
        problem=problem_id,
        target="answer",
    )
    with pytest.raises(_InjectedBridgeAdmissionCrash):
        GroundedBridgeApplicationService().build(intent)
    assert initial_dispatches == ["summarizer"]
    assert qualification_calls == {"load": 1, "validate": 1}

    monkeypatch.setattr(
        InquiryTransactionService,
        "record_semantic_admission",
        original_admission,
    )
    remaining = {role: [] for role in ("summarizer", "thesis", "judge")}
    for role, response in _recovery_responses()[1:]:
        remaining[role].append(response)
    recovery_dispatches = []
    monkeypatch.setattr(
        adapter_module,
        "_endpoint_from_spec",
        _scripted_application_endpoint_factory(
            manifest,
            remaining,
            recovery_dispatches,
        ),
    )

    result = GroundedBridgeApplicationService().build(intent)

    assert result.exit_code == 0
    assert recovery_dispatches == ["thesis", "judge", "judge"]
    assert qualification_calls == {"load": 2, "validate": 2}
    reopened = Harness(root)
    work = tuple(reopened.workflow_state.transaction_work.values())
    assert [item.preparation.contract_id for item in work] == [
        "bridge.ledger.v3",
        "bridge.composition.v2",
        DirectWireContract(GroundingVerdictWireV1).contract_id,
        DirectWireContract(GroundingRepairWireV1).contract_id,
    ]
    assert all(item.terminal is not None for item in work)
    assert all(item.terminal.status == "completed" for item in work)
    assert derive_terminal_authority(root, manifest=manifest).current_valid


def test_bound_v6_direct_bridge_honors_disabled_launch_policy_before_dispatch(
    tmp_path, monkeypatch
):
    root = tmp_path / "bridge-direct-launch-disabled"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _recovery_responses(),
        dispatches,
    )
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    monkeypatch.setenv("DEEPREASON_DISABLE_V6_LAUNCHES", "1")

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)

    assert dispatches == []
    assert {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    } == before


def test_bound_direct_bridge_inaccessible_manifest_fails_before_dispatch(
    tmp_path, monkeypatch
):
    root = tmp_path / "bridge-direct-manifest-inaccessible"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _recovery_responses(),
        dispatches,
    )
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    manifest_path = root / MANIFEST_NAME
    original_lstat = Path.lstat

    def inaccessible(path):
        if path == manifest_path:
            raise PermissionError("bound bridge manifest inspection denied")
        return original_lstat(path)

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "lstat", inaccessible)
        with pytest.raises(
            PermissionError, match="bound bridge manifest inspection denied"
        ):
            _run_recovery_bridge(harness, manifest, problem_id, adapter)

    assert dispatches == []
    assert {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    } == before


@pytest.mark.parametrize("crash_ordinal", range(4))
def test_v6_bridge_restart_replays_saved_provider_result_without_redispatch(
    tmp_path, monkeypatch, crash_ordinal
):
    from deepreason.cli import doctor

    root = tmp_path / f"bridge-restart-{crash_ordinal}"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    qualification_calls = {"load": 0, "validate": 0}
    original_load = doctor.load_production_contract_report
    original_validate = doctor.validate_production_contract_qualification

    def counted_load(*args, **kwargs):
        qualification_calls["load"] += 1
        return original_load(*args, **kwargs)

    def counted_validate(*args, **kwargs):
        qualification_calls["validate"] += 1
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(doctor, "load_production_contract_report", counted_load)
    monkeypatch.setattr(
        doctor,
        "validate_production_contract_qualification",
        counted_validate,
    )
    initial_dispatches = []
    adapter = _recovery_adapter(
        harness,
        manifest,
        _recovery_responses(),
        initial_dispatches,
    )
    assert qualification_calls == {"load": 1, "validate": 1}
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
    assert qualification_calls == {"load": 2, "validate": 2}
    terminal = _run_recovery_bridge(reopened, manifest, problem_id, recovered_adapter)

    assert terminal.process_status == "success"
    assert terminal.formal_seq == frozen_fence
    assert recovery_dispatches == [role for role, _response in remaining]
    recovered_work = tuple(reopened.workflow_state.transaction_work.values())
    assert len(recovered_work) == 4
    assert all(item.terminal is not None for item in recovered_work)
    assert all(item.terminal.status == "completed" for item in recovered_work)
    assert all(item.preparation.formal_fence_seq == frozen_fence for item in recovered_work)
    assert qualification_calls == {"load": 2, "validate": 2}
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
    assert derive_terminal_authority(root, manifest=manifest).current_valid

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
        assert qualification_calls == {"load": 3, "validate": 3}
        repeat = _run_recovery_bridge(again, manifest, problem_id, idempotent_adapter)
        assert repeat == terminal
        assert idempotent_dispatches == []
        assert tuple(again.log.read()) == log_before
        assert again.bridge_state == bridge_state_before
        assert (root / BRIDGE_RESULT_NAME).read_bytes() == result_before
        assert qualification_calls == {"load": 3, "validate": 3}

def test_v6_bridge_restart_corrupt_saved_result_fails_closed_without_redispatch(
    tmp_path, monkeypatch
):
    root = tmp_path / "bridge-restart-corrupt"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
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
    root = tmp_path / "bridge-restart-missing-receipt"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
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
    root = tmp_path / "bridge-restart-invalid-provider-result"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
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
    root = tmp_path / "bridge-restart-extra-prefix-work"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
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
    root = tmp_path / "bridge-restart-extra-completed-work"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
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
    assert retry_events == []
    assert reopened.bridge_state.workflow_retries == {}
    (transition,) = reopened.workflow_state.contract_decomposition_by_source_work.values()
    assert transition.source_contract_id == "bridge.ledger.v3"
    assert transition.atomic_contract_id == "bridge.ledger-batch.v1"
    source = reopened.workflow_state.transaction_work[transition.source_work_id]
    assert source.terminal.status == "schema_exhausted"
    child = next(
        item
        for item in reopened.workflow_state.transaction_work.values()
        if item.preparation.task_payload_value.get("decomposition_transition_ref")
        == transition.id
    )
    assert child.preparation.contract_id == "bridge.ledger-batch.v1"
    assert child.terminal.status == "completed"

    replayed = Harness(root)
    assert replayed.bridge_state.workflow_retries == {}
    assert replayed.workflow_state.contract_decomposition_by_source_work == (
        reopened.workflow_state.contract_decomposition_by_source_work
    )


def test_v6_bridge_restart_missing_snapshot_fails_before_dispatch(tmp_path):
    root = tmp_path / "bridge-restart-missing-snapshot"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
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
        source_terminal_commitment_ref=adapter.source_terminal_commitment_ref,
        task_payload_value={
            "schema": "bridge.transaction-task.v2",
            "source_terminal_commitment_ref": adapter.source_terminal_commitment_ref,
            "execution_id": "sha256:" + "1" * 64,
            "execution_snapshot_ref": "sha256:" + "2" * 64,
            "ordinal": 0,
            "role": "summarizer",
            "seat": 0,
            "template_role": "bridge_ledger",
            "contract_id": "bridge.ledger.v3",
        },
    )

    with pytest.raises(ValueError, match="BRIDGE_RECOVERY_SNAPSHOT_INVALID"):
        _run_recovery_bridge(harness, manifest, problem_id, adapter)

    item = harness.workflow_state.transaction_work[preparation.id]
    assert not item.issued
    assert item.provider_attempts == {}
    assert dispatches == []
    assert not (root / BRIDGE_RESULT_NAME).exists()
    assert all(event.bridge is None for event in harness.log.read())
