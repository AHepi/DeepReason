"""Harness-owned API for the immutable advisory scratch workspace."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from itertools import islice
from pathlib import Path

from deepreason.harness import Harness, ReadOnlyHarnessError
from deepreason.ontology.event import LLMCall
from deepreason.scratch.errors import (
    ScratchAlreadyMember,
    ScratchBlockNotFound,
    ScratchBlockPrefixAmbiguous,
    ScratchClusterNotFound,
    ScratchClusterPrefixAmbiguous,
    ScratchLimitInvalid,
    ScratchLinkNotFound,
    ScratchLinkRetired,
    ScratchNotMember,
    ScratchReadOnly,
)
from deepreason.scratch.events import ScratchAction, ScratchEventPayloadV1
from deepreason.scratch.models import (
    ClusterGuideV1,
    ClusterMembershipV1,
    ClusterSnapshotV1,
    CoverageCycleV1,
    InstanceRef,
    MembershipAction,
    ScratchBlockBodyV1,
    ScratchBlockV1,
    ScratchClusterV1,
    ScratchLinkBodyV1,
    ScratchLinkV1,
    ScratchProvenanceV1,
    SimilarityHitV1,
    AttentionReceiptV1,
    domain_hash,
)
from deepreason.scratch.search import literal_search
from deepreason.scratch.state import LinkState


_HEX = re.compile(r"^[0-9a-f]*$")
_MAX_QUERY_LIMIT = 10_000


class ScratchService:
    """One deterministic service shared by workflows, CLI, MCP, and tests.

    The service never owns a second database or cache. Its writable state is
    the Harness object/blob stores plus typed events; every query reads the
    replay materialization. A service created at a historical sequence is
    physically read-only because all underlying stores are read-only too.
    """

    def __init__(
        self,
        source: Harness | Path | str,
        *,
        upto_seq: int | None = None,
        run_id: str | None = None,
    ) -> None:
        if isinstance(source, Harness):
            if upto_seq is not None:
                raise ValueError("upto_seq cannot be combined with an existing Harness")
            self.harness = source
        elif upto_seq is None:
            self.harness = Harness(source)
        else:
            self.harness = Harness.at(source, upto_seq)
        self._run_id = self._resolve_run_id(run_id)

    @property
    def state(self):
        return self.harness.scratch_state

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def read_only(self) -> bool:
        return self.harness._read_only

    def _resolve_run_id(self, requested: str | None) -> str:
        observed: set[str] = set()
        collections = (
            self.state.blocks.values(),
            self.state.links.values(),
            self.state.clusters.values(),
            self.state.memberships.values(),
            self.state.similarity_hits.values(),
            self.state.attention_receipts.values(),
        )
        for records in collections:
            for record in records:
                instance = getattr(record, "instance", None)
                if instance is not None:
                    observed.add(instance.run_id)
        for guides in self.state.guides_by_cluster.values():
            observed.update(guide.instance.run_id for guide in guides)
        observed.update(
            progress.cycle.instance.run_id
            for progress in self.state.coverage_cycles.values()
        )
        if len(observed) > 1:
            raise ValueError("scratch history contains more than one run_id")
        if requested is not None:
            requested = InstanceRef(run_id=requested, seq=0).run_id
            if observed and requested not in observed:
                raise ValueError("requested run_id conflicts with scratch history")
            return requested
        if observed:
            return next(iter(observed))
        digest_path = self.harness.root / "run-manifest.sha256"
        if digest_path.is_file():
            digest = digest_path.read_text(encoding="utf-8").strip()
            if re.fullmatch(r"[0-9a-f]{64}", digest):
                return f"sha256:{digest}"
        return domain_hash(
            "scratch.run.root.v1", {"root": str(self.harness.root.resolve())}
        )

    def _ensure_writable(self) -> None:
        if self.read_only:
            raise ScratchReadOnly("historical scratch views cannot be mutated")

    def _instance(self) -> InstanceRef:
        return InstanceRef(run_id=self.run_id, seq=self.harness._next_seq)

    @staticmethod
    def _limit(limit: int, location: str = "/limit") -> int:
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or limit <= 0
            or limit > _MAX_QUERY_LIMIT
        ):
            raise ScratchLimitInvalid(
                f"limit must be an integer from 1 through {_MAX_QUERY_LIMIT}",
                location=location,
            )
        return limit

    @staticmethod
    def _prefix_parts(value: str) -> tuple[str, str]:
        if not isinstance(value, str):
            return "", ""
        raw = value.strip().casefold()
        suffix = raw[7:] if raw.startswith("sha256:") else raw
        if not suffix or len(suffix) > 64 or _HEX.fullmatch(suffix) is None:
            return raw, ""
        return raw, suffix

    @classmethod
    def _resolve_prefix(
        cls,
        value: str,
        candidates: Iterable[str],
        *,
        not_found,
        ambiguous,
        location: str,
    ) -> str:
        raw, suffix = cls._prefix_parts(value)
        ids = sorted(set(candidates))
        if raw in ids:
            return raw
        matches = [candidate for candidate in ids if suffix and candidate[7:].startswith(suffix)]
        if not matches:
            raise not_found(f"no object matches {value!r}", location=location)
        if len(matches) > 1:
            raise ambiguous(
                f"prefix {value!r} matches more than one object",
                location=location,
                details={"candidates": matches[:16]},
            )
        return matches[0]

    def _block_id(self, value: str, location: str = "/block_id") -> str:
        return self._resolve_prefix(
            value,
            self.state.blocks,
            not_found=ScratchBlockNotFound,
            ambiguous=ScratchBlockPrefixAmbiguous,
            location=location,
        )

    def _cluster_id(self, value: str, location: str = "/cluster_id") -> str:
        return self._resolve_prefix(
            value,
            self.state.clusters,
            not_found=ScratchClusterNotFound,
            ambiguous=ScratchClusterPrefixAmbiguous,
            location=location,
        )

    def _link(self, link_id: str) -> ScratchLinkV1:
        link = self.state.links.get(link_id)
        if link is None:
            raise ScratchLinkNotFound(
                f"scratch link {link_id!r} does not exist", location="/link_id"
            )
        return link

    @staticmethod
    def _provenance(
        value: ScratchProvenanceV1 | Mapping,
    ) -> ScratchProvenanceV1:
        return ScratchProvenanceV1.model_validate(value)

    def _record(
        self,
        action: ScratchAction,
        *,
        actor,
        inputs: list[str] | None = None,
        outputs: list[str] | None = None,
        reason_ref: str | None = None,
        context_ref: str | None = None,
        retrieval_receipt_ref: str | None = None,
        llm: LLMCall | None = None,
    ):
        payload = ScratchEventPayloadV1(
            action=action,
            actor=actor,
            inputs=inputs or [],
            outputs=outputs or [],
            reason_ref=reason_ref,
            context_ref=context_ref,
            retrieval_receipt_ref=retrieval_receipt_ref,
        )
        try:
            return self.harness.record_scratch_event(payload, llm=llm)
        except ReadOnlyHarnessError as exc:
            raise ScratchReadOnly("historical scratch views cannot be mutated") from exc

    def create_block(
        self,
        body: ScratchBlockBodyV1 | Mapping,
        provenance: ScratchProvenanceV1 | Mapping,
    ) -> ScratchBlockV1:
        self._ensure_writable()
        provenance = self._provenance(provenance)
        block = ScratchBlockV1.create(body, self._instance(), provenance)
        self.harness.objects.put("scratch-block", block)
        self._record(
            ScratchAction.BLOCK_CREATED,
            actor=provenance.actor,
            outputs=[block.id],
        )
        return block

    def revise_block(
        self,
        block_id: str,
        body: ScratchBlockBodyV1 | Mapping,
        provenance: ScratchProvenanceV1 | Mapping,
    ) -> ScratchBlockV1:
        self._ensure_writable()
        parent = self._block_id(block_id)
        provenance = self._provenance(provenance)
        block = ScratchBlockV1.create(
            body, self._instance(), provenance, revision_of=parent
        )
        self.harness.objects.put("scratch-block", block)
        self._record(
            ScratchAction.BLOCK_REVISED,
            actor=provenance.actor,
            inputs=[parent],
            outputs=[block.id],
        )
        return block

    def create_link(
        self,
        body: ScratchLinkBodyV1 | Mapping,
        provenance: ScratchProvenanceV1 | Mapping,
    ) -> ScratchLinkV1:
        self._ensure_writable()
        body = ScratchLinkBodyV1.model_validate(body)
        self._block_id(body.from_, "/body/from")
        self._block_id(body.to, "/body/to")
        if body.supersedes is not None:
            self._link(body.supersedes)
        provenance = self._provenance(provenance)
        link = ScratchLinkV1.create(body, self._instance())
        self.harness.objects.put("scratch-link", link)
        self._record(
            ScratchAction.LINK_CREATED,
            actor=provenance.actor,
            outputs=[link.id],
        )
        return link

    def mark_link_used(self, link_id: str, context_ref: str) -> ScratchLinkV1:
        self._ensure_writable()
        link = self._link(link_id)
        if self.state.link_status[link.id] == LinkState.RETIRED:
            raise ScratchLinkRetired(
                f"scratch link {link.id} is retired", location="/link_id"
            )
        self._record(
            ScratchAction.LINK_USED,
            actor="harness",
            inputs=[link.id],
            context_ref=context_ref,
        )
        return link

    def retire_link(
        self,
        link_id: str,
        reason: str,
        provenance: ScratchProvenanceV1 | Mapping,
    ) -> ScratchLinkV1:
        self._ensure_writable()
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 262_144:
            raise ValueError("/reason: expected non-blank text of at most 262144 characters")
        link = self._link(link_id)
        if self.state.link_status[link.id] == LinkState.RETIRED:
            raise ScratchLinkRetired(
                f"scratch link {link.id} is already retired", location="/link_id"
            )
        provenance = self._provenance(provenance)
        reason_ref = self.harness.blobs.put(reason.encode("utf-8"))
        self._record(
            ScratchAction.LINK_RETIRED,
            actor=provenance.actor,
            inputs=[link.id],
            reason_ref=reason_ref,
        )
        return link

    def create_cluster(
        self,
        seed_focus: str,
        provenance: ScratchProvenanceV1 | Mapping,
    ) -> ScratchClusterV1:
        self._ensure_writable()
        provenance = self._provenance(provenance)
        cluster = ScratchClusterV1.create(seed_focus, self._instance())
        self.harness.objects.put("scratch-cluster", cluster)
        self._record(
            ScratchAction.CLUSTER_CREATED,
            actor=provenance.actor,
            outputs=[cluster.id],
        )
        return cluster

    def _membership(
        self,
        action: MembershipAction,
        cluster_id: str,
        block_id: str,
        reason: str | None,
        provenance: ScratchProvenanceV1 | Mapping,
    ) -> ClusterMembershipV1:
        self._ensure_writable()
        cluster_id = self._cluster_id(cluster_id)
        block_id = self._block_id(block_id)
        is_member = block_id in self.state.current_memberships.get(cluster_id, set())
        if action == MembershipAction.ADD and is_member:
            raise ScratchAlreadyMember(
                "block is already a member of the cluster", location="/block_id"
            )
        if action == MembershipAction.REMOVE and not is_member:
            raise ScratchNotMember(
                "block is not a member of the cluster", location="/block_id"
            )
        provenance = self._provenance(provenance)
        record = ClusterMembershipV1.create(
            cluster_id,
            block_id,
            action,
            self._instance(),
            reason=reason,
        )
        self.harness.objects.put("scratch-membership", record)
        reason_ref = (
            self.harness.blobs.put(reason.encode("utf-8")) if reason is not None else None
        )
        event_action = (
            ScratchAction.CLUSTER_MEMBER_ADDED
            if action == MembershipAction.ADD
            else ScratchAction.CLUSTER_MEMBER_REMOVED
        )
        self._record(
            event_action,
            actor=provenance.actor,
            inputs=[cluster_id, block_id],
            outputs=[record.id],
            reason_ref=reason_ref,
        )
        return record

    def add_cluster_member(
        self,
        cluster_id: str,
        block_id: str,
        reason: str | None,
        provenance: ScratchProvenanceV1 | Mapping,
    ) -> ClusterMembershipV1:
        return self._membership(
            MembershipAction.ADD, cluster_id, block_id, reason, provenance
        )

    def remove_cluster_member(
        self,
        cluster_id: str,
        block_id: str,
        reason: str | None,
        provenance: ScratchProvenanceV1 | Mapping,
    ) -> ClusterMembershipV1:
        return self._membership(
            MembershipAction.REMOVE, cluster_id, block_id, reason, provenance
        )

    def store_guide(
        self, guide: ClusterGuideV1, *, llm: LLMCall | None = None
    ) -> ClusterGuideV1:
        self._ensure_writable()
        guide = ClusterGuideV1.model_validate(guide)
        cluster_id = self._cluster_id(guide.cluster_id)
        snapshot = self.cluster_snapshot(cluster_id)
        if guide.based_on_snapshot != snapshot.snapshot_hash:
            raise ValueError("/based_on_snapshot: guide is not bound to the current snapshot")
        if guide.instance != self._instance():
            raise ValueError("/instance: guide instance must use the next event sequence")
        for index, block_id in enumerate(guide.entry_points or []):
            self._block_id(block_id, f"/entry_points/{index}")
        self.harness.objects.put("scratch-cluster-snapshot", snapshot)
        self.harness.objects.put("scratch-guide", guide)
        self._record(
            ScratchAction.CLUSTER_GUIDE_WRITTEN,
            actor="llm",
            inputs=[cluster_id],
            outputs=[snapshot.id, guide.id],
            llm=llm,
        )
        return guide

    def record_similarity(
        self, hit: SimilarityHitV1, *, llm: LLMCall | None = None
    ) -> SimilarityHitV1:
        self._ensure_writable()
        hit = SimilarityHitV1.model_validate(hit)
        if hit.instance != self._instance():
            raise ValueError("/instance: similarity hit must use the next event sequence")
        self._block_id(hit.block_a, "/block_a")
        self._block_id(hit.block_b, "/block_b")
        self.harness.objects.put("scratch-similarity", hit)
        self._record(
            ScratchAction.SIMILARITY_RECORDED,
            actor="harness",
            outputs=[hit.id],
            llm=llm,
        )
        return hit

    def record_attention_receipt(
        self,
        receipt: AttentionReceiptV1,
        *,
        context_ref: str | None = None,
    ) -> AttentionReceiptV1:
        """Commit an actually rendered pack and its immutable selection receipt."""

        self._ensure_writable()
        receipt = AttentionReceiptV1.model_validate(receipt)
        if receipt.instance != self._instance():
            raise ValueError("/instance: attention receipt must use the next event sequence")
        expected_state_seq = self.harness._next_seq - 1
        if receipt.state_seq != expected_state_seq:
            raise ValueError("/state_seq: attention plan is stale")
        for channel, block_ids in receipt.selected_by_channel.items():
            for index, block_id in enumerate(block_ids):
                self._block_id(block_id, f"/selected_by_channel/{channel.value}/{index}")
        for index, block_id in enumerate(receipt.final_order):
            self._block_id(block_id, f"/final_order/{index}")
        if receipt.coverage_cycle_id is not None:
            progress = self.state.coverage_cycles.get(receipt.coverage_cycle_id)
            if progress is None or progress.completed:
                raise ValueError("/coverage_cycle_id: coverage cycle is not active")
        self.harness.objects.put("scratch-attention-receipt", receipt)
        self._record(
            ScratchAction.ATTENTION_PACK_RENDERED,
            actor="harness",
            outputs=[receipt.id],
            context_ref=context_ref,
            retrieval_receipt_ref=receipt.id,
        )
        return receipt

    def active_coverage_cycle(self):
        active = [
            progress
            for progress in self.state.coverage_cycles.values()
            if not progress.completed
        ]
        if len(active) > 1:
            raise ValueError("scratch history contains multiple active coverage cycles")
        return active[0] if active else None

    def start_coverage_cycle(self) -> CoverageCycleV1:
        self._ensure_writable()
        if self.active_coverage_cycle() is not None:
            raise ValueError("a coverage cycle is already active")
        live_ids = sorted(self.state.blocks)
        if not live_ids:
            raise ValueError("cannot start a coverage cycle without live blocks")
        cycle = CoverageCycleV1.create(live_ids, self._instance())
        self.harness.objects.put("scratch-coverage-cycle", cycle)
        self._record(
            ScratchAction.COVERAGE_CYCLE_STARTED,
            actor="harness",
            outputs=[cycle.id],
        )
        return cycle

    def record_coverage_render(
        self, cycle_id: str, block_id: str, receipt_ref: str
    ) -> None:
        self._ensure_writable()
        progress = self.state.coverage_cycles.get(cycle_id)
        if progress is None or progress.completed:
            raise ValueError("/cycle_id: coverage cycle is not active")
        block_id = self._block_id(block_id)
        if block_id not in progress.pending_block_ids:
            raise ValueError("/block_id: block is not pending in the coverage cycle")
        if receipt_ref not in self.state.attention_receipts:
            raise ValueError("/receipt_ref: attention receipt is unknown")
        self._record(
            ScratchAction.COVERAGE_BLOCK_RENDERED,
            actor="harness",
            inputs=[cycle_id, block_id],
            retrieval_receipt_ref=receipt_ref,
        )

    def complete_coverage_cycle(self, cycle_id: str) -> None:
        self._ensure_writable()
        progress = self.state.coverage_cycles.get(cycle_id)
        if progress is None or progress.completed:
            raise ValueError("/cycle_id: coverage cycle is not active")
        if progress.pending_block_ids:
            raise ValueError("/cycle_id: coverage cycle still has pending blocks")
        self._record(
            ScratchAction.COVERAGE_CYCLE_COMPLETED,
            actor="harness",
            inputs=[cycle_id],
        )

    def get_block(self, block_id_or_unique_prefix: str) -> ScratchBlockV1:
        return self.state.blocks[self._block_id(block_id_or_unique_prefix)]

    def get_blocks(self, ids: Iterable[str]) -> list[ScratchBlockV1]:
        values = list(islice(ids, _MAX_QUERY_LIMIT + 1))
        if len(values) > _MAX_QUERY_LIMIT:
            raise ScratchLimitInvalid(
                f"at most {_MAX_QUERY_LIMIT} block IDs may be requested",
                location="/ids",
            )
        return [self.get_block(value) for value in values]

    def revisions(self, block_id: str) -> list[ScratchBlockV1]:
        parent = self._block_id(block_id)
        ids = self.state.revision_children.get(parent, [])
        return sorted(
            (self.state.blocks[item] for item in ids),
            key=lambda block: (block.instance.seq, block.id),
        )

    def links_for(
        self, block_id: str, *, include_retired: bool = False
    ) -> list[ScratchLinkV1]:
        block_id = self._block_id(block_id)
        links = (
            self.state.links[item]
            for item in self.state.links_by_endpoint.get(block_id, [])
            if include_retired or self.state.link_status[item] != LinkState.RETIRED
        )
        return sorted(links, key=lambda link: (link.instance.seq, link.id))

    def get_cluster(self, cluster_id_or_unique_prefix: str) -> ScratchClusterV1:
        return self.state.clusters[self._cluster_id(cluster_id_or_unique_prefix)]

    def cluster_members(self, cluster_id: str) -> list[ScratchBlockV1]:
        cluster_id = self._cluster_id(cluster_id)
        return [
            self.state.blocks[block_id]
            for block_id in sorted(self.state.current_memberships.get(cluster_id, set()))
        ]

    def cluster_snapshot(self, cluster_id: str) -> ClusterSnapshotV1:
        cluster_id = self._cluster_id(cluster_id)
        members = sorted(self.state.current_memberships.get(cluster_id, set()))
        member_set = set(members)
        links = sorted(
            link_id
            for link_id, link in self.state.links.items()
            if self.state.link_status[link_id] != LinkState.RETIRED
            and (link.body.from_ in member_set or link.body.to in member_set)
        )
        return ClusterSnapshotV1.create(cluster_id, members, links)

    def current_guide(self, cluster_id: str) -> ClusterGuideV1 | None:
        cluster_id = self._cluster_id(cluster_id)
        snapshot_hash = self.state.current_snapshot_hash(cluster_id)
        guides = [
            guide
            for guide in self.state.guides_by_cluster.get(cluster_id, [])
            if guide.based_on_snapshot == snapshot_hash
        ]
        if not guides:
            return None
        return max(guides, key=lambda guide: (guide.instance.seq, guide.id))

    def cluster_map(
        self, limit: int, ordering: str = "created"
    ) -> list[ScratchClusterV1]:
        limit = self._limit(limit)
        clusters = list(self.state.clusters.values())
        if ordering == "created":
            clusters.sort(key=lambda cluster: (cluster.instance.seq, cluster.id))
        elif ordering == "id":
            clusters.sort(key=lambda cluster: cluster.id)
        elif ordering == "size":
            clusters.sort(
                key=lambda cluster: (
                    -len(self.state.current_memberships.get(cluster.id, set())),
                    cluster.id,
                )
            )
        else:
            raise ValueError("/ordering: expected created, id, or size")
        return clusters[:limit]

    def search_phrase(self, query: str, limit: int) -> list[ScratchBlockV1]:
        limit = self._limit(limit)
        hits = literal_search(list(self.state.blocks.values()), query, limit=limit)
        return [hit.block for hit in hits]

    def unlinked_blocks(self, limit: int) -> list[ScratchBlockV1]:
        limit = self._limit(limit)
        blocks = [
            block
            for block in self.state.blocks.values()
            if not any(
                self.state.link_status[link_id] != LinkState.RETIRED
                for link_id in self.state.links_by_endpoint.get(block.id, [])
            )
        ]
        return sorted(blocks, key=lambda block: (block.instance.seq, block.id))[:limit]

    def dormant_blocks(
        self, current_seq: int, dormant_after_events: int, limit: int
    ) -> list[ScratchBlockV1]:
        limit = self._limit(limit)
        if isinstance(current_seq, bool) or not isinstance(current_seq, int) or current_seq < 0:
            raise ValueError("/current_seq: expected a non-negative integer")
        if (
            isinstance(dormant_after_events, bool)
            or not isinstance(dormant_after_events, int)
            or dormant_after_events < 0
        ):
            raise ValueError("/dormant_after_events: expected a non-negative integer")
        ranked: list[tuple[int, str, ScratchBlockV1]] = []
        for block in self.state.blocks.values():
            visibility = self.state.visibility.get(block.id)
            last = (
                visibility.last_rendered_seq
                if visibility is not None and visibility.last_rendered_seq is not None
                else block.instance.seq
            )
            if current_seq - last >= dormant_after_events:
                ranked.append((last, block.id, block))
        ranked.sort(key=lambda item: (item[0], item[1]))
        return [block for _, _, block in ranked[:limit]]

    def underexposed_blocks(self, limit: int) -> list[ScratchBlockV1]:
        limit = self._limit(limit)
        def key(block: ScratchBlockV1):
            visibility = self.state.visibility.get(block.id)
            return (
                visibility.render_count if visibility is not None else 0,
                visibility.last_rendered_seq
                if visibility is not None and visibility.last_rendered_seq is not None
                else -1,
                block.id,
            )
        return sorted(self.state.blocks.values(), key=key)[:limit]

    def unseen_in_investigation(
        self, investigation_receipts: Iterable[str], limit: int
    ) -> list[ScratchBlockV1]:
        limit = self._limit(limit)
        seen: set[str] = set()
        receipts = list(islice(investigation_receipts, _MAX_QUERY_LIMIT + 1))
        if len(receipts) > _MAX_QUERY_LIMIT:
            raise ScratchLimitInvalid(
                f"at most {_MAX_QUERY_LIMIT} receipts may be inspected",
                location="/investigation_receipts",
            )
        for index, receipt_hash in enumerate(receipts):
            receipt = self.state.attention_receipts.get(receipt_hash)
            if receipt is None:
                raise KeyError(f"/investigation_receipts/{index}: unknown receipt")
            seen.update(receipt.final_order)
        return sorted(
            (block for block in self.state.blocks.values() if block.id not in seen),
            key=lambda block: (block.instance.seq, block.id),
        )[:limit]

    def sample_without_semantic_relevance(
        self, seed: int, limit: int
    ) -> list[ScratchBlockV1]:
        limit = self._limit(limit)
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError("/seed: expected an integer")
        return sorted(
            self.state.blocks.values(),
            key=lambda block: (
                domain_hash(
                    "scratch.exploratory.sample.v1",
                    {"seed": seed, "block_id": block.id},
                ),
                block.id,
            ),
        )[:limit]


__all__ = ["ScratchService"]
