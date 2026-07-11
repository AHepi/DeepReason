"""Compact hot paths use local aliases and compile back to canonical values."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.informal.standards import register_standard
from deepreason.informal.trial import pairwise_discriminate, run_trial
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.contracts import VariatorOutput
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.programs import content_text
from deepreason.rules.crit import crit_argumentative_batch
from deepreason.rules.synth import synthesize
from deepreason.scheduler.scheduler import Scheduler


def _problem(harness, *, problem_id="pi-tides", description="explain the tides"):
    harness.register_commitment(
        Commitment(id="k-moon", eval="predicate:'moon' in content")
    )
    return harness.register_problem(
        Problem(
            id=problem_id,
            description=description,
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def test_compact_scheduler_aliases_conjecture_neighbours_and_critic_target(tmp_path):
    harness = Harness(tmp_path / "run")
    _problem(harness)
    neighbour = harness.create_artifact("prior moon mechanism")
    conj_prompts = []
    critic_prompts = []

    def conjecturer(prompt):
        conj_prompts.append(prompt)
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": "moon geometry explains spring tides",
                        "typicality": 0.3,
                        "neighbours": ["A1"],
                    }
                ]
            }
        )

    def critic(prompt):
        critic_prompts.append(prompt)
        return json.dumps(
            {
                "attack": False,
                "target_alias": "A1",
                "claim": "",
                "grounds": "",
                "cited_input_aliases": [],
            }
        )

    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(conjecturer),
            "argumentative_critic": MockEndpoint(critic),
        },
        harness.blobs,
        model_profile="compact",
    )
    config = Config(
        VS_K=1,
        N_SCHOOLS=0,
        FLOOR=0,
        ARG_CRIT_PER_CYCLE=1,
        RECRIT_STANDING=False,
        GEN_PROPOSE_PERIOD=0,
        PROP_PROPOSE_PERIOD=0,
    )
    Scheduler(harness, adapter, config).step()

    candidate = next(
        artifact
        for artifact in harness.state.artifacts.values()
        if content_text(artifact, harness.blobs)
        == "moon geometry explains spring tides"
    )
    assert candidate.interface.refs[0].target == neighbour.id
    assert neighbour.id not in conj_prompts[0]
    assert candidate.id not in critic_prompts[0]
    assert "neighbours" in conj_prompts[0]
    assert "target_alias" in critic_prompts[0]


def test_compact_batch_request_splits_into_deterministic_single_target_calls(harness):
    first = harness.create_artifact("first moon claim")
    second = harness.create_artifact("second moon claim")
    prompts = []

    def critic(prompt):
        prompts.append(prompt)
        return json.dumps(
            {
                "attack": False,
                "target_alias": "A1",
                "claim": "",
                "grounds": "",
                "cited_input_aliases": [],
            }
        )

    adapter = LLMAdapter(
        {"argumentative_critic": MockEndpoint(critic)},
        harness.blobs,
        model_profile="compact",
    )
    assert crit_argumentative_batch(
        harness, [first.id, second.id], adapter, Config()
    ) == []
    assert len(prompts) == 2
    assert first.id not in prompts[0] and second.id not in prompts[1]
    assert all("target_alias" in prompt and "cases" not in prompt for prompt in prompts)


def test_compact_critic_repairs_a_known_alias_for_the_wrong_target(harness):
    target = harness.create_artifact("target moon claim")
    validity = harness.create_artifact("the prior attack is sound")
    prior = harness.create_artifact(
        "prior fault",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w:prior-target-alias-test",
                target=target.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=validity.id,
            )
        ],
        rule=Rule.CRIT,
    )
    assert (prior.id, target.id) in harness.state.att

    prompts = []
    responses = [
        {
            "attack": False,
            "target_alias": "A2",
            "claim": "",
            "grounds": "",
            "cited_input_aliases": [],
        },
        {
            "attack": False,
            "target_alias": "A1",
            "claim": "",
            "grounds": "",
            "cited_input_aliases": [],
        },
    ]

    def critic(prompt):
        prompts.append(prompt)
        return json.dumps(responses.pop(0))

    adapter = LLMAdapter(
        {"argumentative_critic": MockEndpoint(critic)},
        harness.blobs,
        model_profile="compact",
    )
    assert crit_argumentative_batch(harness, [target.id], adapter, Config()) == []
    assert len(prompts) == 2
    assert '"const": "A1"' in prompts[0]
    assert '"path": "/target_alias"' in prompts[1]


def test_compact_trial_preserves_ensemble_and_referential_integrity(tmp_path):
    harness = Harness(tmp_path / "trial")
    register_standard(
        harness, "std-1", "clause 2: no parallel fifths", mode="absolute"
    )
    commitment = Commitment(id="kappa-taste", eval="rubric:std-1")
    harness.register_commitment(commitment)
    target = harness.create_artifact(
        "a chorale passage with parallel fifths in bar 3",
        interface=Interface(commitments=[commitment.id]),
    )
    case = "parallel fifths in bar 3 violate clause 2"
    prompts = {"critic": [], "defender": [], "judge": []}

    def critic(prompt):
        prompts["critic"].append(prompt)
        return json.dumps(
            {
                "attack": True,
                "target_alias": "A1",
                "claim": case,
                "grounds": "",
                "cited_input_aliases": [],
            }
        )

    def defender(prompt):
        prompts["defender"].append(prompt)
        return json.dumps(
            {
                "clauses": [
                    {"item_alias": "K1", "response": "the echo is intentional"}
                ]
            }
        )

    def judge(prompt):
        prompts["judge"].append(prompt)
        return json.dumps(
            {
                "decision": "fail",
                "decisive_point_alias": "K1",
                "grounds": "the cited clause is explicit",
            }
        )

    adapter = LLMAdapter(
        {
            "argumentative_critic": MockEndpoint(critic),
            "defender": MockEndpoint(defender),
            "judge": [
                MockEndpoint(
                    judge, name="mock://judge-gemma", model="gemma-test"
                ),
                MockEndpoint(
                    judge, name="mock://judge-qwen", model="qwen-test"
                ),
            ],
        },
        harness.blobs,
        model_profile="compact",
    )
    result = run_trial(
        harness, target.id, commitment, adapter, Config(TRIAL_PARAPHRASE_N=0)
    )
    assert result is not None
    assert harness.state.status[target.id] == Status.REFUTED
    warrant = next(w for w in harness.warrants.values() if w.target == target.id)
    transcript = json.loads(harness.blobs.get(warrant.trace_ref))
    assert transcript["ruling"]["decisive_point"] == case
    assert case in f"{transcript['case']}\n{transcript['answer']}"
    assert len(prompts["judge"]) == 2
    assert "target_alias" in prompts["critic"][0]
    assert "item_alias" in prompts["defender"][0]
    assert all("decisive_point_alias" in prompt for prompt in prompts["judge"])


def test_compact_pairwise_aliases_preserve_order_swap(harness):
    first = harness.create_artifact("differential lunar pull explains both tides")
    second = harness.create_artifact("solar heating explains both tides")
    problem = harness.register_problem(
        Problem(
            id="disc:tides",
            description="discriminate tidal explanations",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "discrimination", "from": [first.id, second.id]}
            ),
        )
    )
    responses = [
        '{"winner":"A","decisive_point_alias":"K1"}',
        '{"winner":"B","decisive_point_alias":"K1"}',
    ]
    endpoint = MockEndpoint(responses)
    adapter = LLMAdapter(
        {"judge": endpoint}, harness.blobs, model_profile="compact"
    )
    ruling = pairwise_discriminate(
        harness, problem, first.id, second.id, adapter, Config()
    )
    assert ruling is not None
    assert harness.state.status[second.id] == Status.REFUTED


def test_compact_synthesizer_compiles_dependence_aliases(harness):
    first = harness.create_artifact("moon forcing mechanism")
    second = harness.create_artifact("basin resonance mechanism")
    problem = harness.register_problem(
        Problem(
            id="conn:tides",
            description="connect the two tidal mechanisms",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "connection", "from": [first.id, second.id]}
            ),
        )
    )
    endpoint = MockEndpoint(
        [
            json.dumps(
                {
                    "relation": "lunar forcing excites basin resonance",
                    "depends_on": ["A1", "A2"],
                }
            )
        ]
    )
    adapter = LLMAdapter(
        {"synthesizer": endpoint}, harness.blobs, model_profile="compact"
    )
    relation = synthesize(harness, problem, adapter, Config())
    assert relation is not None
    assert {ref.target for ref in relation.interface.refs} == {first.id, second.id}
    prompt = harness.blobs.get(
        next(event.llm.prompt_ref for event in harness.log.read() if event.llm)
    ).decode()
    assert first.id not in prompt and second.id not in prompt


def test_compact_variator_uses_alias_free_bounded_edit_contract(harness):
    endpoint = MockEndpoint(
        [
            json.dumps(
                {
                    "edits": [
                        {
                            "content": "moon forcing with a narrower scope",
                            "changed_fields": ["scope"],
                        }
                    ]
                }
            )
        ]
    )
    adapter = LLMAdapter(
        {"variator": endpoint}, harness.blobs, model_profile="compact"
    )
    output, call = adapter.call(
        "variator", "TARGET CONTENT:\nmoon forcing", VariatorOutput
    )
    assert output.edits[0].content == "moon forcing with a narrower scope"
    prompt = harness.blobs.get(call.prompt_ref).decode()
    assert "changed_fields" in prompt
