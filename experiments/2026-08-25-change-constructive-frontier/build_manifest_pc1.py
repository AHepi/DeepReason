#!/usr/bin/env python3
"""Compile P-C1 ARM H's bound RunManifest v6: solo, everything on, no judge.

SPEC.md S7.  Two things make this builder different from its P-R1
predecessor, and both follow from the question rather than from taste.

**The dossier is EMPTY.**  P-R1's question was *about* an attached record,
so twelve files had to be bound at seed.  P-C1's question is a construction
problem: there is no external evidence a candidate could cite, and the only
thing that settles a claim is the checker.  An empty dossier is therefore
the honest shape, and it has a second effect worth naming -- the soak's
recorded blind spot (poietics PARKED.md P1: `_require_v6_workload_match`
compares `problem.json`'s `sources` against the bound dossier, and the soak
never constructs a disagreement) cannot bite here, because `sources: []`
against an empty dossier is the case that matches trivially.

**There is no judge, so `rubric_policy` FORBIDS rubrics.**  P-R1 set
`require_cross_family` because its judge ensemble was the point.  Here a
rubric criterion would be a criterion no program can decide, which is
exactly what R15 rules out.  `forbid` makes that structural rather than
conventional: a rubric cannot enter the run at all.

`single_model="glm-5.2"` collapses the role matrix to one route
(`run_manifest.py`), which is what "solo" means and what the config already
says role by role.

Writes, under <root>: blobs/, evidence-dossier.json, run-input.json,
run-manifest.json, problem.json.  Creates no Harness and dispatches no
model call -- that is the ladder's qualify/reason phases.

Usage:  python build_manifest_pc1.py <root>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(TRANCHE))

from criteria import CRITERIA  # noqa: E402
from deepreason.config import load as load_config  # noqa: E402
from deepreason.evidence import (  # noqa: E402
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.preparation import _question_digest  # noqa: E402
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest  # noqa: E402
from deepreason.v6_policy import (  # noqa: E402
    engaged_control_plane_policy_v3,
    engaged_inquiry_capability_policy,
    engaged_simulation_toolchain,
)

CONFIG_PATH = TRANCHE / "run-config.yaml"

# SPEC.md S7, frozen.  ONE BYTE OF DRIFT HERE MINTS A DIFFERENT RUN ID.
#
# The first sentence is REQUEST.md R18's registered template with N and
# <objects> instantiated.  Everything after it states the scoring rule and
# the wire format (SPEC.md S2), without which R15 is not mechanisable --
# a candidate nobody can parse cannot have its claim checked by program.
from question import QUESTION  # noqa: E402  (SPEC.md S7, frozen)

# Frozen, not read from the clock: bind_run_manifest requires byte-identical
# canonical bytes on a second call, so a wall-clock stamp would make
# re-running this script against an existing root fail instead of being
# idempotent.
COMPILED_AT = "2026-08-25T00:00:00Z"


def _assert_workload_matches(root: Path) -> None:
    """Refuse to hand the ladder a root `deepreason run` will reject.

    P-R1's first launch died at `_require_v6_workload_match` AFTER the
    qualification battery had been paid for (~14 min, ~1160 calls). The
    CLI's own predicate is imported rather than reimplemented, so this
    guard cannot drift from the check it stands in for.
    """
    from deepreason.cli.main import _read_problem_file, _require_v6_workload_match
    from deepreason.evidence import load_evidence_dossier, load_run_input
    from deepreason.workloads.text import ReasoningWorkloadSpec

    payload = _read_problem_file(root / "problem.json")
    spec = ReasoningWorkloadSpec.model_validate(payload)
    _require_v6_workload_match(load_run_input(root), load_evidence_dossier(root), spec)


def build(root: Path, *, config_path: Path | str | None = None) -> dict:
    # ``config_path`` exists for cycle_soak.py, which hands in a copy of
    # this tranche's config with every endpoint redirected to its local
    # stub. The soak must drive THIS shape; restating the shape there
    # would let the instrument and the launch drift apart.
    config = load_config(config_path or CONFIG_PATH)
    problem_id = f"question-{_question_digest(QUESTION)[:32]}"

    # An EMPTY dossier, bound explicitly. The attached-evidence policy is
    # OFF: nothing may be cited because there is nothing to cite, and a
    # construction that appealed to an outside source would be appealing
    # past the only thing that decides it.
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="P-C1 ARM H build_manifest_pc1.py",
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
        # No judge (R15): a rubric criterion is one no program can decide.
        rubric_policy="forbid",
        single_model="glm-5.2",
        concurrency=2,
        compiled_at=COMPILED_AT,
        control_plane_policy=engaged_control_plane_policy_v3(),
        # Simulation is ON under "everything on", and an enabled simulation
        # policy must bind exactly one frozen toolchain whose id equals the
        # policy's own python_toolchain_identity, or the manifest refuses
        # V6_SIMULATION_TOOLCHAIN_REQUIRED. That identity follows the runner
        # choice (contained by default), so it is ASKED FOR here, never pinned
        # to one runner -- a pinned runner silently stops matching the day the
        # default moves.
        toolchains=(engaged_simulation_toolchain(),),
        inquiry_capability_policy=engaged_inquiry_capability_policy(
            attached_evidence=False
        ),
        run_input_digest=run_input.run_input_digest,
    )
    bind_run_manifest(manifest, root)

    (root / "problem.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-text-workload-v1",
                "problem": {"id": problem_id, "description": QUESTION},
                "criteria": [json.loads(c.model_dump_json()) for c in CRITERIA],
                # Empty, and it must equal the dossier's source ids or
                # cli/main.py refuses the launch with RUN_INPUT_MISMATCH.
                "sources": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    _assert_workload_matches(root)

    for notice in manifest.compile_notices or ():
        print(f"NOTICE {notice.code}: {notice.message}", file=sys.stderr)

    return {
        "attached_evidence_enabled": (
            manifest.inquiry_capability_policy.attached_evidence.enabled
        ),
        "compile_notices": [
            {"code": n.code, "message": n.message}
            for n in (manifest.compile_notices or ())
        ],
        "criteria": [c.id for c in CRITERIA],
        "dossier_sources": len(dossier.sources),
        "judge_seats_enabled": config.JUDGE_SEATS_ENABLED,
        "manifest_sha256": manifest.sha256,
        "problem_id": problem_id,
        "question_sha256": _question_digest(QUESTION),
        "run_input_digest": run_input.run_input_digest,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: build_manifest_pc1.py <root>", file=sys.stderr)
        return 2
    print(json.dumps(build(Path(sys.argv[1])), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
