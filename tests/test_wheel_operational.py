from __future__ import annotations

import importlib.util
import json
from pathlib import Path
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


def _annotation_record(stderr: str) -> dict:
    prefix = (
        "::error title=DeepReason installed-wheel operational smoke failed::"
    )
    assert stderr.count(prefix) == 1
    return json.loads(stderr.strip().removeprefix(prefix))


def _diagnostic_sentinels(repo: Path, temp_root: Path) -> tuple[str, ...]:
    return (
        "SENTINEL_ARBITRARY_EXCEPTION_MESSAGE",
        "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE",
        "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE",
        "SENTINEL_SYNTHETIC_ARGUMENT",
        "SENTINEL_SYNTHETIC_QUESTION",
        "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE",
        "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD",
        "SENTINEL_SYNTHETIC_MANAGED_ID",
        "SENTINEL_SYNTHETIC_MANIFEST_PATH",
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
    assert json.loads(public_failure) == {
        "exit_status": 23,
        "failure_kind": OPERATIONAL.FAILURE_COMMAND,
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_BUILD_WHEEL,
        "timeout": False,
    }

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
    assert record == {
        "cleanup_completed": True,
        "exit_status": 23,
        "failure_kind": OPERATIONAL.FAILURE_COMMAND,
        "platform_family": OPERATIONAL._platform_family(),
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_BUILD_WHEEL,
        "timeout": False,
    }
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
    assert record == {
        "cleanup_completed": True,
        "failure_kind": OPERATIONAL.FAILURE_UNEXPECTED,
        "platform_family": OPERATIONAL._platform_family(),
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_BUILD_WHEEL,
        "timeout": False,
    }
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
    assert json.loads(public_failure) == {
        "detail_code": OPERATIONAL.DETAIL_CHILD_TIMEOUT,
        "durable_progress": OPERATIONAL.DURABLE_PREPARATION_ABSENT,
        "event_log_present": False,
        "failure_kind": OPERATIONAL.FAILURE_TIMEOUT,
        "loopback_start_present": False,
        "managed_registration_present": False,
        "manifest_present": False,
        "preparation_present": False,
        "progress_log_present": False,
        "run_root_present": False,
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_REASON,
        "terminal_result_present": False,
        "timeout": True,
    }


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
    assert json.loads(public_failure) == {
        "exit_status": 47,
        "failure_kind": OPERATIONAL.FAILURE_COMMAND,
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_MCP_REQUEST,
        "timeout": False,
    }
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
    assert record == {
        "cleanup_completed": True,
        "exit_status": 47,
        "failure_kind": OPERATIONAL.FAILURE_COMMAND,
        "platform_family": OPERATIONAL._platform_family(),
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_MCP_REQUEST,
        "timeout": False,
    }
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
    assert json.loads(public_failure) == {
        "failure_kind": OPERATIONAL.FAILURE_ASSERTION,
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_CONTINUATION_RESUME,
        "timeout": False,
    }
    _assert_sentinels_absent(public_failure, sentinels)

    client.is_error = False
    with pytest.raises(OPERATIONAL.OperationalSmokeFailure) as raised_success:
        client.tool_error(
            "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD",
            {"payload": "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE"},
            stage=OPERATIONAL.STAGE_CONTINUATION_REJECTION,
        )
    unexpected_success_failure = str(raised_success.value)
    assert json.loads(unexpected_success_failure) == {
        "failure_kind": OPERATIONAL.FAILURE_ASSERTION,
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_CONTINUATION_REJECTION,
        "timeout": False,
    }
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
    assert record == {
        "cleanup_completed": True,
        "failure_kind": OPERATIONAL.FAILURE_ASSERTION,
        "platform_family": OPERATIONAL._platform_family(),
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_CONTINUATION_RESUME,
        "timeout": False,
    }
    _assert_sentinels_absent(
        public_failure
        + unexpected_success_failure
        + captured.out
        + captured.err
        + json.dumps(record),
        sentinels,
    )
    assert not temp_root.exists()


def test_v2_diagnostic_fields_and_allowlists_are_closed():
    assert OPERATIONAL.FAILURE_SCHEMA == "deepreason-wheel-operational-failure-v2"
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
    assert record == {
        "detail_code": OPERATIONAL.TYPED_REASON_RUN_WORKER_NOT_FOUND,
        "durable_progress": OPERATIONAL.DURABLE_EVENT_LOG_PRESENT,
        "event_log_present": True,
        "exit_status": 23,
        "failure_kind": OPERATIONAL.FAILURE_COMMAND,
        "loopback_start_present": True,
        "managed_registration_present": True,
        "manifest_present": True,
        "preparation_present": True,
        "progress_log_present": True,
        "run_root_present": True,
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_REASON,
        "terminal_result_present": False,
        "timeout": False,
    }
    assert record["detail_code"] in OPERATIONAL.ALLOWED_DETAIL_CODES
    assert record["durable_progress"] in OPERATIONAL.ALLOWED_DURABLE_PROGRESS
    assert set(record) <= {
        "schema",
        "stage",
        "failure_kind",
        "timeout",
        "exit_status",
        "detail_code",
        "durable_progress",
        *OPERATIONAL.ALLOWED_STATE_PRESENCE_FIELDS,
    }
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
        "platform_family": OPERATIONAL._platform_family(),
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
    assert "exit_status" not in record
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
    assert record == {
        "detail_code": expected_detail,
        "durable_progress": OPERATIONAL.DURABLE_STATE_INSPECTION_UNAVAILABLE,
        "exit_status": 41,
        "failure_kind": OPERATIONAL.FAILURE_COMMAND,
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_REASON,
        "timeout": False,
    }
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
    assert record == {
        "cleanup_completed": False,
        "failure_kind": OPERATIONAL.FAILURE_CLEANUP,
        "platform_family": OPERATIONAL._platform_family(),
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_CLEANUP,
        "timeout": False,
    }
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


def test_package_layout_excludes_mini_and_external_smoke_fixture():
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'packages = ["src/deepreason"]' in project
    assert "mini/minireason" not in project
    assert not (ROOT / "src" / "deepreason" / "deterministic_provider.py").exists()
