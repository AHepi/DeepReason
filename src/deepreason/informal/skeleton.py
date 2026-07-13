"""Skeleton + forbidden cases (spec §10.1).

skeleton-wf (eval:program) passes iff the content parses as the skeleton
schema AND forbidden != []. At registration — before id computation, so
deterministically — each forbidden case compiles into a commitment in
I(a): "if this case obtains, I fail." Forbid nothing => fail skeleton-wf
=> refuted by a program: demarcation made real (§6). Prose is a §8 view.
D2 intact: this constrains what survives, not what gamma may emit.

Not a type: skeleton-ness is a content convention keyed on whether the
bytes parse; the discipline enters through problem criteria.
"""

import json

from pydantic import BaseModel, Field, ValidationError, field_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology import Commitment
from deepreason.ontology.commitment import Budget

SKELETON_WF_ID = "skeleton-wf"


class ForbiddenCase(BaseModel):
    case: str = Field(min_length=1)
    eval: str  # "rubric:<spec-id>" | "program:<ref>"
    observation_valued: bool = False

    @field_validator("eval")
    @classmethod
    def _eval_kind_is_safe(cls, v: str) -> str:
        """SECURITY (stress-campaign RCE): forbidden cases come from
        UNTRUSTED skeleton content (LLM output). Their eval string is
        copied verbatim into a registered Commitment and can reach
        programs.evaluate. A `predicate:` here would put attacker-
        controlled text into an eval() — arbitrary code execution via the
        object-subclasses walk. Untrusted forbidden cases may ONLY name a
        rubric standard (judged via the trial protocol) or a known safe
        program; never an inline predicate. A skeleton with any other eval
        kind fails to parse (so skeleton-wf fails) rather than registering
        a dangerous commitment."""
        if not (v.startswith("rubric:") or v.startswith("program:")):
            raise ValueError(
                "forbidden-case eval must be 'rubric:<spec-id>' or "
                "'program:<ref>' (untrusted content may not carry an "
                f"inline predicate): {v[:40]!r}")
        return v


class Scope(BaseModel):
    covers: list[str] = Field(default_factory=list)
    excludes: list[str] = Field(default_factory=list)


class Skeleton(BaseModel):
    claim: str
    mechanism: str
    scope: Scope = Field(default_factory=Scope)
    forbidden: list[ForbiddenCase] = Field(default_factory=list)
    prose_notes: str | None = None  # rendered, never adjudicated


def parse_skeleton(text: str) -> Skeleton | None:
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or "claim" not in data or "mechanism" not in data:
        return None
    try:
        return Skeleton.model_validate(data)
    except ValidationError:
        return None


def skeleton_wf_program(text: str, budget) -> tuple[str, dict]:
    """The skeleton-wf commitment program: parse AND forbidden != []."""
    skeleton = parse_skeleton(text)
    if skeleton is None:
        return "fail", {"error": "content does not parse as a skeleton"}
    if not skeleton.forbidden:
        return "fail", {"error": "forbids nothing: empty attack surface (§6)"}
    return "pass", {"forbidden_cases": len(skeleton.forbidden)}


def skeleton_wf_commitment() -> Commitment:
    return Commitment(id=SKELETON_WF_ID, eval="program:skeleton_wf")


def forbidden_commitment(case: ForbiddenCase) -> Commitment:
    """Pure canonical construction for one model-authored forbidden case.

    Registration is deliberately left to the caller. Keeping identity,
    budget, and observation semantics here lets both engine profiles consume
    the same commitment without maintaining a reduced-engine copy.
    """
    cid = "fc:" + sha256_hex(canonical_json({
        "case": case.case,
        "eval": case.eval,
        "observation_valued": case.observation_valued,
    }))[:12]
    return Commitment(
        id=cid,
        eval=case.eval,
        observation_valued=case.observation_valued,
        budget=Budget(extra={"case": case.case}),
    )


def compile_forbidden_commitments(harness, skeleton: Skeleton) -> list[str]:
    """Compile each forbidden case into a registered commitment; the case
    text rides in budget.extra for trial packs. Deterministic ids, so the
    same skeleton always compiles to the same interface."""
    ids: list[str] = []
    for case in skeleton.forbidden:
        # observation_valued is part of the commitment's identity: register_
        # commitment dedupes by id, so omitting it would let an earlier
        # observation_valued=False case mask a later True one, silently
        # suppressing the research-evidence Spawn trigger (§12).
        commitment = forbidden_commitment(case)
        harness.register_commitment(commitment)
        ids.append(commitment.id)
    return ids
