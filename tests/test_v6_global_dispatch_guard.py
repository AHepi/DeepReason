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
    SchoolExecutionPolicyV1,
    ScratchAuthoringPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.runtime.launch_policy import (
    RELEASE_POLICY_ENV,
    RELEASE_POLICY_SCHEMA,
    V6_LAUNCH_DISABLE_ENV,
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

    prompt, _contract, _lease, maximum = adapter.preview_request(
        "conjecturer", "PACK", ConjecturerOutput
    )
    assert "PACK" in prompt
    assert maximum >= 0

    with pytest.raises(WorkflowAuthorizationError, match="bound transaction"):
        adapter.call("conjecturer", "PACK", ConjecturerOutput)
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
    import deepreason.scheduler.scheduler as scheduler_module

    calls = []
    monkeypatch.setattr(harness.log, "read", _forbid(calls, "event log"))
    monkeypatch.setattr(ops, "require_full_engine", _forbid(calls, "engine preflight"))
    monkeypatch.setattr(budget_module, "TokenMeter", _forbid(calls, "token meter"))
    monkeypatch.setattr(adapter_module, "build_adapter", _forbid(calls, "adapter"))
    monkeypatch.setattr(scheduler_module, "Scheduler", _forbid(calls, "scheduler"))
    return calls


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
