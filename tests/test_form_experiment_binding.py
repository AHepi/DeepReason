"""The experiment's two binding rules, as CHECKS rather than prose (S12.4,
S12.5).

A pre-registration that only states its rules is a document someone can
forget. These two decide whether the later tranche's numbers mean anything, so
they are asserted here and each is shown able to fail.
"""

import importlib.util
import pathlib

import pytest

TRANCHE = (
    pathlib.Path(__file__).resolve().parent.parent
    / "experiments"
    / "2026-09-03-change-conjecturer-pluggable-interface"
)


def _analyse():
    spec = importlib.util.spec_from_file_location(
        "analyse_form_arms", TRANCHE / "analyse_form_arms.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provenance_is_omitted_entirely_and_never_blanked():
    """`docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md` measured that a
    present-but-blank slot draws MORE attention than a filled one, so blanking
    would be worse than not blinding at all. The key must be GONE."""
    analyse = _analyse()
    record = {
        "claim": "the sky view factor sets the gap",
        "layout_id": "seat-pack.conjecturer.legacy-v0",
        "form_id": "conjecturer.turn.v6",
        "shell_id": "seat.conjecturer.legacy-v0",
        "arm": "A1",
    }
    blinded = analyse.blind(record)
    assert blinded == {"claim": "the sky view factor sets the gap"}
    for field in analyse.PROVENANCE_FIELDS:
        assert field not in blinded, field
        assert field not in repr(blinded), field


def test_the_blinding_rule_can_fail():
    """The mutation, permanent rather than performed once: a blinding
    implementation that emptied a field instead of removing it passes any
    "no value leaked" test and fails this one."""
    analyse = _analyse()

    def blanking(record):
        return {
            k: ("" if k in analyse.PROVENANCE_FIELDS else v)
            for k, v in record.items()
        }

    record = {"claim": "x", "layout_id": "L"}
    assert blanking(record) != analyse.blind(record)
    assert "layout_id" in blanking(record)
    assert "layout_id" not in analyse.blind(record)


def test_no_self_reported_number_is_a_declared_measure():
    """S12.5, carried from the diversity tranche's own PREREG: a typicality
    estimate is CONTENT the model wrote, not a measurement of it. The four
    declared measures must all come from committed instruments."""
    prereg = (TRANCHE / "PREREG.md").read_text()
    section = prereg.split("## §6")[1].split("## §7")[0]
    assert "census_conjecturer_failures.py" in section
    assert "analyse.py" in section
    for self_reported in ("typicality", "confidence", "self-report", "self_report"):
        assert self_reported not in section.lower(), self_reported
    assert "No measure is invented here" in prereg


def test_the_analysis_calls_the_committed_instruments_rather_than_copying_them():
    """A second implementation of a measure is a second answer to the same
    question, and the record would then hold two numbers with no way to choose
    between them."""
    source = (TRANCHE / "analyse_form_arms.py").read_text()
    assert "census_conjecturer_failures.py" in source
    assert "2026-08-28-diversity-generation" in source
    # It must not reimplement the diversity measures.
    for reimplementation in ("def distinct_ideas", "def pairwise_distance", "def yield_"):
        assert reimplementation not in source, reimplementation
    assert _analyse().self_test() == 0


def test_the_prereg_declares_a_no_harness_baseline_arm():
    """The operator's standing success law (2026-09-03): success is progress
    over what the same model produces WITHOUT the harness. An experiment with
    no baseline arm cannot measure that, however good its other numbers."""
    prereg = (TRANCHE / "PREREG.md").read_text()
    assert "NO HARNESS" in prereg
    assert "no-harness baseline" in prereg.lower()


def test_the_prereg_says_it_has_not_run():
    """R19's sequence rule: this tranche commits the RECIPE. A pre-registration
    that quietly acquired results would be one written after seeing them."""
    prereg = (TRANCHE / "PREREG.md").read_text()
    assert "NOT RUN" in prereg
    assert "BEFORE any call" in prereg
