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
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.firewall import (
    reject_model_control_fields,
    route_fingerprint,
    select_lease,
)
from deepreason.llm.repair import SchemaRepairError, parse_one_json_value
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
    "bridge_ledger": "bridge.ledger.v3",
    "bridge_compose": "bridge.composition.v2",
}
_BRIDGE_TRANSACTION_SCHEMA_V2 = "bridge.transaction-task.v2"


class BridgeRecoveryError(RuntimeError):
    """A saved bridge provider result cannot safely resume normal work."""

    def __init__(self, code: str, message: str, *, spend=None) -> None:
        self.code = code
        self.spend = spend
        super().__init__(message)


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

    def __init__(self, adapter, harness, manifest) -> None:
        if manifest.schema_version != 6:
            raise ValueError("transactional bridge adapter requires RunManifest v6")
        versions = manifest.control_plane_policy.contract_versions
        if (
            versions.bridge_ledger_wire_contract != "bridge.ledger.v3"
            or versions.bridge_composition_contract != "bridge.composition.v2"
        ):
            raise ValueError("v6 bridge adapter requires the frozen v3/v2 contract pair")
        self._adapter = adapter
        self.harness = harness
        self.manifest = manifest
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

    def _execution_items(self):
        if self._execution_id is None:
            return ()
        items = []
        for item in self.harness.workflow_state.transaction_work.values():
            payload = item.preparation.task_payload_value
            if (
                isinstance(payload, Mapping)
                and payload.get("schema") == _BRIDGE_TRANSACTION_SCHEMA_V2
                and payload.get("execution_id") == self._execution_id
            ):
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
        if (
            provider.contract_id != wire_contract.contract_id
            or provider.route_lease != route_ref
            or provider.prompt_sha256 != prompt_sha256
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
        **authority,
    ):
        if authority:
            raise ValueError("bridge transaction authority is adapter-owned")
        if template_role not in _TEMPLATE_TASKS:
            raise ValueError("unrecognized canonical bridge model call")
        if wire_contract is None:
            raise ValueError("v6 bridge calls require an exact call-local contract")
        expected = _EXACT_V6_CONTRACTS.get(template_role)
        if expected is not None and wire_contract.contract_id != expected:
            raise ValueError(
                f"{template_role} requires frozen contract {expected}, "
                f"not {wire_contract.contract_id}"
            )

        lease = endpoint_lease or select_lease(self._adapter.leases, role, endpoint_index)
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
        context_refs = tuple(
            object_ref for _namespace, object_ref, _content in _context_seeds(wire_contract, pack)
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
                retry_max=(
                    self.manifest.bridge_policy.max_schema_repair_attempts
                    if self.manifest.bridge_policy is not None
                    else 2
                ),
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
