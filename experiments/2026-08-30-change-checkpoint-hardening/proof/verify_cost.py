"""What re-deriving the replay verdict costs, per committed root.

The integrity gate this tranche adds calls `verify_root` once per `continue`
or `amend`. That cost is the price of the security clause and belongs in
SPEC.md as a number, not an adjective.

    python experiments/2026-08-30-change-checkpoint-hardening/proof/verify_cost.py

Walks committed roots smallest-log-first up to MAX_EVENTS, timing one
`verify_root` each. Writes verify_cost.json beside itself.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "verify_cost.json"
MAX_EVENTS = 300


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    from deepreason.invariants import verify_root

    listing = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    roots = []
    for line in listing:
        if not line.endswith("/log.jsonl"):
            continue
        root = REPO / line[: -len("/log.jsonl")]
        if not (root / "run-status.json").exists():
            continue
        roots.append((sum(1 for _ in (root / "log.jsonl").open()), root))
    roots.sort()
    rows = []
    for events, root in roots:
        if events > MAX_EVENTS:
            break
        started = time.monotonic()
        try:
            verdict = verify_root(root)
            violations = [v.get("check") for v in verdict["violations"]]
            error = None
        except Exception as failure:
            violations = None
            error = f"{type(failure).__name__}: {failure}"
        elapsed = time.monotonic() - started
        row = {
            "root": str(root.relative_to(REPO)),
            "events": events,
            "seconds": round(elapsed, 2),
            "ms_per_event": round(1000 * elapsed / max(events, 1), 1),
            "violations": violations,
            "error": error,
        }
        rows.append(row)
        print(
            f"{row['events']:>5} events  {row['seconds']:>7.2f}s  "
            f"{row['ms_per_event']:>6.1f} ms/event  {row['root']}",
            flush=True,
        )
    OUT.write_text(json.dumps({"max_events": MAX_EVENTS, "rows": rows}, indent=2) + "\n")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
