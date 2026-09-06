"""Length held constant, and per-seat spend. PREREG_D8.md §4 and §5.

A port of the committed `analyse_length_bias.py` (same OLS, same Spearman,
same permutation tests, same quintile stratification) to two arms, plus the
decision rule §4 fixes and the spend table §5 fixes. Seed 20260906. Run only
AFTER `judge_d8.py reveal` -- it reads the keymap.
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
BLIND = HERE / "blind"
SEED = 20260906
CTL, TREAT = "ARM0-single-call", "ARMM-isolation"


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


def ols(y, X):
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


def spearman(a, b):
    def rk(v):
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
    return num / den if den else float("nan")


def r2(y, X, b):
    my = statistics.mean(y)
    res = sum((y[i] - sum(b[j] * X[i][j] for j in range(len(b)))) ** 2 for i in range(len(y)))
    tot = sum((v - my) ** 2 for v in y)
    return 1 - res / tot if tot else float("nan")


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


def perm_p(a, b, draws=100000):
    rng = random.Random(SEED)
    pool = a + b
    obs = abs(statistics.mean(a) - statistics.mean(b))
    n, hits = len(a), 0
    for _ in range(draws):
        rng.shuffle(pool)
        if abs(statistics.mean(pool[:n]) - statistics.mean(pool[n:])) >= obs:
            hits += 1
    return (hits + 1) / (draws + 1)


def stratified(data, ctl, treat):
    """Quintile-held gap over strata holding BOTH arms; (gap, strata) or (None, 0)."""
    qs = statistics.quantiles([r[2] for r in data], n=5)
    buckets: dict[int, list[tuple[str, float]]] = {}
    for arm, t, c in data:
        buckets.setdefault(sum(c > q for q in qs), []).append((arm, t))
    num = den = 0.0
    strata = 0
    print("  length quintile means (pooled quintiles):")
    for s in sorted(buckets):
        a = [t for arm, t in buckets[s] if arm == ctl]
        h = [t for arm, t in buckets[s] if arm == treat]
        print(f"    q{s+1}: ARM0 n={len(a):>2} {statistics.mean(a) if a else float('nan'):5.2f} | "
              f"ARMM n={len(h):>2} {statistics.mean(h) if h else float('nan'):5.2f}")
        if not a or not h:
            continue
        strata += 1
        d = statistics.mean(h) - statistics.mean(a)
        num += d * len(buckets[s])
        den += len(buckets[s])
    return (num / den if den else None), strata


def describe(label, xs):
    xs = sorted(xs)
    print(f"  {label:<18} n={len(xs):>3} mean={statistics.mean(xs):8.1f} median={statistics.median(xs):8.1f} "
          f"min={xs[0]:8.0f} max={xs[-1]:8.0f}")


def quality() -> dict:
    data = rows()
    print("D8_LENGTH_HELD_CONSTANT_V1")
    print(f"  usable candidates: {len(data)}")
    a = [r for r in data if r[0] == CTL]
    h = [r for r in data if r[0] == TREAT]
    print("\n1. length per arm (characters)")
    describe(CTL, [r[2] for r in a]); describe(TREAT, [r[2] for r in h])
    print(f"  pooled quintile boundaries: {[round(q) for q in statistics.quantiles([r[2] for r in data], n=5)]}")
    print("\n2. does the panel pay for length (pooled)")
    y = [r[1] for r in data]; c = [r[2] for r in data]
    rho = spearman(c, y)
    X = [[1.0, math.log(v)] for v in c]; b = ols(y, X)
    print(f"  Spearman rho(chars, total) = {rho:+.3f}")
    print(f"  total ~ {b[0]:+.2f} {b[1]:+.2f}*log(chars)   R^2 = {r2(y, X, b):.3f}")
    ya, yh = [r[1] for r in a], [r[1] for r in h]
    raw = statistics.mean(yh) - statistics.mean(ya)
    p_raw = perm_p(ya, yh)
    print("\n3. raw gap (ARMM - ARM0, of 15)")
    print(f"  ARM0 mean {statistics.mean(ya):.2f}  ARMM mean {statistics.mean(yh):.2f}  gap {raw:+.3f}  p={p_raw:.4f}")
    print(f"  length gap: ARM0 {statistics.mean([r[2] for r in a]):.0f} -> ARMM {statistics.mean([r[2] for r in h]):.0f} chars  "
          f"p={perm_p([r[2] for r in a], [r[2] for r in h]):.4f}")
    print("\n4. length-adjusted gap  (total ~ 1 + log(chars) + [arm=ARMM])")
    coef, p_adj, rr = arm_term(data, TREAT)
    print(f"  arm coefficient {coef:+.3f} of 15  p={p_adj:.4f}  (model R^2 {rr:.3f})")
    print("\n5. quintile-held gap")
    strat, strata = stratified(data, CTL, TREAT)
    print(f"  strata holding both arms: {strata}   gap: {'UNDEFINED' if strat is None else f'{strat:+.3f}'}")
    # §4 decision rule, verbatim in code.
    floor = len(h) >= 8 and len(a) >= 2 and strata >= 1
    if not floor:
        verdict = "INCONCLUSIVE"
        why = f"floor not met: ARMM usable {len(h)} (need 8), ARM0 usable {len(a)} (need 2), overlapping strata {strata} (need 1)"
    elif raw > 0 and coef > 0 and p_adj < 0.05 and (strat is None or strat > 0):
        verdict, why = "M BETTER", "raw > 0, adjusted > 0 with p < 0.05, quintile-held > 0 or undefined"
    elif raw <= 0 and coef <= 0 and p_adj < 0.05 and (strat is None or strat <= 0):
        verdict, why = "M WORSE", "raw <= 0, adjusted <= 0 with p < 0.05, quintile-held <= 0 or undefined"
    else:
        verdict, why = "INDISTINGUISHABLE", "floor met and neither directional rule fired"
    print(f"\nVERDICT (PREREG_D8 §4 rule): {verdict} -- {why}")
    return {"verdict": verdict, "why": why, "raw_gap": raw, "p_raw": p_raw, "adjusted": coef,
            "p_adjusted": p_adj, "quintile_held": strat, "strata": strata, "rho": rho,
            "n_arm0": len(a), "n_armM": len(h)}


def spend() -> dict:
    sys.path.insert(0, str(HERE.parents[2] / "mini"))
    from minireason.loop import Session

    terminal = json.loads((HERE / "armM" / "ARMM_TERMINAL.json").read_text(encoding="utf-8"))
    session = Session(pathlib.Path(terminal["root"]))
    table: dict[str, dict] = {}

    def add(row, tokens):
        t = table.setdefault(row, {"calls": 0, "tokens": 0})
        t["calls"] += 1; t["tokens"] += int(tokens)

    for e in session.state.events:
        if e.llm is None:
            continue
        ins = list(e.inputs)
        if ins and ins[0] == "mini:record":
            kind = next((i[len("kind:"):] for i in ins if i.startswith("kind:")), "?")
            add({"mini.criticism.v1": "critic", "mini.commitment-proposal.v1": "commitment"}.get(kind, f"record:{kind}"), e.llm.tokens)
        elif ins and ins[0] == "mini:stage-empty":
            add("stage-empty " + " ".join(i for i in ins if i.startswith("stage:")), e.llm.tokens)
        elif ins and ins[0] == "dropped-call":
            add("dropped-call", e.llm.tokens)
        elif (ins and ins[0] in ("all-blocked", "workflow-conjecture-call")) or e.outputs:
            add("conjecturer", e.llm.tokens)
        else:
            add("other:" + ",".join(ins[:2]), e.llm.tokens)
    total = sum(t["tokens"] for t in table.values())
    print("\nD8_PER_SEAT_SPEND_V1  (ARM M, from the record's llm.tokens)")
    print(f"  {'seat':<32} {'calls':>5} {'tokens':>9} {'share':>7}")
    for row in sorted(table, key=lambda r: -table[r]["tokens"]):
        t = table[row]
        print(f"  {row:<32} {t['calls']:>5} {t['tokens']:>9} {t['tokens']/total*100 if total else 0:6.1f}%")
    logged = terminal["logged_tokens_this_run"]
    print(f"  {'TOTAL':<32} {sum(t['calls'] for t in table.values()):>5} {total:>9}")
    print(f"  cross-check: rows sum {total} == logged_tokens_this_run {logged}: {total == logged}; "
          f"meter_equals_log: {terminal['meter_equals_log']}")
    arm0 = json.loads((HERE / "arm0" / "ARM0_RESULT.json").read_text(encoding="utf-8"))
    print(f"  ARM0 (single call x{arm0['k']}): calls {arm0['completed_calls']}  tokens {arm0['total_tokens']}")
    conj = table.get("conjecturer", {}).get("tokens", 0)
    if arm0["total_tokens"]:
        print(f"  ARMM total / ARM0 total = {total/arm0['total_tokens']:.2f}x ; ARMM conjecturer / ARM0 total = {conj/arm0['total_tokens']:.2f}x")
    return {"table": table, "total": total, "cross_check": total == logged, "arm0_total": arm0["total_tokens"]}


def main() -> int:
    out = {"quality": quality(), "spend": spend()}
    (HERE / "ANALYSIS_D8.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
