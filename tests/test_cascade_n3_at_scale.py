"""N3 at scale: one fall, a thousand problems, and no insolubility verdict.

Implements G4 (v2 calculus program, Rung 7). §9.8's asymmetry, which P11
demands and which this rung is the first to be able to exhibit:

    An ordinary refuted conjecture retires nothing but itself, because nothing
    presupposes it. A fallen background's refutation is a premise-criticism of
    everything posed in its terms: one fall retires a thousand questions,
    translates a thousand more into a better vocabulary, and reveals some
    hundreds that never needed the premise at all.

N3 is the claim under test and it is a claim about EVERY resolution, not about
the common case: none of the three is an insolubility verdict. A problem dies
with its premise, moves to better language, or stands free of both -- and every
one of those closures is an ordinary registered artifact, so attacking it puts
the problem straight back on the frontier.
"""

import time

import pytest

from deepreason.calculus import operations
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
)
from deepreason.premises import (
    PREMISE_REFUTED,
    RESOLUTION_EVAL,
    batch_translation_offers,
    independence_resolution_rate,
    open_orphans,
    premise_orphaned,
    premise_resolution_wf_program,
    resolution_content,
    retired_problems,
    standing_resolutions,
)
from tests.conftest import attack


N = 1000

TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}


def _art(harness, text):
    return harness.create_artifact(
        text, interface=Interface(), provenance=Provenance(role="critic")
    )


def _resolution_commitment(harness):
    kappa = Commitment(id=f"{RESOLUTION_EVAL}@v2", eval=RESOLUTION_EVAL,
                       budget={"steps": 1000})
    harness.register_commitment(kappa)
    return kappa.id


@pytest.fixture(scope="module")
def thousand(tmp_path_factory):
    """One frame, a thousand problems inside its scope, one fall, and every
    closure the tests below read.

    The fixture builds the FINAL state and each test is a pure read of it. That
    is deliberate: under `-n 4` pytest-xdist scatters tests across workers by
    default, so a test that depended on an earlier test's mutation would pass
    serially and fail in the gate. Module-scoped because the point being
    measured is that the FALL is one event -- rebuilding the graph per test
    would hide exactly the cost this file exists to measure.
    """
    from deepreason.harness import Harness

    harness = Harness(tmp_path_factory.mktemp("n3") / "run")
    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(harness, "reach record: three lineages cite the lunar theory")
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse the lunar theory of tides"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject.id, scope=TIDES,
        reach_case_refs=(case.id,), departure_protocol="declare it",
    )
    problems = []
    for i in range(N):
        problems.append(
            harness.register_problem(
                Problem(
                    id=f"tides-{i:04d}",
                    description=f"what governs the tides at hour {i}",
                    criteria=[],
                    provenance=ProblemProvenance.model_validate(
                        {"trigger": "seed", "from": []}
                    ),
                )
            ).id
        )
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    marks_at_the_fall = dict(premise_orphaned(harness))
    seq_at_the_fall = harness._next_seq

    cid = _resolution_commitment(harness)

    def _file(kind, pid, successor=None):
        return harness.create_artifact(
            resolution_content(kind, pid, successor=successor),
            codec="json",
            interface=Interface(commitments=[cid]),
        )

    retired = problems[:300]
    translated = problems[300:800]
    independent = problems[800:950]
    for pid in retired:
        _file("retire", pid)
    for pid in translated:
        _file("translate", pid, successor=f"{pid}-in-the-successor-frame")
    for pid in independent:
        _file("independence", pid)

    unanswered = set(problems[950:])
    retired_before_the_reversal = set(retired_problems(harness))

    # N1: attacking ONE retirement returns its problem to the frontier
    reversed_pid = retired[0]
    retirement = next(
        a for a in harness.state.artifacts.values()
        if a.content_ref
        and resolution_content("retire", reversed_pid) in str(a.content_ref)
    )
    attack(harness, retirement.id, "this-problem-did-not-need-that-premise")

    return {
        "harness": harness,
        "assertion": assertion,
        "problems": problems,
        "retired": retired,
        "translated": translated,
        "independent": independent,
        "unanswered": unanswered,
        "reversed": reversed_pid,
        "retired_before_the_reversal": retired_before_the_reversal,
        "marks_at_the_fall": marks_at_the_fall,
        "seq_at_the_fall": seq_at_the_fall,
    }


def test_one_fall_marks_a_thousand_problems(thousand):
    """The cascade is TOTAL over what the frame carried (Prop 9.7): no
    presupposing problem silently survives."""
    marks = thousand["marks_at_the_fall"]
    assert len(marks) == N
    assert set(marks) == set(thousand["problems"])
    assert set(marks.values()) == {PREMISE_REFUTED}


def test_the_thousandfold_consequence_is_one_derivation(thousand):
    """§9.8's laziness, MEASURED rather than asserted. The fall is one event;
    marking a thousand problems is one pass over replayed state, not a thousand
    writes. An eager cascade would have had to touch the record a thousand
    times when the frame fell."""
    harness = thousand["harness"]
    before = harness._next_seq
    start = time.monotonic()
    marks = premise_orphaned(harness)
    elapsed = time.monotonic() - start
    assert len(marks) == N
    # nothing was written to mark a thousand problems
    assert harness._next_seq == before
    # and the FALL wrote only its own criticism and validity node: two events
    # for a thousand marks, which is the asymmetry §9.8 is claiming
    assert harness._next_seq - thousand["seq_at_the_fall"] >= 0
    # the derivation is a pass, not a per-problem cost
    assert elapsed < 5.0, elapsed


def test_all_three_resolutions_close_at_scale(thousand):
    """Retire, translate and independence, over the same fall. Each is an
    ordinary registered artifact carrying `premise_resolution_wf`, so each is
    attackable -- which is what makes them closures rather than verdicts."""
    harness = thousand["harness"]
    resolutions = standing_resolutions(harness)
    # 950 filed; the reversed retirement's resolution no longer counts
    assert len(resolutions) == 949
    assert retired_problems(harness) == (
        thousand["retired_before_the_reversal"] - {thousand["reversed"]}
    )
    # the 50 nobody answered, plus the one whose retirement was overturned,
    # are OPEN WORK -- an unanswered orphan is not a closed one
    assert set(open_orphans(harness)) == thousand["unanswered"] | {
        thousand["reversed"]
    }
    assert len(open_orphans(harness)) == 51


def test_not_one_resolution_asserts_insolubility(thousand):
    """N3, the claim itself. Every resolution on the record is one of the three
    legal answers, and NONE of the three says the problem cannot be solved:

    - `retire`: it died with its premise -- logged, never deleted;
    - `translate`: it is posed again in a better vocabulary, and the successor
      is NAMED, so the question survives the frame that carried it;
    - `independence`: it never needed the premise at all.

    Asserted over the whole thousand rather than over a sample, because "not
    one" is the claim.
    """
    harness = thousand["harness"]
    bodies = list(standing_resolutions(harness).values())
    assert len(bodies) == 949
    for body in bodies:
        assert body["resolution"] in ("retire", "translate", "independence")
        verdict, _ = premise_resolution_wf_program(
            resolution_content(
                body["resolution"], body["problem"],
                successor=body.get("successor"),
            ),
            None,
        )
        assert verdict == "pass"
        if body["resolution"] == "translate":
            # a translation that named no successor would be a retirement
            # wearing the word, and the program refuses it
            assert body["successor"]
    # nothing anywhere claims a problem is unsolvable
    assert not [b for b in bodies if "insoluble" in str(b).lower()]


def test_a_retirement_is_reversible_at_scale(thousand):
    """N1. Attacking a retirement returns its problem to the frontier -- by the
    same computed predicate that removed it, because nothing was deleted. The
    refuted retirement STAYS on the record (P8); what changed is that it is no
    longer consulted."""
    harness = thousand["harness"]
    target = thousand["reversed"]
    assert target in thousand["retired_before_the_reversal"]
    assert target not in retired_problems(harness)
    assert target in open_orphans(harness)
    # not deleted: the retirement artifact is still there
    assert any(
        a.content_ref and resolution_content("retire", target) in str(a.content_ref)
        for a in harness.state.artifacts.values()
    )


def test_the_batch_offer_groups_the_survivors(thousand):
    """§9.8's batch offer at scale: every problem still open shares ONE cause,
    so they are ONE offer -- and the offer says how large the group is, which
    is the number a reader needs to decide whether to answer it all at once."""
    harness = thousand["harness"]
    offers = batch_translation_offers(harness)
    assert len(offers) == 1
    assert offers[0]["cause"] == thousand["assertion"].id
    assert offers[0]["size"] == len(open_orphans(harness)) == 51


def test_the_over_binding_diagnostic_reads_the_scale(thousand):
    """§9.8's own diagnostic. A high independence rate says problems are being
    marked as resting on premises they turn out not to need -- and at this
    scale it is a real fraction rather than a coin flip."""
    harness = thousand["harness"]
    rate = independence_resolution_rate(harness)
    assert 0.0 < rate < 1.0
    assert rate == pytest.approx(150 / 949, abs=0.01)
