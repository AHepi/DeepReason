#!/usr/bin/env python
"""Court calibration v1 runner
(prereg: experiments/court_calibration_v1_prereg.yaml).

84 singles (42 clean + 42 corrupted, interleaved by pair id), judged blind
by the exact feedback-v2 court: critic deepseek-v4-flash, defender
deepseek-v4-pro, seats [deepseek-v4-pro, gpt-oss:120b], order-split.
Checkpoint: experiments/court_calibration_run/judgments.jsonl.
Ledger ceiling 700,000. Max 3 in flight. Console: ids/counts only.
"""

import concurrent.futures
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from e02_adversary import UsageLedger  # noqa: E402
from court_cross_run import judge_item  # noqa: E402

PAIRS = REPO / "experiments/court_calibration_items/pairs_v1.json"
RUN_DIR = REPO / "experiments/court_calibration_run"
LEDGER_PATH = RUN_DIR / "token_usage.json"
TOKEN_CEILING = 700_000
MAX_IN_FLIGHT = 3
COURT = {"critic": "deepseek-v4-flash",
         "seats": ["deepseek-v4-pro", "gpt-oss:120b"]}


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    import os
    if not os.environ.get("OLLAMA_API_KEY"):
        from deepreason.easy import load_credentials
        load_credentials()
    pairs = json.loads(PAIRS.read_text())
    singles = []
    for pair in pairs:
        singles.append({"sha256": f"{pair['pair_id']}:clean",
                        "content": pair["clean"]})
        singles.append({"sha256": f"{pair['pair_id']}:corrupted",
                        "content": pair["corrupted"]})
    ckpt = RUN_DIR / "judgments.jsonl"
    done = set()
    if ckpt.exists():
        done = {json.loads(l)["id"] for l in ckpt.read_text().splitlines()}
    todo = [s for s in singles if s["sha256"] not in done]
    print(f"{len(done)} done, {len(todo)} to judge", flush=True)
    ledger = UsageLedger(LEDGER_PATH, TOKEN_CEILING)

    def worker(item):
        return judge_item("calibration", COURT, item, ledger)

    with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
        for rec in pool.map(worker, todo):
            with ckpt.open("a") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
                fh.flush()
    print("CALIBRATION COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
