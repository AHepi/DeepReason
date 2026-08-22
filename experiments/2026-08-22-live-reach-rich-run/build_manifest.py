#!/usr/bin/env python3
"""Compile run-config.yaml into a bound RunManifest v6 for this tranche.

Unlike `deepreason reason`, this path can carry the run's OWN criteria:
the managed preparation service hardcodes ``criteria=()``
(preparation.py:940-945), so a run whose problems must carry
subject-substantive commitments has to enter through the manifest surface.
That is the same single run path either way -- `deepreason run
--run-manifest` is a rendering shell over
``TextRunApplicationService.start_manifest_run`` (operator law 2026-08-13,
operations parity), owning no scheduler, no lock and no terminalization of
its own.

Writes, under ``--root``: evidence-dossier.json, run-input.json,
run-manifest.json, problem.json. Creates no Harness and dispatches no model
call -- that is reach_run.sh's qualify/reason phases.

The three subject criteria are PREREG.md §3, frozen there before this file
was written. They are ordinary `predicate:` commitments over the artifact's
own bytes; nothing here registers a program, changes a threshold, or touches
a frozen surface.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))

from deepreason.config import load as load_config  # noqa: E402
from deepreason.evidence import (  # noqa: E402
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.ontology import Commitment  # noqa: E402
from deepreason.preparation import _question_digest  # noqa: E402
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest  # noqa: E402
from deepreason.v6_policy import engaged_control_plane_policy_v3  # noqa: E402

CONFIG_PATH = TRANCHE / "run-config.yaml"

QUESTION = (
    "Why does the air in a large city stay several degrees warmer than the "
    "surrounding countryside on a clear, calm night, and what single "
    "mechanism best explains why that night-time gap is larger in some "
    "cities than in others?"
)

# The compile timestamp is frozen (not read from the clock) so re-running
# this script against an existing root is idempotent: bind_run_manifest
# requires byte-identical canonical bytes on a second call.
COMPILED_AT = "2026-08-22T00:00:00Z"

_ENERGY_BALANCE_TERMS = (
    "albedo", "thermal mass", "heat capacity", "evapotranspiration",
    "longwave", "sky view", "anthropogenic heat", "latent heat",
    "sensible heat", "emissivity", "impervious",
)
_NIGHT_TERMS = ("night", "nocturnal", "after sunset")
_RELEASE_TERMS = ("stored", "storage", "release", "releas", "retain",
                  "cooling rate", "daytime")
_MODULATOR_TERMS = (
    "sky view", "street canyon", "building height", "built density",
    "vegetation", "green space", "irrigation", "population", "aridity",
    "humidity", "wind speed", "city size",
)
_DIRECTION_TERMS = (
    "larger", "greater", "stronger", "smaller", "weaker", "increase",
    "decrease", "more pronounced", "less pronounced", "scales with",
    "proportional", "depends on",
)


def _any_expr(terms: tuple[str, ...]) -> str:
    return f"any(t in content.lower() for t in {terms!r})"


CRITERIA = (
    Commitment(
        id="uhi-energy-balance@v1",
        eval=(
            "predicate:sum(1 for t in "
            f"{_ENERGY_BALANCE_TERMS!r} if t in content.lower()) >= 2"
        ),
    ),
    Commitment(
        id="uhi-nocturnal-release@v1",
        eval=(
            f"predicate:{_any_expr(_NIGHT_TERMS)} and {_any_expr(_RELEASE_TERMS)}"
        ),
    ),
    Commitment(
        id="uhi-cross-city-modulator@v1",
        eval=(
            f"predicate:{_any_expr(_MODULATOR_TERMS)} and "
            f"{_any_expr(_DIRECTION_TERMS)}"
        ),
    ),
)


def build(root: Path) -> dict:
    config = load_config(CONFIG_PATH)

    # No dossier is bound (PREREG.md §3): the question needs no attached
    # evidence, and an empty dossier keeps the run's whole surface inside
    # the model's own answer plus the criteria under test.
    problem_id = f"question-{_question_digest(QUESTION)[:32]}"
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="reach-rich tranche build_manifest.py",
            acquisition_method="no attached evidence",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id, description=QUESTION, criteria=CRITERIA
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)

    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        single_model="glm-5.2",
        # Provider rules (docs/OLLAMA_CLOUD_OPERATIONS.md, binding):
        # explicit concurrency everywhere, including qualification.
        concurrency=2,
        compiled_at=COMPILED_AT,
        # The public default `deepreason reason` itself compiles: bounded
        # scratch authoring and model context ON, schools conditioning-only,
        # zero workflow retries. Deviating from it would make this run
        # non-comparable with every managed root without buying anything the
        # measure needs.
        control_plane_policy=engaged_control_plane_policy_v3(),
        run_input_digest=run_input.run_input_digest,
    )
    bind_run_manifest(manifest, root)

    problem_payload = {
        "schema": "deepreason-text-workload-v1",
        "problem": {"id": problem_id, "description": QUESTION},
        "criteria": [
            json.loads(commitment.model_dump_json()) for commitment in CRITERIA
        ],
        "sources": [],
    }
    (root / "problem.json").write_text(
        json.dumps(problem_payload, indent=2, sort_keys=True) + "\n"
    )

    for notice in manifest.compile_notices or ():
        print(f"NOTICE {notice.code}: {notice.message}", file=sys.stderr)

    return {
        "manifest_sha256": manifest.sha256,
        "run_input_digest": run_input.run_input_digest,
        "evidence_dossier_digest": dossier.dossier_digest,
        "problem_id": problem_id,
        "criteria": [c.id for c in CRITERIA],
        "compile_notices": [
            {"code": n.code, "message": n.message}
            for n in (manifest.compile_notices or ())
        ],
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: build_manifest.py <root>", file=sys.stderr)
        return 2
    print(json.dumps(build(Path(sys.argv[1])), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
