"""Process records for cross-run skills.

Skills are pinned prior material, never ontology types and never warrants.  The
records in this module describe verified distillation inputs, immutable library
snapshots, retrieval receipts, and explicit current-run test adoption.  None of
them participates in ``att``, ``dep``, or status computation.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology import Commitment


_FROZEN = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ToolchainCoordinate(BaseModel):
    """Exact source-side coordinates, retained as provenance only."""

    model_config = _FROZEN

    id: str = Field(min_length=1)
    executable: str = Field(min_length=1)
    version_output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    lock_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class PackageCoordinate(BaseModel):
    """An exact resolved package coordinate; never a floating request."""

    model_config = _FROZEN

    package: str = Field(min_length=1)
    version: str = Field(min_length=1)
    integrity: str = Field(min_length=1)
    archive_id: str | None = None


class PassedCommitmentDefinition(BaseModel):
    """An exact reusable test definition, not its old verdict."""

    model_config = _FROZEN

    definition: Commitment
    closure_refs: tuple[str, ...] = ()

    @property
    def id(self) -> str:
        return self.definition.id


class DependencyLink(BaseModel):
    model_config = _FROZEN

    dependent: str = Field(min_length=1)
    dependency: str = Field(min_length=1)


class VerifiedDistillationSource(BaseModel):
    """A time-travel-verified accepted source and the bytes inspected.

    ``source_root`` is an audit locator.  Identity is supplied by the snapshot
    digest and content-addressed closure, so moving the source run does not
    change a distilled capsule.
    """

    model_config = _FROZEN

    schema_: Literal["deepreason-verified-distillation-source-v1"] = Field(
        default="deepreason-verified-distillation-source-v1", alias="schema"
    )
    source_root: str = Field(min_length=1)
    source_event_seq: int = Field(ge=0)
    accepted_artifact_id: str = Field(min_length=1)
    source_content_ref: str = Field(min_length=1)
    source_codec: str = Field(min_length=1)
    source_content_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    object_closure: tuple[str, ...] = Field(min_length=1)
    blob_closure: tuple[str, ...] = ()
    dependency_topology: tuple[DependencyLink, ...] = ()
    passed_commitments: tuple[PassedCommitmentDefinition, ...] = ()
    toolchains: tuple[ToolchainCoordinate, ...] = ()
    packages: tuple[PackageCoordinate, ...] = ()
    source_config_provenance: tuple[str, ...] = ()
    distiller_version: str = Field(min_length=1)
    source_snapshot_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class CapsuleDraft(BaseModel):
    """Positive, source-side material emitted by a distiller."""

    model_config = _FROZEN

    problem_signature: str = Field(min_length=1, max_length=4_000)
    accepted_source_structure: tuple[str, ...] = Field(min_length=1, max_length=128)
    scope: tuple[str, ...] = Field(default=(), max_length=64)
    source_owned_counterconditions: tuple[str, ...] = Field(default=(), max_length=64)
    unresolved_conditions: tuple[str, ...] = Field(default=(), max_length=64)
    overturn_conditions: tuple[str, ...] = Field(min_length=1, max_length=64)


class SkillCapsule(BaseModel):
    """Positive source material with no imported acceptance authority."""

    model_config = _FROZEN

    schema_: Literal["deepreason-skill-capsule-v1"] = Field(
        default="deepreason-skill-capsule-v1", alias="schema"
    )
    id: str = Field(pattern=r"^[0-9a-f]{64}$")
    problem_signature: str = Field(min_length=1, max_length=4_000)
    accepted_source_structure: tuple[str, ...] = Field(min_length=1, max_length=128)
    scope: tuple[str, ...] = Field(default=(), max_length=64)
    source_owned_counterconditions: tuple[str, ...] = Field(default=(), max_length=64)
    passed_commitments: tuple[PassedCommitmentDefinition, ...] = ()
    toolchains: tuple[ToolchainCoordinate, ...] = ()
    packages: tuple[PackageCoordinate, ...] = ()
    dependency_topology: tuple[DependencyLink, ...] = ()
    unresolved_conditions: tuple[str, ...] = Field(default=(), max_length=64)
    overturn_conditions: tuple[str, ...] = Field(min_length=1, max_length=64)
    source_artifact_id: str = Field(min_length=1)
    source_event_seq: int = Field(ge=0)
    source_snapshot_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_config_provenance: tuple[str, ...] = ()
    distiller_version: str = Field(min_length=1)

    def identity_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude={"id"})

    @model_validator(mode="after")
    def _content_addressed_id(self):
        expected = sha256_hex(canonical_json(self.identity_payload()))
        if self.id != expected:
            raise ValueError("skill capsule id does not match canonical content")
        return self

    @classmethod
    def create(cls, **values: Any) -> "SkillCapsule":
        provisional = cls.model_construct(
            schema_="deepreason-skill-capsule-v1", id="0" * 64, **values
        )
        payload = provisional.identity_payload()
        payload["id"] = sha256_hex(canonical_json(payload))
        return cls.model_validate(payload)


class LessonMemory(BaseModel):
    model_config = _FROZEN

    schema_: Literal["deepreason-lesson-v1"] = Field(
        default="deepreason-lesson-v1", alias="schema"
    )
    claim: str = Field(min_length=1, max_length=4_000)
    conditions: tuple[str, ...] = Field(min_length=1, max_length=64)
    procedure: tuple[str, ...] = Field(min_length=1, max_length=64)
    checks: tuple[str, ...] = Field(default=(), max_length=64)
    limits: tuple[str, ...] = Field(default=(), max_length=64)
    overturn_conditions: tuple[str, ...] = Field(min_length=1, max_length=64)
    source_refs: tuple[str, ...] = Field(min_length=1, max_length=64)


class SkillCatalogEntry(BaseModel):
    model_config = _FROZEN

    capsule_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_ref: str = Field(pattern=r"^[0-9a-f]{64}$")
    byte_length: int = Field(ge=1)
    problem_signature: str = Field(min_length=1)


class SkillLibrarySnapshot(BaseModel):
    model_config = _FROZEN

    schema_: Literal["deepreason-skill-library-snapshot-v1"] = Field(
        default="deepreason-skill-library-snapshot-v1", alias="schema"
    )
    library_id: str = Field(min_length=1)
    catalog: tuple[SkillCatalogEntry, ...]
    catalog_ref: str = Field(pattern=r"^[0-9a-f]{64}$")
    snapshot_digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _catalog_is_canonical(self):
        ids = [item.capsule_id for item in self.catalog]
        if ids != sorted(set(ids)):
            raise ValueError("skill snapshot catalog must have unique sorted ids")
        if self.snapshot_digest != self.catalog_ref:
            raise ValueError("skill snapshot digest must pin the catalog bytes")
        return self


class RawEmbedding(BaseModel):
    model_config = _FROZEN

    item_id: str = Field(min_length=1)
    vector: tuple[float, ...]


class RankedSkill(BaseModel):
    model_config = _FROZEN

    capsule_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    score_ppm: int = Field(ge=-1_000_000, le=1_000_000)
    rank: int = Field(ge=1)


class SchoolSkillSlice(BaseModel):
    model_config = _FROZEN

    school_id: str = Field(min_length=1)
    blind: bool = False
    capsule_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _blind_has_no_capsules(self):
        if self.blind and self.capsule_ids:
            raise ValueError("a skill-blind school cannot receive capsules")
        return self


class RevoicedSkill(BaseModel):
    model_config = _FROZEN

    capsule_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    summary_ref: str = Field(pattern=r"^[0-9a-f]{64}$")
    summary_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    overlap_ppm: int = Field(ge=0, le=1_000_000)
    longest_overlap_words: int = Field(ge=0)
    summarizer_version: str = Field(min_length=1)


class SkillRetrievalReceipt(BaseModel):
    model_config = _FROZEN

    schema_: Literal["deepreason-skill-retrieval-v1"] = Field(
        default="deepreason-skill-retrieval-v1", alias="schema"
    )
    snapshot_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    query: str = Field(min_length=1)
    query_ref: str = Field(pattern=r"^[0-9a-f]{64}$")
    embedder_fingerprint: tuple[str, ...]
    raw_embeddings: tuple[RawEmbedding, ...]
    ranking: tuple[RankedSkill, ...]
    school_slices: tuple[SchoolSkillSlice, ...]
    selected_bytes: tuple[SkillCatalogEntry, ...]
    summaries: tuple[RevoicedSkill, ...] = ()
    receipt_digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    def identity_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude={"receipt_digest"})

    @model_validator(mode="after")
    def _receipt_matches(self):
        expected = sha256_hex(canonical_json(self.identity_payload()))
        if self.receipt_digest != expected:
            raise ValueError("skill retrieval receipt digest does not match content")
        blind = [item for item in self.school_slices if item.blind]
        if self.school_slices and len(blind) > 1:
            raise ValueError("at most one school may be skill-blind")
        school_ids = [item.school_id for item in self.school_slices]
        if len(school_ids) != len(set(school_ids)):
            raise ValueError("skill receipt contains duplicate schools")
        ranking_ids = [item.capsule_id for item in self.ranking]
        if len(ranking_ids) != len(set(ranking_ids)):
            raise ValueError("skill receipt ranking contains duplicate capsules")
        sliced = {
            capsule_id for item in self.school_slices for capsule_id in item.capsule_ids
        }
        selected = {item.capsule_id for item in self.selected_bytes}
        if sliced != selected:
            raise ValueError("skill receipt selected bytes do not match school slices")
        if any(item.capsule_id not in selected for item in self.summaries):
            raise ValueError("skill receipt summary was not selected")
        return self

    @classmethod
    def create(cls, **values: Any) -> "SkillRetrievalReceipt":
        provisional = cls.model_construct(
            schema_="deepreason-skill-retrieval-v1",
            receipt_digest="0" * 64,
            **values,
        )
        payload = provisional.identity_payload()
        payload["receipt_digest"] = sha256_hex(canonical_json(payload))
        return cls.model_validate(payload)


class AdoptionEvaluation(BaseModel):
    model_config = _FROZEN

    commitment_id: str = Field(min_length=1)
    verdict: Literal["pass", "fail", "overrun"]
    trace_ref: str = Field(pattern=r"^[0-9a-f]{64}$")


class AdoptionResult(BaseModel):
    """Current-run evaluation only; it deliberately carries no status."""

    model_config = _FROZEN

    source_capsule_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_candidate_id: str = Field(min_length=1)
    adopted_candidate_id: str = Field(min_length=1)
    commitment_ids: tuple[str, ...] = Field(min_length=1)
    evaluations: tuple[AdoptionEvaluation, ...] = Field(min_length=1)


class SkillMetrics(BaseModel):
    """Attention/process metrics; no status or grounding fields are allowed."""

    model_config = _FROZEN

    snapshots: int = Field(ge=0)
    retrievals: int = Field(ge=0)
    ranked_capsules: int = Field(ge=0)
    selected_capsules: int = Field(ge=0)
    blind_schools: int = Field(ge=0)
    revoiced_capsules: int = Field(ge=0)
    adopted_tests: int = Field(ge=0)
    adopted_passes: int = Field(ge=0)
    adopted_failures: int = Field(ge=0)
    adopted_overruns: int = Field(ge=0)
