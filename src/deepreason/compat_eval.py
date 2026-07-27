"""Reproducible, process-only compatibility evaluation for website runs.

This module is deliberately downstream of the harness.  It reads frozen run
manifests, append-only events, terminal summaries, and exported paths; it does
not register artifacts, construct warrants, change labels, or select routes.

The report distinguishes live provider observations from offline/mock inputs.
Offline/mock data can exercise aggregation and reporting but is never eligible
to satisfy the implementation acceptance criteria.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal


MATRIX_SCHEMA_VERSION = 1
CHECKPOINT_SCHEMA_VERSION = 1
REPORT_SCHEMA_VERSION = 1
PROFILES = ("compact", "standard", "frontier")
EVIDENCE_CLASSES = ("live", "offline_mock")
REQUIRED_WEBSITE_TAGS = frozenset(
    {
        "multiple_components",
        "single_component",
        "animation_heavy",
        "reduced_motion_heavy",
        "no_import",
        "permitted_import",
        "malformed_dependency",
        "conflicting_id",
    }
)
POST_MANIFEST_STAGES = frozenset(
    {"COMPONENT_BUILD", "ASSEMBLE", "INTEGRATION_VALIDATE", "EXPORT"}
)
DESIGN_STAGES = frozenset(
    {"DESIGN_OUTLINE", "COMPONENT_CONTRACTS", "MANIFEST_COMPILE", "MANIFEST_VALIDATE"}
)
FRONTIER_QUALITY_METRICS = (
    "browser_oracle_pass_rate",
    "integration_success_rate",
    "attack_validity_rate",
    "survivor_hv_mean",
)


class CompatibilityEvaluationError(ValueError):
    """A stable evaluation input/checkpoint error."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _read_json(path: Path | str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CompatibilityEvaluationError(f"cannot read JSON {path}: {error}") from error


def _atomic_json(path: Path | str, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_matrix(path: Path | str) -> dict[str, Any]:
    """Load and validate a frozen website compatibility preregistration."""

    matrix = _read_json(path)
    if not isinstance(matrix, dict):
        raise CompatibilityEvaluationError("matrix must be a JSON object")
    if matrix.get("schema_version") != MATRIX_SCHEMA_VERSION:
        raise CompatibilityEvaluationError("unsupported matrix schema_version")
    if not matrix.get("matrix_id") or not matrix.get("preregistered_at"):
        raise CompatibilityEvaluationError("matrix_id and preregistered_at are required")
    if matrix.get("locked_before_evidence") is not True:
        raise CompatibilityEvaluationError("matrix must declare locked_before_evidence=true")

    prompts = matrix.get("prompts")
    if not isinstance(prompts, list) or len(prompts) < 50:
        raise CompatibilityEvaluationError("website matrix must contain at least 50 prompts")
    prompt_ids = [row.get("id") for row in prompts if isinstance(row, dict)]
    if len(prompt_ids) != len(prompts) or any(not value for value in prompt_ids):
        raise CompatibilityEvaluationError("every prompt requires a nonempty id")
    if len(prompt_ids) != len(set(prompt_ids)):
        raise CompatibilityEvaluationError("prompt ids must be unique")
    for row in prompts:
        if not isinstance(row.get("prompt"), str) or not row["prompt"].strip():
            raise CompatibilityEvaluationError(f"prompt {row['id']} has no text")
        if not isinstance(row.get("tags"), list) or not row["tags"]:
            raise CompatibilityEvaluationError(f"prompt {row['id']} has no tags")
    observed_tags = {tag for row in prompts for tag in row["tags"]}
    missing_tags = sorted(REQUIRED_WEBSITE_TAGS - observed_tags)
    if missing_tags:
        raise CompatibilityEvaluationError(
            f"matrix is missing required website strata: {', '.join(missing_tags)}"
        )

    seeds = matrix.get("seeds")
    if not isinstance(seeds, list) or not seeds or any(not isinstance(seed, int) for seed in seeds):
        raise CompatibilityEvaluationError("matrix seeds must be a nonempty integer list")
    profiles = matrix.get("profiles")
    if (
        not isinstance(profiles, list)
        or not profiles
        or any(profile not in PROFILES for profile in profiles)
        or len(profiles) != len(set(profiles))
    ):
        raise CompatibilityEvaluationError("matrix profiles must be unique known profiles")

    protocol = matrix.get("protocol")
    if not isinstance(protocol, dict):
        raise CompatibilityEvaluationError("matrix protocol is required")
    if int(protocol.get("cycles", 0)) < 1:
        raise CompatibilityEvaluationError("protocol cycles must be positive")
    if int(protocol.get("token_budget", 0)) < 1:
        raise CompatibilityEvaluationError("protocol token_budget must be positive")
    if int(protocol.get("max_design_rounds", 0)) != 3:
        raise CompatibilityEvaluationError("max_design_rounds must remain preregistered at 3")

    thresholds = matrix.get("thresholds")
    required_thresholds = {f"A{number}" for number in range(3, 11)}
    if not isinstance(thresholds, dict) or not required_thresholds <= thresholds.keys():
        raise CompatibilityEvaluationError("thresholds A3 through A10 are required")
    baseline = matrix.get("frontier_baseline")
    if not isinstance(baseline, dict):
        raise CompatibilityEvaluationError("frontier_baseline preregistration is required")
    if tuple(baseline.get("metrics", ())) != FRONTIER_QUALITY_METRICS:
        raise CompatibilityEvaluationError("frontier baseline metrics changed from v1")
    if float(baseline.get("max_regression_percentage_points", -1)) != 2.0:
        raise CompatibilityEvaluationError("frontier regression bound must remain 2.0 points")
    return matrix


def matrix_digest(matrix: dict[str, Any]) -> str:
    """Content digest binding checkpoints and reports to the preregistration."""

    return _sha256(matrix)


def trial_key(prompt_id: str, seed: int, profile: str) -> str:
    if profile not in PROFILES:
        raise CompatibilityEvaluationError(f"unknown model profile: {profile}")
    return f"{profile}:{prompt_id}:seed-{seed}"


def new_checkpoint(
    matrix: dict[str, Any],
    *,
    phase: Literal["baseline", "candidate"],
    evidence_class: Literal["live", "offline_mock"],
) -> dict[str, Any]:
    return {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "matrix_id": matrix["matrix_id"],
        "matrix_sha256": matrix_digest(matrix),
        "phase": phase,
        "evidence_class": evidence_class,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "records": {},
    }


def load_checkpoint(
    path: Path | str,
    matrix: dict[str, Any],
    *,
    phase: Literal["baseline", "candidate"],
    evidence_class: Literal["live", "offline_mock"],
) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return new_checkpoint(matrix, phase=phase, evidence_class=evidence_class)
    checkpoint = _read_json(target)
    expected = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "matrix_id": matrix["matrix_id"],
        "matrix_sha256": matrix_digest(matrix),
        "phase": phase,
        "evidence_class": evidence_class,
    }
    for field, value in expected.items():
        if checkpoint.get(field) != value:
            raise CompatibilityEvaluationError(
                f"checkpoint {field} mismatch: {checkpoint.get(field)!r} != {value!r}"
            )
    if not isinstance(checkpoint.get("records"), dict):
        raise CompatibilityEvaluationError("checkpoint records must be an object")
    return checkpoint


def save_checkpoint(path: Path | str, checkpoint: dict[str, Any]) -> None:
    checkpoint["updated_at"] = _utc_now()
    _atomic_json(path, checkpoint)


def expected_trial_keys(matrix: dict[str, Any], profile: str) -> set[str]:
    return {
        trial_key(prompt["id"], seed, profile)
        for prompt in matrix["prompts"]
        for seed in matrix["seeds"]
    }


def _stage_rows(events: Iterable[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        inputs = list(event.inputs)
        if not inputs or inputs[0] != "website-stage" or len(inputs) < 5:
            continue
        diagnostics: list[dict[str, Any]] = []
        if len(inputs) >= 6:
            try:
                parsed = json.loads(inputs[5])
                if isinstance(parsed, list):
                    diagnostics = [item for item in parsed if isinstance(item, dict)]
            except json.JSONDecodeError:
                diagnostics = []
        try:
            attempt = int(inputs[4])
        except ValueError:
            attempt = 0
        rows.append(
            {
                "seq": event.seq,
                "stage": inputs[1],
                "outcome": inputs[2],
                "next_action": inputs[3],
                "attempt": attempt,
                "diagnostics": diagnostics,
            }
        )
    return rows


def _terminal_summary(root: Path) -> dict[str, Any] | None:
    path = root / "website-terminal.json"
    if not path.exists():
        return None
    value = _read_json(path)
    return value if isinstance(value, dict) else None


def _terminal_summary_complete(summary: dict[str, Any] | None) -> bool:
    if summary is None:
        return False
    required = {
        "failed_stage",
        "direct_calls",
        "compact_calls",
        "schema_failures_by_path",
        "manifest_wf_failures_by_code",
        "critic_refutations",
        "last_valid_intermediate",
        "resume_command",
        "diagnostics",
    }
    return (
        required <= summary.keys()
        and isinstance(summary.get("diagnostics"), list)
        and bool(summary.get("diagnostics"))
        and isinstance(summary.get("last_valid_intermediate"), str)
        and bool(summary["last_valid_intermediate"].strip())
        and isinstance(summary.get("resume_command"), str)
        and "deepreason" in summary["resume_command"]
        and "make" in summary["resume_command"]
    )


def _is_compact_recovery_signal(inputs: Iterable[str]) -> bool:
    values = list(inputs)
    if not values or values[0] != "website-design-mode":
        return False
    tokens = {value.strip().lower() for value in values[1:]}
    return "compact-recovery" in tokens or any("fallback" in value for value in tokens)


def _quality_counts(harness, events: list[Any], stage_rows: list[dict[str, Any]]) -> dict[str, Any]:
    from deepreason.ontology import Status
    from deepreason.programs import content_text

    browser = Counter()
    for artifact in harness.state.artifacts.values():
        if artifact.codec != "json" or artifact.provenance.role.value != "import":
            continue
        try:
            payload = json.loads(content_text(artifact, harness.blobs))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and payload.get("browser") and payload.get("verdict"):
            browser[str(payload["verdict"])] += 1

    carrier_ids = {artifact_id for artifact_id, _warrant_id in harness.state.carries}
    attackers = [
        artifact
        for artifact in harness.state.artifacts.values()
        if artifact.id in carrier_ids
    ]
    standing_attackers = sum(
        harness.state.status.get(artifact.id) == Status.ACCEPTED for artifact in attackers
    )
    addressed = {artifact_id for artifact_id, _problem_id in harness.state.addr}
    survivor_hv = [
        harness.state.hv[artifact_id]
        for artifact_id in addressed
        if harness.state.status.get(artifact_id) == Status.ACCEPTED
        and artifact_id in harness.state.hv
    ]
    integration_success = any(
        row["stage"] == "INTEGRATION_VALIDATE" and row["outcome"] == "success"
        for row in stage_rows
    )
    return {
        "browser_passes": browser.get("pass", 0),
        "browser_failures": browser.get("fail", 0),
        "attackers": len(attackers),
        "standing_attackers": standing_attackers,
        "survivor_hv_n": len(survivor_hv),
        "survivor_hv_sum": sum(survivor_hv),
        "integration_success": integration_success,
    }


def collect_trial_record(
    run_root: Path | str,
    *,
    prompt_id: str,
    seed: int,
    profile: str,
    evidence_class: Literal["live", "offline_mock"],
    output_paths: Iterable[Path | str] = (),
    execution_error: str | None = None,
) -> dict[str, Any]:
    """Materialize one terminal observation from a run root without mutation."""

    from deepreason.harness import Harness
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    root = Path(run_root)
    manifest = load_run_manifest(root / MANIFEST_NAME)
    harness = Harness(root, read_only=True)
    events = list(harness.log.read())
    stages = _stage_rows(events)
    terminal = _terminal_summary(root)

    roles: dict[str, dict[str, int]] = {}
    schema_failures: Counter[str] = Counter()
    total_tokens = 0
    total_ms = 0
    compact_calls = 0
    direct_calls = 0
    route_mismatch_calls = 0
    frozen_routes = [route for routes in manifest.roles.values() for route in routes]
    allowed_models = {route.model_id for route in frozen_routes}
    non_mock_routes = {
        (route.base_url, route.model_id)
        for route in frozen_routes
        if route.provider.lower() != "mock"
        and not route.base_url.lower().startswith(("mock:", "mock+"))
    }
    non_mock_route_families = {
        (route.base_url, route.model_id): route.family
        for route in frozen_routes
        if route.provider.lower() != "mock"
        and not route.base_url.lower().startswith(("mock:", "mock+"))
    }
    non_mock_transport_calls = 0
    mock_transport_calls = 0
    observed_non_mock_families: set[str] = set()
    for event in events:
        if event.llm is None:
            continue
        call = event.llm
        total_tokens += call.tokens
        total_ms += call.ms
        row = roles.setdefault(
            call.role,
            {
                "calls": 0,
                "traced_calls": 0,
                "first_pass_valid": 0,
                "eventual_valid": 0,
                "schema_exhausted": 0,
            },
        )
        row["calls"] += 1
        trace = list(call.attempt_trace)
        if trace:
            row["traced_calls"] += 1
            row["first_pass_valid"] += int(trace[0].valid)
            valid = any(attempt.valid for attempt in trace)
            row["eventual_valid"] += int(valid)
            row["schema_exhausted"] += int(
                not valid and not any(attempt.usage_unknown for attempt in trace)
            )
            for attempt in trace:
                if not attempt.valid:
                    schema_failures[attempt.validation_path or "<root>"] += 1
        if call.model not in allowed_models:
            route_mismatch_calls += 1
        if (call.endpoint, call.model) in non_mock_routes:
            non_mock_transport_calls += 1
            observed_non_mock_families.add(
                non_mock_route_families[(call.endpoint, call.model)]
            )
        else:
            mock_transport_calls += 1
        signal = list(event.inputs)[0] if event.inputs else ""
        if signal.startswith("website-compact-"):
            compact_calls += 1
        else:
            direct_calls += 1

    manifest_validation = [
        row for row in stages if row["stage"] == "MANIFEST_VALIDATE"
    ]
    manifest_valid_seq = next(
        (row["seq"] for row in manifest_validation if row["outcome"] == "success"), None
    )
    invalid_manifest_reached_post_validation = any(
        row["stage"] in POST_MANIFEST_STAGES
        and (manifest_valid_seq is None or row["seq"] < manifest_valid_seq)
        for row in stages
    )
    compile_success = next(
        (
            row
            for row in stages
            if row["stage"] == "MANIFEST_COMPILE" and row["outcome"] == "success"
        ),
        None,
    )
    max_design_attempt = max(
        (row["attempt"] for row in stages if row["stage"] in DESIGN_STAGES), default=0
    )
    design_terminal_failure = bool(
        terminal is not None and terminal.get("failed_stage") in DESIGN_STAGES
    )
    compact_recovery_declared = any(
        _is_compact_recovery_signal(event.inputs) for event in events
    )
    exported = [str(Path(path)) for path in output_paths]
    if not exported:
        export_root = root.parents[2] / "exports" / profile / f"{prompt_id}-s{seed}"
        if export_root.exists():
            exported = [str(path) for path in sorted(export_root.rglob("*")) if path.is_file()]
    export_success = any(path.lower().endswith(".html") for path in exported) and any(
        row["stage"] == "EXPORT" and row["outcome"] == "success" for row in stages
    )

    manifest_failures: Counter[str] = Counter()
    for row in stages:
        for diagnostic in row["diagnostics"]:
            code = diagnostic.get("code")
            if code:
                manifest_failures[str(code)] += 1
    if terminal is not None:
        manifest_failures.update(terminal.get("manifest_wf_failures_by_code", {}))
        schema_failures.update(terminal.get("schema_failures_by_path", {}))

    return {
        "state": "terminal",
        "key": trial_key(prompt_id, seed, profile),
        "prompt_id": prompt_id,
        "seed": seed,
        "profile": profile,
        "evidence_class": evidence_class,
        "run_root": str(root),
        "manifest_sha256": manifest.sha256,
        "frozen_models": sorted(allowed_models),
        "frozen_families": sorted(
            {route.family for routes in manifest.roles.values() for route in routes}
        ),
        "non_mock_frozen_families": sorted({
            route.family
            for routes in manifest.roles.values()
            for route in routes
            if route.provider.lower() != "mock"
            and not route.base_url.lower().startswith(("mock:", "mock+"))
        }),
        "observed_non_mock_families": sorted(observed_non_mock_families),
        "live_transport_observed": (
            evidence_class == "live" and non_mock_transport_calls > 0
        ),
        "execution_error": execution_error,
        "process": {
            "roles": roles,
            "tokens": total_tokens,
            "latency_ms": total_ms,
            "direct_calls": direct_calls,
            "compact_calls": compact_calls,
            "non_mock_transport_calls": non_mock_transport_calls,
            "mock_transport_calls": mock_transport_calls,
            "route_mismatch_calls": route_mismatch_calls,
            "schema_failures_by_path": dict(sorted(schema_failures.items())),
            "manifest_failures_by_code": dict(sorted(manifest_failures.items())),
        },
        "website": {
            "manifest_valid": manifest_valid_seq is not None,
            "manifest_valid_within_three_rounds": bool(
                manifest_valid_seq is not None
                and compile_success is not None
                and 1 <= compile_success["attempt"] <= 3
            ),
            "design_rounds_observed": max_design_attempt,
            "design_terminal_failure": design_terminal_failure,
            "terminal_summary_present": terminal is not None,
            "terminal_summary_complete": _terminal_summary_complete(terminal),
            "resumable_intermediate_present": bool(
                terminal and terminal.get("last_valid_intermediate")
            ),
            "invalid_manifest_reached_post_validation": (
                invalid_manifest_reached_post_validation
            ),
            "manifest_wf_success": manifest_valid_seq is not None,
            "component_wf_success": any(
                row["stage"] == "COMPONENT_BUILD" and row["outcome"] == "success"
                for row in stages
            ),
            "integration_wf_success": any(
                row["stage"] == "INTEGRATION_VALIDATE" and row["outcome"] == "success"
                for row in stages
            ),
            "export_success": export_success,
            "compact_recovery_declared": compact_recovery_declared,
            "exported_paths": exported,
        },
        "quality_counts": _quality_counts(harness, events, stages),
        "collected_at": _utc_now(),
    }


def _terminal_records(checkpoint: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        record
        for record in checkpoint.get("records", {}).values()
        if isinstance(record, dict) and record.get("state") == "terminal"
    ]


def frontier_family_coverage(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Report non-mock frontier-family coverage for acceptance eligibility."""

    families = sorted({
        str(family)
        for record in records
        for family in record.get("observed_non_mock_families", ())
        if str(family).strip()
    })
    return {
        "families": families,
        "family_count": len(families),
        "required_family_count": 2,
        "complete": len(families) >= 2,
    }


def aggregate_role_metrics(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Aggregate schema conformance by role using traced-call denominators."""

    totals: dict[str, Counter[str]] = {}
    for record in records:
        for role, row in record.get("process", {}).get("roles", {}).items():
            target = totals.setdefault(role, Counter())
            for field in (
                "calls",
                "traced_calls",
                "first_pass_valid",
                "eventual_valid",
                "schema_exhausted",
            ):
                target[field] += int(row.get(field, 0))
    result: dict[str, dict[str, Any]] = {}
    for role, counter in sorted(totals.items()):
        traced = counter["traced_calls"]
        calls = counter["calls"]
        result[role] = {
            **dict(counter),
            "trace_coverage": traced / calls if calls else None,
            "first_pass_valid_rate": counter["first_pass_valid"] / traced if traced else None,
            "eventual_valid_rate": counter["eventual_valid"] / traced if traced else None,
        }
    return result


def _safe_rate(numerator: int | float, denominator: int | float) -> float | None:
    return numerator / denominator if denominator else None


def _frontier_quality(records: Iterable[dict[str, Any]]) -> dict[str, float | None]:
    rows = list(records)
    browser_passes = sum(row.get("quality_counts", {}).get("browser_passes", 0) for row in rows)
    browser_failures = sum(
        row.get("quality_counts", {}).get("browser_failures", 0) for row in rows
    )
    attackers = sum(row.get("quality_counts", {}).get("attackers", 0) for row in rows)
    standing = sum(
        row.get("quality_counts", {}).get("standing_attackers", 0) for row in rows
    )
    hv_n = sum(row.get("quality_counts", {}).get("survivor_hv_n", 0) for row in rows)
    hv_sum = sum(row.get("quality_counts", {}).get("survivor_hv_sum", 0.0) for row in rows)
    return {
        "browser_oracle_pass_rate": _safe_rate(
            browser_passes, browser_passes + browser_failures
        ),
        "integration_success_rate": _safe_rate(
            sum(bool(row.get("quality_counts", {}).get("integration_success")) for row in rows),
            len(rows),
        ),
        "attack_validity_rate": _safe_rate(standing, attackers),
        "survivor_hv_mean": _safe_rate(hv_sum, hv_n),
    }


def threshold_verdict(
    value: float | int | None,
    *,
    minimum: float | int | None = None,
    maximum: float | int | None = None,
    eligible: bool = True,
    reason: str = "required evidence is incomplete",
) -> dict[str, Any]:
    """Return a four-state threshold verdict without treating missing data as failure."""

    if not eligible or value is None:
        return {"status": "insufficient_evidence", "observed": value, "reason": reason}
    passed = (minimum is None or value >= minimum) and (maximum is None or value <= maximum)
    return {
        "status": "pass" if passed else "fail",
        "observed": value,
        "minimum": minimum,
        "maximum": maximum,
    }


def compare_frontier_baseline(
    current: dict[str, float | None],
    baseline_report: dict[str, Any] | None,
    *,
    matrix_sha256: str,
    max_regression_percentage_points: float,
) -> dict[str, Any]:
    """Compare the locked frontier metric set to an eligible live baseline."""

    if baseline_report is None:
        return {
            "status": "insufficient_evidence",
            "reason": "no preregistered baseline report supplied",
            "metrics": {},
        }
    eligible = (
        baseline_report.get("phase") == "baseline"
        and baseline_report.get("matrix", {}).get("sha256") == matrix_sha256
        and baseline_report.get("evidence", {}).get("class") == "live"
        and baseline_report.get("evidence", {}).get("acceptance_claim_eligible") is True
        and baseline_report.get("coverage", {}).get("frontier", {}).get("complete") is True
        and baseline_report.get("coverage", {}).get("frontier", {}).get(
            "family_count", 0
        ) >= 2
    )
    if not eligible:
        return {
            "status": "insufficient_evidence",
            "reason": "baseline must be complete live evidence from the same matrix digest",
            "metrics": {},
        }
    baseline = baseline_report.get("metrics", {}).get("frontier_quality", {})
    rows: dict[str, Any] = {}
    all_pass = True
    for metric in FRONTIER_QUALITY_METRICS:
        before = baseline.get(metric)
        after = current.get(metric)
        if before is None or after is None:
            rows[metric] = {
                "status": "insufficient_evidence",
                "baseline": before,
                "current": after,
            }
            all_pass = False
            continue
        delta_pp = (after - before) * 100.0
        passed = delta_pp >= -max_regression_percentage_points
        rows[metric] = {
            "status": "pass" if passed else "fail",
            "baseline": before,
            "current": after,
            "delta_percentage_points": delta_pp,
            "minimum_delta_percentage_points": -max_regression_percentage_points,
        }
        all_pass = all_pass and passed
    if any(row["status"] == "insufficient_evidence" for row in rows.values()):
        status = "insufficient_evidence"
    else:
        status = "pass" if all_pass else "fail"
    return {"status": status, "metrics": rows}


def aggregate_report(
    matrix: dict[str, Any],
    checkpoint: dict[str, Any],
    *,
    frontier_baseline: dict[str, Any] | None = None,
    verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate a checkpoint and issue A3--A10 evidence-aware verdicts."""

    digest = matrix_digest(matrix)
    if checkpoint.get("matrix_sha256") != digest:
        raise CompatibilityEvaluationError("checkpoint does not match matrix digest")
    records = _terminal_records(checkpoint)
    by_profile = {
        profile: [row for row in records if row.get("profile") == profile]
        for profile in PROFILES
    }
    coverage: dict[str, dict[str, Any]] = {}
    record_keys = {row.get("key") for row in records}
    for profile in PROFILES:
        expected = expected_trial_keys(matrix, profile)
        observed = expected & record_keys
        coverage[profile] = {
            "expected": len(expected),
            "observed": len(observed),
            "complete": observed == expected,
            "missing": sorted(expected - observed),
        }

    evidence_classes = {row.get("evidence_class") for row in records}
    if evidence_classes == {"live"}:
        evidence_class = "live"
    elif evidence_classes == {"offline_mock"}:
        evidence_class = "offline_mock"
    elif evidence_classes:
        evidence_class = "mixed"
    else:
        evidence_class = "none"
    live_transport_coverage = _safe_rate(
        sum(bool(row.get("live_transport_observed")) for row in records), len(records)
    )
    live_only = evidence_class == "live"
    live_evidence = live_only and bool(records) and live_transport_coverage == 1.0

    role_metrics = {
        profile: aggregate_role_metrics(rows) for profile, rows in by_profile.items()
    }
    process_totals = {
        "terminal_trials": len(records),
        "tokens": sum(row.get("process", {}).get("tokens", 0) for row in records),
        "latency_ms": sum(row.get("process", {}).get("latency_ms", 0) for row in records),
        "direct_calls": sum(
            row.get("process", {}).get("direct_calls", 0) for row in records
        ),
        "compact_calls": sum(
            row.get("process", {}).get("compact_calls", 0) for row in records
        ),
        "route_mismatch_calls": sum(
            row.get("process", {}).get("route_mismatch_calls", 0) for row in records
        ),
    }
    schema_failures: Counter[str] = Counter()
    manifest_failures: Counter[str] = Counter()
    for row in records:
        schema_failures.update(row.get("process", {}).get("schema_failures_by_path", {}))
        manifest_failures.update(row.get("process", {}).get("manifest_failures_by_code", {}))

    website_metrics: dict[str, dict[str, Any]] = {}
    for profile, rows in by_profile.items():
        design_failures = [
            row for row in rows if row.get("website", {}).get("design_terminal_failure")
        ]
        website_metrics[profile] = {
            "trials": len(rows),
            "valid_manifest_within_three_rate": _safe_rate(
                sum(
                    bool(row.get("website", {}).get("manifest_valid_within_three_rounds"))
                    for row in rows
                ),
                len(rows),
            ),
            "manifest_wf_success_rate": _safe_rate(
                sum(bool(row.get("website", {}).get("manifest_wf_success")) for row in rows),
                len(rows),
            ),
            "component_wf_success_rate": _safe_rate(
                sum(bool(row.get("website", {}).get("component_wf_success")) for row in rows),
                len(rows),
            ),
            "integration_wf_success_rate": _safe_rate(
                sum(
                    bool(row.get("website", {}).get("integration_wf_success")) for row in rows
                ),
                len(rows),
            ),
            "export_success_rate": _safe_rate(
                sum(bool(row.get("website", {}).get("export_success")) for row in rows),
                len(rows),
            ),
            "design_terminal_failures": len(design_failures),
            "complete_design_terminal_diagnostics_rate": (
                _safe_rate(
                    sum(
                        bool(row.get("website", {}).get("terminal_summary_complete"))
                        for row in design_failures
                    ),
                    len(design_failures),
                )
                if design_failures
                else 1.0
            ),
            "invalid_manifest_post_validation_violations": sum(
                bool(
                    row.get("website", {}).get("invalid_manifest_reached_post_validation")
                )
                for row in rows
            ),
        }

    frontier_quality = _frontier_quality(by_profile["frontier"])
    baseline_rule = matrix["frontier_baseline"]
    frontier_comparison = compare_frontier_baseline(
        frontier_quality,
        frontier_baseline,
        matrix_sha256=digest,
        max_regression_percentage_points=float(
            baseline_rule["max_regression_percentage_points"]
        ),
    )

    hot_roles = matrix["hot_path_roles"]
    compact_roles = role_metrics["compact"]
    role_evidence_complete = all(
        role in compact_roles
        and compact_roles[role].get("trace_coverage") == 1.0
        and compact_roles[role].get("traced_calls", 0) > 0
        for role in hot_roles
    )
    first_pass_rates = {
        role: compact_roles.get(role, {}).get("first_pass_valid_rate") for role in hot_roles
    }
    eventual_rates = {
        role: compact_roles.get(role, {}).get("eventual_valid_rate") for role in hot_roles
    }
    compact_eligible = (
        live_evidence and coverage["compact"]["complete"] and role_evidence_complete
    )
    a3_value = min(
        (value for value in first_pass_rates.values() if value is not None), default=None
    )
    a4_value = min(
        (value for value in eventual_rates.values() if value is not None), default=None
    )

    target_model = matrix["target_small_model_id"]
    small_rows = [
        row
        for row in by_profile["compact"]
        if row.get("frozen_models") == [target_model]
    ]
    small_model_complete = (
        live_evidence
        and coverage["compact"]["complete"]
        and len(small_rows) == coverage["compact"]["expected"]
    )
    a5_value = _safe_rate(
        sum(
            bool(row.get("website", {}).get("manifest_valid_within_three_rounds"))
            for row in small_rows
        ),
        len(small_rows),
    )
    design_failures = [
        row for row in small_rows if row.get("website", {}).get("design_terminal_failure")
    ]
    a6_value = (
        _safe_rate(
            sum(
                bool(row.get("website", {}).get("terminal_summary_complete"))
                for row in design_failures
            ),
            len(design_failures),
        )
        if design_failures
        else 1.0
    )
    a7_violations = sum(
        bool(row.get("website", {}).get("invalid_manifest_reached_post_validation"))
        for row in records
    )
    all_profiles_complete = all(
        coverage[profile]["complete"] for profile in matrix["profiles"]
    )

    verification_pass = bool(
        verification
        and verification.get("scope") == "full"
        and verification.get("passed") is True
        and verification.get("evidence_class") == "local_execution"
    )
    frontier_rows = by_profile["frontier"]
    frontier_families = frontier_family_coverage(frontier_rows)
    coverage["frontier"].update(frontier_families)
    frontier_eligible = (
        live_evidence
        and coverage["frontier"]["complete"]
        and frontier_families["complete"]
    )
    compact_overhead_violations = sum(
        row.get("process", {}).get("compact_calls", 0)
        for row in frontier_rows
        if row.get("process", {}).get("compact_calls", 0)
        and not row.get("website", {}).get("compact_recovery_declared")
    )

    a3 = threshold_verdict(
        a3_value,
        minimum=float(matrix["thresholds"]["A3"]["minimum_rate"]),
        eligible=compact_eligible,
        reason="requires complete live compact coverage and traced hot-path roles",
    )
    a3["per_role"] = first_pass_rates
    a4 = threshold_verdict(
        a4_value,
        minimum=float(matrix["thresholds"]["A4"]["minimum_rate"]),
        eligible=compact_eligible,
        reason="requires complete live compact coverage and traced hot-path roles",
    )
    a4["per_role"] = eventual_rates
    a5 = threshold_verdict(
        a5_value,
        minimum=float(matrix["thresholds"]["A5"]["minimum_rate"]),
        eligible=small_model_complete,
        reason=f"requires the complete live compact matrix pinned only to {target_model}",
    )
    a6 = threshold_verdict(
        a6_value,
        minimum=1.0,
        eligible=small_model_complete,
        reason="requires complete live small-model coverage",
    )
    a6["design_failures"] = len(design_failures)
    a7 = threshold_verdict(
        a7_violations,
        maximum=0,
        eligible=live_evidence and all_profiles_complete,
        reason="requires complete live coverage for every preregistered profile",
    )
    a8 = threshold_verdict(
        int(verification_pass) if verification is not None else None,
        minimum=1,
        eligible=verification is not None,
        reason="requires a supplied full-suite local-execution verification record",
    )
    a9 = {
        "status": (
            frontier_comparison["status"]
            if frontier_eligible and checkpoint.get("phase") == "candidate"
            else "insufficient_evidence"
        ),
        "maximum_regression_percentage_points": baseline_rule[
            "max_regression_percentage_points"
        ],
        "comparison": frontier_comparison,
        "frontier_family_coverage": frontier_families,
    }
    if checkpoint.get("phase") == "baseline":
        a9["status"] = "not_applicable"
        a9["reason"] = "this report is the preregistered baseline phase"
    a10 = threshold_verdict(
        compact_overhead_violations,
        maximum=0,
        eligible=frontier_eligible,
        reason="requires complete live frontier coverage across at least two families",
    )
    a10["frontier_compact_calls_without_recovery"] = compact_overhead_violations

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": f"{matrix['matrix_id']}:{checkpoint['phase']}:{digest[:12]}",
        "generated_at": _utc_now(),
        "phase": checkpoint["phase"],
        "matrix": {
            "id": matrix["matrix_id"],
            "sha256": digest,
            "preregistered_at": matrix["preregistered_at"],
            "prompt_count": len(matrix["prompts"]),
            "seeds": matrix["seeds"],
            "profiles": matrix["profiles"],
        },
        "evidence": {
            "class": evidence_class,
            "acceptance_claim_eligible": live_evidence,
            "live_transport_coverage": live_transport_coverage,
            "note": (
                "live eligibility requires non-mock provider calls in every terminal record"
                if evidence_class == "live"
                else "offline/mock observations test plumbing only and cannot establish A3-A10"
            ),
        },
        "coverage": coverage,
        "metrics": {
            "process": process_totals,
            "roles_by_profile": role_metrics,
            "schema_failures_by_path": dict(sorted(schema_failures.items())),
            "manifest_failures_by_code": dict(sorted(manifest_failures.items())),
            "website_by_profile": website_metrics,
            "frontier_quality": frontier_quality,
        },
        "acceptance": {
            "A3": a3,
            "A4": a4,
            "A5": a5,
            "A6": a6,
            "A7": a7,
            "A8": a8,
            "A9": a9,
            "A10": a10,
        },
        "frontier_comparison": frontier_comparison,
        "verification": verification,
        "records_sha256": _sha256(records),
        "limitations": [
            "Provider sampling seeds are not part of the current Route contract; seed values are fixed replicate identifiers and Python-local seeds, not a claim of provider determinism.",
            "A9 is unavailable until a complete eligible live baseline report from the identical matrix digest is supplied.",
            "Compatibility metrics are process/reporting data only and never participate in labels or warrant validity.",
        ],
    }


def _write_running_record(
    checkpoint: dict[str, Any],
    *,
    key: str,
    prompt_id: str,
    seed: int,
    profile: str,
    run_root: Path,
) -> None:
    checkpoint["records"][key] = {
        "state": "running",
        "key": key,
        "prompt_id": prompt_id,
        "seed": seed,
        "profile": profile,
        "evidence_class": "live",
        "run_root": str(run_root),
        "started_at": _utc_now(),
    }


def run_live_matrix(
    matrix: dict[str, Any],
    checkpoint: dict[str, Any],
    *,
    checkpoint_path: Path | str,
    config_path: Path | str,
    work_dir: Path | str,
    profiles: Iterable[str] | None = None,
    prompt_ids: Iterable[str] | None = None,
    single_model: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Run pending live trials, checkpointing before and after every trial."""

    if checkpoint.get("evidence_class") != "live":
        raise CompatibilityEvaluationError("live runner requires a live checkpoint")
    from deepreason.config import load
    from deepreason.easy import make
    from deepreason.run_manifest import bind_run_manifest, compile_run_manifest

    selected_profiles = list(profiles or matrix["profiles"])
    if any(profile not in matrix["profiles"] for profile in selected_profiles):
        raise CompatibilityEvaluationError("selected profile was not preregistered")
    selected_ids = set(prompt_ids or [row["id"] for row in matrix["prompts"]])
    known_ids = {row["id"] for row in matrix["prompts"]}
    if not selected_ids <= known_ids:
        raise CompatibilityEvaluationError(
            f"unknown prompt ids: {', '.join(sorted(selected_ids - known_ids))}"
        )
    source_config = load(Path(config_path))
    base = Path(work_dir)
    protocol = matrix["protocol"]
    compiled_at = protocol["manifest_compiled_at"]
    completed = 0

    for profile in selected_profiles:
        for prompt in matrix["prompts"]:
            if prompt["id"] not in selected_ids:
                continue
            for seed in matrix["seeds"]:
                key = trial_key(prompt["id"], seed, profile)
                if checkpoint["records"].get(key, {}).get("state") == "terminal":
                    continue
                if limit is not None and completed >= limit:
                    return checkpoint
                run_root = base / "roots" / profile / f"{prompt['id']}-s{seed}"
                out_dir = base / "exports" / profile / f"{prompt['id']}-s{seed}"
                manifest = compile_run_manifest(
                    source_config,
                    model_profile=profile,
                    single_model=single_model,
                    rubric_policy="forbid",
                    compiled_at=compiled_at,
                )
                bind_run_manifest(manifest, run_root)
                _write_running_record(
                    checkpoint,
                    key=key,
                    prompt_id=prompt["id"],
                    seed=seed,
                    profile=profile,
                    run_root=run_root,
                )
                save_checkpoint(checkpoint_path, checkpoint)

                # The current provider Route has no sampling-seed field. This
                # fixes any Python-local randomness and records a replicate id
                # without pretending that provider sampling is deterministic.
                random.seed(seed)
                outputs: list[Path] = []
                execution_error = None
                try:
                    outputs = make(
                        prompt["prompt"],
                        out=str(out_dir),
                        cycles=int(protocol["cycles"]),
                        token_budget=int(protocol["token_budget"]),
                        config=str(config_path),
                        root=str(run_root),
                        echo=lambda message: print(f"[{key}] {message}"),
                        staged=True,
                        chunked=True,
                    )
                except Exception as error:  # noqa: BLE001 - preserve failed live evidence
                    execution_error = f"{type(error).__name__}: {error}"[:2000]
                checkpoint["records"][key] = collect_trial_record(
                    run_root,
                    prompt_id=prompt["id"],
                    seed=seed,
                    profile=profile,
                    evidence_class="live",
                    output_paths=outputs,
                    execution_error=execution_error,
                )
                save_checkpoint(checkpoint_path, checkpoint)
                completed += 1
    return checkpoint


def import_offline_observations(
    checkpoint: dict[str, Any], observations_path: Path | str
) -> dict[str, Any]:
    """Import fixtures while forcibly labelling them offline/mock."""

    payload = _read_json(observations_path)
    if isinstance(payload, dict):
        payload = payload.get("records")
    if not isinstance(payload, list):
        raise CompatibilityEvaluationError("offline observations must be a list")
    for source in payload:
        if not isinstance(source, dict):
            raise CompatibilityEvaluationError("offline observation must be an object")
        row = json.loads(json.dumps(source))
        key = row.get("key") or trial_key(row["prompt_id"], int(row["seed"]), row["profile"])
        row.update(
            {
                "state": "terminal",
                "key": key,
                "evidence_class": "offline_mock",
                "live_transport_observed": False,
                "offline_source": str(observations_path),
            }
        )
        checkpoint["records"][key] = row
    return checkpoint


def load_optional_report(path: Path | str | None) -> dict[str, Any] | None:
    if path is None:
        return None
    value = _read_json(path)
    if not isinstance(value, dict):
        raise CompatibilityEvaluationError(f"report {path} must be an object")
    return value


def write_report(path: Path | str, report: dict[str, Any]) -> None:
    _atomic_json(path, report)
