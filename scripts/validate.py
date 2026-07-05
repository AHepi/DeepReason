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
from deepreason.llm.endpoints import (  # noqa: E402
    EndpointError,
    OpenAICompatEndpoint,
    resolve_model,
)

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


def structured(endpoint, prompt, model_cls, meter, retries=2):
    """Bounded schema-repair loop. On exhaustion RAISE — never fabricate a
    default. CritiqueOut.sound defaults True, so silently returning the
    default on a parse failure would score a truncated critic as 'no error
    found', biasing the harness arm and corrupting the study's numbers."""
    error = ""
    for attempt in range(retries + 1):
        meter.check()
        request = prompt if not error else (
            prompt + f"\n\nYour previous output was invalid JSON: {error}\n"
            "Return ONLY a valid JSON object.")
        raw = endpoint.complete(request)
        usage = getattr(endpoint, "last_usage", None) or {
            "prompt_tokens": len(request) // 4, "completion_tokens": len(raw) // 4}
        meter.add(usage)
        try:
            return model_cls.model_validate_json(_extract_json(raw))
        except Exception as e:  # noqa: BLE001 - retry, then surface loudly
            error = str(e)[:300]
    raise RuntimeError(
        f"{model_cls.__name__}: no valid JSON after {retries + 1} attempts: {error}")


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


def _conf_vote(cands, threshold) -> str:
    """Majority over candidates with surprisal <= threshold; empty pool
    falls back to the full pool (same fallback rule as the harness arm).
    Candidates with no surprisal (missing logprobs) are never filtered."""
    kept = [c["answer"] for c in cands
            if c.get("surprisal") is None or c["surprisal"] <= threshold]
    return majority(kept if kept else [c["answer"] for c in cands])


def confidence_analysis(checkpoint: dict) -> dict | None:
    """The pre-registered confidence-filtered arm (d239's design,
    experiments/criticism_decisive_prereg.yaml): tune the surprisal
    threshold on the calibration split (even index of sorted qids), report
    every comparison on the test split (odd index) only."""
    qids = sorted(checkpoint)
    calib = [q for i, q in enumerate(qids) if i % 2 == 0]
    test = [q for i, q in enumerate(qids) if i % 2 == 1]
    if not calib or not test:
        return None

    def is_ok(ans, accept) -> bool:
        return any(normalize(ans) == normalize(a) for a in accept)

    def arm_accuracy(qs, vote_fn) -> float:
        hits = sum(is_ok(vote_fn(checkpoint[q]["candidates"]),
                         checkpoint[q]["accept"]) for q in qs)
        return hits / len(qs)

    grid = sorted({c["surprisal"] for q in calib
                   for c in checkpoint[q]["candidates"]
                   if c.get("surprisal") is not None})
    if not grid:
        return None  # no logprobs captured
    grid.append(grid[-1] + 1.0)  # keep-everything sentinel
    # Max calibration accuracy; ties break to the LARGEST threshold (least
    # aggressive filtering — the conservative optimum).
    threshold, calib_acc = max(
        ((t, arm_accuracy(calib, lambda cs, t=t: _conf_vote(cs, t))) for t in grid),
        key=lambda pair: (pair[1], pair[0]),
    )

    test_cands = [c for q in test for c in checkpoint[q]["candidates"]]
    base_error = sum(not c["correct"] for c in test_cands) / len(test_cands)
    arms = {
        "confidence_filtered": arm_accuracy(
            test, lambda cs: _conf_vote(cs, threshold)),
        "self_consistency": arm_accuracy(
            test, lambda cs: majority([c["answer"] for c in cs])),
        "single": arm_accuracy(test, lambda cs: cs[0]["answer"]),
        "llm_critic": arm_accuracy(
            test, lambda cs: majority(
                [c["answer"] for c in cs if c["critic_sound"] is not False]
                or [c["answer"] for c in cs])),
    }
    fixed = broke = 0
    for q in test:
        cs, accept = checkpoint[q]["candidates"], checkpoint[q]["accept"]
        sc_ok = is_ok(majority([c["answer"] for c in cs]), accept)
        cf_ok = is_ok(_conf_vote(cs, threshold), accept)
        fixed += int(cf_ok and not sc_ok)
        broke += int(sc_ok and not cf_ok)
    right = [c["surprisal"] for q in qids for c in checkpoint[q]["candidates"]
             if c["correct"] and c.get("surprisal") is not None]
    wrong = [c["surprisal"] for q in qids for c in checkpoint[q]["candidates"]
             if not c["correct"] and c.get("surprisal") is not None]
    return {
        "threshold": round(threshold, 6),
        "calibration": {"n": len(calib), "accuracy": round(calib_acc, 3)},
        "test": {"n": len(test),
                 "candidate_base_error": round(base_error, 3),
                 "accuracy": {k: round(v, 3) for k, v in arms.items()},
                 "fixed": fixed, "broke": broke, "net": fixed - broke},
        "surprisal_means": {
            "correct": round(sum(right) / len(right), 4) if right else None,
            "wrong": round(sum(wrong) / len(wrong), 4) if wrong else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--budget", type=int, default=300_000)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--crit-base-url", default=None,
                        help="critic endpoint (default: --base-url); enables a "
                             "cross-provider critic")
    parser.add_argument("--crit-api-key-env", default=None)
    parser.add_argument("--model", default=None,
                        help="force a model id (e.g. deepseek-v4-flash to escape ceiling)")
    parser.add_argument("--crit-model", default=None,
                        help="separate critic model (default: same as --model)")
    parser.add_argument("--tag", default="", help="suffix for report/checkpoint filenames")
    parser.add_argument("--questions", default=None, help="path to a questions json")
    parser.add_argument("--confidence", action="store_true",
                        help="capture per-candidate mean token surprisal (logprobs) "
                             "and score the confidence-filtered arm "
                             "(criticism_decisive_prereg.yaml)")
    parser.add_argument("--gen-only", action="store_true",
                        help="probe mode: generation only, no critic calls")
    parser.add_argument("--temperature", type=float, default=1.0,
                        help="generator temperature (gauntlet: raise to induce errors)")
    parser.add_argument("--max-tokens", type=int, default=1200,
                        help="generator completion cap")
    args = parser.parse_args()
    global OUT, CKPT, QUESTIONS
    if args.questions:
        QUESTIONS = json.loads(Path(args.questions).read_text())
    if args.tag:
        OUT = OUT.with_name(f"validation_report_{args.tag}.json")
        CKPT = CKPT.with_name(f"validation_checkpoint_{args.tag}.json")
    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"{args.api_key_env} not set", file=sys.stderr)
        return 1
    crit_base = args.crit_base_url or args.base_url
    crit_key = os.environ.get(args.crit_api_key_env) if args.crit_api_key_env else api_key
    if not crit_key:
        print(f"{args.crit_api_key_env} not set", file=sys.stderr)
        return 1

    # Resolve models via the shared package helper (auto => v4-pro cascade),
    # so this study and live_run.py pick the same model by the same rule.
    gen_model = resolve_model(args.model or "auto", args.base_url, api_key)
    crit_model = (
        resolve_model(args.crit_model, crit_base, crit_key)
        if args.crit_model else gen_model
    )
    print(f"gen: {gen_model}  crit: {crit_model}  K={args.k}  budget={args.budget}")

    def ep(base, key, model, temp, logprobs=False, max_tokens=1200):
        return OpenAICompatEndpoint(base, model, api_key=key,
                                    temperature=temp, max_tokens=max_tokens, json_mode=True,
                                    request_logprobs=logprobs,
                                    reasoning="none")  # reasoning OFF (prereg)
    gen = ep(args.base_url, api_key, gen_model, args.temperature,
             logprobs=args.confidence, max_tokens=args.max_tokens)
    crit = ep(crit_base, crit_key, crit_model, 0.3)
    meter = TokenMeter(budget=args.budget)

    checkpoint = json.loads(CKPT.read_text()) if CKPT.exists() else {}
    skipped = 0
    try:
        for q in QUESTIONS:
            if q["id"] in checkpoint:
                continue
            try:
                cands = []
                for _ in range(args.k):
                    a = structured(gen, GEN_PROMPT.format(q=q["q"]), AnswerOut, meter)
                    surprisal = getattr(gen, "last_mean_surprisal", None) if args.confidence else None
                    if args.gen_only:
                        sound = None  # probe mode: no critic verdict collected
                    else:
                        verdict = structured(
                            crit, CRIT_PROMPT.format(q=q["q"], reasoning=a.reasoning[:1500],
                                                     answer=a.final_answer), CritiqueOut, meter)
                        sound = verdict.sound
                    cands.append({"answer": a.final_answer,
                                  "correct": correct(a.final_answer, q["accept"]),
                                  "critic_sound": sound,
                                  "surprisal": surprisal})
            except (EndpointError, RuntimeError) as e:
                # A question that persistently fails is SKIPPED (never
                # scored, never fabricated); it stays absent from the
                # checkpoint so a later rerun can resume it. Bounded so a
                # dead provider cannot burn the whole budget on retries.
                skipped += 1
                print(f"{q['id']}: skipped ({str(e)[:100]})")
                if skipped >= 5:
                    print("too many skips — provider unhealthy, stopping")
                    break
                continue
            checkpoint[q["id"]] = {"accept": q["accept"], "candidates": cands}
            CKPT.write_text(json.dumps(checkpoint, indent=2))
            print(f"{q['id']}: {sum(c['correct'] for c in cands)}/{args.k} correct "
                  f"| spent {meter.snapshot()['total']}")
    except TokenBudgetExceeded:
        print("budget exhausted — scoring what completed")

    # -- score the three arms + criticism error-detection --------------- #
    arms = {"single": [0, 0], "self_consistency": [0, 0], "harness": [0, 0]}
    tp = fp = fn = tn = 0  # critic-unsound vs actually-wrong confusion
    fixed = broke = 0
    per_q = {}
    for qid, rec in checkpoint.items():
        cands, accept = rec["candidates"], rec["accept"]
        answers = [c["answer"] for c in cands]
        # critic_sound None (gen-only probe) counts as unflagged.
        survivors = [c["answer"] for c in cands if c["critic_sound"] is not False]
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
            flagged = c["critic_sound"] is False
            tp += int(flagged and wrong)
            fp += int(flagged and not wrong)
            fn += int(not flagged and wrong)
            tn += int(not flagged and not wrong)
        per_q[qid] = {"single": single, "sc": sc, "harness": hv, "accept": accept,
                      "n_correct": sum(c["correct"] for c in cands)}

    confidence = confidence_analysis(checkpoint) if args.confidence else None

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
        "confidence_arm": confidence,
        "tokens": meter.snapshot(), "per_question": per_q}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
    print("\n=== RESULT ===")
    print(json.dumps({k: report[k] for k in
                      ("accuracy", "harness_vs_self_consistency",
                       "criticism_error_detection")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
