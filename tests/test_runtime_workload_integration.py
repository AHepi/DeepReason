"""Production-path regressions for workload-owned runtime metadata."""

import json
from types import SimpleNamespace

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.packs import render_conj_pack
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.run_manifest import RunManifest, persist_run_manifest
from deepreason.runtime.progress import ProgressSink
from deepreason.runtime.stop import StopController, StopPolicy
from deepreason.scheduler.scheduler import Scheduler, problem_family_key
from deepreason.unification.isolation import lineage_ref_commitment
from deepreason.workloads.models import MandatoryInterface, MandatoryRef, compile_interface
from deepreason.workloads.text import (
    ReasoningWorkloadSpec,
    WorkloadProblem,
    seed_reasoning_workload,
)


def _candidate_response(*values: str) -> str:
    return json.dumps(
        {
            "candidates": [
                {"content": value, "typicality": 0.5}
                for value in values
            ]
        }
    )


def test_scheduler_owns_lineage_and_stable_code_relapse_domain(tmp_path):
    harness = Harness(tmp_path / "run")
    foundation = harness.create_artifact("frozen component input")
    lineage = lineage_ref_commitment([foundation.id])
    harness.register_commitment(lineage)
    problem = harness.register_problem(
        Problem(
            id="code:root",
            description="implement the frozen component",
            criteria=[lineage.id],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(
                [_candidate_response("implementation one", "implementation two")]
            )
        },
        harness.blobs,
    )
    config = Config(
        VS_K=2,
        N_SCHOOLS=0,
        FLOOR=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        NEAR_DUP_EPS=None,
    )

    Scheduler(
        harness, adapter, config, workload_profile="code"
    ).run(1)

    candidates = [
        harness.state.artifacts[artifact_id]
        for artifact_id, problem_id in harness.state.addr
        if problem_id == problem.id
    ]
    assert len(candidates) == 2
    assert all(
        (candidate.id, foundation.id) in harness.state.dep
        for candidate in candidates
    )
    records = [
        json.loads(line)
        for line in (harness.root / "relapse.log.jsonl").read_text().splitlines()
        if json.loads(line).get("type") == "domain"
    ]
    candidate_records = [
        record for record in records
        if record["artifact_id"] in {candidate.id for candidate in candidates}
    ]
    assert len(candidate_records) == 2
    domains = [record["domain"] for record in candidate_records]
    assert {domain["problem_family"] for domain in domains} == {problem.id}
    assert len({domain["component_spec_digest"] for domain in domains}) == 1
    assert all(domain["component_spec_digest"] for domain in domains)
    assert all(
        domain["mandatory_ref_digest"] == domains[0]["mandatory_ref_digest"]
        for domain in domains
    )

    successor = harness.register_problem(
        Problem(
            id="code:successor",
            description="retry the component",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "successor", "from": [candidates[0].id]}
            ),
        )
    )
    assert problem_family_key(harness.state, successor.id) == problem.id


def test_role_aware_mandatory_refs_do_not_promote_memory_to_dependence(harness):
    lineage = harness.create_artifact("lineage")
    memory = harness.create_artifact("contextual memory")
    problem = harness.register_problem(
        Problem(
            id="pi-role-aware",
            description="use lineage and context",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    mandatory = MandatoryInterface(
        refs=(
            MandatoryRef(lineage.id, "dependence"),
            MandatoryRef(memory.id, "mention"),
        )
    )
    interface = compile_interface(
        harness, problem, "candidate", mandatory=mandatory
    )
    candidate = harness.create_artifact(
        "candidate", interface=interface, problem_id=problem.id
    )

    assert (candidate.id, lineage.id) in harness.state.dep
    assert (candidate.id, memory.id) not in harness.state.dep
    assert {(ref.target, ref.role.value) for ref in interface.refs} == {
        (lineage.id, "dependence"),
        (memory.id, "mention"),
    }
    assert mandatory.domain_refs() == (
        f"dependence:{lineage.id}",
        f"mention:{memory.id}",
    )


def test_reasoning_compact_v2_aliases_are_rendered_before_transport(harness):
    memory = harness.create_artifact("accepted contextual evidence")
    problem = seed_reasoning_workload(
        harness,
        ReasoningWorkloadSpec(
            problem=WorkloadProblem(id="reason:aliases", description="Explain X")
        ),
    )
    prompts: list[str] = []

    def respond(prompt: str) -> str:
        prompts.append(prompt)
        return json.dumps(
            {
                "candidates": [
                    {
                        "claim": "X follows",
                        "mechanism": "feedback",
                        "counterconditions": ["feedback reverses"],
                        "typicality": 0.5,
                        "optional_refs": ["A1"],
                        "sidecar": {
                            "search_signal": "productive",
                            "requested_context_aliases": [],
                        },
                    }
                ]
            }
        )

    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(respond)},
        harness.blobs,
        model_profile="compact",
    )
    from deepreason.rules.conj import conj

    artifacts = conj(harness, problem.id, adapter, Config(VS_K=1))
    assert "A1" in prompts[0]
    assert memory.id not in prompts[0]
    assert [(ref.target, ref.role.value) for ref in artifacts[0].interface.refs] == [
        (memory.id, "mention")
    ]


def test_reasoning_slices_before_compiling_counterconditions(harness):
    problem = seed_reasoning_workload(
        harness,
        ReasoningWorkloadSpec(
            problem=WorkloadProblem(id="reason:slice", description="Explain Y")
        ),
    )
    response = json.dumps(
        {
            "candidates": [
                {
                    "claim": f"claim {index}",
                    "mechanism": "mechanism",
                    "counterconditions": [f"counter {index}"],
                    "typicality": 0.5,
                    "optional_refs": [],
                }
                for index in range(3)
            ]
        }
    )
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([response])}, harness.blobs
    )
    from deepreason.rules.conj import conj

    assert len(conj(harness, problem.id, adapter, Config(VS_K=1))) == 1
    assert len(
        [key for key in harness.commitments if key.startswith("reason-counter@")]
    ) == 1


def test_production_conj_pack_uses_sections_and_preserves_mandatory_tail(harness):
    harness.register_commitment(
        Commitment(
            id="k-large",
            eval=(
                "predicate:"
                + "True and " * 300
                + "('MANDATORY_CRITERION_TAIL' == 'MANDATORY_CRITERION_TAIL')"
            ),
        )
    )
    problem = harness.register_problem(
        Problem(
            id="pi-pack-ir",
            description="bounded production renderer",
            criteria=["k-large"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    harness.create_artifact("optional memory " * 1000, problem_id=problem.id)

    pack = render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        vs_k=1,
        token_budget=40,
    )
    assert "## criteria" in pack and "k-large" in pack
    assert "## output-contract" in pack
    assert pack.rstrip().endswith(
        "estimates. Include atypical candidates, not just the modal answer."
    )
    assert len(pack) > 40 * 4  # explicit mandatory overflow, not prefix clipping
    assert "optional memory" not in pack

    prompts: list[str] = []

    def respond(prompt):
        prompts.append(prompt)
        return _candidate_response("candidate")

    from deepreason.rules.conj import conj

    conj(
        harness,
        problem.id,
        LLMAdapter(
            {"conjecturer": MockEndpoint(respond)},
            harness.blobs,
            model_profile="compact",
        ),
        Config(VS_K=1, PACK_TOKEN_BUDGET=40),
    )
    assert "MANDATORY_CRITERION_TAIL" in prompts[0]
    assert "Include atypical candidates" in prompts[0]


def test_verify_root_accepts_independent_v2_profiles(tmp_path):
    root = tmp_path / "run"
    manifest = RunManifest(
        schema_version=2,
        engine_profile="full",
        model_profile="compact",
        workload_profile="text",
        roles={},
        rubric_policy="forbid",
        concurrency=1,
        pack_profile="reasoning.text.v1",
        output_profile="compact.v2",
        source_config_hash="0" * 64,
        compiled_at="2026-07-13T00:00:00Z",
        engine_config_json="{}",
    )
    persist_run_manifest(manifest, root)
    result = verify_root(root)
    assert not [
        violation for violation in result["violations"]
        if violation["check"] == "profile-metadata"
    ]


def test_ops_forwards_manifest_workload_profile(monkeypatch, tmp_path):
    harness = Harness(tmp_path / "run")
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint([_candidate_response("unused")])},
        harness.blobs,
    )
    captured = {}

    class SchedulerSpy:
        def __init__(self, *_args, **kwargs):
            captured.update(kwargs)

        def run(self, cycles, on_cycle=None):
            return {"cycles": cycles}

    monkeypatch.setattr("deepreason.llm.adapter.build_adapter", lambda *_a, **_k: adapter)
    monkeypatch.setattr("deepreason.scheduler.scheduler.Scheduler", SchedulerSpy)
    monkeypatch.setattr("deepreason.run_manifest.preflight_harness", lambda *_a: None)
    monkeypatch.setattr("deepreason.ops.make_embedder", lambda *_a: None)
    monkeypatch.setattr("deepreason.ops.make_research_service", lambda *_a: None)
    manifest = SimpleNamespace(engine_profile="full", workload_profile="formal")

    from deepreason.ops import run_scheduler

    result, _, _ = run_scheduler(
        harness,
        Config(CONTROLLER=False),
        0,
        run_manifest=manifest,
    )
    assert result == {"cycles": 0}
    assert captured["workload_profile"] == "formal"

    legacy = SimpleNamespace(engine_profile="full", workload_profile=None)
    run_scheduler(
        Harness(tmp_path / "legacy-website"),
        Config(CONTROLLER=False),
        0,
        run_manifest=legacy,
    )
    assert captured["workload_profile"] is None

    v2 = SimpleNamespace(
        engine_profile="full",
        workload_profile="text",
        schema_version=2,
        stop_policy={"enabled": False},
    )
    run_scheduler(
        Harness(tmp_path / "v2-stop-policy"),
        Config(CONTROLLER=False),
        0,
        run_manifest=v2,
    )
    assert isinstance(captured["stop_controller"], StopController)
    assert not captured["stop_controller"].policy.enabled

    v3 = SimpleNamespace(
        engine_profile="full",
        workload_profile="text",
        schema_version=3,
        stop_policy={"enabled": False},
    )
    run_scheduler(
        Harness(tmp_path / "v3-stop-policy"),
        Config(CONTROLLER=False),
        0,
        run_manifest=v3,
    )
    assert isinstance(captured["stop_controller"], StopController)
    assert not captured["stop_controller"].policy.enabled

    v6 = SimpleNamespace(
        engine_profile="full",
        workload_profile="text",
        schema_version=6,
        stop_policy={"enabled": False},
    )
    run_scheduler(
        Harness(tmp_path / "v6-stop-policy"),
        Config(CONTROLLER=False),
        0,
        run_manifest=v6,
    )
    assert isinstance(captured["stop_controller"], StopController)
    assert not captured["stop_controller"].policy.enabled


def test_scheduler_stop_controller_stops_only_after_sustained_convergence(tmp_path):
    harness = Harness(tmp_path / "converged")
    progress = ProgressSink(
        harness.root, run_id="convergence-test", workload="text"
    )
    scheduler = Scheduler(
        harness,
        LLMAdapter({}, harness.blobs),
        Config(N_SCHOOLS=0),
        stop_controller=StopController(
            StopPolicy(min_cycles=1, window=2, stable_windows=2)
        ),
        progress_sink=progress,
    )

    def quiet_step():
        scheduler._cycles += 1

    scheduler.step = quiet_step
    report = scheduler.run(10)

    assert scheduler._cycles == 3
    assert scheduler.last_stop_decision.reason == "converged"
    assert report["stop_reason"] == "converged"
    assert (harness.root / "run-stop.json").exists()
    assert progress.read_since(-1)[-1].stop_reason == "converged"


def test_scheduler_stuck_signal_alone_cannot_stop(tmp_path):
    harness = Harness(tmp_path / "stuck-only")
    scheduler = Scheduler(
        harness,
        LLMAdapter({}, harness.blobs),
        Config(N_SCHOOLS=0),
        stop_controller=StopController(
            StopPolicy(
                min_cycles=100,
                window=2,
                stable_windows=99,
                stuck_signal_window=2,
                escape_attempts=0,
            )
        ),
    )

    def stuck_step():
        scheduler.diagnostics.append({"search_signal": "stuck"})
        scheduler._cycles += 1

    scheduler.step = stuck_step
    scheduler.run(5)

    assert scheduler._cycles == 5
    assert scheduler.last_stop_decision is not None
    assert not scheduler.last_stop_decision.stop
    assert not (harness.root / "run-stop.json").exists()
