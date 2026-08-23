"""Structural well-formedness for claim bodies.

STRUCTURAL in the exact sense `measures/reach.py::_STRUCTURAL_PROGRAMS` means:
passing proves the body is well formed, never that its claim holds. So these
ground no reach and confer no prose immunity — an artifact cannot immunise
itself by being a well-formed claim.
"""

from __future__ import annotations

from deepreason.calculus.claims import (
    DERIVATION_MANIFEST_V1,
    FRAME_ASSERTION_V1,
    PREMISE_ATTRIBUTION_V1,
    PROBLEM_SUBJECT_V1,
    ClaimDecodeError,
    FrameAssertionV1,
    decode,
)
from deepreason.ontology import Commitment

PROBLEM_SUBJECT_WF = "problem_subject_wf"
PREMISE_ATTRIBUTION_WF = "premise_attribution_wf"
FRAME_ASSERTION_WF = "frame_assertion_wf"
DERIVATION_MANIFEST_WF = "derivation_manifest_wf"

PROBLEM_SUBJECT_COMMITMENT = Commitment(
    id="claim:problem-subject-wf@v1", eval=f"program:{PROBLEM_SUBJECT_WF}"
)
PREMISE_ATTRIBUTION_COMMITMENT = Commitment(
    id="claim:premise-attribution-wf@v1", eval=f"program:{PREMISE_ATTRIBUTION_WF}"
)
FRAME_ASSERTION_COMMITMENT = Commitment(
    id="claim:frame-assertion-wf@v1", eval=f"program:{FRAME_ASSERTION_WF}"
)
DERIVATION_MANIFEST_COMMITMENT = Commitment(
    id="claim:derivation-manifest-wf@v1", eval=f"program:{DERIVATION_MANIFEST_WF}"
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


def frame_assertion_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    """Law 9.4 as a well-formedness commitment.

    The mention law is checked FIRST, ahead of the shared controller-compiled
    comparison. That comparison would also reject a dependence on the subject
    -- the compiler never emits one -- but its reason reads
    "claim-interface-not-controller-compiled", which is what a reader sees for
    ANY mis-registered artifact. Naming the law is what lets them tell a
    violated separation from a botched registration, and this program's verdict
    is the record's only account of which happened.
    """
    try:
        body = decode(text)
    except ClaimDecodeError as error:
        return "fail", {"reason": error.code, "detail": error.detail}
    if isinstance(body, FrameAssertionV1) and artifact is not None:
        depended = {
            ref.target for ref in artifact.interface.refs
            if ref.role.value == "dependence"
        }
        if body.subject_ref in depended:
            return "fail", {
                "reason": "frame-assertion-depends-on-subject",
                "detail": body.subject_ref,
            }
    return _wf(text, FRAME_ASSERTION_V1, artifact)


def derivation_manifest_wf(text: str, budget, artifact=None) -> tuple[str, dict]:
    """Structural well-formedness for a bill of materials.

    STRUCTURAL, which here has a sharp consequence worth stating: a well-formed
    receipt must not immunise the judgment it accounts for. Declaring what you
    rest on is not evidence that what you rest on is sound, so this program
    grounds no reach and confers no prose immunity -- otherwise filing a bill
    would be a way of buying protection from criticism by admitting debt.
    """
    return _wf(text, DERIVATION_MANIFEST_V1, artifact)
