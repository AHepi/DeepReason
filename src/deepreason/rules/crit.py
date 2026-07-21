"""Crit (spec §3): register critic artifacts carrying valid warrants.

- crit_program: run the target's evaluable commitments (tau_kappa); each
  ``fail`` packages an ordinary demonstrative warrant (commitment, verdict,
  trace_ref, attackable validity node nu). A bare verdict is never an edge.
- crit_argumentative: the argumentative_critic role mounts a case. What the
  case may do to a non-execution-backed target is governed by
  config.ARGUMENTATIVE_AUTHORITY (RC1): observe_only records scrutiny
  evidence, trial_required routes the case through the defended cross-family
  trial, legacy_direct preserves the pre-repair self-certifying warrant.
  Demonstrative outcomes (counterexamples run against the target) remain
  status-changing under every mode. Rubric verdicts exist only downstream
  of the trial guard (P5).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from enum import Enum
import hashlib
import math

from deepreason import programs
from deepreason.authority import argumentative_authority_mode
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.llm.contracts import ArgumentativeCriticOutput, BatchCase, BatchCriticOutput
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.firewall import EndpointLease, route_fingerprint
from deepreason.llm.packs import (
    aliases_for_pack,
    render_batch_crit_pack,
    render_crit_pack,
    render_cx_retry_pack,
)
from deepreason.llm.profiles import ModelProfile, get_profile
from deepreason.llm.repair import SchemaRepairError
from deepreason.llm.wire import (
    AliasTable,
    AtomicCriticWireContractV1,
    BatchCriticWireContractV2,
    wire_contract_for,
)
from deepreason.ontology import Artifact, Provenance, Rule, Warrant, WarrantType
from deepreason.rules.warrants import (
    execution_backed,
    register_fail_warrant,
    verdict_on_record,
)


def _register_nu(harness, content: str, *, critic_school_id: str | None = None) -> Artifact:
    return harness.create_artifact(
        content,
        provenance=Provenance(role="critic", school=critic_school_id),
    )


def _authority(config) -> str:
    """ARGUMENTATIVE_AUTHORITY (RC1), fail-safe for direct helper callers.

    Historical shims must now state ``legacy_direct`` explicitly. Missing or
    malformed duck-typed values are observe-only rather than an implicit route
    to prose-derived status authority.
    """
    return argumentative_authority_mode(config)


_POLICY_AUTHORITIES = frozenset({"observe_only", "defended_trial"})


def _authority_value(value: object) -> str:
    if isinstance(value, Enum):
        value = value.value
    return str(value)


def _resolve_authority(
    config,
    explicit_authority: object | None,
    *,
    policy_call: bool,
) -> str:
    """Resolve prose authority before provider dispatch.

    Legacy direct helpers retain their Config-based compatibility behavior.
    A manifest-owned criticism call, however, must carry the already-frozen
    policy value explicitly.  It can never discover authority by rereading a
    mutable Config object, and the historical ``legacy_direct`` escape hatch
    is deliberately not a v4 policy value.
    """

    if explicit_authority is None:
        if policy_call:
            raise ValueError("manifest-bound criticism requires explicit argumentative authority")
        return _authority(config)
    authority = _authority_value(explicit_authority)
    if authority not in _POLICY_AUTHORITIES:
        raise ValueError(
            "manifest-bound criticism authority must be observe_only or defended_trial"
        )
    return "trial_required" if authority == "defended_trial" else authority


def _critic_execution(
    *,
    endpoint_lease: EndpointLease | None,
    critic_school_id: str | None,
    critic_school_context: Mapping[str, object] | None,
) -> tuple[dict, str]:
    """Validate and render one code-authored school execution envelope.

    The returned kwargs are the exact route inputs for ``LLMAdapter.call``;
    the rendered prefix is semantic conditioning only.  No field from the
    conditioning record is interpreted as routing or authority.
    """

    supplied = (
        endpoint_lease is not None,
        critic_school_id is not None,
        critic_school_context is not None,
    )
    if any(supplied) and not all(supplied):
        raise ValueError(
            "school-routed criticism requires endpoint_lease, critic_school_id, "
            "and critic_school_context"
        )
    if endpoint_lease is None:
        return {}, ""
    if endpoint_lease.role != "argumentative_critic":
        raise ValueError("criticism endpoint lease must belong to argumentative_critic")
    assert critic_school_id is not None
    assert critic_school_context is not None
    if critic_school_context.get("id") != critic_school_id:
        raise ValueError("critic execution school must match its semantic conditioning record")
    stance = critic_school_context.get("stance_text")
    if not isinstance(stance, str) or not stance.strip():
        raise ValueError("critic school conditioning requires non-blank stance_text")
    # Keep an unreasonable setup value from crowding the target out of a
    # bounded pack. This is semantic prompt material, not an authority field.
    stance = stance.strip()[:2_000]
    prefix = "\n".join(
        [
            "CRITIC SCHOOL CONDITIONING (semantic stance only; it grants no "
            "routing or status authority):",
            f"school: {critic_school_id}",
            f"stance: {stance}",
        ]
    )
    return (
        {
            "endpoint_index": endpoint_lease.seat,
            "endpoint_lease": endpoint_lease,
            "school_id": critic_school_id,
        },
        prefix,
    )


def _conditioned_budget(token_budget: int, prefix: str) -> int:
    """Reserve prompt budget for the school prefix before pack rendering."""

    if not prefix:
        return token_budget
    remaining = token_budget - math.ceil((len(prefix) + 2) / 4)
    if remaining < 256:
        raise ValueError("critic school conditioning leaves insufficient bounded pack budget")
    return remaining


def _condition_pack(pack: str, prefix: str) -> str:
    return f"{prefix}\n\n{pack}" if prefix else pack


def _llm_event_seq(harness, llm_call) -> int | None:
    """Return the durable event carrying one exact in-memory call receipt."""

    for event in reversed(list(harness.log.read())):
        if event.llm == llm_call:
            return event.seq
    return None


def _observe_coverage(
    harness,
    target_ids: tuple[str, ...],
    llm_call,
    observer: Callable[[str, int], None] | None,
) -> None:
    """Report primary exposure only after its LLMCall is append-only state."""

    if observer is None:
        return
    event_seq = _llm_event_seq(harness, llm_call)
    if event_seq is None:
        return
    for target_id in target_ids:
        observer(target_id, event_seq)


def _artifact_context_digest(harness, target_id: str) -> str:
    """Digest the exact target bytes named by one call-local SRC alias."""

    artifact = harness.state.artifacts[target_id]
    content_ref = artifact.content_ref
    if content_ref.startswith("inline:"):
        content = content_ref.removeprefix("inline:").encode("utf-8")
    else:
        try:
            content = harness.blobs.get(content_ref)
        except (FileNotFoundError, KeyError, ValueError):
            content = content_ref.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _v6_transactional_batch_call(
    harness,
    adapter,
    run_manifest,
    *,
    endpoint_lease: EndpointLease,
    critic_school_id: str,
    target_ids: tuple[str, ...],
    assignment_refs: tuple[str, ...],
    coverage_attempt_index: int,
    phase: str,
    caller_trigger_ref: str | None,
    pack_factory: Callable[[], str],
    recover_existing: bool = False,
) -> tuple[BatchCriticOutput, object]:
    """Authorize and terminalize one v6 critic provider boundary.

    Preparation is durable before the pack is rendered.  The call-local
    contract, context plan, reservation, exposure receipt, and dispatch
    bundle then become reachable through one WORK_ISSUED append.  Every
    counterexample retry invokes this helper again and therefore receives a
    distinct authorization bundle.
    """

    from deepreason.run_manifest import RunManifest
    from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
    from deepreason.workflow.transaction import (
        ContextNamespace,
        VisibleContextItemV1,
        WorkBudgetDenied,
    )
    from deepreason.workflow.transaction_service import InquiryTransactionService

    manifest = RunManifest.model_validate(run_manifest)
    control = manifest.control_plane_policy
    if (
        manifest.schema_version != 6
        or control is None
        or control.controller_version != "workflow.controller.v3"
        or control.contract_versions.batch_critic_contract != "batch-critic.v2"
    ):
        raise ValueError("transactional criticism requires the exact v6 critic contract")
    if endpoint_lease.role != "argumentative_critic":
        raise ValueError("transactional criticism requires a critic route lease")
    if not critic_school_id:
        raise ValueError("transactional criticism requires a critic school")
    targets = tuple(dict.fromkeys(target_ids))
    if not targets or len(targets) != len(target_ids):
        raise ValueError("transactional criticism targets must be nonempty and unique")
    if len(assignment_refs) != len(set(assignment_refs)):
        raise ValueError("transactional criticism assignment refs must be unique")
    meter = getattr(adapter, "meter", None)
    if meter is None:
        raise ValueError("v6 criticism dispatch requires a provider token meter")

    route_ref = RouteLeaseRefV1(
        role="argumentative_critic",
        seat=endpoint_lease.seat,
        endpoint_id=endpoint_lease.route.endpoint_id,
        route_sha256=route_fingerprint(endpoint_lease.route),
    )
    payload = {
        "schema": "criticism.semantic-task.v1",
        "critic_school_id": critic_school_id,
        "target_ids": list(targets),
        "assignment_refs": list(assignment_refs),
        "coverage_attempt_index": coverage_attempt_index,
        "phase": phase,
        "caller_trigger_ref": caller_trigger_ref,
    }
    service = InquiryTransactionService(harness, manifest, meter)
    aliases = AliasTable(
        {f"SRC_{index:03d}": target_id for index, target_id in enumerate(targets, 1)}
    )
    contract = BatchCriticWireContractV2(
        aliases,
        expected_targets=targets,
    )
    if recover_existing:
        matches = [
            item
            for item in harness.workflow_state.transaction_work.values()
            if item.preparation.contract_id == contract.contract_id
            and item.preparation.task_payload_value == payload
            and item.preparation.route_lease == route_ref
        ]
        if len(matches) > 1:
            raise ValueError("transactional criticism recovery is ambiguous")
        if matches:
            from deepreason.workflow.atomic_recovery import recover_atomic_child_output

            return recover_atomic_child_output(
                harness, manifest, service, matches[0], contract
            )
    fence = max(0, harness._next_seq - 1)
    trigger_ref = "criticism:" + hashlib.sha256(canonical_json(payload)).hexdigest()
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CRITICISM,
        attempt_index=coverage_attempt_index,
        route_lease=route_ref,
        contract_id="batch-critic.v2",
        trigger_ref=trigger_ref,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
        target_refs=targets,
        input_refs=assignment_refs,
        task_payload_value=payload,
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
        pack = pack_factory()
        rendered_bytes = len(pack.encode("utf-8"))
        items = tuple(
            VisibleContextItemV1(
                namespace=ContextNamespace.SOURCE,
                alias=alias,
                object_ref=target_id,
                content_sha256=_artifact_context_digest(harness, target_id),
                planned_bytes=(rendered_bytes if index == 0 else 0),
            )
            for index, (alias, target_id) in enumerate(aliases.aliases.items())
        )
        plan = service.context_plan(
            preparation,
            plan_kind="dossier",
            items=items,
            maximum_bytes=rendered_bytes,
            rendered_bytes=rendered_bytes,
        )
        prompt, preview_contract, preview_lease, maximum_tokens = adapter.preview_request(
            "argumentative_critic",
            pack,
            BatchCriticOutput,
            endpoint_index=endpoint_lease.seat,
            template_role="batch_critic",
            wire_contract=contract,
            aliases=aliases,
            endpoint_lease=endpoint_lease,
        )
        if preview_contract is not contract or preview_lease != endpoint_lease:
            raise ValueError("v6 critic preview changed frozen call authority")
        authorized = service.issue(
            preparation,
            plans=(plan,),
            prompt=prompt,
            max_tokens=maximum_tokens,
        )
    except WorkBudgetDenied:
        raise
    except Exception:
        abandon(issued=False, reason_code="critic_preissue_failure")
        raise

    provider = None
    try:
        output, llm_call = adapter.call(
            "argumentative_critic",
            pack,
            BatchCriticOutput,
            endpoint_index=endpoint_lease.seat,
            template_role="batch_critic",
            wire_contract=contract,
            aliases=aliases,
            endpoint_lease=endpoint_lease,
            school_id=critic_school_id,
            dispatch_authorization=authorized,
        )
    except EndpointError as error:
        spend = getattr(error, "spend", None)
        if spend is None:
            abandon(issued=True, reason_code="critic_transport_result_unknown")
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
                reason_code="critic_transport_failure",
                usage_status="unknown",
                provider_attempt=provider,
            )
            error.spend = None
        error.transaction_terminalized = True
        raise
    except SchemaRepairError as error:
        try:
            repaired = service.repair_schema_failure(
                adapter=adapter,
                authorized=authorized,
                error=error,
                role="argumentative_critic",
                pack=pack,
                output_model=BatchCriticOutput,
                wire_contract=contract,
                endpoint_index=endpoint_lease.seat,
                template_role="batch_critic",
                endpoint_lease=endpoint_lease,
                school_id=critic_school_id,
                reason_prefix="critic",
            )
        except SchemaRepairError as exhausted:
            if not isinstance(getattr(exhausted, "source_work_id", None), str):
                exhausted.source_work_id = preparation.id
            raise
        output = repaired.output
        llm_call = repaired.llm_call
        preparation = repaired.preparation
        authorized = repaired.authorized
        provider = repaired.provider_attempt
    except Exception:
        abandon(issued=True, reason_code="critic_authority_failure")
        raise

    if provider is None:
        provider = service.record_provider_attempt(
            authorized,
            call=llm_call,
            outcome="provider_result",
            usage_status="exact",
        )
    admitted_ref = harness.blobs.put(
        canonical_json(output.model_dump(mode="json", exclude_none=True))
    )
    admission = service.record_semantic_admission(
        provider,
        outcome="admitted",
        admitted_refs=(admitted_ref,),
    )
    service.terminate(
        work_id=preparation.id,
        attempt_index=preparation.attempt_index,
        status="completed",
        reason_code="critic_output_admitted",
        usage_status="exact",
        prompt_tokens=llm_call.prompt_tokens,
        completion_tokens=llm_call.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    return output, llm_call


def _v6_transactional_atomic_critic_call(
    harness,
    adapter,
    run_manifest,
    *,
    endpoint_lease: EndpointLease,
    critic_school_id: str,
    target_id: str,
    transition,
    child_index: int,
    child_count: int,
    pack_factory: Callable[[], str],
) -> tuple[ArgumentativeCriticOutput, object]:
    """Execute or recover one manifest-authorized target child transaction."""

    from deepreason.run_manifest import RunManifest
    from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
    from deepreason.workflow.transaction import ContextNamespace, VisibleContextItemV1
    from deepreason.workflow.transaction_service import InquiryTransactionService

    manifest = RunManifest.model_validate(run_manifest)
    route_ref = RouteLeaseRefV1(
        role="argumentative_critic",
        seat=endpoint_lease.seat,
        endpoint_id=endpoint_lease.route.endpoint_id,
        route_sha256=route_fingerprint(endpoint_lease.route),
    )
    if (
        transition.route_lease != route_ref
        or transition.atomic_contract_id != "critic.atomic-target.v1"
        or not 0 <= child_index < child_count <= transition.maximum_children
    ):
        raise ValueError("atomic critic child differs from decomposition authority")
    payload = {
        "schema": "contract-decomposition-child.v1",
        "decomposition_transition_ref": transition.id,
        "source_work_id": transition.source_work_id,
        "source_contract_id": transition.source_contract_id,
        "atomic_contract_id": transition.atomic_contract_id,
        "child_partition": transition.child_partition,
        "child_index": child_index,
        "child_count": child_count,
        "child_key": target_id,
        "critic_school_id": critic_school_id,
    }
    aliases = AliasTable({"SRC_001": target_id})
    contract = AtomicCriticWireContractV1(aliases, expected_target=target_id)
    service = InquiryTransactionService(harness, manifest, adapter.meter)

    matches = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if item.preparation.contract_id == contract.contract_id
        and item.preparation.task_payload_value == payload
        and item.preparation.route_lease == route_ref
    ]
    if len(matches) > 1:
        raise ValueError("atomic critic child history is ambiguous")
    if matches:
        item = matches[0]
        from deepreason.workflow.atomic_recovery import recover_atomic_child_output

        return recover_atomic_child_output(
            harness, manifest, service, item, contract
        )

    fence = max(0, harness._next_seq - 1)
    trigger_ref = "decomposition-child:" + hashlib.sha256(
        canonical_json(payload)
    ).hexdigest()
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CRITICISM,
        attempt_index=0,
        route_lease=route_ref,
        contract_id=contract.contract_id,
        trigger_ref=trigger_ref,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
        target_refs=(target_id,),
        input_refs=(
            transition.source_work_id,
            transition.id,
            transition.child_context_refs[child_index],
            target_id,
        ),
        task_payload_value=payload,
    )
    pack = pack_factory()
    rendered_bytes = len(pack.encode("utf-8"))
    plan = service.context_plan(
        preparation,
        plan_kind="dossier",
        items=(
            VisibleContextItemV1(
                namespace=ContextNamespace.SOURCE,
                alias="SRC_001",
                object_ref=target_id,
                content_sha256=_artifact_context_digest(harness, target_id),
                planned_bytes=rendered_bytes,
            ),
        ),
        maximum_bytes=rendered_bytes,
        rendered_bytes=rendered_bytes,
    )
    prompt, preview_contract, preview_lease, maximum_tokens = adapter.preview_request(
        "argumentative_critic",
        pack,
        ArgumentativeCriticOutput,
        endpoint_index=endpoint_lease.seat,
        template_role="argumentative_critic",
        wire_contract=contract,
        aliases=aliases,
        endpoint_lease=endpoint_lease,
    )
    if preview_contract is not contract or preview_lease != endpoint_lease:
        raise ValueError("atomic critic preview changed frozen authority")
    authorized = service.issue(
        preparation, plans=(plan,), prompt=prompt, max_tokens=maximum_tokens
    )
    try:
        output, call = adapter.call(
            "argumentative_critic",
            pack,
            ArgumentativeCriticOutput,
            endpoint_index=endpoint_lease.seat,
            template_role="argumentative_critic",
            wire_contract=contract,
            aliases=aliases,
            endpoint_lease=endpoint_lease,
            school_id=critic_school_id,
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
                reason_code="atomic_critic_provider_result_unknown",
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
                reason_code="atomic_critic_transport_failure",
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
            role="argumentative_critic",
            pack=pack,
            output_model=ArgumentativeCriticOutput,
            wire_contract=contract,
            endpoint_index=endpoint_lease.seat,
            template_role="argumentative_critic",
            endpoint_lease=endpoint_lease,
            school_id=critic_school_id,
            reason_prefix="atomic_critic",
        )
        output, call = repaired.output, repaired.llm_call
        preparation, authorized = repaired.preparation, repaired.authorized
        provider = repaired.provider_attempt
    else:
        provider = service.record_provider_attempt(
            authorized, call=call, outcome="provider_result", usage_status="exact"
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
        reason_code="atomic_critic_output_admitted",
        usage_status="exact",
        prompt_tokens=call.prompt_tokens,
        completion_tokens=call.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    return output, call


def _observe_case(
    harness,
    target_id: str,
    case_text: str,
    llm_call,
    *,
    critic_school_id: str | None = None,
    restart_safe: bool = False,
    effect_source_call_seq: int | None = None,
):
    """observe_only semantics: the case is scrutiny evidence, never a status
    change. Registers the case as a critic-role artifact with NO warrants and
    records a ["scrutiny", target, critic] Measure. A non-None llm_call is
    accounted exactly once: on the registration event when it commits, on
    the scrutiny Measure when the prose dedupes; callers passing a shared
    call must treat it as spent after this returns."""
    before = set(harness.state.artifacts)
    critic = harness.create_artifact(
        case_text,
        provenance=Provenance(role="critic", school=critic_school_id),
        rule=Rule.CRIT,
        llm=llm_call,
    )
    carried = llm_call is not None and critic.id not in before
    inputs = ["scrutiny", target_id, critic.id]
    if effect_source_call_seq is not None:
        inputs.append(f"source:{effect_source_call_seq}")
    existing = [
        event
        for event in harness.log.read()
        if event.rule == Rule.MEASURE
        and list(event.inputs) == inputs
    ]
    if len(existing) > 1:
        raise RuntimeError("criticism scrutiny effect is duplicated")
    if not restart_safe or not existing:
        harness.record_measure(
            inputs=inputs,
            llm=None if carried else llm_call,
        )
    return critic


def _has_property_oracle(harness, target_id: str) -> bool:
    """Counterexamples can ground only against a property-oracle commitment
    (checker-decided correctness); retrying against anything else is spend
    with no possible payoff."""
    from deepreason.oracle import PROPERTY_PROGRAM

    target = harness.state.artifacts.get(target_id)
    if target is None:
        return False
    return any(
        (kappa := harness.commitments.get(cid)) is not None
        and kappa.eval == f"program:{PROPERTY_PROGRAM}"
        for cid in target.interface.commitments
    )


def try_counterexample(
    harness,
    target_id: str,
    args,
    *,
    case: str,
    llm=None,
    critic_school_id: str | None = None,
    restart_safe: bool = False,
    effect_source_call_seq: int | None = None,
) -> tuple[Artifact | None, str]:
    """The critic's grounded recourse (§3 execution supremacy): the critic
    proposed a concrete INPUT; run the target on it and check the declared
    property. Admissible iff the target carries a property-oracle commitment
    (correctness is checker-decided, reference-free) and the spec's input gate
    admits the args. A violated property mints a content-addressed
    counterexample commitment and registers an ordinary DEMONSTRATIVE fail
    warrant — the critic refuted by EXECUTION, so execution supremacy does not
    apply. Anything else grounds nothing: returns (None, reason), where reason
    is the DETERMINISTIC gate/oracle verdict on why — callers may echo it back
    to the critic (§3 counterexample retry). Deterministic (§0): minting,
    evaluation, and the warrant are pure functions of frozen spec + args."""
    from deepreason.oracle import PROPERTY_PROGRAM, admit_counterexample

    target = harness.state.artifacts.get(target_id)
    if target is None:
        return None, "unknown target"
    if args is None:
        return None, "no counterexample proposed"
    reasons: list[str] = []
    saw_property_oracle = False
    for cid in target.interface.commitments:
        base = harness.commitments.get(cid)
        if base is None or base.eval != f"program:{PROPERTY_PROGRAM}":
            continue
        saw_property_oracle = True
        cx, reason = admit_counterexample(base, args)
        if cx is None:
            reasons.append(reason)
            continue  # inadmissible against this commitment's input gate
        verdict, trace = programs.evaluate(cx, target, harness.blobs)
        if trace.get("sandbox_abort"):
            reasons.append(
                "the execution sandbox aborted before producing a verdict — "
                "the proposed input grounds nothing and may be retried"
            )
            continue
        if verdict == programs.OVERRUN:
            reasons.append(
                "the property oracle was unusable on this input and produced "
                "no verdict — the proposed input grounds nothing"
            )
            continue
        if verdict != programs.FAIL:
            reasons.append(
                "the target RAN your input and the property HELD — this "
                "counterexample does not discriminate; construct an input where "
                "the target's OUTPUT violates the checker"
            )
            continue
        harness.register_commitment(cx)
        if verdict_on_record(harness, cx.id, target_id):
            if restart_safe and effect_source_call_seq is not None:
                matches = []
                for event in harness.log.read():
                    if event.seq <= effect_source_call_seq:
                        continue
                    for artifact_id in event.outputs:
                        artifact = harness.state.artifacts.get(artifact_id)
                        if artifact is None:
                            continue
                        if any(
                            (warrant := harness.warrants.get(warrant_id)) is not None
                            and warrant.commitment == cx.id
                            and warrant.target == target_id
                            for warrant_id in artifact.warrants
                        ):
                            matches.append(artifact)
                if len(matches) > 1:
                    raise RuntimeError("grounded criticism effect is duplicated")
                if matches:
                    return matches[0], ""
            return None, "this exact counterexample already refutes the target"
        return register_fail_warrant(
            harness,
            commitment_id=cx.id,
            target_id=target_id,
            nu_content=(
                f"nu: counterexample verdict of {cx.id} on {target_id} is sound "
                f"(input admitted by {base.id}'s gate, property checker inherited)"
            ),
            critic_content=(
                f"critic: counterexample {canonical_json(args).decode()} violates "
                f"the property of {base.id} on {target_id[:12]} — {case}"
            ),
            trace_ref=harness.blobs.put(canonical_json(trace)),
            llm=llm,
            critic_school_id=critic_school_id,
        ), ""
    if not saw_property_oracle:
        return None, "target carries no property oracle: counterexamples do not apply"
    return None, "; ".join(reasons)


def crit_program(harness, target_id: str) -> list[Artifact]:
    """Evaluate the target's commitments; register a critic per failure."""
    target = harness.state.artifacts[target_id]
    critics: list[Artifact] = []
    for cid in target.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None or not programs.evaluable(kappa):
            continue
        if verdict_on_record(harness, cid, target_id):
            continue  # guard checked pre-evaluation: skips the τκ run too
        verdict, trace = programs.evaluate(kappa, target, harness.blobs)
        pending_key = (cid, target_id)
        if trace.get("sandbox_abort"):
            harness._oracle_pending.add(pending_key)
            continue  # availability failure: no verdict and no warrant
        harness._oracle_pending.discard(pending_key)
        if verdict != programs.FAIL:
            continue
        critics.append(
            register_fail_warrant(
                harness,
                commitment_id=cid,
                target_id=target_id,
                nu_content=f"nu: verdict of {cid} on {target_id} is sound and relevant",
                critic_content=f"critic: {cid} failed on {target_id[:12]}",
                trace_ref=harness.blobs.put(canonical_json(trace)),
            )
        )
    return critics


# Deterministic tick incremented whenever a property violation is quarantined
# (population not yet supporting): the scheduler's fuzz sweep snapshots it to
# avoid marking such a target clean — the verdict is pending population
# growth, not settled. Derived from deterministic control flow (replay-safe).
QUARANTINE_TICK = [0]


def crit_fuzz(harness, target_id: str, config) -> Artifact | None:
    """Deterministic fuzz criticism (§3): the HARNESS experiments, no LLM. For
    each property-oracle commitment on the target that carries a generator,
    enumerate gate-valid inputs (oracle.fuzz_property) and RUN the target; the
    first property violation goes through the same admission/minting path as a
    critic-proposed counterexample and registers an ordinary DEMONSTRATIVE
    fail warrant. Cheap (sandboxed executions only), replay-deterministic,
    and immune to the attractor problem the probe exposed — an enumerator
    cannot fixate on cycle attacks."""
    from deepreason.oracle import PROPERTY_PROGRAM, admit_counterexample, fuzz_property

    if config.FUZZ_N <= 0:
        return None
    target = harness.state.artifacts.get(target_id)
    if target is None:
        return None
    source = programs.content_text(target, harness.blobs)
    for cid in target.interface.commitments:
        base = harness.commitments.get(cid)
        if base is None or base.eval != f"program:{PROPERTY_PROGRAM}":
            continue
        # The spec's own generator first, then every ACCEPTED experimenter-
        # designed generator (rules/experiment.py) — the system probing with
        # experiments it designed for itself. Lazy import: experiment.py
        # imports crit_program from this module.
        from deepreason.rules.experiment import accepted_generators

        probes: list[tuple[str | None, str | None]] = [(None, None)]
        probes += [(gid, src) for gid, src in accepted_generators(harness, cid)]
        for gen_id, gen_source in probes:
            violation, detail = fuzz_property(source, base, config.FUZZ_N, generator=gen_source)
            if violation is None:
                if detail.get("sandbox_abort") or detail.get("oracle_overrun"):
                    QUARANTINE_TICK[0] += 1  # unavailable is pending, never clean
                continue
            cx, _ = admit_counterexample(base, violation)
            if cx is None:
                continue  # generator emitted an inadmissible input: never grounds
            verdict, trace = programs.evaluate(cx, target, harness.blobs)
            if verdict != programs.FAIL:
                continue
            harness.register_commitment(cx)
            if verdict_on_record(harness, cx.id, target_id):
                continue
            credit = f"designed by {gen_id[:12]}" if gen_id else "spec generator"
            nu_interface = None
            if gen_id:
                from deepreason.ontology import Interface, Ref
                from deepreason.ontology.artifact import RefRole

                # Credit flows in the graph: the nu mentions the generator
                # that designed the killing experiment (provenance, not a
                # warrant — D2).
                nu_interface = Interface(refs=[Ref(target=gen_id, role=RefRole.MENTION)])
            return register_fail_warrant(
                harness,
                commitment_id=cx.id,
                target_id=target_id,
                nu_content=(
                    f"nu: fuzz counterexample verdict of {cx.id} on {target_id} "
                    f"is sound (deterministic enumeration k={detail.get('k')}, "
                    f"{credit}, gate-admitted, property checker inherited from "
                    f"{base.id})"
                ),
                critic_content=(
                    f"critic: fuzz found counterexample "
                    f"{canonical_json(violation).decode()} violating the property "
                    f"of {base.id} on {target_id[:12]} (k={detail.get('k')}, "
                    f"{detail.get('fuzzed')} inputs tried, {credit})"
                ),
                nu_interface=nu_interface,
                trace_ref=harness.blobs.put(canonical_json(trace)),
            )
        # The trusted spec checker found nothing: probe with ACTIVE proposed
        # properties (conjectured ground truth — checker_wf'd, trial-passed,
        # wipeout-guarded, and collapsible via the source-artifact closure).
        prop_critic = _crit_proposed_properties(harness, target_id, base, source, probes, config)
        if prop_critic is not None:
            return prop_critic
    return None


def _refute_crashing_property(harness, prop_id: str, detail: dict) -> None:
    """A conjectured checker that THROWS on a real domain input is refuted
    demonstratively — the crash is the counterexample to its own checker_wf
    claim (compiles/bounded/runs on the domain). Mechanical, deduplicated;
    the source-artifact closure then collapses any verdicts it minted."""
    from deepreason.oracle import CHECKER_PROGRAM

    prop = harness.state.artifacts.get(prop_id)
    if prop is None:
        return
    wf_id = next(
        (
            cid
            for cid in prop.interface.commitments
            if (kappa := harness.commitments.get(cid)) is not None
            and kappa.eval == f"program:{CHECKER_PROGRAM}"
        ),
        None,
    )
    if wf_id is None:
        return
    harness.record_measure(
        inputs=["property-checker-crash", prop_id, str(detail.get("error", ""))[:120]]
    )
    register_fail_warrant(
        harness,
        commitment_id=wf_id,
        target_id=prop_id,
        nu_content=(
            f"nu: proposed checker {prop_id[:12]} crashed on a real domain "
            "input during fuzz — a well-formed checker rejects, it does not "
            "throw; this crash refutes the checker, not the candidate"
        ),
        critic_content=(
            f"critic: checker of {prop_id[:12]} raised during property fuzz: "
            f"{str(detail.get('error', ''))[:120]}"
        ),
        trace_ref=harness.blobs.put(canonical_json(detail)),
        skip_if_on_record=True,
    )


def _crit_proposed_properties(
    harness, target_id: str, base, source: str, probes: list, config
) -> Artifact | None:
    """Fuzz the target against each ACTIVE proposed property: frozen inputs
    first (cheapest), then every generator probe. A violation grounds a
    DEMONSTRATIVE warrant only if the population supports the property (at
    least one accepted sibling passes it — otherwise the property is indicting
    everyone and is quarantined). The minted commitment DECLARES the property
    as source_artifact, so the att closure (edges.py) makes the property's
    attackers attack this verdict's nu: refute the property and the target
    reinstates. Deterministic given the graph; no LLM calls."""
    from deepreason.oracle import (
        _load_spec,
        admit_counterexample,
        fuzz_property,
        property_violation_commitment,
        run_property,
    )
    from deepreason.rules.experiment import (
        active_properties,
        population_supports,
        promoted_properties,
    )

    from deepreason.rules.experiment import checker_crashed

    spec = _load_spec(base.budget)
    entry, frozen = spec.get("entry"), spec.get("inputs", [])
    promoted = promoted_properties(harness, base.id, config)
    for prop_id, claim, prop_source in active_properties(harness, base.id):
        violation = None
        if entry and frozen:
            verdict, d = run_property(source, entry, frozen, prop_source)
            if verdict == programs.OVERRUN:
                QUARANTINE_TICK[0] += 1
                continue
            if verdict == programs.FAIL and "case" in d:
                if checker_crashed(d):
                    # The CHECKER threw, not the candidate (intervals/boot
                    # postmortem: a conjectured checker's own bug executed
                    # seven correct candidates). A crash is not a verdict —
                    # it grounds nothing against the target and is instead a
                    # demonstrative counterexample to the CHECKER's
                    # well-formedness, with the crash as trace.
                    _refute_crashing_property(harness, prop_id, d)
                    continue
                violation = frozen[d["case"]]
        if violation is None:
            for _, gen_source in probes:
                found, _detail = fuzz_property(
                    source,
                    base,
                    config.FUZZ_N,
                    generator=gen_source,
                    checker=prop_source,
                )
                if _detail.get("sandbox_abort") or _detail.get("oracle_overrun"):
                    QUARANTINE_TICK[0] += 1
                    continue
                if found is not None:
                    candidate, _ = admit_counterexample(base, found)
                    if candidate is None:
                        continue  # out-of-gate input: never grounds
                    # Classify before blaming: re-run the single input and
                    # route checker crashes to the property, not the target.
                    if entry:
                        _, d2 = run_property(source, entry, [found], prop_source)
                        if checker_crashed(d2):
                            _refute_crashing_property(harness, prop_id, d2)
                            found = None
                            break
                    violation = found
                    break
        if violation is None:
            continue
        # Promotion (the ratchet): a property past probation holds the line
        # without population support — the standard does not sink with a bad
        # generation of candidates. Probationary properties still need a
        # sibling that satisfies them.
        if prop_id not in promoted and not population_supports(
            harness, base, prop_source, target_id
        ):
            QUARANTINE_TICK[0] += 1  # sweep must NOT mark this target clean
            harness.record_measure(inputs=["property-wipeout-quarantine", prop_id, target_id])
            continue
        cx = property_violation_commitment(base, prop_id, prop_source, violation)
        verdict, trace = programs.evaluate(cx, harness.state.artifacts[target_id], harness.blobs)
        if verdict != programs.FAIL:
            continue
        harness.register_commitment(cx)
        if verdict_on_record(harness, cx.id, target_id):
            continue
        from deepreason.ontology import Interface, Ref
        from deepreason.ontology.artifact import RefRole

        return register_fail_warrant(
            harness,
            commitment_id=cx.id,
            target_id=target_id,
            nu_content=(
                f"nu: proposed-property verdict of {cx.id} on {target_id} is "
                f"sound — property {prop_id} ({claim[:80]}) was checker-wf'd, "
                f"trial-validated, and population-supported; refute the "
                f"property and this verdict falls with it"
            ),
            critic_content=(
                f"critic: input {canonical_json(violation).decode()} violates "
                f"proposed property {prop_id[:12]} ({claim[:80]}) on "
                f"{target_id[:12]}"
            ),
            # Load-bearing source is DECLARED on the commitment (closure);
            # the MENTION here is for readers and reach.
            nu_interface=Interface(refs=[Ref(target=prop_id, role=RefRole.MENTION)]),
            trace_ref=harness.blobs.put(canonical_json(trace)),
        )
    return None


def crit_argumentative(
    harness,
    target_id: str,
    adapter,
    config,
    *,
    endpoint_lease: EndpointLease | None = None,
    critic_school_id: str | None = None,
    critic_school_context: Mapping[str, object] | None = None,
    argumentative_authority: object | None = None,
    coverage_observer: Callable[[str, int], None] | None = None,
) -> Artifact | None:
    """One argumentative-critic call; registers a critic iff it attacks.

    The optional keyword-only envelope is the v4 path: code supplies one
    exact route lease, its critic-school lineage and semantic stance, and the
    already-frozen prose authority. Historical callers omit the envelope and
    retain the original Config-driven behavior.
    """

    call_kwargs, school_prefix = _critic_execution(
        endpoint_lease=endpoint_lease,
        critic_school_id=critic_school_id,
        critic_school_context=critic_school_context,
    )
    policy_call = (
        bool(call_kwargs) or argumentative_authority is not None or coverage_observer is not None
    )
    authority = _resolve_authority(config, argumentative_authority, policy_call=policy_call)
    pack = render_crit_pack(
        target_id,
        harness.state,
        harness.commitments,
        harness.blobs,
        token_budget=_conditioned_budget(config.PACK_TOKEN_BUDGET, school_prefix),
    )
    pack = _condition_pack(pack, school_prefix)
    aliases = aliases_for_pack(pack, harness.state.artifacts, prefix="A")
    wire_contract = wire_contract_for(
        "argumentative_critic",
        ArgumentativeCriticOutput,
        adapter.profile_for("argumentative_critic"),
        aliases,
        expected_target=target_id,
    )
    output, llm_call = adapter.call(
        "argumentative_critic",
        pack,
        ArgumentativeCriticOutput,
        aliases=aliases,
        wire_contract=wire_contract,
        **call_kwargs,
    )
    primary_llm_call = llm_call
    try:
        if not output.attack or not output.case.strip():
            # No fault found: the call still spent tokens and must be logged once.
            harness.record_measure(inputs=["arg-crit", target_id], llm=llm_call)
            return None
        before = set(harness.state.artifacts)
        grounded, reason = try_counterexample(
            harness,
            target_id,
            output.counterexample,
            case=output.case,
            llm=llm_call,
            critic_school_id=critic_school_id,
        )
        if grounded is not None:
            # The critic refuted by EXECUTION (counterexample violated the
            # property) — strictly stronger than the argument it came with.
            if grounded.id in before:
                harness.record_measure(inputs=["arg-crit", target_id], llm=llm_call)
            return grounded
        if execution_backed(harness, target_id):
            # Execution supremacy (§3): a verdict from reality stands and a purely
            # argumentative case cannot override it. Before giving up, echo the
            # gate/oracle's DETERMINISTIC rejection reason back to the critic (§3
            # counterexample retry): the one-shot caller otherwise never learns
            # why its input refuted nothing.
            cx = output.counterexample
            retries = config.CX_RETRY_MAX if _has_property_oracle(harness, target_id) else 0
            for _ in range(max(0, retries)):
                harness.record_measure(inputs=["arg-crit-cx-rejected", target_id], llm=llm_call)
                retry_pack = render_cx_retry_pack(
                    [{"target": target_id, "counterexample": cx, "reason": reason}],
                    harness.state,
                    harness.commitments,
                    harness.blobs,
                    token_budget=_conditioned_budget(config.PACK_TOKEN_BUDGET, school_prefix),
                )
                retry_pack = _condition_pack(retry_pack, school_prefix)
                retry_aliases = aliases_for_pack(retry_pack, harness.state.artifacts, prefix="A")
                retry_contract = wire_contract_for(
                    "argumentative_critic",
                    ArgumentativeCriticOutput,
                    adapter.profile_for("argumentative_critic"),
                    retry_aliases,
                    expected_target=target_id,
                )
                retry, llm_call = adapter.call(
                    "argumentative_critic",
                    retry_pack,
                    ArgumentativeCriticOutput,
                    aliases=retry_aliases,
                    wire_contract=retry_contract,
                    **call_kwargs,
                )
                if not retry.attack:
                    break  # the critic withdrew: nothing further to ground
                before = set(harness.state.artifacts)
                grounded, reason = try_counterexample(
                    harness,
                    target_id,
                    retry.counterexample,
                    case=retry.case.strip() or output.case,
                    llm=llm_call,
                    critic_school_id=critic_school_id,
                )
                if grounded is not None:
                    if grounded.id in before:
                        harness.record_measure(inputs=["arg-crit", target_id], llm=llm_call)
                    return grounded
                cx = retry.counterexample
            harness.record_measure(
                inputs=["arg-crit-overridden-by-execution", target_id], llm=llm_call
            )
            return None
        # Authority gate (RC1): only the historical legacy path lets a prose
        # case mint its own warrant. Manifest policy permits observation or a
        # defended trial; demonstrative execution above remains authoritative.
        if authority == "observe_only":
            return _observe_case(
                harness,
                target_id,
                output.case,
                llm_call,
                critic_school_id=critic_school_id,
            )
        if authority == "trial_required":
            from deepreason.informal.trial import run_argument_trial_from_case

            return run_argument_trial_from_case(
                harness,
                adapter,
                config,
                target_id,
                output.case,
                llm_call,
                authority="status",
                critic_school_id=critic_school_id,
            )
        case_hash = sha256_hex(output.case.encode())[:16]
        nu = _register_nu(
            harness,
            f"nu: argumentative case {case_hash} against {target_id} is sound",
            critic_school_id=critic_school_id,
        )
        warrant = Warrant(
            id=f"w:arg:{case_hash}:{target_id}",
            target=target_id,
            type=WarrantType.ARGUMENTATIVE,
            validity_node=nu.id,
        )
        before = set(harness.state.artifacts)
        critic = harness.create_artifact(
            output.case,
            provenance=Provenance(role="critic", school=critic_school_id),
            warrants=[warrant],
            rule=Rule.CRIT,
            llm=llm_call,
        )
        if critic.id in before:
            # The critic content deduped to an existing artifact, so no event
            # carried llm_call — log it so token accounting sees the call once.
            harness.record_measure(inputs=["arg-crit", target_id], llm=llm_call)
        return critic
    finally:
        _observe_coverage(
            harness,
            (target_id,),
            primary_llm_call,
            coverage_observer,
        )


def crit_argumentative_batch(
    harness,
    target_ids,
    adapter,
    config,
    *,
    endpoint_lease: EndpointLease | None = None,
    critic_school_id: str | None = None,
    critic_school_context: Mapping[str, object] | None = None,
    argumentative_authority: object | None = None,
    coverage_observer: Callable[[str, int], None] | None = None,
    run_manifest=None,
    transaction_attempt_index: int = 0,
    transaction_assignment_refs: tuple[str, ...] = (),
    transaction_trigger_ref: str | None = None,
) -> list[Artifact]:
    """One argumentative-critic call over K targets (§14 batching — the call
    structure is not the epistemology; the warrant structure is). Every
    attacking case registers exactly as in the single path: per-target
    argumentative warrant with its own attackable nu. A case naming an id
    outside the batch is dropped — no verdict without exposure. A single
    target delegates to the single-target contract unchanged."""
    call_kwargs, school_prefix = _critic_execution(
        endpoint_lease=endpoint_lease,
        critic_school_id=critic_school_id,
        critic_school_context=critic_school_context,
    )
    policy_call = (
        bool(call_kwargs) or argumentative_authority is not None or coverage_observer is not None
    )
    authority = _resolve_authority(config, argumentative_authority, policy_call=policy_call)
    active_v6 = False
    if run_manifest is not None:
        from deepreason.run_manifest import RunManifest

        run_manifest = RunManifest.model_validate(run_manifest)
        active_v6 = run_manifest.schema_version == 6
    if active_v6 and (endpoint_lease is None or critic_school_id is None):
        raise ValueError("v6 criticism requires one manifest-bound school route")
    target_ids = list(dict.fromkeys(target_ids))
    if not target_ids:
        return []
    if len(target_ids) == 1 and not active_v6:
        critic = crit_argumentative(
            harness,
            target_ids[0],
            adapter,
            config,
            endpoint_lease=endpoint_lease,
            critic_school_id=critic_school_id,
            critic_school_context=critic_school_context,
            argumentative_authority=argumentative_authority,
            coverage_observer=coverage_observer,
        )
        return [critic] if critic else []
    if (
        not active_v6
        and get_profile(adapter.profile_for("argumentative_critic")).name == ModelProfile.COMPACT
    ):
        # Compact is one semantic target per call. Preserve per-target warrant
        # construction and deterministic target order by using the ordinary
        # single-target path rather than exposing BatchCriticOutput.
        critics = []
        for target_id in target_ids:
            critic = crit_argumentative(
                harness,
                target_id,
                adapter,
                config,
                endpoint_lease=endpoint_lease,
                critic_school_id=critic_school_id,
                critic_school_context=critic_school_context,
                argumentative_authority=argumentative_authority,
                coverage_observer=coverage_observer,
            )
            if critic is not None:
                critics.append(critic)
        return critics

    def primary_pack_factory() -> str:
        pack = render_batch_crit_pack(
            target_ids,
            harness.state,
            harness.commitments,
            harness.blobs,
            token_budget=_conditioned_budget(config.PACK_TOKEN_BUDGET, school_prefix),
        )
        return _condition_pack(pack, school_prefix)

    transactional_call = None
    atomic_call_by_target: dict[str, object] = {}
    decomposition_transition = None
    resuming_atomic_decomposition = False
    if active_v6:
        assert endpoint_lease is not None
        assert critic_school_id is not None

        from deepreason.workflow.models import RouteLeaseRefV1

        expected_route_ref = RouteLeaseRefV1(
            role="argumentative_critic",
            seat=endpoint_lease.seat,
            endpoint_id=endpoint_lease.route.endpoint_id,
            route_sha256=route_fingerprint(endpoint_lease.route),
        )
        expected_strong_payload = {
            "schema": "criticism.semantic-task.v1",
            "critic_school_id": critic_school_id,
            "target_ids": list(target_ids),
            "assignment_refs": list(transaction_assignment_refs),
            "coverage_attempt_index": transaction_attempt_index,
            "phase": "primary",
            "caller_trigger_ref": transaction_trigger_ref,
        }

        def source_root_payload(transition):
            source = harness.workflow_state.transaction_work.get(
                transition.source_work_id
            )
            if source is None:
                return None
            value = source.preparation.task_payload_value
            if (
                isinstance(value, Mapping)
                and value.get("schema") == "repair.semantic-task.v1"
            ):
                source = harness.workflow_state.transaction_work.get(
                    value.get("parent_work_id")
                )
                if source is None:
                    return None
                value = source.preparation.task_payload_value
            return value

        def execute_atomic_transition(transition):
            nonlocal atomic_call_by_target
            if (
                transition.route_lease != expected_route_ref
                or transition.source_contract_id != "batch-critic.v2"
                or transition.atomic_contract_id != "critic.atomic-target.v1"
                or tuple(transition.child_keys) != tuple(target_ids)
                or len(transition.child_context_refs) != len(target_ids)
            ):
                raise ValueError("atomic criticism differs from decomposition authority")
            atomic_cases = []
            atomic_calls = []
            for child_index, target_id in enumerate(target_ids):

                def atomic_pack_factory(child_index=child_index):
                    return harness.blobs.get(
                        transition.child_context_refs[child_index]
                    ).decode("utf-8")

                atomic_output, atomic_call = _v6_transactional_atomic_critic_call(
                    harness,
                    adapter,
                    run_manifest,
                    endpoint_lease=endpoint_lease,
                    critic_school_id=critic_school_id,
                    target_id=target_id,
                    transition=transition,
                    child_index=child_index,
                    child_count=len(target_ids),
                    pack_factory=atomic_pack_factory,
                )
                atomic_cases.append(
                    BatchCase(
                        target=target_id,
                        attack=atomic_output.attack,
                        case=atomic_output.case,
                        counterexample=atomic_output.counterexample,
                    )
                )
                atomic_calls.append(atomic_call)
                atomic_call_by_target[target_id] = atomic_call
            if any(_llm_event_seq(harness, call) is None for call in atomic_calls):
                raise RuntimeError("atomic criticism has an undurable source call")
            return BatchCriticOutput(cases=atomic_cases), atomic_calls[-1]

        def transactional_call(
            selected_targets: tuple[str, ...],
            pack_factory: Callable[[], str],
            phase: str,
        ):
            return _v6_transactional_batch_call(
                harness,
                adapter,
                run_manifest,
                endpoint_lease=endpoint_lease,
                critic_school_id=critic_school_id,
                target_ids=selected_targets,
                assignment_refs=transaction_assignment_refs,
                coverage_attempt_index=transaction_attempt_index,
                phase=phase,
                caller_trigger_ref=transaction_trigger_ref,
                pack_factory=pack_factory,
                recover_existing=resuming_atomic_decomposition,
            )

        incomplete = [
            transition
            for transition in harness.workflow_state.contract_decomposition_by_source_work.values()
            if transition.manifest_digest == run_manifest.sha256
            and transition.route_lease == expected_route_ref
            and transition.source_contract_id == "batch-critic.v2"
            and transition.atomic_contract_id == "critic.atomic-target.v1"
            and source_root_payload(transition) == expected_strong_payload
            and transition.id
            not in harness.workflow_state.contract_decomposition_completion_by_transition
        ]
        if len(incomplete) > 1:
            raise ValueError("atomic criticism history is ambiguous")
        if incomplete:
            resuming_atomic_decomposition = True
            decomposition_transition = incomplete[0]
            output, llm_call = execute_atomic_transition(
                decomposition_transition
            )
        else:
            try:
                output, llm_call = transactional_call(
                    tuple(target_ids),
                    primary_pack_factory,
                    "primary",
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
                    resolve_route_seat_contract_decomposition(
                        run_manifest,
                        role="argumentative_critic",
                        seat=endpoint_lease.seat,
                        endpoint_id=endpoint_lease.route.endpoint_id,
                        route_sha256=expected_route_ref.route_sha256,
                        source_contract_id="batch-critic.v2",
                    )
                except RunManifestError as authority_error:
                    if authority_error.code in {
                        "V6_CONTRACT_DECOMPOSITION_AUTHORITY_REQUIRED",
                        "V6_CONTRACT_DECOMPOSITION_GRANT_REQUIRED",
                    }:
                        # The strong batch is already durably schema-exhausted.
                        # No separately frozen edge means no atomic provider work.
                        raise exhausted
                    raise
                atomic_packs = {
                    target_id: _condition_pack(
                        render_crit_pack(
                            target_id,
                            harness.state,
                            harness.commitments,
                            harness.blobs,
                            token_budget=_conditioned_budget(
                                config.PACK_TOKEN_BUDGET, school_prefix
                            ),
                        ),
                        school_prefix,
                    )
                    for target_id in target_ids
                }
                decomposition_transition = harness.activate_contract_decomposition(
                    run_manifest,
                    source_work_id,
                    child_contexts=tuple(atomic_packs.items()),
                )
                output, llm_call = execute_atomic_transition(
                    decomposition_transition
                )
    else:
        pack = primary_pack_factory()
        output, llm_call = adapter.call(
            "argumentative_critic",
            pack,
            BatchCriticOutput,
            template_role="batch_critic",
            **call_kwargs,
        )
    effect_source_call_seq = _llm_event_seq(harness, llm_call) if active_v6 else None
    if active_v6 and effect_source_call_seq is None:
        raise RuntimeError("v6 criticism has no durable source call")
    criticism_completed = False
    try:
        result = _crit_argumentative_batch_result(
            harness,
            target_ids,
            adapter,
            config,
            output,
            llm_call,
            authority=authority,
            call_kwargs=call_kwargs,
            school_prefix=school_prefix,
            critic_school_id=critic_school_id,
            transactional_call=transactional_call,
            llm_already_recorded=active_v6,
            restart_safe=resuming_atomic_decomposition,
            decomposition_transition_ref=(
                decomposition_transition.id
                if decomposition_transition is not None
                else None
            ),
            allow_provider_followup=decomposition_transition is None,
            effect_source_call_seq=effect_source_call_seq,
            effect_source_call_seqs=(
                {
                    target_id: _llm_event_seq(harness, atomic_call)
                    for target_id, atomic_call in atomic_call_by_target.items()
                }
                if atomic_call_by_target
                else None
            ),
        )
        if decomposition_transition is not None:
            harness.complete_contract_decomposition(
                run_manifest,
                decomposition_transition,
                admitted_effect_refs=tuple(item.id for item in result),
            )
        criticism_completed = True
        return result
    finally:
        if criticism_completed or not active_v6:
            if atomic_call_by_target:
                for target_id, atomic_call in atomic_call_by_target.items():
                    _observe_coverage(
                        harness,
                        (target_id,),
                        atomic_call,
                        coverage_observer,
                    )
            else:
                _observe_coverage(
                    harness,
                    tuple(target_ids),
                    llm_call,
                    coverage_observer,
                )


def _apply_counterexample_retry_result(
    harness,
    output: BatchCriticOutput,
    fallback_cases: Mapping[str, str],
    llm_call,
    *,
    critic_school_id: str | None,
    llm_already_recorded: bool = False,
    restart_safe: bool = False,
    effect_source_call_seq: int | None = None,
) -> tuple[list[Artifact], list[dict]]:
    """Apply one retry response through the ordinary counterexample path."""

    critics: list[Artifact] = []
    pending = None if llm_already_recorded else llm_call
    seen: set[str] = set()
    rejected: list[dict] = []
    for case in output.cases:
        if case.target not in fallback_cases or case.target in seen:
            continue
        seen.add(case.target)
        if not case.attack:
            continue
        before = set(harness.state.artifacts)
        grounded, reason = try_counterexample(
            harness,
            case.target,
            case.counterexample,
            case=case.case.strip() or fallback_cases[case.target],
            llm=pending,
            critic_school_id=critic_school_id,
            restart_safe=restart_safe,
            effect_source_call_seq=effect_source_call_seq,
        )
        if grounded is not None:
            critics.append(grounded)
            if grounded.id not in before:
                pending = None
            continue
        rejected.append(
            {
                "target": case.target,
                "counterexample": case.counterexample,
                "reason": reason,
                "case": case.case,
            }
        )
    if pending is not None:
        inputs = ["batch-crit-cx-retry", *sorted(fallback_cases)]
        if effect_source_call_seq is not None:
            inputs.append(f"source:{effect_source_call_seq}")
        harness.record_measure(inputs=inputs, llm=pending)
    return critics, rejected


def _crit_argumentative_batch_result(
    harness,
    target_ids: list[str],
    adapter,
    config,
    output: BatchCriticOutput,
    llm_call,
    *,
    authority: str,
    call_kwargs: dict,
    school_prefix: str,
    critic_school_id: str | None,
    transactional_call=None,
    llm_already_recorded: bool = False,
    restart_safe: bool = False,
    effect_source_call_seq: int | None = None,
    effect_source_call_seqs: Mapping[str, int] | None = None,
    allow_provider_followup: bool = True,
    decomposition_transition_ref: str | None = None,
) -> list[Artifact]:
    """Process one already-returned batch without changing its route policy."""

    critics: list[Artifact] = []
    ruled: set[str] = set()
    rejected: list[dict] = []  # execution-backed targets queued for cx retry
    # The shared call must be logged on exactly one committed event. Attach it
    # to the first registration that actually COMMITS (a deduped critic
    # commits no event), and fall back to a Measure if none do.
    llm_pending: object | None = None if llm_already_recorded else llm_call
    for case in output.cases:
        if case.target not in target_ids or case.target in ruled:
            continue
        ruled.add(case.target)
        if not case.attack or not case.case.strip():
            continue  # no fault found for this target: registers nothing
        case_source_call_seq = (
            effect_source_call_seqs.get(case.target, effect_source_call_seq)
            if effect_source_call_seqs is not None
            else effect_source_call_seq
        )
        before = set(harness.state.artifacts)
        grounded, reason = try_counterexample(
            harness,
            case.target,
            case.counterexample,
            case=case.case,
            llm=llm_pending,
            critic_school_id=critic_school_id,
            restart_safe=restart_safe,
            effect_source_call_seq=case_source_call_seq,
        )
        if grounded is not None:
            critics.append(grounded)
            if grounded.id not in before:
                llm_pending = None  # a real event carried the shared call
            continue
        if execution_backed(harness, case.target):
            # Execution supremacy (§3): reality overrides the argument. Log the
            # override (llm=None — the shared call is accounted exactly once
            # elsewhere) and queue the target for the counterexample retry.
            override_inputs = ["arg-crit-overridden-by-execution", case.target]
            if case_source_call_seq is not None:
                override_inputs.append(f"source:{case_source_call_seq}")
            existing_overrides = [
                event
                for event in harness.log.read()
                if event.rule == Rule.MEASURE
                and list(event.inputs) == override_inputs
            ]
            if len(existing_overrides) > 1:
                raise RuntimeError("execution override criticism effect is duplicated")
            if not restart_safe or not existing_overrides:
                harness.record_measure(inputs=override_inputs)
            if _has_property_oracle(harness, case.target):
                rejected.append(
                    {
                        "target": case.target,
                        "counterexample": case.counterexample,
                        "reason": reason,
                        "case": case.case,
                    }
                )
            continue
        # Authority gate (RC1), per target; the shared call stays accounted
        # exactly once (observe/trial consume llm_pending when passed).
        if authority == "observe_only":
            critic = _observe_case(
                harness,
                case.target,
                case.case,
                llm_pending,
                critic_school_id=critic_school_id,
                restart_safe=restart_safe,
                effect_source_call_seq=case_source_call_seq,
            )
            llm_pending = None  # accounted inside _observe_case
            critics.append(critic)
            continue
        if authority == "trial_required":
            from deepreason.informal.trial import run_argument_trial_from_case

            trial_critic = run_argument_trial_from_case(
                harness,
                adapter,
                config,
                case.target,
                case.case,
                llm_pending,
                authority="status",
                critic_school_id=critic_school_id,
            )
            if llm_pending is not None:
                llm_pending = None  # accounted inside the trial (trial-llm)
            if trial_critic is not None:
                critics.append(trial_critic)
            continue
        case_hash = sha256_hex(case.case.encode())[:16]
        nu = _register_nu(
            harness,
            f"nu: argumentative case {case_hash} against {case.target} is sound",
            critic_school_id=critic_school_id,
        )
        warrant = Warrant(
            id=f"w:arg:{case_hash}:{case.target}",
            target=case.target,
            type=WarrantType.ARGUMENTATIVE,
            validity_node=nu.id,
        )
        before = set(harness.state.artifacts)
        critic = harness.create_artifact(
            case.case,
            provenance=Provenance(role="critic", school=critic_school_id),
            warrants=[warrant],
            rule=Rule.CRIT,
            llm=llm_pending,
        )
        critics.append(critic)
        if critic.id not in before:
            llm_pending = None  # a real event carried the call
    # Counterexample retry (§3): ONE shared follow-up call per round for every
    # overridden attack, echoing each gate/oracle rejection reason. Same
    # batching philosophy as above — the call is shared, warrants per-target.
    retry_limit = max(0, config.CX_RETRY_MAX) if allow_provider_followup else 0
    for retry_index in range(retry_limit):
        if not rejected:
            break
        retry_inputs = [dict(item) for item in rejected]
        allowed = {item["target"]: item for item in retry_inputs}

        def retry_pack_factory() -> str:
            retry_pack = render_cx_retry_pack(
                retry_inputs,
                harness.state,
                harness.commitments,
                harness.blobs,
                token_budget=_conditioned_budget(config.PACK_TOKEN_BUDGET, school_prefix),
            )
            return _condition_pack(retry_pack, school_prefix)

        if transactional_call is not None:
            retry_out, retry_llm = transactional_call(
                tuple(sorted(allowed)),
                retry_pack_factory,
                f"counterexample_retry:{retry_index}",
            )
        else:
            retry_pack = retry_pack_factory()
            retry_out, retry_llm = adapter.call(
                "argumentative_critic",
                retry_pack,
                BatchCriticOutput,
                template_role="batch_critic",
                **call_kwargs,
            )
        retry_source_call_seq = (
            _llm_event_seq(harness, retry_llm)
            if transactional_call is not None
            else None
        )
        if transactional_call is not None and retry_source_call_seq is None:
            raise RuntimeError("v6 criticism retry has no durable source call")
        retry_critics, rejected = _apply_counterexample_retry_result(
            harness,
            retry_out,
            {target: str(value.get("case", "")) for target, value in allowed.items()},
            retry_llm,
            critic_school_id=critic_school_id,
            llm_already_recorded=(transactional_call is not None),
            restart_safe=restart_safe,
            effect_source_call_seq=retry_source_call_seq,
        )
        critics.extend(retry_critics)
    if llm_pending is not None:
        # Nothing committed the call (no attacks, or every critic deduped).
        harness.record_measure(inputs=["batch-crit", *target_ids], llm=llm_pending)
    if decomposition_transition_ref is not None:
        for critic in critics:
            marker = [
                "contract-decomposition-effect",
                decomposition_transition_ref,
                critic.id,
            ]
            existing = [
                event
                for event in harness.log.read()
                if event.rule == Rule.MEASURE and list(event.inputs) == marker
            ]
            if len(existing) > 1:
                raise RuntimeError("contract decomposition effect is duplicated")
            if not existing:
                harness.record_measure(inputs=marker)
    return critics
