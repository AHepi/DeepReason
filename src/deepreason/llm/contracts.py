"""Role output contracts (spec §9) — Pydantic models; the JSON schema shown
to the model is derived via model_json_schema().

The conjecturer contract is Verbalized Sampling (§11.6): a candidate
distribution with stated typicality estimates, never a single point.
"""

from typing import Literal

from pydantic import BaseModel, Field


class CandidateRef(BaseModel):
    target: str
    role: Literal["dependence", "mention"] = "dependence"


class ConjectureCandidate(BaseModel):
    content: str
    # Stated probability/typicality estimate for this candidate (§11.6).
    typicality: float = Field(ge=0.0, le=1.0)
    # Born-connected (§7 L1): refs to neighbourhood artifacts where natural.
    refs: list[CandidateRef] = Field(default_factory=list)


class ConjecturerOutput(BaseModel):
    candidates: list[ConjectureCandidate] = Field(min_length=1)


class ArgumentativeCriticOutput(BaseModel):
    attack: bool
    case: str = ""  # the argument; becomes the critic artifact's content
