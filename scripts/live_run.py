#!/usr/bin/env python
"""Live P6 run against an OpenAI-compatible provider (default: DeepSeek).

Usage:
    DEEPSEEK_API_KEY=... python scripts/live_run.py \
        --root runs/live --cycles 4 [--model deepseek-v4-pro] [--dry-run]

Resolves model ids against the provider's /models list: --model wins if
listed; otherwise prefers ids containing (v4, pro), then chat, then the
first listed. The judge ensemble uses the primary model plus the most
different other model available (same-provider approximation of the §9
cross-family rule — noted in the report). Prints the P6 eval report and
the surviving frontier at the end; the run directory replays like any
other harness.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.config import load as load_config  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.llm.adapter import LLMAdapter  # noqa: E402
from deepreason.llm.endpoints import OpenAICompatEndpoint  # noqa: E402
from deepreason.ontology import Commitment, Problem, ProblemProvenance  # noqa: E402
from deepreason.report import eval_report  # noqa: E402
from deepreason.scheduler.scheduler import Scheduler  # noqa: E402
from deepreason.views.theory import theory  # noqa: E402


def list_models(base_url: str, api_key: str) -> list[str]:
    request = urllib.request.Request(
        base_url.rstrip("/") + "/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    return [m["id"] for m in data.get("data", [])]


def pick_model(available: list[str], preferred: str | None) -> str:
    if preferred and preferred in available:
        return preferred
    for want in (("v4", "pro"), ("v4",), ("pro",), ("chat",)):
        hits = [m for m in available if all(w in m.lower() for w in want)]
        if hits:
            return sorted(hits)[0]
    if not available:
        raise SystemExit("provider returned no models")
    return sorted(available)[0]


def pick_alt(available: list[str], primary: str) -> str:
    others = [m for m in available if m != primary]
    # Prefer a reasoner-style alternate for the second judge seat.
    for want in ("reason", "r1"):
        hits = [m for m in others if want in m.lower()]
        if hits:
            return sorted(hits)[0]
    return sorted(others)[0] if others else primary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="runs/live")
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--model", default=None, help="preferred model id (e.g. a V4 pro variant)")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "deepseek.yaml"))
    parser.add_argument("--dry-run", action="store_true", help="resolve models and exit")
    args = parser.parse_args()

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"{args.api_key_env} is not set — add the key and rerun.", file=sys.stderr)
        return 1

    available = list_models(args.base_url, api_key)
    primary = pick_model(available, args.model)
    alt = pick_alt(available, primary)
    print(f"models available: {available}")
    print(f"primary model: {primary}   judge alternate: {alt}")
    if args.dry_run:
        return 0

    config = load_config(Path(args.config))

    def endpoint(model: str, temperature: float) -> OpenAICompatEndpoint:
        return OpenAICompatEndpoint(args.base_url, model, api_key=api_key, temperature=temperature)

    adapter = LLMAdapter(
        {
            "conjecturer": endpoint(primary, 1.0),
            "argumentative_critic": endpoint(primary, 0.7),
            "defender": endpoint(primary, 0.7),
            "variator": endpoint(primary, 1.0),
            "synthesizer": endpoint(primary, 0.9),
            "judge": [endpoint(primary, 0.0), endpoint(alt, 0.0)],
        },
        None,  # blob store attached after the harness exists
        retry_max=config.RETRY_MAX,
    )

    harness = Harness(Path(args.root))
    adapter.blobs = harness.blobs
    # A problem with real, program-checkable teeth: the criteria are cheap
    # predicates, so every verdict in the loop is exogenous (lambda = 1).
    harness.register_commitment(
        Commitment(id="k-mechanism", eval="predicate:len(content) > 120")
    )
    harness.register_commitment(
        Commitment(
            id="k-tidal-facts",
            eval=(
                "predicate:('moon' in content.lower() or 'lunar' in content.lower()) "
                "and ('sun' in content.lower() or 'solar' in content.lower())"
            ),
        )
    )
    harness.register_problem(
        Problem(
            id="pi-tides",
            description=(
                "Explain why most coasts see two high tides a day, why their "
                "height varies across the month, and why a few seas (e.g. the "
                "Gulf of Mexico) see only one."
            ),
            criteria=["k-mechanism", "k-tidal-facts"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )

    scheduler = Scheduler(harness, adapter, config)
    result = scheduler.run(args.cycles)

    print("\n=== P6 EVAL REPORT ===")
    print(json.dumps(eval_report(harness, config), indent=2, sort_keys=True))
    print("\n=== FRONTIER ===")
    for aid in result["frontier"]:
        print(f"\n--- {aid[:12]} ---")
        print(theory(aid, harness.state, harness.blobs, log=harness.log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
