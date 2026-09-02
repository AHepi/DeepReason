"""Offline contract tests for the exact full-judge campaign runner."""

from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import threading
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
TRANCHE = ROOT / "experiments/2026-09-01-change-live-full-judge-seat-matrix"
MATRIX_PATH = TRANCHE / "matrix.py"
DOMAIN_PATH = TRANCHE / "MATRIX_DOMAIN.json"


@pytest.fixture(scope="module")
def matrix():
    if not MATRIX_PATH.is_file():
        pytest.fail(f"absent experiment module: {MATRIX_PATH}")
    spec = importlib.util.spec_from_file_location("live_full_judge_matrix", MATRIX_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def domain(matrix):
    return matrix.load_domain(DOMAIN_PATH)


def refusal(matrix, code):
    return pytest.raises(matrix.MatrixRefusal, match=code)


def test_domain_fixture_counts_are_exact(matrix, domain):
    assert matrix.domain_counts(domain) == {
        "seat": 5_387_888,
        "transport": 28_512,
        "combined": 5_416_400,
    }
    assert matrix.seat_counts(22) == {
        "judge_pairs": 484,
        "core_courts": 10_648,
        "no_variator": 234_256,
        "with_variator": 5_153_632,
        "total": 5_387_888,
    }
    assert matrix.transport_counts(22) == {
        "per_model": 1_296,
        "total": 28_512,
    }


def test_domain_mini_catalog_is_literal_cartesian_and_ordered(matrix):
    models = ["model-a", "model-b"]
    rows = list(matrix.iter_seat_cases(models, catalog_sha256="c" * 64))
    expected = {
        (*parts, None) for parts in itertools.product(models, repeat=4)
    } | set(itertools.product(models, repeat=5))
    keyed = {
        (r["critic"], r["defender"], r["judge0"], r["judge1"], r["variator"]): r
        for r in rows
    }
    assert set(keyed) == expected
    assert len(rows) == len(keyed) == 48
    forward = keyed[("model-a", "model-a", "model-a", "model-b", None)]
    reverse = keyed[("model-a", "model-a", "model-b", "model-a", None)]
    assert forward["case_id"] != reverse["case_id"]


def test_structural_domain_ids_and_frozen_digest(matrix, domain):
    case_ids = matrix.structural_case_ids(domain)
    assert len(case_ids) == len(set(case_ids)) == 452
    assert all(case_id.startswith("sha256:") for case_id in case_ids)
    assert matrix.length_prefixed_set_digest(case_ids) == (
        "b8c2e8c3d1d650c39ef46c59d499c954b36ec9202cddaab740d2c525148cf895"
    )


def test_catalog_raw_identity_and_kimi_k3_normalization(matrix, domain):
    rule = domain["catalog_rule"]
    for raw in rule["positive_vectors"]:
        assert "kimik3" in matrix.normalize_model_id(raw)
    for raw in rule["negative_vectors"]:
        assert "kimik3" not in matrix.normalize_model_id(raw)
    frozen = matrix.freeze_catalog(["zeta", "A-B", "ab", "kimi-k2.6"])
    assert frozen["model_ids"] == ["A-B", "ab", "kimi-k2.6", "zeta"]
    assert frozen["excluded"] == []
    excluded = matrix.freeze_catalog(["safe", "KIMI K3:cloud"])
    assert excluded["model_ids"] == ["safe"]
    assert excluded["excluded"] == [
        {"model_id": "KIMI K3:cloud", "code": "KIMI_K3_FORBIDDEN"}
    ]
    with refusal(matrix, "DUPLICATE_RAW_MODEL_ID"):
        matrix.freeze_catalog(["same", "same"])


def test_reasoning_validates_exact_final_wire_fields(matrix):
    body = matrix.build_provider_body("minimax-m3", "low")
    body["prose"] = "maximum flexibility is welcome"
    matrix.validate_provider_body(body)
    assert body["model"] == "minimax-m3"
    assert body["reasoning_effort"] == "low"
    assert matrix.build_provider_body("glm-5.3", 2_000)["reasoning_effort"] == "low"
    for value in ("high", "HIGH", "max", "xhigh", 2_001):
        with refusal(matrix, "FORBIDDEN_REASONING_EFFORT"):
            matrix.build_provider_body("glm-5.3", value)
    with refusal(matrix, "REASONING_EFFORT_REQUIRED"):
        matrix.build_provider_body("glm-5.3", None)
    with refusal(matrix, "REASONING_EFFORT_REQUIRED"):
        matrix.validate_provider_body({"model": "glm-5.3"})
    with refusal(matrix, "KIMI_K3_FORBIDDEN"):
        matrix.validate_provider_body({"model": "kimi_k3/cloud", "reasoning_effort": "low"})


def test_authority_and_contracts_are_guarded_before_dispatch(matrix):
    body = matrix.build_provider_body("glm-5.3", "low")
    manifest = {
        "authority": "defended_trial",
        "trial_contracts": {
            "defender[0]": ["defender.direct.v1"],
            "judge[0]": ["judgeruling.direct.v1"],
            "judge[1]": ["judgeruling.direct.v1"],
        },
    }
    dispatched = []
    complete = lambda request: dispatched.append(request) or "ok"
    assert matrix.guarded_complete("defended_trial", manifest, body, complete) == "ok"
    assert dispatched == [body]
    for config_authority, candidate in (
        ("observe_only", manifest),
        ("defended_trial", {**manifest, "authority": "observe_only"}),
        ("defended_trial", {**manifest, "trial_contracts": {}}),
    ):
        with refusal(matrix, "DEFENDED_TRIAL_NOT_AUTHORIZED"):
            matrix.guarded_complete(config_authority, candidate, body, complete)
    assert dispatched == [body]


def test_concurrency_never_exceeds_three_when_more_workers_requested(matrix):
    lock, release = threading.Lock(), threading.Event()
    state = {"active": 0, "peak": 0}

    def complete():
        with lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
            if state["peak"] == 3:
                release.set()
        assert release.wait(2)
        time.sleep(0.01)
        with lock:
            state["active"] -= 1
        return "ok"

    assert matrix.run_bounded([complete] * 9, workers=9) == ["ok"] * 9
    assert state == {"active": 0, "peak": 3}


def test_machine_wide_lock_refuses_second_coordinator(matrix, tmp_path):
    lock_path = tmp_path / "campaign.lock"
    with matrix.coordinator_lock(lock_path):
        with refusal(matrix, "COORDINATOR_ALREADY_RUNNING"):
            with matrix.coordinator_lock(lock_path):
                pass


def test_credential_serialization_is_allowlisted_and_secret_scanned(matrix):
    secret = "sentinel-secret-never-persist"
    safe = json.loads(matrix.safe_result_bytes({
        "case_id": "case-1", "status": "trial_outcome", "message": "valid prose",
        "headers": {"Authorization": secret}, "arbitrary": "discard me",
    }, secret=secret))
    assert safe == {"case_id": "case-1", "message": "valid prose", "status": "trial_outcome"}
    withheld = matrix.safe_result_bytes({
        "case_id": "case-2", "status": "unexpected_error", "message": secret,
    }, secret=secret)
    assert secret.encode() not in withheld
    assert json.loads(withheld)["code"] == "SECRET_BEARING_DIAGNOSTIC_WITHHELD"


def test_terminal_writes_are_atomic_immutable_and_resume_rotates(matrix, tmp_path, monkeypatch):
    target = tmp_path / "terminal.json"
    replaced = []
    real_replace = matrix.os.replace
    def recording_replace(src, dst):
        replaced.append((Path(src), Path(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(matrix.os, "replace", recording_replace)
    matrix.atomic_terminal_write(target, {"case_id": "one", "status": "trial_outcome"})
    original = target.read_bytes()
    assert replaced and replaced[-1][1] == target
    with refusal(matrix, "TERMINAL_RESULT_IMMUTABLE"):
        matrix.atomic_terminal_write(target, {"case_id": "one", "status": "changed"})
    assert target.read_bytes() == original

    attempts = tmp_path / "attempts"
    first = matrix.prepare_attempt(attempts, domain_sha256="domain-a", catalog_sha256="catalog-a")
    sentinel = first / "immutable.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    matrix.mark_interrupted(first)
    second = matrix.prepare_attempt(attempts, domain_sha256="domain-a", catalog_sha256="catalog-a")
    assert (first.name, second.name) == ("attempt-0001", "attempt-0002")
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
    with refusal(matrix, "DOMAIN_DIGEST_MISMATCH"):
        matrix.prepare_attempt(attempts, domain_sha256="domain-b", catalog_sha256="catalog-a")
    with refusal(matrix, "CATALOG_DIGEST_MISMATCH"):
        matrix.prepare_attempt(attempts, domain_sha256="domain-a", catalog_sha256="catalog-b")


def test_topology_direct_config_compiles_explicit_defended_two_and_three_judges(
    matrix, monkeypatch
):
    from deepreason.config import Config

    observed_policies = []
    shipped_compile = matrix.compile_run_manifest

    def capture_policy(*args, **kwargs):
        observed_policies.append(kwargs.get("criticism_policy"))
        return shipped_compile(*args, **kwargs)

    monkeypatch.setattr(matrix, "compile_run_manifest", capture_policy)
    for judge_count in (2, 3):
        built = matrix.compile_stubbed_court(judge_count=judge_count)
        config, manifest = built["config"], built["manifest"]
        assert isinstance(config, Config)
        assert config.ENGAGED_CRITICISM_AUTHORITY == "defended_trial"
        assert len(config.roles["judge"]) == len(manifest.roles["judge"]) == judge_count
        assert manifest.criticism_policy.authority == "defended_trial"
        grants = {
            (entry.role, entry.seat): {grant.contract_id for grant in entry.contracts}
            for entry in manifest.route_seat_behavioral_capability_plan.entries
        }
        assert "defender.direct.v1" in grants[("defender", 0)]
        for seat in range(judge_count):
            assert "judgeruling.direct.v1" in grants[("judge", seat)]
    assert len(observed_policies) == 2
    assert all(policy is not None and policy.authority == "defended_trial"
               for policy in observed_policies)


def test_managed_path_reports_its_shipped_first_boundary_not_direct_success(matrix):
    same_model = matrix.classify_managed_path(diverse_nonjudge=False)
    diverse = matrix.classify_managed_path(diverse_nonjudge=True)
    assert same_model == {
        "construction": "managed_preparation",
        "status": "configuration_refused",
        "stage": "trial_preflight",
        "code": "single-judge-seat",
        "dispatch_history": ["critic"],
    }
    assert diverse["construction"] == "managed_preparation"
    assert diverse["status"] == "configuration_refused"
    assert diverse["stage"] == "trial_preflight"
    assert diverse["code"] == "SECOND_JUDGE_FAMILY_REQUIRED"
    assert diverse["dispatch_history"] == ["critic"]


@pytest.mark.parametrize(
    ("paraphrases", "expected"),
    [
        (None, ["critic", "defender", "judge:0", "judge:1"]),
        (("restatement one", "restatement two"), [
            "critic", "defender", "judge:0", "judge:1", "variator",
            "judge:paraphrase:0:0", "judge:paraphrase:0:1",
            "judge:paraphrase:1:0", "judge:paraphrase:1:1",
        ]),
    ],
)
def test_sequence_fixed_ungrounded_court_reaches_each_required_dispatch(
    matrix, tmp_path, paraphrases, expected
):
    row = matrix.run_stubbed_court(
        tmp_path / ("plain" if paraphrases is None else "varied"),
        judge_count=2,
        returned_paraphrases=paraphrases,
    )
    assert row["status"] == "trial_outcome"
    assert row["first_refusal"] is None
    assert row["target_formally_backed"] is False
    assert row["dispatch_extent"] == expected


def test_typed_first_refusal_is_terminal_and_preserves_exact_history(matrix, tmp_path):
    row = matrix.run_stubbed_court(
        tmp_path / "one-judge", judge_count=1, returned_paraphrases=None
    )
    assert row["status"] == "configuration_refused"
    assert row["first_refusal"]["stage"] == "trial_preflight"
    assert row["first_refusal"]["code"] == "SECOND_JUDGE_FAMILY_REQUIRED"
    assert "SECOND_JUDGE_FAMILY_REQUIRED" in row["first_refusal"]["message"]
    assert row["dispatch_extent"] == ["critic"]


def test_typed_semantic_trial_outcome_is_never_a_configuration_refusal(matrix, tmp_path):
    row = matrix.run_stubbed_court(
        tmp_path / "sustained", judge_count=2,
        returned_paraphrases=("unreached",), judge_verdict="pass",
    )
    assert row["status"] == "trial_outcome"
    assert row["outcome_code"] == "defence-sustained"
    assert row["dispatch_extent"] == ["critic", "defender", "judge:0", "judge:1"]
    assert row["variator_reachability"] == "not_exercised_by_outcome"


def test_typed_prose_receipt_survives_parser_failure_separately(matrix, tmp_path):
    prose = "A human-readable objection remains available for inspection."
    receipts = matrix.persist_response_receipts(
        tmp_path, prose, parser_outcome="invalid", schema_outcome="not_run",
        fallback_events=("json_parse_failed",),
    )
    prose_receipt = receipts["prose_receipt"]
    parser_receipt = receipts["parser_receipt"]
    assert prose_receipt["byte_count"] == len(prose.encode())
    assert len(prose_receipt["sha256"]) == 64
    assert (tmp_path / prose_receipt["blob_ref"]).read_text() == prose
    assert parser_receipt == {
        "parser_outcome": "invalid",
        "schema_outcome": "not_run",
        "fallback_events": ["json_parse_failed"],
        "structured_value": None,
    }


def test_soak_wrapper_registers_experiment_case_without_editing_shipped_driver(matrix):
    driver = ROOT / "scripts/cycle_soak.py"
    before = driver.read_bytes()
    cycle_soak, case = matrix.install_soak_case()
    assert driver.read_bytes() == before
    assert cycle_soak.CASES["judge-matrix"] is case
    assert isinstance(case, cycle_soak.SoakCase)
    assert case.id == "judge-matrix" and case.default_cycles == 8
    assert "kimik3" not in matrix.normalize_model_id(case.description)
