"""RunManifest-v6 adapters cannot dispatch outside a work transaction."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

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
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import MockEndpoint
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
    load_run_manifest,
    write_run_manifest,
)
from deepreason.runtime.launch_policy import (
    RELEASE_POLICY_ENV,
    RELEASE_POLICY_SCHEMA,
    V6_LAUNCH_DISABLE_ENV,
    require_v6_production_qualification,
)
from deepreason.storage.blobs import BlobStore


GOOD = json.dumps(
    {"candidates": [{"content": "bounded dispatch", "typicality": 0.5}]}
)


def test_transaction_required_adapter_rejects_unbound_dispatch(tmp_path):
    endpoint = MockEndpoint([GOOD])
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        BlobStore(tmp_path / "blobs"),
        transaction_authority_required=True,
    )

    with pytest.raises(
        WorkflowAuthorizationError,
        match="behavioral manifest authority",
    ):
        adapter.preview_request("conjecturer", "PACK", ConjecturerOutput)
    assert endpoint.last_transport_attempts == 0


def test_legacy_adapter_keeps_unbound_dispatch_compatibility(tmp_path):
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([GOOD])},
        BlobStore(tmp_path / "blobs"),
    )

    output, _call = adapter.call("conjecturer", "PACK", ConjecturerOutput)
    assert output.candidates[0].content == "bounded dispatch"

def _disable_v6(monkeypatch) -> None:
    monkeypatch.setenv(V6_LAUNCH_DISABLE_ENV, "1")
    monkeypatch.delenv(RELEASE_POLICY_ENV, raising=False)


def _forbid(calls, boundary: str):
    def forbidden(*_args, **_kwargs):
        calls.append(boundary)
        raise AssertionError(f"v6 launch policy reached {boundary}")

    return forbidden


def _assert_scheduler_policy_rejected(monkeypatch, manifest, expected_error: str) -> None:
    import deepreason.llm.adapter as adapter_module
    import deepreason.llm.budget as budget_module
    import deepreason.ops as ops
    import deepreason.run_manifest as run_manifest_module
    import deepreason.scheduler.scheduler as scheduler_module

    calls = []
    harness = SimpleNamespace(
        blobs=object(),
        log=SimpleNamespace(read=_forbid(calls, "event log")),
    )
    monkeypatch.setattr(ops, "require_full_engine", _forbid(calls, "engine preflight"))
    monkeypatch.setattr(
        run_manifest_module,
        "preflight_harness",
        _forbid(calls, "manifest preflight"),
    )
    monkeypatch.setattr(budget_module, "TokenMeter", _forbid(calls, "token meter"))
    monkeypatch.setattr(adapter_module, "build_adapter", _forbid(calls, "adapter"))
    monkeypatch.setattr(scheduler_module, "Scheduler", _forbid(calls, "scheduler"))

    with pytest.raises(ValueError, match=expected_error):
        ops.run_scheduler(
            harness,
            SimpleNamespace(),
            cycles=1,
            token_budget=1,
            run_manifest=manifest,
        )

    assert calls == []


def _bound_v6_scheduler_harness(tmp_path):
    root = tmp_path / "bound-v6-scheduler-root"
    problem_id = "bound-v6-scheduler-problem"
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="scheduler containment regression",
            acquisition_method="offline construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id,
            description="Verify bound-manifest scheduler containment.",
            criteria=(),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    config = Config(
        N_SCHOOLS=0,
        roles={
            "conjecturer": [
                {
                    "endpoint_id": "scheduler-guard-route",
                    "endpoint": "mock://scheduler-guard-route",
                    "model": "offline-scheduler-guard",
                    "provider": "mock",
                    "family": "offline-scheduler-guard",
                    "max_tokens": 64,
                    "context_window_tokens": 262_144,
                }
            ]
        },
    )
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
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
        scratch_authoring=ScratchAuthoringPolicyV1(),
    )
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-19T00:00:00Z",
        control_plane_policy=control,
        run_input_digest=run_input.run_input_digest,
    )
    bind_run_manifest(manifest, root)
    return Harness(root), config


def _root_snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _forbid_bound_scheduler_work(monkeypatch, harness):
    import deepreason.llm.adapter as adapter_module
    import deepreason.llm.budget as budget_module
    import deepreason.ops as ops
    import deepreason.run_manifest as run_manifest_module
    import deepreason.scheduler.scheduler as scheduler_module

    calls = []
    monkeypatch.setattr(harness.log, "read", _forbid(calls, "event log"))
    monkeypatch.setattr(ops, "require_full_engine", _forbid(calls, "engine preflight"))
    monkeypatch.setattr(
        run_manifest_module,
        "preflight_harness",
        _forbid(calls, "manifest preflight"),
    )
    monkeypatch.setattr(budget_module, "TokenMeter", _forbid(calls, "token meter"))
    monkeypatch.setattr(adapter_module, "build_adapter", _forbid(calls, "adapter"))
    monkeypatch.setattr(scheduler_module, "Scheduler", _forbid(calls, "scheduler"))
    return calls


def _qualified_manifest_and_report():
    from tests.test_cli_production_doctor_v6 import _manifest, _qualified_report

    manifest = _manifest()
    return manifest, _qualified_report(manifest)


def _write_required_report(root, manifest, report):
    from deepreason.cli.doctor import write_production_contract_report

    policy = manifest.production_qualification_policy
    assert policy is not None
    return write_production_contract_report(report, root / policy.report_filename)


def _allow_scheduler_work(monkeypatch, calls):
    import deepreason.llm.adapter as adapter_module
    import deepreason.ops as ops
    import deepreason.run_manifest as run_manifest_module
    import deepreason.scheduler.scheduler as scheduler_module

    class Adapter:
        def has_role(self, role):
            return role == "conjecturer"

    class Scheduler:
        def __init__(self, *_args, **_kwargs):
            calls.append("scheduler")

        def run(self, cycles, **_kwargs):
            calls.append(("run", cycles))
            return {"cycles": cycles}

    monkeypatch.setattr(
        run_manifest_module,
        "preflight_harness",
        lambda *_args: calls.append("manifest preflight"),
    )
    monkeypatch.setattr(
        adapter_module,
        "build_adapter",
        lambda *_args, **_kwargs: calls.append("adapter") or Adapter(),
    )
    monkeypatch.setattr(scheduler_module, "Scheduler", Scheduler)
    monkeypatch.setattr(ops, "make_embedder", lambda *_args: None)
    monkeypatch.setattr(ops, "make_research_service", lambda *_args: None)
    monkeypatch.setattr(ops.importlib.util, "find_spec", lambda _name: None)


def _scheduler_harness(root, *, log_read=lambda: ()):
    return SimpleNamespace(
        root=root,
        blobs=object(),
        log=SimpleNamespace(read=log_read),
        bind_model_classification=lambda _manifest, _report: None,
    )


@pytest.mark.parametrize("token_budget", (1, None))
def test_v6_scheduler_requires_qualification_before_protected_work(
    tmp_path,
    monkeypatch,
    token_budget,
):
    import deepreason.ops as ops

    manifest, _report = _qualified_manifest_and_report()
    root = tmp_path / "missing-qualification"
    root.mkdir()
    harness = _scheduler_harness(root)
    before = _root_snapshot(root)
    calls = _forbid_bound_scheduler_work(monkeypatch, harness)

    with pytest.raises(RunManifestError) as caught:
        ops.run_scheduler(
            harness,
            SimpleNamespace(),
            cycles=1,
            token_budget=token_budget,
            run_manifest=manifest,
        )

    assert caught.value.code == "DOCTOR_REPORT_MISSING"
    assert calls == []
    assert _root_snapshot(root) == before


def test_canonical_qualified_report_allows_existing_scheduler_path(
    tmp_path,
    monkeypatch,
):
    import deepreason.ops as ops

    manifest, report = _qualified_manifest_and_report()
    root = tmp_path / "qualified"
    root.mkdir()
    assert not (root / MANIFEST_NAME).exists()
    _write_required_report(root, manifest, report)
    assert require_v6_production_qualification(
        manifest,
        root=root,
        operation="full scheduler",
    ) == report
    calls = []
    _allow_scheduler_work(monkeypatch, calls)

    harness = Harness(root)
    result, meter, accounting = ops.run_scheduler(
        harness,
        SimpleNamespace(CONTROLLER=False, engine_profile="full"),
        cycles=1,
        token_budget=None,
        run_manifest=manifest,
        stop_controller=object(),
    )

    assert result == {"cycles": 1}
    assert meter.budget is None
    assert accounting["metered_tokens"] == 0
    assert calls == ["manifest preflight", "adapter", "scheduler", ("run", 1)]
    classification = harness.workflow_state.route_seat_model_classification
    assert classification == report.route_seat_model_classification
    assert harness.workflow_state.model_classification_binding is not None
    assert sum(
        event.control is not None
        and event.control.action == "classification_bound"
        for event in harness.log.read()
    ) == 1


@pytest.mark.parametrize(
    ("variant", "expected_code"),
    (
        ("elsewhere", "DOCTOR_REPORT_MISSING"),
        ("symlink", "DOCTOR_REPORT_UNSAFE"),
        ("malformed", "DOCTOR_REPORT_INVALID"),
        ("noncanonical", "DOCTOR_REPORT_NONCANONICAL"),
        ("wrong-manifest", "DOCTOR_REPORT_MANIFEST_MISMATCH"),
        ("wrong-profile", "DOCTOR_REPORT_MANIFEST_MISMATCH"),
        ("altered-pair", "DOCTOR_REPORT_PAIR_INVENTORY_MISMATCH"),
    ),
)
def test_inexact_qualification_reports_fail_before_scheduler_work(
    tmp_path,
    monkeypatch,
    variant,
    expected_code,
):
    import deepreason.ops as ops
    from deepreason.cli.doctor import write_production_contract_report
    from tests.test_cli_production_doctor_v6 import _manifest, _qualified_report

    manifest, report = _qualified_manifest_and_report()
    root = tmp_path / variant
    root.mkdir()
    policy = manifest.production_qualification_policy
    assert policy is not None
    required = root / policy.report_filename
    if variant == "elsewhere":
        write_production_contract_report(report, root / "elsewhere.json")
    elif variant == "symlink":
        elsewhere = write_production_contract_report(report, root / "elsewhere.json")
        required.symlink_to(elsewhere)
    elif variant == "malformed":
        required.write_bytes(b"{\n")
    elif variant == "noncanonical":
        required.write_text(
            json.dumps(report.model_dump(mode="json", by_alias=True), indent=2)
            + "\n",
            encoding="utf-8",
        )
    elif variant == "wrong-manifest":
        payload = json.loads(manifest.canonical_bytes())
        payload["compiled_at"] = "2026-07-20T00:00:01Z"
        foreign = RunManifest.model_validate(payload)
        write_production_contract_report(_qualified_report(foreign), required)
    elif variant == "wrong-profile":
        foreign = _manifest(route_profiles={"conjecturer": "compact"})
        write_production_contract_report(_qualified_report(foreign), required)
    else:
        pairs = list(report.pairs)
        first = pairs[0]
        pairs[0] = first.model_copy(
            update={
                "pair": first.pair.model_copy(
                    update={"endpoint_id": first.pair.endpoint_id + "-foreign"}
                )
            }
        )
        write_production_contract_report(
            report.model_copy(update={"pairs": tuple(pairs)}),
            required,
        )
    harness = _scheduler_harness(root)
    before = _root_snapshot(root)
    calls = _forbid_bound_scheduler_work(monkeypatch, harness)

    with pytest.raises(RunManifestError) as caught:
        ops.run_scheduler(
            harness,
            SimpleNamespace(),
            cycles=1,
            run_manifest=manifest,
        )

    assert caught.value.code == expected_code
    assert calls == []
    assert _root_snapshot(root) == before


def test_repair_overclaim_and_unqualified_reports_fail_before_scheduler_work(
    tmp_path,
    monkeypatch,
):
    import deepreason.ops as ops
    from deepreason.cli.doctor import (
        ProductionContractDoctorReportV1,
        run_production_contract_doctor,
    )
    from tests.test_cli_production_doctor_v6 import (
        _admitted_case,
        _case,
        _manifest,
        _pair_report,
        _with_contract_grant,
    )

    zero_manifest = _with_contract_grant(_manifest(), "batch-critic.v2", 0)
    zero_report = run_production_contract_doctor(
        zero_manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    pair_index = next(
        index
        for index, item in enumerate(zero_report.pairs)
        if item.pair.contract_id == "batch-critic.v2"
    )
    pair_report = zero_report.pairs[pair_index]
    cases = list(pair_report.cases)
    cases[0] = _admitted_case(0, repairs=1)
    pairs = list(zero_report.pairs)
    pairs[pair_index] = _pair_report(pair_report.pair, tuple(cases))
    overclaim = ProductionContractDoctorReportV1(
        run_manifest_sha256=zero_manifest.sha256,
        pairs=tuple(pairs),
        summary=zero_report.summary.model_copy(
            update={
                "first_pass_valid_count": zero_report.summary.first_pass_valid_count
                - 1,
                "repair_count": zero_report.summary.repair_count + 1,
            }
        ),
    )
    unqualified_manifest = _manifest()
    unqualified = run_production_contract_doctor(
        unqualified_manifest,
        case_executor=lambda _manifest, pair, index: _case(
            index,
            alias_failure=(
                pair.contract_id == "conjecturer.turn.v6" and index == 0
            ),
        ),
    )

    for name, manifest, report, code in (
        (
            "repair-overclaim",
            zero_manifest,
            overclaim,
            "DOCTOR_REPORT_REPAIR_GRANT_EXCEEDED",
        ),
        (
            "unqualified",
            unqualified_manifest,
            unqualified,
            "DOCTOR_REPORT_PAIR_UNQUALIFIED",
        ),
    ):
        root = tmp_path / name
        root.mkdir()
        _write_required_report(root, manifest, report)
        harness = _scheduler_harness(root)
        before = _root_snapshot(root)
        calls = _forbid_bound_scheduler_work(monkeypatch, harness)
        with pytest.raises(RunManifestError) as caught:
            ops.run_scheduler(
                harness,
                SimpleNamespace(),
                cycles=1,
                run_manifest=manifest,
            )
        assert caught.value.code == code
        assert calls == []
        assert _root_snapshot(root) == before


def test_historical_v6_policy_absence_and_missing_root_fail_closed(
    tmp_path,
    monkeypatch,
):
    import deepreason.ops as ops

    manifest, _report = _qualified_manifest_and_report()
    payload = json.loads(manifest.canonical_bytes())
    payload.pop("production_qualification_policy")
    historical = RunManifest.model_validate(payload)
    root = tmp_path / "historical"
    root.mkdir()
    harness = _scheduler_harness(root)
    calls = _forbid_bound_scheduler_work(monkeypatch, harness)

    with pytest.raises(RunManifestError) as caught:
        ops.run_scheduler(
            harness,
            SimpleNamespace(),
            cycles=1,
            run_manifest=historical,
        )
    assert caught.value.code == "V6_PRODUCTION_QUALIFICATION_POLICY_REQUIRED"
    assert calls == []

    with pytest.raises(RunManifestError) as caught:
        require_v6_production_qualification(
            manifest,
            root=None,
            operation="full scheduler",
        )
    assert caught.value.code == "V6_PRODUCTION_QUALIFICATION_ROOT_REQUIRED"


def test_zero_cycles_and_pre_v6_never_inspect_qualification_report(
    tmp_path,
    monkeypatch,
):
    import deepreason.cli.doctor as doctor_module
    import deepreason.ops as ops

    manifest, _report = _qualified_manifest_and_report()
    calls = []
    _allow_scheduler_work(monkeypatch, calls)
    monkeypatch.setattr(
        doctor_module,
        "load_production_contract_report",
        _forbid(calls, "qualification report"),
    )
    config = SimpleNamespace(CONTROLLER=False, engine_profile="full")
    root = tmp_path / "no-report-inspection"
    root.mkdir()

    ops.run_scheduler(
        _scheduler_harness(root),
        config,
        cycles=0,
        run_manifest=manifest,
        stop_controller=object(),
    )
    for schema_version in range(1, 6):
        ops.run_scheduler(
            _scheduler_harness(root),
            config,
            cycles=1,
            run_manifest=SimpleNamespace(
                schema_version=schema_version,
                engine_profile="full",
                workload_profile="text",
            ),
            stop_controller=object(),
        )
    assert "qualification report" not in calls


def test_bound_and_explicit_manifest_launches_require_the_same_report(
    tmp_path,
    monkeypatch,
):
    import deepreason.ops as ops

    manifest, _report = _qualified_manifest_and_report()
    explicit_root = tmp_path / "explicit"
    bound_root = tmp_path / "bound"
    explicit_root.mkdir()
    bound_root.mkdir()
    write_run_manifest(manifest, bound_root / MANIFEST_NAME)

    for root, supplied in ((explicit_root, manifest), (bound_root, None)):
        harness = _scheduler_harness(root)
        calls = _forbid_bound_scheduler_work(monkeypatch, harness)
        with pytest.raises(RunManifestError) as caught:
            ops.run_scheduler(
                harness,
                SimpleNamespace(),
                cycles=1,
                run_manifest=supplied,
            )
        assert caught.value.code == "DOCTOR_REPORT_MISSING"
        assert calls == []


def test_conflicting_explicit_and_bound_manifests_fail_before_qualification(
    tmp_path,
    monkeypatch,
):
    import deepreason.cli.doctor as doctor_module
    import deepreason.ops as ops
    from tests.test_cli_production_doctor_v6 import _manifest, _qualified_report

    bound_manifest = _manifest()
    explicit_manifest = _manifest(route_profiles={"conjecturer": "compact"})
    assert explicit_manifest.sha256 != bound_manifest.sha256
    root = tmp_path / "conflicting-explicit-and-bound"
    root.mkdir()
    write_run_manifest(bound_manifest, root / MANIFEST_NAME)
    _write_required_report(
        root,
        explicit_manifest,
        _qualified_report(explicit_manifest),
    )
    harness = _scheduler_harness(root)
    before = _root_snapshot(root)
    calls = _forbid_bound_scheduler_work(monkeypatch, harness)
    monkeypatch.setattr(
        doctor_module,
        "load_production_contract_report",
        _forbid(calls, "qualification report loader"),
    )
    monkeypatch.setattr(
        doctor_module,
        "validate_production_contract_qualification",
        _forbid(calls, "qualification report validator"),
    )

    with pytest.raises(RunManifestError) as caught:
        ops.run_scheduler(
            harness,
            SimpleNamespace(),
            cycles=1,
            token_budget=None,
            run_manifest=explicit_manifest,
        )

    assert caught.value.code == "RUN_MANIFEST_CONFLICT"
    assert calls == []
    assert _root_snapshot(root) == before


def test_matching_explicit_and_bound_manifest_allows_qualified_scheduler(
    tmp_path,
    monkeypatch,
):
    import deepreason.ops as ops

    manifest, report = _qualified_manifest_and_report()
    root = tmp_path / "matching-explicit-and-bound"
    root.mkdir()
    write_run_manifest(manifest, root / MANIFEST_NAME)
    _write_required_report(root, manifest, report)
    calls = []
    _allow_scheduler_work(monkeypatch, calls)

    result, meter, accounting = ops.run_scheduler(
        _scheduler_harness(root),
        SimpleNamespace(CONTROLLER=False, engine_profile="full"),
        cycles=1,
        token_budget=None,
        run_manifest=manifest,
        stop_controller=object(),
    )

    assert result == {"cycles": 1}
    assert meter.budget is None
    assert accounting["metered_tokens"] == 0
    assert calls == ["manifest preflight", "adapter", "scheduler", ("run", 1)]


def test_release_disable_precedes_qualification_report_inspection(
    tmp_path,
    monkeypatch,
):
    import deepreason.cli.doctor as doctor_module
    import deepreason.ops as ops

    manifest, _report = _qualified_manifest_and_report()
    root = tmp_path / "release-disabled"
    root.mkdir()
    calls = _forbid_bound_scheduler_work(monkeypatch, _scheduler_harness(root))
    monkeypatch.setattr(
        doctor_module,
        "load_production_contract_report",
        _forbid(calls, "qualification report"),
    )
    _disable_v6(monkeypatch)

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        ops.run_scheduler(
            _scheduler_harness(root),
            SimpleNamespace(),
            cycles=1,
            run_manifest=manifest,
        )
    assert calls == []


def test_qualification_loader_and_validator_run_once_per_scheduler_invocation(
    tmp_path,
    monkeypatch,
):
    import deepreason.cli.doctor as doctor_module
    import deepreason.ops as ops

    manifest, report = _qualified_manifest_and_report()
    root = tmp_path / "qualification-once"
    root.mkdir()
    _write_required_report(root, manifest, report)
    counts = {"load": 0, "validate": 0}
    original_load = doctor_module.load_production_contract_report
    original_validate = doctor_module.validate_production_contract_qualification

    def load_once(path):
        counts["load"] += 1
        return original_load(path)

    def validate_once(loaded, supplied_manifest):
        counts["validate"] += 1
        return original_validate(loaded, supplied_manifest)

    monkeypatch.setattr(doctor_module, "load_production_contract_report", load_once)
    monkeypatch.setattr(
        doctor_module,
        "validate_production_contract_qualification",
        validate_once,
    )
    calls = []
    _allow_scheduler_work(monkeypatch, calls)
    ops.run_scheduler(
        _scheduler_harness(root),
        SimpleNamespace(CONTROLLER=False, engine_profile="full"),
        cycles=1,
        run_manifest=manifest,
        stop_controller=object(),
    )

    assert counts == {"load": 1, "validate": 1}


def test_bound_v6_manifest_is_effective_when_scheduler_argument_is_omitted(
    tmp_path, monkeypatch
):
    import deepreason.ops as ops

    _disable_v6(monkeypatch)
    harness, config = _bound_v6_scheduler_harness(tmp_path)
    before = _root_snapshot(harness.root)
    calls = _forbid_bound_scheduler_work(monkeypatch, harness)

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        ops.run_scheduler(harness, config, cycles=1, token_budget=1)

    assert calls == []
    assert _root_snapshot(harness.root) == before


def test_inaccessible_bound_manifest_fails_closed_before_scheduler_work(
    tmp_path, monkeypatch
):
    import deepreason.ops as ops

    harness, config = _bound_v6_scheduler_harness(tmp_path)
    manifest_path = harness.root / MANIFEST_NAME
    before = _root_snapshot(harness.root)
    calls = _forbid_bound_scheduler_work(monkeypatch, harness)
    original_lstat = Path.lstat

    def inaccessible(path):
        if path == manifest_path:
            raise PermissionError("bound manifest inspection denied")
        return original_lstat(path)

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "lstat", inaccessible)
        with pytest.raises(PermissionError, match="bound manifest inspection denied"):
            ops.run_scheduler(harness, config, cycles=1, token_budget=1)

    assert calls == []
    assert _root_snapshot(harness.root) == before


def test_inaccessible_bound_manifest_is_not_bypassed_by_explicit_manifest(
    tmp_path, monkeypatch
):
    import deepreason.cli.doctor as doctor_module
    import deepreason.ops as ops

    harness, config = _bound_v6_scheduler_harness(tmp_path)
    manifest_path = harness.root / MANIFEST_NAME
    explicit_manifest = load_run_manifest(manifest_path)
    before = _root_snapshot(harness.root)
    calls = _forbid_bound_scheduler_work(monkeypatch, harness)
    monkeypatch.setattr(
        doctor_module,
        "load_production_contract_report",
        _forbid(calls, "qualification report loader"),
    )
    monkeypatch.setattr(
        doctor_module,
        "validate_production_contract_qualification",
        _forbid(calls, "qualification report validator"),
    )
    original_lstat = Path.lstat

    def inaccessible(path):
        if path == manifest_path:
            raise PermissionError("bound manifest inspection denied")
        return original_lstat(path)

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "lstat", inaccessible)
        with pytest.raises(PermissionError, match="bound manifest inspection denied"):
            ops.run_scheduler(
                harness,
                config,
                cycles=1,
                token_budget=None,
                run_manifest=explicit_manifest,
            )

    assert calls == []
    assert _root_snapshot(harness.root) == before


def test_invalid_bound_manifest_fails_closed_before_scheduler_work(tmp_path, monkeypatch):
    import deepreason.ops as ops

    harness, config = _bound_v6_scheduler_harness(tmp_path)
    (harness.root / MANIFEST_NAME).write_bytes(b"{")
    before = _root_snapshot(harness.root)
    calls = _forbid_bound_scheduler_work(monkeypatch, harness)

    with pytest.raises(ValueError, match="INVALID_RUN_MANIFEST"):
        ops.run_scheduler(harness, config, cycles=1, token_budget=1)

    assert calls == []
    assert _root_snapshot(harness.root) == before


def test_disabled_v6_launch_policy_precedes_direct_scheduler_work(monkeypatch):
    _disable_v6(monkeypatch)

    _assert_scheduler_policy_rejected(
        monkeypatch,
        SimpleNamespace(schema_version=6, engine_profile="full"),
        "V6_LAUNCH_DISABLED",
    )


def test_invalid_v6_release_policy_precedes_direct_scheduler_work(tmp_path, monkeypatch):
    policy = tmp_path / "invalid-release-policy.json"
    policy.write_text("{", encoding="utf-8")
    monkeypatch.delenv(V6_LAUNCH_DISABLE_ENV, raising=False)
    monkeypatch.setenv(RELEASE_POLICY_ENV, str(policy))

    _assert_scheduler_policy_rejected(
        monkeypatch,
        SimpleNamespace(schema_version=6, engine_profile="full"),
        "V6_LAUNCH_POLICY_INVALID",
    )


def test_direct_scheduler_allows_enabled_explicit_v6_manifest(tmp_path, monkeypatch):
    import deepreason.llm.adapter as adapter_module
    import deepreason.ops as ops
    import deepreason.run_manifest as run_manifest_module
    import deepreason.scheduler.scheduler as scheduler_module

    policy = tmp_path / "enabled-release-policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema": RELEASE_POLICY_SCHEMA,
                "v6_launches_enabled": True,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv(V6_LAUNCH_DISABLE_ENV, raising=False)
    monkeypatch.setenv(RELEASE_POLICY_ENV, str(policy))
    manifest = SimpleNamespace(
        schema_version=6,
        engine_profile="full",
        workload_profile="text",
    )

    calls = []
    captured = {}

    class Adapter:
        def has_role(self, role):
            return role == "conjecturer"

    class Scheduler:
        def __init__(self, *_args, **_kwargs):
            calls.append("scheduler")

        def run(self, cycles, **_kwargs):
            calls.append(("run", cycles))
            return {"cycles": cycles}

    def preflight(*_args, **_kwargs):
        calls.append("manifest preflight")

    def build_adapter(*_args, **_kwargs):
        calls.append("adapter")
        captured["meter"] = _kwargs["meter"]
        return Adapter()

    monkeypatch.setattr(run_manifest_module, "preflight_harness", preflight)
    monkeypatch.setattr(adapter_module, "build_adapter", build_adapter)
    monkeypatch.setattr(scheduler_module, "Scheduler", Scheduler)
    monkeypatch.setattr(ops, "make_embedder", lambda *_args: None)
    monkeypatch.setattr(ops, "make_research_service", lambda *_args: None)
    monkeypatch.setattr(ops.importlib.util, "find_spec", lambda _name: None)

    result, meter, accounting = ops.run_scheduler(
        SimpleNamespace(blobs=object(), log=SimpleNamespace(read=lambda: ())),
        SimpleNamespace(CONTROLLER=False, engine_profile="full"),
        cycles=0,
        run_manifest=manifest,
        stop_controller=object(),
    )

    assert result == {"cycles": 0}
    assert meter is captured["meter"]
    assert meter.budget is None
    assert meter.snapshot() == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total": 0,
        "budget": None,
        "calls": 0,
        "reserved": 0,
    }
    assert accounting["metered_tokens"] == 0
    assert accounting["delta"] == 0
    assert calls == ["manifest preflight", "adapter", "scheduler", ("run", 0)]


def _cli_args(root, *, dry_run: bool):
    return SimpleNamespace(
        budget="1",
        root=str(root),
        run_manifest=str(root.parent / "v6-manifest.json"),
        config=None,
        problem=None,
        dry_run=dry_run,
        experimental_v5=False,
        token_budget=1,
    )


def _install_cli_v6_manifest(monkeypatch, manifest):
    import deepreason.ops as ops
    import deepreason.run_manifest as run_manifest_module

    monkeypatch.setattr(run_manifest_module, "load_run_manifest", lambda _path: manifest)
    monkeypatch.setattr(
        run_manifest_module,
        "config_from_run_manifest",
        lambda _manifest: SimpleNamespace(),
    )
    monkeypatch.setattr(
        ops,
        "require_full_engine",
        lambda *_args, **_kwargs: None,
    )
    return run_manifest_module


def test_cli_v6_launch_policy_precedes_root_binding(tmp_path, monkeypatch, capsys):
    from deepreason.cli import main as cli_module
    import deepreason.locking as locking_module

    _disable_v6(monkeypatch)
    root = tmp_path / "blocked-cli-root"
    manifest = SimpleNamespace(
        schema_version=6,
        engine_profile="full",
        sha256="a" * 64,
    )
    run_manifest_module = _install_cli_v6_manifest(monkeypatch, manifest)
    calls = []
    monkeypatch.setattr(
        run_manifest_module,
        "bind_run_manifest",
        _forbid(calls, "manifest binding"),
    )
    monkeypatch.setattr(
        locking_module,
        "operator_locks",
        _forbid(calls, "operator lock"),
    )

    assert cli_module._cmd_run(_cli_args(root, dry_run=False)) == 1
    assert "V6_LAUNCH_DISABLED" in capsys.readouterr().err
    assert calls == []
    assert not root.exists()


def test_execute_bound_run_v6_launch_policy_precedes_harness(
    tmp_path, monkeypatch, capsys
):
    from deepreason.cli import main as cli_module

    _disable_v6(monkeypatch)
    root = tmp_path / "blocked-direct-cli-root"
    calls = []
    monkeypatch.setattr(cli_module, "Harness", _forbid(calls, "harness"))

    result = cli_module._execute_bound_run(
        SimpleNamespace(problem=None, experimental_v5=False, token_budget=1),
        SimpleNamespace(schema_version=6),
        SimpleNamespace(),
        root,
        1,
    )

    assert result == 1
    assert "V6_LAUNCH_DISABLED" in capsys.readouterr().err
    assert calls == []
    assert not root.exists()


def test_cli_dry_run_remains_available_while_v6_is_disabled(
    tmp_path, monkeypatch, capsys
):
    from deepreason.cli import main as cli_module
    import deepreason.locking as locking_module

    _disable_v6(monkeypatch)
    root = tmp_path / "dry-run-root"
    manifest = SimpleNamespace(
        schema_version=6,
        engine_profile="full",
        sha256="b" * 64,
    )
    run_manifest_module = _install_cli_v6_manifest(monkeypatch, manifest)
    calls = []
    monkeypatch.setattr(
        run_manifest_module,
        "bind_run_manifest",
        _forbid(calls, "manifest binding"),
    )
    monkeypatch.setattr(
        run_manifest_module,
        "render_role_matrix",
        lambda _manifest: "dry-run role matrix",
    )
    monkeypatch.setattr(
        locking_module,
        "operator_locks",
        _forbid(calls, "operator lock"),
    )

    assert cli_module._cmd_run(_cli_args(root, dry_run=True)) == 0
    assert "dry-run role matrix" in capsys.readouterr().out
    assert calls == []
    assert not root.exists()
