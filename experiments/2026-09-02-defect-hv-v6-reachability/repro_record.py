"""Record-replay reproduction: the v6 gate ignores the grant it stands in for.

Reads every committed v6 run root READ-ONLY and joins two facts that live in
different files of the same root:

  * `run-manifest.json` -> whether the `variator` seat was granted a behavioural
    contract (`variator.direct.v1` / `variator.compact.v1`), which is the
    configuration the deferral gate exists to stand in for;
  * `log.jsonl` -> how many `hv_set` measurements the run actually recorded, and
    how many times it recorded `v6-model-phase-deferred.v1` for an `hv` phase
    instead.

The defect is the row where the grant is PRESENT, the deferrals are many, and
the measurements are zero. No provider, no soak, no live run: the contradiction
is already committed.

Usage:  python experiments/2026-09-02-defect-hv-v6-reachability/repro_record.py
Exit 0  the defect is REPRODUCED (>=1 grant-bearing root measured no hv).
Exit 1  the defect is ABSENT (no such root) -- which after the fix is what a
        NEW grant-bearing root would show; the committed roots here were
        written by the defective code and never change.
"""

from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
HV_PHASES = {"hv-floor", "hv-spot-check"}
VARIATOR_CONTRACTS = {"variator.direct.v1", "variator.compact.v1"}
MARKER = "v6-model-phase-deferred.v1"


def variator_grants(manifest: dict) -> list[str]:
    """The behavioural contracts granted to any `variator` seat, sorted."""

    plan = manifest.get("route_seat_behavioral_capability_plan") or {}
    return sorted(
        contract["contract_id"]
        for entry in plan.get("entries", ())
        if entry.get("role") == "variator"
        for contract in entry.get("contracts", ())
    )


def walk_log(log_path: pathlib.Path) -> tuple[int, int, dict[str, int]]:
    """(events, non-empty hv_set events, deferred hv phase -> count)."""

    events = measured = 0
    deferred: dict[str, int] = {}
    with log_path.open() as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            events += 1
            if (event.get("state_diff") or {}).get("hv_set"):
                measured += 1
            inputs = event.get("inputs") or []
            if len(inputs) >= 2 and inputs[0] == MARKER and inputs[1] in HV_PHASES:
                deferred[inputs[1]] = deferred.get(inputs[1], 0) + 1
    return events, measured, deferred


def main() -> int:
    rows = []
    for manifest_path in sorted(REPO.glob("experiments/**/run-manifest.json")):
        root = manifest_path.parent
        log_path = root / "log.jsonl"
        if not log_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("schema_version") != 6:
            continue
        grants = variator_grants(manifest)
        events, measured, deferred = walk_log(log_path)
        if not grants and not deferred:
            continue  # nothing was asked for and nothing was granted
        rows.append(
            {
                "root": str(root.relative_to(REPO)),
                "grants": grants,
                "events": events,
                "hv_set": measured,
                "hv_deferred": sum(deferred.values()),
                "by_phase": deferred,
                "status": read_status(root),
            }
        )

    rows.sort(key=lambda row: (not row["grants"], -row["hv_deferred"]))
    width = max((len(row["root"]) for row in rows), default=4)
    print(f"{'root'.ljust(width)}  grant  events  hv_set  hv_deferred  state")
    for row in rows:
        print(
            f"{row['root'].ljust(width)}  "
            f"{'YES  ' if row['grants'] else ' no  '}  "
            f"{row['events']:6d}  {row['hv_set']:6d}  {row['hv_deferred']:11d}  "
            f"{row['status']}"
        )
        if row["by_phase"]:
            print(f"{' ' * width}         {row['by_phase']}")

    contradictions = [
        row for row in rows if row["grants"] and row["hv_deferred"] and not row["hv_set"]
    ]
    print()
    for row in contradictions:
        print(
            f"DEFECT  {row['root']}\n"
            f"        variator seat holds {row['grants']}, the run asked for hv "
            f"{row['hv_deferred']} times, and recorded {row['hv_set']} hv_set events."
        )
    controls = [row for row in rows if not row["grants"] and row["hv_deferred"]]
    for row in controls:
        print(
            f"CONTROL {row['root']}\n"
            f"        variator seat holds NO grant; deferring {row['hv_deferred']} "
            f"hv phases is the CORRECT behaviour and must not change."
        )
    print()
    if contradictions:
        print(f"REPRODUCED: {len(contradictions)} grant-bearing root(s) measured no hv.")
        return 0
    print("NOT REPRODUCED: no committed grant-bearing v6 root asked for hv.")
    return 1


def read_status(root: pathlib.Path) -> str:
    path = root / "run-status.json"
    if not path.exists():
        return "-"
    try:
        status = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return "-"
    return f"{status.get('state')}/{status.get('stop_reason')}"


if __name__ == "__main__":
    sys.exit(main())
