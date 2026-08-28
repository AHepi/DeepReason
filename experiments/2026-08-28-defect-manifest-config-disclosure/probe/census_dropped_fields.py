#!/usr/bin/env python3
"""P10 blast-radius census (AUDIT_REPORT.md residue item 4).

Answers three questions from committed evidence alone, offline:

  1. WHICH Config fields the manifest's engine-config echo drops, at the
     schema version every live run uses (v6).
  2. WHICH of them are BEHAVIOURAL -- consumed at run time from the Config
     that `config_from_run_manifest` rebuilds -- versus IDENTITY-ONLY,
     consumed only at compile time and therefore already spent by the time
     the echo is written.
  3. WHETHER the loss is a `--run-manifest` problem or a universal one:
     for every committed `run-config.yaml` on main, which dropped fields
     the operator set away from default, and what the run actually took.

Usage: PYTHONPATH=. python experiments/.../probe/census_dropped_fields.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from deepreason.config import Config, load as load_config
from deepreason.run_manifest import (
    RunManifest,
    _source_config_data,
    _versioned_source_config_data,
)

REPO = Path(__file__).resolve().parents[3]
LIVE_SCHEMA = 6

# Consumption sites, one per dropped field, measured by
#   grep -rn "\bFIELD\b" src/deepreason --include=*.py
# excluding config.py (the declaration) and run_manifest.py (the drop list).
# RUN means the site is reached with `config_from_run_manifest(manifest)`;
# COMPILE means the site only ever sees the builder's own Config.
CONSUMERS: dict[str, tuple[str, str]] = {
    "ADJUDICATION_STATUS_AUTHORITY_ENABLED": ("RUN", "authority.py, rules/crit.py, rules/experiment.py, signals.py, imports.py"),
    "ATTENTION_ALLOCATION_POLICY": ("RUN", "wander.py"),
    "CAPTURE14_AGE_FLOOR": ("RUN", "capture/diagnostics.py"),
    "CAPTURE14_ENTER_K": ("RUN", "capture/hysteresis.py"),
    "CAPTURE14_EXIT_K": ("RUN", "capture/hysteresis.py"),
    "CAPTURE14_PRECISION": ("RUN", "capture/diagnostics.py, capture/hysteresis.py"),
    "CAPTURE14_SC_CEILING": ("RUN", "capture/hysteresis.py"),
    "CAPTURE14_WINDOW": ("RUN", "capture/diagnostics.py"),
    "CHANNELS_DISABLED": ("RUN", "channels.py, v6_policy.py, preparation.py"),
    "DISCHARGE_POLICY": ("RUN", "discharge/policy.py"),
    "ENGAGED_CRITICISM_AUTHORITY": ("COMPILE", "preparation.py only"),
    "FRAME_SLICE_ATTACKERS": ("RUN", "capture/hysteresis.py"),
    "FRAME_SLICE_DEPARTURES": ("RUN", "capture/hysteresis.py"),
    "JUDGE_SEATS_ENABLED": ("RUN", "authority.py, scheduler/scheduler.py"),
    "JUDGE_SUMMONS_COOLDOWN": ("RUN", "scheduler/scheduler.py"),
    "JUDGE_SUMMONS_PER_CYCLE": ("RUN", "scheduler/scheduler.py"),
    "K_FRAME": ("RUN", "calculus/nomination.py"),
    "LEGACY_CRITICISM_ENABLED": ("COMPILE", "preparation.py, cli/main.py"),
    "PROMOTION_ENVIRONMENT_MAX": ("RUN", "calculus/nomination.py"),
    "SCHOOL_SEATS_ENABLED": ("COMPILE", "preparation.py, cli/main.py"),
    "SCOPE_MAX_DEPTH": ("RUN", "calculus/nomination.py"),
    "SCOPE_MAX_NODES": ("RUN", "calculus/nomination.py"),
    "SEED_PROBLEM_BUDGET_FLOOR": ("RUN", "wander.py"),
    "SPLIT_BUDGET_EXTRACTION_TOKENS": ("RUN", "llm/adapter.py"),
    "SPLIT_BUDGET_SEAT_PROTOCOL": ("RUN", "llm/adapter.py"),
}


def dropped_fields(schema_version: int = LIVE_SCHEMA) -> list[str]:
    defaults = Config()
    full = _source_config_data(defaults)
    echoed = _versioned_source_config_data(defaults, schema_version)
    return sorted(set(full) - set(echoed))


def main() -> int:
    defaults = _source_config_data(Config())
    dropped = dropped_fields()

    print("== 1. fields dropped from engine_config_json at schema v%d: %d ==" % (LIVE_SCHEMA, len(dropped)))
    unclassified = [f for f in dropped if f not in CONSUMERS]
    if unclassified:
        print("   UNCLASSIFIED (the census is stale, re-measure): %s" % unclassified)
    behavioural = [f for f in dropped if CONSUMERS.get(f, ("RUN", ""))[0] == "RUN"]
    identity = [f for f in dropped if CONSUMERS.get(f, ("RUN", ""))[0] == "COMPILE"]
    for field in dropped:
        kind, sites = CONSUMERS.get(field, ("?", "?"))
        print("   %-9s %-40s default=%-22r %s" % (kind, field, defaults[field], sites))
    print("\n   BEHAVIOURAL (silently reverts at run time): %d" % len(behavioural))
    print("   IDENTITY-ONLY (spent at compile time):      %d  %s" % (len(identity), identity))

    files = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()

    print("\n== 2. committed run-config.yaml: dropped fields set away from default ==")
    affected = 0
    for rel in [f for f in files if f.endswith("run-config.yaml")]:
        try:
            cfg = _source_config_data(load_config(REPO / rel))
        except Exception as error:  # noqa: BLE001
            print("  %s\n      LOAD FAILED: %s" % (rel, type(error).__name__))
            continue
        diverged = {k: (defaults[k], cfg[k]) for k in dropped if cfg[k] != defaults[k]}
        print("  %s" % rel)
        if not diverged:
            print("      (none -- every dropped field at its default)")
            continue
        affected += 1
        for field, (default_value, set_value) in sorted(diverged.items()):
            kind = CONSUMERS.get(field, ("?", ""))[0]
            print("      %-9s %-40s configured=%-18r run takes=%r"
                  % (kind, field, set_value, default_value))
    print("\n   configs losing at least one dropped field: %d of %d"
          % (affected, len([f for f in files if f.endswith('run-config.yaml')])))

    print("\n== 3. committed run-manifest.json: what the echo actually carries ==")
    leaked = 0
    for rel in [f for f in files if f.endswith("run-manifest.json")]:
        try:
            manifest = RunManifest.model_validate_json((REPO / rel).read_text())
        except Exception as error:  # noqa: BLE001
            print("  %-92s UNREADABLE (%s)" % (rel, type(error).__name__))
            continue
        echo = json.loads(manifest.engine_config_json)
        present = sorted(k for k in dropped if k in echo)
        leaked += bool(present)
        policy = manifest.criticism_policy
        print("  %-92s v%d dropped-present=%-4s criticism_policy=%-14s compile_notices=%d"
              % (rel, manifest.schema_version, present or "none",
                 "None" if policy is None else policy.authority,
                 len(manifest.compile_notices or ())))
    print("\n   committed manifests whose echo carries any dropped field: %d" % leaked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
