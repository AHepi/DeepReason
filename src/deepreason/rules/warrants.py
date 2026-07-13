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
) -> Artifact | None:
    """Register ν + DEMONSTRATIVE fail warrant + critic; returns the critic
    (None when skip_if_on_record and the verdict is already on the graph)."""
    if skip_if_on_record and verdict_on_record(harness, commitment_id, target_id):
        return None
    nu = harness.create_artifact(
        nu_content,
        interface=nu_interface,
        provenance=Provenance(role="critic"),
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
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
        llm=llm,
    )
