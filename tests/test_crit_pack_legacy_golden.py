"""The critic half of the acceptance test this tranche turns on (SPEC S10.4,
§17.3).

Amendment 2 (`REQUEST.md` §1b) made the seat a shell: the same machinery
renders every seat's brief. That is only worth having if it changes nothing
first, so `render_crit_pack` owes the same byte-identical default its
conjecturer sibling owes.

Regression discipline (CHECKLIST step 21): if a fixture stops matching, the
refactor is wrong. The fixture is never edited to make this file pass.
"""

import pathlib

import pytest

from tests.crit_pack_golden_cases import FIXTURE_DIRNAME, render_all

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / FIXTURE_DIRNAME


def _golden(name: str) -> str:
    return (FIXTURES / f"{name}.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rendered() -> dict[str, str]:
    return render_all()


def test_every_committed_fixture_has_a_case_and_the_reverse():
    on_disk = {path.stem for path in FIXTURES.glob("*.txt")}
    assert on_disk == set(render_all()), on_disk


@pytest.mark.parametrize("name", ["minimal", "maximal", "withheld", "legacy_layout"])
def test_the_default_render_is_byte_identical_to_the_committed_golden(
    rendered, name
):
    assert rendered[name] == _golden(name)


def test_the_four_cases_between_them_reach_every_critic_section_slot():
    """A golden that never renders a section cannot notice that section
    changing, so the coverage is asserted rather than assumed."""
    seen = set()
    for text in render_all().values():
        seen.update(
            line[3:] for line in text.splitlines() if line.startswith("## ")
        )
    expected = {
        "problem-context",
        "target-commitments",
        "machine-evaluation-boundary",
        "target",
        "target-support-chain",
        "target-support-content",
        "standing-attacks",
        "frame-crisis",
        "frame-slice",
        "citable-evidence-blocks",
        "premise-invitation",
        "counterexample-recourse",
        "output-contract",
        "context-withheld",
        "question",
    }
    assert expected <= seen, sorted(expected - seen)
    assert any(name.startswith("reference-menu-") for name in seen), sorted(seen)


def test_the_golden_can_fail_on_a_single_character(rendered):
    """The permanent companion mutation (`dr-execute-step`, durable rule 3)."""
    mutated = _golden("maximal").replace("MACHINE", "MACHIME", 1)
    assert mutated != _golden("maximal")
    assert rendered["maximal"] != mutated
