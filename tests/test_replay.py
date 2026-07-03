"""P0 acceptance: replay-from-log reproduces state byte-for-byte (spec §16)."""

import pytest

pytestmark = pytest.mark.skip(reason="P0 not implemented yet")


def test_replay_reproduces_state_byte_for_byte():
    """Materialize state from the event log twice; serializations identical."""


def test_time_travel_truncated_replay():
    """Replaying up to seq N yields the state as of event N."""
