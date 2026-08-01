"""Protocol invariants for the positive-headroom TSP jolt pilot v3.1."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from deepreason.config import Config
from deepreason.experiments.jolt_tsp import (
    J3_PREFIX,
    J4_PREFIX,
    J6_DIRECTIVE,
    MOVEMENT_DIRECTIVE,
    Checkpoint,
    branch_order,
    brute_force,
    calibration_thresholds,
    canonical_tour,
    edge_set,
    generate_instance,
    held_karp,
    retained_edge_fraction,
    score_feedback,
    treatment_context,
    trigger_window,
)
from deepreason.harness import Harness
from deepreason.jolts import root_state_digest
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance
from deepreason.rules.conj import conj


ROOT = Path(__file__).resolve().parents[1]
CAL_INSTANCES = ROOT / "experiments" / "jolt_positive_headroom_v3_1_calibration_instances.json"
EXP_INSTANCES = ROOT / "experiments" / "jolt_positive_headroom_v3_1_instances.json"
OPTIMA = ROOT / "experiments" / "jolt_positive_headroom_v3_1_optima.json"


def _history(instance: dict) -> list[dict]:
    tours = [
        tuple(str(index) for index in range(14)),
        ("0", "2", "1", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"),
    ]
    return [
        {
            "valid": True,
            "admission_id": f"call-0{index}-candidate-00",
            "canonical_tour": list(canonical_tour(tour)),
            "edges": [list(edge) for edge in sorted(edge_set(tour), key=lambda item: (int(item[0]), int(item[1])))],
            "distance": 1000 - index,
            "call_index": index,
            "gate_blocked": False,
        }
        for index, tour in enumerate(tours)
    ]


def test_instance_cohorts_are_frozen_and_disjoint():
    calibration = json.loads(CAL_INSTANCES.read_text())
    experimental = json.loads(EXP_INSTANCES.read_text())
    assert calibration["seeds"] == [20260701, 20260702, 20260703]
    assert experimental["seeds"] == list(range(20260715, 20260723))
    assert set(calibration["seeds"]).isdisjoint(experimental["seeds"])
    assert calibration["instances"] == [generate_instance(seed) for seed in calibration["seeds"]]
    assert experimental["instances"] == [generate_instance(seed) for seed in experimental["seeds"]]


def test_held_karp_matches_brute_force_on_small_instance():
    small = {
        "seed": 1,
        "cities": [
            {"id": str(index), "x": x, "y": y}
            for index, (x, y) in enumerate(
                ((0, 0), (1, 3), (4, 2), (5, 7), (8, 1), (3, 9), (9, 9))
            )
        ],
    }
    certificate = held_karp(small)
    brute_distance, brute_tour = brute_force(small)
    assert certificate["exact_distance"] == brute_distance
    assert tuple(certificate["canonical_optimal_tour"]) == brute_tour


def test_sealed_optima_recompute_exactly():
    optima = json.loads(OPTIMA.read_text())
    instances = {}
    for path in (CAL_INSTANCES, EXP_INSTANCES):
        instances.update({row["seed"]: row for row in json.loads(path.read_text())["instances"]})
    assert optima["sealed_from_conjecturer"] is True
    for row in optima["certificates"]:
        recomputed = held_karp(instances[row["seed"]])
        assert row["exact_distance"] == recomputed["exact_distance"]
        assert row["canonical_optimal_tour"] == recomputed["canonical_optimal_tour"]
        assert row["certificate_sha256"] == recomputed["certificate_sha256"]


def test_tour_canonicalisation_and_duplicate_admission_rule():
    tour = tuple(str(index) for index in range(14))
    reverse = ("0", *reversed(tour[1:]))
    assert canonical_tour(tour) == canonical_tour(reverse)
    rows = [
        {"valid": True, "canonical": canonical_tour(tour), "duplicate": False, "functional": True},
        {"valid": True, "canonical": canonical_tour(reverse), "duplicate": True, "functional": False},
    ]
    assert sum(row["valid"] for row in rows) == 2
    assert len({row["canonical"] for row in rows}) == 1
    assert sum(not row["duplicate"] for row in rows) == 1
    assert sum(row["functional"] for row in rows) == 1


def test_retained_incumbent_edge_fraction_is_undirected_over_14():
    incumbent = tuple(str(index) for index in range(14))
    two_opt = ("0", "2", "1", *tuple(str(index) for index in range(3, 14)))
    expected = len(edge_set(incumbent) & edge_set(two_opt)) / 14
    assert retained_edge_fraction(two_opt, incumbent) == expected
    assert retained_edge_fraction(incumbent, incumbent) == 1.0


def test_score_feedback_is_identical_and_arm_treatments_are_pure():
    instance = generate_instance(20260715)
    history = _history(instance)
    incumbent = tuple(history[-1]["canonical_tour"])
    prompts = {
        arm: treatment_context(
            arm,
            instance=instance,
            history=history,
            incumbent=incumbent,
            median_retained=0.625,
            failure_classes=[],
        )
        for arm in ("J0", "J1", "J3", "J4", "J6")
    }
    feedback = score_feedback(history)
    assert all(prompt.startswith(feedback + "\n\n") for prompt in prompts.values())
    assert "tour=" not in feedback and "total_distance=" in feedback
    assert all(prompts[arm].count(MOVEMENT_DIRECTIVE) == 1 for arm in ("J1", "J3", "J4"))
    assert MOVEMENT_DIRECTIVE not in prompts["J0"] and MOVEMENT_DIRECTIVE not in prompts["J6"]
    assert "at least two edges" in MOVEMENT_DIRECTIVE
    assert J3_PREFIX in prompts["J3"] and J4_PREFIX in prompts["J4"]
    assert J6_DIRECTIVE in prompts["J6"]
    assert "longest" not in prompts["J3"].casefold()
    assert "--" not in prompts["J4"]
    assert "exact_optimal" not in prompts["J4"] and "gap" not in prompts["J4"].casefold()
    assert "INCUMBENT UNDIRECTED EDGES" not in prompts["J4"]


def test_j3_incumbent_edges_are_lexicographic_not_length_ordered():
    instance = generate_instance(20260715)
    history = _history(instance)
    incumbent = tuple(history[-1]["canonical_tour"])
    prompt = treatment_context(
        "J3", instance=instance, history=history, incumbent=incumbent,
        median_retained=0.7, failure_classes=[],
    )
    section = prompt.split("INCUMBENT UNDIRECTED EDGES (lexicographic endpoint order):\n", 1)[1]
    lines = section.split("\n\n", 1)[0].splitlines()
    pairs = [tuple(map(int, line.removeprefix("- ").split("--"))) for line in lines]
    assert pairs == sorted(pairs)


def test_trigger_requires_positive_headroom_and_disjoint_past_window():
    incumbent = tuple(str(index) for index in range(14))
    history = []
    for index in range(12):
        history.append({
            "valid": True,
            "admission_id": f"a-{index}",
            "canonical_tour": list(incumbent),
            "edges": [list(edge) for edge in edge_set(incumbent)],
            "distance": 500 if index < 4 else 500,
            "call_index": index,
            "gate_blocked": False,
        })
    eligible = trigger_window(
        history, incumbent=incumbent, optimum=400, r_med=0.6, r_low=0.35,
        successful_calls=12,
    )
    assert eligible["eligible"] is True
    complete = trigger_window(
        history, incumbent=incumbent, optimum=500, r_med=0.6, r_low=0.35,
        successful_calls=12,
    )
    assert complete["eligible"] is False and complete["certified_completion"] is True
    blocked = trigger_window(
        history, incumbent=incumbent, optimum=400, r_med=0.6, r_low=0.35,
        successful_calls=12, hard_orbit_blocks=1,
    )
    assert blocked["eligible"] is False


def test_calibration_rejects_improvement_window_fires():
    incumbent = tuple(str(index) for index in range(14))
    base = [
        {
            "valid": True, "canonical_tour": list(incumbent), "distance": 500,
            "call_index": index, "gate_blocked": False,
        }
        for index in range(12)
    ]
    result = calibration_thresholds([list(base), list(base), list(base)], optima=[400, 400, 400])
    assert result is not None and result["fired_instances"] == 3
    improving = [dict(row) for row in base]
    improving[-1]["distance"] = 450
    assert calibration_thresholds([improving, improving, list(base)], optima=[400, 400, 400]) is None


def test_randomisation_encoding_and_checkpoint_budget_are_exact():
    seed = 20260715
    source = "a" * 64
    prereg = "b" * 64
    seed_hex = hashlib.sha256(f"{seed}:{source}:{prereg}".encode("utf-8")).hexdigest()
    expected = ["J0", "J1", "J3", "J4", "J6"]
    random.Random(int(seed_hex, 16)).shuffle(expected)
    assert branch_order(seed, source, prereg) == tuple(expected)
    checkpoint = Checkpoint(
        instance_seed=seed, source_state_digest=source,
        incumbent=tuple(str(index) for index in range(14)),
        history_digest="c" * 64, remaining_calls=5, remaining_tokens=35000,
    )
    assert checkpoint.payload()["remaining_calls"] == 5
    assert checkpoint.payload()["remaining_tokens"] == 35000
    assert checkpoint.payload()["pending_queues"] == []


def test_matched_copy_state_digest_and_measure_action_are_status_neutral(tmp_path):
    source = tmp_path / "source"
    harness = Harness(source)
    harness.register_commitment(Commitment(id="k", eval="predicate:True"))
    harness.register_problem(Problem(
        id="p", description="fixture", criteria=["k"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    before = root_state_digest(source)
    branch = tmp_path / "branch"
    import shutil
    shutil.copytree(source, branch)
    assert root_state_digest(branch) == before
    status_before = dict(Harness(branch).state.status)
    branch_harness = Harness(branch)
    branch_harness.record_measure(inputs=["jolt-tsp-action-v3.1", json.dumps({"arm": "J3"})])
    assert dict(branch_harness.state.status) == status_before
    assert not branch_harness.warrants and not branch_harness.state.att


def test_opt_in_candidate_capture_preserves_default_diagnostics(tmp_path):
    def response(_prompt):
        return json.dumps({"candidates": [{"content": "hello", "typicality": 0.5}]})

    def run(capture: bool):
        harness = Harness(tmp_path / ("capture" if capture else "default"))
        harness.register_commitment(Commitment(id="k", eval="predicate:True"))
        harness.register_problem(Problem(
            id="p", description="fixture", criteria=["k"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        ))
        adapter = LLMAdapter({"conjecturer": MockEndpoint(response)}, harness.blobs)
        diagnostics = []
        conj(
            harness, "p", adapter, Config(VS_K=1), diagnostics,
            capture_candidate_content=capture,
        )
        return diagnostics[0]

    default = run(False)
    captured = run(True)
    assert set(default) == {"candidate", "gate", "search_signal"}
    assert captured["candidate_content"] == "hello"
    assert len(captured["artifact_id"]) == 64


def test_prior_pilot_records_are_byte_unchanged():
    expected = {
        "experiments/jolt_trigger_glm52_pilot_v2_prereg.yaml": "d2a24f0895204d93388e9dff3ee28288ee41c77eb185c3ec2bd0052d0cf3a0d5",
        "experiments/results/jolt_trigger_glm52_pilot_v2_report.json": "ea563f00fc0e60b776d4700a694f74a042b321034538140cd7d75bd0c56f07c9",
        "experiments/results/jolt_trigger_glm52_pilot_v2_forensic_addendum.json": "444fac8d702e5757152c422f1b76b47683542b1270cdbf9a04ac9a7e20acd70f",
        "experiments/jolt_trigger_glm52_pilot_prereg.yaml": "29460a9ac3fdbdb73e3b3ca0ca11f97ce813a87195b3b5b5b84ea8bfec088bbe",
        "experiments/results/jolt_trigger_glm52_pilot_report.json": "c481f0bf85deea1926d4250d9ae6c27710a979729d0e4421561df68e22ff77df",
    }
    for relative, digest in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest


def test_frozen_budget_arithmetic_and_zero_adjudicator_roles():
    assert 3 * 32 + 8 * 32 + 8 * 5 * 5 == 552
    config = Config.model_validate({
        "ARG_CRIT_PER_CYCLE": 0,
        "RUBRIC_TRIALS_PER_ARTIFACT": 0,
        "ADVISORY_TRIALS_PER_CYCLE": 0,
        "RESEARCH_BACKEND": None,
        "CONTROLLER": False,
        "roles": {"conjecturer": {"endpoint": "mock://only", "model": "fixture"}},
    })
    assert set(config.roles) == {"conjecturer"}
    assert config.RUBRIC_TRIALS_PER_ARTIFACT == 0
    assert config.ADVISORY_TRIALS_PER_CYCLE == 0
