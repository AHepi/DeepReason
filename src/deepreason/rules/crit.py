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
from deepreason.llm.packs import render_batch_crit_pack, render_crit_pack
from deepreason.ontology import Artifact, Provenance, Rule, Warrant, WarrantType
from deepreason.oracle import EXEC_PROGRAM
from deepreason.rules.warrants import register_fail_warrant, verdict_on_record


def _register_nu(harness, content: str) -> Artifact:
    return harness.create_artifact(content, provenance=Provenance(role="critic"))


def execution_backed(harness, target_id: str) -> bool:
    """Execution-supremacy guard (§3): True iff the target carries at least one
    exec-oracle commitment and EVERY exec-oracle commitment it carries currently
    passes. A passing execution verdict is a warrant from reality (the candidate
    was RUN against fixed tests and produced the right answers); a purely
    *argumentative* critic — an LLM arguing an LLM's output is wrong — must not
    override it. When this holds, crit_argumentative registers no warrant: the
    critic keeps its grounded recourse (supply a failing input via a stronger
    exec-oracle, whose demonstrative fail warrant refutes by execution; or attack
    the oracle's validity node / the commitment itself), but it cannot win by
    assertion. Deterministic (§0): the oracle re-runs the candidate against its
    frozen tests, so the guard is a pure function of content and replays
    byte-for-byte; it decides only whether an edge is CREATED — it never
    adjudicates an edge already on the graph, so att/dep stay the only inputs to
    labels, and nothing is deleted (D8) or made final (N1: execution can still
    refute)."""
    target = harness.state.artifacts.get(target_id)
    if target is None:
        return False
    saw = False
    for cid in target.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None or kappa.eval != f"program:{EXEC_PROGRAM}":
            continue
        saw = True
        verdict, _ = programs.evaluate(kappa, target, harness.blobs)
        if verdict != programs.PASS:
            return False  # execution already refutes it: no protection to give
    return saw


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
    if execution_backed(harness, target_id):
        # Execution supremacy (§3): the target passes its exec-oracle, so a
        # verdict from reality already stands. A purely argumentative case
        # cannot override it — register nothing and log the override so the
        # call is on the record. The critic's grounded recourse is unaffected.
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
        if execution_backed(harness, case.target):
            continue  # execution supremacy (§3): reality overrides the argument
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
    if llm_pending is not None:
        # Nothing committed the call (no attacks, or every critic deduped).
        harness.record_measure(inputs=["batch-crit", *target_ids], llm=llm_pending)
    return critics
