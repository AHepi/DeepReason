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

    def passes(artifact) -> bool:
        return programs.evaluate(oracle, artifact, harness.blobs)[0] == programs.PASS

    conjectures = [
        a
        for a in harness.state.artifacts.values()
        if a.provenance.role.value in ("conjecturer", "synthesizer")
    ]
    oracle_pass = (
        sum(1 for a in conjectures if passes(a)) / len(conjectures)
        if conjectures
        else 0.0
    )
    # v2 primary metric: distinct registered seed-problem candidates that
    # pass — a count, immune to side-problem dilution (prereg v2).
    seed_candidates = [
        harness.state.artifacts[aid]
        for aid, pid in harness.state.addr
        if pid == "pi-arm"
        and harness.state.artifacts[aid].provenance.role.value
        in ("conjecturer", "synthesizer")
    ]
    seed_passes = sum(1 for a in seed_candidates if passes(a))
    gate_blocks = sum(
        1
        for d in scheduler.diagnostics
        if str(d.get("gate", "")).startswith(("hash", "battery-equivalent"))
    )
    window = config.CAPTURE_W
    return {
        "generator": detection.generator_metrics(harness, embedder, window),
        "adjudicator": detection.adjudicator_metrics(harness, window),
        "lambda": detection.grounding_lambda(harness, window),
        "oracle_pass_rate": oracle_pass,
        "oracle_passes": seed_passes,
        "oracle_pass_rate_seed": (
            seed_passes / len(seed_candidates) if seed_candidates else 0.0
        ),
        "gate_blocks": gate_blocks,
        "n_conjectures": len(conjectures),
        "n_seed_candidates": len(seed_candidates),
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
        # v2 metrics, when the runs carry them (prereg v2).
        for key in ("oracle_passes", "oracle_pass_rate_seed", "gate_blocks"):
            if all(key in r for r in runs):
                out[arm][key] = _distribution([float(r[key]) for r in runs])
    return out


def verdict(summary: dict, preregistration_path: Path) -> dict:
    """Score the pre-registered falsifier; record the outcome either way.
    The primary metric and gap threshold come from the registration file,
    so an amendment is a new file, never a code change after first look."""
    prereg = yaml.safe_load(preregistration_path.read_text())
    thresholds = prereg["thresholds"]
    metric = prereg.get("primary_metric", "oracle_pass_rate")
    gap_min = thresholds.get("gap_min", thresholds.get("oracle_gap_min"))
    full = summary["lambda_full"][metric].get("mean", 0.0)
    closed = summary["lambda0"][metric].get("mean", 0.0)
    gap = full - closed
    falsified = gap < gap_min
    return {
        "preregistration": preregistration_path.name,
        "metric": metric,
        "gap": gap,
        "gap_min": gap_min,
        "oracle_gap": gap,  # kept for continuity with the pilot report
        "oracle_gap_min": gap_min,
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
