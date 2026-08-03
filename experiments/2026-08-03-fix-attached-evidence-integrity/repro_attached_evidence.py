"""Reproduction for the attached-evidence citation defect (tranche artifact).

Not part of the gate. Run explicitly:

    python -m pytest experiments/2026-08-03-fix-attached-evidence-integrity/repro_attached_evidence.py -q -s

Two v6 roots differing in ONE respect: whether the cycle-time conjecture
carries a `mention` ref to the bound source's source-record artifact. The
control is what every clean root in the corpus looks like. The repro is what
run-0a3e93d6 looks like at seq 43 — a model citing the evidence it was given.

Every piece of scaffolding is imported from the existing gate fixtures; only
the scheduler stub varies, because that is the one thing `_converged_root`
does not expose as a hook.
"""

from __future__ import annotations

import json
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


COMMITTED_ROOT = (
    "experiments/2026-08-02-stress-triplet/home-triage/runs/"
    "run-0a3e93d6e8031e2e6d1d21dde2fa93cc"
)


def _source_record_id(harness) -> str:
    """The attached-source-record.v1 artifact, found the way verify_root finds it."""

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


def _run(tmp_path, monkeypatch, *, name, cite_the_source):
    """One converged v6 root whose single conjecture may or may not cite evidence."""

    root = tmp_path / name
    commitment = _commitment()
    problem_id = _problem_id(ORIGINAL_QUESTION)
    dossier, _report = admit_sources(
        [AdmissionInput(locator="delayed.md", data=SOURCE_TEXT.encode("utf-8"))],
        problem_ref=problem_id,
        provenance=AttachedSourceProvenanceV1(
            supplied_by="repro fixture",
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
        # The one varying line. A conjecture that cites its evidence is the
        # system working; it must not decide the root's integrity verdict.
        interface = None
        if cite_the_source:
            interface = Interface(
                refs=[Ref(target=_source_record_id(harness), role="mention")]
            )
        harness.create_artifact(
            "Loop gain above unity is what sustains the oscillation.",
            interface=interface,
            provenance=Provenance(role="conjecturer"),
            problem_id=problem_id,
        )
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


def test_repro_a_cited_source_invalidates_an_otherwise_clean_root(
    tmp_path, monkeypatch
):
    control = _run(tmp_path, monkeypatch, name="control", cite_the_source=False)
    control_findings = [
        v for v in verify_root(control)["violations"] if v["check"] == "attached-evidence"
    ]
    print("\ncontrol  (conjecture does NOT cite the source):", control_findings)

    cited = _run(tmp_path, monkeypatch, name="cited", cite_the_source=True)
    cited_findings = [
        v for v in verify_root(cited)["violations"] if v["check"] == "attached-evidence"
    ]
    print("repro    (conjecture DOES cite the source):", cited_findings)

    assert control_findings == []
    assert len(cited_findings) == 1
    assert cited_findings[0]["detail"].endswith(
        "lacks one reliability-dependent candidate evidence artifact"
    )

    # The artifact the finding calls missing is present in both roots.
    harness = Harness(cited, read_only=True)
    record_ref = _source_record_id(harness)
    proper = [
        a
        for a in harness.state.artifacts.values()
        if any(r.target == record_ref and r.role == "mention" for r in a.interface.refs)
        and any(r.role == "dependence" for r in a.interface.refs)
    ]
    print("reliability-dependent candidate evidence artifacts present:", len(proper))
    assert len(proper) == 1


def test_repro_the_committed_root_shows_the_same_single_finding():
    """Record replay: the defect as the live run recorded it. Read-only."""

    findings = verify_root(pathlib.Path(COMMITTED_ROOT))
    print("\ncommitted run-0a3e93d6 violations:", findings["violations"])
    assert [v["check"] for v in findings["violations"]] == ["attached-evidence"]
