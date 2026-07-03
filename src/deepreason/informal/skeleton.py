"""Skeleton + forbidden cases (spec §10.1).

skeleton-wf (eval:program) passes iff the content parses as the skeleton
schema AND forbidden != []. At registration (before id computation) each
forbidden case compiles into a commitment in I(a): "if this case obtains, I
fail." Forbid nothing => fail skeleton-wf => refuted by a program.
"""

from pydantic import BaseModel, Field


class ForbiddenCase(BaseModel):
    case: str
    eval: str  # "rubric:<spec-id>" | "program:<ref>"
    observation_valued: bool = False


class Scope(BaseModel):
    covers: list[str] = Field(default_factory=list)
    excludes: list[str] = Field(default_factory=list)


class Skeleton(BaseModel):
    claim: str
    mechanism: str
    scope: Scope
    forbidden: list[ForbiddenCase]
    prose_notes: str | None = None  # rendered, never adjudicated


def skeleton_wf(content: bytes) -> str:
    """Commitment program: pass | fail. TODO(P5)."""
    raise NotImplementedError


def compile_forbidden(skeleton: Skeleton) -> list:
    """Compile forbidden cases into commitments (deterministic). TODO(P5)."""
    raise NotImplementedError
