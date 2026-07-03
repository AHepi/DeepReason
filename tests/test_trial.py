"""P5 acceptance (c) (spec §16): a rubric warrant registers only with a
conforming trial transcript; an order-swap inconsistency blocks a pairwise
warrant. Plus: referential integrity, paraphrase flips, ensemble splits."""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness, WellFormednessError
from deepreason.informal.standards import register_standard
from deepreason.informal.trial import pairwise_discriminate, run_trial
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Status,
    Warrant,
    WarrantType,
)
from tests.conftest import art

CASE = "the passage uses parallel fifths in bar 3, violating clause 2"
DEFENCE = "the fifths are an intentional echo of the cantus firmus"
CRITIC = json.dumps({"attack": True, "case": CASE})
DEFENDER = json.dumps({"answer": DEFENCE})
FAIL_RULING = json.dumps({"verdict": "fail", "decisive_point": "parallel fifths in bar 3"})
PASS_RULING = json.dumps({"verdict": "pass", "decisive_point": "intentional echo"})
PARAPHRASES = json.dumps(
    {"edits": [{"content": "fifths move in parallel at bar 3; clause 2 forbids it"},
               {"content": "bar 3 contains consecutive fifths, contra clause 2"}]}
)


def _setup(harness) -> tuple[str, Commitment]:
    register_standard(harness, "std-1", "clause 2: no parallel fifths", mode="absolute")
    kappa = Commitment(id="kappa-taste", eval="rubric:std-1")
    harness.register_commitment(kappa)
    target = art(harness, "a chorale passage with parallel fifths in bar 3",
                 interface=Interface(commitments=["kappa-taste"]))
    return target.id, kappa


def _adapter(harness, judge_responses, *, judge2=None, with_variator=True):
    endpoints = {
        "argumentative_critic": MockEndpoint([CRITIC]),
        "defender": MockEndpoint([DEFENDER]),
        "judge": (
            [MockEndpoint(judge_responses), MockEndpoint(judge2)]
            if judge2 is not None
            else MockEndpoint(judge_responses)
        ),
    }
    if with_variator:
        endpoints["variator"] = MockEndpoint([PARAPHRASES])
    return LLMAdapter(endpoints, harness.blobs, retry_max=2)


def test_surviving_trial_packages_rubric_warrant(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    target_id, kappa = _setup(harness)
    config = Config(TRIAL_PARAPHRASE_N=2)
    # judge: initial ruling + 2 paraphrase re-rulings, all fail.
    adapter = _adapter(harness, [FAIL_RULING, FAIL_RULING, FAIL_RULING])
    critic = run_trial(harness, target_id, kappa, adapter, config)
    assert critic is not None
    assert harness.state.status[target_id] == Status.REFUTED
    warrant = next(w for w in harness.warrants.values() if w.target == target_id)
    transcript = json.loads(harness.blobs.get(warrant.trace_ref))
    assert transcript["case"] == CASE and transcript["answer"] == DEFENCE
    assert transcript["checks"]["paraphrase"] == {"n": 2, "flips": 0}
    # nu mentions the standard: the case-law closure is armed (§1).
    nu = harness.state.artifacts[warrant.validity_node]
    assert any(r.role.value == "mention" for r in nu.interface.refs)
    assert Harness(root).state.model_dump_json() == harness.state.model_dump_json()


def test_rubric_warrant_without_transcript_rejected(harness):
    """Acceptance (c): the guard is unbypassable — a directly constructed
    rubric warrant without a conforming transcript violates §2."""
    _setup(harness)
    target = art(harness, "another passage")
    nu = art(harness, "nu: a bare assertion of soundness")
    bogus = Warrant(
        id="w-bogus", target=target.id, type=WarrantType.DEMONSTRATIVE,
        commitment="kappa-taste", verdict="fail",
        trace_ref="inline:not-a-transcript", validity_node=nu.id,
    )
    with pytest.raises(WellFormednessError):
        harness.create_artifact(
            "critic: bogus rubric fail", provenance=Provenance(role="critic"),
            warrants=[bogus],
        )


def test_referential_integrity_blocks_unresolvable_ruling(harness):
    target_id, kappa = _setup(harness)
    bad = json.dumps({"verdict": "fail", "decisive_point": "a point nobody made"})
    adapter = _adapter(harness, [bad])
    assert run_trial(harness, target_id, kappa, adapter, Config()) is None
    assert harness.state.status[target_id] == Status.ACCEPTED  # no warrant
    blocks = [e for e in harness.log.read()
              if any(t == "trial-blocked:referential-integrity" for t in e.inputs)]
    assert blocks  # blocked rulings are logged, never registered


def test_paraphrase_flip_blocks_warrant(harness):
    target_id, kappa = _setup(harness)
    adapter = _adapter(harness, [FAIL_RULING, FAIL_RULING, PASS_RULING])
    assert run_trial(harness, target_id, kappa, adapter, Config(TRIAL_PARAPHRASE_N=2)) is None
    assert harness.state.status[target_id] == Status.ACCEPTED


def test_ensemble_split_blocks_and_logs(harness):
    target_id, kappa = _setup(harness)
    adapter = _adapter(harness, [FAIL_RULING], judge2=[PASS_RULING])
    assert adapter.ensemble_size("judge") == 2
    assert run_trial(harness, target_id, kappa, adapter, Config()) is None
    blocks = [e for e in harness.log.read()
              if any(t == "trial-blocked:ensemble-split" for t in e.inputs)]
    assert blocks  # disagreement is a signal, never averaged away (§10.4)


def _pairwise_setup(harness):
    a = art(harness, "rival A: the moon's differential pull explains both tides")
    b = art(harness, "rival B: solar heating explains the tides")
    problem = harness.register_problem(
        Problem(
            id="disc:pi-tides", description="discriminate rivals", criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "discrimination", "from": ["pi-tides", a.id, b.id]}
            ),
        )
    )
    return problem, a, b


def test_order_swap_inconsistency_blocks_pairwise(harness):
    """Acceptance (c): same presented label wins both orders => positional
    preference, not discrimination => no warrant, rivalry stands."""
    problem, a, b = _pairwise_setup(harness)
    ruling_a = json.dumps({"winner": "A", "decisive_point": "differential pull"})
    adapter = LLMAdapter(
        {"judge": MockEndpoint([ruling_a, ruling_a])}, harness.blobs, retry_max=2
    )
    assert pairwise_discriminate(harness, problem, a.id, b.id, adapter, Config()) is None
    assert harness.state.status[a.id] == Status.ACCEPTED
    assert harness.state.status[b.id] == Status.ACCEPTED  # unresolved, correctly
    blocks = [e for e in harness.log.read()
              if any(t == "trial-blocked:order-swap" for t in e.inputs)]
    assert blocks


def test_consistent_pairwise_registers_indexed_warrant(harness):
    problem, a, b = _pairwise_setup(harness)
    responses = [
        json.dumps({"winner": "A", "decisive_point": "differential pull"}),
        json.dumps({"winner": "B", "decisive_point": "differential pull"}),  # swapped order
    ]
    adapter = LLMAdapter({"judge": MockEndpoint(responses)}, harness.blobs, retry_max=2)
    ruling = pairwise_discriminate(harness, problem, a.id, b.id, adapter, Config())
    assert ruling is not None
    assert harness.state.status[b.id] == Status.REFUTED   # loser, for pi only
    assert harness.state.status[a.id] == Status.ACCEPTED
    body = json.loads(harness.blobs.get(ruling.content_ref) if not
                      ruling.content_ref.startswith("inline:") else
                      ruling.content_ref[len("inline:"):].encode())
    assert body["pairwise"]["problem"] == problem.id  # indexed to pi (D10)


def test_judge_cannot_discriminate_registers_nothing(harness):
    problem, a, b = _pairwise_setup(harness)
    neither = json.dumps({"winner": "neither", "decisive_point": ""})
    adapter = LLMAdapter({"judge": MockEndpoint([neither])}, harness.blobs, retry_max=2)
    assert pairwise_discriminate(harness, problem, a.id, b.id, adapter, Config()) is None
    assert harness.state.status[a.id] == Status.ACCEPTED
    assert harness.state.status[b.id] == Status.ACCEPTED
