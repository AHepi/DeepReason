"""Phase 4 step 1: sample 80 hits + 40 clean non-hits from the
sibling branch's FINAL patrol_results.jsonl (must already be fetched
locally as patrol_results_final.jsonl -- see fetch_patrol_results.sh).
Excludes fence-wrapped parse failures from the non-hit frame
(PREREG-P4.yaml's documented, inherited-defect handling).

Usage: python3 phase4_sample.py PATROL_RESULTS_JSONL OUT_JSON
"""

import json
import random
import re
import sys
from pathlib import Path

SEED = 20260809
HIT_N = 80
NON_HIT_N = 40

FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def is_fence_wrapped_parse_failure(row: dict) -> bool:
    if row.get("parsed") is not None:
        return False
    raw = row.get("raw_response")
    if not raw:
        return False
    m = FENCE_RE.match(raw)
    if not m:
        return False
    try:
        obj = json.loads(m.group(1))
    except Exception:  # noqa: BLE001
        return False
    return "contradiction" in obj


def main() -> None:
    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    hits = []
    clean_non_hits = []
    excluded_fence_failures = 0
    total = 0
    for line in in_path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        total += 1
        if row.get("is_hit"):
            hits.append(row)
        else:
            if is_fence_wrapped_parse_failure(row):
                excluded_fence_failures += 1
                continue
            clean_non_hits.append(row)

    rng = random.Random(SEED)
    hit_sample = rng.sample(hits, min(HIT_N, len(hits)))
    rng2 = random.Random(SEED)  # fresh, deterministic, independent of hit draw order
    non_hit_sample = rng2.sample(clean_non_hits, min(NON_HIT_N, len(clean_non_hits)))

    out = {
        "seed": SEED,
        "total_records": total,
        "total_hits": len(hits),
        "total_clean_non_hits": len(clean_non_hits),
        "excluded_fence_parse_failures": excluded_fence_failures,
        "hit_sample_n": len(hit_sample),
        "non_hit_sample_n": len(non_hit_sample),
        "hit_sample": hit_sample,
        "non_hit_sample": non_hit_sample,
    }
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(
        f"total={total} hits={len(hits)} clean_non_hits={len(clean_non_hits)} "
        f"excluded_fence_failures={excluded_fence_failures} "
        f"sampled hits={len(hit_sample)} non_hits={len(non_hit_sample)} -> {out_path}"
    )


if __name__ == "__main__":
    main()
