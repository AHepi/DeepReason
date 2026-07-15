"""Deterministic multi-channel attention over advisory scratch records."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Literal

from pydantic import Field, field_validator, model_validator

from deepreason.ontology.frozen import FrozenDict, FrozenList
from deepreason.scratch.coverage import CoverageController
from deepreason.scratch.models import (
    AttentionReceiptV1,
    ClusterGuideV1,
    HashRef,
    InstanceRef,
    RetrievalChannel,
    ScratchBlockV1,
    ScratchRecord,
    domain_hash,
)
from deepreason.scratch.search import search_tokens
from deepreason.scratch.service import ScratchService
from deepreason.scratch.state import LinkState


_ATTENTION_CHANNELS = tuple(
    channel for channel in RetrievalChannel if channel != RetrievalChannel.DIRECT_OPEN
)


class AttentionPolicyV1(ScratchRecord):
    """Immutable policy seam later compiled into RunManifest v3."""

    schema_: Literal["scratch.attention.policy.v1"] = Field(
        "scratch.attention.policy.v1", alias="schema"
    )
    max_blocks_per_pack: int = Field(gt=0, le=1_000)
    max_guides_per_pack: int = Field(ge=0, le=100)
    semantic_retrieval: bool
    keyword_retrieval: bool
    coverage_enabled: bool
    coverage_slot_every_n_packs: int = Field(gt=0)
    exploratory_fraction: float = Field(ge=0.0, le=1.0)
    underexposed_fraction: float = Field(ge=0.0, le=1.0)
    dormant_after_events: int = Field(ge=0)
    similarity_top_k: int = Field(gt=0, le=10_000)
    similarity_threshold: float | None = None
    guide_max_open_threads: int = Field(ge=0, le=256)
    guide_max_entry_points: int = Field(ge=0, le=256)
    channel_priority: list[RetrievalChannel] = Field(max_length=len(_ATTENTION_CHANNELS))
    per_channel_limits: Mapping[RetrievalChannel, int]

    @property
    def coverage_cadence(self) -> int:
        return self.coverage_slot_every_n_packs

    @field_validator("similarity_threshold")
    @classmethod
    def _finite_threshold(cls, value):
        if value is not None and not math.isfinite(value):
            raise ValueError("similarity_threshold must be finite")
        return value

    @field_validator("channel_priority", mode="after")
    @classmethod
    def _complete_priority(cls, value):
        if len(value) != len(set(value)) or set(value) != set(_ATTENTION_CHANNELS):
            raise ValueError("channel_priority must contain every attention channel once")
        if value[0] != RetrievalChannel.FOCUS:
            raise ValueError("focus must be the first attention channel")
        return FrozenList(value)

    @field_validator("per_channel_limits", mode="after")
    @classmethod
    def _channel_limits(cls, value):
        normalized = {RetrievalChannel(key): item for key, item in value.items()}
        if set(normalized) != set(_ATTENTION_CHANNELS):
            raise ValueError("per_channel_limits must name every attention channel")
        if any(
            isinstance(item, bool) or item <= 0 or item > 10_000
            for item in normalized.values()
        ):
            raise ValueError("per-channel limits must be integers from 1 through 10000")
        return FrozenDict(normalized)

    @model_validator(mode="after")
    def _reserved_fraction(self):
        if self.exploratory_fraction + self.underexposed_fraction > 1.0:
            raise ValueError("reserved attention fractions must not exceed one")
        return self


class AttentionRequestV1(ScratchRecord):
    schema_: Literal["scratch.attention.request.v1"] = Field(
        "scratch.attention.request.v1", alias="schema"
    )
    focus_blocks: list[HashRef] | None = Field(default=None, max_length=1_000)
    focus_clusters: list[HashRef] | None = Field(default=None, max_length=1_000)
    maximum_blocks: int = Field(gt=0, le=1_000)
    maximum_cluster_guides: int = Field(ge=0, le=100)
    include_nearby: bool = True
    include_recent: bool = True
    include_loose: bool = True
    include_dormant: bool = True
    include_underexposed: bool = True
    include_exploratory: bool = True
    deterministic_seed: int

    @field_validator("focus_blocks", "focus_clusters", mode="after")
    @classmethod
    def _ordered_unique_focus(cls, value):
        if value is not None and len(value) != len(set(value)):
            raise ValueError("focus references must not contain duplicates")
        return None if value is None else FrozenList(value)

    @property
    def request_hash(self) -> str:
        return domain_hash(
            "scratch.attention.request.v1",
            self.model_dump(mode="json", by_alias=True, exclude={"schema_"}),
        )


class GuideSelectionV1(ScratchRecord):
    guide: ClusterGuideV1
    state: Literal["current", "stale"]


class AttentionPackV1(ScratchRecord):
    """Bounded view; only its receipt is persisted after actual rendering."""

    state_seq: int = Field(ge=0)
    request_hash: HashRef
    current_focus: list[HashRef] = Field(default_factory=FrozenList)
    blocks: list[ScratchBlockV1] = Field(default_factory=FrozenList, max_length=1_000)
    channel_blocks: Mapping[RetrievalChannel, list[HashRef]] = Field(
        default_factory=FrozenDict
    )
    cluster_guides: list[GuideSelectionV1] = Field(default_factory=FrozenList)
    selection_receipt: AttentionReceiptV1

    @field_validator("current_focus", "blocks", "cluster_guides", mode="after")
    @classmethod
    def _freeze_lists(cls, value):
        return FrozenList(value)

    @field_validator("channel_blocks", mode="after")
    @classmethod
    def _freeze_channels(cls, value):
        return FrozenDict({channel: FrozenList(ids) for channel, ids in value.items()})

    @model_validator(mode="after")
    def _matches_receipt(self):
        if [block.id for block in self.blocks] != list(self.selection_receipt.final_order):
            raise ValueError("pack blocks do not match the receipt final order")
        if self.state_seq != self.selection_receipt.state_seq:
            raise ValueError("pack and receipt state fences differ")
        if self.request_hash != self.selection_receipt.request_hash:
            raise ValueError("pack and receipt request hashes differ")
        return self


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


class AttentionPlanner:
    """Pure planner plus an explicit durable render commit."""

    def __init__(self, service: ScratchService, policy: AttentionPolicyV1) -> None:
        self.service = service
        self.policy = AttentionPolicyV1.model_validate(policy)

    def _validate_request(self, request: AttentionRequestV1) -> None:
        if request.maximum_blocks > self.policy.max_blocks_per_pack:
            raise ValueError("/maximum_blocks: request exceeds compiled policy")
        if request.maximum_cluster_guides > self.policy.max_guides_per_pack:
            raise ValueError("/maximum_cluster_guides: request exceeds compiled policy")

    def _focus(self, request: AttentionRequestV1) -> tuple[list[str], list[str]]:
        blocks = [self.service.get_block(item).id for item in request.focus_blocks or []]
        clusters = [
            self.service.get_cluster(item).id for item in request.focus_clusters or []
        ]
        return blocks, clusters

    def _linked(self, focus: list[str]) -> list[str]:
        found: list[str] = []
        for block_id in focus:
            for link in self.service.links_for(block_id):
                if self.service.state.link_status[link.id] == LinkState.RETIRED:
                    continue
                found.append(link.body.to if link.body.from_ == block_id else link.body.from_)
        return _dedupe(found)

    def _clustered(self, focus: list[str], clusters: list[str]) -> tuple[list[str], list[str]]:
        ordered_clusters = list(clusters)
        for block_id in focus:
            ordered_clusters.extend(sorted(self.service.state.clusters_by_block.get(block_id, set())))
        ordered_clusters = _dedupe(ordered_clusters)
        members: list[str] = []
        for cluster_id in ordered_clusters:
            members.extend(block.id for block in self.service.cluster_members(cluster_id))
        return _dedupe(members), ordered_clusters

    def _keyword(self, focus: list[str], clusters: list[str]) -> list[str]:
        pieces = [self.service.state.blocks[item].body.content for item in focus]
        pieces.extend(self.service.state.clusters[item].seed_focus for item in clusters)
        tokens: list[str] = []
        for piece in pieces:
            tokens.extend(search_tokens(piece))
        bounded_query = " ".join(_dedupe(tokens)[:64])[:4_096]
        if not bounded_query:
            return []
        limit = self.policy.per_channel_limits[RetrievalChannel.KEYWORD]
        return [block.id for block in self.service.search_phrase(bounded_query, limit)]

    def _semantic(self, focus: list[str]) -> list[str]:
        focus_set = set(focus)
        ranked: list[tuple[float, str, str]] = []
        for hit in self.service.state.similarity_hits.values():
            if hit.block_a in focus_set:
                other = hit.block_b
            elif hit.block_b in focus_set:
                other = hit.block_a
            else:
                continue
            threshold = (
                self.policy.similarity_threshold
                if self.policy.similarity_threshold is not None
                else hit.threshold_used
            )
            if hit.score >= threshold:
                ranked.append((-hit.score, other, hit.id))
        ranked.sort()
        return _dedupe([other for _, other, _ in ranked])[: self.policy.similarity_top_k]

    def _recent(self) -> list[str]:
        return [
            block.id
            for block in sorted(
                self.service.state.blocks.values(),
                key=lambda item: (-item.instance.seq, item.id),
            )
        ]

    def _guides(self, clusters: list[str], limit: int) -> list[GuideSelectionV1]:
        if limit == 0:
            return []
        selected: list[GuideSelectionV1] = []
        for cluster_id in clusters:
            guides = self.service.state.guides_by_cluster.get(cluster_id, [])
            if not guides:
                continue
            current = [
                guide for guide in guides if self.service.state.guide_state(guide) == "current"
            ]
            guide = max(current or guides, key=lambda item: (item.instance.seq, item.id))
            selected.append(
                GuideSelectionV1(
                    guide=guide,
                    state=self.service.state.guide_state(guide),
                )
            )
            if len(selected) == limit:
                break
        return selected

    def _candidates(
        self,
        request: AttentionRequestV1,
        focus: list[str],
        focus_clusters: list[str],
        *,
        pack_count: int,
    ) -> tuple[dict[RetrievalChannel, list[str]], list[str], str | None]:
        clustered, relevant_clusters = self._clustered(focus, focus_clusters)
        channels = {channel: [] for channel in _ATTENTION_CHANNELS}
        channels[RetrievalChannel.FOCUS] = focus
        if request.include_nearby:
            channels[RetrievalChannel.LINK] = self._linked(focus)
            channels[RetrievalChannel.CLUSTER] = clustered
            if self.policy.keyword_retrieval:
                channels[RetrievalChannel.KEYWORD] = self._keyword(
                    focus, relevant_clusters
                )
            if self.policy.semantic_retrieval:
                channels[RetrievalChannel.SEMANTIC] = self._semantic(focus)
        if request.include_recent:
            channels[RetrievalChannel.RECENT] = self._recent()
        query_limit = request.maximum_blocks
        if request.include_loose:
            channels[RetrievalChannel.LOOSE] = [
                item.id for item in self.service.unlinked_blocks(query_limit)
            ]
        if request.include_dormant:
            channels[RetrievalChannel.DORMANT] = [
                item.id
                for item in self.service.dormant_blocks(
                    max(0, self.service.harness._next_seq - 1),
                    self.policy.dormant_after_events,
                    query_limit,
                )
            ]
        focus_ids = set(focus)
        if request.include_underexposed:
            channels[RetrievalChannel.UNDEREXPOSED] = [
                item.id
                for item in self.service.underexposed_blocks(query_limit + len(focus))
                if item.id not in focus_ids
            ][:query_limit]
        if request.include_exploratory:
            channels[RetrievalChannel.EXPLORATORY] = [
                item.id
                for item in self.service.sample_without_semantic_relevance(
                    request.deterministic_seed, query_limit + len(focus)
                )
                if item.id not in focus_ids
            ]
            channels[RetrievalChannel.EXPLORATORY] = channels[
                RetrievalChannel.EXPLORATORY
            ][:query_limit]
        coverage = CoverageController(self.service, self.policy)
        active = coverage.active_cycle()
        cycle_id = active.cycle.id if active is not None else None
        if active is not None and coverage.coverage_due(pack_count):
            pending = coverage.next_pending()
            channels[RetrievalChannel.COVERAGE] = [pending] if pending else []
        return channels, relevant_clusters, cycle_id

    def _apply_channel_limits(
        self, candidates: dict[RetrievalChannel, list[str]]
    ) -> tuple[dict[RetrievalChannel, list[str]], dict[RetrievalChannel, list[str]]]:
        selected: dict[RetrievalChannel, list[str]] = {}
        excluded: dict[RetrievalChannel, list[str]] = {}
        for channel in _ATTENTION_CHANNELS:
            values = _dedupe(candidates[channel])
            limit = self.policy.per_channel_limits[channel]
            selected[channel] = values[:limit]
            excluded[channel] = values[limit:]
        return selected, excluded

    @staticmethod
    def _quota(maximum: int, fraction: float, available: bool) -> int:
        if not available or fraction <= 0:
            return 0
        return max(1, math.floor(maximum * fraction))

    def _final_order(
        self,
        selected: dict[RetrievalChannel, list[str]],
        maximum: int,
    ) -> tuple[list[str], list[str]]:
        reserved_channels = (
            RetrievalChannel.COVERAGE,
            RetrievalChannel.UNDEREXPOSED,
            RetrievalChannel.EXPLORATORY,
        )
        quotas = {
            RetrievalChannel.COVERAGE: int(bool(selected[RetrievalChannel.COVERAGE])),
            RetrievalChannel.UNDEREXPOSED: self._quota(
                maximum,
                self.policy.underexposed_fraction,
                bool(selected[RetrievalChannel.UNDEREXPOSED]),
            ),
            RetrievalChannel.EXPLORATORY: self._quota(
                maximum,
                self.policy.exploratory_fraction,
                bool(selected[RetrievalChannel.EXPLORATORY]),
            ),
        }
        reserved: list[str] = []
        focus_set = set(selected[RetrievalChannel.FOCUS])
        for channel in self.policy.channel_priority:
            if channel not in reserved_channels:
                continue
            for block_id in selected[channel]:
                if block_id not in focus_set and block_id not in reserved:
                    reserved.append(block_id)
                    if sum(1 for item in reserved if item in selected[channel]) >= quotas[channel]:
                        break
            if len(reserved) >= maximum:
                break
        focus_budget = max(0, maximum - len(reserved))
        final = selected[RetrievalChannel.FOCUS][:focus_budget]
        for block_id in reserved:
            if len(final) == maximum:
                break
            if block_id not in final:
                final.append(block_id)
        for channel in self.policy.channel_priority:
            for block_id in selected[channel]:
                if len(final) == maximum:
                    break
                if block_id not in final:
                    final.append(block_id)
        all_selected: list[str] = []
        for channel in self.policy.channel_priority:
            all_selected.extend(selected[channel])
        excluded_global = [item for item in _dedupe(all_selected) if item not in final]
        return final, excluded_global

    def plan(
        self,
        request: AttentionRequestV1,
        *,
        pack_count: int | None = None,
    ) -> AttentionPackV1:
        request = AttentionRequestV1.model_validate(request)
        self._validate_request(request)
        if pack_count is None:
            pack_count = len(self.service.state.attention_receipts)
        if isinstance(pack_count, bool) or not isinstance(pack_count, int) or pack_count < 0:
            raise ValueError("/pack_count: expected a non-negative integer")
        focus, focus_clusters = self._focus(request)
        candidates, relevant_clusters, cycle_id = self._candidates(
            request, focus, focus_clusters, pack_count=pack_count
        )
        selected, excluded_by_channel = self._apply_channel_limits(candidates)
        final, excluded_global = self._final_order(selected, request.maximum_blocks)
        state_seq = self.service.harness._next_seq - 1
        if state_seq < 0:
            raise ValueError("cannot build an attention pack from an empty scratch history")
        receipt = AttentionReceiptV1.create(
            state_seq=state_seq,
            request_hash=request.request_hash,
            selected_by_channel=selected,
            final_order=final,
            excluded_by_global_limit=excluded_global,
            excluded_by_channel=excluded_by_channel,
            deterministic_seed=request.deterministic_seed,
            coverage_cycle_id=cycle_id,
            instance=InstanceRef(run_id=self.service.run_id, seq=self.service.harness._next_seq),
        )
        guide_limit = min(
            request.maximum_cluster_guides, self.policy.max_guides_per_pack
        )
        return AttentionPackV1(
            state_seq=state_seq,
            request_hash=request.request_hash,
            current_focus=focus,
            blocks=[self.service.state.blocks[item] for item in final],
            channel_blocks=selected,
            cluster_guides=self._guides(relevant_clusters, guide_limit),
            selection_receipt=receipt,
        )

    def commit_render(
        self,
        pack: AttentionPackV1,
        *,
        context_ref: str | None = None,
        advance_coverage: bool = True,
    ) -> AttentionReceiptV1:
        if self.service.harness._next_seq - 1 != pack.state_seq:
            raise ValueError("attention plan is stale and must be rebuilt")
        receipt = self.service.record_attention_receipt(
            pack.selection_receipt, context_ref=context_ref
        )
        if advance_coverage:
            CoverageController(self.service, self.policy).record_receipt(receipt)
        return receipt


__all__ = [
    "AttentionPackV1",
    "AttentionPlanner",
    "AttentionPolicyV1",
    "AttentionRequestV1",
    "GuideSelectionV1",
]
