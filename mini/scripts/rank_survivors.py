#!/usr/bin/env python
"""Offline: rank a creativity run's surviving conjectures with the
calibrated instrument (judge.py) — the substantive question the loop
deliberately does NOT answer. Survivors are shortlisted to a DIVERSE set
(greedy max-min Jaccard, since many survivors are near-duplicate
mechanisms), then run through a pairwise round-robin: cross-family seats,
both presentation orders, verbosity penalty, and the degraded-control
validity gate. Copeland score (wins - losses) ranks them; the run is void
if the control gate fails. Budget-bounded: a BudgetExceeded stops the
tournament and ranks the pairs completed so far.

Usage: DEEPSEEK_API_KEY=... POOLSIDE_API_KEY=... \\
       python mini/scripts/rank_survivors.py [--shortlist 6] [--budget 60000]
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
from minireason.analytics import normalize  # noqa: E402
from minireason.log import BlobStore  # noqa: E402
from minireason.loop import Session  # noqa: E402

RUBRIC = (
    "The problem: explain why a strong LLM's creative novelty decays under "
    "sustained self-conditioning on its own output. A candidate better "
    "satisfies the standard when it names a concrete, mechanistically "
    "specific cause (not a redescription of the symptom), states claims that "
    "identifiable evidence could refute, claims no more than its mechanism "
    "supports, stays internally coherent, and points to checkable evidence."
)


def load_survivors(root: Path) -> list[tuple[str, str, object]]:
    s = Session(root)
    refuted = s.state.refuted
    out = []
    for aid, p in s.state.addr:
        if aid in refuted:
            continue
        text = s.state.artifacts[aid]["content_ref"][len("inline:"):]
        sk = parse_skeleton(text)
        if sk is not None:
            out.append((aid, text, sk))
    return out


def diverse_shortlist(survivors, k: int):
    """Greedy max-min Jaccard distance: start from the most detailed
    candidate, then repeatedly add whichever survivor is most DIFFERENT from
    everything picked so far — so the tournament ranks distinct theories,
    not paraphrase clusters."""
    toks = [normalize(sk.claim + " " + sk.mechanism) for _, _, sk in survivors]

    def dist(i, j):
        a, b = toks[i], toks[j]
        return 1 - len(a & b) / max(1, len(a | b))

    start = max(range(len(survivors)), key=lambda i: len(survivors[i][2].mechanism))
    picked = [start]
    while len(picked) < min(k, len(survivors)):
        cand = max((i for i in range(len(survivors)) if i not in picked),
                   key=lambda i: min(dist(i, j) for j in picked))
        picked.append(cand)
    return [survivors[i] for i in picked]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="runs/mini_creativity")
    parser.add_argument("--shortlist", type=int, default=6)
    parser.add_argument("--budget", type=int, default=60_000)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    args = parser.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1

    survivors = load_survivors(Path(args.root))
    print(f"{len(survivors)} survivors; shortlisting {args.shortlist} diverse ones",
          flush=True)
    short = diverse_shortlist(survivors, args.shortlist)
    labels = {aid: chr(ord("A") + i) for i, (aid, _, _) in enumerate(short)}
    for aid, _, sk in short:
        print(f"  {labels[aid]}: {sk.claim[:80]}", flush=True)

    # flash/default (not pro): the mini's HttpEndpoint has no reasoning-off
    # knob, and pro reasons by default — ~13k tokens/pair and truncated
    # criterion JSON. flash/default certified at 0.0 planted-flaw error, so
    # it is the right cheap seat; laguna adds the cross-family check.
    seats = {
        "flash/default": HttpEndpoint(args.base_url, "deepseek-v4-flash",
                                      api_key=api_key, temperature=0.0,
                                      max_tokens=1500),
    }
    poolside_key = os.environ.get("POOLSIDE_API_KEY")
    if poolside_key:
        seats["laguna-m.1"] = HttpEndpoint(
            "https://inference.poolside.ai/v1", "poolside/laguna-m.1",
            api_key=poolside_key, temperature=0.0, max_tokens=1500)

    meter = TokenMeter(budget=args.budget)
    blobs = BlobStore(Path("runs/mini_rank_blobs"))
    wins = {aid: 0 for aid, _, _ in short}
    losses = {aid: 0 for aid, _, _ in short}
    margins = {aid: [] for aid, _, _ in short}
    pairs_out = []
    stopped = None
    try:
        for (ai, ax, _), (bi, bx, _) in combinations(short, 2):
            row = judge.score_pair(seats, ax, bx, RUBRIC, meter, blobs)
            m = row["margin"]
            pairs_out.append({"x": labels[ai], "y": labels[bi],
                              "margin": m, "point": row["point"]})
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
        # Control: the leader vs its degraded self — validates instrument.
        leader = max(short, key=lambda t: wins[t[0]] - losses[t[0]])
        control = judge.score_pair(seats, leader[1], judge.degrade(leader[1]),
                                   RUBRIC, meter, blobs)
    except BudgetExceeded:
        stopped = "budget"
        control = None
        print("budget exhausted — ranking pairs completed so far", flush=True)

    def score(aid):
        return (wins[aid] - losses[aid],
                round(sum(margins[aid]) / len(margins[aid]), 4) if margins[aid] else 0.0)

    ranking = sorted(short, key=lambda t: score(t[0]), reverse=True)
    gate_pass = bool(control and control["margin"] is not None
                     and control["margin"] >= judge.CONTROL_GATE)

    report = {
        "experiment": "offline instrument ranking of creativity survivors",
        "n_survivors": len(survivors), "shortlist": args.shortlist,
        "seats": list(seats), "stopped": stopped,
        "instrument_valid": gate_pass,
        "control_margin": control["margin"] if control else None,
        "ranking": [
            {"rank": r + 1, "label": labels[aid],
             "copeland": wins[aid] - losses[aid],
             "mean_margin": score(aid)[1],
             "claim": sk.claim, "mechanism": sk.mechanism,
             "artifact": aid[:12]}
            for r, (aid, _, sk) in enumerate(ranking)],
        "pairs": pairs_out,
        "tokens": meter.snapshot(),
    }
    out = MINI.parent / "experiments" / "results" / "mini_creativity_ranking.json"
    out.write_text(json.dumps(report, indent=2) + "\n")

    print(f"\nCONTROL GATE: {'PASS' if gate_pass else 'FAIL/absent'} "
          f"(margin {report['control_margin']}, need >= {judge.CONTROL_GATE})")
    print("\nRANKING (Copeland wins-losses, mean margin):")
    for entry in report["ranking"]:
        print(f"  #{entry['rank']} [{entry['label']}] "
              f"{entry['copeland']:+d} ({entry['mean_margin']:+.3f})  "
              f"{entry['claim'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
