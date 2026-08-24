"""L-3: the whole promotion path completes on a SOLO configuration (R14).

The operator's standing law, verbatim (CLAUDE.md, 2026-08-09): "A solo run with
everything on should be an option. That's what solo run option should always
have been. However, turning on judges at all should be done with caution. I
would prefer to do without, since they prosecute without any discernable
discrimination."

D-6 answer A is what makes promotion satisfy it (C7): `accounts-for` is
program-checked against a machine-derived wound list, so succession -- the one
place §9.7's letter is judge-shaped ("pairwise ruling, cited decisive point,
mandatory order-swap") -- needs no judge seat. A rubric ruling can still enter,
but only through the existing trial guard, and nothing in this path invokes it.

Asserted STRUCTURALLY and BEHAVIOURALLY, because either alone is satisfiable by
the wrong thing: a path that merely happens not to reach a seat today is not the
same as a path that cannot.
"""

import ast
import pathlib

import pytest

from deepreason.calculus import nomination, operations, promotion
from deepreason.calculus.standing import consultability_of, consulted, standing_view
from deepreason.config import Config
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    SpawnTrigger,
    Status,
)

SCOPE_ALL = {"schema": "declarative-scope.v1", "predicate": {"const": True}}
SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "deepreason" / "calculus"


def test_the_default_configuration_really_is_solo():
    """The premise of every behavioural claim below. If judges were on by
    default, a green path here would prove nothing about a solo run."""
    config = Config()
    assert config.JUDGE_SEATS_ENABLED is False
    assert config.JUDGE_SUMMONS_PER_CYCLE == 0


def test_no_promotion_module_can_reach_a_seat():
    """The structural half. Neither module imports an LLM, adapter, seat,
    qualification, judge or trial path -- so the promotion road cannot acquire
    a seat dependency by a later edit without this test going red.

    This is also frozen surface 5 held at zero: the v2 program adds NO new LLM
    role, so no qualification subject digest moves and no home owes a
    ~14-minute battery rerun.
    """
    forbidden = ("llm", "adapter", "seat", "provider", "qualification", "judge",
                 "trial", "ensemble")
    for name in ("nomination.py", "promotion.py"):
        tree = ast.parse((SRC / name).read_text())
        modules = [
            (node.module or "") for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ] + [
            alias.name for node in ast.walk(tree)
            if isinstance(node, ast.Import) for alias in node.names
        ]
        assert not any(
            part in module for module in modules for part in forbidden
        ), (name, modules)


def test_the_whole_path_completes_with_no_seats_at_all(harness):
    """The behavioural half, end to end and in the scheduler's own order:
    reach -> nominate -> certificate -> criteria -> warrants -> consultation.

    No adapter is constructed anywhere in this test. If any step needed a seat
    it would raise rather than quietly degrade.
    """
    config = Config()
    kappa = Commitment(id="k-mechanism", eval="predicate:len(content) > 0")
    harness.register_commitment(kappa)
    left = harness.register_problem(Problem(
        id="question-left", description="why do tides follow the moon",
        criteria=[kappa.id],
        provenance=ProblemProvenance.model_validate({"trigger": SpawnTrigger.SEED,
                                                     "from": []}),
    ))
    right = harness.register_problem(Problem(
        id="question-right", description="why do spring tides recur fortnightly",
        criteria=[kappa.id],
        provenance=ProblemProvenance.model_validate({"trigger": SpawnTrigger.SEED,
                                                     "from": []}),
    ))
    subject = harness.create_artifact(
        "b: the lunar theory of tides",
        interface=Interface(commitments=[kappa.id]),
        provenance=Provenance(role="conjecturer"), problem_id=left.id,
    )
    harness.record_measure(reach={subject.id: 1.0}, addr=[(subject.id, right.id)])

    # 1. NOMINATE. A promotion problem exists that did not exist before.
    spawned = nomination.nominate(harness, config)
    assert [p.provenance.trigger for p in spawned] == [SpawnTrigger.PROMOTION]
    problem = spawned[0]
    assert len(problem.criteria) == len(promotion.PROMOTION_PROGRAMS)

    # 2. The frozen certificate is on the record as an ordinary artifact.
    certificate = next(
        a for a in harness.state.artifacts.values()
        if "claim:reach-certificate-wf@v1" in a.interface.commitments
    )
    assert harness.state.status[certificate.id] is Status.ACCEPTED

    # 3. A candidate answers the promotion problem, as an ordinary Conj would.
    good = operations.file_frame_assertion(
        harness, problem=problem, subject_ref=subject.id, scope=SCOPE_ALL,
        departure_protocol="declare the departure in the pack and cite this id",
        reach_case_refs=[certificate.id],
    )
    naked = operations.file_frame_assertion(
        harness, problem=problem, subject_ref=subject.id, scope=SCOPE_ALL,
        departure_protocol="declare the departure in the pack and cite this id",
    )

    # 4. The criteria fire and mint DEMONSTRATIVE warrants -- no seat, no judge.
    minted = promotion.promotion_criteria_sweep(harness, config)
    assert minted

    # 5. The refused candidate stops being consulted; the surviving one is not
    #    refused by any criterion.
    assert harness.state.status[naked.id] is Status.REFUTED
    assert not consultability_of(harness, naked.id).consultable
    assert not [w for w in harness.warrants.values() if w.target == good.id]

    # 6. The read-only standing view renders, which is the whole point of the
    #    path: a solo run can say what is framing what.
    view = standing_view(harness)
    assert view["view"] == "standing.v1"
    assert good.id in {g.assertion_id for g in consulted(harness)}
    assert naked.id not in {g.assertion_id for g in consulted(harness)}


def test_succession_itself_needs_no_judge(harness):
    """The clause D-6 was asked about. §9.7 resolves succession by
    discrimination, which is judge-shaped; `accounts-for` resolves it by
    program, and the relation is exercised here with no seat in the process."""
    from deepreason.calculus.claims import (
        FrameAssertionV1,
        FrozenGrantV1,
        FrozenProblemV1,
        FrozenSubjectV1,
        ReachCertificateV1,
    )

    certificate = ReachCertificateV1(
        subject_ref="e-prime", scope=SCOPE_ALL, k_frame=2,
        problems=[FrozenProblemV1(id="p1", description="p1", trigger="seed",
                                  criteria=["k-mechanism"]),
                  FrozenProblemV1(id="p2", description="p2", trigger="seed",
                                  criteria=["k-mechanism"])],
        subjects=[
            FrozenSubjectV1(artifact_id="e", accounted=["p1"], hv=0.6,
                            commitments=["k-mechanism"], wound_refs=["w1"],
                            demarcation="load-bearing"),
            FrozenSubjectV1(artifact_id="e-prime", accounted=["p1", "p2"], hv=0.7,
                            commitments=["k-mechanism"], demarcation="load-bearing"),
        ],
        consulted=[FrozenGrantV1(assertion_id="a-e", subject_ref="e",
                                 scope=SCOPE_ALL)],
    )
    claim = FrameAssertionV1(
        subject_ref="e-prime", scope=SCOPE_ALL,
        departure_protocol="cite this id", succeeded_wound_refs=["w1"],
    )
    verdict, detail = promotion.succeeds(certificate, claim)
    assert verdict == "pass"
    assert detail["strictness"] == "recovery"
