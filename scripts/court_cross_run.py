#!/usr/bin/env python
"""Bronze court-cross v1 judging runner
(pre-registered: experiments/bronze_court_cross_v1_prereg.yaml, amendment 1).

One frozen, blinded candidate pool (experiments/court_cross_pool_v1.json,
110 items); the treatment is the court alone:

  arm dsflash:  critic deepseek-v4-flash,     seats [deepseek-v4-pro, gpt-oss:120b]
  arm kimi:     critic kimi-k2.6,             seats [kimi-k2.6, gpt-oss:120b]
  arm mistral:  critic mistral-large-3:675b,  seats [mistral-large-3:675b, gpt-oss:120b]

Per item per arm: neutral critic (defended_trial_v1's NEUTRAL_CRITIC_PROMPT,
identical conviction rule); if it objects, the fixed defender
(deepseek-v4-pro) responds, then seat 1 rules with objection first and
seat 2 rules with defence first (the two-seat order-split reading of the
prereg, amendment 1). All rulings recorded; observe-only study, no status
changes anywhere.

Checkpoints append-only: experiments/court_cross_run/arm_<name>.jsonl
Ledger: experiments/court_cross_run/token_usage.json, ceiling 600,000.
Max 3 requests in flight. Console: ids/counts only, never item bodies.
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
from defended_trial_run import (  # noqa: E402
    ADJUDICATOR_PROMPT, DEFENDER_PROMPT, NEUTRAL_CRITIC_PROMPT,
    strict_json_call, VALID_VERDICTS)

POOL = REPO / "experiments/court_cross_pool_v1.json"
RUN_DIR = REPO / "experiments/court_cross_run"
LEDGER_PATH = RUN_DIR / "token_usage.json"
TOKEN_CEILING = 600_000
MAX_IN_FLIGHT = 3
DEFENDER_MODEL = "deepseek-v4-pro"

ARMS = {
    "dsflash": {"critic": "deepseek-v4-flash",
                "seats": ["deepseek-v4-pro", "gpt-oss:120b"]},
    "kimi": {"critic": "kimi-k2.6",
             "seats": ["kimi-k2.6", "gpt-oss:120b"]},
    "mistral": {"critic": "mistral-large-3:675b",
                "seats": ["mistral-large-3:675b", "gpt-oss:120b"]},
}


def seat_rule(seat_model: str, artifact: str, objection: str, defence: str,
              order: str, arm: str, ledger: UsageLedger) -> dict:
    if order == "objection_first":
        fl, ft, sl, st = "OBJECTION", objection, "DEFENCE", defence
    else:
        fl, ft, sl, st = "DEFENCE", defence, "OBJECTION", objection
    call = strict_json_call(
        seat_model,
        ADJUDICATOR_PROMPT.format(artifact=artifact, first_label=fl,
                                  first_text=ft, second_label=sl,
                                  second_text=st),
        f"{arm}_seat", ledger, max_tokens=400)
    verdict = None
    if not call["parse_failure"]:
        raw_v = (call.get("parsed") or {}).get("verdict")
        if isinstance(raw_v, str) and raw_v.strip().lower() in VALID_VERDICTS:
            verdict = raw_v.strip().lower()
    return {"seat": seat_model, "order": order, "verdict": verdict,
            "malformed": verdict is None,
            "prompt_tokens": call["prompt_tokens"],
            "completion_tokens": call["completion_tokens"]}


def judge_item(arm: str, spec: dict, item: dict, ledger: UsageLedger) -> dict:
    artifact = item["content"]
    rec: dict = {"id": item["sha256"], "arm": arm}
    ccall = strict_json_call(
        spec["critic"], NEUTRAL_CRITIC_PROMPT.format(artifact=artifact),
        f"{arm}_critic", ledger, max_tokens=1200)
    defect_found, defect_text, convicts = critic_convicts(
        ccall.get("parsed") or {})
    rec.update({"critic_model": spec["critic"],
                "objects": bool(convicts),
                "objection": (defect_text or "")[:600] or None,
                "critic_parse_failure": ccall["parse_failure"]})
    if not convicts:
        rec["rulings"] = []
        return rec
    dcall = strict_json_call(
        DEFENDER_MODEL,
        DEFENDER_PROMPT.format(artifact=artifact, objection=defect_text),
        f"{arm}_defender", ledger, max_tokens=2000)
    defence = str((dcall.get("parsed") or {}).get("defence") or "").strip()
    rec["defender_parse_failure"] = dcall["parse_failure"]
    if dcall["parse_failure"] or not defence:
        rec.update({"rulings": [], "abstain_reason": "defender_malformed"})
        return rec
    rec["rulings"] = [
        seat_rule(spec["seats"][0], artifact, defect_text, defence,
                  "objection_first", arm, ledger),
        seat_rule(spec["seats"][1], artifact, defect_text, defence,
                  "defence_first", arm, ledger),
    ]
    verdicts = [r["verdict"] for r in rec["rulings"]]
    if None in verdicts:
        rec["outcome"] = "abstain"
    elif verdicts[0] != verdicts[1]:
        rec["outcome"] = "abstain"
        rec["seat_disagreement"] = True
    else:
        rec["outcome"] = verdicts[0]
        rec["seat_disagreement"] = False
    return rec


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    import os
    if not os.environ.get("OLLAMA_API_KEY"):
        from deepreason.easy import load_credentials
        load_credentials()
    pool = json.loads(POOL.read_text())["items"]
    ledger = UsageLedger(LEDGER_PATH, TOKEN_CEILING)
    for arm, spec in ARMS.items():
        ckpt = RUN_DIR / f"arm_{arm}.jsonl"
        done = set()
        if ckpt.exists():
            done = {json.loads(l)["id"] for l in ckpt.read_text().splitlines()}
        todo = [item for item in pool if item["sha256"] not in done]
        print(f"[{arm}] {len(done)} done, {len(todo)} to judge", flush=True)

        def worker(item, arm=arm, spec=spec):
            return judge_item(arm, spec, item, ledger)

        with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as poolx:
            for rec in poolx.map(worker, todo):
                with ckpt.open("a") as fh:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
                    fh.flush()
        print(f"[{arm}] complete", flush=True)
    print("ALL ARMS COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
