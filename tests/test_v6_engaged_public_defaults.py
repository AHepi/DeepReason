"""The engaged public preset: scratch ON and semantic criticism actually runs.

Three seams are pinned here:

1. The compiled public manifest (`build_preparation_manifest`) enables the
   advisory scratchpad and carries a complete foreign-school criticism
   policy binding every seeded public school to the single provider seat.
2. Behavior-level, with mock endpoints: a public-preset v6 run dispatches at
   least one school-routed criticism work order and records durable coverage.
3. Behavior-level: the public preset's scratch-authoring authority admits a
   bounded advisory proposal without touching formal state.
"""

from __future__ import annotations

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Provenance, Status
from deepreason.preparation import build_preparation_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.run_manifest import compile_run_manifest
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
    engaged_control_plane_policy_v3,
    engaged_criticism_policy,
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


def test_public_manifest_enables_scratch_and_binds_all_four_schools():
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
        EMBEDDER_MODEL=None,
        roles={
            "conjecturer": [_route("conjecturer-route")],
            "argumentative_critic": [_route("critic-route-0")],
            "synthesizer": [_route("synthesizer-route")],
            "summarizer": [_route("summarizer-route")],
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
        run_input_digest="f" * 64,
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
