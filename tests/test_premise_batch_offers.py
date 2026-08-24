"""§9.8's batch translation offers -- groups of orphans, materialized together.

Implements R3 (v2 calculus program, Rung 7). "The fall is one event; its
thousandfold consequence is paid as the frontier is touched, not all at once."
One translation into a better vocabulary answers for a whole GROUP, because the
group shares a cause -- so the offer is a grouping by what fell, and a group
with two causes would be two translations wearing one name.

ATTENTION ONLY, and that is what most of this file exists to pin. An offer
registers nothing, spawns nothing, retires nothing and moves no label; a critic
who ignores every offer pays nothing. The three resolutions stay ordinary
adjudicated closures authored one at a time.
"""

import ast
import inspect
import pathlib

from deepreason.calculus import operations
from deepreason.ontology import Interface, Problem, ProblemProvenance, Provenance
from deepreason.premises import (
    PREMISE_REFUTED,
    PREMISE_UNACCREDITED,
    batch_translation_offers,
    file_premise,
    open_orphans,
    orphan_causes,
    premise_orphaned,
    resolution_content,
    RESOLUTION_EVAL,
)
from tests.conftest import attack


TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}


def _art(harness, text):
    return harness.create_artifact(
        text, interface=Interface(), provenance=Provenance(role="critic")
    )


def _problem(harness, pid, description):
    return harness.register_problem(
        Problem(
            id=pid, description=description, criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    ).id


def _frame(harness):
    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(harness, "reach record: three lineages cite the lunar theory")
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse the lunar theory of tides"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject.id, scope=TIDES,
        reach_case_refs=(case.id,), departure_protocol="declare it",
    )
    return subject, case, assertion


def _resolution(harness, kind, problem_id, *, successor=None):
    from deepreason.ontology import Commitment

    kappa = Commitment(id=f"{RESOLUTION_EVAL}@v2", eval=RESOLUTION_EVAL,
                       budget={"steps": 1000})
    harness.register_commitment(kappa)
    return harness.create_artifact(
        resolution_content(kind, problem_id, successor=successor),
        codec="json",
        interface=Interface(commitments=[kappa.id]),
    )


# --- the grouping ------------------------------------------------------------


def test_one_fall_offers_one_group(harness):
    """The shape §9.8 asks for: a fall over many problems is ONE offer, not
    many, because one translation would answer for all of them."""
    _, _, assertion = _frame(harness)
    ids = [_problem(harness, f"tides-{i}", f"what governs the tides at hour {i}")
           for i in range(5)]
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    offers = batch_translation_offers(harness)
    assert len(offers) == 1
    assert offers[0]["cause"] == assertion.id
    assert offers[0]["grade"] == PREMISE_REFUTED
    assert offers[0]["problems"] == sorted(ids)
    assert offers[0]["size"] == 5


def test_two_causes_are_two_offers(harness):
    """A group with two causes would be two translations wearing one name."""
    _, _, assertion = _frame(harness)
    framed = _problem(harness, "tides-0", "what governs the tides at dawn")
    other = _problem(harness, "winds-0", "what governs the trade winds")
    premise, _ = file_premise(harness, other, "X: the trade winds are steady")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")
    attack(harness, premise.id, "the-trade-winds-reverse-in-the-monsoon")

    offers = batch_translation_offers(harness)
    assert len(offers) == 2
    assert {o["cause"] for o in offers} == {assertion.id, premise.id}
    assert {tuple(o["problems"]) for o in offers} == {(framed,), (other,)}
    # sorted by cause id, so two readers of one root see one order
    assert [o["cause"] for o in offers] == sorted([assertion.id, premise.id])


def test_a_revocation_group_carries_the_weaker_grade(harness):
    """The offer inherits the grade rather than inventing one: an unaccredited
    group and a refuted group are different offers to the same reader."""
    _, case, _ = _frame(harness)
    _problem(harness, "tides-0", "what governs the tides at dawn")
    attack(harness, case.id, "the-reach-record-double-counts-one-lineage")

    offers = batch_translation_offers(harness)
    assert [o["grade"] for o in offers] == [PREMISE_UNACCREDITED]


def test_a_resolved_orphan_leaves_its_group(harness):
    """Offers are over OPEN orphans. A problem whose resolution is consulted is
    not outstanding work, so it is not on offer -- and the group shrinks by
    exactly one rather than the offer disappearing."""
    _, _, assertion = _frame(harness)
    ids = [_problem(harness, f"tides-{i}", f"what governs the tides at hour {i}")
           for i in range(3)]
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")
    assert batch_translation_offers(harness)[0]["size"] == 3

    _resolution(harness, "retire", ids[0])
    offers = batch_translation_offers(harness)
    assert offers[0]["size"] == 2
    assert ids[0] not in offers[0]["problems"]


def test_no_orphans_offers_nothing(harness):
    """An empty offer list is empty, never a group of size zero -- a reader
    counting groups must not find one that names no problems."""
    _frame(harness)
    _problem(harness, "tides-0", "what governs the tides at dawn")
    assert batch_translation_offers(harness) == ()


def test_the_cause_agrees_with_the_mark(harness):
    """`orphan_causes` and `premise_orphaned` are two readings of one record,
    and they must not disagree about a grade. A problem reached by a fall and a
    revocation is explained by the FALL, because that is the mark it carries."""
    _, case, assertion = _frame(harness)
    problem = _problem(harness, "tides-0", "what governs the tides at dawn")
    premise, _ = file_premise(harness, problem, "X: the tides are lunar")
    attack(harness, case.id, "the-reach-record-double-counts-one-lineage")
    attack(harness, premise.id, "the-tides-are-not-purely-lunar")

    marks = premise_orphaned(harness)
    causes = orphan_causes(harness)
    assert set(marks) == set(causes)
    assert all(causes[pid][1] == grade for pid, grade in marks.items())
    assert causes[problem] == (premise.id, PREMISE_REFUTED)


# --- attention only ----------------------------------------------------------


def test_offering_registers_nothing_and_moves_no_label(harness):
    """C5 and A9. Computing the offers leaves the record byte-identical: no
    artifact, no event, no label. An offer that wrote would be a resolution
    nobody adjudicated."""
    _, _, assertion = _frame(harness)
    _problem(harness, "tides-0", "what governs the tides at dawn")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    before = (
        dict(harness.state.status),
        set(harness.state.artifacts),
        harness._next_seq,
        sorted(harness.state.problems),
    )
    offers = batch_translation_offers(harness)
    assert offers
    assert (
        dict(harness.state.status),
        set(harness.state.artifacts),
        harness._next_seq,
        sorted(harness.state.problems),
    ) == before


def test_the_offer_function_holds_no_call_that_could_write(harness):
    """Structural, because the behavioural test above can only prove it for the
    graphs it built. Neither function reaches a mutator."""
    for fn in (batch_translation_offers, orphan_causes):
        tree = ast.parse(inspect.getsource(fn))
        calls = [ast.unparse(n.func) for n in ast.walk(tree)
                 if isinstance(n, ast.Call)]
        assert not [
            c for c in calls
            if c.split(".")[-1].startswith(
                ("create_", "register_", "record_", "commit_", "append_")
            )
        ], (fn.__name__, calls)


def test_declining_every_offer_costs_nothing(harness):
    """C5's own words. Nothing ranks, admits, or accepts on whether an offer
    was taken up: the offer is not readable from any problem's record, and the
    marks are exactly what they were before it was computed."""
    _, _, assertion = _frame(harness)
    ids = [_problem(harness, f"tides-{i}", f"what governs the tides at hour {i}")
           for i in range(3)]
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    before = dict(premise_orphaned(harness))
    for _ in range(3):
        batch_translation_offers(harness)
    assert premise_orphaned(harness) == before
    assert set(open_orphans(harness)) == set(ids)


# --- the receipt -------------------------------------------------------------


def test_the_signal_is_declared_through_the_typed_channel():
    """`DR-INV-signal-contract` clause (1): a new signal enters by DECLARATION
    -- name, unit, producer-agnostic semantics and a staleness bound -- never
    by teaching a consumer about a subsystem."""
    from deepreason.signals import declaration

    d = declaration("premise.batch-translation-offered.v1")
    assert d is not None
    assert d.unit == "count" and d.staleness == "cycle"
    assert "attention only" in d.semantics.lower()


def test_the_scheduler_emits_the_receipt_every_cycle():
    """The anti-E28 receipt. A mechanism nobody triggers is a mechanism that
    never runs, and this tree has shipped two of those -- so the offer is on
    the record whether or not anyone acts on it."""
    from deepreason.scheduler.scheduler import Scheduler

    src = inspect.getsource(Scheduler._record_detection_signals)
    assert "premise.batch-translation-offered.v1" in src
    assert "batch_translation_offers(harness)" in src
