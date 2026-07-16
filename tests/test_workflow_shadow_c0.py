"""C0 workflow observer is diagnostic only; legacy actuation stays authoritative."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    RunManifest,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.profiles import route_lease_reference
from deepreason.workflow.models import TransitionKind
from deepreason.workflow.shadow import (
    ConjectureShadowObserver,
    ShadowMismatchCode,
    ShadowTerminationKind,
)


STAMP = "2026-07-16T00:00:00Z"


def _config(*, vs_k: int = 1, retry_max: int = 0) -> Config:
    return Config(
        N_SCHOOLS=0,
        VS_K=vs_k,
        FLOOR=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        NEAR_DUP_EPS=None,
        RETRY_MAX=retry_max,
        RESEARCH_BACKEND=None,
        model_profile="standard",
        roles={
            "conjecturer": {
                "endpoint_id": "workflow-c0-conjecturer",
                "endpoint": "mock://workflow-c0-conjecturer",
                "model": "workflow-c0-model",
                "provider": "mock",
                "family": "workflow-c0-family",
                "max_tokens": 256,
            }
        },
    )


def _disabled_context() -> ConjectureContextPolicyV1:
    return ConjectureContextPolicyV1(
        mode="disabled",
        initial_max_blocks=0,
        initial_max_guides=0,
        max_context_expansion_requests=0,
        max_extra_blocks=0,
        permitted_retrieval_channels=(),
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )


def _manifest(config: Config, mode: str) -> RunManifest:
    controlled = mode == "shadow"
    control = ControlPlanePolicyV1(
        controller_version=(
            "workflow.controller.v1" if controlled else "legacy.scheduler.v1"
        ),
        mode=mode,
        workflow_profile=(
            "conjecture.shadow.v1" if controlled else "legacy.scheduler.v1"
        ),
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=_disabled_context(),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v1",
            conjecturer_turn_contract="conjecturer.legacy.v1",
            control_event_schema="control.event.v1" if controlled else "none",
        ),
        capability_profile="conjecture-control.v1" if controlled else "legacy.v1",
    )
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
    )


def _candidates(*contents: str) -> str:
    return json.dumps(
        {
            "candidates": [
                {
                    "content": content,
                    "typicality": 0.42 + index / 100,
                }
                for index, content in enumerate(contents)
            ]
        }
    )


def _candidate() -> str:
    return _candidates("A deterministic C0 scheduler candidate.")


def _normalized_events(harness: Harness) -> list[dict]:
    records = []
    for event in harness.log.read():
        record = event.model_dump(mode="json", by_alias=True)
        record.pop("ts")
        # Wall-clock latency is observational and naturally differs by a
        # millisecond across two otherwise identical in-process mock runs.
        if record["llm"] is not None:
            record["llm"].pop("ms")
            for attempt in record["llm"]["attempt_trace"]:
                attempt.pop("ms")
        records.append(record)
    return records


def _tree_payloads(root: Path) -> dict[str, str]:
    """Durable content except manifest sidecars, whose policies intentionally differ."""

    payloads = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative.startswith("run-manifest") or relative == "log.jsonl":
            continue
        payloads[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return payloads


def _all_tree_payloads(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    }


@dataclass
class _RunCapture:
    harness: Harness
    scheduler: Scheduler
    prompts: list[str]
    meter: TokenMeter
    meter_before: dict
    report: dict


def _run(
    root: Path,
    mode: str,
    *,
    response: str | None = None,
    responses: tuple[str, ...] | None = None,
    cycles: int = 1,
    vs_k: int = 1,
    problem_id: str = "pi-workflow-shadow-c0",
    retry_max: int = 0,
    meter_budget: int = 100_000,
) -> _RunCapture:
    if response is not None and responses is not None:
        raise ValueError("provide one fixed response or one response sequence")
    config = _config(vs_k=vs_k, retry_max=retry_max)
    manifest = _manifest(config, mode)
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id=problem_id,
            description="Exercise one deterministic legacy conjecture cycle.",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    prompts: list[str] = []
    scripted = iter(responses) if responses is not None else None

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        if scripted is not None:
            return next(scripted)
        return _candidate() if response is None else response

    meter = TokenMeter(budget=meter_budget)
    meter_before = meter.snapshot()
    endpoint = MockEndpoint(
        complete,
        name=manifest.roles["conjecturer"][0].base_url,
        model=manifest.roles["conjecturer"][0].model_id,
        max_tokens=256,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        meter=meter,
        retry_max=retry_max,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    scheduler = Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    report = scheduler.run(cycles)
    return _RunCapture(harness, scheduler, prompts, meter, meter_before, report)


def _assert_authoritative_surfaces_equal(
    legacy: _RunCapture,
    shadow: _RunCapture,
) -> None:
    assert shadow.prompts == legacy.prompts
    assert shadow.meter.snapshot() == legacy.meter.snapshot()
    assert shadow.report == legacy.report
    assert shadow.scheduler._cycles == legacy.scheduler._cycles
    assert shadow.scheduler._problem_worked == legacy.scheduler._problem_worked
    assert _normalized_events(shadow.harness) == _normalized_events(legacy.harness)
    assert shadow.harness.state.model_dump(mode="json") == (
        legacy.harness.state.model_dump(mode="json")
    )
    assert shadow.harness.scratch_state == legacy.harness.scratch_state
    assert shadow.harness.bridge_state == legacy.harness.bridge_state
    assert shadow.harness.commitments == legacy.harness.commitments
    assert shadow.harness.warrants == legacy.harness.warrants
    assert _tree_payloads(shadow.harness.root) == _tree_payloads(legacy.harness.root)


def test_shadow_cycle_is_durably_identical_to_legacy_scheduler(tmp_path):
    legacy = _run(tmp_path / "legacy", "legacy")
    shadow = _run(tmp_path / "shadow", "shadow")

    observations = getattr(shadow.scheduler, "workflow_shadow_observations", None)
    assert observations, "the shadow reducer must actually observe the conjecture path"
    assert all(observation.matched for observation in observations)

    # Exact prompts, calls, admission, scheduler bookkeeping, and accounting
    # remain those of the authoritative legacy scheduler.
    _assert_authoritative_surfaces_equal(legacy, shadow)

    # Observations live outside the formal log and all replayed materialized
    # states; C1, not C0, owns durable control events.
    assert not any(event.rule.value == "Control" for event in shadow.harness.log.read())
    reopened = Harness(shadow.harness.root)
    assert reopened.state == shadow.harness.state
    assert reopened.scratch_state == shadow.harness.scratch_state
    assert reopened.bridge_state == shadow.harness.bridge_state


def test_shadow_explains_legacy_no_register_as_deduplication(tmp_path):
    legacy = _run(tmp_path / "legacy-dedupe", "legacy", cycles=2)
    shadow = _run(tmp_path / "shadow-dedupe", "shadow", cycles=2)

    observations = shadow.scheduler.workflow_shadow_observations
    assert len(observations) == 2
    assert all(observation.matched for observation in observations)
    first, second = observations
    assert TransitionKind.PROPOSAL_ADMITTED in first.expected_transition_kinds
    assert second.admitted_refs == ()
    assert second.proposal_candidate_refs == second.deduplicated_refs
    assert second.deduplicated_refs
    assert TransitionKind.PROPOSAL_DEDUPLICATED in (
        second.expected_transition_kinds
    )
    assert TransitionKind.WORK_FINISHED not in second.expected_transition_kinds
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_shadow_explains_mixed_admission_and_existing_deduplication(tmp_path):
    first = _candidates("Existing candidate.")
    mixed = _candidates("Existing candidate.", "New candidate.")
    legacy = _run(
        tmp_path / "legacy-mixed-dedupe",
        "legacy",
        cycles=2,
        vs_k=2,
        responses=(first, mixed),
    )
    shadow = _run(
        tmp_path / "shadow-mixed-dedupe",
        "shadow",
        cycles=2,
        vs_k=2,
        responses=(first, mixed),
    )

    comparison = shadow.scheduler.workflow_shadow_observations[1]
    assert comparison.matched
    assert len(comparison.proposal_candidate_refs) == 2
    assert len(comparison.admitted_refs) == 1
    assert len(comparison.deduplicated_refs) == 1
    assert set(comparison.proposal_candidate_refs) == {
        *comparison.admitted_refs,
        *comparison.deduplicated_refs,
    }
    assert TransitionKind.PROPOSAL_ADMITTED in comparison.expected_transition_kinds
    assert TransitionKind.WORK_FINISHED not in comparison.expected_transition_kinds
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_shadow_names_repeated_candidate_occurrences_independently(tmp_path):
    repeated = _candidates("Repeated candidate.", "Repeated candidate.")
    legacy = _run(
        tmp_path / "legacy-repeated-candidate",
        "legacy",
        vs_k=2,
        response=repeated,
    )
    shadow = _run(
        tmp_path / "shadow-repeated-candidate",
        "shadow",
        vs_k=2,
        response=repeated,
    )

    comparison = shadow.scheduler.workflow_shadow_observations[0]
    assert comparison.matched
    assert len(comparison.proposal_candidate_refs) == 2
    assert len(set(comparison.proposal_candidate_refs)) == 2
    assert comparison.admitted_refs == comparison.proposal_candidate_refs[:1]
    assert comparison.deduplicated_refs == comparison.proposal_candidate_refs[1:]
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_direct_shadow_observer_consumes_snapshots_without_mutation(tmp_path):
    run = _run(tmp_path / "direct-shadow", "shadow")
    manifest = run.scheduler.run_manifest
    observer = ConjectureShadowObserver.from_manifest(manifest)
    assert observer is not None

    events = tuple(run.harness.log.read())
    call_event = next(event for event in events if event.llm is not None)
    contract_id = call_event.llm.attempt_trace[0].contract_id
    route = route_lease_reference(
        leases_from_manifest(manifest)["conjecturer"][0]
    )
    problem_ref = "pi-workflow-shadow-c0"
    canonical_problem_refs = tuple(sorted(run.harness.state.problems))

    before = {
        "formal": copy.deepcopy(run.harness.state),
        "scratch": copy.deepcopy(run.harness.scratch_state),
        "bridge": copy.deepcopy(run.harness.bridge_state),
        "commitments": copy.deepcopy(run.harness.commitments),
        "warrants": copy.deepcopy(run.harness.warrants),
        "events": _normalized_events(run.harness),
        "files": _all_tree_payloads(run.harness.root),
        "prompts": tuple(run.prompts),
        "meter": run.meter.snapshot(),
        "report": copy.deepcopy(run.report),
    }

    for invalid_refs in ((), ("problem:another-prefix",)):
        with pytest.raises(ValueError, match="canonical"):
            observer.begin_conjecture(
                problem_ref=problem_ref,
                canonical_problem_refs=invalid_refs,
                school_id=None,
                route_lease=route,
                contract_id=contract_id,
                formal_fence_seq=0,
                scratch_fence_seq=0,
                event_start_seq=0,
                meter_before=run.meter_before,
            )

    ticket = observer.begin_conjecture(
        problem_ref=problem_ref,
        canonical_problem_refs=canonical_problem_refs,
        school_id=None,
        route_lease=route,
        contract_id=contract_id,
        formal_fence_seq=0,
        scratch_fence_seq=0,
        event_start_seq=0,
        meter_before=run.meter_before,
    )
    admitted_refs = tuple(
        output
        for event in events
        if event.rule.value == "Conj"
        for output in event.outputs
    )
    comparison = observer.finish_conjecture(
        ticket,
        actual_problem_ref=problem_ref,
        events=events,
        admitted_refs=admitted_refs,
        meter_after=run.meter.snapshot(),
    )

    assert comparison.matched
    assert comparison.expected_route == comparison.actual_route == route
    assert comparison.admitted_refs == admitted_refs

    wrong_problem = observer.finish_conjecture(
        ticket,
        actual_problem_ref="pi-another-workflow-problem",
        events=events,
        admitted_refs=admitted_refs,
        meter_after=run.meter.snapshot(),
    )
    assert not wrong_problem.matched
    assert ShadowMismatchCode.PROBLEM in wrong_problem.mismatch_codes

    changed_meter = dict(run.meter.snapshot())
    changed_meter["calls"] += 1
    budget_mismatch = observer.finish_conjecture(
        ticket,
        actual_problem_ref=problem_ref,
        events=events,
        admitted_refs=admitted_refs,
        meter_after=changed_meter,
    )
    assert not budget_mismatch.matched
    assert ShadowMismatchCode.BUDGET in budget_mismatch.mismatch_codes

    context_ticket = observer.begin_conjecture(
        problem_ref=problem_ref,
        canonical_problem_refs=canonical_problem_refs,
        school_id=None,
        route_lease=route,
        contract_id=contract_id,
        formal_fence_seq=0,
        scratch_fence_seq=0,
        event_start_seq=0,
        meter_before=run.meter_before,
        advisory_context_ref="sha256:" + "9" * 64,
    )
    context_mismatch = observer.finish_conjecture(
        context_ticket,
        actual_problem_ref=problem_ref,
        events=events,
        admitted_refs=admitted_refs,
        meter_after=run.meter.snapshot(),
    )
    assert not context_mismatch.matched
    assert ShadowMismatchCode.CONTEXT in context_mismatch.mismatch_codes

    contract_ticket = observer.begin_conjecture(
        problem_ref=problem_ref,
        canonical_problem_refs=canonical_problem_refs,
        school_id=None,
        route_lease=route,
        contract_id="conjecturer.unexpected.v999",
        formal_fence_seq=0,
        scratch_fence_seq=0,
        event_start_seq=0,
        meter_before=run.meter_before,
    )
    contract_mismatch = observer.finish_conjecture(
        contract_ticket,
        actual_problem_ref=problem_ref,
        events=events,
        admitted_refs=admitted_refs,
        meter_after=run.meter.snapshot(),
    )
    assert not contract_mismatch.matched
    assert ShadowMismatchCode.CONTRACT in contract_mismatch.mismatch_codes

    assert run.harness.state == before["formal"]
    assert run.harness.scratch_state == before["scratch"]
    assert run.harness.bridge_state == before["bridge"]
    assert run.harness.commitments == before["commitments"]
    assert run.harness.warrants == before["warrants"]
    assert _normalized_events(run.harness) == before["events"]
    assert _all_tree_payloads(run.harness.root) == before["files"]
    assert tuple(run.prompts) == before["prompts"]
    assert run.meter.snapshot() == before["meter"]
    assert run.report == before["report"]


@pytest.mark.parametrize(
    "method_name",
    ("from_manifest", "begin_conjecture", "finish_conjecture"),
)
def test_observer_failure_is_non_authoritative(
    tmp_path,
    monkeypatch,
    method_name: str,
):
    def fail_observation(*_args, **_kwargs):
        raise RuntimeError(f"injected-{method_name}-failure")

    monkeypatch.setattr(ConjectureShadowObserver, method_name, fail_observation)
    legacy = _run(tmp_path / f"legacy-{method_name}", "legacy")
    shadow = _run(tmp_path / f"shadow-{method_name}", "shadow")

    observations = shadow.scheduler.workflow_shadow_observations
    assert observations
    assert any(
        getattr(observation, "error_type", None) == "RuntimeError"
        for observation in observations
    )
    _assert_authoritative_surfaces_equal(legacy, shadow)
    assert not any(event.rule.value == "Control" for event in shadow.harness.log.read())


def test_candidate_sink_setup_failure_is_non_authoritative(tmp_path, monkeypatch):
    original = Scheduler._workflow_shadow_candidate_sink

    def fail_only_when_shadow_is_enabled(self):
        if self.workflow_shadow_observer is not None:
            raise RuntimeError("injected-candidate-sink-setup-failure")
        return original(self)

    monkeypatch.setattr(
        Scheduler,
        "_workflow_shadow_candidate_sink",
        fail_only_when_shadow_is_enabled,
    )
    legacy = _run(tmp_path / "legacy-candidate-sink-failure", "legacy")
    shadow = _run(tmp_path / "shadow-candidate-sink-failure", "shadow")

    observations = shadow.scheduler.workflow_shadow_observations
    assert observations
    assert any(
        observation.error_type == "RuntimeError" for observation in observations
    )
    _assert_authoritative_surfaces_equal(legacy, shadow)
    assert not any(event.rule.value == "Control" for event in shadow.harness.log.read())


def test_schema_repair_drop_is_observed_without_shadow_side_effects(tmp_path):
    invalid_response = "{this-is-not-valid-json"
    legacy = _run(
        tmp_path / "legacy-schema-drop",
        "legacy",
        response=invalid_response,
    )
    shadow = _run(
        tmp_path / "shadow-schema-drop",
        "shadow",
        response=invalid_response,
    )

    observations = shadow.scheduler.workflow_shadow_observations
    assert len(observations) == 1
    comparison = observations[0]
    assert comparison.matched
    assert comparison.admitted_refs == ()
    assert comparison.source_call_seq is not None
    assert shadow.meter.snapshot()["calls"] >= 1
    assert any(
        event.llm is not None
        and event.rule.value == "Measure"
        and event.inputs
        and event.inputs[0] == "dropped-call"
        for event in shadow.harness.log.read()
    )
    _assert_authoritative_surfaces_equal(legacy, shadow)
    assert not any(event.rule.value == "Control" for event in shadow.harness.log.read())


def test_unrepresentable_legacy_problem_ref_cannot_escape_observer(tmp_path):
    problem_id = "pi-" + "x" * 512
    legacy = _run(
        tmp_path / "legacy-long-problem-ref",
        "legacy",
        problem_id=problem_id,
    )
    shadow = _run(
        tmp_path / "shadow-long-problem-ref",
        "shadow",
        problem_id=problem_id,
    )

    observations = shadow.scheduler.workflow_shadow_observations
    assert len(observations) == 1
    diagnostic = observations[0]
    assert not diagnostic.matched
    assert diagnostic.error_type == "ValidationError"
    assert diagnostic.problem_ref.startswith("unrepresentable:sha256:")
    assert ShadowMismatchCode.OBSERVER_ERROR in diagnostic.mismatch_codes
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_mid_retry_budget_stop_is_not_reported_as_repair_exhaustion(tmp_path):
    invalid_response = "{this-is-not-valid-json"
    legacy = _run(
        tmp_path / "legacy-mid-retry-budget-stop",
        "legacy",
        response=invalid_response,
        retry_max=2,
        meter_budget=850,
    )
    shadow = _run(
        tmp_path / "shadow-mid-retry-budget-stop",
        "shadow",
        response=invalid_response,
        retry_max=2,
        meter_budget=850,
    )

    observations = shadow.scheduler.workflow_shadow_observations
    assert len(observations) == 1
    comparison = observations[0]
    assert not comparison.matched
    assert (
        comparison.termination_kind
        == ShadowTerminationKind.TOKEN_BUDGET_EXCEEDED
    )
    assert ShadowMismatchCode.BUDGET in comparison.mismatch_codes
    assert TransitionKind.REPAIR_EXHAUSTED not in comparison.expected_transition_kinds
    assert comparison.proposal_receipt_id is None
    assert any("token budget" in item["stopped"] for item in shadow.scheduler.diagnostics)
    _assert_authoritative_surfaces_equal(legacy, shadow)
