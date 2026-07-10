"""Isolation floor (spec §7 L2).

    conn(a) = #{accepted dependence edges a participates in}
    iso(a)  = max(0, FLOOR - conn(a))

iso(a) > 0 => Spawn a cheap connection problem against top-K neighbours
(rank: shared problem > shared refs > lexical/embedding overlap), under
INTEGRATION_BUDGET_SHARE. Emergent: raw uninterpreted data is maximally
isolated, so the same signal drives interpretation of numeric/opaque content.
"""

from collections.abc import Iterable

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology.commitment import Budget, Commitment
from deepreason.ontology.state import Status


def lineage_ref_commitment(endpoints: Iterable[str]) -> Commitment:
    """Program criterion pinned on connection problems (§7 L2): a candidate
    must carry a `dependence` ref into one of these lineage endpoints (the
    isolated node + its ranked neighbours). Content-addressed like hv-floor —
    the endpoint set is frozen into the id, so verdicts are replay-stable and
    retuning the neighbourhood only affects future instantiations."""
    ids = sorted({e for e in endpoints if e})
    digest = sha256_hex(canonical_json(ids))[:12]
    return Commitment(
        id=f"lineage-ref@{digest}",
        eval="program:lineage_ref",
        budget=Budget(extra={"endpoints": ",".join(ids)}),
    )


_RELATION_KINDS = ("depends on", "reduces to", "shares mechanism",
                   "shared mechanism", "compatible with", "inherits",
                   "integrates", "contradicts", "abstracts")
_RELATION_EXPR = (
    "'refuted if' in content.lower() and any(k in content.lower() for k in ("
    + ", ".join(repr(k) for k in _RELATION_KINDS) + "))"
)


def relation_form_commitment() -> Commitment:
    """Form gate for RELATION candidates (connection/integration problems):
    a relation must NAME its kind (dependence, reduction, shared mechanism,
    compatibility, inheritance, integration, contradiction, abstraction) and
    state a 'REFUTED IF' condition — the minimum that makes the asserted
    relation criticisable. A prose summary that merely restates its endpoints
    fails on form, mechanically, before any judge spends tokens (approved
    correction: the synthesizer is defective only when it staples artifacts
    together without proposing a testable relation)."""
    digest = sha256_hex(canonical_json(_RELATION_EXPR))[:12]
    return Commitment(id=f"relation-form@{digest}",
                      eval=f"predicate:{_RELATION_EXPR}")


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
