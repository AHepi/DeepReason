"""Event schema (spec §1) — the source of truth, append-only JSONL.

Graph state is a materialized view; recompute from the log at any ``seq``
for time-travel. Embedder calls are logged exactly like any other role
(prompt/input ref + raw output ref) so every §11.3 diagnostic is
replay-deterministic.
"""

from enum import Enum

from pydantic import BaseModel, Field


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


class LLMCall(BaseModel):
    role: str
    model: str
    endpoint: str
    prompt_ref: str  # blob
    raw_ref: str  # blob — replay consumes logged raws (§0)
    tokens: int = 0
    ms: int = 0
    attempts: int = 1  # completions consumed incl. schema repairs (P6 valid-JSON rate)


class StateDiff(BaseModel):
    att_add: list[tuple[str, str]] = Field(default_factory=list, alias="att+")
    dep_add: list[tuple[str, str]] = Field(default_factory=list, alias="dep+")
    a_add: list[str] = Field(default_factory=list, alias="A+")
    pi_add: list[str] = Field(default_factory=list, alias="Π+")
    status_changed: list[str] = Field(default_factory=list)
    # Measure-rule payloads (§6): estimates recorded in the event so replay
    # applies them without re-running the variator (raws are logged too).
    hv_set: dict[str, float] = Field(default_factory=dict)
    reach_set: dict[str, float] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class Event(BaseModel):
    seq: int
    ts: str  # iso8601
    rule: Rule
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    llm: LLMCall | None = None
    state_diff: StateDiff = Field(default_factory=StateDiff)
