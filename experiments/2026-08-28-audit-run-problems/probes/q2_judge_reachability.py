#!/usr/bin/env python3
"""Q2 probe -- reconstruct the Config the run actually executed under, from the
committed manifest, and evaluate every gate on the two judge roads.

Why this is the right instrument. The ladder launches with
`--run-manifest` and no `--config` (pt1_run.sh:120-124), so `run-config.yaml`
is consumed ONLY by the builder. At run time the Config is rebuilt by
`run_manifest.py::config_from_run_manifest` (4287), which does
`Config.model_validate(json.loads(manifest.engine_config_json))` -- so any
Config field the manifest's engine-config echo does not carry takes its
DEFAULT, whatever the builder's own Config said.

The two roads a judge can be called on:
  RUBRIC road       scheduler.py:1338-1379 -- needs a `rubric:` commitment,
                    JUDGE_SEATS_ENABLED, and `_judge_summons_admitted`
                    (scheduler.py:1063, gated on JUDGE_SUMMONS_PER_CYCLE).
  ARGUMENTATIVE     crit.py:1596-1618 -- runs a trial only when the resolved
  road              authority is in _TRIAL_MODES (crit.py:79); observe_only
                    returns `_observe_case` instead.

Usage: q2_judge_reachability.py <root> [<root> ...]
"""
import json
import pathlib
import sys

sys.path.insert(0, "src")
from deepreason.config import Config  # noqa: E402
from deepreason.run_manifest import config_from_run_manifest, load_run_manifest  # noqa: E402

WATCH = [
    "JUDGE_SEATS_ENABLED",
    "JUDGE_SUMMONS_PER_CYCLE",
    "JUDGE_SUMMONS_COOLDOWN",
    "ADJUDICATION_STATUS_AUTHORITY_ENABLED",
    "ENGAGED_CRITICISM_AUTHORITY",
    "LEGACY_CRITICISM_ENABLED",
    "ARGUMENTATIVE_AUTHORITY",
    "ADVISORY_TRIALS_PER_CYCLE",
    "RUBRIC_TRIALS_PER_ARTIFACT",
    "SCHOOL_SEATS_ENABLED",
    "SEED_PROBLEM_BUDGET_FLOOR",
    "ATTENTION_ALLOCATION_POLICY",
]


def report(root: pathlib.Path) -> dict:
    manifest = load_run_manifest(root / "run-manifest.json")
    echo = json.loads(manifest.engine_config_json)
    cfg = config_from_run_manifest(manifest)
    defaults = Config()
    rows = {}
    for name in WATCH:
        effective = getattr(cfg, name, "<absent from Config>")
        rows[name] = {
            "in_manifest_echo": name in echo,
            "effective_at_run_time": effective,
            "config_default": getattr(defaults, name, "<absent>"),
            "took_default": name not in echo,
        }
    return {
        "root": root.name,
        "criticism_policy_in_manifest": manifest.criticism_policy is not None,
        "rubric_policy": manifest.rubric_policy,
        "judge_routes_bound": len(manifest.roles.get("judge", ()) or ()),
        "judge_models": [r.model_id for r in (manifest.roles.get("judge", ()) or ())],
        "engine_echo_key_count": len(echo),
        "config_fields": rows,
    }


if __name__ == "__main__":
    print(json.dumps([report(pathlib.Path(a)) for a in sys.argv[1:]], indent=2, default=str))
