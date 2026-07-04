#!/usr/bin/env python
"""Live λ dose-response experiment (spec §11.8) against DeepSeek.

Oracle-blind, oracle-scored: the verifier EXISTS in both arms but is
registered into the loop only for lambda_full; lambda0 runs the closed loop
(argumentative criticism only) and the oracle scores everything post-hoc.

v2 protocol (experiments/lambda_preregistration_v2.yaml, committed before
any v2 run): an arbitrary word-length sequence (no famous mnemonic — blocks
memorization), scheduler focus-locked to the seed problem (no side-problem
dilution), primary metric = distinct verified passers per run.

Run one arm per process so both arms proceed in parallel:
    DEEPSEEK_API_KEY=... python scripts/lambda_live.py --arm lambda0 \
        --root runs/lambda_v2 --replicates 5 --cycles 30 --focus-lock
    DEEPSEEK_API_KEY=... python scripts/lambda_live.py --arm lambda_full ...

Then aggregate:
    python scripts/lambda_live.py --aggregate \
        runs/lambda_v2/lambda0_results.json runs/lambda_v2/lambda_full_results.json \
        --root runs/lambda_v2
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

PREREG_DIR = Path(__file__).resolve().parents[1] / "experiments"
DEFAULT_SEQUENCE = "4,2,9,3,7,5,8,2,6,10"


def oracle_for(sequence: list[int]) -> tuple[str, str]:
    n = len(sequence)
    eval_str = (
        f'predicate:[len(w) for w in re.findall(r"[A-Za-z]+", content)][:{n}] '
        f"== {sequence} and len(re.findall(r\"[A-Za-z]+\", content)) >= {n}"
    )
    spec = ", ".join(str(d) for d in sequence)
    problem = (
        f"Compose one grammatical English sentence of at least {n} words whose "
        f"first {n} words have exactly these letter counts, in order: {spec}. "
        "Only letters count — punctuation and digits are ignored. The sentence "
        "should read naturally. Getting every word length exactly right matters "
        "more than elegance."
    )
    return eval_str, problem


def run_one_arm(args) -> int:
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"{args.api_key_env} is not set", file=sys.stderr)
        return 1
    sequence = [int(x) for x in args.sequence.split(",")]
    oracle_eval, problem = oracle_for(sequence)
    in_loop = args.arm == "lambda_full"
    config = Config(
        VS_K=2, N_SCHOOLS=0, FLOOR=0, CAPTURE_W=10, RETRY_MAX=2,
        ARG_CRIT_PER_CYCLE=1,
        FOCUS_PROBLEM="pi-arm" if args.focus_lock else None,
    )
    runs = []
    grand_total = 0
    for replicate in range(args.replicates):
        root = Path(args.root) / args.arm / str(replicate)
        meter = TokenMeter(budget=args.per_run_budget)

        def endpoint(temperature: float, cap: int, reasoning=None) -> OpenAICompatEndpoint:
            return OpenAICompatEndpoint(
                args.base_url, args.model, api_key=api_key,
                temperature=temperature, max_tokens=cap, json_mode=True,
                request_logprobs=True, reasoning=reasoning,
            )

        # The letter-count task is one v4-pro demonstrably solves BY
        # reasoning, so the conjecturer keeps thinking — but budgeted
        # (docs/TOKEN_ECONOMY.md angle 1); the critic runs without.
        conj_reasoning = (
            int(args.conjecturer_reasoning)
            if args.conjecturer_reasoning.isdigit()
            else (None if args.conjecturer_reasoning == "default" else args.conjecturer_reasoning)
        )
        adapter = LLMAdapter(
            {
                "conjecturer": endpoint(1.0, 4000, reasoning=conj_reasoning),
                "argumentative_critic": endpoint(0.7, 1400, reasoning="none"),
            },
            BlobStore(root / "blobs"),
            retry_max=config.RETRY_MAX,
            meter=meter,
        )
        print(f"[{args.arm} #{replicate}] running {args.cycles} cycles ...", flush=True)
        result = lambda_run.run_arm(
            root,
            program_criteria_in_loop=in_loop,
            oracle_eval=oracle_eval,
            problem_description=problem,
            adapter=adapter,
            config=config,
            cycles=args.cycles,
        )
        result["tokens"] = meter.total
        grand_total += meter.total
        runs.append(result)
        print(
            f"[{args.arm} #{replicate}] passes={result['oracle_passes']} "
            f"seed_rate={result['oracle_pass_rate_seed']:.2f} "
            f"blocks={result['gate_blocks']} conjectures={result['n_conjectures']} "
            f"tokens={meter.total}",
            flush=True,
        )

    out_path = Path(args.results_out or (Path(args.root) / f"{args.arm}_results.json"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"arm": args.arm, "runs": runs}, indent=2, sort_keys=True))
    print(f"\n[{args.arm}] total tokens: {grand_total}\nresults written: {out_path}")
    return 0


def aggregate(args) -> int:
    results: dict[str, list[dict]] = {}
    for path in args.aggregate:
        data = json.loads(Path(path).read_text())
        results[data["arm"]] = data["runs"]
    prereg = Path(args.prereg)
    summary = lambda_run.summarize(results)
    verdict = lambda_run.verdict(summary, prereg)
    if args.deviation:
        verdict["deviation_from_preregistration"] = args.deviation
    report_path = Path(args.root) / "lambda_report.json"
    lambda_run.record(report_path, summary, verdict)
    print(json.dumps({"summary": summary, "verdict": verdict}, indent=2, sort_keys=True))
    print(f"\nreport written: {report_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["lambda0", "lambda_full"], default=None)
    parser.add_argument("--aggregate", nargs=2, metavar="RESULTS_JSON", default=None)
    parser.add_argument("--root", default="runs/lambda_v2")
    parser.add_argument("--replicates", type=int, default=5)
    parser.add_argument("--cycles", type=int, default=30)
    parser.add_argument("--per-run-budget", type=int, default=200_000)
    parser.add_argument("--sequence", default=DEFAULT_SEQUENCE)
    parser.add_argument("--focus-lock", action="store_true")
    parser.add_argument("--results-out", default=None)
    parser.add_argument("--prereg", default=str(PREREG_DIR / "lambda_preregistration_v2.yaml"))
    parser.add_argument("--deviation", default=None)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--conjecturer-reasoning", default="2000",
                        help="default|none|high|max|<int budget tokens>")
    args = parser.parse_args()

    if args.aggregate:
        return aggregate(args)
    if args.arm is None:
        print("pass --arm lambda0|lambda_full, or --aggregate a.json b.json", file=sys.stderr)
        return 1
    return run_one_arm(args)


if __name__ == "__main__":
    sys.exit(main())
