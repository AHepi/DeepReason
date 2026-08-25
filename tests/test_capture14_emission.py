"""The six §14 diagnostics, emitted once per cycle from ONE vector.

Implements R8's emission half (v2 calculus program, Rung 8). They join the
site that already emits the three v2 detection signals every cycle, "so the
series is complete rather than sampled" -- and they are computed ONCE and
emitted six times, because six independent computations could straddle a cycle
boundary and describe different windows.
"""

import pytest

from deepreason.capture.diagnostics import CAPTURE14_SIGNALS
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.scheduler.scheduler import Scheduler

RUNG2_SIGNALS = (
    "problem.thrash.v1",
    "criticism.attack-target-entropy.v1",
    "problem.independence-resolution-rate.v1",
)


@pytest.fixture
def scheduler_harness(tmp_path):
    """A real `Scheduler` over a real root. The emission site is inside the
    scheduler, and a test that called the capture functions directly would
    prove the formulas and not the WIRING -- which is the failure ERRATA E28
    records twice (the controller that never steered, the reach trigger that
    never fired)."""
    harness = Harness(tmp_path / "run")
    harness.register_problem(
        Problem(
            id="what-governs-the-tides",
            description="what governs the tides at the equinox",
            criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    return harness, Scheduler(harness, LLMAdapter({}, harness.blobs), Config(N_SCHOOLS=0))


def _emitted(harness):
    return [
        list(event.inputs)
        for event in harness.log.read()
        if event.inputs and event.inputs[0].startswith(("capture14.", "problem.", "criticism."))
    ]


def test_the_scheduler_emits_all_six_every_cycle(scheduler_harness):
    harness, scheduler = scheduler_harness
    scheduler._record_detection_signals()
    tags = [row[0] for row in _emitted(harness)]
    for signal in CAPTURE14_SIGNALS:
        assert tags.count(signal) == 1, signal


def test_the_three_rung_two_signals_still_fire(scheduler_harness):
    """V-6 as behaviour: a distinct family ADDS, it does not replace."""
    harness, scheduler = scheduler_harness
    scheduler._record_detection_signals()
    tags = [row[0] for row in _emitted(harness)]
    for signal in RUNG2_SIGNALS:
        assert tags.count(signal) == 1, signal


def test_all_six_describe_one_window(scheduler_harness):
    """One computation, six emissions. If the six were computed separately,
    a registration landing between two of them would give them different `n`
    -- and the vector would describe no single state of the record."""
    harness, scheduler = scheduler_harness
    scheduler._record_detection_signals()
    rows = {row[0]: row for row in _emitted(harness) if row[0].startswith("capture14.")}
    windows = {tuple(row[2:]) for row in rows.values() if len(row) > 2}
    assert len(windows) == 1, windows


def test_emission_is_deterministic_over_one_record(scheduler_harness):
    """A2/A10: two emissions over an unchanged record carry identical values."""
    harness, scheduler = scheduler_harness
    scheduler._record_detection_signals()
    first = {row[0]: row[1] for row in _emitted(harness) if row[0].startswith("capture14.")}
    scheduler._record_detection_signals()
    rows = [row for row in _emitted(harness) if row[0].startswith("capture14.")]
    second = {row[0]: row[1] for row in rows[len(first):]}
    assert first == second


def test_every_emitted_tag_is_declared(scheduler_harness):
    from deepreason.signals import declaration

    harness, scheduler = scheduler_harness
    scheduler._record_detection_signals()
    for row in _emitted(harness):
        assert declaration(row[0]) is not None, row[0]
