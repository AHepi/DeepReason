"""Stage B3: manifest-bound scratch context reaches ordinary Conj honestly."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.capture.detection import evidence_lambda, grounding_lambda
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter, SchemaRepairError
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Problem, ProblemProvenance, StateDiff
from deepreason.rules.conj import conj
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    RunManifest,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.scratch.conjecture import (
    ConjectureContextStale,
    PlannedConjectureContextV1,
    commit_conjecture_context,
    plan_conjecture_context,
)
from deepreason.scratch.errors import ScratchReadOnly
from deepreason.scratch.models import ScratchProvenanceV1
from deepreason.scratch.render import ScratchRenderReceiptV1
from deepreason.scratch.service import ScratchService


STAMP = "2026-07-16T00:00:00Z"
PROBLEM_ID = "pi-scratch-context"


def _context_policy(*, mode: str = "harness_only") -> ConjectureContextPolicyV1:
    enabled = mode != "disabled"
    return ConjectureContextPolicyV1(
        mode=mode,
        initial_max_blocks=4 if enabled else 0,
        initial_max_guides=0,
        max_context_expansion_requests=0,
        max_extra_blocks=0,
        permitted_retrieval_channels=(
            ("focus", "keyword", "recent") if enabled else ()
        ),
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )


def _control_policy(
    *, context_mode: str = "harness_only"
) -> ControlPlanePolicyV1:
    return ControlPlanePolicyV1(
        controller_version="workflow.controller.v1",
        mode="active_conjecture",
        workflow_profile="conjecture.active.v1",
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=_context_policy(mode=context_mode),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v2",
            conjecturer_turn_contract="conjecturer.turn.v4",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )


def _config(*, scratch_enabled: bool = True) -> Config:
    return Config(
        N_SCHOOLS=0,
        VS_K=1,
        FLOOR=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        NEAR_DUP_EPS=None,
        RETRY_MAX=0,
        model_profile="standard",
        scratchpad={
            "enabled": scratch_enabled,
            "max_blocks_per_pack": 4,
            "max_guides_per_pack": 0,
            "semantic_retrieval": False,
            "keyword_retrieval": True,
            "coverage_enabled": False,
            "exploratory_fraction": 0.0,
            "underexposed_fraction": 0.0,
        },
        roles={
            "conjecturer": {
                "endpoint_id": "conjecturer-0",
                "endpoint": "mock://conjecturer-0",
                "model": "offline-conjecturer",
                "provider": "mock",
                "family": "offline-family",
                "max_tokens": 512,
            }
        },
    )


def _manifest(
    config: Config,
    *,
    context_mode: str = "harness_only",
) -> RunManifest:
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control_policy(context_mode=context_mode),
    )


def _seed(harness: Harness) -> Problem:
    problem = Problem(
        id=PROBLEM_ID,
        description="Explain why a bounded feedback loop may stabilize the record.",
        provenance=ProblemProvenance.model_validate(
            {"trigger": "seed", "from": []}
        ),
    )
    harness.register_problem(problem)
    return problem


def _relevant_block(service: ScratchService, problem: Problem):
    return service.create_block(
        {
            "content": (
                "A delayed negative feedback loop might stabilize the observed "
                "oscillation, but this abandoned note may be wrong."
            ),
            "unfinished": "Check whether the delay changes sign.",
        },
        ScratchProvenanceV1(
            actor="user",
            origin="b3-test",
            formal_artifact_refs=[problem.id],
        ),
    )


def _plan(
    service: ScratchService,
    manifest: RunManifest,
    problem: Problem,
) -> PlannedConjectureContextV1 | None:
    fence = service.harness._next_seq - 1
    assert manifest.scratch_policy is not None
    assert manifest.control_plane_policy is not None
    return plan_conjecture_context(
        service,
        problem=problem,
        school_id=None,
        manifest_digest=manifest.sha256,
        scratch_policy=manifest.scratch_policy,
        context_policy=manifest.control_plane_policy.conjecture_context,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
    )


def _candidate(*, reference: str | None = None) -> str:
    candidate: dict[str, object] = {
        "content": "A bounded negative-feedback mechanism is a testable candidate.",
        "typicality": 0.4,
    }
    if reference is not None:
        candidate["refs"] = [{"target": reference, "role": "dependence"}]
    return json.dumps({"candidates": [candidate]})


def _adapter(
    harness: Harness,
    responder,
    *,
    retry_max: int = 0,
    manifest: RunManifest | None = None,
) -> tuple[LLMAdapter, MockEndpoint]:
    endpoint = MockEndpoint(
        responder,
        name="mock://conjecturer-0",
        model="offline-conjecturer",
        max_tokens=512,
    )
    return (
        LLMAdapter(
            {"conjecturer": endpoint},
            harness.blobs,
            retry_max=retry_max,
            model_profile="standard",
            leases=(
                leases_from_manifest(manifest) if manifest is not None else None
            ),
        ),
        endpoint,
    )


def _filesystem_snapshot(root: Path) -> dict[str, tuple[int, int]]:
    return {
        str(path.relative_to(root)): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    }


def test_enabled_context_is_exactly_rendered_and_all_receipts_are_durable(tmp_path):
    config = _config()
    manifest = _manifest(config)
    root = tmp_path / "run"
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    problem = _seed(harness)
    service = ScratchService(harness)
    block = _relevant_block(service, problem)

    events_before = list(harness.log.read())
    plan = _plan(service, manifest, problem)
    assert plan is not None
    assert list(harness.log.read()) == events_before  # planning is pure
    assert service.state.attention_receipts == {}
    assert service.state.advisory_contexts == {}
    assert block.id in plan.attention_pack.selection_receipt.final_order

    seen_prompts: list[str] = []

    def respond(prompt: str) -> str:
        seen_prompts.append(prompt)
        return _candidate()

    adapter, _endpoint = _adapter(harness, respond, manifest=manifest)
    admitted = conj(
        harness,
        problem.id,
        adapter,
        config,
        workload_profile="text",
        conjecture_context_plan=plan,
    )
    assert len(admitted) == 1
    assert len(seen_prompts) == 1
    assert seen_prompts[0].count(plan.rendered_context.text) == 1

    warning = plan.advisory_context.warning.casefold()
    for phrase in (
        "non-authoritative",
        "wrong",
        "stale",
        "contradictory",
        "abandoned",
        "does not ground",
        "ignore",
    ):
        assert phrase in warning

    call_event = next(event for event in reversed(list(harness.log.read())) if event.llm)
    receipt = call_event.llm.conjecture_context
    assert receipt is not None
    assert receipt.selection_receipt_ref == plan.attention_pack.selection_receipt.id
    assert receipt.advisory_context_ref == plan.advisory_context.id
    assert service.state.attention_receipts[receipt.selection_receipt_ref] == (
        plan.attention_pack.selection_receipt
    )
    assert service.state.advisory_contexts[receipt.advisory_context_ref] == (
        plan.advisory_context
    )

    render_receipt = ScratchRenderReceiptV1.model_validate_json(
        harness.blobs.get(receipt.render_receipt_ref)
    )
    assert render_receipt == plan.rendered_context.receipt
    assert render_receipt.block_handles == {"B1": block.id}
    assert harness.blobs.get(receipt.rendered_context_ref).decode() == (
        plan.rendered_context.text
    )
    recorded_prompt = harness.blobs.get(call_event.llm.prompt_ref).decode()
    assert recorded_prompt.count(plan.rendered_context.text) == 1

    scratch_actions = [
        (event.seq, event.scratch.action.value)
        for event in harness.log.read()
        if event.scratch is not None
    ]
    assert [action for _seq, action in scratch_actions[-2:]] == [
        "attention_pack_rendered",
        "advisory_context_created",
    ]
    assert scratch_actions[-1][0] < call_event.seq
    assert verify_root(root)["violations"] == []


@pytest.mark.parametrize(
    ("scratch_enabled", "context_mode"),
    ((False, "harness_only"), (True, "disabled")),
)
def test_disabled_context_preserves_exact_legacy_conj_behavior(
    tmp_path,
    scratch_enabled: bool,
    context_mode: str,
):
    config = _config(scratch_enabled=scratch_enabled)
    manifest = _manifest(config, context_mode=context_mode)
    prompts: list[list[str]] = [[], []]
    artifacts = []

    for index in range(2):
        harness = Harness(tmp_path / f"run-{index}")
        problem = _seed(harness)
        service = ScratchService(harness)
        _relevant_block(service, problem)
        plan = _plan(service, manifest, problem) if index else None
        assert plan is None

        def respond(prompt: str, *, slot=index) -> str:
            prompts[slot].append(prompt)
            return _candidate()

        adapter, _endpoint = _adapter(harness, respond)
        kwargs = {"conjecture_context_plan": plan} if index else {}
        admitted = conj(
            harness,
            problem.id,
            adapter,
            config,
            workload_profile="text",
            **kwargs,
        )
        artifacts.append(admitted)
        assert service.state.attention_receipts == {}
        assert service.state.advisory_contexts == {}
        call = next(event.llm for event in harness.log.read() if event.llm)
        assert call.conjecture_context is None

    assert prompts[0] == prompts[1]
    assert artifacts[0] == artifacts[1]


def test_stale_plan_cannot_commit_and_a_fresh_rebuild_can(tmp_path):
    harness = Harness(tmp_path / "run")
    problem = _seed(harness)
    service = ScratchService(harness)
    _relevant_block(service, problem)
    manifest = _manifest(_config())
    stale = _plan(service, manifest, problem)
    assert stale is not None

    harness.record_measure(inputs=["advance-formal-and-scratch-fence"])
    before_failed_commit = _filesystem_snapshot(harness.root)
    with pytest.raises(ConjectureContextStale, match="STALE|stale|fence"):
        commit_conjecture_context(
            service,
            stale,
            final_conjecture_pack="CONJ\n" + stale.rendered_context.text,
            attention_policy=manifest.scratch_policy.attention_policy(),
        )
    assert _filesystem_snapshot(harness.root) == before_failed_commit
    assert stale.attention_pack.selection_receipt.id not in (
        service.state.attention_receipts
    )

    rebuilt = _plan(service, manifest, problem)
    assert rebuilt is not None
    assert rebuilt.formal_fence_seq > stale.formal_fence_seq
    assert rebuilt.scratch_fence_seq > stale.scratch_fence_seq
    committed = commit_conjecture_context(
        service,
        rebuilt,
        final_conjecture_pack="CONJ\n" + rebuilt.rendered_context.text,
        attention_policy=manifest.scratch_policy.attention_policy(),
    )
    assert committed.selection_receipt_ref in service.state.attention_receipts
    assert committed.advisory_context_ref in service.state.advisory_contexts


def test_schema_exhaustion_retains_the_exact_rendered_context_receipt(tmp_path):
    harness = Harness(tmp_path / "run")
    problem = _seed(harness)
    service = ScratchService(harness)
    _relevant_block(service, problem)
    config = _config()
    manifest = _manifest(config)
    plan = _plan(service, manifest, problem)
    assert plan is not None
    adapter, _endpoint = _adapter(harness, lambda _prompt: "not-json")

    with pytest.raises(SchemaRepairError) as exhausted:
        conj(
            harness,
            problem.id,
            adapter,
            config,
            workload_profile="text",
            conjecture_context_plan=plan,
        )
    spend = exhausted.value.spend
    assert spend is not None
    assert spend.conjecture_context is not None
    assert spend.conjecture_context.selection_receipt_ref in (
        service.state.attention_receipts
    )
    assert spend.conjecture_context.advisory_context_ref in (
        service.state.advisory_contexts
    )
    initial_prompt = harness.blobs.get(spend.attempt_trace[0].prompt_ref).decode()
    rendered = harness.blobs.get(
        spend.conjecture_context.rendered_context_ref
    ).decode()
    assert rendered == plan.rendered_context.text
    assert initial_prompt.count(rendered) == 1
    assert ScratchRenderReceiptV1.model_validate_json(
        harness.blobs.get(spend.conjecture_context.render_receipt_ref)
    ) == plan.rendered_context.receipt

    harness.record_llm_calls([spend], "dropped-call", str(exhausted.value))
    durable = list(harness.log.read())[-1]
    assert durable.llm is not None
    assert durable.llm.conjecture_context == spend.conjecture_context
    assert durable.inputs[0] == "dropped-call"


def test_scratch_handles_never_enter_formal_state_or_grounding(tmp_path):
    harness = Harness(tmp_path / "run")
    problem = _seed(harness)
    service = ScratchService(harness)
    block = _relevant_block(service, problem)
    config = _config()
    manifest = _manifest(config)
    plan = _plan(service, manifest, problem)
    assert plan is not None
    adapter, _endpoint = _adapter(harness, lambda _prompt: _candidate(reference="B1"))
    grounding_before = grounding_lambda(harness, 100)
    evidence_before = evidence_lambda(harness)

    admitted = conj(
        harness,
        problem.id,
        adapter,
        config,
        workload_profile="text",
        conjecture_context_plan=plan,
    )
    assert len(admitted) == 1
    artifact = admitted[0]
    assert artifact.interface.refs == []
    assert artifact.warrants == []
    assert harness.warrants == {}
    assert grounding_lambda(harness, 100) == grounding_before == 1.0
    assert evidence_lambda(harness) is evidence_before is None

    forbidden = {
        "B1",
        block.id,
        plan.attention_pack.selection_receipt.id,
        plan.advisory_context.id,
        plan.rendered_context.receipt.receipt_hash,
    }
    for event in harness.log.read():
        if event.scratch is not None:
            assert event.state_diff == StateDiff()
        formal_diff = json.dumps(
            event.state_diff.model_dump(mode="json", by_alias=True),
            sort_keys=True,
        )
        assert not any(value in formal_diff for value in forbidden)
    artifact_formal = json.dumps(artifact.interface.model_dump(mode="json"))
    assert not any(value in artifact_formal for value in forbidden)


def test_historical_views_can_neither_plan_nor_commit_context(tmp_path):
    root = tmp_path / "run"
    live = Harness(root)
    problem = _seed(live)
    live_service = ScratchService(live)
    _relevant_block(live_service, problem)
    manifest = _manifest(_config())
    live_plan = _plan(live_service, manifest, problem)
    assert live_plan is not None

    fence = live._next_seq - 1
    historical = Harness.at(root, fence)
    service = ScratchService(historical)
    before = _filesystem_snapshot(root)
    assert manifest.scratch_policy is not None
    assert manifest.control_plane_policy is not None
    with pytest.raises(ScratchReadOnly, match="historical|read.only"):
        plan_conjecture_context(
            service,
            problem=problem,
            school_id=None,
            manifest_digest=manifest.sha256,
            scratch_policy=manifest.scratch_policy,
            context_policy=manifest.control_plane_policy.conjecture_context,
            formal_fence_seq=fence,
            scratch_fence_seq=fence,
        )
    with pytest.raises(ScratchReadOnly, match="historical|read.only"):
        commit_conjecture_context(
            service,
            live_plan,
            final_conjecture_pack="CONJ\n" + live_plan.rendered_context.text,
            attention_policy=manifest.scratch_policy.attention_policy(),
        )
    assert _filesystem_snapshot(root) == before
