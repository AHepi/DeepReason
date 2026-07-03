"""Merge (spec §14, P3): componentwise set-union + re-adjudicate.

G-Set CRDT — no conflicts possible. Identical artifacts dedupe by
content-addressed id; school-policy artifacts union like any artifact and the
scheduler reconciles active rosters from config.
"""


def merge(state_a, state_b):
    """Set-union both states, then re-run two-pass adjudication. TODO(P3)."""
    raise NotImplementedError
