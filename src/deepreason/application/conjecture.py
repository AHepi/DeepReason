"""Shared application boundary for one capability-typed conjecture call.

The full scheduler and reduced Mini loop may differ in breadth, but their
overlapping provider call uses the same workflow planner, canonical records,
and replay seam.  This module keeps that authority choreography out of client
code while leaving semantic candidate construction and admission where they
already live.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from deepreason.llm.firewall import EndpointLease
from deepreason.workflow.models import GuardFindingV1, RouteLeaseRefV1
from deepreason.workflow.profiles import route_lease_reference
from deepreason.workflow.shadow import (
    ConjectureShadowObserver,
    ShadowComparisonV1,
    ShadowTicketV1,
)
from deepreason.workflow.trace import ConjectureControlTrace


def _shared_meter_snapshot(value: Mapping[str, int] | None):
    if value is None:
        return None
    snapshot = dict(value)
    # The reduced compatibility meter predates reserve/settle.  Its truthful
    # outstanding reservation is therefore always zero; keep that projection
    # inside the shared boundary so historical Mini result payloads do not
    # acquire a new field.
    snapshot.setdefault("reserved", 0)
    return snapshot


@dataclass(slots=True)
class ConjectureApplicationBoundary:
    """One shared authority envelope around an existing conjecture path."""

    harness: Any
    observer: ConjectureShadowObserver
    ticket: ShadowTicketV1
    trace: ConjectureControlTrace
    problem_ref: str
    findings: tuple[GuardFindingV1, ...] = field(default=(), init=False)

    @classmethod
    def begin(
        cls,
        harness: Any,
        manifest: Any,
        *,
        problem_ref: str,
        route_lease: EndpointLease | RouteLeaseRefV1,
        contract_id: str,
        school_id: str | None = None,
        meter_before: Mapping[str, int] | None = None,
        advisory_context_ref: str | None = None,
    ) -> "ConjectureApplicationBoundary | None":
        """Plan one owned v4 call, or leave historical/legacy runs untouched."""

        observer = ConjectureShadowObserver.from_manifest(manifest)
        if observer is None:
            return None
        event_start_seq = harness._next_seq
        fence = max(0, event_start_seq - 1)
        try:
            ticket = observer.begin_conjecture(
                problem_ref=problem_ref,
                canonical_problem_refs=tuple(sorted(harness.state.problems)),
                school_id=school_id,
                route_lease=(
                    route_lease_reference(route_lease)
                    if isinstance(route_lease, EndpointLease)
                    else route_lease
                ),
                contract_id=contract_id,
                formal_fence_seq=fence,
                scratch_fence_seq=fence,
                event_start_seq=event_start_seq,
                meter_before=_shared_meter_snapshot(meter_before),
                advisory_context_ref=advisory_context_ref,
            )
        except Exception:
            if observer.profile.mode in {"active_conjecture", "active_inquiry"}:
                raise
            return None
        authoritative = observer.profile.mode in {"active_conjecture", "active_inquiry"}
        trace = ConjectureControlTrace(
            harness,
            ticket,
            authoritative=authoritative,
        )
        return cls(
            harness=harness,
            observer=observer,
            ticket=ticket,
            trace=trace,
            problem_ref=problem_ref,
        )

    @property
    def work_order_id(self) -> str:
        return self.trace.ticket.work_order.id

    def authorize_dispatch(self, reserved_tokens: int) -> str | None:
        return self.trace.authorize_dispatch(reserved_tokens)

    def authorize_repair(self, rejected_attempt: Any) -> None:
        self.trace.record_repair_request(rejected_attempt)

    def record_provider_result(
        self,
        *,
        source_call_seq: int,
        llm_call: Any,
        candidate_refs: Sequence[str],
    ) -> None:
        self.trace.record_provider_result(
            source_call_seq=source_call_seq,
            llm_call=llm_call,
            candidate_refs=tuple(candidate_refs),
        )

    def record_guard(self, findings: Sequence[GuardFindingV1]) -> None:
        self.findings = tuple(
            GuardFindingV1.model_validate(
                finding.model_dump(mode="python", by_alias=True)
                if isinstance(finding, GuardFindingV1)
                else finding
            )
            for finding in findings
        )
        if self.findings:
            self.trace.record_guard(self.findings)

    def complete(
        self,
        *,
        admitted_refs: Sequence[str],
        meter_after: Mapping[str, int] | None = None,
    ) -> ShadowComparisonV1 | None:
        """Close, compare, and checkpoint after the semantic path completes."""

        try:
            self.trace.finish()
            comparison = self.observer.finish_conjecture(
                self.trace.ticket,
                actual_problem_ref=self.problem_ref,
                events=tuple(self.harness._events_since(self.ticket.event_start_seq)),
                admitted_refs=tuple(admitted_refs),
                candidate_dispositions=self.findings,
                meter_after=_shared_meter_snapshot(meter_after),
            )
            self.trace.finalize(comparison)
            return comparison
        except Exception:
            self.trace.seal()
            if self.trace.authoritative:
                raise
            return None

    def abandon(self, trigger_ref: str) -> None:
        """Close a durable prefix after a call cannot produce a full receipt."""

        self.trace.abandon(trigger_ref)


__all__ = ["ConjectureApplicationBoundary"]
