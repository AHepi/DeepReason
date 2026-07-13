"""Receipt construction for replayable, external-brain-free prompts."""

from __future__ import annotations

from deepreason.brain.models import CandidateScore, RetrievalReceipt
from deepreason.brain.store import BrainStore
from deepreason.canonical import canonical_json, sha256_hex


def make_inclusion_proofs(store: BrainStore, record_ids: tuple[str, ...]) -> str:
    from deepreason.brain.index import indexed_record_events

    indexed = indexed_record_events(store, store.manifest.root_digest, record_ids)
    if indexed is None:
        events_by_record: dict[str, list[dict[str, object]]] = {
            record_id: [] for record_id in record_ids
        }
        for event in store.iter_events():
            direct = event.payload.get("record_id")
            if isinstance(direct, str) and direct in events_by_record:
                events_by_record[direct].append({"seq": event.seq, "digest": event.digest})
    else:
        events_by_record = {
            record_id: list(events) for record_id, events in indexed.items()
        }
    proofs = {
        "schema": "deepreason-brain-inclusion-proofs-v1",
        "root_digest": store.manifest.root_digest,
        "records": {},
    }
    for record_id in record_ids:
        record_bytes = store._object_path(record_id).read_bytes()
        proofs["records"][record_id] = {  # type: ignore[index]
            "object_sha256": sha256_hex(record_bytes),
            "content_ref": store.get_memory(record_id).content_ref,
            "events": events_by_record[record_id],
        }
    return store.put_blob(canonical_json(proofs))


def make_receipt(
    store: BrainStore,
    *,
    root_digest: str,
    normalized_query: str,
    query_bucket: str,
    policy_digest: str,
    candidates: tuple[CandidateScore, ...],
    selected: tuple[str, ...],
    expanded: tuple[str, ...],
) -> RetrievalReceipt:
    proof_ref = make_inclusion_proofs(store, selected)
    return RetrievalReceipt.create(
        brain_id=store.manifest.brain_id,
        root_digest=root_digest,
        index_version=store.manifest.index_version,
        card_version=store.manifest.card_version,
        query=normalized_query,
        query_day=query_bucket,
        policy_digest=policy_digest,
        candidate_pool=candidates,
        selected=selected,
        expanded=expanded,
        merkle_proofs_ref=proof_ref,
    )
