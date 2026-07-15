"""Strict immutable records for the non-authoritative scratchpad.

Identity is domain-separated from the formal ontology and from every other
scratch object kind.  All factories compute IDs; parsing a stored or
caller-supplied record verifies the same computation.  Text fields are inert
data: no relation phrase, guide, source reference, or scratch identifier can
express workflow, routing, predicate, or adjudication authority.
"""

from __future__ import annotations

import math
from collections.abc import Mapping as MappingABC
from enum import Enum
from typing import Annotated, Literal, Mapping

from pydantic import ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology.frozen import FrozenDict, FrozenList, FrozenRecord


HashRef = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
OpaqueRef = Annotated[str, Field(min_length=1, max_length=512)]
ShortText = Annotated[str, Field(min_length=1, max_length=16_384)]
LongText = Annotated[str, Field(min_length=1, max_length=262_144)]


def _canonical_value(value):
    if hasattr(value, "model_dump"):
        return _canonical_value(
            value.model_dump(mode="json", by_alias=True, exclude_none=True)
        )
    if isinstance(value, MappingABC):
        return {
            str(key.value if isinstance(key, Enum) else key): _canonical_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        converted = [_canonical_value(item) for item in value]
        return sorted(converted, key=canonical_json)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("canonical values cannot contain non-finite floats")
    if isinstance(value, Enum):
        return value.value
    return value


def domain_hash(domain: str, value) -> str:
    """Hash canonical bytes with the ontology's explicit NUL domain fence."""

    if not domain or "\x00" in domain:
        raise ValueError("hash domain must be a non-empty NUL-free string")
    payload = domain.encode("utf-8") + b"\x00" + canonical_json(_canonical_value(value))
    return "sha256:" + sha256_hex(payload)


def _without_none(**values) -> dict:
    return {key: _canonical_value(value) for key, value in values.items() if value is not None}


def _require_nonblank(value: str | None) -> str | None:
    if value is not None and not value.strip():
        raise ValueError("text must contain a non-whitespace character")
    return value


def _freeze_list(value):
    return None if value is None else FrozenList(value)


def _sorted_unique(values: list[str], field: str) -> FrozenList:
    expected = sorted(set(values))
    if list(values) != expected:
        raise ValueError(f"{field} must be sorted and contain no duplicates")
    return FrozenList(values)


class ScratchRecord(FrozenRecord):
    """Strict frozen base used only by scratch canonical records."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)


class ScratchActor(str, Enum):
    USER = "user"
    LLM = "llm"
    HARNESS = "harness"


class LinkDirection(str, Enum):
    DIRECTED = "directed"
    SYMMETRIC = "symmetric"


class MembershipAction(str, Enum):
    ADD = "add"
    REMOVE = "remove"


class CoverageState(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class RetrievalChannel(str, Enum):
    FOCUS = "focus"
    LINK = "link"
    CLUSTER = "cluster"
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    RECENT = "recent"
    LOOSE = "loose"
    DORMANT = "dormant"
    UNDEREXPOSED = "underexposed"
    EXPLORATORY = "exploratory"
    COVERAGE = "coverage"
    DIRECT_OPEN = "direct_open"


class InstanceRef(ScratchRecord):
    run_id: HashRef
    seq: int = Field(ge=0)


class ScratchProvenanceV1(ScratchRecord):
    """Intellectual origin only; never a warrant or routing instruction."""

    actor: ScratchActor
    origin: Annotated[str, Field(min_length=1, max_length=512)] | None = None
    source_refs: list[OpaqueRef] = Field(default_factory=FrozenList, max_length=256)
    formal_artifact_refs: list[OpaqueRef] = Field(default_factory=FrozenList, max_length=256)

    @field_validator("origin")
    @classmethod
    def _origin_nonblank(cls, value):
        return _require_nonblank(value)

    @field_validator("source_refs", "formal_artifact_refs", mode="after")
    @classmethod
    def _freeze_refs(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("provenance references must not contain duplicates")
        return FrozenList(value)


class ScratchBlockBodyV1(ScratchRecord):
    content: LongText
    why_keep_this: LongText | None = None
    unfinished: LongText | None = None
    possible_next_move: LongText | None = None

    @field_validator("content", "why_keep_this", "unfinished", "possible_next_move")
    @classmethod
    def _nonblank_text(cls, value):
        return _require_nonblank(value)


class ScratchBlockV1(ScratchRecord):
    schema_: Literal["scratch.block.v1"] = Field("scratch.block.v1", alias="schema")
    id: HashRef
    body: ScratchBlockBodyV1
    body_hash: HashRef
    instance: InstanceRef
    provenance: ScratchProvenanceV1
    revision_of: HashRef | None = None

    @staticmethod
    def compute_body_hash(body: ScratchBlockBodyV1) -> str:
        return domain_hash("scratch.block.body.v1", body)

    @staticmethod
    def compute_id(
        body_hash: str,
        instance: InstanceRef,
        provenance: ScratchProvenanceV1,
        revision_of: str | None = None,
    ) -> str:
        return domain_hash(
            "scratch.block.instance.v1",
            _without_none(
                body_hash=body_hash,
                instance=instance,
                revision_of=revision_of,
                provenance=provenance,
            ),
        )

    @classmethod
    def create(
        cls,
        body: ScratchBlockBodyV1 | Mapping,
        instance: InstanceRef | Mapping,
        provenance: ScratchProvenanceV1 | Mapping,
        *,
        revision_of: str | None = None,
    ) -> ScratchBlockV1:
        body = ScratchBlockBodyV1.model_validate(body)
        instance = InstanceRef.model_validate(instance)
        provenance = ScratchProvenanceV1.model_validate(provenance)
        body_hash = cls.compute_body_hash(body)
        return cls(
            id=cls.compute_id(body_hash, instance, provenance, revision_of),
            body=body,
            body_hash=body_hash,
            instance=instance,
            provenance=provenance,
            revision_of=revision_of,
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        expected_body = self.compute_body_hash(self.body)
        if self.body_hash != expected_body:
            raise ValueError("body_hash does not match canonical scratch block body")
        expected = self.compute_id(
            self.body_hash, self.instance, self.provenance, self.revision_of
        )
        if self.id != expected:
            raise ValueError("id does not match canonical scratch block identity")
        return self


class ScratchLinkBodyV1(ScratchRecord):
    from_: HashRef = Field(alias="from")
    to: HashRef
    relation_hint: ShortText
    because: LongText | None = None
    holds_when: LongText | None = None
    weakens_when: LongText | None = None
    direction: LinkDirection | None = None
    supersedes: HashRef | None = None

    @field_validator("relation_hint", "because", "holds_when", "weakens_when")
    @classmethod
    def _nonblank_text(cls, value):
        return _require_nonblank(value)


class ScratchLinkV1(ScratchRecord):
    schema_: Literal["scratch.link.v1"] = Field("scratch.link.v1", alias="schema")
    id: HashRef
    body: ScratchLinkBodyV1
    instance: InstanceRef

    @staticmethod
    def compute_id(body: ScratchLinkBodyV1, instance: InstanceRef) -> str:
        return domain_hash(
            "scratch.link.instance.v1",
            {"body": _canonical_value(body), "instance": _canonical_value(instance)},
        )

    @classmethod
    def create(
        cls, body: ScratchLinkBodyV1 | Mapping, instance: InstanceRef | Mapping
    ) -> ScratchLinkV1:
        body = ScratchLinkBodyV1.model_validate(body)
        instance = InstanceRef.model_validate(instance)
        return cls(id=cls.compute_id(body, instance), body=body, instance=instance)

    @model_validator(mode="after")
    def _identity_matches(self):
        if self.id != self.compute_id(self.body, self.instance):
            raise ValueError("id does not match canonical scratch link identity")
        return self


class ScratchClusterV1(ScratchRecord):
    schema_: Literal["scratch.cluster.v1"] = Field("scratch.cluster.v1", alias="schema")
    id: HashRef
    seed_focus: LongText
    instance: InstanceRef

    @field_validator("seed_focus")
    @classmethod
    def _nonblank_focus(cls, value):
        return _require_nonblank(value)

    @staticmethod
    def compute_id(seed_focus: str, instance: InstanceRef) -> str:
        return domain_hash(
            "scratch.cluster.instance.v1",
            {"seed_focus": seed_focus, "instance": _canonical_value(instance)},
        )

    @classmethod
    def create(cls, seed_focus: str, instance: InstanceRef | Mapping) -> ScratchClusterV1:
        instance = InstanceRef.model_validate(instance)
        return cls(
            id=cls.compute_id(seed_focus, instance),
            seed_focus=seed_focus,
            instance=instance,
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        if self.id != self.compute_id(self.seed_focus, self.instance):
            raise ValueError("id does not match canonical scratch cluster identity")
        return self


class ClusterMembershipV1(ScratchRecord):
    schema_: Literal["scratch.cluster.membership.v1"] = Field(
        "scratch.cluster.membership.v1", alias="schema"
    )
    id: HashRef
    cluster_id: HashRef
    block_id: HashRef
    action: MembershipAction
    reason: LongText | None = None
    instance: InstanceRef

    @field_validator("reason")
    @classmethod
    def _nonblank_reason(cls, value):
        return _require_nonblank(value)

    @staticmethod
    def compute_id(
        cluster_id: str,
        block_id: str,
        action: MembershipAction | str,
        instance: InstanceRef,
        reason: str | None = None,
    ) -> str:
        action = MembershipAction(action)
        return domain_hash(
            "scratch.cluster.membership.v1",
            _without_none(
                cluster_id=cluster_id,
                block_id=block_id,
                action=action.value,
                reason=reason,
                instance=instance,
            ),
        )

    @classmethod
    def create(
        cls,
        cluster_id: str,
        block_id: str,
        action: MembershipAction | str,
        instance: InstanceRef | Mapping,
        *,
        reason: str | None = None,
    ) -> ClusterMembershipV1:
        instance = InstanceRef.model_validate(instance)
        action = MembershipAction(action)
        return cls(
            id=cls.compute_id(cluster_id, block_id, action, instance, reason),
            cluster_id=cluster_id,
            block_id=block_id,
            action=action,
            reason=reason,
            instance=instance,
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        if self.id != self.compute_id(
            self.cluster_id, self.block_id, self.action, self.instance, self.reason
        ):
            raise ValueError("id does not match canonical cluster membership identity")
        return self


class ClusterSnapshotV1(ScratchRecord):
    schema_: Literal["scratch.cluster.snapshot.v1"] = Field(
        "scratch.cluster.snapshot.v1", alias="schema"
    )
    cluster_id: HashRef
    member_ids: list[HashRef] = Field(default_factory=FrozenList, max_length=100_000)
    live_link_ids: list[HashRef] = Field(default_factory=FrozenList, max_length=100_000)
    snapshot_hash: HashRef

    @property
    def id(self) -> str:
        """Compatibility identity used by the shared/MiniReason object API."""

        return self.snapshot_hash

    @staticmethod
    def compute_hash(cluster_id: str, member_ids: list[str], live_link_ids: list[str]) -> str:
        return domain_hash(
            "scratch.cluster.snapshot.v1",
            {
                "cluster_id": cluster_id,
                "member_ids": sorted(set(member_ids)),
                "live_link_ids": sorted(set(live_link_ids)),
            },
        )

    @classmethod
    def create(
        cls, cluster_id: str, member_ids: list[str], live_link_ids: list[str]
    ) -> ClusterSnapshotV1:
        members = sorted(set(member_ids))
        links = sorted(set(live_link_ids))
        return cls(
            cluster_id=cluster_id,
            member_ids=members,
            live_link_ids=links,
            snapshot_hash=cls.compute_hash(cluster_id, members, links),
        )

    @field_validator("member_ids", "live_link_ids", mode="after")
    @classmethod
    def _canonical_lists(cls, value, info):
        return _sorted_unique(value, info.field_name)

    @model_validator(mode="after")
    def _identity_matches(self):
        if self.snapshot_hash != self.compute_hash(
            self.cluster_id, self.member_ids, self.live_link_ids
        ):
            raise ValueError("snapshot_hash does not match canonical cluster snapshot")
        return self


class LLMCallRef(ScratchRecord):
    event_seq: int = Field(ge=0)
    model: Annotated[str, Field(min_length=1, max_length=512)]
    endpoint: Annotated[str, Field(min_length=1, max_length=2_048)]
    prompt_ref: OpaqueRef
    raw_ref: OpaqueRef

    @field_validator("model", "endpoint", "prompt_ref", "raw_ref")
    @classmethod
    def _nonblank_values(cls, value):
        return _require_nonblank(value)


class ClusterGuideV1(ScratchRecord):
    schema_: Literal["scratch.cluster.guide.v1"] = Field(
        "scratch.cluster.guide.v1", alias="schema"
    )
    id: HashRef
    cluster_id: HashRef
    based_on_snapshot: HashRef
    working_focus: LongText
    open_threads: list[ShortText] | None = Field(default=None, max_length=256)
    entry_points: list[HashRef] | None = Field(default=None, max_length=256)
    local_summary: LongText | None = None
    authored_by: LLMCallRef
    instance: InstanceRef

    @field_validator("working_focus", "local_summary")
    @classmethod
    def _nonblank_text(cls, value):
        return _require_nonblank(value)

    @field_validator("open_threads", mode="after")
    @classmethod
    def _freeze_threads(cls, value):
        if value is not None:
            for item in value:
                _require_nonblank(item)
        return _freeze_list(value)

    @field_validator("entry_points", mode="after")
    @classmethod
    def _freeze_entries(cls, value):
        if value is not None and len(set(value)) != len(value):
            raise ValueError("entry_points must not contain duplicates")
        return _freeze_list(value)

    @classmethod
    def _identity_payload(cls, values: Mapping) -> dict:
        return {key: _canonical_value(value) for key, value in values.items() if value is not None}

    @classmethod
    def create(
        cls,
        *,
        cluster_id: str,
        based_on_snapshot: str,
        working_focus: str,
        authored_by: LLMCallRef | Mapping,
        instance: InstanceRef | Mapping,
        open_threads: list[str] | None = None,
        entry_points: list[str] | None = None,
        local_summary: str | None = None,
    ) -> ClusterGuideV1:
        authored_by = LLMCallRef.model_validate(authored_by)
        instance = InstanceRef.model_validate(instance)
        payload = cls._identity_payload(
            {
                "cluster_id": cluster_id,
                "based_on_snapshot": based_on_snapshot,
                "working_focus": working_focus,
                "open_threads": open_threads,
                "entry_points": entry_points,
                "local_summary": local_summary,
                "authored_by": authored_by,
                "instance": instance,
            }
        )
        return cls(
            id=domain_hash("scratch.cluster.guide.v1", payload),
            cluster_id=cluster_id,
            based_on_snapshot=based_on_snapshot,
            working_focus=working_focus,
            open_threads=open_threads,
            entry_points=entry_points,
            local_summary=local_summary,
            authored_by=authored_by,
            instance=instance,
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        payload = self._identity_payload(
            self.model_dump(
                mode="python",
                by_alias=True,
                exclude={"schema_", "id"},
                exclude_none=True,
            )
        )
        if self.id != domain_hash("scratch.cluster.guide.v1", payload):
            raise ValueError("id does not match canonical cluster guide identity")
        return self


class SimilarityHitV1(ScratchRecord):
    schema_: Literal["scratch.similarity.v1"] = Field(
        "scratch.similarity.v1", alias="schema"
    )
    id: HashRef
    block_a: HashRef
    block_b: HashRef
    embedder: Annotated[str, Field(min_length=1, max_length=512)]
    embedder_version: Annotated[str, Field(min_length=1, max_length=512)]
    score: float
    threshold_used: float
    input_body_hash_a: HashRef
    input_body_hash_b: HashRef
    output_ref: OpaqueRef | None = None
    instance: InstanceRef

    @field_validator("embedder", "embedder_version", "output_ref")
    @classmethod
    def _nonblank_values(cls, value):
        return _require_nonblank(value)

    @field_validator("score", "threshold_used")
    @classmethod
    def _finite_values(cls, value):
        if not math.isfinite(value):
            raise ValueError("similarity values must be finite")
        return value

    @classmethod
    def create(cls, **values) -> SimilarityHitV1:
        normalized = dict(values)
        normalized["score"] = float(normalized["score"])
        normalized["threshold_used"] = float(normalized["threshold_used"])
        normalized["instance"] = InstanceRef.model_validate(normalized["instance"])
        payload = {
            key: _canonical_value(value)
            for key, value in normalized.items()
            if value is not None
        }
        return cls(id=domain_hash("scratch.similarity.v1", payload), **normalized)

    @model_validator(mode="after")
    def _identity_matches(self):
        payload = self.model_dump(
            mode="json", by_alias=True, exclude={"schema_", "id"}, exclude_none=True
        )
        if self.id != domain_hash("scratch.similarity.v1", payload):
            raise ValueError("id does not match canonical similarity observation")
        return self


class AttentionReceiptV1(ScratchRecord):
    schema_: Literal["scratch.attention.receipt.v1"] = Field(
        "scratch.attention.receipt.v1", alias="schema"
    )
    receipt_hash: HashRef
    state_seq: int = Field(ge=0)
    request_hash: HashRef
    selected_by_channel: Mapping[RetrievalChannel, list[HashRef]] = Field(
        default_factory=FrozenDict
    )
    final_order: list[HashRef] = Field(default_factory=FrozenList, max_length=10_000)
    excluded_by_global_limit: list[HashRef] = Field(
        default_factory=FrozenList, max_length=100_000
    )
    excluded_by_channel: Mapping[RetrievalChannel, list[HashRef]] = Field(
        default_factory=FrozenDict
    )
    deterministic_seed: int
    coverage_cycle_id: HashRef | None = None
    instance: InstanceRef

    @property
    def id(self) -> str:
        """Compatibility identity used by the shared/MiniReason object API."""

        return self.receipt_hash

    @field_validator("selected_by_channel", "excluded_by_channel", mode="after")
    @classmethod
    def _freeze_channel_maps(cls, value):
        return FrozenDict({key: FrozenList(ids) for key, ids in value.items()})

    @field_validator("final_order", "excluded_by_global_limit", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)

    @classmethod
    def create(cls, **values) -> AttentionReceiptV1:
        payload = {key: _canonical_value(value) for key, value in values.items() if value is not None}
        return cls(
            receipt_hash=domain_hash("scratch.attention.receipt.v1", payload), **values
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        payload = self.model_dump(
            mode="json",
            by_alias=True,
            exclude={"schema_", "receipt_hash"},
            exclude_none=True,
        )
        if self.receipt_hash != domain_hash("scratch.attention.receipt.v1", payload):
            raise ValueError("receipt_hash does not match canonical attention receipt")
        return self


class VisibilityRecordV1(ScratchRecord):
    schema_: Literal["scratch.visibility.record.v1"] = Field(
        "scratch.visibility.record.v1", alias="schema"
    )
    id: HashRef
    block_id: HashRef
    first_created_seq: int = Field(ge=0)
    render_count: int = Field(ge=0)
    last_rendered_seq: int | None = Field(default=None, ge=0)
    retrieval_channels_used: list[RetrievalChannel] = Field(
        default_factory=FrozenList, max_length=len(RetrievalChannel)
    )
    contexts_rendered_into: list[HashRef] = Field(default_factory=FrozenList, max_length=100_000)
    instance: InstanceRef

    @field_validator("retrieval_channels_used", mode="after")
    @classmethod
    def _canonical_channels(cls, value):
        values = [item.value if isinstance(item, RetrievalChannel) else item for item in value]
        if values != sorted(set(values)):
            raise ValueError("retrieval_channels_used must be sorted and unique")
        return FrozenList(value)

    @field_validator("contexts_rendered_into", mode="after")
    @classmethod
    def _freeze_contexts(cls, value):
        return FrozenList(value)

    @model_validator(mode="after")
    def _sequence_consistency(self):
        if self.render_count == 0 and self.last_rendered_seq is not None:
            raise ValueError("an unrendered block cannot have last_rendered_seq")
        if self.render_count > 0 and self.last_rendered_seq is None:
            raise ValueError("a rendered block requires last_rendered_seq")
        if self.last_rendered_seq is not None and self.last_rendered_seq < self.first_created_seq:
            raise ValueError("last_rendered_seq cannot precede block creation")
        payload = self.model_dump(
            mode="json", by_alias=True, exclude={"schema_", "id"}, exclude_none=True
        )
        if self.id != domain_hash("scratch.visibility.record.v1", payload):
            raise ValueError("id does not match canonical visibility record")
        return self

    @classmethod
    def create(cls, **values) -> VisibilityRecordV1:
        payload = {key: _canonical_value(value) for key, value in values.items() if value is not None}
        return cls(id=domain_hash("scratch.visibility.record.v1", payload), **values)


class CoverageCycleV1(ScratchRecord):
    schema_: Literal["scratch.coverage.cycle.v1"] = Field(
        "scratch.coverage.cycle.v1", alias="schema"
    )
    cycle_id: HashRef
    started_at_seq: int = Field(ge=0)
    pending_block_ids: list[HashRef] = Field(default_factory=FrozenList, max_length=100_000)
    rendered_block_ids: list[HashRef] = Field(default_factory=FrozenList, max_length=100_000)
    state: CoverageState
    instance: InstanceRef

    @property
    def id(self) -> str:
        """Compatibility identity used by the shared/MiniReason object API."""

        return self.cycle_id

    @field_validator("pending_block_ids", "rendered_block_ids", mode="after")
    @classmethod
    def _canonical_lists(cls, value, info):
        return _sorted_unique(value, info.field_name)

    @staticmethod
    def compute_id(live_ids: list[str], instance: InstanceRef) -> str:
        return domain_hash(
            "scratch.coverage.cycle.v1",
            {"live_ids": sorted(set(live_ids)), "instance": _canonical_value(instance)},
        )

    @classmethod
    def create(
        cls, live_ids: list[str], instance: InstanceRef | Mapping
    ) -> CoverageCycleV1:
        instance = InstanceRef.model_validate(instance)
        live_ids = sorted(set(live_ids))
        return cls(
            cycle_id=cls.compute_id(live_ids, instance),
            started_at_seq=instance.seq,
            pending_block_ids=live_ids,
            rendered_block_ids=[],
            state=CoverageState.ACTIVE if live_ids else CoverageState.COMPLETED,
            instance=instance,
        )

    @model_validator(mode="after")
    def _identity_and_state_match(self):
        if set(self.pending_block_ids) & set(self.rendered_block_ids):
            raise ValueError("pending and rendered coverage blocks must be disjoint")
        if self.started_at_seq != self.instance.seq:
            raise ValueError("coverage started_at_seq must equal its instance seq")
        if self.state == CoverageState.COMPLETED and self.pending_block_ids:
            raise ValueError("a completed coverage cycle cannot have pending blocks")
        if self.state == CoverageState.ACTIVE and not self.pending_block_ids:
            raise ValueError("an active coverage cycle requires pending blocks")
        live_ids = sorted([*self.pending_block_ids, *self.rendered_block_ids])
        if self.cycle_id != self.compute_id(live_ids, self.instance):
            raise ValueError("cycle_id does not match canonical coverage population")
        return self


class AdvisoryContextV1(ScratchRecord):
    schema_: Literal["scratch.advisory.context.v1"] = Field(
        "scratch.advisory.context.v1", alias="schema"
    )
    id: HashRef
    warning: LongText
    blocks: list[ScratchBlockV1] = Field(default_factory=FrozenList, max_length=1_000)
    links: list[ScratchLinkV1] | None = Field(default=None, max_length=1_000)
    guides: list[ClusterGuideV1] | None = Field(default=None, max_length=100)
    retrieval_receipt: HashRef
    instance: InstanceRef

    @field_validator("warning")
    @classmethod
    def _nonblank_warning(cls, value):
        value = _require_nonblank(value)
        if "non-authoritative" not in value.casefold():
            raise ValueError("advisory warning must identify scratch material as non-authoritative")
        return value

    @field_validator("blocks", "links", "guides", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return _freeze_list(value)

    @classmethod
    def create(cls, **values) -> AdvisoryContextV1:
        payload = {key: _canonical_value(value) for key, value in values.items() if value is not None}
        return cls(id=domain_hash("scratch.advisory.context.v1", payload), **values)

    @model_validator(mode="after")
    def _identity_matches(self):
        payload = self.model_dump(
            mode="json", by_alias=True, exclude={"schema_", "id"}, exclude_none=True
        )
        if self.id != domain_hash("scratch.advisory.context.v1", payload):
            raise ValueError("id does not match canonical advisory context")
        return self
