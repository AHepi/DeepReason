"""Preregistered website compatibility matrix and process-only reporting."""

from pathlib import Path

from deepreason.compat_eval import (
    REQUIRED_WEBSITE_TAGS,
    _is_compact_recovery_signal,
    aggregate_report,
    aggregate_role_metrics,
    collect_trial_record,
    compare_frontier_baseline,
    frontier_family_coverage,
    load_matrix,
    matrix_digest,
    new_checkpoint,
    threshold_verdict,
    trial_key,
)


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "experiments" / "website_compat_matrix_v1.json"


def _record(prompt_id: str, *, first_pass: int, eventual: int) -> dict:
    return {
        "state": "terminal",
        "key": trial_key(prompt_id, 1729, "compact"),
        "prompt_id": prompt_id,
        "seed": 1729,
        "profile": "compact",
        "evidence_class": "offline_mock",
        "frozen_models": ["gemma4:31b"],
        "live_transport_observed": False,
        "process": {
            "roles": {
                "conjecturer": {
                    "calls": 1,
                    "traced_calls": 1,
                    "first_pass_valid": first_pass,
                    "eventual_valid": eventual,
                    "schema_exhausted": 1 - eventual,
                }
            },
            "tokens": 100,
            "latency_ms": 20,
            "direct_calls": 0,
            "compact_calls": 1,
            "route_mismatch_calls": 0,
            "schema_failures_by_path": {"/candidates/0": 1 - first_pass},
            "manifest_failures_by_code": {},
        },
        "website": {
            "manifest_valid_within_three_rounds": True,
            "manifest_wf_success": True,
            "component_wf_success": True,
            "integration_wf_success": True,
            "export_success": True,
            "design_terminal_failure": False,
            "terminal_summary_complete": False,
            "invalid_manifest_reached_post_validation": False,
            "compact_recovery_declared": False,
        },
        "quality_counts": {
            "browser_passes": 1,
            "browser_failures": 0,
            "attackers": 2,
            "standing_attackers": 2,
            "survivor_hv_n": 1,
            "survivor_hv_sum": 0.8,
            "integration_success": True,
        },
    }


def test_preregistered_website_matrix_has_required_size_and_strata():
    matrix = load_matrix(MATRIX_PATH)
    assert len(matrix["prompts"]) == 60
    assert matrix["protocol"]["max_design_rounds"] == 3
    assert matrix["thresholds"]["A3"]["minimum_rate"] == 0.9
    assert matrix["thresholds"]["A10"]["maximum_count"] == 0
    tags = {tag for prompt in matrix["prompts"] for tag in prompt["tags"]}
    assert REQUIRED_WEBSITE_TAGS <= tags


def test_report_aggregation_uses_traced_call_denominators_and_honest_evidence():
    matrix = load_matrix(MATRIX_PATH)
    records = [_record("W001", first_pass=0, eventual=1), _record("W002", first_pass=1, eventual=1)]
    role = aggregate_role_metrics(records)["conjecturer"]
    assert role["calls"] == 2
    assert role["first_pass_valid_rate"] == 0.5
    assert role["eventual_valid_rate"] == 1.0

    checkpoint = new_checkpoint(matrix, phase="candidate", evidence_class="offline_mock")
    checkpoint["records"] = {record["key"]: record for record in records}
    report = aggregate_report(matrix, checkpoint)
    assert report["metrics"]["process"]["tokens"] == 200
    assert report["metrics"]["schema_failures_by_path"] == {"/candidates/0": 1}
    assert report["evidence"]["class"] == "offline_mock"
    assert report["evidence"]["acceptance_claim_eligible"] is False
    assert all(
        verdict["status"] not in {"pass", "fail"}
        for verdict in report["acceptance"].values()
    )


def test_threshold_verdict_boundaries_and_missing_evidence():
    assert threshold_verdict(0.9, minimum=0.9)["status"] == "pass"
    assert threshold_verdict(0.899, minimum=0.9)["status"] == "fail"
    assert threshold_verdict(0, maximum=0)["status"] == "pass"
    assert threshold_verdict(1, maximum=0)["status"] == "fail"
    assert threshold_verdict(None, minimum=0.9)["status"] == "insufficient_evidence"
    assert threshold_verdict(1.0, minimum=0.9, eligible=False)["status"] == (
        "insufficient_evidence"
    )


def test_compact_recovery_uses_stable_signal_token_and_legacy_fallback():
    assert _is_compact_recovery_signal(
        ["website-design-mode", "frontier", "compact-recovery", "schema-exhausted"]
    )


def test_mock_manifest_route_cannot_be_labelled_live_transport(tmp_path):
    from deepreason.harness import Harness
    from deepreason.ontology import LLMAttempt, LLMCall
    from deepreason.run_manifest import Route, RunManifest, persist_run_manifest

    root = tmp_path / "work" / "roots" / "compact" / "W001-s1729"
    route = Route(
        endpoint_id="mock-seat",
        base_url="mock://compat",
        model_id="gemma4:31b",
        provider="mock",
        family="gemma",
    )
    manifest = RunManifest(
        engine_profile="full",
        model_profile="compact",
        roles={"conjecturer": (route,)},
        rubric_policy="forbid",
        concurrency=1,
        pack_profile="compact",
        output_profile="compact",
        source_config_hash="0" * 64,
        compiled_at="2026-07-12T00:00:00Z",
        engine_config_json="{}",
    )
    persist_run_manifest(manifest, root)
    harness = Harness(root)
    prompt_ref = harness.blobs.put(b"prompt")
    raw_ref = harness.blobs.put(b"{}")
    harness.record_measure(
        inputs=["website-compact-call", "design-outline"],
        llm=LLMCall(
            role="conjecturer",
            model=route.model_id,
            endpoint=route.base_url,
            prompt_ref=prompt_ref,
            raw_ref=raw_ref,
            attempt_trace=[
                LLMAttempt(
                    prompt_ref=prompt_ref,
                    raw_ref=raw_ref,
                    valid=True,
                )
            ],
        ),
    )
    record = collect_trial_record(
        root,
        prompt_id="W001",
        seed=1729,
        profile="compact",
        evidence_class="live",
    )
    assert record["live_transport_observed"] is False
    assert record["process"]["mock_transport_calls"] == 1
    assert _is_compact_recovery_signal(
        ["website-design-mode", "standard", "compact-fallback"]
    )
    assert not _is_compact_recovery_signal(
        ["website-design-mode", "frontier", "direct"]
    )


def test_frontier_comparison_requires_locked_live_baseline_and_two_point_bound():
    matrix = load_matrix(MATRIX_PATH)
    digest = matrix_digest(matrix)
    baseline_metrics = {
        "browser_oracle_pass_rate": 0.96,
        "integration_success_rate": 0.98,
        "attack_validity_rate": 0.95,
        "survivor_hv_mean": 0.75,
    }
    baseline = {
        "phase": "baseline",
        "matrix": {"sha256": digest},
        "evidence": {"class": "live", "acceptance_claim_eligible": True},
        "coverage": {"frontier": {"complete": True, "family_count": 2}},
        "metrics": {"frontier_quality": baseline_metrics},
    }
    within = dict(baseline_metrics)
    within["attack_validity_rate"] = 0.93
    verdict = compare_frontier_baseline(
        within,
        baseline,
        matrix_sha256=digest,
        max_regression_percentage_points=2.0,
    )
    assert verdict["status"] == "pass"

    regressed = dict(within)
    regressed["survivor_hv_mean"] = 0.70
    verdict = compare_frontier_baseline(
        regressed,
        baseline,
        matrix_sha256=digest,
        max_regression_percentage_points=2.0,
    )
    assert verdict["status"] == "fail"
    assert verdict["metrics"]["survivor_hv_mean"]["delta_percentage_points"] < -2


def test_frontier_acceptance_requires_two_non_mock_families():
    one = frontier_family_coverage([
        {"observed_non_mock_families": ["openai-gpt"]},
        {"observed_non_mock_families": ["openai-gpt"]},
    ])
    assert one == {
        "families": ["openai-gpt"],
        "family_count": 1,
        "required_family_count": 2,
        "complete": False,
    }

    two = frontier_family_coverage([
        {"observed_non_mock_families": ["openai-gpt"]},
        {"observed_non_mock_families": ["anthropic-claude"]},
    ])
    assert two["families"] == ["anthropic-claude", "openai-gpt"]
    assert two["complete"] is True

    matrix = load_matrix(MATRIX_PATH)
    digest = matrix_digest(matrix)
    baseline = {
        "phase": "baseline",
        "matrix": {"sha256": digest},
        "evidence": {"class": "live", "acceptance_claim_eligible": True},
        "coverage": {"frontier": {"complete": True, "family_count": 1}},
        "metrics": {"frontier_quality": {
            "browser_oracle_pass_rate": 1.0,
            "integration_success_rate": 1.0,
            "attack_validity_rate": 1.0,
            "survivor_hv_mean": 1.0,
        }},
    }
    assert compare_frontier_baseline(
        baseline["metrics"]["frontier_quality"],
        baseline,
        matrix_sha256=digest,
        max_regression_percentage_points=2.0,
    )["status"] == "insufficient_evidence"
