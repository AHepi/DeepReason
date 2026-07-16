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
import math

from deepreason import programs
from deepreason.authority import argumentative_authority_mode
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.llm.contracts import ArgumentativeCriticOutput, BatchCriticOutput
from deepreason.llm.firewall import EndpointLease
from deepreason.llm.packs import (
    aliases_for_pack,
    render_batch_crit_pack,
    render_crit_pack,
    render_cx_retry_pack,
)
from deepreason.llm.profiles import ModelProfile, get_profile
from deepreason.llm.wire import wire_contract_for
from deepreason.ontology import Artifact, Provenance, Rule, Warrant, WarrantType
from deepreason.rules.warrants import (
    execution_backed,
    register_fail_warrant,
    verdict_on_record,
)


def _register_nu(
    harness, content: str, *, critic_school_id: str | None = None
) -> Artifact:
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
            raise ValueError(
                "manifest-bound criticism requires explicit argumentative authority"
            )
        return _authority(config)
    authority = _authority_value(explicit_authority)
    if authority not in _POLICY_AUTHORITIES:
        raise ValueError(
            "manifest-bound criticism authority must be observe_only or "
            "defended_trial"
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
        raise ValueError(
            "criticism endpoint lease must belong to argumentative_critic"
        )
    assert critic_school_id is not None
    assert critic_school_context is not None
    if critic_school_context.get("id") != critic_school_id:
        raise ValueError(
            "critic execution school must match its semantic conditioning record"
        )
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
        raise ValueError(
            "critic school conditioning leaves insufficient bounded pack budget"
        )
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


def _observe_case(
    harness,
    target_id: str,
    case_text: str,
    llm_call,
    *,
    critic_school_id: str | None = None,
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
    harness.record_measure(
        inputs=["scrutiny", target_id, critic.id],
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
            violation, detail = fuzz_property(
                source, base, config.FUZZ_N, generator=gen_source
            )
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
                    source, base, config.FUZZ_N, generator=gen_source,
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
        bool(call_kwargs)
        or argumentative_authority is not None
        or coverage_observer is not None
    )
    authority = _resolve_authority(
        config, argumentative_authority, policy_call=policy_call
    )
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
            retries = (
                config.CX_RETRY_MAX
                if _has_property_oracle(harness, target_id)
                else 0
            )
            for _ in range(max(0, retries)):
                harness.record_measure(
                    inputs=["arg-crit-cx-rejected", target_id], llm=llm_call
                )
                retry_pack = render_cx_retry_pack(
                    [{"target": target_id, "counterexample": cx, "reason": reason}],
                    harness.state,
                    harness.commitments,
                    harness.blobs,
                    token_budget=_conditioned_budget(
                        config.PACK_TOKEN_BUDGET, school_prefix
                    ),
                )
                retry_pack = _condition_pack(retry_pack, school_prefix)
                retry_aliases = aliases_for_pack(
                    retry_pack, harness.state.artifacts, prefix="A"
                )
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
                        harness.record_measure(
                            inputs=["arg-crit", target_id], llm=llm_call
                        )
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
        bool(call_kwargs)
        or argumentative_authority is not None
        or coverage_observer is not None
    )
    authority = _resolve_authority(
        config, argumentative_authority, policy_call=policy_call
    )
    target_ids = list(dict.fromkeys(target_ids))
    if not target_ids:
        return []
    if len(target_ids) == 1:
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
        get_profile(adapter.profile_for("argumentative_critic")).name
        == ModelProfile.COMPACT
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
    pack = render_batch_crit_pack(
        target_ids,
        harness.state,
        harness.commitments,
        harness.blobs,
        token_budget=_conditioned_budget(config.PACK_TOKEN_BUDGET, school_prefix),
    )
    pack = _condition_pack(pack, school_prefix)
    output, llm_call = adapter.call(
        "argumentative_critic",
        pack,
        BatchCriticOutput,
        template_role="batch_critic",
        **call_kwargs,
    )
    try:
        return _crit_argumentative_batch_result(
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
        )
    finally:
        _observe_coverage(
            harness,
            tuple(target_ids),
            llm_call,
            coverage_observer,
        )


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
) -> list[Artifact]:
    """Process one already-returned batch without changing its route policy."""

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
            harness,
            case.target,
            case.counterexample,
            case=case.case,
            llm=llm_pending,
            critic_school_id=critic_school_id,
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
    for _ in range(max(0, config.CX_RETRY_MAX)):
        if not rejected:
            break
        retry_pack = render_cx_retry_pack(
            rejected,
            harness.state,
            harness.commitments,
            harness.blobs,
            token_budget=_conditioned_budget(
                config.PACK_TOKEN_BUDGET, school_prefix
            ),
        )
        retry_pack = _condition_pack(retry_pack, school_prefix)
        retry_out, retry_llm = adapter.call(
            "argumentative_critic",
            retry_pack,
            BatchCriticOutput,
            template_role="batch_critic",
            **call_kwargs,
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
                critic_school_id=critic_school_id,
            )
            if grounded is not None:
                critics.append(grounded)
                if grounded.id not in before:
                    retry_pending = None
                continue
            next_rejected.append(
                {
                    "target": case.target,
                    "counterexample": case.counterexample,
                    "reason": reason,
                    "case": case.case,
                }
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
