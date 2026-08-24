"""The five pinned promotion criteria as programs (§9.4, R4, R13).

Each criterion is a pure function of the CANDIDATE's bytes and interface plus
ONE frozen, fence-stamped reach certificate fetched from the blob store by
digest. Nothing here reads live graph state (Rider 5 clause 4), which is what
makes a promotion verdict reproducible.

`overrun` is used throughout for UNOBTAINABLE and never for slow (Prop 12.1,
C2). The distinction is load-bearing rather than pedantic: `DR-SEAM-evaluation-
x-rules`'s own agreement makes a verdict an epistemic move only through
`register_fail_warrant` and only from a `fail`, so an `overrun` is pending and
mints nothing. "We could not check" must never look like "we checked and it was
fine".
"""

import json

import pytest

from deepreason.calculus import nomination, operations, promotion
from deepreason.calculus.claims import FrameAssertionV1, encode
from deepreason.calculus.compiler import compile_interface
from deepreason.config import Config
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
    Provenance,
    SpawnTrigger,
    Status,
)
from deepreason.ontology.commitment import Budget
from deepreason.programs import evaluate

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
    kappa = Commitment(
        id=cid, eval=f"predicate:{expr}", observation_valued=observation
    )
    harness.register_commitment(kappa)
    return kappa


def _subject(harness, text, problem_id, commitments=()):
    from deepreason.ontology import Interface

    artifact = harness.create_artifact(
        text,
        interface=Interface(commitments=list(commitments)),
        provenance=Provenance(role="conjecturer"),
        problem_id=problem_id,
    )
    assert harness.state.status.get(artifact.id) is Status.ACCEPTED
    return artifact


@pytest.fixture
def nominated(harness):
    """One subject reaching two lineages, nominated, with its certificate.

    Returns `(subject, promotion_problem, certificate_artifact, criteria)`.
    """
    kappa = _substantive(harness, "k-left")
    left = _problem(harness, "question-left", criteria=[kappa.id])
    right = _problem(harness, "question-right", criteria=[kappa.id])
    subject = _subject(harness, "b: one account of both domains", left.id, [kappa.id])
    harness.record_measure(reach={subject.id: 1.0}, addr=[(subject.id, right.id)])
    problems = nomination.nominate(harness, Config(K_FRAME=2))
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


def _verdict(harness, criteria, name, candidate):
    return evaluate(_criterion(harness, criteria, name), candidate, harness.blobs)


# --- the shared frozen-input contract ----------------------------------------


def test_a_criterion_reads_its_certificate_by_digest(nominated, harness):
    subject, problem, certificate, criteria = nominated
    kappa = _criterion(harness, criteria, promotion.SCOPE_DETERMINISM)
    spec = json.loads(kappa.budget.extra["spec"])
    assert spec["certificate_ref"] == certificate.content_ref
    assert certificate.content_ref[:12] in kappa.id


def test_a_criterion_with_no_certificate_is_unobtainable(nominated, harness):
    """No frozen input means no verdict, and that is `overrun`, not `fail`."""
    subject, problem, certificate, criteria = nominated
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    orphan = Commitment(
        id="promotion:orphan", eval=f"program:{promotion.SCOPE_DETERMINISM}",
        budget=Budget(steps=10, time_ms=10),
    )
    verdict, detail = evaluate(orphan, candidate, harness.blobs)
    assert verdict == "overrun", (verdict, detail)


def test_a_criterion_on_something_that_is_not_a_frame_claim_is_unobtainable(
    nominated, harness
):
    """Remark 9.5's other half, from the criteria's side. An ordinary artifact
    addressed to a promotion problem -- the problem's own companion subject, the
    certificate itself -- makes no frame claim, so the promotion relation is
    UNOBTAINABLE for it rather than false. Returning `fail` here would mint a
    warrant against every piece of the promotion problem's own paperwork."""
    subject, problem, certificate, criteria = nominated
    for name in promotion.PROMOTION_PROGRAMS:
        verdict, detail = _verdict(harness, criteria, name, certificate)
        assert verdict == "overrun", (name, verdict, detail)


# --- criterion 1: subject-demarcation (S4, R8) -------------------------------


def test_demarcation_refuses_a_subject_that_declares_nothing(harness):
    """`crit` alone settles this and needs no sample: an interface that
    declares nothing at all forbids nothing, so there is no attack surface to
    be load-bearing on. Rung 2's rule, transferred."""
    left = _problem(harness, "question-left")
    right = _problem(harness, "question-right")
    bare = _subject(harness, "b: a claim that forbids nothing", left.id)
    harness.record_measure(reach={bare.id: 1.0}, addr=[(bare.id, right.id)])
    problem = nomination.nominate(harness, Config(K_FRAME=2))[0]
    certificate = next(
        a for a in harness.state.artifacts.values()
        if "claim:reach-certificate-wf@v1" in a.interface.commitments
    )
    candidate = _candidate(harness, problem, subject_ref=bare.id,
                           cases=[certificate.id])
    verdict, detail = _verdict(
        harness, problem.criteria, promotion.SUBJECT_DEMARCATION, candidate
    )
    assert verdict == "fail"
    assert detail["reason"] == "subject-declares-nothing"


def test_demarcation_abstains_when_the_load_reading_was_never_taken(
    nominated, harness
):
    """Rung 2's cost answer, carried forward. The `load` half needs the variator
    seat and one provider call per subject; nomination has no seat, so what it
    freezes is `declared-only` and the criterion returns `overrun`."""
    subject, problem, certificate, criteria = nominated
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = _verdict(
        harness, criteria, promotion.SUBJECT_DEMARCATION, candidate
    )
    assert verdict == "overrun"
    assert detail["reason"] == "demarcation-undecided-no-variator"


def test_an_empirical_scope_needs_an_observation_valued_commitment(harness):
    """§12.2's closing clause, the one Rung 2 could not meet (R8, drift row S-5).

    Checked BEFORE the demarcation reading on purpose: the empirical clause is
    fully decidable from the frozen record with no seat, so letting the
    variator abstention short-circuit it would hide a real refusal behind an
    honest "could not check"."""
    observed = _substantive(harness, "k-observed", observation=True)
    plain = _substantive(harness, "k-plain")
    left = _problem(harness, "question-left", criteria=[observed.id])
    right = _problem(harness, "question-right", criteria=[observed.id])
    subject = _subject(harness, "b: an account carrying no observation",
                       left.id, [plain.id])
    harness.record_measure(reach={subject.id: 1.0}, addr=[(subject.id, right.id)])
    problem = nomination.nominate(harness, Config(K_FRAME=2))[0]
    certificate = next(
        a for a in harness.state.artifacts.values()
        if "claim:reach-certificate-wf@v1" in a.interface.commitments
    )
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = _verdict(
        harness, problem.criteria, promotion.SUBJECT_DEMARCATION, candidate
    )
    assert verdict == "fail"
    assert detail["reason"] == "empirical-scope-without-observation-valued-commitment"


# --- criterion 2: reach-integrity (S5, I-6) ----------------------------------


def test_reach_integrity_refuses_a_candidate_that_cites_no_case(
    nominated, harness
):
    subject, problem, certificate, criteria = nominated
    candidate = _candidate(harness, problem, subject_ref=subject.id, cases=[])
    verdict, detail = _verdict(
        harness, criteria, promotion.REACH_INTEGRITY, candidate
    )
    assert verdict == "fail"
    assert detail["reason"] == "no-reach-case"


def test_reach_integrity_refuses_a_case_the_record_does_not_know(
    nominated, harness
):
    """A case nomination did not freeze cannot have its provenance checked, so
    it is refused rather than taken on trust."""
    subject, problem, certificate, criteria = nominated
    invented = harness.create_artifact(
        "a case nobody recorded", provenance=Provenance(role="critic")
    )
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[invented.id])
    verdict, detail = _verdict(
        harness, criteria, promotion.REACH_INTEGRITY, candidate
    )
    assert verdict == "fail"
    assert detail["reason"] == "reach-case-not-in-the-record"


def test_reach_integrity_accepts_the_certificate_as_the_case(nominated, harness):
    subject, problem, certificate, criteria = nominated
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = _verdict(
        harness, criteria, promotion.REACH_INTEGRITY, candidate
    )
    assert verdict == "pass", detail


def test_reach_integrity_reads_the_log_s_own_ordering(nominated, harness):
    """§10.5's novel-fact criterion, mechanized: the log timestamps prove the
    artifact predates what it went on to survive. A record whose subject was
    registered AFTER the measure that credited it is refused."""
    subject, problem, certificate, criteria = nominated
    assert promotion.ordering_holds(
        [{"subject_seq": 1, "measure_seq": 2, "reveal_seq": None}]
    )
    assert not promotion.ordering_holds(
        [{"subject_seq": 5, "measure_seq": 2, "reveal_seq": None}]
    )
    # Sealed evidence revealed BEFORE the subject existed is not a novel fact.
    assert not promotion.ordering_holds(
        [{"subject_seq": 5, "measure_seq": 9, "reveal_seq": 3}]
    )
    assert promotion.ordering_holds(
        [{"subject_seq": 5, "measure_seq": 9, "reveal_seq": 7}]
    )


# --- criterion 3: scope-determinism (S6, C1) ---------------------------------


def test_scope_determinism_passes_a_scope_in_the_closed_DSL(nominated, harness):
    subject, problem, certificate, criteria = nominated
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = _verdict(
        harness, criteria, promotion.SCOPE_DETERMINISM, candidate
    )
    assert verdict == "pass", detail


def test_scope_determinism_refuses_a_scope_that_does_not_compile(
    nominated, harness
):
    """`file_frame_assertion` compiles the scope at authoring time, so an
    uncompilable scope reaches a criterion only on an artifact registered
    around that operation -- which is exactly what an adversary would do."""
    subject, problem, certificate, criteria = nominated
    from deepreason.calculus.programs import FRAME_ASSERTION_COMMITMENT

    harness.register_commitment(FRAME_ASSERTION_COMMITMENT)
    body = FrameAssertionV1(
        subject_ref=subject.id,
        scope={"schema": "declarative-scope.v1",
               "predicate": {"op": "teleport", "args": []}},
        departure_protocol="cite this id",
        reach_case_refs=[certificate.id],
    )
    candidate = harness.create_artifact(
        encode(body), codec="json", interface=compile_interface(body),
        problem_id=problem.id, provenance=Provenance(role="conjecturer"),
    )
    verdict, detail = _verdict(
        harness, criteria, promotion.SCOPE_DETERMINISM, candidate
    )
    assert verdict == "fail"
    assert detail["reason"] == "scope-does-not-compile"


def test_a_scope_too_large_for_the_DSL_is_unobtainable_not_false(
    nominated, harness
):
    """C2 again: exceeding a declared bound means the verdict could not be
    obtained. A `fail` here would refuse a candidate for being big."""
    subject, problem, certificate, criteria = nominated
    deep = {"const": True}
    for _ in range(40):
        deep = {"op": "not", "args": [deep]}
    from deepreason.calculus.programs import FRAME_ASSERTION_COMMITMENT

    harness.register_commitment(FRAME_ASSERTION_COMMITMENT)
    body = FrameAssertionV1(
        subject_ref=subject.id,
        scope={"schema": "declarative-scope.v1", "predicate": deep},
        departure_protocol="cite this id",
        reach_case_refs=[certificate.id],
    )
    candidate = harness.create_artifact(
        encode(body), codec="json", interface=compile_interface(body),
        problem_id=problem.id, provenance=Provenance(role="conjecturer"),
    )
    verdict, detail = _verdict(
        harness, criteria, promotion.SCOPE_DETERMINISM, candidate
    )
    assert verdict == "overrun", detail


# --- criterion 4: compatibility (S7) -----------------------------------------


def test_compatibility_passes_when_nothing_is_consulted(nominated, harness):
    subject, problem, certificate, criteria = nominated
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    verdict, detail = _verdict(
        harness, criteria, promotion.COMPATIBILITY, candidate
    )
    assert verdict == "pass", detail


# --- Prop 12.1: every criterion terminates inside its declared budget ---------


def test_every_criterion_overruns_on_a_zero_budget(nominated, harness):
    """Prop 12.1 (R13). Zero declared steps is a bound that cannot be met, and
    every criterion says so with `overrun` rather than guessing."""
    subject, problem, certificate, criteria = nominated
    candidate = _candidate(harness, problem, subject_ref=subject.id,
                           cases=[certificate.id])
    for name in promotion.PROMOTION_PROGRAMS:
        kappa = _criterion(harness, criteria, name)
        starved = Commitment(
            id=f"{kappa.id}#starved", eval=kappa.eval,
            budget=Budget(steps=0, time_ms=0, extra=dict(kappa.budget.extra)),
        )
        verdict, detail = evaluate(starved, candidate, harness.blobs)
        assert verdict == "overrun", (name, verdict, detail)
        assert detail.get("reason") == "budget-exhausted", (name, detail)


def test_no_criterion_grounds_reach_or_confers_prose_immunity(harness):
    """A8, from the other side. A promotion criterion that counted SUBSTANTIVE
    would ground reach -- and reach is what nominates, so promotion paperwork
    would manufacture the signal that produced it. It would also sell prose
    immunity for `promotion_accounts_for`'s VACUOUS pass, which is what an
    artifact gets when there is no incumbent to succeed."""
    from deepreason.measures.reach import _STRUCTURAL_PROGRAMS, _substantive as sub
    from deepreason.programs import PROGRAMS, programs_by_class

    declared = set(programs_by_class()["structural"])
    assert declared == set(_STRUCTURAL_PROGRAMS)
    for name in promotion.PROMOTION_PROGRAMS + ("reach_certificate_wf",):
        assert name in PROGRAMS, name
        assert name in declared, name
        assert sub(Commitment(id=f"k-{name}", eval=f"program:{name}")) is False
