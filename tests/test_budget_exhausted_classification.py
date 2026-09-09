"""A budget denial on a SPENT ceiling is a clean stop; one with headroom is not.

Operator law, 2026-08-29 (CLAUDE.md): "clean stop. with an assurance that
continuing is possible.  Too often an operational failure overlooks securing
enough checkpoints to allow relaunches" -- and, stated for this exact case, "a
budget denial on an exhausted budget terminates as `budget_exhausted` (clean),
never `operational_failure`".

Regression (organiser ARM R, run-c3f3bf10bc57d63e224a9f1c68bf1057, epoch-0
terminal at commit ebdfe976e): the run spent 495 362 of its 500 000-token
ceiling, the next criticism dispatch was refused by the meter, and the run
published `state: failed`, `stop_reason: operational_failure`.  Its record was
sound -- `verify_root` re-derived 0 violations -- so the defect was the
CLASSIFICATION alone.  The cause: `Scheduler.run` absorbs `TokenBudgetExceeded`
onto a clean-stop road and the v6 transactional path raises `WorkBudgetDenied`,
which is not that type, so the denial left the run and the terminalizer's
catch-all called it a breakage.

Both directions are pinned here, because a fix that made every denial clean
would be as wrong as the defect: a refusal the ceiling could still have
afforded is not the budget ending the run.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepreason.llm.budget import (
    TokenBudgetExceeded,
    TokenMeter,
    budget_denial_exhausted,
)
from deepreason.runtime.continuation import prepare_continuation
from deepreason.workflow.transaction import WorkBudgetDenied
from tests.test_lifecycle_operation_parity import MANIFEST_NAME, _bind_v6_root

# The observed root's own numbers: run-manifest.json caps every seat at 8192
# completion tokens, and run-status.json records 495362 spent of 500000.
CEILING = 500_000
SPENT = 495_362
SEAT_CAP = 8_192


def _refusal(meter: TokenMeter, **kwargs) -> TokenBudgetExceeded:
    with pytest.raises(TokenBudgetExceeded) as raised:
        meter.reserve(**kwargs)
    return raised.value


# --------------------------------------------------------------------------
# 1. The rule, decided where the numbers are.
# --------------------------------------------------------------------------


def test_the_observed_roots_own_numbers_read_as_a_spent_ceiling():
    """4638 tokens left against an 8192-token cap: nothing more is dispatchable."""

    meter = TokenMeter(budget=CEILING)
    meter.prompt_tokens = SPENT
    error = _refusal(meter, prompt_text="x" * 3_000, max_tokens=SEAT_CAP)

    assert error.budget_remaining == CEILING - SPENT == 4_638
    # The booking is a 3000-character prompt bounded at chars/3, plus the cap.
    assert error.budget_booking == 1_000 + SEAT_CAP
    assert error.budget_booking <= CEILING       # an empty ceiling would have served it
    assert error.budget_exhausted is True
    assert budget_denial_exhausted(error) is True


def test_a_request_no_empty_ceiling_could_have_served_is_not_exhaustion():
    """Nothing is spent, and this dispatch still would not fit.

    The ceiling is not what stopped this run -- the request is larger than the
    whole budget, so no amount of unspent headroom would have helped.  That is
    a dispatch too large for the run's configuration, and it must not buy the
    clean terminal the operator's law reserves for a spent budget.
    """

    meter = TokenMeter(budget=CEILING)
    error = _refusal(meter, prompt_text="x" * 3_000_000, max_tokens=SEAT_CAP)

    assert error.budget_remaining == CEILING
    assert error.budget_booking > CEILING
    assert error.budget_exhausted is False
    assert budget_denial_exhausted(error) is False


def test_the_rules_edge_sits_at_the_whole_ceiling_both_sides():
    """A booking of exactly the ceiling is spent; one token more never was."""

    fits_empty = TokenMeter(budget=CEILING)
    fits_empty.prompt_tokens = 1
    assert _refusal(
        fits_empty, prompt_tokens=CEILING - SEAT_CAP, max_tokens=SEAT_CAP
    ).budget_exhausted is True

    never_fits = TokenMeter(budget=CEILING)
    never_fits.prompt_tokens = 1
    assert _refusal(
        never_fits, prompt_tokens=CEILING - SEAT_CAP + 1, max_tokens=SEAT_CAP
    ).budget_exhausted is False


def test_a_fail_closed_refusal_is_a_plumbing_fault_until_nothing_remains():
    """A dispatch whose own size cannot be established is not the ceiling.

    Neither bound can be compared against a budget, so the only thing left to
    read is whether anything remains at all.
    """

    with_room = TokenMeter(budget=CEILING)
    assert _refusal(with_room, max_tokens=SEAT_CAP).budget_exhausted is False
    assert _refusal(with_room, prompt_text="short").budget_exhausted is False

    spent = TokenMeter(budget=CEILING)
    spent.prompt_tokens = CEILING
    assert _refusal(spent, prompt_text="short").budget_exhausted is True


def test_check_reports_a_spent_ceiling_and_a_bare_error_defaults_to_spent():
    """`check()` only raises past the ceiling.  And every raise site written
    before this field existed is a ceiling already reached, so an error
    carrying no answer reads as spent -- a default of False would silently
    reclassify stops this regression was not asked to touch."""

    meter = TokenMeter(budget=CEILING)
    meter.prompt_tokens = CEILING
    with pytest.raises(TokenBudgetExceeded) as raised:
        meter.check()
    assert raised.value.budget_exhausted is True

    assert budget_denial_exhausted(TokenBudgetExceeded("no metadata")) is True


def test_the_transactional_denial_carries_the_meters_answer():
    """`WorkBudgetDenied` is not a `TokenBudgetExceeded`, so the verdict has to
    travel by hand or it is lost at the exception change."""

    terminal = SimpleNamespace(work_id="sha256:" + "d" * 8)
    assert WorkBudgetDenied(terminal).budget_exhausted is False
    assert WorkBudgetDenied(terminal, budget_exhausted=True).budget_exhausted is True
    assert budget_denial_exhausted(WorkBudgetDenied(terminal)) is False


# --------------------------------------------------------------------------
# 2 and 3. What the run PUBLISHES, through the one run path.
# --------------------------------------------------------------------------


def _run_denied(tmp_path, monkeypatch, *, exhausted: bool, name: str):
    """Drive `deepreason run --run-manifest` to a terminal, denying one cycle.

    The REAL `ops.run_scheduler` runs -- the real meter, the real adapter, the
    real `Scheduler` -- and only `Scheduler.step` is replaced, so nothing but
    the cycle loop's own exception arm decides what happens next.  No provider
    is reached because no dispatch is ever attempted.

    Deliberately NOT `tests.test_lifecycle_operation_parity._launch_through_cli`:
    that helper installs a no-provider stand-in for `run_scheduler`, which
    would skip the loop this regression is about and leave both directions
    asserting on a run that never denied anything.
    """

    from deepreason.cli.main import main
    from deepreason.scheduler.scheduler import Scheduler

    root, _manifest, _spec, problem_file = _bind_v6_root(tmp_path, name=name)

    def _deny(self):
        raise WorkBudgetDenied(
            SimpleNamespace(work_id="sha256:" + "d" * 8),
            budget_exhausted=exhausted,
        )

    monkeypatch.setattr(Scheduler, "step", _deny)
    code = main(
        [
            "--root", str(root), "run", "--budget", "1",
            "--problem", str(problem_file),
            "--run-manifest", str(root / MANIFEST_NAME),
        ]
    )
    return root, code


def test_a_denial_on_a_spent_ceiling_publishes_a_clean_budget_exhausted_stop(
    tmp_path, monkeypatch
):
    """The defect, inverted: the terminal ARM R should have published."""

    root, code = _run_denied(
        tmp_path, monkeypatch, exhausted=True, name="spent-ceiling"
    )
    assert code == 0

    status = json.loads((root / "run-status.json").read_text())
    assert status["state"] == "completed"
    assert status["stop_reason"] == "budget_exhausted"

    result = json.loads((root / "run-result.json").read_text())
    assert result["state"] == "completed"
    assert result["stop"]["reason"] == "budget_exhausted"


def test_the_clean_budget_stop_leaves_what_a_relaunch_needs(tmp_path, monkeypatch):
    """The other half of the same law: every terminal secures continuation.

    A stop that cannot assure continuability is itself a defect ("corrupted
    stop"), so the new road is asserted on the checkpoint, the typed STOPPED
    receipt, and an actual continuation being prepared -- not on the stop
    reason alone.
    """

    from deepreason.harness import Harness

    root, _code = _run_denied(
        tmp_path, monkeypatch, exhausted=True, name="spent-ceiling-checkpoints"
    )

    checkpoint = json.loads((root / "checkpoint.json").read_text())
    assert checkpoint["schema"] == "deepreason-checkpoint-v1"
    stop = json.loads((root / "run-stop.json").read_text())
    assert stop["reason"] == "budget_exhausted"
    assert checkpoint["stop_digest"] == stop["digest"]

    decision = Harness(root, read_only=True).workflow_state.terminal_lifecycle_decision
    assert decision is not None
    assert decision.deterministic_decision.reason == "budget_exhausted"

    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / root.name
        shutil.copytree(root, copy, symlinks=True)
        prepared = prepare_continuation(
            copy, cycles=1, tokens=10, check_operator_lock=False
        )
    assert prepared["schema"] == "deepreason-continuation-v1"


def test_a_denial_with_budget_remaining_stays_an_operational_failure(
    tmp_path, monkeypatch
):
    """The guard.  A refusal the ceiling could still have afforded is not the
    budget ending the run, and must not buy a clean terminal."""

    root, code = _run_denied(
        tmp_path, monkeypatch, exhausted=False, name="budget-remaining"
    )
    assert code != 0

    status = json.loads((root / "run-status.json").read_text())
    assert status["state"] == "failed"
    assert status["stop_reason"] == "operational_failure"

    result = json.loads((root / "run-result.json").read_text())
    assert result["state"] == "failed"
    assert result["stop"]["reason"] == "operational_failure"
