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

from deepreason.llm.contracts import CandidateRef, ConjectureCandidate, ConjecturerOutput
from deepreason.llm.packs import aliases_for_pack, render_conj_pack
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
) -> list[Artifact]:
    problem = harness.state.problems.get(problem_id)
    if problem is None:
        raise KeyError(f"Conj is gated on a registered problem; unknown: {problem_id}")
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
    )
    aliases = aliases_for_pack(pack, harness.state.artifacts, prefix="A")
    reasoning = any(
        harness.commitments[commitment_id].eval == "program:reasoning-envelope-wf"
        for commitment_id in problem.criteria
        if commitment_id in harness.commitments
    )
    output_model = ReasoningConjecturerOutput if reasoning else ConjecturerOutput
    output, llm_call = adapter.call("conjecturer", pack, output_model, aliases=aliases)
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

    batch: list[tuple[Artifact, list[Warrant]]] = []
    candidate_domains: dict[str, anti_relapse.RelapseDomain] = {}
    seen: set[str] = set()
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
        overlay = {**harness.commitments, **{item.id: item for item in draft}}
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
        # Gate first (spec §3): a refuted-equivalent is a block, not a dedupe.
        effective_workload = "text" if reasoning else workload_profile
        effective_contract = (
            "reasoning.conjecturer.compact.v2" if reasoning else contract_id
        )
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
            diagnostics.append(
                {
                    "candidate": artifact.id[:12],
                    "gate": reason,
                    "search_signal": search_signal,
                }
            )
        if not admitted:
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
            continue  # attention-level dedupe of a registered twin — never a block (§0)
        # Commit after admission (RC5): only now do draft commitments reach
        # the registry (idempotent for ids an earlier candidate registered).
        for commitment in draft:
            harness.register_commitment(commitment)
        seen.add(artifact.id)
        batch.append((artifact, []))
        if domain is not None:
            candidate_domains[artifact.id] = domain
    for artifact, _warrants in batch:
        if artifact.id in candidate_domains:
            anti_relapse.record_domain(harness, artifact.id, candidate_domains[artifact.id])
    registered = harness.register_batch(
        batch, problem_id=problem_id, rule=Rule.CONJ, llm=llm_call
    )
    if not registered:
        # All candidates gate-blocked or deduped => no Conj event committed;
        # the gamma call still spent tokens and must reach the log once (§0).
        harness.record_llm_calls([llm_call], "conj-noregister")
    return registered
