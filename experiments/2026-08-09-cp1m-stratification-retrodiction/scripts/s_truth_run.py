"""CP1-M Phase S-truth: pairs on questions with a KNOWN ground-truth
answer (root_ground_truth.json, derived from the 10 Phase-1 base/hard/
hard2 roots' own validation_questions*.json `accept` fields -- matched
by seed-problem-text prefix, recorded in RESULTS.md). Eligibility:
in a ground-truth root AND NOT already S-mech-eligible (priority order,
PREREG.md).

Method: one bounded model call per PAIR (not per claim), the ground
truth stated explicitly in the prompt, judging each claim
CONSISTENT/CONTRADICTS. This needs no code authoring/sandbox execution
-- it is a simple classification task made reliable by handing the model
the known-correct answer -- but is still a MODEL JUDGMENT step, so it
carries the same 10%-sampled stability repeat pass as every other
judgment step (PREREG.md).
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = pathlib.Path("/home/user/DeepReason")
TRANCHE = REPO / "experiments/2026-08-09-cp1m-stratification-retrodiction"
sys.path.insert(0, str(REPO / "src"))

from deepreason.llm.endpoints import OpenAICompatEndpoint  # noqa: E402

BASE_URL = "https://ollama.com/v1"
MODELS = ["glm-5.2", "gemma4:31b"]
KEY_ENV_VARS = ["OLLAMA_API_KEY_AARON", "OLLAMA_API_KEY_DARRELL"]
MAX_TOKENS = 400
TIMEOUT_S = 60

RULE_PAT = re.compile(r"\bRule\s*\d+\b", re.IGNORECASE)
NUMERIC_ASSERTION = re.compile(r"\b\d+(\.\d+)?\b")
COUNT_WORDS = re.compile(
    r"\b(pieces?|cuts?|counts?|total|sum|width|length|cycles?|steps?|tour|"
    r"nodes?|edges?|permutation|distance|iterations?|pattern|periodic|"
    r"linear|nonlinear)\b",
    re.IGNORECASE,
)


def mech_eligible(claim_a, claim_b) -> bool:
    for c in (claim_a, claim_b):
        if not c:
            continue
        if RULE_PAT.search(c):
            return True
        if NUMERIC_ASSERTION.search(c) and COUNT_WORDS.search(c):
            return True
    return False


PROMPT_TEMPLATE = """This claim pair comes from a solved reasoning problem whose correct \
answer is KNOWN: {accept}

Claim A: {claim_a}

Claim B: {claim_b}

For EACH claim, judge only whether it is CONSISTENT with the known \
correct answer above, or CONTRADICTS it. A claim that says something \
irrelevant to the final answer (e.g. an intermediate step that does not \
itself assert a final value) is CONSISTENT by default -- only mark \
CONTRADICTS if the claim asserts a specific value/conclusion that \
conflicts with the known answer.

Respond with STRICT JSON only, nothing else:
{{"claim_a_verdict": "consistent" or "contradicts",
  "claim_b_verdict": "consistent" or "contradicts",
  "reason": "one sentence, at most 200 characters"}}"""


def load_population():
    gt = json.loads((TRANCHE / "root_ground_truth.json").read_text())
    rows = [
        json.loads(l) for l in (TRANCHE / "hits_with_claims.jsonl").read_text().splitlines()
    ]
    out = []
    for r in rows:
        matched_key = next((k for k in gt if r["root"].endswith(k)), None)
        if matched_key is None:
            continue
        if mech_eligible(r["_claim_a"], r["_claim_b"]):
            continue
        out.append({**r, "_accept": gt[matched_key]["accept"], "_question_id": gt[matched_key]["question_id"]})
    out.sort(key=lambda r: (r["root"], r["artifact_a"], r["artifact_b"]))
    return out


def pair_key(row) -> str:
    return f"{row['root']}\x00{row['artifact_a']}\x00{row['artifact_b']}"


def is_stability_sample(key: str) -> bool:
    h = hashlib.sha256(("cp1m-s-truth-stability-v1\x00" + key).encode()).digest()
    return int.from_bytes(h[:2], "big") % 10 == 0


_endpoints: dict[tuple[str, str], OpenAICompatEndpoint] = {}
_endpoints_lock = threading.Lock()
_key_semaphores = {name: threading.Semaphore(3) for name in KEY_ENV_VARS}


def get_endpoint(model: str, key_env: str) -> OpenAICompatEndpoint:
    cache_key = (model, key_env)
    with _endpoints_lock:
        if cache_key not in _endpoints:
            _endpoints[cache_key] = OpenAICompatEndpoint(
                base_url=BASE_URL, model=model, api_key=os.environ[key_env],
                temperature=0.0, max_tokens=MAX_TOKENS, timeout_s=TIMEOUT_S,
                json_mode=True, reasoning="none",
            )
        return _endpoints[cache_key]


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_verdict(raw: str):
    for text in (raw, _FENCE_RE.sub("", raw).strip()):
        try:
            obj = json.loads(text)
            a = str(obj["claim_a_verdict"]).lower()
            b = str(obj["claim_b_verdict"]).lower()
            if a not in ("consistent", "contradicts") or b not in ("consistent", "contradicts"):
                continue
            return {"claim_a_verdict": a, "claim_b_verdict": b, "reason": str(obj.get("reason", ""))[:200]}
        except Exception:  # noqa: BLE001
            continue
    return None


def run_one(row, model, key_env):
    prompt = PROMPT_TEMPLATE.format(
        accept=" or ".join(row["_accept"]), claim_a=row["_claim_a"], claim_b=row["_claim_b"]
    )
    endpoint = get_endpoint(model, key_env)
    sem = _key_semaphores[key_env]
    sem.acquire()
    try:
        t0 = time.monotonic()
        try:
            raw = endpoint.complete(prompt)
            error = None
        except Exception as exc:  # noqa: BLE001
            raw, error = None, f"{type(exc).__name__}: {exc}"
        elapsed = round(time.monotonic() - t0, 3)
    finally:
        sem.release()

    parsed = parse_verdict(raw) if raw is not None else None
    if parsed is None:
        outcome = "parse_failed" if error is None else "call_error"
        return {"outcome": outcome, "raw_response": raw, "error": error, "elapsed_s": elapsed}

    a, b = parsed["claim_a_verdict"], parsed["claim_b_verdict"]
    if a == "contradicts" and b == "consistent":
        outcome = "confirmed_b"  # A is wrong, B stands
    elif b == "contradicts" and a == "consistent":
        outcome = "confirmed_a"  # B is wrong, A stands
    elif a == "contradicts" and b == "contradicts":
        outcome = "both_contradict_ground_truth"
    else:
        outcome = "ground_truth_agrees"
    return {"outcome": outcome, "raw_response": raw, "error": error, "elapsed_s": elapsed, "parsed": parsed}


def already_done_keys(out_path: pathlib.Path) -> set:
    keys = set()
    if not out_path.exists():
        return keys
    for line in out_path.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        keys.add((row["pair_key"], row.get("call_variant", "primary")))
    return keys


def main():
    max_calls = None
    for arg in sys.argv[1:]:
        if arg.startswith("--max-calls="):
            max_calls = int(arg.split("=", 1)[1])

    out_path = TRANCHE / "s_truth_results.jsonl"
    population = load_population()
    print(f"S-truth population: {len(population)} pairs")

    done_keys = already_done_keys(out_path)
    if done_keys:
        print(f"resuming: {len(done_keys)} (pair,variant) already recorded")

    tasks = []
    for i, row in enumerate(population):
        key = pair_key(row)
        model = MODELS[i % 2]
        key_env = KEY_ENV_VARS[i % 2]
        if (key, "primary") not in done_keys:
            tasks.append((row, model, key_env, "primary"))
        if is_stability_sample(key) and (key, "repeat") not in done_keys:
            tasks.append((row, model, key_env, "repeat"))

    if max_calls is not None:
        tasks = tasks[:max_calls]
    print(f"tasks this invocation: {len(tasks)}")

    lock = threading.Lock()
    counts = {}
    done_count = 0
    with out_path.open("a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(run_one, row, model, key_env): (row, pair_key(row), model, key_env, variant)
            for row, model, key_env, variant in tasks
        }
        for fut in as_completed(futures):
            row, pkey, model, key_env, variant = futures[fut]
            try:
                result = fut.result()
            except Exception as exc:  # noqa: BLE001
                result = {"outcome": "worker_exception", "error": f"{type(exc).__name__}: {exc}"}
            record = {
                "pair_key": pkey, "call_variant": variant, "model": model, "key_holder": key_env,
                "root": row["root"], "problem_id": row["problem_id"], "question_id": row["_question_id"],
                "accept": row["_accept"],
                "artifact_a": row["artifact_a"], "artifact_b": row["artifact_b"],
                "reason": row.get("reason"), "confidence": row.get("confidence"),
                **result,
            }
            with lock:
                out.write(json.dumps(record, sort_keys=True, default=str) + "\n")
                out.flush()
                done_count += 1
                counts[result.get("outcome", "?")] = counts.get(result.get("outcome", "?"), 0) + 1
                if done_count % 10 == 0:
                    print(f"[{done_count}/{len(tasks)}] {counts}")

    print(f"S-TRUTH CHUNK COMPLETE: {done_count} calls -> {out_path}")
    print(f"outcome counts this invocation: {counts}")


if __name__ == "__main__":
    main()
