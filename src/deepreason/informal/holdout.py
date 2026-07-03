"""Holdout + novel-case commitments (spec §10.5).

HOLDOUT_SHARE of the evidence corpus is registered sealed: hash visible,
bytes excluded from all packs until the scheduled Reveal event. Sealed
evidence does not count as covering (no premature research Spawn). Pass on
held-out material = a reach hit with the strongest provenance the informal
side can produce (Lakatos's novel-fact criterion, mechanized).
"""


def seal(evidence_blob: bytes, reveal_at_cycle: int, state):
    """Register sealed evidence in the holdout namespace. TODO(P5)."""
    raise NotImplementedError


def reveal(evidence_id: str, state):
    """Reveal event: instantiate and evaluate pending commitments. TODO(P5)."""
    raise NotImplementedError
