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


def _check_experimental_v5(manifest, enabled: bool) -> None:
    """Fail closed while the legacy CLI flag awaits removal in G02."""

    _require_v6_manifest(manifest, operation="full scheduler")
    if enabled:
        from deepreason.run_manifest import RunManifestError

        raise RunManifestError(
            "EXPERIMENTAL_V5_UNSUPPORTED",
            "experimental_v5 cannot enable a historical execution path",
            "/experimental_v5",
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
    workload_path = root / "text-workload.json"
    if workload_path.exists():
        data["workload_spec"] = json.loads(
            workload_path.read_text(encoding="utf-8")
        )
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

        harness = Harness(Path(root).resolve(), read_only=True)
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
        return OutstandingWorkResultV1(
            process_digest=workflow.digest,
            last_control_seq=(
                max(workflow.event_seqs) if workflow.event_seqs else -1
            ),
            work=tuple(items),
        )

    def result(self, intent: InspectTextRunIntentV1) -> TextRunTerminalResultV1:
        intent = InspectTextRunIntentV1.model_validate(intent)
        root = Path(intent.root).resolve()
        target = root / "run-result.json"
        try:
            target.lstat()
        except FileNotFoundError:
            from deepreason.harness import Harness
            from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
            from deepreason.runtime.progress import _atomic_json
            from deepreason.runtime.terminal_authority import (
                recover_terminal_result,
            )

            manifest = load_run_manifest(root / MANIFEST_NAME)
            _require_v6_manifest(manifest, operation="run result recovery")
            recovered = recover_terminal_result(Harness(root), manifest)
            if recovered is not None:
                _atomic_json(target, recovered)
        if not target.exists():
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
        from deepreason.evidence.state import (
            load_evidence_dossier,
            load_run_input,
            verify_run_input,
        )
        from deepreason.run_manifest import RunManifestError

        verified_input = verify_run_input(root)
        if verified_input.get("input_schema_version", 1) != 2:
            raise RunManifestError(
                "RUN_INPUT_SCHEMA_MISMATCH",
                "RunManifest v6 requires run-input manifest v2",
                "/run-input.json/schema",
            )
        run_input = load_run_input(root)
        dossier = load_evidence_dossier(root)
        if (
            verified_input["run_input_digest"] != manifest.run_input_digest
            or run_input.run_input_digest != manifest.run_input_digest
            or not _run_input_matches_spec(run_input, spec)
            or dossier.dossier_digest != run_input.evidence_dossier_digest
            or dossier.problem_ref != spec.problem.id
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
        from deepreason.status_display import display_status_counts
        from deepreason.workloads.text import seed_reasoning_workload
        from deepreason.capabilities.audit import write_tranche_a_audits
        from deepreason.capabilities.simulation import SimulationCapabilityController

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
            scheduler_reason = result.get("stop_reason")
            stop_reason = (
                "operator_cancelled"
                if cancelled
                else scheduler_reason or "budget_exhausted"
            )
            if scheduler_reason and not cancelled:
                stop = json.loads((root / "run-stop.json").read_text())
            else:
                policy = StopPolicy()
                metrics = StopMetrics(cycle=latest_cycle)
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
                write_tranche_a_audits(root)
                if manifest.schema_version >= 5
                else {}
            )
            payload = _v6_run_result(root, manifest, {
                "schema": "deepreason-run-result-v1",
                "state": "cancelled" if cancelled else "completed",
                "workload": "text",
                "problem_id": spec.problem.id,
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
            _atomic_json(root / "run-result.json", payload)
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
    "missing_manifest_credentials",
]
