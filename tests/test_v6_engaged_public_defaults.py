"""The engaged public preset: scratch, criticism, bridge, and simulation run.

The pinned seams:

1. The compiled public manifest (`build_preparation_manifest`) enables the
   advisory scratchpad, carries a complete foreign-school criticism policy
   binding every seeded public school to the single provider seat, compiles
   the review-free grounded two-stage bridge with both frozen bridge roles
   seated on the single provider endpoint, and enables declarative-numeric
   local simulation on one frozen interpreter-derived toolchain.
2. Behavior-level, with mock endpoints: a public-preset v6 run dispatches at
   least one school-routed criticism work order and records durable coverage.
3. Behavior-level: the public preset's scratch-authoring authority admits a
   bounded advisory proposal without touching formal state.
4. Behavior-level, with mock endpoints: a public-preset run root accepts MCP
   ``start_bridge`` and reaches the completed bridge terminal.
5. Behavior-level, with mock endpoints: a public-preset run stages one
   simulation proposal, executes it locally, and consumes its result in one
   fresh follow-up conjecture turn.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from deepreason import mcp_scratch_bridge as mcp
from deepreason.bridge.events import BridgeAction
from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.simulation import SimulationCapabilityController
from deepreason.config import Config
from deepreason.evidence import bind_run_input
from deepreason.harness import Harness
from deepreason.llm import adapter as adapter_module
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Provenance, Status
from deepreason import preparation as preparation_module
from deepreason.preparation import _records_for_question, build_preparation_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.rules.conj import conj
from deepreason.run_manifest import RunManifestError, bind_run_manifest, compile_run_manifest
from deepreason.scheduler.scheduler import Scheduler
from deepreason.scratch.authoring import ScratchAuthoringService
from deepreason.scratch.proposals import (
    ScratchBlockDraftBodyV1,
    ScratchNewBlockDraftV1,
    ScratchProposalLinkV1,
    ScratchProposalV1,
)
from deepreason.scratch.service import ScratchService
from deepreason.v6_policy import (
    POLICY_PRESET_ID,
    engaged_bridge_source,
    engaged_control_plane_policy_v3,
    engaged_criticism_policy,
    engaged_inquiry_capability_policy,
    engaged_simulation_toolchain,
    engaged_simulation_policy,
)
from tests.test_cli_production_doctor_v6 import _admitted_case
from deepreason.cli.doctor import run_production_contract_doctor


STAMP = "2026-07-25T00:00:00Z"


def _profile(**updates) -> ProviderProfileV1:
    values = dict(
        provider="openai",
        endpoint="https://api.example.test/v1",
        model_id="model-engaged-v6",
        model_revision="revision-1",
        family="family-engaged-v6",
        context_window_tokens=131_072,
        maximum_completion_tokens=4_096,
        credential_env="DEEPREASON_ENGAGED_TEST_KEY",
    )
    values.update(updates)
    return ProviderProfileV1.create(**values)


def test_public_manifest_enables_scratch_with_legacy_criticism_by_default():
    """Amendment 11/R28 (2026-08-10): legacy (school-free) criticism is now
    the default -- schools remain seeded for CONJECTURE (N_SCHOOLS, an
    independent knob) but criticism_policy is None by default, not the
    school-routed engaged policy. The full school-routed criticism shape
    (bindings, coverage, authority) is now covered by
    test_public_manifest_binds_all_four_schools_when_school_routed_
    criticism_is_enabled below, under its explicit opt-back-in."""
    profile = _profile()
    manifest = build_preparation_manifest(
        profile,
        question="Does the public preset actually engage its capabilities?",
        compiled_at=STAMP,
    )

    assert POLICY_PRESET_ID == "deepreason.v6.engaged.v1"
    # Scratchpad ON with the deterministic embedder and no new dependency.
    assert manifest.scratch_policy is not None
    assert manifest.scratch_policy.enabled is True
    assert manifest.scratch_policy.embedder_backend == "deterministic_hashing"
    assert manifest.scratch_policy.embedder_model is None
    # Scratch authoring and bounded conjecture context are ON.
    control = manifest.control_plane_policy
    assert control == engaged_control_plane_policy_v3()
    assert control.scratch_authoring.enabled is True
    assert control.conjecture_context.mode == "harness_plus_model_request"
    # Legacy (school-free) criticism by default: Road E's circuit, no
    # manifest-owned criticism_policy at all.
    assert manifest.criticism_policy is None
    # The conjecture-side school roster is unaffected -- still seeded,
    # independent of criticism's routing.
    engine = json.loads(manifest.engine_config_json)
    assert engine["N_SCHOOLS"] == 4


def test_public_manifest_binds_all_four_schools_when_school_routed_criticism_is_enabled(
    monkeypatch,
):
    """The pre-Amendment-11 default shape, now reachable by explicitly
    setting LEGACY_CRITICISM_ENABLED=False -- the operator's own words:
    "That's a configuration option." Nothing about the mechanism changed,
    only which value ships as the default."""
    original_config = preparation_module.Config

    def _forced_school_routed_config(**kwargs):
        return original_config(**kwargs, LEGACY_CRITICISM_ENABLED=False)

    monkeypatch.setattr(preparation_module, "Config", _forced_school_routed_config)
    profile = _profile()
    manifest = build_preparation_manifest(
        profile,
        question="Does opting back into school-routed criticism still work?",
        compiled_at=STAMP,
    )

    # Foreign-school criticism is compiled into the public manifest with one
    # binding per seeded school, all seated on the single provider endpoint.
    criticism = manifest.criticism_policy
    assert criticism is not None
    assert criticism == engaged_criticism_policy(profile.endpoint_id)
    assert tuple(binding.school_id for binding in criticism.bindings) == (
        "school-0",
        "school-1",
        "school-2",
        "school-3",
    )
    assert all(
        binding.role == "argumentative_critic"
        and binding.seat == 0
        and binding.endpoint_id == profile.endpoint_id
        for binding in criticism.bindings
    )
    assert criticism.minimum_foreign_school_coverage == 1
    assert criticism.authority == "observe_only"
    assert criticism.target_eligibility == "accepted_school_artifacts"
    assert criticism.allow_shared is True
    # The seeded school roster and the criticism bindings agree.
    engine = json.loads(manifest.engine_config_json)
    assert engine["N_SCHOOLS"] == len(criticism.bindings) == 4


def test_seat_school_flag_produces_route_bound_policy(monkeypatch):
    """Part E (S2d/R5, Amendment 11/R27) Step 44: school_seats (the
    --school-seat CLI flag's eventual carrier) binds ONE named school's
    conjecturer seat to a distinct route, gated on SCHOOL_SEATS_ENABLED,
    and never touches criticism_policy at all -- proving the conjecture-
    side lever is independent of the criticism-side one (Step 44b)."""

    original_config = preparation_module.Config

    def _forced_school_seats_config(**kwargs):
        return original_config(**kwargs, SCHOOL_SEATS_ENABLED=True)

    monkeypatch.setattr(preparation_module, "Config", _forced_school_seats_config)
    profile = _profile()
    distinct_profile = _profile(
        endpoint="https://distinct.example.test/v1",
        model_id="model-school-seat",
        credential_env="DEEPREASON_SCHOOL_SEAT_TEST_KEY",
    )

    manifest = build_preparation_manifest(
        profile,
        question="Does a school seat bind just that school's route?",
        compiled_at=STAMP,
        school_seats={"school-1": distinct_profile},
    )

    # The conjecturer role is now a two-seat ensemble: the default profile
    # at seat 0, the distinct profile at seat 1.
    conjecturer_routes = manifest.roles["conjecturer"]
    assert len(conjecturer_routes) == 2
    assert conjecturer_routes[0].endpoint_id == profile.endpoint_id
    assert conjecturer_routes[1].endpoint_id == distinct_profile.endpoint_id

    school_execution = manifest.control_plane_policy.school_execution
    assert school_execution.mode == "route_bound"
    by_school = {b.school_id: b for b in school_execution.bindings}
    assert set(by_school) == {"school-0", "school-1", "school-2", "school-3"}
    assert by_school["school-1"].endpoint_id == distinct_profile.endpoint_id
    assert by_school["school-1"].seat == 1
    assert by_school["school-1"].role == "conjecturer"
    for school_id in ("school-0", "school-2", "school-3"):
        assert by_school[school_id].endpoint_id == profile.endpoint_id
        assert by_school[school_id].seat == 0
    # Legacy (default, per Part B2) criticism is untouched by this flag.
    assert manifest.criticism_policy is None


def test_seat_school_flag_refuses_without_the_master_gate(monkeypatch):
    """Defense-in-depth companion (mirrors the CLI's own gate): school_seats
    given while SCHOOL_SEATS_ENABLED stays at its default False is a typed
    refusal, not a silent no-op or an accidental route_bound compile."""

    profile = _profile()
    distinct_profile = _profile(
        endpoint="https://distinct.example.test/v1",
        model_id="model-school-seat",
        credential_env="DEEPREASON_SCHOOL_SEAT_TEST_KEY",
    )

    with pytest.raises(RunManifestError, match="SCHOOL_SEATS_DISABLED"):
        build_preparation_manifest(
            profile,
            question="Does an ungated school seat refuse cleanly?",
            compiled_at=STAMP,
            school_seats={"school-0": distinct_profile},
        )


def test_criticism_seat_flag_produces_distinct_binding_when_school_routed(monkeypatch):
    """Step 44b (S2d/R27, SPEC.md addendum S18): criticism_seats (the
    --criticism-seat CLI flag's eventual carrier) binds ONE named school's
    argumentative_critic seat to a distinct route, gated on
    SCHOOL_SEATS_ENABLED AND LEGACY_CRITICISM_ENABLED=False, and never
    touches control_plane_policy.school_execution at all -- proving the
    criticism-side lever is independent of Step 44's conjecture-side one."""

    original_config = preparation_module.Config

    def _forced_criticism_seats_config(**kwargs):
        return original_config(
            **kwargs, SCHOOL_SEATS_ENABLED=True, LEGACY_CRITICISM_ENABLED=False
        )

    monkeypatch.setattr(preparation_module, "Config", _forced_criticism_seats_config)
    profile = _profile()
    distinct_profile = _profile(
        endpoint="https://distinct.example.test/v1",
        model_id="model-criticism-seat",
        credential_env="DEEPREASON_CRITICISM_SEAT_TEST_KEY",
    )

    manifest = build_preparation_manifest(
        profile,
        question="Does a criticism seat bind just that school's critic route?",
        compiled_at=STAMP,
        criticism_seats={"school-2": distinct_profile},
    )

    # The argumentative_critic role is now a two-seat ensemble: the default
    # profile at seat 0, the distinct profile at seat 1.
    critic_routes = manifest.roles["argumentative_critic"]
    assert len(critic_routes) == 2
    assert critic_routes[0].endpoint_id == profile.endpoint_id
    assert critic_routes[1].endpoint_id == distinct_profile.endpoint_id

    criticism = manifest.criticism_policy
    by_school = {b.school_id: b for b in criticism.bindings}
    assert set(by_school) == {"school-0", "school-1", "school-2", "school-3"}
    assert by_school["school-2"].endpoint_id == distinct_profile.endpoint_id
    assert by_school["school-2"].seat == 1
    assert by_school["school-2"].role == "argumentative_critic"
    for school_id in ("school-0", "school-1", "school-3"):
        assert by_school[school_id].endpoint_id == profile.endpoint_id
        assert by_school[school_id].seat == 0
    # Conjecture-side routing (Step 44's lever) is untouched by this flag.
    assert manifest.control_plane_policy.school_execution.mode == "conditioning_only"


def test_criticism_seat_flag_refuses_without_school_routed_criticism(monkeypatch):
    """criticism_seats requires LEGACY_CRITICISM_ENABLED=False already set:
    a per-school distinct critic route means nothing while criticism is
    still routed through the school-free legacy circuit (Amendment 11/R28's
    now-default). Refuses typed, not a silent no-op."""

    original_config = preparation_module.Config

    def _forced_school_seats_only_config(**kwargs):
        return original_config(**kwargs, SCHOOL_SEATS_ENABLED=True)

    monkeypatch.setattr(preparation_module, "Config", _forced_school_seats_only_config)
    profile = _profile()
    distinct_profile = _profile(
        endpoint="https://distinct.example.test/v1",
        model_id="model-criticism-seat",
        credential_env="DEEPREASON_CRITICISM_SEAT_TEST_KEY",
    )

    with pytest.raises(
        RunManifestError, match="CRITICISM_SEATS_REQUIRE_SCHOOL_ROUTED_CRITICISM"
    ):
        build_preparation_manifest(
            profile,
            question="Does a criticism seat refuse cleanly under legacy criticism?",
            compiled_at=STAMP,
            criticism_seats={"school-0": distinct_profile},
        )


def test_criticism_seat_flag_refuses_without_the_master_gate():
    """Defense-in-depth companion (mirrors the CLI's own gate): criticism_seats
    given while SCHOOL_SEATS_ENABLED stays at its default False is a typed
    refusal -- checked ahead of the LEGACY_CRITICISM_ENABLED check, so this
    fires even though LEGACY_CRITICISM_ENABLED is also still at its default
    True here (both prerequisites are missing; the master gate is reported
    first, matching Step 44's own precedent)."""

    profile = _profile()
    distinct_profile = _profile(
        endpoint="https://distinct.example.test/v1",
        model_id="model-criticism-seat",
        credential_env="DEEPREASON_CRITICISM_SEAT_TEST_KEY",
    )

    with pytest.raises(RunManifestError, match="SCHOOL_SEATS_DISABLED"):
        build_preparation_manifest(
            profile,
            question="Does an ungated criticism seat refuse cleanly?",
            compiled_at=STAMP,
            criticism_seats={"school-0": distinct_profile},
        )


def test_legacy_criticism_enabled_by_default_is_byte_identical():
    """Amendment 11/R28 (2026-08-10, supersedes Part B/R3's original
    default): LEGACY_CRITICISM_ENABLED now defaults True -- the operator's
    words, "Legacy, not schools, should be default for criticism" -- so
    build_preparation_manifest's criticism_policy is None (Road E's
    school-free circuit) at the bare default, not the school-routed
    engaged policy."""

    assert Config().LEGACY_CRITICISM_ENABLED is True
    profile = _profile()
    manifest = build_preparation_manifest(
        profile,
        question="Does the default public preset stay school-free?",
        compiled_at=STAMP,
    )
    assert manifest.criticism_policy is None


def test_legacy_criticism_enabled_routes_to_school_free_circuit(monkeypatch):
    """Part B (S2c, R3): with the flag True, build_preparation_manifest
    passes criticism_policy=None -- Road E's school-free circuit -- instead
    of the engaged school-routed policy. `_config_for_profile` builds its
    own Config internally with no caller override, so the flag is forced
    the same way any of its non-injected fields would be: by wrapping the
    Config constructor it calls."""

    original_config = preparation_module.Config

    def _forced_legacy_config(**kwargs):
        return original_config(**kwargs, LEGACY_CRITICISM_ENABLED=True)

    monkeypatch.setattr(preparation_module, "Config", _forced_legacy_config)
    profile = _profile()

    manifest = build_preparation_manifest(
        profile,
        question="Does the legacy-enabled preset skip school routing?",
        compiled_at=STAMP,
    )

    assert manifest.criticism_policy is None


def test_engaged_criticism_authority_inert_without_the_master_gate(monkeypatch):
    """Part C (S2a, R1): ENGAGED_CRITICISM_AUTHORITY is one of the six
    knobs SPEC.md's design names explicitly ("it only permits an
    operator to set ARGUMENTATIVE_AUTHORITY/ENGAGED_CRITICISM_AUTHORITY/
    etc. away from observe_only") -- found missing while writing Step
    31's map claim that "all six knobs sit behind this gate," which was
    not yet true for this one. With ADJUDICATION_STATUS_AUTHORITY_ENABLED
    at its default False, setting ENGAGED_CRITICISM_AUTHORITY away from
    observe_only must not reach the compiled manifest.

    Amendment 11/R28 collateral: ENGAGED_CRITICISM_AUTHORITY only matters
    on the school-routed path (it's engaged_criticism_policy's authority=
    argument), so this test must also opt back into school routing
    (LEGACY_CRITICISM_ENABLED=False, now non-default) to keep exercising
    what it actually tests -- otherwise criticism_policy is None and this
    knob's gate is untestable, not proven inert."""

    original_config = preparation_module.Config

    def _forced_defended_trial_config(**kwargs):
        return original_config(
            **kwargs,
            ENGAGED_CRITICISM_AUTHORITY="defended_trial",
            LEGACY_CRITICISM_ENABLED=False,
        )

    monkeypatch.setattr(preparation_module, "Config", _forced_defended_trial_config)
    profile = _profile()

    manifest = build_preparation_manifest(
        profile,
        question="Does an unconsented defended_trial setting stay inert?",
        compiled_at=STAMP,
    )

    assert manifest.criticism_policy.authority == "observe_only"


def test_engaged_criticism_authority_reachable_with_the_master_gate(monkeypatch):
    """Part C (S2a, R1) companion: with the master flag ALSO True,
    ENGAGED_CRITICISM_AUTHORITY's configured value reaches
    engaged_criticism_policy's authority= argument -- proving the gate
    does not accidentally make the knob permanently unreachable, only
    conditionally so. Checked at the argument-passing layer, not a full
    manifest compile: `defended_trial` also requires two cross-family
    judge seats (a separate, unrelated compile-time guard) that
    build_preparation_manifest's single-profile broadcast cannot supply
    regardless of this flag -- reaching that combination is Part D's
    seat-diversity territory, not this test's concern.

    Amendment 11/R28 collateral: same reasoning as the companion test
    above -- LEGACY_CRITICISM_ENABLED=False is required to keep this
    test on the school-routed path ENGAGED_CRITICISM_AUTHORITY actually
    gates."""

    original_config = preparation_module.Config

    def _forced_defended_trial_config(**kwargs):
        return original_config(
            **kwargs,
            ENGAGED_CRITICISM_AUTHORITY="defended_trial",
            ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
            LEGACY_CRITICISM_ENABLED=False,
        )

    monkeypatch.setattr(preparation_module, "Config", _forced_defended_trial_config)
    captured = {}
    original_policy = preparation_module.configured_criticism_policy

    def _capturing_policy(config, endpoint_id, *, seat_map=None):
        captured.update(
            authority=config.ENGAGED_CRITICISM_AUTHORITY,
            endpoint_id=endpoint_id,
            school_count=config.N_SCHOOLS,
        )
        safe = config.model_copy(
            update={"ENGAGED_CRITICISM_AUTHORITY": "observe_only"}
        )
        return original_policy(safe, endpoint_id, seat_map=seat_map)

    monkeypatch.setattr(
        preparation_module, "configured_criticism_policy", _capturing_policy
    )
    profile = _profile()

    build_preparation_manifest(
        profile,
        question="Does a consented defended_trial setting reach the call?",
        compiled_at=STAMP,
    )

    assert captured == {
        "authority": "defended_trial",
        "endpoint_id": profile.endpoint_id,
        "school_count": 4,
    }


def test_public_manifest_compiles_the_grounded_two_stage_bridge():
    profile = _profile()
    manifest = build_preparation_manifest(
        profile,
        question="Can the public preset build a grounded final view?",
        compiled_at=STAMP,
    )

    bridge = manifest.bridge_policy
    assert bridge is not None
    assert bridge.mode == "grounded_two_stage"
    # The audited review-free single-route shape from the engaged preset.
    assert bridge.grounding_review is True
    assert bridge.max_schema_repair_attempts == 1
    assert bridge.max_grounding_repair_attempts == 0
    assert bridge.output_section_limit == 4
    assert bridge.ledger_role == "summarizer"
    assert bridge.composer_role == "thesis"
    assert bridge.allow_partial is True
    assert bridge.allow_abstention is True
    assert bridge.require_claim_ledger is True
    assert bridge.require_claim_uses is True
    # Both frozen bridge roles are seated on the single public endpoint.
    for role in ("summarizer", "thesis"):
        (route,) = manifest.roles[role]
        assert route.endpoint_id == profile.endpoint_id
    # Frozen schema-repair authority covers the four bridge wire contracts.
    repair_policy = manifest.contract_schema_repair_policy
    assert repair_policy is not None
    grants = {grant.contract_id: grant for grant in repair_policy.grants}
    for contract_id in (
        "bridge.ledger.v3",
        "bridge.ledger-batch.v1",
        "bridge.composition.v2",
        "bridge.composition-batch.v1",
    ):
        assert grants[contract_id].maximum_schema_repairs == 1
        assert grants[contract_id].maximum_provider_calls == 2


def test_public_manifest_grants_conjecture_family_multi_pointer_repairs():
    """One patch repairs one pointer; four covers live multi-pointer failures.

    The first live engaged run made four independent handle-pattern mistakes
    in one semantically sound conjecturer.turn.v6 output and was structurally
    doomed under the shared two-repair ceiling.  The public preset therefore
    grants the conjecture family (strong turn plus its atomic decomposition
    child) four repairs / five provider calls, keeps every other non-bridge
    contract at two repairs, and announces the recomputed qualification
    maximum: 2 conjecture pairs x 20 cases x 5 calls + 8 pairs x 20 x 3 +
    5 bridge pairs x 20 x 2 = 880 (the reviewer seat is the fifth).
    """

    from deepreason.preparation import qualification_subject_manifest
    from deepreason.qualification import (
        production_qualification_maximum_provider_calls,
    )

    manifest = qualification_subject_manifest(_profile())
    repair_policy = manifest.contract_schema_repair_policy
    assert repair_policy is not None
    grants = {grant.contract_id: grant for grant in repair_policy.grants}
    for contract_id in ("conjecturer.turn.v6", "conjecturer.atomic-candidate.v1"):
        assert grants[contract_id].maximum_schema_repairs == 4
        assert grants[contract_id].maximum_provider_calls == 5
    for contract_id in sorted(grants):
        # The grounding review/repair streams are bridge-family contracts
        # whose ids carry no "bridge." prefix; they take the bridge
        # ceiling, not the ordinary non-bridge one.
        if contract_id.startswith(("bridge.", "conjecturer.", "grounding")):
            continue
        assert grants[contract_id].maximum_schema_repairs == 2
        assert grants[contract_id].maximum_provider_calls == 3
    # 880 base battery calls plus the bounded flake re-exercise allowance
    # (the three most expensive pair blocks may each be redrawn once).
    # Seating the reviewer added one bridge pair: 20 cases x 2 calls = 40,
    # so the announced ceiling is the direct price of that seat.
    assert production_qualification_maximum_provider_calls(manifest) == 1140


def test_public_manifest_enables_declarative_local_simulation():
    profile = _profile()
    manifest = build_preparation_manifest(
        profile,
        question="Can the public preset run one bounded local simulation?",
        compiled_at=STAMP,
    )

    capabilities = manifest.inquiry_capability_policy
    assert capabilities is not None
    assert capabilities.capability_profile == "inquiry-capabilities.v2"
    assert capabilities == engaged_inquiry_capability_policy()
    simulation = capabilities.simulation
    assert simulation == engaged_simulation_policy()
    assert simulation.enabled is True
    # The CONTAINED runner since 2026-08-28, so model-authored
    # `sandboxed_python_v1` executes on a run nobody configured. Declarative
    # numeric documents still run too — the container profile serves both, and
    # is the stronger home for the harness-compiled one. One bounded proposal
    # per turn, no sealed inputs in question-only public preparation.
    assert simulation.runner_profile == "simulation.container.v1"
    assert simulation.maximum_proposals_per_turn == 1
    assert simulation.input_catalog == ()
    # Research became a default-ON evidence channel in F3 (2026-08-26) --
    # "turning research and, simulation and coding permanently on" -- so the
    # public manifest now compiles it enabled, with the declared allowlist and
    # the finite bounds its validator requires. The two that stay OFF stay off
    # for their own reasons: attached evidence is the operator's per-run
    # attach gesture, and formalization is Lean, which the manifest validator
    # refuses to enable at all.
    assert capabilities.attached_evidence.enabled is False
    assert capabilities.formalization.enabled is False
    assert capabilities.research.enabled is True
    assert capabilities.research.domain_allowlist
    assert capabilities.research.maximum_requests > 0
    assert capabilities.research.maximum_sources > 0
    # One frozen no-network toolchain, pinned to the preparing interpreter
    # rather than any hardcoded path, and PAIRED with the runner the policy
    # names — a configuration must never carry a toolchain its runner cannot
    # dispatch to.
    (toolchain,) = manifest.toolchains
    assert toolchain.id == simulation.python_toolchain_identity
    assert toolchain.runner == "container"
    assert toolchain.network is False
    assert toolchain.executable == str(Path(sys.executable).resolve())


def _route(endpoint_id: str, seat: int = 0) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": f"offline-model-{seat}",
        "provider": "mock",
        "family": f"offline-family-{seat}",
        "max_tokens": 64,
        "context_window_tokens": 262_144,
    }


def _public_preset_mock_manifest():
    """Compile the engaged public preset against one shared mock endpoint."""

    config = Config(
        N_SCHOOLS=4,
        scratchpad={"enabled": True},
        bridge=engaged_bridge_source(),
        EMBEDDER_MODEL=None,
        roles={
            "conjecturer": [_route("conjecturer-route")],
            "argumentative_critic": [_route("critic-route-0")],
            "synthesizer": [_route("synthesizer-route")],
            "summarizer": [_route("summarizer-route")],
            "thesis": [_route("thesis-route")],
            # The engaged bridge now reviews, and the reviewer role is
            # judge; a grounded bridge refuses to compile without it.
            "judge": [_route("judge-route")],
        },
    )
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=engaged_control_plane_policy_v3(),
        criticism_policy=engaged_criticism_policy("critic-route-0"),
        inquiry_capability_policy=engaged_inquiry_capability_policy(),
        run_input_digest="f" * 64,
        # Track the ENGAGED policy rather than hardcoding the local toolchain:
        # the manifest validator requires the bound toolchain to match the
        # policy's runner, and the default runner changed on 2026-08-28.
        toolchains=(engaged_simulation_toolchain(),),
    )
    return config, manifest


def _bind_classification(harness: Harness, manifest) -> None:
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    harness.bind_model_classification(manifest, report)


def test_public_preset_run_dispatches_school_routed_criticism(tmp_path):
    config, manifest = _public_preset_mock_manifest()
    harness = Harness(tmp_path / "criticism")
    _bind_classification(harness, manifest)
    target = harness.create_artifact(
        "school-owned mechanism awaiting foreign review",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    assert harness.state.status[target.id] == Status.ACCEPTED
    critic_route = manifest.roles["argumentative_critic"][0]
    critic_response = json.dumps(
        {
            "cases": [
                {
                    "target_alias": "SRC_001",
                    "attack": True,
                    "case": "the mechanism names no discriminating observation",
                }
            ]
        }
    )
    endpoints = {
        "conjecturer": MockEndpoint(lambda _prompt: '{"candidates":[]}'),
        "argumentative_critic": MockEndpoint(
            lambda _prompt: critic_response,
            name=critic_route.base_url,
            model=critic_route.model_id,
            max_tokens=critic_route.max_tokens,
        ),
    }
    adapter = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
        meter=TokenMeter(100_000),
    )
    scheduler = Scheduler(harness, adapter, config, run_manifest=manifest)

    scheduler._foreign_arg_crit()

    assignments = []
    attempts = []
    debts = []
    for event in harness.log.read():
        for object_id in event.outputs:
            schema, record = harness.objects.get(object_id)
            if schema == "criticism-assignment-v1" and record.target_id == target.id:
                assignments.append(record)
            elif schema == "criticism-attempt-v1" and record.target_id == target.id:
                attempts.append(record)
            elif schema == "criticism-coverage-debt-v1" and record.target_id == target.id:
                debts.append(record)
    # At least one school-routed criticism work order dispatched and landed.
    assert len(assignments) == 1
    assert assignments[0].critic_school_id != "school-0"
    assert assignments[0].endpoint_id == "critic-route-0"
    assert len(attempts) == 1
    assert attempts[0].coverage_completed is True
    assert attempts[0].critic_school_id == assignments[0].critic_school_id
    # The dispatching provider call carries its school-route receipt.
    source = next(
        event
        for event in harness.log.read()
        if event.seq == attempts[0].source_call_seq
    )
    assert source.llm is not None
    assert source.llm.school_route.school_id == assignments[0].critic_school_id
    # A semantic (not merely form-checking) criticism was admitted.
    critics = [
        artifact
        for artifact in harness.state.artifacts.values()
        if artifact.provenance is not None
        and artifact.provenance.role == "critic"
        and artifact.provenance.school == assignments[0].critic_school_id
    ]
    assert len(critics) == 1
    assert "discriminating observation" in critics[0].content_ref
    # Coverage completed: the manifest floor of one foreign school is met.
    assert len(debts) == 1
    assert debts[0].termination_reason == "coverage_complete"
    assert debts[0].completed_school_ids == (assignments[0].critic_school_id,)
    assert debts[0].outstanding_school_ids == ()


def _legacy_criticism_mock_manifest():
    """Compile a public-preset-shaped manifest with LEGACY_CRITICISM_ENABLED
    True: schools stay seeded (unrelated), but criticism_policy is None --
    Road E's school-free circuit -- exactly what build_preparation_manifest
    now produces for this flag."""

    config = Config(
        N_SCHOOLS=4,
        LEGACY_CRITICISM_ENABLED=True,
        scratchpad={"enabled": True},
        bridge=engaged_bridge_source(),
        EMBEDDER_MODEL=None,
        roles={
            "conjecturer": [_route("conjecturer-route")],
            "argumentative_critic": [_route("critic-route-0")],
            "synthesizer": [_route("synthesizer-route")],
            "summarizer": [_route("summarizer-route")],
            "thesis": [_route("thesis-route")],
            "judge": [_route("judge-route")],
        },
    )
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=engaged_control_plane_policy_v3(),
        criticism_policy=None,
        inquiry_capability_policy=engaged_inquiry_capability_policy(),
        run_input_digest="f" * 64,
        # Track the ENGAGED policy rather than hardcoding the local toolchain:
        # the manifest validator requires the bound toolchain to match the
        # policy's runner, and the default runner changed on 2026-08-28.
        toolchains=(engaged_simulation_toolchain(),),
    )
    return config, manifest


def test_legacy_criticism_end_to_end_dispatches_without_a_school(tmp_path):
    """Part B (S2c, R3): with LEGACY_CRITICISM_ENABLED True and
    criticism_policy=None, a scheduler run's plain _arg_crit path actually
    dispatches a live crit_argumentative_batch call through Road E's
    contract -- not deferred, and with no school in the resulting artifact
    or durable payload."""

    config, manifest = _legacy_criticism_mock_manifest()
    harness = Harness(tmp_path / "legacy-criticism-end-to-end")
    _bind_classification(harness, manifest)
    target = harness.create_artifact(
        "a claim with no school-owned lineage",
        provenance=Provenance(role="conjecturer"),
    )
    assert harness.state.status[target.id] == Status.ACCEPTED
    critic_route = manifest.roles["argumentative_critic"][0]
    critic_response = json.dumps(
        {
            "cases": [
                {
                    "target_alias": "SRC_001",
                    "attack": True,
                    "case": "the claim omits a required boundary condition",
                }
            ]
        }
    )
    endpoints = {
        "conjecturer": MockEndpoint(lambda _prompt: '{"candidates":[]}'),
        "argumentative_critic": MockEndpoint(
            lambda _prompt: critic_response,
            name=critic_route.base_url,
            model=critic_route.model_id,
            max_tokens=critic_route.max_tokens,
        ),
    }
    adapter = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
        meter=TokenMeter(100_000),
    )
    scheduler = Scheduler(harness, adapter, config, run_manifest=manifest)

    scheduler._arg_crit([target.id])

    assert not any(
        event.inputs[:2] == ("v6-model-phase-deferred.v1", "argumentative-criticism")
        for event in harness.log.read()
    )
    critics = [
        artifact
        for artifact in harness.state.artifacts.values()
        if artifact.provenance is not None and artifact.provenance.role == "critic"
    ]
    assert len(critics) == 1
    assert critics[0].provenance.school is None
    assert "required boundary condition" in critics[0].content_ref
    work = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.task_payload_value.get("schema")
        == "criticism.semantic-task.v1"
    ]
    assert len(work) == 1
    assert work[0].preparation.task_payload_value["critic_school_id"] is None
    assert work[0].preparation.task_payload_value["dispatch_authority"] == "observe_only"


def test_public_preset_permits_bounded_scratch_authoring(tmp_path):
    policy = engaged_control_plane_policy_v3().scratch_authoring
    assert policy.enabled is True
    service = ScratchService(tmp_path / "scratch")
    author = ScratchAuthoringService(service, object())
    formal_before = service.harness.state.model_dump(mode="json")

    proposal = ScratchProposalV1(
        new_blocks=(
            ScratchNewBlockDraftV1(
                local_key="NEW_001",
                body=ScratchBlockDraftBodyV1(
                    content="Provisional pressure-relief thought",
                    unfinished="Needs one discriminating counter-case",
                ),
            ),
            ScratchNewBlockDraftV1(
                local_key="NEW_002",
                body=ScratchBlockDraftBodyV1(content="A rival provisional thought"),
            ),
        ),
        links=(
            ScratchProposalLinkV1(
                from_ref="NEW_001",
                to_ref="NEW_002",
                relation_hint="provisional rivalry",
            ),
        ),
    )
    outputs = author.admit_proposal(
        proposal,
        policy=policy,
        visible_aliases={},
        context_ref="transaction:engaged-preset:scratch-authoring",
    )

    assert len(outputs) == 3
    assert len(service.state.blocks) == 2
    assert len(service.state.links) == 1
    # Advisory only: nothing leaked into formal ontology state.
    assert service.harness.state.model_dump(mode="json") == formal_before


def test_public_preset_mock_run_stages_and_consumes_one_simulation_proposal(
    tmp_path,
):
    """The engaged preset carries one proposal through its whole lifecycle.

    Wire: a mock conjecture turn proposes one declarative-numeric simulation.
    Staging: the transactional conjecture admits it as a durable proposal.
    Execute: the first scheduler capability step compiles and runs it on the
    frozen local toolchain and packages the bounded result. Consume: the
    second capability step dispatches one fresh follow-up conjecture turn
    that sees the recorded result and records the consumption.
    """

    config, manifest = _public_preset_mock_manifest()
    harness = ScratchService(tmp_path / "public-simulation").harness
    harness.register_commitment(
        Commitment(id="k-public-sim", eval="predicate:len(content) > 0")
    )
    harness.register_problem(
        Problem(
            id="pi-public-sim",
            description="Does the bounded transfer stay below ten units?",
            criteria=["k-public-sim"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    source = json.dumps(
        {
            "schema": "declarative-numeric.v1",
            "observables": {
                "x": {
                    "op": "div",
                    "args": [
                        {"input": "parameters.weight_bytes"},
                        {"const": 2},
                    ],
                }
            },
        }
    )
    simulation_turn = {
        "candidates": [
            {
                "content": "A bounded mechanism awaiting one discriminating simulation.",
                "typicality": 0.31,
            }
        ],
        # The public preset has no sealed input catalog, so the proposal
        # names no input aliases and parameterizes its program directly.
        "simulation_proposals": [
            {
                "request_identifier": "public-preset-discriminator",
                "hypothesis": "The bounded transfer stays below ten units.",
                "rival_predictions": ["x is below 10", "x is at least 10"],
                "discriminating_purpose": "Separate the two bounded rivals.",
                "declared_assumptions": ["The schedule is synthetic."],
                "parameter_definitions": [
                    {"name": "one", "values_json": '{"weight_bytes":12}'}
                ],
                "requested_seed_set": [],
                "simulation_mode": "declarative_numeric_v1",
                "model_source": source,
                "requested_observables": ["x"],
                "interpretation_conditions": ["x below 10 favors the first rival."],
            }
        ],
    }
    prompts: list[str] = []

    def respond(prompt: str) -> str:
        prompts.append(prompt)
        if len(prompts) == 1:
            return json.dumps(simulation_turn)
        assert "recorded simulation result" in prompt
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": (
                            "A fresh formal proposal stated after the recorded "
                            "simulation."
                        ),
                        "typicality": 0.2,
                    }
                ]
            }
        )

    route = manifest.roles["conjecturer"][0]
    endpoint = MockEndpoint(
        respond,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    _bind_classification(harness, manifest)
    adapter.bind_v6_authority(harness, manifest)

    conj(
        harness,
        "pi-public-sim",
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )

    # Staged: one durable transactional proposal bound to its provider work.
    (proposal,) = harness.capability_state.proposals.values()
    assert proposal.simulation_mode == "declarative_numeric_v1"
    assert proposal.input_aliases == ()
    controller = SimulationCapabilityController(harness, manifest)
    controller.require_transactional_origin(proposal)

    scheduler = Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    scheduler.step()

    # Executed on the frozen local toolchain and packaged, never denied.
    state = harness.capability_state
    (package,) = state.result_packages.values()
    transition = state.transitions[state.current_transition_by_request[proposal.id]]
    assert transition.lifecycle == CapabilityLifecycle.RESULT_PACKAGED
    assert not any(
        item.lifecycle == CapabilityLifecycle.DENIED
        for item in state.transitions.values()
    )
    (receipt,) = state.receipts.values()
    assert receipt.operational_status == "succeeded"

    scheduler.step()

    # Consumed by one fresh follow-up conjecture work item.
    transition = state.transitions[state.current_transition_by_request[proposal.id]]
    assert transition.lifecycle == CapabilityLifecycle.CONSUMED
    (consumption,) = state.consumptions.values()
    assert consumption.result_package_ref == package.id
    assert consumption.follow_up_work_order_ref != proposal.originating_work_order_ref
    assert len(prompts) == 2
    assert "recorded simulation result" in prompts[1]


def test_public_preset_root_accepts_start_bridge_and_reaches_terminal(
    tmp_path, monkeypatch
):
    """MCP ``start_bridge`` completes on a real public-preset run root.

    The root is prepared exactly as the public boundary leaves it: the
    question-derived run input, the compiled engaged-preset manifest, the
    qualification report, the bound model classification, and an eligible
    completed ``run-result.json``.  Provider transport is mocked at
    ``_endpoint_from_spec``; everything else is the production path.
    """

    from tests.test_v6_bridge_transactions import (
        _write_bridge_qualification,
        _write_eligible_v6_run_result,
    )

    question = "Which surviving public idea should be presented?"
    profile = _profile()
    root = tmp_path / "public-bridge-run"
    dossier, run_input, _workload = _records_for_question(question)
    bind_run_input(run_input, dossier, root)
    manifest = build_preparation_manifest(
        profile, question=question, compiled_at=STAMP
    )
    assert manifest.run_input_digest == run_input.run_input_digest
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    problem_id = run_input.problem.id
    harness.register_problem(
        Problem(
            id=problem_id,
            description=question,
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    harness.create_artifact(
        "A genuinely novel surviving conjecture.",
        provenance=Provenance(role="conjecturer"),
        problem_id=problem_id,
    )
    _write_bridge_qualification(harness, manifest)
    _write_eligible_v6_run_result(root, manifest)

    # The public bridge does three units of provider WORK: the frozen
    # summarizer builds the claim ledger, the frozen thesis route composes the
    # grounded output, and the frozen judge route reviews its grounding. The
    # third is the direct cost of seating the reviewer: review is a provider
    # call, not free.
    #
    # Each of those is now TWO dispatches, not one. The public preset is a
    # reasoning route, so the split-budget seat protocol (llm/split.py) arms
    # under its shipped default: a deliberation leg at B_r whose prose is never
    # validated, then a non-thinking emission leg at B_a that produces the wire
    # value. The script therefore interleaves -- prose, value, prose, value,
    # prose, value -- and the deliberation responses are deliberately not
    # JSON, because nothing parses them.
    deliberation = "Weighing the record before serialising."
    responses = [
        deliberation,
        json.dumps(
            {
                "entries": [
                    {
                        "entry_key": "CLM_1",
                        "claim_class": "surviving_conjecture",
                        "claim": "A novel conjecture survives the formal record.",
                        "formal_artifact_handles": ["ART_1"],
                    }
                ]
            }
        ),
        deliberation,
        json.dumps(
            {
                "sections": [
                    {
                        "span_id": "S1",
                        "text": (
                            "Conjecture: the surviving idea may explain the result."
                        ),
                        "ledger_entry_handles": ["E2"],
                    }
                ],
                "resolution": "partially_answered",
                "resolution_reason": "The record supports a conjecture, not a fact.",
            }
        ),
        deliberation,
        json.dumps({"finding": "supported"}),
    ]
    dispatched = []
    route = manifest.roles["summarizer"][0]

    def endpoint_factory(spec):
        assert spec["endpoint_id"] == profile.endpoint_id

        def dispatch(_prompt):
            dispatched.append(spec["endpoint_id"])
            assert responses, "the public bridge dispatched unscripted provider work"
            return responses.pop(0)

        return MockEndpoint(
            dispatch,
            name=route.base_url,
            model=route.model_id,
            max_tokens=route.max_tokens,
        )

    monkeypatch.setattr(adapter_module, "_endpoint_from_spec", endpoint_factory)
    run_id = root.name
    monkeypatch.setattr(mcp, "_managed_root", lambda value: {run_id: root}[value])

    started = mcp.call_tool(
        "start_bridge",
        {"run_id": run_id, "problem": problem_id, "target": "answer"},
    )
    assert started["state"] == "running"
    assert started["run_id"] == run_id
    worker = mcp._BRIDGE_THREADS[str(root.resolve())]
    worker.join(timeout=10)
    assert not worker.is_alive()

    status = mcp.call_tool("bridge_status", {"run_id": run_id})
    assert status["state"] == "completed"
    assert status["process_status"] == "success"
    result = mcp.call_tool("bridge_result", {"run_id": run_id, "limit": 5})
    assert result["terminal"]["process_status"] == "success"
    assert result["output"]["resolution"] == "partially_answered"
    # Exactly the six scripted dispatches, no more: three units of work at
    # two legs each. The three units are ledger, composition and grounding
    # review; the second leg of each is what the split-budget protocol costs
    # in round trips, and it buys a seat that answers when its cap runs out.
    assert dispatched == [profile.endpoint_id] * 6
    assert responses == []
    actions = [
        event.bridge.action
        for event in Harness(root, read_only=True).log.read()
        if event.bridge is not None
    ]
    assert actions[-1] == BridgeAction.COMPLETED


def test_the_reviewer_seat_carries_behavioral_authority():
    """Regression (coin canonicity run-c5f901f38208e862f4ce2fe60a26e551): the
    run recorded 9 criticisms and 0 refutations, and closed reporting
    accepted:29 refuted:0 over artifacts asserting mutually contradictory
    bounds. The cause was typed — every adjudicating seat qualified
    ``inactive_no_authorized_contract`` and seqs 261-274 deferred the
    spot-check phase with ``transaction-contract-unavailable`` for all 14
    survivors, because ``grounding_review`` was off and that flag is the ONLY
    branch of ``_route_seat_behavioral_contract_assignments`` granting the
    reviewer seat a contract.

    This pins the seat, not the flag: criticism that cannot be adjudicated
    is not criticism the record can act on.
    """

    from deepreason.run_manifest import (
        _route_seat_behavioral_contract_assignments,
    )

    profile = _profile()
    manifest = build_preparation_manifest(
        profile,
        question="Does the reviewer seat actually hold authority?",
        compiled_at=STAMP,
    )
    assignments = _route_seat_behavioral_contract_assignments(manifest)
    by_role: dict[str, set[str]] = {}
    for contract_id, role, _seat in assignments:
        by_role.setdefault(role, set()).add(contract_id)

    reviewer_role = manifest.bridge_policy.reviewer_role
    assert manifest.bridge_policy.grounding_review is True
    # The seat the bridge policy names must hold at least one contract, or
    # it classifies inactive and every phase needing it defers.
    assert by_role.get(reviewer_role), (
        f"reviewer seat {reviewer_role!r} holds no contract; it will qualify "
        "inactive_no_authorized_contract and adjudication will defer"
    )
    # The criticising seat was never the problem and must stay authorized.
    assert by_role.get("argumentative_critic")
