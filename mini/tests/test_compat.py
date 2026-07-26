"""W7: MiniReason consumes one shared compatibility kernel."""

import json

import pytest

from deepreason.llm.firewall import RouteFirewallError
from deepreason.run_manifest import (
    UnsupportedRunManifestVersionError,
    load_run_manifest,
)
from minireason.call import HttpEndpoint, MockEndpoint, TokenMeter, call
from minireason.compat import DEFAULT_MODEL_PROFILE, ENGINE_PROFILE, initialize
from minireason.log import BlobStore
from minireason.loop import ConjOut, run


def _skeleton(index: int) -> str:
    return json.dumps(
        {
            "claim": f"claim {index}",
            "mechanism": f"mechanism {index}",
            "forbidden": [
                {"case": "valid JSON required", "eval": "program:json-wf"}
            ],
        }
    )


def _candidates(count: int) -> str:
    return json.dumps(
        {
            "candidates": [
                {"content": _skeleton(index), "typicality": 0.5}
                for index in range(count)
            ]
        }
    )


def test_mini_defaults_are_explicit_and_manifested(tmp_path):
    endpoint = MockEndpoint([_candidates(5)], name="mock://mini", model="gemma-mini")
    root = tmp_path / "run"
    summary = run(
        [("pi-1", "why?")],
        endpoint,
        budget=100_000,
        root=root,
        max_cycles=1,
    )

    manifest = load_run_manifest(root / "run-manifest.json")
    assert summary["engine_profile"] == manifest.engine_profile == ENGINE_PROFILE
    assert summary["model_profile"] == manifest.model_profile == DEFAULT_MODEL_PROFILE.value
    assert manifest.rubric_policy == "forbid"
    assert manifest.concurrency == 1
    assert manifest.roles["conjecturer"][0].model_id == "gemma-mini"
    # New mini roots are V6-native: the mandatory control plane is present in
    # its minimal/disabled form and every transactional-only authority the
    # reduced loop cannot honor is explicitly absent, not declared-and-ignored.
    assert manifest.schema_version == 6
    assert manifest.control_plane_policy is not None
    assert manifest.control_plane_policy.mode == "active_inquiry"
    assert manifest.control_plane_policy.school_execution.mode == "conditioning_only"
    assert manifest.control_plane_policy.conjecture_context.mode == "disabled"
    assert manifest.control_plane_policy.scratch_authoring.enabled is False
    assert manifest.run_input_digest is not None
    assert manifest.route_seat_presentation_plan is not None
    assert manifest.production_qualification_policy is None
    assert manifest.terminal_commitment_policy is None
    assert manifest.compact_recovery_policy is None
    assert manifest.contract_schema_repair_policy is None
    assert manifest.route_seat_behavioral_capability_plan is None
    assert manifest.route_seat_contract_decomposition_plan is None
    from deepreason.evidence import verify_run_input

    assert verify_run_input(root)["run_input_digest"] == manifest.run_input_digest
    # Compact VS_K=4 is a presentation/process default; the fifth valid
    # response never enters MiniReason's unchanged admission loop.
    assert summary["problems"] == {"pi-1": 4}


def test_kernel_objects_come_from_parent_shared_modules(tmp_path):
    endpoint = MockEndpoint([], name="mock://mini", model="m")
    kernel = initialize(tmp_path / "run", endpoint)

    assert type(kernel.profile).__module__ == "deepreason.llm.profiles"
    assert type(kernel.lease).__module__ == "deepreason.llm.firewall"
    assert type(kernel.wire_contract).__module__ == "deepreason.llm.wire"
    assert (
        kernel.wire_contract.contract_id
        == "conjecturer.compact.reference_free.v1"
    )
    assert "neighbours" not in json.dumps(kernel.wire_contract.model_json_schema())


def test_http_endpoint_manifest_records_inferred_provider_identity(tmp_path):
    endpoint = HttpEndpoint(
        "https://api.deepseek.com/v1", "deepseek-v4-flash", api_key="unused"
    )
    kernel = initialize(tmp_path / "provider-root", endpoint)

    route = kernel.manifest.roles["conjecturer"][0]
    assert route.provider == "deepseek"
    assert route.family == "deepseek"
    assert route.output_mechanism == "json_text"


def test_control_fields_are_local_repair_failures_not_commands(tmp_path):
    responses = iter(
        [
            json.dumps(
                {
                    "candidates": [
                        {"content": _skeleton(1), "typicality": 0.5}
                    ],
                    "delegate": True,
                }
            ),
            _candidates(1),
        ]
    )
    endpoint = MockEndpoint(lambda _prompt: next(responses), name="mock://mini", model="m")
    kernel = initialize(tmp_path / "run", endpoint)

    output, spend = call(
        endpoint,
        "make one conjecture",
        ConjOut,
        TokenMeter(),
        BlobStore(tmp_path / "blobs"),
        role="conjecturer",
        wire_contract=kernel.wire_contract,
        endpoint_lease=kernel.lease,
    )

    assert output.candidates[0].content == _skeleton(0)
    assert spend.attempts == 2
    assert kernel.lease.route.model_id == "m"


def test_route_mutation_between_repairs_fails_closed(tmp_path):
    endpoint = MockEndpoint(["not json", _candidates(1)], name="mock://mini", model="m")
    complete = endpoint.complete

    def mutating_complete(prompt):
        raw = complete(prompt)
        endpoint.model = "unauthorized-model"
        return raw

    endpoint.complete = mutating_complete
    kernel = initialize(tmp_path / "run", endpoint)
    meter = TokenMeter()
    blobs = BlobStore(tmp_path / "blobs")
    with pytest.raises(RouteFirewallError, match="ROUTE_LEASE_MISMATCH") as error:
        call(
            endpoint,
            "make one conjecture",
            ConjOut,
            meter,
            blobs,
            role="conjecturer",
            wire_contract=kernel.wire_contract,
            endpoint_lease=kernel.lease,
        )

    spend = error.value.spend
    assert spend is not None
    assert spend.tokens == meter.total > 0
    assert spend.attempts == len(spend.attempt_trace) == 1
    assert not spend.attempt_trace[0].valid
    assert spend.attempt_trace[0].raw_ref
    assert blobs.get(spend.prompt_ref) == blobs.get(spend.attempt_trace[0].prompt_ref)


def test_compact_survivor_context_exposes_content_without_reference_ids(tmp_path):
    prompts: list[str] = []
    responses = iter([_candidates(1), _candidates(1)])

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        return next(responses)

    root = tmp_path / "reference-free"
    run(
        [("pi-1", "why?")],
        MockEndpoint(complete, name="mock://mini", model="m"),
        budget=100_000,
        root=root,
        vs_k=1,
        max_cycles=2,
    )

    from minireason.loop import Session

    survivor = Session(root).survivors("pi-1")[0]
    assert len(prompts) == 2
    assert _skeleton(0) in prompts[1]
    assert survivor not in prompts[1]
    assert survivor[:12] not in prompts[1]
    assert "neighbours" not in prompts[1]


def test_legacy_v1_root_fails_closed_but_replays_read_only(tmp_path):
    """Legacy mini roots stay v1 on disk and are never migrated or mutated.

    Reopening one through the parent loader is the intended fail-closed
    refusal; the log itself remains readable through the manifest-free
    read-only replay path.
    """
    from deepreason.canonical import canonical_json, sha256_hex
    from deepreason.llm.firewall import route_from_endpoint
    from deepreason.run_manifest import RunManifest
    from minireason.log import replay
    from minireason.loop import Session

    root = tmp_path / "legacy-mini"
    session = Session(root)  # pre-manifest root: plain canonical log
    session.spawn_problem("pi-legacy", "a retired mini investigation")
    session.measure(["ok"])
    digest_before = session.state.digest()

    endpoint = MockEndpoint([], name="mock://legacy-mini", model="legacy-mini")
    legacy = RunManifest(
        schema_version=1,
        engine_profile=ENGINE_PROFILE,
        model_profile=DEFAULT_MODEL_PROFILE.value,
        roles={"conjecturer": (route_from_endpoint(endpoint),)},
        rubric_policy="forbid",
        concurrency=1,
        pack_profile=DEFAULT_MODEL_PROFILE.value,
        output_profile=DEFAULT_MODEL_PROFILE.value,
        source_config_hash=sha256_hex(canonical_json({"legacy": True})),
        compiled_at="2026-01-01T00:00:00Z",
        engine_config_json="{}",
    )
    (root / "run-manifest.json").write_bytes(legacy.canonical_bytes())
    (root / "run-manifest.sha256").write_text(legacy.sha256 + "\n")
    tracked = {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }

    with pytest.raises(UnsupportedRunManifestVersionError):
        initialize(root, endpoint)
    with pytest.raises(UnsupportedRunManifestVersionError):
        run([("pi-x", "d")], endpoint, budget=1_000, root=root, max_cycles=1)

    state = replay(root)
    assert set(state.problems) == {"pi-legacy"}
    assert state.digest() == digest_before
    assert {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    } == tracked


def test_existing_full_root_cannot_be_silently_downgraded(tmp_path):
    endpoint = MockEndpoint([], name="mock://mini", model="m")
    kernel = initialize(tmp_path / "run", endpoint)
    payload = kernel.manifest.model_copy(update={"engine_profile": "full"})
    (tmp_path / "run" / "run-manifest.json").write_bytes(payload.canonical_bytes())
    (tmp_path / "run" / "run-manifest.sha256").write_text(payload.sha256 + "\n")

    with pytest.raises(RouteFirewallError, match="ENGINE_MISMATCH"):
        initialize(tmp_path / "run", endpoint)
