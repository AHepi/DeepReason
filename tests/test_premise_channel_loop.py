"""The premise channel WIRED: the producer fires in the real loop.

Regression (v2 calculus program, Rung 2 step 2). `tests/test_premise_channel.py`
proves the channel's shape; this file proves something the shape cannot —
that a run reaches it. Two mechanisms have shipped in this harness that no
producer ever triggered (the controller that never steered, the reach trigger
that never fired; docs/ERRATA.md E28), so the test that matters here drives
`Scheduler.step` and reads the record afterwards.
"""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Status,
)
from deepreason.premises import (
    PREMISE_REFUTED,
    RESOLUTION_EVAL,
    premise_orphaned,
    resolution_content,
    standing_attributions,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.signals import declaration

_PREMISE = "a siren is the kind of thing that has a colour"

_DETECTION_SIGNALS = (
    "problem.thrash.v1",
    "criticism.attack-target-entropy.v1",
    "problem.independence-resolution-rate.v1",
)


def _problem(harness, pid: str, *, criteria=()):
    return harness.register_problem(
        Problem(
            id=pid,
            description=pid.replace("-", " "),
            criteria=list(criteria),
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def _flat_variator(prompt: str) -> str:
    """A variator whose edits are the target reworded into itself.

    Under ≈_B a rename is the same explanation, so `mod` is False and the
    second demarcation reading agrees with the first — which is the case where
    a prose premise is allowed to fall.
    """
    text = prompt.split("TARGET CONTENT:\n", 1)[1].split("\n\n", 1)[0]
    return json.dumps({"edits": [{"content": text}]})


def _distinct_variator(prompt: str) -> str:
    """Edits that say something different: `mod` holds, so the premise stands
    however bare its interface is."""
    return json.dumps({"edits": [{"content": "a siren is individuated by its housing"}]})


_ANSWERS = ("the colour is red", "it is loud", "it is shrill")
_ANSWERS_ALL_PASSING = ("the colour is red", "the colour is grey")


def _siren_run(
    tmp_path, critic_responses, answers=_ANSWERS, variator=_flat_variator, **config_kwargs
):
    """A run whose problem refutes most of what is offered for it.

    The criterion is deterministic, so the refutations that arm the producer
    come from the harness rather than from a hand-written attack. Selection is
    pinned to the seed problem: successor problems minted from the refutations
    would otherwise out-age it, and what is under test here is the producer,
    not the rotation (which `test_a_marked_problem_yields_to_unmarked_work`
    covers separately).
    """
    harness = Harness(tmp_path / "run")
    harness.register_commitment(
        Commitment(id="k-colour", eval="predicate:'colour' in content")
    )
    _problem(harness, "colour-of-a-siren", criteria=["k-colour"])
    conjectures = json.dumps(
        {
            "candidates": [
                {"content": text, "typicality": 0.9 - 0.1 * index}
                for index, text in enumerate(answers)
            ]
        }
    )
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint([conjectures] * 4),
            "argumentative_critic": MockEndpoint(critic_responses),
            # The second demarcation reading (§6 mod) needs the variator seat.
            "variator": MockEndpoint(variator),
        },
        harness.blobs,
        retry_max=2,
    )
    config = Config(
        VS_K=3,
        N_SCHOOLS=0,
        FUZZ_N=0,
        FOCUS_PROBLEM="colour-of-a-siren",
        **config_kwargs,
    )
    return harness, Scheduler(harness, adapter, config)


def _measures(harness, signal: str):
    return [
        event
        for event in harness.log.read()
        if event.rule.value == "Measure" and event.inputs[:1] == [signal]
    ]


def test_the_producer_fires_in_the_real_loop(tmp_path):
    """A15/M16 — nothing in this test attacks anything by hand.

    The problem's own criterion fells the candidates that do not answer it;
    that arms the invitation; the invitation reaches the critic's pack; the
    critic names the presupposition; the rent battery refutes it because it
    forbids nothing; the problem is marked. Every step is the loop's.
    """
    harness, scheduler = _siren_run(
        tmp_path,
        [
            json.dumps({"attack": False, "case": ""}),
            json.dumps({"attack": False, "case": "", "premise": _PREMISE}),
        ],
    )

    scheduler.step()
    assert not _measures(harness, "premise.work-invited.v1")  # not yet armed

    scheduler.step()

    invited = _measures(harness, "premise.work-invited.v1")
    assert [event.inputs[1] for event in invited] == ["colour-of-a-siren"]

    filed = _measures(harness, "premise.attribution-filed.v1")
    assert len(filed) == 1 and filed[0].inputs[1] == "colour-of-a-siren"

    attributions = standing_attributions(harness)
    assert len(attributions) == 1
    _, problem_id, premise_id = attributions[0]
    assert problem_id == "colour-of-a-siren"
    # Refuted by DEMARCATION, on the sweep, with no written refutation.
    assert harness.state.status[premise_id] == Status.REFUTED
    assert premise_orphaned(harness) == {"colour-of-a-siren": PREMISE_REFUTED}


def test_the_invitation_reaches_the_critics_pack(tmp_path):
    """The invitation is a pack section, so the model can actually see it."""
    seen: list[str] = []

    def critic(prompt: str) -> str:
        seen.append(prompt)
        return json.dumps({"attack": False, "case": ""})

    harness, scheduler = _siren_run(tmp_path, critic)
    scheduler.step()
    scheduler.step()

    assert seen and any("PREMISE INVITATION" in prompt for prompt in seen)
    assert "costs you nothing" in [p for p in seen if "PREMISE INVITATION" in p][0]


def test_an_uninvited_premise_registers_nothing(tmp_path):
    """A18/C5 — the producer offers the work; a field filled in unasked is not
    an offer the run made, and honouring it would let a call file work no
    producer ever authorised."""
    harness, scheduler = _siren_run(
        tmp_path,
        lambda prompt: json.dumps(
            {"attack": False, "case": "", "premise": _PREMISE}
        ),
        answers=_ANSWERS_ALL_PASSING,
    )

    scheduler.step()  # every candidate answers the problem: nothing is refuted
    scheduler.step()

    assert not _measures(harness, "premise.work-invited.v1")
    assert not _measures(harness, "premise.attribution-filed.v1")
    assert standing_attributions(harness) == []


def test_the_three_detection_signals_are_emitted_and_declared(tmp_path):
    """A17/M14 — emitted by the real loop, and every one carries a real unit
    and a real staleness bound; `unspecified` is not available to a new
    signal."""
    harness, scheduler = _siren_run(
        tmp_path, [json.dumps({"attack": False, "case": ""})] * 2
    )
    scheduler.step()

    for signal in _DETECTION_SIGNALS:
        events = _measures(harness, signal)
        assert len(events) == 1, signal
        float(events[0].inputs[1])  # a parseable ratio, not a label
        contract = declaration(signal)
        assert contract is not None, signal
        assert contract.unit != "unspecified", signal
        assert contract.staleness != "unspecified", signal


def test_a_prose_premise_with_a_variation_surface_survives_the_loop(tmp_path):
    """M21 in the real loop — the second check is what stops the rent battery
    from felling every premise a critic ever files."""
    harness, scheduler = _siren_run(
        tmp_path,
        [
            json.dumps({"attack": False, "case": ""}),
            json.dumps({"attack": False, "case": "", "premise": _PREMISE}),
        ],
        variator=_distinct_variator,
    )
    scheduler.step()
    scheduler.step()

    attributions = standing_attributions(harness)
    assert len(attributions) == 1
    _, _, premise_id = attributions[0]
    assert harness.state.status[premise_id] == Status.ACCEPTED
    assert premise_orphaned(harness) == {}
    assert [
        event.inputs[2]
        for event in _measures(harness, "premise.rent-undecided.v1")
    ] == ["varies"]


def test_a_run_with_no_variator_seat_fells_no_premise(tmp_path):
    """M21 — a solo run holding only the first reading says so, once per
    premise, and leaves the premise standing."""
    harness = Harness(tmp_path / "run")
    harness.register_commitment(
        Commitment(id="k-colour", eval="predicate:'colour' in content")
    )
    _problem(harness, "colour-of-a-siren", criteria=["k-colour"])
    conjectures = json.dumps(
        {"candidates": [{"content": t, "typicality": 0.9} for t in _ANSWERS]}
    )
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint([conjectures] * 4),
            "argumentative_critic": MockEndpoint(
                [
                    json.dumps({"attack": False, "case": ""}),
                    json.dumps({"attack": False, "case": "", "premise": _PREMISE}),
                ]
            ),
        },
        harness.blobs,
        retry_max=2,
    )
    scheduler = Scheduler(
        harness,
        adapter,
        Config(VS_K=3, N_SCHOOLS=0, FUZZ_N=0, FOCUS_PROBLEM="colour-of-a-siren"),
    )
    scheduler.step()
    scheduler.step()

    _, _, premise_id = standing_attributions(harness)[0]
    assert harness.state.status[premise_id] == Status.ACCEPTED
    assert premise_orphaned(harness) == {}
    undecided = _measures(harness, "premise.rent-undecided.v1")
    assert [event.inputs[1:] for event in undecided] == [[premise_id, "no-variator"]]


# --- selection: attention only ---------------------------------------------


@pytest.mark.parametrize("liveness", [True, False])
def test_a_retired_problem_is_not_selected(tmp_path, liveness):
    """M13/M18 — and it is not deleted: attacking the retirement puts it back."""
    from tests.conftest import attack

    harness = Harness(tmp_path / "run")
    _problem(harness, "aaa-retired")
    _problem(harness, "bbb-live")
    cid = "premise-resolution-wf@v1"
    harness.register_commitment(Commitment(id=cid, eval=RESOLUTION_EVAL))
    retirement = harness.create_artifact(
        resolution_content("retire", "aaa-retired"),
        codec="json",
        interface=Interface(commitments=[cid]),
    )
    scheduler = Scheduler(
        harness,
        LLMAdapter({}, harness.blobs),
        Config(N_SCHOOLS=0, LIVENESS_QUEUE=liveness),
    )

    assert scheduler._select_problem().id == "bbb-live"

    attack(harness, retirement.id, "the premise was reinstated")

    assert {p.id for p in harness.state.problems.values()} == {
        "aaa-retired",
        "bbb-live",
    }
    scheduler._problem_worked.clear()
    assert scheduler._select_problem().id == "aaa-retired"  # back on the frontier


@pytest.mark.parametrize("liveness", [True, False])
def test_a_marked_problem_yields_to_unmarked_work(tmp_path, liveness):
    """M13 — attention only. The mark changes no status and deletes nothing;
    it moves the problem behind equally-aged work of the same class."""
    from tests.conftest import art, attack
    from tests.test_premise_channel import _attribution

    harness = Harness(tmp_path / "run")
    _problem(harness, "aaa-marked")
    _problem(harness, "bbb-unmarked")
    scheduler = Scheduler(
        harness,
        LLMAdapter({}, harness.blobs),
        Config(N_SCHOOLS=0, LIVENESS_QUEUE=liveness),
    )

    assert scheduler._select_problem().id == "aaa-marked"  # id tie-break, unmarked

    premise = art(harness, _PREMISE)
    _attribution(harness, "aaa-marked", premise.id)
    attack(harness, premise.id, "sound events bear no colour")
    assert premise_orphaned(harness) == {"aaa-marked": PREMISE_REFUTED}

    scheduler._problem_worked.clear()
    assert scheduler._select_problem().id == "bbb-unmarked"
    assert harness.state.problems["aaa-marked"] is not None  # nothing deleted
