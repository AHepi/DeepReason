"""Grounded composition after an orderly typed stop (live finding, GLM ladder).

A public run that exhausts its bounded budget records a typed STOPPED
lifecycle decision so it stays continuable.  The bridge then composes a
grounded answer FROM that frozen record — its work orders are prepared
against the source run's terminal commitment.  The replay guard must
keep forbidding ordinary work-bound calls after the stop (continuation
requires typed RESUMED authority) while admitting exactly the
terminal-bound composition calls; before this rule, every budget-bounded
public run was uncomposable (BRIDGE_STAGE_A_FAILED, observed live on
run-889fa5110b88329aa71409e4ea97dc5e).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from deepreason.workflow.replay import WorkflowReplayState


def _state(*, reason: str, terminal_ref: str | None) -> tuple:
    state = WorkflowReplayState()
    decision = SimpleNamespace(
        id="sha256:" + "d" * 64,
        deterministic_decision=SimpleNamespace(stop=True, reason=reason),
    )
    state.terminal_decision_id = decision.id
    state.lifecycle_decisions[decision.id] = decision
    work_id = "sha256:" + "a" * 64
    state.transaction_work[work_id] = SimpleNamespace(
        issued=True,
        terminal=None,
        preparation=SimpleNamespace(
            source_terminal_commitment_ref=terminal_ref
        ),
    )
    event = SimpleNamespace(
        seq=400,
        inputs=(),
        outputs=(),
        llm=SimpleNamespace(work_order_id=work_id),
    )
    return state, event


def test_terminal_bound_composition_call_survives_a_resumable_stop():
    state, event = _state(
        reason="budget_exhausted", terminal_ref="sha256:" + "e" * 64
    )
    state.observe_event(event)  # must not raise
    assert 400 in state.transaction_calls_by_seq

    converged, event = _state(
        reason="converged", terminal_ref="sha256:" + "e" * 64
    )
    converged.observe_event(event)
    assert 400 in converged.transaction_calls_by_seq


def test_ordinary_work_after_a_typed_stop_stays_forbidden():
    state, event = _state(reason="budget_exhausted", terminal_ref=None)
    with pytest.raises(ValueError, match="follows terminal lifecycle state"):
        state.observe_event(event)


def test_composition_after_a_non_resumable_stop_stays_forbidden():
    state, event = _state(
        reason="repair_exhausted", terminal_ref="sha256:" + "e" * 64
    )
    with pytest.raises(ValueError, match="follows terminal lifecycle state"):
        state.observe_event(event)
