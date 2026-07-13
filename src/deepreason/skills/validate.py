"""Verification boundary for accepted-only skill distillation."""

from __future__ import annotations

import json
from pathlib import Path

from deepreason import programs
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.harness import Harness
from deepreason.ontology import Status
from deepreason.ontology.artifact import RefRole
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
from deepreason.skills.models import (
    DependencyLink,
    PackageCoordinate,
    PassedCommitmentDefinition,
    ToolchainCoordinate,
    VerifiedDistillationSource,
)


class DistillationSourceError(ValueError):
    """The requested source is absent, not accepted, or not fully pinned."""


def _content_bytes(harness: Harness, artifact) -> bytes:
    if artifact.content_ref.startswith("inline:"):
        return artifact.content_ref.removeprefix("inline:").encode()
    try:
        return harness.blobs.get(artifact.content_ref)
    except KeyError as error:
        raise DistillationSourceError(
            f"source artifact blob is missing: {artifact.content_ref}"
        ) from error


def _positive_dependency_closure(harness: Harness, artifact_id: str) -> tuple[str, ...]:
    pending = [artifact_id]
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        artifact = harness.state.artifacts.get(current)
        if artifact is None:
            raise DistillationSourceError(f"dependency is absent at source sequence: {current}")
        if harness.state.status.get(current) != Status.ACCEPTED:
            raise DistillationSourceError(
                f"distillation closure contains a non-accepted artifact: {current}"
            )
        seen.add(current)
        pending.extend(
            ref.target
            for ref in artifact.interface.refs
            if ref.role == RefRole.DEPENDENCE
        )
    return tuple(sorted(seen))


def _toolchains(root: Path) -> tuple[ToolchainCoordinate, ...]:
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.exists():
        return ()
    manifest = load_run_manifest(manifest_path)
    return tuple(
        ToolchainCoordinate(
            id=item.id,
            executable=item.executable,
            version_output_sha256=item.version_output_sha256,
            lock_digest=item.lock_digest,
        )
        for item in manifest.toolchains
    )


def _config_provenance(root: Path) -> tuple[str, ...]:
    manifest_path = root / MANIFEST_NAME
    if not manifest_path.exists():
        return ("run-manifest:none",)
    manifest = load_run_manifest(manifest_path)
    values = [f"run-manifest:{sha256_hex(manifest_path.read_bytes())}"]
    if manifest.source_config_hash:
        values.append(f"source-config:{manifest.source_config_hash}")
    return tuple(values)


def _packages(harness: Harness, artifacts: tuple[str, ...]) -> tuple[PackageCoordinate, ...]:
    coordinates: dict[tuple[str, str, str], PackageCoordinate] = {}
    for artifact_id in artifacts:
        artifact = harness.state.artifacts[artifact_id]
        if artifact.codec != "json":
            continue
        try:
            payload = json.loads(_content_bytes(harness, artifact))
        except (TypeError, ValueError):
            continue
        if not isinstance(payload, dict) or payload.get("schema") != "resolved-import-v1":
            continue
        archives = {
            item.get("package"): item
            for item in payload.get("packages", ())
            if isinstance(item, dict)
        }
        for item in payload.get("resolved", ()):
            if not isinstance(item, dict):
                continue
            package = item.get("package")
            version = item.get("version")
            integrity = item.get("integrity")
            if not all(isinstance(value, str) and value for value in (package, version, integrity)):
                continue
            archive = archives.get(package, {})
            coordinate = PackageCoordinate(
                package=package,
                version=version,
                integrity=integrity,
                archive_id=archive.get("archive_id"),
            )
            coordinates[(package, version, integrity)] = coordinate
    return tuple(coordinates[key] for key in sorted(coordinates))


def validate_distillation_source(
    source_root: Path | str,
    *,
    source_event_seq: int,
    accepted_artifact_id: str,
    distiller_version: str,
) -> VerifiedDistillationSource:
    """Pin the exact positive closure of an accepted artifact at ``seq``.

    The time-travel materialization is essential: checking the live head would
    let later criticism silently change which historical source was distilled.
    Refuted and suspended roots fail closed.  Only accepted dependence sources
    and currently passing deterministic commitment definitions enter the
    capsule material; critics and failed rivals are never traversed.
    """

    root = Path(source_root).resolve()
    if not root.is_dir():
        raise DistillationSourceError(f"source root does not exist: {root}")
    all_events = list(Harness(root, read_only=True).log.read())
    if not any(event.seq == source_event_seq for event in all_events):
        raise DistillationSourceError(f"source event sequence does not exist: {source_event_seq}")
    source = Harness.at(root, source_event_seq)
    artifact = source.state.artifacts.get(accepted_artifact_id)
    if artifact is None:
        raise DistillationSourceError(
            f"artifact is absent at source sequence: {accepted_artifact_id}"
        )
    if source.state.status.get(accepted_artifact_id) != Status.ACCEPTED:
        raise DistillationSourceError(
            f"distillation source is not accepted at sequence {source_event_seq}"
        )

    artifacts = _positive_dependency_closure(source, accepted_artifact_id)
    links = tuple(
        sorted(
            (
                DependencyLink(dependent=current, dependency=ref.target)
                for current in artifacts
                for ref in source.state.artifacts[current].interface.refs
                if ref.role == RefRole.DEPENDENCE and ref.target in artifacts
            ),
            key=lambda item: (item.dependent, item.dependency),
        )
    )
    commitment_ids = tuple(
        sorted(
            {
                commitment_id
                for current in artifacts
                for commitment_id in source.state.artifacts[current].interface.commitments
            }
        )
    )
    passed: list[PassedCommitmentDefinition] = []
    for commitment_id in commitment_ids:
        commitment = source.commitments.get(commitment_id)
        if commitment is None:
            raise DistillationSourceError(f"source commitment object is absent: {commitment_id}")
        if commitment_id not in artifact.interface.commitments:
            continue
        try:
            verdict, _trace = programs.evaluate(commitment, artifact, source.blobs)
        except programs.NotEvaluable:
            continue
        if verdict == programs.PASS:
            closure_ref = commitment.budget.extra.get("source_artifact")
            closure = (str(closure_ref),) if closure_ref else ()
            if closure and closure[0] not in artifacts:
                # A reusable proposed checker must remain attackable.  Do not
                # advertise a commitment whose defining artifact was not in
                # the positive source closure captured above.
                continue
            passed.append(
                PassedCommitmentDefinition(definition=commitment, closure_refs=closure)
            )

    blob_refs = tuple(
        sorted(
            {
                item.content_ref
                for current in artifacts
                if not (item := source.state.artifacts[current]).content_ref.startswith("inline:")
            }
        )
    )
    object_refs = tuple(sorted({*artifacts, *commitment_ids}))
    toolchains = _toolchains(root)
    packages = _packages(source, artifacts)
    config_provenance = _config_provenance(root)
    snapshot_payload = {
        "source_event_seq": source_event_seq,
        "accepted_artifact_id": accepted_artifact_id,
        "artifacts": [
            source.state.artifacts[item].model_dump(mode="json", by_alias=True)
            for item in artifacts
        ],
        "commitments": [
            source.commitments[item].model_dump(mode="json", by_alias=True)
            for item in commitment_ids
        ],
        "blobs": [
            {"ref": item, "digest": sha256_hex(source.blobs.get(item))}
            for item in blob_refs
        ],
        "toolchains": [item.model_dump(mode="json") for item in toolchains],
        "packages": [item.model_dump(mode="json") for item in packages],
        "source_config_provenance": config_provenance,
    }
    content = _content_bytes(source, artifact)
    return VerifiedDistillationSource(
        source_root=str(root),
        source_event_seq=source_event_seq,
        accepted_artifact_id=accepted_artifact_id,
        source_content_ref=artifact.content_ref,
        source_codec=artifact.codec,
        source_content_digest=sha256_hex(content),
        object_closure=object_refs,
        blob_closure=blob_refs,
        dependency_topology=links,
        passed_commitments=tuple(passed),
        toolchains=toolchains,
        packages=packages,
        source_config_provenance=config_provenance,
        distiller_version=distiller_version,
        source_snapshot_digest=sha256_hex(canonical_json(snapshot_payload)),
    )
