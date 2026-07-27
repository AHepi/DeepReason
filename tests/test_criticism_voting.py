"""Tests for the criticism-filtered voting model and the theory verifier.

hypothesis is not a project dependency, so there are no property-based
tests; every check here is a fixed exact case.
"""
from __future__ import annotations

import importlib.util
import json
import random
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from deepreason.experiments.criticism_voting import (
    TIE_RULES,
    AbstainIfAnyFlag,
    DifficultyMixture,
    HomogeneousCritic,
    IndependentErrors,
    MajorityConditionalCritic,
    MarginConditionalCritic,
    Question,
    RemoveAllFlagged,
    RemoveOneFlagged,
    Reweight,
    aggregate_metrics,
    broken,
    enumerate_joint,
    exact_metrics,
    outcome_after,
    outcome_before,
    population_eval,
    repair_break_probs,
    repaired,
    simulate_metrics,
)

REPO = Path(__file__).resolve().parents[1]


def _load_verifier():
    spec = importlib.util.spec_from_file_location(
        "verify_glm_judge_theory", REPO / "scripts" / "verify_glm_judge_theory.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("verify_glm_judge_theory", mod)
    spec.loader.exec_module(mod)
    return mod


def q(correct, flags):
    return Question(len(correct), tuple(correct), tuple(flags))


T, N = True, False


# ---------------------------------------------------------------------------
# Majority rule and tie rules


def test_exact_majority_odd_k():
    assert outcome_before(q([T, T, N], [N] * 3), "incorrect") == 1
    assert outcome_before(q([T, N, N], [N] * 3), "incorrect") == 0


def test_exact_majority_even_k_tie_rules():
    # Even k, 2-2 pre-filter tie: rule-dependent; "unchanged" has no earlier
    # outcome at pre-filter and resolves as incorrect.
    tied = q([T, T, N, N], [N] * 4)
    assert outcome_before(tied, "incorrect") == 0
    assert outcome_before(tied, "random") == F(1, 2)
    assert outcome_before(tied, "unchanged") == 0


def test_post_filter_tie_rules():
    # 3 correct vs 2 wrong; one false flag makes it 2-2 post-filter.
    qq = q([T, T, T, N, N], [T, N, N, N, N])
    pol = RemoveAllFlagged()
    assert outcome_after(qq, pol, "incorrect") == 0
    assert outcome_after(qq, pol, "random") == F(1, 2)
    # "unchanged" falls back to the pre-filter outcome, which was correct.
    assert outcome_after(qq, pol, "unchanged") == 1


# ---------------------------------------------------------------------------
# Filtering policy semantics


def test_remove_all_flagged():
    qq = q([T, T, N, N, N], [N, T, T, T, N])
    # Remaining: 1 correct, 1 wrong -> tie.
    assert outcome_after(qq, RemoveAllFlagged(), "incorrect") == 0
    qq2 = q([T, T, N, N, N], [N, N, T, T, N])
    # Remaining: 2 correct, 1 wrong -> correct.
    assert outcome_after(qq2, RemoveAllFlagged(), "incorrect") == 1


def test_remove_one_flagged_takes_first_in_index_order():
    # First flagged candidate is the correct one at index 1, not the wrong
    # one at index 3; removal leaves 2 correct vs 2 wrong -> tie -> incorrect.
    qq = q([T, T, T, N, N], [N, T, N, T, N])
    assert outcome_after(qq, RemoveOneFlagged(), "incorrect") == 0
    # No flags: no-op.
    clean = q([T, T, T, N, N], [N] * 5)
    assert outcome_after(clean, RemoveOneFlagged(), "incorrect") == 1


def test_abstain_if_any_flag_scores_prefilter_outcome():
    qq = q([T, T, N, N, N], [T, T, N, N, N])
    # Filtering would empty the correct votes; abstain keeps the (wrong)
    # pre-filter outcome and never repairs or breaks.
    assert outcome_after(qq, AbstainIfAnyFlag(), "incorrect") == 0
    assert repair_break_probs(qq, AbstainIfAnyFlag(), "incorrect") == (0, 0)
    right = q([T, T, T, N, N], [T, T, T, N, N])
    assert outcome_after(right, AbstainIfAnyFlag(), "incorrect") == 1


def test_reweight_policy():
    # 2 correct (one flagged at weight 1/2) vs 2 wrong (one flagged):
    # correct weight 3/2 vs wrong weight 3/2 -> tie.
    qq = q([T, T, N, N], [T, N, T, N])
    assert outcome_after(qq, Reweight(F(1, 2)), "incorrect") == 0
    # Weight 0 reduces to remove-all.
    assert outcome_after(qq, Reweight(F(0)), "incorrect") == outcome_after(
        qq, RemoveAllFlagged(), "incorrect"
    )
    # Weight 1 is a no-op.
    assert outcome_after(qq, Reweight(F(1)), "incorrect") == outcome_before(qq, "incorrect")


# ---------------------------------------------------------------------------
# Derived aggregates, repair and break detection


def test_aggregates_from_explicit_vectors():
    qs = [
        q([T, T, N, N, N], [N, T, T, N, N]),  # tp=1 fp=1
        q([T, T, T, T, N], [N, N, N, N, T]),  # tp=1 fp=0
    ]
    agg = aggregate_metrics(qs)
    assert agg["tp"] == 2 and agg["fp"] == 1
    assert agg["n_wrong"] == 4 and agg["n_correct"] == 6
    assert agg["precision"] == F(2, 3)
    assert agg["recall"] == F(1, 2)
    assert agg["fpr"] == F(1, 6)
    assert agg["base_error"] == F(2, 5)


def test_aggregates_undefined_cases():
    agg = aggregate_metrics([q([T, T, T], [N, N, N])])
    assert agg["precision"] is None
    assert agg["recall"] is None
    assert agg["fpr"] == 0


def test_repair_and_break_detection():
    fixed = q([T, T, N, N, N], [N, N, T, T, N])
    assert repaired(fixed, RemoveAllFlagged(), "incorrect")
    assert not broken(fixed, RemoveAllFlagged(), "incorrect")
    wrecked = q([T, T, T, N, N], [T, T, N, N, N])
    assert broken(wrecked, RemoveAllFlagged(), "incorrect")
    assert not repaired(wrecked, RemoveAllFlagged(), "incorrect")
    untouched = q([T, T, T, N, N], [N] * 5)
    assert not repaired(untouched, RemoveAllFlagged(), "incorrect")
    assert not broken(untouched, RemoveAllFlagged(), "incorrect")


# ---------------------------------------------------------------------------
# Identical aggregates, different outcomes (hand-built Experiment C witness)


def test_identical_aggregates_opposite_outcomes():
    # Same candidate population (correct counts 1, 2, 3 out of k=5) and the
    # same flag totals (TP=2, FP=1), so precision, recall, FPR and base error
    # are identical; only the allocation across questions differs.
    critic_x = [
        q([T, N, N, N, N], [T, N, N, N, N]),  # FP parked on a robust wrong pool
        q([T, T, N, N, N], [N, N, T, T, N]),  # TPs repair the fragile wrong pool
        q([T, T, T, N, N], [N, N, N, N, N]),
    ]
    critic_y = [
        q([T, N, N, N, N], [N, T, N, N, N]),  # TP wasted on a robust wrong pool
        q([T, T, N, N, N], [N, N, T, N, N]),  # TP wasted (2-2 tie stays wrong)
        q([T, T, T, N, N], [T, N, N, N, N]),  # FP breaks the fragile correct pool
    ]
    rx = population_eval(critic_x, RemoveAllFlagged(), "incorrect")
    ry = population_eval(critic_y, RemoveAllFlagged(), "incorrect")
    for key in ("precision", "recall", "fpr", "base_error", "tp", "fp"):
        assert rx["aggregates"][key] == ry["aggregates"][key]
    assert rx["net"] > 0 > ry["net"]
    assert rx["repaired"] == 1 and rx["broken"] == 0
    assert ry["repaired"] == 0 and ry["broken"] == 1


# ---------------------------------------------------------------------------
# Exhaustive enumeration


def test_enumeration_probabilities_sum_to_one_exactly():
    em = DifficultyMixture(F(1, 3), F(7, 10), F(1, 10))
    cr = MajorityConditionalCritic(F(1, 5), F(1, 20), F(4, 5), F(1, 2))
    total = sum(w for _, w in enumerate_joint(4, em, cr))
    assert total == 1
    assert sum(1 for _ in enumerate_joint(4, em, cr)) == 4**4


def test_enumeration_reproducible():
    em = IndependentErrors(F(3, 10))
    cr = HomogeneousCritic(F(3, 4), F(1, 10))
    a = exact_metrics(5, em, cr, RemoveAllFlagged(), "incorrect")
    b = exact_metrics(5, em, cr, RemoveAllFlagged(), "incorrect")
    assert a == b


@pytest.mark.parametrize("k", [3, 4, 5])
@pytest.mark.parametrize("tie", TIE_RULES)
def test_counts_method_equals_full_enumeration(k, tie):
    em = IndependentErrors(F(1, 4))
    cr = HomogeneousCritic(F(3, 4), F(1, 10))
    for pol in (RemoveAllFlagged(), RemoveOneFlagged(), AbstainIfAnyFlag(), Reweight(F(1, 3))):
        assert exact_metrics(k, em, cr, pol, tie, "counts") == exact_metrics(
            k, em, cr, pol, tie, "full"
        )


def test_counts_method_equals_full_for_conditional_critics():
    em = DifficultyMixture(F(1, 2), F(3, 5), F(1, 10))
    for cr in (
        MajorityConditionalCritic(F(1, 5), F(1, 20), F(4, 5), F(1, 2)),
        MarginConditionalCritic((F(1, 2), F(1, 5)), ((1, F(9, 10), F(1, 2)), (-1, F(1, 10), F(0)))),
    ):
        for k in (3, 4, 5):
            assert exact_metrics(k, em, cr, RemoveAllFlagged(), "random", "counts") == (
                exact_metrics(k, em, cr, RemoveAllFlagged(), "random", "full")
            )


def test_exact_metrics_known_value():
    # k=3, e=1/2, perfect critic (TPR=1, FPR=0), remove_all, tie incorrect:
    # every wrong candidate is removed, so harness is correct unless all
    # three candidates are wrong (prob 1/8) or ties resolve; remaining pool
    # is all-correct whenever at least one correct exists -> harness = 7/8.
    m = exact_metrics(3, IndependentErrors(F(1, 2)), HomogeneousCritic(F(1), F(0)),
                      RemoveAllFlagged(), "incorrect")
    assert m.sc_accuracy == F(1, 2)
    assert m.harness_accuracy == F(7, 8)
    assert m.p_break == 0
    assert m.precision == 1
    assert m.recall == 1
    assert m.base_error == F(1, 2)


# ---------------------------------------------------------------------------
# Monte Carlo determinism


def test_fixed_seed_reproducibility():
    em = IndependentErrors(F(1, 4))
    cr = HomogeneousCritic(F(3, 4), F(1, 10))
    a = simulate_metrics(11, 500, em, cr, RemoveAllFlagged(), "random", seed=123)
    b = simulate_metrics(11, 500, em, cr, RemoveAllFlagged(), "random", seed=123)
    assert a == b
    c = simulate_metrics(11, 500, em, cr, RemoveAllFlagged(), "random", seed=124)
    assert a != c


# ---------------------------------------------------------------------------
# Verifier helpers: minimization determinism and JSON round-trip


def test_counterexample_minimization_deterministic():
    v = _load_verifier()
    ces = [
        v.CE(7, F(1, 4), F(1, 2), F(0), "incorrect", F(0), F(1), F(3, 100), "a"),
        v.CE(5, F(1, 2), F(1), F(1, 4), "random", F(0), F(1), F(1, 100), "b"),
        v.CE(5, F(1, 2), F(1, 4), F(1, 4), "random", F(0), F(1), F(1, 100), "c"),
        v.CE(5, F(3, 4), F(1), F(1, 4), "unchanged", F(0), F(1), F(2, 100), "d"),
    ]
    expected = ces[2]  # smallest (k, distance, e, tpr, ...)
    rng = random.Random(0)
    for _ in range(5):
        shuffled = ces[:]
        rng.shuffle(shuffled)
        assert v.smallest_counterexample(shuffled) == expected
    assert v.smallest_counterexample([]) is None


def test_theorem_record_json_round_trip():
    v = _load_verifier()
    ce = v.CE(5, F(1, 4), F(1, 2), F(1, 20), "incorrect", F(3, 4), F(7, 8),
              F(1, 100), "note", extra=(("precision", F(2, 3)),))
    rec = v.make_theorem_record(
        "T0-test", "deadbeef", "assumptions", "formula", "domain",
        10, 2, 9, [ce], "refuted", ["obligation"],
        [{"reading": "r", "verdict": "refuted"}],
    )
    assert json.loads(json.dumps(rec)) == rec
    smallest = rec["counterexamples"]["smallest"]
    assert smallest == rec["counterexamples"]["all"][0]
    assert smallest["e"] == "1/4" and smallest["precision"] == "2/3"


def test_verifier_grid_helpers():
    v = _load_verifier()
    lo, hi = v.window_bounds("k_over_k_plus_2", 5)
    assert (lo, hi) == (F(1, 6), F(5, 7))
    assert v.window_bounds("half", 7) == (F(1, 8), F(1, 2))
    pts = v.e_points(5)
    assert all(0 < p < 1 for p in pts)
    assert F(1, 6) + F(1, 100) in pts and F(1, 6) - F(1, 100) in pts
    # T7's p_min at a hand-checked point: e=1/4, r=1/2, k=5:
    # A = (1/4)(4/6) = 1/6, B = (3/4)(1/2)(6/4) = 9/16 -> p_min = 8/35.
    assert v.t7_p_min(F(1, 4), F(1, 2), 5) == F(8, 35)
    with pytest.raises(ZeroDivisionError):
        v.t7_p_min(F(1, 4), F(1, 2), 1)


# ---------------------------------------------------------------------------
# Input validation


def test_question_validation():
    with pytest.raises(ValueError):
        Question(3, (T, N), (N, N, N))
    with pytest.raises(TypeError):
        Question(2, (1, 0), (N, N))


def test_exact_parameters_reject_floats():
    with pytest.raises(TypeError):
        IndependentErrors(0.25)
    with pytest.raises(TypeError):
        HomogeneousCritic(0.5, F(0))
    with pytest.raises(ValueError):
        HomogeneousCritic(F(3, 2), F(0))
