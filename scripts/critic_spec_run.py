#!/usr/bin/env python
"""Critic specificity — critic pass over both batteries
(pre-registered: experiments/critic_specificity_prereg.yaml).

Runs the argumentative critic EXACTLY as fielded — the t2b call shape is
imported from scripts/e02_t2b_readjudicate.py (same model deepseek-v4-flash,
same CRITIC_PROMPT, same strict-JSON call with bounded backoff, same
conviction rule: defect_found AND a named defect string >= 20 chars not
'none'; parse failure never convicts) — over:

  (a) the 40 frozen known-flawed t1 items
      (experiments/e02_t1_items/known_flaws.json), and
  (b) the 40 new verified-sound items
      (experiments/critic_spec_items/sound_items.json).

Judgments are checkpointed append-only in
experiments/critic_spec_run/judgments.jsonl (resume-safe). Ledger shared
with the corpus builder (whole-experiment ceiling 250,000 tokens); max 3
requests in flight. Console output: ids/booleans/counts only.

Usage: python scripts/critic_spec_run.py
"""

import concurrent.futures
import json
import sys
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from e02_adversary import UsageLedger  # noqa: E402
from e02_t2b_readjudicate import (  # noqa: E402
    CRITIC_MODEL, CRITIC_PROMPT, coerce_bool, strict_json_call)

from deepreason.easy import load_credentials  # noqa: E402

MAX_IN_FLIGHT = 3
TOKEN_CEILING = 250_000  # whole-experiment cap (corpus + critic runs)

FLAWED_ITEMS = REPO / "experiments/e02_t1_items/known_flaws.json"
SOUND_ITEMS = REPO / "experiments/critic_spec_items/sound_items.json"
RUN_DIR = REPO / "experiments/critic_spec_run"
LEDGER_PATH = RUN_DIR / "token_usage.json"
CHECKPOINT = RUN_DIR / "judgments.jsonl"


def critic_convicts(parsed: dict) -> tuple[bool | None, str, bool]:
    """t2b conviction rule, verbatim semantics."""
    defect_found = coerce_bool(parsed.get("defect_found"))
    defect = parsed.get("defect")
    defect_text = str(defect).strip() if defect is not None else ""
    convicts = bool(
        defect_found is True and defect_text
        and defect_text.lower() != "none" and len(defect_text) >= 20)
    return defect_found, defect_text, convicts


def judge_one(item: dict, battery: str, ledger: UsageLedger) -> dict:
    call = strict_json_call(
        CRITIC_MODEL, CRITIC_PROMPT.format(artifact=item["judged_text"]),
        f"critic_{battery}", ledger)
    parsed = call.get("parsed") or {}
    defect_found, defect_text, convicts = critic_convicts(parsed)
    return {
        "id": item["id"],
        "battery": battery,
        "critic_model": CRITIC_MODEL,
        "defect_found": defect_found,
        "defect": defect_text[:400] if defect_text else None,
        "convicts": convicts,
        "parse_failure": call["parse_failure"],
        "json_retries": call["json_retries"],
        "transport_retries": call["transport_retries"],
        "prompt_tokens": call["prompt_tokens"],
        "completion_tokens": call["completion_tokens"],
    }


def main() -> int:
    load_credentials()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    ledger = UsageLedger(LEDGER_PATH, ceiling=TOKEN_CEILING)

    flawed = json.loads(FLAWED_ITEMS.read_text())
    sound = json.loads(SOUND_ITEMS.read_text())
    assert len(flawed) == 40, f"expected 40 flawed items, saw {len(flawed)}"
    assert len(sound) == 40, f"expected 40 sound items, saw {len(sound)}"
    assert all(i["hidden_annotation"]["verified_true"] for i in sound)

    work = ([(i, "flawed") for i in flawed] + [(i, "sound") for i in sound])
    done: dict[str, dict] = {}
    if CHECKPOINT.exists():
        for line in CHECKPOINT.read_text().splitlines():
            rec = json.loads(line)
            done[rec["id"]] = rec  # last write wins
    todo = [(i, b) for i, b in work if i["id"] not in done]
    print(f"critic pass: {len(todo)} items to run ({len(done)} "
          f"checkpointed; tokens so far {ledger.total})", flush=True)
    write_lock = threading.Lock()

    def worker(item, battery):
        rec = judge_one(item, battery, ledger)
        with write_lock:
            with CHECKPOINT.open("a") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
            done[rec["id"]] = rec
        print(f"  {rec['id']} [{battery}]: convicts={rec['convicts']} "
              f"parse_failure={rec['parse_failure']} "
              f"(tokens {ledger.total})", flush=True)

    with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
        futures = [pool.submit(worker, i, b) for i, b in todo]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    n_conv = {"flawed": 0, "sound": 0}
    for i, b in work:
        if done[i["id"]]["convicts"]:
            n_conv[b] += 1
    print(json.dumps({
        "flawed_convictions": n_conv["flawed"],
        "sound_convictions": n_conv["sound"],
        "tokens": ledger.total,
    }), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
