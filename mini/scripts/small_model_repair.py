#!/usr/bin/env python
"""Repair the 12B's format failures with flash + pro
(experiments/small_model_repair_prereg.yaml).

Corpus = the committed malformed candidates from the 12B roots (zero new
12B tokens). Three arms over the SAME frozen corpus: a deterministic
control (R-mechanical, zero tokens), R-flash, R-pro. Recovery / survival
/ claim-fidelity / cost are recomputed with the committed checks.py — the
same code that judged the originals malformed.

Usage: DEEPSEEK_API_KEY=... python mini/scripts/small_model_repair.py
       python mini/scripts/small_model_repair.py --mock   # offline sanity
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

MINI = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MINI))

from minireason import call as llm  # noqa: E402
from minireason.checks import compile_checks, parse_skeleton, run_checks  # noqa: E402
from minireason.gate import normalize  # noqa: E402
from minireason.log import BlobStore  # noqa: E402
from minireason.loop import Session  # noqa: E402
from pydantic import BaseModel  # noqa: E402

CORPUS_ROOTS = ["runs/nemotron12b/A-12b-stock", "runs/nemotron12b/C-12b-compact"]

SKELETON_SPEC = (
    '{"claim": str, "mechanism": str, "scope": {"covers": [str], '
    '"excludes": [str]}, "forbidden": [{"case": str, "eval": str}], '
    '"prose_notes": str}')


class Repaired(BaseModel):
    claim: str
    mechanism: str
    scope: dict = {}
    forbidden: list = []
    prose_notes: str | None = None


def build_corpus() -> list[dict]:
    items = []
    for root in CORPUS_ROOTS:
        if not Path(root).exists():
            continue
        s = Session(root)
        for aid, _ in s.state.addr:
            c = s.state.artifacts[aid]["content_ref"][len("inline:"):]
            if parse_skeleton(c) is None:
                items.append({"root": Path(root).name, "aid": aid[:12],
                              "original": c})
    return items


def salvage_claim(text: str) -> str:
    """Best-effort claim string out of malformed JSON (for fidelity)."""
    m = re.search(r'"claim"\s*:\s*"(.*?)"\s*,\s*"mechanism"', text, re.S)
    if m:
        return m.group(1)
    m = re.search(r'"claim"\s*:\s*"([^"]{0,300})', text)
    return m.group(1) if m else ""


def mechanical_repair(text: str) -> str:
    """Deterministic control: normalise smart quotes, drop control chars,
    truncate trailing data after the first balanced top-level object. No
    model, no tokens — the floor on how much needs an LLM."""
    t = (text.replace("‘", "'").replace("’", "'")
             .replace("“", '"').replace("”", '"'))
    t = "".join(ch for ch in t if ch >= " " or ch == "\n")
    depth, end, instr, esc = 0, None, False, False
    for i, ch in enumerate(t):
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
            continue
        if ch == '"':
            instr = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    return t[:end] if end else t


def repair_prompt(malformed: str) -> str:
    return (
        "The text below was meant to be a JSON object with this schema:\n"
        f"{SKELETON_SPEC}\n\n"
        "It is MALFORMED (bad JSON syntax and/or non-Python predicate "
        "language). FIX ONLY the formatting:\n"
        "- correct the JSON so it parses (delimiters, quotes, escaping);\n"
        "- each forbidden[].eval must be 'predicate:<PYTHON expression over "
        "the string variable content>' (e.g. predicate:len(content) > 10) or "
        "'rubric:std' — never JavaScript, never a call to an undefined "
        "function;\n"
        "- PRESERVE the claim, mechanism, scope, and prose wording verbatim "
        "wherever legible; do NOT invent new content.\n"
        "Return ONLY the corrected JSON object.\n\n"
        f"MALFORMED:\n{malformed}"
    )


def assess(repaired_text: str, original: str) -> dict:
    sk = parse_skeleton(repaired_text)
    if sk is None:
        return {"recovered": False, "survived": False, "claim_fidelity": None}
    recovered = bool(sk.forbidden)
    survived = False
    if recovered:
        cks = compile_checks(repaired_text)
        survived = not run_checks(repaired_text, cks)
    orig_claim = normalize(salvage_claim(original))
    new_claim = normalize(sk.claim)
    fid = (len(orig_claim & new_claim) / max(1, len(orig_claim | new_claim))
           if orig_claim else None)
    return {"recovered": recovered, "survived": survived,
            "claim_fidelity": round(fid, 4) if fid is not None else None}


def run_model_arm(name: str, endpoint, corpus: list[dict], meter, blobs) -> dict:
    items, aborted = [], None
    for it in corpus:
        try:
            out, _ = llm.call(endpoint, repair_prompt(it["original"]), Repaired,
                              meter, blobs, retry_max=1, role="repairer")
            repaired_text = out.model_dump_json()
        except llm.BudgetExceeded:
            aborted = "budget"
            break
        except (llm.SchemaError, llm.EndpointError) as e:
            items.append({**it, "repair_error": str(e)[:100],
                          "recovered": False, "survived": False,
                          "claim_fidelity": None})
            continue
        items.append({**it, **assess(repaired_text, it["original"])})
    return summarize(name, items, meter.snapshot(), aborted)


def run_mechanical_arm(corpus: list[dict]) -> dict:
    items = [{**it, **assess(mechanical_repair(it["original"]), it["original"])}
             for it in corpus]
    return summarize("R-mechanical", items,
                     {"total": 0, "prompt_tokens": 0, "completion_tokens": 0,
                      "calls": 0, "budget": None}, None)


def summarize(name: str, items: list[dict], tokens: dict, aborted) -> dict:
    n = len(items)
    rec = [x for x in items if x.get("recovered")]
    surv = [x for x in items if x.get("survived")]
    fids = sorted(x["claim_fidelity"] for x in rec if x.get("claim_fidelity") is not None)
    median_fid = fids[len(fids) // 2] if fids else None
    return {
        "arm": name, "processed": n, "aborted": aborted,
        "recovered": len(rec), "survived": len(surv),
        "recovery_rate": round(len(rec) / n, 4) if n else None,
        "survival_rate_of_corpus": round(len(surv) / n, 4) if n else None,
        "survival_rate_of_recovered": round(len(surv) / len(rec), 4) if rec else None,
        "median_claim_fidelity": median_fid,
        "tokens": tokens, "items": items,
    }


def evaluate(corpus_n: int, flash: dict, pro: dict, mech: dict) -> dict:
    out = {}
    if flash.get("aborted"):
        out["P1"] = {"verdict": "UNDECIDED", "reason": f"R-flash aborted: {flash['aborted']}"}
    else:
        rec_ok = flash["recovery_rate"] >= 0.50
        surv_ok = flash["survival_rate_of_corpus"] >= 0.33
        out["P1"] = {"verdict": "CONFIRMED" if rec_ok and surv_ok else "REFUTED",
                     "recovery_clause": rec_ok, "survival_clause": surv_ok,
                     "flash_recovery_rate": flash["recovery_rate"],
                     "flash_survival_of_corpus": flash["survival_rate_of_corpus"]}
    if pro.get("aborted") or flash.get("aborted"):
        out["P2"] = {"verdict": "UNDECIDED", "reason": "an arm aborted"}
    else:
        out["P2"] = {"verdict": "CONFIRMED" if pro["recovery_rate"] >= flash["recovery_rate"]
                     else "REFUTED", "pro": pro["recovery_rate"], "flash": flash["recovery_rate"]}
    mf = flash.get("median_claim_fidelity")
    if flash.get("aborted") or mf is None:
        out["P3"] = {"verdict": "UNDECIDED", "reason": "no recovered items with fidelity"}
    else:
        out["P3"] = {"verdict": "CONFIRMED" if mf >= 0.50 else "REFUTED",
                     "median_claim_fidelity": mf}
    out["P4_control"] = {"mechanical_recovery_rate": mech["recovery_rate"],
                         "note": "context only; >=0.50 => model not needed for the majority"}
    return out


def mock_factory(model):
    def respond(prompt: str) -> str:
        return json.dumps({"claim": "recovered mock claim",
                           "mechanism": "recovered mock mechanism",
                           "scope": {"covers": [], "excludes": []},
                           "forbidden": [{"case": "x", "eval": "predicate:len(content) > 5"}],
                           "prose_notes": ""})
    return llm.MockEndpoint(respond, name="mock", model=model)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--budget", type=int, default=250_000)
    parser.add_argument("--out", default=str(
        MINI.parent / "experiments" / "results" / "small_model_repair_report.json"))
    args = parser.parse_args()

    corpus = build_corpus()
    from collections import Counter
    print(f"corpus: {len(corpus)} malformed 12B candidates "
          f"{dict(Counter(x['root'] for x in corpus))}", flush=True)
    mech = run_mechanical_arm(corpus)
    print(f"R-mechanical (0 tokens): recovered {mech['recovered']}/{len(corpus)}, "
          f"survived {mech['survived']}", flush=True)

    blobs = BlobStore(Path("runs/repair_blobs"))
    if args.mock:
        factory, budget = mock_factory, 50_000
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            print("DEEPSEEK_API_KEY not set", file=sys.stderr)
            return 1
        budget = args.budget

        def factory(model):
            return llm.HttpEndpoint(args.base_url, model, api_key=api_key,
                                    temperature=0.0, max_tokens=1200)

    meter = llm.TokenMeter(budget=budget)
    print("--- R-flash ---", flush=True)
    flash = run_model_arm("R-flash", factory("deepseek-v4-flash"), corpus, meter, blobs)
    print(f"R-flash: recovered {flash['recovered']}/{flash['processed']}, "
          f"survived {flash['survived']}, median_fidelity {flash['median_claim_fidelity']}, "
          f"tokens {flash['tokens']['total']}", flush=True)
    print("--- R-pro ---", flush=True)
    pro = run_model_arm("R-pro", factory("deepseek-v4-pro"), corpus, meter, blobs)
    print(f"R-pro: recovered {pro['recovered']}/{pro['processed']}, "
          f"survived {pro['survived']}, median_fidelity {pro['median_claim_fidelity']}, "
          f"tokens {pro['tokens']['total']}", flush=True)

    report = {
        "prereg": "experiments/small_model_repair_prereg.yaml",
        "mode": "mock" if args.mock else "live",
        "corpus_size": len(corpus),
        "corpus_source": CORPUS_ROOTS,
        "arms": {"R-mechanical": mech, "R-flash": flash, "R-pro": pro},
        "predictions": evaluate(len(corpus), flash, pro, mech),
        "total_deepseek_tokens": meter.total,
    }
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["predictions"], indent=2))
    print(f"total DeepSeek tokens: {meter.total}\nreport -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
