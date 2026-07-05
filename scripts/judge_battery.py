#!/usr/bin/env python
"""T1a/T1b judge battery: planted-flaw calibration + verbosity bias probes.

Ground truth by construction (spec §10.4): 12 arguments with planted flaws
(circularity, equivocation, affirming-the-consequent, false premise, ...)
plus 12 valid controls. Each judge configuration rules on all 24; the error
rate is a PROGRAM check on the informal judge — the number every rubric
verdict depends on. Configurations cross model {v4-pro, v4-flash} with
reasoning {provider default, off}: the config keeps judge reasoning ON
"pending audit data" — this battery IS that audit (judge spend was 50% of
the criticism run, 22% of its calls truncated by reasoning length).

Usage: DEEPSEEK_API_KEY=... python scripts/judge_battery.py [--budget 160000]
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.config import Config  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.informal.audits import bias_probes, planted_flaw_calibration  # noqa: E402
from deepreason.llm.adapter import LLMAdapter  # noqa: E402
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter  # noqa: E402
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402

RUBRIC = (
    "An argument violates this standard iff its stated reasoning contains a "
    "definite logical or factual error that undermines its conclusion: "
    "circular justification, equivocation on a term, a formally invalid "
    "inference (e.g. affirming the consequent, denying the antecedent), a "
    "false arithmetic or factual premise, an unsupported causal leap, or a "
    "probability error. A valid argument with true premises does NOT violate "
    "the standard, even if its topic is mundane."
)

FLAWED = [
    "The Bible is true because it is the word of God, and we know it is the "
    "word of God because the Bible itself says so.",
    "A feather is light. Whatever is light cannot be dark. Therefore a "
    "feather cannot be dark.",
    "If it rains, the street gets wet. The street is wet. Therefore it rained.",
    "If a creature is a fish, it can swim. A dolphin is not a fish. "
    "Therefore a dolphin cannot swim.",
    "Since 7 times 8 equals 54, and 54 is even, the product of 7 and 8 is even.",
    "A disease affects 1 in 10,000 people. The test for it is 99% accurate. "
    "Maria tested positive, so it is 99% certain she has the disease.",
    "Every member of the committee is efficient. Therefore the committee as "
    "a whole must be efficient.",
    "The rooster crows immediately before sunrise. Therefore the rooster's "
    "crowing causes the sun to rise.",
    "Both times I visited that city it rained. So it must rain there most days.",
    "Opium induces sleep because it possesses a dormitive virtue — that is, "
    "a power whose nature is to induce sleep.",
    "The recipe needs 3 eggs per cake and we have 10 eggs, so we can bake 4 "
    "whole cakes.",
    "Linda is outspoken and majored in philosophy. It is therefore more "
    "probable that Linda is a bank teller who is active in the feminist "
    "movement than that she is a bank teller.",
]

CLEAN = [
    "All squares are rectangles. All rectangles are quadrilaterals. "
    "Therefore all squares are quadrilaterals.",
    "If the fuse were intact, the lamp would light. The lamp does not "
    "light. Therefore the fuse is not intact.",
    "7 times 8 equals 56, and 56 is even, so the product of 7 and 8 is even.",
    "The key is either in the drawer or in the coat. It is not in the "
    "drawer. Therefore it is in the coat.",
    "The recipe needs 3 eggs per cake and we have 10 eggs, so we can bake "
    "at most 3 whole cakes.",
    "All birds in this aviary are finches. This bird is not a finch, so it "
    "is not from this aviary.",
    "Machine A alone finishes the job in 6 hours, so in 2 hours it "
    "completes one third of the job.",
    "Any number divisible by 4 is divisible by 2, because 4 is 2 times 2 "
    "and divisibility is transitive over factors.",
    "If the tank is empty, the engine stops. The tank is empty. Therefore "
    "the engine stops.",
    "A fair coin is flipped twice. The chance of two heads is 1/4, because "
    "the flips are independent and each head has chance 1/2.",
    "The angles of a triangle sum to 180 degrees. Two of them are 90 and "
    "60, so the third is 30 degrees.",
    "The sample was randomly drawn and large, so its mean is a reasonable "
    "estimate of the population mean within a margin of error.",
]

CALIBRATION = [(t, True) for t in FLAWED] + [(t, False) for t in CLEAN]

# Verbosity probes: same content, terse vs padded (§10.4). The judge is
# asked which is BETTER; systematic preference for the padded twin is bias.
VERBOSITY_PAIRS = [
    ("The tides are driven by the Moon's differential gravity across Earth.",
     "It is important to carefully note, after thorough and detailed "
     "consideration of all the relevant factors involved, that the tides "
     "are, in the final analysis, driven by the Moon's differential "
     "gravity acting across the extent of the Earth."),
    ("Water boils at lower temperatures at altitude because air pressure drops.",
     "As is widely appreciated by experts across many scientific fields, "
     "water does indeed boil at lower temperatures when one is at higher "
     "altitude, and the underlying reason for this is that atmospheric "
     "air pressure drops as elevation increases."),
    ("Vaccines train the immune system using a harmless antigen preview.",
     "Vaccines, which represent one of the most significant achievements "
     "in the entire history of medicine, function by training the human "
     "immune system through what may be described as a harmless preview "
     "of the relevant antigen."),
    ("Compound interest grows savings exponentially over time.",
     "It is genuinely remarkable, and worth emphasizing at some length, "
     "that compound interest causes savings to grow in an exponential "
     "fashion as time goes on and on."),
    ("Evolution proceeds by variation and selective retention.",
     "Evolution, as countless studies have exhaustively demonstrated over "
     "the many decades since Darwin, proceeds by means of variation "
     "followed by the selective retention of advantageous traits."),
    ("Prime numbers thin out, but never stop: Euclid proved there are "
     "infinitely many.",
     "Prime numbers do become progressively rarer as one examines larger "
     "and larger integers, and yet — as the ancient mathematician Euclid "
     "elegantly and definitively proved long ago — they never actually "
     "come to an end: there are infinitely many of them."),
    ("Antibiotic resistance spreads because treatment selects for "
     "resistant strains.",
     "Antibiotic resistance spreads through bacterial populations for a "
     "reason that is, upon careful reflection, quite intuitive: the very "
     "act of treatment applies selective pressure that favors precisely "
     "those strains which happen to be resistant."),
    ("A hotter object radiates more: power scales with the fourth power "
     "of temperature.",
     "A hotter object radiates a great deal more energy than a cooler "
     "one; indeed, as the Stefan-Boltzmann law informs us in no uncertain "
     "terms, the radiated power scales with the fourth power of the "
     "absolute temperature."),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=int, default=160_000)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--root", default="runs/judge_battery")
    parser.add_argument("--only", default="",
                        help="substring filter on config names (e.g. 'laguna')")
    parser.add_argument("--tag", default="",
                        help="suffix for the report filename")
    args = parser.parse_args()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1

    harness = Harness(Path(args.root))
    config = Config(JUDGE_ERR_MAX=0.25)
    meter = TokenMeter(budget=args.budget)
    report: dict = {"experiment": "judge-battery (planted-flaw + verbosity bias)",
                    "n_calibration": len(CALIBRATION), "configs": {}}

    configs = [
        ("v4-pro/reasoning-default", args.base_url, api_key, "deepseek-v4-pro", None),
        ("v4-pro/reasoning-off", args.base_url, api_key, "deepseek-v4-pro", "none"),
        ("v4-flash/reasoning-default", args.base_url, api_key, "deepseek-v4-flash", None),
        ("v4-flash/reasoning-off", args.base_url, api_key, "deepseek-v4-flash", "none"),
    ]
    poolside_key = os.environ.get("POOLSIDE_API_KEY")
    if poolside_key:
        # Cross-family seat (§9): calibrate before it judges anything.
        configs.append(("laguna-m.1/default", "https://inference.poolside.ai/v1",
                        poolside_key, "poolside/laguna-m.1", None))
    if args.only:
        configs = [c for c in configs if args.only in c[0]]
    try:
        for name, base_url, key, model, reasoning in configs:
            endpoint = OpenAICompatEndpoint(
                base_url, model, api_key=key, temperature=0.0,
                max_tokens=2400, json_mode=True, reasoning=reasoning,
            )
            adapter = LLMAdapter({"judge": endpoint}, harness.blobs,
                                 retry_max=2, meter=meter)
            before = meter.total
            rate = planted_flaw_calibration(harness, adapter, config, CALIBRATION, RUBRIC)
            flaw_tokens = meter.total - before
            before = meter.total
            bias = bias_probes(harness, adapter, config,
                               verbosity_pairs=VERBOSITY_PAIRS)
            report["configs"][name] = {
                "planted_flaw_error_rate": round(rate, 4),
                "passes_JUDGE_ERR_MAX_0.25": rate <= 0.25,
                "verbosity_bias_rate": bias["verbosity"],
                "tokens": {"planted_flaw": flaw_tokens,
                           "bias_probes": meter.total - before},
            }
            print(f"{name}: error_rate={rate:.3f} "
                  f"verbosity_bias={bias['verbosity']} "
                  f"spent={meter.total}", flush=True)
    except TokenBudgetExceeded:
        print("budget exhausted — reporting completed configs")
    except EndpointError as e:
        print(f"endpoint error: {e} — reporting completed configs")

    report["tokens"] = meter.snapshot()
    suffix = f"_{args.tag}" if args.tag else ""
    out = Path(f"experiments/results/judge_battery_report{suffix}.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["configs"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
