#!/usr/bin/env python
"""E0.2 tranche 2b — re-adjudication of suspect clean items
(pre-registered: experiments/e02_t2b_clean_readjudication_prereg.yaml).

Motivated by the t3 exploratory finding that 11 of 40 "clean" items drew
flags from >=5 of the 13 zoo/reasoning seats. Each suspect item is
adjudicated by two high-precision instruments:

  (a) the argumentative critic (deepseek-v4-flash, t1-certified as the
      effective defense), required to name ONE specific, checkable defect
      — strict JSON {"defect_found": bool, "defect": str};
  (b) mistral-large-3:675b (zoo clean FP 0.00 in t3), same strict-JSON
      verdict prompt as the zoo seats ({"flawed": bool, "kind": str}).

An item is reclassified DEFECTIVE only if BOTH concur (conservative
conjunction — precision over recall; both instruments are themselves
fallible LLM judges). The corrected clean set then re-scores t2's P2/P3
(t2 catch rates on the flawed batteries are untouched; only the clean
false-positive denominator shrinks by the reclassified items). The
original t2 report is never edited — this report supersedes its clean-FP
rows as a correction record.

Verdicts (prereg literal):
  P1 CONFIRMED iff >= 3 of the 11 suspect items are reclassified DEFECTIVE.
  P2 CONFIRMED iff corrected either-suffices cross-family clean FP <= 0.40
     (the t2 rejection line); REFUTED if it stays > 0.40.
  P3 CONFIRMED iff the corrected t2 net (unknown-catch gain pp minus
     corrected clean-FP rise pp, cross-family) is strictly positive.

Budget: 120,000 tokens (UsageLedger, experiments/e02_t2b_run/
token_usage.json); max 3 requests in flight; adjudications checkpointed
append-only in adjudications.jsonl (resume-safe).

Usage: python scripts/e02_t2b_readjudicate.py
"""

import concurrent.futures
import datetime as dt
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
from e02_judge import JUDGE_PROMPT  # noqa: E402
from e02_t2_score import PAIRS, RULES, load_seats, pair_flags, rate_row  # noqa: E402

from deepreason.easy import load_credentials  # noqa: E402
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402
from deepreason.llm.repair import parse_one_json_value  # noqa: E402

BASE_URL = "https://ollama.com/v1"
MAX_IN_FLIGHT = 3
TOKEN_CEILING = 120_000
CRITIC_MODEL = "deepseek-v4-flash"
JUDGE_MODEL = "mistral-large-3:675b"
SUSPECT_MIN_FLAGS = 5

PREREG = "experiments/e02_t2b_clean_readjudication_prereg.yaml"
SCHEMA = "deepreason-e02-t2b-v1"

T3_JUDGMENTS = REPO / "experiments/e02_t3_run/judgments.jsonl"
CLEAN_ITEMS = REPO / "experiments/e02_t2_items/clean_items.json"
T1_DIR = REPO / "experiments/e02_t1_items"
T2_DIR = REPO / "experiments/e02_t2_items"
OUT_DIR = REPO / "experiments/e02_t2b_run"
RESULTS = REPO / "experiments/results"

CRITIC_PROMPT = """You are the argumentative critic of a certification \
pipeline. The artifact below was submitted as flaw-free, but an ensemble of \
independent judges flagged it; your job is to attack it and find a genuine \
disqualifying reasoning defect if one exists.

ARTIFACT:
{artifact}

A defect counts ONLY if it is SPECIFIC and CHECKABLE: name the exact claim, \
step, number, or inference in the artifact that is wrong, and say why \
(logical, quantitative, structural, or evidential). Judge the reasoning \
itself. Style, tone, formatting, simplification for a lay audience, or \
minor omissions that would not disqualify certification do NOT count. If \
you cannot name one specific checkable defect, report that honestly.

Reply with EXACTLY one strict JSON object and nothing else:
{{"defect_found": <true|false>, "defect": "<the specific checkable defect, \
citing the exact claim or step and why it is wrong; or 'none'>"}}"""


def make_endpoint(model: str) -> OpenAICompatEndpoint:
    return OpenAICompatEndpoint(
        BASE_URL, model,
        api_key=os.environ["OLLAMA_API_KEY"],
        temperature=0.0, max_tokens=1200, json_mode=True,
        reasoning="none", provider="ollama", timeout_s=600,
    )


def suspect_ids() -> tuple[list[dict], int]:
    """Clean items flagged by >= SUSPECT_MIN_FLAGS of their t3 seats."""
    flags: dict[str, int] = {}
    seats_per_item: dict[str, int] = {}
    for line in T3_JUDGMENTS.read_text().splitlines():
        rec = json.loads(line)
        if rec["sub_battery"] != "clean":
            continue
        seats_per_item[rec["item_id"]] = seats_per_item.get(rec["item_id"], 0) + 1
        if rec["flawed"]:
            flags[rec["item_id"]] = flags.get(rec["item_id"], 0) + 1
    n_seats = sorted(set(seats_per_item.values()))
    assert n_seats == [13], f"expected 13 seats per clean item, saw {n_seats}"
    suspects = sorted(
        (i for i, c in flags.items() if c >= SUSPECT_MIN_FLAGS),
        key=lambda i: (-flags[i], i))
    return [{"id": i, "t3_zoo_flags": flags[i], "t3_seats": 13}
            for i in suspects], len(seats_per_item)


def strict_json_call(model: str, prompt: str, phase: str,
                     ledger: UsageLedger) -> dict:
    """One adjudication call: bounded transport backoff + JSON re-asks.
    A persistent failure returns {"parse_failure": True} — conservative
    against reclassification (a failed instrument never convicts)."""
    record: dict = {"model": model, "parse_failure": False,
                    "json_retries": 0, "transport_retries": 0,
                    "prompt_tokens": None, "completion_tokens": None}
    ask = prompt
    last_err: Exception | None = None
    for attempt in range(5):
        ledger.check()
        endpoint = make_endpoint(model)
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
        if record["prompt_tokens"] is None:
            record["prompt_tokens"] = usage.get("prompt_tokens")
            record["completion_tokens"] = usage.get("completion_tokens")
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


def coerce_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ("true", "false"):
        return value.strip().lower() == "true"
    return None


def adjudicate_one(item: dict, meta: dict, ledger: UsageLedger) -> dict:
    """Both instruments on one suspect item; DEFECTIVE iff both concur."""
    text = item["judged_text"]
    critic = strict_json_call(CRITIC_MODEL, CRITIC_PROMPT.format(artifact=text),
                              "critic", ledger)
    judge = strict_json_call(JUDGE_MODEL, JUDGE_PROMPT.format(artifact=text),
                             "judge", ledger)

    critic_parsed = critic.get("parsed") or {}
    defect_found = coerce_bool(critic_parsed.get("defect_found"))
    defect = critic_parsed.get("defect")
    defect_text = str(defect).strip() if defect is not None else ""
    # Prereg requirement: the critic must NAME a specific checkable defect.
    # A bare true with no substantive defect string does not convict.
    critic_convicts = bool(
        defect_found is True and defect_text
        and defect_text.lower() != "none" and len(defect_text) >= 20)

    judge_parsed = judge.get("parsed") or {}
    flawed = coerce_bool(judge_parsed.get("flawed"))
    kind = judge_parsed.get("kind")
    judge_convicts = flawed is True

    return {
        "id": item["id"],
        "t3_zoo_flags": meta["t3_zoo_flags"],
        "t3_seats": meta["t3_seats"],
        "critic": {
            "model": CRITIC_MODEL,
            "defect_found": defect_found,
            "defect": defect_text[:400] if defect_text else None,
            "convicts": critic_convicts,
            "parse_failure": critic["parse_failure"],
            "json_retries": critic["json_retries"],
            "transport_retries": critic["transport_retries"],
        },
        "judge": {
            "model": JUDGE_MODEL,
            "flawed": flawed,
            "kind": str(kind)[:120] if kind is not None else None,
            "convicts": judge_convicts,
            "parse_failure": judge["parse_failure"],
            "json_retries": judge["json_retries"],
            "transport_retries": judge["transport_retries"],
        },
        "reclassified_defective": critic_convicts and judge_convicts,
    }


def corrected_rate_table(defective_ids: set[str]) -> tuple[dict, dict]:
    """Re-run the t2 scoring on the corrected clean set: reclassified
    items leave the clean FP denominator; flawed-battery catch rates are
    recomputed unchanged from the same committed judgments."""
    items: list[dict] = []
    for name in ("unknown_flaws.json", "known_flaws.json"):
        items.extend(json.loads((T1_DIR / name).read_text()))
    clean_items = json.loads((T2_DIR / "clean_items.json").read_text())
    items.extend(clean_items)

    seats = load_seats(T1_DIR / "judgments.jsonl")
    seats.update(load_seats(T2_DIR / "judgments.jsonl"))

    per_item = []
    for item in sorted(items, key=lambda i: i["id"]):
        per_item.append({
            "id": item["id"],
            "sub_battery": item["sub_battery"],
            "pairs": {pair: pair_flags(seats, item["id"], pair)
                      for pair in PAIRS},
        })
    batteries = {
        "unknown_flaw": [r for r in per_item if r["sub_battery"] == "unknown_flaw"],
        "known_flaw": [r for r in per_item if r["sub_battery"] == "known_flaw"],
        "clean_corrected": [r for r in per_item if r["sub_battery"] == "clean"
                            and r["id"] not in defective_ids],
        "clean_original": [r for r in per_item if r["sub_battery"] == "clean"],
    }
    table = {rule: {pair: {battery: rate_row(rows, pair, rule)
                           for battery, rows in batteries.items()}
                    for pair in PAIRS}
             for rule in RULES}
    volumes = {battery: len(rows) for battery, rows in batteries.items()}
    return table, volumes


def main() -> int:
    load_credentials()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    ledger = UsageLedger(OUT_DIR / "token_usage.json", ceiling=TOKEN_CEILING)

    suspects, n_clean = suspect_ids()
    assert n_clean == 40, f"expected 40 clean items in t3, saw {n_clean}"
    assert len(suspects) == 11, \
        f"prereg names 11 suspect items; recomputed {len(suspects)}"
    by_id = {s["id"]: s for s in suspects}
    clean_items = {i["id"]: i for i in json.loads(CLEAN_ITEMS.read_text())}
    print("suspects:", json.dumps(
        {s["id"]: s["t3_zoo_flags"] for s in suspects}), flush=True)

    # ------------------------------------------------------------------ #
    # Adjudication (checkpointed, resume-safe, max 3 in flight).
    # ------------------------------------------------------------------ #
    checkpoint = OUT_DIR / "adjudications.jsonl"
    done: dict[str, dict] = {}
    if checkpoint.exists():
        for line in checkpoint.read_text().splitlines():
            rec = json.loads(line)
            done[rec["id"]] = rec  # last write wins
    todo = [clean_items[s["id"]] for s in suspects if s["id"] not in done]
    print(f"adjudicating: {len(todo)} items to run "
          f"({len(done)} checkpointed; tokens so far {ledger.total})",
          flush=True)
    write_lock = threading.Lock()

    def worker(item):
        rec = adjudicate_one(item, by_id[item["id"]], ledger)
        with write_lock:
            with checkpoint.open("a") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
            done[rec["id"]] = rec
        print(f"  {rec['id']}: critic={rec['critic']['convicts']} "
              f"judge={rec['judge']['convicts']} "
              f"defective={rec['reclassified_defective']} "
              f"(tokens {ledger.total})", flush=True)
        return rec

    with concurrent.futures.ThreadPoolExecutor(MAX_IN_FLIGHT) as pool:
        futures = [pool.submit(worker, item) for item in todo]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    adjudications = [done[s["id"]] for s in suspects]
    defective_ids = {a["id"] for a in adjudications
                     if a["reclassified_defective"]}
    n_defective = len(defective_ids)

    # ------------------------------------------------------------------ #
    # Corrected t2 P2/P3 (correction record; t2 report never edited).
    # ------------------------------------------------------------------ #
    table, volumes = corrected_rate_table(defective_ids)

    def rate(rule, pair, battery):
        return table[rule][pair][battery]["rate"]

    p1 = "CONFIRMED" if n_defective >= 3 else "REFUTED"

    fp_corrected = rate("either_suffices", "cross_family", "clean_corrected")
    p2 = "CONFIRMED" if fp_corrected <= 0.40 else "REFUTED"

    catch_gain_pp = round(
        (rate("either_suffices", "cross_family", "unknown_flaw")
         - rate("require_both", "cross_family", "unknown_flaw")) * 100, 2)
    fp_rise_pp = round(
        (rate("either_suffices", "cross_family", "clean_corrected")
         - rate("require_both", "cross_family", "clean_corrected")) * 100, 2)
    net_pp = round(catch_gain_pp - fp_rise_pp, 2)
    p3 = "CONFIRMED" if net_pp > 0 else "REFUTED"

    verdicts = {
        "P1": {"verdict": p1,
               "measured": {"suspects": len(suspects),
                            "reclassified_defective": n_defective,
                            "defective_ids": sorted(defective_ids)},
               "threshold": ">= 3 of 11 reclassified defective"},
        "P2": {"verdict": p2,
               "measured": {
                   "corrected_cross_family_either_suffices_clean_fp":
                       fp_corrected,
                   "original_t2_value": 0.60,
                   "corrected_same_family_either_suffices_clean_fp":
                       rate("either_suffices", "same_family",
                            "clean_corrected")},
               "threshold": "<= 0.40 (t2 rejection line)"},
        "P3": {"verdict": p3,
               "measured": {"unknown_catch_gain_pp_cross_family": catch_gain_pp,
                            "corrected_clean_fp_rise_pp_cross_family": fp_rise_pp,
                            "net_pp": net_pp,
                            "original_t2_net_pp": 0.0},
               "threshold": "net pp strictly > 0"},
    }

    total_tokens = ledger.total
    assert total_tokens <= TOKEN_CEILING, \
        f"t2b spend {total_tokens} over cap {TOKEN_CEILING}"

    caveats = [
        "Both adjudication instruments are themselves fallible LLM judges; "
        "the conjunction rule was chosen for precision over recall, so the "
        "corrected clean set is a LOWER bound on contamination — suspects "
        "acquitted here may still be defective, and un-suspected items were "
        "never re-examined.",
        "The suspect list is conditioned on the t3 zoo (>=5 of 13 seats): "
        "items every seat missed stay in the clean denominator untouched.",
        "The critic (deepseek-v4-flash) shares no family with the t2 judge "
        "pairs, but mistral-large-3:675b's clean FP 0.00 in t3 was measured "
        "on these very 40 items; its acquittals here are therefore "
        "correlated with the original FP measurement (conservative "
        "direction: it under-convicts, shrinking the correction).",
        "All 40 clean items were authored by one adversary model "
        "(deepseek-v4-pro); adjudication verdicts inherit any family "
        "blindness toward its style.",
        "The critic conviction additionally requires a named defect string "
        "of >= 20 chars not equal to 'none' (the prereg's 'specific, "
        "checkable defect' clause, enforced mechanically; defect text is "
        "recorded per item but its checkability was not independently "
        "verified by a third instrument).",
        "Parse failures (none occurred unless recorded per item) count as "
        "acquittal — a failed instrument never convicts.",
        "The original t2 verdict block is never edited; this report is a "
        "correction record that supersedes only the clean-FP rows.",
        "Catch rates on the flawed batteries are recomputed unchanged from "
        "the committed t1 judgments; only the clean denominator shrinks "
        f"(40 -> {volumes['clean_corrected']}).",
    ]

    report = {
        "schema": SCHEMA,
        "prereg": PREREG,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "design": {
            "suspect_rule": f">= {SUSPECT_MIN_FLAGS} of 13 t3 seats flagged",
            "instruments": {
                "argumentative_critic": {
                    "model": CRITIC_MODEL, "temperature": 0.0,
                    "schema": '{"defect_found": bool, "defect": str}',
                    "conviction": "defect_found AND a named, non-trivial "
                                  "defect string"},
                "judge": {
                    "model": JUDGE_MODEL, "temperature": 0.0,
                    "schema": '{"flawed": bool, "kind": str}',
                    "prompt": "identical to zoo seats (scripts/e02_judge.py)"},
            },
            "reclassification_rule": "DEFECTIVE iff BOTH instruments convict "
                                     "(conservative conjunction)",
            "concurrency_max_in_flight": MAX_IN_FLIGHT,
        },
        "suspects": suspects,
        "adjudications": adjudications,
        "reclassified_defective_ids": sorted(defective_ids),
        "corrected_rate_table": {
            "structure": "rule -> pair -> battery; clean_corrected excludes "
                         "reclassified items from the FP denominator; "
                         "clean_original reproduces the t2 rows",
            **table,
        },
        "volumes": volumes,
        "verdicts": verdicts,
        "token_spend": {
            "ledger": ledger.state,
            "total_tokens": total_tokens,
            "ceiling": TOKEN_CEILING,
        },
        "caveats": caveats,
    }
    report_path = RESULTS / "e02_t2b_readjudication_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    index_path = RESULTS / f"INDEX_{dt.date.today().isoformat()}.md"
    index_line = (
        f"\n## E0.2-t2b clean-item re-adjudication "
        f"({dt.date.today().isoformat()})\n\n"
        f"P1 {p1} ({n_defective}/11 suspects reclassified defective, bar 3), "
        f"P2 {p2} (corrected cross-family either-suffices clean FP "
        f"{fp_corrected}, line 0.40, was 0.60), "
        f"P3 {p3} (catch gain {catch_gain_pp:+.1f}pp vs corrected FP rise "
        f"{fp_rise_pp:+.1f}pp, net {net_pp:+.1f}pp). "
        f"{total_tokens} live LLM tokens (cap {TOKEN_CEILING}). "
        f"Prereg: `{PREREG}`. Report: "
        f"`experiments/results/e02_t2b_readjudication_report.json`. "
        f"Original t2 verdicts superseded for clean-FP rows only, never "
        f"edited.\n")
    with index_path.open("a") as fh:
        fh.write(index_line)

    print(json.dumps({
        "verdicts": {k: v["verdict"] for k, v in verdicts.items()},
        "reclassified_defective": sorted(defective_ids),
        "corrected_fp_cross_either": fp_corrected,
        "net_pp": net_pp,
        "tokens": total_tokens,
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
