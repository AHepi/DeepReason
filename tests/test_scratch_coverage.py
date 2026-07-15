"""C4 deterministic anti-starvation and crash-safe coverage tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from deepreason.scratch.coverage import CoverageController
from deepreason.scratch.models import (
    AttentionReceiptV1,
    RetrievalChannel,
    ScratchProvenanceV1,
    domain_hash,
)
from deepreason.scratch.service import ScratchService


@dataclass(frozen=True)
class _Policy:
    coverage_enabled: bool = True
    coverage_cadence: int = 2


def _user() -> ScratchProvenanceV1:
    return ScratchProvenanceV1(actor="user", origin="coverage-test")


def _receipt(
    service: ScratchService, cycle_id: str, block_id: str, seed: int
) -> AttentionReceiptV1:
    return AttentionReceiptV1.create(
        state_seq=service.harness._next_seq - 1,
        request_hash=domain_hash("test.coverage.request.v1", {"seed": seed}),
        selected_by_channel={RetrievalChannel.COVERAGE: [block_id]},
        final_order=[block_id],
        excluded_by_global_limit=[],
        excluded_by_channel={},
        deterministic_seed=seed,
        coverage_cycle_id=cycle_id,
        instance=service._instance(),
    )


def test_coverage_progress_requires_a_committed_render_receipt(tmp_path):
    service = ScratchService(tmp_path / "run")
    block = service.create_block({"content": "buried thought"}, _user())
    controller = CoverageController(service, _Policy(coverage_cadence=1))
    progress = controller.maybe_start_cycle()
    assert progress is not None and controller.next_pending() == block.id

    proposed = _receipt(service, progress.cycle.id, block.id, 1)
    with pytest.raises(ValueError, match="receipt"):
        controller.record_render(progress.cycle.id, block.id, proposed)
    assert controller.next_pending() == block.id

    service.record_attention_receipt(proposed, context_ref="coverage:test")
    assert controller.next_pending() == block.id
    controller.record_receipt(proposed)
    assert service.state.coverage_cycles[progress.cycle.id].completed


def test_coverage_rejects_receipt_that_did_not_render_pending_block(tmp_path):
    service = ScratchService(tmp_path / "run")
    pending = service.create_block({"content": "pending"}, _user())
    other = service.create_block({"content": "other"}, _user())
    controller = CoverageController(service, _Policy(coverage_cadence=1))
    progress = controller.maybe_start_cycle()
    assert progress is not None
    selected = controller.next_pending()
    assert selected is not None
    wrong = other.id if selected == pending.id else pending.id
    receipt = AttentionReceiptV1.create(
        state_seq=service.harness._next_seq - 1,
        request_hash=domain_hash("test.coverage.request.v1", {"wrong": True}),
        selected_by_channel={RetrievalChannel.COVERAGE: [wrong]},
        final_order=[wrong],
        excluded_by_global_limit=[],
        excluded_by_channel={},
        deterministic_seed=9,
        coverage_cycle_id=progress.cycle.id,
        instance=service._instance(),
    )
    service.record_attention_receipt(receipt)

    with pytest.raises(ValueError, match="did not render"):
        service.record_coverage_render(progress.cycle.id, selected, receipt.id)
    assert selected in service.active_coverage_cycle().pending_block_ids


def test_only_one_coverage_cycle_may_be_active(tmp_path):
    service = ScratchService(tmp_path / "run")
    service.create_block({"content": "one"}, _user())
    service.start_coverage_cycle()
    with pytest.raises(ValueError, match="already active"):
        service.start_coverage_cycle()


def test_new_blocks_wait_for_the_next_cycle_and_cycles_repeat(tmp_path):
    service = ScratchService(tmp_path / "run")
    first = service.create_block({"content": "first"}, _user())
    controller = CoverageController(service, _Policy(coverage_cadence=1))
    first_cycle = controller.maybe_start_cycle()
    assert first_cycle is not None
    late = service.create_block({"content": "created during cycle"}, _user())
    assert late.id not in first_cycle.pending_block_ids

    receipt = _receipt(service, first_cycle.cycle.id, first.id, 2)
    service.record_attention_receipt(receipt)
    controller.record_receipt(receipt)
    assert first_cycle.completed

    second_cycle = controller.maybe_start_cycle()
    assert second_cycle is not None
    assert second_cycle.cycle.id != first_cycle.cycle.id
    assert second_cycle.pending_block_ids == sorted([first.id, late.id])


def test_continued_packs_eventually_select_pathological_block_by_coverage(tmp_path):
    service = ScratchService(tmp_path / "run")
    focus = service.create_block({"content": "current attractor"}, _user())
    buried = service.create_block(
        {"content": "old unlinked semantically distant dormant material"}, _user()
    )
    cluster = service.create_cluster("Dormant region", _user())
    service.add_cluster_member(cluster.id, buried.id, "old local grouping", _user())
    controller = CoverageController(service, _Policy(coverage_cadence=3))
    cycle = controller.maybe_start_cycle()
    assert cycle is not None

    rendered: list[str] = []
    for pack_count in range(12):
        if not controller.coverage_due(pack_count):
            rendered.append(focus.id)
            continue
        selected = controller.next_pending()
        assert selected is not None
        receipt = _receipt(service, cycle.cycle.id, selected, pack_count)
        service.record_attention_receipt(receipt)
        controller.record_receipt(receipt)
        rendered.append(selected)
        if cycle.completed:
            break

    assert buried.id in rendered
    assert service.state.visibility[buried.id].retrieval_channels_used == [
        RetrievalChannel.COVERAGE
    ]


def test_disabled_coverage_never_starts_and_historical_checks_do_not_write(tmp_path):
    root = tmp_path / "run"
    service = ScratchService(root)
    service.create_block({"content": "one"}, _user())
    disabled = CoverageController(service, _Policy(coverage_enabled=False))
    assert disabled.maybe_start_cycle() is None
    assert not disabled.coverage_due(10)

    before = {path.relative_to(root): path.stat().st_mtime_ns for path in root.rglob("*")}
    historical = ScratchService(root, upto_seq=0)
    read_only = CoverageController(historical, _Policy())
    assert read_only.active_cycle() is None
    assert read_only.next_pending() is None
    after = {path.relative_to(root): path.stat().st_mtime_ns for path in root.rglob("*")}
    assert after == before
