#!/usr/bin/env python
"""Small-model chaos battery: drive the harness down never-exercised paths
with a weak model (poolside laguna-xs) in each role, then verify hard
invariants over the wreckage (deepreason.invariants.verify_root). Every
violation or traceback in the report is a bug candidate.

Scenarios (see the plan / chaos_report.json):
  S1 garbage generator     — schema-repair storms, dropped-call accounting
  S2 weak judge seat       — ensemble splits, guard screens, blocked spend
  S3 all-weak, low temp    — capture flags + response ladder firing LIVE
  S4 weak skeletons        — skeleton discipline, successor cascades,
                             problem-description growth

Usage: DEEPSEEK_API_KEY=... POOLSIDE_API_KEY=... python scripts/chaos_battery.py
       [--only S3] [--budget-per 55000] [--cycles-scale 1.0]
"""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from deepreason.config import load as load_config  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.invariants import verify_root  # noqa: E402
from deepreason.llm.adapter import LLMAdapter  # noqa: E402
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter  # noqa: E402
from deepreason.llm.endpoints import OpenAICompatEndpoint  # noqa: E402
from deepreason.scheduler.scheduler import Scheduler  # noqa: E402
from deepreason.views.narrate import narrate  # noqa: E402

DEEPSEEK = "https://api.deepseek.com"
POOLSIDE = "https://inference.poolside.ai/v1"
REPORT = Path(__file__).resolve().parents[1] / "experiments" / "results" / "chaos_report.json"


def _ep(base, key_env, model, temp, max_tokens=2400, reasoning=None):
    key = os.environ[key_env]
    return OpenAICompatEndpoint(base, model, api_key=key, temperature=temp,
                                max_tokens=max_tokens, json_mode=True,
                                reasoning=reasoning)


def xs(temp, max_tokens=2400):
    return _ep(POOLSIDE, "POOLSIDE_API_KEY", "poolside/laguna-xs.2", temp, max_tokens)


def flash(temp, max_tokens=2400, reasoning="none"):
    return _ep(DEEPSEEK, "DEEPSEEK_API_KEY", "deepseek-v4-flash", temp,
               max_tokens, reasoning)


def pro(temp, max_tokens=2400, reasoning="none"):
    return _ep(DEEPSEEK, "DEEPSEEK_API_KEY", "deepseek-v4-pro", temp,
               max_tokens, reasoning)


# scenario -> (suite, cycles, roles builder, config overrides, what it targets)
SCENARIOS = {
    "S1-garbage-generator": dict(
        suite="tides", cycles=12,
        roles=lambda: {
            "conjecturer": xs(1.0, max_tokens=1600),
            "argumentative_critic": flash(0.7),
            "variator": flash(1.0),
        },
        overrides={"N_SCHOOLS": 0, "FLOOR": 0, "VS_K": 2},
        targets="schema-repair storms; dropped-call spend; gate under junk",
    ),
    "S2-weak-judge-seat": dict(
        suite="republic", cycles=10,
        roles=lambda: {
            "conjecturer": pro(1.0, max_tokens=4000),
            "argumentative_critic": flash(0.7),
            "defender": xs(0.7, max_tokens=900),
            "variator": flash(1.0),
            "judge": [pro(0.0), xs(0.0)],
        },
        overrides={"N_SCHOOLS": 0, "FLOOR": 0, "VS_K": 2},
        targets="ensemble splits; guard screens; blocked-trial spend; weak defender",
    ),
    "S3-all-weak-lowtemp": dict(
        suite="tides", cycles=15,
        roles=lambda: {
            "conjecturer": xs(0.2, max_tokens=1600),
            "argumentative_critic": xs(0.7, max_tokens=1600),
            "variator": xs(1.0, max_tokens=1600),
            "synthesizer": xs(0.9, max_tokens=1200),
        },
        overrides={"N_SCHOOLS": 2, "FLOOR": 0, "VS_K": 2, "CAPTURE_W": 10},
        targets="capture flags + response ladder live; reseed; xexam floor",
    ),
    "S4-weak-skeletons": dict(
        suite="criticism", cycles=12,
        roles=lambda: {
            "conjecturer": xs(1.0, max_tokens=2400),
            "argumentative_critic": flash(0.7),
            "defender": xs(0.7, max_tokens=900),
            "variator": xs(1.0, max_tokens=1600),
            "judge": [flash(0.0), xs(0.0)],
        },
        overrides={"N_SCHOOLS": 2, "FLOOR": 0, "VS_K": 2},
        targets="skeleton discipline; successor cascade; description growth",
    ),
}


def run_scenario(name: str, spec: dict, budget: int, cycles_scale: float) -> dict:
    from live_run import SUITES

    root = Path("runs/chaos") / name
    harness = Harness(root)
    problem_id, seed = SUITES[spec["suite"]]
    if problem_id not in harness.state.problems:
        seed(harness)

    config = load_config(Path(__file__).resolve().parents[1] / "config" / "deepseek.yaml")
    for k, v in spec["overrides"].items():
        setattr(config, k, v)
    meter = TokenMeter(budget=budget)
    adapter = LLMAdapter(spec["roles"](), harness.blobs,
                         retry_max=config.RETRY_MAX, meter=meter)

    finding: dict = {"targets": spec["targets"], "suite": spec["suite"]}
    try:
        result = Scheduler(harness, adapter, config).run(
            max(1, int(spec["cycles"] * cycles_scale)))
        finding["completed"] = True
        finding["dropped_cycles"] = sum(1 for d in result["diagnostics"] if "dropped" in d)
        finding["stopped"] = next(
            (d["stopped"] for d in result["diagnostics"] if "stopped" in d), None)
    except TokenBudgetExceeded as e:
        finding["completed"] = True
        finding["stopped"] = str(e)
    except Exception:  # noqa: BLE001 - an uncaught exception IS the finding
        finding["completed"] = False
        finding["traceback"] = traceback.format_exc()[-2000:]

    check = verify_root(root, meter.total)
    finding["violations"] = check["violations"]
    finding["stats"] = check["stats"]
    finding["meter"] = meter.snapshot()
    try:
        finding["narration_tail"] = narrate(Harness(root), window=25)
    except Exception:  # noqa: BLE001 - narrate crashing on chaos is a finding too
        finding["narration_tail_error"] = traceback.format_exc()[-800:]
    return finding


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="", help="substring filter on scenario names")
    parser.add_argument("--budget-per", type=int, default=55_000)
    parser.add_argument("--cycles-scale", type=float, default=1.0)
    args = parser.parse_args()
    for env in ("DEEPSEEK_API_KEY", "POOLSIDE_API_KEY"):
        if not os.environ.get(env):
            print(f"{env} not set", file=sys.stderr)
            return 1

    report: dict = {"experiment": "small-model chaos battery", "scenarios": {}}
    exit_code = 0
    for name, spec in SCENARIOS.items():
        if args.only and args.only not in name:
            continue
        print(f"=== {name}: {spec['targets']} ===", flush=True)
        finding = run_scenario(name, spec, args.budget_per, args.cycles_scale)
        report["scenarios"][name] = finding
        bad = finding["violations"] or not finding["completed"]
        if bad:
            exit_code = 1
        print(json.dumps({k: finding[k] for k in
                          ("completed", "violations", "stats") if k in finding},
                         indent=1)[:1200], flush=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nreport: {REPORT}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
