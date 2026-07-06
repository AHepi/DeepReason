"""Role output contracts (spec §9) — Pydantic models; the JSON schema shown
to the model is derived via model_json_schema().

The conjecturer contract is Verbalized Sampling (§11.6): a candidate
distribution with stated typicality estimates, never a single point.
"""

import json
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class CandidateRef(BaseModel):
    target: str
    role: Literal["dependence", "mention"] = "dependence"


class ConjectureCandidate(BaseModel):
    content: str
    # Stated probability/typicality estimate for this candidate (§11.6).
    typicality: float = Field(ge=0.0, le=1.0)
    # Born-connected (§7 L1): refs to neighbourhood artifacts where natural.
    refs: list[CandidateRef] = Field(default_factory=list)

    @field_validator("content", mode="before")
    @classmethod
    def _coerce_object_content(cls, value):
        # Models asked for skeleton content often emit the skeleton as a JSON
        # object instead of an embedded string — accept it canonically.
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True)
        return value


class ConjecturerOutput(BaseModel):
    candidates: list[ConjectureCandidate] = Field(min_length=1)


class ArgumentativeCriticOutput(BaseModel):
    attack: bool
    case: str = ""  # the argument; becomes the critic artifact's content


class BatchCase(BaseModel):
    """One target's entry in a batched criticism pass (§14 batching): the
    CALL is shared across targets, the case never is — each attacking entry
    becomes an ordinary per-target argumentative warrant with its own nu."""

    target: str  # must be an id listed in the pack; others are dropped
    attack: bool
    case: str = ""


class BatchCriticOutput(BaseModel):
    cases: list[BatchCase] = Field(default_factory=list)


class VariatorEdit(BaseModel):
    content: str


class VariatorOutput(BaseModel):
    """Bounded edits under mu / mu_struct (§6): role-level substitutions
    (mechanism, scope, causal link) for skeleton content, substantive local
    edits otherwise — never mere rewordings."""

    edits: list[VariatorEdit] = Field(min_length=1)


class SynthesizerOutput(BaseModel):
    """A proposed relation artifact (§9): content + the artifact ids it
    connects (rendered as dependence refs)."""

    relation: str
    connects: list[str] = Field(min_length=1)


class DefenderOutput(BaseModel):
    answer: str = Field(min_length=1)


class JudgeRuling(BaseModel):
    """Trial ruling (§3 guard): decisive_point MUST resolve to an actual
    element of the exchange — program-checked (referential integrity)."""

    verdict: Literal["fail", "pass"]
    decisive_point: str = Field(min_length=1)


class PairwiseRuling(BaseModel):
    """Pairwise discrimination (§10.2): A-beats-B-for-pi, never a global
    ranking. 'neither' registers nothing — the rivalry stands."""

    winner: Literal["A", "B", "neither"]
    decisive_point: str = ""


class ProseOutput(BaseModel):
    prose: str = Field(min_length=1)


class ThesisSection(BaseModel):
    """One section of a thesis argument; ``citations`` are pack artifact
    id prefixes (bracketed in the pack) — program-checked afterwards."""

    heading: str = Field(min_length=1)
    body: str = Field(min_length=1)
    citations: list[str] = Field(default_factory=list)


class ThesisRival(BaseModel):
    """A surviving rival position, stated fairly, with the concrete
    evidence or test that would discriminate it from the thesis."""

    artifact: str = ""  # pack id prefix ("" when positional)
    position: str = Field(min_length=1)
    discriminator: str = Field(min_length=1)


class ThesisOutput(BaseModel):
    """Committed thesis over a finished run's adjudicated record (§8 view):
    one defended position, argued from the pack ONLY."""

    thesis: str = Field(min_length=1)
    argument: list[ThesisSection] = Field(min_length=1)
    rebuttals: list[ThesisSection] = Field(default_factory=list)
    rivals: list[ThesisRival] = Field(default_factory=list)
    overturn: list[str] = Field(min_length=1)
