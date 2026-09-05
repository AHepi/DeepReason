"""The controller hook: declared, never implemented, called by nothing.

Implements S7 (R7, R8, C2) of the mini isolation programme. R7 asks that what
a seat is shown be "calibrated on the fly and modifiable by the controller";
R8 is the operator's "Don't change the controller just yet". The window
ruling of 2026-09-05 fixes the shape: "The hook is an interface with a no-op
default and zero callers; an architecture test asserts zero callers." This
file is that test. It supersedes the earlier wording in SPEC S7 and CHECKLIST
step 34 ("called between cycles"): the seam is declared, and nothing walks
it until the operator says how the controller steps in.
"""

import ast
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
MINI = REPO / "mini" / "minireason"


def test_the_default_resolves_to_the_noop_and_it_is_the_only_hook():
    from minireason.seats import (
        DEFAULT_CALIBRATION_HOOK_ID,
        MiniCalibrationHookV1,
        mini_calibration_hook_ids,
        resolve_mini_calibration_hook,
    )

    assert mini_calibration_hook_ids() == ("mini.calibration.noop.v1",)
    hook = resolve_mini_calibration_hook()
    assert hook.hook_id == DEFAULT_CALIBRATION_HOOK_ID == "mini.calibration.noop.v1"
    assert isinstance(hook, MiniCalibrationHookV1)
    assert resolve_mini_calibration_hook("mini.calibration.noop.v1") is hook


def test_the_noop_returns_none_for_every_input():
    from minireason.seats import MINI_LAYOUTS, MINI_SEATS, resolve_mini_calibration_hook

    hook = resolve_mini_calibration_hook()
    for seat in MINI_SEATS:
        for cycle in (0, 1, 7, 1000):
            assert hook.calibrate(seat_id=seat, cycle=cycle, entries=MINI_LAYOUTS[seat].entries) is None
    assert hook.calibrate(seat_id="not-a-seat", cycle=-1, entries=()) is None


def test_nothing_registers_a_second_hook():
    """R8, on the source: exactly two sites name the registration function
    under src/ and mini/minireason/ -- its definition and the one no-op
    registration. A third is a controller stepping in before the operator
    said how."""
    sites = []
    for root in (REPO / "src", MINI):
        for path in sorted(root.rglob("*.py")):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "register_mini_calibration_hook" in line:
                    sites.append(f"{path.relative_to(REPO)}:{lineno}")
    assert len(sites) == 2, sites


def test_the_hook_has_zero_callers():
    """The window's ruling, on the AST: no module under src/ or
    mini/minireason/ CALLS `calibrate` or `resolve_mini_calibration_hook`,
    other than the module that defines them (whose one call is the no-op's
    registration). The seam exists; nothing walks it."""
    callers = []
    for root in (REPO / "src", MINI):
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                if name in {"calibrate", "resolve_mini_calibration_hook"}:
                    callers.append(f"{path.relative_to(REPO)}:{node.lineno}: {name}")
    assert callers == [], callers


def test_a_run_with_the_hook_consulted_renders_the_same_briefs(tmp_path):
    """R8 honoured: consulting the hook changes nothing. The briefs rendered
    from the layout as declared and from the layout the hook returns -- None,
    meaning as declared -- are byte-identical for every seat."""
    import json

    from minireason.call import MockEndpoint
    from minireason.loop import Session, run
    from minireason.seats import (
        MINI_LAYOUTS,
        MINI_SEATS,
        render_mini_brief,
        resolve_mini_calibration_hook,
    )

    def endpoint_fn(prompt):
        return json.dumps({"candidates": [{"content": json.dumps(
            {"claim": "c", "mechanism": "m", "forbidden": [{"case": "x", "eval": "program:json-wf"}]}
        ), "typicality": 0.5}]})

    root = tmp_path / "run"
    run([("pi-0", "why?")], MockEndpoint(endpoint_fn), budget=100_000, root=root, vs_k=1, max_cycles=1)
    session = Session(root)
    target = session.survivors("pi-0")[0]
    hook = resolve_mini_calibration_hook()
    for seat in MINI_SEATS:
        declared = MINI_LAYOUTS[seat].entries
        reshaped = hook.calibrate(seat_id=seat, cycle=1, entries=declared)
        entries = declared if reshaped is None else reshaped
        assert entries == declared
        a = render_mini_brief(session, seat, "pi-0", target_id=target, supplied={"vs_k": 1})
        b = render_mini_brief(session, seat, "pi-0", target_id=target, supplied={"vs_k": 1})
        assert a == b


def test_a_second_registration_is_refused_typed():
    from minireason.seats import MiniSeatError, register_mini_calibration_hook

    class _Other:
        hook_id = "mini.calibration.noop.v1"
        hook_version = "9.0.0"

        def calibrate(self, *, seat_id, cycle, entries):
            return entries

    with pytest.raises(MiniSeatError) as refused:
        register_mini_calibration_hook(_Other())
    assert refused.value.code == "MINI_CALIBRATION_HOOK_CONFLICT"
