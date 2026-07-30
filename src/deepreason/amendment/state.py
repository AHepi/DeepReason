"""Durable amendment-epoch chain: staging, commitment, and resolution.

Nothing here ever edits a bound record.  Epoch 0 is the manifest, run input,
and dossier bound at the run root; every later epoch is a directory under
``run-epochs/`` holding its own complete, canonical documents, chained by an
append-only ``run-amendments.jsonl``.

Roots with no amendment pay one ``exists`` check: every resolver short-circuits
to the epoch-0 documents when the chain file is absent, so historical roots
read exactly as they always did.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path

from deepreason.amendment.models import RunAmendmentV1
from deepreason.canonical import canonical_json
from deepreason.evidence.models import EvidenceDossier, RunInputManifest
from deepreason.evidence.state import (
    RunInputError,
    load_evidence_dossier,
    load_run_input,
)
from deepreason.locking import ProcessLock


AMENDMENT_CHAIN_NAME = "run-amendments.jsonl"
AMENDMENT_EPOCH_DIR = "run-epochs"
AMENDMENT_RECORD_NAME = "run-amendment.json"
AMENDMENT_LOCK_NAME = ".run-amendment.lock"
WORKLOAD_NAME = "text-workload.json"

_MAX_CHAIN_BYTES = 4 * 1024 * 1024
_MAX_EPOCHS = 999


class AmendmentError(ValueError):
    """A typed, durable reason an amendment cannot be read or applied."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


@contextmanager
def amendment_lock(root: Path):
    with ProcessLock(
        Path(root) / AMENDMENT_LOCK_NAME, owner="run-amendment", blocking=True
    ):
        yield


def epoch_directory(root: Path | str, seq: int) -> Path:
    """The canonical directory holding epoch ``seq``'s bound documents."""

    if not 1 <= seq <= _MAX_EPOCHS:
        raise AmendmentError(
            "AMENDMENT_EPOCH_OUT_OF_RANGE", f"epoch {seq} is outside the epoch range"
        )
    return Path(root) / AMENDMENT_EPOCH_DIR / f"{seq:03d}"


def _chain_path(root: Path | str) -> Path:
    return Path(root) / AMENDMENT_CHAIN_NAME


def _read_chain_lines(root: Path | str) -> list[str]:
    path = _chain_path(root)
    try:
        if path.is_symlink() or not path.is_file():
            return []
        if path.stat().st_size > _MAX_CHAIN_BYTES:
            raise AmendmentError(
                "AMENDMENT_CHAIN_INVALID", "amendment chain exceeds its size bound"
            )
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise AmendmentError(
            "AMENDMENT_CHAIN_UNREADABLE", f"cannot read {AMENDMENT_CHAIN_NAME}: {error}"
        ) from error
    return [line for line in raw.splitlines() if line]


def _decode_record(line: str) -> RunAmendmentV1:
    try:
        payload = json.loads(line)
        record = RunAmendmentV1.model_validate(payload)
    except ValueError as error:
        raise AmendmentError(
            "AMENDMENT_RECORD_INVALID", "amendment record is not canonical"
        ) from error
    if canonical_json(
        record.model_dump(mode="json", by_alias=True, exclude_none=True)
    ).decode("utf-8") != line:
        raise AmendmentError(
            "AMENDMENT_RECORD_INVALID", "amendment record bytes are not canonical"
        )
    return record


def record_bytes(record: RunAmendmentV1) -> bytes:
    return canonical_json(
        record.model_dump(mode="json", by_alias=True, exclude_none=True)
    )


def load_amendments(root: Path | str) -> tuple[RunAmendmentV1, ...]:
    """Load and structurally validate the committed amendment chain.

    Structural validation is deliberately local: contiguous sequence numbers,
    an unbroken record-digest chain, strictly increasing fences, and matching
    parent/successor document digests.  Whether the ledger honours those
    fences is ``verify_root``'s question, not this reader's.
    """

    records: list[RunAmendmentV1] = []
    previous: RunAmendmentV1 | None = None
    for index, line in enumerate(_read_chain_lines(root)):
        record = _decode_record(line)
        expected_seq = index + 1
        if record.seq != expected_seq:
            raise AmendmentError(
                "AMENDMENT_CHAIN_INVALID",
                f"amendment at line {index} declares epoch {record.seq}",
            )
        if previous is not None and (
            record.parent_amendment_digest != previous.amendment_digest
            or record.parent_manifest_digest != previous.successor_manifest_digest
            or record.parent_run_input_digest != previous.successor_run_input_digest
            or record.parent_dossier_digest != previous.successor_dossier_digest
            or record.fence_seq <= previous.fence_seq
        ):
            raise AmendmentError(
                "AMENDMENT_CHAIN_BROKEN",
                f"amendment epoch {record.seq} does not chain to its parent",
            )
        records.append(record)
        previous = record
    return tuple(records)


def staged_amendment(root: Path | str) -> RunAmendmentV1 | None:
    """The staged record of an epoch whose commitment has not landed yet.

    A crash between staging and commitment leaves exactly this: a typed
    partial chain.  Readers refuse to continue past it and ``amend`` completes
    it only from byte-identical staged intent.
    """

    committed = load_amendments(root)
    pending_path = epoch_directory(root, len(committed) + 1) / AMENDMENT_RECORD_NAME
    try:
        if pending_path.is_symlink() or not pending_path.is_file():
            return None
        raw = pending_path.read_text(encoding="utf-8")
    except OSError as error:
        raise AmendmentError(
            "AMENDMENT_RECORD_UNREADABLE", f"cannot read staged amendment: {error}"
        ) from error
    return _decode_record(raw.strip())


def require_no_partial_amendment(root: Path | str, *, code: str) -> None:
    """Fail closed while a staged amendment has not been committed."""

    if staged_amendment(root) is not None:
        raise AmendmentError(
            code,
            "this root carries a staged amendment that was never committed; "
            "re-run `deepreason amend` with the same inputs to complete it",
        )


def current_epoch(root: Path | str) -> int:
    return len(load_amendments(root))


def _epoch_root(root: Path | str, epoch: int) -> Path:
    return Path(root) if epoch == 0 else epoch_directory(root, epoch)


def _epoch_manifest_path(root: Path | str, epoch: int) -> Path:
    from deepreason.run_manifest import MANIFEST_NAME

    return _epoch_root(root, epoch) / MANIFEST_NAME


def load_epoch_manifest(root: Path | str, epoch: int):
    from deepreason.run_manifest import load_run_manifest

    return load_run_manifest(_epoch_manifest_path(root, epoch))


def load_epoch_run_input(root: Path | str, epoch: int) -> RunInputManifest:
    return load_run_input(_epoch_root(root, epoch))


def load_epoch_dossier(root: Path | str, epoch: int) -> EvidenceDossier:
    return load_evidence_dossier(_epoch_root(root, epoch))


def verify_epoch_run_input(root: Path | str, epoch: int) -> dict:
    """Verify one epoch's run input and dossier against their own digests."""

    from deepreason.evidence.state import verify_run_input

    if epoch == 0:
        return verify_run_input(root)
    # Later epochs share the root's content-addressed blob store: source bytes
    # are never copied, only referenced by a second dossier.
    directory = epoch_directory(root, epoch)
    run_input = load_run_input(directory)
    dossier = load_evidence_dossier(directory)
    if run_input.evidence_dossier_digest != dossier.dossier_digest:
        raise RunInputError("RUN_INPUT_DOSSIER_MISMATCH", "epoch records disagree")
    # A later epoch may cite a dossier admitted for the question it
    # supersedes; the amendment record, not this pair, binds the lineage.
    from deepreason.evidence.state import _check_source_blobs

    _check_source_blobs(Path(root), dossier)
    report = {
        "valid": True,
        "run_input_digest": run_input.run_input_digest,
        "evidence_dossier_digest": dossier.dossier_digest,
        "source_count": len(dossier.sources),
        "source_bytes": dossier.total_byte_count,
        "input_schema_version": int(getattr(run_input, "input_schema_version", 1)),
    }
    return report


def epoch_problem_ids(root: Path | str) -> frozenset[str]:
    """Every question this root has asked, oldest epoch through newest.

    A superseded question is still a question the run bound evidence for, so
    it keeps its claim on the dossier the same way its positions keep their
    status.
    """

    ids = set()
    for epoch in range(current_epoch(root) + 1):
        try:
            ids.add(load_epoch_run_input(root, epoch).problem.id)
        except (RunInputError, OSError):
            continue
    return frozenset(ids)


def dossier_union(root: Path | str) -> tuple[EvidenceDossier, ...]:
    """Every dossier bound to this root, oldest epoch first, deduped.

    Dossiers are immutable and cumulative: a citation verified against
    epoch 0's dossier verifies identically after any number of amendments,
    because that dossier is still loaded and still checked against its own
    digest.
    """

    seen: set[str] = set()
    dossiers: list[EvidenceDossier] = []
    for epoch in range(current_epoch(root) + 1):
        try:
            dossier = load_epoch_dossier(root, epoch)
        except (RunInputError, OSError):
            continue
        if dossier.dossier_digest in seen:
            continue
        seen.add(dossier.dossier_digest)
        dossiers.append(dossier)
    return tuple(dossiers)


def union_citable_blocks(root: Path | str) -> tuple:
    """Admission blocks from every bound dossier, in epoch order."""

    blocks: list = []
    known: set[str] = set()
    for dossier in dossier_union(root):
        for block in getattr(dossier, "blocks", ()):
            if block.id in known:
                continue
            known.add(block.id)
            blocks.append(block)
    return tuple(blocks)


def epoch_workload_path(root: Path | str, epoch: int) -> Path:
    return _epoch_root(root, epoch) / WORKLOAD_NAME


__all__ = [
    "AMENDMENT_CHAIN_NAME",
    "AMENDMENT_EPOCH_DIR",
    "AMENDMENT_LOCK_NAME",
    "AMENDMENT_RECORD_NAME",
    "AmendmentError",
    "amendment_lock",
    "current_epoch",
    "dossier_union",
    "epoch_directory",
    "epoch_problem_ids",
    "epoch_workload_path",
    "load_amendments",
    "load_epoch_dossier",
    "load_epoch_manifest",
    "load_epoch_run_input",
    "record_bytes",
    "require_no_partial_amendment",
    "staged_amendment",
    "union_citable_blocks",
    "verify_epoch_run_input",
]
