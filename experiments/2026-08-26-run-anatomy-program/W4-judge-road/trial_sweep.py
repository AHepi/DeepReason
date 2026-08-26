#!/usr/bin/env python3
"""W4 Q1: the STANDING FACT, re-derived over every committed root.

`experiments/2026-08-25-poietics-program/PARKED.md` P5 says "no defended
trial has ever run in this repository", strengthened by a census of "every
committed root that reports the field". That qualifier is the weakness:
`deepreason results` only reports the field for roots it can open, so the
census could not distinguish "zero trials" from "root not summarizable".

This instrument removes the qualifier. It re-derives
`application/results.py::_adjudication`'s four counters straight from
`log.jsonl` for all 54 roots in W1's `ROOT_INVENTORY.json` -- no Harness
open, no summarizability requirement -- and additionally counts the
UPSTREAM road markers that would exist if a case had ever got as far as
the trial door but been turned away there:

    trial-blocked:<reason>        a ruling screened out by a guard
    trial-declined                the defended case did not sustain
    trial-observation             an advisory trial completed, no warrant
    LLMCall(role="judge")         a judge seat actually dispatched
    defended-trial-deferred       crash recovery had no provider boundary
    arg-crit-overridden-by-execution   execution supremacy took the case

The last two are this instrument's addition to the P5 census: they are the
two recorded ways a case can leave the argumentative road WITHOUT reaching
the authority gate, so counting them is how "no trial ran" is separated
from "no case ever arrived".

Writes trial_sweep.json. Read-only: roots are opened as text, never as a
Harness.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
REPO = PROGRAM.parents[1]
INVENTORY = PROGRAM / "ROOT_INVENTORY.json"
OUT = HERE / "trial_sweep.json"

# Every Measure signal that marks a point on the defended-trial road, and
# the road stage it marks. Sourced from informal/trial.py's own
# record_measure calls and rules/crit.py's two non-authority exits.
ROAD_SIGNALS = {
    "trial-observation": "trial_ran_advisory",
    "trial-declined": "trial_ran_case_failed",
    "defended-trial-deferred": "left_road_recovery_no_provider",
    "arg-crit-overridden-by-execution": "left_road_execution_supremacy",
}
BLOCKED_PREFIX = "trial-blocked:"


def sweep_root(root: Path) -> dict:
    counters = {name: 0 for name in ROAD_SIGNALS.values()}
    blocked: dict[str, int] = {}
    observations: dict[str, int] = {}
    declined: dict[str, int] = {}
    judge_calls = 0
    judge_models: dict[str, int] = {}
    crit_events = 0
    llm_calls = 0
    roles: dict[str, int] = {}
    log = root / "log.jsonl"
    with log.open() as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            if event.get("rule") == "Crit":
                crit_events += 1
            llm = event.get("llm")
            if llm:
                llm_calls += 1
                role = str(llm.get("role"))
                roles[role] = roles.get(role, 0) + 1
                if role == "judge":
                    judge_calls += 1
                    model = str(llm.get("model") or llm.get("model_id") or "?")
                    judge_models[model] = judge_models.get(model, 0) + 1
            inputs = [str(v) for v in (event.get("inputs") or ())]
            if not inputs:
                continue
            signal = inputs[0]
            stage = ROAD_SIGNALS.get(signal)
            if stage is not None:
                counters[stage] += 1
            if signal == "trial-observation":
                outcome = inputs[3] if len(inputs) > 3 else "unrecorded"
                observations[outcome] = observations.get(outcome, 0) + 1
            elif signal == "trial-declined":
                reason = inputs[2] if len(inputs) > 2 else "unrecorded"
                declined[reason] = declined.get(reason, 0) + 1
            elif signal.startswith(BLOCKED_PREFIX):
                reason = signal[len(BLOCKED_PREFIX):] or "unrecorded"
                blocked[reason] = blocked.get(reason, 0) + 1
    total = judge_calls + sum(observations.values()) + sum(declined.values())
    return {
        # `_adjudication`'s own four fields, re-derived.
        "ran": bool(total or blocked),
        "judge_calls": judge_calls,
        "trial_observations": dict(sorted(observations.items())),
        "trial_declined": dict(sorted(declined.items())),
        "trial_blocked": dict(sorted(blocked.items())),
        # W4's additions.
        "judge_models_dispatched": dict(sorted(judge_models.items())),
        "crit_events": crit_events,
        "llm_calls": llm_calls,
        "llm_calls_by_role": dict(sorted(roles.items())),
        "road_markers": counters,
    }


def manifest_authority(root: Path) -> dict:
    """The two manifest fields that decide the authority gate, if present."""
    path = root / "run-manifest.json"
    if not path.exists():
        return {"manifest": False}
    manifest = json.loads(path.read_text())
    policy = manifest.get("criticism_policy")
    engine = manifest.get("engine_config_json")
    if isinstance(engine, str):
        engine = json.loads(engine)
    engine = engine or {}
    return {
        "manifest": True,
        "schema_version": manifest.get("schema_version"),
        "criticism_policy_present": policy is not None,
        "criticism_policy_authority": (policy or {}).get("authority"),
        "rubric_policy": manifest.get("rubric_policy"),
        "judge_seats_declared": len(manifest.get("roles", {}).get("judge", []) or []),
        "defender_seats_declared": len(
            manifest.get("roles", {}).get("defender", []) or []
        ),
        # Config echo. The authority master gates are DROPPED from this echo
        # by `_versioned_source_config_data` (docs/ERRATA.md E44), so their
        # absence here is expected and is itself part of the finding.
        "ARGUMENTATIVE_AUTHORITY": engine.get("ARGUMENTATIVE_AUTHORITY", "<absent>"),
        "ENGAGED_CRITICISM_AUTHORITY": engine.get(
            "ENGAGED_CRITICISM_AUTHORITY", "<absent>"
        ),
        "ADJUDICATION_STATUS_AUTHORITY_ENABLED": engine.get(
            "ADJUDICATION_STATUS_AUTHORITY_ENABLED", "<absent>"
        ),
        "JUDGE_SEATS_ENABLED": engine.get("JUDGE_SEATS_ENABLED", "<absent>"),
        "LEGACY_CRITICISM_ENABLED": engine.get("LEGACY_CRITICISM_ENABLED", "<absent>"),
        "CALIBRATION_RECEIPT": engine.get("CALIBRATION_RECEIPT", "<absent>"),
    }


def main() -> int:
    inventory = json.loads(INVENTORY.read_text())
    rows = []
    for entry in inventory["roots"]:
        root = REPO / entry["root"]
        row = {"root": entry["root"], "run_id": entry["run_id"][:16]}
        row.update(sweep_root(root))
        row["config"] = manifest_authority(root)
        rows.append(row)
    totals = {
        "roots": len(rows),
        "roots_with_any_judge_call": sum(1 for r in rows if r["judge_calls"]),
        "roots_with_ran_true": sum(1 for r in rows if r["ran"]),
        "judge_calls": sum(r["judge_calls"] for r in rows),
        "trial_observations": sum(sum(r["trial_observations"].values()) for r in rows),
        "trial_declined": sum(sum(r["trial_declined"].values()) for r in rows),
        "trial_blocked": sum(sum(r["trial_blocked"].values()) for r in rows),
        "crit_events": sum(r["crit_events"] for r in rows),
        "roots_declaring_judge_seats": sum(
            1 for r in rows if r["config"].get("judge_seats_declared")
        ),
        "roots_with_criticism_policy": sum(
            1 for r in rows if r["config"].get("criticism_policy_present")
        ),
        "criticism_policy_authorities": {},
        "road_markers": {
            stage: sum(r["road_markers"][stage] for r in rows)
            for stage in sorted(set(ROAD_SIGNALS.values()))
        },
    }
    for r in rows:
        auth = r["config"].get("criticism_policy_authority")
        key = str(auth)
        totals["criticism_policy_authorities"][key] = (
            totals["criticism_policy_authorities"].get(key, 0) + 1
        )
    payload = {
        "schema": "w4.trial-sweep.v1",
        "inventory": str(INVENTORY.relative_to(REPO)),
        "totals": totals,
        "roots": rows,
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(json.dumps(totals, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
