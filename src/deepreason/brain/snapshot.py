"""Copy the bounded retrieval closure into a run-local blob store."""

from __future__ import annotations

from typing import Protocol

from deepreason.brain.models import (
    MemoryCard,
    RetrievalReceipt,
    RetrievalResult,
    RunLocalBrainSnapshot,
)
from deepreason.brain.store import BrainStore
from deepreason.canonical import canonical_json


class BlobStoreLike(Protocol):
    def put(self, data: bytes) -> str: ...

    def get(self, ref: str) -> bytes: ...


def snapshot_retrieval(
    store: BrainStore, result: RetrievalResult, run_blobs: BlobStoreLike
) -> RunLocalBrainSnapshot:
    receipt_ref = run_blobs.put(canonical_json(result.receipt.model_dump(mode="json")))
    proof_bytes = store.get_blob(result.receipt.merkle_proofs_ref)
    proof_ref = run_blobs.put(proof_bytes)
    card_refs: dict[str, str] = {}
    record_refs: dict[str, str] = {}
    body_refs: dict[str, str] = {}
    referenced: set[str] = {proof_ref}
    for card in result.cards:
        card_refs[card.record_id] = run_blobs.put(canonical_json(card.model_dump(mode="json")))
        record = store.get_memory(card.record_id)
        record_refs[card.record_id] = run_blobs.put(
            canonical_json(record.model_dump(mode="json"))
        )
        if record.summary_ref is not None:
            referenced.add(run_blobs.put(store.get_blob(record.summary_ref)))
    for record_id, body in result.bodies.items():
        body_refs[record_id] = run_blobs.put(body)
    referenced.update(body_refs.values())
    return RunLocalBrainSnapshot(
        receipt_ref=receipt_ref,
        proof_ref=proof_ref,
        card_refs=card_refs,
        record_refs=record_refs,
        body_refs=body_refs,
        referenced_blob_refs=tuple(sorted(referenced)),
    )


def replay_snapshot(snapshot: RunLocalBrainSnapshot, run_blobs: BlobStoreLike) -> RetrievalResult:
    """Recreate prompt material using only pinned run bytes."""

    receipt = RetrievalReceipt.model_validate_json(run_blobs.get(snapshot.receipt_ref))
    if receipt.merkle_proofs_ref != snapshot.proof_ref:
        raise ValueError("snapshot proof does not match retrieval receipt")
    run_blobs.get(snapshot.proof_ref)
    cards = tuple(
        MemoryCard.model_validate_json(run_blobs.get(snapshot.card_refs[record_id]))
        for record_id in receipt.selected
    )
    bodies = {
        record_id: run_blobs.get(snapshot.body_refs[record_id]) for record_id in receipt.expanded
    }
    activation = {
        candidate.id: candidate.strength_ppm / 1_000_000
        for candidate in receipt.candidate_pool
        if candidate.id in receipt.selected
    }
    return RetrievalResult(receipt=receipt, cards=cards, bodies=bodies, activation=activation)
