"""Corpus-enrichment pilot, Phase 2: consistency patrol.

Samples ACCEPTED-artifact pairs from every openable root (historical
corpus + this tranche's Phase 1 enriched roots), batched by topical
neighborhood (shared problem address, prereg.yaml's rule), and asks the
provider model ONE bounded, pre-registered narrow question per pair:
do these two accepted claims contradict each other? Raw responses are
preserved verbatim. A hit is a CANDIDATE measurement for future
criticism -- never a verdict, never an edge, never written into any
root (prereg.yaml, task framing, binding).

--dry-run: build the pairing plan and print counts only, no API calls.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import random
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[2]
TRANCHE = pathlib.Path(__file__).resolve().parent
ENRICHED_HOME = TRANCHE / "home"
GROUP_CAP = 20
MODEL = "glm-5.2"
BASE_URL = "https://ollama.com/v1"
CONFIDENCE_THRESHOLD = 0.6

PROMPT_TEMPLATE = """You are given two claims (A and B), both currently accepted as
true within the reasoning record they come from. Judge ONLY
whether A and B, read together, assert something that cannot both
be true -- a genuine contradiction between them. Do not evaluate
whether either claim is correct on its own; judge mutual
consistency only.

Claim A: {claim_a}

Claim B: {claim_b}

Respond with EXACTLY one JSON object and nothing else:
{{"contradiction": true or false, "confidence": a number from 0.0
to 1.0, "reason": "one sentence, at most 200 characters"}}"""


def corpus() -> list[pathlib.Path]:
    return sorted({p.parent for p in (REPO / "experiments").rglob("log.jsonl")})


def corpus_half(root: pathlib.Path) -> str:
    try:
        root.relative_to(ENRICHED_HOME)
        return "enriched"
    except ValueError:
        return "historical"


def build_pairs_for_root(root: pathlib.Path):
    """Return (pairs, unaddressed_count) for one root.

    pairs: list of dicts {problem_id, artifact_a, artifact_b, claim_a, claim_b}
    """
    from deepreason.harness import Harness
    from deepreason.ontology.state import Status
    from deepreason.programs import content_text

    harness = Harness(root, read_only=True)
    accepted = [
        aid for aid, status in harness.state.status.items() if status == Status.ACCEPTED
    ]

    problem_of: dict[str, str] = {}
    for artifact_id, problem_id in sorted(harness.state.addr):
        problem_of.setdefault(artifact_id, problem_id)

    groups: dict[str, list[str]] = {}
    unaddressed = 0
    for aid in accepted:
        key = problem_of.get(aid)
        if key is None:
            unaddressed += 1
            continue
        groups.setdefault(key, []).append(aid)

    pairs = []
    root_id = str(root)
    for problem_id, members in sorted(groups.items()):
        members = sorted(members)
        if len(members) < 2:
            continue
        if len(members) > GROUP_CAP:
            seed = int(
                hashlib.sha256(f"{root_id}\x00{problem_id}".encode()).hexdigest(), 16
            )
            members = sorted(random.Random(seed).sample(members, GROUP_CAP))
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                pairs.append(
                    {
                        "problem_id": problem_id,
                        "artifact_a": a,
                        "artifact_b": b,
                        "claim_a": content_text(harness.state.artifacts[a], harness.blobs),
                        "claim_b": content_text(harness.state.artifacts[b], harness.blobs),
                    }
                )
    return pairs, unaddressed


def make_endpoint():
    from deepreason.llm.endpoints import OpenAICompatEndpoint

    api_key = os.environ.get("OLLAMA_API_KEY")
    return OpenAICompatEndpoint(
        base_url=BASE_URL,
        model=MODEL,
        api_key=api_key,
        temperature=0.0,
        max_tokens=300,
        timeout_s=60,
        json_mode=True,
        reasoning="none",
    )


def parse_response(raw: str):
    try:
        obj = json.loads(raw)
        contradiction = obj["contradiction"]
        confidence = float(obj["confidence"])
        reason = str(obj["reason"])[:200]
        if not isinstance(contradiction, bool):
            raise ValueError("contradiction not bool")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("confidence out of range")
        return {"contradiction": contradiction, "confidence": confidence, "reason": reason}
    except Exception as error:  # noqa: BLE001 - parse failure is a typed outcome, not fatal
        return None


def already_done_keys(out_path: pathlib.Path) -> set:
    """(root, artifact_a, artifact_b) keys already recorded -- lets this
    script run in bounded chunks across several invocations (the corpus
    is large enough, at 9000+ pairs, that one continuous call risks the
    same container instability Phase 1 hit) without re-spending a call
    on a pair already answered."""
    keys = set()
    if not out_path.exists():
        return keys
    for line in out_path.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        keys.add((row["root"], row["artifact_a"], row["artifact_b"]))
    return keys


def main():
    dry_run = "--dry-run" in sys.argv
    max_calls = None
    for arg in sys.argv[1:]:
        if arg.startswith("--max-calls="):
            max_calls = int(arg.split("=", 1)[1])
    out_path = TRANCHE / "patrol_results.jsonl"

    roots = corpus()
    total_pairs = 0
    total_unaddressed = 0
    by_half_pairs = {"historical": 0, "enriched": 0}
    root_plans = []
    unopenable = []

    for root in roots:
        try:
            pairs, unaddressed = build_pairs_for_root(root)
        except Exception as error:  # noqa: BLE001 - a per-root open failure must not kill the sweep
            unopenable.append({"root": str(root), "error": f"{type(error).__name__}: {error}"})
            continue
        total_unaddressed += unaddressed
        if pairs:
            half = corpus_half(root)
            by_half_pairs[half] += len(pairs)
            total_pairs += len(pairs)
            root_plans.append((root, half, pairs))

    print(
        f"corpus roots={len(roots)} openable={len(roots) - len(unopenable)} "
        f"unopenable={len(unopenable)} pairs={total_pairs} "
        f"historical={by_half_pairs['historical']} enriched={by_half_pairs['enriched']} "
        f"unaddressed_accepted_excluded={total_unaddressed}"
    )
    if unopenable:
        unopenable_path = TRANCHE / "phase2_unopenable_roots.json"
        unopenable_path.write_text(json.dumps(unopenable, indent=2, sort_keys=True) + "\n")
        print(f"unopenable root list -> {unopenable_path}")

    if dry_run:
        return

    done_keys = already_done_keys(out_path)
    if done_keys:
        print(f"resuming: {len(done_keys)} pairs already recorded, skipping them")

    endpoint = make_endpoint()
    hits = 0
    parse_failures = 0
    done = 0
    calls_this_invocation = 0
    with out_path.open("a", encoding="utf-8") as out:
        for root, half, pairs in root_plans:
            for pair in pairs:
                key = (str(root), pair["artifact_a"], pair["artifact_b"])
                if key in done_keys:
                    continue
                if max_calls is not None and calls_this_invocation >= max_calls:
                    print(
                        f"max-calls={max_calls} reached this invocation; "
                        f"{calls_this_invocation} calls made, re-run to continue"
                    )
                    print(
                        f"PATROL CHUNK COMPLETE: pairs_this_run={calls_this_invocation} "
                        f"-> {out_path}"
                    )
                    return
                calls_this_invocation += 1
                prompt = PROMPT_TEMPLATE.format(
                    claim_a=pair["claim_a"], claim_b=pair["claim_b"]
                )
                t0 = time.monotonic()
                try:
                    raw = endpoint.complete(prompt)
                    error = None
                except Exception as exc:  # noqa: BLE001 - one bounded call, record and move on
                    raw = None
                    error = f"{type(exc).__name__}: {exc}"
                elapsed = round(time.monotonic() - t0, 3)

                parsed = parse_response(raw) if raw is not None else None
                is_hit = bool(
                    parsed
                    and parsed["contradiction"]
                    and parsed["confidence"] >= CONFIDENCE_THRESHOLD
                )
                if parsed is None and error is None:
                    parse_failures += 1
                if is_hit:
                    hits += 1

                row = {
                    "root": str(root),
                    "corpus_half": half,
                    "problem_id": pair["problem_id"],
                    "artifact_a": pair["artifact_a"],
                    "artifact_b": pair["artifact_b"],
                    "raw_response": raw,
                    "parsed": parsed,
                    "error": error,
                    "is_hit": is_hit,
                    "elapsed_s": elapsed,
                }
                out.write(json.dumps(row, sort_keys=True) + "\n")
                out.flush()
                done += 1
                if done % 25 == 0:
                    print(f"[{done}/{total_pairs}] hits={hits} parse_failures={parse_failures}")

    print(
        f"PATROL COMPLETE: pairs={done} hits={hits} parse_failures={parse_failures} "
        f"-> {out_path}"
    )


if __name__ == "__main__":
    main()
