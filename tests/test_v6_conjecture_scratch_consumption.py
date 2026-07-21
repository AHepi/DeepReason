"""V6 conjecture consumes canonical advisory scratch exactly once."""

from __future__ import annotations

import json

import pytest

import deepreason.scratch.conjecture as conjecture_context
from deepreason.harness import Harness
from deepreason.rules.conj import conj
from deepreason.scratch.conjecture import plan_conjecture_context
from deepreason.scratch.models import RetrievalChannel, ScratchProvenanceV1
from deepreason.scratch.render import ScratchRenderReceiptV1
from deepreason.scratch.service import ScratchService
from deepreason.workflow.conjecture_recovery import (
    ConjectureRecoveryAuthorityError,
)
from tests.test_v6_context_continuation import (
    _abstention,
    _adapter,
    _config,
    _manifest,
    _run,
    _seed,
)
from tests.test_v6_transaction_qualification import (
    _config as _disabled_config,
    _live_adapter,
    _manifest as _disabled_manifest,
    _scratch_context_config_and_manifest,
    _seed_live_conjecture,
)


def _scratch_events(harness: Harness, action: str):
    return [
        event
        for event in harness.log.read()
        if event.scratch is not None and event.scratch.action.value == action
    ]


def test_initial_v6_conjecture_commits_exact_model_facing_scratch_once(tmp_path):
    config = _config()
    manifest = _manifest(config)
    harness = Harness(tmp_path / "initial")
    _problem, focus, _expansion, _tertiary = _seed(harness)
    adapter, prompts = _adapter(harness, manifest, [_abstention()])

    assert _run(harness, manifest, config, adapter) == []

    (work,) = harness.workflow_state.transaction_work.values()
    (call,) = [event.llm for event in harness.log.read() if event.llm is not None]
    receipt = call.conjecture_context
    assert receipt is not None
    rendered = harness.blobs.get(receipt.rendered_context_ref).decode("utf-8")
    prompt = harness.blobs.get(call.prompt_ref).decode("utf-8")
    assert prompt == prompts[0]
    assert prompt.count(rendered) == 1
    assert '"handle":"SCR_001"' in rendered
    assert '"handle":"B1"' not in rendered

    scratch_exposure = {
        item.alias: item.object_ref
        for item in work.exposure.exposed_items
        if item.namespace.value == "scratch"
    }
    assert scratch_exposure == {"SCR_001": focus.id}
    service = ScratchService(harness)
    selection = service.state.attention_receipts[receipt.selection_receipt_ref]
    advisory = service.state.advisory_contexts[receipt.advisory_context_ref]
    render_receipt = ScratchRenderReceiptV1.model_validate_json(
        harness.blobs.get(receipt.render_receipt_ref)
    )
    assert selection.final_order == [focus.id]
    assert advisory.retrieval_receipt == selection.id
    assert render_receipt.attention_receipt == selection.id
    assert tuple(render_receipt.block_handles.values()) == (focus.id,)
    assert service.state.visibility[focus.id].render_count == 1
    assert service.state.visibility[focus.id].contexts_rendered_into == [selection.id]
    assert len(_scratch_events(harness, "attention_pack_rendered")) == 1
    assert len(_scratch_events(harness, "advisory_context_created")) == 1

    attention_before = dict(service.state.attention_receipts)
    advisory_before = dict(service.state.advisory_contexts)
    visibility_before = dict(service.state.visibility)
    coverage_before = dict(service.state.coverage_cycles)
    reopened_service = ScratchService(Harness(harness.root))
    assert reopened_service.state.attention_receipts == attention_before
    assert reopened_service.state.advisory_contexts == advisory_before
    assert reopened_service.state.visibility == visibility_before
    assert reopened_service.state.coverage_cycles == coverage_before


def test_disabled_v6_context_does_not_mutate_scratch_or_prompt(tmp_path):
    config = _disabled_config()
    manifest = _disabled_manifest()
    harness = Harness(tmp_path / "disabled")
    _seed_live_conjecture(harness)
    ScratchService(harness).create_block(
        {"content": "Advisory material must remain hidden while context is disabled."},
        ScratchProvenanceV1(actor="user", origin="disabled-context-test"),
    )
    before = tuple(harness.log.read())
    adapter, _endpoint = _live_adapter(
        harness,
        manifest,
        [json.dumps(_abstention())],
    )

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

    (call,) = [event.llm for event in harness.log.read() if event.llm is not None]
    assert call.conjecture_context is None
    work, = harness.workflow_state.transaction_work.values()
    assert not [
        item
        for item in work.exposure.exposed_items
        if item.namespace.value == "scratch"
    ]
    service = ScratchService(harness)
    assert service.state.attention_receipts == {}
    assert service.state.advisory_contexts == {}
    assert service.state.visibility == {}
    assert not any(
        event.scratch is not None
        and event.scratch.action.value
        in {"attention_pack_rendered", "advisory_context_created"}
        for event in tuple(harness.log.read())[len(before) :]
    )


def test_initial_v6_conjecture_advances_applicable_coverage_once(tmp_path):
    config, manifest = _scratch_context_config_and_manifest(coverage=True)
    harness = Harness(tmp_path / "coverage")
    _seed_live_conjecture(harness)
    service = ScratchService(harness)
    block = service.create_block(
        {"content": "One advisory fragment occupies the active coverage slot."},
        ScratchProvenanceV1(
            actor="user",
            origin="v6-coverage-test",
            formal_artifact_refs=["pi-live-v6"],
        ),
    )
    cycle = service.start_coverage_cycle()
    problem = harness.state.problems["pi-live-v6"]
    fence = harness._next_seq - 1
    events_before_plan = tuple(harness.log.read())
    planned = plan_conjecture_context(
        service,
        problem=problem,
        school_id=None,
        manifest_digest=manifest.sha256,
        scratch_policy=manifest.scratch_policy,
        context_policy=manifest.control_plane_policy.conjecture_context,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
    )
    assert planned is not None
    assert tuple(harness.log.read()) == events_before_plan

    adapter, _endpoint = _live_adapter(
        harness,
        manifest,
        [json.dumps(_abstention())],
    )
    assert (
        conj(
            harness,
            problem.id,
            adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        )
        == []
    )

    (call,) = [event.llm for event in harness.log.read() if event.llm is not None]
    receipt = call.conjecture_context
    assert receipt is not None
    selection = service.state.attention_receipts[receipt.selection_receipt_ref]
    assert selection.selected_by_channel[RetrievalChannel.COVERAGE] == [block.id]
    assert service.state.coverage_cycles[cycle.id].completed
    assert len(_scratch_events(harness, "coverage_block_rendered")) == 1
    assert len(_scratch_events(harness, "coverage_cycle_completed")) == 1
    coverage_before = dict(service.state.coverage_cycles)
    reopened = ScratchService(Harness(harness.root))
    assert reopened.state.coverage_cycles == coverage_before


def test_recovery_rejects_scratch_exposure_without_durable_context_authority(
    tmp_path,
    monkeypatch,
):
    config = _config()
    manifest = _manifest(config)
    root = tmp_path / "missing-context-authority"
    harness = Harness(root)
    _seed(harness)
    adapter, _prompts = _adapter(
        harness,
        manifest,
        [
            {
                "candidates": [
                    {
                        "content": "A bounded candidate used to reach admission.",
                        "typicality": 0.2,
                    }
                ]
            }
        ],
    )
    original_register_batch = harness.register_batch

    def crash_before_semantic_effect(*args, **kwargs):
        if kwargs.get("process_inputs"):
            raise OSError("injected crash after durable provider result")
        return original_register_batch(*args, **kwargs)

    monkeypatch.setattr(harness, "register_batch", crash_before_semantic_effect)
    with pytest.raises(OSError, match="after durable provider result"):
        _run(harness, manifest, config, adapter)

    crashed = Harness(root)
    original_read = crashed.log.read
    durable_events = tuple(original_read())
    assert any(event.llm and event.llm.conjecture_context for event in durable_events)

    def without_context_authority():
        return iter(
            event.model_copy(
                update={
                    "llm": event.llm.model_copy(update={"conjecture_context": None})
                }
            )
            if event.llm is not None
            else event
            for event in durable_events
        )

    monkeypatch.setattr(crashed.log, "read", without_context_authority)
    recovery_adapter, recovery_prompts = _adapter(crashed, manifest, [])
    from deepreason.scheduler.scheduler import Scheduler

    with pytest.raises(
        ConjectureRecoveryAuthorityError,
        match="no conjecture context authority",
    ):
        Scheduler(
            crashed,
            recovery_adapter,
            config,
            workload_profile="text",
            run_manifest=manifest,
        ).run(0)
    assert recovery_prompts == []


def test_context_commit_failure_abandons_prepared_work_before_dispatch(
    tmp_path,
    monkeypatch,
):
    config = _config()
    manifest = _manifest(config)
    harness = Harness(tmp_path / "commit-failure")
    _seed(harness)
    adapter, prompts = _adapter(harness, manifest, [_abstention()])

    def reject_commit(*_args, **_kwargs):
        raise ValueError("injected canonical context validation failure")

    monkeypatch.setattr(
        conjecture_context,
        "commit_conjecture_context",
        reject_commit,
    )
    with pytest.raises(ValueError, match="context validation failure"):
        _run(harness, manifest, config, adapter)

    (work,) = harness.workflow_state.transaction_work.values()
    assert work.terminal.status == "abandoned"
    assert work.terminal.reason_code == "conjecture_context_preissue_failed"
    assert (work.terminal.prompt_tokens, work.terminal.completion_tokens) == (0, 0)
    assert work.reservation is None
    assert work.exposure is None
    assert work.authorization is None
    assert work.provider_attempts == {}
    assert prompts == []
    assert adapter.meter.snapshot()["reserved"] == 0
    assert not any(event.llm is not None for event in harness.log.read())
