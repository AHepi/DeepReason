#!/usr/bin/env python3
"""Run the offline cycle soak on P-A2's launch shape, WITHOUT editing source.

The tranche instruction is explicit: "no source edits, configuration and
ladder only; anything needing a code edit is a FINDING." P-A1 added its case
by editing `scripts/cycle_soak.py`'s CASES registry. That road is closed
here, and it does not need to be open: `cycle_soak.main()` resolves the case
against the module-global `CASES` dict at call time, so a case registered
from THIS file -- which is a tranche deliverable, not source -- reaches it
exactly as a committed row would.

Nothing about the soak's logic, its other cases, or the shape it drives
changes. The case READS this tranche's own run-config.yaml and delegates root
construction to build_manifest_pa2, so the soak drives the launch shape
rather than a restatement of it: a drift in the real config is a drift in the
soak, which is the property the SoakCase docstring exists to protect.

Usage:  python -u soak_pa2.py [--case pa2|hv-grant] [cycle_soak args...]
"""
from __future__ import annotations

import pathlib
import sys

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import cycle_soak  # noqa: E402

cycle_soak.CASES["pa2"] = cycle_soak.SoakCase(
    id="pa2",
    description=(
        "the P-A2 CORRECTED all-modules shape: P-A1's four models across "
        "eleven roles, with the six glm-5.3 seats at reasoning `low` and a "
        "32768 cap, and the split-budget seat protocol OFF. Everything else "
        "-- the explicit defended-trial policy, the grounded two-stage "
        "bridge, route-bound schools, both evidence channels with the raised "
        "simulation budget, the armed config referee and the calibrated "
        "NEAR_DUP_EPS -- is P-A1's, unchanged"
    ),
    config_path=TRANCHE / "run-config.yaml",
    builder="build_manifest_pa2",
    builder_dir=TRANCHE,
    # Same reason P-A1's case gave: the dossier is EMPTY but the CHANNEL is
    # on, and the builder owns that distinction along with the explicit
    # criticism policy, the engaged capability preset and the route-bound
    # control plane. The default root-construction path can express none of
    # them, and an instrument that soaks the wrong shape is worse than no
    # instrument because it reports green.
    attached_evidence=True,
    delegates_to_builder=True,
    # The LAUNCH's own depth and budget, not a sample of them.
    default_cycles=24,
    default_token_budget=3_000_000,
)

if __name__ == "__main__":
    argv = sys.argv[1:] or ["--case", "pa2"]
    raise SystemExit(cycle_soak.main(argv))
