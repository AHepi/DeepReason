"""Shared read-only helpers for the Rung O1 grounded-overlay scripts.

MEASURE ONLY (SPEC.md R5/R6): every overlay script opens a root through
`open_root` below, which always passes `read_only=True` — the one
audited call site every other script imports, instead of five
independent ones that could each drift.
"""

import pathlib

from deepreason.harness import Harness


def corpus() -> list[pathlib.Path]:
    """Every committed root under experiments/, the same corpus
    tools/root_sweep.py already walks (SPEC.md A7)."""
    return sorted({p.parent for p in pathlib.Path("experiments").rglob("log.jsonl")})


def open_root(root: pathlib.Path) -> Harness:
    """The one place any overlay script opens a Harness. Always
    read-only: an overlay script must never create or mutate a root."""
    return Harness(root, read_only=True)


if __name__ == "__main__":
    roots = corpus()
    print(f"{len(roots)} committed root(s) found under experiments/")
