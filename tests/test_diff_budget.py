"""Tests for tools/diff_budget.py (Rung G1: actual-diff budget gate).

Regression motivation: Rung S5 (experiments/2026-08-07-change-seats-in-
record-s5/) overran its ledgered budget twice because the ceiling was
checked against SPEC.md's plan-time estimate, never against the actual
`git diff`. These tests pin the gate's verdict logic against a disposable
fixture repo, not against any committed root -- the tool itself is what
gets exercised via subprocess, matching how dr-execute-step actually
invokes it.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "diff_budget.py"


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _run(repo, *args):
    return subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=repo, capture_output=True, text=True
    )


@pytest.fixture
def repo(tmp_path):
    """A disposable git repo: one base commit (a.txt, b.txt, 10 lines
    each), then a second commit adding 5 lines to a.txt and 3 to b.txt
    (8 insertions total, the fixture every test below reasons about)."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "a.txt").write_text("line\n" * 10)
    (tmp_path / "b.txt").write_text("line\n" * 10)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()
    (tmp_path / "a.txt").write_text("line\n" * 10 + "new\n" * 5)
    (tmp_path / "b.txt").write_text("line\n" * 10 + "new\n" * 3)
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "change")
    return tmp_path, base


def test_within_verdict_when_actual_at_or_under_ceiling(repo):
    tmp_path, base = repo
    result = _run(tmp_path, base, "--ceiling", "8")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["result_type"] == "DIFF_BUDGET_RESULT_V1"
    assert data["total_insertions"] == 8
    assert data["verdict"] == "WITHIN"


def test_exceeded_verdict_when_actual_over_ceiling(repo):
    tmp_path, base = repo
    result = _run(tmp_path, base, "--ceiling", "5")
    data = json.loads(result.stdout)
    assert data["total_insertions"] == 8
    assert data["verdict"] == "EXCEEDED"


def test_boundary_equality_is_within_not_exceeded(repo):
    """Permanent mutation companion (dr-execute-step 'Durable tests' rule
    3): pins the WITHIN/EXCEEDED comparison at total_insertions == ceiling
    to `<=`, not `<`. A mutation that flips the comparison operator kills
    this test and only this test in the file."""
    tmp_path, base = repo
    result = _run(tmp_path, base, "--ceiling", "8")
    data = json.loads(result.stdout)
    assert data["total_insertions"] == data["ceiling"] == 8
    assert data["verdict"] == "WITHIN"


def test_no_ceiling_verdict_when_ceiling_omitted(repo):
    tmp_path, base = repo
    result = _run(tmp_path, base)
    data = json.loads(result.stdout)
    assert data["ceiling"] is None
    assert data["verdict"] == "NO_CEILING"


def test_area_breakdown_for_multiple_paths(repo):
    tmp_path, base = repo
    result = _run(tmp_path, base, "--paths", "a.txt", "b.txt")
    data = json.loads(result.stdout)
    assert data["areas"] == {"a.txt": 5, "b.txt": 3}


def test_total_insertions_independent_of_paths_overlap(repo):
    """total_insertions is computed from the unrestricted diff, not by
    summing --paths areas -- so overlapping or partial --paths never
    silently shrinks the number the ceiling is actually checked against."""
    tmp_path, base = repo
    result = _run(tmp_path, base, "--paths", "a.txt")
    data = json.loads(result.stdout)
    assert data["areas"] == {"a.txt": 5}
    assert data["total_insertions"] == 8


def test_against_a_specific_commit_not_the_working_tree(repo):
    """--against REF diffs base..REF instead of base..worktree -- the
    mode the retrodiction demonstration (SPEC.md S3) depends on."""
    tmp_path, base = repo
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True, check=True
    ).stdout.strip()
    result = _run(tmp_path, base, "--against", head, "--ceiling", "8")
    data = json.loads(result.stdout)
    assert data["against"] == head
    assert data["total_insertions"] == 8
    assert data["verdict"] == "WITHIN"


def test_invalid_invocation_exit_class_for_missing_base(repo):
    tmp_path, _base = repo
    result = _run(tmp_path)
    assert result.returncode == 2
    assert result.stdout == ""


def test_invalid_invocation_exit_class_for_negative_ceiling(repo):
    tmp_path, base = repo
    result = _run(tmp_path, base, "--ceiling", "-1")
    assert result.returncode == 2
    assert result.stdout == ""


def test_evidence_unavailable_exit_class_for_unresolvable_ref(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "not-a-real-ref")
    assert result.returncode == 3
    assert result.stdout == ""


def test_evidence_unavailable_exit_class_outside_a_git_repo(tmp_path):
    result = _run(tmp_path, "HEAD")
    assert result.returncode == 3
    assert result.stdout == ""


def test_self_test_mode_passes():
    result = subprocess.run(
        [sys.executable, str(TOOL), "--self-test"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "SELF-TEST PASS" in result.stdout
