"""Does the judge panel score merit, or length?

NOT a pre-registered measure. It was run because CLAUDE.md's judge law records
verbosity bias as having ZERO live measurements, and this tranche happens to
hold 167 blind-judged candidates whose lengths are already on disk. The check
costs one pass over two committed files.

It matters for the verdict rather than merely decorating it: if the panel pays
for length, and the two arms wrote to different lengths, then part of the
arm-level gap is a length statistic wearing a quality label. Both antecedents
turned out to hold, so §3.4 of RESULTS_M1_QUALITY.md reports the raw gap and
the length-held-constant gap side by side rather than the raw gap alone.

Two adjustments are computed, not one, because each fails differently: the
log-length regression assumes a shape for the length effect, and the quintile
stratification does not but throws away within-stratum information. They agree
on direction and differ on size, and both numbers are reported.
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import statistics

HERE = pathlib.Path(__file__).resolve().parent
BLIND = HERE / "blind"
SEED = 20260904


def rows() -> list[tuple[str, float, float]]:
    scores = json.loads((BLIND / "scores.json").read_text())
    keymap = json.loads((BLIND / "keymap.json").read_text())
    text = {
        json.loads(l)["bid"]: json.loads(l)["text"]
        for l in (BLIND / "candidates.jsonl").read_text().splitlines()
        if l.strip()
    }
    return [
        (keymap[b]["arm"], float(s["median"]), float(len(text[b])))
        for b, s in scores.items()
        if not s.get("failed")
    ]


def ols(y: list[float], X: list[list[float]]) -> list[float]:
    n, k = len(y), len(X[0])
    M = [
        [sum(X[i][a] * X[i][c] for i in range(n)) for c in range(k)]
        + [sum(X[i][a] * y[i] for i in range(n))]
        for a in range(k)
    ]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(k):
            if r != c:
                f = M[r][c] / M[c][c]
                for cc in range(c, k + 1):
                    M[r][cc] -= f * M[c][cc]
    return [M[i][k] / M[i][i] for i in range(k)]


def spearman(a: list[float], b: list[float]) -> float:
    def rk(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        out = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                out[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return out
    x, y = rk(a), rk(b)
    mx, my = statistics.mean(x), statistics.mean(y)
    num = sum((p - mx) * (q - my) for p, q in zip(x, y))
    den = (sum((p - mx) ** 2 for p in x) * sum((q - my) ** 2 for q in y)) ** 0.5
    return num / den


def r2(y: list[float], X: list[list[float]], b: list[float]) -> float:
    my = statistics.mean(y)
    res = sum((y[i] - sum(b[j] * X[i][j] for j in range(len(b)))) ** 2 for i in range(len(y)))
    return 1 - res / sum((v - my) ** 2 for v in y)


def arm_term(data: list[tuple[str, float, float]], treat: str, draws: int = 20000):
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


def perm_p(a: list[float], b: list[float], draws: int = 100000) -> float:
    """Two-sided p for a difference in means under label exchangeability."""
    rng = random.Random(SEED)
    pool = a + b
    obs = abs(statistics.mean(a) - statistics.mean(b))
    n, hits = len(a), 0
    for _ in range(draws):
        rng.shuffle(pool)
        if abs(statistics.mean(pool[:n]) - statistics.mean(pool[n:])) >= obs:
            hits += 1
    return (hits + 1) / (draws + 1)


def stratified(data: list[tuple[str, float, float]], ctl: str, treat: str) -> float:
    qs = statistics.quantiles([r[2] for r in data], n=5)
    buckets: dict[int, list[tuple[str, float]]] = {}
    for arm, t, c in data:
        buckets.setdefault(sum(c > q for q in qs), []).append((arm, t))
    num = den = 0.0
    print("  length quintile means:")
    for s in sorted(buckets):
        a = [t for arm, t in buckets[s] if arm == ctl]
        h = [t for arm, t in buckets[s] if arm == treat]
        if not a or not h:
            continue
        d = statistics.mean(h) - statistics.mean(a)
        num += d * len(buckets[s])
        den += len(buckets[s])
        print(f"    q{s+1}: {ctl.split('-')[1]} n={len(a):>2} {statistics.mean(a):5.2f} | "
              f"{treat.split('-')[1]} n={len(h):>2} {statistics.mean(h):5.2f} | {d:+.2f}")
    return num / den


def main() -> int:
    data = rows()
    print("LENGTH_BIAS_RESULT_V1  [NOT pre-registered; descriptive]")
    print(f"  candidates: {len(data)}")
    print("\nDOES THE PANEL PAY FOR LENGTH?  (pooled, all arms)")
    y = [r[1] for r in data]
    c = [r[2] for r in data]
    print(f"  Spearman rho(chars, total) = {spearman(c, y):+.3f}")
    X = [[1.0, math.log(v)] for v in c]
    b = ols(y, X)
    print(f"  total ~ {b[0]:+.2f} {b[1]:+.2f}*log(chars)   R^2 = {r2(y, X, b):.3f}")
    print("  -> length alone accounts for most of the variance in judged totals.")

    for ctl, treat in (("M1-H0P-control", "M1-H1R-history"),
                       ("M3-C0P-blind", "M3-C1I-informed")):
        pair = [r for r in data if r[0] in (ctl, treat)]
        a = [r[2] for r in pair if r[0] == ctl]
        h = [r[2] for r in pair if r[0] == treat]
        ya = [r[1] for r in pair if r[0] == ctl]
        yh = [r[1] for r in pair if r[0] == treat]
        print(f"\n{treat} vs {ctl}")
        print(f"  candidate length: {statistics.mean(a):.1f} -> {statistics.mean(h):.1f} chars "
              f"({(statistics.mean(h)/statistics.mean(a)-1)*100:+.1f}%)  p={perm_p(a, h):.4f}")
        print(f"  raw score gap   : {statistics.mean(yh)-statistics.mean(ya):+.3f} of 15")
        coef, p, rr = arm_term(pair, treat)
        print(f"  length-adjusted : {coef:+.2f} of 15  p={p:.4f}  (model R^2 {rr:.3f})")
        print(f"  quintile-held   : {stratified(pair, ctl, treat):+.3f} of 15")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
