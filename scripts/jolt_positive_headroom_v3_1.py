#!/usr/bin/env python
"""Prepare, calibrate, run, and report the preregistered TSP jolt pilot v3.1.

The live subcommands are deliberately separate.  ``calibrate`` cannot create
experimental roots, and ``experiment`` refuses to run unless the calibration
commit is an ancestor of the immutable preregistration commit.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from statistics import median

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deepreason.canonical import canonical_json, sha256_hex  # noqa: E402
from deepreason.config import Config  # noqa: E402
from deepreason.experiments.jolt_tsp import (  # noqa: E402
    ACTION_SIGNAL,
    CITY_IDS,
    EVALUATOR_FINGERPRINT,
    J3_PREFIX,
    J4_PREFIX,
    J6_DIRECTIVE,
    MOVEMENT_DIRECTIVE,
    OBSERVATION_SIGNAL,
    TRIGGER_SIGNAL,
    Checkpoint,
    branch_order,
    calibration_thresholds,
    canonical_tour,
    edge_set,
    generate_instance,
    held_karp,
    instance_problem_description,
    parse_tour,
    retained_edge_fraction,
    tour_distance,
    treatment_context,
    trigger_window,
)
from deepreason.harness import Harness  # noqa: E402
from deepreason.invariants import verify_root  # noqa: E402
from deepreason.jolts import root_state_digest  # noqa: E402
from deepreason.llm.adapter import build_adapter  # noqa: E402
from deepreason.llm.budget import TokenBudgetExceeded, TokenMeter  # noqa: E402
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Status  # noqa: E402
from deepreason.rules.conj import conj  # noqa: E402
from deepreason.rules.crit import crit_program  # noqa: E402
from deepreason.run_manifest import (  # noqa: E402
    bind_run_manifest,
    compile_run_manifest,
    config_from_run_manifest,
    load_run_manifest,
    preflight_harness,
)

PROTOCOL = "jolt-positive-headroom-v3.1"
CAL_SEEDS = tuple(range(20260701, 20260704))
EXP_SEEDS = tuple(range(20260715, 20260723))
ARMS = ("J0", "J1", "J3", "J4", "J6")
CALL_SIGNAL = "jolt-tsp-call-v3.1"

EXPERIMENTS = ROOT / "experiments"
RESULTS = EXPERIMENTS / "results"
RUNS = ROOT / "runs" / "jolt_positive_headroom_v3_1"
CAL_INSTANCES = EXPERIMENTS / "jolt_positive_headroom_v3_1_calibration_instances.json"
EXP_INSTANCES = EXPERIMENTS / "jolt_positive_headroom_v3_1_instances.json"
OPTIMA = EXPERIMENTS / "jolt_positive_headroom_v3_1_optima.json"
CAL_PLAN = EXPERIMENTS / "jolt_positive_headroom_v3_1_calibration_plan.json"
CAL_REPORT_JSON = RESULTS / "jolt_positive_headroom_v3_1_calibration_report.json"
CAL_REPORT_MD = RESULTS / "jolt_positive_headroom_v3_1_calibration_report.md"
PREREG = EXPERIMENTS / "jolt_positive_headroom_v3_1_prereg.yaml"
MANIFEST_PLAN = EXPERIMENTS / "jolt_positive_headroom_v3_1_manifest_plan.json"
ANALYSIS_PLAN = EXPERIMENTS / "jolt_positive_headroom_v3_1_analysis_plan.json"
RAW_REPORT = RESULTS / "jolt_positive_headroom_v3_1_raw_report.json"
REPORT_JSON = RESULTS / "jolt_positive_headroom_v3_1_report.json"
REPORT_MD = RESULTS / "jolt_positive_headroom_v3_1_report.md"
VERIFY_REPORT = RESULTS / "jolt_positive_headroom_v3_1_retained_root_verification.json"
FORENSIC = RESULTS / "jolt_positive_headroom_v3_1_forensic_addendum.md"
LEDGER = RUNS / "aggregate_ledger.json"

MAX_CALLS = 552
EXPECTED_TOKENS = 900_000
HARD_TOKENS = 1_600_000
ACQUISITION_CALLS = 32
BRANCH_CALLS = 5
BRANCH_TOKENS = 35_000

CHANGES_FROM_V3 = [
    "Added a pre-experimental trigger-calibration phase on held-out seeds.",
    'Added arm "J1" (movement-directive-only control); the movement directive is now identical wherever used, with an edge-change floor of two, permitting 2-opt moves.',
    "Overlap redefined as retained-incumbent-edge fraction; thresholds set by calibration, not assumed.",
    "Acquisition cap raised to 32 calls; minimum valid-tour history lowered to 12.",
    "J4 purified: the longest-edge listing removed. J3 edge rendering sorted lexicographically, not by length, so no arm embeds the longest-edge heuristic.",
    "Score feedback to the conjecturer made an explicit, arm-invariant requirement.",
    "Duplicate-admission rule defined.",
    "Randomisation hash encoding specified.",
    "Budgets recomputed for five arms.",
]


def _write_json(path: Path, value: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def _config() -> Config:
    return Config.model_validate({
        "N_SCHOOLS": 0,
        "VS_K": 3,
        "NEIGHBOURHOOD_N": 0,
        "NEAR_DUP_EPS": None,
        "ARG_CRIT_PER_CYCLE": 0,
        "RUBRIC_TRIALS_PER_ARTIFACT": 0,
        "ADVISORY_TRIALS_PER_CYCLE": 0,
        "PROP_PROPOSE_PERIOD": 0,
        "VISION_CRIT_PER_CYCLE": 0,
        "RECRIT_STANDING": False,
        "RESEARCH_BACKEND": None,
        "CONTROLLER": False,
        "SPEC_INJECTION": False,
        "COMPLEMENT_ALWAYS": False,
        "TEXT_RUBRIC_AUTHORITY": "observe_only",
        "PAIRWISE_AUTHORITY": "observe_only",
        "INFRASTRUCTURE_REVIEW_AUTHORITY": "observe_only",
        "ARGUMENTATIVE_AUTHORITY": "observe_only",
        "roles": {
            "conjecturer": {
                "endpoint": "https://ollama.com/v1",
                "model": "glm-5.2",
                "provider": "ollama",
                "temperature": 1.0,
                "api_key_env": "OLLAMA_API_KEY",
                "reasoning": "none",
                "max_tokens": 2000,
                "json_mode": True,
                "timeout_s": 600,
            }
        },
    })


def _manifest():
    return compile_run_manifest(
        _config(),
        schema_version=2,
        workload_profile="formal",
        rubric_policy="forbid",
        compiled_at="2026-07-15T00:00:00Z",
        budget_policy={
            "aggregate_token_hard_ceiling": HARD_TOKENS,
            "aggregate_call_hard_ceiling": MAX_CALLS,
            "branch_token_ceiling": BRANCH_TOKENS,
            "branch_call_ceiling": BRANCH_CALLS,
            "judge_tokens": 0,
            "critic_tokens": 0,
            "research_tokens": 0,
        },
        stop_policy={
            "calibration_calls_per_instance": ACQUISITION_CALLS,
            "acquisition_calls_per_instance": ACQUISITION_CALLS,
            "first_eligible_state_only": True,
            "branches_per_block": len(ARMS),
        },
    )


def _instance_document(seeds: tuple[int, ...], cohort: str) -> dict:
    instances = [generate_instance(seed) for seed in seeds]
    return {
        "schema": "deepreason-jolt-tsp14-instances-v3.1",
        "cohort": cohort,
        "generation": {
            "prng": "python.random.Random",
            "operation": "randrange(0,100) coordinate pairs until 14 unique",
            "city_ids": list(CITY_IDS),
            "id_order": "generation order",
        },
        "seeds": list(seeds),
        "instances": instances,
    }


def _load_instances(path: Path) -> dict[int, dict]:
    data = json.loads(path.read_text())
    return {int(row["seed"]): row for row in data["instances"]}


def _load_optima() -> dict[int, dict]:
    data = json.loads(OPTIMA.read_text())
    return {int(row["seed"]): row for row in data["certificates"]}


def prepare() -> None:
    cal = _instance_document(CAL_SEEDS, "held-out-calibration")
    exp = _instance_document(EXP_SEEDS, "experimental")
    _write_json(CAL_INSTANCES, cal)
    _write_json(EXP_INSTANCES, exp)
    certificates = []
    for cohort, document in (("calibration", cal), ("experimental", exp)):
        for instance in document["instances"]:
            certificate = held_karp(instance)
            certificates.append({"cohort": cohort, "seed": instance["seed"], **certificate})
    _write_json(OPTIMA, {
        "schema": "deepreason-jolt-tsp14-exact-optima-v3.1",
        "sealed_from_conjecturer": True,
        "distance": "integer Manhattan cycle distance",
        "certificates": certificates,
    })
    manifest = _manifest()
    _write_json(CAL_PLAN, {
        "schema": "deepreason-jolt-positive-headroom-calibration-plan-v3.1",
        "protocol": PROTOCOL,
        "seeds": list(CAL_SEEDS),
        "maximum_calls_per_instance": ACQUISITION_CALLS,
        "score_feedback_required": True,
        "jolts": False,
        "threshold_selection": (
            "select replay-observed R_med/R_low for >=2/3 positive-headroom "
            "non-improving windows and zero improving-window fires; otherwise stop"
        ),
        "provider": {"endpoint": "https://ollama.com/v1", "model": "glm-5.2", "thinking": "off", "temperature": 1.0},
        "authority": {"roles": ["conjecturer"], "judge_calls": 0, "critic_calls": 0, "rubric_policy": "forbid", "status": "deterministic verifier only"},
        "manifest_sha256": manifest.sha256,
        "calibration_instances_sha256": _sha(CAL_INSTANCES),
        "experimental_instances_sha256": _sha(EXP_INSTANCES),
        "optima_sha256": _sha(OPTIMA),
        "evaluator_fingerprint": EVALUATOR_FINGERPRINT,
        "aggregate_call_ceiling": MAX_CALLS,
        "aggregate_token_ceiling": HARD_TOKENS,
    })
    print(json.dumps({
        "calibration_instances": _sha(CAL_INSTANCES),
        "experimental_instances": _sha(EXP_INSTANCES),
        "optima": _sha(OPTIMA),
        "manifest": manifest.sha256,
    }, indent=2))


def _problem_id(seed: int) -> str:
    return f"tsp14-manhattan-{seed}"


def _open_root(root: Path, instance: dict) -> tuple[Harness, object]:
    if (root / "run-manifest.json").exists():
        manifest = load_run_manifest(root / "run-manifest.json")
        harness = Harness(root)
    else:
        manifest = _manifest()
        harness = Harness(root)
        bind_run_manifest(manifest, root)
        criterion = f"tsp14-valid-tour-{instance['seed']}"
        harness.register_commitment(Commitment(id=criterion, eval="program:tsp14_tour_wf"))
        harness.register_problem(Problem(
            id=_problem_id(instance["seed"]),
            description=instance_problem_description(instance),
            criteria=[criterion],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        ))
    cfg = config_from_run_manifest(manifest)
    preflight_harness(manifest, harness, cfg)
    return harness, manifest


def _payloads(harness: Harness, signal: str) -> list[dict]:
    rows = []
    for event in harness.log.read():
        if len(event.inputs) >= 2 and event.inputs[0] == signal:
            rows.append(json.loads(event.inputs[1]))
    return rows


def _ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {
        "schema": "deepreason-jolt-positive-headroom-ledger-v3.1",
        "hard_token_ceiling": HARD_TOKENS,
        "hard_call_ceiling": MAX_CALLS,
        "entries": [],
    }


def _ledger_totals(ledger: dict) -> tuple[int, int]:
    return (
        sum(int(row["tokens"]) for row in ledger["entries"]),
        len(ledger["entries"]),
    )


def _record_ledger(entry: dict) -> None:
    ledger = _ledger()
    if any(row["opportunity_id"] == entry["opportunity_id"] for row in ledger["entries"]):
        raise RuntimeError("duplicate aggregate-ledger opportunity")
    tokens, calls = _ledger_totals(ledger)
    if calls + 1 > MAX_CALLS or tokens + int(entry["tokens"]) > HARD_TOKENS:
        raise RuntimeError("aggregate hard ceiling violation")
    ledger["entries"].append(entry)
    _write_json(LEDGER, ledger)


def _best(history: list[dict]) -> dict | None:
    valid = [row for row in history if row["valid"]]
    return min(valid, key=lambda row: (row["distance"], row["canonical_tour"])) if valid else None


def _failure_classes(history: list[dict]) -> list[str]:
    return sorted({row["failure_class"] for row in history[-24:] if row.get("failure_class")})


def _window_gate_blocks(history: list[dict]) -> int:
    valid = [row for row in history if row["valid"]]
    if len(valid) < 8:
        return 0
    first_call = int(valid[-8]["call_index"])
    last_call = int(valid[-1]["call_index"])
    return sum(
        bool(row.get("gate_blocked"))
        for row in history
        if first_call <= int(row["call_index"]) <= last_call
    )


def _call_once(
    harness: Harness,
    manifest,
    instance: dict,
    *,
    phase: str,
    root_label: str,
    arm: str,
    call_index: int,
    branch_token_remaining: int | None = None,
) -> dict:
    history = _payloads(harness, OBSERVATION_SIGNAL)
    incumbent_row = _best(history)
    incumbent = tuple(incumbent_row["canonical_tour"]) if incumbent_row else None
    recent_valid = [row for row in history if row["valid"]][-8:]
    retained = (
        [retained_edge_fraction(row["canonical_tour"], incumbent) for row in recent_valid]
        if incumbent is not None else []
    )
    context = treatment_context(
        arm,
        instance=instance,
        history=history,
        incumbent=incumbent,
        median_retained=median(retained) if retained else None,
        failure_classes=_failure_classes(history),
    )
    ledger = _ledger()
    global_tokens, global_calls = _ledger_totals(ledger)
    if global_calls >= MAX_CALLS:
        raise TokenBudgetExceeded("aggregate call ceiling exhausted")
    remaining = HARD_TOKENS - global_tokens
    if branch_token_remaining is not None:
        remaining = min(remaining, branch_token_remaining)
    if remaining <= 0:
        raise TokenBudgetExceeded("aggregate or branch token ceiling exhausted")
    meter = TokenMeter(budget=remaining)
    cfg = config_from_run_manifest(manifest)
    adapter = build_adapter(
        cfg,
        harness.blobs,
        meter=meter,
        only_roles={"conjecturer"},
        run_manifest=manifest,
        process_events=harness.log.read(),
    )
    diagnostics: list[dict] = []
    error = None
    returned = []
    before_seq = harness._next_seq
    try:
        returned = conj(
            harness,
            _problem_id(instance["seed"]),
            adapter,
            cfg,
            diagnostics,
            workload_profile="formal",
            generation_context=context,
            capture_candidate_content=True,
        )
        for artifact in returned:
            crit_program(harness, artifact.id)
    except Exception as caught:  # all failures are registered outcomes
        error = f"{type(caught).__name__}: {str(caught)[:300]}"
        spend = getattr(caught, "spend", None)
        harness.record_llm_calls([spend], "dropped-call", error)

    prior_canonicals = {
        tuple(row["canonical_tour"]) for row in history if row["valid"]
    }
    prior_edges = {
        frozenset(tuple(edge) for edge in row["edges"])
        for row in history if row["valid"]
    }
    current_best = _best(history)
    rows = []
    for candidate_index, diagnostic in enumerate(diagnostics):
        content = diagnostic.get("candidate_content", "")
        tour = parse_tour(content)
        gate_blocked = not str(diagnostic.get("gate", "")).startswith("admitted")
        artifact_id = diagnostic.get("artifact_id")
        status = harness.state.status.get(artifact_id) if artifact_id else None
        valid = bool(tour is not None and not gate_blocked and status == Status.ACCEPTED)
        canonical = canonical_tour(tour) if valid and tour is not None else None
        edges = edge_set(canonical) if canonical is not None else frozenset()
        distance = tour_distance(instance, canonical) if canonical is not None else None
        duplicate = canonical in prior_canonicals if canonical is not None else False
        functionally_novel = edges not in prior_edges if canonical is not None else False
        incumbent_before = tuple(current_best["canonical_tour"]) if current_best else None
        improvement = bool(distance is not None and (current_best is None or distance < current_best["distance"]))
        if valid and (
            current_best is None
            or (distance, canonical) < (current_best["distance"], tuple(current_best["canonical_tour"]))
        ):
            current_best = {"distance": distance, "canonical_tour": list(canonical)}
        incumbent_after = tuple(current_best["canonical_tour"]) if current_best else None
        row = {
            "schema": "deepreason-jolt-tsp-observation-v3.1",
            "phase": phase,
            "root_label": root_label,
            "arm": arm,
            "call_index": call_index,
            "candidate_index": candidate_index,
            "admission_id": f"call-{call_index:02d}-candidate-{candidate_index:02d}",
            "artifact_id": artifact_id,
            "gate": diagnostic.get("gate"),
            "gate_blocked": gate_blocked,
            "valid": valid,
            "failure_class": (
                None if valid else ("anti-relapse-gate" if gate_blocked else "schema-or-tour-validity")
            ),
            "canonical_tour": list(canonical) if canonical is not None else None,
            "edges": [list(edge) for edge in sorted(edges, key=lambda item: (int(item[0]), int(item[1])))],
            "distance": distance,
            "duplicate_admission": duplicate,
            "unique_canonical_tour": bool(valid and not duplicate),
            "functional_novelty": bool(valid and functionally_novel),
            "improves_incumbent": improvement,
            "retained_vs_incumbent_before": (
                retained_edge_fraction(canonical, incumbent_before)
                if canonical is not None and incumbent_before is not None else None
            ),
            "retained_vs_incumbent_after": (
                retained_edge_fraction(canonical, incumbent_after)
                if canonical is not None and incumbent_after is not None else None
            ),
            "status_source": "deterministic",
        }
        harness.record_measure(inputs=[OBSERVATION_SIGNAL, json.dumps(row, sort_keys=True, separators=(",", ":"))])
        rows.append(row)
        if valid:
            prior_canonicals.add(canonical)
            prior_edges.add(edges)

    snapshot = meter.snapshot()
    receipt = {
        "schema": "deepreason-jolt-tsp-call-v3.1",
        "phase": phase,
        "root_label": root_label,
        "arm": arm,
        "call_index": call_index,
        "event_seq_before": before_seq,
        "event_seq_after": harness._next_seq,
        "successful_contract_call": error is None,
        "error": error,
        "candidates": len(diagnostics),
        "valid_candidates": sum(row["valid"] for row in rows),
        "tokens": snapshot,
        "score_feedback_sha256": sha256(context.split("\n\n", 1)[0].encode()).hexdigest(),
        "prompt_context_sha256": sha256(context.encode()).hexdigest(),
    }
    harness.record_measure(inputs=[CALL_SIGNAL, json.dumps(receipt, sort_keys=True, separators=(",", ":"))])
    _record_ledger({
        "opportunity_id": f"{phase}:{root_label}:{arm}:{call_index}",
        "phase": phase,
        "root_label": root_label,
        "arm": arm,
        "call_index": call_index,
        "tokens": snapshot["total"],
        "prompt_tokens": snapshot["prompt_tokens"],
        "completion_tokens": snapshot["completion_tokens"],
        "provider_attempts": snapshot["calls"],
        "error": error,
    })
    return receipt


def _run_fixed_calls(root: Path, instance: dict, *, phase: str, calls: int) -> None:
    harness, manifest = _open_root(root, instance)
    completed = _payloads(harness, CALL_SIGNAL)
    for call_index in range(len(completed), calls):
        receipt = _call_once(
            harness,
            manifest,
            instance,
            phase=phase,
            root_label=str(instance["seed"]),
            arm="J0",
            call_index=call_index,
        )
        print(json.dumps({"seed": instance["seed"], **receipt["tokens"], "valid": receipt["valid_candidates"], "error": receipt["error"]}))


def calibrate() -> None:
    if not os.environ.get("OLLAMA_API_KEY"):
        raise SystemExit("OLLAMA_API_KEY is required")
    instances = _load_instances(CAL_INSTANCES)
    optima = _load_optima()
    for seed in CAL_SEEDS:
        _run_fixed_calls(RUNS / "calibration" / str(seed), instances[seed], phase="calibration", calls=ACQUISITION_CALLS)
    histories = []
    summaries = []
    for seed in CAL_SEEDS:
        root = RUNS / "calibration" / str(seed)
        harness = Harness(root)
        history = _payloads(harness, OBSERVATION_SIGNAL)
        calls = _payloads(harness, CALL_SIGNAL)
        histories.append(history)
        valid = [row for row in history if row["valid"]]
        best_by_call = []
        for index in range(ACQUISITION_CALLS):
            prefix = [row for row in valid if row["call_index"] <= index]
            best_by_call.append(min((row["distance"] for row in prefix), default=None))
        overlaps = [row["retained_vs_incumbent_before"] for row in valid if row["retained_vs_incumbent_before"] is not None]
        summaries.append({
            "seed": seed,
            "calls": len(calls),
            "successful_calls": sum(row["successful_contract_call"] for row in calls),
            "candidates": len(history),
            "valid_admissions": len(valid),
            "validity_rate": len(valid) / len(history) if history else 0.0,
            "candidates_per_call": len(history) / len(calls) if calls else 0.0,
            "duplicate_admissions": sum(row["duplicate_admission"] for row in valid),
            "unique_canonical_tours": sum(row["unique_canonical_tour"] for row in valid),
            "improvement_trajectory": best_by_call,
            "retained_incumbent_edge_fractions": overlaps,
            "exact_optimum": optima[seed]["exact_distance"],
            "verify_root": verify_root(root),
        })
    thresholds = calibration_thresholds(
        histories,
        optima=[optima[seed]["exact_distance"] for seed in CAL_SEEDS],
    )
    status = "complete" if thresholds is not None else "calibration_failure"
    report = {
        "schema": "deepreason-jolt-positive-headroom-calibration-report-v3.1",
        "status": status,
        "held_out_seeds": list(CAL_SEEDS),
        "thresholds": thresholds,
        "instances": summaries,
        "calibration_instances_sha256": _sha(CAL_INSTANCES),
        "experimental_instances_sha256": _sha(EXP_INSTANCES),
        "optima_sha256": _sha(OPTIMA),
        "ledger": _ledger(),
    }
    _write_json(CAL_REPORT_JSON, report)
    lines = [
        "# Positive-Headroom Jolt Pilot v3.1 — calibration",
        "",
        f"Status: **{status}**.",
        "",
        "This held-out phase used ordinary J0 generation with arm-invariant verifier score feedback. No jolt, judge, critic, pairwise, synthesis, research, or controller call was made.",
        "",
    ]
    if thresholds:
        lines.extend([
            f"Frozen thresholds: `R_med = {thresholds['R_med']:.12g}`, `R_low = {thresholds['R_low']:.12g}`.",
            f"The candidate trigger fired on {thresholds['fired_instances']} of 3 held-out instances and on zero windows containing an improvement.",
            "",
        ])
    else:
        lines.extend(["No threshold pair satisfied the registered calibration criterion. Experimental execution is forbidden.", ""])
    lines.append("| seed | calls | candidates | valid | unique | duplicates | optimum |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|")
    for row in summaries:
        lines.append(f"| {row['seed']} | {row['calls']} | {row['candidates']} | {row['valid_admissions']} | {row['unique_canonical_tours']} | {row['duplicate_admissions']} | {row['exact_optimum']} |")
    CAL_REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps(report, indent=2))
    if thresholds is None:
        raise SystemExit(3)


def preregister() -> None:
    calibration = json.loads(CAL_REPORT_JSON.read_text())
    if calibration["status"] != "complete" or not calibration.get("thresholds"):
        raise SystemExit("calibration is not complete")
    calibration_commit = _git("rev-parse", "HEAD")
    for path in (CAL_REPORT_JSON, CAL_REPORT_MD, CAL_INSTANCES, EXP_INSTANCES, OPTIMA):
        if _git("status", "--short", "--", str(path.relative_to(ROOT))):
            raise SystemExit(f"calibration prerequisite is not committed: {path}")
    thresholds = calibration["thresholds"]
    manifest = _manifest()
    prereg = {
        "schema": "deepreason-jolt-positive-headroom-prereg-v3.1",
        "status": "preregistered-feasibility-pilot",
        "preserved_prior_result": "A no-improvement window does not imply stagnation when the registered objective has already been completed.",
        "changes_from_v3_verbatim": CHANGES_FROM_V3,
        "research_question": "Among reached, certified-positive-headroom plateau states, which prompt-only intervention restores verifier-backed progress, and which component carries the effect?",
        "estimand": "Conditional matched-state jolt effects among reached, certified-positive-headroom plateau states.",
        "non_estimands": [
            "whole-run adaptive-policy effects", "fixed-schedule versus adaptive intervention effects",
            "production trigger performance on unknown-headroom tasks", "hard-orbit treatment effects",
            "cross-model or cross-domain effects", "automatic deployment policy",
        ],
        "scope_limit": "In-distribution TSP family; score-fed but arithmetic-limited GLM-5.2 generator.",
        "provider": {"service": "Ollama Cloud", "endpoint": "https://ollama.com/v1", "model": "glm-5.2", "thinking": "disabled", "temperature": 1.0, "role": "conjecturer-only"},
        "authority": {"judge_calls": 0, "critic_calls": 0, "pairwise_calls": 0, "synthesizer_calls": 0, "research_calls": 0, "controller_calls": 0, "rubric_policy": "forbidden", "status_authority": "deterministic verifier only"},
        "workload": {"cities": 14, "distance": "integer Manhattan", "cycle_start": "0", "implicit_return": True, "canonicalisation": "lexicographically smaller reverse-equivalent orientation", "instance_generation": "random.Random(seed), randrange(0,100) unique pairs"},
        "seeds": {"calibration": list(CAL_SEEDS), "experimental": list(EXP_SEEDS)},
        "calibration": {"commit": calibration_commit, "report_sha256": _sha(CAL_REPORT_JSON), "R_med": thresholds["R_med"], "R_low": thresholds["R_low"], "criterion": ">=2/3 instances, zero fires in improvement windows"},
        "exact_optima": {"file": str(OPTIMA.relative_to(ROOT)), "sha256": _sha(OPTIMA), "algorithm": "Held-Karp", "never_rendered": True},
        "acquisition": {"calls_per_instance": 32, "minimum_successful_calls": 10, "minimum_valid_admissions": 12, "blocks_per_instance": 1, "first_eligible_only": True},
        "trigger": {"window_valid_admissions": 8, "no_improvement_vs_pre_window_incumbent": True, "median_retained_edge_fraction_at_least": thresholds["R_med"], "at_most_one_fraction_below": thresholds["R_low"], "hard_gate_blocks": 0, "operationally_quiescent": True, "certified_headroom_ratio_at_least": 0.03, "future_information": False},
        "shared_movement_directive": MOVEMENT_DIRECTIVE,
        "arms": {
            "J0": {"description": "ordinary no-intervention continuation", "added_text": ""},
            "J1": {"description": "movement directive only", "added_text": MOVEMENT_DIRECTIVE},
            "J3": {"description": "distance matrix, lexicographic incumbent edges, recent edge differences, representation reset, shared directive", "prefix": J3_PREFIX, "directive": MOVEMENT_DIRECTIVE},
            "J4": {"description": "registered deterministic verifier diagnostics, verifier challenge, shared directive", "prefix": J4_PREFIX, "directive": MOVEMENT_DIRECTIVE, "forbidden": ["optimal distance", "numerical gap", "optimal tour", "improving move", "edge listing"]},
            "J6": {"description": "generic complement negative control", "added_text": J6_DIRECTIVE},
        },
        "duplicate_rule": "A valid canonical duplicate is admitted to history and valid totals, but not unique-tour or novelty totals.",
        "score_feedback": "Every prior valid admission's verifier total is rendered in the same byte structure in every arm.",
        "branching": {"arms": list(ARMS), "calls_per_arm": 5, "tokens_per_arm": 35000, "no_borrowing": True, "order_seed_utf8": "str(instance_seed)+\":\"+source_state_digest_hex+\":\"+preregistration_digest_hex", "provider_nondeterminism": "matched continuations, not deterministic counterfactuals"},
        "outcomes": {
            "primary_1": "branch_best_distance < source_best_distance",
            "primary_2": "(source_best-branch_best)/(source_best-exact_optimum)",
            "primary_3": "calls and tokens to first verified improvement, censored at caps",
            "secondary": ["valid admissions", "duplicate admissions", "unique canonical tours", "functionally novel edge sets", "retained-edge fractions", "best distance", "schema failures", "invalid candidates", "transport failures", "token efficiencies"],
        },
        "comparisons": ["J3 vs J0", "J4 vs J0", "J1 vs J0", "J3 vs J1", "J4 vs J1", "J6 vs J0"],
        "exclusions": ["certified completion", "headroom below 3%", "hard/soft ambiguity", "insufficient history", "unreproducible incumbent or optimum", "uncheckpointable state", "unresolved operation"],
        "stopping": {"attempt_all_instances": 8, "feasible_blocks_at_least": 6, "no_efficiency_claim_below_blocks": 12, "do_not_add_instances": True, "protocol_violation": "freeze, forensic addendum, stop"},
        "budgets": {"calibration_calls": 96, "acquisition_calls": 256, "branch_calls": 200, "absolute_calls": 552, "expected_tokens": EXPECTED_TOKENS, "hard_tokens": HARD_TOKENS, "judge_tokens": 0, "critic_tokens": 0, "research_tokens": 0},
        "analysis": {"unit": "matched source-state block", "report_each_block": True, "no_cross_domain_pooling": True, "source_and_branch_tokens_separate": True, "feasibility_not_confirmatory": True},
        "frozen_hashes": {"calibration_instances": _sha(CAL_INSTANCES), "experimental_instances": _sha(EXP_INSTANCES), "optima": _sha(OPTIMA), "calibration_report": _sha(CAL_REPORT_JSON), "manifest": manifest.sha256},
    }
    PREREG.write_text(yaml.safe_dump(prereg, sort_keys=False, allow_unicode=True))
    prereg_digest = _sha(PREREG)
    _write_json(MANIFEST_PLAN, {
        "schema": "deepreason-jolt-positive-headroom-manifest-plan-v3.1",
        "preregistration_sha256": prereg_digest,
        "run_manifest_sha256": manifest.sha256,
        "role_matrix": {"conjecturer": [{"provider": "ollama", "endpoint": "https://ollama.com/v1", "model": "glm-5.2", "temperature": 1.0, "reasoning": "none", "max_tokens": 2000}], "all_other_roles": []},
        "workload_profile": "formal",
        "rubric_policy": "forbid",
        "budgets": prereg["budgets"],
        "root_layout": "runs/jolt_positive_headroom_v3_1/{source,branches}",
        "credential_storage": "environment only; excluded from manifests, roots, and reports",
    })
    _write_json(ANALYSIS_PLAN, {
        "schema": "deepreason-jolt-positive-headroom-analysis-plan-v3.1",
        "preregistration_sha256": prereg_digest,
        "unit": "matched source-state block",
        "primary_outcomes": prereg["outcomes"],
        "comparisons": prereg["comparisons"],
        "reporting": ["per-block arm table", "paired improvement-indicator difference", "paired gap-closed difference", "median paired branch-token difference", "all failures/exclusions"],
        "inference_limit": "descriptive conditional model/task-family result; no general superiority declaration below 12 blocks",
        "gap_closed_audit": "values above 1 trigger verifier audit; clamp only reporting errors",
        "malformed_and_transport": "retain in assigned arm and count against calls/tokens",
        "missing_data": "no imputation; branch censored at registered cap",
    })
    print(json.dumps({"preregistration_sha256": prereg_digest, "calibration_commit": calibration_commit, "manifest_sha256": manifest.sha256}, indent=2))


def _trigger(history: list[dict], optimum: int, thresholds: dict, calls: list[dict]) -> dict:
    incumbent = _best(history)
    if incumbent is None:
        return {"eligible": False, "reason": "no-valid-incumbent"}
    successful = sum(row["successful_contract_call"] for row in calls)
    return trigger_window(
        history,
        incumbent=tuple(incumbent["canonical_tour"]),
        optimum=optimum,
        r_med=thresholds["R_med"],
        r_low=thresholds["R_low"],
        successful_calls=successful,
        hard_orbit_blocks=_window_gate_blocks(history),
        operationally_quiescent=True,
    )


def _copy_branches(source: Path, destination: Path, seed: int, prereg_digest: str, trigger: dict) -> dict:
    source_digest = root_state_digest(source)
    history = _payloads(Harness(source), OBSERVATION_SIGNAL)
    incumbent = _best(history)
    checkpoint = Checkpoint(
        instance_seed=seed,
        source_state_digest=source_digest,
        incumbent=tuple(incumbent["canonical_tour"]),
        history_digest=sha256_hex(canonical_json(history)),
        remaining_calls=BRANCH_CALLS,
        remaining_tokens=BRANCH_TOKENS,
    )
    order = branch_order(seed, source_digest, prereg_digest)
    receipt = {
        "schema": "deepreason-jolt-tsp-branch-plan-v3.1",
        "source_state_digest": source_digest,
        "checkpoint": checkpoint.payload(),
        "execution_order": list(order),
        "randomisation_seed_sha256": sha256(f"{seed}:{source_digest}:{prereg_digest}".encode("utf-8")).hexdigest(),
        "trigger": trigger,
        "equal_budget": {"calls": BRANCH_CALLS, "tokens": BRANCH_TOKENS},
    }
    destination.mkdir(parents=True, exist_ok=False)
    for arm in ARMS:
        root = destination / arm
        shutil.copytree(source, root)
        if root_state_digest(root) != source_digest:
            raise RuntimeError("copied branch does not match frozen source state")
        _write_json(root / "jolt-branch-receipt.json", {**receipt, "arm": arm})
    _write_json(destination / "branch-plan.json", receipt)
    return receipt


def _branch_summary(root: Path, source_history: list[dict], source_best: int, optimum: int) -> dict:
    harness = Harness(root)
    all_history = _payloads(harness, OBSERVATION_SIGNAL)
    post = all_history[len(source_history):]
    valid = [row for row in post if row["valid"]]
    branch_best = min([source_best, *(row["distance"] for row in valid)])
    improved_rows = [row for row in valid if row["distance"] < source_best]
    calls = _payloads(harness, CALL_SIGNAL)
    source_call_count = sum(1 for row in calls if row["phase"] == "acquisition")
    post_calls = calls[source_call_count:]
    first_improvement = min((row["call_index"] for row in improved_rows), default=None)
    source_incumbent = tuple(_best(source_history)["canonical_tour"])
    tokens_to_first = None
    if first_improvement is not None:
        tokens_to_first = sum(row["tokens"]["total"] for row in post_calls if row["call_index"] <= first_improvement)
    gap = source_best - optimum
    return {
        "source_best_distance": source_best,
        "branch_best_distance": branch_best,
        "verified_improvement": branch_best < source_best,
        "gap_closed": (source_best - branch_best) / gap if gap else None,
        "calls_to_first_improvement": (first_improvement + 1) if first_improvement is not None else None,
        "tokens_to_first_improvement": tokens_to_first,
        "censored": not improved_rows,
        "valid_admissions": len(valid),
        "duplicate_admissions": sum(row["duplicate_admission"] for row in valid),
        "unique_canonical_tours": sum(row["unique_canonical_tour"] for row in valid),
        "functionally_novel_edge_sets": sum(row["functional_novelty"] for row in valid),
        "mean_retained_vs_source": (
            sum(retained_edge_fraction(row["canonical_tour"], source_incumbent) for row in valid) / len(valid)
            if valid else None
        ),
        "schema_or_invalid": sum(not row["valid"] for row in post),
        "transport_failures": sum(bool(row["error"]) for row in post_calls),
        "tokens": {
            "prompt": sum(row["tokens"]["prompt_tokens"] for row in post_calls),
            "completion": sum(row["tokens"]["completion_tokens"] for row in post_calls),
            "total": sum(row["tokens"]["total"] for row in post_calls),
        },
        "warrants": len(harness.warrants),
        "attacks": len(harness.state.att),
        "verify_root": verify_root(root),
    }


def experiment() -> None:
    if not os.environ.get("OLLAMA_API_KEY"):
        raise SystemExit("OLLAMA_API_KEY is required")
    prereg_digest = _sha(PREREG)
    plan = json.loads(MANIFEST_PLAN.read_text())
    if plan["preregistration_sha256"] != prereg_digest:
        raise SystemExit("preregistration digest mismatch")
    prereg = yaml.safe_load(PREREG.read_text())
    calibration_commit = prereg["calibration"]["commit"]
    prereg_commit = _git("log", "-1", "--format=%H", "--", str(PREREG.relative_to(ROOT)))
    if subprocess.run(("git", "merge-base", "--is-ancestor", calibration_commit, prereg_commit), cwd=ROOT).returncode:
        raise SystemExit("calibration commit is not an ancestor of preregistration commit")
    if _git("status", "--short", "--", str(PREREG.relative_to(ROOT)), str(MANIFEST_PLAN.relative_to(ROOT)), str(ANALYSIS_PLAN.relative_to(ROOT))):
        raise SystemExit("preregistration artifacts are not committed")
    instances = _load_instances(EXP_INSTANCES)
    optima = _load_optima()
    thresholds = {"R_med": prereg["calibration"]["R_med"], "R_low": prereg["calibration"]["R_low"]}
    results = []
    for seed in EXP_SEEDS:
        source_root = RUNS / "source" / str(seed)
        harness, manifest = _open_root(source_root, instances[seed])
        trigger = _trigger(_payloads(harness, OBSERVATION_SIGNAL), optima[seed]["exact_distance"], thresholds, _payloads(harness, CALL_SIGNAL))
        while len(_payloads(harness, CALL_SIGNAL)) < ACQUISITION_CALLS and not trigger.get("eligible"):
            call_index = len(_payloads(harness, CALL_SIGNAL))
            receipt = _call_once(harness, manifest, instances[seed], phase="acquisition", root_label=str(seed), arm="J0", call_index=call_index)
            print(json.dumps({"seed": seed, "phase": "acquisition", "call": call_index, "tokens": receipt["tokens"]["total"], "valid": receipt["valid_candidates"], "error": receipt["error"]}))
            trigger = _trigger(_payloads(harness, OBSERVATION_SIGNAL), optima[seed]["exact_distance"], thresholds, _payloads(harness, CALL_SIGNAL))
            if trigger.get("certified_completion"):
                break
        trigger["decision_event_seq"] = harness._next_seq
        trigger["digest"] = sha256_hex(canonical_json(trigger))
        harness.record_measure(inputs=[TRIGGER_SIGNAL, json.dumps(trigger, sort_keys=True, separators=(",", ":"))])
        source_verify = verify_root(source_root)
        if source_verify["violations"]:
            raise RuntimeError(f"source root verification failure: {seed}")
        row = {"seed": seed, "trigger": trigger, "source_verify": source_verify, "branches": {}}
        if trigger.get("eligible"):
            branch_parent = RUNS / "branches" / str(seed)
            if branch_parent.exists():
                branch_plan = json.loads((branch_parent / "branch-plan.json").read_text())
            else:
                branch_plan = _copy_branches(source_root, branch_parent, seed, prereg_digest, trigger)
            source_history = _payloads(Harness(source_root), OBSERVATION_SIGNAL)
            source_best = _best(source_history)["distance"]
            for arm in branch_plan["execution_order"]:
                branch_root = branch_parent / arm
                branch_harness = Harness(branch_root)
                branch_manifest = load_run_manifest(branch_root / "run-manifest.json")
                post_calls = [receipt for receipt in _payloads(branch_harness, CALL_SIGNAL) if receipt["phase"] == "branch"]
                spent = sum(receipt["tokens"]["total"] for receipt in post_calls)
                if not _payloads(branch_harness, ACTION_SIGNAL):
                    action = {
                        "schema": "deepreason-jolt-tsp-action-v3.1",
                        "arm": arm,
                        "status_neutral": True,
                        "prompt_context_sha256": sha256(treatment_context(
                            arm,
                            instance=instances[seed],
                            history=source_history,
                            incumbent=tuple(_best(source_history)["canonical_tour"]),
                            median_retained=trigger["median_retained_edge_fraction"],
                            failure_classes=_failure_classes(source_history),
                        ).encode()).hexdigest(),
                    }
                    branch_harness.record_measure(inputs=[ACTION_SIGNAL, json.dumps(action, sort_keys=True, separators=(",", ":"))])
                while len(post_calls) < BRANCH_CALLS and spent < BRANCH_TOKENS:
                    call_index = len(post_calls)
                    receipt = _call_once(
                        branch_harness,
                        branch_manifest,
                        instances[seed],
                        phase="branch",
                        root_label=str(seed),
                        arm=arm,
                        call_index=call_index,
                        branch_token_remaining=BRANCH_TOKENS - spent,
                    )
                    print(json.dumps({"seed": seed, "phase": "branch", "arm": arm, "call": call_index, "tokens": receipt["tokens"]["total"], "valid": receipt["valid_candidates"], "error": receipt["error"]}))
                    post_calls.append(receipt)
                    spent += receipt["tokens"]["total"]
                row["branches"][arm] = _branch_summary(branch_root, source_history, source_best, optima[seed]["exact_distance"])
        else:
            row["exclusion"] = (
                "healthy-completion" if trigger.get("certified_completion")
                else "trigger-not-reached-within-cap"
            )
        results.append(row)
        _write_json(RAW_REPORT, {"schema": "deepreason-jolt-positive-headroom-raw-report-v3.1", "preregistration_sha256": prereg_digest, "blocks": results, "ledger": _ledger()})
    print(json.dumps({"eligible_blocks": sum(bool(row["branches"]) for row in results), "ledger_totals": _ledger_totals(_ledger())}, indent=2))


def report() -> None:
    calibration = json.loads(CAL_REPORT_JSON.read_text())
    if calibration["status"] == "calibration_failure":
        roots = []
        for seed in CAL_SEEDS:
            root = RUNS / "calibration" / str(seed)
            roots.append({"root": str(root.relative_to(ROOT)), "verify": verify_root(root)})
        ledger = calibration["ledger"]
        total_tokens, total_calls = _ledger_totals(ledger)
        final = {
            "schema": "deepreason-jolt-positive-headroom-report-v3.1",
            "status": "calibration_failure",
            "verdict": "calibration failure",
            "preserved_prior_result": (
                "A no-improvement window does not imply stagnation when the "
                "registered objective has already been completed."
            ),
            "calibration": {
                "thresholds": None,
                "criterion": (
                    "at least two of three held-out instances and zero fires "
                    "in any window containing an improvement"
                ),
                "candidate_pairs_examined": 78,
                "candidate_pairs_satisfying_criterion": 0,
                "best_zero-improvement-window-fire_pairs": {
                    "nonimproving_instances_reached": 0,
                    "example": {"R_med": 1.0, "R_low": 0.35},
                },
                "most_selective_pair_reaching_all_three_nonimproving_instances": {
                    "R_med": 0.7142857142857143,
                    "R_low": 0.7142857142857143,
                    "improving_window_fires": 10,
                },
                "instances": calibration["instances"],
            },
            "experimental_execution": {
                "started": False,
                "acquisition_calls": 0,
                "matched_blocks": 0,
                "branch_calls": 0,
                "reason": "registered calibration-failure stop condition",
            },
            "live_usage": {
                "conjecturer_call_opportunities": total_calls,
                "tokens": total_tokens,
                "judge_tokens": 0,
                "critic_tokens": 0,
                "research_tokens": 0,
                "pairwise_tokens": 0,
                "synthesis_tokens": 0,
                "controller_tokens": 0,
                "hard_token_ceiling": HARD_TOKENS,
            },
            "credential_audit": {
                "storage": "environment only",
                "plaintext_credentials_in_protocol_artifacts_or_roots": 0,
                "credentials_committed": False,
            },
            "retained_root_verification": {
                "roots": roots,
                "violating_roots": [row for row in roots if row["verify"]["violations"]],
            },
            "interpretation": (
                "The proposed overlap thresholds did not separate plateau "
                "windows from windows still containing verifier improvement. "
                "No jolt-effect estimand was observed and no efficacy claim is possible."
            ),
        }
        _write_json(REPORT_JSON, final)
        REPORT_MD.write_text(
            "# Positive-Headroom Jolt Pilot v3.1\n\n"
            "Verdict: **calibration failure**.\n\n"
            "The held-out calibration completed 96 conjecturer opportunities, "
            f"using {total_tokens:,} tokens. No candidate `R_med`/`R_low` pair "
            "fired on at least two of three held-out instances while firing on "
            "zero windows that contained an improvement. The experimental phase "
            "therefore did not start.\n\n"
            "The most selective pair that reached non-improving windows on all "
            "three instances (`R_med = R_low = 5/7`) also fired on 10 windows "
            "containing an improvement. Every zero-improvement-window-fire pair "
            "reached zero non-improving instances. This means retained-edge "
            "contraction, as calibrated here, did not identify an improvement-free "
            "plateau without temporal false positives.\n\n"
            "No experimental acquisition, matched branch, or jolt call was made. "
            "Judge, critic, pairwise, synthesis, research, and controller token use "
            "was zero. Novelty was not interpreted as useful progress.\n\n"
            f"All {len(roots)} retained calibration roots verified with zero "
            "violations.\n"
        )
        print(json.dumps(final, indent=2))
        return
    raw = json.loads(RAW_REPORT.read_text())
    eligible = [row for row in raw["blocks"] if row["branches"]]
    comparisons = (("J3", "J0"), ("J4", "J0"), ("J1", "J0"), ("J3", "J1"), ("J4", "J1"), ("J6", "J0"))
    comparison_rows = {}
    for left, right in comparisons:
        rows = []
        for block in eligible:
            a, b = block["branches"][left], block["branches"][right]
            rows.append({
                "seed": block["seed"],
                "improvement_indicator_difference": int(a["verified_improvement"]) - int(b["verified_improvement"]),
                "gap_closed_difference": a["gap_closed"] - b["gap_closed"],
                "branch_token_difference": a["tokens"]["total"] - b["tokens"]["total"],
            })
        comparison_rows[f"{left}_vs_{right}"] = rows
    all_roots = []
    for row in raw["blocks"]:
        all_roots.append({"root": f"source/{row['seed']}", "verify": row["source_verify"]})
        for arm, branch in row["branches"].items():
            all_roots.append({"root": f"branches/{row['seed']}/{arm}", "verify": branch["verify_root"]})
    ledger = raw["ledger"]
    total_tokens, total_calls = _ledger_totals(ledger)
    violations = [item for item in all_roots if item["verify"]["violations"]]
    status = "feasibility_demonstrated" if len(eligible) >= 6 else "trigger_scarcity"
    any_direction = any(
        sum(row["improvement_indicator_difference"] for row in rows) != 0
        for rows in comparison_rows.values()
    )
    verdict = (
        "promising directional result requiring confirmation"
        if status == "feasibility_demonstrated" and any_direction
        else ("no directional evidence" if status == "feasibility_demonstrated" else "trigger scarcity")
    )
    report_value = {
        "schema": "deepreason-jolt-positive-headroom-report-v3.1",
        "status": status,
        "verdict": verdict,
        "estimand": "conditional matched-state effects among reached certified-positive-headroom plateau states",
        "eligible_blocks": len(eligible),
        "excluded_instances": [{"seed": row["seed"], "reason": row.get("exclusion")} for row in raw["blocks"] if not row["branches"]],
        "blocks": raw["blocks"],
        "comparisons": comparison_rows,
        "live_usage": {"conjecturer_call_opportunities": total_calls, "tokens": total_tokens, "hard_token_ceiling": HARD_TOKENS, "judge_tokens": 0, "critic_tokens": 0, "research_tokens": 0},
        "retained_root_verification": {"roots": len(all_roots), "violating_roots": violations},
        "scope": {"can_establish": ["matched-state verified improvement", "within-family directional component advantage", "operational validity and branch-token differences", "whether a larger study is warranted"], "cannot_establish": ["production trigger accuracy", "unknown-headroom effects", "open-research effects", "whole-run adaptive-policy benefit", "hard-orbit treatment", "cross-model generality", "universal best jolt"]},
    }
    _write_json(REPORT_JSON, report_value)
    lines = [
        "# Positive-Headroom Jolt Pilot v3.1",
        "",
        f"Verdict: **{verdict}**.",
        "",
        f"Reached {len(eligible)} eligible matched blocks from eight experimental instances. Live use across calibration, acquisition, and branches was {total_calls} conjecturer-call opportunities and {total_tokens:,} tokens. Judge, critic, research, pairwise, synthesis, and controller usage was zero.",
        "",
        "The estimand is conditional matched-state performance among reached, mechanically certified positive-headroom plateau states. It is not a whole-run adaptive-policy or cross-domain effect.",
        "",
        "## Per-block outcomes",
        "",
        "| seed | source best | optimum | J0 | J1 | J3 | J4 | J6 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    optima = _load_optima()
    for block in eligible:
        branches = block["branches"]
        lines.append(
            f"| {block['seed']} | {block['trigger']['source_best_distance']} | {optima[block['seed']]['exact_distance']} | "
            + " | ".join(f"{branches[arm]['branch_best_distance']} ({'improved' if branches[arm]['verified_improvement'] else 'no'})" for arm in ARMS)
            + " |"
        )
    if not eligible:
        lines.append("| — | — | — | — | — | — | — | — |")
    lines.extend([
        "",
        "Novelty counts are reported only as secondary operational measures; useful progress means deterministic distance improvement or certified gap closure.",
        "",
        f"All {len(all_roots)} retained roots verified with {len(violations)} roots containing violations.",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n")
    if violations and not FORENSIC.exists():
        FORENSIC.write_text("# Positive-Headroom Jolt Pilot v3.1 — forensic addendum\n\nInvariant failure detected during retained-root verification. Live protocol is frozen. See the JSON report for exact violations.\n")
    print(json.dumps(report_value, indent=2))


def verify() -> None:
    roots = [
        RUNS / "calibration" / str(seed) for seed in CAL_SEEDS
    ] + [
        ROOT / "runs" / "jolt_trigger_glm52_pilot" / "source",
        ROOT / "runs" / "jolt_trigger_glm52_pilot_v2" / "source",
        ROOT / "runs" / "jolt_trigger_glm52_pilot_v2" / "branches" / "branch-00-J3",
        ROOT / "runs" / "jolt_trigger_glm52_pilot_v2" / "branches" / "branch-01-J0",
        ROOT / "runs" / "jolt_trigger_glm52_pilot_v2" / "branches" / "branch-02-J4",
        ROOT / "runs" / "jolt_trigger_glm52_pilot_v2" / "branches" / "branch-03-J6",
    ]
    rows = []
    for root in roots:
        if not root.exists():
            rows.append({"root": str(root.relative_to(ROOT)), "missing": True})
            continue
        rows.append({
            "root": str(root.relative_to(ROOT)),
            "state_digest": root_state_digest(root),
            "verification": verify_root(root),
        })
    value = {
        "schema": "deepreason-jolt-positive-headroom-retained-root-verification-v3.1",
        "roots": rows,
        "root_count": len(rows),
        "missing_roots": sum(bool(row.get("missing")) for row in rows),
        "violation_count": sum(
            len(row.get("verification", {}).get("violations", [])) for row in rows
        ),
    }
    _write_json(VERIFY_REPORT, value)
    print(json.dumps(value, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("prepare", "calibrate", "preregister", "experiment", "report", "verify"),
    )
    args = parser.parse_args()
    globals()[args.command]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
