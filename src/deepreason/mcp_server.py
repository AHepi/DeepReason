"""Narrow MCP facade for harness-owned reasoning and website execution.

Endpoint models never receive MCP tools and cannot select routes, edit
configuration, browse repositories, write events, or alter guards/status.
The historical research/operator verbs remain quarantined behind
``DEEPREASON_ENABLE_LEGACY_MCP=1`` for explicit migration work.
"""

import json
import os
import re
import sys
import threading
from pathlib import Path

from deepreason.locking import (
    MAKE_OPERATOR_LOCK_NAME,
    RUN_OPERATOR_LOCK_NAME,
    ProcessLockBusy,
    operator_locks,
)

_PROTOCOL = "2024-11-05"
_MAX_MCP_PATH_CHARS = 4_096
_MAX_MCP_TEXT_CHARS = 65_536
_MAX_MCP_INPUT_BYTES = 1_048_576
_MAX_MCP_TOOL_NAME_CHARS = 128
_MCP_TOOL_NAME = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_ROOT = {
    "root": {
        "type": "string",
        "description": "harness state directory",
        "default": ".deepreason",
        "minLength": 1,
        "maxLength": _MAX_MCP_PATH_CHARS,
        "pattern": "^[^\\x00]+$",
    }
}
_CONFIG = {
    "config": {
        "type": "string",
        "description": "partial YAML profile path (default: built-in typed defaults)",
        "minLength": 1,
        "maxLength": _MAX_MCP_PATH_CHARS,
        "pattern": "^[^\\x00]+$",
    }
}
_MAKE_STATUS_NAME = "make-status.json"
_MAKE_OPERATOR_LOCK_NAME = MAKE_OPERATOR_LOCK_NAME
_RUN_OPERATOR_LOCK_NAME = RUN_OPERATOR_LOCK_NAME
_MAKE_THREADS: dict[str, threading.Thread] = {}
_MAKE_LOCK = threading.Lock()
_RUN_THREADS: dict[str, threading.Thread] = {}
_RUN_LOCK = threading.Lock()


def _limit_schema(*, legacy_zero: bool = False) -> dict:
    minimum = 0 if legacy_zero else 1
    return {
        "anyOf": [
            {"type": "integer", "minimum": minimum},
            {"type": "string", "enum": ["unlimited"]},
        ]
    }


def _run_tools() -> list[dict]:
    budget = {
        "type": "object",
        "properties": {
            "cycles": _limit_schema(),
            "token_budget": _limit_schema(legacy_zero=True),
        },
        "required": ["cycles", "token_budget"],
        "additionalProperties": False,
    }
    return [
        {
            "name": "start_run",
            "description": (
                "Start a harness-owned reasoning run from a typed workload and "
                "precompiled immutable RunManifest. Exposes no shell, path browser, "
                "route editor, event writer, guard bypass, or status setter."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    **_ROOT,
                    "workload": {"type": "string", "enum": ["text"]},
                    "problem": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": _MAX_MCP_TEXT_CHARS,
                                "pattern": "^[^\\x00]+$",
                            },
                        },
                        "required": ["description"],
                        "additionalProperties": False,
                    },
                    "run_manifest_ref": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": _MAX_MCP_PATH_CHARS,
                        "pattern": "^[^\\x00]+$",
                    },
                    "budget": budget,
                },
                "required": ["workload", "problem", "run_manifest_ref", "budget"],
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
                    **_ROOT,
                    "since_seq": {"type": "integer", "minimum": -1, "default": -1},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "run_result",
            "description": "Read the fixed terminal run result below the run root.",
            "inputSchema": {
                "type": "object", "properties": {**_ROOT},
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
                    **_ROOT,
                    "budget": budget,
                    "expected_manifest_digest": {
                        "type": "string",
                        "minLength": 64,
                        "maxLength": 64,
                        "pattern": "^[0-9a-f]{64}$",
                    },
                },
                "required": ["budget"],
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
                "type": "object", "properties": {**_ROOT},
                "additionalProperties": False,
            },
        },
    ]


def _legacy_tools() -> list[dict]:
    return [
        *_run_tools(),
        {
            "name": "start_make",
            "description": (
                "Start the deterministic website harness with a typed problem and a "
                "precompiled immutable RunManifest. The operation exposes no shell, "
                "repository browser, model selector, config editor, guard control, "
                "event writer, or status setter."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    **_ROOT,
                    "problem": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": _MAX_MCP_TEXT_CHARS,
                                "pattern": "^[^\\x00]+$",
                            },
                        },
                        "required": ["description"],
                        "additionalProperties": False,
                    },
                    "run_manifest_ref": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": _MAX_MCP_PATH_CHARS,
                        "pattern": "^[^\\x00]+$",
                    },
                    "budget": {
                        "type": "object",
                        "properties": {
                            "cycles": {"type": "integer", "minimum": 1, "default": 10},
                            "token_budget": {
                                "type": "integer", "minimum": 0,
                                "description": "0 means unlimited",
                            },
                        },
                        "additionalProperties": False,
                    },
                },
                "required": ["problem", "run_manifest_ref", "budget"],
                "additionalProperties": False,
            },
        },
        {
            "name": "make_status",
            "description": "Read operational progress for start_make; never changes harness state.",
            "inputSchema": {
                "type": "object", "properties": {**_ROOT},
                "additionalProperties": False,
            },
        },
        {
            "name": "make_result",
            "description": (
                "Read a successful or typed terminal-failure start_make result; "
                "never changes harness state or reads arbitrary files."
            ),
            "inputSchema": {
                "type": "object", "properties": {**_ROOT},
                "additionalProperties": False,
            },
        },
        {
            "name": "seed_problem",
            "description": (
                "Register a problem on the frontier, with its commitments and "
                "(optionally) a rubric standard. Criteria including "
                "'skeleton-wf' auto-register the skeleton well-formedness "
                "program. Nothing is ever deleted; re-seeding an id is an error."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    **_ROOT,
                    "problem": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "description": {"type": "string"},
                            "criteria": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["id", "description"],
                    },
                    "commitments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"id": {"type": "string"}, "eval": {"type": "string"}},
                            "required": ["id", "eval"],
                        },
                    },
                    "standard": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "rubric": {"type": "string"},
                            "mode": {"type": "string", "enum": ["absolute", "anchored", "pairwise"]},
                        },
                        "required": ["id", "rubric"],
                    },
                },
                "required": ["problem"],
            },
        },
        {
            "name": "run_cycles",
            "description": (
                "Fund N scheduler cycles (Conj -> Crit -> Adj with schools, "
                "capture control, budget triage). Requires LLM roles in the "
                "config knob file's role table — any OpenAI-compatible "
                "provider works; api keys come from the named env vars. "
                "token_budget is a hard ceiling; the run stops gracefully."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    **_ROOT,
                    **_CONFIG,
                    "cycles": {"type": "integer", "minimum": 1},
                    "token_budget": {"type": "integer", "description": "hard prompt+completion cap"},
                },
                "required": ["cycles"],
            },
        },
        {
            "name": "frontier",
            "description": "List problems on the frontier and the surviving (accepted) artifacts per problem.",
            "inputSchema": {"type": "object", "properties": {**_ROOT}},
        },
        {
            "name": "theory",
            "description": "Render the theory view for an artifact id (or unique prefix): content, attack surface, refs, status history.",
            "inputSchema": {
                "type": "object",
                "properties": {**_ROOT, "id": {"type": "string"}},
                "required": ["id"],
            },
        },
        {
            "name": "narrate",
            "description": "Render the event log as chain-of-thought prose: proposals, attacks, refutations, reinstatements and blocked rulings joined by logical connectors. Deterministic view of the log.",
            "inputSchema": {
                "type": "object",
                "properties": {**_ROOT, "window": {"type": "integer"}},
            },
        },
        {
            "name": "why",
            "description": "Print the attack/defence chain justifying an artifact's current status.",
            "inputSchema": {
                "type": "object",
                "properties": {**_ROOT, "id": {"type": "string"}},
                "required": ["id"],
            },
        },
        {
            "name": "eval_report",
            "description": "P6 eval report: per-role LLM metrics, attack validity, trial-guard blocks, capture dashboard, survivor HV/reach.",
            "inputSchema": {"type": "object", "properties": {**_ROOT, **_CONFIG}},
        },
        {
            "name": "docket",
            "description": (
                "Disagreement-ranked queue of cases awaiting an appellate "
                "ruling (§10.6) — the ONLY channel by which an operator's "
                "judgement enters the graph, and it is budgeted."
            ),
            "inputSchema": {"type": "object", "properties": {**_ROOT, **_CONFIG}},
        },
        {
            "name": "appellate_rule",
            "description": "Enter an appellate ruling on a docket case: a one-line holding calibrating a named standard. Registers a precedent artifact.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    **_ROOT,
                    "case_id": {"type": "string"},
                    "holding": {"type": "string"},
                    "standard": {"type": "string"},
                },
                "required": ["case_id", "holding", "standard"],
            },
        },
        {
            "name": "research_docket",
            "description": (
                "Open evidence requests (§12): research problems whose "
                "observation-valued commitment has no covering evidence. "
                "Read-only and deterministic. The operating agent reads "
                "this, retrieves with its OWN tools, then answers via "
                "submit_evidence or report_research_failure."
            ),
            "inputSchema": {"type": "object", "properties": {**_ROOT, **_CONFIG}},
        },
        {
            "name": "submit_evidence",
            "description": (
                "Register CANDIDATE evidence for a research problem. "
                "Registration is not coverage: the material enters as an "
                "attackable import artifact depending on an attackable "
                "source-reliability claim, is checked against the problem's "
                "relevance/scope commitments, and covers only while it "
                "remains accepted and supported. You never adjudicate, mark "
                "problems solved, or touch statuses — you only return "
                "candidate evidence."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    **_ROOT,
                    **_CONFIG,
                    "problem_id": {"type": "string"},
                    "source": {"type": "string", "description": "source identifier or URL"},
                    "content": {"type": "string", "description": "the retrieved source text"},
                    "retrieved_at": {
                        "type": "string",
                        "description": "agent-claimed retrieval time (stored as claim metadata only; event time is harness-controlled)",
                    },
                    "title": {"type": "string"},
                    "query": {"type": "string", "description": "the search query / retrieval trace"},
                },
                "required": ["problem_id", "source", "content"],
            },
        },
        {
            "name": "report_research_failure",
            "description": (
                "Record a FAILED retrieval attempt for a research problem "
                "(operational event, never evidence, never a verdict): the "
                "problem stays open and scheduled-pending."
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    **_ROOT,
                    "problem_id": {"type": "string"},
                    "source": {"type": "string", "description": "attempted source or query"},
                    "reason": {"type": "string"},
                    "category": {"type": "string", "description": "e.g. fetch-error | blocked | not-found | timeout"},
                    "detail": {"type": "string", "description": "optional HTTP status / exception class"},
                },
                "required": ["problem_id", "source", "reason"],
            },
        },
    ]


_NARROW_TOOL_NAMES = frozenset(
    {
        "start_run", "run_status", "run_result", "continue_run", "cancel_run",
        "start_make", "make_status", "make_result",
        "scratch_map", "scratch_search", "scratch_open", "scratch_related",
        "scratch_attention", "start_bridge", "bridge_status", "bridge_result",
        "bridge_claims",
    }
)


def _tools() -> list[dict]:
    from deepreason.mcp_scratch_bridge import tool_definitions

    tools = [*_legacy_tools(), *tool_definitions()]
    if os.environ.get("DEEPREASON_ENABLE_LEGACY_MCP") == "1":
        return tools
    return [tool for tool in tools if tool["name"] in _NARROW_TOOL_NAMES]


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
        raise _MCPInputSchemaError(f"{path or '/'} is outside its allowed values")
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            raise _MCPInputSchemaError(f"{path or '/'} must be an object")
        properties = schema.get("properties") or {}
        required = schema.get("required") or []
        missing = [name for name in required if name not in value]
        if missing:
            raise _MCPInputSchemaError(
                f"{path or '/'} is missing required schema fields"
            )
        extras = [name for name in value if name not in properties]
        additional = schema.get("additionalProperties", True)
        if extras and additional is False:
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


def _harness(arguments: dict):
    from deepreason.harness import Harness

    return Harness(Path(arguments.get("root") or ".deepreason"))


def _config(arguments: dict):
    from deepreason.config import load

    path = arguments.get("config")
    return load(Path(path) if path else None)


def _make_status_path(root: Path) -> Path:
    return root / _MAKE_STATUS_NAME


def _write_make_status(root: Path, payload: dict) -> None:
    """Atomic operational status write; no epistemic event or status change."""
    root.mkdir(parents=True, exist_ok=True)
    target = _make_status_path(root)
    temporary = root / (_MAKE_STATUS_NAME + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(target)


def _read_make_status(root: Path) -> dict:
    target = _make_status_path(root)
    if not target.exists():
        return {"state": "not-started", "root": str(root)}
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid make status record")
    return data


def _acquire_operator_locks(root: Path, *, owner: str):
    """Claim both legacy lock names so run and make cannot share one root."""
    try:
        return operator_locks(root, owner=owner, blocking=False)
    except ProcessLockBusy as error:
        raise ValueError(
            f"{owner.upper()}_ALREADY_RUNNING: another operator owns this run root"
        ) from error


def _acquire_make_operator_lock(root: Path):
    return _acquire_operator_locks(root, owner="make")


def _acquire_run_operator_lock(root: Path):
    return _acquire_operator_locks(root, owner="run")


def _release_operator_locks(locks) -> None:
    locks.release()


def _release_make_operator_lock(streams) -> None:
    _release_operator_locks(streams)


def _read_website_terminal(root: Path, manifest_sha256: str) -> dict | None:
    """Read and validate the workflow's one fixed terminal-summary record.

    This is operational output emitted by the deterministic website harness,
    not model data.  The MCP surface never accepts a path to it and never
    follows a path contained within it.
    """

    target = root / "website-terminal.json"
    if not target.exists():
        return None
    from deepreason.workflows.website import TerminalSummary

    summary = TerminalSummary.model_validate_json(target.read_text(encoding="utf-8"))
    if summary.manifest_sha256 not in (None, manifest_sha256):
        raise ValueError(
            "WEBSITE_TERMINAL_MANIFEST_MISMATCH: terminal summary belongs to "
            "a different frozen RunManifest"
        )
    return summary.model_dump(mode="json")


def _start_make(arguments: dict) -> dict:
    """Start one harness-owned worker; endpoint models receive no tools."""
    from deepreason.ops import require_full_engine
    from deepreason.run_manifest import (
        bind_run_manifest,
        load_run_manifest,
        materialize_run_config,
        preflight_payload,
    )

    root = Path(arguments.get("root") or ".deepreason").resolve()
    problem = arguments["problem"]
    if not isinstance(problem, dict) or not str(problem.get("description") or "").strip():
        raise ValueError("start_make.problem.description must be a non-empty string")
    budget = arguments["budget"]
    if not isinstance(budget, dict):
        raise ValueError("start_make.budget must be an object")
    cycles = int(budget.get("cycles", 10))
    if cycles < 1:
        raise ValueError("start_make.budget.cycles must be at least 1")
    raw_token_budget = budget.get("token_budget", 150_000)
    if raw_token_budget is not None and int(raw_token_budget) < 0:
        raise ValueError("start_make.budget.token_budget cannot be negative")
    token_budget = None if raw_token_budget in (None, 0) else int(raw_token_budget)

    manifest = load_run_manifest(arguments["run_manifest_ref"])
    require_full_engine(manifest, workload="website")
    preflight_payload(
        manifest,
        {"problem": {"description": problem["description"]}, "commitments": []},
    )
    output = root / "deliverable"
    key = str(root)

    missing_credentials = sorted({
        route.api_key_env
        for routes in manifest.roles.values()
        for route in routes
        if route.api_key_env and not os.environ.get(route.api_key_env)
    })
    if missing_credentials:
        raise ValueError(
            "MAKE_CREDENTIAL_MISSING: required environment variable(s) are "
            "unset: " + ", ".join(missing_credentials)
        )

    with _MAKE_LOCK:
        existing = _MAKE_THREADS.get(key)
        if existing is not None and existing.is_alive():
            raise ValueError("MAKE_ALREADY_RUNNING: this root already has an active make")
        operator_lock = _acquire_make_operator_lock(root)
        try:
            previous = _read_make_status(root)
            if previous.get("state") == "completed":
                raise ValueError(
                    "MAKE_ALREADY_STARTED: root is completed; choose a fresh root"
                )
            # Holding the durable operator lock proves that a persisted
            # `running` record has no live owner (for example, a crashed MCP
            # process). The same immutable manifest can safely recover it.
            stale_recovery = previous.get("state") == "running"
            previous_sha = previous.get("manifest_sha256")
            if stale_recovery and previous_sha not in (None, manifest.sha256):
                raise ValueError(
                    "MAKE_STALE_MANIFEST_CONFLICT: stale status belongs to a "
                    "different RunManifest"
                )
            # bind_run_manifest refuses a different pre-existing manifest.
            bind_run_manifest(manifest, root)
            config_path = materialize_run_config(manifest, root)
            status = {
                "state": "running",
                "root": str(root),
                "manifest_sha256": manifest.sha256,
                "problem": str(problem["description"]),
                "budget": {"cycles": cycles, "token_budget": raw_token_budget},
                "progress": [],
                "recovered_from_stale_status": stale_recovery,
            }
            _write_make_status(root, status)
        except BaseException:
            _release_make_operator_lock(operator_lock)
            raise

        def worker() -> None:
            progress: list[str] = []

            def update(message="") -> None:
                text = str(message).strip()
                if text:
                    progress.append(text[:500])
                    del progress[:-40]
                    status["progress"] = list(progress)
                    _write_make_status(root, status)

            try:
                # Keep imports and all result processing inside the worker's
                # terminalization boundary.  A SystemExit raised anywhere in
                # this path is an operational failure, never permission to
                # strand a durable ``running`` record.
                from deepreason import easy

                paths = easy.make(
                    str(problem["description"]),
                    out=str(output),
                    cycles=cycles,
                    token_budget=token_budget,
                    config=str(config_path),
                    root=str(root),
                    echo=update,
                )
                outputs = [str(Path(path)) for path in paths]
                if outputs:
                    status.update({"state": "completed", "outputs": outputs})
                else:
                    terminal = None
                    try:
                        terminal = _read_website_terminal(root, manifest.sha256)
                    except Exception as error:
                        status.update(
                            {
                                "state": "failed",
                                "failure_kind": "invalid-terminal-summary",
                                "error_type": type(error).__name__,
                                "error": str(error)[:2000],
                                "outputs": [],
                            }
                        )
                    if terminal is not None:
                        status.update(
                            {
                                "state": "failed",
                                "failure_kind": "website-terminal",
                                "outputs": [],
                                "terminal_summary": terminal,
                                "resume_command": terminal["resume_command"],
                                "terminal_summary_ref": str(
                                    (root / "website-terminal.json").resolve()
                                ),
                            }
                        )
                    elif status.get("failure_kind") != "invalid-terminal-summary":
                        status.update(
                            {
                                "state": "failed",
                                "failure_kind": "missing-terminal-summary",
                                "error_type": "MissingWebsiteTerminalSummary",
                                "error": (
                                    "easy.make returned no output and did not persist "
                                    "website-terminal.json"
                                ),
                                "outputs": [],
                            }
                        )
            except (Exception, SystemExit) as error:  # worker result, not protocol failure
                status.update(
                    {
                        "state": "failed",
                        "failure_kind": "worker-exception",
                        "error_type": type(error).__name__,
                        "error": str(error)[:2000],
                        "outputs": [],
                    }
                )
            finally:
                try:
                    _write_make_status(root, status)
                finally:
                    _release_make_operator_lock(operator_lock)

        thread = threading.Thread(
            target=worker, name=f"deepreason-make-{manifest.sha256[:8]}", daemon=True
        )
        _MAKE_THREADS[key] = thread
        try:
            thread.start()
        except BaseException as error:
            # Status was already published as running.  If the worker could
            # not start, replace it synchronously before relinquishing the
            # cross-process lock so readers never observe an orphaned run.
            status.update(
                {
                    "state": "failed",
                    "failure_kind": "worker-start-failure",
                    "error_type": type(error).__name__,
                    "error": str(error)[:2000],
                    "outputs": [],
                }
            )
            try:
                _write_make_status(root, status)
            finally:
                _MAKE_THREADS.pop(key, None)
                _release_make_operator_lock(operator_lock)
            raise
    return {
        "state": "running",
        "root": str(root),
        "manifest_sha256": manifest.sha256,
        "status_operation": "make_status",
        "result_operation": "make_result",
    }


def _parse_run_budget(budget: dict) -> tuple[object, object, int | None, int]:
    from deepreason.runtime.budget import parse_limit

    if not isinstance(budget, dict):
        raise ValueError("run budget must be an object")
    cycles, _ = parse_limit(budget.get("cycles"), optional=False)
    tokens, _ = parse_limit(budget.get("token_budget"))
    token_budget = tokens.value if tokens.mode == "bounded" else None
    scheduler_cycles = cycles.value if cycles.mode == "bounded" else sys.maxsize
    return cycles, tokens, token_budget, int(scheduler_cycles)


def _missing_manifest_credentials(manifest) -> list[str]:
    return sorted(
        {
            route.api_key_env
            for routes in manifest.roles.values()
            for route in routes
            if route.api_key_env and not os.environ.get(route.api_key_env)
        }
    )


def _run_request(root: Path) -> dict:
    target = root / "run-request.json"
    if not target.exists():
        raise ValueError("RUN_REQUEST_MISSING: fixed run-request.json is absent")
    data = json.loads(target.read_text(encoding="utf-8"))
    if (
        not isinstance(data, dict)
        or data.get("schema") != "deepreason-run-request-v1"
        or data.get("workload") != "text"
        or not isinstance(data.get("problem"), dict)
        or not str(data["problem"].get("description") or "").strip()
    ):
        raise ValueError("RUN_REQUEST_INVALID: fixed run request is not valid text input")
    return data


def _start_run(
    arguments: dict,
    *,
    continuation: bool = False,
    progress_callback=None,
) -> dict:
    """Start one run-neutral worker under a durable cross-process lock."""
    from deepreason.ops import require_full_engine
    from deepreason.run_manifest import (
        MANIFEST_NAME,
        bind_run_manifest,
        load_run_manifest,
        preflight_payload,
    )
    from deepreason.runtime.continuation import prepare_continuation
    from deepreason.runtime.progress import ProgressSink, _atomic_json

    def notify_progress(event) -> None:
        if progress_callback is None:
            return
        try:
            progress_callback(event.model_dump(mode="json"))
        except Exception:
            # Presentation transport failure cannot change run execution.
            pass

    root = Path(arguments.get("root") or ".deepreason").resolve()
    cycles, tokens, token_budget, scheduler_cycles = _parse_run_budget(arguments["budget"])
    if continuation:
        manifest = load_run_manifest(root / MANIFEST_NAME)
        request = _run_request(root)
        expected = arguments.get("expected_manifest_digest")
        if expected and expected != manifest.sha256:
            raise ValueError("CONTINUE_MANIFEST_MISMATCH")
    else:
        workload = arguments.get("workload")
        if workload != "text":
            raise ValueError("RUN_WORKLOAD_UNSUPPORTED: start_run currently executes text")
        problem = arguments.get("problem")
        if not isinstance(problem, dict) or not str(problem.get("description") or "").strip():
            raise ValueError("start_run.problem.description must be a non-empty string")
        manifest = load_run_manifest(arguments["run_manifest_ref"])
        request = {
            "schema": "deepreason-run-request-v1",
            "workload": "text",
            "problem": {"description": str(problem["description"]).strip()},
        }
    require_full_engine(manifest, workload="text reasoning")
    if manifest.schema_version not in {2, 3} or manifest.workload_profile != "text":
        raise ValueError(
            "RUN_MANIFEST_WORKLOAD_MISMATCH: start_run requires a v2/v3 text manifest"
        )
    preflight_payload(manifest, {"problem": request["problem"], "commitments": []})
    missing_credentials = _missing_manifest_credentials(manifest)
    if missing_credentials:
        raise ValueError(
            "RUN_CREDENTIAL_MISSING: required environment variable(s) are unset: "
            + ", ".join(missing_credentials)
        )

    key = str(root)
    with _RUN_LOCK:
        existing = _RUN_THREADS.get(key)
        if existing is not None and existing.is_alive():
            raise ValueError("RUN_ALREADY_RUNNING: this root has an active run")
        operator_locks = _acquire_run_operator_lock(root)
        try:
            if continuation:
                continuation_record = prepare_continuation(
                    root,
                    cycles=cycles,
                    tokens=tokens,
                    expected_manifest_digest=manifest.sha256,
                    check_operator_lock=False,
                )
                progress = ProgressSink(
                    root, run_id=manifest.sha256, workload="text"
                )
            else:
                if (root / "progress.jsonl").exists() or (root / "run-result.json").exists():
                    raise ValueError("RUN_ALREADY_STARTED: choose a fresh root or continue_run")
                bind_run_manifest(manifest, root)
                _atomic_json(root / "run-request.json", request)
                progress = ProgressSink(
                    root, run_id=manifest.sha256, workload="text"
                )
                progress.clear_cancellation()
                initial = progress.emit(
                    state="starting",
                    phase="manifest",
                    activity="bound",
                    token_limit=token_budget,
                    determinate=False,
                    message="immutable text manifest bound",
                )
                notify_progress(initial)
                continuation_record = None
        except BaseException:
            _release_operator_locks(operator_locks)
            raise

        def worker() -> None:
            from deepreason.harness import Harness
            from deepreason.ops import run_scheduler
            from deepreason.run_manifest import config_from_run_manifest
            from deepreason.runtime.stop import (
                StopMetrics,
                StopPolicy,
                write_stop_record,
            )
            from deepreason.status_display import display_status_counts
            from deepreason.workloads.text import (
                WorkloadProblem,
                seed_reasoning_workload,
                spec_from_text,
            )

            harness = Harness(root)
            latest_cycle = 0
            try:
                spec = spec_from_text(request["problem"]["description"])
                if request["problem"].get("id"):
                    spec = spec.model_copy(
                        update={
                            "problem": WorkloadProblem(
                                id=request["problem"]["id"],
                                description=request["problem"]["description"],
                            )
                        }
                    )
                if continuation:
                    if spec.problem.id not in harness.state.problems:
                        raise ValueError("CONTINUE_PROBLEM_MISSING: seeded problem is absent")
                    harness.record_measure(
                        inputs=[
                            "run-resume",
                            continuation_record["prior_stop_digest"],
                            manifest.sha256,
                        ]
                    )
                else:
                    seed_reasoning_workload(harness, spec)
                prior = progress.read_since(-1)
                base_cycle = max((event.cycle for event in prior), default=0)
                base_token_spend = sum(
                    event.llm.tokens for event in harness.log.read() if event.llm
                )
                display_token_limit = (
                    None if token_budget is None else base_token_spend + token_budget
                )
                loaded = progress.emit(
                    state="running",
                    phase="workload",
                    activity="loaded",
                    cycle=base_cycle,
                    problem_id=spec.problem.id,
                    token_spend=base_token_spend,
                    token_limit=display_token_limit,
                    determinate=False,
                    display_status_counts=display_status_counts(harness, manifest),
                )
                notify_progress(loaded)

                def on_cycle(scheduler):
                    nonlocal latest_cycle
                    latest_cycle = base_cycle + scheduler._cycles
                    counts = {name: 0 for name in ("accepted", "refuted", "suspended")}
                    for label in scheduler.harness.state.status.values():
                        if label.value in counts:
                            counts[label.value] += 1
                    cycle_report = scheduler.report()
                    token_spend = sum(
                        event.llm.tokens for event in scheduler.harness.log.read() if event.llm
                    )
                    event = progress.emit(
                        state="running",
                        phase="reasoning",
                        activity="cycle complete",
                        cycle=latest_cycle,
                        problem_id=spec.problem.id,
                        frontier_size=len(cycle_report["frontier"]),
                        accepted=counts["accepted"],
                        refuted=counts["refuted"],
                        suspended=counts["suspended"],
                        display_status_counts=display_status_counts(
                            scheduler.harness, manifest
                        ),
                        token_spend=token_spend,
                        token_limit=display_token_limit,
                        determinate=False,
                    )
                    notify_progress(event)
                    return progress.cancellation_requested()

                result, meter, accounting = run_scheduler(
                    harness,
                    config_from_run_manifest(manifest),
                    scheduler_cycles,
                    token_budget,
                    on_cycle=on_cycle,
                    run_manifest=manifest,
                    progress_sink=progress,
                )
                cancelled = progress.cancellation_requested()
                scheduler_reason = result.get("stop_reason")
                stop_reason = (
                    "operator_cancelled"
                    if cancelled
                    else scheduler_reason or "budget_exhausted"
                )
                if scheduler_reason and not cancelled:
                    stop = json.loads((root / "run-stop.json").read_text())
                else:
                    metrics = StopMetrics(cycle=latest_cycle)
                    policy = StopPolicy()
                    harness.record_measure(
                        inputs=[
                            "run-stop",
                            policy.digest,
                            json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
                            stop_reason,
                            str(harness._next_seq),
                        ]
                    )
                    stop = write_stop_record(
                        root,
                        reason=stop_reason,
                        policy=policy,
                        metrics=metrics,
                        event_seq=max(0, harness._next_seq - 1),
                    )
                _atomic_json(
                    root / "checkpoint.json",
                    {
                        "schema": "deepreason-checkpoint-v1",
                        "manifest_digest": manifest.sha256,
                        "stop_digest": stop["digest"],
                        "event_seq": harness._next_seq,
                    },
                )
                payload = {
                    "schema": "deepreason-run-result-v1",
                    "state": "cancelled" if cancelled else "completed",
                    "workload": "text",
                    "problem_id": spec.problem.id,
                    "frontier": result["frontier"],
                    "survivors": result["survivors"],
                    "display": {
                        "status_counts": display_status_counts(harness, manifest),
                    },
                    "accounting": accounting,
                    "stop": stop,
                }
                _atomic_json(root / "run-result.json", payload)
                terminal = progress.emit(
                    state=payload["state"],
                    phase="stop",
                    activity=stop_reason,
                    cycle=latest_cycle,
                    problem_id=spec.problem.id,
                    token_spend=sum(
                        event.llm.tokens for event in harness.log.read() if event.llm
                    ),
                    token_limit=display_token_limit,
                    determinate=False,
                    stop_reason=stop_reason,
                    display_status_counts=display_status_counts(harness, manifest),
                )
                notify_progress(terminal)
            except (Exception, SystemExit) as error:
                policy = StopPolicy()
                metrics = StopMetrics(cycle=latest_cycle)
                try:
                    harness.record_measure(
                        inputs=[
                            "run-stop",
                            policy.digest,
                            json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
                            "operational_failure",
                            type(error).__name__,
                        ]
                    )
                    stop = write_stop_record(
                        root,
                        reason="operational_failure",
                        policy=policy,
                        metrics=metrics,
                        event_seq=max(0, harness._next_seq - 1),
                    )
                    _atomic_json(
                        root / "checkpoint.json",
                        {
                            "schema": "deepreason-checkpoint-v1",
                            "manifest_digest": manifest.sha256,
                            "stop_digest": stop["digest"],
                            "event_seq": harness._next_seq,
                        },
                    )
                    payload = {
                        "schema": "deepreason-run-result-v1",
                        "state": "failed",
                        "workload": "text",
                        "error_type": type(error).__name__,
                        "error": str(error)[:2000],
                        "stop": stop,
                    }
                    _atomic_json(root / "run-result.json", payload)
                    failed = progress.emit(
                        state="failed",
                        phase="stop",
                        activity="operational failure",
                        cycle=latest_cycle,
                        token_limit=token_budget,
                        determinate=False,
                        message=str(error)[:500],
                        stop_reason="operational_failure",
                    )
                    notify_progress(failed)
                except Exception:
                    pass
            finally:
                _release_operator_locks(operator_locks)

        thread = threading.Thread(
            target=worker,
            name=f"deepreason-run-{manifest.sha256[:8]}",
            daemon=True,
        )
        _RUN_THREADS[key] = thread
        try:
            thread.start()
        except BaseException:
            _RUN_THREADS.pop(key, None)
            _release_operator_locks(operator_locks)
            raise
    return {
        "state": "running",
        "root": str(root),
        "manifest_sha256": manifest.sha256,
        "workload": "text",
        "status_operation": "run_status",
        "result_operation": "run_result",
    }


def _read_run_result(root: Path) -> dict:
    target = root / "run-result.json"
    if not target.exists():
        from deepreason.ui.status import read_run_status

        state = read_run_status(root).get("state", "not-started")
        raise ValueError(f"RUN_RESULT_NOT_READY: current state is {state}")
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != "deepreason-run-result-v1":
        raise ValueError("RUN_RESULT_INVALID")
    return data


_REQUIRED_ARGS = {
    "start_run": ("workload", "problem", "run_manifest_ref", "budget"),
    "continue_run": ("budget",),
    "start_make": ("problem", "run_manifest_ref", "budget"),
    "seed_problem": ("problem",),
    "run_cycles": ("cycles",),
    "theory": ("id",),
    "why": ("id",),
    "appellate_rule": ("case_id", "holding", "standard"),
    "submit_evidence": ("problem_id", "source", "content"),
    "report_research_failure": ("problem_id", "source", "reason"),
}


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
    from deepreason.mcp_scratch_bridge import TOOL_NAMES as scratch_bridge_tools

    if name in scratch_bridge_tools:
        from deepreason.mcp_scratch_bridge import call_tool_text

        return call_tool_text(
            name,
            arguments,
            progress_callback=progress_callback,
        )
    from deepreason.ontology import Status
    from deepreason.ops import require_full_engine, resolve_prefix as _resolve
    from deepreason.ops import run_scheduler, seed_problem_payload

    # Actionable argument errors: operator models burn steps on a bare
    # KeyError and conclude the TOOL is broken (observed live: an operator
    # called theory(artifact_id=...) four times and reported the tool as
    # failing). Name what is missing and what was received.
    missing = [k for k in _REQUIRED_ARGS.get(name, ()) if k not in arguments]
    if missing:
        raise ValueError(
            f"{name}: missing required argument(s) {missing}; received "
            f"{sorted(k for k in arguments if k != 'root')}. "
            f"Required: {list(_REQUIRED_ARGS[name])}."
        )

    if name == "start_run":
        return json.dumps(
            _start_run(arguments, progress_callback=progress_callback),
            indent=2,
            sort_keys=True,
        )

    if name == "run_status":
        from deepreason.ui.status import read_run_status

        root = Path(arguments.get("root") or ".deepreason").resolve()
        return json.dumps(
            read_run_status(root, since_seq=int(arguments.get("since_seq", -1))),
            indent=2,
            sort_keys=True,
        )

    if name == "run_result":
        root = Path(arguments.get("root") or ".deepreason").resolve()
        return json.dumps(_read_run_result(root), indent=2, sort_keys=True)

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
        from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
        from deepreason.runtime.progress import ProgressSink
        from deepreason.ui.status import read_run_status

        root = Path(arguments.get("root") or ".deepreason").resolve()
        status = read_run_status(root)
        if status.get("state") not in {"starting", "running"}:
            raise ValueError(
                f"RUN_NOT_ACTIVE: current state is {status.get('state', 'unknown')}"
            )
        manifest = load_run_manifest(root / MANIFEST_NAME)
        sink = ProgressSink(
            root,
            run_id=manifest.sha256,
            workload=manifest.workload_profile or "text",
        )
        sink.request_cancel()
        return json.dumps(
            {
                "state": "cancellation-requested",
                "root": str(root),
                "safe_boundary": "completed-cycle",
            },
            indent=2,
            sort_keys=True,
        )

    if name == "start_make":
        return json.dumps(_start_make(arguments), indent=2, sort_keys=True)

    if name == "make_status":
        root = Path(arguments.get("root") or ".deepreason").resolve()
        return json.dumps(_read_make_status(root), indent=2, sort_keys=True)

    if name == "make_result":
        root = Path(arguments.get("root") or ".deepreason").resolve()
        status = _read_make_status(root)
        if status.get("state") not in {"completed", "failed"}:
            raise ValueError(
                f"MAKE_RESULT_NOT_READY: current state is {status.get('state', 'unknown')}"
            )
        result = {
            key: status[key]
            for key in (
                "state",
                "root",
                "manifest_sha256",
                "problem",
                "outputs",
                "failure_kind",
                "error_type",
                "error",
                "terminal_summary",
                "terminal_summary_ref",
                "resume_command",
            )
            if key in status
        }
        return json.dumps(result, indent=2, sort_keys=True)

    if name == "seed_problem":
        harness = _harness(arguments)
        problem = seed_problem_payload(harness, arguments)
        return f"registered problem {problem.id} with criteria {list(problem.criteria)}"

    if name == "run_cycles":
        from deepreason.views.narrate import narrate
        from deepreason.llm.capabilities import CapabilityCache
        from deepreason.run_manifest import (
            MANIFEST_NAME,
            bind_run_manifest,
            compile_run_manifest,
            config_from_run_manifest,
            load_run_manifest,
            preflight_payload,
        )

        harness = _harness(arguments)
        rubric_commitments = [
            commitment.model_dump(mode="json")
            for commitment in harness.commitments.values()
            if commitment.eval.startswith("rubric:")
        ]
        bound_path = harness.root / MANIFEST_NAME
        if bound_path.exists():
            manifest = load_run_manifest(bound_path)
        else:
            config = _config(arguments)
            policy = "require_cross_family" if rubric_commitments else "forbid"
            manifest = compile_run_manifest(
                config,
                rubric_policy=policy,
                capability_cache=CapabilityCache(harness.root / "capabilities.json"),
            )
        require_full_engine(manifest, workload="full scheduler")
        bind_run_manifest(manifest, harness.root)
        preflight_payload(manifest, {"commitments": rubric_commitments})
        config = config_from_run_manifest(manifest)
        result, meter, accounting = run_scheduler(
            harness, config, arguments["cycles"], arguments.get("token_budget"),
            run_manifest=manifest,
        )
        payload = {
            "survivors": result["survivors"],
            "frontier": result["frontier"],
            "problems": result["problems"],
            "diagnostics": result["diagnostics"][-20:],
            # In-band truth (docs/OPERATOR_DIAGNOSIS.md): silent failure
            # modes must be visible in the tool result itself.
            "accounting": accounting,
            "narration": narrate(harness, window=25),
        }
        if meter is not None:
            payload["token_spend"] = meter.snapshot()
        return json.dumps(payload, indent=2, sort_keys=True)

    if name == "frontier":
        harness = _harness(arguments)
        out = []
        for pid, problem in harness.state.problems.items():
            survivors = [
                a for a, p in harness.state.addr
                if p == pid and harness.state.status.get(a) == Status.ACCEPTED
            ]
            out.append(
                {
                    "problem": pid,
                    "trigger": problem.provenance.trigger.value,
                    "description": problem.description[:200],
                    "survivors": survivors,
                }
            )
        return json.dumps(out, indent=2, sort_keys=True)

    if name == "theory":
        from deepreason.views.theory import theory

        harness = _harness(arguments)
        return theory(_resolve(harness, arguments["id"]), harness.state, harness.blobs, log=harness.log)

    if name == "why":
        from deepreason.views.why import why

        harness = _harness(arguments)
        return why(_resolve(harness, arguments["id"]), harness.state, harness.warrants)

    if name == "narrate":
        from deepreason.views.narrate import narrate

        harness = _harness(arguments)
        return narrate(harness, window=arguments.get("window"))

    if name == "eval_report":
        from deepreason.report import eval_report

        return json.dumps(
            eval_report(_harness(arguments), _config(arguments)), indent=2, sort_keys=True
        )

    if name == "docket":
        from deepreason.informal.appellate import docket

        entries = docket(_harness(arguments), _config(arguments))
        return json.dumps(entries, indent=2, sort_keys=True) if entries else "(docket is empty)"

    if name == "appellate_rule":
        from deepreason.informal.appellate import rule as appellate_rule

        harness = _harness(arguments)
        precedent = appellate_rule(
            harness, arguments["case_id"], arguments["holding"], arguments["standard"]
        )
        return f"precedent registered: {precedent.id}"

    if name == "research_docket":
        from deepreason.ops import research_docket

        entries = research_docket(_harness(arguments), _config(arguments))
        return (json.dumps(entries, indent=2, sort_keys=True)
                if entries else "(no open research problems)")

    if name == "submit_evidence":
        from deepreason.ops import submit_evidence
        from deepreason.research.backends import covered

        harness = _harness(arguments)
        metadata = {
            k: arguments[k]
            for k in ("retrieved_at", "title", "query")
            if arguments.get(k)
        }
        evidence = submit_evidence(
            harness, arguments["problem_id"], arguments["source"],
            arguments["content"], metadata=metadata or None,
        )
        now_covered = covered(harness, arguments["problem_id"])
        return (
            f"candidate evidence registered: {evidence.id} "
            f"(status {harness.state.status.get(evidence.id).value}; "
            f"problem {'covered' if now_covered else 'still open'} — coverage "
            "is derived from the graph and may change under criticism)"
        )

    if name == "report_research_failure":
        from deepreason.ops import report_research_failure

        report_research_failure(
            _harness(arguments), arguments["problem_id"], arguments["source"],
            arguments["reason"], category=arguments.get("category", "fetch-error"),
            detail=arguments.get("detail"),
        )
        return (f"failure recorded for {arguments['problem_id']} — the request "
                "stays open (a failed fetch is never a verdict)")

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
            result = {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    if msg_id is None:
        return None  # unknown notification: ignore per JSON-RPC
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"method not found: {method}"},
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
