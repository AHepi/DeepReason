#!/usr/bin/env python3
"""Driver for the diversity-of-generation experiment.  PREREG.md is the
authority for every number here; this file only executes it.

Reads the credential from the process environment ONLY (OLLAMA_API_KEY),
never from an argument and never from a file inside git.  Writes every
provider response to raw/ VERBATIM, before any parsing, so the metrics in
analyse.py are recomputable from the committed raw record alone.

Resumable by construction: a call whose raw file already exists is skipped.
The container can roll back mid-run, and a partially-spent budget must not
be re-spent.
"""
import argparse
import concurrent.futures as futures
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

import requests

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from questions import QUESTIONS  # noqa: E402

BASE_URL = "https://ollama.com/v1"
MODEL = "glm-5.2"
TEMPERATURE = 0.9
TOP_P = 0.95
REASONING_EFFORT = "none"          # llm/providers.py::_ollama_reasoning; thinking OFF
TIMEOUT_S = 300

ARMS = ("A", "B", "C", "D")
REPS = (1, 2, 3)
N_DIRECTIONS = 6
K = 10
PER_DIRECTION_CALLS = 10           # arm B: 6 x 10 = 60 candidates
DIRECT_CALLS = 60                  # arm A
VS_CALLS = 6                       # arm C: 6 x k=10 = 60 candidates
CELL_TOKEN_CAP = 40_000
MAX_TOKENS_SINGLE = 400
MAX_TOKENS_PLAN = 800
MAX_TOKENS_VS = 3000
CONCURRENCY = 8

SYSTEM = (
    "You are proposing scientific conjectures. A conjecture is a bold, specific,\n"
    "falsifiable claim or approach -- not a summary, not a plan, and not a hedge.\n"
    "Write plainly."
)

P_DIRECT = """{q}

Propose ONE conjecture in response.
Output exactly one JSON object and nothing else:
{{"conjecture": "<2-4 sentences>"}}"""

P_PLAN = """{q}

Name 6 genuinely different directions an answer to this could take --
different in mechanism, level of description, measurement, scope, formal
apparatus, or failure mode. Do not answer the question itself.
Output exactly one JSON object and nothing else:
{{"directions": ["<one short phrase>", "<...>", "<...>", "<...>", "<...>", "<...>"]}}"""

P_DIRECT_STRAT = """{q}

Stay within this direction: {d}

Propose ONE conjecture in response, within that direction.
Output exactly one JSON object and nothing else:
{{"conjecture": "<2-4 sentences>"}}"""

P_VS = """{q}

Generate 10 candidate conjectures in response, sampled from the full
distribution of responses you could give to this prompt. For each, give the
conjecture and your estimated probability that it is the response you would
give to this prompt. Every candidate's probability must be below 0.10.
Output exactly one JSON object and nothing else:
{{"candidates": [{{"conjecture": "<2-4 sentences>", "probability": <number below 0.10>}}, ... 10 items]}}"""

P_VS_STRAT = """{q}

Stay within this direction: {d}

Generate 10 candidate conjectures within that direction, sampled from the
full distribution of responses you could give. For each, give the
conjecture and your estimated probability that it is the response you would
give to this prompt. Every candidate's probability must be below 0.10.
Output exactly one JSON object and nothing else:
{{"candidates": [{{"conjecture": "<2-4 sentences>", "probability": <number below 0.10>}}, ... 10 items]}}"""


def log(line):
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    text = f"{stamp} {line}"
    print(text, flush=True)
    with (HERE / "driver.log").open("a") as fh:
        fh.write(text + "\n")


def assert_questions_frozen():
    digests = json.loads((HERE / "question_digests.json").read_text())
    for key, text in sorted(QUESTIONS.items()):
        actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digests.get(key) != actual:
            raise SystemExit(
                f"QUESTION DRIFT on {key!r}: committed {digests.get(key)} != {actual}. "
                "PREREG.md §3 freezes these bytes; refusing to run."
            )
    log(f"question digests verified: {json.dumps(digests, sort_keys=True)}")


def api_key():
    key = os.environ.get("OLLAMA_API_KEY")
    if not key:
        raise SystemExit(
            "OLLAMA_API_KEY is not set. Source the gitignored env file; never "
            "pass the key as an argument and never write it into the repository."
        )
    return key


def build_body(user, max_tokens):
    return {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": max_tokens,
        "reasoning_effort": REASONING_EFFORT,
    }


def call(session, key, user, max_tokens, out_path):
    """One provider call.  ONE retry, on transport error ONLY (PREREG §6):
    a parse failure is never retried and never repaired -- it is the
    measurement.  The verbatim response lands on disk before any caller
    looks at it."""
    if out_path.exists():
        return json.loads(out_path.read_text())
    body = build_body(user, max_tokens)
    record = {"request": body, "attempts": []}
    for attempt in (1, 2):
        t0 = time.time()
        try:
            resp = session.post(
                f"{BASE_URL}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {key}"},
                timeout=TIMEOUT_S,
            )
            elapsed = time.time() - t0
            try:
                payload = resp.json()
            except ValueError:
                payload = {"_non_json_body": resp.text[:20000]}
            record["attempts"].append(
                {"attempt": attempt, "http_status": resp.status_code,
                 "elapsed_s": round(elapsed, 3)}
            )
            if resp.status_code == 200:
                record["response"] = payload
                record["transport_error"] = None
                break
            record["response"] = payload
            record["transport_error"] = f"http_{resp.status_code}"
        except Exception as exc:  # transport: connection, timeout, TLS
            record["attempts"].append(
                {"attempt": attempt, "http_status": None,
                 "elapsed_s": round(time.time() - t0, 3)}
            )
            record["response"] = None
            record["transport_error"] = f"{type(exc).__name__}: {exc}"
        if attempt == 1:
            time.sleep(2.0)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return record


def tokens_of(record):
    usage = ((record.get("response") or {}).get("usage")) or {}
    total = usage.get("total_tokens")
    if isinstance(total, int):
        return total
    return int(usage.get("prompt_tokens") or 0) + int(usage.get("completion_tokens") or 0)


def content_of(record):
    try:
        return record["response"]["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def parse_json_object(text):
    """Tolerant extraction of the one JSON object a prompt asked for: strip a
    markdown fence if present, else take the outermost brace span.  Tolerance
    here is deliberate and one-directional -- it must not let a malformed
    response count as valid, only stop a fence from doing so."""
    if not text:
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("```")[1] if "```" in stripped[3:] else stripped[3:]
        if stripped.lstrip().lower().startswith("json"):
            stripped = stripped.lstrip()[4:]
    start, end = stripped.find("{"), stripped.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(stripped[start:end + 1])
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def directions_from(record):
    obj = parse_json_object(content_of(record))
    if not obj:
        return None
    dirs = obj.get("directions")
    if not isinstance(dirs, list):
        return None
    dirs = [str(d).strip() for d in dirs if str(d).strip()]
    return dirs[:N_DIRECTIONS] if len(dirs) >= N_DIRECTIONS else None


def run_cell(session, key, arm, qkey, rep):
    """One arm x question x repetition cell.  Returns its ledger row."""
    cell_dir = HERE / "raw" / arm / qkey / f"r{rep}"
    question = QUESTIONS[qkey]
    spent = 0
    truncated = False
    planning_failed = False
    directions = None

    if arm in ("B", "D"):
        rec = call(session, key, P_PLAN.format(q=question), MAX_TOKENS_PLAN,
                   cell_dir / "plan.json")
        spent += tokens_of(rec)
        directions = directions_from(rec)
        if directions is None:
            # A cell whose planning call failed is recorded as such and its
            # generation is not run.  Substituting a hand-written direction
            # list would measure the author, not the arm.
            planning_failed = True
            log(f"  {arm}/{qkey}/r{rep}: PLANNING CALL FAILED -- cell not generated")
            return {"arm": arm, "question": qkey, "rep": rep, "tokens": spent,
                    "budget_truncated": False, "planning_failed": True,
                    "directions": None, "calls": 1}

    jobs = []
    if arm == "A":
        for i in range(DIRECT_CALLS):
            jobs.append((cell_dir / f"c{i:03d}.json",
                         P_DIRECT.format(q=question), MAX_TOKENS_SINGLE))
    elif arm == "B":
        for i in range(N_DIRECTIONS * PER_DIRECTION_CALLS):
            d = directions[i // PER_DIRECTION_CALLS]
            jobs.append((cell_dir / f"c{i:03d}.json",
                         P_DIRECT_STRAT.format(q=question, d=d), MAX_TOKENS_SINGLE))
    elif arm == "C":
        for i in range(VS_CALLS):
            jobs.append((cell_dir / f"c{i:03d}.json",
                         P_VS.format(q=question), MAX_TOKENS_VS))
    else:
        for i in range(N_DIRECTIONS):
            jobs.append((cell_dir / f"c{i:03d}.json",
                         P_VS_STRAT.format(q=question, d=directions[i]), MAX_TOKENS_VS))

    made = 1 if arm in ("B", "D") else 0
    with futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        for start in range(0, len(jobs), CONCURRENCY):
            if spent >= CELL_TOKEN_CAP:
                truncated = True
                log(f"  {arm}/{qkey}/r{rep}: budget cap reached at {spent} tokens")
                break
            wave = jobs[start:start + CONCURRENCY]
            for rec in pool.map(
                lambda job: call(session, key, job[1], job[2], job[0]), wave
            ):
                spent += tokens_of(rec)
                made += 1

    if directions is not None:
        (cell_dir / "directions.json").write_text(
            json.dumps(directions, indent=2, ensure_ascii=False) + "\n")
    return {"arm": arm, "question": qkey, "rep": rep, "tokens": spent,
            "budget_truncated": truncated, "planning_failed": planning_failed,
            "directions": directions, "calls": made}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--questions", default=",".join(sorted(QUESTIONS)))
    ap.add_argument("--reps", default=",".join(str(r) for r in REPS))
    args = ap.parse_args()

    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True,
                         text=True).stdout.strip()
    log(f"=== driver start; PREREG frozen at commit {sha} ===")
    log(f"provider: {BASE_URL} model={MODEL} temperature={TEMPERATURE} "
        f"top_p={TOP_P} reasoning_effort={REASONING_EFFORT}")
    assert_questions_frozen()

    key = api_key()
    session = requests.Session()
    ledger = []
    ledger_path = HERE / "cell_ledger.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text())
    done = {(r["arm"], r["question"], r["rep"]) for r in ledger}

    for qkey in args.questions.split(","):
        for rep in [int(r) for r in args.reps.split(",")]:
            for arm in args.arms.split(","):
                if (arm, qkey, rep) in done:
                    log(f"cell {arm}/{qkey}/r{rep}: already in ledger, skipping")
                    continue
                t0 = time.time()
                row = run_cell(session, key, arm, qkey, rep)
                row["wall_s"] = round(time.time() - t0, 1)
                ledger.append(row)
                ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n")
                log(f"cell {arm}/{qkey}/r{rep}: {row['calls']} calls, "
                    f"{row['tokens']} tokens, {row['wall_s']}s"
                    + (" [TRUNCATED]" if row["budget_truncated"] else "")
                    + (" [PLANNING FAILED]" if row["planning_failed"] else ""))

    total = sum(r["tokens"] for r in ledger)
    log(f"=== driver done; {len(ledger)} cells, {total} tokens total ===")


if __name__ == "__main__":
    main()
