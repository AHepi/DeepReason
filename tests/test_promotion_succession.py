"""`accounts-for` implements the STRONG succession relation (R5, R6, R10).

RIDER 4 / R57, converging with R46 and Formalization §3.5. A good rival
covering the same explicanda is NOT a strict successor. Four parts, all
required:

    recovery          X(e) subset-of X(e'), or an unrefuted account of why e
                      worked over its restricted domain
    rigidity          e' is no easier to vary over the shared explicanda
    non-immunization  no PROPER functional component of e' is removable while
                      preserving every registered accounting and criticism
                      outcome
    strictness        at least one of recovery, criticism survival or rigidity
                      is STRICT

The weak form was never built. The rider forbids it in as many words -- "this
program has already paid twice for exactly that ordering" -- and the first test
below is why: a rival that recovers the incumbent's explicanda and nothing more
PASSES under the weak reading and must FAIL under this one. It carries the
mutation proof (CHECKLIST step 12).
"""

import pytest

from deepreason.calculus import operations, promotion
from deepreason.calculus.claims import (
    FrozenGrantV1,
    FrozenSubjectV1,
    ReachCertificateV1,
)

SCOPE_ALL = {"schema": "declarative-scope.v1", "predicate": {"const": True}}


def _certificate(*, incumbent, rival, consulted_scope=None):
    """A frozen environment holding exactly two subjects: e and e'.

    Built directly rather than through a run, because what is under test is the
    RELATION over a frozen reading, and a fixture that had to drive a whole run
    to vary one HV number would test the run instead.

    Every accounted problem is frozen with `k-mechanism` as its criterion. That
    is not decoration: non-immunization asks what a rival's accounted problems
    ASK FOR, and a certificate that froze no problems cannot answer, so the
    relation reports `accounting-not-in-environment` rather than treating an
    unknown demand as no demand.
    """
    accounted = sorted(set(incumbent.accounted) | set(rival.accounted))
    declared = sorted(set(incumbent.commitments) | set(rival.commitments))
    return ReachCertificateV1(
        subject_ref=rival.artifact_id,
        scope=SCOPE_ALL,
        k_frame=2,
        subjects=[incumbent, rival],
        problems=[_frozen_problem(pid, ["k-mechanism"]) for pid in accounted],
        commitments=[_frozen_commitment(cid) for cid in declared],
        consulted=[
            FrozenGrantV1(
                assertion_id="assertion-incumbent",
                subject_ref=incumbent.artifact_id,
                scope=consulted_scope or SCOPE_ALL,
            )
        ],
    )


def _subject(aid, *, accounted, hv, commitments=("k-mechanism",),
             wounds=(), criticised=()):
    return FrozenSubjectV1(
        artifact_id=aid,
        commitments=list(commitments),
        demarcation="load-bearing",
        hv=hv,
        accounted=list(accounted),
        wound_refs=list(wounds),
        criticised_commitments=list(criticised),
    )


def _rival_body(*, subject_ref, wounds, validity="universal", **kwargs):
    from deepreason.calculus.claims import FrameAssertionV1

    return FrameAssertionV1(
        subject_ref=subject_ref,
        scope=SCOPE_ALL,
        validity=validity,
        departure_protocol="cite this id",
        succeeded_wound_refs=list(wounds),
        **kwargs,
    )


# --- the refusal the weak reading would have missed ---------------------------


def test_a_rival_that_only_recovers_is_not_a_successor():
    """R10's first refusal, and the one that carries the mutation proof.

    Everything the weak reading asks for is satisfied: the rival accounts for
    every explicandum the incumbent does, it is no easier to vary, and nothing
    in it is idle. It is still refused, because NOTHING about it is strictly
    better -- same explicanda, same rigidity, same criticism record. A calculus
    that promoted this would let an equally good restatement displace an
    incumbent, which is theory choice by coin flip.
    """
    incumbent = _subject("e", accounted=["p1", "p2"], hv=0.6, wounds=["w1"],
                         criticised=["k-mechanism"])
    rival = _subject("e-prime", accounted=["p1", "p2"], hv=0.6,
                     criticised=["k-mechanism"])
    body = _rival_body(subject_ref="e-prime", wounds=["w1"])
    verdict, detail = promotion.succeeds(_certificate(incumbent=incumbent,
                                                      rival=rival), body)
    assert verdict == "fail", detail
    assert detail["reason"] == "no-strictness-witness"


def test_a_rival_that_recovers_MORE_is_a_successor():
    """The control. Without it the test above would pass for a version of
    `succeeds` that refuses everything."""
    incumbent = _subject("e", accounted=["p1"], hv=0.6, wounds=["w1"])
    rival = _subject("e-prime", accounted=["p1", "p2"], hv=0.6)
    body = _rival_body(subject_ref="e-prime", wounds=["w1"])
    verdict, detail = promotion.succeeds(_certificate(incumbent=incumbent,
                                                      rival=rival), body)
    assert verdict == "pass", detail
    assert detail["strictness"] == "recovery"


# --- one refusal per remaining clause ----------------------------------------


def test_a_rival_that_loses_an_explicandum_is_refused_on_recovery():
    incumbent = _subject("e", accounted=["p1", "p2"], hv=0.6, wounds=["w1"])
    rival = _subject("e-prime", accounted=["p1", "p3"], hv=0.9)
    body = _rival_body(subject_ref="e-prime", wounds=["w1"])
    verdict, detail = promotion.succeeds(_certificate(incumbent=incumbent,
                                                      rival=rival), body)
    assert verdict == "fail"
    assert detail["reason"] == "recovery-fails"
    assert detail["residue"] == ["p2"]


def test_a_lost_explicandum_may_be_recovered_by_a_BOUNDED_validity():
    """§3.5's own escape: `X(e) subset-of X(e')` OR an unrefuted account of why
    `e` worked over its restricted domain. The tree already has the shape for
    that account -- a `bounded` validity naming the residue as its domain -- so
    no new field is invented for it. The account is an ordinary attackable
    claim: refute the assertion and the successor falls with it."""
    incumbent = _subject("e", accounted=["p1", "p2"], hv=0.6, wounds=["w1"])
    rival = _subject("e-prime", accounted=["p1", "p3"], hv=0.9)
    body = _rival_body(
        subject_ref="e-prime", wounds=["w1"], validity="bounded",
        validity_domain="e remains correct over p2, where its idealisation holds",
        validity_tolerance="within the stated idealisation",
    )
    verdict, detail = promotion.succeeds(_certificate(incumbent=incumbent,
                                                      rival=rival), body)
    assert verdict == "pass", detail
    assert detail["strictness"] == "rigidity"


def test_an_easier_to_vary_rival_is_refused_on_rigidity():
    """R10's second refusal. Recovery holds and is even STRICT, so the
    strictness witness is satisfied -- and it is still refused, which is what
    "all four required" means."""
    incumbent = _subject("e", accounted=["p1"], hv=0.8, wounds=["w1"])
    rival = _subject("e-prime", accounted=["p1", "p2"], hv=0.3)
    body = _rival_body(subject_ref="e-prime", wounds=["w1"])
    verdict, detail = promotion.succeeds(_certificate(incumbent=incumbent,
                                                      rival=rival), body)
    assert verdict == "fail"
    assert detail["reason"] == "rival-is-easier-to-vary"


def test_an_unmeasured_rigidity_is_unobtainable_not_a_refusal():
    """Prop 12.1 again. HV is a sampled spot-check that may never have been
    taken; a missing reading is not evidence that the rival is easy to vary."""
    incumbent = _subject("e", accounted=["p1"], hv=None, wounds=["w1"])
    rival = _subject("e-prime", accounted=["p1", "p2"], hv=0.9)
    body = _rival_body(subject_ref="e-prime", wounds=["w1"])
    verdict, detail = promotion.succeeds(_certificate(incumbent=incumbent,
                                                      rival=rival), body)
    assert verdict == "overrun"
    assert detail["reason"] == "rigidity-unmeasured"


def test_a_rival_with_an_excisable_idle_part_is_refused_on_non_immunization():
    """R10's third refusal, and the clause that rejects ad-hoc riders
    MECHANICALLY rather than by taste.

    `k-rider` is idle on all three counts: no registered criticism cites it, no
    problem the rival accounts for asks for it, and it risks nothing empirically.
    Removing it preserves every registered accounting and criticism outcome, so
    it is a proper functional component that does no function.
    """
    incumbent = _subject("e", accounted=["p1"], hv=0.6, wounds=["w1"])
    rival = _subject(
        "e-prime", accounted=["p1", "p2"], hv=0.9,
        commitments=["k-mechanism", "k-rider"], criticised=["k-mechanism"],
    )
    certificate = _certificate(incumbent=incumbent, rival=rival)
    certificate = certificate.model_copy(update={
        "problems": [
            _frozen_problem("p1", ["k-mechanism"]),
            _frozen_problem("p2", ["k-mechanism"]),
        ],
        "commitments": [
            _frozen_commitment("k-mechanism"),
            _frozen_commitment("k-rider"),
        ],
    })
    body = _rival_body(subject_ref="e-prime", wounds=["w1"])
    verdict, detail = promotion.succeeds(certificate, body)
    assert verdict == "fail"
    assert detail["reason"] == "excisable-idle-component"
    assert detail["component"] == "k-rider"


def test_an_observation_valued_component_is_never_idle():
    """The control for the clause above. A commitment that exposes the rival to
    evidence does work by existing, whether or not anything has attacked it
    yet -- so excising it would not preserve what the rival risks."""
    incumbent = _subject("e", accounted=["p1"], hv=0.6, wounds=["w1"])
    rival = _subject(
        "e-prime", accounted=["p1", "p2"], hv=0.9,
        commitments=["k-mechanism", "k-observation"], criticised=["k-mechanism"],
    )
    certificate = _certificate(incumbent=incumbent, rival=rival)
    certificate = certificate.model_copy(update={
        "problems": [
            _frozen_problem("p1", ["k-mechanism"]),
            _frozen_problem("p2", ["k-mechanism"]),
        ],
        "commitments": [
            _frozen_commitment("k-mechanism"),
            _frozen_commitment("k-observation", observation=True),
        ],
    })
    body = _rival_body(subject_ref="e-prime", wounds=["w1"])
    verdict, detail = promotion.succeeds(certificate, body)
    assert verdict == "pass", detail


def test_a_rival_that_survives_a_criticism_the_incumbent_did_not_is_strict():
    """The third road to a strictness witness, and the one that matters for a
    successor with identical coverage and identical rigidity: it survived
    something the incumbent did not."""
    incumbent = _subject("e", accounted=["p1"], hv=0.6, wounds=["w1"],
                         criticised=["k-mechanism"])
    rival = _subject("e-prime", accounted=["p1"], hv=0.6, criticised=[])
    certificate = _certificate(incumbent=incumbent, rival=rival)
    certificate = certificate.model_copy(update={
        "problems": [_frozen_problem("p1", ["k-mechanism"])],
        "commitments": [_frozen_commitment("k-mechanism")],
    })
    body = _rival_body(subject_ref="e-prime", wounds=["w1"])
    verdict, detail = promotion.succeeds(certificate, body)
    assert verdict == "pass", detail
    assert detail["strictness"] == "criticism-survival"


# --- succession is DECLARED, and only over wounds the record knows ------------


def test_with_no_declared_incumbent_the_criterion_passes_vacuously():
    """There is nothing to succeed. The pass is explicitly labelled so a reader
    never mistakes "nobody to beat" for "beat somebody"."""
    incumbent = _subject("e", accounted=["p1", "p2"], hv=0.9, wounds=["w1"])
    rival = _subject("e-prime", accounted=[], hv=0.1)
    body = _rival_body(subject_ref="e-prime", wounds=[])
    verdict, detail = promotion.succeeds(_certificate(incumbent=incumbent,
                                                      rival=rival), body)
    assert verdict == "pass"
    assert detail["reason"] == "no-incumbent"


def test_a_wound_the_record_never_registered_declares_nothing():
    """The wound list is machine-derived from registered warrants (D-6 answer
    A), so a candidate cannot choose which wounds it is answering for by
    inventing one."""
    incumbent = _subject("e", accounted=["p1", "p2"], hv=0.9, wounds=["w1"])
    rival = _subject("e-prime", accounted=[], hv=0.1)
    body = _rival_body(subject_ref="e-prime", wounds=["w-invented"])
    verdict, detail = promotion.succeeds(_certificate(incumbent=incumbent,
                                                      rival=rival), body)
    assert verdict == "pass"
    assert detail["reason"] == "no-incumbent"


def _frozen_problem(pid, criteria):
    from deepreason.calculus.claims import FrozenProblemV1

    return FrozenProblemV1(
        id=pid, description=pid, trigger="seed", criteria=list(criteria)
    )


def _frozen_commitment(cid, *, observation=False):
    from deepreason.calculus.claims import FrozenCommitmentV1

    return FrozenCommitmentV1(
        id=cid, eval="predicate:True", observation_valued=observation
    )
