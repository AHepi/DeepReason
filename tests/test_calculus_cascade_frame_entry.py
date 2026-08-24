"""The cascade's SECOND entry condition: a fallen frame marks what it framed.

Implements R2, G2 and G3 (v2 calculus program, Rung 7). Prop 9.7 is complete
only with both entries in it, and the claim these tests exist to make
falsifiable is that there is exactly ONE marking function -- the entries
differ in what they READ and not in what they DO. A second marking mechanism
would be invisible to a behavioural test that only checked that marks appear,
so the absence is asserted structurally as well.

§9.7's two grades are distinguished by the TWO-PASS LABELS and by nothing
else: `refuted` (pass one) is a fall, `suspended_unsupported` (pass two) is a
revocation, and `suspended` is neither because nobody has won. No grade is
stored anywhere -- if one ever were, the record could disagree with the labels
that imply it.
"""

import ast
import inspect
import pathlib

from deepreason.calculus import operations
from deepreason.calculus.standing import (
    consulted,
    fallen_frames,
    framed_problem_ids,
    unseparated_fallen_frames,
)
from deepreason.ontology import Interface, Provenance, Ref, Status
from deepreason.ontology.artifact import RefRole
from deepreason.premises import (
    PREMISE_REFUTED,
    PREMISE_UNACCREDITED,
    open_orphans,
    premise_orphaned,
)
from tests.conftest import attack


TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}


def _art(harness, text, refs=(), role="critic"):
    return harness.create_artifact(
        text,
        interface=Interface(refs=list(refs)),
        provenance=Provenance(role=role),
    )


def _framed_problem(harness, description):
    """An ordinary seed problem inside the frame's scope."""
    from deepreason.ontology import Problem, ProblemProvenance

    return harness.register_problem(
        Problem(
            id=description.replace(" ", "-"),
            description=description,
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    ).id


def _unresolved_attack_on(harness, target_id: str):
    """Attack `target_id` with a critic locked in an unresolved CYCLE.

    Imported in shape from `tests/test_frame_render.py`, where the same
    construction pins the third exit grade. Warrants attach only at artifact
    registration, so the cycle is closed by letting the first critic name a
    target that does not exist yet.
    """
    from deepreason.ontology import Artifact, Warrant, WarrantType

    nu_a = _art(harness, "nu: the overreach case is sound")
    nu_b = _art(harness, "nu: the rebuttal is sound")
    against_rebuttal = Warrant(
        id="w-overreach-vs-rebuttal", target="CRITIC-REBUTTAL",
        type=WarrantType.ARGUMENTATIVE, validity_node=nu_a.id,
    )
    against_target = Warrant(
        id="w-overreach-vs-frame", target=target_id,
        type=WarrantType.ARGUMENTATIVE, validity_node=nu_a.id,
    )
    harness.register_artifact(
        Artifact(
            id="CRITIC-OVERREACH",
            content_ref="inline:critic: this frame overreaches its scope",
            warrants=[against_rebuttal.id, against_target.id],
            provenance=Provenance(role="critic"),
        ),
        warrants=[against_rebuttal, against_target],
    )
    against_overreach = Warrant(
        id="w-rebuttal-vs-overreach", target="CRITIC-OVERREACH",
        type=WarrantType.ARGUMENTATIVE, validity_node=nu_b.id,
    )
    harness.register_artifact(
        Artifact(
            id="CRITIC-REBUTTAL",
            content_ref="inline:critic: the overreach case misreads the scope",
            warrants=[against_overreach.id],
            provenance=Provenance(role="critic"),
        ),
        warrants=[against_overreach],
    )


def _frame(harness, *, scope=None):
    """A consulted frame assertion over the tides scope.

    The reach case is a SEPARATE artifact from the subject, which is what keeps
    Comp(f) and Comp(b) disjoint -- a case that depended on the subject would
    make the assertion unconsultable before anything fell (Rung 3b).
    """
    subject = _art(harness, "b: the lunar theory of tides")
    case = _art(harness, "reach record: three lineages cite the lunar theory")
    problem = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse the lunar theory of tides"
    )
    assertion = operations.file_frame_assertion(
        harness,
        problem=problem,
        subject_ref=subject.id,
        scope=scope if scope is not None else TIDES,
        reach_case_refs=(case.id,),
        departure_protocol="declare the departure in the pack and cite this id",
    )
    return subject, case, problem, assertion


# --- what a fallen frame IS --------------------------------------------------


def test_a_consulted_frame_is_not_a_fallen_one(harness):
    """The precondition. While the assertion is unrefuted it frames, and the
    cascade's second entry is empty -- otherwise every consulted frame would
    orphan its own scope from the moment it was filed."""
    _, _, _, assertion = _frame(harness)
    _framed_problem(harness, "what governs the tides")
    assert [g.assertion_id for g in consulted(harness)] == [assertion.id]
    assert fallen_frames(harness) == ()
    assert premise_orphaned(harness) == {}


def test_a_fall_marks_every_problem_the_frame_carried(harness):
    """§9.7 fall-grade. A warranted attack on the ASSERTION refutes it; every
    problem sigma admits is marked `premise refuted`."""
    _, _, _, assertion = _frame(harness)
    inside = _framed_problem(harness, "what governs the tides")
    outside = _framed_problem(harness, "what governs the seasons")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    assert harness.state.status[assertion.id] is Status.REFUTED
    fallen = fallen_frames(harness)
    assert [f.grade for f in fallen] == ["fall"]
    marks = premise_orphaned(harness)
    assert marks == {inside: PREMISE_REFUTED}
    assert outside not in marks


def test_a_revocation_marks_with_the_weaker_grade(harness):
    """§9.7 revocation-grade. Refuting the REACH CASE cuts the assertion's
    support; pass two makes it `suspended_unsupported` and the mark says
    `premise unaccredited` -- unearned, not wrong."""
    _, case, _, assertion = _frame(harness)
    inside = _framed_problem(harness, "what governs the tides")
    attack(harness, case.id, "the-reach-record-double-counts-one-lineage")

    assert harness.state.status[assertion.id] is Status.SUSPENDED_UNSUPPORTED
    assert [f.grade for f in fallen_frames(harness)] == ["revocation"]
    assert premise_orphaned(harness) == {inside: PREMISE_UNACCREDITED}


def test_contestation_marks_nothing(harness):
    """The grade §9.7's table does NOT name. An unresolved attack is nobody's
    win, so the frame has not left standing and its scope is not orphaned.

    The cycle is what makes the label `suspended` rather than `refuted`: an
    attacker attacked by an unattacked critic is simply refuted, and the frame
    would be reinstated.
    """
    _, _, _, assertion = _frame(harness)
    inside = _framed_problem(harness, "what governs the tides")
    # Rung 6's own construction, reused rather than rebuilt: two critics
    # attacking each other leave the attacker on the assertion neither
    # accepted nor defeated. A CHAIN would reinstate the first critic under
    # grounded semantics and produce `refuted`, which is not this case.
    _unresolved_attack_on(harness, assertion.id)

    assert harness.state.status[assertion.id] is Status.SUSPENDED
    assert fallen_frames(harness) == ()
    assert inside not in premise_orphaned(harness)


def test_an_unseparated_fallen_assertion_marks_nothing(harness):
    """R64 at the frame entry, and A6 preserved. An assertion sharing an
    adjudication component with its subject is UNCONSULTABLE: it never framed
    anything, so it has no standing to lose and orphans nothing.

    It is still ENUMERATED, because components only ever grow and a reader of a
    finished run needs telling that the record holds one.
    """
    subject = _art(harness, "b: the lunar theory of tides")
    # the reach case DEPENDS on the subject -- Comp(f) and Comp(b) merge
    case = _art(
        harness,
        "reach record: derived from the lunar theory itself",
        refs=[Ref(target=subject.id, role=RefRole.DEPENDENCE)],
    )
    problem = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse the lunar theory of tides"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=problem, subject_ref=subject.id, scope=TIDES,
        reach_case_refs=(case.id,),
        departure_protocol="declare it",
    )
    inside = _framed_problem(harness, "what governs the tides")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    assert harness.state.status[assertion.id] is Status.REFUTED
    assert fallen_frames(harness) == ()
    assert [f.assertion_id for f in unseparated_fallen_frames(harness)] == [
        assertion.id
    ]
    assert inside not in premise_orphaned(harness)


def test_a_fallen_frame_does_not_orphan_its_own_promotion_problem(harness):
    """D-1, read back into the cascade. The promotion problem is the problem
    the assertion ANSWERS, not one posed under it -- and sigma can admit it by
    accident, because the two are about the same subject.

    D-1 was answered A: when a frame falls, "the incumbent's promotion problem
    stays on the frontier, ranked by wound count". A mark deprioritizes a
    problem in scheduling, so marking this one would push down the one problem
    the answer requires to stay up.
    """
    _, _, promotion, assertion = _frame(harness)
    inside = _framed_problem(harness, "what governs the tides")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    # sigma DOES admit it -- the exclusion is doing the work, not the scope
    assert promotion.id in framed_problem_ids(harness, TIDES)
    assert premise_orphaned(harness) == {inside: PREMISE_REFUTED}


def test_a_scope_that_no_longer_compiles_carries_nothing(harness):
    """`framed_problem_ids` answers, it does not raise. The assertion is on the
    record and cannot be edited, so a reader asking what it carries must get an
    answer -- and the refusal is visible as an empty set, never as a crash."""
    _framed_problem(harness, "what governs the tides")
    assert framed_problem_ids(harness, {"schema": "not-a-scope"}) == ()


# --- G2: ONE marking function, both entries ---------------------------------


def test_both_entries_reach_one_marking_function(harness):
    """G2. A premise fall and a frame fall mark THROUGH THE SAME FUNCTION, and
    a problem reached by both gets one mark, not two."""
    from deepreason.premises import file_premise

    _, _, _, assertion = _frame(harness)
    inside = _framed_problem(harness, "what governs the tides")
    premise, attribution = file_premise(
        harness, inside, "X: the tides are periodic in the lunar month"
    )
    attack(harness, premise.id, "the-lunar-month-premise-is-false")
    attack(harness, assertion.id, "the-lunar-frame-overreaches-its-scope")

    marks = premise_orphaned(harness)
    assert marks[inside] == PREMISE_REFUTED
    assert isinstance(marks[inside], str)   # ONE grade, not a list of them


def test_the_fall_grade_dominates_the_revocation_grade(harness):
    """A5. One problem reached by a fall and by a revocation carries the fall:
    a refuted premise is a stronger fact about the problem than an unaccredited
    one. Identical for both entries, which is what keeps it one function."""
    from deepreason.premises import file_premise

    _, case, _, assertion = _frame(harness)
    inside = _framed_problem(harness, "what governs the tides")
    premise, _ = file_premise(
        harness, inside, "X: the tides are periodic in the lunar month"
    )
    attack(harness, case.id, "the-reach-record-double-counts-one-lineage")
    attack(harness, premise.id, "the-lunar-month-premise-is-false")

    assert harness.state.status[assertion.id] is Status.SUSPENDED_UNSUPPORTED
    assert premise_orphaned(harness)[inside] == PREMISE_REFUTED


def test_there_is_no_second_marking_mechanism(harness):
    """G2's ABSENCE, asserted structurally because no behavioural test can see
    it. Exactly one function in `src/` NAMES a cascade grade constant, so a
    second grading rule cannot exist without appearing here -- every consumer
    of the marks reads that function's output rather than deriving its own.

    `orphan_causes` is the near miss worth naming: it needs to know which cause
    explains a mark, and an earlier draft compared grade strings to decide it.
    It now expresses precedence on the LABEL and reads the grade from the mark,
    so it cannot disagree with the function that assigned it.
    """
    src = pathlib.Path("src/deepreason")
    assigning = []
    for path in sorted(src.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            body = ast.unparse(node)
            if "PREMISE_REFUTED" in body or "PREMISE_UNACCREDITED" in body:
                assigning.append(f"{path.name}::{node.name}")
    assert assigning == ["premises.py::premise_orphaned"], assigning


def test_the_frame_entry_is_read_not_reimplemented(harness):
    """The entry READS `fallen_frames`; it does not re-derive which frames
    fell. Two readings of "a frame that fell" would leave no way to tell which
    one the record meant -- the same reason `consultability_of` calls Rung 3b's
    predicate rather than re-deriving the graph condition."""
    from deepreason.premises import _fallen_frame_entries

    entry = inspect.getsource(_fallen_frame_entries)
    assert "fallen_frames" in entry and "framed_problem_ids" in entry
    marking = inspect.getsource(premise_orphaned)
    assert "_fallen_frame_entries" in marking
    # ONE grading step, shared by both entries: the grade is decided here,
    # from the label, and is not recomputed by either entry.
    assert "Status.REFUTED" in marking
    assert "Status.REFUTED" not in entry
    assert "EXIT_GRADES" not in marking and "EXIT_GRADES" not in entry


# --- G3: the two grades, from the two-pass labels, with no new machinery -----


def test_no_grade_is_stored_anywhere(harness):
    """G3. The grade is a pure function of the label. No field was added to
    `Problem`, `EpistemicState` or `Event`, so no stored grade can disagree
    with the labels that imply it."""
    from deepreason.ontology import Event, Problem
    from deepreason.ontology.state import EpistemicState

    for model in (Problem, Event, EpistemicState):
        fields = set(getattr(model, "model_fields", {}))
        assert not {f for f in fields if "orphan" in f or "grade" in f}, model


def test_the_two_grades_come_from_the_two_pass_labels(harness):
    """G3, positively. The grade a fallen frame carries is decided by its
    label and by nothing else -- the same two labels the premise entry reads,
    which is why §9.7 needs no new machinery to tell fall from revocation."""
    from deepreason.calculus.standing import _MARKING_GRADES

    assert _MARKING_GRADES == {
        Status.REFUTED: "fall",
        Status.SUSPENDED_UNSUPPORTED: "revocation",
    }
    assert Status.SUSPENDED not in _MARKING_GRADES
    assert Status.ACCEPTED not in _MARKING_GRADES


def test_the_mark_is_reversible_by_the_same_computed_predicate(harness):
    """N1 at the frame entry. Defeating the frame's critic reinstates the
    assertion and UN-marks its problems -- by the same computed predicate that
    marked them, because nothing was written down to undo."""
    _, _, _, assertion = _frame(harness)
    inside = _framed_problem(harness, "what governs the tides")
    critic, _ = attack(harness, assertion.id, "the-lunar-frame-overreaches")
    assert premise_orphaned(harness) == {inside: PREMISE_REFUTED}

    attack(harness, critic.id, "the-overreach-charge-misreads-the-scope")
    assert harness.state.status[assertion.id] is Status.ACCEPTED
    assert premise_orphaned(harness) == {}
    assert open_orphans(harness) == {}
