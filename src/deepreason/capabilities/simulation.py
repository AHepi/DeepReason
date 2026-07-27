"""Deterministic Tranche-A simulation controller and result reinjection data."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.models import (
    CapabilityBudgetDeltaV1,
    CapabilityTransitionV1,
    CompiledSimulationSpecV1,
    CompiledSimulationV1,
    SimulationAttemptV1,
    SimulationConsumptionV1,
    SimulationExecutionReceiptV1,
    SimulationGrantV1,
    SimulationProposalDraftV1,
    SimulationProposalV1,
    SimulationResultPackageV1,
    SimulationWorkOrderV1,
    capability_next_process_digest,
)

TRUSTED_CHECKER_SOURCE_V1 = """def check(input_item, seed, output):
    return {"pass": True, "metrics": {"declared_observables": len(output)}}
"""


class CapabilityTerminalError(RuntimeError):
    """A frozen terminal capability policy ended the inquiry."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class SimulationCapabilityController:
    """Compile semantic proposals into the one manifest-owned simulation runner."""

    def __init__(self, harness, manifest) -> None:
        self.harness = harness
        self.manifest = manifest
        topology = manifest.inquiry_capability_policy
        self.policy = topology.simulation if topology is not None else None
        if manifest.schema_version not in {5, 6} or self.policy is None:
            raise ValueError("simulation controller requires one v5+ run manifest")

    def _transition(
        self,
        proposal: SimulationProposalV1,
        lifecycle: CapabilityLifecycle,
        *,
        previous: CapabilityTransitionV1 | None,
        phase_record=None,
        reason_code: str,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> CapabilityTransitionV1:
        trigger_ref = (
            f"provider-call:{proposal.source_call_seq}" if previous is None else previous.id
        )
        budget_delta = {
            CapabilityLifecycle.PROPOSED: CapabilityBudgetDeltaV1(requests=1),
            CapabilityLifecycle.DISPATCHED: CapabilityBudgetDeltaV1(executions=1),
            CapabilityLifecycle.CONSUMED: CapabilityBudgetDeltaV1(result_follow_ups=1),
        }.get(lifecycle, CapabilityBudgetDeltaV1())
        previous_process_digest = self.harness.capability_state.process_digest
        phase_record_ref = getattr(phase_record, "id", None)
        next_process_digest = capability_next_process_digest(
            previous_process_digest=previous_process_digest,
            request_ref=proposal.id,
            request_digest=proposal.id,
            lifecycle=lifecycle,
            previous_transition_ref=previous.id if previous is not None else None,
            phase_record_ref=phase_record_ref,
            trigger_ref=trigger_ref,
            budget_delta=budget_delta,
        )
        transition = CapabilityTransitionV1.create(
            manifest_digest=self.manifest.sha256,
            run_input_digest=self.manifest.run_input_digest,
            capability_policy_digest=self.policy.digest,
            request_ref=proposal.id,
            request_digest=proposal.id,
            originating_work_order_ref=proposal.originating_work_order_ref,
            problem_ref=proposal.problem_ref,
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
            lifecycle=lifecycle,
            previous_transition_ref=previous.id if previous is not None else None,
            phase_record_ref=phase_record_ref,
            trigger_ref=trigger_ref,
            budget_delta=budget_delta,
            previous_process_digest=previous_process_digest,
            next_process_digest=next_process_digest,
            reason_code=reason_code,
        )
        self.harness.record_capability_transition(
            transition,
            phase_record=phase_record,
        )
        return transition

    def _denied(
        self,
        proposal: SimulationProposalV1,
        previous: CapabilityTransitionV1,
        reason: str,
        *,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> None:
        self._transition(
            proposal,
            CapabilityLifecycle.DENIED,
            previous=previous,
            reason_code=reason,
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )

    def _toolchain_available(self, proposal: SimulationProposalV1) -> bool:
        matches = tuple(
            item
            for item in self.manifest.toolchains
            if item.id == self.policy.python_toolchain_identity
        )
        if len(matches) != 1:
            return False
        toolchain = matches[0]
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        # Model-authored Python is never sent to the local subprocess backend.
        # A future certified container adapter must provide a distinct trusted
        # implementation before this branch may return True.
        if proposal.simulation_mode == "sandboxed_python_v1":
            return False
        return (
            proposal.simulation_mode == "declarative_numeric_v1"
            and self.policy.runner_profile == "simulation.declarative.v1"
            and toolchain.runner == "local"
            and toolchain.network is False
            and Path(toolchain.executable).resolve() == Path(sys.executable).resolve()
            and toolchain.version_output_sha256 == sha256_hex(version.encode("utf-8"))
        )

    def _compile_inputs(self, proposal: SimulationProposalV1) -> tuple[bytes, str | None]:
        catalog = (
            {f"SIM_{index:03d}": item for index, item in enumerate(self.policy.input_catalog, 1)}
            if self.manifest.schema_version == 6
            else {item.alias: item for item in self.policy.input_catalog}
        )
        unknown = sorted(set(proposal.input_aliases) - set(catalog))
        if unknown:
            return b"", "unknown_input_alias"
        sealed = {alias: catalog[alias].value for alias in proposal.input_aliases}
        parameter_sets = proposal.parameter_definitions or ()
        inputs: list[dict[str, Any]] = []
        if parameter_sets:
            for item in parameter_sets:
                inputs.append(
                    {
                        "parameter_set": item.name,
                        "parameters": item.values,
                        "sealed_inputs": sealed,
                    }
                )
        else:
            inputs.append({"parameter_set": "default", "parameters": {}, "sealed_inputs": sealed})
        encoded = canonical_json(inputs)
        if len(encoded) > self.policy.maximum_input_bytes:
            return b"", "input_bytes_exceeded"
        return encoded, None

    def propose(
        self,
        draft: SimulationProposalDraftV1,
        *,
        proposal_index: int,
        work_order,
        source_call_seq: int,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> SimulationProposalV1:
        """Record semantic intent only; no validation grant or execution occurs."""

        from deepreason.workflow.models import CapabilityOutcome

        if CapabilityOutcome.SIMULATION_REQUEST not in work_order.capability_grant.allowed_outcomes:
            raise ValueError("originating work order does not permit a simulation proposal")

        proposal_values = draft.model_dump(mode="python")
        proposal = SimulationProposalV1.create(
            **proposal_values,
            proposal_index=proposal_index,
            originating_work_order_ref=work_order.id,
            source_call_seq=source_call_seq,
            problem_ref=work_order.problem_ref,
            run_input_digest=self.manifest.run_input_digest,
        )
        self._transition(
            proposal,
            CapabilityLifecycle.PROPOSED,
            previous=None,
            phase_record=proposal,
            reason_code="model_semantic_proposal",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )
        return proposal

    def _stage_transactional_proposal(
        self,
        draft: SimulationProposalDraftV1,
        *,
        proposal_index: int,
        preparation,
        provider_attempt,
        source_call_seq: int,
    ) -> SimulationProposalV1:
        """Build and validate a v6 proposal without appending any event.

        This seam never accepts a legacy WorkOrderEnvelope. The preparation
        fixes the problem, run input, route, contract, and proposal authority;
        the provider-result event proves which authorized result supplied the
        semantic content. The returned immutable proposal is preparation data.
        """

        from deepreason.workflow.models import CapabilityOutcome, WorkflowTaskKind
        from deepreason.workflow.transaction import (
            ProviderAttemptV1,
            WorkPreparationV1,
        )

        if self.manifest.schema_version != 6:
            raise ValueError("transactional simulation proposals require RunManifest v6")
        preparation = WorkPreparationV1.model_validate(
            preparation.model_dump(mode="python", by_alias=True)
        )
        provider_attempt = ProviderAttemptV1.model_validate(
            provider_attempt.model_dump(mode="python", by_alias=True)
        )
        item = self.harness.workflow_state.transaction_work.get(preparation.id)
        if (
            item is None
            or item.preparation != preparation
            or provider_attempt.work_id != preparation.id
            or item.provider_attempts.get(provider_attempt.attempt_index) != provider_attempt
            or preparation.task_kind != WorkflowTaskKind.CONJECTURE
            or preparation.contract_id != "conjecturer.turn.v6"
        ):
            raise ValueError("simulation proposal lacks its durable v6 provider work")
        payload = preparation.task_payload_value
        if not isinstance(payload, Mapping):
            raise ValueError("v6 conjecture preparation has no semantic task payload")
        simulation_authority = payload.get("simulation_authority")
        allowed_outcomes = payload.get("allowed_outcomes")
        if (
            not isinstance(simulation_authority, Mapping)
            or simulation_authority.get("enabled") is not True
            or simulation_authority.get("policy_digest") != self.policy.digest
            or simulation_authority.get("maximum_proposals_per_turn")
            != self.policy.maximum_proposals_per_turn
            or not isinstance(allowed_outcomes, (tuple, list))
            or CapabilityOutcome.SIMULATION_REQUEST.value not in allowed_outcomes
            or proposal_index >= self.policy.maximum_proposals_per_turn
        ):
            raise ValueError("v6 preparation does not authorize this simulation proposal")
        authorized_aliases = tuple(simulation_authority.get("input_aliases") or ())
        expected_aliases = tuple(
            f"SIM_{index:03d}" for index, _item in enumerate(self.policy.input_catalog, 1)
        )
        if tuple(sorted(authorized_aliases)) != expected_aliases or any(
            alias not in expected_aliases for alias in draft.input_aliases
        ):
            raise ValueError("simulation proposal uses context outside sealed input authority")
        source = next(
            (
                event
                for event in self.harness._events_since(source_call_seq)
                if event.seq == source_call_seq
            ),
            None,
        )
        if (
            source is None
            or source.llm is None
            or source.llm.work_order_id != preparation.id
            or source.llm.dispatch_authorization_ref != provider_attempt.authorization_bundle_ref
            or provider_attempt.id not in source.outputs
        ):
            raise ValueError("simulation proposal source is not its provider-result event")
        problem_ref = payload.get("problem_ref")
        if not isinstance(problem_ref, str) or not problem_ref:
            raise ValueError("v6 simulation authority has no problem reference")

        proposal = SimulationProposalV1.create(
            **draft.model_dump(mode="python"),
            proposal_index=proposal_index,
            originating_work_order_ref=preparation.id,
            originating_provider_attempt_ref=provider_attempt.id,
            source_call_seq=source_call_seq,
            problem_ref=problem_ref,
            run_input_digest=self.manifest.run_input_digest,
        )
        existing = self.harness.capability_state.proposals.get(proposal.id)
        if existing is not None:
            if existing != proposal:
                raise ValueError("transactional simulation proposal identity conflict")
            return existing
        return proposal

    def stage_transactional_proposals(
        self,
        drafts: tuple[SimulationProposalDraftV1, ...],
        *,
        preparation,
        provider_attempt,
        source_call_seq: int,
    ) -> tuple[SimulationProposalV1, ...]:
        """Purely validate a complete proposal batch before semantic mutation."""

        if len(drafts) > self.policy.maximum_proposals_per_turn:
            raise ValueError("simulation proposal batch exceeds frozen turn authority")
        proposals = tuple(
            self._stage_transactional_proposal(
                draft,
                proposal_index=index,
                preparation=preparation,
                provider_attempt=provider_attempt,
                source_call_seq=source_call_seq,
            )
            for index, draft in enumerate(drafts)
        )
        if len({proposal.id for proposal in proposals}) != len(proposals):
            raise ValueError("transactional simulation proposal batch contains duplicates")
        return proposals

    def propose_transactional(
        self,
        draft: SimulationProposalDraftV1,
        *,
        proposal_index: int,
        preparation,
        provider_attempt,
        source_call_seq: int,
    ) -> SimulationProposalV1:
        """Bind one staged v6 proposal to its durable provider transaction."""

        proposal = self._stage_transactional_proposal(
            draft,
            proposal_index=proposal_index,
            preparation=preparation,
            provider_attempt=provider_attempt,
            source_call_seq=source_call_seq,
        )
        existing = self.harness.capability_state.proposals.get(proposal.id)
        if existing is not None:
            return existing
        item = self.harness.workflow_state.transaction_work[proposal.originating_work_order_ref]
        self._transition(
            proposal,
            CapabilityLifecycle.PROPOSED,
            previous=None,
            phase_record=proposal,
            reason_code="transaction_semantic_proposal",
            formal_fence_seq=item.preparation.formal_fence_seq,
            scratch_fence_seq=item.preparation.scratch_fence_seq,
        )
        return proposal

    def materialize_transactional_proposals(
        self,
        drafts: tuple[SimulationProposalDraftV1, ...],
        *,
        preparation,
        provider_attempt,
        source_call_seq: int,
    ) -> tuple[str, ...]:
        """Return deterministic proposal IDs, reusing replayed records on recovery."""

        if len(drafts) > self.policy.maximum_proposals_per_turn:
            raise ValueError("simulation proposal batch exceeds frozen turn authority")
        return tuple(
            self.propose_transactional(
                draft,
                proposal_index=index,
                preparation=preparation,
                provider_attempt=provider_attempt,
                source_call_seq=source_call_seq,
            ).id
            for index, draft in enumerate(drafts)
        )

    def require_transactional_origin(self, proposal: SimulationProposalV1):
        """Return the completed v6 origin or fail closed on any broken link."""

        if self.manifest.schema_version != 6:
            raise ValueError("transactional simulation origin requires v6")
        item = self.harness.workflow_state.transaction_work.get(proposal.originating_work_order_ref)
        if item is None or proposal.originating_work_order_ref in (
            self.harness.workflow_state.work_orders
        ):
            raise ValueError("v6 simulation proposal names legacy or missing work")
        provider_attempt = next(
            (
                attempt
                for attempt in item.provider_attempts.values()
                if attempt.id == proposal.originating_provider_attempt_ref
            ),
            None,
        )
        terminal = item.terminal
        admission = item.admissions.get(terminal.attempt_index) if terminal is not None else None
        payload = item.preparation.task_payload_value
        source = next(
            (
                event
                for event in self.harness._events_since(proposal.source_call_seq)
                if event.seq == proposal.source_call_seq
            ),
            None,
        )
        simulation_authority = (
            payload.get("simulation_authority") if isinstance(payload, Mapping) else None
        )
        if (
            provider_attempt is None
            or terminal is None
            or terminal.status != "completed"
            or admission is None
            or admission.outcome != "admitted"
            or proposal.id not in admission.admitted_refs
            or terminal.semantic_admission_ref != admission.id
            or item.preparation.contract_id != "conjecturer.turn.v6"
            or not isinstance(payload, Mapping)
            or payload.get("problem_ref") != proposal.problem_ref
            or payload.get("run_input_digest") != proposal.run_input_digest
            or not isinstance(simulation_authority, Mapping)
            or simulation_authority.get("policy_digest") != self.policy.digest
            or source is None
            or source.llm is None
            or source.llm.work_order_id != item.preparation.id
            or source.llm.dispatch_authorization_ref != provider_attempt.authorization_bundle_ref
            or provider_attempt.id not in source.outputs
        ):
            raise ValueError(
                "v6 simulation proposal does not resolve to completed transaction authority"
            )
        return item

    def execute(
        self,
        draft: SimulationProposalDraftV1 | SimulationProposalV1,
        *,
        proposal_index: int | None = None,
        work_order=None,
        source_call_seq: int | None = None,
        formal_fence_seq: int | None = None,
        scratch_fence_seq: int | None = None,
    ) -> SimulationResultPackageV1 | None:
        """Authorize and execute one already-recorded proposal.

        The draft form remains an internal compatibility seam for offline unit
        tests. Production conjecture turns call :meth:`propose`; only the
        scheduler capability phase calls this method with a canonical proposal.
        """

        if isinstance(draft, SimulationProposalV1):
            proposal = SimulationProposalV1.model_validate(
                draft.model_dump(mode="python", by_alias=True)
            )
            transition_ref = self.harness.capability_state.current_transition_by_request.get(
                proposal.id
            )
            if transition_ref is None:
                raise ValueError("simulation proposal has no durable PROPOSED transition")
            current = self.harness.capability_state.transitions[transition_ref]
            if current.lifecycle != CapabilityLifecycle.PROPOSED:
                raise ValueError("simulation proposal was already processed")
            formal_fence_seq = current.formal_fence_seq
            scratch_fence_seq = current.scratch_fence_seq
        else:
            if (
                None
                in {
                    proposal_index,
                    source_call_seq,
                    formal_fence_seq,
                    scratch_fence_seq,
                }
                or work_order is None
            ):
                raise ValueError("draft execution requires complete originating authority")
            proposal = self.propose(
                draft,
                proposal_index=proposal_index,
                work_order=work_order,
                source_call_seq=source_call_seq,
                formal_fence_seq=formal_fence_seq,
                scratch_fence_seq=scratch_fence_seq,
            )
            current = self.harness.capability_state.transitions[
                self.harness.capability_state.current_transition_by_request[proposal.id]
            ]
        assert formal_fence_seq is not None and scratch_fence_seq is not None
        current = self._transition(
            proposal,
            CapabilityLifecycle.VALIDATED,
            previous=current,
            reason_code="typed_semantic_schema_valid",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )

        from deepreason.simulation.compiler import (
            DeclarativeSimulationError,
            compile_declarative_numeric,
            validate_sandboxed_python_source,
        )

        reason = None
        source_bytes = b""
        if not self.policy.enabled:
            reason = "capability_disabled"
        else:
            ordered_requests = sorted(
                self.harness.capability_state.proposals.values(),
                key=lambda item: (
                    item.source_call_seq,
                    item.proposal_index,
                    item.id,
                ),
            )
            request_ordinal = ordered_requests.index(proposal) + 1
            if request_ordinal > self.policy.maximum_simulation_requests:
                reason = "request_budget_exhausted"
        if (
            reason is None
            and self.harness.capability_state.execution_count
            >= self.policy.maximum_simulation_executions
        ):
            reason = "execution_budget_exhausted"
        if (
            reason is None
            and len(proposal.model_source.encode("utf-8"))
            > self.policy.maximum_generated_code_bytes
        ):
            reason = "generated_code_bytes_exceeded"

        expected_profile = (
            "simulation.declarative.v1"
            if proposal.simulation_mode == "declarative_numeric_v1"
            else "simulation.container.v1"
        )
        if self.policy.runner_profile != expected_profile:
            reason = reason or "runner_profile_mismatch"
        if reason is None:
            try:
                if proposal.simulation_mode == "declarative_numeric_v1":
                    source_bytes = compile_declarative_numeric(
                        proposal.model_source,
                        proposal.requested_observables,
                    )
                else:
                    validate_sandboxed_python_source(proposal.model_source)
            except (DeclarativeSimulationError, ValueError):
                reason = "invalid_model_program"
        if source_bytes and len(source_bytes) > self.policy.maximum_generated_code_bytes:
            reason = reason or "generated_code_bytes_exceeded"
        if reason is None and not self._toolchain_available(proposal):
            reason = "runner_unavailable"

        if self.policy.deterministic_seed_policy == "fixed_manifest":
            seeds = self.policy.fixed_seed_set
        else:
            seeds = proposal.requested_seed_set
            if not seeds:
                reason = reason or "seed_set_required"
        input_bytes, input_error = self._compile_inputs(proposal)
        reason = reason or input_error
        sample_count = len(seeds) * (
            len(proposal.parameter_definitions) if proposal.parameter_definitions else 1
        )
        if sample_count > self.policy.maximum_samples:
            reason = reason or "sample_limit_exceeded"
        if reason is not None:
            self._denied(
                proposal,
                current,
                reason,
                formal_fence_seq=formal_fence_seq,
                scratch_fence_seq=scratch_fence_seq,
            )
            return None

        grant = SimulationGrantV1.create(
            proposal_ref=proposal.id,
            manifest_digest=self.manifest.sha256,
            run_input_digest=self.manifest.run_input_digest,
            policy_digest=self.policy.digest,
            template_identity=self.policy.runner_template_identity,
            backend_identity=self.policy.backend_identity,
            toolchain_identity=self.policy.python_toolchain_identity,
            seed_set=seeds,
            deterministic_step_limit=self.policy.maximum_steps,
            sample_limit=self.policy.maximum_samples,
            maximum_output_bytes=self.policy.maximum_output_bytes,
        )
        current = self._transition(
            proposal,
            CapabilityLifecycle.GRANTED,
            previous=current,
            phase_record=grant,
            reason_code="manifest_policy_grant",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )

        checker_bytes = TRUSTED_CHECKER_SOURCE_V1.encode("utf-8")
        source_ref = self.harness.blobs.put(source_bytes)
        input_ref = self.harness.blobs.put(input_bytes)
        checker_ref = self.harness.blobs.put(checker_bytes)
        specification = CompiledSimulationSpecV1(
            entry="simulate",
            seed_set=seeds,
            inputs_ref=input_ref,
            observables=proposal.requested_observables,
            checker_ref=checker_ref,
            deterministic_step_limit=self.policy.maximum_steps,
            sample_limit=self.policy.maximum_samples,
            toolchain_id=self.policy.python_toolchain_identity,
        )
        compiled = CompiledSimulationV1.create(
            proposal_ref=proposal.id,
            grant_ref=grant.id,
            template_identity=self.policy.runner_template_identity,
            source_ref=source_ref,
            source_sha256=sha256_hex(source_bytes),
            input_ref=input_ref,
            input_sha256=sha256_hex(input_bytes),
            checker_ref=checker_ref,
            checker_sha256=sha256_hex(checker_bytes),
            specification=specification,
            generated_code_bytes=len(source_bytes),
            input_bytes=len(input_bytes),
            maximum_output_bytes=self.policy.maximum_output_bytes,
        )
        current = self._transition(
            proposal,
            CapabilityLifecycle.COMPILED,
            previous=current,
            phase_record=compiled,
            reason_code="trusted_template_compiled",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )
        work_order = SimulationWorkOrderV1.create(
            proposal_ref=proposal.id,
            grant_ref=grant.id,
            compiled_simulation_ref=compiled.id,
            manifest_digest=self.manifest.sha256,
            run_input_digest=self.manifest.run_input_digest,
            policy_digest=self.policy.digest,
            runner_profile=self.policy.runner_profile,
            template_identity=self.policy.runner_template_identity,
            backend_identity=self.policy.backend_identity,
            toolchain_identity=self.policy.python_toolchain_identity,
            maximum_wall_ms=self.policy.maximum_wall_ms,
            maximum_memory_bytes=self.policy.maximum_memory_bytes,
            maximum_output_bytes=self.policy.maximum_output_bytes,
            deterministic_step_limit=self.policy.maximum_steps,
            sample_limit=self.policy.maximum_samples,
            network=False,
            filesystem_policy=self.policy.filesystem_policy,
        )
        current = self._transition(
            proposal,
            CapabilityLifecycle.DISPATCHED,
            previous=current,
            phase_record=work_order,
            reason_code="trusted_runner_dispatched",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )

        from deepreason.verification.simulation import (
            SimulationBackend,
            SimulationRequest,
        )
        from deepreason.workloads.code import SimulationSpec

        backend = SimulationBackend(
            toolchain_id=self.policy.python_toolchain_identity,
            maximum_wall_ms=self.policy.maximum_wall_ms,
            maximum_memory_bytes=self.policy.maximum_memory_bytes,
        )
        backend_request = SimulationRequest(
            source_ref=source_ref,
            spec=SimulationSpec.model_validate(
                specification.model_dump(mode="python", by_alias=True)
            ),
            maximum_output_bytes=self.policy.maximum_output_bytes,
        )
        started_at = _utc_now()
        attempts: list[SimulationAttemptV1] = []
        final = None
        for attempt_index in range(self.policy.retry_ceiling + 1):
            try:
                final = backend.verify(backend_request, self.harness.blobs)
            except Exception:  # noqa: BLE001 - preserve trusted-runner failure
                return self.recover_interrupted(proposal)
            attempts.append(
                SimulationAttemptV1(
                    attempt=attempt_index,
                    backend_verdict=final.verdict,
                    fingerprint=final.fingerprint,
                    diagnostics_ref=final.diagnostics_ref,
                    output_ref=final.output_ref,
                    stdout_ref=final.stdout_ref,
                    stderr_ref=final.stderr_ref,
                    sample_count=final.sample_count,
                )
            )
            if final.verdict != "overrun":
                break
        assert final is not None and final.output_ref is not None
        completed_at = _utc_now()
        full_output = self.harness.blobs.get(final.output_ref)
        output_truncated = bool(final.trace.get("output_truncated")) or (
            len(full_output) > self.policy.maximum_output_bytes
        )
        operational_status = (
            "failed" if final.verdict != "pass" or output_truncated else "succeeded"
        )
        receipt = SimulationExecutionReceiptV1.create(
            proposal_ref=proposal.id,
            run_input_digest=self.manifest.run_input_digest,
            simulation_work_order_ref=work_order.id,
            compiled_specification_ref=compiled.id,
            started_at=started_at,
            completed_at=completed_at,
            operational_status=operational_status,
            attempts=tuple(attempts),
            final_backend_verdict=final.verdict,
            source_sha256=final.source_sha256,
            inputs_sha256=final.inputs_sha256,
            checker_sha256=final.checker_sha256,
            specification_sha256=final.spec_sha256,
            output_bytes=len(full_output),
            output_truncated=output_truncated,
            resource_limits={
                **backend.resource_limits(),
                "manifest_maximum_wall_ms": self.policy.maximum_wall_ms,
                "manifest_maximum_memory_bytes": self.policy.maximum_memory_bytes,
                "deterministic_step_limit": self.policy.maximum_steps,
                "sample_limit": self.policy.maximum_samples,
                "maximum_output_bytes": self.policy.maximum_output_bytes,
            },
            diagnostic=("output exceeded the manifest bound" if output_truncated else None),
        )
        lifecycle = (
            CapabilityLifecycle.SUCCEEDED
            if operational_status == "succeeded"
            else CapabilityLifecycle.FAILED
        )
        current = self._transition(
            proposal,
            lifecycle,
            previous=current,
            phase_record=receipt,
            reason_code=(
                "runner_completed" if operational_status == "succeeded" else "runner_failed"
            ),
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )

        if output_truncated:
            structured = canonical_json(
                {
                    "truncated": True,
                    "retained_output_ref": final.output_ref,
                    "retained_output_sha256": sha256_hex(full_output),
                    "retained_output_bytes": len(full_output),
                    "generated_output_sha256": final.trace.get("generated_output_sha256"),
                    "generated_output_bytes": final.trace.get("generated_output_bytes"),
                }
            )
        else:
            structured = full_output
        structured_ref = self.harness.blobs.put(structured)
        limitations = [
            "The receipt establishes only the recorded program execution under its exact inputs and seeds.",
            "The trusted checker validates output shape, not real-hardware or universal scientific adequacy.",
            "Simulated hardware quantities are model outputs, not measurements of the reference machine.",
        ]
        if operational_status == "failed":
            limitations.append(
                "The execution failed operationally and does not refute the hypothesis."
            )
        context_payload = {
            "schema": "simulation-result-context.v1",
            "proposal_ref": proposal.id,
            "hypothesis": proposal.hypothesis,
            "rival_predictions": list(proposal.rival_predictions),
            "discriminating_purpose": proposal.discriminating_purpose,
            "declared_assumptions": list(proposal.declared_assumptions),
            "interpretation_conditions": list(proposal.interpretation_conditions),
            "receipt_ref": receipt.id,
            "operational_status": operational_status,
            "backend_verdict": final.verdict,
            "structured_result_ref": structured_ref,
            "structured_result": json.loads(structured),
            "execution_limitations": limitations,
            "epistemic_status": "recorded_observation",
        }
        context_ref = self.harness.blobs.put(canonical_json(context_payload))
        package = SimulationResultPackageV1.create(
            proposal_ref=proposal.id,
            run_input_digest=self.manifest.run_input_digest,
            receipt_ref=receipt.id,
            structured_result_ref=structured_ref,
            result_context_ref=context_ref,
            assumptions=proposal.declared_assumptions,
            execution_limitations=tuple(limitations),
            original_hypothesis=proposal.hypothesis,
            rival_predictions=proposal.rival_predictions,
        )
        self._transition(
            proposal,
            CapabilityLifecycle.RESULT_PACKAGED,
            previous=current,
            phase_record=package,
            reason_code="bounded_result_context_packaged",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )
        if operational_status == "failed" and self.policy.failure_policy == "terminal":
            raise CapabilityTerminalError("terminal simulation failure policy was reached")
        return package

    def recover_interrupted(
        self,
        proposal: SimulationProposalV1,
    ) -> SimulationResultPackageV1:
        """Close a durable DISPATCHED prefix without inventing an execution.

        A process can stop after the simulation work order is committed but
        before a runner receipt is durable. Replay cannot know whether the
        external subprocess began or completed. The safe recovery is therefore
        an explicit unknown operational failure, never a silent rerun.
        """

        state = self.harness.capability_state
        proposal = state.proposals.get(proposal.id, proposal)
        transition_ref = state.current_transition_by_request.get(proposal.id)
        if transition_ref is None:
            raise ValueError("interrupted simulation has no durable transition")
        current = state.transitions[transition_ref]
        if current.lifecycle != CapabilityLifecycle.DISPATCHED:
            raise ValueError("only a dispatched simulation can be recovered")
        work_orders = [
            item for item in state.work_orders.values() if item.proposal_ref == proposal.id
        ]
        if len(work_orders) != 1:
            raise ValueError("interrupted simulation has no unique work order")
        work_order = work_orders[0]
        compiled = state.compiled[work_order.compiled_simulation_ref]
        output = b"[]"
        output_ref = self.harness.blobs.put(output)
        diagnostics = canonical_json(
            {
                "error": (
                    "durable dispatch has no execution receipt; whether the "
                    "runner began or completed is unknown"
                ),
                "execution_observed": False,
            }
        )
        diagnostics_ref = self.harness.blobs.put(diagnostics)
        empty_ref = self.harness.blobs.put(b"")
        attempt = SimulationAttemptV1(
            attempt=0,
            backend_verdict="overrun",
            fingerprint={
                "backend": work_order.backend_identity,
                "toolchain_id": work_order.toolchain_identity,
                "execution_observed": False,
            },
            diagnostics_ref=diagnostics_ref,
            output_ref=output_ref,
            stdout_ref=empty_ref,
            stderr_ref=empty_ref,
            sample_count=0,
        )
        recovered_at = _utc_now()
        receipt = SimulationExecutionReceiptV1.create(
            proposal_ref=proposal.id,
            run_input_digest=self.manifest.run_input_digest,
            simulation_work_order_ref=work_order.id,
            compiled_specification_ref=compiled.id,
            started_at=recovered_at,
            completed_at=recovered_at,
            execution_disposition="dispatch_interrupted",
            operational_status="failed",
            attempts=(attempt,),
            final_backend_verdict="overrun",
            source_sha256=compiled.source_sha256,
            inputs_sha256=compiled.input_sha256,
            checker_sha256=compiled.checker_sha256,
            specification_sha256=sha256_hex(
                canonical_json(compiled.specification.model_dump(mode="json", by_alias=True))
            ),
            output_bytes=len(output),
            output_truncated=False,
            resource_limits={
                "memory_bytes": work_order.maximum_memory_bytes,
                "wall_ms": work_order.maximum_wall_ms,
                "deterministic_step_limit": work_order.deterministic_step_limit,
                "sample_limit": work_order.sample_limit,
                "maximum_output_bytes": work_order.maximum_output_bytes,
                "filesystem": work_order.filesystem_policy,
                "network": False,
                "execution_observed": False,
            },
            diagnostic=("dispatch was durable but no execution receipt was; outcome unknown"),
        )
        current = self._transition(
            proposal,
            CapabilityLifecycle.FAILED,
            previous=current,
            phase_record=receipt,
            reason_code="dispatch_interrupted",
            formal_fence_seq=current.formal_fence_seq,
            scratch_fence_seq=current.scratch_fence_seq,
        )
        limitations = (
            "No runner completion was observed; the execution outcome is unknown.",
            "The interrupted dispatch does not refute the motivating hypothesis.",
            "The harness did not silently rerun the work order during recovery.",
        )
        structured_ref = output_ref
        context_payload = {
            "schema": "simulation-result-context.v1",
            "proposal_ref": proposal.id,
            "hypothesis": proposal.hypothesis,
            "rival_predictions": list(proposal.rival_predictions),
            "discriminating_purpose": proposal.discriminating_purpose,
            "declared_assumptions": list(proposal.declared_assumptions),
            "interpretation_conditions": list(proposal.interpretation_conditions),
            "receipt_ref": receipt.id,
            "operational_status": "failed",
            "backend_verdict": "overrun",
            "structured_result_ref": structured_ref,
            "structured_result": [],
            "execution_limitations": list(limitations),
            "epistemic_status": "recorded_observation",
        }
        context_ref = self.harness.blobs.put(canonical_json(context_payload))
        package = SimulationResultPackageV1.create(
            proposal_ref=proposal.id,
            run_input_digest=self.manifest.run_input_digest,
            receipt_ref=receipt.id,
            structured_result_ref=structured_ref,
            result_context_ref=context_ref,
            assumptions=proposal.declared_assumptions,
            execution_limitations=limitations,
            original_hypothesis=proposal.hypothesis,
            rival_predictions=proposal.rival_predictions,
        )
        self._transition(
            proposal,
            CapabilityLifecycle.RESULT_PACKAGED,
            previous=current,
            phase_record=package,
            reason_code="interrupted_result_packaged",
            formal_fence_seq=current.formal_fence_seq,
            scratch_fence_seq=current.scratch_fence_seq,
        )
        if self.policy.failure_policy == "terminal":
            raise CapabilityTerminalError(
                "terminal interrupted-simulation failure policy was reached"
            )
        return package

    def consume(
        self,
        package: SimulationResultPackageV1,
        *,
        follow_up_work_order_ref: str,
        formal_fence_seq: int,
        scratch_fence_seq: int,
        follow_up_semantic_admission_ref: str | None = None,
    ) -> SimulationConsumptionV1:
        if self.harness.capability_state.consumption_count >= (
            self.policy.maximum_follow_up_reasoning_turns
        ):
            raise ValueError("simulation result follow-up budget is exhausted")
        proposal = self.harness.capability_state.proposals[package.proposal_ref]
        previous = self.harness.capability_state.transitions[
            self.harness.capability_state.current_transition_by_request[proposal.id]
        ]
        consumption = SimulationConsumptionV1.create(
            proposal_ref=proposal.id,
            run_input_digest=self.manifest.run_input_digest,
            result_package_ref=package.id,
            follow_up_work_order_ref=follow_up_work_order_ref,
            follow_up_semantic_admission_ref=follow_up_semantic_admission_ref,
        )
        self._transition(
            proposal,
            CapabilityLifecycle.CONSUMED,
            previous=previous,
            phase_record=consumption,
            reason_code="fresh_reasoning_work_order_created",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )
        return consumption

    def consume_transactional(
        self,
        package: SimulationResultPackageV1,
        *,
        follow_up_work_ref: str,
    ) -> SimulationConsumptionV1:
        """Consume a result only after one fresh completed v6 work item."""

        if self.manifest.schema_version != 6:
            raise ValueError("transactional simulation consumption requires v6")
        item = self.harness.workflow_state.transaction_work.get(follow_up_work_ref)
        proposal = self.harness.capability_state.proposals[package.proposal_ref]
        if item is None or item.preparation.id == proposal.originating_work_order_ref:
            raise ValueError("simulation result requires a fresh transaction work item")
        payload = item.preparation.task_payload_value
        terminal = item.terminal
        admission = item.admissions.get(terminal.attempt_index) if terminal is not None else None
        result_plans = tuple(
            plan for plan in item.plans.values() if plan.plan_kind == "simulation_result"
        )
        simulation_authority = (
            payload.get("simulation_authority") if isinstance(payload, Mapping) else None
        )
        sealed_input_aliases = (
            tuple(simulation_authority.get("input_aliases") or ())
            if isinstance(simulation_authority, Mapping)
            else ()
        )
        if (
            not isinstance(payload, Mapping)
            or payload.get("capability_result_package_ref") != package.id
            or payload.get("capability_result_context_ref") != package.result_context_ref
            or package.id not in item.preparation.input_refs
            or package.result_context_ref not in item.preparation.input_refs
            or terminal is None
            or terminal.status != "completed"
            or admission is None
            or admission.outcome != "admitted"
            or terminal.semantic_admission_ref != admission.id
            or len(result_plans) != 1
            or len(result_plans[0].items) != 1
            or result_plans[0].items[0].object_ref != package.id
            or result_plans[0].items[0].content_sha256 != package.result_context_ref
            or result_plans[0].items[0].alias in sealed_input_aliases
        ):
            raise ValueError(
                "simulation result was not exposed and admitted by fresh completed work"
            )
        transition = self.harness.capability_state.transitions[
            self.harness.capability_state.current_transition_by_request[proposal.id]
        ]
        return self.consume(
            package,
            follow_up_work_order_ref=item.preparation.id,
            follow_up_semantic_admission_ref=admission.id,
            formal_fence_seq=transition.formal_fence_seq,
            scratch_fence_seq=transition.scratch_fence_seq,
        )

    def result_context(self, package: SimulationResultPackageV1) -> str:
        return self.harness.blobs.get(package.result_context_ref).decode("utf-8")

    def accounting(self) -> dict[str, Any]:
        state = self.harness.capability_state
        attempts = sum(len(receipt.attempts) for receipt in state.receipts.values())
        return {
            "schema": "capability-accounting.v1",
            "simulation_requests": state.request_count,
            "simulation_executions": state.execution_count,
            "simulation_backend_attempts": attempts,
            "result_follow_up_work_orders": state.consumption_count,
            "compilation_usage_known": True,
            "execution_usage_known": True,
        }


__all__ = [
    "CapabilityTerminalError",
    "SimulationCapabilityController",
    "TRUSTED_CHECKER_SOURCE_V1",
]
