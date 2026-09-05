"""One interface, three seats: mini's shells, and the first consumer of
`SeatShellV1.form_id`.

Implements S6 (R7, C7, C8) of the mini isolation programme. R7 is the
operator's "all three seats need the same pluggable interface with relaxed
forms"; C7 is the seat-is-a-shell law -- a seat kind is a registered pairing
of a brief layout and a form. Before this, `form_id` was a registered field
nothing read (PARKED P3): the shell paired a layout with a form on paper while
every dispatch site chose its form inline. Mini's dispatch resolves its form
THROUGH the shell, which is what makes the three seats one interface rather
than three similar code paths.
"""

import ast
import json
import pathlib

import pytest

from minireason.call import MockEndpoint
from minireason.loop import Session, run

MINI = pathlib.Path(__file__).resolve().parents[1] / "minireason"


def _skeleton(i: int) -> str:
    return json.dumps(
        {
            "claim": f"claim {i}",
            "mechanism": f"mechanism {i}",
            "forbidden": [{"case": "x", "eval": "program:json-wf"}],
        }
    )


@pytest.fixture
def session(tmp_path):
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        return json.dumps(
            {
                "candidates": [
                    {"content": _skeleton(2 * calls["n"] + i), "typicality": 0.5}
                    for i in range(2)
                ]
            }
        )

    root = tmp_path / "run"
    run([("pi-0", "why did X happen?")], MockEndpoint(endpoint_fn), budget=200_000,
        root=root, vs_k=2, max_cycles=2)
    return Session(root)


def test_each_mini_seat_resolves_its_form_through_its_shell():
    """SPEC S6's accept, verbatim: the form a seat fills is the one its shell
    names, for all three seats."""
    from deepreason.llm.seat_sections import resolve_seat_shell
    from minireason.seats import MINI_SEATS, form_for_seat

    assert MINI_SEATS == ("mini.conjecturer", "mini.critic", "mini.commitment")
    for seat in MINI_SEATS:
        assert form_for_seat(seat).form_id == resolve_seat_shell(seat).form_id
    assert form_for_seat("mini.conjecturer").form_id == "mini.conjecturer.relaxed.v1"
    assert form_for_seat("mini.critic").form_id == "mini.critic.relaxed.v1"
    assert form_for_seat("mini.commitment").form_id == "mini.commitment.relaxed.v1"


def test_the_shell_is_the_default_and_the_declared_orders_still_win(monkeypatch):
    """Argument, then `DEEPREASON_MINI_FORM`, then the SHELL's form -- the
    stored form is one selection away, never a code edit (R-stored)."""
    from minireason.forms import MINI_FORM_ENV
    from minireason.seats import form_for_seat

    assert form_for_seat("mini.conjecturer", "mini.conjecturer.legacy-v0").form_id == (
        "mini.conjecturer.legacy-v0"
    )
    monkeypatch.setenv(MINI_FORM_ENV, "mini.conjecturer=mini.conjecturer.legacy-v0")
    assert form_for_seat("mini.conjecturer").form_id == "mini.conjecturer.legacy-v0"
    # another seat's assignment does not leak
    assert form_for_seat("mini.critic").form_id == "mini.critic.relaxed.v1"


def test_binding_another_shell_changes_both_what_is_shown_and_what_is_asked(
    session, monkeypatch
):
    """C7, both halves at once: the critic's shell bound in the conjecturer's
    seat changes the brief it renders AND the form it is asked to fill."""
    from deepreason.llm.seat_sections import SEAT_SHELL_ENV, SectionReceiptV1
    from minireason.seats import form_for_seat, render_mini_brief

    target = session.survivors("pi-0")[0]
    receipts: list[SectionReceiptV1] = []
    before = render_mini_brief(session, "mini.conjecturer", "pi-0", target_id=target,
                               supplied={"vs_k": 2}, receipts=receipts)
    assert "## everything-so-far" in before
    assert "## target-conjecture" not in before
    assert form_for_seat("mini.conjecturer").form_id == "mini.conjecturer.relaxed.v1"

    monkeypatch.setenv(SEAT_SHELL_ENV, "mini.conjecturer=seat.mini.critic.v0")
    swapped: list[SectionReceiptV1] = []
    after = render_mini_brief(session, "mini.conjecturer", "pi-0", target_id=target,
                              supplied={"vs_k": 2}, receipts=swapped)
    assert "## target-conjecture" in after
    assert "## everything-so-far" not in after
    assert "You are the critic seat" in after
    assert form_for_seat("mini.conjecturer").form_id == "mini.critic.relaxed.v1"
    assert {r.plugin_id for r in swapped} == {
        "mini.problem", "mini.target-conjecture", "mini.directive"
    }


def test_the_directive_takes_the_requests_values(session):
    from minireason.seats import render_mini_brief

    brief = render_mini_brief(session, "mini.conjecturer", "pi-0", supplied={"vs_k": 7})
    assert "Return 7 diverse candidates" in brief
    # an unsupplied placeholder is left visible rather than silently blanked
    bare = render_mini_brief(session, "mini.conjecturer", "pi-0")
    assert "Return {vs_k} diverse candidates" in bare


def test_mini_renders_through_the_public_road_only():
    """C8's bypass check for mini: no module under `mini/minireason/` names a
    private symbol of `deepreason.llm.packs`, builds a `PackSection`, or
    calls the allocator directly. Checked on the AST, over every mini module,
    so a new one cannot slip past a list."""
    offenders = []
    for path in sorted(MINI.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "deepreason.llm.packs":
                for alias in node.names:
                    if alias.name.startswith("_") or alias.name in {
                        "PackSection", "allocate_pack", "PackIR"
                    }:
                        offenders.append(f"{path.name}:{node.lineno}: {alias.name}")
            if isinstance(node, ast.Attribute) and node.attr in {
                "_walk_seat_layout", "_allocate_sections", "_pack_section"
            }:
                offenders.append(f"{path.name}:{node.lineno}: .{node.attr}")
    assert not offenders, offenders


def test_the_full_harness_shells_and_layouts_are_untouched():
    """C4: registering mini's three shells changes nothing about the two the
    full harness ships; their pairings resolve exactly as before."""
    from deepreason.llm.seat_layouts import (
        CONJECTURER_LEGACY_SHELL,
        CRITIC_LEGACY_SHELL,
    )
    from deepreason.llm.seat_sections import resolve_seat_shell, seat_shell_ids
    import minireason.seats  # noqa: F401 - the registration under test

    assert resolve_seat_shell("conjecturer") == CONJECTURER_LEGACY_SHELL
    assert resolve_seat_shell("argumentative_critic") == CRITIC_LEGACY_SHELL
    assert CONJECTURER_LEGACY_SHELL.form_id == "conjecturer.turn.v6"
    assert CRITIC_LEGACY_SHELL.form_id == "argumentative_critic.compact.v1"
    assert {"seat.mini.conjecturer.v0", "seat.mini.critic.v0", "seat.mini.commitment.v0"} <= set(
        seat_shell_ids()
    )
