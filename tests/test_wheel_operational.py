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
        "SENTINEL_SYNTHETIC_PROVIDER_RESPONSE",
        "SENTINEL_SYNTHETIC_FIXTURE_PAYLOAD",
        str(repo.resolve()),
        str(temp_root.resolve()),
        "SENTINEL_COMPLETE_COMMAND",
        "SENTINEL_CAPTURED_STDOUT",
        "SENTINEL_CAPTURED_STDERR",
        "SyntheticUnexpectedFailure",
    )


def _assert_sentinels_absent(payload: str, sentinels: tuple[str, ...]) -> None:
    for sentinel in sentinels:
        assert sentinel not in payload


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
        OPERATIONAL._run(
            command,
            cwd=repo,
            env={
                "SENTINEL_SYNTHETIC_CREDENTIAL_REFERENCE": (
                    "SENTINEL_SYNTHETIC_CREDENTIAL_VALUE"
                )
            },
            stage=OPERATIONAL.STAGE_REASON,
        )
    public_failure = str(raised.value)
    _assert_sentinels_absent(public_failure, sentinels)
    assert json.loads(public_failure) == {
        "failure_kind": OPERATIONAL.FAILURE_TIMEOUT,
        "schema": OPERATIONAL.FAILURE_SCHEMA,
        "stage": OPERATIONAL.STAGE_REASON,
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


def test_package_layout_excludes_mini_and_external_smoke_fixture():
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'packages = ["src/deepreason"]' in project
    assert "mini/minireason" not in project
    assert not (ROOT / "src" / "deepreason" / "deterministic_provider.py").exists()
