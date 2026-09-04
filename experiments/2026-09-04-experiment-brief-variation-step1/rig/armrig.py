"""The arm rig — six briefs, one form, and NO edit under `src/`.

## Why a rig exists at all, and what it says about the shipped surface

`docs/map/REC-add-a-section-plugin.md` gives four steps for changing what a
seat is shown: write the plugin, register a layout that includes it, select it
with `DEEPREASON_SEAT_PACK_LAYOUT`, and do all of that without opening a file
under `src/`. Steps 1 and 4 ship. Steps 2 and 3 do not reach a live run, and
this file exists because of that gap rather than in spite of it:

  * `load_operator_plugins` -- the ONLY loader for the operator's own
    `seat_plugins/` directory -- has no call site anywhere in `src/`. It is
    called by seven tests and by nothing else. So a `.tmpl` an operator drops
    in that directory is never registered by `deepreason reason`.
  * `register_seat_pack_layout` is likewise reachable only from Python. There
    is no file, flag or environment road that puts a NEW layout in the
    registry, so `DEEPREASON_SEAT_PACK_LAYOUT` can only ever select one of the
    two layouts `seat_layouts.py` hard-codes.

Both are recorded as findings in `PARKED.md` (F1, F2) and neither is fixed
here: this is an experiment tranche and the operator's R33 is "Change no
default yourself."

What this file does instead is supply the two missing steps FROM THE
EXPERIMENT'S OWN SIDE, at interpreter start, through `sitecustomize` -- a
stock Python hook, no source edit, no monkeypatch of harness behaviour. The
run itself is still the ordinary `deepreason reason` CLI on the managed path,
so the ladder rules and the operations-parity law are untouched: the only
difference between an arm and a default run is which layout id resolves.

## The arms

`A0` is the shipped default and registers nothing, so it is the control in the
strongest sense available: the rig is INERT for it.

| arm | the one thing that varies |
|---|---|
| `A0` | nothing -- shipped default, rig inert |
| `A1` | `dr.history.v1` params `include_refuted=true, refuted_n=3` |
| `A1P` | `dr.history.v1` REMOVED from the layout entirely |
| `A2` | `dr.active-properties` param `claim_chars=800` (from 200) |
| `A3` | `dr.neighbourhood` replaced by an operator `.tmpl` |

`B0` is not here: it runs no harness at all (`baseline_b0.py`).

## The A0 == A1P identity, which is a measurement rather than an accident

`llm/layout.py` sets `superseded_summary_n` to 0 in BOTH registered
arrangements, and `_History.render` reads exactly that number unless
`include_refuted` raises it. So at the shipped default the history section
renders `None` -- history is OFF as shipped -- and removing the plugin can
change nothing. `prove_arms.py` measures this rather than asserting it, and
`PREREG.md` §A3 turns the pair into the experiment's noise floor.
"""

from __future__ import annotations

import os
import pathlib

ARM_ENV = "DR_ARM"
LAYOUT_ENV = "DEEPREASON_SEAT_PACK_LAYOUT"
CONJECTURER_SEAT = "conjecturer"

# The operator's own template, and the id it claims. The filename in
# `seat_plugins/` must be `<plugin-id>@<section-id>.tmpl` for the shipped
# loader to read the two ids off it.
TEMPLATE_PLUGIN_ID = "op.neighbourhood.v1"
TEMPLATE_SECTION_ID = "neighbourhood"
TEMPLATE_FILENAME = f"{TEMPLATE_PLUGIN_ID}@{TEMPLATE_SECTION_ID}.tmpl"

ARMS = ("A0", "A1", "A1P", "A2", "A3")


def layout_id(arm: str) -> str:
    return f"seat-pack.conjecturer.step1-{arm.lower()}"


def _entries():
    from deepreason.llm.seat_layouts import CONJECTURER_LEGACY_LAYOUT

    return list(CONJECTURER_LEGACY_LAYOUT.entries)


def _replace(entries, target, **changes):
    """One entry changed, every other entry the same OBJECT.

    `model_copy(update=...)` rather than a rebuilt entry, so a field this arm
    does not name cannot drift: an arm that silently moved a priority would be
    varying two things and reporting one.
    """

    out, hits = [], 0
    for entry in entries:
        if entry.plugin_id == target:
            hits += 1
            out.append(entry.model_copy(update=changes))
        else:
            out.append(entry)
    if hits != 1:
        raise SystemExit(
            f"ARM RIG REFUSED: expected exactly one {target!r} entry in the "
            f"shipped conjecturer layout, found {hits}"
        )
    return out


def _drop(entries, plugin_id):
    out = [e for e in entries if e.plugin_id != plugin_id]
    if len(out) != len(entries) - 1:
        raise SystemExit(
            f"ARM RIG REFUSED: expected exactly one {plugin_id!r} entry to "
            f"drop, dropped {len(entries) - len(out)}"
        )
    return out


def build(arm: str):
    """The layout for one arm, or None for the arm that varies nothing."""

    from deepreason.llm.seat_sections import SeatPackLayoutV1

    if arm == "A0":
        return None
    entries = _entries()
    if arm == "A1":
        entries = _replace(
            entries,
            "dr.history.v1",
            params={"include_refuted": True, "refuted_n": 3},
        )
    elif arm == "A1P":
        entries = _drop(entries, "dr.history.v1")
    elif arm == "A2":
        entries = _replace(
            entries, "dr.active-properties", params={"claim_chars": 800}
        )
    elif arm == "A3":
        entries = _replace(entries, "dr.neighbourhood", plugin_id=TEMPLATE_PLUGIN_ID)
    else:
        raise SystemExit(f"ARM RIG REFUSED: unknown arm {arm!r}; known: {ARMS}")
    return SeatPackLayoutV1(layout_id=layout_id(arm), entries=tuple(entries))


def template_source() -> str:
    """The operator's `.tmpl`, verbatim, so the arm is auditable from here.

    WHAT IT CAN AND CANNOT CARRY, stated before any call rather than after the
    numbers. The template language sees `SectionRequestV1.supplied` and
    nothing else, and the conjecturer's `supplied["accepted"]` is a tuple of
    artifact IDS. The distilled claim text that `dr.neighbourhood` prints
    beside each id is computed inside that plugin from the run's state and
    blobs, which no template can reach.

    So A3 is a FORMAT change WITH CONTENT LOSS, not the same content in a
    different shape. That is the honest description of what the shipped
    template channel can do to this section, it is registered here before the
    arm runs, and the gap it names is `PARKED.md` F3.
    """

    return (
        "NEIGHBOURHOOD (accepted artifacts already standing on this problem) "
        "— identifiers only:\n"
        "{% for a in accepted %}  · {{ a }}\n"
        "{% endfor %}"
    )


def install(environ=None, *, arm=None):
    """Register this process's arm layout and select it. Idempotent.

    Returns a receipt dict describing exactly what was done, which `arm.sh`
    writes beside the run so the arm can be audited from the record instead of
    from this docstring.
    """

    environ = os.environ if environ is None else environ
    arm = (arm or environ.get(ARM_ENV) or "").strip().upper()
    if not arm:
        return {"arm": None, "installed": False, "reason": "DR_ARM unset"}
    if arm not in ARMS:
        raise SystemExit(f"ARM RIG REFUSED: unknown arm {arm!r}; known: {ARMS}")

    from deepreason.llm.seat_sections import (
        register_seat_pack_layout,
        seat_pack_layout_ids,
    )

    receipt = {"arm": arm, "installed": False, "template_loaded": [], "notices": []}

    if arm == "A3":
        from deepreason.llm.seat_sections import load_operator_plugins

        loaded, notices = load_operator_plugins(environ=environ)
        receipt["template_loaded"] = list(loaded)
        receipt["notices"] = list(notices)
        if TEMPLATE_PLUGIN_ID not in loaded:
            raise SystemExit(
                f"ARM RIG REFUSED: arm A3 needs {TEMPLATE_PLUGIN_ID!r} from the "
                f"operator plugin directory; loaded={loaded} notices={notices}. "
                "An A3 that silently fell back to the shipped neighbourhood "
                "would be A0 wearing A3's label."
            )

    layout = build(arm)
    if layout is not None and layout.layout_id not in seat_pack_layout_ids():
        register_seat_pack_layout(layout)
    if layout is not None:
        environ[LAYOUT_ENV] = f"{CONJECTURER_SEAT}={layout.layout_id}"
        receipt["layout_id"] = layout.layout_id
        receipt["installed"] = True
    else:
        # A0 selects nothing. Leaving the variable set from a previous arm
        # would make the control a treatment, so it is cleared rather than
        # left alone.
        environ.pop(LAYOUT_ENV, None)
        receipt["layout_id"] = None
        receipt["installed"] = True
    return receipt


def write_template(destination: pathlib.Path) -> pathlib.Path:
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / TEMPLATE_FILENAME
    path.write_text(template_source(), encoding="utf-8")
    return path
