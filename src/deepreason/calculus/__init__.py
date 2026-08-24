"""The typed claim substrate (v2 calculus program, Rung 3c).

A claim is a versioned body from a CLOSED set, compiled to an ``Interface`` by
one controller-owned compiler. The closure and the single compiler are the two
halves of one guarantee: nothing outside the set can become quasi-ontology, and
no model ever chooses whether an endpoint is a mention, a dependence, or
evidence. Bodies are proposable; semantics are not.
"""

from deepreason.calculus.claims import (
    CLAIM_SCHEMAS,
    DepartureDeclarationV1,
    DerivationManifestV1,
    KernelCheckV1,
    FrameAssertionV1,
    ClaimDecodeError,
    PremiseAttributionV1,
    ProblemSubjectV1,
    decode,
    encode,
)
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.operations import (
    ensure_problem_subject,
    ensure_promotion_problem,
    file_departure_declaration,
    file_frame_assertion,
)
from deepreason.calculus.scope import ScopeError, compile_scope, scope_admits
from deepreason.calculus.separation import (
    FRAME_ENDPOINT_UNREGISTERED,
    FRAME_NOT_SEPARATED,
    Consultability,
    adjudication_component,
    consultability,
    frame_separated,
)
from deepreason.calculus.standing import (
    FRAME_NOT_ADDRESSED_TO_PROMOTION,
    FRAME_NOT_A_FRAME_ASSERTION,
    FRAME_NOT_UNREFUTED,
    StandingGrant,
    consulted,
    consultability_of,
    frame_assertions,
    frames,
    standing_of,
    standing_view,
)
from deepreason.calculus.views import (
    problem_status,
    problem_subject_missing,
    problem_subject_of,
)

__all__ = [
    "CLAIM_SCHEMAS",
    "DepartureDeclarationV1",
    "DerivationManifestV1",
    "KernelCheckV1",
    "FRAME_NOT_ADDRESSED_TO_PROMOTION",
    "FRAME_NOT_A_FRAME_ASSERTION",
    "FRAME_NOT_UNREFUTED",
    "FrameAssertionV1",
    "ScopeError",
    "StandingGrant",
    "compile_scope",
    "consultability_of",
    "consulted",
    "ensure_promotion_problem",
    "file_departure_declaration",
    "file_frame_assertion",
    "frame_assertions",
    "frames",
    "scope_admits",
    "standing_of",
    "standing_view",
    "FRAME_ENDPOINT_UNREGISTERED",
    "FRAME_NOT_SEPARATED",
    "ClaimDecodeError",
    "Consultability",
    "PremiseAttributionV1",
    "ProblemSubjectV1",
    "adjudication_component",
    "compile_interface",
    "consultability",
    "decode",
    "encode",
    "ensure_problem_subject",
    "frame_separated",
    "problem_status",
    "problem_subject_missing",
    "problem_subject_of",
]
