"""The record-integrity gate: a tampered record buys neither verb.

Regression (committed root `experiments/2026-08-27-pc2b-symmetric-reasoning/run`,
tranche `experiments/2026-08-31-defect-jailbreak-gate-closure`): flipping ONE
byte of the first provider endpoint recorded in `log.jsonl` used to buy the whole
operator sequence -- `amend` committed epoch 1 and `continue` then accepted
`seq=0` -- while the root's own published `REPLAY_VALIDATION.json` still read
`valid: true`.  Measured 2026-08-30 and again on this tranche's HEAD as
`proof/RED-forge_amend_ready.txt` (`jailbreak_open: True`).

The gate asks a NARROWER question than `verify_root`'s verdict: it refuses on the
SECURITY channel only.  The 2026-08-30 attempt refused on every violation and
collided with eight lifecycle tests, three of which assert roads that REPAIR an
invalid record (a staged amendment mid-recovery, a bound but unintroduced
source).  Those roads are `integrity`-channel and must stay open, which is what
`test_a_record_that_is_merely_incomplete_still_amends_and_continues` guards.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# An `amend_ready` committed root: both verbs run to completion on it, which is
# the only shape in which the whole jailbreak is visible.  A FAILED root refuses
# `continue` for a reason that has nothing to do with the record.
FORGE_ROOT = REPO / "experiments/2026-08-27-pc2b-symmetric-reasoning/run"

_ENDPOINT = b'"endpoint":"https://ollama.com/v1"'
_HOST_BYTE = len(b'"endpoint":"https://oll')


def _copy(tmp_path: Path, source: Path, arm: str) -> Path:
    # Distinct arms, because a test may want both in one temp directory and the
    # committed roots all share the basename `run`.
    copy = tmp_path / arm / source.name
    copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, copy, symlinks=True)
    return copy


def _forge_one_byte(root: Path) -> None:
    """Flip one byte of the recorded provider endpoint, preserving length.

    Same length on purpose: a size change is detectable without replaying, and
    the point is that only re-derivation sees this.
    """

    log = root / "log.jsonl"
    raw = bytearray(log.read_bytes())
    before = len(raw)
    offset = bytes(raw).index(_ENDPOINT) + _HOST_BYTE
    raw[offset] = ord("7") if chr(raw[offset]) != "7" else ord("6")
    log.write_bytes(bytes(raw))
    assert len(log.read_bytes()) == before


def _tree(root: Path) -> dict[str, int]:
    """Every path under `root` with its size — the witness that nothing landed.

    Sizes rather than mtimes: a refusal that rewrote a file with identical bytes
    would still be a write, and a refusal that created an empty marker would
    still be caught.
    """

    return {
        str(path.relative_to(root)): (path.stat().st_size if path.is_file() else -1)
        for path in sorted(root.rglob("*"))
        if not path.name.endswith(".lock")
    }


@pytest.fixture()
def forged(tmp_path: Path) -> Path:
    root = _copy(tmp_path, FORGE_ROOT, "forged")
    _forge_one_byte(root)
    return root


@pytest.fixture()
def intact(tmp_path: Path) -> Path:
    return _copy(tmp_path, FORGE_ROOT, "intact")


def _security_checks(root: Path) -> list[str]:
    from deepreason.runtime.continuation import record_security_checks

    return record_security_checks(root)


def test_the_forged_record_is_detected_only_by_re_derivation(forged: Path) -> None:
    """The stored verdict is not a fallback: it still publishes `valid: true`."""

    from deepreason.invariants import verify_root

    stored = json.loads((forged / "REPLAY_VALIDATION.json").read_text())
    assert stored["valid"] is True, "the forgery leaves the published verdict intact"

    checks = sorted({item["check"] for item in verify_root(forged)["violations"]})
    assert checks == ["attempt-route", "frozen-route"]
    assert _security_checks(forged) == ["attempt-route", "frozen-route"]


def test_continue_refuses_a_forged_record_and_names_the_checks(forged: Path) -> None:
    from deepreason.runtime.continuation import prepare_continuation

    with pytest.raises(ValueError) as raised:
        prepare_continuation(forged, cycles=1, tokens=10, check_operator_lock=False)

    message = str(raised.value)
    assert message.startswith("CONTINUE_RECORD_NOT_VERIFIED")
    # Naming the checks is the clean-stop law's "every stop assures its own
    # story": an operator must be able to read WHY without re-deriving.
    assert "attempt-route" in message and "frozen-route" in message


def test_amend_refuses_a_forged_record_and_names_the_checks(forged: Path) -> None:
    from deepreason.amendment.apply import amend_run
    from deepreason.amendment.state import AmendmentError

    with pytest.raises(AmendmentError) as raised:
        amend_run(forged, reshape_question="does a forged record buy an epoch?")

    assert raised.value.code == "AMEND_RECORD_NOT_VERIFIED"
    assert "attempt-route" in str(raised.value)
    assert "frozen-route" in str(raised.value)


def test_a_refused_verb_writes_nothing_into_the_tampered_root(forged: Path) -> None:
    """Refusal lands BEFORE the first write, so the root is byte-identical.

    A gate that refuses after archiving the stop, or after staging an epoch
    directory, has already let the tampered root grow -- and `run-stops/` and
    `run-epochs/NNN` are exactly what a second attempt would read.
    """

    from deepreason.amendment.apply import amend_run
    from deepreason.amendment.state import AmendmentError
    from deepreason.runtime.continuation import prepare_continuation

    before = _tree(forged)

    with pytest.raises(ValueError):
        prepare_continuation(forged, cycles=1, tokens=10, check_operator_lock=False)
    assert _tree(forged) == before, "continue wrote into a record it refused"

    with pytest.raises(AmendmentError):
        amend_run(forged, reshape_question="does a forged record buy an epoch?")
    assert _tree(forged) == before, "amend wrote into a record it refused"


def test_an_intact_record_still_amends_and_continues(intact: Path) -> None:
    """The other half of the gate: refusing everything is not a gate."""

    from deepreason.amendment.apply import amend_run
    from deepreason.runtime.continuation import prepare_continuation

    assert _security_checks(intact) == []

    record = amend_run(intact, reshape_question="an ordinary reshaped question")
    assert record["epoch"] == 1

    continuation = prepare_continuation(
        intact, cycles=1, tokens=10, check_operator_lock=False
    )
    assert continuation["seq"] == 0


def test_a_record_that_is_merely_incomplete_still_passes_the_gate() -> None:
    """The collision guarantee, as a test rather than as a claim.

    The 2026-08-30 attempt refused on EVERY `verify_root` violation and turned
    eight lifecycle tests red.  These committed roots are replay-INVALID today —
    and every one of their findings is `integrity` or `completion`, i.e. a record
    that is incomplete, mid-repair, or written by an older version.  The gate
    must be silent on all of them.
    """

    from deepreason.invariants import verify_root

    invalid_but_lawful = [
        REPO / "experiments/2026-08-26-pc2-rematch"
        / "retired-truncation-cap32768-run-58fb0d20488be869",
        REPO / "experiments/live_research_2026-07-29/referee/runs"
        / "run-e542c3c1fc266943e0260c5aa8d7c107",
    ]
    seen_a_violation = False
    for root in invalid_but_lawful:
        if not (root / "run-status.json").exists():  # pragma: no cover
            pytest.skip(f"committed witness absent: {root}")
        if verify_root(root)["violations"]:
            seen_a_violation = True
        assert _security_checks(root) == [], f"the gate fired on a lawful root: {root}"

    assert seen_a_violation, (
        "both witnesses verify clean, so this test no longer proves the "
        "narrowing — pick roots that are replay-invalid on the integrity channel"
    )


def test_the_gate_agrees_with_the_reports_own_channel_classification(
    forged: Path, intact: Path
) -> None:
    """`results --verify` answers from the report; the gate answers from
    `verify_root`. They must not be able to disagree.

    The equality holds by construction — `verification/report.py` classifies the
    legacy violation stream through `_legacy_channel` and stamps those findings
    `source="legacy"` — but construction can change, and a silent divergence
    would let `results` tell an operator a root is fine that `continue` refuses.
    """

    from deepreason.verification.report import verify_root_report

    for root in (intact, forged):
        report = verify_root_report(root, allow_missing_terminal=True)
        legacy_security = sorted(
            {finding.check for finding in report.security if finding.source == "legacy"}
        )
        assert _security_checks(root) == legacy_security


def test_results_verify_stops_calling_a_forged_root_amend_ready(forged: Path) -> None:
    """The reader half: the surface must not contradict the gate on one screen.

    Before this tranche `deepreason results --verify` printed `security=2` and,
    a few lines later, `ready for deepreason amend / deepreason continue: yes`.
    """

    from deepreason.application.results import results_summary

    default = results_summary(forged)["terminal"]
    assert default["record_security_violations"] == {
        "absent": True,
        "reason": "SECURITY_CHANNEL_NOT_REDERIVED",
    }, "the default path must report a typed absence, never a guess"

    verified = results_summary(forged, verify=True)["terminal"]
    assert verified["record_security_violations"] == ["attempt-route", "frozen-route"]
    assert verified["amend_ready"] is False


def test_results_verify_leaves_an_intact_root_amend_ready(intact: Path) -> None:
    from deepreason.application.results import results_summary

    verified = results_summary(intact, verify=True)["terminal"]
    assert verified["record_security_violations"] == []
    assert verified["amend_ready"] is True
