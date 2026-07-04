#!/usr/bin/env python
"""Live P6 run against an OpenAI-compatible provider (default: DeepSeek).

Usage:
    DEEPSEEK_API_KEY=... python scripts/live_run.py \
        --root runs/live --cycles 4 --suite republic \
        --token-budget 400000 [--model deepseek-v4-pro] [--dry-run]

Model ids resolve against the provider's /models list (--model wins if
listed; else v4+pro > v4 > pro > chat > first). The judge ensemble is the
primary model plus the most different other model available — a
same-provider approximation of the §9 cross-family rule, noted honestly.

Suites:
  tides     — formal-ish: program predicates only, every verdict exogenous.
  republic  — informal (§10): skeleton-wf pinned, a registered standard,
              a rubric criterion judged under the live trial protocol
              (judge ensemble, order-swap, paraphrase spot-check).

The --token-budget is a HARD ceiling on prompt+completion tokens for the
whole run; the scheduler stops gracefully when it is reached.
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
from deepreason.informal.skeleton import skeleton_wf_commitment  # noqa: E402
from deepreason.informal.standards import register_standard  # noqa: E402
from deepreason.llm.adapter import LLMAdapter  # noqa: E402
from deepreason.llm.budget import TokenMeter  # noqa: E402
from deepreason.llm.endpoints import OpenAICompatEndpoint  # noqa: E402
from deepreason.ontology import Commitment, Problem, ProblemProvenance  # noqa: E402
from deepreason.report import eval_report  # noqa: E402
from deepreason.scheduler.scheduler import Scheduler  # noqa: E402
from deepreason.views.theory import theory  # noqa: E402

# Per-role completion caps. Calibrated from live-run data: 1600 truncated
# VS_K skeleton candidates mid-JSON (every completion hit the cap exactly),
# so skeleton-bearing roles get real headroom; the adapter also detects
# finish_reason=length and asks for compression instead of blind retries.
MAX_TOKENS = {
    "conjecturer": 4000,
    "argumentative_critic": 1400,  # 900 starved long cases (33% valid-JSON observed)
    "defender": 900,
    "variator": 3000,  # 2000 truncated paraphrases of large skeleton exchanges
    "synthesizer": 1400,  # 900 truncated a relation proposal
    "judge": 1200,  # v4-pro rulings run long even in JSON mode
}

# Per-role reasoning policy (docs/TOKEN_ECONOMY.md angle 1): reasoning off
# for prose/skeleton generation and aux roles — quality is carried by
# criticism (D2), and the eval report certifies the change. The judge keeps
# the provider default pending audit data. Overridable via --reasoning.
REASONING = {
    "conjecturer": "none",
    "argumentative_critic": "none",
    "defender": "none",
    "variator": "none",
    "synthesizer": "none",
    "judge": None,
}


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
    for want in ("reason", "r1"):
        hits = [m for m in others if want in m.lower()]
        if hits:
            return sorted(hits)[0]
    return sorted(others)[0] if others else primary


def seed_tides(harness: Harness) -> None:
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


def seed_republic(harness: Harness) -> None:
    """Informal-domain suite (§10): skeletons + a standard + a rubric trial."""
    register_standard(
        harness,
        "std-hist",
        rubric=(
            "A historical-mechanism account must: (1) name a specific causal "
            "mechanism — an institution, incentive, or process — not a mood, "
            "essence, or inevitability; (2) state forbidden cases that are "
            "concrete observations which could realistically have obtained "
            "(a record, an event, a datable pattern); (3) claims of the form "
            "'decline was inevitable' or 'moral decay' with no mechanism "
            "violate this standard."
        ),
        mode="absolute",
    )
    harness.register_commitment(skeleton_wf_commitment())
    harness.register_commitment(Commitment(id="kappa-hist", eval="rubric:std-hist"))
    harness.register_problem(
        Problem(
            id="pi-republic",
            description=(
                "Why did the Roman Republic, after four centuries of durable "
                "aristocratic power-sharing, collapse into one-man rule within a "
                "single lifetime (133-27 BC)? Each candidate's content MUST be a "
                "JSON skeleton object, exactly this shape: "
                '{"claim": str, "mechanism": str, '
                '"scope": {"covers": [str], "excludes": [str]}, '
                '"forbidden": [{"case": str, "eval": "rubric:std-hist"}], '
                '"prose_notes": str}. '
                "The forbidden cases must be historical observations that would "
                "have refuted the account had they obtained."
            ),
            criteria=["skeleton-wf", "kappa-hist"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


SUITES = {"tides": ("pi-tides", seed_tides), "republic": ("pi-republic", seed_republic)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="runs/live")
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--suite", choices=sorted(SUITES), default="tides")
    parser.add_argument("--token-budget", type=int, default=400_000)
    parser.add_argument("--model", default=None, help="preferred model id (e.g. a V4 pro variant)")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config" / "deepseek.yaml"))
    parser.add_argument("--dry-run", action="store_true", help="resolve models and exit")
    parser.add_argument("--reasoning", default="policy",
                        help="conjecturer reasoning override: policy|default|none|high|max|<int>")
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
    print(f"suite: {args.suite}   token budget: {args.token_budget}")
    if args.dry_run:
        return 0

    config = load_config(Path(args.config))
    meter = TokenMeter(budget=args.token_budget)

    def endpoint(role: str, model: str, temperature: float) -> OpenAICompatEndpoint:
        reasoning = REASONING.get(role)
        if role == "conjecturer" and args.reasoning != "policy":
            reasoning = None if args.reasoning == "default" else args.reasoning
        return OpenAICompatEndpoint(
            args.base_url, model, api_key=api_key, temperature=temperature,
            max_tokens=MAX_TOKENS.get(role), json_mode=True, request_logprobs=True,
            reasoning=reasoning,
        )

    adapter = LLMAdapter(
        {
            "conjecturer": endpoint("conjecturer", primary, 1.0),
            "argumentative_critic": endpoint("argumentative_critic", primary, 0.7),
            "defender": endpoint("defender", primary, 0.7),
            "variator": endpoint("variator", primary, 1.0),
            "synthesizer": endpoint("synthesizer", primary, 0.9),
            "judge": [endpoint("judge", primary, 0.0), endpoint("judge", alt, 0.0)],
        },
        None,
        retry_max=config.RETRY_MAX,
        meter=meter,
    )

    harness = Harness(Path(args.root))
    adapter.blobs = harness.blobs
    problem_id, seed = SUITES[args.suite]
    seed(harness)

    scheduler = Scheduler(harness, adapter, config)
    result = scheduler.run(args.cycles)

    print("\n=== TOKEN SPEND ===")
    print(json.dumps(meter.snapshot(), indent=2, sort_keys=True))
    print("\n=== P6 EVAL REPORT ===")
    print(json.dumps(eval_report(harness, config), indent=2, sort_keys=True))
    print("\n=== FRONTIER ===")
    for aid in result["frontier"]:
        print(f"\n--- {aid[:12]} ---")
        print(theory(aid, harness.state, harness.blobs, log=harness.log))
    dropped = [d for d in result["diagnostics"] if "dropped" in d]
    if dropped:
        print(f"\nDROPPED CYCLES ({len(dropped)}):")
        for d in dropped:
            print(f"  cycle={d.get('cycle')}: {d['dropped'][:160]}")
    stopped = [d for d in result["diagnostics"] if "stopped" in d]
    if stopped:
        print(f"\nNOTE: run stopped early: {stopped[-1]['stopped']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
