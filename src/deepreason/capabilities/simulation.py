"""Deterministic Tranche-A simulation controller and result reinjection data."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.models import (
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
        self.policy = manifest.simulation_capability_policy
        if manifest.schema_version != 5 or self.policy is None:
            raise ValueError("simulation controller requires one v5 run manifest")

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
        transition = CapabilityTransitionV1.create(
            manifest_digest=self.manifest.sha256,
            capability_policy_digest=self.policy.digest,
            request_ref=proposal.id,
            request_digest=proposal.id,
            originating_work_order_ref=proposal.originating_work_order_ref,
            problem_ref=proposal.problem_ref,
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
            lifecycle=lifecycle,
            previous_transition_ref=previous.id if previous is not None else None,
            phase_record_ref=getattr(phase_record, "id", None),
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

    def _toolchain_available(self) -> bool:
        matches = tuple(
            item
            for item in self.manifest.toolchains
            if item.id == self.policy.python_toolchain_identity
        )
        if len(matches) != 1:
            return False
        toolchain = matches[0]
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        return (
            toolchain.runner == "local"
            and toolchain.network is False
            and Path(toolchain.executable).resolve() == Path(sys.executable).resolve()
            and toolchain.version_output_sha256 == sha256_hex(version.encode("utf-8"))
        )

    def _compile_inputs(self, proposal: SimulationProposalV1) -> tuple[bytes, str | None]:
        catalog = {item.alias: item for item in self.policy.input_catalog}
        unknown = sorted(set(proposal.input_aliases) - set(catalog))
        if unknown:
            return b"", "unknown_input_alias"
        sealed = {
            alias: catalog[alias].value
            for alias in proposal.input_aliases
        }
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

    def execute(
        self,
        draft: SimulationProposalDraftV1,
        *,
        proposal_index: int,
        work_order,
        source_call_seq: int,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> SimulationResultPackageV1 | None:
        """Record, authorize, execute, and package one semantic proposal."""

        proposal_values = draft.model_dump(mode="python")
        proposal = SimulationProposalV1.create(
            **proposal_values,
            proposal_index=proposal_index,
            originating_work_order_ref=work_order.id,
            source_call_seq=source_call_seq,
            problem_ref=work_order.problem_ref,
        )
        current = self._transition(
            proposal,
            CapabilityLifecycle.PROPOSED,
            previous=None,
            phase_record=proposal,
            reason_code="model_semantic_proposal",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )
        current = self._transition(
            proposal,
            CapabilityLifecycle.VALIDATED,
            previous=current,
            reason_code="typed_semantic_schema_valid",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )

        reason = None
        if not self.policy.enabled:
            reason = "capability_disabled"
        elif self.harness.capability_state.request_count > self.policy.maximum_simulation_requests:
            reason = "request_budget_exhausted"
        elif self.harness.capability_state.execution_count >= self.policy.maximum_simulation_executions:
            reason = "execution_budget_exhausted"
        elif not self._toolchain_available():
            reason = "runner_unavailable"
        elif len(proposal.model_source.encode("utf-8")) > self.policy.maximum_generated_code_bytes:
            reason = "generated_code_bytes_exceeded"

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

        source_bytes = proposal.model_source.encode("utf-8")
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
        current = self._transition(
            proposal,
            CapabilityLifecycle.DISPATCHED,
            previous=current,
            reason_code="trusted_runner_dispatched",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )

        from deepreason.verification.simulation import (
            SimulationBackend,
            SimulationRequest,
        )
        from deepreason.workloads.code import SimulationSpec

        backend = SimulationBackend(toolchain_id=self.policy.python_toolchain_identity)
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
            final = backend.verify(backend_request, self.harness.blobs)
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
                "deterministic_step_limit": self.policy.maximum_steps,
                "sample_limit": self.policy.maximum_samples,
                "maximum_output_bytes": self.policy.maximum_output_bytes,
            },
            diagnostic=(
                "output exceeded the manifest bound"
                if output_truncated
                else None
            ),
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
                    "generated_output_sha256": final.trace.get(
                        "generated_output_sha256"
                    ),
                    "generated_output_bytes": final.trace.get(
                        "generated_output_bytes"
                    ),
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
            limitations.append("The execution failed operationally and does not refute the hypothesis.")
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

    def consume(
        self,
        package: SimulationResultPackageV1,
        *,
        follow_up_work_order_ref: str,
        formal_fence_seq: int,
        scratch_fence_seq: int,
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
            result_package_ref=package.id,
            follow_up_work_order_ref=follow_up_work_order_ref,
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
