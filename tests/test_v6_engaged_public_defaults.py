"""The engaged public preset: scratch, criticism, and the grounded bridge run.

Four seams are pinned here:

1. The compiled public manifest (`build_preparation_manifest`) enables the
   advisory scratchpad, carries a complete foreign-school criticism policy
   binding every seeded public school to the single provider seat, and
   compiles the review-free grounded two-stage bridge with both frozen
   bridge roles seated on the single provider endpoint.
2. Behavior-level, with mock endpoints: a public-preset v6 run dispatches at
   least one school-routed criticism work order and records durable coverage.
3. Behavior-level: the public preset's scratch-authoring authority admits a
   bounded advisory proposal without touching formal state.
4. Behavior-level, with mock endpoints: a public-preset run root accepts MCP
   ``start_bridge`` and reaches the completed bridge terminal.
"""

from __future__ import annotations

import json

from deepreason import mcp_scratch_bridge as mcp
from deepreason.bridge.events import BridgeAction
from deepreason.config import Config
from deepreason.evidence import bind_run_input
from deepreason.harness import Harness
from deepreason.llm import adapter as adapter_module
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Problem, ProblemProvenance, Provenance, Status
from deepreason.preparation import _records_for_question, build_preparation_manifest
from deepreason.provider_profile import ProviderProfileV1
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
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
    assert bridge.grounding_review is False
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

    # The review-free public bridge makes exactly two provider calls: the
    # frozen summarizer builds the claim ledger, then the frozen thesis
    # route composes the grounded output.  Every canonical role rides one
    # endpoint, so a single ordered script serves both dispatches.
    responses = [
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
    # Review-free means exactly the two scripted stage calls, no more.
    assert dispatched == [profile.endpoint_id, profile.endpoint_id]
    assert responses == []
    actions = [
        event.bridge.action
        for event in Harness(root, read_only=True).log.read()
        if event.bridge is not None
    ]
    assert actions[-1] == BridgeAction.COMPLETED
