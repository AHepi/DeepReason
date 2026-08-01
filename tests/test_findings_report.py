"""The reader-facing findings report: deterministic, honest, model-free."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

NARROW = (
    Path(__file__).resolve().parent.parent
    / "experiments"
    / "live_research_2026-07-29"
    / "narrow"
    / "runs"
    / "run-7d8723fbe8626c71db880826c244d332"
)

pytestmark = pytest.mark.skipif(
    not NARROW.is_dir(), reason="live narrow evidence root is not present"
)


def test_findings_report_translates_the_live_record(tmp_path):
    from deepreason.findings import write_findings_report

    root = tmp_path / "root"
    shutil.copytree(NARROW, root)
    target = write_findings_report(root)
    assert target is not None
    body = target.read_text(encoding="utf-8")

    # The question and real positions in plain language.
    assert "## Question" in body
    assert "idempotent operation" in body
    assert "f(f(x))=f(x)" in body
    # Rivalry is preserved, not merged.
    assert "unresolved rivals" in body
    # Evidence bookkeeping never masquerades as a position.
    assert "source-reliability" not in body
    assert "Logging handlers" not in body
    # Hedges are explicit: failed citations are NOT established.
    assert "11 claimed citation(s) failed" in body
    assert "NOT established" in body
    # The evidence trail names every fetch and the verified count.
    assert "https://docs.python.org/3/library/sqlite3.html" in body
    assert "Byte-verified citations of admitted evidence: 0." in body
    # The composed view is present and marked supersedable.
    assert "no answer is final" in body
    # The fallibilist footer.
    assert "Accepted does not mean true" in body


def test_findings_report_never_raises_on_a_bare_directory(tmp_path):
    from deepreason.findings import write_findings_report

    assert write_findings_report(tmp_path) is None


def test_citable_block_legend_shows_checker_resolvable_ids(tmp_path):
    from deepreason.capabilities.research import consumed_research_blocks
    from deepreason.evidence import render_citable_blocks
    from deepreason.harness import Harness

    root = tmp_path / "root"
    shutil.copytree(NARROW, root)
    harness = Harness(root, read_only=True)
    blocks = consumed_research_blocks(harness)
    assert blocks
    legend = render_citable_blocks(blocks, harness.blobs)
    assert legend is not None
    assert "CITABLE EVIDENCE BLOCKS" in legend
    assert f"[{blocks[0].id[:16]}]" in legend
    # Excerpts come from the fetched documents themselves.
    assert "logging" in legend.lower() or "sqlite" in legend.lower()
