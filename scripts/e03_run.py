"""E0.3 runner: executes exactly the measurements pre-registered in
experiments/e03_detector_calibration_prereg.yaml and writes the report.

Zero LLM tokens, zero network: synthetic roots are generated through the
real harness registration path (scripts/e03_synthetic_regimes.py), verified
with deepreason.invariants.verify_root (violations recorded, never patched),
and scored with the REAL capture-detection functions
(deepreason.capture.detection) plus AUC against the healthy arm.

Pre-committed operationalizations (stated here because the prereg fixes the
detector list, directions, and the literal thresholds, but not every
mechanical detail):

  - Per-run detector summaries use a FULL-RUN window (window = event count)
    passed to the real detection functions; raw_flags alone runs at the
    production default Config() (CAPTURE_W=20), since it is itself the
    composite being scored.
  - gate_block_rate and g_churn are normalized per CAPTURE_W(=20)-event
    window: value * 20 / n_events ("per-window" in the prereg).
  - Directions (higher score = more pathological): gate_block_rate +,
    contraction mean pairwise distance -, contraction slope -,
    attack_target_entropy -, criticism_debt +, g_churn - (a priori from
    detection.raw_flags, whose stagnation conjunction treats zero churn as
    the pathological pole; the prereg's direction list omits g_churn),
    reinstatement_rate -, raw_flags composite (count of true flags) +.
  - Imputation, fixed a priori: attack_target_entropy None (fewer than two
    attacks) -> 0.0; reinstatement_rate None (no refutations) -> 0.0;
    dist_slope None -> 0.0. Raw values are reported alongside.
  - "generator contraction" verdicts (P3, P4) use the mean pairwise
    distance AUC as primary (the prereg direction list names "contraction
    distance"); the slope AUC is reported as a secondary row.
  - P2 is evaluated over every scored detector row.
  - P4's "adjudicator metrics stay unchanged relative to P2" is
    operationalized as |AUC_mimicry - AUC_wrong_but_stable| <= 0.10 for each
    of attack_target_entropy, criticism_debt, g_churn, reinstatement_rate
    (the prereg gives no literal tolerance; failures of only this clause
    yield UNDECIDED, never a silent pass).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from e03_synthetic_regimes import REGIMES, build_run  # noqa: E402

from deepreason.capture.detection import (  # noqa: E402
    adjudicator_metrics,
    gate_block_count,
    generator_metrics,
    raw_flags,
)
from deepreason.config import Config  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.invariants import verify_root  # noqa: E402
from deepreason.llm.embedder import HashingEmbedder  # noqa: E402

PREREG = "experiments/e03_detector_calibration_prereg.yaml"
REPORT_PATH = REPO / "experiments/results/e03_detector_calibration_report.json"
INDEX_PATH = REPO / "experiments/results/INDEX_2026-07-13.md"
DEFAULT_OUT_ROOT = (
    "/tmp/claude-0/-home-user-DeepReason/ac9743fe-69f0-5a0d-a640-aa2c1585799f/"
    "scratchpad/e03_roots"
)
SEEDS = list(range(10))

# detector row -> (summary key, direction). direction=+1: higher = worse;
# -1: lower = worse. See module docstring for the a-priori rationale.
DETECTORS: dict[str, tuple[str, int]] = {
    "gate_block_rate": ("gate_block_rate", +1),
    "contraction_mean_pairwise_dist": ("contraction_mean_pairwise_dist", -1),
    "contraction_dist_slope": ("contraction_dist_slope", -1),
    "attack_target_entropy": ("attack_target_entropy_imputed", -1),
    "criticism_debt": ("criticism_debt", +1),
    "g_churn": ("g_churn_rate", -1),
    "reinstatement_rate": ("reinstatement_rate_imputed", -1),
    "raw_flags_composite": ("raw_flags_composite", +1),
}
ADJUDICATOR_DETECTORS = [
    "attack_target_entropy", "criticism_debt", "g_churn", "reinstatement_rate",
]
PATHOLOGICAL = [r for r in REGIMES if r != "healthy"]


def summarize_run(root: Path) -> dict:
    """Per-run detector summary using the real detection functions over a
    freshly reopened (replayed) harness."""
    h = Harness(root)
    embedder = HashingEmbedder()
    cfg = Config()
    n_events = h._next_seq
    window = max(n_events, 1)

    gen = generator_metrics(h, embedder, window)
    adj = adjudicator_metrics(h, window)
    blocks = gate_block_count(h, window)
    flags = raw_flags(h, embedder, cfg)

    entropy = adj["attack_target_entropy"]
    reinst = adj["reinstatement_rate"]
    slope = gen["dist_slope"]
    return {
        "n_events": n_events,
        "n_conjectures": gen["stream_len"],
        "gate_blocks": blocks,
        "gate_block_rate": blocks * cfg.CAPTURE_W / n_events,
        "contraction_mean_pairwise_dist": gen["mean_pairwise_dist"],
        "contraction_dist_slope": 0.0 if slope is None else slope,
        "contraction_dist_slope_raw": slope,
        "inter_school_dist_ratio": gen["inter_school_dist_ratio"],
        "attack_target_entropy_raw": entropy,
        "attack_target_entropy_imputed": 0.0 if entropy is None else entropy,
        "criticism_debt": adj["criticism_debt"],
        "g_churn": adj["g_churn"],
        "g_churn_rate": adj["g_churn"] * cfg.CAPTURE_W / n_events,
        "refutations": adj["refutations"],
        "n_attacks": adj["n_attacks"],
        "reinstatement_rate_raw": reinst,
        "reinstatement_rate_imputed": 0.0 if reinst is None else reinst,
        "raw_flags": flags,
        "raw_flags_composite": sum(1 for v in flags.values() if v),
    }


def auc(pathological: list[float], healthy: list[float]) -> float:
    """Mann-Whitney AUC of 'pathological scores exceed healthy scores',
    ties counted 0.5. Scores are already direction-adjusted."""
    pairs = [(p, h) for p in pathological for h in healthy]
    hits = sum(1.0 if p > h else 0.5 if p == h else 0.0 for p, h in pairs)
    return hits / len(pairs)


def main() -> None:
    out_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(DEFAULT_OUT_ROOT)

    generation: list[dict] = []
    summaries: dict[str, list[dict]] = {r: [] for r in REGIMES}
    verifications: list[dict] = []
    total_violations = 0
    total_tokens = 0

    for regime in REGIMES:
        for seed in SEEDS:
            root = out_root / regime / str(seed)
            meta = build_run(regime, seed, root)
            generation.append(meta)

            verdict = verify_root(root)
            total_violations += len(verdict["violations"])
            total_tokens += verdict["stats"].get("logged_tokens", 0)
            verifications.append({
                "regime": regime,
                "seed": seed,
                "root": str(root),
                "violations": verdict["violations"],
                "stats": {
                    k: verdict["stats"].get(k)
                    for k in ("events", "artifacts", "warrants", "accepted",
                              "refuted", "gate_blocks", "logged_tokens")
                },
            })

            summary = summarize_run(root)
            summary.update({"regime": regime, "seed": seed, "root": str(root)})
            summaries[regime].append(summary)
            print(f"[e03] {regime}/{seed}: events={summary['n_events']} "
                  f"conj={summary['n_conjectures']} blocks={summary['gate_blocks']} "
                  f"dist={summary['contraction_mean_pairwise_dist']:.3f} "
                  f"churn={summary['g_churn']} "
                  f"reinst={summary['reinstatement_rate_raw']} "
                  f"flags={summary['raw_flags_composite']} "
                  f"violations={len(verdict['violations'])}")

    # ------------------------------------------------------------------ #
    # AUC table: detector x pathological regime, vs the healthy arm.      #
    # ------------------------------------------------------------------ #
    def scores(regime: str, detector: str) -> list[float]:
        key, direction = DETECTORS[detector]
        return [direction * s[key] for s in summaries[regime]]

    auc_table: dict[str, dict[str, float]] = {}
    for regime in PATHOLOGICAL:
        auc_table[regime] = {
            det: round(auc(scores(regime, det), scores("healthy", det)), 4)
            for det in DETECTORS
        }

    # ------------------------------------------------------------------ #
    # Verdicts against the literal pre-registered thresholds.            #
    # ------------------------------------------------------------------ #
    p1_auc = auc_table["hard_circling"]["gate_block_rate"]
    p1 = "CONFIRMED" if p1_auc >= 0.95 else "REFUTED"

    p2_hits = {det: a for det, a in auc_table["wrong_but_stable"].items() if a >= 0.7}
    p2 = "CONFIRMED" if not p2_hits else "REFUTED"

    p3_auc = auc_table["soft_basin"]["contraction_mean_pairwise_dist"]
    p3 = "CONFIRMED" if p3_auc >= 0.8 else "REFUTED"

    p4_contraction = auc_table["adversarial_mimicry"]["contraction_mean_pairwise_dist"]
    adj_deltas = {
        det: round(abs(auc_table["adversarial_mimicry"][det]
                       - auc_table["wrong_but_stable"][det]), 4)
        for det in ADJUDICATOR_DETECTORS
    }
    if p4_contraction >= 0.7:
        p4 = "REFUTED"
    elif max(adj_deltas.values()) <= 0.10:
        p4 = "CONFIRMED"
    else:
        p4 = "UNDECIDED"

    verdicts = {
        "P1": {
            "statement": "gate_block_rate separates hard_circling from healthy "
                         "with AUC >= 0.95",
            "auc": p1_auc,
            "threshold": 0.95,
            "verdict": p1,
        },
        "P2": {
            "statement": "(expected to fail) no scored detector separates "
                         "wrong_but_stable from healthy with AUC >= 0.7",
            "threshold": 0.7,
            "detectors_at_or_above_threshold": p2_hits,
            "verdict": p2,
        },
        "P3": {
            "statement": "generator contraction separates soft_basin from "
                         "healthy with AUC >= 0.8",
            "auc_mean_pairwise_dist": p3_auc,
            "auc_dist_slope_secondary": auc_table["soft_basin"]["contraction_dist_slope"],
            "threshold": 0.8,
            "verdict": p3,
        },
        "P4": {
            "statement": "adversarial_mimicry drops the contraction detector "
                         "below AUC 0.7 while wrong_but_stable-style "
                         "adjudicator metrics stay unchanged relative to P2",
            "auc_contraction_mimicry": p4_contraction,
            "auc_contraction_wrong_but_stable":
                auc_table["wrong_but_stable"]["contraction_mean_pairwise_dist"],
            "adjudicator_auc_deltas_mimicry_vs_wrong": adj_deltas,
            "tolerance_operationalized": 0.10,
            "verdict": p4,
        },
    }

    report = {
        "schema": "deepreason-e03-report-v1",
        "prereg": PREREG,
        "date": "2026-07-13",
        "budget": {"llm_tokens_logged_across_all_roots": total_tokens},
        "generation": {
            "method": "real harness registration path (ontology events, genuine "
                       "anti-relapse gate via rules.guards.anti_relapse.check, "
                       "crit_program refutations, argumentative reinstatements); "
                       "no raw JSONL written; fixed topic pools (tides, bridges, "
                       "chess openings, plate tectonics, bronze-age trade); "
                       "parameters jittered by per-run seed",
            "generator": "scripts/e03_synthetic_regimes.py",
            "runner": "scripts/e03_run.py",
            "runs_per_regime": len(SEEDS),
            "seeds": SEEDS,
            "regimes": list(REGIMES),
            "out_root": str(out_root),
            "run_metadata": generation,
        },
        "scoring": {
            "embedder": "HashingEmbedder (production default)",
            "detector_window": "full run (window = event count) for per-run "
                               "summaries; raw_flags at production Config() "
                               "(CAPTURE_W=20)",
            "rate_normalization": "gate blocks and g_churn scaled to per-20-event "
                                  "windows (value * CAPTURE_W / n_events)",
            "directions": {det: ("higher_is_worse" if d > 0 else "lower_is_worse")
                           for det, (_, d) in DETECTORS.items()},
            "imputation": {
                "attack_target_entropy_none": 0.0,
                "reinstatement_rate_none": 0.0,
                "dist_slope_none": 0.0,
            },
            "auc": "Mann-Whitney, ties 0.5, pathological (n=10) vs healthy (n=10)",
        },
        "auc_table": auc_table,
        "per_run_summaries": [s for r in REGIMES for s in summaries[r]],
        "verify_root": {
            "total_violations": total_violations,
            "run_set_valid": total_violations == 0,
            "note": "any violation invalidates the run set and is reported, "
                    "never patched (prereg decision rule)",
            "per_root": verifications,
        },
        "verdicts": verdicts,
        "caveats": [
            "Fixture realism: adjudication schedules are scripted, so regime "
            "definitions themselves (healthy always reinstates; "
            "wrong_but_stable never does) can hand a detector separation that "
            "says nothing about live-run detection power — any "
            "reinstatement_rate/g_churn separation of wrong_but_stable is "
            "construction-driven, not evidence the blind spot is closed.",
            "adversarial_mimicry and wrong_but_stable share one schedule rng "
            "per seed by construction, so P4's 'adjudicator metrics unchanged' "
            "clause is partly guaranteed by the fixture, not discovered.",
            "The mimicry vocabulary was authored to be lexically disjoint; it "
            "attacks the HashingEmbedder's lexical geometry specifically and "
            "says nothing about neural-embedder contraction detectors.",
            "attack_target_entropy is normalized entropy over attack targets; "
            "runs with <2 attacks are imputed to 0.0, which inflates its AUC "
            "on low-adjudication regimes (hard_circling).",
            "criticism_debt is structurally zero in every regime here (all "
            "commitments are evaluable predicates), so its AUC of 0.5 is a "
            "fixture limitation, not a measurement of the detector.",
            "hard_circling has ~30 registration ATTEMPTS but fewer committed "
            "registrations (blocked candidates never register, as in "
            "production).",
        ],
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\n[e03] report -> {REPORT_PATH}")
    print(json.dumps({p: v["verdict"] for p, v in verdicts.items()}, indent=2))
    print(json.dumps(auc_table, indent=2))


if __name__ == "__main__":
    main()
