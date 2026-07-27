"""Canonical records for a pre-freeze evidence dossier and run input."""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar, Literal

from pydantic import ConfigDict, Field, StrictInt, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.frozen import FrozenDict, FrozenRecord
from deepreason.ontology.commitment import Budget, Commitment


_DIGEST = r"^[0-9a-f]{64}$"
_SOURCE_ID = r"^[A-Za-z][A-Za-z0-9._:-]{0,127}$"


def _canonical_digest(domain: str, payload: dict) -> str:
    return sha256_hex(domain.encode("utf-8") + b"\x00" + canonical_json(payload))


class _InputRecord(FrozenRecord):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        serialize_by_alias=True,
    )


class AttachedSourceProvenanceV1(_InputRecord):
    """Operator-claimed provenance; informative and explicitly attackable."""

    supplied_by: str = Field(min_length=1, max_length=512)
    acquisition_method: str = Field(min_length=1, max_length=512)
    note: str | None = Field(default=None, max_length=4_096)

    @field_validator("supplied_by", "acquisition_method", "note")
    @classmethod
    def _nonblank(cls, value):
        if value is not None and not value.strip():
            raise ValueError("provenance text must be nonblank")
        return value


class AttachedSourceV1(_InputRecord):
    schema_: Literal["attached-source.v1"] = Field(
        "attached-source.v1", alias="schema"
    )
    id: str = Field(pattern=_SOURCE_ID)
    title: str = Field(min_length=1, max_length=1_024)
    source_locator: str = Field(min_length=1, max_length=4_096)
    source_class: Literal[
        "primary_paper",
        "official_hardware_documentation",
        "official_implementation",
        "reproducible_benchmark",
        "disputed_measurement",
        "synthetic_assumption",
        "other",
    ]
    media_type: str = Field(min_length=1, max_length=256)
    content_ref: str = Field(pattern=_DIGEST)
    content_sha256: str = Field(pattern=_DIGEST)
    byte_count: StrictInt = Field(ge=1, le=16 * 1024 * 1024)
    retrieved_at_claim: str | None = Field(default=None, max_length=128)
    license_or_usage_note: str | None = Field(default=None, max_length=4_096)
    provenance: AttachedSourceProvenanceV1
    declared_entities: tuple[str, ...] = Field(default=(), max_length=256)
    declared_facets: tuple[str, ...] = Field(default=(), max_length=256)

    @field_validator(
        "title",
        "source_locator",
        "media_type",
        "retrieved_at_claim",
        "license_or_usage_note",
    )
    @classmethod
    def _nonblank(cls, value):
        if value is not None and not value.strip():
            raise ValueError("source text fields must be nonblank")
        return value

    @field_validator("declared_entities", "declared_facets")
    @classmethod
    def _canonical_terms(cls, value):
        cleaned = tuple(term.strip() for term in value)
        if any(not term or len(term) > 256 for term in cleaned):
            raise ValueError("declared source terms must be bounded and nonblank")
        if cleaned != tuple(sorted(set(cleaned), key=lambda term: (term.casefold(), term))):
            raise ValueError("declared source terms must be unique and canonically sorted")
        return cleaned

    @model_validator(mode="after")
    def _content_identity(self):
        # BlobStore uses the raw-content SHA-256 as its reference. Keeping both
        # fields makes the provenance contract explicit without permitting two
        # disagreeing identities.
        if self.content_ref != self.content_sha256:
            raise ValueError("attached source content reference and digest differ")
        return self


class EvidenceDossierV1(_InputRecord):
    schema_: Literal["evidence-dossier.v1"] = Field(
        "evidence-dossier.v1", alias="schema"
    )
    dossier_digest: str = Field(pattern=_DIGEST)
    problem_ref: str = Field(min_length=1, max_length=512)
    sources: tuple[AttachedSourceV1, ...] = Field(max_length=1_000)
    total_byte_count: StrictInt = Field(ge=0, le=64 * 1024 * 1024)
    creation_provenance: AttachedSourceProvenanceV1

    IDENTITY_DOMAIN: ClassVar[str] = "evidence-dossier.v1"

    @classmethod
    def create(cls, **values) -> "EvidenceDossierV1":
        payload = cls._identity_payload_from_values(values)
        return cls(dossier_digest=_canonical_digest(cls.IDENTITY_DOMAIN, payload), **values)

    @classmethod
    def _identity_payload_from_values(cls, values: dict) -> dict:
        provisional = cls.model_construct(dossier_digest="0" * 64, **values)
        return provisional.model_dump(
            mode="json", by_alias=True, exclude={"dossier_digest"}
        )

    def identity_payload(self) -> dict:
        return self.model_dump(
            mode="json", by_alias=True, exclude={"dossier_digest"}
        )

    @field_validator("sources")
    @classmethod
    def _canonical_sources(cls, value):
        ids = tuple(source.id for source in value)
        if ids != tuple(sorted(ids)) or len(ids) != len(set(ids)):
            raise ValueError("dossier sources must be ID-unique and sorted")
        return tuple(value)

    @model_validator(mode="after")
    def _identity_and_size(self):
        if self.total_byte_count != sum(source.byte_count for source in self.sources):
            raise ValueError("dossier total byte count does not match its sources")
        expected = _canonical_digest(self.IDENTITY_DOMAIN, self.identity_payload())
        if self.dossier_digest != expected:
            raise ValueError("dossier digest does not match its canonical payload")
        return self


class RunInputProblemV1(_InputRecord):
    id: str = Field(min_length=1, max_length=512)
    description: str = Field(min_length=1, max_length=262_144)
    criteria: tuple[str, ...] = Field(default=(), max_length=4_096)

    @field_validator("criteria")
    @classmethod
    def _unique_criteria(cls, value):
        if len(value) != len(set(value)) or any(not item.strip() for item in value):
            raise ValueError("run-input criteria must be unique and nonblank")
        return tuple(value)


class RunInputManifestV1(_InputRecord):
    schema_: Literal["run-input-manifest.v1"] = Field(
        "run-input-manifest.v1", alias="schema"
    )
    input_schema_version: Literal[1] = 1
    run_input_digest: str = Field(pattern=_DIGEST)
    problem: RunInputProblemV1
    evidence_dossier_digest: str = Field(pattern=_DIGEST)
    brain_snapshot_digest: str | None = Field(default=None, pattern=_DIGEST)

    IDENTITY_DOMAIN: ClassVar[str] = "run-input-manifest.v1"

    @classmethod
    def create(cls, **values) -> "RunInputManifestV1":
        provisional = cls.model_construct(run_input_digest="0" * 64, **values)
        payload = provisional.model_dump(
            mode="json", by_alias=True, exclude={"run_input_digest"}
        )
        return cls(
            run_input_digest=_canonical_digest(cls.IDENTITY_DOMAIN, payload),
            **values,
        )

    def identity_payload(self) -> dict:
        return self.model_dump(
            mode="json", by_alias=True, exclude={"run_input_digest"}
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        expected = _canonical_digest(self.IDENTITY_DOMAIN, self.identity_payload())
        if self.run_input_digest != expected:
            raise ValueError("run-input digest does not match its canonical payload")
        return self


class RunInputBudgetV1(_InputRecord):
    """Version-frozen snapshot of every field in a Commitment budget."""

    steps: StrictInt | None = 100_000
    time_ms: StrictInt | None = 2_000
    extra: Mapping[str, StrictInt | str] = Field(default_factory=FrozenDict)

    @field_validator("extra", mode="after")
    @classmethod
    def _freeze_extra(cls, value):
        return FrozenDict(dict(value))

    @classmethod
    def from_budget(cls, budget: Budget) -> "RunInputBudgetV1":
        return cls.model_validate(budget.model_dump(mode="json"))


class RunInputCommitmentV1(_InputRecord):
    """Complete immutable Commitment definition embedded by run-input v2."""

    schema_: Literal["run-input-commitment.v1"] = Field(
        "run-input-commitment.v1", alias="schema"
    )
    id: str
    eval: str
    budget: RunInputBudgetV1 = Field(default_factory=RunInputBudgetV1)
    observation_valued: bool = False

    @classmethod
    def from_commitment(cls, commitment: Commitment) -> "RunInputCommitmentV1":
        return cls(
            id=commitment.id,
            eval=commitment.eval,
            budget=RunInputBudgetV1.from_budget(commitment.budget),
            observation_valued=commitment.observation_valued,
        )



class RunInputProblemV2(_InputRecord):
    id: str = Field(min_length=1, max_length=512)
    description: str = Field(min_length=1, max_length=262_144)
    criteria: tuple[RunInputCommitmentV1, ...] = Field(
        default=(), max_length=4_096
    )

    @field_validator("criteria")
    @classmethod
    def _unique_criteria(cls, value):
        ids = tuple(item.id for item in value)
        if len(ids) != len(set(ids)):
            raise ValueError("run-input commitment IDs must be unique")
        return tuple(value)

    @classmethod
    def from_commitments(
        cls,
        *,
        id: str,
        description: str,
        criteria: tuple[Commitment, ...],
    ) -> "RunInputProblemV2":
        return cls(
            id=id,
            description=description,
            criteria=tuple(
                RunInputCommitmentV1.from_commitment(item) for item in criteria
            ),
        )


class RunInputManifestV2(_InputRecord):
    """V6-only input authority binding complete Commitment definitions."""

    schema_: Literal["run-input-manifest.v2"] = Field(
        "run-input-manifest.v2", alias="schema"
    )
    input_schema_version: Literal[2] = 2
    run_input_digest: str = Field(pattern=_DIGEST)
    problem: RunInputProblemV2
    evidence_dossier_digest: str = Field(pattern=_DIGEST)
    brain_snapshot_digest: str | None = Field(default=None, pattern=_DIGEST)

    IDENTITY_DOMAIN: ClassVar[str] = "run-input-manifest.v2"

    @classmethod
    def create(cls, **values) -> "RunInputManifestV2":
        provisional = cls.model_construct(run_input_digest="0" * 64, **values)
        payload = provisional.model_dump(
            mode="json", by_alias=True, exclude={"run_input_digest"}
        )
        return cls(
            run_input_digest=_canonical_digest(cls.IDENTITY_DOMAIN, payload),
            **values,
        )

    def identity_payload(self) -> dict:
        return self.model_dump(
            mode="json", by_alias=True, exclude={"run_input_digest"}
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        expected = _canonical_digest(self.IDENTITY_DOMAIN, self.identity_payload())
        if self.run_input_digest != expected:
            raise ValueError("run-input digest does not match its canonical payload")
        return self


RunInputManifest = RunInputManifestV1 | RunInputManifestV2



class DossierExcerptV1(_InputRecord):
    source_id: str = Field(pattern=_SOURCE_ID)
    excerpt_ref: str = Field(pattern=_DIGEST)
    excerpt_sha256: str = Field(pattern=_DIGEST)
    byte_count: StrictInt = Field(ge=1, le=262_144)

    @model_validator(mode="after")
    def _same_identity(self):
        if self.excerpt_ref != self.excerpt_sha256:
            raise ValueError("excerpt blob reference and digest differ")
        return self


class DossierPackReceiptV1(_InputRecord):
    schema_: Literal["dossier-pack-receipt.v1"] = Field(
        "dossier-pack-receipt.v1", alias="schema"
    )
    receipt_digest: str = Field(pattern=_DIGEST)
    run_input_digest: str = Field(pattern=_DIGEST)
    work_order_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    query: str = Field(min_length=1, max_length=16_384)
    candidate_source_ids: tuple[str, ...] = Field(max_length=1_000)
    selected_source_ids: tuple[str, ...] = Field(max_length=1_000)
    excerpts: tuple[DossierExcerptV1, ...] = Field(max_length=1_000)
    excluded_source_ids: tuple[str, ...] = Field(max_length=1_000)
    policy_digest: str = Field(pattern=_DIGEST)
    state_fence: str = Field(min_length=1, max_length=512)

    IDENTITY_DOMAIN: ClassVar[str] = "dossier-pack-receipt.v1"

    @classmethod
    def create(cls, **values) -> "DossierPackReceiptV1":
        provisional = cls.model_construct(receipt_digest="0" * 64, **values)
        payload = provisional.model_dump(
            mode="json", by_alias=True, exclude={"receipt_digest"}
        )
        return cls(
            receipt_digest=_canonical_digest(cls.IDENTITY_DOMAIN, payload),
            **values,
        )

    def identity_payload(self) -> dict:
        return self.model_dump(
            mode="json", by_alias=True, exclude={"receipt_digest"}
        )

    @model_validator(mode="after")
    def _canonical_identity_and_partition(self):
        candidates = tuple(self.candidate_source_ids)
        selected = tuple(self.selected_source_ids)
        excluded = tuple(self.excluded_source_ids)
        if len(candidates) != len(set(candidates)):
            raise ValueError("candidate source IDs must be unique")
        if len(selected) != len(set(selected)) or len(excluded) != len(set(excluded)):
            raise ValueError("selected and excluded source IDs must be unique")
        if set(selected) & set(excluded) or set(selected) | set(excluded) != set(candidates):
            raise ValueError("selected and excluded sources must partition candidates")
        if tuple(excerpt.source_id for excerpt in self.excerpts) != selected:
            raise ValueError("excerpt order must exactly match selected sources")
        expected = _canonical_digest(self.IDENTITY_DOMAIN, self.identity_payload())
        if self.receipt_digest != expected:
            raise ValueError("dossier pack receipt digest is not canonical")
        return self


__all__ = [
    "AttachedSourceProvenanceV1",
    "AttachedSourceV1",
    "DossierExcerptV1",
    "DossierPackReceiptV1",
    "EvidenceDossierV1",
    "RunInputBudgetV1",
    "RunInputCommitmentV1",
    "RunInputManifest",
    "RunInputManifestV1",
    "RunInputManifestV2",
    "RunInputProblemV1",
    "RunInputProblemV2",
]
