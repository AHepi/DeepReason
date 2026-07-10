"""Immutable, schema-namespaced object storage (spec §14).

New records live under ``objects/<schema>/<hash>.json``. Legacy flat records
remain readable, so old roots replay without migration. IDs are still globally
unique because events reference IDs rather than typed handles: a same-ID record
with different schema or bytes is corruption and is rejected immediately.
"""

import json
import os
from pathlib import Path

from pydantic import BaseModel

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology.artifact import Artifact
from deepreason.ontology.commitment import Commitment
from deepreason.ontology.problem import Problem
from deepreason.ontology.warrant import Warrant

SCHEMAS: dict[str, type[BaseModel]] = {
    "artifact": Artifact,
    "commitment": Commitment,
    "warrant": Warrant,
    "problem": Problem,
}


class ObjectConflictError(ValueError):
    """An object ID already names different immutable bytes or a schema."""


class ReadOnlyObjectStoreError(RuntimeError):
    """A write was attempted through a read-only view."""


class ObjectStore:
    def __init__(self, root: Path, *, read_only: bool = False) -> None:
        self.root = Path(root)
        self.read_only = read_only
        if not read_only:
            self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, oid: str) -> Path:
        """Legacy flat path, retained for old roots and diagnostics."""
        return self.root / f"{sha256_hex(oid.encode())}.json"

    def _schema_path(self, schema: str, oid: str) -> Path:
        if schema not in SCHEMAS:
            raise ValueError(f"unknown object schema: {schema}")
        return self.root / schema / f"{sha256_hex(oid.encode())}.json"

    @staticmethod
    def _record(schema: str, obj: BaseModel) -> dict:
        if schema not in SCHEMAS:
            raise ValueError(f"unknown object schema: {schema}")
        normalized = SCHEMAS[schema].model_validate(obj.model_dump(mode="json", by_alias=True))
        return {
            "schema": schema,
            "id": normalized.id,
            "data": normalized.model_dump(mode="json", by_alias=True),
        }

    @staticmethod
    def _read_record(path: Path, *, expected_id: str | None = None) -> tuple[str, BaseModel, dict]:
        try:
            record = json.loads(path.read_text())
            schema = record["schema"]
            oid = record["id"]
            model = SCHEMAS[schema]
            obj = model.model_validate(record["data"])
        except (KeyError, TypeError, ValueError, OSError) as e:
            raise ValueError(f"corrupt object record: {path}") from e
        if obj.id != oid or (expected_id is not None and oid != expected_id):
            raise ValueError(f"object id mismatch in {path}")
        canonical = {
            "schema": schema,
            "id": oid,
            "data": obj.model_dump(mode="json", by_alias=True),
        }
        return schema, obj, canonical

    def put(self, schema: str, obj: BaseModel) -> None:
        if self.read_only:
            raise ReadOnlyObjectStoreError("object store is read-only")
        expected = self._record(schema, obj)
        oid = expected["id"]
        target = self._schema_path(schema, oid)

        # A globally referenced ID may have exactly one immutable meaning.
        # Check every namespaced record plus the legacy flat slot before write.
        candidates = [self._schema_path(name, oid) for name in SCHEMAS]
        candidates.append(self._path(oid))
        target_is_valid = False
        for path in candidates:
            if not path.exists():
                continue
            try:
                existing_schema, _existing_obj, existing = self._read_record(
                    path, expected_id=oid
                )
            except ValueError:
                # A torn target can be atomically healed. Corrupt legacy/other
                # slots are not authoritative once a valid namespaced record is
                # written, and are never deleted (D8).
                continue
            if existing_schema != schema or canonical_json(existing) != canonical_json(expected):
                raise ObjectConflictError(
                    f"object id {oid!r} conflicts with existing {existing_schema} record"
                )
            if path == target:
                target_is_valid = True
        if target_is_valid:
            return

        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".tmp.{os.getpid()}")
        data = canonical_json(expected)
        with open(tmp, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, target)
        try:
            directory_fd = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass

    @staticmethod
    def _readable(path: Path) -> bool:
        try:
            ObjectStore._read_record(path)
            return True
        except ValueError:
            return False

    def get(self, oid: str, schema: str | None = None) -> tuple[str, BaseModel]:
        if schema is not None:
            self._schema_path(schema, oid)  # validate the requested schema
            found_schema, obj = self.get(oid)
            if found_schema != schema:
                raise ObjectConflictError(
                    f"object id {oid!r} is {found_schema}, expected {schema}"
                )
            return found_schema, obj

        found: list[tuple[str, BaseModel]] = []
        for name in SCHEMAS:
            path = self._schema_path(name, oid)
            if path.exists():
                found_schema, obj, _ = self._read_record(path, expected_id=oid)
                found.append((found_schema, obj))
        if len(found) > 1:
            raise ObjectConflictError(f"object id {oid!r} exists in multiple schemas")
        if found:
            return found[0]
        legacy = self._path(oid)
        if legacy.exists():
            found_schema, obj, _ = self._read_record(legacy, expected_id=oid)
            return found_schema, obj
        raise KeyError(f"object not found: {oid}")
