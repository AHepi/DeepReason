"""Regression (ARM R run-c3f3bf10bc57d63e224a9f1c68bf1057; run-9a6be78e1e79184a0bd89923b957586c):
a work order abandoned in flight verified clean while it was open, and its
honest closure by a no-op continuation was condemned.

`_controller_v3_history` routed EVERY non-admitted semantic admission to
`FAILURE_REQUIRED`, whose `attempt-validity` clause forbids a wire-valid
attempt, with one narrow patch-repair exception.  A closure written by a resume
- a semantic admission `schema_exhausted` over the attempt the original run
already recorded - could not reach that exception, so the same call verified
clean while its work order was open and violated once it was closed.

The classification now reads the attempt trace: a non-admitted call whose final
attempt is wire-valid is a SEMANTIC_REJECTION (at most one final wire-valid
attempt); anything else stays a failure.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from deepreason.harness import Harness
from deepreason.invariants import _controller_v3_history, verify_root
from deepreason.storage.objects import ObjectStore
from deepreason.workflow.transaction import (
    CompactRecoveryTransitionV1,
    SemanticAdmissionV1,
    WorkLifecycleTransitionV1,
    WorkTerminalV1,
    WorkTransitionKind,
)
from tests.test_v6_controller3_replay_verification import (
    _canonical_root,
    _log_rows,
    _write_log,
)


def _provider_seqs(rows: list[dict]) -> list[int]:
    return [
        row["seq"]
        for row in rows
        if (row.get("control") or {}).get("action") == "provider_result"
    ]


def _abandoned(base: Path, target: Path) -> Path:
    """The run dies right after the second provider result: the work order is
    open, no semantic admission, no terminal - exactly ARM R's three."""

    shutil.copytree(base, target)
    rows = _log_rows(target)
    cut = _provider_seqs(rows)[-1]
    _write_log(target, [row for row in rows if row["seq"] <= cut])
    return target


def _devalidate_final_attempt(root: Path) -> None:
    """Make the last provider call's final attempt not wire-valid, leaving the
    token accounting the trace and the call must agree on untouched."""

    rows = _log_rows(root)
    row = next(row for row in reversed(rows) if row["seq"] == _provider_seqs(rows)[-1])
    row["llm"]["attempt_trace"][-1]["valid"] = False
    _write_log(root, rows)


def _duplicate_final_attempt(root: Path) -> None:
    """Give the last provider call two wire-valid attempts, both valid, so the
    trace carries a valid attempt that is NOT the final one as well."""

    rows = _log_rows(root)
    row = next(row for row in reversed(rows) if row["seq"] == _provider_seqs(rows)[-1])
    trace = row["llm"]["attempt_trace"]
    extra = json.loads(json.dumps(trace[-1]))
    extra["attempt"] = 1
    # The call's own token sides are frozen against its total, so the second
    # attempt has to be free: this test is about validity, not accounting.
    extra["tokens"] = 0
    trace.append(extra)
    row["llm"]["attempts"] = len(trace)
    _write_log(root, rows)


def _closed(abandoned: Path, target: Path, *, outcome: str = "schema_exhausted") -> Path:
    """Append the closure a no-op continuation writes: a semantic admission over
    the attempt the original run already recorded, and its typed terminal.  No
    model call, no new attempt - what the resume wrote at ARM R's seqs 1171/1172."""

    shutil.copytree(abandoned, target)
    harness = Harness(target, read_only=True)
    rows = _log_rows(target)
    last = rows[-1]
    attempt = next(
        record
        for schema, record in (harness.objects.get(oid) for oid in last["outputs"])
        if schema == "workflow-provider-attempt-v1"
    )
    store = ObjectStore(target / "objects")
    admission = SemanticAdmissionV1.create(
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        provider_attempt_ref=attempt.id,
        outcome=outcome,
        admitted_refs=(),
        diagnostic_refs=(),
        authorized_pointers=(),
    )
    admission_transition = WorkLifecycleTransitionV1.create(
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        transition_kind=WorkTransitionKind.SEMANTIC_ADMISSION,
        trigger_ref=admission.id,
    )
    recovery = CompactRecoveryTransitionV1.create(
        manifest_digest=(target / "run-manifest.sha256").read_text().strip(),
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        route_lease=attempt.route_lease,
        source_profile="standard",
        semantic_admission_ref=admission.id,
    )
    terminal = WorkTerminalV1.create(
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        status=outcome,
        usage_status=attempt.usage_status,
        prompt_tokens=attempt.prompt_tokens,
        completion_tokens=attempt.completion_tokens,
        provider_attempt_ref=attempt.id,
        semantic_admission_ref=admission.id,
        reason_code=f"recovered_{outcome}",
        compact_recovery_transition_ref=recovery.id,
    )
    terminal_transition = WorkLifecycleTransitionV1.create(
        work_id=attempt.work_id,
        attempt_index=attempt.attempt_index,
        transition_kind=WorkTransitionKind.WORK_TERMINATED,
        trigger_ref=terminal.id,
    )
    store.put("workflow-compact-recovery-transition-v1", recovery)
    store.put("workflow-semantic-admission-v1", admission)
    store.put("workflow-work-lifecycle-transition-v1", admission_transition)
    store.put("workflow-work-terminal-v1", terminal)
    store.put("workflow-work-lifecycle-transition-v1", terminal_transition)

    def control_row(seq, record, transition, extra=()):
        outputs = [*[item.id for item in extra], record.id, transition.id]
        return {
            "seq": seq,
            "ts": last["ts"],
            "rule": "Control",
            "inputs": [transition.work_id, transition.trigger_ref],
            "outputs": list(outputs),
            "llm": None,
            "state_diff": {
                "att+": [], "dep+": [], "A+": [], "Π+": [], "status_changed": [],
                "hv_set": {}, "reach_set": {}, "addr+": [], "carry+": [],
            },
            "control": {
                "schema": "control.event.v3",
                "action": "work_transition",
                "decision_ref": transition.id,
                "inputs": [transition.work_id, transition.trigger_ref],
                "outputs": list(outputs),
            },
        }

    seq = rows[-1]["seq"]
    rows.append(control_row(seq + 1, admission, admission_transition))
    rows.append(control_row(seq + 2, terminal, terminal_transition, extra=(recovery,)))
    _write_log(target, rows)
    return target


def _classification(root: Path) -> tuple[int, set[int], set[int]]:
    _findings, context = _controller_v3_history(root)
    rows = _log_rows(root)
    return (
        _provider_seqs(rows)[-1],
        set(context["failure_call_seqs"]),
        set(context["semantic_rejection_call_seqs"]),
    )


def _checks(root: Path) -> list[str]:
    return [item["check"] for item in verify_root(root)["violations"]]


@pytest.fixture(scope="module")
def states(tmp_path_factory) -> dict[str, Path]:
    tmp = tmp_path_factory.mktemp("attempt-validity-semantic-rejection")
    admitted = _canonical_root(tmp)
    abandoned = _abandoned(admitted, tmp / "abandoned")
    return {
        "admitted": admitted,
        "abandoned": abandoned,
        "closed": _closed(abandoned, tmp / "closed"),
    }


def test_an_abandoned_work_order_and_its_honest_closure_verify_the_same(states):
    """The defect, stated as the disagreement it produced: the SAME wire-valid
    call verified clean while its work order was open and violated once the
    work order was closed.  Both verdicts must now agree, and agree with the
    root as the run originally wrote it."""

    assert _checks(states["admitted"]) == []
    assert _checks(states["abandoned"]) == []
    assert _checks(states["closed"]) == []

    open_stats = verify_root(states["abandoned"])["stats"]
    closed_stats = verify_root(states["closed"])["stats"]
    assert open_stats["outstanding_work_orders"], (
        "the abandoned root must still name its open work order - the fix is "
        "about the closure's verdict, not about hiding the open one"
    )
    assert closed_stats["outstanding_work_orders"] == []


def test_a_wire_valid_reply_refused_on_its_semantics_is_a_semantic_rejection(states):
    """The classification itself, not just its consequence: the closed call
    leaves FAILURE_REQUIRED (whose rule forbids any valid attempt) for
    SEMANTIC_REJECTION (which permits one final wire-valid attempt)."""

    seq, failures, rejections = _classification(states["closed"])
    assert seq in rejections
    assert seq not in failures


def test_a_non_admitted_call_with_no_wire_valid_reply_stays_a_failure(tmp_path):
    """The check must not go blind.  A non-admitted call whose final attempt
    never parsed is an ordinary failure and keeps FAILURE_REQUIRED, so the
    widened route cannot be reached by simply appending a rejecting admission."""

    admitted = _canonical_root(tmp_path)
    abandoned = _abandoned(admitted, tmp_path / "abandoned")
    _devalidate_final_attempt(abandoned)
    closed = _closed(abandoned, tmp_path / "closed")

    seq, failures, rejections = _classification(closed)
    assert seq in failures
    assert seq not in rejections
    assert "attempt-validity" not in _checks(closed)


def test_a_valid_attempt_that_is_not_the_final_one_is_still_condemned(tmp_path):
    """SEMANTIC_REJECTION permits at most ONE final wire-valid attempt.  A trace
    carrying a second valid attempt is still a violation, so the widened route
    is a category, not a blanket permission."""

    admitted = _canonical_root(tmp_path)
    abandoned = _abandoned(admitted, tmp_path / "abandoned")
    _duplicate_final_attempt(abandoned)
    closed = _closed(abandoned, tmp_path / "closed")

    seq, _failures, rejections = _classification(closed)
    assert seq in rejections
    assert "attempt-validity" in _checks(closed)
