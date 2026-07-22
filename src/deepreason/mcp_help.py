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
        "title": "Example prepared-run calls",
        "summary": (
            "The current MCP surface operates an already-prepared V6 root; "
            "it does not prepare a normal question yet."
        ),
        "details": (
            "Use start_run only after an operator has frozen RunInputManifestV2 and its dossier.",
            "The root must already contain the exact bound and production-qualified V6 manifest.",
        ),
        "examples": (
            "start_run(root, workload='text', problem.description, run_manifest_ref, budget)",
        ),
    },
    "creating_a_run": {
        "title": "Starting an operator-prepared V6 run",
        "summary": (
            "DeepReason does not yet expose run preparation over MCP. Supply an "
            "existing prepared, bound, and production-qualified V6 root."
        ),
        "details": (
            "The root must contain RunManifest schema 6, RunInputManifestV2, and its exact dossier.",
            "problem.description must exactly match the frozen V6 input.",
            "run_manifest_ref must identify the same immutable manifest bound to the root.",
            "Supply explicit cycle and token budgets; no historical fallback is compiled.",
        ),
        "examples": (
            "First action: ask the operator for the path to a prepared V6 root and its bound manifest.",
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
        "summary": "Check the prepared V6 root and exact frozen bindings first.",
        "details": (
            "A missing RunManifest is distinct from an unsupported historical version.",
            "Every lifecycle, scratch, and bridge operation requires a valid V6 root.",
            "Provider selection, credentials, route selection, policy construction, and preparation are not MCP fields.",
        ),
        "examples": (
            "If only a normal question is available, report that managed V6 preparation is not implemented yet.",
        ),
    },
}

_REQUIREMENT_CONTENT: dict[str, dict[str, Any]] = {
    "reasoning_run": {
        "required_information": (
            ("workload", "Must be the fixed value text."),
            ("problem.description", "Exactly matches the question frozen in RunInputManifestV2."),
            ("run_manifest_ref", "Identifies the exact schema-6 manifest already bound to the root."),
            ("budget.cycles", "Sets a positive integer cycle allowance or unlimited."),
            ("budget.token_budget", "Sets a non-negative integer token allowance or unlimited."),
        ),
        "optional_information": (
            ("root", "Selects an existing prepared, bound, and qualified V6 run root; defaults to .deepreason."),
        ),
        "next_operation": "start_run",
    },
    "continue_run": {
        "required_information": (
            ("budget.cycles", "Sets a positive integer cycle allowance or unlimited."),
            ("budget.token_budget", "Sets a non-negative integer token allowance or unlimited."),
        ),
        "optional_information": (
            ("root", "Selects an existing prepared and bound V6 run root; defaults to .deepreason."),
            ("expected_manifest_digest", "Pins the already-bound manifest digest."),
        ),
        "next_operation": "continue_run",
    },
    "grounded_bridge": {
        "required_information": (
            ("problem", "Names the bounded problem identifier to compose from."),
        ),
        "optional_information": (
            ("root", "Selects an existing prepared, bound, and qualified V6 run root; defaults to .deepreason."),
            ("target", "Selects thesis, summary, or answer; defaults to answer."),
            ("run_manifest_ref", "Pins the same schema-6 manifest already bound to the root."),
            ("focus_blocks", "Selects bounded canonical scratch block references."),
            ("focus_clusters", "Selects bounded canonical scratch cluster references."),
            ("budget.token_budget", "Sets a positive bounded bridge token allowance."),
        ),
        "next_operation": "start_bridge",
    },
}

_CAPABILITY_AREAS = (
    ("reasoning_runs", "Start work only in an operator-prepared V6 root.", ("start_run",)),
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
    "Question-only V6 preparation and readiness are not implemented on MCP yet.",
    "MCP accepts no provider, route, policy, credential, or plaintext key fields.",
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
