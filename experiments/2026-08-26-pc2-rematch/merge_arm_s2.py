#!/usr/bin/env python3
"""Merge ARM S2's segments into ONE matched arm, and rule on admissibility.

P-C1's ARM S ran in three segments because two workers died mid-run; each
resumption carried the REMAINING budget, so the segments sum to one arm
rather than three. `arm_s_summary.json` records that as `parts` plus a
`segments_note`, and this file reproduces the same shape for P-C2 so the two
tranches' summaries can be read side by side.

IT RULES, IT DOES NOT DECIDE. PREREG §5.4's admissibility rule and §6's
verdict are quoted from the frozen document and applied; nothing here
chooses a threshold.

Usage:  python merge_arm_s2.py
"""
from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

# PREREG.md §5.4 and §6, quoted so a reader can diff code against the frozen
# document rather than trust that they agree.
ADMISSIBILITY_FLOOR = 0.95
VERDICT_RULE = "value is claimed iff best_H2 > best_S2"


def main() -> int:
    tokens = json.loads((HERE / "arm_h2_tokens.json").read_text())
    t_h = int(tokens["T_H"])
    scores = json.loads((HERE / "arm_h2_scores.json").read_text())
    best_h2 = scores.get("best_score")

    rows: list[dict] = []
    parts: list[str] = []
    for directory in sorted(HERE.glob("arm_s2*")):
        ledger = directory / "results.jsonl"
        if not directory.is_dir() or not ledger.exists():
            continue
        segment = [json.loads(line) for line in ledger.open() if line.strip()]
        if not segment:
            continue
        parts.append(directory.name)
        rows.extend(segment)

    # Each segment's counter restarts at 0, so the arm's spend is the SUM of
    # the segments' finals -- never the last one's.
    #
    # A TRANSPORT ERROR row carries no `cumulative_tokens` at all (it has
    # `error` and `tokens: 0`), so the max is taken over the rows that have
    # one. Skipping them is correct rather than convenient: a request that
    # timed out bought nothing, and counting it as spend would shrink the
    # sampler's real budget and flatter the harness.
    t_s = 0
    for part in parts:
        counted = [
            json.loads(line)["cumulative_tokens"]
            for line in (HERE / part / "results.jsonl").open()
            if line.strip() and "cumulative_tokens" in json.loads(line)
        ]
        t_s += max(counted) if counted else 0

    transport_errors = [r for r in rows if "error" in r]
    valid = [r for r in rows if r.get("valid")]
    best = max(valid, key=lambda r: r["score"]) if valid else None
    ratio = round(t_s / t_h, 4) if t_h else 0.0
    admissible = ratio >= ADMISSIBILITY_FLOOR
    best_s2 = best["score"] if best else None

    claims_value = (
        bool(admissible and best_s2 is not None and best_h2 is not None and best_h2 > best_s2)
    )

    summary = {
        "arm": "S2",
        "parts": parts,
        "segments_note": (
            "ARM S2 ran in one or more segments; each resumption carried the "
            "REMAINING budget, so the segments sum to one matched arm rather "
            "than several arms. Same procedure as P-C1's ARM S."
        ),
        "model": "glm-5.2",
        "temperature": 1.0,
        "max_tokens": 32768,
        "token_budget_matched_to_arm_h2": t_h,
        "tokens_spent": t_s,
        "match_ratio": ratio,
        "admissible": admissible,
        "admissibility_rule": (
            f"PREREG §5.4 -- below {ADMISSIBILITY_FLOOR} the comparison is "
            "UNMATCHED and no margin is claimed"
        ),
        "n_samples": len(rows),
        "n_transport_errors": len(transport_errors),
        "transport_error_rate": (
            round(len(transport_errors) / len(rows), 4) if rows else None
        ),
        "transport_errors_note": (
            "A timed-out request buys nothing and is excluded from tokens_spent. "
            "P-C1's ARM S recorded 1 transport error in 54 samples; a materially "
            "higher rate here is an operational fact about this session's network "
            "path, recorded rather than smoothed."
        ),
        "n_valid": len(valid),
        "n_refuted": sum(1 for r in rows if r.get("valid") is False),
        "best_score": best_s2,
        "best_score_exact": best["score_exact"] if best else None,
        "best_sample_index": best["index"] if best else None,
        "valid_scores_desc": sorted((r["score"] for r in valid), reverse=True),
        "VERDICT": {
            "rule": VERDICT_RULE,
            "best_H2": best_h2,
            "best_S2": best_s2,
            "harness_claims_value": claims_value,
            "answer": (
                "value claimed" if claims_value
                else ("UNMATCHED -- no margin claimed" if not admissible
                      else "CURE FAILED")
            ),
        },
    }
    (HERE / "arm_s2_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    with (HERE / "arm_s2_merged.jsonl").open("w") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
