"""One run path: the managed service runs every configuration.

Implements R1-R6 and R10 of
``experiments/2026-08-13-change-single-run-path-unification``.

Regression (grounded-extension run, manifest_sha256 8e22d0431fd2b98d,
``experiments/2026-08-12-live-grounded-extension-expansion``): that
configuration -- a two-seat judge ensemble, school-routed conjecture, a
``criticism_policy`` -- could only be launched through a second,
scheduler-only CLI dispatch, because the managed service had no entry a
caller holding a precompiled manifest could use.  The second dispatch
wrote none of the lifecycle records the managed one writes.  The property
that replaced it, and that this module pins: ONE service entry accepts
every configuration the compiler emits, and the CLI verb is a thin alias
over it.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from deepreason.admission.parse import AdmissionInput, admit_sources
from deepreason.application import TEXT_RUN_SERVICE, InspectTextRunIntentV1
from deepreason.application.text_runs import workload_spec_for_root
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.ontology import Provenance
from deepreason.run_manifest import (
    MANIFEST_NAME,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.storage.blobs import BlobStore
from deepreason.v6_policy import (
    engaged_control_plane_policy_v3,
    engaged_criticism_policy,
    engaged_inquiry_capability_policy,
    engaged_simulation_toolchain,
    route_bound_school_execution_policy,
)

from tests.test_amendment_epochs import STAMP, _problem_id
from tests.test_run_input_v6_commitments import _write_qualification

REPO = Path(__file__).resolve().parents[1]
GROUNDED_TRANCHE = REPO / "experiments/2026-08-12-live-grounded-extension-expansion"
GROUNDED_ROOT = GROUNDED_TRANCHE / "run"

# The digest the live grounded run compiled to.  It names that run; it is NOT
# a golden for a fresh compile.  The run bound six local documents as its
# evidence dossier (build_manifest.py DOSSIER_PATHS), two of them under
# docs/map/, so a fresh compile addresses whatever those files say TODAY --
# editing one moves the digest, which is run identity working.  Anchored to
# the committed root, whose bytes cannot move, instead.
GROUNDED_MANIFEST_SHA256 = (
    "8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d"
)

# The one manifest field the bound evidence reaches: dossier bytes ->
# evidence_dossier_digest -> run_input_digest -> manifest.sha256.
EVIDENCE_BEARING_MANIFEST_FIELD = "run_input_digest"

RICH_QUESTION = "Which configurations may the one run path refuse?"
RICH_SOURCE = (
    "# Configuration space\n\n"
    "A run path that inspects a manifest's roles has become a second "
    "admission gate.\n"
)


def _seat(endpoint_id: str, *, model: str, family: str) -> dict:
    return {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": model,
        "provider": "mock",
        "family": family,
        "max_tokens": 64,
        "context_window_tokens": 262_144,
    }


def _rich_config():
    """Every lever `deepreason config compile` cannot express, at once.

    Mirrors the grounded tranche's own run-config.yaml in SHAPE -- a judge
    ensemble of genuinely distinct families, a conjecture seat distinct
    from the criticism seat -- with offline mock endpoints so the test
    needs no provider.
    """

    from deepreason.config import Config

    conjecturer = _seat("offline-conjecture", model="offline-conj", family="alpha")
    critic = _seat("offline-critic", model="offline-crit", family="beta")
    return Config(
        roles={
            "conjecturer": conjecturer,
            "variator": conjecturer,
            "argumentative_critic": critic,
            "defender": critic,
            "summarizer": critic,
            "synthesizer": critic,
            "thesis": critic,
            "judge": [
                _seat("offline-judge-a", model="offline-judge-a", family="gamma"),
                _seat("offline-judge-b", model="offline-judge-b", family="delta"),
            ],
        }
    )


def _rich_manifest(run_input_digest: str):
    """A manifest carrying all three levers the bare path had to hand-feed."""

    control = engaged_control_plane_policy_v3().model_copy(
        update={
            "school_execution": route_bound_school_execution_policy(
                "offline-conjecture"
            )
        }
    )
    return compile_run_manifest(
        _rich_config(),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
        criticism_policy=engaged_criticism_policy(
            "offline-critic", authority="defended_trial"
        ),
        inquiry_capability_policy=engaged_inquiry_capability_policy(
            attached_evidence=True
        ),
        run_input_digest=run_input_digest,
        toolchains=(engaged_simulation_toolchain(),),
    )


def _offline_scheduler(problem_id: str):
    """A scheduler stand-in that reasons once and writes no stop record.

    The launch path must write the stop itself; a stand-in that wrote one
    would hide the record whose presence these tests are about.
    """

    def run(harness, _config, _cycles, _token_budget, **_kwargs):
        harness.create_artifact(
            "One admission gate is enough for one run.",
            provenance=Provenance(role="conjecturer"),
            problem_id=problem_id,
        )
        harness.record_measure(inputs=["cycle", "0", problem_id])
        return (
            {
                "frontier": [],
                "survivors": [],
                "problems": [],
                "diagnostics": [],
            },
            None,
            {
                "metered_tokens": None,
                "logged_tokens_this_run": 0,
                "delta": None,
                "note": "offline no-provider fixture",
            },
        )

    return run


def _bind_rich_root(tmp_path, *, name="rich-root"):
    """Bind the immutable v6 authority a rich-configuration run starts from."""

    root = tmp_path / name
    problem_id = _problem_id(RICH_QUESTION)
    dossier, _report = admit_sources(
        [AdmissionInput(locator="space.md", data=RICH_SOURCE.encode("utf-8"))],
        problem_ref=problem_id,
        provenance=AttachedSourceProvenanceV1(
            supplied_by="single run path fixture",
            acquisition_method="offline construction",
        ),
    )
    BlobStore(root / "blobs").put(RICH_SOURCE.encode("utf-8"))
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id, description=RICH_QUESTION, criteria=()
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    manifest = _rich_manifest(run_input.run_input_digest)
    bind_run_manifest(manifest, root)
    _write_qualification(root, manifest)
    problem_file = root / "problem.json"
    problem_file.write_text(
        json.dumps(
            {
                "schema": "deepreason-text-workload-v1",
                "problem": {"id": problem_id, "description": RICH_QUESTION},
                "criteria": [],
                "sources": [source.id for source in dossier.sources],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return root, manifest, problem_id, problem_file


def _load_grounded_builder():
    """Import the grounded tranche's own committed compile script.

    Pinned to a git-tracked path rather than a copy: the acceptance
    fixture is the operator's real configuration or it is not the
    acceptance fixture.
    """

    target = GROUNDED_TRANCHE / "build_manifest.py"
    assert target.exists(), target
    spec = importlib.util.spec_from_file_location("grounded_build_manifest", target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _without_evidence(manifest_payload: dict) -> dict:
    """The configuration half of a manifest: everything evidence cannot reach."""

    return {
        key: value
        for key, value in manifest_payload.items()
        if key != EVIDENCE_BEARING_MANIFEST_FIELD
    }


def _terminal_state(root) -> str:
    TEXT_RUN_SERVICE.wait(str(root))
    terminal = TEXT_RUN_SERVICE.result(InspectTextRunIntentV1(root=str(root)))
    return terminal.presentation_payload()["state"]


@pytest.mark.parametrize("reference", ("object", "path"))
def test_service_entry_accepts_a_precompiled_manifest_object_and_a_manifest_path(
    tmp_path, monkeypatch, reference
):
    """R1: the door takes a manifest a caller already holds, either shape.

    A caller of `deepreason run --run-manifest` holds a RunManifest bound
    at the root; a ladder holds a path to one.  Neither could reach the
    managed service before, because `start` accepts only an intent whose
    workload spec and budget the caller must have built already.
    """

    root, manifest, problem_id, problem_file = _bind_rich_root(
        tmp_path, name=f"entry-{reference}"
    )
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler", _offline_scheduler(problem_id)
    )

    TEXT_RUN_SERVICE.start_manifest_run(
        root=root,
        manifest=manifest if reference == "object" else root / MANIFEST_NAME,
        problem_path=problem_file,
        cycles=1,
        # `run --token-budget` defaults to absent; the intent vocabulary
        # spells that "unlimited", and the door is what translates.
        token_budget=None,
    )

    assert _terminal_state(root) == "completed"


def test_the_door_narrows_no_configuration_the_compiler_admits(
    tmp_path, monkeypatch
):
    """R2: judge ensemble, school-routed conjecture and criticism_policy.

    None of the three is expressible through `deepreason config compile`,
    and all three had to be hand-fed to the deleted scheduler-only
    dispatch.  The service must run the manifest without inspecting any
    of them.
    """

    root, manifest, problem_id, problem_file = _bind_rich_root(tmp_path)
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler", _offline_scheduler(problem_id)
    )

    # The manifest really does carry all three levers.
    assert len(manifest.roles["judge"]) == 2
    assert manifest.criticism_policy is not None
    assert manifest.control_plane_policy.school_execution.mode == "route_bound"

    TEXT_RUN_SERVICE.start_manifest_run(
        root=root,
        manifest=manifest,
        problem_path=problem_file,
        cycles=1,
    )

    assert _terminal_state(root) == "completed"


def test_the_grounded_tranche_config_enters_through_the_new_door(
    tmp_path, monkeypatch
):
    """R3: the operator's own committed configuration, unmodified.

    `experiments/2026-08-12-live-grounded-extension-expansion` compiled
    run-config.yaml through build_manifest.py because no service entry
    accepted a precompiled manifest.  That exact config must now enter
    through the one door.

    "That exact config" is checked field by field against the manifest the
    live run committed, excluding the one field its bound evidence reaches.
    A whole-digest comparison would say the same thing less precisely and
    would additionally assert that six working-tree documents still hold
    the bytes they held in August 2026 -- two of them map documents that
    SCHEMA.md REQUIRES be edited whenever the code they describe moves.
    """

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("OLLAMA_API_KEY", "offline-fixture-key")
    root = tmp_path / "grounded-root"
    root.mkdir(parents=True)

    summary = _load_grounded_builder().build(root)

    compiled = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    committed = json.loads(
        (GROUNDED_ROOT / MANIFEST_NAME).read_text(encoding="utf-8")
    )
    # Field by field, EXCEPT the fields a default legitimately moved. Each
    # delta is asserted below rather than waived -- excluding a field without
    # pinning what changed inside it is how a second, unnoticed drift would
    # ride along.
    #
    # F3 (2026-08-26) turned research on by default, so a recompile of the same
    # config carries an enabled research policy the August run did not have.
    #
    # The execution-safety tranche (2026-08-28) made the CONTAINED runner the
    # default, on the operator's "If so switch both on" and a SAFE containment
    # verdict, so the same recompile now binds the contained toolchain and the
    # contained simulation envelope. Old roots owe the future nothing (operator
    # law, 2026-08-14): a committed manifest ceasing to match a fresh compile is
    # this law in action, not a regression.
    moved = {"inquiry_capability_policy", "toolchains"}
    assert _without_evidence(compiled).keys() == _without_evidence(committed).keys()
    assert {
        k: v for k, v in _without_evidence(compiled).items() if k not in moved
    } == {k: v for k, v in _without_evidence(committed).items() if k not in moved}

    # The toolchain moved from the local runner to the contained one, and
    # NOTHING ELSE about the entry moved -- same interpreter, same no-network
    # pin. Asserted by popping the two fields that had to change and comparing
    # the remainder.
    (compiled_toolchain,) = compiled["toolchains"]
    (committed_toolchain,) = committed["toolchains"]
    compiled_toolchain = dict(compiled_toolchain)
    committed_toolchain = dict(committed_toolchain)
    assert compiled_toolchain.pop("id") == "python@deepreason-public-contained.v1"
    assert committed_toolchain.pop("id") == "python@deepreason-public-local.v1"
    assert compiled_toolchain.pop("runner") == "container"
    assert committed_toolchain.pop("runner") == "local"
    assert compiled_toolchain == committed_toolchain
    assert compiled_toolchain["network"] is False

    # Inside the capability policy, research and simulation differ and nothing
    # else does, each in exactly the direction the operator asked for.
    compiled_caps = dict(compiled["inquiry_capability_policy"])
    committed_caps = dict(committed["inquiry_capability_policy"])
    assert compiled_caps.pop("research")["enabled"] is True
    assert committed_caps.pop("research")["enabled"] is False
    compiled_simulation = compiled_caps.pop("simulation")
    committed_simulation = committed_caps.pop("simulation")
    assert compiled_simulation["runner_profile"] == "simulation.container.v1"
    assert committed_simulation["runner_profile"] == "simulation.declarative.v1"
    # Both remain ON and both remain finite: the switch changed the runner, not
    # whether simulation runs or whether its authority is bounded.
    assert compiled_simulation["enabled"] is committed_simulation["enabled"] is True
    assert 0 < compiled_simulation["maximum_simulation_executions"] < 1_000
    assert compiled_caps == committed_caps
    # The evidence half is identity too, so it is asserted, not waived:
    # it must address the dossier this compile actually admitted.
    assert compiled[EVIDENCE_BEARING_MANIFEST_FIELD] == summary["run_input_digest"]
    # And the constant still names the live run -- proved against the
    # committed root, which no later edit can move.
    assert (GROUNDED_ROOT / "run-manifest.sha256").read_text(
        encoding="utf-8"
    ).strip() == GROUNDED_MANIFEST_SHA256

    from deepreason.run_manifest import load_run_manifest

    manifest = load_run_manifest(root / MANIFEST_NAME)
    _write_qualification(root, manifest)
    spec = workload_spec_for_root(root, problem_path=root / "problem.json")
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler", _offline_scheduler(spec.problem.id)
    )

    TEXT_RUN_SERVICE.start_manifest_run(
        root=root,
        manifest=root / MANIFEST_NAME,
        problem_path=root / "problem.json",
        cycles=1,
    )

    assert _terminal_state(root) == "completed"


def _run_subparser():
    from deepreason.cli.main import build_parser

    parser = build_parser()
    verbs = [
        action
        for action in parser._actions
        if getattr(action, "choices", None) and "run" in action.choices
    ]
    assert len(verbs) == 1, "the run verb must be reachable exactly once"
    return verbs[0].choices["run"]


def test_run_verb_parser_surface_is_byte_identical():
    """R4: the alias keeps the verb's exact CLI surface.

    Ladders and scripts call `deepreason run` unmodified across this
    unification, so the option strings, their defaults, whether each is
    required, and the action each takes are the contract -- not an
    implementation detail of whichever code the verb dispatches into.
    """

    observed = tuple(
        (
            tuple(action.option_strings),
            action.dest,
            action.default,
            action.required,
            type(action).__name__,
        )
        for action in _run_subparser()._actions
    )

    assert observed == (
        (("-h", "--help"), "help", "==SUPPRESS==", False, "_HelpAction"),
        (("--budget",), "budget", None, True, "_StoreAction"),
        (("--problem",), "problem", None, False, "_StoreAction"),
        (("--token-budget",), "token_budget", None, False, "_StoreAction"),
        (("--run-manifest",), "run_manifest", None, False, "_StoreAction"),
        (("--dry-run",), "dry_run", False, False, "_StoreTrueAction"),
    )


def _failing_scheduler(problem_id: str):
    """A scheduler stand-in that dies mid-run, after real events exist."""

    def run(harness, _config, _cycles, _token_budget, **_kwargs):
        harness.create_artifact(
            "A conjecture recorded before the engine failed.",
            provenance=Provenance(role="conjecturer"),
            problem_id=problem_id,
        )
        raise ValueError("SCHEDULER_FIXTURE_FAILURE: provider unreachable")

    return run


@pytest.mark.parametrize(
    ("scheduler", "expected_state", "expected_code"),
    (
        (_offline_scheduler, "completed", 0),
        (_failing_scheduler, "failed", 4),
    ),
    ids=("completed", "failed"),
)
def test_run_exit_code_contract_is_run_result_exit_code(
    tmp_path, monkeypatch, scheduler, expected_state, expected_code
):
    """R5: terminal outcomes exit through application.models.

    The deleted dispatch returned 0 for any scheduler completion and 1 for
    everything else, so a run that DIED left exit code 1 and no published
    terminal at all -- indistinguishable at the process boundary from a
    manifest that failed preflight.  The one path publishes a terminal
    whatever happened, and `run_result_exit_code` maps it: 0 completed,
    3 cancelled, 4 failed, 5 integrity-invalid.  The `failed` case is what
    makes this a pin rather than a coincidence -- `completed` maps to 0
    under both the old behavior and the new.
    """

    from deepreason.application.models import run_result_exit_code
    from deepreason.cli.main import main

    root, _manifest, problem_id, problem_file = _bind_rich_root(
        tmp_path, name=f"exit-{expected_state}"
    )
    monkeypatch.setattr("deepreason.ops.run_scheduler", scheduler(problem_id))

    code = main(
        [
            "--root", str(root), "run", "--budget", "1",
            "--problem", str(problem_file),
        ]
    )

    published = json.loads((root / "run-result.json").read_text(encoding="utf-8"))
    assert published["state"] == expected_state
    assert code == run_result_exit_code(published) == expected_code


def test_run_preflight_refusals_still_exit_one(tmp_path, capsys):
    """R5: a refusal raised before any terminal exists keeps exiting 1.

    `run_result_exit_code` maps a published terminal; a root that never
    reached one has no terminal to map, so the typed refusal keeps the
    exit code every ladder already branches on.
    """

    from deepreason.cli.main import main

    root, _manifest, _problem_id, _problem_file = _bind_rich_root(
        tmp_path, name="refusal-root"
    )

    assert main(["--root", str(root), "run", "--budget", "0"]) == 1
    assert not (root / "run-result.json").exists()
    assert "positive cycle count" in capsys.readouterr().err


def test_the_door_carries_the_token_steering_authority(tmp_path, monkeypatch):
    """R2, Amendment 1: the config referee reaches the scheduler unchanged.

    The token-steering controller (`referee.run_config_referee` -- its role
    prompt calls its target "the harness's dynamic token-steering
    configuration") is authorized by manifest data alone:
    `InquiryCapabilityPolicyV1.config_referee`, read inside
    `Scheduler._maybe_config_referee`. No launch path appears in that gate,
    and the one door must not become the first thing that does.
    """

    from deepreason.run_manifest import config_from_run_manifest
    from deepreason.v6_policy import engaged_config_referee_policy

    referee_policy = engaged_config_referee_policy({"DEEPREASON_CONFIG_REFEREE": "2"})
    assert referee_policy is not None and referee_policy.enabled

    root = tmp_path / "steering-root"
    problem_id = _problem_id(RICH_QUESTION)
    dossier, _report = admit_sources(
        [AdmissionInput(locator="space.md", data=RICH_SOURCE.encode("utf-8"))],
        problem_ref=problem_id,
        provenance=AttachedSourceProvenanceV1(
            supplied_by="single run path fixture",
            acquisition_method="offline construction",
        ),
    )
    BlobStore(root / "blobs").put(RICH_SOURCE.encode("utf-8"))
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id, description=RICH_QUESTION, criteria=()
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    steering = engaged_inquiry_capability_policy(attached_evidence=True).model_copy(
        update={"config_referee": referee_policy}
    )
    manifest = compile_run_manifest(
        _rich_config(),
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=engaged_control_plane_policy_v3().model_copy(
            update={
                "school_execution": route_bound_school_execution_policy(
                    "offline-conjecture"
                )
            }
        ),
        criticism_policy=engaged_criticism_policy(
            "offline-critic", authority="defended_trial"
        ),
        inquiry_capability_policy=steering,
        run_input_digest=run_input.run_input_digest,
        toolchains=(engaged_simulation_toolchain(),),
    )
    bind_run_manifest(manifest, root)
    _write_qualification(root, manifest)
    (root / "problem.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-text-workload-v1",
                "problem": {"id": problem_id, "description": RICH_QUESTION},
                "criteria": [],
                "sources": [source.id for source in dossier.sources],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    seen = {}

    def capturing_scheduler(harness, config, cycles, token_budget, **kwargs):
        seen["run_manifest"] = kwargs.get("run_manifest")
        seen["token_budget"] = token_budget
        seen["cycles"] = cycles
        return _offline_scheduler(problem_id)(
            harness, config, cycles, token_budget, **kwargs
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", capturing_scheduler)

    TEXT_RUN_SERVICE.start_manifest_run(
        root=root,
        manifest=manifest,
        problem_path=root / "problem.json",
        cycles=4,
    )
    TEXT_RUN_SERVICE.wait(str(root))

    # The scheduler receives the caller's own compiled manifest, steering
    # authority intact -- not a reduced or re-derived one. Identity is by
    # digest, not by object: `_launch` reconciles the passed manifest
    # against the one bound at the root and hands the scheduler that,
    # which is the reconciliation every launch has always performed.
    delivered = seen["run_manifest"]
    assert delivered.sha256 == manifest.sha256
    assert delivered.canonical_bytes() == manifest.canonical_bytes()
    assert delivered.inquiry_capability_policy.config_referee == referee_policy
    assert delivered.inquiry_capability_policy.research is not None
    assert delivered.inquiry_capability_policy.simulation is not None
    # An absent --token-budget stays unbounded through the intent vocabulary,
    # exactly as the deleted dispatch passed None straight to run_scheduler.
    assert seen["token_budget"] is None
    assert seen["cycles"] == 4
    # And the gate the referee actually fires behind reads the manifest, not
    # the launch path: config_from_run_manifest is what the scheduler is
    # built from, and the policy survives that conversion.
    assert config_from_run_manifest(delivered) is not None


def test_run_identity_is_deterministic_through_the_one_road(tmp_path, monkeypatch):
    """R10: same configuration, same run id, through the surviving path.

    `DR-CON-run-identity`: a manifest-launched root records
    `run_id == manifest.sha256` in `progress.jsonl`, and the manifest
    digest is a pure function of the compiled configuration AND the
    evidence that configuration binds.  The check that matters after
    deleting a launch path is that BOTH halves still hold on the survivor
    -- compiling twice must agree, and the root the one path writes must
    carry that same digest.  Neither half needs a literal: comparing to a
    constant would test the working tree's documents, not the survivor.
    """

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("OLLAMA_API_KEY", "offline-fixture-key")
    builder = _load_grounded_builder()

    first = builder.build(tmp_path / "identity-a")
    second = builder.build(tmp_path / "identity-b")
    assert first["manifest_sha256"] == second["manifest_sha256"]
    assert first["run_input_digest"] == second["run_input_digest"]

    root = tmp_path / "identity-a"
    from deepreason.run_manifest import load_run_manifest

    manifest = load_run_manifest(root / MANIFEST_NAME)
    _write_qualification(root, manifest)
    spec = workload_spec_for_root(root, problem_path=root / "problem.json")
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler", _offline_scheduler(spec.problem.id)
    )

    TEXT_RUN_SERVICE.start_manifest_run(
        root=root,
        manifest=manifest,
        problem_path=root / "problem.json",
        cycles=1,
    )
    assert _terminal_state(root) == "completed"

    recorded = {
        json.loads(line)["run_id"]
        for line in (root / "progress.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert recorded == {first["manifest_sha256"]}


def test_manifest_sha_sensitivity_to_bound_evidence_is_correct_behaviour(
    tmp_path, monkeypatch
):
    """Regression (grounded-extension run 8e22d0431fd2b98d): editing a
    document the run BOUND AS EVIDENCE must move its manifest digest.

    This is identity working, not a defect.  It was diagnosed as a defect
    twice -- once as a stale enum, once as a container cache -- before
    `experiments/2026-08-16-defect-manifest-sha-doc-coupling` settled it
    with an A/B probe: editing a document inside `DOSSIER_PATHS` moves the
    digest chain, editing a map document outside it moves nothing.  The
    two tests above used to assert the opposite by pinning a literal, so
    the direction is asserted here rather than left to a comment.

    The dossier is FROZEN into `tmp_path` first.  A test that pins a
    digest against `docs/` is pinning documentation, which is the defect
    this file carried; owning the bytes is what makes the pin honest.
    """

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("OLLAMA_API_KEY", "offline-fixture-key")
    builder = _load_grounded_builder()

    frozen_dir = tmp_path / "frozen-dossier"
    frozen_dir.mkdir()
    frozen = []
    for index, declared in enumerate(builder.DOSSIER_PATHS):
        declared = Path(declared)
        copy = frozen_dir / f"{index:02d}-{declared.name}"
        copy.write_bytes(declared.read_bytes())
        frozen.append(copy)
    assert len(frozen) == 6, [str(path) for path in frozen]
    monkeypatch.setattr(builder, "DOSSIER_PATHS", frozen)

    before = builder.build(tmp_path / "frozen-a")
    again = builder.build(tmp_path / "frozen-b")
    assert before["manifest_sha256"] == again["manifest_sha256"]
    assert before["evidence_dossier_digest"] == again["evidence_dossier_digest"]

    # The copy of the map document whose ordinary, SCHEMA.md-mandated
    # edits triggered the misdiagnoses.
    edited = next(path for path in frozen if path.name.endswith("SUB-adjudication.md"))
    edited.write_bytes(edited.read_bytes() + b"\n<!-- one more sentence -->\n")

    after = builder.build(tmp_path / "frozen-c")
    assert after["evidence_dossier_digest"] != before["evidence_dossier_digest"]
    assert after["run_input_digest"] != before["run_input_digest"]
    assert after["manifest_sha256"] != before["manifest_sha256"]

    # ...and moved through the evidence channel alone: the configuration
    # half of the manifest is untouched by an evidence edit.
    before_manifest = json.loads(
        (tmp_path / "frozen-a" / MANIFEST_NAME).read_text(encoding="utf-8")
    )
    after_manifest = json.loads(
        (tmp_path / "frozen-c" / MANIFEST_NAME).read_text(encoding="utf-8")
    )
    assert _without_evidence(after_manifest) == _without_evidence(before_manifest)
    assert (
        after_manifest[EVIDENCE_BEARING_MANIFEST_FIELD]
        != before_manifest[EVIDENCE_BEARING_MANIFEST_FIELD]
    )
