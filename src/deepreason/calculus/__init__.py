"""The typed claim substrate (v2 calculus program, Rung 3c).

A claim is a versioned body from a CLOSED set, compiled to an ``Interface`` by
one controller-owned compiler. The closure and the single compiler are the two
halves of one guarantee: nothing outside the set can become quasi-ontology, and
no model ever chooses whether an endpoint is a mention, a dependence, or
evidence. Bodies are proposable; semantics are not.
"""

from deepreason.calculus.claims import (
    CLAIM_SCHEMAS,
    ClaimDecodeError,
    PremiseAttributionV1,
    ProblemSubjectV1,
    decode,
    encode,
)
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.operations import ensure_problem_subject
from deepreason.calculus.separation import (
    FRAME_ENDPOINT_UNREGISTERED,
    FRAME_NOT_SEPARATED,
    Consultability,
    adjudication_component,
    consultability,
    frame_separated,
)
from deepreason.calculus.views import (
    problem_status,
    problem_subject_missing,
    problem_subject_of,
)

__all__ = [
    "CLAIM_SCHEMAS",
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
