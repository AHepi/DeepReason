"""The signal registry is a CONTRACT, not a wiring.

Regression (v2 calculus program, Rung 1b-i): the operator's design law
(CLAUDE.md, 2026-08-14) says a signal is anything DECLARING a name, a unit,
producer-agnostic semantics, and a staleness bound, and that new setups add
signals by declaration through this typed channel -- never by teaching a
consumer about a subsystem.

These tests pin the three properties that make that a contract rather than a
convention: the declaration is complete, the public registry cannot drift from
it, and the pre-contract migration debt can only shrink.
"""

import ast
import pathlib
import typing

import pytest

from deepreason import signals
from deepreason.signals import (
    PREFIXES,
    PREFIX_DECLARATIONS,
    SIGNALS,
    SIGNAL_DECLARATIONS,
    SignalDeclaration,
    declaration,
    unspecified_declarations,
)


# Every entry that existed before the contract. The number is allowed to fall
# and never to rise; see test_the_migration_debt_can_only_shrink.
MIGRATION_DEBT = 89


def test_every_declaration_is_complete():
    """Four fields, all present, all non-empty."""
    for name, d in {**SIGNAL_DECLARATIONS, **PREFIX_DECLARATIONS}.items():
        assert d.name == name
        assert d.semantics.strip(), name
        assert d.unit, name
        assert d.staleness, name


def test_the_public_registry_is_derived_and_cannot_drift():
    """SIGNALS/PREFIXES are views of the declarations, not a second copy.

    Two hand-maintained copies of the same fact is how a registry stops being a
    contract; the derived view is what makes drift impossible rather than
    merely discouraged.
    """
    assert SIGNALS == {n: d.semantics for n, d in SIGNAL_DECLARATIONS.items()}
    assert PREFIXES == {n: d.semantics for n, d in PREFIX_DECLARATIONS.items()}


def test_the_migration_debt_can_only_shrink():
    """`unspecified` is an honest marker for signals whose author stated no
    unit, not a default a NEW signal may take.

    A new signal declared `unspecified` raises this count and fails here, which
    is what makes the contract binding for new setups while leaving the
    migrated entries truthfully marked.
    """
    debt = unspecified_declarations()
    assert len(debt) <= MIGRATION_DEBT, (
        f"{len(debt)} unspecified declarations, was {MIGRATION_DEBT}: a NEW "
        f"signal must declare its unit and staleness. Added: "
        f"{sorted(set(debt))[:5]}"
    )


def test_the_vocabularies_are_closed():
    """Unit and staleness are closed sets: an open string is not a contract."""
    units = set(typing.get_args(signals.Unit))
    staleness = set(typing.get_args(signals.Staleness))
    assert "unspecified" in units and "unspecified" in staleness
    for d in {**SIGNAL_DECLARATIONS, **PREFIX_DECLARATIONS}.values():
        assert d.unit in units, d
        assert d.staleness in staleness, d


def test_an_incomplete_declaration_is_refused():
    with pytest.raises(ValueError):
        SignalDeclaration(name="x", unit="event", semantics="", staleness="run")


def test_declaration_resolves_exactly_then_by_longest_prefix():
    exact = next(iter(SIGNAL_DECLARATIONS))
    assert declaration(exact) is SIGNAL_DECLARATIONS[exact]
    prefix = next(iter(PREFIX_DECLARATIONS))
    assert declaration(prefix + "whatever-follows") is PREFIX_DECLARATIONS[prefix]
    assert declaration("no-such-signal-anywhere") is None


# --- interface-only consumption (SC-3) -------------------------------------

FORBIDDEN_FOR_THE_CONTROLLER = ("schools", "rules", "informal", "capture")


def test_the_allocation_controller_consumes_only_the_interface():
    """The controller may not import schools / rules / criticism internals.

    This passes on the tree as it stands -- `controller.py` imports only
    `deepreason.ontology` -- so its value is not that it turns anything green
    today. It is that it FAILS the day someone reaches around the signal
    interface into a subsystem, which is the exact move the operator's clause
    (3) exists to prevent: "never by teaching a consumer about a subsystem".
    """
    source = pathlib.Path(signals.__file__).parent / "controller.py"
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source.read_text())):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    reached = sorted(
        m for m in imported
        if m.startswith("deepreason.")
        and m.split(".")[1] in FORBIDDEN_FOR_THE_CONTROLLER
    )
    assert not reached, (
        f"controller.py reaches into {reached}; allocation must consume the "
        f"signal interface only"
    )
