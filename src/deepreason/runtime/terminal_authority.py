"""Root-local terminal commitment construction and exact-once recovery."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.locking import ProcessLock
from deepreason.runtime.stop import validate_stop_record
from deepreason.runtime.progress import _atomic_json
from deepreason.workflow.models import (
    RunTerminalCommitmentV1,
    RunTerminalResultDraftV1,
)


_TERMINAL_COMMITMENT_LOCK_NAME = ".terminal-commitment.lock"
_REPLAY_VALIDATION_NAME = "REPLAY_VALIDATION.json"
_RESULT_PROJECTION_FIELDS = frozenset(
    {
        "verification",
        "completion_status",
        "canonical_bridge_eligible",
    }
)


class TerminalReplayValidationBindingV1(BaseModel):
    """Derived binding from replay validation to one committed terminal head."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_: Literal["terminal-replay-validation-binding.v1"] = Field(
        "terminal-replay-validation-binding.v1", alias="schema"
    )
    run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    terminal_epoch: int = Field(ge=0)
    terminal_commitment_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    result_draft_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    parent_terminal_commitment_ref: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    opening_resume_ref: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    terminal_commitment_event_seq: int = Field(ge=0)
    reasoning_event_horizon_seq: int = Field(ge=0)
    evaluated_event_horizon_seq: int = Field(ge=0)
    terminal_commitment_ledger_digest: str = Field(
        pattern=r"^sha256:[0-9a-f]{64}$"
    )
    stop_record_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    replay_validation_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    result_projection_digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _binding_shape(self):
        if self.run_id != self.manifest_digest:
            raise ValueError("terminal replay binding names another run")
        if self.evaluated_event_horizon_seq < self.terminal_commitment_event_seq:
            raise ValueError("terminal replay binding excludes its commitment event")
        parent_bound = self.parent_terminal_commitment_ref is not None
        resume_bound = self.opening_resume_ref is not None
        if self.terminal_epoch == 0:
            if parent_bound or resume_bound:
                raise ValueError("epoch zero replay binding cannot name a predecessor")
        elif not parent_bound or not resume_bound:
            raise ValueError("resumed replay binding requires predecessor and resume")
        return self


class TerminalAuthorityDerivationV1(BaseModel):
    """Read-only projection of one root's terminal authority.

    This is deliberately not a persisted receipt.  It is the single consumer
    boundary used by verification and canonical bridge preflight to interpret
    the manifest-owned commitment ledger.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_: Literal["terminal-authority-derivation.v1"] = Field(
        "terminal-authority-derivation.v1", alias="schema"
    )
    status: Literal[
        "current_valid_committed",
        "current_open_uncommitted",
        "historical_read_only",
        "operational_abort",
        "invalid_incomplete",
    ]
    manifest_sha256: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    terminal_epoch: int | None = Field(default=None, ge=0)
    terminal_status: Literal["completed", "cancelled", "failed"] | None = None
    canonical_bridge_eligible: bool | None = None
    terminal_commitment_ref: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    result_draft_ref: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    reasoning_event_horizon_seq: int | None = Field(default=None, ge=0)
    terminal_commitment_event_seq: int | None = Field(default=None, ge=0)
    stop_record_digest: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    detail_code: str | None = Field(
        default=None, pattern=r"^[A-Z][A-Z0-9_]{0,127}$"
    )

    @model_validator(mode="after")
    def _authority_shape(self):
        bound = (
            self.terminal_epoch,
            self.terminal_status,
            self.canonical_bridge_eligible,
            self.terminal_commitment_ref,
            self.result_draft_ref,
            self.reasoning_event_horizon_seq,
            self.terminal_commitment_event_seq,
            self.stop_record_digest,
        )
        if self.status == "current_valid_committed":
            if self.manifest_sha256 is None or any(value is None for value in bound):
                raise ValueError("valid terminal authority requires complete identity")
            if self.detail_code is not None:
                raise ValueError("valid terminal authority cannot carry a failure code")
        elif any(value is not None for value in bound):
            raise ValueError("non-authoritative terminal projection cannot grant identity")
        return self

    @property
    def current_valid(self) -> bool:
        return self.status == "current_valid_committed"


def _terminal_projection(
    status: str,
    *,
    manifest_sha256: str | None = None,
    detail_code: str | None = None,
    **values: Any,
) -> TerminalAuthorityDerivationV1:
    return TerminalAuthorityDerivationV1(
        status=status,
        manifest_sha256=manifest_sha256,
        detail_code=detail_code,
        **values,
    )


def _read_current_result(root: Path) -> dict[str, Any] | None:
    path = root / "run-result.json"
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(observed.st_mode) or observed.st_size > 4 * 1024 * 1024:
        raise ValueError("TERMINAL_RESULT_UNSAFE")
    try:
        raw = path.read_bytes()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("TERMINAL_RESULT_INVALID") from error
    if not isinstance(payload, dict):
        raise ValueError("TERMINAL_RESULT_INVALID")
    if raw != canonical_json(payload) + b"\n":
        raise ValueError("TERMINAL_RESULT_NONCANONICAL")
    return payload


def _result_without_projection(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in _RESULT_PROJECTION_FIELDS
    }


def _result_projection(payload: dict[str, Any]) -> dict[str, Any]:
    if not _RESULT_PROJECTION_FIELDS <= payload.keys():
        raise ValueError("TERMINAL_RESULT_PROJECTION_INCOMPLETE")
    return {
        key: payload[key]
        for key in (
            "verification",
            "completion_status",
            "canonical_bridge_eligible",
        )
    }


def _result_projection_digest(payload: dict[str, Any]) -> str:
    return sha256_hex(canonical_json(_result_projection(payload)))


def _pending_terminal_result(expected: dict[str, Any]) -> dict[str, Any]:
    """Return one deterministic fail-closed projection over an immutable draft."""

    verification = dict(expected["verification"])
    counts = dict(verification["finding_counts"])
    counts["integrity"] = max(1, int(counts["integrity"]))
    verification.update(
        {
            "valid": False,
            "integrity_valid": False,
            "finding_counts": counts,
        }
    )
    pending = {
        **expected,
        "verification": verification,
        "completion_status": (
            "satisfied"
            if verification["completion_satisfied"]
            else "incomplete"
        ),
        "canonical_bridge_eligible": False,
    }
    from deepreason.application.models import RunResultV2

    return RunResultV2.model_validate(pending).model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )


def _read_replay_validation(root: Path) -> dict[str, Any] | None:
    path = root / _REPLAY_VALIDATION_NAME
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return None
    if (
        not stat.S_ISREG(observed.st_mode)
        or observed.st_size < 2
        or observed.st_size > 16 * 1024 * 1024
    ):
        raise ValueError("TERMINAL_REPLAY_VALIDATION_UNSAFE")
    try:
        raw = path.read_bytes()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("TERMINAL_REPLAY_VALIDATION_INVALID") from error
    if not isinstance(payload, dict) or raw not in {
        canonical_json(payload),
        canonical_json(payload) + b"\n",
    }:
        raise ValueError("TERMINAL_REPLAY_VALIDATION_NONCANONICAL")
    return payload


def _public_terminal_projection_required(draft: RunTerminalResultDraftV1) -> bool:
    """Identify public text terminals whose audit report must be post-commit."""

    body = draft.result_body
    return (
        isinstance(body.get("capability_audits"), dict)
        or body.get("workload") == "text"
        and isinstance(body.get("error_type"), str)
    )


def _same_epoch_commitment_objects(harness, manifest, epoch: int):
    directory = Path(harness.objects.root) / "workflow-run-terminal-commitment-v1"
    try:
        observed = directory.lstat()
    except FileNotFoundError:
        return ()
    if not stat.S_ISDIR(observed.st_mode):
        raise ValueError("TERMINAL_COMMITMENT_OBJECT_DIRECTORY_UNSAFE")
    found = []
    for path in sorted(directory.glob("*.json")):
        schema, value, _record = harness.objects._read_record(path)
        if schema != "workflow-run-terminal-commitment-v1":
            raise ValueError("TERMINAL_COMMITMENT_OBJECT_SCHEMA_MISMATCH")
        if (
            value.manifest_sha256 == manifest.sha256
            and value.run_id == manifest.sha256
            and value.terminal_epoch == epoch
        ):
            found.append(value)
    return tuple(found)


def _validate_commitment_checkpoint(root: Path, harness, commitment) -> None:
    path = root / "workflow-checkpoint.json"
    try:
        observed = path.lstat()
    except FileNotFoundError as error:
        raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_REQUIRED") from error
    if not stat.S_ISREG(observed.st_mode):
        raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_UNSAFE")
    harness._verify_workflow_checkpoint()
    try:
        payload = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_INVALID") from error
    event_seq = harness.workflow_state.terminal_commitment_event_seq.get(commitment.id)
    if (
        type(payload.get("last_control_seq")) is not int
        or payload["last_control_seq"] < event_seq
        or payload.get("terminal_commitment_ledger_digest")
        != harness.workflow_state.terminal_commitment_ledger_digest
    ):
        raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_MISMATCH")


def _replay_validation_base(payload: dict[str, Any]) -> dict[str, Any]:
    base = {
        key: value
        for key, value in payload.items()
        if key != "terminal_binding"
    }
    if set(base) != {
        "schema",
        "manifest_digest",
        "workflow_process_digest",
        "capability_process_digest",
        "valid",
        "verification",
    }:
        raise ValueError("TERMINAL_REPLAY_VALIDATION_SHAPE_INVALID")
    if base.get("schema") != "replay-validation.v1":
        raise ValueError("TERMINAL_REPLAY_VALIDATION_SCHEMA_INVALID")
    verification = base.get("verification")
    if not isinstance(verification, dict):
        raise ValueError("TERMINAL_REPLAY_VALIDATION_REPORT_INVALID")
    violations = verification.get("violations")
    if not isinstance(violations, list) or base.get("valid") is not (
        not violations
    ):
        raise ValueError("TERMINAL_REPLAY_VALIDATION_VALIDITY_MISMATCH")
    return base


def _evaluated_replay_horizon(
    harness,
    manifest,
    commitment,
    replay_validation: dict[str, Any],
) -> int:
    base = _replay_validation_base(replay_validation)
    verification = base["verification"]
    stats = verification.get("stats")
    process = stats.get("process") if isinstance(stats, dict) else None
    events = stats.get("events") if isinstance(stats, dict) else None
    durable_events = tuple(harness.log.read())
    if (
        base.get("manifest_digest") != manifest.sha256
        or not isinstance(process, dict)
        or process.get("manifest_sha256") != manifest.sha256
        or base.get("workflow_process_digest")
        != stats.get("workflow_process_digest")
        or base.get("capability_process_digest")
        != stats.get("capability_process_digest")
        or type(events) is not int
        or events < 1
        or events > len(durable_events)
    ):
        raise ValueError("TERMINAL_REPLAY_VALIDATION_AUTHORITY_MISMATCH")
    if events == len(durable_events) and (
        base.get("workflow_process_digest") != harness.workflow_state.digest
        or base.get("capability_process_digest") != harness.capability_state.digest
    ):
        raise ValueError("TERMINAL_REPLAY_VALIDATION_PROCESS_MISMATCH")
    evaluated = events - 1
    commitment_seq = harness.workflow_state.terminal_commitment_event_seq.get(
        commitment.id
    )
    if (
        commitment_seq is None
        or evaluated < commitment_seq
        or evaluated >= len(durable_events)
    ):
        raise ValueError("TERMINAL_REPLAY_VALIDATION_HORIZON_MISMATCH")
    return evaluated


def _expected_replay_binding(
    harness,
    manifest,
    commitment,
    replay_validation: dict[str, Any],
    result: dict[str, Any],
) -> TerminalReplayValidationBindingV1:
    evaluated = _evaluated_replay_horizon(
        harness,
        manifest,
        commitment,
        replay_validation,
    )
    return TerminalReplayValidationBindingV1(
        run_id=commitment.run_id,
        manifest_digest=manifest.sha256,
        terminal_epoch=commitment.terminal_epoch,
        terminal_commitment_ref=commitment.id,
        result_draft_ref=commitment.result_draft_ref,
        parent_terminal_commitment_ref=(
            commitment.parent_terminal_commitment_ref
        ),
        opening_resume_ref=commitment.opening_resume_ref,
        terminal_commitment_event_seq=(
            harness.workflow_state.terminal_commitment_event_seq[commitment.id]
        ),
        reasoning_event_horizon_seq=commitment.reasoning_event_horizon_seq,
        evaluated_event_horizon_seq=evaluated,
        terminal_commitment_ledger_digest=(
            harness.workflow_state.terminal_commitment_ledger_digest
        ),
        stop_record_digest=commitment.stop_record_digest,
        replay_validation_digest=sha256_hex(
            canonical_json(_replay_validation_base(replay_validation))
        ),
        result_projection_digest=_result_projection_digest(result),
    )


def _validate_result_projection_binding(
    harness,
    manifest,
    commitment,
    result: dict[str, Any],
) -> None:
    replay_validation = _read_replay_validation(Path(harness.root))
    if replay_validation is None:
        raise ValueError("TERMINAL_REPLAY_VALIDATION_REQUIRED")
    try:
        observed = TerminalReplayValidationBindingV1.model_validate(
            replay_validation.get("terminal_binding")
        )
        expected = _expected_replay_binding(
            harness,
            manifest,
            commitment,
            replay_validation,
            result,
        )
    except (TypeError, ValueError) as error:
        raise ValueError("TERMINAL_REPLAY_VALIDATION_BINDING_INVALID") from error
    if observed != expected:
        raise ValueError("TERMINAL_REPLAY_VALIDATION_BINDING_MISMATCH")


def is_commitment_bound_bridge_work(
    workflow_state,
    preparation,
    commitment_ref: str,
    *,
    seen: frozenset[str] = frozenset(),
) -> bool:
    """Return whether one work item is an exact descendant of a terminal bridge."""

    if preparation.id in seen or preparation.source_terminal_commitment_ref != commitment_ref:
        return False
    payload = preparation.task_payload_value
    if not isinstance(payload, dict):
        return False
    schema = payload.get("schema")
    task_by_template = {
        "bridge_ledger": "bridge_ledger",
        "bridge_compose": "bridge_composition",
        "bridge_review": "bridge_review",
        "bridge_grounding_repair": "repair",
    }
    template_role = payload.get("template_role")
    exact_bridge_call = (
        payload.get("source_terminal_commitment_ref") == commitment_ref
        and payload.get("contract_id") == preparation.contract_id
        and payload.get("role") == preparation.route_lease.role
        and payload.get("seat") == preparation.route_lease.seat
        and task_by_template.get(template_role)
        == getattr(preparation.task_kind, "value", preparation.task_kind)
    )
    if schema == "bridge.transaction-task.v1":
        return exact_bridge_call
    if schema in {
        "bridge.transaction-task.v2",
        "contract-decomposition-child.v1",
    }:
        return (
            exact_bridge_call
            and isinstance(payload.get("execution_id"), str)
            and bool(payload["execution_id"])
            and isinstance(payload.get("execution_snapshot_ref"), str)
            and bool(payload["execution_snapshot_ref"])
        )
    if schema != "repair.semantic-task.v1":
        return False
    parent_id = payload.get("parent_work_id")
    parent = workflow_state.transaction_work.get(parent_id)
    return parent is not None and is_commitment_bound_bridge_work(
        workflow_state,
        parent.preparation,
        commitment_ref,
        seen=seen | {preparation.id},
    )


def _validate_post_terminal_descendants(harness, commitment) -> None:
    from deepreason.bridge.state import validate_terminal_bridge_history
    from deepreason.ontology.event import Rule

    events = tuple(harness.log.read())
    transaction_work = harness.workflow_state.transaction_work

    def commitment_bound_bridge_work(item) -> bool:
        return is_commitment_bound_bridge_work(
            harness.workflow_state,
            item.preparation,
            commitment.id,
        )

    commitment_seq = harness.workflow_state.terminal_commitment_event_seq.get(
        commitment.id
    )
    try:
        validate_terminal_bridge_history(
            events=events,
            objects=harness.objects,
            workflow_state=harness.workflow_state,
            commitment_ref=commitment.id,
            horizon_seq=commitment.reasoning_event_horizon_seq,
        )
    except ValueError as error:
        if str(error).startswith("TERMINAL_"):
            raise
        raise ValueError("TERMINAL_POST_HORIZON_BRIDGE_INVALID") from error
    for event in events:
        if event.seq <= commitment.reasoning_event_horizon_seq:
            continue
        control = getattr(event, "control", None)
        if event.seq == commitment_seq:
            if (
                event.rule != Rule.CONTROL
                or getattr(control, "action", None) != "terminal_committed"
                or getattr(control, "decision_ref", None) != commitment.id
                or tuple(event.outputs)[-1:] != (commitment.id,)
            ):
                raise ValueError("TERMINAL_COMMITMENT_EVENT_MISMATCH")
            continue
        if event.rule == Rule.BRIDGE:
            if event.bridge is None:
                raise ValueError("TERMINAL_POST_HORIZON_BRIDGE_INVALID")
            continue
        if event.rule == Rule.CONTROL:
            matching = [
                item
                for item in harness.workflow_state.transaction_work.values()
                if event.seq in item.event_seqs
            ]
            if (
                len(matching) == 1
                and commitment_bound_bridge_work(matching[0])
            ):
                continue
            action = getattr(control, "action", None)
            decision_ref = getattr(control, "decision_ref", None)
            if action == "contract_decomposition_activated":
                transitions = [
                    transition
                    for transition in harness.workflow_state.contract_decomposition_by_source_work.values()
                    if transition.id == decision_ref
                    and harness.workflow_state.contract_decomposition_event_seq.get(
                        transition.id
                    )
                    == event.seq
                ]
                if len(transitions) == 1:
                    source = transaction_work.get(transitions[0].source_work_id)
                    if source is not None and commitment_bound_bridge_work(source):
                        continue
            if action == "contract_decomposition_completed":
                completions = [
                    completion
                    for completion in harness.workflow_state.contract_decomposition_completion_by_transition.values()
                    if completion.id == decision_ref
                ]
                if len(completions) == 1:
                    source = transaction_work.get(completions[0].source_work_id)
                    if source is not None and commitment_bound_bridge_work(source):
                        continue
        raise ValueError("TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED")


def derive_terminal_authority(
    root: Path | str,
    *,
    manifest: Any | None = None,
    result_payload: dict[str, Any] | None = None,
) -> TerminalAuthorityDerivationV1:
    """Derive terminal authority without mutating the root.

    Optional result fields never decide whether authority is required.  That
    decision comes only from the canonical bound manifest's frozen policy.
    """

    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    root = Path(root)
    manifest_sha256 = getattr(manifest, "sha256", None)
    if getattr(manifest, "schema_version", None) != 6:
        return _terminal_projection(
            "historical_read_only", manifest_sha256=manifest_sha256
        )
    if getattr(manifest, "terminal_commitment_policy", None) is None:
        return _terminal_projection(
            "historical_read_only", manifest_sha256=manifest_sha256
        )
    try:
        bound = load_run_manifest(root / MANIFEST_NAME)
        if bound.sha256 != manifest.sha256:
            raise ValueError("TERMINAL_MANIFEST_MISMATCH")
        from deepreason.harness import Harness

        harness = Harness(root, read_only=True)
        durable_payload = _read_current_result(root)
        if result_payload is not None and result_payload != durable_payload:
            raise ValueError("TERMINAL_RESULT_VIEW_MISMATCH")
        payload = durable_payload
        current = harness.workflow_state.current_terminal_commitment
        if current is None:
            if payload is None:
                return _terminal_projection(
                    "current_open_uncommitted", manifest_sha256=manifest.sha256
                )
            no_process_history = not tuple(harness.log.read())
            if payload.get("state") == "failed" and no_process_history:
                return _terminal_projection(
                    "operational_abort", manifest_sha256=manifest.sha256
                )
            raise ValueError("TERMINAL_COMMITMENT_REQUIRED")
        if payload is None:
            raise ValueError("TERMINAL_RESULT_REQUIRED")

        from deepreason.application.models import RunResultV2

        result = RunResultV2.model_validate(payload).model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
        same_epoch = _same_epoch_commitment_objects(
            harness, manifest, current.terminal_epoch
        )
        if len(same_epoch) != 1 or same_epoch[0].id != current.id:
            raise ValueError("TERMINAL_COMMITMENT_OBJECT_AMBIGUOUS")
        schema, draft = harness.objects.get(
            current.result_draft_ref,
            schema="workflow-run-terminal-result-draft-v1",
        )
        if schema != "workflow-run-terminal-result-draft-v1" or not isinstance(
            draft, RunTerminalResultDraftV1
        ):
            raise ValueError("TERMINAL_RESULT_DRAFT_REQUIRED")
        expected_result = {
            **dict(draft.result_body),
            "terminal_commitment_ref": current.id,
        }
        expected_result = RunResultV2.model_validate(expected_result).model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
        if _result_without_projection(result) != _result_without_projection(
            expected_result
        ):
            raise ValueError("TERMINAL_RESULT_DRAFT_MISMATCH")
        pending_result = _pending_terminal_result(expected_result)
        if result == pending_result:
            pass
        elif (
            result == expected_result
            and not _public_terminal_projection_required(draft)
        ):
            # Historical and lower-level callers did not own the public audit
            # projection.  Preserve their exact draft-plus-reference contract.
            pass
        else:
            _validate_result_projection_binding(
                harness,
                manifest,
                current,
                result,
            )
        stop = validate_stop_record(dict(result["stop"]))
        pointer = root / "run-stop.json"
        observed = pointer.lstat()
        if not stat.S_ISREG(observed.st_mode):
            raise ValueError("TERMINAL_STOP_POINTER_UNSAFE")
        if pointer.read_bytes() != canonical_json(stop) + b"\n":
            raise ValueError("TERMINAL_STOP_POINTER_MISMATCH")
        if (
            result.get("terminal_commitment_ref") != current.id
            or result.get("state") != current.terminal_status
            or result["model_execution"].get("event_horizon_seq")
            != current.reasoning_event_horizon_seq
            or stop["event_seq"] != current.reasoning_event_horizon_seq
            or stop["digest"] != current.stop_record_digest
        ):
            raise ValueError("TERMINAL_RESULT_AUTHORITY_MISMATCH")
        _validate_commitment_checkpoint(root, harness, current)
        _validate_post_terminal_descendants(harness, current)
        return _terminal_projection(
            "current_valid_committed",
            manifest_sha256=manifest.sha256,
            terminal_epoch=current.terminal_epoch,
            terminal_status=current.terminal_status,
            canonical_bridge_eligible=result["canonical_bridge_eligible"],
            terminal_commitment_ref=current.id,
            result_draft_ref=current.result_draft_ref,
            reasoning_event_horizon_seq=current.reasoning_event_horizon_seq,
            terminal_commitment_event_seq=(
                harness.workflow_state.terminal_commitment_event_seq[current.id]
            ),
            stop_record_digest=current.stop_record_digest,
        )
    except Exception as error:  # one typed, non-authoritative failure projection
        code = str(error).split(":", 1)[0]
        if not code or not code.replace("_", "").isalnum() or not code.isupper():
            code = "TERMINAL_AUTHORITY_INVALID"
        return _terminal_projection(
            "invalid_incomplete",
            manifest_sha256=manifest_sha256,
            detail_code=code[:128],
        )


def validate_application_stop_source(
    inputs: Any,
    stop: dict[str, Any],
    *,
    event_seq: int,
) -> None:
    """Bind one application stop to its exact ordered durable source inputs."""

    stop = validate_stop_record(stop)
    if event_seq != stop["event_seq"]:
        raise ValueError("TERMINAL_APPLICATION_STOP_SEQUENCE_MISMATCH")
    metrics_json = json.dumps(stop["metrics"], sort_keys=True)
    try:
        parsed_metrics = json.loads(metrics_json)
    except json.JSONDecodeError as error:  # pragma: no cover - typed stop prevents it
        raise ValueError("TERMINAL_APPLICATION_STOP_METRICS_INVALID") from error
    if parsed_metrics != stop["metrics"] or json.dumps(
        parsed_metrics, sort_keys=True
    ) != metrics_json:
        raise ValueError("TERMINAL_APPLICATION_STOP_METRICS_NONCANONICAL")
    expected = (
        "run-stop",
        stop["policy_digest"],
        metrics_json,
        stop["reason"],
        str(stop["event_seq"]),
    )
    if not isinstance(inputs, (tuple, list)) or tuple(inputs) != expected:
        raise ValueError("TERMINAL_APPLICATION_STOP_SOURCE_MISMATCH")


def _terminal_commitment_lock(harness) -> ProcessLock:
    return ProcessLock(
        Path(harness.root) / _TERMINAL_COMMITMENT_LOCK_NAME,
        owner="terminal-commitment",
        blocking=True,
    )


def model_execution_summary_digest(summary: BaseModel | dict[str, Any]) -> str:
    """Digest the exact alias-aware terminal execution projection."""

    payload = (
        summary.model_dump(mode="json", by_alias=True, exclude_none=True)
        if isinstance(summary, BaseModel)
        else summary
    )
    if not isinstance(payload, dict):
        raise ValueError("terminal model-execution summary must be an object")
    return sha256_hex(canonical_json(payload))


def _validate_stop_history(root: Path, stop: dict[str, Any]) -> None:
    path = root / "run-stops" / (
        f"{stop['event_seq']:012d}-{stop['digest']}.json"
    )
    try:
        data = path.read_bytes()
        loaded = json.loads(data)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("TERMINAL_STOP_OBJECT_REQUIRED") from error
    expected = canonical_json(stop)
    if data not in {expected, expected + b"\n", expected + b"\r\n"}:
        raise ValueError("TERMINAL_STOP_OBJECT_NONCANONICAL")
    if validate_stop_record(loaded) != stop:
        raise ValueError("TERMINAL_STOP_OBJECT_MISMATCH")


def validate_terminal_commitment_storage(root: Path | str, workflow_state) -> None:
    """Validate every latched commitment's immutable local stop object."""

    root = Path(root)
    for epoch, commitment in sorted(
        workflow_state.terminal_commitments_by_epoch.items()
    ):
        if commitment.terminal_epoch != epoch:
            raise ValueError("TERMINAL_COMMITMENT_EPOCH_MISMATCH")
        path = root / commitment.stop_record_ref
        try:
            loaded = json.loads(path.read_bytes())
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("TERMINAL_STOP_OBJECT_REQUIRED") from error
        stop = validate_stop_record(loaded)
        if (
            stop["event_seq"] != commitment.reasoning_event_horizon_seq
            or stop["digest"] != commitment.stop_record_digest
            or stop["reason"] != commitment.stop_reason
        ):
            raise ValueError("TERMINAL_STOP_OBJECT_MISMATCH")
        _validate_stop_history(root, stop)


def _expected_commitment(
    harness,
    manifest,
    *,
    terminal_status: Literal["completed", "cancelled", "failed"],
    stop: dict[str, Any],
    model_execution: BaseModel | dict[str, Any],
    result_body: dict[str, Any],
    commitment_event_seq: int,
) -> tuple[RunTerminalResultDraftV1, RunTerminalCommitmentV1]:
    stop = validate_stop_record(stop)
    _validate_stop_history(Path(harness.root), stop)
    summary_payload = (
        model_execution.model_dump(mode="json", by_alias=True, exclude_none=True)
        if isinstance(model_execution, BaseModel)
        else model_execution
    )
    if not isinstance(summary_payload, dict):
        raise ValueError("terminal model-execution summary must be an object")
    if summary_payload.get("event_horizon_seq") != stop["event_seq"]:
        raise ValueError("terminal summary horizon differs from its stop")

    state = harness.workflow_state
    epoch = state.current_terminal_epoch
    terminal = state.terminal_lifecycle_decision
    if (
        terminal is not None
        and terminal.stop_event_seq == stop["event_seq"]
        and terminal.stop_record_digest == stop["digest"]
    ):
        terminal_source = "workflow_lifecycle"
        lifecycle_ref = terminal.id
        if terminal.deterministic_decision.reason != stop["reason"]:
            raise ValueError("terminal lifecycle reason differs from its stop")
    else:
        terminal_source = "application_terminal"
        lifecycle_ref = None
        inputs = state.event_inputs_by_seq.get(stop["event_seq"])
        validate_application_stop_source(
            inputs,
            stop,
            event_seq=stop["event_seq"],
        )

    parent = state.terminal_commitments_by_epoch.get(epoch - 1) if epoch else None
    opening_resume_ref = state.terminal_epoch_opening_resume_ref.get(epoch)
    draft = RunTerminalResultDraftV1.create(
        manifest_sha256=manifest.sha256,
        run_id=manifest.sha256,
        terminal_epoch=epoch,
        result_body=result_body,
    )
    commitment = RunTerminalCommitmentV1.create(
        manifest_sha256=manifest.sha256,
        run_id=manifest.sha256,
        terminal_epoch=epoch,
        parent_terminal_commitment_ref=parent.id if parent is not None else None,
        opening_resume_ref=opening_resume_ref,
        terminal_status=terminal_status,
        stop_reason=stop["reason"],
        reasoning_event_horizon_seq=stop["event_seq"],
        stop_record_digest=stop["digest"],
        stop_record_ref=(
            "run-stops/"
            f"{stop['event_seq']:012d}-{stop['digest']}.json"
        ),
        terminal_source=terminal_source,
        lifecycle_decision_ref=lifecycle_ref,
        terminal_source_event_seq=stop["event_seq"],
        model_execution_summary_digest=model_execution_summary_digest(
            summary_payload
        ),
        result_draft_ref=draft.id,
        expected_commitment_event_seq=commitment_event_seq,
        allowed_post_terminal="exact_commitment_bound_descendants",
    )
    return draft, commitment


def _current_epoch_orphans(harness, manifest) -> tuple[RunTerminalCommitmentV1, ...]:
    """Resolve unlatched commitment objects through the canonical object reader."""

    directory = (
        Path(harness.objects.root) / "workflow-run-terminal-commitment-v1"
    )
    if not directory.exists():
        return ()
    latched = {
        item.id for item in harness.workflow_state.terminal_commitments_by_epoch.values()
    }
    found: list[RunTerminalCommitmentV1] = []
    for path in sorted(directory.glob("*.json")):
        schema, value, _record = harness.objects._read_record(path)
        if schema != "workflow-run-terminal-commitment-v1":
            raise ValueError("TERMINAL_COMMITMENT_OBJECT_SCHEMA_MISMATCH")
        assert isinstance(value, RunTerminalCommitmentV1)
        if value.id in latched:
            continue
        if (
            value.manifest_sha256 == manifest.sha256
            and value.run_id == manifest.sha256
            and value.terminal_epoch
            == harness.workflow_state.current_terminal_epoch
        ):
            found.append(value)
    return tuple(found)


def ensure_terminal_commitment(
    harness,
    manifest,
    *,
    terminal_status: Literal["completed", "cancelled", "failed"],
    stop: dict[str, Any],
    model_execution: BaseModel | dict[str, Any],
    result_body: dict[str, Any],
) -> RunTerminalCommitmentV1 | None:
    """Create or recover the exact current-epoch terminal commitment once.

    Historical policy-absent manifests remain readable and acquire no inferred
    authority. Content-addressed object persistence may precede the event; an
    orphan can only be reused when its complete deterministic payload matches.
    """

    if getattr(manifest, "schema_version", None) != 6:
        return None
    policy = getattr(manifest, "terminal_commitment_policy", None)
    if policy is None:
        return None
    with _terminal_commitment_lock(harness):
        harness.reload_durable_authority()
        bound = getattr(harness.workflow_state, "_run_manifest", None)
        if bound is None or bound.sha256 != manifest.sha256:
            raise ValueError("TERMINAL_COMMITMENT_MANIFEST_MISMATCH")

        existing = harness.workflow_state.current_terminal_commitment
        event_seq = (
            harness.workflow_state.terminal_commitment_event_seq[existing.id]
            if existing is not None
            else harness._next_seq
        )
        expected_draft, expected = _expected_commitment(
            harness,
            manifest,
            terminal_status=terminal_status,
            stop=stop,
            model_execution=model_execution,
            result_body=result_body,
            commitment_event_seq=event_seq,
        )
        if existing is not None:
            if existing != expected:
                raise ValueError("TERMINAL_COMMITMENT_CONFLICT")
            _seal_terminal_commitment_checkpoint(harness, manifest, existing)
            _write_generic_terminal_checkpoint(harness, manifest, stop)
            return existing

        orphans = _current_epoch_orphans(harness, manifest)
        if len(orphans) > 1:
            raise ValueError("TERMINAL_COMMITMENT_ORPHAN_AMBIGUOUS")
        if orphans and orphans[0] != expected:
            raise ValueError("TERMINAL_COMMITMENT_ORPHAN_CONFLICT")

        event = harness.record_terminal_commitment(expected, expected_draft)
        if event.seq != expected.expected_commitment_event_seq:
            raise RuntimeError("terminal commitment crossed its declared event fence")
        _seal_terminal_commitment_checkpoint(harness, manifest, expected)
        _write_generic_terminal_checkpoint(harness, manifest, stop)
        return expected


def _write_generic_terminal_checkpoint(harness, manifest, stop: dict[str, Any]) -> None:
    _atomic_json(
        Path(harness.root) / "checkpoint.json",
        {
            "schema": "deepreason-checkpoint-v1",
            "manifest_digest": manifest.sha256,
            "stop_digest": stop["digest"],
            "event_seq": harness._next_seq,
        },
    )


def _seal_terminal_commitment_checkpoint(harness, manifest, commitment) -> None:
    """Idempotently seal the replayed terminal ledger before result publication."""

    state = harness.workflow_state
    current = state.current_terminal_commitment
    if current is None or current.id != commitment.id:
        raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_AUTHORITY_MISMATCH")
    bound = getattr(state, "_run_manifest", None)
    if bound is None or bound.sha256 != manifest.sha256:
        raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_MANIFEST_MISMATCH")
    event_seq = state.terminal_commitment_event_seq.get(commitment.id)
    if event_seq != commitment.expected_commitment_event_seq:
        raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_EVENT_MISMATCH")

    path = Path(harness.root) / "workflow-checkpoint.json"
    try:
        observed = path.lstat()
    except FileNotFoundError:
        observed = None
    if observed is not None:
        if not stat.S_ISREG(observed.st_mode):
            raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_UNSAFE")
        harness._verify_workflow_checkpoint()
        payload = json.loads(path.read_bytes())
        checkpoint_seq = payload["last_control_seq"]
        if checkpoint_seq >= event_seq:
            if (
                payload.get("terminal_commitment_ledger_digest")
                != state.terminal_commitment_ledger_digest
            ):
                raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_LEDGER_MISMATCH")
            return

    harness.write_workflow_checkpoint()
    harness._verify_workflow_checkpoint()
    payload = json.loads(path.read_bytes())
    if (
        payload.get("last_control_seq", -1) < event_seq
        or payload.get("terminal_commitment_ledger_digest")
        != state.terminal_commitment_ledger_digest
    ):
        raise ValueError("TERMINAL_COMMITMENT_CHECKPOINT_SEAL_FAILED")


def _expected_terminal_result(harness, manifest, commitment):
    schema, draft = harness.objects.get(
        commitment.result_draft_ref,
        schema="workflow-run-terminal-result-draft-v1",
    )
    if schema != "workflow-run-terminal-result-draft-v1" or not isinstance(
        draft, RunTerminalResultDraftV1
    ):
        raise ValueError("TERMINAL_RESULT_DRAFT_REQUIRED")
    if (
        draft.manifest_sha256 != manifest.sha256
        or draft.run_id != manifest.sha256
        or draft.terminal_epoch != commitment.terminal_epoch
    ):
        raise ValueError("TERMINAL_RESULT_DRAFT_MISMATCH")
    from deepreason.application.models import RunResultV2

    expected = {
        **dict(draft.result_body),
        "terminal_commitment_ref": commitment.id,
    }
    return (
        RunResultV2.model_validate(expected).model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        ),
        draft,
    )


def _fresh_replay_validation(root: Path) -> dict[str, Any]:
    from deepreason.harness import Harness
    from deepreason.invariants import verify_root
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    manifest = load_run_manifest(root / MANIFEST_NAME)
    replayed = Harness(root, read_only=True)
    verification = verify_root(root)
    return {
        "schema": "replay-validation.v1",
        "manifest_digest": manifest.sha256,
        "workflow_process_digest": replayed.workflow_state.digest,
        "capability_process_digest": replayed.capability_state.digest,
        "valid": not verification["violations"],
        "verification": verification,
    }


def _post_commit_result(expected: dict[str, Any], report) -> dict[str, Any]:
    from deepreason.application.models import RunResultV2

    projected = {
        **expected,
        "verification": report.summary_payload(),
        "completion_status": (
            "satisfied" if report.completion_satisfied else "incomplete"
        ),
        "canonical_bridge_eligible": (
            expected["state"] == "completed" and report.valid
        ),
    }
    return RunResultV2.model_validate(projected).model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )


def _current_projection_is_fresh(
    harness,
    manifest,
    commitment,
    expected: dict[str, Any],
    observed: dict[str, Any],
) -> bool:
    if _result_without_projection(observed) != _result_without_projection(expected):
        return False
    try:
        _validate_result_projection_binding(
            harness,
            manifest,
            commitment,
            observed,
        )
        persisted = _read_replay_validation(Path(harness.root))
        if persisted is None or _replay_validation_base(persisted) != (
            _fresh_replay_validation(Path(harness.root))
        ):
            return False
        from deepreason.verification.report import verify_post_commit_report

        current = _post_commit_result(
            expected,
            verify_post_commit_report(harness.root),
        )
    except (OSError, TypeError, ValueError):
        return False
    return observed == current


def _publish_current_replay_projection(
    harness,
    manifest,
    commitment,
    expected: dict[str, Any],
) -> dict[str, Any]:
    from deepreason.capabilities.audit import write_tranche_a_audits
    from deepreason.verification.report import verify_post_commit_report

    write_tranche_a_audits(harness.root)
    replay_validation = _read_replay_validation(Path(harness.root))
    if replay_validation is None:
        raise ValueError("TERMINAL_REPLAY_VALIDATION_REQUIRED")
    fresh = _fresh_replay_validation(Path(harness.root))
    if _replay_validation_base(replay_validation) != fresh:
        raise ValueError("TERMINAL_REPLAY_VALIDATION_REFRESH_MISMATCH")

    result = _post_commit_result(
        expected,
        verify_post_commit_report(harness.root),
    )
    binding = _expected_replay_binding(
        harness,
        manifest,
        commitment,
        replay_validation,
        result,
    )
    bound_validation = {
        **fresh,
        "terminal_binding": binding.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=False,
        ),
    }
    _atomic_json(
        Path(harness.root) / _REPLAY_VALIDATION_NAME,
        bound_validation,
    )
    _validate_result_projection_binding(
        harness,
        manifest,
        commitment,
        result,
    )
    return result


def _finalize_terminal_result_locked(
    harness,
    manifest,
    commitment,
    expected: dict[str, Any],
) -> dict[str, Any]:
    root = Path(harness.root)
    observed = _read_current_result(root)
    if observed is not None and _current_projection_is_fresh(
        harness,
        manifest,
        commitment,
        expected,
        observed,
    ):
        return observed
    if observed is not None and _result_without_projection(
        observed
    ) != _result_without_projection(expected):
        prior_refs = {
            item.id
            for epoch, item in harness.workflow_state.terminal_commitments_by_epoch.items()
            if epoch < commitment.terminal_epoch
        }
        if observed.get("terminal_commitment_ref") not in prior_refs:
            raise ValueError("TERMINAL_RESULT_CONFLICT")

    pending = _pending_terminal_result(expected)
    if observed != pending:
        _atomic_json(root / "run-result.json", pending)
    return _publish_current_replay_projection(
        harness,
        manifest,
        commitment,
        expected,
    )


def finalize_terminal_result(
    harness,
    manifest,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Publish current post-commit validation without changing immutable records."""

    policy = getattr(manifest, "terminal_commitment_policy", None)
    if getattr(manifest, "schema_version", None) != 6 or policy is None:
        return result
    with _terminal_commitment_lock(harness):
        harness.reload_durable_authority()
        commitment = harness.workflow_state.current_terminal_commitment
        if commitment is None:
            raise ValueError("TERMINAL_COMMITMENT_REQUIRED")
        _seal_terminal_commitment_checkpoint(harness, manifest, commitment)
        expected, draft = _expected_terminal_result(
            harness,
            manifest,
            commitment,
        )
        if _result_without_projection(result) != _result_without_projection(
            expected
        ):
            raise ValueError("TERMINAL_RESULT_DRAFT_MISMATCH")
        if not _public_terminal_projection_required(draft):
            return result
        return _finalize_terminal_result_locked(
            harness,
            manifest,
            commitment,
            expected,
        )


def recover_terminal_result(harness, manifest) -> dict[str, Any] | None:
    """Reconstruct and, for public text runs, revalidate the current result."""

    policy = getattr(manifest, "terminal_commitment_policy", None)
    if getattr(manifest, "schema_version", None) != 6 or policy is None:
        return None
    with _terminal_commitment_lock(harness):
        harness.reload_durable_authority()
        commitment = harness.workflow_state.current_terminal_commitment
        if commitment is None:
            return None
        _seal_terminal_commitment_checkpoint(harness, manifest, commitment)
        expected, draft = _expected_terminal_result(
            harness,
            manifest,
            commitment,
        )
        stop = validate_stop_record(
            json.loads((Path(harness.root) / commitment.stop_record_ref).read_bytes())
        )
        _write_generic_terminal_checkpoint(harness, manifest, stop)
        if not _public_terminal_projection_required(draft):
            return expected
        return _finalize_terminal_result_locked(
            harness,
            manifest,
            commitment,
            expected,
        )


__all__ = [
    "TerminalAuthorityDerivationV1",
    "derive_terminal_authority",
    "ensure_terminal_commitment",
    "finalize_terminal_result",
    "is_commitment_bound_bridge_work",
    "model_execution_summary_digest",
    "recover_terminal_result",
    "validate_application_stop_source",
    "validate_terminal_commitment_storage",
]
