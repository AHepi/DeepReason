"""Phase 3-4 forensic verification of the GLM judge-problem theory census.

Every executable claim in experiments/results/glm_judge_v1_theory_census.json
is tested against the exact model in deepreason.experiments.criticism_voting,
under the assumptions the census records for that artifact. Symbols are
artifact-local; no formula is merged across artifacts. Zero LLM tokens; all
exact results use fractions.Fraction, and the only floats are the mutual
information computations (logarithms), flagged as such.

Verdict vocabulary: verified_on_finite_domain (exhaustive domain, no
counterexample), refuted (explicit counterexample), under_specified,
simulation_supported_only, not_executable. Exhaustive agreement never
upgrades beyond verified_on_finite_domain; sampled agreement never upgrades
beyond simulation_supported_only.

Output: experiments/results/glm_judge_v1_theory_verification.json
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import combinations_with_replacement, product as iproduct
from math import comb
from pathlib import Path

from deepreason.experiments.criticism_voting import (
    TIE_RULES,
    AbstainIfAnyFlag,
    DifficultyMixture,
    HomogeneousCritic,
    IndependentErrors,
    MarginConditionalCritic,
    Question,
    RemoveAllFlagged,
    RemoveOneFlagged,
    broken,
    exact_metrics,
    outcome_after,
    outcome_before,
    population_eval,
    repaired,
    simulate_metrics,
)

CENSUS_PATH = Path("experiments/results/glm_judge_v1_theory_census.json")
OUT_PATH = Path("experiments/results/glm_judge_v1_theory_verification.json")

# Global grids. e runs on a 0.05 grid plus each window boundary +- 0.01.
K_GRID = (3, 5, 7, 9)
E_STEP = tuple(F(n, 20) for n in range(1, 20))
TPR_GRID = (F(0), F(1, 4), F(1, 2), F(3, 4), F(1))
FPR_GRID = (F(0), F(1, 20), F(1, 4), F(1, 2))
BOUNDARY_DELTA = F(1, 100)
MC_SEED = 20260714
MI_TOL = 1e-9

ONE = F(1)
HALF = F(1, 2)


# ---------------------------------------------------------------------------
# Windows and grid points


def window_bounds(name: str, k: int):
    lo = F(1, k + 1)
    if name == "k_over_k_plus_2":
        return lo, F(k, k + 2)
    if name == "k_over_k_plus_1":
        return lo, F(k, k + 1)
    if name == "half":
        return lo, HALF
    if name == "t13_band":
        return F(11, 20), F(3, 4)
    raise ValueError(name)


def relevant_boundaries(k: int):
    bs = {F(1, k + 1), F(k, k + 2), F(k, k + 1), HALF}
    if k == 5:
        bs |= {F(11, 20), F(3, 4)}
    return bs


def e_points(k: int):
    pts = set(E_STEP)
    for b in relevant_boundaries(k):
        for e in (b - BOUNDARY_DELTA, b + BOUNDARY_DELTA):
            if 0 < e < 1:
                pts.add(e)
    return tuple(sorted(pts))


def inside(e: F, lo: F, hi: F) -> bool:
    return lo < e < hi


def boundary_distance(e: F, k: int) -> F:
    return min(abs(e - b) for b in relevant_boundaries(k))


# ---------------------------------------------------------------------------
# Exact-cell cache


_CELLS: dict = {}


def cell(k, e, tpr, fpr, tie, policy="remove_all", err="iid"):
    key = (k, e, tpr, fpr, tie, policy, err)
    got = _CELLS.get(key)
    if got is not None:
        return got
    if err == "iid":
        em = IndependentErrors(e)
    elif err == "corr":
        # Mixture centered on e so the derived base error equals e exactly.
        em = DifficultyMixture(HALF, e + F(3, 20), e - F(3, 20))
    else:
        raise ValueError(err)
    pol = {"remove_all": RemoveAllFlagged(), "remove_one": RemoveOneFlagged()}[policy]
    m = exact_metrics(k, em, HomogeneousCritic(tpr, fpr), pol, tie, method="counts")
    _CELLS[key] = m
    return m


def scan(k_set, tie_rules=TIE_RULES, policy="remove_all", err="iid", e_filter=None):
    for k in k_set:
        for e in e_points(k):
            if e_filter is not None and not e_filter(e):
                continue
            for tpr in TPR_GRID:
                for fpr in FPR_GRID:
                    for tie in tie_rules:
                        yield k, e, tpr, fpr, tie, cell(k, e, tpr, fpr, tie, policy, err)


# ---------------------------------------------------------------------------
# Counterexample bookkeeping


def frac_s(x):
    if x is None:
        return None
    if isinstance(x, F):
        return str(x)
    if isinstance(x, float):
        return float(f"{x:.12g}")
    return x


@dataclass(frozen=True)
class CE:
    """One counterexample cell. distance is the grid distance of e to the
    nearest censused window boundary for that k (0 when e is not a model
    parameter of the counterexample)."""

    k: int
    e: F | None
    tpr: F | None
    fpr: F | None
    tie: str
    sc: F
    harness: F
    distance: F = F(0)
    note: str = ""
    extra: tuple = ()

    def sort_key(self):
        return (
            self.k,
            self.distance,
            self.e if self.e is not None else F(0),
            self.tpr if self.tpr is not None else F(0),
            self.fpr if self.fpr is not None else F(0),
            TIE_RULES.index(self.tie) if self.tie in TIE_RULES else len(TIE_RULES),
            self.note,
        )

    def to_json(self):
        d = {
            "k": self.k,
            "e": frac_s(self.e),
            "tpr": frac_s(self.tpr),
            "fpr": frac_s(self.fpr),
            "tie": self.tie,
            "sc": frac_s(self.sc),
            "harness": frac_s(self.harness),
            "grid_distance": frac_s(self.distance),
        }
        if self.note:
            d["note"] = self.note
        for key, val in self.extra:
            d[key] = frac_s(val)
        return d


def smallest_counterexample(ces):
    """Deterministic minimization: (k, grid distance, e, tpr, fpr, tie, note)."""
    if not ces:
        return None
    return min(ces, key=lambda c: c.sort_key())


def ce_block(ces):
    sm = smallest_counterexample(ces)
    return {
        "count": len(ces),
        "smallest": sm.to_json() if sm else None,
        "all": [c.to_json() for c in sorted(ces, key=lambda c: c.sort_key())],
    }


def make_theorem_record(
    theorem_id,
    artifact_id,
    assumptions,
    formula,
    domain,
    exhaustive_cases,
    simulation_cases,
    matched_cases,
    ces,
    verdict,
    obligations,
    interpretations=None,
):
    return {
        "theorem_id": theorem_id,
        "source_artifact_id": artifact_id,
        "formalized_assumptions": assumptions,
        "exact_formula": formula,
        "test_domain": domain,
        "exhaustive_cases_checked": exhaustive_cases,
        "simulation_cases_checked": simulation_cases,
        "matched_cases": matched_cases,
        "counterexamples": ce_block(ces),
        "verdict": verdict,
        "remaining_proof_obligations": obligations,
        "interpretations": interpretations or [],
    }


# ---------------------------------------------------------------------------
# Formula helpers (artifact-local; never merged across theorems)


def t7_p_min(e: F, r: F, k: int) -> F:
    a = e * F(k - 1, k + 1)
    b = (ONE - e) * r * F(k + 1, k - 1)
    return a / (a + b)


def strict(m) -> bool:
    return m.harness_accuracy > m.sc_accuracy


# ---------------------------------------------------------------------------
# Mutual information helpers (floats; the only non-Fraction arithmetic)


def _xlogx(x: float) -> float:
    return 0.0 if x <= 0.0 else x * math.log(x)


def per_candidate_mi(e: F, tpr: F, fpr: F) -> float:
    """I(flag; bad) for one candidate, natural log."""
    e_, t_, f_ = float(e), float(tpr), float(fpr)
    joint = {
        (1, 1): e_ * t_,
        (1, 0): e_ * (1 - t_),
        (0, 1): (1 - e_) * f_,
        (0, 0): (1 - e_) * (1 - f_),
    }
    pb = {1: e_, 0: 1 - e_}
    pf = {1: e_ * t_ + (1 - e_) * f_, 0: e_ * (1 - t_) + (1 - e_) * (1 - f_)}
    mi = 0.0
    for (b, fl), p in joint.items():
        if p > 0 and pb[b] > 0 and pf[fl] > 0:
            mi += p * math.log(p / (pb[b] * pf[fl]))
    return mi


def flag_pattern_majority_mi(k: int, e: F, tpr: F, fpr: F) -> float:
    """I(flag pattern; majority wrong) for odd k.

    By exchangeability every flag pattern with the same flag count has the
    same joint probability with the majority indicator, so the pattern MI
    equals I(flag count; majority wrong).
    """
    if k % 2 == 0:
        raise ValueError("odd k only")
    joint = {}
    for m, pm in IndependentErrors(e).wrong_count_dist(k).items():
        nc = k - m
        mwrong = 1 if m > nc else 0
        for fw in range(m + 1):
            pw = comb(m, fw) * tpr**fw * (ONE - tpr) ** (m - fw)
            for fc in range(nc + 1):
                pc = comb(nc, fc) * fpr**fc * (ONE - fpr) ** (nc - fc)
                w = pm * pw * pc
                if w:
                    j = fw + fc
                    joint[(j, mwrong)] = joint.get((j, mwrong), F(0)) + w
    pj: dict = {}
    pmw: dict = {}
    for (j, mw), p in joint.items():
        pj[j] = pj.get(j, F(0)) + p
        pmw[mw] = pmw.get(mw, F(0)) + p
    mi = 0.0
    for (j, mw), p in joint.items():
        pf, qf, rf = float(p), float(pj[j]), float(pmw[mw])
        if pf > 0 and qf > 0 and rf > 0:
            mi += pf * math.log(pf / (qf * rf))
    return mi


def binary_kl(a: F, b: F) -> float:
    a_, b_ = float(a), float(b)
    if b_ <= 0.0 or b_ >= 1.0:
        return math.inf
    return (
        _xlogx(a_)
        + _xlogx(1 - a_)
        - a_ * math.log(b_)
        - (1 - a_) * math.log(1 - b_)
    )


def fpr_from_precision(e: F, precision: F, recall: F):
    """Homogeneous-critic FPR implied by (e, precision, recall); None if > 1."""
    if precision == 0:
        return None
    fpr = recall * e * (ONE - precision) / (precision * (ONE - e))
    return fpr if 0 <= fpr <= 1 else None


# ---------------------------------------------------------------------------
# Experiment A: majority-fragility windows


def window_survey():
    """Per-window necessity/sufficiency raw survey over the full grid, plus
    sensitivity (correlated errors, remove_one) and k=15 Monte Carlo."""
    out = {}
    for name in ("k_over_k_plus_2", "k_over_k_plus_1", "half"):
        outside_beats = inside_nonbeats = cells = 0
        for k, e, tpr, fpr, tie, m in scan(K_GRID):
            cells += 1
            lo, hi = window_bounds(name, k)
            if strict(m) and not inside(e, lo, hi):
                outside_beats += 1
            if not strict(m) and inside(e, lo, hi):
                inside_nonbeats += 1
        corr = sum(
            1
            for k, e, tpr, fpr, tie, m in scan(
                (5, 7), ("incorrect",), "remove_all", "corr",
                e_filter=lambda e: F(1, 5) <= e <= F(4, 5) and e in E_STEP,
            )
            if strict(m) and not inside(e, *window_bounds(name, k))
        )
        r1 = sum(
            1
            for k, e, tpr, fpr, tie, m in scan((5, 7), ("incorrect",), "remove_one")
            if strict(m) and not inside(e, *window_bounds(name, k))
        )
        out[name] = {
            "cells": cells,
            "strict_beats_outside_window": outside_beats,
            "inside_window_cells_without_strict_beat": inside_nonbeats,
            "necessity_survives": outside_beats == 0,
            "sensitivity_correlated_outside_beats": corr,
            "sensitivity_remove_one_outside_beats": r1,
        }
    sims = []
    for e in (F(1, 20), F(3, 10), F(3, 5)):
        r = simulate_metrics(
            15, 40000, IndependentErrors(e), HomogeneousCritic(ONE, F(0)),
            RemoveAllFlagged(), "incorrect", MC_SEED,
        )
        sims.append(
            {
                "k": 15,
                "e": frac_s(e),
                "tpr": "1",
                "fpr": "0",
                "seed": MC_SEED,
                "n_questions": r["n_questions"],
                "sc_accuracy": frac_s(r["sc_accuracy"]),
                "harness_accuracy": frac_s(r["harness_accuracy"]),
                "strict_beat_observed": r["harness_accuracy"] > r["sc_accuracy"],
            }
        )
    out["monte_carlo_k15"] = {
        "note": "simulation only; supports at most simulation_supported_only",
        "runs": sims,
    }
    return out


def eval_window_necessity(window_name, k_set, gates):
    """Counterexamples to 'strict beat only if e in window AND gates'.

    gates(m, e, tpr, fpr) returns True when the artifact's critic-side
    conditions hold; a strict beat where the window or any gate fails is a
    counterexample to the necessity conjunction.
    """
    ces, checked = [], 0
    for k, e, tpr, fpr, tie, m in scan(k_set):
        checked += 1
        lo, hi = window_bounds(window_name, k)
        if strict(m) and not (inside(e, lo, hi) and gates(m, e, tpr, fpr)):
            note = "outside window" if not inside(e, lo, hi) else "gate violated"
            ces.append(
                CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                   boundary_distance(e, k), note,
                   extra=(("precision", m.precision),))
            )
    return ces, checked


def eval_sensitivity_necessity(window_name, gates):
    """Same necessity check under correlated errors and remove_one."""
    out = {}
    for label, policy, err, efilt in (
        ("correlated_errors", "remove_all", "corr",
         lambda e: F(1, 5) <= e <= F(4, 5) and e in E_STEP),
        ("remove_one_filtering", "remove_one", "iid", None),
    ):
        ces = []
        checked = 0
        for k, e, tpr, fpr, tie, m in scan((5, 7), ("incorrect",), policy, err, efilt):
            checked += 1
            lo, hi = window_bounds(window_name, k)
            if strict(m) and not (inside(e, lo, hi) and gates(m, e, tpr, fpr)):
                ces.append(
                    CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                       boundary_distance(e, k), label)
                )
        out[label] = {"cells": checked, "counterexamples": len(ces),
                      "smallest": (smallest_counterexample(ces).to_json() if ces else None)}
    return out


# ---------------------------------------------------------------------------
# Theorem evaluators


def theorem_S3():
    lo_k = [k for k in range(1, 1001) if not F(k, k + 2) < F(k, k + 1)]
    verdict = "verified_on_finite_domain" if not lo_k else "refuted"
    return make_theorem_record(
        "S3-window-nesting",
        "862de34bced36d488ac299f984c270812db349a12e50b3acf126462c0be93e72",
        "pure algebra; no model needed",
        "k/(k+2) < k/(k+1) for k > 0",
        "k in 1..1000, exact rationals",
        1000, 0, 1000 - len(lo_k), [], verdict,
        ["algebraic proof for all k > 0 (trivial, not machine-checked here)"],
    )


def theorem_S4():
    division_by_zero = False
    try:
        t7_p_min(F(1, 4), F(1, 2), 1)
    except ZeroDivisionError:
        division_by_zero = True
    return make_theorem_record(
        "S4-k1-degenerate-reduction",
        "3c2294e394226aa806195f042eefa03f1b3fa37d282a3ca7f54c6ce94eedae72",
        "claims p_min(e,r,k) collapses at k=1 to a pairwise veto tradeoff",
        "p_min(e,r,1) with p_min per T7: B-term divides by (k-1) = 0",
        "direct substitution k=1, e=1/4, r=1/2",
        1, 0, 0, [],
        "not_executable" if division_by_zero else "refuted",
        ["the reduction claim cannot be evaluated: T7's formula is undefined at k=1 "
         "(ZeroDivisionError confirmed); no alternative k=1 form is supplied"],
    )


def theorem_T1():
    k_set = (5, 7)
    ces, checked = [], 0
    for k, e, tpr, fpr, tie, m in scan(k_set):
        checked += 1
        if strict(m) and e <= HALF:
            ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                          abs(e - HALF), "strict beat with e <= 1/2"))
    interp = [
        {
            "reading": "candidate-removal semantics (census-endorsed enumerable reading)",
            "verdict": "refuted" if ces else "verified_on_finite_domain",
            "counterexamples": len(ces),
        },
        {
            "reading": "set-level veto semantics",
            "verdict": "under_specified",
            "counterexamples": 0,
            "note": "post-veto fallback answer undefined; not executable as stated",
        },
    ]
    return make_theorem_record(
        "T1-e-above-half",
        "5b4538abe4a712f8c9c0a33fe17fe62d43ac359f1375d97921d389955ef1f08a",
        "i.i.d. errors, homogeneous critic, remove_all_flagged, all tie rules, k in {5,7}",
        "strict beat only if e > 0.5 (second conjunct not executable at set level)",
        "k x e-grid x TPR x FPR x tie rules",
        checked, 0, checked - len(ces), ces,
        "refuted" if ces else "verified_on_finite_domain",
        ["set-level veto conjunct untested (fallback undefined)"],
        interp,
    )


def theorem_T2():
    # Set-level veto with confidence threshold tau. The artifact never says
    # what the harness answers after a veto. Both natural fallbacks make the
    # biconditional degenerate, so the claim is fallback-dependent.
    #  - fallback "keep SC answer": veto is a no-op; net = 0 for every tau.
    #  - fallback "score vetoed question wrong": vetoing a wrong-majority
    #    question changes nothing (already wrong) and vetoing a right-majority
    #    question loses it; net <= 0 for every tau.
    # Under either fallback, no tau yields positive net even when the wrong-
    # majority score distribution strictly first-order dominates.
    probes = [
        {
            "fallback": "keep SC answer",
            "dominant_score_model": "wrong scores {0.9,0.6}, right scores {0.4,0.1}, equal mass",
            "max_net_over_tau": "0",
        },
        {
            "fallback": "score vetoed question wrong",
            "dominant_score_model": "same",
            "max_net_over_tau": "0 (attained only at tau above all right-majority scores)",
        },
    ]
    return make_theorem_record(
        "T2-adaptive-threshold",
        "30e483eb494067d8323a796b7e319a77a3abce4c45ba08a487df2b6838e5082b",
        "set-level veto at confidence > tau; score distributions per majority class",
        "exists tau with positive expected net iff wrong-majority scores stochastically dominate",
        "two deterministic fallback probes (no seeded simulation needed: both are closed-form)",
        2, 0, 0, [],
        "under_specified",
        [
            "post-veto fallback answer undefined and decisive (probes: " + json.dumps(probes) + ")",
            "stochastic dominance order unspecified (assumed first-order)",
        ],
    )


def theorem_T3():
    pol = RemoveAllFlagged()
    ces = []
    checked = 0
    for k in (3, 5, 7):
        for correct in iproduct((True, False), repeat=k):
            nc = sum(correct)
            nw = k - nc
            for flags in iproduct((True, False), repeat=k):
                q = Question(k, correct, flags)
                fw = sum(1 for c, f in zip(correct, flags) if not c and f)
                fc = sum(1 for c, f in zip(correct, flags) if c and f)
                for tie in TIE_RULES:
                    checked += 1
                    b = outcome_before(q, tie)
                    a = outcome_after(q, pol, tie)
                    if b == 0:
                        pred_fix = fw > nw - nc
                        actual_fix = repaired(q, pol, tie)
                        if pred_fix != actual_fix:
                            ces.append(
                                CE(k, None, None, None, tie, b, a, F(0),
                                   f"fix rule mismatch: nc={nc} nw={nw} fc={fc} fw={fw} "
                                   f"predicted={pred_fix} actual={actual_fix}")
                            )
                    elif b == 1:
                        pred_no_break = fc < nc - nw
                        actual_no_break = not broken(q, pol, tie)
                        if pred_no_break != actual_no_break:
                            ces.append(
                                CE(k, None, None, None, tie, b, a, F(0),
                                   f"break rule mismatch: nc={nc} nw={nw} fc={fc} fw={fw} "
                                   f"predicted_no_break={pred_no_break} actual={actual_no_break}")
                            )
    return make_theorem_record(
        "T3-per-question-rates",
        "c9386a6c7b3038d7ebaf9f80aed2b6bfd17ad2be03ed64556d0173f0d0085495",
        "explicit flag vectors, remove_all_flagged, all tie rules; per-question rules "
        "evaluated on every realizable (correctness, flag) pair",
        "fix iff SC wrong and r_w*n_w > n_w-n_c; no break iff r_c*n_c < n_c-n_w",
        "all 4^k vector pairs, k in {3,5,7}, x 3 tie rules",
        checked, 0, checked - len(ces), ces,
        "refuted" if ces else "verified_on_finite_domain",
        ["the fix rule ignores same-question false flags; the break rule ignores "
         "same-question true flags; both directions produce mismatches"],
    )


def theorem_T4():
    k_set = (7, 9)
    readings = {
        "fragile_subset_precision": lambda m, e: (m.fragile_precision is not None
                                                  and m.fragile_precision > e),
        "global_precision": lambda m, e: (m.precision is not None and m.precision > e),
    }
    interp = []
    all_ces = []
    checked = 0
    for label, prec_ok in readings.items():
        ces = []
        n = 0
        gate_hits = 0
        for k, e, tpr, fpr, tie, m in scan(k_set):
            n += 1
            lo, hi = window_bounds("k_over_k_plus_2", k)
            if not (inside(e, lo, hi) and tpr > ONE - e and prec_ok(m, e)):
                continue
            gate_hits += 1
            if not strict(m):
                ces.append(
                    CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                       boundary_distance(e, k), f"sufficiency fails ({label})",
                       extra=(("precision", m.precision),
                              ("fragile_precision", m.fragile_precision)))
                )
        checked = n
        interp.append({
            "reading": label,
            "cells_with_all_gates_true": gate_hits,
            "counterexamples": len(ces),
            "verdict": "refuted" if ces else "verified_on_finite_domain",
        })
        all_ces.extend(ces)
    return make_theorem_record(
        "T4-window-k7-fragile-subset",
        "2d711b2eb5fff4e61cba262914dc9aa29cf142c91d43bf4fffdda495e76c90c4",
        "i.i.d. errors, homogeneous critic, remove_all_flagged, odd k in {7,9}; "
        "recall on the fragile subset equals TPR for a homogeneous critic",
        "1/(k+1) < e < k/(k+2) AND P > e AND R > 1-e (fragile subset) => strict beat",
        "k in {7,9} x e-grid x TPR x FPR x tie rules; both precision readings",
        checked * len(readings), 0, checked * len(readings) - len(all_ces), all_ces,
        "refuted" if all_ces else "verified_on_finite_domain",
        ["sufficiency outside the tested grids", "behavior of the critic off the "
         "fragile subset is unspecified by the artifact"],
        interp,
    )


def theorem_T5(sensitivity):
    def gates(m, e, tpr, fpr):
        return tpr > fpr and m.precision is not None and m.precision > HALF

    ces, checked = eval_window_necessity("k_over_k_plus_1", (5, 7, 9), gates)
    return make_theorem_record(
        "T5-window-wide",
        "7811dbda8316264703217e333840089b140aa9a640a7f195c385b88c8394d3dc",
        "i.i.d. errors, homogeneous critic, remove_all_flagged, odd k >= 5; "
        "recall_wrong = TPR, falseflag_rate_correct = FPR, precision_wrong = derived precision",
        "strict beat only if 1/(k+1) < e < k/(k+1) AND TPR > FPR AND precision > 1/2",
        "k in {5,7,9} x e-grid x TPR x FPR x tie rules; sensitivity: correlated errors, remove_one",
        checked, 0, checked - len(ces), ces,
        "refuted" if ces else "verified_on_finite_domain",
        ["necessity beyond the tested grids"],
        [{"reading": "necessity under sensitivity models", "results": sensitivity}],
    )


def theorem_T6():
    k_set = (3, 5, 7, 9)
    readings = {}
    all_ces = []
    checked = 0
    for label, swap in (("census_naming_F_broke_is_fragile_correct", False),
                        ("inverted_naming", True)):
        agree = disagree = 0
        ces = []
        n = 0
        for k, e, tpr, fpr, tie, m in scan(k_set):
            n += 1
            lo, hi = window_bounds("k_over_k_plus_2", k)
            f_broke = m.p_fragile_correct
            f_fixed = m.p_fragile_wrong
            if swap:
                f_broke, f_fixed = f_fixed, f_broke
            p, r = m.precision, tpr
            # p > (1-r)*F_broke/(r*F_fixed) cross-multiplied; false when no flags.
            thr_ok = p is not None and p * r * f_fixed > (ONE - r) * f_broke
            predicted = inside(e, lo, hi) and thr_ok
            actual = strict(m)
            if predicted == actual:
                agree += 1
            else:
                disagree += 1
                note = ("predicted beat, none observed" if predicted
                        else "unpredicted strict beat")
                ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                              boundary_distance(e, k), f"{label}: {note}",
                              extra=(("precision", p),
                                     ("F_broke", f_broke), ("F_fixed", f_fixed))))
        checked = n
        readings[label] = {
            "agreement_rate": frac_s(F(agree, agree + disagree)),
            "agree": agree,
            "disagree": disagree,
            "counterexamples": len(ces),
        }
        all_ces.extend(ces)
    better = max(readings, key=lambda lbl: F(readings[lbl]["agree"]))
    return make_theorem_record(
        "T6-realized-ratio-threshold",
        "e977c688ba005d3f8e9136e93656d8b5e72254470555b462a5c80e2954808770",
        "i.i.d. errors, homogeneous critic, remove_all_flagged; F_broke/F_fixed read as "
        "expected per-question counts of margin-1 fragile-correct / fragile-wrong "
        "majorities pre-filter (census naming), plus the inverted reading",
        "strict beat iff 1/(k+1) < e < k/(k+2) AND p > (1-r)*F_broke/(r*F_fixed)",
        "k in {3,5,7,9} x e-grid x TPR x FPR x tie rules; both naming readings",
        checked * 2, 0, checked * 2 - len(all_ces), all_ces,
        "refuted" if all_ces else "verified_on_finite_domain",
        ["threshold as a realization-level (not expectation-level) quantity"],
        [{"reading": lbl, **stats} for lbl, stats in readings.items()]
        + [{"reading_comparison": f"higher agreement: {better}"}],
    )


def theorem_T7(equal_precision_pairs):
    k_set = (5, 7, 9)
    ces = []
    checked = agree = 0
    sign_table = {}
    inside_agree = inside_total = 0
    for k, e, tpr, fpr, tie, m in scan(k_set):
        if tpr == 0:
            continue
        checked += 1
        lo, hi = window_bounds("k_over_k_plus_2", k)
        p = m.precision
        pm = t7_p_min(e, tpr, k)
        predicted = inside(e, lo, hi) and p is not None and p > pm
        actual = strict(m)
        if inside(e, lo, hi) and p is not None:
            inside_total += 1
            s_net = (m.net > 0) - (m.net < 0)
            s_thr = (p > pm) - (p < pm)
            sign_table[f"net{s_net:+d}_thr{s_thr:+d}"] = (
                sign_table.get(f"net{s_net:+d}_thr{s_thr:+d}", 0) + 1
            )
            if s_net == s_thr:
                inside_agree += 1
        if predicted == actual:
            agree += 1
        else:
            note = "predicted beat, none observed" if predicted else "unpredicted strict beat"
            ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                          boundary_distance(e, k), note,
                          extra=(("precision", p), ("p_min", pm))))
    return make_theorem_record(
        "T7-pmin-closed-form",
        "edc14bbd1ae6e3cc76eea0f6db2966a0dbe1446bf6b7655bbafce61f46750f45",
        "i.i.d. binomial errors, homogeneous critic, remove_all_flagged, odd k >= 5; "
        "r = TPR, p = derived global precision",
        "strict beat iff 1/(k+1) < e < k/(k+2) AND p > p_min(e,r,k), "
        "p_min = A/(A+B), A = e(k-1)/(k+1), B = (1-e)r(k+1)/(k-1)",
        "k in {5,7,9} x e-grid x TPR>0 x FPR x tie rules",
        checked, 0, agree, ces,
        "refuted" if ces else "verified_on_finite_domain",
        ["whether any (e,P,R,k) threshold can be exact (see Experiment C: none can)"],
        [
            {"reading": "biconditional over full grid",
             "agreement_rate": frac_s(F(agree, checked)), "counterexamples": len(ces)},
            {"reading": "inside-window sign(harness-SC) vs sign(p-p_min)",
             "cells": inside_total,
             "sign_agreement_rate": frac_s(F(inside_agree, inside_total)) if inside_total else None,
             "sign_table": sign_table},
            {"reading": "equal precision, different FPR (flag prevalence)",
             "results": equal_precision_pairs},
        ],
    )


def experiment_B_equal_precision_pairs():
    pairs = []
    status_changed = False
    for k in (5, 7):
        for e in (F(1, 4), F(3, 10)):
            for p_target in (HALF, F(7, 10)):
                tpr_a = F(2, 5)
                fpr_a = fpr_from_precision(e, p_target, tpr_a)
                if fpr_a is None:
                    continue
                tpr_b, fpr_b = 2 * tpr_a, 2 * fpr_a
                if fpr_b > 1 or tpr_b > 1:
                    continue
                ma = cell(k, e, tpr_a, fpr_a, "incorrect")
                mb = cell(k, e, tpr_b, fpr_b, "incorrect")
                assert ma.precision == p_target and mb.precision == p_target
                sa, sb = strict(ma), strict(mb)
                if sa != sb:
                    status_changed = True
                pairs.append({
                    "k": k, "e": frac_s(e), "precision": frac_s(p_target),
                    "critic_a": {"tpr": frac_s(tpr_a), "fpr": frac_s(fpr_a),
                                 "strict_beat": sa, "net": frac_s(ma.net)},
                    "critic_b": {"tpr": frac_s(tpr_b), "fpr": frac_s(fpr_b),
                                 "strict_beat": sb, "net": frac_s(mb.net)},
                    "strict_beat_status_differs": sa != sb,
                })
    return {
        "construction": "same (k, e, global precision); flag prevalence doubled, so "
                        "recall and FPR double while precision is held fixed",
        "pairs": pairs,
        "precision_alone_insufficient": status_changed,
    }


def theorem_T8(sensitivity):
    k_set = (3, 5, 7)
    ces = []
    checked = 0
    kinds = {"window_necessity": 0, "precision_necessity": 0,
             "recall_necessity": 0, "joint_sufficiency": 0}
    for k, e, tpr, fpr, tie, m in scan(k_set):
        checked += 1
        lo, hi = window_bounds("half", k)
        p = m.precision
        if strict(m):
            if not inside(e, lo, hi):
                kinds["window_necessity"] += 1
                ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                              boundary_distance(e, k), "strict beat outside window"))
            if p is not None and p < HALF:
                kinds["precision_necessity"] += 1
                ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                              boundary_distance(e, k), "strict beat with P < 1/2",
                              extra=(("precision", p),)))
            if tpr == 0:
                kinds["recall_necessity"] += 1
                ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                              boundary_distance(e, k), "strict beat with R = 0"))
        else:
            if inside(e, lo, hi) and tpr > 0 and p is not None and p >= HALF:
                kinds["joint_sufficiency"] += 1
                ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                              boundary_distance(e, k), "joint sufficiency fails",
                              extra=(("precision", p),)))
    return make_theorem_record(
        "T8-three-condition-iff",
        "3a28bc3e8bde28be2af04bc4e23b5753948be3c6b53c7580e5edbc8fceab68da",
        "i.i.d. errors, homogeneous critic, remove_all_flagged, odd k in {3,5,7}",
        "strict beat iff 1/(k+1) < e < 1/2 AND P >= 1/2 AND R > 0 "
        "(each conjunct claimed individually necessary, jointly sufficient)",
        "k in {3,5,7} x e-grid x TPR x FPR x tie rules; sensitivity models",
        checked, 0, checked - len(ces), ces,
        "refuted" if ces else "verified_on_finite_domain",
        [],
        [{"reading": "violations by conjunct", "counts": kinds},
         {"reading": "necessity under sensitivity models", "results": sensitivity}],
    )


def theorem_T9(sensitivity):
    k_set = (3, 5, 7, 9)
    ces = []
    checked = 0
    loss_ces = []
    for k, e, tpr, fpr, tie, m in scan(k_set):
        checked += 1
        lo, hi = window_bounds("half", k)
        p = m.precision
        if strict(m) and not (inside(e, lo, hi) and p is not None and p > HALF and tpr > 0):
            ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                          boundary_distance(e, k), "iff necessity direction fails",
                          extra=(("precision", p),)))
        if (not strict(m)) and inside(e, lo, hi) and tpr > 0 and p is not None and p > HALF:
            ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                          boundary_distance(e, k), "iff sufficiency direction fails",
                          extra=(("precision", p),)))
        # Strict-loss branch: P < 1/2 => harness strictly below SC (expectation
        # reading, tested inside the artifact's window).
        if inside(e, lo, hi) and p is not None and p < HALF and m.net >= 0:
            loss_ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                               boundary_distance(e, k), "P < 1/2 without strict loss",
                               extra=(("precision", p), ("net", m.net))))
    # Realization-level no-op counterexample to the loss branch: one false
    # flag on a robust correct pool; realized precision 0 < 1/2, harness == SC.
    q = Question(5, (True,) * 5, (True, False, False, False, False))
    noop = population_eval([q], RemoveAllFlagged(), "incorrect")
    realization = {
        "question": {"correct": [1] * 5, "flags": [1, 0, 0, 0, 0]},
        "realized_precision": frac_s(noop["aggregates"]["precision"]),
        "sc": frac_s(noop["sc_correct"]),
        "harness": frac_s(noop["harness_correct"]),
        "strict_loss": bool(noop["net"] < 0),
    }
    all_ces = ces + loss_ces
    return make_theorem_record(
        "T9-three-condition-iff-with-loss",
        "6389657ce9643a2bea111796be310dfa94f7021c8ae323bb7345b5431b9de029",
        "i.i.d. errors, homogeneous critic, remove_all_flagged, odd k",
        "strict beat iff window AND P > 1/2 AND R > 0; P < 1/2 => strict loss",
        "k in {3,5,7,9} x e-grid x TPR x FPR x tie rules",
        checked, 0, checked - len(all_ces), all_ces,
        "refuted" if all_ces else "verified_on_finite_domain",
        ["loss-branch quantifier (always vs in expectation) unspecified; both readings refuted"],
        [
            {"reading": "biconditional", "counterexamples": len(ces)},
            {"reading": "strict-loss branch, expectation reading",
             "counterexamples": len(loss_ces)},
            {"reading": "strict-loss branch, realization reading (no-op false flag)",
             "worked_example": realization,
             "verdict": "refuted" if not realization["strict_loss"] else "verified_on_finite_domain"},
            {"reading": "necessity under sensitivity models", "results": sensitivity},
        ],
    )


def theorem_T11():
    k_set = (3, 5, 7, 9)
    exp_ces = []
    checked = 0
    for k, e, tpr, fpr, tie, m in scan(k_set):
        if fpr != 0 or tpr == 0:
            continue
        checked += 1
        if not strict(m):
            exp_ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy, m.harness_accuracy,
                              boundary_distance(e, k), "P=1, R>0 without strict beat"))
    # Realization reading: >=1 broken-majority item with >=1 flagged error
    # must yield strictly positive net. Partial removal that leaves the wrong
    # answer winning (or tied) is the censused gap.
    real_ces = []
    examples = []
    for correct, flags, label in (
        ((True, True, False, False, False), (False, False, True, False, False),
         "3-2 broken majority, one flagged error, post-filter 2-2 tie"),
        ((True, False, False, False, False), (False, True, False, False, False),
         "4-1 broken majority, one flagged error, still wrong after removal"),
    ):
        q = Question(5, correct, flags)
        for tie in TIE_RULES:
            r = population_eval([q], RemoveAllFlagged(), tie)
            if not r["net"] > 0:
                real_ces.append(CE(5, None, None, None, tie,
                                   r["sc_correct"], r["harness_correct"], F(0),
                                   f"realization: {label}"))
        examples.append({"correct": [int(c) for c in correct],
                         "flags": [int(f) for f in flags], "case": label})
    interp = [
        {"reading": "expectation reading (FPR=0, TPR>0, any e in (0,1))",
         "cells": checked, "counterexamples": len(exp_ces),
         "verdict": "refuted" if exp_ces else "verified_on_finite_domain",
         "note": "contradicts window necessity of T5/T8/T9 wherever it holds"},
        {"reading": "realization reading (census proposed inequality, as stated)",
         "worked_examples": examples, "counterexamples": len(real_ces),
         "verdict": "refuted" if real_ces else "verified_on_finite_domain"},
    ]
    return make_theorem_record(
        "T11-perfect-precision-tail",
        "92918f72767b73347fd0a1ddcddf0741e94701bf80b2fb4df588f1f06e66e5f3",
        "i.i.d. errors, homogeneous critic with FPR=0 (P=1), remove_all_flagged",
        "P = 1 AND R > 0 AND >=1 broken-majority item with >=1 flagged error "
        "=> strictly positive net",
        "expectation reading on the FPR=0 grid column; realization reading on "
        "explicit vectors, all tie rules",
        checked + len(TIE_RULES) * 2, 0,
        checked - len(exp_ces) + len(TIE_RULES) * 2 - len(real_ces),
        exp_ces + real_ces,
        "refuted" if real_ces else ("refuted" if exp_ces else "verified_on_finite_domain"),
        ["the expectation reading's strict beat outside every censused window is "
         "itself established here on the finite grid only"],
        interp,
    )


def theorem_T12():
    ces = []
    checked = agree = 0
    for k in (3, 5):
        for e in (F(1, 10), F(3, 10), F(1, 2), F(7, 10), F(9, 10)):
            for tpr in (F(3, 10), F(3, 5), F(9, 10), ONE):
                for fpr in (F(0), F(1, 10), F(3, 10)):
                    checked += 1
                    i_cb = k * per_candidate_mi(e, tpr, fpr)
                    i_cm = flag_pattern_majority_mi(k, e, tpr, fpr)
                    m = cell(k, e, tpr, fpr, "incorrect")
                    predicted = i_cb > i_cm + MI_TOL
                    actual = strict(m)
                    robust = abs(i_cb - i_cm) > MI_TOL
                    if predicted == actual:
                        agree += 1
                    elif robust:
                        note = ("MI predicts beat, none observed" if predicted
                                else "strict beat without MI dominance")
                        ces.append(CE(k, e, tpr, fpr, "incorrect",
                                      m.sc_accuracy, m.harness_accuracy,
                                      boundary_distance(e, k), note,
                                      extra=(("I_CB", i_cb), ("I_CM", i_cm))))
    return make_theorem_record(
        "T12-mutual-information",
        "88f00f0d4243bf6a2e3c1acf713d99a20e752bd30cafb420aaf8f8a523da604d",
        "i.i.d. errors, homogeneous critic, remove_all_flagged, tie rule incorrect; "
        "I(C;B) = k * per-candidate MI (flags conditionally independent); "
        "I(C;M_wrong) = I(flag count; majority wrong) by exchangeability; "
        "MI in floats (natural log), tolerance 1e-9",
        "strict beat iff I(C;B) > I(C;M_wrong)",
        "k in {3,5} x 5 e-points x 4 TPR x 3 FPR",
        checked, 0, agree, ces,
        "refuted" if ces else "verified_on_finite_domain",
        ["MI values are float-computed; every persisted counterexample has "
         "|I_CB - I_CM| > 1e-9", "the iff over arbitrary flag-dependence "
         "structures is untested (exchangeable critics only)"],
    )


def theorem_T13(sensitivity):
    def gates(m, e, tpr, fpr):
        return (tpr > F(7, 10) and m.precision is not None
                and m.precision > F(3, 10))

    ces, checked = eval_window_necessity("t13_band", (5,), gates)
    # Loss claim: psi < 0.2 with SC right => strict loss. Committed
    # expectation reading: e <= 1/2 (SC majority typically right), derived
    # precision < 1/5, expect net < 0.
    loss_ces = []
    loss_checked = 0
    for k, e, tpr, fpr, tie, m in scan((5,)):
        p = m.precision
        if e <= HALF and p is not None and p < F(1, 5):
            loss_checked += 1
            if m.net >= 0:
                loss_ces.append(CE(k, e, tpr, fpr, tie, m.sc_accuracy,
                                   m.harness_accuracy, boundary_distance(e, k),
                                   "psi < 0.2 without strict loss",
                                   extra=(("precision", p),)))
    all_ces = ces + loss_ces
    return make_theorem_record(
        "T13-high-error-band",
        "dea717ccf1eaefe5b8c4a898bf54bc124534ccb5768439bedef3f2f4157b5192",
        "i.i.d. errors, homogeneous critic, remove_all_flagged, k=5; p (base error) "
        "is artifact-local and distinct from other artifacts' p (precision)",
        "strict win only if 0.55 < e < 0.75 AND phi > 0.7 AND psi > 0.3; "
        "strict loss when psi < 0.2 and SC was right",
        "k=5 x e-grid (with 0.55/0.75 +- 0.01) x TPR x FPR x tie rules",
        checked + loss_checked, 0,
        checked - len(ces) + loss_checked - len(loss_ces), all_ces,
        "refuted" if all_ces else "verified_on_finite_domain",
        ["band constants stated 'roughly'; boundary +-0.01 points included",
         "loss-claim scope committed as e <= 1/2 (SC-right in expectation)"],
        [{"reading": "band necessity", "counterexamples": len(ces)},
         {"reading": "strict-loss claim (expectation, e <= 1/2)",
          "cells": loss_checked, "counterexamples": len(loss_ces)},
         {"reading": "necessity under sensitivity models", "results": sensitivity}],
    )


def theorem_S5():
    ces = []
    checked = 0
    truth_varies_with_pr = []
    for k in (7, 9):
        lo, hi = window_bounds("k_over_k_plus_2", k)
        for e in e_points(k):
            truths = set()
            for dp in (F(1, 10), F(3, 10)):
                p = min(e + dp, F(19, 20))
                if not p > e:
                    continue
                for r in (min(ONE, ONE - e + F(1, 20)), ONE):
                    if not r > ONE - e:
                        continue
                    fpr = fpr_from_precision(e, p, r)
                    if fpr is None:
                        continue
                    checked += 1
                    i_cb = k * per_candidate_mi(e, r, fpr)
                    i_cm = flag_pattern_majority_mi(k, e, r, fpr)
                    mi_truth = i_cb > i_cm + MI_TOL
                    truths.add(mi_truth)
                    if mi_truth != inside(e, lo, hi) and abs(i_cb - i_cm) > MI_TOL:
                        ces.append(CE(k, e, r, fpr, "incorrect", F(0), F(0),
                                      boundary_distance(e, k),
                                      "MI inequality truth != window membership",
                                      extra=(("precision", p), ("I_CB", i_cb),
                                             ("I_CM", i_cm))))
            if len(truths) > 1:
                truth_varies_with_pr.append({"k": k, "e": frac_s(e)})
    return make_theorem_record(
        "S5-MI-collapse-claim",
        "457a95bed9d3969f3ee5cd1388138a3078cb2461b90a1519d879af07a77a7b1f",
        "i.i.d. Bernoulli(e) errors; flags conditionally independent with "
        "precision P > e and recall R > 1-e; MI in floats, tolerance 1e-9",
        "I(C;B) > I(C;M_wrong) evaluates to exactly 1/(k+1) < e < k/(k+2), odd k >= 7",
        "k in {7,9} x e-grid x (P,R) satisfying the stated gates",
        checked, 0, checked - len(ces), ces,
        "refuted" if ces else "verified_on_finite_domain",
        ["artifact is suspended_unsupported in the census (parent T12 refuted)",
         f"MI truth value varies with (P,R) at fixed e in {len(truth_varies_with_pr)} "
         "e-points, so no P,R-free interval can be exact"],
        [{"reading": "e-points where MI truth depends on (P,R)",
          "points": truth_varies_with_pr[:20], "count": len(truth_varies_with_pr)}],
    )


def theorem_S6():
    mismatches = []
    checked = 0
    for e in (F(1, 10), F(1, 4), F(2, 5)):
        for p in (F(1, 2), F(7, 10), F(9, 10)):
            for r in (F(7, 10), F(9, 10), ONE):
                fpr = fpr_from_precision(e, p, r)
                if fpr is None:
                    continue
                checked += 1
                true_mi = per_candidate_mi(e, r, fpr)
                stated = float(e) * binary_kl(p, e) + (1 - float(e)) * binary_kl(r, ONE - e)
                if not math.isfinite(stated) or abs(true_mi - stated) > MI_TOL:
                    mismatches.append({
                        "e": frac_s(e), "P": frac_s(p), "R": frac_s(r),
                        "true_per_candidate_MI": frac_s(true_mi),
                        "stated_decomposition": ("inf" if not math.isfinite(stated)
                                                 else frac_s(stated)),
                    })
    return make_theorem_record(
        "S6-MI-specialization-formula",
        "a6806e68a370426a7c681b87ae20a5578788b756795fd67f8f840a411c2a656b",
        "binary-error/binary-flag model; stated decomposition "
        "I = e*D(P||e) + (1-e)*D(R||1-e) compared against the true per-candidate MI",
        "P > e and R > 1-e is the specialization of I(C;B) > I(C;M_wrong)",
        "9-point (e,P,R) grid (skipping infeasible FPR)",
        checked, 0, checked - len(mismatches), [],
        "under_specified",
        ["artifact formula is truncated in the emission and suspended_unsupported",
         f"the stated decomposition disagrees with the true MI in {len(mismatches)} "
         f"of {checked} tested points (KL applied to a precision and a base rate "
         "is dimensionally inconsistent); recorded as evidence, not a refutation "
         "of the truncated original",
         "sample mismatches: " + json.dumps(mismatches[:3])],
    )


# ---------------------------------------------------------------------------
# Experiment C: identical aggregates, opposite outcomes (T10, primary hypothesis)


def _question_delta(c: int, fc: int, fw: int) -> int:
    # k=5, tie rule incorrect, remove_all_flagged; delta in {-1, 0, 1}.
    w = 5 - c
    before = 1 if c > w else 0
    after = 1 if (c - fc) > (w - fw) else 0
    return after - before


def _build_questions(pop, alloc):
    qs = []
    for c, (fc, fw) in zip(pop, alloc):
        w = 5 - c
        correct = (True,) * c + (False,) * w
        flags = tuple([i < fc for i in range(c)] + [i < fw for i in range(w)])
        qs.append(Question(5, correct, flags))
    return qs


def run_experiment_C():
    levels = []
    best = None
    for n in range(2, 7):
        pops = list(combinations_with_replacement(range(6), n))
        found = []
        for pop in pops:
            dp = {(0, 0): (0, (), 0, ())}
            for c in pop:
                w = 5 - c
                opts = [(fc, fw, _question_delta(c, fc, fw))
                        for fc in range(c + 1) for fw in range(w + 1)]
                ndp: dict = {}
                for (tp, fp), (mn, ma, mx, xa) in sorted(dp.items()):
                    for fc, fw, d in opts:
                        key = (tp + fw, fp + fc)
                        cur = ndp.get(key)
                        lo_v, lo_a = mn + d, ma + ((fc, fw),)
                        hi_v, hi_a = mx + d, xa + ((fc, fw),)
                        if cur is None:
                            ndp[key] = [lo_v, lo_a, hi_v, hi_a]
                        else:
                            if lo_v < cur[0] or (lo_v == cur[0] and lo_a < cur[1]):
                                cur[0], cur[1] = lo_v, lo_a
                            if hi_v > cur[2] or (hi_v == cur[2] and hi_a < cur[3]):
                                cur[2], cur[3] = hi_v, hi_a
                dp = {key: tuple(v) for key, v in ndp.items()}
            for (tp, fp) in sorted(dp):
                mn, ma, mx, xa = dp[(tp, fp)]
                if mx > 0 and mn < 0:
                    found.append((tp + fp, tp, fp, pop, xa, ma))
        levels.append({"n_questions": n, "populations_scanned": len(pops),
                       "opposite_sign_pairs_found": len(found)})
        if found:
            found.sort()
            best = (n,) + found[0]
            break
    result = {
        "search": "k=5, tie rule incorrect, remove_all_flagged; populations are "
                  "multisets of per-question correct counts, sizes 2..6 ascending; "
                  "flag allocations enumerated exhaustively via per-question "
                  "(false flags, true flags) counts; identical aggregates enforced "
                  "by equal (total TP, total FP) on the same candidate population",
        "levels": levels,
        "found": best is not None,
    }
    if best is None:
        result["conclusion"] = "no opposite-sign pair with identical aggregates found"
        return result
    n, total_flags, tp, fp, pop, alloc_pos, alloc_neg = best
    qx = _build_questions(pop, alloc_pos)
    qy = _build_questions(pop, alloc_neg)
    rx = population_eval(qx, RemoveAllFlagged(), "incorrect")
    ry = population_eval(qy, RemoveAllFlagged(), "incorrect")
    ax, ay = rx["aggregates"], ry["aggregates"]
    for key in ("precision", "recall", "fpr", "base_error", "tp", "fp"):
        assert ax[key] == ay[key], (key, ax[key], ay[key])
    assert rx["net"] > 0 > ry["net"], (rx["net"], ry["net"])
    result["worked_example"] = {
        "n_questions": n,
        "k": 5,
        "population_correct_counts": list(pop),
        "shared_aggregates": {
            "base_error": frac_s(ax["base_error"]),
            "precision": frac_s(ax["precision"]),
            "recall": frac_s(ax["recall"]),
            "fpr": frac_s(ax["fpr"]),
            "tp": ax["tp"], "fp": ax["fp"],
        },
        "critic_X_improves": {
            "questions": [{"correct": [int(c) for c in q.correct],
                           "flags": [int(f) for f in q.flags],
                           "before": frac_s(pq["before"]),
                           "after": frac_s(pq["after"])}
                          for q, pq in zip(qx, rx["per_question"])],
            "sc_correct": frac_s(rx["sc_correct"]),
            "harness_correct": frac_s(rx["harness_correct"]),
            "net": frac_s(rx["net"]),
        },
        "critic_Y_worsens": {
            "questions": [{"correct": [int(c) for c in q.correct],
                           "flags": [int(f) for f in q.flags],
                           "before": frac_s(pq["before"]),
                           "after": frac_s(pq["after"])}
                          for q, pq in zip(qy, ry["per_question"])],
            "sc_correct": frac_s(ry["sc_correct"]),
            "harness_correct": frac_s(ry["harness_correct"]),
            "net": frac_s(ry["net"]),
        },
    }
    result["conclusion"] = (
        "two flag allocations with identical (base error, precision, recall, FPR, k) "
        "on the identical candidate population produce strictly opposite harness-vs-SC "
        "signs; no universal rule on (e, P, R, k) can decide the sign"
    )
    return result


def theorem_T10(exp_c):
    found = exp_c["found"]
    checked = sum(lvl["populations_scanned"] for lvl in exp_c["levels"])
    return make_theorem_record(
        "T10-no-fixed-tuple",
        "44c4273f5c5a9b2b39d6bcf3615259073155ac7d8a44c8f8c281d48c415dbc3e",
        "explicit two-population construction, k=5, tie rule incorrect, "
        "remove_all_flagged; aggregates derived from realized vectors",
        "exists two settings with identical (e, P, R, k) and opposite "
        "harness-vs-SC signs",
        "exhaustive DP over flag allocations on populations of 2..6 questions "
        "(stopped at the smallest size containing a witness)",
        checked, 0, checked, [],
        "verified_on_finite_domain" if found else "refuted",
        ["existence established by explicit witness (Experiment C); the stronger "
         "per-item-calibration sufficiency prose is not formalized in the census "
         "inequality and remains untested"],
        [{"reading": "witness", "summary": exp_c.get("conclusion")}],
    )


# ---------------------------------------------------------------------------
# Experiment D: sufficient conditional statistics


def _class_conditional_rates(k, e, critic, right_class: bool):
    num_t = den_t = num_f = den_f = F(0)
    for m, pm in IndependentErrors(e).wrong_count_dist(k).items():
        nc = k - m
        if (nc > m) != right_class:
            continue
        t, f = critic.rates_for_counts(nc, m)
        num_t += pm * m * t
        den_t += pm * m
        num_f += pm * nc * f
        den_f += pm * nc
    return (num_t / den_t if den_t else None, num_f / den_f if den_f else None)


def run_experiment_D():
    k = 5
    tie = "incorrect"
    pol = RemoveAllFlagged()
    base_t, base_f = F(3, 5), F(1, 5)
    uniform = HomogeneousCritic(base_t, base_f)
    cases = []
    insufficient = False
    for e in (F(1, 4), F(2, 5)):
        dist = IndependentErrors(e).wrong_count_dist(k)
        # Correct-class margins +1,+3,+5 correspond to c = 3,4,5.
        w_mass = {c: dist[k - c] * (k - c) for c in (3, 4, 5)}
        c_mass = {c: dist[k - c] * c for c in (3, 4, 5)}
        # Raise the margin-1 rates and lower the rest, preserving the class-
        # conditional expectation; the skew is half the largest feasible one.
        w1, w_rest = w_mass[3], w_mass[4] + w_mass[5]
        d_t = min(ONE - base_t, base_t * w_rest / w1) / 2
        t1 = base_t + d_t
        t_rest = base_t - d_t * w1 / w_rest
        c1, c_rest = c_mass[3], c_mass[4] + c_mass[5]
        d_f = min(ONE - base_f, base_f * c_rest / c1) / 2
        f1 = base_f + d_f
        f_rest = base_f - d_f * c1 / c_rest
        assert 0 < d_t and 0 < d_f, (d_t, d_f)
        assert 0 <= t_rest <= 1 and 0 <= f_rest <= 1, (t_rest, f_rest)
        skewed = MarginConditionalCritic(
            default=(base_t, base_f),
            overrides=((1, t1, f1), (3, t_rest, f_rest), (5, t_rest, f_rest)),
        )
        for right_class in (True, False):
            ru = _class_conditional_rates(k, e, uniform, right_class)
            rs = _class_conditional_rates(k, e, skewed, right_class)
            assert ru == rs, (right_class, ru, rs)
        em = IndependentErrors(e)
        mu = exact_metrics(k, em, uniform, pol, tie)
        ms = exact_metrics(k, em, skewed, pol, tie)
        # Determinism of the exact evaluator: identical inputs, identical output.
        assert ms == exact_metrics(k, em, skewed, pol, tie)
        differs = mu.net != ms.net
        insufficient = insufficient or differs
        cases.append({
            "e": frac_s(e),
            "class_conditional_TPR_FPR": {
                "right_class": [frac_s(x) for x in _class_conditional_rates(k, e, uniform, True)],
                "wrong_class": [frac_s(x) for x in _class_conditional_rates(k, e, uniform, False)],
            },
            "uniform_critic_net": frac_s(mu.net),
            "margin_skewed_critic_net": frac_s(ms.net),
            "net_benefit_differs": differs,
            "skewed_rates": {"margin_1": [frac_s(t1), frac_s(f1)],
                             "margin_3_and_5": [frac_s(t_rest), frac_s(f_rest)]},
        })
    return {
        "k": k,
        "tie_rule": tie,
        "construction": "margin-conditional critic whose class-conditional expected "
                        "(TPR, FPR) equal the uniform critic's on both majority-"
                        "correctness classes, but whose FPR concentrates on the "
                        "fragile (margin +1) pools",
        "cases": cases,
        "four_tuple_sufficient": not insufficient,
        "smallest_sufficient_statistic_found": (
            "the per-signed-margin (TPR, FPR) profile together with the error-count "
            "distribution; within the exchangeable model class this determines every "
            "reported expectation by construction of the count-based evaluator"
        ),
        "caveat": "sufficiency is claimed only WITHIN the tested exchangeable model "
                  "class; nothing is claimed for critics with within-pool, "
                  "position-dependent, or cross-question flag dependence",
    }


def theorem_S1():
    return make_theorem_record(
        "S1-subsumption-chain",
        "5597507043f5427f7073b4c80fe87419bbf3b32c9207ae3f808100790dd11909",
        "structural meta-claim about artifact subsumption; no model mapping exists",
        "8e9b8d5285aa is the base case generalized by T2 then T3",
        "none",
        0, 0, 0, [],
        "not_executable",
        ["claim is about artifact relationships; its base artifact is structurally "
         "invalid per the census, so there is no mathematical content to execute"],
    )


def theorem_S2(t4_record):
    t4_refuted = t4_record["verdict"] == "refuted"
    nesting_ok = all(F(k, k + 2) < F(k, k + 1) for k in range(1, 1001))
    verdict = "refuted" if (nesting_ok and t4_refuted) else (
        "verified_on_finite_domain" if nesting_ok else "refuted")
    return make_theorem_record(
        "S2-T5-weakens-T4",
        "324c6fa9540384cf3fc3f2e3aa2a22bf6716654413b5a55a0c38f37ce7883040",
        "window nesting is pure algebra; the claim additionally asserts T4's "
        "P > e / R > 1-e gate is genuinely sufficient, which inherits T4's verdict",
        "window(T4) subset window(T5); T4's gates sufficient for strict beat",
        "algebra k in 1..1000 plus T4's grid",
        1000 + t4_record["exhaustive_cases_checked"], 0,
        1000, [],
        verdict,
        ["nesting part holds exactly (k in 1..1000); the claim's own REFUTED-IF "
         "condition fires because T4's sufficiency gate fails on the tested grid "
         "(see T4-window-k7-fragile-subset counterexamples)"],
        [{"reading": "window nesting", "verdict": "verified_on_finite_domain"},
         {"reading": "T4 gates genuinely sufficient",
          "verdict": "refuted" if t4_refuted else "verified_on_finite_domain"}],
    )


# ---------------------------------------------------------------------------
# Cross-checks and main


def cross_check_counts_vs_full():
    checks = []
    for k, e, tpr, fpr, tie in ((3, F(1, 4), F(3, 4), F(1, 10), "incorrect"),
                                (5, F(2, 5), F(1, 2), F(1, 4), "random"),
                                (4, F(3, 10), F(3, 5), F(1, 20), "unchanged")):
        em = IndependentErrors(e)
        cr = HomogeneousCritic(tpr, fpr)
        for pol_name, pol in (("remove_all", RemoveAllFlagged()),
                              ("remove_one", RemoveOneFlagged()),
                              ("abstain", AbstainIfAnyFlag())):
            a = exact_metrics(k, em, cr, pol, tie, "counts")
            b = exact_metrics(k, em, cr, pol, tie, "full")
            assert a == b, (k, pol_name, tie)
            checks.append({"k": k, "policy": pol_name, "tie": tie, "equal": True})
    return checks


def main():
    census = json.loads(CENSUS_PATH.read_text())
    by_tid = {a["theorem_id"]: a for a in census["artifacts"]}

    cross = cross_check_counts_vs_full()
    survey = window_survey()
    exp_b_pairs = experiment_B_equal_precision_pairs()
    exp_c = run_experiment_C()
    exp_d = run_experiment_D()

    sens_t5 = eval_sensitivity_necessity(
        "k_over_k_plus_1",
        lambda m, e, tpr, fpr: tpr > fpr and m.precision is not None and m.precision > HALF)
    sens_half = eval_sensitivity_necessity(
        "half",
        lambda m, e, tpr, fpr: m.precision is not None and m.precision >= HALF and tpr > 0)
    sens_t13 = eval_sensitivity_necessity(
        "t13_band",
        lambda m, e, tpr, fpr: tpr > F(7, 10) and m.precision is not None
        and m.precision > F(3, 10))

    t4 = theorem_T4()
    records = [
        theorem_S1(),
        theorem_S2(t4),
        theorem_S3(),
        theorem_S4(),
        theorem_S5(),
        theorem_S6(),
        theorem_T1(),
        theorem_T2(),
        theorem_T3(),
        t4,
        theorem_T5(sens_t5),
        theorem_T6(),
        theorem_T7(exp_b_pairs),
        theorem_T8(sens_half),
        theorem_T9(sens_half),
        theorem_T10(exp_c),
        theorem_T11(),
        theorem_T12(),
        theorem_T13(sens_t13),
    ]

    for rec in records:
        art = by_tid.get(rec["theorem_id"])
        assert art is not None and art["artifact_id"] == rec["source_artifact_id"], rec["theorem_id"]

    report = {
        "schema": "deepreason-glm-judge-theory-verification-v1",
        "census": str(CENSUS_PATH),
        "date": "2026-07-14",
        "method": {
            "model_module": "deepreason.experiments.criticism_voting",
            "exactness": "all accuracies, repair/break probabilities, and derived "
                         "aggregates are fractions.Fraction; the only floats are the "
                         "mutual-information computations (natural log, tol 1e-9)",
            "enumeration": "count-based sufficient-statistic enumeration, proven equal "
                           "to full 4^k (correctness, flag) vector enumeration by "
                           "exchangeability and cross-checked in-run and in tests",
            "grids": {
                "k": list(K_GRID),
                "e": "0.05 step grid on (0,1) plus each censused window boundary "
                     "(1/(k+1), k/(k+2), k/(k+1), 1/2, and 0.55/0.75 at k=5) +- 0.01",
                "tpr": [frac_s(x) for x in TPR_GRID],
                "fpr": [frac_s(x) for x in FPR_GRID],
                "tie_rules": list(TIE_RULES),
            },
            "e_convention": "e is the per-candidate error probability in every artifact",
            "counterexample_order": "smallest by (k, grid distance of e to the nearest "
                                    "censused boundary, e, tpr, fpr, tie rule, note)",
            "verdict_rules": "exhaustive domains cap at verified_on_finite_domain; "
                             "sampled agreement caps at simulation_supported_only; "
                             "a single exact counterexample refutes",
            "cross_checks_counts_vs_full": cross,
            "monte_carlo_seed": MC_SEED,
        },
        "experiments": {
            "A_majority_fragility_windows": survey,
            "B_precision_thresholds": {
                "equal_precision_different_fpr": exp_b_pairs,
                "note": "per-theorem agreement rates and counterexamples live in the "
                        "T6/T7 records",
            },
            "C_identical_aggregates_opposite_outcomes": exp_c,
            "D_sufficient_conditional_statistics": exp_d,
        },
        "theorems": records,
        "verdict_table": [
            {"theorem_id": r["theorem_id"], "verdict": r["verdict"],
             "counterexamples": r["counterexamples"]["count"]}
            for r in records
        ],
    }
    OUT_PATH.write_text(json.dumps(report, indent=1))
    for row in report["verdict_table"]:
        print(f"{row['theorem_id']:40s} {row['verdict']:28s} ce={row['counterexamples']}")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
