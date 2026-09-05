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


# ------------------------------- the STANDARD frozen input (S1, R12)


def _frozen_root(tmp_path, *, criteria=()):
    """Write the record `deepreason input freeze` writes, by the same call."""
    from deepreason.evidence import (
        AttachedSourceProvenanceV1,
        EvidenceDossierV1,
        RunInputManifestV2,
        RunInputProblemV2,
        bind_run_input,
    )

    root = tmp_path / "frozen"
    dossier = EvidenceDossierV1.create(
        problem_ref="pi-standard",
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="operator workload",
            acquisition_method="deepreason input freeze",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id="pi-standard",
            description="why does the sky look blue?",
            criteria=criteria,
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    return run_input, dossier


def test_a_supplied_frozen_input_is_bound_instead_of_the_process_root(tmp_path):
    """Implements R12: "It's starting input should be standard."

    The standard input is the RunInputManifestV2 the full harness takes. When
    one is supplied, mini binds THAT to its root -- the manifest's
    run_input_digest is the frozen record's, not the constant process root's.
    """
    from minireason.call import MockEndpoint
    from minireason.compat import (
        MINI_RUN_INPUT_PROBLEM_ID,
        bind_mini_root,
        mini_run_input,
    )
    from deepreason.evidence import load_run_input

    run_input, dossier = _frozen_root(tmp_path)
    constant, _ = mini_run_input()
    assert run_input.run_input_digest != constant.run_input_digest

    root = tmp_path / "run"
    endpoint = MockEndpoint(lambda prompt: "{}")
    manifest = bind_mini_root(root, endpoint, run_input=run_input, dossier=dossier)

    assert manifest.run_input_digest == run_input.run_input_digest
    bound = load_run_input(root)
    assert bound.problem.id == "pi-standard" != MINI_RUN_INPUT_PROBLEM_ID
    assert bound.problem.description == "why does the sky look blue?"


def test_no_supplied_input_still_binds_the_constant_process_root(tmp_path):
    """The bare form is unchanged: mini's constant process root, byte for byte."""
    from minireason.call import MockEndpoint
    from minireason.compat import bind_mini_root, mini_run_input

    constant, _ = mini_run_input()
    manifest = bind_mini_root(tmp_path / "run", MockEndpoint(lambda p: "{}"))
    assert manifest.run_input_digest == constant.run_input_digest


def test_reopening_a_root_against_a_different_frozen_input_is_refused(tmp_path):
    """A root's identity includes what it was asked.

    A manifest that says one thing while the run answered another is a
    reader's trap; the refusal is typed so it can be acted on.
    """
    import pytest

    from deepreason.llm.firewall import RouteFirewallError
    from minireason.call import MockEndpoint
    from minireason.compat import bind_mini_root

    run_input, dossier = _frozen_root(tmp_path)
    other, other_dossier = _frozen_root(tmp_path / "second")
    root = tmp_path / "run"
    endpoint = MockEndpoint(lambda prompt: "{}")
    bind_mini_root(root, endpoint, run_input=run_input, dossier=dossier)

    # Same root, a DIFFERENT frozen input: refused, named.
    from deepreason.evidence import RunInputManifestV2, RunInputProblemV2

    different = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id="pi-standard",
            description="a different question entirely",
            criteria=(),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    with pytest.raises(RouteFirewallError) as caught:
        bind_mini_root(root, endpoint, run_input=different, dossier=dossier)
    assert "MINI_ROOT_RUN_INPUT_MISMATCH" in str(caught.value)

    # Rebinding the SAME one is not a refusal: it is the recovery path.
    bind_mini_root(root, endpoint, run_input=run_input, dossier=dossier)


def test_a_run_input_without_its_dossier_is_refused(tmp_path):
    import pytest

    from deepreason.llm.firewall import RouteFirewallError
    from minireason.call import MockEndpoint
    from minireason.compat import bind_mini_root

    run_input, _ = _frozen_root(tmp_path)
    with pytest.raises(RouteFirewallError) as caught:
        bind_mini_root(tmp_path / "run", MockEndpoint(lambda p: "{}"),
                       run_input=run_input)
    assert "MINI_RUN_INPUT_INCOMPLETE" in str(caught.value)
