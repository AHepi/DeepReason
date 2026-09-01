#!/usr/bin/env python
"""Re-verify a model profile document against the provider, or against a
recorded fixture.

A model profile is a human's claim about a model, dated.  Models change and
claims rot, and the whole design rests on a stale document failing a CHECK
rather than a RUN -- so every document names this script in its ``probe:``
field, and this script exits NON-ZERO when a declared claim no longer holds.

What it checks, and nothing else:

* ``trace_destination[v]`` -- for each value the document describes, does the
  reasoning trace actually land where it says?  ``side_channel`` means a
  populated ``reasoning``/``reasoning_content`` field; ``content`` means the
  answer itself opened with prose instead of the requested value; ``absent``
  means neither.
* ``disabling_values`` -- does the model really stop producing a trace for
  those values, and only those?
* ``thinking_disablable`` -- is there ANY value that makes the trace vanish?
* ``extraction_value`` -- does the value the emission leg will actually send
  produce clean content on every trial?  This is the claim that killed three
  runs when it was wrong, so it is checked hardest.

What it does NOT do: change any document, choose a value, or touch the run
record.  It reports and it exits.

Two modes.  ``--offline --fixture`` replays a recorded observation set, which
is how this script is tested and how a claim can be re-checked without
spending provider calls.  Live mode sends ``--trials`` requests per described
value through the ordinary endpoint stack.

Tranche: experiments/2026-09-01-change-model-profile-registry/ (S6).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# A prompt whose correct answer is tiny and unambiguous, so "the content is
# clean" is decidable without a judgement call: anything but a JSON object
# first means the model put something in front of its answer.
PROBE_PROMPT = 'Reply with exactly this JSON and nothing else: {"ok":true}'

SIDE_CHANNEL = "side_channel"
IN_CONTENT = "content"
ABSENT = "absent"


def _document(path: str):
    from deepreason.model_profiles import parse_document

    return parse_document(Path(path).read_text(encoding="utf-8"))


def _resolve(model_id: str):
    from deepreason.model_profiles import resolve

    profile = resolve(model_id)
    if profile is None:
        raise SystemExit(
            f"MODEL_PROFILE_MISSING: no document describes {model_id!r}. "
            "Looked in the one place the harness looks; run with --document to "
            "probe a file that is not installed."
        )
    return profile


def observed_destination(trial: dict) -> str:
    """Where this one trial's reasoning trace actually landed."""

    if trial.get("reasoning_field"):
        return SIDE_CHANNEL
    if not trial.get("content_clean", False):
        return IN_CONTENT
    return ABSENT


def evaluate(profile, observations: dict) -> list[dict]:
    """Compare a document's claims against observed trials.

    Returns one row per claim: ``{claim, value, expected, observed, ok}``.
    Values the document describes but the observation set does not cover are
    reported as ``ok=False`` with ``observed="not probed"`` -- an unprobed
    claim is unverified, and reporting it as a pass is the failure mode this
    whole instrument exists to prevent.
    """

    rows: list[dict] = []
    facts = profile.reasoning
    if facts is None:
        return rows

    described = sorted(set(facts.trace_destination) | set(facts.disabling_values))
    for value in described:
        trials = observations.get(value)
        expected = facts.trace_destination.get(value)
        if not trials:
            if expected is not None:
                rows.append({
                    "claim": "trace_destination",
                    "value": value,
                    "expected": expected,
                    "observed": "not probed",
                    "ok": False,
                })
            continue
        seen = {observed_destination(t) for t in trials}
        if expected is not None:
            rows.append({
                "claim": "trace_destination",
                "value": value,
                "expected": expected,
                "observed": "/".join(sorted(seen)),
                "ok": seen == {expected},
            })
        disables = all(observed_destination(t) == ABSENT for t in trials)
        rows.append({
            "claim": "disabling_values",
            "value": value,
            "expected": value in facts.disabling_values,
            "observed": disables,
            "ok": (value in facts.disabling_values) == disables,
        })

    any_disables = any(
        all(observed_destination(t) == ABSENT for t in trials)
        for trials in observations.values()
        if trials
    )
    rows.append({
        "claim": "thinking_disablable",
        "value": "-",
        "expected": facts.thinking_disablable,
        "observed": any_disables,
        "ok": facts.thinking_disablable == any_disables,
    })

    # The claim that matters most: what the emission leg will actually send.
    if facts.extraction_value is not None:
        trials = observations.get(facts.extraction_value)
        if not trials:
            rows.append({
                "claim": "extraction_value",
                "value": facts.extraction_value,
                "expected": "clean content on every trial",
                "observed": "not probed",
                "ok": False,
            })
        else:
            clean = sum(1 for t in trials if t.get("content_clean"))
            rows.append({
                "claim": "extraction_value",
                "value": facts.extraction_value,
                "expected": f"{len(trials)}/{len(trials)} clean",
                "observed": f"{clean}/{len(trials)} clean",
                "ok": clean == len(trials),
            })
    return rows


def probe_live(profile, trials: int) -> dict:
    """Send the probe prompt for every described value.  One provider call per
    trial per value, and no retries: a failed call is an observation."""

    from deepreason.llm.endpoints import OpenAICompatEndpoint
    from deepreason.provider_profile import resolve_provider_profile

    resolved = resolve_provider_profile(None).profile
    if resolved.model_id != profile.model_id:
        raise SystemExit(
            f"PROBE_MODEL_MISMATCH: the configured provider profile names "
            f"{resolved.model_id!r} but this document describes "
            f"{profile.model_id!r}. Probing a different model would produce "
            "observations that look like evidence and are not."
        )
    endpoint = OpenAICompatEndpoint(
        base_url=resolved.endpoint,
        model=resolved.model_id,
        api_key_env=resolved.credential_env,
        provider=resolved.provider,
    )
    facts = profile.reasoning
    described = sorted(set(facts.trace_destination) | set(facts.disabling_values))
    observations: dict[str, list[dict]] = {}
    for value in described:
        rows = []
        for _ in range(trials):
            text = endpoint.complete(PROBE_PROMPT, max_tokens=256, reasoning=value)
            rows.append({
                "content_clean": str(text).lstrip().startswith("{"),
                "reasoning_field": bool(
                    getattr(endpoint, "last_reasoning_trace", None)
                ),
                "completion_tokens": int(
                    getattr(endpoint, "last_completion_tokens", 0) or 0
                ),
            })
        observations[value] = rows
    return observations


def _self_test() -> int:
    """Prove the instrument can fail.

    A probe that cannot go red is not a probe -- `docs/map/SCHEMA.md`'s rule
    about checks, applied to the thing that checks the checks.
    """

    from deepreason.model_profiles import FENCE_INFO, parse_document

    document = parse_document(
        "```" + FENCE_INFO + """
schema: deepreason-model-profile.v1
model_id: probe-self-test
measured_on: 2026-09-01
reasoning:
  documented_values: [none, low]
  extraction_value: low
  thinking_disablable: false
  disabling_values: []
  trace_destination: {none: content, low: side_channel}
```
"""
    )
    agreeing = {
        "none": [{"content_clean": False, "reasoning_field": False}] * 3,
        "low": [{"content_clean": True, "reasoning_field": True}] * 3,
    }
    rows = evaluate(document, agreeing)
    assert rows and all(r["ok"] for r in rows), [r for r in rows if not r["ok"]]

    # One byte of the observation changed, and the claim it contradicts fails.
    contradicting = {
        "none": [{"content_clean": False, "reasoning_field": False}] * 3,
        "low": [{"content_clean": False, "reasoning_field": True}] * 3,
    }
    rows = evaluate(document, contradicting)
    failed = {r["claim"] for r in rows if not r["ok"]}
    assert "extraction_value" in failed, rows

    # An unprobed claim is a failure, never a silent pass.
    rows = evaluate(document, {"low": agreeing["low"]})
    assert any(r["observed"] == "not probed" and not r["ok"] for r in rows), rows

    # A document claiming disablability that the trials do not show.
    optimistic = parse_document(
        "```" + FENCE_INFO + """
schema: deepreason-model-profile.v1
model_id: probe-self-test-2
measured_on: 2026-09-01
reasoning:
  extraction_value: none
  thinking_disablable: true
  disabling_values: [none]
  trace_destination: {none: absent}
```
"""
    )
    rows = evaluate(optimistic, {"none": [{"content_clean": True, "reasoning_field": True}] * 3})
    failed = {r["claim"] for r in rows if not r["ok"]}
    assert {"trace_destination", "disabling_values", "thinking_disablable"} <= failed, rows

    print("model_profile_probe --self-test: OK (4 cases, agreeing and contradicting)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--document", help="path to an agent.md to verify")
    parser.add_argument("--model", help="model id to resolve from the installed registry")
    parser.add_argument("--trials", type=int, default=8)
    parser.add_argument("--offline", action="store_true", help="replay a fixture, spend nothing")
    parser.add_argument("--fixture", help="recorded observations, JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    from deepreason.model_profiles import profiles_root

    print(f"profiles_root: {profiles_root()}", file=sys.stderr)

    if args.document:
        profile = _document(args.document)
    elif args.model:
        profile = _resolve(args.model)
    else:
        parser.error("one of --document, --model or --self-test is required")

    if profile.reasoning is None:
        print(f"{profile.model_id}: the document declares no reasoning facts; nothing to probe")
        return 0

    if args.offline:
        if not args.fixture:
            parser.error("--offline requires --fixture")
        observations = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        observations = observations.get("trials", observations)
    else:
        observations = probe_live(profile, args.trials)

    rows = evaluate(profile, observations)
    width = max((len(r["claim"]) for r in rows), default=10)
    for row in rows:
        mark = "ok  " if row["ok"] else "FAIL"
        print(
            f"{mark} {row['claim']:<{width}} {row['value']:<6} "
            f"expected={row['expected']} observed={row['observed']}"
        )
    failures = [r for r in rows if not r["ok"]]
    print(
        f"{profile.model_id}: {len(rows) - len(failures)}/{len(rows)} claims hold "
        f"(measured {profile.measured_on.isoformat()})"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
