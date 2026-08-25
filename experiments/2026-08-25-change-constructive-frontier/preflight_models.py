#!/usr/bin/env python3
"""OFFLINE-ish control: every seat's model exists in the provider catalogue.

Compile no longer refuses an otherwise-parseable configuration that names an
unreachable model (operator law 2026-08-12, "All configurations should be
allowed"): impossibility surfaces at the point of USE, which for a role
model is somewhere inside qualification or -- worse -- mid-run. This check
moves that discovery to the cheapest possible place.

It is not a substitute for qualification. It answers one question only:
does the provider LIST this model id? A listed model can still refuse the
run's schema, its token ceiling, or its reasoning setting, and only the
qualification battery measures that.

Requires network but NOT the operator's key: https://ollama.com/v1/models
answers unauthenticated. Deliberately so -- an id check that needed the
credential could not run before the credential arrives.

Usage:  python preflight_models.py
"""
from __future__ import annotations

import json
import pathlib
import sys
import urllib.request

TRANCHE = pathlib.Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from deepreason.config import load as load_config  # noqa: E402

CATALOGUE = "https://ollama.com/v1/models"


def _routes(config):
    """Every (role, seat_index, model) in the config, ensembles included."""

    for role, entry in sorted(config.roles.items()):
        seats = entry if isinstance(entry, (list, tuple)) else [entry]
        for index, route in enumerate(seats):
            # Routes arrive as plain dicts from the loader, but a future
            # loader returning models would still answer to attributes.
            if isinstance(route, dict):
                model = route.get("model") or route.get("model_id")
            else:
                model = getattr(route, "model", None) or getattr(
                    route, "model_id", None
                )
            yield role, index, str(model)


def main() -> int:
    config = load_config(TRANCHE / "run-config.yaml")
    with urllib.request.urlopen(CATALOGUE, timeout=60) as response:
        catalogue = json.loads(response.read().decode("utf-8"))
    listed = {entry["id"] for entry in catalogue.get("data", ())}

    rows = []
    for role, index, model in _routes(config):
        rows.append({
            "role": role,
            "seat": index,
            "model": model,
            "listed": model in listed,
        })

    missing = sorted({row["model"] for row in rows if not row["listed"]})
    report = {
        "catalogue": CATALOGUE,
        "catalogue_size": len(listed),
        "distinct_models": sorted({row["model"] for row in rows}),
        "missing": missing,
        "rows": rows,
        "holds": not missing,
    }
    (TRANCHE / "preflight_models.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )

    for row in rows:
        mark = "ok " if row["listed"] else "MISSING"
        print(f"{mark} {row['role']:22} seat {row['seat']}  {row['model']}")
    print(f"\ncatalogue lists {len(listed)} models; this config names "
          f"{len(report['distinct_models'])} distinct")
    if missing:
        print(f"NOT LISTED: {missing}")
        print("The seats are the operator's, verbatim (REQUEST.md A3/R17). "
              "A missing id is a STOP, not a substitution.")
        return 1
    print("every seat's model is listed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
