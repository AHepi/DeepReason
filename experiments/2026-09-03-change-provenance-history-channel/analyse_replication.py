"""The three M1 pairs side by side, and Amendment 5's decision rule applied.

Reports, per pair, the three quantities Amendment 5 registered a direction for
-- tokens per admitted conjecture, blind-judged mean, and mean candidate length
-- and then states REPLICATED / UNRESOLVED / REFUTED for each, by the table
fixed in that amendment before any replicate ran:

    both new pairs agree with the first  -> REPLICATED
    one of two                           -> UNRESOLVED
    neither                              -> REFUTED

The rule is applied mechanically here rather than read off by a human, for the
same reason the aggregation was: a rule applied by hand after seeing the
numbers is not the rule that was registered.

The judged column is absent until blind-r/ is scored; every other column works
from the roots alone, so this can be run the moment the arms land.
"""

from __future__ import annotations

import json
import pathlib
import statistics
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PAIRS = {
    "P1 (original)": {
        "control": "runs/home-m1/runs/run-ad41064484366337ed61a9d5a58de58f",
        "history": "runs/home-m1/runs/run-f23da86ddfd5ab820957221cfebe4b2e",
        "blind": ("blind", {"control": "M1-H0P-control", "history": "M1-H1R-history"}),
    },
    "P2 (replicate)": {
        "control": "runs/home-m1-r2/runs/run-ad41064484366337ed61a9d5a58de58f",
        "history": "runs/home-m1-r2/runs/run-f23da86ddfd5ab820957221cfebe4b2e",
        "blind": ("blind-r", {"control": "R2-H0P-control", "history": "R2-H1R-history"}),
    },
    "P3 (replicate)": {
        "control": "runs/home-m1-r3/runs/run-ad41064484366337ed61a9d5a58de58f",
        "history": "runs/home-m1-r3/runs/run-f23da86ddfd5ab820957221cfebe4b2e",
        "blind": ("blind-r", {"control": "R3-H0P-control", "history": "R3-H1R-history"}),
    },
}


def arm_facts(rel: str) -> dict | None:
    """Admitted seed-problem conjectures, their length, and the run's spend."""
    from measure_diversity_per_problem import conjectures, _seed_problem

    root = HERE / rel
    if not (root / "run-status.json").exists():
        return None
    # A RUNNING arm is not a partial result, it is no result. Without this the
    # table happily prints an arm three minutes into its first cycle beside a
    # finished one and invites the reader to compare them; caught doing exactly
    # that on R3's treatment, which showed as -82.9% conjectures one minute
    # after launch.
    status = json.loads((root / "run-status.json").read_text())
    if status.get("state") != "completed":
        return None
    out = subprocess.run(
        ["deepreason", "results", str(root), "--json"],
        capture_output=True, text=True,
    )
    run = json.loads(out.stdout).get("run", {}) if out.returncode == 0 else {}
    seed = _seed_problem(root)
    claims = [c["claim"] for c in conjectures(root) if c["problem"] == seed]
    spend = run.get("token_spend")
    return {
        "state": run.get("state"),
        "stop_reason": run.get("stop_reason"),
        "cycles": run.get("cycles_completed"),
        "n": len(claims),
        "spend": spend,
        "per_conj": (spend / len(claims)) if spend and claims else None,
        "chars": statistics.mean(len(c) for c in claims) if claims else None,
    }


def judged(blind_dir: str, arm: str) -> float | None:
    b = HERE / blind_dir
    if not (b / "scores.json").exists() or not (b / "keymap.json").exists():
        return None
    scores = json.loads((b / "scores.json").read_text())
    keymap = json.loads((b / "keymap.json").read_text())
    v = [s["median"] for bid, s in scores.items()
         if not s.get("failed") and keymap.get(bid, {}).get("arm") == arm]
    return statistics.mean(v) if v else None


def main() -> int:
    print("M1_REPLICATION_RESULT_V1 -- three pairs, decision rule from PREREG Amendment 5\n")
    rows: dict[str, dict] = {}
    for name, spec in PAIRS.items():
        c, h = arm_facts(spec["control"]), arm_facts(spec["history"])
        if c is None or h is None:
            print(f"{name}: not complete yet\n")
            continue
        bdir, arms = spec["blind"]
        c["judged"], h["judged"] = judged(bdir, arms["control"]), judged(bdir, arms["history"])
        rows[name] = {"control": c, "history": h}
        print(f"{name}")
        print(f"  {'':<22}{'control':>18}{'history':>18}{'change':>10}")
        for label, k, fmt in (
            ("terminal", "stop_reason", "s"),
            ("admitted conjectures", "n", "d"),
            ("tokens spent", "spend", "d"),
            ("tokens per conjecture", "per_conj", "f"),
            ("judged mean of 15", "judged", "f"),
            ("mean chars", "chars", "f"),
        ):
            a, b = c.get(k), h.get(k)
            if fmt == "s":
                print(f"  {label:<22}{str(a):>18}{str(b):>18}")
            elif a is None or b is None:
                print(f"  {label:<22}{'-' if a is None else a:>18}"
                      f"{'-' if b is None else b:>18}{'not scored':>10}")
            else:
                d = (b / a - 1) * 100
                w = f"{a:,.0f}" if fmt == "d" else f"{a:,.2f}"
                x = f"{b:,.0f}" if fmt == "d" else f"{b:,.2f}"
                print(f"  {label:<22}{w:>18}{x:>18}{d:>+9.1f}%")
        print()

    if len(rows) < 3:
        print("Decision rule needs all three pairs; it is not applied on a partial set.")
        return 0

    print("REGISTERED DIRECTIONS, scored by the rule fixed before the replicates ran")
    print("  (each prediction: the history arm is LOWER than its paired control)\n")
    for label, k in (("cost: tokens per conjecture", "per_conj"),
                     ("quality: blind-judged mean", "judged"),
                     ("length: mean chars", "chars")):
        holds = {}
        for name, r in rows.items():
            a, b = r["control"].get(k), r["history"].get(k)
            holds[name] = None if a is None or b is None else b < a
        first = holds["P1 (original)"]
        new = [holds["P2 (replicate)"], holds["P3 (replicate)"]]
        if first is None or any(v is None for v in new):
            verdict = "NOT SCORABLE (a value is missing)"
        else:
            agree = sum(1 for v in new if v == first)
            verdict = {2: "REPLICATED", 1: "UNRESOLVED", 0: "REFUTED"}[agree]
        marks = "  ".join(
            f"{n.split()[0]}={'lower' if v else 'higher' if v is not None else '?'}"
            for n, v in holds.items()
        )
        print(f"  {label:<28} {marks:<46} {verdict}")
    print("\n  No significance test is quoted and none is implied: three paired runs")
    print("  of one question on one model are three observations, not a sample.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
