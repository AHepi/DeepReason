"""Crit (spec §3): register critic artifacts carrying valid warrants.

- crit_program: run the target's evaluable commitments (tau_kappa); each
  ``fail`` packages an ordinary demonstrative warrant (commitment, verdict,
  trace_ref, attackable validity node nu). A bare verdict is never an edge.
- crit_argumentative: the argumentative_critic role mounts a case; it
  registers on its own merits as an argumentative warrant. Rubric verdicts
  exist only downstream of the trial guard (P5).
"""

from deepreason import programs
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.llm.contracts import ArgumentativeCriticOutput, BatchCriticOutput
from deepreason.llm.packs import (
    render_batch_crit_pack,
    render_crit_pack,
    render_cx_retry_pack,
)
from deepreason.ontology import Artifact, Provenance, Rule, Warrant, WarrantType
from deepreason.rules.warrants import (
    execution_backed,
    register_fail_warrant,
    verdict_on_record,
)


def _register_nu(harness, content: str) -> Artifact:
    return harness.create_artifact(content, provenance=Provenance(role="critic"))


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
    harness, target_id: str, args, *, case: str, llm=None
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
        if verdict != programs.FAIL:
            reasons.append(
                "the target RAN your input and the property HELD — this "
                "counterexample does not discriminate; construct an input where "
                "the target's OUTPUT violates the checker"
            )
            continue
        harness.register_commitment(cx)
        if verdict_on_record(harness, cx.id, target_id):
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
            violation, detail = fuzz_property(
                source, base, config.FUZZ_N, generator=gen_source
            )
            if violation is None:
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
        prop_critic = _crit_proposed_properties(
            harness, target_id, base, source, probes, config
        )
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
        (cid for cid in prop.interface.commitments
         if (kappa := harness.commitments.get(cid)) is not None
         and kappa.eval == f"program:{CHECKER_PROGRAM}"),
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
                    source, base, config.FUZZ_N, generator=gen_source,
                    checker=prop_source,
                )
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
            harness.record_measure(
                inputs=["property-wipeout-quarantine", prop_id, target_id]
            )
            continue
        cx = property_violation_commitment(base, prop_id, prop_source, violation)
        verdict, trace = programs.evaluate(
            cx, harness.state.artifacts[target_id], harness.blobs
        )
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


def crit_argumentative(harness, target_id: str, adapter, config) -> Artifact | None:
    """One argumentative-critic call; registers a critic iff it attacks."""
    pack = render_crit_pack(
        target_id,
        harness.state,
        harness.commitments,
        harness.blobs,
        token_budget=config.PACK_TOKEN_BUDGET,
    )
    output, llm_call = adapter.call("argumentative_critic", pack, ArgumentativeCriticOutput)
    if not output.attack or not output.case.strip():
        # No fault found: the call still spent tokens and must be logged once.
        harness.record_measure(inputs=["arg-crit", target_id], llm=llm_call)
        return None
    before = set(harness.state.artifacts)
    grounded, reason = try_counterexample(
        harness, target_id, output.counterexample, case=output.case, llm=llm_call
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
                token_budget=config.PACK_TOKEN_BUDGET,
            )
            retry, llm_call = adapter.call(
                "argumentative_critic", retry_pack, ArgumentativeCriticOutput
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
    case_hash = sha256_hex(output.case.encode())[:16]
    nu = _register_nu(
        harness, f"nu: argumentative case {case_hash} against {target_id} is sound"
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
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=llm_call,
    )
    if critic.id in before:
        # The critic content deduped to an existing artifact, so no event
        # carried llm_call — log it so token accounting sees the call once.
        harness.record_measure(inputs=["arg-crit", target_id], llm=llm_call)
    return critic


def crit_argumentative_batch(harness, target_ids, adapter, config) -> list[Artifact]:
    """One argumentative-critic call over K targets (§14 batching — the call
    structure is not the epistemology; the warrant structure is). Every
    attacking case registers exactly as in the single path: per-target
    argumentative warrant with its own attackable nu. A case naming an id
    outside the batch is dropped — no verdict without exposure. A single
    target delegates to the single-target contract unchanged."""
    target_ids = list(dict.fromkeys(target_ids))
    if not target_ids:
        return []
    if len(target_ids) == 1:
        critic = crit_argumentative(harness, target_ids[0], adapter, config)
        return [critic] if critic else []
    pack = render_batch_crit_pack(
        target_ids,
        harness.state,
        harness.commitments,
        harness.blobs,
        token_budget=config.PACK_TOKEN_BUDGET,
    )
    output, llm_call = adapter.call(
        "argumentative_critic", pack, BatchCriticOutput, template_role="batch_critic"
    )
    critics: list[Artifact] = []
    ruled: set[str] = set()
    rejected: list[dict] = []  # execution-backed targets queued for cx retry
    # The shared call must be logged on exactly one committed event. Attach it
    # to the first registration that actually COMMITS (a deduped critic
    # commits no event), and fall back to a Measure if none do.
    llm_pending: object | None = llm_call
    for case in output.cases:
        if case.target not in target_ids or case.target in ruled:
            continue
        ruled.add(case.target)
        if not case.attack or not case.case.strip():
            continue  # no fault found for this target: registers nothing
        before = set(harness.state.artifacts)
        grounded, reason = try_counterexample(
            harness, case.target, case.counterexample, case=case.case, llm=llm_pending
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
            harness.record_measure(
                inputs=["arg-crit-overridden-by-execution", case.target]
            )
            if _has_property_oracle(harness, case.target):
                rejected.append(
                    {"target": case.target, "counterexample": case.counterexample,
                     "reason": reason, "case": case.case}
                )
            continue
        case_hash = sha256_hex(case.case.encode())[:16]
        nu = _register_nu(
            harness, f"nu: argumentative case {case_hash} against {case.target} is sound"
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
            provenance=Provenance(role="critic"),
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
    for _ in range(max(0, config.CX_RETRY_MAX)):
        if not rejected:
            break
        retry_pack = render_cx_retry_pack(
            rejected,
            harness.state,
            harness.commitments,
            harness.blobs,
            token_budget=config.PACK_TOKEN_BUDGET,
        )
        retry_out, retry_llm = adapter.call(
            "argumentative_critic", retry_pack, BatchCriticOutput, template_role="batch_critic"
        )
        allowed = {item["target"]: item for item in rejected}
        retry_pending: object | None = retry_llm
        seen_retry: set[str] = set()
        next_rejected: list[dict] = []
        for case in retry_out.cases:
            if case.target not in allowed or case.target in seen_retry:
                continue
            seen_retry.add(case.target)
            if not case.attack:
                continue  # the critic withdrew this attack
            before = set(harness.state.artifacts)
            grounded, reason = try_counterexample(
                harness,
                case.target,
                case.counterexample,
                case=case.case.strip() or allowed[case.target].get("case", ""),
                llm=retry_pending,
            )
            if grounded is not None:
                critics.append(grounded)
                if grounded.id not in before:
                    retry_pending = None
                continue
            next_rejected.append(
                {"target": case.target, "counterexample": case.counterexample,
                 "reason": reason, "case": case.case}
            )
        if retry_pending is not None:
            harness.record_measure(
                inputs=["batch-crit-cx-retry", *sorted(allowed)], llm=retry_pending
            )
        rejected = next_rejected
    if llm_pending is not None:
        # Nothing committed the call (no attacks, or every critic deduped).
        harness.record_measure(inputs=["batch-crit", *target_ids], llm=llm_pending)
    return critics
