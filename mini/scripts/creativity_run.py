#!/usr/bin/env python
"""Point MiniReason at its own subject: the creativity of LLM generators.

Two tightly-coupled angles of one open question, drawn from this repo's own
experiment record (docs/BASIN_REPORT.md, the informal A/B stages, the
lambda/rotation studies): why a strong generator's novelty decays under
sustained self-conditioning, and why structural interventions restore it
where adversarial criticism does not. The mini generates skeleton
explanations (claim + mechanism + falsifiable forbidden cases); its own
compiled checks refute the ones that forbid nothing or fail their own
predicates. The survivors are what the mini "believes" — the explanations
it could not kill.

Usage: DEEPSEEK_API_KEY=... python mini/scripts/creativity_run.py [--budget 45000]
"""

import argparse
import json
import os
import sys
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINI))
sys.path.insert(0, str(MINI.parent / "src"))

from minireason.call import HttpEndpoint  # noqa: E402
from minireason.checks import parse_skeleton  # noqa: E402
from minireason.log import replay  # noqa: E402
from minireason.loop import Session, run  # noqa: E402

PROBLEMS = [
    ("pi-novelty-decay",
     "A strong LLM asked to generate many candidate explanations for one "
     "problem produces a diverse first batch, but its novelty decays over a "
     "sustained run: later candidates cluster, paraphrase earlier ones, and "
     "re-propose ideas already set aside. Why does the novelty of an LLM "
     "conjecture generator collapse under sustained self-conditioning on its "
     "own recent output, even at high sampling temperature?"),
    ("pi-restoration",
     "Empirically, cheap structural interventions restore novelty in a "
     "stalling LLM generator — rotating the generation stance, switching to "
     "a different problem, and blocking re-proposals of already-refuted "
     "ideas — while expensive per-candidate adversarial criticism does not "
     "improve the creative output at low base error. Why do structural "
     "interventions on the generator's conditioning outperform adversarial "
     "filtering of its products?"),
]


def render(root: Path) -> str:
    session = Session(root)
    refuted = session.state.refuted
    lines: list[str] = ["# What MiniReason says about LLM creativity\n"]
    for pid, problem in session.state.problems.items():
        lines.append(f"\n## {pid}\n\n> {problem['description']}\n")
        survivors = []
        for aid, p in session.state.addr:
            if p != pid or aid in refuted:
                continue
            text = session.state.artifacts[aid]["content_ref"][len("inline:"):]
            sk = parse_skeleton(text)
            if sk is not None:
                survivors.append((aid, sk))
        lines.append(f"**{len(survivors)} surviving conjectures.**\n")
        for i, (aid, sk) in enumerate(survivors, 1):
            forbid = sk.forbidden[0].case if sk.forbidden else "(none)"
            lines.append(
                f"\n### {i}. {sk.claim}\n\n"
                f"- **Mechanism:** {sk.mechanism}\n"
                f"- **Forbidden (what would refute it):** {forbid}\n"
                f"- `{aid[:12]}`\n")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=45_000)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--root", default="runs/mini_creativity")
    args = parser.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1

    endpoint = HttpEndpoint(args.base_url, args.model, api_key=api_key,
                            temperature=1.0, max_tokens=4000)
    summary = run(PROBLEMS, endpoint, budget=args.budget, root=args.root,
                  vs_k=6, turnover_k=6, stance_decay=5, max_cycles=80)

    # Invariants still hold on a real hard run.
    session = Session(args.root)
    summary["replayable"] = replay(args.root).digest() == session.state.digest()
    try:
        from deepreason.invariants import verify_root
        report = verify_root(Path(args.root), meter_total=summary["logged_tokens"])
        summary["parent_ingest_violations"] = report["violations"]
    except ImportError:
        summary["parent_ingest_violations"] = "parent not importable"

    out_json = MINI.parent / "experiments" / "results" / "mini_creativity_report.json"
    out_json.write_text(json.dumps(summary, indent=2) + "\n")
    prose = render(Path(args.root))
    out_md = MINI.parent / "experiments" / "results" / "mini_creativity_survivors.md"
    out_md.write_text(prose + "\n")

    print(json.dumps(summary, indent=2))
    print("\n" + prose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
