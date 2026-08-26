"""W6 — P-C1 ARM H: a line-item post-mortem of 702 789 tokens.

Read-only.  ARM H lost its matched-budget race against blind sampling by a
factor of 33 on best score.  This instrument asks the narrower question the
loss makes interesting: WHAT DID THE 702 789 TOKENS BUY, line by line.

The line items are cut three ways, all of them record-native:

    by the PROBLEM the call was posed against, read out of the rendered
    prompt's own `PROBLEM`/`PROBLEM CONTEXT` line and cross-checked against
    the run's problem objects -- this is the line the loss turns on;
    by purpose and call kind, from FLOW_CALLS.jsonl;
    by what the call bought, from the same table's fate class.

Writes PC1_POSTMORTEM.json beside itself.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(PROGRAM, "..", ".."))
ROOT = "experiments/2026-08-25-change-constructive-frontier/run"
PC1 = os.path.join(REPO, "experiments", "2026-08-25-change-constructive-frontier")

# `PROBLEM <id>` on the packed contracts, `PROBLEM CONTEXT (<id>)` on the
# batch critic.  A repair re-ask carries no pack and therefore no problem
# line; it is reported as such rather than assigned to a neighbour.
PROBLEM_LINE = re.compile(r"^PROBLEM(?: CONTEXT)? \(?([^)\n]+)\)?", re.M)


def bucket(rows: list[dict], key) -> dict:
    out: dict = {}
    for r in rows:
        k = key(r)
        a = out.setdefault(k, {"calls": 0, "tokens": 0, "prompt_tokens": 0,
                               "completion_tokens": 0})
        a["calls"] += 1
        a["tokens"] += r["total_tokens"]
        a["prompt_tokens"] += r["prompt_tokens"] or 0
        a["completion_tokens"] += r["completion_tokens"] or 0
    total = sum(a["tokens"] for a in out.values()) or 1
    for a in out.values():
        a["share"] = round(a["tokens"] / total, 4)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["tokens"]))


def main() -> int:
    rows = [json.loads(l) for l in open(os.path.join(HERE, "FLOW_CALLS.jsonl"))
            if json.loads(l)["root"] == ROOT]
    rows.sort(key=lambda r: r["seq"])
    abs_root = os.path.join(REPO, ROOT)

    prompt_ref = {}
    spawns = []
    for line in open(os.path.join(abs_root, "log.jsonl")):
        e = json.loads(line)
        if e.get("llm"):
            prompt_ref[e["seq"]] = e["llm"]["prompt_ref"]
        if e["rule"] == "Spawn":
            spawns.append({"seq": e["seq"], "outputs": e["outputs"]})

    problems = {}
    pdir = os.path.join(abs_root, "objects", "problem")
    for f in sorted(os.listdir(pdir)):
        d = json.load(open(os.path.join(pdir, f)))["data"]
        problems[d["id"]] = {"description": d.get("description"),
                             "provenance": d.get("provenance")}

    seed = next(p for p in problems if p.startswith("question-"))

    for r in rows:
        ref = prompt_ref[r["seq"]]
        with open(os.path.join(abs_root, "blobs", ref[:2], ref),
                  encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        m = PROBLEM_LINE.search(text)
        r["problem"] = m.group(1).strip() if m else "no-problem-line-in-prompt"
        r["on_seed_question"] = r["problem"] == seed

    unknown = sorted({r["problem"] for r in rows
                      if r["problem"] not in problems
                      and r["problem"] != "no-problem-line-in-prompt"})

    seed_rows = [r for r in rows if r["on_seed_question"]]
    other = [r for r in rows if not r["on_seed_question"]
             and r["problem"] != "no-problem-line-in-prompt"]
    norow = [r for r in rows if r["problem"] == "no-problem-line-in-prompt"]

    total = sum(r["total_tokens"] for r in rows)
    spawn_seq = next((s["seq"] for s in spawns if "audit:ritual" in s["outputs"]), None)
    before = [r for r in rows if spawn_seq is not None and r["seq"] < spawn_seq]
    after = [r for r in rows if spawn_seq is not None and r["seq"] > spawn_seq]

    scores = json.load(open(os.path.join(PC1, "arm_h_scores.json")))
    summary = json.load(open(os.path.join(PC1, "arm_s_summary.json")))

    doc = {
        "schema": "run-anatomy.w6.pc1-postmortem.v1",
        "regenerate": "python3 pc1_postmortem.py  (after flow.py)",
        "root": ROOT,
        "total_tokens": total,
        "calls": len(rows),
        "seed_question_id": seed,
        "problems_in_the_run": problems,
        "problem_ids_seen_in_prompts_but_not_in_objects": unknown,
        "the_line_that_matters": {
            "question": "how much of the budget was spent on the question the "
                        "operator asked?",
            "on_the_seed_question": {
                "calls": len(seed_rows),
                "tokens": sum(r["total_tokens"] for r in seed_rows),
                "share": round(sum(r["total_tokens"] for r in seed_rows) / total, 4),
            },
            "on_problems_the_run_spawned_for_itself": {
                "calls": len(other),
                "tokens": sum(r["total_tokens"] for r in other),
                "share": round(sum(r["total_tokens"] for r in other) / total, 4),
                "problem_ids": sorted({r["problem"] for r in other}),
            },
            "on_repair_re_asks_carrying_no_pack_and_so_no_problem_line": {
                "calls": len(norow),
                "tokens": sum(r["total_tokens"] for r in norow),
                "share": round(sum(r["total_tokens"] for r in norow) / total, 4),
            },
            "arm_S_share_on_the_seed_question": 1.0,
            "arm_S_note": "ARM S poses the instance and nothing else; it has "
                          "no mechanism for spawning a sub-problem, so its "
                          "whole budget is on the question by construction.",
        },
        "the_spawn": {
            "audit_ritual_spawned_at_log_seq": spawn_seq,
            "log_events_in_root": sum(1 for _ in open(os.path.join(abs_root, "log.jsonl"))),
            "before_the_spawn": {
                "calls": len(before),
                "tokens": sum(r["total_tokens"] for r in before),
                "seed_share": round(
                    sum(r["total_tokens"] for r in before if r["on_seed_question"])
                    / max(1, sum(r["total_tokens"] for r in before)), 4),
            },
            "after_the_spawn": {
                "calls": len(after),
                "tokens": sum(r["total_tokens"] for r in after),
                "seed_share": round(
                    sum(r["total_tokens"] for r in after if r["on_seed_question"])
                    / max(1, sum(r["total_tokens"] for r in after)), 4),
            },
            "spawn_provenance": problems.get("audit:ritual", {}).get("provenance"),
        },
        "by_problem": bucket(rows, lambda r: r["problem"]),
        "by_problem_and_purpose": bucket(
            rows, lambda r: f"{r['problem']} | {r['purpose_detail']}"),
        "by_purpose_detail": bucket(rows, lambda r: r["purpose_detail"]),
        "by_call_kind": bucket(rows, lambda r: r["call_kind"]),
        "by_fate_class": bucket(rows, lambda r: r["fate_class"]),
        "by_cycle": bucket(rows, lambda r: f"cycle-{r['cycle']:02d}"),
        "what_it_all_bought": {
            "candidates_attempted": scores["n_candidates"],
            "checker_valid": scores["n_valid"],
            "checker_refuted": scores["n_refuted"],
            "refutations_by_code": scores["refutations_by_code"],
            "valid_but_below_the_registered_floor": scores["n_below_floor"],
            "above_the_registered_floor": 0,
            "survivors": scores["survivors_generative_only"],
            "best_score": scores["best_score"],
            "arm_S_best_score": summary["best_score"],
            "tokens_per_candidate_attempted": round(total / scores["n_candidates"], 1),
            "seed_question_tokens_per_candidate_attempted": round(
                sum(r["total_tokens"] for r in seed_rows) / scores["n_candidates"], 1),
        },
    }
    json.dump(doc, open(os.path.join(HERE, "PC1_POSTMORTEM.json"), "w"), indent=1)

    L = doc["the_line_that_matters"]
    print(f"ARM H {total} tokens over {len(rows)} calls")
    print(f"  on the seed question:        {L['on_the_seed_question']['tokens']:7} "
          f"({L['on_the_seed_question']['share']:.1%}) in {L['on_the_seed_question']['calls']} calls")
    print(f"  on self-spawned problems:    "
          f"{L['on_problems_the_run_spawned_for_itself']['tokens']:7} "
          f"({L['on_problems_the_run_spawned_for_itself']['share']:.1%}) in "
          f"{L['on_problems_the_run_spawned_for_itself']['calls']} calls "
          f"-> {L['on_problems_the_run_spawned_for_itself']['problem_ids']}")
    print(f"  on repair re-asks (no pack): "
          f"{L['on_repair_re_asks_carrying_no_pack_and_so_no_problem_line']['tokens']:7} "
          f"({L['on_repair_re_asks_carrying_no_pack_and_so_no_problem_line']['share']:.1%})")
    S = doc["the_spawn"]
    print(f"  audit:ritual spawned at log seq {S['audit_ritual_spawned_at_log_seq']} "
          f"of {S['log_events_in_root']}")
    print(f"    before: {S['before_the_spawn']['tokens']} tokens, "
          f"{S['before_the_spawn']['seed_share']:.1%} on the seed question")
    print(f"    after:  {S['after_the_spawn']['tokens']} tokens, "
          f"{S['after_the_spawn']['seed_share']:.1%} on the seed question")
    if unknown:
        print(f"  NOTE problem ids in prompts with no problem object: {unknown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
