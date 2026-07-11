"""The website workflow is deterministic process machinery, not a model role."""

import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.workflows.website import (
    NextAction,
    StageOutcome,
    WebsiteStage,
    WebsiteCheckpointError,
    WebsiteStateMachine,
    WebsiteWorkflow,
    _CompactCallResult,
)
from deepreason.workflows.manifest_compiler import (
    CompactArtDirection,
    CompactComponentContract,
    CompactDesignOutline,
    ManifestCompiler,
)


def test_success_path_is_fixed_and_complete():
    machine = WebsiteStateMachine()
    seen = []
    while not machine.complete:
        current = machine.stage
        result = machine.success([current.value.lower()])
        seen.append(result.stage)
        assert result.outcome == StageOutcome.SUCCESS
        if current == WebsiteStage.EXPORT:
            assert result.next_action == NextAction.COMPLETE
        else:
            assert result.next_action == NextAction.ADVANCE

    assert seen == list(WebsiteStage)
    assert [result.attempt for result in machine.history] == [1] * len(WebsiteStage)


def test_retry_is_local_and_cannot_choose_a_transition():
    machine = WebsiteStateMachine()
    machine.success(["plan-id"])
    assert machine.stage == WebsiteStage.DESIGN_OUTLINE

    result = machine.retryable_failure(
        [{"code": "INVALID_OUTLINE", "path": "/components/0"}]
    )
    assert result.next_action == NextAction.RETRY_STAGE
    assert machine.stage == WebsiteStage.DESIGN_OUTLINE
    assert machine.attempt == 2

    second = machine.success(["outline-id"])
    assert second.attempt == 2
    assert machine.stage == WebsiteStage.COMPONENT_CONTRACTS


def test_manifest_failure_selects_component_contract_repair():
    machine = WebsiteStateMachine()
    for _ in range(2):
        machine.success([])
    assert machine.stage == WebsiteStage.COMPONENT_CONTRACTS
    result = machine.retryable_failure(
        [{"code": "UNKNOWN_DEPENDENCY_ALIAS", "component_alias": "C2"}],
        component_contract=True,
    )
    assert result.next_action == NextAction.REPAIR_COMPONENT_CONTRACT
    assert machine.stage == WebsiteStage.COMPONENT_CONTRACTS


def test_terminal_result_never_advances_or_exports():
    machine = WebsiteStateMachine()
    result = machine.terminal_failure([{"code": "REPAIR_EXHAUSTED"}])
    assert result.outcome == StageOutcome.TERMINAL_FAILURE
    assert result.next_action == NextAction.TERMINATE
    assert machine.complete
    assert machine.stage == WebsiteStage.PLAN


class _RecordingHarness:
    def __init__(self, root: Path, all_finished: threading.Event):
        self.root = root
        self.all_finished = all_finished
        self.records = []

    def record_measure(self, *, inputs=(), llm=None, **_kwargs):
        # No result may be registered while another independent call is live.
        assert self.all_finished.is_set()
        self.records.append((list(inputs), threading.get_ident(), llm))

    def record_llm_calls(self, calls, tag, *extra):
        assert self.all_finished.is_set()
        self.records.extend(
            ([tag, *extra], threading.get_ident(), call) for call in calls
        )


def _art_direction():
    return CompactArtDirection(
        palette="deep navy with cyan highlights",
        typography="geometric headings and readable body text",
        spacing_strategy="fluid grid spacing",
        responsive_strategy="single column on narrow screens",
        interaction_state_model="local controls plus global motion state",
        motion_language="slow orbital strand motion",
        scroll_narrative="sections reveal in page order",
        depth_structure="helix over quiet cellular layers",
        transition_grammar="opacity and transform",
        texture_language="luminous grain",
        reduced_motion_version="all content remains visible and still",
        static_fallback="complete readable still composition",
    )


def test_component_contract_calls_are_bounded_collected_then_logged_in_id_order(
    tmp_path,
):
    all_finished = threading.Event()
    harness = _RecordingHarness(tmp_path, all_finished)
    run_manifest = SimpleNamespace(model_profile="compact", concurrency=2)
    workflow = WebsiteWorkflow(
        harness,
        SimpleNamespace(model_profile="compact"),
        "DNA",
        tmp_path / "out",
        6,
        300,
        lambda _message: None,
        run_manifest=run_manifest,
    )
    outline = CompactDesignOutline.model_validate({
        # Deliberately not component-id order: registration must not inherit
        # either outline order or nondeterministic worker completion order.
        "components": [
            {"alias": "C3", "purpose": "closing navigation"},
            {"alias": "C1", "purpose": "DNA hero"},
            {"alias": "C2", "purpose": "replication"},
        ]
    })

    first_pair = threading.Barrier(2)
    release_c1 = threading.Event()
    lock = threading.Lock()
    active = 0
    max_active = 0
    completed = 0
    worker_threads = set()

    def fake_collect(**job):
        nonlocal active, max_active, completed
        alias = job["label"].rsplit(":", 1)[1]
        with lock:
            active += 1
            max_active = max(max_active, active)
            worker_threads.add(threading.get_ident())
        if alias in {"C1", "C2"}:
            first_pair.wait(timeout=2)
        if alias == "C1":
            release_c1.wait(timeout=2)
        elif alias == "C2":
            # Force completion order to differ from commit order.
            release_c1.set()
        output = CompactComponentContract(
            alias=alias,
            owned_dom_ids=[f"{alias.lower()}-root"],
        )
        with lock:
            active -= 1
            completed += 1
            if completed == 3:
                all_finished.set()
        return _CompactCallResult(
            label=job["label"],
            output=output,
            raw_ref=f"raw-{alias}",
            tokens=int(alias[1:]),
        )

    workflow._collect_compact_call = fake_collect
    results = workflow._compact_contract_batch(
        outline.components, outline, _art_direction()
    )

    assert max_active == 2
    assert len(worker_threads) == 2
    assert [contract.alias for contract, _ in results] == ["C1", "C2", "C3"]
    assert [ref for _, ref in results] == ["raw-C1", "raw-C2", "raw-C3"]
    assert [record[0][1] for record in harness.records] == [
        "component-contract:C1",
        "component-contract:C2",
        "component-contract:C3",
    ]
    assert {record[1] for record in harness.records} == {threading.get_ident()}
    assert workflow.compact_calls == 3
    assert workflow.spent == 6


def test_compact_profile_defaults_to_serial_component_contract_calls(tmp_path):
    all_finished = threading.Event()
    workflow = WebsiteWorkflow(
        _RecordingHarness(tmp_path, all_finished),
        SimpleNamespace(model_profile="compact"),
        "DNA",
        tmp_path / "out",
        6,
        None,
        lambda _message: None,
    )

    assert workflow._component_concurrency(8) == 1


def test_terminal_checkpoint_binds_root_manifest_and_intermediates(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    workflow = WebsiteWorkflow(
        harness,
        Config(),
        "the wonders of DNA",
        tmp_path / "site",
        6,
        1_000,
        lambda _message: None,
        run_manifest=SimpleNamespace(
            model_profile="compact", concurrency=1, sha256="a" * 64
        ),
    )
    workflow.plan_id = "plan-1"
    workflow.last_valid_intermediate = "plan-1"

    assert workflow._terminal(
        [{"code": "TEST_FAILURE", "path": "/design"}], "stopped"
    ) == []

    checkpoint = json.loads((root / "website-checkpoint.json").read_text())
    assert checkpoint["manifest_sha256"] == "a" * 64
    assert checkpoint["complete"] is True
    assert checkpoint["stage"] == "PLAN"
    assert checkpoint["canonical_intermediates"]["plan_id"] == "plan-1"
    assert checkpoint["last_valid_intermediate"] == "plan-1"
    assert checkpoint["event_seq"] == 2

    terminal = json.loads((root / "website-terminal.json").read_text())
    command = terminal["resume_command"]
    assert str(root.resolve()) in command
    assert str((root / "run-manifest.json").resolve()) in command
    assert str((tmp_path / "site").resolve()) in command
    assert terminal["checkpoint_ref"] == str(
        (root / "website-checkpoint.json").resolve()
    )


def test_compiled_design_frontloads_every_required_critic_dimension(tmp_path):
    outline = CompactDesignOutline.model_validate({
        "components": [
            {"alias": "C1", "purpose": "animated DNA hero"},
            {"alias": "C2", "purpose": "replication story"},
        ]
    })
    contracts = [
        CompactComponentContract(
            alias="C1", owned_dom_ids=["dna-hero"], motion_requirement="full"
        ),
        CompactComponentContract(
            alias="C2", owned_dom_ids=["dna-copy"], depends_on=["C1"]
        ),
    ]
    art = _art_direction()
    compiled = ManifestCompiler(known_libs=set()).compile(
        outline, contracts, art_direction=art, title="DNA"
    )
    assert compiled.ok

    document = WebsiteWorkflow._compiled_design_document(
        outline, contracts, art, compiled.manifest
    )
    synopsis = document.split("## Page layout", 1)[0]
    for label in (
        "Layout:",
        "Visual system:",
        "Components:",
        "Interaction and state:",
        "Responsive behavior:",
        "Motion behavior:",
        "Reduced-motion behavior:",
        "Static alternative:",
    ):
        assert label in synopsis
    assert "all content remains visible and still" in synopsis


def _resume_manifest():
    outline = CompactDesignOutline.model_validate({"components": [
        {"alias": "C1", "purpose": "hero"},
        {"alias": "C2", "purpose": "replication"},
    ]})
    result = ManifestCompiler().compile(outline, [
        CompactComponentContract(alias="C1", owned_dom_ids=["hero"]),
        CompactComponentContract(alias="C2", owned_dom_ids=["copy"]),
    ], art_direction=_art_direction(), title="DNA")
    assert result.ok
    return result.manifest


def test_component_checkpoint_restores_and_skips_completed_calls(tmp_path, monkeypatch):
    root, out = tmp_path / "run", tmp_path / "out"
    route = SimpleNamespace(model_profile="compact", concurrency=1, sha256="b" * 64)
    harness = Harness(root)
    plan = harness.create_artifact("plan")
    design = harness.create_artifact("design")
    first = harness.create_artifact("first component")
    workflow = WebsiteWorkflow(
        harness, Config(), "DNA", out, 10, 1_000, lambda _message: None,
        run_manifest=route,
    )
    workflow.plan_id, workflow.design_id = plan.id, design.id
    workflow.manifest = _resume_manifest()
    workflow.chosen = {"c1": first.id}
    workflow.imports_resolved = True
    for value in (plan.id, "outline", "contracts", design.id, "validated"):
        workflow.machine.success([value])
    workflow._write_checkpoint()

    resumed = WebsiteWorkflow(
        Harness(root), Config(), "DNA", out, 10, 1_000, lambda _message: None,
        run_manifest=route,
    )
    calls = []
    def stop(**kwargs):
        calls.append(kwargs["label"])
        raise RuntimeError("stop")
    monkeypatch.setattr(resumed, "_run_stage", stop)
    with pytest.raises(RuntimeError, match="stop"):
        resumed.run()
    assert calls == ["component c2"]
    assert resumed.machine.stage == WebsiteStage.COMPONENT_BUILD
    assert resumed.chosen == {"c1": first.id}


def test_terminal_checkpoint_reopens_failed_stage_without_replaying_prefix(tmp_path):
    root, out = tmp_path / "run", tmp_path / "out"
    route = SimpleNamespace(model_profile="compact", concurrency=1, sha256="c" * 64)
    first = WebsiteWorkflow(
        Harness(root), Config(), "DNA", out, 6, None, lambda _message: None,
        run_manifest=route,
    )
    first._terminal([{"code": "NO_PLAN_SURVIVOR"}], "stopped")
    resumed = WebsiteWorkflow(
        Harness(root), Config(), "DNA", out, 6, None, lambda _message: None,
        run_manifest=route,
    )
    assert resumed.machine.stage == WebsiteStage.PLAN
    assert not resumed.machine.complete
    assert resumed.machine.attempt == 2
    assert resumed.machine.history[-1].outcome == StageOutcome.TERMINAL_FAILURE


def test_terminal_component_resume_uses_successor_problem(tmp_path, monkeypatch):
    from deepreason import easy

    root, out = tmp_path / "run", tmp_path / "out"
    route = SimpleNamespace(model_profile="compact", concurrency=1, sha256="f" * 64)
    harness = Harness(root)
    plan = harness.create_artifact("plan")
    design = harness.create_artifact("design")
    manifest = _resume_manifest()
    spec = manifest.ordered()[0]
    easy.seed_component(
        harness, "DNA", design.id, manifest, spec, Config().CHUNK_MAX_CHARS
    )
    failed = harness.create_artifact("failed component", problem_id="pi-comp-c1")
    workflow = WebsiteWorkflow(
        harness, Config(), "DNA", out, 10, None, lambda _message: None,
        run_manifest=route,
    )
    workflow.plan_id, workflow.design_id, workflow.manifest = plan.id, design.id, manifest
    workflow.imports_resolved = True
    for value in (plan.id, "outline", "contracts", design.id, "validated"):
        workflow.machine.success([value])
    workflow._terminal([{
        "code": "NO_COMPONENT_SURVIVOR", "component": "c1",
        "path": "/components/c1",
    }], "stopped")

    resumed = WebsiteWorkflow(
        Harness(root), Config(), "DNA", out, 10, None, lambda _message: None,
        run_manifest=route,
    )
    seen = []
    def stop(**kwargs):
        seen.append(kwargs["root_pid"])
        raise RuntimeError("stop")
    monkeypatch.setattr(resumed, "_run_stage", stop)
    with pytest.raises(RuntimeError, match="stop"):
        resumed.run()
    assert seen == ["pi-comp-c1-resume-2"]
    successor = resumed.harness.state.problems["pi-comp-c1-resume-2"]
    assert successor.provenance.trigger.value == "successor"
    assert successor.provenance.from_ == [failed.id]


@pytest.mark.parametrize("field", ["description", "out", "manifest"])
def test_incompatible_checkpoint_fails_closed(tmp_path, field):
    root, out = tmp_path / "run", tmp_path / "out"
    route = SimpleNamespace(model_profile="compact", concurrency=1, sha256="d" * 64)
    first = WebsiteWorkflow(
        Harness(root), Config(), "DNA", out, 6, None, lambda _message: None,
        run_manifest=route,
    )
    first._terminal([{"code": "STOP"}], "stopped")
    with pytest.raises(WebsiteCheckpointError) as caught:
        WebsiteWorkflow(
            Harness(root), Config(), "changed" if field == "description" else "DNA",
            tmp_path / "changed" if field == "out" else out, 6, None,
            lambda _message: None,
            run_manifest=(
                SimpleNamespace(model_profile="compact", concurrency=1, sha256="e" * 64)
                if field == "manifest" else route
            ),
        )
    assert caught.value.code == "CHECKPOINT_INCOMPATIBLE"
