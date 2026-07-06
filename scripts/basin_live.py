#!/usr/bin/env python
"""Basin study, live manipulation battery (experiments/basin_study_prereg.yaml).

Seven conjecture-only arms on the fixed pi-bronze problem, one manipulated
variable each: neighbourhood visibility, stance decay rate, complement
directive, model strength x temperature. Analysis reuses the exact
offline instrument (views/basin.py via basin_study.analyze_root).

  --arm NAME    run one arm (resumable; skips if already at budget)
  --arms A,B    run several sequentially
  --report      analyze all arm roots + evaluate the preregistered
                predictions -> experiments/results/basin_live_report.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from deepreason.config import Config  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.invariants import verify_root  # noqa: E402
from deepreason.llm.adapter import LLMAdapter  # noqa: E402
from deepreason.llm.budget import TokenMeter  # noqa: E402
from deepreason.llm.endpoints import OpenAICompatEndpoint  # noqa: E402
from deepreason.scheduler.scheduler import Scheduler  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "results" / "basin_live_report.json"
ARM_BUDGET = 60_000
CYCLES = 30

ARMS: dict[str, dict] = {
    "A-control":    {"model": "pro", "temp": 1.0, "overrides": {}},
    "B-blind":      {"model": "pro", "temp": 1.0, "overrides": {"NEIGHBOURHOOD_N": 0}},
    "C-decay-off":  {"model": "pro", "temp": 1.0, "overrides": {"STANCE_DECAY": 1e9}},
    "D-decay-fast": {"model": "pro", "temp": 1.0, "overrides": {"STANCE_DECAY": 5.0}},
    "E-complement": {"model": "pro", "temp": 1.0, "overrides": {"COMPLEMENT_ALWAYS": True}},
    "F-weak-cold":  {"model": "laguna", "temp": 0.2, "overrides": {}},
    "G-weak-hot":   {"model": "laguna", "temp": 1.0, "overrides": {}},
}


def _endpoint(spec: dict) -> OpenAICompatEndpoint:
    if spec["model"] == "pro":
        return OpenAICompatEndpoint(
            "https://api.deepseek.com", "deepseek-v4-pro",
            api_key=os.environ["DEEPSEEK_API_KEY"], temperature=spec["temp"],
            max_tokens=4000, json_mode=True, request_logprobs=True,
            reasoning="none")
    return OpenAICompatEndpoint(
        "https://inference.poolside.ai/v1", "poolside/laguna-m.1",
        api_key=os.environ["POOLSIDE_API_KEY"], temperature=spec["temp"],
        max_tokens=4000, json_mode=True)


def run_arm(name: str) -> dict:
    from live_run import seed_bronze

    spec = ARMS[name]
    root = ROOT / "runs" / "basin" / name
    h = Harness(root)
    if "pi-bronze" not in h.state.problems:
        seed_bronze(h)
    meter = TokenMeter(budget=ARM_BUDGET)
    adapter = LLMAdapter({"conjecturer": _endpoint(spec)}, h.blobs,
                         retry_max=2, meter=meter)
    config = Config(VS_K=2, N_SCHOOLS=2, FLOOR=0, **spec["overrides"])
    print(f"[{name}] running {CYCLES} cycles, cap {ARM_BUDGET}", flush=True)
    result = Scheduler(h, adapter, config).run(CYCLES)
    n_conj = sum(1 for a in h.state.artifacts.values()
                 if a.provenance.role.value in ("conjecturer", "synthesizer"))
    check = verify_root(root, meter.total)
    print(f"[{name}] done: {n_conj} conjectures, {meter.total} tokens, "
          f"violations={len(check['violations'])}", flush=True)
    return {"arm": name, "conjectures": n_conj, "tokens": meter.snapshot(),
            "violations": check["violations"],
            "stopped": [d for d in result["diagnostics"] if "stopped" in d][-1:]}


def _dup_events(root: Path) -> dict:
    h = Harness(root)
    gate = noreg = 0
    for e in h.log.read():
        joined = " ".join(str(i) for i in e.inputs)
        if "gate:" in joined:
            gate += 1
        if "conj-noregister" in joined:
            noreg += 1
    return {"gate_blocks": gate, "conj_noregister": noreg}


def report() -> int:
    from basin_study import analyze_root

    arms = {}
    for name, spec in ARMS.items():
        root = ROOT / "runs" / "basin" / name
        if not (root / "log.jsonl").exists():
            arms[name] = {"missing": True}
            continue
        a = analyze_root(root)
        a.pop("series", None)  # keep the report readable; curves stay in roots
        a["dups"] = _dup_events(root)
        arms[name] = a

    def g(arm, *path):
        node = arms.get(arm, {})
        for p in path:
            node = node.get(p) if isinstance(node, dict) else None
            if node is None:
                return None
        return node

    # Preregistered predictions (basin_study_prereg.yaml).
    predictions = {}
    a_le = g("A-control", "onset", "late_over_early")
    b_le = g("B-blind", "onset", "late_over_early")
    a_dup = (g("A-control", "dups", "gate_blocks") or 0) + (g("A-control", "dups", "conj_noregister") or 0)
    b_dup = (g("B-blind", "dups", "gate_blocks") or 0) + (g("B-blind", "dups", "conj_noregister") or 0)
    if a_le is not None and b_le is not None:
        p1 = abs(b_le - a_le) <= 0.15 and b_dup >= 2 * max(1, a_dup)
        predictions["P1-exhaustion"] = {
            "confirmed": p1, "A_late_over_early": a_le, "B_late_over_early": b_le,
            "A_dups": a_dup, "B_dups": b_dup,
            "note": "blind ~= control novelty AND blind >= 2x dups required"}
    else:
        predictions["P1-exhaustion"] = {"undecided": "missing metric"}

    f_echo, g_echo = g("F-weak-cold", "echo_vs_chance"), g("G-weak-hot", "echo_vs_chance")
    f_le, g_le = g("F-weak-cold", "onset", "late_over_early"), g("G-weak-hot", "onset", "late_over_early")
    if None not in (f_echo, g_echo, f_le, g_le):
        predictions["P2-echo-weak"] = {
            "confirmed": f_echo > 1.0 > g_echo and (g_le - f_le) >= 0.1,
            "F_echo": f_echo, "G_echo": g_echo, "F_late": f_le, "G_late": g_le}
    else:
        predictions["P2-echo-weak"] = {"undecided": "missing metric"}

    def tail_inter(arm):
        w = arms.get(arm, {}).get("windows_tail") or []
        vals = [x["inter_school_min"] for x in w if x.get("inter_school_min") is not None]
        return sum(vals) / len(vals) if vals else None

    c_i, d_i, a_i = tail_inter("C-decay-off"), tail_inter("D-decay-fast"), tail_inter("A-control")
    if None not in (c_i, d_i):
        # offline within-problem IQR/2 ~ 0.1 on the bronze scale
        predictions["P3-decay"] = {
            "confirmed": (c_i - d_i) >= 0.1, "C_inter": round(c_i, 4),
            "D_inter": round(d_i, 4), "A_inter": round(a_i, 4) if a_i else None}
    else:
        predictions["P3-decay"] = {"undecided": "missing metric"}

    e_le = g("E-complement", "onset", "late_over_early")
    if None not in (e_le, a_le):
        predictions["P4-complement"] = {
            "confirmed": e_le >= a_le + 0.1, "E_late": e_le, "A_late": a_le}
    else:
        predictions["P4-complement"] = {"undecided": "missing metric"}

    OUT.write_text(json.dumps({"arms": arms, "predictions": predictions}, indent=2))
    print(json.dumps(predictions, indent=2))
    print(f"report: {OUT}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm")
    parser.add_argument("--arms", help="comma-separated arm names")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.report:
        return report()
    names = [args.arm] if args.arm else (args.arms.split(",") if args.arms else list(ARMS))
    results = [run_arm(n) for n in names]
    for r in results:
        print(json.dumps({k: r[k] for k in ("arm", "conjectures", "violations")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
