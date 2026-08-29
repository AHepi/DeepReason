"""A refused STOPPED lifecycle receipt is TYPED, RECORDED, and REPORTED.

Regression (soak case ``epoch3``, offline; audit 2026-08-28 finding F-C;
parked prompt P6 + amendment P6-A): a run that exhausted its budget with 11
outstanding work orders published ``state=completed``,
``stop_reason=budget_exhausted`` and a clean ``verify_root``, and
``deepreason results`` reported

    ready for `deepreason amend` / `deepreason continue`: yes

while ``deepreason continue`` refused CONTINUE_TYPED_STOP_REQUIRED on that
same root.  ``workflow/lifecycle.py`` was refusing CORRECTLY; the defect was
that ``application/text_runs.py`` answered the refusal with a bare

    except ValueError:
        return None

so no trace of the rejection reached the terminal, and the two surfaces then
evaluated independent predicates over facts only one of them could see.

Nothing here asserts that unfinished workflow authority OUGHT to permit
continuation — that question is open and belongs to the operator (P2).  These
tests assert only that the refusal cannot be silent.
"""

from __future__ import annotations

import json

import pytest

from deepreason.application.results import results_summary
from deepreason.harness import Harness
from deepreason.runtime.progress import ProgressEvent
from deepreason.runtime.stop import (
    StopController,
    StopMetrics,
    StopPolicy,
    build_stop_record,
)
from deepreason.workflow.lifecycle import (
    UnfinishedWorkflowAuthorityError,
    build_stopped_lifecycle,
    outstanding_work_snapshot,
)

from tests.test_lifecycle_operation_parity import (
    _bind_v6_root,
    _launch_through_cli,
)
from tests.test_workflow_stop_lifecycle_c4 import _OutstandingReplay


def test_the_stopped_refusal_is_typed_and_carries_the_counts_that_caused_it():
    """The builder's refusal is a NAMED type, not one of seven bare ValueErrors.

    `build_stopped_lifecycle` and `outstanding_work_snapshot` raise
    `ValueError` in seven places; six are bugs and this one is a correct,
    expected refusal decided by the record.  A caller that cannot tell them
    apart answers all seven with the same silence, which is exactly what
    happened.
    """

    replay = _OutstandingReplay()
    snapshot = outstanding_work_snapshot(
        replay,
        manifest_digest="a" * 64,
        controller_version="workflow.controller.v1",
        event_fence_seq=4,
    )
    assert snapshot.outstanding_work

    policy = StopPolicy(min_cycles=0, window=1, stable_windows=1)
    controller = StopController(policy)
    before = controller.snapshot()
    metrics = StopMetrics(cycle=1)
    decision = controller.evaluate(metrics)
    stop = build_stop_record(
        reason=decision.reason, policy=policy, metrics=metrics, event_seq=5
    )

    with pytest.raises(UnfinishedWorkflowAuthorityError) as raised:
        build_stopped_lifecycle(
            replay,
            manifest_digest="a" * 64,
            controller_version="workflow.controller.v1",
            workflow_profile="conjecture.active.v1",
            policy=policy,
            metrics=metrics,
            deterministic_decision=decision,
            controller_state_before=before,
            controller_state_after=controller.snapshot(),
            stop_event_seq=5,
            stop_record_digest=stop["digest"],
        )

    error = raised.value
    assert error.code == "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"
    assert error.outstanding_work_count == len(snapshot.outstanding_work)
    assert error.unconsumed_bound_call_count == len(
        snapshot.unconsumed_bound_call_seqs
    )
    # It stays a ValueError so every handler written before the type existed
    # keeps catching it, and the historical message substring survives.
    assert isinstance(error, ValueError)
    assert "unfinished workflow authority" in str(error)


def _refused_root(tmp_path, monkeypatch, *, error):
    """Drive the real run path with the lifecycle builder refusing.

    DECLARED LIMIT: the refusal is injected rather than grown from eleven real
    outstanding work orders, because what is under test here is the CALLER's
    handling, which is where the defect is.  That the refusal genuinely fires
    on real outstanding authority is proven by the first test in this module
    against a real `outstanding_work_snapshot`, and end to end by the 98-second
    `cycle_soak.py --case epoch3` recorded in this tranche's VERIFY.md, which
    is far too slow to sit in the gate.
    """

    root, manifest, _spec, problem_file = _bind_v6_root(
        tmp_path, name="refused-terminal-root"
    )

    def _refuse(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(
        "deepreason.workflow.lifecycle.build_stopped_lifecycle", _refuse
    )
    assert _launch_through_cli(root, manifest, problem_file, monkeypatch) == 0
    return root


def test_a_refused_terminal_records_the_refusal_and_no_surface_claims_continue(
    tmp_path, monkeypatch
):
    """The whole defect, end to end: refused, recorded, reported, consistent."""

    replay = _OutstandingReplay()
    snapshot = outstanding_work_snapshot(
        replay,
        manifest_digest="a" * 64,
        controller_version="workflow.controller.v1",
        event_fence_seq=4,
    )
    root = _refused_root(
        tmp_path, monkeypatch, error=UnfinishedWorkflowAuthorityError(snapshot)
    )

    # 1. The terminal record carries the refusal, typed.
    result = json.loads((root / "run-result.json").read_text())
    refusal = result["terminal_lifecycle_refusal"]
    assert refusal["schema"] == "deepreason-terminal-lifecycle-refusal-v1"
    assert refusal["code"] == "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"
    assert refusal["outstanding_work"] == len(snapshot.outstanding_work)
    assert refusal["unconsumed_bound_calls"] == len(
        snapshot.unconsumed_bound_call_seqs
    )
    assert "unfinished workflow authority" in refusal["detail"]

    # 2. The polled operational surface carries the code.
    status = json.loads((root / "run-status.json").read_text())
    assert status["stop_reason"] == "budget_exhausted"
    assert (
        status["terminal_lifecycle_refusal"]
        == "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"
    )

    # 3. The record still shows exactly what made `continue` refuse.
    workflow_state = Harness(root, read_only=True).workflow_state
    assert workflow_state.terminal_lifecycle_decision is None
    assert workflow_state.current_resume_decision is None

    # 4. `results` no longer promises the continuation `continue` refuses,
    #    and names why.
    terminal = results_summary(root)["terminal"]
    assert terminal["continuation_authority"] is False
    assert terminal["amend_ready"] is False
    assert (
        terminal["lifecycle_refusal"]
        == "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"
    )
    assert terminal["stop_reason_resumable"] is True  # the stop reason alone
    #                                                   never was the question


def test_a_lifecycle_bug_records_a_DIFFERENT_code_than_a_correct_refusal(
    tmp_path, monkeypatch
):
    """Typing the refusal is pointless if every ValueError still shares a code.

    The other six `ValueError`s the builder raises are bugs, not refusals, and
    must not be recorded as `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`.
    """

    root = _refused_root(
        tmp_path,
        monkeypatch,
        error=ValueError("lifecycle controller state does not replay exactly"),
    )
    refusal = json.loads((root / "run-result.json").read_text())[
        "terminal_lifecycle_refusal"
    ]
    assert refusal["code"] == "TERMINAL_LIFECYCLE_REJECTED"
    assert "does not replay exactly" in refusal["detail"]
    assert results_summary(root)["terminal"]["amend_ready"] is False


def test_an_unrefused_terminal_still_reports_ready_and_records_no_refusal(
    tmp_path, monkeypatch
):
    """The CONTROL. The fix may only ever turn a FALSE yes into a no.

    Without this, a fix that reported `amend_ready: False` unconditionally
    would pass every assertion above while destroying the operation the
    2026-08-13 operations-parity law requires of every configuration.
    """

    root, manifest, _spec, problem_file = _bind_v6_root(
        tmp_path, name="ordinary-terminal-root"
    )
    assert _launch_through_cli(root, manifest, problem_file, monkeypatch) == 0

    result = json.loads((root / "run-result.json").read_text())
    assert "terminal_lifecycle_refusal" not in result
    status = json.loads((root / "run-status.json").read_text())
    assert status["terminal_lifecycle_refusal"] is None

    assert (
        Harness(root, read_only=True).workflow_state.terminal_lifecycle_decision
        is not None
    )
    terminal = results_summary(root)["terminal"]
    assert terminal["continuation_authority"] is True
    assert terminal["amend_ready"] is True
    assert terminal["lifecycle_refusal"] == {
        "absent": True,
        "reason": "NO_LIFECYCLE_REFUSAL_RECORD",
    }


def test_a_progress_line_written_before_the_field_existed_still_validates():
    """`ProgressEvent` forbids extras, so a new field must not orphan old lines.

    Every committed root's `progress.jsonl` is read back through this model.
    A required field, or one without a default, would make each of those lines
    unreadable — which would be a reader breaking on evidence it used to read.
    """

    historical = json.dumps(
        {
            "seq": 0,
            "run_id": "r",
            "state": "completed",
            "workload": "text",
            "phase": "stop",
            "activity": "budget_exhausted",
        }
    )
    event = ProgressEvent.model_validate_json(historical)
    assert event.terminal_lifecycle_refusal is None
