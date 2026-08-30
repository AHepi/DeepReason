"""The successor-destination registry is a CONTRACT, not a wiring.

The operator's modularity law (2026-08-26) and the P9 law (2026-08-29) meet
here: "The scratch pad option must function like a plugin that allows for
movement elsewhere as well. Again, the modularity thing and Max config thing."
"Enforced" means a check that can FAIL, so these are the four properties that
make the registry a plugin point rather than a promise about future authors:

1. a declaration carries no number, so there is no weight for any
   configuration to set;
2. an unknown selector FALLS BACK and DISCLOSES, and never raises
   (the all-configurations law applied to a selector);
3. ADDING a destination costs a registration and NO consumer edit -- proved by
   registering a throw-away row in-test and routing to it through the public
   interface alone;
4. no consumer branches on WHICH row it got -- the producer-agnostic rule
   (`DR-INV-signal-contract`: "a consumer that needs to know the producer has
   left the contract").

Property 3 is the one that would silently rot: it stays true only while
`route` dispatches through the registered writer instead of naming a row.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from deepreason.harness import Harness
from deepreason.successor import (
    DESTINATIONS,
    SUCCESSOR_DESTINATION_REGISTRY_VERSION,
    resolve,
    route,
    unknown_destination_notices,
)
from deepreason.successor.registry import (
    GATES,
    SuccessorDeclaration,
    declaration_field_types,
    register_destination,
    unregister_destination,
)

SRC = pathlib.Path("src/deepreason")


class _Selects:
    """A configuration that names one destination and nothing else."""

    def __init__(self, destination_id):
        self.SUCCESSOR_QUESTION_DESTINATION = destination_id


class _Defaults:
    """A configuration that names nothing at all."""


# --- 1: no number on a declaration ----------------------------------------- #


def test_no_declaration_field_is_numeric():
    """Checked over the MODEL, not over today's rows: a row registered by a
    future setup cannot introduce a weight the model does not allow."""
    numeric = [
        name
        for name, annotation in declaration_field_types().items()
        if annotation in (int, float)
    ]
    assert not numeric, numeric
    assert declaration_field_types(), "the model has no fields at all"  # anchor


def test_the_registry_is_versioned_as_a_whole():
    """The VERSIONED layer of the signal contract: what the rows MEAN moves
    under a version, while which row a run picks is free configuration."""
    assert isinstance(SUCCESSOR_DESTINATION_REGISTRY_VERSION, str)
    assert SUCCESSOR_DESTINATION_REGISTRY_VERSION.strip()
    assert SUCCESSOR_DESTINATION_REGISTRY_VERSION.endswith(".v1")


def test_exactly_one_destination_is_the_shipped_default():
    """A registry with two defaults, or none, cannot answer "where does an
    unconfigured question go?" -- which is the question the law asks."""
    defaults = [row.id for row in DESTINATIONS.values() if row.default]
    assert defaults == ["scratchpad.v1"], defaults
    assert resolve(_Defaults()).id == "scratchpad.v1"


# --- 2: unknown falls back and discloses ----------------------------------- #


def test_an_unknown_selector_falls_back_and_discloses_exactly_once():
    """Disclose, never die. A configuration naming a destination that does not
    exist still compiles, still runs, and carries a notice saying so."""
    config = _Selects("no-such-destination.v9")
    assert resolve(config).id == "scratchpad.v1"
    notices = unknown_destination_notices(config)
    assert len(notices) == 1, notices
    assert notices[0].code == "SUCCESSOR_DESTINATION_UNKNOWN"
    assert "no-such-destination.v9" in notices[0].message
    assert "scratchpad.v1" in (notices[0].resolution or "")
    assert unknown_destination_notices(_Defaults()) == ()


def test_an_unknown_selector_never_raises_on_the_routing_path(tmp_path):
    """The point of use is where an impossibility surfaces, and this one is not
    an impossibility at all: an unknown id routes to the shipped default."""
    harness = Harness(tmp_path / "run")
    written = route(
        harness, _Selects("no-such-destination.v9"),
        problem_id="p-1", question="what should be asked next?",
    )
    assert written is not None
    assert len(harness.scratch_state.blocks) == 1


# --- 3: adding a row costs a registration and no consumer edit ------------- #


def test_adding_a_destination_requires_no_edit_to_any_consumer(tmp_path):
    """THE modularity claim, made failable.

    A throw-away row is registered with its own writer and reached through the
    public interface alone. Nothing in `route` is touched, and nothing in this
    test names the shipped scratchpad row -- so if `route` ever grew a branch
    on which row it got, this would be the test that could not be written.
    """
    harness = Harness(tmp_path / "run")
    seen = []

    def writer(harness, config, *, problem_id, question, llm_call=None):
        seen.append((problem_id, question))
        return "written-elsewhere"

    row = SuccessorDeclaration(
        id="test-sink.v1",
        routes="a test-local sink that records what it was handed",
        default=False,
        enforcement="tests/test_successor_registry.py",
        authority="this test",
    )
    register_destination(row, writer)
    try:
        config = _Selects("test-sink.v1")
        assert resolve(config).id == "test-sink.v1"
        assert unknown_destination_notices(config) == ()
        out = route(harness, config, problem_id="p-1", question="what next?")
        assert out == "written-elsewhere"
        assert seen == [("p-1", "what next?")]
        # The workshop was NOT written to: movement elsewhere means elsewhere.
        assert harness.scratch_state.blocks == {}
    finally:
        unregister_destination("test-sink.v1")
    assert "test-sink.v1" not in DESTINATIONS


def test_a_declared_row_with_no_writer_discloses_instead_of_crashing(tmp_path):
    """A row may be DECLARED before anything can serve it -- the declaration is
    the versioned contract, the writer is ordinary code implementing it. That
    gap is disclosed at the point of use rather than hidden."""
    harness = Harness(tmp_path / "run")
    register_destination(
        SuccessorDeclaration(
            id="declared-only.v1", routes="declared, unserved", default=False,
            enforcement="none yet", authority="this test",
        )
    )
    try:
        out = route(
            harness, _Selects("declared-only.v1"),
            problem_id="p-1", question="what next?",
        )
        assert out is None
        assert harness.scratch_state.blocks == {}
    finally:
        unregister_destination("declared-only.v1")


def test_the_shipped_default_cannot_be_unregistered():
    """A registry with no fallback turns an unknown selector from a disclosure
    into a failure, which is the one thing the all-configurations law forbids."""
    with pytest.raises(ValueError):
        unregister_destination("scratchpad.v1")
    assert "scratchpad.v1" in DESTINATIONS


# --- 4: no consumer branches on which row it got --------------------------- #


def _row_ids() -> set[str]:
    return {*DESTINATIONS, *GATES}


def test_no_module_compares_against_a_registered_row_id():
    """The producer-agnostic rule, as an ABSENCE over the whole tree.

    A consumer that asks "is this the scratchpad row?" has stopped consuming
    the interface and started knowing the subsystem, and the next destination
    would have to teach it about itself. Paired with two POSITIVE ANCHORS so a
    broken walker fails loudly instead of passing vacuously.
    """
    ids = _row_ids()
    assert ids, "the registry is empty"                       # positive anchor
    compares = 0
    scanned = 0
    offenders = []
    for path in SRC.rglob("*.py"):
        scanned += 1
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            compares += 1
            operands = [node.left, *node.comparators]
            for operand in operands:
                if isinstance(operand, ast.Constant) and operand.value in ids:
                    offenders.append((str(path), node.lineno, operand.value))
    assert scanned > 200, scanned                             # positive anchor
    assert compares > 100, compares                           # positive anchor
    assert not offenders, offenders


def test_a_row_id_literal_appears_in_the_registry_and_nowhere_else():
    """The blunter half of the same rule, and the one that catches a lookup
    keyed on a hard-coded id rather than a comparison against one."""
    for row_id in sorted(_row_ids()):
        holders = sorted(
            str(p) for p in SRC.rglob("*.py") if row_id in p.read_text(encoding="utf-8")
        )
        assert holders == ["src/deepreason/successor/registry.py"], (row_id, holders)
