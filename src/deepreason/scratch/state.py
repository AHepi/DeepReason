"""Replay-only materialized scratchpad state.

This module contains no persistence and no calls to an embedder or model.
Every index is rebuilt from immutable ObjectStore records named by typed
scratch events.  It is deliberately separate from ``EpistemicState``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
from collections import Counter

from deepreason.ontology.event import Event
from deepreason.scratch.events import ScratchAction
from deepreason.scratch.models import (
    AdvisoryContextV1,
    AttentionReceiptV1,
    ClusterGuideV1,
    ClusterMembershipV1,
    ClusterSnapshotV1,
    CoverageCycleV1,
    InstanceRef,
    RetrievalChannel,
    ScratchBlockV1,
    ScratchClusterV1,
    ScratchLinkV1,
    SimilarityHitV1,
    VisibilityRecordV1,
)
from deepreason.storage.objects import ObjectStore


class LinkState(str, Enum):
    SUGGESTED = "suggested"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


@dataclass
class CoverageProgress:
    cycle: CoverageCycleV1
    pending_block_ids: list[str]
    rendered_block_ids: list[str]
    completed: bool

    @classmethod
    def from_cycle(cls, cycle: CoverageCycleV1) -> CoverageProgress:
        return cls(
            cycle=cycle,
            pending_block_ids=list(cycle.pending_block_ids),
            rendered_block_ids=list(cycle.rendered_block_ids),
            completed=cycle.state.value == "completed",
        )


@dataclass
class ScratchState:
    blocks: dict[str, ScratchBlockV1] = field(default_factory=dict)
    block_instances_by_body_hash: dict[str, list[str]] = field(default_factory=dict)
    revision_children: dict[str, list[str]] = field(default_factory=dict)
    links: dict[str, ScratchLinkV1] = field(default_factory=dict)
    link_status: dict[str, LinkState] = field(default_factory=dict)
    links_by_endpoint: dict[str, list[str]] = field(default_factory=dict)
    _used_links: set[str] = field(default_factory=set, repr=False)
    _retired_links: set[str] = field(default_factory=set, repr=False)
    clusters: dict[str, ScratchClusterV1] = field(default_factory=dict)
    memberships: dict[str, ClusterMembershipV1] = field(default_factory=dict)
    current_memberships: dict[str, set[str]] = field(default_factory=dict)
    clusters_by_block: dict[str, set[str]] = field(default_factory=dict)
    snapshots: dict[str, ClusterSnapshotV1] = field(default_factory=dict)
    guides_by_cluster: dict[str, list[ClusterGuideV1]] = field(default_factory=dict)
    guides_by_snapshot: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    similarity_hits: dict[str, SimilarityHitV1] = field(default_factory=dict)
    similarity_by_block: dict[str, list[str]] = field(default_factory=dict)
    similarity_by_pair: dict[tuple[str, str, str, str], list[str]] = field(
        default_factory=dict
    )
    attention_receipts: dict[str, AttentionReceiptV1] = field(default_factory=dict)
    advisory_contexts: dict[str, AdvisoryContextV1] = field(default_factory=dict)
    visibility: dict[str, VisibilityRecordV1] = field(default_factory=dict)
    coverage_cycles: dict[str, CoverageProgress] = field(default_factory=dict)

    @staticmethod
    def _load(objects: ObjectStore, oid: str, schema: str):
        found_schema, obj = objects.get(oid, schema=schema)
        if found_schema != schema:
            raise ValueError(f"scratch event output {oid} is {found_schema}, expected {schema}")
        return obj

    @staticmethod
    def _append_unique(index: dict[str, list[str]], key: str, value: str) -> None:
        values = index.setdefault(key, [])
        if value not in values:
            values.append(value)

    def _register_block(self, block: ScratchBlockV1) -> None:
        if block.revision_of is not None and block.revision_of not in self.blocks:
            raise ValueError(f"scratch revision parent is unknown: {block.revision_of}")
        self.blocks[block.id] = block
        self._append_unique(self.block_instances_by_body_hash, block.body_hash, block.id)
        if block.revision_of is not None:
            self._append_unique(self.revision_children, block.revision_of, block.id)

    def _register_link(self, link: ScratchLinkV1) -> None:
        for block_id in (link.body.from_, link.body.to):
            if block_id not in self.blocks:
                raise ValueError(f"scratch link endpoint is unknown: {block_id}")
        if link.body.supersedes is not None and link.body.supersedes not in self.links:
            raise ValueError(f"superseded scratch link is unknown: {link.body.supersedes}")
        self.links[link.id] = link
        self._append_unique(self.links_by_endpoint, link.body.from_, link.id)
        self._append_unique(self.links_by_endpoint, link.body.to, link.id)
        self._derive_link_status()

    def _derive_link_status(self) -> None:
        superseded = {
            link.body.supersedes
            for link in self.links.values()
            if link.id not in self._retired_links and link.body.supersedes is not None
        }
        self.link_status = {}
        for link_id in self.links:
            if link_id in self._retired_links:
                state = LinkState.RETIRED
            elif link_id in superseded:
                state = LinkState.SUPERSEDED
            elif link_id in self._used_links:
                state = LinkState.ACTIVE
            else:
                state = LinkState.SUGGESTED
            self.link_status[link_id] = state

    def _register_membership(self, record: ClusterMembershipV1) -> None:
        if record.cluster_id not in self.clusters:
            raise ValueError(f"scratch membership cluster is unknown: {record.cluster_id}")
        if record.block_id not in self.blocks:
            raise ValueError(f"scratch membership block is unknown: {record.block_id}")
        self.memberships[record.id] = record
        members = self.current_memberships.setdefault(record.cluster_id, set())
        clusters = self.clusters_by_block.setdefault(record.block_id, set())
        if record.action.value == "add":
            members.add(record.block_id)
            clusters.add(record.cluster_id)
        else:
            members.discard(record.block_id)
            clusters.discard(record.cluster_id)

    def _register_similarity(self, hit: SimilarityHitV1) -> None:
        for block_id, body_hash in (
            (hit.block_a, hit.input_body_hash_a),
            (hit.block_b, hit.input_body_hash_b),
        ):
            block = self.blocks.get(block_id)
            if block is None:
                raise ValueError(f"similarity block is unknown: {block_id}")
            if block.body_hash != body_hash:
                raise ValueError(f"similarity body hash does not match block {block_id}")
        self.similarity_hits[hit.id] = hit
        self._append_unique(self.similarity_by_block, hit.block_a, hit.id)
        self._append_unique(self.similarity_by_block, hit.block_b, hit.id)
        pair = (hit.block_a, hit.block_b, hit.embedder, hit.embedder_version)
        values = self.similarity_by_pair.setdefault(pair, [])
        if hit.id not in values:
            values.append(hit.id)

    def _render_attention(self, receipt: AttentionReceiptV1, event_seq: int) -> None:
        if receipt.instance.seq != event_seq:
            raise ValueError("attention receipt instance does not match event sequence")
        if receipt.state_seq != event_seq - 1:
            raise ValueError("attention receipt does not name the preceding state fence")
        selected: set[str] = set()
        for channel, block_ids in receipt.selected_by_channel.items():
            if len(block_ids) != len(set(block_ids)):
                raise ValueError(f"attention channel {channel.value} contains duplicates")
            selected.update(block_ids)
        if len(receipt.final_order) != len(set(receipt.final_order)):
            raise ValueError("attention final order contains duplicate blocks")
        if not set(receipt.final_order).issubset(selected):
            raise ValueError("attention final order contains an unselected block")
        referenced = set(receipt.final_order) | selected | set(
            receipt.excluded_by_global_limit
        )
        for block_ids in receipt.excluded_by_channel.values():
            referenced.update(block_ids)
        unknown = sorted(referenced - self.blocks.keys())
        if unknown:
            raise ValueError(f"attention receipt references unknown block {unknown[0]}")
        if set(receipt.final_order) & set(receipt.excluded_by_global_limit):
            raise ValueError("globally excluded attention blocks cannot be rendered")
        if (
            receipt.selected_by_channel.get(RetrievalChannel.COVERAGE)
            and receipt.coverage_cycle_id is None
        ):
            raise ValueError("coverage attention requires a coverage cycle")
        self.attention_receipts[receipt.receipt_hash] = receipt
        rendered = set(receipt.final_order)
        for block_id in receipt.final_order:
            block = self.blocks.get(block_id)
            if block is None:  # guarded above; retain a defensive replay fence
                raise ValueError(f"attention receipt references unknown block {block_id}")
            channels = sorted(
                channel.value
                for channel, ids in receipt.selected_by_channel.items()
                if block_id in ids and block_id in rendered
            )
            previous = self.visibility.get(block_id)
            contexts = list(previous.contexts_rendered_into) if previous else []
            if receipt.receipt_hash not in contexts:
                contexts.append(receipt.receipt_hash)
            used = {channel.value for channel in previous.retrieval_channels_used} if previous else set()
            used.update(channels)
            self.visibility[block_id] = VisibilityRecordV1.create(
                block_id=block_id,
                first_created_seq=block.instance.seq,
                render_count=(previous.render_count if previous else 0) + 1,
                last_rendered_seq=event_seq,
                retrieval_channels_used=sorted(used),
                contexts_rendered_into=contexts,
                instance=InstanceRef(run_id=receipt.instance.run_id, seq=event_seq),
            )

    def _load_outputs(self, event: Event, objects: ObjectStore) -> None:
        for oid in event.outputs:
            schema, obj = objects.get(oid)
            if schema == "scratch-block":
                self._register_block(obj)
            elif schema == "scratch-link":
                self._register_link(obj)
            elif schema == "scratch-cluster":
                self.clusters[obj.id] = obj
                self.current_memberships.setdefault(obj.id, set())
            elif schema == "scratch-membership":
                self._register_membership(obj)
            elif schema == "scratch-cluster-snapshot":
                self.snapshots[obj.snapshot_hash] = obj
            elif schema == "scratch-guide":
                if obj.cluster_id not in self.clusters:
                    raise ValueError(f"guide cluster is unknown: {obj.cluster_id}")
                if obj.based_on_snapshot not in self.snapshots:
                    raise ValueError(
                        f"guide snapshot is unknown: {obj.based_on_snapshot}"
                    )
                if any(block_id not in self.blocks for block_id in (obj.entry_points or [])):
                    raise ValueError("guide contains an unknown entry-point block")
                self.guides_by_cluster.setdefault(obj.cluster_id, []).append(obj)
                key = (obj.cluster_id, obj.based_on_snapshot)
                values = self.guides_by_snapshot.setdefault(key, [])
                if obj.id not in values:
                    values.append(obj.id)
            elif schema == "scratch-similarity":
                self._register_similarity(obj)
            elif schema == "scratch-attention-receipt":
                self.attention_receipts[obj.receipt_hash] = obj
            elif schema == "scratch-coverage-cycle":
                if any(not progress.completed for progress in self.coverage_cycles.values()):
                    raise ValueError("a coverage cycle is already active")
                self.coverage_cycles[obj.cycle_id] = CoverageProgress.from_cycle(obj)
            elif schema == "scratch-advisory-context":
                if obj.instance.seq != event.seq:
                    raise ValueError(
                        "advisory context instance does not match event sequence"
                    )
                if obj.retrieval_receipt not in self.attention_receipts:
                    raise ValueError(
                        "advisory context references an unknown attention receipt"
                    )
                if any(self.blocks.get(block.id) != block for block in obj.blocks):
                    raise ValueError("advisory context contains a non-canonical block")
                if any(self.links.get(link.id) != link for link in obj.links or ()):
                    raise ValueError("advisory context contains a non-canonical link")
                known_guides = {
                    guide.id: guide
                    for guides in self.guides_by_cluster.values()
                    for guide in guides
                }
                if any(
                    known_guides.get(guide.id) != guide for guide in obj.guides or ()
                ):
                    raise ValueError("advisory context contains a non-canonical guide")
                self.advisory_contexts[obj.id] = obj
            elif schema == "scratch-visibility":
                # Visibility is derived from attention events and does not
                # change navigation indexes when read as an immutable object.
                continue
            else:
                raise ValueError(f"scratch event names non-scratch output schema {schema}")

    @staticmethod
    def _expected_output_schemas(action: ScratchAction) -> Counter:
        expected = {
            ScratchAction.BLOCK_CREATED: ["scratch-block"],
            ScratchAction.BLOCK_REVISED: ["scratch-block"],
            ScratchAction.LINK_CREATED: ["scratch-link"],
            ScratchAction.LINK_USED: [],
            ScratchAction.LINK_RETIRED: [],
            ScratchAction.CLUSTER_CREATED: ["scratch-cluster"],
            ScratchAction.CLUSTER_MEMBER_ADDED: ["scratch-membership"],
            ScratchAction.CLUSTER_MEMBER_REMOVED: ["scratch-membership"],
            ScratchAction.CLUSTER_GUIDE_WRITTEN: [
                "scratch-cluster-snapshot",
                "scratch-guide",
            ],
            ScratchAction.SIMILARITY_RECORDED: ["scratch-similarity"],
            ScratchAction.ATTENTION_PACK_RENDERED: ["scratch-attention-receipt"],
            ScratchAction.ADVISORY_CONTEXT_CREATED: ["scratch-advisory-context"],
            ScratchAction.COVERAGE_CYCLE_STARTED: ["scratch-coverage-cycle"],
            ScratchAction.COVERAGE_BLOCK_RENDERED: [],
            ScratchAction.COVERAGE_CYCLE_COMPLETED: [],
        }
        return Counter(expected[action])

    def apply(self, event: Event, objects: ObjectStore) -> None:
        payload = event.scratch
        if payload is None:
            return
        actual_schemas = Counter(objects.get(oid)[0] for oid in event.outputs)
        expected_schemas = self._expected_output_schemas(payload.action)
        if actual_schemas != expected_schemas:
            raise ValueError(
                f"scratch action {payload.action.value} outputs {dict(actual_schemas)}, "
                f"expected {dict(expected_schemas)}"
            )
        if payload.action in {ScratchAction.BLOCK_CREATED, ScratchAction.BLOCK_REVISED}:
            block = objects.get(event.outputs[0], schema="scratch-block")[1]
            is_revision = block.revision_of is not None
            if is_revision != (payload.action == ScratchAction.BLOCK_REVISED):
                raise ValueError("scratch block action does not match revision_of")
            if is_revision and block.revision_of != payload.inputs[0]:
                raise ValueError("scratch revision input does not match revision_of")
        if payload.action in {
            ScratchAction.CLUSTER_MEMBER_ADDED,
            ScratchAction.CLUSTER_MEMBER_REMOVED,
        }:
            record = objects.get(event.outputs[0], schema="scratch-membership")[1]
            expected_action = (
                "add"
                if payload.action == ScratchAction.CLUSTER_MEMBER_ADDED
                else "remove"
            )
            if record.action.value != expected_action:
                raise ValueError("scratch membership action does not match event action")
            if [record.cluster_id, record.block_id] != list(payload.inputs):
                raise ValueError("scratch membership inputs do not match record")
        if payload.action == ScratchAction.ADVISORY_CONTEXT_CREATED:
            context = objects.get(
                event.outputs[0], schema="scratch-advisory-context"
            )[1]
            if context.retrieval_receipt != payload.inputs[0]:
                raise ValueError(
                    "advisory context input does not match its retrieval receipt"
                )
            receipt = self.attention_receipts.get(context.retrieval_receipt)
            if receipt is None or [block.id for block in context.blocks] != list(
                receipt.final_order
            ):
                raise ValueError(
                    "advisory context blocks do not match its attention receipt"
                )
            selected = set(receipt.final_order)
            for link in context.links or ():
                if (
                    link.body.from_ not in selected
                    or link.body.to not in selected
                ):
                    raise ValueError(
                        "advisory context links must connect selected blocks"
                    )
                if self.link_status.get(link.id) == LinkState.RETIRED:
                    raise ValueError("advisory context cannot include a retired link")
        self._load_outputs(event, objects)
        action = payload.action
        if action == ScratchAction.LINK_USED:
            if payload.inputs[0] not in self.links:
                raise ValueError(f"unknown scratch link {payload.inputs[0]}")
            self._used_links.add(payload.inputs[0])
            self._derive_link_status()
        elif action == ScratchAction.LINK_RETIRED:
            if payload.inputs[0] not in self.links:
                raise ValueError(f"unknown scratch link {payload.inputs[0]}")
            self._retired_links.add(payload.inputs[0])
            self._derive_link_status()
        elif action == ScratchAction.ATTENTION_PACK_RENDERED:
            receipt = self._load(objects, payload.retrieval_receipt_ref, "scratch-attention-receipt")
            self._render_attention(receipt, event.seq)
        elif action == ScratchAction.COVERAGE_BLOCK_RENDERED:
            cycle_id, block_id = payload.inputs
            progress = self.coverage_cycles.get(cycle_id)
            if progress is None:
                raise ValueError(f"unknown coverage cycle {cycle_id}")
            if progress.completed:
                raise ValueError(f"coverage cycle {cycle_id} is already completed")
            receipt = self.attention_receipts.get(payload.retrieval_receipt_ref)
            if receipt is None:
                raise ValueError("coverage progress references an unknown attention receipt")
            coverage_ids = receipt.selected_by_channel.get(RetrievalChannel.COVERAGE, [])
            if receipt.coverage_cycle_id != cycle_id:
                raise ValueError("coverage receipt names a different coverage cycle")
            if block_id not in coverage_ids or block_id not in receipt.final_order:
                raise ValueError("coverage receipt did not render the pending block")
            if block_id not in progress.pending_block_ids:
                raise ValueError(f"coverage block {block_id} is not pending")
            progress.pending_block_ids.remove(block_id)
            progress.rendered_block_ids.append(block_id)
            progress.rendered_block_ids.sort()
        elif action == ScratchAction.COVERAGE_CYCLE_COMPLETED:
            progress = self.coverage_cycles.get(payload.inputs[0])
            if progress is None:
                raise ValueError(f"unknown coverage cycle {payload.inputs[0]}")
            if progress.completed:
                raise ValueError("coverage cycle is already completed")
            if progress.pending_block_ids:
                raise ValueError("coverage cycle cannot complete with pending blocks")
            progress.completed = True

    def current_snapshot_hash(self, cluster_id: str) -> str:
        members = sorted(self.current_memberships.get(cluster_id, set()))
        member_set = set(members)
        links = sorted(
            link_id
            for link_id, link in self.links.items()
            if self.link_status.get(link_id) != LinkState.RETIRED
            and (link.body.from_ in member_set or link.body.to in member_set)
        )
        return ClusterSnapshotV1.compute_hash(cluster_id, members, links)

    def guide_state(self, guide: ClusterGuideV1) -> str:
        return (
            "current"
            if guide.based_on_snapshot == self.current_snapshot_hash(guide.cluster_id)
            else "stale"
        )


def rebuild_scratch_state(objects: ObjectStore, events: Iterable[Event]) -> ScratchState:
    state = ScratchState()
    for event in events:
        state.apply(event, objects)
    return state
