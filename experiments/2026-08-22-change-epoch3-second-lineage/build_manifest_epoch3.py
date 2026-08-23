#!/usr/bin/env python3
"""Compile the epoch-3 RunManifest: the reach-rich design, one field moved.

Epoch 3 must put a SECOND problem lineage in the root, and the only surface
that can create one without a `src/` change is an amendment epoch
(SPEC.md M1). Every amendment that `deepreason continue` will accept has to
carry `--attach` (M4: a question-only amendment leaves the epoch dossier
pointing at the superseded problem and the continuation refuses with
RUN_INPUT_MISMATCH), and `--attach` is gated on the manifest's
`inquiry_capability_policy.attached_evidence.enabled` (M5). So this builder
differs from the reach-rich `build_manifest.py` in EXACTLY that flag.

Everything that defines the experiment -- the question, the three subject
predicates, the solo glm-5.2 config, the policy preset, the frozen compile
timestamp -- is IMPORTED from that file rather than restated, so the two
manifests cannot drift apart in anything but the one field under change.

Consequences, both measured before this file was written (SPEC.md M7/M8):
  - manifest sha256 becomes 685990000eea3d73..., so epoch 3 is a NEW root
    and neither reach-rich root needs retiring;
  - the qualification subject digest moves, so the ~14-minute production
    battery runs once more. That is the priced cost of the second lineage.

The seed dossier stays EMPTY (PREREG_EPOCH3.md): phase 1 is the reach-rich
design unchanged in substance, and the supplement enters only at the
amendment, bound to the second lineage.

Writes, under <root>: evidence-dossier.json, run-input.json,
run-manifest.json, problem.json. Creates no Harness and dispatches no model
call.

Usage:  python build_manifest_epoch3.py <root>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
REACH_RICH = REPO / "experiments" / "2026-08-22-live-reach-rich-run"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REACH_RICH))

from build_manifest import (  # noqa: E402  (the reach-rich tranche's builder)
    COMPILED_AT,
    CONFIG_PATH,
    CRITERIA,
    QUESTION,
)
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
    engaged_attached_evidence_policy,
    engaged_control_plane_policy_v3,
)

# The reach-rich manifest names no inquiry policy, so `compile_run_manifest`
# DERIVES the all-disabled one. That derived object is the baseline this
# builder must reproduce exactly, and it cannot be hand-assembled: flipping
# `enabled` on the engaged policy leaves the engaged bounds behind, and the
# model refuses a disabled capability carrying non-zero bounds. So compile
# once WITHOUT an inquiry policy (in memory, nothing bound), read the derived
# policy back, and move the one field.


def _epoch3_inquiry_policy(config, run_input_digest: str):
    """The reach-rich derived policy, with attached evidence enabled."""

    baseline = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        single_model="glm-5.2",
        concurrency=2,
        compiled_at=COMPILED_AT,
        control_plane_policy=engaged_control_plane_policy_v3(),
        run_input_digest=run_input_digest,
    )
    return baseline.inquiry_capability_policy.model_copy(
        update={"attached_evidence": engaged_attached_evidence_policy(attached=True)}
    )


def build(root: Path) -> dict:
    config = load_config(CONFIG_PATH)
    problem_id = f"question-{_question_digest(QUESTION)[:32]}"
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="epoch-3 tranche build_manifest_epoch3.py",
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
        concurrency=2,
        compiled_at=COMPILED_AT,
        control_plane_policy=engaged_control_plane_policy_v3(),
        inquiry_capability_policy=_epoch3_inquiry_policy(
            config, run_input.run_input_digest
        ),
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
        "attached_evidence_enabled": (
            manifest.inquiry_capability_policy.attached_evidence.enabled
        ),
        "compile_notices": [
            {"code": n.code, "message": n.message}
            for n in (manifest.compile_notices or ())
        ],
        "criteria": [c.id for c in CRITERIA],
        "evidence_dossier_digest": dossier.dossier_digest,
        "manifest_sha256": manifest.sha256,
        "problem_id": problem_id,
        "run_input_digest": run_input.run_input_digest,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: build_manifest_epoch3.py <root>", file=sys.stderr)
        return 2
    print(json.dumps(build(Path(sys.argv[1])), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
