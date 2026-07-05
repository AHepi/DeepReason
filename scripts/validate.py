#!/usr/bin/env python
"""Validation study (experiments/validation_prereg.yaml): does harness-style
criticism extract more reliable knowledge than the raw model?

Three arms on ONE shared pool of K candidate answers per question:
  single           = candidate[0]                 (raw single-shot)
  self_consistency = majority vote over all K      (ensembling, no criticism)
  harness          = majority vote over the K that the critic did NOT refute
                     (the epistemology); falls back to full vote if all refuted

The answer key is held out from every model call; scoring is external.
Per-question results are checkpointed so a container restart resumes.

Usage: DEEPSEEK_API_KEY=... python scripts/validate.py [--k 5] [--budget 300000]
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pydantic import BaseModel  # noqa: E402

from deepreason.llm.adapter import _extract_json  # noqa: E402
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter  # noqa: E402
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = json.loads((ROOT / "experiments" / "validation_questions.json").read_text())
OUT = ROOT / "experiments" / "results" / "validation_report.json"
CKPT = ROOT / "experiments" / "results" / "validation_checkpoint.json"

GEN_PROMPT = (
    "Solve this problem. Think it through, then give ONLY the final answer as a "
    "bare number or single word (no units, no punctuation) in final_answer.\n\n"
    "Return ONLY JSON: {{\"reasoning\": str, \"final_answer\": str}}\n\nProblem: {q}"
)
CRIT_PROMPT = (
    "You are a critic. Here is a problem and one proposed solution. Decide whether "
    "the solution's REASONING contains a definite error that makes its final answer "
    "wrong. Be strict but fair: only mark unsound if you can name a concrete error.\n\n"
    "Return ONLY JSON: {{\"sound\": bool, \"error\": str}}\n\n"
    "Problem: {q}\n\nProposed reasoning: {reasoning}\nProposed final answer: {answer}"
)


class AnswerOut(BaseModel):
    reasoning: str = ""
    final_answer: str = ""


class CritiqueOut(BaseModel):
    sound: bool = True
    error: str = ""


def structured(endpoint, prompt, model_cls, meter):
    meter.check()
    raw = endpoint.complete(prompt)
    usage = getattr(endpoint, "last_usage", None) or {
        "prompt_tokens": len(prompt) // 4, "completion_tokens": len(raw) // 4}
    meter.add(usage)
    try:
        return model_cls.model_validate_json(_extract_json(raw))
    except Exception:
        return model_cls()


_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
          "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
          "ten": "10", "eleven": "11", "twelve": "12"}


# Time-units 'second'/'minute' are deliberately EXCLUDED: 'second' is also
# the ordinal answer to q09, and numeric answers are caught by the regex
# below regardless of a trailing unit — so stripping them would only harm.
_UNITS = ("dollars", "dollar", "cents", "cent", "mph", "feet", "foot",
          "rungs", "rung", "months", "month", "days", "day", "matches",
          "match", "handshakes", "diagonals", "squares", "typists",
          "pages", "place")


def normalize(ans: str) -> str:
    s = str(ans).strip().lower()
    s = s.replace("$", "").replace(",", "").replace("%", "")
    # Drop unit words only as WHOLE tokens (so 'friday' keeps its 'day').
    s = re.sub(r"\b(" + "|".join(_UNITS) + r")\b", " ", s)
    s = s.strip().strip(".").strip()
    s = _WORDS.get(s, s)
    m = re.search(r"-?\d+\.?\d*", s)
    if m:
        try:
            f = float(m.group())
            return str(int(f)) if f == int(f) else str(f)
        except ValueError:
            pass
    return s


def correct(ans: str, accept: list[str]) -> bool:
    na = normalize(ans)
    return any(na == normalize(a) for a in accept)


def majority(answers: list[str]) -> str:
    if not answers:
        return ""
    norm = [normalize(a) for a in answers]
    return Counter(norm).most_common(1)[0][0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--budget", type=int, default=300_000)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--model", default=None,
                        help="force a model id (e.g. deepseek-v4-flash to escape ceiling)")
    parser.add_argument("--crit-model", default=None,
                        help="separate critic model (default: same as --model)")
    parser.add_argument("--tag", default="", help="suffix for report/checkpoint filenames")
    args = parser.parse_args()
    global OUT, CKPT
    if args.tag:
        OUT = OUT.with_name(f"validation_report_{args.tag}.json")
        CKPT = CKPT.with_name(f"validation_checkpoint_{args.tag}.json")
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY not set", file=sys.stderr)
        return 1

    import urllib.request
    req = urllib.request.Request(args.base_url.rstrip("/") + "/models",
                                 headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        models = [m["id"] for m in json.load(r).get("data", [])]
    gen_model = args.model or next((m for m in models if "v4" in m and "pro" in m), sorted(models)[0])
    crit_model = args.crit_model or gen_model
    print(f"gen: {gen_model}  crit: {crit_model}  K={args.k}  budget={args.budget}")

    def ep(model, temp):
        return OpenAICompatEndpoint(args.base_url, model, api_key=api_key,
                                    temperature=temp, max_tokens=1200, json_mode=True,
                                    reasoning="none")  # reasoning OFF (prereg)
    gen, crit = ep(gen_model, 1.0), ep(crit_model, 0.3)
    meter = TokenMeter(budget=args.budget)

    checkpoint = json.loads(CKPT.read_text()) if CKPT.exists() else {}
    try:
        for q in QUESTIONS:
            if q["id"] in checkpoint:
                continue
            cands = []
            for _ in range(args.k):
                a = structured(gen, GEN_PROMPT.format(q=q["q"]), AnswerOut, meter)
                verdict = structured(
                    crit, CRIT_PROMPT.format(q=q["q"], reasoning=a.reasoning[:1500],
                                             answer=a.final_answer), CritiqueOut, meter)
                cands.append({"answer": a.final_answer,
                              "correct": correct(a.final_answer, q["accept"]),
                              "critic_sound": verdict.sound})
            checkpoint[q["id"]] = {"accept": q["accept"], "candidates": cands}
            CKPT.write_text(json.dumps(checkpoint, indent=2))
            print(f"{q['id']}: {sum(c['correct'] for c in cands)}/{args.k} correct "
                  f"| spent {meter.snapshot()['total']}")
    except TokenBudgetExceeded:
        print("budget exhausted — scoring what completed")
    except EndpointError as e:
        print(f"endpoint error: {e} — scoring what completed")

    # -- score the three arms + criticism error-detection --------------- #
    arms = {"single": [0, 0], "self_consistency": [0, 0], "harness": [0, 0]}
    tp = fp = fn = tn = 0  # critic-unsound vs actually-wrong confusion
    fixed = broke = 0
    per_q = {}
    for qid, rec in checkpoint.items():
        cands, accept = rec["candidates"], rec["accept"]
        answers = [c["answer"] for c in cands]
        survivors = [c["answer"] for c in cands if c["critic_sound"]]
        single = normalize(answers[0])
        sc = majority(answers)
        hv = majority(survivors) if survivors else sc
        for name, ans in (("single", single), ("self_consistency", sc), ("harness", hv)):
            ok = any(normalize(ans) == normalize(a) for a in accept)
            arms[name][0] += int(ok)
            arms[name][1] += 1
        sc_ok = any(sc == normalize(a) for a in accept)
        hv_ok = any(hv == normalize(a) for a in accept)
        if not sc_ok and hv_ok:
            fixed += 1
        if sc_ok and not hv_ok:
            broke += 1
        for c in cands:
            wrong = not c["correct"]
            flagged = not c["critic_sound"]
            tp += int(flagged and wrong)
            fp += int(flagged and not wrong)
            fn += int(not flagged and wrong)
            tn += int(not flagged and not wrong)
        per_q[qid] = {"single": single, "sc": sc, "harness": hv, "accept": accept,
                      "n_correct": sum(c["correct"] for c in cands)}

    n_cand = tp + fp + fn + tn
    base_wrong = (tp + fn) / n_cand if n_cand else 0
    report = {
        "experiment": "validation-does-criticism-help",
        "gen_model": gen_model, "crit_model": crit_model, "k": args.k,
        "n_questions": len(checkpoint),
        "accuracy": {k: round(v[0] / v[1], 3) if v[1] else None for k, v in arms.items()},
        "harness_vs_self_consistency": {"fixed": fixed, "broke": broke, "net": fixed - broke},
        "criticism_error_detection": {
            "candidates": n_cand, "base_rate_wrong": round(base_wrong, 3),
            "precision": round(tp / (tp + fp), 3) if (tp + fp) else None,
            "recall": round(tp / (tp + fn), 3) if (tp + fn) else None,
            "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn}},
        "tokens": meter.snapshot(), "per_question": per_q}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print("\n=== RESULT ===")
    print(json.dumps({k: report[k] for k in
                      ("accuracy", "harness_vs_self_consistency",
                       "criticism_error_detection")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
