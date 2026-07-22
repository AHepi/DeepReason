"""Closed MCP facade for managed question-only V6 reasoning.

Endpoint models never receive MCP tools and cannot select providers, routes,
policies, credentials, edit configuration, write events, or alter authority.
Paths, manifests, provider authority, and credentials are host-owned.
"""

import json
import re
import sys
import threading

from deepreason.application.text_runs import TEXT_RUN_SERVICE, TEXT_RUN_WORKERS

_PROTOCOL = "2024-11-05"
_MAX_MCP_TEXT_CHARS = 65_536
_MAX_MCP_INPUT_BYTES = 1_048_576
_MAX_MCP_TOOL_NAME_CHARS = 128
_MCP_TOOL_NAME = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_SAFE_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_RUN_ID = {
    "run_id": {
        "type": "string",
        "description": "opaque DeepReason-managed run identity",
        "minLength": 1,
        "maxLength": 128,
        "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
    }
}
# Read-only process-local views for integrations that wait on an accepted
# application-service worker. The application service owns the registry.
_RUN_THREADS = TEXT_RUN_WORKERS.threads
_RUN_LOCK = TEXT_RUN_WORKERS.lock


def _run_tools() -> list[dict]:
    from deepreason.preparation import PUBLIC_MAX_CYCLES, PUBLIC_MAX_TOKEN_BUDGET

    budget = {
        "type": "object",
        "properties": {
            "cycles": {"type": "integer", "minimum": 1, "maximum": PUBLIC_MAX_CYCLES},
            "token_budget": {
                "type": "integer",
                "minimum": 1,
                "maximum": PUBLIC_MAX_TOKEN_BUDGET,
            },
        },
        "additionalProperties": False,
    }
    return [
        {
            "name": "get_readiness",
            "description": "Read secret-free V6 provider and qualification readiness.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "start_run",
            "description": (
                "Prepare and start one normal question using host-owned V6 authority."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": _MAX_MCP_TEXT_CHARS,
                        "pattern": "^[^\\x00]+$",
                    },
                    "budget": budget,
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        },
        {
            "name": "run_status",
            "description": (
                "Read the latest operational snapshot and append-only progress "
                "events after since_seq; never changes graph state."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    **_RUN_ID,
                    "since_seq": {"type": "integer", "minimum": -1, "default": -1},
                },
                "required": ["run_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "run_result",
            "description": "Read the fixed terminal result for one managed run.",
            "inputSchema": {
                "type": "object", "properties": {**_RUN_ID},
                "required": ["run_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "continue_run",
            "description": (
                "Continue the same stopped run under its bound manifest and append "
                "new events without deleting prior stops."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    **_RUN_ID,
                    "budget": budget,
                },
                "required": ["run_id", "budget"],
                "additionalProperties": False,
            },
        },
        {
            "name": "cancel_run",
            "description": (
                "Request cancellation. The harness observes it only at the next "
                "safe completed-cycle boundary."
            ),
            "inputSchema": {
                "type": "object", "properties": {**_RUN_ID},
                "required": ["run_id"],
                "additionalProperties": False,
            },
        },
    ]


def _tools() -> list[dict]:
    from deepreason.mcp_help import tool_definitions as help_tool_definitions
    from deepreason.mcp_scratch_bridge import tool_definitions

    return [*_run_tools(), *tool_definitions(), *help_tool_definitions()]


class _MCPInputSchemaError(ValueError):
    """An untrusted MCP argument violates its advertised closed schema."""


def _schema_ref(root_schema: dict, reference: str) -> dict:
    if not reference.startswith("#/"):
        raise _MCPInputSchemaError("unsupported external schema reference")
    value: object = root_schema
    for component in reference[2:].split("/"):
        if not isinstance(value, dict) or component not in value:
            raise _MCPInputSchemaError("invalid local schema reference")
        value = value[component]
    if not isinstance(value, dict):
        raise _MCPInputSchemaError("invalid local schema reference")
    return value


def _validate_mcp_input(
    value: object,
    schema: dict,
    *,
    root_schema: dict,
    path: str = "",
) -> None:
    """Validate the small JSON-Schema subset used by the MCP contracts.

    Keeping this local avoids a new mandatory dependency while ensuring the
    runtime enforces the same closed fields and finite bounds advertised by
    ``tools/list``. Error text names only trusted schema paths, never caller
    values, credentials, prompts, or model-authored text.
    """

    if "$ref" in schema:
        _validate_mcp_input(
            value,
            _schema_ref(root_schema, schema["$ref"]),
            root_schema=root_schema,
            path=path,
        )
        return
    alternatives = schema.get("anyOf")
    if isinstance(alternatives, list):
        for alternative in alternatives:
            try:
                _validate_mcp_input(
                    value,
                    alternative,
                    root_schema=root_schema,
                    path=path,
                )
            except _MCPInputSchemaError:
                continue
            return
        raise _MCPInputSchemaError(f"{path or '/'} does not match an allowed shape")

    if "enum" in schema and value not in schema["enum"]:
        allowed = ", ".join(repr(item) for item in schema["enum"])
        raise _MCPInputSchemaError(
            f"{path or '/'} must be one of: {allowed}"
        )
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            raise _MCPInputSchemaError(f"{path or '/'} must be an object")
        properties = schema.get("properties") or {}
        required = schema.get("required") or []
        missing = [name for name in required if name not in value]
        if missing:
            if len(missing) == 1:
                child = f"{path}/{missing[0]}" if path else f"/{missing[0]}"
                raise _MCPInputSchemaError(f"{child} is required")
            raise _MCPInputSchemaError(
                f"{path or '/'} is missing required schema fields"
            )
        extras = [name for name in value if name not in properties]
        additional = schema.get("additionalProperties", True)
        if extras and additional is False:
            if (
                len(extras) == 1
                and isinstance(extras[0], str)
                and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", extras[0])
            ):
                child = f"{path}/{extras[0]}" if path else f"/{extras[0]}"
                raise _MCPInputSchemaError(f"{child} is outside the closed schema")
            raise _MCPInputSchemaError(
                f"{path or '/'} contains fields outside the closed schema"
            )
        for name, item in value.items():
            child = f"{path}/{name}" if path else f"/{name}"
            if name in properties:
                _validate_mcp_input(
                    item,
                    properties[name],
                    root_schema=root_schema,
                    path=child,
                )
            elif isinstance(additional, dict):
                _validate_mcp_input(
                    item,
                    additional,
                    root_schema=root_schema,
                    path=child,
                )
        return
    if expected == "array":
        if not isinstance(value, list):
            raise _MCPInputSchemaError(f"{path or '/'} must be an array")
        if len(value) < int(schema.get("minItems", 0)):
            raise _MCPInputSchemaError(f"{path or '/'} has too few items")
        maximum = schema.get("maxItems")
        if maximum is not None and len(value) > int(maximum):
            raise _MCPInputSchemaError(f"{path or '/'} has too many items")
        if schema.get("uniqueItems"):
            encoded = [
                json.dumps(item, sort_keys=True, separators=(",", ":"))
                for item in value
            ]
            if len(encoded) != len(set(encoded)):
                raise _MCPInputSchemaError(f"{path or '/'} contains duplicate items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate_mcp_input(
                    item,
                    item_schema,
                    root_schema=root_schema,
                    path=f"{path}/{index}" if path else f"/{index}",
                )
        return
    if expected == "string":
        if not isinstance(value, str):
            raise _MCPInputSchemaError(f"{path or '/'} must be a string")
        if len(value) < int(schema.get("minLength", 0)):
            raise _MCPInputSchemaError(f"{path or '/'} is too short")
        maximum = schema.get("maxLength")
        if maximum is not None and len(value) > int(maximum):
            raise _MCPInputSchemaError(f"{path or '/'} is too long")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, value) is None:
            raise _MCPInputSchemaError(f"{path or '/'} has an invalid format")
        return
    if expected == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise _MCPInputSchemaError(f"{path or '/'} must be an integer")
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            raise _MCPInputSchemaError(f"{path or '/'} is below its minimum")
        if maximum is not None and value > maximum:
            raise _MCPInputSchemaError(f"{path or '/'} is above its maximum")
        return
    if expected == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise _MCPInputSchemaError(f"{path or '/'} must be a number")
        return
    if expected == "boolean" and not isinstance(value, bool):
        raise _MCPInputSchemaError(f"{path or '/'} must be a boolean")
    if expected == "null" and value is not None:
        raise _MCPInputSchemaError(f"{path or '/'} must be null")


def _missing_manifest_credentials(manifest) -> list[str]:
    from deepreason.application.text_runs import missing_manifest_credentials

    # The application may use configured environment-variable names to check
    # presence, but MCP responses must not reveal those credential references.
    return (
        ["configured provider credential"]
        if missing_manifest_credentials(manifest)
        else []
    )


def _resolve_managed_root(run_id: str):
    from deepreason.preparation import resolve_managed_run_root

    return resolve_managed_run_root(run_id)


def _public_budget(arguments: dict):
    from deepreason.application.models import RunBudgetIntentV1
    from deepreason.preparation import PUBLIC_DEFAULT_CYCLES, PUBLIC_DEFAULT_TOKEN_BUDGET

    raw = arguments.get("budget") or {}
    return RunBudgetIntentV1(
        cycles=raw.get("cycles", PUBLIC_DEFAULT_CYCLES),
        token_budget=raw.get("token_budget", PUBLIC_DEFAULT_TOKEN_BUDGET),
    )


def _require_readiness():
    from deepreason.readiness import get_readiness

    readiness = get_readiness()
    if not readiness.ready:
        raise ValueError(f"READINESS_REQUIRED: {readiness.next_action}")
    return readiness


def _preparation_service():
    from deepreason.preparation import RunPreparationService

    return RunPreparationService()


def _start_run(
    arguments: dict,
    *,
    continuation: bool = False,
    progress_callback=None,
) -> dict:
    """Start one run-neutral worker under a durable cross-process lock."""
    from deepreason.application.models import ContinueTextRunIntentV1
    from deepreason.application.intents import start_text_run_intent

    budget = _public_budget(arguments)
    if continuation:
        root = _resolve_managed_root(arguments["run_id"])
        accepted = TEXT_RUN_SERVICE.continue_run(
            ContinueTextRunIntentV1(
                root=str(root),
                budget=budget,
            ),
            progress_callback=progress_callback,
            credential_checker=_missing_manifest_credentials,
        )
    else:
        _require_readiness()
        from deepreason.preparation import RunPreparationRequestV1

        prepared = _preparation_service().prepare(
            RunPreparationRequestV1(question=arguments["question"], budget=budget)
        )
        accepted = TEXT_RUN_SERVICE.start(
            start_text_run_intent(
                root=prepared.root,
                workload=prepared.workload,
                run_manifest_ref=prepared.run_manifest_ref,
                cycles=budget.cycles,
                token_budget=budget.token_budget,
            ),
            progress_callback=progress_callback,
            credential_checker=_missing_manifest_credentials,
        )
        return {
            "state": accepted.lifecycle,
            "run_id": prepared.managed_run_id,
            "status_operation": "run_status",
            "result_operation": "run_result",
        }
    return {
        "state": accepted.lifecycle,
        "run_id": arguments["run_id"],
        "status_operation": "run_status",
        "result_operation": "run_result",
    }

def _read_run_result(root) -> dict:
    from deepreason.application.models import InspectTextRunIntentV1

    return TEXT_RUN_SERVICE.result(
        InspectTextRunIntentV1(root=str(root))
    ).presentation_payload()


def _managed_response(run_id: str, payload: dict) -> dict:
    """Remove host path authority and pin the caller-facing managed identity."""

    safe = dict(payload)
    for field in ("root", "run_manifest_ref", "manifest_path"):
        safe.pop(field, None)
    safe["run_id"] = run_id
    return safe


def _safe_tool_error(error: Exception) -> str:
    """Expose stable codes, never arbitrary provider, path, or payload text."""

    message = str(error)
    if message.startswith(("MCP_INPUT_INVALID:", "MCP_TOOL_NOT_EXPOSED:")):
        return f"{type(error).__name__}: {message}"
    code = getattr(error, "code", None)
    if not isinstance(code, str) or _SAFE_ERROR_CODE.fullmatch(code) is None:
        matched = re.match(r"^([A-Z][A-Z0-9_]{2,127})(?::|\b)", message)
        code = matched.group(1) if matched is not None else "MCP_OPERATION_FAILED"
    return f"{type(error).__name__}: {code}"


_RUN_TOOL_NAMES = frozenset(
    {"get_readiness", "start_run", "run_status", "run_result", "continue_run", "cancel_run"}
)


def call_tool(name: str, arguments: dict, *, progress_callback=None) -> str:
    """Execute one tool; returns the text payload (raises on error)."""
    if (
        not isinstance(name, str)
        or len(name) > _MAX_MCP_TOOL_NAME_CHARS
        or _MCP_TOOL_NAME.fullmatch(name) is None
    ):
        raise ValueError("MCP_TOOL_NOT_EXPOSED: invalid tool name")
    if not isinstance(arguments, dict):
        raise ValueError("MCP_INPUT_INVALID: arguments must be an object")
    try:
        encoded_arguments = json.dumps(
            arguments,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("MCP_INPUT_INVALID: arguments must contain JSON values") from error
    if len(encoded_arguments) > _MAX_MCP_INPUT_BYTES:
        raise ValueError("MCP_INPUT_INVALID: arguments exceed the fixed request bound")
    exposed = {tool["name"]: tool for tool in _tools()}
    if name not in exposed:
        raise ValueError("MCP_TOOL_NOT_EXPOSED: requested tool is outside the active surface")
    try:
        _validate_mcp_input(
            arguments,
            exposed[name]["inputSchema"],
            root_schema=exposed[name]["inputSchema"],
        )
    except _MCPInputSchemaError as error:
        raise ValueError(f"MCP_INPUT_INVALID: {name}: {error}") from error
    from deepreason.mcp_help import TOOL_NAMES as help_tools

    if name in help_tools:
        from deepreason.mcp_help import call_tool as call_help_tool

        return json.dumps(
            call_help_tool(name, arguments, active_tool_names=set(exposed)),
            indent=2,
            sort_keys=True,
        )
    from deepreason.mcp_scratch_bridge import TOOL_NAMES as scratch_bridge_tools

    if name in scratch_bridge_tools:
        from deepreason.mcp_scratch_bridge import call_tool_text

        return call_tool_text(
            name,
            arguments,
            progress_callback=progress_callback,
        )

    if name not in _RUN_TOOL_NAMES:
        raise ValueError("MCP_TOOL_NOT_EXPOSED: requested tool is outside the active surface")

    if name == "get_readiness":
        from deepreason.readiness import get_readiness

        return get_readiness().model_dump_json(by_alias=True)

    if name == "start_run":
        return json.dumps(
            _start_run(arguments, progress_callback=progress_callback),
            indent=2,
            sort_keys=True,
        )

    from deepreason.cli.main import _admit_v6_root

    root = _resolve_managed_root(arguments["run_id"])
    _admit_v6_root(root, operation=f"MCP {name}")

    if name == "run_status":
        from deepreason.application.models import InspectTextRunIntentV1

        return json.dumps(
            _managed_response(
                arguments["run_id"],
                TEXT_RUN_SERVICE.inspect(
                    InspectTextRunIntentV1(
                        root=str(root), since_seq=int(arguments.get("since_seq", -1))
                    )
                ).presentation_payload(),
            ),
            indent=2,
            sort_keys=True,
        )

    if name == "run_result":
        return json.dumps(
            _managed_response(arguments["run_id"], _read_run_result(root)),
            indent=2,
            sort_keys=True,
        )

    if name == "continue_run":
        return json.dumps(
            _start_run(
                arguments,
                continuation=True,
                progress_callback=progress_callback,
            ),
            indent=2,
            sort_keys=True,
        )

    if name == "cancel_run":
        from deepreason.application.models import CancelTextRunIntentV1

        return json.dumps(
            _managed_response(
                arguments["run_id"],
                TEXT_RUN_SERVICE.cancel(
                    CancelTextRunIntentV1(root=str(root))
                ).presentation_payload(),
            ),
            indent=2,
            sort_keys=True,
        )

    raise ValueError(f"unknown tool: {name}")


def handle(message: dict, *, notification_sink=None) -> dict | None:
    """One JSON-RPC message in, one response out (None for notifications)."""
    method = message.get("method")
    msg_id = message.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": _PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "deepreason", "version": "0.1.0"},
                "instructions": (
                    "First action: call get_readiness. When ready, call start_run "
                    "with a normal question and optional bounded budget."
                ),
            },
        }
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": _tools()}}
    if method == "tools/call":
        params = message["params"] if "params" in message else {}
        try:
            if not isinstance(params, dict):
                raise ValueError("MCP_INPUT_INVALID: tools/call params must be an object")
            if set(params) - {"name", "arguments", "_meta"}:
                raise ValueError(
                    "MCP_INPUT_INVALID: tools/call params contain unknown fields"
                )
            try:
                params_size = len(
                    json.dumps(
                        params,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "MCP_INPUT_INVALID: tools/call params must contain JSON values"
                ) from error
            if params_size > _MAX_MCP_INPUT_BYTES:
                raise ValueError(
                    "MCP_INPUT_INVALID: tools/call params exceed the fixed request bound"
                )
            meta = params["_meta"] if "_meta" in params else {}
            if not isinstance(meta, dict):
                raise ValueError("MCP_INPUT_INVALID: _meta must be an object")
            if set(meta) - {"progressToken"}:
                raise ValueError("MCP_INPUT_INVALID: _meta contains unknown fields")
            progress_token = meta.get("progressToken")
            if progress_token is not None and (
                isinstance(progress_token, bool)
                or not isinstance(progress_token, (str, int))
                or (isinstance(progress_token, str) and len(progress_token) > 256)
                or (
                    isinstance(progress_token, int)
                    and not -(2**63) <= progress_token <= 2**63 - 1
                )
            ):
                raise ValueError("MCP_INPUT_INVALID: progressToken is invalid")

            def progress_callback(event: dict) -> None:
                if notification_sink is None or progress_token is None:
                    return
                notification_sink(
                    {
                        "jsonrpc": "2.0",
                        "method": "notifications/progress",
                        "params": {
                            "progressToken": progress_token,
                            "progress": event["seq"],
                            "message": event.get("message") or event.get("activity") or "",
                        },
                    }
                )

            text = call_tool(
                params.get("name", ""),
                params["arguments"] if "arguments" in params else {},
                progress_callback=progress_callback,
            )
            result = {"content": [{"type": "text", "text": text}], "isError": False}
        except Exception as e:  # tool errors are results, not protocol errors
            result = {
                "content": [{"type": "text", "text": _safe_tool_error(e)}],
                "isError": True,
            }
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    if msg_id is None:
        return None  # unknown notification: ignore per JSON-RPC
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": "method not found"},
    }


def main() -> int:
    """Newline-delimited JSON-RPC over stdio (MCP stdio transport)."""
    from deepreason.easy import load_credentials

    load_credentials()  # keys stored by `deepreason setup` reach MCP runs too
    output_lock = threading.Lock()

    def emit(payload: dict) -> None:
        with output_lock:
            print(json.dumps(payload), flush=True)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            emit(
                {"jsonrpc": "2.0", "id": None,
                 "error": {"code": -32700, "message": f"parse error: {e}"}},
            )
            continue
        response = handle(message, notification_sink=emit)
        if response is not None:
            emit(response)
    return 0


if __name__ == "__main__":
    sys.exit(main())
