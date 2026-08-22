"""Equivalence check: the census re-implements reach_sweep's decision tree,
so the census is only evidence if the REAL `reach_sweep` agrees with it.

`reach_sweep` writes (`record_measure`) when it finds anything, and a
committed root must never be written to, so this runs the real function
against a COPY of each root in a scratch directory and compares:

  - the hits it returns (census predicts [] on every current-version root)
  - whether it appended anything to the copy's log (census predicts no
    reach_set / addr+ / reach-provisional event, i.e. no growth at all)

Usage: python verify_sweep_equivalence.py <scratch-dir> <root> [<root>...]
"""

import json
import pathlib
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]


def check(root: pathlib.Path, scratch: pathlib.Path) -> dict:
    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.measures.reach import reach_sweep

    copy = scratch / root.name
    if copy.exists():
        shutil.rmtree(copy)
    shutil.copytree(root, copy)
    before = len((copy / "log.jsonl").read_text().splitlines())
    harness = Harness(copy, read_only=False)
    hits = reach_sweep(harness, coverage_min=Config().REACH_COVERAGE_MIN)
    after = len((copy / "log.jsonl").read_text().splitlines())
    appended = []
    if after > before:
        appended = (copy / "log.jsonl").read_text().splitlines()[before:]
    return {
        "root": str(root.relative_to(REPO)),
        "reach_sweep_hits": hits,
        "log_lines_before": before,
        "log_lines_after": after,
        "appended_events": [json.loads(line) for line in appended],
    }


if __name__ == "__main__":
    scratch = pathlib.Path(sys.argv[1])
    scratch.mkdir(parents=True, exist_ok=True)
    rows = [check(REPO / arg, scratch) for arg in sys.argv[2:]]
    path = pathlib.Path(__file__).with_name("verify_sweep_equivalence.json")
    path.write_text(json.dumps(rows, indent=2) + "\n")
    for row in rows:
        print(f"{row['root']}\n  hits={row['reach_sweep_hits']} "
              f"log {row['log_lines_before']} -> {row['log_lines_after']} "
              f"appended={len(row['appended_events'])}")
    print(f"\nwrote {path}")
