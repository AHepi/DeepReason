"""Frame render semantics and the departure protocol (v2 calculus, Rung 6).

The claims these tests exist to make falsifiable, in the order the tranche's
REQUEST.md numbers them:

- R1  the pack for a problem in scope carries the frame's articulation digest
      AND the subject's standing attackers -- "the frame ships its own crisis";
- R2/R3 the slice carries the departure directive, and a DECLARED departure
      removes the hidden-premise criticism's target deterministically, while
      the declaration stays an ordinary attackable artifact;
- R4  (L-4) nothing scores a departure -- asserted as an ABSENCE, both
      behaviourally and structurally;
- R5  scope predicates cannot read a departure declaration;
- R7  all three exit grades are reachable and the render distinguishes them;
- G2  (Prop 12.5, render layer) rendering the slice moves no label;
- G4  (C1) the slice is byte-identical across renders;
- G5  (N1) no pack emits an empty provenance-shaped slot;
- G6  (N2) an attacker present at cycle k still renders at the TERMINAL cycle.
"""

import json

import pytest

from deepreason.calculus import operations
from deepreason.calculus.render import (
    EXIT_GRADES,
    FRAME_SLICE_ATTACKERS_N,
    articulation_digest,
    declared_departures,
    exit_grade,
    frame_exits,
    frame_slices,
    held_frame_obligations,
    render_frame_slice_context,
)
from deepreason.harness import Harness
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
)
from deepreason.ontology.artifact import RefRole
from tests.conftest import attack

SCOPE = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}
SUBJECT_COMMITMENT = Commitment(id="k:tides-are-lunar-only", eval="prose")
SUBJECT_TEXT = (
    "b: the lunar theory of tides -- the tide is the moon's differential "
    "pull, and the sun contributes nothing that matters at the scale of a "
    "harbour timetable."
)


def _art(harness, text, *, interface=None, role="import"):
    return harness.create_artifact(
        text,
        interface=interface if interface is not None else Interface(refs=[]),
        provenance=Provenance(role=role),
    )


def _problem(harness, pid, description):
    return harness.register_problem(
        Problem(
            id=pid, description=description, criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _framed(harness):
    """A consulted frame over a subject that carries one commitment.

    The subject carries a commitment because a departure names commitment
    IDS: a subject with an empty interface would make the departure protocol
    untestable while every assertion about it still passed.
    """
    harness.register_commitment(SUBJECT_COMMITMENT)
    subject = _art(
        harness, SUBJECT_TEXT,
        interface=Interface(commitments=[SUBJECT_COMMITMENT.id], refs=[]),
    )
    case = _art(harness, "reach record: three lineages cite this subject")
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "should the lunar theory frame this scope"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject.id, scope=SCOPE,
        reach_case_refs=(case.id,),
        departure_protocol="name the broken commitment ids in a declaration",
    )
    return subject, case, promotion, assertion


# --- R1: the slice, and what it carries --------------------------------------

def test_a_consulted_frame_renders_its_digest_and_its_standing_attackers(harness):
    """R1. Both halves, in one pack: the articulation the frame asserts, and
    the open indictments against it. A slice with only the first would be a
    frame presented as settled, which is the state §9.5 exists to refuse."""
    subject, _, _, assertion = _framed(harness)
    critic, _ = attack(
        harness, subject.id, "mispredicts-the-neap-tide-by-forty-minutes"
    )
    problem = _problem(harness, "p-tides", "predict the spring tides here")

    text = render_frame_slice_context(harness, "p-tides")
    assert text is not None
    assert subject.id in text
    assert "the moon's differential" in text          # the digest
    assert SUBJECT_COMMITMENT.id in text              # the departure surface
    assert critic.id in text                          # the crisis, in frame
    assert "STANDING ATTACKERS" in text
    assert problem.id == "p-tides"


def test_a_problem_outside_the_scope_carries_no_frame_slice(harness):
    """R1's other half. sigma decides, and a scope that admits everything
    would make every assertion above pass for the wrong reason."""
    _framed(harness)
    _problem(harness, "p-orbits", "predict the orbit of a comet")
    assert render_frame_slice_context(harness, "p-orbits") is None
    assert frame_slices(harness, "p-orbits") == ()


def test_the_standing_attacker_cap_states_itself(harness):
    """G7, in the render. A count shown without its total is a silent cap,
    and a reader cannot then tell a quiet frame from a truncated one."""
    subject, _, _, _ = _framed(harness)
    for index in range(FRAME_SLICE_ATTACKERS_N + 2):
        attack(harness, subject.id, f"independent-fault-{index}")
    _problem(harness, "p-tides", "predict the spring tides here")

    text = render_frame_slice_context(harness, "p-tides")
    assert f"{FRAME_SLICE_ATTACKERS_N} of {FRAME_SLICE_ATTACKERS_N + 2} shown" in text
    slice_ = frame_slices(harness, "p-tides")[0]
    assert len(slice_.attackers) == FRAME_SLICE_ATTACKERS_N
    assert slice_.attackers_total == FRAME_SLICE_ATTACKERS_N + 2


# --- R2, R3: the departure protocol ------------------------------------------

def test_the_slice_carries_the_departure_directive_and_the_protocol(harness):
    """R2. The directive is standing text in every pack in scope, and the
    assertion's own protocol string travels with it."""
    _framed(harness)
    _problem(harness, "p-tides", "predict the spring tides here")
    text = render_frame_slice_context(harness, "p-tides")
    assert "DEPARTURES ARE PERMITTED" in text
    assert "no penalty anywhere" in text
    assert "UNDECLARED conflict" in text
    assert "name the broken commitment ids in a declaration" in text


def test_declaring_a_departure_removes_the_held_obligation(harness):
    """R3, and it is the DETERMINISTIC gate rather than an instruction.

    Q1's finding is that a standing rule in context decays regardless of
    where it sits, so what the hidden-premise criticism aims at cannot be
    whatever the model says it assumed. It is the record's own subtraction:
    the subject's commitment ids minus the ids the candidate declared.
    """
    subject, _, _, _ = _framed(harness)
    problem = _problem(harness, "p-tides", "predict the spring tides here")
    silent = _art(harness, "c1: a tidal model that quietly assumes the sun away")
    departing = _art(harness, "c2: a solar-lunar composite")

    assert held_frame_obligations(harness, subject.id, silent.id) == (
        SUBJECT_COMMITMENT.id,
    )
    operations.file_departure_declaration(
        harness, problem=problem, subject_ref=subject.id,
        departing_ref=departing.id, broken_ids=[SUBJECT_COMMITMENT.id],
        rationale="the solar term is not negligible at the equinox",
    )
    assert held_frame_obligations(harness, subject.id, departing.id) == ()
    assert held_frame_obligations(harness, subject.id, silent.id) == (
        SUBJECT_COMMITMENT.id,
    )
    assert departing.id in render_frame_slice_context(harness, "p-tides")


def test_a_departure_declaration_is_itself_attackable(harness):
    """R3's second half. Nothing protects the declaration: it takes an attack
    and is refuted exactly as any artifact would be. A declaration that could
    not be attacked would let a candidate exempt itself by asserting it."""
    subject, _, _, _ = _framed(harness)
    problem = _problem(harness, "p-tides", "predict the spring tides here")
    departing = _art(harness, "c: a solar-lunar composite")
    declaration = operations.file_departure_declaration(
        harness, problem=problem, subject_ref=subject.id,
        departing_ref=departing.id, broken_ids=[SUBJECT_COMMITMENT.id],
        rationale="the solar term is not negligible at the equinox",
    )
    assert harness.state.status[declaration.id] == Status.ACCEPTED
    attack(harness, declaration.id, "the-named-commitment-is-not-the-one-broken")
    assert harness.state.status[declaration.id] == Status.REFUTED


# --- G4 / C1: determinism -----------------------------------------------------

def test_the_slice_is_byte_identical_across_renders(tmp_path):
    """G4. Two renders of one problem over one state, and two independently
    replayed harnesses over one root, agree byte for byte.

    What this pins is PURITY: a renderer that consumed an iterator, cached
    mutable state between calls, or read anything outside the replayed record
    fails it. What it does NOT pin is the attacker ORDER -- `state.att` is a
    list in log order, so an unsorted render would be deterministic too. That
    claim needs its own test, and has one below."""
    root = tmp_path / "run"
    harness = Harness(root)
    subject, _, _, _ = _framed(harness)
    for index in range(3):
        attack(harness, subject.id, f"independent-fault-{index}")
    _problem(harness, "p-tides", "predict the spring tides here")

    first = render_frame_slice_context(harness, "p-tides")
    assert first == render_frame_slice_context(harness, "p-tides")
    replayed = Harness(root, read_only=True)
    assert render_frame_slice_context(replayed, "p-tides") == first


# --- G5 / N1: omit, do not redact --------------------------------------------

# Labels that name WHO or WHAT produced a content. Judge blinding's placebo
# result is that a present-but-empty one of these draws more attention than a
# populated one, so the slice carries none of them in either state.
PROVENANCE_SHAPED = (
    "author", "provenance", "origin", "produced by", "produced-by",
    "seat:", "model:", "endpoint:", "school:", "role:", "redacted",
)


def test_the_frame_slice_emits_no_provenance_shaped_slot(harness):
    """G5 (N1). Not "no EMPTY provenance slot" -- no provenance slot at all,
    in the fully-populated case and in the everything-absent case alike. A
    slot that is only omitted when empty is a slot, and its absence is then
    itself the signal."""
    subject, _, _, _ = _framed(harness)
    _problem(harness, "p-tides", "predict the spring tides here")

    bare = render_frame_slice_context(harness, "p-tides")
    assert bare is not None
    attack(harness, subject.id, "mispredicts-the-neap-tide")
    departing = _art(harness, "c: a solar-lunar composite")
    operations.file_departure_declaration(
        harness, problem=harness.state.problems["p-tides"],
        subject_ref=subject.id, departing_ref=departing.id,
        broken_ids=[SUBJECT_COMMITMENT.id], rationale="the solar term matters",
    )
    full = render_frame_slice_context(harness, "p-tides")

    for text in (bare, full):
        lowered = text.lower()
        for label in PROVENANCE_SHAPED:
            assert label not in lowered, (label, text)
    # And the empty parts are ABSENT rather than blanked.
    assert "STANDING ATTACKERS" not in bare
    assert "ALREADY DECLARED" not in bare
    assert "(none)" not in full and "—\n" not in full


def test_an_absent_frame_renders_nothing_rather_than_a_no_frame_notice(harness):
    """G5's sharpest case. A "no frame is consulted here" line would be the
    empty slot itself: every unframed pack would carry a header inviting the
    model to wonder what was withheld."""
    _problem(harness, "p-plain", "an ordinary problem with no frame at all")
    assert render_frame_slice_context(harness, "p-plain") is None


def test_attackers_render_in_id_order_whatever_order_the_state_holds(harness):
    """The ordering claim, against a SHUFFLED `att`, because the obvious test
    is vacuous.

    `Harness._adjudicate` already does `self.state.att = sorted(att)`, so a
    test that registers three attacks and checks the render is sorted passes
    with the sort in `subject_attackers` deleted -- it measures the harness,
    not this module. That first version was written and thrown away; this one
    hands the renderer a state whose `att` is in the opposite order and
    fails if the module leans on someone else's sortedness.

    Why the property is worth a test at all: under the cap, arrival order
    would let an early criticism hold a slot against every later one, and
    arrival order is origin information that appraisal may not read (Ax 4.1).
    """
    subject, _, _, _ = _framed(harness)
    _problem(harness, "p-tides", "predict the spring tides here")
    made = [attack(harness, subject.id, f"fault-{i}")[0].id for i in range(3)]

    harness.state.att = list(reversed(harness.state.att))
    assert [a for a, _ in harness.state.att if _ == subject.id] != sorted(made)

    slice_ = frame_slices(harness, "p-tides")[0]
    assert [attacker for attacker, _, _ in slice_.attackers] == sorted(made)
