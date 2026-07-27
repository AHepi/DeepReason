"""Commitment schema (spec §1, Def 3.1).

Verdict V(kappa, c) = U^{<=beta}(tau_kappa, c) in {pass, fail, overrun}:
extensional, budgeted, decidable. ``eval:rubric`` verdicts exist only
downstream of the trial guard (§3, §10); prefer program/predicate wherever
content is formal/numeric/code.
"""

from enum import Enum
from typing import Mapping

from pydantic import Field, field_validator

from deepreason.ontology.frozen import FrozenDict, FrozenRecord


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    OVERRUN = "overrun"


class Budget(FrozenRecord):
    """Structured budget interpreted by the test program tau_kappa.

    Canonical keys: steps, time_ms. Program evals may declare extended
    structured budgets (e.g. k, per_edit_steps for hv-floor, §7). Total
    resource is always finite and declared.
    """

    steps: int | None = 100_000
    time_ms: int | None = 2_000
    extra: Mapping[str, int | str] = Field(default_factory=FrozenDict)

    @field_validator("extra", mode="after")
    @classmethod
    def _freeze_extra(cls, value):
        return FrozenDict(value)


class Commitment(FrozenRecord):
    id: str
    # "program:<ref>" | "rubric:<spec-id>" | "predicate:<expr>"
    # rubric <spec-id> MUST resolve to a registered standard artifact (§10.3).
    eval: str
    budget: Budget = Field(default_factory=Budget)
    # True + no covering evidence artifact => Spawn research problem (§12).
    # Sealed holdout evidence does not count as covering pre-reveal (§10.5).
    observation_valued: bool = False
