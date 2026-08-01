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

from pathlib import Path

from deepreason.harness import Harness
from deepreason.verification.report import verify_root_report
from tests.test_v6_engaged_repair_verification import _engaged_root


def test_a_root_with_no_attacks_reproduces_the_live_shape(tmp_path):
    """Fidelity guard: without this the two tests below prove nothing."""

    harness = Harness(_engaged_root(tmp_path / "shape"), read_only=True)

    assert harness.state.artifacts
    assert len(harness.state.att) == 0
    assert len(harness.state.carries) == 0
    assert len(harness.warrants) == 0


#: Committed, git-tracked roots. The positive ran criticism 11 times and
#: produced no attack; the negative ran it 28 times and produced one.
_BLIND_ROOT = Path("experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847")
_SIGHTED_ROOT = Path(
    "experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf"
)


def test_a_run_whose_criticism_attacked_nothing_is_flagged():
    harness = Harness(_BLIND_ROOT, read_only=True)
    assert len(harness.state.att) == 0, "fixture root gained attacks"

    report = verify_root_report(_BLIND_ROOT)

    blind = [f for f in report.epistemic if f.check == "adjudication-blindness"]
    assert len(blind) == 1, report.epistemic
    assert report.epistemic_checks_passed is False


def test_a_run_that_did_attack_is_not_flagged():
    """The predicate is criticism-ran-and-attacked-nothing, not zero attacks.
    Without this, a flag that fires on everything would look like a fix.
    """

    harness = Harness(_SIGHTED_ROOT, read_only=True)
    assert len(harness.state.att) == 1, "control root lost its attack"

    report = verify_root_report(_SIGHTED_ROOT)

    assert not [f for f in report.epistemic if f.check == "adjudication-blindness"]


def test_a_run_with_no_criticism_is_not_flagged(tmp_path):
    """A fixture that never ran criticism never had the opportunity to attack.
    Flagging it would be noise, and 22 test modules assert such roots verify
    with an empty violation list.
    """

    root = _engaged_root(tmp_path / "nocrit")
    assert not any(e.rule.value == "Crit" for e in Harness(root, read_only=True).log.read())

    report = verify_root_report(root)

    assert not [f for f in report.epistemic if f.check == "adjudication-blindness"]
