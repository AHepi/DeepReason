"""Does each arm's brief ACTUALLY differ from the control's? Measure it.

## The failure this exists to prevent

The history tranche's `arm.sh` carries an `exit 6` guard and a comment saying
why: an arm whose injected content is empty "runs, costs a full battery and
four cycles, and reports a null result that looks like evidence". A layout arm
can fail the same way and more quietly -- a parameter that changes nothing
produces a treatment arm byte-identical to the control, and no log line says
so.

So before any provider call, every arm renders a conjecturer brief over the
COMMITTED golden fixture inputs (`tests/conj_pack_golden_cases.py`, whose
state carries one refuted and several accepted artifacts) and is diffed
against A0's. An arm that does not differ is named here, not discovered in the
numbers.

Reusing the golden fixture rather than building a state is deliberate: it is
the input shape the gate already pins, so a difference this script reports is
a difference in the ARM and not in a fixture written to flatter it.

Usage:
    python prove_arms.py            # table + exit 0/1
    python prove_arms.py --show A1  # the differing lines, for the record
"""

from __future__ import annotations

import argparse
import difflib
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE / "rig"))

import armrig  # noqa: E402


def _render(arm: str, home: pathlib.Path) -> str:
    from deepreason.llm.packs import render_conj_pack
    from deepreason.llm.layout import ROBUST_LAYOUT_POLICY
    from deepreason.llm.seat_sections import (
        register_seat_pack_layout,
        seat_pack_layout_ids,
    )
    from tests.conj_pack_golden_cases import _rich_kwargs, _seed

    if arm == "A3":
        from deepreason.llm.seat_sections import load_operator_plugins

        armrig.write_template(home / "seat_plugins")
        loaded, notices = load_operator_plugins(environ={"DEEPREASON_HOME": str(home)})
        if armrig.TEMPLATE_PLUGIN_ID not in loaded:
            raise SystemExit(f"A3 template did not load: {loaded} {notices}")

    layout = armrig.build(arm)
    layout_id = None
    if layout is not None:
        if layout.layout_id not in seat_pack_layout_ids():
            register_seat_pack_layout(layout)
        layout_id = layout.layout_id

    problem, harness, ids = _seed(home / f"golden-{arm}")
    rich = _rich_kwargs(problem, harness, ids)
    return render_conj_pack(
        **rich,
        token_budget=6000,
        layout=ROBUST_LAYOUT_POLICY,
        seat_pack_layout=layout_id,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show", default=None, help="print the diff for one arm")
    args = parser.parse_args(argv[1:])

    with tempfile.TemporaryDirectory() as tmp:
        home = pathlib.Path(tmp)
        rendered = {arm: _render(arm, home) for arm in armrig.ARMS}

    control = rendered["A0"]
    print("ARM_BRIEF_DIFFERENCE_V1  (conjecturer brief, committed golden inputs)")
    print(f"  A0 control: {len(control)} bytes")
    identical = []
    for arm in armrig.ARMS:
        if arm == "A0":
            continue
        text = rendered[arm]
        same = text == control
        changed = sum(
            1
            for line in difflib.unified_diff(
                control.splitlines(), text.splitlines(), n=0, lineterm=""
            )
            if line[:1] in "+-" and line[:3] not in ("+++", "---")
        )
        verdict = "IDENTICAL TO A0" if same else f"differs, {changed} lines"
        print(f"  {arm:<4} {len(text):>6} bytes  {verdict}")
        if same:
            identical.append(arm)

    if args.show:
        text = rendered[args.show]
        print(f"\n--- unified diff A0 -> {args.show} ---")
        for line in difflib.unified_diff(
            control.splitlines(), text.splitlines(), "A0", args.show, n=1, lineterm=""
        ):
            print(line)

    print()
    if identical:
        print(
            "ARMS THAT VARY NOTHING: "
            + ", ".join(identical)
            + "\n  These are not treatments. Either the parameter does not reach "
            "the brief\n  on this input shape, or the arm is a NOISE-FLOOR pair "
            "and PREREG.md says so."
        )
        return 1
    print("every arm differs from A0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
