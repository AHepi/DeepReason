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


def rank_neighbours(artifact_id: str, harness, k: int) -> list[str]:
    """Deterministic top-K neighbours for a connection problem — rank by
    shared problem > shared refs > lexical overlap (§7 L2)."""
    from deepreason.programs import content_text

    state = harness.state
    addressed: dict[str, set[str]] = {}
    for aid, pid in state.addr:
        addressed.setdefault(aid, set()).add(pid)
    my_problems = addressed.get(artifact_id, set())
    me = state.artifacts[artifact_id]
    my_refs = {r.target for r in me.interface.refs}
    my_tokens = set(content_text(me, harness.blobs).lower().split())
    scored: list[tuple[float, str]] = []
    for other_id in addressed:
        if other_id == artifact_id or state.status.get(other_id) != Status.ACCEPTED:
            continue
        other = state.artifacts[other_id]
        other_refs = {r.target for r in other.interface.refs}
        other_tokens = set(content_text(other, harness.blobs).lower().split())
        overlap = (
            len(my_tokens & other_tokens) / len(my_tokens | other_tokens)
            if my_tokens | other_tokens
            else 0.0
        )
        score = (
            10.0 * len(my_problems & addressed[other_id])
            + 3.0 * len(my_refs & (other_refs | {other_id}))
            + overlap
        )
        scored.append((-score, other_id))
    return [oid for _, oid in sorted(scored)[:k]]
