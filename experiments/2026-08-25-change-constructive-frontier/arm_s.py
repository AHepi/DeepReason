#!/usr/bin/env python3
"""ARM S: the sampling baseline. Blind repeated one-shot construction.

SPEC.md S8/S9, REQUEST.md R21, R19.

WHAT THIS ARM IS.  The same model, the same question, the same total token
budget as ARM H -- and no machinery at all.  Each sample is an independent
one-shot request that sees nothing: no other sample, no score, no history,
no criticism.  Every reply is scored by the SAME exact checker, and the best
valid one is kept.  That is the whole arm.

WHY IT IS THE RIGHT COMPARATOR, AND WHY IT IS A HARD ONE.
`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q4 records zero of 36
published comparisons beating repeated sampling at equal cost, with
self-assessing methods below the baseline in all 18 of theirs.  Q4 also
states its own scope limit: on open-ended work majority voting does not
exist, so the strongest competitor to criticism is normally unavailable.
Here it IS available, in a stronger form than counting -- an EXACT CHECKER
picks the best of N.  So this baseline is deliberately harder to beat than
the one Q4 measured, and the harness gets no easy win.

DELIBERATE DESIGN CHOICES, REGISTERED BEFORE LAUNCH:

  * `temperature` is set EXPLICITLY to 1.0.  A near-deterministic sampler
    would return near-identical replies and the baseline would be trivially
    weak -- which would make ARM H look good for the wrong reason.  The
    baseline has to be allowed to explore or the comparison is rigged.
  * `max_tokens` matches ARM H's seat cap (32768) so neither arm is
    truncated on terms the other is not.
  * Matching is on MEASURED spend, not on the registered cap: sampling
    stops once cumulative provider-counted tokens would exceed ARM H's
    actual total.  Matching on caps would let an arm that under-spends look
    cheap.
  * Every raw reply is preserved, scored or not.  A reply that failed to
    parse is evidence about this arm, not a sample to quietly drop.

NO HARNESS MACHINERY (R21).  This file imports `checker` and the standard
library.  It imports nothing from `deepreason`; `question.py` is a shared
literal with no imports of its own, which is how both arms are guaranteed
to ask the same bytes without either keeping a copy.

Usage:
    python arm_s.py --token-budget 2413556 [--out arm_s] [--max-samples 400]
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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import checker  # noqa: E402
from question import QUESTION  # noqa: E402

ENDPOINT = "https://ollama.com/v1/chat/completions"
MODEL = "glm-5.2"
TEMPERATURE = 1.0
MAX_TOKENS = 32768
TIMEOUT_S = 180


def sample(api_key: str) -> dict:
    """One blind one-shot construction request."""
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": QUESTION}],
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--token-budget",
        type=int,
        required=True,
        help="ARM H's MEASURED total token spend (SPEC.md S9)",
    )
    parser.add_argument("--out", default="arm_s")
    parser.add_argument(
        "--max-samples",
        type=int,
        default=1000,
        help="runaway guard only; the token budget is the real stop",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OLLAMA_API_KEY", "").strip()
    if not api_key:
        print("FATAL: OLLAMA_API_KEY is not set", file=sys.stderr)
        return 1

    out = pathlib.Path(args.out)
    (out / "samples").mkdir(parents=True, exist_ok=True)
    results_path = out / "results.jsonl"

    spent = 0
    best = None
    n_valid = 0
    n_refuted = 0
    errors = 0

    with results_path.open("w") as ledger:
        for index in range(args.max_samples):
            if spent >= args.token_budget:
                print(f"[arm-s] budget reached: {spent} >= {args.token_budget}")
                break

            started = time.time()
            try:
                payload = sample(api_key)
            except Exception as exc:  # noqa: BLE001
                # Deliberately broad. A narrower tuple
                # (URLError, HTTPError, TimeoutError) let
                # http.client.RemoteDisconnected escape and kill the run at
                # 72% of budget -- it is an OSError, not a URLError. Any
                # transport failure must be RECORDED and stepped over, never
                # allowed to end the arm early: an arm that dies partway
                # through its budget is an unmatched arm, which is worse
                # than a arm with a logged error in it.
                errors += 1
                # A transport failure is recorded, not retried into silence:
                # an arm that hides its failures is not a measured arm.
                ledger.write(
                    json.dumps({"index": index, "error": str(exc), "tokens": 0}) + "\n"
                )
                ledger.flush()
                if errors > 20:
                    print("[arm-s] too many transport errors; stopping", file=sys.stderr)
                    break
                time.sleep(2)
                continue

            usage = payload.get("usage") or {}
            total = int(usage.get("total_tokens") or 0)
            choices = payload.get("choices") or [{}]
            text = (choices[0].get("message") or {}).get("content") or ""

            # Preserve the raw reply BEFORE scoring it. Scoring can be
            # redone from the file; a discarded reply cannot.
            (out / "samples" / f"{index:04d}.txt").write_text(text)

            verdict = checker.check(text)
            spent += total
            if verdict["valid"]:
                n_valid += 1
                if best is None or verdict["score"] > best["score"]:
                    best = {**verdict, "index": index}
            else:
                n_refuted += 1

            ledger.write(
                json.dumps(
                    {
                        "index": index,
                        "tokens": total,
                        "prompt_tokens": usage.get("prompt_tokens"),
                        "completion_tokens": usage.get("completion_tokens"),
                        "elapsed_s": round(time.time() - started, 2),
                        "cumulative_tokens": spent,
                        **verdict,
                    }
                )
                + "\n"
            )
            ledger.flush()

            print(
                f"[arm-s] {index:04d} tokens={total:6d} cum={spent:8d}/"
                f"{args.token_budget} valid={verdict['valid']} "
                f"score={verdict['score']} best={best['score'] if best else None}",
                flush=True,
            )

    summary = {
        "arm": "S",
        "model": MODEL,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "token_budget_matched_to_arm_h": args.token_budget,
        "tokens_spent": spent,
        "n_samples": n_valid + n_refuted,
        "n_valid": n_valid,
        "n_refuted": n_refuted,
        "n_transport_errors": errors,
        "best_score": best["score"] if best else None,
        "best_score_exact": best["score_exact"] if best else None,
        "best_sample_index": best["index"] if best else None,
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
