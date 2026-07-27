"""Constrained standalone scratch execution and recovery through public paths."""

from __future__ import annotations

import pytest

from deepreason.scratch.authoring import ScratchAuthoringService
from deepreason.scratch.render import ScratchRenderer
from deepreason.scratch.service import ScratchService

from tests.test_v6_scratch_authoring_transactions import (
    _adapter,
    _bind_v6_root,
    _context,
    _invoke,
)


_OPERATIONS = (
    (
        "block",
        "conjecturer",
        "scratch.block.compact.v1",
        "scratch.block.minimal.v1",
        '{"content":"one bounded provisional idea"}',
    ),
    (
        "link",
        "synthesizer",
        "scratch.link.compact.v1",
        "scratch.link.minimal.v1",
        '{"from_index":0,"to_index":1,"relation_hint":"may constrain"}',
    ),
    (
        "guide",
        "summarizer",
        "scratch.cluster-guide.compact.v1",
        "scratch.cluster-guide.minimal.v1",
        '{"working_focus":"compare the two provisional mechanisms"}',
    ),
)


def _provider_contracts(service):
    return tuple(
        event.llm.attempt_trace[0].contract_id
        for event in service.harness.log.read()
        if event.llm is not None
    )


@pytest.mark.parametrize(
    ("operation", "role", "strong_contract", "minimal_contract", "minimal_raw"),
    _OPERATIONS,
)
def test_authorized_minimal_scratch_fallback_is_separate_exact_work(
    tmp_path,
    operation,
    role,
    strong_contract,
    minimal_contract,
    minimal_raw,
):
    root = tmp_path / f"minimal-{operation}"
    manifest = _bind_v6_root(root, grant_ceiling=(strong_contract, 0))
    service = ScratchService(root)
    renderer, rendered, _first, _second, cluster = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {role: ["not-json", minimal_raw]},
    )

    effect = _invoke(
        ScratchAuthoringService(
            service,
            adapter,
            renderer=renderer,
            run_manifest=manifest,
        ),
        operation,
        rendered,
        cluster.id,
    )

    work = tuple(service.harness.workflow_state.transaction_work.values())
    assert tuple(item.preparation.contract_id for item in work) == (
        strong_contract,
        minimal_contract,
    )
    assert tuple(item.terminal.status for item in work) == (
        "schema_exhausted",
        "completed",
    )
    assert work[1].preparation.route_lease == work[0].preparation.route_lease
    assert work[1].preparation.task_payload_value["schema"] == (
        "contract-decomposition-child.v1"
    )
    assert adapter.meter.calls == 2
    assert adapter.meter.reserved == 0
    assert _provider_contracts(service) == (strong_contract, minimal_contract)

    transitions = tuple(
        service.harness.workflow_state.contract_decomposition_by_source_work.values()
    )
    completions = tuple(
        service.harness.workflow_state.
        contract_decomposition_completion_by_transition.values()
    )
    assert len(transitions) == len(completions) == 1
    transition = transitions[0]
    assert transition.source_work_id == work[0].preparation.id
    assert transition.source_contract_id == strong_contract
    assert transition.atomic_contract_id == minimal_contract
    assert transition.child_partition == "scratch_single_object"
    assert completions[0].admitted_effect_refs == (effect.id,)

    calls = tuple(
        event.llm
        for event in service.harness.log.read()
        if event.llm is not None
    )
    assert all(
        service.harness.blobs.get(call.prompt_ref).decode("utf-8").count(rendered.text)
        == 1
        for call in calls
    )
    assert calls[0].attempt_trace[0].model_profile == "standard"
    assert calls[0].attempt_trace[0].transport_profile == "standard"
    assert calls[1].attempt_trace[0].model_profile == "standard"
    assert calls[1].attempt_trace[0].transport_profile == "compact"

    if operation == "block":
        assert effect.body.unfinished is None
        assert effect.body.possible_next_move is None
    elif operation == "link":
        assert effect.body.because is None
        assert effect.body.holds_when is None
        assert effect.body.weakens_when is None
    else:
        assert effect.open_threads is None
        assert effect.entry_points is None
        assert effect.local_summary is None


@pytest.mark.parametrize(
    ("operation", "role", "strong_contract", "minimal_contract", "minimal_raw"),
    _OPERATIONS,
)
def test_minimal_scratch_durable_result_recovers_without_redispatch(
    tmp_path,
    monkeypatch,
    operation,
    role,
    strong_contract,
    minimal_contract,
    minimal_raw,
):
    root = tmp_path / f"minimal-recovery-{operation}"
    manifest = _bind_v6_root(root, grant_ceiling=(strong_contract, 0))
    service = ScratchService(root)
    renderer, rendered, _first, _second, cluster = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {role: ["not-json", minimal_raw]},
    )
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    original_call = author._call

    def crash_after_durable_child(*args, **kwargs):
        result = original_call(*args, **kwargs)
        assert result.preparation.contract_id == minimal_contract
        raise SystemExit("simulated constrained-scratch process loss")

    monkeypatch.setattr(author, "_call", crash_after_durable_child)
    with pytest.raises(SystemExit, match="constrained-scratch process loss"):
        _invoke(author, operation, rendered, cluster.id)

    before = tuple(service.harness.workflow_state.transaction_work.values())
    assert tuple(item.preparation.contract_id for item in before) == (
        strong_contract,
        minimal_contract,
    )
    assert before[0].terminal.status == "schema_exhausted"
    assert before[1].terminal is None
    assert len(before[1].provider_attempts) == 1
    assert adapter.meter.calls == 2

    restarted = ScratchService(root)
    redispatches = []

    def forbidden(prompt):
        redispatches.append(prompt)
        raise AssertionError("durable constrained scratch was redispatched")

    recovery_adapter, _recovery_endpoints = _adapter(
        restarted,
        manifest,
        {role: forbidden},
    )
    recovered = _invoke(
        ScratchAuthoringService(
            restarted,
            recovery_adapter,
            renderer=ScratchRenderer(restarted),
            run_manifest=manifest,
        ),
        operation,
        rendered,
        cluster.id,
    )

    assert redispatches == []
    assert recovery_adapter.meter.calls == 0
    work = tuple(restarted.harness.workflow_state.transaction_work.values())
    assert len(work) == 2
    assert tuple(item.terminal.status for item in work) == (
        "schema_exhausted",
        "completed",
    )
    completions = tuple(
        restarted.harness.workflow_state.
        contract_decomposition_completion_by_transition.values()
    )
    assert len(completions) == 1
    assert completions[0].admitted_effect_refs == (recovered.id,)
    effect_events = tuple(
        event
        for event in restarted.harness.log.read()
        if event.scratch is not None and recovered.id in event.outputs
    )
    assert len(effect_events) == 1


@pytest.mark.parametrize(
    ("operation", "role", "strong_contract", "minimal_contract", "minimal_raw"),
    _OPERATIONS,
)
def test_completed_minimal_effect_finishes_transition_without_redispatch(
    tmp_path,
    monkeypatch,
    operation,
    role,
    strong_contract,
    minimal_contract,
    minimal_raw,
):
    root = tmp_path / f"minimal-completion-recovery-{operation}"
    manifest = _bind_v6_root(root, grant_ceiling=(strong_contract, 0))
    service = ScratchService(root)
    renderer, rendered, _first, _second, cluster = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {role: ["not-json", minimal_raw]},
    )
    author = ScratchAuthoringService(
        service,
        adapter,
        renderer=renderer,
        run_manifest=manifest,
    )
    original_complete = author._complete_decomposition

    def crash_before_completion(*_args, **_kwargs):
        raise SystemExit("simulated post-effect process loss")

    monkeypatch.setattr(author, "_complete_decomposition", crash_before_completion)
    with pytest.raises(SystemExit, match="post-effect process loss"):
        _invoke(author, operation, rendered, cluster.id)
    monkeypatch.setattr(author, "_complete_decomposition", original_complete)

    before = tuple(service.harness.workflow_state.transaction_work.values())
    assert tuple(item.preparation.contract_id for item in before) == (
        strong_contract,
        minimal_contract,
    )
    assert tuple(item.terminal.status for item in before) == (
        "schema_exhausted",
        "completed",
    )
    assert (
        service.harness.workflow_state.
        contract_decomposition_completion_by_transition
        == {}
    )
    admitted_ref = next(
        iter(before[1].admissions.values())
    ).admitted_refs[0]
    assert len(
        [
            event
            for event in service.harness.log.read()
            if event.scratch is not None and admitted_ref in event.outputs
        ]
    ) == 1

    restarted = ScratchService(root)
    redispatches = []

    def forbidden(prompt):
        redispatches.append(prompt)
        raise AssertionError("completed constrained scratch was redispatched")

    recovery_adapter, _recovery_endpoints = _adapter(
        restarted,
        manifest,
        {role: forbidden},
    )
    recovered = _invoke(
        ScratchAuthoringService(
            restarted,
            recovery_adapter,
            renderer=ScratchRenderer(restarted),
            run_manifest=manifest,
        ),
        operation,
        rendered,
        cluster.id,
    )

    assert recovered.id == admitted_ref
    assert redispatches == []
    assert recovery_adapter.meter.calls == 0
    after = tuple(restarted.harness.workflow_state.transaction_work.values())
    assert len(after) == 2
    assert tuple(item.preparation.contract_id for item in after) == (
        strong_contract,
        minimal_contract,
    )
    completions = tuple(
        restarted.harness.workflow_state.
        contract_decomposition_completion_by_transition.values()
    )
    assert len(completions) == 1
    assert completions[0].admitted_effect_refs == (admitted_ref,)
    assert len(
        [
            event
            for event in restarted.harness.log.read()
            if event.scratch is not None and admitted_ref in event.outputs
        ]
    ) == 1
