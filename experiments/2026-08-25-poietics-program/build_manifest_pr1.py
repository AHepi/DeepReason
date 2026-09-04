#!/usr/bin/env python3
"""Compile P-R1's bound RunManifest v6: cross-family seats, dossier attached.

Two things make this builder different from every committed predecessor, and
both are forced rather than chosen.

**A NON-EMPTY dossier is bound at seed.** The reach-rich and epoch-3 builders
bind an EMPTY `EvidenceDossierV1` and enable the attached-evidence policy only
so a later amendment can carry `--attach`. P-R1's question is *about* an
attached record, so the twelve curated files must be in the dossier from cycle
0. That means going through the admission pipeline (`admit_attachment_paths`)
rather than hand-assembling a dossier: admission is the one shared path every
end-user surface uses, so the same bytes and question yield the same digest no
matter which door they entered by. Its `EvidenceDossierV2` carries the parsed
BLOCKS that make quoted-evidence citability work — a critic citing the dossier
cites a block, and `check_candidate_citations` byte-checks it.

**The seats are cross-family, so `single_model` must be None.** Every
predecessor passed `single_model="glm-5.2"`, which collapses the role matrix to
one route and does not consult the others (`run_manifest.py:3459`). P-R1 carries
four distinct models across eleven roles, so the config's own matrix must be
read, and `rubric_policy` moves from "forbid" to "require_cross_family" because
the judge ensemble is the point.

The admitted blobs are copied from the admission store into the root's own
BlobStore before binding: `bind_run_input` verifies every source's bytes
against its card (`evidence/state.py::_check_source_blobs`) and refuses a
dossier whose blobs the root cannot produce.

Writes, under <root>: blobs/, evidence-dossier.json, run-input.json,
run-manifest.json, problem.json. Creates no Harness and dispatches no model
call -- that is the ladder's qualify/reason phases.

Usage:  python build_manifest_pr1.py <root>
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
from deepreason.ontology import Commitment  # noqa: E402
from deepreason.preparation import _question_digest  # noqa: E402
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest  # noqa: E402
from deepreason.storage.blobs import BlobStore  # noqa: E402
from deepreason.v6_policy import (  # noqa: E402
    engaged_control_plane_policy_v3,
    engaged_inquiry_capability_policy,
    engaged_simulation_toolchain,
)

CONFIG_PATH = TRANCHE / "run-config.yaml"
RECORD_DIR = TRANCHE / "record"

# REQUEST.md R10a, verbatim and frozen. One byte of drift here mints a
# different run id and a different dossier problem_ref.
QUESTION = (
    "Under what conditions does a test constrain its subject rather than "
    "describe it? Account for the 3-of-26 result in the attached record and "
    "its distribution — compile.py 1/9 mutations lost under shown-to-fail-"
    "first installation, every ordinarily-guarded module 4/4 to 6/7 — same "
    "author, same week, same care."
)

# Frozen, not read from the clock: bind_run_manifest requires byte-identical
# canonical bytes on a second call, so a wall-clock stamp would make
# re-running this script against an existing root fail instead of being
# idempotent.
COMPILED_AT = "2026-08-25T00:00:00Z"

# Subject predicates over the artifact's own bytes (PREREG.md §4).
#
# These are deliberately WEAKER than "is this a good explanation". A
# machine-evaluable predicate cannot judge an account; what it can do is
# refuse an artifact that never engages the question's actual subject. The
# discrimination control in `preflight_criteria.py` is what keeps them
# honest: a criterion the attached record satisfies by itself would let an
# artifact pass by quoting the dossier, which measures the operator's
# document rather than the model's reasoning.
_CONDITION_TERMS = (
    "condition", "when ", "only if", "unless", "requires", "depends on",
    "sufficient", "necessary", "holds when", "fails when",
)
_CONSTRAINT_TERMS = (
    "constrain", "constraint", "describ", "restate", "derive", "independent",
    "by construction", "circular", "tautolog", "redundan",
)
_INSTALLATION_TERMS = (
    "shown-to-fail", "shown to fail", "planted", "fail first", "fails first",
    "install", "ritual", "registry", "mutation", "guard",
)
_DISTRIBUTION_TERMS = (
    "compile.py", "1 of 9", "1/9", "3 of 26", "3/26", "distribution",
    "every other module", "ordinarily-guarded", "ordinarily guarded",
)
_CONFOUND_TERMS = (
    "confound", "one repository", "one author", "one week", "single author",
    "arbitrar", "registry size", "not established", "untested",
    "magnitude", "typical",
)


def _any_expr(terms: tuple[str, ...]) -> str:
    return f"any(t in content.lower() for t in {terms!r})"


def _count_expr(terms: tuple[str, ...], floor: int) -> str:
    return (
        f"sum(1 for t in {terms!r} if t in content.lower()) >= {floor}"
    )


CRITERIA = (
    # A conditional claim about constraining-versus-describing: the
    # question's literal subject. Two constraint terms, not one, so a bare
    # mention of the word "constraint" does not clear it.
    Commitment(
        id="poietics-constraint-condition@v1",
        eval=(
            f"predicate:{_any_expr(_CONDITION_TERMS)} and "
            f"{_count_expr(_CONSTRAINT_TERMS, 2)}"
        ),
    ),
    # The mechanism the record's own distribution points at: how a guard
    # was INSTALLED, not what it asserts.
    Commitment(
        id="poietics-installation-mechanism@v1",
        eval=(
            f"predicate:{_count_expr(_INSTALLATION_TERMS, 2)} and "
            f"{_any_expr(_DISTRIBUTION_TERMS)}"
        ),
    ),
    # The record's own stated limits, which the question hands the critics
    # as ammunition rather than hiding.
    Commitment(
        id="poietics-confound@v1",
        eval=f"predicate:{_count_expr(_CONFOUND_TERMS, 2)}",
    ),
)


def _assert_workload_matches(root: Path) -> None:
    """Refuse to hand the ladder a root `deepreason run` will reject.

    `_require_v6_workload_match` compares the CLI workload (problem.json)
    against the frozen run input AND the dossier's source ids. It is imported
    rather than reimplemented so this guard cannot drift from the check it
    stands in for.
    """
    from deepreason.cli.main import _read_problem_file, _require_v6_workload_match
    from deepreason.evidence import load_evidence_dossier, load_run_input
    from deepreason.workloads.text import ReasoningWorkloadSpec

    # The same three lines cli/main.py runs at launch, in the same order.
    payload = _read_problem_file(root / "problem.json")
    spec = ReasoningWorkloadSpec.model_validate(payload)
    _require_v6_workload_match(load_run_input(root), load_evidence_dossier(root), spec)


def build(root: Path, *, config_path: Path | str | None = None) -> dict:
    # ``config_path`` exists for cycle_soak.py, which hands in a copy of
    # this tranche's config with every endpoint redirected to its local
    # stub.  The soak must drive THIS shape; restating the shape there
    # instead would let the instrument and the launch drift apart.
    config = load_config(config_path or CONFIG_PATH)
    problem_id = f"question-{_question_digest(QUESTION)[:32]}"

    # Admission mints the dossier from the twelve curated files. The
    # problem_ref it stamps is derived from the question, so it must equal
    # problem_id above or bind_run_input refuses RUN_INPUT_PROBLEM_MISMATCH.
    admitted = admit_attachment_paths(
        QUESTION,
        [str(RECORD_DIR)],
        supplied_by="poietics P-R1 build_manifest_pr1.py",
        allow_partial=False,
    )
    dossier = admitted.dossier
    if dossier.problem_ref != problem_id:  # pragma: no cover - guard only
        raise SystemExit(
            f"DOSSIER_PROBLEM_MISMATCH: {dossier.problem_ref} != {problem_id}"
        )
    if admitted.report.refusals:
        raise SystemExit(
            "ADMISSION_REFUSALS: "
            + json.dumps([r.code for r in admitted.report.refusals])
        )

    # The dossier's cards point at blobs by content ref; the root must be
    # able to produce those bytes itself, because a run root is the whole
    # evidentiary unit and may not depend on a store outside it.
    contents = AdmissionStore().source_bytes(dossier)
    blobs = BlobStore(root / "blobs")
    for source in dossier.sources:
        blobs.put(contents[source.content_sha256])

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
        # The judge ensemble is the point of this configuration, so the
        # rubric gate is required rather than forbidden.
        rubric_policy="require_cross_family",
        # NOT single_model: four distinct models across eleven roles.
        single_model=None,
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
            attached_evidence=True
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
                # EVERY dossier source id, in the dossier's own order. The
                # predecessor builders wrote [] here and were right to: their
                # dossiers were empty. Ours is not, and
                # cli/main.py::_require_v6_workload_match refuses the launch
                # with RUN_INPUT_MISMATCH when this list and the dossier's
                # disagree -- which is exactly how P-R1's first launch died,
                # after the qualification battery had already been paid for.
                "sources": [source.id for source in dossier.sources],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    # Assert the launch contract HERE, in the builder that can still fix it,
    # rather than discovering it three minutes and one battery later. This
    # calls the CLI's own predicate rather than a copy of it: a copy would
    # agree with the original only until one of them changed.
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
        "dossier_blocks": len(dossier.blocks),
        "dossier_sources": len(dossier.sources),
        "evidence_dossier_digest": dossier.dossier_digest,
        "manifest_sha256": manifest.sha256,
        "problem_id": problem_id,
        "run_input_digest": run_input.run_input_digest,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: build_manifest_pr1.py <root>", file=sys.stderr)
        return 2
    print(json.dumps(build(Path(sys.argv[1])), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
