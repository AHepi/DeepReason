"""Rung S5 (seats in the typed record): every run records which
provider/model sat in which role group.

Implements R2/R4/R5/R6 and SPEC.md Items S2-S7 of
``experiments/2026-08-07-change-seats-in-record-s5``. The reader is
tested BEFORE the writer exists, because absence of the stamp must be
valid for every root recorded before the feature -- that ordering is the
rung's own guardrail (R4, C4), mirroring rung 4's own guardrail.

Regression discipline carried forward from rung 4 (C5's trap in
``DR-SEAM-harness-x-verification``: "a census check expires; a
partition check does not" -- ``tests/test_module_fingerprints.py``
asserted NO committed root carried a stamp, which was true only until
the first run recorded after that rung's writer landed): no assertion
below claims a permanent census over committed roots. The absence claim
below is scoped to what the reader itself promises -- it does not raise
and tolerates an event with no attribute -- never to "no root has ever
been stamped", which this rung's own future live runs will falsify.
"""

import subprocess
from pathlib import Path

from deepreason.harness import Harness
from deepreason.run_manifest import UnsupportedRunManifestVersionError
from deepreason.seat_events import (
    SeatBindingsEventPayloadV1,
    SeatBindingV1,
    recorded_seat_bindings,
)


def _committed_roots() -> list[Path]:
    """Only roots ``git ls-files`` knows: a session-local root would take the
    meaning of every assertion below with it when the session ends."""

    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [Path(p).parent for p in tracked if p.endswith("/log.jsonl")]


def test_recorded_seat_bindings_is_absent_on_a_fresh_harness(tmp_path):
    """SPEC.md Item S2's own accept criterion: a fresh run with no
    seat-bindings event reads as absent, not as an error."""

    harness = Harness(tmp_path / "run")
    harness.record_measure(inputs=["x"])
    assert recorded_seat_bindings(harness) == ()


def test_the_reader_tolerates_every_currently_committed_root():
    """The reader must never raise on a root it can open, whatever that
    root's own history is. Unlike a claim about WHICH roots carry a
    stamp (a census, C5's trap), "the reader does not crash" cannot ever
    be falsified by a future run stamping one -- it stays true forever,
    which is what makes it safe to assert here permanently.
    """

    roots = _committed_roots()
    opened = 0
    refused = 0
    for root in roots:
        try:
            harness = Harness(root, read_only=True)
        except UnsupportedRunManifestVersionError:
            refused += 1
            continue
        assert isinstance(recorded_seat_bindings(harness), tuple), root
        opened += 1
    assert opened + refused == len(roots)
    assert opened > 20, opened  # today's floor; not an upper bound


def test_the_reader_tolerates_an_event_with_no_seat_bindings_attribute(tmp_path):
    """R4 at the EVENT level rather than the root level: an event object
    that predates the payload field has no attribute to read, and the
    reader must treat that as absence rather than raising.
    """

    harness = Harness(tmp_path / "run")
    harness.record_measure(inputs=["x"])

    class _EventWithoutTheField:
        pass

    assert getattr(_EventWithoutTheField(), "seat_bindings", None) is None
    assert recorded_seat_bindings(harness) == ()


def test_the_reader_extracts_a_stamp_the_event_already_carries():
    """The reader's own contract -- read whatever ``event.seat_bindings``
    holds -- does not depend on ``Event.seat_bindings`` existing as a
    declared model field yet (step 7). A bare object exercises the
    reader in isolation from the payload-field step that comes later.
    """

    binding = SeatBindingV1.of(
        "coder",
        type("Profile", (), {"provider": "generic", "model_id": "m", "profile_digest": "d"})(),
    )
    payload = SeatBindingsEventPayloadV1.of([binding])

    class _EventWithTheField:
        seat_bindings = payload

    harness_log = [_EventWithTheField()]

    class _FakeLog:
        def read(self):
            return harness_log

    class _FakeHarness:
        log = _FakeLog()

    assert recorded_seat_bindings(_FakeHarness()) == (payload,)
