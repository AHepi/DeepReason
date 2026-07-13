#!/usr/bin/env python
"""E0.2 tranche 3 — the judge zoo (pre-registered:
experiments/e02_t3_judge_zoo_prereg.yaml).

Judges the frozen tranche-1/2 corpus (40 known-flaw + 40 unknown-flaw +
40 clean = 120 items, reused unchanged, zero generation spend) with every
seat of the prereg roster individually at temperature 0, reasoning none,
plus a three-model reasoning arm (deepseek-v4-flash, gpt-oss:120b,
kimi-k2.6) re-judging all 120 items at reasoning low.

Phases:
  (1) roster probe: GET /v1/models; every roster model is checked for
      availability and any substitution is recorded in roster_probe.json
      (never silent).
  (2) judging: one call per (item, seat); strict-JSON verdict prompt
      identical to tranches 1/2 (scripts/e02_judge.py). Each judgment
      records latency, prompt/completion token usage, response length,
      parse failures and retry counts.
  (3) checkpointing: append-only judgments.jsonl under
      experiments/e02_t3_run/; the run resumes after any crash.

Budget: shared UsageLedger (experiments/e02_t3_run/token_usage.json),
hard ceiling 1,500,000 tokens; max 3 requests in flight.

Usage: python scripts/e02_t3_run.py [--out-dir experiments/e02_t3_run]
                                    [--probe-only]
"""

import argparse
import concurrent.futures
import json
import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from e02_adversary import UsageLedger  # noqa: E402
from e02_judge import JUDGE_PROMPT  # noqa: E402

from deepreason.easy import load_credentials  # noqa: E402
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402
from deepreason.llm.repair import parse_one_json_value  # noqa: E402

BASE_URL = "https://ollama.com/v1"
MAX_IN_FLIGHT = 3
TOKEN_CEILING = 1_500_000

# Prereg roster (design.seats), in prereg order: anchors first.
ROSTER = [
    "gpt-oss:120b",
    "qwen3-coder:480b",
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    "glm-5.2",
    "kimi-k2.6",
    "minimax-m2.7",
    "mistral-large-3:675b",
    "nemotron-3-ultra",
    "qwen3.5:397b",
    "gemma3:27b",
]

# Prereg reasoning arm (design.reasoning_arm): reasoning low vs default none.
REASONING_ARM = ["deepseek-v4-flash", "gpt-oss:120b", "kimi-k2.6"]

KNOWN = REPO / "experiments/e02_t1_items/known_flaws.json"
UNKNOWN = REPO / "experiments/e02_t1_items/unknown_flaws.json"
CLEAN = REPO / "experiments/e02_t2_items/clean_items.json"


def load_items() -> list[dict]:
    items: list[dict] = []
    for path in (KNOWN, UNKNOWN, CLEAN):
        items.extend(json.loads(path.read_text()))
    assert len(items) == 120, f"expected 120 frozen items, found {len(items)}"
    return items


def probe_roster(out_dir: Path) -> list[str]:
    """GET /v1/models; record availability + substitutions (none silent)."""
    req = urllib.request.Request(
        BASE_URL + "/models",
        headers={"Authorization": f"Bearer {os.environ['OLLAMA_API_KEY']}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        available = sorted(m["id"] for m in json.load(resp)["data"])
    roster_as_run: list[str] = []
    substitutions: list[dict] = []
    for model in ROSTER:
        if model in available:
            roster_as_run.append(model)
        else:
            # Substitution policy: nearest same-family tag by shared prefix;
            # if none, the seat is dropped. Either way it is RECORDED.
            family = model.split(":")[0].rstrip("0123456789.-")
            candidates = [m for m in available if m.startswith(family)]
            sub = sorted(candidates)[-1] if candidates else None
            substitutions.append(
                {"requested": model, "substituted": sub,
                 "reason": "not in /v1/models at probe time"})
            if sub:
                roster_as_run.append(sub)
    record = {
        "probed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": BASE_URL + "/models",
        "available_model_count": len(available),
        "roster_requested": ROSTER,
        "roster_as_run": roster_as_run,
        "substitutions": substitutions,
        "reasoning_arm": REASONING_ARM,
    }
    (out_dir / "roster_probe.json").write_text(
        json.dumps(record, indent=2) + "\n")
    print(f"probe: {len(roster_as_run)}/{len(ROSTER)} roster seats available, "
          f"{len(substitutions)} substitutions", flush=True)
    return roster_as_run


def make_endpoint(model: str, reasoning: str, max_tokens: int):
    return OpenAICompatEndpoint(
        BASE_URL, model,
        api_key=os.environ["OLLAMA_API_KEY"],
        temperature=0.0, max_tokens=max_tokens, json_mode=True,
        reasoning=reasoning, provider="ollama", timeout_s=600,
    )


def judge_one(item: dict, seat_id: str, model: str, reasoning: str,
              max_tokens: int, ledger: UsageLedger) -> dict:
    """One seat judgment with per-call latency/usage capture, strict-JSON
    parsing, bounded JSON re-asks and transport backoff. Parse failure is
    recorded as flawed=false (conservative against the judge), as t1/t2."""
    prompt = JUDGE_PROMPT.format(artifact=item["judged_text"])
    record = {
        "item_id": item["id"], "seat": seat_id, "model": model,
        "reasoning": reasoning, "sub_battery": item["sub_battery"],
        "latency_s": None, "prompt_tokens": None, "completion_tokens": None,
        "response_chars": None, "json_retries": 0, "transport_retries": 0,
    }
    ask = prompt
    last_err = None
    started = time.monotonic()
    for attempt in range(5):
        ledger.check()
        endpoint = make_endpoint(model, reasoning, max_tokens)
        t0 = time.monotonic()
        try:
            raw = endpoint.complete(ask)
        except EndpointError as e:
            last_err = e
            record["transport_retries"] += 1
            delay = min(15 * (2 ** attempt), 240)
            print(f"  [{seat_id}/{item['id']}] endpoint error "
                  f"({type(e).__name__}); backoff {delay}s", flush=True)
            time.sleep(delay)
            continue
        latency = time.monotonic() - t0
        usage = endpoint.last_usage or {}
        ledger.add(f"judge-{seat_id}", endpoint.last_usage, ask, raw)
        # First successful wire response defines the seat's latency/cost row;
        # re-ask spend is still ledgered and counted in *_retries.
        if record["latency_s"] is None:
            record.update({
                "latency_s": round(latency, 3),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "response_chars": len(raw),
                "finish_reason": endpoint.last_finish_reason,
            })
        try:
            parsed = json.loads(parse_one_json_value(raw).text)
            if not isinstance(parsed, dict):
                raise ValueError("top-level JSON value is not an object")
        except ValueError as e:
            last_err = e
            record["json_retries"] += 1
            ask = (prompt + "\n\nYour previous reply was not a single valid "
                   "JSON object. Reply with EXACTLY one JSON object and "
                   "nothing else.")
            continue
        flawed = parsed.get("flawed")
        kind = parsed.get("kind")
        if not isinstance(flawed, bool):
            if isinstance(flawed, str) and \
                    flawed.strip().lower() in ("true", "false"):
                flawed = flawed.strip().lower() == "true"
            else:
                last_err = ValueError("no boolean 'flawed' field")
                record["json_retries"] += 1
                ask = (prompt + "\n\nYour previous reply lacked a boolean "
                       '"flawed" field. Reply with EXACTLY '
                       '{"flawed": <true|false>, "kind": "<words>"} '
                       "and nothing else.")
                continue
        record.update({
            "flawed": flawed,
            "kind": str(kind)[:120] if kind is not None else None,
            "parse_failure": False,
            "total_s": round(time.monotonic() - started, 3),
        })
        return record
    record.update({
        "flawed": False, "kind": None, "parse_failure": True,
        "error": f"{type(last_err).__name__}: {str(last_err)[:300]}",
        "total_s": round(time.monotonic() - started, 3),
    })
    return record


def run(out_dir: Path, roster: list[str], items: list[dict],
        ledger: UsageLedger) -> None:
    checkpoint = out_dir / "judgments.jsonl"
    done: set[tuple[str, str]] = set()
    if checkpoint.exists():
        for line in checkpoint.read_text().splitlines():
            rec = json.loads(line)
            done.add((rec["item_id"], rec["seat"]))

    # Seat plan: roster seats (reasoning none, max_tokens 1200 as t1/t2),
    # then the reasoning arm (reasoning low, larger cap so thinking tokens
    # cannot truncate the verdict JSON).
    seats: list[tuple[str, str, str, int]] = []
    for model in roster:
        seats.append((f"zoo:{model}", model, "none", 1200))
    for model in REASONING_ARM:
        seats.append((f"rlow:{model}", model, "low", 3000))

    jobs = [(item, seat_id, model, reasoning, max_tokens)
            for seat_id, model, reasoning, max_tokens in seats
            for item in items
            if (item["id"], seat_id) not in done]
    print(f"judging: {len(jobs)} seat-calls to run "
          f"({len(done)} already checkpointed; "
          f"tokens so far {ledger.total})", flush=True)
    write_lock = threading.Lock()
    completed = 0

    def worker(item, seat_id, model, reasoning, max_tokens):
        nonlocal completed
        rec = judge_one(item, seat_id, model, reasoning, max_tokens, ledger)
        with write_lock:
            with checkpoint.open("a") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
            completed += 1
            if completed % 40 == 0:
                print(f"  {completed}/{len(jobs)} judgments "
                      f"(tokens: {ledger.total})", flush=True)
        return rec

    with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
        futures = [pool.submit(worker, *job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            future.result()  # propagate budget exhaustion
    print(f"judging complete; total tokens {ledger.total}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="experiments/e02_t3_run")
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args()
    load_credentials()
    out_dir = REPO / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    roster = probe_roster(out_dir)
    if args.probe_only:
        return 0
    items = load_items()
    ledger = UsageLedger(out_dir / "token_usage.json", ceiling=TOKEN_CEILING)
    run(out_dir, roster, items, ledger)
    print(json.dumps(
        {k: v["prompt_tokens"] + v["completion_tokens"]
         for k, v in ledger.state["phases"].items()}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
