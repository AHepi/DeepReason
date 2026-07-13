"""Bounded deterministic hybrid retrieval with a fixed exploration lane."""

from __future__ import annotations

import math
from datetime import date

from deepreason.brain.activation import activation_strengths, normalized_strength_ppm
from deepreason.brain.cards import load_card
from deepreason.brain.index import (
    build_index,
    candidate_ids,
    card_text,
    collections,
    cosine,
    graph_neighbors,
    hashed_vector,
    normalize_query,
    tokens,
)
from deepreason.brain.models import CandidateScore, MemoryPolicy, RetrievalResult
from deepreason.brain.receipts import make_receipt
from deepreason.brain.store import BrainStore
from deepreason.canonical import sha256_hex


def _ppm(value: float) -> int:
    return max(0, min(1_000_000, round(value * 1_000_000)))


def _novelty_ppm(root: str, query: str, record_id: str) -> int:
    digest = sha256_hex(f"{root}\0{query}\0{record_id}".encode())
    return int(digest[:12], 16) * 1_000_000 // (16**12 - 1)


def _weighted_score(policy: MemoryPolicy, components: tuple[int, int, int, int, int]) -> int:
    weights = (
        policy.lexical_weight_ppm,
        policy.vector_weight_ppm,
        policy.graph_weight_ppm,
        policy.strength_weight_ppm,
        policy.novelty_weight_ppm,
    )
    return sum(weight * component for weight, component in zip(weights, components, strict=True)) // 1_000_000


def _quota_select(
    ordered: list[str],
    collection_by_id: dict[str, str],
    *,
    limit: int,
    quota: int,
    excluded: set[str] | None = None,
) -> list[str]:
    if limit <= 0:
        return []
    selected: list[str] = []
    blocked = excluded or set()
    counts: dict[str, int] = {}
    for record_id in blocked:
        collection = collection_by_id.get(record_id, "unfiled")
        counts[collection] = counts.get(collection, 0) + 1
    for record_id in ordered:
        if record_id in blocked:
            continue
        collection = collection_by_id.get(record_id, "unfiled")
        if counts.get(collection, 0) >= quota:
            continue
        selected.append(record_id)
        counts[collection] = counts.get(collection, 0) + 1
        if len(selected) >= limit:
            break
    return selected


def retrieve(
    store: BrainStore,
    query: str,
    *,
    query_day: date | None = None,
    logical_seq: int | None = None,
    policy: MemoryPolicy | None = None,
    record_access: bool = True,
) -> RetrievalResult:
    """Retrieve advisory memory; no ontology or evidence API is touched."""

    if (query_day is None) == (logical_seq is None):
        raise ValueError("provide exactly one of query_day or logical_seq")
    declared = policy or MemoryPolicy()
    normalized = normalize_query(query)
    if not normalized:
        raise ValueError("memory query has no searchable terms")

    build_index(store)
    root = store.manifest.root_digest
    lexical_hits, vector_hits = candidate_ids(
        store,
        root,
        normalized,
        limit=declared.candidate_pool_limit,
        posting_limit=declared.posting_read_limit,
    )
    initial = sorted(
        set(lexical_hits) | set(vector_hits),
        key=lambda record_id: (
            -lexical_hits.get(record_id, 0),
            -vector_hits.get(record_id, 0),
            record_id,
        ),
    )[: declared.candidate_pool_limit]
    neighbors = graph_neighbors(
        store,
        root,
        initial[: declared.graph_seed_limit],
        limit=max(0, declared.candidate_pool_limit - len(initial)),
    )
    candidate_order = list(dict.fromkeys((*initial, *neighbors)))[: declared.candidate_pool_limit]
    neighbor_set = set(neighbors)
    query_terms = set(tokens(normalized))
    query_vector = hashed_vector(normalized)

    scores: dict[str, CandidateScore] = {}
    strengths = activation_strengths(
        store,
        tuple(candidate_order),
        query_day=query_day,
        logical_seq=logical_seq,
        policy=declared,
    )
    relevance: dict[str, int] = {}
    for record_id in candidate_order:
        card = load_card(store, root, record_id)
        candidate_terms = set(tokens(card_text(card)))
        union = query_terms | candidate_terms
        lexical = _ppm(len(query_terms & candidate_terms) / len(union)) if union else 0
        vector = _ppm(cosine(query_vector, hashed_vector(card_text(card))))
        graph = 1_000_000 if record_id in neighbor_set else 0
        strength = strengths[record_id]
        strength_ppm = normalized_strength_ppm(strength, declared)
        novelty = _novelty_ppm(root, normalized, record_id)
        score = _weighted_score(declared, (lexical, vector, graph, strength_ppm, novelty))
        scores[record_id] = CandidateScore(
            id=record_id,
            lexical_ppm=lexical,
            vector_ppm=vector,
            graph_ppm=graph,
            strength_ppm=strength_ppm,
            score_ppm=score,
        )
        relevance[record_id] = lexical + vector + graph

    ranked = sorted(scores, key=lambda record_id: (-scores[record_id].score_ppm, record_id))
    exploration_count = min(
        declared.selected_limit,
        math.ceil(declared.selected_limit * declared.exploration_ppm / 1_000_000),
    )
    exploitation_count = declared.selected_limit - exploration_count
    collection_by_id = collections(store, root, candidate_order)
    selected = _quota_select(
        ranked,
        collection_by_id,
        limit=exploitation_count,
        quota=declared.collection_quota,
    )
    # Relevant low-strength memories receive a deterministic lane.  Novelty is
    # the final tie-break, never a learned downstream-success signal.
    exploration_order = sorted(
        scores,
        key=lambda record_id: (
            -relevance[record_id],
            scores[record_id].strength_ppm,
            -_novelty_ppm(root, normalized, record_id),
            record_id,
        ),
    )
    selected.extend(
        _quota_select(
            exploration_order,
            collection_by_id,
            limit=exploration_count,
            quota=declared.collection_quota,
            excluded=set(selected),
        )
    )
    # Fill spare lane capacity while retaining the declared collection quota.
    selected.extend(
        _quota_select(
            ranked,
            collection_by_id,
            limit=declared.selected_limit - len(selected),
            quota=declared.collection_quota,
            excluded=set(selected),
        )
    )
    selected_tuple = tuple(selected)

    cards = tuple(load_card(store, root, record_id) for record_id in selected_tuple)
    bodies: dict[str, bytes] = {}
    used_bytes = 0
    for record_id in selected_tuple:
        if len(bodies) >= declared.expanded_limit:
            break
        body = store.get_blob(store.get_memory(record_id).content_ref)
        if used_bytes + len(body) > declared.body_byte_limit:
            continue
        bodies[record_id] = body
        used_bytes += len(body)
    expanded = tuple(bodies)

    candidate_receipt = tuple(
        scores[record_id]
        for record_id in sorted(scores, key=lambda item: (-scores[item].score_ppm, item))
    )
    bucket = query_day.isoformat() if query_day is not None else f"logical:{logical_seq}"
    receipt = make_receipt(
        store,
        root_digest=root,
        normalized_query=normalized,
        query_bucket=bucket,
        policy_digest=declared.digest,
        candidates=candidate_receipt,
        selected=selected_tuple,
        expanded=expanded,
    )
    result = RetrievalResult(
        receipt=receipt,
        cards=cards,
        bodies=bodies,
        activation={
            record_id: scores[record_id].strength_ppm / 1_000_000
            for record_id in selected_tuple
        },
    )
    if record_access:
        store.record_access(
            selected_tuple,
            event_day=query_day or store.manifest.created_at.date(),
            logical_seq=logical_seq,
        )
    return result
