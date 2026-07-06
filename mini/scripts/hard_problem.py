#!/usr/bin/env python
"""Run MiniReason end-to-end on ONE hard problem, then rank its survivors
with the calibrated offline instrument — the full pipeline in one job, for
head-to-head comparison against a human/other-model answer.

Phase 1 (loop): generate skeleton conjectures, refute mechanically for free.
Phase 2 (offline): shortlist a DIVERSE set of survivors and run a pairwise
round-robin (cross-family certified seats, both orders, degraded-control
validity gate). Both phases are budget-bounded and log-clean; invariants are
re-checked on the live root.

Usage: DEEPSEEK_API_KEY=... POOLSIDE_API_KEY=... \\
       python mini/scripts/hard_problem.py [--gen-budget 35000] [--rank-budget 45000]
"""

import argparse
import json
import os
import sys
from itertools import combinations
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINI))
sys.path.insert(0, str(MINI.parent / "src"))

from minireason import judge  # noqa: E402
from minireason.call import BudgetExceeded, HttpEndpoint, TokenMeter  # noqa: E402
from minireason.checks import parse_skeleton  # noqa: E402
from minireason.gate import normalize  # noqa: E402
from minireason.log import BlobStore, replay  # noqa: E402
from minireason.loop import Session, run  # noqa: E402

PID = "pi-arrow-of-time"
DESCRIPTION = (
    "The microphysical laws are essentially time-symmetric (CPT-invariant), "
    "yet time has a robust thermodynamic direction: entropy rises toward the "
    "future, we remember the past not the future, causes precede effects. "
    "Why does a temporal arrow exist at all, given time-symmetric dynamics, "
    "and what fixes its direction? A good answer must confront the "
    "reversibility objection: symmetric dynamics plus symmetric statistics "
    "cannot by themselves prefer a direction.")

RUBRIC = (
    "The problem: explain why a thermodynamic arrow of time exists given "
    "time-symmetric microphysical laws, and what fixes its direction. A "
    "candidate better satisfies the standard when it (1) locates the "
    "asymmetry precisely (in laws vs. boundary/initial conditions vs. "
    "statistics), (2) confronts the reversibility/Loschmidt objection that "
    "symmetric dynamics + symmetric statistics cannot pick a direction, "
    "(3) names a concrete mechanism rather than restating the phenomenon, "
    "(4) makes claims that evidence or a consistency argument could refute, "
    "and (5) claims no more than its mechanism supports.")


def render(root: Path) -> tuple[str, list]:
    s = Session(root)
    refuted = s.state.refuted
    survivors = []
    for aid, p in s.state.addr:
        if p != PID or aid in refuted:
            continue
        text = s.state.artifacts[aid]["content_ref"][len("inline:"):]
        sk = parse_skeleton(text)
        if sk is not None:
            survivors.append((aid, text, sk))
    lines = [f"# MiniReason on the arrow of time\n\n> {DESCRIPTION}\n",
             f"**{len(survivors)} surviving conjectures.**\n"]
    for i, (aid, _, sk) in enumerate(survivors, 1):
        forbid = sk.forbidden[0].case if sk.forbidden else "(none)"
        lines.append(f"\n### {i}. {sk.claim}\n\n"
                     f"- **Mechanism:** {sk.mechanism}\n"
                     f"- **Forbidden:** {forbid}\n- `{aid[:12]}`\n")
    return "\n".join(lines), survivors


def diverse_shortlist(survivors, k):
    toks = [normalize(sk.claim + " " + sk.mechanism) for _, _, sk in survivors]

    def dist(i, j):
        return 1 - len(toks[i] & toks[j]) / max(1, len(toks[i] | toks[j]))

    start = max(range(len(survivors)), key=lambda i: len(survivors[i][2].mechanism))
    picked = [start]
    while len(picked) < min(k, len(survivors)):
        picked.append(max((i for i in range(len(survivors)) if i not in picked),
                          key=lambda i: min(dist(i, j) for j in picked)))
    return [survivors[i] for i in picked]


def rank(survivors, seats, budget, shortlist):
    short = diverse_shortlist(survivors, shortlist)
    labels = {aid: chr(ord("A") + i) for i, (aid, _, _) in enumerate(short)}
    meter = TokenMeter(budget=budget)
    blobs = BlobStore(Path("runs/mini_hard_rank_blobs"))
    wins = {a: 0 for a, _, _ in short}
    losses = {a: 0 for a, _, _ in short}
    margins = {a: [] for a, _, _ in short}
    control = None
    stopped = None
    try:
        for (ai, ax, _), (bi, bx, _) in combinations(short, 2):
            row = judge.score_pair(seats, ax, bx, RUBRIC, meter, blobs)
            m = row["margin"]
            if m is not None:
                margins[ai].append(m)
                margins[bi].append(-m)
                if row["point"] == "harness":
                    wins[ai] += 1
                    losses[bi] += 1
                elif row["point"] == "solo":
                    wins[bi] += 1
                    losses[ai] += 1
            print(f"  {labels[ai]} vs {labels[bi]}: {row['point']} "
                  f"(margin {m}, spent {meter.total})", flush=True)
        leader = max(short, key=lambda t: wins[t[0]] - losses[t[0]])
        control = judge.score_pair(seats, leader[1], judge.degrade(leader[1]),
                                   RUBRIC, meter, blobs)
    except BudgetExceeded:
        stopped = "budget"
        print("  rank budget exhausted — ranking pairs so far", flush=True)

    def sc(a):
        return (wins[a] - losses[a],
                round(sum(margins[a]) / len(margins[a]), 4) if margins[a] else 0.0)

    order = sorted(short, key=lambda t: sc(t[0]), reverse=True)
    gate = bool(control and control["margin"] is not None
                and control["margin"] >= judge.CONTROL_GATE)
    return {
        "instrument_valid": gate, "stopped": stopped,
        "control_margin": control["margin"] if control else None,
        "ranking": [{"rank": r + 1, "label": labels[a], "copeland": wins[a] - losses[a],
                     "mean_margin": sc(a)[1], "claim": sk.claim,
                     "mechanism": sk.mechanism, "artifact": a[:12]}
                    for r, (a, _, sk) in enumerate(order)],
        "tokens": meter.snapshot(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen-budget", type=int, default=35_000)
    parser.add_argument("--rank-budget", type=int, default=45_000)
    parser.add_argument("--shortlist", type=int, default=5)
    parser.add_argument("--root", default="runs/mini_arrow")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    args = parser.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1

    gen = HttpEndpoint(args.base_url, "deepseek-v4-flash", api_key=api_key,
                       temperature=1.0, max_tokens=4000)
    summary = run([(PID, DESCRIPTION)], gen, budget=args.gen_budget,
                  root=args.root, vs_k=6, turnover_k=8, stance_decay=5,
                  max_cycles=80)
    s = Session(args.root)
    summary["replayable"] = replay(args.root).digest() == s.state.digest()
    try:
        from deepreason.invariants import verify_root
        summary["parent_ingest_violations"] = verify_root(
            Path(args.root), meter_total=summary["logged_tokens"])["violations"]
    except ImportError:
        summary["parent_ingest_violations"] = "parent not importable"

    prose, survivors = render(Path(args.root))
    (MINI.parent / "experiments" / "results" / "mini_arrow_survivors.md").write_text(prose + "\n")

    seats = {"flash/default": HttpEndpoint(args.base_url, "deepseek-v4-flash",
                                           api_key=api_key, temperature=0.0, max_tokens=1500)}
    poolside_key = os.environ.get("POOLSIDE_API_KEY")
    if poolside_key:
        seats["laguna-m.1"] = HttpEndpoint("https://inference.poolside.ai/v1",
                                           "poolside/laguna-m.1", api_key=poolside_key,
                                           temperature=0.0, max_tokens=1500)
    ranking = rank(survivors, seats, args.rank_budget, args.shortlist) if survivors else {}

    report = {"problem": PID, "description": DESCRIPTION, "run": summary,
              "ranking": ranking}
    (MINI.parent / "experiments" / "results" / "mini_arrow_report.json").write_text(
        json.dumps(report, indent=2) + "\n")

    print(json.dumps({"run": summary, "control_gate": ranking.get("instrument_valid"),
                      "control_margin": ranking.get("control_margin")}, indent=2))
    print("\n" + prose)
    if ranking:
        print(f"\nCONTROL GATE: {'PASS' if ranking['instrument_valid'] else 'FAIL/absent'} "
              f"(margin {ranking['control_margin']})")
        print("RANKING (Copeland, mean margin):")
        for e in ranking["ranking"]:
            print(f"  #{e['rank']} [{e['label']}] {e['copeland']:+d} "
                  f"({e['mean_margin']:+.3f})  {e['claim'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
