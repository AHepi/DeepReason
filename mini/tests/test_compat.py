"""W7: MiniReason consumes one shared compatibility kernel."""

import json

import pytest

from deepreason.llm.firewall import RouteFirewallError
from deepreason.run_manifest import load_run_manifest
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


def test_existing_full_root_cannot_be_silently_downgraded(tmp_path):
    endpoint = MockEndpoint([], name="mock://mini", model="m")
    kernel = initialize(tmp_path / "run", endpoint)
    payload = kernel.manifest.model_copy(update={"engine_profile": "full"})
    (tmp_path / "run" / "run-manifest.json").write_bytes(payload.canonical_bytes())
    (tmp_path / "run" / "run-manifest.sha256").write_text(payload.sha256 + "\n")

    with pytest.raises(RouteFirewallError, match="ENGINE_MISMATCH"):
        initialize(tmp_path / "run", endpoint)
