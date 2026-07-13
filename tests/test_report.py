"""P6 eval report: every reported metric derives from the log/state and the
report is JSON-serializable end to end."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.report import eval_report
from deepreason.scheduler.scheduler import Scheduler


def _vs(prompt: str) -> str:
    return json.dumps(
        {
            "candidates": [
                {"content": f"the moon pulls the sea ({hash(prompt) % 97})", "typicality": 0.8},
                {"content": f"the tides are magic ({hash(prompt) % 89})", "typicality": 0.2},
            ]
        }
    )


def _edits(prompt: str) -> str:
    return json.dumps({"edits": [{"content": f"edit {i}: another mechanism"} for i in range(3)]})


def test_eval_report_from_scheduler_run(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(_vs), "variator": MockEndpoint(_edits)},
        harness.blobs,
        retry_max=2,
    )
    config = Config(VS_K=2, N_SCHOOLS=2, HV_K=3, HV_MIN=0.5, CAPTURE_W=10)
    Scheduler(harness, adapter, config).run(4)
    # Stage a trial block and an intervention so those sections populate.
    harness.record_measure(inputs=["trial-blocked:order-swap", "case-1"])
    harness.record_measure(inputs=["intervention:stagnation-recruit"])
    harness.record_measure(inputs=["judge-error-rate:0.2500"])

    report = eval_report(harness, config)
    json.dumps(report)  # fully serializable

    assert report["totals"]["events"] > 0
    llm = report["llm"]
    assert llm["conjecturer"]["valid_json_rate"] == 1.0  # every call one attempt
    assert "variator" in llm
    assert 0.0 <= report["attack_validity_rate"] <= 1.0
    assert report["survivor_hv"]["n"] > 0
    assert report["trial_guard"]["blocked"] == {"order-swap": 1}
    assert report["trial_guard"]["survival_rate"] == 0.0  # 0 warrants, 1 block
    assert report["audits"]["planted_flaw_error_rate"] == 0.25
    assert set(report["schools"]["roster"]) == {"school-0", "school-1"}
    assert report["interventions"][-1]["rule"] == "stagnation-recruit"
    assert report["capture"]["lambda"] == 1.0  # program verdicts only
    grounding = report["capture"]["program_grounding"]
    assert set(grounding["counts"]) == {
        "structural", "execution", "simulation", "formal", "observation"
    }
    assert grounding["structural_program_fraction"] == 1.0
    assert grounding["execution_lambda"] == 0.0
    assert grounding["simulation_lambda"] == 0.0
    assert grounding["formal_lambda"] == 0.0
    assert grounding["rubric_fraction"] == 0.0
    assert 0.0 < grounding["predicate_fraction"] < 1.0
    # The signals block: the log's table of contents, family-normalized.
    signals = report["signals"]
    assert signals["cycle"] == 4                      # one heartbeat per cycle
    assert signals["trial-blocked:*"] == 1
    assert signals["intervention:*"] >= 1
    assert signals["judge-error-rate:*"] == 1


def test_valid_json_rate_counts_repair_attempts(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_problem(
        Problem(
            id="pi-1",
            description="a problem",
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    good = json.dumps({"candidates": [{"content": "a fine claim", "typicality": 0.5}]})
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(["not json", good])}, harness.blobs, retry_max=2
    )
    from deepreason.rules.conj import conj

    conj(harness, "pi-1", adapter, Config(VS_K=1, NEAR_DUP_EPS=None))
    report = eval_report(harness, Config())
    row = report["llm"]["conjecturer"]
    assert row["calls"] == 1 and row["attempts"] == 2
    assert row["valid_json_rate"] == 0.5  # one repair retry consumed
