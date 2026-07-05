"""Object store (spec §14): flat content-addressed JSON files.

Stores the four ontology records (artifact, commitment, warrant, problem) by
id so the event log can reference ids only and replay can rehydrate. The
``schema`` tag is storage bookkeeping over the spec's four record schemas —
NOT an artifact type (artifacts stay untyped, §0). Files are written once
and never mutated (D8).
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


class ObjectStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, oid: str) -> Path:
        # ids may be arbitrary strings (warrant/problem ids); hash for a safe filename
        return self.root / f"{sha256_hex(oid.encode())}.json"

    def put(self, schema: str, obj: BaseModel) -> None:
        assert schema in SCHEMAS
        path = self._path(obj.id)
        if path.exists() and self._readable(path):
            return  # immutable; same id => same record
        # A torn write (crash/ENOSPC mid-write) may have left a corrupt file:
        # write a temp file and atomically replace so the record heals.
        record = {"schema": schema, "id": obj.id, "data": obj.model_dump(mode="json", by_alias=True)}
        tmp = path.with_suffix(f".tmp.{os.getpid()}")
        tmp.write_bytes(canonical_json(record))
        os.replace(tmp, path)

    @staticmethod
    def _readable(path: Path) -> bool:
        try:
            json.loads(path.read_text())
            return True
        except (ValueError, OSError):
            return False

    def get(self, oid: str) -> tuple[str, BaseModel]:
        path = self._path(oid)
        if not path.exists():
            raise KeyError(f"object not found: {oid}")
        record = json.loads(path.read_text())
        model = SCHEMAS[record["schema"]]
        return record["schema"], model.model_validate(record["data"])
