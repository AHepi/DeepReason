"""Transport-neutral application boundary for advisory scratch queries.

The query vocabulary is deliberately closed.  Preview operations are
physically read-only, while ``record_direct_open`` is a distinct intent whose
only mutation is the historical direct-open attention receipt and visibility
update.  CLI and MCP adapters own parsing, bounds specific to their transports,
and presentation; this module owns canonical query semantics.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    TypeAdapter,
    field_validator,
)

from deepreason.harness import Harness
from deepreason.locking import ProcessLockBusy, operator_locks
from deepreason.scratch.attention import AttentionPackV1, AttentionPlanner, AttentionRequestV1
from deepreason.scratch.errors import ScratchRootBusy
from deepreason.scratch.models import (
    AttentionReceiptV1,
    HashRef,
    RetrievalChannel,
    ScratchBlockV1,
    VisibilityRecordV1,
    domain_hash,
)
from deepreason.scratch.service import ScratchService


MAX_QUERY_RESULTS = 100
MAX_QUERY_TEXT_CHARS = 16_384
MAX_REFERENCE_CHARS = 512
PREVIEW_CHARS = 320


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        populate_by_name=True,
    )


class _QueryBase(_StrictModel):
    root: str = Field(min_length=1, max_length=4_096)

    @field_validator("root")
    @classmethod
    def _safe_root_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("root contains a NUL byte")
        return value


class _HistoricalQueryBase(_QueryBase):
    at_seq: StrictInt | None = Field(default=None, ge=0)
    limit: StrictInt = Field(default=20, ge=1, le=MAX_QUERY_RESULTS)


class ScratchMapQueryV1(_HistoricalQueryBase):
    operation: Literal["map"] = "map"
    ordering: Literal["created", "id", "size"] = "created"


class ScratchSearchQueryV1(_HistoricalQueryBase):
    operation: Literal["search"] = "search"
    query: str = Field(min_length=1, max_length=MAX_QUERY_TEXT_CHARS)

    @field_validator("query")
    @classmethod
    def _nonblank_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value


class _BlockQueryBase(_HistoricalQueryBase):
    block: str = Field(min_length=1, max_length=MAX_REFERENCE_CHARS)
    include_retired: bool = False

    @field_validator("block")
    @classmethod
    def _safe_block_reference(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("block reference contains a NUL byte")
        return value


class ScratchOpenPreviewQueryV1(_BlockQueryBase):
    operation: Literal["open_preview"] = "open_preview"


class ScratchRecordDirectOpenQueryV1(_QueryBase):
    """The one query intent allowed to record scratch retrieval visibility."""

    operation: Literal["record_direct_open"] = "record_direct_open"
    block: str = Field(min_length=1, max_length=MAX_REFERENCE_CHARS)
    include_retired: bool = False
    limit: StrictInt = Field(default=20, ge=1, le=MAX_QUERY_RESULTS)

    @field_validator("block")
    @classmethod
    def _safe_block_reference(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("block reference contains a NUL byte")
        return value


class ScratchRelatedQueryV1(_BlockQueryBase):
    operation: Literal["related"] = "related"


class ScratchAttentionPreviewQueryV1(_QueryBase):
    operation: Literal["attention_preview"] = "attention_preview"
    at_seq: StrictInt | None = Field(default=None, ge=0)
    focus_blocks: tuple[str, ...] = Field(default=(), max_length=64)
    focus_clusters: tuple[str, ...] = Field(default=(), max_length=64)
    maximum_blocks: StrictInt = Field(default=20, ge=1, le=32)
    maximum_cluster_guides: StrictInt = Field(default=4, ge=0, le=8)
    deterministic_seed: StrictInt = Field(default=0, ge=0, le=2**63 - 1)

    @field_validator("focus_blocks", "focus_clusters")
    @classmethod
    def _bounded_unique_references(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)):
            raise ValueError("focus references must be unique")
        if any(
            not value or len(value) > MAX_REFERENCE_CHARS or "\x00" in value for value in values
        ):
            raise ValueError("focus references must be bounded non-NUL text")
        return values


ScratchQueryV1: TypeAlias = Annotated[
    ScratchMapQueryV1
    | ScratchSearchQueryV1
    | ScratchOpenPreviewQueryV1
    | ScratchRecordDirectOpenQueryV1
    | ScratchRelatedQueryV1
    | ScratchAttentionPreviewQueryV1,
    Field(discriminator="operation"),
]


class ScratchIdentityIndexV1(_StrictModel):
    """Internal-only identity population used for collision-safe CLI labels."""

    block_ids: tuple[HashRef, ...] = ()
    link_ids: tuple[HashRef, ...] = ()
    cluster_ids: tuple[HashRef, ...] = ()
    coverage_ids: tuple[HashRef, ...] = ()


class ScratchBlockSummaryV1(_StrictModel):
    block_id: HashRef
    content_preview: str
    created_seq: StrictInt = Field(ge=0)
    render_count: StrictInt = Field(ge=0)
    last_rendered_seq: StrictInt | None = Field(default=None, ge=0)
    revision_of: HashRef | None = None

    def presentation_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


class ScratchLinkSummaryV1(_StrictModel):
    link_id: HashRef
    from_: HashRef = Field(alias="from")
    to: HashRef
    relation_hint: str
    status: Literal["suggested", "active", "superseded", "retired"]
    supersedes: HashRef | None = None

    def presentation_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


class ScratchClusterMapItemV1(_StrictModel):
    cluster_id: HashRef
    focus_preview: str
    member_count: StrictInt = Field(ge=0)
    member_ids: tuple[HashRef, ...]
    members_truncated: bool
    guide_id: HashRef | None = None
    guide_state: Literal["current", "stale"] | None = None

    def presentation_payload(self) -> dict[str, Any]:
        # Historical output includes explicit null guide fields.
        return self.model_dump(mode="json", by_alias=True)


class ScratchRelatedClusterV1(_StrictModel):
    cluster_id: HashRef
    focus_preview: str
    member_count: StrictInt = Field(ge=0)


class ScratchSimilaritySummaryV1(_StrictModel):
    similarity_id: HashRef
    block_id: HashRef
    score: float
    threshold_used: float
    embedder: str
    embedder_version: str


class ScratchRelatedBlockV1(ScratchBlockSummaryV1):
    channels: tuple[Literal["link", "cluster", "semantic_similarity"], ...]

    def presentation_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


class _ResultBase(_StrictModel):
    identities: ScratchIdentityIndexV1 = Field(exclude=True)


class ScratchMapResultV1(_ResultBase):
    operation: Literal["map"] = Field(default="map", exclude=True)
    clusters: tuple[ScratchClusterMapItemV1, ...]
    count: StrictInt = Field(ge=0)
    ordering: Literal["created", "id", "size"]
    unclustered_block_count: StrictInt = Field(ge=0)

    def presentation_payload(self) -> dict[str, Any]:
        return {
            "clusters": [item.presentation_payload() for item in self.clusters],
            "count": self.count,
            "ordering": self.ordering,
            "unclustered_block_count": self.unclustered_block_count,
        }


class ScratchSearchResultV1(_ResultBase):
    operation: Literal["search"] = Field(default="search", exclude=True)
    query: str
    blocks: tuple[ScratchBlockSummaryV1, ...]
    count: StrictInt = Field(ge=0)

    def presentation_payload(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "blocks": [item.presentation_payload() for item in self.blocks],
            "count": self.count,
        }


class _ScratchOpenResultBase(_ResultBase):
    block: ScratchBlockV1
    revisions: tuple[ScratchBlockSummaryV1, ...]
    revision_count: StrictInt = Field(ge=0)
    links: tuple[ScratchLinkSummaryV1, ...]
    link_count: StrictInt = Field(ge=0)
    cluster_ids: tuple[HashRef, ...]
    cluster_count: StrictInt = Field(ge=0)
    visibility: VisibilityRecordV1 | None
    retrieval_receipt_id: HashRef | None
    committed: bool

    def presentation_payload(self, *, include_committed: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "block": self.block.model_dump(mode="json", by_alias=True, exclude_none=True),
            "revisions": [item.presentation_payload() for item in self.revisions],
            "revision_count": self.revision_count,
            "links": [item.presentation_payload() for item in self.links],
            "link_count": self.link_count,
            "cluster_ids": list(self.cluster_ids),
            "cluster_count": self.cluster_count,
            "visibility": (
                self.visibility.model_dump(mode="json", by_alias=True, exclude_none=True)
                if self.visibility is not None
                else None
            ),
            "retrieval_receipt_id": self.retrieval_receipt_id,
        }
        if include_committed:
            payload["committed"] = self.committed
        return payload


class ScratchOpenPreviewResultV1(_ScratchOpenResultBase):
    operation: Literal["open_preview"] = Field(default="open_preview", exclude=True)
    retrieval_receipt_id: None = None
    committed: Literal[False] = False


class ScratchRecordDirectOpenResultV1(_ScratchOpenResultBase):
    operation: Literal["record_direct_open"] = Field(default="record_direct_open", exclude=True)
    retrieval_receipt_id: HashRef
    committed: Literal[True] = True


class ScratchRelatedResultV1(_ResultBase):
    operation: Literal["related"] = Field(default="related", exclude=True)
    focus_block_id: HashRef
    blocks: tuple[ScratchRelatedBlockV1, ...]
    links: tuple[ScratchLinkSummaryV1, ...]
    clusters: tuple[ScratchRelatedClusterV1, ...]
    similarity_observations: tuple[ScratchSimilaritySummaryV1, ...]
    count: StrictInt = Field(ge=0)
    advisory_warning: Literal[
        "Similarity is retrieval-only and does not establish identity, truth, "
        "support, attack, duplication, or deletion."
    ] = (
        "Similarity is retrieval-only and does not establish identity, truth, "
        "support, attack, duplication, or deletion."
    )

    def presentation_payload(self) -> dict[str, Any]:
        return {
            "focus_block_id": self.focus_block_id,
            "blocks": [item.presentation_payload() for item in self.blocks],
            "links": [item.presentation_payload() for item in self.links],
            "clusters": [item.model_dump(mode="json", by_alias=True) for item in self.clusters],
            "similarity_observations": [
                item.model_dump(mode="json", by_alias=True) for item in self.similarity_observations
            ],
            "count": self.count,
            "advisory_warning": self.advisory_warning,
        }


class ScratchAttentionPreviewResultV1(_ResultBase):
    operation: Literal["attention_preview"] = Field(default="attention_preview", exclude=True)
    pack: AttentionPackV1
    committed: Literal[False] = False
    advisory_warning: Literal[
        "This is a retrieval-only preview. It changes no visibility, coverage, "
        "formal state, identity, truth, support, or attack."
    ] = (
        "This is a retrieval-only preview. It changes no visibility, coverage, "
        "formal state, identity, truth, support, or attack."
    )

    def presentation_payload(self) -> dict[str, Any]:
        payload = self.pack.model_dump(mode="json", by_alias=True, exclude_none=True)
        payload["selection_receipt"]["id"] = self.pack.selection_receipt.id
        payload.update(
            {
                "committed": self.committed,
                "advisory_warning": self.advisory_warning,
            }
        )
        return payload


ScratchQueryResultV1: TypeAlias = Annotated[
    ScratchMapResultV1
    | ScratchSearchResultV1
    | ScratchOpenPreviewResultV1
    | ScratchRecordDirectOpenResultV1
    | ScratchRelatedResultV1
    | ScratchAttentionPreviewResultV1,
    Field(discriminator="operation"),
]


_QUERY_ADAPTER = TypeAdapter(ScratchQueryV1)


def _terminal_safe(value: str) -> str:
    result: list[str] = []
    for character in value:
        if character in {"\n", "\t"}:
            result.append(character)
        elif unicodedata.category(character).startswith("C"):
            result.append(f"\\u{ord(character):04x}")
        else:
            result.append(character)
    return "".join(result)


def _preview(value: str, limit: int = PREVIEW_CHARS) -> str:
    normalized = " ".join(_terminal_safe(value).split())
    return normalized if len(normalized) <= limit else normalized[: limit - 1] + "…"


def _identity_index(service: ScratchService) -> ScratchIdentityIndexV1:
    return ScratchIdentityIndexV1(
        block_ids=tuple(service.state.blocks),
        link_ids=tuple(service.state.links),
        cluster_ids=tuple(service.state.clusters),
        coverage_ids=tuple(service.state.coverage_cycles),
    )


def _block_summary(service: ScratchService, block) -> ScratchBlockSummaryV1:
    visibility = service.state.visibility.get(block.id)
    return ScratchBlockSummaryV1(
        block_id=block.id,
        content_preview=_preview(block.body.content),
        created_seq=block.instance.seq,
        render_count=visibility.render_count if visibility is not None else 0,
        last_rendered_seq=(visibility.last_rendered_seq if visibility is not None else None),
        revision_of=block.revision_of,
    )


def _link_summary(service: ScratchService, link) -> ScratchLinkSummaryV1:
    return ScratchLinkSummaryV1(
        link_id=link.id,
        **{
            "from": link.body.from_,
            "to": link.body.to,
            "relation_hint": _preview(link.body.relation_hint),
            "status": service.state.link_status[link.id].value,
            "supersedes": link.body.supersedes,
        },
    )


def _read_service(root: str, at_seq: int | None) -> ScratchService:
    path = Path(root)
    harness = Harness.at(path, at_seq) if at_seq is not None else Harness(path, read_only=True)
    return ScratchService(harness)


def _open_result_values(
    service: ScratchService,
    *,
    block_reference: str,
    include_retired: bool,
    limit: int,
) -> dict[str, Any]:
    block = service.get_block(block_reference)
    revisions = service.revisions(block.id)
    links = service.links_for(block.id, include_retired=include_retired)
    clusters = sorted(service.state.clusters_by_block.get(block.id, set()))
    return {
        "identities": _identity_index(service),
        "block": block,
        "revisions": tuple(_block_summary(service, item) for item in revisions[:limit]),
        "revision_count": len(revisions),
        "links": tuple(_link_summary(service, item) for item in links[:limit]),
        "link_count": len(links),
        "cluster_ids": tuple(clusters[:limit]),
        "cluster_count": len(clusters),
        "visibility": service.state.visibility.get(block.id),
    }


class ScratchQueryApplicationService:
    """Execute the closed scratch query vocabulary without transport policy."""

    def execute(self, query: ScratchQueryV1) -> ScratchQueryResultV1:
        query = _QUERY_ADAPTER.validate_python(query)
        if isinstance(query, ScratchMapQueryV1):
            return self._map(query)
        if isinstance(query, ScratchSearchQueryV1):
            return self._search(query)
        if isinstance(query, ScratchOpenPreviewQueryV1):
            return self._open_preview(query)
        if isinstance(query, ScratchRecordDirectOpenQueryV1):
            return self._record_direct_open(query)
        if isinstance(query, ScratchRelatedQueryV1):
            return self._related(query)
        if isinstance(query, ScratchAttentionPreviewQueryV1):
            return self._attention_preview(query)
        raise TypeError("unsupported scratch query")

    @staticmethod
    def _map(query: ScratchMapQueryV1) -> ScratchMapResultV1:
        service = _read_service(query.root, query.at_seq)
        clusters = service.cluster_map(query.limit, ordering=query.ordering)
        items: list[ScratchClusterMapItemV1] = []
        for cluster in clusters:
            members = service.cluster_members(cluster.id)
            guides = service.state.guides_by_cluster.get(cluster.id, [])
            guide = max(guides, key=lambda item: (item.instance.seq, item.id)) if guides else None
            guide_state = service.state.guide_state(guide) if guide is not None else None
            items.append(
                ScratchClusterMapItemV1(
                    cluster_id=cluster.id,
                    focus_preview=_preview(cluster.seed_focus),
                    member_count=len(members),
                    member_ids=tuple(block.id for block in members[: query.limit]),
                    members_truncated=len(members) > query.limit,
                    guide_id=guide.id if guide is not None else None,
                    guide_state=guide_state,
                )
            )
        clustered = (
            set().union(*service.state.current_memberships.values())
            if service.state.current_memberships
            else set()
        )
        return ScratchMapResultV1(
            identities=_identity_index(service),
            clusters=tuple(items),
            count=len(items),
            ordering=query.ordering,
            unclustered_block_count=len(set(service.state.blocks) - clustered),
        )

    @staticmethod
    def _search(query: ScratchSearchQueryV1) -> ScratchSearchResultV1:
        service = _read_service(query.root, query.at_seq)
        blocks = service.search_phrase(query.query, query.limit)
        summaries = tuple(_block_summary(service, block) for block in blocks)
        return ScratchSearchResultV1(
            identities=_identity_index(service),
            query=query.query,
            blocks=summaries,
            count=len(summaries),
        )

    @staticmethod
    def _open_preview(
        query: ScratchOpenPreviewQueryV1,
    ) -> ScratchOpenPreviewResultV1:
        service = _read_service(query.root, query.at_seq)
        return ScratchOpenPreviewResultV1(
            **_open_result_values(
                service,
                block_reference=query.block,
                include_retired=query.include_retired,
                limit=query.limit,
            )
        )

    @staticmethod
    def _record_direct_open(
        query: ScratchRecordDirectOpenQueryV1,
    ) -> ScratchRecordDirectOpenResultV1:
        root = Path(query.root)
        if not root.is_dir():
            raise FileNotFoundError(f"read-only harness root does not exist: {root}")
        try:
            locks = operator_locks(root, owner="scratch-show", blocking=False)
        except ProcessLockBusy as error:
            raise ScratchRootBusy("another operator owns this run root") from error
        try:
            service = ScratchService(Harness(root))
            block = service.get_block(query.block)
            state_seq = service.harness._next_seq - 1
            receipt = AttentionReceiptV1.create(
                state_seq=state_seq,
                request_hash=domain_hash(
                    "scratch.cli.direct-open.request.v1",
                    {"block_id": block.id, "state_seq": state_seq},
                ),
                selected_by_channel={RetrievalChannel.DIRECT_OPEN: [block.id]},
                final_order=[block.id],
                excluded_by_global_limit=[],
                excluded_by_channel={},
                deterministic_seed=0,
                instance=service._instance(),
            )
            service.record_attention_receipt(receipt, context_ref="cli:scratch-show")
            return ScratchRecordDirectOpenResultV1(
                **_open_result_values(
                    service,
                    block_reference=block.id,
                    include_retired=query.include_retired,
                    limit=query.limit,
                ),
                retrieval_receipt_id=receipt.id,
            )
        finally:
            locks.release()

    @staticmethod
    def _related(query: ScratchRelatedQueryV1) -> ScratchRelatedResultV1:
        service = _read_service(query.root, query.at_seq)
        focus = service.get_block(query.block)
        neighbours: dict[str, list[str]] = {}
        link_records = service.links_for(focus.id, include_retired=query.include_retired)
        links: list[ScratchLinkSummaryV1] = []
        for link in link_records[: query.limit]:
            other = link.body.to if link.body.from_ == focus.id else link.body.from_
            neighbours.setdefault(other, []).append("link")
            links.append(_link_summary(service, link))

        clusters: list[ScratchRelatedClusterV1] = []
        cluster_ids = sorted(service.state.clusters_by_block.get(focus.id, set()))[: query.limit]
        for cluster_id in cluster_ids:
            members = service.cluster_members(cluster_id)
            for block in members[: query.limit + 1]:
                if block.id != focus.id:
                    neighbours.setdefault(block.id, []).append("cluster")
            cluster = service.get_cluster(cluster_id)
            clusters.append(
                ScratchRelatedClusterV1(
                    cluster_id=cluster.id,
                    focus_preview=_preview(cluster.seed_focus),
                    member_count=len(members),
                )
            )

        similarity: list[tuple[float, str, str, Any]] = []
        for hit_id in service.state.similarity_by_block.get(focus.id, []):
            hit = service.state.similarity_hits[hit_id]
            other = hit.block_b if hit.block_a == focus.id else hit.block_a
            similarity.append((-hit.score, other, hit.id, hit))
        similarity.sort(key=lambda item: (item[0], item[1], item[2]))
        observations: list[ScratchSimilaritySummaryV1] = []
        for _negative_score, other, _hit_id, hit in similarity[: query.limit]:
            neighbours.setdefault(other, []).append("semantic_similarity")
            observations.append(
                ScratchSimilaritySummaryV1(
                    similarity_id=hit.id,
                    block_id=other,
                    score=hit.score,
                    threshold_used=hit.threshold_used,
                    embedder=hit.embedder,
                    embedder_version=hit.embedder_version,
                )
            )

        ordered_ids = list(neighbours)[: query.limit]
        related_blocks: list[ScratchRelatedBlockV1] = []
        for block_id in ordered_ids:
            summary = _block_summary(service, service.get_block(block_id))
            related_blocks.append(
                ScratchRelatedBlockV1(
                    **summary.model_dump(),
                    channels=tuple(dict.fromkeys(neighbours[block_id])),
                )
            )
        return ScratchRelatedResultV1(
            identities=_identity_index(service),
            focus_block_id=focus.id,
            blocks=tuple(related_blocks),
            links=tuple(links),
            clusters=tuple(clusters),
            similarity_observations=tuple(observations),
            count=len(related_blocks),
        )

    @staticmethod
    def _attention_preview(
        query: ScratchAttentionPreviewQueryV1,
    ) -> ScratchAttentionPreviewResultV1:
        from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

        service = _read_service(query.root, query.at_seq)
        try:
            manifest = load_run_manifest(Path(query.root) / MANIFEST_NAME)
        except (OSError, RuntimeError, ValueError) as error:
            raise ValueError("BRIDGE_RESULT_MANIFEST_INVALID") from error
        policy = manifest.scratch_policy
        if manifest.schema_version != 3 or policy is None or not policy.enabled:
            raise ValueError("SCRATCH_MANIFEST_V3_REQUIRED")
        block_ids = [service.get_block(item).id for item in query.focus_blocks]
        cluster_ids = [service.get_cluster(item).id for item in query.focus_clusters]
        request = AttentionRequestV1(
            focus_blocks=block_ids or None,
            focus_clusters=cluster_ids or None,
            maximum_blocks=query.maximum_blocks,
            maximum_cluster_guides=query.maximum_cluster_guides,
            deterministic_seed=query.deterministic_seed,
        )
        pack = AttentionPlanner(service, policy.attention_policy()).plan(request)
        return ScratchAttentionPreviewResultV1(
            identities=_identity_index(service),
            pack=pack,
        )


SCRATCH_QUERY_SERVICE = ScratchQueryApplicationService()


__all__ = [
    "MAX_QUERY_RESULTS",
    "SCRATCH_QUERY_SERVICE",
    "ScratchAttentionPreviewQueryV1",
    "ScratchAttentionPreviewResultV1",
    "ScratchMapQueryV1",
    "ScratchMapResultV1",
    "ScratchOpenPreviewQueryV1",
    "ScratchOpenPreviewResultV1",
    "ScratchQueryApplicationService",
    "ScratchQueryResultV1",
    "ScratchQueryV1",
    "ScratchRecordDirectOpenQueryV1",
    "ScratchRecordDirectOpenResultV1",
    "ScratchRelatedQueryV1",
    "ScratchRelatedResultV1",
    "ScratchSearchQueryV1",
    "ScratchSearchResultV1",
]
