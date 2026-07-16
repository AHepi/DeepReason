"""Bounded model-facing scratch rendering with opaque local handles."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Literal

from pydantic import Field, field_validator, model_validator

from deepreason.canonical import canonical_json
from deepreason.frozen import FrozenDict
from deepreason.scratch.attention import AttentionPackV1
from deepreason.scratch.contracts import SCRATCH_CONTRACT_INSTRUCTIONS
from deepreason.scratch.models import (
    AdvisoryContextV1,
    HashRef,
    ScratchRecord,
    domain_hash,
)
from deepreason.scratch.service import ScratchService
from deepreason.scratch.state import LinkState


_HANDLE = re.compile(r"^[BCLG][1-9][0-9]{0,4}$")


class ScratchRenderError(ValueError):
    def __init__(self, code: str, message: str, pointer: str = "") -> None:
        self.code = code
        self.pointer = pointer
        where = f" at {pointer}" if pointer else ""
        super().__init__(f"{code}{where}: {message}")


class ScratchRenderReceiptV1(ScratchRecord):
    schema_: Literal["scratch.render.receipt.v1"] = Field(
        "scratch.render.receipt.v1", alias="schema"
    )
    receipt_hash: HashRef
    state_seq: int = Field(ge=0)
    attention_receipt: HashRef
    block_handles: Mapping[str, HashRef] = Field(default_factory=FrozenDict)
    cluster_handles: Mapping[str, HashRef] = Field(default_factory=FrozenDict)
    link_handles: Mapping[str, HashRef] = Field(default_factory=FrozenDict)
    guide_handles: Mapping[str, HashRef] = Field(default_factory=FrozenDict)

    @field_validator(
        "block_handles", "cluster_handles", "link_handles", "guide_handles", mode="after"
    )
    @classmethod
    def _freeze_handle_maps(cls, value, info):
        prefix = {
            "block_handles": "B",
            "cluster_handles": "C",
            "link_handles": "L",
            "guide_handles": "G",
        }[info.field_name]
        if len(value) > 10_000:
            raise ValueError("render handle maps are bounded to 10000 entries")
        if len(set(value.values())) != len(value):
            raise ValueError("each canonical target must have one local handle")
        for handle in value:
            if _HANDLE.fullmatch(handle) is None or not handle.startswith(prefix):
                raise ValueError(f"invalid {prefix} local handle")
        return FrozenDict(dict(value))

    @staticmethod
    def _payload(values: Mapping) -> dict:
        return {
            key: value
            for key, value in values.items()
            if key not in {"schema", "schema_", "receipt_hash"}
        }

    @classmethod
    def create(cls, **values) -> ScratchRenderReceiptV1:
        payload = cls._payload(values)
        return cls(
            receipt_hash=domain_hash("scratch.render.receipt.v1", payload), **values
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        payload = self._payload(
            self.model_dump(mode="json", by_alias=True, exclude_none=True)
        )
        if self.receipt_hash != domain_hash("scratch.render.receipt.v1", payload):
            raise ValueError("receipt_hash does not match the render mapping")
        return self

    def resolve(self, handle: str, *, kind: str | None = None) -> str:
        if not isinstance(handle, str) or _HANDLE.fullmatch(handle) is None:
            raise ScratchRenderError(
                "SCRATCH_HANDLE_INVALID", "expected an opaque local handle", "/handle"
            )
        tables = {
            "block": self.block_handles,
            "cluster": self.cluster_handles,
            "link": self.link_handles,
            "guide": self.guide_handles,
        }
        selected = [tables[kind]] if kind in tables else list(tables.values())
        matches = [table[handle] for table in selected if handle in table]
        if len(matches) != 1:
            raise ScratchRenderError(
                "SCRATCH_HANDLE_NOT_FOUND", f"unknown local handle {handle!r}", "/handle"
            )
        return matches[0]

    def alias_map(self, kind: str = "block") -> dict[str, str]:
        table = {
            "block": self.block_handles,
            "cluster": self.cluster_handles,
            "link": self.link_handles,
            "guide": self.guide_handles,
        }.get(kind)
        if table is None:
            raise ValueError("kind must be block, cluster, link, or guide")
        return dict(table)


class RenderedScratchPackV1(ScratchRecord):
    text: str = Field(min_length=1, max_length=1_048_576)
    receipt: ScratchRenderReceiptV1
    truncated_fields: int = Field(ge=0)


class ScratchRenderer:
    def __init__(
        self,
        service: ScratchService,
        *,
        max_text_chars: int = 8_192,
        max_bytes: int = 262_144,
        max_links: int = 256,
    ) -> None:
        if max_text_chars <= 0 or max_bytes <= 0 or max_links < 0:
            raise ScratchRenderError(
                "SCRATCH_RENDER_LIMIT_INVALID", "render bounds must be positive"
            )
        self.service = service
        self.max_text_chars = max_text_chars
        self.max_bytes = max_bytes
        self.max_links = max_links

    def _clip(self, value: str | None, truncated: list[str], label: str):
        if value is None or len(value) <= self.max_text_chars:
            return value
        truncated.append(label)
        return value[: self.max_text_chars] + "\n[truncated by deterministic render bound]"

    @staticmethod
    def _handles(prefix: str, ids: list[str]) -> dict[str, str]:
        return {f"{prefix}{index}": value for index, value in enumerate(ids, 1)}

    def render_attention_pack(self, pack: AttentionPackV1) -> RenderedScratchPackV1:
        if self.service.harness._next_seq - 1 != pack.state_seq:
            raise ScratchRenderError(
                "SCRATCH_RENDER_STALE", "attention pack is not at the current state fence"
            )
        block_ids = list(pack.selection_receipt.final_order)
        if [block.id for block in pack.blocks] != block_ids:
            raise ScratchRenderError(
                "SCRATCH_RENDER_FORGED", "pack blocks do not match its receipt"
            )
        for block in pack.blocks:
            if self.service.state.blocks.get(block.id) != block:
                raise ScratchRenderError(
                    "SCRATCH_RENDER_FORGED", "pack contains a non-canonical block"
                )
        block_handles = self._handles("B", block_ids)
        block_alias = {block_id: handle for handle, block_id in block_handles.items()}

        cluster_ids: list[str] = []
        for selection in pack.cluster_guides:
            if selection.guide.cluster_id not in cluster_ids:
                cluster_ids.append(selection.guide.cluster_id)
        for block_id in block_ids:
            for cluster_id in sorted(self.service.state.clusters_by_block.get(block_id, set())):
                if cluster_id not in cluster_ids:
                    cluster_ids.append(cluster_id)
        cluster_handles = self._handles("C", cluster_ids)
        cluster_alias = {value: key for key, value in cluster_handles.items()}

        link_ids = sorted(
            link_id
            for link_id, link in self.service.state.links.items()
            if self.service.state.link_status[link_id] != LinkState.RETIRED
            and link.body.from_ in block_alias
            and link.body.to in block_alias
        )[: self.max_links]
        link_handles = self._handles("L", link_ids)
        guide_ids = [selection.guide.id for selection in pack.cluster_guides]
        guide_handles = self._handles("G", guide_ids)
        guide_alias = {value: key for key, value in guide_handles.items()}
        receipt = ScratchRenderReceiptV1.create(
            state_seq=pack.state_seq,
            attention_receipt=pack.selection_receipt.id,
            block_handles=block_handles,
            cluster_handles=cluster_handles,
            link_handles=link_handles,
            guide_handles=guide_handles,
        )

        truncated: list[str] = []
        blocks = []
        for block in pack.blocks:
            body = block.body
            blocks.append(
                {
                    "handle": block_alias[block.id],
                    "content": self._clip(body.content, truncated, f"{block.id}:content"),
                    **(
                        {"why_keep_this": self._clip(body.why_keep_this, truncated, "why")}
                        if body.why_keep_this is not None
                        else {}
                    ),
                    **(
                        {"unfinished": self._clip(body.unfinished, truncated, "unfinished")}
                        if body.unfinished is not None
                        else {}
                    ),
                    **(
                        {
                            "possible_next_move": self._clip(
                                body.possible_next_move, truncated, "possible_next_move"
                            )
                        }
                        if body.possible_next_move is not None
                        else {}
                    ),
                }
            )
        links = []
        for handle, link_id in link_handles.items():
            link = self.service.state.links[link_id]
            links.append(
                {
                    "handle": handle,
                    "from": block_alias[link.body.from_],
                    "to": block_alias[link.body.to],
                    "relation_hint": self._clip(
                        link.body.relation_hint, truncated, "relation_hint"
                    ),
                    **(
                        {"because": self._clip(link.body.because, truncated, "because")}
                        if link.body.because is not None
                        else {}
                    ),
                }
            )
        guides = []
        for selection in pack.cluster_guides:
            guide = selection.guide
            guides.append(
                {
                    "handle": guide_alias[guide.id],
                    "cluster": cluster_alias[guide.cluster_id],
                    "state": selection.state,
                    "working_focus": self._clip(
                        guide.working_focus, truncated, "working_focus"
                    ),
                    **(
                        {
                            "open_threads": [
                                self._clip(item, truncated, "open_thread")
                                for item in guide.open_threads
                            ]
                        }
                        if guide.open_threads is not None
                        else {}
                    ),
                    **(
                        {
                            "entry_points": [
                                block_alias[item]
                                for item in guide.entry_points
                                if item in block_alias
                            ]
                        }
                        if guide.entry_points is not None
                        else {}
                    ),
                    **(
                        {
                            "local_summary": self._clip(
                                guide.local_summary, truncated, "local_summary"
                            )
                        }
                        if guide.local_summary is not None
                        else {}
                    ),
                }
            )
        payload = {
            "warning": SCRATCH_CONTRACT_INSTRUCTIONS,
            "state_seq": pack.state_seq,
            "blocks": blocks,
            "links": links,
            "guides": guides,
        }
        text = "SCRATCH_ADVISORY_CONTEXT_V1\n" + json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )
        if len(text.encode("utf-8")) > self.max_bytes:
            raise ScratchRenderError(
                "SCRATCH_RENDER_LIMIT_EXCEEDED",
                "bounded render exceeds max_bytes; request a smaller attention pack",
            )
        return RenderedScratchPackV1(
            text=text, receipt=receipt, truncated_fields=len(truncated)
        )

    def render_advisory_context(
        self,
        pack: AttentionPackV1,
        context: AdvisoryContextV1,
    ) -> RenderedScratchPackV1:
        """Render only the exact repository-authored advisory context."""

        context = AdvisoryContextV1.model_validate(context)
        expected = self.service.prepare_advisory_context(
            pack,
            warning=SCRATCH_CONTRACT_INSTRUCTIONS,
        )
        if context != expected:
            raise ScratchRenderError(
                "SCRATCH_CONTEXT_FORGED",
                "advisory context does not match the planned attention pack",
            )
        return self.render_attention_pack(pack)

    def persist_receipt(self, receipt: ScratchRenderReceiptV1) -> str:
        """Explicitly persist handle provenance; pure rendering never writes."""

        data = canonical_json(receipt.model_dump(mode="json", by_alias=True))
        return self.service.harness.blobs.put(data)


__all__ = [
    "RenderedScratchPackV1",
    "ScratchRenderError",
    "ScratchRenderReceiptV1",
    "ScratchRenderer",
]
