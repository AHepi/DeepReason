#!/usr/bin/env python
"""Ask the harness — running on ONLY deepseek-v4-pro with thinking OFF —
for solutions to: how can a ~10B model run this harness entirely on its
own (no stronger model in the loop)?

This is the repo's self-referential move (the creativity/criticism-design
runs did the same): point MiniReason at a question about its own design.
pro-thinking-off is the conjecturer AND the single ranking seat (the
record certifies pro reasoning-off at 0.0 flaw error). The surviving
conjectures are HYPOTHESES the harness proposes, never findings — each
carries its own falsification condition (forbidden cases).

Usage: DEEPSEEK_API_KEY=... python mini/scripts/ask_harness_10b.py
       [--gen-budget 60000] [--rank-budget 40000]
"""

import argparse
import json
import os
import sys
from itertools import combinations
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINI))
sys.path.insert(0, str(MINI / "scripts"))
sys.path.insert(0, str(MINI.parent / "src"))

from minireason import judge  # noqa: E402
from minireason.call import BudgetExceeded, TokenMeter  # noqa: E402
from minireason.checks import parse_skeleton  # noqa: E402
from minireason.gate import normalize  # noqa: E402
from minireason.log import BlobStore, replay  # noqa: E402
from minireason.loop import Session, run  # noqa: E402

from small_model_repair import ReasoningOffEndpoint  # noqa: E402

PID = "pi-10b-solo-harness"
DESCRIPTION = (
    "A reasoning harness requires each model turn to emit a strict nested-JSON "
    "'skeleton': a claim, a mechanism, a scope, and one or more self-"
    "falsifying 'forbidden' cases whose checks are Python predicate expressions "
    "over the raw content string (e.g. len(content) > 10). Measured on a real "
    "~10B/12B model, it fails to run this harness unaided: (1) malformed nested "
    "JSON — premature object close before the last field, missing delimiters, "
    "unescaped inner quotes, smart quotes; (2) predicates in the WRONG language "
    "— JavaScript (content.mechanism.includes(...)) or calls to undefined "
    "functions, which error under Python eval and self-refute the candidate; "
    "(3) token degradation at high temperature — garbled/hallucinated tokens. "
    "A larger model repairing the output is DISALLOWED: the ~10B model must run "
    "the harness entirely on its own. Why does a small model fail to satisfy a "
    "self-criticizing structured-output contract unaided, and what changes to "
    "the harness's OWN design — its output contract, its prompting, its "
    "decoding constraints, or its criticism protocol — would let a ~10B model "
    "run it end to end with no stronger model in the loop? A good answer names "
    "a concrete mechanism, locates the fix in the harness rather than the "
    "model, and states what evidence would refute it.")

RUBRIC = (
    "The problem: what harness-side change lets a ~10B model satisfy a "
    "self-criticizing nested-JSON contract entirely on its own. A candidate "
    "better satisfies the standard when it (1) locates the failure precisely "
    "(output-contract complexity vs prompt vs decoding vs criticism protocol), "
    "(2) proposes a concrete harness-side mechanism a ~10B model could execute "
    "unaided — not 'use a bigger model' and not an external repair pass, "
    "(3) confronts the measured failure modes (malformed nested JSON, "
    "wrong-language predicates, temperature degradation) rather than restating "
    "them, (4) makes a claim that evidence could refute, and (5) claims no "
    "more than its mechanism supports.")


def render(root: Path):
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
    lines = ["# The harness's own proposals: how a ~10B model runs it solo\n",
             f"> {DESCRIPTION}\n",
             "**Engine: deepseek-v4-pro, thinking OFF. These are surviving "
             "CONJECTURES (each states what would refute it), not findings.**\n",
             f"\n**{len(survivors)} surviving conjectures.**\n"]
    for i, (aid, _, sk) in enumerate(survivors, 1):
        forbid = sk.forbidden[0].case if sk.forbidden else "(none)"
        lines.append(f"\n### {i}. {sk.claim}\n\n"
                     f"- **Mechanism:** {sk.mechanism}\n"
                     f"- **Would be refuted by:** {forbid}\n- `{aid[:12]}`\n")
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
    blobs = BlobStore(Path("runs/ask10b_rank_blobs"))
    wins = {a: 0 for a, _, _ in short}
    losses = {a: 0 for a, _, _ in short}
    margins = {a: [] for a, _, _ in short}
    control, stopped = None, None
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
        print("  rank budget exhausted", flush=True)

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
    parser.add_argument("--gen-budget", type=int, default=60_000)
    parser.add_argument("--rank-budget", type=int, default=40_000)
    parser.add_argument("--shortlist", type=int, default=5)
    parser.add_argument("--root", default="runs/ask10b_pro")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    args = parser.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1

    # ONLY v4-pro, thinking OFF — generator and (single) ranking seat.
    gen = ReasoningOffEndpoint(args.base_url, "deepseek-v4-pro", api_key=api_key,
                               temperature=1.0, max_tokens=4000)
    summary = run([(PID, DESCRIPTION)], gen, budget=args.gen_budget,
                  root=args.root, vs_k=6, turnover_k=10, stance_decay=5,
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
    (MINI.parent / "experiments" / "results" / "ask_harness_10b_survivors.md").write_text(prose + "\n")

    seats = {"pro/thinking-off": ReasoningOffEndpoint(
        args.base_url, "deepseek-v4-pro", api_key=api_key,
        temperature=0.0, max_tokens=1500)}
    ranking = rank(survivors, seats, args.rank_budget, args.shortlist) if survivors else {}

    report = {"problem": PID, "engine": "deepseek-v4-pro (thinking OFF only)",
              "description": DESCRIPTION, "run": summary, "ranking": ranking,
              "note": "surviving conjectures are hypotheses proposed by the "
                      "harness, not validated findings (SELF_IMPROVEMENT §1.5)"}
    (MINI.parent / "experiments" / "results" / "ask_harness_10b_report.json").write_text(
        json.dumps(report, indent=2) + "\n")

    print(json.dumps({"run": summary, "survivors": len(survivors),
                      "control_gate": ranking.get("instrument_valid"),
                      "control_margin": ranking.get("control_margin")}, indent=2))
    print("\n" + prose)
    if ranking:
        print(f"\nCONTROL GATE: {'PASS' if ranking['instrument_valid'] else 'FAIL/absent'} "
              f"(margin {ranking['control_margin']})")
        print("RANKING (Copeland, mean margin):")
        for e in ranking["ranking"]:
            print(f"  #{e['rank']} [{e['label']}] {e['copeland']:+d} "
                  f"({e['mean_margin']:+.3f})  {e['claim'][:72]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
