"""Narrow MCP tools for advisory scratch reads and grounded bridge views.

This module is deliberately independent of the JSON-RPC transport.  The MCP
server only needs to append :func:`tool_definitions` to its production list
and delegate names in :data:`TOOL_NAMES` to :func:`call_tool_text`.
"""

from __future__ import annotations

import json
import re
import stat
import threading
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
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
    "start_bridge": "Start the harness-owned two-stage grounded bridge from a precompiled v3 RunManifest.",
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


def _read_service(value: _Input):
    from deepreason.harness import Harness
    from deepreason.scratch.service import ScratchService

    root = _safe_root(value.root, code="SCRATCH_RUN_NOT_FOUND")
    harness = (
        Harness.at(root, value.at_seq)
        if getattr(value, "at_seq", None) is not None
        else Harness(root, read_only=True)
    )
    return ScratchService(harness)


def _scratch_args(value: _HistoricalPage) -> SimpleNamespace:
    root = _safe_root(value.root, code="SCRATCH_RUN_NOT_FOUND")
    return SimpleNamespace(
        root=str(root),
        at_seq=value.at_seq,
        limit=value.limit,
        ordering=getattr(value, "ordering", "created"),
        query=getattr(value, "query", None),
        block=getattr(value, "block", None),
        include_retired=getattr(value, "include_retired", False),
    )


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
    from deepreason.cli.scratch import _map

    payload, _human = _map(_scratch_args(value))
    return _bounded_scratch_payload(payload)


def _scratch_search(value: ScratchSearchInput) -> dict[str, Any]:
    from deepreason.cli.scratch import _search

    payload, _human = _search(_scratch_args(value))
    return _bounded_scratch_payload(payload)


def _scratch_open(value: ScratchOpenInput) -> dict[str, Any]:
    from deepreason.cli.scratch import _block_summary, _canonical, _link_summary

    service = _read_service(value)
    block = service.get_block(value.block)
    revisions = service.revisions(block.id)
    links = service.links_for(block.id, include_retired=value.include_retired)
    clusters = sorted(service.state.clusters_by_block.get(block.id, set()))
    visibility = service.state.visibility.get(block.id)
    payload = {
        "block": _canonical(block),
        "revisions": [
            _block_summary(service, item) for item in revisions[: value.limit]
        ],
        "revision_count": len(revisions),
        "links": [_link_summary(service, item) for item in links[: value.limit]],
        "link_count": len(links),
        "cluster_ids": clusters[: value.limit],
        "cluster_count": len(clusters),
        "visibility": _canonical(visibility) if visibility is not None else None,
        "retrieval_receipt_id": None,
        "committed": False,
    }
    return _bounded_scratch_payload(payload)


def _scratch_related(value: ScratchRelatedInput) -> dict[str, Any]:
    from deepreason.cli.scratch import _related

    payload, _human = _related(_scratch_args(value))
    return _bounded_scratch_payload(payload)


def _scratch_attention(value: ScratchAttentionInput) -> dict[str, Any]:
    from deepreason.cli.bridge import _load_result_manifest
    from deepreason.scratch.attention import AttentionPlanner, AttentionRequestV1

    service = _read_service(value)
    root = _safe_root(value.root, code="SCRATCH_RUN_NOT_FOUND")
    manifest = _load_result_manifest(root)
    policy = manifest.scratch_policy
    if manifest.schema_version != 3 or policy is None or not policy.enabled:
        raise ValueError("SCRATCH_MANIFEST_V3_REQUIRED")
    block_ids = [service.get_block(item).id for item in value.focus_blocks]
    cluster_ids = [service.get_cluster(item).id for item in value.focus_clusters]
    request = AttentionRequestV1(
        focus_blocks=block_ids or None,
        focus_clusters=cluster_ids or None,
        maximum_blocks=value.maximum_blocks,
        maximum_cluster_guides=value.maximum_cluster_guides,
        deterministic_seed=value.deterministic_seed,
    )
    pack = AttentionPlanner(service, policy.attention_policy()).plan(request)
    payload = pack.model_dump(mode="json", by_alias=True, exclude_none=True)
    payload["selection_receipt"]["id"] = pack.selection_receipt.id
    payload.update(
        {
            "committed": False,
            "advisory_warning": (
                "This is a retrieval-only preview. It changes no visibility, "
                "coverage, formal state, identity, truth, support, or attack."
            ),
        }
    )
    return _bounded_scratch_payload(payload)


@dataclass(frozen=True)
class _PreparedBridge:
    root: Path
    manifest: Any
    harness: Any
    problem_id: str
    target: str
    adapter: Any
    attention_pack: Any
    locks: Any
    token_budget: int | None


_BRIDGE_THREADS: dict[str, threading.Thread] = {}
_BRIDGE_THREAD_LOCK = threading.Lock()


def _start_payload(
    state: Literal["running", "busy", "completed", "failed"],
    root: Path,
    *,
    manifest_sha256: str | None = None,
    terminal=None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "deepreason-mcp-bridge-start-v1",
        "state": state,
        "root": str(root),
        "status_operation": "bridge_status",
        "result_operation": "bridge_result",
    }
    if manifest_sha256 is not None:
        payload["manifest_sha256"] = manifest_sha256
    if terminal is not None:
        payload["process_status"] = terminal.process_status
        payload["resolution"] = (
            terminal.resolution.value if terminal.resolution is not None else None
        )
        payload["terminal_event_seq"] = terminal.terminal_event_seq
    return payload


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


def _notify(progress_callback, event: dict[str, Any]) -> None:
    if progress_callback is None:
        return
    try:
        progress_callback(event)
    except (Exception, SystemExit):
        # Presentation/transport callbacks never own workflow state.
        return


def _existing_terminal(root: Path):
    from deepreason.bridge.harness import BRIDGE_RESULT_NAME
    from deepreason.cli.bridge import _load_snapshot

    result = root / BRIDGE_RESULT_NAME
    if not result.exists():
        return None
    return _load_snapshot(root).terminal


def _prepare_bridge(value: StartBridgeInput, locks) -> _PreparedBridge:
    from deepreason.cli.bridge import (
        _attention_pack,
        _bounded_focus,
        _build_bridge_adapter,
        _load_bound_manifest,
        _preflight_focus,
        _resolve_problem,
    )
    from deepreason.harness import Harness
    from deepreason.llm.budget import TokenMeter
    from deepreason.run_manifest import bind_run_manifest

    root = _safe_root(value.root, code="BRIDGE_RUN_NOT_FOUND")
    manifest_ref = (
        _safe_manifest_ref(value.run_manifest_ref)
        if value.run_manifest_ref is not None
        else None
    )
    manifest = _load_bound_manifest(
        root, str(manifest_ref) if manifest_ref is not None else None, bind=False
    )
    preflight = Harness(root, read_only=True)
    problem_id = _resolve_problem(preflight, value.problem)
    blocks = _bounded_focus(value.focus_blocks, "focus-block")
    clusters = _bounded_focus(value.focus_clusters, "focus-cluster")
    resolved_blocks, resolved_clusters = _preflight_focus(
        preflight, manifest, blocks, clusters
    )
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    adapter = _build_bridge_adapter(manifest, harness)
    token_budget = value.budget.token_budget if value.budget is not None else None
    if token_budget is not None:
        adapter.meter = TokenMeter(token_budget)
    attention = _attention_pack(
        harness, manifest, resolved_blocks, resolved_clusters
    )
    return _PreparedBridge(
        root=root,
        manifest=manifest,
        harness=harness,
        problem_id=problem_id,
        target=value.target,
        adapter=adapter,
        attention_pack=attention,
        locks=locks,
        token_budget=token_budget,
    )


def _execute_bridge(prepared: _PreparedBridge):
    from deepreason.cli.bridge import _load_snapshot

    policy = prepared.manifest.bridge_policy
    terminal = prepared.harness.build_bridge(
        prepared.problem_id,
        prepared.target,
        policy.workflow_policy(),
        run_manifest_digest=prepared.manifest.sha256,
        stage_a_adapter=prepared.adapter,
        composition_adapter=prepared.adapter,
        review_adapter=(prepared.adapter if policy.grounding_review else None),
        repair_adapter=(
            prepared.adapter
            if policy.grounding_review and policy.max_grounding_repair_attempts
            else None
        ),
        attention_pack=prepared.attention_pack,
        maximum_sections=policy.output_section_limit,
        formatting_profile=policy.target_profile,
    )
    _load_snapshot(prepared.root, terminal=terminal)
    return terminal


def _start_bridge(
    value: StartBridgeInput, *, progress_callback=None
) -> dict[str, Any]:
    from deepreason.cli.bridge import _load_bound_manifest, _preflight_focus, _resolve_problem
    from deepreason.harness import Harness
    from deepreason.locking import ProcessLockBusy, operator_locks

    root = _safe_root(value.root, code="BRIDGE_RUN_NOT_FOUND")
    manifest_ref = (
        _safe_manifest_ref(value.run_manifest_ref)
        if value.run_manifest_ref is not None
        else None
    )
    # Invalid requests must not create lock files, bind manifests, or publish status.
    manifest = _load_bound_manifest(
        root, str(manifest_ref) if manifest_ref is not None else None, bind=False
    )
    preflight = Harness(root, read_only=True)
    _resolve_problem(preflight, value.problem)
    _preflight_focus(
        preflight, manifest, list(value.focus_blocks), list(value.focus_clusters)
    )
    key = str(root)
    with _BRIDGE_THREAD_LOCK:
        active = _BRIDGE_THREADS.get(key)
        if active is not None and active.is_alive():
            return _start_payload("busy", root, manifest_sha256=manifest.sha256)
        existing = _existing_terminal(root)
        if existing is not None:
            state = "completed" if existing.process_status == "success" else "failed"
            return _start_payload(
                state,
                root,
                manifest_sha256=manifest.sha256,
                terminal=existing,
            )
        try:
            locks = operator_locks(root, owner="bridge", blocking=False)
        except ProcessLockBusy:
            return _start_payload("busy", root, manifest_sha256=manifest.sha256)
        existing = _existing_terminal(root)
        if existing is not None:
            locks.release()
            state = "completed" if existing.process_status == "success" else "failed"
            return _start_payload(
                state,
                root,
                manifest_sha256=manifest.sha256,
                terminal=existing,
            )
        try:
            prepared = _prepare_bridge(value, locks)
            from deepreason.bridge.operations import write_running

            write_running(root, manifest.sha256)
        except BaseException:
            locks.release()
            raise

        launch_gate = threading.Event()

        def worker() -> None:
            launch_gate.wait()
            try:
                _execute_bridge(prepared)
            except (Exception, SystemExit) as error:
                # Pre-terminal operational failures are not epistemic results.
                from deepreason.bridge.operations import write_failure

                write_failure(root, manifest.sha256, type(error).__name__)
            else:
                # Cleanup is presentation/operation housekeeping after a
                # replay-validated terminal. It can never relabel that result.
                from deepreason.bridge.operations import clear

                try:
                    clear(root)
                except (OSError, ValueError):
                    pass
                _notify(
                    progress_callback,
                    {"seq": 1, "activity": "bridge_completed"},
                )
            finally:
                prepared.locks.release()

        thread = threading.Thread(
            target=worker,
            name=f"deepreason-bridge-{manifest.sha256[:8]}",
            daemon=True,
        )
        _BRIDGE_THREADS[key] = thread
        try:
            thread.start()
        except BaseException as error:
            _BRIDGE_THREADS.pop(key, None)
            try:
                from deepreason.bridge.operations import write_failure

                write_failure(root, manifest.sha256, type(error).__name__)
            finally:
                prepared.locks.release()
            return _start_payload(
                "failed", root, manifest_sha256=manifest.sha256
            )
        try:
            _notify(progress_callback, {"seq": 0, "activity": "bridge_started"})
        finally:
            # No presentation callback, including a BaseException, may leave
            # the worker waiting while it owns the process locks.
            launch_gate.set()
    return _start_payload("running", root, manifest_sha256=manifest.sha256)


def _bridge_status(value: BridgeStatusInput) -> dict[str, Any]:
    from deepreason.cli.bridge import _status_payload

    root = _safe_root(value.root, code="BRIDGE_RUN_NOT_FOUND")
    try:
        return _status_payload(root)
    except ValueError as error:
        if str(error).startswith("BRIDGE_RECORD_UNAVAILABLE"):
            return {
                "schema": "deepreason-mcp-bridge-status-v1",
                "state": "not_started",
            }
        raise


def _bridge_result(value: BridgeResultInput) -> dict[str, Any]:
    from deepreason.cli.bridge import _load_snapshot, _result_payload

    root = _safe_root(value.root, code="BRIDGE_RUN_NOT_FOUND")
    from deepreason.bridge.operations import read_failure

    try:
        snapshot = _load_snapshot(root)
    except ValueError:
        operation = read_failure(root)
        if operation is None:
            raise
        return operation.model_dump(mode="json", by_alias=True, exclude_none=True)
    return _result_payload(snapshot, limit=value.limit, offset=value.offset)


def _bridge_claims(value: BridgeClaimsInput) -> dict[str, Any]:
    from deepreason.cli.bridge import _claims_payload, _load_snapshot

    root = _safe_root(value.root, code="BRIDGE_RUN_NOT_FOUND")
    return _claims_payload(
        _load_snapshot(root),
        limit=value.limit,
        offset=value.offset,
    )


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
