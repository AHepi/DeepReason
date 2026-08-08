"""Shared demonstrative fail-warrant package (spec §2/§3).

Six sites used to hand-build the same triple — attackable validity node ν,
DEMONSTRATIVE fail warrant (`w:<commitment>:<target>`), critic artifact
carrying it — with the duplicate-verdict guard present at only some of
them. The id scheme, the ν/critic wiring, and the guard predicate are
load-bearing for adjudication and the audit machinery, so they live here
exactly once. Every site passes its own ν wording, critic wording, and
trace payload unchanged — the helper is plumbing, not policy.
"""

from deepreason.ontology import Artifact, Interface, Provenance, Rule, Warrant, WarrantType


def verdict_on_record(harness, commitment_id: str, target_id: str) -> bool:
    """The §3 duplicate-verdict guard: one (κ, target) fail verdict on the
    graph at a time — re-registration would double-register critics."""
    return any(
        w.commitment == commitment_id and w.target == target_id
        for w in harness.warrants.values()
    )


def execution_backed(harness, target_id: str) -> bool:
    """Execution-supremacy guard (§3): True iff the target carries at least one
    exec-oracle commitment and EVERY exec-oracle commitment it carries currently
    passes. A passing execution verdict is a warrant from reality (the candidate
    was RUN against fixed tests and produced the right answers); a purely
    *argumentative* warrant — an LLM arguing an LLM's output is wrong, or a
    pairwise judge preferring a rival (§10.2) — must not override it. Every
    argumentative registration path consults this guard and, when it holds,
    registers nothing: the critic keeps its grounded recourse (supply a failing
    input via a stronger exec-oracle, whose DEMONSTRATIVE fail warrant refutes by
    execution; or attack the oracle's validity node / the commitment itself), but
    it cannot win by assertion or preference.

    Deterministic (§0): the oracle re-runs the candidate against its frozen tests,
    so the guard is a pure function of content and replays byte-for-byte; it
    decides only whether an edge is CREATED — it never adjudicates an edge already
    on the graph, so att/dep stay the only inputs to labels, nothing is deleted
    (D8), and nothing is made final (N1: execution can still refute)."""
    from deepreason import programs
    from deepreason.oracle import EXEC_PROGRAMS

    execution_evals = {f"program:{p}" for p in EXEC_PROGRAMS}
    target = harness.state.artifacts.get(target_id)
    if target is None:
        return False
    saw = False
    for cid in target.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None or kappa.eval not in execution_evals:
            continue
        saw = True
        verdict, _ = programs.evaluate(kappa, target, harness.blobs)
        if verdict != programs.PASS:
            return False  # execution already refutes it: no protection to give
    return saw


def formally_backed(harness, target_id: str) -> bool:
    """Prose-immunity guard: True iff the target carries at least one EVALUABLE
    AND SUBSTANTIVE commitment and EVERY such commitment currently passes.

    A superset of ``execution_backed``: every exec-oracle commitment is
    substantive, so anything execution protects this protects too. What it adds
    is the rest of the formal set — ``predicate:`` criteria and substantive
    ``program:`` checks — which are formal claims and so require formal
    refutation.

    SUBSTANTIVE is load-bearing and is not decoration. An artifact's
    commitments are compiled from the problem's criteria plus harness-owned
    mandatory ones, EXCEPT for one model-authored route: safe skeleton
    compilation turns a conjecturer's own forbidden cases into Commitments
    (workloads/models.py:105). ``ForbiddenCase`` forbids ``predicate:`` there
    for RCE reasons, so predicates can only come from operator-authored
    criteria — but ``program:`` can be model-authored. Were mere evaluability
    enough, a candidate could attach ``program:json-wf``, which passes for
    anything well-formed, and immunise itself against criticism. Structural
    well-formedness proves nothing about the subject, so it protects nothing
    about the subject; ``measures/reach.py`` refuses reach on the same ground.

    The all-currently-pass clause is ``execution_backed``'s and is kept for its
    reason: a failing formal commitment is already refuted mechanically, and
    protecting it would protect a claim that is already defeated.

    Dual-mode conjecture (D2 rev 2, R43): a ``program:candidate_checker``
    commitment (the sole kind that can carry a relatedness claim, oracle.py)
    additionally requires ``relatedness_claim_holds`` — a sustained
    relatedness challenge strips it from this set even while it still
    passes, so the shield falls without touching the target's own
    ``Status``. Every other kind is unaffected: no linked claim is possible
    for them, so the check is a no-op (F6's opt-out default, R-a).
    """
    from deepreason import programs
    from deepreason.measures.reach import _substantive
    from deepreason.oracle import CANDIDATE_CHECKER_PROGRAM
    from deepreason.rules.relatedness import relatedness_claim_holds

    target = harness.state.artifacts.get(target_id)
    if target is None:
        return False
    saw = False
    for cid in target.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None or not _substantive(kappa):
            continue
        if kappa.eval == f"program:{CANDIDATE_CHECKER_PROGRAM}" and not relatedness_claim_holds(
            harness, target_id, cid
        ):
            continue
        saw = True
        verdict, _ = programs.evaluate(kappa, target, harness.blobs)
        if verdict != programs.PASS:
            return False
    return saw


def register_fail_warrant(
    harness,
    *,
    commitment_id: str,
    target_id: str,
    nu_content: str,
    critic_content: str,
    trace_ref: str,
    nu_interface: Interface | None = None,
    warrant_id: str | None = None,
    llm=None,
    skip_if_on_record: bool = False,
    critic_school_id: str | None = None,
) -> Artifact | None:
    """Register ν + DEMONSTRATIVE fail warrant + critic; returns the critic
    (None when skip_if_on_record and the verdict is already on the graph)."""
    if skip_if_on_record and verdict_on_record(harness, commitment_id, target_id):
        return None
    nu = harness.create_artifact(
        nu_content,
        interface=nu_interface,
        provenance=Provenance(role="critic", school=critic_school_id),
    )
    warrant = Warrant(
        id=warrant_id or f"w:{commitment_id}:{target_id}",
        target=target_id,
        type=WarrantType.DEMONSTRATIVE,
        commitment=commitment_id,
        verdict="fail",
        trace_ref=trace_ref,
        validity_node=nu.id,
    )
    return harness.create_artifact(
        critic_content,
        provenance=Provenance(role="critic", school=critic_school_id),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=llm,
    )
