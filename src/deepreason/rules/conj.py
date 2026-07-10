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

from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.packs import render_conj_pack
from deepreason.ontology import Artifact, Interface, Provenance, Ref, Rule, Warrant
from deepreason.rules.guards import anti_relapse


def _resolve_ref(target: str, artifacts: dict) -> str | None:
    """Resolve a candidate ref to a registered artifact id. Models reliably
    emit truncated ids (packs show 12-char heads), and silently dropping the
    ref would mechanically refute a lineage-bound candidate — so a UNIQUE
    prefix resolves to the full id (deterministic; the resolved ref enters
    the content-addressed identity exactly as a correctly-typed one would).
    Ambiguous or unknown targets drop, as before."""
    if not target:
        return None
    if target in artifacts:
        return target
    matches = [aid for aid in artifacts if aid.startswith(target)]
    return matches[0] if len(matches) == 1 else None


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
    )
    output, llm_call = adapter.call("conjecturer", pack, ConjecturerOutput)
    # Level-2 transmission diagnostic (attention/reporting only, §0): did
    # candidate k actually realize spec k? Logged as a replayable Measure.
    if specs and embedder is not None:
        from deepreason.llm.specs import transmission_score

        score = transmission_score(specs, [c.content for c in output.candidates], embedder)
        if score is not None:
            harness.record_measure(inputs=[f"spec-transmission:{score:.4f}", problem_id])

    candidates = list(output.candidates)
    if tail_weighted:  # stagnation response (§11.4): fund the atypical tail
        candidates.sort(key=lambda c: c.typicality)

    batch: list[tuple[Artifact, list[Warrant]]] = []
    seen: set[str] = set()
    for candidate in candidates[: config.VS_K]:
        commitments = [c for c in problem.criteria if c in harness.commitments]
        # Skeleton discipline (§10.1): content that parses as a skeleton has
        # its forbidden cases compiled into commitments — at registration,
        # BEFORE id computation, deterministically.
        from deepreason.informal.skeleton import compile_forbidden_commitments, parse_skeleton

        skeleton = parse_skeleton(candidate.content)
        if skeleton is not None:
            commitments += [
                c for c in compile_forbidden_commitments(harness, skeleton)
                if c not in commitments
            ]
        interface = Interface(
            commitments=commitments,
            refs=[
                Ref(target=resolved, role=r.role)
                for r in candidate.refs
                if (resolved := _resolve_ref(r.target, harness.state.artifacts))
            ],
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
        # Gate first (spec §3): a refuted-equivalent is a block, not a dedupe.
        admitted, reason = anti_relapse.check(
            artifact, [], harness, embedder=embedder, near_dup_eps=config.NEAR_DUP_EPS
        )
        if diagnostics is not None:
            diagnostics.append({"candidate": artifact.id[:12], "gate": reason})
        if not admitted:
            # Persist the block (stress campaign T7 finding): gate decisions
            # were in-memory only, so a finished run could not be audited for
            # block counts — violating log-as-source-of-truth. A Measure is
            # the right vehicle: attention/diagnostic, never a status.
            harness.record_measure(inputs=[f"gate:{reason}", artifact.id, problem_id])
            continue
        if artifact.id in seen or artifact.id in harness.state.artifacts:
            continue  # attention-level dedupe of a registered twin — never a block (§0)
        seen.add(artifact.id)
        batch.append((artifact, []))
    registered = harness.register_batch(batch, problem_id=problem_id, rule=Rule.CONJ, llm=llm_call)
    if not registered:
        # All candidates gate-blocked or deduped => no Conj event committed;
        # the gamma call still spent tokens and must reach the log once (§0).
        harness.record_llm_calls([llm_call], "conj-noregister")
    return registered
