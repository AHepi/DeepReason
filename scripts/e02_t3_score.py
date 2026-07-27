#!/usr/bin/env python
"""E0.2 tranche 3 — scoring (pre-registered:
experiments/e02_t3_judge_zoo_prereg.yaml).

Consumes experiments/e02_t3_run/judgments.jsonl (append-only checkpoint
written by scripts/e02_t3_run.py) and produces:

  - per-seat metric table: known catch, unknown catch, clean FP rate,
    generalization ratio (unknown/known);
  - mechanical verdicts P1-P4 against the prereg literals;
  - the exploratory observables (explicitly NON-verdict-bearing): wire
    discipline, latency/cost, response-length vs verdict point-biserial,
    inter-seat agreement matrix + family clustering summary,
    deepseek-seats-on-deepseek-authored flaws, per-flaw-class catch rates;
  - experiments/results/e02_t3_judge_zoo_report.json
    (schema deepreason-e02-t3-report-v1) and an index line appended to
    experiments/results/INDEX_2026-07-13.md.

Zero LLM tokens. Usage: python scripts/e02_t3_score.py [--no-index]
"""

import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUN_DIR = REPO / "experiments/e02_t3_run"
PREREG = "experiments/e02_t3_judge_zoo_prereg.yaml"
REPORT = REPO / "experiments/results/e02_t3_judge_zoo_report.json"
INDEX = REPO / "experiments/results/INDEX_2026-07-13.md"

KNOWN = REPO / "experiments/e02_t1_items/known_flaws.json"
UNKNOWN = REPO / "experiments/e02_t1_items/unknown_flaws.json"
CLEAN = REPO / "experiments/e02_t2_items/clean_items.json"

FAMILY = {  # model -> family, for the clustering summary
    "gpt-oss:120b": "gpt-oss", "qwen3-coder:480b": "qwen",
    "qwen3.5:397b": "qwen", "deepseek-v4-flash": "deepseek",
    "deepseek-v4-pro": "deepseek", "glm-5.2": "glm", "kimi-k2.6": "kimi",
    "minimax-m2.7": "minimax", "mistral-large-3:675b": "mistral",
    "nemotron-3-ultra": "nemotron", "gemma3:27b": "gemma",
}


def load() -> tuple[dict, dict[str, list[dict]]]:
    items = {}
    for path in (KNOWN, UNKNOWN, CLEAN):
        for it in json.loads(path.read_text()):
            items[it["id"]] = it
    by_seat: dict[str, list[dict]] = {}
    for line in (RUN_DIR / "judgments.jsonl").read_text().splitlines():
        rec = json.loads(line)
        by_seat.setdefault(rec["seat"], []).append(rec)
    # Deduplicate on (item, seat), keeping the first (append-only resume can
    # in principle double-write on a crash mid-append).
    for seat, recs in by_seat.items():
        seen, uniq = set(), []
        for rec in recs:
            if rec["item_id"] not in seen:
                seen.add(rec["item_id"])
                uniq.append(rec)
        by_seat[seat] = uniq
    return items, by_seat


def rate(recs: list[dict], battery: str) -> float:
    sub = [r for r in recs if r["sub_battery"] == battery]
    if not sub:
        return float("nan")
    return sum(1 for r in sub if r.get("flawed") is True) / len(sub)


def seat_metrics(recs: list[dict]) -> dict:
    known = rate(recs, "known_flaw")
    unknown = rate(recs, "unknown_flaw")
    clean_fp = rate(recs, "clean")
    ratio = (unknown / known) if known > 0 else None
    return {
        "n_judgments": len(recs),
        "known_catch": round(known, 4),
        "unknown_catch": round(unknown, 4),
        "clean_fp": round(clean_fp, 4),
        "generalization_ratio": round(ratio, 4) if ratio is not None else None,
    }


def point_biserial(xs: list[float], flags: list[bool]) -> float | None:
    """Pearson r between a binary flag and a continuous variable."""
    if len(xs) < 3 or len(set(flags)) < 2 or len(set(xs)) < 2:
        return None
    mx = statistics.fmean(xs)
    mf = statistics.fmean(1.0 if f else 0.0 for f in flags)
    num = sum((x - mx) * ((1.0 if f else 0.0) - mf)
              for x, f in zip(xs, flags))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs)
                    * sum(((1.0 if f else 0.0) - mf) ** 2 for f in flags))
    return round(num / den, 4) if den else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-index", action="store_true")
    args = parser.parse_args()
    items, by_seat = load()
    roster_probe = json.loads((RUN_DIR / "roster_probe.json").read_text())
    ledger = json.loads((RUN_DIR / "token_usage.json").read_text())

    zoo_seats = sorted(s for s in by_seat if s.startswith("zoo:"))
    rlow_seats = sorted(s for s in by_seat if s.startswith("rlow:"))
    all_seats = zoo_seats + rlow_seats
    incomplete = {s: len(by_seat[s]) for s in all_seats
                  if len(by_seat[s]) != 120}

    table = {s: seat_metrics(by_seat[s]) for s in all_seats}

    # ------------------------------------------------------------------ #
    # Verdicts against the prereg literals. "Seats" = the zoo roster at
    # reasoning none (the reasoning arm is its own arm, P4 only).
    # ------------------------------------------------------------------ #
    ratios = [table[s]["generalization_ratio"] for s in zoo_seats
              if table[s]["generalization_ratio"] is not None]
    p1_median = round(statistics.median(ratios), 4) if ratios else None
    p1 = {
        "statement": "median unknown/known catch ratio across all seats < 0.8",
        "median_generalization_ratio": p1_median,
        "n_seats": len(ratios),
        "threshold": 0.8,
        "verdict": ("CONFIRMED" if p1_median is not None and p1_median < 0.8
                    else "REFUTED"),
    }

    fps = [table[s]["clean_fp"] for s in zoo_seats]
    p2_span = round(max(fps) - min(fps), 4)
    p2 = {
        "statement": "clean FP rates span >= 30 percentage points across seats",
        "clean_fp_min": min(fps), "clean_fp_max": max(fps),
        "span_pp": round(p2_span * 100, 2),
        "threshold_pp": 30.0,
        "verdict": "CONFIRMED" if p2_span >= 0.30 else "REFUTED",
    }

    pareto = {s: table[s] for s in zoo_seats
              if table[s]["unknown_catch"] >= 0.5
              and table[s]["clean_fp"] <= 0.15}
    p3 = {
        "statement": "at least one seat reaches unknown catch >= 0.5 "
                     "AND clean FP <= 0.15",
        "qualifying_seats": {s: {"unknown_catch": m["unknown_catch"],
                                 "clean_fp": m["clean_fp"]}
                             for s, m in pareto.items()},
        "verdict": "CONFIRMED" if pareto else "REFUTED",
    }

    p4_rows = {}
    p4_hits = 0
    for model in roster_probe["reasoning_arm"]:
        base, arm = f"zoo:{model}", f"rlow:{model}"
        if base not in table or arm not in table:
            p4_rows[model] = {"error": "missing seat data"}
            continue
        lift = round(table[arm]["unknown_catch"]
                     - table[base]["unknown_catch"], 4)
        fp_rise = round(table[arm]["clean_fp"] - table[base]["clean_fp"], 4)
        hit = lift >= 0.10 and fp_rise <= lift
        p4_hits += hit
        p4_rows[model] = {
            "unknown_catch_none": table[base]["unknown_catch"],
            "unknown_catch_low": table[arm]["unknown_catch"],
            "unknown_lift_pp": round(lift * 100, 2),
            "clean_fp_none": table[base]["clean_fp"],
            "clean_fp_low": table[arm]["clean_fp"],
            "clean_fp_rise_pp": round(fp_rise * 100, 2),
            "counts": hit,
        }
    p4 = {
        "statement": "reasoning low lifts unknown catch by >= 10pp on >= 2 "
                     "of 3 arm models without a larger clean-FP rise",
        "rule": "counts iff unknown_lift >= 10pp AND clean_fp_rise <= "
                "unknown_lift",
        "per_model": p4_rows,
        "models_counting": p4_hits,
        "threshold_models": 2,
        "verdict": "CONFIRMED" if p4_hits >= 2 else "REFUTED",
    }

    # ------------------------------------------------------------------ #
    # Exploratory observables — NON-verdict-bearing.
    # ------------------------------------------------------------------ #
    wire = {}
    for s in all_seats:
        recs = by_seat[s]
        wire[s] = {
            "parse_failures": sum(1 for r in recs if r.get("parse_failure")),
            "json_retries": sum(r.get("json_retries", 0) for r in recs),
            "transport_retries": sum(r.get("transport_retries", 0)
                                     for r in recs),
        }

    latency_cost = {}
    for s in all_seats:
        recs = [r for r in by_seat[s] if r.get("latency_s") is not None]
        lats = sorted(r["latency_s"] for r in recs)
        comp = [r["completion_tokens"] for r in recs
                if r.get("completion_tokens") is not None]
        prom = [r["prompt_tokens"] for r in recs
                if r.get("prompt_tokens") is not None]
        phase = ledger["phases"].get(f"judge-{s}", {})
        latency_cost[s] = {
            "latency_median_s": round(statistics.median(lats), 3) if lats else None,
            "latency_p90_s": round(lats[int(0.9 * (len(lats) - 1))], 3) if lats else None,
            "mean_prompt_tokens": round(statistics.fmean(prom), 1) if prom else None,
            "mean_completion_tokens": round(statistics.fmean(comp), 1) if comp else None,
            "phase_total_tokens": (phase.get("prompt_tokens", 0)
                                   + phase.get("completion_tokens", 0)),
            "tokens_per_120_items": (phase.get("prompt_tokens", 0)
                                     + phase.get("completion_tokens", 0)),
        }

    length_verdict = {}
    for s in all_seats:
        recs = [r for r in by_seat[s]
                if r.get("response_chars") is not None
                and isinstance(r.get("flawed"), bool)
                and not r.get("parse_failure")]
        length_verdict[s] = {
            "r_response_chars": point_biserial(
                [float(r["response_chars"]) for r in recs],
                [r["flawed"] for r in recs]),
            "r_completion_tokens": point_biserial(
                [float(r["completion_tokens"]) for r in recs
                 if r.get("completion_tokens") is not None],
                [r["flawed"] for r in recs
                 if r.get("completion_tokens") is not None]),
        }
    pooled = [r for s in all_seats for r in by_seat[s]
              if r.get("completion_tokens") is not None
              and isinstance(r.get("flawed"), bool)
              and not r.get("parse_failure")]
    length_verdict["POOLED_all_seats"] = {
        "r_response_chars": point_biserial(
            [float(r["response_chars"]) for r in pooled],
            [r["flawed"] for r in pooled]),
        "r_completion_tokens": point_biserial(
            [float(r["completion_tokens"]) for r in pooled],
            [r["flawed"] for r in pooled]),
    }

    # Inter-seat agreement (zoo seats, verdict on all 120 items).
    verdicts = {s: {r["item_id"]: bool(r.get("flawed"))
                    for r in by_seat[s]} for s in all_seats}
    agreement: dict[str, dict[str, float]] = {}
    for a in zoo_seats:
        agreement[a] = {}
        for b in zoo_seats:
            common = set(verdicts[a]) & set(verdicts[b])
            agreement[a][b] = round(
                sum(verdicts[a][i] == verdicts[b][i] for i in common)
                / len(common), 4) if common else None

    within, across = [], []
    for i, a in enumerate(zoo_seats):
        for b in zoo_seats[i + 1:]:
            fa = FAMILY.get(a.split(":", 1)[1], a)
            fb = FAMILY.get(b.split(":", 1)[1], b)
            (within if fa == fb else across).append(agreement[a][b])
    pairs = [(a, b, agreement[a][b]) for i, a in enumerate(zoo_seats)
             for b in zoo_seats[i + 1:] if agreement[a][b] is not None]
    clustering = {
        "same_family_pairs": len(within),
        "same_family_mean_agreement": (round(statistics.fmean(within), 4)
                                       if within else None),
        "cross_family_pairs": len(across),
        "cross_family_mean_agreement": (round(statistics.fmean(across), 4)
                                        if across else None),
        "most_agreeing_pair": (max(pairs, key=lambda t: t[2])
                               if pairs else None),
        "least_agreeing_pair": (min(pairs, key=lambda t: t[2])
                                if pairs else None),
    }

    # Deepseek seats on deepseek-authored flaws (all 40 unknown-flaw items
    # were generated by deepseek-v4-pro; clean items too).
    ds_seats = [s for s in zoo_seats
                if FAMILY.get(s.split(":", 1)[1]) == "deepseek"]
    other_seats = [s for s in zoo_seats if s not in ds_seats]
    def _mean(vals):
        vals = [v for v in vals if v is not None and not math.isnan(v)]
        return round(statistics.fmean(vals), 4) if vals else None

    self_family = {
        "note": "all 40 unknown-flaw items were authored by deepseek-v4-pro",
        "deepseek_seats": {s: table[s]["unknown_catch"] for s in ds_seats},
        "deepseek_mean_unknown_catch": _mean(
            table[s]["unknown_catch"] for s in ds_seats),
        "other_seats_mean_unknown_catch": _mean(
            table[s]["unknown_catch"] for s in other_seats),
    }

    # Per-flaw-class catch rates across seats.
    flaw_class = {}
    classes: dict[str, list[str]] = {}
    for it in items.values():
        if "flaw_class" in it:
            classes.setdefault(it["flaw_class"], []).append(it["id"])
    for cls, ids in sorted(classes.items()):
        per_seat = {}
        for s in zoo_seats:
            v = [verdicts[s][i] for i in ids if i in verdicts[s]]
            per_seat[s] = round(sum(v) / len(v), 4) if v else None
        vals = [v for v in per_seat.values() if v is not None]
        covered = {s: v for s, v in per_seat.items() if v is not None}
        battery = ("known" if ids[0].startswith("kf") else "unknown")
        flaw_class[cls] = {
            "battery": battery, "n_items": len(ids),
            "mean_catch_across_seats": (round(statistics.fmean(vals), 4)
                                        if vals else None),
            "min_seat": (min(covered, key=covered.get) if covered else None),
            "min_catch": min(vals) if vals else None,
            "max_seat": (max(covered, key=covered.get) if covered else None),
            "max_catch": max(vals) if vals else None,
            "per_seat": per_seat,
        }

    report = {
        "schema": "deepreason-e02-t3-report-v1",
        "prereg": PREREG,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "design": {
            "corpus": "frozen tranche-1/2 items: 40 known-flaw + 40 "
                      "unknown-flaw (experiments/e02_t1_items/) + 40 clean "
                      "(experiments/e02_t2_items/clean_items.json); zero "
                      "generation spend",
            "seats": "single seats, temperature 0, reasoning none, judged "
                     "individually; strict-JSON verdict prompt identical to "
                     "tranches 1/2",
            "reasoning_arm": "deepseek-v4-flash, gpt-oss:120b, kimi-k2.6 "
                             "re-judge all 120 items at reasoning low",
            "aggregation": "none baked into collection; raw per-seat "
                           "verdicts only",
        },
        "roster": {
            "requested": roster_probe["roster_requested"],
            "as_run": roster_probe["roster_as_run"],
            "substitutions": roster_probe["substitutions"],
            "probe": roster_probe["probed_at"],
        },
        "volumes": {
            "items": len(items),
            "zoo_seats": len(zoo_seats),
            "reasoning_arm_seats": len(rlow_seats),
            "judgments": sum(len(v) for v in by_seat.values()),
            "incomplete_seats": incomplete,
        },
        "per_seat_table": table,
        "verdicts": {"P1": p1, "P2": p2, "P3": p3, "P4": p4},
        "exploratory": {
            "NON_VERDICT_BEARING": True,
            "note": "recorded per prereg exploratory_observables; hypothesis "
                    "generation only, no verdict rests on anything below",
            "wire_discipline": wire,
            "latency_cost": latency_cost,
            "response_length_vs_verdict_point_biserial": length_verdict,
            "inter_seat_agreement": agreement,
            "family_clustering": clustering,
            "deepseek_self_family": self_family,
            "per_flaw_class": flaw_class,
        },
        "token_spend": {
            "prompt_tokens": ledger["prompt_tokens"],
            "completion_tokens": ledger["completion_tokens"],
            "total": ledger["prompt_tokens"] + ledger["completion_tokens"],
            "calls": ledger["calls"],
            "ceiling": 1_500_000,
        },
        "caveats": [
            "40 items per cell; per-seat rates have ~±0.08 binomial SE near "
            "0.5",
            "all unknown-flaw and clean items were authored by a single "
            "adversary (deepseek-v4-pro); family effects on those batteries "
            "are confounded with the author family",
            "parse failures count as flawed=false (conservative against the "
            "judge), as in tranches 1/2",
            "P1's 'all seats' is read as the 11 zoo seats at reasoning "
            "none; the reasoning arm bears only on P4",
            "reasoning-arm seats ran with max_tokens 3000 (vs 1200 for zoo "
            "seats) so thinking could not truncate the verdict JSON; "
            "latency/cost rows are therefore not cap-matched across arms",
            "single provider (Ollama Cloud); latency observables reflect "
            "one day's provider load",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(f"report written: {REPORT}")
    for s in all_seats:
        print(f"  {s}: {table[s]}")
    for p in ("P1", "P2", "P3", "P4"):
        print(f"  {p}: {report['verdicts'][p]['verdict']}")

    if not args.no_index:
        line = (
            "\n## E0.2 judge zoo, tranche 3 (2026-07-13)\n\n"
            f"P1 {p1['verdict']} (median generalization ratio "
            f"{p1['median_generalization_ratio']}, line 0.8), "
            f"P2 {p2['verdict']} (clean-FP span {p2['span_pp']}pp, line 30), "
            f"P3 {p3['verdict']} ({len(p3['qualifying_seats'])} seat(s) with "
            f"unknown>=0.5 & FP<=0.15), "
            f"P4 {p4['verdict']} ({p4['models_counting']}/3 arm models, "
            f"line 2). {len(zoo_seats)} zoo seats + {len(rlow_seats)} "
            f"reasoning-arm seats x 120 frozen items; 0 substitutions. "
            f"{report['token_spend']['total']} live LLM tokens (cap "
            f"1500000). Prereg: `{PREREG}`. Report: "
            f"`experiments/results/e02_t3_judge_zoo_report.json`.\n"
        )
        with INDEX.open("a") as fh:
            fh.write(line)
        print("index line appended")
    return 0


if __name__ == "__main__":
    sys.exit(main())
