"""G01: text-run admission is V6-only and precedes every stateful seam."""

from __future__ import annotations

import inspect
import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import deepreason.application.text_runs as text_runs_module
from deepreason.application import (
    CancelTextRunIntentV1,
    ContinueTextRunIntentV1,
    InspectTextRunIntentV1,
    StartTextRunIntentV1,
)
from deepreason.application.intents import (
    continue_text_run_intent,
    start_text_run_intent,
)
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
)
from deepreason.canonical import canonical_json
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
)
from deepreason.run_manifest import (
    RunManifestError,
    bind_run_manifest,
    write_run_manifest,
)
from deepreason.runtime.launch_policy import require_v6_launch_allowed
from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem
from tests.test_run_input_v6_commitments import (
    PROBLEM_ID,
    _bind_v1,
    _bind_v2,
    _commitment,
    _manifest,
    _spec,
    _write_qualification,
)


def _snapshot(root):
    if not root.exists():
        return None
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _manifest_path(tmp_path, manifest, name="manifest.json"):
    path, _sidecar = write_run_manifest(manifest, tmp_path / name)
    return path


def _intent(root, manifest_path, *, spec=None):
    return StartTextRunIntentV1(
        root=str(root),
        workload=spec or _spec(_commitment()),
        run_manifest_ref=str(manifest_path),
        budget={"cycles": 1, "token_budget": "unlimited"},
    )


def _forbid(calls, name):
    def forbidden(*_args, **_kwargs):
        calls.append(name)
        raise AssertionError(f"invalid admission reached {name}")

    return forbidden


class _ForbiddenLock:
    def __init__(self, calls):
        self.calls = calls

    def __enter__(self):
        self.calls.append("registry lock")
        raise AssertionError("invalid admission acquired the registry lock")

    def __exit__(self, *_args):  # pragma: no cover - __enter__ always fails
        return False


class _ForbiddenRegistry:
    def __init__(self, calls):
        self.calls = calls
        self.lock = _ForbiddenLock(calls)
        self.threads = {}

    def live(self, _root):
        self.calls.append("registry lookup")
        raise AssertionError("invalid admission reached worker lookup")


def _guarded_service(monkeypatch):
    import deepreason.harness as harness_module
    import deepreason.llm.adapter as adapter_module
    import deepreason.ops as ops_module
    import deepreason.run_manifest as run_manifest_module
    import deepreason.runtime.progress as progress_module
    import deepreason.scheduler.scheduler as scheduler_module

    calls = []
    service = TextRunApplicationService(_ForbiddenRegistry(calls))
    monkeypatch.setattr(
        text_runs_module, "operator_locks", _forbid(calls, "operator lock")
    )
    monkeypatch.setattr(
        text_runs_module.threading, "Thread", _forbid(calls, "worker")
    )
    monkeypatch.setattr(
        run_manifest_module,
        "bind_run_manifest",
        _forbid(calls, "manifest write"),
    )
    monkeypatch.setattr(
        progress_module, "_atomic_json", _forbid(calls, "application write")
    )
    monkeypatch.setattr(harness_module, "Harness", _forbid(calls, "harness"))
    monkeypatch.setattr(ops_module, "run_scheduler", _forbid(calls, "dispatch"))
    monkeypatch.setattr(
        adapter_module, "build_adapter", _forbid(calls, "adapter")
    )
    monkeypatch.setattr(
        adapter_module,
        "_endpoint_from_spec",
        _forbid(calls, "provider client"),
    )
    monkeypatch.setattr(
        scheduler_module, "Scheduler", _forbid(calls, "scheduler")
    )
    return service, calls


def _assert_unchanged(root, before, calls):
    assert calls == []
    assert _snapshot(root) == before


@pytest.mark.parametrize("schema_version", range(1, 6))
def test_raw_historical_manifest_is_rejected_before_all_application_seams(
    tmp_path, monkeypatch, schema_version
):
    root = tmp_path / f"run-v{schema_version}"
    manifest_path = tmp_path / f"historical-v{schema_version}.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "roles": {"conjecturer": [{"nested": "must-not-be-read"}]},
            }
        ),
        encoding="utf-8",
    )
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(RunManifestError) as caught:
        service.start(_intent(root, manifest_path))

    assert caught.value.code == "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert caught.value.rejected_version == schema_version
    _assert_unchanged(root, None, calls)


@pytest.mark.parametrize("operation", ("start", "continue", "cancel", "result"))
def test_missing_manifest_is_distinct_and_precedes_mutation(
    tmp_path, monkeypatch, operation
):
    root = tmp_path / operation
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(RunManifestError) as caught:
        if operation == "start":
            service.start(_intent(root, tmp_path / "missing-manifest.json"))
        elif operation == "continue":
            service.continue_run(
                ContinueTextRunIntentV1(
                    root=str(root),
                    budget={"cycles": 1, "token_budget": "unlimited"},
                )
            )
        elif operation == "cancel":
            service.cancel(CancelTextRunIntentV1(root=str(root)))
        else:
            service.result(InspectTextRunIntentV1(root=str(root)))

    assert caught.value.code == "MANIFEST_FILE_UNAVAILABLE"
    assert caught.value.code != "UNSUPPORTED_RUN_MANIFEST_VERSION"
    _assert_unchanged(root, None, calls)


@pytest.mark.parametrize("operation", ("continue", "cancel", "result"))
def test_bound_historical_manifest_rejects_before_alternate_operation_seams(
    tmp_path, monkeypatch, operation
):
    root = tmp_path / operation
    root.mkdir()
    (root / "run-manifest.json").write_text(
        '{"schema_version":5,"nested":{"secret":"not-interpreted"}}',
        encoding="utf-8",
    )
    before = _snapshot(root)
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(RunManifestError) as caught:
        if operation == "continue":
            service.continue_run(
                ContinueTextRunIntentV1(
                    root=str(root),
                    budget={"cycles": 1, "token_budget": "unlimited"},
                )
            )
        elif operation == "cancel":
            service.cancel(CancelTextRunIntentV1(root=str(root)))
        else:
            service.result(InspectTextRunIntentV1(root=str(root)))

    assert caught.value.code == "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert caught.value.rejected_version == 5
    _assert_unchanged(root, before, calls)


def test_v6_missing_run_input_fails_before_root_creation(tmp_path, monkeypatch):
    root = tmp_path / "missing-input"
    manifest = _manifest(6, "a" * 64)
    manifest_path = _manifest_path(tmp_path, manifest)
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(ValueError) as caught:
        service.start(_intent(root, manifest_path))

    assert getattr(caught.value, "code", None) == "RUN_INPUT_FILE_UNAVAILABLE"
    _assert_unchanged(root, None, calls)


def test_v6_rejects_run_input_v1_without_translation(tmp_path, monkeypatch):
    root = tmp_path / "input-v1"
    frozen = _bind_v1(root, _commitment())
    manifest = _manifest(6, frozen.run_input_digest)
    manifest_path = _manifest_path(tmp_path, manifest)
    before = _snapshot(root)
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(ValueError) as caught:
        service.start(_intent(root, manifest_path))

    assert getattr(caught.value, "code", None) == "RUN_INPUT_SCHEMA_MISMATCH"
    _assert_unchanged(root, before, calls)


def test_v6_rejects_mismatched_input_digest(tmp_path, monkeypatch):
    root = tmp_path / "digest-mismatch"
    _bind_v2(root, _commitment())
    manifest = _manifest(6, "e" * 64)
    manifest_path = _manifest_path(tmp_path, manifest)
    before = _snapshot(root)
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(ValueError, match="RUN_INPUT_MISMATCH"):
        service.start(_intent(root, manifest_path))

    _assert_unchanged(root, before, calls)


def test_v6_rejects_mismatched_question(tmp_path, monkeypatch):
    root = tmp_path / "question-mismatch"
    commitment = _commitment()
    frozen = _bind_v2(root, commitment)
    manifest = _manifest(6, frozen.run_input_digest)
    manifest_path = _manifest_path(tmp_path, manifest)
    changed = ReasoningWorkloadSpec(
        problem=WorkloadProblem(
            id=PROBLEM_ID,
            description="A different question cannot reuse frozen authority.",
        ),
        criteria=(commitment,),
        allow_rubric=False,
    )
    before = _snapshot(root)
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(ValueError, match="RUN_INPUT_MISMATCH"):
        service.start(_intent(root, manifest_path, spec=changed))

    _assert_unchanged(root, before, calls)


def test_v6_rejects_mismatched_dossier(tmp_path, monkeypatch):
    root = tmp_path / "dossier-mismatch"
    commitment = _commitment()
    frozen = _bind_v2(root, commitment)
    manifest = _manifest(6, frozen.run_input_digest)
    manifest_path = _manifest_path(tmp_path, manifest)
    other = EvidenceDossierV1.create(
        problem_ref=PROBLEM_ID,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="different dossier",
            acquisition_method="mismatch fixture",
        ),
    )
    (root / "evidence-dossier.json").write_bytes(
        canonical_json(other.model_dump(mode="json", by_alias=True))
    )
    (root / "evidence-dossier.sha256").write_text(
        other.dossier_digest + "\n", encoding="ascii"
    )
    before = _snapshot(root)
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(ValueError) as caught:
        service.start(_intent(root, manifest_path))

    assert getattr(caught.value, "code", None) == "RUN_INPUT_DOSSIER_MISMATCH"
    _assert_unchanged(root, before, calls)


def test_v6_rejects_missing_production_qualification(tmp_path, monkeypatch):
    root = tmp_path / "missing-qualification"
    frozen = _bind_v2(root, _commitment())
    manifest = _manifest(6, frozen.run_input_digest)
    manifest_path = _manifest_path(tmp_path, manifest)
    before = _snapshot(root)
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(RunManifestError) as caught:
        service.start(_intent(root, manifest_path))

    assert caught.value.code == "DOCTOR_REPORT_MISSING"
    _assert_unchanged(root, before, calls)


def test_v6_rejects_mismatched_production_qualification(tmp_path, monkeypatch):
    from tests.test_cli_production_doctor_v6 import _qualified_report

    root = tmp_path / "mismatched-qualification"
    frozen = _bind_v2(root, _commitment())
    manifest = _manifest(6, frozen.run_input_digest)
    foreign = _manifest(6, "f" * 64)
    _write_qualification(root, manifest, report=_qualified_report(foreign))
    manifest_path = _manifest_path(tmp_path, manifest)
    before = _snapshot(root)
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(RunManifestError) as caught:
        service.start(_intent(root, manifest_path))

    assert caught.value.code == "DOCTOR_REPORT_MANIFEST_MISMATCH"
    _assert_unchanged(root, before, calls)


def test_v6_rejects_conflicting_bound_manifest_before_lock(tmp_path, monkeypatch):
    root = tmp_path / "manifest-conflict"
    frozen = _bind_v2(root, _commitment())
    bound = _manifest(6, frozen.run_input_digest)
    bind_run_manifest(bound, root)
    requested = _manifest(6, "f" * 64)
    requested_path = _manifest_path(tmp_path, requested)
    before = _snapshot(root)
    service, calls = _guarded_service(monkeypatch)

    with pytest.raises(RunManifestError) as caught:
        service.start(_intent(root, requested_path))

    assert caught.value.code == "RUN_MANIFEST_CONFLICT"
    _assert_unchanged(root, before, calls)


def test_experimental_v5_is_absent_from_every_application_constructor(tmp_path):
    payload = {
        "root": str(tmp_path / "run"),
        "workload": _spec(_commitment()),
        "run_manifest_ref": str(tmp_path / "manifest.json"),
        "budget": {"cycles": 1, "token_budget": "unlimited"},
    }
    with pytest.raises(ValidationError, match="extra_forbidden"):
        StartTextRunIntentV1.model_validate({**payload, "experimental_v5": False})
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ContinueTextRunIntentV1.model_validate(
            {
                "root": payload["root"],
                "budget": payload["budget"],
                "experimental_v5": True,
            }
        )
    with pytest.raises(TypeError):
        start_text_run_intent(
            root=payload["root"],
            workload=payload["workload"],
            run_manifest_ref=payload["run_manifest_ref"],
            cycles=1,
            token_budget="unlimited",
            experimental_v5=False,
        )
    with pytest.raises(TypeError):
        continue_text_run_intent(
            root=payload["root"],
            cycles=1,
            token_budget="unlimited",
            experimental_v5=True,
        )
    assert "experimental_v5" not in inspect.signature(
        TextRunApplicationService._launch
    ).parameters
    assert "experimental_v5" not in inspect.signature(
        TextRunApplicationService._worker
    ).parameters


@pytest.mark.parametrize("schema_version", range(1, 6))
def test_require_v6_launch_allowed_fails_closed_for_non_v6(schema_version):
    with pytest.raises(RunManifestError) as caught:
        require_v6_launch_allowed(
            SimpleNamespace(schema_version=schema_version),
            operation="application admission test",
        )
    assert caught.value.code == "V6_RUN_MANIFEST_REQUIRED"


def test_exact_v6_admission_reaches_worker_seam_without_provider_call(
    tmp_path, monkeypatch
):
    import deepreason.ops as ops_module

    root = tmp_path / "accepted-v6"
    commitment = _commitment()
    frozen = _bind_v2(root, commitment)
    manifest = _manifest(6, frozen.run_input_digest)
    _write_qualification(root, manifest)
    manifest_path = _manifest_path(tmp_path, manifest)
    calls = []

    class LockProbe:
        released = False

        def release(self):
            self.released = True

    lock = LockProbe()

    class ThreadProbe:
        def __init__(self, *, target, kwargs, name, daemon):
            self.target = target
            self.kwargs = kwargs
            self.name = name
            self.daemon = daemon
            self.started = False
            calls.append("worker constructed")

        def start(self):
            self.started = True
            calls.append("worker started")

        def is_alive(self):
            return self.started

    def operator_locks(_root, *, owner, blocking):
        assert owner == "run" and blocking is False
        calls.append("operator lock")
        return lock

    monkeypatch.setattr(text_runs_module, "operator_locks", operator_locks)
    monkeypatch.setattr(text_runs_module.threading, "Thread", ThreadProbe)
    monkeypatch.setattr(
        ops_module,
        "run_scheduler",
        lambda *_args, **_kwargs: pytest.fail(
            "provider/scheduler work must remain behind the worker seam"
        ),
    )
    service = TextRunApplicationService(TextRunWorkerRegistry())

    started = service.start(
        _intent(root, manifest_path, spec=_spec(commitment)),
        credential_checker=lambda _manifest: [],
    )

    thread = service.registry.threads[str(root.resolve())]
    assert started.manifest_digest == manifest.sha256
    assert thread.target == service._worker
    assert thread.kwargs["manifest"] == manifest
    assert thread.started is True
    assert calls == ["operator lock", "worker constructed", "worker started"]
    assert (root / "run-manifest.json").read_bytes() == manifest.canonical_bytes()
    assert (root / "run-request.json").exists()
    assert (root / "text-workload.json").exists()
    assert (root / "progress.jsonl").exists()
    thread.kwargs["locks"].release()
    assert lock.released is True
