"""Regression (soak-case rot, 2026-09-04): the soak must run everything it
declares, and must say so when it cannot.

Two defects motivated this file, and they compounded. Five of the nine
committed soak cases stopped compiling when the default simulation runner
became the contained one while their builders still pinned the LOCAL
toolchain, so `compile_run_manifest` refused them with
V6_SIMULATION_TOOLCHAIN_REQUIRED. Two of those five -- `pc2` and `pc2b` --
are the only cases in `IN_RUN_EVALUATION_CASES`, the set that carries
assertions A5 and A6. So A5/A6 were emitted by no runnable case at all,
while `assess_run` simply omitted them and exit 0 went on reading as though
the whole instrument had passed.

That is the `docs_verify` fault recurring: an instrument that discards what
it cannot handle reports a green total over a population it never examined
(docs/AUDIT_BASELINES.md, the superseded docs_verify entry).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import cycle_soak  # noqa: E402

from deepreason.v6_policy import engaged_simulation_policy  # noqa: E402


def _root_with_attempt(tmp_path: Path, payload: str) -> Path:
    root = tmp_path / "run"
    directory = root / "objects" / "workflow-provider-attempt-v1"
    directory.mkdir(parents=True)
    (directory / "a.json").write_text(payload)
    (root / "run-status.json").write_text(
        json.dumps({"state": "completed", "stop_reason": "budget_exhausted"})
    )
    return root


def _assert_ids(root: Path, case=None):
    checks = cycle_soak.assess_run(
        root, {"typed_error": None, "terminal": {}}, cycles=8, case=case, criteria=[]
    )
    return {c["id"]: c for c in checks}


# --------------------------------------------------------------------------
# The compile rot itself
# --------------------------------------------------------------------------


@pytest.mark.parametrize("case", sorted(cycle_soak.CASES))
def test_every_committed_soak_case_compiles(case, tmp_path):
    """A case that cannot compile is a case whose assertions never run.

    The soak's own baseline (docs/AUDIT_BASELINES.md) pins only `--case
    epoch3`, so five cases rotted for two months without moving any recorded
    number. This test is what makes that impossible: it compiles every case
    in the registry, not the one the baseline happens to name.
    """
    entry = cycle_soak.CASES[case]
    root = tmp_path / case
    root.mkdir()
    summary = cycle_soak.build_root(entry, root, port=1)
    assert summary["manifest_sha256"]


def test_every_builder_binds_the_toolchain_the_policy_asks_for():
    """The identity must be ASKED FOR, never pinned to one runner.

    `engaged_local_simulation_toolchain()` returns the local id whatever the
    policy wants; `engaged_simulation_toolchain()` follows the runner choice.
    Pinning the first is what rotted -- it kept returning `local` after the
    default became `contained`.
    """
    wanted = engaged_simulation_policy().python_toolchain_identity
    builders = sorted(
        Path("experiments").glob("*/build_manifest*.py")
    )
    assert builders, "no committed manifest builders found"
    offenders = [
        str(path)
        for path in builders
        if "engaged_local_simulation_toolchain()" in path.read_text()
    ]
    assert not offenders, (
        "these builders pin the LOCAL toolchain instead of asking the policy "
        f"(which currently wants {wanted!r}), so they refuse "
        f"V6_SIMULATION_TOOLCHAIN_REQUIRED the moment the default moves: "
        f"{offenders}"
    )


# --------------------------------------------------------------------------
# The silent-omission fault
# --------------------------------------------------------------------------


def test_a5_a6_are_emitted_even_when_the_case_does_not_carry_them(tmp_path):
    """Never omit a declared assertion -- mark it not-applicable instead."""
    root = _root_with_attempt(tmp_path, json.dumps({"data": {"attempt_index": 0}}))
    checks = _assert_ids(root, case=None)
    for identifier in ("A5-in-run-checker-fired",
                       "A6-discharge-channel-carried-them"):
        assert identifier in checks, f"{identifier} vanished from the report"
        assert checks[identifier]["applicable"] is False
        assert "not carried by case" in checks[identifier]["detail"]


def test_the_carrier_cases_actually_evaluate_a5_a6():
    """The not-applicable road must not become the only road.

    If IN_RUN_EVALUATION_CASES ever again names only cases that cannot
    compile, A5/A6 would be permanently not-applicable -- visible, but never
    evaluated. The carriers must exist and must compile.
    """
    assert cycle_soak.IN_RUN_EVALUATION_CASES
    known = set(cycle_soak.CASES)
    assert cycle_soak.IN_RUN_EVALUATION_CASES <= known


def test_non_applicable_assertions_cannot_mask_a_real_failure(tmp_path):
    """A not-applicable row is ok=True; it must never make the verdict green."""
    root = _root_with_attempt(tmp_path, "{ not json")
    checks = list(_assert_ids(root, case=None).values())
    report = {"checks": checks, "seams": [], "status": {}}
    assert cycle_soak._verdict(report) == 1


# --------------------------------------------------------------------------
# A7 -- the record was fully read
# --------------------------------------------------------------------------


def test_a7_is_silent_on_a_readable_record(tmp_path):
    root = _root_with_attempt(tmp_path, json.dumps({"data": {"attempt_index": 0}}))
    assert _assert_ids(root)["A7-record-fully-read"]["ok"] is True


def test_a7_fires_on_a_record_the_readers_cannot_parse(tmp_path):
    """An unreadable record moves every other count in the PASSING direction.

    `attempts_without_complete_lease` can only be raised by a record the
    reader actually read, so dropping unreadable ones silently makes D2 more
    likely to pass, not less.
    """
    root = _root_with_attempt(tmp_path, "{ this is not json")
    check = _assert_ids(root)["A7-record-fully-read"]
    assert check["ok"] is False
    assert "could not be parsed" in check["detail"]


def test_unreadable_records_are_counted_not_dropped(tmp_path):
    root = _root_with_attempt(tmp_path, "{ this is not json")
    facts = cycle_soak._attempt_facts(root)
    assert facts["unreadable_records"] == 1
    assert facts["attempts"] == 0


# --------------------------------------------------------------------------
# Builder isolation -- the silent wrong-shape road
# --------------------------------------------------------------------------


def test_builders_do_not_inherit_another_experiments_sibling_modules(tmp_path):
    """Two cases built in one process must each get their OWN question bytes.

    Three experiment directories define a bare `question.py`, and their
    QUESTION bytes differ. Before builder imports were isolated, the first
    case's `question` module stayed in `sys.modules` and every later case
    silently compiled against it. `pc1` and `pa1` are the sharpest pair: they
    sit in different directories, both import `from question import QUESTION`,
    and their digests differ.
    """
    digests = {}
    for case in ("pa1", "pc1"):
        root = tmp_path / case
        root.mkdir()
        digests[case] = cycle_soak.build_root(
            cycle_soak.CASES[case], root, port=1
        )["manifest_sha256"]
    assert digests["pa1"] != digests["pc1"]


def _experiment_modules() -> set:
    return {n for n, m in sys.modules.items()
            if getattr(m, "__file__", None)
            and "experiments" in str(getattr(m, "__file__"))}


def test_case_module_leaves_no_experiment_module_cached():
    """The eviction is the mechanism; assert it rather than trusting it.

    The cache is cleared FIRST so this cannot pass merely because an earlier
    test in the same session already imported the modules -- a check that can
    only go green is not a check.
    """
    for name in _experiment_modules():
        del sys.modules[name]
    before = _experiment_modules()
    assert not before
    cycle_soak._case_module(cycle_soak.CASES["pc1"])
    leaked = _experiment_modules()
    assert not leaked, f"leaked into sys.modules: {sorted(leaked)}"


def test_case_module_restores_sys_path():
    saved = list(sys.path)
    cycle_soak._case_module(cycle_soak.CASES["pc2b"])
    assert sys.path == saved
