"""Per-arm aggregate over blind/scores.json, run only after all 167 are scored.

WHY THIS IS A SEPARATE SCRIPT FROM `judge.py reveal`. `reveal` prints the four
arms' means and bests, which is what the copied protocol asks for. It does not
say whether the two M1 arms differ by more than the scatter of a 43-candidate
sample, and that is the question `RESULTS_M1.md` left open. This adds that,
plus the pre-registered outputs, in one pass.

WHAT IS PRE-REGISTERED AND WHAT IS NOT, stated here rather than in the report
so the distinction cannot be lost between the two:

  PRE-REGISTERED (`JUDGING_PREREG_COPIED.md`): the five criteria, 0-3 each; the
  MEDIAN of three judges as a candidate's total; the contested flag at >4 of 15
  spread; the single highest total as the winner; the highest scorer from EACH
  arm reported alongside it.

  NOT PRE-REGISTERED, and labelled descriptive wherever it appears: every
  arm-level summary (mean, median, quartiles) and the permutation test below.
  No threshold was registered for an arm-level difference in judged quality
  because no direction was registered for it either. These numbers describe the
  scored sample; they do not execute a decision rule.

The permutation test is exact-in-the-limit rather than asymptotic: it shuffles
the arm labels over the observed candidate medians many times and asks how
often chance alone separates the two arms by at least as much as the labels
did. It assumes nothing about the shape of the distribution, which matters
because the judged totals are bounded at 0 and 15 and are visibly not normal.
It is still ONE question and ONE run per arm: a small p here would say the two
candidate POOLS differ, never that a rerun of either arm would differ again.
"""

from __future__ import annotations

import json
import pathlib
import random
import statistics

HERE = pathlib.Path(__file__).resolve().parent
BLIND = HERE / "blind"
M1 = ("M1-H0P-control", "M1-H1R-history")
M3 = ("M3-C0P-blind", "M3-C1I-informed")
SHUFFLES = 100_000
SEED = 20260904  # fixed so the reported p is reproducible


def load() -> tuple[dict, dict]:
    scores = json.loads((BLIND / "scores.json").read_text())
    n_cand = sum(
        1 for l in (BLIND / "candidates.jsonl").read_text().splitlines() if l.strip()
    )
    if len(scores) != n_cand:
        raise SystemExit(
            f"REFUSED: {len(scores)} scored of {n_cand}. The keymap stays shut "
            "until every candidate is scored."
        )
    return scores, json.loads((BLIND / "keymap.json").read_text())


def permutation_p(a: list[float], b: list[float]) -> float:
    """Two-sided p for |mean(a) - mean(b)| under label exchangeability."""
    rng = random.Random(SEED)
    pool = a + b
    observed = abs(statistics.mean(a) - statistics.mean(b))
    n = len(a)
    hits = 0
    for _ in range(SHUFFLES):
        rng.shuffle(pool)
        if abs(statistics.mean(pool[:n]) - statistics.mean(pool[n:])) >= observed:
            hits += 1
    return (hits + 1) / (SHUFFLES + 1)


def describe(name: str, v: list[float]) -> None:
    s = sorted(v)
    q1 = statistics.quantiles(s, n=4)[0] if len(s) > 1 else s[0]
    q3 = statistics.quantiles(s, n=4)[2] if len(s) > 1 else s[0]
    print(
        f"  {name:<18} n={len(s):>3}  mean={statistics.mean(s):5.2f}  "
        f"median={statistics.median(s):5.2f}  q1={q1:4.1f}  q3={q3:4.1f}  "
        f"min={s[0]:4.1f}  max={s[-1]:4.1f}"
    )


def main() -> int:
    scores, keymap = load()
    by_arm: dict[str, list[float]] = {}
    best: dict[str, tuple[float, str]] = {}
    contested: dict[str, int] = {}
    one_judge: dict[str, int] = {}
    for bid, s in scores.items():
        if s.get("failed"):
            continue
        arm = keymap[bid]["arm"]
        by_arm.setdefault(arm, []).append(s["median"])
        contested[arm] = contested.get(arm, 0) + bool(s.get("contested"))
        one_judge[arm] = one_judge.get(arm, 0) + (s.get("judges", 3) < 3)
        if arm not in best or s["median"] > best[arm][0]:
            best[arm] = (s["median"], bid)

    print("BLIND_JUDGING_RESULT_V2  (candidate total = median of 3 judges, 0-15)")
    print(f"  candidates scored : {sum(len(v) for v in by_arm.values())}")
    print("\nPER-ARM DISTRIBUTION  [descriptive; no arm-level threshold registered]")
    for arm in sorted(by_arm):
        describe(arm, by_arm[arm])
    print("\nPRE-REGISTERED OUTPUTS")
    top = max(scores.items(), key=lambda kv: -1 if kv[1].get("failed") else kv[1]["median"])
    print(f"  single highest total : {top[1]['median']} "
          f"(arm {keymap[top[0]]['arm']}, artifact {keymap[top[0]]['artifact']})")
    for arm in sorted(best):
        print(f"  best in {arm:<18} {best[arm][0]:5.1f}  artifact "
              f"{keymap[best[arm][1]]['artifact']}")
    print("\nJUDGE AGREEMENT")
    for arm in sorted(by_arm):
        print(f"  {arm:<18} contested (>4 of 15 spread)={contested.get(arm,0):>3}  "
              f"scored on fewer than 3 judges={one_judge.get(arm,0):>2}")
    print("\nPAIRED COMPARISONS  [descriptive; permutation over labels, "
          f"{SHUFFLES} shuffles, seed {SEED}]")
    for pair in (M1, M3):
        a, b = by_arm.get(pair[0], []), by_arm.get(pair[1], [])
        if not a or not b:
            print(f"  {pair[0]} vs {pair[1]}: one arm has no scored candidates")
            continue
        d = statistics.mean(b) - statistics.mean(a)
        print(f"  {pair[1]} minus {pair[0]}: "
              f"mean diff {d:+.3f} of 15  ({d / statistics.mean(a) * 100:+.1f}% relative)"
              f"  p={permutation_p(a, b):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
