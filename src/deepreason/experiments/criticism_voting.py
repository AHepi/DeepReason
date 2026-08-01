"""Deterministic model of criticism-filtered voting vs self-consistency (SC).

State is explicit and low-level: a Question holds an ensemble size k, a
per-candidate correctness vector, and a per-candidate critic flag vector.
Every aggregate (precision, recall, FPR, base error) is derived from these
vectors; none is ever supplied as an input to an outcome computation.

Fixed conventions (each artifact under test is mapped onto these):

- Majority rule: the ensemble answer is correct iff strictly more than half
  of the remaining post-filter weight sits on correct candidates.
- Tie: equal correct/wrong weight among remaining candidates, including an
  empty remainder. Tie rules:
    "incorrect": a tie scores as wrong.
    "random":    a tie scores 1/2 in exact evaluators; realized evaluators
                 draw a fair coin from the caller's seeded RNG.
    "unchanged": a post-filter tie falls back to the pre-filter outcome.
                 The pre-filter baseline itself resolves ties (even k only)
                 as incorrect, because there is no earlier outcome.
- Filtering policies:
    RemoveAllFlagged: drop every flagged candidate.
    RemoveOneFlagged: drop the first flagged candidate in index order.
    AbstainIfAnyFlag: if any candidate is flagged the question is scored as
                      the pre-filter outcome (filtering is a no-op).
    Reweight(w):      flagged candidates keep weight w in [0, 1] instead of
                      weight 1; the vote compares total weights.
- Error generators: IndependentErrors(e) draws candidate errors i.i.d.
  Bernoulli(e). DifficultyMixture(rho, e_hard, e_easy) draws one shared
  per-question difficulty latent: with probability rho the whole question
  uses error rate e_hard, otherwise e_easy; candidates are i.i.d. given the
  latent. This is the documented correlation scheme.
- Critic models: HomogeneousCritic flags wrong candidates with probability
  TPR and correct candidates with probability FPR, independently.
  MajorityConditionalCritic uses one (TPR, FPR) pair when the pre-filter
  majority is strictly correct and another otherwise (ties and wrong
  majorities share the "wrong" pair). MarginConditionalCritic keys the
  (TPR, FPR) pair on the signed pre-filter margin n_correct - n_wrong.
- Exact evaluators use fractions.Fraction end to end; float parameters are
  rejected. Exact repair/break probabilities treat the "random" tie coins
  before and after filtering as independent draws.

No I/O in this module.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import comb
from typing import Iterator, Union

TIE_RULES = ("incorrect", "random", "unchanged")

ONE = Fraction(1)
ZERO = Fraction(0)
HALF = Fraction(1, 2)


def _frac(x) -> Fraction:
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    raise TypeError(f"exact parameter must be Fraction or int, got {type(x).__name__}")


def _check_prob(x: Fraction, name: str) -> Fraction:
    x = _frac(x)
    if x < 0 or x > 1:
        raise ValueError(f"{name} must lie in [0, 1], got {x}")
    return x


# ---------------------------------------------------------------------------
# Low-level state


@dataclass(frozen=True)
class Question:
    """k candidates; correct[i] and flags[i] are the full low-level state."""

    k: int
    correct: tuple
    flags: tuple

    def __post_init__(self):
        if len(self.correct) != self.k or len(self.flags) != self.k:
            raise ValueError("k must equal len(correct) and len(flags)")
        if not all(isinstance(b, bool) for b in self.correct + self.flags):
            raise TypeError("correctness and flag vectors must contain bools")

    @property
    def n_correct(self) -> int:
        return sum(self.correct)

    @property
    def n_wrong(self) -> int:
        return self.k - self.n_correct


# ---------------------------------------------------------------------------
# Filtering policies


@dataclass(frozen=True)
class RemoveAllFlagged:
    pass


@dataclass(frozen=True)
class RemoveOneFlagged:
    pass


@dataclass(frozen=True)
class AbstainIfAnyFlag:
    pass


@dataclass(frozen=True)
class Reweight:
    weight: Fraction

    def __post_init__(self):
        object.__setattr__(self, "weight", _check_prob(self.weight, "weight"))


Policy = Union[RemoveAllFlagged, RemoveOneFlagged, AbstainIfAnyFlag, Reweight]

_ABSTAIN = object()


def _vote(weight_correct, weight_wrong, tie_rule: str, prefilter) -> Fraction:
    """P(answer correct) for a pool with the given correct/wrong weight.

    prefilter is the pre-filter outcome probability, used only by the
    "unchanged" tie rule; None means there is no earlier outcome and a tie
    resolves as incorrect.
    """
    if tie_rule not in TIE_RULES:
        raise ValueError(f"unknown tie rule {tie_rule!r}")
    if weight_correct > weight_wrong:
        return ONE
    if weight_wrong > weight_correct:
        return ZERO
    if tie_rule == "incorrect":
        return ZERO
    if tie_rule == "random":
        return HALF
    return ZERO if prefilter is None else prefilter


def _post_weights(q: Question, policy: Policy):
    """Post-filter (weight_correct, weight_wrong) or the abstain sentinel."""
    if isinstance(policy, AbstainIfAnyFlag):
        if any(q.flags):
            return _ABSTAIN
        return q.n_correct, q.n_wrong
    if isinstance(policy, RemoveAllFlagged):
        wc = sum(1 for c, f in zip(q.correct, q.flags) if c and not f)
        ww = sum(1 for c, f in zip(q.correct, q.flags) if not c and not f)
        return wc, ww
    if isinstance(policy, RemoveOneFlagged):
        wc, ww = q.n_correct, q.n_wrong
        for c, f in zip(q.correct, q.flags):
            if f:
                if c:
                    wc -= 1
                else:
                    ww -= 1
                break
        return wc, ww
    if isinstance(policy, Reweight):
        w = policy.weight
        wc = sum((w if f else ONE) for c, f in zip(q.correct, q.flags) if c)
        ww = sum((w if f else ONE) for c, f in zip(q.correct, q.flags) if not c)
        return wc, ww
    raise TypeError(f"unknown policy {policy!r}")


def outcome_before(q: Question, tie_rule: str) -> Fraction:
    """Pre-filter SC outcome as an exact P(correct) in {0, 1/2, 1}."""
    return _vote(q.n_correct, q.n_wrong, tie_rule, None)


def outcome_after(q: Question, policy: Policy, tie_rule: str) -> Fraction:
    """Post-filter harness outcome as an exact P(correct)."""
    state = _post_weights(q, policy)
    if state is _ABSTAIN:
        return outcome_before(q, tie_rule)
    wc, ww = state
    return _vote(wc, ww, tie_rule, outcome_before(q, tie_rule))


def repaired(q: Question, policy: Policy, tie_rule: str) -> bool:
    """Wrong majority became right; requires both outcomes determined."""
    return outcome_before(q, tie_rule) == 0 and outcome_after(q, policy, tie_rule) == 1


def broken(q: Question, policy: Policy, tie_rule: str) -> bool:
    """Right majority became wrong; requires both outcomes determined."""
    return outcome_before(q, tie_rule) == 1 and outcome_after(q, policy, tie_rule) == 0


def repair_break_probs(q: Question, policy: Policy, tie_rule: str):
    """(P(repair), P(break)) with independent tie coins before and after."""
    b = outcome_before(q, tie_rule)
    state = _post_weights(q, policy)
    if state is _ABSTAIN:
        return ZERO, ZERO
    wc, ww = state
    if wc > ww:
        return (ONE - b), ZERO
    if ww > wc:
        return ZERO, b
    if tie_rule == "incorrect":
        return ZERO, b
    if tie_rule == "random":
        return (ONE - b) * HALF, b * HALF
    return ZERO, ZERO


# ---------------------------------------------------------------------------
# Realized (boolean) outcomes for Monte Carlo


def realized_outcome_before(q: Question, tie_rule: str, rng: random.Random) -> bool:
    p = outcome_before(q, tie_rule)
    if p == 1:
        return True
    if p == 0:
        return False
    return rng.random() < 0.5


def realized_outcome_after(
    q: Question, policy: Policy, tie_rule: str, rng: random.Random, before: bool
) -> bool:
    state = _post_weights(q, policy)
    if state is _ABSTAIN:
        return before
    wc, ww = state
    if wc > ww:
        return True
    if ww > wc:
        return False
    if tie_rule == "incorrect":
        return False
    if tie_rule == "random":
        return rng.random() < 0.5
    return before


# ---------------------------------------------------------------------------
# Derived aggregates from realized vectors


def aggregate_metrics(questions) -> dict:
    """Precision/recall/FPR/base error derived from explicit vectors only."""
    tp = fp = wrong = correct = 0
    for q in questions:
        for c, f in zip(q.correct, q.flags):
            if c:
                correct += 1
                if f:
                    fp += 1
            else:
                wrong += 1
                if f:
                    tp += 1
    total = wrong + correct
    return {
        "tp": tp,
        "fp": fp,
        "n_wrong": wrong,
        "n_correct": correct,
        "n_candidates": total,
        "precision": Fraction(tp, tp + fp) if tp + fp else None,
        "recall": Fraction(tp, wrong) if wrong else None,
        "fpr": Fraction(fp, correct) if correct else None,
        "base_error": Fraction(wrong, total) if total else None,
    }


def population_eval(questions, policy: Policy, tie_rule: str) -> dict:
    """Exact SC/harness scores and derived aggregates for a fixed population."""
    questions = list(questions)
    sc = ZERO
    harness = ZERO
    n_repaired = 0
    n_broken = 0
    per_question = []
    for q in questions:
        b = outcome_before(q, tie_rule)
        a = outcome_after(q, policy, tie_rule)
        sc += b
        harness += a
        r = repaired(q, policy, tie_rule)
        k = broken(q, policy, tie_rule)
        n_repaired += r
        n_broken += k
        per_question.append({"before": b, "after": a, "repaired": r, "broken": k})
    return {
        "n_questions": len(questions),
        "sc_correct": sc,
        "harness_correct": harness,
        "net": harness - sc,
        "repaired": n_repaired,
        "broken": n_broken,
        "per_question": per_question,
        "aggregates": aggregate_metrics(questions),
    }


# ---------------------------------------------------------------------------
# Error generators


@dataclass(frozen=True)
class IndependentErrors:
    """Candidate errors i.i.d. Bernoulli(e)."""

    e: Fraction

    def __post_init__(self):
        object.__setattr__(self, "e", _check_prob(self.e, "e"))

    def wrong_count_dist(self, k: int) -> dict:
        e = self.e
        return {m: comb(k, m) * e**m * (ONE - e) ** (k - m) for m in range(k + 1)}

    def vector_prob(self, correct) -> Fraction:
        e = self.e
        nw = sum(1 for c in correct if not c)
        return e**nw * (ONE - e) ** (len(correct) - nw)

    def sample(self, k: int, rng: random.Random):
        e = float(self.e)
        return tuple(rng.random() >= e for _ in range(k))


@dataclass(frozen=True)
class DifficultyMixture:
    """Shared per-question difficulty latent: hard (rate e_hard) with
    probability rho, else easy (rate e_easy); candidates i.i.d. given it."""

    rho: Fraction
    e_hard: Fraction
    e_easy: Fraction

    def __post_init__(self):
        object.__setattr__(self, "rho", _check_prob(self.rho, "rho"))
        object.__setattr__(self, "e_hard", _check_prob(self.e_hard, "e_hard"))
        object.__setattr__(self, "e_easy", _check_prob(self.e_easy, "e_easy"))

    def _components(self):
        return (
            (self.rho, IndependentErrors(self.e_hard)),
            (ONE - self.rho, IndependentErrors(self.e_easy)),
        )

    def wrong_count_dist(self, k: int) -> dict:
        out = {m: ZERO for m in range(k + 1)}
        for w, comp in self._components():
            for m, p in comp.wrong_count_dist(k).items():
                out[m] += w * p
        return out

    def vector_prob(self, correct) -> Fraction:
        return sum(w * comp.vector_prob(correct) for w, comp in self._components())

    def sample(self, k: int, rng: random.Random):
        hard = rng.random() < float(self.rho)
        comp = IndependentErrors(self.e_hard if hard else self.e_easy)
        return comp.sample(k, rng)


# ---------------------------------------------------------------------------
# Critic models


@dataclass(frozen=True)
class HomogeneousCritic:
    """Flags wrong candidates with prob TPR, correct ones with prob FPR."""

    tpr: Fraction
    fpr: Fraction

    def __post_init__(self):
        object.__setattr__(self, "tpr", _check_prob(self.tpr, "tpr"))
        object.__setattr__(self, "fpr", _check_prob(self.fpr, "fpr"))

    def rates_for_counts(self, n_correct: int, n_wrong: int):
        return self.tpr, self.fpr


@dataclass(frozen=True)
class MajorityConditionalCritic:
    """(TPR, FPR) conditioned on pre-filter majority correctness; ties and
    wrong majorities use the *_wrong pair."""

    tpr_right: Fraction
    fpr_right: Fraction
    tpr_wrong: Fraction
    fpr_wrong: Fraction

    def __post_init__(self):
        for name in ("tpr_right", "fpr_right", "tpr_wrong", "fpr_wrong"):
            object.__setattr__(self, name, _check_prob(getattr(self, name), name))

    def rates_for_counts(self, n_correct: int, n_wrong: int):
        if n_correct > n_wrong:
            return self.tpr_right, self.fpr_right
        return self.tpr_wrong, self.fpr_wrong


@dataclass(frozen=True)
class MarginConditionalCritic:
    """(TPR, FPR) keyed on the signed pre-filter margin n_correct - n_wrong.

    overrides is a sorted tuple of (margin, tpr, fpr) triples; margins not
    listed use the default pair.
    """

    default: tuple
    overrides: tuple = ()

    def __post_init__(self):
        d = (_check_prob(self.default[0], "default tpr"), _check_prob(self.default[1], "default fpr"))
        object.__setattr__(self, "default", d)
        ov = tuple(
            sorted(
                (int(m), _check_prob(t, "override tpr"), _check_prob(f, "override fpr"))
                for m, t, f in self.overrides
            )
        )
        if len({m for m, _, _ in ov}) != len(ov):
            raise ValueError("duplicate margin override")
        object.__setattr__(self, "overrides", ov)

    def rates_for_counts(self, n_correct: int, n_wrong: int):
        margin = n_correct - n_wrong
        for m, t, f in self.overrides:
            if m == margin:
                return t, f
        return self.default


Critic = Union[HomogeneousCritic, MajorityConditionalCritic, MarginConditionalCritic]


def flag_vector_prob(critic: Critic, correct, flags) -> Fraction:
    nc = sum(1 for c in correct if c)
    tpr, fpr = critic.rates_for_counts(nc, len(correct) - nc)
    p = ONE
    for c, f in zip(correct, flags):
        rate = fpr if c else tpr
        p *= rate if f else (ONE - rate)
    return p


def sample_flags(critic: Critic, correct, rng: random.Random):
    nc = sum(1 for c in correct if c)
    tpr, fpr = critic.rates_for_counts(nc, len(correct) - nc)
    tpr_f, fpr_f = float(tpr), float(fpr)
    return tuple(rng.random() < (fpr_f if c else tpr_f) for c in correct)


# ---------------------------------------------------------------------------
# Exhaustive exact evaluation


@dataclass(frozen=True)
class ExactMetrics:
    """Exact expectations per question under a parameterization.

    Fragile fields restrict to pools whose pre-filter absolute margin is
    <= 2 (for odd k that is exactly margin 1). p_fragile_correct and
    p_fragile_wrong are the probabilities of pre-filter margin +1 and -1.
    """

    k: int
    sc_accuracy: Fraction
    harness_accuracy: Fraction
    p_repair: Fraction
    p_break: Fraction
    expected_tp: Fraction
    expected_fp: Fraction
    expected_wrong: Fraction
    expected_correct: Fraction
    fragile_tp: Fraction
    fragile_fp: Fraction
    fragile_wrong: Fraction
    fragile_correct: Fraction
    p_fragile_correct: Fraction
    p_fragile_wrong: Fraction

    @property
    def net(self) -> Fraction:
        return self.harness_accuracy - self.sc_accuracy

    @property
    def precision(self):
        denom = self.expected_tp + self.expected_fp
        return None if denom == 0 else self.expected_tp / denom

    @property
    def recall(self):
        return None if self.expected_wrong == 0 else self.expected_tp / self.expected_wrong

    @property
    def fpr(self):
        return None if self.expected_correct == 0 else self.expected_fp / self.expected_correct

    @property
    def base_error(self) -> Fraction:
        return self.expected_wrong / self.k

    @property
    def fragile_precision(self):
        denom = self.fragile_tp + self.fragile_fp
        return None if denom == 0 else self.fragile_tp / denom


def enumerate_joint(k: int, error_model, critic: Critic) -> Iterator[tuple]:
    """ALL (correctness vector, flag vector) pairs with exact probabilities.

    Yields 4**k atoms; intended for k <= 9.
    """
    for correct in product((True, False), repeat=k):
        pc = error_model.vector_prob(correct)
        for flags in product((True, False), repeat=k):
            yield Question(k, correct, flags), pc * flag_vector_prob(critic, correct, flags)


def _count_branches(policy: Policy, nc: int, m: int, fc: int, fw: int):
    """Post-filter weight branches given counts; None means abstain no-op.

    Returns a list of (weight_correct, weight_wrong, branch_prob). The
    RemoveOneFlagged split uses exchangeability: conditioned on fc + fw
    flags, the first flagged candidate is correct with prob fc/(fc+fw).
    """
    if isinstance(policy, AbstainIfAnyFlag):
        if fc + fw > 0:
            return None
        return [(nc, m, ONE)]
    if isinstance(policy, RemoveAllFlagged):
        return [(nc - fc, m - fw, ONE)]
    if isinstance(policy, RemoveOneFlagged):
        total = fc + fw
        if total == 0:
            return [(nc, m, ONE)]
        out = []
        if fc:
            out.append((nc - 1, m, Fraction(fc, total)))
        if fw:
            out.append((nc, m - 1, Fraction(fw, total)))
        return out
    if isinstance(policy, Reweight):
        w = policy.weight
        return [((nc - fc) + w * fc, (m - fw) + w * fw, ONE)]
    raise TypeError(f"unknown policy {policy!r}")


def _accumulate(acc: dict, weight: Fraction, b: Fraction, branches, tie_rule: str):
    """Fold one atom's post-filter branches into the accumulators."""
    if branches is None:
        acc["harness"] += weight * b
        return
    for wc, ww, bp in branches:
        wgt = weight * bp
        if wc > ww:
            acc["harness"] += wgt
            acc["repair"] += wgt * (ONE - b)
        elif ww > wc:
            acc["break"] += wgt * b
        elif tie_rule == "incorrect":
            acc["break"] += wgt * b
        elif tie_rule == "random":
            acc["harness"] += wgt * HALF
            acc["repair"] += wgt * (ONE - b) * HALF
            acc["break"] += wgt * b * HALF
        else:
            acc["harness"] += wgt * b


def _exact_by_counts(k, error_model, critic, policy, tie_rule) -> ExactMetrics:
    acc = {
        "sc": ZERO, "harness": ZERO, "repair": ZERO, "break": ZERO,
        "tp": ZERO, "fp": ZERO, "wrong": ZERO, "correct": ZERO,
        "ftp": ZERO, "ffp": ZERO, "fwrong": ZERO, "fcorrect": ZERO,
        "pfc": ZERO, "pfw": ZERO,
    }
    for m, pm in error_model.wrong_count_dist(k).items():
        if pm == 0:
            continue
        nc = k - m
        tpr, fpr = critic.rates_for_counts(nc, m)
        b = _vote(nc, m, tie_rule, None)
        margin = nc - m
        fragile = abs(margin) <= 2
        acc["sc"] += pm * b
        acc["wrong"] += pm * m
        acc["correct"] += pm * nc
        if margin == 1:
            acc["pfc"] += pm
        elif margin == -1:
            acc["pfw"] += pm
        if fragile:
            acc["fwrong"] += pm * m
            acc["fcorrect"] += pm * nc
        pw = [comb(m, fw) * tpr**fw * (ONE - tpr) ** (m - fw) for fw in range(m + 1)]
        pc = [comb(nc, fc) * fpr**fc * (ONE - fpr) ** (nc - fc) for fc in range(nc + 1)]
        for fw in range(m + 1):
            if pw[fw] == 0:
                continue
            for fc in range(nc + 1):
                if pc[fc] == 0:
                    continue
                weight = pm * pw[fw] * pc[fc]
                acc["tp"] += weight * fw
                acc["fp"] += weight * fc
                if fragile:
                    acc["ftp"] += weight * fw
                    acc["ffp"] += weight * fc
                _accumulate(acc, weight, b, _count_branches(policy, nc, m, fc, fw), tie_rule)
    return ExactMetrics(
        k=k, sc_accuracy=acc["sc"], harness_accuracy=acc["harness"],
        p_repair=acc["repair"], p_break=acc["break"],
        expected_tp=acc["tp"], expected_fp=acc["fp"],
        expected_wrong=acc["wrong"], expected_correct=acc["correct"],
        fragile_tp=acc["ftp"], fragile_fp=acc["ffp"],
        fragile_wrong=acc["fwrong"], fragile_correct=acc["fcorrect"],
        p_fragile_correct=acc["pfc"], p_fragile_wrong=acc["pfw"],
    )


def _exact_by_full_enumeration(k, error_model, critic, policy, tie_rule) -> ExactMetrics:
    acc = {
        "sc": ZERO, "harness": ZERO, "repair": ZERO, "break": ZERO,
        "tp": ZERO, "fp": ZERO, "wrong": ZERO, "correct": ZERO,
        "ftp": ZERO, "ffp": ZERO, "fwrong": ZERO, "fcorrect": ZERO,
        "pfc": ZERO, "pfw": ZERO,
    }
    seen_correct = set()
    for q, weight in enumerate_joint(k, error_model, critic):
        if weight == 0:
            continue
        nc, m = q.n_correct, q.n_wrong
        b = outcome_before(q, tie_rule)
        margin = nc - m
        fragile = abs(margin) <= 2
        if q.correct not in seen_correct:
            seen_correct.add(q.correct)
            pcv = error_model.vector_prob(q.correct)
            acc["sc"] += pcv * b
            acc["wrong"] += pcv * m
            acc["correct"] += pcv * nc
            if margin == 1:
                acc["pfc"] += pcv
            elif margin == -1:
                acc["pfw"] += pcv
            if fragile:
                acc["fwrong"] += pcv * m
                acc["fcorrect"] += pcv * nc
        fw = sum(1 for c, f in zip(q.correct, q.flags) if not c and f)
        fc = sum(1 for c, f in zip(q.correct, q.flags) if c and f)
        acc["tp"] += weight * fw
        acc["fp"] += weight * fc
        if fragile:
            acc["ftp"] += weight * fw
            acc["ffp"] += weight * fc
        acc["harness"] += weight * outcome_after(q, policy, tie_rule)
        rp, bp = repair_break_probs(q, policy, tie_rule)
        acc["repair"] += weight * rp
        acc["break"] += weight * bp
    return ExactMetrics(
        k=k, sc_accuracy=acc["sc"], harness_accuracy=acc["harness"],
        p_repair=acc["repair"], p_break=acc["break"],
        expected_tp=acc["tp"], expected_fp=acc["fp"],
        expected_wrong=acc["wrong"], expected_correct=acc["correct"],
        fragile_tp=acc["ftp"], fragile_fp=acc["ffp"],
        fragile_wrong=acc["fwrong"], fragile_correct=acc["fcorrect"],
        p_fragile_correct=acc["pfc"], p_fragile_wrong=acc["pfw"],
    )


def exact_metrics(k, error_model, critic, policy, tie_rule, method="counts") -> ExactMetrics:
    """Exact expected metrics; "counts" and "full" must agree.

    "counts" enumerates the sufficient-statistic partition (wrong count,
    flags-on-correct, flags-on-wrong), valid because all shipped error and
    critic models are exchangeable over candidate positions given those
    counts. "full" enumerates all 4**k (correctness, flag) vector pairs.
    """
    if method == "counts":
        return _exact_by_counts(k, error_model, critic, policy, tie_rule)
    if method == "full":
        return _exact_by_full_enumeration(k, error_model, critic, policy, tie_rule)
    raise ValueError(f"unknown method {method!r}")


# ---------------------------------------------------------------------------
# Monte Carlo


def simulate_metrics(k, n_questions, error_model, critic, policy, tie_rule, seed) -> dict:
    """Seeded Monte Carlo estimate of the same quantities, for larger k.

    Draw order per question: correctness vector, flag vector, pre-filter
    tie coin (if needed), post-filter tie coin (if needed).
    """
    rng = random.Random(seed)
    sc = harness = repairs = breaks = 0
    tp = fp = wrong = correct = 0
    for _ in range(n_questions):
        cv = error_model.sample(k, rng)
        fv = sample_flags(critic, cv, rng)
        q = Question(k, cv, fv)
        before = realized_outcome_before(q, tie_rule, rng)
        after = realized_outcome_after(q, policy, tie_rule, rng, before)
        sc += before
        harness += after
        repairs += (not before) and after
        breaks += before and (not after)
        for c, f in zip(cv, fv):
            if c:
                correct += 1
                fp += f
            else:
                wrong += 1
                tp += f
    n = n_questions
    return {
        "seed": seed,
        "n_questions": n,
        "sc_accuracy": sc / n,
        "harness_accuracy": harness / n,
        "p_repair": repairs / n,
        "p_break": breaks / n,
        "precision": (tp / (tp + fp)) if tp + fp else None,
        "recall": (tp / wrong) if wrong else None,
        "fpr": (fp / correct) if correct else None,
        "base_error": wrong / (wrong + correct),
    }
