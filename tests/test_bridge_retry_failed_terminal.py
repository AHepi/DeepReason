"""Owner decision 4b: an explicit operator intent retries a process-failed
bridge terminal as a typed continuation of the recorded retry chain.

A completed epistemic resolution is permanent. A process failure — a crash,
a stage failure, a harness defect fixed after the fact — may be retried,
but only explicitly, only additively (the failed attempt stays in the
append-only log, bridged by a WORKFLOW_RETRY_STARTED receipt derived from
replayed state), and only under the frozen execution fence the failed
attempt already held.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deepreason.application.bridge import (
    GroundedBridgeBuildIntentV1,
    load_snapshot,
)
from deepreason.bridge.events import BridgeAction
from deepreason.harness import Harness
from deepreason.run_manifest import WorkflowRetryPolicyV1
from deepreason.runtime.terminal_authority import derive_terminal_authority
from deepreason.verification.report import verify_root_report
from tests.test_v6_bridge_transactions import (
    _bind_recovery_manifest,
    _recovery_adapter,
    _recovery_policy,
    _recovery_responses,
    _seed_recovery_problem,
)


def _build(harness, manifest, problem_id, adapter, *, retry=False):
    return harness.build_bridge(
        problem_id,
        "answer",
        _recovery_policy(manifest),
        run_manifest_digest=manifest.sha256,
        stage_a_adapter=adapter,
        composition_adapter=adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
        retry_failed_terminal=retry,
    )


def _failed_root(tmp_path, name="retry-root"):
    root = tmp_path / name
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    adapter = _recovery_adapter(
        harness, manifest, (("summarizer", "{not-json"),), []
    )
    terminal = _build(harness, manifest, problem_id, adapter)
    assert terminal.process_status == "failure"
    assert terminal.error_code == "BRIDGE_STAGE_A_FAILED"
    return root, manifest, problem_id, terminal


def _bridge_actions(root):
    return [
        event.bridge.action
        for event in Harness(root, read_only=True).log.read()
        if event.bridge is not None
    ]


def test_failed_terminal_stays_idempotent_without_the_flag(tmp_path):
    root, manifest, problem_id, terminal = _failed_root(tmp_path)
    harness = Harness(root)
    dispatches = []
    adapter = _recovery_adapter(harness, manifest, _recovery_responses(), dispatches)

    served = _build(harness, manifest, problem_id, adapter)

    assert served == terminal
    assert dispatches == []


def test_operator_retry_reruns_a_failed_terminal_to_completion(tmp_path):
    root, manifest, problem_id, failed = _failed_root(tmp_path)
    harness = Harness(root)
    dispatches = []
    adapter = _recovery_adapter(harness, manifest, _recovery_responses(), dispatches)

    terminal = _build(harness, manifest, problem_id, adapter, retry=True)

    assert terminal.process_status == "success"
    assert dispatches  # a genuinely fresh attempt, not a replay
    assert terminal.terminal_event_seq > failed.terminal_event_seq

    # The record keeps the failure, the typed retry, and the fresh attempt.
    actions = _bridge_actions(root)
    assert actions[: 2] == [BridgeAction.FAILED, BridgeAction.WORKFLOW_RETRY_STARTED]
    assert actions[-1] == BridgeAction.COMPLETED
    replayed = Harness(root, read_only=True)
    assert failed.failure_id in replayed.bridge_state.failures
    (retry,) = replayed.bridge_state.workflow_retries.values()
    assert retry.prior_failure_id == failed.failure_id
    assert retry.attempt_number == 2

    # Root authority, verification, and the result snapshot all stay valid.
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    report = verify_root_report(root)
    assert report.integrity_valid and report.security_valid
    assert load_snapshot(root).terminal == terminal

    # Idempotence resumes on the new terminal, which is now permanent.
    idle = Harness(root)
    idle_adapter = _recovery_adapter(idle, manifest, (), [])
    assert _build(idle, manifest, problem_id, idle_adapter) == terminal
    with pytest.raises(ValueError, match="BRIDGE_RETRY_TERMINAL_NOT_FAILED"):
        _build(idle, manifest, problem_id, idle_adapter, retry=True)


def test_operator_retry_chain_survives_a_second_failure(tmp_path):
    root, manifest, problem_id, first = _failed_root(tmp_path)

    second_harness = Harness(root)
    second_adapter = _recovery_adapter(
        second_harness,
        manifest,
        # Distinct garbage: bridge failures are content-addressed, so an
        # identical re-failure reuses the same failure object; the chain
        # test wants a genuinely new failure.
        (("summarizer", "{worse-json"), ("summarizer", "{worse-json")),
        [],
    )
    second = _build(second_harness, manifest, problem_id, second_adapter, retry=True)
    assert second.process_status == "failure"
    assert second.failure_id != first.failure_id

    third_harness = Harness(root)
    dispatches = []
    third_adapter = _recovery_adapter(
        third_harness, manifest, _recovery_responses(), dispatches
    )
    third = _build(third_harness, manifest, problem_id, third_adapter, retry=True)

    # The second operator retry is chain-legal (attempt 3 of at most 3), but
    # operator authority never overrides frozen provider-capability facts:
    # two schema exhaustions terminally exhausted the ledger route seat, so
    # the fresh attempt resolves as a typed capability refusal — recorded,
    # never silent — without a single new dispatch.
    assert third.process_status == "failure"
    assert third.error_code == "V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY"
    assert third.failure_id != second.failure_id
    assert dispatches == []
    replayed = Harness(root, read_only=True)
    retries = sorted(
        replayed.bridge_state.workflow_retries.values(),
        key=lambda retry: retry.attempt_number,
    )
    assert [retry.attempt_number for retry in retries] == [2, 3]
    assert retries[1].prior_failure_id == second.failure_id
    assert retries[1].prior_retry_id == retries[0].id
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    report = verify_root_report(root)
    assert report.integrity_valid and report.security_valid


def test_operator_retry_requires_an_existing_failed_terminal(tmp_path):
    root = tmp_path / "no-terminal"
    manifest = _bind_recovery_manifest(root, WorkflowRetryPolicyV1())
    harness = Harness(root)
    problem_id = _seed_recovery_problem(harness)
    adapter = _recovery_adapter(harness, manifest, _recovery_responses(), [])

    with pytest.raises(ValueError, match="BRIDGE_RETRY_TERMINAL_ABSENT"):
        _build(harness, manifest, problem_id, adapter, retry=True)


def test_retry_intent_rejects_derived_destinations():
    with pytest.raises(ValidationError, match="BRIDGE_RETRY_DERIVED_UNSUPPORTED"):
        GroundedBridgeBuildIntentV1(
            root="/run",
            problem="problem-id",
            run_manifest_ref="/manifest",
            derived_output="/derived",
            at_seq=5,
            retry_failed_terminal=True,
        )


def test_completed_terminal_is_superseded_when_the_commitment_advances(tmp_path):
    """No answer is final: a stored bridge terminal is served idempotently
    only while the run's terminal commitment still matches its fence. Once a
    continuation opens a new terminal epoch, the stored terminal is history
    and a fresh view composes at the current fence."""

    from deepreason.bridge.harness import _read_existing_bridge_terminal

    root, manifest, problem_id, _failed = _failed_root(tmp_path)
    harness = Harness(root)
    adapter = _recovery_adapter(harness, manifest, _recovery_responses(), [])
    terminal = _build(harness, manifest, problem_id, adapter, retry=True)
    assert terminal.process_status == "success"
    fence_commitment = terminal.source_terminal_commitment_ref
    assert fence_commitment is not None

    reader = Harness(root, read_only=True)
    served = _read_existing_bridge_terminal(
        reader,
        manifest_digest=manifest.sha256,
        problem_id=problem_id,
        target="answer",
        source_run_digest=None,
        source_terminal_commitment_ref=fence_commitment,
    )
    assert served == terminal

    advanced = "sha256:" + "e" * 64
    superseded = _read_existing_bridge_terminal(
        reader,
        manifest_digest=manifest.sha256,
        problem_id=problem_id,
        target="answer",
        source_run_digest=None,
        source_terminal_commitment_ref=advanced,
    )
    assert superseded is None  # fresh compose authorized at the new fence

    with pytest.raises(ValueError, match="BRIDGE_RESULT_AUTHORITY_MISMATCH"):
        _read_existing_bridge_terminal(
            reader,
            manifest_digest=manifest.sha256,
            problem_id="another-problem",
            target="answer",
            source_run_digest=None,
            source_terminal_commitment_ref=fence_commitment,
        )
