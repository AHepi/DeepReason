#!/usr/bin/env python
"""Live λ dose-response pilot (spec §11.8) against DeepSeek.

Oracle-blind, oracle-scored, on a program-checkable synthesis problem: a
pi mnemonic whose word lengths must encode 3.1415926. The verifier EXISTS
in both arms but is registered into the loop only for lambda_full; the
lambda0 arm runs the closed loop (argumentative criticism only) and the
oracle scores every conjecture post-hoc.

Usage:
    DEEPSEEK_API_KEY=... python scripts/lambda_live.py \
        --root runs/lambda --replicates 3 --cycles 12 --per-run-budget 100000

HONESTY NOTE: with fewer replicates/cycles than the pre-registration
(>=5 x 30), this is a PILOT; the deviation is recorded in the report JSON
and the verdict is labeled accordingly. Thresholds themselves are the
pre-registered ones, unedited.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.config import Config  # noqa: E402
from deepreason.experiments import lambda_run  # noqa: E402
from deepreason.llm.adapter import LLMAdapter  # noqa: E402
from deepreason.llm.budget import TokenMeter  # noqa: E402
from deepreason.llm.endpoints import OpenAICompatEndpoint  # noqa: E402
from deepreason.storage.blobs import BlobStore  # noqa: E402

PREREG = Path(__file__).resolve().parents[1] / "experiments" / "lambda_preregistration.yaml"

# The withheld verifier: word lengths encode the first 8 digits of pi.
ORACLE_EVAL = (
    'predicate:[len(w) for w in re.findall(r"[A-Za-z]+", content)][:8] '
    "== [3, 1, 4, 1, 5, 9, 2, 6] and len(re.findall(r\"[A-Za-z]+\", content)) >= 8"
)
PROBLEM = (
    "Compose one grammatical English sentence that encodes the first 8 digits "
    "of pi (3.1415926) in its word lengths: the 1st word has exactly 3 letters, "
    "the 2nd exactly 1, then 4, 1, 5, 9, 2, 6 letters. Only letters count — "
    "punctuation and digits are ignored. The sentence should read naturally."
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="runs/lambda")
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--cycles", type=int, default=12)
    parser.add_argument("--per-run-budget", type=int, default=100_000)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"{args.api_key_env} is not set", file=sys.stderr)
        return 1

    config = Config(
        VS_K=2, N_SCHOOLS=0, FLOOR=0, CAPTURE_W=10, RETRY_MAX=2,
        ARG_CRIT_PER_CYCLE=2,
    )
    grand_total = 0
    results: dict[str, list[dict]] = {}
    for arm, in_loop in (("lambda0", False), ("lambda_full", True)):
        results[arm] = []
        for replicate in range(args.replicates):
            root = Path(args.root) / arm / str(replicate)
            meter = TokenMeter(budget=args.per_run_budget)

            def endpoint(temperature: float, cap: int) -> OpenAICompatEndpoint:
                return OpenAICompatEndpoint(
                    args.base_url, args.model, api_key=api_key,
                    temperature=temperature, max_tokens=cap, json_mode=True,
                )

            # v4-pro reasons before answering; letter-counting tasks consume
            # the completion budget as reasoning, so caps need real headroom
            # (1200 returned EMPTY content on every call — all reasoning).
            adapter = LLMAdapter(
                {
                    "conjecturer": endpoint(1.0, 4000),
                    "argumentative_critic": endpoint(0.7, 1400),
                },
                BlobStore(root / "blobs"),
                retry_max=config.RETRY_MAX,
                meter=meter,
            )
            print(f"[{arm} #{replicate}] running {args.cycles} cycles ...", flush=True)
            result = lambda_run.run_arm(
                root,
                program_criteria_in_loop=in_loop,
                oracle_eval=ORACLE_EVAL,
                problem_description=PROBLEM,
                adapter=adapter,
                config=config,
                cycles=args.cycles,
            )
            result["tokens"] = meter.total
            grand_total += meter.total
            results[arm].append(result)
            print(
                f"[{arm} #{replicate}] oracle_pass={result['oracle_pass_rate']:.2f} "
                f"conjectures={result['n_conjectures']} tokens={meter.total}",
                flush=True,
            )

    summary = lambda_run.summarize(results)
    verdict = lambda_run.verdict(summary, PREREG)
    verdict["deviation_from_preregistration"] = (
        f"PILOT: {args.replicates} replicates x {args.cycles} cycles "
        "(pre-registration requires >=5 x 30); thresholds unedited"
    )
    report_path = Path(args.root) / "lambda_report.json"
    lambda_run.record(report_path, summary, verdict)

    print(f"\ntotal tokens across all runs: {grand_total}")
    print("\n=== SUMMARY (distributions) ===")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("\n=== VERDICT (against pre-registered falsifier) ===")
    print(json.dumps(verdict, indent=2, sort_keys=True))
    print(f"\nreport written: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
