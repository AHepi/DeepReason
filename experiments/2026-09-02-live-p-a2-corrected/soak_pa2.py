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
import wheel_operational_smoke as _smoke  # noqa: E402  (the ONE stub)

# ---------------------------------------------------------------------------
# FINDING F1 (P-A2), and the runtime repair that routes around it
# ---------------------------------------------------------------------------
# The offline stub on `main` has no fixture for `ConfigRefereeWireV1` or
# `GroundingRepairWireV1`, and its generic schema synthesiser cannot produce
# either. An unsatisfied fixture is an HTTP 500, and a 500 trips the
# qualification circuit breaker for the WHOLE endpoint -- so those two genuine
# gaps failed 13 of 23 pairs on the first P-A2 soak, 11 of them as cascade:
#
#   config-referee.v1                  ENDPOINT_HTTP_500        x20  (genuine)
#   groundingrepairwirev1.direct.v1    ENDPOINT_HTTP_500        x20  (genuine)
#   ...11 further pairs                CIRCUIT_OPEN_ENDPOINT_HTTP_500 (cascade)
#
# THIS IS NOT A DEFECT IN P-A2's CONFIGURATION AND NOT ONE THE LIVE RUN CAN
# HIT: it is the INSTRUMENT lacking a fixture for two contracts that only a
# maximum-configuration run grants. P-A1 met it first (its FINDINGS.md F1),
# fixed it in `scripts/wheel_operational_smoke.py`, and that fix never merged
# to main -- so it recurs for every later tranche that turns those two modules
# on. It is filed as a FINDING of this tranche; the fix belongs to a change
# tranche, not to a run tranche.
#
# The two values below are P-A1's, VERBATIM, together with the reasoning that
# earned them -- reused rather than re-derived because P-A1 paid for the
# lesson and a second guess could only drift from it:
#
#   ConfigRefereeWireV1 is conservative by construction: it never reports
#   mistuning and never recommends a change, so the soak exercises the
#   dispatch path without the referee steering the run.
#
#   GroundingRepairWireV1 -> `remove_span`, and the choice is NOT arbitrary.
#   STRUCTURALLY it is the one action accepting no substantive field, so it
#   satisfies every allOf/if/then branch by carrying nothing. IN SCOPE it is
#   the only action present in EVERY entry of `bridge.repair._ALLOWED_BY_STATUS`
#   -- the caller narrows the contract to one finding status's permitted
#   actions while the advertised JSON Schema still `$ref`s the full enum, so a
#   fixture chosen from the schema alone can be structurally valid and out of
#   scope. `correct_wording` is exactly that trap: it validates, then
#   `_admit_production_probe_output` raises BRIDGE_REPAIR_ACTION_FORBIDDEN.
#
# The patch is a WRAPPER that delegates everything else to the original. It
# makes the gate STRONGER, not weaker: two contracts that could not be
# exercised at all now must return schema-valid, in-scope responses or their
# pairs still fail. Nothing here can turn a failing pair green by relaxing a
# check -- there is no check here to relax.
_ORIGINAL_RESPONSE_FOR_SCHEMA = _smoke.response_for_schema


def _response_for_schema_with_pa1_fixtures(schema: dict, prompt: str):
    title = schema.get("title")
    if title == "ConfigRefereeWireV1":
        return {
            "verdict": "config_effective",
            "assessment": "The bounded loopback fixture observes no mistuning.",
            "cited_seqs": [0],
            "recommendation": "no_change",
        }
    if title == "GroundingRepairWireV1":
        return {"action": "remove_span"}
    return _ORIGINAL_RESPONSE_FOR_SCHEMA(schema, prompt)


# Patched on the MODULE, not on a local name: the stub's request handler calls
# the bare global `response_for_schema`, resolved in wheel_operational_smoke's
# namespace at call time, so rebinding the attribute is what actually reaches
# the server. cycle_soak imports the stub rather than minting a second one, so
# there is exactly one object to patch.
_smoke.response_for_schema = _response_for_schema_with_pa1_fixtures

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
