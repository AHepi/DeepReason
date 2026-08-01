"""A run that never attacked anything must not be reported epistemically clean.

Regression (jolt run-b4d6dfda0c20676a864a051fbc97bda4): the run completed with
``len(state.att) == 0``, ``len(state.carries) == 0`` and zero warrants across
851 events, all 72 artifacts ACCEPTED, and ``run-result.json`` recorded
``epistemic_checks_passed: true`` with ``finding_counts.epistemic: 0``.

`docs/harness-spec-v1.3.md` section 11.3 names that state a pathology --
"validity-node attack rate (if no test is ever attacked, D3 has died in
practice while remaining true on paper)" -- and makes a near-zero
validity-attack rate one of the four conditions whose conjunction is an
adjudication ritual.

Two independent things are wrong, and the second is why fixing the first alone
would change nothing observable:

1. At ``n_attacks == 0`` the ritual condition cannot fire. Two of the four
   conditions are gated behind ``MIN_ATTACKS_FOR_RITUAL`` and
   ``attack_target_entropy`` is ``None`` with no attacks, so at most one of
   four can be true and ``adjudication_ritual`` needs two. Total blindness is
   the case the detector is least able to see.
2. Verification calls ``raw_flags`` only to assert it does not raise and
   DISCARDS the result (``invariants.py``), and the epistemic channel is fed
   only from ``_EPISTEMIC_CHECKS`` (``verification/report.py``), which no
   detection flag can join. So no flag reaches any finding at any threshold.

The live root is gitignored, so these build the state offline from the engaged
repair fixture, which is a real v6 text root with artifacts and no attacks.
"""

from __future__ import annotations

import deepreason.capture.detection as detection
from deepreason.capture.detection import raw_flags
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.embedder import HashingEmbedder
from deepreason.verification.report import verify_root_report
from tests.test_v6_engaged_repair_verification import _engaged_root


def test_a_root_with_no_attacks_reproduces_the_live_shape(tmp_path):
    """Fidelity guard: without this the two tests below prove nothing."""

    harness = Harness(_engaged_root(tmp_path / "shape"), read_only=True)

    assert harness.state.artifacts
    assert len(harness.state.att) == 0
    assert len(harness.state.carries) == 0
    assert len(harness.warrants) == 0


def test_the_ritual_flag_cannot_fire_when_nothing_was_ever_attacked(tmp_path):
    root = _engaged_root(tmp_path / "flag")
    harness = Harness(root, read_only=True)

    flags = raw_flags(harness, HashingEmbedder(), Config())

    assert flags["adjudication_ritual"] is True, (
        "a run with zero attacks must raise the adjudication-ritual flag; "
        f"flags were {flags}"
    )


def test_detection_flags_reach_the_epistemic_channel(tmp_path, monkeypatch):
    """The load-bearing half. If a FORCED flag still produces no finding, then
    the thresholds are not the barrier and no threshold change can fix this.
    """

    root = _engaged_root(tmp_path / "channel")
    real = detection.raw_flags
    monkeypatch.setattr(
        detection,
        "raw_flags",
        lambda *args, **kwargs: {key: True for key in real(*args, **kwargs)},
    )

    report = verify_root_report(root)

    assert report.epistemic, (
        "every detection flag was forced True and the epistemic channel is "
        "still empty: verification discards what the detector returns"
    )
