"""Offline contract tests for the exact full-judge campaign runner."""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
TRANCHE = ROOT / "experiments/2026-09-01-change-live-full-judge-seat-matrix"
MATRIX_PATH = TRANCHE / "matrix.py"
DOMAIN_PATH = TRANCHE / "MATRIX_DOMAIN.json"
FULL_CROSS_DOMAIN_PATH = TRANCHE / "FULL_CROSS_DOMAIN.json"


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


def _narrow_full_cross_domain(domain, **axis_overrides):
    """Return a small literal subdomain without mutating the frozen fixture."""
    narrowed = json.loads(json.dumps(domain))
    narrowed["finite_axes"].update(axis_overrides)
    return narrowed


def _literal_full_cross_payloads(domain, model_ids, catalog_sha256):
    """Independent, deliberately simple Cartesian membership oracle."""
    axes = domain["finite_axes"]
    ordered_models = sorted(model_ids, key=lambda value: value.encode("utf-8"))
    seat_tuples = [
        {
            "model_id": model_id,
            "model_profile": profile,
            "output_mode": output_mode,
            "output_mechanism": output_mechanism,
            "reasoning": reasoning,
        }
        for model_id, profile, output_mode, output_mechanism, reasoning
        in itertools.product(
            ordered_models,
            axes["model_profile_per_seat"],
            axes["output_mode_per_seat"],
            axes["output_mechanism_per_seat"],
            axes["reasoning_per_seat"],
        )
    ]
    payloads = []
    for judge_count in axes["judge_count"]:
        judge_roles = [f"judge:{seat}" for seat in range(judge_count)]
        for with_variator in (False, True):
            roles = ["critic", "defender", *judge_roles]
            paraphrases = [None]
            if with_variator:
                roles.append("variator")
                paraphrases = axes["paraphrase_count_with_variator"]
            for split_protocol, paraphrase_count, assignments in itertools.product(
                axes["split_protocol"],
                paraphrases,
                itertools.product(seat_tuples, repeat=len(roles)),
            ):
                payloads.append({
                    "schema": "deepreason.full-cross-judge-case.v1",
                    "catalog_sha256": catalog_sha256,
                    "judge_count": judge_count,
                    "split_protocol": split_protocol,
                    "paraphrase_count": paraphrase_count,
                    "seats": [
                        {"role": role, **assignment}
                        for role, assignment in zip(roles, assignments)
                    ],
                })
    return payloads


def _literal_case_id(payload):
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _full_cross_identity(row):
    return {
        key: row[key]
        for key in (
            "schema", "catalog_sha256", "judge_count", "split_protocol",
            "paraphrase_count", "seats",
        )
    }


def _read_frozen_full_cross_domain():
    return json.loads(FULL_CROSS_DOMAIN_PATH.read_text(encoding="utf-8"))


def _minimal_full_cross_domain(domain, **overrides):
    axes = {
        "judge_count": [2, 3],
        "split_protocol": ["off"],
        "model_profile_per_seat": ["standard"],
        "output_mode_per_seat": ["json_object"],
        "output_mechanism_per_seat": ["json_text"],
        "reasoning_per_seat": [{"kind": "string", "value": "low"}],
        "paraphrase_count_with_variator": [0],
        "paraphrase_count_without_variator": None,
    }
    axes.update(overrides)
    return _narrow_full_cross_domain(domain, **axes)


def _live_seat(**overrides):
    seat = {
        "role": "judge:0",
        "model_id": "glm-5.3",
        "model_profile": "frontier",
        "output_mode": "json_object",
        "output_mechanism": "native_json_schema",
        "reasoning": {"kind": "string", "value": "none"},
    }
    seat.update(overrides)
    return seat


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


def test_live_resume_excludes_integrity_stopped_attempts(matrix, tmp_path):
    root = tmp_path / "live-seat-matrix"
    quarantined = root / "attempt-0001"
    results = quarantined / "results"
    results.mkdir(parents=True)
    case_payload = {"schema": matrix.SEAT_SCHEMA, "ordinal": 0}
    case_id = matrix._sha256_id(case_payload)
    matrix.atomic_terminal_write(
        results / f"{case_id.removeprefix('sha256:')}.json",
        {
            "status": "trial_outcome",
            "domain_sha256": "domain-a",
            "catalog_sha256": "catalog-a",
            "case_payload": case_payload,
            "case_id": case_id,
        },
    )
    matrix._atomic_bytes(
        quarantined / "INTEGRITY_STOP.json",
        matrix.canonical_json({
            "schema": "deepreason.live_attempt_integrity_stop.v1",
            "status": "quarantined",
            "result_disposition": "preserved_excluded",
        }),
    )

    assert matrix._load_live_terminals(
        root,
        domain_sha256="domain-a",
        catalog_sha256="catalog-a",
        secret="sentinel-secret-never-persist",
    ) == {}


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


def test_full_cross_domain_loader_preserves_the_frozen_document(matrix):
    assert matrix.load_full_cross_domain(FULL_CROSS_DOMAIN_PATH) == (
        _read_frozen_full_cross_domain()
    )


def test_full_cross_fixture_counts_are_exact_for_both_judge_topologies(matrix):
    domain = _read_frozen_full_cross_domain()
    assert matrix.full_cross_seat_tuple_count(domain, model_count=22) == 1_584
    assert matrix.full_cross_counts(domain, model_count=22) == {
        "seat_tuples": 1_584,
        "judge_count_2": 149_596_687_470_624_768,
        "judge_count_3": 236_961_152_953_469_632_512,
        "total": 237_110_749_640_940_257_280,
    }


def test_full_cross_tiny_domain_is_the_literal_cartesian_product(matrix):
    frozen = _read_frozen_full_cross_domain()
    domain = _minimal_full_cross_domain(
        frozen,
        split_protocol=["auto", "off"],
        model_profile_per_seat=["compact", "frontier"],
        paraphrase_count_with_variator=[-1, 2],
    )
    catalog_sha256 = "a" * 64
    rows = list(matrix.iter_full_cross_cases(
        domain, ["model-a"], catalog_sha256=catalog_sha256,
        criticism_authority="defended_trial",
    ))
    expected_payloads = _literal_full_cross_payloads(
        domain, ["model-a"], catalog_sha256
    )
    expected_ids = {_literal_case_id(payload) for payload in expected_payloads}
    actual_ids = {row["case_id"] for row in rows}

    assert matrix.full_cross_counts(domain, model_count=1) == {
        "seat_tuples": 2,
        "judge_count_2": 160,
        "judge_count_3": 320,
        "total": 480,
    }
    assert len(rows) == len(actual_ids) == len(expected_ids) == 480
    assert actual_ids == expected_ids
    assert {_literal_case_id(_full_cross_identity(row)) for row in rows} == actual_ids
    assert {row["judge_count"] for row in rows} == {2, 3}
    assert {row["split_protocol"] for row in rows} == {"auto", "off"}
    assert {row["paraphrase_count"] for row in rows if row["seats"][-1]["role"] == "variator"} == {-1, 2}
    assert {row["paraphrase_count"] for row in rows if row["seats"][-1]["role"] != "variator"} == {None}
    assert all(row["criticism_authority"] == "defended_trial" for row in rows)


def test_full_cross_ordered_judge_reversal_changes_case_identity(matrix):
    domain = _minimal_full_cross_domain(
        _read_frozen_full_cross_domain(), judge_count=[2]
    )
    rows = list(matrix.iter_full_cross_cases(
        domain, ["same-family/model-a", "same-family/model-b"],
        catalog_sha256="b" * 64, criticism_authority="defended_trial",
    ))

    def find(judge0, judge1):
        for row in rows:
            seats = {seat["role"]: seat for seat in row["seats"]}
            if (
                row["paraphrase_count"] is None
                and seats["critic"]["model_id"] == "same-family/model-a"
                and seats["defender"]["model_id"] == "same-family/model-a"
                and seats["judge:0"]["model_id"] == judge0
                and seats["judge:1"]["model_id"] == judge1
            ):
                return row
        pytest.fail("literal ordered judge assignment was filtered")

    forward = find("same-family/model-a", "same-family/model-b")
    reverse = find("same-family/model-b", "same-family/model-a")
    assert forward["case_id"] != reverse["case_id"]
    assert forward["seats"][2]["role"] == reverse["seats"][2]["role"] == "judge:0"


def test_full_cross_one_seat_transport_and_typed_reasoning_change_ids(matrix):
    domain = _minimal_full_cross_domain(
        _read_frozen_full_cross_domain(),
        judge_count=[2],
        model_profile_per_seat=["compact", "frontier"],
        reasoning_per_seat=[
            {"kind": "string", "value": "low"},
            {"kind": "integer", "value": 2_000},
        ],
    )
    rows = list(matrix.iter_full_cross_cases(
        domain, ["model-a"], catalog_sha256="c" * 64,
        criticism_authority="defended_trial",
    ))

    def find(critic_profile, critic_reasoning):
        for row in rows:
            if row["paraphrase_count"] is not None:
                continue
            seats = row["seats"]
            critic, rest = seats[0], seats[1:]
            if (
                critic["model_profile"] == critic_profile
                and critic["reasoning"] == critic_reasoning
                and all(seat["model_profile"] == "compact" for seat in rest)
                and all(
                    seat["reasoning"] == {"kind": "string", "value": "low"}
                    for seat in rest
                )
            ):
                return row
        pytest.fail("independent critic transport assignment was filtered")

    string_low = {"kind": "string", "value": "low"}
    integer_low = {"kind": "integer", "value": 2_000}
    baseline = find("compact", string_low)
    profile_change = find("frontier", string_low)
    typed_change = find("compact", integer_low)
    assert len({baseline["case_id"], profile_change["case_id"], typed_change["case_id"]}) == 3
    assert baseline["seats"][1:] == profile_change["seats"][1:] == typed_change["seats"][1:]
    assert matrix.build_provider_body("model-a", "low")["reasoning_effort"] == "low"
    assert matrix.build_provider_body("model-a", 2_000)["reasoning_effort"] == "low"


def test_full_cross_requires_explicit_defended_authority_before_enumeration(matrix):
    domain = _minimal_full_cross_domain(
        _read_frozen_full_cross_domain(), judge_count=[2]
    )
    accepted = matrix.iter_full_cross_cases(
        domain, ["model-a"], catalog_sha256="d" * 64,
        criticism_authority="defended_trial",
    )
    assert next(accepted)["criticism_authority"] == "defended_trial"
    for authority in (None, "observe_only", "trial_required"):
        with refusal(matrix, "FULL_CROSS_REQUIRES_DEFENDED_TRIAL"):
            next(matrix.iter_full_cross_cases(
                domain, ["model-a"], catalog_sha256="d" * 64,
                criticism_authority=authority,
            ))

    tampered = json.loads(json.dumps(domain))
    tampered["request_integrity"]["criticism_authority"] = "observe_only"
    with refusal(matrix, "FULL_CROSS_REQUIRES_DEFENDED_TRIAL"):
        next(matrix.iter_full_cross_cases(
            tampered, ["model-a"], catalog_sha256="d" * 64,
            criticism_authority="defended_trial",
        ))


def test_full_cross_has_no_family_or_preflight_membership_filter(matrix):
    domain = _minimal_full_cross_domain(_read_frozen_full_cross_domain())
    safe_models = ["same-family/model-a", "same-family/model-b"]
    rows = list(matrix.iter_full_cross_cases(
        domain, [*safe_models, "KIMI K3:cloud"], catalog_sha256="e" * 64,
        criticism_authority="defended_trial",
    ))
    expected = _literal_full_cross_payloads(domain, safe_models, "e" * 64)
    assert len(rows) == len(expected) == 144
    assert {row["case_id"] for row in rows} == {
        _literal_case_id(payload) for payload in expected
    }
    assert {
        seat["model_id"] for row in rows for seat in row["seats"]
    } == set(safe_models)
    assert any(
        row["seats"][2]["model_id"] == row["seats"][3]["model_id"]
        for row in rows
    )
    assert all(
        "kimik3" not in matrix.normalize_model_id(seat["model_id"])
        for row in rows for seat in row["seats"]
    )


def test_full_cross_direct_ordinal_round_trips_each_component_boundary(
    matrix, monkeypatch
):
    domain = _minimal_full_cross_domain(
        _read_frozen_full_cross_domain(),
        split_protocol=["auto", "off"],
        model_profile_per_seat=["compact", "frontier"],
        paraphrase_count_with_variator=[-1, 2],
    )
    models, catalog_sha256 = ["model-a"], "6" * 64
    literal = _literal_full_cross_payloads(domain, models, catalog_sha256)
    case_at = matrix.full_cross_case_at
    case_ordinal = matrix.full_cross_case_ordinal
    monkeypatch.setattr(
        matrix, "iter_full_cross_cases",
        lambda *args, **kwargs: pytest.fail("direct ordinal API walked the iterator"),
    )

    # J2/no-variator [0, 32), J2/variator [32, 160),
    # J3/no-variator [160, 224), and J3/variator [224, 480).
    for ordinal in (0, 31, 32, 159, 160, 223, 224, 479):
        row = case_at(
            domain, models, ordinal,
            catalog_sha256=catalog_sha256,
            criticism_authority="defended_trial",
        )
        assert row["ordinal"] == ordinal
        assert _full_cross_identity(row) == literal[ordinal]
        assert row["case_id"] == _literal_case_id(literal[ordinal])
        assert case_ordinal(domain, models, row) == ordinal


def test_full_cross_direct_fixture_tail_does_not_enumerate_its_prefix(
    matrix, monkeypatch
):
    domain = _read_frozen_full_cross_domain()
    models = [
        entry["model_id"]
        for entry in json.loads(DOMAIN_PATH.read_text(encoding="utf-8"))[
            "fixture_catalog"
        ]
    ]
    total = domain["cardinality"]["fixture_total"]
    case_at = matrix.full_cross_case_at
    case_ordinal = matrix.full_cross_case_ordinal
    monkeypatch.setattr(
        matrix, "iter_full_cross_cases",
        lambda *args, **kwargs: pytest.fail("fixture tail walked its prior cases"),
    )
    tail = case_at(
        domain, models, total - 1,
        catalog_sha256="7" * 64,
        criticism_authority="defended_trial",
    )
    assert tail["ordinal"] == total - 1
    assert tail["judge_count"] == 3
    assert tail["split_protocol"] == "off"
    assert tail["paraphrase_count"] == 3
    assert [seat["role"] for seat in tail["seats"]] == [
        "critic", "defender", "judge:0", "judge:1", "judge:2", "variator",
    ]
    expected_model = sorted(models, key=lambda value: value.encode("utf-8"))[-1]
    assert all(seat["model_id"] == expected_model for seat in tail["seats"])
    assert all(seat["model_profile"] == "frontier" for seat in tail["seats"])
    assert all(seat["output_mode"] == "json_object" for seat in tail["seats"])
    assert all(seat["output_mechanism"] == "json_text" for seat in tail["seats"])
    assert all(
        seat["reasoning"] == {"kind": "integer", "value": 2_000}
        for seat in tail["seats"]
    )
    assert case_ordinal(domain, models, tail) == total - 1


def test_full_cross_lazy_ordinals_resume_the_same_stable_sequence(matrix):
    domain = _minimal_full_cross_domain(
        _read_frozen_full_cross_domain(),
        split_protocol=["auto", "off"],
        model_profile_per_seat=["compact", "frontier"],
        paraphrase_count_with_variator=[-1, 2],
    )
    kwargs = {
        "catalog_sha256": "f" * 64,
        "criticism_authority": "defended_trial",
    }
    generated = matrix.iter_full_cross_cases(domain, ["model-a"], **kwargs)
    assert iter(generated) is generated
    whole = list(generated)
    assert [row["ordinal"] for row in whole] == list(range(480))
    assert list(matrix.iter_full_cross_cases(
        domain, ["model-a"], start_ordinal=137, stop_ordinal=149, **kwargs,
    )) == whole[137:149]
    assert list(matrix.iter_full_cross_cases(
        domain, ["model-a"], start_ordinal=480, **kwargs,
    )) == []


def test_full_cross_resume_loader_finds_sparse_gap_without_prefix_walk(
    matrix, tmp_path, monkeypatch
):
    domain = _minimal_full_cross_domain(_read_frozen_full_cross_domain())
    models, catalog_sha256 = ["model-a"], "2" * 64
    domain_sha256 = "1" * 64
    root = tmp_path / "live-full-cross"
    attempt = matrix.prepare_attempt(
        root,
        domain_sha256=domain_sha256,
        catalog_sha256=catalog_sha256,
    )
    cases = {
        ordinal: matrix.full_cross_case_at(
            domain,
            models,
            ordinal,
            catalog_sha256=catalog_sha256,
            criticism_authority="defended_trial",
        )
        for ordinal in (0, 2)
    }
    for ordinal, case in cases.items():
        receipt = {
            "case_id": case["case_id"],
            "ordinal": ordinal,
            "status": "trial_outcome" if ordinal == 0 else "configuration_refused",
            "catalog_sha256": catalog_sha256,
            "domain_sha256": domain_sha256,
            "branch_commit": "3" * 40,
            "case_payload": case,
            "criticism_authority": "defended_trial",
            "full_dispatch_reached": ordinal == 0,
        }
        matrix._atomic_bytes(
            attempt / "results" / f"{case['case_id'].removeprefix('sha256:')}.json",
            matrix.safe_live_result_bytes(receipt),
        )
    matrix.mark_interrupted(attempt)
    terminals = matrix._load_full_cross_terminals(
        root,
        domain=domain,
        model_ids=models,
        domain_sha256=domain_sha256,
        catalog_sha256=catalog_sha256,
    )
    monkeypatch.setattr(
        matrix,
        "iter_full_cross_cases",
        lambda *args, **kwargs: pytest.fail("resume summary walked the prefix"),
    )
    summary = matrix.full_cross_resume_summary(
        domain,
        models,
        catalog_sha256=catalog_sha256,
        terminals=terminals,
    )
    expected_next = matrix.full_cross_case_at(
        domain,
        models,
        1,
        catalog_sha256=catalog_sha256,
        criticism_authority="defended_trial",
    )
    assert summary == {
        "expected": 4,
        "terminal": 2,
        "possible": 1,
        "impossible": 1,
        "provider_indeterminate": 0,
        "unexpected_error": 0,
        "interrupted": 0,
        "pending": 2,
        "next_ordinal": 1,
        "next_case_id": expected_next["case_id"],
    }


def test_full_cross_frozen_summary_is_exact_and_constant_time(matrix, monkeypatch):
    domain = _read_frozen_full_cross_domain()
    catalog = json.loads((TRANCHE / "CATALOG.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(
        matrix,
        "iter_full_cross_cases",
        lambda *args, **kwargs: pytest.fail("frozen summary walked the full cross"),
    )
    summary = matrix.full_cross_resume_summary(
        domain,
        catalog["model_ids"],
        catalog_sha256=catalog["catalog_sha256"],
        terminals={},
    )
    first = matrix.full_cross_case_at(
        domain,
        catalog["model_ids"],
        0,
        catalog_sha256=catalog["catalog_sha256"],
        criticism_authority="defended_trial",
    )
    assert summary == {
        "expected": 71_141_539_390_075_109_376,
        "terminal": 0,
        "possible": 0,
        "impossible": 0,
        "provider_indeterminate": 0,
        "unexpected_error": 0,
        "interrupted": 0,
        "pending": 71_141_539_390_075_109_376,
        "next_ordinal": 0,
        "next_case_id": first["case_id"],
    }


def test_live_authenticated_catalog_keeps_every_non_kimi_raw_id(matrix):
    response = {
        "object": "list",
        "data": [
            {"id": "not-a-chat-model", "object": "model"},
            {"id": "KIMI K3:cloud", "object": "model"},
            {"id": "minimax-m3", "object": "model"},
            {"id": "kimi-k2.7-code", "object": "model"},
            {"id": "glm-5.3", "object": "model"},
        ],
    }
    frozen = matrix.freeze_authenticated_catalog(response)
    assert frozen["model_ids"] == [
        "glm-5.3", "kimi-k2.7-code", "minimax-m3", "not-a-chat-model",
    ]
    assert frozen["excluded"] == [
        {"model_id": "KIMI K3:cloud", "code": "KIMI_K3_FORBIDDEN"}
    ]
    assert frozen["catalog_sha256"] == hashlib.sha256(
        matrix.canonical_json(frozen["model_ids"])
    ).hexdigest()
    duplicate = {"object": "list", "data": [{"id": "same"}, {"id": "same"}]}
    with refusal(matrix, "DUPLICATE_RAW_MODEL_ID"):
        matrix.freeze_authenticated_catalog(duplicate)


def test_live_endpoint_preserves_each_registered_seat_transport_field(matrix):
    environment = {"OLLAMA_API_KEY": "in-memory-test-credential"}
    cases = (
        ("glm-5.3", "frontier", "json_object", "native_json_schema",
         {"kind": "string", "value": "none"}, "none"),
        ("minimax-m3", "compact", "text", "grammar",
         {"kind": "integer", "value": 2_000}, "low"),
        ("kimi-k2.7-code", "standard", "json_object", "json_text",
         {"kind": "string", "value": "medium"}, "medium"),
    )
    for model, profile, mode, mechanism, reasoning, wire_reasoning in cases:
        binding = matrix.build_live_endpoint(
            _live_seat(
                model_id=model, model_profile=profile, output_mode=mode,
                output_mechanism=mechanism, reasoning=reasoning,
            ),
            criticism_authority="defended_trial", environ=environment,
        )
        assert binding.role == "judge:0"
        assert binding.model_profile == profile
        endpoint = binding.endpoint
        assert endpoint.name == "https://ollama.com/v1"
        assert endpoint.model == model
        assert endpoint.provider == "ollama"
        assert endpoint.reasoning == reasoning["value"]
        assert endpoint.json_mode is (mode == "json_object")
        assert endpoint.output_mechanism == mechanism
        assert endpoint.api_key == environment["OLLAMA_API_KEY"]
        body = endpoint.build_body(
            "Return the probe object.", response_schema={"type": "object"},
            output_mechanism=endpoint.output_mechanism,
        )
        assert body["model"] == model
        assert body["reasoning_effort"] == wire_reasoning
        if mechanism == "native_json_schema":
            assert body["response_format"]["type"] == "json_schema"
        elif mechanism == "grammar":
            assert "grammar" in body
        else:
            assert "grammar" not in body and "response_format" not in body


def test_live_endpoint_integrity_rejects_observation_and_unsafe_reasoning(matrix):
    environment = {"OLLAMA_API_KEY": "in-memory-test-credential"}
    for authority in (None, "observe_only", "trial_required"):
        with refusal(matrix, "LIVE_REQUIRES_DEFENDED_TRIAL"):
            matrix.build_live_endpoint(
                _live_seat(), criticism_authority=authority, environ=environment,
            )
    for reasoning in (
        {"kind": "string", "value": "high"},
        {"kind": "string", "value": "xhigh"},
        {"kind": "string", "value": "max"},
        {"kind": "integer", "value": 2_001},
    ):
        with refusal(matrix, "FORBIDDEN_REASONING_EFFORT"):
            matrix.build_live_endpoint(
                _live_seat(reasoning=reasoning),
                criticism_authority="defended_trial",
                environ=environment,
            )


def test_live_glm_none_probe_records_populated_trace_without_reinterpreting_it(matrix):
    trace = "provider returned this trace even though none was requested"
    receipt = matrix.reasoning_probe_receipt(
        model_id="glm-5.3",
        requested_reasoning="none",
        message={"content": '{"ok":true}', "reasoning_content": trace},
    )
    assert receipt["status"] == "probe_usable"
    assert receipt["requested_reasoning"] == "none"
    assert receipt["message_keys"] == ["content", "reasoning_content"]
    assert receipt["parser_outcome"] == receipt["schema_outcome"] == "valid"
    assert receipt["trace_fields"]["reasoning_content"] == {
        "present": True,
        "byte_count": len(trace.encode("utf-8")),
        "sha256": hashlib.sha256(trace.encode("utf-8")).hexdigest(),
    }
    assert trace not in json.dumps(receipt)
    assert "disabled" not in json.dumps(receipt).casefold()


def test_live_global_endpoint_gate_never_exceeds_three_calls(matrix):
    lock, release = threading.Lock(), threading.Event()
    state = {"active": 0, "peak": 0}

    class BlockingEndpoint:
        def complete(self, _prompt):
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

    endpoints = [matrix.BoundedLiveEndpoint(BlockingEndpoint()) for _ in range(9)]
    with ThreadPoolExecutor(max_workers=9) as pool:
        results = list(pool.map(lambda endpoint: endpoint.complete("probe"), endpoints))
    assert results == ["ok"] * 9
    assert state == {"active": 0, "peak": 3}


def test_live_baseline_case_drives_critic_defender_and_both_judges(
    matrix, monkeypatch, tmp_path
):
    from deepreason.llm.endpoints import MockEndpoint
    from deepreason.run_manifest import infer_model_family

    responses = {
        "critic": '{"attack":true,"case":"boundary condition is omitted"}',
        "defender": '{"answer":"the boundary condition is enforced"}',
        "judge:0": '{"verdict":"fail","decisive_point":"boundary condition"}',
        "judge:1": '{"verdict":"fail","decisive_point":"boundary condition"}',
    }

    def fake_live_endpoint(seat, *, criticism_authority, environ):
        assert criticism_authority == "defended_trial"
        assert environ == {"OLLAMA_API_KEY": "test-only-secret"}
        endpoint = MockEndpoint(
            [responses[seat["role"]]] * (3 if seat["role"] == "critic" else 1),
            name="https://ollama.com/v1",
            model=seat["model_id"],
            max_tokens=8_192,
        )
        endpoint.provider = "ollama"
        endpoint.family = infer_model_family(seat["model_id"], "ollama")
        endpoint.model_revision = None
        endpoint.reasoning = seat["reasoning"]["value"]
        endpoint.json_mode = seat["output_mode"] == "json_object"
        endpoint.output_mechanism = seat["output_mechanism"]
        endpoint.request_logprobs = False
        endpoint.temperature = None
        endpoint.context_window_tokens = 131_072
        endpoint.timeout_s = 300
        return matrix.LiveEndpointBinding(
            role=seat["role"],
            model_profile=seat["model_profile"],
            endpoint=matrix.BoundedLiveEndpoint(endpoint),
        )

    monkeypatch.setattr(matrix, "build_live_endpoint", fake_live_endpoint)
    frozen = matrix.freeze_catalog(["baseline-model"])
    row = next(matrix.iter_seat_cases(
        frozen["model_ids"], catalog_sha256=frozen["catalog_sha256"]
    ))
    result = matrix.run_live_seat_case(
        row,
        tmp_path / "live-case",
        secret="test-only-secret",
        domain_sha256="1" * 64,
        branch_commit="2" * 40,
    )
    assert result["status"] == "trial_outcome"
    assert result["dispatch_extent"][0] == "critic"
    assert result["dispatch_extent"][-3:] == ["defender", "judge:0", "judge:1"]
    assert result["critic_compatibility"]["status"] == "mechanically_compatible", result["critic_compatibility"]["first_boundary"]["message"]
    assert result["fixed_case_court_reachability"]["status"] == "trial_outcome"
    assert result["full_dispatch_reached"] is True
    assert b"test-only-secret" not in matrix.safe_live_result_bytes(
        result, secret="test-only-secret"
    )


def test_live_result_classification_preserves_the_first_typed_boundary(matrix):
    extent = ["critic", "defender"]
    typed = matrix.MatrixRefusal("V6_ROUTE_REFUSED", "verbatim refusal")
    typed.pointer = "/roles/judge/0"
    refused = matrix.classify_live_result(
        error=typed, stage="judge:0", dispatch_extent=extent,
        provider_dependent=False,
    )
    assert refused == {
        "status": "configuration_refused",
        "dispatch_extent": extent,
        "first_boundary": {
            "stage": "judge:0",
            "exception_type": "MatrixRefusal",
            "code": "V6_ROUTE_REFUSED",
            "pointer": "/roles/judge/0",
            "message": "V6_ROUTE_REFUSED: verbatim refusal",
        },
    }
    provider = matrix.classify_live_result(
        error=TimeoutError("provider timed out"), stage="judge:0",
        dispatch_extent=extent, provider_dependent=True,
    )
    assert provider["status"] == "provider_indeterminate"
    assert provider["first_boundary"]["message"] == "provider timed out"
    outcome = matrix.classify_live_result(
        outcome_code="ensemble-split", stage="trial", dispatch_extent=extent,
    )
    assert outcome == {
        "status": "trial_outcome", "outcome_code": "ensemble-split",
        "dispatch_extent": extent, "first_boundary": None,
    }


def test_live_persistence_allowlist_cannot_store_auth_or_raw_trace(matrix):
    secret = "credential-sentinel-never-write"
    trace = "raw hidden trace must not be persisted"
    result = {
        "case_id": "sha256:" + "1" * 64,
        "ordinal": 17,
        "status": "provider_indeterminate",
        "catalog_sha256": "2" * 64,
        "domain_sha256": "3" * 64,
        "branch_commit": "4" * 40,
        "dispatch_extent": ["critic", "defender"],
        "response_metadata": {
            "message_keys": ["content", "reasoning_content"],
            "trace_fields": {
                "reasoning_content": {
                    "present": True, "byte_count": len(trace.encode()),
                    "sha256": hashlib.sha256(trace.encode()).hexdigest(),
                },
            },
            "raw_reasoning_trace": trace,
        },
        "headers": {"Authorization": f"Bearer {secret}"},
        "api_key": secret,
        "raw_request_body": {"authorization": secret},
    }
    encoded = matrix.safe_live_result_bytes(result, secret=secret)
    persisted = json.loads(encoded)
    assert persisted["case_id"] == result["case_id"]
    assert persisted["ordinal"] == 17
    assert persisted["dispatch_extent"] == ["critic", "defender"]
    assert persisted["response_metadata"]["trace_fields"] == (
        result["response_metadata"]["trace_fields"]
    )
    assert secret.encode() not in encoded
    assert hashlib.sha256(secret.encode()).hexdigest().encode() not in encoded
    assert trace.encode() not in encoded
    assert b"Authorization" not in encoded and b"api_key" not in encoded
    withheld = json.loads(matrix.safe_live_result_bytes({
        **result,
        "first_boundary": {"message": secret, "code": "PROVIDER_ERROR"},
    }, secret=secret))
    assert withheld["code"] == "SECRET_BEARING_DIAGNOSTIC_WITHHELD"


def test_live_case_receipt_binds_full_cross_identity_without_raw_request(matrix):
    domain = _minimal_full_cross_domain(_read_frozen_full_cross_domain())
    row = matrix.full_cross_case_at(
        domain, ["model-a"], 0, catalog_sha256="8" * 64,
        criticism_authority="defended_trial",
    )
    request_body = {
        "model": "model-a", "messages": [{"role": "user", "content": "probe"}],
        "reasoning_effort": "low",
    }
    receipt = matrix.build_live_case_receipt(
        row, domain_sha256="9" * 64, branch_commit="a" * 40,
        request_body=request_body,
    )
    assert receipt["case_id"] == row["case_id"]
    assert receipt["ordinal"] == 0
    assert receipt["case_payload"] == _full_cross_identity(row)
    assert receipt["catalog_sha256"] == "8" * 64
    assert receipt["domain_sha256"] == "9" * 64
    assert receipt["branch_commit"] == "a" * 40
    assert receipt["request_body_sha256"] == hashlib.sha256(
        matrix.canonical_json(request_body)
    ).hexdigest()
    assert "request_body" not in receipt
    assert receipt["criticism_authority"] == "defended_trial"


def test_live_full_cross_resume_validates_receipts_and_returns_first_gap(matrix):
    domain = _minimal_full_cross_domain(_read_frozen_full_cross_domain())
    kwargs = {
        "catalog_sha256": "b" * 64,
        "criticism_authority": "defended_trial",
    }
    rows = list(matrix.iter_full_cross_cases(domain, ["model-a"], **kwargs))
    terminals = [
        {"ordinal": row["ordinal"], "case_id": row["case_id"]}
        for row in rows[:2]
    ]
    resumed = matrix.next_pending_full_cross_case(
        domain, ["model-a"], terminal_receipts=terminals,
        start_ordinal=0, **kwargs,
    )
    assert resumed == rows[2]
    corrupted = [*terminals, {"ordinal": 2, "case_id": rows[3]["case_id"]}]
    with refusal(matrix, "FULL_CROSS_RECEIPT_ID_MISMATCH"):
        matrix.next_pending_full_cross_case(
            domain, ["model-a"], terminal_receipts=corrupted,
            start_ordinal=0, **kwargs,
        )
