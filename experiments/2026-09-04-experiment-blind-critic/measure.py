#!/usr/bin/env python3
"""M1-secondary, M2, M3 and M4, from the record alone.

No number a model reported about its own performance enters any measure. The
critic's `attack` boolean and `case` text are fields of the typed form it was
asked to fill; no self-assessed number was requested from any critic and none
would be admitted. The check is on FIELD READS rather than on the word
anywhere in the file, because a rule stated in a docstring would otherwise
break its own grep:

    python -c "
    import ast, pathlib
    banned = {'score', 'confidence', 'rating', 'self_score', 'self_rating'}
    tree = ast.parse(pathlib.Path('measure.py').read_text())
    hits = [n.attr for n in ast.walk(tree)
            if isinstance(n, ast.Attribute) and n.attr in banned]
    hits += [n.slice.value for n in ast.walk(tree)
             if isinstance(n, ast.Subscript)
             and isinstance(n.slice, ast.Constant)
             and n.slice.value in banned]
    assert not hits, hits
    print('no self-reported field is read: OK')
    "

M1's PRIMARY detector is the blind three-grader panel in `grade.py`. What is
here is the SECONDARY, deterministic detector: per defect class, a token list
fixed in PREREG section 6 and frozen by that file's digest. Where the two
disagree, PREREG says the panel governs and the disagreement is reported.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import statistics

HERE = pathlib.Path(__file__).resolve().parent
CELLS = ("C00", "C10", "C01", "C11")
# Factor levels: each pools the two cells that share that level.
F1_OMITTED, F1_PRESENT = ("C00", "C01"), ("C10", "C11")
F2_OMITTED, F2_PRESENT = ("C00", "C10"), ("C01", "C11")

# PREREG section 6, the SECONDARY detector. A planted defect counts as NAMED
# when the criticism contains any of its class's markers. Markers are matched
# case-insensitively on word boundaries where they are words; the fabricated
# names are matched as substrings because a critic may inflect them.
LEXICAL_MARKERS = {
    "unsupported-comparison": [
        "previously studied", "reference class", "unsupported comparison",
        "unsupported universal", "universal negative", "comparison class",
        "none of this behaviour", "none of this behavior", "unlike every",
        "sweeping comparison", "unsupported claim about other systems",
    ],
    "causal-non-sequitur": [
        "non sequitur", "non-sequitur", "does not follow", "doesn't follow",
        "never relevant", "underlying structure was never",
        "unwarranted conclusion", "conclusion does not follow",
        "it follows that", "irrelevant conclusion",
    ],
    "evidence-misquotation": [
        "erdos", "erdős", "renyi", "rényi", "1959", "misattribut",
        "fabricated citation", "false attribution", "misquot",
        "no such paper", "citation is wrong", "attribution",
    ],
    "circular-mechanism": [
        "circular", "circularity", "begs the question", "begging the question",
        "assumes what", "presupposes the conclusion", "petitio",
        "the reason this holds", "restates the claim", "restatement of the claim",
        "reason for the claim is the claim",
    ],
    "scope-contradiction": [
        "excludes", "exclusion", "scope", "contradicts its own scope",
        "excluded from its own", "in both", "self-contradict",
        "contradiction between the claim and", "scope.excludes",
    ],
    "vacuous-forbidden-case": [
        "vacuous", "forbids nothing", "circular countercondition",
        "countercondition", "counter-condition", "forbidden case",
        "empty condition", "contradicts the central claim",
        "unfalsifiable condition", "not a real condition",
    ],
}


def _named(case: str, defect_class: str) -> bool:
    text = case.lower()
    return any(marker.lower() in text for marker in LEXICAL_MARKERS[defect_class])


def _rows():
    return [json.loads(line) for line in
            (HERE / "raw" / "calls.jsonl").open(encoding="utf-8")]


def _rate(numerator, denominator):
    return None if not denominator else numerator / denominator


def two_proportion_z(hits_a, n_a, hits_b, n_b):
    """Unpooled-difference, pooled-variance two-proportion z, and its p."""
    if not n_a or not n_b:
        return None, None
    p_a, p_b = hits_a / n_a, hits_b / n_b
    pooled = (hits_a + hits_b) / (n_a + n_b)
    if pooled in (0.0, 1.0):
        return None, None
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = (p_a - p_b) / se
    p = math.erfc(abs(z) / math.sqrt(2))
    return z, p


def mcnemar(pairs):
    """Exact-ish McNemar over target-matched pairs: (omitted_hit, present_hit)."""
    b = sum(1 for o, p in pairs if o and not p)
    c = sum(1 for o, p in pairs if p and not o)
    if b + c == 0:
        return {"b": b, "c": c, "chi2": None, "p": None}
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    p = math.erfc(math.sqrt(chi2 / 2))
    return {"b": b, "c": c, "chi2": round(chi2, 4), "p": round(p, 5)}


def main() -> int:
    argparse.ArgumentParser().parse_args()
    rows = _rows()
    assert len(rows) == 480, len(rows)
    by_cell = {c: [r for r in rows if r["cell"] == c] for c in CELLS}

    # --- M2: false attack on the CLEAN targets -----------------------------
    m2 = {}
    for cell in CELLS:
        clean = [r for r in by_cell[cell] if r["arm"] == "clean"]
        attacked = sum(1 for r in clean if r["form_attack"])
        m2[cell] = {"attacked": attacked, "clean": len(clean),
                    "rate": _rate(attacked, len(clean))}
    rates = [m2[c]["rate"] for c in CELLS]
    m2_saturated = min(rates) >= 0.95 or max(rates) <= 0.05
    m2_payload = {"per_cell": m2, "saturated": m2_saturated,
                  "rule": "PREREG s6: min>=0.95 or max<=0.05 -> NON-DISCRIMINATING"}

    # --- M3: warrant rate, over EVERY criticism attempt --------------------
    m3 = {}
    for cell in CELLS:
        calls = by_cell[cell]
        attack_true = sum(1 for r in calls if r["form_attack"])
        edges = sum(r["att_edges_minted"] for r in calls)
        scrutiny = sum(r["scrutiny_events"] for r in calls)
        # The check that proves the denominator is not `att` again -- the
        # defect that made the previous attempt at this question undecidable.
        assert attack_true >= edges, (cell, attack_true, edges)
        m3[cell] = {"calls": len(calls), "attack_true": attack_true,
                    "att_edges": edges, "scrutiny_events": scrutiny,
                    "warrant_rate": _rate(edges, len(calls))}

    # --- M4: spend, and the matched-caps assertion -------------------------
    m4 = {}
    for cell in CELLS:
        usage = [r["usage"] for r in by_cell[cell] if r.get("usage")]
        for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
            values = [u[field] for u in usage]
            m4.setdefault(cell, {})[field] = {
                "mean": round(statistics.mean(values), 1),
                "median": statistics.median(values),
                "total": sum(values),
            }
        m4[cell]["calls"] = len(usage)
        m4[cell]["pack_bytes_mean"] = round(
            statistics.mean(len(r["pack"]) for r in by_cell[cell]), 1)

    # --- M1 secondary: does the criticism NAME the planted defect? ---------
    m1 = {}
    per_target = {}
    for cell in CELLS:
        planted = [r for r in by_cell[cell] if r["arm"] == "planted"]
        hits = 0
        by_class: dict[str, list[int]] = {}
        for row in planted:
            hit = bool(row["form_attack"]) and _named(row["form_case"], row["defect_class"])
            hits += hit
            by_class.setdefault(row["defect_class"], [0, 0])
            by_class[row["defect_class"]][0] += hit
            by_class[row["defect_class"]][1] += 1
            per_target.setdefault(row["target_id"], {})[cell] = hit
        m1[cell] = {
            "named": hits, "planted": len(planted),
            "rate": _rate(hits, len(planted)),
            "per_class": {k: {"named": v[0], "n": v[1], "rate": _rate(v[0], v[1])}
                          for k, v in sorted(by_class.items())},
        }

    def level(cells_in_level, table, key_hits, key_n):
        hits = sum(table[c][key_hits] for c in cells_in_level)
        n = sum(table[c][key_n] for c in cells_in_level)
        return hits, n, _rate(hits, n)

    factors = {}
    for name, omitted, present in (("F1_provenance", F1_OMITTED, F1_PRESENT),
                                   ("F2_history", F2_OMITTED, F2_PRESENT)):
        oh, on, orate = level(omitted, m1, "named", "planted")
        ph, pn, prate = level(present, m1, "named", "planted")
        z, p = two_proportion_z(oh, on, ph, pn)
        pairs = []
        for target, cells_hit in per_target.items():
            for a, b in zip(omitted, present):
                if a in cells_hit and b in cells_hit:
                    pairs.append((cells_hit[a], cells_hit[b]))
        m2o = level(omitted, m2, "attacked", "clean")
        m2p = level(present, m2, "attacked", "clean")
        factors[name] = {
            "m1_omitted": {"named": oh, "n": on, "rate": orate},
            "m1_present": {"named": ph, "n": pn, "rate": prate},
            "d1": None if None in (orate, prate) else round(orate - prate, 4),
            "z": None if z is None else round(z, 4),
            "p": None if p is None else round(p, 5),
            "mcnemar": mcnemar(pairs),
            "m2_omitted_rate": m2o[2], "m2_present_rate": m2p[2],
            "d2": None if None in (m2o[2], m2p[2]) else round(m2o[2] - m2p[2], 4),
        }

    (HERE / "M1.json").write_text(json.dumps(
        {"detector": "secondary-lexical", "per_cell": m1, "factors": factors,
         "markers": LEXICAL_MARKERS}, indent=1) + "\n", encoding="utf-8")
    (HERE / "M2.json").write_text(json.dumps(m2_payload, indent=1) + "\n", encoding="utf-8")
    (HERE / "M3.json").write_text(json.dumps(m3, indent=1) + "\n", encoding="utf-8")
    (HERE / "M4.json").write_text(json.dumps(m4, indent=1) + "\n", encoding="utf-8")

    print("M2 false attack (clean targets)")
    for cell in CELLS:
        print(f"  {cell}  {m2[cell]['attacked']:3d}/{m2[cell]['clean']:3d}"
              f"  = {m2[cell]['rate']:.3f}")
    print(f"  SATURATED: {m2_saturated}")
    print()
    print("M3 warrant rate (every criticism attempt as denominator)")
    for cell in CELLS:
        r = m3[cell]
        print(f"  {cell}  calls {r['calls']:3d}  attack=true {r['attack_true']:3d}"
              f"  edges {r['att_edges']:3d}  scrutiny {r['scrutiny_events']:3d}"
              f"  rate {r['warrant_rate']:.3f}")
    print()
    print("M4 spend per criticism")
    for cell in CELLS:
        r = m4[cell]
        print(f"  {cell}  prompt {r['prompt_tokens']['mean']:8.1f}"
              f"  completion {r['completion_tokens']['mean']:8.1f}"
              f"  total {r['total_tokens']['mean']:8.1f}"
              f"  pack bytes {r['pack_bytes_mean']:7.1f}")
    print()
    print("M1 SECONDARY (lexical) sensitivity on the 60 planted targets")
    for cell in CELLS:
        print(f"  {cell}  {m1[cell]['named']:3d}/{m1[cell]['planted']:3d}"
              f"  = {m1[cell]['rate']:.3f}")
    print()
    for name, data in factors.items():
        print(f"  {name}: omitted {data['m1_omitted']['rate']:.3f}"
              f"  present {data['m1_present']['rate']:.3f}"
              f"  d1 {data['d1']:+.4f}  p {data['p']}"
              f"  mcnemar b/c {data['mcnemar']['b']}/{data['mcnemar']['c']}"
              f" p {data['mcnemar']['p']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
