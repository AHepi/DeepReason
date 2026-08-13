#!/usr/bin/env python3
"""Compile run-config.yaml into a bound RunManifest v6 for this tranche.

Thin shim over ``compile_run_manifest`` for exactly what `deepreason config
compile` cannot express (verified against cli/main.py:795-863): a two-seat
judge ensemble, school-routed conjecture AND criticism wired to the same
existing routes (no new model diversity), and a ``criticism_policy``. Every
routing/authority value is read from run-config.yaml via ``config.*``; the
only things this script supplies that are not in that file are the
experiment's QUESTION and DOSSIER paths, which are PREREG.md's business, not
Config's -- see PREREG.md "Launch mechanics".

Writes, under ``--root``: evidence-dossier.json, run-input.json,
run-manifest.json, problem.json. Does not create a Harness or dispatch any
model call -- that is grounded_run.sh's qualify/reason phases.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from deepreason.admission.attach import admit_attachment_paths  # noqa: E402
from deepreason.admission.store import AdmissionStore  # noqa: E402
from deepreason.config import load as load_config  # noqa: E402
from deepreason.evidence import (  # noqa: E402
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.preparation import _question_digest  # noqa: E402
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest  # noqa: E402
from deepreason.storage.blobs import BlobStore  # noqa: E402
from deepreason.v6_policy import (  # noqa: E402
    engaged_control_plane_policy_v3,
    engaged_criticism_policy,
    engaged_inquiry_capability_policy,
    engaged_simulation_toolchain,
    route_bound_school_execution_policy,
)

CONFIG_PATH = TRANCHE / "run-config.yaml"

QUESTION = (
    "Propose innovative ways to expand and strengthen DeepReason's grounded "
    "extension — the skeptical fixed-point semantics (spec §4, Pass 1) by "
    "which conjectures are accepted, refuted, or suspended — such that each "
    "proposal preserves the existing guarantees: determinism of the fixed "
    "point, polynomial cost, reinstatement as a derived property, and the "
    "validity of every committed root."
)

DOSSIER_PATHS = [
    REPO / "docs/STATE_OF_THE_THEORY.md",
    REPO / "docs/harness-spec-v1.3.md",
    REPO / "docs/proposals/GROUNDED_OVERLAY_PREPLAN.md",
    REPO / "experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md",
    REPO / "docs/map/CON-warrants-and-attacks.md",
    REPO / "docs/map/SUB-adjudication.md",
]

# The compile timestamp is frozen here (not taken from the clock at import
# time) so re-running this script against an existing root is idempotent --
# bind_run_manifest requires byte-identical canonical bytes on a second call.
COMPILED_AT = "2026-08-13T09:24:06Z"


def _route_endpoint_id(config, role: str) -> str:
    seat = config.roles[role]
    if isinstance(seat, list):
        seat = seat[0]
    return seat["endpoint_id"]


def build(root: Path) -> dict:
    config = load_config(CONFIG_PATH)

    admitted = admit_attachment_paths(
        QUESTION,
        [str(p) for p in DOSSIER_PATHS],
        supplied_by="grounded-extension-expansion build_manifest.py",
        allow_partial=False,
    )
    # admit_attachments derives the dossier's problem_ref from the question
    # text alone (deepreason.admission.attach.admit_attachments docstring:
    # "the same way run preparation derives it"); the run input's problem id
    # must equal it exactly or bind_run_input refuses RUN_INPUT_PROBLEM_MISMATCH.
    problem_id = f"question-{_question_digest(QUESTION)[:32]}"
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id, description=QUESTION, criteria=()
        ),
        evidence_dossier_digest=admitted.dossier_digest,
    )
    # admit_attachment_paths persists source bytes into the global admission
    # store (keyed by dossier digest), not into --root; bind_run_input's own
    # first-writer verification (_check_source_blobs) requires them staged
    # under root/blobs first -- same two-step RunPreparationService.prepare
    # itself performs (preparation.py:816-826) before its own bind_run_input.
    admission_store = AdmissionStore()
    source_contents = admission_store.source_bytes(
        admission_store.load(admitted.dossier_digest)
    )
    staged_blobs = BlobStore(root / "blobs")
    for body in source_contents.values():
        staged_blobs.put(body)
    bind_run_input(run_input, admitted.dossier, root)

    conjecturer_endpoint_id = _route_endpoint_id(config, "conjecturer")
    critic_endpoint_id = _route_endpoint_id(config, "argumentative_critic")

    # SCHOOL_SEATS_ENABLED=true, per the config header: "exercise real school
    # seats for both conjecture and criticism, each seat bound to the seat's
    # existing model (no new model diversity introduced)" -- route_bound
    # topology, every school sharing the one already-configured route
    # (no seat_map => every school falls through to seat 0 / the default
    # endpoint_id, deepreason.v6_policy.route_bound_school_execution_policy).
    control_plane_policy = engaged_control_plane_policy_v3().model_copy(
        update={
            "school_execution": route_bound_school_execution_policy(
                conjecturer_endpoint_id
            ),
        }
    )

    # LEGACY_CRITICISM_ENABLED=false and ENGAGED_CRITICISM_AUTHORITY=
    # defended_trial together select the school-routed engaged criticism
    # policy at defended-trial authority (config.py's own documented
    # precondition: ADJUDICATION_STATUS_AUTHORITY_ENABLED gates whether
    # ENGAGED_CRITICISM_AUTHORITY takes effect at all, else falls back to
    # observe_only -- mirrors preparation.py:build_preparation_manifest).
    criticism_policy = None
    if not config.LEGACY_CRITICISM_ENABLED:
        criticism_policy = engaged_criticism_policy(
            critic_endpoint_id,
            authority=(
                config.ENGAGED_CRITICISM_AUTHORITY
                if config.ADJUDICATION_STATUS_AUTHORITY_ENABLED
                else "observe_only"
            ),
        )

    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        # Provider rules (docs/OLLAMA_CLOUD_OPERATIONS.md, binding): explicit
        # concurrency 2 everywhere, including qualification.
        concurrency=2,
        compiled_at=COMPILED_AT,
        control_plane_policy=control_plane_policy,
        criticism_policy=criticism_policy,
        # A non-empty dossier is bound above, so the attached-evidence
        # envelope must be opted in -- byte-identical gesture to `reason
        # --attach` (preparation.py:build_preparation_manifest).
        inquiry_capability_policy=engaged_inquiry_capability_policy(
            attached_evidence=True
        ),
        run_input_digest=run_input.run_input_digest,
        toolchains=(engaged_simulation_toolchain(),),
    )
    bind_run_manifest(manifest, root)

    problem_payload = {
        "schema": "deepreason-text-workload-v1",
        "problem": {"id": problem_id, "description": QUESTION},
        "criteria": [],
        "sources": [source.id for source in admitted.dossier.sources],
    }
    (root / "problem.json").write_text(
        json.dumps(problem_payload, indent=2, sort_keys=True) + "\n"
    )

    for notice in manifest.compile_notices or ():
        print(f"NOTICE {notice.code}: {notice.message}", file=sys.stderr)

    return {
        "manifest_sha256": manifest.sha256,
        "run_input_digest": run_input.run_input_digest,
        "evidence_dossier_digest": admitted.dossier_digest,
        "dossier_sources": [source.id for source in admitted.dossier.sources],
        "compile_notices": [
            {"code": n.code, "message": n.message} for n in (manifest.compile_notices or ())
        ],
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: build_manifest.py <root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    summary = build(root)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
