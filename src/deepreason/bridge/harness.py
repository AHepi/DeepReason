"""Full-harness integration for fixed-fence grounded final views."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from deepreason.bridge.compose import CompositionRequestV1
from deepreason.bridge.evidence_pack import (
    EvidencePackV1,
    assemble_evidence_pack,
    build_claim_ledger_catalog,
)
from deepreason.bridge.events import BridgeAction
from deepreason.bridge.models import (
    BridgeFailureDiagnosticV1,
    BridgeFailureV1,
    BridgeResolution,
)
from deepreason.bridge.retry import (
    BridgeWorkflowAttemptFenceV1,
    WorkflowRetryPolicyV1,
    bridge_prompt_policy_digest,
    run_bridge_workflow_with_retries,
)
from deepreason.bridge.workflow import (
    BridgePersistenceBatch,
    BridgeWorkflow,
    BridgeWorkflowPolicy,
    BridgeWorkflowResultV1,
)
from deepreason.ontology.frozen import FrozenList, FrozenRecord
from deepreason.runtime.progress import _atomic_json
from deepreason.scratch.service import ScratchService


BRIDGE_RESULT_NAME = "bridge-result.json"
BRIDGE_STATUS_NAME = "bridge-status.json"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class BridgeTerminalResultV1(FrozenRecord):
    """Fixed, machine-readable pointer record for one terminal bridge run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_: Literal["deepreason-bridge-result-v1"] = Field(
        "deepreason-bridge-result-v1", alias="schema"
    )
    run_manifest_digest: str
    formal_seq: int = Field(ge=0)
    source_run_digest: str | None = None
    terminal_event_seq: int = Field(ge=0)
    problem_id: str = Field(min_length=1, max_length=512)
    target: Literal["thesis", "summary", "answer"]
    evidence_pack_id: str
    claim_ledger_id: str | None = None
    bridge_output_id: str | None = None
    validation_report_id: str | None = None
    review_id: str | None = None
    failure_id: str | None = None
    resolution: BridgeResolution | None = None
    output_paths: list[str] = Field(default_factory=FrozenList, max_length=32)
    process_status: Literal["success", "failure"]
    error_code: str | None = None
    error_message: str | None = Field(default=None, max_length=16_384)

    @field_validator("run_manifest_digest", "source_run_digest")
    @classmethod
    def _manifest_digest(cls, value):
        if value is None:
            return value
        if _SHA256.fullmatch(value) is None:
            raise ValueError("digest must be 64 lowercase hex characters")
        return value

    @field_validator("output_paths", mode="after")
    @classmethod
    def _safe_output_paths(cls, value):
        for item in value:
            path = PurePosixPath(item)
            if (
                not item
                or len(item) > 512
                or path.is_absolute()
                or ".." in path.parts
                or "\\" in item
            ):
                raise ValueError("output_paths must be bounded relative POSIX paths")
        return FrozenList(value)

    @model_validator(mode="after")
    def _terminal_shape(self):
        # In a same-root build the terminal event necessarily follows the
        # formal fence in one sequence.  A derived build has two independent
        # append-only logs, so comparing their sequence numbers is meaningless.
        if self.source_run_digest is None and self.terminal_event_seq <= self.formal_seq:
            raise ValueError("terminal event must follow the fixed formal fence")
        if self.process_status == "success":
            if any(
                value is None
                for value in (
                    self.claim_ledger_id,
                    self.bridge_output_id,
                    self.validation_report_id,
                    self.resolution,
                )
            ):
                raise ValueError("successful terminal result requires bridge object IDs")
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("successful terminal result cannot carry an error")
            if self.failure_id is not None:
                raise ValueError("successful terminal result cannot name a failure")
        elif (
            self.error_code is None
            or self.error_message is None
            or self.failure_id is None
        ):
            raise ValueError("failed terminal result requires replay-backed diagnostics")
        return self


class _HarnessBridgeSink:
    def __init__(
        self,
        harness,
        evidence_pack: EvidencePackV1,
        catalog,
        *,
        manifest_digest: str,
        problem_id: str,
        target: str,
    ) -> None:
        self.harness = harness
        self.evidence_pack = evidence_pack
        self.catalog = catalog
        self.manifest_digest = manifest_digest
        self.problem_id = problem_id
        self.target = target
        self._pack_written = False
        self.failure: BridgeFailureV1 | None = None

    def persist_bridge_batch(self, batch: BridgePersistenceBatch) -> None:
        records = list(batch.records)
        first_material_event = batch.action in {
            BridgeAction.LEDGER_CREATED,
            BridgeAction.FAILED,
        }
        if first_material_event and not self._pack_written:
            records.insert(0, ("bridge-evidence-pack", self.evidence_pack))
            if batch.action == BridgeAction.FAILED:
                records.insert(1, ("bridge-ledger-input-catalog", self.catalog))
            self._pack_written = True
        if batch.action == BridgeAction.FAILED:
            if batch.error_code is None or batch.error_message is None:
                raise RuntimeError("failed bridge batch lacks typed diagnostics")
            if batch.failure_phase is None:
                raise RuntimeError("failed bridge batch lacks a phase")

            def partial_id(mapping):
                matches = [object_id for object_id in batch.inputs if object_id in mapping]
                if len(matches) > 1:
                    raise RuntimeError("failed bridge batch has ambiguous partial objects")
                return matches[0] if matches else None

            state = self.harness.bridge_state
            diagnostics = []
            for item in batch.failure_diagnostics:
                values = item.model_dump(mode="json")
                code = str(values.get("code") or "")
                if re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", code) is None:
                    values["code"] = "BRIDGE_REPAIR_DIAGNOSTIC"
                diagnostics.append(BridgeFailureDiagnosticV1.model_validate(values))
            self.failure = BridgeFailureV1.create(
                run_manifest_digest=self.manifest_digest,
                formal_seq=self.evidence_pack.formal_seq,
                problem_ref=self.problem_id,
                output_target=self.target,
                evidence_pack_id=self.evidence_pack.id,
                catalog_id=self.catalog.id,
                phase=batch.failure_phase,
                error_code=batch.error_code,
                error_message=batch.error_message,
                claim_ledger_id=partial_id(state.ledgers),
                bridge_output_id=partial_id(state.outputs),
                validation_report_id=partial_id(state.validation_reports),
                review_id=partial_id(state.grounding_reviews),
                diagnostics=diagnostics,
                terminal_inputs=list(batch.inputs),
            )
            records.append(("bridge-failure", self.failure))
        self.harness.record_bridge_event(
            batch.action,
            actor=batch.actor,
            inputs=batch.inputs,
            records=records,
            llm=batch.llm,
            finding_ref=batch.finding_ref,
            error_code=batch.error_code,
        )


def _bound_manifest_digest(root, supplied: str) -> str:
    if _SHA256.fullmatch(supplied) is None:
        raise ValueError("run_manifest_digest must be 64 lowercase hex characters")
    path = root / "run-manifest.sha256"
    if path.is_symlink():
        raise ValueError("BRIDGE_MANIFEST_MISMATCH")
    if path.is_file():
        bound = path.read_text(encoding="utf-8").strip()
        if bound != supplied:
            raise ValueError("BRIDGE_MANIFEST_MISMATCH")
    return supplied


def _bound_scratch_attention_policy(root, manifest_digest: str, attention_pack):
    """Load the sole compiled coverage authority for a model-bound pack.

    Direct low-level fixtures predating RunManifest v3 may have no manifest.
    Production v3 runs do, and must use its immutable scratch policy rather
    than a caller-authored coverage knob.
    """

    if attention_pack is None:
        return None
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    path = root / MANIFEST_NAME
    if path.is_symlink():
        raise ValueError("BRIDGE_MANIFEST_MISMATCH")
    if not path.is_file():
        return None
    manifest = load_run_manifest(path)
    if manifest.sha256 != manifest_digest:
        raise ValueError("BRIDGE_MANIFEST_MISMATCH")
    scratch = manifest.scratch_policy
    if manifest.schema_version not in {3, 4} or scratch is None or not scratch.enabled:
        raise ValueError("BRIDGE_SCRATCH_MANIFEST_V3_REQUIRED")
    return scratch.attention_policy()


def _bound_bridge_execution(root, manifest_digest: str, supplied_policy):
    """Resolve the sole v4 contract/retry authority from the bound manifest.

    A missing or historical manifest preserves the original low-level fixture
    path exactly.  For v4, callers may supply only the bridge-policy projection;
    the control plane owns the wire contract and whole-workflow retry ceiling.
    """

    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    supplied = BridgeWorkflowPolicy.model_validate(supplied_policy)
    path = root / MANIFEST_NAME
    if path.is_symlink():
        raise ValueError("BRIDGE_MANIFEST_MISMATCH")
    if not path.is_file():
        return supplied, WorkflowRetryPolicyV1(), None
    manifest = load_run_manifest(path)
    if manifest.sha256 != manifest_digest:
        raise ValueError("BRIDGE_MANIFEST_MISMATCH")
    if manifest.schema_version < 4:
        return supplied, WorkflowRetryPolicyV1(), None

    control = manifest.control_plane_policy
    bridge = manifest.bridge_policy
    if control is None or bridge is None:
        raise ValueError("BRIDGE_CONTROL_POLICY_V4_REQUIRED")
    historical_projection = bridge.workflow_policy(ledger_contract_version="v1")
    if supplied != historical_projection:
        raise ValueError("BRIDGE_WORKFLOW_POLICY_MISMATCH")
    contract_version = {
        "bridge.ledger.v1": "v1",
        "bridge.ledger.v2": "v2",
    }[control.contract_versions.bridge_ledger_wire_contract]
    effective = bridge.workflow_policy(ledger_contract_version=contract_version)
    routes = manifest.roles.get(effective.ledger_role, ())
    if not routes:
        raise ValueError("BRIDGE_LEDGER_ROUTE_REQUIRED")
    from deepreason.llm.firewall import EndpointLease

    seat, route = next(iter(enumerate(routes)))
    return (
        effective,
        control.workflow_retry,
        EndpointLease(role=effective.ledger_role, seat=seat, route=route),
    )


def _assert_adapter_matches_retry_lease(adapter, expected) -> None:
    """Fail before dispatch if runtime wiring differs from manifest authority."""

    from deepreason.bridge.retry import WorkflowRetryBoundaryError
    from deepreason.llm.firewall import RouteFirewallError, select_lease

    try:
        actual = select_lease(adapter.leases, expected.role, expected.seat)
        configured = adapter.endpoints[expected.role]
        endpoints = (
            tuple(configured)
            if isinstance(configured, (list, tuple))
            else (configured,)
        )
        endpoint = endpoints[expected.seat]
        expected.verify(endpoint)
    except (AttributeError, IndexError, KeyError, RouteFirewallError) as error:
        raise WorkflowRetryBoundaryError(
            "BRIDGE_WORKFLOW_RETRY_ROUTE_CHANGED"
        ) from error
    if actual != expected:
        raise WorkflowRetryBoundaryError("BRIDGE_WORKFLOW_RETRY_ROUTE_CHANGED")


def _terminal_record(
    *,
    result: BridgeWorkflowResultV1,
    evidence_pack: EvidencePackV1,
    manifest_digest: str,
    problem_id: str,
    target: str,
    terminal_event_seq: int,
    failure_id: str | None,
) -> BridgeTerminalResultV1:
    output = result.bridge_output
    return BridgeTerminalResultV1(
        run_manifest_digest=manifest_digest,
        formal_seq=evidence_pack.formal_seq,
        source_run_digest=evidence_pack.source_run_digest,
        terminal_event_seq=terminal_event_seq,
        problem_id=problem_id,
        target=target,
        evidence_pack_id=evidence_pack.id,
        claim_ledger_id=(result.claim_ledger.id if result.claim_ledger is not None else None),
        bridge_output_id=(output.id if output is not None else None),
        validation_report_id=(
            result.validation_report.id if result.validation_report is not None else None
        ),
        review_id=(
            result.grounded_review.id if result.grounded_review is not None else None
        ),
        failure_id=failure_id,
        resolution=(output.resolution if output is not None else None),
        process_status=result.process_status,
        error_code=result.error_code,
        error_message=result.error_message,
    )


def build_grounded_bridge(
    harness,
    problem_id: str,
    target: Literal["thesis", "summary", "answer"],
    policy: BridgeWorkflowPolicy | dict,
    *,
    run_manifest_digest: str,
    stage_a_adapter,
    composition_adapter=None,
    review_adapter=None,
    repair_adapter=None,
    attention_pack=None,
    source_harness=None,
    source_run_digest: str | None = None,
    source_sealed_blob_refs: frozenset[str] | None = None,
    evidence_budget_chars: int = 24_000,
    desired_length_chars: int = 16_384,
    maximum_sections: int = 32,
    formatting_profile: str = "plain",
) -> BridgeTerminalResultV1:
    """Build and persist one grounded final view without touching formal state."""

    harness._ensure_writable()
    derived = (
        source_harness is not None
        or source_run_digest is not None
        or source_sealed_blob_refs is not None
    )
    if derived and (source_harness is None or source_run_digest is None):
        raise ValueError(
            "derived bridge requires both source_harness and source_run_digest"
        )
    if derived:
        if not source_harness._read_only:
            raise ValueError("derived bridge source harness must be read-only")
        source_root = source_harness.root.resolve()
        destination_root = harness.root.resolve()
        if (
            source_root == destination_root
            or source_root.is_relative_to(destination_root)
            or destination_root.is_relative_to(source_root)
        ):
            raise ValueError("derived bridge source and destination must not overlap")
        if _SHA256.fullmatch(source_run_digest) is None:
            raise ValueError("source_run_digest must be 64 lowercase hex characters")
        from deepreason.bridge.derived import (
            _DerivedSourceIntegrityError,
            _source_snapshot,
            _verified_source_view,
        )

        observed_digest, observed_sealed_refs = _source_snapshot(source_harness)
        if observed_digest != source_run_digest:
            raise ValueError("derived bridge source digest does not match source fence")
        if (
            source_sealed_blob_refs is not None
            and source_sealed_blob_refs != observed_sealed_refs
        ):
            raise ValueError("derived bridge source availability does not match source fence")
        source_sealed_blob_refs = observed_sealed_refs
        if attention_pack is not None:
            raise ValueError(
                "derived bridge scratch attention must be canonically persisted first"
            )
        if any(vars(source_harness.scratch_state).values()):
            raise ValueError(
                "derived bridge does not accept source scratch state without "
                "canonical destination receipts"
            )
        source = source_harness
    else:
        source = harness
    if problem_id not in source.state.problems:
        raise KeyError(f"unknown problem {problem_id!r}")
    if target not in {"thesis", "summary", "answer"}:
        raise ValueError("target must be thesis, summary, or answer")
    manifest_digest = _bound_manifest_digest(harness.root, run_manifest_digest)
    attention_policy = _bound_scratch_attention_policy(
        harness.root, manifest_digest, attention_pack
    )
    workflow_policy, retry_policy, retry_lease = _bound_bridge_execution(
        harness.root, manifest_digest, policy
    )

    scratch_service = None
    context = None
    if attention_pack is not None:
        scratch_service = ScratchService(harness)
        context = scratch_service.prepare_advisory_context(attention_pack)

    formal_seq = source._next_seq - 1
    frozen = (
        _verified_source_view(source, sealed_refs=source_sealed_blob_refs)
        if derived
        else harness.at(harness.root, formal_seq)
    )
    source_formal_before = source.state.model_dump_json()
    source_commitments_before = dict(source.commitments)
    source_warrants_before = dict(source.warrants)
    sink_formal_before = harness.state.model_dump_json()
    sink_commitments_before = dict(harness.commitments)
    sink_warrants_before = dict(harness.warrants)
    if derived:
        try:
            evidence_pack = assemble_evidence_pack(
                frozen,
                problem_id,
                budget_chars=evidence_budget_chars,
                formal_seq=formal_seq,
                source_run_digest=source_run_digest,
            )
        except _DerivedSourceIntegrityError as error:
            raise ValueError(
                "derived bridge source blob changed during assembly"
            ) from error
    else:
        evidence_pack = assemble_evidence_pack(
            frozen,
            problem_id,
            budget_chars=evidence_budget_chars,
            formal_seq=formal_seq,
            source_run_digest=source_run_digest,
        )
    if derived:
        final_digest, final_sealed_refs = _source_snapshot(source)
        if (
            final_digest != source_run_digest
            or final_sealed_refs != source_sealed_blob_refs
        ):
            raise ValueError("derived bridge source changed while assembling evidence")
    catalog = build_claim_ledger_catalog(
        evidence_pack,
        target,
        advisory_context=context,
    )
    # Review receives exact excerpts from this closed, harness-authored catalog.
    # Scratch excerpts are deliberately omitted: provenance cannot ground a span.
    materials = {
        item.ref: item.excerpt for item in catalog.items if item.kind != "scratch"
    }
    composition_request = CompositionRequestV1(
        output_target=target,
        formatting_profile=formatting_profile,
        desired_length_chars=desired_length_chars,
        maximum_sections=maximum_sections,
    )
    if context is not None:
        assert scratch_service is not None
        committed = scratch_service.commit_prepared_advisory_context(
            attention_pack,
            context,
            context_ref=evidence_pack.id,
            coverage_policy=attention_policy,
        )
        if committed != context:
            raise RuntimeError("committed advisory context differs from prepared context")
    sinks: list[_HarnessBridgeSink] = []

    def workflow_factory(_attempt_number: int):
        sink = _HarnessBridgeSink(
            harness,
            evidence_pack,
            catalog,
            manifest_digest=manifest_digest,
            problem_id=problem_id,
            target=target,
        )
        sinks.append(sink)
        return BridgeWorkflow(
            stage_a_adapter,
            composition_adapter or stage_a_adapter,
            review_adapter=review_adapter,
            repair_adapter=repair_adapter,
            policy=workflow_policy,
            sink=sink,
        )

    if retry_lease is None:
        result = workflow_factory(1).run(
            catalog, composition_request, materials=materials
        )
    else:
        from deepreason.llm.firewall import route_fingerprint

        _assert_adapter_matches_retry_lease(stage_a_adapter, retry_lease)
        retry_route = retry_lease.route

        contract_id = (
            "bridge.claim-ledger.compact.v2"
            if workflow_policy.ledger_contract_version == "v2"
            else "bridge.claim-ledger.compact.v1"
        )
        prompt_policy_digest = bridge_prompt_policy_digest(
            workflow_policy, composition_request
        )
        attempt_fence = BridgeWorkflowAttemptFenceV1(
            manifest_digest=manifest_digest,
            formal_seq=formal_seq,
            catalog_id=catalog.id,
            contract_id=contract_id,
            prompt_policy_digest=prompt_policy_digest,
            role=retry_lease.role,
            seat=retry_lease.seat,
            endpoint_id=retry_route.endpoint_id,
            route_sha256=route_fingerprint(retry_route),
        )

        def failure_id_for_result(_result):
            failure = sinks[-1].failure
            if failure is None:
                raise RuntimeError("retryable bridge result lacks a persisted failure")
            return failure.id

        def persist_retry(receipt):
            harness.record_bridge_event(
                BridgeAction.WORKFLOW_RETRY_STARTED,
                inputs=[receipt.prior_failure_id],
                records=[("bridge-workflow-retry", receipt)],
            )

        result = run_bridge_workflow_with_retries(
            workflow_factory,
            catalog,
            composition_request,
            retry_policy=retry_policy,
            attempt_fence=attempt_fence,
            failure_id_for_result=failure_id_for_result,
            persist_retry=persist_retry,
            materials=materials,
            manifest_digest=manifest_digest,
            prompt_policy_digest=prompt_policy_digest,
            contract_id=contract_id,
        )
    sink = sinks[-1]

    if (
        source.state.model_dump_json() != source_formal_before
        or source.commitments != source_commitments_before
        or source.warrants != source_warrants_before
        or harness.state.model_dump_json() != sink_formal_before
        or harness.commitments != sink_commitments_before
        or harness.warrants != sink_warrants_before
    ):
        raise RuntimeError("bridge workflow altered formal materialized state")
    terminal_seq = harness._next_seq - 1
    terminal = _terminal_record(
        result=result,
        evidence_pack=evidence_pack,
        manifest_digest=manifest_digest,
        problem_id=problem_id,
        target=target,
        terminal_event_seq=terminal_seq,
        failure_id=sink.failure.id if sink.failure is not None else None,
    )
    payload = terminal.model_dump(mode="json", by_alias=True, exclude_none=True)
    _atomic_json(harness.root / BRIDGE_RESULT_NAME, payload)
    _atomic_json(
        harness.root / BRIDGE_STATUS_NAME,
        {
            "schema": "deepreason-bridge-status-v1",
            "state": "completed" if terminal.process_status == "success" else "failed",
            "process_status": terminal.process_status,
            "formal_seq": terminal.formal_seq,
            "terminal_event_seq": terminal.terminal_event_seq,
            "resolution": (
                terminal.resolution.value if terminal.resolution is not None else None
            ),
            "error_code": terminal.error_code,
        },
    )
    return terminal


__all__ = [
    "BRIDGE_RESULT_NAME",
    "BRIDGE_STATUS_NAME",
    "BridgeTerminalResultV1",
    "build_grounded_bridge",
]
