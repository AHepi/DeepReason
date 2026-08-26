"""The discharge channel's VERSIONED layer: kind declarations and policy presets.

Two registries, both declarations rather than wiring, in the shape
`DR-INV-signal-contract` establishes for signals:

- `DISCHARGE_KIND_DECLARATIONS` says what each way of discharging a criticism
  ASSERTS and what it must carry. A new kind enters HERE and reaches the wire
  schema, the submission screen and the pack render without any of them being
  edited -- which is what the operator's modularity law requires and what
  `tests/test_discharge_contract.py` makes failable.
- `DISCHARGE_POLICY_PRESETS` says how the channel behaves. `Config.DISCHARGE_
  POLICY` names one; the values inside a preset's envelope are the FREE layer.

The law this module may never cross is stated in `DR-CON-discharge-channel`:
discharge constrains how content is GENERATED, never what counts as EVIDENCE.
There is no numeric field on a declaration, so there is no rank or admission
weight for any configuration to set -- the formalism-optional guarantee
(`DR-CON-conjecture-kinds` R-g) made structural rather than promised.
"""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# The fields a declaration may require of a discharge. A kind that needs
# something outside this set is a WIRE change, not a declaration -- the honest
# edge of this module's modularity claim, stated rather than left to be
# discovered (SPEC.md A8, PARKED.md P3).
DECLARED_FIELDS = ("note", "where")


class UnknownDischargePolicyError(ValueError):
    """`Config.DISCHARGE_POLICY` names no registered preset.

    Typed at the point of USE, never at compile: an unreachable value is an
    impossibility where it is consumed, not a configuration that should have
    been refused (the all-configurations law).
    """


class UnknownDischargeKindError(ValueError):
    """A submission named a kind no declaration registers."""


class DischargeKindDeclaration(BaseModel):
    """One way of discharging a criticism, declared rather than wired.

    NO NUMERIC FIELD, and that absence is load-bearing: a rank, weight or
    score here would be the thing that lets a discharge reach adjudication,
    which is the one move the law line forbids. `tests/test_discharge_contract`
    pins the absence.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    # Producer-agnostic semantics: what discharging THIS way asserts. Never a
    # statement about who may use it or what it earns.
    asserts: str = Field(min_length=1)
    requires: tuple[str, ...] = Field(min_length=1)
    directive_line: str = Field(min_length=1)
    # Whether discharging this way registers an ordinary, attackable artifact
    # in the graph. True for `rebutted` because a rebuttal is a claim, and a
    # claim nobody can attack is not in the graph at all.
    attackable: bool = False

    @field_validator("requires")
    @classmethod
    def _within_the_declared_field_set(cls, value: tuple[str, ...]):
        unknown = sorted(set(value) - set(DECLARED_FIELDS))
        if unknown:
            raise ValueError(
                f"a kind may require only the declared fields "
                f"{list(DECLARED_FIELDS)}; got {unknown}"
            )
        return value


DISCHARGE_KIND_DECLARATIONS: dict[str, DischargeKindDeclaration] = {
    d.name: d
    for d in (
        DischargeKindDeclaration(
            name="revised",
            asserts="the candidate was changed in the respect the criticism named",
            requires=("note", "where"),
            directive_line=(
                "revised -- say WHAT changed and WHERE in the candidate"
            ),
        ),
        DischargeKindDeclaration(
            name="rebutted",
            asserts="the criticism itself fails, and the rebuttal says why",
            requires=("note",),
            directive_line=(
                "rebutted -- say why the criticism fails. Your rebuttal enters "
                "the record as an ordinary claim and can be attacked like any "
                "other"
            ),
            attackable=True,
        ),
        DischargeKindDeclaration(
            name="departure_declared",
            asserts=(
                "the candidate breaks with what the criticism presupposes, "
                "declared under the departure protocol"
            ),
            requires=("note",),
            directive_line=(
                "departure_declared -- say what you are breaking with. "
                "Declaring costs you nothing; nothing scores a departure"
            ),
        ),
    )
}

# DERIVED, never a second hand-maintained copy -- two copies of one fact is how
# a registry stops being a contract (`DR-INV-signal-contract`).
KINDS: dict[str, str] = {
    name: declaration.asserts
    for name, declaration in DISCHARGE_KIND_DECLARATIONS.items()
}


def discharge_kind_names() -> tuple[str, ...]:
    """Every declared kind, read LIVE from the registry.

    Live rather than snapshotted at import: a consumer holding a frozen copy
    would be a consumer that has to be edited when a kind is declared, which
    is the exact coupling this module exists to remove.
    """
    return tuple(DISCHARGE_KIND_DECLARATIONS)


def declaration(kind: str) -> DischargeKindDeclaration:
    try:
        return DISCHARGE_KIND_DECLARATIONS[kind]
    except KeyError:
        raise UnknownDischargeKindError(
            f"no discharge kind is declared as {kind!r}; declared: "
            f"{list(discharge_kind_names())}"
        ) from None


class DischargePolicyV1(BaseModel):
    """How the channel behaves for one run. A recorded artifact, not a knob bag.

    `kinds` empty means EVERY DECLARED KIND, so a newly declared kind is legal
    without this preset being edited. A preset that wants to narrow may list
    them; nothing in the tree does today.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_name: Literal["discharge-policy.v1"] = Field(
        default="discharge-policy.v1", alias="schema"
    )
    policy_id: str = Field(min_length=1)
    enabled: bool
    reask: Literal["once", "never"]
    disclose_undischarged: bool
    # How many open handles the pack shows. The cap is stated IN BAND wherever
    # it bites: an undisclosed cap is a silent truncation, which is the thing
    # `llm/packs.py::_allocate_sections` exists to abolish for its own sections.
    handles_n: int = Field(ge=0, le=64)
    claim_head_chars: int = Field(ge=0, le=4096)
    span_head_chars: int = Field(ge=0, le=4096)
    kinds: tuple[str, ...] = ()

    def kind_names(self) -> tuple[str, ...]:
        """The kinds legal under this policy, resolved against the live registry."""
        return self.kinds or discharge_kind_names()

    def policy_digest(self) -> str:
        payload = json.dumps(
            self.model_dump(mode="json", by_alias=True), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode()).hexdigest()


DISCHARGE_POLICY_PRESETS: dict[str, DischargePolicyV1] = {
    # The default. F1 ships the machinery; turning it on is a DEFAULT, and
    # defaults are F3's. With this in force nothing renders, nothing is
    # screened, and no pack byte, wire byte or label moves.
    "off": DischargePolicyV1(
        policy_id="off",
        enabled=False,
        reask="never",
        disclose_undischarged=False,
        handles_n=0,
        claim_head_chars=0,
        span_head_chars=0,
    ),
    # The channel Q5 describes: criticism in the working context, re-submission
    # requiring discharge. `reask="once"` is R4's own bound -- returned ONCE
    # with the open list, then ACCEPTED with a typed disclosure. Never a gate.
    "discharge-required.v1": DischargePolicyV1(
        policy_id="discharge-required.v1",
        enabled=True,
        reask="once",
        disclose_undischarged=True,
        handles_n=8,
        claim_head_chars=240,
        span_head_chars=160,
    ),
}


def resolve_policy(config) -> DischargePolicyV1:
    """The preset `Config.DISCHARGE_POLICY` names.

    Raises rather than defaulting: silently falling back to `off` would make a
    typo indistinguishable from a deliberate choice to disable the channel,
    and the operator would have no way to tell which run they got.
    """
    policy_id = getattr(config, "DISCHARGE_POLICY", "off")
    try:
        return DISCHARGE_POLICY_PRESETS[policy_id]
    except KeyError:
        raise UnknownDischargePolicyError(
            f"no discharge policy preset is registered as {policy_id!r}; "
            f"registered: {sorted(DISCHARGE_POLICY_PRESETS)}"
        ) from None
