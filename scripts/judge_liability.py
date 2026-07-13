#!/usr/bin/env python
"""Judge liability index — validation tranche (pre-registered:
experiments/judge_liability_index_prereg.yaml).

A pure replay/scoring program (zero LLM tokens). Builds an event-driven,
per-seat exhibited-error index from signals the tranche-1 log already
emits, then validates it against ground truth. Ground truth (the hidden
annotations in the corpus files) is used ONLY to score the index, never
as an index input.

Index inputs (NO ground truth):
  - experiments/e02_t1_items/judgments.jsonl   (per-item per-seat verdicts)
  - experiments/e02_t1_items/toothless_funnel.json (critic outcomes; the
    argumentative critic is the stronger layer for toothless items)

Signals per seat ruling (an item judged by the seat), in the seat's own
event order (append order in judgments.jsonl):
  - toothless items: the critic ruled on every envelope; a seat ruling is
    SCRUTINIZED, and it EXHIBITS AN ERROR iff the seat passed
    (flawed=false) an item the critic failed (survives_criticism=false).
  - unknown-flaw / known-flaw items: a seat ruling is SCRUTINIZED iff ANY
    other seat flagged the item (the critic did not rule on these); it
    EXHIBITS AN ERROR iff the seat passed an item another seat flagged.
  - exposure: count of scrutinized rulings. Seats below the exposure
    floor are reported UNCALIBRATED, never clean.

Scoring: exhibited errors per scrutinized ruling, each error's weight
decaying multiplicatively with every SUBSEQUENT clean scrutinized ruling
by the same seat (decay constant recorded in the report; attention-style,
never a status input):

    index = sum_i DECAY^(clean_scrutinized_after_i) / exposure

Seats scored (three distinct seat configurations; raw verdicts kept
separate): gpt-oss-seat-A (raw seat same-A), gpt-oss-seat-B (raw seat
same-B), qwen-seat (raw seat cross-B). Raw seat cross-A is a duplicate
gpt-oss configuration and is scored in an appendix row only.

Validation (ground truth used ONLY here): true unknown-flaw
false-negative rate per seat (every unknown-flaw item is flawed by
construction; annotations checked for presence).

Usage: python scripts/judge_liability.py
         [--t1-items-dir experiments/e02_t1_items]
         [--t2-items-dir experiments/e02_t2_items]
         [--out-dir experiments/results]
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PREREG = "experiments/judge_liability_index_prereg.yaml"
SCHEMA = "deepreason-judge-liability-v1"
DECAY = 0.95           # per subsequent clean scrutinized ruling; recorded
EXPOSURE_FLOOR = 10    # scrutinized rulings; below => UNCALIBRATED

RAW_SEATS = ("same-A", "same-B", "cross-A", "cross-B")
NAMED_SEATS = {         # the three distinct seat configurations under test
    "gpt-oss-seat-A": "same-A",
    "gpt-oss-seat-B": "same-B",
    "qwen-seat": "cross-B",
}
APPENDIX_SEATS = {"gpt-oss-seat-A-cross-dup": "cross-A"}


def load_events(judgments_path: Path) -> dict[str, list[dict]]:
    """Per raw seat, rulings in log append order (the seat's event order)."""
    events: dict[str, list[dict]] = {seat: [] for seat in RAW_SEATS}
    seen: set[tuple[str, str]] = set()
    for line in judgments_path.read_text().splitlines():
        rec = json.loads(line)
        key = (rec["item_id"], rec["seat"])
        if key in seen:  # checkpoint replays: keep first occurrence order
            continue
        seen.add(key)
        events[rec["seat"]].append(rec)
    return events


def scrutiny_signal(rec: dict, all_verdicts: dict, critic_failed: dict
                    ) -> tuple[bool, bool]:
    """(scrutinized, exhibited_error) for one seat ruling — NO ground truth.

    all_verdicts: (item_id, seat) -> flawed bool
    critic_failed: item_id -> bool (toothless items only)
    """
    item_id = rec["item_id"]
    seat = rec["seat"]
    passed = not bool(rec["flawed"])
    if rec["sub_battery"] == "toothless_envelope":
        # The argumentative critic ruled on every envelope: always
        # scrutinized; error iff this seat passed what the critic failed.
        failed_by_critic = critic_failed[item_id]
        return True, (passed and failed_by_critic)
    # unknown_flaw / known_flaw (and, in the sensitivity variant, clean):
    # scrutiny exists where ANY other seat flagged the item.
    other_flagged = any(
        all_verdicts.get((item_id, other), False)
        for other in RAW_SEATS if other != seat
        if (item_id, other) in all_verdicts
    )
    return other_flagged, (passed and other_flagged)


def score_seat(rulings: list[dict], all_verdicts: dict, critic_failed: dict,
               decay: float = DECAY) -> dict:
    """Event-driven exhibited-error index for one seat's event stream."""
    exposure = 0
    exhibited = 0
    error_mass = 0.0  # decays on every clean scrutinized ruling
    for rec in rulings:
        scrutinized, error = scrutiny_signal(rec, all_verdicts, critic_failed)
        if not scrutinized:
            continue
        exposure += 1
        if error:
            exhibited += 1
            error_mass += 1.0
        else:
            error_mass *= decay
    out = {
        "rulings_total": len(rulings),
        "exposure_scrutinized_rulings": exposure,
        "exhibited_errors_raw": exhibited,
        "decayed_error_mass": round(error_mass, 4),
    }
    if exposure < EXPOSURE_FLOOR:
        # Uncalibrated-not-clean rule: no score, never a clean verdict.
        out["status"] = "UNCALIBRATED"
        out["liability_index"] = None
    else:
        out["status"] = "CALIBRATED"
        out["liability_index"] = round(error_mass / exposure, 4)
    return out


def true_unknown_fn_rate(rulings: list[dict], unknown_ids: set[str]) -> float:
    """Ground truth, validation ONLY: every unknown-flaw item is flawed by
    construction, so a pass (flawed=false) is a false negative."""
    rows = [r for r in rulings if r["item_id"] in unknown_ids]
    return sum(1 for r in rows if not r["flawed"]) / len(rows)


def rank_desc(values: dict[str, float]) -> list[str]:
    """Seat names sorted worst-first; deterministic tiebreak by name so a
    genuine tie shows up as rank disagreement unless both signals tie."""
    return sorted(values, key=lambda s: (-values[s], s))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--t1-items-dir", default="experiments/e02_t1_items")
    parser.add_argument("--t2-items-dir", default="experiments/e02_t2_items")
    parser.add_argument("--out-dir", default="experiments/results")
    args = parser.parse_args()
    t1 = REPO / args.t1_items_dir
    t2 = REPO / args.t2_items_dir
    out_dir = REPO / args.out_dir if not Path(args.out_dir).is_absolute() \
        else Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    events = load_events(t1 / "judgments.jsonl")
    all_verdicts = {(r["item_id"], r["seat"]): bool(r["flawed"])
                    for rulings in events.values() for r in rulings}
    funnel = json.loads((t1 / "toothless_funnel.json").read_text())
    critic_failed = {rec["item_id"]: not rec["survives_criticism"]
                     for rec in funnel}

    # Ground truth (validation ONLY): unknown-flaw ids; annotations present.
    unknown_items = json.loads((t1 / "unknown_flaws.json").read_text())
    assert all(item.get("hidden_annotation") for item in unknown_items)
    unknown_ids = {item["id"] for item in unknown_items}

    # ------------------------------------------------------------------ #
    # Index (no ground truth), then validation columns.
    # ------------------------------------------------------------------ #
    models = {r["seat"]: r["model"] for rulings in events.values()
              for r in rulings}
    table: dict[str, dict] = {}
    for name, raw_seat in {**NAMED_SEATS, **APPENDIX_SEATS}.items():
        row = score_seat(events[raw_seat], all_verdicts, critic_failed)
        row["raw_seat"] = raw_seat
        row["model"] = models[raw_seat]
        row["true_unknown_fn_rate_validation_only"] = round(
            true_unknown_fn_rate(events[raw_seat], unknown_ids), 4)
        table[name] = row

    named = {name: table[name] for name in NAMED_SEATS}

    # P1 — exact rank agreement (n=3), index vs true unknown-flaw FN rate.
    calibrated = all(row["status"] == "CALIBRATED" for row in named.values())
    index_rank = rank_desc({n: r["liability_index"] for n, r in named.items()}) \
        if calibrated else None
    truth_rank = rank_desc({n: r["true_unknown_fn_rate_validation_only"]
                            for n, r in named.items()})
    p1 = ("CONFIRMED" if calibrated and index_rank == truth_rank
          else "REFUTED")

    # P2 — weakest/strongest separation >= 2x on the index score.
    scores = [r["liability_index"] for r in named.values()]
    if not calibrated:
        p2, ratio = "REFUTED", None
    else:
        weakest, strongest = max(scores), min(scores)
        ratio = (float("inf") if strongest == 0 and weakest > 0
                 else None if weakest == strongest == 0
                 else weakest / strongest)
        p2 = "CONFIRMED" if ratio is not None and ratio >= 2 else "REFUTED"

    # P3 — mechanical checks: every seat's exposure reported; a seat with
    # zero scrutinized rulings gets UNCALIBRATED, never a clean score.
    exposures_reported = all(
        isinstance(row.get("exposure_scrutinized_rulings"), int)
        for row in table.values())
    synthetic = score_seat([], all_verdicts, critic_failed)  # zero-scrutiny seat
    uncalibrated_not_clean = (synthetic["status"] == "UNCALIBRATED"
                              and synthetic["liability_index"] is None)
    p3 = ("CONFIRMED" if exposures_reported and uncalibrated_not_clean
          else "REFUTED")

    # ------------------------------------------------------------------ #
    # Decay-sensitivity sweep (reported, not verdict-bearing): the prereg
    # fixes the decay's ROLE but not its constant; the primary constant is
    # the value coded before the first data run (DECAY above). The sweep
    # shows how rank agreement depends on that free choice.
    # ------------------------------------------------------------------ #
    decay_sweep = {}
    for d in (1.0, 0.999, 0.99, 0.98, DECAY, 0.90):
        rows = {name: score_seat(events[raw], all_verdicts, critic_failed,
                                 decay=d)
                for name, raw in NAMED_SEATS.items()}
        sweep_rank = rank_desc({n: r["liability_index"]
                                for n, r in rows.items()})
        decay_sweep[str(d)] = {
            "scores": {n: r["liability_index"] for n, r in rows.items()},
            "rank_worst_first": sweep_rank,
            "rank_matches_truth": sweep_rank == truth_rank,
        }

    # ------------------------------------------------------------------ #
    # Sensitivity variant (reported, not verdict-bearing): tranche-2 clean
    # judgments appended to each seat's event stream, same signal rules.
    # On clean items an other-seat flag is itself an error, so this variant
    # knowingly mis-scores some rulings; it probes ranking robustness.
    # ------------------------------------------------------------------ #
    sensitivity = None
    t2_judgments = t2 / "judgments.jsonl"
    if t2_judgments.exists():
        t2_events = load_events(t2_judgments)
        merged = {seat: events[seat] + t2_events[seat] for seat in RAW_SEATS}
        merged_verdicts = dict(all_verdicts)
        merged_verdicts.update({(r["item_id"], r["seat"]): bool(r["flawed"])
                                for rs in t2_events.values() for r in rs})
        sens_rows = {}
        for name, raw_seat in NAMED_SEATS.items():
            row = score_seat(merged[raw_seat], merged_verdicts, critic_failed)
            sens_rows[name] = {
                "liability_index": row["liability_index"],
                "exposure_scrutinized_rulings":
                    row["exposure_scrutinized_rulings"],
                "status": row["status"],
            }
        sens_calibrated = all(r["status"] == "CALIBRATED"
                              for r in sens_rows.values())
        sensitivity = {
            "population": ("tranche-1 events + tranche-2 clean-item events "
                           "(same signal rules; other-seat flags on clean "
                           "items are themselves errors — see caveats)"),
            "per_seat": sens_rows,
            "rank_worst_first": (
                rank_desc({n: r["liability_index"]
                           for n, r in sens_rows.items()})
                if sens_calibrated else None),
            "rank_matches_primary": (
                rank_desc({n: r["liability_index"]
                           for n, r in sens_rows.items()}) == index_rank
                if sens_calibrated and index_rank else None),
        }

    verdicts = {
        "P1": {"verdict": p1,
               "statement": "index (computed without ground truth) ranks the "
                            "three seat configurations exactly as their true "
                            "unknown-flaw false-negative rates",
               "measured": {"index_rank_worst_first": index_rank,
                            "truth_rank_worst_first": truth_rank}},
        "P2": {"verdict": p2,
               "statement": "weakest/strongest index score ratio >= 2x",
               "measured": {"ratio": (None if ratio is None
                                      else ("inf" if ratio == float("inf")
                                            else round(ratio, 4)))}},
        "P3": {"verdict": p3,
               "statement": "every seat's exposure reported; zero-scrutiny "
                            "seat is UNCALIBRATED, never clean",
               "measured": {"exposures_reported": exposures_reported,
                            "synthetic_zero_scrutiny_seat": synthetic}},
    }

    caveats = [
        "Single validation tranche (the committed tranche-1 corpus); no "
        "out-of-tranche replication yet.",
        "Critic-as-oracle assumption: for toothless items the argumentative "
        "critic's outcome is treated as the stronger layer; the critic is "
        "itself an imperfect instrument (here it failed all 40 envelopes, "
        "which the corpus construction says is correct, but that agreement "
        "is not guaranteed in general).",
        "n=3 seats: exact rank agreement has a 1-in-6 chance under a random "
        "ranking, so P1 alone is weak evidence; P2's separation requirement "
        "is the stronger check.",
        "On unknown/known-flaw items, scrutiny comes from other seats' "
        "flags; because every item in those sub-batteries is flawed by "
        "construction, a flagging seat is always right on this fixture. On "
        "live mixed traffic that assumption fails for sound items — see the "
        "sensitivity variant, where tranche-2 clean items make other-seat "
        "flags themselves errors and exhibited-error attribution can "
        "penalize a correct lenient seat.",
        "Raw seat cross-A is a fourth ruling stream with the same "
        "configuration as the gpt-oss seats; it is excluded from the n=3 "
        "validation (duplicate configuration) and reported as an appendix "
        "row.",
        "The prereg's paraphrase/order-variation disagreement signal is "
        "absent from the tranche-1 data (no paraphrase arms were run); the "
        "index here uses only cross-instrument contradiction + exposure + "
        "decay.",
        f"Decay constant {DECAY} and exposure floor {EXPOSURE_FLOOR} were "
        "coded before the first data run but the prereg left the constant "
        "free; it is an untuned choice, recorded here, attention-style, "
        "never a status input. The decay_sensitivity_sweep shows the "
        "verdict-bearing rank is SENSITIVE to this choice for the two "
        "near-tied gpt-oss seats: the primary constant was NOT revised "
        "after seeing outcomes.",
        "Event order in this replay is the per-seat append order of "
        "judgments.jsonl, i.e. thread-pool completion order over a static "
        "corpus; it carries no live temporal meaning, so decay interacts "
        "with an essentially arbitrary ordering (roughly corpus order: "
        "unknown, known, toothless). In live operation the order would be "
        "real ruling time.",
        "Ground truth (hidden annotations; unknown-flaw items flawed by "
        "construction) was used ONLY to compute the validation columns and "
        "verdicts, never as an index input.",
    ]

    report = {
        "schema": SCHEMA,
        "prereg": PREREG,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "program": "scripts/judge_liability.py (pure replay; 0 LLM tokens)",
        "instrument": {
            "decay_constant_per_clean_scrutinized_ruling": DECAY,
            "exposure_floor": EXPOSURE_FLOOR,
            "event_order": "per-seat append order in judgments.jsonl",
            "signals": ["cross-instrument contradiction (critic on toothless; "
                        "any-other-seat flag on flawed batteries)",
                        "exposure (scrutinized-ruling count)",
                        "decay on subsequent clean scrutinized rulings"],
        },
        "seats": {"named": NAMED_SEATS, "appendix": APPENDIX_SEATS},
        "per_seat_table": table,
        "verdicts": verdicts,
        "decay_sensitivity_sweep": decay_sweep,
        "sensitivity_with_t2_clean_events": sensitivity,
        "llm_tokens_spent": 0,
        "caveats": caveats,
    }
    report_path = out_dir / "judge_liability_index_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    index_path = out_dir / f"INDEX_{dt.date.today().isoformat()}.md"
    scores_txt = ", ".join(
        f"{name} {row['liability_index']}" for name, row in named.items())
    index_line = (
        f"\n## Judge liability index, validation tranche "
        f"({dt.date.today().isoformat()})\n\n"
        f"P1 {p1} (rank worst-first: "
        f"{index_rank}), P2 {p2} (weakest/strongest ratio "
        f"{verdicts['P2']['measured']['ratio']}), P3 {p3}. Scores: "
        f"{scores_txt}. 0 LLM tokens. Prereg: `{PREREG}`. Report: "
        f"`experiments/results/judge_liability_index_report.json`.\n")
    with index_path.open("a") as fh:
        fh.write(index_line)

    print(json.dumps({
        "verdicts": {k: v["verdict"] for k, v in verdicts.items()},
        "per_seat": {name: {"liability_index": row["liability_index"],
                            "exposure": row["exposure_scrutinized_rulings"],
                            "exhibited_errors_raw": row["exhibited_errors_raw"],
                            "status": row["status"],
                            "true_unknown_fn_rate_validation_only":
                                row["true_unknown_fn_rate_validation_only"]}
                     for name, row in table.items()},
        "ranks": {"index": index_rank, "truth": truth_rank},
        "ratio": verdicts["P2"]["measured"]["ratio"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
