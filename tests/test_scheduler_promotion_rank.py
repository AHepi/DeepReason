"""D-1's one scheduling consequence: the wounded background stays visible.

Implements C-D1 (v2 calculus program, Rung 7). The decision the operator
answered was whether a wound to a consulted background gets its own standing-
layer spawn trigger, and the answer was A:

    Render state only (+ the incumbent's promotion problem stays on the
    frontier, ranked up by wound count — attention only).

Two things are therefore under test, and the ABSENCE is the more important of
them. There is no crisis-problem spawn trigger anywhere: H1's content is "stop
minting problems from failures", and re-introducing that shape one layer up
would be the same shape. What there IS instead is a rank term — attention only,
after the seed term, moving no label.
"""

import ast
import inspect
import pathlib

from deepreason.calculus import operations
from deepreason.calculus.nomination import promotion_wound_counts
from deepreason.config import Config
from deepreason.ontology import (
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    SpawnTrigger,
)
from deepreason.llm.adapter import LLMAdapter
from deepreason.scheduler.scheduler import Scheduler
from tests.conftest import attack


def _art(harness, text):
    return harness.create_artifact(
        text, interface=Interface(), provenance=Provenance(role="critic")
    )


def _promotion(harness, label, wounds):
    subject = _art(harness, f"b-{label}: a background for the tides")
    problem = operations.ensure_promotion_problem(
        harness, subject.id, f"promote or refuse {label}"
    )
    for i in range(wounds):
        attack(harness, subject.id, f"{label}-mispredicts-observation-{i}")
    return subject, problem


def _scheduler(harness, **config_kwargs):
    """A scheduler with NO seats. Selection is attention and reaches no
    provider, so an empty adapter is the honest fixture: if selection ever
    needed a seat, this would fail rather than quietly succeed."""
    return Scheduler(harness, LLMAdapter({}, harness.blobs), Config(**config_kwargs))


def _seed(harness, pid="the-operators-question"):
    return harness.register_problem(
        Problem(
            id=pid, description="what governs the tides", criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


# --- the count ---------------------------------------------------------------

def test_the_count_is_warrants_against_the_subject(harness):
    """A wound is what the RECORD says broke the incumbent -- a registered
    warrant against its subject. Derived, never authored."""
    subject, problem = _promotion(harness, "lunar", wounds=3)
    counts = promotion_wound_counts(harness)
    assert counts == {problem.id: 3}
    assert all(
        harness.warrants[wid].target == subject.id
        for wid in harness.warrants
    )


def test_an_unwounded_promotion_problem_counts_zero(harness):
    """Zero is a count, not an absence: a promotion problem nobody has wounded
    is still on the frontier, it simply does not rise."""
    _, problem = _promotion(harness, "lunar", wounds=0)
    assert promotion_wound_counts(harness) == {problem.id: 0}


def test_only_promotion_problems_are_counted(harness):
    """An ordinary problem has no incumbent, so it has no wound count. Counting
    one would be ranking every problem by how much criticism its candidates
    attracted, which is a different measure entirely."""
    _seed(harness)
    _, problem = _promotion(harness, "lunar", wounds=2)
    assert set(promotion_wound_counts(harness)) == {problem.id}


# --- the rank term -----------------------------------------------------------

def test_the_more_wounded_background_is_selected_first(harness):
    """The consequence D-1 asks for. Two promotion problems of the same age;
    the one carrying more wounds is worked first, because a wounded background
    with no account of its wounds is the louder open demand."""
    _, quiet = _promotion(harness, "quiet", wounds=1)
    _, loud = _promotion(harness, "loud", wounds=4)
    scheduler = _scheduler(harness, LIVENESS_QUEUE=True)
    assert scheduler._select_problem().id == loud.id


def test_the_operators_seed_question_still_wins_every_tie(harness):
    """A CLAUDE.md invariant, and the reason the term sits AFTER the seed term
    rather than before it. A heavily wounded background must not be able to
    outrank the operator's own question."""
    _promotion(harness, "loud", wounds=40)
    seed = _seed(harness)
    scheduler = _scheduler(harness, LIVENESS_QUEUE=True)
    assert scheduler._select_problem().id == seed.id


def test_the_seed_wins_on_the_rotation_path_too(harness):
    """The non-liveness pool sorts by the same key, so the guarantee does not
    depend on which selection path a run is configured for."""
    _promotion(harness, "loud", wounds=40)
    seed = _seed(harness)
    scheduler = _scheduler(harness, LIVENESS_QUEUE=False)
    assert scheduler._select_problem().id == seed.id


def test_the_rank_term_moves_no_label(harness):
    """C5. Selection is attention: computing the rank leaves every label, every
    edge and the log length exactly as they were."""
    _promotion(harness, "loud", wounds=3)
    _seed(harness)
    # Built BEFORE the snapshot: constructing a scheduler records its own
    # start-up events, and folding those into this test would make it assert
    # something it is not about.
    scheduler = _scheduler(harness, LIVENESS_QUEUE=True)
    before = (dict(harness.state.status), list(harness.state.att),
              harness._next_seq)
    assert scheduler._select_problem() is not None
    assert (dict(harness.state.status), list(harness.state.att),
            harness._next_seq) == before


# --- the ABSENCE D-1 actually decided ---------------------------------------

def test_no_standing_layer_spawn_trigger_exists(harness):
    """D-1 answered A, and A is defined by what it does NOT build. Road B was a
    trigger minting a crisis problem from a consulted assertion under attack --
    the shape H1 deleted, one layer up. Nothing in the tree mints a problem
    from a wound."""
    counts = {}
    for path in sorted(pathlib.Path("src/deepreason").rglob("*.py")):
        source = path.read_text()
        if "SpawnTrigger" not in source:
            continue
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.FunctionDef):
                continue
            body = ast.unparse(node)
            if "register_problem" not in body and "spawn(" not in body:
                continue
            if "warrant" in body.lower() and "crisis" in body.lower():
                counts[f"{path.name}::{node.name}"] = True
    assert counts == {}, counts
    assert not [
        p for p in pathlib.Path("src/deepreason").rglob("*.py")
        if "crisis_problem" in p.read_text()
    ]


def test_a_wound_still_spawns_nothing(harness):
    """Behaviourally, on the record rather than on the source. Wounding the
    subject of a consulted frame adds NO problem to the frontier."""
    _, problem = _promotion(harness, "lunar", wounds=0)
    before = set(harness.state.problems)
    attack(harness, harness.state.problems[problem.id].provenance.from_[0],
           "the-lunar-theory-mispredicts-the-lag")
    assert set(harness.state.problems) == before


def test_the_scheduler_reaches_no_standing_view(harness):
    """The narrowed disambiguation check, still true. The rank term reads a
    warrant count and a problem's own provenance -- never `standing_of`,
    `standing_view` or `problem_status`."""
    source = inspect.getsource(promotion_wound_counts)
    for symbol in ("standing_of", "standing_view", "consulted", "problem_status"):
        assert symbol not in source, symbol
    for path in sorted(pathlib.Path("src/deepreason/scheduler").rglob("*.py")):
        tree = ast.parse(path.read_text())
        names = {a.name for n in ast.walk(tree)
                 if isinstance(n, ast.ImportFrom) for a in n.names}
        assert not (names & {"standing_of", "standing_view", "problem_status"})
