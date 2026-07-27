"""Replay-only materialization for durable workflow authority transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from pydantic import BaseModel

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.control_events import (
    ControlEventPayloadV1,
    ControlEventPayloadV2,
    ControlEventPayloadV3,
)
from deepreason.run_manifest import (
    resolve_route_seat_contract_decomposition,
    resolve_route_seat_base_profile,
    resolve_route_seat_behavioral_capability,
)
from deepreason.workflow.models import (
    CapabilityOutcome,
    GuardFindingOutcome,
    GuardResultV1,
    ProposalReceiptV1,
    ProposalValidationOutcome,
    RepairWorkOrderV1,
    RunTerminalCommitmentV1,
    RunTerminalResultDraftV1,
    StopMetricsObservationV1,
    TransitionDecisionV1,
    TransitionKind,
    WorkOrderEnvelopeV1,
    WorkflowLifecycleDecisionV1,
    WorkflowLifecycleSnapshotV1,
    WorkflowResumeDecisionV1,
    WorkflowTaskKind,
    repair_attempt_trigger_ref,
)
from deepreason.workflow.state import (
    WorkItemStatus,
    WorkflowProcessStateV1,
    apply_decision,
)
from deepreason.workflow.transaction import (
    CompactRecoveryTransitionV1,
    ContractDecompositionCompletionV1,
    ContractDecompositionTransitionV1,
    ContextExposureReceiptV2,
    ContextPackPlanV1,
    DispatchAuthorizationBundleV1,
    ModelClassificationBindingV1,
    ProviderAttemptV1,
    RouteSeatInsufficientCapabilityV1,
    RouteSeatModelClassificationPlanV1,
    SemanticAdmissionV1,
    TokenReservationV2,
    WorkLifecycleTransitionV1,
    WorkPreparationV1,
    WorkTerminalV1,
    WorkTransitionKind,
)


ControlEventPayload = (
    ControlEventPayloadV1 | ControlEventPayloadV2 | ControlEventPayloadV3
)


_SCHEMA_MODELS = {
    "workflow-work-order": WorkOrderEnvelopeV1,
    "workflow-repair-work-order": RepairWorkOrderV1,
    "workflow-proposal-receipt": ProposalReceiptV1,
    "workflow-guard-result": GuardResultV1,
    "workflow-transition-decision": TransitionDecisionV1,
    "workflow-stop-metrics-observation": StopMetricsObservationV1,
    "workflow-lifecycle-snapshot": WorkflowLifecycleSnapshotV1,
    "workflow-lifecycle-decision": WorkflowLifecycleDecisionV1,
    "workflow-resume-decision": WorkflowResumeDecisionV1,
    "workflow-run-terminal-commitment-v1": RunTerminalCommitmentV1,
    "workflow-run-terminal-result-draft-v1": RunTerminalResultDraftV1,
    "workflow-work-preparation-v1": WorkPreparationV1,
    "workflow-context-pack-plan-v1": ContextPackPlanV1,
    "workflow-token-reservation-v2": TokenReservationV2,
    "workflow-context-exposure-v2": ContextExposureReceiptV2,
    "workflow-dispatch-authorization-v1": DispatchAuthorizationBundleV1,
    "workflow-provider-attempt-v1": ProviderAttemptV1,
    "workflow-semantic-admission-v1": SemanticAdmissionV1,
    "workflow-compact-recovery-transition-v1": CompactRecoveryTransitionV1,
    "workflow-contract-decomposition-transition-v1": (
        ContractDecompositionTransitionV1
    ),
    "workflow-contract-decomposition-completion-v1": (
        ContractDecompositionCompletionV1
    ),
    "workflow-route-seat-insufficient-capability-v1": (
        RouteSeatInsufficientCapabilityV1
    ),
    "workflow-work-terminal-v1": WorkTerminalV1,
    "workflow-work-lifecycle-transition-v1": WorkLifecycleTransitionV1,
    "workflow-route-seat-model-classification-plan-v1": (
        RouteSeatModelClassificationPlanV1
    ),
    "workflow-model-classification-binding-v1": ModelClassificationBindingV1,
}
_PROVIDER_TRANSITIONS = {
    TransitionKind.PROPOSAL_RECEIVED,
    TransitionKind.REPAIR_EXHAUSTED,
}
_VALID_PROPOSAL_OUTCOMES = {
    ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
    ProposalValidationOutcome.VALID_AFTER_REPAIR,
}
_FAILED_PROPOSAL_OUTCOMES = {
    ProposalValidationOutcome.REPAIR_EXHAUSTED,
    ProposalValidationOutcome.TRANSPORT_FAILED,
}
_GUARDED_TRANSITIONS = {
    TransitionKind.PROPOSAL_ADMITTED,
    TransitionKind.PROPOSAL_REJECTED,
    TransitionKind.PROPOSAL_DEDUPLICATED,
}


class WorkflowRecoveryStatus(str, Enum):
    ENABLED = "enabled"
    ISSUED = "issued"
    PROVIDER_RESULT_RECEIVED = "provider_result_received"
    REPAIR_PENDING = "repair_pending"
    CONTEXT_PENDING = "context_pending"
    FINISHED = "finished"
    ABANDONED = "abandoned"


@dataclass
class WorkflowBranchState:
    branch_id: str
    process_state: WorkflowProcessStateV1
    work_order_ids: list[str] = field(default_factory=list)
    decision_ids: list[str] = field(default_factory=list)
    event_seqs: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class _PlannedApply:
    decision: TransitionDecisionV1
    work_order: WorkOrderEnvelopeV1
    repair_work_order: RepairWorkOrderV1 | None
    proposal: ProposalReceiptV1 | None
    guard: GuardResultV1 | None
    branch_id: str
    next_state: WorkflowProcessStateV1
    new_branch: bool


def _canonical(model_type, value):
    payload = (
        value.model_dump(mode="python", by_alias=True)
        if isinstance(value, BaseModel)
        else value
    )
    return model_type.model_validate(payload)


def _record_map(
    records: Iterable[tuple[str, str, BaseModel]],
) -> dict[str, tuple[str, BaseModel]]:
    result: dict[str, tuple[str, BaseModel]] = {}
    for schema, object_id, value in records:
        if schema not in _SCHEMA_MODELS:
            raise ValueError(f"control event uses non-workflow schema {schema!r}")
        normalized = _canonical(_SCHEMA_MODELS[schema], value)
        if normalized.id != object_id:
            raise ValueError("resolved workflow object ID differs from its record")
        if object_id in result:
            raise ValueError("control event resolves one object ID more than once")
        result[object_id] = (schema, normalized)
    return result


def _call_index(values: Any) -> dict[int, Any]:
    if isinstance(values, Mapping):
        return {int(seq): call for seq, call in values.items()}
    indexed: dict[int, Any] = {}
    for value in values:
        if isinstance(value, tuple) and len(value) == 2:
            seq, call = value
        else:
            seq, call = getattr(value, "seq", None), getattr(value, "llm", None)
        if seq is not None and call is not None:
            indexed[int(seq)] = call
    return indexed


def _guard_transition(
    guard: GuardResultV1,
) -> tuple[TransitionKind, tuple[str, ...]]:
    outcomes = {finding.outcome for finding in guard.findings}
    if GuardFindingOutcome.ADMIT in outcomes:
        return TransitionKind.PROPOSAL_ADMITTED, guard.admitted_refs
    if GuardFindingOutcome.REJECT in outcomes:
        return TransitionKind.PROPOSAL_REJECTED, guard.rejected_refs
    return TransitionKind.PROPOSAL_DEDUPLICATED, guard.deduplicated_refs


@dataclass
class TransactionReplayItem:
    """Replay-only materialization of one controller-v3 work transaction."""

    preparation: WorkPreparationV1
    plans: dict[str, ContextPackPlanV1] = field(default_factory=dict)
    reservation: TokenReservationV2 | None = None
    exposure: ContextExposureReceiptV2 | None = None
    authorization: DispatchAuthorizationBundleV1 | None = None
    provider_attempts: dict[int, ProviderAttemptV1] = field(default_factory=dict)
    provider_calls: dict[int, Any] = field(default_factory=dict)
    admissions: dict[int, SemanticAdmissionV1] = field(default_factory=dict)
    terminal: WorkTerminalV1 | None = None
    transitions: list[WorkLifecycleTransitionV1] = field(default_factory=list)
    event_seqs: list[int] = field(default_factory=list)

    @property
    def issued(self) -> bool:
        return self.authorization is not None

    @property
    def outstanding(self) -> bool:
        return self.terminal is None


@dataclass
class WorkflowReplayState:
    """Deterministic process-only index reconstructed from ``Control`` events."""

    work_orders: dict[str, WorkOrderEnvelopeV1] = field(default_factory=dict)
    repair_work_orders: dict[str, RepairWorkOrderV1] = field(default_factory=dict)
    proposal_receipts: dict[str, ProposalReceiptV1] = field(default_factory=dict)
    guard_results: dict[str, GuardResultV1] = field(default_factory=dict)
    decisions: dict[str, TransitionDecisionV1] = field(default_factory=dict)
    stop_observations: dict[str, StopMetricsObservationV1] = field(
        default_factory=dict
    )
    lifecycle_snapshots: dict[str, WorkflowLifecycleSnapshotV1] = field(
        default_factory=dict
    )
    lifecycle_decisions: dict[str, WorkflowLifecycleDecisionV1] = field(
        default_factory=dict
    )
    resume_decisions: dict[str, WorkflowResumeDecisionV1] = field(
        default_factory=dict
    )
    terminal_decision_id: str | None = None
    current_resume_decision_id: str | None = None
    resume_decision_event_seq: dict[str, int] = field(default_factory=dict)
    terminal_commitments_by_epoch: dict[int, RunTerminalCommitmentV1] = field(
        default_factory=dict
    )
    terminal_commitment_event_seq: dict[str, int] = field(default_factory=dict)
    terminal_epoch_opening_resume_ref: dict[int, str] = field(default_factory=dict)
    current_terminal_epoch: int = 0
    branches: dict[str, WorkflowBranchState] = field(default_factory=dict)
    work_to_branch: dict[str, str] = field(default_factory=dict)
    decision_event_seq: dict[str, int] = field(default_factory=dict)
    calls_by_seq: dict[int, Any] = field(default_factory=dict)
    transaction_work: dict[str, TransactionReplayItem] = field(default_factory=dict)
    transaction_calls_by_seq: dict[int, Any] = field(default_factory=dict)
    compact_recovery_by_route_seat: dict[
        tuple[str, int, str, str], CompactRecoveryTransitionV1
    ] = field(default_factory=dict)
    insufficient_capability_by_route_seat: dict[
        tuple[str, int, str, str], RouteSeatInsufficientCapabilityV1
    ] = field(default_factory=dict)
    contract_decomposition_by_source_work: dict[
        str, ContractDecompositionTransitionV1
    ] = field(default_factory=dict)
    contract_decomposition_event_seq: dict[str, int] = field(default_factory=dict)
    contract_decomposition_completion_by_transition: dict[
        str, ContractDecompositionCompletionV1
    ] = field(default_factory=dict)
    route_seat_model_classification: RouteSeatModelClassificationPlanV1 | None = None
    model_classification_binding: ModelClassificationBindingV1 | None = None
    model_classification_event_seq: int | None = None
    event_seqs: list[int] = field(default_factory=list)
    event_inputs_by_seq: dict[int, tuple[str, ...]] = field(default_factory=dict)
    event_outputs_by_seq: dict[int, tuple[str, ...]] = field(default_factory=dict)
    _run_manifest: Any | None = field(default=None, repr=False)

    def bind_run_manifest(self, manifest: Any) -> None:
        """Bind replay validation to one immutable v6 manifest authority."""

        if getattr(manifest, "schema_version", None) != 6:
            raise ValueError("transaction replay requires RunManifest v6 authority")
        current = self._run_manifest
        if current is not None and current.sha256 != manifest.sha256:
            raise ValueError("workflow replay is already bound to another manifest")
        self._run_manifest = manifest
        try:
            for epoch, commitment in self.terminal_commitments_by_epoch.items():
                if (
                    commitment.manifest_sha256 != manifest.sha256
                    or commitment.run_id != manifest.sha256
                    or commitment.terminal_epoch != epoch
                ):
                    raise ValueError(
                        "terminal commitment history belongs to another manifest"
                    )
            for item in self.transaction_work.values():
                preparation = item.preparation
                if preparation.manifest_digest != manifest.sha256:
                    raise ValueError("transaction history belongs to another manifest")
                self._validate_preparation_behavioral_authority(
                    manifest,
                    preparation,
                )
                self._validate_preparation_decomposition_authority(preparation)
            for transition in self.contract_decomposition_by_source_work.values():
                self._validate_contract_decomposition_transition(transition)
            if any(
                completion.manifest_digest != manifest.sha256
                for completion in self.contract_decomposition_completion_by_transition.values()
            ):
                raise ValueError("decomposition completion belongs to another manifest")
            if self.route_seat_model_classification is not None:
                self._validate_model_classification(
                    manifest,
                    self.route_seat_model_classification,
                )
            for outcome in self.insufficient_capability_by_route_seat.values():
                item = self.transaction_work.get(outcome.work_id)
                attempt = (
                    item.provider_attempts.get(outcome.attempt_index)
                    if item is not None
                    else None
                )
                admission = (
                    item.admissions.get(outcome.attempt_index)
                    if item is not None
                    else None
                )
                if item is None or attempt is None or admission is None:
                    raise ValueError(
                        "insufficient capability lacks durable work authority"
                    )
                self._validate_insufficient_capability(
                    outcome, item, attempt, admission
                )
        except BaseException:
            self._run_manifest = current
            raise

    @staticmethod
    def _validate_model_classification(manifest: Any, plan) -> None:
        from deepreason.canonical import canonical_json
        import hashlib

        if plan.manifest_digest != manifest.sha256:
            raise ValueError("model classification belongs to another manifest")
        behavioral_plan = manifest.route_seat_behavioral_capability_plan
        if behavioral_plan is None:
            raise ValueError("model classification lacks behavioral authority")
        if len(plan.entries) != len(behavioral_plan.entries):
            raise ValueError("model classification route inventory is incomplete")
        for selected, grant in zip(plan.entries, behavioral_plan.entries, strict=True):
            grant_digest = hashlib.sha256(
                b"deepreason.route-seat-behavioral-grant.v1\x00"
                + canonical_json(
                    grant.model_dump(mode="json", by_alias=True, exclude_none=True)
                )
            ).hexdigest()
            identity = (grant.role, grant.seat, grant.endpoint_id, grant.route_sha256)
            observed = (
                selected.role,
                selected.seat,
                selected.endpoint_id,
                selected.route_sha256,
            )
            contracts = tuple(item.contract_id for item in grant.contracts)
            if (
                observed != identity
                or selected.behavioral_grant_sha256 != grant_digest
                or selected.authorized_contract_ids != contracts
            ):
                raise ValueError("model classification differs from behavioral authority")
            expected_class = (
                "inactive_no_authorized_contract"
                if not contracts
                else "qualified_exact_behavior"
            )
            if selected.selected_class != expected_class:
                raise ValueError("model classification does not authorize exact behavior")

    def _apply_model_classification(self, event, payload, resolved_records) -> None:
        if self.route_seat_model_classification is not None:
            raise ValueError("model classification authority is already bound")
        if [schema for schema, _object_id, _value in resolved_records] != [
            "workflow-route-seat-model-classification-plan-v1",
            "workflow-model-classification-binding-v1",
        ]:
            raise ValueError("classification binding has the wrong record order")
        plan = resolved_records[0][2]
        binding = resolved_records[1][2]
        if (
            payload.decision_ref != binding.id
            or tuple(payload.inputs)
            != (
                plan.id,
                "classification:" + plan.qualification_evidence_sha256,
            )
            or tuple(payload.outputs) != (plan.id, binding.id)
            or binding.classification_plan_ref != plan.id
            or binding.manifest_digest != plan.manifest_digest
            or binding.algorithm != plan.algorithm
            or binding.algorithm_version != plan.algorithm_version
            or binding.qualification_evidence_sha256
            != plan.qualification_evidence_sha256
        ):
            raise ValueError("classification binding differs from its plan")
        if self._run_manifest is not None:
            self._validate_model_classification(self._run_manifest, plan)
        self.route_seat_model_classification = plan
        self.model_classification_binding = binding
        self.model_classification_event_seq = int(event.seq)
        self.event_seqs.append(int(event.seq))

    def _validate_contract_decomposition_transition(
        self,
        transition: ContractDecompositionTransitionV1,
    ) -> None:
        manifest = self._run_manifest
        if manifest is None or transition.manifest_digest != manifest.sha256:
            raise ValueError("contract decomposition lacks manifest authority")
        item = self.transaction_work.get(transition.source_work_id)
        if item is None or item.terminal is None:
            raise ValueError("contract decomposition lacks terminal source work")
        terminal = item.terminal
        admission = item.admissions.get(transition.source_attempt_index)
        if (
            terminal.id != transition.source_terminal_ref
            or terminal.status != "schema_exhausted"
            or admission is None
            or admission.id != transition.source_semantic_admission_ref
            or admission.outcome != "schema_exhausted"
            or item.preparation.contract_id != transition.source_contract_id
            or item.preparation.route_lease != transition.route_lease
        ):
            raise ValueError("contract decomposition differs from exhausted source work")
        grant = resolve_route_seat_contract_decomposition(
            manifest,
            role=transition.route_lease.role,
            seat=transition.route_lease.seat,
            endpoint_id=transition.route_lease.endpoint_id,
            route_sha256=transition.route_lease.route_sha256,
            source_contract_id=transition.source_contract_id,
        )
        if (
            transition.atomic_contract_id != grant.atomic_contract_id
            or transition.trigger != grant.trigger
            or transition.child_partition != grant.child_partition
            or transition.maximum_children != grant.maximum_children
            or transition.coverage != grant.coverage
            or transition.execution != grant.execution
            or transition.source_failure_preserved != grant.source_failure_preserved
        ):
            raise ValueError("contract decomposition differs from manifest grant")
        if grant.child_partition == "conjecture_candidate_slot":
            expected_keys = tuple(
                f"candidate-slot-{index:03d}"
                for index in range(grant.maximum_children)
            )
        elif grant.child_partition == "scratch_single_object":
            source = item
            source_payload = source.preparation.task_payload_value
            if (
                isinstance(source_payload, Mapping)
                and source_payload.get("schema") == "repair.semantic-task.v1"
            ):
                source = self.transaction_work.get(source_payload.get("parent_work_id"))
                source_payload = (
                    source.preparation.task_payload_value
                    if source is not None
                    else None
                )
            operation = (
                source_payload.get("operation")
                if isinstance(source_payload, Mapping)
                else None
            )
            if operation not in {"block", "link", "guide"}:
                raise ValueError("scratch decomposition source operation is invalid")
            expected_keys = (f"scratch-{operation}-minimal",)
        else:
            expected_keys = item.preparation.target_refs
        if transition.child_keys != expected_keys:
            raise ValueError("contract decomposition child inventory differs")

    def _apply_contract_decomposition(self, event, payload, resolved_records) -> None:
        if [schema for schema, _object_id, _value in resolved_records] != [
            "workflow-contract-decomposition-transition-v1"
        ]:
            raise ValueError("contract decomposition has a noncanonical record shape")
        transition = resolved_records[0][2]
        assert isinstance(transition, ContractDecompositionTransitionV1)
        if (
            payload.decision_ref != transition.id
            or tuple(payload.inputs)
            != (transition.source_work_id, transition.source_terminal_ref)
            or tuple(payload.outputs) != (transition.id,)
        ):
            raise ValueError("contract decomposition control event differs")
        if transition.source_work_id in self.contract_decomposition_by_source_work:
            raise ValueError("source work has duplicate contract decomposition")
        self._validate_contract_decomposition_transition(transition)
        self.contract_decomposition_by_source_work[transition.source_work_id] = transition
        self.contract_decomposition_event_seq[transition.id] = int(event.seq)
        self.event_seqs.append(int(event.seq))

    def _apply_contract_decomposition_completion(
        self, event, payload, resolved_records
    ) -> None:
        if [schema for schema, _object_id, _value in resolved_records] != [
            "workflow-contract-decomposition-completion-v1"
        ]:
            raise ValueError("decomposition completion has a noncanonical shape")
        completion = resolved_records[0][2]
        assert isinstance(completion, ContractDecompositionCompletionV1)
        transition = next(
            (
                item
                for item in self.contract_decomposition_by_source_work.values()
                if item.id == completion.transition_ref
            ),
            None,
        )
        if (
            transition is None
            or completion.transition_ref
            in self.contract_decomposition_completion_by_transition
            or payload.decision_ref != completion.id
            or tuple(payload.inputs)
            != (completion.source_work_id, completion.transition_ref)
            or tuple(payload.outputs) != (completion.id,)
            or completion.manifest_digest != transition.manifest_digest
            or completion.source_work_id != transition.source_work_id
            or not completion.source_failure_preserved
        ):
            raise ValueError("decomposition completion differs from its transition")
        children = [
            item
            for item in self.transaction_work.values()
            if isinstance(item.preparation.task_payload_value, Mapping)
            and item.preparation.task_payload_value.get(
                "decomposition_transition_ref"
            )
            == transition.id
            and item.preparation.task_payload_value.get("schema")
            == "contract-decomposition-child.v1"
        ]
        children.sort(
            key=lambda item: item.preparation.task_payload_value["child_index"]
        )
        if tuple(
            item.preparation.task_payload_value["child_index"] for item in children
        ) != tuple(range(len(transition.child_keys))):
            raise ValueError("decomposition completion child indices differ")
        results = []
        admissions = []
        for item in children:
            candidates = [item]
            candidates.extend(
                candidate
                for candidate in self.transaction_work.values()
                if isinstance(candidate.preparation.task_payload_value, Mapping)
                and candidate.preparation.task_payload_value.get("schema")
                == "repair.semantic-task.v1"
                and candidate.preparation.task_payload_value.get("parent_work_id")
                == item.preparation.id
            )
            completed = [
                candidate
                for candidate in candidates
                if candidate.terminal is not None
                and candidate.terminal.status == "completed"
            ]
            if len(completed) != 1:
                raise ValueError("decomposition completion names unfinished child work")
            result = completed[0]
            admission = result.admissions.get(result.preparation.attempt_index)
            if admission is None or admission.outcome != "admitted":
                raise ValueError("decomposition completion child admission differs")
            results.append(result)
            admissions.append(admission)
        if (
            len(children) != len(transition.child_keys)
            or completion.child_work_ids
            != tuple(item.preparation.id for item in results)
            or completion.child_semantic_admission_refs
            != tuple(admission.id for admission in admissions)
        ):
            raise ValueError("decomposition completion child inventory differs")
        self._validate_contract_decomposition_effects(
            transition,
            tuple(results),
            completion.admitted_effect_refs,
            completion_event_seq=int(event.seq),
        )
        self.contract_decomposition_completion_by_transition[
            transition.id
        ] = completion
        self.event_seqs.append(int(event.seq))

    def _validate_contract_decomposition_effects(
        self,
        transition: ContractDecompositionTransitionV1,
        results: tuple[TransactionReplayItem, ...],
        effect_refs: tuple[str, ...],
        *,
        completion_event_seq: int,
    ) -> None:
        """Bind claimed merge effects to events following exact child calls."""

        result_ids = {item.preparation.id for item in results}
        child_call_seqs = sorted(
            seq
            for seq, call in self.transaction_calls_by_seq.items()
            if call.work_order_id in result_ids
        )
        if len(child_call_seqs) != len(results):
            raise ValueError("decomposition effects lack exact child provider calls")
        latest = child_call_seqs[-1]
        expected: list[str] = []
        if transition.child_partition == "conjecture_candidate_slot":
            marker = f"conjecture-call:{latest}"
            for seq in sorted(self.event_outputs_by_seq):
                if marker in self.event_inputs_by_seq.get(seq, ()):
                    expected.extend(self.event_outputs_by_seq.get(seq, ()))
        else:
            marker = "contract-decomposition-effect"
            marker_events: list[tuple[int, str]] = []
            for seq in sorted(self.event_inputs_by_seq):
                inputs = self.event_inputs_by_seq[seq]
                if (
                    len(inputs) == 3
                    and inputs[0] == marker
                    and inputs[1] == transition.id
                    and latest < seq < completion_event_seq
                ):
                    marker_events.append((seq, inputs[2]))
            if len(marker_events) != len(effect_refs):
                raise ValueError(
                    "decomposition completion lacks exact chronological effect markers"
                )
            for marker_seq, effect_ref in marker_events:
                if not any(
                    latest < effect_seq < marker_seq
                    and effect_ref in outputs
                    for effect_seq, outputs in self.event_outputs_by_seq.items()
                ):
                    raise ValueError(
                        "decomposition effect is not reachable after exact child calls"
                    )
                expected.append(effect_ref)
        expected_effects = tuple(dict.fromkeys(expected))
        if effect_refs != expected_effects:
            raise ValueError(
                "decomposition completion differs from exact semantic effects"
            )

    @staticmethod
    def _validate_preparation_behavioral_authority(
        manifest: Any,
        preparation: WorkPreparationV1,
    ) -> None:
        """Validate one durable preparation before or during manifest binding."""

        if manifest.route_seat_behavioral_capability_plan is None:
            return
        behavioral = resolve_route_seat_behavioral_capability(
            manifest,
            role=preparation.route_lease.role,
            seat=preparation.route_lease.seat,
            endpoint_id=preparation.route_lease.endpoint_id,
            route_sha256=preparation.route_lease.route_sha256,
        )
        if preparation.contract_id not in {
            grant.contract_id for grant in behavioral.contracts
        }:
            raise ValueError(
                "work preparation contract lacks route-seat behavioral authority"
            )

    def _validate_preparation_decomposition_authority(
        self,
        preparation: WorkPreparationV1,
    ) -> None:
        manifest = self._run_manifest
        if manifest is None or manifest.route_seat_contract_decomposition_plan is None:
            return
        atomic_grants = {
            entry.atomic_contract_id: entry
            for entry in manifest.route_seat_contract_decomposition_plan.entries
            if entry.role == preparation.route_lease.role
            and entry.seat == preparation.route_lease.seat
            and entry.endpoint_id == preparation.route_lease.endpoint_id
            and entry.route_sha256 == preparation.route_lease.route_sha256
        }
        grant = atomic_grants.get(preparation.contract_id)
        if grant is None:
            return
        payload = preparation.task_payload_value
        if not isinstance(payload, Mapping):
            raise ValueError("atomic child preparation lacks decomposition payload")
        if payload.get("schema") == "repair.semantic-task.v1":
            parent = self.transaction_work.get(payload.get("parent_work_id"))
            if (
                parent is None
                or parent.preparation.contract_id != preparation.contract_id
                or parent.preparation.route_lease != preparation.route_lease
                or parent.preparation.target_refs != preparation.target_refs
            ):
                raise ValueError("atomic repair differs from its decomposition child")
            self._validate_preparation_decomposition_authority(parent.preparation)
            return
        source_work_id = payload.get("source_work_id")
        transition = self.contract_decomposition_by_source_work.get(source_work_id)
        child_index = payload.get("child_index")
        child_count = payload.get("child_count")
        source = (
            self.transaction_work.get(transition.source_work_id)
            if transition is not None
            else None
        )
        source_payload = (
            source.preparation.task_payload_value if source is not None else None
        )
        if (
            isinstance(source_payload, Mapping)
            and source_payload.get("schema") == "repair.semantic-task.v1"
        ):
            source = self.transaction_work.get(source_payload.get("parent_work_id"))
        if (
            transition is None
            or payload.get("schema") != "contract-decomposition-child.v1"
            or payload.get("decomposition_transition_ref") != transition.id
            or payload.get("source_work_id") != transition.source_work_id
            or payload.get("source_contract_id") != transition.source_contract_id
            or payload.get("atomic_contract_id") != transition.atomic_contract_id
            or payload.get("child_partition") != transition.child_partition
            or transition.atomic_contract_id != preparation.contract_id
            or transition.source_contract_id != grant.source_contract_id
            or preparation.route_lease != transition.route_lease
            or not isinstance(child_index, int)
            or isinstance(child_index, bool)
            or not isinstance(child_count, int)
            or isinstance(child_count, bool)
            or child_count != len(transition.child_keys)
            or not 0 <= child_index < child_count <= grant.maximum_children
            or payload.get("child_key") != transition.child_keys[child_index]
            or source is None
            or (
                transition.child_partition == "critic_target"
                and preparation.target_refs
                != (transition.child_keys[child_index],)
            )
            or (
                transition.child_partition == "conjecture_candidate_slot"
                and preparation.target_refs != source.preparation.target_refs
            )
            or (
                transition.child_partition
                in {"bridge_catalog_batch", "bridge_ledger_batch", "scratch_single_object"}
                and preparation.target_refs
                != (transition.child_keys[child_index],)
            )
            or transition.id not in preparation.input_refs
            or transition.source_work_id not in preparation.input_refs
            or transition.child_context_refs[child_index]
            not in preparation.input_refs
        ):
            raise ValueError("atomic child preparation lacks prior exact decomposition")

    @staticmethod
    def _route_seat_key(route_lease) -> tuple[str, int, str, str]:
        return (
            route_lease.role,
            route_lease.seat,
            route_lease.endpoint_id,
            route_lease.route_sha256,
        )

    def _root_transaction_item(self, item: TransactionReplayItem):
        seen: set[str] = set()
        current = item
        while self._is_schema_repair_item(current):
            payload = current.preparation.task_payload_value
            parent_id = payload.get("parent_work_id") if isinstance(payload, Mapping) else None
            if not isinstance(parent_id, str) or parent_id in seen:
                raise ValueError("repair ancestry is not canonical")
            seen.add(parent_id)
            current = self.transaction_work.get(parent_id)
            if current is None:
                raise ValueError("repair ancestry lacks its parent work")
        return current

    @staticmethod
    def _is_schema_repair_item(item: TransactionReplayItem) -> bool:
        """Distinguish schema-repair children from domain repair work."""

        payload = item.preparation.task_payload_value
        return (
            item.preparation.task_kind == WorkflowTaskKind.REPAIR
            and isinstance(payload, Mapping)
            and payload.get("schema") == "repair.semantic-task.v1"
        )

    def _transaction_chain(self, root: TransactionReplayItem):
        values = []
        for item in self.transaction_work.values():
            if (
                item.preparation.id == root.preparation.id
                or (
                    self._is_schema_repair_item(item)
                    and self._root_transaction_item(item).preparation.id
                    == root.preparation.id
                )
            ):
                if (
                    item.preparation.contract_id != root.preparation.contract_id
                    or item.preparation.route_lease != root.preparation.route_lease
                ):
                    raise ValueError("repair chain differs from its root authority")
                values.append(item)
        return tuple(
            sorted(
                values,
                key=lambda item: (
                    min(item.event_seqs) if item.event_seqs else 2**63,
                    item.preparation.id,
                ),
            )
        )

    def insufficient_capability_fields(
        self,
        work_id: str,
        attempt_index: int,
    ) -> dict[str, Any] | None:
        """Derive final route-seat authority from canonical durable state only."""

        manifest = self._run_manifest
        item = self.transaction_work.get(work_id)
        if manifest is None or item is None:
            return None
        preparation = item.preparation
        attempt = item.provider_attempts.get(attempt_index)
        admission = item.admissions.get(attempt_index)
        if (
            manifest.schema_version != 6
            or manifest.route_seat_behavioral_capability_plan is None
            or manifest.route_seat_contract_decomposition_plan is None
            or attempt is None
            or admission is None
            or attempt.outcome != "provider_result"
            or admission.outcome != "schema_exhausted"
            or attempt.contract_id != preparation.contract_id
            or attempt.route_lease != preparation.route_lease
        ):
            return None
        key = self._route_seat_key(preparation.route_lease)
        outgoing = tuple(
            grant
            for grant in manifest.route_seat_contract_decomposition_plan.entries
            if (
                grant.role,
                grant.seat,
                grant.endpoint_id,
                grant.route_sha256,
                grant.source_contract_id,
            )
            == (*key, preparation.contract_id)
        )
        if outgoing:
            return None

        plan = self.route_seat_model_classification
        binding = self.model_classification_binding
        if plan is None or binding is None:
            return None
        selected = tuple(
            entry
            for entry in plan.entries
            if (entry.role, entry.seat, entry.endpoint_id, entry.route_sha256) == key
        )
        if (
            len(selected) != 1
            or selected[0].selected_class != "qualified_exact_behavior"
            or preparation.contract_id not in selected[0].authorized_contract_ids
            or binding.classification_plan_ref != plan.id
            or binding.qualification_evidence_sha256
            != plan.qualification_evidence_sha256
        ):
            return None
        repair_policy = manifest.contract_schema_repair_policy
        repair_grants = tuple(
            grant
            for grant in (repair_policy.grants if repair_policy is not None else ())
            if grant.contract_id == preparation.contract_id
        )
        if len(repair_grants) != 1:
            return None
        repair_grant = repair_grants[0]

        final_root = self._root_transaction_item(item)
        transition = None
        payload = final_root.preparation.task_payload_value
        if isinstance(payload, Mapping) and payload.get("schema") == (
            "contract-decomposition-child.v1"
        ):
            transition_ref = payload.get("decomposition_transition_ref")
            transition = next(
                (
                    value
                    for value in self.contract_decomposition_by_source_work.values()
                    if value.id == transition_ref
                ),
                None,
            )
            if (
                transition is None
                or transition.atomic_contract_id != preparation.contract_id
                or transition.route_lease != preparation.route_lease
            ):
                return None

        chains = []
        if transition is not None:
            source = self.transaction_work.get(transition.source_work_id)
            if source is None:
                return None
            chains.extend(self._transaction_chain(self._root_transaction_item(source)))
        chains.extend(self._transaction_chain(final_root))
        attempted = tuple(
            dict.fromkeys(
                item.preparation.id
                for item in sorted(
                    chains,
                    key=lambda value: (
                        min(value.event_seqs) if value.event_seqs else 2**63,
                        value.preparation.id,
                    ),
                )
            )
        )
        attempted_items = tuple(self.transaction_work[item_id] for item_id in attempted)
        if not attempted_items or attempted_items[-1].preparation.id != work_id:
            return None
        final_chain = self._transaction_chain(final_root)
        observed_provider_calls = sum(
            len(value.provider_attempts) for value in final_chain
        )
        if not 1 <= observed_provider_calls <= repair_grant.maximum_provider_calls:
            return None
        compact_refs = tuple(
            value.id
            for route_key, value in sorted(
                self.compact_recovery_by_route_seat.items(), key=lambda pair: pair[1].id
            )
            if route_key == key
        )
        return {
            "manifest_digest": manifest.sha256,
            "work_id": work_id,
            "attempt_index": attempt_index,
            "route_lease": preparation.route_lease,
            "contract_id": preparation.contract_id,
            "provider_attempt_ref": attempt.id,
            "semantic_admission_ref": admission.id,
            "attempted_work_ids": attempted,
            "attempted_contract_ids": tuple(
                value.preparation.contract_id for value in attempted_items
            ),
            "decomposition_transition_refs": (
                (transition.id,) if transition is not None else ()
            ),
            "compact_recovery_transition_refs": compact_refs,
            "classification_plan_ref": plan.id,
            "classification_binding_ref": binding.id,
            "qualification_evidence_sha256": plan.qualification_evidence_sha256,
            "behavioral_grant_sha256": selected[0].behavioral_grant_sha256,
            "maximum_schema_repairs": repair_grant.maximum_schema_repairs,
            "maximum_provider_calls": repair_grant.maximum_provider_calls,
            "observed_provider_calls": observed_provider_calls,
        }

    def _validate_insufficient_capability(
        self,
        outcome: RouteSeatInsufficientCapabilityV1,
        item: TransactionReplayItem,
        attempt: ProviderAttemptV1,
        admission: SemanticAdmissionV1,
    ) -> tuple[str, int, str, str]:
        expected = self.insufficient_capability_fields(
            item.preparation.id,
            item.preparation.attempt_index,
        )
        if (
            expected is None
            or outcome != RouteSeatInsufficientCapabilityV1.create(**expected)
            or outcome.provider_attempt_ref != attempt.id
            or outcome.semantic_admission_ref != admission.id
        ):
            raise ValueError(
                "insufficient-capability outcome differs from durable authority"
            )
        return outcome.route_seat_key

    def _manifest_route(self, route_lease):
        manifest = self._run_manifest
        if manifest is None:
            raise ValueError("compact recovery transition lacks manifest authority")
        routes = manifest.roles.get(route_lease.role, ())
        if route_lease.seat >= len(routes):
            raise ValueError("compact recovery route seat is outside the manifest")
        route = routes[route_lease.seat]
        if route.endpoint_id != route_lease.endpoint_id:
            raise ValueError("compact recovery endpoint differs from the manifest")
        from deepreason.llm.firewall import route_fingerprint

        if route_fingerprint(route) != route_lease.route_sha256:
            raise ValueError("compact recovery route digest differs from the manifest")
        return route

    def _compact_policy(self, preparation: WorkPreparationV1):
        manifest = self._run_manifest
        if manifest is None:
            return None
        if preparation.manifest_digest != manifest.sha256:
            raise ValueError("compact recovery work belongs to another manifest")
        return manifest.compact_recovery_policy

    def _validate_compact_transition(
        self,
        compact: CompactRecoveryTransitionV1,
        item: TransactionReplayItem,
        attempt: ProviderAttemptV1,
        admission: SemanticAdmissionV1,
    ) -> tuple[str, int, str, str]:
        manifest = self._run_manifest
        policy = self._compact_policy(item.preparation)
        if manifest is None or policy is None:
            raise ValueError("compact recovery was not authorized by the manifest")
        route = self._manifest_route(compact.route_lease)
        base_profile = resolve_route_seat_base_profile(
            manifest,
            role=compact.route_lease.role,
            seat=compact.route_lease.seat,
            endpoint_id=compact.route_lease.endpoint_id,
        )
        if base_profile not in policy.source_profiles:
            raise ValueError("manifest profile cannot source compact recovery")
        if (
            compact.manifest_digest != manifest.sha256
            or compact.work_id != item.preparation.id
            or compact.attempt_index != admission.attempt_index
            or compact.semantic_admission_ref != admission.id
            or compact.route_lease != item.preparation.route_lease
            or compact.route_lease != attempt.route_lease
            or compact.source_profile != base_profile
            or compact.source_profile not in policy.source_profiles
            or compact.target_profile != policy.target_profile
            or compact.trigger != policy.trigger
            or compact.scope != policy.scope
            or compact.sticky != policy.sticky
            or compact.applies_to != policy.applies_to
            or compact.retry_failed_work != policy.retry_failed_work
            or admission.outcome != "schema_exhausted"
            or attempt.outcome != "provider_result"
        ):
            raise ValueError("compact recovery transition differs from durable authority")
        call = item.provider_calls.get(compact.attempt_index)
        if call is None or not call.attempt_trace:
            raise ValueError("compact recovery lacks a durable provider attempt trace")
        if (
            call.role != compact.route_lease.role
            or call.model != route.model_id
            or call.endpoint != route.base_url
            or len(call.attempt_trace) != call.attempts
            or any(
                trace.contract_id != item.preparation.contract_id
                or trace.endpoint_id != compact.route_lease.endpoint_id
                or trace.route_sha256 != compact.route_lease.route_sha256
                or trace.seat != compact.route_lease.seat
                or trace.model_profile != compact.source_profile
                or trace.transport_profile != compact.source_profile
                for trace in call.attempt_trace
            )
        ):
            raise ValueError("compact recovery provider trace differs from its route seat")
        return compact.route_seat_key

    def observe_event(self, event: Any) -> None:
        """Index a preceding work-bound provider call without mutating authority."""

        call = getattr(event, "llm", None)
        seq = getattr(event, "seq", None)
        if seq is not None:
            seq = int(seq)
            if seq in self.event_inputs_by_seq or seq in self.event_outputs_by_seq:
                raise ValueError("workflow event sequence appears more than once")
            self.event_inputs_by_seq[seq] = tuple(getattr(event, "inputs", ()))
            self.event_outputs_by_seq[seq] = tuple(getattr(event, "outputs", ()))
        if call is None or seq is None or getattr(call, "work_order_id", None) is None:
            return
        if self.terminal_decision_id is not None:
            raise ValueError("work-bound provider call follows terminal lifecycle state")
        if seq in self.calls_by_seq:
            raise ValueError("workflow provider-call sequence appears more than once")
        work_id = call.work_order_id
        transaction = self.transaction_work.get(work_id)
        if transaction is not None:
            if not transaction.issued or transaction.terminal is not None:
                raise ValueError(
                    "transactional provider call lacks live issued authority"
                )
            if seq in self.transaction_calls_by_seq:
                raise ValueError("transactional provider call sequence is duplicated")
            self.transaction_calls_by_seq[seq] = call
            return
        work = self.work_orders.get(work_id)
        if work is None:
            raise ValueError("provider call names an unknown work order")
        branch_id = self.work_to_branch[work_id]
        item = self.branches[branch_id].process_state.work_item(work_id)
        if item is None or item.status not in {
            WorkItemStatus.ISSUED,
            WorkItemStatus.REPAIR_PENDING,
        }:
            raise ValueError("provider call was not preceded by issued work")
        bound_calls = sum(
            prior.work_order_id == work_id
            for prior in self.calls_by_seq.values()
        )
        if bound_calls >= work.capability_grant.max_provider_calls:
            raise ValueError("provider-call capability is already exhausted")
        self.calls_by_seq[seq] = call

    def _branch_for(
        self,
        decision: TransitionDecisionV1,
        work_order: WorkOrderEnvelopeV1 | None,
    ) -> tuple[str, WorkflowProcessStateV1, bool]:
        known = self.work_to_branch.get(decision.work_order_id)
        if known is not None:
            if decision.transition_kind == TransitionKind.WORK_ENABLED:
                raise ValueError("duplicate work-order enable transition")
            return known, self.branches[known].process_state, False
        if decision.transition_kind != TransitionKind.WORK_ENABLED or work_order is None:
            raise ValueError("unknown work order must begin with work_enabled")

        matches = [
            branch_id
            for branch_id, branch in self.branches.items()
            if branch.process_state.digest == decision.previous_process_digest
        ]
        if len(matches) > 1:
            raise ValueError("work-order branch is ambiguous at its state digest")
        if matches:
            return matches[0], self.branches[matches[0]].process_state, False
        initial = WorkflowProcessStateV1.initial(
            manifest_digest=work_order.manifest_digest,
            workflow_profile=work_order.workflow_profile,
            formal_fence_seq=work_order.formal_fence_seq,
            scratch_fence_seq=work_order.scratch_fence_seq,
        )
        if initial.digest != decision.previous_process_digest:
            raise ValueError("work-enabled decision does not begin at its declared fence")
        return work_order.id, initial, True

    @staticmethod
    def _validate_work_decision(
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        state: WorkflowProcessStateV1,
    ) -> None:
        if (
            decision.work_order_id != work.id
            or decision.route_lease != work.route_lease
            or decision.manifest_digest != work.manifest_digest
            or decision.workflow_profile != work.workflow_profile
        ):
            raise ValueError("transition decision differs from its work-order authority")
        if (
            state.manifest_digest != work.manifest_digest
            or state.workflow_profile != work.workflow_profile
            or state.formal_fence_seq != work.formal_fence_seq
            or state.scratch_fence_seq != work.scratch_fence_seq
        ):
            raise ValueError("work order belongs to another replay branch")
        if (
            decision.transition_kind == TransitionKind.WORK_ENABLED
            and decision.trigger_ref != work.problem_ref
        ):
            raise ValueError("work-enabled trigger differs from its selected problem")
        if (
            decision.transition_kind == TransitionKind.WORK_ISSUED
            and decision.trigger_ref
            != (work.advisory_context_ref or work.id)
        ):
            raise ValueError("work-issued trigger differs from its prepared context")
        if state.selected_problem_ref not in {None, work.problem_ref}:
            raise ValueError("work order differs from the branch selected problem")
        current = state.work_item(work.id)
        grant = work.capability_grant
        budget = decision.budget_delta
        if decision.transition_kind == TransitionKind.WORK_ISSUED:
            if budget.spent_tokens or budget.released_tokens:
                raise ValueError("work issuance may only reserve tokens")
        elif decision.transition_kind in _PROVIDER_TRANSITIONS:
            # Exact provider settlement is checked against its receipt below.
            pass
        elif decision.transition_kind in {
            TransitionKind.WORK_FINISHED,
            TransitionKind.WORK_ABANDONED,
        }:
            expected_release = current.reserved_tokens if current is not None else 0
            if (
                budget.reserved_tokens
                or budget.spent_tokens
                or budget.released_tokens != expected_release
            ):
                raise ValueError("work completion has an invalid budget release")
        elif any(budget.model_dump(mode="json").values()):
            raise ValueError("transition cannot change token budget state")
        if (
            decision.transition_kind == TransitionKind.CONTEXT_REQUESTED
            and CapabilityOutcome.CONTEXT_REQUEST not in grant.allowed_outcomes
        ):
            raise ValueError("work order does not grant context-request authority")
        if (
            decision.transition_kind == TransitionKind.CONTEXT_GRANTED
            and CapabilityOutcome.CONTEXT_REQUEST not in grant.allowed_outcomes
        ):
            raise ValueError("work order does not grant context-expansion authority")
        if (
            decision.transition_kind == TransitionKind.REPAIR_REQUESTED
            and (
                current is None
                or current.local_repairs_used >= grant.max_local_repairs
            )
        ):
            raise ValueError("work order has exhausted local-repair authority")
        calls = (current.provider_calls_used if current else 0) + (
            decision.provider_call_delta
        )
        repairs = (current.local_repairs_used if current else 0) + (
            decision.local_repair_delta
        )
        contexts = (current.context_expansions_used if current else 0) + (
            decision.context_expansion_delta
        )
        if calls > grant.max_provider_calls:
            raise ValueError("transition exceeds provider-call capability")
        if repairs > grant.max_local_repairs:
            raise ValueError("transition exceeds local-repair capability")
        if contexts > grant.remaining_context_expansions:
            raise ValueError("transition exceeds context-expansion capability")

    @staticmethod
    def _validate_observed_call_capability(
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        prior_calls: Any,
        event_seq: int | None,
    ) -> None:
        if prior_calls is None:
            return
        calls = _call_index(prior_calls)
        bound_count = sum(
            getattr(call, "work_order_id", None) == work.id
            and (event_seq is None or seq < event_seq)
            for seq, call in calls.items()
        )
        if decision.transition_kind == TransitionKind.WORK_ENABLED and bound_count:
            raise ValueError("provider call predates its work-order authority")
        if bound_count > work.capability_grant.max_provider_calls:
            raise ValueError("preceding calls exceed provider-call capability")

    @staticmethod
    def _validate_repair_work_order(
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        repair: RepairWorkOrderV1,
        prior_repair_requests: int,
    ) -> None:
        """Validate one repair authorization against its immutable parent."""

        expected_attempt = prior_repair_requests + 1
        if (
            repair.parent_work_order_id != work.id
            or repair.attempt != expected_attempt
            or repair.remaining_local_attempts
            != work.capability_grant.max_local_repairs - expected_attempt + 1
            or repair.contract_id != work.contract_id
            or repair.route_lease != work.route_lease
            or repair.formal_fence_seq != work.formal_fence_seq
            or repair.scratch_fence_seq != work.scratch_fence_seq
            or repair.repair_policy_ref != work.repair_policy_ref
        ):
            raise ValueError("repair work order differs from its parent authority")
        expected_trigger = repair_attempt_trigger_ref(
            repair.attempt - 1,
            repair.rejected_diagnostic_ref,
        )
        if decision.trigger_ref != expected_trigger:
            raise ValueError("repair work order differs from its rejected diagnostic")

    def _validate_proposal(
        self,
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        proposal: ProposalReceiptV1,
        state: WorkflowProcessStateV1,
        prior_calls: Any,
        event_seq: int | None,
    ) -> None:
        if (
            proposal.id != decision.trigger_ref
            or proposal.work_order_id != work.id
            or proposal.route_lease != work.route_lease
            or proposal.contract_id != work.contract_id
            or tuple(proposal.candidate_payload_refs) != tuple(decision.output_refs)
        ):
            raise ValueError("proposal receipt differs from its transition authority")
        if len(proposal.candidate_payload_refs) > work.capability_grant.max_candidates:
            raise ValueError("proposal exceeds its candidate capability")
        allowed = work.capability_grant.allowed_outcomes
        if (
            proposal.candidate_payload_refs
            and CapabilityOutcome.CANDIDATE_PROPOSAL not in allowed
        ):
            raise ValueError("proposal exceeds its candidate capability")
        if (
            proposal.context_request_ref is not None
            and CapabilityOutcome.CONTEXT_REQUEST not in allowed
        ):
            raise ValueError("proposal exceeds its context-request capability")
        if (
            proposal.abstention_ref is not None
            and CapabilityOutcome.ABSTENTION not in allowed
        ):
            raise ValueError("proposal exceeds its abstention capability")
        outcome = proposal.validation_outcome
        if (
            decision.transition_kind == TransitionKind.PROPOSAL_RECEIVED
            and outcome not in _VALID_PROPOSAL_OUTCOMES
        ) or (
            decision.transition_kind == TransitionKind.REPAIR_EXHAUSTED
            and outcome not in _FAILED_PROPOSAL_OUTCOMES
        ):
            raise ValueError(
                "proposal validation outcome differs from its provider transition"
            )
        if (
            work.workflow_profile in {"conjecture.active.v1", "inquiry.active.v1"}
            and outcome == ProposalValidationOutcome.REPAIR_EXHAUSTED
            and proposal.attempt_count
            != work.capability_grant.max_local_repairs + 1
        ):
            raise ValueError(
                "repair exhaustion predates the authorized local-repair ceiling"
            )
        expected_repair_delta = proposal.attempt_count - 1
        if decision.local_repair_delta != expected_repair_delta:
            label = (
                "valid-after-repair receipt"
                if outcome == ProposalValidationOutcome.VALID_AFTER_REPAIR
                else "proposal receipt"
            )
            raise ValueError(
                f"{label} attempt count differs from local-repair consumption"
            )
        current = state.work_item(work.id)
        if current is None:
            raise ValueError("proposal receipt belongs to work that was not issued")
        expected_reserved = max(0, proposal.tokens - current.reserved_tokens)
        expected_released = max(0, current.reserved_tokens - proposal.tokens)
        delta = decision.budget_delta
        if (
            delta.reserved_tokens != expected_reserved
            or delta.spent_tokens != proposal.tokens
            or delta.released_tokens != expected_released
        ):
            raise ValueError("proposal budget settlement differs from issued work")

        if prior_calls is None:
            return
        calls = _call_index(prior_calls)
        preceding_bound_calls = {
            seq: call
            for seq, call in calls.items()
            if getattr(call, "work_order_id", None) == work.id
            and (event_seq is None or seq < event_seq)
        }
        consumed_call_seqs = {
            receipt.source_call_seq
            for receipt in self.proposal_receipts.values()
            if receipt.work_order_id == work.id
        }
        if len(consumed_call_seqs) != current.provider_calls_used:
            raise ValueError(
                "provider-call receipts differ from process-state consumption"
            )
        newly_consumed = set(preceding_bound_calls) - consumed_call_seqs
        if (
            not consumed_call_seqs.issubset(preceding_bound_calls)
            or len(preceding_bound_calls)
            != current.provider_calls_used + decision.provider_call_delta
            or newly_consumed != {proposal.source_call_seq}
        ):
            raise ValueError(
                "provider call transition must consume exactly its preceding source call"
            )
        call = calls.get(proposal.source_call_seq)
        if call is None:
            raise ValueError("proposal receipt has no preceding provider call")
        if event_seq is not None and proposal.source_call_seq >= event_seq:
            raise ValueError("proposal receipt points to a non-preceding provider call")
        trace = tuple(getattr(call, "attempt_trace", ()))
        if (
            getattr(call, "role", None) != "conjecturer"
            or getattr(call, "work_order_id", None) != work.id
            or getattr(call, "prompt_ref", None) != proposal.prompt_ref
            or (getattr(call, "raw_ref", None) or None) != proposal.raw_ref
            or int(getattr(call, "tokens", -1)) != proposal.tokens
            or int(getattr(call, "attempts", -1)) != proposal.attempt_count
            or not trace
        ):
            raise ValueError("proposal receipt differs from its provider call")
        repair_triggers = tuple(
            prior.trigger_ref
            for prior in self.decisions.values()
            if prior.work_order_id == work.id
            and prior.transition_kind == TransitionKind.REPAIR_REQUESTED
        )
        expected_repair_triggers = tuple(
            repair_attempt_trigger_ref(
                int(getattr(attempt, "attempt", -1)),
                getattr(attempt, "diagnostic_ref", ""),
            )
            for attempt in trace[:-1]
        )
        if (
            not all(expected_repair_triggers)
            or repair_triggers != expected_repair_triggers
        ):
            raise ValueError(
                "repair requests differ from provider attempt diagnostics"
            )
        repair_orders = tuple(
            sorted(
                (
                    order
                    for order in self.repair_work_orders.values()
                    if order.parent_work_order_id == work.id
                ),
                key=lambda order: order.attempt,
            )
        )
        if work.workflow_profile in {"conjecture.active.v1", "inquiry.active.v1"}:
            if len(repair_orders) != len(trace) - 1:
                raise ValueError(
                    "repair work orders differ from provider attempt lineage"
                )
            for repair_order, rejected_attempt in zip(
                repair_orders,
                trace[:-1],
                strict=True,
            ):
                expected_attempt = int(getattr(rejected_attempt, "attempt", -1)) + 1
                if (
                    repair_order.attempt != expected_attempt
                    or repair_order.rejected_prompt_ref
                    != getattr(rejected_attempt, "prompt_ref", "")
                    or repair_order.rejected_raw_ref
                    != getattr(rejected_attempt, "raw_ref", "")
                    or repair_order.rejected_diagnostic_ref
                    != getattr(rejected_attempt, "diagnostic_ref", "")
                    or repair_order.validation_pointer
                    != getattr(rejected_attempt, "validation_path", "")
                    or repair_order.authorized_subtree_pointer
                    != getattr(rejected_attempt, "repair_scope", "")
                    or repair_order.remaining_local_attempts
                    != work.capability_grant.max_local_repairs - expected_attempt + 1
                ):
                    raise ValueError(
                        "repair work order differs from rejected provider attempt"
                    )
        school_receipt = getattr(call, "school_route", None)
        if work.school_id is None:
            if school_receipt is not None:
                raise ValueError("provider call adds an unauthorized school route")
        elif (
            school_receipt is None
            or school_receipt.school_id != work.school_id
            or school_receipt.role != "conjecturer"
            or school_receipt.seat != work.route_lease.seat
            or school_receipt.endpoint_id != work.route_lease.endpoint_id
            or school_receipt.route_sha256 != work.route_lease.route_sha256
            or school_receipt.contract_id != work.contract_id
        ):
            raise ValueError("provider call differs from its school authority")
        context_receipt = getattr(call, "conjecture_context", None)
        if work.advisory_context_ref is None:
            if context_receipt is not None:
                raise ValueError("provider call adds unauthorized advisory context")
        elif (
            context_receipt is None
            or context_receipt.manifest_digest != work.manifest_digest
            or context_receipt.problem_id != work.problem_ref
            or context_receipt.school_id != work.school_id
            or context_receipt.formal_fence_seq != work.formal_fence_seq
            or context_receipt.scratch_fence_seq != work.scratch_fence_seq
            or context_receipt.advisory_context_ref != work.advisory_context_ref
        ):
            raise ValueError("provider call differs from its advisory-context authority")
        if len(trace) != proposal.attempt_count:
            raise ValueError("proposal attempt count differs from its attempt trace")
        if tuple(attempt.attempt for attempt in trace) != tuple(range(len(trace))):
            raise ValueError("proposal attempt trace has non-canonical indices")
        if any(attempt.usage_unknown and attempt.tokens for attempt in trace):
            raise ValueError("attempt with unknown usage must record zero tokens")
        known_trace_tokens = sum(
            attempt.tokens for attempt in trace if not attempt.usage_unknown
        )
        if known_trace_tokens != call.tokens:
            raise ValueError("provider-call spend differs from attempt-trace token total")
        if any(attempt.usage_unknown and attempt.valid for attempt in trace):
            raise ValueError("attempt with unknown usage cannot be valid")
        if outcome in _VALID_PROPOSAL_OUTCOMES:
            if not trace[-1].valid or any(attempt.valid for attempt in trace[:-1]):
                raise ValueError(
                    "valid proposal outcome differs from attempt-trace validity"
                )
        elif any(attempt.valid for attempt in trace):
            raise ValueError("failed proposal outcome differs from attempt-trace validity")
        has_unknown_usage = any(attempt.usage_unknown for attempt in trace)
        if (
            outcome == ProposalValidationOutcome.TRANSPORT_FAILED
            and not has_unknown_usage
        ) or (
            outcome == ProposalValidationOutcome.REPAIR_EXHAUSTED
            and has_unknown_usage
        ):
            raise ValueError(
                "failed proposal outcome differs from attempt usage evidence"
            )
        if any(
            attempt.contract_id != work.contract_id
            or attempt.seat != work.route_lease.seat
            or attempt.endpoint_id != work.route_lease.endpoint_id
            or attempt.route_sha256 != work.route_lease.route_sha256
            for attempt in trace
        ):
            raise ValueError("proposal provider call differs from its route authority")

    def _validate_guard(
        self,
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        guard: GuardResultV1,
    ) -> None:
        proposal = self.proposal_receipts.get(guard.proposal_receipt_id)
        if (
            guard.id != decision.trigger_ref
            or guard.id != decision.guard_result_ref
            or guard.work_order_id != work.id
            or proposal is None
            or proposal.work_order_id != work.id
            or {item.candidate_ref for item in guard.findings}
            != set(proposal.candidate_payload_refs)
        ):
            raise ValueError("guard result differs from its proposal authority")
        expected_kind, expected_outputs = _guard_transition(guard)
        if (
            decision.transition_kind != expected_kind
            or tuple(decision.output_refs) != tuple(expected_outputs)
        ):
            raise ValueError("guard disposition differs from its transition decision")

    def _validate_context_request(
        self,
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        state: WorkflowProcessStateV1,
    ) -> None:
        if decision.transition_kind != TransitionKind.CONTEXT_REQUESTED:
            return
        current = state.work_item(work.id)
        proposal = (
            self.proposal_receipts.get(current.proposal_receipt_id)
            if current is not None and current.proposal_receipt_id is not None
            else None
        )
        if (
            proposal is None
            or proposal.context_request_hash is None
            or proposal.context_request_ref is None
            or decision.trigger_ref != proposal.context_request_hash
        ):
            raise ValueError(
                "context-request trigger differs from its stored proposal receipt"
            )

    def _validate_context_decision(
        self,
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        state: WorkflowProcessStateV1,
    ) -> None:
        if decision.transition_kind not in {
            TransitionKind.CONTEXT_GRANTED,
            TransitionKind.CONTEXT_DENIED,
        }:
            return
        current = state.work_item(work.id)
        proposal = (
            self.proposal_receipts.get(current.proposal_receipt_id)
            if current is not None and current.proposal_receipt_id is not None
            else None
        )
        if (
            current is None
            or current.status != WorkItemStatus.CONTEXT_PENDING
            or proposal is None
            or proposal.context_request_hash is None
            or proposal.context_request_ref is None
        ):
            raise ValueError("context decision has no pending stored request")
        if not (
            decision.trigger_ref.startswith("sha256:")
            and len(decision.trigger_ref) == 71
        ):
            raise ValueError("context decision requires a canonical decision reference")

    def _validate_follow_up_work(self, work: WorkOrderEnvelopeV1) -> None:
        parent_ref = work.input_refs[-1] if work.input_refs else None
        parent = self.work_orders.get(parent_ref) if parent_ref is not None else None
        if parent is None:
            return
        parent_branch = self.branches[self.work_to_branch[parent.id]]
        parent_item = parent_branch.process_state.work_item(parent.id)
        if parent_item is None or parent_item.status != WorkItemStatus.FINISHED:
            raise ValueError("context follow-up predates closure of its parent work")
        grants = [
            prior
            for prior in self.decisions.values()
            if prior.work_order_id == parent.id
            and prior.transition_kind == TransitionKind.CONTEXT_GRANTED
        ]
        if len(grants) != 1:
            raise ValueError("context follow-up requires one parent grant")
        parent_grant = parent.capability_grant
        expected_remaining = parent_grant.remaining_context_expansions - 1
        child_grant = work.capability_grant
        if expected_remaining < 0 or (
            child_grant.remaining_context_expansions != expected_remaining
            or child_grant.max_candidates != parent_grant.max_candidates
            or child_grant.max_local_repairs != parent_grant.max_local_repairs
        ):
            raise ValueError("context follow-up does not reduce parent capability")
        expected_inputs = tuple(dict.fromkeys((*parent.input_refs, parent.id)))
        if (
            work.id == parent.id
            or work.input_refs != expected_inputs
            or work.advisory_context_ref is None
            or work.advisory_context_ref == parent.advisory_context_ref
            or work.problem_ref != parent.problem_ref
            or work.school_id != parent.school_id
            or work.route_lease != parent.route_lease
            or work.contract_id != parent.contract_id
            or work.manifest_digest != parent.manifest_digest
            or work.workflow_profile != parent.workflow_profile
            or work.repair_policy_ref != parent.repair_policy_ref
            or work.task_payload_schema_id != parent.task_payload_schema_id
            or work.task_payload_ref != parent.task_payload_ref
            or work.task_payload_value != parent.task_payload_value
        ):
            raise ValueError("context follow-up differs from its parent authority")

    def _plan(
        self,
        payload: ControlEventPayload,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
        *,
        prior_calls: Any = None,
        event_seq: int | None = None,
    ) -> _PlannedApply:
        payload = _canonical(type(payload), payload)
        records = _record_map(resolved_records)
        if tuple(records) != tuple(payload.outputs):
            raise ValueError("resolved workflow records differ from control outputs")
        decision_entry = records.get(payload.decision_ref)
        if decision_entry is None or decision_entry[0] != "workflow-transition-decision":
            raise ValueError("control decision_ref does not name one transition decision")
        decision = decision_entry[1]
        assert isinstance(decision, TransitionDecisionV1)
        if decision.id in self.decisions:
            raise ValueError("duplicate transition decision")
        if tuple(payload.inputs) != (decision.work_order_id, decision.trigger_ref):
            raise ValueError("control inputs differ from transition decision")

        supplied_work = next(
            (
                value
                for schema, value in records.values()
                if schema == "workflow-work-order"
            ),
            None,
        )
        if supplied_work is not None and not isinstance(supplied_work, WorkOrderEnvelopeV1):
            raise TypeError("workflow work-order record has the wrong model")
        work = supplied_work or self.work_orders.get(decision.work_order_id)
        if work is None:
            raise ValueError("transition decision names an unknown work order")
        if supplied_work is not None and supplied_work.id != decision.work_order_id:
            raise ValueError("control event supplies another work order")
        if (
            supplied_work is not None
            and decision.transition_kind == TransitionKind.WORK_ENABLED
        ):
            self._validate_follow_up_work(supplied_work)

        expected_schemas = ["workflow-transition-decision"]
        if decision.transition_kind == TransitionKind.WORK_ENABLED:
            expected_schemas.insert(0, "workflow-work-order")
        repair_work_order = next(
            (
                value
                for schema, value in records.values()
                if schema == "workflow-repair-work-order"
            ),
            None,
        )
        if repair_work_order is not None and not isinstance(
            repair_work_order, RepairWorkOrderV1
        ):
            raise TypeError("workflow repair-work-order record has the wrong model")
        if (
            repair_work_order is not None
            and repair_work_order.id in self.repair_work_orders
        ):
            raise ValueError("duplicate repair work order")
        if decision.transition_kind == TransitionKind.REPAIR_REQUESTED:
            if decision.workflow_profile in {"conjecture.active.v1", "inquiry.active.v1"}:
                expected_schemas.insert(0, "workflow-repair-work-order")
                if not isinstance(repair_work_order, RepairWorkOrderV1):
                    raise ValueError(
                        "active repair request requires one repair work order"
                    )
            elif repair_work_order is not None:
                expected_schemas.insert(0, "workflow-repair-work-order")
        elif repair_work_order is not None:
            raise ValueError("only a repair request may carry repair work authority")
        proposal = next(
            (
                value
                for schema, value in records.values()
                if schema == "workflow-proposal-receipt"
            ),
            None,
        )
        if decision.transition_kind in _PROVIDER_TRANSITIONS:
            expected_schemas.insert(0, "workflow-proposal-receipt")
            if not isinstance(proposal, ProposalReceiptV1):
                raise ValueError("provider-result transition requires one proposal receipt")
        guard = next(
            (
                value
                for schema, value in records.values()
                if schema == "workflow-guard-result"
            ),
            None,
        )
        if decision.transition_kind in _GUARDED_TRANSITIONS:
            expected_schemas.insert(0, "workflow-guard-result")
            if not isinstance(guard, GuardResultV1):
                raise ValueError("guarded transition requires one guard result")
        actual_schemas = [schema for schema, _value in records.values()]
        if actual_schemas != expected_schemas:
            raise ValueError("control outputs have the wrong transition record shape")

        branch_id, state, new_branch = self._branch_for(decision, supplied_work)
        prior_repair_requests = sum(
            prior.work_order_id == work.id
            and prior.transition_kind == TransitionKind.REPAIR_REQUESTED
            for prior in self.decisions.values()
        )
        if decision.transition_kind == TransitionKind.REPAIR_REQUESTED:
            if prior_repair_requests >= work.capability_grant.max_local_repairs:
                raise ValueError("work order has exhausted local-repair authority")
            if any(
                prior.work_order_id == work.id
                and prior.transition_kind == TransitionKind.REPAIR_REQUESTED
                and prior.trigger_ref == decision.trigger_ref
                for prior in self.decisions.values()
            ):
                raise ValueError("repair diagnostic was already consumed")
            if repair_work_order is not None:
                self._validate_repair_work_order(
                    work,
                    decision,
                    repair_work_order,
                    prior_repair_requests,
                )
        if decision.transition_kind == TransitionKind.REPAIR_EXHAUSTED and any(
            prior.work_order_id == work.id
            and prior.transition_kind == TransitionKind.REPAIR_EXHAUSTED
            for prior in self.decisions.values()
        ):
            raise ValueError("work order already emitted repair exhaustion")
        if (
            proposal is not None
            and proposal.attempt_count - 1 != prior_repair_requests
        ):
            raise ValueError(
                "proposal attempts differ from durable repair-request authority"
            )
        self._validate_work_decision(work, decision, state)
        self._validate_context_request(work, decision, state)
        self._validate_context_decision(work, decision, state)
        self._validate_observed_call_capability(
            work,
            decision,
            prior_calls,
            event_seq,
        )
        if proposal is not None:
            self._validate_proposal(
                work,
                decision,
                proposal,
                state,
                prior_calls,
                event_seq,
            )
        if guard is not None:
            self._validate_guard(work, decision, guard)
        next_state = apply_decision(state, decision)
        return _PlannedApply(
            decision=decision,
            work_order=work,
            repair_work_order=repair_work_order,
            proposal=proposal,
            guard=guard,
            branch_id=branch_id,
            next_state=next_state,
            new_branch=new_branch,
        )

    def validate(
        self,
        payload: ControlEventPayload,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
        *,
        prior_calls: Any = None,
        event_seq: int | None = None,
    ) -> None:
        self._plan(
            payload,
            resolved_records,
            prior_calls=prior_calls,
            event_seq=event_seq,
        )

    def _apply_terminal_commitment(
        self,
        event: Any,
        payload: ControlEventPayloadV3,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
    ) -> None:
        """Fill one manifest-owned terminal-epoch latch exactly once."""

        records = _record_map(resolved_records)
        if tuple(records) != tuple(payload.outputs):
            raise ValueError(
                "resolved terminal commitment differs from control outputs"
            )
        entry = records.get(payload.decision_ref)
        if (
            entry is None
            or entry[0] != "workflow-run-terminal-commitment-v1"
            or len(records) != 2
        ):
            raise ValueError("terminal commitment event has the wrong record shape")
        commitment = entry[1]
        assert isinstance(commitment, RunTerminalCommitmentV1)
        draft_entry = records.get(commitment.result_draft_ref)
        if (
            draft_entry is None
            or draft_entry[0] != "workflow-run-terminal-result-draft-v1"
        ):
            raise ValueError("terminal commitment lacks its result draft")
        draft = draft_entry[1]
        assert isinstance(draft, RunTerminalResultDraftV1)
        manifest = self._run_manifest
        policy = getattr(manifest, "terminal_commitment_policy", None)
        if manifest is None or policy is None:
            raise ValueError(
                "terminal commitment requires manifest-owned terminal authority"
            )
        seq = int(getattr(event, "seq"))
        if commitment.expected_commitment_event_seq != seq:
            raise ValueError("terminal commitment differs from its event fence")
        if (
            commitment.manifest_sha256 != manifest.sha256
            or commitment.run_id != manifest.sha256
            or draft.manifest_sha256 != manifest.sha256
            or draft.run_id != manifest.sha256
            or draft.terminal_epoch != commitment.terminal_epoch
        ):
            raise ValueError("terminal commitment belongs to another run manifest")
        epoch = commitment.terminal_epoch
        if epoch != self.current_terminal_epoch:
            raise ValueError("terminal commitment names a non-current epoch")
        if epoch in self.terminal_commitments_by_epoch:
            raise ValueError("terminal epoch already has a canonical commitment")
        if epoch == 0:
            if (
                commitment.parent_terminal_commitment_ref is not None
                or commitment.opening_resume_ref is not None
            ):
                raise ValueError("terminal epoch zero cannot rewrite a parent")
        else:
            parent = self.terminal_commitments_by_epoch.get(epoch - 1)
            opening = self.terminal_epoch_opening_resume_ref.get(epoch)
            if (
                parent is None
                or commitment.parent_terminal_commitment_ref != parent.id
                or opening is None
                or commitment.opening_resume_ref != opening
            ):
                raise ValueError("terminal child epoch differs from resume authority")
        if tuple(payload.inputs)[1] != commitment.stop_record_digest:
            raise ValueError("terminal commitment trigger differs from its stop")
        draft_stop = draft.result_body.get("stop")
        draft_summary = draft.result_body.get("model_execution")
        if (
            not isinstance(draft_stop, Mapping)
            or draft_stop.get("digest") != commitment.stop_record_digest
            or draft_stop.get("event_seq")
            != commitment.reasoning_event_horizon_seq
            or draft.result_body.get("state") != commitment.terminal_status
            or not isinstance(draft_summary, Mapping)
            or draft_summary.get("event_horizon_seq")
            != commitment.reasoning_event_horizon_seq
            or sha256_hex(canonical_json(dict(draft_summary)))
            != commitment.model_execution_summary_digest
        ):
            raise ValueError("terminal result draft differs from its commitment")
        if commitment.terminal_source == "workflow_lifecycle":
            terminal = self.terminal_lifecycle_decision
            if (
                terminal is None
                or tuple(payload.inputs)[0] != terminal.id
                or commitment.lifecycle_decision_ref != terminal.id
                or commitment.reasoning_event_horizon_seq
                != terminal.stop_event_seq
                or commitment.stop_record_digest != terminal.stop_record_digest
                or commitment.stop_reason
                != terminal.deterministic_decision.reason
            ):
                raise ValueError(
                    "terminal commitment differs from lifecycle authority"
                )
        else:
            if tuple(payload.inputs)[0] != commitment.id:
                raise ValueError(
                    "application terminal commitment has a foreign source"
                )
            source_inputs = self.event_inputs_by_seq.get(
                commitment.reasoning_event_horizon_seq
            )
            from deepreason.runtime.terminal_authority import (
                validate_application_stop_source,
            )

            validate_application_stop_source(
                source_inputs,
                dict(draft_stop),
                event_seq=commitment.reasoning_event_horizon_seq,
            )
        # The summary is a deterministic projection of this exact replay
        # prefix. Validate its digest here so neither the writer nor a later
        # result payload can invent terminal execution history.
        from types import SimpleNamespace

        from deepreason.application.models import derive_model_execution_summary

        horizon_events = tuple(
            SimpleNamespace(
                seq=seq,
                outputs=list(outputs),
                llm=(
                    self.transaction_calls_by_seq.get(seq)
                    or self.calls_by_seq.get(seq)
                ),
            )
            for seq, outputs in sorted(self.event_outputs_by_seq.items())
            if seq <= commitment.reasoning_event_horizon_seq
        )
        summary = derive_model_execution_summary(
            SimpleNamespace(
                log=SimpleNamespace(read=lambda: horizon_events),
                workflow_state=self,
            ),
            manifest,
        ).model_copy(
            update={
                "event_horizon_seq": commitment.reasoning_event_horizon_seq
            }
        )
        expected_summary_digest = sha256_hex(
            canonical_json(
                summary.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                )
            )
        )
        if (
            commitment.model_execution_summary_digest
            != expected_summary_digest
        ):
            raise ValueError(
                "terminal commitment summary differs from replayed execution"
            )
        self.terminal_commitments_by_epoch[epoch] = commitment
        self.terminal_commitment_event_seq[commitment.id] = seq
        self.event_seqs.append(seq)

    def _apply_lifecycle(
        self,
        event: Any,
        payload: ControlEventPayload,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
    ) -> None:
        """Validate and index one terminal lifecycle event without re-planning work."""

        from deepreason.runtime.stop import StopController, build_stop_record
        from deepreason.workflow.lifecycle import outstanding_work_snapshot

        records = _record_map(resolved_records)
        if tuple(records) != tuple(payload.outputs):
            raise ValueError("resolved lifecycle records differ from control outputs")
        expected_schemas = [
            "workflow-stop-metrics-observation",
            "workflow-lifecycle-snapshot",
            "workflow-lifecycle-decision",
        ]
        if [schema for schema, _record in records.values()] != expected_schemas:
            raise ValueError("lifecycle control outputs have the wrong record shape")
        observation = next(
            record
            for schema, record in records.values()
            if schema == "workflow-stop-metrics-observation"
        )
        snapshot = next(
            record
            for schema, record in records.values()
            if schema == "workflow-lifecycle-snapshot"
        )
        decision = next(
            record
            for schema, record in records.values()
            if schema == "workflow-lifecycle-decision"
        )
        assert isinstance(observation, StopMetricsObservationV1)
        assert isinstance(snapshot, WorkflowLifecycleSnapshotV1)
        assert isinstance(decision, WorkflowLifecycleDecisionV1)
        seq = int(getattr(event, "seq"))
        if self.terminal_decision_id is not None:
            raise ValueError("workflow already has a terminal lifecycle decision")
        if payload.decision_ref != decision.id or tuple(payload.inputs) != (
            observation.id,
            snapshot.id,
        ):
            raise ValueError("lifecycle Control references differ from its decision")
        if (
            decision.metrics_observation_ref != observation.id
            or decision.checkpoint_ref != snapshot.id
            or decision.stop_event_seq != seq
            or snapshot.event_fence_seq != seq - 1
        ):
            raise ValueError("lifecycle decision differs from its checkpoint fence")
        process_digest = self.digest
        if not (
            observation.manifest_digest
            == snapshot.manifest_digest
            == decision.manifest_digest
        ) or not (
            observation.controller_version
            == snapshot.controller_version
            == decision.controller_version
        ):
            raise ValueError("lifecycle records belong to different authority")
        if (
            observation.process_digest != process_digest
            or snapshot.process_digest != process_digest
            or decision.previous_process_digest != process_digest
            or decision.next_process_digest != process_digest
        ):
            raise ValueError("lifecycle records differ from replayed process state")
        expected_snapshot = outstanding_work_snapshot(
            self,
            manifest_digest=decision.manifest_digest,
            controller_version=decision.controller_version,
            event_fence_seq=seq - 1,
        )
        if expected_snapshot != snapshot:
            raise ValueError("lifecycle outstanding-work snapshot does not replay")
        if snapshot.outstanding_work or snapshot.unconsumed_bound_call_seqs:
            raise ValueError("STOPPED cannot forget unfinished workflow authority")
        verifier = StopController(
            observation.stop_policy,
            state=observation.controller_state_before,
        )
        if verifier.evaluate(observation.metrics) != decision.deterministic_decision:
            raise ValueError("lifecycle decision differs from deterministic stop policy")
        if verifier.snapshot() != observation.controller_state_after:
            raise ValueError("lifecycle controller state does not replay")
        stop_record = build_stop_record(
            reason=decision.deterministic_decision.reason,
            policy=observation.stop_policy,
            metrics=observation.metrics,
            event_seq=seq,
        )
        if stop_record["digest"] != decision.stop_record_digest:
            raise ValueError("lifecycle run-stop digest does not replay")
        self.stop_observations[observation.id] = observation
        self.lifecycle_snapshots[snapshot.id] = snapshot
        self.lifecycle_decisions[decision.id] = decision
        self.terminal_decision_id = decision.id
        self.current_resume_decision_id = None
        self.event_seqs.append(seq)

    def _apply_resume(
        self,
        event: Any,
        payload: ControlEventPayload,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
    ) -> None:
        """Validate and enact one RESUMED authority transition."""

        from deepreason.workflow.lifecycle import (
            RESUMABLE_STOP_REASONS,
            outstanding_work_snapshot,
        )

        records = _record_map(resolved_records)
        if tuple(records) != tuple(payload.outputs):
            raise ValueError("resolved resume records differ from control outputs")
        if [schema for schema, _record in records.values()] != [
            "workflow-lifecycle-snapshot",
            "workflow-resume-decision",
        ]:
            raise ValueError("resume Control outputs have the wrong record shape")
        snapshot = next(
            record
            for schema, record in records.values()
            if schema == "workflow-lifecycle-snapshot"
        )
        decision = next(
            record
            for schema, record in records.values()
            if schema == "workflow-resume-decision"
        )
        assert isinstance(snapshot, WorkflowLifecycleSnapshotV1)
        assert isinstance(decision, WorkflowResumeDecisionV1)
        terminal = self.terminal_lifecycle_decision
        terminal_snapshot = self.terminal_lifecycle_snapshot
        terminal_observation = self.terminal_stop_observation
        if terminal is None or terminal_snapshot is None or terminal_observation is None:
            raise ValueError("RESUMED requires one active typed STOPPED decision")
        seq = int(getattr(event, "seq"))
        if payload.decision_ref != decision.id or tuple(payload.inputs) != (
            terminal.id,
            snapshot.id,
        ):
            raise ValueError("resume Control references differ from its decision")
        if (
            decision.resume_snapshot_ref != snapshot.id
            or decision.resume_event_seq != seq
            or snapshot.event_fence_seq != seq - 1
            or decision.continuation_seq != len(self.resume_decisions)
        ):
            raise ValueError("resume decision differs from its event fence")
        if (
            decision.prior_terminal_decision_ref != terminal.id
            or decision.prior_metrics_observation_ref != terminal_observation.id
            or decision.prior_checkpoint_ref != terminal_snapshot.id
            or decision.prior_stop_digest != terminal.stop_record_digest
            or decision.prior_process_digest != terminal.next_process_digest
            or decision.controller_state
            != terminal_observation.controller_state_after
        ):
            raise ValueError("resume decision differs from its terminal authority")
        if terminal.deterministic_decision.reason not in RESUMABLE_STOP_REASONS:
            raise ValueError("terminal stop reason does not authorize RESUMED")
        if (
            decision.manifest_digest != terminal.manifest_digest
            or decision.controller_version != terminal.controller_version
            or decision.workflow_profile != terminal.workflow_profile
            or snapshot.manifest_digest != terminal.manifest_digest
            or snapshot.controller_version != terminal.controller_version
        ):
            raise ValueError("resume records belong to another controller authority")
        process_digest = self.digest
        if (
            decision.previous_process_digest != process_digest
            or decision.next_process_digest != process_digest
            or snapshot.process_digest != process_digest
        ):
            raise ValueError("resume records differ from replayed process state")
        expected_snapshot = outstanding_work_snapshot(
            self,
            manifest_digest=decision.manifest_digest,
            controller_version=decision.controller_version,
            event_fence_seq=seq - 1,
        )
        if expected_snapshot != snapshot:
            raise ValueError("resume outstanding-work snapshot does not replay")
        if snapshot.outstanding_work or snapshot.unconsumed_bound_call_seqs:
            raise ValueError("RESUMED cannot forget unfinished workflow authority")
        manifest = self._run_manifest
        commitment_policy = getattr(manifest, "terminal_commitment_policy", None)
        if commitment_policy is not None:
            parent_commitment = self.terminal_commitments_by_epoch.get(
                self.current_terminal_epoch
            )
            expected_epoch = self.current_terminal_epoch + 1
            if parent_commitment is None:
                raise ValueError(
                    "RESUMED requires the current epoch terminal commitment"
                )
            if (
                decision.prior_terminal_commitment_ref != parent_commitment.id
                or decision.opened_terminal_epoch != expected_epoch
            ):
                raise ValueError(
                    "RESUMED differs from terminal commitment authority"
                )
        elif (
            decision.prior_terminal_commitment_ref is not None
            or decision.opened_terminal_epoch is not None
        ):
            raise ValueError(
                "historical replay cannot fabricate terminal commitment epochs"
            )
        self.lifecycle_snapshots[snapshot.id] = snapshot
        self.resume_decisions[decision.id] = decision
        self.resume_decision_event_seq[decision.id] = seq
        self.current_resume_decision_id = decision.id
        self.terminal_decision_id = None
        if commitment_policy is not None:
            assert decision.opened_terminal_epoch is not None
            self.current_terminal_epoch = decision.opened_terminal_epoch
            self.terminal_epoch_opening_resume_ref[
                self.current_terminal_epoch
            ] = decision.id
        self.event_seqs.append(seq)

    def _apply_transaction(
        self,
        event: Any,
        payload: ControlEventPayloadV3,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
    ) -> None:
        """Validate and materialize one controller-v3 transaction append."""

        records = _record_map(resolved_records)
        if tuple(records) != tuple(payload.outputs):
            raise ValueError("resolved transaction records differ from control outputs")
        transition_entry = records.get(payload.decision_ref)
        if (
            transition_entry is None
            or transition_entry[0] != "workflow-work-lifecycle-transition-v1"
        ):
            raise ValueError("control.event.v3 decision_ref is not a lifecycle transition")
        transition = transition_entry[1]
        assert isinstance(transition, WorkLifecycleTransitionV1)
        if tuple(payload.inputs) != (transition.work_id, transition.trigger_ref):
            raise ValueError("transaction inputs differ from its transition")
        if tuple(records)[-1] != transition.id:
            raise ValueError("transaction transition must be the final output")
        phase_records = [
            (schema, record)
            for object_id, (schema, record) in records.items()
            if object_id != transition.id
        ]
        if any(
            getattr(record, "work_id", None) != transition.work_id
            or getattr(record, "attempt_index", None) != transition.attempt_index
            for _schema, record in phase_records
        ):
            raise ValueError("transaction outputs belong to another work attempt")

        kind = transition.transition_kind
        expected_action = (
            "provider_result"
            if kind == WorkTransitionKind.PROVIDER_RESULT
            else "work_transition"
        )
        if payload.action != expected_action:
            raise ValueError("transaction control action differs from its transition")
        seq = int(getattr(event, "seq"))
        item = self.transaction_work.get(transition.work_id)
        if kind == WorkTransitionKind.WORK_PREPARED:
            if item is not None or [schema for schema, _record in phase_records] != [
                "workflow-work-preparation-v1"
            ]:
                raise ValueError("work_prepared must introduce exactly one preparation")
            preparation = phase_records[0][1]
            assert isinstance(preparation, WorkPreparationV1)
            if (
                preparation.id != transition.work_id
                or preparation.trigger_ref != transition.trigger_ref
            ):
                raise ValueError("preparation transition differs from prepared authority")
            if (
                self._route_seat_key(preparation.route_lease)
                in self.insufficient_capability_by_route_seat
            ):
                raise ValueError(
                    "work preparation follows terminal route-seat capability"
                )
            manifest = self._run_manifest
            if manifest is not None:
                if self.route_seat_model_classification is None:
                    raise ValueError(
                        "work preparation precedes model classification authority"
                    )
                self._validate_preparation_behavioral_authority(
                    manifest,
                    preparation,
                )
                self._validate_preparation_decomposition_authority(preparation)
            item = TransactionReplayItem(preparation=preparation)
            self.transaction_work[preparation.id] = item
        elif item is None:
            raise ValueError("transaction must begin with durable work preparation")
        elif item.terminal is not None:
            raise ValueError("transaction transition follows typed termination")
        elif kind == WorkTransitionKind.WORK_ISSUED:
            if item.issued:
                raise ValueError("transactional work was already issued")
            if (
                self._route_seat_key(item.preparation.route_lease)
                in self.insufficient_capability_by_route_seat
            ):
                raise ValueError(
                    "work issuance follows terminal route-seat capability"
                )
            plans = [
                record
                for schema, record in phase_records
                if schema == "workflow-context-pack-plan-v1"
            ]
            reservations = [
                record
                for schema, record in phase_records
                if schema == "workflow-token-reservation-v2"
            ]
            exposures = [
                record
                for schema, record in phase_records
                if schema == "workflow-context-exposure-v2"
            ]
            bundles = [
                record
                for schema, record in phase_records
                if schema == "workflow-dispatch-authorization-v1"
            ]
            actual_schemas = [schema for schema, _record in phase_records]
            expected_schemas = [
                *("workflow-context-pack-plan-v1" for _plan in plans),
                "workflow-token-reservation-v2",
                "workflow-context-exposure-v2",
                "workflow-dispatch-authorization-v1",
            ]
            if (
                actual_schemas != expected_schemas
                or len(reservations) != 1
                or len(exposures) != 1
                or len(bundles) != 1
            ):
                raise ValueError("work_issued has a noncanonical record shape")
            reservation = reservations[0]
            exposure = exposures[0]
            bundle = bundles[0]
            assert isinstance(reservation, TokenReservationV2)
            assert isinstance(exposure, ContextExposureReceiptV2)
            assert isinstance(bundle, DispatchAuthorizationBundleV1)
            if (
                tuple(exposure.context_plan_refs) != tuple(plan.id for plan in plans)
                or tuple(exposure.exposed_items)
                != tuple(context for plan in plans for context in plan.items)
                or exposure.prompt_sha256 != reservation.prompt_sha256
                or bundle.prompt_sha256 != reservation.prompt_sha256
                or bundle.reservation_ref != reservation.id
                or bundle.exposure_receipt_ref != exposure.id
                or bundle.issue_transition_ref != transition.id
                or bundle.contract_id != item.preparation.contract_id
                or bundle.route_lease != item.preparation.route_lease
            ):
                raise ValueError("issued authority records do not bind one request")
            item.plans.update({plan.id: plan for plan in plans})
            item.reservation = reservation
            item.exposure = exposure
            item.authorization = bundle
        elif kind == WorkTransitionKind.BUDGET_DENIED:
            if item.issued or [schema for schema, _record in phase_records] != [
                "workflow-work-terminal-v1"
            ]:
                raise ValueError("budget denial cannot follow issuance")
            terminal = phase_records[0][1]
            assert isinstance(terminal, WorkTerminalV1)
            if terminal.status != "budget_denied":
                raise ValueError("budget_denied transition requires its typed terminal")
            item.terminal = terminal
        elif kind == WorkTransitionKind.PROVIDER_RESULT:
            if not item.issued or [schema for schema, _record in phase_records] != [
                "workflow-provider-attempt-v1"
            ]:
                raise ValueError("provider result requires issued authority")
            if (
                self._route_seat_key(item.preparation.route_lease)
                in self.insufficient_capability_by_route_seat
            ):
                raise ValueError(
                    "provider result follows terminal route-seat capability"
                )
            attempt = phase_records[0][1]
            assert isinstance(attempt, ProviderAttemptV1)
            if attempt.attempt_index in item.provider_attempts:
                raise ValueError("provider attempt is already durable")
            call = getattr(event, "llm", None)
            if call is None or call.work_order_id != transition.work_id:
                raise ValueError("provider result requires its work-bound LLM call")
            if (
                item.authorization is None
                or call.dispatch_authorization_ref != item.authorization.id
                or attempt.authorization_bundle_ref != item.authorization.id
                or attempt.contract_id != item.authorization.contract_id
                or attempt.route_lease != item.authorization.route_lease
                or attempt.prompt_sha256 != item.authorization.prompt_sha256
                or attempt.raw_ref != (call.raw_ref or None)
            ):
                raise ValueError("provider result differs from issued authority")
            if attempt.usage_status == "exact" and (
                int(attempt.prompt_tokens or 0) + int(attempt.completion_tokens or 0)
                != call.tokens
            ):
                raise ValueError("provider result usage differs from its LLM call")
            item.provider_attempts[attempt.attempt_index] = attempt
            item.provider_calls[attempt.attempt_index] = call
        elif kind == WorkTransitionKind.SEMANTIC_ADMISSION:
            if [schema for schema, _record in phase_records] != [
                "workflow-semantic-admission-v1"
            ]:
                raise ValueError("semantic admission has a noncanonical record shape")
            admission = phase_records[0][1]
            assert isinstance(admission, SemanticAdmissionV1)
            attempt = item.provider_attempts.get(admission.attempt_index)
            if (
                attempt is None
                or admission.provider_attempt_ref != attempt.id
                or admission.attempt_index in item.admissions
            ):
                raise ValueError("semantic admission lacks one durable provider result")
            item.admissions[admission.attempt_index] = admission
        elif kind == WorkTransitionKind.WORK_TERMINATED:
            schemas = [schema for schema, _record in phase_records]
            if schemas not in (
                ["workflow-work-terminal-v1"],
                [
                    "workflow-compact-recovery-transition-v1",
                    "workflow-work-terminal-v1",
                ],
                [
                    "workflow-route-seat-insufficient-capability-v1",
                    "workflow-work-terminal-v1",
                ],
                [
                    "workflow-compact-recovery-transition-v1",
                    "workflow-route-seat-insufficient-capability-v1",
                    "workflow-work-terminal-v1",
                ],
            ):
                raise ValueError("work termination has a noncanonical record shape")
            compact = next(
                (
                    record
                    for schema, record in phase_records
                    if schema == "workflow-compact-recovery-transition-v1"
                ),
                None,
            )
            insufficient = next(
                (
                    record
                    for schema, record in phase_records
                    if schema == "workflow-route-seat-insufficient-capability-v1"
                ),
                None,
            )
            terminal = phase_records[-1][1]
            if compact is not None:
                assert isinstance(compact, CompactRecoveryTransitionV1)
            if insufficient is not None:
                assert isinstance(insufficient, RouteSeatInsufficientCapabilityV1)
            assert isinstance(terminal, WorkTerminalV1)
            attempt = item.provider_attempts.get(terminal.attempt_index)
            admission = item.admissions.get(terminal.attempt_index)
            if terminal.provider_attempt_ref != (attempt.id if attempt else None):
                raise ValueError("terminal provider reference does not replay")
            if terminal.semantic_admission_ref != (
                admission.id if admission else None
            ):
                raise ValueError("terminal admission reference does not replay")
            expected_status = {
                "admitted": "completed",
                "schema_exhausted": "schema_exhausted",
                "rejected": "rejected",
                "unrepairable": "rejected",
            }.get(admission.outcome) if admission is not None else None
            if terminal.status == "abandoned":
                if attempt is not None:
                    raise ValueError("abandoned recovery cannot hide a provider result")
            elif terminal.status == "transport_failed":
                if attempt is None or attempt.outcome != "transport_failure":
                    raise ValueError("transport terminal lacks a failed provider attempt")
            elif terminal.status != expected_status:
                raise ValueError("work terminal differs from semantic admission")

            policy = self._compact_policy(item.preparation)
            eligible = (
                terminal.status == "schema_exhausted"
                and admission is not None
                and policy is not None
                and self._run_manifest is not None
                and resolve_route_seat_base_profile(
                    self._run_manifest,
                    role=item.preparation.route_lease.role,
                    seat=item.preparation.route_lease.seat,
                    endpoint_id=item.preparation.route_lease.endpoint_id,
                )
                in policy.source_profiles
            )
            compact_ref = terminal.compact_recovery_transition_ref
            if eligible:
                if compact_ref is None:
                    raise ValueError(
                        "authorized schema exhaustion lacks compact recovery transition"
                    )
                if attempt is None or admission is None:
                    raise ValueError("compact recovery lacks provider admission authority")
                key = self._route_seat_key(item.preparation.route_lease)
                if compact is not None:
                    if compact.id != compact_ref:
                        raise ValueError(
                            "terminal names another compact recovery transition"
                        )
                    validated_key = self._validate_compact_transition(
                        compact, item, attempt, admission
                    )
                    if validated_key != key:
                        raise ValueError("compact recovery durable key does not replay")
                    if key in self.compact_recovery_by_route_seat:
                        raise ValueError(
                            "route seat has a duplicate compact recovery transition"
                        )
                    self.compact_recovery_by_route_seat[key] = compact
                else:
                    existing = self.compact_recovery_by_route_seat.get(key)
                    if existing is None or existing.id != compact_ref:
                        raise ValueError(
                            "terminal compact recovery reference is missing or foreign"
                        )
            elif compact is not None or compact_ref is not None:
                raise ValueError(
                    "work terminal claims unauthorized compact recovery authority"
                )

            insufficient_ref = terminal.insufficient_capability_ref
            expected_insufficient = self.insufficient_capability_fields(
                item.preparation.id,
                item.preparation.attempt_index,
            )
            if expected_insufficient is not None:
                if insufficient_ref is None:
                    raise ValueError(
                        "smallest-contract exhaustion lacks capability terminal"
                    )
                route_key = self._route_seat_key(item.preparation.route_lease)
                if insufficient is not None:
                    if insufficient.id != insufficient_ref:
                        raise ValueError(
                            "work terminal names another capability outcome"
                        )
                    if attempt is None or admission is None:
                        raise ValueError(
                            "insufficient capability lacks provider admission"
                        )
                    validated_key = self._validate_insufficient_capability(
                        insufficient,
                        item,
                        attempt,
                        admission,
                    )
                    if validated_key != route_key:
                        raise ValueError(
                            "insufficient capability route key does not replay"
                        )
                    if route_key in self.insufficient_capability_by_route_seat:
                        raise ValueError(
                            "route seat has duplicate insufficient capability"
                        )
                    self.insufficient_capability_by_route_seat[route_key] = insufficient
                else:
                    existing = self.insufficient_capability_by_route_seat.get(
                        route_key
                    )
                    if existing is None or existing.id != insufficient_ref:
                        raise ValueError(
                            "terminal capability reference is missing or foreign"
                        )
            elif insufficient is not None or insufficient_ref is not None:
                raise ValueError(
                    "work terminal claims unauthorized insufficient capability"
                )
            item.terminal = terminal
        else:  # pragma: no cover - enum validation keeps this fail-closed
            raise ValueError("unknown controller-v3 transaction transition")

        assert item is not None
        item.transitions.append(transition)
        item.event_seqs.append(seq)
        self.event_seqs.append(seq)

    def apply(
        self,
        event: Any,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
        *,
        prior_calls: Any = None,
    ) -> None:
        payload = getattr(event, "control", None)
        if payload is None:
            raise ValueError("workflow replay accepts only typed control events")
        resolved_records = tuple(resolved_records)
        if (
            isinstance(payload, ControlEventPayloadV3)
            and payload.action in {"work_transition", "provider_result"}
        ):
            self._apply_transaction(event, payload, resolved_records)
            return
        if (
            isinstance(payload, ControlEventPayloadV3)
            and payload.action == "terminal_committed"
        ):
            self._apply_terminal_commitment(event, payload, resolved_records)
            return
        if (
            isinstance(payload, ControlEventPayloadV3)
            and payload.action == "classification_bound"
        ):
            self._apply_model_classification(event, payload, resolved_records)
            return
        if (
            isinstance(payload, ControlEventPayloadV3)
            and payload.action == "contract_decomposition_activated"
        ):
            self._apply_contract_decomposition(event, payload, resolved_records)
            return
        if (
            isinstance(payload, ControlEventPayloadV3)
            and payload.action == "contract_decomposition_completed"
        ):
            self._apply_contract_decomposition_completion(
                event, payload, resolved_records
            )
            return
        decision_entry = next(
            (
                (schema, value)
                for schema, object_id, value in resolved_records
                if object_id == payload.decision_ref
            ),
            None,
        )
        if decision_entry is not None and decision_entry[0] == "workflow-lifecycle-decision":
            if (
                isinstance(payload, ControlEventPayloadV3)
                and payload.action != "lifecycle_stopped"
            ):
                raise ValueError("controller-v3 lifecycle action is not stopped")
            self._apply_lifecycle(event, payload, resolved_records)
            return
        if decision_entry is not None and decision_entry[0] == "workflow-resume-decision":
            if (
                isinstance(payload, ControlEventPayloadV3)
                and payload.action != "lifecycle_resumed"
            ):
                raise ValueError("controller-v3 lifecycle action is not resumed")
            self._apply_resume(event, payload, resolved_records)
            return
        if isinstance(payload, ControlEventPayloadV3):
            raise ValueError("controller-v3 action differs from its decision record")
        if self.terminal_decision_id is not None:
            raise ValueError("workflow transition follows terminal lifecycle state")
        seq = int(getattr(event, "seq"))
        planned = self._plan(
            payload,
            resolved_records,
            prior_calls=(self.calls_by_seq if prior_calls is None else prior_calls),
            event_seq=seq,
        )
        decision = planned.decision
        work = planned.work_order
        if planned.new_branch:
            self.branches[planned.branch_id] = WorkflowBranchState(
                branch_id=planned.branch_id,
                process_state=planned.next_state,
            )
        branch = self.branches[planned.branch_id]
        branch.process_state = planned.next_state
        if work.id not in branch.work_order_ids:
            branch.work_order_ids.append(work.id)
        branch.decision_ids.append(decision.id)
        branch.event_seqs.append(seq)
        self.work_orders.setdefault(work.id, work)
        self.work_to_branch[work.id] = planned.branch_id
        self.decisions[decision.id] = decision
        self.decision_event_seq[decision.id] = seq
        if planned.repair_work_order is not None:
            repair = planned.repair_work_order
            self.repair_work_orders[repair.id] = repair
        if planned.proposal is not None:
            self.proposal_receipts[planned.proposal.id] = planned.proposal
        if planned.guard is not None:
            self.guard_results[planned.guard.id] = planned.guard
        self.event_seqs.append(seq)

    @property
    def outstanding_work_order_ids(self) -> tuple[str, ...]:
        outstanding = []
        for work_id, branch_id in self.work_to_branch.items():
            item = self.branches[branch_id].process_state.work_item(work_id)
            if item is not None and item.status not in {
                WorkItemStatus.FINISHED,
                WorkItemStatus.ABANDONED,
            }:
                outstanding.append(work_id)
        outstanding.extend(
            work_id
            for work_id, item in self.transaction_work.items()
            if item.outstanding
        )
        return tuple(sorted(outstanding))

    @property
    def terminal_lifecycle_decision(self) -> WorkflowLifecycleDecisionV1 | None:
        """Latest typed STOPPED authority, if this prefix is terminal."""

        if self.terminal_decision_id is None:
            return None
        return self.lifecycle_decisions[self.terminal_decision_id]

    @property
    def current_terminal_commitment(self) -> RunTerminalCommitmentV1 | None:
        """Committed authority for the current epoch, absent while it is open."""

        return self.terminal_commitments_by_epoch.get(self.current_terminal_epoch)

    @property
    def current_terminal_authority(self) -> RunTerminalCommitmentV1 | None:
        """Alias naming the only terminal head eligible for later consumers."""

        return self.current_terminal_commitment

    def terminal_commitment_ledger_payload(self) -> dict[str, Any]:
        """Stable replay projection kept separate from the process digest."""

        return {
            "schema": "terminal-commitment-ledger.v1",
            "run_id": (
                self._run_manifest.sha256 if self._run_manifest is not None else None
            ),
            "current_epoch": self.current_terminal_epoch,
            "commitments": [
                {
                    "epoch": epoch,
                    "commitment_ref": commitment.id,
                    "event_seq": self.terminal_commitment_event_seq[commitment.id],
                    "opening_resume_ref": self.terminal_epoch_opening_resume_ref.get(
                        epoch
                    ),
                }
                for epoch, commitment in sorted(
                    self.terminal_commitments_by_epoch.items()
                )
            ],
        }

    @property
    def terminal_commitment_ledger_digest(self) -> str:
        return "sha256:" + sha256_hex(
            canonical_json(self.terminal_commitment_ledger_payload())
        )

    @property
    def terminal_lifecycle_snapshot(self) -> WorkflowLifecycleSnapshotV1 | None:
        decision = self.terminal_lifecycle_decision
        return (
            self.lifecycle_snapshots[decision.checkpoint_ref]
            if decision is not None
            else None
        )

    @property
    def terminal_stop_observation(self) -> StopMetricsObservationV1 | None:
        decision = self.terminal_lifecycle_decision
        return (
            self.stop_observations[decision.metrics_observation_ref]
            if decision is not None
            else None
        )

    @property
    def terminal_controller_version(self) -> str | None:
        decision = self.terminal_lifecycle_decision
        return decision.controller_version if decision is not None else None

    @property
    def terminal_checkpoint_digest(self) -> str | None:
        decision = self.terminal_lifecycle_decision
        return decision.checkpoint_ref if decision is not None else None

    @property
    def terminal_process_digest(self) -> str | None:
        snapshot = self.terminal_lifecycle_snapshot
        return snapshot.process_digest if snapshot is not None else None

    @property
    def terminal_stop_digest(self) -> str | None:
        decision = self.terminal_lifecycle_decision
        return decision.stop_record_digest if decision is not None else None

    @property
    def current_resume_decision(self) -> WorkflowResumeDecisionV1 | None:
        if self.current_resume_decision_id is None:
            return None
        return self.resume_decisions[self.current_resume_decision_id]

    @property
    def current_resume_event_seq(self) -> int | None:
        decision = self.current_resume_decision
        return (
            self.resume_decision_event_seq[decision.id]
            if decision is not None
            else None
        )

    @property
    def post_resume_work_started(self) -> bool:
        resume_seq = self.current_resume_event_seq
        return bool(
            resume_seq is not None
            and any(seq > resume_seq for seq in self.decision_event_seq.values())
        )

    def recovery_status(self, work_order_id: str) -> WorkflowRecoveryStatus:
        branch_id = self.work_to_branch[work_order_id]
        item = self.branches[branch_id].process_state.work_item(work_order_id)
        if item is None:
            raise KeyError(work_order_id)
        mapping = {
            WorkItemStatus.ENABLED: WorkflowRecoveryStatus.ENABLED,
            WorkItemStatus.ISSUED: WorkflowRecoveryStatus.ISSUED,
            WorkItemStatus.PROPOSAL_RECEIVED: (
                WorkflowRecoveryStatus.PROVIDER_RESULT_RECEIVED
            ),
            WorkItemStatus.REPAIR_PENDING: WorkflowRecoveryStatus.REPAIR_PENDING,
            WorkItemStatus.CONTEXT_PENDING: WorkflowRecoveryStatus.CONTEXT_PENDING,
            WorkItemStatus.FINISHED: WorkflowRecoveryStatus.FINISHED,
            WorkItemStatus.ABANDONED: WorkflowRecoveryStatus.ABANDONED,
        }
        return mapping[item.status]

    @property
    def digest(self) -> str:
        payload = {
            "branches": [
                {
                    "branch_id": branch_id,
                    "process_digest": self.branches[branch_id].process_state.digest,
                    "decision_ids": list(self.branches[branch_id].decision_ids),
                    "event_seqs": list(self.branches[branch_id].event_seqs),
                }
                for branch_id in sorted(self.branches)
            ],
            "repair_work_order_ids": sorted(self.repair_work_orders),
        }
        # Preserve the exact v1/v2 replay digest for every historical root.
        # Transaction state is absent, rather than an added empty default,
        # until a controller-v3 event actually exists.
        if self.transaction_work:
            payload["transactions"] = [
                {
                    "work_id": work_id,
                    "transition_ids": [
                        transition.id for transition in item.transitions
                    ],
                    "event_seqs": list(item.event_seqs),
                    "terminal_ref": item.terminal.id if item.terminal else None,
                }
                for work_id, item in sorted(self.transaction_work.items())
            ]
        if self.compact_recovery_by_route_seat:
            payload["compact_recovery_by_route_seat"] = [
                {
                    "role": key[0],
                    "seat": key[1],
                    "endpoint_id": key[2],
                    "route_sha256": key[3],
                    "transition_ref": transition.id,
                }
                for key, transition in sorted(
                    self.compact_recovery_by_route_seat.items()
                )
            ]
        if self.insufficient_capability_by_route_seat:
            payload["insufficient_capability_by_route_seat"] = [
                {
                    "role": key[0],
                    "seat": key[1],
                    "endpoint_id": key[2],
                    "route_sha256": key[3],
                    "outcome_ref": outcome.id,
                }
                for key, outcome in sorted(
                    self.insufficient_capability_by_route_seat.items()
                )
            ]
        if self.contract_decomposition_by_source_work:
            payload["contract_decomposition_by_source_work"] = [
                {
                    "source_work_id": source_work_id,
                    "transition_ref": transition.id,
                    "event_seq": self.contract_decomposition_event_seq[transition.id],
                }
                for source_work_id, transition in sorted(
                    self.contract_decomposition_by_source_work.items()
                )
            ]
        if self.contract_decomposition_completion_by_transition:
            payload["contract_decomposition_completions"] = [
                {
                    "transition_ref": transition_ref,
                    "completion_ref": completion.id,
                }
                for transition_ref, completion in sorted(
                    self.contract_decomposition_completion_by_transition.items()
                )
            ]
        if self.route_seat_model_classification is not None:
            payload["route_seat_model_classification"] = {
                "plan_ref": self.route_seat_model_classification.id,
                "binding_ref": self.model_classification_binding.id,
                "event_seq": self.model_classification_event_seq,
            }
        return "sha256:" + sha256_hex(
            b"workflow.replay-state.v1\x00" + canonical_json(payload)
        )


def replay_workflow(
    events: Iterable[Any],
    objects: Any,
    *,
    manifest: Any | None = None,
) -> WorkflowReplayState:
    """Reconstruct workflow state from records; never run a model or reducer."""

    state = WorkflowReplayState()
    if manifest is not None and getattr(manifest, "schema_version", None) == 6:
        state.bind_run_manifest(manifest)
    for event in events:
        state.observe_event(event)
        payload = getattr(event, "control", None)
        if payload is None:
            continue
        records = []
        for object_id in event.outputs:
            schema, value = objects.get(object_id)
            records.append((schema, object_id, value))
        state.apply(event, records, prior_calls=state.calls_by_seq)
    return state


# Stable v1 spelling for callers that prefer explicit versioning.
WorkflowReplayStateV1 = WorkflowReplayState


__all__ = [
    "WorkflowBranchState",
    "WorkflowRecoveryStatus",
    "WorkflowReplayState",
    "WorkflowReplayStateV1",
    "replay_workflow",
]
