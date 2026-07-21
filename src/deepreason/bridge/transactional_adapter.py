"""RunManifest-v6 authorization for canonical bridge model calls.

The bridge workflow deliberately remains unaware of controller mechanics.  This
adapter decorates its ordinary :class:`LLMAdapter` only for v6 runs: each call
gets a durable preparation, a call-local context plan, one atomic issue event,
and a typed provider/admission/terminal sequence.  Earlier manifests continue
to receive the undecorated adapter.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from threading import Lock
from typing import Any

from pydantic import BaseModel

from deepreason.canonical import canonical_json
from deepreason.llm.budget import TokenMeter
from deepreason.llm.adapter import (
    V6ModelProfileOverrideForbidden,
    WorkflowAuthorizationError,
)
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.firewall import (
    leases_from_manifest,
    reject_model_control_fields,
    route_fingerprint,
    select_lease,
)
from deepreason.llm.repair import SchemaRepairError, parse_one_json_value
from deepreason.llm.profiles import get_profile
from deepreason.run_manifest import resolve_route_seat_base_profile
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction import (
    ContextNamespace,
    VisibleContextItemV1,
    WorkBudgetDenied,
)
from deepreason.workflow.transaction_service import InquiryTransactionService


_TEMPLATE_TASKS = {
    "bridge_ledger": WorkflowTaskKind.BRIDGE_LEDGER,
    "bridge_compose": WorkflowTaskKind.BRIDGE_COMPOSITION,
    "bridge_review": WorkflowTaskKind.BRIDGE_REVIEW,
    "bridge_grounding_repair": WorkflowTaskKind.REPAIR,
}
_EXACT_V6_CONTRACTS = {
    "bridge_ledger": {"bridge.ledger.v3", "bridge.ledger-batch.v1"},
    "bridge_compose": {
        "bridge.composition.v2",
        "bridge.composition-batch.v1",
    },
}
_BRIDGE_TRANSACTION_SCHEMA_V2 = "bridge.transaction-task.v2"


class BridgeRecoveryError(RuntimeError):
    """A saved bridge provider result cannot safely resume normal work."""

    def __init__(self, code: str, message: str, *, spend=None) -> None:
        self.code = code
        self.spend = spend
        super().__init__(message)


def _require_durable_model_classification(harness, manifest, qualification) -> None:
    """Purely match durable classification to the validated doctor report."""

    from deepreason.workflow.transaction import (
        ModelClassificationBindingV1,
        RouteSeatModelClassificationPlanV1,
    )

    expected = qualification.route_seat_model_classification
    state = harness.workflow_state
    current = state.route_seat_model_classification
    binding = state.model_classification_binding
    event_seq = state.model_classification_event_seq
    if (
        not isinstance(expected, RouteSeatModelClassificationPlanV1)
        or not isinstance(current, RouteSeatModelClassificationPlanV1)
        or not isinstance(binding, ModelClassificationBindingV1)
        or event_seq is None
    ):
        raise WorkflowAuthorizationError(
            "BRIDGE_MODEL_CLASSIFICATION_REQUIRED"
        )
    try:
        state._validate_model_classification(manifest, current)
    except ValueError as error:
        raise WorkflowAuthorizationError(
            "BRIDGE_MODEL_CLASSIFICATION_MISMATCH"
        ) from error
    if (
        current != expected
        or binding.manifest_digest != manifest.sha256
        or binding.classification_plan_ref != current.id
        or binding.algorithm != current.algorithm
        or binding.algorithm_version != current.algorithm_version
        or binding.qualification_evidence_sha256
        != current.qualification_evidence_sha256
    ):
        raise WorkflowAuthorizationError(
            "BRIDGE_MODEL_CLASSIFICATION_MISMATCH"
        )


def _semantic_bytes(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", by_alias=True, exclude_none=True)
    return canonical_json(value)


def _namespace_for(*, handle: str | None = None, kind: str | None = None):
    prefix = (handle or "").split("_", 1)[0]
    if kind == "scratch" or prefix == "SCR":
        return ContextNamespace.SCRATCH
    if kind == "simulation" or prefix == "SIM":
        return ContextNamespace.SIMULATION
    return ContextNamespace.SOURCE


def _context_seeds(contract, pack: str):
    """Return the immutable objects visibly represented by one bridge pack."""

    seeds: list[tuple[ContextNamespace, str, bytes]] = []
    wire_items = getattr(contract, "_wire_items", None)
    if isinstance(wire_items, Mapping):
        for handle, item in wire_items.items():
            seeds.append(
                (
                    _namespace_for(handle=str(handle), kind=str(item.kind)),
                    str(item.ref),
                    str(item.excerpt).encode("utf-8"),
                )
            )

    # Amendments expose bounded prior entries in addition to the current
    # catalog; composition contracts expose their ledger entries here.
    for mapping_name in ("prior_entry_keys", "prior_conflict_keys"):
        mapping = getattr(contract, mapping_name, None)
        if isinstance(mapping, Mapping):
            for handle, target in mapping.items():
                seeds.append(
                    (
                        _namespace_for(handle=str(handle)),
                        str(target),
                        str(target).encode("utf-8"),
                    )
                )
    aliases = getattr(getattr(contract, "aliases", None), "aliases", None)
    if isinstance(aliases, Mapping):
        for handle, target in aliases.items():
            seeds.append(
                (
                    _namespace_for(handle=str(handle)),
                    str(target),
                    str(target).encode("utf-8"),
                )
            )

    if not seeds:
        # Direct review and repair contracts have no reference catalog.  Bind
        # the exact rendered pack as one content-addressed context object.
        content = pack.encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        seeds.append((ContextNamespace.SOURCE, digest, content))

    unique: list[tuple[ContextNamespace, str, bytes]] = []
    namespaces_by_ref: dict[str, ContextNamespace] = {}
    for namespace, object_ref, content in seeds:
        prior = namespaces_by_ref.get(object_ref)
        if prior is not None:
            if prior != namespace:
                raise ValueError("one bridge context reference occupies incompatible namespaces")
            continue
        namespaces_by_ref[object_ref] = namespace
        unique.append((namespace, object_ref, content))
    return tuple(unique)


def _context_items(harness, contract, pack: str):
    seeds = _context_seeds(contract, pack)
    counters = {namespace: 0 for namespace in ContextNamespace}
    prefixes = {
        ContextNamespace.SOURCE: "SRC",
        ContextNamespace.SIMULATION: "SIM",
        ContextNamespace.SCRATCH: "SCR",
    }
    rendered_bytes = len(pack.encode("utf-8"))
    items = []
    for index, (namespace, object_ref, content) in enumerate(seeds):
        counters[namespace] += 1
        if len(object_ref) > 512:
            raise ValueError("bridge context reference exceeds transaction limit")
        # Direct packs use their raw digest as the object reference; make the
        # corresponding bytes reachable without assigning them formal status.
        if object_ref == hashlib.sha256(content).hexdigest():
            object_ref = harness.blobs.put(content)
        items.append(
            VisibleContextItemV1(
                namespace=namespace,
                alias=f"{prefixes[namespace]}_{counters[namespace]:03d}",
                object_ref=object_ref,
                content_sha256=hashlib.sha256(content).hexdigest(),
                planned_bytes=(rendered_bytes if index == 0 else 0),
            )
        )
    return tuple(items), rendered_bytes


class TransactionalBridgeAdapter:
    """v6-only bridge adapter that owns one transaction per model call."""

    def __init__(
        self,
        adapter,
        harness,
        manifest,
        *,
        source_terminal_commitment_ref: str | None = None,
    ) -> None:
        from deepreason.runtime.launch_policy import (
            BOUND_RUN_MANIFEST_REQUIRED,
            require_v6_launch_allowed,
            require_v6_production_qualification,
            resolve_effective_run_manifest,
        )
        from deepreason.run_manifest import RunManifestError

        operation = "standalone transactional grounded bridge"
        try:
            manifest = resolve_effective_run_manifest(
                manifest,
                root=getattr(harness, "root", None),
                operation=operation,
                require_bound_manifest=True,
            )
        except RunManifestError as error:
            if error.code == BOUND_RUN_MANIFEST_REQUIRED:
                raise ValueError("BRIDGE_MANIFEST_MISMATCH") from error
            raise
        if manifest is None:
            raise ValueError("transactional bridge adapter requires RunManifest v6")
        if manifest.schema_version != 6:
            raise ValueError("transactional bridge adapter requires RunManifest v6")
        require_v6_launch_allowed(manifest, operation=operation)
        qualification = require_v6_production_qualification(
            manifest,
            root=getattr(harness, "root", None),
            operation=operation,
        )
        from deepreason.runtime.terminal_authority import derive_terminal_authority

        terminal_authority = derive_terminal_authority(
            harness.root,
            manifest=manifest,
        )
        if not terminal_authority.current_valid:
            raise ValueError("BRIDGE_TERMINAL_AUTHORITY_INVALID")
        if (
            terminal_authority.terminal_status != "completed"
            or terminal_authority.canonical_bridge_eligible is not True
        ):
            raise ValueError("BRIDGE_TERMINAL_OUTCOME_INELIGIBLE")
        from deepreason.verification.report import verify_root_report

        verification = verify_root_report(harness.root)
        if not verification.integrity_valid or not verification.security_valid:
            raise ValueError("BRIDGE_ROOT_AUTHORITY_INVALID")
        if (
            source_terminal_commitment_ref is not None
            and source_terminal_commitment_ref
            != terminal_authority.terminal_commitment_ref
        ):
            raise ValueError("BRIDGE_TERMINAL_AUTHORITY_MISMATCH")
        source_terminal_commitment_ref = (
            terminal_authority.terminal_commitment_ref
        )
        versions = manifest.control_plane_policy.contract_versions
        if (
            versions.bridge_ledger_wire_contract != "bridge.ledger.v3"
            or versions.bridge_composition_contract != "bridge.composition.v2"
        ):
            raise ValueError("v6 bridge adapter requires the frozen v3/v2 contract pair")
        if adapter.base_model_profile != manifest.model_profile:
            raise WorkflowAuthorizationError(
                "adapter presentation identity differs from the manifest"
            )
        if adapter.leases != leases_from_manifest(manifest):
            raise WorkflowAuthorizationError(
                "adapter route leases differ from the manifest"
            )
        if (
            adapter._v6_authority_harness is not None
            and adapter._v6_authority_harness is not harness
        ):
            raise WorkflowAuthorizationError(
                "transactional adapter is already bound to another harness"
            )
        if (
            adapter._v6_authority_manifest is not None
            and adapter._v6_authority_manifest.sha256 != manifest.sha256
        ):
            raise WorkflowAuthorizationError(
                "transactional adapter is already bound to another manifest"
            )
        harness_manifest = getattr(harness, "_workflow_manifest", None)
        if (
            harness_manifest is not None
            and harness_manifest.sha256 != manifest.sha256
        ):
            raise WorkflowAuthorizationError(
                "transaction manifest differs from bound root authority"
            )
        replay_state = harness.workflow_state
        replay_manifest = getattr(replay_state, "_run_manifest", None)
        if (
            replay_manifest is not None
            and replay_manifest.sha256 != manifest.sha256
        ):
            raise WorkflowAuthorizationError(
                "workflow replay is already bound to another manifest"
            )
        if any(
            item.preparation.manifest_digest != manifest.sha256
            for item in replay_state.transaction_work.values()
        ):
            raise WorkflowAuthorizationError(
                "transaction history belongs to another manifest"
            )
        _require_durable_model_classification(harness, manifest, qualification)
        self._adapter = adapter
        self.harness = harness
        self.manifest = manifest
        self.source_terminal_commitment_ref = source_terminal_commitment_ref
        self._adapter.transaction_authority_required = True
        self._adapter.bind_v6_authority(harness, manifest)
        self._ordinal = 0
        self._ordinal_lock = Lock()
        if self._adapter.meter is None:
            self._adapter.meter = TokenMeter()
        self._execution_id: str | None = None
        self._execution_snapshot_ref: str | None = None
        self._execution_formal_fence: int | None = None
        self._recovery_mode = False
        self._recovery_items = ()
        self._recovered_work_ids: set[str] = set()
        self._staged_calls = []
        self._pending_staged_transition = None

    def bind_bridge_execution(
        self,
        *,
        execution_id: str,
        execution_snapshot_ref: str,
        formal_fence_seq: int,
        recovery: bool,
    ) -> None:
        """Bind one harness-frozen bridge execution to later v6 work.

        The caller owns construction of the immutable execution snapshot.  This
        adapter only records its reference before issue and, on restart, uses
        it to select replayable provider work without touching a transport.
        """

        if not isinstance(execution_id, str) or not execution_id:
            raise ValueError("bridge execution requires a non-empty identity")
        if not isinstance(execution_snapshot_ref, str) or not execution_snapshot_ref:
            raise ValueError("bridge execution requires a snapshot reference")
        if type(formal_fence_seq) is not int or formal_fence_seq < 0:
            raise ValueError("bridge execution requires a non-negative formal fence")
        self._execution_id = execution_id
        self._execution_snapshot_ref = execution_snapshot_ref
        self._execution_formal_fence = formal_fence_seq
        self._recovery_mode = bool(recovery)
        self._recovery_items = self._execution_items() if self._recovery_mode else ()
        self._recovered_work_ids = set()
        self._ordinal = 0
        self._staged_calls = []
        self._pending_staged_transition = None

    def _execution_items(self):
        if self._execution_id is None:
            return ()
        items = []
        for item in self.harness.workflow_state.transaction_work.values():
            payload = item.preparation.task_payload_value
            if isinstance(payload, Mapping) and payload.get("execution_id") == self._execution_id and payload.get("schema") in {
                _BRIDGE_TRANSACTION_SCHEMA_V2,
                "contract-decomposition-child.v1",
            }:
                items.append((item, payload))
        return tuple(items)

    def __getattr__(self, name):
        return getattr(self._adapter, name)

    @property
    def meter(self):
        return self._adapter.meter

    @meter.setter
    def meter(self, value):
        self._adapter.meter = value

    def _next_ordinal(self) -> int:
        with self._ordinal_lock:
            value = self._ordinal
            self._ordinal += 1
            return value

    def _matching_recovery_item(self, payload):
        """Return one exact replay candidate or fail before a new issue."""

        if not self._recovery_mode:
            return None
        matches = []
        unconsumed = []
        for item, stored in self._recovery_items:
            if (
                stored.get("execution_snapshot_ref") != self._execution_snapshot_ref
                or item.preparation.manifest_digest != self.manifest.sha256
            ):
                raise BridgeRecoveryError(
                    "BRIDGE_RECOVERY_AUTHORITY_MISMATCH",
                    "stored bridge work names different execution authority",
                )
            stored_ordinal = stored.get("ordinal")
            if type(stored_ordinal) is not int or stored_ordinal < 0:
                raise BridgeRecoveryError(
                    "BRIDGE_RECOVERY_SEQUENCE_MISMATCH",
                    "stored bridge work has an invalid recovery ordinal",
                )
            if item.preparation.id in self._recovered_work_ids:
                continue
            unconsumed.append(item)
            if stored_ordinal != payload.get("ordinal"):
                continue
            if canonical_json(stored) != canonical_json(payload):
                raise BridgeRecoveryError(
                    "BRIDGE_RECOVERY_AUTHORITY_MISMATCH",
                    "stored bridge work differs from the reconstructed call",
                )
            matches.append(item)
        if len(matches) > 1:
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_AMBIGUOUS_WORK",
                "more than one stored bridge work matches one replay call",
            )
        if matches:
            return matches[0]
        if unconsumed:
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_SEQUENCE_MISMATCH",
                "stored bridge work is not an exact consumed recovery prefix",
            )
        return None

    def assert_recovery_complete(self) -> None:
        """Reject a successful bridge that leaves frozen v6 work unreplayed."""

        if not self._recovery_mode:
            return
        if any(
            item.preparation.id not in self._recovered_work_ids
            for item, _stored in self._recovery_items
        ):
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_SEQUENCE_MISMATCH",
                "stored bridge work remained unreplayed at bridge completion",
            )

    def _stored_provider_call(self, provider, *, role: str, lease, prompt_sha256: str):
        matches = []
        for event in self.harness.log.read():
            call = event.llm
            if (
                call is not None
                and call.work_order_id == provider.work_id
                and call.dispatch_authorization_ref == provider.authorization_bundle_ref
                and provider.id in event.outputs
            ):
                matches.append(call)
        if len(matches) != 1:
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_PROVIDER_RECEIPT_MISSING",
                "stored bridge provider result lacks one canonical call receipt",
            )
        call = matches[0]
        try:
            prompt_bytes = self.harness.blobs.get(call.prompt_ref)
        except (KeyError, OSError, TypeError) as error:
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_PROVIDER_RECEIPT_MISSING",
                "stored bridge provider receipt lacks its prompt bytes",
            ) from error
        if (
            call.role != role
            or call.model != lease.route.model_id
            or call.endpoint != lease.route.base_url
            or call.raw_ref != provider.raw_ref
            or hashlib.sha256(prompt_bytes).hexdigest() != prompt_sha256
        ):
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_AUTHORITY_MISMATCH",
                "stored bridge provider receipt differs from reconstructed authority",
            )
        return call

    @staticmethod
    def _provider_counts(provider):
        return provider.prompt_tokens, provider.completion_tokens

    def _terminate_unavailable_recovery(self, service, item, *, reason_code: str):
        preparation = item.preparation
        if item.issued:
            service.terminate(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                status="abandoned",
                reason_code=reason_code,
                usage_status="unknown",
            )
        else:
            service.terminate(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                status="abandoned",
                reason_code=reason_code,
                usage_status="exact",
                prompt_tokens=0,
                completion_tokens=0,
            )
        raise BridgeRecoveryError(
            "BRIDGE_RECOVERY_RESULT_INCOMPLETE",
            "stored bridge work has no durable provider result",
        )

    def _terminate_invalid_recovery(
        self,
        service,
        item,
        provider,
        *,
        reason_code: str,
    ) -> None:
        """Close an issued result that cannot safely be replayed."""

        if item.terminal is not None:
            return
        admission = item.admissions.get(item.preparation.attempt_index)
        if admission is None:
            diagnostic_ref = self.harness.blobs.put(
                canonical_json(
                    {
                        "schema": "bridge.recovery-diagnostic.v1",
                        "code": reason_code.upper(),
                    }
                )
            )
            admission = service.record_semantic_admission(
                provider,
                outcome="rejected",
                diagnostic_refs=(diagnostic_ref,),
            )
        if admission.outcome != "rejected":
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_ADMISSION_MISMATCH",
                "stored bridge admission prevents rejected recovery terminal",
            )
        prompt_tokens, completion_tokens = self._provider_counts(provider)
        service.terminate(
            work_id=item.preparation.id,
            attempt_index=item.preparation.attempt_index,
            status="rejected",
            reason_code=reason_code,
            usage_status=provider.usage_status,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            provider_attempt=provider,
            admission=admission,
        )

    def _recover_output(
        self,
        item,
        *,
        role: str,
        pack: str,
        output_model: type[BaseModel],
        endpoint_index: int,
        template_role: str,
        wire_contract,
        model_profile: str | None,
        aliases,
        lease,
        conjecture_context,
        route_ref,
        context_refs: tuple[str, ...],
    ):
        """Revalidate one persisted result without preparing or dispatching work."""

        preparation = item.preparation
        provider = item.provider_attempts.get(preparation.attempt_index)
        admission = item.admissions.get(preparation.attempt_index)
        terminal = item.terminal
        service = InquiryTransactionService(self.harness, self.manifest, self.meter)
        if (
            preparation.task_kind != _TEMPLATE_TASKS[template_role]
            or preparation.contract_id != wire_contract.contract_id
            or preparation.route_lease != route_ref
            or preparation.input_refs != context_refs
            or preparation.formal_fence_seq != self._execution_formal_fence
        ):
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_AUTHORITY_MISMATCH",
                "stored bridge work differs from its frozen call authority",
            )
        if provider is None:
            return self._terminate_unavailable_recovery(
                service,
                item,
                reason_code=(
                    "bridge_issued_result_unknown_recovery"
                    if item.issued
                    else "bridge_prepared_unissued_recovery"
                ),
            )
        if provider.outcome == "transport_failure":
            if terminal is None:
                service.terminate(
                    work_id=preparation.id,
                    attempt_index=preparation.attempt_index,
                    status="transport_failed",
                    reason_code="bridge_recovered_transport_failure",
                    usage_status=provider.usage_status,
                    prompt_tokens=provider.prompt_tokens,
                    completion_tokens=provider.completion_tokens,
                    provider_attempt=provider,
                )
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_TRANSPORT_FAILURE",
                "stored bridge provider transport failed",
            )
        if provider.outcome != "provider_result" or provider.raw_ref is None:
            self._terminate_invalid_recovery(
                service,
                item,
                provider,
                reason_code="bridge_recovery_provider_result_invalid",
            )
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_PROVIDER_RESULT_INVALID",
                "stored bridge provider outcome is not recoverable",
            )
        prompt, preview_contract, preview_lease, _maximum_tokens = (
            self._adapter.preview_request(
                role,
                pack,
                output_model,
                endpoint_index=endpoint_index,
                template_role=template_role,
                wire_contract=wire_contract,
                model_profile=model_profile,
                aliases=aliases,
                endpoint_lease=lease,
                conjecture_context=conjecture_context,
            )
        )
        if preview_contract is not wire_contract or preview_lease != lease:
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_AUTHORITY_MISMATCH",
                "bridge recovery preview changed frozen call authority",
            )
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if prompt_sha256 != provider.prompt_sha256:
            key = (
                route_ref.role,
                route_ref.seat,
                route_ref.endpoint_id,
                route_ref.route_sha256,
            )
            compact = self.harness.workflow_state.compact_recovery_by_route_seat.get(
                key
            )
            # The exhausted strong call necessarily predates the compact
            # transition that it triggered.  Reconstructing it from the live
            # sticky state would render the *later* compact presentation and
            # falsely reject its already-bound base-profile prompt.  The exact
            # task payload, route, contract, authorization bundle, stored prompt
            # bytes, and chronological source transition remain independently
            # replay-validated below.
            if not (
                terminal is not None
                and terminal.status == "schema_exhausted"
                and compact is not None
                and compact.work_id == preparation.id
                and compact.route_lease == route_ref
            ):
                raise BridgeRecoveryError(
                    "BRIDGE_RECOVERY_AUTHORITY_MISMATCH",
                    "stored provider result differs from the reconstructed request",
                )
            prompt_sha256 = provider.prompt_sha256
        if (
            provider.contract_id != wire_contract.contract_id
            or provider.route_lease != route_ref
        ):
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_AUTHORITY_MISMATCH",
                "stored provider result differs from the reconstructed request",
            )
        try:
            call = self._stored_provider_call(
                provider,
                role=role,
                lease=lease,
                prompt_sha256=prompt_sha256,
            )
        except BridgeRecoveryError:
            self._terminate_invalid_recovery(
                service,
                item,
                provider,
                reason_code="bridge_recovery_provider_receipt_invalid",
            )
            raise
        if terminal is not None and terminal.status == "schema_exhausted":
            if (
                admission is None
                or admission.outcome != "schema_exhausted"
                or terminal.provider_attempt_ref != provider.id
                or terminal.semantic_admission_ref != admission.id
            ):
                raise BridgeRecoveryError(
                    "BRIDGE_RECOVERY_TERMINAL_MISMATCH",
                    "stored schema exhaustion lacks its canonical terminal authority",
                    spend=call,
                )
            matching_failures = [
                failure
                for failure_id, failure in self.harness.bridge_state.failures.items()
                if any(
                    getattr(stored_call, "work_order_id", None) == preparation.id
                    for stored_call in self.harness.bridge_state.calls_by_failure.get(
                        failure_id, ()
                    )
                )
            ]
            if len(matching_failures) > 1:
                raise BridgeRecoveryError(
                    "BRIDGE_RECOVERY_SCHEMA_FAILURE_AMBIGUOUS",
                    "stored schema exhaustion maps to more than one bridge failure",
                    spend=call,
                )
            message = (
                matching_failures[0].error_message
                if matching_failures
                else "schema_exhausted: stored bridge provider result"
            )
            error = SchemaRepairError(message, spend=call)
            error.transaction_terminalized = True
            error.source_work_id = preparation.id
            raise error
        try:
            raw_bytes = self.harness.blobs.get(provider.raw_ref)
        except (KeyError, OSError, TypeError) as error:
            self._terminate_invalid_recovery(
                service,
                item,
                provider,
                reason_code="bridge_recovery_provider_result_invalid",
            )
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_PROVIDER_RESULT_INVALID",
                "stored bridge provider result lacks raw bytes",
                spend=call,
            ) from error
        try:
            raw = raw_bytes.decode("utf-8")
            raw_value = parse_one_json_value(raw).value
            reject_model_control_fields(raw_value)
            output = wire_contract.compile(wire_contract.validate_value(raw_value))
        except (TypeError, UnicodeDecodeError, ValueError) as error:
            diagnostic_ref = self.harness.blobs.put(
                canonical_json(
                    {
                        "schema": "bridge.recovery-diagnostic.v1",
                        "code": "BRIDGE_RECOVERY_SCHEMA_EXHAUSTED",
                        "error_type": type(error).__name__,
                    }
                )
            )
            if admission is None:
                admission = service.record_semantic_admission(
                    provider,
                    outcome="schema_exhausted",
                    diagnostic_refs=(diagnostic_ref,),
                )
            if terminal is None:
                prompt_tokens, completion_tokens = self._provider_counts(provider)
                service.terminate(
                    work_id=preparation.id,
                    attempt_index=preparation.attempt_index,
                    status="schema_exhausted",
                    reason_code="bridge_recovered_schema_exhausted",
                    usage_status=provider.usage_status,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    provider_attempt=provider,
                    admission=admission,
                )
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_SCHEMA_EXHAUSTED",
                "stored bridge provider result failed deterministic validation",
                spend=call,
            ) from error
        admitted_ref = self.harness.blobs.put(_semantic_bytes(output))
        if admission is None:
            admission = service.record_semantic_admission(
                provider,
                outcome="admitted",
                admitted_refs=(admitted_ref,),
            )
        elif admission.outcome != "admitted" or admission.admitted_refs != (admitted_ref,):
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_ADMISSION_MISMATCH",
                "stored bridge admission differs from deterministic output",
            )
        if terminal is None:
            prompt_tokens, completion_tokens = self._provider_counts(provider)
            service.terminate(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                status="completed",
                reason_code="bridge_output_recovered",
                usage_status=provider.usage_status,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                provider_attempt=provider,
                admission=admission,
            )
        elif (
            terminal.status != "completed"
            or terminal.provider_attempt_ref != provider.id
            or terminal.semantic_admission_ref != admission.id
        ):
            raise BridgeRecoveryError(
                "BRIDGE_RECOVERY_TERMINAL_MISMATCH",
                "stored bridge terminal differs from deterministic admission",
            )
        return output, call

    @staticmethod
    def _chunks(values, size: int = 8):
        values = tuple(values)
        return tuple(values[index : index + size] for index in range(0, len(values), size))

    def staged_ledger_fallback(self, error, catalog):
        """Execute exact catalog batches after durable strong-ledger exhaustion."""

        from deepreason.bridge.ledger import (
            ClaimLedgerBatchWireContractV1,
            ClaimLedgerInputCatalogV3,
            render_claim_ledger_stage_a_pack,
        )
        from deepreason.bridge.models import ClaimLedgerV1
        from deepreason.bridge.validate import validate_claim_ledger

        source_work_id = getattr(error, "source_work_id", None)
        if not isinstance(source_work_id, str):
            raise error
        item_chunks = self._chunks(catalog.items)
        batches = []
        if item_chunks:
            for index, items in enumerate(item_chunks):
                batches.append(
                    ClaimLedgerInputCatalogV3.create(
                        problem_ref=catalog.problem_ref,
                        formal_seq=catalog.formal_seq,
                        problem_text=catalog.problem_text,
                        output_target=catalog.output_target,
                        items=items,
                        process_observations=(
                            catalog.process_observations or () if index == 0 else ()
                        ),
                        advisory_context_ref=catalog.advisory_context_ref,
                        retrieval_receipt_ref=catalog.retrieval_receipt_ref,
                    )
                )
        elif catalog.process_observations:
            batches.append(
                ClaimLedgerInputCatalogV3.create(
                    problem_ref=catalog.problem_ref,
                    formal_seq=catalog.formal_seq,
                    problem_text=catalog.problem_text,
                    output_target=catalog.output_target,
                    items=(),
                    process_observations=catalog.process_observations,
                    advisory_context_ref=catalog.advisory_context_ref,
                    retrieval_receipt_ref=catalog.retrieval_receipt_ref,
                )
            )
        else:
            raise error
        contracts = tuple(ClaimLedgerBatchWireContractV1(batch) for batch in batches)
        packs = tuple(
            render_claim_ledger_stage_a_pack(batch, contract=contract)
            for batch, contract in zip(batches, contracts, strict=True)
        )
        child_contexts = tuple(
            (f"catalog-batch-{index:03d}", pack)
            for index, pack in enumerate(packs)
        )
        transition = self.harness.activate_contract_decomposition(
            self.manifest, source_work_id, child_contexts=child_contexts
        )
        ledgers = []
        calls = []
        for index, (batch, contract, pack) in enumerate(
            zip(batches, contracts, packs, strict=True)
        ):
            ledger, call = self.call(
                transition.route_lease.role,
                pack,
                ClaimLedgerV1,
                endpoint_index=transition.route_lease.seat,
                template_role="bridge_ledger",
                wire_contract=contract,
                _decomposition_transition=transition,
                _decomposition_child_index=index,
            )
            ledgers.append(ledger)
            calls.append(call)
        entries = tuple(dict.fromkeys(entry.id for ledger in ledgers for entry in ledger.entries))
        entry_by_id = {entry.id: entry for ledger in ledgers for entry in ledger.entries}
        uncovered_by_id = {
            value.id: value
            for ledger in ledgers
            for value in ledger.uncovered_requirements or ()
        }
        conflicts_by_id = {
            value.id: value
            for ledger in ledgers
            for value in ledger.source_conflicts or ()
        }
        merged = ClaimLedgerV1.create(
            problem_ref=catalog.problem_ref,
            formal_seq=catalog.formal_seq,
            output_target=catalog.output_target,
            entries=[entry_by_id[ref] for ref in entries],
            uncovered_requirements=list(uncovered_by_id.values()) or None,
            source_conflicts=list(conflicts_by_id.values()) or None,
            advisory_context_ref=catalog.advisory_context_ref,
            retrieval_receipt_ref=catalog.retrieval_receipt_ref,
        )
        if not validate_claim_ledger(merged).valid:
            raise ValueError("staged ledger merge failed canonical validation")
        self._staged_calls = calls
        self._pending_staged_transition = (transition, merged.id)
        return merged, calls[-1]

    def staged_composition_fallback(self, error, ledger, request):
        """Execute exact ledger batches after durable strong-composition exhaustion."""

        from deepreason.bridge.compose import (
            BridgeCompositionBatchWireContractV1,
            CompositionDraftV1,
            _composition_pack,
        )
        from deepreason.bridge.models import (
            BridgeOutputV1,
            BridgeResolution,
            ClaimLedgerV1,
            ClaimUseV1,
        )
        from deepreason.bridge.validate import validate_bridge_output

        source_work_id = getattr(error, "source_work_id", None)
        if not isinstance(source_work_id, str):
            raise error
        entry_chunks = self._chunks(ledger.entries)
        if not entry_chunks:
            raise error
        subledgers = tuple(
            ClaimLedgerV1.create(
                problem_ref=ledger.problem_ref,
                formal_seq=ledger.formal_seq,
                output_target=ledger.output_target,
                entries=chunk,
                advisory_context_ref=ledger.advisory_context_ref,
                retrieval_receipt_ref=ledger.retrieval_receipt_ref,
            )
            for chunk in entry_chunks
        )
        contracts = tuple(
            BridgeCompositionBatchWireContractV1(
                item,
                maximum_sections=min(request.maximum_sections, 8),
                desired_length_chars=request.desired_length_chars,
            )
            for item in subledgers
        )
        packs = tuple(
            _composition_pack(item, request, contract_version="v2")
            for item in subledgers
        )
        child_contexts = tuple(
            (f"ledger-batch-{index:03d}", pack)
            for index, pack in enumerate(packs)
        )
        transition = self.harness.activate_contract_decomposition(
            self.manifest, source_work_id, child_contexts=child_contexts
        )
        outputs = []
        calls = []
        for index, (contract, pack) in enumerate(zip(contracts, packs, strict=True)):
            draft, call = self.call(
                transition.route_lease.role,
                pack,
                CompositionDraftV1,
                endpoint_index=transition.route_lease.seat,
                template_role="bridge_compose",
                wire_contract=contract,
                _decomposition_transition=transition,
                _decomposition_child_index=index,
            )
            if draft.amendment_needed is not None or draft.output is None:
                raise ValueError("staged composition child requested unsupported amendment")
            outputs.append(draft.output)
            calls.append(call)
        sections = []
        for output in outputs:
            for section in output.sections:
                sections.append(
                    ClaimUseV1.create(
                        span_id=f"S{len(sections) + 1}",
                        text=section.text,
                        rendering_mode=section.rendering_mode,
                        ledger_entry_ids=section.ledger_entry_ids,
                    )
                )
        unresolved = [item for output in outputs for item in output.unresolved_items or ()]
        rank = {
            BridgeResolution.ANSWERED: 0,
            BridgeResolution.PARTIALLY_ANSWERED: 1,
            BridgeResolution.UNDERDETERMINED: 2,
            BridgeResolution.INSUFFICIENT_EVIDENCE: 3,
            BridgeResolution.CONFLICTING_EVIDENCE: 4,
            BridgeResolution.OUTSIDE_SCOPE: 5,
        }
        resolution = max((item.resolution for item in outputs), key=rank.__getitem__)
        reasons = tuple(
            dict.fromkeys(item.resolution_reason for item in outputs if item.resolution_reason)
        )
        merged = BridgeOutputV1.create(
            claim_ledger_id=ledger.id,
            sections=sections,
            unresolved_items=unresolved or None,
            resolution=resolution,
            resolution_reason="\n".join(reasons) or None,
        )
        report = validate_bridge_output(
            ledger, merged, allow_conservative_mixed_modes=True
        )
        if not report.valid:
            raise ValueError("staged composition merge failed canonical validation")
        self._staged_calls = calls
        self._pending_staged_transition = (transition, merged.id)
        return merged, calls[-1]

    def consume_staged_calls(self, fallback_call):
        calls = tuple(self._staged_calls) or ((fallback_call,) if fallback_call else ())
        self._staged_calls = []
        return calls

    def finalize_staged_effect(self, effect_ref: str) -> None:
        pending = self._pending_staged_transition
        if pending is None:
            return
        transition, expected_ref = pending
        if effect_ref != expected_ref:
            raise ValueError("staged bridge effect differs from deterministic merge")
        if not any(effect_ref in event.outputs for event in self.harness.log.read()):
            raise ValueError("staged bridge effect is not canonically reachable")
        marker = ["contract-decomposition-effect", transition.id, effect_ref]
        if not any(list(event.inputs) == marker for event in self.harness.log.read()):
            self.harness.record_measure(inputs=marker)
        self.harness.complete_contract_decomposition(
            self.manifest, transition, admitted_effect_refs=(effect_ref,)
        )
        self._pending_staged_transition = None

    def call(
        self,
        role: str,
        pack: str,
        output_model: type[BaseModel],
        endpoint_index: int = 0,
        template_role: str | None = None,
        images: list[bytes] | None = None,
        wire_contract=None,
        model_profile: str | None = None,
        aliases=None,
        output_mechanism=None,
        endpoint_lease=None,
        school_id: str | None = None,
        conjecture_context=None,
        _decomposition_transition=None,
        _decomposition_child_index: int | None = None,
        **authority,
    ):
        if authority:
            raise ValueError("bridge transaction authority is adapter-owned")
        if template_role not in _TEMPLATE_TASKS:
            raise ValueError("unrecognized canonical bridge model call")
        if wire_contract is None:
            raise ValueError("v6 bridge calls require an exact call-local contract")
        expected = _EXACT_V6_CONTRACTS.get(template_role)
        if expected is not None and wire_contract.contract_id not in expected:
            raise ValueError(
                f"{template_role} requires one frozen contract from {sorted(expected)}, "
                f"not {wire_contract.contract_id}"
            )
        is_smaller = wire_contract.contract_id in {
            "bridge.ledger-batch.v1",
            "bridge.composition-batch.v1",
        }
        if is_smaller != (_decomposition_transition is not None):
            raise ValueError("staged bridge contract requires exact decomposition authority")

        lease = endpoint_lease or select_lease(self._adapter.leases, role, endpoint_index)
        base_profile = resolve_route_seat_base_profile(
            self.manifest,
            role=role,
            seat=endpoint_index,
            endpoint_id=lease.route.endpoint_id,
        )
        if model_profile is not None:
            try:
                requested_profile = get_profile(model_profile).name.value
            except (KeyError, TypeError, ValueError) as error:
                raise V6ModelProfileOverrideForbidden(
                    role=role,
                    frozen_profile=base_profile,
                ) from error
            if requested_profile != base_profile:
                raise V6ModelProfileOverrideForbidden(
                    role=role,
                    frozen_profile=base_profile,
                )
        model_profile = base_profile
        route_ref = RouteLeaseRefV1(
            role=role,
            seat=endpoint_index,
            endpoint_id=lease.route.endpoint_id,
            route_sha256=route_fingerprint(lease.route),
        )
        ordinal = self._next_ordinal()
        pack_sha256 = hashlib.sha256(pack.encode("utf-8")).hexdigest()
        payload = {
            "schema": "bridge.transaction-task.v1",
            "ordinal": ordinal,
            "role": role,
            "seat": endpoint_index,
            "template_role": template_role,
            "contract_id": wire_contract.contract_id,
            "output_model": output_model.__name__,
            "pack_sha256": pack_sha256,
            "source_terminal_commitment_ref": (
                self.source_terminal_commitment_ref
            ),
        }
        if self._execution_id is not None:
            if (
                self._execution_snapshot_ref is None
                or self._execution_formal_fence is None
            ):
                raise RuntimeError("bridge execution binding is incomplete")
            payload = {
                **payload,
                "schema": _BRIDGE_TRANSACTION_SCHEMA_V2,
                "execution_id": self._execution_id,
                "execution_snapshot_ref": self._execution_snapshot_ref,
            }
        target_refs = ()
        if (
            wire_contract.contract_id == "bridge.ledger.v3"
            and (catalog := getattr(wire_contract, "catalog", None)) is not None
        ):
            count = max(1, (len(catalog.items) + 7) // 8)
            target_refs = tuple(f"catalog-batch-{index:03d}" for index in range(count))
        elif (
            wire_contract.contract_id == "bridge.composition.v2"
            and (ledger := getattr(wire_contract, "ledger", None)) is not None
        ):
            count = max(1, (len(ledger.entries) + 7) // 8)
            target_refs = tuple(f"ledger-batch-{index:03d}" for index in range(count))
        if target_refs:
            payload["decomposition_child_keys"] = list(target_refs)
        context_refs = tuple(
            object_ref for _namespace, object_ref, _content in _context_seeds(wire_contract, pack)
        )
        if _decomposition_transition is not None:
            transition = _decomposition_transition
            child_index = _decomposition_child_index
            if (
                transition.manifest_digest != self.manifest.sha256
                or transition.route_lease != route_ref
                or transition.atomic_contract_id != wire_contract.contract_id
                or type(child_index) is not int
                or not 0 <= child_index < len(transition.child_keys)
            ):
                raise ValueError("staged bridge child differs from decomposition authority")
            payload = {
                "schema": "contract-decomposition-child.v1",
                "decomposition_transition_ref": transition.id,
                "source_work_id": transition.source_work_id,
                "source_contract_id": transition.source_contract_id,
                "atomic_contract_id": transition.atomic_contract_id,
                "child_partition": transition.child_partition,
                "child_index": child_index,
                "child_count": len(transition.child_keys),
                "child_key": transition.child_keys[child_index],
                "execution_id": self._execution_id,
                "execution_snapshot_ref": self._execution_snapshot_ref,
                "ordinal": ordinal,
                "role": role,
                "seat": endpoint_index,
                "template_role": template_role,
                "contract_id": wire_contract.contract_id,
                "output_model": output_model.__name__,
                "pack_sha256": pack_sha256,
                "source_terminal_commitment_ref": (
                    self.source_terminal_commitment_ref
                ),
            }
            target_refs = (transition.child_keys[child_index],)
            context_refs = tuple(
                dict.fromkeys(
                    (
                        transition.id,
                        transition.source_work_id,
                        transition.child_context_refs[child_index],
                        *context_refs,
                    )
                )
            )
        recovery_item = self._matching_recovery_item(payload)
        if recovery_item is not None:
            try:
                recovered = self._recover_output(
                    recovery_item,
                    role=role,
                    pack=pack,
                    output_model=output_model,
                    endpoint_index=endpoint_index,
                    template_role=template_role,
                    wire_contract=wire_contract,
                    model_profile=model_profile,
                    aliases=aliases,
                    lease=lease,
                    conjecture_context=conjecture_context,
                    route_ref=route_ref,
                    context_refs=context_refs,
                )
            except SchemaRepairError:
                # A durable schema-exhausted terminal is a consumed ordinary
                # workflow result, not an unissued candidate for redispatch.
                self._recovered_work_ids.add(recovery_item.preparation.id)
                raise
            self._recovered_work_ids.add(recovery_item.preparation.id)
            return recovered
        trigger_ref = "bridge:" + hashlib.sha256(canonical_json(payload)).hexdigest()
        service = InquiryTransactionService(
            self.harness,
            self.manifest,
            self.meter,
        )
        fence = (
            self._execution_formal_fence
            if self._execution_formal_fence is not None
            else max(0, self.harness._next_seq - 1)
        )
        preparation = service.prepare(
            task_kind=_TEMPLATE_TASKS[template_role],
            attempt_index=0,
            route_lease=route_ref,
            contract_id=wire_contract.contract_id,
            trigger_ref=trigger_ref,
            formal_fence_seq=fence,
            scratch_fence_seq=fence,
            task_payload_value=payload,
            input_refs=context_refs,
            target_refs=target_refs,
            source_terminal_commitment_ref=(
                self.source_terminal_commitment_ref
            ),
        )
        authorized = None

        def abandon(*, issued: bool, reason_code: str) -> None:
            if authorized is not None and authorized.reservation.is_open:
                authorized.release()
            service.terminate(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                status="abandoned",
                reason_code=reason_code,
                usage_status=("unknown" if issued else "exact"),
                prompt_tokens=(None if issued else 0),
                completion_tokens=(None if issued else 0),
            )

        try:
            items, rendered_bytes = _context_items(self.harness, wire_contract, pack)
            namespaces = {item.namespace for item in items}
            plan_kind = (
                "scratch"
                if namespaces == {ContextNamespace.SCRATCH}
                else "simulation"
                if namespaces == {ContextNamespace.SIMULATION}
                else "dossier"
                if namespaces == {ContextNamespace.SOURCE}
                else "combined"
            )
            plan = service.context_plan(
                preparation,
                plan_kind=plan_kind,
                items=items,
                maximum_bytes=rendered_bytes,
                rendered_bytes=rendered_bytes,
            )
            prompt, preview_contract, preview_lease, maximum_tokens = self._adapter.preview_request(
                role,
                pack,
                output_model,
                endpoint_index=endpoint_index,
                template_role=template_role,
                wire_contract=wire_contract,
                model_profile=model_profile,
                aliases=aliases,
                endpoint_lease=lease,
                conjecture_context=conjecture_context,
            )
            if preview_contract is not wire_contract or preview_lease != lease:
                raise ValueError("bridge preview changed frozen call authority")
            authorized = service.issue(
                preparation,
                plans=(plan,),
                prompt=prompt,
                max_tokens=maximum_tokens,
            )
        except WorkBudgetDenied:
            raise
        except BaseException:
            abandon(issued=False, reason_code="bridge_preissue_failure")
            raise

        provider = None
        try:
            output, llm_call = self._adapter.call(
                role,
                pack,
                output_model,
                endpoint_index=endpoint_index,
                template_role=template_role,
                images=images,
                wire_contract=wire_contract,
                model_profile=model_profile,
                aliases=aliases,
                output_mechanism=output_mechanism,
                endpoint_lease=lease,
                school_id=school_id,
                conjecture_context=conjecture_context,
                dispatch_authorization=authorized,
            )
        except EndpointError as error:
            spend = getattr(error, "spend", None)
            if spend is None:
                abandon(
                    issued=True,
                    reason_code="bridge_transport_result_unknown",
                )
            else:
                diagnostic_ref = (
                    spend.attempt_trace[-1].diagnostic_ref
                    if spend.attempt_trace and spend.attempt_trace[-1].diagnostic_ref
                    else self.harness.blobs.put(str(error).encode("utf-8"))
                )
                provider = service.record_provider_attempt(
                    authorized,
                    call=spend,
                    outcome="transport_failure",
                    usage_status="unknown",
                    diagnostic_ref=diagnostic_ref,
                )
                service.terminate(
                    work_id=preparation.id,
                    attempt_index=preparation.attempt_index,
                    status="transport_failed",
                    reason_code="bridge_transport_failure",
                    usage_status="unknown",
                    provider_attempt=provider,
                )
            error.transaction_terminalized = True
            raise
        except SchemaRepairError as error:
            repaired = service.repair_schema_failure(
                adapter=self._adapter,
                authorized=authorized,
                error=error,
                role=role,
                pack=pack,
                output_model=output_model,
                wire_contract=wire_contract,
                endpoint_index=endpoint_index,
                template_role=template_role,
                model_profile=model_profile,
                output_mechanism=output_mechanism,
                endpoint_lease=lease,
                school_id=school_id,
                reason_prefix="bridge",
                preserve_terminalized_spend=True,
            )
            output = repaired.output
            llm_call = repaired.llm_call
            preparation = repaired.preparation
            authorized = repaired.authorized
            provider = repaired.provider_attempt
        except BaseException:
            abandon(issued=True, reason_code="bridge_dispatch_failure")
            raise

        if provider is None:
            provider = service.record_provider_attempt(
                authorized,
                call=llm_call,
                outcome="provider_result",
                usage_status="exact",
            )
        admitted_ref = self.harness.blobs.put(_semantic_bytes(output))
        admission = service.record_semantic_admission(
            provider,
            outcome="admitted",
            admitted_refs=(admitted_ref,),
        )
        service.terminate(
            work_id=preparation.id,
            attempt_index=preparation.attempt_index,
            status="completed",
            reason_code="bridge_output_admitted",
            usage_status="exact",
            prompt_tokens=llm_call.prompt_tokens,
            completion_tokens=llm_call.completion_tokens,
            provider_attempt=provider,
            admission=admission,
        )
        return output, llm_call


__all__ = ["BridgeRecoveryError", "TransactionalBridgeAdapter"]
