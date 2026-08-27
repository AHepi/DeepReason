#!/usr/bin/env python3
"""Compile P-C2b ARM H's bound RunManifest v6: rebuilt harness, REASONING ON.

PREREG.md §2 and §4.  This builder exists to be P-C1's builder with the
problem inputs IMPORTED rather than restated, so that "same instance, same
question, same checker" is a property of the code and not of a promise.

WHAT IS IMPORTED, NEVER COPIED:

    QUESTION   experiments/2026-08-25-change-constructive-frontier/question.py
    CRITERIA   experiments/2026-08-25-change-constructive-frontier/criteria.py

A copy would be a second thing to keep true, and the one failure this
tranche cannot afford is a rematch fought on a question that drifted by a
byte.  `preflight_pc2.py` asserts `question_sha256` against the value
PREREG.md §2 froze, so drift is caught before any provider call.

WHAT DIFFERS FROM `build_manifest_pc1.py` IN THIS FILE, and it is one
thing: `run-config.yaml` names `DISCHARGE_POLICY: discharge-required.v1`.
That field does NOT reach the compiled manifest at all -- PREREG.md §3
FINDING F-A: it is popped from the config echo.  The channel is on in the
run because of DEVIATION D1, the code default, and nothing else.

THE COMPILED MANIFEST IS NEVERTHELESS NOT BYTE-IDENTICAL TO P-C1'S, and
the reason is the tranche's first piece of evidence rather than a defect.
`preflight_pc2.py` measures the whole difference and refuses anything it
cannot account for.  Measured, 2026-08-26, against P-C1's committed
`run/run-manifest.json`:

    inquiry_capability_policy.research.enabled      false -> true
    inquiry_capability_policy.research.backend_identity
                                          "disabled" -> "web.contained.v1"
    inquiry_capability_policy.research.domain_allowlist
                              null -> ["arxiv.org", "en.wikipedia.org"]
    inquiry_capability_policy.research.maximum_requests        0 -> 6
    inquiry_capability_policy.research.maximum_sources         0 -> 3
    inquiry_capability_policy.research.maximum_response_bytes  null -> 4 MiB
    run_input_digest                                        (see below)

The research rows are REBUILD F3 landing: P-C1's YAML said
`RESEARCH_BACKEND: agent` and compiled to a DISABLED research capability,
which is precisely the defect F3's DELIVERY.md names ("Research was
previously off for every run that did not set an environment variable").
The engine config echo itself is byte-identical, so no other default moved.

`run_input_digest` differs because the empty dossier's
`creation_provenance.supplied_by` names THIS builder.  Naming the builder
honestly is worth more than a digest collision with P-C1, and it also mints
a distinct run id, which is what keeps the two roots from ever contending.

COMPILED_AT is P-C1's value, deliberately.  Changing it would change the
manifest sha for no reason, and the manifest sha is exactly the thing this
builder wants to hold still.

Usage:  python build_manifest_pc2b.py <root>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TRANCHE = Path(__file__).resolve().parent
REPO = TRANCHE.parents[1]
FRONTIER = REPO / "experiments" / "2026-08-25-change-constructive-frontier"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(FRONTIER))

from criteria import CRITERIA  # noqa: E402  (P-C1's battery, IMPORTED)
from question import QUESTION  # noqa: E402  (P-C1's bytes, IMPORTED)

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
    engaged_local_simulation_toolchain,
)

CONFIG_PATH = TRANCHE / "run-config.yaml"

# P-C1's value, held still on purpose (see the module docstring).
COMPILED_AT = "2026-08-25T00:00:00Z"

# PREREG.md §2.  The question bytes are frozen by DIGEST, not by copy.
QUESTION_SHA256 = "64b724c4118320989925d111501a8e41cd4518d9b631bb81a6ae048d3cfb5c7e"


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
    # ``config_path`` exists for cycle_soak.py, which hands in a copy of this
    # tranche's config with every endpoint redirected to its local stub. The
    # soak must drive THIS shape; restating the shape there would let the
    # instrument and the launch drift apart.
    config = load_config(config_path or CONFIG_PATH)

    if _question_digest(QUESTION) != QUESTION_SHA256:
        raise SystemExit(
            "QUESTION BYTES DRIFTED from the value PREREG.md §2 froze: "
            f"{_question_digest(QUESTION)} != {QUESTION_SHA256}"
        )

    problem_id = f"question-{_question_digest(QUESTION)[:32]}"

    # An EMPTY dossier, bound explicitly (P-C1's shape, and its reasoning):
    # nothing may be cited because there is nothing to cite, and a
    # construction that appealed to an outside source would be appealing
    # past the only thing that decides it.
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="P-C2b ARM H build_manifest_pc2b.py",
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
        toolchains=(engaged_local_simulation_toolchain(),),
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

    # The runtime Config the run will ACTUALLY see, reconstructed exactly as
    # `application/text_runs.py` reconstructs it. Reported, never asserted
    # here: F-A means this reads "off" whenever deviation D1 is absent, and
    # `preflight_pc2.py` owns the decision to refuse on that.
    from deepreason.run_manifest import config_from_run_manifest

    runtime = config_from_run_manifest(manifest)

    return {
        "attached_evidence_enabled": (
            manifest.inquiry_capability_policy.attached_evidence.enabled
        ),
        "compile_notices": [
            {"code": n.code, "message": n.message}
            for n in (manifest.compile_notices or ())
        ],
        "criteria": [c.id for c in CRITERIA],
        "discharge_policy_declared_in_yaml": config.DISCHARGE_POLICY,
        "discharge_policy_at_runtime": runtime.DISCHARGE_POLICY,
        "dossier_sources": len(dossier.sources),
        "judge_seats_enabled": config.JUDGE_SEATS_ENABLED,
        "manifest_sha256": manifest.sha256,
        "problem_id": problem_id,
        "question_sha256": _question_digest(QUESTION),
        "run_input_digest": run_input.run_input_digest,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: build_manifest_pc2b.py <root>", file=sys.stderr)
        return 2
    print(json.dumps(build(Path(sys.argv[1])), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
