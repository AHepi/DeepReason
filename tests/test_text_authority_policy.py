"""Prospective text authority is advisory by default; mechanics stay live."""

import json
from types import SimpleNamespace

import pytest

from deepreason.authority import AuthoritySurface, TrialAuthority, trial_authority_for
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.informal.standards import register_standard
from deepreason.informal.trial import (
    pairwise_discriminate,
    run_argument_trial_from_case,
    run_trial,
)
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
)
from deepreason.oracle import property_oracle_commitment
from deepreason.ops import review_infrastructure
from deepreason.rules.crit import crit_argumentative, crit_program
from deepreason.runtime.progress import ProgressSink
from deepreason.scheduler.scheduler import Scheduler
from deepreason.status_display import display_status, display_status_counts
from deepreason.ui.terminal import render_terminal_status


CASE = "parallel fifths in bar 3 violate clause 2"
DEFENCE = "the fifths are an intentional echo"
CRITIC = json.dumps({"attack": True, "case": CASE})
DEFENDER = json.dumps({"answer": DEFENCE})
FAIL = json.dumps({"verdict": "fail", "decisive_point": "parallel fifths in bar 3"})


def _rubric_target(harness):
    standard = register_standard(
        harness, "std-authority", "clause 2: no parallel fifths", mode="absolute"
    )
    commitment = Commitment(id="rubric-authority", eval="rubric:std-authority")
    harness.register_commitment(commitment)
    target = harness.create_artifact(
        "a chorale has parallel fifths in bar 3",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer"),
    )
    return target, commitment, standard


def _rubric_adapter(harness):
    return LLMAdapter(
        {
            "argumentative_critic": MockEndpoint([CRITIC]),
            "defender": MockEndpoint([DEFENDER]),
            "judge": [
                MockEndpoint([FAIL], name="mock://judge-gemma", model="gemma-test"),
                MockEndpoint([FAIL], name="mock://judge-qwen", model="qwen-test"),
            ],
        },
        harness.blobs,
        retry_max=2,
    )


def _content(harness, artifact):
    if artifact.content_ref.startswith("inline:"):
        return artifact.content_ref.removeprefix("inline:")
    return harness.blobs.get(artifact.content_ref).decode("utf-8")


def _pairwise_problem(harness):
    first = harness.create_artifact(
        "rival A: differential pull explains the tides",
        provenance=Provenance(role="conjecturer"),
    )
    second = harness.create_artifact(
        "rival B: solar heating explains the tides",
        provenance=Provenance(role="conjecturer"),
    )
    problem = harness.register_problem(
        Problem(
            id="disc:authority",
            description="discriminate rivals",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "discrimination", "from": ["pi", first.id, second.id]}
            ),
        )
    )
    return problem, first, second


def test_default_text_policy_keeps_prose_criticism_as_scrutiny(tmp_path):
    harness = Harness(tmp_path / "run")
    target = harness.create_artifact(
        "a speculative causal account",
        provenance=Provenance(role="conjecturer"),
    )
    adapter = LLMAdapter(
        {"argumentative_critic": MockEndpoint([json.dumps({"attack": True, "case": "missing mechanism"})])},
        harness.blobs,
        retry_max=2,
    )

    critic = crit_argumentative(harness, target.id, adapter, Config())

    assert critic is not None
    assert harness.state.status[target.id] == Status.ACCEPTED
    assert not harness.warrants
    assert not harness.state.att
    assert any(event.inputs[:2] == ["scrutiny", target.id] for event in harness.log.read())


def test_missing_direct_prose_authority_is_observe_only(tmp_path):
    harness = Harness(tmp_path / "run")
    target = harness.create_artifact(
        "a speculative causal account",
        provenance=Provenance(role="conjecturer"),
    )
    adapter = LLMAdapter(
        {
            "argumentative_critic": MockEndpoint(
                [json.dumps({"attack": True, "case": "missing mechanism"})]
            )
        },
        harness.blobs,
        retry_max=2,
    )
    values = Config().model_dump()
    values.pop("ARGUMENTATIVE_AUTHORITY")

    critic = crit_argumentative(harness, target.id, adapter, SimpleNamespace(**values))

    assert critic is not None
    assert harness.state.status[target.id] == Status.ACCEPTED
    assert not harness.warrants
    assert not harness.state.att


def test_default_policy_keeps_infrastructure_review_as_scrutiny(harness):
    standard = register_standard(
        harness, "std-infrastructure", "clause: state concrete assumptions"
    )
    adapter = LLMAdapter(
        {"argumentative_critic": MockEndpoint([CRITIC])},
        harness.blobs,
        retry_max=2,
    )

    critic = review_infrastructure(harness, adapter, Config(), standard.id)

    assert critic is not None
    assert harness.state.status[standard.id] == Status.ACCEPTED
    assert not harness.warrants
    assert not harness.state.att
    assert any(event.inputs[:2] == ["scrutiny", standard.id] for event in harness.log.read())


def test_unverified_calibrated_infrastructure_review_is_observe_only(harness):
    standard = register_standard(
        harness, "std-infrastructure-unverified", "clause: state concrete assumptions"
    )
    adapter = LLMAdapter(
        {"argumentative_critic": MockEndpoint([CRITIC])},
        harness.blobs,
        retry_max=2,
    )
    config = Config(
        INFRASTRUCTURE_REVIEW_AUTHORITY="calibrated_status",
        CALIBRATION_RECEIPT="sha256:arbitrary-unverified-reference",
    )

    critic = review_infrastructure(harness, adapter, config, standard.id)

    assert critic is not None
    assert harness.state.status[standard.id] == Status.ACCEPTED
    assert not harness.warrants
    assert not harness.state.att


def test_default_text_policy_routes_rubric_trial_to_advisory(harness):
    target, commitment, _ = _rubric_target(harness)
    observation = run_trial(
        harness,
        target.id,
        commitment,
        _rubric_adapter(harness),
        Config(TRIAL_PARAPHRASE_N=0),
    )

    assert trial_authority_for(Config(), "text", AuthoritySurface.RUBRIC) == TrialAuthority.OBSERVE_ONLY
    assert observation is not None
    assert harness.state.status[target.id] == Status.ACCEPTED
    assert not harness.warrants
    assert not harness.state.att
    payload = json.loads(_content(harness, observation))
    record = payload["trial_observation"]
    assert record["case"] == CASE
    assert record["answer"] == DEFENCE
    assert record["outcome"] == "sustained"
    assert any(event.inputs[:2] == ["trial-observation", target.id] for event in harness.log.read())


def test_default_text_scheduler_spends_no_rubric_trial_tokens_without_advisory_budget(harness):
    target, _, _ = _rubric_target(harness)
    # An empty judge queue makes an accidental trial call immediately visible.
    adapter = LLMAdapter({"judge": MockEndpoint([])}, harness.blobs, retry_max=2)
    scheduler = Scheduler(
        harness,
        adapter,
        Config(N_SCHOOLS=0),
        workload_profile="text",
    )

    scheduler._criticize(target)

    assert harness.state.status[target.id] == Status.ACCEPTED
    assert not harness.warrants
    assert not [event for event in harness.log.read() if event.llm]


def test_default_text_policy_routes_pairwise_to_advisory(harness):
    problem, first, second = _pairwise_problem(harness)
    adapter = LLMAdapter(
        {
            "judge": MockEndpoint(
                [
                    json.dumps({"winner": "A", "decisive_point": "differential pull"}),
                    json.dumps({"winner": "B", "decisive_point": "differential pull"}),
                ]
            )
        },
        harness.blobs,
        retry_max=2,
    )
    observation = pairwise_discriminate(
        harness,
        problem,
        first.id,
        second.id,
        adapter,
        Config(),
    )

    assert trial_authority_for(Config(), "text", AuthoritySurface.PAIRWISE) == TrialAuthority.OBSERVE_ONLY
    assert observation is not None
    assert harness.state.status[first.id] == Status.ACCEPTED
    assert harness.state.status[second.id] == Status.ACCEPTED
    assert not harness.warrants
    assert not harness.state.att
    record = json.loads(_content(harness, observation))["pairwise_observation"]
    assert record["winner"] == first.id
    assert record["loser"] == second.id
    assert record["order_swap"] == "pass"


def test_default_text_scheduler_records_pairwise_observation_without_warrant(harness):
    problem, first, second = _pairwise_problem(harness)
    adapter = LLMAdapter(
        {
            "judge": MockEndpoint(
                [
                    json.dumps({"winner": "A", "decisive_point": "differential pull"}),
                    json.dumps({"winner": "B", "decisive_point": "differential pull"}),
                ]
            )
        },
        harness.blobs,
        retry_max=2,
    )
    scheduler = Scheduler(
        harness,
        adapter,
        Config(N_SCHOOLS=0, ADVISORY_TRIALS_PER_CYCLE=1),
        workload_profile="text",
    )

    scheduler.step()

    assert problem.id in harness.state.problems
    assert harness.state.status[first.id] == Status.ACCEPTED
    assert harness.state.status[second.id] == Status.ACCEPTED
    assert not harness.warrants
    assert any(
        event.inputs[:2] == ["pairwise-observation", problem.id]
        for event in harness.log.read()
    )


def test_default_text_scheduler_spends_no_pairwise_judge_tokens(harness):
    _pairwise_problem(harness)
    adapter = LLMAdapter({"judge": MockEndpoint([])}, harness.blobs, retry_max=2)
    scheduler = Scheduler(
        harness,
        adapter,
        Config(N_SCHOOLS=0),
        workload_profile="text",
    )

    scheduler.step()

    assert not [event for event in harness.log.read() if event.llm]
    assert not any(event.inputs[:1] == ["pairwise-observation"] for event in harness.log.read())


def test_execution_authority_survives_default_text_policy(harness):
    checker = (
        "def check(inp, out):\n"
        "    xs = inp[0]\n"
        "    return isinstance(out, list) and sorted(xs) == out\n"
    )
    gate = (
        "def valid(inp):\n"
        "    return isinstance(inp, list) and len(inp) == 1 and isinstance(inp[0], list)\n"
    )
    commitment = property_oracle_commitment("solve", [[[2, 1]]], checker, gate)
    harness.register_commitment(commitment)
    target = harness.create_artifact(
        "def solve(xs):\n    return xs\n",
        codec="code:python",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer"),
    )

    crit_program(harness, target.id)

    assert harness.state.status[target.id] == Status.REFUTED
    assert harness.warrants


def test_default_precomputed_argument_trial_is_advisory(harness):
    target = harness.create_artifact(
        "a speculative causal account", provenance=Provenance(role="conjecturer")
    )

    observation = run_argument_trial_from_case(
        harness, None, Config(), target.id, "missing mechanism"
    )

    assert observation is not None
    assert harness.state.status[target.id] == Status.ACCEPTED
    assert not harness.warrants
    assert not harness.state.att


def test_legacy_trial_authority_is_rejected_before_provider_use(harness):
    target, commitment, _ = _rubric_target(harness)
    adapter = _rubric_adapter(harness)

    with pytest.raises(ValueError, match="legacy_status"):
        run_trial(
            harness,
            target.id,
            commitment,
            adapter,
            Config(TRIAL_PARAPHRASE_N=0),
            authority="legacy_status",
        )

    assert harness.state.status[target.id] == Status.ACCEPTED
    assert not [event for event in harness.log.read() if event.llm]


def test_text_display_says_standing_without_mutating_internal_status(harness):
    artifact = harness.create_artifact("a still-live text claim")

    assert harness.state.status[artifact.id] == Status.ACCEPTED
    assert display_status(Status.ACCEPTED, "text") == "standing"
    assert display_status(Status.ACCEPTED, "formal") == "accepted"
    counts = display_status_counts(harness, workload_profile="text")
    assert counts == {"standing": 1}
    progress = ProgressSink(harness.root, run_id="text-status", workload="text")
    event = progress.emit(
        state="running",
        phase="reasoning",
        activity="cycle complete",
        display_status_counts=counts,
    )
    assert event.display_status_counts == {"standing": 1}
    assert "standing:1" in render_terminal_status(event.model_dump(mode="json"))


def test_scheduler_progress_uses_text_display_statuses(harness):
    harness.create_artifact("a still-live text claim")
    progress = ProgressSink(harness.root, run_id="scheduler-text", workload="text")
    scheduler = Scheduler(
        harness,
        LLMAdapter({}, harness.blobs, retry_max=2),
        Config(N_SCHOOLS=0),
        workload_profile="text",
        progress_sink=progress,
    )

    scheduler._emit_progress(
        SimpleNamespace(cycle=1, pending_deterministic_checks=0), None
    )

    assert progress.read_since(-1)[-1].display_status_counts == {"standing": 1}
