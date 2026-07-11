"""Regression: trial spend reaches the log exactly once — even when the
critic artifact DEDUPES and when a judge seat dies mid-ensemble.

Found on the 1M arrow-of-time run (verify_root accounting delta 10,022):
two rubric commitments resolving to the same standard produced trials with
byte-identical critic artifacts; the second registration content-address-
deduped, committing no event, while the decisive judge ruling had already
been removed from the trial-llm list — a swallowed call per collision. A
mock sweep also showed _judge_all's local list losing seat 1's completed
spend whenever a later seat raised."""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.informal.skeleton import skeleton_wf_commitment
from deepreason.informal.standards import register_standard
from deepreason.informal.trial import run_trial
from deepreason.llm.adapter import LLMAdapter, SchemaRepairError
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Provenance
from deepreason.ontology.commitment import Budget


def _logged(harness) -> int:
    return sum(e.llm.tokens for e in harness.log.read() if e.llm is not None)


def _seeded(tmp_path):
    h = Harness(tmp_path / "run")
    register_standard(h, "std-x", rubric="must name a mechanism", mode="absolute")
    h.register_commitment(skeleton_wf_commitment())
    h.register_commitment(Commitment(id="kappa-x", eval="rubric:std-x"))
    # A second rubric commitment resolving to the SAME standard — the 1M
    # run's fc: forbidden cases had exactly this shape.
    h.register_commitment(Commitment(id="fc:same-standard", eval="rubric:std-x",
                                     budget=Budget(extra={"case": "z"})))
    target = h.create_artifact(
        json.dumps({"claim": "c", "mechanism": "m",
                    "forbidden": [{"case": "z", "eval": "rubric:std-x"}]}),
        provenance=Provenance(role="conjecturer"))
    return h, target


FAIL = json.dumps({"verdict": "fail", "decisive_point": "the mechanism is vacuous"})


def test_deduped_critic_does_not_swallow_the_ruling(tmp_path):
    h, target = _seeded(tmp_path)
    meter = TokenMeter(budget=10**9)
    adapter = LLMAdapter({
        # Identical case/defence/ruling across both trials => identical
        # critic artifact => the second registration dedupes.
        "argumentative_critic": MockEndpoint(
            [json.dumps({"attack": True, "case": "the mechanism is vacuous"})] * 4),
        "defender": MockEndpoint([json.dumps({"answer": "it is fine"})] * 4),
        "judge": [
            MockEndpoint(
                [FAIL] * 8, name="mock://judge-gemma", model="gemma-test"
            ),
            MockEndpoint(
                [FAIL] * 8, name="mock://judge-qwen", model="qwen-test"
            ),
        ],
    }, h.blobs, retry_max=2, meter=meter)
    config = Config()
    run_trial(h, target.id, h.commitments["kappa-x"], adapter, config, [])
    run_trial(h, target.id, h.commitments["fc:same-standard"], adapter, config, [])
    assert _logged(h) == meter.total  # every token on the log exactly once


def test_seat_one_spend_survives_seat_two_storm(tmp_path):
    h, target = _seeded(tmp_path)
    meter = TokenMeter(budget=10**9)
    adapter = LLMAdapter({
        "argumentative_critic": MockEndpoint(
            [json.dumps({"attack": True, "case": "the mechanism is vacuous"})]),
        "defender": MockEndpoint([json.dumps({"answer": "it is fine"})]),
        "judge": [
            MockEndpoint(
                [FAIL] * 4, name="mock://judge-gemma", model="gemma-test"
            ),
            MockEndpoint(
                ["never json"] * 4,
                name="mock://judge-qwen",
                model="qwen-test",
            ),
        ],
    }, h.blobs, retry_max=2, meter=meter)
    with pytest.raises(SchemaRepairError) as err:
        run_trial(h, target.id, h.commitments["kappa-x"], adapter, Config(), [])
    # The storming seat's spend rides the exception (the scheduler logs it);
    # seat 1's COMPLETED call must already be on the log, not lost with the
    # ensemble's local list.
    on_log = _logged(h)
    carried = err.value.spend.tokens if err.value.spend else 0
    assert on_log + carried == meter.total
