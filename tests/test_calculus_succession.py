"""Succession detection and the ONE proper render exception.

Implements R4 (v2 calculus program, Rung 7). §9.7:

    Succession is discrimination. Rival frame assertions over overlapping scope
    trigger the ordinary >=2-survivors discrimination spawn... One render
    exception is proper to succession: the succession pack suppresses the
    incumbent's frame slice and renders both articulation digests, so the trial
    of a frame is framed by neither party.

The failure mitigated has a name -- INCUMBENT-JUDGE BIAS: a succession posed
inside the incumbent's vocabulary is adjudicated by the defendant. Two things
are asserted about the mitigation and the second matters as much as the first:
that the incumbent's frame is SUPPRESSED, and that what replaces it is
SYMMETRIC. A pack that suppressed the frame and then showed one candidate more
generously would have moved the bias rather than removed it.
"""

import ast
import pathlib

from deepreason.calculus import operations
from deepreason.calculus.render import (
    frame_slices,
    render_frame_crisis_context,
    render_frame_slice_context,
)
from deepreason.calculus.succession import (
    SUCCESSION_CRITERION_ORDER,
    is_succession_trial,
    render_succession_context,
    succession_trial_of,
)
from deepreason.ontology import (
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    SpawnTrigger,
)
from deepreason.rules.spawn import scan_spawns
from tests.conftest import attack


TIDES = {
    "schema": "declarative-scope.v1",
    "predicate": {"op": "contains",
                  "args": [{"field": "description"}, {"text": "tides"}]},
}

# A scope that admits the DISCRIMINATION problem as well as the tidal ones,
# because that is the case the suppression exists for: a frame whose sigma
# reaches the succession problem posed inside it would otherwise frame its own
# trial. The narrow TIDES scope would make the suppression untestable -- it
# would look suppressed when it was merely out of scope.
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


def _rivalry(harness, *, criteria=("k-beta", "k-alpha")):
    """Two rival frame assertions on ONE promotion problem, and the ordinary
    discrimination problem the existing spawn rule mints for them.

    `scan_spawns` is called unchanged and knows nothing about frames: two
    accepted candidates on one problem is two accepted candidates on one
    problem. That is what "succession as ordinary discrimination" means -- the
    rivalry reaches the frontier through machinery this rung did not touch.
    """
    from deepreason.config import Config

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
    )
    a2 = operations.file_frame_assertion(
        harness, problem=promotion, subject_ref=rival.id, scope=WIDE,
        reach_case_refs=(case2.id,), departure_protocol="declare it",
    )
    spawned = scan_spawns(harness, Config())
    disc = next(
        p for p in spawned
        if p.provenance.trigger is SpawnTrigger.DISCRIMINATION
    )
    return incumbent, rival, promotion, a1, a2, disc


# --- detection ---------------------------------------------------------------


def test_the_ordinary_discrimination_spawn_is_what_mints_it(harness):
    """R4's first half. Nothing in this rung spawns a succession problem: the
    rivalry arrives through `rules/spawn.py`'s existing >=2-survivors branch,
    which has no idea what a frame is."""
    _, _, promotion, a1, a2, disc = _rivalry(harness)
    assert disc.id == f"disc:{promotion.id}"
    assert disc.provenance.from_[0] == promotion.id
    assert set(disc.provenance.from_[1:]) == {a1.id, a2.id}


def test_a_succession_trial_is_recognised_from_the_record(harness):
    """Three conditions, each a fact about the record rather than a claim: a
    discrimination problem, over a promotion problem, between recognised frame
    assertions."""
    incumbent, rival, promotion, a1, a2, disc = _rivalry(harness)
    trial = succession_trial_of(harness, disc.id)
    assert trial is not None
    assert trial.promotion_problem == promotion.id
    assert sorted(trial.rival_ids) == sorted([a1.id, a2.id])
    assert sorted(trial.subject_ids) == sorted([incumbent.id, rival.id])


def test_an_ordinary_discrimination_is_not_a_succession_trial(harness):
    """The negative control, and it is the one that keeps the exception NARROW.
    Two candidates on an ordinary problem get the ordinary pack -- if they did
    not, every discrimination in the run would lose its frame."""
    from deepreason.config import Config

    problem = harness.register_problem(
        Problem(
            id="what-governs-the-tides", description="what governs the tides",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    harness.create_artifact("c1: a lunar account", problem_id=problem.id)
    harness.create_artifact("c2: a solar account", problem_id=problem.id)
    disc = next(
        p for p in scan_spawns(harness, Config())
        if p.provenance.trigger is SpawnTrigger.DISCRIMINATION
    )
    assert succession_trial_of(harness, disc.id) is None
    assert is_succession_trial(harness, disc.id) is False


def test_a_discrimination_between_non_frames_is_not_one(harness):
    """Recognition is STRICT. Two artifacts that merely mention frames are not
    frame claims, and a discrimination between them is ordinary."""
    from deepreason.config import Config

    subject = _art(harness, "b: the lunar theory of tides")
    promotion = operations.ensure_promotion_problem(
        harness, subject.id, "promote or refuse a frame for the tides"
    )
    harness.create_artifact("not a frame claim, only prose about frames",
                            problem_id=promotion.id)
    harness.create_artifact("also prose about frames", problem_id=promotion.id)
    disc = next(
        p for p in scan_spawns(harness, Config())
        if p.provenance.trigger is SpawnTrigger.DISCRIMINATION
    )
    assert succession_trial_of(harness, disc.id) is None


# --- the ONE render exception ------------------------------------------------


def test_the_incumbents_frame_slice_is_suppressed(harness):
    """R4's centrepiece. The frame that would otherwise have framed this
    problem yields NO slice -- and the suppression covers BOTH renderers,
    because it lives in `frame_slices` and not in either of them."""
    _, _, _, _, _, disc = _rivalry(harness)
    # sigma admits the discrimination problem, so a frame WOULD render here
    from deepreason.calculus.standing import frames
    from deepreason.calculus.standing import consulted

    assert consulted(harness)                    # the frames are consulted
    assert any(
        frames(harness, g.subject_id, disc.id) for g in consulted(harness)
    )
    assert frame_slices(harness, disc.id) == ()
    assert render_frame_crisis_context(harness, disc.id) is None


def test_both_articulation_digests_are_rendered(harness):
    """The other half of §9.7's sentence. Suppressing the frame and showing
    nothing would leave the trial with no candidates to compare; suppressing it
    and showing ONE would be the bias wearing a different hat."""
    incumbent, rival, _, _, _, disc = _rivalry(harness)
    text = render_frame_slice_context(harness, disc.id)
    assert text is not None
    assert "SUCCESSION TRIAL" in text
    assert "the lunar theory of tides" in text
    assert "the lunisolar theory of tides" in text
    assert incumbent.id in text and rival.id in text


def test_the_two_candidates_are_presented_identically(harness):
    """SYMMETRIC EXPOSURE, checked as a property of the text rather than
    trusted to the author. Both candidates get the same block shape, and
    neither is labelled incumbent or challenger anywhere."""
    _, _, _, _, _, disc = _rivalry(harness)
    text = render_succession_context(harness, disc.id)
    assert text.count("subject ") == 2
    assert "CANDIDATE A" in text and "CANDIDATE B" in text
    lowered = text.lower()
    for word in ("incumbent", "challenger", "successor", "defender",
                 "original", "new frame"):
        assert word not in lowered, word


def test_the_pack_carries_no_provenance_populated_or_blank(harness):
    """`RESEARCH_JUDGE_BLINDING`'s placebo result: a present-but-empty
    provenance slot draws MORE attention than a filled one. So no author, no
    seat, no role, no school, no "(none)" and no "redacted"."""
    _, _, _, _, _, disc = _rivalry(harness)
    text = render_succession_context(harness, disc.id).lower()
    for word in ("author", "provenance", "school", "seat", "role:", "model",
                 "endpoint", "(none)", "redacted"):
        assert word not in text, word


def test_the_candidates_are_ordered_by_content_not_by_arrival(harness):
    """Ax 4.1 (Genesis Inertness). Ordering the two by who arrived first would
    let provenance into what the judge sees; they are ordered by subject id,
    which is a fact about content."""
    incumbent, rival, _, _, _, disc = _rivalry(harness)
    text = render_succession_context(harness, disc.id)
    first, second = sorted([incumbent.id, rival.id])
    assert text.index(first) < text.index(second)


def test_the_wounds_render_on_both_sides_or_neither(harness):
    """ANOMALY CONSERVATION at the render layer. What broke each candidate is
    what a successor must predict, so it is shown for both -- under the same
    cap, stated in-band where it bites."""
    incumbent, rival, _, _, _, disc = _rivalry(harness)
    critic_a, _ = attack(harness, incumbent.id, "the-lunar-theory-mispredicts-the-lag")
    critic_b, _ = attack(harness, rival.id, "the-lunisolar-theory-overfits-the-record")

    text = render_succession_context(harness, disc.id)
    assert text.count("ITS WOUNDS") == 2
    assert critic_a.id in text and critic_b.id in text


def test_the_criteria_render_in_the_recorded_fixed_order(harness):
    """Q2c reaches the PACK as well as the record, and it must be the same
    order in both -- a trial that recorded "fixed" while showing the criteria
    in registration order would be recording a discipline it did not have."""
    _, _, _, _, _, disc = _rivalry(harness, criteria=("k-beta", "k-alpha"))
    text = render_succession_context(harness, disc.id)
    assert SUCCESSION_CRITERION_ORDER == "fixed"
    assert text.index("k-alpha") < text.index("k-beta")
    trial = succession_trial_of(harness, disc.id)
    assert list(trial.criteria) == ["k-alpha", "k-beta"]


def test_an_ordinary_problem_still_gets_its_frame(harness):
    """The exception is ONE exception. Every problem that is not a succession
    trial renders exactly as Rung 6 delivered it."""
    _rivalry(harness)
    problem = harness.register_problem(
        Problem(
            id="what-governs-the-tides", description="what governs the tides",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    text = render_frame_slice_context(harness, problem.id)
    assert text is not None
    assert text.startswith("FRAME (consulted background")
    assert "SUCCESSION TRIAL" not in text


def test_the_suppression_is_one_site(harness):
    """Structural, and the reason it is worth asserting: two suppressions could
    drift, and a pack that suppressed the digest but kept the crisis would
    still be posed in the incumbent's vocabulary."""
    source = pathlib.Path("src/deepreason/calculus/render.py").read_text()
    assert source.count("is_succession_trial") == 2   # the import and the call
    tree = ast.parse(source)
    calling = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and "is_succession_trial(" in ast.unparse(node)
    ]
    assert calling == ["frame_slices"], calling


def test_the_succession_render_writes_nothing(harness):
    """A9. The render acts through attention only: computing it leaves the
    record byte-identical."""
    _, _, _, _, _, disc = _rivalry(harness)
    before = (dict(harness.state.status), set(harness.state.artifacts),
              harness._next_seq)
    assert render_succession_context(harness, disc.id) is not None
    assert (dict(harness.state.status), set(harness.state.artifacts),
            harness._next_seq) == before
