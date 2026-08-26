"""The discharge channel is a CONTRACT, not a wiring (REBUILD F1, R12-R15).

The operator's modularity law (CLAUDE.md, 2026-08-26): "There needs to be a
priority that enforces modularity. Customisation needs to be easy." Bound to
this tranche in REQUEST.md Amendment 1: "the discharge policy (kinds, the
re-ask behavior, the disclosure road) is a registered, config-selectable
policy -- new discharge kinds enter by declaration, not by editing the
submission path", and "you ship an ARCHITECTURE TEST that goes RED when a
consumer bypasses the interface -- a modularity claim without a failable
check is decoration".

This file is that check. Four properties, each of which can fail:

1. no consumer reaches past `deepreason.discharge` into a submodule;
2. the package itself consumes only what it declares -- it cannot learn about
   packs, rules, adjudication or the scheduler;
3. a FOURTH discharge kind reaches the wire, the screen and the render by
   DECLARATION ALONE, with the three consumer files unedited;
4. turning the channel on and changing a cap are pure configuration.

Property 3 is the load-bearing one and the reason this file exists rather than
a sentence in a design document: it is the exact move the law forbids -- adding
a kind by editing the submission path -- made mechanically detectable.
"""

import ast
import pathlib

import pytest

from deepreason.config import Config
from deepreason.discharge import (
    DISCHARGE_KIND_DECLARATIONS,
    DischargeKindDeclaration,
    discharge_kind_names,
    resolve_policy,
)
from deepreason.discharge.policy import KINDS

# `render_open_criticism_context`, `open_criticisms` and `screen_submission`
# are imported INSIDE the tests that use them, not here. Not style: this file
# is written before them and must stay collectable while they land, so that
# the checks it CAN make are running from the first step rather than waiting
# for the last. Importing `deepreason.discharge.policy` for `KINDS` is the one
# deliberate exception to this file's own interface rule -- `KINDS` is the
# DERIVED view whose agreement with the registry is the thing under test, and
# a test of a derivation has to be able to see both sides of it.

SRC = pathlib.Path("src/deepreason")
PACKAGE = SRC / "discharge"

# The three files that would have to be edited if a kind were NOT a
# declaration. Named here once so property 3 and its companion cannot drift
# apart into two lists of "the consumers".
CONSUMERS = (
    SRC / "rules" / "conj.py",
    SRC / "llm" / "packs.py",
    SRC / "llm" / "wire.py",
)

# What the package is allowed to know about. Deliberately short: the render
# returns a STRING and `llm/packs.py` decides what to do with it, so the pack
# layer learns nothing about criticism and this package learns nothing about
# packs.
DECLARED_DEPENDENCIES = frozenset({"ontology", "config", "programs"})


def _imported_modules(path: pathlib.Path) -> set[str]:
    """Every `deepreason.*` module a file imports, RELATIVE IMPORTS INCLUDED.

    A substring grep for "deepreason.rules" walks straight past
    `from ..rules.spawn import ...`; the map's own falsification pass found
    that class of hole on a seam's core dependency-arrow claim
    (`DR-SCHEMA`, check-writing rule 3). So levels are resolved through the
    AST rather than matched textually.
    """
    package_parts = path.resolve().relative_to(SRC.resolve()).parts[:-1]
    imported: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = ("deepreason", *package_parts[: len(package_parts) - node.level + 1])
                imported.add(".".join((*base, node.module)) if node.module else ".".join(base))
            elif node.module:
                imported.add(node.module)
    return {m for m in imported if m == "deepreason" or m.startswith("deepreason.")}


# --- 1: nobody reaches past the interface ---------------------------------- #


def test_no_consumer_reaches_past_the_interface():
    """R14. The package exports an interface; consumers may use only that.

    `test_signal_contract.py::test_the_allocation_controller_consumes_only_the
    _interface` is the model, including its reason for existing: this passes on
    the tree as it stands, so its value is not that it turns anything green
    today. It is that it FAILS the day someone imports
    `deepreason.discharge.submission` directly and starts depending on an
    internal that the interface never promised.
    """
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        if PACKAGE.resolve() in path.resolve().parents:
            continue
        deep = sorted(
            m for m in _imported_modules(path)
            if m.startswith("deepreason.discharge.")
        )
        if deep:
            offenders.append((str(path), deep))
    assert not offenders, (
        f"these reach past the interface into discharge internals: {offenders}"
    )

    # Positive anchor (DR-SCHEMA check-writing rule 1): a moved or renamed
    # package would make the loop above vacuous rather than failing, so the
    # test also demands that the interface is actually being consumed. The
    # count is pinned with `==` and the file named, because it IS the claim
    # (rule 6, "counts are claims"): the whole channel reaches the rest of the
    # tree through ONE file. `llm/packs.py` is deliberately not on this list --
    # the render hands it a plain string, so the pack layer never learns that
    # criticism is what it is rendering.
    consumers = [
        str(p) for p in sorted(SRC.rglob("*.py"))
        if PACKAGE.resolve() not in p.resolve().parents
        and "deepreason.discharge" in _imported_modules(p)
    ]
    assert consumers == ["src/deepreason/rules/conj.py"], consumers


# --- 2: the package consumes only what it declares ------------------------- #


def test_the_package_consumes_only_what_it_declares():
    """R14. The boundary in the other direction, which is the one that rots.

    A channel that grew an `llm` import would start deciding how criticism is
    PRESENTED, and a channel that grew an `adjudication` import would be one
    edit away from crossing the law line. Neither is prevented by taste; both
    are prevented by this.
    """
    files = sorted(PACKAGE.rglob("*.py"))
    assert files, f"{PACKAGE} has no modules -- this test would be vacuous"

    reached: dict[str, list[str]] = {}
    for path in files:
        outside = sorted(
            m for m in _imported_modules(path)
            if m != "deepreason"
            and m.split(".")[1] not in DECLARED_DEPENDENCIES
            and not m.startswith("deepreason.discharge")
        )
        if outside:
            reached[str(path)] = outside
    assert not reached, (
        f"the discharge package reaches outside its declared dependencies "
        f"{sorted(DECLARED_DEPENDENCIES)}: {reached}"
    )


# --- 3: a fourth kind enters by DECLARATION alone -------------------------- #


def test_no_consumer_names_a_discharge_kind_literally():
    """R12's companion, and the cheaper half of property 3.

    If `conj.py` said `if kind == "revised"`, adding a kind WOULD mean editing
    the submission path -- exactly what the operator's law forbids -- and the
    monkeypatched test below might still pass by luck of which branch it took.
    """
    for path in CONSUMERS:
        assert path.exists(), path            # positive anchor
        text = path.read_text()
        for name in sorted(DISCHARGE_KIND_DECLARATIONS):
            assert f'"{name}"' not in text, (path, name)
            assert f"'{name}'" not in text, (path, name)


def test_a_fourth_kind_enters_by_declaration_alone(harness, monkeypatch):
    """R12/R14, the load-bearing check: declaration is sufficient.

    A synthetic fourth kind is REGISTERED and nothing else is touched. It must
    reach all three surfaces a kind has to reach -- the wire schema the model
    reads, the screen that accepts a discharge, and the render that tells the
    writer the kind exists -- with `rules/conj.py`, `llm/packs.py` and
    `llm/wire.py` byte-unchanged.

    Mutation-proved rather than asserted: hard-coding the kind tuple in a
    scratch copy turns this RED (`proof/arch_red.txt`).
    """
    from deepreason.discharge import open_criticisms
    from deepreason.llm.wire import discharge_kind_enum

    before = {p: p.read_bytes() for p in CONSUMERS}

    synthetic = DischargeKindDeclaration(
        name="scoped_out",
        asserts="the criticism is outside the problem as posed",
        requires=("note",),
        directive_line="scoped_out -- say which part of the problem excludes it",
        attackable=False,
    )
    monkeypatch.setitem(DISCHARGE_KIND_DECLARATIONS, "scoped_out", synthetic)

    # (a) the wire schema the model actually reads
    assert "scoped_out" in discharge_kind_enum()

    # (b) the screen accepts it
    policy = resolve_policy(Config(DISCHARGE_POLICY="discharge-required.v1"))
    assert "scoped_out" in policy.kind_names()

    # (c) the render tells the writer it exists
    from deepreason.discharge import render_open_criticism_context

    problem, criticism = _problem_with_one_open_criticism(harness)
    rendered = render_open_criticism_context(harness, problem.id, policy)
    assert rendered is not None
    assert "scoped_out" in rendered
    assert criticism.id in rendered
    assert open_criticisms(harness, problem.id, policy)

    after = {p: p.read_bytes() for p in CONSUMERS}
    assert before == after, "a kind must not require editing a consumer"


# --- 4: configuration, not code -------------------------------------------- #


def test_a_channel_toggle_is_pure_configuration(harness):
    """R13. Turning the channel on is a Config value, never an edit.

    The default is OFF (SPEC A7 -- the DEFAULT itself is F3's to set), so this
    also pins the property every other test in the tranche leans on: with the
    channel off, the render produces NOTHING and no existing pack byte moves.
    """
    from deepreason.discharge import render_open_criticism_context

    problem, _ = _problem_with_one_open_criticism(harness)

    off = resolve_policy(Config())
    assert render_open_criticism_context(harness, problem.id, off) is None

    on = resolve_policy(Config(DISCHARGE_POLICY="discharge-required.v1"))
    assert render_open_criticism_context(harness, problem.id, on) is not None


def test_a_cap_change_is_pure_configuration(harness):
    """R13. The FREE layer: a parameter inside a preset's envelope.

    Two criticisms, a cap of one: the render must show one and say so. The
    number is not a decoration -- an undisclosed cap is the silent truncation
    `_allocate_sections` exists to abolish, applied to a different section.
    """
    from deepreason.discharge import render_open_criticism_context

    problem, _ = _problem_with_one_open_criticism(harness, extra=1)

    wide = resolve_policy(Config(DISCHARGE_POLICY="discharge-required.v1"))
    narrow = wide.model_copy(update={"handles_n": 1})

    assert len(open_criticisms_for(harness, problem, wide)) == 2
    assert len(open_criticisms_for(harness, problem, narrow)) == 1
    assert "1 of 2" in render_open_criticism_context(harness, problem.id, narrow)


# --- shared fixtures ------------------------------------------------------- #


def open_criticisms_for(harness, problem, policy):
    from deepreason.discharge import open_criticisms

    return open_criticisms(harness, problem.id, policy)


def _problem_with_one_open_criticism(harness, *, extra: int = 0):
    """A problem, a candidate addressed to it, and `1 + extra` open criticisms.

    The criticisms are `observe_only` -- a critic-role artifact plus a
    `["scrutiny", target, critic]` Measure and NO warrant. That is deliberate
    and is the whole point of the tranche: W2 measured that population as the
    one never routed anywhere (0 of 196 exposed), and a fixture that used
    warrant-bearing attacks instead would test the channel on criticism that
    was already acting.
    """
    from deepreason.ontology import Problem, ProblemProvenance, Provenance

    problem = harness.register_problem(
        Problem(
            id="p-discharge",
            description="state the tide table for this harbour",
            criteria=[],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    target = harness.create_artifact(
        "candidate: the tide is lunar only",
        problem_id=problem.id,
        provenance=Provenance(role="conjecturer"),
    )
    first = None
    for index in range(1 + extra):
        critic = harness.create_artifact(
            f"critic {index}: the solar contribution is omitted, so the "
            f"spring-neap range cannot be right",
            provenance=Provenance(role="critic"),
        )
        harness.record_measure(inputs=["scrutiny", target.id, critic.id])
        first = first or critic
    return problem, first


@pytest.fixture
def harness(tmp_path):
    from deepreason.harness import Harness

    return Harness(tmp_path / "run")
