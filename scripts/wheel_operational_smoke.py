"""Qualify and operate the installed DeepReason wheel against loopback HTTP.

The deterministic OpenAI-compatible provider in this file is an external
qualification fixture.  It uses only the standard library, is never imported
by :mod:`deepreason`, and is excluded from the wheel by the package layout.
"""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import venv
import zipfile


EXPECTED_MCP_SCHEMA_SHA256 = (
    "7520ea29fa8efba50c98a9ffa76adfbe0c59c66f51541dfe609dee7736bf82e1"
)
EXPECTED_MCP_TOOLS = (
    "get_readiness",
    "start_run",
    "run_status",
    "run_result",
    "continue_run",
    "cancel_run",
    "scratch_map",
    "scratch_search",
    "scratch_open",
    "scratch_related",
    "scratch_attention",
    "start_bridge",
    "bridge_status",
    "bridge_result",
    "bridge_claims",
    "get_capabilities",
    "get_help_topic",
    "get_request_requirements",
)
TEST_CREDENTIAL_ENV = "DEEPREASON_LOOPBACK_SMOKE_KEY"
TEST_CREDENTIAL = "loopback-credential-must-never-appear"
LOOPBACK_READY_ENV = "DEEPREASON_WHEEL_LOOPBACK_READY"
RESUMABLE_STOP_QUESTION = (
    "What makes a typed resumable stop preserve continuation authority?"
)
FAILURE_SCHEMA = "deepreason-wheel-operational-failure-v2"
STAGE_BUILD_WHEEL = "build_wheel"
STAGE_CREATE_ENVIRONMENT = "create_environment"
STAGE_INSTALL_WHEEL = "install_wheel"
STAGE_SETUP_PROFILE = "setup_profile"
STAGE_QUALIFY = "qualify"
STAGE_READINESS = "readiness"
STAGE_REASON = "reason"
STAGE_MCP_INITIALIZE = "mcp_initialize"
STAGE_MCP_REQUEST = "mcp_request"
STAGE_CONTINUATION_REJECTION = "continuation_rejection"
STAGE_CONTINUATION_RESUME = "continuation_resume"
STAGE_REPLAY_VALIDATION = "replay_validation"
STAGE_RESTART_RECOVERY = "restart_recovery"
STAGE_BUDGET_REJECTION = "budget_rejection"
STAGE_MANIFEST_REJECTION = "manifest_rejection"
STAGE_DISCLOSURE_CHECK = "disclosure_check"
STAGE_CLEANUP = "cleanup"
ALLOWED_FAILURE_STAGES = frozenset(
    {
        STAGE_BUILD_WHEEL,
        STAGE_CREATE_ENVIRONMENT,
        STAGE_INSTALL_WHEEL,
        STAGE_SETUP_PROFILE,
        STAGE_QUALIFY,
        STAGE_READINESS,
        STAGE_REASON,
        STAGE_MCP_INITIALIZE,
        STAGE_MCP_REQUEST,
        STAGE_CONTINUATION_REJECTION,
        STAGE_CONTINUATION_RESUME,
        STAGE_REPLAY_VALIDATION,
        STAGE_RESTART_RECOVERY,
        STAGE_BUDGET_REJECTION,
        STAGE_MANIFEST_REJECTION,
        STAGE_DISCLOSURE_CHECK,
        STAGE_CLEANUP,
    }
)
FAILURE_COMMAND = "command_failed"
FAILURE_TIMEOUT = "timeout"
FAILURE_ASSERTION = "assertion_failed"
FAILURE_UNEXPECTED = "unexpected_failure"
FAILURE_CLEANUP = "cleanup_failed"
ALLOWED_FAILURE_KINDS = frozenset(
    {
        FAILURE_COMMAND,
        FAILURE_TIMEOUT,
        FAILURE_ASSERTION,
        FAILURE_UNEXPECTED,
        FAILURE_CLEANUP,
    }
)
DETAIL_CHILD_EXIT_NONZERO = "child_exit_nonzero"
DETAIL_CHILD_LAUNCH_FAILED = "child_launch_failed"
DETAIL_CHILD_TIMEOUT = "child_timeout"
DETAIL_EXECUTABLE_RESOLUTION_FAILED = "executable_resolution_failed"
DETAIL_FILESYSTEM_ACCESS_DENIED = "filesystem_access_denied"
DETAIL_UNKNOWN_REASON_FAILURE = "unknown_reason_failure"
TYPED_REASON_RUN_WORKER_NOT_FOUND = "RUN_WORKER_NOT_FOUND"
ALLOWED_TYPED_REASON_CODES = frozenset({TYPED_REASON_RUN_WORKER_NOT_FOUND})
ALLOWED_DETAIL_CODES = frozenset(
    {
        DETAIL_CHILD_EXIT_NONZERO,
        DETAIL_CHILD_LAUNCH_FAILED,
        DETAIL_CHILD_TIMEOUT,
        DETAIL_EXECUTABLE_RESOLUTION_FAILED,
        DETAIL_FILESYSTEM_ACCESS_DENIED,
        DETAIL_UNKNOWN_REASON_FAILURE,
        *ALLOWED_TYPED_REASON_CODES,
    }
)
DURABLE_PREPARATION_ABSENT = "preparation_absent"
DURABLE_RUN_ROOT_PRESENT = "run_root_present"
DURABLE_PREPARATION_PRESENT = "preparation_present"
DURABLE_MANAGED_REGISTRATION_PRESENT = "managed_registration_present"
DURABLE_EVENT_LOG_PRESENT = "event_log_present"
DURABLE_TERMINAL_RESULT_PRESENT = "terminal_result_present"
DURABLE_STATE_INSPECTION_UNAVAILABLE = "state_inspection_unavailable"
ALLOWED_DURABLE_PROGRESS = frozenset(
    {
        DURABLE_PREPARATION_ABSENT,
        DURABLE_RUN_ROOT_PRESENT,
        DURABLE_PREPARATION_PRESENT,
        DURABLE_MANAGED_REGISTRATION_PRESENT,
        DURABLE_EVENT_LOG_PRESENT,
        DURABLE_TERMINAL_RESULT_PRESENT,
        DURABLE_STATE_INSPECTION_UNAVAILABLE,
    }
)
STATE_RUN_ROOT_PRESENT = "run_root_present"
STATE_PREPARATION_PRESENT = "preparation_present"
STATE_MANIFEST_PRESENT = "manifest_present"
STATE_MANAGED_REGISTRATION_PRESENT = "managed_registration_present"
STATE_PROGRESS_LOG_PRESENT = "progress_log_present"
STATE_EVENT_LOG_PRESENT = "event_log_present"
STATE_TERMINAL_RESULT_PRESENT = "terminal_result_present"
STATE_LOOPBACK_START_PRESENT = "loopback_start_present"
ALLOWED_STATE_PRESENCE_FIELDS = frozenset(
    {
        STATE_RUN_ROOT_PRESENT,
        STATE_PREPARATION_PRESENT,
        STATE_MANIFEST_PRESENT,
        STATE_MANAGED_REGISTRATION_PRESENT,
        STATE_PROGRESS_LOG_PRESENT,
        STATE_EVENT_LOG_PRESENT,
        STATE_TERMINAL_RESULT_PRESENT,
        STATE_LOOPBACK_START_PRESENT,
    }
)


class OperationalSmokeFailure(Exception):
    """Fixed, payload-free operational failure."""

    def __init__(
        self,
        *,
        stage: str,
        failure_kind: str,
        exit_status: int | None = None,
        timeout: bool = False,
        detail_code: str | None = None,
        durable_progress: str | None = None,
        state_presence: dict[str, bool] | None = None,
    ) -> None:
        if stage not in ALLOWED_FAILURE_STAGES:
            raise ValueError("invalid fixed operational stage")
        if failure_kind not in ALLOWED_FAILURE_KINDS:
            raise ValueError("invalid fixed operational failure kind")
        if exit_status is not None and (
            isinstance(exit_status, bool) or not isinstance(exit_status, int)
        ):
            raise TypeError("operational exit status must be an integer")
        if not isinstance(timeout, bool):
            raise TypeError("operational timeout status must be boolean")
        if detail_code is not None and detail_code not in ALLOWED_DETAIL_CODES:
            raise ValueError("invalid fixed operational detail code")
        if (
            durable_progress is not None
            and durable_progress not in ALLOWED_DURABLE_PROGRESS
        ):
            raise ValueError("invalid fixed durable progress")
        fixed_state = dict(state_presence or {})
        if not set(fixed_state) <= ALLOWED_STATE_PRESENCE_FIELDS:
            raise ValueError("invalid fixed state-presence field")
        if any(type(value) is not bool for value in fixed_state.values()):
            raise TypeError("state-presence values must be boolean")
        self.stage = stage
        self.failure_kind = failure_kind
        self.exit_status = exit_status
        self.timeout = timeout
        self.detail_code = detail_code
        self.durable_progress = durable_progress
        self.state_presence = {
            key: fixed_state[key] for key in sorted(fixed_state)
        }
        record: dict[str, object] = {
            "failure_kind": failure_kind,
            "schema": FAILURE_SCHEMA,
            "stage": stage,
            "timeout": timeout,
        }
        if exit_status is not None:
            record["exit_status"] = exit_status
        if detail_code is not None:
            record["detail_code"] = detail_code
        if durable_progress is not None:
            record["durable_progress"] = durable_progress
        record.update(self.state_presence)
        super().__init__(json.dumps(record, sort_keys=True, separators=(",", ":")))


class _MCPToolResponseError(OperationalSmokeFailure):
    """Payload-free signal for an expected MCP tool error response."""

    def __init__(self, *, stage: str) -> None:
        super().__init__(
            stage=stage,
            failure_kind=FAILURE_ASSERTION,
        )


def _resolve_ref(schema: dict, root: dict) -> dict:
    reference = schema.get("$ref")
    if not reference:
        return schema
    value = root
    for component in reference.removeprefix("#/").split("/"):
        value = value[component]
    return value


def _schema_value(schema: dict, root: dict, *, field: str = "value"):
    schema = _resolve_ref(schema, root)
    if "const" in schema:
        return schema["const"]
    if schema.get("enum"):
        return schema["enum"][0]
    alternatives = schema.get("anyOf") or schema.get("oneOf")
    if alternatives:
        selected = next(
            (item for item in alternatives if item.get("type") != "null"),
            alternatives[0],
        )
        return _schema_value(selected, root, field=field)
    if schema.get("allOf"):
        return _schema_value(schema["allOf"][0], root, field=field)
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        return {
            name: _schema_value(properties[name], root, field=name)
            for name in schema.get("required", [])
        }
    if kind == "array":
        count = max(0, int(schema.get("minItems", 0)))
        return [
            _schema_value(schema.get("items", {}), root, field=field)
            for _ in range(count)
        ]
    if kind == "boolean":
        return False
    if kind == "integer":
        return int(schema.get("minimum", 0))
    if kind == "number":
        minimum = float(schema.get("minimum", 0.0))
        maximum = schema.get("maximum")
        return min(maximum, max(minimum, 0.5)) if maximum is not None else max(minimum, 0.5)
    if kind == "null":
        return None
    pattern = str(schema.get("pattern") or "")
    if "sha256" in pattern:
        return "sha256:" + "1" * 64
    if "[0-9a-f]{64}" in pattern:
        return "1" * 64
    if "NEW" in pattern:
        return "NEW_001"
    if "SCR" in pattern:
        return "SCR_001"
    if field == "values_json":
        return "{}"
    return "deterministic fixture value"


def response_for_schema(schema: dict, prompt: str) -> dict:
    """Return one semantically conservative value for an advertised schema."""

    title = schema.get("title")
    if (
        "typed resumable stop" in prompt.casefold()
        and title in {"ConjecturerTurnWireV6", "ReasoningConjecturerTurnWireV6"}
    ):
        return {
            "candidates": [],
            "context_request": None,
            "abstention": {
                "search_signal": "stuck",
                "note": "No further proposal is warranted for this bounded fixture.",
            },
        }
    if title == "BatchCriticWireV2":
        case_schema = schema["$defs"]["BatchCriticCaseWireV2"]
        aliases = case_schema["properties"]["target_alias"].get("enum", [])
        return {
            "cases": [
                {"target_alias": alias, "attack": False, "case": ""}
                for alias in aliases
            ]
        }
    if title == "AtomicConjectureCandidateWireV1":
        return {
            "candidate": {
                "content": "A deterministic, criticizable loopback explanation.",
                "typicality": 0.5,
                "neighbours": [],
            },
            "abstention": None,
        }
    if title == "AtomicReasoningConjectureCandidateWireV1":
        return {
            "candidate": {
                "claim": "A deterministic, criticizable loopback explanation.",
                "mechanism": "Recorded causes expose a bounded test surface.",
                "counterconditions": ["A contradictory durable record."],
                "typicality": 0.5,
            },
            "abstention": None,
        }
    exact = re.search(
        r"return exactly\s+([0-9]+)\s+diverse candidates",
        prompt,
        flags=re.IGNORECASE,
    )
    candidate_count = int(exact.group(1)) if exact else 1
    candidates = [
        {
            "content": (
                "A deterministic, criticizable loopback explanation "
                f"with test surface {index + 1}."
            ),
            "typicality": max(0.1, 0.8 - index * 0.1),
            "neighbours": [],
        }
        for index in range(candidate_count)
    ]
    reasoning_candidates = [
        {
            "claim": (
                "A deterministic, criticizable loopback claim "
                f"with test surface {index + 1}."
            ),
            "mechanism": "Recorded causes expose a bounded test surface.",
            "counterconditions": ["A contradictory durable record."],
            "typicality": max(0.1, 0.8 - index * 0.1),
        }
        for index in range(candidate_count)
    ]
    if title == "ConjecturerTurnWireV6":
        return {
            "candidates": candidates,
            "context_request": None,
            "abstention": None,
        }
    if title == "ReasoningConjecturerTurnWireV6":
        return {
            "candidates": reasoning_candidates,
            "context_request": None,
            "abstention": None,
        }
    if title == "BoundCompactCritic":
        target = schema["properties"]["target_alias"]["const"]
        return {
            "attack": False,
            "target_alias": target,
            "claim": "",
            "grounds": "",
            "cited_input_aliases": [],
        }
    if title in {"ConjecturerOutput", "CompactConjecturerOutput"}:
        return {"candidates": candidates}
    if title == "ReasoningConjecturerOutput":
        return {"candidates": reasoning_candidates}
    value = _schema_value(schema, schema)
    if not isinstance(value, dict):
        raise AssertionError("provider fixture cannot satisfy advertised schema")
    return value


def _schema_from_request(body: dict, prompt: str) -> dict:
    response_format = body.get("response_format") or {}
    advertised = response_format.get("json_schema") or {}
    schema = advertised.get("schema")
    if isinstance(schema, dict):
        return schema
    marker_at = max(prompt.find("JSON Schema"), prompt.find("closed schema"))
    schema_at = prompt.find("{", marker_at)
    if marker_at < 0 or schema_at < 0:
        raise ValueError("loopback request did not advertise an output schema")
    decoded, _end = json.JSONDecoder().raw_decode(prompt[schema_at:])
    if not isinstance(decoded, dict):
        raise ValueError("loopback request output schema is not an object")
    return decoded


class ProviderState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.requests: list[dict[str, object]] = []

    def record(self, *, prompt: str, model: str, max_tokens: int | None) -> None:
        with self.lock:
            self.requests.append(
                {
                    "qualification": "Qualification case " in prompt,
                    "model": model,
                    "max_tokens": max_tokens,
                }
            )

    @property
    def qualification_calls(self) -> int:
        with self.lock:
            return sum(bool(item["qualification"]) for item in self.requests)

    @property
    def total_calls(self) -> int:
        with self.lock:
            return len(self.requests)


def _provider_server(state: ProviderState):
    class Handler(BaseHTTPRequestHandler):
        server_version = "DeepReasonLoopback/1"

        def log_message(self, _format, *_args):
            return

        def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
            try:
                if self.path != "/v1/chat/completions":
                    self.send_error(404)
                    return
                if self.headers.get("Authorization") != f"Bearer {TEST_CREDENTIAL}":
                    self.send_error(401)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length))
                prompt = body["messages"][0]["content"]
                if not isinstance(prompt, str):
                    raise ValueError("loopback fixture accepts text requests only")
                schema = _schema_from_request(body, prompt)
                response = response_for_schema(schema, prompt)
                content = json.dumps(response, sort_keys=True, separators=(",", ":"))
                state.record(
                    prompt=prompt,
                    model=str(body.get("model")),
                    max_tokens=body.get("max_tokens"),
                )
                payload = {
                    "id": "chatcmpl-deepreason-loopback",
                    "object": "chat.completion",
                    "created": 0,
                    "model": body.get("model"),
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": content},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": max(1, len(prompt) // 4),
                        "completion_tokens": max(1, len(content) // 4),
                        "total_tokens": max(2, (len(prompt) + len(content)) // 4),
                    },
                }
                encoded = json.dumps(payload, separators=(",", ":")).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
            except Exception:  # fixture failures must fail the real call
                encoded = json.dumps(
                    {
                        "error": {
                            "type": "loopback_fixture_failure",
                            "message": "loopback fixture request failed",
                        }
                    }
                ).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _environment(
    home: Path, *, provider_port: int, provider_state_path: Path
) -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop(LOOPBACK_READY_ENV, None)
    environment["HOME"] = str(home)
    environment["USERPROFILE"] = str(home)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment[TEST_CREDENTIAL_ENV] = TEST_CREDENTIAL
    environment["DEEPREASON_WHEEL_LOOPBACK_FIXTURE"] = "1"
    environment["DEEPREASON_WHEEL_LOOPBACK_PORT"] = str(provider_port)
    environment["DEEPREASON_WHEEL_LOOPBACK_STATE"] = str(provider_state_path)
    environment["NO_PROXY"] = "127.0.0.1,localhost"
    environment["no_proxy"] = "127.0.0.1,localhost"
    environment.pop("DEEPREASON_PROFILE", None)
    environment.pop("DEEPREASON_HOME", None)
    return environment


def _unused_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _provider_counts(path: Path) -> dict[str, int]:
    if not path.exists():
        return {"qualification_calls": 0, "total_calls": 0}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "qualification_calls": int(payload["qualification_calls"]),
        "total_calls": int(payload["total_calls"]),
    }


def _assert_no_incremental_provider_calls(path: Path, before: int) -> None:
    if _provider_counts(path)["total_calls"] != before:
        raise AssertionError("zero-call operation dispatched to the provider")


def _install_loopback_fixture(
    *,
    repo: Path,
    python: Path,
    work: Path,
    env: dict[str, str],
    stage: str,
) -> Path:
    purelib = Path(
        _run(
            [
                str(python),
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ],
            cwd=work,
            env=env,
            stage=stage,
        ).stdout.strip()
    )
    target = purelib / "sitecustomize.py"
    shutil.copyfile(repo / "scripts" / "wheel_loopback_sitecustomize.py", target)
    return target


def _venv_executable(root: Path, name: str) -> Path:
    directory = root / ("Scripts" if os.name == "nt" else "bin")
    suffix = ".exe" if os.name == "nt" else ""
    return directory / f"{name}{suffix}"


def _is_regular_file(path: Path) -> bool:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(observed.st_mode)


def _managed_run_roots(home: Path) -> frozenset[Path]:
    runs = home / ".deepreason" / "runs"
    try:
        entries = tuple(runs.iterdir())
    except FileNotFoundError:
        return frozenset()
    roots = []
    for entry in entries:
        observed = entry.lstat()
        if stat.S_ISDIR(observed.st_mode) and not entry.name.startswith("."):
            roots.append(entry)
    return frozenset(roots)


def _reason_state_presence(
    *,
    home: Path,
    ready_marker: Path,
    roots_before: frozenset[Path] | None,
) -> tuple[dict[str, bool], str]:
    if roots_before is None:
        raise OSError("reason state baseline was unavailable")
    roots = _managed_run_roots(home) - roots_before
    state = {
        STATE_RUN_ROOT_PRESENT: bool(roots),
        STATE_PREPARATION_PRESENT: any(
            _is_regular_file(root / "run-preparation.json") for root in roots
        ),
        STATE_MANIFEST_PRESENT: any(
            _is_regular_file(root / "run-manifest.json") for root in roots
        ),
        STATE_MANAGED_REGISTRATION_PRESENT: any(
            _is_regular_file(root / "run-request.json") for root in roots
        ),
        STATE_PROGRESS_LOG_PRESENT: any(
            _is_regular_file(root / "progress.jsonl") for root in roots
        ),
        STATE_EVENT_LOG_PRESENT: any(
            _is_regular_file(root / "log.jsonl") for root in roots
        ),
        STATE_TERMINAL_RESULT_PRESENT: any(
            _is_regular_file(root / "run-result.json") for root in roots
        ),
        STATE_LOOPBACK_START_PRESENT: _is_regular_file(ready_marker),
    }
    if state[STATE_TERMINAL_RESULT_PRESENT]:
        durable = DURABLE_TERMINAL_RESULT_PRESENT
    elif state[STATE_EVENT_LOG_PRESENT]:
        durable = DURABLE_EVENT_LOG_PRESENT
    elif (
        state[STATE_MANAGED_REGISTRATION_PRESENT]
        or state[STATE_PROGRESS_LOG_PRESENT]
    ):
        durable = DURABLE_MANAGED_REGISTRATION_PRESENT
    elif state[STATE_PREPARATION_PRESENT] or state[STATE_MANIFEST_PRESENT]:
        durable = DURABLE_PREPARATION_PRESENT
    elif state[STATE_RUN_ROOT_PRESENT]:
        durable = DURABLE_RUN_ROOT_PRESENT
    else:
        durable = DURABLE_PREPARATION_ABSENT
    return state, durable


def _typed_reason_code(stdout: str, stderr: str) -> str | None:
    for captured in (stderr, stdout):
        candidate = captured.strip()
        if candidate in ALLOWED_TYPED_REASON_CODES:
            return candidate
    return None


def _reason_failure(
    *,
    failure_kind: str,
    home: Path,
    ready_marker: Path,
    roots_before: frozenset[Path] | None,
    exit_status: int | None = None,
    stdout: str = "",
    stderr: str = "",
    timeout: bool = False,
    fixed_detail_code: str | None = None,
) -> OperationalSmokeFailure:
    typed_code = _typed_reason_code(stdout, stderr)
    detail_code = fixed_detail_code or typed_code
    try:
        state_presence, durable_progress = _reason_state_presence(
            home=home,
            ready_marker=ready_marker,
            roots_before=roots_before,
        )
    except PermissionError:
        state_presence = {}
        durable_progress = DURABLE_STATE_INSPECTION_UNAVAILABLE
        if detail_code is None:
            detail_code = DETAIL_FILESYSTEM_ACCESS_DENIED
    except OSError:
        state_presence = {}
        durable_progress = DURABLE_STATE_INSPECTION_UNAVAILABLE
        if detail_code is None:
            detail_code = DETAIL_UNKNOWN_REASON_FAILURE
    if detail_code is None:
        detail_code = (
            DETAIL_UNKNOWN_REASON_FAILURE
            if stdout or stderr
            else DETAIL_CHILD_EXIT_NONZERO
        )
    return OperationalSmokeFailure(
        stage=STAGE_REASON,
        failure_kind=failure_kind,
        exit_status=exit_status,
        timeout=timeout,
        detail_code=detail_code,
        durable_progress=durable_progress,
        state_presence=state_presence,
    )


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stage: str,
    expected: tuple[int, ...] = (0,),
    timeout: int = 600,
    _reason_context: tuple[Path, Path, frozenset[Path] | None] | None = None,
) -> subprocess.CompletedProcess[str]:
    if (stage == STAGE_REASON) != (_reason_context is not None):
        raise ValueError("reason stage must use the fixed diagnostic wrapper")
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        if _reason_context is not None:
            home, ready_marker, roots_before = _reason_context
            raise _reason_failure(
                failure_kind=FAILURE_TIMEOUT,
                home=home,
                ready_marker=ready_marker,
                roots_before=roots_before,
                timeout=True,
                fixed_detail_code=DETAIL_CHILD_TIMEOUT,
            ) from None
        raise OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_TIMEOUT,
            timeout=True,
        ) from None
    except FileNotFoundError:
        if _reason_context is None:
            raise
        home, ready_marker, roots_before = _reason_context
        raise _reason_failure(
            failure_kind=FAILURE_UNEXPECTED,
            home=home,
            ready_marker=ready_marker,
            roots_before=roots_before,
            fixed_detail_code=DETAIL_EXECUTABLE_RESOLUTION_FAILED,
        ) from None
    except OSError:
        if _reason_context is None:
            raise
        home, ready_marker, roots_before = _reason_context
        raise _reason_failure(
            failure_kind=FAILURE_UNEXPECTED,
            home=home,
            ready_marker=ready_marker,
            roots_before=roots_before,
            fixed_detail_code=DETAIL_CHILD_LAUNCH_FAILED,
        ) from None
    if completed.returncode not in expected:
        if _reason_context is not None:
            home, ready_marker, roots_before = _reason_context
            raise _reason_failure(
                failure_kind=FAILURE_COMMAND,
                home=home,
                ready_marker=ready_marker,
                roots_before=roots_before,
                exit_status=int(completed.returncode),
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        raise OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_COMMAND,
            exit_status=int(completed.returncode),
        )
    return completed


def _run_reason(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    home: Path,
    ready_marker: Path,
    expected: tuple[int, ...] = (0,),
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    try:
        roots_before: frozenset[Path] | None = _managed_run_roots(home)
    except OSError:
        roots_before = None
    reason_env = dict(env)
    reason_env[LOOPBACK_READY_ENV] = str(ready_marker)
    return _run(
        command,
        cwd=cwd,
        env=reason_env,
        stage=STAGE_REASON,
        expected=expected,
        timeout=timeout,
        _reason_context=(home, ready_marker, roots_before),
    )


class MCPClient:
    def __init__(
        self,
        executable: Path,
        *,
        cwd: Path,
        env: dict[str, str],
        stage: str = STAGE_MCP_INITIALIZE,
    ) -> None:
        try:
            self.process = subprocess.Popen(
                [str(executable)],
                cwd=cwd,
                env=env,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
            )
        except OSError:
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_UNEXPECTED,
            ) from None
        self._next_id = 1
        self.transcript: list[str] = []

    def _raise_process_failure(self, *, stage: str) -> None:
        returncode = self.process.poll()
        if returncode is None:
            try:
                returncode = self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                raise OperationalSmokeFailure(
                    stage=stage,
                    failure_kind=FAILURE_TIMEOUT,
                    timeout=True,
                ) from None
        raise OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_COMMAND,
            exit_status=int(returncode),
        ) from None

    @staticmethod
    def _response_text(
        response: dict,
        *,
        stage: str,
    ) -> tuple[bool, str]:
        try:
            result = response["result"]
            text = result["content"][0]["text"]
        except (IndexError, KeyError, TypeError):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            ) from None
        if not isinstance(result, dict) or not isinstance(text, str):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            )
        is_error = result.get("isError", False)
        if not isinstance(is_error, bool):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            )
        return is_error, text

    def request(
        self,
        method: str,
        params: dict | None = None,
        *,
        stage: str = STAGE_MCP_REQUEST,
    ) -> dict:
        assert self.process.stdin is not None and self.process.stdout is not None
        request_id = self._next_id
        self._next_id += 1
        message = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        try:
            self.process.stdin.write(
                json.dumps(message, separators=(",", ":")) + "\n"
            )
            self.process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            self._raise_process_failure(stage=stage)
        while True:
            try:
                line = self.process.stdout.readline()
            except (OSError, ValueError):
                self._raise_process_failure(stage=stage)
            if not line:
                self._raise_process_failure(stage=stage)
            self.transcript.append(line)
            try:
                response = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                raise OperationalSmokeFailure(
                    stage=stage,
                    failure_kind=FAILURE_ASSERTION,
                ) from None
            if not isinstance(response, dict):
                raise OperationalSmokeFailure(
                    stage=stage,
                    failure_kind=FAILURE_ASSERTION,
                )
            if response.get("id") == request_id:
                return response

    def tool(
        self,
        name: str,
        arguments: dict,
        *,
        stage: str = STAGE_MCP_REQUEST,
    ) -> dict:
        response = self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
            stage=stage,
        )
        is_error, text = self._response_text(response, stage=stage)
        if is_error:
            raise _MCPToolResponseError(stage=stage) from None
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            ) from None
        if not isinstance(payload, dict):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            )
        return payload

    def tool_error(
        self,
        name: str,
        arguments: dict,
        *,
        stage: str = STAGE_MCP_REQUEST,
    ) -> str:
        response = self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
            stage=stage,
        )
        is_error, text = self._response_text(response, stage=stage)
        if not is_error:
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            )
        return text

    def close(self, *, stage: str = STAGE_MCP_REQUEST) -> None:
        if self.process.stdin:
            try:
                self.process.stdin.close()
            except OSError:
                self._raise_process_failure(stage=stage)
        try:
            returncode = self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=10)
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_TIMEOUT,
                timeout=True,
            ) from None
        if returncode != 0:
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_COMMAND,
                exit_status=int(returncode),
            )


def _build_wheel(repo: Path, temp_root: Path) -> Path:
    wheelhouse = temp_root / "wheelhouse"
    wheelhouse.mkdir()
    build_home = temp_root / "build home"
    build_home.mkdir()
    build_env = dict(os.environ)
    build_env.pop("PYTHONPATH", None)
    build_env["HOME"] = str(build_home)
    build_env["USERPROFILE"] = str(build_home)
    build_env["PYTHONNOUSERSITE"] = "1"
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                ".",
                "--no-deps",
                "--wheel-dir",
                str(wheelhouse),
            ],
            cwd=repo,
            env=build_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        raise OperationalSmokeFailure(
            stage=STAGE_BUILD_WHEEL,
            failure_kind=FAILURE_TIMEOUT,
            timeout=True,
        ) from None
    if completed.returncode:
        raise OperationalSmokeFailure(
            stage=STAGE_BUILD_WHEEL,
            failure_kind=FAILURE_COMMAND,
            exit_status=int(completed.returncode),
        )
    wheels = sorted(wheelhouse.glob("deepreason-*.whl"))
    if len(wheels) != 1:
        raise AssertionError("wheel build did not produce exactly one wheel")
    return wheels[0]


def _inspect_operational_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = {name.casefold() for name in archive.namelist()}
    required = {
        "deepreason/__main__.py",
        "deepreason/readiness.py",
        "deepreason/provider_profile.py",
        "deepreason/qualification.py",
        "deepreason/preparation.py",
        "deepreason/mcp_registration.py",
    }
    if not required <= names:
        raise AssertionError("operational wheel omits required installed modules")
    if any(
        name.startswith(("mini/", "minireason/", "tests/", "scripts/"))
        or "deterministic_provider" in name
        for name in names
    ):
        raise AssertionError("repository-only fixture, tests, or Mini entered the wheel")


def _assert_resumable_terminal(payload: dict) -> None:
    _assert_committed_terminal(payload)
    verification = payload.get("verification") or {}
    required = (
        "completion_satisfied",
        "epistemic_checks_passed",
        "operational_checks_passed",
    )
    if not all(verification.get(name) is True for name in required):
        raise AssertionError("terminal verification is incomplete")
    if payload.get("completion_status") != "satisfied":
        raise AssertionError("terminal completion was not satisfied")
    stop = payload.get("stop") or {}
    if stop.get("reason") != "converged":
        raise AssertionError("terminal is not a resumable convergence stop")


def _assert_non_resumable_rejection(text: str) -> None:
    if text.strip() not in {
        "CONTINUE_TYPED_STOP_REQUIRED",
        "ValueError: CONTINUE_TYPED_STOP_REQUIRED",
    }:
        raise AssertionError("completed non-resumable run was not rejected")


def _assert_committed_terminal(payload: dict) -> None:
    if payload.get("schema") != "deepreason-run-result-v2":
        raise AssertionError("terminal result schema is not V6")
    if payload.get("state") != "completed":
        raise AssertionError("reasoning did not complete")
    verification = payload.get("verification") or {}
    for field in ("valid", "integrity_valid", "security_valid"):
        if verification.get(field) is not True:
            raise AssertionError("terminal verification failed")
    if not str(payload.get("terminal_commitment_ref", "")).startswith("sha256:"):
        raise AssertionError("terminal result lacks durable terminal authority")


def _assert_durable_replay(home: Path, run_id: str) -> None:
    replay_path = home / ".deepreason" / "runs" / run_id / "REPLAY_VALIDATION.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    if replay.get("schema") != "replay-validation.v1" or replay.get("valid") is not True:
        raise AssertionError("durable replay verification failed")
    if not re.fullmatch(r"[0-9a-f]{64}", str(replay.get("manifest_digest", ""))):
        raise AssertionError("durable replay omitted its exact manifest digest")


def _tool_list(client: MCPClient) -> list[dict]:
    initialized = client.request("initialize", {}, stage=STAGE_MCP_INITIALIZE)
    if initialized["result"]["serverInfo"]["name"] != "deepreason":
        raise AssertionError("installed MCP server identity drifted")
    return client.request(
        "tools/list",
        stage=STAGE_MCP_INITIALIZE,
    )["result"]["tools"]


def _assert_exact_tools(tools: list[dict]) -> None:
    names = tuple(tool["name"] for tool in tools)
    if names != EXPECTED_MCP_TOOLS:
        raise AssertionError("MCP tool inventory drifted")
    encoded = json.dumps(tools, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != EXPECTED_MCP_SCHEMA_SHA256:
        raise AssertionError("MCP schemas differ from the accepted public facade")
    lowered = encoded.decode().casefold()
    for forbidden in (
        '"root"',
        "run_manifest_ref",
        "manifest_path",
        "provider_profile",
        "credential_env",
        "api_key",
    ):
        if forbidden in lowered:
            raise AssertionError("MCP schema exposes forbidden authority")


def _poll_terminal(
    client: MCPClient,
    run_id: str,
    *,
    prior_terminal_commitment_ref: str | None = None,
    stage: str = STAGE_MCP_REQUEST,
) -> tuple[dict, dict]:
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        status = client.tool("run_status", {"run_id": run_id}, stage=stage)
        if status.get("state") in {"completed", "failed", "cancelled"}:
            try:
                result = client.tool(
                    "run_result",
                    {"run_id": run_id},
                    stage=stage,
                )
            except _MCPToolResponseError:
                time.sleep(0.05)
                continue
            if (
                prior_terminal_commitment_ref is not None
                and result.get("terminal_commitment_ref")
                == prior_terminal_commitment_ref
            ):
                time.sleep(0.05)
                continue
            return status, result
        time.sleep(0.05)
    raise OperationalSmokeFailure(
        stage=stage,
        failure_kind=FAILURE_TIMEOUT,
        timeout=True,
    )


def _assert_no_disclosure(
    *, repo: Path, home: Path, outputs: list[str], transcripts: list[str]
) -> None:
    forbidden = (str(repo.resolve()), TEST_CREDENTIAL)
    combined = "\n".join([*outputs, *transcripts])
    for value in forbidden:
        if value.casefold() in combined.casefold():
            raise AssertionError("command or MCP output disclosed repository/credential data")
    for path in home.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        payload = path.read_bytes()
        for value in forbidden:
            if value.encode() in payload:
                raise AssertionError("run/state record disclosed forbidden data")


def _platform_family() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    return "other"


def _diagnostic_record(
    failure: OperationalSmokeFailure,
    *,
    cleanup_completed: bool,
) -> dict[str, object]:
    if not isinstance(cleanup_completed, bool):
        raise TypeError("cleanup status must be boolean")
    record: dict[str, object] = {
        "cleanup_completed": cleanup_completed,
        "failure_kind": failure.failure_kind,
        "platform_family": _platform_family(),
        "schema": FAILURE_SCHEMA,
        "stage": failure.stage,
        "timeout": failure.timeout,
    }
    if failure.exit_status is not None:
        record["exit_status"] = failure.exit_status
    if failure.detail_code is not None:
        record["detail_code"] = failure.detail_code
    if failure.durable_progress is not None:
        record["durable_progress"] = failure.durable_progress
    record.update(failure.state_presence)
    return record


def _emit_failure_diagnostic(
    failure: OperationalSmokeFailure,
    *,
    cleanup_completed: bool,
) -> None:
    """Emit one fixed-schema, payload-free Actions annotation."""

    encoded = json.dumps(
        _diagnostic_record(failure, cleanup_completed=cleanup_completed),
        sort_keys=True,
        separators=(",", ":"),
    )
    try:
        print(
            "::error title=DeepReason installed-wheel operational smoke failed::"
            f"{encoded}",
            file=sys.stderr,
            flush=True,
        )
    except Exception:
        return


def _failure_exit_status(failure: OperationalSmokeFailure) -> int:
    if failure.exit_status is not None and 1 <= failure.exit_status <= 255:
        return failure.exit_status
    return 1


def _cleanup_temp_root(temp_root: Path | None) -> bool:
    if temp_root is None:
        return True
    try:
        shutil.rmtree(temp_root)
        return not temp_root.exists()
    except OSError:
        return False


def _finalize_operational_smoke(
    failure: OperationalSmokeFailure | None,
    *,
    temp_root: Path | None,
) -> int:
    cleanup_completed = _cleanup_temp_root(temp_root)
    if failure is None and not cleanup_completed:
        failure = OperationalSmokeFailure(
            stage=STAGE_CLEANUP,
            failure_kind=FAILURE_CLEANUP,
        )
    if failure is not None:
        _emit_failure_diagnostic(
            failure,
            cleanup_completed=cleanup_completed,
        )
        return _failure_exit_status(failure)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[1]
    temp_root: Path | None = None
    failure: OperationalSmokeFailure | None = None
    succeeded = False
    stage = STAGE_CREATE_ENVIRONMENT
    try:
        temp_root = Path(tempfile.mkdtemp(prefix="deepreason-wheel-operational-"))
        provider_port = _unused_loopback_port()
        provider_state_path = temp_root / "loopback-provider-counts.json"
        outputs: list[str] = []
        transcripts: list[str] = []
        stage = STAGE_BUILD_WHEEL
        wheel = _build_wheel(repo, temp_root)
        _inspect_operational_wheel(wheel)
        stage = STAGE_CREATE_ENVIRONMENT
        environment = temp_root / "installed environment with spaces"
        venv.EnvBuilder(
            with_pip=True,
            clear=True,
            system_site_packages=False,
        ).create(environment)
        if "include-system-site-packages = false" not in (
            environment / "pyvenv.cfg"
        ).read_text(encoding="utf-8").casefold():
            raise AssertionError("operational venv inherited system site packages")
        python = _venv_executable(environment, "python")
        deepreason = _venv_executable(environment, "deepreason")
        mcp = _venv_executable(environment, "deepreason-mcp")
        home = temp_root / "blank home"
        work = temp_root / "unrelated empty directory"
        home.mkdir()
        work.mkdir()
        clean_env = _environment(
            home,
            provider_port=provider_port,
            provider_state_path=provider_state_path,
        )
        stage = STAGE_INSTALL_WHEEL
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                str(wheel),
            ],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        _run(
            [str(python), "-m", "pip", "check"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        fixture_path = _install_loopback_fixture(
            repo=repo,
            python=python,
            work=work,
            env=clean_env,
            stage=stage,
        )
        if environment.resolve() not in fixture_path.resolve().parents:
            raise AssertionError("external provider fixture escaped the disposable venv")

        stage = STAGE_INSTALL_WHEEL
        imported = json.loads(
            _run(
                [
                    str(python),
                    "-c",
                    (
                        "import deepreason,json,sys;"
                        "print(json.dumps({'file':deepreason.__file__,'path':sys.path}))"
                    ),
                ],
                cwd=work,
                env=clean_env,
                stage=stage,
            ).stdout
        )
        module_file = Path(imported["file"]).resolve()
        if environment.resolve() not in module_file.parents or repo.resolve() in module_file.parents:
            raise AssertionError("installed import escaped the clean venv")
        if any(str(repo.resolve()).casefold() in str(item).casefold() for item in imported["path"]):
            raise AssertionError("repository path appears in installed sys.path")

        stage = STAGE_READINESS
        bare = _run(
            [str(deepreason)],
            cwd=work,
            env=clean_env,
            stage=stage,
            expected=(1,),
        )
        outputs.extend((bare.stdout, bare.stderr))
        if "Next action: deepreason setup" not in bare.stdout:
            raise AssertionError("bare deepreason did not report setup readiness")

        endpoint = f"http://127.0.0.1:{provider_port}/v1"
        stage = STAGE_SETUP_PROFILE
        setup = _run(
            [
                str(deepreason),
                "setup",
                "--provider",
                "generic",
                "--endpoint",
                endpoint,
                "--model",
                "deepreason-loopback-v6",
                "--model-revision",
                "fixture-1",
                "--family",
                "deterministic-loopback",
                "--context-window-tokens",
                "1000000",
                "--maximum-completion-tokens",
                "512",
                "--credential-env",
                TEST_CREDENTIAL_ENV,
            ],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((setup.stdout, setup.stderr))
        stage = STAGE_READINESS
        calls_before_status = _provider_counts(provider_state_path)["total_calls"]
        unqualified = _run(
            [str(deepreason), "status", "--json"],
            cwd=work,
            env=clean_env,
            stage=stage,
            expected=(1,),
        )
        outputs.extend((unqualified.stdout, unqualified.stderr))
        unqualified_payload = json.loads(unqualified.stdout)
        if unqualified_payload["qualification_state"] != "unqualified":
            raise AssertionError("setup did not transition readiness to unqualified")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_status,
        )

        stage = STAGE_QUALIFY
        qualified = _run(
            [str(deepreason), "qualify", "--yes"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((qualified.stdout, qualified.stderr))
        notice = re.search(
            r"maximum expected provider calls: ([0-9]+)", qualified.stderr
        )
        if notice is None or int(notice.group(1)) != 240:
            raise AssertionError("qualification did not announce the frozen maximum")
        counts = _provider_counts(provider_state_path)
        if counts != {"qualification_calls": 80, "total_calls": 80}:
            raise AssertionError(
                "qualification did not make exactly 80 loopback calls"
            )

        stage = STAGE_READINESS
        calls_before_status = counts["total_calls"]
        ready = _run(
            [str(deepreason), "status", "--json"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((ready.stdout, ready.stderr))
        ready_payload = json.loads(ready.stdout)
        if not ready_payload["ready"] or ready_payload["product_mode"] != "v6-only":
            raise AssertionError("installed status did not become V6 ready")
        module_status = _run(
            [str(python), "-m", "deepreason", "status", "--json"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((module_status.stdout, module_status.stderr))
        if json.loads(module_status.stdout) != ready_payload:
            raise AssertionError("python -m status differs from the console")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_status,
        )

        stage = STAGE_QUALIFY
        calls_before_cache = _provider_counts(provider_state_path)["total_calls"]
        cached = _run(
            [str(deepreason), "qualify", "--yes", "--json"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((cached.stdout, cached.stderr))
        cached_payload = json.loads(cached.stdout)
        if not cached_payload["cache_reused"] or cached_payload["maximum_expected_provider_calls"] != 0:
            raise AssertionError("completed qualification cache was not reused")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_cache,
        )

        stage = STAGE_REASON
        first = _run_reason(
            [str(deepreason), "reason", "Why can layered explanations remain testable?"],
            cwd=work,
            env=clean_env,
            home=home,
            ready_marker=temp_root / ".initial-reason-loopback-ready",
            expected=(0, 5),
            timeout=600,
        )
        outputs.extend((first.stdout, first.stderr))
        first_result = json.loads(first.stdout)
        _assert_committed_terminal(first_result)
        first_run_id = first_result["run_id"]
        if _provider_counts(provider_state_path)["qualification_calls"] != 80:
            raise AssertionError("question preparation silently requalified")

        stage = STAGE_MCP_INITIALIZE
        calls_before_retrieval = _provider_counts(provider_state_path)["total_calls"]
        registration = _run(
            [str(deepreason), "mcp-registration"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((registration.stdout, registration.stderr))
        registration_payload = json.loads(registration.stdout)
        registered = registration_payload["mcpServers"]["deepreason"]
        if registered != {"command": str(mcp.resolve()), "args": []} or " " not in registered["command"]:
            raise AssertionError("generic MCP registration mishandled the installed spaced path")

        stage = STAGE_MCP_INITIALIZE
        first_client = MCPClient(mcp, cwd=work, env=clean_env)
        _assert_exact_tools(_tool_list(first_client))
        stage = STAGE_MCP_REQUEST
        first_status = first_client.tool(
            "run_status",
            {"run_id": first_run_id},
            stage=stage,
        )
        first_retrieved = first_client.tool(
            "run_result",
            {"run_id": first_run_id},
            stage=stage,
        )
        _assert_committed_terminal(first_retrieved)
        if first_retrieved != {key: value for key, value in first_result.items()}:
            raise AssertionError("durable CLI result changed when retrieved through MCP")
        if first_status.get("state") != "completed":
            raise AssertionError("restarted process did not recover CLI run status")
        stage = STAGE_CONTINUATION_REJECTION
        calls_before_rejection = _provider_counts(provider_state_path)["total_calls"]
        rejected_continuation = first_client.tool_error(
            "continue_run",
            {
                "run_id": first_run_id,
                "budget": {"cycles": 6, "token_budget": 100000},
            },
            stage=stage,
        )
        _assert_non_resumable_rejection(rejected_continuation)
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_rejection,
        )
        if first_client.tool(
            "run_result",
            {"run_id": first_run_id},
            stage=stage,
        ) != first_retrieved:
            raise AssertionError("rejected continuation changed the terminal result")
        transcripts.extend(first_client.transcript)
        first_client.close(stage=stage)
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_retrieval,
        )

        stage = STAGE_REASON
        resumable = _run_reason(
            [
                str(deepreason),
                "reason",
                RESUMABLE_STOP_QUESTION,
                "--cycles",
                "12",
                "--token-budget",
                "200000",
            ],
            cwd=work,
            env=clean_env,
            home=home,
            ready_marker=temp_root / ".resumable-reason-loopback-ready",
            expected=(0, 5),
            timeout=600,
        )
        outputs.extend((resumable.stdout, resumable.stderr))
        resumable_result = json.loads(resumable.stdout)
        _assert_resumable_terminal(resumable_result)
        resumable_run_id = resumable_result["run_id"]
        stage = STAGE_CONTINUATION_RESUME
        calls_before_resumable_retrieval = _provider_counts(provider_state_path)[
            "total_calls"
        ]
        continuation_client = MCPClient(mcp, cwd=work, env=clean_env)
        _assert_exact_tools(_tool_list(continuation_client))
        resumable_retrieved = continuation_client.tool(
            "run_result",
            {"run_id": resumable_run_id},
            stage=stage,
        )
        if resumable_retrieved != resumable_result:
            raise AssertionError("resumable CLI result changed when retrieved through MCP")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_resumable_retrieval,
        )
        continued = continuation_client.tool(
            "continue_run",
            {
                "run_id": resumable_run_id,
                "budget": {"cycles": 6, "token_budget": 100000},
            },
            stage=stage,
        )
        if continued.get("run_id") != resumable_run_id:
            raise AssertionError("continuation changed the opaque managed identity")
        _continued_status, final_resumable_result = _poll_terminal(
            continuation_client,
            resumable_run_id,
            prior_terminal_commitment_ref=resumable_result[
                "terminal_commitment_ref"
            ],
            stage=stage,
        )
        _assert_resumable_terminal(final_resumable_result)
        transcripts.extend(continuation_client.transcript)
        continuation_client.close(stage=stage)

        stage = STAGE_RESTART_RECOVERY
        calls_before_restart = _provider_counts(provider_state_path)["total_calls"]
        restarted_first = MCPClient(mcp, cwd=work, env=clean_env)
        _assert_exact_tools(_tool_list(restarted_first))
        restarted_first_status = restarted_first.tool(
            "run_status",
            {"run_id": resumable_run_id},
            stage=stage,
        )
        restarted_first_result = restarted_first.tool(
            "run_result",
            {"run_id": resumable_run_id},
            stage=stage,
        )
        transcripts.extend(restarted_first.transcript)
        restarted_first.close(stage=stage)
        if (
            restarted_first_status.get("state") != "completed"
            or restarted_first_result != final_resumable_result
        ):
            raise AssertionError("continued CLI run did not survive process restart")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_restart,
        )
        stage = STAGE_REPLAY_VALIDATION
        _assert_durable_replay(home, first_run_id)
        _assert_durable_replay(home, resumable_run_id)

        stage = STAGE_BUDGET_REJECTION
        before_roots = {path.name for path in (home / ".deepreason" / "runs").iterdir() if path.is_dir()}
        before_calls = _provider_counts(provider_state_path)["total_calls"]
        over_budget = _run(
            [str(deepreason), "reason", "This must not start", "--cycles", "13"],
            cwd=work,
            env=clean_env,
            stage=stage,
            expected=(1,),
        )
        outputs.extend((over_budget.stdout, over_budget.stderr))
        after_roots = {path.name for path in (home / ".deepreason" / "runs").iterdir() if path.is_dir()}
        if (
            before_roots != after_roots
            or before_calls != _provider_counts(provider_state_path)["total_calls"]
        ):
            raise AssertionError("over-ceiling reasoning mutated state or called the provider")

        stage = STAGE_REASON
        second = _run_reason(
            [
                str(deepreason),
                "reason",
                "How can deterministic records make disagreement inspectable?",
                "--cycles",
                "1",
            ],
            cwd=work,
            env=clean_env,
            home=home,
            ready_marker=temp_root / ".second-reason-loopback-ready",
            timeout=180,
        )
        outputs.extend((second.stdout, second.stderr))
        _assert_committed_terminal(json.loads(second.stdout))
        if _provider_counts(provider_state_path)["qualification_calls"] != 80:
            raise AssertionError("second preparation made qualification calls")

        stage = STAGE_MCP_REQUEST
        mcp_client = MCPClient(mcp, cwd=work, env=clean_env)
        _assert_exact_tools(_tool_list(mcp_client))
        started = mcp_client.tool(
            "start_run",
            {
                "question": "What makes a new explanation robust under criticism?",
                "budget": {"cycles": 1, "token_budget": 50000},
            },
            stage=stage,
        )
        mcp_run_id = started["run_id"]
        _status, mcp_result = _poll_terminal(
            mcp_client,
            mcp_run_id,
            stage=stage,
        )
        transcripts.extend(mcp_client.transcript)
        mcp_client.close(stage=stage)
        _assert_committed_terminal(mcp_result)
        if _provider_counts(provider_state_path)["qualification_calls"] != 80:
            raise AssertionError("MCP preparation initiated qualification")

        stage = STAGE_RESTART_RECOVERY
        calls_before_restart = _provider_counts(provider_state_path)["total_calls"]
        restarted = MCPClient(mcp, cwd=work, env=clean_env)
        _assert_exact_tools(_tool_list(restarted))
        restarted_status = restarted.tool(
            "run_status",
            {"run_id": mcp_run_id},
            stage=stage,
        )
        restarted_result = restarted.tool(
            "run_result",
            {"run_id": mcp_run_id},
            stage=stage,
        )
        transcripts.extend(restarted.transcript)
        restarted.close(stage=stage)
        if restarted_status.get("state") != "completed" or restarted_result != mcp_result:
            raise AssertionError("managed MCP identity did not survive server restart")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_restart,
        )

        stage = STAGE_MANIFEST_REJECTION
        calls_before_manifest_rejection = _provider_counts(provider_state_path)[
            "total_calls"
        ]
        runs_before_history = {
            path.name for path in (home / ".deepreason" / "runs").iterdir() if path.is_dir()
        }
        for version in range(1, 6):
            raw = work / f"historical-v{version}.json"
            raw.write_text(json.dumps({"schema_version": version, "nested": TEST_CREDENTIAL}))
            rejected = _run(
                [
                    str(deepreason),
                    "config",
                    "inspect",
                    "--run-manifest",
                    str(raw),
                ],
                cwd=work,
                env=clean_env,
                stage=stage,
                expected=(1,),
            )
            outputs.extend((rejected.stdout, rejected.stderr))
            if "UNSUPPORTED_RUN_MANIFEST_VERSION" not in rejected.stderr:
                raise AssertionError("historical manifest was not rejected")
            if TEST_CREDENTIAL in rejected.stdout + rejected.stderr:
                raise AssertionError("historical rejection echoed nested payload content")
        runs_after_history = {
            path.name for path in (home / ".deepreason" / "runs").iterdir() if path.is_dir()
        }
        if runs_before_history != runs_after_history:
            raise AssertionError("historical manifest rejection created a managed run root")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_manifest_rejection,
        )

        stage = STAGE_DISCLOSURE_CHECK
        _assert_no_disclosure(
            repo=repo,
            home=home,
            outputs=outputs,
            transcripts=transcripts,
        )
        final_provider_counts = _provider_counts(provider_state_path)
        print(
            "wheel operational smoke passed: installed setup, explicit qualification "
            f"({final_provider_counts['qualification_calls']} qualification calls; "
            f"{final_provider_counts['total_calls']} total calls), "
            "readiness, question-only "
            "reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP "
            "restart, budget ceiling, and pre-V6 fail-closed admission"
        )
        succeeded = True
    except OperationalSmokeFailure as error:
        failure = error
    except AssertionError:
        failure = OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_ASSERTION,
        )
    except Exception:
        failure = OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_UNEXPECTED,
        )

    if succeeded and args.keep:
        print(f"retained: {temp_root}")
        return 0

    return _finalize_operational_smoke(failure, temp_root=temp_root)


if __name__ == "__main__":
    raise SystemExit(main())
