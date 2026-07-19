"""Typed application boundary for the grounded two-stage bridge.

Clients choose only an immutable manifest, an existing problem, optional
advisory focus, and presentation bounds.  This service owns manifest binding,
route construction, locking, bridge execution, replay validation, and worker
lifecycle.  It deliberately exposes no generic prompt execution, route
selector, raw event append, or status mutation surface.
"""

from __future__ import annotations

import json
import re
import stat
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)

from deepreason.bridge.evidence_pack import EvidencePackV1
from deepreason.bridge.events import BridgeAction
from deepreason.bridge.harness import (
    BRIDGE_RESULT_NAME,
    BRIDGE_STATUS_NAME,
    BridgeTerminalResultV1,
)
from deepreason.bridge.models import (
    BridgeFailureV1,
    BridgeOutputV1,
    BridgeResolution,
    BridgeValidationReportV1,
    ClaimLedgerV1,
    GroundingReviewV1,
)
from deepreason.locking import ProcessLockBusy, operator_locks


MAX_CONTROL_FILE_BYTES = 4 * 1024 * 1024
MAX_FOCUS_REFS = 64
MAX_REFERENCE_CHARS = 512
DEFAULT_PAGE_LIMIT = 25
MAX_PAGE_LIMIT = 100
MAX_PAGE_OFFSET = 1_000_000
MAX_JSON_TEXT_CHARS = 16_384
MAX_JSON_ARRAY_ITEMS = 100
_SHA256_REFERENCE = re.compile(r"^(?:sha256:)?[0-9a-f]{1,64}$")


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        populate_by_name=True,
        hide_input_in_errors=True,
    )


class GroundedBridgeBuildIntentV1(_StrictModel):
    """Closed operator intent for one canonical or derived bridge build."""

    schema_: Literal["application.grounded-bridge.build.v1"] = Field(
        "application.grounded-bridge.build.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)
    problem: str
    target: Literal["thesis", "summary", "answer"] = "answer"
    run_manifest_ref: str | None = Field(default=None, min_length=1, max_length=4_096)
    focus_blocks: tuple[str, ...] = ()
    focus_clusters: tuple[str, ...] = ()
    derived_output: str | None = Field(default=None, min_length=1, max_length=4_096)
    at_seq: StrictInt | None = Field(default=None, ge=0)
    diagnostic_after_failure: bool = False
    token_budget: StrictInt | None = Field(default=None, ge=1, le=10_000_000)

    @field_validator("root", "run_manifest_ref", "derived_output")
    @classmethod
    def _safe_path_text(cls, value: str | None) -> str | None:
        if value is not None and "\x00" in value:
            raise ValueError("path text cannot contain NUL")
        return value

    @field_validator("problem")
    @classmethod
    def _safe_problem(cls, value: str) -> str:
        if value != value.strip() or "\x00" in value:
            raise ValueError("BRIDGE_INPUT_INVALID: problem must be non-blank text")
        if len(value) > MAX_REFERENCE_CHARS:
            raise ValueError("BRIDGE_INPUT_TOO_LARGE: problem")
        return value

    @field_validator("focus_blocks", "focus_clusters")
    @classmethod
    def _safe_focus(cls, values: tuple[str, ...], info) -> tuple[str, ...]:
        label = "focus-block" if info.field_name == "focus_blocks" else "focus-cluster"
        if len(values) > MAX_FOCUS_REFS:
            raise ValueError(f"BRIDGE_INPUT_TOO_LARGE: at most {MAX_FOCUS_REFS} {label} values")
        normalized = tuple(value.casefold() for value in values)
        if len(normalized) != len(set(normalized)):
            raise ValueError(f"BRIDGE_INPUT_INVALID: duplicate {label}")
        if any(
            len(value) > MAX_REFERENCE_CHARS or _SHA256_REFERENCE.fullmatch(value) is None
            for value in normalized
        ):
            raise ValueError(f"BRIDGE_INPUT_INVALID: {label} must be an ID or hex prefix")
        return values

    @model_validator(mode="after")
    def _derived_shape(self):
        derived = self.derived_output is not None or self.at_seq is not None
        if derived and (self.derived_output is None or self.at_seq is None):
            raise ValueError(
                "BRIDGE_DERIVED_FLAGS_REQUIRED: --derived-output and --at-seq "
                "must be supplied together"
            )
        if derived and self.run_manifest_ref is None:
            raise ValueError("BRIDGE_DERIVED_MANIFEST_REQUIRED: pass a separate v3 --run-manifest")
        if derived and (self.focus_blocks or self.focus_clusters):
            raise ValueError(
                "BRIDGE_DERIVED_SCRATCH_CONTEXT_UNAVAILABLE: derived focus requires "
                "canonical destination receipts"
            )
        if self.diagnostic_after_failure and self.derived_output is None:
            raise ValueError(
                "BRIDGE_DIAGNOSTIC_DERIVED_REQUIRED: --diagnostic-after-failure "
                "requires --derived-output"
            )
        return self


class GroundedBridgeStatusIntentV1(_StrictModel):
    schema_: Literal["application.grounded-bridge.status.v1"] = Field(
        "application.grounded-bridge.status.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)

    @field_validator("root")
    @classmethod
    def _safe_root_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("root contains a NUL byte")
        return value


class _GroundedBridgePageIntentV1(_StrictModel):
    root: str = Field(min_length=1, max_length=4_096)
    limit: StrictInt = Field(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT)
    offset: StrictInt = Field(default=0, ge=0, le=MAX_PAGE_OFFSET)

    @field_validator("root")
    @classmethod
    def _safe_root_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("root contains a NUL byte")
        return value


class GroundedBridgeResultIntentV1(_GroundedBridgePageIntentV1):
    schema_: Literal["application.grounded-bridge.result.v1"] = Field(
        "application.grounded-bridge.result.v1", alias="schema"
    )


class GroundedBridgeClaimsIntentV1(_GroundedBridgePageIntentV1):
    schema_: Literal["application.grounded-bridge.claims.v1"] = Field(
        "application.grounded-bridge.claims.v1", alias="schema"
    )


class GroundedBridgeInspectIntentV1(_GroundedBridgePageIntentV1):
    schema_: Literal["application.grounded-bridge.inspect.v1"] = Field(
        "application.grounded-bridge.inspect.v1", alias="schema"
    )


class GroundedBridgeValidateIntentV1(_GroundedBridgePageIntentV1):
    schema_: Literal["application.grounded-bridge.validate.v1"] = Field(
        "application.grounded-bridge.validate.v1", alias="schema"
    )


class BridgeCLIStatusV1(BaseModel):
    """Strict fixed-name terminal status record written by the harness."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_: str = Field(alias="schema", pattern=r"^deepreason-bridge-status-v1$")
    state: str = Field(pattern=r"^(?:starting|running|completed|failed)$")
    process_status: str | None = Field(default=None, pattern=r"^(?:success|failure)$")
    formal_seq: int | None = Field(default=None, ge=0)
    terminal_event_seq: int | None = Field(default=None, ge=0)
    resolution: BridgeResolution | None = None
    error_code: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{0,127}$")

    @model_validator(mode="after")
    def _terminal_shape(self):
        terminal = self.state in {"completed", "failed"}
        if terminal and (
            self.process_status is None
            or self.formal_seq is None
            or self.terminal_event_seq is None
        ):
            raise ValueError("terminal bridge status is missing terminal fields")
        if self.process_status == "success" and self.resolution is None:
            raise ValueError("successful bridge status requires a resolution")
        if self.process_status == "failure" and self.error_code is None:
            raise ValueError("failed bridge status requires an error_code")
        if self.state == "completed" and self.process_status != "success":
            raise ValueError("completed bridge status must report process success")
        if self.state == "failed" and self.process_status != "failure":
            raise ValueError("failed bridge status must report process failure")
        if not terminal and any(
            value is not None
            for value in (
                self.process_status,
                self.formal_seq,
                self.terminal_event_seq,
                self.resolution,
                self.error_code,
            )
        ):
            raise ValueError("non-terminal bridge status cannot carry terminal fields")
        return self


@dataclass(frozen=True)
class GroundedBridgeSnapshotV1:
    """Replay-validated immutable objects behind a terminal pointer."""

    terminal: BridgeTerminalResultV1
    ledger: ClaimLedgerV1 | None = None
    output: BridgeOutputV1 | None = None
    validation_report: BridgeValidationReportV1 | None = None
    review: GroundingReviewV1 | None = None
    evidence_pack: EvidencePackV1 | None = None
    failure: BridgeFailureV1 | None = None


class GroundedBridgeBuildResultV1(_StrictModel):
    schema_: Literal["application.grounded-bridge.build-result.v1"] = Field(
        "application.grounded-bridge.build-result.v1", alias="schema"
    )
    snapshot: GroundedBridgeSnapshotV1
    exit_code: Literal[0, 1]


class GroundedBridgeStartResultV1(_StrictModel):
    schema_: Literal["deepreason-mcp-bridge-start-v1"] = Field(
        "deepreason-mcp-bridge-start-v1", alias="schema"
    )
    state: Literal["running", "busy", "completed", "failed"]
    root: str
    manifest_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    status_operation: Literal["bridge_status"] = "bridge_status"
    result_operation: Literal["bridge_result"] = "bridge_result"
    process_status: Literal["success", "failure"] | None = None
    resolution: BridgeResolution | None = None
    terminal_event_seq: StrictInt | None = Field(default=None, ge=0)

    def presentation_payload(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        # Historical MCP responses include an explicit null epistemic
        # resolution for a replay-backed failed terminal, but not for an
        # operational launch failure that has no terminal event.
        if self.terminal_event_seq is not None and "resolution" not in payload:
            payload["resolution"] = None
        return payload


class GroundedBridgeViewResultV1(_StrictModel):
    schema_: Literal["application.grounded-bridge.view-result.v1"] = Field(
        "application.grounded-bridge.view-result.v1", alias="schema"
    )
    operation: Literal["status", "result", "claims", "inspect", "validate"]
    payload: dict[str, Any]
    exit_code: Literal[0, 1]
    snapshot: GroundedBridgeSnapshotV1 | None = Field(default=None, exclude=True)
    valid: bool | None = None

    def presentation_payload(self) -> dict[str, Any]:
        return dict(self.payload)


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


class GroundedBridgeWorkerRegistry:
    """Process-local worker handles; operator locks remain durable authority."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.threads: dict[str, threading.Thread] = {}

    def key(self, root: Path) -> str:
        return str(root.resolve())

    def live(self, root: Path) -> threading.Thread | None:
        thread = self.threads.get(self.key(root))
        return thread if thread is not None and thread.is_alive() else None


GROUNDED_BRIDGE_WORKERS = GroundedBridgeWorkerRegistry()


def read_bounded_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError(f"BRIDGE_RECORD_UNAVAILABLE: {path.name}")
    try:
        size = path.stat().st_size
    except OSError as error:
        raise ValueError(f"BRIDGE_RECORD_UNAVAILABLE: {path.name}") from error
    if size < 2 or size > MAX_CONTROL_FILE_BYTES:
        raise ValueError(f"BRIDGE_RECORD_SIZE_INVALID: {path.name}")
    try:
        value = json.loads(path.read_bytes())
    except (OSError, ValueError) as error:
        raise ValueError(f"BRIDGE_RECORD_CORRUPT: {path.name}") from error
    if not isinstance(value, dict):
        raise ValueError(f"BRIDGE_RECORD_CORRUPT: {path.name} must contain an object")
    return value


def validate_reference(value: str, *, field: str, require_hash: bool = False) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"BRIDGE_INPUT_INVALID: {field} must be non-blank text")
    if len(value) > MAX_REFERENCE_CHARS:
        raise ValueError(f"BRIDGE_INPUT_TOO_LARGE: {field}")
    if require_hash and _SHA256_REFERENCE.fullmatch(value.casefold()) is None:
        raise ValueError(f"BRIDGE_INPUT_INVALID: {field} must be an ID or hex prefix")
    return value


def bounded_focus(values: list[str] | tuple[str, ...], field: str) -> list[str]:
    if len(values) > MAX_FOCUS_REFS:
        raise ValueError(f"BRIDGE_INPUT_TOO_LARGE: at most {MAX_FOCUS_REFS} {field} values")
    normalized = [validate_reference(value, field=field, require_hash=True) for value in values]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"BRIDGE_INPUT_INVALID: duplicate {field}")
    return normalized


def resolve_problem(harness, value: str) -> str:
    value = validate_reference(value, field="problem")
    ids = sorted(harness.state.problems)
    if value in harness.state.problems:
        return value
    matches = [problem_id for problem_id in ids if problem_id.startswith(value)]
    if not matches:
        raise ValueError(f"BRIDGE_PROBLEM_NOT_FOUND: {value!r}")
    if len(matches) > 1:
        shown = matches[:8]
        prefixes = _unique_short_ids(matches)
        short = ", ".join(prefixes[item] for item in shown)
        raise ValueError(f"BRIDGE_PROBLEM_PREFIX_AMBIGUOUS: {value!r} ({short})")
    return matches[0]


def _validate_manifest_files(path: Path) -> None:
    """Reject unsafe manifest/sidecar paths before any parser reads them."""

    from deepreason.run_manifest import MANIFEST_HASH_NAME

    try:
        observed = path.lstat()
    except OSError as error:
        raise ValueError("BRIDGE_MANIFEST_INVALID") from error
    if (
        not stat.S_ISREG(observed.st_mode)
        or path.is_symlink()
        or not 2 <= observed.st_size <= MAX_CONTROL_FILE_BYTES
    ):
        raise ValueError("BRIDGE_MANIFEST_INVALID")
    for sidecar in (
        path.with_suffix(path.suffix + ".sha256"),
        path.parent / MANIFEST_HASH_NAME,
    ):
        try:
            sidecar_stat = sidecar.lstat()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise ValueError("BRIDGE_MANIFEST_INVALID") from error
        if (
            not stat.S_ISREG(sidecar_stat.st_mode)
            or sidecar.is_symlink()
            or not 1 <= sidecar_stat.st_size <= 1_024
        ):
            raise ValueError("BRIDGE_MANIFEST_INVALID")


def _load_manifest_without_echo(path: Path):
    from deepreason.run_manifest import RunManifestError, load_run_manifest

    try:
        return load_run_manifest(path)
    except RunManifestError as error:
        raise RunManifestError(
            error.code,
            "manifest validation or integrity check failed",
            error.pointer,
        ) from error


def load_bound_manifest(root: Path, supplied: str | None, *, bind: bool):
    from deepreason.run_manifest import MANIFEST_NAME, RunManifestError, bind_run_manifest

    bound_path = root / MANIFEST_NAME
    if bound_path.is_symlink():
        raise ValueError("BRIDGE_MANIFEST_INVALID")
    if bound_path.is_file():
        _validate_manifest_files(bound_path)
        manifest = _load_manifest_without_echo(bound_path)
        if supplied is not None:
            supplied_path = Path(supplied)
            _validate_manifest_files(supplied_path)
            requested = _load_manifest_without_echo(supplied_path)
            if requested.canonical_bytes() != manifest.canonical_bytes():
                raise RunManifestError(
                    "RUN_MANIFEST_CONFLICT",
                    "run root is already bound to a different manifest",
                    f"/{MANIFEST_NAME}",
                )
    elif supplied is not None:
        supplied_path = Path(supplied)
        _validate_manifest_files(supplied_path)
        manifest = _load_manifest_without_echo(supplied_path)
    else:
        raise ValueError("BRIDGE_MANIFEST_REQUIRED: pass --run-manifest for an unbound run")

    if manifest.schema_version not in {3, 4, 5, 6}:
        raise ValueError(
            "BRIDGE_MANIFEST_V3_REQUIRED: grounded bridge requires schema v3, v4, v5, or v6"
        )
    if manifest.workload_profile != "text":
        raise ValueError("BRIDGE_MANIFEST_WORKLOAD_MISMATCH: expected a v3 text manifest")
    policy = manifest.bridge_policy
    if policy is None or policy.mode != "grounded_two_stage":
        raise ValueError(
            "GROUNDED_BRIDGE_POLICY_REQUIRED: manifest does not enable grounded_two_stage"
        )
    if bind and not bound_path.is_file():
        bind_run_manifest(manifest, root)
    return manifest


def reasoning_run_state(root: Path, manifest=None) -> str | None:
    """Read one canonical reasoning terminal without inferring success."""

    target = root / "run-result.json"
    if target.is_symlink():
        raise ValueError("BRIDGE_RUN_RESULT_INVALID")
    if not target.exists():
        if manifest is not None and manifest.schema_version >= 6:
            raise ValueError(
                "BRIDGE_RUN_RESULT_REQUIRED: a v6 canonical bridge requires run-result.json"
            )
        return None
    try:
        payload = read_bounded_json(target)
    except ValueError as error:
        raise ValueError("BRIDGE_RUN_RESULT_INVALID") from error
    result_schema = payload.get("schema")
    if result_schema not in {
        "deepreason-run-result-v1",
        "deepreason-run-result-v2",
    }:
        raise ValueError("BRIDGE_RUN_RESULT_INVALID")
    if (
        manifest is not None
        and manifest.schema_version == 6
        and result_schema != "deepreason-run-result-v2"
    ):
        raise ValueError(
            "BRIDGE_RUN_RESULT_V2_REQUIRED: a v6 canonical bridge requires "
            "deepreason-run-result-v2"
        )
    if result_schema == "deepreason-run-result-v2":
        from deepreason.application.models import RunResultV2

        try:
            RunResultV2.model_validate(payload)
        except ValueError as error:
            raise ValueError("BRIDGE_RUN_RESULT_INVALID") from error
    state = payload.get("state")
    if state not in {"completed", "cancelled", "failed"}:
        raise ValueError("BRIDGE_RUN_RESULT_INVALID")
    return str(state)


def preflight_canonical_bridge(root: Path, manifest) -> None:
    state = reasoning_run_state(root, manifest)
    if state is not None and state != "completed":
        raise ValueError(
            f"BRIDGE_REASONING_NOT_COMPLETED: canonical run state is {state}"
        )
    if state == "completed":
        payload = read_bounded_json(root / "run-result.json")
        if (
            payload.get("schema") == "deepreason-run-result-v2"
            and payload.get("canonical_bridge_eligible") is not True
        ):
            raise ValueError(
                "BRIDGE_RUN_NOT_ELIGIBLE: RunResult v2 denies canonical bridge construction"
            )
        if manifest.schema_version == 6:
            from deepreason.verification.report import verify_root_report

            try:
                report = verify_root_report(root)
            except Exception as error:  # noqa: BLE001 - authority checks fail closed
                raise ValueError(
                    "BRIDGE_ROOT_VERIFICATION_FAILED: the v6 root could not be "
                    "verified before canonical bridge construction"
                ) from error
            if not report.integrity_valid or not report.security_valid:
                raise ValueError(
                    "BRIDGE_ROOT_AUTHORITY_INVALID: live v2 verification found an "
                    "integrity or security failure"
                )


def _build_bridge_adapter(manifest, harness):
    """Construct only frozen bridge routes with the manifest's repair cap."""

    from deepreason.llm.adapter import build_adapter
    from deepreason.run_manifest import config_from_run_manifest

    policy = manifest.bridge_policy
    roles = {policy.ledger_role, policy.composer_role}
    if policy.grounding_review:
        roles.add(policy.reviewer_role)
        roles.add(policy.grounding_repair_role)
    runtime_config = config_from_run_manifest(manifest)
    adapter_config = runtime_config.model_copy(
        update={"RETRY_MAX": policy.max_schema_repair_attempts}
    )
    adapter = build_adapter(
        adapter_config,
        harness.blobs,
        only_roles=roles,
        run_manifest=manifest,
        process_events=harness.log.read(),
    )
    if adapter.retry_max != policy.max_schema_repair_attempts:
        raise ValueError("BRIDGE_SCHEMA_REPAIR_POLICY_MISMATCH")
    missing = sorted(role for role in roles if not adapter.has_role(role))
    if missing:
        raise ValueError(
            "BRIDGE_ROUTE_UNAVAILABLE: manifest route could not construct " + ", ".join(missing)
        )
    if manifest.schema_version == 6:
        from deepreason.bridge.transactional_adapter import (
            TransactionalBridgeAdapter,
        )

        return TransactionalBridgeAdapter(adapter, harness, manifest)
    return adapter


def _compiled_bridge_workflow_policy(manifest):
    """Select the immutable bridge contract pair owned by this manifest."""

    policy = manifest.bridge_policy
    if manifest.schema_version == 6:
        return policy.workflow_policy(
            ledger_contract_version="v3",
            composition_contract_version="v2",
        )
    return policy.workflow_policy()


def preflight_focus(
    harness,
    manifest,
    block_refs: list[str],
    cluster_refs: list[str],
) -> tuple[list[str], list[str]]:
    """Resolve all operator focus before an unbound run is mutated."""

    from deepreason.scratch.service import ScratchService

    scratch = manifest.scratch_policy
    if scratch is None:
        raise ValueError("BRIDGE_MANIFEST_V3_REQUIRED: scratch policy is missing")
    if not scratch.enabled:
        if block_refs or cluster_refs:
            raise ValueError("BRIDGE_SCRATCH_DISABLED: focus values require scratchpad.enabled")
        return [], []
    service = ScratchService(harness)
    if not service.state.blocks:
        if block_refs or cluster_refs:
            raise ValueError("BRIDGE_SCRATCH_EMPTY: no focus object can be resolved")
        return [], []
    blocks = [service.get_block(value).id for value in block_refs]
    clusters = [service.get_cluster(value).id for value in cluster_refs]
    return blocks, clusters


def attention_pack(
    harness,
    manifest,
    block_refs: list[str],
    cluster_refs: list[str],
):
    from deepreason.scratch.attention import AttentionPlanner, AttentionRequestV1
    from deepreason.scratch.service import ScratchService

    scratch = manifest.scratch_policy
    if scratch is None or not scratch.enabled:
        return None
    service = ScratchService(harness)
    if not service.state.blocks:
        if block_refs or cluster_refs:
            raise ValueError("BRIDGE_SCRATCH_EMPTY: no focus object can be resolved")
        return None
    blocks = [service.get_block(value).id for value in block_refs]
    clusters = [service.get_cluster(value).id for value in cluster_refs]
    planner = AttentionPlanner(service, scratch.attention_policy())
    return planner.plan(
        AttentionRequestV1(
            focus_blocks=blocks or None,
            focus_clusters=clusters or None,
            maximum_blocks=scratch.max_blocks_per_pack,
            maximum_cluster_guides=scratch.max_guides_per_pack,
            deterministic_seed=harness._next_seq,
        )
    )


def _unique_short_ids(values) -> dict[str, str]:
    ordered = list(dict.fromkeys(value for value in values if value is not None))
    raw = {value: value.removeprefix("sha256:") for value in ordered}
    if not ordered:
        return {}
    maximum = max(len(value) for value in raw.values())
    for width in range(min(12, maximum), maximum + 1):
        prefixes = {value: body[:width] for value, body in raw.items()}
        if len(set(prefixes.values())) == len(prefixes):
            return prefixes
    return raw


def _prepare_bridge(
    intent: GroundedBridgeBuildIntentV1,
    locks,
) -> _PreparedBridge:
    from deepreason.harness import Harness
    from deepreason.llm.budget import TokenMeter
    from deepreason.run_manifest import bind_run_manifest

    root = Path(intent.root).resolve()
    manifest = load_bound_manifest(root, intent.run_manifest_ref, bind=False)
    preflight_canonical_bridge(root, manifest)
    preflight = Harness(root, read_only=True)
    problem_id = resolve_problem(preflight, intent.problem)
    blocks = bounded_focus(intent.focus_blocks, "focus-block")
    clusters = bounded_focus(intent.focus_clusters, "focus-cluster")
    resolved_blocks, resolved_clusters = preflight_focus(preflight, manifest, blocks, clusters)
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    adapter = _build_bridge_adapter(manifest, harness)
    if intent.token_budget is not None:
        adapter.meter = TokenMeter(intent.token_budget)
    attention = attention_pack(harness, manifest, resolved_blocks, resolved_clusters)
    return _PreparedBridge(
        root=root,
        manifest=manifest,
        harness=harness,
        problem_id=problem_id,
        target=intent.target,
        adapter=adapter,
        attention_pack=attention,
        locks=locks,
        token_budget=intent.token_budget,
    )


def _execute_bridge(prepared: _PreparedBridge) -> BridgeTerminalResultV1:
    """Run one already-authorized bridge using only manifest-owned routes."""

    policy = prepared.manifest.bridge_policy
    terminal = prepared.harness.build_bridge(
        prepared.problem_id,
        prepared.target,
        _compiled_bridge_workflow_policy(prepared.manifest),
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
    load_snapshot(prepared.root, terminal=terminal)
    return terminal


def _build_canonical(
    intent: GroundedBridgeBuildIntentV1,
) -> GroundedBridgeBuildResultV1:
    from deepreason.harness import Harness
    from deepreason.llm.budget import TokenMeter
    from deepreason.run_manifest import bind_run_manifest
    from deepreason.runtime.launch_policy import require_v6_launch_allowed

    root = Path(intent.root)
    if not root.is_dir():
        raise ValueError(f"BRIDGE_RUN_NOT_FOUND: {root}")
    blocks = bounded_focus(intent.focus_blocks, "focus-block")
    clusters = bounded_focus(intent.focus_clusters, "focus-cluster")
    manifest = load_bound_manifest(root, intent.run_manifest_ref, bind=False)
    require_v6_launch_allowed(manifest, operation="grounded bridge")
    preflight_canonical_bridge(root, manifest)
    preflight = Harness(root, read_only=True)
    problem_id = resolve_problem(preflight, intent.problem)
    resolved_blocks, resolved_clusters = preflight_focus(preflight, manifest, blocks, clusters)
    try:
        locks = operator_locks(root, owner="bridge", blocking=False)
    except ProcessLockBusy as error:
        raise ValueError("BRIDGE_ALREADY_RUNNING: another operator owns this run root") from error
    try:
        bind_run_manifest(manifest, root)
        harness = Harness(root)
        adapter = _build_bridge_adapter(manifest, harness)
        if intent.token_budget is not None:
            adapter.meter = TokenMeter(intent.token_budget)
        pack = attention_pack(harness, manifest, resolved_blocks, resolved_clusters)
        policy = manifest.bridge_policy
        terminal = harness.build_bridge(
            problem_id,
            intent.target,
            _compiled_bridge_workflow_policy(manifest),
            run_manifest_digest=manifest.sha256,
            stage_a_adapter=adapter,
            composition_adapter=adapter,
            review_adapter=(adapter if policy.grounding_review else None),
            repair_adapter=(
                adapter
                if policy.grounding_review and policy.max_grounding_repair_attempts
                else None
            ),
            attention_pack=pack,
            maximum_sections=policy.output_section_limit,
            formatting_profile=policy.target_profile,
        )
        snapshot = load_snapshot(root, terminal=terminal)
        return GroundedBridgeBuildResultV1(
            snapshot=snapshot,
            exit_code=0 if terminal.process_status == "success" else 1,
        )
    finally:
        locks.release()


def _build_derived(
    intent: GroundedBridgeBuildIntentV1,
) -> GroundedBridgeBuildResultV1:
    from deepreason.bridge.derived import (
        build_derived_bridge,
        open_derived_source,
        reserve_derived_destination,
    )
    from deepreason.harness import Harness
    from deepreason.llm.budget import TokenMeter
    from deepreason.run_manifest import bind_run_manifest
    from deepreason.runtime.launch_policy import require_v6_launch_allowed

    if intent.derived_output is None or intent.at_seq is None:
        raise ValueError(
            "BRIDGE_DERIVED_FLAGS_REQUIRED: --derived-output and --at-seq must be supplied together"
        )
    if intent.run_manifest_ref is None:
        raise ValueError("BRIDGE_DERIVED_MANIFEST_REQUIRED: pass a separate v3 --run-manifest")
    if intent.focus_blocks or intent.focus_clusters:
        raise ValueError(
            "BRIDGE_DERIVED_SCRATCH_CONTEXT_UNAVAILABLE: derived focus requires "
            "canonical destination receipts"
        )
    source_state = reasoning_run_state(Path(intent.root))
    if source_state in {"failed", "cancelled"} and not intent.diagnostic_after_failure:
        raise ValueError(
            "BRIDGE_REASONING_NOT_COMPLETED: use --diagnostic-after-failure with "
            "a separate --derived-output"
        )
    if intent.diagnostic_after_failure and source_state not in {"failed", "cancelled"}:
        raise ValueError(
            "BRIDGE_DIAGNOSTIC_SOURCE_NOT_FAILED: diagnostic mode requires a "
            "failed or cancelled source run"
        )
    source = open_derived_source(intent.root, intent.derived_output, intent.at_seq)
    problem_id = resolve_problem(source.harness, intent.problem)
    manifest = load_bound_manifest(source.destination_root, intent.run_manifest_ref, bind=False)
    require_v6_launch_allowed(manifest, operation="grounded bridge")
    reserve_derived_destination(source)
    if intent.diagnostic_after_failure:
        from deepreason.runtime.progress import _atomic_json

        _atomic_json(
            source.destination_root / "diagnostic-bridge.json",
            {
                "schema": "deepreason-diagnostic-bridge-v1",
                "canonical": False,
                "label": "noncanonical-after-failure",
                "source_state": source_state,
                "source_run_digest": source.source_run_digest,
                "formal_seq": source.formal_seq,
            },
        )
    try:
        locks = operator_locks(source.destination_root, owner="bridge-derived", blocking=False)
    except ProcessLockBusy as error:
        raise ValueError(
            "BRIDGE_ALREADY_RUNNING: another operator owns the derived root"
        ) from error
    try:
        bind_run_manifest(manifest, source.destination_root)
        destination = Harness(source.destination_root)
        adapter = _build_bridge_adapter(manifest, destination)
        if intent.token_budget is not None:
            adapter.meter = TokenMeter(intent.token_budget)
        policy = manifest.bridge_policy
        terminal = build_derived_bridge(
            source,
            destination,
            problem_id,
            intent.target,
            _compiled_bridge_workflow_policy(manifest),
            run_manifest_digest=manifest.sha256,
            stage_a_adapter=adapter,
            composition_adapter=adapter,
            review_adapter=(adapter if policy.grounding_review else None),
            repair_adapter=(
                adapter
                if policy.grounding_review and policy.max_grounding_repair_attempts
                else None
            ),
            maximum_sections=policy.output_section_limit,
            formatting_profile=policy.target_profile,
        )
        snapshot = load_snapshot(source.destination_root, terminal=terminal)
        return GroundedBridgeBuildResultV1(
            snapshot=snapshot,
            exit_code=0 if terminal.process_status == "success" else 1,
        )
    finally:
        locks.release()


def load_terminal(root: Path) -> BridgeTerminalResultV1:
    try:
        return BridgeTerminalResultV1.model_validate(read_bounded_json(root / BRIDGE_RESULT_NAME))
    except ValueError as error:
        if str(error).startswith("BRIDGE_RECORD_"):
            raise
        raise ValueError("BRIDGE_RESULT_INVALID") from error


def _load_result_manifest(root: Path):
    from deepreason.run_manifest import MANIFEST_NAME

    manifest_path = root / MANIFEST_NAME
    try:
        _validate_manifest_files(manifest_path)
        return _load_manifest_without_echo(manifest_path)
    except (OSError, RuntimeError, ValueError) as error:
        raise ValueError("BRIDGE_RESULT_MANIFEST_INVALID") from error


def load_snapshot(
    root: Path,
    *,
    terminal: BridgeTerminalResultV1 | None = None,
) -> GroundedBridgeSnapshotV1:
    """Replay and validate every object named by a terminal pointer."""

    from deepreason.harness import Harness

    terminal = terminal or load_terminal(root)
    manifest = _load_result_manifest(root)
    if terminal.run_manifest_digest != manifest.sha256:
        raise ValueError("BRIDGE_RESULT_INVALID: manifest digest differs from binding")
    if (
        manifest.schema_version not in {3, 4, 5, 6}
        or manifest.workload_profile != "text"
        or manifest.bridge_policy is None
        or manifest.bridge_policy.mode != "grounded_two_stage"
    ):
        raise ValueError(
            "BRIDGE_RESULT_INVALID: grounded result requires manifest v3, v4, or v5"
        )
    harness = Harness.at(root, terminal.terminal_event_seq)
    state = harness.bridge_state
    replay_events = list(harness.log.read(upto_seq=terminal.terminal_event_seq))
    terminal_event = next(
        (event for event in replay_events if event.seq == terminal.terminal_event_seq),
        None,
    )
    if terminal_event is None or terminal_event.bridge is None:
        raise ValueError("BRIDGE_RESULT_INVALID: terminal bridge event is absent")
    if terminal.process_status == "success":
        if (
            terminal.terminal_event_seq not in state.completed_events
            or terminal_event.bridge.action != BridgeAction.COMPLETED
        ):
            raise ValueError("BRIDGE_RESULT_INVALID: terminal completion event is absent")
        required_inputs = {
            terminal.claim_ledger_id,
            terminal.bridge_output_id,
            terminal.validation_report_id,
        }
        if terminal.review_id is not None:
            required_inputs.add(terminal.review_id)
        if None in required_inputs or set(terminal_event.bridge.inputs) != required_inputs:
            raise ValueError("BRIDGE_RESULT_INVALID: terminal completion inputs differ from result")
    else:
        if (
            terminal.terminal_event_seq not in state.failed_events
            or terminal_event.bridge.action != BridgeAction.FAILED
        ):
            raise ValueError("BRIDGE_RESULT_INVALID: terminal failure event is absent")
        if state.error_codes_by_event.get(terminal.terminal_event_seq) != terminal.error_code:
            raise ValueError("BRIDGE_RESULT_INVALID: terminal failure code differs from replay")

    def required(mapping, object_id: str | None, label: str):
        if object_id is None:
            return None
        try:
            return mapping[object_id]
        except KeyError as error:
            raise ValueError(f"BRIDGE_RESULT_INVALID: {label} object is absent") from error

    ledger = required(state.ledgers, terminal.claim_ledger_id, "claim ledger")
    output = required(state.outputs, terminal.bridge_output_id, "bridge output")
    report = required(
        state.validation_reports,
        terminal.validation_report_id,
        "validation report",
    )
    review = required(state.grounding_reviews, terminal.review_id, "grounding review")
    failure = required(state.failures, terminal.failure_id, "bridge failure")
    pack = state.evidence_packs.get(terminal.evidence_pack_id)
    if pack is None:
        raise ValueError("BRIDGE_RESULT_INVALID: evidence pack object is absent")
    if (
        pack.problem_ref != terminal.problem_id
        or pack.formal_seq != terminal.formal_seq
        or pack.source_run_digest != terminal.source_run_digest
    ):
        raise ValueError("BRIDGE_RESULT_INVALID: evidence-pack source fence differs from result")
    if ledger is not None and (
        ledger.problem_ref != terminal.problem_id
        or ledger.formal_seq != terminal.formal_seq
        or ledger.output_target != terminal.target
    ):
        raise ValueError("BRIDGE_RESULT_INVALID: claim-ledger identity differs from result")
    if output is not None and output.claim_ledger_id != terminal.claim_ledger_id:
        raise ValueError("BRIDGE_RESULT_INVALID: output names a different claim ledger")
    if output is None:
        if terminal.resolution is not None:
            raise ValueError("BRIDGE_RESULT_INVALID: result resolution has no output")
    elif output.resolution != terminal.resolution:
        raise ValueError("BRIDGE_RESULT_INVALID: result resolution differs from output")
    if report is not None and (
        report.claim_ledger_id != terminal.claim_ledger_id
        or report.bridge_output_id != terminal.bridge_output_id
    ):
        raise ValueError("BRIDGE_RESULT_INVALID: validation report names different objects")
    if review is not None and review.claim_ledger_id != terminal.claim_ledger_id:
        raise ValueError("BRIDGE_RESULT_INVALID: grounded review names different objects")

    def has_safe_replayed_repair() -> bool:
        if review is None or output is None:
            return False
        prior = state.outputs.get(review.bridge_output_id)
        if prior is None:
            return False
        repaired = any(
            event.bridge is not None
            and event.bridge.action == BridgeAction.REPAIR_ATTEMPTED
            and review.id in event.bridge.inputs
            and review.bridge_output_id in event.bridge.inputs
            and output.id in event.bridge.outputs
            for event in replay_events
        )
        if not repaired:
            return False
        from deepreason.bridge.repair import assert_safe_repair_diff

        try:
            assert_safe_repair_diff(prior, output)
        except (RuntimeError, ValueError):
            return False
        return True

    if terminal.process_status == "success":
        if report is None or not report.valid:
            raise ValueError("BRIDGE_RESULT_INVALID: successful result requires valid report")
        review_required = manifest.bridge_policy.grounding_review
        if review_required:
            if review is None:
                raise ValueError("BRIDGE_RESULT_INVALID: successful grounded review is absent")
            if review.passed:
                if review.bridge_output_id != terminal.bridge_output_id:
                    raise ValueError(
                        "BRIDGE_RESULT_INVALID: grounded review names different objects"
                    )
            elif not has_safe_replayed_repair():
                raise ValueError(
                    "BRIDGE_RESULT_INVALID: successful grounded review did not pass "
                    "or authorize a replayed safe repair"
                )
        if not review_required and review is not None:
            raise ValueError("BRIDGE_RESULT_INVALID: review is outside frozen policy")
        if failure is not None:
            raise ValueError("BRIDGE_RESULT_INVALID: successful result names a failure")
    else:
        if (
            review is not None
            and review.bridge_output_id != terminal.bridge_output_id
            and not has_safe_replayed_repair()
        ):
            raise ValueError("BRIDGE_RESULT_INVALID: grounded review names different objects")
        if failure is None or terminal.failure_id not in terminal_event.bridge.outputs:
            raise ValueError("BRIDGE_RESULT_INVALID: failed event does not store its failure")
        expected = {
            "run_manifest_digest": terminal.run_manifest_digest,
            "formal_seq": terminal.formal_seq,
            "problem_ref": terminal.problem_id,
            "output_target": terminal.target,
            "evidence_pack_id": terminal.evidence_pack_id,
            "error_code": terminal.error_code,
            "error_message": terminal.error_message,
            "claim_ledger_id": terminal.claim_ledger_id,
            "bridge_output_id": terminal.bridge_output_id,
            "validation_report_id": terminal.validation_report_id,
            "review_id": terminal.review_id,
        }
        if any(getattr(failure, field) != value for field, value in expected.items()):
            raise ValueError("BRIDGE_RESULT_INVALID: failure fields differ from replay")
        if failure.catalog_id not in state.catalogs:
            raise ValueError("BRIDGE_RESULT_INVALID: failure catalog is absent")
        if set(failure.terminal_inputs) != set(terminal_event.bridge.inputs):
            raise ValueError("BRIDGE_RESULT_INVALID: failure inputs differ from replay")
    return GroundedBridgeSnapshotV1(
        terminal=terminal,
        ledger=ledger,
        output=output,
        validation_report=report,
        review=review,
        evidence_pack=pack,
        failure=failure,
    )


def _model_json(value):
    return (
        value.model_dump(mode="json", by_alias=True, exclude_none=True)
        if value is not None
        else None
    )


def _json_item(value):
    return _model_json(value) if hasattr(value, "model_dump") else value


def page_bounds(limit: int, offset: int) -> tuple[int, int]:
    if isinstance(limit, bool) or not 1 <= limit <= MAX_PAGE_LIMIT:
        raise ValueError(f"BRIDGE_PAGE_LIMIT_INVALID: --limit must be 1 through {MAX_PAGE_LIMIT}")
    if isinstance(offset, bool) or not 0 <= offset <= MAX_PAGE_OFFSET:
        raise ValueError(
            f"BRIDGE_PAGE_OFFSET_INVALID: --offset must be 0 through {MAX_PAGE_OFFSET}"
        )
    return limit, offset


def _page_values(values, *, limit: int, offset: int):
    items = list(values or ())
    selected = items[offset : offset + limit]
    return selected, {
        "offset": offset,
        "limit": limit,
        "total": len(items),
        "returned": len(selected),
        "has_more": offset + len(selected) < len(items),
        "next_offset": (
            offset + len(selected) if selected and offset + len(selected) < len(items) else None
        ),
    }


def _page_model_field(
    model_data: dict[str, Any] | None,
    source,
    field: str,
    pointer: str,
    *,
    limit: int,
    offset: int,
    collections: list[dict[str, Any]],
) -> None:
    values, metadata = _page_values(
        getattr(source, field, None) if source is not None else (),
        limit=limit,
        offset=offset,
    )
    metadata["pointer"] = pointer
    collections.append(metadata)
    if model_data is not None and field in model_data:
        model_data[field] = [_json_item(item) for item in values]


def _bounded_json_text(value, *, pointer: str = "", truncated=None):
    if truncated is None:
        truncated = []
    if isinstance(value, dict):
        return {
            key: _bounded_json_text(
                item,
                pointer=f"{pointer}/{str(key).replace('~', '~0').replace('/', '~1')}",
                truncated=truncated,
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        selected = value[:MAX_JSON_ARRAY_ITEMS]
        if len(value) > len(selected):
            truncated.append(
                {
                    "pointer": pointer or "/",
                    "original_items": len(value),
                    "returned_items": len(selected),
                }
            )
        return [
            _bounded_json_text(
                item,
                pointer=f"{pointer}/{index}",
                truncated=truncated,
            )
            for index, item in enumerate(selected)
        ]
    if isinstance(value, str) and len(value) > MAX_JSON_TEXT_CHARS:
        truncated.append(
            {
                "pointer": pointer or "/",
                "original_chars": len(value),
                "returned_chars": MAX_JSON_TEXT_CHARS,
            }
        )
        return value[:MAX_JSON_TEXT_CHARS]
    return value


def _finish_bounded_payload(
    payload: dict[str, Any],
    collections: list[dict[str, Any]],
    *,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    truncated: list[dict[str, Any]] = []
    payload = _bounded_json_text(payload, truncated=truncated)
    payload["pagination"] = {
        "offset": offset,
        "limit": limit,
        "collections": collections,
    }
    payload["truncation"] = {
        "text_limit_chars": MAX_JSON_TEXT_CHARS,
        "array_limit_items": MAX_JSON_ARRAY_ITEMS,
        "truncated": bool(truncated),
        "fields": truncated,
    }
    return payload


def result_payload(
    snapshot: GroundedBridgeSnapshotV1,
    *,
    limit: int = DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    limit, offset = page_bounds(limit, offset)
    ledger = _model_json(snapshot.ledger)
    output = _model_json(snapshot.output)
    validation = _model_json(snapshot.validation_report)
    review = _model_json(snapshot.review)
    collections: list[dict[str, Any]] = []
    for data, source, field, pointer in (
        (ledger, snapshot.ledger, "entries", "/claim_ledger/entries"),
        (
            ledger,
            snapshot.ledger,
            "uncovered_requirements",
            "/claim_ledger/uncovered_requirements",
        ),
        (
            ledger,
            snapshot.ledger,
            "source_conflicts",
            "/claim_ledger/source_conflicts",
        ),
        (output, snapshot.output, "sections", "/output/sections"),
        (output, snapshot.output, "unresolved_items", "/output/unresolved_items"),
        (
            validation,
            snapshot.validation_report,
            "findings",
            "/validation_report/findings",
        ),
        (review, snapshot.review, "findings", "/grounded_review/findings"),
    ):
        _page_model_field(
            data,
            source,
            field,
            pointer,
            limit=limit,
            offset=offset,
            collections=collections,
        )
    return _finish_bounded_payload(
        {
            "schema": "deepreason-cli-bridge-result-v1",
            "terminal": _model_json(snapshot.terminal),
            "failure": _model_json(snapshot.failure),
            "claim_ledger": ledger,
            "output": output,
            "validation_report": validation,
            "grounded_review": review,
        },
        collections,
        limit=limit,
        offset=offset,
    )


def claims_payload(
    snapshot: GroundedBridgeSnapshotV1,
    *,
    limit: int = DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    limit, offset = page_bounds(limit, offset)
    ledger = snapshot.ledger
    if ledger is None:
        raise ValueError("BRIDGE_RESULT_HAS_NO_LEDGER")
    entries, entries_page = _page_values(ledger.entries, limit=limit, offset=offset)
    uncovered, uncovered_page = _page_values(
        ledger.uncovered_requirements, limit=limit, offset=offset
    )
    conflicts, conflicts_page = _page_values(ledger.source_conflicts, limit=limit, offset=offset)
    collections = [
        {**page, "pointer": pointer}
        for pointer, page in (
            ("/entries", entries_page),
            ("/uncovered_requirements", uncovered_page),
            ("/source_conflicts", conflicts_page),
        )
    ]
    return _finish_bounded_payload(
        {
            "schema": "deepreason-cli-bridge-claims-v1",
            "claim_ledger_id": ledger.id,
            "problem_id": snapshot.terminal.problem_id,
            "formal_seq": ledger.formal_seq,
            "entries": [_model_json(entry) for entry in entries],
            "uncovered_requirements": [_model_json(item) for item in uncovered],
            "source_conflicts": [_model_json(item) for item in conflicts],
        },
        collections,
        limit=limit,
        offset=offset,
    )


def inspect_payload(
    snapshot: GroundedBridgeSnapshotV1,
    *,
    limit: int = DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    limit, offset = page_bounds(limit, offset)
    pack = _model_json(snapshot.evidence_pack)
    validation = _model_json(snapshot.validation_report)
    review = _model_json(snapshot.review)
    collections: list[dict[str, Any]] = []
    for data, source, field, pointer in (
        (
            pack,
            snapshot.evidence_pack,
            "problem_family_refs",
            "/evidence_pack/problem_family_refs",
        ),
        (pack, snapshot.evidence_pack, "survivors", "/evidence_pack/survivors"),
        (
            pack,
            snapshot.evidence_pack,
            "argued_refutations",
            "/evidence_pack/argued_refutations",
        ),
        (
            pack,
            snapshot.evidence_pack,
            "pairwise_rulings",
            "/evidence_pack/pairwise_rulings",
        ),
        (
            pack,
            snapshot.evidence_pack,
            "open_rivals",
            "/evidence_pack/open_rivals",
        ),
        (
            pack,
            snapshot.evidence_pack,
            "catalog_items",
            "/evidence_pack/catalog_items",
        ),
        (
            pack,
            snapshot.evidence_pack,
            "legacy_citable_ids",
            "/evidence_pack/legacy_citable_ids",
        ),
        (
            validation,
            snapshot.validation_report,
            "findings",
            "/validation_report/findings",
        ),
        (review, snapshot.review, "findings", "/grounded_review/findings"),
    ):
        _page_model_field(
            data,
            source,
            field,
            pointer,
            limit=limit,
            offset=offset,
            collections=collections,
        )
    return _finish_bounded_payload(
        {
            "schema": "deepreason-cli-bridge-inspect-v1",
            "terminal": _model_json(snapshot.terminal),
            "failure": _model_json(snapshot.failure),
            "evidence_pack": pack,
            "validation_report": validation,
            "grounded_review": review,
        },
        collections,
        limit=limit,
        offset=offset,
    )


def validate_payload(
    snapshot: GroundedBridgeSnapshotV1,
    *,
    limit: int = DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> tuple[dict[str, Any], bool]:
    from deepreason.bridge.validate import validate_bridge_output, validate_claim_ledger

    limit, offset = page_bounds(limit, offset)
    if snapshot.ledger is None or snapshot.output is None:
        raise ValueError("BRIDGE_RESULT_HAS_NO_VALIDATABLE_OUTPUT")
    ledger_report = validate_claim_ledger(snapshot.ledger)
    output_report = validate_bridge_output(snapshot.ledger, snapshot.output)
    stored_matches = (
        snapshot.validation_report is not None and snapshot.validation_report.id == output_report.id
    )
    valid = ledger_report.valid and output_report.valid and stored_matches
    ledger_data = _model_json(ledger_report)
    output_data = _model_json(output_report)
    collections: list[dict[str, Any]] = []
    for data, report, pointer in (
        (ledger_data, ledger_report, "/claim_ledger_report/findings"),
        (output_data, output_report, "/bridge_output_report/findings"),
    ):
        _page_model_field(
            data,
            report,
            "findings",
            pointer,
            limit=limit,
            offset=offset,
            collections=collections,
        )
    return (
        _finish_bounded_payload(
            {
                "schema": "deepreason-cli-bridge-validation-v1",
                "valid": valid,
                "stored_report_matches": stored_matches,
                "claim_ledger_report": ledger_data,
                "bridge_output_report": output_data,
            },
            collections,
            limit=limit,
            offset=offset,
        ),
        valid,
    )


def status_payload(root: Path) -> dict[str, Any]:
    from deepreason.bridge.operations import read_failure, read_status

    operation = read_status(root)
    status_path = root / BRIDGE_STATUS_NAME
    if not status_path.exists():
        if operation is not None:
            if operation.state == "failed":
                read_failure(root)
            return operation.model_dump(mode="json", by_alias=True, exclude_none=True)
        raise ValueError(f"BRIDGE_RECORD_UNAVAILABLE: {BRIDGE_STATUS_NAME}")
    try:
        status = BridgeCLIStatusV1.model_validate(read_bounded_json(status_path))
    except ValueError as error:
        if operation is not None and operation.state == "failed":
            read_failure(root)
            return operation.model_dump(mode="json", by_alias=True, exclude_none=True)
        if str(error).startswith("BRIDGE_RECORD_"):
            raise
        raise ValueError("BRIDGE_STATUS_INVALID") from error
    payload = status.model_dump(mode="json", by_alias=True, exclude_none=True)
    result_path = root / BRIDGE_RESULT_NAME
    if status.state in {"completed", "failed"}:
        if not result_path.is_file() or result_path.is_symlink():
            if operation is not None and operation.state == "failed":
                read_failure(root)
                return operation.model_dump(mode="json", by_alias=True, exclude_none=True)
            raise ValueError("BRIDGE_STATUS_INVALID: terminal result is absent")
        try:
            snapshot = load_snapshot(root)
        except ValueError:
            if operation is not None and operation.state == "failed":
                read_failure(root)
                return operation.model_dump(mode="json", by_alias=True, exclude_none=True)
            raise
        terminal = snapshot.terminal
        if terminal.terminal_event_seq != status.terminal_event_seq:
            raise ValueError("BRIDGE_STATUS_INVALID: status/result sequence mismatch")
        if terminal.process_status != status.process_status:
            raise ValueError("BRIDGE_STATUS_INVALID: status/result process mismatch")
        if terminal.formal_seq != status.formal_seq:
            raise ValueError("BRIDGE_STATUS_INVALID: status/result formal fence mismatch")
        if terminal.resolution != status.resolution:
            raise ValueError("BRIDGE_STATUS_INVALID: status/result resolution mismatch")
        if terminal.error_code != status.error_code:
            raise ValueError("BRIDGE_STATUS_INVALID: status/result error mismatch")
        payload["stable_ids"] = {
            "evidence_pack_id": terminal.evidence_pack_id,
            "claim_ledger_id": terminal.claim_ledger_id,
            "bridge_output_id": terminal.bridge_output_id,
            "validation_report_id": terminal.validation_report_id,
            "review_id": terminal.review_id,
            "failure_id": terminal.failure_id,
        }
    elif operation is not None and operation.state == "failed":
        read_failure(root)
        return operation.model_dump(mode="json", by_alias=True, exclude_none=True)
    return payload


def _notify(progress_callback, event: dict[str, Any]) -> None:
    if progress_callback is None:
        return
    try:
        progress_callback(event)
    except (Exception, SystemExit):
        # Presentation and transport callbacks never own workflow state.
        return


def _existing_terminal(root: Path) -> BridgeTerminalResultV1 | None:
    result = root / BRIDGE_RESULT_NAME
    if not result.exists():
        return None
    return load_snapshot(root).terminal


def _start_result(
    state: Literal["running", "busy", "completed", "failed"],
    root: Path,
    *,
    manifest_sha256: str | None = None,
    terminal: BridgeTerminalResultV1 | None = None,
) -> GroundedBridgeStartResultV1:
    return GroundedBridgeStartResultV1(
        state=state,
        root=str(root),
        manifest_sha256=manifest_sha256,
        process_status=(terminal.process_status if terminal is not None else None),
        resolution=(terminal.resolution if terminal is not None else None),
        terminal_event_seq=(terminal.terminal_event_seq if terminal is not None else None),
    )


class GroundedBridgeApplicationService:
    """Canonical bridge preparation, execution, lifecycle, and inspection."""

    def __init__(
        self,
        registry: GroundedBridgeWorkerRegistry | None = None,
    ) -> None:
        self.registry = registry or GROUNDED_BRIDGE_WORKERS

    def build(
        self,
        intent: GroundedBridgeBuildIntentV1,
    ) -> GroundedBridgeBuildResultV1:
        intent = GroundedBridgeBuildIntentV1.model_validate(intent)
        if intent.derived_output is not None or intent.at_seq is not None:
            return _build_derived(intent)
        return _build_canonical(intent)

    def start(
        self,
        intent: GroundedBridgeBuildIntentV1,
        *,
        progress_callback=None,
    ) -> GroundedBridgeStartResultV1:
        """Launch one asynchronous build after complete read-only preflight."""

        from deepreason.bridge.operations import write_running
        from deepreason.harness import Harness
        from deepreason.runtime.launch_policy import require_v6_launch_allowed

        intent = GroundedBridgeBuildIntentV1.model_validate(intent)
        if intent.derived_output is not None or intent.at_seq is not None:
            raise ValueError("BRIDGE_ASYNC_DERIVED_UNSUPPORTED")
        root = Path(intent.root)
        if root.is_symlink() or not root.is_dir():
            raise ValueError("BRIDGE_RUN_NOT_FOUND")
        root = root.resolve()
        manifest = load_bound_manifest(root, intent.run_manifest_ref, bind=False)
        require_v6_launch_allowed(manifest, operation="grounded bridge")
        preflight_canonical_bridge(root, manifest)
        preflight = Harness(root, read_only=True)
        resolve_problem(preflight, intent.problem)
        blocks = bounded_focus(intent.focus_blocks, "focus-block")
        clusters = bounded_focus(intent.focus_clusters, "focus-cluster")
        preflight_focus(preflight, manifest, blocks, clusters)

        with self.registry.lock:
            if self.registry.live(root) is not None:
                return _start_result("busy", root, manifest_sha256=manifest.sha256)
            existing = _existing_terminal(root)
            if existing is not None:
                state = "completed" if existing.process_status == "success" else "failed"
                return _start_result(
                    state,
                    root,
                    manifest_sha256=manifest.sha256,
                    terminal=existing,
                )
            try:
                locks = operator_locks(root, owner="bridge", blocking=False)
            except ProcessLockBusy:
                return _start_result("busy", root, manifest_sha256=manifest.sha256)
            try:
                existing = _existing_terminal(root)
            except BaseException:
                locks.release()
                raise
            if existing is not None:
                locks.release()
                state = "completed" if existing.process_status == "success" else "failed"
                return _start_result(
                    state,
                    root,
                    manifest_sha256=manifest.sha256,
                    terminal=existing,
                )
            try:
                prepared = _prepare_bridge(
                    intent,
                    locks,
                )
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
                    from deepreason.bridge.operations import write_failure

                    write_failure(root, manifest.sha256, type(error).__name__)
                else:
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
            self.registry.threads[self.registry.key(root)] = thread
            try:
                thread.start()
            except BaseException as error:
                self.registry.threads.pop(self.registry.key(root), None)
                try:
                    from deepreason.bridge.operations import write_failure

                    write_failure(root, manifest.sha256, type(error).__name__)
                finally:
                    prepared.locks.release()
                return _start_result("failed", root, manifest_sha256=manifest.sha256)
            try:
                _notify(
                    progress_callback,
                    {"seq": 0, "activity": "bridge_started"},
                )
            finally:
                launch_gate.set()
        return _start_result("running", root, manifest_sha256=manifest.sha256)

    def status(
        self,
        intent: GroundedBridgeStatusIntentV1,
    ) -> GroundedBridgeViewResultV1:
        intent = GroundedBridgeStatusIntentV1.model_validate(intent)
        root = Path(intent.root).resolve()
        try:
            payload = status_payload(root)
        except ValueError as error:
            if not str(error).startswith("BRIDGE_RECORD_UNAVAILABLE"):
                raise
            payload = {
                "schema": "deepreason-mcp-bridge-status-v1",
                "state": "not_started",
            }
        return GroundedBridgeViewResultV1(
            operation="status",
            payload=payload,
            exit_code=1 if payload.get("process_status") == "failure" else 0,
        )

    def result(
        self,
        intent: GroundedBridgeResultIntentV1,
    ) -> GroundedBridgeViewResultV1:
        from deepreason.bridge.operations import read_failure

        intent = GroundedBridgeResultIntentV1.model_validate(intent)
        root = Path(intent.root).resolve()
        try:
            snapshot = load_snapshot(root)
        except ValueError:
            operation = read_failure(root)
            if operation is None:
                raise
            return GroundedBridgeViewResultV1(
                operation="result",
                payload=operation.model_dump(mode="json", by_alias=True, exclude_none=True),
                exit_code=1,
            )
        return GroundedBridgeViewResultV1(
            operation="result",
            payload=result_payload(
                snapshot,
                limit=intent.limit,
                offset=intent.offset,
            ),
            exit_code=0 if snapshot.terminal.process_status == "success" else 1,
            snapshot=snapshot,
        )

    def claims(
        self,
        intent: GroundedBridgeClaimsIntentV1,
    ) -> GroundedBridgeViewResultV1:
        intent = GroundedBridgeClaimsIntentV1.model_validate(intent)
        snapshot = load_snapshot(Path(intent.root).resolve())
        return GroundedBridgeViewResultV1(
            operation="claims",
            payload=claims_payload(
                snapshot,
                limit=intent.limit,
                offset=intent.offset,
            ),
            exit_code=0,
            snapshot=snapshot,
        )

    def inspect(
        self,
        intent: GroundedBridgeInspectIntentV1,
    ) -> GroundedBridgeViewResultV1:
        intent = GroundedBridgeInspectIntentV1.model_validate(intent)
        snapshot = load_snapshot(Path(intent.root).resolve())
        return GroundedBridgeViewResultV1(
            operation="inspect",
            payload=inspect_payload(
                snapshot,
                limit=intent.limit,
                offset=intent.offset,
            ),
            exit_code=0 if snapshot.terminal.process_status == "success" else 1,
            snapshot=snapshot,
        )

    def validate(
        self,
        intent: GroundedBridgeValidateIntentV1,
    ) -> GroundedBridgeViewResultV1:
        intent = GroundedBridgeValidateIntentV1.model_validate(intent)
        snapshot = load_snapshot(Path(intent.root).resolve())
        payload, valid = validate_payload(
            snapshot,
            limit=intent.limit,
            offset=intent.offset,
        )
        return GroundedBridgeViewResultV1(
            operation="validate",
            payload=payload,
            exit_code=0 if valid else 1,
            snapshot=snapshot,
            valid=valid,
        )


GROUNDED_BRIDGE_SERVICE = GroundedBridgeApplicationService()


__all__ = [
    "BridgeCLIStatusV1",
    "DEFAULT_PAGE_LIMIT",
    "GROUNDED_BRIDGE_SERVICE",
    "GROUNDED_BRIDGE_WORKERS",
    "GroundedBridgeApplicationService",
    "GroundedBridgeBuildIntentV1",
    "GroundedBridgeBuildResultV1",
    "GroundedBridgeClaimsIntentV1",
    "GroundedBridgeInspectIntentV1",
    "GroundedBridgeResultIntentV1",
    "GroundedBridgeSnapshotV1",
    "GroundedBridgeStartResultV1",
    "GroundedBridgeStatusIntentV1",
    "GroundedBridgeValidateIntentV1",
    "GroundedBridgeViewResultV1",
    "attention_pack",
    "bounded_focus",
    "claims_payload",
    "inspect_payload",
    "load_bound_manifest",
    "load_snapshot",
    "load_terminal",
    "page_bounds",
    "preflight_focus",
    "preflight_canonical_bridge",
    "read_bounded_json",
    "reasoning_run_state",
    "resolve_problem",
    "result_payload",
    "status_payload",
    "validate_payload",
]
