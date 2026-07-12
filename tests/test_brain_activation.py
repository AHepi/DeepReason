from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from deepreason.brain.activation import activation_strength
from deepreason.brain.ingest import ingest_file
from deepreason.brain.models import ActivationSpec, MemoryPolicy
from deepreason.brain.store import BrainStore


def _record(tmp_path, *, half_life: float = 10.0) -> tuple[BrainStore, str]:
    brain = BrainStore.init(
        tmp_path / "brain",
        brain_id="activation-test",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    source = tmp_path / "memory.txt"
    source.write_text("bounded memory")
    record_id = ingest_file(
        brain,
        source,
        title="bounded memory",
        created_day=date(2026, 1, 1),
        activation=ActivationSpec(base_strength=1.0, half_life_days=half_life),
    )
    return brain, record_id


def test_activation_fades_deterministically_without_mutation(tmp_path) -> None:
    brain, record_id = _record(tmp_path)
    head = brain.manifest.head_seq
    assert activation_strength(brain, record_id, query_day=date(2026, 1, 11)) == pytest.approx(0.5)
    assert activation_strength(brain, record_id, query_day=date(2026, 1, 11)) == pytest.approx(0.5)
    assert brain.manifest.head_seq == head


def test_reinforce_pin_unpin_and_acceptance_rejection(tmp_path) -> None:
    brain, record_id = _record(tmp_path)
    brain.reinforce(record_id, event_day=date(2026, 1, 11))
    assert activation_strength(brain, record_id, query_day=date(2026, 1, 11)) == pytest.approx(1.5)
    brain.pin(record_id, floor=2.0, event_day=date(2026, 1, 12))
    assert activation_strength(brain, record_id, query_day=date(2027, 1, 1)) == 2.0
    brain.unpin(record_id, event_day=date(2027, 1, 2))
    assert activation_strength(brain, record_id, query_day=date(2027, 1, 2)) < 0.1
    with pytest.raises(ValueError, match="acceptance never reinforces"):
        brain.reinforce(record_id, reason="downstream_acceptance")


def test_automatic_access_reinforcement_is_capped_per_day(tmp_path) -> None:
    brain, record_id = _record(tmp_path, half_life=90.0)
    day = date(2026, 1, 1)
    brain.record_access((record_id,), event_day=day)
    brain.record_access((record_id,), event_day=day)
    brain.record_access((record_id,), event_day=day)
    policy = MemoryPolicy(automatic_access_per_day=1)
    assert activation_strength(brain, record_id, query_day=day, policy=policy) == pytest.approx(1.05)


def test_logical_sequence_mode_is_calendar_independent(tmp_path) -> None:
    brain, record_id = _record(tmp_path, half_life=10.0)
    assert activation_strength(brain, record_id, logical_seq=11) == pytest.approx(0.5)
    brain.reinforce(record_id, logical_seq=11, event_day=date(2099, 1, 1))
    assert activation_strength(brain, record_id, logical_seq=11) == pytest.approx(1.5)
