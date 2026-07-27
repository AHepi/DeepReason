#!/usr/bin/env python
"""Defended trial v1 — arms A/B/C
(pre-registered: experiments/defended_trial_v1_prereg.yaml).

Arm A (baseline): REPLAYED from the committed critic_specificity judgments
  (experiments/critic_spec_run/judgments.jsonl) — zero new tokens.
Arm B (neutral): same critic model (deepseek-v4-flash, temp 0, strict
  JSON), prompt stripped of prosecutorial framing — a neutral "assess for
  one material, checkable defect" ask with NO mention of prior flags or
  judges — over all 80 items (40 verified-sound + 40 known-flawed). Same
  conviction rule as arm A (defect_found AND named defect >= 20 chars,
  != 'none'; parse failure never convicts).
Arm C (defended): every arm-B conviction goes to trial — independent
  defender deepseek-v4-pro (sees artifact + objection, argues against;
  strict JSON {"defence": str}) then adjudicator mistral-large-3:675b
  (temp 0, strict JSON {"verdict": sustain|overrule|abstain}) run TWICE
  with presentation order swapped (objection-then-defence and
  defence-then-objection). Any disagreement between the two runs, or a
  malformed reply anywhere in the trial, = abstain. Only sustain =
  conviction. Arm-B acquittals pass through as acquittals (no trial
  without an objection).

Checkpoints append-only (resume-safe):
  experiments/defended_trial_run/arm_b.jsonl
  experiments/defended_trial_run/arm_c.jsonl
Ledger: experiments/defended_trial_run/token_usage.json, ceiling 400,000.
Max 3 requests in flight. Console output: ids/booleans/counts only —
never item bodies.

Usage: python scripts/defended_trial_run.py
"""

import concurrent.futures
import json
import os
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from e02_adversary import UsageLedger  # noqa: E402
from e02_t2b_readjudicate import coerce_bool  # noqa: E402
from critic_spec_run import critic_convicts  # noqa: E402

from deepreason.easy import load_credentials  # noqa: E402
from deepreason.llm.endpoints import (  # noqa: E402
    EndpointError, OpenAICompatEndpoint)
from deepreason.llm.repair import parse_one_json_value  # noqa: E402

BASE_URL = "https://ollama.com/v1"
MAX_IN_FLIGHT = 3
TOKEN_CEILING = 400_000

CRITIC_MODEL = "deepseek-v4-flash"
DEFENDER_MODEL = "deepseek-v4-pro"
ADJUDICATOR_MODEL = "mistral-large-3:675b"

FLAWED_ITEMS = REPO / "experiments/e02_t1_items/known_flaws.json"
SOUND_ITEMS = REPO / "experiments/critic_spec_items/sound_items.json"
BASELINE_JUDGMENTS = REPO / "experiments/critic_spec_run/judgments.jsonl"
RUN_DIR = REPO / "experiments/defended_trial_run"
LEDGER_PATH = RUN_DIR / "token_usage.json"
ARM_B_CKPT = RUN_DIR / "arm_b.jsonl"
ARM_C_CKPT = RUN_DIR / "arm_c.jsonl"

# Arm B: neutral critic — no prosecutorial framing, no mention of prior
# flags or judges. Same SPECIFIC-and-CHECKABLE defect definition and the
# same strict-JSON schema as the baseline critic, so the conviction rule
# is applied identically across arms.
NEUTRAL_CRITIC_PROMPT = """Assess the argument below for ONE material, \
checkable reasoning defect.

ARTIFACT:
{artifact}

A defect counts ONLY if it is SPECIFIC and CHECKABLE: name the exact \
claim, step, number, or inference in the artifact that is wrong, and say \
why (logical, quantitative, structural, or evidential). Judge the \
reasoning itself. Style, tone, formatting, simplification for a lay \
audience, or minor omissions do NOT count. If there is no such defect, \
say so.

Reply with EXACTLY one strict JSON object and nothing else:
{{"defect_found": <true|false>, "defect": "<the specific checkable \
defect, citing the exact claim or step and why it is wrong; or 'none'>"}}"""

DEFENDER_PROMPT = """You are the independent defender in an \
argument-adjudication procedure. An objection has been raised against \
the artifact below. Your job is to argue AGAINST the objection: check \
the objection's specifics carefully (the exact claims, numbers, steps, \
and inferences it attacks) and present the strongest honest defence of \
the artifact. If, after checking, the objection is simply correct, an \
honest defence concedes that and says why.

ARTIFACT:
{artifact}

OBJECTION:
{objection}

Reply with EXACTLY one strict JSON object and nothing else:
{{"defence": "<your defence of the artifact against this objection, \
citing the exact claims, numbers, or steps that show the objection \
mistaken or immaterial; or a concession if the objection is correct>"}}"""

ADJUDICATOR_PROMPT = """You are the adjudicator in an \
argument-adjudication procedure. An artifact was submitted; an objection \
was raised against it; a defence of the artifact was offered. Decide \
whether the objection is sustained.

ARTIFACT:
{artifact}

{first_label}:
{first_text}

{second_label}:
{second_text}

SUSTAIN the objection only if it names a genuine, material, checkable \
defect in the artifact's reasoning — a specific claim, step, number, or \
inference that is actually wrong — and the defence does not adequately \
rebut it. OVERRULE if the objection is mistaken, immaterial, or \
adequately rebutted. ABSTAIN only if you genuinely cannot decide.

Reply with EXACTLY one strict JSON object and nothing else:
{{"verdict": "<sustain|overrule|abstain>"}}"""


def make_endpoint(model: str, max_tokens: int) -> OpenAICompatEndpoint:
    return OpenAICompatEndpoint(
        BASE_URL, model,
        api_key=os.environ["OLLAMA_API_KEY"],
        temperature=0.0, max_tokens=max_tokens, json_mode=True,
        reasoning="none", provider="ollama", timeout_s=600,
    )


def strict_json_call(model: str, prompt: str, phase: str,
                     ledger: UsageLedger, max_tokens: int) -> dict:
    """One call: bounded transport backoff + JSON re-asks. A persistent
    failure returns {"parse_failure": True} — a failed instrument never
    convicts (arm B) and forces abstain (arm C)."""
    record: dict = {"model": model, "parse_failure": False,
                    "json_retries": 0, "transport_retries": 0,
                    "prompt_tokens": 0, "completion_tokens": 0}
    ask = prompt
    last_err: Exception | None = None
    for attempt in range(5):
        ledger.check()
        endpoint = make_endpoint(model, max_tokens)
        try:
            raw = endpoint.complete(ask)
        except EndpointError as e:
            last_err = e
            record["transport_retries"] += 1
            delay = min(15 * (2 ** attempt), 240)
            print(f"  [{phase}] endpoint error ({type(e).__name__}); "
                  f"backoff {delay}s", flush=True)
            time.sleep(delay)
            continue
        usage = endpoint.last_usage or {}
        ledger.add(phase, endpoint.last_usage, ask, raw)
        record["prompt_tokens"] += int(usage.get("prompt_tokens") or 0)
        record["completion_tokens"] += int(
            usage.get("completion_tokens") or 0)
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
        record["parsed"] = parsed
        return record
    record.update({"parse_failure": True,
                   "error": f"{type(last_err).__name__}: {str(last_err)[:300]}"})
    return record


def load_items() -> list[tuple[dict, str]]:
    flawed = json.loads(FLAWED_ITEMS.read_text())
    sound = json.loads(SOUND_ITEMS.read_text())
    assert len(flawed) == 40, f"expected 40 flawed items, saw {len(flawed)}"
    assert len(sound) == 40, f"expected 40 sound items, saw {len(sound)}"
    assert all(i["hidden_annotation"]["verified_true"] for i in sound)
    return [(i, "flawed") for i in flawed] + [(i, "sound") for i in sound]


def read_checkpoint(path: Path) -> dict[str, dict]:
    done: dict[str, dict] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            rec = json.loads(line)
            done[rec["id"]] = rec  # last write wins
    return done


def arm_b_judge(item: dict, battery: str, ledger: UsageLedger) -> dict:
    call = strict_json_call(
        CRITIC_MODEL,
        NEUTRAL_CRITIC_PROMPT.format(artifact=item["judged_text"]),
        f"arm_b_{battery}", ledger, max_tokens=1200)
    parsed = call.get("parsed") or {}
    defect_found, defect_text, convicts = critic_convicts(parsed)
    return {
        "id": item["id"], "battery": battery, "arm": "B",
        "critic_model": CRITIC_MODEL,
        "defect_found": defect_found,
        "defect": defect_text[:600] if defect_text else None,
        "convicts": convicts,
        "parse_failure": call["parse_failure"],
        "json_retries": call["json_retries"],
        "transport_retries": call["transport_retries"],
        "prompt_tokens": call["prompt_tokens"],
        "completion_tokens": call["completion_tokens"],
    }


VALID_VERDICTS = ("sustain", "overrule", "abstain")


def adjudicate(artifact: str, objection: str, defence: str, order: str,
               battery: str, ledger: UsageLedger) -> dict:
    if order == "objection_first":
        fl, ft, sl, st = "OBJECTION", objection, "DEFENCE", defence
    else:
        fl, ft, sl, st = "DEFENCE", defence, "OBJECTION", objection
    call = strict_json_call(
        ADJUDICATOR_MODEL,
        ADJUDICATOR_PROMPT.format(artifact=artifact, first_label=fl,
                                  first_text=ft, second_label=sl,
                                  second_text=st),
        f"arm_c_adjudicator_{battery}", ledger, max_tokens=400)
    verdict = None
    if not call["parse_failure"]:
        raw_v = (call.get("parsed") or {}).get("verdict")
        if isinstance(raw_v, str) and raw_v.strip().lower() in VALID_VERDICTS:
            verdict = raw_v.strip().lower()
    return {"order": order, "verdict": verdict,
            "malformed": verdict is None,
            "parse_failure": call["parse_failure"],
            "json_retries": call["json_retries"],
            "transport_retries": call["transport_retries"],
            "prompt_tokens": call["prompt_tokens"],
            "completion_tokens": call["completion_tokens"]}


def arm_c_try(item: dict, battery: str, objection: str,
              ledger: UsageLedger) -> dict:
    """One defended trial. Outcome in {sustain, overrule, abstain}:
    only two concurring valid adjudicator verdicts stand; any malformed
    reply (defender or adjudicator) or order-swap disagreement = abstain."""
    artifact = item["judged_text"]
    rec: dict = {"id": item["id"], "battery": battery, "arm": "C",
                 "defender_model": DEFENDER_MODEL,
                 "adjudicator_model": ADJUDICATOR_MODEL,
                 "objection": objection[:600]}
    dcall = strict_json_call(
        DEFENDER_MODEL,
        DEFENDER_PROMPT.format(artifact=artifact, objection=objection),
        f"arm_c_defender_{battery}", ledger, max_tokens=2000)
    defence = (dcall.get("parsed") or {}).get("defence")
    defence = str(defence).strip() if defence is not None else ""
    rec["defender_parse_failure"] = dcall["parse_failure"]
    rec["defence"] = defence[:600] if defence else None
    rec["defender_prompt_tokens"] = dcall["prompt_tokens"]
    rec["defender_completion_tokens"] = dcall["completion_tokens"]
    if dcall["parse_failure"] or not defence:
        rec.update({"outcome": "abstain", "abstain_reason": "defender_malformed",
                    "adjudications": [], "order_swap_disagreement": None})
        return rec
    adjs = [adjudicate(artifact, objection, defence, order, battery, ledger)
            for order in ("objection_first", "defence_first")]
    rec["adjudications"] = adjs
    v1, v2 = adjs[0]["verdict"], adjs[1]["verdict"]
    if v1 is None or v2 is None:
        outcome, reason = "abstain", "adjudicator_malformed"
        rec["order_swap_disagreement"] = None
    elif v1 != v2:
        outcome, reason = "abstain", "order_swap_disagreement"
        rec["order_swap_disagreement"] = True
    else:
        outcome = v1
        reason = "adjudicator_abstain" if v1 == "abstain" else None
        rec["order_swap_disagreement"] = False
    rec["outcome"] = outcome
    rec["abstain_reason"] = reason
    rec["convicts"] = outcome == "sustain"
    return rec


def main() -> int:
    load_credentials()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    ledger = UsageLedger(LEDGER_PATH, ceiling=TOKEN_CEILING)
    work = load_items()
    by_id = {i["id"]: (i, b) for i, b in work}

    # Arm A sanity replay (zero tokens): confirm the committed baseline.
    base = read_checkpoint(BASELINE_JUDGMENTS)
    assert set(base) == set(by_id), "baseline judgments do not cover items"

    write_lock = threading.Lock()

    def append(path: Path, rec: dict) -> None:
        with write_lock:
            with path.open("a") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")

    # ---- Arm B ----
    done_b = read_checkpoint(ARM_B_CKPT)
    todo_b = [(i, b) for i, b in work if i["id"] not in done_b]
    print(f"arm B: {len(todo_b)} to run ({len(done_b)} checkpointed; "
          f"tokens {ledger.total})", flush=True)

    def b_worker(item, battery):
        rec = arm_b_judge(item, battery, ledger)
        append(ARM_B_CKPT, rec)
        done_b[rec["id"]] = rec
        print(f"  B {rec['id']} [{battery}]: convicts={rec['convicts']} "
              f"parse_failure={rec['parse_failure']} (tokens {ledger.total})",
              flush=True)

    with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
        for f in concurrent.futures.as_completed(
                [pool.submit(b_worker, i, b) for i, b in todo_b]):
            f.result()

    convictions = [rid for rid, r in done_b.items() if r["convicts"]]
    print(f"arm B done: {len(convictions)}/80 convictions "
          f"(tokens {ledger.total})", flush=True)

    # ---- Arm C (arm-B convictions only) ----
    done_c = read_checkpoint(ARM_C_CKPT)
    todo_c = [rid for rid in sorted(convictions) if rid not in done_c]
    print(f"arm C: {len(todo_c)} trials to run ({len(done_c)} checkpointed)",
          flush=True)

    def c_worker(rid):
        item, battery = by_id[rid]
        rec = arm_c_try(item, battery, done_b[rid]["defect"], ledger)
        append(ARM_C_CKPT, rec)
        print(f"  C {rid} [{battery}]: outcome={rec['outcome']} "
              f"reason={rec.get('abstain_reason')} (tokens {ledger.total})",
              flush=True)

    with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
        for f in concurrent.futures.as_completed(
                [pool.submit(c_worker, rid) for rid in todo_c]):
            f.result()

    done_c = read_checkpoint(ARM_C_CKPT)
    n_sustain = sum(1 for r in done_c.values() if r["outcome"] == "sustain")
    n_abstain = sum(1 for r in done_c.values() if r["outcome"] == "abstain")
    n_overrule = sum(1 for r in done_c.values() if r["outcome"] == "overrule")
    print(json.dumps({
        "arm_b_convictions": len(convictions),
        "arm_c_trials": len(done_c),
        "arm_c_sustain": n_sustain,
        "arm_c_overrule": n_overrule,
        "arm_c_abstain": n_abstain,
        "tokens": ledger.total,
    }), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
