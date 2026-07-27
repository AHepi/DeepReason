#!/usr/bin/env python
"""Schema comparator v1 runner
(prereg: experiments/schema_comparator_v1_prereg.yaml).

85 items x 3 frozen forms x 2 critics, critic calls only (the measured
outcome is the objection ground). Checkpoints append-only per critic:
experiments/schema_comparator_run/<critic>.jsonl. Ledger ceiling 1.5M,
max 3 in flight. Console: ids/counts only.
"""

import concurrent.futures
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from e02_adversary import UsageLedger  # noqa: E402
from critic_spec_run import critic_convicts  # noqa: E402
from defended_trial_run import NEUTRAL_CRITIC_PROMPT, strict_json_call  # noqa: E402

FORMS = REPO / "experiments/schema_comparator_forms_v1.json"
RUN_DIR = REPO / "experiments/schema_comparator_run"
LEDGER_PATH = RUN_DIR / "token_usage.json"
TOKEN_CEILING = 1_500_000
MAX_IN_FLIGHT = 3
CRITICS = {"dsflash": "deepseek-v4-flash", "kimi": "kimi-k2.6"}
FORM_KEYS = ("A_original", "B_comparator_aware", "C_scope_neutral_prose")


def judge(critic_model: str, critic_key: str, item: dict, form_key: str,
          ledger: UsageLedger) -> dict:
    call = strict_json_call(
        critic_model,
        NEUTRAL_CRITIC_PROMPT.format(artifact=item["forms"][form_key]),
        f"{critic_key}_{form_key}", ledger, max_tokens=1200)
    _found, defect_text, convicts = critic_convicts(call.get("parsed") or {})
    return {
        "id": item["sha256"], "form": form_key, "critic": critic_key,
        "objects": bool(convicts),
        "objection": (defect_text or "")[:600] or None,
        "parse_failure": call["parse_failure"],
        "prompt_tokens": call["prompt_tokens"],
        "completion_tokens": call["completion_tokens"],
    }


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    import os
    if not os.environ.get("OLLAMA_API_KEY"):
        from deepreason.easy import load_credentials
        load_credentials()
    items = json.loads(FORMS.read_text())["items"]
    ledger = UsageLedger(LEDGER_PATH, TOKEN_CEILING)
    for critic_key, critic_model in CRITICS.items():
        ckpt = RUN_DIR / f"{critic_key}.jsonl"
        done = set()
        if ckpt.exists():
            done = {(r["id"], r["form"])
                    for r in map(json.loads, ckpt.read_text().splitlines())}
        todo = [(item, form) for item in items for form in FORM_KEYS
                if (item["sha256"], form) not in done]
        print(f"[{critic_key}] {len(done)} done, {len(todo)} to judge", flush=True)

        def worker(pair, ck=critic_key, cm=critic_model):
            item, form = pair
            return judge(cm, ck, item, form, ledger)

        with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
            for rec in pool.map(worker, todo):
                with ckpt.open("a") as fh:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
                    fh.flush()
        print(f"[{critic_key}] complete", flush=True)
    print("SCHEMA COMPARATOR COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
