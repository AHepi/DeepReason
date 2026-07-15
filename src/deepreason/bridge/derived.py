"""Explicit dual-root grounded bridge views over historical run fences.

The source is always opened through :meth:`Harness.at` and is never used as a
write sink.  The destination is a newly reserved run root with its own v3
manifest, object store, blob store, and append-only event log.  Canonical
records contain only a path-independent digest and source sequence fence; no
source filesystem path crosses the model or persistence boundary.
"""

from __future__ import annotations

import os
import re
import stat
from contextlib import ExitStack
from copy import copy
from dataclasses import dataclass
from pathlib import Path

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.harness import Harness
from deepreason.storage.objects import ObjectStore


_SOURCE_DIGEST_DOMAIN = b"deepreason.bridge.derived-source.v1\0"
_BLOB_REF = re.compile(r"^[0-9a-f]{64}$")
_MAX_SOURCE_BLOB_BYTES = 64 * 1024 * 1024


class DerivedBridgeError(ValueError):
    """An explicit derived-view precondition was not met."""


@dataclass(frozen=True)
class DerivedBridgeSource:
    """One read-only source fence and its separate, not-yet-created sink."""

    harness: Harness
    source_run_digest: str
    formal_seq: int
    destination_root: Path
    sealed_blob_refs: frozenset[str]


def _is_link_like(path: Path, observed: os.stat_result) -> bool:
    """Recognize symlinks and, where Python exposes them, Windows junctions."""

    if stat.S_ISLNK(observed.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if getattr(observed, "st_file_attributes", 0) & reparse_flag:
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def _same_identity(before: os.stat_result, after: os.stat_result) -> bool:
    if stat.S_IFMT(before.st_mode) != stat.S_IFMT(after.st_mode):
        return False
    if before.st_ino and after.st_ino:
        return (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    # Some Windows filesystems do not expose a useful inode.  This fallback is
    # deliberately conservative and supplements, rather than replaces, the
    # no-link checks on every path component.
    return (
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) == (
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )


def _checked_directory(path: Path) -> os.stat_result:
    try:
        observed = path.lstat()
    except OSError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID") from error
    if not stat.S_ISDIR(observed.st_mode) or _is_link_like(path, observed):
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
    return observed


def _read_verified_blob(store, ref: str) -> bytes:
    """Read one bounded content-addressed blob without following links."""

    if _BLOB_REF.fullmatch(ref) is None:
        raise KeyError("source blob reference is not a canonical digest")
    root = Path(store.root)
    shard = root / ref[:2]
    path = shard / ref
    root_before = _checked_directory(root)
    shard_before = _checked_directory(shard)
    try:
        observed = path.lstat()
    except FileNotFoundError as error:
        raise KeyError("source blob is absent") from error
    except OSError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID") from error
    if (
        not stat.S_ISREG(observed.st_mode)
        or _is_link_like(path, observed)
        or observed.st_nlink != 1
        or observed.st_size > _MAX_SOURCE_BLOB_BYTES
    ):
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_BINARY", 0)
    )
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_BINARY", 0)
    )
    supports_dir_fd = os.open in getattr(os, "supports_dir_fd", set())
    try:
        with ExitStack() as stack:
            root_descriptor = shard_descriptor = None
            if supports_dir_fd:
                root_descriptor = os.open(root, directory_flags)
                stack.callback(os.close, root_descriptor)
                if not _same_identity(root_before, os.fstat(root_descriptor)):
                    raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
                shard_descriptor = os.open(
                    ref[:2], directory_flags, dir_fd=root_descriptor
                )
                stack.callback(os.close, shard_descriptor)
                if not _same_identity(shard_before, os.fstat(shard_descriptor)):
                    raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
                descriptor = os.open(ref, flags, dir_fd=shard_descriptor)
            else:
                descriptor = os.open(path, flags)
            try:
                wrapped = os.fdopen(descriptor, "rb")
            except BaseException:
                os.close(descriptor)
                raise
            stream = stack.enter_context(wrapped)
            opened = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or opened.st_size != observed.st_size
                or opened.st_size > _MAX_SOURCE_BLOB_BYTES
            ):
                raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
            data = stream.read(_MAX_SOURCE_BLOB_BYTES + 1)
            root_current = root.lstat()
            shard_current = shard.lstat()
            current = path.lstat()
            if root_descriptor is not None and not _same_identity(
                root_before, os.fstat(root_descriptor)
            ):
                raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
            if shard_descriptor is not None and not _same_identity(
                shard_before, os.fstat(shard_descriptor)
            ):
                raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
    except DerivedBridgeError:
        raise
    except OSError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID") from error
    if (
        len(data) != opened.st_size
        or len(data) > _MAX_SOURCE_BLOB_BYTES
        or not stat.S_ISREG(current.st_mode)
        or _is_link_like(path, current)
        or current.st_nlink != 1
        or current.st_size != opened.st_size
        or _is_link_like(root, root_current)
        or _is_link_like(shard, shard_current)
        or not _same_identity(root_before, root_current)
        or not _same_identity(shard_before, shard_current)
        or not _same_identity(opened, current)
        or sha256_hex(data) != ref
    ):
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
    return data


class _VerifiedBlobView:
    """Read-only blob facade that verifies every byte consumed by the pack."""

    def __init__(self, store, *, sealed_refs: set[str]) -> None:
        self.root = store.root
        self.read_only = True
        self._sealed_refs = frozenset(sealed_refs)
        self._cache: dict[str, bytes] = {}

    def get(self, ref: str) -> bytes:
        if ref in self._sealed_refs:
            # Match canonical holdout semantics at the historical fence even
            # if a later Reveal has since copied these bytes into BlobStore.
            raise KeyError("source blob is sealed at the requested fence")
        if ref not in self._cache:
            try:
                self._cache[ref] = _read_verified_blob(self, ref)
            except (KeyError, DerivedBridgeError) as error:
                # Evidence helpers intentionally tolerate a missing blob in
                # ordinary historical views.  A derived bridge must instead
                # fail closed, and this non-ValueError signal cannot be
                # swallowed by those compatibility fallbacks.
                raise _DerivedSourceIntegrityError from error
        return self._cache[ref]

    def is_grounding_available(self, ref: str) -> bool:
        """Return fence-pinned availability without reading sealed bytes."""

        return ref not in self._sealed_refs


class _DerivedSourceIntegrityError(RuntimeError):
    """A source blob became unavailable while a fixed pack was assembled."""


def _verified_source_view(
    harness: Harness, *, sealed_refs: frozenset[str] | set[str]
) -> Harness:
    view = copy(harness)
    view.blobs = _VerifiedBlobView(
        harness.blobs,
        sealed_refs=set(sealed_refs),
    )
    return view


def _holdout_marker_exists(harness: Harness, ref: str) -> bool:
    """Inspect only metadata needed to identify canonical sealed content."""

    holdout_root = harness.root / "holdout"
    try:
        root_stat = holdout_root.lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID") from error
    if not stat.S_ISDIR(root_stat.st_mode) or _is_link_like(holdout_root, root_stat):
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
    marker = holdout_root / ref
    try:
        marker_stat = marker.lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID") from error
    if (
        not stat.S_ISREG(marker_stat.st_mode)
        or _is_link_like(marker, marker_stat)
        or marker_stat.st_nlink != 1
    ):
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_BLOB_INVALID")
    return True


def _sealed_blob_refs(harness: Harness, events) -> set[str]:
    pinned = getattr(harness.blobs, "sealed_refs", None)
    if pinned is not None:
        return set(pinned)
    revealed_artifacts = {
        artifact_id
        for event in events
        if event.rule.value == "Reveal"
        for artifact_id in event.inputs
    }
    return {
        artifact.content_ref
        for artifact_id, artifact in harness.state.artifacts.items()
        if artifact_id not in revealed_artifacts
        and not artifact.content_ref.startswith("inline:")
        and _holdout_marker_exists(harness, artifact.content_ref)
    }


def _required_blob_refs(
    harness: Harness, events, *, sealed_refs: set[str]
) -> set[str]:
    """Return the explicit canonical blob closure for a formal source fence."""

    refs = {
        artifact.content_ref
        for artifact in harness.state.artifacts.values()
        if not artifact.content_ref.startswith("inline:")
        and artifact.content_ref not in sealed_refs
    }
    refs.update(
        warrant.trace_ref
        for warrant in harness.warrants.values()
        if warrant.trace_ref
    )
    for event in events:
        if event.llm is None:
            continue
        for ref in (event.llm.prompt_ref, event.llm.raw_ref):
            if ref:
                refs.add(ref)
        for attempt in event.llm.attempt_trace:
            for ref in (
                attempt.prompt_ref,
                attempt.raw_ref,
                attempt.diagnostic_ref,
            ):
                if ref:
                    refs.add(ref)
    return refs


def _absolute(path: Path | str) -> Path:
    value = Path(path)
    return value if value.is_absolute() else Path.cwd() / value


def _reject_symlink_components(path: Path) -> None:
    """Reject an existing symlink at the leaf or in any parent component."""

    absolute = _absolute(path)
    parts = absolute.parts
    current = Path(parts[0])
    for part in parts[1:]:
        current = current / part
        try:
            observed = current.lstat()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise DerivedBridgeError("BRIDGE_DERIVED_PATH_INVALID") from error
        if _is_link_like(current, observed):
            raise DerivedBridgeError("BRIDGE_DERIVED_SYMLINK_REJECTED")


def _validate_roots(
    source_root: Path | str, destination_root: Path | str
) -> tuple[Path, Path]:
    source = _absolute(source_root)
    destination = _absolute(destination_root)
    _reject_symlink_components(source)
    _reject_symlink_components(destination)

    try:
        source_stat = source.lstat()
    except FileNotFoundError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_NOT_FOUND") from error
    except OSError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_INVALID") from error
    if not stat.S_ISDIR(source_stat.st_mode):
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_INVALID")
    try:
        source = source.resolve(strict=True)
        destination = destination.resolve(strict=False)
    except OSError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_PATH_INVALID") from error
    if (
        source == destination
        or destination.is_relative_to(source)
        or source.is_relative_to(destination)
    ):
        raise DerivedBridgeError("BRIDGE_DERIVED_ROOTS_OVERLAP")
    try:
        destination.lstat()
    except FileNotFoundError:
        pass
    except OSError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_DESTINATION_INVALID") from error
    else:
        raise DerivedBridgeError("BRIDGE_DERIVED_DESTINATION_EXISTS")
    if not destination.parent.is_dir():
        raise DerivedBridgeError("BRIDGE_DERIVED_DESTINATION_PARENT_NOT_FOUND")
    return source, destination


def _source_snapshot(harness: Harness) -> tuple[str, frozenset[str]]:
    """Return one digest and the exact holdout availability snapshot it binds."""

    if not harness._read_only:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_NOT_READ_ONLY")
    formal_seq = harness._next_seq - 1
    if formal_seq < 0:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_EMPTY")
    prefix = list(harness.log.read(upto_seq=formal_seq))
    events = [
        event.model_dump(mode="json", by_alias=True, exclude_none=True)
        for event in prefix
    ]
    if len(events) != formal_seq + 1:
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_FENCE_INVALID")
    object_ids = {
        object_id
        for event in prefix
        for object_id in (*event.inputs, *event.outputs)
    }
    object_ids.update(harness.state.problems)
    object_ids.update(harness.state.artifacts)
    object_ids.update(harness.commitments)
    object_ids.update(harness.warrants)
    materialized = {
        **{key: ("problem", value) for key, value in harness.state.problems.items()},
        **{key: ("artifact", value) for key, value in harness.state.artifacts.items()},
        **{key: ("commitment", value) for key, value in harness.commitments.items()},
        **{key: ("warrant", value) for key, value in harness.warrants.items()},
    }
    canonical_objects = []
    for object_id in sorted(object_ids):
        try:
            schema, record = harness.objects.get(object_id)
        except KeyError:
            # Prompt/raw/blob refs are content-addressed elsewhere and remain
            # bound by the canonical event.  Only object-store records belong
            # in this sorted materialized-object component.
            continue
        expected = materialized.get(object_id)
        if expected is not None and (schema, record) != expected:
            raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_OBJECT_MISMATCH")
        canonical_objects.append(ObjectStore._record(schema, record))
    sealed_hashes = _sealed_blob_refs(harness, prefix)
    referenced_hashes = _required_blob_refs(
        harness, prefix, sealed_refs=sealed_hashes
    )
    verified_blobs = []
    for ref in sorted(referenced_hashes):
        try:
            _read_verified_blob(harness.blobs, ref)
        except KeyError as error:
            raise DerivedBridgeError(
                "BRIDGE_DERIVED_SOURCE_BLOB_INVALID"
            ) from error
        verified_blobs.append(ref)
    payload = {
        "schema": "deepreason.bridge.derived-source.v1",
        "formal_seq": formal_seq,
        "events": events,
        "objects": canonical_objects,
        "blobs": verified_blobs,
        "sealed_blobs": sorted(sealed_hashes),
        # Formal records are included because legacy problem IDs need not be
        # content hashes.  Sorting by stable IDs makes this independent of
        # dictionary insertion details as well as filesystem placement.
        "formal_state": harness.state.model_dump(mode="json", by_alias=True),
        "commitments": [
            harness.commitments[key].model_dump(mode="json", by_alias=True)
            for key in sorted(harness.commitments)
        ],
        "warrants": [
            harness.warrants[key].model_dump(mode="json", by_alias=True)
            for key in sorted(harness.warrants)
        ],
    }
    return (
        sha256_hex(_SOURCE_DIGEST_DOMAIN + canonical_json(payload)),
        frozenset(sealed_hashes),
    )


def source_snapshot_digest(harness: Harness) -> str:
    """Return a path-independent digest of one already-fixed source view."""

    return _source_snapshot(harness)[0]


def open_derived_source(
    source_root: Path | str,
    destination_root: Path | str,
    formal_seq: int,
) -> DerivedBridgeSource:
    """Validate roots and open exactly one historical source sequence."""

    if isinstance(formal_seq, bool) or not isinstance(formal_seq, int) or formal_seq < 0:
        raise DerivedBridgeError("BRIDGE_DERIVED_SEQ_INVALID")
    source, destination = _validate_roots(source_root, destination_root)
    historical = Harness.at(source, formal_seq)
    if historical._next_seq - 1 != formal_seq:
        raise DerivedBridgeError("BRIDGE_DERIVED_SEQ_OUT_OF_RANGE")
    if any(vars(historical.scratch_state).values()):
        raise DerivedBridgeError("BRIDGE_DERIVED_SCRATCH_CONTEXT_UNAVAILABLE")
    source_run_digest, sealed_blob_refs = _source_snapshot(historical)
    return DerivedBridgeSource(
        harness=historical,
        source_run_digest=source_run_digest,
        formal_seq=formal_seq,
        destination_root=destination,
        sealed_blob_refs=sealed_blob_refs,
    )


def reserve_derived_destination(source: DerivedBridgeSource) -> Path:
    """Atomically reserve the validated new destination leaf."""

    validated_source, validated_destination = _validate_roots(
        source.harness.root, source.destination_root
    )
    current_digest, current_sealed_refs = _source_snapshot(source.harness)
    if (
        validated_source != source.harness.root.resolve()
        or validated_destination != source.destination_root
        or not source.harness._read_only
        or source.formal_seq != source.harness._next_seq - 1
        or source.source_run_digest != current_digest
        or source.sealed_blob_refs != current_sealed_refs
    ):
        raise DerivedBridgeError("BRIDGE_DERIVED_SOURCE_MISMATCH")
    try:
        source.destination_root.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_DESTINATION_EXISTS") from error
    except OSError as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_DESTINATION_CREATE_FAILED") from error
    return source.destination_root


def build_derived_bridge(
    source: DerivedBridgeSource,
    destination_harness: Harness,
    problem_id: str,
    target: str,
    policy,
    **kwargs,
):
    """Run the canonical bridge workflow with independent source/sink logs."""

    source_root = source.harness.root.resolve()
    destination_root = destination_harness.root.resolve()
    if (
        destination_root != source.destination_root
        or source_root == destination_root
        or source_root.is_relative_to(destination_root)
        or destination_root.is_relative_to(source_root)
    ):
        raise DerivedBridgeError("BRIDGE_DERIVED_DESTINATION_MISMATCH")
    if destination_harness._next_seq != 0:
        raise DerivedBridgeError("BRIDGE_DERIVED_DESTINATION_NOT_NEW")
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    try:
        manifest = load_run_manifest(destination_harness.root / MANIFEST_NAME)
    except (OSError, RuntimeError, ValueError) as error:
        raise DerivedBridgeError("BRIDGE_DERIVED_MANIFEST_INVALID") from error
    if (
        manifest.schema_version != 3
        or manifest.workload_profile != "text"
        or manifest.bridge_policy is None
        or manifest.bridge_policy.mode != "grounded_two_stage"
    ):
        raise DerivedBridgeError("BRIDGE_DERIVED_MANIFEST_V3_REQUIRED")
    if kwargs.get("run_manifest_digest") != manifest.sha256:
        raise DerivedBridgeError("BRIDGE_DERIVED_MANIFEST_MISMATCH")
    attention_pack = kwargs.pop("attention_pack", None)
    if attention_pack is not None:
        raise DerivedBridgeError("BRIDGE_DERIVED_SCRATCH_CONTEXT_UNAVAILABLE")
    return destination_harness.build_bridge(
        problem_id,
        target,
        policy,
        source_harness=source.harness,
        source_run_digest=source.source_run_digest,
        source_sealed_blob_refs=source.sealed_blob_refs,
        attention_pack=None,
        **kwargs,
    )


__all__ = [
    "DerivedBridgeError",
    "DerivedBridgeSource",
    "build_derived_bridge",
    "open_derived_source",
    "reserve_derived_destination",
    "source_snapshot_digest",
]
