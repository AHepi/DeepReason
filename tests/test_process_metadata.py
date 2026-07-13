"""Compatibility profile/repair/route data stays process-only and replayable."""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter, SchemaRepairError
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import EndpointError, MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.wire import AliasTable
from deepreason.ontology import Problem, ProblemProvenance, Rule
from deepreason.ontology.event import LLMAttempt, LLMCall
from deepreason.report import eval_report
from deepreason.rules.conj import conj
from deepreason.run_manifest import Route, RunManifest, persist_run_manifest


def _manifest(endpoint, *, engine_profile="full", model_profile="compact"):
    route = Route(
        endpoint_id="mock-seat",
        base_url=endpoint.name,
        model_id=endpoint.model,
        provider="mock",
        family="mock-family",
        # Authorize the mock's completion cap so attempt-limit invariants
        # see a route-sanctioned max_tokens on every trace.
        max_tokens=endpoint.max_tokens,
    )
    return RunManifest(
        engine_profile=engine_profile,
        model_profile=model_profile,
        roles={"conjecturer": (route,)},
        rubric_policy="forbid",
        concurrency=1,
        pack_profile=model_profile,
        output_profile=model_profile,
        source_config_hash="0" * 64,
        compiled_at="2026-07-11T00:00:00Z",
        engine_config_json="{}",
    )


def _profiled_run(root):
    invalid = '{"candidates":[{"content":"keep","typicality":2}]}'
    valid = json.dumps(
        {"candidates": [{"content": "keep", "typicality": 0.5}]}
    )
    endpoint = MockEndpoint([invalid, valid], name="mock://profiled", model="model-1")
    manifest = _manifest(endpoint)
    persist_run_manifest(manifest, root)
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="pi-1",
            description="a problem",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=2,
        model_profile="compact",
        leases=leases_from_manifest(manifest),
    )
    conj(harness, "pi-1", adapter, Config(VS_K=1, NEAR_DUP_EPS=None))
    return harness, manifest


def test_report_groups_repair_metrics_by_frozen_model_profile(tmp_path):
    root = tmp_path / "run"
    harness, manifest = _profiled_run(root)

    first = eval_report(harness, Config())["process"]
    second = eval_report(Harness(root), Config())["process"]
    assert first == second
    assert first["engine_profile"] == "full"
    assert first["model_profile"] == "compact"
    assert first["manifest_sha256"] == manifest.sha256
    assert first["profile_totals"] == {
        "compact": {
            "calls": 1,
            "attempts": 2,
            "repair_attempts": 1,
            "repaired_calls": 1,
            "truncated_calls": 0,
            "tokens": first["profile_totals"]["compact"]["tokens"],
            "attempt_distribution": {"2": 1},
            "traced_calls": 1,
            "trace_coverage": 1.0,
            "first_pass_valid": 0,
            "first_pass_valid_rate": 0.0,
            "eventual_valid": 1,
            "eventual_valid_rate": 1.0,
            "schema_exhausted": 0,
            "transport_dropped": 0,
            "usage_unknown_attempts": 0,
            "provider_transport_attempts": 2,
        }
    }
    assert first["profile_totals"]["compact"]["tokens"] > 0
    assert first["frozen_routes"][0]["model_id"] == "model-1"

    # Compatibility data is absent from the canonical ontology record.
    artifact = next(iter(harness.state.artifacts.values()))
    ontology = artifact.model_dump(mode="json")
    assert not ({"engine_profile", "model_profile", "repair_attempts"} & ontology.keys())


def test_invariants_verify_manifest_routes_blobs_and_profile_totals(tmp_path):
    root = tmp_path / "run"
    _profiled_run(root)
    result = verify_root(root)

    assert result["violations"] == []
    process = result["stats"]["process"]
    assert process["manifest_present"]
    assert process["engine_profile"] == "full"
    assert process["model_profile"] == "compact"
    assert process["profile_totals"]["compact"]["calls"] == 1
    assert process["profile_totals"]["compact"]["repair_attempts"] == 1


def test_invariants_reject_unlogged_effective_transport_limit(tmp_path):
    root = tmp_path / "run"
    endpoint = MockEndpoint([], name="mock://frozen", model="model-1")
    manifest = _manifest(endpoint)
    persist_run_manifest(manifest, root)
    route = manifest.roles["conjecturer"][0]
    harness = Harness(root)
    prompt_ref = harness.blobs.put(b"prompt")
    raw_ref = harness.blobs.put(b"{}")
    harness.record_measure(
        inputs=["process-test"],
        llm=LLMCall(
            role="conjecturer",
            model=route.model_id,
            endpoint=route.base_url,
            prompt_ref=prompt_ref,
            raw_ref=raw_ref,
            attempt_trace=[LLMAttempt(
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                contract_id="conjecturer.direct.v1",
                endpoint_id=route.endpoint_id,
                route_sha256=route_fingerprint(route),
                model_profile=manifest.model_profile,
                transport_profile=manifest.model_profile,
                max_tokens=9999,
                timeout_s=route.timeout_s,
                valid=True,
                output_mechanism=route.output_mechanism,
            )],
        ),
    )

    checks = {item["check"] for item in verify_root(root)["violations"]}
    assert "attempt-limits" in checks


def test_invariants_reject_a_call_outside_the_frozen_route(tmp_path):
    root = tmp_path / "run"
    endpoint = MockEndpoint([], name="mock://frozen", model="model-1")
    persist_run_manifest(_manifest(endpoint), root)
    harness = Harness(root)
    prompt_ref = harness.blobs.put(b"prompt")
    raw_ref = harness.blobs.put(b"{}")
    harness._commit(
        Rule.MEASURE,
        inputs=["process-test"],
        outputs=[],
        llm=LLMCall(
            role="conjecturer",
            model="model-2",
            endpoint="mock://substituted",
            prompt_ref=prompt_ref,
            raw_ref=raw_ref,
        ),
    )

    checks = {item["check"] for item in verify_root(root)["violations"]}
    assert "frozen-route" in checks


def test_invariants_reject_unbounded_or_untraceable_repair_metadata(tmp_path):
    root = tmp_path / "run"
    endpoint = MockEndpoint([], name="mock://frozen", model="model-1")
    persist_run_manifest(_manifest(endpoint), root)
    harness = Harness(root)
    harness._commit(
        Rule.MEASURE,
        inputs=["process-test"],
        outputs=[],
        llm=LLMCall(
            role="conjecturer",
            model="model-1",
            endpoint="mock://frozen",
            prompt_ref=harness.blobs.put(b"no repair diagnostic"),
            raw_ref=harness.blobs.put(b"{}"),
            attempts=4,
        ),
    )

    checks = {item["check"] for item in verify_root(root)["violations"]}
    assert "repair-metadata" in checks


def test_invariants_detect_manifest_hash_corruption(tmp_path):
    root = tmp_path / "run"
    endpoint = MockEndpoint([], name="mock://frozen", model="model-1")
    persist_run_manifest(_manifest(endpoint), root)
    (root / "run-manifest.sha256").write_text("f" * 64 + "\n")

    checks = {item["check"] for item in verify_root(root)["violations"]}
    assert "run-manifest" in checks


def test_reports_distinguish_schema_exhaustion_from_transport_drop(tmp_path):
    root = tmp_path / "run"
    route_endpoint = MockEndpoint(
        [], name="mock://profiled", model="model-1"
    )
    manifest = _manifest(route_endpoint)
    persist_run_manifest(manifest, root)
    harness = Harness(root)

    schema_endpoint = MockEndpoint(
        ["bad", "bad", "bad"], name="mock://profiled", model="model-1"
    )
    schema_adapter = LLMAdapter(
        {"conjecturer": schema_endpoint},
        harness.blobs,
        model_profile="compact",
        leases=leases_from_manifest(manifest),
    )
    with pytest.raises(SchemaRepairError) as schema_error:
        schema_adapter.call(
            "conjecturer", "PACK", ConjecturerOutput, aliases=AliasTable()
        )
    harness.record_llm_calls(
        [schema_error.value.spend], "dropped-call", "schema-exhausted"
    )

    def timeout(_prompt):
        raise EndpointError("bounded timeout")

    transport_endpoint = MockEndpoint(
        timeout, name="mock://profiled", model="model-1"
    )
    transport_adapter = LLMAdapter(
        {"conjecturer": transport_endpoint},
        harness.blobs,
        model_profile="compact",
        leases=leases_from_manifest(manifest),
    )
    with pytest.raises(EndpointError) as transport_error:
        transport_adapter.call(
            "conjecturer", "PACK", ConjecturerOutput, aliases=AliasTable()
        )
    harness.record_llm_calls(
        [transport_error.value.spend], "dropped-call", "transport"
    )

    report = eval_report(harness, Config())
    row = report["llm"]["conjecturer"]
    assert row["traced_calls"] == 2
    assert row["first_pass_valid"] == row["eventual_valid"] == 0
    assert row["schema_exhausted"] == 1
    assert row["transport_dropped"] == 1
    process = report["process"]["profile_totals"]["compact"]
    assert process["schema_exhausted"] == 1
    assert process["transport_dropped"] == 1
    assert process["usage_unknown_attempts"] == 1
    assert verify_root(root)["violations"] == []
