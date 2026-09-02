"""Which behavioural contract a legacy model phase needs before it may dispatch.

``Scheduler._defer_untransactional_v6_phase`` consults this table, so whether an
optional legacy model phase is completion debt or a dispatch is CONFIGURATION —
the manifest's own grants — rather than a constant.  Why it was a constant, and
what that cost, is `DR-SEAM-scheduler-x-workflow`'s Traps entry; the recipe for
converting a phase is `REC-give-a-legacy-phase-v6-transactional-dispatch.md`.

Two fields decide, and both are necessary:

``contract_ids``
    the seat must hold one of these in the manifest's
    ``route_seat_behavioral_capability_plan``.  Two ids per role because
    ``wire_contract_for`` resolves a contract from the SEAT's own base profile:
    ``compact`` yields ``*.compact.v1`` and ``standard``/``frontier`` yield
    ``*.direct.v1``.  A row naming only the direct id silently refuses every
    compact seat.

``dispatch``
    whether a transactional dispatch path has actually been WRITTEN for the
    phase.  A row still marked ``UNCONVERTED`` defers even when the grant is
    present, because letting it through would dispatch unbound and trip the very
    fail-closed guard the fence stands in for.  Converting a row is therefore a
    two-part change — this value and the phase's own dispatch — and
    ``docs/map/REC-give-a-legacy-phase-v6-transactional-dispatch.md`` is the
    recipe.

The table is READ ONLY of duck-typed attributes (``entries``, ``role``,
``seat``, ``contracts``, ``contract_id``).  It imports nothing from
``run_manifest``: that module is a frozen surface, and a reader that names none
of its internals cannot drift with them.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

LEGACY_PHASE_CONTRACTS_VERSION = "legacy-phase-contracts.v1"

TRANSACTIONAL = "v6_transactional"
UNCONVERTED = "unconverted"

_VARIATOR = frozenset({"variator.direct.v1", "variator.compact.v1"})
_JUDGE = frozenset({"judgeruling.direct.v1", "judgeruling.compact.v1"})
_CONJECTURER = frozenset({"conjecturer.turn.v6", "conjecturer.atomic-candidate.v1"})


@dataclass(frozen=True)
class LegacyPhaseContractRow:
    """One phase's authority requirement, keyed by the fence's own arguments."""

    phase: str
    role: str
    contract_ids: frozenset[str]
    dispatch: str


def _row(phase: str, role: str, contract_ids: frozenset[str], dispatch: str):
    return LegacyPhaseContractRow(
        phase=phase, role=role, contract_ids=contract_ids, dispatch=dispatch
    )


LEGACY_PHASE_CONTRACTS: Mapping[str, LegacyPhaseContractRow] = MappingProxyType(
    {
        row.phase: row
        for row in (
            _row("hv-spot-check", "variator", _VARIATOR, TRANSACTIONAL),
            # hv-floor is NOT a ranking measure: on `hv < hv_min` it mints a
            # demonstrative fail warrant, and `rules/spawn.py` pins its
            # criterion onto every connection problem — so converting it
            # changes what a run refutes.  Held at UNCONVERTED pending the
            # operator ruling that tranche 2026-09-02 stopped for.
            _row("hv-floor", "variator", _VARIATOR, UNCONVERTED),
            _row("premise-demarcation-variation", "variator", _VARIATOR, UNCONVERTED),
            _row("paraphrase-audit-variation", "variator", _VARIATOR, UNCONVERTED),
            _row("rubric-trial", "judge", _JUDGE, UNCONVERTED),
            _row("pairwise-discrimination", "judge", _JUDGE, UNCONVERTED),
            _row("paraphrase-audit-judgment", "judge", _JUDGE, UNCONVERTED),
            _row("property-relevance-trial", "judge", _JUDGE, UNCONVERTED),
            _row("experiment-generator-authoring", "conjecturer", _CONJECTURER, UNCONVERTED),
            # No compiler mints a behavioural grant for these two roles today,
            # so an empty set states "no contract can authorize this yet"
            # rather than guessing an id that would never match.
            _row("property-design", "property_designer", frozenset(), UNCONVERTED),
            _row("vision-criticism", "vision_critic", frozenset(), UNCONVERTED),
        )
    }
)


def granted_contract_ids(manifest, *, role: str, seat: int = 0) -> frozenset[str]:
    """Behavioural contracts the manifest grants one route seat.

    Absence-tolerant by construction: a manifest with no behavioural plan — a
    historical manifest, or a test fixture standing in for one — grants nothing
    rather than raising, so a caller cannot be made to choose between an
    exception and an unconditional answer.
    """

    plan = getattr(manifest, "route_seat_behavioral_capability_plan", None)
    if plan is None:
        return frozenset()
    return frozenset(
        contract.contract_id
        for entry in getattr(plan, "entries", ())
        if entry.role == role and entry.seat == seat
        for contract in getattr(entry, "contracts", ())
    )


def seat_may_dispatch_legacy_phase(
    manifest, *, phase: str, role: str, seat: int = 0
) -> bool:
    """Whether `phase` may reach a provider on this manifest's `role` seat.

    ``seat`` defaults to 0 because that is the seat the dispatch itself
    resolves (``adapter.bound_v6_default_lease(role, 0)``); a grant held by a
    seat the call will never reach is not authority for that call.
    """

    row = LEGACY_PHASE_CONTRACTS.get(phase)
    if row is None or row.role != role or row.dispatch != TRANSACTIONAL:
        return False
    if not row.contract_ids:
        return False
    return bool(row.contract_ids & granted_contract_ids(manifest, role=role, seat=seat))
