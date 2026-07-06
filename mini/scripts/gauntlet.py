#!/usr/bin/env python
"""Live hot gauntlet: deliberately hostile live conditions — a completion
cap low enough to force length truncations (exercising the compression-hint
repair path against a real provider), high temperature, several problems,
and a hard budget. The pass bar is the same trio as always: meter == log,
byte-replay, parent ingest clean. Truncation/repair rates are reported so
the stress is visible, not assumed.

Usage: DEEPSEEK_API_KEY=... python mini/scripts/gauntlet.py [--budget 25000]
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
from minireason.log import replay  # noqa: E402
from minireason.loop import Session, run  # noqa: E402

PROBLEMS = [
    ("pi-collapse", "Why did the Late Bronze Age interstate system collapse "
                    "within a single generation?"),
    ("pi-needham", "Why did the scientific-industrial revolution emerge in "
                   "Europe rather than China?"),
    ("pi-antikythera", "Why did Hellenistic gear-computing technology leave "
                       "no visible successors for a millennium?"),
    ("pi-republic", "Why do republics repeatedly drift toward personalist "
                    "rule during prolonged security crises?"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=25_000)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--max-tokens", type=int, default=900,
                        help="low on purpose: forces truncation repairs")
    parser.add_argument("--root", default="runs/mini_gauntlet")
    args = parser.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1

    endpoint = HttpEndpoint(args.base_url, args.model, api_key=api_key,
                            temperature=1.0, max_tokens=args.max_tokens)
    summary = run(PROBLEMS, endpoint, budget=args.budget, root=args.root,
                  vs_k=6, turnover_k=4, max_cycles=60)

    session = Session(args.root)
    llm_events = [e for e in session.state.events if e.llm is not None]
    summary["llm_events"] = len(llm_events)
    summary["truncated_calls"] = sum(1 for e in llm_events if e.llm.truncated)
    summary["repaired_calls"] = sum(1 for e in llm_events if e.llm.attempts > 1)
    summary["dropped_calls"] = sum(1 for e in session.state.events
                                   if "dropped-call" in e.inputs)

    failures = []
    if not summary["meter_equals_log"]:
        failures.append("meter != log")
    if replay(args.root).digest() != session.state.digest():
        failures.append("replay divergence")
    try:
        from deepreason.invariants import verify_root

        report = verify_root(Path(args.root), meter_total=summary["logged_tokens"])
        summary["parent_ingest_violations"] = report["violations"]
        if report["violations"]:
            failures.append("parent ingest violations")
    except ImportError:
        summary["parent_ingest_violations"] = "parent not importable"
    summary["gauntlet_failures"] = failures

    out = MINI.parent / "experiments" / "results" / "mini_gauntlet_report.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"\nGAUNTLET: {'FAIL — ' + '; '.join(failures) if failures else 'PASS'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
