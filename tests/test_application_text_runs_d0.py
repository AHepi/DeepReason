"""D0: one typed application boundary for CLI and MCP text runs."""

from __future__ import annotations

import inspect
import json
import threading
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from deepreason import mcp_server
from deepreason.application import (
    ContinueTextRunIntentV1,
    InspectTextRunIntentV1,
    RunStartedV1,
    StartTextRunIntentV1,
    TEXT_RUN_SERVICE,
    TEXT_RUN_WORKERS,
    TextRunTerminalResultV1,
)
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
)
from deepreason.cli import main as cli_module
from deepreason.cli.main import main as cli_main
from deepreason.canonical import canonical_json
from deepreason.harness import Harness
from deepreason.locking import operator_locks
from deepreason.run_manifest import bind_run_manifest, write_run_manifest
from deepreason.workloads.text import spec_from_text


def _prepared_cli_manifest(root, text):
    from deepreason.evidence import (
        AttachedSourceProvenanceV1,
        EvidenceDossierV1,
        RunInputManifestV2,
        RunInputProblemV2,
        bind_run_input,
    )
    from tests.test_run_input_v6_commitments import _manifest as compile_v6_manifest

    spec = spec_from_text(text)
    dossier = EvidenceDossierV1.create(
        problem_ref=spec.problem.id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="G02 CLI fixture",
            acquisition_method="test preparation",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=spec.problem.id,
            description=spec.problem.description,
            criteria=spec.criteria,
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    manifest = compile_v6_manifest(6, run_input.run_input_digest)
    manifest_path, _ = bind_run_manifest(manifest, root)
    return manifest, manifest_path


def _install_public_preparation(monkeypatch, root, text, manifest_path):
    class PreparedService:
        def prepare(self, request):
            assert request.question == text
            return SimpleNamespace(
                root=str(root),
                managed_run_id=root.name,
                run_manifest_ref=str(manifest_path),
                workload=spec_from_text(text),
                budget=request.budget,
            )

    monkeypatch.setattr(
        "deepreason.preparation.RunPreparationService", PreparedService
    )
    monkeypatch.setattr(mcp_server, "_preparation_service", PreparedService)
    monkeypatch.setattr(mcp_server, "_require_readiness", lambda: None)


def test_start_intent_is_strict_and_has_no_client_authority_fields(tmp_path):
    spec = spec_from_text("Why should clients share one application service?")
    payload = {
        "root": str(tmp_path / "run"),
        "workload": spec,
        "run_manifest_ref": str(tmp_path / "manifest.json"),
        "budget": {"cycles": 1, "token_budget": "unlimited"},
    }

    with pytest.raises(ValidationError, match="extra_forbidden"):
        StartTextRunIntentV1.model_validate(
            {**payload, "route": "model-authored"}
        )
    with pytest.raises(ValidationError, match="extra_forbidden"):
        StartTextRunIntentV1.model_validate(
            {**payload, "status": "accepted"}
        )
    with pytest.raises(ValidationError):
        StartTextRunIntentV1.model_validate(
            {**payload, "budget": {"cycles": True, "token_budget": 10}}
        )
    with pytest.raises(ValidationError, match="extra_forbidden"):
        StartTextRunIntentV1.model_validate(
            {**payload, "experimental_v5": False}
        )
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ContinueTextRunIntentV1.model_validate(
            {
                "root": str(tmp_path / "run"),
                "budget": {"cycles": 1, "token_budget": "unlimited"},
                "experimental_v5": True,
            }
        )

    schema = json.dumps(StartTextRunIntentV1.model_json_schema(), sort_keys=True)
    assert all(
        forbidden not in schema
        for forbidden in (
            "route",
            "status",
            "raw_control",
            "guard_override",
            "experimental_v5",
        )
    )
    assert "experimental_v5" not in json.dumps(
        ContinueTextRunIntentV1.model_json_schema(), sort_keys=True
    )


def test_cli_and_mcp_compile_the_same_start_intent(
    tmp_path, monkeypatch, capsys
):
    root = tmp_path / "same-root"
    text = "Why should equivalent clients produce equivalent authority?"
    manifest, manifest_path = _prepared_cli_manifest(root, text)
    _install_public_preparation(monkeypatch, root, text, manifest_path)
    captured = []

    def fake_start(intent, **_kwargs):
        captured.append(intent)
        return RunStartedV1(
            root=str(root.resolve()), manifest_digest=manifest.sha256
        )

    monkeypatch.setattr(TEXT_RUN_SERVICE, "start", fake_start)
    monkeypatch.setattr(TEXT_RUN_SERVICE, "wait", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "result",
        lambda _intent: TextRunTerminalResultV1(
            lifecycle="completed",
            payload={
                "schema": "deepreason-run-result-v1",
                "state": "completed",
                "workload": "text",
            },
        ),
    )

    mcp_server._start_run(
        {
            "question": text,
            "budget": {"cycles": 12, "token_budget": 200_000},
        }
    )
    assert (
        cli_main(
            [
                "reason",
                text,
                "--cycles",
                "12",
                "--token-budget",
                "200000",
            ]
        )
        == 0
    )

    assert len(captured) == 2
    assert captured[0] == captured[1]
    assert json.loads(capsys.readouterr().out)["state"] == "completed"


@pytest.mark.parametrize(
    ("state", "verification", "expected"),
    [
        ("completed", None, 0),
        ("cancelled", None, 3),
        ("failed", None, 4),
        (
            "completed",
            {"integrity_valid": False, "security_valid": True},
            5,
        ),
    ],
)
def test_synchronous_cli_preserves_state_and_uses_terminal_exit_contract(
    tmp_path, monkeypatch, capsys, state, verification, expected
):
    root = tmp_path / state
    text = "Which terminal state controls automation?"
    manifest, manifest_path = _prepared_cli_manifest(root, text)
    _install_public_preparation(monkeypatch, root, text, manifest_path)
    payload = {
        "schema": "deepreason-run-result-v1",
        "state": state,
        "workload": "text",
    }
    if verification is not None:
        payload["verification"] = verification
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "start",
        lambda *_args, **_kwargs: RunStartedV1(
            root=str(root.resolve()), manifest_digest=manifest.sha256
        ),
    )
    monkeypatch.setattr(TEXT_RUN_SERVICE, "wait", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "result",
        lambda _intent: TextRunTerminalResultV1(
            lifecycle=state, payload=payload
        ),
    )

    exit_code = cli_main(
        [
            "reason",
            text,
            "--cycles",
            "1",
        ]
    )

    assert exit_code == expected
    assert json.loads(capsys.readouterr().out)["state"] == state


def test_synchronous_cli_returns_unknown_terminal_exit_for_invalid_result(
    tmp_path, monkeypatch, capsys
):
    root = tmp_path / "invalid"
    text = "Can an unknown terminal be reported as success?"
    manifest, manifest_path = _prepared_cli_manifest(root, text)
    _install_public_preparation(monkeypatch, root, text, manifest_path)
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "start",
        lambda *_args, **_kwargs: RunStartedV1(
            root=str(root.resolve()), manifest_digest=manifest.sha256
        ),
    )
    monkeypatch.setattr(TEXT_RUN_SERVICE, "wait", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "result",
        lambda _intent: (_ for _ in ()).throw(ValueError("RUN_RESULT_INVALID")),
    )

    assert (
        cli_main(
            [
                "reason",
                text,
                "--cycles",
                "1",
            ]
        )
        == 6
    )
    assert "RUN_RESULT_INVALID" in capsys.readouterr().err


def test_outstanding_work_projection_reads_replay_state_without_reducing(
    tmp_path, monkeypatch
):
    from tests.test_workflow_control_replay_c1 import _planned

    harness = Harness(tmp_path)
    _initial, planned = _planned()
    work = planned.work_orders[0]
    harness.record_control_transition(planned.decisions[0], work_order=work)
    harness.record_control_transition(planned.decisions[1])
    monkeypatch.setattr(
        "deepreason.workflow.reducer.reduce_conjecture",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("projection must not rerun reducer")
        ),
    )

    projection = TEXT_RUN_SERVICE.inspect_outstanding_work(tmp_path)

    assert projection.process_digest == harness.workflow_state.digest
    assert projection.last_control_seq == max(harness.workflow_state.event_seqs)
    assert len(projection.work) == 1
    item = projection.work[0]
    assert item.work_order_id == work.id
    assert item.recovery == "issued"
    assert item.route_digest == work.route_lease.route_sha256
    assert item.contract_id == work.contract_id
    assert item.reserved_tokens == planned.state.reserved_tokens
    assert item.provider_calls_limit == work.capability_grant.max_provider_calls
    status = TEXT_RUN_SERVICE.inspect(
        InspectTextRunIntentV1(root=str(tmp_path))
    ).presentation_payload()
    assert status["outstanding_work"] == projection.presentation_payload()


def test_outstanding_work_projection_accepts_v6_transaction_ids(tmp_path):
    from deepreason.llm.budget import TokenMeter
    from deepreason.workflow.transaction_service import InquiryTransactionService
    from tests.test_v6_transaction_qualification import _manifest, _prepare

    manifest = _manifest()
    harness = Harness(tmp_path)
    service = InquiryTransactionService(harness, manifest, TokenMeter(1_000))
    preparation = _prepare(service, manifest, trigger="cancellation-inspection")

    projection = TEXT_RUN_SERVICE.inspect_outstanding_work(tmp_path)

    assert projection.process_digest == harness.workflow_state.digest
    assert [item.work_order_id for item in projection.work] == [preparation.id]
    assert projection.work[0].recovery == "prepared"
    assert projection.work[0].contract_id == "conjecturer.turn.v6"
    assert projection.work[0].reserved_tokens == 0


def test_worker_harness_constructor_failure_releases_operator_lock(tmp_path):
    import deepreason.harness as harness_module
    from tests.test_run_input_v6_commitments import (
        _bind_v2,
        _commitment,
        _manifest,
        _spec,
        _write_qualification,
    )

    root = tmp_path / "constructor-failure"
    commitment = _commitment()
    frozen = _bind_v2(root, commitment)
    manifest = _manifest(6, frozen.run_input_digest)
    manifest_path, _ = write_run_manifest(manifest, tmp_path / "manifest.json")
    _write_qualification(root, manifest)
    service = TextRunApplicationService(TextRunWorkerRegistry())
    original_init = Harness.__init__

    def fail_constructor(_self, *_args, **_kwargs):
        raise RuntimeError("constructor failed")

    with pytest.MonkeyPatch.context() as scoped:
        scoped.setattr(Harness, "__init__", fail_constructor)
        assert harness_module.Harness is Harness
        accepted = service.start(
            StartTextRunIntentV1(
                root=str(root),
                workload=_spec(commitment),
                run_manifest_ref=str(manifest_path),
                budget={"cycles": 1, "token_budget": "unlimited"},
            ),
            credential_checker=lambda _manifest: [],
        )
        worker = service.registry.threads[str(root.resolve())]
        service.wait(accepted.root)

        assert not worker.is_alive()
        assert service.registry.live(root) is None

    assert harness_module.Harness is Harness
    assert Harness.__init__ is original_init
    locks = operator_locks(root, owner="lock-release-test", blocking=False)
    locks.release()


def test_result_does_not_enter_recovery_while_process_local_worker_is_alive(
    tmp_path, monkeypatch
):
    import deepreason.harness as harness_module
    from deepreason.runtime import progress as progress_module
    from deepreason.runtime import terminal_authority
    from tests.test_v6_resumed_terminal_revalidation import (
        _forbid_dispatch,
        _start_converged_run,
    )

    root, manifest, _initial_service, scheduler_calls, epoch_zero = (
        _start_converged_run(tmp_path, monkeypatch)
    )
    authority = Harness(root)
    commitment = authority.workflow_state.current_terminal_commitment
    assert commitment is not None
    expected, _draft = terminal_authority._expected_terminal_result(
        authority,
        manifest,
        commitment,
    )
    pending = terminal_authority._pending_terminal_result(expected)
    (root / "run-result.json").write_bytes(canonical_json(pending) + b"\n")
    (root / "REPLAY_VALIDATION.json").unlink()
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }

    registry = TextRunWorkerRegistry()
    original_live = registry.live

    class TrackingLock:
        def __init__(self):
            self._lock = threading.Lock()
            self.held = False

        def __enter__(self):
            self._lock.acquire()
            self.held = True
            return self

        def __exit__(self, _exc_type, _exc, _traceback):
            self.held = False
            self._lock.release()

    registry.lock = TrackingLock()

    def live_requires_registry_lock(bound_root):
        assert registry.lock.held
        return original_live(bound_root)

    monkeypatch.setattr(registry, "live", live_requires_registry_lock)
    service = TextRunApplicationService(registry)
    entered = threading.Event()
    release = threading.Event()

    def parked_worker():
        entered.set()
        assert release.wait(timeout=15)

    worker = threading.Thread(target=parked_worker, daemon=True)
    registry.put(root, worker)
    worker.start()
    assert entered.wait(timeout=15)
    _forbid_dispatch(monkeypatch)
    forbidden_calls: list[str] = []

    def forbidden(name):
        def fail(*_args, **_kwargs):
            forbidden_calls.append(name)
            raise AssertionError(f"live-worker result reached {name}")

        return fail

    try:
        with pytest.MonkeyPatch.context() as scoped:
            scoped.setattr(harness_module, "Harness", forbidden("harness"))
            scoped.setattr(
                terminal_authority,
                "recover_terminal_result",
                forbidden("terminal recovery"),
            )
            scoped.setattr(
                terminal_authority,
                "_terminal_commitment_lock",
                forbidden("terminal lock"),
            )
            scoped.setattr(
                terminal_authority,
                "_fresh_replay_validation",
                forbidden("replay regeneration"),
            )
            scoped.setattr(
                progress_module,
                "_atomic_json",
                forbidden("filesystem mutation"),
            )
            with pytest.raises(
                ValueError,
                match=(
                    "^RUN_RESULT_NOT_READY: terminalization remains active$"
                ),
            ):
                service.result(InspectTextRunIntentV1(root=str(root)))
    finally:
        release.set()
        worker.join(timeout=15)

    assert not worker.is_alive()
    assert original_live(root) is None
    assert forbidden_calls == []
    assert {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    } == before

    recovered = service.result(
        InspectTextRunIntentV1(root=str(root))
    ).payload
    assert recovered == epoch_zero
    assert recovered["terminal_commitment_ref"] == commitment.id
    assert scheduler_calls == [None]


def test_clients_have_only_thin_service_dispatch_and_one_registry():
    assert mcp_server._RUN_THREADS is TEXT_RUN_WORKERS.threads
    assert mcp_server._RUN_LOCK is TEXT_RUN_WORKERS.lock
    for function in (mcp_server._start_run, cli_module._cmd_reason):
        source = inspect.getsource(function)
        assert "run_scheduler" not in source
        assert "StopPolicy" not in source
        assert "Harness(" not in source
