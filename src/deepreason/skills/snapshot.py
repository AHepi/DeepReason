"""Run-local snapshots of explicit external skill catalogs."""

from __future__ import annotations

from collections.abc import Iterable

from deepreason.canonical import canonical_json
from deepreason.skills.models import SkillCapsule, SkillCatalogEntry, SkillLibrarySnapshot


def capsule_bytes(capsule: SkillCapsule) -> bytes:
    return canonical_json(capsule.model_dump(mode="json", by_alias=True))


def snapshot_library(
    capsules: Iterable[SkillCapsule],
    blobs,
    *,
    library_id: str,
) -> SkillLibrarySnapshot:
    """Copy the complete explicit catalog into the current run's BlobStore.

    Retrieval accepts this snapshot rather than a path.  Consequently replay
    never re-opens the external catalog and a later library edit cannot alter
    rankings or selected prompt bytes.
    """

    by_id: dict[str, SkillCapsule] = {}
    for capsule in capsules:
        existing = by_id.get(capsule.id)
        if existing is not None and existing != capsule:
            raise ValueError(f"skill capsule id conflict: {capsule.id}")
        by_id[capsule.id] = capsule
    catalog: list[SkillCatalogEntry] = []
    for capsule_id in sorted(by_id):
        capsule = by_id[capsule_id]
        encoded = capsule_bytes(capsule)
        content_ref = blobs.put(encoded)
        catalog.append(
            SkillCatalogEntry(
                capsule_id=capsule.id,
                content_ref=content_ref,
                byte_length=len(encoded),
                problem_signature=capsule.problem_signature,
            )
        )
    catalog_payload = {
        "schema": "deepreason-skill-catalog-v1",
        "library_id": library_id,
        "catalog": [item.model_dump(mode="json") for item in catalog],
    }
    catalog_ref = blobs.put(canonical_json(catalog_payload))
    return SkillLibrarySnapshot(
        library_id=library_id,
        catalog=tuple(catalog),
        catalog_ref=catalog_ref,
        snapshot_digest=catalog_ref,
    )


def load_capsule(entry: SkillCatalogEntry, blobs) -> SkillCapsule:
    try:
        encoded = blobs.get(entry.content_ref)
    except KeyError as error:
        raise ValueError(f"snapshotted capsule bytes are missing: {entry.capsule_id}") from error
    if len(encoded) != entry.byte_length:
        raise ValueError(f"snapshotted capsule byte length changed: {entry.capsule_id}")
    capsule = SkillCapsule.model_validate_json(encoded)
    if capsule.id != entry.capsule_id:
        raise ValueError(f"snapshotted capsule id mismatch: {entry.capsule_id}")
    return capsule
