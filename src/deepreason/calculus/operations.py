"""Claim-authoring operations. Dedicated, never a generalised synthesizer.

Two-step and idempotent by construction: the body is a pure function of the
`Problem` record, so its content address is too. Calling `ensure_problem_subject`
twice registers one artifact and commits one event the first time and none the
second, which is what makes the crash gap between the two writes recoverable by
simply running it again.
"""

from __future__ import annotations

from deepreason.calculus.claims import (
    DepartureDeclarationV1,
    FrameAssertionV1,
    ProblemSubjectV1,
    encode,
)
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.programs import (
    DEPARTURE_DECLARATION_COMMITMENT,
    FRAME_ASSERTION_COMMITMENT,
    PROBLEM_SUBJECT_COMMITMENT,
)
from deepreason.calculus.scope import compile_scope
from deepreason.calculus.views import problem_subject_of
from deepreason.ontology import Problem, ProblemProvenance, Provenance, SpawnTrigger


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


def ensure_promotion_problem(
    harness, subject_id: str, description: str, criteria=()
):
    """Register the promotion problem for a subject, once (§9.4).

    Deterministic and idempotent for the same reason
    `ensure_problem_subject` is: the id is a pure function of the subject, so
    re-running after a crash between the two writes registers nothing new.

    This rung defines what a promotion problem IS, because Def 9.2's consult
    condition -- "addressed to a promotion problem" -- is otherwise undefined
    and the standing view would have nothing to gate on. It does NOT decide
    when one should exist: nomination is Rung 5's measure-rule, and it calls
    this operation rather than minting its own shape.

    `criteria` is Rung 5's addition and carries §9.4's five pinned criteria.
    They are passed at REGISTRATION because `Problem` is immutable: a promotion
    problem that existed for one event without its criteria would be a problem a
    candidate could be addressed to before anything could refuse it, which is
    the exact hole Remark 9.5's closure exists to shut. The early return above
    keeps idempotency intact -- an existing problem is returned unexamined, so a
    caller that passes criteria to a problem Rung 4's own tests created without
    them gets that problem back rather than a well-formedness conflict.
    """
    pid = f"{SpawnTrigger.PROMOTION.value}:{subject_id[:12]}"
    existing = harness.state.problems.get(pid)
    if existing is not None:
        return existing
    return harness.register_problem(
        Problem(
            id=pid,
            description=description,
            criteria=list(criteria),
            provenance=ProblemProvenance.model_validate(
                {"trigger": SpawnTrigger.PROMOTION, "from": [subject_id]}
            ),
        )
    )


def file_frame_assertion(
    harness,
    *,
    problem,
    subject_ref: str,
    scope: dict,
    departure_protocol: str,
    validity: str = "universal",
    validity_domain: str | None = None,
    validity_tolerance: str | None = None,
    reach_case_refs=(),
    succeeded_wound_refs=(),
):
    """Register a frame assertion as an ORDINARY artifact (Def 9.2).

    `scope` is compiled here and the compiled form is discarded: compiling is
    a VALIDATION, and its result must not be stored, because the artifact's
    content address is taken over the document rather than over whatever a
    given version of the compiler makes of it. A scope that cannot compile is
    refused at authoring time rather than at membership time, which is what
    keeps sigma total (C1).
    """
    compile_scope(scope)
    harness.register_commitment(FRAME_ASSERTION_COMMITMENT)
    body = FrameAssertionV1(
        subject_ref=subject_ref,
        scope=scope,
        validity=validity,
        validity_domain=validity_domain,
        validity_tolerance=validity_tolerance,
        departure_protocol=departure_protocol,
        reach_case_refs=list(reach_case_refs),
        succeeded_wound_refs=list(succeeded_wound_refs),
    )
    return harness.create_artifact(
        encode(body),
        codec="json",
        interface=compile_interface(body),
        problem_id=problem.id,
        provenance=Provenance(role="import"),
    )


def file_departure_declaration(
    harness,
    *,
    problem,
    subject_ref: str,
    departing_ref: str,
    broken_ids,
    rationale: str,
):
    """Declare that one artifact breaks with named commitments of a frame.

    An ORDINARY artifact, like every other claim here, and that is the whole
    of "the declaration is itself attackable": nothing special protects it, so
    a critic attacks it exactly as they would attack anything else.

    Idempotent by content address for the same reason `file_frame_assertion`
    is -- the body is a pure function of its arguments, so declaring the same
    departure twice registers one artifact.

    NO CHECK RUNS HERE against the subject's actual commitment ids. Refusing a
    declaration that names an id the subject does not carry would make the
    authoring path a judge of whether a departure is real, and a departure a
    critic disputes is a criticism they mount, not an authoring error. The
    render subtracts what is declared; whether the subtraction was earned is
    an ordinary question for criticism.
    """
    harness.register_commitment(DEPARTURE_DECLARATION_COMMITMENT)
    body = DepartureDeclarationV1(
        subject_ref=subject_ref,
        departing_ref=departing_ref,
        broken_ids=list(broken_ids),
        rationale=rationale,
    )
    return harness.create_artifact(
        encode(body),
        codec="json",
        interface=compile_interface(body),
        problem_id=problem.id,
        provenance=Provenance(role="import"),
    )
