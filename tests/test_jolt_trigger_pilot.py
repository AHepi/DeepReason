"""Deterministic acceptance tests for the status-neutral jolt pilot surface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.jolts import (
    BRANCH_MANIFEST_NAME,
    JoltAction,
    JoltArm,
    JoltDiagnosis,
    JoltError,
    PublicVerifierFailure,
    build_jolt_action,
    materialize_matched_branches,
    plan_matched_branches,
    preflight_pilot_runtime,
    problem_for_post_trigger_call,
    record_false_trigger_sample,
    record_jolt_action,
    root_state_digest,
)
from deepreason.llm.packs import render_conj_pack
from deepreason.ontology import (
    Commitment,
    LLMCall,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
    Status,
)
from deepreason.run_manifest import Route, RunManifest
from deepreason.scheduler.scheduler import Scheduler
from deepreason.views.jolt_signals import (
    Diagnosis,
    FunctionalObservation,
    JoltSignalError,
    StatusSource,
    VerifierMetric,
    VerifierMetricKind,
    diagnose,
    functional_observations,
    hard_orbit_snapshot,
    record_functional_observation,
    require_embedder_fingerprint,
    soft_exhaustion_snapshot,
)


_FP = {
    "model": "nomic-ai/nomic-embed-text-v1.5",
    "version": "fastembed-0.8.0+onnxruntime-1.27.0",
    "sentinel": "d6e3599ce0377000",
}
_DIGEST = "a" * 64


class _PilotEmbedder:
    """Orthogonal early vectors and one repeated late vector."""

    model = _FP["model"]

    def fingerprint(self):
        return dict(_FP)

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * 20
        if text.startswith("early-"):
            index = int(text.split("-", 1)[1])
            vector[index] = 1.0
        elif text.startswith("late-"):
            vector[0] = 1.0
        else:
            vector[-1] = 1.0
        return vector


def _problem(harness: Harness, problem_id: str) -> Problem:
    harness.register_commitment(
        Commitment(id=f"k-{problem_id}", eval="predicate:len(content) > 0")
    )
    return harness.register_problem(
        Problem(
            id=problem_id,
            description=f"deterministic task {problem_id}",
            criteria=[f"k-{problem_id}"],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _call(harness: Harness, *, tokens: int = 100) -> LLMCall:
    return LLMCall(
        role="conjecturer",
        model="fixture-model",
        endpoint="mock://fixture",
        prompt_ref=harness.blobs.put(b"fixture prompt"),
        raw_ref=harness.blobs.put(b"fixture raw"),
        tokens=tokens,
    )


def _completed_candidate(
    harness: Harness,
    problem_id: str,
    content: str,
    *,
    school: str | None = None,
    tokens: int = 100,
):
    harness.record_measure(inputs=["cycle", str(harness._next_seq), problem_id])
    return harness.create_artifact(
        content,
        problem_id=problem_id,
        provenance=Provenance(
            role="conjecturer", school=school, event_seq=harness._next_seq
        ),
        rule=Rule.CONJ,
        llm=_call(harness, tokens=tokens),
    )


def _hard_root(root: Path) -> tuple[Harness, str]:
    from tests.conftest import attack

    harness = Harness(root)
    _problem(harness, "pi-hard")
    attractor = _completed_candidate(
        harness, "pi-hard", "refuted attractor", school="school-0"
    )
    attack(harness, attractor.id, "hard-orbit-fixture")
    assert harness.state.status[attractor.id] == Status.REFUTED
    for index in range(10):
        harness.record_measure(inputs=["cycle", str(index), "pi-hard"])
        harness.record_measure(
            inputs=[
                f"gate:battery-equivalent (~=_B) to refuted {attractor.id[:12]}",
                f"blocked-{index}",
                "pi-hard",
            ]
        )
        harness.record_measure(inputs=["conj-noregister"], llm=_call(harness, tokens=80))
    return harness, attractor.id


def _observation(
    candidate_id: str,
    *,
    problem_id: str,
    functional: bool,
    mechanism: str,
    metric: VerifierMetric | None = None,
    semantic_report: float | None = None,
) -> FunctionalObservation:
    return FunctionalObservation(
        candidate_id=candidate_id,
        problem_id=problem_id,
        problem_family=problem_id,
        domain="finite",
        evaluator_id="fixture-exhaustive-enumerator-v1",
        evaluator_fingerprint="e" * 64,
        admitted=True,
        functional_novelty=functional,
        mechanism_class=mechanism,
        verifier_metric=metric,
        semantic_novelty=semantic_report,
        status_source=StatusSource.DETERMINISTIC,
    )


def _soft_root(
    root: Path, *, new_late_mechanism: bool = False, improve_late: bool = False
) -> Harness:
    harness = Harness(root)
    _problem(harness, "pi-soft")
    for index in range(17):
        early = index < 9
        candidate = _completed_candidate(
            harness,
            "pi-soft",
            f"{'early' if early else 'late'}-{index if early else index - 9}",
        )
        mechanism = "base"
        if new_late_mechanism and index == 16:
            mechanism = "new-mechanism"
        metric = None
        if improve_late and index == 16:
            metric = VerifierMetric(
                name="exhaustive coverage",
                kind=VerifierMetricKind.COVERAGE,
                before=8,
                after=9,
                delta=1,
                unit="cases",
                source_receipt="f" * 64,
            )
        record_functional_observation(
            harness,
            _observation(
                candidate.id,
                problem_id="pi-soft",
                functional=early,
                mechanism=mechanism,
                metric=metric,
                # A deliberately misleading report value proves the trigger
                # recomputes geometry instead of trusting an outcome sidecar.
                semantic_report=99.0 if not early else 0.0,
            ),
        )
    return harness


def test_hard_orbit_is_replay_derived_and_deterministic(tmp_path):
    harness, target_id = _hard_root(tmp_path / "run")

    first = hard_orbit_snapshot(harness)
    replayed = hard_orbit_snapshot(Harness(tmp_path / "run"))

    assert first == replayed
    assert first.sufficient_data and first.trigger
    assert first.gate_block_count == 10
    assert first.empty_cycle_count == 10
    assert first.no_register_rate == 1.0
    assert first.blocked_target_concentration == 1.0
    assert first.blocked_lineage_concentration == 1.0
    assert first.same_problem_family_block_share == 1.0
    assert first.refuted_attractor_present
    assert first.concentrated_target_id == target_id
    assert first.tokens_per_admitted_candidate is None
    assert len(first.source_event_seqs) == 20


def test_verifier_improvement_prevents_hard_trigger(tmp_path):
    harness, target_id = _hard_root(tmp_path / "run")
    record_functional_observation(
        harness,
        _observation(
            target_id,
            problem_id="pi-hard",
            functional=True,
            mechanism="new-invariant",
            metric=VerifierMetric(
                name="withheld tests",
                kind=VerifierMetricKind.TEST_SCORE,
                before=4,
                after=5,
                delta=1,
                unit="tests",
                source_receipt="f" * 64,
            ),
        ),
    )

    snapshot = hard_orbit_snapshot(harness)
    assert snapshot.verifier_improvement_count == 1
    assert not snapshot.trigger


def test_soft_exhaustion_uses_nonoverlapping_within_run_ratio(tmp_path):
    harness = _soft_root(tmp_path / "run")

    snapshot = soft_exhaustion_snapshot(
        harness,
        problem_family="pi-soft",
        embedder=_PilotEmbedder(),
        expected_embedder_fingerprint=_FP,
    )

    assert snapshot.sufficient_data and snapshot.trigger
    assert snapshot.early_novelty_median == 1.0
    assert snapshot.recent_novelty_median == 0.0
    assert snapshot.late_early_novelty_ratio == 0.0
    assert snapshot.within_run_normalised_semantic_novelty == (0.0,) * 8
    assert snapshot.mechanism_class_discovery_rate == 0.0
    assert snapshot.new_executable_commitment_rate == 0.0
    assert snapshot.verifier_improvement_count == 0
    assert snapshot.semantic_cluster_growth_without_functional_growth == 1.0
    assert snapshot.problem_age == 17
    # The sidecar claimed 99.0; it is report data and did not drive the ratio.
    assert functional_observations(harness)[-1].observation.semantic_novelty == 99.0


@pytest.mark.parametrize("variant", ["mechanism", "verifier"])
def test_soft_trigger_requires_functional_and_verifier_stall(tmp_path, variant):
    harness = _soft_root(
        tmp_path / variant,
        new_late_mechanism=variant == "mechanism",
        improve_late=variant == "verifier",
    )
    snapshot = soft_exhaustion_snapshot(
        harness,
        problem_family="pi-soft",
        embedder=_PilotEmbedder(),
        expected_embedder_fingerprint=_FP,
    )
    assert snapshot.sufficient_data
    assert not snapshot.trigger


def test_hard_and_soft_diagnoses_are_separate(tmp_path):
    hard_harness, _ = _hard_root(tmp_path / "hard")
    soft_harness = _soft_root(tmp_path / "soft")
    soft = soft_exhaustion_snapshot(
        soft_harness,
        problem_family="pi-soft",
        embedder=_PilotEmbedder(),
        expected_embedder_fingerprint=_FP,
    )
    soft_hard_view = hard_orbit_snapshot(soft_harness)
    result = diagnose(soft_hard_view, soft)
    assert result.diagnosis == Diagnosis.SOFT_EXHAUSTION

    hard = hard_orbit_snapshot(hard_harness)
    insufficient_soft = soft.model_copy(
        update={"sufficient_data": False, "trigger": False}
    )
    assert diagnose(hard, insufficient_soft).diagnosis == Diagnosis.HARD_ORBIT


def test_embedder_evidence_mode_fails_closed():
    require_embedder_fingerprint(_PilotEmbedder(), _FP)
    with pytest.raises(JoltSignalError, match="JOLT_EMBEDDER_FINGERPRINT_MISMATCH"):
        require_embedder_fingerprint(
            _PilotEmbedder(), {**_FP, "sentinel": "different"}
        )
    with pytest.raises(JoltSignalError, match="JOLT_EMBEDDER_UNAVAILABLE"):
        require_embedder_fingerprint(None, _FP)


def test_functional_receipt_is_measure_only_and_rejects_prose_source(tmp_path):
    harness = Harness(tmp_path / "run")
    _problem(harness, "pi")
    candidate = _completed_candidate(harness, "pi", "candidate")
    before = harness.state.model_dump(mode="json")

    event = record_functional_observation(
        harness,
        _observation(
            candidate.id,
            problem_id="pi",
            functional=True,
            mechanism="enumeration",
        ),
    )

    assert event.rule == Rule.MEASURE
    assert not event.outputs
    assert not event.state_diff.att_add
    assert not event.state_diff.dep_add
    assert not event.state_diff.status_changed
    assert harness.state.model_dump(mode="json") == before
    assert not harness.warrants
    with pytest.raises(ValidationError):
        FunctionalObservation.model_validate(
            {
                **_observation(
                    candidate.id,
                    problem_id="pi",
                    functional=False,
                    mechanism="same",
                ).model_dump(mode="json", by_alias=True),
                "status_source": "rubric",
            }
        )


def test_jolt_actions_are_typed_status_neutral_and_have_no_authority_fields(tmp_path):
    harness = Harness(tmp_path / "run")
    _problem(harness, "pi")
    action = build_jolt_action(
        JoltArm.J1,
        diagnosis=JoltDiagnosis.HARD_ORBIT,
        original_problem_id="pi",
        current_stance="mechanism-first",
    )
    before = harness.state.model_dump(mode="json")
    artifacts_before = set(harness.state.artifacts)

    event = record_jolt_action(harness, action)

    assert event.rule == Rule.MEASURE
    assert harness.state.model_dump(mode="json") == before
    assert set(harness.state.artifacts) == artifacts_before
    assert not harness.warrants and not harness.state.att
    assert "counterexample-first" in action.prompt_context
    with pytest.raises(ValidationError):
        JoltAction.model_validate(
            {
                **action.model_dump(mode="json", by_alias=True),
                "status": "accepted",
            }
        )


def test_stance_suppression_is_limited_to_the_refuted_lineage(tmp_path):
    harness, target_id = _hard_root(tmp_path / "run")
    same_lineage = harness.create_artifact(
        "accepted alternative",
        problem_id="pi-hard",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    other_lineage = harness.create_artifact(
        "unrelated accepted alternative",
        problem_id="pi-hard",
        provenance=Provenance(role="conjecturer", school="school-1"),
    )
    safe = build_jolt_action(
        JoltArm.J1,
        diagnosis=JoltDiagnosis.HARD_ORBIT,
        original_problem_id="pi-hard",
        current_stance="mechanism-first",
        refuted_target_id=target_id,
        suppressed_artifact_ids=(same_lineage.id,),
    )
    record_jolt_action(harness, safe)
    unsafe = build_jolt_action(
        JoltArm.J1,
        diagnosis=JoltDiagnosis.HARD_ORBIT,
        original_problem_id="pi-hard",
        current_stance="mechanism-first",
        refuted_target_id=target_id,
        suppressed_artifact_ids=(other_lineage.id,),
    )
    with pytest.raises(JoltError, match="JOLT_SUPPRESSED_EXEMPLAR_LINEAGE_MISMATCH"):
        record_jolt_action(harness, unsafe)


def test_problem_turnover_has_fixed_return_schedule():
    action = build_jolt_action(
        JoltArm.J2,
        diagnosis=JoltDiagnosis.HARD_ORBIT,
        original_problem_id="original",
        related_problem_id="restricted",
    )
    assert [problem_for_post_trigger_call(action, index) for index in range(5)] == [
        "restricted",
        "restricted",
        "original",
        "original",
        "original",
    ]


def test_representation_and_public_verifier_jolts_do_not_smuggle_outcomes():
    reset = build_jolt_action(
        JoltArm.J3,
        diagnosis=JoltDiagnosis.SOFT_EXHAUSTION,
        original_problem_id="pi",
        domain="code",
    )
    assert "state, invariant, transition" in reset.prompt_context
    failure = PublicVerifierFailure(
        label="duplicate-input cases",
        source_receipt="b" * 64,
    )
    challenge = build_jolt_action(
        JoltArm.J4,
        diagnosis=JoltDiagnosis.SOFT_EXHAUSTION,
        original_problem_id="pi",
        public_failures=(failure,),
    )
    assert "duplicate-input cases" in challenge.prompt_context
    with pytest.raises(ValidationError, match="JOLT_VERIFIER_OUTCOME_LEAKAGE"):
        PublicVerifierFailure(
            label="withheld test input [1, 2]",
            source_receipt="b" * 64,
        )


@pytest.mark.parametrize("arm", [JoltArm.J5, JoltArm.J7])
def test_contaminating_or_nonidentifiable_arms_are_deferred(arm):
    with pytest.raises(JoltError, match="JOLT_ARM_DEFERRED"):
        build_jolt_action(
            arm,
            diagnosis=JoltDiagnosis.SOFT_EXHAUSTION,
            original_problem_id="pi",
        )


def test_pack_overlay_suppresses_only_displayed_exemplar(tmp_path):
    harness = Harness(tmp_path / "run")
    problem = _problem(harness, "pi")
    exemplar = harness.create_artifact("modal exemplar", problem_id="pi")
    default = render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        vs_k=1,
        token_budget=1000,
    )
    jolted = render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        vs_k=1,
        token_budget=1000,
        generation_context="use a different state representation",
        suppressed_exemplars=(exemplar.id,),
    )
    assert exemplar.id in default
    assert exemplar.id not in jolted
    assert "use a different state representation" in jolted
    assert harness.state.status[exemplar.id] == Status.ACCEPTED


def test_capture_flags_can_be_observed_without_actuating_ladder(
    tmp_path, monkeypatch
):
    harness = Harness(tmp_path / "run")
    scheduler = Scheduler(
        harness,
        object(),
        Config(N_SCHOOLS=0),
        capture_responses=False,
    )
    monkeypatch.setattr(
        "deepreason.scheduler.scheduler.detection.raw_flags",
        lambda *_args: {"attractor_orbiting": True},
    )
    monkeypatch.setattr(
        "deepreason.scheduler.scheduler.ladder.respond",
        lambda *_args: pytest.fail("capture response actuated"),
    )
    state_before = harness.state.model_dump(mode="json")

    scheduler._capture_step()
    scheduler._capture_step()

    assert scheduler.diagnostics[-1] == {
        "cycle": 0,
        "flags": ["attractor_orbiting"],
        "responses": [],
        "observed_only": True,
    }
    assert harness.state.model_dump(mode="json") == state_before


def _branch_source(root: Path) -> Harness:
    harness = Harness(root)
    original = _problem(harness, "pi-original")
    harness.register_problem(
        Problem(
            id="pi-related",
            description="pre-existing restricted successor",
            criteria=list(original.criteria),
            provenance=ProblemProvenance.model_validate(
                {"trigger": "successor", "from": [original.id]}
            ),
        )
    )
    return harness


def _hard_plan(root: Path, seed: str = "branch-order-seed"):
    return plan_matched_branches(
        root,
        arms=(JoltArm.J0, JoltArm.J1, JoltArm.J2, JoltArm.J6),
        diagnosis=JoltDiagnosis.HARD_ORBIT,
        original_problem_id="pi-original",
        related_problem_id="pi-related",
        branch_order_seed=seed,
        experiment_manifest_plan_digest="1" * 64,
        run_manifest_digest="2" * 64,
        route_matrix_digest="3" * 64,
        verifier_fingerprint="4" * 64,
        functional_evaluator_fingerprint="5" * 64,
        embedder_fingerprint=_FP,
        trigger_receipt_digest="6" * 64,
    )


def test_matched_branches_start_identical_with_equal_budgets_and_j0(tmp_path):
    _branch_source(tmp_path / "source")
    plan = _hard_plan(tmp_path / "source")
    assert plan == _hard_plan(tmp_path / "source")
    assert {branch.arm for branch in plan.branches} == {
        JoltArm.J0,
        JoltArm.J1,
        JoltArm.J2,
        JoltArm.J6,
    }
    assert len({branch.budget for branch in plan.branches}) == 1

    roots = materialize_matched_branches(plan, tmp_path / "branches")

    assert len(roots) == 4
    assert {root_state_digest(root) for root in roots} == {plan.source_state_digest}
    manifests = [json.loads((root / BRANCH_MANIFEST_NAME).read_text()) for root in roots]
    assert {manifest["arm"] for manifest in manifests} >= {"J0"}
    assert len({json.dumps(manifest["budget"], sort_keys=True) for manifest in manifests}) == 1
    assert all(not manifest["exact_counterfactual_replay_claimed"] for manifest in manifests)


def test_branch_freeze_fails_if_source_advances(tmp_path):
    harness = _branch_source(tmp_path / "source")
    plan = _hard_plan(tmp_path / "source")
    harness.record_measure(inputs=["jolt-false-trigger", "advanced"])
    with pytest.raises(JoltError, match="JOLT_SOURCE_STATE_ADVANCED"):
        materialize_matched_branches(plan, tmp_path / "branches")


def test_branch_digest_includes_anti_relapse_operational_state(tmp_path):
    _branch_source(tmp_path / "source")
    plan = _hard_plan(tmp_path / "source")
    (tmp_path / "source" / "relapse.log.jsonl").write_text(
        '{"type":"domain","artifact_id":"changed"}\n'
    )
    with pytest.raises(JoltError, match="JOLT_SOURCE_STATE_ADVANCED"):
        materialize_matched_branches(plan, tmp_path / "branches")


def test_problem_turnover_rejects_an_unrelated_preexisting_problem(tmp_path):
    source = tmp_path / "source"
    harness = Harness(source)
    _problem(harness, "pi-original")
    _problem(harness, "pi-unrelated")
    with pytest.raises(JoltError, match="JOLT_RELATED_PROBLEM_FAMILY_MISMATCH"):
        plan_matched_branches(
            source,
            arms=(JoltArm.J0, JoltArm.J1, JoltArm.J2, JoltArm.J6),
            diagnosis=JoltDiagnosis.HARD_ORBIT,
            original_problem_id="pi-original",
            related_problem_id="pi-unrelated",
            branch_order_seed="seed",
            experiment_manifest_plan_digest="1" * 64,
            run_manifest_digest="2" * 64,
            route_matrix_digest="3" * 64,
            verifier_fingerprint="4" * 64,
            functional_evaluator_fingerprint="5" * 64,
            embedder_fingerprint=_FP,
            trigger_receipt_digest="6" * 64,
        )


def test_false_trigger_sample_is_status_inert(tmp_path):
    harness = Harness(tmp_path / "run")
    before = harness.state.model_dump(mode="json")
    event = record_false_trigger_sample(
        harness,
        state_digest="a" * 64,
        diagnosis_arm_set="soft_exhaustion",
        sample_seed="seed-1",
    )
    assert event.rule == Rule.MEASURE
    assert harness.state.model_dump(mode="json") == before


def _manifest(*, judge: bool = False) -> RunManifest:
    route = Route(
        endpoint_id="fixture",
        base_url="https://ollama.invalid/v1",
        model_id="fixture-model",
        provider="ollama",
        family="fixture-family",
        api_key_env="OLLAMA_API_KEY",
    )
    roles = {"conjecturer": (route,)}
    if judge:
        roles["judge"] = (route,)
    return RunManifest(
        schema_version=2,
        engine_profile="full",
        model_profile="standard",
        workload_profile="code",
        roles=roles,
        rubric_policy="forbid",
        concurrency=1,
        pack_profile="fixture.pack.v1",
        output_profile="fixture.output.v1",
        source_config_hash="0" * 64,
        compiled_at="2026-07-14T00:00:00Z",
        engine_config_json="{}",
    )


def _pilot_config(**updates) -> Config:
    values = dict(
        ARG_CRIT_PER_CYCLE=0,
        RUBRIC_TRIALS_PER_ARTIFACT=0,
        ADVISORY_TRIALS_PER_CYCLE=0,
        PROP_PROPOSE_PERIOD=0,
        VISION_CRIT_PER_CYCLE=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        RESEARCH_BACKEND=None,
        EMBEDDER_FAILURE_POLICY="error",
    )
    values.update(updates)
    return Config(**values)


def test_pilot_preflight_enforces_zero_judge_budget_and_status_neutrality():
    receipt = preflight_pilot_runtime(
        manifest=_manifest(),
        config=_pilot_config(),
        embedder=_PilotEmbedder(),
        expected_embedder_fingerprint=_FP,
        preregistration_digest=_DIGEST,
        committed_preregistration_digest=_DIGEST,
        workload_receipt_digests=("b" * 64,),
        capture_responses=False,
        controller_present=False,
    )
    assert receipt.judge_tokens == 0
    assert receipt.manifest_digest == _manifest().sha256

    with pytest.raises(JoltError, match="JOLT_ADVISORY_BUDGET_NONZERO"):
        preflight_pilot_runtime(
            manifest=_manifest(),
            config=_pilot_config(ADVISORY_TRIALS_PER_CYCLE=1),
            embedder=_PilotEmbedder(),
            expected_embedder_fingerprint=_FP,
            preregistration_digest=_DIGEST,
            committed_preregistration_digest=_DIGEST,
            workload_receipt_digests=("b" * 64,),
            capture_responses=False,
            controller_present=False,
        )
    with pytest.raises(JoltError, match="JOLT_JUDGE_ROUTE_FORBIDDEN"):
        preflight_pilot_runtime(
            manifest=_manifest(judge=True),
            config=_pilot_config(),
            embedder=_PilotEmbedder(),
            expected_embedder_fingerprint=_FP,
            preregistration_digest=_DIGEST,
            committed_preregistration_digest=_DIGEST,
            workload_receipt_digests=("b" * 64,),
            capture_responses=False,
            controller_present=False,
        )


def test_pilot_preflight_fails_uncommitted_and_capture_active():
    common = dict(
        manifest=_manifest(),
        config=_pilot_config(),
        embedder=_PilotEmbedder(),
        expected_embedder_fingerprint=_FP,
        preregistration_digest=_DIGEST,
        workload_receipt_digests=("b" * 64,),
        controller_present=False,
    )
    with pytest.raises(JoltError, match="JOLT_PREREG_NOT_COMMITTED"):
        preflight_pilot_runtime(
            **common,
            committed_preregistration_digest="c" * 64,
            capture_responses=False,
        )
    with pytest.raises(JoltError, match="JOLT_CAPTURE_RESPONSE_ACTIVE"):
        preflight_pilot_runtime(
            **common,
            committed_preregistration_digest=_DIGEST,
            capture_responses=True,
        )


def test_preregistration_hashes_and_token_budget_are_self_consistent():
    repo = Path(__file__).resolve().parents[1]
    plan = json.loads((repo / "experiments/jolt_trigger_v1_manifest_plan.json").read_text())
    for relative, expected in plan["bound_artifacts"].items():
        actual = hashlib.sha256((repo / relative).read_bytes()).hexdigest()
        assert actual == expected, relative
    prereg = yaml.safe_load(
        (repo / "experiments/jolt_trigger_v1_prereg.yaml").read_text()
    )
    assert not prereg["live_execution_allowed"]
    assert prereg["budget"]["judge_tokens"] == 0
    budget = plan["budget_policy"]
    assert budget["maximum_conjecturer_calls"] * (
        budget["prompt_tokens_per_call"] + budget["completion_tokens_per_call"]
    ) == budget["aggregate_hard_token_cap"]
    assert budget["judge_tokens"] == 0
