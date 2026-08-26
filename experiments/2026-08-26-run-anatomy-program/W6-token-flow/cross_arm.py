"""W6 — the cross-arm ratio: what one valid candidate cost each arm.

Read-only.  P-C1 ran two arms at a matched budget on the same instance:
ARM H, the harness driving conjecture-criticism over candidates, and ARM S,
the same model at the same budget doing blind repeated one-shot sampling.
The whole apparatus reduces here to one number -- tokens per valid
candidate -- and to a second one the first hides: tokens per candidate that
SURVIVED, which is not the same question and does not have the same answer.

Sources, all committed, none of them prose:

    arm_h_scores.json    per-candidate checker verdicts and harness status
                         for ARM H, produced by that tranche's score_run.py
    arm_s_merged.jsonl   one row per ARM S sample, with its own
                         prompt/completion split
    arm_s_summary.json   ARM S's own rollup
    milestones.json      the pre-registered milestone verdicts
    <root>/TOKEN_ACCOUNTING.json  ARM H's provider token total

The harness status column is re-derived here from a READ-ONLY replay rather
than trusted from the scoring artifact, so the ratio does not rest on
another window's arithmetic.

Writes CROSS_ARM.json beside itself.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(PROGRAM, "..", ".."))
PC1 = os.path.join(REPO, "experiments", "2026-08-25-change-constructive-frontier")
ARM_H_ROOT = os.path.join(PC1, "run")


def ratio(numerator: int, denominator: int) -> dict:
    """A cost ratio that says so when its denominator is zero.

    Zero valid candidates is a real outcome, not a division error, and
    printing "inf" or silently omitting the row would both hide it.
    """
    if denominator == 0:
        return {"value": None, "undefined_because": "denominator is zero",
                "numerator": numerator, "denominator": 0}
    return {"value": round(numerator / denominator, 1),
            "exact": str(Fraction(numerator, denominator)),
            "numerator": numerator, "denominator": denominator}


def main() -> int:
    from deepreason.harness import Harness

    scores = json.load(open(os.path.join(PC1, "arm_h_scores.json")))
    summary = json.load(open(os.path.join(PC1, "arm_s_summary.json")))
    milestones = json.load(open(os.path.join(PC1, "milestones.json")))
    accounting = json.load(open(os.path.join(ARM_H_ROOT, "TOKEN_ACCOUNTING.json")))

    h_tokens = accounting["inquiry_provider_tokens"]
    candidates = scores["candidates"]

    # re-derive the harness's own status for each candidate artifact
    h = Harness(ARM_H_ROOT, read_only=True)
    status = {aid: st.value for aid, st in h.state.status.items()}
    harness_status = Counter(status.get(c["artifact"], "not-in-state") for c in candidates)

    h_valid = sum(1 for c in candidates if c["valid"])
    h_above_floor = sum(1 for c in candidates if c.get("above_floor"))
    h_survivors = sum(1 for c in candidates if c["survivor"])
    h_accepted = sum(1 for c in candidates if c["accepted"])

    s_rows = [json.loads(l) for l in
              open(os.path.join(PC1, "arm_s_merged.jsonl")) if l.strip()]
    s_tokens = sum(r.get("tokens") or 0 for r in s_rows)
    s_prompt = sum(r.get("prompt_tokens") or 0 for r in s_rows)
    s_completion = sum(r.get("completion_tokens") or 0 for r in s_rows)
    s_valid = sum(1 for r in s_rows if r.get("valid"))
    s_above_floor = sum(1 for r in s_rows if r.get("above_floor"))
    s_errors = sum(1 for r in s_rows if r.get("error"))

    # ARM H's prompt/completion split, from the flow table this window built
    flow = [json.loads(l) for l in open(os.path.join(HERE, "FLOW_CALLS.jsonl"))]
    h_rows = [r for r in flow if r["root"].endswith("change-constructive-frontier/run")]
    h_prompt = sum(r["prompt_tokens"] or 0 for r in h_rows)
    h_completion = sum(r["completion_tokens"] or 0 for r in h_rows)
    h_gen = [r for r in h_rows if r["purpose"] == "generation"]
    h_gen_tokens = sum(r["total_tokens"] for r in h_gen)
    h_gen_prompt = sum(r["prompt_tokens"] or 0 for r in h_gen)

    doc = {
        "schema": "run-anatomy.w6.cross-arm.v1",
        "regenerate": "python3 cross_arm.py  (after flow.py)",
        "instance": "13 points in the unit square, maximise the minimum "
                    "triangle area over all 286 triples",
        "budget_match_ratio_S_over_H": summary["match_ratio"],
        "budget_match_admissible_per_prereg": milestones["margin"]["budget_matched_per_S9"],
        "arm_H": {
            "tokens": h_tokens,
            "prompt_tokens": h_prompt,
            "completion_tokens": h_completion,
            "prompt_share": round(h_prompt / h_tokens, 4),
            "provider_calls": len(h_rows),
            "candidates": len(candidates),
            "valid": h_valid,
            "above_floor": h_above_floor,
            "survivors": h_survivors,
            "accepted_in_harness_state": h_accepted,
            "harness_status_of_the_candidate_artifacts": dict(harness_status),
            "refutations_by_code": scores["refutations_by_code"],
            "best_score": scores["best_score"],
            "best_score_exact": scores["best_score_exact"],
            "generation_purpose_tokens": h_gen_tokens,
            "generation_purpose_prompt_tokens": h_gen_prompt,
        },
        "arm_S": {
            "tokens": s_tokens,
            "prompt_tokens": s_prompt,
            "completion_tokens": s_completion,
            "prompt_share": round(s_prompt / s_tokens, 4),
            "samples": len(s_rows),
            "transport_errors": s_errors,
            "valid": s_valid,
            "above_floor": s_above_floor,
            "best_score": summary["best_score"],
            "best_score_exact": summary["best_score_exact"],
            "summary_tokens_spent": summary["tokens_spent"],
            "summary_valid": summary["n_valid"],
        },
        "cost_per": {
            "H_tokens_per_attempted_candidate": ratio(h_tokens, len(candidates)),
            "S_tokens_per_attempted_sample": ratio(s_tokens, len(s_rows)),
            "H_tokens_per_valid_candidate": ratio(h_tokens, h_valid),
            "S_tokens_per_valid_sample": ratio(s_tokens, s_valid),
            "H_tokens_per_above_floor_candidate": ratio(h_tokens, h_above_floor),
            "S_tokens_per_above_floor_sample": ratio(s_tokens, s_above_floor),
            "H_tokens_per_survivor": ratio(h_tokens, h_survivors),
        },
        "the_one_number": {
            "definition": "ARM H tokens per valid candidate divided by ARM S "
                          "tokens per valid sample, at a matched budget. Above "
                          "1 means the apparatus paid more for the same unit "
                          "of checker-confirmed output.",
            "H_per_valid": round(h_tokens / h_valid, 1) if h_valid else None,
            "S_per_valid": round(s_tokens / s_valid, 1) if s_valid else None,
            "overhead_ratio": (
                round((h_tokens / h_valid) / (s_tokens / s_valid), 3)
                if h_valid and s_valid else None
            ),
            "and_the_number_it_hides": (
                "Cost per valid candidate flatters ARM H, because 'valid' "
                "means the checker confirmed the claim, not that the "
                "construction was any good. On the run's own registered "
                "0.005 floor ARM H cleared it "
                f"{h_above_floor} times in {len(candidates)} attempts and ARM S "
                f"{s_above_floor} times in {len(s_rows)}, so ARM H's cost per "
                "construction worth having is not a large number, it is an "
                "undefined one."
            ),
        },
        "prompt_side_comparison": {
            "note": "ARM S poses the same instance in a fixed one-shot prompt; "
                    "ARM H poses it inside an assembled pack. The gap between "
                    "the two mean prompt sizes is the harness's overhead "
                    "signature, per call, in tokens.",
            "S_mean_prompt_tokens_per_sample": round(s_prompt / len(s_rows), 1),
            "H_mean_prompt_tokens_per_generation_call": (
                round(h_gen_prompt / len(h_gen), 1) if h_gen else None),
            "ratio_H_over_S": (
                round((h_gen_prompt / len(h_gen)) / (s_prompt / len(s_rows)), 1)
                if h_gen and s_prompt else None),
        },
    }
    json.dump(doc, open(os.path.join(HERE, "CROSS_ARM.json"), "w"), indent=1)

    n = doc["the_one_number"]
    print(f"ARM H {h_tokens} tokens, {len(candidates)} candidates, {h_valid} valid, "
          f"{h_above_floor} above floor, {h_survivors} survivors")
    print(f"ARM S {s_tokens} tokens, {len(s_rows)} samples, {s_valid} valid, "
          f"{s_above_floor} above floor")
    print(f"tokens per valid: H {n['H_per_valid']} vs S {n['S_per_valid']} "
          f"-> overhead ratio {n['overhead_ratio']}")
    print(f"mean prompt tokens: H generation "
          f"{doc['prompt_side_comparison']['H_mean_prompt_tokens_per_generation_call']} "
          f"vs S {doc['prompt_side_comparison']['S_mean_prompt_tokens_per_sample']} "
          f"-> {doc['prompt_side_comparison']['ratio_H_over_S']}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
