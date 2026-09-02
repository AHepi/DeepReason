"""Regression (poietics P-R1 run-1b31f006, and selfstudy run-9175f0ec before it):
import-role admission records must never be counted as survivors.

`run-9175f0ec` installed the rule in `Scheduler._select_problem` only. Twelve
months of surfaces later, `run-1b31f006` -- the first run in this repository to
bind a non-empty dossier at seed -- published **82 survivors, 24 of them
IMPORT-role sections of the operator's own attached record**, every one of them
registered at log seq 5-40 while the log's first LLM-bearing event is seq 85.
They survived no criticism; there was none yet to survive.

These tests read the COMMITTED root read-only and construct nothing: the
evidence is the run, not a fixture that agrees with the fix. Each is skipped,
never silently passed, if the root is absent from the checkout.
"""
from __future__ import annotations

import inspect
import json
import pathlib
from pathlib import Path

import pytest

from deepreason.application.results import results_summary
from deepreason.harness import Harness
from deepreason.ontology.artifact import ProvenanceRole
from deepreason.ontology.state import Status, counts_as_survivor, is_import_admission

ROOT = Path(__file__).resolve().parents[1] / "experiments" / "2026-08-25-poietics-program" / "run"


def _root() -> Path:
    if not (ROOT / "run-result.json").is_file():
        pytest.skip(f"committed evidence root absent from this checkout: {ROOT}")
    return ROOT


@pytest.fixture(scope="module")
def state():
    return Harness(_root(), read_only=True).state


@pytest.fixture(scope="module")
def stored() -> list[str]:
    return json.loads((_root() / "run-result.json").read_text())["survivors"]


def test_the_committed_record_still_carries_the_defect_it_was_recorded_for(state, stored):
    """The evidence, asserted so the later tests cannot pass vacuously.

    If the root ever stopped carrying import-role members, every assertion
    below would hold for a reason that has nothing to do with the fix.
    """

    imports = [a for a in stored if state.artifacts[a].provenance.role == ProvenanceRole.IMPORT]
    assert len(stored) == 82, "the root's own published survivor set is not edited by a fix"
    assert len(imports) == 24
    assert len({a for a in stored} - {a for a in imports}) == 58


def test_the_results_surface_reports_the_conjectures_and_not_the_dossier(state, stored):
    """`deepreason results` must report 58, not 82, for run-1b31f006."""

    summary = results_summary(_root())
    assert summary["artifacts"]["survivor_count"] == 58
    counted = {a for a in stored if not is_import_admission(state, a)}
    assert len(counted) == summary["artifacts"]["survivor_count"]
    # Set identity, not a count: an off-by-one that dropped the wrong artifact
    # would satisfy `== 58` and be a different, worse defect.
    assert counted == {
        a for a in stored if state.artifacts[a].provenance.role != ProvenanceRole.IMPORT
    }
    assert {a for a in stored} - counted == {
        a for a in stored if state.artifacts[a].provenance.role == ProvenanceRole.IMPORT
    }


def test_the_writer_publishes_a_survivor_set_the_invariant_already_holds_over(state):
    """`run_report` is tested apart from the reader: fixing one proves nothing
    about the other, and the reader can only subtract from what this writes."""

    from deepreason.config import Config
    from deepreason.scheduler.scheduler import run_report

    report = run_report(Harness(_root(), read_only=True), Config())
    assert len(report["survivors"]) == 58
    assert not [
        a for a in report["survivors"]
        if state.artifacts[a].provenance.role == ProvenanceRole.IMPORT
    ]
    # Every dropped id was ACCEPTED: the rule that removed it is the role
    # clause, never an accidental status filter.
    dropped = {a for a, _ in state.addr if state.status.get(a) == Status.ACCEPTED} - set(
        report["survivors"]
    )
    assert len(dropped) == 24
    assert all(state.status.get(a) == Status.ACCEPTED for a in dropped)


def test_the_frontier_does_not_move_because_every_dropped_member_was_dominated(state):
    """Excluding the 24 IMPORT records does not reshape the frontier: the real
    artifacts retained are the same set whether or not the imports are scored
    alongside them.

    Stated as that comparison rather than as "the re-derived frontier equals the
    one this root published" (its form until 2026-09-02), because the second is
    not the claim and was hostage to every later scoring change. It broke on the
    first one: since `experiments/2026-09-02-defect-coverage-pending-commitments/`
    a commitment that evaluates OVERRUN leaves the coverage denominator, the
    published frontier of this root re-derives to 58 rather than the 40 stored in
    its `run-result.json`, and 12 of these 24 imports -- which carry evaluable
    commitments that all evaluate OVERRUN -- would no longer be dominated points
    at all. The premise in the old docstring is therefore gone; the claim is not,
    and a stored result owes a later reader no agreement (operator law
    2026-08-14). None of it reaches production: `run_report` scores only
    `counts_as_survivor` members, and imports are never among them."""

    from deepreason.capture.pareto import frontier
    from deepreason.config import Config
    from deepreason.scheduler.scheduler import pareto_scores, run_report

    harness = Harness(_root(), read_only=True)
    config = Config()
    published = json.loads((_root() / "run-result.json").read_text())
    imports = [
        a for a in published["survivors"]
        if state.artifacts[a].provenance.role == ProvenanceRole.IMPORT
    ]
    assert len(published["frontier"]) == 40, "a fix never edits a committed root"
    assert imports, "setup: the root must still carry the members being dropped"

    retained = list(run_report(harness, config)["frontier"])
    assert not set(retained) & set(imports), "an import reached the reported frontier"

    scored = sorted(set(retained) | set(imports))
    with_imports = frontier([(a, pareto_scores(harness, a)) for a in scored], config.PARETO_AXES)
    assert sorted(set(with_imports) - set(imports)) == sorted(retained), (
        "scoring the imports alongside the survivors changes which real "
        "artifacts are retained -- the exclusion is reshaping the frontier"
    )
    assert not [a for a in imports if a in state.hv or a in state.reach]


def test_one_authority_names_the_rule_and_every_survivor_surface_calls_it():
    """The property that would decay. Three consumers spelled the rule out
    themselves once; two agreed and one did not, and nothing could tell."""

    from deepreason.application import results as results_module
    from deepreason.scheduler.scheduler import Scheduler, run_report

    for site in (inspect.getsource(Scheduler._select_problem), inspect.getsource(run_report)):
        assert "counts_as_survivor" in site
    assert "is_import_admission" in inspect.getsource(results_module._survivor_count)
    # Named once, in `ontology.state`. A consumer that re-spells it is a
    # second authority, which is the defect this tranche fixed.
    for module in (Scheduler, results_module):
        assert "ProvenanceRole.IMPORT" not in pathlib.Path(inspect.getfile(module)).read_text()


def test_the_predicate_admits_every_conjecture_survivor_unchanged(state):
    """The rule is a no-op where no dossier was attached: a run with no
    import-role artifact must report exactly what it reported before."""

    conjectures = [
        a for a, _ in state.addr
        if state.status.get(a) == Status.ACCEPTED
        and state.artifacts[a].provenance.role != ProvenanceRole.IMPORT
    ]
    assert len(conjectures) == 58
    assert all(counts_as_survivor(state, a) for a in conjectures)
    assert not any(is_import_admission(state, a) for a in conjectures)
