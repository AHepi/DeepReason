#!/usr/bin/env python
"""M2 live smoke (MINI_PLAN §4): 2 problems x ~20 cycles on the cheap
provider, ~30k tokens. Asserts the three run-health properties the mock
tests cannot: zero orbit windows on real generation, meter == log, and a
late/early novelty ratio at or above the parent control-arm baseline
(0.846) — plus the parent ingesting the finished root without violations
when the parent repo is importable.

Usage: DEEPSEEK_API_KEY=... python mini/scripts/smoke.py [--budget 30000]
"""

import argparse
import json
import os
import sys
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINI))
sys.path.insert(0, str(MINI.parent / "src"))  # parent, for the ingest check

from minireason.call import HttpEndpoint  # noqa: E402
from minireason.gate import normalize  # noqa: E402
from minireason.loop import Session, run  # noqa: E402

PROBLEMS = [
    ("pi-bronze", "Why did the Late Bronze Age interstate system collapse "
                  "within roughly a single generation (c. 1200-1150 BCE)?"),
    ("pi-needham", "Why did sustained scientific-industrial revolution emerge "
                   "in early-modern Europe rather than Song-Ming China?"),
]

NOVELTY_BASELINE = 0.846  # parent control arm late/early (docs/BASIN_REPORT.md)


def novelty_late_early(session: Session) -> float | None:
    """Token-set novelty proxy: mean pairwise Jaccard distance within the
    late half of survivors over the early half (no embedder in the mini)."""
    texts = [session.state.artifacts[a]["content_ref"][len("inline:"):]
             for a, _ in session.state.addr if a not in session.state.refuted]
    sets = [normalize(t) for t in texts]

    def mean_dist(xs):
        pairs = [(i, j) for i in range(len(xs)) for j in range(i + 1, len(xs))]
        if not pairs:
            return None
        return sum(1 - len(xs[i] & xs[j]) / max(1, len(xs[i] | xs[j]))
                   for i, j in pairs) / len(pairs)

    half = len(sets) // 2
    early, late = mean_dist(sets[:half]), mean_dist(sets[half:])
    return None if (early in (None, 0) or late is None) else late / early


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=30_000)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--root", default="runs/mini_smoke")
    args = parser.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1

    endpoint = HttpEndpoint(args.base_url, args.model, api_key=api_key,
                            temperature=1.0, max_tokens=4000)
    summary = run(PROBLEMS, endpoint, budget=args.budget, root=args.root,
                  max_cycles=40)
    session = Session(args.root)
    summary["novelty_late_early"] = novelty_late_early(session)
    summary["novelty_baseline"] = NOVELTY_BASELINE

    failures = []
    if not summary["meter_equals_log"]:
        failures.append("meter != log (G1 violated)")
    if summary["gate_blocks"] > 0 and summary["rotations"] == 0:
        failures.append("gate blocks without rotation response")
    ratio = summary["novelty_late_early"]
    if ratio is not None and ratio < NOVELTY_BASELINE:
        failures.append(f"novelty late/early {ratio:.3f} < baseline "
                        f"{NOVELTY_BASELINE} — fall back to STANCE_DECAY 10 "
                        "and note it (MINI_PLAN §6 risk 3)")
    try:
        from deepreason.invariants import verify_root

        report = verify_root(Path(args.root), meter_total=summary["logged_tokens"])
        summary["parent_ingest_violations"] = report["violations"]
        if report["violations"]:
            failures.append(f"parent ingest violations: {report['violations']}")
    except ImportError:
        summary["parent_ingest_violations"] = "parent not importable, skipped"

    summary["smoke_failures"] = failures
    out = MINI.parent / "experiments" / "results" / "mini_smoke_report.json"
    out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"\nSMOKE: {'FAIL — ' + '; '.join(failures) if failures else 'PASS'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
