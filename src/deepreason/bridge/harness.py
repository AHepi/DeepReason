"""Full-harness integration for fixed-fence grounded final views."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
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
from deepreason.bridge.ledger import ClaimLedgerInputCatalogV1, ClaimLedgerInputCatalogV3
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
from deepreason.canonical import canonical_json
from deepreason.ontology.frozen import FrozenList, FrozenRecord
from deepreason.runtime.progress import _atomic_json
from deepreason.scratch.service import ScratchService
from deepreason.storage.objects import ObjectStore


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
    source_terminal_commitment_ref: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
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


_BRIDGE_EXECUTION_SNAPSHOT_SCHEMA = "bridge.execution-snapshot.v1"
_BRIDGE_TRANSACTION_SCHEMA_V2 = "bridge.transaction-task.v2"
_BRIDGE_TASK_KINDS = {
    "bridge_ledger",
    "bridge_composition",
    "bridge_review",
    "repair",
}


@dataclass(frozen=True)
class _BridgeExecutionSnapshot:
    execution_id: str
    snapshot_ref: str
    manifest_digest: str
    formal_seq: int
    problem_id: str
    target: str
    source_run_digest: str | None
    source_terminal_commitment_ref: str | None
    evidence_budget_chars: int
    attention_pack_id: str | None
    advisory_context_id: str | None
    evidence_pack: EvidencePackV1
    catalog: ClaimLedgerInputCatalogV1
    composition_request: CompositionRequestV1
    workflow_policy: BridgeWorkflowPolicy


def _snapshot_model_value(value):
    return value.model_dump(mode="json", by_alias=True, exclude_none=True)


def _attention_pack_id(attention_pack) -> str | None:
    value = getattr(attention_pack, "id", None)
    return str(value) if value is not None else None


def _snapshot_error(code: str) -> ValueError:
    return ValueError(code)


def _load_bridge_execution_snapshot(
    harness,
    snapshot_ref: str,
    *,
    manifest_digest: str,
) -> _BridgeExecutionSnapshot:
    try:
        raw = harness.blobs.get(snapshot_ref)
        payload = json.loads(raw.decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_INVALID") from error
    if not isinstance(payload, Mapping) or canonical_json(payload) != raw:
        raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_INVALID")
    if (
        payload.get("schema") != _BRIDGE_EXECUTION_SNAPSHOT_SCHEMA
        or payload.get("manifest_digest") != manifest_digest
    ):
        raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_AUTHORITY_MISMATCH")
    formal_seq = payload.get("formal_seq")
    evidence_budget_chars = payload.get("evidence_budget_chars")
    problem_id = payload.get("problem_id")
    target = payload.get("target")
    source_run_digest = payload.get("source_run_digest")
    source_terminal_commitment_ref = payload.get(
        "source_terminal_commitment_ref"
    )
    attention_pack_id = payload.get("attention_pack_id")
    advisory_context_id = payload.get("advisory_context_id")
    if (
        type(formal_seq) is not int
        or formal_seq < 0
        or type(evidence_budget_chars) is not int
        or evidence_budget_chars <= 0
        or not isinstance(problem_id, str)
        or not problem_id
        or target not in {"thesis", "summary", "answer"}
        or source_run_digest is not None
        and not isinstance(source_run_digest, str)
        or source_terminal_commitment_ref is not None
        and (
            not isinstance(source_terminal_commitment_ref, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", source_terminal_commitment_ref)
            is None
        )
        or attention_pack_id is not None
        and not isinstance(attention_pack_id, str)
        or advisory_context_id is not None
        and not isinstance(advisory_context_id, str)
    ):
        raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_INVALID")
    try:
        evidence_pack = EvidencePackV1.model_validate(payload["evidence_pack"])
        catalog_value = payload["catalog"]
        if not isinstance(catalog_value, Mapping):
            raise TypeError("catalog must be an object")
        catalog_type = (
            ClaimLedgerInputCatalogV3
            if catalog_value.get("schema") == "bridge.catalog.v3"
            else ClaimLedgerInputCatalogV1
        )
        catalog = catalog_type.model_validate(catalog_value)
        composition_request = CompositionRequestV1.model_validate(
            payload["composition_request"]
        )
        workflow_policy = BridgeWorkflowPolicy.model_validate(payload["workflow_policy"])
    except (KeyError, TypeError, ValueError) as error:
        raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_INVALID") from error
    if (
        evidence_pack.formal_seq != formal_seq
        or evidence_pack.problem_ref != problem_id
        or evidence_pack.source_run_digest != source_run_digest
        or evidence_pack.source_terminal_commitment_ref
        != source_terminal_commitment_ref
        or catalog.formal_seq != formal_seq
        or catalog.problem_ref != problem_id
        or catalog.output_target != target
        or composition_request.output_target != target
    ):
        raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_AUTHORITY_MISMATCH")
    return _BridgeExecutionSnapshot(
        execution_id=f"bridge-execution:{snapshot_ref}",
        snapshot_ref=snapshot_ref,
        manifest_digest=manifest_digest,
        formal_seq=formal_seq,
        problem_id=problem_id,
        target=target,
        source_run_digest=source_run_digest,
        source_terminal_commitment_ref=source_terminal_commitment_ref,
        evidence_budget_chars=evidence_budget_chars,
        attention_pack_id=attention_pack_id,
        advisory_context_id=advisory_context_id,
        evidence_pack=evidence_pack,
        catalog=catalog,
        composition_request=composition_request,
        workflow_policy=workflow_policy,
    )


def _write_bridge_execution_snapshot(
    harness,
    *,
    manifest_digest: str,
    formal_seq: int,
    problem_id: str,
    target: str,
    source_run_digest: str | None,
    source_terminal_commitment_ref: str | None,
    evidence_budget_chars: int,
    attention_pack,
    advisory_context,
    evidence_pack: EvidencePackV1,
    catalog: ClaimLedgerInputCatalogV1,
    composition_request: CompositionRequestV1,
    workflow_policy: BridgeWorkflowPolicy,
) -> _BridgeExecutionSnapshot:
    payload = {
        "schema": _BRIDGE_EXECUTION_SNAPSHOT_SCHEMA,
        "manifest_digest": manifest_digest,
        "formal_seq": formal_seq,
        "problem_id": problem_id,
        "target": target,
        "source_run_digest": source_run_digest,
        "source_terminal_commitment_ref": source_terminal_commitment_ref,
        "evidence_budget_chars": evidence_budget_chars,
        "attention_pack_id": _attention_pack_id(attention_pack),
        "advisory_context_id": (
            str(advisory_context.id) if advisory_context is not None else None
        ),
        "evidence_pack": _snapshot_model_value(evidence_pack),
        "catalog": _snapshot_model_value(catalog),
        "composition_request": _snapshot_model_value(composition_request),
        "workflow_policy": _snapshot_model_value(workflow_policy),
    }
    snapshot_ref = harness.blobs.put(canonical_json(payload))
    return _load_bridge_execution_snapshot(
        harness,
        snapshot_ref,
        manifest_digest=manifest_digest,
    )


def _find_bridge_execution_snapshot(
    harness,
    manifest_digest: str,
    source_terminal_commitment_ref: str | None,
):
    v2_items = []
    for item in harness.workflow_state.transaction_work.values():
        payload = item.preparation.task_payload_value
        task_kind = getattr(item.preparation.task_kind, "value", item.preparation.task_kind)
        if (
            isinstance(payload, Mapping)
            and payload.get("schema")
            in {_BRIDGE_TRANSACTION_SCHEMA_V2, "contract-decomposition-child.v1"}
            and isinstance(payload.get("execution_id"), str)
            and isinstance(payload.get("execution_snapshot_ref"), str)
        ):
            v2_items.append((item, payload))
        elif item.terminal is None and task_kind in _BRIDGE_TASK_KINDS:
            raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_MISSING")
    if not v2_items:
        return None
    execution_ids = {payload.get("execution_id") for _item, payload in v2_items}
    snapshot_refs = {
        payload.get("execution_snapshot_ref") for _item, payload in v2_items
    }
    if (
        len(execution_ids) != 1
        or len(snapshot_refs) != 1
        or not isinstance(next(iter(execution_ids)), str)
        or not isinstance(next(iter(snapshot_refs)), str)
    ):
        raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_AMBIGUOUS")
    execution_id = next(iter(execution_ids))
    snapshot_ref = next(iter(snapshot_refs))
    snapshot = _load_bridge_execution_snapshot(
        harness,
        snapshot_ref,
        manifest_digest=manifest_digest,
    )
    if (
        execution_id != snapshot.execution_id
        or snapshot.source_terminal_commitment_ref
        != source_terminal_commitment_ref
    ):
        raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_AUTHORITY_MISMATCH")
    for item, payload in v2_items:
        if (
            item.preparation.manifest_digest != manifest_digest
            or item.preparation.formal_fence_seq != snapshot.formal_seq
            or item.preparation.scratch_fence_seq != snapshot.formal_seq
            or payload.get("execution_id") != snapshot.execution_id
            or payload.get("execution_snapshot_ref") != snapshot.snapshot_ref
            or item.preparation.source_terminal_commitment_ref
            != source_terminal_commitment_ref
        ):
            raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_AUTHORITY_MISMATCH")
    return snapshot


def _transactional_bridge_adapters(*adapters):
    unique = []
    seen = set()
    for adapter in adapters:
        if id(adapter) in seen:
            continue
        seen.add(id(adapter))
        if callable(getattr(adapter, "bind_bridge_execution", None)):
            unique.append(adapter)
    return tuple(unique)


def _transactional_v6_manifest_required(*adapters) -> bool:
    """Return whether canonical transactional bridge authority is present."""

    from deepreason.bridge.transactional_adapter import TransactionalBridgeAdapter

    return any(
        isinstance(adapter, TransactionalBridgeAdapter)
        for adapter in adapters
        if adapter is not None
    )


def _transactional_source_terminal_commitment_ref(*adapters) -> str | None:
    transactional = _transactional_bridge_adapters(*adapters)
    if not transactional:
        return None
    refs = {
        adapter.source_terminal_commitment_ref for adapter in transactional
    }
    if None in refs or len(refs) != 1:
        raise ValueError("BRIDGE_TERMINAL_AUTHORITY_MISMATCH")
    return next(iter(refs))


def _assert_snapshot_matches_invocation(
    snapshot: _BridgeExecutionSnapshot,
    *,
    problem_id: str,
    target: str,
    source_run_digest: str | None,
    source_terminal_commitment_ref: str | None,
    evidence_budget_chars: int,
    attention_pack,
    composition_request: CompositionRequestV1,
    workflow_policy: BridgeWorkflowPolicy,
) -> None:
    if (
        snapshot.problem_id != problem_id
        or snapshot.target != target
        or snapshot.source_run_digest != source_run_digest
        or snapshot.source_terminal_commitment_ref
        != source_terminal_commitment_ref
        or snapshot.evidence_budget_chars != evidence_budget_chars
        or snapshot.attention_pack_id != _attention_pack_id(attention_pack)
        or snapshot.composition_request != composition_request
        or snapshot.workflow_policy != workflow_policy
    ):
        raise _snapshot_error("BRIDGE_RECOVERY_SNAPSHOT_AUTHORITY_MISMATCH")


def _read_existing_bridge_terminal(
    harness,
    *,
    manifest_digest: str,
    problem_id: str,
    target: str,
    source_run_digest: str | None,
    source_terminal_commitment_ref: str | None,
) -> BridgeTerminalResultV1 | None:
    path = harness.root / BRIDGE_RESULT_NAME
    if path.is_symlink() or path.exists() and not path.is_file():
        raise ValueError("BRIDGE_RESULT_INVALID")
    if not path.is_file():
        return None
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        encoded = canonical_json(payload)
        if raw not in {encoded, encoded + b"\n", encoded + b"\r\n"}:
            raise ValueError("noncanonical bridge result")
        terminal = BridgeTerminalResultV1.model_validate(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("BRIDGE_RESULT_INVALID") from error
    if (
        terminal.run_manifest_digest != manifest_digest
        or terminal.problem_id != problem_id
        or terminal.target != target
        or terminal.source_run_digest != source_run_digest
        or terminal.source_terminal_commitment_ref
        != source_terminal_commitment_ref
    ):
        raise ValueError("BRIDGE_RESULT_AUTHORITY_MISMATCH")
    return terminal

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
        source_terminal_commitment_ref: str | None,
        recovery: bool = False,
        recovery_completion_assertion=None,
    ) -> None:
        self.harness = harness
        self.evidence_pack = evidence_pack
        self.catalog = catalog
        self.manifest_digest = manifest_digest
        self.problem_id = problem_id
        self.target = target
        self.source_terminal_commitment_ref = source_terminal_commitment_ref
        self._recovery = recovery
        self._pack_written = False
        self._recovery_completion_assertion = recovery_completion_assertion
        self.failure: BridgeFailureV1 | None = None

    def _already_persisted(
        self,
        batch: BridgePersistenceBatch,
        *,
        inputs: tuple[str, ...],
        records: list[tuple[str, object]],
    ) -> bool:
        if not getattr(self, "_recovery", False):
            return False
        log = getattr(self.harness, "log", None)
        if log is None:
            return False
        output_ids = tuple(
            ObjectStore._record(schema, record)["id"] for schema, record in records
        )
        actor = getattr(batch.actor, "value", batch.actor)
        for event in log.read():
            payload = event.bridge
            if payload is None:
                continue
            if (
                payload.action == batch.action
                and payload.actor.value == actor
                and tuple(event.inputs) == inputs
                and tuple(event.outputs) == output_ids
                and payload.finding_ref == batch.finding_ref
                and payload.error_code == batch.error_code
            ):
                return True
        return False

    def persist_bridge_batch(self, batch: BridgePersistenceBatch) -> None:
        records = list(batch.records)
        if batch.action == BridgeAction.COMPLETED and getattr(self, "_recovery", False):
            assertion = getattr(self, "_recovery_completion_assertion", None)
            if assertion is not None:
                assertion()
        # Controller-v3 provider results already own the sole canonical LLM
        # receipt.  Keep the call on BridgeWorkflowResultV1 for accounting,
        # but never append the same authorized dispatch a second time through
        # its semantic bridge event.  Legacy calls have no authorization ref.
        persisted_llm = batch.llm
        event_inputs = tuple(batch.inputs)
        if (
            self.source_terminal_commitment_ref is not None
            and batch.action != BridgeAction.FAILED
            and self.source_terminal_commitment_ref not in event_inputs
        ):
            event_inputs += (self.source_terminal_commitment_ref,)
        if getattr(persisted_llm, "dispatch_authorization_ref", None) is not None:
            persisted_llm = None
            if batch.action not in {BridgeAction.FAILED, BridgeAction.COMPLETED}:
                work_id = batch.llm.work_order_id
                if work_id not in event_inputs:
                    event_inputs += (work_id,)
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
        if self._already_persisted(batch, inputs=event_inputs, records=records):
            return
        self.harness.record_bridge_event(
            batch.action,
            actor=batch.actor,
            inputs=event_inputs,
            records=records,
            llm=persisted_llm,
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
    if manifest.schema_version not in {3, 4, 5, 6} or scratch is None or not scratch.enabled:
        raise ValueError("BRIDGE_SCRATCH_MANIFEST_V3_REQUIRED")
    return scratch.attention_policy()


def _derive_bridge_execution_policy(manifest, supplied_policy):
    """Purely derive effective bridge authority from one immutable manifest."""

    supplied = BridgeWorkflowPolicy.model_validate(supplied_policy)
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
        "bridge.ledger.v3": "v3",
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


def preflight_bound_bridge_policy(*, policy, run_manifest):
    """Validate and derive bridge authority without mutating runtime state."""

    effective, _retry, _lease = _derive_bridge_execution_policy(
        run_manifest,
        policy,
    )
    return effective


def _bound_bridge_execution(
    root,
    manifest_digest: str,
    supplied_policy,
    *,
    transactional_manifest_required: bool = False,
):
    """Resolve the sole v4 contract/retry authority from the bound manifest.

    A missing or historical manifest preserves the original low-level fixture
    path exactly.  For v4, callers may supply only the bridge-policy projection;
    the control plane owns the wire contract and whole-workflow retry ceiling.
    """

    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    path = root / MANIFEST_NAME
    try:
        path.lstat()
    except FileNotFoundError:
        if transactional_manifest_required:
            raise ValueError("BRIDGE_MANIFEST_MISMATCH")
        supplied = BridgeWorkflowPolicy.model_validate(supplied_policy)
        return supplied, WorkflowRetryPolicyV1(), None
    manifest = load_run_manifest(path)
    if manifest.sha256 != manifest_digest:
        raise ValueError("BRIDGE_MANIFEST_MISMATCH")
    from deepreason.runtime.launch_policy import require_v6_launch_allowed

    require_v6_launch_allowed(manifest, operation="grounded bridge")
    return _derive_bridge_execution_policy(manifest, supplied_policy)


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
        source_terminal_commitment_ref=(
            evidence_pack.source_terminal_commitment_ref
        ),
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
    transactional_manifest_required = _transactional_v6_manifest_required(
        stage_a_adapter,
        composition_adapter,
        review_adapter,
        repair_adapter,
    )
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
        harness.root,
        manifest_digest,
        policy,
        transactional_manifest_required=transactional_manifest_required,
    )
    composition_request = CompositionRequestV1(
        output_target=target,
        formatting_profile=formatting_profile,
        desired_length_chars=desired_length_chars,
        maximum_sections=maximum_sections,
    )
    active_adapters = tuple(
        adapter
        for adapter in (
            stage_a_adapter,
            composition_adapter or stage_a_adapter,
            review_adapter if workflow_policy.grounding_review else None,
            repair_adapter
            if workflow_policy.grounding_review
            and workflow_policy.max_grounding_repair_attempts
            else None,
        )
        if adapter is not None
    )
    transactional_adapters = _transactional_bridge_adapters(*active_adapters)
    source_terminal_commitment_ref = (
        _transactional_source_terminal_commitment_ref(*active_adapters)
    )
    if transactional_adapters:
        from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
        from deepreason.runtime.terminal_authority import derive_terminal_authority
        from deepreason.verification.report import verify_root_report

        bound_manifest = load_run_manifest(harness.root / MANIFEST_NAME)
        authority = derive_terminal_authority(
            harness.root,
            manifest=bound_manifest,
        )
        if (
            not authority.current_valid
            or authority.terminal_commitment_ref
            != source_terminal_commitment_ref
        ):
            raise ValueError("BRIDGE_TERMINAL_AUTHORITY_MISMATCH")
        if (
            authority.terminal_status != "completed"
            or authority.canonical_bridge_eligible is not True
        ):
            raise ValueError("BRIDGE_TERMINAL_OUTCOME_INELIGIBLE")
        verification = verify_root_report(harness.root)
        if not verification.integrity_valid or not verification.security_valid:
            raise ValueError("BRIDGE_ROOT_AUTHORITY_INVALID")
        terminal = _read_existing_bridge_terminal(
            harness,
            manifest_digest=manifest_digest,
            problem_id=problem_id,
            target=target,
            source_run_digest=source_run_digest,
            source_terminal_commitment_ref=source_terminal_commitment_ref,
        )
        if terminal is not None:
            return terminal
        recovery_snapshot = _find_bridge_execution_snapshot(
            harness,
            manifest_digest,
            source_terminal_commitment_ref,
        )
    else:
        recovery_snapshot = None
    recovery = recovery_snapshot is not None

    scratch_service = None
    context = None
    if recovery:
        if len(transactional_adapters) != len({id(adapter) for adapter in active_adapters}):
            raise ValueError("BRIDGE_RECOVERY_ADAPTER_REQUIRED")
        assert recovery_snapshot is not None
        _assert_snapshot_matches_invocation(
            recovery_snapshot,
            problem_id=problem_id,
            target=target,
            source_run_digest=source_run_digest,
            source_terminal_commitment_ref=source_terminal_commitment_ref,
            evidence_budget_chars=evidence_budget_chars,
            attention_pack=attention_pack,
            composition_request=composition_request,
            workflow_policy=workflow_policy,
        )
        formal_seq = recovery_snapshot.formal_seq
        evidence_pack = recovery_snapshot.evidence_pack
        catalog = recovery_snapshot.catalog
        composition_request = recovery_snapshot.composition_request
    else:
        if attention_pack is not None:
            scratch_service = ScratchService(harness)
            context = scratch_service.prepare_advisory_context(attention_pack)
        formal_seq = source._next_seq - 1
        frozen = (
            _verified_source_view(source, sealed_refs=source_sealed_blob_refs)
            if derived
            else harness.at(harness.root, formal_seq)
        )
        if derived:
            try:
                evidence_pack = assemble_evidence_pack(
                    frozen,
                    problem_id,
                    budget_chars=evidence_budget_chars,
                    formal_seq=formal_seq,
                    source_run_digest=source_run_digest,
                    source_terminal_commitment_ref=(
                        source_terminal_commitment_ref
                    ),
                    catalog_version=(
                        "v3"
                        if workflow_policy.ledger_contract_version == "v3"
                        else "v1"
                    ),
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
                source_terminal_commitment_ref=(
                    source_terminal_commitment_ref
                ),
                catalog_version=(
                    "v3"
                    if workflow_policy.ledger_contract_version == "v3"
                    else "v1"
                ),
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
        if context is not None:
            assert scratch_service is not None
            committed = scratch_service.commit_prepared_advisory_context(
                attention_pack,
                context,
                context_ref=evidence_pack.id,
                coverage_policy=attention_policy,
            )
            if committed != context:
                raise RuntimeError(
                    "committed advisory context differs from prepared context"
                )
        if transactional_adapters:
            recovery_snapshot = _write_bridge_execution_snapshot(
                harness,
                manifest_digest=manifest_digest,
                formal_seq=formal_seq,
                problem_id=problem_id,
                target=target,
                source_run_digest=source_run_digest,
                source_terminal_commitment_ref=(
                    source_terminal_commitment_ref
                ),
                evidence_budget_chars=evidence_budget_chars,
                attention_pack=attention_pack,
                advisory_context=context,
                evidence_pack=evidence_pack,
                catalog=catalog,
                composition_request=composition_request,
                workflow_policy=workflow_policy,
            )

    # Review receives exact excerpts from this closed, harness-authored catalog.
    # Scratch excerpts are deliberately omitted: provenance cannot ground a span.
    materials = {
        item.ref: item.excerpt for item in catalog.items if item.kind != "scratch"
    }
    source_formal_before = source.state.model_dump_json()
    source_commitments_before = dict(source.commitments)
    source_warrants_before = dict(source.warrants)
    sink_formal_before = harness.state.model_dump_json()
    sink_commitments_before = dict(harness.commitments)
    sink_warrants_before = dict(harness.warrants)
    if recovery_snapshot is not None:
        for adapter in transactional_adapters:
            adapter.bind_bridge_execution(
                execution_id=recovery_snapshot.execution_id,
                execution_snapshot_ref=recovery_snapshot.snapshot_ref,
                formal_fence_seq=recovery_snapshot.formal_seq,
                recovery=recovery,
            )
    sinks: list[_HarnessBridgeSink] = []

    def assert_recovery_complete() -> None:
        for adapter in transactional_adapters:
            assertion = getattr(adapter, "assert_recovery_complete", None)
            if callable(assertion):
                assertion()

    def workflow_factory(_attempt_number: int):
        sink = _HarnessBridgeSink(
            harness,
            evidence_pack,
            catalog,
            manifest_digest=manifest_digest,
            problem_id=problem_id,
            target=target,
            source_terminal_commitment_ref=(
                source_terminal_commitment_ref
            ),
            recovery=recovery,
            recovery_completion_assertion=(
                assert_recovery_complete if recovery else None
            ),
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

        contract_id = {
            "v1": "bridge.claim-ledger.compact.v1",
            "v2": "bridge.claim-ledger.compact.v2",
            "v3": "bridge.ledger.v3",
        }[workflow_policy.ledger_contract_version]
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
            records = [("bridge-workflow-retry", receipt)]
            retry_inputs = (receipt.prior_failure_id,)
            if source_terminal_commitment_ref is not None:
                retry_inputs += (source_terminal_commitment_ref,)
            batch = BridgePersistenceBatch(
                action=BridgeAction.WORKFLOW_RETRY_STARTED,
                inputs=retry_inputs,
                records=tuple(records),
            )
            if sinks[-1]._already_persisted(
                batch, inputs=batch.inputs, records=records
            ):
                return
            harness.record_bridge_event(
                BridgeAction.WORKFLOW_RETRY_STARTED,
                inputs=list(retry_inputs),
                records=records,
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
            "source_terminal_commitment_ref": (
                terminal.source_terminal_commitment_ref
            ),
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
    "preflight_bound_bridge_policy",
]
