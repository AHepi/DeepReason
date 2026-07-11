"""Narrow MCP facade for harness-owned website execution.

The production surface exposes only ``start_make``, ``make_status``, and
``make_result``.  Endpoint models never receive MCP tools and cannot select
routes, edit configuration, browse repositories, write events, or alter
guards/status.  The historical research/operator verbs remain quarantined
behind ``DEEPREASON_ENABLE_LEGACY_MCP=1`` for explicit migration work.
"""

import fcntl
import json
import os
import sys
import threading
from pathlib import Path

_PROTOCOL = "2024-11-05"
_ROOT = {"root": {"type": "string", "description": "harness state directory", "default": ".deepreason"}}
_CONFIG = {
    "config": {
        "type": "string",
        "description": "partial YAML profile path (default: built-in typed defaults)",
    }
}
_MAKE_STATUS_NAME = "make-status.json"
_MAKE_OPERATOR_LOCK_NAME = ".make-operator.lock"
_MAKE_THREADS: dict[str, threading.Thread] = {}
_MAKE_LOCK = threading.Lock()


def _legacy_tools() -> list[dict]:
    return [
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
                            "description": {"type": "string", "minLength": 1},
                        },
                        "required": ["description"],
                        "additionalProperties": False,
                    },
                    "run_manifest_ref": {"type": "string", "minLength": 1},
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


_NARROW_TOOL_NAMES = frozenset({"start_make", "make_status", "make_result"})


def _tools() -> list[dict]:
    tools = _legacy_tools()
    if os.environ.get("DEEPREASON_ENABLE_LEGACY_MCP") == "1":
        return tools
    return [tool for tool in tools if tool["name"] in _NARROW_TOOL_NAMES]


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


def _acquire_make_operator_lock(root: Path):
    """Claim one run root across MCP processes for the worker lifetime."""
    root.mkdir(parents=True, exist_ok=True)
    stream = open(root / _MAKE_OPERATOR_LOCK_NAME, "a+b")
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        stream.close()
        raise ValueError(
            "MAKE_ALREADY_RUNNING: another process owns this run root"
        ) from error
    return stream


def _release_make_operator_lock(stream) -> None:
    try:
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    finally:
        stream.close()


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


_REQUIRED_ARGS = {
    "start_make": ("problem", "run_manifest_ref", "budget"),
    "seed_problem": ("problem",),
    "run_cycles": ("cycles",),
    "theory": ("id",),
    "why": ("id",),
    "appellate_rule": ("case_id", "holding", "standard"),
    "submit_evidence": ("problem_id", "source", "content"),
    "report_research_failure": ("problem_id", "source", "reason"),
}


def call_tool(name: str, arguments: dict) -> str:
    """Execute one tool; returns the text payload (raises on error)."""
    exposed = {tool["name"] for tool in _tools()}
    if name not in exposed:
        raise ValueError(
            f"MCP_TOOL_NOT_EXPOSED: {name!r} is outside the active operator surface"
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


def handle(message: dict) -> dict | None:
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
        params = message.get("params") or {}
        try:
            text = call_tool(params.get("name", ""), params.get("arguments") or {})
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
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            print(
                json.dumps({"jsonrpc": "2.0", "id": None,
                            "error": {"code": -32700, "message": f"parse error: {e}"}}),
                flush=True,
            )
            continue
        response = handle(message)
        if response is not None:
            print(json.dumps(response), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
