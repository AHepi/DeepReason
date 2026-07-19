"""Role -> endpoint routing (spec §9).

Every call stores the rendered prompt and the raw output as blobs and
returns an LLMCall record for the consuming event — replay consumes logged
raws (§0), so nothing downstream depends on live model behavior.
Schema-invalid output => feed the error back, RETRY_MAX bounded retries,
then SchemaRepairError (caller drops the cycle, logged).
"""

import json
import hashlib
import os
import re
import time
from collections.abc import Callable

from pydantic import BaseModel

from deepreason.llm.budget import TokenBudgetExceeded, conservative_prompt_bound
from deepreason.llm.endpoints import EndpointError, OpenAICompatEndpoint, resolve_model
from deepreason.llm.firewall import (
    EndpointLease,
    JudgeEnsemblePolicyError,
    ModelControlFieldError,
    RouteFirewallError,
    leases_from_endpoints,
    leases_from_manifest,
    reject_model_control_fields,
    require_cross_family_judge_ensemble,
    route_fingerprint,
    sanitize_model_control_fields_for_repair,
    select_lease,
)
from deepreason.llm.packs import AllocatedPack, apply_model_profile
from deepreason.llm.profiles import ModelProfile, get_profile
from deepreason.llm.repair import (
    BoundedRepairSession,
    OutputMechanism,
    SchemaRepairError,
    parse_one_json_value,
)
from deepreason.llm.roles import render_role_prompt
from deepreason.llm.wire import (
    AliasTable,
    DirectWireContract,
    WireContract,
    minimal_example,
    wire_contract_for,
)
from deepreason.ontology.event import (
    ConjectureContextCallReceiptV1,
    LLMAttempt,
    LLMCall,
    SchoolRouteReceiptV1,
)
from deepreason.run_manifest import infer_model_family


class WorkflowAuthorizationError(RuntimeError):
    """Active workflow authority could not be persisted before dispatch."""

    def __init__(self, message: str, *, spend: LLMCall | None = None) -> None:
        super().__init__(message)
        self.spend = spend


def _usage_tokens(usage: dict | None, request: str, raw: str) -> dict:
    """Normalize a provider usage block to prompt/completion token counts.

    Providers commonly omit one side or expose only ``total_tokens``.  Keep
    every reported side verbatim and estimate only the missing side.  A
    total-only report is split in proportion to the same deterministic text
    estimates, preserving the provider total whenever it can represent all
    non-empty sides.  In particular, missing never means zero merely because
    the usage object itself was truthy.
    """

    def estimate(text: str) -> int:
        return max(1, (len(text) + 3) // 4) if text else 0

    prompt_est = estimate(request)
    completion_est = estimate(raw)
    prompt = usage.get("prompt_tokens") if usage else None
    completion = usage.get("completion_tokens") if usage else None
    total = usage.get("total_tokens") if usage else None

    if prompt is not None or completion is not None:
        prompt_tokens = int(prompt) if prompt is not None else prompt_est
        completion_tokens = (
            int(completion) if completion is not None else completion_est
        )
        # Do not under-count a provider total when it is compatible with the
        # reported side.  Any required remainder belongs to the missing side;
        # reported prompt/completion values remain untouched.
        if total is not None and (prompt is None) != (completion is None):
            remainder = max(0, int(total) - prompt_tokens - completion_tokens)
            if prompt is None:
                prompt_tokens += remainder
            else:
                completion_tokens += remainder
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

    if total is not None:
        total_tokens = max(0, int(total))
        estimated_total = prompt_est + completion_est
        if estimated_total == 0:
            return {"prompt_tokens": total_tokens, "completion_tokens": 0}
        # Allocate by text-derived proportions while ensuring a non-empty
        # side is nonzero whenever the provider total makes that possible.
        nonempty_sides = int(prompt_est > 0) + int(completion_est > 0)
        if total_tokens < nonempty_sides:
            return {
                "prompt_tokens": prompt_est,
                "completion_tokens": completion_est,
            }
        prompt_tokens = round(total_tokens * prompt_est / estimated_total)
        if prompt_est:
            prompt_tokens = max(1, prompt_tokens)
        if completion_est:
            prompt_tokens = min(total_tokens - 1, prompt_tokens)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": total_tokens - prompt_tokens,
        }

    return {
        "prompt_tokens": prompt_est,
        "completion_tokens": completion_est,
    }


def _extract_json(raw: str) -> str:
    """Compatibility wrapper for callers that need normalized JSON text.

    The old helper sliced from the first ``{`` to the last ``}``, which could
    silently combine multiple values.  Keep the import surface while using
    W4's semantics-preserving single-value parser.
    """

    return parse_one_json_value(raw).text


class LLMAdapter:
    def __init__(
        self,
        endpoints: dict[str, object],
        blob_store,
        retry_max: int = 2,
        meter=None,
        model_profile: str | None = None,
        output_mechanism: str | OutputMechanism | None = None,
        leases: dict[str, tuple[EndpointLease, ...]] | None = None,
        transaction_authority_required: bool = False,
    ) -> None:
        self.endpoints = endpoints
        self.blobs = blob_store
        self.retry_max = retry_max
        self.meter = meter  # TokenMeter: hard provider-wide budget (llm/budget.py)
        # Immutable run-level presentation identity. Recovery state below may
        # select another wire transport for a later call, but never mutates
        # this value or the persisted RunManifest.
        self.base_model_profile = model_profile
        self.model_profile = model_profile
        self.output_mechanism = (
            OutputMechanism(output_mechanism) if output_mechanism else None
        )
        self.leases = leases if leases is not None else leases_from_endpoints(endpoints)
        self.transaction_authority_required = bool(transaction_authority_required)
        self._compact_recovery_roles: set[str] = set()

    def rehydrate_compact_recovery(self, process_events) -> frozenset[str]:
        """Restore later-call compact transport from durable process evidence.

        Recovery is intentionally derived only from harness-authored fields on
        a dropped, schema-exhausted direct call.  Prompt/raw contents and error
        prose are never inspected, so a model response cannot arm recovery.
        Route fingerprints and endpoint identities must still match the
        adapter's frozen leases; evidence from another route is irrelevant.

        The evidence arms the *next* ordinary call.  It does not issue a call,
        alter a lease, or add an attempt to the exhausted call.
        """

        if self.base_model_profile is None:
            return frozenset()
        base = get_profile(self.base_model_profile).name
        if base not in {ModelProfile.STANDARD, ModelProfile.FRONTIER}:
            return frozenset()

        recovered: set[str] = set()
        for event in process_events:
            inputs = list(getattr(event, "inputs", ()))
            call = getattr(event, "llm", None)
            if not inputs or inputs[0] != "dropped-call" or call is None:
                continue
            role = str(getattr(call, "role", ""))
            trace = list(getattr(call, "attempt_trace", ()))
            if role not in self.endpoints or not trace:
                continue
            # A transport failure, budget stop, successful generation, or
            # partial trace is not schema-repair exhaustion.
            if (
                len(trace) != int(getattr(call, "attempts", 0))
                or any(attempt.valid or attempt.usage_unknown for attempt in trace)
            ):
                continue
            seats = {int(attempt.seat) for attempt in trace}
            if len(seats) != 1:
                continue
            seat = seats.pop()
            try:
                lease = select_lease(self.leases, role, seat)
            except (KeyError, RouteFirewallError):
                continue
            fingerprint = route_fingerprint(lease.route)
            if (
                call.model != lease.route.model_id
                or call.endpoint != lease.route.base_url
            ):
                continue
            if not all(
                attempt.contract_id.endswith(".direct.v1")
                and attempt.model_profile == base.value
                and attempt.transport_profile == base.value
                and attempt.endpoint_id == lease.route.endpoint_id
                and attempt.route_sha256 == fingerprint
                and bool(attempt.raw_ref)
                and bool(attempt.diagnostic_ref)
                for attempt in trace
            ):
                continue
            recovered.add(role)

        self._compact_recovery_roles.update(recovered)
        return frozenset(recovered)

    def profile_for(self, role: str) -> str | None:
        """Effective transport profile for the next ordinary call to ``role``.

        Standard/frontier roles enter compact recovery only after a complete
        direct-contract call exhausts its bounded attempts. Compact runs stay
        compact, and unprofiled legacy adapters retain their existing direct
        behavior rather than acquiring an implicit policy.
        """

        if self.base_model_profile is None:
            return None
        base = get_profile(self.base_model_profile).name
        if role in self._compact_recovery_roles and base in {
            ModelProfile.STANDARD,
            ModelProfile.FRONTIER,
        }:
            return ModelProfile.COMPACT.value
        return base.value

    def _mark_compact_recovery(
        self,
        role: str,
        profile,
        wire_contract: WireContract,
    ) -> None:
        """Arm only a later call; never change transport inside this call."""

        if self.base_model_profile is None or profile is None:
            return
        base = get_profile(self.base_model_profile).name
        effective = get_profile(profile).name
        if (
            base in {ModelProfile.STANDARD, ModelProfile.FRONTIER}
            and effective in {ModelProfile.STANDARD, ModelProfile.FRONTIER}
            and wire_contract.variant == "direct"
        ):
            self._compact_recovery_roles.add(role)

    def has_role(self, role: str) -> bool:
        return role in self.endpoints

    def ensemble_size(self, role: str) -> int:
        entry = self.endpoints.get(role)
        return len(entry) if isinstance(entry, (list, tuple)) else (1 if entry else 0)

    def require_cross_family_judges(self) -> tuple[EndpointLease, ...]:
        """Preflight the frozen normative rubric ensemble and its bindings."""

        seats = require_cross_family_judge_ensemble(self.leases)
        configured = self.endpoints.get("judge")
        endpoints = (
            tuple(configured)
            if isinstance(configured, (list, tuple))
            else ((configured,) if configured is not None else ())
        )
        if len(endpoints) != len(seats):
            raise JudgeEnsemblePolicyError()
        # Verify the whole ensemble before seat zero can spend. This turns a
        # stale/mutated endpoint binding into a localized preflight failure,
        # rather than discovering it after a partial normative ruling.
        for lease, endpoint in zip(seats, endpoints, strict=True):
            lease.verify(endpoint)
        return seats

    def _resolve(self, role: str, index: int):
        entry = self.endpoints[role]
        if isinstance(entry, (list, tuple)):
            return entry[index]
        if index:
            raise KeyError(f"role {role!r} has no ensemble endpoint {index}")
        return entry

    def preview_request(
        self,
        role: str,
        pack: str,
        output_model: type[BaseModel],
        *,
        endpoint_index: int = 0,
        template_role: str | None = None,
        wire_contract: WireContract | None = None,
        model_profile: str | None = None,
        aliases: AliasTable | None = None,
        endpoint_lease: EndpointLease | None = None,
        conjecture_context: ConjectureContextCallReceiptV1 | None = None,
        pre_rendered_request: str | None = None,
    ) -> tuple[str, WireContract, EndpointLease, int]:
        """Render the exact first provider request without dispatching it.

        Transactional callers use this pure boundary to bind the prompt digest
        and conservative completion ceiling before WORK_ISSUED. call renders
        through the same helper and verifies the resulting digest, so preview
        and dispatch cannot silently drift.
        """

        prompt, contract, lease, endpoint, _profile = self._render_request(
            role,
            pack,
            output_model,
            endpoint_index=endpoint_index,
            template_role=template_role,
            wire_contract=wire_contract,
            model_profile=model_profile,
            aliases=aliases,
            endpoint_lease=endpoint_lease,
            conjecture_context=conjecture_context,
            pre_rendered_request=pre_rendered_request,
        )
        maximum = getattr(endpoint, "max_tokens", lease.route.max_tokens)
        return prompt, contract, lease, int(maximum or 0)

    def _render_request(
        self,
        role: str,
        pack: str,
        output_model: type[BaseModel],
        *,
        endpoint_index: int,
        template_role: str | None,
        wire_contract: WireContract | None,
        model_profile: str | None,
        aliases: AliasTable | None,
        endpoint_lease: EndpointLease | None,
        conjecture_context: ConjectureContextCallReceiptV1 | None,
        pre_rendered_request: str | None,
    ):
        """Resolve route, contract, presentation profile, and exact prompt."""

        if role not in self.endpoints:
            raise KeyError(f"no endpoint configured for role {role!r}")
        endpoint = self._resolve(role, endpoint_index)
        lease = endpoint_lease or select_lease(self.leases, role, endpoint_index)
        if lease.role != role or lease.seat != endpoint_index:
            raise ValueError(
                f"endpoint lease {lease.role}[{lease.seat}] cannot serve "
                f"{role}[{endpoint_index}]"
            )
        lease.verify(endpoint)
        profile = (
            model_profile if model_profile is not None else self.profile_for(role)
        )
        if wire_contract is None:
            wire_contract = (
                wire_contract_for(role, output_model, profile, aliases)
                if profile is not None
                else DirectWireContract(output_model)
            )
        if wire_contract.canonical_model is not output_model:
            raise TypeError(
                f"wire contract {wire_contract.contract_id} compiles to "
                f"{wire_contract.canonical_model.__name__}, expected {output_model.__name__}"
            )
        schema_value = wire_contract.model_json_schema()
        schema = json.dumps(schema_value, sort_keys=True)
        rendered_pack = pack
        pack_is_allocated = isinstance(pack, AllocatedPack)
        if (
            wire_contract.variant.startswith("compact")
            and wire_contract.aliases.aliases
        ):
            if conjecture_context is None:
                rendered_pack = wire_contract.aliases.render_pack(rendered_pack)
            else:
                protected = self.blobs.get(
                    conjecture_context.rendered_context_ref
                ).decode("utf-8")
                if rendered_pack.count(protected) != 1:
                    raise ValueError(
                        "advisory context bytes are absent or duplicated before aliasing"
                    )
                before, separator, after = rendered_pack.partition(protected)
                rendered_pack = (
                    wire_contract.aliases.render_pack(before)
                    + separator
                    + wire_contract.aliases.render_pack(after)
                )
        if profile is not None and not pack_is_allocated:
            rendered_pack = apply_model_profile(rendered_pack, profile)
        alias_labels = "\n".join(
            alias
            for alias in wire_contract.aliases.aliases
            if re.search(
                rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])",
                rendered_pack,
            )
        )
        if pre_rendered_request is not None:
            if not isinstance(pre_rendered_request, str) or not pre_rendered_request:
                raise ValueError("pre-rendered provider request must be nonempty text")
            prompt = pre_rendered_request
        else:
            prompt = render_role_prompt(
                template_role or role,
                schema=schema,
                pack=rendered_pack,
                profile=profile,
                example=minimal_example(wire_contract),
                aliases=alias_labels,
            )
        return prompt, wire_contract, lease, endpoint, profile

    def call(
        self,
        role: str,
        pack: str,
        output_model: type[BaseModel],
        endpoint_index: int = 0,
        template_role: str | None = None,
        images: list[bytes] | None = None,
        wire_contract: WireContract | None = None,
        model_profile: str | None = None,
        aliases: AliasTable | None = None,
        output_mechanism: str | OutputMechanism | None = None,
        endpoint_lease: EndpointLease | None = None,
        school_id: str | None = None,
        conjecture_context: ConjectureContextCallReceiptV1 | None = None,
        work_order_id: str | None = None,
        workflow_dispatch_observer: Callable[[int], str | None] | None = None,
        workflow_repair_observer: Callable[[LLMAttempt], None] | None = None,
        workflow_dispatch_required: bool = False,
        repair_scope_required: bool = False,
        dispatch_authorization=None,
        pre_rendered_request: str | None = None,
    ) -> tuple[BaseModel, LLMCall]:
        """endpoint_index selects within a role's ensemble (§9: the judge
        MUST run on >=2 endpoints from different families). template_role
        lets an auxiliary contract (e.g. spec generation) reuse a configured
        endpoint with a different prompt template. ``images`` (PNG bytes)
        makes the request multimodal (vision roles): image bytes are NOT
        duplicated into the log — callers pass content-addressed evidence
        artifacts and the pack text names their ids, so prompt_ref still
        honestly reconstructs the exchange (§0)."""
        if self.transaction_authority_required and dispatch_authorization is None:
            raise WorkflowAuthorizationError(
                "RunManifest v6 provider dispatch requires a bound transaction"
            )
        if role not in self.endpoints:
            raise KeyError(f"no endpoint configured for role {role!r}")
        if dispatch_authorization is not None:
            from deepreason.workflow.transaction import AuthorizedDispatch

            if not isinstance(dispatch_authorization, AuthorizedDispatch):
                raise TypeError("dispatch_authorization must be an AuthorizedDispatch")
            if work_order_id is not None or workflow_dispatch_observer is not None:
                raise ValueError(
                    "transactional authorization replaces legacy work callbacks"
                )
            work_order_id = dispatch_authorization.bundle.work_id
        elif pre_rendered_request is not None:
            raise ValueError(
                "pre-rendered requests require transactional dispatch authorization"
            )
        if work_order_id is not None and (
            (
                dispatch_authorization is None
                and role != "conjecturer"
            )
            or re.fullmatch(r"sha256:[0-9a-f]{64}", work_order_id) is None
        ):
            raise ValueError(
                "work_order_id requires canonical provider-work authority"
            )
        if workflow_dispatch_observer is not None and (
            role != "conjecturer" or work_order_id is not None
        ):
            raise ValueError(
                "workflow dispatch observation requires an unbound conjecturer call"
            )
        if workflow_repair_observer is not None and (
            role != "conjecturer" or workflow_dispatch_observer is None
        ):
            raise ValueError(
                "workflow repair observation requires conjecture dispatch observation"
            )
        if workflow_dispatch_required and workflow_dispatch_observer is None:
            raise ValueError(
                "required workflow dispatch needs an authorization callback"
            )
        if school_id is not None and endpoint_lease is None:
            raise ValueError("school-routed calls require an explicit endpoint lease")
        if conjecture_context is not None:
            conjecture_context = ConjectureContextCallReceiptV1.model_validate(
                conjecture_context
            )
            if role != "conjecturer":
                raise ValueError("only conjecturer calls accept advisory context")
            if school_id != conjecture_context.school_id:
                raise ValueError("school route and advisory context must name one school")
        prompt, wire_contract, lease, endpoint, profile = self._render_request(
            role,
            pack,
            output_model,
            endpoint_index=endpoint_index,
            template_role=template_role,
            wire_contract=wire_contract,
            model_profile=model_profile,
            aliases=aliases,
            endpoint_lease=endpoint_lease,
            conjecture_context=conjecture_context,
            pre_rendered_request=pre_rendered_request,
        )
        schema_value = wire_contract.model_json_schema()
        if dispatch_authorization is not None:
            from deepreason.workflow.models import RouteLeaseRefV1

            prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            route_ref = RouteLeaseRefV1(
                role=role,
                seat=endpoint_index,
                endpoint_id=lease.route.endpoint_id,
                route_sha256=route_fingerprint(lease.route),
            )
            dispatch_authorization.bundle.verify_dispatch(
                work_id=dispatch_authorization.preparation.id,
                attempt_index=dispatch_authorization.preparation.attempt_index,
                contract_id=wire_contract.contract_id,
                route_lease=route_ref,
                prompt_sha256=prompt_sha256,
                reservation_ref=dispatch_authorization.reservation_record.id,
            )
            if not dispatch_authorization.reservation.is_open:
                raise ValueError("transactional token reservation is no longer open")
        fixed_mechanism = OutputMechanism(lease.route.output_mechanism)
        requested_mechanism = (
            OutputMechanism(output_mechanism)
            if output_mechanism
            else self.output_mechanism
        )
        if requested_mechanism is not None and requested_mechanism != fixed_mechanism:
            raise ValueError(
                f"output mechanism is frozen by endpoint lease as "
                f"{fixed_mechanism.value!r}, not {requested_mechanism.value!r}"
            )
        mechanism = fixed_mechanism
        started = time.monotonic()
        tokens_used = 0
        exact_prompt_tokens = 0
        exact_completion_tokens = 0
        truncated_any = False
        raw_ref = ""
        prompt_ref = self.blobs.put(prompt.encode())
        attempt_trace: list[LLMAttempt] = []
        frozen_profile = (
            self.base_model_profile
            if self.base_model_profile is not None
            else profile
        )
        trace_identity = {
            "contract_id": wire_contract.contract_id,
            "endpoint_id": lease.route.endpoint_id,
            "route_sha256": route_fingerprint(lease.route),
            "seat": endpoint_index,
            # This is manifest/base process identity, not the effective wire
            # recovery path. A later direct -> compact scheduler cycle is
            # visible through contract_id without pretending the frozen run
            # profile mutated.
            "model_profile": str(
                getattr(frozen_profile, "value", frozen_profile) or ""
            ),
            "transport_profile": str(
                getattr(profile, "value", profile) or ""
            ),
        }
        school_route = (
            SchoolRouteReceiptV1(
                school_id=school_id,
                role=role,
                seat=endpoint_index,
                endpoint_id=lease.route.endpoint_id,
                route_sha256=trace_identity["route_sha256"],
                contract_id=wire_contract.contract_id,
            )
            if school_id is not None
            else None
        )
        repair = BoundedRepairSession(
            contract=wire_contract.contract_id,
            schema=schema_value,
            initial_request=prompt,
            # Each v6 patch attempt is separately prepared, reserved, issued,
            # and dispatched.  One authorization bundle can never silently
            # cover an internally generated repair request.
            retry_max=(0 if dispatch_authorization is not None else self.retry_max),
            enforce_scope=(
                workflow_dispatch_required
                or repair_scope_required
                or wire_contract.contract_id
                == "bridge.claim-ledger.compact.v2"
            ),
        )
        effective_work_order_id = work_order_id
        dispatch_authorization_ref = (
            dispatch_authorization.bundle.id
            if dispatch_authorization is not None
            else None
        )

        def _spend(attempts: int) -> LLMCall | None:
            if not tokens_used and not attempt_trace:
                return None
            return LLMCall(
                role=role,
                model=lease.route.model_id,
                endpoint=lease.route.base_url,
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                tokens=tokens_used,
                ms=int((time.monotonic() - started) * 1000),
                attempts=max(attempts, len(attempt_trace)),
                truncated=truncated_any,
                mean_surprisal=getattr(endpoint, "last_mean_surprisal", None),
                attempt_trace=attempt_trace,
                school_route=school_route,
                conjecture_context=conjecture_context,
                work_order_id=effective_work_order_id,
                dispatch_authorization_ref=dispatch_authorization_ref,
                prompt_tokens=(
                    exact_prompt_tokens if dispatch_authorization is not None else None
                ),
                completion_tokens=(
                    exact_completion_tokens if dispatch_authorization is not None else None
                ),
            )

        for attempt in range(repair.attempt_count):
            attempt_started = time.monotonic()
            if self.meter is not None and dispatch_authorization is None:
                try:
                    self.meter.check()  # hard stop BEFORE spending (llm/budget.py)
                except TokenBudgetExceeded as e:
                    # Exhaustion mid-retry: prior attempts already spent
                    # tokens that no LLMCall will carry — hand the caller
                    # the spend record (found live by the in-band
                    # accounting check: 833-token delta on first outing).
                    e.spend = _spend(attempt)
                    raise
            turn = repair.turn(attempt)
            request = turn.request
            response_schema = turn.response_schema
            # Re-check immediately before every provider request, including
            # both repair forms. A mid-call mutation is terminal, but its
            # exception carries prior spend for append-only process logging.
            try:
                lease.verify(endpoint)
            except RouteFirewallError as e:
                e.spend = _spend(attempt)
                raise
            # Prepare the next prompt reference without advancing the
            # top-level call pointer yet.  If reservation fails, ``_spend``
            # must continue to name the last request that actually reached
            # the provider, not this generated-but-unsent repair prompt.
            request_prompt_ref = (
                prompt_ref if attempt == 0 else self.blobs.put(request.encode())
            )
            # Snapshot the effective process-health limits at the wire
            # boundary. A logged controller may have adjusted either value
            # since manifest compilation; the attempt trace must describe
            # the request that was actually sent, not only the base route.
            transport_limits = {
                "max_tokens": getattr(
                    endpoint, "max_tokens", lease.route.max_tokens
                ),
                "timeout_s": getattr(
                    endpoint, "timeout_s", lease.route.timeout_s
                ),
            }
            # Reserve-settle (llm/budget.py): book the call's conservative
            # upper bound (chars/3 prompt estimate + the transport
            # max_tokens cap) BEFORE dispatch.  Against a finite ceiling an
            # unboundable call fails closed; concurrent dispatchers can
            # never jointly push the logged total past the ceiling.
            reservation = None
            reservation_bound = conservative_prompt_bound(request) + int(
                transport_limits["max_tokens"] or 0
            )
            if dispatch_authorization is not None:
                if attempt != 0:
                    raise WorkflowAuthorizationError(
                        "transactional repair requires a new authorization bundle",
                        spend=_spend(attempt),
                    )
                reservation = dispatch_authorization.reservation
                if reservation.amount != reservation_bound:
                    raise WorkflowAuthorizationError(
                        "transactional reservation bound differs from rendered request"
                    )
            elif self.meter is not None:
                try:
                    reservation = self.meter.reserve(
                        prompt_text=request,
                        max_tokens=transport_limits["max_tokens"],
                    )
                except TokenBudgetExceeded as e:
                    e.spend = _spend(attempt)
                    raise
            if attempt == 0 and workflow_dispatch_observer is not None:
                # Observation happens after the real reserve is booked and
                # immediately before provider dispatch.  A shadow observer
                # failure cannot suppress the legacy call.
                authorization_error = None
                try:
                    observed_work_order_id = workflow_dispatch_observer(
                        reservation.amount
                        if reservation is not None
                        else reservation_bound
                    )
                except Exception as error:  # noqa: BLE001 - mode checked below
                    observed_work_order_id = None
                    authorization_error = error
                if (
                    isinstance(observed_work_order_id, str)
                    and re.fullmatch(
                        r"sha256:[0-9a-f]{64}", observed_work_order_id
                    )
                    is not None
                ):
                    effective_work_order_id = observed_work_order_id
                elif workflow_dispatch_required:
                    if reservation is not None:
                        reservation.release()
                    raise WorkflowAuthorizationError(
                        "active workflow dispatch was not durably authorized"
                    ) from authorization_error
            prompt_ref = request_prompt_ref
            try:
                kwargs = {}
                if images:
                    kwargs["images"] = images
                if mechanism != OutputMechanism.JSON_TEXT:
                    kwargs.update(
                        response_schema=response_schema,
                        output_mechanism=mechanism,
                    )
                raw = endpoint.complete(request, **kwargs)
            except EndpointError as e:
                if reservation is not None:
                    # Usage unknown: return the reserve without recording
                    # spend (matches the pre-reserve accounting for calls
                    # that died in transport before any usage report).
                    reservation.release()
                diagnostic_payload = json.dumps(
                    {
                        "contract": wire_contract.contract_id,
                        "attempt": attempt,
                        "error": str(e)[:500],
                        "validation_path": turn.validation_path,
                        "repair_scope": turn.repair_scope,
                        "transport_diagnostics": list(
                            getattr(endpoint, "last_transport_diagnostics", ())
                        ),
                    },
                    sort_keys=True,
                )
                attempt_trace.append(LLMAttempt(
                    prompt_ref=prompt_ref,
                    diagnostic_ref=self.blobs.put(diagnostic_payload.encode()),
                    attempt=attempt,
                    validation_path=turn.validation_path,
                    **trace_identity,
                    repair_scope=turn.repair_scope,
                    **transport_limits,
                    ms=int((time.monotonic() - attempt_started) * 1000),
                    valid=False,
                    usage_unknown=True,
                    output_mechanism=mechanism.value,
                    transport_attempts=max(
                        1, int(getattr(endpoint, "last_transport_attempts", 0) or 0)
                    ),
                    transport_diagnostics=list(
                        getattr(endpoint, "last_transport_diagnostics", ())
                    ),
                ))
                # Even a zero-token transport failure is a replayable process
                # event; prior schema attempts and every route retry remain
                # reachable through this spend record.
                e.spend = _spend(attempt + 1)
                raise
            except BaseException:
                if reservation is not None:
                    reservation.release()
                raise
            if getattr(endpoint, "last_finish_reason", None) == "length":
                truncated_any = True  # process signal for the controller
            usage = _usage_tokens(getattr(endpoint, "last_usage", None), request, raw)
            attempt_tokens = usage["prompt_tokens"] + usage["completion_tokens"]
            tokens_used += attempt_tokens
            exact_prompt_tokens += usage["prompt_tokens"]
            exact_completion_tokens += usage["completion_tokens"]
            if reservation is not None:
                # Settle the reservation to provider-reported usage; the
                # bound shrinks to reality under the meter lock.
                reservation.settle(usage)
            raw_ref = self.blobs.put(raw.encode())
            try:
                candidate = repair.candidate_from_raw(turn, raw)
                reject_model_control_fields(candidate)
                wire_value = wire_contract.validate_value(candidate)
                data = wire_contract.compile(wire_value)
            except (TypeError, ValueError) as e:
                if isinstance(e, ModelControlFieldError):
                    # The exact raw and field-level diagnostic remain in the
                    # append-only process trace. The next model-facing pack
                    # receives only a sanitized copy and neutral root-scoped
                    # diagnostic, so authored operator language cannot be
                    # reflected into a repair instruction.
                    diagnostic = repair.note_control_invalid(
                        e,
                        sanitize_model_control_fields_for_repair(candidate),
                    )
                else:
                    diagnostic = repair.note_invalid(
                        turn,
                        raw,
                        e,
                        truncated=(
                            getattr(endpoint, "last_finish_reason", None) == "length"
                        ),
                    )
                diagnostic_ref = self.blobs.put(
                    diagnostic.model_dump_json().encode()
                )
                attempt_trace.append(LLMAttempt(
                    prompt_ref=prompt_ref,
                    raw_ref=raw_ref,
                    diagnostic_ref=diagnostic_ref,
                    attempt=attempt,
                    validation_path=diagnostic.path,
                    **trace_identity,
                    repair_scope=diagnostic.repair_scope,
                    **transport_limits,
                    tokens=attempt_tokens,
                    ms=int((time.monotonic() - attempt_started) * 1000),
                    valid=False,
                    output_mechanism=mechanism.value,
                    transport_attempts=max(
                        1, int(getattr(endpoint, "last_transport_attempts", 1) or 1)
                    ),
                    transport_diagnostics=list(
                        getattr(endpoint, "last_transport_diagnostics", ())
                    ),
                ))
                if attempt + 1 < repair.attempt_count:
                    # The rejected attempt and its diagnostic are immutable at
                    # this point. Persist repair authority before the next
                    # reservation or provider dispatch; observer failure stays
                    # contained on the C1 shadow path.
                    if workflow_repair_observer is None:
                        if workflow_dispatch_required:
                            raise WorkflowAuthorizationError(
                                "active workflow repair was not durably authorized",
                                spend=_spend(attempt + 1),
                            )
                    else:
                        try:
                            workflow_repair_observer(attempt_trace[-1])
                        except Exception as error:  # noqa: BLE001 - mode checked below
                            if workflow_dispatch_required:
                                raise WorkflowAuthorizationError(
                                    "active workflow repair was not durably authorized",
                                    spend=_spend(attempt + 1),
                                ) from error
                continue
            attempt_trace.append(LLMAttempt(
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                attempt=attempt,
                validation_path=turn.validation_path,
                **trace_identity,
                repair_scope=turn.repair_scope,
                **transport_limits,
                tokens=attempt_tokens,
                ms=int((time.monotonic() - attempt_started) * 1000),
                valid=True,
                output_mechanism=mechanism.value,
                transport_attempts=max(
                    1, int(getattr(endpoint, "last_transport_attempts", 1) or 1)
                ),
                transport_diagnostics=list(
                    getattr(endpoint, "last_transport_diagnostics", ())
                ),
            ))
            call = LLMCall(
                role=role,
                model=lease.route.model_id,
                endpoint=lease.route.base_url,
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                tokens=tokens_used,
                ms=int((time.monotonic() - started) * 1000),
                attempts=attempt + 1,
                truncated=truncated_any,
                mean_surprisal=getattr(endpoint, "last_mean_surprisal", None),
                attempt_trace=attempt_trace,
                school_route=school_route,
                conjecture_context=conjecture_context,
                work_order_id=effective_work_order_id,
                dispatch_authorization_ref=dispatch_authorization_ref,
                prompt_tokens=(
                    exact_prompt_tokens if dispatch_authorization is not None else None
                ),
                completion_tokens=(
                    exact_completion_tokens if dispatch_authorization is not None else None
                ),
            )
            return data, call
        error = SchemaRepairError(
            f"role {role}: no schema-valid output after bounded repair: "
            f"{str(repair.last_error)[:500]}",
            spend=_spend(repair.attempt_count),
        )
        self._mark_compact_recovery(
            role,
            profile,
            wire_contract,
        )
        raise error


def _endpoint_from_spec(spec: dict) -> OpenAICompatEndpoint | None:
    """The §15 role table is the model-change plug: endpoint, model,
    provider, reasoning, caps — all config, no call-site edits."""
    if not isinstance(spec, dict) or not spec.get("endpoint"):
        return None
    api_key_env = spec.get("api_key_env") or ""
    api_key = os.environ.get(api_key_env) if api_key_env else None
    model = resolve_model(spec.get("model") or "", spec["endpoint"], api_key)
    timeout_kwargs = (
        {"timeout_s": spec["timeout_s"]} if spec.get("timeout_s") else {}
    )
    endpoint = OpenAICompatEndpoint(
        base_url=spec["endpoint"],
        model=model,
        api_key=api_key,
        temperature=spec.get("temperature"),
        max_tokens=spec.get("max_tokens"),
        json_mode=bool(spec.get("json_mode", False)),
        request_logprobs=bool(spec.get("logprobs", False)),
        reasoning=spec.get("reasoning"),
        provider=spec.get("provider"),
        output_mechanism=spec.get("output_mechanism") or "json_text",
        **timeout_kwargs,
    )
    # Preserve compile-time identities when a standalone manifest has been
    # materialized as Config for an existing workflow facade.
    endpoint.endpoint_id = spec.get("endpoint_id") or spec["endpoint"]
    # Default to the same deterministic inference the route lease uses
    # (route_from_endpoint), so a config without an explicit family key can
    # never disagree with its own lease and fail closed at the first call.
    endpoint.family = spec.get("family") or infer_model_family(
        model, spec.get("provider") or ""
    )
    endpoint.model_revision = spec.get("model_revision") or None
    return endpoint


def build_adapter(
    config,
    blob_store,
    meter=None,
    only_roles: set[str] | None = None,
    run_manifest=None,
    process_events=None,
) -> LLMAdapter:
    """Build from the §15 role table. Roles with a null endpoint are absent
    (has_role False); a list spec becomes an ensemble (judge, §9).
    ``only_roles`` lets a single-purpose view use its configured seat without
    resolving or requiring credentials for unrelated engine roles."""
    endpoints: dict[str, object] = {}
    role_specs = (
        {
            role: (
                [route.endpoint_spec() for route in routes]
                if len(routes) > 1
                else routes[0].endpoint_spec()
            )
            for role, routes in run_manifest.roles.items()
            if routes
        }
        if run_manifest is not None
        else (config.roles or {})
    )
    for role, spec in role_specs.items():
        if only_roles is not None and role not in only_roles:
            continue
        if isinstance(spec, list):
            built = [e for e in (_endpoint_from_spec(s) for s in spec) if e is not None]
            if built:
                endpoints[role] = built
            continue
        endpoint = _endpoint_from_spec(spec)
        if endpoint is not None:
            endpoints[role] = endpoint
    leases = leases_from_manifest(run_manifest) if run_manifest is not None else None
    adapter = LLMAdapter(
        endpoints,
        blob_store,
        retry_max=config.RETRY_MAX,
        meter=meter,
        model_profile=(
            run_manifest.model_profile
            if run_manifest is not None
            else getattr(config, "model_profile", None)
        ),
        leases=leases,
        transaction_authority_required=(
            run_manifest is not None and run_manifest.schema_version == 6
        ),
    )
    if process_events is not None:
        adapter.rehydrate_compact_recovery(process_events)
    return adapter
