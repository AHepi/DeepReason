"""Standing -- Def 9.3, derived and never stored, and the consult path.

Two axes, and the whole of this module exists to keep them apart. STATUS is
truth-standing under criticism; STANDING is an artifact's role in the economy
of generation -- whether it is one node among the retrieved neighbours or the
coordinate system every conjecture in a scope is written in. An artifact can be
refuted and still framing, which is the ordinary condition of mature knowledge,
and Prop 9.1 shows a single-axis calculus cannot host it.

Nothing here writes. `standing(b)` is recomputed from replayed state on every
call (C4: statuses are computed, never stored), and Prop 12.5 is what makes the
separation real rather than nominal -- label computation reads `att` and `dep`
only, and standing is consumed by render and schedule ALONE. This module holds
no call that could write, and it does not import `adjudication`: it consumes
that package's OUTPUT through replayed state, never its logic.

REVOCATION HAS NO RULE OF ITS OWN, and no function below implements one
(S-10). Attacking the reach records cuts the assertion's support, pass two
makes it `suspended_unsupported`, and `consulted` stops returning it. Orphaned
!= false does exactly the right work: revocation says unearned, not wrong.
"""

from __future__ import annotations

from dataclasses import dataclass

from deepreason.calculus.claims import ClaimDecodeError, FrameAssertionV1, decode
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.programs import FRAME_ASSERTION_COMMITMENT
from deepreason.calculus.scope import ScopeError, compile_scope, scope_admits
from deepreason.calculus.separation import Consultability, consultability
from deepreason.ontology import SpawnTrigger, Status
from deepreason.programs import content_text

FRAME_NOT_A_FRAME_ASSERTION = "frame-not-a-frame-assertion"
FRAME_NOT_ADDRESSED_TO_PROMOTION = "frame-not-addressed-to-promotion"
FRAME_NOT_UNREFUTED = "frame-not-unrefuted"


@dataclass(frozen=True)
class StandingGrant:
    """One consulted frame assertion, as a reader sees it. DERIVED: built on
    every call and never stored, so there is no grant record to fall out of
    step with the log that implies it.

    `validity` is CONTENT, not a third standing value (C3). A reader telling
    instrument standing from unqualified standing reads this field; the
    RELATION granted is the same one either way, which is why there is exactly
    one grant type here and not two.
    """

    assertion_id: str
    subject_id: str
    problem_id: str
    scope: dict
    validity: str
    validity_domain: str | None
    validity_tolerance: str | None
    departure_protocol: str
    reach_case_refs: tuple[str, ...]


def frame_assertion_body(harness, artifact) -> FrameAssertionV1 | None:
    """The recognised frame-assertion body of an artifact, or None.

    Recognition is the same shape the problem-subject companion uses: the body
    parses, the structural commitment is present, and the declared interface
    MATCHES what the controller's compiler would emit. That last condition is
    what carries the mention law here -- an artifact whose interface the
    compiler would not have produced is not this claim, whatever it says.
    """
    if FRAME_ASSERTION_COMMITMENT.id not in artifact.interface.commitments:
        return None
    try:
        body = decode(content_text(artifact, harness.blobs))
    except (ClaimDecodeError, UnicodeDecodeError, KeyError):
        return None
    if not isinstance(body, FrameAssertionV1):
        return None
    declared = {(r.target, r.role.value) for r in artifact.interface.refs}
    expected = {(r.target, r.role.value) for r in compile_interface(body).refs}
    if declared != expected:
        return None
    return body


def frame_assertions(harness) -> tuple[tuple[str, FrameAssertionV1], ...]:
    """Every recognised frame assertion in the run, in registration order."""
    return tuple(
        (aid, body)
        for aid, artifact in harness.state.artifacts.items()
        if (body := frame_assertion_body(harness, artifact)) is not None
    )


def _promotion_problem_of(harness, assertion_id: str) -> str | None:
    """The promotion problem an assertion addresses, if it addresses one.

    Remark 9.5's closure lives here: "the renderer consults only assertions
    addressed to promotion problems, which exist only by Spawn. A frame
    assertion born anywhere else is an ordinary artifact the renderer ignores."
    """
    for aid, pid in sorted(harness.state.addr):
        if aid != assertion_id:
            continue
        problem = harness.state.problems.get(pid)
        if problem is not None and problem.provenance.trigger is SpawnTrigger.PROMOTION:
            return pid
    return None


def consultability_of(harness, assertion_id: str) -> Consultability:
    """Def 9.2's four conditions, in order, returning Rung 3b's own type.

    The fourth condition CALLS `separation.consultability` rather than
    re-deriving the graph condition: Rung 3b delivered the predicate, its typed
    codes and its proof, and the codes this returns for a separation failure
    are that module's own constants unchanged. Re-implementing it here would
    give two definitions of one invariant and no way to tell which the record
    meant.
    """
    artifact = harness.state.artifacts.get(assertion_id)
    if artifact is None or frame_assertion_body(harness, artifact) is None:
        return Consultability(False, FRAME_NOT_A_FRAME_ASSERTION, (assertion_id,))
    body = frame_assertion_body(harness, artifact)
    problem_id = _promotion_problem_of(harness, assertion_id)
    if problem_id is None:
        return Consultability(
            False, FRAME_NOT_ADDRESSED_TO_PROMOTION, (assertion_id,)
        )
    if harness.state.status.get(assertion_id) is not Status.ACCEPTED:
        # final(fa) = unrefuted. This one clause is the whole of revocation:
        # a lost reach case makes the label suspended_unsupported upstream, and
        # the assertion simply stops being consulted. No revocation path exists
        # because none is needed (S-10).
        return Consultability(
            False, FRAME_NOT_UNREFUTED,
            (str(harness.state.status.get(assertion_id)),),
        )
    return consultability(harness, assertion_id, body.subject_ref)


def consulted(harness) -> tuple[StandingGrant, ...]:
    """Every consulted frame assertion, as grants. Recomputed, never stored."""
    grants = []
    for assertion_id, body in frame_assertions(harness):
        if not consultability_of(harness, assertion_id).consultable:
            continue
        grants.append(
            StandingGrant(
                assertion_id=assertion_id,
                subject_id=body.subject_ref,
                problem_id=_promotion_problem_of(harness, assertion_id),
                scope=body.scope,
                validity=body.validity,
                validity_domain=body.validity_domain,
                validity_tolerance=body.validity_tolerance,
                departure_protocol=body.departure_protocol,
                reach_case_refs=tuple(body.reach_case_refs),
            )
        )
    return tuple(grants)


def standing_of(harness, subject_id: str) -> tuple[StandingGrant, ...]:
    """Def 9.3: standing(b) is background over sigma iff a consulted frame
    assertion has b as its subject. There is no third value and no scalar --
    the answer is the grants themselves, because everything a reader needs to
    act on (the scope, the validity, the departure protocol) is their content.
    """
    return tuple(g for g in consulted(harness) if g.subject_id == subject_id)


def frames(harness, subject_id: str, problem_id: str) -> bool:
    """Does b frame THIS problem? sigma evaluated on the problem record alone.

    A scope that no longer compiles admits nothing rather than raising: the
    assertion is on the record and cannot be edited, so a reader asking whether
    it frames a problem must get an answer. The refusal is visible as an
    absent grant, never as a crashed render.
    """
    problem = harness.state.problems.get(problem_id)
    if problem is None:
        return False
    for grant in standing_of(harness, subject_id):
        try:
            if scope_admits(compile_scope(grant.scope), problem):
                return True
        except ScopeError:
            continue
    return False


def standing_view(harness) -> dict:
    """The whole read-only projection, for render and schedule ONLY (Prop 12.5).

    Sorted by assertion id so two renders of one root agree byte for byte, and
    carrying `framed_problems` because a grant a reader cannot locate in the
    frontier is a grant they cannot act on.
    """
    grants = sorted(consulted(harness), key=lambda g: g.assertion_id)
    return {
        "view": "standing.v1",
        "grants": [
            {
                "assertion": g.assertion_id,
                "subject": g.subject_id,
                "promotion_problem": g.problem_id,
                "validity": g.validity,
                "validity_domain": g.validity_domain,
                "validity_tolerance": g.validity_tolerance,
                "departure_protocol": g.departure_protocol,
                "reach_case_refs": list(g.reach_case_refs),
                "scope": g.scope,
                "framed_problems": sorted(
                    pid for pid in harness.state.problems
                    if frames(harness, g.subject_id, pid)
                ),
            }
            for g in grants
        ],
        "subjects": sorted({g.subject_id for g in grants}),
    }
