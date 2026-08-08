"""Regression (Rung L1, 2026-08-08): deepreason continue must never crash
resuming a run that ever decomposed a criticism batch into atomic
children.

S6 PARKED P3 / D1 PARKED P2: the crash-interrupted-work recovery sweep
(``Scheduler._recover_workflow_prefixes``) re-checked every admitted
criticism work item -- including atomic decomposition children that
were ALREADY fully resolved -- and routed every one of them through
``_criticism_contract``, a handler built only for the BATCH payload
shape (``"criticism.semantic-task.v1"``). An atomic child's own
payload schema (``"contract-decomposition-child.v1"``) failed that
handler's very first authority check, raising
``NonConjectureRecoveryAuthorityError("unknown critic task")`` and
terminalizing the run as ``state="failed"``,
``stop_reason="operational_failure"`` -- reproduced against the
committed fixture ``experiments/2026-08-08-live-two-seat-ab-s6/
home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949`` in
this tranche's own ``REPRO.md``.
"""

import shutil
from pathlib import Path

import pytest

from deepreason.canonical import canonical_json
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.llm.wire import AliasTable, AtomicCriticWireContractV1
from deepreason.ontology import Provenance
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
from deepreason.runtime.stop import StopController, StopPolicy
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.models import WorkflowTaskKind
from deepreason.workflow.nonconjecture_recovery import (
    NonConjectureRecoveryAuthorityError,
    recover_nonconjecture_admission,
)
from deepreason.workflow.transaction_service import InquiryTransactionService

from tests.test_v6_nonconjecture_recovery import _manifest, _provider_prefix

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "2026-08-08-live-two-seat-ab-s6"
    / "home-s6"
    / "runs"
    / "failed-epoch1-run-8c77c6588485304d1f73416318c62949"
)


def _decomposed_atomic_child(root, manifest, *, terminalize):
    """Build one criticism atomic decomposition child through the
    harness's own real seams -- a schema-exhausted batch source item,
    a genuine ``activate_contract_decomposition`` transition (the
    harness's own write-time replay validator refuses an atomic-child
    preparation without one), then one atomic child shaped exactly as
    ``rules/crit.py``'s ``execute_atomic_transition`` builds it.
    ``terminalize=False`` leaves it in the genuine crash window this
    tranche's fix must also cover: admitted, not yet terminal."""
    harness = Harness(root)
    target = harness.create_artifact(
        "one school-owned target",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    source_payload = {
        "schema": "criticism.semantic-task.v1",
        "critic_school_id": "school-1",
        "target_ids": [target.id],
        "assignment_refs": [],
        "coverage_attempt_index": 0,
        "phase": "qualification",
        "caller_trigger_ref": None,
    }
    source_preparation, source_provider = _provider_prefix(
        harness,
        manifest,
        task_kind=WorkflowTaskKind.CRITICISM,
        role="argumentative_critic",
        seat=1,
        contract_id="batch-critic.v2",
        payload=source_payload,
        trigger_prefix="criticism:",
        raw=b"not valid json",
        target_refs=(target.id,),
    )
    reopened = Harness(root)
    transaction = InquiryTransactionService(reopened, manifest, TokenMeter(100_000))
    source_admission = transaction.record_semantic_admission(
        source_provider, outcome="schema_exhausted"
    )
    transaction.terminate(
        work_id=source_provider.work_id,
        attempt_index=source_provider.attempt_index,
        status="schema_exhausted",
        reason_code="recovered_criticism_schema_exhausted",
        usage_status="exact",
        prompt_tokens=source_provider.prompt_tokens,
        completion_tokens=source_provider.completion_tokens,
        provider_attempt=source_provider,
        admission=source_admission,
    )

    reopened = Harness(root)
    transition = reopened.activate_contract_decomposition(
        manifest,
        source_preparation.id,
        child_contexts=((target.id, "one bounded atomic critic pack"),),
    )
    child_payload = {
        "schema": "contract-decomposition-child.v1",
        "decomposition_transition_ref": transition.id,
        "source_work_id": transition.source_work_id,
        "source_contract_id": transition.source_contract_id,
        "atomic_contract_id": transition.atomic_contract_id,
        "child_partition": transition.child_partition,
        "child_index": 0,
        "child_count": 1,
        "child_key": target.id,
        "critic_school_id": "school-1",
    }
    raw_output = b'{"target_alias":"SRC_001","attack":false,"claim":"a recovered atomic child"}'
    child_preparation, child_provider = _provider_prefix(
        reopened,
        manifest,
        task_kind=WorkflowTaskKind.CRITICISM,
        role="argumentative_critic",
        seat=1,
        contract_id=transition.atomic_contract_id,
        payload=child_payload,
        trigger_prefix="decomposition-child:",
        raw=raw_output,
        target_refs=(target.id,),
        input_refs=(
            transition.source_work_id,
            transition.id,
            transition.child_context_refs[0],
            target.id,
        ),
    )

    reopened = Harness(root)
    contract = AtomicCriticWireContractV1(
        AliasTable({"SRC_001": target.id}), expected_target=target.id
    )
    output = contract.parse_compile(raw_output.decode("utf-8"))
    admitted_ref = reopened.blobs.put(
        canonical_json(output.model_dump(mode="json", exclude_none=True))
    )
    transaction = InquiryTransactionService(reopened, manifest, TokenMeter(100_000))
    admission = transaction.record_semantic_admission(
        child_provider, outcome="admitted", admitted_refs=(admitted_ref,)
    )
    if terminalize:
        transaction.terminate(
            work_id=child_provider.work_id,
            attempt_index=child_provider.attempt_index,
            status="completed",
            reason_code="atomic_critic_output_admitted",
            usage_status="exact",
            prompt_tokens=child_provider.prompt_tokens,
            completion_tokens=child_provider.completion_tokens,
            provider_attempt=child_provider,
            admission=admission,
        )
        # else: deliberately no terminate() -- the genuine crash window
        # is admitted, not yet terminal.

    return Harness(root), child_preparation, child_provider


def test_already_resolved_atomic_child_recovers_as_clean_noop(tmp_path):
    """Regression (Rung L1): an atomic criticism decomposition child that
    already reached a terminal record must not be re-swept through the
    batch-only ``_criticism_contract`` handler -- ``recover_nonconjecture_
    admission`` now recognizes it and returns the existing admission
    untouched, with no redispatch."""
    _config, manifest = _manifest()
    reopened, preparation, provider = _decomposed_atomic_child(
        tmp_path / "already-resolved", manifest, terminalize=True
    )
    before = tuple(reopened.log.read())
    admission = recover_nonconjecture_admission(
        reopened, manifest, TokenMeter(100_000), provider
    )
    after = tuple(reopened.log.read())
    assert after == before
    assert admission is not None and admission.outcome == "admitted"
    item = reopened.workflow_state.transaction_work[preparation.id]
    assert item.terminal is not None and item.terminal.status == "completed"


def test_still_open_atomic_child_refuses_with_one_consistent_typed_reason(tmp_path):
    """Regression (Rung L1): a genuinely still-open atomic criticism
    decomposition child (admitted, not yet terminal -- the crash window
    between ``record_semantic_admission`` and ``terminate``) refuses
    with ONE consistent, actionable typed reason, never the misleading
    ``"unknown critic task"`` ``_criticism_contract`` would have
    raised for a shape it was never built to recognize."""
    _config, manifest = _manifest()
    reopened, preparation, provider = _decomposed_atomic_child(
        tmp_path / "still-open", manifest, terminalize=False
    )
    with pytest.raises(
        NonConjectureRecoveryAuthorityError,
        match="atomic criticism decomposition child recovery is not supported",
    ):
        recover_nonconjecture_admission(reopened, manifest, TokenMeter(100_000), provider)
    item = reopened.workflow_state.transaction_work[preparation.id]
    assert item.terminal is None


def _load_fixture_scheduler(root):
    """Build a Scheduler over a fixture copy with a mock endpoint that
    raises if ever dispatched -- proving crash-recovery never
    redispatches a durable result, matching REPRO.md's own form-1
    artifact. Mirrors ops.py's own stop_controller construction for a
    resumed run -- Scheduler.run() requires one bound before it will
    rehydrate a RESUMED root's deterministic stop window."""
    manifest = load_run_manifest(root / MANIFEST_NAME)
    stop_controller = StopController(
        StopPolicy.model_validate(getattr(manifest, "stop_policy", None) or {})
    )

    def forbidden(prompt: str) -> str:
        raise AssertionError("recovery redispatched a durable result")

    endpoints = {
        role: [
            MockEndpoint(forbidden, name=route.base_url, model=route.model_id)
            for route in routes
        ]
        for role, routes in manifest.roles.items()
    }
    config = Config(
        roles={
            role: [
                {
                    "endpoint_id": route.endpoint_id,
                    "endpoint": route.base_url,
                    "model": route.model_id,
                    "provider": route.provider,
                    "family": route.family,
                    "max_tokens": route.max_tokens,
                    "context_window_tokens": route.context_window_tokens,
                }
                for route in routes
            ]
            for role, routes in manifest.roles.items()
        }
    )
    harness = Harness(root)
    adapter = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(1_000_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    return Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
        stop_controller=stop_controller,
    )


def test_committed_fixture_replays_without_crashing(tmp_path):
    """Regression (Rung L1, S6 PARKED P3 / D1 PARKED P2): the real
    committed crash-reproduction fixture no longer crashes on
    ``Scheduler.run(0)``'s crash-interrupted-work recovery sweep.
    Copy only -- the committed root itself stays byte-frozen."""
    copy = tmp_path / FIXTURE.name
    shutil.copytree(FIXTURE, copy)

    _load_fixture_scheduler(copy).run(0)  # must not raise

    item = Harness(copy, read_only=True).workflow_state.transaction_work[
        "sha256:82f77c869e6996b8b60a3d3a37b07226785a19cf9b7978d5805cd4a2c17f17f9"
    ]
    assert item.terminal is not None and item.terminal.status == "completed"
