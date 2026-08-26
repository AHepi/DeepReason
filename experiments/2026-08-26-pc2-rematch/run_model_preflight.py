#!/usr/bin/env python3
"""Run P-C1's committed `preflight_models.py` WITHOUT writing into P-C1.

The script writes `preflight_models.json` beside its own `__file__`. Invoking
it in place therefore overwrites P-C1's committed evidence with this run's
catalogue -- which the first P-C2 launch did (`catalogue_size` 19 -> 20),
caught by `git status` and restored with `git checkout`. A committed root's
contents are never edited; a committed TRANCHE's preflight output is the same
kind of thing.

The source is READ AT RUN TIME and executed from this directory, so this is
reuse rather than a copy: the two cannot drift, because there is only one
copy of the logic and it lives in P-C1.
"""
from __future__ import annotations

import pathlib
import runpy
import sys

HERE = pathlib.Path(__file__).resolve().parent
FRONTIER = HERE.parents[1] / "experiments" / "2026-08-25-change-constructive-frontier"
SOURCE = FRONTIER / "preflight_models.py"

shim = HERE / ".preflight_models_shim.py"
shim.write_text(SOURCE.read_text())
sys.path.insert(0, str(FRONTIER))
try:
    sys.argv = [str(shim)]
    runpy.run_path(str(shim), run_name="__main__")
except SystemExit as exit_:
    raise SystemExit(exit_.code)
finally:
    shim.unlink(missing_ok=True)
