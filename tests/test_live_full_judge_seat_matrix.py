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
