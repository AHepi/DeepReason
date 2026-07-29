"""Replay regression pinned on the first live in-run research root.

run-0c3ce902 (glm-5.2, 2026-07-29, allowlist en.wikipedia.org +
www.rfc-editor.org) is the first live run in which the model proposed
directed fetches on the v6 conjecture wire. Its reasoning crashed
mid-flight on a since-fixed simulation-only assumption, but its research
capability record is complete: three proposals, granted and dispatched
contained fetches, receipts, packages, and consumptions. This test pins
that the replay verifier and the Tranche-A audit writer understand such
a root forever.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = (
    Path(__file__).resolve().parent.parent
    / "experiments"
    / "live_research_2026-07-29"
    / "wide"
    / "runs"
    / "run-0c3ce902cc5bca75a709b04e2473d100"
)

pytestmark = pytest.mark.skipif(
    not ROOT.is_dir(), reason="live research evidence root is not present"
)


def test_live_research_root_replays_valid_and_audits_cleanly(tmp_path):
    import shutil

    from deepreason.capabilities.audit import write_tranche_a_audits
    from deepreason.capabilities.models import (
        ResearchConsumptionV1,
        ResearchExecutionReceiptV1,
        ResearchFetchProposalV1,
    )
    from deepreason.harness import Harness
    from deepreason.invariants import verify_root

    root = tmp_path / "root"
    shutil.copytree(ROOT, root)

    validation = verify_root(root)
    assert validation["violations"] == []

    harness = Harness(root, read_only=True)
    state = harness.capability_state
    proposals = [
        proposal
        for proposal in state.proposals.values()
        if isinstance(proposal, ResearchFetchProposalV1)
    ]
    assert len(proposals) == 3
    receipts = [
        receipt
        for receipt in state.receipts.values()
        if isinstance(receipt, ResearchExecutionReceiptV1)
    ]
    assert receipts
    outcomes = {receipt.outcome for receipt in receipts}
    assert "fetched" in outcomes
    # One live response exceeded the frozen 4 MiB per-response ceiling and
    # was refused by containment: a typed nothing_fetched receipt whose
    # attempt spent its request without minting content.
    assert "nothing_fetched" in outcomes
    assert any(
        isinstance(consumption, ResearchConsumptionV1)
        for consumption in state.consumptions.values()
    )

    written = write_tranche_a_audits(root)
    assert "REPLAY_VALIDATION.json" in written
    replay = json.loads((root / "REPLAY_VALIDATION.json").read_text())
    assert replay["valid"] is True
    tokens = json.loads((root / "TOKEN_ACCOUNTING.json").read_text())
    assert tokens["research_requests"] == 3
    assert tokens["research_fetch_attempts"] >= 3
