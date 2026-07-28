"""The research capability controller: directed fetches under frozen authority.

Mirrors the simulation controller's transactional discipline over the
shared capability transition machinery: PROPOSED → VALIDATED →
GRANTED/DENIED → COMPILED → DISPATCHED → SUCCEEDED/FAILED →
RESULT_PACKAGED → CONSUMED, one chained process digest per step.

The two owner decisions (docs/RESEARCH_BACKEND.md) are enforced here and
replay-validated in capabilities/state.py: every URL must match the
policy's frozen domain allowlist, and the fetch budget is denominated in
dispatched requests — cumulative across every proposal in the run — with
typed exhaustion receipts carrying count and limit.
"""

from __future__ import annotations

import hashlib

from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.models import (
    CapabilityBudgetDeltaV1,
    CapabilityTransitionV1,
    CompiledResearchFetchV1,
    ResearchConsumptionV1,
    ResearchExecutionReceiptV1,
    ResearchFetchAttemptV1,
    ResearchFetchProposalDraftV1,
    ResearchFetchProposalV1,
    ResearchFetchedItemV1,
    ResearchGrantV1,
    ResearchResultPackageV1,
    ResearchWorkOrderV1,
    capability_next_process_digest,
)

BACKEND_IDENTITY = "web.contained.v1"


class ResearchCapabilityController:
    """Compile directed-fetch proposals into contained, receipted execution."""

    def __init__(self, harness, manifest, *, transport=None) -> None:
        self.harness = harness
        self.manifest = manifest
        topology = manifest.inquiry_capability_policy
        self.policy = topology.research if topology is not None else None
        if manifest.schema_version != 6 or self.policy is None:
            raise ValueError("research controller requires one v6 run manifest")
        self.transport = transport
        self._current: dict[str, CapabilityTransitionV1] = {}

    # -- shared transition mechanics (simulation-controller idiom) --------

    def _transition(
        self,
        proposal: ResearchFetchProposalV1,
        lifecycle: CapabilityLifecycle,
        *,
        previous: CapabilityTransitionV1 | None,
        phase_record=None,
        reason_code: str,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> CapabilityTransitionV1:
        trigger_ref = (
            f"provider-call:{proposal.source_call_seq}"
            if previous is None
            else previous.id
        )
        budget_delta = {
            CapabilityLifecycle.PROPOSED: CapabilityBudgetDeltaV1(requests=1),
            CapabilityLifecycle.DISPATCHED: CapabilityBudgetDeltaV1(executions=1),
            CapabilityLifecycle.CONSUMED: CapabilityBudgetDeltaV1(
                result_follow_ups=1
            ),
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
            transition, phase_record=phase_record
        )
        self._current[proposal.id] = transition
        return transition

    # -- budget derivation (replayed state is the only authority) ---------

    def _requests_already_used(self) -> int:
        """Run-cumulative spend, derived from replayed receipts only.

        Each receipt's counter continues from the prior receipt's total
        (the fetcher is preloaded below), so the cumulative spend is the
        maximum total any receipt records — never a stored counter that
        could drift from the log."""

        return max(
            (
                receipt.requests_used_total
                for receipt in self.harness.capability_state.receipts.values()
                if isinstance(receipt, ResearchExecutionReceiptV1)
            ),
            default=0,
        )

    def _sources_already_consumed(self) -> int:
        return sum(
            len(consumption.evidence_refs)
            for consumption in self.harness.capability_state.consumptions.values()
            if isinstance(consumption, ResearchConsumptionV1)
        )

    # -- lifecycle --------------------------------------------------------

    def propose(
        self,
        draft: ResearchFetchProposalDraftV1,
        *,
        proposal_index: int,
        work_order,
        source_call_seq: int,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> ResearchFetchProposalV1:
        """Record semantic intent only; no validation, grant, or fetch."""

        from deepreason.workflow.models import CapabilityOutcome

        if (
            CapabilityOutcome.RESEARCH_REQUEST
            not in work_order.capability_grant.allowed_outcomes
        ):
            raise ValueError(
                "originating work order does not permit a research proposal"
            )
        proposal = ResearchFetchProposalV1.create(
            **draft.model_dump(mode="python"),
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

    def execute(
        self,
        proposal: ResearchFetchProposalV1,
        *,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> ResearchResultPackageV1 | None:
        """Validate, grant, compile, dispatch, and package one proposal.

        Returns the result package, or None when the proposal was denied
        (denial is itself a durable typed transition, never silence).
        """

        from deepreason.research.fetch import (
            ContainedFetcher,
            WebResearchConfigV1,
        )

        fences = {
            "formal_fence_seq": formal_fence_seq,
            "scratch_fence_seq": scratch_fence_seq,
        }
        previous = self._current[proposal.id]
        previous = self._transition(
            proposal,
            CapabilityLifecycle.VALIDATED,
            previous=previous,
            reason_code="harness_validation",
            **fences,
        )

        def denied(reason: str) -> None:
            self._transition(
                proposal,
                CapabilityLifecycle.DENIED,
                previous=previous,
                reason_code=reason,
                **fences,
            )

        if not self.policy.enabled:
            denied("research_disabled")
            return None
        if self.policy.backend_identity != BACKEND_IDENTITY:
            denied("backend_identity_mismatch")
            return None
        config = WebResearchConfigV1(
            domain_allowlist=self.policy.domain_allowlist,
            maximum_requests=self.policy.maximum_requests,
            maximum_response_bytes=self.policy.maximum_response_bytes,
        )
        if any(not config.allows(_host(url)) for url in proposal.urls):
            denied("url_outside_frozen_allowlist")
            return None
        already_used = self._requests_already_used()
        if already_used >= self.policy.maximum_requests:
            denied("requests_budget_exhausted")
            return None

        grant = ResearchGrantV1.create(
            proposal_ref=proposal.id,
            manifest_digest=self.manifest.sha256,
            run_input_digest=self.manifest.run_input_digest,
            policy_digest=self.policy.digest,
            backend_identity=BACKEND_IDENTITY,
            granted_urls=proposal.urls,
            requests_limit=self.policy.maximum_requests,
            maximum_response_bytes=self.policy.maximum_response_bytes,
        )
        previous = self._transition(
            proposal,
            CapabilityLifecycle.GRANTED,
            previous=previous,
            phase_record=grant,
            reason_code="allowlist_and_budget_validated",
            **fences,
        )
        compiled = CompiledResearchFetchV1.create(
            proposal_ref=proposal.id,
            grant_ref=grant.id,
            urls=grant.granted_urls,
            domain_allowlist=self.policy.domain_allowlist,
            requests_limit=grant.requests_limit,
            maximum_response_bytes=grant.maximum_response_bytes,
            timeout_seconds=config.timeout_seconds,
        )
        previous = self._transition(
            proposal,
            CapabilityLifecycle.COMPILED,
            previous=previous,
            phase_record=compiled,
            reason_code="fetch_plan_frozen",
            **fences,
        )
        work_order = ResearchWorkOrderV1.create(
            proposal_ref=proposal.id,
            grant_ref=grant.id,
            compiled_research_ref=compiled.id,
            manifest_digest=self.manifest.sha256,
            run_input_digest=self.manifest.run_input_digest,
            policy_digest=self.policy.digest,
            requests_limit=grant.requests_limit,
            maximum_response_bytes=grant.maximum_response_bytes,
        )
        previous = self._transition(
            proposal,
            CapabilityLifecycle.DISPATCHED,
            previous=previous,
            phase_record=work_order,
            reason_code="contained_fetch_dispatch",
            **fences,
        )

        fetcher = ContainedFetcher(config, transport=self.transport)
        # The budget is run-cumulative across proposals: preload what the
        # replayed capability state proves was already spent.
        fetcher.requests_used = already_used
        texts: dict[str, str] = {}
        for url in compiled.urls:
            outcome = fetcher.fetch(url)
            if outcome.text and outcome.receipt.content_sha256:
                texts[outcome.receipt.content_sha256] = outcome.text
        attempts = tuple(
            ResearchFetchAttemptV1(
                seq=receipt.seq,
                url=receipt.url,
                host=receipt.host,
                outcome=receipt.outcome,
                http_status=receipt.http_status,
                byte_count=receipt.byte_count,
                content_sha256=receipt.content_sha256,
                requests_used=receipt.requests_used,
            )
            for receipt in fetcher.drain_receipts()
        )
        exhausted = any(
            attempt.outcome == "RESEARCH_BUDGET_EXHAUSTED" for attempt in attempts
        )
        receipt = ResearchExecutionReceiptV1.create(
            proposal_ref=proposal.id,
            run_input_digest=self.manifest.run_input_digest,
            research_work_order_ref=work_order.id,
            compiled_specification_ref=compiled.id,
            attempts=attempts,
            requests_used_total=attempts[-1].requests_used,
            requests_limit=work_order.requests_limit,
            outcome=(
                "budget_exhausted"
                if exhausted
                else "fetched"
                if texts
                else "nothing_fetched"
            ),
        )
        previous = self._transition(
            proposal,
            CapabilityLifecycle.SUCCEEDED if texts else CapabilityLifecycle.FAILED,
            previous=previous,
            phase_record=receipt,
            reason_code=receipt.outcome,
            **fences,
        )
        items = []
        for attempt in attempts:
            if attempt.outcome != "FETCHED" or attempt.content_sha256 not in texts:
                continue
            text = texts[attempt.content_sha256]
            self.harness.blobs.put(text.encode("utf-8"))
            items.append(
                ResearchFetchedItemV1(
                    url=attempt.url,
                    content_sha256=attempt.content_sha256,
                    byte_count=attempt.byte_count,
                    text_sha256=hashlib.sha256(
                        text.encode("utf-8")
                    ).hexdigest(),
                )
            )
        package = ResearchResultPackageV1.create(
            proposal_ref=proposal.id,
            run_input_digest=self.manifest.run_input_digest,
            execution_receipt_ref=receipt.id,
            items=tuple(items),
        )
        self._transition(
            proposal,
            CapabilityLifecycle.RESULT_PACKAGED,
            previous=previous,
            phase_record=package,
            reason_code="fetched_material_packaged",
            **fences,
        )
        return package

    def consume(
        self,
        proposal: ResearchFetchProposalV1,
        package: ResearchResultPackageV1,
        problem,
        *,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> tuple[str, ...]:
        """Register packaged material as candidate evidence, bounded by the
        policy's maximum_sources across the whole run.

        Each consumed document is also deterministically segmented into
        admission blocks (increment C): the block ids land on the
        attackable reliability node — visible in packs — and the §4
        citation checker resolves them, so fetched material is citable
        and byte-checkable exactly like an attached dossier."""

        from deepreason.research.backends import register_evidence

        if not package.items:
            raise ValueError("an empty research package cannot be consumed")
        headroom = self.policy.maximum_sources - self._sources_already_consumed()
        if headroom <= 0:
            raise ValueError("research source budget is exhausted")
        evidence_refs = []
        for item in package.items[:headroom]:
            text = self.harness.blobs.get(item.text_sha256).decode("utf-8")
            blocks = blocks_for_fetched_text(text)
            evidence = register_evidence(
                self.harness,
                problem,
                text,
                item.url,
                via=BACKEND_IDENTITY,
                metadata={
                    "url": item.url,
                    "content_sha256": item.content_sha256,
                    "result_package_ref": package.id,
                    "citable_blocks": [block.id[:16] for block in blocks],
                },
            )
            evidence_refs.append(evidence.id)
        consumption = ResearchConsumptionV1.create(
            proposal_ref=proposal.id,
            run_input_digest=self.manifest.run_input_digest,
            result_package_ref=package.id,
            evidence_refs=tuple(evidence_refs),
        )
        self._transition(
            proposal,
            CapabilityLifecycle.CONSUMED,
            previous=self._current[proposal.id],
            phase_record=consumption,
            reason_code="evidence_registered",
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )
        return tuple(evidence_refs)


def _host(url: str) -> str:
    from urllib.parse import urlparse

    return (urlparse(url).hostname or "").lower()


def blocks_for_fetched_text(text: str):
    """Deterministically segment one fetched document into admission blocks.

    The core admission parser is the single canonical segmenter: the same
    text bytes mint the same block ids forever (parser-version-bound), and
    span blocks reference the text bytes — which consume() stores
    content-addressed in blobs — so quote byte-checks resolve through the
    same path as attached-dossier blocks.
    """

    from deepreason.admission import AdmissionInput, admit_sources
    from deepreason.evidence.models import AttachedSourceProvenanceV1

    dossier, _report = admit_sources(
        [AdmissionInput(locator="research-fetch", data=text.encode("utf-8"))],
        problem_ref="research-consumption",
        provenance=AttachedSourceProvenanceV1(
            supplied_by="deepreason.research",
            acquisition_method="contained directed fetch",
            note=None,
        ),
    )
    return tuple(dossier.blocks)


def consumed_research_blocks(harness):
    """Re-derive every consumed document's citable blocks from replayed
    state and content-addressed blobs alone — never a stored listing."""

    blocks = []
    packages = {
        package.id: package
        for package in harness.capability_state.result_packages.values()
        if isinstance(package, ResearchResultPackageV1)
    }
    for consumption in harness.capability_state.consumptions.values():
        if not isinstance(consumption, ResearchConsumptionV1):
            continue
        package = packages.get(consumption.result_package_ref)
        if package is None:
            continue
        for item in package.items:
            try:
                text = harness.blobs.get(item.text_sha256).decode("utf-8")
            except KeyError:
                continue
            blocks.extend(blocks_for_fetched_text(text))
    return tuple(blocks)


__all__ = [
    "BACKEND_IDENTITY",
    "ResearchCapabilityController",
    "blocks_for_fetched_text",
    "consumed_research_blocks",
]
