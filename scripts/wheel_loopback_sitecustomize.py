"""External deterministic HTTP fixture for installed-wheel qualification.

The operational smoke copies this standard-library-only module into its
disposable virtual environment as ``sitecustomize.py``.  When explicitly
enabled through the smoke-only environment below, it starts a loopback
OpenAI-compatible endpoint inside each installed entry-point process.  It is
not a DeepReason module and is excluded from the wheel.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import threading


ENABLE_ENV = "DEEPREASON_WHEEL_LOOPBACK_FIXTURE"
PORT_ENV = "DEEPREASON_WHEEL_LOOPBACK_PORT"
STATE_ENV = "DEEPREASON_WHEEL_LOOPBACK_STATE"
READY_ENV = "DEEPREASON_WHEEL_LOOPBACK_READY"
CREDENTIAL_ENV = "DEEPREASON_LOOPBACK_SMOKE_KEY"
CREDENTIAL = "loopback-credential-must-never-appear"
RESUMABLE_STOP_MARKER = "typed resumable stop"


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
        return (
            min(maximum, max(minimum, 0.5))
            if maximum is not None
            else max(minimum, 0.5)
        )
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


def response_for_schema(schema: dict, _prompt: str) -> dict:
    """Return one semantically conservative value for an advertised schema."""

    title = schema.get("title")
    if (
        RESUMABLE_STOP_MARKER in _prompt.casefold()
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
        _prompt,
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
        raise AssertionError(f"provider fixture cannot satisfy schema {title!r}")
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


_STATE_LOCK = threading.Lock()


def _record_call(
    state_path: Path, *, qualification: bool, schema_title: str | None
) -> None:
    with _STATE_LOCK:
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
        else:
            state = {
                "errors": [],
                "qualification_calls": 0,
                "schema_titles": {},
                "total_calls": 0,
            }
        state["total_calls"] += 1
        state["qualification_calls"] += int(qualification)
        title = schema_title or "<untitled>"
        titles = state.setdefault("schema_titles", {})
        titles[title] = int(titles.get(title, 0)) + 1
        temporary = state_path.with_name(state_path.name + ".tmp")
        temporary.write_text(
            json.dumps(state, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, state_path)


def _record_error(state_path: Path, error: BaseException) -> None:
    with _STATE_LOCK:
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
        else:
            state = {
                "errors": [],
                "qualification_calls": 0,
                "schema_titles": {},
                "total_calls": 0,
            }
        state.setdefault("errors", []).append(
            {"message": str(error), "type": type(error).__name__}
        )
        temporary = state_path.with_name(state_path.name + ".tmp")
        temporary.write_text(
            json.dumps(state, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, state_path)


def _handler(state_path: Path):
    class Handler(BaseHTTPRequestHandler):
        server_version = "DeepReasonLoopback/1"

        def log_message(self, _format, *_args):
            return

        def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
            try:
                if self.path != "/v1/chat/completions":
                    self.send_error(404)
                    return
                if self.headers.get("Authorization") != f"Bearer {CREDENTIAL}":
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
                _record_call(
                    state_path,
                    qualification="Qualification case " in prompt,
                    schema_title=schema.get("title"),
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
                        "total_tokens": max(
                            2, (len(prompt) + len(content)) // 4
                        ),
                    },
                }
                encoded = json.dumps(payload, separators=(",", ":")).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
            except Exception as error:  # fixture failures must fail the real call
                _record_error(state_path, error)
                encoded = json.dumps(
                    {"error": {"type": type(error).__name__, "message": str(error)}}
                ).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

    return Handler


class _ReusableLoopbackServer(ThreadingHTTPServer):
    allow_reuse_address = True


def _start_if_enabled() -> None:
    if os.environ.get(ENABLE_ENV) != "1":
        return
    port = int(os.environ[PORT_ENV])
    state_path = Path(os.environ[STATE_ENV])
    server = _ReusableLoopbackServer(("127.0.0.1", port), _handler(state_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # The global reference keeps the listening socket alive for the process.
    globals()["_ACTIVE_SERVER"] = server
    ready_path = os.environ.get(READY_ENV)
    if ready_path:
        try:
            Path(ready_path).write_bytes(b"ready\n")
        except OSError:
            # Marker absence remains an unknown diagnostic state.  It must not
            # change whether the deterministic fixture can serve requests.
            pass


_start_if_enabled()
