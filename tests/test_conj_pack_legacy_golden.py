"""The acceptance test the pluggable-brief tranche turns on (SPEC S10.4).

`render_conj_pack` must return the SAME BYTES after the renderer becomes a
walk over registered section plugins as it returned before, for every input
shape the brief can take. Nothing changes unless someone configures it -- that
is the operator's "configurable with defaults" (`R11`) made checkable, and it
is the only evidence that twenty mechanical extractions extracted the text
rather than rewriting it.

Regression discipline (experiments/2026-09-03-change-conjecturer-pluggable-
interface/CHECKLIST.md step 15): if a fixture stops matching, the refactor is
wrong. The fixture is never edited to make this file pass.
"""

import pathlib

import pytest

from tests.conj_pack_golden_cases import FIXTURE_DIRNAME, render_all

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / FIXTURE_DIRNAME


def _golden(name: str) -> str:
    return (FIXTURES / f"{name}.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rendered() -> dict[str, str]:
    return render_all()


def test_every_committed_fixture_has_a_case_and_the_reverse():
    """A case with no fixture proves nothing, and a fixture with no case is a
    file no failure can reach."""
    on_disk = {path.stem for path in FIXTURES.glob("*.txt")}
    assert on_disk == set(render_all()), on_disk


@pytest.mark.parametrize(
    "name", ["minimal", "maximal", "withheld", "legacy_layout", "superseded"]
)
def test_the_default_render_is_byte_identical_to_the_committed_golden(
    rendered, name
):
    assert rendered[name] == _golden(name)


def test_the_five_cases_between_them_reach_every_section_slot():
    """A golden that never renders a section cannot notice that section
    changing, so the coverage is asserted rather than assumed."""
    seen = set()
    for text in render_all().values():
        seen.update(
            line[3:] for line in text.splitlines() if line.startswith("## ")
        )
    expected = {
        "problem",
        "criteria",
        "open-criticisms",
        "mandatory-interface",
        "active-properties",
        "school-stance",
        "experimental-generation-context",
        "scratch-advisory-context",
        "frozen-evidence-context",
        "citable-evidence-blocks",
        "capability-result-context",
        "frame-crisis",
        "frame-slice",
        "neighbourhood",
        "live-neighbourhood",
        "superseded-conjectures",
        "crossover",
        "complement-directive",
        "diversity-specifications",
        "output-contract",
        "context-withheld",
        "question",
    }
    assert expected <= seen, sorted(expected - seen)
    assert any(name.startswith("reference-menu-") for name in seen), sorted(seen)


def test_the_golden_can_fail_on_a_single_character(rendered):
    """The permanent companion mutation (`dr-execute-step`, durable rule 3):
    an equality test with no proof it can fail is not a check."""
    mutated = _golden("maximal").replace("PROBLEM p-golden", "PROBLEM q-golden", 1)
    assert mutated != _golden("maximal")
    assert rendered["maximal"] != mutated
