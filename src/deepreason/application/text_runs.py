"""One application service and worker registry for full-engine text runs."""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from deepreason.application.models import (
    CancelTextRunIntentV1,
    ContinueTextRunIntentV1,
    InspectTextRunIntentV1,
    OperatorCancellationIntentV1,
    OutstandingWorkItemProjectionV1,
    OutstandingWorkResultV1,
    RunBudgetIntentV1,
    RunCancellationAcceptedV1,
    RunProgressResultV1,
    RunResultV2,
    RunStartedV1,
    StartTextRunIntentV1,
    TextRunTerminalResultV1,
    WatchTextRunIntentV1,
    derive_model_execution_summary,
)
from deepreason.locking import ProcessLockBusy, operator_locks


class TextRunWorkerRegistry:
    """Process-local handles; durable ownership remains the operator lock."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.threads: dict[str, threading.Thread] = {}

    def live(self, root: Path) -> threading.Thread | None:
        thread = self.threads.get(str(root.resolve()))
        return thread if thread is not None and thread.is_alive() else None

    def put(self, root: Path, thread: threading.Thread) -> None:
        self.threads[str(root.resolve())] = thread

    def discard(self, root: Path) -> None:
        self.threads.pop(str(root.resolve()), None)

    def join(self, root: Path | str, timeout: float | None = None) -> None:
        thread = self.threads.get(str(Path(root).resolve()))
        if thread is None:
            raise ValueError("RUN_WORKER_NOT_FOUND")
        thread.join(timeout=timeout)


TEXT_RUN_WORKERS = TextRunWorkerRegistry()


def _require_v6_manifest(manifest, *, operation: str) -> None:
    """Require an actual schema-v6 manifest without applying launch rollback."""

    from deepreason.run_manifest import RunManifest, RunManifestError
    from deepreason.runtime.launch_policy import V6_RUN_MANIFEST_REQUIRED

    if not isinstance(manifest, RunManifest) or manifest.schema_version != 6:
        raise RunManifestError(
            V6_RUN_MANIFEST_REQUIRED,
            f"{operation} requires RunManifest schema version 6",
            "/schema_version",
        )


def _v6_run_result(
    root: Path,
    manifest,
    payload: dict[str, Any],
    *,
    harness=None,
) -> dict[str, Any]:
    """Add the v2 terminal envelope only for opt-in v6 runs."""

    if manifest.schema_version != 6:
        return payload
    from deepreason.verification.report import (
        VerificationFindingV2,
        verify_root_report,
    )

    try:
        report = verify_root_report(root, allow_missing_terminal=True)
    except Exception as error:  # noqa: BLE001 - terminalization must remain total
        from deepreason.verification.report import VerificationReportV2

        report = VerificationReportV2(
            operational=(
                VerificationFindingV2(
                    channel="operational",
                    check="terminal-verification",
                    detail=f"terminal verification could not complete: {error!r}"[:2_000],
                    source="derived",
                ),
            )
        )
    state = payload["state"]
    if (
        manifest.terminal_commitment_policy is not None
        and payload.get("stop") is None
        and not (state == "failed" and harness is None)
    ):
        raise ValueError(
            "current v6 terminal writing requires canonical stop authority"
        )
    updates: dict[str, tuple] = {}
    if state in {"failed", "cancelled"} and not report.completion:
        updates["completion"] = (
            VerificationFindingV2(
                channel="completion",
                check="run-terminal",
                detail=(
                    "reasoning failed before ordinary completion"
                    if state == "failed"
                    else "reasoning was cancelled before ordinary completion"
                ),
                source="terminal",
            ),
        )
    if state == "failed" and not report.operational:
        updates["operational"] = (
            VerificationFindingV2(
                channel="operational",
                check="run-terminal",
                detail=str(payload.get("error") or "reasoning terminated as failed")[:2_000],
                source="terminal",
            ),
        )
    if updates:
        report = report.model_copy(update=updates)
    from deepreason.harness import Harness

    stop = payload.get("stop")
    event_horizon_seq = (
        stop.get("event_seq") if isinstance(stop, dict) else None
    )
    authority_harness = harness or Harness(root)
    model_execution = derive_model_execution_summary(
        authority_harness,
        manifest,
        event_horizon_seq=event_horizon_seq,
    )
    result_body = {
        **payload,
        "schema": "deepreason-run-result-v2",
        "verification": report.summary_payload(),
        "completion_status": (
            "satisfied" if report.completion_satisfied else "incomplete"
        ),
        "canonical_bridge_eligible": state == "completed" and report.valid,
        "model_execution": model_execution,
    }
    result_body = RunResultV2.model_validate(result_body).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    terminal_commitment_ref = None
    if stop is not None and manifest.terminal_commitment_policy is not None:
        from deepreason.runtime.terminal_authority import (
            ensure_terminal_commitment,
        )

        terminal_commitment = ensure_terminal_commitment(
            authority_harness,
            manifest,
            terminal_status=state,
            stop=stop,
            model_execution=model_execution,
            result_body=result_body,
        )
        assert terminal_commitment is not None
        terminal_commitment_ref = terminal_commitment.id
    result = {
        **result_body,
        "terminal_commitment_ref": terminal_commitment_ref,
    }
    return RunResultV2.model_validate(result).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )


def _record_exhaustion_lifecycle_stop(harness, manifest, *, policy, metrics):
    """Record a typed, continuable STOPPED receipt for a budget-exhausted run.

    Returns the persisted stop record, or ``None`` when this root cannot
    carry the receipt (no owned control plane, or the workflow holds
    unfinished authority) — the caller then keeps the bare stop record and
    the terminal stays non-resumable, exactly as before.
    """

    from deepreason.runtime.stop import (
        StopControllerStateV1,
        StopDecision,
        build_stop_record,
        persist_stop_record,
    )
    from deepreason.workflow.lifecycle import build_stopped_lifecycle

    control = (
        getattr(manifest, "control_plane_policy", None)
        if manifest is not None and getattr(manifest, "schema_version", 1) in {4, 5, 6}
        else None
    )
    if (
        control is None
        or control.controller_version
        not in {
            "workflow.controller.v1",
            "workflow.controller.v2",
            "workflow.controller.v3",
        }
        or control.mode not in {"shadow", "active_conjecture", "active_inquiry"}
    ):
        return None
    stop_event_seq = harness._next_seq
    record = build_stop_record(
        reason="budget_exhausted",
        policy=policy,
        metrics=metrics,
        event_seq=stop_event_seq,
    )
    idle = StopControllerStateV1(policy_digest=policy.digest)
    try:
        observation, snapshot, lifecycle = build_stopped_lifecycle(
            harness.workflow_state,
            manifest_digest=manifest.sha256,
            controller_version=control.controller_version,
            workflow_profile=control.workflow_profile,
            policy=policy,
            metrics=metrics,
            deterministic_decision=StopDecision(stop=True, reason="budget_exhausted"),
            controller_state_before=idle,
            controller_state_after=idle,
            stop_event_seq=stop_event_seq,
            stop_record_digest=record["digest"],
        )
    except ValueError:
        return None
    event = harness.record_lifecycle_transition(observation, snapshot, lifecycle)
    if event.seq != stop_event_seq:
        raise RuntimeError("lifecycle Control event crossed its stop fence")
    stop = persist_stop_record(harness.root, record)
    harness.write_workflow_checkpoint()
    return stop


def _recoverable_typed_stop(harness, root: Path):
    """This root's own typed stop, when one was recorded but never committed.

    Terminalization is not atomic: the stop receipt lands as an event, the
    terminal commitment lands as a later one, and a process can die between
    them (observed 2026-08-13 — a container snapshot killed a `finalize`
    on the grounded-extension root after its STOPPED receipt and before its
    commitment). Recording a SECOND stop on the re-run would put two
    terminal claims on one epoch, so the durable one is reused instead.
    Returns ``None`` whenever the two records do not agree exactly, which
    keeps the ordinary path fail-closed.
    """

    from deepreason.runtime.stop import validate_stop_record

    state = harness.workflow_state
    decision = state.terminal_lifecycle_decision
    if decision is None or state.current_terminal_commitment is not None:
        return None
    path = Path(root) / "run-stop.json"
    if not path.exists():
        return None
    try:
        stop = validate_stop_record(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if (
        stop["digest"] != decision.stop_record_digest
        or stop["event_seq"] != decision.stop_event_seq
        or stop["reason"] != decision.deterministic_decision.reason
    ):
        return None
    return stop


def terminalize_text_run(
    harness,
    manifest,
    *,
    root,
    result,
    accounting,
    problem_id,
    cancelled: bool = False,
    latest_cycle: int = 0,
) -> dict[str, Any]:
    """Take one finished text run from its last event to a published terminal.

    Every configuration path that runs the scheduler ends here, because a
    second copy of this sequence is a second copy that drifts: the bare
    ``deepreason run --run-manifest`` path had no counterpart at all, so its
    roots could never be amended, continued, or read as results
    (grounded-extension run 8e22d0431fd2b98d).
    """

    from deepreason.capabilities.audit import write_tranche_a_audits
    from deepreason.capabilities.simulation import SimulationCapabilityController
    from deepreason.runtime.progress import _atomic_json
    from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record
    from deepreason.runtime.terminal_authority import finalize_terminal_result
    from deepreason.status_display import display_status_counts

    root = Path(root)
    scheduler_reason = result.get("stop_reason")
    stop_reason = (
        "operator_cancelled"
        if cancelled
        else scheduler_reason or "budget_exhausted"
    )
    if scheduler_reason and not cancelled:
        stop = json.loads((root / "run-stop.json").read_text())
    elif (recovered := _recoverable_typed_stop(harness, root)) is not None:
        stop = recovered
    else:
        policy = StopPolicy()
        metrics = StopMetrics(cycle=latest_cycle)
        stop = None
        if stop_reason == "budget_exhausted":
            # A typed STOPPED lifecycle receipt makes the exhaustion a
            # continuable terminal (owner decision: budget stops on public
            # runs are resumable).  A root that cannot take the receipt (no
            # owned control plane, unfinished workflow authority) keeps the
            # bare fail-closed stop.
            stop = _record_exhaustion_lifecycle_stop(
                harness, manifest, policy=policy, metrics=metrics
            )
        if stop is None:
            harness.record_measure(
                inputs=[
                    "run-stop",
                    policy.digest,
                    json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
                    stop_reason,
                    str(harness._next_seq),
                ]
            )
            stop = write_stop_record(
                root,
                reason=stop_reason,
                policy=policy,
                metrics=metrics,
                event_seq=max(0, harness._next_seq - 1),
            )
    _atomic_json(
        root / "checkpoint.json",
        {
            "schema": "deepreason-checkpoint-v1",
            "manifest_digest": manifest.sha256,
            "stop_digest": stop["digest"],
            "event_seq": harness._next_seq,
        },
    )
    capability_audits = (
        write_tranche_a_audits(root) if manifest.schema_version >= 5 else {}
    )
    payload = _v6_run_result(root, manifest, {
        "schema": "deepreason-run-result-v1",
        "state": "cancelled" if cancelled else "completed",
        "workload": "text",
        "problem_id": problem_id,
        "frontier": result["frontier"],
        "survivors": result["survivors"],
        "display": {
            "status_counts": display_status_counts(harness, manifest),
        },
        "accounting": accounting,
        "capability_accounting": (
            SimulationCapabilityController(harness, manifest).accounting()
            if manifest.schema_version >= 5
            else None
        ),
        "capability_audits": capability_audits,
        "stop": stop,
    }, harness=harness)
    payload = finalize_terminal_result(harness, manifest, payload)
    _atomic_json(root / "run-result.json", payload)
    return payload


def completed_cycles(harness) -> int:
    """How many scheduler cycles a root's own record says it completed.

    Derived from the log rather than from `progress.jsonl`, so a root that
    never had a progress stream still reports an honest stop metric.
    """

    from deepreason.ontology import Rule

    highest = -1
    for event in harness.log.read():
        inputs = tuple(event.inputs)
        if (
            event.rule == Rule.MEASURE
            and len(inputs) >= 2
            and inputs[0] == "cycle"
            and inputs[1].isdigit()
        ):
            highest = max(highest, int(inputs[1]))
    return highest + 1


def workload_spec_for_root(root: Path | str, *, problem_path=None, harness=None):
    """The frozen workload a root's lifecycle documents must describe.

    Preference order is deliberate: an explicit ``--problem`` file, then the
    documents a run root already carries, then a reconstruction from the
    immutable run input.  The reconstruction needs the harness because
    run-input records a commitment's definition, not the registered
    Commitment object the workload spec holds.
    """

    from deepreason.evidence.state import load_evidence_dossier, load_run_input
    from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem

    root = Path(root)
    for candidate in (
        problem_path,
        root / "text-workload.json",
        root / "problem.json",
    ):
        if candidate is None or not Path(candidate).exists():
            continue
        payload = json.loads(Path(candidate).read_text(encoding="utf-8"))
        if (
            isinstance(payload, dict)
            and payload.get("schema") == "deepreason-text-workload-v1"
        ):
            return ReasoningWorkloadSpec.model_validate(payload)
    run_input = load_run_input(root)
    criteria = []
    for item in run_input.problem.criteria:
        commitment = (
            harness.commitments.get(item.id) if harness is not None else None
        )
        if commitment is None:
            raise ValueError(
                "RUN_WORKLOAD_UNRESOLVED: this root records commitment "
                f"{item.id} in its run input but carries no workload document "
                "and no registered commitment to rebuild it from"
            )
        criteria.append(commitment)
    return ReasoningWorkloadSpec(
        problem=WorkloadProblem(
            id=run_input.problem.id, description=run_input.problem.description
        ),
        criteria=tuple(criteria),
        sources=tuple(
            source.id for source in load_evidence_dossier(root).sources
        ),
        allow_rubric=False,
    )


def ensure_lifecycle_documents(root: Path | str, *, spec) -> None:
    """Write the two documents a continuation reads, when they are absent.

    ``continue`` reads ``run-request.json`` and the workload beside it; a
    root that never wrote them refuses with ``RUN_REQUEST_MISSING`` however
    complete the rest of its record is.  Existing bytes are never replaced —
    a differing document is a typed conflict, not an overwrite.
    """

    from deepreason.evidence.state import load_run_input
    from deepreason.runtime.progress import _atomic_json

    root = Path(root)
    request = {
        "schema": "deepreason-run-request-v1",
        "workload": "text",
        "problem": {
            "id": spec.problem.id,
            "description": spec.problem.description,
        },
        "run_input_digest": load_run_input(root).run_input_digest,
    }
    documents = {
        _request_path(root): request,
        root / "text-workload.json": spec.model_dump(mode="json", by_alias=True),
    }
    for target, payload in documents.items():
        if target.exists():
            existing = json.loads(target.read_text(encoding="utf-8"))
            if existing != payload:
                raise ValueError(
                    f"RUN_REQUEST_CONFLICT: {target.name} already binds a "
                    "different workload"
                )
            continue
        _atomic_json(target, payload)


def finalize_stopped_root(root: Path | str) -> dict[str, Any]:
    """Terminalize a root whose run ended without writing a terminal.

    Appends only.  The run's own frontier is re-derived read-only from the
    replayed state, the typed stop receipt and the terminal commitment are
    appended as new events, and every document this writes is a file the
    root did not have.  Nothing already on disk is opened for modification —
    a committed root is immutable, and this is the operation that lets one
    reach ``amend`` without violating that.

    It deliberately does NOT render a bound dossier that the run never
    introduced.  Attached evidence is admissible only ahead of the epoch's
    first model call, so introducing it after the reasoning has happened
    would record a false claim about what the models could see; the honest
    route for a root in that state is an amendment epoch, whose own window
    the records would legitimately precede.
    """

    from deepreason.harness import Harness
    from deepreason.run_manifest import (
        MANIFEST_NAME,
        config_from_run_manifest,
        load_run_manifest,
    )
    from deepreason.runtime.terminal_authority import derive_terminal_authority
    from deepreason.scheduler.scheduler import run_report

    root = Path(root).resolve()
    manifest = load_run_manifest(root / MANIFEST_NAME)
    if manifest.schema_version != 6:
        raise ValueError(
            "FINALIZE_MANIFEST_UNSUPPORTED: finalization requires a "
            "RunManifest v6 root"
        )
    authority = derive_terminal_authority(root, manifest=manifest)
    if authority.current_valid:
        raise ValueError(
            "FINALIZE_ALREADY_TERMINAL: this root already stands at a valid "
            "typed terminal stop"
        )
    if authority.status != "current_open_uncommitted":
        raise ValueError(
            "FINALIZE_AUTHORITY_UNAVAILABLE: terminal authority is "
            f"{authority.status}"
            f"{f', {authority.detail_code}' if authority.detail_code else ''}"
        )
    try:
        locks = operator_locks(root, owner="finalize", blocking=False)
    except ProcessLockBusy as error:
        raise ValueError(
            "FINALIZE_RUN_ACTIVE: another operator owns this run root"
        ) from error
    try:
        harness = Harness(root)
        spec = workload_spec_for_root(root, harness=harness)
        ensure_lifecycle_documents(root, spec=spec)
        # run_report, never the Scheduler's own method: constructing a
        # scheduler performs setup writes that append events (DR-SUB-scheduler
        # names them). Past a recovered stop's horizon those are unauthorized
        # and the root's own terminal check fails
        # TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED. Finalization appends the
        # terminal records and nothing else.
        report = run_report(harness, config_from_run_manifest(manifest))
        return terminalize_text_run(
            harness,
            manifest,
            root=root,
            result={
                "frontier": report["frontier"],
                "survivors": report["survivors"],
                "stop_reason": None,
            },
            accounting={
                "metered_tokens": None,
                "logged_tokens_this_run": 0,
                "delta": None,
                "note": "finalization metered nothing; this invocation made "
                        "no model call",
            },
            problem_id=spec.problem.id,
            latest_cycle=completed_cycles(harness),
        )
    finally:
        locks.release()


def attach_bound_evidence_once(harness, root: Path | str, *, problem_id: str) -> bool:
    """Render this root's bound dossier into source records, at most once.

    Idempotent on the record itself rather than on a flag: a second call
    would introduce each source twice, which replay validation rejects.
    """

    from deepreason.evidence.render import attach_bound_evidence
    from deepreason.evidence.state import load_evidence_dossier, load_run_input

    root = Path(root)
    dossier = load_evidence_dossier(root)
    if not dossier.sources:
        return False
    for artifact in harness.state.artifacts.values():
        provenance = artifact.provenance
        if provenance is not None and getattr(
            provenance.role, "value", provenance.role
        ) == "import":
            return False
    attach_bound_evidence(
        harness,
        run_input=load_run_input(root),
        dossier=dossier,
        problem_id=problem_id,
    )
    return True


def missing_manifest_credentials(manifest) -> list[str]:
    return sorted(
        {
            route.api_key_env
            for routes in manifest.roles.values()
            for route in routes
            if route.api_key_env and not os.environ.get(route.api_key_env)
        }
    )


def _budget_values(budget: RunBudgetIntentV1):
    from deepreason.runtime.budget import parse_limit

    cycles, _ = parse_limit(budget.cycles, optional=False)
    tokens, _ = parse_limit(budget.token_budget)
    token_budget = tokens.value if tokens.mode == "bounded" else None
    scheduler_cycles = cycles.value if cycles.mode == "bounded" else sys.maxsize
    return cycles, tokens, token_budget, int(scheduler_cycles)


def _request_path(root: Path) -> Path:
    return root / "run-request.json"


def _request_for_intent(intent: StartTextRunIntentV1) -> dict[str, Any]:
    spec = intent.workload
    return {
        "schema": "deepreason-run-request-v1",
        "workload": "text",
        "problem": {
            "id": spec.problem.id,
            "description": spec.problem.description,
        },
    }


def _read_request(root: Path) -> dict[str, Any]:
    target = _request_path(root)
    if not target.exists():
        raise ValueError("RUN_REQUEST_MISSING: fixed run-request.json is absent")
    data = json.loads(target.read_text(encoding="utf-8"))
    if (
        not isinstance(data, dict)
        or data.get("schema") != "deepreason-run-request-v1"
        or data.get("workload") != "text"
        or not isinstance(data.get("problem"), dict)
        or not str(data["problem"].get("description") or "").strip()
    ):
        raise ValueError("RUN_REQUEST_INVALID: fixed run request is not valid text input")
    # An amendment epoch supersedes the question in place: the newest epoch's
    # workload is what a continuation must run, while the root's original
    # request stays exactly as it was written.
    from deepreason.amendment.state import current_epoch, epoch_workload_path

    epoch = current_epoch(root)
    amended = epoch > 0 and epoch_workload_path(root, epoch).exists()
    workload_path = (
        epoch_workload_path(root, epoch) if amended else root / "text-workload.json"
    )
    if workload_path.exists():
        spec = json.loads(workload_path.read_text(encoding="utf-8"))
        data["workload_spec"] = spec
        if amended:
            # Only an amendment epoch may restate the question, and only from
            # its own durable workload. Epoch 0 keeps the original strict
            # request/workload agreement check in _spec_from_request.
            data["problem"] = {
                "id": spec["problem"]["id"],
                "description": spec["problem"]["description"],
            }
    return data


def _spec_from_request(request: dict[str, Any]):
    from deepreason.workloads.text import (
        ReasoningWorkloadSpec,
        WorkloadProblem,
        spec_from_text,
    )

    encoded = request.get("workload_spec")
    if encoded is not None:
        spec = ReasoningWorkloadSpec.model_validate(encoded)
        if (
            spec.problem.id != request["problem"].get("id")
            or spec.problem.description != request["problem"]["description"]
        ):
            raise ValueError("RUN_REQUEST_INVALID: workload spec differs from problem")
        return spec
    spec = spec_from_text(request["problem"]["description"])
    if request["problem"].get("id"):
        spec = spec.model_copy(
            update={
                "problem": WorkloadProblem(
                    id=request["problem"]["id"],
                    description=request["problem"]["description"],
                )
            }
        )
    return spec


def _run_input_matches_spec(run_input, spec) -> bool:
    """Compare the complete frozen v6 workload authority."""

    from deepreason.evidence.models import (
        RunInputCommitmentV1,
        RunInputManifestV2,
    )

    return (
        isinstance(run_input, RunInputManifestV2)
        and run_input.problem.id == spec.problem.id
        and run_input.problem.description == spec.problem.description
        and run_input.problem.criteria
        == tuple(
            RunInputCommitmentV1.from_commitment(item)
            for item in spec.criteria
        )
    )



class TextRunApplicationService:
    """Own text lifecycle, scheduler dispatch, progress, result, and cancel."""

    def __init__(self, registry: TextRunWorkerRegistry | None = None) -> None:
        self.registry = registry or TEXT_RUN_WORKERS
        self._outstanding_cache: dict[str, tuple[tuple, OutstandingWorkResultV1]] = {}
        self._outstanding_cache_lock = threading.Lock()

    def start(
        self,
        intent: StartTextRunIntentV1,
        *,
        progress_callback: Callable[[dict], None] | None = None,
        credential_checker: Callable[[Any], list[str]] = missing_manifest_credentials,
        manifest_override=None,
    ) -> RunStartedV1:
        from deepreason.run_manifest import load_run_manifest

        intent = StartTextRunIntentV1.model_validate(intent)
        manifest = (
            manifest_override
            if manifest_override is not None
            else load_run_manifest(intent.run_manifest_ref)
        )
        return self._launch(
            root=Path(intent.root).resolve(),
            budget=intent.budget,
            manifest=manifest,
            request=_request_for_intent(intent),
            spec_override=intent.workload,
            continuation=False,
            expected_manifest_digest=None,
            progress_callback=progress_callback,
            credential_checker=credential_checker,
        )

    def start_manifest_run(
        self,
        *,
        root: Path | str,
        manifest,
        problem_path: Path | str | None = None,
        cycles,
        token_budget=None,
        progress_callback: Callable[[dict], None] | None = None,
        credential_checker: Callable[[Any], list[str]] = missing_manifest_credentials,
    ) -> RunStartedV1:
        """Start a run from a manifest and a root the caller already holds.

        The entry for every configuration a compiled manifest can express
        — role ensembles, route-bound seats, adjudication policy — none of
        which this method or ``_launch``
        inspects.  That is why no configuration the compiler emits can be
        refused here for its SHAPE: whatever ``start`` refuses this
        refuses identically, because it IS ``start``.  A second entry that
        validated manifests of its own would be the second admission gate
        this consolidation exists to remove.
        """

        from deepreason.application.intents import start_text_run_intent
        from deepreason.run_manifest import (
            MANIFEST_NAME,
            RunManifest,
            load_run_manifest,
        )

        root = Path(root).resolve()
        held = isinstance(manifest, RunManifest)
        resolved = manifest if held else load_run_manifest(manifest)
        # Reconstructing a spec from the frozen run input needs the
        # registered commitments, and read-only is the only admissible
        # way to read them here: `_launch`, not this method, decides
        # whether the root may be written to at all.
        harness = None
        if (root / "log.jsonl").exists():
            from deepreason.harness import Harness

            harness = Harness(root, read_only=True)
        spec = workload_spec_for_root(
            root,
            problem_path=None if problem_path is None else Path(problem_path),
            harness=harness,
        )
        return self.start(
            start_text_run_intent(
                root=str(root),
                workload=spec,
                run_manifest_ref=str(root / MANIFEST_NAME if held else manifest),
                cycles=cycles,
                # An absent ceiling is "unlimited" in the intent
                # vocabulary; `run --token-budget` spells it as None.
                token_budget="unlimited" if token_budget is None else token_budget,
            ),
            progress_callback=progress_callback,
            credential_checker=credential_checker,
            manifest_override=resolved,
        )

    def continue_run(
        self,
        intent: ContinueTextRunIntentV1,
        *,
        progress_callback: Callable[[dict], None] | None = None,
        credential_checker: Callable[[Any], list[str]] = missing_manifest_credentials,
    ) -> RunStartedV1:
        from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

        intent = ContinueTextRunIntentV1.model_validate(intent)
        root = Path(intent.root).resolve()
        manifest = load_run_manifest(root / MANIFEST_NAME)
        if (
            intent.expected_manifest_digest is not None
            and intent.expected_manifest_digest != manifest.sha256
        ):
            raise ValueError("CONTINUE_MANIFEST_MISMATCH")
        return self._launch(
            root=root,
            budget=intent.budget,
            manifest=manifest,
            request=_read_request(root),
            spec_override=None,
            continuation=True,
            expected_manifest_digest=manifest.sha256,
            progress_callback=progress_callback,
            credential_checker=credential_checker,
        )

    def inspect(self, intent: InspectTextRunIntentV1) -> RunProgressResultV1:
        from deepreason.ui.status import read_run_status

        intent = InspectTextRunIntentV1.model_validate(intent)
        payload = read_run_status(
            Path(intent.root).resolve(), since_seq=int(intent.since_seq)
        )
        root = Path(intent.root).resolve()
        payload["outstanding_work"] = (
            self.inspect_outstanding_work(root).presentation_payload()
            if root.is_dir()
            else None
        )
        return RunProgressResultV1(
            lifecycle=str(payload.get("state", "not-started")), payload=payload
        )

    def inspect_outstanding_work(
        self, root: Path | str
    ) -> OutstandingWorkResultV1:
        """Project replayed authority only; never rerun a reducer or scheduler."""

        from deepreason.harness import Harness
        from deepreason.run_manifest import MANIFEST_NAME

        resolved = Path(root).resolve()
        # A full replay per status poll is O(run length) and starves the
        # worker's own terminalization replays on slow filesystems. The log
        # is append-only and the projection is a pure function of it, so
        # identical durable inputs may reuse the previous projection.
        # (Storage revalidation still happens on every input change and on
        # every result read; a stale-input cache hit only skips re-raising
        # for corruption introduced without any input change.)
        def _identity(name: str) -> tuple | None:
            try:
                observed = (resolved / name).stat()
            except OSError:
                return None
            return (observed.st_size, observed.st_mtime_ns, observed.st_ino)

        key = tuple(
            _identity(name)
            for name in ("log.jsonl", "workflow-checkpoint.json", MANIFEST_NAME)
        )
        cache_id = str(resolved)
        with self._outstanding_cache_lock:
            cached = self._outstanding_cache.get(cache_id)
            if cached is not None and cached[0] == key:
                return cached[1]

        harness = Harness(resolved, read_only=True)
        workflow = harness.workflow_state
        items = []
        for work_id in workflow.outstanding_work_order_ids:
            transaction = workflow.transaction_work.get(work_id)
            if transaction is not None:
                preparation = transaction.preparation
                lease = preparation.route_lease
                if transaction.admissions:
                    recovery = "semantic_admission_recorded"
                elif transaction.provider_attempts:
                    outcomes = {
                        attempt.outcome
                        for attempt in transaction.provider_attempts.values()
                    }
                    recovery = (
                        "provider_result_received"
                        if outcomes == {"provider_result"}
                        else "transport_failure_received"
                    )
                elif transaction.issued:
                    recovery = "issued"
                else:
                    recovery = "prepared"
                items.append(
                    OutstandingWorkItemProjectionV1(
                        work_order_id=work_id,
                        recovery=recovery,
                        role=lease.role,
                        seat=lease.seat,
                        endpoint_id=lease.endpoint_id,
                        route_digest=lease.route_sha256,
                        contract_id=preparation.contract_id,
                        reserved_tokens=(
                            transaction.reservation.reserved_tokens
                            if transaction.reservation is not None
                            else 0
                        ),
                        provider_calls_used=len(transaction.provider_attempts),
                        provider_calls_limit=1,
                        local_repairs_used=0,
                        local_repairs_limit=0,
                        context_expansions_used=0,
                        context_expansions_limit=0,
                    )
                )
                continue
            work = workflow.work_orders[work_id]
            branch_id = workflow.work_to_branch[work_id]
            state = workflow.branches[branch_id].process_state.work_item(work_id)
            if state is None:
                raise ValueError("outstanding workflow work has no replayed state")
            grant = work.capability_grant
            lease = work.route_lease
            items.append(
                OutstandingWorkItemProjectionV1(
                    work_order_id=work_id,
                    recovery=workflow.recovery_status(work_id).value,
                    role=lease.role,
                    seat=lease.seat,
                    endpoint_id=lease.endpoint_id,
                    route_digest=lease.route_sha256,
                    contract_id=work.contract_id,
                    reserved_tokens=state.reserved_tokens,
                    provider_calls_used=state.provider_calls_used,
                    provider_calls_limit=grant.max_provider_calls,
                    local_repairs_used=state.local_repairs_used,
                    local_repairs_limit=grant.max_local_repairs,
                    context_expansions_used=state.context_expansions_used,
                    context_expansions_limit=grant.remaining_context_expansions,
                )
            )
        projection = OutstandingWorkResultV1(
            process_digest=workflow.digest,
            last_control_seq=(
                max(workflow.event_seqs) if workflow.event_seqs else -1
            ),
            work=tuple(items),
        )
        with self._outstanding_cache_lock:
            while len(self._outstanding_cache) >= 16:
                self._outstanding_cache.pop(next(iter(self._outstanding_cache)))
            self._outstanding_cache[cache_id] = (key, projection)
        return projection

    def result(self, intent: InspectTextRunIntentV1) -> TextRunTerminalResultV1:
        intent = InspectTextRunIntentV1.model_validate(intent)
        root = Path(intent.root).resolve()
        target = root / "run-result.json"
        from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

        manifest_path = root / MANIFEST_NAME
        if manifest_path.exists() or not target.exists():
            from deepreason.runtime.progress import _atomic_json
            from deepreason.runtime.terminal_authority import (
                derive_terminal_authority,
                recover_terminal_result,
            )

            manifest = load_run_manifest(manifest_path)
            if manifest.schema_version == 6:
                _require_v6_manifest(manifest, operation="run result recovery")
                with self.registry.lock:
                    if self.registry.live(root) is not None:
                        raise ValueError(
                            "RUN_RESULT_NOT_READY: terminalization remains active"
                        )
                # Recovery runs outside the registry lock: it replays the
                # full event log, and holding the process-wide lock for that
                # long serializes every start/cancel/result for every root
                # behind one slow reader. Concurrency safety comes from the
                # durable authority itself — the terminal-commitment lock
                # plus the epoch-regression guard inside
                # recover_terminal_result — which also covers workers in
                # other processes that this registry cannot see.
                from deepreason.harness import Harness

                recovered = recover_terminal_result(Harness(root), manifest)
                if recovered is not None:
                    try:
                        durable = json.loads(target.read_text(encoding="utf-8"))
                    except (
                        FileNotFoundError,
                        OSError,
                        UnicodeError,
                        json.JSONDecodeError,
                    ):
                        durable = None
                    if durable != recovered:
                        _atomic_json(target, recovered)
                elif manifest.terminal_commitment_policy is not None:
                    authority = derive_terminal_authority(
                        root,
                        manifest=manifest,
                    )
                    if authority.status != "operational_abort":
                        lifecycle = self.inspect(intent).lifecycle
                        raise ValueError(
                            "RUN_RESULT_NOT_READY: current terminalization is "
                            f"{lifecycle}"
                        )
        if not target.exists():
            load_run_manifest(manifest_path)
            lifecycle = self.inspect(intent).lifecycle
            raise ValueError(f"RUN_RESULT_NOT_READY: current state is {lifecycle}")
        try:
            if target.is_symlink() or not 2 <= target.stat().st_size <= 4 * 1024 * 1024:
                raise ValueError("RUN_RESULT_INVALID")
            payload = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("RUN_RESULT_INVALID") from error
        if not isinstance(payload, dict) or payload.get("schema") not in {
            "deepreason-run-result-v1",
            "deepreason-run-result-v2",
        }:
            raise ValueError("RUN_RESULT_INVALID")
        if payload.get("schema") == "deepreason-run-result-v2":
            try:
                payload = RunResultV2.model_validate(payload).model_dump(
                    mode="json", by_alias=True, exclude_none=True
                )
            except ValueError as error:
                raise ValueError("RUN_RESULT_INVALID") from error
        lifecycle = str(payload.get("state") or "")
        if lifecycle not in {"completed", "cancelled", "failed"}:
            raise ValueError("RUN_RESULT_INVALID")
        return TextRunTerminalResultV1(lifecycle=lifecycle, payload=payload)

    def cancel(self, intent: CancelTextRunIntentV1) -> RunCancellationAcceptedV1:
        from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
        from deepreason.runtime.progress import ProgressSink

        intent = CancelTextRunIntentV1.model_validate(intent)
        root = Path(intent.root).resolve()
        manifest = load_run_manifest(root / MANIFEST_NAME)
        _require_v6_manifest(manifest, operation="run cancellation")
        with self.registry.lock:
            lifecycle = self.inspect(
                InspectTextRunIntentV1(root=str(root))
            ).lifecycle
            if lifecycle not in {"starting", "running"}:
                raise ValueError(f"RUN_NOT_ACTIVE: current state is {lifecycle}")
            outstanding = self.inspect_outstanding_work(root)
            intent_path = root / "operator-intents.jsonl"
            prior = []
            if intent_path.exists():
                prior = [
                    OperatorCancellationIntentV1.model_validate_json(line)
                    for line in intent_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                if [item.sequence for item in prior] != list(range(len(prior))):
                    raise ValueError("operator intent sequence is not contiguous")
            record = OperatorCancellationIntentV1.create(
                sequence=len(prior),
                manifest_digest=manifest.sha256,
                process_digest=outstanding.process_digest,
                last_control_seq=outstanding.last_control_seq,
            )
            with intent_path.open("a", encoding="utf-8") as stream:
                stream.write(record.model_dump_json(by_alias=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            # The durable typed intent precedes the compatibility flag.  The
            # scheduler/controller still decides when the safe boundary lands.
            ProgressSink(
                root,
                run_id=manifest.sha256,
                workload=manifest.workload_profile or "text",
            ).request_cancel()
        return RunCancellationAcceptedV1(root=str(root))

    def watch(self, intent: WatchTextRunIntentV1) -> Iterator[RunProgressResultV1]:
        intent = WatchTextRunIntentV1.model_validate(intent)
        terminal = {"completed", "failed", "cancelled", "paused"}
        while True:
            snapshot = self.inspect(InspectTextRunIntentV1(root=intent.root))
            yield snapshot
            if intent.once or snapshot.lifecycle in terminal:
                return
            time.sleep(intent.interval)

    def wait(self, root: Path | str, timeout: float | None = None) -> None:
        self.registry.join(root, timeout=timeout)

    def _launch(
        self,
        *,
        root: Path,
        budget: RunBudgetIntentV1,
        manifest,
        request: dict[str, Any],
        spec_override,
        continuation: bool,
        expected_manifest_digest: str | None,
        progress_callback,
        credential_checker,
    ) -> RunStartedV1:
        from deepreason.ops import require_full_engine
        from deepreason.run_manifest import bind_run_manifest, preflight_payload
        from deepreason.runtime.continuation import prepare_continuation
        from deepreason.runtime.launch_policy import (
            require_v6_launch_allowed,
            require_v6_production_qualification,
            resolve_effective_run_manifest,
        )
        from deepreason.runtime.progress import ProgressSink, _atomic_json

        cycles, tokens, token_budget, scheduler_cycles = _budget_values(budget)
        require_v6_launch_allowed(manifest, operation="text reasoning")
        require_full_engine(manifest, workload="text reasoning")
        manifest = resolve_effective_run_manifest(
            manifest,
            root=root,
            operation="text reasoning",
            require_bound_manifest=continuation,
        )
        assert manifest is not None
        _require_v6_manifest(manifest, operation="text reasoning")
        if manifest.workload_profile != "text":
            raise ValueError(
                "RUN_MANIFEST_WORKLOAD_MISMATCH: start_run requires a v6 text manifest"
            )
        spec = spec_override or _spec_from_request(request)
        from deepreason.evidence.state import load_run_input, verify_run_input
        from deepreason.run_manifest import RunManifestError

        verified_input = verify_run_input(root)
        if verified_input.get("input_schema_version", 1) != 2:
            raise RunManifestError(
                "RUN_INPUT_SCHEMA_MISMATCH",
                "RunManifest v6 requires run-input manifest v2",
                "/run-input.json/schema",
            )
        run_input = load_run_input(root)
        # The manifest names the run's one input identity for its whole life;
        # an amendment epoch supersedes the question and the evidence behind a
        # fence, so the spec is checked against the current epoch's records
        # and the identity anchor against the root's.
        from deepreason.amendment.state import (
            current_epoch,
            load_epoch_dossier,
            load_epoch_run_input,
        )

        epoch = current_epoch(root)
        epoch_input = load_epoch_run_input(root, epoch)
        epoch_dossier = load_epoch_dossier(root, epoch)
        if (
            verified_input["run_input_digest"] != manifest.run_input_digest
            or run_input.run_input_digest != manifest.run_input_digest
            or not _run_input_matches_spec(epoch_input, spec)
            or epoch_dossier.dossier_digest != epoch_input.evidence_dossier_digest
            or epoch_dossier.problem_ref != spec.problem.id
        ):
            raise ValueError(
                "RUN_INPUT_MISMATCH: text request differs from the frozen "
                "v6 run input"
            )
        request = {**request, "run_input_digest": run_input.run_input_digest}
        require_v6_production_qualification(
            manifest,
            root=root,
            operation="text reasoning",
        )
        preflight_payload(
            manifest,
            {
                "problem": {"description": spec.problem.description},
                "commitments": [
                    item.model_dump(mode="json") for item in spec.criteria
                ],
            },
        )
        def notify(event) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback(event.model_dump(mode="json"))
            except Exception:
                pass

        with self.registry.lock:
            if self.registry.live(root) is not None:
                raise ValueError("RUN_ALREADY_RUNNING: this root has an active run")
            try:
                locks = operator_locks(root, owner="run", blocking=False)
            except ProcessLockBusy as error:
                raise ValueError(
                    "RUN_ALREADY_RUNNING: another operator owns this run root"
                ) from error
            try:
                missing = credential_checker(manifest)
                if missing:
                    raise ValueError(
                        "RUN_CREDENTIAL_MISSING: required environment variable(s) "
                        "are unset: " + ", ".join(missing)
                    )
                if continuation:
                    continuation_record = prepare_continuation(
                        root,
                        cycles=cycles,
                        tokens=tokens,
                        expected_manifest_digest=expected_manifest_digest,
                        check_operator_lock=False,
                    )
                    progress = ProgressSink(
                        root, run_id=manifest.sha256, workload="text"
                    )
                else:
                    if (root / "progress.jsonl").exists() or (
                        root / "run-result.json"
                    ).exists():
                        raise ValueError(
                            "RUN_ALREADY_STARTED: choose a fresh root or continue_run"
                        )
                    bind_run_manifest(manifest, root)
                    _atomic_json(_request_path(root), request)
                    _atomic_json(
                        root / "text-workload.json",
                        spec.model_dump(mode="json", by_alias=True),
                    )
                    progress = ProgressSink(
                        root, run_id=manifest.sha256, workload="text"
                    )
                    progress.clear_cancellation()
                    initial = progress.emit(
                        state="starting",
                        phase="manifest",
                        activity="bound",
                        token_limit=token_budget,
                        determinate=False,
                        message="immutable text manifest bound",
                    )
                    notify(initial)
                    continuation_record = None
            except BaseException:
                locks.release()
                raise

            thread = threading.Thread(
                target=self._worker,
                kwargs={
                    "root": root,
                    "manifest": manifest,
                    "spec": spec,
                    "scheduler_cycles": scheduler_cycles,
                    "token_budget": token_budget,
                    "continuation": continuation,
                    "continuation_record": continuation_record,
                    "progress": progress,
                    "notify": notify,
                    "locks": locks,
                },
                name=f"deepreason-run-{manifest.sha256[:8]}",
                daemon=True,
            )
            self.registry.put(root, thread)
            try:
                thread.start()
            except BaseException:
                self.registry.discard(root)
                locks.release()
                raise
        return RunStartedV1(
            root=str(root), manifest_digest=manifest.sha256
        )

    @staticmethod
    def _worker(
        *,
        root,
        manifest,
        spec,
        scheduler_cycles,
        token_budget,
        continuation,
        continuation_record,
        progress,
        notify,
        locks,
    ) -> None:
        from deepreason.harness import Harness
        from deepreason.ops import run_scheduler
        from deepreason.run_manifest import config_from_run_manifest
        from deepreason.runtime.progress import _atomic_json
        from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record
        from deepreason.runtime.terminal_authority import finalize_terminal_result
        from deepreason.status_display import display_status_counts
        from deepreason.workloads.text import seed_reasoning_workload

        harness = None
        latest_cycle = 0
        try:
            harness = Harness(root)
            if continuation:
                if spec.problem.id not in harness.state.problems:
                    raise ValueError(
                        "CONTINUE_PROBLEM_MISSING: seeded problem is absent"
                    )
                harness.record_measure(
                    inputs=[
                        "run-resume",
                        continuation_record["prior_stop_digest"],
                        manifest.sha256,
                    ]
                )
            else:
                seed_reasoning_workload(harness, spec)
                if manifest.schema_version >= 5:
                    from deepreason.evidence.render import attach_bound_evidence
                    from deepreason.evidence.state import (
                        load_evidence_dossier,
                        load_run_input,
                    )

                    attach_bound_evidence(
                        harness,
                        run_input=load_run_input(root),
                        dossier=load_evidence_dossier(root),
                        problem_id=spec.problem.id,
                    )
            prior = progress.read_since(-1)
            base_cycle = max((event.cycle for event in prior), default=0)
            base_token_spend = sum(
                event.llm.tokens for event in harness.log.read() if event.llm
            )
            display_token_limit = (
                None if token_budget is None else base_token_spend + token_budget
            )
            loaded = progress.emit(
                state="running",
                phase="workload",
                activity="loaded",
                cycle=base_cycle,
                problem_id=spec.problem.id,
                token_spend=base_token_spend,
                token_limit=display_token_limit,
                determinate=False,
                display_status_counts=display_status_counts(harness, manifest),
            )
            notify(loaded)

            def on_cycle(scheduler):
                nonlocal latest_cycle
                latest_cycle = base_cycle + scheduler._cycles
                counts = {name: 0 for name in ("accepted", "refuted", "suspended")}
                for label in scheduler.harness.state.status.values():
                    if label.value in counts:
                        counts[label.value] += 1
                report = scheduler.report()
                token_spend = sum(
                    event.llm.tokens
                    for event in scheduler.harness.log.read()
                    if event.llm
                )
                event = progress.emit(
                    state="running",
                    phase="reasoning",
                    activity="cycle complete",
                    cycle=latest_cycle,
                    problem_id=spec.problem.id,
                    frontier_size=len(report["frontier"]),
                    accepted=counts["accepted"],
                    refuted=counts["refuted"],
                    suspended=counts["suspended"],
                    display_status_counts=display_status_counts(
                        scheduler.harness, manifest
                    ),
                    token_spend=token_spend,
                    token_limit=display_token_limit,
                    determinate=False,
                )
                notify(event)
                return progress.cancellation_requested()

            result, _meter, accounting = run_scheduler(
                harness,
                config_from_run_manifest(manifest),
                scheduler_cycles,
                token_budget,
                on_cycle=on_cycle,
                run_manifest=manifest,
                progress_sink=progress,
            )
            cancelled = progress.cancellation_requested()
            payload = terminalize_text_run(
                harness,
                manifest,
                root=root,
                result=result,
                accounting=accounting,
                problem_id=spec.problem.id,
                cancelled=cancelled,
                latest_cycle=latest_cycle,
            )
            stop_reason = payload["stop"]["reason"]
            terminal = progress.emit(
                state=payload["state"],
                phase="stop",
                activity=stop_reason,
                cycle=latest_cycle,
                problem_id=spec.problem.id,
                token_spend=sum(
                    event.llm.tokens for event in harness.log.read() if event.llm
                ),
                token_limit=display_token_limit,
                determinate=False,
                stop_reason=stop_reason,
                display_status_counts=display_status_counts(harness, manifest),
            )
            notify(terminal)
        except (Exception, SystemExit) as error:
            if harness is None:
                try:
                    _atomic_json(
                        root / "run-result.json",
                        _v6_run_result(root, manifest, {
                            "schema": "deepreason-run-result-v1",
                            "state": "failed",
                            "workload": "text",
                            "error_type": type(error).__name__,
                            "error": str(error)[:2000],
                        }),
                    )
                    failed = progress.emit(
                        state="failed",
                        phase="stop",
                        activity="operational failure",
                        cycle=0,
                        token_limit=token_budget,
                        determinate=False,
                        message=str(error)[:500],
                        stop_reason="operational_failure",
                    )
                    notify(failed)
                except Exception:
                    pass
                return
            if harness.workflow_state.current_terminal_commitment is not None:
                try:
                    failed = progress.emit(
                        state="failed",
                        phase="stop",
                        activity="terminal publication recovery required",
                        cycle=latest_cycle,
                        token_limit=token_budget,
                        determinate=False,
                        message="TERMINAL_PUBLICATION_RECOVERY_REQUIRED",
                        stop_reason="operational_failure",
                    )
                    notify(failed)
                except Exception:
                    pass
                return
            policy = StopPolicy()
            metrics = StopMetrics(cycle=latest_cycle)
            try:
                harness.record_measure(
                    inputs=[
                        "run-stop",
                        policy.digest,
                        json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
                        "operational_failure",
                        str(harness._next_seq),
                    ]
                )
                stop = write_stop_record(
                    root,
                    reason="operational_failure",
                    policy=policy,
                    metrics=metrics,
                    event_seq=max(0, harness._next_seq - 1),
                )
                _atomic_json(
                    root / "checkpoint.json",
                    {
                        "schema": "deepreason-checkpoint-v1",
                        "manifest_digest": manifest.sha256,
                        "stop_digest": stop["digest"],
                        "event_seq": harness._next_seq,
                    },
                )
                payload = _v6_run_result(root, manifest, {
                    "schema": "deepreason-run-result-v1",
                    "state": "failed",
                    "workload": "text",
                    "error_type": type(error).__name__,
                    "error": str(error)[:2000],
                    "stop": stop,
                }, harness=harness)
                payload = finalize_terminal_result(harness, manifest, payload)
                _atomic_json(root / "run-result.json", payload)
                failed = progress.emit(
                    state="failed",
                    phase="stop",
                    activity="operational failure",
                    cycle=latest_cycle,
                    token_limit=token_budget,
                    determinate=False,
                    message=str(error)[:500],
                    stop_reason="operational_failure",
                )
                notify(failed)
            except Exception:
                pass
        finally:
            locks.release()


TEXT_RUN_SERVICE = TextRunApplicationService()


__all__ = [
    "TEXT_RUN_SERVICE",
    "TEXT_RUN_WORKERS",
    "TextRunApplicationService",
    "TextRunWorkerRegistry",
    "_v6_run_result",
    "attach_bound_evidence_once",
    "completed_cycles",
    "ensure_lifecycle_documents",
    "finalize_stopped_root",
    "missing_manifest_credentials",
    "terminalize_text_run",
    "workload_spec_for_root",
]
