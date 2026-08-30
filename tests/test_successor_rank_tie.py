"""A minted successor problem never wins a rank TIE against the seed question.

Regression (selfstudy run-9175f0ec): at cycle 0 every problem is never-worked,
so selection fell to the bare id tie-break and a spawned problem preempted the
operator's question, which then terminated `budget_denied` with zero calls.
`tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero`
pinned that against the spawn triggers that existed then. This file MIRRORS it
-- deliberately, rather than editing it, so the existing regression stays
byte-unchanged -- with the trigger the 2026-08-29 P9 law revived:
`SpawnTrigger.SUCCESSOR`.

WHAT THIS PROVES: the seed term. `Scheduler._select_problem` ranks under two
keys, and in both of them `p.provenance.trigger != SpawnTrigger.SEED` is False
for the seed and True for a successor, and False sorts before True. So a minted
successor loses every TIE to the operator's question, in both selection modes,
by construction and with no scheduler change.

WHAT THIS DOES NOT PROVE, stated plainly because a test that overclaims is
worse than no test: STRICT DOMINATION. In the LIVENESS_QUEUE key the FIRST term
is `-(age * weight)` and the seed term is SECOND, so a freshly minted successor
-- never worked, therefore maximally aged -- can out-AGE a seed that HAS been
worked. Closing that would change the rank key itself, a socket pinned by two
map checks and by the regression this file mirrors; it is parked as the
tranche's Q4 and is a separate tranche, not a silent widening of this one.
"""

from __future__ import annotations

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Provenance
from deepreason.ontology.problem import SpawnTrigger
from deepreason.scheduler.scheduler import Scheduler

SEED_ID = "question-98a0e3a77a0e"
SUCCESSOR_ID = "succ:0e26d6be54fd"
# A second successor whose id sorts BEFORE the seed's. Live successor ids are
# "succ:<digest>" and every one of them sorts AFTER "question-<digest>", so a
# fixture built only from real-shaped ids cannot exercise the seed term at all
# in LIVENESS_QUEUE mode -- the final `p.id` tie-break decides it first.
EARLY_ID_SUCCESSOR_ID = "aaa:0e26d6be54fd"


def _register(harness, *, early_id_successor: bool = False):
    harness.register_commitment(Commitment(id="k-q", eval="predicate:'x' in content"))
    # Registration order favours the successor. Id-order does NOT: a real
    # "succ:..." id sorts AFTER "question-...", so the bare id tie-break
    # already favours the seed and cannot prove the seed term on its own.
    # `early_id_successor` adds one that DOES sort first, which is what makes
    # the LIVENESS_QUEUE arm below able to fail.
    harness.register_problem(Problem(
        id=SUCCESSOR_ID, description="what would settle the solar term?",
        criteria=["k-q"],
        provenance=ProblemProvenance.model_validate(
            {"trigger": "successor", "from": [SEED_ID, "artifact-under-criticism"]}),
    ))
    if early_id_successor:
        harness.register_problem(Problem(
            id=EARLY_ID_SUCCESSOR_ID,
            description="what would settle the lunar term?",
            criteria=["k-q"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "successor",
                 "from": [SEED_ID, "artifact-under-criticism"]}),
        ))
    harness.register_problem(Problem(
        id=SEED_ID, description="the operator's question", criteria=["k-q"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    # Admission bookkeeping: accepted import-role records addressing the
    # question. Import-role admissions must not count as survivors, or the
    # question drops to the 0.3 aging weight before a single provider call.
    for i in range(2):
        harness.create_artifact(
            f"attached-source record {i}",
            provenance=Provenance(role="import"),
            problem_id=SEED_ID,
        )


def test_a_minted_successor_loses_the_rank_tie_to_the_seed_question(tmp_path):
    """Both selection modes, at cycle 0, where every problem is never-worked
    and the tie-break is the only thing separating them.

    One of the two successors carries an id that sorts BEFORE the seed's, so
    in BOTH keys every term below the seed term now favours a successor: the
    seed can win here only on the seed term itself. Without it this arm passed
    with the LIVENESS_QUEUE seed term deleted, because "succ:..." sorts after
    "question-..." and the id tie-break was quietly doing the work.
    """
    for liveness in (True, False):
        harness = Harness(tmp_path / f"run-{liveness}")
        _register(harness, early_id_successor=True)
        # The fixture is what it says it is: both rivals really do carry the
        # trigger the seed term discriminates on.
        assert {
            harness.state.problems[pid].provenance.trigger
            for pid in (SUCCESSOR_ID, EARLY_ID_SUCCESSOR_ID)
        } == {SpawnTrigger.SUCCESSOR}
        config = Config(LIVENESS_QUEUE=liveness, N_SCHOOLS=0)
        scheduler = Scheduler(harness, LLMAdapter({}, harness.blobs), config)

        first = scheduler._select_problem()
        assert first is not None and first.id == SEED_ID, (
            f"cycle 0 (liveness={liveness}) went to {first and first.id}: "
            "a minted successor problem preempted the operator's question"
        )


def test_the_rank_term_follows_the_trigger_and_not_the_id(tmp_path):
    """The mechanism, EXERCISED rather than re-derived: the term is a boolean
    over the TRIGGER, so moving the seed trigger to the other problem moves the
    winner with it, with the two ids held fixed.

    Four arms: both selection modes crossed with both placements of the seed
    trigger. The arm where the seed holds the id-disfavoured "zzz-" id dies if
    the seed term is deleted from that mode's key; all four die if the term is
    kept but inverted (`not (p.provenance.trigger != SpawnTrigger.SEED)`) --
    the edit that reverses this file's whole guarantee while leaving a
    source-text count of it untouched.
    """
    low, high = "aaa-rank-probe", "zzz-rank-probe"
    for liveness in (True, False):
        for seed_id in (low, high):
            other = high if seed_id == low else low
            harness = Harness(tmp_path / f"run-{liveness}-{seed_id}")
            harness.register_commitment(
                Commitment(id="k-q", eval="predicate:'x' in content")
            )
            # The successor is registered FIRST, so registration order never
            # decides this in the round-robin key either.
            harness.register_problem(Problem(
                id=other, description="the successor's question",
                criteria=["k-q"],
                provenance=ProblemProvenance.model_validate(
                    {"trigger": "successor",
                     "from": [seed_id, "artifact-under-criticism"]}),
            ))
            harness.register_problem(Problem(
                id=seed_id, description="the operator's question",
                criteria=["k-q"],
                provenance=ProblemProvenance.model_validate(
                    {"trigger": "seed", "from": []}),
            ))
            config = Config(LIVENESS_QUEUE=liveness, N_SCHOOLS=0)
            scheduler = Scheduler(harness, LLMAdapter({}, harness.blobs), config)

            first = scheduler._select_problem()
            assert first is not None and first.id == seed_id, (
                f"liveness={liveness}, seed on {seed_id!r}: selection went to "
                f"{first and first.id!r} -- the winner followed the id, not "
                "the trigger"
            )


def test_the_seed_term_appears_once_per_selection_mode():
    """A TEXT pin on the term's ARITY, and nothing more.

    Stated plainly because the previous version of this test claimed to assert
    the mechanism and did not: a source count survives an edit that keeps the
    substring and inverts its sense. The term's SENSE is carried by
    `test_the_rank_term_follows_the_trigger_and_not_the_id` above; what this
    adds is that a THIRD or a MISSING selection-mode key is visible here even
    when no fixture happens to reach it.
    """
    import pathlib

    source = pathlib.Path("src/deepreason/scheduler/scheduler.py").read_text()
    assert source.count("provenance.trigger != SpawnTrigger.SEED") == 2, (
        "the seed term appears once per selection mode; a change to that count "
        "is a change to the promise this file mirrors"
    )


def test_the_successor_still_gets_worked_once_the_question_has_been(tmp_path):
    """Losing every tie is not starvation. Once the seed has been worked, the
    aged never-worked successor wins on the age term -- which is the rotation
    working, and is also exactly the residue Q4 parks."""
    harness = Harness(tmp_path / "run")
    _register(harness)
    config = Config(LIVENESS_QUEUE=True, N_SCHOOLS=0)
    scheduler = Scheduler(harness, LLMAdapter({}, harness.blobs), config)

    assert scheduler._select_problem().id == SEED_ID
    scheduler._cycles = 1
    assert scheduler._select_problem().id == SUCCESSOR_ID
