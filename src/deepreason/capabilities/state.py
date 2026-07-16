"""Replay-only state machine for autonomous capability work."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from deepreason.canonical import canonical_json
from deepreason.capabilities.models import (
    CapabilityLifecycle,
    CapabilityTransitionV1,
    CompiledSimulationV1,
    SimulationConsumptionV1,
    SimulationExecutionReceiptV1,
    SimulationGrantV1,
    SimulationProposalV1,
    SimulationResultPackageV1,
    SimulationWorkOrderV1,
    capability_next_process_digest,
)

_ALLOWED_PREVIOUS = {
    CapabilityLifecycle.PROPOSED: set(),
    CapabilityLifecycle.VALIDATED: {CapabilityLifecycle.PROPOSED},
    CapabilityLifecycle.GRANTED: {CapabilityLifecycle.VALIDATED},
    CapabilityLifecycle.DENIED: {
        CapabilityLifecycle.VALIDATED,
    },
    CapabilityLifecycle.COMPILED: {CapabilityLifecycle.GRANTED},
    CapabilityLifecycle.DISPATCHED: {CapabilityLifecycle.COMPILED},
    CapabilityLifecycle.SUCCEEDED: {CapabilityLifecycle.DISPATCHED},
    CapabilityLifecycle.FAILED: {CapabilityLifecycle.DISPATCHED},
    CapabilityLifecycle.RESULT_PACKAGED: {
        CapabilityLifecycle.SUCCEEDED,
        CapabilityLifecycle.FAILED,
    },
    CapabilityLifecycle.CONSUMED: {CapabilityLifecycle.RESULT_PACKAGED},
}

_PHASE_MODELS = {
    CapabilityLifecycle.PROPOSED: SimulationProposalV1,
    CapabilityLifecycle.GRANTED: SimulationGrantV1,
    CapabilityLifecycle.COMPILED: CompiledSimulationV1,
    CapabilityLifecycle.DISPATCHED: SimulationWorkOrderV1,
    CapabilityLifecycle.SUCCEEDED: SimulationExecutionReceiptV1,
    CapabilityLifecycle.FAILED: SimulationExecutionReceiptV1,
    CapabilityLifecycle.RESULT_PACKAGED: SimulationResultPackageV1,
    CapabilityLifecycle.CONSUMED: SimulationConsumptionV1,
}


@dataclass
class CapabilityReplayState:
    proposals: dict[str, SimulationProposalV1] = field(default_factory=dict)
    transitions: dict[str, CapabilityTransitionV1] = field(default_factory=dict)
    current_transition_by_request: dict[str, str] = field(default_factory=dict)
    grants: dict[str, SimulationGrantV1] = field(default_factory=dict)
    compiled: dict[str, CompiledSimulationV1] = field(default_factory=dict)
    work_orders: dict[str, SimulationWorkOrderV1] = field(default_factory=dict)
    receipts: dict[str, SimulationExecutionReceiptV1] = field(default_factory=dict)
    result_packages: dict[str, SimulationResultPackageV1] = field(default_factory=dict)
    consumptions: dict[str, SimulationConsumptionV1] = field(default_factory=dict)
    event_seqs: list[int] = field(default_factory=list)
    process_digest: str = "sha256:" + hashlib.sha256(
        b"capability.process-state.v1\x00empty"
    ).hexdigest()

    @property
    def request_count(self) -> int:
        return len(self.proposals)

    @property
    def execution_count(self) -> int:
        return len(self.work_orders)

    @property
    def consumption_count(self) -> int:
        return len(self.consumptions)

    @property
    def digest(self) -> str:
        payload = {
            "proposals": sorted(self.proposals),
            "transitions": sorted(self.transitions),
            "current": dict(sorted(self.current_transition_by_request.items())),
            "grants": sorted(self.grants),
            "compiled": sorted(self.compiled),
            "work_orders": sorted(self.work_orders),
            "receipts": sorted(self.receipts),
            "result_packages": sorted(self.result_packages),
            "consumptions": sorted(self.consumptions),
            "event_seqs": self.event_seqs,
            "process_digest": self.process_digest,
        }
        return "sha256:" + hashlib.sha256(canonical_json(payload)).hexdigest()

    def apply(self, event, resolved_records: list[tuple[str, str, Any]]) -> None:
        payload = event.capability
        if payload is None:
            raise ValueError("capability replay requires a typed capability event")
        if event.seq in self.event_seqs:
            raise ValueError("capability event sequence was already consumed")
        records = {object_id: (schema, value) for schema, object_id, value in resolved_records}
        try:
            transition_schema, transition = records[payload.transition_ref]
        except KeyError as error:
            raise ValueError("capability transition record is absent") from error
        if transition_schema != "capability-transition" or not isinstance(
            transition, CapabilityTransitionV1
        ):
            raise ValueError("capability transition output has the wrong schema")
        if transition.id in self.transitions:
            raise ValueError("capability transition was already applied")
        expected_next_process = capability_next_process_digest(
            previous_process_digest=transition.previous_process_digest,
            request_ref=transition.request_ref,
            request_digest=transition.request_digest,
            lifecycle=transition.lifecycle,
            previous_transition_ref=transition.previous_transition_ref,
            phase_record_ref=transition.phase_record_ref,
            trigger_ref=transition.trigger_ref,
            budget_delta=transition.budget_delta,
        )
        if (
            transition.lifecycle != payload.lifecycle
            or transition.request_ref != payload.request_ref
            or transition.originating_work_order_ref != event.inputs[0]
            or transition.previous_process_digest != self.process_digest
            or transition.next_process_digest != expected_next_process
        ):
            raise ValueError("capability event differs from its transition")

        previous_ref = self.current_transition_by_request.get(transition.request_ref)
        if transition.lifecycle == CapabilityLifecycle.PROPOSED:
            if previous_ref is not None or transition.request_ref in self.proposals:
                raise ValueError("capability proposal was already introduced")
        else:
            if previous_ref != transition.previous_transition_ref:
                raise ValueError("capability transition does not extend the current chain")
            previous = self.transitions.get(previous_ref or "")
            if previous is None or previous.lifecycle not in _ALLOWED_PREVIOUS[
                transition.lifecycle
            ]:
                raise ValueError("capability lifecycle transition is not permitted")
            if any(
                (
                    transition.manifest_digest != previous.manifest_digest,
                    transition.capability_policy_digest
                    != previous.capability_policy_digest,
                    transition.originating_work_order_ref
                    != previous.originating_work_order_ref,
                    transition.problem_ref != previous.problem_ref,
                    transition.formal_fence_seq != previous.formal_fence_seq,
                    transition.scratch_fence_seq != previous.scratch_fence_seq,
                    transition.request_digest != previous.request_digest,
                    transition.run_input_digest != previous.run_input_digest,
                )
            ):
                raise ValueError("capability transition changed frozen authority")

        expected_model = _PHASE_MODELS.get(transition.lifecycle)
        phase_record = None
        if transition.phase_record_ref is not None:
            try:
                _phase_schema, phase_record = records[transition.phase_record_ref]
            except KeyError as error:
                raise ValueError("capability phase record is absent") from error
        if expected_model is None:
            if phase_record is not None:
                raise ValueError("this capability transition cannot carry a phase record")
        elif not isinstance(phase_record, expected_model):
            raise ValueError("capability phase record has the wrong type")

        proposal = (
            phase_record
            if transition.lifecycle == CapabilityLifecycle.PROPOSED
            else self.proposals.get(transition.request_ref)
        )
        if not isinstance(proposal, SimulationProposalV1):
            raise ValueError("capability transition has no canonical proposal")
        if (
            proposal.id != transition.request_ref
            or proposal.originating_work_order_ref
            != transition.originating_work_order_ref
            or proposal.problem_ref != transition.problem_ref
            or proposal.run_input_digest != transition.run_input_digest
        ):
            raise ValueError("simulation proposal differs from transition authority")

        if transition.lifecycle == CapabilityLifecycle.PROPOSED:
            self.proposals[proposal.id] = proposal
        elif isinstance(phase_record, SimulationGrantV1):
            if phase_record.proposal_ref != proposal.id:
                raise ValueError("simulation grant names another proposal")
            if phase_record.run_input_digest != proposal.run_input_digest:
                raise ValueError("simulation grant names another run input")
            self.grants[phase_record.id] = phase_record
        elif isinstance(phase_record, CompiledSimulationV1):
            if phase_record.proposal_ref != proposal.id:
                raise ValueError("compiled simulation names another proposal")
            self.compiled[phase_record.id] = phase_record
        elif isinstance(phase_record, SimulationWorkOrderV1):
            if phase_record.proposal_ref != proposal.id:
                raise ValueError("simulation work order names another proposal")
            if phase_record.run_input_digest != proposal.run_input_digest:
                raise ValueError("simulation work order names another run input")
            compiled = self.compiled.get(phase_record.compiled_simulation_ref)
            if (
                compiled is None
                or compiled.proposal_ref != proposal.id
                or compiled.grant_ref != phase_record.grant_ref
            ):
                raise ValueError("simulation work order has no matching compilation")
            self.work_orders[phase_record.id] = phase_record
        elif isinstance(phase_record, SimulationExecutionReceiptV1):
            if phase_record.proposal_ref != proposal.id:
                raise ValueError("simulation receipt names another proposal")
            if phase_record.run_input_digest != proposal.run_input_digest:
                raise ValueError("simulation receipt names another run input")
            work_order = self.work_orders.get(phase_record.simulation_work_order_ref)
            if (
                work_order is None
                or work_order.proposal_ref != proposal.id
                or work_order.compiled_simulation_ref
                != phase_record.compiled_specification_ref
            ):
                raise ValueError("simulation receipt has no matching work order")
            self.receipts[phase_record.id] = phase_record
        elif isinstance(phase_record, SimulationResultPackageV1):
            if phase_record.proposal_ref != proposal.id:
                raise ValueError("simulation package names another proposal")
            if phase_record.run_input_digest != proposal.run_input_digest:
                raise ValueError("simulation package names another run input")
            self.result_packages[phase_record.id] = phase_record
        elif isinstance(phase_record, SimulationConsumptionV1):
            if phase_record.proposal_ref != proposal.id:
                raise ValueError("simulation consumption names another proposal")
            if phase_record.run_input_digest != proposal.run_input_digest:
                raise ValueError("simulation consumption names another run input")
            if any(
                item.result_package_ref == phase_record.result_package_ref
                for item in self.consumptions.values()
            ):
                raise ValueError("simulation result package was consumed more than once")
            self.consumptions[phase_record.id] = phase_record

        self.transitions[transition.id] = transition
        self.current_transition_by_request[transition.request_ref] = transition.id
        self.event_seqs.append(event.seq)
        self.process_digest = transition.next_process_digest


__all__ = ["CapabilityReplayState"]
