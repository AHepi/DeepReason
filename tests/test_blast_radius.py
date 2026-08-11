"""Tests for tools/blast_radius.py (Rung G6: blast-radius disclosure gate).

Regression motivation: experiments/2026-08-10-change-blast-radius-analysis/
CENSUS.md Part B names seven cases of an authorized change hiding or
disconnecting architecture the request never disclosed -- most directly
docs/ERRATA_EXECUTOR.md's 2026-08-09 entry, where a tranche's own SPEC.md
had already found a frozen-surface contact in prose and the STOP that
finding should have forced did not happen before the commit landed. These
tests pin the gate's four computations against a disposable fixture repo,
not against any committed root -- the tool itself is what gets exercised
via subprocess, matching how dr-execute-step actually invokes it (test_
diff_budget.py's own pattern).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "blast_radius.py"


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _head(repo):
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def _run(repo, *args):
    return subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=repo, capture_output=True, text=True
    )


@pytest.fixture
def repo(tmp_path):
    """A disposable git repo mirroring the real tree's own layout closely
    enough to exercise every computation: a frozen-surface stand-in
    (harness.py), an unrelated file, an entry-point file (cli/main.py)
    calling live_func, a module with a live and a dead function, a test
    file referencing live_func, a map document referencing live_func, a
    manifest stand-in with a typed field, a pyproject.toml console
    script, and a wheel-smoke stand-in with a pinned MCP tool name."""
    (tmp_path / "src" / "deepreason" / "cli").mkdir(parents=True)
    (tmp_path / "src" / "deepreason" / "rules").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs" / "map").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()

    (tmp_path / "src" / "deepreason" / "harness.py").write_text("class Harness:\n    pass\n")
    (tmp_path / "src" / "deepreason" / "unrelated.py").write_text("VALUE = 1\n")
    (tmp_path / "src" / "deepreason" / "cli" / "main.py").write_text(
        "from deepreason.rules.experiment import live_func\n\n\ndef main():\n    live_func()\n"
    )
    (tmp_path / "src" / "deepreason" / "rules" / "experiment.py").write_text(
        "def live_func():\n    return 1\n\n\ndef dead_func():\n    return 2\n"
    )
    (tmp_path / "src" / "deepreason" / "run_manifest.py").write_text(
        "class RunManifest:\n    schema_version: int\n    engaged_field: str\n"
    )
    (tmp_path / "src" / "deepreason" / "qualification.py").write_text(
        "def qualification_subject_payload(manifest, profile):\n    return manifest\n"
    )
    (tmp_path / "tests" / "test_experiment.py").write_text(
        "from deepreason.rules.experiment import live_func\n"
    )
    (tmp_path / "docs" / "map" / "SUB-fixture.md").write_text(
        "This subsystem calls live_func at its own entry point.\n"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project.scripts]\nfixture-cli = "deepreason.cli.main:main"\n'
    )
    (tmp_path / "scripts" / "wheel_smoke.py").write_text(
        "EXPECTED_MCP_TOOLS = {\"pinned_tool\", \"other_tool\"}\n"
    )

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path, _head(tmp_path)


# ---------------------------------------------------------------------
# Computation 1: frozen-surface contacts
# ---------------------------------------------------------------------


def test_frozen_surface_direct_contact_on_target_file(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--files", "src/deepreason/harness.py")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["result_type"] == "BLAST_RADIUS_RESULT_V1"
    assert data["frozen_surface_verdict"] == "CONTACT"
    direct = [c for c in data["frozen_surface_contacts"] if c["tier"] == "DIRECT"]
    assert direct and direct[0]["target"] == "src/deepreason/harness.py"


def test_frozen_surface_clear_when_no_target_matches(repo):
    """Permanent mutation companion (dr-execute-step 'Durable tests' rule
    3): pins the DIRECT-tier path comparison to an exact match, not a
    substring/prefix match. A mutation that loosens the comparison (e.g.
    `in` instead of `==`) would flag `unrelated.py` too."""
    tmp_path, _base = repo
    result = _run(tmp_path, "--files", "src/deepreason/unrelated.py")
    data = json.loads(result.stdout)
    assert data["frozen_surface_verdict"] == "CLEAR"
    assert data["frozen_surface_contacts"] == []


def test_frozen_surface_symbol_indirect_contact_is_tier_tagged(repo):
    """A symbol referenced inside a frozen-surface file (but not the file
    itself declared as a target) is reported as SYMBOL_INDIRECT, never
    silently merged into DIRECT -- the two tiers carry different
    evidentiary weight and the calling skill must be able to tell them
    apart (SPEC.md Item 1's own honesty rule)."""
    tmp_path, _base = repo
    (tmp_path / "src" / "deepreason" / "harness.py").write_text(
        "class Harness:\n    def apply(self, engaged_field):\n        pass\n"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "reference engaged_field in harness.py")
    result = _run(tmp_path, "--symbols", "engaged_field")
    data = json.loads(result.stdout)
    hits = [c for c in data["frozen_surface_contacts"] if c["target"] == "engaged_field"]
    assert hits and all(h["tier"] == "SYMBOL_INDIRECT" for h in hits)


# ---------------------------------------------------------------------
# Computation 2: reachability
# ---------------------------------------------------------------------


def test_reachability_reachable_for_called_function(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "live_func")
    data = json.loads(result.stdout)
    assert data["reachability"][0]["status_current"] == "REACHABLE"


def test_reachability_unreachable_for_uncalled_function(repo):
    """Permanent mutation companion: pins UNREACHABLE for a function with
    zero call sites from any registered entry-point file. This is the
    exact shape CENSUS.md B4's `property_designer` incident needed a
    human to trace by hand three tranches late."""
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "dead_func")
    data = json.loads(result.stdout)
    assert data["reachability"][0]["status_current"] == "UNREACHABLE"


def test_reachability_unknown_for_unresolvable_symbol_name(repo):
    """A symbol name the static walk cannot resolve to any definition
    (e.g. a role-dispatch string label, not a Python identifier) reports
    UNKNOWN, never guessed as REACHABLE or UNREACHABLE -- the honesty
    rule SPEC.md Item 1 states explicitly."""
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "not_a_real_symbol")
    data = json.loads(result.stdout)
    assert data["reachability"][0]["status_current"] == "UNKNOWN"


def test_reachability_against_ref_flags_newly_live(repo):
    tmp_path, base = repo
    (tmp_path / "src" / "deepreason" / "cli" / "main.py").write_text(
        "from deepreason.rules.experiment import live_func, dead_func\n\n\n"
        "def main():\n    live_func()\n    dead_func()\n"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "wire up dead_func")
    result = _run(tmp_path, "--symbols", "dead_func", "--against", base)
    data = json.loads(result.stdout)
    entry = data["reachability"][0]
    assert entry["status_base"] == "UNREACHABLE"
    assert entry["status_current"] == "REACHABLE"
    assert entry["direction"] == "newly_live"


def test_reachability_against_ref_flags_newly_dead(repo):
    tmp_path, base = repo
    (tmp_path / "src" / "deepreason" / "cli" / "main.py").write_text(
        "def main():\n    pass\n"
    )
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "orphan live_func")
    result = _run(tmp_path, "--symbols", "live_func", "--against", base)
    data = json.loads(result.stdout)
    entry = data["reachability"][0]
    assert entry["status_base"] == "REACHABLE"
    assert entry["status_current"] == "UNREACHABLE"
    assert entry["direction"] == "newly_dead"


# ---------------------------------------------------------------------
# Computation 3: consumers
# ---------------------------------------------------------------------


def test_consumers_tests_hit_appears_and_disappears(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "live_func")
    data = json.loads(result.stdout)
    assert any(t["target"] == "live_func" for t in data["consumers"]["tests"])

    (tmp_path / "tests" / "test_experiment.py").unlink()
    result = _run(tmp_path, "--symbols", "live_func")
    data = json.loads(result.stdout)
    assert data["consumers"]["tests"] == []


def test_consumers_map_checks_hit(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "live_func")
    data = json.loads(result.stdout)
    assert any(t["target"] == "live_func" for t in data["consumers"]["map_checks"])


def test_qualification_digest_confirmed_for_manifest_field(repo):
    """A symbol resolving to a RunManifest field is CONFIRMED, not
    PLAUSIBLE -- qualification_subject_payload hashes the whole manifest
    dump (SPEC.md M2), so any field addition changes the digest
    unconditionally, not merely plausibly."""
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "engaged_field")
    data = json.loads(result.stdout)
    hits = [q for q in data["consumers"]["qualification_digest"] if q["target"] == "engaged_field"]
    assert hits and hits[0]["tier"] == "CONFIRMED"


def test_qualification_digest_confirmed_for_declared_source_file(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--files", "src/deepreason/qualification.py")
    data = json.loads(result.stdout)
    hits = [q for q in data["consumers"]["qualification_digest"] if q["target"] == "src/deepreason/qualification.py"]
    assert hits and hits[0]["tier"] == "CONFIRMED"


def test_wheel_smoke_pin_confirmed_for_console_script(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "main")
    data = json.loads(result.stdout)
    hits = [w for w in data["consumers"]["wheel_smoke_pins"] if w["target"] == "main"]
    assert hits and hits[0]["tier"] == "CONFIRMED" and hits[0]["pin"] == "CONSOLE_ENTRY_POINT"


def test_wheel_smoke_pin_confirmed_for_mcp_tool_name(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "pinned_tool")
    data = json.loads(result.stdout)
    hits = [w for w in data["consumers"]["wheel_smoke_pins"] if w["target"] == "pinned_tool"]
    assert hits and hits[0]["tier"] == "CONFIRMED" and hits[0]["pin"] == "MCP_TOOLS"


# ---------------------------------------------------------------------
# Computation 4: disclosure summary
# ---------------------------------------------------------------------


def test_disclosure_summary_names_the_touched_surface(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--files", "src/deepreason/harness.py")
    data = json.loads(result.stdout)
    assert "harness.py" in data["disclosure_summary"]
    assert "frozen surfaces" in data["disclosure_summary"]


def test_disclosure_summary_states_reachability_is_syntactic_not_provably_exercised(repo):
    """The summary must carry its own honesty limit in-line -- REACHABLE
    means a call path exists, not that it is ever exercised at runtime
    (the exact gap the property_designer incident, CENSUS.md B4, showed
    a pure call-graph check cannot close on its own)."""
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "live_func")
    data = json.loads(result.stdout)
    assert "does not evaluate" in data["disclosure_summary"]


# ---------------------------------------------------------------------
# Exit classes
# ---------------------------------------------------------------------


def test_invalid_invocation_exit_class_when_no_targets_given(repo):
    tmp_path, _base = repo
    result = _run(tmp_path)
    assert result.returncode == 2
    assert result.stdout == ""


def test_evidence_unavailable_exit_class_for_missing_file(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--files", "src/deepreason/does_not_exist.py")
    assert result.returncode == 3
    assert result.stdout == ""


def test_evidence_unavailable_exit_class_for_unresolvable_ref(repo):
    tmp_path, _base = repo
    result = _run(tmp_path, "--symbols", "live_func", "--against", "not-a-real-ref")
    assert result.returncode == 3
    assert result.stdout == ""


def test_self_test_mode_passes():
    result = subprocess.run(
        [sys.executable, str(TOOL), "--self-test"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "SELF-TEST PASS" in result.stdout
