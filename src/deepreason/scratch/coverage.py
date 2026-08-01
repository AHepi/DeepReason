"""Deterministic append-only anti-starvation coverage cycles."""

from __future__ import annotations

from typing import Protocol

from deepreason.scratch.models import AttentionReceiptV1, RetrievalChannel
from deepreason.scratch.service import ScratchService
from deepreason.scratch.state import CoverageProgress


class CoveragePolicy(Protocol):
    coverage_enabled: bool
    coverage_cadence: int


class CoverageController:
    """Coordinate coverage without making relevance or epistemic judgments."""

    def __init__(self, service: ScratchService, policy: CoveragePolicy) -> None:
        self.service = service
        self.policy = policy

    def active_cycle(self) -> CoverageProgress | None:
        return self.service.active_coverage_cycle()

    def maybe_start_cycle(self) -> CoverageProgress | None:
        if not self.policy.coverage_enabled or not self.service.state.blocks:
            return None
        active = self.active_cycle()
        if active is not None:
            return active
        cycle = self.service.start_coverage_cycle()
        return self.service.state.coverage_cycles[cycle.id]

    def coverage_due(self, pack_count: int) -> bool:
        if isinstance(pack_count, bool) or not isinstance(pack_count, int) or pack_count < 0:
            raise ValueError("/pack_count: expected a non-negative integer")
        cadence = self.policy.coverage_cadence
        if cadence <= 0:
            raise ValueError("coverage cadence must be positive")
        return (
            self.policy.coverage_enabled
            and self.active_cycle() is not None
            and (pack_count + 1) % cadence == 0
        )

    def next_pending(self) -> str | None:
        active = self.active_cycle()
        if active is None or not active.pending_block_ids:
            return None
        return active.pending_block_ids[0]

    def record_render(
        self, cycle_id: str, block_id: str, receipt: AttentionReceiptV1 | str
    ) -> None:
        """Advance only after a durable receipt proves the block was rendered."""

        receipt_ref = receipt.id if isinstance(receipt, AttentionReceiptV1) else receipt
        self.service.record_coverage_render(cycle_id, block_id, receipt_ref)
        progress = self.service.state.coverage_cycles[cycle_id]
        if not progress.pending_block_ids:
            self.service.complete_coverage_cycle(cycle_id)

    def record_receipt(self, receipt: AttentionReceiptV1) -> list[str]:
        """Advance a committed receipt and keep deterministic coverage running.

        Starting or restarting a cycle belongs to the durable-render boundary,
        not planning: previews remain pure while continued committed attention
        eventually gives every block a coverage slot.
        """

        if self.service.state.attention_receipts.get(receipt.id) != receipt:
            raise ValueError("/receipt_ref: attention receipt is not committed")

        cycle_id = receipt.coverage_cycle_id
        rendered: list[str] = []
        if cycle_id is not None:
            selected = receipt.selected_by_channel.get(RetrievalChannel.COVERAGE, [])
            rendered = [
                block_id for block_id in selected if block_id in receipt.final_order
            ]
            for block_id in rendered:
                self.record_render(cycle_id, block_id, receipt)
        self.maybe_start_cycle()
        return rendered


__all__ = ["CoverageController", "CoveragePolicy"]
