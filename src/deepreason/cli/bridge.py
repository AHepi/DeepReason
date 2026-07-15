"""Grounded final-output bridge commands.

The command surface deliberately exposes only one harness-owned workflow and
read-only views of its canonical records.  Models never receive paths, route
selectors, provider catalogs, or the complete scratch workspace.  Machine
output retains full stable IDs; the default human view uses short unique
prefixes and explicit epistemic labels.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepreason.bridge.harness import (
    BRIDGE_RESULT_NAME,
    BRIDGE_STATUS_NAME,
    BridgeTerminalResultV1,
)
from deepreason.bridge.events import BridgeAction
from deepreason.bridge.models import BridgeResolution, RenderingMode


_MAX_CONTROL_FILE_BYTES = 4 * 1024 * 1024
_MAX_FOCUS_REFS = 64
_MAX_REFERENCE_CHARS = 512
_SHORT_ID_LENGTH = 12
_SHA256 = re.compile(r"^(?:sha256:)?[0-9a-f]{1,64}$")
_DEFAULT_PAGE_LIMIT = 25
_MAX_PAGE_LIMIT = 100
_MAX_PAGE_OFFSET = 1_000_000
_MAX_JSON_TEXT_CHARS = 16_384
_MAX_JSON_ARRAY_ITEMS = 100


class BridgeCLIStatusV1(BaseModel):
    """Strict fixed-name status record shared with the later MCP worker."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    schema_: str = Field(alias="schema", pattern=r"^deepreason-bridge-status-v1$")
    state: str = Field(pattern=r"^(?:starting|running|completed|failed)$")
    process_status: str | None = Field(
        default=None, pattern=r"^(?:success|failure)$"
    )
    formal_seq: int | None = Field(default=None, ge=0)
    terminal_event_seq: int | None = Field(default=None, ge=0)
    resolution: BridgeResolution | None = None
    error_code: str | None = Field(
        default=None, pattern=r"^[A-Z][A-Z0-9_]{0,127}$"
    )

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
class _BridgeSnapshot:
    terminal: BridgeTerminalResultV1
    harness: Any
    ledger: Any = None
    output: Any = None
    validation_report: Any = None
    review: Any = None
    evidence_pack: Any = None
    failure: Any = None


_MODE_LABELS = {
    RenderingMode.FACT: "Grounded fact",
    RenderingMode.OBSERVATION: "Recorded observation",
    RenderingMode.INFERENCE: "Supported inference",
    RenderingMode.CONJECTURE: "Surviving conjecture",
    RenderingMode.ASSUMPTION: "Explicit assumption",
    RenderingMode.UNKNOWN: "Unknown",
    RenderingMode.CONFLICT: "Conflicting evidence",
}

_CLAIM_LABELS = {
    "source_fact": "Grounded fact",
    "recorded_observation": "Recorded observation",
    "supported_inference": "Supported inference",
    "surviving_conjecture": "Surviving conjecture",
    "assumption": "Explicit assumption",
    "unknown": "Unknown",
    "conflict": "Conflicting evidence",
}

_RESOLUTION_LABELS = {
    BridgeResolution.ANSWERED: "Answered",
    BridgeResolution.PARTIALLY_ANSWERED: "Partially answered",
    BridgeResolution.UNDERDETERMINED: "Underdetermined",
    BridgeResolution.INSUFFICIENT_EVIDENCE: "Insufficient evidence",
    BridgeResolution.CONFLICTING_EVIDENCE: "Conflicting evidence",
    BridgeResolution.OUTSIDE_SCOPE: "Outside scope",
}


def register_bridge_commands(subparsers) -> None:
    """Register the non-breaking ``bridge`` command family on argparse."""

    bridge = subparsers.add_parser(
        "bridge", help="build and inspect grounded final outputs"
    )
    commands = bridge.add_subparsers(dest="bridge_command", required=True)

    build = commands.add_parser(
        "build", help="build a validated claim ledger, then compose the final output"
    )
    build.add_argument("problem", help="problem ID or unique prefix")
    build.add_argument(
        "--target", choices=("thesis", "summary", "answer"), default="answer"
    )
    build.add_argument(
        "--run-manifest",
        default=None,
        help="v3 manifest (needed only when this run is not already bound)",
    )
    build.add_argument(
        "--focus-block", action="append", default=[], help="scratch block ID or prefix"
    )
    build.add_argument(
        "--focus-cluster",
        action="append",
        default=[],
        help="scratch cluster ID or prefix",
    )
    build.add_argument("--json", action="store_true", help="emit typed machine JSON")
    _add_page_arguments(build)

    for name, help_text in (
        ("status", "show bridge process status"),
        ("result", "show the latest grounded output"),
        ("inspect", "inspect validation and grounded-review records"),
        ("claims", "inspect the validated claim ledger"),
        ("validate", "re-run deterministic ledger and output validation"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument(
            "--json", action="store_true", help="emit typed machine JSON"
        )
        if name in {"result", "inspect", "claims", "validate"}:
            _add_page_arguments(command)


# Friendly aliases let the dispatcher refactor independently without
# proliferating command implementations.
add_bridge_parser = register_bridge_commands
register_parser = register_bridge_commands


def _add_page_arguments(parser) -> None:
    parser.add_argument(
        "--limit",
        type=int,
        default=_DEFAULT_PAGE_LIMIT,
        help=f"records per collection (default {_DEFAULT_PAGE_LIMIT}, max {_MAX_PAGE_LIMIT})",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="zero-based collection offset",
    )


def _read_bounded_json(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise ValueError(f"BRIDGE_RECORD_UNAVAILABLE: {path.name}")
    try:
        size = path.stat().st_size
    except OSError as error:
        raise ValueError(f"BRIDGE_RECORD_UNAVAILABLE: {path.name}") from error
    if size < 2 or size > _MAX_CONTROL_FILE_BYTES:
        raise ValueError(f"BRIDGE_RECORD_SIZE_INVALID: {path.name}")
    try:
        value = json.loads(path.read_bytes())
    except (OSError, ValueError) as error:
        raise ValueError(f"BRIDGE_RECORD_CORRUPT: {path.name}") from error
    if not isinstance(value, dict):
        raise ValueError(f"BRIDGE_RECORD_CORRUPT: {path.name} must contain an object")
    return value


def _safe_human(value: object, *, maximum: int = 4_096) -> str:
    """Bound untrusted terminal text and neutralize controls/ANSI escapes."""

    text = str(value)
    clipped = text[:maximum]
    rendered: list[str] = []
    for character in clipped:
        if character in "\r\n\t":
            rendered.append(" ")
        elif unicodedata.category(character).startswith("C"):
            rendered.append(f"\\u{ord(character):04x}")
        else:
            rendered.append(character)
    if len(text) > maximum:
        rendered.append("…")
    return "".join(rendered)


def _validate_reference(value: str, *, field: str, require_hash: bool = False) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"BRIDGE_INPUT_INVALID: {field} must be non-blank text")
    if len(value) > _MAX_REFERENCE_CHARS:
        raise ValueError(f"BRIDGE_INPUT_TOO_LARGE: {field}")
    if require_hash and _SHA256.fullmatch(value.casefold()) is None:
        raise ValueError(f"BRIDGE_INPUT_INVALID: {field} must be an ID or hex prefix")
    return value


def _bounded_focus(values: list[str], field: str) -> list[str]:
    if len(values) > _MAX_FOCUS_REFS:
        raise ValueError(
            f"BRIDGE_INPUT_TOO_LARGE: at most {_MAX_FOCUS_REFS} {field} values"
        )
    normalized = [
        _validate_reference(value, field=field, require_hash=True) for value in values
    ]
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"BRIDGE_INPUT_INVALID: duplicate {field}")
    return normalized


def _resolve_problem(harness, value: str) -> str:
    value = _validate_reference(value, field="problem")
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


def _load_bound_manifest(root: Path, supplied: str | None, *, bind: bool):
    from deepreason.run_manifest import (
        MANIFEST_NAME,
        RunManifestError,
        bind_run_manifest,
        load_run_manifest,
    )

    bound_path = root / MANIFEST_NAME
    if bound_path.is_file():
        manifest = load_run_manifest(bound_path)
        if supplied is not None:
            requested = load_run_manifest(supplied)
            if requested.canonical_bytes() != manifest.canonical_bytes():
                raise RunManifestError(
                    "RUN_MANIFEST_CONFLICT",
                    "run root is already bound to a different manifest",
                    f"/{MANIFEST_NAME}",
                )
    elif supplied is not None:
        manifest = load_run_manifest(supplied)
    else:
        raise ValueError(
            "BRIDGE_MANIFEST_REQUIRED: pass --run-manifest for an unbound run"
        )

    if manifest.schema_version != 3:
        raise ValueError("BRIDGE_MANIFEST_V3_REQUIRED: grounded bridge requires schema v3")
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
    # The authoritative immutable cap stays in the manifest. The adapter is
    # constructed with a derived local Config; neither authority is mutated.
    if adapter.retry_max != policy.max_schema_repair_attempts:
        raise ValueError("BRIDGE_SCHEMA_REPAIR_POLICY_MISMATCH")
    missing = sorted(role for role in roles if not adapter.has_role(role))
    if missing:
        raise ValueError(
            "BRIDGE_ROUTE_UNAVAILABLE: manifest route could not construct "
            + ", ".join(missing)
        )
    return adapter


def _preflight_focus(harness, manifest, block_refs: list[str], cluster_refs: list[str]):
    """Resolve all operator focus before an unbound run is mutated."""

    from deepreason.scratch.service import ScratchService

    scratch = manifest.scratch_policy
    if scratch is None:
        raise ValueError("BRIDGE_MANIFEST_V3_REQUIRED: scratch policy is missing")
    if not scratch.enabled:
        if block_refs or cluster_refs:
            raise ValueError(
                "BRIDGE_SCRATCH_DISABLED: focus values require scratchpad.enabled"
            )
        return [], []
    service = ScratchService(harness)
    if not service.state.blocks:
        if block_refs or cluster_refs:
            raise ValueError("BRIDGE_SCRATCH_EMPTY: no focus object can be resolved")
        return [], []
    blocks = [service.get_block(value).id for value in block_refs]
    clusters = [service.get_cluster(value).id for value in cluster_refs]
    return blocks, clusters


def _attention_pack(harness, manifest, block_refs: list[str], cluster_refs: list[str]):
    from deepreason.scratch.attention import (
        AttentionPlanner,
        AttentionRequestV1,
    )
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
    request = AttentionRequestV1(
        focus_blocks=blocks or None,
        focus_clusters=clusters or None,
        maximum_blocks=scratch.max_blocks_per_pack,
        maximum_cluster_guides=scratch.max_guides_per_pack,
        deterministic_seed=harness._next_seq,
    )
    pack = planner.plan(request)
    return pack


def _build(args) -> tuple[_BridgeSnapshot, int]:
    from deepreason.harness import Harness
    from deepreason.run_manifest import bind_run_manifest

    root = Path(args.root)
    if not root.is_dir():
        raise ValueError(f"BRIDGE_RUN_NOT_FOUND: {root}")
    block_refs = _bounded_focus(list(args.focus_block), "focus-block")
    cluster_refs = _bounded_focus(list(args.focus_cluster), "focus-cluster")
    # Validate the manifest, run, problem, and focus through a physically
    # read-only view before binding an unbound run or constructing an endpoint.
    manifest = _load_bound_manifest(root, args.run_manifest, bind=False)
    preflight = Harness(root, read_only=True)
    problem_id = _resolve_problem(preflight, args.problem)
    resolved_blocks, resolved_clusters = _preflight_focus(
        preflight, manifest, block_refs, cluster_refs
    )
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    # Adapter/route construction must succeed before an attention receipt says
    # that scratch material was rendered to a model.
    adapter = _build_bridge_adapter(manifest, harness)
    pack = _attention_pack(harness, manifest, resolved_blocks, resolved_clusters)
    policy = manifest.bridge_policy
    terminal = harness.build_bridge(
        problem_id,
        args.target,
        policy.workflow_policy(),
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
    snapshot = _load_snapshot(root, terminal=terminal)
    return snapshot, 0 if terminal.process_status == "success" else 1


def _load_terminal(root: Path) -> BridgeTerminalResultV1:
    try:
        return BridgeTerminalResultV1.model_validate(
            _read_bounded_json(root / BRIDGE_RESULT_NAME)
        )
    except ValueError as error:
        if str(error).startswith("BRIDGE_RECORD_"):
            raise
        raise ValueError("BRIDGE_RESULT_INVALID") from error


def _load_result_manifest(root: Path):
    """Load the exact bound manifest without following fixed-name symlinks."""

    from deepreason.run_manifest import (
        MANIFEST_HASH_NAME,
        MANIFEST_NAME,
        load_run_manifest,
    )

    manifest_path = root / MANIFEST_NAME
    sidecars = (
        root / MANIFEST_HASH_NAME,
        manifest_path.with_suffix(manifest_path.suffix + ".sha256"),
    )
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("BRIDGE_RESULT_MANIFEST_INVALID")
    try:
        if not 2 <= manifest_path.stat().st_size <= _MAX_CONTROL_FILE_BYTES:
            raise ValueError("BRIDGE_RESULT_MANIFEST_INVALID")
        for sidecar in sidecars:
            if sidecar.is_symlink():
                raise ValueError("BRIDGE_RESULT_MANIFEST_INVALID")
            if sidecar.exists() and (
                not sidecar.is_file() or sidecar.stat().st_size > 1_024
            ):
                raise ValueError("BRIDGE_RESULT_MANIFEST_INVALID")
        return load_run_manifest(manifest_path)
    except (OSError, RuntimeError, ValueError) as error:
        if str(error) == "BRIDGE_RESULT_MANIFEST_INVALID":
            raise
        raise ValueError("BRIDGE_RESULT_MANIFEST_INVALID") from error


def _load_snapshot(
    root: Path, *, terminal: BridgeTerminalResultV1 | None = None
) -> _BridgeSnapshot:
    from deepreason.harness import Harness

    terminal = terminal or _load_terminal(root)
    manifest = _load_result_manifest(root)
    if terminal.run_manifest_digest != manifest.sha256:
        raise ValueError("BRIDGE_RESULT_INVALID: manifest digest differs from binding")
    if (
        manifest.schema_version != 3
        or manifest.workload_profile != "text"
        or manifest.bridge_policy is None
        or manifest.bridge_policy.mode != "grounded_two_stage"
    ):
        raise ValueError("BRIDGE_RESULT_INVALID: grounded result requires manifest v3")
    harness = Harness.at(root, terminal.terminal_event_seq)
    state = harness.bridge_state
    replay_events = list(harness.log.read(upto_seq=terminal.terminal_event_seq))
    terminal_event = next(
        (
            event
            for event in replay_events
            if event.seq == terminal.terminal_event_seq
        ),
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
            raise ValueError(
                "BRIDGE_RESULT_INVALID: terminal completion inputs differ from result"
            )
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
        state.validation_reports, terminal.validation_report_id, "validation report"
    )
    review = required(state.grounding_reviews, terminal.review_id, "grounding review")
    failure = required(state.failures, terminal.failure_id, "bridge failure")
    pack = state.evidence_packs.get(terminal.evidence_pack_id)
    if pack is None:
        raise ValueError("BRIDGE_RESULT_INVALID: evidence pack object is absent")
    if pack is not None and (
        pack.problem_ref != terminal.problem_id or pack.formal_seq != terminal.formal_seq
    ):
        raise ValueError("BRIDGE_RESULT_INVALID: evidence-pack fence differs from result")
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
        """Recognize only the harness-authorized quarantine/remove terminal path."""

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
                raise ValueError(
                    "BRIDGE_RESULT_INVALID: successful grounded review is absent"
                )
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
            raise ValueError(
                "BRIDGE_RESULT_INVALID: grounded review names different objects"
            )
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
    return _BridgeSnapshot(
        terminal, harness, ledger, output, report, review, pack, failure
    )


def _unique_short_ids(values) -> dict[str, str]:
    """Return the shortest display prefixes that are unique in this view."""

    ordered = list(dict.fromkeys(value for value in values if value is not None))
    raw = {value: value.removeprefix("sha256:") for value in ordered}
    if not ordered:
        return {}
    maximum = max(len(value) for value in raw.values())
    for width in range(min(_SHORT_ID_LENGTH, maximum), maximum + 1):
        prefixes = {value: body[:width] for value, body in raw.items()}
        if len(set(prefixes.values())) == len(prefixes):
            return prefixes
    return raw


def _model_json(value):
    return (
        value.model_dump(mode="json", by_alias=True, exclude_none=True)
        if value is not None
        else None
    )


def _json_item(value):
    return _model_json(value) if hasattr(value, "model_dump") else value


def _page_bounds(limit: int, offset: int) -> tuple[int, int]:
    if isinstance(limit, bool) or not 1 <= limit <= _MAX_PAGE_LIMIT:
        raise ValueError(
            f"BRIDGE_PAGE_LIMIT_INVALID: --limit must be 1 through {_MAX_PAGE_LIMIT}"
        )
    if isinstance(offset, bool) or not 0 <= offset <= _MAX_PAGE_OFFSET:
        raise ValueError(
            f"BRIDGE_PAGE_OFFSET_INVALID: --offset must be 0 through {_MAX_PAGE_OFFSET}"
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
            offset + len(selected)
            if selected and offset + len(selected) < len(items)
            else None
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
        selected = value[:_MAX_JSON_ARRAY_ITEMS]
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
    if isinstance(value, str) and len(value) > _MAX_JSON_TEXT_CHARS:
        truncated.append(
            {
                "pointer": pointer or "/",
                "original_chars": len(value),
                "returned_chars": _MAX_JSON_TEXT_CHARS,
            }
        )
        return value[:_MAX_JSON_TEXT_CHARS]
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
        "text_limit_chars": _MAX_JSON_TEXT_CHARS,
        "array_limit_items": _MAX_JSON_ARRAY_ITEMS,
        "truncated": bool(truncated),
        "fields": truncated,
    }
    return payload


def _result_payload(
    snapshot: _BridgeSnapshot,
    *,
    limit: int = _DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    limit, offset = _page_bounds(limit, offset)
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
        (
            output,
            snapshot.output,
            "unresolved_items",
            "/output/unresolved_items",
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
    payload = {
        "schema": "deepreason-cli-bridge-result-v1",
        "terminal": _model_json(snapshot.terminal),
        "failure": _model_json(snapshot.failure),
        "claim_ledger": ledger,
        "output": output,
        "validation_report": validation,
        "grounded_review": review,
    }
    return _finish_bounded_payload(
        payload, collections, limit=limit, offset=offset
    )


def _grounding_source_count(ledger) -> int:
    references: set[str] = set()
    for entry in ledger.entries:
        for field in (
            "source_refs",
            "evidence_refs",
            "event_refs",
            "trace_refs",
            "formal_observation_refs",
        ):
            references.update(getattr(entry, field) or ())
    return len(references)


def _render_result(
    snapshot: _BridgeSnapshot,
    *,
    limit: int = _DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> str:
    limit, offset = _page_bounds(limit, offset)
    terminal = snapshot.terminal
    if terminal.process_status == "failure":
        return "\n".join(
            (
                "Bridge failed",
                f"Error: {terminal.error_code}",
                f"Detail: {_safe_human(terminal.error_message)}",
            )
        )
    output = snapshot.output
    ledger = snapshot.ledger
    sections, section_page = _page_values(
        output.sections, limit=limit, offset=offset
    )
    unresolved, unresolved_page = _page_values(
        output.unresolved_items, limit=limit, offset=offset
    )
    prefixes = _unique_short_ids(
        [ledger.id, *(entry.id for entry in ledger.entries)]
    )
    lines = [f"Resolution: {_RESOLUTION_LABELS[output.resolution]}", "", "Answer:"]
    if sections:
        for section in sections:
            refs = ",".join(prefixes[value] for value in section.ledger_entry_ids)
            lines.append(
                f"  [{_MODE_LABELS[section.rendering_mode]} {refs}] "
                f"{_safe_human(section.text)}"
            )
    elif not output.sections:
        lines.append("  [Unknown] No supported answer is available.")
    else:
        lines.append("  (no answer sections on this page)")
    lines.extend(("", "Unresolved items:"))
    if unresolved:
        for item in unresolved:
            suffix = f" — {_safe_human(item.reason)}" if item.reason else ""
            lines.append(f"  - {_safe_human(item.description)}{suffix}")
    elif output.unresolved_items:
        lines.append("  (no unresolved items on this page)")
    elif output.resolution == BridgeResolution.ANSWERED:
        lines.append("  (none)")
    else:
        lines.append(
            "  - "
            + _safe_human(
                output.resolution_reason or "The result remains unresolved."
            )
        )
    lines.extend(
        (
            "",
            f"Grounding sources: {_grounding_source_count(ledger)}",
            f"Claim ledger: {prefixes[ledger.id]}",
            "Inspect claim details with: deepreason --root RUN bridge claims",
            (
                f"Page: offset {offset}, limit {limit}; "
                f"answer sections {section_page['returned']}/{section_page['total']}, "
                f"unresolved items {unresolved_page['returned']}/{unresolved_page['total']}"
            ),
        )
    )
    return "\n".join(lines)


def _claims_payload(
    snapshot: _BridgeSnapshot,
    *,
    limit: int = _DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    limit, offset = _page_bounds(limit, offset)
    ledger = snapshot.ledger
    if ledger is None:
        raise ValueError("BRIDGE_RESULT_HAS_NO_LEDGER")
    entries, entries_page = _page_values(ledger.entries, limit=limit, offset=offset)
    uncovered, uncovered_page = _page_values(
        ledger.uncovered_requirements, limit=limit, offset=offset
    )
    conflicts, conflicts_page = _page_values(
        ledger.source_conflicts, limit=limit, offset=offset
    )
    collections = []
    for pointer, page in (
        ("/entries", entries_page),
        ("/uncovered_requirements", uncovered_page),
        ("/source_conflicts", conflicts_page),
    ):
        collections.append({**page, "pointer": pointer})
    payload = {
        "schema": "deepreason-cli-bridge-claims-v1",
        "claim_ledger_id": ledger.id,
        "problem_id": snapshot.terminal.problem_id,
        "formal_seq": ledger.formal_seq,
        "entries": [_model_json(entry) for entry in entries],
        "uncovered_requirements": [_model_json(item) for item in uncovered],
        "source_conflicts": [_model_json(item) for item in conflicts],
    }
    return _finish_bounded_payload(
        payload, collections, limit=limit, offset=offset
    )


def _render_claims(
    snapshot: _BridgeSnapshot,
    *,
    limit: int = _DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> str:
    limit, offset = _page_bounds(limit, offset)
    ledger = snapshot.ledger
    if ledger is None:
        raise ValueError("BRIDGE_RESULT_HAS_NO_LEDGER")
    entries, entries_page = _page_values(ledger.entries, limit=limit, offset=offset)
    uncovered, uncovered_page = _page_values(
        ledger.uncovered_requirements, limit=limit, offset=offset
    )
    conflicts, conflicts_page = _page_values(
        ledger.source_conflicts, limit=limit, offset=offset
    )
    prefixes = _unique_short_ids([ledger.id, *(entry.id for entry in entries)])
    lines = [
        f"Claim ledger: {prefixes[ledger.id]}",
        (
            f"Claims page: offset {offset}, limit {limit}; "
            f"showing {entries_page['returned']} of {entries_page['total']}"
        ),
    ]
    for entry in entries:
        label = _CLAIM_LABELS[entry.claim_class.value]
        lines.append(
            f"  [{label} {prefixes[entry.id]}] {_safe_human(entry.claim)}"
        )
        if entry.qualification:
            lines.append(f"    Qualification: {_safe_human(entry.qualification)}")
    if uncovered:
        lines.append("Uncovered requirements:")
        for item in uncovered:
            lines.append(f"  - {_safe_human(item.requirement)}")
    if conflicts:
        lines.append(
            f"Source conflicts on page: {conflicts_page['returned']} "
            f"of {conflicts_page['total']}"
        )
    if any(
        page["has_more"]
        for page in (entries_page, uncovered_page, conflicts_page)
    ):
        lines.append(f"More records are available; use --offset {offset + limit}.")
    return "\n".join(lines)


def _inspect_payload(
    snapshot: _BridgeSnapshot,
    *,
    limit: int = _DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> dict[str, Any]:
    limit, offset = _page_bounds(limit, offset)
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
    payload = {
        "schema": "deepreason-cli-bridge-inspect-v1",
        "terminal": _model_json(snapshot.terminal),
        "failure": _model_json(snapshot.failure),
        "evidence_pack": pack,
        "validation_report": validation,
        "grounded_review": review,
    }
    return _finish_bounded_payload(
        payload, collections, limit=limit, offset=offset
    )


def _render_inspect(snapshot: _BridgeSnapshot) -> str:
    terminal = snapshot.terminal
    ids = _unique_short_ids(
        [
            terminal.evidence_pack_id,
            terminal.claim_ledger_id,
            terminal.bridge_output_id,
        ]
    )
    lines = [
        f"Process: {terminal.process_status}",
        f"Problem: {_safe_human(terminal.problem_id, maximum=512)}",
        f"Formal fence: {terminal.formal_seq}",
        f"Evidence pack: {ids.get(terminal.evidence_pack_id, '-')}",
        f"Claim ledger: {ids.get(terminal.claim_ledger_id, '-')}",
        f"Output: {ids.get(terminal.bridge_output_id, '-')}",
    ]
    if snapshot.validation_report is not None:
        lines.append(
            "Deterministic validation: "
            + ("valid" if snapshot.validation_report.valid else "invalid")
        )
    if snapshot.review is not None:
        lines.append(
            "Grounded review: " + ("passed" if snapshot.review.passed else "findings remain")
        )
    return "\n".join(lines)


def _validate_payload(
    snapshot: _BridgeSnapshot,
    *,
    limit: int = _DEFAULT_PAGE_LIMIT,
    offset: int = 0,
) -> tuple[dict[str, Any], bool]:
    from deepreason.bridge.validate import validate_bridge_output, validate_claim_ledger

    limit, offset = _page_bounds(limit, offset)
    if snapshot.ledger is None or snapshot.output is None:
        raise ValueError("BRIDGE_RESULT_HAS_NO_VALIDATABLE_OUTPUT")
    ledger_report = validate_claim_ledger(snapshot.ledger)
    output_report = validate_bridge_output(snapshot.ledger, snapshot.output)
    stored_matches = (
        snapshot.validation_report is not None
        and snapshot.validation_report.id == output_report.id
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
    payload = _finish_bounded_payload(
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
    )
    return (
        payload,
        valid,
    )


def _status_payload(root: Path) -> dict[str, Any]:
    try:
        status = BridgeCLIStatusV1.model_validate(
            _read_bounded_json(root / BRIDGE_STATUS_NAME)
        )
    except ValueError as error:
        if str(error).startswith("BRIDGE_RECORD_"):
            raise
        raise ValueError("BRIDGE_STATUS_INVALID") from error
    payload = status.model_dump(mode="json", by_alias=True, exclude_none=True)
    result_path = root / BRIDGE_RESULT_NAME
    if status.state in {"completed", "failed"}:
        if not result_path.is_file() or result_path.is_symlink():
            raise ValueError("BRIDGE_STATUS_INVALID: terminal result is absent")
        snapshot = _load_snapshot(root)
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
    return payload


def handle_bridge_command(args) -> int:
    """Execute one parsed bridge subcommand using stable process exit codes."""

    try:
        root = Path(args.root)
        command = args.bridge_command
        if command in {"build", "result", "inspect", "claims", "validate"}:
            page_limit, page_offset = _page_bounds(args.limit, args.offset)
        else:
            page_limit, page_offset = _DEFAULT_PAGE_LIMIT, 0
        if command == "build":
            snapshot, exit_code = _build(args)
            output = (
                json.dumps(
                    _result_payload(
                        snapshot, limit=page_limit, offset=page_offset
                    ),
                    indent=2,
                    sort_keys=True,
                )
                if args.json
                else _render_result(
                    snapshot, limit=page_limit, offset=page_offset
                )
            )
        elif command == "status":
            payload = _status_payload(root)
            exit_code = 1 if payload.get("process_status") == "failure" else 0
            if args.json:
                output = json.dumps(payload, indent=2, sort_keys=True)
            else:
                resolution = payload.get("resolution")
                resolution_text = (
                    f" — {_RESOLUTION_LABELS[BridgeResolution(resolution)]}"
                    if resolution
                    else ""
                )
                output = f"Bridge: {payload['state']}{resolution_text}"
                if payload.get("error_code"):
                    output += f"\nError: {payload['error_code']}"
        else:
            snapshot = _load_snapshot(root)
            if command == "result":
                payload = _result_payload(
                    snapshot, limit=page_limit, offset=page_offset
                )
                output = (
                    json.dumps(payload, indent=2, sort_keys=True)
                    if args.json
                    else _render_result(
                        snapshot, limit=page_limit, offset=page_offset
                    )
                )
                exit_code = 0 if snapshot.terminal.process_status == "success" else 1
            elif command == "inspect":
                payload = _inspect_payload(
                    snapshot, limit=page_limit, offset=page_offset
                )
                output = (
                    json.dumps(payload, indent=2, sort_keys=True)
                    if args.json
                    else _render_inspect(snapshot)
                )
                exit_code = 0 if snapshot.terminal.process_status == "success" else 1
            elif command == "claims":
                payload = _claims_payload(
                    snapshot, limit=page_limit, offset=page_offset
                )
                output = (
                    json.dumps(payload, indent=2, sort_keys=True)
                    if args.json
                    else _render_claims(
                        snapshot, limit=page_limit, offset=page_offset
                    )
                )
                exit_code = 0
            elif command == "validate":
                payload, valid = _validate_payload(
                    snapshot, limit=page_limit, offset=page_offset
                )
                output = (
                    json.dumps(payload, indent=2, sort_keys=True)
                    if args.json
                    else (
                        "Bridge validation: valid"
                        if valid
                        else "Bridge validation: invalid"
                    )
                )
                exit_code = 0 if valid else 1
            else:  # pragma: no cover - argparse owns the finite command set
                raise ValueError(f"unknown bridge command: {command}")
        print(output)
        return exit_code
    except (KeyError, OSError, ValueError) as error:
        print(_safe_human(error, maximum=2_048), file=sys.stderr)
        return 1


dispatch_bridge = handle_bridge_command
run_command = handle_bridge_command


__all__ = [
    "BridgeCLIStatusV1",
    "add_bridge_parser",
    "dispatch_bridge",
    "handle_bridge_command",
    "register_parser",
    "register_bridge_commands",
    "run_command",
]
