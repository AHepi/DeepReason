"""Derived views over the claim substrate. Nothing here is stored.

`Problem` remains the immutable scheduling and provenance record; the companion
subject carries the criticism. Reading a problem's standing therefore means
reading an ORDINARY artifact status, which is what keeps problems criticisable
without giving them a status of their own.
"""

from __future__ import annotations

from deepreason.calculus.claims import (
    PROBLEM_SUBJECT_V1,
    ClaimDecodeError,
    ProblemSubjectV1,
    decode,
)
from deepreason.calculus.programs import PROBLEM_SUBJECT_COMMITMENT
from deepreason.programs import content_text


def _recognised(harness, artifact, problem) -> bool:
    """The six conditions, all of them, in the advice's order.

    Any one of them failing means this artifact is not the problem's subject.
    Condition 3 -- the copies MATCH the record -- is the one carrying the
    weight: without it a companion drifts from its problem and criticism lands
    on a stale statement of the question.
    """
    if PROBLEM_SUBJECT_COMMITMENT.id not in artifact.interface.commitments:
        return False                                              # (4)
    try:
        body = decode(content_text(artifact, harness.blobs))       # (1)
    except ClaimDecodeError:
        return False
    if not isinstance(body, ProblemSubjectV1):
        return False
    if body.problem_id != problem.id:                              # (2)
        return False
    if (
        body.description != problem.description
        or list(body.criteria) != list(problem.criteria)
        or body.trigger != problem.provenance.trigger.value
        or list(body.sources) != list(problem.provenance.from_)
    ):
        return False                                               # (3)
    if (artifact.id, problem.id) not in harness.state.addr:         # (5)
        return False
    if artifact.interface.refs:                                     # (6)
        return False
    return True


def problem_subject_of(harness, problem_id: str):
    """The recognised companion artifact for a problem, or None."""
    problem = harness.state.problems.get(problem_id)
    if problem is None:
        return None
    for aid, pid in sorted(harness.state.addr):
        if pid != problem_id:
            continue
        artifact = harness.state.artifacts.get(aid)
        if artifact is not None and _recognised(harness, artifact, problem):
            return artifact
    return None


def problem_status(harness, problem_id: str):
    """A problem's standing = its companion's ORDINARY artifact status.

    None when no companion is recognised, which is a different thing from a
    problem being fine: read it with `problem_subject_missing`.
    """
    subject = problem_subject_of(harness, problem_id)
    if subject is None:
        return None
    return harness.state.status.get(subject.id)


def problem_subject_missing(harness) -> list[str]:
    """Registered problems with no recognised companion — the typed diagnostic.

    This is where a crash between `register_problem` and
    `ensure_problem_subject` shows up, and the repair is to run the operation
    again rather than to make the two writes atomic. A very small recoverable
    gap is not worth changing event atomicity for.
    """
    return sorted(
        pid
        for pid in harness.state.problems
        if problem_subject_of(harness, pid) is None
    )
