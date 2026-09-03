"""A stopped run whose record verifies intact is resumable, whatever it stopped on.

Regression (three committed roots, three terminal shapes, one refusal):

  * P-A1 ``4565139800f5ca020e2b74acff45355c1277a9d510068a8e8b4ed65813f1a49c``
    (``experiments/2026-09-01-live-all-modules-p-a1/run``) -- a FAILED terminal
    that took no receipt by declaration and recorded
    TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL.
  * P-A2 epoch 4 ``63e48f57415d05323b608a84f138ee5c22c274d7d8ebccc2e219b613d7c3a722``
    (``experiments/2026-09-02-live-p-a2-corrected/run``) -- KILLED mid-work;
    ``finalize`` wrote a clean terminal and ``continue`` was still refused
    STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY on 10 outstanding work items.
  * ``run-fe00609058e10605590206d51ab2b7a0`` -- an ordinary CLEAN four-cycle
    completion, exit code 0, 47 admitted conjectures, same refusal on 6 items.

All three reported ``verify_root`` violations: 0.  The refusal was never the
integrity gate; it was ``build_stopped_lifecycle`` refusing on
``snapshot.outstanding_work``, which on all three roots (and on 31/3/11 stub
roots driven to the same shapes) was accompanied by ZERO unconsumed provider
calls.  Evidence:
``experiments/2026-09-03-defect-stopped-run-resumption/proof/``.

Operator law, 2026-08-29 (CLAUDE.md), which these tests enforce: "clean stop.
with an assurance that continuing is possible. ... I don't want a jailbroken
run to be continuable."  Both halves.  The receipt never authorizes a
continuation by itself -- the SECURITY-channel gate does, at continue/amend
time, and ``tests/test_jailbreak_gate.py`` owns that half.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from deepreason.harness import Harness
from deepreason.runtime.stop import (
    StopController,
    StopDecision,
    StopMetrics,
    StopPolicy,
    build_stop_record,
)
from deepreason.workflow.lifecycle import (
    COMPOSABLE_STOP_REASONS,
    RESUMABLE_STOP_REASONS,
    UnfinishedWorkflowAuthorityError,
    build_stopped_lifecycle,
    outstanding_work_snapshot,
)

from tests.test_workflow_stop_lifecycle_c4 import _OutstandingReplay

MANIFEST_DIGEST = "a" * 64


class _TransactionalOutstandingReplay:
    """The shape every real root actually stops in.

    Outstanding transactional work whose provider call COMPLETED and was
    already consumed by replay -- awaiting only semantic admission -- and so
    carrying no unread provider authority at all.  This is what 23 of the 24
    outstanding items across the four cited roots look like, and what
    ``Scheduler._recover_workflow_prefixes`` closes on the next scheduler.

    ``issued`` distinguishes the one sub-shape the stub cannot produce: P-A2
    epoch 4 carried a CRITICISM work order issued with NO provider attempt,
    because the container kill landed between dispatch and the atomic attempt
    append.  It holds no unread result either, so it must not veto the receipt.
    """

    def __init__(self, *, count: int = 3, with_attempt: bool = True):
        self.transaction_work = {}
        for index in range(count):
            work_id = "sha256:" + f"{index:x}" * 64
            self.transaction_work[work_id] = SimpleNamespace(
                preparation=SimpleNamespace(manifest_digest=MANIFEST_DIGEST),
                issued=True,
                provider_attempts={0: object()} if with_attempt else {},
                admissions={},
            )
        self.outstanding_work_order_ids = tuple(sorted(self.transaction_work))
        self.work_orders = {}
        self.transaction_calls_by_seq = {}
        # The decisive fact: no provider call is unaccounted for.
        self.calls_by_seq = {}
        self.proposal_receipts = {}
        self.event_seqs = [3]
        self.digest = "sha256:" + "2" * 64

    def recovery_status(self, _work_id):  # pragma: no cover - never reached
        raise AssertionError("transactional work does not use legacy recovery")


def _receipt_inputs(reason: str, *, event_seq: int = 5):
    policy = StopPolicy(min_cycles=0, window=1, stable_windows=1)
    controller = StopController(policy)
    idle = controller.snapshot()
    metrics = StopMetrics(cycle=1)
    record = build_stop_record(
        reason=reason, policy=policy, metrics=metrics, event_seq=event_seq
    )
    return {
        "manifest_digest": MANIFEST_DIGEST,
        "controller_version": "workflow.controller.v1",
        "workflow_profile": "conjecture.active.v1",
        "policy": policy,
        "metrics": metrics,
        "deterministic_decision": StopDecision(stop=True, reason=reason),
        "controller_state_before": idle,
        "controller_state_after": idle,
        "stop_event_seq": event_seq,
        "stop_record_digest": record["digest"],
    }


# --- the narrowing --------------------------------------------------------


@pytest.mark.parametrize("with_attempt", [True, False])
def test_outstanding_work_with_no_unread_result_takes_the_receipt(with_attempt):
    """The shape all four cited roots stop in must NOT veto the receipt.

    Parametrized over the two sub-shapes the census found: a provider result
    awaiting admission (23 of 24 items), and a work order issued with no
    provider attempt at all (P-A2 epoch 4's CRITICISM item, 1 of 24).  Neither
    holds a result nobody has read, so neither is what the refusal protects.
    """

    replay = _TransactionalOutstandingReplay(with_attempt=with_attempt)
    snapshot = outstanding_work_snapshot(
        replay,
        manifest_digest=MANIFEST_DIGEST,
        controller_version="workflow.controller.v1",
        event_fence_seq=4,
    )
    # The premise: work IS outstanding, and none of it is unread authority.
    assert len(snapshot.outstanding_work) == 3
    assert snapshot.unconsumed_bound_call_seqs == ()

    _observation, taken, decision = build_stopped_lifecycle(
        replay, **_receipt_inputs("budget_exhausted")
    )
    # The receipt is taken AND still carries the outstanding work, so a resume
    # re-enters it rather than forgetting it.
    assert taken.outstanding_work == snapshot.outstanding_work
    assert decision.deterministic_decision.reason == "budget_exhausted"


def test_an_unread_provider_result_still_refuses_the_receipt():
    """The protection, pinned apart from the narrowing.

    An unconsumed bound call is a provider result nobody read: closing a stop
    over one forces a resume to re-issue the call (two calls recorded for one
    authority) or drop a result the record already holds.  ``_OutstandingReplay``
    carries exactly that -- call seq 7 with no receipt.
    """

    replay = _OutstandingReplay()
    snapshot = outstanding_work_snapshot(
        replay,
        manifest_digest=MANIFEST_DIGEST,
        controller_version="workflow.controller.v1",
        event_fence_seq=4,
    )
    assert snapshot.unconsumed_bound_call_seqs == (7,)

    with pytest.raises(UnfinishedWorkflowAuthorityError) as raised:
        build_stopped_lifecycle(replay, **_receipt_inputs("budget_exhausted"))
    assert raised.value.code == "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"
    assert raised.value.unconsumed_bound_call_count == 1


def test_every_receipt_predicate_asks_the_same_question():
    """Five sites decide this, and they must not drift apart.

    Two build sites (``build_stopped_lifecycle``, ``build_resumed_lifecycle``)
    and two apply sites in ``workflow/replay.py``, plus the terminal-snapshot
    check inside the resume builder.  A receipt granted by one and refused by
    another produces a root that terminates and then refuses one layer later,
    which is the defect this tranche repaired wearing a different hat.  The
    property is asserted over SOURCE because the four sites are reached by
    four different code paths that no single fixture drives.
    """

    import inspect

    from deepreason.workflow import lifecycle, replay

    # The old, wider predicate must survive at NONE of the five sites: any one
    # left behind re-creates the asymmetry.
    for module in (lifecycle, replay):
        source = inspect.getsource(module)
        assert "outstanding_work or snapshot.unconsumed_bound_call_seqs" not in source
        assert (
            "terminal_snapshot.outstanding_work or "
            "terminal_snapshot.unconsumed_bound_call_seqs"
        ) not in source

    # And each site still asks the question that carries the protection.
    guards = inspect.getsource(lifecycle).count(
        "if snapshot.unconsumed_bound_call_seqs:"
    ) + inspect.getsource(replay).count("if snapshot.unconsumed_bound_call_seqs:")
    assert guards == 4, f"expected four snapshot guards, found {guards}"
    assert (
        "if terminal_snapshot.unconsumed_bound_call_seqs:"
        in inspect.getsource(lifecycle)
    )


# --- the reasons ----------------------------------------------------------


def test_a_failure_terminal_may_be_resumed_and_a_cancellation_may_not():
    """The operator's 2026-08-29 law, and the boundary it does not cross.

    "Every terminal -- clean or failed -- must leave checkpoints sufficient for
    relaunch."  A cancellation is a decision rather than an interruption, so it
    is deliberately NOT widened; that would need its own ruling.
    """

    assert "operational_failure" in RESUMABLE_STOP_REASONS
    assert "budget_exhausted" in RESUMABLE_STOP_REASONS
    assert "converged" in RESUMABLE_STOP_REASONS
    assert "operator_cancelled" not in RESUMABLE_STOP_REASONS
    assert "completed" not in RESUMABLE_STOP_REASONS


def test_widening_resumption_did_not_widen_bridge_composition():
    """Composing FROM a frozen terminal is a different permission from resuming one.

    ``_post_terminal_composition_call`` read ``RESUMABLE_STOP_REASONS`` until
    2026-09-03.  Had it kept reading it, widening resumption to failure
    terminals would silently have admitted bridge composition calls after an
    operational failure -- a change nobody asked for, arriving as a side
    effect.  The two sets are separate so that cannot happen by omission.
    """

    assert "operational_failure" not in COMPOSABLE_STOP_REASONS
    assert COMPOSABLE_STOP_REASONS < RESUMABLE_STOP_REASONS

    import inspect

    from deepreason.workflow import replay

    # Anchored on the executable line, not on raw text: the method's own
    # comment names the set it deliberately does NOT read.
    source = inspect.getsource(replay.WorkflowReplayState._post_terminal_composition_call)
    assert "if reason not in COMPOSABLE_STOP_REASONS:" in source
    assert "if reason not in RESUMABLE_STOP_REASONS:" not in source


def test_a_runtime_decided_stop_replays_no_controller_authority():
    """Neither exhaustion nor failure passes through ``StopController.evaluate``.

    The cycle loop and token meter decide one; an unhandled error decides the
    other.  A receipt for either must declare that no controller authority was
    consumed, or the builder tries to replay an evaluation that never happened.
    """

    from deepreason.workflow.lifecycle import _is_runtime_decided

    for reason in ("budget_exhausted", "operational_failure"):
        assert _is_runtime_decided(StopDecision(stop=True, reason=reason))
    assert not _is_runtime_decided(StopDecision(stop=True, reason="converged"))
    assert not _is_runtime_decided(
        StopDecision(stop=True, reason="budget_exhausted", escape_action="widen")
    )

    replay = _TransactionalOutstandingReplay()
    inputs = _receipt_inputs("operational_failure")
    inputs["controller_state_after"] = StopController(
        StopPolicy(min_cycles=0, window=1, stable_windows=1)
    ).snapshot()
    # Same idle state either side: accepted.
    build_stopped_lifecycle(replay, **inputs)


# --- the two records may never disagree again -----------------------------


def test_the_terminal_and_the_results_surface_describe_the_same_root(
    tmp_path, monkeypatch
):
    """Regression (provenance tranche PARKED P1): two typed records, one root,
    opposite answers.  ``results --json`` published
    ``"stop_reason_resumable": true`` on a root whose ``continue`` refused
    CONTINUE_TYPED_STOP_REQUIRED, because one surface read the stop REASON and
    the other read whether the receipt was ever taken.

    The fix does not teach the two surfaces to agree; it removes the condition
    under which they could differ, by making the receipt actually get taken.
    This test fails if that ever comes apart again -- on the clean path and on
    the failure path alike.
    """

    from deepreason.application.results import results_summary

    from tests.test_checkpoint_hardening import _failed_root
    from tests.test_lifecycle_operation_parity import _manifest_launched_root

    clean_root, _manifest, _spec = _manifest_launched_root(
        tmp_path, monkeypatch, name="agreement-clean-root"
    )
    failed_root = _failed_root(
        tmp_path, monkeypatch, name="agreement-failed-root"
    )

    for root in (clean_root, failed_root):
        result = json.loads((root / "run-result.json").read_text())
        status = json.loads((root / "run-status.json").read_text())
        terminal = results_summary(root)["terminal"]

        recorded_refusal = result.get("terminal_lifecycle_refusal")
        assert recorded_refusal is None, f"{root.name} refused its receipt"
        assert status["terminal_lifecycle_refusal"] is None

        # The record's own answer, read directly rather than via either surface.
        state = Harness(root, read_only=True).workflow_state
        assert state.terminal_lifecycle_decision is not None

        # THE AGREEMENT: a root that reports its stop reason resumable must
        # also report the authority that makes resuming possible. Reporting one
        # without the other is the defect, in either direction.
        assert terminal["stop_reason_resumable"] is True
        assert terminal["continuation_authority"] is True
