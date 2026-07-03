"""λ dose-response experiment runner (spec §11.8, P2 acceptance).

Arms differ ONLY in whether the verifier's program criteria are registered
into the loop (λ=full) or withheld (λ=0 — the closed loop). The oracle
(the withheld program commitment) scores outcomes post-hoc in every arm:
oracle-blind, oracle-scored. Thresholds are pre-registered in
experiments/lambda_preregistration.yaml and committed before first look;
the verdict is recorded against the falsifier either way.
"""

import json
import statistics
from pathlib import Path

import yaml

from deepreason import programs
from deepreason.capture import detection
from deepreason.harness import Harness
from deepreason.llm.embedder import HashingEmbedder
from deepreason.ontology import (
    Commitment,
    Problem,
    ProblemProvenance,
)
from deepreason.scheduler.scheduler import Scheduler


def run_arm(
    root: Path,
    *,
    program_criteria_in_loop: bool,
    oracle_eval: str,
    problem_description: str,
    adapter,
    config,
    cycles: int,
) -> dict:
    harness = Harness(root)
    criteria: list[str] = []
    if program_criteria_in_loop:
        harness.register_commitment(Commitment(id="oracle", eval=oracle_eval))
        criteria = ["oracle"]
    harness.register_problem(
        Problem(
            id="pi-arm",
            description=problem_description,
            criteria=criteria,
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    embedder = HashingEmbedder()
    scheduler = Scheduler(harness, adapter, config, embedder=embedder)
    report = scheduler.run(cycles)

    # Post-hoc oracle scoring: the withheld verifier judges every conjecture.
    oracle = Commitment(id="oracle-posthoc", eval=oracle_eval)
    conjectures = [
        a
        for a in harness.state.artifacts.values()
        if a.provenance.role.value in ("conjecturer", "synthesizer")
    ]
    oracle_pass = (
        sum(
            1
            for a in conjectures
            if programs.evaluate(oracle, a, harness.blobs)[0] == programs.PASS
        )
        / len(conjectures)
        if conjectures
        else 0.0
    )
    window = config.CAPTURE_W
    return {
        "generator": detection.generator_metrics(harness, embedder, window),
        "adjudicator": detection.adjudicator_metrics(harness, window),
        "lambda": detection.grounding_lambda(harness, window),
        "oracle_pass_rate": oracle_pass,
        "n_conjectures": len(conjectures),
        "survivors": len(report["survivors"]),
    }


def _distribution(values: list[float | None]) -> dict:
    xs = [v for v in values if v is not None]
    if not xs:
        return {"n": 0}
    return {
        "n": len(xs),
        "mean": statistics.mean(xs),
        "min": min(xs),
        "max": max(xs),
        "values": xs,  # distributions, not means (§11.8)
    }


def summarize(arm_results: dict[str, list[dict]]) -> dict:
    """Both-surface metrics as distributions per arm."""
    out: dict[str, dict] = {}
    for arm, runs in arm_results.items():
        out[arm] = {
            "oracle_pass_rate": _distribution([r["oracle_pass_rate"] for r in runs]),
            "mean_pairwise_dist": _distribution(
                [r["generator"]["mean_pairwise_dist"] for r in runs]
            ),
            "dist_slope": _distribution([r["generator"]["dist_slope"] for r in runs]),
            "attack_target_entropy": _distribution(
                [r["adjudicator"]["attack_target_entropy"] for r in runs]
            ),
            "criticism_debt": _distribution(
                [r["adjudicator"]["criticism_debt"] for r in runs]
            ),
            "lambda": _distribution([r["lambda"] for r in runs]),
        }
    return out


def verdict(summary: dict, preregistration_path: Path) -> dict:
    """Score the pre-registered falsifier; record the outcome either way."""
    prereg = yaml.safe_load(preregistration_path.read_text())
    thresholds = prereg["thresholds"]
    full = summary["lambda_full"]["oracle_pass_rate"].get("mean", 0.0)
    closed = summary["lambda0"]["oracle_pass_rate"].get("mean", 0.0)
    gap = full - closed
    falsified = gap < thresholds["oracle_gap_min"]
    return {
        "oracle_gap": gap,
        "oracle_gap_min": thresholds["oracle_gap_min"],
        "falsifier_triggered": falsified,
        "reading": (
            "anchoring as built does NOT earn the exemption (lambda_full tracks lambda0)"
            if falsified
            else "anchoring earns the exemption on this problem set"
        ),
    }


def record(report_path: Path, summary: dict, verdict_result: dict) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps({"summary": summary, "verdict": verdict_result}, indent=2, sort_keys=True)
    )
