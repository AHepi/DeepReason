"""Isolation floor (spec §7 L2).

    conn(a) = #{accepted dependence edges a participates in}
    iso(a)  = max(0, FLOOR - conn(a))

iso(a) > 0 => Spawn a cheap connection problem against top-K neighbours
(rank: shared problem > shared refs > lexical/embedding overlap), under
INTEGRATION_BUDGET_SHARE. Emergent: raw uninterpreted data is maximally
isolated, so the same signal drives interpretation of numeric/opaque content.
"""

from collections.abc import Iterable

from deepreason.ontology.state import Status


def conn_map(
    dep_edges: Iterable[tuple[str, str]],
    status: dict[str, Status],
) -> dict[str, int]:
    """conn per artifact: a dependence edge counts as accepted when both of
    its endpoints are finally accepted; it counts for both endpoints."""
    counts = {aid: 0 for aid in status}
    for a, b in dep_edges:
        if status.get(a) == Status.ACCEPTED and status.get(b) == Status.ACCEPTED:
            counts[a] += 1
            counts[b] += 1
    return counts


def iso(artifact_id: str, conn: dict[str, int], floor: int) -> int:
    return max(0, floor - conn.get(artifact_id, 0))


def rank_neighbours(artifact_id: str, state, k: int) -> list[str]:
    """Deterministic neighbour ranking for connection problems. TODO(P2)."""
    raise NotImplementedError
