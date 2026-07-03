"""Isolation floor (spec §7 L2).

    conn(a) = #{accepted dependence edges a participates in}
    iso(a)  = max(0, FLOOR - conn(a))

iso(a) > 0 => Spawn a cheap connection problem against top-K neighbours
(rank: shared problem > shared refs > lexical/embedding overlap), under
INTEGRATION_BUDGET_SHARE. Emergent: raw uninterpreted data is maximally
isolated, so the same signal drives interpretation of numeric/opaque content.
"""


def conn(artifact_id: str, state) -> int:
    raise NotImplementedError


def iso(artifact_id: str, state, floor: int) -> int:
    raise NotImplementedError


def rank_neighbours(artifact_id: str, state, k: int) -> list[str]:
    """Deterministic neighbour ranking for connection problems. TODO(P2)."""
    raise NotImplementedError
