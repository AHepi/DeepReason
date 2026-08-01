"""Measure attractor collapse in glm-5.2, and how far candidate jolts move it.

This driver is HARNESS-SIDE and fixed. The model under study never authors the
code that holds the credential or opens the socket: `sandboxed_python_v1` runs
under `unshare --net` and fails closed without it, and that namespace is the
only reason model-authored Python is safe to execute at all. So the probing is
done here, deterministically and auditably, and the RESULTS are sealed into the
run's input catalog for the model to reason over.

An ATTRACTOR here is operational: over N independent samples at fixed settings,
the fraction of probability mass landing on the single most common answer. A
model with no attractor spreads; a model in one returns "37" every time.

A JOLT is any runtime intervention that does not change the model family and
does not fine-tune: sampling knobs, prompt framing, decoding constraints,
adversarial stances. The question the run has to answer is which of these
actually move the collapse, and whether they buy diversity at the cost of
quality — a jolt that produces novel garbage has not solved anything.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter

ENDPOINT = "https://ollama.com/v1/chat/completions"
MODEL = "glm-5.2"

# Prompts with a known dominant answer, so collapse is measurable rather than
# a matter of taste. Each returns one short token-like answer.
TASKS = {
    "random_number": "Pick a random integer from 1 to 100. Reply with the number only.",
    "fruit": "Name a fruit. Reply with the single word only.",
    "colour": "Name a colour. Reply with the single word only.",
    "animal": "Name an animal. Reply with the single word only.",
    "card": "Name a playing card. Reply with the card only, e.g. 'seven of clubs'.",
    "vegetable": "Name a vegetable. Reply with the single word only.",
}

# Candidate jolts. `system` is prepended as a system message; `extra` is
# appended to the user prompt; sampling knobs go on the request body.
JOLTS = {
    "baseline": {},
    "temperature_high": {"body": {"temperature": 1.3}},
    "temperature_max": {"body": {"temperature": 1.8}},
    "top_p_wide": {"body": {"temperature": 1.0, "top_p": 0.99}},
    "seed_varied": {"vary_seed": True},
    "avoid_obvious": {"extra": " Do not give the most obvious or most common answer."},
    "persona_random": {
        "system": "You are a random selection device. Your outputs must be "
        "uniformly distributed over the space of valid answers."
    },
    # DeepReason's own schools mechanism, transplanted: a foreign critical
    # stance assigned per call. This is the one the dossier asks the model to
    # improve on, so it is measured rather than assumed to work.
    "school_stance": {
        "system": "Adopt critical school {school}. Each school has a distinct "
        "intellectual temperament and would reach for a different answer than "
        "the others. Answer as that school would.",
        "vary_school": True,
    },
    "anti_anchor_fewshot": {
        "system": "Previous answerers already said the three most popular "
        "answers. Yours must differ from all of them."
    },
}

SAMPLES = 12


def call(prompt: str, *, system: str | None, body_extra: dict, key: str,
         retries: int = 3) -> str | None:
    payload = {
        "model": MODEL,
        "messages": ([{"role": "system", "content": system}] if system else [])
        + [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "reasoning_effort": "none",
        **body_extra,
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read())
            return (body["choices"][0]["message"].get("content") or "").strip()
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
            if attempt == retries - 1:
                return None
            time.sleep(2 * (attempt + 1))
    return None


def normalise(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", text)
    return re.sub(r"\s+", " ", text)[:64]


def collapse(answers: list[str]) -> dict:
    """Top-mass and distinct count. Top-mass 1.0 is total collapse."""

    clean = [normalise(a) for a in answers if a]
    if not clean:
        return {"samples": 0, "distinct": 0, "top_mass": None, "mode": None}
    counts = Counter(clean)
    mode, hits = counts.most_common(1)[0]
    return {
        "samples": len(clean),
        "distinct": len(counts),
        "top_mass": round(hits / len(clean), 4),
        "mode": mode,
        "histogram": dict(counts.most_common(8)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--samples", type=int, default=SAMPLES)
    args = parser.parse_args()

    key = os.environ["OLLAMA_API_KEY"]
    results = {"schema": "jolt-probe.v1", "model": MODEL, "samples": args.samples,
               "task_prompts": TASKS, "jolts": {}}

    for jolt_name, spec in JOLTS.items():
        results["jolts"][jolt_name] = {}
        for task_name, prompt in TASKS.items():
            answers = []
            for index in range(args.samples):
                body = dict(spec.get("body", {}))
                if spec.get("vary_seed"):
                    body["seed"] = 1000 + index
                system = spec.get("system")
                if system and spec.get("vary_school"):
                    system = system.format(school=f"school-{index % 5}")
                text = call(
                    prompt + spec.get("extra", ""),
                    system=system,
                    body_extra=body,
                    key=key,
                )
                if text is not None:
                    answers.append(text)
            summary = collapse(answers)
            results["jolts"][jolt_name][task_name] = summary
            print(f"{jolt_name:22} {task_name:16} "
                  f"distinct={summary['distinct']:>3} "
                  f"top_mass={summary['top_mass']} mode={summary['mode']!r}",
                  flush=True)

    with open(args.out, "w") as handle:
        json.dump(results, handle, indent=1, sort_keys=True)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
