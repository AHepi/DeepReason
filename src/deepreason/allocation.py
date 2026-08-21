"""Allocation's view of the signal contract: seat instances, and the signals
the controller is allowed to read.

The operator's design law (CLAUDE.md, 2026-08-14) has three clauses this
module owns. Signals are keyed by SEAT INSTANCE, not role, because one
conjecturer may sit in "multiple structurally asymmetric seats that may need
throttling independently". The allocation controller consumes ONLY the signal
interface. And a topology that cannot produce a signal COMPILES, carrying a
typed open-loop notice.

Everything here is read-only over process facts and returns numbers, names or
booleans. Allocation touches EFFICIENCY, NEVER EVIDENCE: no function in this
module writes a status, a warrant or an edge, and `controller.py` reaches the
graph only through the two policy-status readers at the bottom -- which is the
whole point of their existing, since a consumer that knows contestation is
spelled `Status.REFUTED` has been taught about a subsystem.
"""

from deepreason.ontology import Status

# The separator between a role and its seat index. Chosen because no role name
# contains it, so `split_seat_instance` is total and needs no escape rule.
SEAT_MARK = "#"

# The only seat that emits an attack. Both contested statuses are downstream of
# one: REFUTED directly, SUSPENDED_UNSUPPORTED through the support cascade in
# adjudication/support.py, which orphans a dependent only after its supporter
# fell. A topology without this seat therefore cannot contest anything.
ATTACKING_ROLE = "argumentative_critic"

_CONTESTED = (Status.REFUTED, Status.SUSPENDED_UNSUPPORTED)


def seat_instance(role: str, seat: int, seats_bound: int) -> str:
    """The canonical name of one seat instance.

    A role bound to exactly ONE seat HAS one seat instance, and that instance's
    name is the bare role name -- the suffix appears only where there is more
    than one seat to tell apart. This is not an exception to seat-instance
    keying; it is what seat-instance keying spells for an ensemble of one, and
    it is why no knob and no Measure input changes spelling for any topology
    already in a committed root.
    """
    return role if seats_bound <= 1 else f"{role}{SEAT_MARK}{seat}"


def split_seat_instance(name: str) -> tuple[str, int | None]:
    """('conjecturer#1') -> ('conjecturer', 1); ('conjecturer') -> ('conjecturer', None).

    A `None` seat means "this name does not single out a seat", which is a
    different fact from "seat 0" and must stay distinguishable: the role form
    anchors to the role's widest route, the seat form to that seat's own.
    """
    role, mark, seat = name.partition(SEAT_MARK)
    if not mark or not seat.isdigit():
        return name, None
    return role, int(seat)


def cap_knob(instance: str) -> str:
    """The completion-cap knob for one seat instance."""
    return f"cap:{instance}"


def route_cap_for_knob(roles, knob: str) -> int | None:
    """The cap the run assigned this knob's seat instance, or None.

    The single derivation both the writer and replay validation must use: a
    steered cap only survives `verify_root` if the barrier is re-derived the
    same way it was written against, and two copies of this rule is how that
    stops being true.

    A ROLE-keyed knob answers with the role's WIDEST route, exactly as before
    seat keying existed. A SEAT-keyed knob answers with that seat's own route,
    which is what makes a narrow seat stay narrow while a wide sibling widens.
    """
    if not knob.startswith("cap:"):
        return None
    role, seat = split_seat_instance(knob[len("cap:"):])
    routes = tuple(roles.get(role) or ())
    if seat is not None:
        if seat >= len(routes):
            return None
        return getattr(routes[seat], "max_tokens", None)
    caps = [
        cap
        for route in routes
        if (cap := getattr(route, "max_tokens", None)) is not None
    ]
    return max(caps) if caps else None


# --- the policy-referenced signals, and whether a topology can produce them - #

# Every signal the allocation policy reads, by registry name. Declared in
# `signals.py` under the contract; named here so a topology can be asked
# whether it can produce each one. Adding a signal the policy reads without
# adding it here is what `test_every_policy_referenced_signal_is_declared`
# and the open-loop census exist to catch.
POLICY_SIGNALS: tuple[str, ...] = (
    "allocation.seat-truncation.v1",
    "allocation.seat-repair.v1",
    "dropped-call",
    "allocation.policy-authorized.v1",
    "allocation.policy-contested.v1",
)


def _has_any_seat(bound_roles) -> bool:
    return bool(tuple(bound_roles))


def _has_attacking_seat(bound_roles) -> bool:
    return ATTACKING_ROLE in set(bound_roles)


# One producer predicate per policy-referenced signal, decided from the BOUND
# ROLES alone so the same answer is available at compile time (from
# `manifest.roles`) and at attach time (from `adapter.endpoints`). Producer
# means "this topology contains something that can emit it", never "it did".
_PRODUCERS = {
    "allocation.seat-truncation.v1": _has_any_seat,
    "allocation.seat-repair.v1": _has_any_seat,
    "dropped-call": _has_any_seat,
    "allocation.policy-authorized.v1": _has_any_seat,
    "allocation.policy-contested.v1": _has_attacking_seat,
}

# What would close each loop. Stated per signal rather than inferred, because
# "no producer" without "and here is the seat that would be one" is a complaint
# rather than a disclosure.
_RESOLUTIONS = {
    "allocation.seat-truncation.v1": "bind at least one role to a route",
    "allocation.seat-repair.v1": "bind at least one role to a route",
    "dropped-call": "bind at least one role to a route",
    "allocation.policy-authorized.v1": "bind at least one role to a route",
    "allocation.policy-contested.v1": (
        f"bind the {ATTACKING_ROLE} role; without it no controller policy can "
        f"be attacked, so fail-static can never fire"
    ),
}


def open_loop_signals(bound_roles) -> tuple[str, ...]:
    """Policy-referenced signals this topology cannot produce, sorted.

    Empty is the ordinary answer and the one the configuration matrix asserts.
    A non-empty answer is a DISCLOSURE, never a refusal: the all-configurations
    law applied to allocation, so allocation runs open-loop on the named signal
    and says so.
    """
    roles = tuple(bound_roles)
    return tuple(
        sorted(
            signal
            for signal in POLICY_SIGNALS
            if not _PRODUCERS[signal](roles)
        )
    )


def open_loop_notices(bound_roles):
    """The same census as typed `CompileNoticeV1` values.

    `CompileNoticeV1` is imported HERE, at call time, rather than at module
    scope: the signal interface must stay importable without the manifest
    module, or a consumer that only reads signals acquires a dependency on the
    thing that compiles them. The type is reused verbatim and never modified --
    it is the established disclose-never-die pattern (all-configs-allowed,
    2026-08-16).
    """
    from deepreason.run_manifest import CompileNoticeV1

    return tuple(
        CompileNoticeV1(
            code="ALLOCATION_OPEN_LOOP",
            message=f"allocation open-loop for signal {signal}",
            pointer="/roles",
            resolution=_RESOLUTIONS[signal],
        )
        for signal in open_loop_signals(bound_roles)
    )


# --- the two policy-status signals, read here so the consumer need not ----- #


def policy_is_authorized(harness, artifact_id) -> bool:
    """`allocation.policy-authorized.v1`: this controller policy's limits are
    the ones currently in force.

    Efficiency, never evidence, and the direction matters: allocation READS an
    adjudication outcome about its OWN artifact to decide whether to keep its
    own limits. Nothing here writes a status, and no reading of it may reach
    another artifact's label.
    """
    return harness.state.status.get(artifact_id) == Status.ACCEPTED


def policy_is_contested(harness, artifact_id) -> bool:
    """`allocation.policy-contested.v1`: this controller policy is under an
    unresolved attack, so the controller must hold (fail-static).

    The spelling of contestation lives here and nowhere else. That is the whole
    migration: `controller.py` asks whether the signal is true, and never how
    the graph says so.
    """
    return harness.state.status.get(artifact_id) in _CONTESTED
