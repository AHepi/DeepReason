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


def test_both_receipt_families_are_declared_signals():
    """The VERSIONED layer's other half: the two receipts this channel emits
    are DECLARED in `signals.py`, not merely recorded.

    `DR-CON-successor-questions` states this as an invariant ("its receipts are
    declared signals with a real unit and a real staleness") and nothing was
    failing when both declarations were deleted -- the emitters kept emitting
    and every test stayed green. So the EXISTENCE of each declaration is pinned
    here, keyed off the emitters' own constants so a renamed receipt cannot
    drift away from the row that gives it meaning.

    `unspecified` is the contract's own word for "predates this discipline" and
    is rejected on both fields: a declaration that carries it is the absence
    this test exists to catch, wearing a row.
    """
    from deepreason.signals import declaration
    from deepreason.successor.mint import MINT_RECEIPT
    from deepreason.successor.route import RECEIPT_PREFIX

    # The prefix family, resolved through each of its three dispositions --
    # every one must land on the SAME declared row, not on some longer prefix
    # that happens to match.
    for disposition in ("ROUTED", "UNAVAILABLE", "UNLINKED"):
        found = declaration(RECEIPT_PREFIX + disposition)
        assert found is not None, RECEIPT_PREFIX + disposition
        assert found.name == RECEIPT_PREFIX, (disposition, found.name)
        assert found.unit and found.unit != "unspecified", found.unit
        assert found.staleness and found.staleness != "unspecified", found.staleness

    minted = declaration(MINT_RECEIPT)
    assert minted is not None, MINT_RECEIPT
    assert minted.name == MINT_RECEIPT, minted.name
    assert minted.unit and minted.unit != "unspecified", minted.unit
    assert minted.staleness and minted.staleness != "unspecified", minted.staleness

    # The gate-warning family (Q2 road B). Added 2026-08-30 because deleting
    # its declaration outright left every signal test GREEN -- nothing in the
    # repo asserts that an EMITTED receipt tag is declared, so a channel's own
    # tests are the only place that property can be pinned. Recorded as a
    # general gap in DELIVERY.md rather than closed repo-wide here.
    from deepreason.successor.mint import GATE_WARNING_RECEIPT

    gate = declaration(GATE_WARNING_RECEIPT)
    assert gate is not None, GATE_WARNING_RECEIPT
    assert GATE_WARNING_RECEIPT.startswith(gate.name), (GATE_WARNING_RECEIPT, gate.name)
    assert gate.unit and gate.unit != "unspecified", gate.unit
    assert gate.staleness and gate.staleness != "unspecified", gate.staleness

    # The dispatcher's two families (Q3 road B): the per-proposal disposition
    # and the per-call bookkeeping receipt that keeps the walk from being
    # quadratic. Both are EMITTED, so both must be DECLARED.
    from deepreason.successor.reader import (
        CALL_FINISHED_RECEIPT,
        DISPATCH_RECEIPT_PREFIX,
    )

    for disposition in ("ROUTED", "ROUTED_TARGET_UNRESOLVED", "UNLINKED"):
        found = declaration(DISPATCH_RECEIPT_PREFIX + disposition)
        assert found is not None, DISPATCH_RECEIPT_PREFIX + disposition
        assert found.name == DISPATCH_RECEIPT_PREFIX, (disposition, found.name)
        assert found.unit and found.unit != "unspecified", found.unit
        assert found.staleness and found.staleness != "unspecified", found.staleness

    done = declaration(CALL_FINISHED_RECEIPT)
    assert done is not None, CALL_FINISHED_RECEIPT
    assert done.name == CALL_FINISHED_RECEIPT, done.name
    assert done.unit and done.unit != "unspecified", done.unit
    assert done.staleness and done.staleness != "unspecified", done.staleness


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

    Two spellings, because a literal check caught only one of them: the row id
    written out, and the registry's own exported id CONSTANT, which `route.py`
    already imports. Comparing against `DEFAULT_DESTINATION_ID` is the same
    offence with better manners. `registry.py` is exempt -- it owns the rows,
    and its `unregister_destination` legitimately compares against the default.
    """
    ids = _row_ids()
    assert ids, "the registry is empty"                       # positive anchor
    constants = {"DEFAULT_DESTINATION_ID", "MINTING_GATE_ID"}
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
                if (
                    isinstance(operand, ast.Name)
                    and operand.id in constants
                    and path.name != "registry.py"
                ):
                    offenders.append((str(path), node.lineno, operand.id))
    assert scanned > 200, scanned                             # positive anchor
    assert compares > 100, compares                           # positive anchor
    assert not offenders, offenders


def test_route_reaches_even_the_shipped_default_through_the_registry(
    tmp_path, monkeypatch
):
    """The producer-agnostic rule as BEHAVIOUR, not as an absence.

    The two source checks in this section are absences over the tree, and an
    absence is only as good as the spellings it knows: a split literal, an
    aliased import, a comparison against the exported constant. This one asks
    what `route` DOES. Every dispatch goes through `writer_for`, the shipped
    default included, so replacing that lookup with a spy must divert the
    default route too. A `route` that served the scratchpad row from a branch
    of its own would never consult the spy, and the real scratch block it wrote
    instead would show up in `scratch_state`.
    """
    from importlib import import_module

    route_module = import_module("deepreason.successor.route")
    asked = []

    def _sentinel(harness, config, *, problem_id, question, llm_call=None):
        return "served-through-the-registry"

    def _spy(destination_id):
        asked.append(destination_id)
        return _sentinel

    monkeypatch.setattr(route_module, "writer_for", _spy)

    harness = Harness(tmp_path / "run")
    default_id = resolve(_Defaults()).id
    out = route(harness, _Defaults(), problem_id="p-1", question="what next?")

    assert asked == [default_id], asked
    assert out == "served-through-the-registry", out
    assert harness.scratch_state.blocks == {}


def test_a_row_id_literal_appears_in_the_registry_and_nowhere_else():
    """The blunter half of the same rule, and the one that catches a lookup
    keyed on a hard-coded id rather than a comparison against one."""
    for row_id in sorted(_row_ids()):
        holders = sorted(
            str(p) for p in SRC.rglob("*.py") if row_id in p.read_text(encoding="utf-8")
        )
        assert holders == ["src/deepreason/successor/registry.py"], (row_id, holders)


def test_the_declared_interface_is_exactly_seven_names():
    """Regression (audit F29): the `__all__` tuple was documented as pinned by
    this file and was not; a mutation dropping two names left all 42 tests of
    the tranche green, and only docs_verify would have caught it.

    Six until 2026-08-30, when Q3 road B added the production entry
    `dispatch_recorded_proposals`. A name a production caller uses belongs in
    the contract, not beside it.
    """
    import deepreason.successor as s

    assert set(s.__all__) == {
        "DESTINATIONS",
        "SUCCESSOR_DESTINATION_REGISTRY_VERSION",
        "dispatch_recorded_proposals",
        "mint",
        "resolve",
        "route",
        "unknown_destination_notices",
    }, s.__all__
    assert len(s.__all__) == 7, s.__all__


def test_every_gate_row_names_a_real_config_field():
    """Regression (audit F12, parked as P9B-8, unblocked by the 2026-08-30
    frozen-surface-4 grant): the shipped `minting.v1` row declared an
    `enforcement` naming `Config.SUCCESSOR_MINTING_ENABLED`, an attribute
    `Config` did not carry and — forbidding extras — could not be given. The
    string was true of nothing, and `enforcement` is the field whose whole job
    is to say where a row is actually READ, so a declaration could claim a
    switch no consumer consults.

    Parked rather than fixed at delivery for a stated reason: the natural check
    could not PASS while no successor `Config` field existed, and writing a
    check that must fail — or weakening it until it passes — would both have
    been worse than recording the gap. The grant lands the fields, so the check
    lands in the SAME commit, which is what `PARKED.md` P9B-8 requires.

    GATE rows only. A destination row's `enforcement` names a call chain
    (`route -> ScratchService.create_block`), not a field, so applying this to
    `DESTINATIONS` would assert something that was never claimed.
    """
    from deepreason.config import Config
    from deepreason.successor.registry import GATES

    for row in GATES.values():
        named = [w.strip(".,;'\"()") for w in row.enforcement.split()]
        fields = [w for w in named if w.isupper() and "_" in w]
        assert fields, (row.id, "a gate row must name the Config field it reads")
        for field in fields:
            assert field in Config.model_fields, (row.id, field)


def test_both_switches_are_real_config_surface_and_not_a_getattr_default():
    """The grant's behavioural half: before it, `Config` forbade extras and
    carried no successor field, so a real run could not CHANGE either default —
    only a duck-typed stub could (audit F16). R4's per-run switch and R6's
    configurable surface were parked on exactly this.

    Both halves are asserted: the SHIPPED defaults are unchanged (scratchpad,
    minting off), and a run that sets each field is actually read by the
    registry's own two consumers rather than falling through to the row
    default.
    """
    from deepreason.config import Config
    from deepreason.successor.registry import (
        DEFAULT_DESTINATION_ID,
        SuccessorDeclaration,
        minting_enabled,
        register_destination,
        resolve,
        unregister_destination,
    )

    assert Config().SUCCESSOR_QUESTION_DESTINATION == DEFAULT_DESTINATION_ID
    assert Config().SUCCESSOR_MINTING_ENABLED is False
    assert resolve(Config()).id == DEFAULT_DESTINATION_ID
    assert minting_enabled(Config()) is False

    on = Config().model_copy(update={"SUCCESSOR_MINTING_ENABLED": True})
    assert minting_enabled(on) is True

    register_destination(
        SuccessorDeclaration(
            id="elsewhere.v1",
            routes="a registered alternative, for this test only",
            default=False,
            enforcement="deepreason.successor.route.route",
            authority="test fixture",
        )
    )
    try:
        aimed = Config().model_copy(
            update={"SUCCESSOR_QUESTION_DESTINATION": "elsewhere.v1"}
        )
        assert resolve(aimed).id == "elsewhere.v1"
    finally:
        unregister_destination("elsewhere.v1")
