"""V6 conjecture admits valid components without cross-component corruption."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from deepreason.canonical import canonical_json
from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.policy import (
    InquiryCapabilityPolicyV1,
    SimulationInputBindingV1,
)
from deepreason.capabilities.simulation import SimulationCapabilityController
from deepreason.config import Config
from deepreason.rules.conj import conj
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ControlPlanePolicyV3,
    ScratchAuthoringPolicyV1,
    ToolchainEntry,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.scratch.service import ScratchService
from deepreason.workflow.transaction import ContextNamespace
from tests.test_v6_transaction_qualification import (
    _control,
    _route,
    _config,
    _live_adapter,
    _manifest,
    _seed_live_conjecture,
    _simulation_policy,
    _v6_simulation_turn,
)


def _component_diagnostics(harness, work) -> list[dict]:
    admission = next(iter(work.admissions.values()))
    return [json.loads(harness.blobs.get(ref)) for ref in admission.diagnostic_refs]


def test_valid_candidate_and_invalid_optional_scratch_complete_partially(tmp_path):
    policy = ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=1,
        maximum_revisions_per_turn=1,
        maximum_links_per_turn=0,
        maximum_unresolved_questions_per_turn=0,
        maximum_cluster_suggestions_per_turn=0,
        maximum_total_bytes=32_768,
    )
    config = _config()
    manifest = _manifest(scratch_authoring=policy)
    harness = ScratchService(tmp_path / "invalid-optional-scratch").harness
    _seed_live_conjecture(harness)
    response = {
        "candidates": [
            {
                "content": "A valid reversible formal mechanism.",
                "typicality": 0.23,
            }
        ],
        "scratch_proposal": {
            "revisions": [
                {
                    "target_alias": "SCR_999",
                    "body": {"content": "This optional revision names no visible scratch."},
                }
            ]
        },
    }
    adapter, _endpoint = _live_adapter(harness, manifest, [json.dumps(response)])

    registered = conj(
        harness,
        "pi-live-v6",
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )

    (artifact,) = registered
    (work,) = harness.workflow_state.transaction_work.values()
    (admission,) = work.admissions.values()
    assert artifact.id in harness.state.artifacts
    assert artifact.id in admission.admitted_refs
    assert not ScratchService(harness).state.blocks
    assert work.terminal.status == "completed"
    assert work.terminal.reason_code == "semantic_admission_partial"
    assert admission.outcome == "admitted"
    diagnostics = _component_diagnostics(harness, work)
    assert diagnostics == [
        {
            "component": "scratch",
            "disposition": "omitted",
            "error_code": "SCRATCH_ALIAS_UNKNOWN",
            "error_type": "ScratchAuthoringError",
            "message": ("SCRATCH_ALIAS_UNKNOWN: unknown scratch proposal reference(s): SCR_999"),
            "partial_refs": [],
            "phase": "semantic_validation",
            "schema": "conjecture-component-diagnostic.v1",
        }
    ]


def test_simulation_materialization_failure_admits_valid_partial_components(
    tmp_path,
    monkeypatch,
):
    config = _config()
    manifest = _manifest(simulation=_simulation_policy())
    harness = ScratchService(tmp_path / "simulation-materialization-failure").harness
    _seed_live_conjecture(harness)
    response = _v6_simulation_turn()
    response["candidates"] = [
        {
            "content": "A formal mechanism independent of simulation bookkeeping.",
            "typicality": 0.31,
        }
    ]
    second = json.loads(json.dumps(response["simulation_proposals"][0]))
    second["request_identifier"] = "v6-second-discriminator"
    second["hypothesis"] = "The second bounded rival remains below nine units."
    response["simulation_proposals"].append(second)
    adapter, _endpoint = _live_adapter(harness, manifest, [json.dumps(response)])

    def materialize_one_then_fail(
        controller,
        drafts,
        *,
        preparation,
        provider_attempt,
        source_call_seq,
    ):
        controller.propose_transactional(
            drafts[0],
            proposal_index=0,
            preparation=preparation,
            provider_attempt=provider_attempt,
            source_call_seq=source_call_seq,
        )
        raise RuntimeError("injected simulation materialization failure")

    monkeypatch.setattr(
        SimulationCapabilityController,
        "materialize_transactional_proposals",
        materialize_one_then_fail,
    )

    registered = conj(
        harness,
        "pi-live-v6",
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )

    (artifact,) = registered
    (proposal,) = harness.capability_state.proposals.values()
    (work,) = harness.workflow_state.transaction_work.values()
    (admission,) = work.admissions.values()
    assert work.terminal.status == "completed"
    assert work.terminal.reason_code == "semantic_admission_partial"
    assert admission.outcome == "admitted"
    assert artifact.id in admission.admitted_refs
    assert proposal.id in admission.admitted_refs
    assert len(harness.capability_state.proposals) == 1
    SimulationCapabilityController(harness, manifest).require_transactional_origin(proposal)
    (diagnostic,) = _component_diagnostics(harness, work)
    assert diagnostic["component"] == "simulation"
    assert diagnostic["phase"] == "materialization"
    assert diagnostic["disposition"] == "partial"
    assert diagnostic["partial_refs"] == [proposal.id]
    assert diagnostic["error_type"] == "RuntimeError"
    assert diagnostic["message"] == "injected simulation materialization failure"


def _scratch_simulation_manifest():
    scratch_authoring = ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=1,
        maximum_revisions_per_turn=1,
        maximum_links_per_turn=0,
        maximum_unresolved_questions_per_turn=0,
        maximum_cluster_suggestions_per_turn=0,
        maximum_total_bytes=32_768,
    )
    config = Config(
        N_SCHOOLS=0,
        roles={"conjecturer": [_route("conjecturer-route")]},
        scratchpad={
            "enabled": True,
            "max_blocks_per_pack": 4,
            "max_guides_per_pack": 0,
            "semantic_retrieval": False,
            "keyword_retrieval": True,
            "coverage_enabled": False,
            "exploratory_fraction": 0,
            "underexposed_fraction": 0,
        },
    )
    context_policy = ConjectureContextPolicyV1(
        mode="harness_only",
        initial_max_blocks=2,
        initial_max_guides=0,
        max_context_expansion_requests=0,
        max_extra_blocks=0,
        permitted_retrieval_channels=("keyword", "recent", "loose"),
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )
    control_values = _control(scratch_authoring=scratch_authoring).model_dump(mode="python")
    control_values["conjecture_context"] = context_policy.model_dump(mode="python")
    control = ControlPlanePolicyV3.model_validate(control_values)
    sealed_value = {"weight_bytes": 12}
    sealed_input = SimulationInputBindingV1(
        alias="WEIGHT_INPUT",
        description="Frozen weight input; never derived from scratch.",
        value=sealed_value,
        content_sha256=hashlib.sha256(canonical_json(sealed_value)).hexdigest(),
    )
    simulation = _simulation_policy(input_catalog=(sealed_input,))
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-17T00:00:00Z",
        control_plane_policy=control,
        inquiry_capability_policy=InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2",
            simulation=simulation,
        ),
        run_input_digest="f" * 64,
        toolchains=(
            ToolchainEntry(
                id=simulation.python_toolchain_identity,
                runner="local",
                executable=str(Path(sys.executable).resolve()),
                version_output_sha256=hashlib.sha256(version.encode("utf-8")).hexdigest(),
                network=False,
            ),
        ),
    )
    return config, manifest, sealed_value


def test_real_scratch_retrieve_simulate_revise_then_fresh_formal(tmp_path):
    config, manifest, sealed_value = _scratch_simulation_manifest()
    harness = ScratchService(tmp_path / "scratch-simulation-lifecycle").harness
    _seed_live_conjecture(harness)
    prompts: list[str] = []

    simulation_turn = _v6_simulation_turn()
    simulation_turn["simulation_proposals"][0]["input_aliases"] = ["SIM_001"]
    simulation_turn["simulation_proposals"][0]["declared_assumptions"] = [
        (
            "Advisory provenance SCR_001 motivated this discriminating setup; "
            "SCR_001 is not a simulation input or formal premise."
        )
    ]

    def response(prompt: str) -> str:
        prompts.append(prompt)
        if len(prompts) == 1:
            return json.dumps(
                {
                    "scratch_proposal": {
                        "new_blocks": [
                            {
                                "local_key": "NEW_001",
                                "body": {
                                    "content": (
                                        "Invent one provisional mechanism in advisory "
                                        "scratch: delayed feedback may reverse the effect."
                                    ),
                                    "unfinished": (
                                        "Stretch this mechanism with a discriminating "
                                        "simulation before proposing it formally."
                                    ),
                                },
                            }
                        ]
                    }
                }
            )
        if len(prompts) == 2:
            assert "SCR_001" in prompt
            assert "SIM_001" in prompt
            return json.dumps(simulation_turn)
        if len(prompts) == 3:
            assert "SCR_001" in prompt
            assert "SIM_002: recorded simulation result" in prompt
            return json.dumps(
                {
                    "candidates": [
                        {
                            "content": (
                                "A fresh formal delayed-feedback proposal, independently "
                                "stated after the recorded simulation."
                            ),
                            "typicality": 0.19,
                        }
                    ],
                    "scratch_proposal": {
                        "revisions": [
                            {
                                "target_alias": "SCR_001",
                                "body": {
                                    "content": (
                                        "Revised advisory mechanism after the negative "
                                        "simulation: delayed feedback needs a threshold."
                                    ),
                                    "unfinished": (
                                        "Still imaginative scratch, not evidence or formal support."
                                    ),
                                },
                            }
                        ]
                    },
                }
            )
        raise AssertionError("unexpected extra provider dispatch")

    adapter, _endpoint = _live_adapter(harness, manifest, response)

    assert (
        conj(
            harness,
            "pi-live-v6",
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        )
        == []
    )
    scratch_service = ScratchService(harness)
    (original,) = scratch_service.state.blocks.values()
    assert original.provenance.origin == "transactional-scratch-authoring.v1"

    assert (
        conj(
            harness,
            "pi-live-v6",
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        )
        == []
    )
    (proposal,) = harness.capability_state.proposals.values()
    assert proposal.input_aliases == ("SIM_001",)
    assert "SCR_001" in proposal.declared_assumptions[0]
    origin = harness.workflow_state.transaction_work[proposal.originating_work_order_ref]
    (scratch_plan,) = (plan for plan in origin.plans.values() if plan.plan_kind == "scratch")
    (simulation_plan,) = (plan for plan in origin.plans.values() if plan.plan_kind == "simulation")
    (scratch_item,) = scratch_plan.items
    (simulation_item,) = simulation_plan.items
    assert scratch_item.namespace == ContextNamespace.SCRATCH
    assert scratch_item.alias == "SCR_001"
    assert scratch_item.object_ref == original.id
    assert simulation_item.namespace == ContextNamespace.SIMULATION
    assert simulation_item.alias == "SIM_001"
    assert simulation_item.object_ref == "WEIGHT_INPUT"
    assert simulation_item.object_ref != original.id

    scheduler = Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    scheduler.step()
    (package,) = harness.capability_state.result_packages.values()
    package_event_seq = next(
        event.seq for event in harness.log.read() if package.id in event.outputs
    )
    transition = harness.capability_state.transitions[
        harness.capability_state.current_transition_by_request[proposal.id]
    ]
    assert transition.lifecycle == CapabilityLifecycle.RESULT_PACKAGED

    scheduler.step()
    transition = harness.capability_state.transitions[
        harness.capability_state.current_transition_by_request[proposal.id]
    ]
    assert transition.lifecycle == CapabilityLifecycle.CONSUMED
    (consumption,) = harness.capability_state.consumptions.values()
    assert consumption.follow_up_work_order_ref != origin.preparation.id

    blocks = tuple(scratch_service.state.blocks.values())
    revised = next(block for block in blocks if block.revision_of == original.id)
    (fresh_formal,) = harness.state.artifacts.values()
    assert fresh_formal.provenance.event_seq > package_event_seq
    assert revised.instance.seq > package_event_seq
    assert not fresh_formal.interface.refs

    (compiled,) = harness.capability_state.compiled.values()
    compiled_inputs = json.loads(harness.blobs.get(compiled.input_ref))
    assert compiled_inputs[0]["sealed_inputs"] == {"SIM_001": sealed_value}

    scratch_ids = set(scratch_service.state.blocks)
    encoded_inputs = canonical_json(compiled_inputs)
    assert all(scratch_id.encode("utf-8") not in encoded_inputs for scratch_id in scratch_ids)
    assert scratch_ids.isdisjoint(harness.state.artifacts)
    assert scratch_ids.isdisjoint(harness.commitments)
    assert scratch_ids.isdisjoint(harness.warrants)
    assert all(
        scratch_id not in edge
        for scratch_id in scratch_ids
        for edge in (*harness.state.att, *harness.state.dep)
    )
    assert len(prompts) == 3
