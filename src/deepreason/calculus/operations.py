"""Claim-authoring operations. Dedicated, never a generalised synthesizer.

Two-step and idempotent by construction: the body is a pure function of the
`Problem` record, so its content address is too. Calling `ensure_problem_subject`
twice registers one artifact and commits one event the first time and none the
second, which is what makes the crash gap between the two writes recoverable by
simply running it again.
"""

from __future__ import annotations

from deepreason.calculus.claims import ProblemSubjectV1, encode
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.programs import PROBLEM_SUBJECT_COMMITMENT
from deepreason.calculus.views import problem_subject_of
from deepreason.ontology import Provenance


def problem_subject_body(problem) -> ProblemSubjectV1:
    """The companion body for a problem — deterministic, and a pure copy."""
    return ProblemSubjectV1(
        problem_id=problem.id,
        description=problem.description,
        criteria=list(problem.criteria),
        trigger=problem.provenance.trigger.value,
        sources=list(problem.provenance.from_),
    )


def ensure_problem_subject(harness, problem):
    """Register the problem's companion subject artifact, once.

    Idempotent: returns the existing recognised companion if there is one, and
    otherwise registers the deterministic body. Nothing is written to the
    `Problem` record — the companion is found through `addr`, computed from the
    record that already exists, so no field is added to `Problem`,
    `EpistemicState` or `Event`.
    """
    existing = problem_subject_of(harness, problem.id)
    if existing is not None:
        return existing
    harness.register_commitment(PROBLEM_SUBJECT_COMMITMENT)
    body = problem_subject_body(problem)
    return harness.create_artifact(
        encode(body),
        codec="json",
        interface=compile_interface(body),
        problem_id=problem.id,
        provenance=Provenance(role="import"),
    )
