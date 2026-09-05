"""The quality replication, with candidate length held constant.

WHY THIS IS NOT OPTIONAL. The 2026-09-04 analysis found this judge panel scores
length: rank correlation +0.80 between a candidate's character count and its
judged total, and length alone explains 59% of the variance. Amendment 5 then
registered length as its own directional prediction precisely so that a quality
replication could be checked against a length replication. Both replicated. So
"the history arm is judged lower in all three pairs" and "the history arm wrote
shorter conjectures in all three pairs" are, so far, the same observation
reported twice.

This separates them, per pair and pooled, by the same two adjustments
analyse_length_bias.py uses on the first pair -- a log-length covariate and a
within-quintile stratification -- because each fails differently and agreement
between them is worth more than either alone.
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyse_length_bias import ols, perm_p, r2, spearman  # noqa: E402

PAIRS = {
    "P1": ("blind", "M1-H0P-control", "M1-H1R-history"),
    "P2": ("blind-r", "R2-H0P-control", "R2-H1R-history"),
    "P3": ("blind-r", "R3-H0P-control", "R3-H1R-history"),
}
SEED = 20260905


def rows(blind_dir: str, arms: tuple[str, ...]) -> list[tuple[str, float, float]]:
    b = HERE / blind_dir
    scores = json.loads((b / "scores.json").read_text())
    keymap = json.loads((b / "keymap.json").read_text())
    text = {json.loads(l)["bid"]: json.loads(l)["text"]
            for l in (b / "candidates.jsonl").read_text().splitlines() if l.strip()}
    return [(keymap[bid]["arm"], float(s["median"]), float(len(text[bid])))
            for bid, s in scores.items()
            if not s.get("failed") and keymap[bid]["arm"] in arms]


def arm_term(data, treat, draws=20000):
    y = [r[1] for r in data]
    X = [[1.0, math.log(r[2]), 1.0 if r[0] == treat else 0.0] for r in data]
    b = ols(y, X)
    rng = random.Random(SEED)
    lab = [x[2] for x in X]
    hits = 0
    for _ in range(draws):
        rng.shuffle(lab)
        if abs(ols(y, [[X[i][0], X[i][1], lab[i]] for i in range(len(X))])[2]) >= abs(b[2]):
            hits += 1
    return b[2], (hits + 1) / (draws + 1), r2(y, X, b)


def main() -> int:
    print("REPLICATION_LENGTH_ADJUSTED_V1\n")
    allrows: list[tuple[str, float, float]] = []
    print("  pair   raw gap    length gap    adjusted gap        p   verdict on the raw gap")
    for name, (bdir, ctl, treat) in PAIRS.items():
        data = rows(bdir, (ctl, treat))
        allrows += [(("control" if r[0] == ctl else "history"), r[1], r[2]) for r in data]
        a = [r for r in data if r[0] == ctl]
        h = [r for r in data if r[0] == treat]
        raw = statistics.mean(x[1] for x in h) - statistics.mean(x[1] for x in a)
        dlen = statistics.mean(x[2] for x in h) / statistics.mean(x[2] for x in a) - 1
        coef, p, _ = arm_term(data, treat)
        survives = "survives" if (coef < 0 and p < 0.10) else "does NOT survive"
        print(f"  {name}   {raw:+7.2f}     {dlen*100:+7.1f}%      {coef:+7.2f}    {p:6.4f}   {survives}")

    print(f"\n  POOLED over all three pairs, {len(allrows)} candidates")
    a = [r for r in allrows if r[0] == "control"]
    h = [r for r in allrows if r[0] == "history"]
    raw = statistics.mean(x[1] for x in h) - statistics.mean(x[1] for x in a)
    print(f"    control n={len(a)} mean={statistics.mean(x[1] for x in a):.2f}  "
          f"history n={len(h)} mean={statistics.mean(x[1] for x in h):.2f}  "
          f"raw gap {raw:+.2f} of 15  p={perm_p([x[1] for x in a], [x[1] for x in h]):.4f}")
    print(f"    control chars={statistics.mean(x[2] for x in a):.1f}  "
          f"history chars={statistics.mean(x[2] for x in h):.1f}  "
          f"p={perm_p([x[2] for x in a], [x[2] for x in h]):.4f}")
    coef, p, rr = arm_term(allrows, "history")
    print(f"    length-adjusted arm term {coef:+.2f} of 15  p={p:.4f}  (model R^2 {rr:.3f})")
    print(f"    rho(chars, total) over all {len(allrows)} = "
          f"{spearman([x[2] for x in allrows], [x[1] for x in allrows]):+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
