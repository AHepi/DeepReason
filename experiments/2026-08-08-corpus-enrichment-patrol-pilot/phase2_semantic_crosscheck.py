"""Corpus-enrichment pilot — semantic-similarity cross-check (addendum,
requested by the operator after Phase 2 delivery, NOT part of the
original pre-registration).

Phase 2's contradiction judgment came from one non-deterministic LLM
call per pair (see RESULTS.md's 2026-08-09 correction). This script
adds a SECOND, fully deterministic signal over the exact same claim
pairs, using DeepReason's own embedding machinery
(`deepreason.llm.embedder`) -- no LLM call, no randomness, same input
always gives the same output. It does not re-judge contradiction (an
embedder cannot tell you TRUE from FALSE); it measures topical/semantic
RELATEDNESS between claim A and claim B for every pair Phase 2 already
scored. The test this enables: do the pairs the LLM called
"contradictory" show a different similarity signature than the pairs it
didn't -- i.e. is the LLM finding genuine same-topic disagreements, or
linking unrelated claims at random? A contradiction requires the two
claims to be ABOUT the same thing while disagreeing, so hits should sit
at moderate-to-high similarity (related topic, opposed content), not
scattered like random pairs.

Two embedders, both deterministic:
  - HashingEmbedder: zero-dependency, lexical (bag of hashed n-grams).
  - NeuralEmbedder(BAAI/bge-small-en-v1.5): ONNX/fastembed, CPU-only, no
    API calls -- deterministic within this environment (module's own
    documented caveat: not guaranteed bit-identical across different
    CPU/library versions, which is why BOTH are reported, not just one).
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from collections import defaultdict

TRANCHE = pathlib.Path(__file__).resolve().parent
IN_PATH = TRANCHE / "patrol_results.jsonl"
OUT_PATH = TRANCHE / "semantic_crosscheck.jsonl"
NEURAL_MODEL = "BAAI/bge-small-en-v1.5"


def main():
    from deepreason.harness import Harness
    from deepreason.llm.embedder import HashingEmbedder, build_embedder, cosine
    from deepreason.programs import content_text

    hashing = HashingEmbedder()
    try:
        neural = build_embedder(NEURAL_MODEL)
        neural_available = True
    except Exception as exc:  # noqa: BLE001 - neural embedder is optional, hashing always works
        print(f"neural embedder unavailable ({type(exc).__name__}: {exc}); hashing-only run")
        neural = None
        neural_available = False

    rows = [json.loads(l) for l in IN_PATH.read_text().splitlines()]
    print(f"{len(rows)} patrol rows loaded")

    by_root = defaultdict(list)
    for r in rows:
        by_root[r["root"]].append(r)

    done = 0
    t_start = time.monotonic()
    with OUT_PATH.open("w", encoding="utf-8") as out:
        for root, root_rows in sorted(by_root.items()):
            try:
                harness = Harness(pathlib.Path(root), read_only=True)
            except Exception as exc:  # noqa: BLE001 - a per-root open failure must not kill the sweep
                for r in root_rows:
                    out.write(json.dumps({
                        "root": root, "artifact_a": r["artifact_a"], "artifact_b": r["artifact_b"],
                        "is_hit": r["is_hit"], "error": f"{type(exc).__name__}: {exc}",
                    }, sort_keys=True) + "\n")
                    done += 1
                continue

            text_cache: dict[str, str] = {}
            hash_vec_cache: dict[str, list] = {}
            neural_vec_cache: dict[str, list] = {}

            def get_text(aid):
                if aid not in text_cache:
                    text_cache[aid] = content_text(harness.state.artifacts[aid], harness.blobs)
                return text_cache[aid]

            def get_hash_vec(aid):
                if aid not in hash_vec_cache:
                    hash_vec_cache[aid] = hashing.embed(get_text(aid))
                return hash_vec_cache[aid]

            def get_neural_vec(aid):
                if aid not in neural_vec_cache:
                    neural_vec_cache[aid] = neural.embed(get_text(aid))
                return neural_vec_cache[aid]

            for r in root_rows:
                a, b = r["artifact_a"], r["artifact_b"]
                row = {
                    "root": root,
                    "problem_id": r["problem_id"],
                    "artifact_a": a,
                    "artifact_b": b,
                    "is_hit": r["is_hit"],
                    "llm_confidence": (r.get("parsed") or {}).get("confidence"),
                    "hashing_cosine": round(cosine(get_hash_vec(a), get_hash_vec(b)), 6),
                }
                if neural_available:
                    row["neural_cosine"] = round(cosine(get_neural_vec(a), get_neural_vec(b)), 6)
                out.write(json.dumps(row, sort_keys=True) + "\n")
                done += 1
            out.flush()
            if done % 500 < len(root_rows):
                elapsed = round(time.monotonic() - t_start, 1)
                print(f"[{done}/{len(rows)}] roots processed so far, {elapsed}s elapsed")

    print(f"CROSSCHECK COMPLETE: {done} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
