"""Anomaly conservation -- what the successor inherits, and what the fallen
subject keeps.

Implements R5 (v2 calculus program, Rung 7). §9.7:

    Nothing is deleted (P8), and the accounts-for criterion makes the successor
    claim the incumbent's wounds as its own commitments -- attackably: the new
    frame must predict what broke the old one. Its scope statement must also
    fix the incumbent's residual validity domain; succession may therefore
    leave a residual bounded-validity frame assertion for the fallen subject,
    which thereby keeps framing its granted domain as a declared approximation
    -- instrument standing (Def 9.3). The predecessor's domain of validity is
    authored by its successor, and that authorship is one more attackable
    claim.

NOTHING NEW IS BUILT HERE EITHER. `succeeded_wound_refs`, the machine-derived
wound list, the MENTION compilation of a claimed wound, and `bounded` validity
with its domain and tolerance all shipped at Rungs 4 and 5. What this rung owes
is the proof that the road exists and CLOSES -- from the successor's claim to
the fallen subject's residual grant, and back out again when someone attacks
it.
"""

import pytest

from deepreason.calculus import operations, promotion
from deepreason.calculus.claims import (
    FrameAssertionV1,
    FrozenCommitmentV1,
    FrozenGrantV1,
    FrozenProblemV1,
    FrozenSubjectV1,
    ReachCertificateV1,
)
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.standing import consulted, fallen_frames, frames, standing_of
from deepreason.ontology import Interface, Provenance, Status
from deepreason.premises import premise_orphaned
from tests.conftest import attack


SCOPE_ALL = {"schema": "declarative-scope.v1", "predicate": {"const": True}}
TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}
SHALLOW = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "shallow water"}]},
}


def _art(harness, text):
    return harness.create_artifact(
        text, interface=Interface(), provenance=Provenance(role="critic")
    )


# --- 1. the successor claims the wounds, as MENTIONS ------------------------

def test_the_successor_claims_the_incumbents_wounds_as_mentions(harness):
    """"The new frame must predict what broke the old one" -- and the claim is
    a MENTION, never a dependence.

    The role is the whole of anomaly conservation's safety. A DEPENDENCE on a
    wound would suspend the successor the moment that wound was reinstated
    away, so a successful defence of the incumbent would silently unseat its
    replacement. A mention makes the claim visible and attackable without
    making the successor hostage to it.
    """
    body = FrameAssertionV1(
        subject_ref="e-prime",
        scope=SCOPE_ALL,
        departure_protocol="cite this id",
        succeeded_wound_refs=["w-perihelion", "w-tidal-lag"],
    )
    roles = {r.target: r.role.value for r in compile_interface(body).refs}
    assert roles["w-perihelion"] == "mention"
    assert roles["w-tidal-lag"] == "mention"
    assert roles["e-prime"] == "mention"
    assert "dependence" not in set(roles.values())


def test_a_successor_cannot_choose_its_own_wounds(harness):
    """D-6 answer A: the wound list is MACHINE-DERIVED. A candidate declares
    which wounds it succeeds over, and the declaration only counts where it
    intersects what the record says actually broke the incumbent."""
    from deepreason.calculus.nomination import _wound_refs

    subject = _art(harness, "b: the lunar theory of tides")
    critic, _ = attack(harness, subject.id, "the-lunar-theory-mispredicts-the-lag")
    derived = _wound_refs(harness, subject.id)
    assert derived
    assert all(harness.warrants[wid].target == subject.id for wid in derived)
    # nothing a candidate writes appears in that list
    assert "w-invented-by-the-candidate" not in derived


# --- 2. the residue must be accounted for, and `bounded` is how -------------

def _certificate(incumbent, rival, *, consulted_scope=None):
    accounted = sorted(set(incumbent.accounted) | set(rival.accounted))
    declared = sorted(set(incumbent.commitments) | set(rival.commitments))
    return ReachCertificateV1(
        subject_ref=rival.artifact_id,
        scope=SCOPE_ALL,
        k_frame=2,
        subjects=[incumbent, rival],
        problems=[
            FrozenProblemV1(id=pid, description=pid, trigger="seed",
                            criteria=["k-mechanism"], lineage_root="r")
            for pid in accounted
        ],
        commitments=[
            FrozenCommitmentV1(id=cid, eval="program:json_wf",
                               observation_valued=False)
            for cid in declared
        ],
        consulted=[
            FrozenGrantV1(assertion_id="assertion-incumbent",
                          subject_ref=incumbent.artifact_id,
                          scope=consulted_scope or SCOPE_ALL)
        ],
    )


def _subject(aid, *, accounted, hv, wounds=(), criticised=()):
    return FrozenSubjectV1(
        artifact_id=aid, commitments=["k-mechanism"], demarcation="load-bearing",
        hv=hv, accounted=list(accounted), wound_refs=list(wounds),
        criticised_commitments=list(criticised),
    )


def test_an_unaccounted_residue_refuses_the_succession():
    """Recovery's first half. A rival that simply DROPS an explicandum the
    incumbent had is not a successor -- nothing is deleted, and a succession
    that lost a question would be deleting one."""
    incumbent = _subject("e", accounted=["p1", "p-shallow"], hv=0.6, wounds=["w1"])
    rival = _subject("e-prime", accounted=["p1", "p2"], hv=0.9)
    body = FrameAssertionV1(subject_ref="e-prime", scope=SCOPE_ALL,
                            departure_protocol="cite this id",
                            succeeded_wound_refs=["w1"])
    verdict, detail = promotion.succeeds(_certificate(incumbent, rival), body)
    assert verdict == "fail"
    assert detail["reason"] == "recovery-fails"
    assert detail["residue"] == ["p-shallow"]


def test_the_scope_statement_fixes_the_incumbents_residual_domain():
    """§9.7's own sentence: "Its scope statement must also fix the incumbent's
    residual validity domain." The successor accounts for the residue by
    declaring a BOUNDED validity that names it -- which is the account, and it
    is a claim the successor AUTHORS rather than a concession the system
    grants."""
    incumbent = _subject("e", accounted=["p1", "p-shallow"], hv=0.6, wounds=["w1"])
    rival = _subject("e-prime", accounted=["p1", "p2"], hv=0.9)
    body = FrameAssertionV1(
        subject_ref="e-prime", scope=SCOPE_ALL,
        validity="bounded",
        validity_domain="p-shallow: the shallow-water regime",
        validity_tolerance="within 5 per cent of the observed lag",
        departure_protocol="cite this id",
        succeeded_wound_refs=["w1"],
    )
    verdict, detail = promotion.succeeds(_certificate(incumbent, rival), body)
    assert verdict == "pass", detail


def test_a_bounded_validity_without_its_domain_is_refused():
    """C3: instrument standing is not a third standing VALUE, it is content --
    and a bounded grant without its declared domain and tolerance would be an
    unqualified one wearing the word."""
    with pytest.raises(ValueError, match="bounded validity requires"):
        FrameAssertionV1(subject_ref="e-prime", scope=SCOPE_ALL,
                         validity="bounded",
                         departure_protocol="cite this id")


# --- 3. the residual grant: instrument standing, end to end -----------------

def _fallen_incumbent(harness):
    """An incumbent whose frame has FALLEN, with a problem in each regime."""
    from deepreason.ontology import Problem, ProblemProvenance

    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(harness, "reach record: three lineages cite the lunar theory")
    promotion_problem = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse the lunar theory of tides"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion_problem, subject_ref=subject.id, scope=TIDES,
        reach_case_refs=(case.id,), departure_protocol="declare it",
    )
    for pid, description in (
        ("deep-tides", "what governs the tides in the deep ocean"),
        ("shallow-tides", "what governs the tides in shallow water"),
    ):
        harness.register_problem(
            Problem(id=pid, description=description, criteria=[],
                    provenance=ProblemProvenance.model_validate(
                        {"trigger": "seed", "from": []})))
    attack(harness, assertion.id, "the-lunar-frame-mispredicts-the-deep-ocean")
    return subject, promotion_problem, assertion


def test_a_fallen_subject_keeps_framing_its_granted_domain(harness):
    """The road §9.7 leaves open, walked end to end.

    The incumbent's frame fell, so it frames nothing and its problems are
    orphaned. The SUCCESSOR then authors a residual assertion: bounded
    validity, the shallow-water domain, a declared tolerance. The fallen
    subject frames that domain again -- as a declared approximation, which is
    what instrument standing IS -- and nothing else.
    """
    subject, promotion_problem, assertion = _fallen_incumbent(harness)
    assert [f.grade for f in fallen_frames(harness)] == ["fall"]
    assert set(premise_orphaned(harness)) == {"deep-tides", "shallow-tides"}
    assert standing_of(harness, subject.id) == ()

    residual_case = _art(harness, "reach record: the shallow-water regime")
    residual = operations.file_frame_assertion(
        harness, problem=promotion_problem, subject_ref=subject.id,
        scope=SHALLOW,
        validity="bounded",
        validity_domain="the shallow-water regime",
        validity_tolerance="within 5 per cent of the observed lag",
        reach_case_refs=(residual_case.id,),
        departure_protocol="declare it",
    )

    grants = standing_of(harness, subject.id)
    assert [g.assertion_id for g in grants] == [residual.id]
    # INSTRUMENT STANDING: the relation is the same one, and `validity` is
    # what tells a reader it is qualified (C3, no third value)
    assert grants[0].validity == "bounded"
    assert grants[0].validity_domain == "the shallow-water regime"
    assert grants[0].validity_tolerance
    # it frames its granted domain, and NOT the one it lost
    assert frames(harness, subject.id, "shallow-tides") is True
    assert frames(harness, subject.id, "deep-tides") is False


def test_the_residual_grant_is_attackable_like_anything(harness):
    """"That authorship is one more attackable claim." Refuting the residual
    assertion ends the residual grant, and the fallen subject stops framing
    even its bounded domain -- no special case, no protection."""
    subject, promotion_problem, _ = _fallen_incumbent(harness)
    residual_case = _art(harness, "reach record: the shallow-water regime")
    residual = operations.file_frame_assertion(
        harness, problem=promotion_problem, subject_ref=subject.id,
        scope=SHALLOW, validity="bounded",
        validity_domain="the shallow-water regime",
        validity_tolerance="within 5 per cent of the observed lag",
        reach_case_refs=(residual_case.id,), departure_protocol="declare it",
    )
    assert standing_of(harness, subject.id)

    attack(harness, residual.id,
           "the-shallow-water-domain-was-drawn-to-save-the-theory")

    assert harness.state.status[residual.id] is Status.REFUTED
    assert standing_of(harness, subject.id) == ()
    assert frames(harness, subject.id, "shallow-tides") is False
    # and the residual assertion's own fall cascades, exactly as the first did
    assert "shallow-tides" in premise_orphaned(harness)


def test_nothing_is_deleted_by_any_of_it(harness):
    """P8, across the whole road. The fallen assertion, its critic, the
    residual assertion and its critic are all still on the record -- what
    changed is which of them are consulted."""
    subject, promotion_problem, assertion = _fallen_incumbent(harness)
    residual_case = _art(harness, "reach record: the shallow-water regime")
    residual = operations.file_frame_assertion(
        harness, problem=promotion_problem, subject_ref=subject.id,
        scope=SHALLOW, validity="bounded",
        validity_domain="the shallow-water regime",
        validity_tolerance="within 5 per cent of the observed lag",
        reach_case_refs=(residual_case.id,), departure_protocol="declare it",
    )
    attack(harness, residual.id, "the-shallow-water-domain-was-drawn-to-save-it")

    for aid in (subject.id, assertion.id, residual.id, residual_case.id):
        assert aid in harness.state.artifacts
    assert consulted(harness) == ()
