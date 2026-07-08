#!/usr/bin/env python
"""Round 2 — ask the harness (ONLY deepseek-v4-pro, thinking OFF) HOW to
implement round 1's recommendations WITHOUT breaking the spec's
conjecture-refutation loop.

Round 1 (ask_harness_10b_report.json) proposed why a ~10B model can't run
the harness solo and what to change. This round hands those ranked
recommendations back to the harness and asks for concrete implementations
that respect the spec's non-negotiable invariants (harness-spec-v1.3.md
§0, §5, §8): the LLM is a bounded pure function pack -> schema-validated
JSON — it must not hold graph state, adjudicate, or control flow; the
harness is deterministic and byte-exactly replayable; every refutation is
a logged warrant inside Conj->Crit->Adj; measures never adjudicate.

Budget: 700k tokens total (gen 650k + rank 50k), pro thinking-off. The
survivors are proposed IMPLEMENTATIONS (hypotheses), not findings.

Usage: DEEPSEEK_API_KEY=... python mini/scripts/ask_harness_impl.py
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

from ask_harness_10b import diverse_shortlist  # noqa: E402
from small_model_repair import ReasoningOffEndpoint  # noqa: E402

PID = "pi-10b-impl-within-spec"
DESCRIPTION = (
    "A prior conjecture round proposed why a ~10B model cannot run this "
    "conjecture-criticism harness unaided and what to change. Its surviving, "
    "top-ranked recommendations were: "
    "(R1) single-pass generation of a deeply nested JSON skeleton is "
    "incompatible with the small model's token-level decoding — it has no "
    "stack to track nesting depth, so it loses brace/quote bookkeeping; "
    "(R2) the self-falsifying 'forbidden' cases force the model to simulate "
    "an adversary against its own claim in one pass, which it cannot reliably "
    "do; "
    "(R3) the inner predicate strings lack syntactic anchoring, so the model "
    "defaults to JavaScript / undefined functions instead of Python over the "
    "content string. "
    "NOW THE CONSTRAINT: any implementation MUST respect the harness spec's "
    "invariants (harness-spec-v1.3.md). The LLM is a BOUNDED PURE FUNCTION "
    "pack -> schema-validated JSON (Def 4.1): it MUST NOT hold graph state, "
    "adjudicate, or control flow — it is only the conjecture operator gamma. "
    "The harness is DETERMINISTIC and its event log must replay BYTE-EXACTLY. "
    "Every refutation is a logged Crit warrant (demonstrative or rubric) with "
    "a validity node, resolved by grounded semantics; MEASURES NEVER "
    "ADJUDICATE (a measurement may not change an artifact's status). Program "
    "checks compiled from a candidate's own forbidden cases are the free, "
    "judge-token-free refutation path and must stay pure functions of "
    "content. "
    "The question: give a CONCRETE implementation of R1, R2, and/or R3 — a "
    "change to the output contract, the gamma-call prompting/decoding, or the "
    "criticism protocol — that a ~10B model could execute end to end UNAIDED "
    "(no stronger model, no external repair), WITHOUT violating any invariant "
    "above. A good answer names the exact mechanism and the spec obligation it "
    "preserves, says where in the loop it sits, and states what evidence or "
    "consistency argument would refute it.")

RUBRIC = (
    "The problem: a concrete implementation of round 1's recommendations (R1 "
    "nested-JSON stack failure, R2 self-falsification burden, R3 predicate "
    "language) that a ~10B model runs UNAIDED while respecting the harness "
    "spec. A candidate better satisfies the standard when it (1) gives a "
    "concrete, buildable mechanism (a contract shape, a decoding constraint, "
    "a prompt/render change, or a criticism-protocol step) rather than a "
    "restatement; (2) keeps the LLM a bounded pure function pack -> schema-"
    "validated JSON — no graph state, no adjudication, no control flow in the "
    "model; (3) preserves determinism and byte-exact event-log replay; (4) "
    "expresses any new criticism as a logged warrant inside Conj->Crit->Adj "
    "with measures-never-adjudicate intact, keeping program checks pure "
    "functions of content; (5) is refutable and claims no more than its "
    "mechanism supports.")


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
    lines = ["# The harness's own proposals: implementing the 10B fixes "
             "within the spec\n",
             "**Engine: deepseek-v4-pro, thinking OFF. Surviving CONJECTURES "
             "(each states what would refute it) — proposed implementations, "
             "not validated findings.**\n",
             f"\n**{len(survivors)} surviving conjectures.**\n"]
    for i, (aid, _, sk) in enumerate(survivors, 1):
        forbid = sk.forbidden[0].case if sk.forbidden else "(none)"
        lines.append(f"\n### {i}. {sk.claim}\n\n"
                     f"- **Mechanism:** {sk.mechanism}\n"
                     f"- **Would be refuted by:** {forbid}\n- `{aid[:12]}`\n")
    return "\n".join(lines), survivors


def rank(survivors, seats, budget, shortlist):
    short = diverse_shortlist(survivors, shortlist)
    labels = {aid: chr(ord("A") + i) for i, (aid, _, _) in enumerate(short)}
    meter = TokenMeter(budget=budget)
    blobs = BlobStore(Path("runs/askimpl_rank_blobs"))
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
                     "mechanism": sk.mechanism, "forbidden":
                     (sk.forbidden[0].case if sk.forbidden else None),
                     "artifact": a[:12]}
                    for r, (a, _, sk) in enumerate(order)],
        "tokens": meter.snapshot(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen-budget", type=int, default=650_000)
    parser.add_argument("--rank-budget", type=int, default=50_000)
    parser.add_argument("--shortlist", type=int, default=6)
    parser.add_argument("--root", default="runs/askimpl_pro")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    args = parser.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1

    gen = ReasoningOffEndpoint(args.base_url, "deepseek-v4-pro", api_key=api_key,
                               temperature=1.0, max_tokens=4000)
    summary = run([(PID, DESCRIPTION)], gen, budget=args.gen_budget,
                  root=args.root, vs_k=6, turnover_k=12, stance_decay=5,
                  max_cycles=400)
    s = Session(args.root)
    summary["replayable"] = replay(args.root).digest() == s.state.digest()
    try:
        from deepreason.invariants import verify_root
        summary["parent_ingest_violations"] = verify_root(
            Path(args.root), meter_total=summary["logged_tokens"])["violations"]
    except ImportError:
        summary["parent_ingest_violations"] = "parent not importable"

    prose, survivors = render(Path(args.root))
    (MINI.parent / "experiments" / "results" / "ask_harness_impl_survivors.md").write_text(prose + "\n")

    seats = {"pro/thinking-off": ReasoningOffEndpoint(
        args.base_url, "deepseek-v4-pro", api_key=api_key,
        temperature=0.0, max_tokens=1500)}
    ranking = rank(survivors, seats, args.rank_budget, args.shortlist) if survivors else {}

    report = {"problem": PID, "engine": "deepseek-v4-pro (thinking OFF only)",
              "round": 2, "prior_round": "ask_harness_10b_report.json",
              "description": DESCRIPTION, "run": summary, "ranking": ranking,
              "note": "surviving conjectures are proposed implementations "
                      "(hypotheses), not validated findings (SELF_IMPROVEMENT §1.5)"}
    (MINI.parent / "experiments" / "results" / "ask_harness_impl_report.json").write_text(
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
