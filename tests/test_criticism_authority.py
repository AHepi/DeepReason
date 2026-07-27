"""Criticism authority (bronze postrun repair, RC1/RC6): a prose objection
must not certify its own soundness. observe_only records scrutiny evidence
with no status change; trial_required mints an argumentative warrant only
through the defended cross-family court; execution counterexamples stay
status-changing under every mode; infrastructure is excluded from ordinary
standing criticism."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.informal.standards import register_standard
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Interface,
    Provenance,
    Status,
    WarrantType,
)
from deepreason.oracle import property_oracle_commitment
from deepreason.rules.crit import crit_argumentative, crit_argumentative_batch
from deepreason.scheduler.scheduler import Scheduler
from tests.conftest import art


def _batch(*cases) -> str:
    return json.dumps({"cases": list(cases)})


def test_observe_only_no_status_change(harness):
    """A batch-critic attack (the bronze-run kill shape) creates scrutiny
    records but leaves every target status unchanged: no warrant, no attack
    edge, and the shared call is accounted exactly once."""
    targets = [
        harness.create_artifact(
            f"conjecture {i}: mechanism variant {i}",
            provenance=Provenance(role="conjecturer"),
        )
        for i in range(3)
    ]
    adapter = LLMAdapter(
        {
            "argumentative_critic": MockEndpoint(
                [
                    _batch(
                        *[
                            {
                                "target": target.id,
                                "attack": True,
                                "case": f"objection to variant {index}",
                            }
                            for index, target in enumerate(targets)
                        ]
                    )
                ]
            )
        },
        harness.blobs,
        retry_max=2,
    )
    critics = crit_argumentative_batch(
        harness, [t.id for t in targets], adapter, Config()
    )
    assert len(critics) == 3
    for target in targets:
        assert harness.state.status[target.id] == Status.ACCEPTED
    assert not harness.warrants  # no attack edge of any kind
    for critic in critics:
        assert not harness.carried_warrant_ids(critic.id)
    scrutiny = [
        event for event in harness.log.read() if event.inputs[:1] == ["scrutiny"]
    ]
    assert {event.inputs[1] for event in scrutiny} == {t.id for t in targets}
    assert all(event.inputs[2] in harness.state.artifacts for event in scrutiny)
    assert sum(event.llm is not None for event in harness.log.read()) == 1


CASE = "the passage uses parallel fifths in bar 3, violating clause 2"
DEFENCE = "the fifths are an intentional echo of the cantus firmus"
CRITIC = json.dumps({"attack": True, "case": CASE})
DEFENDER = json.dumps({"answer": DEFENCE})
FAIL_RULING = json.dumps(
    {"verdict": "fail", "decisive_point": "parallel fifths in bar 3"}
)
PASS_RULING = json.dumps({"verdict": "pass", "decisive_point": "intentional echo"})
PARAPHRASES = json.dumps(
    {"edits": [{"content": "fifths move in parallel at bar 3; clause 2 forbids it"},
               {"content": "bar 3 contains consecutive fifths, contra clause 2"}]}
)


def _court(harness, judge1, judge2, *, with_defender=True, meter=None):
    endpoints = {
        "argumentative_critic": MockEndpoint([CRITIC]),
        "judge": [
            MockEndpoint(judge1, name="mock://judge-gemma", model="gemma-test"),
            MockEndpoint(judge2, name="mock://judge-qwen", model="qwen-test"),
        ],
        "variator": MockEndpoint([PARAPHRASES]),
    }
    if with_defender:
        endpoints["defender"] = MockEndpoint([DEFENDER])
    return LLMAdapter(endpoints, harness.blobs, retry_max=2, meter=meter)


def test_trial_required_needs_court(harness):
    """No warrant until the defender answers, every judge seat finishes, and
    the guard accepts the ruling; every non-sustained path is a logged
    trial-declined Measure with the target status unchanged."""
    config = Config(ARGUMENTATIVE_AUTHORITY="trial_required", TRIAL_PARAPHRASE_N=2)
    target = art(
        harness,
        "a chorale passage with parallel fifths in bar 3",
        provenance=Provenance(role="conjecturer"),
    )
    # 1. No defender role: the case cannot become a warrant.
    adapter = _court(harness, [FAIL_RULING], [FAIL_RULING], with_defender=False)
    assert crit_argumentative(harness, target.id, adapter, config) is None
    assert harness.state.status[target.id] == Status.ACCEPTED
    declines = [e for e in harness.log.read() if e.inputs[:1] == ["trial-declined"]]
    assert declines[-1].inputs == ["trial-declined", target.id, "no-defender-role"]
    # 2. Ensemble split: seats disagree, no warrant.
    adapter = _court(harness, [FAIL_RULING], [PASS_RULING])
    assert crit_argumentative(harness, target.id, adapter, config) is None
    assert harness.state.status[target.id] == Status.ACCEPTED
    declines = [e for e in harness.log.read() if e.inputs[:1] == ["trial-declined"]]
    assert declines[-1].inputs == ["trial-declined", target.id, "ensemble-split"]
    assert not any(w.target == target.id for w in harness.warrants.values())
    # 3. The full court sustains through every guard: the warrant mints.
    meter = TokenMeter()
    llm_before = sum(event.llm is not None for event in harness.log.read())
    adapter = _court(harness, [FAIL_RULING] * 3, [FAIL_RULING] * 3, meter=meter)
    critic = crit_argumentative(harness, target.id, adapter, config)
    assert critic is not None
    assert harness.state.status[target.id] == Status.REFUTED
    warrant = next(w for w in harness.warrants.values() if w.target == target.id)
    assert warrant.type == WarrantType.ARGUMENTATIVE
    transcript = json.loads(harness.blobs.get(warrant.trace_ref))
    assert transcript["case"] == CASE and transcript["answer"] == DEFENCE
    assert transcript["checks"]["paraphrase"] == {"n": 2, "flips": 0}
    # Complete call accounting: critic + defender + 6 rulings + variator all
    # reach the log exactly once (decisive ruling on the critic event, the
    # rest as trial-llm Measures).
    llm_after = sum(event.llm is not None for event in harness.log.read())
    assert meter.calls == llm_after - llm_before == 9


def test_infrastructure_not_in_standing_pool(tmp_path):
    """RC6: standards and stance seeds never enter the ordinary standing
    argumentative pool; ops.review_infrastructure is their only attack path."""
    harness = Harness(tmp_path / "run")
    standard = register_standard(
        harness, "std-house", "clause 1: no unfalsifiable prose"
    )
    stance = harness.create_artifact(
        "stance seed: prefer mechanistic explanations",
        provenance=Provenance(role="seed"),
    )
    survivor = harness.create_artifact(
        "a standing moon conjecture nobody attacked",
        provenance=Provenance(role="conjecturer"),
    )
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(['{"candidates": []}'])},
        harness.blobs,
        retry_max=2,
    )
    scheduler = Scheduler(harness, adapter, Config(N_SCHOOLS=0))
    pool = scheduler._standing_recrit_pool()
    assert survivor.id in pool
    assert standard.id not in pool
    assert stance.id not in pool


CHECKER = (
    "def check(inp, out):\n"
    "    xs = inp[0]\n"
    "    return isinstance(out, list) and sorted(xs) == out\n"
)
GATE = (
    "def valid(inp):\n"
    "    if not isinstance(inp, list) or len(inp) != 1:\n"
    "        return False\n"
    "    xs = inp[0]\n"
    "    if not isinstance(xs, list) or len(xs) > 20:\n"
    "        return False\n"
    "    return all(isinstance(x, int) for x in xs)\n"
)
SORT_INPUTS = [[[3, 1, 2]]]
SNEAKY_SORT = (
    "def solve(xs):\n"
    "    if len(xs) > 2:\n"
    "        return sorted(xs)\n"
    "    return xs\n"
)


def test_execution_counterexample_still_refutes_under_observe_only(harness):
    """Demonstrative outcomes are exempt from the authority gate: a critic
    counterexample that RUNS and violates the property refutes by execution
    even in observe_only mode."""
    commitment = property_oracle_commitment("solve", SORT_INPUTS, CHECKER, GATE)
    harness.register_commitment(commitment)
    sneaky = harness.create_artifact(
        SNEAKY_SORT,
        codec="code:python",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer"),
    )
    adapter = LLMAdapter(
        {
            "argumentative_critic": MockEndpoint(
                [json.dumps({"attack": True, "case": "fails on short lists",
                             "counterexample": [[2, 1]]})]
            )
        },
        harness.blobs,
        retry_max=2,
    )
    critic = crit_argumentative(
        harness, sneaky.id, adapter, Config(ARGUMENTATIVE_AUTHORITY="observe_only")
    )
    assert critic is not None
    assert harness.state.status[sneaky.id] == Status.REFUTED
    warrant = next(w for w in harness.warrants.values() if w.target == sneaky.id)
    assert warrant.type == WarrantType.DEMONSTRATIVE  # a run verdict, not prose
