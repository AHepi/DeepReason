"""The succession trial, and the four things Q2 requires it to record.

Implements R6-R9 and G5 (v2 calculus program, Rung 7), from
`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q2, whose verdict is the reason
this file exists:

    Swap-and-aggregate does not cancel bias. It reduces variance. Require both
    orders anyway, but on the correct justification... Ordering alone flips the
    top-1 candidate on 16-39% of prompts... The bias bites hardest in
    selection, which is exactly what a succession trial is.

So the trial owes four things, and each is a test below:

    Q2a  it judges BOTH orders of the two articulation digests
    Q2b  order-disagreement is a typed NO-VERDICT, never a tiebreak
    Q2c  criterion order is fixed or randomized, and WHICH is recorded
    Q2d  the per-trial FLIP RATE is a first-class recorded diagnostic

The last one is the one a reader would otherwise have to take on trust: "a
succession trial that never reports its flip rate is claiming a precision it
does not have."
"""

import json

from deepreason.calculus import operations
from deepreason.calculus.succession import (
    NEITHER,
    NO_VERDICT,
    ORDER_DISAGREEMENT,
    SUCCESSION_CRITERION_ORDER,
    program_road,
    record_succession_trial,
    rubric_presentation,
    run_succession_trial,
    succession_trial_of,
)
from deepreason.config import Config
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Interface, Provenance, SpawnTrigger
from deepreason.rules.spawn import scan_spawns
from tests.conftest import attack


WIDE = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "or", "args": [
        {"op": "contains", "args": [{"field": "description"}, {"text": "tides"}]},
        {"op": "contains",
         "args": [{"field": "description"}, {"text": "surviving rivals"}]},
    ]},
}


def _art(harness, text):
    return harness.create_artifact(
        text, interface=Interface(), provenance=Provenance(role="critic")
    )


def _rivalry(harness, *, wounds_a=(), wounds_b=(), criteria=("k-beta", "k-alpha")):
    """Two rival frame assertions on one promotion problem, plus the ordinary
    discrimination problem the existing spawn rule mints."""
    incumbent = _art(harness, "b1: the lunar theory of tides")
    rival = _art(harness, "b2: the lunisolar theory of tides")
    case1 = _art(harness, "reach record: three lineages cite the lunar theory")
    case2 = _art(harness, "reach record: three lineages cite the lunisolar theory")
    promotion = operations.ensure_promotion_problem(
        harness, incumbent.id, "promote or refuse a frame for the tides",
        criteria=list(criteria),
    )
    a1 = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=incumbent.id, scope=WIDE,
        reach_case_refs=(case1.id,), departure_protocol="declare it",
        succeeded_wound_refs=list(wounds_a),
    )
    a2 = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=rival.id, scope=WIDE,
        reach_case_refs=(case2.id,), departure_protocol="declare it",
        succeeded_wound_refs=list(wounds_b),
    )
    disc = next(
        p for p in scan_spawns(harness, Config())
        if p.provenance.trigger is SpawnTrigger.DISCRIMINATION
    )
    return incumbent, rival, a1, a2, disc


def _body(harness, artifact) -> dict:
    ref = artifact.content_ref
    raw = (
        ref[len("inline:"):].encode() if ref.startswith("inline:")
        else harness.blobs.get(ref)
    )
    return json.loads(raw)


# --- Q2a: both orders, of the two articulation digests -----------------------

def test_the_program_road_judges_both_orders(harness):
    """Q2a for the road that needs no seat. The program's verdict is
    order-invariant by construction -- and running it BOTH ways is what turns
    that from an assertion into a recorded fact. A road that skipped the second
    order because it knew the answer would be claiming an invariance it never
    exhibited."""
    _, _, _, _, disc = _rivalry(harness)
    trial = succession_trial_of(harness, disc.id)
    evaluations = program_road(harness, trial)

    assert len(evaluations) == 1
    orders = evaluations[0]["orders"]
    assert [o["order"] for o in orders] == ["ab", "ba"]
    assert evaluations[0]["flipped"] is False


def test_the_rubric_road_is_handed_the_articulation_digests(harness):
    """Q2a's own words. A judge handed the frame ASSERTIONS would be comparing
    paperwork -- the JSON claim bodies -- rather than the two accounts of the
    world that §9.7 says the succession pack renders."""
    incumbent, rival, a1, a2, disc = _rivalry(harness)
    trial = succession_trial_of(harness, disc.id)
    presentation = rubric_presentation(harness, trial, a1.id, a2.id)

    assert "the lunar theory of tides" in presentation.a_text
    assert "the lunisolar theory of tides" in presentation.b_text
    # the assertions' own bytes are NOT what is judged
    assert "declarative-scope.v1" not in presentation.a_text
    assert "subject_ref" not in presentation.a_text
    assert presentation.criteria == ("k-alpha", "k-beta")


# --- Q2b: order-disagreement is a typed no-verdict ---------------------------

def test_a_constructed_order_disagreement_is_a_no_verdict(harness):
    """G5's constructed case, and the point of the whole file.

    A judge that names the SAME PRESENTED LABEL in both orders has expressed a
    positional preference, not a discrimination. The trial records
    `no-verdict`, names the reason, and picks NOTHING from either order -- and
    both candidates keep their labels, so the rivalry is still open.
    """
    _, _, a1, a2, disc = _rivalry(harness)
    same_slot = json.dumps({"winner": "A", "decisive_point": "lunar"})
    adapter = LLMAdapter(
        {"judge": MockEndpoint([same_slot, same_slot])}, harness.blobs, retry_max=2
    )
    artifact = run_succession_trial(
        harness, harness.state.problems[disc.id], adapter, Config(),
        authority="status",
    )
    body = _body(harness, artifact)

    rubric = [e for e in body["evaluations"] if e["road"] == "rubric"]
    assert len(rubric) == 1
    assert rubric[0]["flipped"] is True
    assert rubric[0]["outcome"] == NO_VERDICT
    assert rubric[0]["no_verdict_reason"] == ORDER_DISAGREEMENT
    assert body["outcome"] == NO_VERDICT
    # NEVER A TIEBREAK. Both orders named a candidate; the trial adopted
    # neither, and the disagreement is the outcome rather than an input to one.
    tops = [o["top"] for o in rubric[0]["orders"]]
    assert tops == [a1.id, a2.id] or tops == [a2.id, a1.id]
    assert body["outcome"] not in tops
    from deepreason.ontology import Status

    assert harness.state.status[a1.id] is Status.ACCEPTED
    assert harness.state.status[a2.id] is Status.ACCEPTED


def test_the_no_verdict_routes_onward_rather_than_resolving(harness):
    """"Flag and route onward, the way the harness already treats
    no-consensus." The existing guard's own `trial-blocked:order-swap` measure
    is what does the flagging -- reused, not reimplemented."""
    _, _, _, _, disc = _rivalry(harness)
    same_slot = json.dumps({"winner": "A", "decisive_point": "lunar"})
    adapter = LLMAdapter(
        {"judge": MockEndpoint([same_slot, same_slot])}, harness.blobs, retry_max=2
    )
    run_succession_trial(
        harness, harness.state.problems[disc.id], adapter, Config(),
        authority="status",
    )
    blocked = [
        e for e in harness.log.read()
        if any(t == "trial-blocked:order-swap" for t in e.inputs)
    ]
    assert blocked


def test_a_consistent_ruling_is_not_a_flip(harness):
    """The control. When the judge names the same REAL candidate under both
    presentations, the trial has a verdict and the flip rate is 0.0 -- so the
    no-verdict road above is not simply what this instrument always says."""
    incumbent, rival, a1, a2, disc = _rivalry(harness)
    responses = [
        json.dumps({"winner": "A", "decisive_point": "lunar"}),
        json.dumps({"winner": "B", "decisive_point": "lunar"}),
    ]
    adapter = LLMAdapter(
        {"judge": MockEndpoint(responses)}, harness.blobs, retry_max=2
    )
    artifact = run_succession_trial(
        harness, harness.state.problems[disc.id], adapter, Config(),
        authority="observe_only",
    )
    body = _body(harness, artifact)
    rubric = [e for e in body["evaluations"] if e["road"] == "rubric"][0]
    assert rubric["flipped"] is False
    assert rubric["outcome"] == sorted([a1.id, a2.id])[0]
    assert rubric["no_verdict_reason"] is None


# --- Q2c: criterion order, fixed, and recorded -------------------------------

def test_the_criterion_order_is_recorded_and_is_fixed(harness):
    """Q2c. Q2's second orthogonal axis: 56 of 60 (judge, criterion) tests were
    significant, shifting a criterion's mean by up to 0.80 points on a 5-point
    scale. Fixing the order does not remove the shift -- it makes it CONSTANT,
    and recording it is what lets a later reader account for it."""
    _, _, _, _, disc = _rivalry(harness, criteria=("k-beta", "k-alpha"))
    artifact = record_succession_trial(harness, disc.id)
    body = _body(harness, artifact)

    assert body["criterion_order"] == SUCCESSION_CRITERION_ORDER == "fixed"
    assert body["criteria"] == ["k-alpha", "k-beta"]


def test_the_recorded_order_is_the_order_the_judge_saw(harness):
    """A recorded order that differed from the presented one would be worse
    than no record at all: it would let a reader correct for a bias that was
    never applied."""
    _, _, a1, a2, disc = _rivalry(harness, criteria=("k-beta", "k-alpha"))
    trial = succession_trial_of(harness, disc.id)
    body = _body(harness, record_succession_trial(harness, disc.id))
    assert list(rubric_presentation(harness, trial, a1.id, a2.id).criteria) == (
        body["criteria"]
    )


# --- Q2d: the flip rate, first-class -----------------------------------------

def test_the_flip_rate_is_a_field_not_a_derivation(harness):
    """Q2d. "A succession trial that never reports its flip rate is claiming a
    precision it does not have." So it is a FIELD, with its numerator and
    denominator beside it -- a bare rate cannot be told from an empty one."""
    _, _, _, _, disc = _rivalry(harness)
    body = _body(harness, record_succession_trial(harness, disc.id))

    assert "flip_rate" in body and "flips" in body and "evaluated" in body
    assert body["evaluated"] == 1
    assert body["flip_rate"] == 0.0


def test_a_flipped_trial_reports_a_flip_rate_of_one(harness):
    """The rate moves with the evidence, which is what makes it a diagnostic
    rather than a constant."""
    _, _, _, _, disc = _rivalry(harness)
    same_slot = json.dumps({"winner": "A", "decisive_point": "lunar"})
    adapter = LLMAdapter(
        {"judge": MockEndpoint([same_slot, same_slot])}, harness.blobs, retry_max=2
    )
    body = _body(harness, run_succession_trial(
        harness, harness.state.problems[disc.id], adapter, Config(),
        authority="status",
    ))
    # one program evaluation (no flip) + one rubric evaluation (flipped)
    assert body["evaluated"] == 2
    assert body["flips"] == 1
    assert body["flip_rate"] == 0.5


def test_an_empty_rate_cannot_be_read_as_a_clean_one(harness):
    """The failure mode a bare `0.0` would hide: nothing was judged. Both
    numbers are always present, so `0.0` beside `evaluated: 0` reads as what it
    is."""
    from deepreason.calculus.succession import SuccessionTrial, trial_record

    empty = SuccessionTrial(
        problem_id="disc:x", promotion_problem="promotion:x",
        rival_ids=(), subject_ids=(), criteria=(),
    )
    body = trial_record(empty, [])
    assert body["flip_rate"] == 0.0 and body["evaluated"] == 0


def test_the_flip_rate_reaches_the_measure_stream(harness):
    """First-class means a reader of the RECORD finds it, not only a reader of
    the artifact. The receipt carries the rate and the outcome."""
    _, _, _, _, disc = _rivalry(harness)
    record_succession_trial(harness, disc.id)
    measures = [
        e for e in harness.log.read()
        if any(t == "succession.trial-flip-rate.v1" for t in e.inputs)
    ]
    assert measures
    assert "0.0000" in measures[-1].inputs


# --- the program road, and the solo law --------------------------------------

def test_succession_runs_with_no_judge_seat_at_all(harness):
    """The operator's standing law: "a solo run with everything on should be an
    option". The program road needs no seat, so a solo run still holds a
    succession trial and still reports its flip rate."""
    _, _, _, _, disc = _rivalry(harness)
    artifact = run_succession_trial(
        harness, harness.state.problems[disc.id], None, Config(),
        authority="observe_only",
    )
    body = _body(harness, artifact)
    assert body["evaluated"] == 1
    assert [e["road"] for e in body["evaluations"]] == ["program"]
    assert body["rubric_pairs_judged"] == 0


def test_the_program_separates_the_two_where_the_record_does(harness):
    """D-6 answer A: a program adjudicates where a program can. A candidate
    that declares wounds of the incumbent it accounts for has done work the
    other has not, and that is a fact about the record."""
    _, _, a1, a2, disc = _rivalry(
        harness, wounds_a=(), wounds_b=("w-perihelion", "w-lag")
    )
    body = _body(harness, record_succession_trial(harness, disc.id))
    evaluation = body["evaluations"][0]
    assert evaluation["outcome"] == a2.id
    assert all(o["reason"] == "accounts-for-strictly-more"
               for o in evaluation["orders"])


def test_the_program_says_neither_rather_than_guessing(harness):
    """And where it cannot, the fallback is VISIBLE. `neither` is an answer and
    it is the honest one -- the alternative is theory choice by coin flip,
    which is exactly what the STRONG succession relation refuses."""
    _, _, _, _, disc = _rivalry(
        harness, wounds_a=("w-lag",), wounds_b=("w-lag",)
    )
    body = _body(harness, record_succession_trial(harness, disc.id))
    evaluation = body["evaluations"][0]
    assert evaluation["outcome"] == NEITHER
    assert all(o["reason"] == "both-account-for-the-same-wounds"
               for o in evaluation["orders"])


# --- the record itself -------------------------------------------------------

def test_the_trial_record_never_becomes_a_rival(harness):
    """`file_premise`'s recorded reason, applied here: an artifact ADDRESSING
    the discrimination problem enters `addr` and becomes a candidate in the
    rivalry it is a diagnostic of."""
    _, _, _, _, disc = _rivalry(harness)
    artifact = record_succession_trial(harness, disc.id)
    assert not [pid for aid, pid in harness.state.addr if aid == artifact.id]


def test_the_trial_record_is_attackable(harness):
    """P6. A diagnostic nobody can attack is a diagnostic nobody can correct --
    "your trial was mis-conducted" has to have somewhere to land."""
    from deepreason.ontology import Status

    _, _, _, _, disc = _rivalry(harness)
    artifact = record_succession_trial(harness, disc.id)
    assert harness.state.status[artifact.id] is Status.ACCEPTED
    attack(harness, artifact.id, "the-trial-judged-the-wrong-digests")
    assert harness.state.status[artifact.id] is Status.REFUTED


def test_recording_an_unchanged_trial_registers_nothing_new(harness):
    """Content-addressed, so a re-record is idempotent rather than a duplicate
    -- the same discipline `ensure_problem_subject` uses."""
    _, _, _, _, disc = _rivalry(harness)
    first = record_succession_trial(harness, disc.id)
    before = set(harness.state.artifacts)
    second = record_succession_trial(harness, disc.id)
    assert second.id == first.id
    assert set(harness.state.artifacts) == before


def test_an_ordinary_discrimination_records_no_trial(harness):
    """The instrument is narrow: nothing is recorded for a problem that is not
    a succession trial."""
    assert record_succession_trial(harness, "not-a-problem") is None


def test_the_rubric_bound_is_disclosed_rather_than_silent(harness):
    """No silent caps. The rubric road costs two provider calls per pair, so a
    caller may bound it -- and a bound nobody can see reads as full
    coverage."""
    _, _, _, _, disc = _rivalry(harness)
    body = _body(harness, record_succession_trial(harness, disc.id))
    assert body["rubric_pairs_available"] == 1
    assert body["rubric_pairs_judged"] == 0
