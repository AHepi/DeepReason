"""CP1-M Phase S-formal: structured (object, property, polarity)
extraction + mechanical negation detection, for hits not claimed by
S-mech or S-truth (priority order, PREREG.md).

One model call per pair extracts {object, property, value_a, value_b,
clean_shape}. clean_shape=false (or extraction parse failure) means the
pair does NOT have the clean same-object/same-property shape this
stratum's method needs -- routed to S-judgment, never forced into a
verdict here. Negation detection itself is MECHANICAL (plain string/
value comparison in this script, not a second model call) once the
extraction is in hand.

--validate-only prints the first 50 rows' raw extraction next to the
claim text for the pre-registered 50-hit human-reviewed validation pass,
and writes nothing to the results file.
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


PROMPT_TEMPLATE = """You are given two claims (A and B) flagged as possibly contradicting \
each other. Try to extract a shared (OBJECT, PROPERTY) pair they are \
both talking about, and what VALUE each claim asserts for that \
property. Only do this if both claims clearly share the SAME object and \
SAME property -- if they don't (different subjects, different \
properties, or the shape is too loose to extract cleanly), say so.

Claim A: {claim_a}

Claim B: {claim_b}

Respond with STRICT JSON only, nothing else:
{{"clean_shape": true or false,
  "object": "short noun phrase, or empty string if clean_shape is false",
  "property": "short noun phrase, or empty string if clean_shape is false",
  "value_a": "claim A's asserted value for that property, as a short string",
  "value_b": "claim B's asserted value for that property, as a short string"}}"""


def load_population():
    rows = [
        json.loads(l) for l in (TRANCHE / "hits_with_claims.jsonl").read_text().splitlines()
    ]
    gt = json.loads((TRANCHE / "root_ground_truth.json").read_text())
    out = []
    for r in rows:
        if mech_eligible(r["_claim_a"], r["_claim_b"]):
            continue
        in_truth_root = any(r["root"].endswith(k) for k in gt)
        if in_truth_root:
            continue  # S-truth already claims every non-mech hit in a ground-truth root
        out.append(r)
    out.sort(key=lambda r: (r["root"], r["artifact_a"], r["artifact_b"]))
    return out


def pair_key(row) -> str:
    return f"{row['root']}\x00{row['artifact_a']}\x00{row['artifact_b']}"


def is_stability_sample(key: str) -> bool:
    h = hashlib.sha256(("cp1m-s-formal-stability-v1\x00" + key).encode()).digest()
    return int.from_bytes(h[:2], "big") % 10 == 0


_endpoints: dict[tuple[str, str], OpenAICompatEndpoint] = {}
_endpoints_lock = threading.Lock()
_key_semaphores = {name: threading.Semaphore(3) for name in KEY_ENV_VARS}


def get_endpoint(model, key_env):
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


def parse_extraction(raw: str):
    for text in (raw, _FENCE_RE.sub("", raw).strip()):
        try:
            obj = json.loads(text)
            clean = bool(obj["clean_shape"])
            return {
                "clean_shape": clean,
                "object": str(obj.get("object", "")),
                "property": str(obj.get("property", "")),
                "value_a": str(obj.get("value_a", "")),
                "value_b": str(obj.get("value_b", "")),
            }
        except Exception:  # noqa: BLE001
            continue
    return None


def _canon(v: str) -> str:
    return re.sub(r"\s+", " ", v.strip().lower())


def mechanical_negation(extraction: dict) -> str:
    """Pure comparison, no model call."""
    if not extraction["clean_shape"]:
        return "not_clean_shape"
    a, b = _canon(extraction["value_a"]), _canon(extraction["value_b"])
    if not a or not b:
        return "not_clean_shape"
    if a == b:
        return "values_agree"  # extraction disagrees with original patrol hit
    return "confirmed_negation"  # same object+property, different values


def run_one(row, model, key_env):
    prompt = PROMPT_TEMPLATE.format(claim_a=row["_claim_a"], claim_b=row["_claim_b"])
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

    extraction = parse_extraction(raw) if raw is not None else None
    if extraction is None:
        outcome = "extraction_parse_failed" if error is None else "call_error"
        return {"outcome": outcome, "raw_response": raw, "error": error, "elapsed_s": elapsed}
    outcome = mechanical_negation(extraction)
    return {"outcome": outcome, "raw_response": raw, "error": error, "elapsed_s": elapsed, "extraction": extraction}


def already_done_keys(out_path):
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
    validate_only = "--validate-only" in sys.argv
    for arg in sys.argv[1:]:
        if arg.startswith("--max-calls="):
            max_calls = int(arg.split("=", 1)[1])

    population = load_population()
    print(f"S-formal candidate population (not S-mech, not S-truth): {len(population)} pairs")

    if validate_only:
        sample = population[:50]
        model, key_env = MODELS[0], KEY_ENV_VARS[0]
        for i, row in enumerate(sample):
            result = run_one(row, model, key_env)
            print(f"--- [{i}] root={row['root'].split('/')[-1]} problem={row['problem_id'][:30]}")
            print(f"claim_a: {row['_claim_a'][:200]}")
            print(f"claim_b: {row['_claim_b'][:200]}")
            print(f"extraction: {result.get('extraction')}")
            print(f"outcome: {result['outcome']}")
        return

    out_path = TRANCHE / "s_formal_results.jsonl"
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
                "root": row["root"], "problem_id": row["problem_id"],
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

    print(f"S-FORMAL CHUNK COMPLETE: {done_count} calls -> {out_path}")
    print(f"outcome counts this invocation: {counts}")


if __name__ == "__main__":
    main()
