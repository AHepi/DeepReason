"""Regression: crash mid-append must not swallow the NEXT event.

Found by the MiniReason chaos battery (mini/tests/test_chaos.py): a torn
final line has no trailing newline, so a post-recovery append used to write
onto the fragment; the merged line was then dropped as "torn" on the next
read — an acknowledged, fsynced event lost after a clean recovery. The fix
truncates the never-durable tail at open."""

import pytest

from deepreason.harness import Harness
from deepreason.ontology import Provenance


def test_append_after_torn_tail_preserves_the_new_event(tmp_path):
    root = tmp_path / "run"
    h = Harness(root)
    h.create_artifact("survivor", provenance=Provenance(role="seed"))
    with open(root / "log.jsonl", "a") as f:
        f.write('{"seq": 1, "rule": "Meas')  # crash mid-append

    with pytest.warns(UserWarning, match="torn final line"):
        h2 = Harness(root)
    recovered = h2.create_artifact("post-crash", provenance=Provenance(role="seed"))

    # The post-crash event survives a fresh replay, on its own line.
    h3 = Harness(root)
    assert recovered.id in h3.state.artifacts
    assert [e.seq for e in h3.log.read()] == [0, 1]


def test_interior_corruption_still_raises(tmp_path):
    h = Harness(tmp_path / "run")
    h.create_artifact("a", provenance=Provenance(role="seed"))
    h.create_artifact("b", provenance=Provenance(role="seed"))
    path = h.log.path
    lines = path.read_text().splitlines()
    lines[0] = lines[0][: len(lines[0]) // 2]
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(Exception):
        Harness(tmp_path / "run")

def test_concurrent_harnesses_conflict_loudly(tmp_path):
    """Two live Harnesses on one root: the stale writer raises instead of
    appending a duplicate seq (single-writer by design; also found by the
    mini chaos battery)."""
    from deepreason.log.event_log import ConcurrentWriterError

    root = tmp_path / "run"
    h1, h2 = Harness(root), Harness(root)
    h1.create_artifact("from-h1", provenance=Provenance(role="seed"))
    with pytest.raises(ConcurrentWriterError):
        h2.create_artifact("from-h2", provenance=Provenance(role="seed"))
