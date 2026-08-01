"""Freeze the bronze court-cross v1 candidate pool (zero LLM tokens).

Per experiments/bronze_court_cross_v1_prereg.yaml: registered AND
gate-blocked emitted proposals from the bronze flat v1 census, deduplicated
by content sha256, stripped of stream/model provenance (blinding), then
deterministically subsampled to fit the judging budget (600k tokens over
three court arms at the defended-trial per-item cost observed in
defended_trial_v1, about 1.7k tokens per item, gives about 110 items).

The subsample is a pure function of the content hashes (sorted, then
sampled with a fixed seed), so rerunning reproduces the identical pool.
Output: experiments/court_cross_pool_v1.json
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bronze_census import stream_candidate_contents  # noqa: E402

CENSUS = Path("experiments/results/bronze_flat_v1_census.json")
OUT = Path("experiments/court_cross_pool_v1.json")
POOL_SIZE = 110
SEED = 42


def main() -> None:
    census = json.loads(CENSUS.read_text())
    eligible: dict[str, str] = {}
    for stream_name, stream in census["streams"].items():
        contents = stream_candidate_contents(stream_name)
        for row in stream["rows"]:
            if row["disposition"] not in ("registered", "gate-blocked"):
                continue
            sha = row.get("content_sha256")
            if not sha or sha in eligible:
                continue
            content = contents.get(sha)
            if content:
                eligible[sha] = content

    ordered = sorted(eligible)
    rng = random.Random(SEED)
    chosen = sorted(rng.sample(ordered, min(POOL_SIZE, len(ordered))))
    pool = {
        "schema": "deepreason-court-cross-pool-v1",
        "prereg": "experiments/bronze_court_cross_v1_prereg.yaml",
        "source_census": str(CENSUS),
        "eligible_unique_candidates": len(eligible),
        "pool_size": len(chosen),
        "sample_seed": SEED,
        "blinding": "stream/model provenance stripped; items keyed by sha only",
        "items": [{"sha256": sha, "content": eligible[sha]} for sha in chosen],
    }
    OUT.write_text(json.dumps(pool, indent=1, sort_keys=True))
    print(f"pool frozen: {len(chosen)} of {len(eligible)} eligible unique candidates")


if __name__ == "__main__":
    main()
