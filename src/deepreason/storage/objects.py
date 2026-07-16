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

from deepreason.bridge.evidence_pack import EvidencePackV1
from deepreason.bridge.ledger import ClaimLedgerInputCatalogV1
from deepreason.bridge.models import (
    BridgeFailureV1,
    BridgeOutputV1,
    BridgeValidationFindingV1,
    BridgeValidationReportV1,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ClaimUseV1,
    GroundingFindingV1,
    GroundingReviewV1,
    SourceConflictV1,
    UncoveredRequirementV1,
    UnresolvedItemV1,
)
from deepreason.bridge.retry import BridgeWorkflowRetryV1
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology.artifact import Artifact
from deepreason.ontology.commitment import Commitment
from deepreason.ontology.problem import Problem
from deepreason.ontology.warrant import Warrant
from deepreason.scratch.models import (
    AdvisoryContextV1,
    AttentionReceiptV1,
    ClusterGuideV1,
    ClusterMembershipV1,
    ClusterSnapshotV1,
    CoverageCycleV1,
    ScratchBlockV1,
    ScratchClusterV1,
    ScratchLinkV1,
    SimilarityHitV1,
    VisibilityRecordV1,
)
from deepreason.workflow.models import (
    GuardResultV1,
    ProposalReceiptV1,
    RepairWorkOrderV1,
    StopMetricsObservationV1,
    TransitionDecisionV1,
    WorkOrderEnvelopeV1,
    WorkflowLifecycleDecisionV1,
    WorkflowLifecycleSnapshotV1,
    WorkflowResumeDecisionV1,
)

SCHEMAS: dict[str, type[BaseModel]] = {
    "artifact": Artifact,
    "commitment": Commitment,
    "warrant": Warrant,
    "problem": Problem,
    "scratch-block": ScratchBlockV1,
    "scratch-link": ScratchLinkV1,
    "scratch-cluster": ScratchClusterV1,
    "scratch-membership": ClusterMembershipV1,
    "scratch-cluster-snapshot": ClusterSnapshotV1,
    "scratch-guide": ClusterGuideV1,
    "scratch-similarity": SimilarityHitV1,
    "scratch-attention-receipt": AttentionReceiptV1,
    "scratch-visibility": VisibilityRecordV1,
    "scratch-coverage-cycle": CoverageCycleV1,
    "scratch-advisory-context": AdvisoryContextV1,
    "bridge-ledger-entry": ClaimLedgerEntryV1,
    "bridge-uncovered-requirement": UncoveredRequirementV1,
    "bridge-source-conflict": SourceConflictV1,
    "bridge-claim-ledger": ClaimLedgerV1,
    "bridge-claim-use": ClaimUseV1,
    "bridge-unresolved-item": UnresolvedItemV1,
    "bridge-output": BridgeOutputV1,
    "bridge-validation-finding": BridgeValidationFindingV1,
    "bridge-validation-report": BridgeValidationReportV1,
    "bridge-grounding-finding": GroundingFindingV1,
    "bridge-grounding-review": GroundingReviewV1,
    "bridge-ledger-input-catalog": ClaimLedgerInputCatalogV1,
    "bridge-evidence-pack": EvidencePackV1,
    "bridge-failure": BridgeFailureV1,
    "bridge-workflow-retry": BridgeWorkflowRetryV1,
    "workflow-work-order": WorkOrderEnvelopeV1,
    "workflow-repair-work-order": RepairWorkOrderV1,
    "workflow-proposal-receipt": ProposalReceiptV1,
    "workflow-guard-result": GuardResultV1,
    "workflow-transition-decision": TransitionDecisionV1,
    "workflow-stop-metrics-observation": StopMetricsObservationV1,
    "workflow-lifecycle-snapshot": WorkflowLifecycleSnapshotV1,
    "workflow-lifecycle-decision": WorkflowLifecycleDecisionV1,
    "workflow-resume-decision": WorkflowResumeDecisionV1,
}

# Most canonical records expose ``id``. A few scratch records retain the
# domain-specific identity names from the scratch ontology. The outer object
# record still uses one globally unique ``id`` field, so legacy readers and
# cross-schema collision checks remain unchanged.
_SCHEMA_ID_FIELDS: dict[str, str] = {
    "scratch-cluster-snapshot": "snapshot_hash",
    "scratch-attention-receipt": "receipt_hash",
    "scratch-coverage-cycle": "cycle_id",
}


def _object_id(schema: str, obj: BaseModel) -> str:
    field = _SCHEMA_ID_FIELDS.get(schema, "id")
    try:
        oid = getattr(obj, field)
    except AttributeError as error:
        raise ValueError(f"object schema {schema!r} has no identity field {field!r}") from error
    if not isinstance(oid, str) or not oid:
        raise ValueError(f"object schema {schema!r} has an invalid identity field {field!r}")
    return oid


def _object_data(schema: str, obj: BaseModel) -> dict:
    """Serialize canonical data without changing historical formal bytes."""

    return obj.model_dump(
        mode="json",
        by_alias=True,
        # Advisory canonical encodings omit absent optional fields. Formal
        # schemas retain their exact established byte representation.
        exclude_none=schema.startswith(("scratch-", "bridge-", "workflow-")),
    )


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
            "id": _object_id(schema, normalized),
            "data": _object_data(schema, normalized),
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
        if _object_id(schema, obj) != oid or (expected_id is not None and oid != expected_id):
            raise ValueError(f"object id mismatch in {path}")
        canonical = {
            "schema": schema,
            "id": oid,
            "data": _object_data(schema, obj),
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

        found: list[tuple[str, BaseModel, dict]] = []
        for name in SCHEMAS:
            path = self._schema_path(name, oid)
            if path.exists():
                found.append(self._read_record(path, expected_id=oid))
        if len(found) > 1:
            raise ObjectConflictError(f"object id {oid!r} exists in multiple schemas")

        legacy = self._path(oid)
        if legacy.exists():
            try:
                legacy_schema, legacy_obj, legacy_record = self._read_record(
                    legacy, expected_id=oid
                )
            except ValueError:
                # Preserve the established torn-legacy healing behavior: once
                # a valid namespaced record exists, an older corrupt flat slot
                # is non-authoritative and remains untouched.
                if found:
                    found_schema, found_obj, _ = found[0]
                    return found_schema, found_obj
                raise
            if found:
                found_schema, found_obj, found_record = found[0]
                if (
                    legacy_schema != found_schema
                    or canonical_json(legacy_record) != canonical_json(found_record)
                ):
                    raise ObjectConflictError(
                        f"object id {oid!r} conflicts with legacy {legacy_schema} record"
                    )
                return found_schema, found_obj
            return legacy_schema, legacy_obj
        if found:
            found_schema, found_obj, _ = found[0]
            return found_schema, found_obj
        raise KeyError(f"object not found: {oid}")
