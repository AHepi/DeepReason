"""Same-root continuation with immutable manifest and preserved stop history."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.locking import ProcessLockBusy, operator_locks
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
from deepreason.runtime.budget import Limit, parse_limit
from deepreason.runtime.progress import ProgressSink


class ContinuationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cycles: Limit
    tokens: Limit


def _digest(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _owned_v4_control(manifest):
    control = (
        manifest.control_plane_policy
        if manifest.schema_version in {4, 5}
        else None
    )
    if (
        control is None
        or control.controller_version
        not in {"workflow.controller.v1", "workflow.controller.v2"}
        or control.mode not in {"shadow", "active_conjecture", "active_inquiry"}
        or control.contract_versions.control_event_schema
        != (
            "control.event.v2"
            if manifest.schema_version == 5
            else "control.event.v1"
        )
    ):
        return None
    return control


def _canonical_file(path: Path, *, error_code: str) -> tuple[dict, str]:
    try:
        data = path.read_bytes()
        payload = json.loads(data)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(error_code) from error
    encoded = canonical_json(payload) if isinstance(payload, dict) else b""
    if not isinstance(payload, dict) or data not in {encoded, encoded + b"\n"}:
        raise ValueError(error_code)
    return payload, sha256_hex(data)


def _continuation_history(path: Path, manifest_digest: str) -> list[dict]:
    if not path.exists():
        return []
    records = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            record = json.loads(line)
            if (
                not isinstance(record, dict)
                or record.get("schema") != "deepreason-continuation-v1"
                or record.get("seq") != index
                or record.get("manifest_digest") != manifest_digest
            ):
                raise ValueError
            records.append(record)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("CONTINUE_HISTORY_INVALID") from error
    return records


def _validate_typed_history(records: list[dict], workflow_state) -> None:
    decisions = tuple(
        sorted(
            workflow_state.resume_decisions.values(),
            key=lambda decision: decision.continuation_seq,
        )
    )
    if len(records) > len(decisions):
        raise ValueError("CONTINUE_HISTORY_AUTHORITY_MISMATCH")
    required = {
        "schema",
        "seq",
        "manifest_digest",
        "prior_stop_digest",
        "request",
        "diagnostics",
        "resume_decision_ref",
        "prior_checkpoint_ref",
        "resume_checkpoint_ref",
        "workflow_checkpoint_digest",
        "run_checkpoint_digest",
    }
    for record, decision in zip(records, decisions, strict=False):
        if set(record) != required or any(
            (
                record["seq"] != decision.continuation_seq,
                record["resume_decision_ref"] != decision.id,
                record["prior_stop_digest"] != decision.prior_stop_digest,
                record["prior_checkpoint_ref"] != decision.prior_checkpoint_ref,
                record["resume_checkpoint_ref"] != decision.resume_snapshot_ref,
                record["workflow_checkpoint_digest"]
                != decision.workflow_checkpoint_digest,
                record["run_checkpoint_digest"] != decision.run_checkpoint_digest,
                record["request"]
                != {
                    "cycles": decision.requested_cycles.model_dump(mode="json"),
                    "tokens": decision.requested_tokens.model_dump(mode="json"),
                },
            )
        ):
            raise ValueError("CONTINUE_HISTORY_AUTHORITY_MISMATCH")


def _assert_no_live_lock(root: Path) -> None:
    try:
        locks = operator_locks(root, owner="continue-check", blocking=False)
    except ProcessLockBusy as error:
        raise ValueError("CONTINUE_RUN_ACTIVE: operator lock is live") from error
    locks.release()


def _append_continuation_record(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _emit_resume_progress(root: Path, manifest, stop_digest: str) -> None:
    workload = getattr(manifest, "workload_profile", None) or "text"
    sink = ProgressSink(root, run_id=manifest.sha256, workload=workload)
    sink.clear_cancellation()
    sink.emit(
        state="running",
        phase="resume",
        activity="continuation prepared",
        message=f"resuming after {stop_digest[:12]}",
    )


def _prepare_owned_v4_continuation(
    root: Path,
    *,
    manifest,
    control,
    stop: dict,
    stop_digest: str,
    fence: dict,
    request: ContinuationRequest,
    diagnostics: list[str],
) -> dict:
    """Emit or recover one typed RESUMED transition before worker dispatch."""

    from deepreason.harness import Harness
    from deepreason.workflow.lifecycle import build_resumed_lifecycle

    if stop.get("digest") != stop_digest:
        raise ValueError("CONTINUE_TYPED_STOP_DIGEST_REQUIRED")
    if set(fence) != {"schema", "manifest_digest", "stop_digest", "event_seq"}:
        raise ValueError("CONTINUE_CHECKPOINT_INVALID")
    _run_payload, run_checkpoint_digest = _canonical_file(
        root / "checkpoint.json",
        error_code="CONTINUE_CHECKPOINT_INVALID",
    )
    harness = Harness(root)
    workflow_checkpoint_digest = harness.workflow_checkpoint_digest()
    if workflow_checkpoint_digest is None:
        raise ValueError("CONTINUE_WORKFLOW_CHECKPOINT_REQUIRED")

    log_path = root / "continuations.jsonl"
    records = _continuation_history(log_path, manifest.sha256)
    _validate_typed_history(records, harness.workflow_state)
    terminal = harness.workflow_state.terminal_lifecycle_decision
    current_resume = harness.workflow_state.current_resume_decision
    if terminal is not None:
        if (
            stop_digest != terminal.stop_record_digest
            or stop.get("event_seq") != terminal.stop_event_seq
            or fence.get("event_seq") != harness._next_seq
            or terminal.manifest_digest != manifest.sha256
            or terminal.controller_version != control.controller_version
            or terminal.workflow_profile != control.workflow_profile
        ):
            raise ValueError("CONTINUE_TYPED_STOP_MISMATCH")
        if len(records) != len(harness.workflow_state.resume_decisions):
            raise ValueError("CONTINUE_HISTORY_AUTHORITY_MISMATCH")
        resume_event_seq = harness._next_seq
        try:
            snapshot, resume = build_resumed_lifecycle(
                harness.workflow_state,
                manifest_digest=manifest.sha256,
                controller_version=control.controller_version,
                workflow_profile=control.workflow_profile,
                workflow_checkpoint_digest=workflow_checkpoint_digest,
                run_checkpoint_digest=run_checkpoint_digest,
                continuation_seq=len(records),
                requested_cycles=request.cycles,
                requested_tokens=request.tokens,
                resume_event_seq=resume_event_seq,
            )
        except ValueError as error:
            raise ValueError(f"CONTINUE_NOT_AUTHORIZED: {error}") from error
        event = harness.record_resume_transition(snapshot, resume)
        if event.seq != resume_event_seq:
            raise RuntimeError("RESUMED crossed its declared event fence")
        record = {
            "schema": "deepreason-continuation-v1",
            "seq": resume.continuation_seq,
            "manifest_digest": manifest.sha256,
            "prior_stop_digest": stop_digest,
            "request": request.model_dump(mode="json"),
            "diagnostics": diagnostics,
            "resume_decision_ref": resume.id,
            "prior_checkpoint_ref": resume.prior_checkpoint_ref,
            "resume_checkpoint_ref": resume.resume_snapshot_ref,
            "workflow_checkpoint_digest": resume.workflow_checkpoint_digest,
            "run_checkpoint_digest": resume.run_checkpoint_digest,
        }
    elif current_resume is not None:
        # Crash recovery is idempotent only before any post-resume work order.
        if harness.workflow_state.post_resume_work_started:
            raise ValueError("CONTINUE_ALREADY_RESUMED")
        if (
            stop_digest != current_resume.prior_stop_digest
            or fence.get("event_seq") != current_resume.resume_event_seq
            or current_resume.run_checkpoint_digest != run_checkpoint_digest
            or current_resume.manifest_digest != manifest.sha256
            or current_resume.controller_version != control.controller_version
            or current_resume.workflow_profile != control.workflow_profile
            or current_resume.requested_cycles != request.cycles
            or current_resume.requested_tokens != request.tokens
        ):
            raise ValueError("CONTINUE_RESUME_RECOVERY_MISMATCH")
        if len(records) not in {
            current_resume.continuation_seq,
            current_resume.continuation_seq + 1,
        }:
            raise ValueError("CONTINUE_HISTORY_AUTHORITY_MISMATCH")
        record = {
            "schema": "deepreason-continuation-v1",
            "seq": current_resume.continuation_seq,
            "manifest_digest": manifest.sha256,
            "prior_stop_digest": stop_digest,
            "request": request.model_dump(mode="json"),
            "diagnostics": diagnostics,
            "resume_decision_ref": current_resume.id,
            "prior_checkpoint_ref": current_resume.prior_checkpoint_ref,
            "resume_checkpoint_ref": current_resume.resume_snapshot_ref,
            "workflow_checkpoint_digest": current_resume.workflow_checkpoint_digest,
            "run_checkpoint_digest": current_resume.run_checkpoint_digest,
        }
        if len(records) == current_resume.continuation_seq + 1:
            if records[-1] != record:
                raise ValueError("CONTINUE_HISTORY_AUTHORITY_MISMATCH")
            harness.write_workflow_checkpoint()
            _emit_resume_progress(root, manifest, stop_digest)
            return record
    else:
        raise ValueError("CONTINUE_TYPED_STOP_REQUIRED")

    _append_continuation_record(log_path, record)
    harness.write_workflow_checkpoint()
    _emit_resume_progress(root, manifest, stop_digest)
    return record


def prepare_continuation(
    root: Path | str,
    *,
    cycles: int | str | Limit,
    tokens: int | str | None | Limit,
    expected_manifest_digest: str | None = None,
    check_operator_lock: bool = True,
) -> dict:
    root_path = Path(root)
    manifest = load_run_manifest(root_path / MANIFEST_NAME)
    control = _owned_v4_control(manifest)
    if expected_manifest_digest and manifest.sha256 != expected_manifest_digest:
        raise ValueError("CONTINUE_MANIFEST_MISMATCH")
    stop_path = root_path / "run-stop.json"
    if not stop_path.exists():
        raise ValueError("CONTINUE_STOP_REQUIRED")
    stop = json.loads(stop_path.read_text(encoding="utf-8"))
    if not isinstance(stop, dict):
        raise ValueError("CONTINUE_STOP_INVALID")
    claimed_stop_digest = stop.get("digest")
    unsigned_stop = {key: value for key, value in stop.items() if key != "digest"}
    stop_digest = _digest(unsigned_stop)
    if claimed_stop_digest not in (None, stop_digest):
        raise ValueError("CONTINUE_STOP_DIGEST_MISMATCH")
    if control is not None:
        canonical_stop, _stop_file_digest = _canonical_file(
            stop_path,
            error_code="CONTINUE_STOP_INVALID",
        )
        if canonical_stop != stop:
            raise ValueError("CONTINUE_STOP_INVALID")
    checkpoint = root_path / "checkpoint.json"
    if manifest.schema_version in {2, 3, 4, 5} and not checkpoint.exists():
        raise ValueError("CONTINUE_CHECKPOINT_REQUIRED")
    if checkpoint.exists():
        try:
            fence = json.loads(checkpoint.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("CONTINUE_CHECKPOINT_INVALID") from error
        expected = {
            "schema": "deepreason-checkpoint-v1",
            "manifest_digest": manifest.sha256,
            "stop_digest": stop_digest,
        }
        if not isinstance(fence, dict) or any(
            fence.get(key) != value for key, value in expected.items()
        ):
            raise ValueError("CONTINUE_CHECKPOINT_MISMATCH")
        if control is None:
            from deepreason.harness import Harness

            if fence.get("event_seq") != Harness(root_path)._next_seq:
                raise ValueError("CONTINUE_CHECKPOINT_EVENT_FENCE_MISMATCH")
    if check_operator_lock:
        _assert_no_live_lock(root_path)
    cycle_limit, cycle_diagnostic = parse_limit(cycles, optional=False)
    token_limit, token_diagnostic = parse_limit(tokens)
    request = ContinuationRequest(cycles=cycle_limit, tokens=token_limit)

    # Preserve a legacy/latest stop before the mutable latest pointer changes
    # on a later stop.
    history = root_path / "run-stops" / (
        f"{int(stop.get('event_seq', 0)):012d}-{stop_digest}.json"
    )
    history.parent.mkdir(parents=True, exist_ok=True)
    if not history.exists():
        history.write_text(
            json.dumps(stop, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    diagnostics = [
        item for item in (cycle_diagnostic, token_diagnostic) if item is not None
    ]
    if control is not None:
        return _prepare_owned_v4_continuation(
            root_path,
            manifest=manifest,
            control=control,
            stop=stop,
            stop_digest=stop_digest,
            fence=fence,
            request=request,
            diagnostics=diagnostics,
        )

    log_path = root_path / "continuations.jsonl"
    seq = len(log_path.read_text(encoding="utf-8").splitlines()) if log_path.exists() else 0
    record = {
        "schema": "deepreason-continuation-v1",
        "seq": seq,
        "manifest_digest": manifest.sha256,
        "prior_stop_digest": stop_digest,
        "request": request.model_dump(mode="json"),
        "diagnostics": diagnostics,
    }
    _append_continuation_record(log_path, record)
    _emit_resume_progress(root_path, manifest, stop_digest)
    return record
