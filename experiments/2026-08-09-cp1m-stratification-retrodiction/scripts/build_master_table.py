"""CP1-M: assemble the master table + headline numbers + dual-mode
verdict + stability (flip-rate) report from the four phases' committed
JSONL outputs. Pure aggregation -- no live calls, no new judgments.
"""
from __future__ import annotations

import json
import pathlib

TRANCHE = pathlib.Path("/home/user/DeepReason/experiments/2026-08-09-cp1m-stratification-retrodiction")


def read_jsonl(path: pathlib.Path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def primary(rows):
    return [r for r in rows if r.get("call_variant", "primary") == "primary" or r.get("reading_id", "").endswith(("baseline", "order_swap", "skeptic")) and "repeat" not in r.get("reading_id", "")]


def flip_rate(rows, key_field, outcome_field="outcome"):
    """Given rows containing both a 'primary'/base reading and its
    'repeat' counterpart for a sampled subset, compute the fraction whose
    outcome differs."""
    by_key = {}
    for r in rows:
        by_key.setdefault(r[key_field], {})[r.get("call_variant") or r.get("reading_id")] = r
    flips, total = 0, 0
    for key, variants in by_key.items():
        pairs = [(k, v) for k, v in variants.items() if "repeat" in str(k)]
        for repeat_key, repeat_row in pairs:
            base_key = repeat_key.replace(":repeat", "").replace("repeat", "primary")
            base_row = variants.get(base_key) or variants.get("primary")
            if base_row is None:
                continue
            total += 1
            if base_row.get(outcome_field) != repeat_row.get(outcome_field):
                flips += 1
    return flips, total


def s_mech_summary():
    rows = read_jsonl(TRANCHE / "s_mech_results.jsonl")
    prim = [r for r in rows if r["call_variant"] == "primary"]
    repeat = [r for r in rows if r["call_variant"] == "repeat"]
    by_model = {}
    for r in prim:
        m = r["model"]
        d = by_model.setdefault(m, {"n": 0, "authoring_success": 0, "compile_pass": 0, "execution_ok": 0, "confirmed": 0})
        d["n"] += 1
        authored = r.get("outcome") not in ("authoring_failed", "call_error")
        if authored:
            d["authoring_success"] += 1
        if r.get("outcome") not in ("authoring_failed", "call_error", "overrun_malformed_spec"):
            d["compile_pass"] += 1 if r.get("outcome") != "compile_fail" else 0
        if r.get("outcome") in ("confirmed_a", "confirmed_b", "both_pass", "both_fail"):
            d["execution_ok"] += 1
        if r.get("outcome") in ("confirmed_a", "confirmed_b"):
            d["confirmed"] += 1

    flips, total = flip_rate(rows, key_field="pair_key")
    outcome_counts = {}
    for r in prim:
        outcome_counts[r["outcome"]] = outcome_counts.get(r["outcome"], 0) + 1

    return {
        "population": len(prim),
        "outcome_counts": outcome_counts,
        "by_model": by_model,
        "stability_flip_rate": f"{flips}/{total}" if total else "0/0",
    }


def s_truth_summary():
    rows = read_jsonl(TRANCHE / "s_truth_results.jsonl")
    prim = [r for r in rows if r["call_variant"] == "primary"]
    outcome_counts = {}
    for r in prim:
        outcome_counts[r["outcome"]] = outcome_counts.get(r["outcome"], 0) + 1
    flips, total = flip_rate(rows, key_field="pair_key")
    return {"population": len(prim), "outcome_counts": outcome_counts, "stability_flip_rate": f"{flips}/{total}" if total else "0/0"}


def s_formal_summary():
    rows = read_jsonl(TRANCHE / "s_formal_results.jsonl")
    prim = [r for r in rows if r["call_variant"] == "primary"]
    outcome_counts = {}
    for r in prim:
        outcome_counts[r["outcome"]] = outcome_counts.get(r["outcome"], 0) + 1
    flips, total = flip_rate(rows, key_field="pair_key")
    return {"population": len(prim), "outcome_counts": outcome_counts, "stability_flip_rate": f"{flips}/{total}" if total else "0/0"}


def s_judgment_summary():
    rows = read_jsonl(TRANCHE / "s_judgment_results.jsonl")
    by_pair = {}
    for r in rows:
        by_pair.setdefault(r["pair_key"], []).append(r)
    confirmed, not_confirmed = 0, 0
    convergence_fracs = []
    for pair_key, readings in by_pair.items():
        core = [r for r in readings if "repeat" not in r["reading_id"]]
        agree = sum(1 for r in core if r.get("outcome") == "agrees")
        available = sum(1 for r in core if r.get("outcome") in ("agrees", "disagrees"))
        if available == 0:
            continue
        convergence_fracs.append((agree, available))
        if agree >= 4:
            confirmed += 1
        else:
            not_confirmed += 1
    flips, total = flip_rate(rows, key_field="pair_key", outcome_field="outcome")
    return {
        "population_pairs": len(by_pair),
        "confirmed": confirmed,
        "not_confirmed": not_confirmed,
        "stability_flip_rate": f"{flips}/{total}" if total else "0/0",
    }


def main():
    summary = {
        "s_mech": s_mech_summary(),
        "s_truth": s_truth_summary(),
        "s_formal": s_formal_summary(),
        "s_judgment": s_judgment_summary(),
    }
    (TRANCHE / "master_table_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
