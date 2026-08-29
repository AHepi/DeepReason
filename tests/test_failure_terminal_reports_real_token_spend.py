"""A run that failed reports the tokens it actually spent, not a zero.

Regression (parked P3, amended by P3-A; audit 2026-08-28 finding F-E):
`deepreason results` printed `tokens spent vs budget: 0 / 600000` for a run
whose own log carried 580 016 tokens over 52 provider calls. Not a corner
case — `docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` organ 10 measured 18 of 54
committed roots reporting `token_spend: 0` while the log and the accounting
agree on a real figure, one of them a 702 789-token run. The spend figure is
what an operator uses to decide whether a configuration is affordable, and it
read zero precisely on the runs that overspent.

P3's own prompt sent the fixer to `application/results.py` and said "the fix
belongs in the READER, not in the record"; **P3-A corrects that**, and the
correction is what these tests encode. The three failure emits in
`application/text_runs.py` passed `token_limit` and NO `token_spend`, and
`runtime/progress.py`'s `token_spend: int = Field(default=0, ge=0)` turns that
omission into a positive assertion of zero — so the key is PRESENT in
`run-status.json` and the reader's absence sentinel can never fire on it. The
reader was behaving correctly on a status file that stated a false fact.

Both halves are regressed here, and which is which:
  (a) WRITER — stops NEW roots asserting a zero they never measured.
  (b) READER — recovers the truth for roots ALREADY committed, by walking
      their own log. Those roots are evidence and are never edited.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from deepreason.application.results import results_summary
from deepreason.harness import Harness
from deepreason.ontology import Provenance
from deepreason.ontology.event import LLMCall

from tests.test_amendment_epochs import ORIGINAL_QUESTION, _problem_id
from tests.test_lifecycle_operation_parity import _bind_v6_root

REPO = Path(__file__).resolve().parents[1]

_SPEND_PER_CALL = (1301, 2207, 734)


def _spending_then_failing_scheduler(*, fail: bool):
    """A scheduler stand-in that logs real provider spend, then dies.

    The spend must reach the LOG (`event.llm.tokens`) rather than an in-memory
    total, because that is the only place a terminal written by the failure
    path can still find it.
    """

    def run(harness, _config, _cycles, _token_budget, **_kwargs):
        harness.create_artifact(
            "A conjecture recorded before the run died.",
            provenance=Provenance(role="conjecturer"),
            problem_id=_problem_id(ORIGINAL_QUESTION),
        )
        prompt = harness.blobs.put(b"PACK")
        raw = harness.blobs.put(b"{}")
        harness.record_llm_calls(
            [
                LLMCall(
                    role="conjecturer",
                    model="stub",
                    endpoint="mock://stub",
                    prompt_ref=prompt,
                    raw_ref=raw,
                    tokens=tokens,
                )
                for tokens in _SPEND_PER_CALL
            ],
            "spend-before-failure",
        )
        if fail:
            raise RuntimeError("the run died after spending real tokens")
        return (
            {"frontier": [], "survivors": [], "problems": [], "diagnostics": []},
            None,
            {
                "metered_tokens": None,
                "logged_tokens_this_run": sum(_SPEND_PER_CALL),
                "delta": None,
                "note": "offline no-provider fixture",
            },
        )

    return run


def _drive(tmp_path, monkeypatch, *, name, fail):
    from deepreason.cli.main import main
    from deepreason.run_manifest import MANIFEST_NAME

    root, _manifest, _spec, problem_file = _bind_v6_root(tmp_path, name=name)
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler", _spending_then_failing_scheduler(fail=fail)
    )
    main(
        [
            "--root", str(root), "run", "--budget", "1",
            "--problem", str(problem_file),
            "--run-manifest", str(root / MANIFEST_NAME),
        ]
    )
    return root


def test_a_failed_run_reports_the_spend_its_own_log_carries(tmp_path, monkeypatch):
    """(a) WRITER. The failure terminal no longer asserts a zero it never measured."""

    root = _drive(tmp_path, monkeypatch, name="spent-then-failed", fail=True)

    status = json.loads((root / "run-status.json").read_text())
    assert status["state"] == "failed"
    assert status["stop_reason"] == "operational_failure"
    assert status["token_spend"] == sum(_SPEND_PER_CALL)

    # And the log — the record itself — agrees with the sidecar.
    logged = sum(
        event.llm.tokens
        for event in Harness(root, read_only=True).log.read()
        if event.llm
    )
    assert logged == sum(_SPEND_PER_CALL)
    assert results_summary(root)["run"]["token_spend"] == sum(_SPEND_PER_CALL)


def test_a_run_that_genuinely_spent_nothing_still_reports_zero(tmp_path, monkeypatch):
    """The CONTROL for the writer: a real zero must survive the fix.

    Without this, a fix that reported any non-zero number would pass the test
    above while making the surface wrong in the other direction.
    """

    from deepreason.cli.main import main
    from deepreason.run_manifest import MANIFEST_NAME
    from tests.test_lifecycle_operation_parity import _no_provider_scheduler

    root, _manifest, _spec, problem_file = _bind_v6_root(
        tmp_path, name="spent-nothing"
    )
    monkeypatch.setattr("deepreason.ops.run_scheduler", _no_provider_scheduler())
    main(
        [
            "--root", str(root), "run", "--budget", "1",
            "--problem", str(problem_file),
            "--run-manifest", str(root / MANIFEST_NAME),
        ]
    )
    assert json.loads((root / "run-status.json").read_text())["token_spend"] == 0
    assert results_summary(root)["run"]["token_spend"] == 0


def _committed_roots_stating_a_false_zero() -> list[Path]:
    """Committed roots whose status says 0 while their own log says otherwise.

    Selected by PROPERTY over `git ls-files`, never by a hard path: a
    committed root may legitimately be renamed (`git mv run-<id>
    failed-epochN-run-<id>` retires one), and a test that named one would fail
    on a rename that changed nothing it guards.
    """

    listed = subprocess.run(
        ["git", "ls-files", "experiments"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.split()
    found = []
    for entry in listed:
        if not entry.endswith("/run-status.json"):
            continue
        root = REPO / Path(entry).parent
        try:
            if json.loads((root / "run-status.json").read_text())["token_spend"] != 0:
                continue
            logged = sum(
                event.llm.tokens
                for event in Harness(root, read_only=True).log.read()
                if event.llm
            )
        except Exception:  # noqa: BLE001 - a legacy root that will not replay
            continue
        if logged > 0:
            found.append(root)
    return found


def test_the_reader_recovers_the_spend_of_a_committed_root_stating_zero():
    """(b) READER. A root already committed with a false zero, never edited.

    The writer fix cannot reach these: their bytes are evidence. The truth is
    still IN them — in the append-only log — and walking it is the only power
    a reader over an append-only record has. `_adjudication` in the same file
    already derives its counts the same way.
    """

    roots = _committed_roots_stating_a_false_zero()
    assert roots, (
        "no committed root states a false zero — if the tree stopped carrying "
        "one, this regression's population is gone and the test should be "
        "retired deliberately rather than left to pass vacuously"
    )
    root = min(roots, key=lambda r: (r / "log.jsonl").stat().st_size)

    before = (root / "run-status.json").read_bytes()
    logged = sum(
        event.llm.tokens
        for event in Harness(root, read_only=True).log.read()
        if event.llm
    )
    reported = results_summary(root)["run"]["token_spend"]

    assert json.loads(before)["token_spend"] == 0
    assert reported == logged > 0
    # The reader wrote nothing. A committed root is evidence.
    assert (root / "run-status.json").read_bytes() == before


def test_a_root_without_a_status_record_still_reports_a_typed_absence(tmp_path):
    """The absence sentinel is PRESERVED for a genuinely absent key.

    Deriving from the log must not turn "this run recorded no status at all"
    into the number 0 — that would state a fact the record never held, which
    is the same class of error this tranche is fixing.
    """

    from deepreason.application.results import _run

    absent = _run(None, None, None)["token_spend"]
    assert absent == {"absent": True, "reason": "NO_RUN_STATUS_JSON"}
    assert _run({"state": "failed"}, None, None)["token_spend"] == absent


def test_a_nonzero_sidecar_figure_is_reported_as_recorded_and_not_re_derived():
    """The reader's scope is NARROW, and stays narrow.

    Nine committed roots carry a nonzero `token_spend` that is SMALLER than
    their own log's sum — a different, un-diagnosed disagreement
    (`RUN_ANATOMY_SYNTHESIS` organ 10, "three token instruments, 27
    disagreements"), parked, not fixed here. Deciding which of two real
    measurements is authoritative is not this regression's question, and a
    reader that quietly answered it would re-adjudicate roots nobody
    diagnosed. Only a ZERO is treated as a non-measurement, because omitting
    the kwarg is exactly what produced it.
    """

    from types import SimpleNamespace

    from deepreason.application.results import _token_spend

    # A stand-in whose log READS CLEANLY and reports a DIFFERENT number. It
    # must not raise: `_token_spend` falls back to the sidecar on any log
    # error, so a stand-in that threw would pass whether or not the log was
    # consulted, and could never fail.
    louder_log = SimpleNamespace(
        log=SimpleNamespace(
            read=lambda: [SimpleNamespace(llm=SimpleNamespace(tokens=119_659))]
        )
    )
    assert _token_spend({"token_spend": 90_700}, louder_log) == 90_700
    # ...and the same stand-in DOES get consulted when the sidecar says zero,
    # which is what makes the assertion above about scope rather than about
    # the stand-in being inert.
    assert _token_spend({"token_spend": 0}, louder_log) == 119_659
