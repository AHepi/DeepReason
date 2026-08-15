"""Regression (stress-triplet run-0a3e93d6): citing attached evidence must not
invalidate the root.

The triage run of experiments/2026-08-02-stress-triplet completed rc=5 with one
verify_root violation because its conjecture at seq 43 carried a mention ref to
the bound source's source-record artifact, and the attached-evidence check
selected candidates by mention alone. The reliability-dependent candidate the
finding named as missing was present at seq 4 the whole time. The candidate
predicate now demands the writer's discriminator — import provenance — which
rule-driven creation can never carry; the uniqueness and dependence demands are
unchanged and still catch real writer faults.
"""

from __future__ import annotations

import pytest
import pathlib

from deepreason.admission.parse import AdmissionInput, admit_sources
from deepreason.application import InspectTextRunIntentV1, StartTextRunIntentV1
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
)
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.ontology import Interface, Provenance, Ref
from deepreason.run_manifest import bind_run_manifest
from deepreason.runtime.terminal_authority import derive_terminal_authority
from deepreason.storage.blobs import BlobStore
from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem

from tests.test_amendment_epochs import (
    ORIGINAL_QUESTION,
    SOURCE_TEXT,
    _evidence_manifest,
    _problem_id,
)
from tests.test_run_input_v6_commitments import _commitment, _write_qualification
from tests.test_v6_resumed_terminal_revalidation import _record_converged_stop


COMMITTED_ROOT = pathlib.Path(
    "experiments/2026-08-02-stress-triplet/home-triage/runs/"
    "run-0a3e93d6e8031e2e6d1d21dde2fa93cc"
)


def _source_record_id(harness) -> str:
    """The attached-source-record.v1 artifact, found as verify_root finds it."""

    import json

    for artifact in harness.state.artifacts.values():
        if not artifact.content_ref.startswith("inline:"):
            continue
        try:
            value = json.loads(artifact.content_ref.removeprefix("inline:"))
        except (TypeError, json.JSONDecodeError):
            continue
        if value.get("schema") == "attached-source-record.v1":
            return artifact.id
    raise AssertionError("fixture bound no attached source record")


def _attached_evidence_root(tmp_path, monkeypatch, *, name, in_cycle):
    """A converged v6 root with one bound source; `in_cycle` runs extra
    artifact creation inside the scheduler stub, after evidence attachment."""

    root = tmp_path / name
    commitment = _commitment()
    problem_id = _problem_id(ORIGINAL_QUESTION)
    dossier, _report = admit_sources(
        [AdmissionInput(locator="delayed.md", data=SOURCE_TEXT.encode("utf-8"))],
        problem_ref=problem_id,
        provenance=AttachedSourceProvenanceV1(
            supplied_by="regression fixture",
            acquisition_method="offline construction",
        ),
    )
    BlobStore(root / "blobs").put(SOURCE_TEXT.encode("utf-8"))
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id,
            description=ORIGINAL_QUESTION,
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    manifest = _evidence_manifest(run_input.run_input_digest)
    bind_run_manifest(manifest, root)
    _write_qualification(root, manifest)

    def finish_without_provider(harness, _config, _cycles, token_budget, **_kwargs):
        in_cycle(harness, problem_id)
        stop = _record_converged_stop(root, manifest, harness)
        return (
            {"frontier": [], "survivors": [], "stop_reason": stop["reason"]},
            None,
            {
                "metered_tokens": None,
                "logged_tokens_this_run": 0,
                "delta": None,
                "note": "offline no-provider fixture",
            },
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", finish_without_provider)
    service = TextRunApplicationService(TextRunWorkerRegistry())
    started = service.start(
        StartTextRunIntentV1(
            root=str(root),
            workload=ReasoningWorkloadSpec(
                problem=WorkloadProblem(id=problem_id, description=ORIGINAL_QUESTION),
                criteria=(commitment,),
                allow_rubric=False,
            ),
            run_manifest_ref=str(tmp_path / "unused-manifest.json"),
            budget={"cycles": 1, "token_budget": "unlimited"},
        ),
        manifest_override=manifest,
        credential_checker=lambda _manifest: [],
    )
    service.wait(started.root, timeout=30)
    service.result(InspectTextRunIntentV1(root=started.root))
    assert derive_terminal_authority(root, manifest=manifest).current_valid
    return root


def _attached_evidence_findings(root) -> list[dict]:
    return [
        v
        for v in verify_root(root)["violations"]
        if v["check"] == "attached-evidence"
    ]


def test_a_conjecture_citing_the_bound_source_leaves_the_root_valid(
    tmp_path, monkeypatch
):
    """Regression (stress-triplet run-0a3e93d6): the live failure shape —
    a cycle-time conjecture mentioning the source record."""

    def conjecture_cites_the_source(harness, problem_id):
        harness.create_artifact(
            "Loop gain above unity is what sustains the oscillation.",
            interface=Interface(
                refs=[Ref(target=_source_record_id(harness), role="mention")]
            ),
            provenance=Provenance(role="conjecturer"),
            problem_id=problem_id,
        )

    root = _attached_evidence_root(
        tmp_path, monkeypatch, name="cited", in_cycle=conjecture_cites_the_source
    )
    assert _attached_evidence_findings(root) == []


@pytest.mark.skip(
    reason="pre-v2 root: carries the deleted `successor` trigger and no longer "
    "loads. Retired by the 2026-08-14 law, not repaired."
)
def test_the_committed_triage_root_verifies_clean():
    """RETIRED — and this one is a real coverage LOSS, said plainly.

    Regression (stress-triplet run-0a3e93d6): the committed live record,
    replayed read-only, reported no integrity breach on its citation. The root
    carries `trigger: "successor"`, and that member was deleted when the
    decommissioned website pipeline's remnant went (operator ruling
    2026-08-15), so v2 readers cannot load it at all.

    Under the 2026-08-14 law — "old runs do not need to be valid or
    returnable" — the root is an artifact of its own version and is owed
    nothing, so widening a reader to keep this green would be the wrong fix.
    But the property it guarded is real and now has no witness: nothing else
    replays a committed root and checks the citation integrity of an attached
    evidence record. The honest disposition is a skip that says so, and the
    coverage returns when a current-version root exercises the same path.
    """

    report = verify_root(COMMITTED_ROOT)
    assert report["violations"] == []


def test_a_duplicate_import_candidate_still_fails_uniqueness(tmp_path, monkeypatch):
    """The narrowing must not weaken the demand it narrows: a second
    import-role artifact mentioning the same source record — a writer fault —
    is still exactly one attached-evidence violation."""

    def duplicate_import_candidate(harness, problem_id):
        record_ref = _source_record_id(harness)
        anchor = harness.create_artifact(
            "source-reliability: duplicate anchor for the writer-fault fixture",
            provenance=Provenance(role="import"),
        )
        harness.create_artifact(
            "a second import-time artifact claiming the same source record",
            interface=Interface(
                refs=[
                    Ref(target=anchor.id, role="dependence"),
                    Ref(target=record_ref, role="mention"),
                ]
            ),
            provenance=Provenance(role="import"),
            problem_id=problem_id,
        )

    root = _attached_evidence_root(
        tmp_path, monkeypatch, name="duplicated", in_cycle=duplicate_import_candidate
    )
    findings = _attached_evidence_findings(root)
    assert len(findings) == 1
    assert findings[0]["detail"].endswith(
        "lacks one reliability-dependent candidate evidence artifact"
    )
