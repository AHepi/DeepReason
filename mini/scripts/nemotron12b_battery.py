#!/usr/bin/env python
"""True-12B replication + long-run stress battery
(experiments/nemotron12b_replication_prereg.yaml).

Phase 1: the burden battery's three flash arms re-run unchanged on
nvidia/nemotron-nano-12b-v2-vl (OpenRouter). Phase 2: judge-seat
certification on the new provider (record-required). Phase 3: long run
on the committed hard problem (pi-arrow-of-time) with the remainder of
the 1M-token cap. Every phase is resume-capable; free-tier transport
ceilings are recorded stop conditions, not failures.

Usage: OPENROUTER_API_KEY=... python mini/scripts/nemotron12b_battery.py [--resume]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINI))
sys.path.insert(0, str(MINI / "scripts"))

from minireason import judge  # noqa: E402
from minireason.call import TokenMeter  # noqa: E402
from minireason.log import BlobStore  # noqa: E402
from minireason.loop import ConjOut, Session, run  # noqa: E402

from hard_problem import DESCRIPTION as ARROW_DESCRIPTION  # noqa: E402
from hard_problem import PID as ARROW_PID  # noqa: E402
from small_model_burden import (PROBLEMS, RobustEndpoint, TerseConjOut,  # noqa: E402
                                arm_metrics, replay_ok, terse_prompt)
from small_model_burden import run_arm as _run_arm_impl  # noqa: E402
from smoke import NOVELTY_BASELINE, novelty_late_early  # noqa: E402

BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
TOTAL_CAP = 1_000_000
ARM_BUDGET = 30_000
CERTIFY_BUDGET = 15_000
MIN_INTERVAL_S = 3.0  # free tier ~20 req/min

ARMS = [
    # (name, prompt_fn, schema_cls, vs_k, neighbourhood)
    ("A-12b-stock",   None,         ConjOut,      6, 8),
    ("B-12b-terse",   terse_prompt, TerseConjOut, 6, 8),
    ("C-12b-compact", terse_prompt, TerseConjOut, 3, 2),
]


class PacedEndpoint(RobustEndpoint):
    """RobustEndpoint plus a minimum inter-request interval, shared across
    instances (one provider, one process): the free tier rate-limits per
    account, not per connection."""

    _last_request = [0.0]

    def complete(self, prompt: str) -> str:
        wait = self._last_request[0] + MIN_INTERVAL_S - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        try:
            return super().complete(prompt)
        finally:
            self._last_request[0] = time.monotonic()


def endpoint(api_key: str, temperature: float, max_tokens: int) -> PacedEndpoint:
    return PacedEndpoint(BASE_URL, MODEL, api_key=api_key,
                         temperature=temperature, max_tokens=max_tokens)


def phase1_burden(api_key: str, resume: bool) -> dict:
    arms = {}
    for name, prompt_fn, schema_cls, vs_k, nb in ARMS:
        print(f"--- arm {name} ({MODEL}, vs_k={vs_k}, nb={nb}) ---", flush=True)
        arms[name] = run_arm_12b(name, prompt_fn, schema_cls, vs_k, nb,
                                 api_key, resume)
        print(json.dumps(arms[name]["metrics"], indent=2), flush=True)
    return arms


def run_arm_12b(name, prompt_fn, schema_cls, vs_k, nb, api_key, resume) -> dict:
    """small_model_burden.run_arm, re-rooted for this battery (that function
    hardcodes runs/small_burden; same logic, same persistence contract)."""
    from minireason import loop as loop_mod
    root = Path("runs/nemotron12b") / name
    result_path = root / "arm_result.json"
    if resume and result_path.exists():
        print(f"(resume: loading committed result for {name})", flush=True)
        return json.loads(result_path.read_text())
    arm_budget, resumed_from = ARM_BUDGET, 0
    if resume and (root / "log.jsonl").exists():
        resumed_from = Session(root).state.logged_tokens()
        arm_budget = max(0, ARM_BUDGET - resumed_from)
        print(f"(resume: {name} continues, {resumed_from} logged, "
              f"{arm_budget} remaining)", flush=True)
    original_prompt, original_schema = loop_mod._prompt, loop_mod.ConjOut
    loop_mod._prompt = prompt_fn or original_prompt
    loop_mod.ConjOut = schema_cls
    try:
        summary = run(PROBLEMS, endpoint(api_key, 1.0, 4000), budget=arm_budget,
                      root=root, vs_k=vs_k, neighbourhood=nb, max_cycles=60)
    finally:
        loop_mod._prompt, loop_mod.ConjOut = original_prompt, original_schema
    metrics = arm_metrics(root)
    tk = summary["tokens"]
    metrics["avg_prompt_tokens_per_call"] = (
        round(tk["prompt_tokens"] / tk["calls"]) if tk["calls"] else None)
    metrics["avg_completion_tokens_per_call"] = (
        round(tk["completion_tokens"] / tk["calls"]) if tk["calls"] else None)
    result = {"arm": name, "model": MODEL, "vs_k": vs_k, "neighbourhood": nb,
              "prompt_variant": "terse" if prompt_fn else "stock",
              "resumed_from_tokens": resumed_from or None,
              "run_summary": summary, "metrics": metrics,
              "meter_equals_log": summary["meter_equals_log"],
              "replay_ok": replay_ok(root)}
    result_path.write_text(json.dumps(result, indent=2) + "\n")
    return result


def phase2_certify(api_key: str, resume: bool) -> dict:
    out_path = Path("runs/nemotron12b/certification.json")
    if resume and out_path.exists():
        print("(resume: loading committed certification)", flush=True)
        return json.loads(out_path.read_text())
    meter = TokenMeter(budget=CERTIFY_BUDGET)
    blobs = BlobStore(Path("runs/nemotron12b/certify_blobs"))
    seat = endpoint(api_key, 0.0, 600)
    result = judge.certify_seat(seat, meter, blobs)
    report = {"seat": f"{MODEL}/default", "result": result,
              "tokens": meter.snapshot()}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return report


def phase3_long_run(api_key: str, budget: int, resume: bool) -> dict:
    root = Path("runs/nemotron12b/long-arrow")
    resumed_from = 0
    if resume and (root / "log.jsonl").exists():
        resumed_from = Session(root).state.logged_tokens()
        budget = max(0, budget - resumed_from)
        print(f"(resume: long run continues, {resumed_from} logged, "
              f"{budget} remaining)", flush=True)
    summary = run([(ARROW_PID, ARROW_DESCRIPTION)],
                  endpoint(api_key, 1.0, 4000), budget=budget, root=root,
                  vs_k=6, turnover_k=12, stance_decay=5, max_cycles=300)
    session = Session(root)
    metrics = arm_metrics(root)
    metrics["novelty_late_early"] = novelty_late_early(session)
    metrics["novelty_baseline"] = NOVELTY_BASELINE
    result = {"problem": ARROW_PID, "resumed_from_tokens": resumed_from or None,
              "run_summary": summary, "metrics": metrics,
              "meter_equals_log": summary["meter_equals_log"],
              "replay_ok": replay_ok(root)}
    (root / "long_result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def evaluate(arms: dict, certification: dict, long_run: dict | None) -> dict:
    def fr(name):
        return arms[name]["metrics"]["failure_rate"]

    def yl(name):
        return arms[name]["metrics"]["yield_per_10k"]

    out = {}
    small = {n: arms[n]["metrics"]["conjecture_calls"] for n in arms}
    if any(small[n] < 8 for n in ("A-12b-stock", "C-12b-compact")):
        out["P1"] = {"verdict": "UNDECIDED",
                     "reason": f"transport ceiling before 8 calls: {small}"}
    elif fr("A-12b-stock") < 0.10:
        out["P1"] = {"verdict": "REFUTED",
                     "reason": f"failure_rate(A)={fr('A-12b-stock')} < 0.10 — the "
                               "flash result replicates downward; premise dead at 12B"}
    else:
        halved = fr("C-12b-compact") <= 0.5 * fr("A-12b-stock")
        kept = (yl("C-12b-compact") or 0) >= 0.8 * (yl("A-12b-stock") or 0)
        out["P1"] = {"verdict": "CONFIRMED" if halved and kept else "REFUTED",
                     "floor_clause": True, "halved_clause": halved,
                     "yield_clause": kept,
                     "failure_A": fr("A-12b-stock"), "failure_C": fr("C-12b-compact"),
                     "yield_A": yl("A-12b-stock"), "yield_C": yl("C-12b-compact"),
                     "failure_B": fr("B-12b-terse"), "yield_B": yl("B-12b-terse")}
    cert = certification.get("result", {})
    if cert.get("planted_flaw_error_rate") is None:
        out["P2"] = {"verdict": "UNDECIDED", "reason": "certification incomplete"}
    else:
        out["P2"] = {"verdict": "CONFIRMED" if not cert.get("passes") else "REFUTED",
                     "planted_flaw_error_rate": cert.get("planted_flaw_error_rate"),
                     "ceiling": 0.25, "passes": cert.get("passes")}
    if long_run is None or long_run["metrics"]["logged_tokens"] < 60_000:
        out["P3"] = {"verdict": "UNDECIDED",
                     "reason": "long run below the 60k decidability floor",
                     "logged": None if long_run is None
                     else long_run["metrics"]["logged_tokens"]}
    else:
        went_dry = long_run["run_summary"]["stop"] == "queue-exhausted"
        tokens = long_run["metrics"]["logged_tokens"]
        out["P3"] = {"verdict": ("CONFIRMED" if went_dry and tokens < 200_000
                                 else "REFUTED"),
                     "stop": long_run["run_summary"]["stop"],
                     "logged_tokens": tokens,
                     "survivors": long_run["metrics"]["survivors"]}
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--skip-long-run", action="store_true")
    parser.add_argument("--out", default=str(
        MINI.parent / "experiments" / "results" / "nemotron12b_report.json"))
    args = parser.parse_args()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set", file=sys.stderr)
        return 1

    arms = phase1_burden(api_key, args.resume)
    certification = phase2_certify(api_key, args.resume)

    spent = sum(a["metrics"]["logged_tokens"] for a in arms.values())
    spent += certification["tokens"]["total"]
    long_run = None
    if not args.skip_long_run:
        long_budget = max(0, TOTAL_CAP - spent)
        print(f"--- long run: {ARROW_PID}, budget {long_budget} ---", flush=True)
        long_run = phase3_long_run(api_key, long_budget, args.resume)
        spent += long_run["metrics"]["logged_tokens"]

    report = {
        "prereg": "experiments/nemotron12b_replication_prereg.yaml",
        "model": MODEL, "provider": BASE_URL,
        "total_openrouter_tokens": spent, "cap": TOTAL_CAP,
        "arms": arms, "certification": certification, "long_run": long_run,
        "predictions": evaluate(arms, certification, long_run),
        "flash_baseline": "experiments/results/small_model_burden_report.json",
    }
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["predictions"], indent=2))
    print(f"total OpenRouter tokens: {spent} / {TOTAL_CAP}")
    print(f"report -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
