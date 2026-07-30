"""The ``amend`` operation: one atomic typed epoch appended to a stopped run.

Order matters and is fail-closed.  The successor epoch's documents and its
typed record are staged first; the ledger chain is applied second; the chain
line is committed last.  A crash anywhere leaves a staged record with no
committed line — a typed partial chain that ``continue`` refuses to run past.

Recovery from there has two shapes, decided by whether the staged epoch ever
reached the ledger.  Nothing applied: a different amendment supersedes it
outright, because there is no event to orphan.  Events applied: they belong to
that epoch, so a byte-identical re-run completes it and a different amendment
becomes the NEXT epoch.  Nothing in the append-only record is rewritten either
way.
"""

from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path
import shutil
import tempfile

from deepreason.amendment.models import RunAmendmentV1
from deepreason.amendment.state import (
    AMENDMENT_CHAIN_NAME,
    AMENDMENT_RECORD_NAME,
    AmendmentError,
    WORKLOAD_NAME,
    amendment_lock,
    dossier_union,
    epoch_directory,
    load_amendments,
    load_epoch_dossier,
    load_epoch_manifest,
    load_epoch_run_input,
    record_bytes,
    staged_amendment,
)
from deepreason.canonical import canonical_json
from deepreason.evidence.models import (
    AttachedSourceProvenanceV1,
    RunInputManifestV2,
    RunInputProblemV2,
)
from deepreason.evidence.state import (
    EVIDENCE_DOSSIER_HASH_NAME,
    EVIDENCE_DOSSIER_NAME,
    RUN_INPUT_HASH_NAME,
    RUN_INPUT_NAME,
)
from deepreason.locking import ProcessLockBusy, operator_locks


MAX_QUESTION_CHARS = 262_144


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write(target: Path, payload: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_once(target: Path, payload: bytes) -> None:
    """Write a staged epoch document, refusing to replace different bytes."""

    if target.exists():
        if target.read_bytes() != payload:
            raise AmendmentError(
                "AMEND_PENDING_CONFLICT",
                f"staged epoch already binds different {target.name} bytes",
            )
        return
    _atomic_write(target, payload)


def _discard_staged_epoch(directory: Path) -> None:
    """Drop a staged epoch that never reached the ledger or the chain.

    Safe exactly because of what it is not touching: no committed chain
    line names this directory (its sequence is one past the chain's end),
    and its caller has already established that no ledger event sits at or
    above its declared fence. Nothing in the append-only record is rewritten
    — this is pre-commitment staging being restaged.
    """

    shutil.rmtree(directory, ignore_errors=True)


def _reshaped_problem_id(question: str) -> str:
    from deepreason.preparation import _question_digest

    return f"question-{_question_digest(question)[:32]}"


def _require_terminal_stop(root: Path, manifest) -> None:
    from deepreason.runtime.terminal_authority import derive_terminal_authority

    authority = derive_terminal_authority(root, manifest=manifest)
    if not authority.current_valid:
        raise AmendmentError(
            "AMEND_NOT_AT_TERMINAL",
            "amendment requires a run standing at a valid typed terminal stop "
            f"(terminal authority is {authority.status})",
        )


def _admit_supplement(
    root: Path,
    *,
    paths,
    problem_ref: str,
    supplied_by: str,
    allow_partial: bool,
):
    from deepreason.admission.attach import collect_attachment_inputs
    from deepreason.admission.parse import AdmissionError, admit_sources

    try:
        inputs = collect_attachment_inputs(paths)
    except AdmissionError as error:
        raise AmendmentError(error.code, str(error)) from error
    if not inputs:
        raise AmendmentError(
            "AMEND_NO_SOURCES", "supply at least one readable file to attach"
        )
    try:
        dossier, report = admit_sources(
            inputs,
            problem_ref=problem_ref,
            provenance=AttachedSourceProvenanceV1(
                supplied_by=supplied_by,
                acquisition_method="operator-supplied amendment attachments",
                note="Admitted after a typed terminal stop by `deepreason amend`.",
            ),
            allow_partial=allow_partial,
        )
    except AdmissionError as error:
        raise AmendmentError(error.code, str(error)) from error
    if not dossier.sources:
        raise AmendmentError(
            "AMEND_NO_SOURCES",
            "no supplied file was admissible; the refusals are typed in the report",
        )
    from deepreason.storage.blobs import BlobStore

    store = BlobStore(root / "blobs")
    by_digest = {}
    import hashlib

    for item in inputs:
        if item.data:
            by_digest[hashlib.sha256(item.data).hexdigest()] = item.data
    for source in dossier.sources:
        store.put(by_digest[source.content_sha256])
    return dossier, report


def _check_evidence_budget(manifest, dossiers) -> None:
    policy = manifest.inquiry_capability_policy
    evidence = policy.attached_evidence
    if not evidence.enabled:
        raise AmendmentError(
            "AMEND_EVIDENCE_NOT_AUTHORIZED",
            "this run's manifest does not enable attached evidence",
        )
    union = {}
    for item in dossiers:
        for source in item.sources:
            union.setdefault(source.id, source)
    total = sum(source.byte_count for source in union.values())
    if len(union) > evidence.maximum_sources or total > evidence.maximum_total_bytes:
        raise AmendmentError(
            "AMEND_EVIDENCE_BUDGET_EXCEEDED",
            f"amended evidence ({len(union)} sources, {total} bytes) exceeds "
            "the manifest's frozen attached-evidence authority",
        )


def _successor_workload(parent_spec, *, problem_id: str, description: str):
    from deepreason.workloads.text import WorkloadProblem

    return parent_spec.model_copy(
        update={
            "problem": WorkloadProblem(id=problem_id, description=description),
            "sources": (),
        }
    )


def _parent_workload(root: Path, epoch: int, run_input):
    from deepreason.amendment.state import epoch_workload_path
    from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem
    import json

    for candidate in (epoch_workload_path(root, epoch), root / WORKLOAD_NAME):
        if candidate.exists():
            return ReasoningWorkloadSpec.model_validate(
                json.loads(candidate.read_text(encoding="utf-8"))
            )
    return ReasoningWorkloadSpec(
        problem=WorkloadProblem(
            id=run_input.problem.id, description=run_input.problem.description
        )
    )


def _apply_ledger_chain(root: Path, record: RunAmendmentV1, *, supplement) -> None:
    """Register the reshaped question and admit the supplemental sources.

    Both steps are content-addressed and therefore idempotent: completing a
    partially applied amendment re-registers exactly the same problem and the
    same artifacts, appending nothing the first attempt already landed.
    """

    from deepreason.evidence.render import attach_bound_evidence
    from deepreason.harness import Harness
    from deepreason.ontology.problem import Problem, ProblemProvenance

    harness = Harness(root)
    successor_input = load_epoch_run_input(root, record.seq)
    if record.problem_id is not None:
        criteria = [
            item.id
            for item in successor_input.problem.criteria
            if item.id in harness.commitments
        ]
        harness.register_problem(
            Problem(
                id=record.problem_id,
                description=successor_input.problem.description,
                criteria=criteria,
                # A seed trigger, not a successor: the reshaped question is
                # the operator's own, so the scheduler's seed-priority
                # guarantee gives it first claim on the continuation budget.
                # ``from`` records the lineage without touching the record of
                # the question it supersedes.
                provenance=ProblemProvenance.model_validate(
                    {"trigger": "seed", "from": [record.superseded_problem_id]}
                ),
            )
        )
    if supplement is not None:
        attach_bound_evidence(
            harness,
            run_input=successor_input,
            dossier=supplement,
            problem_id=successor_input.problem.id,
        )


def amend_run(
    root: Path | str,
    *,
    attach=(),
    reshape_question: str | None = None,
    supplied_by: str = "operator",
    allow_partial: bool = False,
) -> dict:
    """Append one amendment epoch to a stopped run and return its summary."""

    root = Path(root).resolve()
    attach = tuple(attach)
    if reshape_question is not None:
        reshape_question = reshape_question.strip()
        if not reshape_question:
            raise AmendmentError(
                "AMEND_QUESTION_EMPTY", "a reshaped question must be nonblank"
            )
        if len(reshape_question) > MAX_QUESTION_CHARS:
            raise AmendmentError(
                "AMEND_QUESTION_TOO_LARGE",
                f"a reshaped question exceeds {MAX_QUESTION_CHARS} characters",
            )
    if not attach and reshape_question is None:
        raise AmendmentError(
            "AMEND_EMPTY",
            "an amendment must attach evidence, reshape the question, or both",
        )
    if not root.is_dir() or root.is_symlink():
        raise AmendmentError(
            "AMEND_ROOT_UNAVAILABLE", "amendment requires one regular run root"
        )

    try:
        locks = operator_locks(root, owner="amend", blocking=False)
    except ProcessLockBusy as error:
        raise AmendmentError(
            "AMEND_RUN_ACTIVE", "another operator owns this run root"
        ) from error
    try:
        with amendment_lock(root):
            return _amend_locked(
                root,
                attach=attach,
                reshape_question=reshape_question,
                supplied_by=supplied_by,
                allow_partial=allow_partial,
            )
    finally:
        locks.release()


def _amend_locked(
    root: Path,
    *,
    attach,
    reshape_question: str | None,
    supplied_by: str,
    allow_partial: bool,
) -> dict:
    committed = load_amendments(root)
    parent_epoch = len(committed)
    seq = parent_epoch + 1
    directory = epoch_directory(root, seq)

    parent_manifest = load_epoch_manifest(root, parent_epoch)
    if parent_manifest.schema_version != 6:
        raise AmendmentError(
            "AMEND_MANIFEST_UNSUPPORTED",
            "amendment epochs require a RunManifest v6 root",
        )
    _require_terminal_stop(root, parent_manifest)

    parent_input = load_epoch_run_input(root, parent_epoch)
    if not isinstance(parent_input, RunInputManifestV2):
        raise AmendmentError(
            "AMEND_RUN_INPUT_UNSUPPORTED",
            "amendment epochs require a run-input manifest v2",
        )
    parent_dossier = load_epoch_dossier(root, parent_epoch)

    if reshape_question is None:
        problem_id = None
        successor_problem_id = parent_input.problem.id
        successor_description = parent_input.problem.description
    else:
        problem_id = _reshaped_problem_id(reshape_question)
        if problem_id == parent_input.problem.id:
            raise AmendmentError(
                "AMEND_QUESTION_UNCHANGED",
                "the reshaped question is the question this epoch already asks",
            )
        successor_problem_id = problem_id
        successor_description = reshape_question

    supplement = None
    report = None
    if attach:
        supplement, report = _admit_supplement(
            root,
            paths=attach,
            problem_ref=successor_problem_id,
            supplied_by=supplied_by,
            allow_partial=allow_partial,
        )
        _check_evidence_budget(
            parent_manifest, (*dossier_union(root), supplement)
        )
        successor_dossier = supplement
    else:
        # A question-only amendment cites exactly the dossier its parent did;
        # the epoch's own copy keeps the per-epoch document shape uniform.
        successor_dossier = parent_dossier

    successor_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id=successor_problem_id,
            description=successor_description,
            criteria=parent_input.problem.criteria,
        ),
        evidence_dossier_digest=successor_dossier.dossier_digest,
        brain_snapshot_digest=parent_input.brain_snapshot_digest,
    )
    if successor_input.run_input_digest == parent_input.run_input_digest:
        raise AmendmentError(
            "AMEND_NO_EFFECT",
            "the amendment would reproduce the run input it supersedes",
        )

    from deepreason.harness import Harness

    live_seq = Harness(root, read_only=True)._next_seq
    pending = staged_amendment(root)
    fence_seq = pending.fence_seq if pending is not None else live_seq

    def build(created_at: str) -> RunAmendmentV1:
        return RunAmendmentV1.create(
            seq=seq,
            parent_amendment_digest=(
                committed[-1].amendment_digest if committed else None
            ),
            parent_manifest_digest=parent_manifest.sha256,
            successor_manifest_digest=parent_manifest.sha256,
            parent_run_input_digest=parent_input.run_input_digest,
            successor_run_input_digest=successor_input.run_input_digest,
            parent_dossier_digest=parent_dossier.dossier_digest,
            successor_dossier_digest=successor_dossier.dossier_digest,
            supplemental_dossier_digests=(
                (supplement.dossier_digest,) if supplement is not None else ()
            ),
            superseded_problem_id=(
                parent_input.problem.id if problem_id is not None else None
            ),
            problem_id=problem_id,
            fence_seq=fence_seq,
            created_at=created_at,
        )

    record = build(pending.created_at if pending is not None else _now())
    if pending is not None and pending.amendment_digest != record.amendment_digest:
        # A staged epoch that never reached the ledger has nothing to
        # orphan, so a different amendment supersedes it outright. Once it
        # HAS applied events, those events belong to that epoch: it is
        # completed, never replaced, and the different amendment becomes the
        # next one.
        if pending.fence_seq != live_seq:
            raise AmendmentError(
                "AMEND_PENDING_CONFLICT",
                f"epoch {pending.seq} is staged, has already applied ledger "
                "events, and cannot be replaced; re-run `deepreason amend` "
                "with its original inputs to complete it, then amend again "
                "to open the next epoch",
            )
        _discard_staged_epoch(directory)
        record = build(_now())

    directory.mkdir(parents=True, exist_ok=True)
    _stage_epoch_documents(
        directory,
        manifest=parent_manifest,
        run_input=successor_input,
        dossier=successor_dossier,
        workload=_successor_workload(
            _parent_workload(root, parent_epoch, parent_input),
            problem_id=successor_problem_id,
            description=successor_description,
        ),
        record=record,
    )
    _apply_ledger_chain(root, record, supplement=supplement)
    _commit_chain_line(root, record)

    return {
        "schema": "deepreason-amendment-result-v1",
        "root": str(root),
        "epoch": record.seq,
        "amendment_digest": record.amendment_digest,
        "fence_seq": record.fence_seq,
        "problem_id": record.problem_id,
        "superseded_problem_id": record.superseded_problem_id,
        "run_input_digest": record.successor_run_input_digest,
        "evidence_dossier_digest": record.successor_dossier_digest,
        "supplemental_dossier_digests": list(record.supplemental_dossier_digests),
        "admission": (
            None
            if report is None
            else {
                "evidence_dossier_digest": report.dossier_digest,
                "sources_admitted": report.source_count,
                "blocks": dict(report.block_counts),
                "tiers": dict(report.tier_counts),
                "refusals": list(report.refusals),
            }
        ),
    }


def _stage_epoch_documents(
    directory: Path,
    *,
    manifest,
    run_input,
    dossier,
    workload,
    record: RunAmendmentV1,
) -> None:
    from deepreason.run_manifest import MANIFEST_HASH_NAME, MANIFEST_NAME

    def canonical(model) -> bytes:
        return canonical_json(
            model.model_dump(mode="json", by_alias=True, exclude_none=True)
        )

    _write_once(directory / EVIDENCE_DOSSIER_NAME, canonical(dossier))
    _write_once(
        directory / EVIDENCE_DOSSIER_HASH_NAME,
        (dossier.dossier_digest + "\n").encode("ascii"),
    )
    _write_once(directory / RUN_INPUT_NAME, canonical(run_input))
    _write_once(
        directory / RUN_INPUT_HASH_NAME,
        (run_input.run_input_digest + "\n").encode("ascii"),
    )
    _write_once(directory / MANIFEST_NAME, manifest.canonical_bytes())
    _write_once(
        directory / MANIFEST_HASH_NAME, (manifest.sha256 + "\n").encode("utf-8")
    )
    _write_once(
        directory / WORKLOAD_NAME,
        canonical_json(workload.model_dump(mode="json", by_alias=True)),
    )
    # Staged last: its presence is exactly the claim that every other epoch
    # document above is already durable.
    _write_once(directory / AMENDMENT_RECORD_NAME, record_bytes(record) + b"\n")


def _commit_chain_line(root: Path, record: RunAmendmentV1) -> None:
    path = root / AMENDMENT_CHAIN_NAME
    line = record_bytes(record) + b"\n"
    existing = load_amendments(root)
    if len(existing) >= record.seq:
        if existing[record.seq - 1].amendment_digest != record.amendment_digest:
            raise AmendmentError(
                "AMEND_CHAIN_CONFLICT",
                "the committed chain already binds a different epoch here",
            )
        return
    with path.open("ab") as stream:
        stream.write(line)
        stream.flush()
        os.fsync(stream.fileno())


__all__ = ["MAX_QUESTION_CHARS", "amend_run"]
