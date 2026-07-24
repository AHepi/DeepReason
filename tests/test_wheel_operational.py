from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import threading

import pytest

from deepreason.cli.doctor import (
    _admit_production_probe_output,
    _production_probe_contract,
    production_contract_pairs,
)
from deepreason.llm.endpoints import OpenAICompatEndpoint
from deepreason.llm.wire import ReasoningConjecturerTurnWireV6
from deepreason.preparation import qualification_subject_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.runtime.continuation import prepare_continuation
from tests.test_v6_resumed_terminal_revalidation import (
    _continue_converged_run,
    _start_converged_run,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "scripts" / "wheel_loopback_sitecustomize.py"
SPEC = importlib.util.spec_from_file_location(
    "wheel_loopback_sitecustomize", FIXTURE_PATH
)
assert SPEC is not None and SPEC.loader is not None
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)
OPERATIONAL_SPEC = importlib.util.spec_from_file_location(
    "wheel_operational_smoke", ROOT / "scripts" / "wheel_operational_smoke.py"
)
assert OPERATIONAL_SPEC is not None and OPERATIONAL_SPEC.loader is not None
OPERATIONAL = importlib.util.module_from_spec(OPERATIONAL_SPEC)
OPERATIONAL_SPEC.loader.exec_module(OPERATIONAL)


def _profile(endpoint: str = "http://127.0.0.1:1/v1"):
    return ProviderProfileV1.create(
        provider="generic",
        endpoint=endpoint,
        model_id="deepreason-loopback-v6",
        model_revision="fixture-1",
        family="deterministic-loopback",
        context_window_tokens=1_000_000,
        maximum_completion_tokens=4_096,
        credential_env=FIXTURE.CREDENTIAL_ENV,
        output_mechanism="native_json_schema",
    )


def test_external_provider_satisfies_every_production_qualification_contract():
    manifest = qualification_subject_manifest(_profile())
    pairs = production_contract_pairs(manifest)
    assert len(pairs) == 4
    for pair in pairs:
        for case_index in range(20):
            contract, prompt = _production_probe_contract(
                manifest, pair, case_index
            )
            candidate = FIXTURE.response_for_schema(
                contract.model_json_schema(), prompt
            )
            wire = contract.validate_value(candidate)
            compiled = contract.compile(wire)
            _admit_production_probe_output(pair, compiled)


def test_external_provider_implements_real_openai_compatible_transport(tmp_path):
    state_path = tmp_path / "provider-counts.json"
    server = FIXTURE._ReusableLoopbackServer(
        ("127.0.0.1", 0), FIXTURE._handler(state_path)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = OpenAICompatEndpoint(
            f"http://127.0.0.1:{server.server_port}/v1",
            "deepreason-loopback-v6",
            api_key=FIXTURE.CREDENTIAL,
            max_tokens=1_024,
            output_mechanism="json_text",
        )
        schema = {
            "title": "SimpleInstalledProbe",
            "type": "object",
            "properties": {"message": {"type": "string", "minLength": 1}},
            "required": ["message"],
            "additionalProperties": False,
        }
        prompt = (
            "ordinary production adapter request\n\n"
            "Respond with ONLY a JSON object conforming to this JSON Schema:\n"
            + json.dumps(schema)
        )
        raw = endpoint.complete(prompt)
        assert json.loads(raw) == {"message": "deterministic fixture value"}
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert state == {
            "errors": [],
            "qualification_calls": 0,
            "schema_titles": {"SimpleInstalledProbe": 1},
            "total_calls": 1,
        }
        assert endpoint.last_usage["prompt_tokens"] > 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_external_provider_honours_runtime_reasoning_candidate_count():
    schema = ReasoningConjecturerTurnWireV6.model_json_schema()
    value = FIXTURE.response_for_schema(
        schema,
        "DIRECTIVE: return exactly 6 diverse candidates with typicality estimates.",
    )
    parsed = ReasoningConjecturerTurnWireV6.model_validate(value)
    assert len(parsed.candidates) == 6
    assert len({candidate.claim for candidate in parsed.candidates}) == 6


def test_external_provider_can_drive_a_genuine_resumable_stop():
    schema = ReasoningConjecturerTurnWireV6.model_json_schema()
    value = FIXTURE.response_for_schema(
        schema,
        OPERATIONAL.RESUMABLE_STOP_QUESTION,
    )
    parsed = ReasoningConjecturerTurnWireV6.model_validate(value)
    assert parsed.candidates == []
    assert parsed.abstention is not None
    assert parsed.abstention.search_signal == "stuck"


def test_operational_smoke_requires_exact_non_resumable_rejection():
    OPERATIONAL._assert_non_resumable_rejection(
        "ValueError: CONTINUE_TYPED_STOP_REQUIRED"
    )
    with pytest.raises(AssertionError, match="non-resumable"):
        OPERATIONAL._assert_non_resumable_rejection(
            "ValueError: CONTINUE_NOT_AUTHORIZED"
        )


def test_operational_poll_waits_for_a_new_terminal_commitment():
    class FakeClient:
        def __init__(self):
            self.result_calls = 0

        def tool(self, name, _arguments, **_kwargs):
            if name == "run_status":
                return {"state": "completed"}
            self.result_calls += 1
            return {
                "state": "completed",
                "terminal_commitment_ref": (
                    "sha256:old" if self.result_calls == 1 else "sha256:new"
                ),
            }

    client = FakeClient()
    _status, result = OPERATIONAL._poll_terminal(
        client,
        "run-id",
        prior_terminal_commitment_ref="sha256:old",
    )
    assert result["terminal_commitment_ref"] == "sha256:new"
    assert client.result_calls == 2


class _DeadlineClock:
    def __init__(self, iterations: int):
        self._values = iter(
            [
                0.0,
                *([0.0] * iterations),
                float(OPERATIONAL.CONTINUATION_DEADLINE_SECONDS),
            ]
        )

    def __call__(self) -> float:
        return next(self._values)


def test_continuation_deadline_and_fixed_running_observations_are_exact():
    observations = OPERATIONAL.ContinuationObservations()
    sleeps = []

    class FixedRunningClient:
        def __init__(self):
            self.status_calls = 0

        def tool(self, name, _arguments, **_kwargs):
            assert name == "run_status"
            self.status_calls += 1
            return {
                "state": "running",
                "phase": "reasoning",
                "seq": 17,
            }

    client = FixedRunningClient()
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        OPERATIONAL._poll_terminal(
            client,
            "SENTINEL_SYNTHETIC_MANAGED_ID",
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
            observations=observations,
            _clock=_DeadlineClock(3),
            _sleep=sleeps.append,
        )
    assert OPERATIONAL.CONTINUATION_DEADLINE_SECONDS == 600
    assert OPERATIONAL.POLL_INTERVAL_SECONDS == 0.05
    assert raised.value.failure_kind == OPERATIONAL.FAILURE_TIMEOUT
    assert raised.value.timeout is True
    assert client.status_calls == 3
    assert sleeps == [0.05, 0.05, 0.05]
    assert observations.snapshot() == {
        **OPERATIONAL._default_continuation_diagnostic(),
        "first_lifecycle_state": "running",
        "last_lifecycle_state": "running",
        "status_observation_count": 3,
        "last_progress_sequence": 17,
        "last_progress_phase": "reasoning",
    }


def test_continuation_poll_counts_stale_epoch_zero_results():
    observations = OPERATIONAL.ContinuationObservations()
    sleeps = []

    class StaleClient:
        def tool(self, name, _arguments, **_kwargs):
            if name == "run_status":
                return {"state": "completed", "phase": "stop", "seq": 19}
            return {
                "state": "completed",
                "terminal_commitment_ref": (
                    "SENTINEL_SYNTHETIC_COMMITMENT_REF"
                ),
            }

    with pytest.raises(OPERATIONAL.OperationalSmokeFailure):
        OPERATIONAL._poll_terminal(
            StaleClient(),
            "SENTINEL_SYNTHETIC_MANAGED_ID",
            prior_terminal_commitment_ref=(
                "SENTINEL_SYNTHETIC_COMMITMENT_REF"
            ),
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
            observations=observations,
            _clock=_DeadlineClock(4),
            _sleep=sleeps.append,
        )
    assert observations.status_observation_count == 4
    assert observations.stale_epoch0_result_observation_count == 4
    assert observations.result_read_error_count == 0
    assert sleeps == [0.05] * 4


def test_continuation_poll_counts_repeated_result_read_failures():
    observations = OPERATIONAL.ContinuationObservations()

    class ResultFailureClient:
        def tool(self, name, _arguments, **kwargs):
            if name == "run_status":
                return {"state": "completed", "phase": "stop", "seq": 23}
            raise OPERATIONAL._MCPToolResponseError(
                stage=kwargs["stage"]
            )

    with pytest.raises(OPERATIONAL.OperationalSmokeFailure):
        OPERATIONAL._poll_terminal(
            ResultFailureClient(),
            "SENTINEL_SYNTHETIC_MANAGED_ID",
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
            observations=observations,
            _clock=_DeadlineClock(3),
            _sleep=lambda _seconds: None,
        )
    assert observations.status_observation_count == 3
    assert observations.result_read_error_count == 3
    assert observations.stale_epoch0_result_observation_count == 0


def test_continuation_status_failure_remains_primary_and_is_counted():
    observations = OPERATIONAL.ContinuationObservations()

    class StatusFailureClient:
        def tool(self, _name, _arguments, **kwargs):
            raise OPERATIONAL._MCPToolResponseError(
                stage=kwargs["stage"]
            )

    with pytest.raises(OPERATIONAL._MCPToolResponseError) as raised:
        OPERATIONAL._poll_terminal(
            StatusFailureClient(),
            "SENTINEL_SYNTHETIC_MANAGED_ID",
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
            observations=observations,
            _clock=_DeadlineClock(1),
            _sleep=lambda _seconds: None,
        )
    assert raised.value.failure_kind == OPERATIONAL.FAILURE_ASSERTION
    assert observations.status_read_error_count == 1
    assert observations.status_observation_count == 0


def test_continuation_child_exit_status_is_preserved():
    observations = OPERATIONAL.ContinuationObservations()

    class ExitedClient:
        def tool(self, _name, _arguments, **kwargs):
            raise OPERATIONAL.OperationalSmokeFailure(
                stage=kwargs["stage"],
                failure_kind=OPERATIONAL.FAILURE_COMMAND,
                exit_status=47,
            )

    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        OPERATIONAL._poll_terminal(
            ExitedClient(),
            "SENTINEL_SYNTHETIC_MANAGED_ID",
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
            observations=observations,
            _clock=_DeadlineClock(1),
            _sleep=lambda _seconds: None,
        )
    assert raised.value.exit_status == 47
    assert raised.value.failure_kind == OPERATIONAL.FAILURE_COMMAND
    assert observations.status_observation_count == 0


def _annotation_record(stderr: str) -> dict:
    prefix = (
        "::error title=DeepReason installed-wheel operational smoke failed::"
    )
    assert stderr.count(prefix) == 1
    return json.loads(stderr.strip().removeprefix(prefix))


def _diagnostic_sentinels(repo: Path, temp_root: Path) -> tuple[str, ...]:
    return (
        "SENTINEL_ARBITRARY_EXCEPTION_MESSAGE",
        "SENTINEL_RAW_LIFECYCLE_VALUE",
        "SENTINEL_RAW_PROGRESS_PHASE",
        "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE",
        "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE",
        "SENTINEL_SYNTHETIC_ENVIRONMENT_NAME",
        "SENTINEL_SYNTHETIC_ARGUMENT",
        "SENTINEL_SYNTHETIC_QUESTION",
        "SENTINEL_SYNTHETIC_PROMPT",
        "SENTINEL_SYNTHETIC_PROVIDER_REQUEST",
        "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE",
        "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD",
        "SENTINEL_SYNTHETIC_MANAGED_ID",
        "SENTINEL_SYNTHETIC_MANIFEST_PATH",
        "SENTINEL_SYNTHETIC_COMMITMENT_REF",
        "SENTINEL_SYNTHETIC_RESULT_REF",
        "SENTINEL_SYNTHETIC_REPLAY_REF",
        "SENTINEL_SYNTHETIC_PREPARATION_REF",
        "SENTINEL_SYNTHETIC_RESUME_REF",
        "SENTINEL_SYNTHETIC_OBJECT_HASH",
        str(repo.resolve()),
        str(temp_root.resolve()),
        "SENTINEL_COMPLETE_COMMAND",
        "SENTINEL_CAPTURED_STDOUT",
        "SENTINEL_CAPTURED_STDERR",
        "SyntheticUnexpectedFailure",
    )


def _assert_sentinels_absent(payload: str, sentinels: tuple[str, ...]) -> None:
    folded = payload.casefold()
    for sentinel in sentinels:
        assert sentinel.casefold() not in folded


def _expected_failure(
    *,
    stage: str,
    failure_kind: str,
    timeout: bool = False,
    cleanup_completed: bool | None = None,
    exit_status: int | None = None,
    detail_code: str | None = None,
    durable_progress: str | None = None,
    state_presence: dict[str, bool] | None = None,
    continuation_diagnostic: dict[str, object] | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "cleanup_completed": cleanup_completed,
        "detail_code": detail_code,
        "durable_progress": durable_progress,
        "exit_status": exit_status,
        "failure_kind": failure_kind,
        "platform_family": OPERATIONAL._platform_family(),
        "schema": "deepreason-wheel-operational-failure-v3",
        "stage": stage,
        "timeout": timeout,
        "event_log_present": None,
        "loopback_start_present": None,
        "managed_registration_present": None,
        "manifest_present": None,
        "preparation_present": None,
        "progress_log_present": None,
        "run_root_present": None,
        "terminal_result_present": None,
        "diagnostic_inspection_status": "not_attempted",
        "first_lifecycle_state": "not_observed",
        "last_lifecycle_state": "not_observed",
        "status_observation_count": 0,
        "last_progress_sequence": None,
        "last_progress_phase": "not_observed",
        "stale_epoch0_result_observation_count": 0,
        "result_read_error_count": 0,
        "status_read_error_count": 0,
        "provider_call_delta": None,
        "loopback_provider_error_count": None,
        "mcp_liveness": "not_started",
        "opening_resume_decision_present": None,
        "durable_terminal_epoch": None,
        "terminal_draft_count": None,
        "terminal_commitment_count": None,
        "latest_commitment_epoch": None,
        "commitment_inclusive_replay_binding_present": None,
        "durable_result_binding": "unknown",
    }
    record.update(state_presence or {})
    record.update(continuation_diagnostic or {})
    return record


class _TrackedProcess:
    def __init__(self, returncode: int | None = None):
        self.returncode = returncode
        self.args = [
            "SENTINEL_COMPLETE_COMMAND",
            "SENTINEL_SYNTHETIC_ARGUMENT",
        ]
        self.stdout = "SENTINEL_CAPTURED_STDOUT"
        self.stderr = "SENTINEL_CAPTURED_STDERR"

    def poll(self):
        return self.returncode


class _TrackedContinuationClient:
    def __init__(
        self,
        *,
        order: list[str] | None = None,
        state: str = "running",
        phase: str = "reasoning",
        sequence: int = 29,
    ):
        self.process = _TrackedProcess()
        self._closed = False
        self.order = order
        self.state = state
        self.phase = phase
        self.sequence = sequence
        self.transcript = [
            {
                "question": "SENTINEL_SYNTHETIC_QUESTION",
                "prompt": "SENTINEL_SYNTHETIC_PROMPT",
                "provider_request": (
                    "SENTINEL_SYNTHETIC_PROVIDER_REQUEST"
                ),
                "provider_response": (
                    "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE"
                ),
            }
        ]

    def tool(self, name, _arguments, **_kwargs):
        assert name == "run_status"
        return {
            "state": self.state,
            "phase": self.phase,
            "seq": self.sequence,
        }

    def close(self, **_kwargs):
        if self._closed:
            return
        if self.order is not None:
            self.order.append("mcp_shutdown")
        self.process.returncode = 0
        self._closed = True


def _diagnostic_context(
    tmp_path: Path,
    observations: object,
    *,
    provider_call_baseline: int = 10,
) -> object:
    work = tmp_path / "unrelated-work"
    work.mkdir(exist_ok=True)
    return OPERATIONAL.ContinuationDiagnosticContext(
        python=Path(sys.executable),
        work=work,
        env={
            "SENTINEL_SYNTHETIC_ENVIRONMENT_NAME": (
                "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE"
            ),
            "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE": (
                "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD"
            ),
        },
        run_root=tmp_path / "SENTINEL_SYNTHETIC_MANAGED_ID",
        prior_terminal_commitment_ref=(
            "SENTINEL_SYNTHETIC_COMMITMENT_REF"
        ),
        provider_state_path=tmp_path / "provider-state.json",
        provider_call_baseline=provider_call_baseline,
        observations=observations,
    )


def _durable_snapshot(
    *,
    opening_resume_decision_present: bool = True,
    durable_terminal_epoch: int = 1,
    terminal_draft_count: int = 1,
    terminal_commitment_count: int = 1,
    latest_commitment_epoch: int | None = 0,
    commitment_inclusive_replay_binding_present: bool = True,
    durable_result_binding: str = "prior_commitment",
) -> dict[str, object]:
    return {
        "opening_resume_decision_present": (
            opening_resume_decision_present
        ),
        "durable_terminal_epoch": durable_terminal_epoch,
        "terminal_draft_count": terminal_draft_count,
        "terminal_commitment_count": terminal_commitment_count,
        "latest_commitment_epoch": latest_commitment_epoch,
        "commitment_inclusive_replay_binding_present": (
            commitment_inclusive_replay_binding_present
        ),
        "durable_result_binding": durable_result_binding,
    }


def test_timeout_wrapper_captures_state_and_shuts_down_before_cleanup(
    tmp_path, monkeypatch, capsys
):
    order = []
    client = _TrackedContinuationClient(order=order)
    observations = OPERATIONAL.ContinuationObservations()
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        OPERATIONAL._poll_terminal(
            client,
            "SENTINEL_SYNTHETIC_MANAGED_ID",
            prior_terminal_commitment_ref=(
                "SENTINEL_SYNTHETIC_COMMITMENT_REF"
            ),
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
            observations=observations,
            _clock=_DeadlineClock(2),
            _sleep=lambda _seconds: None,
        )
    context = _diagnostic_context(tmp_path, observations)
    monkeypatch.setattr(
        OPERATIONAL,
        "_read_loopback_diagnostic_state",
        lambda _path: (10, 0),
    )
    monkeypatch.setattr(
        OPERATIONAL,
        "_run_durable_inspection",
        lambda _context: _durable_snapshot(),
    )
    original_cleanup = OPERATIONAL._cleanup_temp_root

    def ordered_cleanup(root):
        order.append("temporary_root_cleanup")
        return original_cleanup(root)

    monkeypatch.setattr(
        OPERATIONAL, "_cleanup_temp_root", ordered_cleanup
    )
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    temp_root.mkdir()
    assert (
        OPERATIONAL._finalize_operational_smoke(
            raised.value,
            temp_root=temp_root,
            mcp_clients=[client],
            diagnostic_context=context,
        )
        == 1
    )
    captured = capsys.readouterr()
    record = _annotation_record(captured.err)
    assert order == ["mcp_shutdown", "temporary_root_cleanup"]
    assert record["cleanup_completed"] is True
    assert record["failure_kind"] == OPERATIONAL.FAILURE_TIMEOUT
    assert record["stage"] == OPERATIONAL.STAGE_CONTINUATION_RESUME
    assert record["diagnostic_inspection_status"] == "succeeded"
    assert record["first_lifecycle_state"] == "running"
    assert record["last_lifecycle_state"] == "running"
    assert record["status_observation_count"] == 2
    assert record["last_progress_sequence"] == 29
    assert record["last_progress_phase"] == "reasoning"
    assert record["provider_call_delta"] == 0
    assert record["loopback_provider_error_count"] == 0
    assert record["mcp_liveness"] == "alive"
    assert record["opening_resume_decision_present"] is True
    assert record["durable_terminal_epoch"] == 1
    assert record["terminal_draft_count"] == 1
    assert record["terminal_commitment_count"] == 1
    assert record["latest_commitment_epoch"] == 0
    assert (
        record["commitment_inclusive_replay_binding_present"] is True
    )
    assert record["durable_result_binding"] == "prior_commitment"
    assert set(record) == OPERATIONAL.FAILURE_RECORD_FIELDS
    assert not temp_root.exists()
    sentinels = _diagnostic_sentinels(
        Path(OPERATIONAL.__file__).resolve().parents[1], temp_root
    )
    _assert_sentinels_absent(
        str(raised.value) + captured.out + captured.err,
        sentinels,
    )


def test_provider_progress_without_terminalization_is_distinguished(
    tmp_path, monkeypatch
):
    observations = OPERATIONAL.ContinuationObservations()
    observations.observe_status(
        {"state": "running", "phase": "reasoning", "seq": 31}
    )
    context = _diagnostic_context(tmp_path, observations)
    client = _TrackedContinuationClient()
    monkeypatch.setattr(
        OPERATIONAL,
        "_read_loopback_diagnostic_state",
        lambda _path: (14, 2),
    )
    monkeypatch.setattr(
        OPERATIONAL,
        "_run_durable_inspection",
        lambda _context: _durable_snapshot(),
    )
    diagnostic = OPERATIONAL._capture_continuation_diagnostic(
        context, clients=[client]
    )
    assert diagnostic["provider_call_delta"] == 4
    assert diagnostic["loopback_provider_error_count"] == 2
    assert diagnostic["latest_commitment_epoch"] == 0
    assert diagnostic["durable_result_binding"] == "prior_commitment"


def test_current_commitment_with_stale_status_and_prior_result_is_distinguished(
    tmp_path, monkeypatch
):
    observations = OPERATIONAL.ContinuationObservations()
    observations.observe_status(
        {"state": "completed", "phase": "stop", "seq": 37}
    )
    observations.stale_epoch0_result_observation_count = 5
    context = _diagnostic_context(tmp_path, observations)
    monkeypatch.setattr(
        OPERATIONAL,
        "_read_loopback_diagnostic_state",
        lambda _path: (12, 0),
    )
    monkeypatch.setattr(
        OPERATIONAL,
        "_run_durable_inspection",
        lambda _context: _durable_snapshot(
            terminal_draft_count=2,
            terminal_commitment_count=2,
            latest_commitment_epoch=1,
            durable_result_binding="prior_commitment",
        ),
    )
    diagnostic = OPERATIONAL._capture_continuation_diagnostic(
        context, clients=[_TrackedContinuationClient()]
    )
    assert diagnostic["last_lifecycle_state"] == "completed"
    assert diagnostic["stale_epoch0_result_observation_count"] == 5
    assert diagnostic["terminal_commitment_count"] == 2
    assert diagnostic["latest_commitment_epoch"] == 1
    assert diagnostic["durable_result_binding"] == "prior_commitment"


def test_durable_current_result_not_yet_accepted_by_poll_is_distinguished(
    tmp_path, monkeypatch
):
    observations = OPERATIONAL.ContinuationObservations()
    observations.observe_status(
        {"state": "running", "phase": "reasoning", "seq": 41}
    )
    context = _diagnostic_context(tmp_path, observations)
    monkeypatch.setattr(
        OPERATIONAL,
        "_read_loopback_diagnostic_state",
        lambda _path: (13, 0),
    )
    monkeypatch.setattr(
        OPERATIONAL,
        "_run_durable_inspection",
        lambda _context: _durable_snapshot(
            terminal_draft_count=2,
            terminal_commitment_count=2,
            latest_commitment_epoch=1,
            durable_result_binding="current_commitment",
        ),
    )
    diagnostic = OPERATIONAL._capture_continuation_diagnostic(
        context, clients=[_TrackedContinuationClient()]
    )
    assert diagnostic["last_lifecycle_state"] == "running"
    assert diagnostic["latest_commitment_epoch"] == 1
    assert diagnostic["durable_result_binding"] == "current_commitment"


def test_installed_durable_inspector_is_read_only_and_finds_open_epoch(
    tmp_path, monkeypatch
):
    root, manifest, _service, _scheduler_calls, epoch_zero = (
        _start_converged_run(tmp_path, monkeypatch)
    )
    prepare_continuation(
        root,
        cycles=1,
        tokens="unlimited",
        expected_manifest_digest=manifest.sha256,
    )
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    work = tmp_path / "inspector-unrelated-work"
    work.mkdir()
    helper_env = dict(os.environ)
    helper_env["PYTHONPATH"] = str(ROOT / "src")
    helper_env["PYTHONDONTWRITEBYTECODE"] = "1"
    context = OPERATIONAL.ContinuationDiagnosticContext(
        python=Path(sys.executable),
        work=work,
        env=helper_env,
        run_root=root,
        prior_terminal_commitment_ref=epoch_zero[
            "terminal_commitment_ref"
        ],
        provider_state_path=tmp_path / "unused-provider-state.json",
        provider_call_baseline=0,
        observations=OPERATIONAL.ContinuationObservations(),
    )
    snapshot = OPERATIONAL._run_durable_inspection(context)
    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert snapshot == _durable_snapshot(
        commitment_inclusive_replay_binding_present=False
    )
    assert after == before


def test_installed_durable_inspector_rejects_stale_binding_for_current_commitment(
    tmp_path, monkeypatch
):
    root, manifest, service, _scheduler_calls, epoch_zero = (
        _start_converged_run(tmp_path, monkeypatch)
    )
    stale_epoch_zero_replay = (root / "REPLAY_VALIDATION.json").read_bytes()
    _continue_converged_run(root, manifest, service)
    (root / "REPLAY_VALIDATION.json").write_bytes(stale_epoch_zero_replay)
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    work = tmp_path / "stale-binding-inspector-work"
    work.mkdir()
    helper_env = dict(os.environ)
    helper_env["PYTHONPATH"] = str(ROOT / "src")
    helper_env["PYTHONDONTWRITEBYTECODE"] = "1"
    context = OPERATIONAL.ContinuationDiagnosticContext(
        python=Path(sys.executable),
        work=work,
        env=helper_env,
        run_root=root,
        prior_terminal_commitment_ref=epoch_zero[
            "terminal_commitment_ref"
        ],
        provider_state_path=tmp_path / "unused-provider-state.json",
        provider_call_baseline=0,
        observations=OPERATIONAL.ContinuationObservations(),
    )
    snapshot = OPERATIONAL._run_durable_inspection(context)
    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert snapshot == _durable_snapshot(
        terminal_draft_count=2,
        terminal_commitment_count=2,
        latest_commitment_epoch=1,
        commitment_inclusive_replay_binding_present=False,
        durable_result_binding="current_commitment",
    )
    assert after == before


def test_malformed_durable_inputs_emit_only_fixed_inspection_failure(
    tmp_path, monkeypatch
):
    root, manifest, _service, _scheduler_calls, epoch_zero = (
        _start_converged_run(tmp_path, monkeypatch)
    )
    prepare_continuation(
        root,
        cycles=1,
        tokens="unlimited",
        expected_manifest_digest=manifest.sha256,
    )
    (root / "log.jsonl").write_text(
        "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD\n",
        encoding="utf-8",
    )
    provider_state = tmp_path / "provider-state.json"
    provider_state.write_text(
        json.dumps({"errors": [], "total_calls": 10}),
        encoding="utf-8",
    )
    work = tmp_path / "malformed-inspector-work"
    work.mkdir()
    helper_env = dict(os.environ)
    helper_env["PYTHONPATH"] = str(ROOT / "src")
    helper_env["PYTHONDONTWRITEBYTECODE"] = "1"
    observations = OPERATIONAL.ContinuationObservations()
    observations.observe_status(
        {"state": "running", "phase": "reasoning", "seq": 43}
    )
    context = OPERATIONAL.ContinuationDiagnosticContext(
        python=Path(sys.executable),
        work=work,
        env=helper_env,
        run_root=root,
        prior_terminal_commitment_ref=epoch_zero[
            "terminal_commitment_ref"
        ],
        provider_state_path=provider_state,
        provider_call_baseline=10,
        observations=observations,
    )
    diagnostic = OPERATIONAL._capture_continuation_diagnostic(
        context, clients=[_TrackedContinuationClient()]
    )
    assert diagnostic["diagnostic_inspection_status"] == "failed"
    assert diagnostic["first_lifecycle_state"] == "running"
    assert diagnostic["provider_call_delta"] is None
    assert diagnostic["durable_terminal_epoch"] is None
    assert diagnostic["terminal_draft_count"] is None
    assert diagnostic["terminal_commitment_count"] is None
    assert diagnostic["latest_commitment_epoch"] is None
    assert diagnostic["opening_resume_decision_present"] is None
    assert (
        diagnostic["commitment_inclusive_replay_binding_present"] is None
    )
    assert diagnostic["durable_result_binding"] == "unknown"
    public = json.dumps(diagnostic, sort_keys=True)
    _assert_sentinels_absent(
        public,
        _diagnostic_sentinels(ROOT, tmp_path),
    )


def test_diagnostic_collection_failure_preserves_primary_and_redacts_raw_values(
    tmp_path, monkeypatch, capsys
):
    order = []
    client = _TrackedContinuationClient(
        order=order,
        state="SENTINEL_RAW_LIFECYCLE_VALUE",
        phase="SENTINEL_RAW_PROGRESS_PHASE",
    )
    observations = OPERATIONAL.ContinuationObservations()
    observations.observe_status(
        {
            "state": "SENTINEL_RAW_LIFECYCLE_VALUE",
            "phase": "SENTINEL_RAW_PROGRESS_PHASE",
            "seq": 47,
        }
    )
    context = _diagnostic_context(tmp_path, observations)
    failure = OPERATIONAL.OperationalSmokeFailure(
        stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
        failure_kind=OPERATIONAL.FAILURE_TIMEOUT,
        timeout=True,
    )

    def fail_collection(*_args, **_kwargs):
        raise RuntimeError("SENTINEL_ARBITRARY_EXCEPTION_MESSAGE")

    monkeypatch.setattr(
        OPERATIONAL, "_capture_continuation_diagnostic", fail_collection
    )
    original_cleanup = OPERATIONAL._cleanup_temp_root

    def ordered_cleanup(root):
        order.append("temporary_root_cleanup")
        return original_cleanup(root)

    monkeypatch.setattr(
        OPERATIONAL, "_cleanup_temp_root", ordered_cleanup
    )
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    temp_root.mkdir()
    assert (
        OPERATIONAL._finalize_operational_smoke(
            failure,
            temp_root=temp_root,
            mcp_clients=[client],
            diagnostic_context=context,
        )
        == 1
    )
    captured = capsys.readouterr()
    record = _annotation_record(captured.err)
    assert order == ["mcp_shutdown", "temporary_root_cleanup"]
    assert record["failure_kind"] == OPERATIONAL.FAILURE_TIMEOUT
    assert record["timeout"] is True
    assert record["diagnostic_inspection_status"] == "failed"
    assert record["first_lifecycle_state"] == "unknown"
    assert record["last_lifecycle_state"] == "unknown"
    assert record["last_progress_phase"] == "unknown"
    assert record["cleanup_completed"] is True
    _assert_sentinels_absent(
        str(failure)
        + captured.out
        + captured.err
        + json.dumps(record),
        _diagnostic_sentinels(ROOT, temp_root),
    )


def test_shutdown_failure_cannot_replace_primary_timeout(
    tmp_path, monkeypatch, capsys
):
    class ShutdownFailureClient(_TrackedContinuationClient):
        def close(self, **_kwargs):
            self.process.returncode = 0
            self._closed = True
            raise OPERATIONAL.OperationalSmokeFailure(
                stage=OPERATIONAL.STAGE_CLEANUP,
                failure_kind=OPERATIONAL.FAILURE_COMMAND,
                exit_status=99,
            )

    client = ShutdownFailureClient()
    failure = OPERATIONAL.OperationalSmokeFailure(
        stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
        failure_kind=OPERATIONAL.FAILURE_TIMEOUT,
        timeout=True,
    )
    monkeypatch.setattr(
        OPERATIONAL,
        "_capture_continuation_diagnostic",
        lambda _context, *, clients: {
            **OPERATIONAL._default_continuation_diagnostic(),
            "diagnostic_inspection_status": "failed",
            "mcp_liveness": "alive",
        },
    )
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    temp_root.mkdir()
    assert (
        OPERATIONAL._finalize_operational_smoke(
            failure,
            temp_root=temp_root,
            mcp_clients=[client],
        )
        == 1
    )
    record = _annotation_record(capsys.readouterr().err)
    assert record["failure_kind"] == OPERATIONAL.FAILURE_TIMEOUT
    assert record["stage"] == OPERATIONAL.STAGE_CONTINUATION_RESUME
    assert record["exit_status"] is None
    assert record["cleanup_completed"] is True


def test_unreadable_durable_diagnostic_is_fixed_and_payload_free(
    tmp_path, monkeypatch
):
    observations = OPERATIONAL.ContinuationObservations()
    observations.observe_status(
        {"state": "running", "phase": "resume", "seq": 53}
    )
    context = _diagnostic_context(tmp_path, observations)
    monkeypatch.setattr(
        OPERATIONAL,
        "_read_loopback_diagnostic_state",
        lambda _path: (10, 0),
    )

    def unreadable(_context):
        raise PermissionError("SENTINEL_ARBITRARY_EXCEPTION_MESSAGE")

    monkeypatch.setattr(
        OPERATIONAL, "_run_durable_inspection", unreadable
    )
    diagnostic = OPERATIONAL._capture_continuation_diagnostic(
        context, clients=[_TrackedContinuationClient()]
    )
    assert diagnostic["diagnostic_inspection_status"] == "failed"
    assert diagnostic["last_progress_phase"] == "resume"
    assert diagnostic["durable_terminal_epoch"] is None
    _assert_sentinels_absent(
        json.dumps(diagnostic),
        _diagnostic_sentinels(ROOT, tmp_path),
    )


def test_exited_continuation_child_keeps_exit_status_and_cleans_up(
    tmp_path, monkeypatch, capsys
):
    class ExitedTrackedClient(_TrackedContinuationClient):
        def __init__(self):
            super().__init__()
            self.process.returncode = 47

        def close(self, **_kwargs):
            self._closed = True
            raise OPERATIONAL.OperationalSmokeFailure(
                stage=OPERATIONAL.STAGE_CLEANUP,
                failure_kind=OPERATIONAL.FAILURE_COMMAND,
                exit_status=47,
            )

    client = ExitedTrackedClient()
    failure = OPERATIONAL.OperationalSmokeFailure(
        stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
        failure_kind=OPERATIONAL.FAILURE_COMMAND,
        exit_status=47,
    )
    monkeypatch.setattr(
        OPERATIONAL,
        "_capture_continuation_diagnostic",
        lambda _context, *, clients: {
            **OPERATIONAL._default_continuation_diagnostic(),
            "mcp_liveness": "exited",
        },
    )
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    temp_root.mkdir()
    assert (
        OPERATIONAL._finalize_operational_smoke(
            failure,
            temp_root=temp_root,
            mcp_clients=[client],
        )
        == 47
    )
    record = _annotation_record(capsys.readouterr().err)
    assert record["exit_status"] == 47
    assert record["mcp_liveness"] == "exited"
    assert record["cleanup_completed"] is True
    assert not temp_root.exists()


def test_command_failure_is_structured_payload_free_and_preserves_exit_status(
    tmp_path, monkeypatch, capsys
):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    temp_root.mkdir()
    sentinels = _diagnostic_sentinels(repo, temp_root)
    command = [
        "SENTINEL_COMPLETE_COMMAND",
        "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE",
    ]
    environment = {
        "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE": (
            "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE"
        )
    }

    def failed_subprocess(args, **_kwargs):
        return OPERATIONAL.subprocess.CompletedProcess(
            args,
            23,
            stdout=(
                "SENTINEL_CAPTURED_STDOUT "
                "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE "
                "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD"
            ),
            stderr=(
                "SENTINEL_CAPTURED_STDERR "
                "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE "
                "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE"
            ),
        )

    monkeypatch.setattr(OPERATIONAL.subprocess, "run", failed_subprocess)
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        OPERATIONAL._run(
            command,
            cwd=repo,
            env=environment,
            stage=OPERATIONAL.STAGE_BUILD_WHEEL,
        )
    public_failure = str(raised.value)
    _assert_sentinels_absent(public_failure, sentinels)
    assert json.loads(public_failure) == _expected_failure(
        stage=OPERATIONAL.STAGE_BUILD_WHEEL,
        failure_kind=OPERATIONAL.FAILURE_COMMAND,
        exit_status=23,
    )

    monkeypatch.setattr(
        OPERATIONAL.tempfile,
        "mkdtemp",
        lambda **_kwargs: str(temp_root),
    )
    monkeypatch.setattr(OPERATIONAL, "_unused_loopback_port", lambda: 1)

    def fail_build(_repo, _temp_root):
        OPERATIONAL._run(
            command,
            cwd=repo,
            env=environment,
            stage=OPERATIONAL.STAGE_BUILD_WHEEL,
        )

    monkeypatch.setattr(OPERATIONAL, "_build_wheel", fail_build)
    assert OPERATIONAL.main([]) == 23
    captured = capsys.readouterr()
    record = _annotation_record(captured.err)
    assert captured.out == ""
    assert record == _expected_failure(
        stage=OPERATIONAL.STAGE_BUILD_WHEEL,
        failure_kind=OPERATIONAL.FAILURE_COMMAND,
        cleanup_completed=True,
        exit_status=23,
    )
    _assert_sentinels_absent(
        public_failure + captured.out + captured.err + json.dumps(record),
        sentinels,
    )
    assert not temp_root.exists()


def test_unexpected_exception_is_fail_closed_and_payload_free(
    tmp_path, monkeypatch, capsys
):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    temp_root.mkdir()
    sentinels = _diagnostic_sentinels(repo, temp_root)
    arbitrary_message = " ".join(sentinels)

    class SyntheticUnexpectedFailure(Exception):
        pass

    monkeypatch.setattr(
        OPERATIONAL.tempfile,
        "mkdtemp",
        lambda **_kwargs: str(temp_root),
    )
    monkeypatch.setattr(OPERATIONAL, "_unused_loopback_port", lambda: 1)

    def fail_build(_repo, _temp_root):
        raise SyntheticUnexpectedFailure(arbitrary_message)

    monkeypatch.setattr(OPERATIONAL, "_build_wheel", fail_build)
    assert OPERATIONAL.main([]) == 1
    captured = capsys.readouterr()
    record = _annotation_record(captured.err)
    assert captured.out == ""
    assert record == _expected_failure(
        stage=OPERATIONAL.STAGE_BUILD_WHEEL,
        failure_kind=OPERATIONAL.FAILURE_UNEXPECTED,
        cleanup_completed=True,
    )
    _assert_sentinels_absent(
        captured.out + captured.err + json.dumps(record),
        sentinels,
    )
    assert not temp_root.exists()


def test_timeout_failure_text_is_fixed_and_payload_free(monkeypatch, tmp_path):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    home = temp_root / "home"
    home.mkdir(parents=True)
    ready_marker = temp_root / "reason-ready"
    sentinels = _diagnostic_sentinels(repo, temp_root)
    command = ["SENTINEL_COMPLETE_COMMAND"]

    def timed_out(args, **_kwargs):
        raise OPERATIONAL.subprocess.TimeoutExpired(
            args,
            5,
            output="SENTINEL_CAPTURED_STDOUT",
            stderr="SENTINEL_CAPTURED_STDERR",
        )

    monkeypatch.setattr(OPERATIONAL.subprocess, "run", timed_out)
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        OPERATIONAL._run_reason(
            command,
            cwd=repo,
            env={
                "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE": (
                    "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE"
                )
            },
            home=home,
            ready_marker=ready_marker,
        )
    public_failure = str(raised.value)
    _assert_sentinels_absent(public_failure, sentinels)
    assert json.loads(public_failure) == _expected_failure(
        stage=OPERATIONAL.STAGE_REASON,
        failure_kind=OPERATIONAL.FAILURE_TIMEOUT,
        timeout=True,
        detail_code=OPERATIONAL.DETAIL_CHILD_TIMEOUT,
        durable_progress=OPERATIONAL.DURABLE_PREPARATION_ABSENT,
        state_presence={
            field: False
            for field in OPERATIONAL.ALLOWED_STATE_PRESENCE_FIELDS
        },
    )


def test_mcp_child_exit_is_payload_free_and_preserves_process_status(
    tmp_path, monkeypatch, capsys
):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    temp_root.mkdir()
    sentinels = _diagnostic_sentinels(repo, temp_root)
    processes = []

    class InputStream:
        def write(self, value):
            return len(value)

        def flush(self):
            return None

    class OutputStream:
        def readline(self):
            return ""

    class ErrorStream:
        def __init__(self):
            self.read_calls = 0

        def read(self):
            self.read_calls += 1
            return (
                "SENTINEL_CAPTURED_STDERR "
                "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE "
                "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE"
            )

    class FailedMCPProcess:
        def __init__(self):
            self.stdin = InputStream()
            self.stdout = OutputStream()
            self.stderr = ErrorStream()

        def poll(self):
            return 47

        def wait(self, **_kwargs):
            return 47

    def failed_popen(*_args, **_kwargs):
        process = FailedMCPProcess()
        processes.append(process)
        return process

    monkeypatch.setattr(OPERATIONAL.subprocess, "Popen", failed_popen)

    def request_from_failed_child():
        client = OPERATIONAL.MCPClient(
            Path("SENTINEL_COMPLETE_COMMAND"),
            cwd=repo,
            env={
                "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE": (
                    "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE"
                )
            },
        )
        client.request(
            "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD",
            {"payload": "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE"},
            stage=OPERATIONAL.STAGE_MCP_REQUEST,
        )

    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        request_from_failed_child()
    public_failure = str(raised.value)
    assert json.loads(public_failure) == _expected_failure(
        stage=OPERATIONAL.STAGE_MCP_REQUEST,
        failure_kind=OPERATIONAL.FAILURE_COMMAND,
        exit_status=47,
    )
    _assert_sentinels_absent(public_failure, sentinels)
    assert processes[-1].stderr.read_calls == 0

    monkeypatch.setattr(
        OPERATIONAL.tempfile,
        "mkdtemp",
        lambda **_kwargs: str(temp_root),
    )
    monkeypatch.setattr(OPERATIONAL, "_unused_loopback_port", lambda: 1)
    monkeypatch.setattr(
        OPERATIONAL,
        "_build_wheel",
        lambda _repo, _temp_root: request_from_failed_child(),
    )
    assert OPERATIONAL.main([]) == 47
    captured = capsys.readouterr()
    record = _annotation_record(captured.err)
    assert captured.out == ""
    assert record == _expected_failure(
        stage=OPERATIONAL.STAGE_MCP_REQUEST,
        failure_kind=OPERATIONAL.FAILURE_COMMAND,
        cleanup_completed=True,
        exit_status=47,
    )
    _assert_sentinels_absent(
        public_failure + captured.out + captured.err + json.dumps(record),
        sentinels,
    )
    assert processes[-1].stderr.read_calls == 0
    assert not temp_root.exists()


def test_mcp_response_failures_never_enter_public_diagnostics(
    tmp_path, monkeypatch, capsys
):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    temp_root.mkdir()
    sentinels = _diagnostic_sentinels(repo, temp_root)
    arbitrary_response = " ".join(sentinels)

    class PayloadClient(OPERATIONAL.MCPClient):
        def __init__(self):
            self.is_error = True

        def request(self, *_args, **_kwargs):
            return {
                "result": {
                    "content": [{"text": arbitrary_response}],
                    "isError": self.is_error,
                }
            }

    client = PayloadClient()
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        client.tool(
            "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD",
            {"payload": "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE"},
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
        )
    public_failure = str(raised.value)
    assert json.loads(public_failure) == _expected_failure(
        stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
        failure_kind=OPERATIONAL.FAILURE_ASSERTION,
    )
    _assert_sentinels_absent(public_failure, sentinels)

    client.is_error = False
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised_success:
        client.tool_error(
            "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD",
            {"payload": "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE"},
            stage=OPERATIONAL.STAGE_CONTINUATION_REJECTION,
        )
    unexpected_success_failure = str(raised_success.value)
    assert json.loads(unexpected_success_failure) == _expected_failure(
        stage=OPERATIONAL.STAGE_CONTINUATION_REJECTION,
        failure_kind=OPERATIONAL.FAILURE_ASSERTION,
    )
    _assert_sentinels_absent(unexpected_success_failure, sentinels)

    client.is_error = True
    monkeypatch.setattr(
        OPERATIONAL.tempfile,
        "mkdtemp",
        lambda **_kwargs: str(temp_root),
    )
    monkeypatch.setattr(OPERATIONAL, "_unused_loopback_port", lambda: 1)
    monkeypatch.setattr(
        OPERATIONAL,
        "_build_wheel",
        lambda _repo, _temp_root: client.tool(
            "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD",
            {"payload": "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE"},
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
        ),
    )
    assert OPERATIONAL.main([]) == 1
    captured = capsys.readouterr()
    record = _annotation_record(captured.err)
    assert captured.out == ""
    assert record == _expected_failure(
        stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
        failure_kind=OPERATIONAL.FAILURE_ASSERTION,
        cleanup_completed=True,
    )
    _assert_sentinels_absent(
        public_failure
        + unexpected_success_failure
        + captured.out
        + captured.err
        + json.dumps(record),
        sentinels,
    )
    assert not temp_root.exists()


def test_v3_diagnostic_fields_types_and_allowlists_are_closed():
    assert OPERATIONAL.FAILURE_SCHEMA == "deepreason-wheel-operational-failure-v3"
    assert OPERATIONAL.ALLOWED_TYPED_REASON_CODES == {"RUN_WORKER_NOT_FOUND"}
    assert OPERATIONAL.ALLOWED_STATE_PRESENCE_FIELDS == {
        "event_log_present",
        "loopback_start_present",
        "managed_registration_present",
        "manifest_present",
        "preparation_present",
        "progress_log_present",
        "run_root_present",
        "terminal_result_present",
    }
    assert OPERATIONAL.CONTINUATION_DIAGNOSTIC_FIELDS == {
        "diagnostic_inspection_status",
        "first_lifecycle_state",
        "last_lifecycle_state",
        "status_observation_count",
        "last_progress_sequence",
        "last_progress_phase",
        "stale_epoch0_result_observation_count",
        "result_read_error_count",
        "status_read_error_count",
        "provider_call_delta",
        "loopback_provider_error_count",
        "mcp_liveness",
        "opening_resume_decision_present",
        "durable_terminal_epoch",
        "terminal_draft_count",
        "terminal_commitment_count",
        "latest_commitment_epoch",
        "commitment_inclusive_replay_binding_present",
        "durable_result_binding",
    }
    assert OPERATIONAL.FAILURE_RECORD_FIELDS == {
        "schema",
        "platform_family",
        "stage",
        "failure_kind",
        "timeout",
        "cleanup_completed",
        "exit_status",
        "detail_code",
        "durable_progress",
        *OPERATIONAL.ALLOWED_STATE_PRESENCE_FIELDS,
        *OPERATIONAL.CONTINUATION_DIAGNOSTIC_FIELDS,
    }
    assert OPERATIONAL.ALLOWED_DIAGNOSTIC_LIFECYCLES == {
        "not_observed",
        "not_started",
        "starting",
        "running",
        "paused",
        "completed",
        "failed",
        "cancelled",
        "unknown",
    }
    assert OPERATIONAL.ALLOWED_DIAGNOSTIC_PHASES == {
        "not_observed",
        "manifest",
        "resume",
        "workload",
        "reasoning",
        "stop",
        "unknown",
    }
    assert OPERATIONAL.ALLOWED_MCP_LIVENESS == {
        "not_started",
        "alive",
        "exited",
        "unknown",
    }
    assert OPERATIONAL.ALLOWED_RESULT_BINDINGS == {
        "absent",
        "prior_commitment",
        "current_commitment",
        "unbound",
        "unknown",
    }
    failure = OPERATIONAL.OperationalSmokeFailure(
        stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
        failure_kind=OPERATIONAL.FAILURE_TIMEOUT,
        timeout=True,
    )
    record = OPERATIONAL._diagnostic_record(
        failure, cleanup_completed=False
    )
    assert set(record) == OPERATIONAL.FAILURE_RECORD_FIELDS
    for field in (
        "status_observation_count",
        "stale_epoch0_result_observation_count",
        "result_read_error_count",
        "status_read_error_count",
    ):
        assert type(record[field]) is int and record[field] >= 0
    for field in (
        "exit_status",
        "last_progress_sequence",
        "provider_call_delta",
        "loopback_provider_error_count",
        "durable_terminal_epoch",
        "terminal_draft_count",
        "terminal_commitment_count",
        "latest_commitment_epoch",
    ):
        assert record[field] is None
    assert type(record["timeout"]) is bool
    assert type(record["cleanup_completed"]) is bool

    with pytest.raises(ValueError, match="detail code"):
        OPERATIONAL.OperationalSmokeFailure(
            stage=OPERATIONAL.STAGE_REASON,
            failure_kind=OPERATIONAL.FAILURE_COMMAND,
            detail_code="SENTINEL_ARBITRARY_EXCEPTION_MESSAGE",
        )
    with pytest.raises(ValueError, match="durable progress"):
        OPERATIONAL.OperationalSmokeFailure(
            stage=OPERATIONAL.STAGE_REASON,
            failure_kind=OPERATIONAL.FAILURE_COMMAND,
            durable_progress="SENTINEL_SYNTHETIC_MANAGED_ID",
        )
    with pytest.raises(ValueError, match="state-presence field"):
        OPERATIONAL.OperationalSmokeFailure(
            stage=OPERATIONAL.STAGE_REASON,
            failure_kind=OPERATIONAL.FAILURE_COMMAND,
            state_presence={"SENTINEL_SYNTHETIC_MANIFEST_PATH": True},
        )
    with pytest.raises(TypeError, match="must be boolean"):
        OPERATIONAL.OperationalSmokeFailure(
            stage=OPERATIONAL.STAGE_REASON,
            failure_kind=OPERATIONAL.FAILURE_COMMAND,
            state_presence={OPERATIONAL.STATE_RUN_ROOT_PRESENT: 1},
        )
    invalid_diagnostic = OPERATIONAL._default_continuation_diagnostic()
    invalid_diagnostic["first_lifecycle_state"] = (
        "SENTINEL_RAW_LIFECYCLE_VALUE"
    )
    with pytest.raises(ValueError, match="lifecycle"):
        OPERATIONAL.OperationalSmokeFailure(
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
            failure_kind=OPERATIONAL.FAILURE_TIMEOUT,
            continuation_diagnostic=invalid_diagnostic,
        )
    invalid_diagnostic = OPERATIONAL._default_continuation_diagnostic()
    invalid_diagnostic["provider_call_delta"] = -1
    with pytest.raises(TypeError, match="non-negative"):
        OPERATIONAL.OperationalSmokeFailure(
            stage=OPERATIONAL.STAGE_CONTINUATION_RESUME,
            failure_kind=OPERATIONAL.FAILURE_TIMEOUT,
            continuation_diagnostic=invalid_diagnostic,
        )


def test_loopback_ready_marker_is_scrubbed_then_injected_reason_only(
    tmp_path, monkeypatch
):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    home = tmp_path / "home"
    inherited_marker = tmp_path / "SENTINEL_SYNTHETIC_MANIFEST_PATH"
    explicit_marker = tmp_path / "reason-ready"
    monkeypatch.setenv(
        OPERATIONAL.LOOPBACK_READY_ENV,
        str(inherited_marker),
    )
    environment = OPERATIONAL._environment(
        home,
        provider_port=1,
        provider_state_path=tmp_path / "provider-state.json",
    )
    assert OPERATIONAL.LOOPBACK_READY_ENV not in environment

    observed_environment = None

    def successful_reason(args, **kwargs):
        nonlocal observed_environment
        observed_environment = kwargs["env"]
        return OPERATIONAL.subprocess.CompletedProcess(
            args,
            0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(OPERATIONAL.subprocess, "run", successful_reason)
    OPERATIONAL._run_reason(
        ["fixed-installed-reason-command"],
        cwd=repo,
        env=environment,
        home=home,
        ready_marker=explicit_marker,
    )
    assert observed_environment is not None
    assert observed_environment[OPERATIONAL.LOOPBACK_READY_ENV] == str(
        explicit_marker
    )
    assert OPERATIONAL.LOOPBACK_READY_ENV not in environment
    assert not inherited_marker.exists()


def test_reason_wrapper_admits_only_exact_typed_code_and_reports_boolean_state(
    tmp_path, monkeypatch, capsys
):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    home = temp_root / "home"
    runs = home / ".deepreason" / "runs"
    runs.mkdir(parents=True)
    decoy = runs / "preexisting-run"
    decoy.mkdir()
    (decoy / "run-result.json").write_text(
        "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD", encoding="utf-8"
    )
    ready_marker = temp_root / "reason-ready"
    sentinels = _diagnostic_sentinels(repo, temp_root)
    command = [
        "SENTINEL_COMPLETE_COMMAND",
        "SENTINEL_SYNTHETIC_ARGUMENT",
        "SENTINEL_SYNTHETIC_QUESTION",
    ]

    def failed_reason(args, **kwargs):
        marker = Path(kwargs["env"][OPERATIONAL.LOOPBACK_READY_ENV])
        marker.write_text("ready\n", encoding="ascii")
        root = runs / "SENTINEL_SYNTHETIC_MANAGED_ID"
        root.mkdir()
        for name in (
            "run-preparation.json",
            "run-manifest.json",
            "run-request.json",
            "progress.jsonl",
            "log.jsonl",
        ):
            (root / name).write_text(
                "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD", encoding="utf-8"
            )
        return OPERATIONAL.subprocess.CompletedProcess(
            args,
            23,
            stdout=(
                "SENTINEL_CAPTURED_STDOUT\n"
                "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE\n"
                "SENTINEL_SYNTHETIC_QUESTION"
            ),
            stderr="RUN_WORKER_NOT_FOUND\n",
        )

    monkeypatch.setattr(OPERATIONAL.subprocess, "run", failed_reason)
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        OPERATIONAL._run_reason(
            command,
            cwd=repo,
            env={
                "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE": (
                    "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE"
                )
            },
            home=home,
            ready_marker=ready_marker,
        )
    public_failure = str(raised.value)
    record = json.loads(public_failure)
    reason_state = {
        "event_log_present": True,
        "loopback_start_present": True,
        "managed_registration_present": True,
        "manifest_present": True,
        "preparation_present": True,
        "progress_log_present": True,
        "run_root_present": True,
        "terminal_result_present": False,
    }
    assert record == _expected_failure(
        stage=OPERATIONAL.STAGE_REASON,
        failure_kind=OPERATIONAL.FAILURE_COMMAND,
        exit_status=23,
        detail_code=OPERATIONAL.TYPED_REASON_RUN_WORKER_NOT_FOUND,
        durable_progress=OPERATIONAL.DURABLE_EVENT_LOG_PRESENT,
        state_presence=reason_state,
    )
    assert record["detail_code"] in OPERATIONAL.ALLOWED_DETAIL_CODES
    assert record["durable_progress"] in OPERATIONAL.ALLOWED_DURABLE_PROGRESS
    assert set(record) == OPERATIONAL.FAILURE_RECORD_FIELDS
    for field in OPERATIONAL.ALLOWED_STATE_PRESENCE_FIELDS:
        assert type(record[field]) is bool
    _assert_sentinels_absent(public_failure, sentinels)

    OPERATIONAL._emit_failure_diagnostic(
        raised.value,
        cleanup_completed=True,
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    annotation = _annotation_record(captured.err)
    assert annotation == {
        **record,
        "cleanup_completed": True,
    }
    _assert_sentinels_absent(
        captured.out + captured.err + json.dumps(annotation),
        sentinels,
    )


@pytest.mark.parametrize(
    "unknown",
    (
        "RUN_WORKER_NOT_FOUND",
        "RUN_WORKER_NOT_FOUND: SENTINEL_ARBITRARY_EXCEPTION_MESSAGE",
        "ValueError: RUN_WORKER_NOT_FOUND",
        "PREFIX_RUN_WORKER_NOT_FOUND",
        "SENTINEL_UNKNOWN_UPPERCASE_CODE",
    ),
)
def test_reason_unknown_text_is_fixed_without_reflection(
    unknown, tmp_path, monkeypatch
):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    home = temp_root / "home"
    home.mkdir(parents=True)
    ready_marker = temp_root / "reason-ready"
    sentinels = _diagnostic_sentinels(repo, temp_root) + (unknown,)

    def failed_reason(args, **kwargs):
        Path(kwargs["env"][OPERATIONAL.LOOPBACK_READY_ENV]).write_text(
            "ready\n", encoding="ascii"
        )
        return OPERATIONAL.subprocess.CompletedProcess(
            args,
            37,
            stdout="SENTINEL_CAPTURED_STDOUT",
            stderr=unknown + "\nSENTINEL_CAPTURED_STDERR",
        )

    monkeypatch.setattr(OPERATIONAL.subprocess, "run", failed_reason)
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        OPERATIONAL._run_reason(
            ["SENTINEL_COMPLETE_COMMAND", "SENTINEL_SYNTHETIC_ARGUMENT"],
            cwd=repo,
            env={},
            home=home,
            ready_marker=ready_marker,
        )
    public_failure = str(raised.value)
    record = json.loads(public_failure)
    assert record["detail_code"] == OPERATIONAL.DETAIL_UNKNOWN_REASON_FAILURE
    assert record["exit_status"] == 37
    assert record["durable_progress"] == OPERATIONAL.DURABLE_PREPARATION_ABSENT
    assert record["loopback_start_present"] is True
    _assert_sentinels_absent(public_failure, sentinels)


@pytest.mark.parametrize(
    ("raised_error", "expected_detail"),
    (
        (
            FileNotFoundError("SENTINEL_ARBITRARY_EXCEPTION_MESSAGE"),
            OPERATIONAL.DETAIL_EXECUTABLE_RESOLUTION_FAILED,
        ),
        (
            PermissionError("SENTINEL_ARBITRARY_EXCEPTION_MESSAGE"),
            OPERATIONAL.DETAIL_CHILD_LAUNCH_FAILED,
        ),
    ),
)
def test_reason_launch_failures_are_fixed_and_payload_free(
    raised_error, expected_detail, tmp_path, monkeypatch
):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    home = temp_root / "home"
    home.mkdir(parents=True)
    sentinels = _diagnostic_sentinels(repo, temp_root)

    def fail_launch(*_args, **_kwargs):
        raise raised_error

    monkeypatch.setattr(OPERATIONAL.subprocess, "run", fail_launch)
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised:
        OPERATIONAL._run_reason(
            ["SENTINEL_COMPLETE_COMMAND", "SENTINEL_SYNTHETIC_ARGUMENT"],
            cwd=repo,
            env={},
            home=home,
            ready_marker=temp_root / "reason-ready",
        )
    public_failure = str(raised.value)
    record = json.loads(public_failure)
    assert record["detail_code"] == expected_detail
    assert record["exit_status"] is None
    assert record["failure_kind"] == OPERATIONAL.FAILURE_UNEXPECTED
    _assert_sentinels_absent(public_failure, sentinels)


@pytest.mark.parametrize(
    ("inspection_error", "expected_detail"),
    (
        (
            PermissionError("SENTINEL_ARBITRARY_EXCEPTION_MESSAGE"),
            OPERATIONAL.DETAIL_FILESYSTEM_ACCESS_DENIED,
        ),
        (
            OSError("SENTINEL_ARBITRARY_EXCEPTION_MESSAGE"),
            OPERATIONAL.DETAIL_UNKNOWN_REASON_FAILURE,
        ),
    ),
)
def test_reason_state_inspection_errors_are_fixed_and_preserve_child_exit(
    inspection_error, expected_detail, tmp_path, monkeypatch
):
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    sentinels = _diagnostic_sentinels(repo, temp_root)

    def fail_inspection(**_kwargs):
        raise inspection_error

    monkeypatch.setattr(OPERATIONAL, "_reason_state_presence", fail_inspection)
    failure = OPERATIONAL._reason_failure(
        failure_kind=OPERATIONAL.FAILURE_COMMAND,
        home=temp_root / "home",
        ready_marker=temp_root / "reason-ready",
        roots_before=frozenset(),
        exit_status=41,
        stdout="SENTINEL_CAPTURED_STDOUT",
        stderr="SENTINEL_CAPTURED_STDERR",
    )
    public_failure = str(failure)
    record = json.loads(public_failure)
    assert record == _expected_failure(
        stage=OPERATIONAL.STAGE_REASON,
        failure_kind=OPERATIONAL.FAILURE_COMMAND,
        exit_status=41,
        detail_code=expected_detail,
        durable_progress=OPERATIONAL.DURABLE_STATE_INSPECTION_UNAVAILABLE,
    )
    _assert_sentinels_absent(public_failure, sentinels)


def test_reason_state_presence_ignores_symlinks_and_preexisting_roots(tmp_path):
    home = tmp_path / "home"
    runs = home / ".deepreason" / "runs"
    runs.mkdir(parents=True)
    preexisting = runs / "preexisting"
    preexisting.mkdir()
    (preexisting / "run-result.json").write_text("existing", encoding="utf-8")
    roots_before = OPERATIONAL._managed_run_roots(home)
    current = runs / "current"
    current.mkdir()
    payload = tmp_path / "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD"
    payload.write_text("sensitive", encoding="utf-8")
    for name in (
        "run-preparation.json",
        "run-manifest.json",
        "run-request.json",
        "progress.jsonl",
        "log.jsonl",
        "run-result.json",
    ):
        (current / name).symlink_to(payload)
    state, durable = OPERATIONAL._reason_state_presence(
        home=home,
        ready_marker=tmp_path / "missing-ready",
        roots_before=roots_before,
    )
    assert state == {
        OPERATIONAL.STATE_EVENT_LOG_PRESENT: False,
        OPERATIONAL.STATE_LOOPBACK_START_PRESENT: False,
        OPERATIONAL.STATE_MANAGED_REGISTRATION_PRESENT: False,
        OPERATIONAL.STATE_MANIFEST_PRESENT: False,
        OPERATIONAL.STATE_PREPARATION_PRESENT: False,
        OPERATIONAL.STATE_PROGRESS_LOG_PRESENT: False,
        OPERATIONAL.STATE_RUN_ROOT_PRESENT: True,
        OPERATIONAL.STATE_TERMINAL_RESULT_PRESENT: False,
    }
    assert durable == OPERATIONAL.DURABLE_RUN_ROOT_PRESENT


def test_cleanup_failure_is_fail_closed_and_payload_free(
    tmp_path, monkeypatch, capsys
):
    temp_root = tmp_path / "SENTINEL_TEMPORARY_PATH"
    temp_root.mkdir()
    repo = Path(OPERATIONAL.__file__).resolve().parents[1]
    sentinels = _diagnostic_sentinels(repo, temp_root)
    monkeypatch.setattr(OPERATIONAL, "_cleanup_temp_root", lambda _root: False)

    assert (
        OPERATIONAL._finalize_operational_smoke(None, temp_root=temp_root)
        == 1
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    record = _annotation_record(captured.err)
    assert record == _expected_failure(
        stage=OPERATIONAL.STAGE_CLEANUP,
        failure_kind=OPERATIONAL.FAILURE_CLEANUP,
        cleanup_completed=False,
    )
    _assert_sentinels_absent(captured.out + captured.err, sentinels)


def test_every_operational_reason_command_uses_the_diagnostic_wrapper():
    source = Path(OPERATIONAL.__file__).read_text(encoding="utf-8")
    assert source.count("= _run_reason(") == 3
    with pytest.raises(ValueError, match="diagnostic wrapper"):
        OPERATIONAL._run(
            ["unused"],
            cwd=ROOT,
            env={},
            stage=OPERATIONAL.STAGE_REASON,
        )


def test_every_operational_mcp_child_uses_tracked_construction():
    source = Path(OPERATIONAL.__file__).read_text(encoding="utf-8")
    assert source.count("MCPClient(") == 1
    assert source.count("= _new_mcp_client(") == 5
    assert "mcp_clients=mcp_clients" in source


def test_package_layout_excludes_mini_and_external_smoke_fixture():
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'packages = ["src/deepreason"]' in project
    assert "mini/minireason" not in project
    assert not (ROOT / "src" / "deepreason" / "deterministic_provider.py").exists()
