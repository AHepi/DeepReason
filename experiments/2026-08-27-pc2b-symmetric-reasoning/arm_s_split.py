#!/usr/bin/env python3
"""ARM S for P-C2b: blind sampling that MIRRORS the harness's split protocol.

The operator's controlling instruction, 2026-08-27: "The two arms must be
SYMMETRIC in this: same model, same reasoning setting, same effective caps",
and for ARM S specifically, "enable the same reasoning mode on its raw calls,
with a completion cap sized so answers survive (mirror the same
reasoning/emission split the profile uses)".

P-C1's `arm_s.py` cannot be reused unchanged here and the reason is the whole
point of this tranche: it makes ONE call with no reasoning field and a 32768
cap, so the model thinks and answers inside one budget. The harness does not
do that -- `llm/split.py` splits every thinking seat into two provider legs.
An ARM S that stayed one-shot would differ from ARM H in the one dimension
P-C2b exists to hold constant.

SYMMETRY IS IMPORTED, NOT RESTATED. The leg budgets come from the SHIPPED
planner, `deepreason.llm.split.plan_split`, called with the same mode,
ceiling, extraction size and provider the run's config gives the harness. Two
hand-written numbers would be two numbers to keep in agreement, and the first
time they drifted the comparison would silently stop being a comparison.

WHAT IS REUSED UNCHANGED, because P-C2b inherits P-C1's instance:
    question.py   the frozen question bytes (digest asserted)
    checker.py    the exact-rational scorer, sole authority for every score

Usage:
    python arm_s_split.py --token-budget 200000 --out arm_s
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

REPO = pathlib.Path(__file__).resolve().parents[2]
FRONTIER = REPO / "experiments" / "2026-08-25-change-constructive-frontier"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(FRONTIER))

import checker  # noqa: E402  (P-C1's committed checker, IMPORTED)
from question import QUESTION  # noqa: E402  (P-C1's frozen bytes, IMPORTED)

from deepreason.llm.split import plan_split  # noqa: E402  (the SHIPPED planner)

ENDPOINT = "https://ollama.com/v1/chat/completions"
MODEL = "glm-5.2"
TEMPERATURE = 1.0
CEILING = 32768
EXTRACTION_TOKENS = 512
TIMEOUT_S = 900
QUESTION_SHA256 = "64b724c4118320989925d111501a8e41cd4518d9b631bb81a6ae048d3cfb5c7e"

# The extraction leg's instruction. It serializes; it does not solve. Kept
# deliberately close to what the harness's own extraction leg asks for: take
# whatever deliberation exists -- possibly truncated, possibly empty -- and
# emit only the wire format.
EXTRACT_INSTRUCTION = (
    "Below is your own deliberation on a problem. It may be incomplete or cut "
    "off. Do not continue reasoning and do not revise it. Emit ONLY the final "
    "answer in exactly the required format: one line \"POINT x y\" for each of "
    "the 13 points, with x and y as decimals with at most 6 decimal places, "
    "then a final line \"CLAIM v\" giving the claimed minimum triangle area. "
    "Output nothing else."
)


def _post(body: dict) -> dict:
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        return json.loads(response.read().decode())


def sample(plan) -> dict:
    """One blind construction, through the same two legs the harness uses.

    Every token either leg spends is counted. The operator's rule: "measured
    as total logged tokens (reasoning tokens count -- they are paid tokens)".
    """
    started = time.time()

    # LEG 1 -- deliberate. Reasoning left ON by sending no reasoning field
    # (`reasoning_disabled`: unset is NOT off), bounded at B_r, and ALLOWED to
    # be cut off exactly as the harness's reason leg is.
    reason_body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": QUESTION}],
        "temperature": TEMPERATURE,
        "max_tokens": plan.reason_max_tokens,
    }
    reason = _post(reason_body)
    reason_msg = reason["choices"][0]["message"]
    reason_usage = reason.get("usage") or {}
    trace = (reason_msg.get("reasoning") or "") + "\n" + (reason_msg.get("content") or "")

    # LEG 2 -- serialize. Thinking switched OFF so the whole of B_a reaches
    # the answer, fed whatever the first leg produced.
    extract_body = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": f"{EXTRACT_INSTRUCTION}\n\n---\n{trace}"}
        ],
        "temperature": TEMPERATURE,
        "max_tokens": plan.extract_max_tokens,
    }
    if plan.extract_reasoning is not None:
        extract_body["reasoning_effort"] = plan.extract_reasoning
    extract = _post(extract_body)
    extract_msg = extract["choices"][0]["message"]
    extract_usage = extract.get("usage") or {}

    text = extract_msg.get("content") or ""
    verdict = checker.check(text)
    reason_total = int(reason_usage.get("total_tokens") or 0) or (
        int(reason_usage.get("prompt_tokens") or 0)
        + int(reason_usage.get("completion_tokens") or 0)
    )
    extract_total = int(extract_usage.get("total_tokens") or 0) or (
        int(extract_usage.get("prompt_tokens") or 0)
        + int(extract_usage.get("completion_tokens") or 0)
    )
    return {
        "text": text,
        "verdict": verdict,
        "elapsed_s": round(time.time() - started, 1),
        "reason_leg": {
            "max_tokens": plan.reason_max_tokens,
            "prompt_tokens": reason_usage.get("prompt_tokens"),
            "completion_tokens": reason_usage.get("completion_tokens"),
            "tokens": reason_total,
            "reasoning_chars": len(reason_msg.get("reasoning") or ""),
            "finish_reason": reason["choices"][0].get("finish_reason"),
        },
        "extract_leg": {
            "max_tokens": plan.extract_max_tokens,
            "reasoning_effort": plan.extract_reasoning,
            "prompt_tokens": extract_usage.get("prompt_tokens"),
            "completion_tokens": extract_usage.get("completion_tokens"),
            "tokens": extract_total,
            "reasoning_chars": len(extract_msg.get("reasoning") or ""),
            "finish_reason": extract["choices"][0].get("finish_reason"),
        },
        "tokens": reason_total + extract_total,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-budget", type=int, required=True)
    parser.add_argument("--out", default="arm_s")
    parser.add_argument(
        "--max-samples", type=int, default=200,
        help="runaway guard only; the token budget is the real stop",
    )
    args = parser.parse_args()

    if not os.environ.get("OLLAMA_API_KEY", "").strip():
        print("FATAL: OLLAMA_API_KEY is not set", file=sys.stderr)
        return 1

    from deepreason.preparation import _question_digest

    if _question_digest(QUESTION) != QUESTION_SHA256:
        print("FATAL: question bytes drifted", file=sys.stderr)
        return 1

    plan = plan_split(
        mode="auto", ceiling=CEILING, extraction_tokens=EXTRACTION_TOKENS,
        provider="ollama", reasoning=None,
    )
    if not plan.armed:
        print(f"FATAL: the shipped planner did not arm: {plan.notice}", file=sys.stderr)
        return 1
    print(f"[arm-s] mirroring the harness split: B_r={plan.reason_max_tokens} "
          f"B_a={plan.extract_max_tokens} extract_reasoning={plan.extract_reasoning!r}")

    out = pathlib.Path(args.out)
    (out / "samples").mkdir(parents=True, exist_ok=True)
    spent = best = 0
    best = None
    n_valid = n_refuted = errors = 0

    with (out / "results.jsonl").open("w") as ledger:
        for index in range(args.max_samples):
            if spent >= args.token_budget:
                print(f"[arm-s] budget reached: {spent} >= {args.token_budget}")
                break
            try:
                result = sample(plan)
            except (urllib.error.URLError, OSError, KeyError, ValueError) as error:
                errors += 1
                print(f"[arm-s] {index:04d} TRANSPORT {type(error).__name__}: {error}")
                ledger.write(json.dumps({"index": index, "error": str(error)}) + "\n")
                ledger.flush()
                continue

            spent += result["tokens"]
            verdict = result["verdict"]
            (out / "samples" / f"{index:04d}.txt").write_text(result["text"])
            row = {
                "index": index,
                "tokens": result["tokens"],
                "cumulative_tokens": spent,
                "elapsed_s": result["elapsed_s"],
                "reason_leg": result["reason_leg"],
                "extract_leg": result["extract_leg"],
                "valid": verdict.get("valid"),
                "code": verdict.get("code"),
                "score": verdict.get("score"),
                "score_exact": verdict.get("score_exact"),
                "claim": verdict.get("claim"),
                "claim_confirmed": verdict.get("claim_confirmed"),
                "n_points": verdict.get("n_points"),
            }
            ledger.write(json.dumps(row) + "\n")
            ledger.flush()

            if verdict.get("valid"):
                n_valid += 1
                if best is None or verdict["score"] > best["score"]:
                    best = {"index": index, "score": verdict["score"],
                            "score_exact": verdict["score_exact"]}
            else:
                n_refuted += 1
            print(f"[arm-s] {index:04d} tokens={result['tokens']:6d} "
                  f"cum={spent:7d}/{args.token_budget} "
                  f"({result['elapsed_s']:.0f}s) valid={verdict.get('valid')} "
                  f"score={verdict.get('score')} best={best['score'] if best else None}")

    summary = {
        "arm": "S (P-C2b, split-mirroring)",
        "model": MODEL,
        "temperature": TEMPERATURE,
        "reasoning": "ON (no reasoning field on the reason leg)",
        "split": {
            "source": "deepreason.llm.split.plan_split -- the SHIPPED planner",
            "ceiling": CEILING,
            "reason_max_tokens": plan.reason_max_tokens,
            "extract_max_tokens": plan.extract_max_tokens,
            "extract_reasoning": plan.extract_reasoning,
        },
        "token_budget": args.token_budget,
        "tokens_spent": spent,
        "n_samples": n_valid + n_refuted,
        "n_valid": n_valid,
        "n_refuted": n_refuted,
        "n_transport_errors": errors,
        "best_score": best["score"] if best else None,
        "best_score_exact": best["score_exact"] if best else None,
        "best_sample_index": best["index"] if best else None,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
