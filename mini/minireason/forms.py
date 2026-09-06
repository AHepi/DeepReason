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
from typing import Any, Callable, Iterable

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
# The WRITER'S ROOM forms (operator, 2026-09-06: "permission to change the
# forms completely to fit the writers room - content brainstorming purpose").
#
# Each top-level model's docstring is its JSON-schema `description`, and the
# schema is prepended to the brief AFTER the call layer's clip -- so the
# seat's task is on the wire even if a brief were ever cut (the D8 root lost
# nine directives that way). Optional labels are free text, never validated
# against a list and never required: formalism is an option, not an
# obligation. Nothing here carries score, rank, weight, confidence, priority,
# authority or severity; nothing here changes a status (R5: the room is not
# the epistemology).
# ---------------------------------------------------------------------------


class MiniRoomCandidate(_MiniWireModel):
    """One conjecture: a bold, criticizable explanation, in whatever shape says
    the interesting part best. `angle` (optional, one line) names the stance
    or move this candidate takes so the room can tell its candidates apart."""

    content: str = Field(min_length=1)
    angle: str | None = None


class MiniRoomConjecturer(_MiniWireModel):
    """CONJECTURE SEAT. Propose the number of candidates the brief asks for,
    each a distinct, bold, criticizable explanation of the PROBLEM. Do not
    restate what the brief already shows; differ from it substantively.
    Candidates are content for criticism, not verdicts."""

    candidates: list[MiniRoomCandidate] = Field(min_length=1)


class MiniRoomObjection(_MiniWireModel):
    """One objection to the TARGET CONJECTURE. `about` is the target's id;
    `body` is the objection in free prose; `would_settle` (optional) says what
    observation or argument would settle it either way."""

    about: str = Field(min_length=1)
    body: str = Field(min_length=1)
    would_settle: str | None = None


class MiniRoomCritic(_MiniWireModel):
    """CRITIC SEAT. Mount the strongest specific objections to the TARGET
    CONJECTURE named in the brief -- each about that conjecture, each stating
    its case. You decide nothing: an objection is recorded and shown, and it
    overturns nothing."""

    objections: list[MiniRoomObjection] = Field(min_length=1)


class MiniRoomProposal(_MiniWireModel):
    """One proposed commitment for the TARGET CONJECTURE: what would refute
    it, what it forbids, what it must not do, or what it predicts. `about` is
    the target's id; `body` is the commitment in free prose; `kind`
    (optional, free text such as refuted-if / forbids / must-not / predicts)
    labels it. Not an answer to the problem: a hostage the conjecture gives."""

    about: str = Field(min_length=1)
    body: str = Field(min_length=1)
    kind: str | None = None


class MiniRoomProposals(_MiniWireModel):
    """COMMITMENT SEAT. Read the TARGET CONJECTURE and propose the commitments
    it should be held to: what would refute it, what it forbids, what it must
    not do, what it predicts. Each proposal names the target. A proposal is
    recorded, never enforced; do not answer the problem, bind the
    conjecture."""

    proposals: list[MiniRoomProposal] = Field(min_length=1)


def _labelled(body: str, label: str | None, name: str) -> str:
    """Keep an optional label WITH the prose it labels, appended so the prose
    is intact; the record holds one body per output."""

    return body if not label else f"{body}\n[{name}: {label}]"


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
    #: For a form whose canonical value is a list of RECORDS rather than
    #: conjecture candidates: how to read `(about, body)` pairs off it. None
    #: means the canonical value is the conjecture road's (`ConjecturerOutput`),
    #: which admission handles. The loop dispatches on this, never on a seat.
    records_of: Callable[[Any], Iterable[tuple[str, str]]] | None = None

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


class _MiniRoomConjecturerContract(WireContract[ConjecturerOutput]):
    def __init__(self) -> None:
        super().__init__(
            "mini.conjecturer.room.v1", MiniRoomConjecturer, ConjecturerOutput, variant="mini"
        )

    def compile(self, wire: MiniRoomConjecturer) -> ConjecturerOutput:
        from deepreason.llm.contracts import ConjectureCandidate

        return ConjecturerOutput(
            candidates=[
                # The canonical candidate carries a typicality; the room does
                # not ask for one, so every candidate compiles at the neutral
                # value -- no shape buys standing, and none is penalized.
                ConjectureCandidate(
                    content=_labelled(item.content, item.angle, "angle"), typicality=0.5
                )
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
        records_of=lambda out: [(item.about, item.body) for item in out.objections],
    )
)
register_mini_form(
    MiniFormV1(
        form_id="mini.commitment.relaxed.v1",
        form_version="1.0.0",
        contract=_MiniPassthroughContract(
            "mini.commitment.relaxed.v1", MiniCommitmentProposals
        ),
        records_of=lambda out: [(item.about, item.body) for item in out.proposals],
    )
)

register_mini_form(
    MiniFormV1(
        form_id="mini.conjecturer.room.v1",
        form_version="1.0.0",
        contract=_MiniRoomConjecturerContract(),
    )
)
register_mini_form(
    MiniFormV1(
        form_id="mini.critic.room.v1",
        form_version="1.0.0",
        contract=_MiniPassthroughContract("mini.critic.room.v1", MiniRoomCritic),
        records_of=lambda out: [
            (item.about, _labelled(item.body, item.would_settle, "would settle"))
            for item in out.objections
        ],
    )
)
register_mini_form(
    MiniFormV1(
        form_id="mini.commitment.room.v1",
        form_version="1.0.0",
        contract=_MiniPassthroughContract("mini.commitment.room.v1", MiniRoomProposals),
        records_of=lambda out: [
            (item.about, _labelled(item.body, item.kind, "kind")) for item in out.proposals
        ],
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
