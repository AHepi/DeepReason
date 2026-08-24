"""Prop 9.6 -- wound persistence, end to end.

Implements R1 and G1 (v2 calculus program, Rung 7). NOTHING NEW IS BUILT for
wounds, and that is the requirement rather than a shortcut: a fail verdict on
the subject's own observation-valued commitment already yields a demonstrative
warrant, an attack edge and a refuted status. What this rung owes is the PROOF
that standing is untouched by it.

    Proposition 9.6 (Wound persistence). A wound changes status(b) and does not
    change standing(b). Proof: the attack targets b; fa carries no dependence on
    b (Law 9.4), so Pass 2 leaves fa's label untouched; the renderer keys on
    final(fa).

Newton between 1859 and 1915 is the intended model of the state these tests
describe: status-refuted, standing-background, the perihelion on display in
every pack, succession wanted. The test that would MISS a violation is one that
checks only the label -- so every layer the wound could have reached is checked:
the label, the grant, the render, and the cascade.
"""

import ast
import pathlib

from deepreason.calculus import operations
from deepreason.calculus.render import (
    render_frame_crisis_context,
    render_frame_slice_context,
)
from deepreason.calculus.standing import (
    consulted,
    fallen_frames,
    frames,
    standing_of,
    standing_view,
)
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Ref,
    Status,
)
from deepreason.ontology.artifact import RefRole
from deepreason.premises import premise_orphaned
from deepreason.rules.warrants import register_fail_warrant
from tests.conftest import attack


TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}

# The subject's OWN observation-valued commitment -- what makes a failure a
# WOUND rather than an ordinary criticism. It is what the subject exposed
# itself to evidence with, so a fail verdict on it is the record's own
# statement of where the incumbent was hurt.
PERIHELION = Commitment(
    id="observation:tidal-lag@v1",
    eval="program:json_wf",
    observation_valued=True,
)


def _art(harness, text, refs=(), commitments=()):
    return harness.create_artifact(
        text,
        interface=Interface(commitments=list(commitments), refs=list(refs)),
        provenance=Provenance(role="critic"),
    )


def _framed(harness):
    """A consulted frame over the tides scope, its subject carrying an
    observation-valued commitment it can be wounded on."""
    harness.register_commitment(PERIHELION)
    subject = _art(
        harness, "b: the lunar theory of tides", commitments=[PERIHELION.id]
    )
    case = _art(harness, "reach record: three lineages cite the lunar theory")
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse the lunar theory of tides"
    )
    assertion = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=subject.id, scope=TIDES,
        reach_case_refs=(case.id,),
        departure_protocol="declare which of its commitments you break with",
    )
    problem = harness.register_problem(
        Problem(
            id="what-governs-the-tides",
            description="what governs the tides at the equinox",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    return subject, case, promotion, assertion, problem


def _wound(harness, subject_id):
    """A fail verdict on the subject's own observation-valued commitment.

    Registered through `rules/warrants.register_fail_warrant` -- the tree's ONE
    warrant constructor -- so this is the ordinary path a live run takes, not a
    test-only shortcut. Nothing in this function knows what a frame is.
    """
    return register_fail_warrant(
        harness,
        commitment_id=PERIHELION.id,
        target_id=subject_id,
        nu_content=(
            "nu: the tidal-lag measurement is sound and relevant -- the "
            "observed lag at the equinox is 42 minutes and the theory "
            "requires 0"
        ),
        critic_content=(
            "critic: the lunar theory mispredicts the equinoctial tidal lag"
        ),
        trace_ref=harness.blobs.put(b'{"verdict": "fail", "observed": 42}'),
    )


# --- G1: the proposition, through the whole path -----------------------------


def test_a_wound_changes_status_and_leaves_standing_untouched(harness):
    """Prop 9.6 END TO END. Every layer a wound could have reached is compared
    across the wound, not only the label:

    1. `status(b)` MOVES -- the wound did land, or the test proves nothing;
    2. the assertion's own label is untouched (Pass 2 never reaches it);
    3. `standing(b)` is byte-identical -- the same grant, same scope, same
       validity, same protocol;
    4. the frame still frames the problem, and still RENDERS;
    5. the cascade does NOT fire -- a wound is not a fall.
    """
    subject, _, _, assertion, problem = _framed(harness)

    before_status = harness.state.status[subject.id]
    before_grants = standing_of(harness, subject.id)
    before_view = standing_view(harness)
    before_slice = render_frame_slice_context(harness, problem.id)
    assert before_status is Status.ACCEPTED
    assert len(before_grants) == 1
    assert before_slice is not None

    _wound(harness, subject.id)

    # 1. the wound landed
    assert harness.state.status[subject.id] is Status.REFUTED
    # 2. the assertion is untouched: it MENTIONS b and depends on nothing of it
    assert harness.state.status[assertion.id] is Status.ACCEPTED
    # 3. standing(b) is unchanged, field for field
    assert standing_of(harness, subject.id) == before_grants
    assert standing_view(harness)["grants"] == before_view["grants"]
    assert standing_view(harness)["subjects"] == [subject.id]
    # 4. it still frames, and still renders
    assert frames(harness, subject.id, problem.id) is True
    assert render_frame_slice_context(harness, problem.id) == before_slice
    # 5. a wound is not a fall
    assert fallen_frames(harness) == ()
    assert premise_orphaned(harness) == {}


def test_the_wound_renders_in_frame_across_the_scope(harness):
    """§9.5/§9.6's intended state: refuted AND framing, with the wound on
    display. The crisis half must NAME the wound -- a frame presented without
    its crisis is the settled-frame presentation the calculus abolishes."""
    subject, _, _, _, problem = _framed(harness)
    critic = _wound(harness, subject.id)

    crisis = render_frame_crisis_context(harness, problem.id)
    assert crisis is not None
    assert critic.id in crisis
    assert "mispredicts the equinoctial tidal lag" in crisis
    assert "STANDING ATTACKERS" in crisis


def test_the_mention_law_is_what_carries_it(harness):
    """The proposition's own proof, checked rather than trusted. The assertion
    MENTIONS its subject and declares no dependence on it, so pass two has no
    path from the subject to the assertion's support."""
    subject, _, _, assertion, _ = _framed(harness)
    refs = {
        r.role.value: r.target
        for r in harness.state.artifacts[assertion.id].interface.refs
        if r.target == subject.id
    }
    assert refs == {"mention": subject.id}
    depends = {
        r.target for r in harness.state.artifacts[assertion.id].interface.refs
        if r.role.value == "dependence"
    }
    assert subject.id not in depends


def test_many_wounds_still_leave_standing_untouched(harness):
    """The quantitative form. Standing is not a budget that wounds spend down:
    three wounds move `status(b)` exactly as one does, and the grant is the
    same object afterwards. A design that degraded standing with wound count
    would pass the single-wound test and fail here."""
    subject, _, _, _, problem = _framed(harness)
    before = standing_of(harness, subject.id)
    _wound(harness, subject.id)
    attack(harness, subject.id, "the-lunar-theory-mispredicts-the-spring-tide")
    attack(harness, subject.id, "the-lunar-theory-cannot-explain-the-amphidrome")

    assert harness.state.status[subject.id] is Status.REFUTED
    assert standing_of(harness, subject.id) == before
    assert frames(harness, subject.id, problem.id) is True


def test_the_wound_is_itself_on_trial(harness):
    """P5, and the faulty instrument computed. The wound's own validity node is
    an ordinary artifact: refuting it collapses the warrant and REINSTATES the
    subject -- and standing was never disturbed on either leg of that round
    trip, which is the whole point of separating the axes."""
    subject, _, _, _, problem = _framed(harness)
    before = standing_of(harness, subject.id)
    critic = _wound(harness, subject.id)
    assert harness.state.status[subject.id] is Status.REFUTED

    attack(harness, critic.id, "the-tidal-lag-instrument-was-uncalibrated")

    assert harness.state.status[subject.id] is Status.ACCEPTED
    assert standing_of(harness, subject.id) == before
    assert frames(harness, subject.id, problem.id) is True


def test_nothing_in_the_standing_path_reads_a_wound(harness):
    """G1, structurally. A behavioural test can only show that standing did not
    move on the graphs it built. This shows the consult path has no way to read
    a wound at all: `standing.py` names no warrant symbol, and the module holds
    no call that could write one."""
    source = pathlib.Path("src/deepreason/calculus/standing.py").read_text()
    tree = ast.parse(source)
    names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not {"warrants", "wound_refs"} & names
    assert "register_fail_warrant" not in source
    calls = [
        ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)
    ]
    assert not [c for c in calls if c.split(".")[-1].startswith(
        ("create_", "register_", "record_", "commit_", "append_")
    )], calls
