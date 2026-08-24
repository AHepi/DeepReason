"""Nomination -- §9.4's promotion signal, as a measure-rule over the log.

    reach events for one subject spanning >= K_FRAME distinct problem LINEAGES
    over a coherent candidate scope  =>  Spawn a promotion problem

**The measure DETECTS; it never decides.** Nothing here writes a status, an
HV reading or a reach count; the only writes are a `Problem`, the commitments
its criteria name, and the frozen certificate those criteria read. Promotion
itself is an ordinary Conj->Crit->Adj pass on the problem this spawns, which is
A8: reach can spawn a promotion problem and cannot directly alter a label.

LINEAGE is the load-bearing definition, and it is not free. A problem's parents
are the problems it descends from, reached BOTH through `provenance.from_`
entries that are problems AND through the ORIGIN problem of entries that are
artifacts -- the FIRST `(aid, pid)` pair for that artifact in the append-only
`state.addr`. Two consequences, both required:

  - Connection and integration problems are spawned FROM ARTIFACTS, never from
    problems. A walk that stopped at an artifact source would make every one of
    them its own lineage, and a single-question run would look like dozens.
    Measured on the committed attempt-4 root
    (`experiments/2026-08-22-change-epoch3-second-lineage/run`): under this
    definition all 210 problems share ONE root, the seed, so its single reach
    event spans one lineage and nothing is nominated. Under the truncated walk
    it would have spanned two and fired on a run nobody claims promoted
    anything.
  - The ORIGIN is the FIRST addressing, not the current set. `reach_sweep`
    APPENDS addressing on a full hit, so reading the current set would let a
    reach event retroactively move the lineage roots that reach event is being
    measured against.
"""

from __future__ import annotations

import json

from deepreason.calculus.claims import (
    FrozenCommitmentV1,
    FrozenGrantV1,
    FrozenProblemV1,
    FrozenSubjectV1,
    ReachCertificateV1,
    ReachRecordV1,
    encode,
)
from deepreason.calculus.compiler import compile_interface
from deepreason.calculus.operations import ensure_promotion_problem
from deepreason.calculus.programs import REACH_CERTIFICATE_COMMITMENT
from deepreason.calculus.scope import SCOPE_SCHEMA, ScopeError, compile_scope, scope_admits
from deepreason.ontology import Provenance
from deepreason.ontology.event import Rule
from deepreason.ontology.state import Status

PROMOTION_SCOPE_INCOHERENT = "promotion.scope-incoherent.v1"
PROMOTION_NOMINATED = "promotion.nominated.v1"


def origin_problem(harness, artifact_id: str) -> str | None:
    """The problem an artifact was FIRST addressed to, or None.

    `state.addr` is append-only and applied in event order, so its first entry
    for an artifact is the addressing that existed when the artifact was
    registered. Nothing later can move it, which is what makes every function
    below a pure fold over the log rather than a reading of the current graph.
    """
    for aid, pid in harness.state.addr:
        if aid == artifact_id:
            return pid
    return None


def problem_parents(harness, problem_id: str) -> frozenset[str]:
    """The problems one problem descends from, through both kinds of source."""
    problem = harness.state.problems.get(problem_id)
    if problem is None:
        return frozenset()
    parents = set()
    for source in problem.provenance.from_:
        if source in harness.state.problems:
            parents.add(source)
        elif source in harness.state.artifacts:
            origin = origin_problem(harness, source)
            if origin is not None:
                parents.add(origin)
    parents.discard(problem_id)
    return frozenset(parents)


def lineage_root(harness, problem_id: str) -> str | None:
    """The seed a problem descends from. TOTAL, and deterministic at branches.

    `min()` at a branch and `min(visited)` on a cycle: both are arbitrary
    CHOICES and neither is arbitrary in EFFECT, because the answer must be the
    same on every replay of one log. Totality is Prop 12.1's demand -- a reader
    asking which lineage a problem belongs to gets an answer, never a hang, even
    on a record whose provenance was spliced by hand.
    """
    if problem_id not in harness.state.problems:
        return None
    seen: set[str] = set()
    current = problem_id
    while True:
        if current in seen:
            return min(seen)
        seen.add(current)
        parents = problem_parents(harness, current)
        if not parents:
            return current
        current = min(parents)


def lineage_span(harness, artifact_id: str) -> tuple[str, ...]:
    """The DISTINCT lineage roots of the problems an artifact addresses."""
    roots = {
        root
        for aid, pid in harness.state.addr
        if aid == artifact_id and (root := lineage_root(harness, pid)) is not None
    }
    return tuple(sorted(roots))


def candidate_scope(problem_ids) -> dict:
    """The canonical candidate scope: sigma admitting exactly these problems.

    An ENUMERATION rather than a generalisation, and deliberately so. Nomination
    detects and never decides (R2), so it must not author the interesting claim
    -- "these problems are the same KIND of problem" is precisely what a
    promotion candidate conjectures and is judged on. What the measure may say
    is only which problems the reach actually covered.

    Sorted, so two nominations over the same problems produce the same bytes and
    the certificate carrying it keeps one content address.
    """
    ids = sorted(set(problem_ids))
    leaves = [
        {"op": "eq", "args": [{"field": "id"}, {"text": pid}]} for pid in ids
    ]
    predicate = leaves[0] if len(leaves) == 1 else {"op": "or", "args": leaves}
    return {"schema": SCOPE_SCHEMA, "predicate": predicate}


def _scope_is_coherent(document: dict, problems) -> bool:
    """Coherent = compiles in the closed DSL, and admits exactly these problems.

    A span too wide for the DSL's node bound is a STATED refusal rather than a
    silent one: the caller records `promotion.scope-incoherent.v1` and does not
    nominate, so "we could not build a scope" never reads as "nothing reached".
    """
    try:
        compiled = compile_scope(document)
    except ScopeError:
        return False
    return all(scope_admits(compiled, problem) for problem in problems)


def _registration_seq(harness, artifact_id: str) -> int:
    """The log seq at which an artifact first appears in an event's outputs."""
    for event in harness.log.read():
        if artifact_id in list(event.outputs):
            return int(event.seq)
    return 0


def _reveal_seq(harness, artifact_id: str) -> int | None:
    """The seq of the Reveal event for sealed evidence, if one was recorded.

    §10.5's novel-fact evidence: a pass on material revealed AFTER the artifact
    was registered is the strongest provenance the informal side produces, and
    the log's own ordering is what proves it.
    """
    for event in harness.log.read():
        if event.rule is Rule.REVEAL and artifact_id in list(event.inputs):
            return int(event.seq)
    return None


def _substantive_criteria(harness, problem) -> list[str]:
    from deepreason.measures.reach import _substantive

    return [
        cid for cid in problem.criteria
        if cid in harness.commitments and _substantive(harness.commitments[cid])
    ]


def _accounted(harness, artifact_id: str) -> list[str]:
    """X(a): the problems `a` addresses whose every substantive criterion PASSES.

    `reach_sweep`'s own all-qualifying-pass test, reused rather than re-derived
    -- two definitions of "accounts for" would give the record two answers and
    no way to tell which a verdict meant.
    """
    from deepreason import programs

    artifact = harness.state.artifacts.get(artifact_id)
    if artifact is None:
        return []
    out = []
    for aid, pid in harness.state.addr:
        if aid != artifact_id or pid in out:
            continue
        problem = harness.state.problems.get(pid)
        if problem is None:
            continue
        qualifying = _substantive_criteria(harness, problem)
        if not qualifying:
            continue
        if all(
            programs.evaluate(harness.commitments[cid], artifact, harness.blobs)[0]
            == programs.PASS
            for cid in qualifying
        ):
            out.append(pid)
    return sorted(out)


def _wound_refs(harness, artifact_id: str) -> list[str]:
    """The incumbent's wound list, machine-derived (D-6 answer A).

    A wound is a registered warrant against the subject: the run's own record of
    where the incumbent failed. Derived, never authored, so a successor cannot
    choose which wounds it is answering for.
    """
    return sorted(
        wid for wid, warrant in harness.warrants.items()
        if warrant.target == artifact_id
    )


def _criticised_commitments(harness, artifact_id: str) -> list[str]:
    """Which commitments registered criticism actually cites against a subject.

    Non-immunization reads this: a component nothing has ever cited, that no
    accounted problem asks for, and that risks nothing empirically, can be cut
    without changing a single registered outcome -- which is what makes it a
    rider rather than a part.
    """
    return sorted(
        {
            warrant.commitment
            for warrant in harness.warrants.values()
            if warrant.target == artifact_id and warrant.commitment
        }
    )


def _demarcation(harness, artifact) -> str:
    """The §12.2 reading, cached into the certificate once per subject.

    `crit` alone is taken here. The `load` half needs the variator seat and one
    provider call per subject, which Rung 2 priced and answered: sample once for
    the life of the run and record a TYPED ABSTENTION when the seat is absent.
    Nomination has no seat, so it freezes `declared-only` (K nonempty, the
    second reading untaken) or `no-attack-surface` (K empty, which `crit`
    settles on its own and which no sample could rescue). It never writes
    `load-bearing`; the field exists so a later sweep holding a variator can.
    """
    from deepreason.measures.demarcation import crit

    return "declared-only" if crit(artifact, harness.commitments) else "no-attack-surface"


def _environment(harness, config, problem_ids):
    """The frozen problem records, criterion specs and candidate subjects.

    Bounded by `PROMOTION_ENVIRONMENT_MAX` so a criterion's re-evaluation loop
    has a declared bound (Prop 12.1). What the bound drops is returned so the
    certificate can carry it: a cap nobody can see reads as full coverage.
    """
    cap = max(1, int(config.PROMOTION_ENVIRONMENT_MAX))
    truncated: list[str] = []
    kept_ids = sorted(problem_ids)
    if len(kept_ids) > cap:
        truncated += kept_ids[cap:]
        kept_ids = kept_ids[:cap]
    problems, commitment_ids = [], set()
    for pid in kept_ids:
        problem = harness.state.problems[pid]
        problems.append(
            FrozenProblemV1(
                id=problem.id,
                description=problem.description,
                trigger=problem.provenance.trigger.value,
                sources=list(problem.provenance.from_),
                criteria=list(problem.criteria),
                lineage_root=lineage_root(harness, pid) or "",
            )
        )
        commitment_ids.update(problem.criteria)
    commitments = [
        FrozenCommitmentV1(
            id=cid,
            eval=harness.commitments[cid].eval,
            observation_valued=harness.commitments[cid].observation_valued,
        )
        for cid in sorted(commitment_ids)
        if cid in harness.commitments
    ]
    pool = sorted(
        {
            aid for aid, pid in harness.state.addr
            if pid in set(kept_ids)
            and harness.state.status.get(aid) is Status.ACCEPTED
        }
    )
    if len(pool) > cap:
        truncated += pool[cap:]
        pool = pool[:cap]
    subjects = [
        FrozenSubjectV1(
            artifact_id=aid,
            registered_seq=_registration_seq(harness, aid),
            commitments=list(harness.state.artifacts[aid].interface.commitments),
            demarcation=_demarcation(harness, harness.state.artifacts[aid]),
            hv=harness.state.hv.get(aid),
            accounted=_accounted(harness, aid),
            wound_refs=_wound_refs(harness, aid),
            criticised_commitments=_criticised_commitments(harness, aid),
        )
        for aid in pool
    ]
    # A subject's OWN commitments join the frozen specs: the empirical clause
    # (§12.2's closing sentence) asks whether any of them is observation-valued,
    # and a criterion that could not resolve them would answer `overrun` on
    # every empirical scope.
    for subject in subjects:
        commitment_ids.update(subject.commitments)
    commitments = [
        FrozenCommitmentV1(
            id=cid,
            eval=harness.commitments[cid].eval,
            observation_valued=harness.commitments[cid].observation_valued,
        )
        for cid in sorted(commitment_ids)
        if cid in harness.commitments
    ]
    return problems, commitments, subjects, sorted(set(truncated))


def build_certificate(harness, config, subject_id: str, problem_ids) -> ReachCertificateV1:
    """Freeze everything the five criteria will read. Built ONCE, by the
    measure, from the log -- never consulted live (Rider 5 clause 4)."""
    from deepreason.calculus.standing import consulted

    measure_seq = 0
    for event in harness.log.read():
        if subject_id in dict(event.state_diff.reach_set):
            measure_seq = int(event.seq)
    subject_seq = _registration_seq(harness, subject_id)
    reach_records = [
        ReachRecordV1(
            problem_id=pid,
            lineage_root=lineage_root(harness, pid) or "",
            measure_seq=measure_seq,
            subject_seq=subject_seq,
            reveal_seq=_reveal_seq(harness, subject_id),
        )
        for pid in sorted(problem_ids)
    ]
    problems, commitments, subjects, truncated = _environment(
        harness, config, problem_ids
    )
    return ReachCertificateV1(
        subject_ref=subject_id,
        scope=candidate_scope(problem_ids),
        k_frame=int(config.K_FRAME),
        reach_records=reach_records,
        problems=problems,
        commitments=commitments,
        subjects=subjects,
        consulted=[
            FrozenGrantV1(
                assertion_id=g.assertion_id, subject_ref=g.subject_id, scope=g.scope
            )
            for g in consulted(harness)
        ],
        truncated=truncated,
    )


def register_certificate(harness, body: ReachCertificateV1):
    """Register the certificate as an ORDINARY artifact, content in BLOBS.

    Bytes rather than an inline string: the criteria find it through
    `blobs.get(<sha>)` and re-digest what they read, which is the fence stamp.
    An inline artifact has no blob to fetch and no digest to check.
    """
    harness.register_commitment(REACH_CERTIFICATE_COMMITMENT)
    return harness.create_artifact(
        encode(body).encode("utf-8"),
        codec="json",
        interface=compile_interface(body),
        provenance=Provenance(role="import"),
    )


def promotion_criteria(harness, certificate_ref: str):
    """The five pinned criteria of §9.4, instantiated against ONE certificate.

    Each is content-addressed by the certificate it reads, so two promotion
    problems never share a criterion and no criterion can be pointed at a
    certificate other than the one its problem was nominated on.
    """
    from deepreason.calculus.promotion import criteria_for

    return criteria_for(certificate_ref)


def nominate(harness, config) -> list:
    """The measure-rule. Returns the promotion problems it spawned.

    Idempotent by construction: the promotion problem's id is a pure function of
    its subject (Rung 4's `ensure_promotion_problem`), so a rescan registers
    nothing. The order is fixed by sorting the subjects, so a replay spawns the
    same problems in the same order.
    """
    spawned = []
    for subject_id in sorted(harness.state.reach):
        if harness.state.reach.get(subject_id, 0.0) <= 0:
            continue
        if harness.state.status.get(subject_id) is not Status.ACCEPTED:
            continue
        problem_ids = sorted(
            {pid for aid, pid in harness.state.addr if aid == subject_id}
        )
        span = lineage_span(harness, subject_id)
        if len(span) < int(config.K_FRAME):
            continue
        document = candidate_scope(problem_ids)
        if not _scope_is_coherent(
            document, [harness.state.problems[pid] for pid in problem_ids]
        ):
            harness.record_measure(
                inputs=[PROMOTION_SCOPE_INCOHERENT, subject_id, str(len(problem_ids))]
            )
            continue
        promotion_id = f"promotion:{subject_id[:12]}"
        if promotion_id in harness.state.problems:
            continue
        certificate = register_certificate(
            harness, build_certificate(harness, config, subject_id, problem_ids)
        )
        criteria = promotion_criteria(harness, certificate.content_ref)
        for commitment in criteria:
            harness.register_commitment(commitment)
        problem = ensure_promotion_problem(
            harness,
            subject_id,
            "promote or refuse: this explanation has survived the criteria of "
            f"{len(span)} distinct problem lineages. Conjecture the frame claim "
            "it earns -- its subject, the scope it governs, its validity, and "
            "the protocol for departing from it -- or show that it earns none.",
            criteria=[k.id for k in criteria],
        )
        harness.record_measure(
            inputs=[PROMOTION_NOMINATED, subject_id, certificate.id, problem.id]
        )
        spawned.append(problem)
    return spawned
