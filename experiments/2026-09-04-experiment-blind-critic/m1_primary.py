#!/usr/bin/env python3
"""M1 PRIMARY, computed after the grades were written: join verdicts to cells.

The keymap was written in the same act as the verdicts and is opened only here.
Nothing in `grade.py` reads it, and nothing that produced a grade could see it.
"""

from __future__ import annotations

import json
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
CELLS = ("C00", "C10", "C01", "C11")
F1_OMITTED, F1_PRESENT = ("C00", "C01"), ("C10", "C11")
F2_OMITTED, F2_PRESENT = ("C00", "C10"), ("C01", "C11")
PLANTED_PER_CELL = 60


def two_proportion_z(hits_a, n_a, hits_b, n_b):
    if not n_a or not n_b:
        return None, None
    pooled = (hits_a + hits_b) / (n_a + n_b)
    if pooled in (0.0, 1.0):
        return None, None
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = (hits_a / n_a - hits_b / n_b) / se
    return z, math.erfc(abs(z) / math.sqrt(2))


def mcnemar(pairs):
    b = sum(1 for o, p in pairs if o and not p)
    c = sum(1 for o, p in pairs if p and not o)
    if b + c == 0:
        return {"b": b, "c": c, "chi2": None, "p": None}
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    return {"b": b, "c": c, "chi2": round(chi2, 4),
            "p": round(math.erfc(math.sqrt(chi2 / 2)), 5)}


def main() -> int:
    import measure

    keymap = json.loads((HERE / "blind" / "keymap.json").read_text())
    verdicts = json.loads((HERE / "blind" / "verdicts.json").read_text())

    per_cell = {c: {"named": 0, "graded": 0, "per_class": {}} for c in CELLS}
    hit_by_target: dict[str, dict[str, bool]] = {}
    for bid, meta in keymap.items():
        if bid not in verdicts:
            continue
        cell, klass = meta["cell"], meta["defect_class"]
        hit = bool(verdicts[bid])
        per_cell[cell]["named"] += hit
        per_cell[cell]["graded"] += 1
        row = per_cell[cell]["per_class"].setdefault(klass, [0, 0])
        row[0] += hit
        row[1] += 1
        hit_by_target.setdefault(meta["target_id"], {})[cell] = hit

    for cell in CELLS:
        data = per_cell[cell]
        # The denominator is the 60 PLANTED targets, not the graded rows: a
        # call that did not attack could not have named anything, and dropping
        # it would inflate the rate by removing its own misses. Every call here
        # attacked, so the two coincide -- asserted rather than assumed.
        assert data["graded"] == PLANTED_PER_CELL, (cell, data["graded"])
        data["planted"] = PLANTED_PER_CELL
        data["rate"] = data["named"] / PLANTED_PER_CELL
        data["per_class"] = {k: {"named": v[0], "n": v[1], "rate": v[0] / v[1]}
                             for k, v in sorted(data["per_class"].items())}

    # Agreement between the two detectors: reported, never reconciled.
    calls = {(r["cell"], r["target_id"]): r for r in measure._rows()}
    agree = disagree = 0
    for bid, meta in keymap.items():
        if bid not in verdicts:
            continue
        call = calls[(meta["cell"], meta["target_id"])]
        lexical = bool(call["form_attack"]) and measure._named(
            call["form_case"], meta["defect_class"])
        agree += lexical == verdicts[bid]
        disagree += lexical != verdicts[bid]

    m2 = json.loads((HERE / "M2.json").read_text())["per_cell"]
    factors = {}
    for name, omitted, present in (("F1_provenance", F1_OMITTED, F1_PRESENT),
                                   ("F2_history", F2_OMITTED, F2_PRESENT)):
        oh = sum(per_cell[c]["named"] for c in omitted)
        on = sum(per_cell[c]["planted"] for c in omitted)
        ph = sum(per_cell[c]["named"] for c in present)
        pn = sum(per_cell[c]["planted"] for c in present)
        z, p = two_proportion_z(oh, on, ph, pn)
        pairs = [(hit_by_target[t][a], hit_by_target[t][b])
                 for t in hit_by_target
                 for a, b in zip(omitted, present)
                 if a in hit_by_target[t] and b in hit_by_target[t]]
        m2o = (sum(m2[c]["attacked"] for c in omitted)
               / sum(m2[c]["clean"] for c in omitted))
        m2p = (sum(m2[c]["attacked"] for c in present)
               / sum(m2[c]["clean"] for c in present))
        factors[name] = {
            "m1_omitted": {"named": oh, "n": on, "rate": round(oh / on, 4)},
            "m1_present": {"named": ph, "n": pn, "rate": round(ph / pn, 4)},
            "d1": round(oh / on - ph / pn, 4),
            "z": None if z is None else round(z, 4),
            "p": None if p is None else round(p, 5),
            "mcnemar": mcnemar(pairs),
            "m2_omitted_rate": m2o, "m2_present_rate": m2p,
            "d2": round(m2o - m2p, 4),
        }

    payload = {"detector": "primary-blind-panel", "per_cell": per_cell,
               "factors": factors,
               "agreement_with_secondary": {
                   "agree": agree, "disagree": disagree,
                   "rate": round(agree / (agree + disagree), 4)}}
    (HERE / "M1_PRIMARY.json").write_text(json.dumps(payload, indent=1) + "\n",
                                          encoding="utf-8")

    print("M1 PRIMARY (blind three-grader panel), 60 planted per cell")
    for cell in CELLS:
        d = per_cell[cell]
        print(f"  {cell}  {d['named']:3d}/{d['planted']:3d} = {d['rate']:.3f}")
    print()
    for name, data in factors.items():
        print(f"  {name}: omitted {data['m1_omitted']['rate']:.3f}"
              f"  present {data['m1_present']['rate']:.3f}"
              f"  d1 {data['d1']:+.4f}  p {data['p']}"
              f"  McNemar b/c {data['mcnemar']['b']}/{data['mcnemar']['c']}"
              f" p {data['mcnemar']['p']}  d2 {data['d2']:+.3f}")
    print()
    a = payload["agreement_with_secondary"]
    print(f"detector agreement: {a['agree']}/{a['agree']+a['disagree']}"
          f" = {a['rate']:.3f}  (disagreement {1 - a['rate']:.3f};"
          f" PREREG falsifier fires above 0.25)")
    print()
    print("per class, per cell:")
    for cell in CELLS:
        row = "  ".join(f"{k.split('-')[0][:9]}:{v['rate']:.2f}"
                        for k, v in per_cell[cell]["per_class"].items())
        print(f"  {cell}  {row}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
