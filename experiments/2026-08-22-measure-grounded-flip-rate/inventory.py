"""Root inventory: which committed roots open under the CURRENT version, and
how big is each one's argument graph. Read-only; opens every root with
``Harness(read_only=True)`` and records nodes / att / dep / baseline labels.

Writes inventory.json next to this file. No root is modified.
"""

import json
import pathlib
import subprocess
import sys
import time
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]


def roots() -> list[pathlib.Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "experiments"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.split("\0")
    return sorted(
        {REPO / p for p in out if p.endswith("/log.jsonl")},
        key=lambda p: str(p),
    )


def main() -> None:
    from deepreason.harness import Harness

    rows = []
    for log in roots():
        root = log.parent
        rel = str(root.relative_to(REPO))
        lines = sum(1 for _ in log.open())
        t0 = time.time()
        try:
            h = Harness(root, read_only=True)
        except Exception as exc:  # noqa: BLE001 - inventory records the refusal
            rows.append({
                "root": rel, "log_lines": lines, "opened": False,
                "error": f"{type(exc).__name__}: {exc}"[:300],
                "open_seconds": round(time.time() - t0, 2),
            })
            print(f"FAIL {rel}: {type(exc).__name__}", file=sys.stderr)
            continue
        secs = round(time.time() - t0, 2)
        att = {tuple(e) for e in h.state.att}
        dep = {tuple(e) for e in h.state.dep}
        nodes = set(h.state.artifacts)
        status = Counter(s.value for s in h.state.status.values())
        rows.append({
            "root": rel, "log_lines": lines, "opened": True,
            "open_seconds": secs,
            "nodes": len(nodes), "att": len(att), "dep": len(dep),
            "status": dict(sorted(status.items())),
        })
        print(f"OK   {rel} n={len(nodes)} att={len(att)} dep={len(dep)} {secs}s",
              file=sys.stderr)
    (HERE / "inventory.json").write_text(json.dumps(rows, indent=2) + "\n")
    ok = [r for r in rows if r["opened"]]
    print(f"\n{len(ok)}/{len(rows)} roots opened; "
          f"total open seconds {sum(r['open_seconds'] for r in rows):.1f}")


if __name__ == "__main__":
    main()
