"""Diversity instrumentation: token surprisal (item 1) and Level-2 spec
injection with the transmission diagnostic (item 2). All attention/
reporting only — never status (§0)."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.embedder import HashingEmbedder
from deepreason.llm.endpoints import MockEndpoint, mean_surprisal
from deepreason.llm.specs import SpecsOutput, transmission_score
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.report import eval_report
from deepreason.rules.conj import conj
from deepreason.scheduler.scheduler import Scheduler


def _vs(*contents) -> str:
    return json.dumps(
        {"candidates": [{"content": c, "typicality": 0.5} for c in contents]}
    )


def _seed(harness) -> None:
    harness.register_commitment(Commitment(id="k-true", eval="predicate:True"))
    harness.register_problem(
        Problem(
            id="pi-1", description="a seed problem", criteria=["k-true"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )


def test_mean_surprisal_parses_openai_shape():
    block = {"content": [{"token": "a", "logprob": -0.5}, {"token": "b", "logprob": -1.5}]}
    assert mean_surprisal(block) == 1.0
    assert mean_surprisal(None) is None
    assert mean_surprisal({"content": []}) is None


def test_surprisal_recorded_on_llmcall_and_in_report(tmp_path):
    harness = Harness(tmp_path / "run")
    _seed(harness)

    class SurprisalMock(MockEndpoint):
        def complete(self, prompt):
            response = super().complete(prompt)
            self.last_mean_surprisal = 2.5
            return response

    adapter = LLMAdapter(
        {"conjecturer": SurprisalMock(lambda p: _vs("one idea", "another idea"))},
        harness.blobs, retry_max=2,
    )
    conj(harness, "pi-1", adapter, Config(VS_K=2))
    event = [e for e in harness.log.read() if e.llm][-1]
    assert event.llm.mean_surprisal == 2.5
    report = eval_report(harness, Config())
    assert report["llm"]["conjecturer"]["mean_surprisal"] == 2.5
    from deepreason.capture import detection

    gen = detection.generator_metrics(harness, HashingEmbedder(), 10)
    assert gen["mean_token_surprisal"] == 2.5


def test_transmission_score_binds_and_ignores():
    embedder = HashingEmbedder()
    specs = ["ocean thermal currents heat", "volcanic tectonic plates magma"]
    bound = ["heat moves through ocean thermal currents", "magma rises between tectonic plates"]
    assert transmission_score(specs, bound, embedder) == 1.0
    ignored = ["the moon is nice", "the moon is very nice"]
    assert transmission_score(specs, ignored, embedder) is not None  # low or chance
    assert transmission_score(["only-one"], bound, embedder) is None  # needs >= 2


def test_spec_injection_end_to_end(tmp_path):
    """Scheduler generates specs (one logged call), pack binds candidate k
    to spec k, and the transmission measure lands in the log + report."""
    harness = Harness(tmp_path / "run")
    _seed(harness)
    specs_json = json.dumps(
        {"specs": ["ocean thermal currents heat", "volcanic tectonic plates magma"]}
    )
    prompts = []

    def conjecture(prompt):
        prompts.append(prompt)
        if "orthogonal" in prompt:  # the spec_generator template
            return specs_json
        return _vs(
            "heat moves through ocean thermal currents",
            "magma rises between tectonic plates",
        )

    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(conjecture)}, harness.blobs, retry_max=2
    )
    config = Config(VS_K=2, N_SCHOOLS=0, FLOOR=0, SPEC_INJECTION=True)
    Scheduler(harness, adapter, config).run(1)

    assert any("DIVERSITY SPECIFICATIONS" in p for p in prompts)  # specs bound into pack
    tags = [t for e in harness.log.read() for t in e.inputs]
    assert "spec-generation" in tags
    scores = [t for t in tags if t.startswith("spec-transmission:")]
    assert scores and float(scores[0].split(":")[1]) == 1.0
    report = eval_report(harness, config)
    assert report["spec_transmission"]["n"] == 1


def test_stagnation_ladder_switches_on_spec_injection(tmp_path):
    from deepreason.capture import ladder

    harness = Harness(tmp_path / "run")
    _seed(harness)
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: _vs("an idea"))}, harness.blobs, retry_max=2
    )
    scheduler = Scheduler(harness, adapter, Config(VS_K=1, N_SCHOOLS=0, FLOOR=0))
    assert scheduler.spec_injection is False
    ladder.respond(scheduler, {"lineage_stagnation": True})
    assert scheduler.spec_injection is True


def test_specs_output_contract():
    out = SpecsOutput.model_validate_json(json.dumps({"specs": ["a", "b"]}))
    assert out.specs == ["a", "b"]
