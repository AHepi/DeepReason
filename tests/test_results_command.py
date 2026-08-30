"""`deepreason results` — the one discoverable typed-outcome reader.

Implements the 2026-08-13 results-retrieval tranche
(experiments/2026-08-13-change-results-retrieval-surface/). The operator's
defect, verbatim: "When retrieving run results, Opus 5 keeps grepping for
flags that dont exist."

Every fixture is selected by PROPERTY over `git ls-files`, never by a hard
path: a committed root may legitimately be renamed (`git mv run-<id>
failed-epochN-run-<id>` retires one), and a test that named it would fail on
a rename that changed nothing it guards.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# Files whose presence distinguishes a fully terminalized root from one that
# stopped before publication. Both shapes exist in the committed tree (87 of
# 107 roots carry run-status.json), which is why R12's typed absences are
# load-bearing rather than a corner case.
_TERMINAL_FILES = (
    "run-status.json",
    "run-result.json",
    "REPLAY_VALIDATION.json",
    "run-stop.json",
)


def _tracked_roots() -> list[Path]:
    """Every git-tracked run root, smallest log first (rule 1: committed evidence)."""

    listed = subprocess.run(
        ["git", "ls-files", "experiments"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    roots = {
        REPO / Path(entry).parent
        for entry in listed
        if entry.endswith("/log.jsonl")
    }
    return sorted(roots, key=lambda root: (root / "log.jsonl").stat().st_size)


def _smallest_root_with(*names: str) -> Path:
    for root in _tracked_roots():
        if all((root / name).exists() for name in names):
            return root
    pytest.skip(f"no committed root carries all of {names}")


def _smallest_root_publishing(key: str) -> Path:
    """Smallest committed root whose `run-result.json` carries ``key``.

    A FAILED run publishes a `deepreason-run-result-v2` payload with
    `error`/`error_type` and no survivor or frontier set, so "has
    run-result.json" is not the same property as "published a survivor set".
    """

    for root in _tracked_roots():
        payload = root / "run-result.json"
        if not payload.exists():
            continue
        if key in json.loads(payload.read_text()):
            return root
    pytest.skip(f"no committed root publishes run-result.json[{key!r}]")


def _smallest_root_logging(*signals: str) -> Path:
    """Smallest committed root whose log carries every named Measure signal.

    Selected by PROPERTY rather than by path so the fixture survives roots
    being retired, renamed by epoch, or added: 4 committed roots carry
    `embedder-fallback` and 105 carry the `embedder` stamp today, and the
    test means "a root of this shape", never "this particular directory".
    """

    for root in _tracked_roots():
        text = (root / "log.jsonl").read_text(errors="ignore")
        if all(f'"{signal}"' in text for signal in signals):
            return root
    pytest.skip(f"no committed root logs all of {signals}")


def _smallest_root_logging_no_embedder() -> Path:
    """Smallest committed root that never stamped an embedder identity.

    Two exist. They predate the stamp, which is exactly why the reader must
    tolerate their absence rather than treat it as a failure.
    """

    for root in _tracked_roots():
        text = (root / "log.jsonl").read_text(errors="ignore")
        if '"embedder"' not in text and '"embedder-fallback"' not in text:
            return root
    pytest.skip("every committed root stamps an embedder identity")


def _smallest_root_without(*names: str) -> Path:
    for root in _tracked_roots():
        if not any((root / name).exists() for name in names):
            return root
    pytest.skip(f"every committed root carries one of {names}")


def _fingerprint(root: Path) -> dict[str, tuple[int, str]]:
    """(size, sha256) for every file under ``root`` — the read-only witness.

    Deliberately content-addressed rather than mtime-based: a reader that
    rewrote a file with identical bytes would still have written into a
    committed root, and mtime alone would also flag a harmless `stat`.
    """

    snapshot: dict[str, tuple[int, str]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        payload = path.read_bytes()
        snapshot[str(path.relative_to(root))] = (
            len(payload),
            hashlib.sha256(payload).hexdigest(),
        )
    return snapshot


def _is_absence(value) -> bool:
    return isinstance(value, dict) and value.get("absent") is True and bool(
        value.get("reason")
    )


def _key_shape(value):
    """Recursive key shape, ignoring values — two roots must agree on it (R12)."""

    if _is_absence(value):
        return "<absent>"
    if isinstance(value, dict):
        return {key: _key_shape(inner) for key, inner in sorted(value.items())}
    return "<value>"


def test_results_summary_reports_run_identity_state_and_budget():
    """R6: run id, state, stop_reason, cycles completed, token spend vs budget."""

    from deepreason.application.results import results_summary
    from deepreason.harness import Harness

    root = _smallest_root_with(*_TERMINAL_FILES)
    summary = results_summary(root)
    status = json.loads((root / "run-status.json").read_text())

    assert summary["identity"]["run_id"] == status["run_id"]
    assert summary["run"]["state"] == status["state"]
    assert summary["run"]["stop_reason"] == status["stop_reason"]
    assert summary["run"]["cycles_completed"] == status["cycle"]
    # Spend comes from the LOG, not from the sidecar, wherever the sidecar
    # says zero: the three failure terminals used to omit the argument, and
    # `ProgressEvent.token_spend` defaults to 0, so a zero there is an
    # omission asserting a measurement rather than a measurement (fixed
    # 2026-08-29; 20 of 59 committed roots carry that false zero, this
    # fixture among them). A nonzero sidecar figure is still reported as
    # recorded. Derived from the root here, never from the reader's own code.
    logged = sum(
        event.llm.tokens
        for event in Harness(root, read_only=True).log.read()
        if event.llm
    )
    assert summary["run"]["token_spend"] == (
        logged if status["token_spend"] == 0 else status["token_spend"]
    )
    # `null` in the record means no ceiling; the reader must SAY so rather
    # than emit a bare None a caller would read as "unknown".
    expected_limit = status["token_limit"]
    assert summary["run"]["token_limit"] == (
        "unlimited" if expected_limit is None else expected_limit
    )


def test_results_summary_reports_artifact_survivor_and_frontier_counts():
    """R7: accepted/refuted/suspended, final survivor count, frontier.

    The survivor count is the published set LESS its import-role admission
    records, which the invariant says never count. This assertion used to read
    `== len(result["survivors"])` and passed while the surface reported 10
    survivors for a root holding 4 admission records
    (`completed-epoch3-run-9e9812fe`), and 82 for `run-1b31f006`. See
    `experiments/2026-08-25-fix-import-role-survivors/`.
    """

    from deepreason.application.results import results_summary
    from deepreason.harness import Harness
    from deepreason.ontology.state import is_import_admission

    root = _smallest_root_publishing("survivors")
    summary = results_summary(root)
    result = json.loads((root / "run-result.json").read_text())
    state = Harness(root, read_only=True).state

    assert summary["artifacts"]["survivor_count"] == sum(
        1 for aid in result["survivors"] if not is_import_admission(state, aid)
    )
    assert summary["artifacts"]["survivor_count"] <= len(result["survivors"])
    assert summary["artifacts"]["frontier"]["count"] == len(result["frontier"])
    assert summary["artifacts"]["frontier"]["artifact_ids"] == list(result["frontier"])
    if (root / "run-status.json").exists():
        status = json.loads((root / "run-status.json").read_text())
        assert summary["artifacts"]["frontier"]["problem_id"] == status["problem_id"]
    for label in ("accepted", "refuted", "suspended"):
        assert isinstance(summary["artifacts"][label], int)


def test_a_failed_run_reports_no_survivor_set_rather_than_zero(tmp_path):
    """S4a/R12: a missing survivor set is an absence, never a false zero.

    A `deepreason-run-result-v2` payload for a run that failed before
    publication carries `error`/`error_type` and no `survivors`/`frontier` —
    counting that as 0 would state a result the record never held.
    """

    from deepreason.application.results import results_summary

    for root in _tracked_roots():
        payload = root / "run-result.json"
        if not payload.exists():
            continue
        if "survivors" in json.loads(payload.read_text()):
            continue
        summary = results_summary(root)
        assert _is_absence(summary["artifacts"]["survivor_count"])
        assert summary["artifacts"]["survivor_count"]["reason"] == "NO_SURVIVOR_RECORD"
        assert "NO_SURVIVOR_RECORD" in summary["absences"]
        return
    pytest.skip("every committed run-result.json publishes a survivor set")


def test_absent_facts_are_typed_absences_not_omitted_keys():
    """R12: a root missing every terminal file has the SAME key shape."""

    from deepreason.application.results import results_summary

    populated = results_summary(_smallest_root_with(*_TERMINAL_FILES))
    bare = results_summary(_smallest_root_without(*_TERMINAL_FILES))

    assert set(bare) == set(populated)
    assert _key_shape({k: v for k, v in bare.items() if k != "absences"}) is not None
    assert bare["absences"], "a root missing every terminal file must report absences"
    assert bare["absences"] == sorted(bare["absences"])
    assert bare["absences"] == sorted(set(bare["absences"])), "absences must be unique"
    assert _is_absence(bare["run"]["state"])
    assert _is_absence(bare["artifacts"]["survivor_count"])
    # Replay-derived facts survive the missing sidecars: the log is the record.
    assert isinstance(bare["artifacts"]["accepted"], int)


def test_every_absence_reason_is_reachable_from_the_declared_set():
    """R12: absence reasons are a closed typed vocabulary, not free text."""

    from deepreason.application.results import ABSENCE_REASONS, results_summary

    for root in (
        _smallest_root_with(*_TERMINAL_FILES),
        _smallest_root_without(*_TERMINAL_FILES),
    ):
        summary = results_summary(root)
        assert set(summary["absences"]) <= set(ABSENCE_REASONS)


def test_results_summary_writes_nothing_into_a_committed_root():
    """R17: the command NEVER writes into a run root — with or without --verify.

    A committed root is evidence; a reader that repaired it would destroy the
    thing it was asked to report on.
    """

    from deepreason.application.results import results_summary

    root = _smallest_root_with(*_TERMINAL_FILES)
    before = _fingerprint(root)
    results_summary(root)
    results_summary(root, verify=True)
    after = _fingerprint(root)

    assert after == before, {
        "added": sorted(set(after) - set(before)),
        "removed": sorted(set(before) - set(after)),
        "changed": sorted(k for k in set(before) & set(after) if before[k] != after[k]),
    }


def test_top_level_help_names_the_results_verb():
    """Implements R16 — the acceptance test for the reported defect itself.

    The operator's words, 2026-08-13: "When retrieving run results, Opus 5
    keeps grepping for flags that dont exist." A session that has only
    `deepreason --help` in front of it must be able to NAME the verb that
    retrieves results, without opening a single source file. Nothing else in
    the top-level help says the words "results" and "run" together — `status`
    is provider readiness, and `findings`' line never uses the word.
    """

    from deepreason.cli.main import build_parser

    help_text = build_parser().format_help()

    assert "results" in help_text
    assert "read a run's typed results" in help_text


def test_results_is_reachable_without_the_global_root_option():
    """R1/R16: the path is a plain positional, so `--root` cannot be misplaced.

    `--root` is a GLOBAL option that must precede the verb; a session writing
    `deepreason findings --root R` gets an argparse error, which is the
    guessing loop this command exists to end.
    """

    from deepreason.cli.main import build_parser

    parsed = build_parser().parse_args(["results", "/some/root", "--json"])
    assert parsed.command == "results"
    assert parsed.path == "/some/root"
    assert parsed.json is True
    assert parsed.verify is False

    bare = build_parser().parse_args(["results"])
    assert bare.path is None, "the path is optional; the home is the default"


def test_results_is_not_a_root_admission_command():
    """SPEC.md A8: a reader must not refuse the pre-V6 roots most worth reading.

    11 committed roots raise `UnsupportedRunManifestVersionError`
    (docs/AUDIT_BASELINES.md). Admitting `results` would refuse them; instead
    the manifest's state is reported as a typed fact.
    """

    from deepreason.cli.main import _ROOT_ADMISSION_COMMANDS

    assert "results" not in _ROOT_ADMISSION_COMMANDS
    assert "findings" not in _ROOT_ADMISSION_COMMANDS


def _root_by_adjudication(*, ran: bool) -> Path:
    """Smallest committed root that did (or did not) run a defended trial.

    Selected by the PROPERTY that produces the fact — a judge call or a
    `trial-*` signal in the log — so reclassifying either empties the witness
    set and skips loudly rather than passing over nothing.
    """

    from deepreason.harness import Harness

    for root in _tracked_roots():
        try:
            events = tuple(Harness(root, read_only=True).log.read())
        except Exception:  # noqa: BLE001 - a legacy root may defeat the reader
            continue
        judges = sum(
            1 for event in events
            if event.llm is not None and event.llm.role == "judge"
        )
        trials = sum(
            1 for event in events
            if event.inputs and str(event.inputs[0]).startswith("trial-")
        )
        if ran and judges and trials:
            return root
        if not ran and not judges and not trials:
            return root
    pytest.skip(f"no committed root with adjudication ran={ran}")


def test_adjudication_counts_judge_calls_and_trial_verdicts():
    """R8: defended-trial verdict counts and judge-call count when adjudication ran."""

    from deepreason.application.results import results_summary

    summary = results_summary(_root_by_adjudication(ran=True))
    adjudication = summary["adjudication"]

    assert adjudication["ran"] is True
    assert adjudication["judge_calls"] > 0
    verdicts = (
        adjudication["trial_observations"]
        | adjudication["trial_declined"]
        | adjudication["trial_blocked"]
    )
    assert verdicts, "a root carrying trial-* signals must report some verdict"
    assert all(isinstance(count, int) for count in verdicts.values())


def test_adjudication_absence_is_a_typed_zero_not_a_missing_key():
    """R8/R12: 'no trial ran' is a fact worth stating, not a gap."""

    from deepreason.application.results import results_summary

    adjudication = results_summary(_root_by_adjudication(ran=False))["adjudication"]

    assert adjudication["ran"] is False
    assert adjudication["judge_calls"] == 0
    assert adjudication["trial_observations"] == {}
    assert adjudication["trial_declined"] == {}
    assert adjudication["trial_blocked"] == {}


def test_verification_reads_the_stored_verdict_and_does_not_replay(monkeypatch):
    """R9: read the stored record; do not re-derive unless --verify is passed.

    Re-deriving replays the whole log, which is O(run length) — the guard here
    is that the default path never enters it, proved by making the replay
    explode rather than by timing it.
    """

    from deepreason.application import results as results_module

    root = _smallest_root_with(*_TERMINAL_FILES)
    stored = json.loads((root / "REPLAY_VALIDATION.json").read_text())
    published = json.loads((root / "run-result.json").read_text())

    import deepreason.verification.report as report_module

    def _must_not_run(*_args, **_kwargs):
        raise AssertionError("the default path re-derived instead of reading")

    monkeypatch.setattr(report_module, "verify_root_report", _must_not_run)
    verification = results_module.results_summary(root)["verification"]

    assert verification["source"] == "stored"
    assert verification["valid"] == stored["valid"]
    assert verification["violations"] == len(stored["verification"]["violations"])
    assert verification["families"] == dict(
        sorted(published["verification"]["finding_counts"].items())
    )
    # The two stored halves agree by construction across every committed root:
    # the violation list is empty in exactly the roots whose verdict is valid.
    assert verification["valid"] == (verification["violations"] == 0)


def test_verify_flag_re_derives_the_same_five_family_shape():
    """R9: --verify re-derives, key-identical to the stored shape."""

    from deepreason.application.results import results_summary

    root = _smallest_root_with(*_TERMINAL_FILES)
    stored = results_summary(root)["verification"]
    rederived = results_summary(root, verify=True)["verification"]

    assert rederived["source"] == "rederived"
    assert set(rederived) == set(stored)
    assert set(rederived["families"]) == {
        "completion",
        "epistemic",
        "integrity",
        "operational",
        "security",
    }


def test_verification_is_a_typed_absence_when_no_verdict_was_published():
    """R9/R12: 21 of the committed roots carry no REPLAY_VALIDATION.json."""

    from deepreason.application.results import results_summary

    verification = results_summary(
        _smallest_root_without("REPLAY_VALIDATION.json")
    )["verification"]

    for key in ("source", "valid", "violations", "families"):
        assert _is_absence(verification[key])
        assert verification[key]["reason"] == "NO_REPLAY_VALIDATION_JSON"


def test_terminal_readiness_answers_the_amend_question():
    """R10: amendment epochs, and whether the root stands at a valid typed terminal.

    The THREE halves answer different questions and all are required: the
    replay verdict says the record is sound, the stop reason says the
    lifecycle will resume from that KIND of stop, and the continuation
    authority says the lifecycle actually RECORDED the transition resumption
    reads.  The third was added 2026-08-28 after a root satisfying the first
    two refused `continue` (P6; audit finding F-C).
    """

    from deepreason.application.results import results_summary
    from deepreason.harness import Harness
    from deepreason.workflow.lifecycle import RESUMABLE_STOP_REASONS

    root = _smallest_root_with(*_TERMINAL_FILES)
    summary = results_summary(root)
    stored = json.loads((root / "REPLAY_VALIDATION.json").read_text())
    stop = json.loads((root / "run-stop.json").read_text())

    terminal = summary["terminal"]
    assert set(terminal) == {
        "valid_typed_terminal",
        "stop_reason_resumable",
        "continuation_authority",
        "lifecycle_refusal",
        "amend_ready",
        "terminal_epoch",
    }
    assert terminal["valid_typed_terminal"] == bool(
        stored["valid"] and isinstance(stored.get("terminal_binding"), dict)
    )
    assert terminal["stop_reason_resumable"] == (
        stop["reason"] in RESUMABLE_STOP_REASONS
    )
    # The third half, added 2026-08-28: `continue` resumes from a recorded
    # lifecycle decision, never from a stop REASON, so a reader consulting
    # only the reason promised continuations `continue` refused
    # (CONTINUE_TYPED_STOP_REQUIRED). Derived from the root here, as the
    # other two are — the reader is not allowed to be its own witness.
    state = Harness(root, read_only=True).workflow_state
    assert terminal["continuation_authority"] == (
        state.terminal_lifecycle_decision is not None
        or state.current_resume_decision is not None
    )
    assert terminal["amend_ready"] == (
        terminal["valid_typed_terminal"]
        and terminal["stop_reason_resumable"]
        and terminal["continuation_authority"]
    )
    assert terminal["terminal_epoch"] == stored["terminal_binding"]["terminal_epoch"]

    assert set(summary["amendment"]) == {"epochs", "epoch_seqs"}
    assert summary["amendment"]["epochs"] == len(summary["amendment"]["epoch_seqs"])


def test_terminal_readiness_is_false_with_typed_absences_on_an_unterminalized_root():
    """R10/R12: a root that never published a terminal says so, and says why."""

    from deepreason.application.results import results_summary

    summary = results_summary(_smallest_root_without(*_TERMINAL_FILES))
    terminal = summary["terminal"]

    assert terminal["valid_typed_terminal"] is False
    assert terminal["amend_ready"] is False
    assert _is_absence(terminal["stop_reason_resumable"])
    assert _is_absence(terminal["terminal_epoch"])
    # An absent amendment chain is an empty one, not an unreadable one.
    assert summary["amendment"]["epochs"] == 0


def test_rendering_glosses_every_technical_label_and_shows_absences():
    """R11: human-readable mode with GLOSSED labels — the point of the command.

    A label a session cannot interpret sends it back to guessing, which is the
    defect this tranche exists to remove.
    """

    from deepreason.application.results import render_results, results_summary

    for root in (
        _smallest_root_with(*_TERMINAL_FILES),
        _smallest_root_without(*_TERMINAL_FILES),
    ):
        summary = results_summary(root)
        rendered = render_results(summary)

        for heading in (
            "## Question",
            "## Run",
            "## Artifacts",
            "## Adjudication",
            "## Verification",
            "## Amendment and terminal readiness",
        ):
            assert heading in rendered
        assert "verify_root" in rendered
        assert "the replay check that re-derives" in rendered
        assert "--verify" in rendered
        if summary["absences"]:
            assert "## Not recorded by this root" in rendered
            for reason in summary["absences"]:
                assert reason in rendered


def test_rendering_never_prints_an_absence_as_a_number():
    """R12: an absent fact must not read as a zero in the human mode either."""

    from deepreason.application.results import render_results, results_summary

    root = _smallest_root_without(*_TERMINAL_FILES)
    rendered = render_results(results_summary(root))

    for line in rendered.splitlines():
        if "survivors (" in line or "cycles completed" in line:
            assert "not recorded" in line, line


def test_a_home_holding_one_run_resolves_to_it(tmp_path):
    """SPEC.md A1: `<root-or-home>` — a home with exactly one run needs no path."""

    from deepreason.application.results import resolve_results_root

    root = tmp_path / "runs" / "run-only"
    root.mkdir(parents=True)
    (root / "log.jsonl").write_text("")

    resolved, how = resolve_results_root(tmp_path)
    assert resolved == root.resolve()
    assert how == "home"


def test_an_ambiguous_home_refuses_and_names_every_candidate(tmp_path):
    """R13/A1: the refusal must cost a paste, not another guess."""

    from deepreason.application.results import ResultsError, resolve_results_root

    for name in ("run-a", "run-b"):
        root = tmp_path / "runs" / name
        root.mkdir(parents=True)
        (root / "log.jsonl").write_text("")

    with pytest.raises(ResultsError) as caught:
        resolve_results_root(tmp_path)

    assert caught.value.code == "RESULTS_HOME_AMBIGUOUS"
    for name in ("run-a", "run-b"):
        assert name in str(caught.value), "the refusal must list every candidate"


def test_a_path_holding_no_run_refuses_with_the_catalogued_code(tmp_path):
    """R13: errors route through the error catalog, so explain-error covers them."""

    from deepreason.application.results import ResultsError, resolve_results_root
    from deepreason.error_catalog import lookup

    with pytest.raises(ResultsError) as caught:
        resolve_results_root(tmp_path / "nowhere")

    assert caught.value.code == "RESULTS_ROOT_NOT_FOUND"
    assert lookup("RESULTS_ROOT_NOT_FOUND") is not None
    assert lookup("RESULTS_HOME_AMBIGUOUS") is not None


def test_results_summary_carries_its_schema_and_resolution_provenance():
    """R5/R11: a stable, self-identifying record — nothing model-authored."""

    from deepreason.application.results import results_summary

    root = _smallest_root_with(*_TERMINAL_FILES)
    summary = results_summary(root)

    assert summary["schema"] == "deepreason-results.v1"
    assert summary["root"] == str(root)
    assert summary["resolved_from"] == "root"
    assert set(summary) >= {
        "schema",
        "root",
        "resolved_from",
        "question",
        "identity",
        "run",
        "artifacts",
        "adjudication",
        "verification",
        "amendment",
        "terminal",
        "absences",
    }
    assert json.loads(json.dumps(summary)) == summary, "the summary must be JSON-stable"


# ---- the embedder a run actually measured with (tranche 2026-08-16) ----


def test_results_surfaces_the_embedder_and_names_a_fallback_loudly():
    """Implements R8 of tranche 2026-08-16-change-embedder-auto-install.

    A run that configured the neural model, failed to build it and measured
    with hashing-128 recorded that as an `embedder-fallback` Measure and then
    told nobody: the grounded-extension run carried the pair at log seq 2 and
    seq 8 and its RESULTS.md never mentioned it. `deepreason results` is where
    an operator already looks for a run's typed outcome, so it is where the
    substituted geometry has to appear.
    """

    from deepreason.application.results import render_results, results_summary

    root = _smallest_root_logging("embedder-fallback")
    summary = results_summary(root)
    embedder = summary["embedder"]

    assert embedder["fallback"] is True
    assert embedder["backend"] == "hashing"
    assert embedder["model"] == "hashing-128"
    # The configured model is the half that makes the fallback legible: it
    # says which geometry the run was SUPPOSED to have.
    assert embedder["configured_model"]
    assert embedder["configured_model"] != embedder["model"]

    rendered = render_results(summary)
    assert "hashing (fallback)" in rendered


def test_results_names_the_neural_backend_when_no_fallback_happened():
    """The same line must distinguish a run that got what it asked for, or
    "fallback" carries no information."""

    from deepreason.application.results import render_results, results_summary

    root = _smallest_root_logging("embedder")
    summary = results_summary(root)
    embedder = summary["embedder"]

    assert _is_absence(embedder) is False
    assert embedder["backend"] in {"hashing", "neural"}
    assert isinstance(embedder["fingerprint"], str)
    rendered = render_results(summary)
    assert f"{embedder['backend']} ({embedder['model']})" in rendered
    # The no-fallback line must NOT carry the alarm word, or "(fallback)"
    # stops distinguishing anything.
    assert "(fallback)" not in rendered


def test_results_embedder_absence_is_typed_not_a_failure():
    """Reader-before-writer guardrail: two committed roots predate the
    embedder stamp entirely. They must read as a typed ABSENCE from the
    closed vocabulary, never as an error and never as a silently omitted key
    a caller cannot distinguish from a false value.
    """

    from deepreason.application.results import (
        ABSENCE_REASONS,
        results_summary,
    )

    root = _smallest_root_logging_no_embedder()
    summary = results_summary(root)

    assert _is_absence(summary["embedder"])
    assert summary["embedder"]["reason"] == "NO_EMBEDDER_RECORD"
    assert "NO_EMBEDDER_RECORD" in ABSENCE_REASONS
    assert "NO_EMBEDDER_RECORD" in summary["absences"]
