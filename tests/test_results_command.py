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

    root = _smallest_root_with(*_TERMINAL_FILES)
    summary = results_summary(root)
    status = json.loads((root / "run-status.json").read_text())

    assert summary["identity"]["run_id"] == status["run_id"]
    assert summary["run"]["state"] == status["state"]
    assert summary["run"]["stop_reason"] == status["stop_reason"]
    assert summary["run"]["cycles_completed"] == status["cycle"]
    assert summary["run"]["token_spend"] == status["token_spend"]
    # `null` in the record means no ceiling; the reader must SAY so rather
    # than emit a bare None a caller would read as "unknown".
    expected_limit = status["token_limit"]
    assert summary["run"]["token_limit"] == (
        "unlimited" if expected_limit is None else expected_limit
    )


def test_results_summary_reports_artifact_survivor_and_frontier_counts():
    """R7: accepted/refuted/suspended, final survivor count, frontier."""

    from deepreason.application.results import results_summary

    root = _smallest_root_publishing("survivors")
    summary = results_summary(root)
    result = json.loads((root / "run-result.json").read_text())

    assert summary["artifacts"]["survivor_count"] == len(result["survivors"])
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
