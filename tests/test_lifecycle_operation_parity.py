"""Lifecycle operations work on runs launched from ANY configuration path.

Regression (grounded-extension run, manifest_sha256 8e22d0431fd2b98d,
experiments/2026-08-12-live-grounded-extension-expansion): a root launched
through ``deepreason run --run-manifest`` completed 24 real cycles and then
could not be amended, continued, or read as a result, because the bare CLI
path called the scheduler and printed instead of writing the terminal
records the managed ``TEXT_RUN_SERVICE`` path writes at stop. The refusal
the operator saw was

    AMEND_NOT_AT_TERMINAL: amendment requires a run standing at a valid
    typed terminal stop (terminal authority is current_open_uncommitted)

The pair that must both hold forever: a manifest-launched run reaches a
typed terminal and accepts ``amend``; a genuinely OPEN run still refuses
with the same code, because that refusal is correct for a run that never
stopped.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepreason.amendment import AmendmentError, amend_run, load_amendments
from deepreason.application.text_runs import (
    ensure_lifecycle_documents,
    finalize_stopped_root,
    workload_spec_for_root,
)
from deepreason.evidence import (
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
    load_evidence_dossier,
)
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.ontology import Provenance
from deepreason.run_manifest import bind_run_manifest
from deepreason.runtime.terminal_authority import derive_terminal_authority
from deepreason.storage.blobs import BlobStore
from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem

from tests.test_amendment_epochs import (
    ORIGINAL_QUESTION,
    SOURCE_TEXT,
    SUPPLEMENT_TEXT,
    _admit,
    _evidence_manifest,
    _problem_id,
)
from tests.test_run_input_v6_commitments import _commitment, _write_qualification


def _no_provider_scheduler(frontier=(), survivors=()):
    """A scheduler stand-in that produces one artifact and no stop record.

    The bare CLI path must write the stop itself; a fixture that wrote one
    would hide exactly the record whose absence this module regresses.
    """

    def run(harness, _config, _cycles, _token_budget, **_kwargs):
        harness.create_artifact(
            "Loop gain above unity is what sustains the oscillation.",
            provenance=Provenance(role="conjecturer"),
            problem_id=_problem_id(ORIGINAL_QUESTION),
        )
        harness.record_measure(inputs=["cycle", "0", _problem_id(ORIGINAL_QUESTION)])
        return (
            {
                "frontier": list(frontier),
                "survivors": list(survivors),
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


def _bind_v6_root(tmp_path, *, name, question=ORIGINAL_QUESTION):
    """Bind the immutable v6 authority a manifest-launched run starts from."""

    root = tmp_path / name
    commitment = _commitment()
    problem_id = _problem_id(question)
    dossier = _admit(SOURCE_TEXT, problem_ref=problem_id, locator="delayed.md")
    BlobStore(root / "blobs").put(SOURCE_TEXT.encode("utf-8"))
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id,
            description=question,
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    manifest = _evidence_manifest(run_input.run_input_digest)
    bind_run_manifest(manifest, root)
    _write_qualification(root, manifest)
    spec = ReasoningWorkloadSpec(
        problem=WorkloadProblem(id=problem_id, description=question),
        criteria=(commitment,),
        sources=tuple(source.id for source in dossier.sources),
        allow_rubric=False,
    )
    problem_file = root / "problem.json"
    problem_file.write_text(
        json.dumps(spec.model_dump(mode="json", by_alias=True), sort_keys=True),
        encoding="utf-8",
    )
    return root, manifest, spec, problem_file


def _launch_through_cli(root, manifest, problem_file, monkeypatch, *, cycles=1):
    """Drive the bare `deepreason run --run-manifest` execution path."""

    from deepreason.cli import main as cli_module
    from deepreason.run_manifest import config_from_run_manifest

    monkeypatch.setattr(
        "deepreason.ops.run_scheduler", _no_provider_scheduler()
    )
    args = SimpleNamespace(problem=str(problem_file), token_budget=None)
    return cli_module._execute_bound_run(
        args, manifest, config_from_run_manifest(manifest), root, cycles
    )


def _manifest_launched_root(tmp_path, monkeypatch, *, name="parity-root"):
    root, manifest, spec, problem_file = _bind_v6_root(tmp_path, name=name)
    assert _launch_through_cli(root, manifest, problem_file, monkeypatch) == 0
    return root, manifest, spec


def _open_root(tmp_path, monkeypatch, *, name="open-root"):
    """A root with real reasoning events and no stop — genuinely open."""

    root, manifest, spec, _problem_file = _bind_v6_root(tmp_path, name=name)
    harness = Harness(root)
    from deepreason.ops import seed_problem_payload

    seed_problem_payload(
        harness,
        {
            "commitments": [spec.criteria[0].model_dump(mode="json")],
            "problem": {
                "id": spec.problem.id,
                "description": spec.problem.description,
                "criteria": [spec.criteria[0].id],
            },
        },
    )
    harness.create_artifact(
        "An unfinished conjecture from a run that never stopped.",
        provenance=Provenance(role="conjecturer"),
        problem_id=spec.problem.id,
    )
    return root, manifest, spec


def _source_records(root) -> tuple[str, ...]:
    """Every bound source this root actually introduced, in record order.

    The verifier's own discriminator: an inline artifact carrying an
    ``attached-source-record.v1`` payload. Counting import-role artifacts
    instead would count the dossier's blocks too.
    """

    found = []
    for artifact in Harness(root, read_only=True).state.artifacts.values():
        if not artifact.content_ref.startswith("inline:"):
            continue
        try:
            payload = json.loads(artifact.content_ref.removeprefix("inline:"))
        except (TypeError, json.JSONDecodeError):
            continue
        if payload.get("schema") == "attached-source-record.v1":
            found.append(str((payload.get("source") or {}).get("id") or ""))
    return tuple(sorted(found))


def _supplement(tmp_path, name="sampled.md", text=SUPPLEMENT_TEXT):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _source_text_file(tmp_path):
    path = tmp_path / "delayed.md"
    path.write_text(SOURCE_TEXT, encoding="utf-8")
    return path


# --- the regression pair (R10) ------------------------------------------


def test_manifest_launched_root_reaches_typed_terminal_and_accepts_amend(
    tmp_path, monkeypatch
):
    root, manifest, _spec = _manifest_launched_root(tmp_path, monkeypatch)

    authority = derive_terminal_authority(root, manifest=manifest)
    assert authority.status == "current_valid_committed", authority.detail_code
    for name in (
        "run-stop.json",
        "checkpoint.json",
        "workflow-checkpoint.json",
        "run-result.json",
        "REPLAY_VALIDATION.json",
        "run-request.json",
        "text-workload.json",
        "progress.jsonl",
    ):
        assert (root / name).exists(), f"{name} is missing from a finished run"

    log_before = (root / "log.jsonl").read_bytes()
    result = amend_run(root, attach=(str(_supplement(tmp_path)),))

    assert result["epoch"] == 1
    assert result["admission"]["sources_admitted"] == 1
    assert len(load_amendments(root)) == 1
    # The amendment appended; it edited nothing.
    assert (root / "log.jsonl").read_bytes().startswith(log_before)


def test_interrupted_run_still_refuses_amend_not_at_terminal(
    tmp_path, monkeypatch
):
    root, _manifest, _spec = _open_root(tmp_path, monkeypatch)

    with pytest.raises(AmendmentError) as raised:
        amend_run(root, attach=(str(_supplement(tmp_path)),))

    assert raised.value.code == "AMEND_NOT_AT_TERMINAL"
    assert "current_open_uncommitted" in str(raised.value)
    assert not (root / "amendments.jsonl").exists()


# --- bound evidence is rendered on the bare path too (S5) ---------------


def test_manifest_launched_root_renders_its_bound_evidence(
    tmp_path, monkeypatch
):
    root, _manifest, _spec = _manifest_launched_root(
        tmp_path, monkeypatch, name="evidence-root"
    )

    assert _source_records(root) == tuple(
        source.id for source in load_evidence_dossier(root).sources
    )
    assert verify_root(root)["violations"] == []


# --- continue (S7) ------------------------------------------------------


def test_manifest_launched_root_accepts_continue_preparation(
    tmp_path, monkeypatch
):
    from deepreason.runtime.continuation import prepare_continuation

    root, _manifest, _spec = _manifest_launched_root(
        tmp_path, monkeypatch, name="continue-root"
    )

    record = prepare_continuation(
        root,
        cycles="2",
        tokens="unlimited",
        check_operator_lock=False,
    )
    assert record["schema"] == "deepreason-continuation-v1"
    assert record["seq"] == 0


# --- finalize (S3) ------------------------------------------------------


def test_finalize_reaches_terminal_on_a_root_that_stopped_without_one(
    tmp_path, monkeypatch
):
    """The grounded-extension case: a stopped root, terminalized by APPEND."""

    root, manifest, spec, problem_file = _bind_v6_root(
        tmp_path, name="unterminalized-root"
    )
    # Reproduce the defect exactly: scheduler ran, nothing terminalized.
    from deepreason.cli import main as cli_module

    harness = Harness(root)
    cli_module._load_problem_file(harness, problem_file)
    _no_provider_scheduler()(harness, None, 1, None)
    assert (
        derive_terminal_authority(root, manifest=manifest).status
        == "current_open_uncommitted"
    )

    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }

    payload = finalize_stopped_root(root)

    assert payload["state"] == "completed"
    assert (
        derive_terminal_authority(root, manifest=manifest).status
        == "current_valid_committed"
    )
    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    # Nothing that existed was edited; log.jsonl only grew.
    for name, payload_bytes in before.items():
        if name == "log.jsonl":
            assert after[name].startswith(payload_bytes)
            continue
        assert after[name] == payload_bytes, f"{name} was edited, not appended"
    assert set(before) <= set(after)


def test_finalize_refuses_a_root_that_already_holds_a_terminal(
    tmp_path, monkeypatch
):
    root, _manifest, _spec = _manifest_launched_root(
        tmp_path, monkeypatch, name="already-terminal-root"
    )

    with pytest.raises(ValueError, match="FINALIZE_ALREADY_TERMINAL"):
        finalize_stopped_root(root)


# --- the amendment duplicate-refusal narrowing (S6) ---------------------


def test_amend_refuses_a_source_already_on_the_log(tmp_path, monkeypatch):
    """The refusal keeps its exact force where its rationale holds."""

    root, _manifest, _spec = _manifest_launched_root(
        tmp_path, monkeypatch, name="duplicate-root"
    )

    with pytest.raises(AmendmentError) as raised:
        amend_run(root, attach=(str(_source_text_file(tmp_path)),))

    assert raised.value.code == "AMEND_SOURCE_ALREADY_ADMITTED"


def test_amend_admits_a_bound_but_unintroduced_source(tmp_path, monkeypatch):
    """A source bound but never rendered has no first introduction to repeat.

    Regression (grounded-extension run): six documents were bound into the
    run identity and never turned into source records, so re-admitting them
    adds evidence rather than duplicating it.
    """

    root, manifest, spec, problem_file = _bind_v6_root(
        tmp_path, name="unintroduced-root"
    )
    from deepreason.cli import main as cli_module

    harness = Harness(root)
    cli_module._load_problem_file(harness, problem_file)
    _no_provider_scheduler()(harness, None, 1, None)
    finalize_stopped_root(root)

    assert _source_records(root) == ()

    result = amend_run(root, attach=(str(_source_text_file(tmp_path)),))

    assert result["admission"]["sources_admitted"] == 1
    assert _source_records(root) == tuple(
        source.id for source in load_evidence_dossier(root).sources
    )


# --- lifecycle documents (S4) -------------------------------------------


def test_ensure_lifecycle_documents_is_idempotent(tmp_path, monkeypatch):
    root, _manifest, spec, _problem_file = _bind_v6_root(
        tmp_path, name="documents-root"
    )

    ensure_lifecycle_documents(root, spec=spec)
    first = {
        name: (root / name).read_bytes()
        for name in ("run-request.json", "text-workload.json")
    }
    ensure_lifecycle_documents(root, spec=spec)
    assert {
        name: (root / name).read_bytes()
        for name in ("run-request.json", "text-workload.json")
    } == first

    from deepreason.application.text_runs import _read_request

    assert _read_request(root)["problem"]["id"] == spec.problem.id


def test_workload_spec_for_root_reads_the_roots_own_problem_document(
    tmp_path, monkeypatch
):
    root, _manifest, spec, _problem_file = _bind_v6_root(
        tmp_path, name="spec-root"
    )

    resolved = workload_spec_for_root(Path(root))

    assert resolved.problem.id == spec.problem.id
    assert resolved.problem.description == spec.problem.description
    assert tuple(item.id for item in resolved.criteria) == tuple(
        item.id for item in spec.criteria
    )
