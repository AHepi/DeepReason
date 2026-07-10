"""Event schema (spec §1) — the source of truth, append-only JSONL.

Graph state is a materialized view; recompute from the log at any ``seq``
for time-travel. Embedder calls are logged exactly like any other role
(prompt/input ref + raw output ref) so every §11.3 diagnostic is
replay-deterministic.
"""

from enum import Enum
from typing import Mapping

from pydantic import ConfigDict, Field, field_validator

from deepreason.ontology.frozen import FrozenDict, FrozenList, FrozenRecord


class Rule(str, Enum):
    CONJ = "Conj"
    CRIT = "Crit"
    ADJ = "Adj"
    SPAWN = "Spawn"
    REFL = "Refl"
    REGISTER = "Register"
    MERGE = "Merge"
    MEASURE = "Measure"
    REVEAL = "Reveal"
    RESEED = "Reseed"


class LLMCall(FrozenRecord):
    role: str
    model: str
    endpoint: str
    prompt_ref: str  # blob
    raw_ref: str  # blob — replay consumes logged raws (§0)
    tokens: int = 0
    ms: int = 0
    attempts: int = 1  # completions consumed incl. schema repairs (P6 valid-JSON rate)
    # A pure PROCESS signal (not outcome): did any attempt in this call hit the
    # completion length limit? Read by the self-calibration controller
    # (controller.py) to widen caps; default False keeps old events replayable.
    truncated: bool = False
    # Mean token surprisal (-mean logprob) of the final completion, when the
    # endpoint returns logprobs. A token-level uncertainty signal that stays
    # informative even when response-level diversity collapses — the
    # decoupling reported in docs/research (alignment tax): detection §11.3.
    mean_surprisal: float | None = None


class StateDiff(FrozenRecord):
    att_add: list[tuple[str, str]] = Field(default_factory=FrozenList, alias="att+")
    dep_add: list[tuple[str, str]] = Field(default_factory=FrozenList, alias="dep+")
    a_add: list[str] = Field(default_factory=FrozenList, alias="A+")
    pi_add: list[str] = Field(default_factory=FrozenList, alias="Π+")
    status_changed: list[str] = Field(default_factory=FrozenList)
    # Measure-rule payloads (§6): estimates recorded in the event so replay
    # applies them without re-running the variator (raws are logged too).
    hv_set: Mapping[str, float] = Field(default_factory=FrozenDict)
    reach_set: Mapping[str, float] = Field(default_factory=FrozenDict)
    # Normative amendment (reach, Def 3.7): a FULL reach hit - genuine
    # cross-problem survival of another problem's non-trivial battery -
    # registers the artifact as ADDRESSING that problem. Carried in the
    # event so replay applies it without re-running the sweep.
    addr_add: list[tuple[str, str]] = Field(default_factory=FrozenList, alias="addr+")
    # Append-only warrant carriage. Kept out of Artifact.compute_id so an
    # artifact remains the same content object when it packages more than one
    # attack; old events remain compatible through the default empty list.
    carry_add: list[tuple[str, str]] = Field(default_factory=FrozenList, alias="carry+")

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    @field_validator("hv_set", "reach_set", mode="after")
    @classmethod
    def _freeze_maps(cls, value):
        return FrozenDict(value)

    @field_validator(
        "att_add", "dep_add", "a_add", "pi_add", "status_changed", "addr_add",
        "carry_add", mode="after",
    )
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)


class Event(FrozenRecord):
    seq: int
    ts: str  # iso8601
    rule: Rule
    inputs: list[str] = Field(default_factory=FrozenList)
    outputs: list[str] = Field(default_factory=FrozenList)
    llm: LLMCall | None = None
    state_diff: StateDiff = Field(default_factory=StateDiff)

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)
