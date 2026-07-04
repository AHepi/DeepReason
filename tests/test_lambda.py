"""P2 acceptance (spec §16/§11.8): pre-registered thresholds committed;
lambda arms run oracle-blind on withheld-verifier problems; both-surface
metrics reported as distributions; the verdict is recorded either way."""

import json
from pathlib import Path

import yaml

from deepreason.config import Config
from deepreason.experiments import lambda_run
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.storage.blobs import BlobStore

PREREG = Path(__file__).resolve().parents[1] / "experiments" / "lambda_preregistration.yaml"


def _vs(*contents) -> str:
    return json.dumps(
        {"candidates": [{"content": c, "typicality": 0.5} for c in contents]}
    )


class _Conjecturer:
    """Improves under criticism: after a refutation appears in the pack's
    standing state, later candidates satisfy the oracle more often."""

    def __init__(self):
        self.calls = 0

    def __call__(self, prompt: str) -> str:
        self.calls += 1
        if "succ:" in prompt or self.calls > 1:
            return _vs(f"the moon pulls the sea, take {self.calls}")
        return _vs(f"the tides are magic, take {self.calls}")


def test_preregistration_is_committed():
    prereg = yaml.safe_load(PREREG.read_text())
    assert "oracle_gap_min" in prereg["thresholds"]  # falsifier stated in advance
    assert prereg["arms"]["lambda0"]["program_criteria_in_loop"] is False
    assert prereg["arms"]["lambda_full"]["program_criteria_in_loop"] is True


def test_arms_run_and_verdict_recorded(tmp_path):
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0, CAPTURE_W=10)
    results: dict[str, list[dict]] = {}
    for arm, in_loop in (("lambda0", False), ("lambda_full", True)):
        runs = []
        for replicate in range(2):
            root = tmp_path / arm / str(replicate)
            adapter = LLMAdapter(
                {"conjecturer": MockEndpoint(_Conjecturer())},
                BlobStore(root / "blobs"),
                retry_max=2,
            )
            runs.append(
                lambda_run.run_arm(
                    root,
                    program_criteria_in_loop=in_loop,
                    oracle_eval="predicate:'moon' in content",
                    problem_description="explain the tides",
                    adapter=adapter,
                    config=config,
                    cycles=3,
                )
            )
        results[arm] = runs

    summary = lambda_run.summarize(results)
    # Both surfaces reported as distributions, not means.
    for arm in ("lambda0", "lambda_full"):
        assert "values" in summary[arm]["oracle_pass_rate"]
        assert "attack_target_entropy" in summary[arm]
    # Oracle scored post-hoc in BOTH arms (oracle-blind in-loop for lambda0).
    verdict = lambda_run.verdict(summary, PREREG)
    assert "falsifier_triggered" in verdict  # recorded either way
    report_path = tmp_path / "report.json"
    lambda_run.record(report_path, summary, verdict)
    recorded = json.loads(report_path.read_text())
    assert recorded["verdict"]["reading"]
    # In the full arm the oracle is in the loop, so bad candidates get refuted
    # and lambda is exogenous; in the closed arm nothing is.
    assert summary["lambda_full"]["lambda"]["mean"] == 1.0


def test_focus_lock_works_only_the_focused_problem(tmp_path):
    """FOCUS_PROBLEM (prereg v2): spawned side-problems are recorded but
    never worked — attention only."""
    from deepreason.harness import Harness
    from deepreason.ontology import Commitment, Problem, ProblemProvenance
    from deepreason.scheduler.scheduler import Scheduler

    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="oracle", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-arm", description="the seed problem", criteria=["oracle"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    calls = {"n": 0}

    def conjecture(prompt):
        calls["n"] += 1
        return _vs(f"the tides are magic {calls['n']}", f"the moon pulls {calls['n']}")

    adapter = LLMAdapter({"conjecturer": MockEndpoint(conjecture)}, harness.blobs, retry_max=2)
    config = Config(VS_K=2, N_SCHOOLS=0, FLOOR=0, FOCUS_PROBLEM="pi-arm")
    Scheduler(harness, adapter, config).run(4)
    worked = {pid for _, pid in harness.state.addr}
    assert worked == {"pi-arm"}  # successors spawn but are never worked
    assert any(p.startswith("succ:") for p in harness.state.problems)


def test_run_arm_reports_v2_metrics(tmp_path):
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: _vs("the moon pulls the sea", "magic"))},
        BlobStore(tmp_path / "b"),
        retry_max=2,
    )
    result = lambda_run.run_arm(
        tmp_path / "run",
        program_criteria_in_loop=True,
        oracle_eval="predicate:'moon' in content",
        problem_description="mention the moon",
        adapter=adapter,
        config=Config(VS_K=2, N_SCHOOLS=0, FLOOR=0, FOCUS_PROBLEM="pi-arm"),
        cycles=1,
    )
    assert result["oracle_passes"] == 1        # one seed candidate passes
    assert result["oracle_pass_rate_seed"] == 0.5
    assert "gate_blocks" in result


def test_verdict_uses_preregistered_primary_metric(tmp_path):
    prereg = tmp_path / "prereg_v2.yaml"
    prereg.write_text(
        "primary_metric: oracle_passes\nthresholds:\n  gap_min: 1.0\n"
    )
    summary = {
        "lambda_full": {"oracle_passes": {"mean": 3.0}},
        "lambda0": {"oracle_passes": {"mean": 1.0}},
    }
    v = lambda_run.verdict(summary, prereg)
    assert v["metric"] == "oracle_passes"
    assert v["gap"] == 2.0
    assert v["falsifier_triggered"] is False
