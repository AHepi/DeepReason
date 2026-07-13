"""Immutable records for the optional, local external-memory substrate.

Brain records are process metadata.  They are deliberately separate from the
ontology: neither a memory form nor a retrieval score can create evidence,
dependencies, warrants, or status.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepreason.canonical import canonical_json, sha256_hex

MemoryForm = Literal["source", "episode", "lesson", "skill", "proof", "simulation", "note"]
MemoryOrigin = Literal["file", "run", "user", "import"]
MemoryRefRole = Literal["related", "derived", "supersedes", "source"]
BrainEventType = Literal[
    "Init",
    "Ingest",
    "Distill",
    "Link",
    "Reinforce",
    "Access",
    "Pin",
    "Unpin",
    "Supersede",
    "Index",
    "Card",
]


class BrainModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        serialize_by_alias=True,
    )


class MemoryRef(BrainModel):
    target: str
    role: MemoryRefRole = "related"


class MemoryProvenance(BrainModel):
    origin: MemoryOrigin
    source_ref: str
    source_digest: str | None = None
    created_seq: int = Field(ge=0)
    created_day: date


class ActivationSpec(BrainModel):
    base_strength: float = Field(default=1.0, ge=0.0)
    half_life_days: float = Field(default=90.0, gt=0.0)
    pin_floor: float = Field(default=0.0, ge=0.0)


def memory_identity(fields: dict[str, Any]) -> str:
    """Return the content address of a memory, excluding its asserted id."""

    identity = dict(fields)
    identity.pop("id", None)
    return sha256_hex(canonical_json(identity))


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


class MemoryRecord(BrainModel):
    schema_: Literal["deepreason-memory-v1"] = Field(
        default="deepreason-memory-v1", alias="schema"
    )
    id: str
    form: MemoryForm
    title: str = Field(min_length=1, max_length=500)
    content_ref: str
    codec: str = Field(min_length=1)
    summary_ref: str | None = None
    facets: tuple[str, ...] = Field(default=(), max_length=128)
    entities: tuple[str, ...] = Field(default=(), max_length=128)
    refs: tuple[MemoryRef, ...] = Field(default=(), max_length=128)
    provenance: MemoryProvenance
    activation: ActivationSpec = ActivationSpec()

    @model_validator(mode="after")
    def _content_addressed(self) -> MemoryRecord:
        expected = memory_identity(self.model_dump(mode="json"))
        if self.id != expected:
            raise ValueError(f"memory id mismatch: expected {expected}")
        return self

    @classmethod
    def create(cls, **fields: Any) -> MemoryRecord:
        payload = _jsonable({"schema": "deepreason-memory-v1", **fields})
        payload["id"] = memory_identity(payload)
        return cls.model_validate(payload)


class LessonRecord(BrainModel):
    schema_: Literal["deepreason-lesson-v1"] = Field(
        default="deepreason-lesson-v1", alias="schema"
    )
    claim: str = Field(min_length=1)
    conditions: tuple[str, ...] = Field(default=(), max_length=128)
    procedure: tuple[str, ...] = Field(default=(), max_length=128)
    checks: tuple[str, ...] = Field(default=(), max_length=128)
    limits: tuple[str, ...] = Field(default=(), max_length=128)
    overturn_conditions: tuple[str, ...] = Field(default=(), max_length=128)
    source_refs: tuple[str, ...] = Field(default=(), max_length=128)


class BrainManifest(BrainModel):
    schema_: Literal["deepreason-brain-v1"] = Field(
        default="deepreason-brain-v1", alias="schema"
    )
    brain_id: str
    head_seq: int = Field(ge=0)
    root_digest: str
    card_version: str = "v1"
    index_version: str = "hybrid-v1"
    created_at: datetime


class BrainEvent(BrainModel):
    schema_: Literal["deepreason-brain-event-v1"] = Field(
        default="deepreason-brain-event-v1", alias="schema"
    )
    seq: int = Field(ge=0)
    type: BrainEventType
    day: date
    logical_seq: int | None = Field(default=None, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)
    prev_digest: str | None = None
    digest: str

    @model_validator(mode="after")
    def _digest_valid(self) -> BrainEvent:
        data = self.model_dump(mode="json")
        asserted = data.pop("digest")
        expected = sha256_hex(canonical_json(data))
        if asserted != expected:
            raise ValueError(f"brain event digest mismatch at seq {self.seq}")
        return self

    @classmethod
    def create(
        cls,
        *,
        seq: int,
        type: BrainEventType,
        day: date,
        payload: dict[str, Any] | None = None,
        prev_digest: str | None,
        logical_seq: int | None = None,
    ) -> BrainEvent:
        data: dict[str, Any] = {
            "schema": "deepreason-brain-event-v1",
            "seq": seq,
            "type": type,
            "day": day.isoformat(),
            "logical_seq": logical_seq,
            "payload": payload or {},
            "prev_digest": prev_digest,
        }
        data["digest"] = sha256_hex(canonical_json(data))
        return cls.model_validate(data)


class MemoryCard(BrainModel):
    schema_: Literal["deepreason-memory-card-v1"] = Field(
        default="deepreason-memory-card-v1", alias="schema"
    )
    record_id: str
    title: str
    summary: str
    facets: tuple[str, ...] = Field(default=(), max_length=128)
    entities: tuple[str, ...] = Field(default=(), max_length=128)
    conditions: tuple[str, ...] = Field(default=(), max_length=128)
    overturn_conditions: tuple[str, ...] = Field(default=(), max_length=128)
    related: tuple[str, ...] = Field(default=(), max_length=128)
    content_digest: str


class TopicCard(BrainModel):
    schema_: Literal["deepreason-topic-card-v1"] = Field(
        default="deepreason-topic-card-v1", alias="schema"
    )
    topic: str
    record_count: int = Field(ge=0)
    record_ids: tuple[str, ...] = Field(max_length=64)
    truncated: bool = False


class MemoryPolicy(BrainModel):
    """Fixed, declared retrieval policy; no field learns from outcomes."""

    lexical_weight_ppm: int = Field(default=400_000, ge=0)
    vector_weight_ppm: int = Field(default=200_000, ge=0)
    graph_weight_ppm: int = Field(default=100_000, ge=0)
    strength_weight_ppm: int = Field(default=200_000, ge=0)
    novelty_weight_ppm: int = Field(default=100_000, ge=0)
    candidate_pool_limit: int = Field(default=256, ge=1, le=4096)
    posting_read_limit: int = Field(default=512, ge=1, le=8192)
    selected_limit: int = Field(default=12, ge=1, le=256)
    expanded_limit: int = Field(default=4, ge=0, le=64)
    body_byte_limit: int = Field(default=32_768, ge=0, le=4_194_304)
    graph_seed_limit: int = Field(default=32, ge=0, le=512)
    collection_quota: int = Field(default=4, ge=1, le=256)
    exploration_ppm: int = Field(default=200_000, ge=0, le=1_000_000)
    strength_cap: float = Field(default=4.0, gt=0.0)
    automatic_access_per_day: int = Field(default=1, ge=0, le=32)
    reinforcement_event_limit: int = Field(default=128, ge=1, le=4096)

    @model_validator(mode="after")
    def _weights_sum(self) -> MemoryPolicy:
        total = (
            self.lexical_weight_ppm
            + self.vector_weight_ppm
            + self.graph_weight_ppm
            + self.strength_weight_ppm
            + self.novelty_weight_ppm
        )
        if total != 1_000_000:
            raise ValueError("memory score weights must sum to 1,000,000 ppm")
        return self

    @property
    def digest(self) -> str:
        return sha256_hex(canonical_json(self.model_dump(mode="json")))


class CandidateScore(BrainModel):
    id: str
    lexical_ppm: int = Field(ge=0, le=1_000_000)
    vector_ppm: int = Field(ge=0, le=1_000_000)
    graph_ppm: int = Field(ge=0, le=1_000_000)
    strength_ppm: int = Field(ge=0, le=1_000_000)
    score_ppm: int = Field(ge=0)


class RetrievalReceipt(BrainModel):
    schema_: Literal["deepreason-brain-retrieval-v1"] = Field(
        default="deepreason-brain-retrieval-v1", alias="schema"
    )
    brain_id: str
    root_digest: str
    index_version: str
    card_version: str
    query: str
    query_day: str
    policy_digest: str
    candidate_pool: tuple[CandidateScore, ...]
    selected: tuple[str, ...]
    expanded: tuple[str, ...]
    merkle_proofs_ref: str
    receipt_digest: str

    @model_validator(mode="after")
    def _receipt_digest_valid(self) -> RetrievalReceipt:
        data = self.model_dump(mode="json")
        asserted = data.pop("receipt_digest")
        expected = sha256_hex(canonical_json(data))
        if asserted != expected:
            raise ValueError("retrieval receipt digest mismatch")
        return self

    @classmethod
    def create(cls, **fields: Any) -> RetrievalReceipt:
        payload = _jsonable({"schema": "deepreason-brain-retrieval-v1", **fields})
        payload["receipt_digest"] = sha256_hex(canonical_json(payload))
        return cls.model_validate(payload)


class RetrievalResult(BrainModel):
    receipt: RetrievalReceipt
    cards: tuple[MemoryCard, ...]
    bodies: dict[str, bytes]
    activation: dict[str, float]


class RunLocalBrainSnapshot(BrainModel):
    schema_: Literal["deepreason-brain-snapshot-v1"] = Field(
        default="deepreason-brain-snapshot-v1", alias="schema"
    )
    receipt_ref: str
    proof_ref: str
    card_refs: dict[str, str]
    record_refs: dict[str, str]
    body_refs: dict[str, str]
    referenced_blob_refs: tuple[str, ...] = ()


def utc_day() -> date:
    return datetime.now(timezone.utc).date()
