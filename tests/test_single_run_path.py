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

# The digest the live grounded run compiled to (its RESULTS.md and its own
# run root name it).  Pinned here because the acceptance fixture is only
# the acceptance fixture if it is the same configuration, not a lookalike.
GROUNDED_MANIFEST_SHA256 = (
    "8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d"
)

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


def _terminal_state(root) -> str:
    TEXT_RUN_SERVICE.wait(str(root))
    terminal = TEXT_RUN_SERVICE.result(InspectTextRunIntentV1(root=str(root)))
    return terminal.presentation_payload()["state"]


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
    """

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("OLLAMA_API_KEY", "offline-fixture-key")
    root = tmp_path / "grounded-root"
    root.mkdir(parents=True)

    summary = _load_grounded_builder().build(root)
    assert summary["manifest_sha256"] == GROUNDED_MANIFEST_SHA256

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
