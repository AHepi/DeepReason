"""MCP server: install DeepReason as an agent tool in any MCP harness.

Any MCP-capable operator — Claude Code/Desktop, Cursor, a custom agent
loop, any LLM behind an MCP client — can drive the harness through these
tools; any OpenAI-compatible LLM can serve as the engine via the §15 role
table (llm/providers.py). Zero dependencies beyond the package: the
transport is newline-delimited JSON-RPC 2.0 over stdio, per the MCP spec.

The tool surface is the spec §13 verb set, not a bypass: an operator can
seed problems, fund cycles, read views, and enter appellate rulings
(§10.6). It CANNOT set a status, delete anything, or adjudicate — those
paths simply do not exist here (§0 stays load-bearing).
"""

import json
import sys
from pathlib import Path

_PROTOCOL = "2024-11-05"
_ROOT = {"root": {"type": "string", "description": "harness state directory", "default": ".deepreason"}}
_CONFIG = {"config": {"type": "string", "description": "knob file path (default: config/default.yaml)"}}


def _tools() -> list[dict]:
    return [
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
    ]


def _harness(arguments: dict):
    from deepreason.harness import Harness

    return Harness(Path(arguments.get("root") or ".deepreason"))


def _config(arguments: dict):
    from deepreason.config import load

    path = arguments.get("config")
    return load(Path(path) if path else None)


_REQUIRED_ARGS = {
    "seed_problem": ("problem",),
    "run_cycles": ("cycles",),
    "theory": ("id",),
    "why": ("id",),
    "appellate_rule": ("case_id", "holding", "standard"),
}


def call_tool(name: str, arguments: dict) -> str:
    """Execute one tool; returns the text payload (raises on error)."""
    from deepreason.ontology import Status
    from deepreason.ops import resolve_prefix as _resolve
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

    if name == "seed_problem":
        harness = _harness(arguments)
        problem = seed_problem_payload(harness, arguments)
        return f"registered problem {problem.id} with criteria {list(problem.criteria)}"

    if name == "run_cycles":
        from deepreason.views.narrate import narrate

        harness = _harness(arguments)
        config = _config(arguments)
        result, meter, accounting = run_scheduler(
            harness, config, arguments["cycles"], arguments.get("token_budget")
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
