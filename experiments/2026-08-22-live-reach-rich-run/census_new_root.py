#!/usr/bin/env python3
"""Run the COMMITTED reach census over one root (import shim, not a reader).

The census tranche already owns both passes -- RECORDED (parses log.jsonl
as text; the authority for "did reach fire") and RE-DERIVED (opens the root
with the current reader and attributes every pair to one exit). Rewriting
either here would put a second reader in the record, which is exactly what
the census tranche built its two-pass design to avoid. This file imports
them and points them at one root.

Usage:  python census_new_root.py <root>
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import traceback

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))

CENSUS_PY = REPO / "experiments/2026-08-21-measure-reach-firing/census.py"


def _load_census():
    # census.py reads sys.argv at import time to decide WITH_VERDICTS.
    # Ask for verdicts: E4/E5/HIT is the whole question here.
    saved = sys.argv
    sys.argv = [str(CENSUS_PY), "--verdicts"]
    try:
        spec = importlib.util.spec_from_file_location("reach_census", CENSUS_PY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.argv = saved


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: census_new_root.py <root>", file=sys.stderr)
        return 2
    root = pathlib.Path(sys.argv[1])
    census = _load_census()
    entry = {"root": str(root), "recorded": census.recorded_census(root)}
    try:
        entry["rederived"] = census.rederived_census(root)
        entry["opens"] = True
    except Exception as error:  # noqa: BLE001 - a reader refusal is a result
        entry["opens"] = False
        entry["open_error"] = f"{type(error).__name__}: {error}"
        entry["open_traceback"] = traceback.format_exc().splitlines()[-3:]

    out = TRANCHE / "reach-census.json"
    out.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n")
    rec = entry["recorded"]
    print(f"root                         {root}")
    print(f"recorded reach_set events    {rec.get('reach_set_events', 0)}")
    print(f"recorded addr pairs          {rec.get('measure_addr_pairs', 0)}")
    print(f"recorded reach-provisional   {rec.get('reach_provisional_events', 0)}")
    if entry["opens"]:
        for key, value in sorted(entry["rederived"].items()):
            if not key.startswith("_") and isinstance(value, int):
                print(f"  {key:34} {value}")
    else:
        print(f"  OUT OF SCOPE: {entry['open_error'][:120]}")
    print(f"\nwrote {out}")
    # Exit 0 iff the run actually recorded reach -- the tranche's success
    # criterion, decided by the record and nothing else.
    return 0 if rec.get("reach_set_events", 0) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
