"""Structural well-formedness for claim bodies.

STRUCTURAL in the exact sense `measures/reach.py::_STRUCTURAL_PROGRAMS` means:
passing proves the body is well formed, never that its claim holds. So these
ground no reach and confer no prose immunity — an artifact cannot immunise
itself by being a well-formed claim.
"""

from __future__ import annotations

from deepreason.calculus.claims import (
    PREMISE_ATTRIBUTION_V1,
    PROBLEM_SUBJECT_V1,
    ClaimDecodeError,
    decode,
)
from deepreason.ontology import Commitment

PROBLEM_SUBJECT_WF = "problem_subject_wf"
PREMISE_ATTRIBUTION_WF = "premise_attribution_wf"

PROBLEM_SUBJECT_COMMITMENT = Commitment(
    id="claim:problem-subject-wf@v1", eval=f"program:{PROBLEM_SUBJECT_WF}"
)
PREMISE_ATTRIBUTION_COMMITMENT = Commitment(
    id="claim:premise-attribution-wf@v1", eval=f"program:{PREMISE_ATTRIBUTION_WF}"
)


def _wf(text: str, schema: str, artifact) -> tuple[str, dict]:
    try:
        body = decode(text)
    except ClaimDecodeError as error:
        return "fail", {"reason": error.code, "detail": error.detail}
    if body.schema_ != schema:
        return "fail", {"reason": "claim-schema-mismatch", "detail": body.schema_}
    if artifact is None:
        return "fail", {"reason": "claim requires its own interface"}
    from deepreason.calculus.compiler import compile_interface

    expected = compile_interface(body)
    declared = {(r.target, r.role.value) for r in artifact.interface.refs}
    if declared != {(r.target, r.role.value) for r in expected.refs}:
        # The compiler is the only authority on ref roles, so an interface that
        # disagrees with it was not compiled by the controller -- whatever else
        # it is, it is not this claim.
        return "fail", {
            "reason": "claim-interface-not-controller-compiled",
            "detail": sorted(f"{t}:{r}" for t, r in declared),
        }
    return "pass", {"schema": body.schema_}


def problem_subject_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    return _wf(text, PROBLEM_SUBJECT_V1, artifact)


def premise_attribution_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    return _wf(text, PREMISE_ATTRIBUTION_V1, artifact)
