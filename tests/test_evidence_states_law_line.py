"""THE LAW LINE for the evidence-states reading (R3, 2026-09-04).

Stated in `experiments/2026-09-04-change-evidence-states/REQUEST.md` R3 and
repeated here because a test file is where a law becomes falsifiable:

    The reading changes NO admission, rank, immunity or refutation. Nothing in
    `scheduler/`, `adjudication/` or `rules/` may read it.

This is the operator's standing guardrail — "seats change how content is
GENERATED, never what counts as EVIDENCE" (CLAUDE.md) — applied to a reading
that is deliberately downstream of everything. A derived reading that fed back
into admission or rank would be a Status wearing a reader's clothes, and R1's
first four words ("A DERIVED READING, not a new status") would be false.

Pinned in two halves, following `tests/test_successor_law_line.py`, because
each closes a different route in:

1. a SPELLING half — no deciding package names the reading. Cheap; catches the
   careless import. It is a search over source text, so a read spelled without
   one of FORBIDDEN_NAMES would pass it; that is what half 2 is for.
2. a BEHAVIOURAL half — computing the reading appends nothing to the record and
   moves no status label. A reader that wrote, or that re-adjudicated on the
   way past, turns this red however it were spelled.

The WRITER is deliberately not forbidden. `runtime/criticism_dispatch.py` holds
the declaration's signal and its one emitter, and the scheduler imports it to
FILE a declaration — that is the scheduler stating a fact about its own
behaviour, which is the opposite of the scheduler consuming a reading. The two
modules do not import each other, which is what makes the separation checkable
rather than a convention.
"""

from __future__ import annotations

import pathlib

from deepreason.harness import Harness
from deepreason.ontology import Status
from deepreason.views.evidence_states import evidence_state_summary, evidence_states
from tests.conftest import art, attack

#: The operator's own list (R3), neither widened nor narrowed.
DECIDING_PACKAGES = (
    pathlib.Path("src/deepreason/scheduler"),
    pathlib.Path("src/deepreason/adjudication"),
    pathlib.Path("src/deepreason/rules"),
)
PERMITTED: tuple[pathlib.Path, ...] = ()

FORBIDDEN_NAMES = (
    "deepreason.views.evidence_states",
    "evidence_states",
    "evidence_state_summary",
    "EvidenceState",
    "frontier_column",
)

#: The writer, which the scheduler MAY name — it emits, it does not consume.
WRITER_MODULE = "deepreason.runtime.criticism_dispatch"

REPO = pathlib.Path(__file__).resolve().parents[1]
PA2_ROOT = REPO / "experiments/2026-09-02-live-p-a2-corrected/run"


def _imported_modules(path: pathlib.Path) -> set[str]:
    """Every module this file imports, by AST rather than by source text."""

    import ast

    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


# --- half 1: the spelling -------------------------------------------------- #


def test_no_deciding_package_names_the_reading():
    """R3. Every negative check is paired with a POSITIVE ANCHOR on the same
    tree, so a moved or renamed package reddens here rather than making the
    whole test vacuous."""

    anchored = 0
    offenders = []
    for package in DECIDING_PACKAGES:
        files = [p for p in (REPO / package).rglob("*.py") if p not in PERMITTED]
        assert files, package                                  # positive anchor
        anchored += len(files)
        for path in files:
            text = path.read_text()
            for name in FORBIDDEN_NAMES:
                if name in text:
                    offenders.append((str(path.relative_to(REPO)), name))
    assert anchored > 5, anchored                              # positive anchor
    assert not offenders, offenders


def test_the_permitted_exception_list_is_empty_and_that_is_the_claim():
    """Some law lines carve an exception for the package whose act the channel
    IS. This one cannot: no deciding package produces the reading, so there is
    nothing for an exception to be for. Emptiness is the statement."""

    assert PERMITTED == ()


def test_the_reader_and_the_writer_do_not_import_each_other():
    """The separation that lets half 1 hold at all. The scheduler files a
    declaration through the writer; the reader reads what was filed. If the
    reader lived in the writer's module, the scheduler would import the reading
    by transitive necessity and R3 could not be stated."""

    reader = REPO / "src/deepreason/views/evidence_states.py"
    writer = REPO / "src/deepreason/runtime/criticism_dispatch.py"

    # Structure, not source text: the writer's docstring NAMES the reader on
    # purpose (that is what a module is for), and a text search would read
    # prose as coupling.
    assert WRITER_MODULE in _imported_modules(reader)           # positive anchor
    assert "deepreason.views.evidence_states" not in _imported_modules(writer), (
        "the writer imports the reading it is supposed to be independent of"
    )
    assert _imported_modules(writer), "no imports at all — the anchor is dead"


def test_the_scheduler_names_the_writer_and_only_the_writer():
    """The one coupling that is allowed, asserted positively so half 1 cannot
    be satisfied by the scheduler simply having stopped filing declarations."""

    scheduler = (REPO / "src/deepreason/scheduler/scheduler.py").read_text()
    assert WRITER_MODULE in scheduler
    assert "declare_criticism_dispatch" in scheduler


# --- half 2: the behaviour ------------------------------------------------- #


def test_computing_the_reading_appends_nothing_to_the_record(harness):
    """R3, behaviourally. A reading that wrote would be an act, and an act on
    the record is exactly what a derived reading may not be."""

    a = art(harness, "a conjecture")
    attack(harness, a.id, "an attack")
    before = len(list(harness.log.read()))

    evidence_states(harness)
    evidence_state_summary(harness)

    assert len(list(harness.log.read())) == before


def test_computing_the_reading_moves_no_status_label(harness):
    """R3, behaviourally. The reading consumes labels; it may never produce
    one. A reader that re-adjudicated on the way past turns this red."""

    a = art(harness, "a conjecture")
    k, _ = attack(harness, a.id, "an attack")
    attack(harness, k.id, "an attack on the attacker")
    before = dict(harness.state.status)

    evidence_states(harness)
    evidence_state_summary(harness)

    assert dict(harness.state.status) == before
    assert before[a.id] == Status.ACCEPTED                      # positive anchor


def test_computing_the_reading_over_a_committed_root_appends_nothing():
    """The same guarantee where it actually matters: a committed root is
    evidence, and a writable pass over one repairs — that is, destroys — it."""

    harness = Harness(PA2_ROOT, read_only=True)
    before = len(list(harness.log.read()))
    assert before > 0                                           # positive anchor

    evidence_state_summary(harness)

    assert len(list(Harness(PA2_ROOT, read_only=True).log.read())) == before
