"""The closed discriminated union of claim bodies.

CLOSED is the requirement, not a style: an open ``RelationClaim(predicate:
str)`` would let arbitrary prose predicates become quasi-ontology, and every
one of them would then need its own interaction with ``att``, ``dep``, replay
and status re-proven. The set of schema NAMES is closed here; a body is
implemented only where this rung has a producer for it.

Declared-and-unimplemented is deliberate and typed. Shipping body models with
no producers is the pattern `docs/ERRATA.md` E28 records — a mechanism nobody
triggers — so `decode` refuses a declared-but-unbuilt schema with a reason
rather than accepting it into a shape nothing can create.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# The closed name set. Adding a name here is an ontology change and belongs in
# the rung that supplies its producer, never in a convenience commit.
CLAIM_SCHEMAS: tuple[str, ...] = (
    "poietic.problem-subject.v1",
    "poietic.premise-attribution.v1",
    "poietic.derivation-manifest.v1",
    "poietic.reach-certificate.v1",
    "poietic.frame-assertion.v1",
    "poietic.problem-retirement.v1",
    "poietic.problem-translation.v1",
    "poietic.localization.v1",
    "poietic.succession.v1",
)

PROBLEM_SUBJECT_V1 = "poietic.problem-subject.v1"
PREMISE_ATTRIBUTION_V1 = "poietic.premise-attribution.v1"

# The two with a producer in this rung. The rest are declared above and refused
# below, with their names on the record so a reader sees the intended shape of
# the substrate rather than only the built part of it.
_IMPLEMENTED: tuple[str, ...] = (PROBLEM_SUBJECT_V1, PREMISE_ATTRIBUTION_V1)


class ClaimDecodeError(ValueError):
    """A typed decode refusal. Carries `code` so callers branch on a value
    rather than on message text."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProblemSubjectV1(_Body):
    """The companion artifact that makes a problem criticisable.

    Every field except `schema` is COPIED from the immutable `Problem` record,
    and recognition re-checks each copy against it. That is what stops a
    companion drifting from the problem it speaks for, which would leave
    criticism landing on a stale statement of the question.
    """

    schema_: Literal["poietic.problem-subject.v1"] = Field(
        default=PROBLEM_SUBJECT_V1, alias="schema"
    )
    problem_id: str
    description: str
    criteria: list[str] = Field(default_factory=list)
    trigger: str
    sources: list[str] = Field(default_factory=list)


class PremiseAttributionV1(_Body):
    """"This problem presupposes X."

    Three endpoints and NOT ONE of them names its own ref role — the compiler
    assigns those. The premise is MENTIONED, never depended on: an attribution
    that depended on its premise would be suspended by pass two at the exact
    moment the premise fell, erasing the relation needed to identify the orphan.
    """

    schema_: Literal["poietic.premise-attribution.v1"] = Field(
        default=PREMISE_ATTRIBUTION_V1, alias="schema"
    )
    problem_subject_ref: str
    premise_ref: str
    derivation_manifest_ref: str | None = None
    # The admitted-citation record this attribution rests on, when it cites
    # evidence at all. Optional because a run with no dossier bound has nothing
    # to cite and the all-configurations law forbids refusing it (R62).
    citation_ref: str | None = None


_MODELS: dict[str, type[_Body]] = {
    PROBLEM_SUBJECT_V1: ProblemSubjectV1,
    PREMISE_ATTRIBUTION_V1: PremiseAttributionV1,
}


def encode(body: _Body) -> str:
    """Canonical JSON for a claim body: sorted keys, aliases, no nulls.

    Canonical because the artifact id is a content address over it — two
    encodings of one claim would be two artifacts, and idempotent registration
    would stop being idempotent.
    """
    payload = body.model_dump(mode="json", by_alias=True, exclude_none=True)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def decode(text: str) -> _Body:
    """Parse a claim body, or refuse with a typed code."""
    try:
        payload = json.loads(text)
    except Exception as error:  # noqa: BLE001 - unparseable content is a refusal
        raise ClaimDecodeError("claim-not-json", str(error)) from None
    if not isinstance(payload, dict):
        raise ClaimDecodeError("claim-not-an-object", type(payload).__name__)
    schema = payload.get("schema")
    if schema not in CLAIM_SCHEMAS:
        raise ClaimDecodeError("claim-schema-unknown", repr(schema))
    if schema not in _IMPLEMENTED:
        raise ClaimDecodeError(
            "claim-schema-not-implemented",
            f"{schema} is declared in the closed set but has no producer yet",
        )
    try:
        return _MODELS[schema].model_validate(payload)
    except Exception as error:  # noqa: BLE001
        raise ClaimDecodeError("claim-body-invalid", str(error)) from None
