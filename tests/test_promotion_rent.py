"""§9.3's RENT, as promotion criterion 6 (R1, v2 calculus Rung 8).

    Promotion is purchase of exposure. [...] promotion is an articulation
    event: a tacit framework becomes promotable only when factored into
    vocabulary, enumerated assumptions, and commitments — because the
    assumption ids are what departures declare against, and the commitments are
    what wounds violate. Articulation is not overhead; it is the manufacture of
    the attack surface.  (§9.3)

Half of §9.3 already shipped at Rung 5 inside criterion 1: `active(b)` is
`demarcation == "load-bearing"` (§9.3's own `active(a) ⇔ crit ∧ mod`), and the
observation-valued clause is `subject_demarcation`'s first branch. What was NOT
on the tree is ARTICULATION, and that is what this criterion is.

It is a SIXTH criterion rather than an extension of the first because the two
answer different questions — does the subject forbid anything, versus is what
it forbids ENUMERABLE — and a candidate can pass either and fail the other. One
`fail` reason covering two defects is what makes a promotion refusal
unanswerable in practice: a critic cannot argue with a verdict that does not
say which thing was wrong.
"""

import json

import pytest

from deepreason.calculus import nomination, operations, promotion
from deepreason.calculus.claims import ReachCertificateV1, decode
from deepreason.config import Config
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    SpawnTrigger,
    Status,
)
from deepreason.programs import content_text, evaluate

SCOPE_ALL = {"schema": "declarative-scope.v1", "predicate": {"const": True}}


def _problem(harness, pid, *, trigger=SpawnTrigger.SEED, sources=(), criteria=()):
    return harness.register_problem(
        Problem(
            id=pid,
            description=f"problem {pid}",
            criteria=list(criteria),
            provenance=ProblemProvenance.model_validate(
                {"trigger": trigger, "from": list(sources)}
            ),
        )
    )


def _substantive(harness, cid, expr="len(content) > 0", *, observation=False):
    kappa = Commitment(id=cid, eval=f"predicate:{expr}", observation_valued=observation)
    harness.register_commitment(kappa)
    return kappa


def _subject(harness, text, problem_id, commitments=()):
    artifact = harness.create_artifact(
        text,
        interface=Interface(commitments=list(commitments)),
        provenance=Provenance(role="conjecturer"),
        problem_id=problem_id,
    )
    assert harness.state.status.get(artifact.id) is Status.ACCEPTED
    return artifact


def _nominate(harness, *, subject_text="b: one account of both domains",
              subject_commitments=None, config=None):
    """One subject reaching two lineages, nominated, with its certificate."""
    kappa = _substantive(harness, "k-left")
    left = _problem(harness, "question-left", criteria=[kappa.id])
    right = _problem(harness, "question-right", criteria=[kappa.id])
    commitments = [kappa.id] if subject_commitments is None else subject_commitments
    subject = _subject(harness, subject_text, left.id, commitments)
    harness.record_measure(reach={subject.id: 1.0}, addr=[(subject.id, right.id)])
    problems = nomination.nominate(harness, config or Config(K_FRAME=2))
    assert len(problems) == 1
    certificate = next(
        harness.state.artifacts[aid]
        for aid in harness.state.artifacts
        if "claim:reach-certificate-wf@v1"
        in harness.state.artifacts[aid].interface.commitments
    )
    return subject, problems[0], certificate, list(problems[0].criteria)


def _criterion(harness, criteria, name):
    return next(
        harness.commitments[cid] for cid in criteria
        if harness.commitments[cid].eval == f"program:{name}"
    )


def _candidate(harness, problem, *, subject_ref, cases, **kwargs):
    return operations.file_frame_assertion(
        harness,
        problem=problem,
        subject_ref=subject_ref,
        scope=kwargs.pop("scope", SCOPE_ALL),
        departure_protocol="declare the departure in the pack and cite this id",
        reach_case_refs=list(cases),
        **kwargs,
    )


def _rent(harness, criteria, candidate):
    return evaluate(_criterion(harness, criteria, promotion.RENT), candidate,
                    harness.blobs)


# --- registration --------------------------------------------------------------


def test_rent_is_a_sixth_pinned_criterion(harness):
    from deepreason import programs

    assert len(promotion.PROMOTION_PROGRAMS) == 6
    assert promotion.RENT in promotion.PROMOTION_PROGRAMS
    # Dual registration, for the reason `promotion.py`'s own module docstring
    # gives: a criterion living only in BLOB_PROGRAMS counts as SUBSTANTIVE,
    # grounds reach and confers prose immunity. Promotion paperwork must do
    # neither.
    assert promotion.RENT in programs.PROGRAMS
    assert promotion.RENT in programs.BLOB_PROGRAMS
    assert programs.PROGRAMS[promotion.RENT].class_ == "structural"


def test_every_promotion_problem_pins_rent(harness):
    _, problem, _, criteria = _nominate(harness)
    evals = {harness.commitments[cid].eval for cid in criteria}
    assert f"program:{promotion.RENT}" in evals


# --- leg 1: commitments ("what wounds violate") -----------------------------------


def test_rent_refuses_a_subject_that_enumerates_no_commitments(harness):
    """A background that declares no commitment has nothing a wound could
    violate, so its exposure is nil and it cannot be purchasing any."""
    subject, problem, certificate, criteria = _nominate(
        harness, subject_commitments=[]
    )
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = _rent(harness, criteria, candidate)
    assert verdict == "fail", (verdict, detail)
    assert detail["reason"] == "subject-enumerates-no-commitments"


# --- leg 2: enumerated assumptions ("what departures declare against") ------------


def test_rent_refuses_an_assumption_id_nothing_enumerates(harness):
    """The ids a departure may name are the subject's own commitment ids
    (`DepartureDeclarationV1.broken_ids`, `render.frame_obligations`). An id a
    departure could name but nothing DEFINES is an unenumerable assumption --
    the departure protocol would accept it and no one could evaluate it."""
    subject, problem, certificate, criteria = _nominate(harness)
    body = decode(content_text(certificate, harness.blobs))
    assert isinstance(body, ReachCertificateV1)
    stripped = body.model_copy(update={"commitments": []})
    doctored = promotion.criteria_for(harness.blobs.put(stripped.model_dump_json(
        by_alias=True, exclude_none=True).encode()))
    kappa = next(k for k in doctored if k.eval == f"program:{promotion.RENT}")
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = evaluate(kappa, candidate, harness.blobs)
    assert verdict == "fail", (verdict, detail)
    assert detail["reason"] == "assumption-id-not-enumerated"


def test_a_truncated_environment_is_overrun_and_never_fail(harness):
    """"We could not check" must never look like "we checked and it was fine",
    and it must never look like a refutation either. When the certificate's own
    cap dropped the id, the verdict is `overrun` -- pending, minting nothing."""
    subject, problem, certificate, criteria = _nominate(harness)
    body = decode(content_text(certificate, harness.blobs))
    missing = body.subjects[0].commitments[0]
    stripped = body.model_copy(update={
        "commitments": [],
        "truncated": [f"commitment:{missing}"],
    })
    doctored = promotion.criteria_for(harness.blobs.put(stripped.model_dump_json(
        by_alias=True, exclude_none=True).encode()))
    kappa = next(k for k in doctored if k.eval == f"program:{promotion.RENT}")
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = evaluate(kappa, candidate, harness.blobs)
    assert verdict == "overrun", (verdict, detail)


# --- leg 3: vocabulary --------------------------------------------------------------


def test_rent_refuses_a_subject_that_states_no_vocabulary(harness):
    """A frame whose subject renders as nothing states no terms, and the frame
    slice would show an empty coordinate system to every conjecture in scope."""
    subject, problem, certificate, criteria = _nominate(
        harness, subject_text="   \n\t  "
    )
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = _rent(harness, criteria, candidate)
    assert verdict == "fail", (verdict, detail)
    assert detail["reason"] == "subject-states-no-vocabulary"


# --- the pass, and what it does NOT do ------------------------------------------------


def test_an_articulated_subject_pays_the_rent(harness):
    subject, problem, certificate, criteria = _nominate(harness)
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = _rent(harness, criteria, candidate)
    assert verdict == "pass", (verdict, detail)
    assert detail["assumptions"] and detail["commitments"]


def test_rent_is_unobtainable_on_something_that_is_not_a_frame_claim(harness):
    """Remark 9.5's rule, which rent inherits rather than re-decides: the
    promotion problem's OWN paperwork makes no frame claim, and returning
    `fail` would mint a warrant against the problem's own evidence."""
    _, _, certificate, criteria = _nominate(harness)
    verdict, detail = _rent(harness, criteria, certificate)
    assert verdict == "overrun", (verdict, detail)


def test_rent_reads_the_frozen_certificate_and_not_live_state(harness):
    """Rider 5 clause (4). Registering another commitment on the live subject
    after the certificate was frozen must not move the verdict."""
    subject, problem, certificate, criteria = _nominate(harness)
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    first = _rent(harness, criteria, candidate)
    _substantive(harness, "k-late")
    second = _rent(harness, criteria, candidate)
    assert first == second


# --- S2's guard, written here so step 19 has one --------------------------------------


def test_the_scope_bound_comes_from_the_certificate_not_the_config(harness):
    """Prop 12.1. The scope-predicate budget is configurable, but a criterion's
    verdict may not move when a run's configuration moves and the commitment
    does not -- so the bound travels INSIDE the certificate, exactly as
    `k_frame` does.
    """
    subject, problem, certificate, criteria = _nominate(
        harness, config=Config(K_FRAME=2, SCOPE_MAX_NODES=512)
    )
    body = decode(content_text(certificate, harness.blobs))
    assert body.scope_max_nodes == 512
    assert body.scope_max_depth == 16

    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    kappa = _criterion(harness, criteria, promotion.SCOPE_DETERMINISM)
    before = evaluate(kappa, candidate, harness.blobs)
    # A hostile config cannot reach a frozen verdict.
    tightened = Config(K_FRAME=2, SCOPE_MAX_NODES=1, SCOPE_MAX_DEPTH=1)
    assert tightened.SCOPE_MAX_NODES == 1
    after = evaluate(kappa, candidate, harness.blobs)
    assert before == after
