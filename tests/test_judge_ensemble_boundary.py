"""Normative rubric judging is preflighted at the frozen route boundary."""

import json

import pytest

from deepreason.config import Config
from deepreason.informal.standards import register_standard
from deepreason.informal.trial import run_trial
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import JudgeEnsemblePolicyError
from deepreason.ontology import Commitment, Interface, Problem, ProblemProvenance, Provenance
from deepreason.rules.experiment import relevance_trial
from tests.conftest import art


def _counting_endpoint(calls, response, *, name, model):
    def complete(_prompt):
        calls.append(model)
        return response

    return MockEndpoint(complete, name=name, model=model)


def _trial_fixture(harness):
    register_standard(harness, "std-x", "must name a mechanism")
    commitment = Commitment(id="k-rubric", eval="rubric:std-x")
    harness.register_commitment(commitment)
    target = art(
        harness,
        "the mechanism is explicit",
        interface=Interface(commitments=[commitment.id]),
    )
    return target, commitment


def _prompt_capturing_endpoint(prompts, response, *, name, model):
    def complete(prompt):
        prompts.append(prompt)
        return response

    return MockEndpoint(complete, name=name, model=model)


def _trial_adapter(harness, judge_endpoints, calls):
    return LLMAdapter(
        {
            "argumentative_critic": _counting_endpoint(
                calls,
                json.dumps({"attack": True, "case": "the mechanism is explicit"}),
                name="mock://critic",
                model="critic-test",
            ),
            "defender": _counting_endpoint(
                calls,
                json.dumps({"answer": "the mechanism is explicit"}),
                name="mock://defender",
                model="defender-test",
            ),
            "judge": judge_endpoints,
        },
        harness.blobs,
    )


def test_judge_seats_disabled_by_default_is_byte_identical():
    """Part D (S2b, R2): the master judge-dispatch gate defaults False,
    and every existing judge-dispatch test in this file passes
    unmodified -- the new gate changes nothing when False."""

    assert Config().JUDGE_SEATS_ENABLED is False


@pytest.mark.parametrize("same_family_pair", [False, True])
def test_trial_rejects_invalid_direct_ensemble_before_any_endpoint_call(
    harness, same_family_pair
):
    target, commitment = _trial_fixture(harness)
    calls = []
    ruling = json.dumps(
        {"verdict": "pass", "decisive_point": "the mechanism is explicit"}
    )
    first = _counting_endpoint(
        calls, ruling, name="mock://judge-1", model="gemma-test-a"
    )
    judges = first
    if same_family_pair:
        judges = [
            first,
            _counting_endpoint(
                calls, ruling, name="mock://judge-2", model="gemma-test-b"
            ),
        ]
    adapter = _trial_adapter(harness, judges, calls)

    with pytest.raises(JudgeEnsemblePolicyError) as raised:
        run_trial(
            harness, target.id, commitment, adapter, Config(),
            authority="status",
        )

    assert raised.value.code == "SECOND_JUDGE_FAMILY_REQUIRED"
    assert calls == []
    assert not any(event.llm is not None for event in harness.log.read())


def test_trial_accepts_frozen_cross_family_direct_ensemble(harness):
    target, commitment = _trial_fixture(harness)
    calls = []
    ruling = json.dumps(
        {"verdict": "pass", "decisive_point": "the mechanism is explicit"}
    )
    judges = [
        _counting_endpoint(
            calls, ruling, name="mock://judge-gemma", model="gemma-test"
        ),
        _counting_endpoint(
            calls, ruling, name="mock://judge-qwen", model="qwen-test"
        ),
    ]

    result = run_trial(
        harness, target.id, commitment, _trial_adapter(harness, judges, calls), Config(),
        authority="status",
    )

    assert result is None
    assert calls == ["critic-test", "defender-test", "gemma-test", "qwen-test"]


def test_trial_accepts_genuinely_identical_model_direct_ensemble(harness):
    """Part D2 (S16, Amendment 9 R24): >=2 judge seats that are the exact
    same (provider, model_id) satisfy require_cross_family_judge_ensemble
    via the structural same-model substitute -- distinct from the
    same_family_pair=True case in test_trial_rejects_invalid_direct_
    ensemble_before_any_endpoint_call above (different model STRINGS of
    one family, still correctly rejected)."""
    target, commitment = _trial_fixture(harness)
    calls = []
    ruling = json.dumps(
        {"verdict": "pass", "decisive_point": "the mechanism is explicit"}
    )
    judges = [
        _counting_endpoint(
            calls, ruling, name="mock://judge-seat-0", model="gemma-test"
        ),
        _counting_endpoint(
            calls, ruling, name="mock://judge-seat-1", model="gemma-test"
        ),
    ]

    result = run_trial(
        harness, target.id, commitment, _trial_adapter(harness, judges, calls), Config(),
        authority="status",
    )

    assert result is None
    assert calls == ["critic-test", "defender-test", "gemma-test", "gemma-test"]


def test_judge_pack_never_names_an_author_school_or_model(harness):
    """Part D2 (S15, Amendment 9 R24, judge-facing twin of R9's
    test_the_criticism_prompt_never_names_an_author_or_a_school): the
    ensemble-diversity requirement is a proxy for BLINDNESS, and the
    operator's clarification makes blindness the actual guarantee a
    same-model judge ensemble must satisfy to mint. This pins that
    property for the JUDGE's own pack (_judge_pack), which R9 never
    covered -- it only pinned the CRITIC pack. Fails if the target's
    distinctive school id, its provenance role, or the word "school"/
    "author"/"provenance"/"model" ever leaks into what the judge reads."""

    register_standard(harness, "std-x", "must name a mechanism")
    commitment = Commitment(id="k-rubric", eval="rubric:std-x")
    harness.register_commitment(commitment)
    target = art(
        harness,
        "the mechanism is explicit",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="conjecturer", school="school-distinctive-xyz"),
    )
    ruling = json.dumps(
        {"verdict": "pass", "decisive_point": "the mechanism is explicit"}
    )
    judge_prompts: list = []
    calls: list = []
    adapter = _trial_adapter(
        harness,
        [
            _prompt_capturing_endpoint(
                judge_prompts, ruling, name="mock://judge-gemma", model="gemma-test"
            ),
            _prompt_capturing_endpoint(
                judge_prompts, ruling, name="mock://judge-qwen", model="qwen-test"
            ),
        ],
        calls,
    )

    run_trial(harness, target.id, commitment, adapter, Config(), authority="status")

    assert len(judge_prompts) == 2
    for prompt in judge_prompts:
        assert "school-distinctive-xyz" not in prompt
        for label in ("school", "author", "provenance", "conjecturer", "gemma", "qwen"):
            assert label not in prompt.lower(), (label, prompt)


def test_property_relevance_rejects_same_family_before_judge_call(harness):
    calls = []
    ruling = json.dumps({"verdict": "pass", "decisive_point": "required"})
    adapter = LLMAdapter(
        {
            "judge": [
                _counting_endpoint(
                    calls, ruling, name="mock://judge-1", model="gemma-test-a"
                ),
                _counting_endpoint(
                    calls, ruling, name="mock://judge-2", model="gemma-test-b"
                ),
            ]
        },
        harness.blobs,
    )
    prop = art(harness, "def check(inp, out):\n    return True")
    problem = Problem(
        id="pi",
        description="required output",
        criteria=[],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    )

    with pytest.raises(JudgeEnsemblePolicyError):
        relevance_trial(
            harness,
            prop,
            "required",
            problem,
            adapter,
            Config(ADJUDICATION_STATUS_AUTHORITY_ENABLED=True),
        )

    assert calls == []
    assert not any(event.llm is not None for event in harness.log.read())
