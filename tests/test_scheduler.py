"""P2 acceptance (spec §16): a multi-cycle run spawns successor,
discrimination, and connection problems; HV and reach are logged; the
frontier persists across save/reload; Pareto focus reports the frontier."""

import json

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.scheduler.scheduler import Scheduler


def _vs(*contents) -> str:
    return json.dumps(
        {
            "candidates": [
                {"content": c, "typicality": round(0.9 - 0.1 * i, 2)}
                for i, c in enumerate(contents)
            ]
        }
    )


class _ScriptedConjecturer:
    """Different content per (problem, call) — deterministic."""

    def __init__(self):
        self.calls = 0

    def __call__(self, prompt: str) -> str:
        self.calls += 1
        n = self.calls
        return _vs(
            f"the moon pulls the sea (variant {n})",
            f"the tides are magic (variant {n})",
        )


def _edits_response(prompt: str) -> str:
    return json.dumps(
        {"edits": [{"content": f"edit {i} of the target idea"} for i in range(3)]}
    )


def _setup(root) -> Harness:
    harness = Harness(root)
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    harness.register_problem(
        Problem(
            id="pi-tides",
            description="explain the tides",
            criteria=["k-moon"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    return harness


def test_multi_cycle_spawns_and_persistence(tmp_path):
    root = tmp_path / "run"
    harness = _setup(root)
    config = Config(VS_K=2, N_SCHOOLS=2, HV_K=3, HV_MIN=0.5, FLOOR=1, CAPTURE_W=10)
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(_ScriptedConjecturer()),
            "variator": MockEndpoint(_edits_response),
        },
        harness.blobs,
        retry_max=2,
    )
    scheduler = Scheduler(harness, adapter, config)
    report = scheduler.run(4)

    problems = harness.state.problems
    assert any(p.startswith("succ:") for p in problems)   # failed verdict => successor
    assert any(p.startswith("disc:") for p in problems)   # >=2 rivals => discrimination
    assert any(p.startswith("conn:") for p in problems)   # iso > 0 => connection
    assert harness.state.hv                               # lazy HV logged
    assert report["survivors"]
    assert set(report["frontier"]) <= set(report["survivors"])  # Pareto focus (§11.7)

    # Frontier persists across save/reload — the log is the save.
    reopened = Harness(root)
    assert reopened.state.model_dump_json() == harness.state.model_dump_json()
    assert sorted(reopened.state.problems) == sorted(problems)


def test_reach_hit_logged_and_spawns_debt(tmp_path):
    harness = _setup(tmp_path / "run")
    # A second problem whose evaluable criterion the survivor also passes.
    harness.register_commitment(Commitment(id="k-sea", eval="predicate:'sea' in content"))
    harness.register_problem(
        Problem(
            id="pi-currents",
            description="explain ocean currents",
            criteria=["k-sea"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=0)  # isolate the reach machinery
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([_vs("the moon pulls the sea"),
                                      _vs("currents follow the sea floor")])},
        harness.blobs,
        retry_max=2,
    )
    Scheduler(harness, adapter, config).run(2)
    reach = harness.state.reach
    assert any(v > 0 for v in reach.values())              # reach logged
    assert any(p.startswith("debt:") for p in harness.state.problems)  # explanation debt


def test_integration_budget_share_caps_connection_work(tmp_path):
    harness = _setup(tmp_path / "run")
    config = Config(VS_K=1, N_SCHOOLS=0, FLOOR=1, INTEGRATION_BUDGET_SHARE=0.0)
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: _vs("the moon pulls the sea"))},
        harness.blobs,
        retry_max=2,
    )
    scheduler = Scheduler(harness, adapter, config)
    scheduler.run(3)
    # Connection problems may spawn, but zero share means none get worked.
    conn_problems = [p for p in harness.state.problems if p.startswith("conn:")]
    worked = {pid for _, pid in harness.state.addr}
    assert not (worked & set(conn_problems))


def test_focus_family_restricts_selection(tmp_path):
    """FOCUS_FAMILY (staged pipelines): selection is limited to the named
    problem's transitive family — in-family successors keep working, but an
    unrelated unsolved problem never wins, no matter its liveness age."""
    from deepreason.ontology import Provenance
    from deepreason.scheduler.scheduler import problem_family

    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-a", eval="predicate:len(content) > 0"))
    for pid in ("pi-stage", "pi-other"):
        harness.register_problem(Problem(
            id=pid, description=pid, criteria=["k-a"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        ))
    # A refuted candidate on pi-stage spawns a successor into the family.
    doomed = harness.create_artifact(
        "x", provenance=Provenance(role="conjecturer"), problem_id="pi-stage")
    from deepreason.rules.warrants import register_fail_warrant
    register_fail_warrant(
        harness, commitment_id="k-a", target_id=doomed.id,
        nu_content="nu", critic_content="critic", trace_ref="")
    conj = json.dumps({"candidates": [{"content": "another idea", "typicality": 0.9}]})
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([conj] * 6)}, harness.blobs, retry_max=2)
    scheduler = Scheduler(
        harness, adapter, Config(VS_K=1, N_SCHOOLS=0, FUZZ_N=0,
                                 FOCUS_FAMILY="pi-stage"))
    for _ in range(4):
        scheduler.step()
    family = problem_family(harness.state, "pi-stage")
    assert "pi-stage" in family
    assert any(pid.startswith("succ:") for pid in family)  # successor joined
    worked = set(scheduler._problem_worked)
    assert worked and worked <= family          # never left the family
    assert "pi-other" not in worked


def test_on_cycle_true_stops_the_run_early(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k-a", eval="predicate:len(content) > 0"))
    harness.register_problem(Problem(
        id="pi-a", description="a", criteria=["k-a"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    conj = json.dumps({"candidates": [{"content": "idea", "typicality": 0.9}]})
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([conj] * 10)}, harness.blobs, retry_max=2)
    scheduler = Scheduler(harness, adapter, Config(VS_K=1, N_SCHOOLS=0, FUZZ_N=0))
    seen = []
    scheduler.run(10, on_cycle=lambda s: seen.append(s._cycles) or len(seen) >= 2)
    assert seen == [1, 2]        # stopped after the 2nd cycle, not 10
    assert scheduler._cycles == 2
