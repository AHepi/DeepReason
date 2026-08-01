"""Experiment design (§3/§6 extension): the system designs its own experiments.

The fuzz pass (oracle.fuzz_property) turned the harness into an experimenter,
but its generators were spec-authored — a human still designed every probe of
the input space. This rule closes that loop: an LLM (the EXPERIMENTER role,
served by the conjecturer's endpoint) proposes `def gen(k)` sources for a
property oracle, and the harness adjudicates them BY THEIR FRUITS with an
ordinary program commitment (generator_wf: compile under the guard, yield
gate-valid inputs, reach at least one novel input). Accepted generators are
then enumerated by crit_fuzz alongside the spec's own.

Soundness is generator-independent by construction (§0): whoever wrote gen,
the FROZEN admission gate screens every input and the FROZEN checker decides
every violation — a generator can never manufacture a false refutation. It
only chooses where the harness looks. That is why no judge, no trial, and no
execution-supremacy interaction is needed here: a bad generator is refuted
mechanically for yield/novelty, a good one earns kills that are checked by
the same oracle as everything else. Generators are ordinary artifacts: D8
(nothing deleted) and N1 (no status final) apply, and a refuted generator can
be reinstated by criticizing its critic like anything else.
"""

from deepreason.llm.contracts import (
    ExperimenterOutput,
    JudgeRuling,
    PropertyDesignerOutput,
)
from deepreason.llm.packs import (
    aliases_for_values,
    render_experiment_pack,
    render_property_pack,
)
from deepreason.ontology import (
    Interface,
    Provenance,
    Ref,
    Rule,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.ontology.artifact import RefRole
from deepreason.rules.crit import crit_program

GEN_CODEC = "code:python-gen"
PROP_CODEC = "code:python-prop"


def _oracle_ready(harness, artifact) -> bool:
    """Require a verdict before activating executable policy.

    A fail already represented by a warrant remains graph-governed (attacking
    its validity node can reinstate the policy, N1). With no on-record fail,
    activation requires a deterministic PASS; sandbox abort and deterministic
    overrun both fail closed without manufacturing a refutation.
    """
    from deepreason import programs
    from deepreason.rules.warrants import verdict_on_record

    for cid in artifact.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None or not programs.evaluable(kappa):
            return False
        if verdict_on_record(harness, cid, artifact.id):
            continue  # status/grounded semantics decide an attacked fail warrant
        key = (cid, artifact.id)
        verdict = harness._verdict_cache.get(key)
        if verdict is None:
            verdict, trace = programs.evaluate(kappa, artifact, harness.blobs)
            if trace.get("sandbox_abort"):
                harness._oracle_pending.add(key)
                return False
            harness._oracle_pending.discard(key)
            harness._verdict_cache[key] = verdict
        if verdict == programs.FAIL:
            crit_program(harness, artifact.id)  # put the deterministic fail on graph
            return False
        if verdict != programs.PASS:
            return False
    return True


def accepted_generators(harness, base_commitment_id: str) -> list[tuple[str, str]]:
    """ACCEPTED experimenter generators targeting the given property oracle,
    as (artifact_id, source) in state insertion order (deterministic)."""
    from deepreason.programs import content_text

    out: list[tuple[str, str]] = []
    for aid, artifact in harness.state.artifacts.items():
        if artifact.codec != GEN_CODEC:
            continue
        if harness.state.status.get(aid) != Status.ACCEPTED:
            continue
        if not _oracle_ready(harness, artifact):
            continue
        if harness.state.status.get(aid) != Status.ACCEPTED:
            continue  # a retry may have produced a deterministic fail warrant
        if not any(
            r.role == RefRole.MENTION and r.target == base_commitment_id
            for r in artifact.interface.refs
        ):
            continue
        out.append((aid, content_text(artifact, harness.blobs)))
    return out


def _survivor_heads(harness, base_commitment_id: str, cap: int = 3) -> list[str]:
    """The code of ACCEPTED candidates carrying the base oracle — what the
    experiment is for. The two live impotent designs (chains that never
    create a tie; alphabetical node lists that make the buggy choice coincide
    with the correct one) were designed BLIND; a directed experiment reads
    the implementation it is probing. Presentation only (§9): the gate and
    checker still decide everything."""
    from deepreason.programs import content_text

    heads: list[str] = []
    for aid, artifact in harness.state.artifacts.items():
        if len(heads) >= cap:
            break
        if harness.state.status.get(aid) != Status.ACCEPTED:
            continue
        if base_commitment_id not in artifact.interface.commitments:
            continue
        heads.append(f"CANDIDATE {aid[:12]}:\n{content_text(artifact, harness.blobs)[:500]}")
    return heads


def propose_generators(harness, base, adapter, config) -> list:
    """One experimenter call for a property oracle: register each returned
    generator as an artifact carrying the derived generator_wf commitment and
    a MENTION ref to the base oracle, then adjudicate immediately via
    crit_program — a generator that doesn't compile, doesn't yield, or
    designs no new experiment is refuted on arrival, mechanically. Returns
    the artifacts that survived admission."""
    from deepreason.oracle import generator_wf_commitment

    wf = generator_wf_commitment(base)
    if wf is None:
        return []
    harness.register_commitment(wf)
    existing = [src for _, src in accepted_generators(harness, base.id)]
    pack = render_experiment_pack(
        base,
        existing,
        token_budget=config.PACK_TOKEN_BUDGET,
        targets=_survivor_heads(harness, base.id),
    )
    output, llm_call = adapter.call(
        "conjecturer", pack, ExperimenterOutput, template_role="experimenter"
    )
    survivors: list = []
    llm_pending = llm_call
    for source in output.generators:
        if not source.strip():
            continue
        before = set(harness.state.artifacts)
        artifact = harness.create_artifact(
            source,
            codec=GEN_CODEC,
            interface=Interface(
                commitments=[wf.id],
                refs=[Ref(target=base.id, role=RefRole.MENTION)],
            ),
            provenance=Provenance(role="experimenter", event_seq=harness._next_seq),
            rule=Rule.CONJ,
            llm=llm_pending,
        )
        if artifact.id not in before:
            llm_pending = None  # a real event carried the shared call
        crit_program(harness, artifact.id)  # generator_wf adjudicates now
        if (
            harness.state.status.get(artifact.id) == Status.ACCEPTED
            and _oracle_ready(harness, artifact)
            and harness.state.status.get(artifact.id) == Status.ACCEPTED
        ):
            survivors.append(artifact)
    if llm_pending is not None:
        # Nothing committed the call (empty/duplicate outputs): log it once.
        harness.record_measure(inputs=["experiment-design", base.id], llm=llm_pending)
    return survivors


# ---------------------------------------------------------------------------
# Proposed PROPERTIES: conjectured ground truth, held accountable.
# ---------------------------------------------------------------------------


def active_properties(harness, base_commitment_id: str) -> list[tuple[str, str, str]]:
    """ACCEPTED proposed properties targeting the given oracle, as
    (artifact_id, claim, checker_source) in insertion order. ACCEPTED is the
    entire activation gate: a property is refuted on arrival by checker_wf
    (mechanical) or the relevance trial, and can be refuted later by ordinary
    criticism — at which point it drops out of this list AND (edges.py
    source-artifact closure) every verdict it ever minted collapses. If its
    critic is itself refuted, it reinstates and reactivates: N1 throughout."""
    from deepreason.programs import content_text

    out: list[tuple[str, str, str]] = []
    for aid, artifact in harness.state.artifacts.items():
        if artifact.codec != PROP_CODEC:
            continue
        if harness.state.status.get(aid) != Status.ACCEPTED:
            continue
        if not _oracle_ready(harness, artifact):
            continue
        if harness.state.status.get(aid) != Status.ACCEPTED:
            continue
        if not any(
            r.role == RefRole.MENTION and r.target == base_commitment_id
            for r in artifact.interface.refs
        ):
            continue
        text = content_text(artifact, harness.blobs)
        claim = ""
        if text.startswith('"""'):
            end = text.find('"""', 3)
            if end > 0:
                claim = text[3:end].strip()
        out.append((aid, claim, text))
    return out


def promoted_properties(harness, base_commitment_id: str, config) -> set[str]:
    """The ratchet (probation -> promotion): artifact ids of ACTIVE properties
    that have survived at least PROP_PROBATION_EVENTS events since their
    registration AND have a WITNESS — at least one registered candidate whose
    output actually satisfies them. A promoted property holds the line even
    when the whole current population fails it (the wipeout guard is waived
    in crit_fuzz) — the standard does not sink with a bad generation of
    candidates.

    The corroboration clause is the intervals/boot postmortem: a buggy
    conjectured checker survived 14 quarantines UNTOUCHED — no critic ever
    read it, no candidate ever satisfied it — aged past probation, and then
    executed seven correct candidates. Age alone is seniority masquerading
    as corroboration (accepted-by-neglect, the exact failure standing
    re-criticism exists to prevent). Promotion now requires age AND either:

      - SURVIVED ATTACK: some critic attacked the property and it is still
        accepted (grounded semantics: an accepted-yet-attacked node has
        defeated its attacker — a real reinstatement record, reachable now
        that active properties sit in the standing re-criticism rotation); or
      - WITNESS: at least one registered carrier's output satisfies it
        (satisfiability evidence — a checker whose entire record is failing
        people has never been tested as a standard, only used as a weapon).

    Promotion remains TRUST, never finality (N1): ordinary criticism can
    refute a promoted property and the source-artifact closure (edges.py)
    still collapses every verdict it ever minted. Deterministic: age is
    semantic-event distance, attack survival is graph structure, the witness
    check runs frozen content in the sandbox; 0 disables promotion."""
    if config.PROP_PROBATION_EVENTS <= 0:
        return set()
    now = harness.semantic_event_clock()
    base = harness.commitments.get(base_commitment_id)
    attacked = {target for _, target in harness.state.att}
    out: set[str] = set()
    for aid, _claim, source in active_properties(harness, base_commitment_id):
        registered = harness.semantic_event_clock(
            harness.state.artifacts[aid].provenance.event_seq
        )
        age = now - registered
        if age < config.PROP_PROBATION_EVENTS:
            continue
        survived_attack = aid in attacked  # active => any attacker was defeated
        if not survived_attack and (
            base is None or not population_supports(harness, base, source, "")
        ):
            continue  # neither scrutiny nor witness: neglect earns no authority
        out.add(aid)
    return out


def population_supports(harness, base, property_source: str, target_id: str) -> bool:
    """Wipeout guard: a property that EVERY sibling candidate also violates is
    indicting the population, not the target — that is what a bogus
    over-strict checker looks like, so it grounds nothing (defense in depth
    behind the trial; the property stays registered and criticizable).

    Support = at least one OTHER registered candidate carrying the base
    oracle whose output SATISFIES the property on the frozen inputs. Any
    status counts (accepted checked first): a candidate refuted for other
    reasons still proves the property is satisfiable by real code — the
    question here is satisfiability, not the supporter's correctness. A
    reject-everything checker still finds no supporter and stays quarantined.
    Deterministic function of the current graph + frozen content."""
    from deepreason.oracle import _load_spec, run_property
    from deepreason.programs import content_text

    spec = _load_spec(base.budget)
    entry, inputs = spec.get("entry"), spec.get("inputs", [])
    if not entry or not inputs:
        return False
    # Membership = carries the base oracle (codec is presentation and varies
    # by admission path; the commitment is the load-bearing link).
    carriers = [
        (aid, artifact) for aid, artifact in harness.state.artifacts.items()
        if aid != target_id and base.id in artifact.interface.commitments
    ]
    accepted_first = sorted(
        carriers,
        key=lambda pair: harness.state.status.get(pair[0]) != Status.ACCEPTED,
    )
    for aid, artifact in accepted_first[:8]:
        verdict, _ = run_property(
            content_text(artifact, harness.blobs), entry, inputs, property_source
        )
        if verdict == "pass":
            return True
    return False


def relevance_trial(harness, prop_artifact, claim: str, problem, adapter, config) -> bool:
    """The §3 sanctioned path for an informal claim: does this property follow
    from the problem statement? Judged by BOTH ensemble seats (different
    families, §9) on the narrow question only. Guards: referential integrity
    (each decisive_point must quote the pack) and unanimity — the property
    activates only if both seats rule pass; otherwise a fail warrant registers
    against the PROPERTY (argumentative, attackable nu: criticize-the-critic
    reinstates it, N1). Judges never touch a candidate's status here — they
    rule on the property artifact alone."""
    from deepreason.canonical import sha256_hex

    judge_seats = adapter.require_cross_family_judges()
    pack = "\n".join([
        "NARROW QUESTION: does the proposed property follow from the problem "
        "statement — is it a requirement the statement actually makes (rule "
        "pass), or does it add or contradict requirements (rule fail)?",
        "",
        f"PROBLEM STATEMENT:\n{problem.description}",
        "",
        f"PROPOSED PROPERTY CLAIM: {claim}",
        "",
        f"PROPOSED CHECKER SOURCE:\n{prop_artifact and _prop_text(harness, prop_artifact)}",
        "",
        "decisive_point MUST quote a span of the problem statement or the claim.",
    ])
    calls: list = []
    rulings: list[JudgeRuling] = []
    try:
        for seat in range(len(judge_seats)):
            ruling, llm_call = adapter.call(
                "judge",
                pack,
                JudgeRuling,
                endpoint_index=seat,
                aliases=aliases_for_values(
                    [problem.description, claim], prefix="K"
                ),
            )
            calls.append(llm_call)
            if ruling.decisive_point and ruling.decisive_point not in pack:
                # Unlocatable grounds: treat as an invalid ruling (fail-closed
                # for ACTIVATION, but registers no warrant — blocked, §3).
                rulings.append(None)
                continue
            rulings.append(ruling)
    finally:
        harness.record_llm_calls(calls, "property-relevance-trial")

    if all(r is not None and r.verdict == "pass" for r in rulings):
        return True
    # Anything short of unanimous located passes: the property does not
    # activate. If at least one seat POSITIVELY ruled fail with located
    # grounds, register that case against the property so the record shows
    # why (and so criticize-the-critic can reinstate it).
    failed = [r for r in rulings if r is not None and r.verdict == "fail"]
    if failed:
        case = failed[0].decisive_point
        case_hash = sha256_hex(case.encode())[:16]
        nu = harness.create_artifact(
            f"nu: relevance ruling {case_hash} against {prop_artifact.id} is sound",
            provenance=Provenance(role="critic"),
        )
        harness.create_artifact(
            f"critic: property does not follow from the problem statement — {case}",
            provenance=Provenance(role="critic"),
            warrants=[Warrant(
                id=f"w:prop-rel:{case_hash}:{prop_artifact.id}",
                target=prop_artifact.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu.id,
            )],
            rule=Rule.CRIT,
        )
    return False


def _prop_text(harness, artifact) -> str:
    from deepreason.programs import content_text

    return content_text(artifact, harness.blobs)


def checker_crashed(detail: dict) -> bool:
    """True when a run_property FAIL was the CHECKER's doing (it raised or
    overran), not the candidate's. For the seed checker that distinction
    doesn't matter — an accountable operator froze it, so an uncheckable
    output is the candidate's problem. For a CONJECTURED checker it is the
    whole ballgame: a crash is at least as likely the checker's bug as the
    candidate's (observed live: `for a, b in inp` on the args wrapper), so a
    crash must never ground a warrant against the candidate."""
    err = str(detail.get("error", ""))
    return err.startswith("checker raised") or err == "step limit exceeded in checker"


def crash_probe(harness, base, checker_source: str, limit: int = 8) -> dict | None:
    """Run a proposed checker against up to ``limit`` existing base-oracle
    carriers on the frozen inputs; return the first CRASH detail, else None.
    A well-formed checker REJECTS outputs it dislikes — it does not throw on
    the problem's own domain. Mechanical, no LLM; any-status carriers count
    (the question is whether the checker runs, not who it judges)."""
    from deepreason.oracle import _load_spec, run_property
    from deepreason.programs import content_text

    spec = _load_spec(base.budget)
    entry, inputs = spec.get("entry"), spec.get("inputs", [])
    if not entry or not inputs:
        return None
    carriers = [
        artifact for aid, artifact in harness.state.artifacts.items()
        if base.id in artifact.interface.commitments
    ]
    for artifact in carriers[:limit]:
        verdict, detail = run_property(
            content_text(artifact, harness.blobs), entry, inputs, checker_source
        )
        if verdict == "fail" and checker_crashed(detail):
            return detail
    return None


def propose_properties(harness, base, problem, adapter, config) -> list:
    """One property-designer call for a property oracle: each proposal is
    registered as an artifact (claim as module docstring + checker source)
    carrying the derived checker_wf commitment and a MENTION ref to the base
    oracle, then adjudicated in two stages ON ARRIVAL: crit_program runs
    checker_wf (mechanical: compiles/bounded/non-vacuous), and survivors face
    the relevance trial (cross-family unanimity). Returns the artifacts that
    activated. The designer sees the PROBLEM and the current checker — never
    candidate code (a property derived from code would enshrine its bugs)."""
    from deepreason.oracle import checker_wf_commitment

    wf = checker_wf_commitment(base)
    if wf is None:
        return []
    harness.register_commitment(wf)
    existing = [claim for _, claim, _ in active_properties(harness, base.id)]
    pack = render_property_pack(
        base, problem.description, existing, token_budget=config.PACK_TOKEN_BUDGET
    )
    output, llm_call = adapter.call(
        "property_designer", pack, PropertyDesignerOutput
    )
    activated: list = []
    llm_pending = llm_call
    for proposal in output.properties:
        source = proposal.checker.strip()
        if not source:
            continue
        content = f'"""{proposal.claim.strip()}"""\n{source}'
        before = set(harness.state.artifacts)
        artifact = harness.create_artifact(
            content,
            codec=PROP_CODEC,
            interface=Interface(
                commitments=[wf.id],
                refs=[Ref(target=base.id, role=RefRole.MENTION)],
            ),
            # event_seq stamps the probation clock (promotion age is derived
            # from it deterministically — no new event kind needed).
            provenance=Provenance(role="experimenter", event_seq=harness._next_seq),
            rule=Rule.CONJ,
            llm=llm_pending,
        )
        if artifact.id not in before:
            llm_pending = None  # a real event carried the shared call
        crit_program(harness, artifact.id)  # checker_wf adjudicates now
        if (
            harness.state.status.get(artifact.id) != Status.ACCEPTED
            or not _oracle_ready(harness, artifact)
            or harness.state.status.get(artifact.id) != Status.ACCEPTED
        ):
            continue
        # Arrival crash probe (intervals/boot postmortem): run the proposed
        # checker against existing carriers' real outputs BEFORE any judge
        # spends tokens on it — a checker that throws on the problem's own
        # domain is refuted mechanically on arrival, with the crash as trace.
        crash = crash_probe(harness, base, content)
        if crash is not None:
            from deepreason.canonical import canonical_json
            from deepreason.rules.warrants import register_fail_warrant

            register_fail_warrant(
                harness,
                commitment_id=wf.id,
                target_id=artifact.id,
                nu_content=(
                    f"nu: proposed checker {artifact.id[:12]} CRASHES on a "
                    "real candidate's output on the frozen inputs — a "
                    "well-formed checker rejects, it does not throw"
                ),
                critic_content=(
                    f"critic: checker of {artifact.id[:12]} raised on the "
                    f"problem's own domain: {str(crash.get('error', ''))[:120]}"
                ),
                trace_ref=harness.blobs.put(canonical_json(crash)),
                skip_if_on_record=True,
            )
            continue
        if relevance_trial(harness, artifact, proposal.claim, problem, adapter, config):
            activated.append(artifact)
    if llm_pending is not None:
        harness.record_measure(inputs=["property-design", base.id], llm=llm_pending)
    return activated
