#!/usr/bin/env python
"""Experiment E — placement forensics over the committed criticism datasets.

Reanalyses the repository's existing LABELED criticism measurements to
separate WHERE the critic's interventions landed, without mixing units.
Three incompatible unit levels exist and are kept separate in every table:

  1. candidate_level_flag  — the original validation studies (k=5 candidate
     pools per question, critic flags individual candidates before a
     majority vote).  Only aggregate numbers survive in this tree (quoted
     from scripts/live_run.py seed_criticism); NOT recomputable here.
  2. item_level_objection  — one critic call per artifact (one artifact per
     item, no k-candidate pool).  Recomputable from the committed
     calibration / critic-spec / court-cross judgment files.
  3. court_conviction      — a sustained verdict from the defended
     two-seat court, downstream of an item-level objection.  Recomputable
     from the calibration and court-cross judgment files.

The historical labels "precision"/"recall" in this repo mix these levels;
every rate emitted here carries an explicit numerator and denominator, and
no rate is named precision or recall unless its unit level is stated in
the same key name.

Zero LLM tokens.  Read-only over data; writes only
experiments/results/glm_judge_v1_experiment_e_placement.json (or the path
given as argv[1]).  Output is deterministic (no timestamps) so reruns are
byte-identical.

Usage: python scripts/experiment_e_placement.py [output_path]
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CAL_PAIRS = REPO / "experiments/court_calibration_items/pairs_v1.json"
CAL_JUDGMENTS = REPO / "experiments/court_calibration_run/judgments.jsonl"
SPEC_SOUND = REPO / "experiments/critic_spec_items/sound_items.json"
SPEC_FLAWED = REPO / "experiments/e02_t1_items/known_flaws.json"
SPEC_JUDGMENTS = REPO / "experiments/critic_spec_run/judgments.jsonl"
CROSS_ARMS = {
    "dsflash": REPO / "experiments/court_cross_run/arm_dsflash.jsonl",
    "kimi": REPO / "experiments/court_cross_run/arm_kimi.jsonl",
    "mistral": REPO / "experiments/court_cross_run/arm_mistral.jsonl",
}
LIVE_RUN = REPO / "scripts/live_run.py"

DEFAULT_OUT = REPO / "experiments/results/glm_judge_v1_experiment_e_placement.json"

SCHEMA = "deepreason-experiment-e-placement-v1"


def rate(numerator: int, denominator: int) -> dict:
    """Every rate in the report is this explicit triple."""
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": round(numerator / denominator, 6) if denominator else None,
    }


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# ---------------------------------------------------------------- glossary

def unit_glossary() -> dict:
    return {
        "candidate_level_flag": (
            "Unit = one of k=5 generated candidate answers to a validation "
            "question; the critic flags individual candidates before a "
            "majority vote over the surviving pool.  'Precision'/'recall' "
            "at this level score flagged candidates against the held-out "
            "answer key.  This level exists ONLY in the original "
            "validation-study aggregates quoted in validation_context; the "
            "validation run roots are not in this tree, so nothing at this "
            "level is recomputable here."
        ),
        "item_level_objection": (
            "Unit = one artifact judged by one critic call (one artifact "
            "per item — there is NO k-candidate pool).  The critic's "
            "positive event is an objection ('objects' in the court "
            "datasets, 'convicts'/'defect_found' in the bare-critic "
            "dataset).  Rates at this level count items, not candidates "
            "and not court verdicts."
        ),
        "court_conviction": (
            "Unit = the final outcome of one defended trial (two-seat "
            "court: sustain / overrule / abstain; an empty rulings list "
            "means no trial completed).  A conviction is outcome == "
            "'sustain'.  Convictions are a strict subset of item-level "
            "objections (no objection, no trial) and must never be pooled "
            "with them or with candidate-level flags."
        ),
        "warning": (
            "Historical labels 'precision'/'recall' in this repository mix "
            "these three levels.  In this report no rate is named "
            "precision or recall unless the unit level is stated in the "
            "same key name."
        ),
    }


# ------------------------------------------------------- dataset 1: court

def calibration_placement() -> dict:
    pairs = json.loads(CAL_PAIRS.read_text())
    rows = load_jsonl(CAL_JUDGMENTS)
    assert len(pairs) == 42, f"expected 42 pairs, got {len(pairs)}"
    assert len(rows) == 84, f"expected 84 judgments, got {len(rows)}"

    by_id = {r["id"]: r for r in rows}
    defect_by_pair = {p["pair_id"]: p["defect_class"] for p in pairs}
    for pid in defect_by_pair:
        for side in ("clean", "corrupted"):
            assert f"{pid}:{side}" in by_id, f"missing judgment {pid}:{side}"

    def side_rows(side: str) -> list[dict]:
        return sorted((r for r in rows if r["id"].endswith(":" + side)),
                      key=lambda r: r["id"])

    def outcome_of(r: dict) -> str:
        # Absent outcome / empty rulings list = no trial completed.
        if not r.get("rulings"):
            return "no_trial"
        return r["outcome"]

    per_class = {}
    counts = {}
    for side in ("clean", "corrupted"):
        sub = side_rows(side)
        n = len(sub)
        n_obj = sum(1 for r in sub if r["objects"])
        c = {o: sum(1 for r in sub if outcome_of(r) == o)
             for o in ("sustain", "overrule", "abstain", "no_trial")}
        counts[side] = {"n": n, "objections": n_obj, **c}
        per_class[side] = {
            "n_items": n,
            "objection_rate": rate(n_obj, n),
            "conviction_rate_sustained": rate(c["sustain"], n),
            "overrule_rate": rate(c["overrule"], n),
            "abstain_rate": rate(c["abstain"], n),
            "no_trial_count": c["no_trial"],
        }

    cl, co = counts["clean"], counts["corrupted"]

    # Placement quantities (unit: court_conviction unless stated otherwise).
    critic_right_vetoed = [
        r["id"] for r in side_rows("corrupted")
        if r["objects"] and outcome_of(r) in ("overrule", "abstain")
    ]
    clean_not_sustained = [
        r["id"] for r in side_rows("clean")
        if r["objects"] and outcome_of(r) != "sustain"
    ]
    n_sustained_total = co["sustain"] + cl["sustain"]
    n_objections_total = co["objections"] + cl["objections"]

    per_defect_class = {}
    for dclass in sorted(set(defect_by_pair.values())):
        pids = sorted(p for p, d in defect_by_pair.items() if d == dclass)
        sub = [by_id[f"{p}:corrupted"] for p in pids]
        per_defect_class[dclass] = {
            "n_corrupted_items": len(sub),
            "corrupted_sustained_count":
                sum(1 for r in sub if outcome_of(r) == "sustain"),
            "corrupted_overruled_count":
                sum(1 for r in sub if outcome_of(r) == "overrule"),
            "corrupted_abstained_count":
                sum(1 for r in sub if outcome_of(r) == "abstain"),
        }

    return {
        "inputs": {
            "pairs": str(CAL_PAIRS.relative_to(REPO)),
            "judgments": str(CAL_JUDGMENTS.relative_to(REPO)),
            "n_pairs": len(pairs),
            "n_judged_items": len(rows),
            "design": "42 clean/corrupted pairs with known labels; critic "
                      "(deepseek-v4-flash) objection then defended two-seat "
                      "court trial per item",
        },
        "unit_levels_present": ["item_level_objection", "court_conviction"],
        "per_item_class": per_class,
        "placement": {
            "interventions_sustained_on_corrupted":
                rate(co["sustain"], co["n"]),
            "interventions_sustained_on_clean":
                rate(cl["sustain"], cl["n"]),
            "critic_right_but_court_vetoed": {
                "definition": "corrupted items where the critic objected "
                              "and the court overruled or abstained",
                **rate(len(critic_right_vetoed), co["objections"]),
                "denominator_definition":
                    "corrupted items with a critic objection",
                "breakdown": {
                    "overruled_count": co["overrule"],
                    "abstained_count": co["abstain"],
                },
                "item_ids": critic_right_vetoed,
            },
            "critic_wrong_but_court_prevented_damage": {
                "definition": "clean items where the critic objected and "
                              "the court did NOT sustain",
                **rate(len(clean_not_sustained), cl["objections"]),
                "denominator_definition":
                    "clean items with a critic objection",
                "breakdown": {
                    "overruled_count": cl["overrule"],
                    "abstained_count": cl["abstain"],
                    "sustained_count_damage_done": cl["sustain"],
                },
            },
        },
        "disentangled_quantities": {
            "item_level_objection_precision": {
                **rate(co["objections"], n_objections_total),
                "definition": "corrupted items objected to / all items "
                              "objected to",
            },
            "item_level_objection_recall_on_corrupted": {
                **rate(co["objections"], co["n"]),
                "definition": "corrupted items objected to / all corrupted "
                              "items",
            },
            "court_conviction_level_precision": {
                **rate(co["sustain"], n_sustained_total),
                "definition": "sustained convictions on corrupted items / "
                              "all sustained convictions",
            },
            "court_conviction_level_recall_on_corrupted": {
                **rate(co["sustain"], co["n"]),
                "definition": "sustained convictions on corrupted items / "
                              "all corrupted items",
            },
        },
        "per_defect_class_corrupted_outcomes": per_defect_class,
        "notes": [
            "The critic objected on 84/84 items (both classes), so the "
            "item_level_objection_precision (42/84) is exactly the "
            "corrupted base rate: at this unit level the objection carries "
            "zero information.  ALL clean/corrupted separation observed in "
            "this dataset was produced by the court, not by the critic's "
            "objection decision.",
            "court_conviction_level_precision is 5/5 = 1.0 but on a tiny "
            "numerator; the same court vetoed 37/42 objections on items "
            "that really were corrupted.",
            "These are item-level and court-level quantities; they are NOT "
            "comparable to the candidate-level precision/recall in "
            "validation_context.",
        ],
    }


# -------------------------------------------------- dataset 2: bare critic

def bare_critic_placement() -> dict:
    flawed_items = json.loads(SPEC_FLAWED.read_text())
    sound_items = json.loads(SPEC_SOUND.read_text())
    rows = load_jsonl(SPEC_JUDGMENTS)
    assert len(flawed_items) == 40 and len(sound_items) == 40
    assert len(rows) == 80, f"expected 80 judgments, got {len(rows)}"

    by_id = {r["id"]: r for r in rows}
    for item in flawed_items:
        assert by_id[item["id"]]["battery"] == "flawed", item["id"]
    for item in sound_items:
        assert by_id[item["id"]]["battery"] == "sound", item["id"]

    def battery(name: str) -> list[dict]:
        return sorted((r for r in rows if r["battery"] == name),
                      key=lambda r: r["id"])

    fl, so = battery("flawed"), battery("sound")
    n_fl_convict = sum(1 for r in fl if r["convicts"])
    n_so_convict = sum(1 for r in so if r["convicts"])
    n_convict_total = n_fl_convict + n_so_convict
    parse_failures = sum(1 for r in rows if r["parse_failure"])

    return {
        "inputs": {
            "flawed_items": str(SPEC_FLAWED.relative_to(REPO)),
            "sound_items": str(SPEC_SOUND.relative_to(REPO)),
            "judgments": str(SPEC_JUDGMENTS.relative_to(REPO)),
            "n_flawed": len(fl),
            "n_sound": len(so),
            "conviction_rule": "per scripts/critic_spec_score.py: convicts "
                               "= defect_found AND named defect string >= "
                               "20 chars, != 'none'; parse failure never "
                               "convicts ('convicts' field in judgments)",
        },
        "unit_levels_present": ["item_level_objection"],
        "no_court": "bare critic only — a 'conviction' here is the "
                    "critic's own item-level verdict, a DIFFERENT event "
                    "from a court sustain; do not pool with "
                    "calibration_placement court outcomes",
        "per_item_class": {
            "flawed": {
                "n_items": len(fl),
                "conviction_rate": rate(n_fl_convict, len(fl)),
                "acquittal_rate": rate(len(fl) - n_fl_convict, len(fl)),
            },
            "sound": {
                "n_items": len(so),
                "conviction_rate": rate(n_so_convict, len(so)),
                "acquittal_rate": rate(len(so) - n_so_convict, len(so)),
            },
        },
        "placement": {
            "convictions_on_flawed": rate(n_fl_convict, len(fl)),
            "convictions_on_sound": rate(n_so_convict, len(so)),
        },
        "disentangled_quantities": {
            "item_level_conviction_precision": {
                **rate(n_fl_convict, n_convict_total),
                "definition": "convictions on known-flawed items / all "
                              "convictions",
            },
            "item_level_conviction_recall_on_flawed": {
                **rate(n_fl_convict, len(fl)),
                "definition": "convictions on known-flawed items / all "
                              "known-flawed items",
            },
        },
        "parse_failure_count": parse_failures,
        "notes": [
            "Sound-item convictions are an UPPER bound on false "
            "convictions: only each sound item's central claim is "
            "mechanically verified true; the surrounding prose is "
            "model-written (see critic_specificity_report.json caveats).",
            "These are item-level quantities from single-artifact items; "
            "they are NOT comparable to the candidate-level "
            "precision/recall in validation_context.",
        ],
    }


# --------------------------------------------------- dataset 3: cross-run

def court_cross_distributions() -> dict:
    arms = {}
    for arm, path in sorted(CROSS_ARMS.items()):
        rows = load_jsonl(path)
        n = len(rows)
        n_obj = sum(1 for r in rows if r["objects"])

        def outcome_of(r: dict) -> str:
            if not r.get("rulings"):
                return "no_trial"
            return r["outcome"]

        c = {o: sum(1 for r in rows if outcome_of(r) == o)
             for o in ("sustain", "overrule", "abstain", "no_trial")}
        no_trial_reasons = sorted(
            r.get("abstain_reason",
                  "critic_parse_failure" if r.get("critic_parse_failure")
                  else "unknown")
            for r in rows if not r.get("rulings"))
        arms[arm] = {
            "judgments": str(path.relative_to(REPO)),
            "critic_model": rows[0]["critic_model"],
            "n_items": n,
            "objection_rate": rate(n_obj, n),
            "outcome_counts": c,
            "sustain_rate_over_all_items": rate(c["sustain"], n),
            "sustain_rate_over_completed_trials":
                rate(c["sustain"],
                     c["sustain"] + c["overrule"] + c["abstain"]),
            "overrule_rate_over_all_items": rate(c["overrule"], n),
            "abstain_rate_over_all_items": rate(c["abstain"], n),
            "no_trial_count": c["no_trial"],
            "no_trial_reasons": no_trial_reasons,
            "seat_disagreement_count":
                sum(1 for r in rows if r.get("seat_disagreement")),
            "critic_parse_failure_count":
                sum(1 for r in rows if r.get("critic_parse_failure")),
        }
    return {
        "label_free": True,
        "warning": (
            "The 85-item blinded pool has NO ground-truth labels in this "
            "repository.  Only objection/outcome DISTRIBUTIONS are "
            "computable; precision and recall are NOT computable at ANY "
            "unit level from this dataset, and no such rate is reported "
            "for it."
        ),
        "unit_levels_present": ["item_level_objection", "court_conviction"],
        "arms": arms,
    }


# --------------------------------------------- dataset 4: validation quote

VALIDATION_QUOTES = {
    "easy_set": (
        "[easy set, 24 q] v4-pro: single=sc=harness=1.00 (ceiling); "
        "v4-flash: all three arms 0.958, critic precision 0.333, recall "
        "0.25 at candidate base error 0.033."
    ),
    "hard_set": (
        "[hard set, 20 q] v4-pro: single 0.95, sc 1.00, harness 1.00; "
        "candidate base error 0.01; critic recall 1.0, precision 0.125; "
        "net fixed-minus-broke 0 — with 4/5 majorities already right, "
        "filtering changed nothing."
    ),
}

# Single-line fragments that must appear verbatim in live_run.py (the
# quoted sentences span concatenated string literals in the source).
VALIDATION_SOURCE_FRAGMENTS = [
    "critic precision 0.333",
    "recall 0.25 at candidate base error 0.033",
    "single 0.95, sc 1.00, harness 1.00",
    "candidate base error 0.01; critic recall 1.0",
    "0.125; net fixed-minus-broke 0",
    "with 4/5 majorities ",
]


def validation_context() -> dict:
    src = LIVE_RUN.read_text()
    for frag in VALIDATION_SOURCE_FRAGMENTS:
        assert frag in src, f"validation fragment not found in source: {frag}"
    return {
        "source": "scripts/live_run.py seed_criticism (pi-criticism "
                  "problem description)",
        "unit_level": "candidate_level_flag",
        "recomputable_from_this_repo": False,
        "why_not_recomputable": (
            "These are aggregates of the ORIGINAL validation studies (k=5 "
            "candidate pools per question, answer key held out); the "
            "validation run roots are not in this tree.  They are context "
            "only, NOT reanalysis inputs, and must not be pooled with the "
            "item-level or court-level tables above."
        ),
        "quotes": VALIDATION_QUOTES,
        "parsed_candidate_level_numbers": {
            "easy_set_24q_v4flash": {
                "candidate_level_critic_precision": 0.333,
                "candidate_level_critic_recall": 0.25,
                "candidate_base_error": 0.033,
                "arm_accuracy_all_three": 0.958,
                "k": 5,
            },
            "hard_set_20q_v4pro": {
                "candidate_level_critic_precision": 0.125,
                "candidate_level_critic_recall": 1.0,
                "candidate_base_error": 0.01,
                "single": 0.95,
                "self_consistency": 1.0,
                "harness": 1.0,
                "net_fixed_minus_broke": 0,
                "k": 5,
            },
        },
    }


# -------------------------------------------------------------- assembly

def build_report() -> dict:
    cal = calibration_placement()
    bare = bare_critic_placement()
    return {
        "schema": SCHEMA,
        "generated_by": "scripts/experiment_e_placement.py",
        "deterministic": True,
        "llm_tokens_spent": 0,
        "unit_glossary": unit_glossary(),
        "calibration_placement": cal,
        "bare_critic_placement": bare,
        "court_cross_distributions": court_cross_distributions(),
        "validation_context": validation_context(),
        "majority_language_caveat": {
            "statement": (
                "The item-level datasets reanalysed here have ONE artifact "
                "per item, not k candidates per question.  'Wrong "
                "majorities repaired' and 'correct majorities broken' are "
                "candidate-level voting quantities and are NOT computable "
                "from these datasets — there is no majority to repair or "
                "break.  Rather than force the voting vocabulary onto "
                "incompatible data, the closest computable analogues are "
                "reported below."
            ),
            "closest_computable_analogues": {
                "planted_defects_convicted": {
                    "calibration_court_sustained_on_corrupted":
                        cal["placement"]
                        ["interventions_sustained_on_corrupted"],
                    "bare_critic_convictions_on_flawed":
                        bare["placement"]["convictions_on_flawed"],
                },
                "clean_items_convicted": {
                    "calibration_court_sustained_on_clean":
                        cal["placement"]["interventions_sustained_on_clean"],
                    "bare_critic_convictions_on_sound":
                        bare["placement"]["convictions_on_sound"],
                },
            },
            "not_computable_here": [
                "wrong_majorities_repaired",
                "correct_majorities_broken",
                "net_fixed_minus_broke",
            ],
        },
    }


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    report = build_report()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    cal = report["calibration_placement"]
    bare = report["bare_critic_placement"]
    summary = {
        "output": str(out),
        "calibration_sustained_corrupted":
            cal["placement"]["interventions_sustained_on_corrupted"],
        "calibration_sustained_clean":
            cal["placement"]["interventions_sustained_on_clean"],
        "critic_right_but_court_vetoed": {
            k: cal["placement"]["critic_right_but_court_vetoed"][k]
            for k in ("numerator", "denominator", "value")},
        "critic_wrong_but_court_prevented_damage": {
            k: cal["placement"]["critic_wrong_but_court_prevented_damage"][k]
            for k in ("numerator", "denominator", "value")},
        "bare_critic_convictions_flawed":
            bare["placement"]["convictions_on_flawed"],
        "bare_critic_convictions_sound":
            bare["placement"]["convictions_on_sound"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
