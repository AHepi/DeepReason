"""The premise channel: how a problem is criticised, marked, and replaced.

Regression (v2 calculus program, Rung 2): a problem is not an artifact and
never enters ``att``/``dep``. It is criticised THROUGH its premise, and what it
receives is a mark with three legal answers -- never a status.

The centrepiece is the operator's own siren case (2026-08-13): "What is the
colour of a siren. It's a question that could be interpreted as a problem, but
it's fundamentally flawed before even receiving an answer... In this case, the
problem itself is the subject of criticism, which is summarily refuted. Not a
conjecture, a problem." No conjecture is ever proposed on that problem, and it
still dies.
"""

import json

import pytest

from deepreason.ontology import Commitment, Interface, Ref, Status
from deepreason.ontology.artifact import RefRole
from deepreason.premises import (
    ATTRIBUTION_EVAL,
    PREMISE_REFUTED,
    PREMISE_UNACCREDITED,
    RESOLUTION_EVAL,
    attribution_content,
    open_orphans,
    premise_orphaned,
    premise_resolution_wf_program,
    premise_work_invited,
    presupposition_wf_program,
    resolution_content,
    retired_problems,
    standing_attributions,
)
from deepreason.ontology import Problem, ProblemProvenance
from tests.conftest import art, attack


def _commitment(harness, eval_name: str) -> str:
    kappa = Commitment(id=f"{eval_name}@v2", eval=eval_name, budget={"steps": 1000})
    harness.register_commitment(kappa)
    return kappa.id


def _attribution(harness, problem_id: str, premise_id: str, *, depend=False):
    """Register an attribution. `depend` mounts the mention-law violation."""
    cid = _commitment(harness, ATTRIBUTION_EVAL)
    role = RefRole.DEPENDENCE if depend else RefRole.MENTION
    return harness.create_artifact(
        attribution_content(problem_id, premise_id),
        codec="json",
        interface=Interface(
            commitments=[cid], refs=[Ref(target=premise_id, role=role)]
        ),
    )


def _problem(harness, description: str) -> str:
    """Register a problem and return its id."""
    problem = harness.register_problem(
        Problem(
            id=description.replace(" ", "-"),
            description=description,
            criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    return problem.id


def _addressed(harness, problem_id: str, text: str):
    """A candidate registered as addressing a problem."""
    return harness.create_artifact(text, problem_id=problem_id)


def _resolution(harness, kind: str, problem_id: str, *, successor=None):
    cid = _commitment(harness, RESOLUTION_EVAL)
    return harness.create_artifact(
        resolution_content(kind, problem_id, successor=successor),
        codec="json",
        interface=Interface(commitments=[cid], refs=[]),
    )


# --- the mention law -------------------------------------------------------


def test_an_attribution_may_not_depend_on_its_premise():
    """Law 9.4' -- the whole separation.

    An attribution that DEPENDS on its premise falls with it, so the cascade
    would disarm itself at exactly the moment it is needed.
    """
    text = attribution_content("pi", "X")

    class _A:
        interface = Interface(
            commitments=[], refs=[Ref(target="X", role=RefRole.DEPENDENCE)]
        )

    verdict, trace = presupposition_wf_program(text, None, _A())
    assert verdict == "fail"
    assert "mention law" in trace["reason"]


def test_a_well_formed_attribution_passes():
    class _A:
        interface = Interface(
            commitments=[], refs=[Ref(target="X", role=RefRole.MENTION)]
        )

    verdict, trace = presupposition_wf_program(attribution_content("pi", "X"), None, _A())
    assert verdict == "pass"
    assert trace == {"problem": "pi", "premise": "X"}


@pytest.mark.parametrize(
    "body",
    [
        "not json at all",
        json.dumps({"problem": "pi"}),
        json.dumps({"premise": "X"}),
        json.dumps({"resolution": "translate", "problem": "pi"}),
    ],
)
def test_malformed_attributions_fail(body):
    class _A:
        interface = Interface(commitments=[], refs=[])

    assert presupposition_wf_program(body, None, _A())[0] == "fail"


def test_translate_must_name_its_successor():
    assert premise_resolution_wf_program(
        json.dumps({"resolution": "translate", "problem": "pi"}), None
    )[0] == "fail"
    assert premise_resolution_wf_program(
        resolution_content("translate", "pi", successor="pi2"), None
    )[0] == "pass"


# --- the two locks ---------------------------------------------------------


def test_an_attribution_alone_marks_nothing(harness):
    """Filing an attribution is not criticising the premise."""
    premise = art(harness, "a siren is the kind of thing that has a colour")
    _attribution(harness, "pi", premise.id)

    assert harness.state.status[premise.id] == Status.ACCEPTED
    assert premise_orphaned(harness) == {}


def test_a_refuted_premise_alone_marks_nothing(harness):
    """No standing attribution, no mark -- refuting a claim does not orphan
    every problem that might arguably have rested on it."""
    premise = art(harness, "a siren is the kind of thing that has a colour")
    attack(harness, premise.id, "sound events bear no colour")

    assert harness.state.status[premise.id] == Status.REFUTED
    assert premise_orphaned(harness) == {}


def test_both_locks_open_marks_the_problem(harness):
    premise = art(harness, "a siren is the kind of thing that has a colour")
    _attribution(harness, "colour-of-a-siren", premise.id)
    attack(harness, premise.id, "sound events bear no colour")

    assert premise_orphaned(harness) == {"colour-of-a-siren": PREMISE_REFUTED}


def test_attacking_the_attribution_releases_the_problem(harness):
    """"The problem never assumed that" -- without rescuing the premise."""
    premise = art(harness, "a siren is the kind of thing that has a colour")
    rho = _attribution(harness, "colour-of-a-siren", premise.id)
    attack(harness, premise.id, "sound events bear no colour")
    assert premise_orphaned(harness)

    attack(harness, rho.id, "the question was always about the housing")

    assert harness.state.status[premise.id] == Status.REFUTED  # premise still down
    assert premise_orphaned(harness) == {}                      # problem released


# --- the operator's siren case, end to end ---------------------------------


def test_the_siren_case_end_to_end(harness):
    """Fundamentally flawed before receiving an answer.

    No conjecture is ever proposed on the problem. It is marked and retired on
    the strength of an attack on what it presupposed -- and every step is
    reversible.
    """
    problem = "colour-of-a-siren"

    premise = art(harness, "a siren is the kind of thing that has a colour")
    _attribution(harness, problem, premise.id)

    # Nothing was ever conjectured against the problem.
    assert not [aid for aid, pid in harness.state.addr if pid == problem]

    critic, _ = attack(harness, premise.id, "a category error: it forbids nothing")
    assert harness.state.status[premise.id] == Status.REFUTED
    assert premise_orphaned(harness) == {problem: PREMISE_REFUTED}
    assert open_orphans(harness) == {problem: PREMISE_REFUTED}

    retirement = _resolution(harness, "retire", problem)
    assert retired_problems(harness) == {problem}
    assert open_orphans(harness) == {}       # resolved, so no longer open work

    # N1: attack the retirement and the problem returns to the frontier.
    attack(harness, retirement.id, "the premise has been reinstated")
    assert retired_problems(harness) == set()
    assert open_orphans(harness) == {problem: PREMISE_REFUTED}

    # N1 again, one level down: defeat the critic and the premise reinstates,
    # which un-marks the problem by the same computed predicate.
    attack(harness, critic.id, "sirens are individuated by their housing")
    assert harness.state.status[premise.id] == Status.ACCEPTED
    assert premise_orphaned(harness) == {}


def test_translate_is_the_only_replacement(harness):
    premise = art(harness, "the siren's emitted pitch falls")
    _attribution(harness, "pi", premise.id)
    attack(harness, premise.id, "the source frequency is constant")

    _resolution(harness, "translate", "pi", successor="pi-observed-pitch")

    from deepreason.premises import standing_resolutions

    body = standing_resolutions(harness)["pi"]
    assert body["resolution"] == "translate"
    assert body["successor"] == "pi-observed-pitch"
    assert retired_problems(harness) == set()   # translated, not retired


def test_independence_closes_without_retiring(harness):
    premise = art(harness, "a siren is the kind of thing that has a colour")
    _attribution(harness, "pi", premise.id)
    attack(harness, premise.id, "a category error")

    _resolution(harness, "independence", "pi")

    assert open_orphans(harness) == {}
    assert retired_problems(harness) == set()
    # The problem's own record is never mutated: the holding is computed from
    # the resolution artifact, not written onto the problem.
    assert premise_orphaned(harness) == {"pi": PREMISE_REFUTED}


def test_an_unsupported_premise_grades_as_unaccredited(harness):
    ground = art(harness, "the ground the premise rests on")
    premise = harness.create_artifact(
        "a siren is the kind of thing that has a colour",
        interface=Interface(
            commitments=[], refs=[Ref(target=ground.id, role=RefRole.DEPENDENCE)]
        ),
    )
    _attribution(harness, "pi", premise.id)
    attack(harness, ground.id, "the ground fails")

    assert harness.state.status[premise.id] == Status.SUSPENDED_UNSUPPORTED
    assert premise_orphaned(harness) == {"pi": PREMISE_UNACCREDITED}


# --- the producer ----------------------------------------------------------


def test_the_producer_fires_after_enough_refutations(harness):
    """The anti-E28 check: a mechanism nobody triggers is a mechanism that
    never runs. This harness has shipped two of those already."""
    problem = _problem(harness, "why does the kettle whistle")

    assert not premise_work_invited(harness, problem, after=2)

    for i in range(2):
        candidate = _addressed(harness, problem, f"answer {i}")
        attack(harness, candidate.id, f"refutation {i}")

    assert premise_work_invited(harness, problem, after=2)


def test_the_producer_stands_down_once_a_premise_is_attributed(harness):
    problem = _problem(harness, "why does the kettle whistle")
    for i in range(2):
        candidate = _addressed(harness, problem, f"answer {i}")
        attack(harness, candidate.id, f"refutation {i}")

    premise = art(harness, "a kettle is the kind of thing that whistles")
    _attribution(harness, problem, premise.id)

    assert not premise_work_invited(harness, problem, after=2)
