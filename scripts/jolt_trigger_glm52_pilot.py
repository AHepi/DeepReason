#!/usr/bin/env python
"""Run the preregistered GLM-5.2 matched soft-stagnation pilot."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deepreason.canonical import canonical_json, sha256_hex  # noqa: E402
from deepreason.config import Config  # noqa: E402
from deepreason.harness import Harness  # noqa: E402
from deepreason.invariants import verify_root  # noqa: E402
from deepreason.jolts import (  # noqa: E402
    JoltArm,
    JoltDiagnosis,
    PublicVerifierFailure,
    build_jolt_action,
    materialize_matched_branches,
    plan_matched_branches,
    record_jolt_action,
)
from deepreason.llm.adapter import build_adapter  # noqa: E402
from deepreason.llm.budget import TokenMeter  # noqa: E402
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Status  # noqa: E402
from deepreason.programs import content_text  # noqa: E402
from deepreason.rules.conj import conj  # noqa: E402
from deepreason.rules.crit import crit_program  # noqa: E402
from deepreason.run_manifest import (  # noqa: E402
    bind_run_manifest,
    compile_run_manifest,
    config_from_run_manifest,
    load_run_manifest,
    preflight_harness,
    role_matrix,
)
from deepreason.scheduler.scheduler import problem_family_key  # noqa: E402
from deepreason.views.jolt_signals import (  # noqa: E402
    FunctionalObservation,
    StatusSource,
    VerifierMetric,
    VerifierMetricKind,
    functional_observations,
    record_functional_observation,
)

PREREG = ROOT / "experiments" / "jolt_trigger_glm52_pilot_v2_prereg.yaml"
OUT = ROOT / "experiments" / "results" / "jolt_trigger_glm52_pilot_v2_report.json"
RUNS = ROOT / "runs" / "jolt_trigger_glm52_pilot_v2"
SOURCE = RUNS / "source"
BRANCHES = RUNS / "branches"
PROBLEM_ID = "pi-jolt-finite-selection-v1"
EVALUATOR_ID = "finite-selection-product-v1"
EVALUATOR_SOURCE = b"six sorted nonadjacent ints 1..20 sum60; objective product"
EVALUATOR_FP = sha256(EVALUATOR_SOURCE).hexdigest()
MANIFEST_PLAN_FP = sha256((PREREG.name + "\0manifest-v1").encode()).hexdigest()


def config() -> Config:
    return Config.model_validate({
        "N_SCHOOLS": 0,
        "VS_K": 3,
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


def _selection(text: str) -> tuple[int, ...] | None:
    try:
        raw = json.loads(text)
        values = raw.get("selection") if isinstance(raw, dict) else None
        if not isinstance(values, list) or len(values) != 6:
            return None
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            return None
        selection = tuple(values)
    except (ValueError, TypeError):
        return None
    if selection != tuple(sorted(selection)) or len(set(selection)) != 6:
        return None
    if min(selection) < 1 or max(selection) > 20 or sum(selection) != 60:
        return None
    if any(right - left < 2 for left, right in zip(selection, selection[1:])):
        return None
    return selection


def _mechanism(selection: tuple[int, ...]) -> str:
    return "low-start" if selection[0] <= 3 else ("middle-start" if selection[0] <= 6 else "high-start")


def seed(harness: Harness) -> None:
    expression = (
        "len(json.loads(content).get('selection', [])) == 6 and "
        "json.loads(content)['selection'] == sorted(json.loads(content)['selection']) and "
        "len({json.loads(content)['selection'][0], json.loads(content)['selection'][1], "
        "json.loads(content)['selection'][2], json.loads(content)['selection'][3], "
        "json.loads(content)['selection'][4], json.loads(content)['selection'][5]}) == 6 and "
        "min(json.loads(content)['selection']) >= 1 and max(json.loads(content)['selection']) <= 20 and "
        "sum(json.loads(content)['selection']) == 60 and "
        "all([json.loads(content)['selection'][1]-json.loads(content)['selection'][0] >= 2, "
        "json.loads(content)['selection'][2]-json.loads(content)['selection'][1] >= 2, "
        "json.loads(content)['selection'][3]-json.loads(content)['selection'][2] >= 2, "
        "json.loads(content)['selection'][4]-json.loads(content)['selection'][3] >= 2, "
        "json.loads(content)['selection'][5]-json.loads(content)['selection'][4] >= 2])"
    )
    harness.register_commitment(Commitment(id="jolt-finite-valid-v1", eval="predicate:" + expression))
    harness.register_problem(Problem(
        id=PROBLEM_ID,
        description=(
            "FINITE OPTIMISATION. Select exactly six strictly increasing, distinct, "
            "non-adjacent integers from 1 through 20 whose sum is exactly 60. Maximise "
            "the product of the six integers. Each candidate content MUST itself be a "
            "single JSON object with exactly this useful shape: "
            "{\"selection\":[int,int,int,int,int,int],\"rationale\":\"short text\"}. "
            "Do not wrap it in markdown. Different candidates should use genuinely "
            "different selections, not reordered duplicates."
        ),
        criteria=["jolt-finite-valid-v1"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))


def _current_best(harness: Harness) -> tuple[int, set[tuple[int, ...]], set[str]]:
    best = 0
    selections: set[tuple[int, ...]] = set()
    mechanisms: set[str] = set()
    for receipt in functional_observations(harness):
        observation = receipt.observation
        if not observation.admitted:
            continue
        metric = observation.verifier_metric
        if metric is not None:
            best = max(best, int(metric.after))
        text = content_text(harness.state.artifacts[observation.candidate_id], harness.blobs)
        selection = _selection(text)
        if selection:
            selections.add(selection)
            mechanisms.add(_mechanism(selection))
    return best, selections, mechanisms


def evaluate_candidates(harness: Harness, artifact_ids: list[str]) -> None:
    best, seen, mechanisms = _current_best(harness)
    family = problem_family_key(harness.state, PROBLEM_ID)
    for artifact_id in artifact_ids:
        crit_program(harness, artifact_id)
        admitted = harness.state.status.get(artifact_id) == Status.ACCEPTED
        selection = _selection(content_text(harness.state.artifacts[artifact_id], harness.blobs)) if admitted else None
        if selection is None:
            observation = FunctionalObservation(
                candidate_id=artifact_id, problem_id=PROBLEM_ID,
                problem_family=family, domain="finite", evaluator_id=EVALUATOR_ID,
                evaluator_fingerprint=EVALUATOR_FP, admitted=False,
                functional_novelty=False, status_source=StatusSource.DETERMINISTIC,
            )
        else:
            score = math.prod(selection)
            after = max(best, score)
            mechanism = _mechanism(selection)
            observation = FunctionalObservation(
                candidate_id=artifact_id, problem_id=PROBLEM_ID,
                problem_family=family, domain="finite", evaluator_id=EVALUATOR_ID,
                evaluator_fingerprint=EVALUATOR_FP, admitted=True,
                functional_novelty=selection not in seen,
                mechanism_class=mechanism,
                verifier_metric=VerifierMetric(
                    name="best-selection-product", kind=VerifierMetricKind.OBJECTIVE,
                    before=float(best), after=float(after), delta=float(after - best),
                    unit="integer_product", source_receipt=EVALUATOR_FP,
                ),
                status_source=StatusSource.DETERMINISTIC,
            )
            best = after
            seen.add(selection)
            mechanisms.add(mechanism)
        record_functional_observation(harness, observation)


def trigger_receipt(harness: Harness) -> dict:
    valid = [r for r in functional_observations(harness) if r.observation.admitted]
    recent = valid[-8:]
    earlier_classes = {r.observation.mechanism_class for r in valid[:-8]}
    recent_classes = {r.observation.mechanism_class for r in recent}
    improvements = sum(
        bool(r.observation.verifier_metric and r.observation.verifier_metric.delta > 0)
        for r in recent
    )
    novel_classes = sorted(value for value in recent_classes - earlier_classes if value)
    fired = len(recent) == 8 and improvements == 0 and not novel_classes
    payload = {
        "schema": "deepreason-functional-soft-trigger-v1",
        "valid_admissions": len(valid), "window": len(recent),
        "improvements_in_window": improvements,
        "new_mechanism_classes": novel_classes, "trigger": fired,
        "source_event_seqs": [r.event_seq for r in recent],
    }
    payload["digest"] = sha256_hex(canonical_json(payload))
    harness.record_measure(inputs=["jolt-trigger", json.dumps(payload, sort_keys=True)])
    return payload


def run_calls(harness: Harness, manifest, calls: int, token_cap: int, *, action=None) -> dict:
    cfg = config_from_run_manifest(manifest)
    meter = TokenMeter(budget=token_cap)
    adapter = build_adapter(cfg, harness.blobs, meter=meter, run_manifest=manifest)
    dropped = []
    for _ in range(calls):
        try:
            artifacts = conj(
                harness, PROBLEM_ID, adapter, cfg, workload_profile="formal",
                generation_context=action.prompt_context if action else None,
                complement=bool(action and action.arm == JoltArm.J6),
                suppressed_exemplars=action.suppressed_artifact_ids if action else (),
            )
            evaluate_candidates(harness, [artifact.id for artifact in artifacts])
        except Exception as error:  # transport/schema failures remain outcomes
            dropped.append(f"{type(error).__name__}: {str(error)[:180]}")
            harness.record_measure(inputs=["jolt-live-dropped", dropped[-1]])
    return {"meter": meter.snapshot(), "dropped": dropped}


def summarize_branch(harness: Harness, source_best: int, runtime: dict) -> dict:
    best, selections, _ = _current_best(harness)
    observations = functional_observations(harness)
    source_seq = json.loads((Path(harness.root) / "jolt-branch-manifest.json").read_text())["source_event_seq"]
    post = [r for r in observations if r.event_seq >= source_seq]
    return {
        "source_best": source_best,
        "final_best": best,
        "objective_delta": best - source_best,
        "verified_progress": best > source_best,
        "post_branch_valid_admissions": sum(r.observation.admitted for r in post),
        "post_branch_functionally_novel": sum(r.observation.functional_novelty for r in post),
        "total_unique_selections": len(selections),
        "tokens": runtime["meter"],
        "dropped": runtime["dropped"],
        "warrants": len(harness.warrants),
        "attacks": len(harness.state.att),
        "verify_root": verify_root(harness.root, runtime["meter"]["total"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    if not os.environ.get("OLLAMA_API_KEY"):
        raise SystemExit("OLLAMA_API_KEY is required")
    if BRANCHES.exists():
        raise SystemExit(f"branch destination already exists: {BRANCHES}")

    cfg = config()
    if SOURCE.exists():
        manifest = load_run_manifest(SOURCE / "run-manifest.json")
        cfg = config_from_run_manifest(manifest)
        source = Harness(SOURCE)
    else:
        manifest = compile_run_manifest(
            cfg, schema_version=2, workload_profile="formal", rubric_policy="forbid"
        )
        source = Harness(SOURCE)
        bind_run_manifest(manifest, SOURCE)
        seed(source)
    preflight_harness(manifest, source, cfg)
    completed_calls = sum(
        1 for event in source.log.read()
        if event.llm is not None and event.llm.role == "conjecturer"
        and event.rule.value == "Conj"
    )
    if completed_calls > 16:
        raise SystemExit("source advanced beyond the frozen sixteen-call acquisition")
    acquisition = {
        "meter": {"prompt_tokens": 0, "completion_tokens": 0, "total": 0, "calls": 0},
        "dropped": [], "resumed_from_calls": completed_calls,
    }
    trigger = trigger_receipt(source) if completed_calls >= 8 else {"trigger": False}
    while completed_calls < 16 and not trigger["trigger"]:
        logged = sum(event.llm.tokens for event in source.log.read() if event.llm is not None)
        runtime = run_calls(source, manifest, 1, max(0, 112000 - logged))
        for field in ("prompt_tokens", "completion_tokens", "total", "calls"):
            acquisition["meter"][field] += runtime["meter"][field]
        acquisition["dropped"].extend(runtime["dropped"])
        completed_calls += 1
        if completed_calls >= 8:
            trigger = trigger_receipt(source)
    acquisition["total_logged_tokens"] = sum(
        event.llm.tokens for event in source.log.read() if event.llm is not None
    )
    acquisition["completed_calls"] = completed_calls
    source_check = verify_root(SOURCE)
    if source_check["violations"]:
        raise SystemExit("source root verification failed")
    if not trigger["trigger"]:
        Path(args.out).write_text(json.dumps({
            "schema": "deepreason-jolt-trigger-glm52-pilot-report-v2",
            "status": "trigger_not_reached", "trigger": trigger,
            "acquisition": acquisition, "source_verify": source_check,
        }, indent=2) + "\n")
        return 2

    prereg_digest = sha256(PREREG.read_bytes()).hexdigest()
    route_digest = sha256_hex(canonical_json(role_matrix(manifest)))
    plan = plan_matched_branches(
        SOURCE, arms=(JoltArm.J0, JoltArm.J3, JoltArm.J4, JoltArm.J6),
        diagnosis=JoltDiagnosis.SOFT_EXHAUSTION, original_problem_id=PROBLEM_ID,
        branch_order_seed="glm52-jolt-pilot-v1",
        experiment_manifest_plan_digest=MANIFEST_PLAN_FP,
        run_manifest_digest=manifest.sha256, route_matrix_digest=route_digest,
        verifier_fingerprint=EVALUATOR_FP,
        functional_evaluator_fingerprint=EVALUATOR_FP,
        embedder_fingerprint={"model": "not-used", "version": "functional-only-v1", "sentinel": prereg_digest[:16]},
        trigger_receipt_digest=trigger["digest"],
    )
    roots = materialize_matched_branches(plan, BRANCHES)
    source_best, _, _ = _current_best(source)
    results = {}
    public_failure = PublicVerifierFailure(
        label="best objective did not improve in the frozen eight-admission window",
        source_receipt=trigger["digest"],
    )
    for branch, root in sorted(zip(plan.branches, roots), key=lambda pair: pair[0].execution_order):
        harness = Harness(root)
        action = build_jolt_action(
            branch.arm, diagnosis=JoltDiagnosis.SOFT_EXHAUSTION,
            original_problem_id=PROBLEM_ID, domain="finite",
            public_failures=(public_failure,) if branch.arm == JoltArm.J4 else (),
        )
        record_jolt_action(harness, action)
        runtime = run_calls(harness, manifest, 5, 35000, action=action)
        results[branch.arm.value] = summarize_branch(harness, source_best, runtime)

    report = {
        "schema": "deepreason-jolt-trigger-glm52-pilot-report-v2",
        "status": "complete", "preregistration_sha256": prereg_digest,
        "manifest_sha256": manifest.sha256, "plan_digest": plan.digest,
        "model": {"id": "glm-5.2", "reasoning": "none"},
        "trigger": trigger, "acquisition": acquisition,
        "source_best": source_best, "branches": results,
        "estimand_limit": "conditional matched-state pilot; one state, no whole-run or hard-orbit claim",
    }
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
