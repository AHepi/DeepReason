"""Trial protocol (spec §3 rubric-verdict guard; §10.2 comparative modes).

The rubric judge is never asked "is this good?" — only the narrow question
the pack poses. Flow: critic drafts the case for fail citing specific
clauses; defender answers; judge rules with a decisive_point. Program
checks then screen the ruling: referential integrity (decisive_point must
resolve to an element of the exchange), order-swap consistency (anchored/
pairwise), paraphrase spot-check, ensemble agreement across families.
Only surviving rulings package warrants; trace_ref = full transcript + all
check results (a warrant-validity condition, §2 — it suppresses noise,
never criticism). Blocked rulings are logged as Measure events; a streak
of blocks is a critic-gaming signal.
"""

import hashlib
import json

from deepreason.authority import TrialAuthority
from deepreason.informal.standards import precedent_slice, resolve_standard, standard_body
from deepreason.llm.contracts import (
    ArgumentativeCriticOutput,
    DefenderOutput,
    JudgeRuling,
    PairwiseRuling,
    VariatorOutput,
)
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.firewall import route_fingerprint
from deepreason.llm.packs import aliases_for_values
from deepreason.llm.repair import SchemaRepairError
from deepreason.llm.wire import wire_contract_for
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology import Interface, Provenance, Ref, Rule, Warrant, WarrantType
from deepreason.programs import content_text
from deepreason.rules.warrants import (
    execution_backed,
    formally_backed,
    register_fail_warrant,
)


def _v6_trial_manifest(adapter):
    """The bound v6 manifest, or None outside RunManifest v6 authority.

    Mirrors ``rules/crit.py``'s own self-detection
    (``adapter.bound_v6_manifest()``): lease resolution stays inside
    ``llm/`` (SEAM-llm-x-rules.md), this module only asks the adapter
    whether it is currently bound.
    """

    if not getattr(adapter, "transaction_authority_required", False):
        return None
    return adapter.bound_v6_manifest()


def _v6_transactional_trial_call(
    harness,
    adapter,
    manifest,
    *,
    role: str,
    target_id: str,
    step: str,
    pack: str,
    output_model,
    seat: int = 0,
    aliases=None,
):
    """Authorize and terminalize one v6 defended-trial provider boundary.

    Mirrors ``rules/crit.py::_v6_transactional_batch_call`` (the same-
    package precedent) and ``bridge/transactional_adapter.py``'s generic
    single-call wrapper: one durable preparation, a call-local context
    plan, one atomic issue, and a typed provider/admission/terminal
    sequence. ``step`` uniquely identifies this exact call within one
    trial invocation (``"defender"``, ``"judge:0"``, ...), folded into the
    trigger digest exactly as ``phase`` is for the batch-critic call.
    """

    from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
    from deepreason.workflow.transaction import (
        ContextNamespace,
        VisibleContextItemV1,
        WorkBudgetDenied,
    )
    from deepreason.workflow.transaction_service import InquiryTransactionService

    meter = getattr(adapter, "meter", None)
    if meter is None:
        raise ValueError("v6 trial dispatch requires a provider token meter")
    lease = adapter.bound_v6_default_lease(role, seat)
    route_ref = RouteLeaseRefV1(
        role=role,
        seat=lease.seat,
        endpoint_id=lease.route.endpoint_id,
        route_sha256=route_fingerprint(lease.route),
    )
    profile = adapter.profile_for(role, lease.seat, endpoint_lease=lease)
    contract = wire_contract_for(role, output_model, profile, aliases)
    payload = {
        "schema": "defended-trial-step.v1",
        "role": role,
        "target_id": target_id,
        "step": step,
    }
    service = InquiryTransactionService(harness, manifest, meter)
    fence = max(0, harness._next_seq - 1)
    trigger_ref = "trial:" + hashlib.sha256(canonical_json(payload)).hexdigest()
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.DEFENDED_TRIAL_STEP,
        attempt_index=0,
        route_lease=route_ref,
        contract_id=contract.contract_id,
        trigger_ref=trigger_ref,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
        target_refs=(target_id,),
        input_refs=(),
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
        rendered_bytes = len(pack.encode("utf-8"))
        digest = hashlib.sha256(pack.encode("utf-8")).hexdigest()
        object_ref = harness.blobs.put(pack.encode("utf-8"))
        items = (
            VisibleContextItemV1(
                namespace=ContextNamespace.SOURCE,
                alias="SRC_001",
                object_ref=object_ref,
                content_sha256=digest,
                planned_bytes=rendered_bytes,
            ),
        )
        plan = service.context_plan(
            preparation,
            plan_kind="dossier",
            items=items,
            maximum_bytes=rendered_bytes,
            rendered_bytes=rendered_bytes,
        )
        prompt, preview_contract, preview_lease, maximum_tokens = adapter.preview_request(
            role,
            pack,
            output_model,
            endpoint_index=lease.seat,
            wire_contract=contract,
            aliases=aliases,
            endpoint_lease=lease,
        )
        if preview_contract is not contract or preview_lease != lease:
            raise ValueError("v6 trial preview changed frozen call authority")
        authorized = service.issue(
            preparation,
            plans=(plan,),
            prompt=prompt,
            max_tokens=maximum_tokens,
        )
    except WorkBudgetDenied:
        raise
    except Exception:
        abandon(issued=False, reason_code="trial_preissue_failure")
        raise

    provider = None
    try:
        output, llm_call = adapter.call(
            role,
            pack,
            output_model,
            endpoint_index=lease.seat,
            wire_contract=contract,
            aliases=aliases,
            endpoint_lease=lease,
            dispatch_authorization=authorized,
        )
    except EndpointError as error:
        spend = getattr(error, "spend", None)
        if spend is None:
            abandon(issued=True, reason_code="trial_transport_result_unknown")
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
                reason_code="trial_transport_failure",
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
            role=role,
            pack=pack,
            output_model=output_model,
            wire_contract=contract,
            endpoint_index=lease.seat,
            endpoint_lease=lease,
            reason_prefix="trial",
        )
        output = repaired.output
        llm_call = repaired.llm_call
        preparation = repaired.preparation
        authorized = repaired.authorized
        provider = repaired.provider_attempt
    except Exception:
        abandon(issued=True, reason_code="trial_authority_failure")
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
        reason_code="trial_output_admitted",
        usage_status="exact",
        prompt_tokens=llm_call.prompt_tokens,
        completion_tokens=llm_call.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    return output, llm_call


def conforming_transcript(blobs, trace_ref: str) -> bool:
    """Well-formedness (§2): a rubric-derived warrant's trace_ref must hold
    a conforming trial transcript — re-checkable by program."""
    try:
        data = json.loads(blobs.get(trace_ref))
    except (KeyError, ValueError):
        return False
    if not isinstance(data, dict):
        return False
    ruling = data.get("ruling") or {}
    decisive = ruling.get("decisive_point", "")
    exchange = f"{data.get('case', '')}\n{data.get('answer', '')}"
    return bool(
        data.get("case")
        and data.get("answer")
        and decisive
        and decisive in exchange
        and isinstance(data.get("checks"), dict)
    )


def transcript_blob(harness, *, case: str, answer: str, decisive_point: str,
                    checks: dict | None = None, **meta) -> str:
    """Store a transcript; returns the trace_ref blob hash."""
    data = {"case": case, "answer": answer,
            "ruling": {"verdict": "fail", "decisive_point": decisive_point},
            "checks": checks or {}, **meta}
    return harness.blobs.put(canonical_json(data))


def _block(harness, reason: str, target_id: str, diagnostics) -> None:
    harness.record_measure(inputs=[f"trial-blocked:{reason}", target_id])
    if diagnostics is not None:
        diagnostics.append({"trial": target_id[:12], "blocked": reason})
    return None


def _decline(harness, target_id: str, reason: str, diagnostics) -> None:
    """Non-sustained argument-trial outcome: a logged Measure, never a
    warrant (phase C trial_required contract)."""
    harness.record_measure(inputs=["trial-declined", target_id, reason])
    if diagnostics is not None:
        diagnostics.append({"trial": target_id[:12], "declined": reason})
    return None


def _coerce_trial_authority(authority: TrialAuthority | str) -> TrialAuthority:
    return authority if isinstance(authority, TrialAuthority) else TrialAuthority(authority)


def _record_trial_observation(
    harness,
    *,
    target_id: str,
    commitment_id: str,
    standard_id: str,
    case: str,
    answer: str,
    rulings: list,
    checks: dict,
    outcome: str,
    trace_ref: str | None,
    llm_call,
    diagnostics,
):
    """Record a completed advisory rubric trial without an attack edge."""

    payload = {
        "trial_observation": {
            "kind": "rubric",
            "target": target_id,
            "commitment": commitment_id,
            "standard": standard_id,
            "case": case,
            "answer": answer,
            "rulings": [ruling.model_dump(mode="json") for ruling in rulings],
            "checks": checks,
            "outcome": outcome,
            "trace_ref": trace_ref,
        }
    }
    before = set(harness.state.artifacts)
    observation = harness.create_artifact(
        json.dumps(payload, sort_keys=True),
        codec="json",
        provenance=Provenance(role="critic"),
        rule=Rule.CRIT,
        llm=llm_call,
    )
    carried = observation.id not in before
    harness.record_measure(
        inputs=["trial-observation", target_id, observation.id, outcome],
        llm=None if carried else llm_call,
    )
    if diagnostics is not None:
        diagnostics.append({"trial": target_id[:12], "advisory": outcome})
    return observation


def _advisory_trial_result(
    harness,
    *,
    target_id: str,
    commitment_id: str,
    standard_id: str,
    case: str,
    answer: str,
    rulings: list,
    checks: dict,
    outcome: str,
    trace_ref: str | None,
    llm_call,
    diagnostics,
    calls: list,
):
    observation = _record_trial_observation(
        harness,
        target_id=target_id,
        commitment_id=commitment_id,
        standard_id=standard_id,
        case=case,
        answer=answer,
        rulings=rulings,
        checks=checks,
        outcome=outcome,
        trace_ref=trace_ref,
        llm_call=llm_call,
        diagnostics=diagnostics,
    )
    # The representative judge call is carried by either the observation
    # artifact or its dedupe Measure; the finally block must not log it again.
    if llm_call is not None and llm_call in calls:
        calls.remove(llm_call)
    return observation


def _judge_pack(harness, config, body, target_text, case, answer,
                standard_id, anchor_text=None, swapped=False) -> str:
    lines = [f"STANDARD {body['spec']} (mode: {body['mode']}):", body["rubric"], ""]
    precedents = precedent_slice(harness, standard_id, config.PRECEDENT_K)
    if precedents:
        lines.append("PRECEDENTS (user rulings first):")
        lines += [f"- {p['holding']}" for p in precedents]
        lines.append("")
    if body["mode"] == "anchored" and anchor_text is not None:
        first = ("KNOWN-BAD ANCHOR", anchor_text) if swapped else ("CANDIDATE", target_text)
        second = ("CANDIDATE", target_text) if swapped else ("KNOWN-BAD ANCHOR", anchor_text)
        lines += [f"{first[0]}:\n{first[1]}", "", f"{second[0]}:\n{second[1]}", "",
                  "QUESTION: does the CANDIDATE beat the anchor on the standard's "
                  "criteria? verdict=pass iff it does."]
    else:
        lines += [f"TARGET:\n{target_text}", "",
                  "QUESTION: does the case establish that the target violates the "
                  "cited clause? verdict=fail iff it does."]
    lines += ["", "THE CASE FOR FAIL:", case, "", "THE DEFENCE:", answer, "",
              "Rule on the exchange; decisive_point MUST quote a span of it."]
    return "\n".join(lines)


def _judge_all(
    harness,
    adapter,
    pack: str,
    diagnostics,
    target_id,
    calls: list,
    aliases,
    *,
    manifest=None,
    step_prefix: str = "judge",
):
    """Rule with the full ensemble; disagreement blocks (never averaged).
    Appends every seat's LLMCall to the CALLER's list as it lands — a local
    list dropped seat 1's completed spend whenever a later seat raised
    (found by the mock accounting sweep: judge2-storm leaked seat 1).

    ``manifest`` is the bound v6 manifest (or None outside v6 authority,
    the default — the rubric/pairwise call sites never pass it, so their
    behavior is unchanged): when set, every seat's call is authorized
    through ``_v6_transactional_trial_call`` instead of the legacy
    ``adapter.call``, and is NOT appended to ``calls`` — a v6 call is
    already durably recorded on its own PROVIDER_RESULT transaction event
    (harness.py: "only provider_result may carry an LLM call"), so folding
    it into the caller's own ``trial-llm`` Measure sweep too would attach
    the same LLMCall to a second control-plane action, which
    ``WorkflowReplayState.observe_event`` correctly refuses
    ("transactional provider call lacks live issued authority")."""
    judge_seats = adapter.judge_seats()

    def _dispatch(index: int):
        if manifest is not None:
            return _v6_transactional_trial_call(
                harness,
                adapter,
                manifest,
                role="judge",
                target_id=target_id,
                step=f"{step_prefix}:{index}",
                pack=pack,
                output_model=JudgeRuling,
                seat=index,
                aliases=aliases,
            )
        return adapter.call(
            "judge", pack, JudgeRuling, endpoint_index=index, aliases=aliases
        )

    ruling, first = _dispatch(0)
    if manifest is None:
        calls.append(first)
    seat_calls = [first]
    seat_rulings = [ruling]
    for index in range(1, len(judge_seats)):
        other, call = _dispatch(index)
        if manifest is None:
            calls.append(call)
        seat_calls.append(call)
        seat_rulings.append(other)
        if other.verdict != ruling.verdict:
            return None, seat_calls, seat_rulings  # critic-gaming signal
    return ruling, seat_calls, seat_rulings


def run_trial(harness, target_id: str, commitment, adapter, config,
              diagnostics: list | None = None, embedder=None, *,
              authority: TrialAuthority | str = TrialAuthority.OBSERVE_ONLY):
    """Full §3 guard in status or advisory mode.

    Status mode preserves the historical warrant path. Advisory mode records
    the critic case, defence, rulings, and guard result as an observation
    artifact, never a warrant or attack edge.
    """
    authority = _coerce_trial_authority(authority)
    # The trial needs critic + defender + judge (variator is optional, §3);
    # a config missing any is a logged no-op, not a mid-run KeyError crash.
    for role in ("argumentative_critic", "defender", "judge"):
        if not adapter.has_role(role):
            return _block(harness, f"no-{role}-role", target_id, diagnostics)
    # Normative rubric policy is a process preflight, not a model decision.
    # Check the immutable leases before even the critic or defender endpoint
    # can be called, so a malformed convenience adapter cannot partially run.
    adapter.require_cross_family_judges()
    # Every call the trial makes reaches the log exactly once (§0): the
    # decisive ruling rides the critic event; everything else — critic case,
    # defence, extra ensemble seats, order-swap and paraphrase re-rulings,
    # including on blocked / no-case / exception exits — lands as trial-llm
    # Measure events. (A live run showed 85% of trial spend was invisible to
    # the log before this: 38 of 44 calls never reached any event.)
    calls: list = []
    try:
        return _trial_steps(
            harness, target_id, commitment, adapter, config, diagnostics, calls, authority
        )
    finally:
        harness.record_llm_calls(calls, "trial-llm")


def _trial_steps(harness, target_id: str, commitment, adapter, config,
                 diagnostics, calls: list, authority: TrialAuthority):
    spec_id = commitment.eval.split(":", 1)[1]
    standard = resolve_standard(harness, spec_id)
    if standard is None:
        return _block(harness, "unresolved-standard", target_id, diagnostics)
    body = standard_body(harness, standard)
    target_text = content_text(harness.state.artifacts[target_id], harness.blobs)
    case_hint = commitment.budget.extra.get("case", "")

    # 1. The critic drafts the case for fail, citing specific clauses.
    critic_pack = "\n".join([
        f"STANDARD {body['spec']}:", body["rubric"], "",
        f"FORBIDDEN CASE UNDER TRIAL: {case_hint}" if case_hint else "",
        f"TARGET:\n{target_text}", "",
        "Draft the strongest case that the target violates the standard, citing "
        "specific clauses/cases — or attack=false if none exists.",
    ])
    critic_aliases = aliases_for_values([target_text], prefix="A")
    critic_contract = wire_contract_for(
        "argumentative_critic",
        ArgumentativeCriticOutput,
        adapter.profile_for("argumentative_critic"),
        critic_aliases,
        expected_target=target_text,
    )
    case_out, call = adapter.call(
        "argumentative_critic",
        critic_pack,
        ArgumentativeCriticOutput,
        aliases=critic_aliases,
        wire_contract=critic_contract,
    )
    calls.append(call)
    if not case_out.attack or not case_out.case.strip():
        return None  # no case, no trial

    # 2. The defender answers.
    defence_pack = f"THE CASE AGAINST THE TARGET:\n{case_out.case}\n\nTARGET:\n{target_text}"
    defence, call = adapter.call(
        "defender",
        defence_pack,
        DefenderOutput,
        aliases=aliases_for_values([case_out.case], prefix="K"),
    )
    calls.append(call)

    # 3. The judge rules on the exchange (precedent slice in the pack).
    anchor_text = None
    if body["mode"] == "anchored":
        anchors = body.get("anchors", [])
        if anchors and anchors[0] in harness.state.artifacts:
            anchor_text = content_text(harness.state.artifacts[anchors[0]], harness.blobs)
    pack = _judge_pack(harness, config, body, target_text, case_out.case,
                       defence.answer, standard.id, anchor_text)
    judge_aliases = aliases_for_values(
        [case_out.case, defence.answer], prefix="K"
    )
    ruling, judge_calls, judge_rulings = _judge_all(
        harness, adapter, pack, diagnostics, target_id, calls, judge_aliases
    )
    if ruling is None:
        if authority == TrialAuthority.OBSERVE_ONLY:
            return _advisory_trial_result(
                harness,
                target_id=target_id,
                commitment_id=commitment.id,
                standard_id=standard.id,
                case=case_out.case,
                answer=defence.answer,
                rulings=judge_rulings,
                checks={"ensemble": len(adapter.require_cross_family_judges())},
                outcome="blocked:ensemble-split",
                trace_ref=None,
                llm_call=judge_calls[0],
                diagnostics=diagnostics,
                calls=calls,
            )
        return _block(harness, "ensemble-split", target_id, diagnostics)
    if ruling.verdict != "fail":
        if authority == TrialAuthority.OBSERVE_ONLY:
            return _advisory_trial_result(
                harness,
                target_id=target_id,
                commitment_id=commitment.id,
                standard_id=standard.id,
                case=case_out.case,
                answer=defence.answer,
                rulings=judge_rulings,
                checks={"ensemble": len(adapter.require_cross_family_judges())},
                outcome="defence-sustained",
                trace_ref=None,
                llm_call=judge_calls[0],
                diagnostics=diagnostics,
                calls=calls,
            )
        return None  # the work survives; nothing registers

    exchange = f"{case_out.case}\n{defence.answer}"
    checks: dict = {"ensemble": len(adapter.require_cross_family_judges())}

    # 4. Referential integrity (program check).
    if any(item.decisive_point not in exchange for item in judge_rulings):
        if authority == TrialAuthority.OBSERVE_ONLY:
            return _advisory_trial_result(
                harness,
                target_id=target_id,
                commitment_id=commitment.id,
                standard_id=standard.id,
                case=case_out.case,
                answer=defence.answer,
                rulings=judge_rulings,
                checks=checks,
                outcome="blocked:referential-integrity",
                trace_ref=None,
                llm_call=judge_calls[0],
                diagnostics=diagnostics,
                calls=calls,
            )
        return _block(harness, "referential-integrity", target_id, diagnostics)
    checks["referential_integrity"] = True

    # 5. Order-swap consistency (anchored/pairwise modes).
    if body["mode"] in ("anchored", "pairwise") and anchor_text is not None:
        swapped_pack = _judge_pack(harness, config, body, target_text, case_out.case,
                                   defence.answer, standard.id, anchor_text, swapped=True)
        swapped, _, swapped_rulings = _judge_all(
            harness,
            adapter,
            swapped_pack,
            diagnostics,
            target_id,
            calls,
            judge_aliases,
        )
        if swapped is None or swapped.verdict != ruling.verdict:
            if authority == TrialAuthority.OBSERVE_ONLY:
                return _advisory_trial_result(
                    harness,
                    target_id=target_id,
                    commitment_id=commitment.id,
                    standard_id=standard.id,
                    case=case_out.case,
                    answer=defence.answer,
                    rulings=judge_rulings + swapped_rulings,
                    checks=checks,
                    outcome="blocked:order-swap",
                    trace_ref=None,
                    llm_call=judge_calls[0],
                    diagnostics=diagnostics,
                    calls=calls,
                )
            return _block(harness, "order-swap", target_id, diagnostics)
        if any(item.decisive_point not in exchange for item in swapped_rulings):
            if authority == TrialAuthority.OBSERVE_ONLY:
                return _advisory_trial_result(
                    harness,
                    target_id=target_id,
                    commitment_id=commitment.id,
                    standard_id=standard.id,
                    case=case_out.case,
                    answer=defence.answer,
                    rulings=judge_rulings + swapped_rulings,
                    checks=checks,
                    outcome="blocked:referential-integrity",
                    trace_ref=None,
                    llm_call=judge_calls[0],
                    diagnostics=diagnostics,
                    calls=calls,
                )
            return _block(harness, "referential-integrity", target_id, diagnostics)
        checks["order_swap"] = "pass"
    else:
        checks["order_swap"] = "skipped"

    # 6. Paraphrase spot-check: every re-ruling uses the same preflighted
    # cross-family ensemble as the decisive ruling.  A lone seat can never
    # issue (or preserve) a rubric warrant: either a split or a unanimous
    # non-fail blocks the trial.
    paraphrase_result, block_reason = _paraphrase_screen(
        harness, adapter, config, pack, exchange, target_id, diagnostics, calls
    )
    if block_reason is not None:
        if authority == TrialAuthority.OBSERVE_ONLY:
            return _advisory_trial_result(
                harness,
                target_id=target_id,
                commitment_id=commitment.id,
                standard_id=standard.id,
                case=case_out.case,
                answer=defence.answer,
                rulings=judge_rulings,
                checks=checks,
                outcome=f"blocked:{block_reason}",
                trace_ref=None,
                llm_call=judge_calls[0],
                diagnostics=diagnostics,
                calls=calls,
            )
        return _block(harness, block_reason, target_id, diagnostics)
    checks["paraphrase"] = paraphrase_result

    # Package: transcript blob, nu MENTIONING the standard (case-law closure
    # extension, §1), ordinary demonstrative warrant, critic artifact.
    trace_ref = transcript_blob(
        harness, case=case_out.case, answer=defence.answer,
        decisive_point=ruling.decisive_point, checks=checks,
        target=target_id, commitment=commitment.id, standard=standard.id,
        mode=body["mode"],
    )
    judge_llm = judge_calls[0]
    if authority == TrialAuthority.OBSERVE_ONLY:
        return _advisory_trial_result(
            harness,
            target_id=target_id,
            commitment_id=commitment.id,
            standard_id=standard.id,
            case=case_out.case,
            answer=defence.answer,
            rulings=judge_rulings,
            checks=checks,
            outcome="sustained",
            trace_ref=trace_ref,
            llm_call=judge_llm,
            diagnostics=diagnostics,
            calls=calls,
        )
    before = set(harness.state.artifacts)
    critic = register_fail_warrant(
        harness,
        commitment_id=commitment.id,
        target_id=target_id,
        nu_content=f"nu: the trial ruling under {body['spec']} on {target_id} is sound",
        nu_interface=Interface(refs=[Ref(target=standard.id, role="mention")]),
        critic_content=(
            f"critic: trial fail under {body['spec']} on {target_id[:12]} — "
            f"{ruling.decisive_point[:100]}"
        ),
        trace_ref=trace_ref,
        llm=judge_llm,
    )
    # The decisive ruling rides the critic event ONLY if one actually
    # committed: a byte-identical critic (same target, same spec, same
    # decisive quote from a second rubric kappa) content-address-dedupes,
    # committing nothing — the 1M arrow run leaked 13 judge rulings this
    # way (verify_root delta 10,022). Uncommitted => the call stays in
    # ``calls`` and lands as trial-llm.
    if critic is not None and critic.id not in before:
        calls.remove(judge_llm)
    return critic


def _paraphrase_screen(
    harness, adapter, config, pack: str, exchange: str, target_id: str,
    diagnostics, calls: list, *, manifest=None,
):
    """Shared paraphrase spot-check. Returns (checks_value, block_reason):
    block_reason is None when the fail ruling survived every meaning-
    preserving paraphrase (or the variator role is absent).

    ``manifest`` is the bound v6 manifest (or None, the default — the
    rubric call site never passes it): when set, the variator call and
    every re-ruling's judge-ensemble calls are authorized through
    ``_v6_transactional_trial_call``."""
    if not adapter.has_role("variator"):
        return "skipped", None
    n = config.TRIAL_PARAPHRASE_N
    if manifest is not None:
        para_out, call = _v6_transactional_trial_call(
            harness,
            adapter,
            manifest,
            role="variator",
            target_id=target_id,
            step="variator",
            pack=(
                f"TARGET CONTENT:\n{exchange}\n\nDIRECTIVE: produce exactly {n} "
                "meaning-preserving paraphrases of this exchange."
            ),
            output_model=VariatorOutput,
        )
    else:
        para_out, call = adapter.call(
            "variator",
            f"TARGET CONTENT:\n{exchange}\n\nDIRECTIVE: produce exactly {n} "
            "meaning-preserving paraphrases of this exchange.",
            VariatorOutput,
        )
    if manifest is None:
        calls.append(call)
    flips = 0
    for index, paraphrase in enumerate([e.content for e in para_out.edits[:n]]):
        repack = pack.replace(exchange, paraphrase) if exchange in pack else (
            pack + "\n\nPARAPHRASED EXCHANGE:\n" + paraphrase)
        paraphrase_aliases = aliases_for_values([paraphrase], prefix="K")
        reruling, _, _ = _judge_all(
            harness,
            adapter,
            repack,
            diagnostics,
            target_id,
            calls,
            paraphrase_aliases,
            manifest=manifest,
            step_prefix=f"judge:paraphrase:{index}",
        )
        if reruling is None:
            return None, "ensemble-split"
        if reruling.verdict != "fail":
            flips += 1
    if flips:
        return None, "paraphrase-flip"
    return {"n": n, "flips": 0}, None


def run_argument_trial_from_case(
    harness, adapter, config, target_id: str, case_text: str, llm_call=None,
    diagnostics: list | None = None, *,
    authority: TrialAuthority | str = TrialAuthority.OBSERVE_ONLY,
    critic_school_id: str | None = None,
):
    """Defended trial over a PRECOMPUTED critic case (phase C trial_required).

    New calls are advisory by default. Explicit canonical ``status`` authority
    is required to enter the defended court path. The critic call already
    happened upstream; its LLMCall arrives as
    ``llm_call`` and is accounted here exactly once (a trial-llm Measure, or
    riding the critic registration when the decisive ruling commits; the
    upstream caller must not log it again). The defender answers, the frozen
    cross-family judge ensemble rules, and the existing guard checks screen
    the ruling (referential integrity, ensemble unanimity, paraphrase
    invariance). Only a guard-accepted sustained (fail) ruling mints the
    ARGUMENTATIVE warrant; every other outcome records a
    ["trial-declined", target, reason] Measure and registers no warrant."""
    authority = _coerce_trial_authority(authority)
    if authority == TrialAuthority.OBSERVE_ONLY:
        from deepreason.rules.crit import _observe_case

        return _observe_case(
            harness,
            target_id,
            case_text,
            llm_call,
            critic_school_id=critic_school_id,
        )
    calls: list = []
    if llm_call is not None:
        calls.append(llm_call)
    try:
        return _argument_trial_steps(
            harness,
            adapter,
            config,
            target_id,
            case_text,
            diagnostics,
            calls,
            critic_school_id=critic_school_id,
        )
    finally:
        harness.record_llm_calls(calls, "trial-llm")


def _argument_trial_steps(
    harness, adapter, config, target_id: str, case_text: str, diagnostics,
    calls: list, *, critic_school_id: str | None = None,
):
    for role in ("defender", "judge"):
        if not adapter.has_role(role):
            return _decline(harness, target_id, f"no-{role}-role", diagnostics)
    target = harness.state.artifacts.get(target_id)
    if target is None:
        return _decline(harness, target_id, "unknown-target", diagnostics)
    # Normative policy is a process preflight, not a model decision, and it
    # runs before any seat spends. Which guarantee is demanded depends on which
    # one the run's route topology can supply, never on configuration.
    if adapter.is_single_model():
        # One model in every position cannot supply cross-FAMILY independence:
        # the ensemble gate is unsatisfiable by construction, so the trial was
        # unreachable rather than strict. The substitute is cross-SCHOOL
        # CRITICISM -- the case must come from a school other than the one that
        # authored the target. It is a weaker guarantee than two model families
        # and is deliberately confined to the runs where the stronger one does
        # not exist.
        if len(adapter.leases.get("judge", ())) < 2:
            return _decline(harness, target_id, "single-judge-seat", diagnostics)
        if not critic_school_id:
            return _decline(harness, target_id, "no-critic-school", diagnostics)
        if critic_school_id == target.provenance.school:
            return _decline(harness, target_id, "same-school-critic", diagnostics)
    else:
        adapter.require_cross_family_judges()
    if formally_backed(harness, target_id):
        # Formal supremacy (§3, widened to the whole formal set): a passing
        # formal commitment stands, and a prose case cannot reach a warrant
        # against it through any trial. This is the ONLY point where prose can
        # mint one, so it is the only place the widened guard belongs: the
        # criticism rule's own execution guard still governs whether a case is
        # RECORDED, and widening that one would delete scrutiny evidence for
        # every target carrying a passing problem criterion.
        # The decline reason keeps its historical spelling: it is compared
        # against recorded roots, and renaming it would change what those
        # roots' diagnostics mean.
        return _decline(harness, target_id, "execution-backed", diagnostics)
    if not case_text.strip():
        return _decline(harness, target_id, "empty-case", diagnostics)
    target_text = content_text(target, harness.blobs)
    manifest = _v6_trial_manifest(adapter)

    # 1. The defender answers the precomputed case.
    defence_pack = f"THE CASE AGAINST THE TARGET:\n{case_text}\n\nTARGET:\n{target_text}"
    defender_aliases = aliases_for_values([case_text], prefix="K")
    if manifest is not None:
        defence, call = _v6_transactional_trial_call(
            harness,
            adapter,
            manifest,
            role="defender",
            target_id=target_id,
            step="defender",
            pack=defence_pack,
            output_model=DefenderOutput,
            aliases=defender_aliases,
        )
    else:
        defence, call = adapter.call(
            "defender",
            defence_pack,
            DefenderOutput,
            aliases=defender_aliases,
        )
    # A v6-dispatched call is already durably recorded on its own
    # PROVIDER_RESULT transaction event (see _judge_all's docstring for the
    # full "only provider_result may carry an LLM call" rationale); only
    # the legacy path needs it swept into the trial-llm Measure below.
    if manifest is None:
        calls.append(call)

    # 2. The judge ensemble rules on the exchange.
    pack = "\n".join([
        f"TARGET:\n{target_text}", "",
        "QUESTION: does the case establish a decisive fault in the target? "
        "verdict=fail iff it does.",
        "", "THE CASE FOR FAIL:", case_text, "", "THE DEFENCE:", defence.answer,
        "", "Rule on the exchange; decisive_point MUST quote a span of it.",
    ])
    judge_aliases = aliases_for_values([case_text, defence.answer], prefix="K")
    ruling, judge_calls, judge_rulings = _judge_all(
        harness, adapter, pack, diagnostics, target_id, calls, judge_aliases,
        manifest=manifest, step_prefix="judge",
    )
    if ruling is None:
        return _decline(harness, target_id, "ensemble-split", diagnostics)
    if ruling.verdict != "fail":
        return _decline(harness, target_id, "defence-sustained", diagnostics)

    exchange = f"{case_text}\n{defence.answer}"
    checks: dict = {"ensemble": len(adapter.judge_seats())}

    # 3. Referential integrity (program check).
    if any(item.decisive_point not in exchange for item in judge_rulings):
        return _decline(harness, target_id, "referential-integrity", diagnostics)
    checks["referential_integrity"] = True

    # 4. Paraphrase spot-check (same screen as the rubric trial).
    paraphrase_result, block_reason = _paraphrase_screen(
        harness, adapter, config, pack, exchange, target_id, diagnostics, calls,
        manifest=manifest,
    )
    if block_reason is not None:
        return _decline(harness, target_id, block_reason, diagnostics)
    checks["paraphrase"] = paraphrase_result

    # Package: transcript blob, nu, ARGUMENTATIVE warrant, critic artifact.
    trace_ref = transcript_blob(
        harness, case=case_text, answer=defence.answer,
        decisive_point=ruling.decisive_point, checks=checks,
        target=target_id, trial="argument",
    )
    case_hash = sha256_hex(case_text.encode())[:16]
    nu = harness.create_artifact(
        f"nu: the defended trial sustaining case {case_hash} against "
        f"{target_id} is sound",
        provenance=Provenance(role="critic", school=critic_school_id),
    )
    warrant = Warrant(
        id=f"w:argtrial:{case_hash}:{target_id}",
        target=target_id,
        type=WarrantType.ARGUMENTATIVE,
        trace_ref=trace_ref,
        validity_node=nu.id,
    )
    judge_llm = judge_calls[0]
    before = set(harness.state.artifacts)
    critic = harness.create_artifact(
        case_text,
        provenance=Provenance(role="critic", school=critic_school_id),
        warrants=[warrant],
        rule=Rule.CRIT,
        # A v6-dispatched judge_llm is already durably recorded on its own
        # PROVIDER_RESULT transaction event; attaching it again here would
        # be a second control-plane action carrying the same call
        # ("only provider_result may carry an LLM call"). The legacy path
        # rides it on the critic event instead, exactly as before.
        llm=(None if manifest is not None else judge_llm),
    )
    # The decisive ruling rides the critic event only when one actually
    # committed; a deduped critic keeps the call in ``calls`` (trial-llm).
    # Not applicable under v6: judge_llm was never appended to ``calls``.
    if manifest is None and critic.id not in before:
        calls.remove(judge_llm)
    return critic


def _record_pairwise_observation(
    harness,
    *,
    problem,
    a_id: str,
    b_id: str,
    ruling1,
    ruling2,
    winner: str | None,
    loser: str | None,
    order_swap: str,
    outcome: str,
    llm_call,
    diagnostics,
):
    """Record a pairwise comparison without an argumentative warrant."""

    payload = {
        "pairwise_observation": {
            "problem": problem.id,
            "a": a_id,
            "b": b_id,
            "winner": winner,
            "loser": loser,
            "first_ruling": ruling1.model_dump(mode="json"),
            "second_ruling": (
                ruling2.model_dump(mode="json") if ruling2 is not None else None
            ),
            "order_swap": order_swap,
            "outcome": outcome,
        }
    }
    before = set(harness.state.artifacts)
    observation = harness.create_artifact(
        json.dumps(payload, sort_keys=True),
        codec="json",
        provenance=Provenance(role="critic"),
        rule=Rule.CRIT,
        llm=llm_call,
        problem_id=problem.id,
    )
    carried = observation.id not in before
    harness.record_measure(
        inputs=["pairwise-observation", problem.id, observation.id, outcome],
        llm=None if carried else llm_call,
    )
    if diagnostics is not None:
        diagnostics.append({"pairwise": problem.id, "advisory": outcome})
    return observation


def _advisory_pairwise_result(
    harness,
    *,
    problem,
    a_id: str,
    b_id: str,
    ruling1,
    ruling2,
    winner: str | None,
    loser: str | None,
    order_swap: str,
    outcome: str,
    llm_call,
    diagnostics,
    calls: list,
):
    observation = _record_pairwise_observation(
        harness,
        problem=problem,
        a_id=a_id,
        b_id=b_id,
        ruling1=ruling1,
        ruling2=ruling2,
        winner=winner,
        loser=loser,
        order_swap=order_swap,
        outcome=outcome,
        llm_call=llm_call,
        diagnostics=diagnostics,
    )
    if llm_call is not None and llm_call in calls:
        calls.remove(llm_call)
    return observation


def pairwise_discriminate(harness, problem, a_id: str, b_id: str, adapter, config,
                          diagnostics: list | None = None, *,
                          authority: TrialAuthority | str = TrialAuthority.OBSERVE_ONLY):
    """§10.2: (A, B, pi, criteria) -> winner + decisive_point, mandatory
    order-swap. Status mode registers an argumentative warrant against the
    loser, indexed to pi — never a global ranking. Advisory mode records the
    comparison without a warrant; 'neither' remains unresolved in both."""
    authority = _coerce_trial_authority(authority)
    a_text = content_text(harness.state.artifacts[a_id], harness.blobs)
    b_text = content_text(harness.state.artifacts[b_id], harness.blobs)
    criteria = "\n".join(f"- {c}" for c in problem.criteria)

    def pack(first, second, first_label, second_label):
        return "\n".join([
            f"PROBLEM {problem.id}: {problem.description}", "CRITERIA:", criteria, "",
            f"{first_label}:\n{first}", "", f"{second_label}:\n{second}", "",
            "QUESTION: which candidate better addresses the problem, for this "
            "problem only? winner=neither if you cannot discriminate. "
            "decisive_point MUST quote a span of a candidate.",
        ])

    calls: list = []
    try:
        return _pairwise_steps(harness, problem, a_id, b_id, a_text, b_text,
                               pack, adapter, diagnostics, calls, authority)
    finally:
        harness.record_llm_calls(calls, "trial-llm")


def _pairwise_steps(harness, problem, a_id, b_id, a_text, b_text, pack,
                    adapter, diagnostics, calls: list, authority: TrialAuthority):
    aliases = aliases_for_values([a_text, b_text], prefix="K")
    ruling1, llm_call = adapter.call(
        "judge",
        pack(a_text, b_text, "A", "B"),
        PairwiseRuling,
        aliases=aliases,
    )
    calls.append(llm_call)
    if ruling1.winner == "neither":
        if authority == TrialAuthority.OBSERVE_ONLY:
            return _advisory_pairwise_result(
                harness,
                problem=problem,
                a_id=a_id,
                b_id=b_id,
                ruling1=ruling1,
                ruling2=None,
                winner=None,
                loser=None,
                order_swap="not-run",
                outcome="neither",
                llm_call=llm_call,
                diagnostics=diagnostics,
                calls=calls,
            )
        return None
    ruling2, call = adapter.call(
        "judge",
        pack(b_text, a_text, "A", "B"),
        PairwiseRuling,
        aliases=aliases,
    )
    calls.append(call)
    # Under the swap, candidate a is labelled B: the same real winner is
    # required (order-swap consistency, §3).
    consistent = (
        (ruling1.winner == "A" and ruling2.winner == "B")
        or (ruling1.winner == "B" and ruling2.winner == "A")
    )
    if not consistent:
        if authority == TrialAuthority.OBSERVE_ONLY:
            return _advisory_pairwise_result(
                harness,
                problem=problem,
                a_id=a_id,
                b_id=b_id,
                ruling1=ruling1,
                ruling2=ruling2,
                winner=None,
                loser=None,
                order_swap="failed",
                outcome="blocked:order-swap",
                llm_call=llm_call,
                diagnostics=diagnostics,
                calls=calls,
            )
        return _block(harness, "order-swap", f"{a_id[:12]}v{b_id[:12]}", diagnostics)
    # Referential integrity (§3): a named winner MUST quote a span of a
    # candidate. An empty decisive_point is unscreened LLM adjudication —
    # block it rather than skipping the check (the empty string is a substring
    # of everything, so it would otherwise pass vacuously). PairwiseRuling
    # allows "" only for 'neither', handled above.
    if not ruling1.decisive_point or ruling1.decisive_point not in f"{a_text}\n{b_text}":
        if authority == TrialAuthority.OBSERVE_ONLY:
            return _advisory_pairwise_result(
                harness,
                problem=problem,
                a_id=a_id,
                b_id=b_id,
                ruling1=ruling1,
                ruling2=ruling2,
                winner=None,
                loser=None,
                order_swap="pass",
                outcome="blocked:referential-integrity",
                llm_call=llm_call,
                diagnostics=diagnostics,
                calls=calls,
            )
        return _block(harness, "referential-integrity", f"{a_id[:12]}v{b_id[:12]}", diagnostics)

    loser = b_id if ruling1.winner == "A" else a_id
    winner = a_id if ruling1.winner == "A" else b_id
    if execution_backed(harness, loser):
        # Execution supremacy (§3): the loser passes its exec-oracle, so a
        # verdict from reality stands. A pairwise PREFERENCE cannot refute it —
        # the rivalry stands unresolved, exactly as for a 'neither' ruling. The
        # judge calls remain logged (the finally records them).
        if authority == TrialAuthority.OBSERVE_ONLY:
            return _advisory_pairwise_result(
                harness,
                problem=problem,
                a_id=a_id,
                b_id=b_id,
                ruling1=ruling1,
                ruling2=ruling2,
                winner=winner,
                loser=loser,
                order_swap="pass",
                outcome="execution-backed-loser",
                llm_call=llm_call,
                diagnostics=diagnostics,
                calls=calls,
            )
        return None
    if authority == TrialAuthority.OBSERVE_ONLY:
        return _advisory_pairwise_result(
            harness,
            problem=problem,
            a_id=a_id,
            b_id=b_id,
            ruling1=ruling1,
            ruling2=ruling2,
            winner=winner,
            loser=loser,
            order_swap="pass",
            outcome="consistent-preference",
            llm_call=llm_call,
            diagnostics=diagnostics,
            calls=calls,
        )
    before = set(harness.state.artifacts)
    trace_ref = harness.blobs.put(canonical_json({
        "pairwise": {"problem": problem.id, "winner": winner, "loser": loser,
                     "decisive_point": ruling1.decisive_point},
        "order_swap": "pass",
    }))
    nu = harness.create_artifact(
        f"nu: the pairwise ruling {winner[:12]} > {loser[:12]} for {problem.id} is sound",
        provenance=Provenance(role="critic"),
    )
    warrant = Warrant(
        id=f"w:pairwise:{problem.id}:{loser}",
        target=loser,
        type=WarrantType.ARGUMENTATIVE,
        trace_ref=trace_ref,
        validity_node=nu.id,
    )
    critic = harness.create_artifact(
        json.dumps({"pairwise": {"problem": problem.id, "winner": winner,
                                 "loser": loser,
                                 "decisive_point": ruling1.decisive_point}},
                   sort_keys=True),
        codec="json",
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=llm_call,
        problem_id=problem.id,
    )
    if critic.id not in before:
        calls.remove(llm_call)  # a real event carried the decisive ruling
    return critic
