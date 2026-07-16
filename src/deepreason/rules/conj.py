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

from pydantic import ValidationError

from deepreason.canonical import canonical_json
from deepreason.conjecture_events import (
    ConjectureTurnAction,
    ConjectureTurnEventPayloadV1,
)
from deepreason.conjecture_turn import (
    ConjecturerTurnV4,
    ReasoningConjecturerTurnV4,
)
from deepreason.llm.contracts import CandidateRef, ConjectureCandidate, ConjecturerOutput
from deepreason.llm.firewall import EndpointLease
from deepreason.llm.packs import aliases_for_pack, render_conj_pack
from deepreason.llm.wire import ConjecturerTurnWireContractV4
from deepreason.ontology import Artifact, Provenance, Rule, Warrant
from deepreason.rules.guards import anti_relapse
from deepreason.workloads.models import MandatoryInterface, compile_interface_draft
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
) -> list[Artifact]:
    problem = harness.state.problems.get(problem_id)
    if problem is None:
        raise KeyError(f"Conj is gated on a registered problem; unknown: {problem_id}")
    if (endpoint_lease is None) != (execution_school_id is None):
        raise ValueError(
            "school-routed Conj requires both endpoint_lease and execution_school_id"
        )
    if execution_school_id is not None:
        if school is None or school.get("id") != execution_school_id:
            raise ValueError(
                "execution school must match the semantic school conditioning record"
            )
        if endpoint_lease.role != "conjecturer":
            raise ValueError("Conj endpoint lease must belong to the conjecturer role")
    if workflow_work_order_id is not None and workflow_control_trace is not None:
        raise ValueError("Conj accepts only one workflow binding seam")

    workflow_guard_findings = []

    def observe_candidate(candidate_ref: str, outcome: str, reason: str) -> None:
        """Report code-derived disposition without granting callback authority."""

        if candidate_observer is None:
            return
        try:
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
        except Exception:  # noqa: BLE001 - observation cannot alter Conj
            return
    if conjecture_context_plan is not None:
        from deepreason.scratch.conjecture import PlannedConjectureContextV1

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
    active_v4 = run_manifest is not None
    context_policy = None
    scratch_policy = None
    if active_v4:
        from deepreason.run_manifest import RunManifest

        run_manifest = RunManifest.model_validate(run_manifest)
        control = run_manifest.control_plane_policy
        if (
            run_manifest.schema_version != 4
            or control is None
            or control.mode != "active_conjecture"
            or control.contract_versions.conjecturer_turn_contract
            != "conjecturer.turn.v4"
        ):
            raise ValueError(
                "v4 conjecture turns require an active_conjecture manifest"
            )
        context_policy = control.conjecture_context
        scratch_policy = run_manifest.scratch_policy
        if scratch_policy is None:
            raise ValueError("active conjecture manifest has no scratch policy")
        if (
            conjecture_context_plan is not None
            and conjecture_context_plan.manifest_digest != run_manifest.sha256
        ):
            raise ValueError("conjecture context belongs to another manifest")
        if generation_context is not None:
            raise ValueError(
                "active v4 Conj requires typed context; raw generation_context "
                "is not permitted"
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
        allow_no_candidate_outcome=active_v4,
    )
    aliases = aliases_for_pack(pack, harness.state.artifacts, prefix="A")
    reasoning = any(
        harness.commitments[commitment_id].eval == "program:reasoning-envelope-wf"
        for commitment_id in problem.criteria
        if commitment_id in harness.commitments
    )
    output_model = (
        ReasoningConjecturerTurnV4
        if active_v4 and reasoning
        else ConjecturerTurnV4
        if active_v4
        else ReasoningConjecturerOutput
        if reasoning
        else ConjecturerOutput
    )
    context_receipt = None
    if conjecture_context_plan is not None:
        from deepreason.scratch.conjecture import commit_conjecture_context
        from deepreason.scratch.service import ScratchService

        context_receipt = commit_conjecture_context(
            ScratchService(harness),
            conjecture_context_plan,
            final_conjecture_pack=pack,
            attention_policy=conjecture_context_plan.attention_policy,
        )
    turn_contract = (
        ConjecturerTurnWireContractV4(
            reasoning=reasoning,
            aliases=aliases,
            scratch_aliases=(
                {
                    **dict(
                        conjecture_context_plan.rendered_context.receipt.block_handles
                    ),
                    **dict(
                        conjecture_context_plan.rendered_context.receipt.cluster_handles
                    ),
                    **dict(
                        conjecture_context_plan.rendered_context.receipt.link_handles
                    ),
                    **dict(
                        conjecture_context_plan.rendered_context.receipt.guide_handles
                    ),
                }
                if conjecture_context_plan is not None
                else {}
            ),
            permitted_retrieval_channels=(
                context_policy.permitted_retrieval_channels
                if context_policy is not None
                else ()
            ),
        )
        if active_v4
        else None
    )
    output, llm_call = adapter.call(
        "conjecturer",
        pack,
        output_model,
        endpoint_index=endpoint_lease.seat if endpoint_lease is not None else 0,
        aliases=aliases,
        wire_contract=turn_contract,
        endpoint_lease=endpoint_lease,
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
    )
    bound_work_order_id = llm_call.work_order_id
    source_call_seq = None
    if active_v4 or bound_work_order_id is not None:
        extra = (
            (f"school:{execution_school_id}",)
            if execution_school_id is not None
            else ()
        )
        harness.record_llm_calls(
            [llm_call],
            (
                "conjecture-turn-call"
                if active_v4
                else "workflow-conjecture-call"
            ),
            problem_id,
            *(
                (f"manifest:{run_manifest.sha256}",)
                if active_v4
                else ()
            ),
            *extra,
        )
        source_call_seq = harness._next_seq - 1
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
                harness.record_measure(
                    inputs=["proposal-envelope-invalid", type(error).__name__]
                )
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
        candidate_rows = [
            (candidate, (), "productive")
            for candidate in proposals[: config.VS_K]
        ]

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
                dict.fromkeys(
                    (*base.commitments, *(item.id for item in draft_pool))
                )
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
            artifact.id
            if occurrence == 1
            else f"{artifact.id}#occurrence-{occurrence}"
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
            "conjecturer.turn.v4"
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
            (f"conjecture-call:{source_call_seq}",)
            if source_call_seq is not None
            else ()
        ),
    )
    if not registered:
        # All candidates gate-blocked or deduped => no Conj event committed;
        # the gamma call still spent tokens and must reach the log once (§0).
        extra = (
            (f"school:{execution_school_id}",)
            if execution_school_id is not None
            else ()
        )
        if source_call_seq is None:
            harness.record_llm_calls([llm_call], "conj-noregister", *extra)
    if not active_v4:
        return registered

    assert source_call_seq is not None
    prior_selection = (
        context_receipt.selection_receipt_ref
        if context_receipt is not None
        else None
    )
    abstention = output.abstention
    if abstention is not None:
        abstention_ref = harness.blobs.put(
            canonical_json(
                abstention.model_dump(mode="json", exclude_none=True)
            )
        )
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

    request = output.context_request
    if request is None:
        return registered
    request_ref = harness.blobs.put(
        canonical_json(request.model_dump(mode="json", exclude_none=True))
    )
    common = {
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
    if desired - permitted:
        harness.record_conjecture_turn_event(
            ConjectureTurnEventPayloadV1.create(
                action=ConjectureTurnAction.CONTEXT_DENIED,
                expansion_index=_context_expansion_index,
                reason_code="channel_not_permitted",
                **common,
            ),
            request=request,
        )
        return registered
    if context_policy.mode != "harness_plus_model_request":
        harness.record_conjecture_turn_event(
            ConjectureTurnEventPayloadV1.create(
                action=ConjectureTurnAction.CONTEXT_DENIED,
                expansion_index=_context_expansion_index,
                reason_code="capability_not_granted",
                **common,
            ),
            request=request,
        )
        return registered
    if _context_expansion_index >= context_policy.max_context_expansion_requests:
        harness.record_conjecture_turn_event(
            ConjectureTurnEventPayloadV1.create(
                action=ConjectureTurnAction.CONTEXT_EXHAUSTED,
                expansion_index=_context_expansion_index,
                reason_code="request_limit_reached",
                **common,
            ),
            request=request,
        )
        return registered

    from deepreason.scratch.conjecture import plan_conjecture_context_expansion
    from deepreason.scratch.service import ScratchService

    expansion_number = _context_expansion_index + 1
    proposed = ConjectureTurnEventPayloadV1.create(
        action=ConjectureTurnAction.CONTEXT_GRANTED,
        expansion_index=expansion_number,
        reason_code="granted",
        **common,
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
        reason = (
            "no_context_capacity"
            if total_cap <= prior_count
            else "no_additional_context"
        )
        harness.record_conjecture_turn_event(
            ConjectureTurnEventPayloadV1.create(
                action=ConjectureTurnAction.CONTEXT_DENIED,
                expansion_index=_context_expansion_index,
                reason_code=reason,
                **common,
            ),
            request=request,
        )
        return registered

    harness.record_conjecture_turn_event(proposed, request=request)
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
        expansion_decision_ref=proposed.decision_id,
        expansion_index=expansion_number,
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
    )
    if expanded_plan is None:
        raise RuntimeError(
            "granted conjecture context expansion became unavailable after its decision"
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
        _context_expansion_index=expansion_number,
        candidate_observer=candidate_observer,
        workflow_work_order_id=workflow_work_order_id,
        workflow_control_trace=workflow_control_trace,
    )
    return [*registered, *follow_up]
