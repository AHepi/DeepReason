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
    PREMISE_RENT,
    PREMISE_UNACCREDITED,
    RESOLUTION_EVAL,
    attribution_content,
    file_premise,
    open_orphans,
    premise_orphaned,
    premise_rent_sweep,
    premise_resolution_wf_program,
    premise_work_invited,
    presupposition_wf_program,
    resolution_content,
    retired_problems,
    standing_attributions,
)
from deepreason.ontology import Problem, ProblemProvenance
from tests.conftest import art, attack

_SIREN_PREMISE = "a siren is the kind of thing that has a colour"


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


class _Variator:
    """A deterministic stand-in for the §12.1 kernel and §12.2's role-variant
    test. `differs` decides whether a sampled variant draws a different verdict
    vector — the whole content of the second demarcation reading."""

    def __init__(self, variants=("a siren has a pitch",), *, differs=False):
        self.variants = list(variants)
        self.differs = differs
        self.sampled: list[str] = []

    def sample(self, artifact):
        from deepreason.programs import content_text

        self.sampled = list(self.variants)
        return content_text(artifact, self._blobs), list(self.variants)

    def role_variant_differs(self, text, variant):
        return self.differs

    def bind(self, harness):
        self._blobs = harness.blobs
        return self


# --- demarcation (Formalization 12.2) ---------------------------------------


def test_crit_is_the_weak_declaration_test(harness):
    """12.2: crit(a) = 1[K_a != {}]. NOT 'carries a substantive commitment'.

    This is the superseded design's inverse and it is deliberate: the
    self-immunisation hole moved to `load`, where it is closed better.
    """
    from deepreason.measures.demarcation import crit

    bare = art(harness, "declares nothing at all")
    assert not crit(bare, harness.commitments)

    structural = art(
        harness, "well formed and nothing more",
        interface=Interface(commitments=[_commitment(harness, "program:json-wf")]),
    )
    assert crit(structural, harness.commitments)

    # The harness refuses to REGISTER an artifact naming an unknown commitment,
    # so this branch is unreachable through the normal path -- which is the
    # stronger guarantee. Checked directly so `crit`'s own contract still holds
    # for any caller holding an unregistered interface.
    class _Unregistered:
        interface = Interface(commitments=["no-such-commitment"])

    assert not crit(_Unregistered(), harness.commitments)


def test_a_structural_battery_is_not_load_bearing(harness):
    """The self-immunisation trap, closed in `load` rather than in `crit`.

    An artifact attaching a well-formedness check has a nonempty attack
    surface, so it passes the first reading. Its role variants pass the same
    check, so the verdict vectors agree and the second reading fails.
    """
    from deepreason.measures.demarcation import crit, demarcated

    cid = _commitment(harness, "program:json-wf")
    immunized = art(harness, '{"ok": true}',
                    interface=Interface(commitments=[cid]))

    assert crit(immunized, harness.commitments)
    assert not demarcated(
        immunized, harness.commitments, _Variator(('{"ok": false}',)).bind(harness)
    )


def test_the_rent_battery_never_enters_its_own_battery(harness):
    """Stratification by construction: the rent commitment is not evaluable, so
    it is absent from B^-HV and no variant can differ on it."""
    from deepreason.measures.demarcation import evaluation_battery

    harness.register_commitment(PREMISE_RENT)
    premise = art(harness, _SIREN_PREMISE,
                  interface=Interface(commitments=[PREMISE_RENT.id]))

    assert PREMISE_RENT.id not in evaluation_battery(harness, premise)


def test_demarcated_is_both_readings(harness):
    """demarcated(a) = crit(a) and load(a); neither half alone is demarcation."""
    from deepreason.measures.demarcation import demarcated

    substantive = _commitment(harness, "predicate: 'steam' in content")
    forbidding = art(harness, "the whistle is driven by steam",
                     interface=Interface(commitments=[substantive]))

    assert demarcated(forbidding, harness.commitments,
                      _Variator(("driven by resonance",), differs=True).bind(harness))
    assert not demarcated(forbidding, harness.commitments,
                          _Variator(("a reword",)).bind(harness))       # load fails

    bare = art(harness, "declares nothing at all")
    assert not demarcated(bare, harness.commitments,
                          _Variator(("anything",), differs=True).bind(harness))  # crit fails


# --- the rent battery ------------------------------------------------------


def test_a_premise_falls_by_demarcation_with_no_written_refutation(harness):
    """A5 on a live path: nobody in this test writes an attack.

    The siren case as the harness must reach it -- the premise is filed, the
    demarcation criterion adjudicates it, the problem is marked. `attack()` is
    never called and no conjecture is ever proposed on the problem.
    """
    problem = _problem(harness, "what is the colour of a siren")
    premise, rho = file_premise(harness, problem, _SIREN_PREMISE)

    assert harness.state.status[premise.id] == Status.ACCEPTED
    assert premise_orphaned(harness) == {}

    critics = premise_rent_sweep(harness, _Variator().bind(harness))

    assert len(critics) == 1
    assert harness.state.status[premise.id] == Status.REFUTED
    assert harness.state.status[rho.id] == Status.ACCEPTED  # the mention law holds
    assert premise_orphaned(harness) == {problem: PREMISE_REFUTED}
    assert not [aid for aid, pid in harness.state.addr if pid == problem]


def test_the_rent_verdict_is_reversible_and_never_doubled(harness):
    problem = _problem(harness, "what is the colour of a siren")
    premise, _ = file_premise(harness, problem, "a siren has a colour")
    critic = premise_rent_sweep(harness, _Variator().bind(harness))[0]

    # Already on record, and the second reading is not re-sampled either.
    assert premise_rent_sweep(harness, _Variator().bind(harness)) == []

    attack(harness, critic.id, "sirens are individuated by their housing")

    assert harness.state.status[premise.id] == Status.ACCEPTED
    assert premise_orphaned(harness) == {}


def test_a_prose_premise_that_is_load_bearing_survives(harness):
    """M21 -- the second reading, and the reason it exists.

    `crit` cannot tell a vacuous prose premise from a contentful one nobody has
    formalised: both declare only the rent battery. `load` can.
    """
    problem = _problem(harness, "why does the kettle whistle")
    premise, _ = file_premise(harness, problem, "the whistle is driven by steam")

    critics = premise_rent_sweep(
        harness, _Variator(("driven by resonance",), differs=True).bind(harness)
    )

    assert critics == []
    assert harness.state.status[premise.id] == Status.ACCEPTED
    assert premise_orphaned(harness) == {}
    undecided = [
        event
        for event in harness.log.read()
        if event.inputs[:1] == ["premise.rent-undecided.v1"]
    ]
    assert [event.inputs[2] for event in undecided] == ["load-bearing"]


def test_without_a_variator_nothing_falls_and_the_record_says_why(harness):
    """M21 -- 'we could not check' must never look like 'we checked'.

    A run with no variator seat cannot take the second reading, so it fells
    nothing and records the abstention against the premise it could not decide.
    """
    problem = _problem(harness, "what is the colour of a siren")
    premise, _ = file_premise(harness, problem, _SIREN_PREMISE)

    assert premise_rent_sweep(harness) == []
    assert harness.state.status[premise.id] == Status.ACCEPTED
    assert premise_orphaned(harness) == {}

    undecided = [
        event
        for event in harness.log.read()
        if event.inputs[:1] == ["premise.rent-undecided.v1"]
    ]
    assert [event.inputs[1:] for event in undecided] == [[premise.id, "no-variator"]]


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


def _refute(harness, problem, label):
    candidate = _addressed(harness, problem, f"answer {label}")
    attack(harness, candidate.id, f"refutation {label}")
    return candidate


def test_a_late_refutation_reopens_the_invitation(harness):
    """The ladder (P11 answer 1). The latch is the wound, not the threshold:
    the technique run established at seq 779 that its own question was
    malformed, 593 events after the only channel for saying so had closed
    (experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md section F-B).

    A criticism that arrives late must still find the channel open, and the
    price of re-opening it is another `after` refutations -- not nothing.
    """
    problem = _problem(harness, "why does the kettle whistle")
    for i in range(2):
        _refute(harness, problem, i)
    assert premise_work_invited(harness, problem, after=2)

    premise = art(harness, "a kettle is the kind of thing that whistles")
    _attribution(harness, problem, premise.id)
    assert not premise_work_invited(harness, problem, after=2)

    # One further refutation does not buy the next rung: the ladder charges
    # `after` for every invitation, so a single late failure cannot re-ask.
    _refute(harness, problem, 2)
    assert not premise_work_invited(harness, problem, after=2)

    # The second one does. This is the case the record needed and never got.
    _refute(harness, problem, 3)
    assert premise_work_invited(harness, problem, after=2)


def test_the_ladder_charges_the_same_rung_for_every_re_invitation(harness):
    """Bounded at `floor(refuted / after)` invitations per problem, so the
    channel's cost is bought by refutations the run had to produce anyway."""
    problem = _problem(harness, "why does the kettle whistle")
    for i in range(6):
        _refute(harness, problem, i)

    for standing in range(3):
        assert premise_work_invited(harness, problem, after=2), standing
        premise = art(harness, f"a kettle presupposes {standing}")
        _attribution(harness, problem, premise.id)

    # Six refutations bought three invitations and no more.
    assert not premise_work_invited(harness, problem, after=2)


def test_refuting_an_attribution_lowers_the_rung(harness):
    """N1, unchanged by the ladder: attacking the attribution ("the problem
    never assumed that") releases the rung it occupied, because
    `standing_attributions` counts only unrefuted ones."""
    problem = _problem(harness, "why does the kettle whistle")
    for i in range(2):
        _refute(harness, problem, i)
    premise = art(harness, "a kettle is the kind of thing that whistles")
    attribution = _attribution(harness, problem, premise.id)
    assert not premise_work_invited(harness, problem, after=2)

    attack(harness, attribution.id, "the problem never assumed that")
    assert premise_work_invited(harness, problem, after=2)


def test_the_ladder_is_the_shipped_rule_when_no_attribution_stands(harness):
    """The change is a strict extension: with zero standing attributions the
    ladder reduces to `refuted >= after`, so no run that never filed a premise
    sees any difference at all."""
    problem = _problem(harness, "why does the kettle whistle")
    assert not premise_work_invited(harness, problem, after=2)
    _refute(harness, problem, 0)
    assert not premise_work_invited(harness, problem, after=2)
    _refute(harness, problem, 1)
    assert premise_work_invited(harness, problem, after=2)
    assert standing_attributions(harness) == []
