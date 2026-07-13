"""Deterministic attention decay derived from immutable records and events."""

from __future__ import annotations

import math
from collections import defaultdict, deque
from datetime import date

from deepreason.brain.models import MemoryPolicy, MemoryRecord
from deepreason.brain.store import BrainStore

EXPLICIT_USER_WEIGHT = 1.0
CANDIDATE_CITATION_WEIGHT = 0.25
PACK_ACCESS_WEIGHT = 0.05


def _calendar_age(query_day: date, event_day: date) -> int:
    return max(0, (query_day - event_day).days)


def _logical_age(query_seq: int, event_seq: int) -> int:
    return max(0, query_seq - event_seq)


def activation_strength(
    store: BrainStore,
    record: MemoryRecord | str,
    *,
    query_day: date | None = None,
    logical_seq: int | None = None,
    policy: MemoryPolicy | None = None,
) -> float:
    """Calculate attention strength without mutating the brain.

    Calendar mode requires an explicit query day.  Logical mode is available
    for synthetic tests and uses event sequence buckets in place of days.
    Future-dated/future-sequence events are not visible to the query.
    """

    if (query_day is None) == (logical_seq is None):
        raise ValueError("provide exactly one of query_day or logical_seq")
    memory = store.get_memory(record) if isinstance(record, str) else record
    return activation_strengths(
        store,
        (memory,),
        query_day=query_day,
        logical_seq=logical_seq,
        policy=policy,
    )[memory.id]


def activation_strengths(
    store: BrainStore,
    records: tuple[MemoryRecord, ...] | tuple[str, ...],
    *,
    query_day: date | None = None,
    logical_seq: int | None = None,
    policy: MemoryPolicy | None = None,
) -> dict[str, float]:
    """Calculate a bounded set of activations with one streaming log pass."""

    if (query_day is None) == (logical_seq is None):
        raise ValueError("provide exactly one of query_day or logical_seq")
    memories = tuple(store.get_memory(item) if isinstance(item, str) else item for item in records)
    declared = policy or MemoryPolicy()
    memory_by_id = {memory.id: memory for memory in memories}

    bases: dict[str, float] = {}
    pin_floors = {memory.id: memory.activation.pin_floor for memory in memories}
    weighted_events: dict[str, deque[tuple[int, float]]] = {
        memory.id: deque(maxlen=declared.reinforcement_event_limit) for memory in memories
    }
    access_counts: dict[tuple[str, object], int] = defaultdict(int)
    for memory in memories:
        if query_day is not None:
            base_age = _calendar_age(query_day, memory.provenance.created_day)
        else:
            base_age = _logical_age(logical_seq, memory.provenance.created_seq)  # type: ignore[arg-type]
        bases[memory.id] = memory.activation.base_strength * 2 ** (
            -base_age / memory.activation.half_life_days
        )

    from deepreason.brain.index import indexed_activation_events

    indexed = indexed_activation_events(store, store.manifest.root_digest, tuple(memory_by_id))
    event_source = store.iter_events() if indexed is None else indexed
    for event in event_source:
        if isinstance(event, dict):
            event_type = event["type"]
            event_day = date.fromisoformat(event["day"])
            event_seq = int(event["seq"])
            event_logical_seq = event.get("logical_seq")
            payload = event["payload"]
        else:
            event_type = event.type
            event_day = event.day
            event_seq = event.seq
            event_logical_seq = event.logical_seq
            payload = event.payload
        if logical_seq is not None:
            event_bucket = event_logical_seq if event_logical_seq is not None else event_seq
            if event_bucket > logical_seq:
                continue
            age = _logical_age(logical_seq, event_bucket)
            access_bucket: object = event_bucket
        else:
            if event_day > query_day:  # type: ignore[operator]
                continue
            age = _calendar_age(query_day, event_day)  # type: ignore[arg-type]
            access_bucket = event_day

        record_id = payload.get("record_id")
        if event_type == "Reinforce" and record_id in memory_by_id:
            reason = payload.get("reason")
            if reason == "explicit_user":
                weight = EXPLICIT_USER_WEIGHT
            elif reason == "candidate_citation":
                weight = CANDIDATE_CITATION_WEIGHT
            else:
                # Unknown and outcome-based reasons are never silently granted weight.
                weight = 0.0
            weighted_events[record_id].append((age, weight))
        elif event_type == "Access":
            for accessed_id in payload.get("record_ids", ()):
                if accessed_id not in memory_by_id:
                    continue
                key = (accessed_id, access_bucket)
                if access_counts[key] < declared.automatic_access_per_day:
                    weighted_events[accessed_id].append((age, PACK_ACCESS_WEIGHT))
                    access_counts[key] += 1
        elif record_id in memory_by_id:
            if event_type == "Pin":
                pin_floors[record_id] = float(payload.get("floor", 1.0))
            elif event_type == "Unpin":
                pin_floors[record_id] = memory_by_id[record_id].activation.pin_floor

    result: dict[str, float] = {}
    for memory in memories:
        reinforcement = sum(
            weight * 2 ** (-age / memory.activation.half_life_days)
            for age, weight in weighted_events[memory.id]
        )
        strength = max(
            pin_floors[memory.id],
            min(declared.strength_cap, bases[memory.id] + reinforcement),
        )
        if not math.isfinite(strength):
            raise ValueError("non-finite memory activation")
        result[memory.id] = strength
    return result


def normalized_strength_ppm(strength: float, policy: MemoryPolicy) -> int:
    return max(0, min(1_000_000, round(strength / policy.strength_cap * 1_000_000)))
