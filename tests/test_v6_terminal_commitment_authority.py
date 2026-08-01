"""Gate T1: root-local first-terminal authority and epoch replay."""

from __future__ import annotations

from copy import deepcopy
import json
import multiprocessing
import queue
import threading

import pytest

from deepreason.application.models import derive_model_execution_summary
from deepreason.application import InspectTextRunIntentV1
from deepreason.application.bridge import preflight_canonical_bridge
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
    _v6_run_result,
)
from deepreason.bridge.evidence_pack import EvidencePackV1, assemble_evidence_pack
from deepreason.bridge.events import BridgeAction, BridgeEventPayloadV1
from deepreason.bridge.models import BridgeFailureV1
from deepreason.bridge.retry import (
    BridgeWorkflowAttemptFenceV1,
    authorize_workflow_retry,
)
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import Event, Problem, ProblemProvenance, Rule, StateDiff
from deepreason.ontology.event import LLMAttempt, LLMCall
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    RunManifest,
    SchoolExecutionPolicyV1,
    TerminalCommitmentPolicyV1,
    compile_run_manifest,
    load_run_manifest,
    write_run_manifest,
)
from deepreason.runtime.continuation import prepare_continuation
from deepreason.runtime.stop import (
    StopController,
    StopMetrics,
    StopPolicy,
    build_stop_record,
    persist_stop_record,
    write_stop_record,
)
from deepreason.runtime.terminal_authority import (
    derive_terminal_authority,
    ensure_terminal_commitment,
)
from deepreason.verification.report import verify_root_report
from deepreason.workflow.lifecycle import build_stopped_lifecycle
from deepreason.workflow.models import (
    RunTerminalCommitmentV1,
    RunTerminalResultDraftV1,
)


STAMP = "2026-07-21T00:00:00Z"


def _manifest(*, run_input_digest: str = "a" * 64):
    config = Config(
        roles={
            "conjecturer": {
                "endpoint_id": "terminal-authority",
                "endpoint": "mock://terminal-authority",
                "model": "offline-model",
                "provider": "mock",
                "family": "offline",
                "max_tokens": 64,
                "context_window_tokens": 262_144,
            }
        }
    )
    control = ControlPlanePolicyV3(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="disabled",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=(),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
    )
    return compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
        run_input_digest=run_input_digest,
    )


def _root(tmp_path, manifest=None):
    manifest = manifest or _manifest()
    write_run_manifest(manifest, tmp_path / "run-manifest.json")
    return manifest, Harness(tmp_path)


def _application_stop(root, harness, *, reason="completed"):
    policy = StopPolicy()
    metrics = StopMetrics(cycle=0)
    harness.record_measure(
        inputs=[
            "run-stop",
            policy.digest,
            json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
            reason,
            str(harness._next_seq),
        ]
    )
    stop = write_stop_record(
        root,
        reason=reason,
        policy=policy,
        metrics=metrics,
        event_seq=harness._next_seq - 1,
    )
    summary = derive_model_execution_summary(
        harness,
        harness.workflow_state._run_manifest,
        event_horizon_seq=stop["event_seq"],
    )
    return stop, summary


def _result_body(status, stop, summary):
    return {
        "schema": "deepreason-run-result-v2",
        "state": status,
        "workload": "text",
        "verification": {
            "schema": "verification.summary.v2",
            "valid": True,
            "integrity_valid": True,
            "security_valid": True,
            "completion_satisfied": True,
            "epistemic_checks_passed": True,
            "operational_checks_passed": True,
            "finding_counts": {
                "integrity": 0,
                "security": 0,
                "completion": 0,
                "epistemic": 0,
                "operational": 0,
            },
        },
        "completion_status": "satisfied",
        "canonical_bridge_eligible": status == "completed",
        "stop": stop,
        "model_execution": summary.model_dump(
            mode="json", by_alias=True, exclude_none=True
        ),
    }


def _commit(root, harness, manifest, *, status="completed", reason="completed"):
    stop, summary = _application_stop(root, harness, reason=reason)
    commitment = ensure_terminal_commitment(
        harness,
        manifest,
        terminal_status=status,
        stop=stop,
        model_execution=summary,
        result_body=_result_body(status, stop, summary),
    )
    assert commitment is not None
    return stop, summary, commitment


def _process_terminal_writer(root, stop, barrier, results):
    """Spawn-safe real Harness terminal writer used by the lock regression."""

    root = __import__("pathlib").Path(root)
    manifest = load_run_manifest(root / "run-manifest.json")
    harness = Harness(root)
    summary = derive_model_execution_summary(
        harness, manifest, event_horizon_seq=stop["event_seq"]
    )
    barrier.wait(timeout=15)
    try:
        commitment = ensure_terminal_commitment(
            harness,
            manifest,
            terminal_status="completed",
            stop=stop,
            model_execution=summary,
            result_body=_result_body("completed", stop, summary),
        )
    except Exception as error:  # pragma: no cover - surfaced through parent assertion
        results.put(("error", type(error).__name__, str(error)))
    else:
        results.put(("ok", commitment.id))


def test_new_v6_manifest_freezes_exact_terminal_commitment_policy(tmp_path):
    manifest = _manifest()
    expected = {
        "schema": "terminal-commitment-policy.v1",
        "required": True,
        "commitment_schema": "run-terminal-commitment.v1",
        "selection": "first_commitment_per_epoch",
        "resume": "typed_resume_opens_next_epoch",
        "integrity_scope": "root_local_manifest_and_replay",
        "post_terminal": "exact_commitment_bound_descendants",
    }
    assert manifest.terminal_commitment_policy == TerminalCommitmentPolicyV1()
    assert manifest.terminal_commitment_policy.model_dump(
        mode="json", by_alias=True
    ) == expected
    path, _digest = write_run_manifest(manifest, tmp_path / "manifest.json")
    assert load_run_manifest(path) == manifest

    historical_payload = json.loads(manifest.canonical_bytes())
    historical_payload.pop("terminal_commitment_policy")
    historical = RunManifest.model_validate(historical_payload)
    assert historical.terminal_commitment_policy is None
    assert historical.sha256 != manifest.sha256
    assert b"terminal_commitment_policy" not in historical.canonical_bytes()


def test_first_commitment_latches_epoch_and_replays_byte_identically(tmp_path):
    manifest, harness = _root(tmp_path)
    stop, summary, commitment = _commit(tmp_path, harness, manifest)

    assert commitment.terminal_epoch == 0
    assert commitment.reasoning_event_horizon_seq == stop["event_seq"]
    assert commitment.model_execution_summary_digest
    assert harness.workflow_state.current_terminal_commitment == commitment
    first_projection = harness.workflow_state.terminal_commitment_ledger_payload()
    checkpoint_bytes = (tmp_path / "workflow-checkpoint.json").read_bytes()

    replayed = Harness(tmp_path)
    assert replayed.workflow_state.current_terminal_commitment == commitment
    assert replayed.workflow_state.terminal_commitment_ledger_payload() == (
        first_projection
    )
    assert ensure_terminal_commitment(
        replayed,
        manifest,
        terminal_status="completed",
        stop=stop,
        model_execution=summary,
        result_body=_result_body("completed", stop, summary),
    ) == commitment
    assert len(replayed.workflow_state.terminal_commitments_by_epoch) == 1
    assert (tmp_path / "workflow-checkpoint.json").read_bytes() == checkpoint_bytes


def test_second_or_foreign_commitment_cannot_replace_epoch_zero(tmp_path):
    manifest, harness = _root(tmp_path)
    _stop, _summary, first = _commit(tmp_path, harness, manifest)
    second = RunTerminalCommitmentV1.create(
        **{
            **first.model_dump(
                mode="python", by_alias=True, exclude={"id"}, exclude_none=True
            ),
            "terminal_status": "failed",
            "expected_commitment_event_seq": harness._next_seq,
        }
    )
    _schema, draft = harness.objects.get(first.result_draft_ref)
    with pytest.raises(Exception, match="already has a canonical commitment"):
        harness.record_terminal_commitment(second, draft)
    assert Harness(tmp_path).workflow_state.current_terminal_commitment == first

    foreign = RunTerminalCommitmentV1.create(
        **{
            **first.model_dump(
                mode="python", by_alias=True, exclude={"id"}, exclude_none=True
            ),
            "manifest_sha256": "f" * 64,
            "run_id": "f" * 64,
            "expected_commitment_event_seq": harness._next_seq,
        }
    )
    with pytest.raises(Exception, match="another run manifest"):
        harness.record_terminal_commitment(foreign, draft)


def test_commitment_rejects_wrong_summary_digest(tmp_path):
    manifest, harness = _root(tmp_path)
    stop, summary = _application_stop(tmp_path, harness)
    draft = RunTerminalResultDraftV1.create(
        manifest_sha256=manifest.sha256,
        run_id=manifest.sha256,
        terminal_epoch=0,
        result_body=_result_body("completed", stop, summary),
    )
    false_summary = RunTerminalCommitmentV1.create(
        manifest_sha256=manifest.sha256,
        run_id=manifest.sha256,
        terminal_epoch=0,
        terminal_status="completed",
        stop_reason=stop["reason"],
        reasoning_event_horizon_seq=stop["event_seq"],
        stop_record_digest=stop["digest"],
        stop_record_ref=(
            f"run-stops/{stop['event_seq']:012d}-{stop['digest']}.json"
        ),
        terminal_source="application_terminal",
        terminal_source_event_seq=stop["event_seq"],
        model_execution_summary_digest="f" * 64,
        result_draft_ref=draft.id,
        expected_commitment_event_seq=harness._next_seq,
    )
    with pytest.raises(Exception, match="result draft differs"):
        harness.record_terminal_commitment(false_summary, draft)
    assert Harness(tmp_path).workflow_state.current_terminal_commitment is None


@pytest.mark.parametrize(
    "alteration",
    ("marker", "policy", "metrics", "reason", "sequence", "missing", "extra"),
)
def test_application_stop_requires_exact_ordered_source_inputs(tmp_path, alteration):
    manifest, harness = _root(tmp_path)
    policy = StopPolicy()
    metrics = StopMetrics(cycle=0)
    stop = build_stop_record(
        reason="completed",
        policy=policy,
        metrics=metrics,
        event_seq=harness._next_seq,
    )
    inputs = [
        "run-stop",
        policy.digest,
        json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
        "completed",
        str(stop["event_seq"]),
    ]
    replacements = {
        "marker": (0, "not-run-stop"),
        "policy": (1, "f" * 64),
        "metrics": (
            2,
            json.dumps(StopMetrics(cycle=1).model_dump(mode="json"), sort_keys=True),
        ),
        "reason": (3, "operational_failure"),
        "sequence": (4, str(stop["event_seq"] + 1)),
    }
    if alteration in replacements:
        index, value = replacements[alteration]
        inputs[index] = value
    elif alteration == "missing":
        inputs.pop()
    else:
        inputs.append("foreign")
    harness.record_measure(inputs=inputs)
    persist_stop_record(tmp_path, stop)
    summary = derive_model_execution_summary(
        harness, manifest, event_horizon_seq=stop["event_seq"]
    )
    with pytest.raises(ValueError, match="TERMINAL_APPLICATION_STOP_SOURCE_MISMATCH"):
        ensure_terminal_commitment(
            harness,
            manifest,
            terminal_status="completed",
            stop=stop,
            model_execution=summary,
            result_body=_result_body("completed", stop, summary),
        )


def test_digest_valid_coordinated_stop_substitution_is_rejected(tmp_path):
    manifest, harness = _root(tmp_path)
    original, summary = _application_stop(tmp_path, harness)
    forged = build_stop_record(
        reason=original["reason"],
        policy=StopPolicy(min_cycles=7),
        metrics=StopMetrics(cycle=99),
        event_seq=original["event_seq"],
    )
    persist_stop_record(tmp_path, forged)
    with pytest.raises(ValueError, match="TERMINAL_APPLICATION_STOP_SOURCE_MISMATCH"):
        ensure_terminal_commitment(
            harness,
            manifest,
            terminal_status="completed",
            stop=forged,
            model_execution=summary,
            result_body=_result_body("completed", forged, summary),
        )


def test_replay_revalidates_exact_application_stop_source(tmp_path):
    manifest, harness = _root(tmp_path)
    _stop, _summary, _commitment = _commit(tmp_path, harness, manifest)
    log_path = tmp_path / "log.jsonl"
    events = [json.loads(line) for line in log_path.read_text().splitlines()]
    events[0]["inputs"][2] = json.dumps(
        StopMetrics(cycle=4).model_dump(mode="json"), sort_keys=True
    )
    log_path.write_text(
        "".join(json.dumps(event, separators=(",", ":")) + "\n" for event in events),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="TERMINAL_APPLICATION_STOP_SOURCE_MISMATCH"):
        Harness(tmp_path)


def _typed_converged_stop(root, harness, manifest):
    policy = StopPolicy(min_cycles=0, window=1, stable_windows=1)
    controller = StopController(policy)
    before = controller.snapshot()
    metrics = StopMetrics(cycle=0)
    decision = controller.evaluate(metrics)
    stop = build_stop_record(
        reason=decision.reason,
        policy=policy,
        metrics=metrics,
        event_seq=harness._next_seq,
    )
    observation, snapshot, lifecycle = build_stopped_lifecycle(
        harness.workflow_state,
        manifest_digest=manifest.sha256,
        controller_version="workflow.controller.v3",
        workflow_profile="inquiry.active.v2",
        policy=policy,
        metrics=metrics,
        deterministic_decision=decision,
        controller_state_before=before,
        controller_state_after=controller.snapshot(),
        stop_event_seq=harness._next_seq,
        stop_record_digest=stop["digest"],
    )
    harness.record_lifecycle_transition(observation, snapshot, lifecycle)
    persist_stop_record(root, stop)
    summary = derive_model_execution_summary(
        harness, manifest, event_horizon_seq=stop["event_seq"]
    )
    commitment = ensure_terminal_commitment(
        harness,
        manifest,
        terminal_status="completed",
        stop=stop,
        model_execution=summary,
        result_body=_result_body("completed", stop, summary),
    )
    return stop, commitment


def test_typed_resume_opens_child_epoch_and_preserves_parent(tmp_path):
    manifest, harness = _root(tmp_path)
    stop, parent = _typed_converged_stop(tmp_path, harness, manifest)
    assert parent is not None
    assert parent.terminal_source == "workflow_lifecycle"
    assert parent.lifecycle_decision_ref == (
        harness.workflow_state.terminal_lifecycle_decision.id
    )

    prepare_continuation(
        tmp_path,
        cycles=1,
        tokens=32,
        check_operator_lock=False,
    )
    resumed = Harness(tmp_path)
    assert resumed.workflow_state.current_terminal_epoch == 1
    assert resumed.workflow_state.current_terminal_commitment is None
    resume = resumed.workflow_state.current_resume_decision
    assert resume is not None
    assert resume.prior_terminal_commitment_ref == parent.id
    assert resume.opened_terminal_epoch == 1
    assert resumed.workflow_state.terminal_commitments_by_epoch[0] == parent

    _stop, _summary, child = _commit(tmp_path, resumed, manifest)
    assert child.terminal_epoch == 1
    assert child.parent_terminal_commitment_ref == parent.id
    assert child.opening_resume_ref == resume.id
    assert Harness(tmp_path).workflow_state.terminal_commitments_by_epoch == {
        0: parent,
        1: child,
    }


@pytest.mark.parametrize(
    ("status", "reason"),
    (
        ("completed", "completed"),
        ("failed", "operational_failure"),
        ("cancelled", "operator_cancelled"),
        ("failed", "workload_terminal"),
    ),
)
def test_all_current_terminal_outcomes_share_commitment_mechanism(
    tmp_path, status, reason
):
    manifest, harness = _root(tmp_path)
    _stop, _summary, commitment = _commit(
        tmp_path, harness, manifest, status=status, reason=reason
    )
    assert commitment.terminal_status == status
    assert commitment.stop_reason == reason


def test_result_writer_recovers_event_without_result_without_duplicate(tmp_path):
    manifest, harness = _root(tmp_path)
    stop, _summary = _application_stop(tmp_path, harness)
    payload = {
        "schema": "deepreason-run-result-v1",
        "state": "completed",
        "workload": "text",
        "stop": stop,
    }
    first = _v6_run_result(tmp_path, manifest, payload, harness=harness)
    event_count = len(tuple(harness.log.read()))
    assert first["terminal_commitment_ref"]
    assert not (tmp_path / "run-result.json").exists()

    service = TextRunApplicationService(TextRunWorkerRegistry())
    recovered_terminal = service.result(
        InspectTextRunIntentV1(root=str(tmp_path))
    )
    recovered = recovered_terminal.payload
    assert recovered == first
    assert json.loads((tmp_path / "run-result.json").read_text()) == first
    assert len(tuple(Harness(tmp_path).log.read())) == event_count
    result_bytes = (tmp_path / "run-result.json").read_bytes()
    assert service.result(
        InspectTextRunIntentV1(root=str(tmp_path))
    ).payload == first
    assert (tmp_path / "run-result.json").read_bytes() == result_bytes
    assert len(tuple(Harness(tmp_path).log.read())) == event_count


def test_orphan_commitment_object_is_reused_deterministically(
    tmp_path, monkeypatch
):
    manifest, harness = _root(tmp_path)
    stop, summary = _application_stop(tmp_path, harness)
    original_commit = Harness._commit

    def crash_before_event(*_args, **_kwargs):
        raise RuntimeError("simulated crash before terminal event")

    monkeypatch.setattr(Harness, "_commit", crash_before_event)
    with pytest.raises(RuntimeError, match="simulated crash"):
        ensure_terminal_commitment(
            harness,
            manifest,
            terminal_status="completed",
                stop=stop,
                model_execution=summary,
                result_body=_result_body("completed", stop, summary),
        )
    objects = tuple(
        (tmp_path / "objects" / "workflow-run-terminal-commitment-v1").glob(
            "*.json"
        )
    )
    assert len(objects) == 1
    assert Harness(tmp_path).workflow_state.current_terminal_commitment is None

    monkeypatch.setattr(Harness, "_commit", original_commit)
    recovered = ensure_terminal_commitment(
        harness,
        manifest,
        terminal_status="completed",
        stop=stop,
        model_execution=summary,
        result_body=_result_body("completed", stop, summary),
    )
    assert recovered is not None
    assert len(
        tuple(
            (tmp_path / "objects" / "workflow-run-terminal-commitment-v1").glob(
                "*.json"
            )
        )
    ) == 1
    assert Harness(tmp_path).workflow_state.current_terminal_commitment == recovered


def test_event_before_checkpoint_recovery_seals_before_result(tmp_path, monkeypatch):
    manifest, harness = _root(tmp_path)
    stop, summary = _application_stop(tmp_path, harness)
    original_write = Harness.write_workflow_checkpoint
    remaining_failures = 2

    def crash_checkpoint(self):
        nonlocal remaining_failures
        if self.workflow_state.current_terminal_commitment and remaining_failures:
            remaining_failures -= 1
            raise RuntimeError("simulated checkpoint crash")
        return original_write(self)

    monkeypatch.setattr(Harness, "write_workflow_checkpoint", crash_checkpoint)
    with pytest.raises(RuntimeError, match="simulated checkpoint crash"):
        ensure_terminal_commitment(
            harness,
            manifest,
            terminal_status="completed",
            stop=stop,
            model_execution=summary,
            result_body=_result_body("completed", stop, summary),
        )
    committed = Harness(tmp_path).workflow_state.current_terminal_commitment
    assert committed is not None
    assert not (tmp_path / "workflow-checkpoint.json").exists()
    assert not (tmp_path / "run-result.json").exists()
    event_count = len(tuple(Harness(tmp_path).log.read()))

    service = TextRunApplicationService(TextRunWorkerRegistry())
    with pytest.raises(RuntimeError, match="simulated checkpoint crash"):
        service.result(InspectTextRunIntentV1(root=str(tmp_path)))
    assert not (tmp_path / "run-result.json").exists()
    assert len(tuple(Harness(tmp_path).log.read())) == event_count

    monkeypatch.setattr(Harness, "write_workflow_checkpoint", original_write)
    result = service.result(InspectTextRunIntentV1(root=str(tmp_path))).payload
    checkpoint = json.loads((tmp_path / "workflow-checkpoint.json").read_text())
    replayed = Harness(tmp_path)
    assert result["terminal_commitment_ref"] == committed.id
    assert checkpoint["terminal_commitment_ledger_digest"] == (
        replayed.workflow_state.terminal_commitment_ledger_digest
    )
    assert len(tuple(replayed.log.read())) == event_count
    result_bytes = (tmp_path / "run-result.json").read_bytes()
    assert service.result(InspectTextRunIntentV1(root=str(tmp_path))).payload == result
    assert (tmp_path / "run-result.json").read_bytes() == result_bytes
    assert len(tuple(Harness(tmp_path).log.read())) == event_count


def test_conflicting_terminal_checkpoint_is_not_overwritten(tmp_path):
    manifest, harness = _root(tmp_path)
    _stop, _summary, _commitment = _commit(tmp_path, harness, manifest)
    path = tmp_path / "workflow-checkpoint.json"
    payload = json.loads(path.read_text())
    payload["terminal_commitment_ledger_digest"] = "sha256:" + "f" * 64
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    before = path.read_bytes()
    service = TextRunApplicationService(TextRunWorkerRegistry())
    with pytest.raises(ValueError, match="workflow checkpoint differs"):
        service.result(InspectTextRunIntentV1(root=str(tmp_path)))
    assert path.read_bytes() == before
    assert not (tmp_path / "run-result.json").exists()


def test_threaded_same_payload_has_one_terminal_event(tmp_path):
    manifest, harness = _root(tmp_path)
    stop, summary = _application_stop(tmp_path, harness)
    barrier = threading.Barrier(2)
    results: queue.Queue = queue.Queue()

    def writer():
        local = Harness(tmp_path)
        barrier.wait(timeout=10)
        try:
            value = ensure_terminal_commitment(
                local,
                manifest,
                terminal_status="completed",
                stop=stop,
                model_execution=summary,
                result_body=_result_body("completed", stop, summary),
            )
        except Exception as error:  # pragma: no cover - asserted below
            results.put(("error", type(error).__name__, str(error)))
        else:
            results.put(("ok", value.id))

    threads = [threading.Thread(target=writer) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
    observed = [results.get(timeout=2) for _ in threads]
    assert {item[0] for item in observed} == {"ok"}
    assert len({item[1] for item in observed}) == 1
    replayed = Harness(tmp_path)
    assert [
        event.control.action
        for event in replayed.log.read()
        if event.control is not None and hasattr(event.control, "action")
    ].count("terminal_committed") == 1


def test_process_same_payload_has_one_terminal_event(tmp_path):
    manifest, harness = _root(tmp_path)
    stop, _summary = _application_stop(tmp_path, harness)
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2)
    results = context.Queue()
    processes = [
        context.Process(
            target=_process_terminal_writer,
            args=(str(tmp_path), stop, barrier, results),
        )
        for _ in range(2)
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=30)
    assert all(process.exitcode == 0 for process in processes)
    observed = [results.get(timeout=3) for _ in processes]
    assert {item[0] for item in observed} == {"ok"}
    assert len({item[1] for item in observed}) == 1
    replayed = Harness(tmp_path)
    assert [event.seq for event in replayed.log.read()] == [0, 1]


def test_threaded_conflicting_payload_first_writer_wins(tmp_path):
    manifest, harness = _root(tmp_path)
    first_stop, first_summary = _application_stop(tmp_path, harness, reason="completed")
    second_stop, second_summary = _application_stop(
        tmp_path, harness, reason="operational_failure"
    )
    candidates = (
        ("completed", first_stop, first_summary),
        ("failed", second_stop, second_summary),
    )
    barrier = threading.Barrier(2)
    results: queue.Queue = queue.Queue()

    def writer(candidate):
        status, stop, summary = candidate
        local = Harness(tmp_path)
        barrier.wait(timeout=10)
        try:
            value = ensure_terminal_commitment(
                local,
                manifest,
                terminal_status=status,
                stop=stop,
                model_execution=summary,
                result_body=_result_body(status, stop, summary),
            )
        except Exception as error:
            results.put(("error", type(error).__name__, str(error)))
        else:
            results.put(("ok", value.id))

    threads = [threading.Thread(target=writer, args=(item,)) for item in candidates]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
    observed = [results.get(timeout=2) for _ in threads]
    assert sorted(item[0] for item in observed) == ["error", "ok"]
    error = next(item for item in observed if item[0] == "error")
    assert "TERMINAL_COMMITMENT_CONFLICT" in error[2]
    replayed = Harness(tmp_path)
    assert len(replayed.workflow_state.terminal_commitments_by_epoch) == 1
    assert [
        event.control.action
        for event in replayed.log.read()
        if event.control is not None and hasattr(event.control, "action")
    ].count("terminal_committed") == 1


def test_missing_immutable_stop_object_invalidates_latched_root(tmp_path):
    manifest, harness = _root(tmp_path)
    _stop, _summary, commitment = _commit(tmp_path, harness, manifest)
    (tmp_path / commitment.stop_record_ref).unlink()
    with pytest.raises(ValueError, match="TERMINAL_STOP_OBJECT_REQUIRED"):
        Harness(tmp_path)


def test_checkpoint_detects_commitment_event_truncation(tmp_path):
    manifest, harness = _root(tmp_path)
    _stop, _summary, _commitment = _commit(tmp_path, harness, manifest)
    log_path = tmp_path / "log.jsonl"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    log_path.write_text(lines[0] + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="lost its checkpointed tail"):
        Harness(tmp_path)


def test_later_stop_without_resume_cannot_replace_committed_epoch(tmp_path):
    manifest, harness = _root(tmp_path)
    _first_stop, _summary, first = _commit(tmp_path, harness, manifest)
    later_stop, later_summary = _application_stop(
        tmp_path, harness, reason="operational_failure"
    )
    with pytest.raises(ValueError, match="commitment"):
        ensure_terminal_commitment(
            harness,
            manifest,
            terminal_status="failed",
            stop=later_stop,
            model_execution=later_summary,
            result_body=_result_body("failed", later_stop, later_summary),
        )
    assert Harness(tmp_path).workflow_state.current_terminal_commitment == first


def test_deleting_optional_result_fields_never_removes_manifest_requirement(tmp_path):
    manifest, harness = _root(tmp_path)
    stop, _summary = _application_stop(tmp_path, harness)
    result = _v6_run_result(
        tmp_path,
        manifest,
        {
            "schema": "deepreason-run-result-v1",
            "state": "completed",
            "workload": "text",
            "stop": stop,
        },
        harness=harness,
    )
    result.pop("terminal_commitment_ref")
    result.pop("stop")
    result["model_execution"].pop("event_horizon_seq")

    parsed = RunManifest.model_validate_json(manifest.canonical_bytes())
    assert parsed.terminal_commitment_policy is not None
    replayed = Harness(tmp_path).workflow_state
    assert replayed.current_terminal_commitment is not None
    assert replayed.current_terminal_authority.id != result.get(
        "terminal_commitment_ref"
    )


def test_pre_harness_abort_is_readable_but_uncommitted(tmp_path):
    manifest = _manifest()
    write_run_manifest(manifest, tmp_path / "run-manifest.json")
    payload = _v6_run_result(
        tmp_path,
        manifest,
        {
            "schema": "deepreason-run-result-v1",
            "state": "failed",
            "workload": "text",
            "error": "pre-harness abort",
        },
    )
    assert "terminal_commitment_ref" not in payload
    assert "stop" not in payload
    assert Harness(tmp_path).workflow_state.current_terminal_authority is None


def _root_bytes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _committed_problem_root(tmp_path):
    manifest, harness = _root(tmp_path)
    problem = Problem(
        id="problem-terminal-bridge",
        description="What result is supported?",
        provenance=ProblemProvenance(trigger="seed", **{"from": []}),
    )
    harness.register_problem(problem)
    _stop, _summary, commitment = _commit(
        tmp_path,
        harness,
        manifest,
    )
    TextRunApplicationService(TextRunWorkerRegistry()).result(
        InspectTextRunIntentV1(root=str(tmp_path))
    )
    return manifest, harness, problem, commitment


def _failure_graph(
    root,
    manifest,
    problem,
    commitment,
    *,
    source_terminal_commitment_ref=None,
    error_code="BRIDGE_STAGE_A_FAILED",
    error_message="bounded stage A failure",
):
    source = Harness.at(root, commitment.reasoning_event_horizon_seq)
    pack = assemble_evidence_pack(
        source,
        problem.id,
        formal_seq=commitment.reasoning_event_horizon_seq,
        source_terminal_commitment_ref=source_terminal_commitment_ref,
    )
    catalog = pack.claim_ledger_catalog("answer")
    failure = BridgeFailureV1.create(
        run_manifest_digest=manifest.sha256,
        formal_seq=pack.formal_seq,
        problem_ref=problem.id,
        output_target="answer",
        evidence_pack_id=pack.id,
        catalog_id=catalog.id,
        phase="stage_a",
        error_code=error_code,
        error_message=error_message,
        terminal_inputs=[],
    )
    return pack, catalog, failure


def _record_failure(
    harness,
    graph,
    *,
    error_code="BRIDGE_STAGE_A_FAILED",
    llm=None,
):
    pack, catalog, failure = graph
    return harness.record_bridge_event(
        BridgeAction.FAILED,
        inputs=[],
        records=[
            ("bridge-evidence-pack", pack),
            ("bridge-ledger-input-catalog", catalog),
            ("bridge-failure", failure),
        ],
        error_code=error_code,
        llm=llm,
    )


def _append_empty_failure(harness, commitment, *, error_code):
    payload = BridgeEventPayloadV1(
        action=BridgeAction.FAILED,
        actor="harness",
        inputs=[commitment.id],
        outputs=[],
        error_code=error_code,
    )
    event = Event(
        seq=harness._next_seq,
        ts=STAMP,
        rule=Rule.BRIDGE,
        inputs=list(payload.inputs),
        outputs=[],
        bridge=payload,
        state_diff=StateDiff(),
    )
    harness.log.append(event)
    harness._next_seq += 1
    return event


def test_post_terminal_empty_failed_writer_denial_is_byte_preserving(tmp_path):
    manifest, harness, _problem, commitment = _committed_problem_root(tmp_path)
    before = _root_bytes(tmp_path)
    log_before = tuple(harness.log.read())
    state_before = deepcopy(harness.bridge_state)
    work_before = deepcopy(harness.workflow_state.transaction_work)

    with pytest.raises(
        ValueError,
        match="requires exactly one bridge failure",
    ):
        harness.record_bridge_event(
            BridgeAction.FAILED,
            inputs=[commitment.id],
            error_code="POST_TERMINAL_GENERIC_INPUT",
        )

    assert tuple(harness.log.read()) == log_before
    assert harness.bridge_state == state_before
    assert harness.workflow_state.transaction_work == work_before
    assert _root_bytes(tmp_path) == before
    assert derive_terminal_authority(tmp_path, manifest=manifest).current_valid


def test_durable_empty_failures_invalidate_authority_root_and_preflight(tmp_path):
    manifest, harness, _problem, commitment = _committed_problem_root(tmp_path)
    _append_empty_failure(
        harness,
        commitment,
        error_code="POST_TERMINAL_GENERIC_INPUT",
    )
    _append_empty_failure(
        harness,
        commitment,
        error_code="POST_TERMINAL_GENERIC_INPUT_REPEAT",
    )

    authority = derive_terminal_authority(tmp_path, manifest=manifest)
    assert authority.status == "invalid_incomplete"
    assert authority.detail_code == "TERMINAL_POST_HORIZON_BRIDGE_INVALID"
    report = verify_root_report(tmp_path)
    assert not report.integrity_valid
    with pytest.raises(ValueError, match="BRIDGE_ROOT_AUTHORITY_INVALID"):
        preflight_canonical_bridge(tmp_path, manifest)


@pytest.mark.parametrize("source_ref", [None, "sha256:" + "f" * 64])
def test_failed_writer_rejects_missing_or_foreign_pack_commitment(
    tmp_path,
    source_ref,
):
    manifest, harness, problem, commitment = _committed_problem_root(tmp_path)
    graph = _failure_graph(
        tmp_path,
        manifest,
        problem,
        commitment,
        source_terminal_commitment_ref=source_ref,
    )
    before = _root_bytes(tmp_path)

    with pytest.raises(
        ValueError,
        match="evidence pack names another commitment",
    ):
        _record_failure(harness, graph)

    assert _root_bytes(tmp_path) == before
    assert harness.bridge_state.failed_events == []
    assert derive_terminal_authority(tmp_path, manifest=manifest).current_valid


def test_valid_no_work_typed_failure_is_authorized_and_repeat_requires_retry(
    tmp_path,
):
    manifest, harness, problem, commitment = _committed_problem_root(tmp_path)
    graph = _failure_graph(
        tmp_path,
        manifest,
        problem,
        commitment,
        source_terminal_commitment_ref=commitment.id,
    )
    event = _record_failure(harness, graph)

    assert event.bridge.action == BridgeAction.FAILED
    assert harness.workflow_state.transaction_work == {}
    assert derive_terminal_authority(tmp_path, manifest=manifest).current_valid
    assert Harness(tmp_path).bridge_state.failures[graph[2].id] == graph[2]

    before = _root_bytes(tmp_path)
    with pytest.raises(ValueError, match="requires an exact retry"):
        _record_failure(harness, graph)
    assert _root_bytes(tmp_path) == before


def test_multiple_typed_failures_are_authorized_only_through_retry_chain(
    tmp_path,
):
    manifest, harness, problem, commitment = _committed_problem_root(tmp_path)
    first_graph = _failure_graph(
        tmp_path,
        manifest,
        problem,
        commitment,
        source_terminal_commitment_ref=commitment.id,
    )
    pack, catalog, first_failure = first_graph
    prompt_ref = harness.blobs.put(b"bounded retry prompt")
    raw_ref = harness.blobs.put(b"invalid retry response")
    fence = BridgeWorkflowAttemptFenceV1(
        manifest_digest=manifest.sha256,
        formal_seq=pack.formal_seq,
        catalog_id=catalog.id,
        contract_id="bridge.claim-ledger.compact.v2",
        prompt_policy_digest="b" * 64,
        role="summarizer",
        seat=0,
        endpoint_id="mock:retry-seat",
        route_sha256="c" * 64,
    )
    call = LLMCall(
        role=fence.role,
        model="offline",
        endpoint="mock://retry",
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=11,
        attempt_trace=[
            LLMAttempt(
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                diagnostic_ref="diagnostic",
                contract_id=fence.contract_id,
                endpoint_id=fence.endpoint_id,
                route_sha256=fence.route_sha256,
                seat=fence.seat,
                tokens=11,
                valid=False,
            )
        ],
    )
    _record_failure(harness, first_graph, llm=call)
    retry = authorize_workflow_retry(
        WorkflowRetryPolicyV1(
            max_workflow_retries=1,
            retryable_error_codes=(first_failure.error_code,),
        ),
        prior_failure_id=first_failure.id,
        error_code=first_failure.error_code,
        completed_retries=0,
        attempt_fence=fence,
        prior_token_count=call.tokens,
    )
    harness.record_bridge_event(
        BridgeAction.WORKFLOW_RETRY_STARTED,
        inputs=[first_failure.id, commitment.id],
        records=[("bridge-workflow-retry", retry)],
    )
    second_graph = _failure_graph(
        tmp_path,
        manifest,
        problem,
        commitment,
        source_terminal_commitment_ref=commitment.id,
        error_message="bounded retry attempt failure",
    )
    _record_failure(harness, second_graph)

    second_failure = second_graph[2]
    assert first_failure.id != second_failure.id
    replayed = Harness(tmp_path)
    assert replayed.bridge_state.retry_id_by_failure[second_failure.id] == retry.id
    assert derive_terminal_authority(tmp_path, manifest=manifest).current_valid


def test_historical_generic_failure_is_readable_without_current_authority(
    tmp_path,
):
    payload = json.loads(_manifest().canonical_bytes())
    payload.pop("terminal_commitment_policy")
    historical = RunManifest.model_validate(payload)
    write_run_manifest(historical, tmp_path / "run-manifest.json")
    harness = Harness(tmp_path)
    harness.record_bridge_event(
        BridgeAction.FAILED,
        error_code="HISTORICAL_BRIDGE_FAILURE",
    )

    reopened = Harness(tmp_path)
    assert reopened.bridge_state.failed_events == [0]
    authority = derive_terminal_authority(tmp_path, manifest=historical)
    assert authority.status == "historical_read_only"
    assert not authority.current_valid
