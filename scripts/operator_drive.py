#!/usr/bin/env python
"""Operator-drive test: put a model in the ACTUAL operator seat.

The model receives AGENT.md's tool surface + rules + playbook and a goal,
then emits one JSON tool call per turn; calls execute against the real
MCP dispatch (mcp_server.call_tool) on a live root with a real engine.
We grade what it does: rule violations, invented tools, budget hygiene,
whether it reads results, and whether it reaches a surviving theory.

This measures the OPERATOR gap end-to-end (docs/OPERATOR_DIAGNOSIS.md):
the static probes test knowledge; this tests driving.

Usage: DEEPSEEK_API_KEY=... POOLSIDE_API_KEY=... python scripts/operator_drive.py
       [--operator deepseek-v4-flash] [--steps 12] [--engine-budget 60000]
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.llm.adapter import _extract_json  # noqa: E402
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402
from deepreason import mcp_server  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEEPSEEK = "https://api.deepseek.com"
POOLSIDE = "https://inference.poolside.ai/v1"

OPERATORS = {
    "deepseek-v4-flash": (DEEPSEEK, "DEEPSEEK_API_KEY", "none"),
    "deepseek-v4-pro": (DEEPSEEK, "DEEPSEEK_API_KEY", "none"),
    "poolside/laguna-m.1": (POOLSIDE, "POOLSIDE_API_KEY", None),
}

_TASK_SHARED = """CONSTRAINTS: at most {steps} tool calls total; total engine spend across
all run_cycles calls at most {engine_budget} tokens (pass token_budget!).

Respond with ONLY one JSON object per turn, no prose:
  {{"tool": "<name>", "arguments": {{...}}, "why": "<one sentence>"}}
Finish with: {{"tool": "done", "arguments": {{"summary": "<what you found,
quoting the surviving theory if any>"}}}}"""

SCENARIOS = {
    "tides": """You are the OPERATING AGENT for the DeepReason harness.

{agent_md}

GOAL: drive the harness on the tides problem until at least one theory
SURVIVES criticism and you have READ it (via the theory tool), or you
conclude the problem resists and say why. Seed exactly this problem first:

  problem: {{"id": "pi-tides", "description": "Explain why most coasts see
  two high tides a day and why their height varies across the month; name
  the mechanism explicitly and state one falsifiable consequence.",
  "criteria": ["k-mechanism", "k-tidal-facts"]}}
  commitments: [{{"id": "k-mechanism", "eval": "predicate:len(content) > 120"}},
  {{"id": "k-tidal-facts", "eval": "predicate:('moon' in content.lower() or
  'lunar' in content.lower()) and ('sun' in content.lower() or 'solar' in
  content.lower())"}}]

""" + _TASK_SHARED,
    "rubric": """You are the OPERATING AGENT for the DeepReason harness.

{agent_md}

GOAL: drive the harness on an informal history problem (judged by a rubric
STANDARD via trials) until at least one account SURVIVES and you have READ
it; if the docket shows a case, clear it with an appellate ruling. Seed
exactly this first:

  problem: {{"id": "pi-fall", "description": "Explain why the Western Roman
  Empire fell in the fifth century while the Eastern half survived; name a
  specific causal mechanism and one observation that would have refuted
  your account.", "criteria": ["kappa-fall"]}}
  commitments: [{{"id": "kappa-fall", "eval": "rubric:std-fall"}}]
  standard: {{"id": "std-fall", "rubric": "An acceptable account must name a
  specific causal mechanism (not a restatement), state at least one
  observation that would have refuted it, and explain the East-West
  asymmetry rather than ignoring it. Circular or unfalsifiable accounts
  violate this standard."}}

""" + _TASK_SHARED,
    # A REAL open problem (docs/OPERATOR_DIAGNOSIS.md, informal_ab reports):
    # pairwise judging saturates on near-tie informal outputs, which blocks
    # measuring the harness's own value. Whatever survives here is a usable
    # design, not a test fixture.
    "instrument": """You are the OPERATING AGENT for the DeepReason harness.

{agent_md}

GOAL: have the harness design a DISCRIMINATION INSTRUMENT for comparing
near-tie informal artifacts, drive it until at least two designs SURVIVE
criticism and you have READ them, clear any docket cases (the entry names
the standard), then finish with a comparative summary. Seed exactly this:

  problem: {{"id": "pi-instrument", "description": "Design a discrimination
  instrument that can reliably rank two near-tie informal artifacts, so
  that harness-vs-raw-generation comparisons stop saturating. Measured
  facts from this repository: three calibrated judge seats across two
  model families (planted-flaw error 0.0-0.125, verbosity bias 0.0-0.375)
  each preferred position A in BOTH presentation orders on rank-matched
  pairs; the order-swap screen discarded 8 of 9 votes; the sole surviving
  vote favored the weaker arm. Plain pairwise winner-picking saturates.
  Your instrument must name what is elicited and how it is scored, the
  regime where it discriminates, and forbidden cases measurable by running
  the instrument on this repository's committed A/B pairs within 150k
  tokens. Each candidate's content MUST be a JSON skeleton object, exactly
  this shape: {{\\"claim\\": str, \\"mechanism\\": str, \\"scope\\":
  {{\\"covers\\": [str], \\"excludes\\": [str]}}, \\"forbidden\\":
  [{{\\"case\\": str, \\"eval\\": \\"rubric:std-instrument\\"}}],
  \\"prose_notes\\": str}}.", "criteria": ["skeleton-wf", "kappa-instrument"]}}
  commitments: [{{"id": "kappa-instrument", "eval": "rubric:std-instrument"}}]
  standard: {{"id": "std-instrument", "rubric": "A discrimination-instrument
  proposal must: (1) name a specific elicitation and scoring mechanism
  (e.g. criterion-wise decomposed grading, tournament against planted
  anchors of known quality, calibrated absolute scoring) — not an
  aspiration ('judge better'); (2) state forbidden cases that are concrete
  measurable outcomes of running the instrument (an agreement rate, a
  position-bias delta, a discrimination rate on pairs of KNOWN quality
  difference); (3) directly address the measured failure modes: position
  bias that survives order-swap screening, verbosity bias, and same-family
  saturation. Instruments that assume an oracle judge or unmeasurable
  quantities violate this standard."}}

""" + _TASK_SHARED,
}


def agent_md_slice() -> str:
    text = (ROOT / "docs" / "AGENT.md").read_text()
    surface = text.split("## MCP tool surface")[1]
    return "## MCP tool surface" + surface[:5200]


def run_operator(model: str, steps: int, engine_budget: int, args) -> dict:
    base, key_env, reasoning = OPERATORS[model]
    endpoint = OpenAICompatEndpoint(
        base, model, api_key=os.environ[key_env], temperature=0.0,
        max_tokens=1200, json_mode=True, reasoning=reasoning,
    )
    slug = f"{model}_{args.scenario}".replace("/", "_").replace(".", "_")
    root = Path("runs/operator_drive") / slug
    if root.exists():
        shutil.rmtree(root)  # fresh seat each attempt (test scaffold, not harness data)

    history = SCENARIOS[args.scenario].format(
        agent_md=agent_md_slice(), steps=steps, engine_budget=engine_budget)
    transcript: list[dict] = []
    engine_spent = 0
    violations: list[str] = []
    invalid_json = 0

    for step in range(steps):
        try:
            raw = endpoint.complete(history[-24_000:])
        except EndpointError as e:
            transcript.append({"step": step, "error": f"operator endpoint: {e}"})
            break
        try:
            move = json.loads(_extract_json(raw))
            tool = move.get("tool", "")
            arguments = move.get("arguments") or {}
        except (ValueError, AttributeError):
            invalid_json += 1
            transcript.append({"step": step, "invalid_json": raw[:300]})
            if invalid_json >= 2:
                violations.append("aborted: two consecutive invalid-JSON turns")
                break
            history += "\n\nYour reply was not valid JSON. Reply with ONLY the JSON object."
            continue
        invalid_json = 0

        if tool == "done":
            transcript.append({"step": step, "done": arguments.get("summary", "")[:800]})
            break

        # Root injection is environment setup, not refereeing: always applied.
        arguments["root"] = str(root)
        if tool == "run_cycles":
            arguments.setdefault("config", str(ROOT / "config" / "deepseek.yaml"))
            budget = arguments.get("token_budget")
            if budget is None:
                violations.append(f"step {step}: run_cycles WITHOUT token_budget (rule 5)")
            if args.unrefereed:
                # No per-call rewriting: the operator manages its own budget.
                # A hard killswitch (1.5x the stated budget) is the only guard.
                if engine_spent >= int(engine_budget * 1.5):
                    result_text = "ERROR: drive killswitch — engine spend exceeded 1.5x budget"
                    transcript.append({"step": step, "tool": tool, "blocked": result_text})
                    history += f"\n\nTOOL CALL: {json.dumps(move)}\nRESULT: {result_text}"
                    continue
            else:
                budget = min(int(budget or 20_000), engine_budget - engine_spent, 30_000)
                if budget <= 0:
                    result_text = "ERROR: engine budget for this drive is exhausted"
                    transcript.append({"step": step, "tool": tool, "blocked": result_text})
                    history += f"\n\nTOOL CALL: {json.dumps(move)}\nRESULT: {result_text}"
                    continue
                arguments["token_budget"] = budget

        known = {"seed_problem", "run_cycles", "frontier", "theory", "why",
                 "eval_report", "docket", "appellate_rule", "narrate"}
        if tool not in known:
            violations.append(f"step {step}: invented/unknown tool {tool!r}")
        try:
            result_text = mcp_server.call_tool(tool, arguments)
        except Exception as e:  # noqa: BLE001 - operator mistakes are data
            result_text = f"ERROR: {e}"
            if "missing required argument" in str(e):
                violations.append(f"step {step}: bad arguments for {tool}")
        if tool == "run_cycles" and "token_spend" in result_text:
            try:
                engine_spent += json.loads(result_text)["token_spend"]["total"]
            except (ValueError, KeyError):
                pass

        transcript.append({"step": step, "tool": tool,
                           "arguments": {k: v for k, v in arguments.items() if k != "root"},
                           "why": move.get("why", "")[:200],
                           "result_head": result_text[:400]})
        history += (f"\n\nTOOL CALL: {json.dumps(move)}\n"
                    f"RESULT:\n{result_text[:2600]}")
    else:
        violations.append("used all steps without finishing")

    # Outcome grading from the root itself.
    outcome: dict = {"engine_spent": engine_spent, "violations": violations}
    try:
        from deepreason.harness import Harness
        from deepreason.ontology import Status

        h = Harness(root)
        addressed = {a for a, p in h.state.addr}
        outcome["survivors"] = sum(
            1 for a in addressed if h.state.status.get(a) == Status.ACCEPTED)
        outcome["events"] = h._next_seq
        outcome["read_theory"] = any(t.get("tool") == "theory" for t in transcript)
        outcome["read_report_or_frontier"] = any(
            t.get("tool") in ("eval_report", "frontier", "why", "narrate", "docket")
            for t in transcript)
        outcome["finished"] = any("done" in t for t in transcript)
    except Exception as e:  # noqa: BLE001
        outcome["root_state"] = f"unopenable: {e!r}"
    return {"operator": model, "outcome": outcome, "transcript": transcript}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operator", action="append", default=None,
                        choices=sorted(OPERATORS), help="repeatable; default: all")
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--engine-budget", type=int, default=60_000)
    parser.add_argument("--scenario", default="tides", choices=sorted(SCENARIOS))
    parser.add_argument("--unrefereed", action="store_true",
                        help="no per-call budget rewriting; killswitch only")
    args = parser.parse_args()
    for env in ("DEEPSEEK_API_KEY", "POOLSIDE_API_KEY"):
        if not os.environ.get(env):
            print(f"{env} not set", file=sys.stderr)
            return 1
    report = {"experiment": f"operator-drive (post-playbook, {args.scenario})",
              "drives": []}
    for model in (args.operator or sorted(OPERATORS)):
        print(f"=== operator: {model} ===", flush=True)
        drive = run_operator(model, args.steps, args.engine_budget, args)
        report["drives"].append(drive)
        print(json.dumps(drive["outcome"], indent=1), flush=True)
    out = ROOT / "experiments" / "results" / f"operator_drive_report_{args.scenario}.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
