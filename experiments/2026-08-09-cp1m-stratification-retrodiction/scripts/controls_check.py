"""CP1-M controls check: run the 150 sampled non-hit controls through the
SAME priority-ordered stratum routing as the 1,941 hits (S-mech if
executable/countable-eligible, else S-truth if in a ground-truth root,
else S-formal-style extraction+mechanical-negation), and report how many
of these ORIGINAL NON-HITS this tranche's stronger methods would flag as
contradictions anyway -- the patrol's own 0.6-confidence threshold's
false-negative rate, the one number in this tranche that speaks to the
threshold choice itself (PREREG.md).

Simplification vs the full 1,941-hit pipeline, recorded here rather than
silently: controls whose extraction comes back `not_clean_shape` are
recorded as `not_flagged` directly, WITHOUT a full S-judgment adversarial
battery (which would be disproportionate machinery for a 150-pair check
whose only job is a single flagged/not-flagged count, not a stratified
master table of its own).
"""
from __future__ import annotations

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
TIMEOUT_S = 90

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


MECH_PROMPT = """You are given two claims (A and B) from a solved reasoning problem. \
Write a short, self-contained Python function `check()` that takes NO \
arguments and MECHANICALLY COMPUTES the true answer to the underlying \
question these claims are about, by direct calculation or simulation. \
Then state what value each claim asserts for that SAME quantity.

Claim A: {claim_a}

Claim B: {claim_b}

`check()` MUST return a single SCALAR value only. Respond with STRICT \
JSON only, no markdown fences:
{{"source": "def check():\\n    ...\\n    return <scalar value>",
  "entry": "check",
  "claim_a_value": <scalar>,
  "claim_b_value": <scalar>}}"""

TRUTH_PROMPT = """This claim pair comes from a solved reasoning problem whose correct \
answer is KNOWN: {accept}

Claim A: {claim_a}

Claim B: {claim_b}

For EACH claim, judge only whether it is CONSISTENT with the known \
correct answer above, or CONTRADICTS it.

Respond with STRICT JSON only:
{{"claim_a_verdict": "consistent" or "contradicts",
  "claim_b_verdict": "consistent" or "contradicts"}}"""

FORMAL_PROMPT = """You are given two claims (A and B). Try to extract a shared (OBJECT, \
PROPERTY) pair they are both talking about, and what VALUE each claim \
asserts for that property. Only do this if both claims clearly share \
the SAME object and SAME property.

Claim A: {claim_a}

Claim B: {claim_b}

Respond with STRICT JSON only:
{{"clean_shape": true or false, "value_a": "short string", "value_b": "short string"}}"""

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
_PY_BOOL_NULL_RE = re.compile(r"\bTrue\b|\bFalse\b|\bNone\b")
_BARE_KEY_RE = re.compile(r"([{,]\s*)(-?\d+(?:\.\d+)?)(\s*:)")


def _repair(text: str) -> str:
    text = _FENCE_RE.sub("", text).strip()
    text = _PY_BOOL_NULL_RE.sub(lambda m: {"True": "true", "False": "false", "None": "null"}[m.group(0)], text)
    text = _BARE_KEY_RE.sub(lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}', text)
    return text


def try_parse(raw):
    for text in (raw, _repair(raw)):
        try:
            return json.loads(text)
        except Exception:  # noqa: BLE001
            continue
    return None


_endpoints = {}
_endpoints_lock = threading.Lock()
_key_semaphores = {name: threading.Semaphore(3) for name in KEY_ENV_VARS}


def get_endpoint(model, key_env, max_tokens):
    cache_key = (model, key_env, max_tokens)
    with _endpoints_lock:
        if cache_key not in _endpoints:
            _endpoints[cache_key] = OpenAICompatEndpoint(
                base_url=BASE_URL, model=model, api_key=os.environ[key_env],
                temperature=0.0, max_tokens=max_tokens, timeout_s=TIMEOUT_S,
                json_mode=True, reasoning="none",
            )
        return _endpoints[cache_key]


def call(prompt, model, key_env, max_tokens):
    endpoint = get_endpoint(model, key_env, max_tokens)
    sem = _key_semaphores[key_env]
    sem.acquire()
    try:
        return endpoint.complete(prompt)
    finally:
        sem.release()


def route_and_check(row, model, key_env):
    a, b = row["_claim_a"], row["_claim_b"]
    gt = json.loads((TRANCHE / "root_ground_truth.json").read_text())
    matched_key = next((k for k in gt if row["root"].endswith(k)), None)

    if mech_eligible(a, b):
        raw = call(MECH_PROMPT.format(claim_a=a, claim_b=b), model, key_env, 1500)
        obj = try_parse(raw)
        if not obj or not obj.get("source") or not obj.get("entry"):
            return "authoring_failed", "s_mech"
        try:
            c_a = candidate_checker_commitment(obj["source"], obj["entry"], [{"in": [], "out": obj.get("claim_a_value")}])
            v_a, _ = run_from_full_spec(c_a.budget)
            c_b = candidate_checker_commitment(obj["source"], obj["entry"], [{"in": [], "out": obj.get("claim_b_value")}])
            v_b, _ = run_from_full_spec(c_b.budget)
        except Exception:  # noqa: BLE001
            return "score_error", "s_mech"
        flagged = (v_a == "pass" and v_b == "fail") or (v_b == "pass" and v_a == "fail")
        return ("flagged" if flagged else "not_flagged"), "s_mech"

    if matched_key is not None:
        accept = " or ".join(gt[matched_key]["accept"])
        raw = call(TRUTH_PROMPT.format(accept=accept, claim_a=a, claim_b=b), model, key_env, 400)
        obj = try_parse(raw)
        if not obj:
            return "parse_failed", "s_truth"
        av, bv = obj.get("claim_a_verdict"), obj.get("claim_b_verdict")
        flagged = (av == "contradicts") != (bv == "contradicts")  # exactly one wrong
        return ("flagged" if flagged else "not_flagged"), "s_truth"

    raw = call(FORMAL_PROMPT.format(claim_a=a, claim_b=b), model, key_env, 400)
    obj = try_parse(raw)
    if not obj:
        return "parse_failed", "s_formal"
    if not obj.get("clean_shape"):
        return "not_flagged", "s_formal"
    va, vb = str(obj.get("value_a", "")).strip().lower(), str(obj.get("value_b", "")).strip().lower()
    return ("flagged" if va and vb and va != vb else "not_flagged"), "s_formal"


def main():
    rows = [json.loads(l) for l in (TRANCHE / "controls_150.jsonl").read_text().splitlines()]
    out_path = TRANCHE / "controls_check_results.jsonl"
    done_keys = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            d = json.loads(line)
            done_keys.add((d["root"], d["artifact_a"], d["artifact_b"]))

    tasks = []
    for i, row in enumerate(rows):
        key = (row["root"], row["artifact_a"], row["artifact_b"])
        if key in done_keys:
            continue
        model = MODELS[i % 2]
        key_env = KEY_ENV_VARS[i % 2]
        tasks.append((row, model, key_env))

    print(f"controls population: {len(rows)}, tasks this invocation: {len(tasks)}")
    lock = threading.Lock()
    counts = {}
    with out_path.open("a") as out, ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(route_and_check, row, model, key_env): (row, model, key_env) for row, model, key_env in tasks}
        done = 0
        for fut in as_completed(futures):
            row, model, key_env = futures[fut]
            try:
                outcome, stratum = fut.result()
            except Exception as exc:  # noqa: BLE001
                outcome, stratum = f"error:{type(exc).__name__}", "unknown"
            record = {
                "root": row["root"], "artifact_a": row["artifact_a"], "artifact_b": row["artifact_b"],
                "problem_id": row["problem_id"], "model": model, "key_holder": key_env,
                "stratum": stratum, "outcome": outcome,
            }
            with lock:
                out.write(json.dumps(record, sort_keys=True) + "\n")
                out.flush()
                done += 1
                counts[outcome] = counts.get(outcome, 0) + 1
                if done % 20 == 0:
                    print(f"[{done}/{len(tasks)}] {counts}")
    print(f"CONTROLS CHECK COMPLETE: {done if tasks else 0} calls, counts this invocation: {counts}")


if __name__ == "__main__":
    main()
