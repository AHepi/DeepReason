"""Normative rubric judging is preflighted at the frozen route boundary."""

import json

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.informal.standards import register_standard
from deepreason.informal.trial import run_argument_trial_from_case, run_trial
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import JudgeEnsemblePolicyError, is_single_model_run, leases_from_manifest
from deepreason.ontology import Commitment, Interface, Problem, ProblemProvenance, Provenance
from deepreason.provider_profile import ProviderProfileV1
from deepreason.rules.experiment import relevance_trial
from tests.conftest import art


_STAMP = "2026-07-16T00:00:00Z"


def _seat_test_profile(**updates) -> ProviderProfileV1:
    values = dict(
        provider="openai",
        endpoint="https://api.example.test/v1",
        model_id="model-judge-boundary-baseline",
        model_revision="revision-1",
        family="family-judge-boundary",
        context_window_tokens=131_072,
        maximum_completion_tokens=4_096,
        credential_env="DEEPREASON_JUDGE_BOUNDARY_TEST_KEY",
    )
    values.update(updates)
    return ProviderProfileV1.create(**values)


def _mock_for_route(route):
    return MockEndpoint(
        lambda _prompt: json.dumps({"answer": "the mechanism is explicit"}),
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )


def _adapter_from_manifest(manifest, harness):
    endpoints = {
        "defender": _mock_for_route(manifest.roles["defender"][0]),
        "judge": _mock_for_route(manifest.roles["judge"][0]),
    }
    return LLMAdapter(
        endpoints, harness.blobs, leases=leases_from_manifest(manifest)
    )


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


def test_school_seat_diversity_flips_single_model_predicate_for_judge_role(monkeypatch, tmp_path):
    """Step 46 (S2d, C6, Amendment 11/R27 -- Consequence-B disclosure): a
    `--school-seat` opt-in that adds route diversity to the CONJECTURER
    role only -- never touching `judge` -- flips `is_single_model_run` to
    False for the WHOLE run, because that predicate scans every role's
    leases (`llm/firewall.py::is_single_model_run` via `_lease_models`),
    not just the caller's own role.

    `informal/trial.py::_argument_trial_steps` reads exactly this
    predicate to choose between two paths: a single-model run with fewer
    than two judge seats DECLINES gracefully ("single-judge-seat", a typed
    Measure, no exception); a NOT-single-model run skips that graceful
    decline entirely and calls `adapter.require_cross_family_judges()`,
    which raises `JudgeEnsemblePolicyError` on that SAME, otherwise
    untouched, still-one-seat judge role. So the school-seat opt-in can
    turn a graceful decline into a hard preflight failure for a role it
    never configured -- this test is the executable proof backing Step
    47's CLI disclosure text, not a design change."""

    import deepreason.preparation as preparation_module
    from deepreason.preparation import build_preparation_manifest

    original_config = preparation_module.Config

    def _forced_school_seats_config(**kwargs):
        return original_config(**kwargs, SCHOOL_SEATS_ENABLED=True)

    monkeypatch.setattr(preparation_module, "Config", _forced_school_seats_config)

    profile = _seat_test_profile()
    # Same family as `profile` -- isolates the MODEL axis `is_single_model_run`
    # actually reads, distinct from the (already-covered) family axis.
    distinct_profile = _seat_test_profile(
        endpoint="https://distinct.example.test/v1",
        model_id="model-judge-boundary-distinct",
        credential_env="DEEPREASON_JUDGE_BOUNDARY_DISTINCT_TEST_KEY",
    )

    baseline_manifest = build_preparation_manifest(
        profile,
        question="Does an untouched run stay single-model?",
        compiled_at=_STAMP,
    )
    diverse_manifest = build_preparation_manifest(
        profile,
        question="Does one conjecturer school seat flip is_single_model_run?",
        compiled_at=_STAMP,
        school_seats={"school-1": distinct_profile},
    )

    # The judge role is untouched by --school-seat in both manifests: one
    # seat, the same route, either way.
    baseline_leases = leases_from_manifest(baseline_manifest)
    diverse_leases = leases_from_manifest(diverse_manifest)
    assert len(baseline_leases["judge"]) == len(diverse_leases["judge"]) == 1
    assert (
        baseline_leases["judge"][0].route.model_id
        == diverse_leases["judge"][0].route.model_id
    )

    # The predicate flip itself.
    assert is_single_model_run(baseline_leases) is True
    assert is_single_model_run(diverse_leases) is False

    # The concrete behavioral consequence: same 1-seat judge role, same
    # target, same case -- graceful decline before the opt-in, hard raise
    # after it.
    for label, manifest, expect_raise in (
        ("baseline", baseline_manifest, False),
        ("diverse", diverse_manifest, True),
    ):
        harness = Harness(tmp_path / f"run-{label}")
        target = art(
            harness,
            "the mechanism is explicit",
            provenance=Provenance(role="conjecturer", school="school-0"),
        )
        adapter = _adapter_from_manifest(manifest, harness)
        diagnostics: list = []
        if expect_raise:
            with pytest.raises(JudgeEnsemblePolicyError):
                run_argument_trial_from_case(
                    harness, adapter, Config(), target.id,
                    "the case for fail", None,
                    authority="status", critic_school_id="school-1",
                    diagnostics=diagnostics,
                )
        else:
            result = run_argument_trial_from_case(
                harness, adapter, Config(), target.id,
                "the case for fail", None,
                authority="status", critic_school_id="school-1",
                diagnostics=diagnostics,
            )
            assert result is None
            assert diagnostics[-1]["declined"] == "single-judge-seat"
