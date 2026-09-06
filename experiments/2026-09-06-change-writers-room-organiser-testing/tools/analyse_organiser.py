"""The verdict, by PREREG.md §6-§7's rule, and nothing else. Run only AFTER
`judge_organiser.py reveal` -- it reads the keymap.

    python analyse_organiser.py [--json OUT]

Why this is not D8's regression: the judged unit is a run's COMPOSED result,
so each harness arm contributes ONE unit (three judge readings), and ARM 0
contributes three essays. D8's length-adjusted regression and quintile
strata need a distribution of candidates per arm and are unidentified on one
point; keeping them here would print a coefficient nobody should read. So
the pre-registered control is a RATIO with a downgrade, stated in §6: a
pairwise BETTER whose better unit is more than 1.5 times the other's length
is reported as NULL (length-uncontrolled), never as BETTER. Length is
reported for every unit either way.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics

HERE = pathlib.Path(__file__).resolve().parent
BLIND = HERE.parent / "blind"
ARM0, ARMH, ARMR = "ARM0-single-call", "ARMH-harness", "ARMR-organiser"
MARGIN = 2.0          # of 15, PREREG §7
LENGTH_RATIO = 1.5    # PREREG §6


def units() -> dict[str, list[dict]]:
    scores = json.loads((BLIND / "scores.json").read_text())
    keymap = json.loads((BLIND / "keymap.json").read_text())
    text = {
        json.loads(l)["bid"]: json.loads(l)["text"]
        for l in (BLIND / "candidates.jsonl").read_text().splitlines()
        if l.strip()
    }
    out: dict[str, list[dict]] = {}
    for bid, s in scores.items():
        if s.get("failed"):
            continue
        out.setdefault(keymap[bid]["arm"], []).append(
            {"bid": bid, "source": keymap[bid]["source"], "median": float(s["median"]),
             "min": float(min(s["totals"])), "max": float(max(s["totals"])),
             "contested": bool(s.get("contested")), "chars": len(text[bid])}
        )
    return out


def arm_summary(rows: list[dict]) -> dict:
    """An arm's score is the median of its units' medians (ARM 0 has three
    units; a harness arm has one, so its score is that unit's median)."""
    return {
        "n_units": len(rows),
        "score": statistics.median(r["median"] for r in rows),
        "worst_judge": min(r["min"] for r in rows),
        "chars": statistics.median(r["chars"] for r in rows),
        "contested_units": sum(r["contested"] for r in rows),
    }


def pairwise(treat: dict, control: dict, label: str) -> dict:
    """§7: BETTER iff treat.score - control.score >= MARGIN; WORSE iff
    control.score - treat.score >= MARGIN; else NULL. §6: a BETTER whose
    better unit is > LENGTH_RATIO times the other's length is downgraded to
    NULL (length-uncontrolled); the mirror holds for WORSE."""
    gap = treat["score"] - control["score"]
    ratio = treat["chars"] / control["chars"] if control["chars"] else float("inf")
    if gap >= MARGIN:
        verdict = "BETTER"
        if ratio > LENGTH_RATIO:
            verdict = "NULL (length-uncontrolled)"
    elif -gap >= MARGIN:
        verdict = "WORSE"
        if ratio < 1 / LENGTH_RATIO:
            verdict = "NULL (length-uncontrolled)"
    else:
        verdict = "NULL"
    return {"pair": label, "gap": gap, "length_ratio": ratio, "verdict": verdict}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    by_arm = units()
    print("ORGANISER_VERDICT_V1  (median of 3 judges per unit, 0-15)")
    summaries = {}
    for arm in (ARM0, ARMH, ARMR):
        rows = by_arm.get(arm, [])
        if not rows:
            print(f"  {arm:<18} n=0  -- no usable unit")
            continue
        summaries[arm] = arm_summary(rows)
        s = summaries[arm]
        print(f"  {arm:<18} units={s['n_units']}  score={s['score']:.1f}  worst judge={s['worst_judge']:.0f}  "
              f"chars={s['chars']:.0f}  contested={s['contested_units']}")
        for r in rows:
            print(f"      {r['source']:<24} median={r['median']:.1f} [{r['min']:.0f}..{r['max']:.0f}] chars={r['chars']}")
    result: dict = {"schema": "organiser-verdict.v1", "arms": summaries}
    if any(arm not in summaries for arm in (ARM0, ARMH, ARMR)):
        result["verdict"] = "INCONCLUSIVE"
        result["why"] = "an arm has no usable unit (§7 floor)"
    else:
        r0 = pairwise(summaries[ARMR], summaries[ARM0], "R vs 0")
        rh = pairwise(summaries[ARMR], summaries[ARMH], "R vs H")
        h0 = pairwise(summaries[ARMH], summaries[ARM0], "H vs 0 (reported, not part of the rule)")
        result["pairs"] = [r0, rh, h0]
        for p in (r0, rh, h0):
            print(f"  {p['pair']:<40} gap={p['gap']:+.1f}  length ratio={p['length_ratio']:.2f}  -> {p['verdict']}")
        if r0["verdict"] == "BETTER" and rh["verdict"] == "BETTER":
            result["verdict"], result["why"] = "ARM R MATERIALLY BETTER", "better than BOTH ARM 0 and ARM H under §7, length within §6"
        elif "WORSE" in (r0["verdict"], rh["verdict"]):
            result["verdict"], result["why"] = "ARM R WORSE", "worse than ARM 0 or ARM H under §7"
        else:
            result["verdict"], result["why"] = "NULL", "not better than both under §7 (or a BETTER was length-uncontrolled under §6)"
    print(f"\nVERDICT (PREREG §7): {result['verdict']} -- {result['why']}")
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
