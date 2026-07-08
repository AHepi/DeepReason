#!/usr/bin/env python
"""Small-model prompt-burden battery (experiments/small_model_burden_prereg.yaml).

Four matched-budget MiniReason arms on the committed smoke problems,
varying ONLY the instruction text and the vs_k / neighbourhood knobs;
validation (pydantic schema), checks, gate, rotation, and accounting are
the committed code paths in every arm. Metrics are recomputed from each
arm's log after the run — the log, not the in-memory summary, is the
evidence.

Usage: DEEPSEEK_API_KEY=... python mini/scripts/small_model_burden.py [--budget 30000]
       python mini/scripts/small_model_burden.py --mock   # pipeline sanity, no network
"""

import argparse
import json
import os
import sys
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINI))

from minireason import call as llm  # noqa: E402
from minireason import loop as loop_mod  # noqa: E402
from minireason.checks import parse_skeleton  # noqa: E402
from minireason.loop import ConjOut, Session, run  # noqa: E402

PROBLEMS = [  # the committed smoke problems, same order, every arm
    ("pi-bronze", "Why did the Late Bronze Age interstate system collapse "
                  "within roughly a single generation (c. 1200-1150 BCE)?"),
    ("pi-needham", "Why did sustained scientific-industrial revolution emerge "
                   "in early-modern Europe rather than Song-Ming China?"),
]

TERSE_SCHEMA = {
    "type": "object",
    "properties": {"candidates": {"type": "array", "items": {
        "type": "object",
        "properties": {"content": {"type": "string"},
                       "typicality": {"type": "number"}},
        "required": ["content", "typicality"]}}},
    "required": ["candidates"],
}


class TerseConjOut(ConjOut):
    """Same fields, same validation — only the schema DUMP shown to the
    model is compacted (the burden knob under test, nothing else)."""

    @classmethod
    def model_json_schema(cls, *args, **kwargs):  # noqa: D102
        return TERSE_SCHEMA


def terse_prompt(description: str, stance_directive: str,
                 neighbourhood: str, vs_k: int) -> str:
    return (
        f"Propose {vs_k} diverse, bold, refutable explanations for the problem. "
        f"Stance: {stance_directive}.\n"
        "Each candidates[i].content is a STRING holding this JSON: "
        '{"claim": str, "mechanism": str, "scope": {"covers": [], "excludes": []}, '
        '"forbidden": [{"case": str, "eval": str}], "prose_notes": str}. '
        'Every candidate needs >=1 forbidden case (evidence that would refute it); '
        'eval is "predicate:<python expr over the string variable content>" or '
        '"rubric:std". typicality in [0,1].\n'
        f"PROBLEM: {description}\n"
        + (f"Do not repeat these:\n{neighbourhood}\n" if neighbourhood else "")
    )


ARMS = [
    # (name, model, prompt_fn, schema_cls, vs_k, neighbourhood)
    ("A-flash-stock",   "deepseek-v4-flash", None,         ConjOut,      6, 8),
    ("B-flash-terse",   "deepseek-v4-flash", terse_prompt, TerseConjOut, 6, 8),
    ("C-flash-compact", "deepseek-v4-flash", terse_prompt, TerseConjOut, 3, 2),
    ("D-pro-stock",     "deepseek-v4-pro",   None,         ConjOut,      6, 8),
]


def arm_metrics(root: Path) -> dict:
    """Recompute every prereg metric from the committed log alone."""
    session = Session(root)
    calls = clean = repaired = dropped = truncated = 0
    prompt_tokens = completion_tokens = 0
    for event in session.state.events:
        if event.llm is None:
            continue
        if event.llm.role != "conjecturer":
            continue
        calls += 1
        is_dropped = event.rule == "Measure" and "dropped-call" in event.inputs
        is_partial = event.rule == "Measure" and "budget-exhausted" in event.inputs
        if event.llm.truncated:
            truncated += 1
        if is_dropped:
            dropped += 1
        elif not is_partial and event.llm.attempts == 1:
            clean += 1
        elif not is_partial:
            repaired += 1
    admitted = [aid for aid, _ in session.state.addr]
    refuted = [aid for aid in admitted if aid in session.state.refuted]
    skeleton_wf_refuted = 0
    for aid in refuted:
        content = session.state.artifacts[aid]["content_ref"][len("inline:"):]
        skeleton = parse_skeleton(content)
        if skeleton is None or not skeleton.forbidden:
            skeleton_wf_refuted += 1
    tokens = session.state.logged_tokens()
    survivors = len(admitted) - len(refuted)
    return {
        "conjecture_calls": calls,
        "clean_first_attempt": clean,
        "repaired": repaired,
        "dropped": dropped,
        "failure_rate": round(1 - clean / calls, 4) if calls else None,
        "truncation_rate": round(truncated / calls, 4) if calls else None,
        "admitted_candidates": len(admitted),
        "refuted": len(refuted),
        "refuted_on_arrival_skeleton_wf": skeleton_wf_refuted,
        "refuted_on_arrival_rate": (round(skeleton_wf_refuted / len(admitted), 4)
                                    if admitted else None),
        "survivors": survivors,
        "logged_tokens": tokens,
        "yield_per_10k": round(survivors / (tokens / 10_000), 3) if tokens else None,
        "avg_prompt_tokens_per_call": round(prompt_tokens / calls) if calls else None,
    }


def run_arm(name: str, model: str, prompt_fn, schema_cls, vs_k: int,
            neighbourhood: int, budget: int, endpoint_factory) -> dict:
    root = Path("runs/small_burden") / name
    original_prompt, original_schema = loop_mod._prompt, loop_mod.ConjOut
    loop_mod._prompt = prompt_fn or original_prompt
    loop_mod.ConjOut = schema_cls
    try:
        summary = run(PROBLEMS, endpoint_factory(model), budget=budget,
                      root=root, vs_k=vs_k, neighbourhood=neighbourhood,
                      max_cycles=60)
    finally:
        loop_mod._prompt, loop_mod.ConjOut = original_prompt, original_schema
    metrics = arm_metrics(root)
    # prompt-side spend from the meter snapshot (burden documentation)
    tk = summary["tokens"]
    metrics["avg_prompt_tokens_per_call"] = (
        round(tk["prompt_tokens"] / tk["calls"]) if tk["calls"] else None)
    metrics["avg_completion_tokens_per_call"] = (
        round(tk["completion_tokens"] / tk["calls"]) if tk["calls"] else None)
    return {"arm": name, "model": model, "vs_k": vs_k,
            "neighbourhood": neighbourhood,
            "prompt_variant": "terse" if prompt_fn else "stock",
            "run_summary": summary, "metrics": metrics,
            "meter_equals_log": summary["meter_equals_log"]}


def evaluate(arms: dict) -> dict:
    """P1-P3 exactly as pre-registered; no other metric may decide."""
    def fr(name):
        return arms[name]["metrics"]["failure_rate"]

    def yl(name):
        return arms[name]["metrics"]["yield_per_10k"]

    def decided(*names):
        return all(arms[n]["metrics"]["conjecture_calls"] >= 8 for n in names)

    out = {}
    if not decided("A-flash-stock", "C-flash-compact"):
        out["P1"] = {"verdict": "UNDECIDED", "reason": "an arm died with < 8 calls"}
    elif fr("A-flash-stock") < 0.10:
        out["P1"] = {"verdict": "REFUTED",
                     "reason": f"degenerate guard: failure_rate(A)={fr('A-flash-stock')}"
                               " < 0.10 — nothing to halve; stock already fits"}
    else:
        halved = fr("C-flash-compact") <= 0.5 * fr("A-flash-stock")
        kept = (yl("C-flash-compact") or 0) >= 0.8 * (yl("A-flash-stock") or 0)
        out["P1"] = {"verdict": "CONFIRMED" if halved and kept else "REFUTED",
                     "halved_clause": halved, "yield_clause": kept,
                     "failure_A": fr("A-flash-stock"), "failure_C": fr("C-flash-compact"),
                     "yield_A": yl("A-flash-stock"), "yield_C": yl("C-flash-compact")}
    if not decided("B-flash-terse"):
        out["P2"] = {"verdict": "UNDECIDED", "reason": "arm B died with < 8 calls"}
    else:
        midpoint = (fr("A-flash-stock") + fr("C-flash-compact")) / 2
        out["P2"] = {"verdict": "CONFIRMED" if fr("B-flash-terse") <= midpoint else "REFUTED",
                     "failure_B": fr("B-flash-terse"), "midpoint_A_C": round(midpoint, 4)}
    if not decided("D-pro-stock", "A-flash-stock"):
        out["P3"] = {"verdict": "UNDECIDED", "reason": "arm D died with < 8 calls"}
    else:
        out["P3"] = {"verdict": ("CONFIRMED" if fr("D-pro-stock") < 0.5 * fr("A-flash-stock")
                                 else "REFUTED"),
                     "failure_D": fr("D-pro-stock"), "failure_A": fr("A-flash-stock")}
    return out


def mock_endpoint_factory(model: str):
    """Deterministic pipeline sanity: valid on first attempt, distinct per call."""
    counter = {"n": 0}

    def respond(prompt: str) -> str:
        counter["n"] += 1
        n = counter["n"]
        skeleton = json.dumps({
            "claim": f"mock claim {n} for burden sanity",
            "mechanism": f"mock mechanism {n}",
            "scope": {"covers": [f"case-{n}"], "excludes": []},
            "forbidden": [{"case": f"refuter {n}", "eval": "predicate:len(content) > 10"}],
            "prose_notes": ""})
        return json.dumps({"candidates": [{"content": skeleton, "typicality": 0.5}]})

    return llm.MockEndpoint(respond, name="mock", model=model)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=30_000)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--out", default=str(
        MINI.parent / "experiments" / "results" / "small_model_burden_report.json"))
    args = parser.parse_args()

    if args.mock:
        factory = mock_endpoint_factory
        budget = 3_000
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            print("DEEPSEEK_API_KEY not set", file=sys.stderr)
            return 1
        budget = args.budget

        def factory(model):
            return llm.HttpEndpoint(args.base_url, model, api_key=api_key,
                                    temperature=1.0, max_tokens=4000)

    arms = {}
    for name, model, prompt_fn, schema_cls, vs_k, nb in ARMS:
        print(f"--- arm {name} ({model}, vs_k={vs_k}, nb={nb}) ---", flush=True)
        arms[name] = run_arm(name, model, prompt_fn, schema_cls, vs_k, nb,
                             budget, factory)
        print(json.dumps(arms[name]["metrics"], indent=2), flush=True)

    report = {
        "prereg": "experiments/small_model_burden_prereg.yaml",
        "mode": "mock" if args.mock else "live",
        "budget_per_arm": budget,
        "problems": [p for p, _ in PROBLEMS],
        "arms": arms,
        "predictions": evaluate(arms),
        "accounting": {n: a["meter_equals_log"] for n, a in arms.items()},
    }
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["predictions"], indent=2))
    print(f"report -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
