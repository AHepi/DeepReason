"""CP1-M Phase S-mech: dual-mode candidate-checker authoring + offline
execution, against REAL historical claim pairs, through the REAL D2/D3
contract shape (deepreason.oracle.candidate_checker_commitment /
run_from_full_spec, eval="program:candidate_checker").

DEVIATION FROM PREREG.md, recorded here and in RESULTS.md: PREREG.md
originally specified one checker per CLAIM. Redesigned to one COMBINED
checker per PAIR before any live call was spent on the original design,
because a per-claim checker risks being a tautological echo of its own
claim (the model just hardcodes what its assigned claim says) rather
than an independent mechanical computation. The pair-level design asks
the encoder to compute the underlying quantity from scratch and state
what each claim asserts about it -- the checker is scored against BOTH
values, so it cannot win by construction.

Concurrency: <=3 concurrent calls per operator key (env discipline,
PREREG.md). Model/key assignment is round-robin over the pre-registered
processing order (Rule-184-family hits first, then the rest of the
S-mech population in patrol_hits.jsonl order) so no model/key
systematically gets an easier or harder slice.

Resumable in chunks (--max-calls=N), same pattern as the patrol pilot's
phase2_patrol.py: skips pairs already recorded in the output file.
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
from deepreason.oracle import candidate_checker_commitment, run_from_full_spec  # noqa: E402

BASE_URL = "https://ollama.com/v1"
MODELS = ["glm-5.2", "gemma4:31b"]
KEY_ENV_VARS = ["OLLAMA_API_KEY_AARON", "OLLAMA_API_KEY_DARRELL"]
MAX_TOKENS = 1500
TIMEOUT_S = 90

PROMPT_TEMPLATE = """You are given two claims (A and B) from a solved reasoning problem \
that were flagged as possibly contradicting each other. Write a short, \
self-contained Python function `check()` that takes NO arguments and \
MECHANICALLY COMPUTES the true answer to the underlying question these \
claims are about, by direct calculation or simulation -- never by \
picking between A and B. Then state what value each claim asserts for \
that SAME quantity, in a form directly comparable to what check() \
returns (same type: a number, a string, or true/false).

Claim A: {claim_a}

Claim B: {claim_b}

`check()` MUST return a single SCALAR value only -- a number, a short \
string, or true/false -- never a list, dict, or nested structure. If the \
underlying question has several parts, compute a single true/false: \
does the FULL claim (all its parts together) hold?

Respond with STRICT JSON only -- double-quoted keys, lowercase \
true/false/null, no comments, no markdown code fences, nothing before \
or after the object:
{{"source": "def check():\\n    ...\\n    return <scalar value>",
  "entry": "check",
  "claim_a_value": <scalar value claim A asserts, comparable to check()'s return>,
  "claim_b_value": <scalar value claim B asserts, comparable to check()'s return>}}

Pure Python standard library only (math/itertools/functools allowed, no \
imports needing network or filesystem). Keep `check` under 40 lines."""

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_PY_BOOL_NULL_RE = re.compile(r"\bTrue\b|\bFalse\b|\bNone\b")
_BARE_KEY_RE = re.compile(r"([{,]\s*)(-?\d+(?:\.\d+)?)(\s*:)")


def _repair_json_ish(text: str) -> str:
    text = _FENCE_RE.sub("", text).strip()
    text = _PY_BOOL_NULL_RE.sub(
        lambda m: {"True": "true", "False": "false", "None": "null"}[m.group(0)], text
    )
    text = _BARE_KEY_RE.sub(lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}', text)
    return text

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


def load_population():
    rows = [
        json.loads(l)
        for l in (TRANCHE / "hits_with_claims.jsonl").read_text().splitlines()
    ]
    eligible = [r for r in rows if mech_eligible(r["_claim_a"], r["_claim_b"])]

    def sort_key(r):
        is_184 = bool(re.search(r"rule\s*184", r.get("reason", ""), re.I))
        return (0 if is_184 else 1, r["root"], r["artifact_a"], r["artifact_b"])

    eligible.sort(key=sort_key)
    return eligible


def pair_key(row) -> str:
    return f"{row['root']}\x00{row['artifact_a']}\x00{row['artifact_b']}"


# Deterministic 10% stability-repeat sample (content-seeded, not wall-clock).
def is_stability_sample(key: str) -> bool:
    h = hashlib.sha256(("cp1m-s-mech-stability-v1\x00" + key).encode()).digest()
    return int.from_bytes(h[:2], "big") % 10 == 0


_endpoints: dict[tuple[str, str], OpenAICompatEndpoint] = {}
_endpoints_lock = threading.Lock()
_key_semaphores = {name: threading.Semaphore(3) for name in KEY_ENV_VARS}


def get_endpoint(model: str, key_env: str) -> OpenAICompatEndpoint:
    cache_key = (model, key_env)
    with _endpoints_lock:
        if cache_key not in _endpoints:
            _endpoints[cache_key] = OpenAICompatEndpoint(
                base_url=BASE_URL,
                model=model,
                api_key=os.environ[key_env],
                temperature=0.0,
                max_tokens=MAX_TOKENS,
                timeout_s=TIMEOUT_S,
                json_mode=True,
                reasoning="none",
            )
        return _endpoints[cache_key]


_SCALAR_TYPES = (str, int, float, bool)


def parse_authoring(raw: str):
    """Two-tier parse: strict JSON first; if that fails, a purely
    SYNTACTIC repair (strip markdown fences, Python True/False/None ->
    JSON, quote bare-numeric dict keys) and retry. The repair never
    touches semantic content (the source code or the asserted values),
    only JSON-vs-Python-literal syntax differences some hosted models
    emit despite json_mode=True. Returns (parsed_or_None, "strict"|"repaired"|None)."""
    for tier, text in (("strict", raw), ("repaired", _repair_json_ish(raw))):
        try:
            obj = json.loads(text)
            source = str(obj["source"])
            entry = str(obj["entry"])
            claim_a_value = obj["claim_a_value"]
            claim_b_value = obj["claim_b_value"]
            if not source.strip() or not entry.strip():
                continue
            if not isinstance(claim_a_value, _SCALAR_TYPES) or not isinstance(claim_b_value, _SCALAR_TYPES):
                continue
            return {
                "source": source,
                "entry": entry,
                "claim_a_value": claim_a_value,
                "claim_b_value": claim_b_value,
            }, tier
        except Exception:  # noqa: BLE001
            continue
    return None, None


def score_checker(authored: dict):
    """Run the SAME authored source against claim_a_value then
    claim_b_value, through the real dispatch path (candidate_checker_commitment
    + run_from_full_spec). Returns (outcome, detail_a, detail_b, verdict_a, verdict_b)."""
    try:
        c_a = candidate_checker_commitment(
            authored["source"], authored["entry"], [{"in": [], "out": authored["claim_a_value"]}]
        )
        verdict_a, detail_a = run_from_full_spec(c_a.budget)
    except Exception as exc:  # noqa: BLE001
        return "score_error", {"error": f"{type(exc).__name__}: {exc}"}, None, "error", None
    try:
        c_b = candidate_checker_commitment(
            authored["source"], authored["entry"], [{"in": [], "out": authored["claim_b_value"]}]
        )
        verdict_b, detail_b = run_from_full_spec(c_b.budget)
    except Exception as exc:  # noqa: BLE001
        return "score_error", detail_a, {"error": f"{type(exc).__name__}: {exc}"}, verdict_a, "error"

    def is_compile_fail(v, d):
        return v == "fail" and isinstance(d, dict) and str(d.get("error", "")).startswith("candidate:")

    if verdict_a == "overrun" or verdict_b == "overrun":
        outcome = "overrun_malformed_spec"
    elif is_compile_fail(verdict_a, detail_a) or is_compile_fail(verdict_b, detail_b):
        outcome = "compile_fail"
    elif verdict_a == "pass" and verdict_b == "fail":
        outcome = "confirmed_a"
    elif verdict_b == "pass" and verdict_a == "fail":
        outcome = "confirmed_b"
    elif verdict_a == "pass" and verdict_b == "pass":
        outcome = "both_pass"
    else:
        outcome = "both_fail"
    return outcome, detail_a, detail_b, verdict_a, verdict_b


def run_one(row, model: str, key_env: str, repeat: bool):
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

    authored, parse_tier = parse_authoring(raw) if raw is not None else (None, None)
    if authored is None:
        outcome = "authoring_failed" if error is None else "call_error"
        return {
            "outcome": outcome, "raw_response": raw, "error": error, "elapsed_s": elapsed,
            "verdict_a": None, "verdict_b": None, "parse_tier": None,
        }
    outcome, detail_a, detail_b, verdict_a, verdict_b = score_checker(authored)
    return {
        "outcome": outcome, "raw_response": raw, "error": error, "elapsed_s": elapsed,
        "authored": authored, "detail_a": detail_a, "detail_b": detail_b,
        "verdict_a": verdict_a, "verdict_b": verdict_b, "parse_tier": parse_tier,
    }


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

    out_path = TRANCHE / "s_mech_results.jsonl"
    population = load_population()
    print(f"S-mech population: {len(population)} pairs")

    done_keys = already_done_keys(out_path)
    if done_keys:
        print(f"resuming: {len(done_keys)} (pair,variant) already recorded")

    tasks = []
    for i, row in enumerate(population):
        key = pair_key(row)
        model = MODELS[i % 2]
        key_env = KEY_ENV_VARS[i % 2]
        if (key, "primary") not in done_keys:
            tasks.append((row, key, model, key_env, "primary"))
        if is_stability_sample(key) and (key, "repeat") not in done_keys:
            tasks.append((row, key, model, key_env, "repeat"))

    print(f"tasks pending this invocation (before --max-calls): {len(tasks)}")
    if max_calls is not None:
        tasks = tasks[:max_calls]
    print(f"tasks this invocation: {len(tasks)}")

    lock = threading.Lock()
    counts = {}
    done_count = 0
    with out_path.open("a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(run_one, row, model, key_env, variant == "repeat"): (row, pair_key(row), model, key_env, variant)
            for row, pair_key_, model, key_env, variant in tasks
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

    print(f"S-MECH CHUNK COMPLETE: {done_count} calls -> {out_path}")
    print(f"outcome counts this invocation: {counts}")


if __name__ == "__main__":
    main()
