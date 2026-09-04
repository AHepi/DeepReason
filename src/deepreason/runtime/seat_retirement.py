"""Which route seats this run has stood down, derived from the record.

The ONE derivation behind every consumer of a shrunk seat set: the scheduler's
school loop, the foreign-criticism batch resolution, the judge ensemble, the
results block. Two readers of the same record cannot disagree about which seats
are still usable if there is only one reader.

Why it exists: P-A1 (run 4565139800f5ca02) terminated `operational_failure`
because ONE seat, `conjecturer#1` on `ollama-glm-5.3`, exhausted its contract
ladder after a transport-fault streak. `conjecturer#0` had answered 30 attempts
with zero faults on a different endpoint, and all four of the run's criticism
bindings pointed at that healthy seat. The record already held the typed
per-seat fact; nothing read it, so one seat's death was the run's death.

Nothing here decides anything the record does not already hold. The exhaustion
trigger reads `RouteSeatInsufficientCapabilityV1`, minted per seat by the
transaction service; the transport trigger reads `provider_health.dead_seats`,
the shipped 2026-09-03 derivation. There is one transport classifier in this
repository and this module is not a second one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from deepreason.allocation import split_seat_instance

# The shipped policy, and the one value that turns retirement off. An unknown
# id falls back to the shipped default and discloses, never refuses: the
# all-configurations law (2026-08-12) applied to a policy selector, the same
# way `llm/transport_policy.py` applies it.
RETIREMENT_POLICIES = ("retire-dead-seats.v1", "off")
DEFAULT_RETIREMENT_POLICY = "retire-dead-seats.v1"

RETIRED_SIGNAL = "seat.retired.v1"
RETIREMENT_DISABLED_SIGNAL = "seat.retirement-disabled.v1"

# The operator's own warning text for turning the gate off, required by the
# ungated-seats law (2026-08-28): switching a gate off is never silent.
RETIREMENT_DISABLED_WARNING = (
    "seat retirement is off: one seat that exhausts its contract ladder or "
    "goes dead will end the whole run, including a run whose other seats are "
    "still answering"
)

TRIGGER_CONTRACT_EXHAUSTED = "contract_exhausted"
TRIGGER_PROVIDER_DEAD = "provider_dead"


@dataclass(frozen=True)
class SeatRetirement:
    """One seat stood down, and the durable fact that stood it down."""

    role: str
    seat: int
    endpoint_id: str
    trigger: str
    evidence: str

    @property
    def instance(self) -> str:
        return f"{self.role}#{self.seat}"

    def measure_inputs(self) -> list[str]:
        return [
            self.instance,
            self.endpoint_id,
            self.trigger,
            self.evidence,
        ]


def resolve_policy(config) -> tuple[str, str | None]:
    """(policy id, id it fell back from). Never raises, never refuses."""

    requested = str(getattr(config, "SEAT_RETIREMENT_POLICY", None) or "")
    if requested in RETIREMENT_POLICIES:
        return requested, None
    return DEFAULT_RETIREMENT_POLICY, (requested or None)


def _seat_of(instance: str, row: dict[str, Any], manifest) -> int | None:
    """Resolve a health key back to a seat index.

    `provider_health.seat_instance` spells a role the RECORD has observed on one
    seat as the bare role name, which does not say which seat that was. The
    endpoint the row carries does: it is the seat's own frozen route identity.
    """

    role, seat = split_seat_instance(instance)
    if seat is not None:
        return seat
    routes = getattr(manifest, "roles", {}).get(role, ()) if manifest else ()
    for index, route in enumerate(routes):
        if getattr(route, "endpoint_id", None) == row.get("endpoint_id"):
            return index
    return 0 if routes else None


def retired_seats(harness, config, manifest=None) -> dict[tuple[str, int], SeatRetirement]:
    """Every route seat this run has stood down, keyed (role, seat).

    Empty when the policy is off, which is what makes the switch a switch
    rather than a second code path: every consumer asks this one question and
    an off policy answers "none retired".
    """

    policy, _fallback = resolve_policy(config)
    if policy == "off":
        return {}

    retired: dict[tuple[str, int], SeatRetirement] = {}

    state = getattr(harness, "workflow_state", None)
    exhausted = getattr(state, "insufficient_capability_by_route_seat", {}) or {}
    for key, outcome in exhausted.items():
        role, seat, endpoint_id = key[0], int(key[1]), key[2]
        retired[(role, seat)] = SeatRetirement(
            role=role,
            seat=seat,
            endpoint_id=endpoint_id,
            trigger=TRIGGER_CONTRACT_EXHAUSTED,
            evidence=getattr(outcome, "id", "") or "",
        )

    threshold = int(getattr(config, "TRANSPORT_DEAD_SEAT_STREAK", 0) or 0)
    if threshold > 0:
        from deepreason.runtime.provider_health import dead_seats, seat_health

        health = seat_health(harness)
        for instance in dead_seats(health, threshold):
            row = health[instance]
            role, _mark = split_seat_instance(instance)
            seat = _seat_of(instance, row, manifest)
            if seat is None or (role, seat) in retired:
                # A seat already stood down for exhaustion keeps that trigger:
                # the exhaustion record is the stronger evidence and it names
                # the contract ladder the seat actually walked.
                continue
            retired[(role, seat)] = SeatRetirement(
                role=role,
                seat=seat,
                endpoint_id=row.get("endpoint_id") or "",
                trigger=TRIGGER_PROVIDER_DEAD,
                evidence=str(row.get("max_zero_byte_streak", 0)),
            )
    return retired


def live_seats(retired, role: str, configured: int) -> tuple[int, ...]:
    """Seat indices of `role` that are still dispatchable.

    `configured` is the CONFIGURED seat count and stays the configured count
    for the life of the run. Shrinking it would rename every seat instance
    mid-run -- `allocation.seat_instance` spells a one-seat role as the bare
    role name -- and a run's later rows would stop matching its earlier ones.
    """

    return tuple(
        seat for seat in range(configured) if (role, seat) not in retired
    )
