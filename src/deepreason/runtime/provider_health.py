"""Per-seat provider health, derived from the append-only record.

The ONE derivation behind both operator-facing surfaces — `progress.jsonl`, which
a monitor tails, and `deepreason results`, which is the single retrieval surface.
Two readers of the same record cannot disagree about a run's provider condition
if there is only one reader.

Why it exists: P-S1 (run 9e48a36b1dec91ee) ran 15 of its 24 cycles against a dead
provider with 54 typed transport failures, and not one of its 13 summary
documents said so — the dead cycles were reported as a milestone MET. P-A1 (run
4565139800f5ca02) repeated it, and the monitor written for that exact signature
raised 0 alerts on 40 faults because it tested keys the attempt trace does not
carry. The record held the receipts the whole time; nothing published them.
"""

from __future__ import annotations

from typing import Any

from deepreason.allocation import seat_instance
from deepreason.llm.transport_policy import classify


def _blank(endpoint_id: str, model: str) -> dict[str, Any]:
    return {
        "endpoint_id": endpoint_id,
        "model": model,
        "calls": 0,
        "attempts": 0,
        "faults": 0,
        "zero_byte_returns": 0,
        "last_fault_kind": None,
        "max_zero_byte_streak": 0,
        "fault_ms": 0,
    }


def seat_health(harness) -> dict[str, dict[str, Any]]:
    """Provider health per seat instance, or an empty map if none was recorded.

    Keyed by `allocation.seat_instance`, the convention the signal contract
    already uses, so a later consumer does not meet a second spelling of a seat.
    """

    by_role_seat: dict[tuple[str, int], dict[str, Any]] = {}
    streaks: dict[tuple[str, int], int] = {}
    seats_by_role: dict[str, set[int]] = {}
    for event in harness.log.read():
        call = getattr(event, "llm", None)
        if call is None:
            continue
        for attempt in call.attempt_trace or ():
            key = (call.role, int(getattr(attempt, "seat", 0) or 0))
            seats_by_role.setdefault(call.role, set()).add(key[1])
            row = by_role_seat.setdefault(
                key, _blank(getattr(attempt, "endpoint_id", "") or "", call.model)
            )
            row["calls"] += 1
            row["attempts"] += max(1, int(getattr(attempt, "transport_attempts", 1) or 1))
            diagnostics = list(getattr(attempt, "transport_diagnostics", ()) or ())
            if not diagnostics:
                streaks[key] = 0
                continue
            row["faults"] += 1
            row["fault_ms"] += int(getattr(attempt, "ms", 0) or 0)
            row["last_fault_kind"] = classify(diagnostics[-1])
            if not getattr(attempt, "tokens", 0):
                row["zero_byte_returns"] += 1
                streaks[key] = streaks.get(key, 0) + 1
                row["max_zero_byte_streak"] = max(
                    row["max_zero_byte_streak"], streaks[key]
                )
            else:
                streaks[key] = 0
    return {
        seat_instance(role, seat, len(seats_by_role.get(role, ()))): row
        for (role, seat), row in sorted(by_role_seat.items())
    }


def dead_seats(health: dict[str, dict[str, Any]], streak_threshold: int) -> list[str]:
    """Seat instances whose consecutive zero-byte returns reached the threshold.

    Disclose, never die: the caller emits a typed notice. Nothing here stops a
    run or stands a seat down (operator disposition 2026-09-03, road A).
    """

    if streak_threshold <= 0:
        return []
    return sorted(
        instance
        for instance, row in health.items()
        if row["max_zero_byte_streak"] >= streak_threshold
    )
