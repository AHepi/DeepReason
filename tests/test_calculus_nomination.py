"""Nomination -- the promotion measure-rule (v2 calculus program, Rung 5).

Implements R1, R2, R3 and R11's positive half. Nomination is a MEASURE over
the log: reach events for one subject spanning at least `K_FRAME` distinct
problem LINEAGES, over a coherent candidate scope, spawn a promotion problem.
It DETECTS and never decides -- the promotion itself is an ordinary
Conj->Crit->Adj pass on the problem it spawns, and the axiom this rung answers
for (A8) is exactly that reach can spawn a promotion problem and cannot touch
a label.

The lineage definition is load-bearing and is not free: a problem's parents are
the problems it descends from, reached through `provenance.from_` both directly
and through the ORIGIN problem of any artifact source -- the FIRST `(aid, pid)`
pair for that artifact in the append-only `state.addr`. Later reach-induced
addressing therefore cannot move a lineage root, which is what keeps the
measure a pure fold over the log.
"""

import pytest

from deepreason.calculus import nomination
from deepreason.calculus.scope import compile_scope, scope_admits
from deepreason.config import Config
from deepreason.ontology import (
    Problem,
    ProblemProvenance,
    Provenance,
    SpawnTrigger,
    Status,
)


def _problem(harness, pid, *, trigger=SpawnTrigger.SEED, sources=(), criteria=()):
    return harness.register_problem(
        Problem(
            id=pid,
            description=f"problem {pid}",
            criteria=list(criteria),
            provenance=ProblemProvenance.model_validate(
                {"trigger": trigger, "from": list(sources)}
            ),
        )
    )


def _accepted(harness, text, problem_id):
    """An artifact addressed to a problem and ACCEPTED, the state reach needs."""
    artifact = harness.create_artifact(
        text, provenance=Provenance(role="conjecturer"), problem_id=problem_id
    )
    assert harness.state.status.get(artifact.id) is Status.ACCEPTED
    return artifact


def _two_lineages(harness):
    """One accepted artifact reaching two problems with DISJOINT roots.

    Both roots are registered with no sources, so each is its own lineage; the
    artifact is addressed to one and reaches the other, which is the shape a
    real reach hit produces.
    """
    left = _problem(harness, "question-left")
    right = _problem(harness, "question-right")
    subject = _accepted(harness, "b: one account of both domains", left.id)
    harness.record_measure(reach={subject.id: 1.0}, addr=[(subject.id, right.id)])
    return subject, left, right


# --- lineage, the definition everything else rests on ------------------------


def test_a_problem_with_no_sources_is_its_own_lineage_root(harness):
    seed = _problem(harness, "question-seed")
    assert nomination.lineage_root(harness, seed.id) == "question-seed"
    assert nomination.problem_parents(harness, seed.id) == frozenset()


def test_a_problem_spawned_from_a_problem_inherits_its_root(harness):
    seed = _problem(harness, "question-seed")
    child = _problem(
        harness, "disc:question-seed",
        trigger=SpawnTrigger.DISCRIMINATION, sources=[seed.id],
    )
    assert nomination.lineage_root(harness, child.id) == seed.id


def test_a_problem_spawned_from_an_ARTIFACT_inherits_that_artifact_s_origin(harness):
    """The case the live root turns on.

    `conn:` problems are spawned `from` ARTIFACTS, never from problems. If the
    walk stopped at an artifact source, every connection problem would be its
    own lineage and a single-seed run would look like dozens of lineages --
    which would make nomination fire on the committed attempt-4 root, the one
    thing R11 says it must not do.
    """
    seed = _problem(harness, "question-seed")
    artifact = _accepted(harness, "a: an isolated conjecture", seed.id)
    conn = _problem(
        harness, "conn:derived",
        trigger=SpawnTrigger.CONNECTION, sources=[artifact.id],
    )
    assert nomination.origin_problem(harness, artifact.id) == seed.id
    assert nomination.lineage_root(harness, conn.id) == seed.id


def test_reach_induced_addressing_cannot_move_an_origin(harness):
    """`state.addr` is append-only and the ORIGIN is its FIRST entry, so a later
    reach hit that registers new addressing leaves every lineage root where it
    was. Without this the measure would not be a fold over the log."""
    seed = _problem(harness, "question-seed")
    foreign = _problem(harness, "question-foreign")
    artifact = _accepted(harness, "a: travels well", seed.id)
    before = nomination.origin_problem(harness, artifact.id)
    harness.record_measure(reach={artifact.id: 1.0}, addr=[(artifact.id, foreign.id)])
    assert nomination.origin_problem(harness, artifact.id) == before == seed.id


def test_lineage_root_is_total_even_on_a_cycle(harness):
    """Totality is Prop 12.1's own demand. Provenance cannot normally cycle,
    but a reader of a hand-built or amended record must still get an answer
    rather than a hang, so the walk returns `min(visited)` deterministically."""
    a = _problem(harness, "p-a")
    b = _problem(harness, "p-b", trigger=SpawnTrigger.CONNECTION, sources=[a.id])
    # A cycle can only be built by hand; splice it into replayed state directly.
    harness.state.problems["p-a"] = Problem(
        id="p-a", description="problem p-a",
        provenance=ProblemProvenance.model_validate(
            {"trigger": SpawnTrigger.CONNECTION, "from": [b.id]}
        ),
    )
    assert nomination.lineage_root(harness, a.id) in {"p-a", "p-b"}
    assert nomination.lineage_root(harness, a.id) == nomination.lineage_root(harness, a.id)


def test_lineage_span_counts_DISTINCT_roots_not_problems(harness):
    seed = _problem(harness, "question-seed")
    artifact = _accepted(harness, "a: one domain", seed.id)
    first = _problem(harness, "conn:one", trigger=SpawnTrigger.CONNECTION,
                     sources=[artifact.id])
    second = _problem(harness, "integ:one", trigger=SpawnTrigger.INTEGRATION,
                      sources=[artifact.id])
    harness.record_measure(
        reach={artifact.id: 2.0},
        addr=[(artifact.id, first.id), (artifact.id, second.id)],
    )
    # Three addressed problems, all descending from one seed: ONE lineage.
    assert nomination.lineage_span(harness, artifact.id) == (seed.id,)


# --- the candidate scope, and what makes it coherent -------------------------


def test_the_candidate_scope_admits_exactly_the_reached_problems(harness):
    subject, left, right = _two_lineages(harness)
    document = nomination.candidate_scope([left.id, right.id])
    compiled = compile_scope(document)
    assert scope_admits(compiled, harness.state.problems[left.id])
    assert scope_admits(compiled, harness.state.problems[right.id])
    other = _problem(harness, "question-elsewhere")
    assert not scope_admits(compiled, harness.state.problems[other.id])


def test_the_candidate_scope_is_canonical(harness):
    """Same reached problems in any order => the same document bytes, because
    the certificate that carries it is content-addressed."""
    assert nomination.candidate_scope(["b", "a"]) == nomination.candidate_scope(["a", "b"])


def test_an_incoherent_scope_abstains_rather_than_nominating(harness):
    """A span too large for the closed DSL's node bound is a STATED refusal.

    Recorded as a typed Measure and never as a silent no-op: "we could not
    build a scope" must not look like "nothing reached".
    """
    seed = _problem(harness, "question-seed")
    subject = _accepted(harness, "b: reaches very widely", seed.id)
    roots = [_problem(harness, f"question-{i:03d}") for i in range(400)]
    harness.record_measure(
        reach={subject.id: float(len(roots))},
        addr=[(subject.id, p.id) for p in roots],
    )
    config = Config(K_FRAME=2, PROMOTION_ENVIRONMENT_MAX=1024)
    assert nomination.nominate(harness, config) == []
    recorded = [
        e for e in harness.log.read()
        if nomination.PROMOTION_SCOPE_INCOHERENT in list(e.inputs)
    ]
    assert recorded, "the refusal is on the record"


# --- the threshold, both sides -----------------------------------------------


def test_nomination_fires_at_the_K_frame_threshold(harness):
    subject, left, right = _two_lineages(harness)
    spawned = nomination.nominate(harness, Config(K_FRAME=2))
    assert [p.provenance.trigger for p in spawned] == [SpawnTrigger.PROMOTION]
    assert spawned[0].provenance.from_ == [subject.id]
    assert spawned[0].criteria, "the five criteria are pinned at registration"


def test_nomination_does_not_fire_one_lineage_short(harness):
    subject, left, right = _two_lineages(harness)
    assert nomination.nominate(harness, Config(K_FRAME=3)) == []


def test_nomination_is_idempotent(harness):
    subject, left, right = _two_lineages(harness)
    config = Config(K_FRAME=2)
    first = nomination.nominate(harness, config)
    assert len(first) == 1
    assert nomination.nominate(harness, config) == []


def test_a_refuted_subject_is_never_nominated(harness):
    """Reach is measured on ACCEPTED artifacts; a refuted one carries a stale
    count and must not buy a promotion problem with it."""
    from tests.conftest import attack

    subject, left, right = _two_lineages(harness)
    attack(harness, subject.id, "the account fails on its own criteria")
    assert harness.state.status.get(subject.id) is Status.REFUTED
    assert nomination.nominate(harness, Config(K_FRAME=2)) == []


# --- R2 / A8: the measure detects, it never decides --------------------------


def test_nomination_changes_no_label_and_no_measure(harness):
    """A8, behaviourally. The structural half is the source assertion in
    CHECKLIST step 5; either alone is satisfiable by the wrong thing.

    "Alters no label" is asserted over the labels that ALREADY EXISTED. The one
    permitted addition is the reach certificate's own status: nomination
    registers that artifact, and every unattacked artifact in this tree is
    ACCEPTED, so a new id appearing is registration rather than adjudication.
    What A8 forbids is reach MOVING a judgment, and the assertion below is
    exactly that -- every prior entry identical, no HV reading touched, and no
    reach count touched, so nothing the scheduler ranks on has moved either.
    """
    subject, left, right = _two_lineages(harness)
    before_status = dict(harness.state.status)
    before_hv = dict(harness.state.hv)
    before_reach = dict(harness.state.reach)
    assert nomination.nominate(harness, Config(K_FRAME=2))
    after_status = dict(harness.state.status)
    for aid, label in before_status.items():
        assert after_status[aid] is label, aid
    added = set(after_status) - set(before_status)
    certificates = [
        aid for aid in added
        if "claim:reach-certificate-wf@v1"
        in harness.state.artifacts[aid].interface.commitments
    ]
    assert sorted(added) == sorted(certificates), sorted(added)
    assert dict(harness.state.hv) == before_hv
    assert dict(harness.state.reach) == before_reach


def test_the_spawned_problem_is_an_ordinary_problem(harness):
    """No new event rule and no new field: the promotion problem is a `Problem`
    registered by `register_problem` like any other, which is what lets Rung 4's
    consult predicate find it without knowing anything about nomination."""
    subject, left, right = _two_lineages(harness)
    problem = nomination.nominate(harness, Config(K_FRAME=2))[0]
    assert harness.state.problems[problem.id] == problem
    assert sorted(Problem.model_fields) == ["criteria", "description", "id", "provenance"]
