"""CP1-M Phase S-judgment: the remainder -- every hit not claimed by
S-mech, S-truth, or S-formal (priority order, PREREG.md). Requires
s_formal_results.jsonl to already exist (to know which pairs S-formal
resolved with confirmed_negation and so does NOT fall through here).

Adversarial battery per pair, 2 models x 3 variants = up to 6 readings:
  baseline    -- the patrol pilot's own narrow contradiction question,
                 verbatim (prereg.yaml's frozen prompt_template), so this
                 stratum's baseline reading is directly comparable to the
                 original patrol call.
  order_swap  -- same question, claims A/B swapped.
  skeptic     -- same question, framed to argue AGAINST a contradiction
                 unless compelled.
Convergence = fraction of available (non-error, non-parse-failure)
readings whose contradiction=true, compared to the original patrol
verdict (always true, since these are all patrol HITS). CONFIRMED iff
>=4 of the readings available (out of up to 6) agree (contradiction=true).

The stability control is the SAME 10%-sampled repeat-pass mechanism
used by every other stratum (PREREG.md), applied to the `baseline`
variant only (repeating an already-adversarial variant a second time
would conflate two different measurements) -- reported as its own
flip-rate metric, not counted toward the 6-reading convergence budget.
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
MAX_TOKENS = 300
TIMEOUT_S = 60
CONFIDENCE_THRESHOLD = 0.6

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


BASELINE_TEMPLATE = """You are given two claims (A and B), both currently accepted as
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

SKEPTIC_TEMPLATE = """You are a skeptical reviewer. You are given two claims (A and B), both
currently accepted as true within the reasoning record they come from.
Your default assumption is that accepted claims from the SAME reasoning
record are usually consistent -- do NOT report a contradiction unless
the evidence is compelling and unavoidable. Judge ONLY whether A and B,
read together, assert something that cannot both be true.

Claim A: {claim_a}

Claim B: {claim_b}

Respond with EXACTLY one JSON object and nothing else:
{{"contradiction": true or false, "confidence": a number from 0.0
to 1.0, "reason": "one sentence, at most 200 characters"}}"""

VARIANTS = {
    "baseline": (BASELINE_TEMPLATE, False),
    "order_swap": (BASELINE_TEMPLATE, True),
    "skeptic": (SKEPTIC_TEMPLATE, False),
}


def load_population():
    rows = [
        json.loads(l) for l in (TRANCHE / "hits_with_claims.jsonl").read_text().splitlines()
    ]
    gt = json.loads((TRANCHE / "root_ground_truth.json").read_text())
    formal_path = TRANCHE / "s_formal_results.jsonl"
    formal_confirmed_keys = set()
    if formal_path.exists():
        for line in formal_path.read_text().splitlines():
            d = json.loads(line)
            if d.get("call_variant", "primary") == "primary" and d.get("outcome") == "confirmed_negation":
                formal_confirmed_keys.add(d["pair_key"])

    out = []
    for r in rows:
        if mech_eligible(r["_claim_a"], r["_claim_b"]):
            continue
        if any(r["root"].endswith(k) for k in gt):
            continue
        key = f"{r['root']}\x00{r['artifact_a']}\x00{r['artifact_b']}"
        if key in formal_confirmed_keys:
            continue
        out.append(r)
    out.sort(key=lambda r: (r["root"], r["artifact_a"], r["artifact_b"]))
    return out


def pair_key(row) -> str:
    return f"{row['root']}\x00{row['artifact_a']}\x00{row['artifact_b']}"


def is_stability_sample(key: str) -> bool:
    h = hashlib.sha256(("cp1m-s-judgment-stability-v1\x00" + key).encode()).digest()
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


def parse_response(raw: str):
    for text in (raw, _FENCE_RE.sub("", raw).strip()):
        try:
            obj = json.loads(text)
            contradiction = obj["contradiction"]
            confidence = float(obj["confidence"])
            if not isinstance(contradiction, bool):
                continue
            if not (0.0 <= confidence <= 1.0):
                continue
            return {"contradiction": contradiction, "confidence": confidence, "reason": str(obj.get("reason", ""))[:200]}
        except Exception:  # noqa: BLE001
            continue
    return None


def run_reading(row, model, key_env, variant):
    template, swap = VARIANTS[variant]
    a, b = (row["_claim_b"], row["_claim_a"]) if swap else (row["_claim_a"], row["_claim_b"])
    prompt = template.format(claim_a=a, claim_b=b)
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

    parsed = parse_response(raw) if raw is not None else None
    if parsed is None:
        outcome = "parse_failed" if error is None else "call_error"
        return {"outcome": outcome, "raw_response": raw, "error": error, "elapsed_s": elapsed}
    agrees = bool(parsed["contradiction"] and parsed["confidence"] >= CONFIDENCE_THRESHOLD)
    return {"outcome": "agrees" if agrees else "disagrees", "raw_response": raw, "error": error,
            "elapsed_s": elapsed, "parsed": parsed}


def already_done_keys(out_path):
    keys = set()
    if not out_path.exists():
        return keys
    for line in out_path.read_text().splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        keys.add((row["pair_key"], row["reading_id"]))
    return keys


def main():
    max_calls = None
    for arg in sys.argv[1:]:
        if arg.startswith("--max-calls="):
            max_calls = int(arg.split("=", 1)[1])

    if not (TRANCHE / "s_formal_results.jsonl").exists():
        print("s_formal_results.jsonl not found yet -- run S-formal first")
        return

    out_path = TRANCHE / "s_judgment_results.jsonl"
    population = load_population()
    print(f"S-judgment population: {len(population)} pairs")

    done_keys = already_done_keys(out_path)
    if done_keys:
        print(f"resuming: {len(done_keys)} (pair,reading_id) already recorded")

    tasks = []
    for i, row in enumerate(population):
        key = pair_key(row)
        for m_idx, model in enumerate(MODELS):
            key_env = KEY_ENV_VARS[(i + m_idx) % 2]
            for variant in ("baseline", "order_swap", "skeptic"):
                reading_id = f"{model}:{variant}"
                if (key, reading_id) not in done_keys:
                    tasks.append((row, model, key_env, variant, reading_id))
            if is_stability_sample(key):
                reading_id = f"{model}:baseline:repeat"
                if (key, reading_id) not in done_keys:
                    tasks.append((row, model, key_env, "baseline", reading_id))

    if max_calls is not None:
        tasks = tasks[:max_calls]
    print(f"tasks this invocation: {len(tasks)}")

    lock = threading.Lock()
    counts = {}
    done_count = 0
    with out_path.open("a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(run_reading, row, model, key_env, variant): (row, pair_key(row), model, key_env, reading_id)
            for row, model, key_env, variant, reading_id in tasks
        }
        for fut in as_completed(futures):
            row, pkey, model, key_env, reading_id = futures[fut]
            try:
                result = fut.result()
            except Exception as exc:  # noqa: BLE001
                result = {"outcome": "worker_exception", "error": f"{type(exc).__name__}: {exc}"}
            record = {
                "pair_key": pkey, "reading_id": reading_id, "model": model, "key_holder": key_env,
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
                if done_count % 20 == 0:
                    print(f"[{done_count}/{len(tasks)}] {counts}")

    print(f"S-JUDGMENT CHUNK COMPLETE: {done_count} calls -> {out_path}")
    print(f"outcome counts this invocation: {counts}")


if __name__ == "__main__":
    main()
