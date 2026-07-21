"""Conj (spec §3): a = gamma(pi, S) via the conjecturer role.

Enabled iff the problem frontier is nonempty (D1 made structural). Each
gamma-call returns a VS_K candidate distribution with typicality estimates
(§11.6); every candidate passes the anti-relapse gate before commit, and
problem criteria are instantiated into each candidate's interface.
Born-connected (§7 L1): candidate refs to registered neighbourhood
artifacts are kept. School conditioning (§11.1) enters ONLY through the
pack render and provenance — never adjudication. Under a stagnation flag
the harness spends budget tail-first on the candidates the model itself
marks atypical (§11.6).
"""

import hashlib
import json
import re

from pydantic import ValidationError

from deepreason.canonical import canonical_json
from deepreason.conjecture_events import (
    ConjectureTurnAction,
    ConjectureTurnEventPayloadV1,
)
from deepreason.conjecture_turn import (
    ContextRequestV1,
    ConjectureTurnV6,
    ConjecturerTurnV4,
    ConjecturerTurnV5,
    ReasoningConjecturerTurnV6,
    ReasoningConjecturerTurnV4,
    ReasoningConjecturerTurnV5,
)
from deepreason.llm.adapter import RequestEnvelopeExceeded, WorkflowAuthorizationError
from deepreason.llm.contracts import CandidateRef, ConjectureCandidate, ConjecturerOutput
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.firewall import EndpointLease, RouteFirewallError
from deepreason.llm.packs import aliases_for_pack, render_conj_pack
from deepreason.llm.repair import SchemaRepairError
from deepreason.llm.wire import (
    AliasTable,
    AtomicConjectureWireContractV1,
    ConjecturerTurnWireContractV4,
    ConjecturerTurnWireContractV5,
    ConjecturerTurnWireContractV6,
)
from deepreason.ontology import Artifact, Provenance, Rule, Warrant
from deepreason.rules.guards import anti_relapse
from deepreason.workloads.models import MandatoryInterface, compile_interface_draft
from deepreason.scratch.proposals import V6_SCRATCH_WORKSHOP_PROMPT
from deepreason.workloads.text import (
    ReasoningConjecturerOutput,
    draft_countercondition_commitments,
    envelope_json,
    proposal_envelope,
)


def _resolve_ref(target: str, artifacts: dict) -> str | None:
    """Backward-compatible unique-prefix resolver used by older callers."""
    if not target:
        return None
    if target in artifacts:
        return target
    matches = [artifact_id for artifact_id in artifacts if artifact_id.startswith(target)]
    return matches[0] if len(matches) == 1 else None


def root_problem_family(state, problem_id: str) -> str:
    """Stable provenance-root family key for anti-relapse domains (RC3).

    Successor problems (succ:*) are fresh attention objects; using their ids
    as the domain's problem_family let a refuted approach re-enter unchanged
    on its next successor. Walk the provenance chain back to the root
    problem id(s) and scope the domain there instead."""
    from deepreason.scheduler.scheduler import problem_family_key

    return problem_family_key(state, problem_id)


def _active_control_trace(
    harness,
    adapter,
    manifest,
    problem,
    *,
    school_id: str | None,
    context_plan,
    endpoint_lease: EndpointLease | None,
):
    """Bootstrap authoritative Conj control when the scheduler has no observer."""

    from deepreason.workflow.events import ConjectureWorkAssignmentV1
    from deepreason.workflow.profiles import (
        compile_workflow_profile,
        resolve_conjecture_route,
    )
    from deepreason.workflow.reducer import plan_conjecture_batch
    from deepreason.workflow.shadow import ShadowTicketV1
    from deepreason.workflow.state import WorkflowProcessStateV1
    from deepreason.workflow.trace import ConjectureControlTrace

    profile = compile_workflow_profile(manifest)
    lease, route = resolve_conjecture_route(
        manifest,
        adapter.leases,
        school_id=school_id,
    )
    if endpoint_lease is not None and endpoint_lease != lease:
        raise ValueError("active Conj endpoint lease differs from workflow authority")
    default_fence = max(0, harness._next_seq - 1)
    formal_fence = getattr(context_plan, "formal_fence_seq", default_fence)
    scratch_fence = getattr(context_plan, "scratch_fence_seq", default_fence)
    state = WorkflowProcessStateV1.initial(
        manifest_digest=profile.manifest_digest,
        workflow_profile=profile.workflow_profile,
        formal_fence_seq=formal_fence,
        scratch_fence_seq=scratch_fence,
    )
    assignment = ConjectureWorkAssignmentV1(
        school_id=school_id,
        route_lease=route,
        contract_id=profile.conjecturer_contract_id,
        task_payload_schema_id="conjecture.semantic-ref.v1",
        task_payload_ref=problem.id,
        input_refs=(problem.id,),
        advisory_context_ref=getattr(getattr(context_plan, "advisory_context", None), "id", None),
    )
    reduction = plan_conjecture_batch(
        profile,
        state=state,
        problem_ref=problem.id,
        assignments=(assignment,),
        canonical_problem_refs=tuple(sorted(harness.state.problems)),
    )
    (work,) = reduction.work_orders
    ticket = ShadowTicketV1.create(
        work_order=work,
        initial_process_state=state,
        process_state=reduction.state,
        planning_decisions=reduction.decisions,
        expected_decision_refs=tuple(item.id for item in reduction.decisions),
        expected_transition_kinds=tuple(item.transition_kind for item in reduction.decisions),
        event_start_seq=harness._next_seq,
        meter_before=(
            adapter.meter.snapshot() if getattr(adapter, "meter", None) is not None else None
        ),
    )
    return ConjectureControlTrace(harness, ticket, authoritative=True)


def _guard_finding(candidate_ref: str, outcome: str, reason: str):
    """Derive the same code-authored guard receipt without a scheduler callback."""

    from deepreason.workflow.models import (
        GuardFindingCode,
        GuardFindingOutcome,
        GuardFindingV1,
    )

    disposition = GuardFindingOutcome(outcome)
    code = (
        GuardFindingCode.PASSED
        if disposition == GuardFindingOutcome.ADMIT
        else GuardFindingCode.CONTENT_DUPLICATE
        if disposition == GuardFindingOutcome.DEDUPLICATE
        else GuardFindingCode.BATTERY_EQUIVALENT
        if "battery-equivalent" in reason
        else GuardFindingCode.REFUTED_EQUIVALENT
        if reason.startswith("hash:")
        else GuardFindingCode.INTERFACE_INVALID
    )
    return GuardFindingV1(
        candidate_ref=candidate_ref,
        outcome=disposition,
        code=code,
        related_refs=(candidate_ref,),
    )


def _v6_component_diagnostic(
    harness,
    *,
    component: str,
    phase: str,
    error: Exception,
    partial_refs: tuple[str, ...] = (),
) -> str:
    """Persist a deterministic diagnostic for one optional semantic component."""

    refs = tuple(dict.fromkeys(partial_refs))
    return harness.blobs.put(
        canonical_json(
            {
                "schema": "conjecture-component-diagnostic.v1",
                "component": component,
                "phase": phase,
                "disposition": "partial" if refs else "omitted",
                "error_code": getattr(error, "code", None),
                "error_type": type(error).__name__,
                "message": str(error)[:500],
                "partial_refs": list(refs),
            }
        )
    )


def _v6_scratch_effect_refs(harness, context_ref: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            output
            for event in harness.log.read()
            if event.scratch is not None and event.scratch.context_ref == context_ref
            for output in event.outputs
        )
    )


def _v6_simulation_effect_refs(
    harness,
    *,
    work_id: str,
    provider_attempt_ref: str,
) -> tuple[str, ...]:
    proposals = sorted(
        (
            proposal
            for proposal in harness.capability_state.proposals.values()
            if proposal.originating_work_order_ref == work_id
            and proposal.originating_provider_attempt_ref == provider_attempt_ref
        ),
        key=lambda proposal: (proposal.proposal_index, proposal.id),
    )
    return tuple(proposal.id for proposal in proposals)


def _validate_v6_context_continuation(
    harness,
    run_manifest,
    problem,
    school_id,
    binding,
    request,
    prior_plan,
):
    """Validate a child request against its completed parent transaction."""

    from deepreason.scratch.conjecture import PlannedConjectureContextV1
    from deepreason.workflow.context_continuation import (
        ConjectureContextContinuationV1,
        context_plan_sha256,
    )

    binding = ConjectureContextContinuationV1.model_validate(binding)
    request = ContextRequestV1.model_validate(request)
    prior_plan = (
        PlannedConjectureContextV1.model_validate(prior_plan) if prior_plan is not None else None
    )
    context_policy = run_manifest.control_plane_policy.conjecture_context
    expected = (
        binding.manifest_digest == run_manifest.sha256,
        binding.problem_id == problem.id,
        binding.school_id == school_id,
        binding.request_hash == request.request_hash,
        binding.policy_mode == context_policy.mode,
        binding.maximum_expansions == context_policy.max_context_expansion_requests,
        binding.maximum_extra_blocks == context_policy.max_extra_blocks,
        binding.permitted_retrieval_channels == context_policy.permitted_retrieval_channels,
        binding.desired_retrieval_channels
        == tuple(channel.value for channel in request.desired_retrieval_channels),
    )
    if not all(expected):
        raise ValueError("v6 context continuation differs from frozen request authority")

    request_bytes = canonical_json(
        request.model_dump(mode="json", by_alias=True, exclude_none=True)
    )
    if harness.blobs.get(binding.request_ref) != request_bytes:
        raise ValueError("v6 context continuation request blob differs from its binding")
    if binding.prior_context_plan_sha256 != context_plan_sha256(prior_plan):
        raise ValueError("v6 context continuation prior plan differs from its binding")
    prior_selection = (
        prior_plan.attention_pack.selection_receipt.id if prior_plan is not None else None
    )
    if binding.prior_selection_receipt_ref != prior_selection:
        raise ValueError("v6 context continuation prior selection differs from its binding")

    parent = harness.workflow_state.transaction_work.get(binding.parent_work_id)
    if parent is None or parent.terminal is None or parent.terminal.status != "completed":
        raise ValueError("v6 context continuation parent is not completed")
    provider = parent.provider_attempts.get(binding.parent_attempt_index)
    admission = parent.admissions.get(binding.parent_attempt_index)
    if (
        provider is None
        or provider.id != binding.parent_provider_attempt_ref
        or parent.exposure is None
        or parent.exposure.id != binding.parent_exposure_receipt_ref
        or admission is None
        or admission.id != binding.parent_semantic_admission_ref
        or parent.terminal.provider_attempt_ref != provider.id
        or parent.terminal.semantic_admission_ref != admission.id
        or binding.parent_semantic_output_ref not in admission.admitted_refs
    ):
        raise ValueError("v6 context continuation parent authority is inconsistent")

    try:
        parent_output = json.loads(
            harness.blobs.get(binding.parent_semantic_output_ref).decode("utf-8")
        )
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("v6 context continuation parent output is unavailable") from error
    if (
        not isinstance(parent_output, dict)
        or canonical_json(parent_output.get("context_request")) != request_bytes
    ):
        raise ValueError("v6 context continuation request was not admitted by its parent")

    source_event = next(
        (event for event in harness.log.read() if event.seq == binding.parent_provider_event_seq),
        None,
    )
    if (
        source_event is None
        or source_event.llm is None
        or source_event.llm.work_order_id != binding.parent_work_id
        or source_event.llm.dispatch_authorization_ref != provider.authorization_bundle_ref
    ):
        raise ValueError("v6 context continuation source event differs from its parent")
    return binding, request, prior_plan


def _v6_context_continuation_input_refs(binding) -> tuple[str, ...]:
    return tuple(
        item
        for item in (
            binding.parent_work_id,
            binding.parent_provider_attempt_ref,
            binding.parent_exposure_receipt_ref,
            binding.parent_semantic_admission_ref,
            binding.parent_semantic_output_ref,
            binding.request_hash,
            binding.request_ref,
            binding.decision_ref,
            binding.prior_selection_receipt_ref,
        )
        if item is not None
    )


def _v6_no_context_reason(scratch_policy, context_policy, prior_plan) -> str:
    prior_count = (
        len(prior_plan.attention_pack.selection_receipt.final_order)
        if prior_plan is not None
        else 0
    )
    root_count = (
        len(
            prior_plan.root_block_ids
            if prior_plan.root_block_ids is not None
            else prior_plan.attention_pack.selection_receipt.final_order
        )
        if prior_plan is not None
        else 0
    )
    total_cap = min(
        scratch_policy.attention_policy().max_blocks_per_pack,
        root_count + context_policy.max_extra_blocks,
    )
    return "no_context_capacity" if total_cap <= prior_count else "no_additional_context"


def _v6_atomic_conjecture_fallback(
    harness,
    adapter,
    manifest,
    *,
    endpoint_lease: EndpointLease,
    school_id: str | None,
    problem,
    strong_payload: dict,
    pack: str,
    aliases: AliasTable,
    exposure_items: tuple,
    transition,
):
    """Execute or recover all deterministic single-candidate child calls."""

    from deepreason.llm.firewall import route_fingerprint
    from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
    from deepreason.workflow.transaction import VisibleContextItemV1
    from deepreason.workflow.transaction_service import InquiryTransactionService

    route_ref = RouteLeaseRefV1(
        role="conjecturer",
        seat=endpoint_lease.seat,
        endpoint_id=endpoint_lease.route.endpoint_id,
        route_sha256=route_fingerprint(endpoint_lease.route),
    )
    if (
        transition.route_lease != route_ref
        or transition.atomic_contract_id != "conjecturer.atomic-candidate.v1"
    ):
        raise ValueError("atomic conjecture differs from decomposition authority")
    reasoning = bool(strong_payload.get("reasoning", False))
    contract = AtomicConjectureWireContractV1(aliases, reasoning=reasoning)
    output_model = ReasoningConjecturerTurnV6 if reasoning else ConjectureTurnV6
    service = InquiryTransactionService(harness, manifest, adapter.meter)
    child_count = transition.maximum_children
    candidates = []
    abstentions = []
    calls = []

    for child_index in range(child_count):
        child_pack = harness.blobs.get(
            transition.child_context_refs[child_index]
        ).decode("utf-8")
        payload = {
            "schema": "contract-decomposition-child.v1",
            "decomposition_transition_ref": transition.id,
            "source_work_id": transition.source_work_id,
            "source_contract_id": transition.source_contract_id,
            "atomic_contract_id": transition.atomic_contract_id,
            "child_partition": transition.child_partition,
            "child_index": child_index,
            "child_count": child_count,
            "child_key": f"candidate-slot-{child_index:03d}",
            "problem_ref": problem.id,
            "school_id": school_id,
            "run_input_digest": manifest.run_input_digest,
            "mandatory_interface": strong_payload.get("mandatory_interface"),
            "component_spec": strong_payload.get("component_spec"),
            "theorem_interface": strong_payload.get("theorem_interface"),
            "tail_weighted": bool(strong_payload.get("tail_weighted", False)),
        }
        matches = [
            item
            for item in harness.workflow_state.transaction_work.values()
            if item.preparation.contract_id == contract.contract_id
            and item.preparation.task_payload_value == payload
            and item.preparation.route_lease == route_ref
        ]
        if len(matches) > 1:
            raise ValueError("atomic conjecture child history is ambiguous")
        if matches:
            item = matches[0]
            from deepreason.workflow.atomic_recovery import (
                recover_atomic_child_output,
            )

            output, call = recover_atomic_child_output(
                harness, manifest, service, item, contract
            )
        else:
            fence = max(0, harness._next_seq - 1)
            trigger_ref = "decomposition-child:" + hashlib.sha256(
                canonical_json(payload)
            ).hexdigest()
            preparation = service.prepare(
                task_kind=WorkflowTaskKind.CONJECTURE,
                attempt_index=0,
                route_lease=route_ref,
                contract_id=contract.contract_id,
                trigger_ref=trigger_ref,
                formal_fence_seq=fence,
                scratch_fence_seq=fence,
                target_refs=(problem.id,),
                input_refs=(
                    transition.source_work_id,
                    transition.id,
                    transition.child_context_refs[child_index],
                    problem.id,
                ),
                task_payload_value=payload,
            )
            planned_bytes = sum(item.planned_bytes for item in exposure_items)
            cloned_items = tuple(
                VisibleContextItemV1.model_validate(item.model_dump(mode="python"))
                for item in exposure_items
            )
            plan = service.context_plan(
                preparation,
                plan_kind="combined",
                items=cloned_items,
                maximum_bytes=planned_bytes,
                rendered_bytes=planned_bytes,
            )
            prompt, preview_contract, preview_lease, maximum_tokens = (
                adapter.preview_request(
                    "conjecturer",
                    child_pack,
                    output_model,
                    endpoint_index=endpoint_lease.seat,
                    wire_contract=contract,
                    aliases=aliases,
                    endpoint_lease=endpoint_lease,
                )
            )
            if preview_contract is not contract or preview_lease != endpoint_lease:
                raise ValueError("atomic conjecture preview changed frozen authority")
            authorized = service.issue(
                preparation,
                plans=(plan,),
                prompt=prompt,
                max_tokens=maximum_tokens,
            )
            try:
                output, call = adapter.call(
                    "conjecturer",
                    child_pack,
                    output_model,
                    endpoint_index=endpoint_lease.seat,
                    wire_contract=contract,
                    aliases=aliases,
                    endpoint_lease=endpoint_lease,
                    school_id=school_id,
                    dispatch_authorization=authorized,
                )
            except EndpointError as error:
                spend = getattr(error, "spend", None)
                if spend is None:
                    if authorized.reservation.is_open:
                        authorized.release()
                    service.terminate(
                        work_id=preparation.id,
                        attempt_index=preparation.attempt_index,
                        status="abandoned",
                        reason_code="atomic_conjecture_provider_result_unknown",
                        usage_status="unknown",
                    )
                else:
                    diagnostic_ref = (
                        spend.attempt_trace[-1].diagnostic_ref
                        if spend.attempt_trace
                        else harness.blobs.put(str(error).encode("utf-8"))
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
                        reason_code="atomic_conjecture_transport_failure",
                        usage_status="unknown",
                        provider_attempt=provider,
                    )
                    error.spend = None
                error.transaction_terminalized = True
                raise
            except SchemaRepairError as error:
                repaired = service.repair_schema_failure(
                    adapter=adapter,
                    authorized=authorized,
                    error=error,
                    role="conjecturer",
                    pack=child_pack,
                    output_model=output_model,
                    wire_contract=contract,
                    endpoint_index=endpoint_lease.seat,
                    endpoint_lease=endpoint_lease,
                    school_id=school_id,
                    reason_prefix="atomic_conjecture",
                )
                output, call = repaired.output, repaired.llm_call
                preparation, authorized = repaired.preparation, repaired.authorized
                provider = repaired.provider_attempt
            else:
                provider = service.record_provider_attempt(
                    authorized,
                    call=call,
                    outcome="provider_result",
                    usage_status="exact",
                )
            admitted_ref = harness.blobs.put(
                canonical_json(output.model_dump(mode="json", exclude_none=True))
            )
            admission = service.record_semantic_admission(
                provider, outcome="admitted", admitted_refs=(admitted_ref,)
            )
            service.terminate(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                status="completed",
                reason_code="atomic_conjecture_output_admitted",
                usage_status="exact",
                prompt_tokens=call.prompt_tokens,
                completion_tokens=call.completion_tokens,
                provider_attempt=provider,
                admission=admission,
            )
        candidates.extend(output.candidates)
        if output.abstention is not None:
            abstentions.append(output.abstention)
        calls.append(call)

    combined_model = ReasoningConjecturerTurnV6 if reasoning else ConjectureTurnV6
    if candidates:
        combined = combined_model(candidates=tuple(candidates))
    elif abstentions:
        combined = combined_model(abstention=abstentions[0])
    else:  # contract validation should make this unreachable
        raise ValueError("atomic conjecture children produced no meaningful outcome")
    return combined, calls


def conj(
    harness,
    problem_id: str,
    adapter,
    config,
    diagnostics: list | None = None,
    *,
    school: dict | None = None,
    tail_weighted: bool = False,
    complement: bool = False,
    specs: list[str] | None = None,
    embedder=None,
    mandatory_interface: MandatoryInterface | None = None,
    workload_profile: str | None = None,
    contract_id: str = "conjecturer.direct.v1",
    component_spec: str | None = None,
    theorem_interface: str | None = None,
    generation_context: str | None = None,
    suppressed_exemplars: tuple[str, ...] = (),
    capture_candidate_content: bool = False,
    endpoint_lease: EndpointLease | None = None,
    execution_school_id: str | None = None,
    conjecture_context_plan=None,
    run_manifest=None,
    _context_expansion_index: int = 0,
    candidate_observer=None,
    workflow_work_order_id: str | None = None,
    workflow_control_trace=None,
    _capability_result_context: str | None = None,
    _capability_result_package_ref: str | None = None,
    _capability_result_context_ref: str | None = None,
    _simulation_follow_up_index: int = 0,
    _v6_context_continuation=None,
    _v6_context_request: ContextRequestV1 | None = None,
    _v6_prior_context_plan=None,
) -> list[Artifact]:
    problem = harness.state.problems.get(problem_id)
    if problem is None:
        raise KeyError(f"Conj is gated on a registered problem; unknown: {problem_id}")
    if (endpoint_lease is None) != (execution_school_id is None):
        raise ValueError("school-routed Conj requires both endpoint_lease and execution_school_id")
    if execution_school_id is not None:
        if school is None or school.get("id") != execution_school_id:
            raise ValueError("execution school must match the semantic school conditioning record")
        if endpoint_lease.role != "conjecturer":
            raise ValueError("Conj endpoint lease must belong to the conjecturer role")
    if workflow_work_order_id is not None and workflow_control_trace is not None:
        raise ValueError("Conj accepts only one workflow binding seam")

    active_v4 = False
    active_v5 = False
    active_v6 = False
    context_policy = None
    scratch_policy = None
    transaction_service = None
    transaction_preparation = None
    transaction_authorization = None
    transaction_provider_attempt = None
    atomic_fallback_completed = False
    atomic_source_call_seq = None
    atomic_decomposition_transition = None
    transaction_simulation_aliases: dict[str, str] = {}
    transaction_capability_result_alias = None
    transaction_capability_result_package_ref = _capability_result_package_ref
    transaction_capability_result_ref = _capability_result_context_ref
    v6_capability_result_context = _capability_result_context
    v6_context_continuation = _v6_context_continuation
    v6_context_request = _v6_context_request
    v6_prior_context_plan = _v6_prior_context_plan
    dispatch_endpoint_lease = endpoint_lease
    if run_manifest is not None:
        from deepreason.run_manifest import RunManifest

        run_manifest = RunManifest.model_validate(run_manifest)
        control = run_manifest.control_plane_policy
        expected_contract = {
            4: "conjecturer.turn.v4",
            5: "conjecturer.turn.v5",
            6: "conjecturer.turn.v6",
        }.get(run_manifest.schema_version)
        if (
            expected_contract is None
            or control is None
            or control.mode not in {"active_conjecture", "active_inquiry"}
            or control.contract_versions.conjecturer_turn_contract != expected_contract
        ):
            raise ValueError(
                "controlled conjecture turns require their exact active manifest contract"
            )
        active_v4 = run_manifest.schema_version in {4, 5}
        active_v5 = run_manifest.schema_version == 5
        active_v6 = run_manifest.schema_version == 6
        context_policy = control.conjecture_context
        scratch_policy = run_manifest.scratch_policy
        if scratch_policy is None:
            raise ValueError("active conjecture manifest has no scratch policy")
        if generation_context is not None:
            raise ValueError(
                "active Conj requires typed context; raw generation_context is not permitted"
            )

    if active_v6:
        if workflow_work_order_id is not None or workflow_control_trace is not None:
            raise ValueError("v6 conjecture uses transaction authority, not legacy work bindings")
        if conjecture_context_plan is not None:
            raise ValueError("v6 conjecture context must be planned after durable work preparation")
        meter = getattr(adapter, "meter", None)
        if meter is None:
            raise ValueError("v6 conjecture dispatch requires a provider token meter")

        from deepreason.workflow.models import CapabilityOutcome, WorkflowTaskKind
        from deepreason.workflow.profiles import (
            compile_workflow_profile,
            resolve_conjecture_route,
        )
        from deepreason.workflow.transaction_service import InquiryTransactionService

        if (v6_context_continuation is None) != (v6_context_request is None):
            raise ValueError("v6 context continuation requires both binding and request")
        if v6_context_continuation is None and v6_prior_context_plan is not None:
            raise ValueError("v6 prior context plan requires a continuation binding")
        if v6_context_continuation is not None:
            (
                v6_context_continuation,
                v6_context_request,
                v6_prior_context_plan,
            ) = _validate_v6_context_continuation(
                harness,
                run_manifest,
                problem,
                execution_school_id,
                v6_context_continuation,
                v6_context_request,
                v6_prior_context_plan,
            )

        dispatch_endpoint_lease, route_ref = resolve_conjecture_route(
            run_manifest,
            adapter.leases,
            school_id=execution_school_id,
        )
        if endpoint_lease is not None and endpoint_lease != dispatch_endpoint_lease:
            raise ValueError("v6 conjecture route differs from its manifest authority")
        profile = compile_workflow_profile(run_manifest)
        grant = profile.capability_grant(completed_context_expansions=_context_expansion_index)
        allowed_outcomes = list(grant.allowed_outcomes)
        if control.scratch_authoring.enabled:
            allowed_outcomes.append(CapabilityOutcome.SCRATCH_PROPOSAL)
        simulation_policy = run_manifest.inquiry_capability_policy.simulation
        transaction_simulation_aliases = {
            f"SIM_{index:03d}": item.alias
            for index, item in enumerate(simulation_policy.input_catalog, 1)
        }
        result_binding = (
            _capability_result_context,
            transaction_capability_result_package_ref,
            transaction_capability_result_ref,
        )
        if _simulation_follow_up_index > 0:
            if any(item is None for item in result_binding):
                raise ValueError("v6 simulation follow-up requires package, context ref, and text")
            from deepreason.capabilities.enums import CapabilityLifecycle

            result_package = harness.capability_state.result_packages.get(
                transaction_capability_result_package_ref
            )
            transition = (
                harness.capability_state.transitions.get(
                    harness.capability_state.current_transition_by_request.get(
                        result_package.proposal_ref, ""
                    )
                )
                if result_package is not None
                else None
            )
            if (
                result_package is None
                or result_package.result_context_ref != transaction_capability_result_ref
                or transition is None
                or transition.lifecycle != CapabilityLifecycle.RESULT_PACKAGED
                or harness.blobs.get(transaction_capability_result_ref).decode("utf-8")
                != _capability_result_context
            ):
                raise ValueError("v6 simulation follow-up result binding is not canonical")
            transaction_capability_result_alias = (
                f"SIM_{len(transaction_simulation_aliases) + 1:03d}"
            )
            v6_capability_result_context = (
                f"{transaction_capability_result_alias}: recorded simulation result\n"
                f"{_capability_result_context}"
            )
        elif any(item is not None for item in result_binding):
            raise ValueError("simulation result context requires a follow-up work index")
        payload = {
            "schema": "conjecture.semantic-task.v2",
            "problem_ref": problem.id,
            "school_id": execution_school_id,
            "run_input_digest": run_manifest.run_input_digest,
            "allowed_outcomes": [item.value for item in allowed_outcomes],
            "maximum_candidates": grant.max_candidates,
            "simulation_authority": {
                "enabled": simulation_policy.enabled,
                "policy_digest": simulation_policy.digest,
                "maximum_proposals_per_turn": (simulation_policy.maximum_proposals_per_turn),
                "input_aliases": sorted(transaction_simulation_aliases),
            },
            "scratch_authoring_enabled": control.scratch_authoring.enabled,
            "context_expansion_index": _context_expansion_index,
            "simulation_follow_up_index": _simulation_follow_up_index,
            "capability_result_ref": transaction_capability_result_ref,
            "capability_result_package_ref": (transaction_capability_result_package_ref),
            "capability_result_context_ref": transaction_capability_result_ref,
            "workload_profile": workload_profile,
            "reasoning": any(
                harness.commitments[commitment_id].eval == "program:reasoning-envelope-wf"
                for commitment_id in problem.criteria
                if commitment_id in harness.commitments
            ),
            "tail_weighted": tail_weighted,
            "complement": complement,
            "specs": list(specs or ()),
            "mandatory_interface": (
                {
                    "commitments": list(mandatory_interface.commitments),
                    "refs": [
                        {"target": ref.target, "role": ref.normalized_role().value}
                        for ref in mandatory_interface.role_refs()
                    ],
                }
                if mandatory_interface is not None
                else None
            ),
            "component_spec": component_spec,
            "theorem_interface": theorem_interface,
            **(
                {
                    "context_continuation": v6_context_continuation.model_dump(
                        mode="json", by_alias=True, exclude_none=True
                    )
                }
                if v6_context_continuation is not None
                else {}
            ),
        }
        transaction_service = InquiryTransactionService(
            harness,
            run_manifest,
            meter,
        )

        def decomposition_source_root(transition):
            source = harness.workflow_state.transaction_work.get(
                transition.source_work_id
            )
            if source is None:
                return None
            value = source.preparation.task_payload_value
            if (
                isinstance(value, dict)
                and value.get("schema") == "repair.semantic-task.v1"
            ):
                source = harness.workflow_state.transaction_work.get(
                    value.get("parent_work_id")
                )
            return source

        incomplete_decompositions = []
        for transition in (
            harness.workflow_state.contract_decomposition_by_source_work.values()
        ):
            source_root = decomposition_source_root(transition)
            if (
                transition.manifest_digest == run_manifest.sha256
                and transition.route_lease == route_ref
                and transition.source_contract_id == "conjecturer.turn.v6"
                and transition.atomic_contract_id
                == "conjecturer.atomic-candidate.v1"
                and source_root is not None
                and source_root.preparation.task_payload_value == payload
                and transition.id
                not in harness.workflow_state.contract_decomposition_completion_by_transition
            ):
                incomplete_decompositions.append((transition, source_root))
        if len(incomplete_decompositions) > 1:
            raise ValueError("atomic conjecture history is ambiguous")
        if incomplete_decompositions:
            transition, source_root = incomplete_decompositions[0]
            if source_root.exposure is None:
                raise ValueError("atomic conjecture source lacks durable exposure")
            from deepreason.workflow.transaction import ContextNamespace

            recovered_aliases = AliasTable(
                {
                    item.alias: item.object_ref
                    for item in source_root.exposure.exposed_items
                    if item.namespace == ContextNamespace.SOURCE
                }
            )
            recovered_output, recovered_calls = _v6_atomic_conjecture_fallback(
                harness,
                adapter,
                run_manifest,
                endpoint_lease=dispatch_endpoint_lease,
                school_id=execution_school_id,
                problem=problem,
                strong_payload=payload,
                pack=harness.blobs.get(transition.child_context_refs[0]).decode(
                    "utf-8"
                ),
                aliases=recovered_aliases,
                exposure_items=tuple(source_root.exposure.exposed_items),
                transition=transition,
            )
            recovered_source_seqs = [
                event.seq
                for event in harness.log.read()
                for call in recovered_calls
                if event.llm == call
            ]
            if len(recovered_source_seqs) != len(recovered_calls):
                raise RuntimeError("atomic conjecture recovery lacks durable calls")
            from deepreason.workflow.conjecture_recovery import _materialize_formal

            recovered_refs = _materialize_formal(
                harness,
                run_manifest,
                recovered_output,
                payload,
                problem,
                recovered_source_seqs[-1],
                embedder=embedder,
                contract_id="conjecturer.atomic-candidate.v1",
            )
            harness.complete_contract_decomposition(
                run_manifest,
                transition,
                admitted_effect_refs=recovered_refs,
            )
            return [harness.state.artifacts[ref] for ref in recovered_refs]

        fence = max(0, harness._next_seq - 1)
        trigger_ref = "conjecture:" + hashlib.sha256(canonical_json(payload)).hexdigest()
        transaction_preparation = transaction_service.prepare(
            task_kind=WorkflowTaskKind.CONJECTURE,
            attempt_index=0,
            route_lease=route_ref,
            contract_id="conjecturer.turn.v6",
            trigger_ref=trigger_ref,
            formal_fence_seq=fence,
            scratch_fence_seq=fence,
            target_refs=(problem.id,),
            input_refs=tuple(
                dict.fromkeys(
                    (
                        *problem.criteria,
                        *(
                            _v6_context_continuation_input_refs(v6_context_continuation)
                            if v6_context_continuation is not None
                            else ()
                        ),
                        *(
                            (
                                transaction_capability_result_package_ref,
                                transaction_capability_result_ref,
                            )
                            if transaction_capability_result_package_ref is not None
                            else ()
                        ),
                    )
                )
            ),
            task_payload_value=payload,
        )

        def abandon_v6_context_preissue(
            reason_code: str = "conjecture_context_preissue_failed",
        ) -> None:
            item = harness.workflow_state.transaction_work[
                transaction_preparation.id
            ]
            if item.terminal is None and not item.issued:
                transaction_service.terminate(
                    work_id=transaction_preparation.id,
                    attempt_index=transaction_preparation.attempt_index,
                    status="abandoned",
                    reason_code=reason_code,
                    usage_status="exact",
                    prompt_tokens=0,
                    completion_tokens=0,
                )

        if v6_context_continuation is not None:
            from deepreason.scratch.conjecture import plan_conjecture_context_expansion
            from deepreason.scratch.service import ScratchService
            from deepreason.workflow.context_continuation import (
                ContextContinuationEligibility,
            )

            eligibility = v6_context_continuation.eligibility
            if eligibility != ContextContinuationEligibility.ELIGIBLE:
                transaction_service.terminate(
                    work_id=transaction_preparation.id,
                    attempt_index=transaction_preparation.attempt_index,
                    status="abandoned",
                    reason_code=f"context_{eligibility.value}",
                    usage_status="exact",
                    prompt_tokens=0,
                    completion_tokens=0,
                )
                return []
            if not scratch_policy.enabled:
                transaction_service.terminate(
                    work_id=transaction_preparation.id,
                    attempt_index=transaction_preparation.attempt_index,
                    status="abandoned",
                    reason_code="context_capability_not_granted",
                    usage_status="exact",
                    prompt_tokens=0,
                    completion_tokens=0,
                )
                return []
            plan_fence = harness._next_seq - 1
            try:
                conjecture_context_plan = plan_conjecture_context_expansion(
                    ScratchService(harness),
                    problem=problem,
                    school_id=execution_school_id,
                    manifest_digest=run_manifest.sha256,
                    scratch_policy=scratch_policy,
                    context_policy=context_policy,
                    request=v6_context_request,
                    prior_plan=v6_prior_context_plan,
                    expansion_decision_ref=v6_context_continuation.decision_ref,
                    expansion_index=v6_context_continuation.expansion_index,
                    formal_fence_seq=plan_fence,
                    scratch_fence_seq=plan_fence,
                )
            except Exception:
                abandon_v6_context_preissue()
                raise
            if conjecture_context_plan is None:
                reason = _v6_no_context_reason(
                    scratch_policy, context_policy, v6_prior_context_plan
                )
                transaction_service.terminate(
                    work_id=transaction_preparation.id,
                    attempt_index=transaction_preparation.attempt_index,
                    status="abandoned",
                    reason_code=f"context_{reason}",
                    usage_status="exact",
                    prompt_tokens=0,
                    completion_tokens=0,
                )
                return []
            if (
                conjecture_context_plan.expansion_decision_ref
                != v6_context_continuation.decision_ref
                or conjecture_context_plan.expansion_request_hash != v6_context_request.request_hash
                or conjecture_context_plan.expansion_index
                != v6_context_continuation.expansion_index
                or len(conjecture_context_plan.added_block_refs or ())
                > context_policy.max_extra_blocks
            ):
                abandon_v6_context_preissue()
                raise ValueError("expanded v6 context plan differs from child authority")
        elif context_policy.mode != "disabled" and scratch_policy.enabled:
            from deepreason.scratch.conjecture import plan_conjecture_context
            from deepreason.scratch.service import ScratchService

            plan_fence = harness._next_seq - 1
            try:
                conjecture_context_plan = plan_conjecture_context(
                    ScratchService(harness),
                    problem=problem,
                    school_id=execution_school_id,
                    manifest_digest=run_manifest.sha256,
                    scratch_policy=scratch_policy,
                    context_policy=context_policy,
                    formal_fence_seq=plan_fence,
                    scratch_fence_seq=plan_fence,
                )
            except Exception:
                abandon_v6_context_preissue()
                raise

    workflow_guard_findings = []
    workflow_guard_occurrences: dict[str, int] = {}

    def observe_candidate(candidate_ref: str, outcome: str, reason: str) -> None:
        """Report code-derived disposition without granting callback authority."""

        finding = None
        try:
            if candidate_observer is not None:
                finding = candidate_observer(candidate_ref, outcome, reason)
            if finding is not None:
                from deepreason.workflow.models import GuardFindingV1

                workflow_guard_findings.append(
                    GuardFindingV1.model_validate(
                        finding.model_dump(mode="python", by_alias=True)
                        if isinstance(finding, GuardFindingV1)
                        else finding
                    )
                )
                return
        except Exception:
            if not active_v4:
                return
        if active_v4 and workflow_control_trace is not None:
            workflow_guard_occurrences[candidate_ref] = (
                workflow_guard_occurrences.get(candidate_ref, 0) + 1
            )
            occurrence = workflow_guard_occurrences[candidate_ref]
            disposition_ref = (
                candidate_ref if occurrence == 1 else f"{candidate_ref}#occurrence-{occurrence}"
            )
            workflow_guard_findings.append(_guard_finding(disposition_ref, outcome, reason))

    if conjecture_context_plan is not None:
        from deepreason.scratch.conjecture import PlannedConjectureContextV1

        try:
            conjecture_context_plan = PlannedConjectureContextV1.model_validate(
                conjecture_context_plan
            )
            if conjecture_context_plan.problem_id != problem_id:
                raise ValueError("conjecture context was planned for another problem")
            if conjecture_context_plan.school_id != execution_school_id:
                raise ValueError("conjecture context was planned for another school")
            if generation_context:
                raise ValueError(
                    "typed scratch context cannot be replaced by raw generation_context"
                )
        except Exception:
            if active_v6:
                abandon_v6_context_preissue()
            raise
    if active_v4:
        control = run_manifest.control_plane_policy
        if (
            control is None
            or control.mode not in {"active_conjecture", "active_inquiry"}
            or control.contract_versions.conjecturer_turn_contract
            != (
                "conjecturer.turn.v5" if run_manifest.schema_version == 5 else "conjecturer.turn.v4"
            )
        ):
            raise ValueError(
                "controlled conjecture turns require their exact active manifest contract"
            )
        if scratch_policy is None:
            raise ValueError("active conjecture manifest has no scratch policy")
        if (
            conjecture_context_plan is not None
            and conjecture_context_plan.manifest_digest != run_manifest.sha256
        ):
            raise ValueError("conjecture context belongs to another manifest")
        if workflow_control_trace is None:
            workflow_control_trace = _active_control_trace(
                harness,
                adapter,
                run_manifest,
                problem,
                school_id=execution_school_id,
                context_plan=conjecture_context_plan,
                endpoint_lease=endpoint_lease,
            )
        workflow_control_trace.require_authority()
        if endpoint_lease is not None:
            from deepreason.workflow.profiles import route_lease_reference

            if workflow_control_trace.ticket.work_order.route_lease != route_lease_reference(
                endpoint_lease
            ):
                raise ValueError("active Conj endpoint lease differs from workflow work order")
    frozen_evidence_context = None
    dossier_receipt = None
    dossier_maximum_bytes = 0
    if active_v5 or active_v6:
        from deepreason.evidence import (
            commit_dossier_pack_receipt,
            dossier_exposure_counts,
            load_evidence_dossier,
            load_run_input,
            pack_dossier,
            render_dossier_pack,
        )

        evidence_policy = run_manifest.inquiry_capability_policy.attached_evidence
        if evidence_policy.enabled:
            bound_input = load_run_input(harness.root)
            dossier = load_evidence_dossier(harness.root)
            if bound_input.run_input_digest != run_manifest.run_input_digest:
                raise ValueError("conjecture evidence belongs to another run input")
            if dossier.problem_ref == problem.id:
                dossier_maximum_bytes = min(
                    evidence_policy.maximum_total_bytes,
                    evidence_policy.maximum_sources_per_pack
                    * evidence_policy.maximum_excerpt_bytes_per_source,
                    4 * 1024 * 1024,
                )
                dossier_receipt = pack_dossier(
                    root=harness.root,
                    run_input=bound_input,
                    dossier=dossier,
                    work_order_ref=(
                        transaction_preparation.id
                        if active_v6
                        else workflow_control_trace.ticket.work_order.id
                    ),
                    query=problem.description,
                    state_fence=(
                        "formal:"
                        f"{harness._next_seq - 1 if active_v6 else workflow_control_trace.ticket.work_order.formal_fence_seq};"
                        "scratch:"
                        f"{harness._next_seq - 1 if active_v6 else workflow_control_trace.ticket.work_order.scratch_fence_seq};"
                        f"workflow:{harness.workflow_state.digest}"
                    ),
                    maximum_sources=evidence_policy.maximum_sources_per_pack,
                    maximum_excerpt_bytes_per_source=(
                        evidence_policy.maximum_excerpt_bytes_per_source
                    ),
                    maximum_total_excerpt_bytes=dossier_maximum_bytes,
                    exposure_counts=dossier_exposure_counts(harness),
                )
                if active_v5:
                    commit_dossier_pack_receipt(harness, dossier_receipt)
                frozen_evidence_context = render_dossier_pack(
                    blobs=harness.blobs,
                    dossier=dossier,
                    receipt=dossier_receipt,
                )
    pack = render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        vs_k=config.VS_K,
        token_budget=config.PACK_TOKEN_BUDGET,
        school=school,
        complement=complement or bool(config.COMPLEMENT_ALWAYS),
        specs=specs,
        neighbourhood_n=config.NEIGHBOURHOOD_N,
        generation_context=generation_context,
        suppressed_exemplars=suppressed_exemplars,
        scratch_context=(
            conjecture_context_plan.rendered_context
            if conjecture_context_plan is not None
            else None
        ),
        frozen_evidence_context=frozen_evidence_context,
        capability_result_context=v6_capability_result_context,
        allow_no_candidate_outcome=active_v4 or active_v6,
    )
    scratch_aliases = {}
    v6_scratch_rendered_text = None
    v6_simulation_rendered_text = ""
    if active_v6 and conjecture_context_plan is not None:
        from deepreason.scratch.conjecture import render_v6_conjecture_context

        try:
            v6_scratch_rendered_text, scratch_aliases = render_v6_conjecture_context(
                conjecture_context_plan
            )
            canonical_scratch_text = conjecture_context_plan.rendered_context.text
            if pack.count(canonical_scratch_text) != 1:
                raise ValueError(
                    "v6 Conj pack must contain canonical scratch context once"
                )
            pack = pack.replace(canonical_scratch_text, v6_scratch_rendered_text, 1)
        except Exception:
            abandon_v6_context_preissue()
            raise

    if active_v6:
        simulation_policy = run_manifest.inquiry_capability_policy.simulation
        if simulation_policy.enabled and simulation_policy.input_catalog:
            sealed_lines = [
                "",
                "SEALED SIMULATION INPUTS (data only; use only the listed SIM handles):",
            ]
            for alias, item in zip(
                transaction_simulation_aliases,
                simulation_policy.input_catalog,
                strict=True,
            ):
                sealed_lines.append(
                    f"{alias}: {item.description}\n" + canonical_json(item.value).decode("utf-8")
                )
            v6_simulation_rendered_text = "\n".join(sealed_lines)
            pack += v6_simulation_rendered_text
        if control.scratch_authoring.enabled:
            pack += "\n\n" + V6_SCRATCH_WORKSHOP_PROMPT
        source_values = list(harness.state.artifacts)
        if dossier_receipt is not None:
            source_values.extend(dossier_receipt.selected_source_ids)
        source_values = list(dict.fromkeys(value for value in source_values if value in pack))
        aliases = AliasTable(
            {f"SRC_{index:03d}": value for index, value in enumerate(source_values, 1)}
        )
    else:
        aliases = aliases_for_pack(pack, harness.state.artifacts, prefix="A")
    reasoning = any(
        harness.commitments[commitment_id].eval == "program:reasoning-envelope-wf"
        for commitment_id in problem.criteria
        if commitment_id in harness.commitments
    )
    output_model = (
        ReasoningConjecturerTurnV6
        if active_v6 and reasoning
        else ConjectureTurnV6
        if active_v6
        else ReasoningConjecturerTurnV5
        if active_v5 and reasoning
        else ConjecturerTurnV5
        if active_v5
        else ReasoningConjecturerTurnV4
        if active_v4 and reasoning
        else ConjecturerTurnV4
        if active_v4
        else ReasoningConjecturerOutput
        if reasoning
        else ConjecturerOutput
    )
    context_receipt = None
    if conjecture_context_plan is not None and not active_v6:
        from deepreason.scratch.conjecture import commit_conjecture_context
        from deepreason.scratch.service import ScratchService

        context_receipt = commit_conjecture_context(
            ScratchService(harness),
            conjecture_context_plan,
            final_conjecture_pack=pack,
            attention_policy=conjecture_context_plan.attention_policy,
        )
    if active_v6:
        simulation_policy = run_manifest.inquiry_capability_policy.simulation
        turn_contract = ConjecturerTurnWireContractV6(
            reasoning=reasoning,
            aliases=aliases,
            scratch_aliases=scratch_aliases,
            permitted_retrieval_channels=context_policy.permitted_retrieval_channels,
            simulation_enabled=simulation_policy.enabled,
            maximum_simulation_proposals=(
                simulation_policy.maximum_proposals_per_turn if simulation_policy.enabled else 0
            ),
            simulation_input_aliases=transaction_simulation_aliases,
            scratch_authoring_policy=control.scratch_authoring,
        )
    elif active_v4:
        turn_contract = (
            ConjecturerTurnWireContractV5 if active_v5 else ConjecturerTurnWireContractV4
        )(
            reasoning=reasoning,
            aliases=aliases,
            scratch_aliases=(
                {
                    **dict(conjecture_context_plan.rendered_context.receipt.block_handles),
                    **dict(conjecture_context_plan.rendered_context.receipt.cluster_handles),
                    **dict(conjecture_context_plan.rendered_context.receipt.link_handles),
                    **dict(conjecture_context_plan.rendered_context.receipt.guide_handles),
                }
                if conjecture_context_plan is not None
                else {}
            ),
            permitted_retrieval_channels=(
                context_policy.permitted_retrieval_channels if context_policy is not None else ()
            ),
            **(
                {
                    "maximum_simulation_proposals": (
                        run_manifest.inquiry_capability_policy.simulation.maximum_proposals_per_turn
                        if run_manifest.inquiry_capability_policy.simulation.enabled
                        else 0
                    )
                }
                if active_v5
                else {}
            ),
        )
    else:
        turn_contract = None

    endpoint_index = dispatch_endpoint_lease.seat if dispatch_endpoint_lease is not None else 0
    transaction_plans = []
    if active_v6:
        from deepreason.workflow.transaction import (
            ContextNamespace,
            VisibleContextItemV1,
        )

        def context_digest(value: str) -> str:
            digest = value.removeprefix("sha256:")
            if re.fullmatch(r"[0-9a-f]{64}", digest):
                return digest
            return hashlib.sha256(value.encode("utf-8")).hexdigest()

        if scratch_aliases and v6_scratch_rendered_text is not None:
            rendered_bytes = len(v6_scratch_rendered_text.encode("utf-8"))
            scratch_items = tuple(
                VisibleContextItemV1(
                    namespace=ContextNamespace.SCRATCH,
                    alias=alias,
                    object_ref=target,
                    content_sha256=context_digest(target),
                    planned_bytes=rendered_bytes,
                )
                for alias, target in scratch_aliases.items()
            )
            transaction_plans.append(
                transaction_service.context_plan(
                    transaction_preparation,
                    plan_kind="scratch",
                    items=scratch_items,
                    maximum_bytes=rendered_bytes,
                    rendered_bytes=rendered_bytes,
                )
            )
        dossier_source_ids = {
            excerpt.source_id
            for excerpt in (dossier_receipt.excerpts if dossier_receipt is not None else ())
        }
        formal_items = tuple(
            (
                alias,
                target,
                harness.state.artifacts[target].content_ref,
            )
            for alias, target in aliases.aliases.items()
            if target in harness.state.artifacts and target not in dossier_source_ids
        )
        if formal_items:
            rendered_bytes = sum(
                len(content.encode("utf-8")) for _alias, _target, content in formal_items
            )
            transaction_plans.append(
                transaction_service.context_plan(
                    transaction_preparation,
                    plan_kind="combined",
                    items=tuple(
                        VisibleContextItemV1(
                            namespace=ContextNamespace.SOURCE,
                            alias=alias,
                            object_ref=target,
                            content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                            planned_bytes=len(content.encode("utf-8")),
                        )
                        for alias, target, content in formal_items
                    ),
                    maximum_bytes=rendered_bytes,
                    rendered_bytes=rendered_bytes,
                )
            )
        if dossier_receipt is not None and dossier_receipt.excerpts:
            alias_for_source = {target: alias for alias, target in aliases.aliases.items()}
            rendered_bytes = len(frozen_evidence_context.encode("utf-8"))
            dossier_items = tuple(
                VisibleContextItemV1(
                    namespace=ContextNamespace.SOURCE,
                    alias=alias_for_source[excerpt.source_id],
                    object_ref=excerpt.source_id,
                    content_sha256=excerpt.excerpt_sha256,
                    planned_bytes=rendered_bytes,
                )
                for excerpt in dossier_receipt.excerpts
            )
            transaction_plans.append(
                transaction_service.context_plan(
                    transaction_preparation,
                    plan_kind="dossier",
                    items=dossier_items,
                    maximum_bytes=max(dossier_maximum_bytes, rendered_bytes),
                    rendered_bytes=rendered_bytes,
                )
            )
        if simulation_policy.enabled and simulation_policy.input_catalog:
            rendered_bytes = len(v6_simulation_rendered_text.encode("utf-8"))
            simulation_items = tuple(
                VisibleContextItemV1(
                    namespace=ContextNamespace.SIMULATION,
                    alias=alias,
                    object_ref=item.alias,
                    content_sha256=item.content_sha256,
                    planned_bytes=rendered_bytes,
                )
                for alias, item in zip(
                    transaction_simulation_aliases,
                    simulation_policy.input_catalog,
                    strict=True,
                )
            )
            transaction_plans.append(
                transaction_service.context_plan(
                    transaction_preparation,
                    plan_kind="simulation",
                    items=simulation_items,
                    maximum_bytes=max(
                        simulation_policy.maximum_input_bytes,
                        rendered_bytes,
                    ),
                    rendered_bytes=rendered_bytes,
                )
            )
        if transaction_capability_result_ref is not None:
            assert transaction_capability_result_package_ref is not None
            assert transaction_capability_result_alias is not None
            assert v6_capability_result_context is not None
            rendered_bytes = len(v6_capability_result_context.encode("utf-8"))
            transaction_plans.append(
                transaction_service.context_plan(
                    transaction_preparation,
                    plan_kind="simulation_result",
                    items=(
                        VisibleContextItemV1(
                            namespace=ContextNamespace.SIMULATION,
                            alias=transaction_capability_result_alias,
                            object_ref=transaction_capability_result_package_ref,
                            content_sha256=transaction_capability_result_ref,
                            planned_bytes=rendered_bytes,
                        ),
                    ),
                    maximum_bytes=rendered_bytes,
                    rendered_bytes=rendered_bytes,
                )
            )
        if conjecture_context_plan is not None:
            from deepreason.scratch.conjecture import (
                commit_conjecture_context,
                prepare_conjecture_context_call,
            )
            from deepreason.scratch.service import ScratchService

            previewed_request = []

            def validate_context_call_receipt(receipt):
                preview = adapter.preview_request(
                    "conjecturer",
                    pack,
                    output_model,
                    endpoint_index=endpoint_index,
                    aliases=aliases,
                    wire_contract=turn_contract,
                    endpoint_lease=dispatch_endpoint_lease,
                    conjecture_context=receipt,
                )
                if preview[1] is not turn_contract or preview[2] != dispatch_endpoint_lease:
                    raise ValueError("v6 conjecture preview changed frozen call authority")
                previewed_request.append(preview)

            try:
                context_receipt = prepare_conjecture_context_call(
                    ScratchService(harness),
                    conjecture_context_plan,
                    final_conjecture_pack=pack,
                    attention_policy=conjecture_context_plan.attention_policy,
                    model_facing_rendered_context=v6_scratch_rendered_text,
                    model_facing_aliases=scratch_aliases,
                    validate_call_receipt=validate_context_call_receipt,
                )
            except RequestEnvelopeExceeded:
                abandon_v6_context_preissue("request_envelope_exceeded")
                return []
            except Exception:
                abandon_v6_context_preissue()
                raise
            (
                prompt,
                preview_contract,
                preview_lease,
                maximum_tokens,
            ) = previewed_request[0]
        else:
            try:
                prompt, preview_contract, preview_lease, maximum_tokens = (
                    adapter.preview_request(
                        "conjecturer",
                        pack,
                        output_model,
                        endpoint_index=endpoint_index,
                        aliases=aliases,
                        wire_contract=turn_contract,
                        endpoint_lease=dispatch_endpoint_lease,
                        conjecture_context=None,
                    )
                )
            except RequestEnvelopeExceeded:
                abandon_v6_context_preissue("request_envelope_exceeded")
                return []
        if preview_contract is not turn_contract or preview_lease != dispatch_endpoint_lease:
            raise ValueError("v6 conjecture preview changed frozen call authority")
        from deepreason.workflow.transaction import WorkBudgetDenied

        try:
            if conjecture_context_plan is not None:
                reserved_dispatch = transaction_service.reserve_dispatch(
                    transaction_preparation,
                    prompt=prompt,
                    max_tokens=maximum_tokens,
                )
            else:
                transaction_authorization = transaction_service.issue(
                    transaction_preparation,
                    plans=transaction_plans,
                    prompt=prompt,
                    max_tokens=maximum_tokens,
                )
        except WorkBudgetDenied:
            if v6_context_continuation is not None:
                return []
            raise
        if conjecture_context_plan is not None:
            try:
                committed_receipt = commit_conjecture_context(
                    ScratchService(harness),
                    conjecture_context_plan,
                    final_conjecture_pack=pack,
                    attention_policy=conjecture_context_plan.attention_policy,
                    model_facing_rendered_context=v6_scratch_rendered_text,
                    model_facing_aliases=scratch_aliases,
                    prepared_call_receipt=context_receipt,
                )
                if committed_receipt != context_receipt:
                    raise ValueError(
                        "committed v6 context differs from prepared call authority"
                    )
                transaction_authorization = transaction_service.finalize_dispatch(
                    reserved_dispatch,
                    plans=transaction_plans,
                    prompt=prompt,
                )
            except Exception:
                reserved_dispatch.release()
                abandon_v6_context_preissue()
                raise

    transaction_context_authorization = transaction_authorization

    try:
        output, llm_call = adapter.call(
            "conjecturer",
            pack,
            output_model,
            endpoint_index=endpoint_index,
            aliases=aliases,
            wire_contract=turn_contract,
            endpoint_lease=dispatch_endpoint_lease,
            school_id=execution_school_id,
            conjecture_context=context_receipt,
            work_order_id=workflow_work_order_id,
            workflow_dispatch_observer=(
                workflow_control_trace.authorize_dispatch
                if workflow_control_trace is not None
                else None
            ),
            workflow_repair_observer=(
                workflow_control_trace.record_repair_request
                if workflow_control_trace is not None
                else None
            ),
            workflow_dispatch_required=active_v4,
            dispatch_authorization=transaction_authorization,
        )
    except (WorkflowAuthorizationError, RouteFirewallError) as error:
        if not active_v6 or getattr(error, "spend", None) is not None:
            raise
        if transaction_authorization.reservation.is_open:
            transaction_authorization.release()
        transaction_service.terminate(
            work_id=transaction_preparation.id,
            attempt_index=transaction_preparation.attempt_index,
            status="abandoned",
            reason_code="provider_predispatch_authority_failed",
            usage_status="exact",
            prompt_tokens=0,
            completion_tokens=0,
        )
        error.transaction_terminalized = True
        raise
    except EndpointError as error:
        if not active_v6:
            raise
        spend = getattr(error, "spend", None)
        if spend is None:
            raise
        diagnostic_ref = spend.attempt_trace[-1].diagnostic_ref if spend.attempt_trace else None
        if diagnostic_ref is None:
            raise
        transaction_provider_attempt = transaction_service.record_provider_attempt(
            transaction_authorization,
            call=spend,
            outcome="transport_failure",
            usage_status="unknown",
            diagnostic_ref=diagnostic_ref,
        )
        transaction_service.terminate(
            work_id=transaction_preparation.id,
            attempt_index=transaction_preparation.attempt_index,
            status="transport_failed",
            reason_code="provider_transport_failure",
            usage_status="unknown",
            provider_attempt=transaction_provider_attempt,
        )
        error.spend = None
        error.transaction_terminalized = True
        raise
    except SchemaRepairError as error:
        if not active_v6:
            raise
        try:
            repaired = transaction_service.repair_schema_failure(
                adapter=adapter,
                authorized=transaction_authorization,
                error=error,
                role="conjecturer",
                pack=pack,
                output_model=output_model,
                wire_contract=turn_contract,
                endpoint_index=endpoint_index,
                endpoint_lease=dispatch_endpoint_lease,
                school_id=execution_school_id,
                reason_prefix="conjecture",
            )
        except SchemaRepairError as exhausted:
            source_work_id = getattr(exhausted, "source_work_id", None)
            if not isinstance(source_work_id, str):
                raise
            from deepreason.run_manifest import (
                RunManifestError,
                resolve_route_seat_contract_decomposition,
            )

            try:
                decomposition_grant = resolve_route_seat_contract_decomposition(
                    run_manifest,
                    role="conjecturer",
                    seat=dispatch_endpoint_lease.seat,
                    endpoint_id=dispatch_endpoint_lease.route.endpoint_id,
                    route_sha256=route_ref.route_sha256,
                    source_contract_id="conjecturer.turn.v6",
                )
            except RunManifestError as authority_error:
                if authority_error.code in {
                    "V6_CONTRACT_DECOMPOSITION_AUTHORITY_REQUIRED",
                    "V6_CONTRACT_DECOMPOSITION_GRANT_REQUIRED",
                }:
                    # The strong work is already durably schema-exhausted.
                    # Absence of a separately frozen edge authorizes no
                    # additional provider work and preserves that terminal.
                    raise exhausted
                raise
            transition = harness.activate_contract_decomposition(
                run_manifest,
                source_work_id,
                child_contexts=tuple(
                    (f"candidate-slot-{index:03d}", pack)
                    for index in range(decomposition_grant.maximum_children)
                ),
            )
            atomic_decomposition_transition = transition
            output, atomic_calls = _v6_atomic_conjecture_fallback(
                harness,
                adapter,
                run_manifest,
                endpoint_lease=dispatch_endpoint_lease,
                school_id=execution_school_id,
                problem=problem,
                strong_payload=payload,
                pack=pack,
                aliases=aliases,
                exposure_items=tuple(
                    transaction_context_authorization.exposure_receipt.exposed_items
                ),
                transition=transition,
            )
            llm_call = atomic_calls[-1]
            atomic_fallback_completed = True
            matching_events = [
                event.seq for event in harness.log.read() if event.llm == llm_call
            ]
            if len(matching_events) != 1:
                raise RuntimeError("atomic conjecture call lacks one durable event")
            atomic_source_call_seq = matching_events[0]
        else:
            output = repaired.output
            llm_call = repaired.llm_call
            transaction_preparation = repaired.preparation
            transaction_authorization = repaired.authorized
            transaction_provider_attempt = repaired.provider_attempt

    if active_v6 and transaction_provider_attempt is None and not atomic_fallback_completed:
        transaction_provider_attempt = transaction_service.record_provider_attempt(
            transaction_authorization,
            call=llm_call,
            outcome="provider_result",
            usage_status="exact",
        )
    bound_work_order_id = llm_call.work_order_id
    source_call_seq = None
    if active_v6:
        source_call_seq = (
            atomic_source_call_seq
            if atomic_fallback_completed
            else harness._next_seq - 1
        )
    elif active_v4 or bound_work_order_id is not None:
        extra = (f"school:{execution_school_id}",) if execution_school_id is not None else ()
        harness.record_llm_calls(
            [llm_call],
            ("conjecture-turn-call" if active_v4 else "workflow-conjecture-call"),
            problem_id,
            *((f"manifest:{run_manifest.sha256}",) if active_v4 else ()),
            *extra,
        )
        source_call_seq = harness._next_seq - 1
    request = output.context_request if active_v4 or active_v6 else None
    abstention = output.abstention if active_v4 or active_v6 else None
    simulation_drafts = output.simulation_proposals if active_v5 or active_v6 else ()
    request_ref = (
        harness.blobs.put(canonical_json(request.model_dump(mode="json", exclude_none=True)))
        if request is not None
        else None
    )
    abstention_ref = (
        harness.blobs.put(canonical_json(abstention.model_dump(mode="json", exclude_none=True)))
        if abstention is not None
        else None
    )
    # Level-2 transmission diagnostic (attention/reporting only, §0): did
    # candidate k actually realize spec k? Logged as a replayable Measure.
    if specs and embedder is not None:
        from deepreason.llm.specs import transmission_score

        proposal_text = [
            getattr(candidate, "content", None) or getattr(candidate, "claim", "")
            for candidate in output.candidates
        ]
        score = transmission_score(specs, proposal_text, embedder)
        if score is not None:
            harness.record_measure(inputs=[f"spec-transmission:{score:.4f}", problem_id])

    candidate_rows: list[tuple[ConjectureCandidate, tuple, str]] = []
    if reasoning:
        # Selection is attention-only, so it must happen before drafting
        # countercondition commitments. Drafts are pure Commitment objects
        # (RC5): nothing reaches the append-only registry until the
        # candidate is gate-admitted.
        proposals = list(output.candidates)
        if tail_weighted:
            proposals.sort(key=lambda proposal: proposal.typicality)
        for proposal in proposals[: config.VS_K]:
            # Containment backstop (live_smoke_v1 finding F1): a proposal
            # that passed the wire schema but cannot compile into an
            # envelope is skipped with a logged measure — model output must
            # never crash the loop. The wire schema mirrors the envelope
            # constraints, so this path only fires on future schema drift.
            try:
                envelope = proposal_envelope(proposal)
            except (ValidationError, ValueError) as error:
                harness.record_measure(inputs=["proposal-envelope-invalid", type(error).__name__])
                continue
            content = envelope_json(envelope)
            compiled = tuple(draft_countercondition_commitments(envelope))
            candidate_rows.append(
                (
                    ConjectureCandidate(
                        content=content,
                        typicality=proposal.typicality,
                        refs=[
                            CandidateRef(target=target, role="mention")
                            for target in proposal.optional_refs
                        ],
                    ),
                    compiled,
                    proposal.sidecar.search_signal,
                )
            )
    else:
        proposals = list(output.candidates)
        if tail_weighted:  # stagnation response (§11.4): fund the atypical tail
            proposals.sort(key=lambda proposal: proposal.typicality)
        candidate_rows = [(candidate, (), "productive") for candidate in proposals[: config.VS_K]]

    # Compile semantic candidates first, without running a guard or touching
    # the registry.  C1 can then record the provider receipt at the real
    # response boundary, before any admission decision is enacted.
    prepared_rows = []
    occurrences: dict[str, int] = {}
    family = root_problem_family(harness.state, problem.id)
    for candidate, draft_pool, search_signal in candidate_rows:
        base = mandatory_interface or MandatoryInterface()
        candidate_mandatory = MandatoryInterface(
            commitments=tuple(
                dict.fromkeys((*base.commitments, *(item.id for item in draft_pool)))
            ),
            refs=base.refs,
        )
        # Two-phase compilation (RC5): the draft interface plus unregistered
        # Commitment objects; nothing touches the registry before admission.
        interface, draft = compile_interface_draft(
            harness,
            problem,
            candidate.content,
            mandatory=candidate_mandatory,
            optional_refs=((ref.target, ref.role) for ref in candidate.refs),
            draft_commitments=draft_pool,
        )
        content_ref = f"inline:{candidate.content}"
        artifact = Artifact(
            id=Artifact.compute_id(content_ref, "utf8", interface),
            content_ref=content_ref,
            codec="utf8",
            interface=interface,
            provenance=Provenance(
                role="conjecturer",
                school=school["id"] if school else None,
                event_seq=harness._next_seq,
            ),
        )
        occurrences[artifact.id] = occurrences.get(artifact.id, 0) + 1
        occurrence = occurrences[artifact.id]
        disposition_ref = (
            artifact.id if occurrence == 1 else f"{artifact.id}#occurrence-{occurrence}"
        )
        prepared_rows.append(
            (
                disposition_ref,
                artifact,
                tuple(draft),
                candidate_mandatory,
                candidate,
                search_signal,
            )
        )

    if (
        workflow_control_trace is not None
        and source_call_seq is not None
        and bound_work_order_id is not None
    ):
        workflow_control_trace.record_provider_result(
            source_call_seq=source_call_seq,
            llm_call=llm_call,
            candidate_refs=tuple(row[0] for row in prepared_rows),
            context_request_hash=(request.request_hash if request is not None else None),
            context_request_ref=request_ref,
            abstention_hash=(abstention.abstention_hash if abstention is not None else None),
            abstention_ref=abstention_ref,
        )

    context_turn_payload = None
    context_granted = False
    context_common = None
    prior_selection = context_receipt.selection_receipt_ref if context_receipt is not None else None
    if active_v4 and request is not None:
        assert request_ref is not None
        workflow_control_trace.record_context_request()
        context_common = {
            "manifest_digest": run_manifest.sha256,
            "problem_id": problem_id,
            "school_id": execution_school_id,
            "source_call_seq": source_call_seq,
            "maximum_expansions": context_policy.max_context_expansion_requests,
            "request_hash": request.request_hash,
            "request_ref": request_ref,
            "prior_selection_receipt_ref": prior_selection,
        }
        desired = {channel.value for channel in request.desired_retrieval_channels}
        permitted = set(context_policy.permitted_retrieval_channels)
        denial = None
        denial_action = ConjectureTurnAction.CONTEXT_DENIED
        if desired - permitted:
            denial = "channel_not_permitted"
        elif context_policy.mode != "harness_plus_model_request":
            denial = "capability_not_granted"
        elif _context_expansion_index >= context_policy.max_context_expansion_requests:
            denial = "request_limit_reached"
            denial_action = ConjectureTurnAction.CONTEXT_EXHAUSTED

        if denial is None:
            from deepreason.scratch.conjecture import plan_conjecture_context_expansion
            from deepreason.scratch.service import ScratchService

            expansion_number = _context_expansion_index + 1
            proposed = ConjectureTurnEventPayloadV1.create(
                action=ConjectureTurnAction.CONTEXT_GRANTED,
                expansion_index=expansion_number,
                reason_code="granted",
                **context_common,
            )
            fence = harness._next_seq - 1
            dry_plan = plan_conjecture_context_expansion(
                ScratchService(harness),
                problem=problem,
                school_id=execution_school_id,
                manifest_digest=run_manifest.sha256,
                scratch_policy=scratch_policy,
                context_policy=context_policy,
                request=request,
                prior_plan=conjecture_context_plan,
                expansion_decision_ref=proposed.decision_id,
                expansion_index=expansion_number,
                formal_fence_seq=fence,
                scratch_fence_seq=fence,
            )
            if dry_plan is None:
                prior_count = (
                    len(conjecture_context_plan.attention_pack.blocks)
                    if conjecture_context_plan is not None
                    else 0
                )
                root_count = (
                    len(
                        conjecture_context_plan.root_block_ids
                        if conjecture_context_plan.root_block_ids is not None
                        else conjecture_context_plan.attention_pack.selection_receipt.final_order
                    )
                    if conjecture_context_plan is not None
                    else 0
                )
                total_cap = min(
                    scratch_policy.attention_policy().max_blocks_per_pack,
                    root_count + context_policy.max_extra_blocks,
                )
                denial = (
                    "no_context_capacity" if total_cap <= prior_count else "no_additional_context"
                )
            else:
                context_turn_payload = proposed
                context_granted = True

        if context_turn_payload is None:
            context_turn_payload = ConjectureTurnEventPayloadV1.create(
                action=denial_action,
                expansion_index=_context_expansion_index,
                reason_code=denial,
                **context_common,
            )
        workflow_control_trace.record_context_decision(
            granted=context_granted,
            trigger_ref=context_turn_payload.decision_id,
        )

    batch: list[tuple[Artifact, list[Warrant]]] = []
    candidate_domains: dict[str, anti_relapse.RelapseDomain] = {}
    admitted_drafts = {}
    seen: set[str] = set()
    for (
        _disposition_ref,
        artifact,
        draft,
        candidate_mandatory,
        candidate,
        search_signal,
    ) in prepared_rows:
        # Gate first (spec §3): a refuted-equivalent is a block, not a dedupe.
        effective_workload = "text" if reasoning else workload_profile
        effective_contract = (
            (
                "conjecturer.atomic-candidate.v1"
                if atomic_fallback_completed
                else "conjecturer.turn.v6"
            )
            if active_v6
            else ("conjecturer.turn.v5" if active_v5 else "conjecturer.turn.v4")
            if active_v4
            else "reasoning.conjecturer.compact.v2"
            if reasoning
            else contract_id
        )
        overlay = {
            **harness.commitments,
            **admitted_drafts,
            **{item.id: item for item in draft},
        }
        domain = (
            anti_relapse.relapse_domain(
                artifact,
                harness,
                workload_profile=effective_workload,
                problem_family=family,
                contract_id=effective_contract,
                mandatory_refs=candidate_mandatory.domain_refs(),
                component_spec=component_spec,
                theorem_interface=theorem_interface,
                commitments=overlay,
            )
            if effective_workload is not None
            else None
        )
        admitted, reason = anti_relapse.check(
            artifact,
            [],
            harness,
            embedder=embedder,
            near_dup_eps=config.NEAR_DUP_EPS,
            domain=domain,
            commitments=overlay,
        )
        if diagnostics is not None:
            diagnostic = {
                "candidate": artifact.id[:12],
                "gate": reason,
                "search_signal": search_signal,
            }
            if capture_candidate_content:
                # Experimental observation only.  The default keeps the
                # historical diagnostic shape and prompt/actuation path.
                diagnostic["artifact_id"] = artifact.id
                diagnostic["candidate_content"] = candidate.content
            diagnostics.append(diagnostic)
        if not admitted:
            observe_candidate(artifact.id, "reject", reason)
            # Persist the block (stress campaign T7 finding): gate decisions
            # were in-memory only, so a finished run could not be audited for
            # block counts — violating log-as-source-of-truth. A Measure is
            # the right vehicle: attention/diagnostic, never a status. The
            # blocked candidate registers NO commitments and emits NO
            # Register events (RC5); the gate's operational receipt names
            # the prior's refuters for a later explicit challenge.
            harness.record_measure(inputs=[f"gate:{reason}", artifact.id, problem_id])
            continue
        if artifact.id in seen or artifact.id in harness.state.artifacts:
            observe_candidate(
                artifact.id,
                "deduplicate",
                "content-duplicate",
            )
            continue  # attention-level dedupe of a registered twin — never a block (§0)
        # Keep drafts process-local until the code-authored C1 guard receipt
        # is durable; this prevents formal admission from preceding authority.
        for commitment in draft:
            admitted_drafts[commitment.id] = commitment
        seen.add(artifact.id)
        batch.append((artifact, []))
        observe_candidate(artifact.id, "admit", "passed")
        if domain is not None:
            candidate_domains[artifact.id] = domain

    # Persist the code-authored disposition before any commitment or artifact
    # becomes formal.  A crash can therefore never leave a semantic admission
    # whose authority trace is still only process-local.
    if workflow_control_trace is not None and workflow_guard_findings:
        workflow_control_trace.record_guard(workflow_guard_findings)
    if active_v4:
        # A request-only, abstention, exhausted, or otherwise candidate-free
        # turn still closes its one-call work. Guarded candidate work is
        # already terminal, so this is an idempotent no-op in that case.
        workflow_control_trace.finish()

    component_diagnostic_refs: list[str] = []
    scratch_proposal = None
    scratch_author = None
    simulation_controller = None
    staged_simulation_refs: tuple[str, ...] = ()
    if active_v6:
        exposure_ref = transaction_context_authorization.exposure_receipt.id
        scratch_proposal = getattr(output, "scratch_proposal", None)
        if scratch_proposal is not None:
            from deepreason.scratch.authoring import (
                ScratchAuthoringError,
                ScratchAuthoringService,
            )
            from deepreason.scratch.service import ScratchService

            scratch_author = ScratchAuthoringService(
                ScratchService(harness),
                adapter,
            )
            try:
                scratch_proposal, _resolved = scratch_author.validate_proposal(
                    scratch_proposal,
                    policy=control.scratch_authoring,
                    visible_aliases=scratch_aliases,
                    context_ref=exposure_ref,
                )
            except (ScratchAuthoringError, ValueError) as error:
                component_diagnostic_refs.append(
                    _v6_component_diagnostic(
                        harness,
                        component="scratch",
                        phase="semantic_validation",
                        error=error,
                    )
                )
                scratch_proposal = None

        if simulation_drafts:
            from deepreason.capabilities.simulation import (
                SimulationCapabilityController,
            )

            simulation_controller = SimulationCapabilityController(
                harness,
                run_manifest,
            )
            try:
                staged = simulation_controller.stage_transactional_proposals(
                    tuple(simulation_drafts),
                    preparation=transaction_preparation,
                    provider_attempt=transaction_provider_attempt,
                    source_call_seq=source_call_seq,
                )
                staged_simulation_refs = tuple(proposal.id for proposal in staged)
            except Exception as error:
                diagnostic_ref = _v6_component_diagnostic(
                    harness,
                    component="simulation",
                    phase="semantic_validation",
                    error=error,
                )
                admission = transaction_service.record_semantic_admission(
                    transaction_provider_attempt,
                    outcome="rejected",
                    diagnostic_refs=tuple(
                        dict.fromkeys((*component_diagnostic_refs, diagnostic_ref))
                    ),
                )
                transaction_service.terminate(
                    work_id=transaction_preparation.id,
                    attempt_index=transaction_preparation.attempt_index,
                    status="rejected",
                    reason_code="simulation_semantic_rejected",
                    usage_status="exact",
                    prompt_tokens=llm_call.prompt_tokens,
                    completion_tokens=llm_call.completion_tokens,
                    provider_attempt=transaction_provider_attempt,
                    admission=admission,
                )
                return []

    # Formal semantics remain the existing RC5 path after the durable guard.
    for commitment in admitted_drafts.values():
        harness.register_commitment(commitment)
    if batch:
        batch = [
            (
                artifact.model_copy(
                    update={
                        "provenance": artifact.provenance.model_copy(
                            update={"event_seq": harness._next_seq}
                        )
                    }
                ),
                warrants,
            )
            for artifact, warrants in batch
        ]
    for artifact, _warrants in batch:
        if artifact.id in candidate_domains:
            anti_relapse.record_domain(harness, artifact.id, candidate_domains[artifact.id])
    registered = harness.register_batch(
        batch,
        problem_id=problem_id,
        rule=Rule.CONJ,
        llm=None if source_call_seq is not None else llm_call,
        process_inputs=(
            (f"conjecture-call:{source_call_seq}",) if source_call_seq is not None else ()
        ),
    )
    if not registered:
        # All candidates gate-blocked or deduped => no Conj event committed;
        # the gamma call still spent tokens and must reach the log once (§0).
        extra = (f"school:{execution_school_id}",) if execution_school_id is not None else ()
        if source_call_seq is None:
            harness.record_llm_calls([llm_call], "conj-noregister", *extra)
    if active_v6 and atomic_fallback_completed:
        harness.complete_contract_decomposition(
            run_manifest,
            atomic_decomposition_transition,
            admitted_effect_refs=tuple(artifact.id for artifact in registered),
        )
        return registered
    if active_v6:
        scratch_output_refs = ()
        if scratch_proposal is not None:
            assert scratch_author is not None
            try:
                scratch_output_refs = scratch_author.admit_proposal(
                    scratch_proposal,
                    policy=control.scratch_authoring,
                    visible_aliases=scratch_aliases,
                    context_ref=exposure_ref,
                )
            except Exception as error:
                scratch_output_refs = _v6_scratch_effect_refs(
                    harness,
                    exposure_ref,
                )
                component_diagnostic_refs.append(
                    _v6_component_diagnostic(
                        harness,
                        component="scratch",
                        phase="materialization",
                        error=error,
                        partial_refs=scratch_output_refs,
                    )
                )

        simulation_output_refs = ()
        if simulation_drafts:
            assert simulation_controller is not None
            try:
                simulation_output_refs = simulation_controller.materialize_transactional_proposals(
                    tuple(simulation_drafts),
                    preparation=transaction_preparation,
                    provider_attempt=transaction_provider_attempt,
                    source_call_seq=source_call_seq,
                )
                if simulation_output_refs != staged_simulation_refs:
                    raise ValueError("simulation materialization differs from its staged batch")
            except Exception as error:
                simulation_output_refs = _v6_simulation_effect_refs(
                    harness,
                    work_id=transaction_preparation.id,
                    provider_attempt_ref=transaction_provider_attempt.id,
                )
                component_diagnostic_refs.append(
                    _v6_component_diagnostic(
                        harness,
                        component="simulation",
                        phase="materialization",
                        error=error,
                        partial_refs=simulation_output_refs,
                    )
                )

        semantic_output_ref = harness.blobs.put(
            canonical_json(
                output.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                )
            )
        )
        admitted_refs = tuple(
            dict.fromkeys(
                (
                    semantic_output_ref,
                    *(artifact.id for artifact in registered),
                    *scratch_output_refs,
                    *simulation_output_refs,
                )
            )
        )
        component_diagnostic_refs = list(dict.fromkeys(component_diagnostic_refs))
        admission = transaction_service.record_semantic_admission(
            transaction_provider_attempt,
            outcome="admitted",
            admitted_refs=admitted_refs,
            diagnostic_refs=tuple(component_diagnostic_refs),
        )
        transaction_service.terminate(
            work_id=transaction_preparation.id,
            attempt_index=transaction_preparation.attempt_index,
            status="completed",
            reason_code=(
                "semantic_admission_partial"
                if component_diagnostic_refs
                else "semantic_admission_complete"
            ),
            usage_status="exact",
            prompt_tokens=llm_call.prompt_tokens,
            completion_tokens=llm_call.completion_tokens,
            provider_attempt=transaction_provider_attempt,
            admission=admission,
        )
        if request is None:
            return registered
        assert request_ref is not None
        assert source_call_seq is not None
        from deepreason.workflow.context_continuation import (
            ConjectureContextContinuationV1,
            context_plan_sha256,
        )

        prior_selection_ref = (
            conjecture_context_plan.attention_pack.selection_receipt.id
            if conjecture_context_plan is not None
            else None
        )
        continuation = ConjectureContextContinuationV1.create(
            manifest_digest=run_manifest.sha256,
            problem_id=problem.id,
            school_id=execution_school_id,
            parent_work_id=transaction_preparation.id,
            parent_attempt_index=transaction_provider_attempt.attempt_index,
            parent_provider_attempt_ref=transaction_provider_attempt.id,
            parent_exposure_receipt_ref=(transaction_context_authorization.exposure_receipt.id),
            parent_semantic_admission_ref=admission.id,
            parent_semantic_output_ref=semantic_output_ref,
            parent_provider_event_seq=source_call_seq,
            request_hash=request.request_hash,
            request_ref=request_ref,
            expansion_index=_context_expansion_index + 1,
            maximum_expansions=context_policy.max_context_expansion_requests,
            maximum_extra_blocks=context_policy.max_extra_blocks,
            policy_mode=context_policy.mode,
            permitted_retrieval_channels=(context_policy.permitted_retrieval_channels),
            desired_retrieval_channels=tuple(
                channel.value for channel in request.desired_retrieval_channels
            ),
            prior_selection_receipt_ref=prior_selection_ref,
            prior_context_plan_sha256=context_plan_sha256(conjecture_context_plan),
        )
        follow_up = conj(
            harness,
            problem_id,
            adapter,
            config,
            diagnostics,
            school=school,
            tail_weighted=tail_weighted,
            complement=complement,
            specs=specs,
            embedder=embedder,
            mandatory_interface=mandatory_interface,
            workload_profile=workload_profile,
            contract_id=contract_id,
            component_spec=component_spec,
            theorem_interface=theorem_interface,
            generation_context=generation_context,
            suppressed_exemplars=suppressed_exemplars,
            capture_candidate_content=capture_candidate_content,
            endpoint_lease=endpoint_lease,
            execution_school_id=execution_school_id,
            run_manifest=run_manifest,
            _context_expansion_index=_context_expansion_index + 1,
            candidate_observer=candidate_observer,
            _capability_result_context=_capability_result_context,
            _capability_result_package_ref=_capability_result_package_ref,
            _capability_result_context_ref=_capability_result_context_ref,
            _simulation_follow_up_index=_simulation_follow_up_index,
            _v6_context_continuation=continuation,
            _v6_context_request=request,
            _v6_prior_context_plan=conjecture_context_plan,
        )
        return [*registered, *follow_up]
    if not active_v4:
        return registered

    assert source_call_seq is not None
    if abstention is not None:
        assert abstention_ref is not None
        harness.record_conjecture_turn_event(
            ConjectureTurnEventPayloadV1.create(
                action=ConjectureTurnAction.ABSTAINED,
                manifest_digest=run_manifest.sha256,
                problem_id=problem_id,
                school_id=execution_school_id,
                source_call_seq=source_call_seq,
                expansion_index=_context_expansion_index,
                maximum_expansions=context_policy.max_context_expansion_requests,
                prior_selection_receipt_ref=prior_selection,
                abstention_hash=abstention.abstention_hash,
                abstention_ref=abstention_ref,
                reason_code="abstained",
            ),
            abstention=abstention,
        )

    if active_v5 and simulation_drafts:
        from deepreason.capabilities.simulation import (
            SimulationCapabilityController,
        )

        controller = SimulationCapabilityController(harness, run_manifest)
        parent_work = workflow_control_trace.ticket.work_order
        for proposal_index, draft in enumerate(simulation_drafts):
            controller.propose(
                draft,
                proposal_index=proposal_index,
                work_order=parent_work,
                source_call_seq=source_call_seq,
                formal_fence_seq=parent_work.formal_fence_seq,
                scratch_fence_seq=parent_work.scratch_fence_seq,
            )

    if request is None:
        workflow_control_trace.seal()
        return registered
    assert context_turn_payload is not None
    harness.record_conjecture_turn_event(context_turn_payload, request=request)
    if not context_granted:
        workflow_control_trace.seal()
        return registered

    from deepreason.scratch.conjecture import plan_conjecture_context_expansion
    from deepreason.scratch.service import ScratchService

    fence = harness._next_seq - 1
    expanded_plan = plan_conjecture_context_expansion(
        ScratchService(harness),
        problem=problem,
        school_id=execution_school_id,
        manifest_digest=run_manifest.sha256,
        scratch_policy=scratch_policy,
        context_policy=context_policy,
        request=request,
        prior_plan=conjecture_context_plan,
        expansion_decision_ref=context_turn_payload.decision_id,
        expansion_index=_context_expansion_index + 1,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
    )
    if expanded_plan is None:
        raise RuntimeError(
            "granted conjecture context expansion became unavailable after its decision"
        )
    follow_up_trace = workflow_control_trace.follow_up(
        advisory_context_ref=expanded_plan.advisory_context.id,
        formal_fence_seq=expanded_plan.formal_fence_seq,
        scratch_fence_seq=expanded_plan.scratch_fence_seq,
    )
    follow_up = conj(
        harness,
        problem_id,
        adapter,
        config,
        diagnostics,
        school=school,
        tail_weighted=tail_weighted,
        complement=complement,
        specs=specs,
        embedder=embedder,
        mandatory_interface=mandatory_interface,
        workload_profile=workload_profile,
        contract_id=contract_id,
        component_spec=component_spec,
        theorem_interface=theorem_interface,
        generation_context=generation_context,
        suppressed_exemplars=suppressed_exemplars,
        capture_candidate_content=capture_candidate_content,
        endpoint_lease=endpoint_lease,
        execution_school_id=execution_school_id,
        conjecture_context_plan=expanded_plan,
        run_manifest=run_manifest,
        _context_expansion_index=_context_expansion_index + 1,
        candidate_observer=candidate_observer,
        workflow_work_order_id=None,
        workflow_control_trace=follow_up_trace,
        _capability_result_context=_capability_result_context,
        _simulation_follow_up_index=_simulation_follow_up_index,
    )
    return [*registered, *follow_up]
