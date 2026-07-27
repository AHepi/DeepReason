"""Small, local, read-only help responses for the public MCP surface."""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "deepreason.mcp-help.v1"

TOOL_NAMES = (
    "get_capabilities",
    "get_help_topic",
    "get_request_requirements",
)

HELP_TOPICS = (
    "overview",
    "examples",
    "creating_a_run",
    "epistemic_outcomes",
    "scratchpad",
    "grounded_bridge",
    "troubleshooting",
)

REQUEST_OPERATIONS = (
    "reasoning_run",
    "continue_run",
    "grounded_bridge",
)

_ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

_TOPIC_CONTENT: dict[str, dict[str, Any]] = {
    "overview": {
        "title": "What DeepReason does",
        "summary": (
            "DeepReason helps examine a question while keeping support, "
            "inference, conjecture, conflict, and uncertainty distinct."
        ),
        "details": (
            "It can preserve an unresolved outcome when the available support is insufficient.",
            "It makes the strength of a conclusion visible instead of filling gaps with certainty.",
            "It keeps exploratory ideas separate from supported conclusions.",
        ),
        "examples": (
            "Compare these reports and identify what each conclusion relies on.",
            "What remains uncertain after considering this material?",
        ),
    },
    "examples": {
        "title": "Example managed-run calls",
        "summary": "Start with readiness, then supply a normal question.",
        "details": (
            "Call get_readiness before start_run.",
            "DeepReason owns input freezing, policy, qualification projection, manifests, and paths.",
        ),
        "examples": (
            "start_run(question='Why does the sky appear blue?')",
        ),
    },
    "creating_a_run": {
        "title": "Starting a managed V6 run",
        "summary": "Supply a question; DeepReason prepares the exact V6 run.",
        "details": (
            "Qualification must already have been completed by the operator.",
            "An optional finite budget may narrow the conservative default.",
            "The returned run_id is opaque and survives MCP process restart.",
        ),
        "examples": (
            "First action: call get_readiness.",
        ),
    },
    "epistemic_outcomes": {
        "title": "Outcomes and uncertainty",
        "summary": "An incomplete or conflicting answer can still be useful.",
        "details": (
            "Observations and facts need support.",
            "Inferences identify the support they draw upon.",
            "Conjectures can be imaginative while remaining clearly conjectural.",
            "Conflict and unknowns remain visible when the material does not settle them.",
        ),
        "examples": (
            "The record supports two incompatible explanations, so the answer remains unresolved.",
        ),
    },
    "scratchpad": {
        "title": "Exploratory scratchpad",
        "summary": (
            "Scratch is a safe exploratory space for bold possibilities, questions, "
            "links, and revisions."
        ),
        "details": (
            "Use it to stretch ideas freely before asking whether they deserve support.",
            "It can retain alternate explanations and unresolved questions for later attention.",
            "Scratch material stays separate from supported conclusions.",
        ),
        "examples": (
            "Record three competing mechanisms and the question each one leaves open.",
        ),
    },
    "grounded_bridge": {
        "title": "Grounded final answer",
        "summary": (
            "A grounded bridge turns a reasoning result into readable prose while "
            "preserving its support and uncertainty."
        ),
        "details": (
            "It keeps observations, inferences, conjectures, and unknowns visibly distinct.",
            "It can retain disagreement or insufficient support instead of forcing one answer.",
            "Choose a focus so the final answer addresses the question that matters most.",
        ),
        "examples": (
            "Compose a concise explanation that preserves the disagreement between the two accounts.",
        ),
    },
    "troubleshooting": {
        "title": "When a run cannot start",
        "summary": "Check readiness and the opaque managed run identity first.",
        "details": (
            "A run cannot start until profile, credential, and qualification readiness are complete.",
            "Every lifecycle, scratch, and bridge operation requires a valid managed run_id.",
            "Provider selection, credentials, routes, policy, manifests, and paths are not MCP fields.",
        ),
        "examples": (
            "Use the one next_action returned by get_readiness.",
        ),
    },
}

_REQUIREMENT_CONTENT: dict[str, dict[str, Any]] = {
    "reasoning_run": {
        "required_information": (
            ("question", "The normal question to prepare and reason over."),
        ),
        "optional_information": (
            ("budget.cycles", "Narrows the finite conservative cycle allowance."),
            ("budget.token_budget", "Narrows the finite conservative token allowance."),
        ),
        "next_operation": "start_run",
    },
    "continue_run": {
        "required_information": (
            ("run_id", "Identifies the managed V6 run without exposing a path."),
            ("budget.cycles", "Sets a finite bounded cycle allowance."),
            ("budget.token_budget", "Sets a finite bounded token allowance."),
        ),
        "optional_information": (),
        "next_operation": "continue_run",
    },
    "grounded_bridge": {
        "required_information": (
            ("run_id", "Identifies the managed V6 run without exposing a path."),
            ("problem", "Names the bounded problem identifier to compose from."),
        ),
        "optional_information": (
            ("target", "Selects thesis, summary, or answer; defaults to answer."),
            ("focus_blocks", "Selects bounded canonical scratch block references."),
            ("focus_clusters", "Selects bounded canonical scratch cluster references."),
            ("budget.token_budget", "Sets a positive bounded bridge token allowance."),
        ),
        "next_operation": "start_bridge",
    },
}

_CAPABILITY_AREAS = (
    ("readiness", "Check whether a managed V6 question may start.", ("get_readiness",)),
    ("reasoning_runs", "Start a normal question under host-owned V6 authority.", ("start_run",)),
    ("continuation", "Request continued work from an earlier reasoning request.", ("continue_run",)),
    ("run_information", "Read reasoning progress and final information.", ("run_status", "run_result")),
    ("cancellation", "Request a safe stop for a reasoning request.", ("cancel_run",)),
    (
        "scratchpad_browsing",
        "Browse bounded exploratory notes.",
        ("scratch_map", "scratch_search", "scratch_open", "scratch_related", "scratch_attention"),
    ),
    (
        "grounded_bridge",
        "Request and inspect grounded final composition.",
        ("start_bridge", "bridge_status", "bridge_claims", "bridge_result"),
    ),
    ("help", "Read concise guidance about this interface.", TOOL_NAMES),
)

_LIMITATIONS = (
    "Help responses describe the interface and do not make changes.",
    "Help responses do not examine saved reasoning work.",
    "Qualification is an explicit operator action and cannot be started through MCP.",
    "MCP accepts no provider, route, policy, manifest, path, credential, or plaintext key fields.",
)


def tool_definitions() -> list[dict[str, Any]]:
    """Return the fixed, closed schemas for the three read-only help tools."""

    return [
        {
            "name": "get_capabilities",
            "description": "Read a bounded summary of user-facing operations.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "annotations": dict(_ANNOTATIONS),
        },
        {
            "name": "get_help_topic",
            "description": "Read one short DeepReason help topic.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "enum": list(HELP_TOPICS)},
                },
                "required": ["topic"],
                "additionalProperties": False,
            },
            "annotations": dict(_ANNOTATIONS),
        },
        {
            "name": "get_request_requirements",
            "description": "Read the information a supported operation needs.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": list(REQUEST_OPERATIONS)},
                },
                "required": ["operation"],
                "additionalProperties": False,
            },
            "annotations": dict(_ANNOTATIONS),
        },
    ]


def _requirement_entries(entries: tuple[tuple[str, str], ...]) -> list[dict[str, str]]:
    return [{"field": field, "reason": reason} for field, reason in entries]


def capabilities_payload(active_tool_names: set[str]) -> dict[str, Any]:
    """Build a deterministic local summary of registered core operations."""

    capabilities = []
    for capability_id, summary, operation_names in _CAPABILITY_AREAS:
        operations = [name for name in operation_names if name in active_tool_names]
        if operations:
            capabilities.append(
                {
                    "id": capability_id,
                    "summary": summary,
                    "operations": operations,
                }
            )
    return {
        "schema_version": SCHEMA_VERSION,
        "capabilities": capabilities,
        "limitations": list(_LIMITATIONS),
    }


def call_tool(
    name: str,
    arguments: dict[str, Any],
    *,
    active_tool_names: set[str],
) -> dict[str, Any]:
    """Return one fixed response after the server has validated its input."""

    if name == "get_capabilities":
        return capabilities_payload(active_tool_names)
    if name == "get_help_topic":
        topic = arguments["topic"]
        content = _TOPIC_CONTENT[topic]
        return {
            "schema_version": SCHEMA_VERSION,
            "topic": topic,
            "title": content["title"],
            "summary": content["summary"],
            "details": list(content["details"]),
            "examples": list(content["examples"]),
        }
    if name == "get_request_requirements":
        operation = arguments["operation"]
        content = _REQUIREMENT_CONTENT[operation]
        return {
            "schema_version": SCHEMA_VERSION,
            "operation": operation,
            "required_information": _requirement_entries(content["required_information"]),
            "optional_information": _requirement_entries(content["optional_information"]),
            "next_operation": content["next_operation"],
        }
    raise ValueError("MCP_TOOL_NOT_EXPOSED: unknown help tool")
