"""Mini's own form registry — what a mini seat is ASKED FOR.

Implements S2 (R2, R7, R-stored, C1, C9) of the mini isolation programme.

A FORM is the output half of a seat ("a seat is a shell: its input and its
output define it", CLAUDE.md 2026-09-03). Forms are registered here BESIDE
each other, so selecting one is configuration rather than a code edit and the
stored default is never replaced by a relaxed one (R-stored).

WHY A MINI-ONLY REGISTRY AND NOT THE V6 CONTRACT LITERALS, and why selection
never reaches `Config` or the manifest: `run_manifest.py` dumps every `Config`
field into `engine_config_json` and `qualification.py` folds that into every
qualification subject digest, so an id declared there moves the digest of every
qualification bundle in the tree. Measured: adding one to
`ContractVersionPolicyV3` touches three of the five frozen surfaces; a registry
here touches none.

R2's "not limit prose length at all" is THREE limits. Two are here: no
`max_length` on any field of any mini form, and no required skeleton, so a
candidate that is one paragraph of prose is well formed. The third — the
truncation of what a seat is SHOWN — belongs to the brief, not to this module.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.wire import ReferenceFreeConjecturerWireContract, WireContract


MINI_FORM_ENV = "DEEPREASON_MINI_FORM"


class MiniFormError(ValueError):
    """A typed refusal about a form: unknown id, malformed selection."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


# ---------------------------------------------------------------------------
# The relaxed wire models.
#
# NO `max_length` ANYWHERE, and no required skeleton. `min_length=1` stays: an
# empty string is not a shorter answer, it is the absence of one, and the
# formalism-optional law protects informal content, not missing content.
# ---------------------------------------------------------------------------


class _MiniWireModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MiniRelaxedCandidate(_MiniWireModel):
    """One conjecture, in whatever shape the seat wants to say it."""

    content: str = Field(min_length=1)
    typicality: float = Field(default=0.5, ge=0.0, le=1.0)


class MiniRelaxedConjecturer(_MiniWireModel):
    candidates: list[MiniRelaxedCandidate] = Field(min_length=1)


class MiniObjection(_MiniWireModel):
    """One criticism. `about` names what it is about; `body` is free prose.

    It carries NO score, rank, weight, confidence or authority field. Shape may
    never buy standing (the formalism-optional law), and within mini a
    criticism overturns nothing at all (operator, 2026-09-05).
    """

    about: str = Field(min_length=1)
    body: str = Field(min_length=1)


class MiniCritic(_MiniWireModel):
    objections: list[MiniObjection] = Field(min_length=1)


class MiniCommitmentProposal(_MiniWireModel):
    """One proposed commitment. Its ONLY requirement is naming its conjecture.

    Everything else is free prose: no required fields, no schema beyond
    non-empty, no length bound. That is R4 in the operator's own words -- an
    artifact that "generates commitments on conjectures, but does not force a
    strict format".
    """

    about: str = Field(min_length=1)
    body: str = Field(min_length=1)


class MiniCommitmentProposals(_MiniWireModel):
    proposals: list[MiniCommitmentProposal] = Field(min_length=1)


# ---------------------------------------------------------------------------
# The registry.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MiniFormV1:
    """One registered form: a wire contract, keyed by id and versioned.

    It HOLDS its contract rather than subclassing one, so the stored default
    can be the shipped instance untouched -- "stored, not deleted" is a
    property of an object nobody wrapped, rewrote or re-derived.
    """

    form_id: str
    form_version: str
    contract: WireContract

    @property
    def wire_model(self) -> type[BaseModel]:
        return self.contract.wire_model

    @property
    def canonical_model(self) -> type:
        return self.contract.canonical_model

    @property
    def compile(self) -> Callable[[Any], Any]:
        return self.contract.compile


class _MiniRelaxedConjecturerContract(WireContract[ConjecturerOutput]):
    def __init__(self) -> None:
        super().__init__(
            "mini.conjecturer.relaxed.v1",
            MiniRelaxedConjecturer,
            ConjecturerOutput,
            variant="mini",
        )

    def compile(self, wire: MiniRelaxedConjecturer) -> ConjecturerOutput:
        from deepreason.llm.contracts import ConjectureCandidate

        return ConjecturerOutput(
            candidates=[
                ConjectureCandidate(content=item.content, typicality=item.typicality)
                for item in wire.candidates
            ]
        )


class _MiniPassthroughContract(WireContract):
    """A form whose canonical value IS its wire value.

    The critic's and the commitment seat's outputs have no parent canonical
    model to compile into, and inventing one would be inventing a second
    ontology -- the thing mini exists not to have. Their content is prose the
    record carries; nothing downstream reads a field of it.
    """

    def __init__(self, contract_id: str, model: type[BaseModel]) -> None:
        super().__init__(contract_id, model, model, variant="mini")

    def compile(self, wire):
        return wire


_REGISTRY: dict[str, MiniFormV1] = {}


def register_mini_form(form: MiniFormV1) -> MiniFormV1:
    """Add a form. Re-registering one id with different values is refused, for
    the reason every other registry here refuses it: an id names ONE form, or
    two runs citing it did not answer the same question."""

    existing = _REGISTRY.get(form.form_id)
    if existing is not None and existing != form:
        raise MiniFormError(
            "MINI_FORM_CONFLICT",
            f"form id {form.form_id!r} is already registered with different values",
        )
    _REGISTRY[form.form_id] = form
    return form


def mini_form_ids() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def resolve_mini_form(form_id: str) -> MiniFormV1:
    form = _REGISTRY.get(form_id)
    if form is None:
        raise MiniFormError(
            "MINI_FORM_UNKNOWN",
            f"no mini form {form_id!r}; registered: " + ", ".join(mini_form_ids()),
        )
    return form


def _environment_assignments(raw: str) -> dict[str, str]:
    """Parse `conjecturer=<id>,critic=<id>`.

    One process renders every seat, so a single-valued variable could not say
    which seat it meant. A malformed term is a TYPED REFUSAL naming it, never
    a silent fallback -- a configuration that quietly did nothing is the shape
    the all-configurations law calls a gate the operator cannot turn on.
    """

    assignments: dict[str, str] = {}
    for term in raw.split(","):
        term = term.strip()
        if not term:
            continue
        seat, separator, form_id = term.partition("=")
        if not separator or not seat.strip() or not form_id.strip():
            raise MiniFormError(
                "MINI_FORM_ASSIGNMENT_MALFORMED",
                f"{term!r} is not `<seat>=<form_id>` in {MINI_FORM_ENV}",
            )
        assignments[seat.strip()] = form_id.strip()
    return assignments


def select_mini_form(
    seat_id: str, form_id: str | None = None, *, default: str | None = None
) -> MiniFormV1:
    """Explicit argument, then `DEEPREASON_MINI_FORM`, then the caller's
    declared default. Resolved PER CALL rather than bound at import, so
    selecting a form takes effect without a restart.

    `default` is the FLOW's declared default once flows exist (S8); until then
    a caller states its own. There is no module-level fallback on purpose: a
    registry that guesses which form a seat wanted is a registry that can be
    wrong silently.
    """

    requested = form_id
    if requested is None:
        raw = os.environ.get(MINI_FORM_ENV) or ""
        if raw.strip():
            requested = _environment_assignments(raw).get(seat_id)
    if requested is None:
        requested = default
    if requested is None:
        raise MiniFormError(
            "MINI_FORM_NO_DEFAULT",
            f"no form selected for seat {seat_id!r} and no default declared; "
            "registered: " + ", ".join(mini_form_ids()),
        )
    return resolve_mini_form(requested)


# The STORED default is registered BESIDE the relaxed forms, never replaced by
# one (R-stored, operator 2026-09-05). It holds the shipped contract instance
# itself; `mini/tests/test_mini_forms.py` pins its rendered bytes.
register_mini_form(
    MiniFormV1(
        form_id="mini.conjecturer.legacy-v0",
        form_version="0.1.0",
        contract=ReferenceFreeConjecturerWireContract(),
    )
)
register_mini_form(
    MiniFormV1(
        form_id="mini.conjecturer.relaxed.v1",
        form_version="1.0.0",
        contract=_MiniRelaxedConjecturerContract(),
    )
)
register_mini_form(
    MiniFormV1(
        form_id="mini.critic.relaxed.v1",
        form_version="1.0.0",
        contract=_MiniPassthroughContract("mini.critic.relaxed.v1", MiniCritic),
    )
)
register_mini_form(
    MiniFormV1(
        form_id="mini.commitment.relaxed.v1",
        form_version="1.0.0",
        contract=_MiniPassthroughContract(
            "mini.commitment.relaxed.v1", MiniCommitmentProposals
        ),
    )
)


__all__ = [
    "MINI_FORM_ENV",
    "MiniCommitmentProposal",
    "MiniCommitmentProposals",
    "MiniCritic",
    "MiniFormError",
    "MiniFormV1",
    "MiniObjection",
    "MiniRelaxedCandidate",
    "MiniRelaxedConjecturer",
    "mini_form_ids",
    "register_mini_form",
    "resolve_mini_form",
    "select_mini_form",
]
