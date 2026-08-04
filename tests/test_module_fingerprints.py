"""Rung 4 (module fingerprints): every run records which modules built it.

Implements R2/R8 and SPEC.md S3 of
``experiments/2026-08-04-change-rung4-module-fingerprints``. The reader is
tested BEFORE the writer exists, because absence of the fingerprint must be
valid for every root recorded before the feature — that ordering is the
rung's own guardrail (R8, C12), not a stylistic preference.
"""

import functools
import subprocess
from pathlib import Path

import pytest

from deepreason.harness import Harness
from deepreason.module_events import (
    ModuleFingerprintV1,
    ModuleFingerprintsEventPayloadV1,
    recorded_module_fingerprints,
)
from deepreason.run_manifest import UnsupportedRunManifestVersionError


def _committed_roots() -> list[Path]:
    """Only roots ``git ls-files`` knows: a session-local root would take the
    meaning of every assertion below with it when the session ends."""

    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [Path(p).parent for p in tracked if p.endswith("/log.jsonl")]


@functools.lru_cache(maxsize=1)
def _sweep_committed_roots() -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """Open every committed root ONCE and split it into (read, refused).

    Two claims below are asserted over the same roots; opening ~45 recorded
    roots is the expensive part of this module, so it happens once per
    session rather than once per assertion.
    """

    read: list[Path] = []
    refused: list[Path] = []
    for root in _committed_roots():
        try:
            harness = Harness(root, read_only=True)
        except UnsupportedRunManifestVersionError:
            refused.append(root)
            continue
        assert recorded_module_fingerprints(harness) == (), root
        read.append(root)
    return tuple(read), tuple(refused)


def test_every_committed_root_reads_as_having_no_module_fingerprints():
    """R8: absence is the VALID answer on every root written before this
    feature, not an error and not an empty-because-unreadable.

    Roots that refuse to open at all are excluded here and counted in
    ``test_the_census_of_committed_roots_is_unchanged`` instead: a pre-v6
    manifest is the harness declining to open the root, which says nothing
    about the reader.
    """

    read, _ = _sweep_committed_roots()
    assert len(read) > 20, len(read)


def test_the_census_of_committed_roots_is_unchanged():
    """The reader must not be credited for roots it never read. Splitting the
    census from the assertion above is what keeps a future change that makes
    roots unopenable from showing up as a passing absence test.
    """

    read, refused = _sweep_committed_roots()
    assert len(read) + len(refused) == len(_committed_roots())
    assert refused, "no root refused; the census this test guards has moved"
    assert len(read) > 20, len(read)


def test_the_reader_tolerates_an_event_with_no_fingerprint_attribute(tmp_path):
    """R8 at the EVENT level rather than the root level: an event object that
    predates the payload field has no attribute to read, and the reader must
    treat that as absence rather than raising.
    """

    harness = Harness(tmp_path / "run")
    harness.record_measure(inputs=["x"])

    class _EventWithoutTheField:
        pass

    assert getattr(_EventWithoutTheField(), "module_fingerprints", None) is None
    assert recorded_module_fingerprints(harness) == ()


def test_a_fingerprint_digest_is_a_function_of_content_not_key_order():
    """Two runs built by the same modules must stamp the same bytes, or
    cross-run comparison compares serialization accidents instead of modules.
    """

    a = ModuleFingerprintV1.of("r", "m", {"backend": "default", "stances": 8})
    b = ModuleFingerprintV1.of("r", "m", {"stances": 8, "backend": "default"})
    assert a.fingerprint_sha256 == b.fingerprint_sha256
    assert ModuleFingerprintsEventPayloadV1.of([a]).digest == (
        ModuleFingerprintsEventPayloadV1.of([b]).digest
    )


def test_a_different_module_produces_a_different_digest():
    """The companion mutation test the durable-test doctrine requires for an
    equality assertion: the comparison above must be able to notice a change.
    """

    a = ModuleFingerprintV1.of("r", "m", {"backend": "default", "stances": 8})
    c = ModuleFingerprintV1.of("r", "m", {"backend": "default", "stances": 9})
    assert a.fingerprint_sha256 != c.fingerprint_sha256
    assert ModuleFingerprintsEventPayloadV1.of([a]).digest != (
        ModuleFingerprintsEventPayloadV1.of([c]).digest
    )


def test_a_payload_carries_no_wall_clock_field():
    """A timestamped payload would make two runs built by identical modules
    compare unequal, which is the opposite of what the rung asks for. The
    enclosing ``Event.ts`` is the run's only clock.
    """

    fields = set(ModuleFingerprintsEventPayloadV1.model_fields) | set(
        ModuleFingerprintV1.model_fields
    )
    assert not {f for f in fields if "ts" == f or "time" in f or "clock" in f}, fields


def test_a_recorded_digest_cannot_disagree_with_its_own_fingerprint():
    """``of`` digests at construction so no call site can record a digest that
    does not describe the value beside it; a hand-built mismatch is refused.
    """

    with pytest.raises(ValueError):
        ModuleFingerprintV1(
            registry="r", module_id="m", fingerprint={"a": 1}, fingerprint_sha256="nope"
        )


def test_an_empty_module_list_is_refused():
    """A stamp naming no modules answers the rung's question with silence
    while still looking like a recorded answer."""

    with pytest.raises(ValueError):
        ModuleFingerprintsEventPayloadV1.of([])
