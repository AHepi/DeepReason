#!/usr/bin/env python
"""Render the committed thesis for a finished run's problem (views/thesis).

Read-only over the root: the adapter gets a SCRATCH blob store, the run's
log and blobs are untouched, and the call's spend is printed in the
output header instead of landing on the log.

Usage:
    DEEPSEEK_API_KEY=... python scripts/thesis.py \\
        --root runs/arrow_full --problem pi-arrow [--model deepseek-v4-pro]
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.harness import Harness  # noqa: E402
from deepreason.llm.adapter import LLMAdapter, SchemaRepairError  # noqa: E402
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter  # noqa: E402
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402
from deepreason.storage.blobs import BlobStore  # noqa: E402
from deepreason.views.thesis import render_thesis, thesis  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--problem", default=None,
                        help="problem id (default: the root's seed problem)")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--budget", type=int, default=6000,
                        help="evidence pack budget in TOKENS (chars/4)")
    parser.add_argument("--token-budget", type=int, default=40_000,
                        help="hard meter ceiling for the thesis call(s)")
    parser.add_argument("--reasoning", default="none")
    parser.add_argument("--out", default=None, help="also write markdown here")
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"{args.api_key_env} not set", file=sys.stderr)
        return 1

    harness = Harness(Path(args.root))
    endpoint = OpenAICompatEndpoint(
        args.base_url, args.model, api_key=api_key, temperature=0.3,
        max_tokens=6000, json_mode=True,
        reasoning=None if args.reasoning == "default" else args.reasoning)
    meter = TokenMeter(budget=args.token_budget)
    scratch = BlobStore(Path(tempfile.mkdtemp(prefix="thesis-blobs-")))
    adapter = LLMAdapter({"thesis": endpoint}, scratch, retry_max=2, meter=meter)

    try:
        result = thesis(harness, adapter, problem_id=args.problem,
                        budget_chars=args.budget * 4)
    except (SchemaRepairError, EndpointError, TokenBudgetExceeded) as e:
        print(f"thesis failed: {e}", file=sys.stderr)
        return 1

    prose = render_thesis(result)
    print(prose)
    if args.out:
        Path(args.out).write_text(prose + "\n\n---\n" + json.dumps(
            {k: result[k] for k in ("problem", "citations", "citation_check",
                                    "pack_chars", "spend")}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
