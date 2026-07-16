"""Narrow MCP tools for advisory scratch reads and grounded bridge views.

This module is deliberately independent of the JSON-RPC transport.  The MCP
server only needs to append :func:`tool_definitions` to its production list
and delegate names in :data:`TOOL_NAMES` to :func:`call_tool_text`.
"""

from __future__ import annotations

import json
import re
import stat
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
)

from deepreason.application.bridge import (
    GROUNDED_BRIDGE_SERVICE,
    GROUNDED_BRIDGE_WORKERS,
    GroundedBridgeBuildIntentV1,
    GroundedBridgeClaimsIntentV1,
    GroundedBridgeResultIntentV1,
    GroundedBridgeStatusIntentV1,
)
from deepreason.application.scratch import (
    SCRATCH_QUERY_SERVICE,
    ScratchAttentionPreviewQueryV1,
    ScratchMapQueryV1,
    ScratchOpenPreviewQueryV1,
    ScratchRelatedQueryV1,
    ScratchSearchQueryV1,
)


_MAX_ROOT_CHARS = 4_096
_MAX_QUERY_CHARS = 4_096
_MAX_REFERENCE_CHARS = 512
_MAX_RESULTS = 25
_MAX_OFFSET = 1_000_000
_MAX_FOCUS = 64
_MAX_ATTENTION_BLOCKS = 32
_MAX_ATTENTION_GUIDES = 8
_MAX_TEXT_RESULT_CHARS = 16_384
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024
_HEX_REFERENCE = re.compile(r"^(?:sha256:)?[0-9a-f]{1,64}$")
_REFERENCE_PATTERN = r"^(?:sha256:)?[0-9a-fA-F]{1,64}$"
HashReference = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=_MAX_REFERENCE_CHARS,
        pattern=_REFERENCE_PATTERN,
    ),
]


class _Input(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    root: str = Field(default=".deepreason", min_length=1, max_length=_MAX_ROOT_CHARS)

    @field_validator("root")
    @classmethod
    def _safe_root(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("root contains a NUL byte")
        return value


class _HistoricalPage(_Input):
    at_seq: int | None = Field(default=None, ge=0)
    limit: int = Field(default=20, ge=1, le=_MAX_RESULTS)


class ScratchMapInput(_HistoricalPage):
    ordering: Literal["created", "id", "size"] = "created"


class ScratchSearchInput(_HistoricalPage):
    query: str = Field(min_length=1, max_length=_MAX_QUERY_CHARS)


class _BlockInput(_HistoricalPage):
    block: HashReference
    include_retired: bool = False

    @field_validator("block")
    @classmethod
    def _block_reference(cls, value: str) -> str:
        if _HEX_REFERENCE.fullmatch(value.casefold()) is None:
            raise ValueError("block must be a canonical ID or hexadecimal prefix")
        return value.casefold()


class ScratchOpenInput(_BlockInput):
    pass


class ScratchRelatedInput(_BlockInput):
    pass


class ScratchAttentionInput(_Input):
    at_seq: int | None = Field(default=None, ge=0)
    focus_blocks: list[HashReference] = Field(
        default_factory=list,
        max_length=_MAX_FOCUS,
        json_schema_extra={"uniqueItems": True},
    )
    focus_clusters: list[HashReference] = Field(
        default_factory=list,
        max_length=_MAX_FOCUS,
        json_schema_extra={"uniqueItems": True},
    )
    maximum_blocks: int = Field(default=20, ge=1, le=_MAX_ATTENTION_BLOCKS)
    maximum_cluster_guides: int = Field(
        default=4, ge=0, le=_MAX_ATTENTION_GUIDES
    )
    deterministic_seed: int = Field(default=0, ge=0, le=2**63 - 1)

    @field_validator("focus_blocks", "focus_clusters")
    @classmethod
    def _focus_references(cls, values: list[str]) -> list[str]:
        normalized = [value.casefold() for value in values]
        if len(normalized) != len(set(normalized)):
            raise ValueError("focus references must be unique")
        if any(_HEX_REFERENCE.fullmatch(value) is None for value in normalized):
            raise ValueError("focus values must be canonical IDs or hexadecimal prefixes")
        return normalized


class BridgeStartBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    token_budget: int = Field(ge=1, le=10_000_000)


class StartBridgeInput(_Input):
    problem: str = Field(min_length=1, max_length=_MAX_REFERENCE_CHARS)
    target: Literal["thesis", "summary", "answer"] = "answer"
    run_manifest_ref: str | None = Field(
        default=None, min_length=1, max_length=_MAX_ROOT_CHARS
    )
    focus_blocks: list[HashReference] = Field(
        default_factory=list,
        max_length=_MAX_FOCUS,
        json_schema_extra={"uniqueItems": True},
    )
    focus_clusters: list[HashReference] = Field(
        default_factory=list,
        max_length=_MAX_FOCUS,
        json_schema_extra={"uniqueItems": True},
    )
    budget: BridgeStartBudget | None = None

    @field_validator("problem")
    @classmethod
    def _problem_reference(cls, value: str) -> str:
        if value != value.strip() or "\x00" in value or "/" in value or "\\" in value:
            raise ValueError("problem must be a bounded identifier, not a path")
        if value in {".", ".."}:
            raise ValueError("problem must not traverse paths")
        return value

    @field_validator("run_manifest_ref")
    @classmethod
    def _manifest_reference(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("run_manifest_ref contains a NUL byte")
        return value

    @field_validator("focus_blocks", "focus_clusters")
    @classmethod
    def _bridge_focus(cls, values: list[str]) -> list[str]:
        return ScratchAttentionInput._focus_references(values)


class BridgeStatusInput(_Input):
    pass


class _BridgePage(_Input):
    limit: int = Field(default=20, ge=1, le=_MAX_RESULTS)
    offset: int = Field(default=0, ge=0, le=_MAX_OFFSET)


class BridgeResultInput(_BridgePage):
    pass


class BridgeClaimsInput(_BridgePage):
    pass


_TOOL_MODELS: dict[str, type[_Input]] = {
    "scratch_map": ScratchMapInput,
    "scratch_search": ScratchSearchInput,
    "scratch_open": ScratchOpenInput,
    "scratch_related": ScratchRelatedInput,
    "scratch_attention": ScratchAttentionInput,
    "start_bridge": StartBridgeInput,
    "bridge_status": BridgeStatusInput,
    "bridge_result": BridgeResultInput,
    "bridge_claims": BridgeClaimsInput,
}
TOOL_NAMES = frozenset(_TOOL_MODELS)


_DESCRIPTIONS = {
    "scratch_map": "Read a bounded cluster map from immutable advisory scratch history.",
    "scratch_search": "Run bounded deterministic literal search over advisory blocks.",
    "scratch_open": "Open one immutable scratch block and bounded relationships without recording attention.",
    "scratch_related": "Read bounded explicit, cluster, and retrieval-only similarity neighbours.",
    "scratch_attention": "Preview a deterministic bounded attention plan without committing a receipt or visibility.",
    "start_bridge": "Start the harness-owned two-stage grounded bridge from a precompiled v3/v4 RunManifest.",
    "bridge_status": "Read fixed bridge operational status and replay-validate terminal state.",
    "bridge_result": "Read a bounded replay-validated grounded bridge result.",
    "bridge_claims": "Read a bounded replay-validated claim ledger.",
}


def tool_definitions() -> list[dict[str, Any]]:
    """Return the exact nine closed, bounded production tool contracts."""

    return [
        {
            "name": name,
            "description": _DESCRIPTIONS[name],
            "inputSchema": model.model_json_schema(),
        }
        for name, model in _TOOL_MODELS.items()
    ]


def _bounded_scratch_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Clip model-authored text with explicit pointers; IDs remain untouched."""

    notices: list[dict[str, Any]] = []

    def visit(value: Any, pointer: str) -> Any:
        if isinstance(value, str) and len(value) > _MAX_TEXT_RESULT_CHARS:
            notices.append(
                {
                    "pointer": pointer or "/",
                    "original_characters": len(value),
                    "returned_characters": _MAX_TEXT_RESULT_CHARS,
                }
            )
            return value[:_MAX_TEXT_RESULT_CHARS]
        if isinstance(value, list):
            if len(value) > _MAX_RESULTS:
                notices.append(
                    {
                        "pointer": pointer or "/",
                        "original_items": len(value),
                        "returned_items": _MAX_RESULTS,
                    }
                )
            return [
                visit(item, f"{pointer}/{index}")
                for index, item in enumerate(value[:_MAX_RESULTS])
            ]
        if isinstance(value, dict):
            return {
                key: visit(item, f"{pointer}/{key}")
                for key, item in value.items()
            }
        return value

    bounded = visit(payload, "")
    bounded["truncation"] = {
        "truncated": bool(notices),
        "fields": notices[:_MAX_RESULTS],
    }
    return bounded


def _scratch_map(value: ScratchMapInput) -> dict[str, Any]:
    root = _safe_root(value.root, code="SCRATCH_RUN_NOT_FOUND")
    result = SCRATCH_QUERY_SERVICE.execute(
        ScratchMapQueryV1(
            root=str(root),
            at_seq=value.at_seq,
            limit=value.limit,
            ordering=value.ordering,
        )
    )
    return _bounded_scratch_payload(result.presentation_payload())


def _scratch_search(value: ScratchSearchInput) -> dict[str, Any]:
    root = _safe_root(value.root, code="SCRATCH_RUN_NOT_FOUND")
    result = SCRATCH_QUERY_SERVICE.execute(
        ScratchSearchQueryV1(
            root=str(root),
            at_seq=value.at_seq,
            limit=value.limit,
            query=value.query,
        )
    )
    return _bounded_scratch_payload(result.presentation_payload())


def _scratch_open(value: ScratchOpenInput) -> dict[str, Any]:
    root = _safe_root(value.root, code="SCRATCH_RUN_NOT_FOUND")
    result = SCRATCH_QUERY_SERVICE.execute(
        ScratchOpenPreviewQueryV1(
            root=str(root),
            at_seq=value.at_seq,
            limit=value.limit,
            block=value.block,
            include_retired=value.include_retired,
        )
    )
    return _bounded_scratch_payload(result.presentation_payload(include_committed=True))


def _scratch_related(value: ScratchRelatedInput) -> dict[str, Any]:
    root = _safe_root(value.root, code="SCRATCH_RUN_NOT_FOUND")
    result = SCRATCH_QUERY_SERVICE.execute(
        ScratchRelatedQueryV1(
            root=str(root),
            at_seq=value.at_seq,
            limit=value.limit,
            block=value.block,
            include_retired=value.include_retired,
        )
    )
    return _bounded_scratch_payload(result.presentation_payload())


def _scratch_attention(value: ScratchAttentionInput) -> dict[str, Any]:
    root = _safe_root(value.root, code="SCRATCH_RUN_NOT_FOUND")
    result = SCRATCH_QUERY_SERVICE.execute(
        ScratchAttentionPreviewQueryV1(
            root=str(root),
            at_seq=value.at_seq,
            focus_blocks=tuple(value.focus_blocks),
            focus_clusters=tuple(value.focus_clusters),
            maximum_blocks=value.maximum_blocks,
            maximum_cluster_guides=value.maximum_cluster_guides,
            deterministic_seed=value.deterministic_seed,
        )
    )
    return _bounded_scratch_payload(result.presentation_payload())


_BRIDGE_THREADS = GROUNDED_BRIDGE_WORKERS.threads
_BRIDGE_THREAD_LOCK = GROUNDED_BRIDGE_WORKERS.lock


def _safe_manifest_ref(value: str) -> Path:
    path = Path(value)
    try:
        observed = path.lstat()
    except OSError as error:
        raise ValueError("BRIDGE_MANIFEST_UNAVAILABLE") from error
    if (
        not stat.S_ISREG(observed.st_mode)
        or path.is_symlink()
        or not 2 <= observed.st_size <= _MAX_MANIFEST_BYTES
    ):
        raise ValueError("BRIDGE_MANIFEST_UNAVAILABLE")
    return path


def _safe_root(value: str, *, code: str) -> Path:
    raw = Path(value)
    if raw.is_symlink() or not raw.is_dir():
        raise ValueError(code)
    return raw.resolve()


def _bridge_intent(value: StartBridgeInput) -> GroundedBridgeBuildIntentV1:
    root = _safe_root(value.root, code="BRIDGE_RUN_NOT_FOUND")
    manifest_ref = (
        _safe_manifest_ref(value.run_manifest_ref)
        if value.run_manifest_ref is not None
        else None
    )
    return GroundedBridgeBuildIntentV1(
        root=str(root),
        problem=value.problem,
        target=value.target,
        run_manifest_ref=(str(manifest_ref) if manifest_ref is not None else None),
        focus_blocks=tuple(value.focus_blocks),
        focus_clusters=tuple(value.focus_clusters),
        token_budget=(
            value.budget.token_budget if value.budget is not None else None
        ),
    )


def _start_bridge(
    value: StartBridgeInput, *, progress_callback=None
) -> dict[str, Any]:
    result = GROUNDED_BRIDGE_SERVICE.start(
        _bridge_intent(value),
        progress_callback=progress_callback,
    )
    return result.presentation_payload()


def _bridge_status(value: BridgeStatusInput) -> dict[str, Any]:
    root = _safe_root(value.root, code="BRIDGE_RUN_NOT_FOUND")
    return GROUNDED_BRIDGE_SERVICE.status(
        GroundedBridgeStatusIntentV1(root=str(root))
    ).presentation_payload()


def _bridge_result(value: BridgeResultInput) -> dict[str, Any]:
    root = _safe_root(value.root, code="BRIDGE_RUN_NOT_FOUND")
    return GROUNDED_BRIDGE_SERVICE.result(
        GroundedBridgeResultIntentV1(
            root=str(root),
            limit=value.limit,
            offset=value.offset,
        )
    ).presentation_payload()


def _bridge_claims(value: BridgeClaimsInput) -> dict[str, Any]:
    root = _safe_root(value.root, code="BRIDGE_RUN_NOT_FOUND")
    return GROUNDED_BRIDGE_SERVICE.claims(
        GroundedBridgeClaimsIntentV1(
            root=str(root),
            limit=value.limit,
            offset=value.offset,
        )
    ).presentation_payload()


_HANDLERS = {
    "scratch_map": _scratch_map,
    "scratch_search": _scratch_search,
    "scratch_open": _scratch_open,
    "scratch_related": _scratch_related,
    "scratch_attention": _scratch_attention,
    "start_bridge": _start_bridge,
    "bridge_status": _bridge_status,
    "bridge_result": _bridge_result,
    "bridge_claims": _bridge_claims,
}


def call_tool(name: str, arguments: dict[str, Any], *, progress_callback=None) -> dict[str, Any]:
    """Validate and execute one of the nine narrow tools."""

    model = _TOOL_MODELS.get(name)
    if model is None:
        raise ValueError("MCP_TOOL_NOT_EXPOSED")
    if not isinstance(arguments, dict):
        raise ValueError("MCP_INPUT_INVALID: arguments must be an object")
    try:
        value = model.model_validate(arguments)
    except ValidationError as error:
        raise ValueError(
            f"MCP_INPUT_INVALID: {name} arguments violate the closed bounded schema"
        ) from error
    if name == "start_bridge":
        return _start_bridge(value, progress_callback=progress_callback)
    return _HANDLERS[name](value)


def call_tool_text(
    name: str, arguments: dict[str, Any], *, progress_callback=None
) -> str:
    return json.dumps(
        call_tool(name, arguments, progress_callback=progress_callback),
        indent=2,
        sort_keys=True,
    )


__all__ = ["TOOL_NAMES", "call_tool", "call_tool_text", "tool_definitions"]
