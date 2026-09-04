#!/usr/bin/env python3
"""The four critic briefs, as configuration. No file under `src/` changes.

Two operator-authored section plugins and four registered layouts, built
through the public registry (`DR-INV-seat-section-plugins`,
`DR-REC-add-a-section-plugin`). The recipe's own rule is that adding a section
contains no source edit; `--census` measures that rather than asserting it, by
hashing every `.py` under `src/deepreason` before and after the whole
registration.

The four cells differ ONLY in the layout. The epistemic state a critic reads is
byte-identical across all four -- the provenance plugin reads
`state.artifacts[target_id].provenance`, which is already there, and the
history plugin reads records this tranche's bench writes into the state under
a prefix no shipped section looks at. Nothing is supplied through
`render_crit_pack`'s argument list, which is why no signature had to move.

Selection is one environment assignment,
`DEEPREASON_SEAT_PACK_LAYOUT=argumentative_critic=<layout-id>`, resolved per
call by `resolve_seat_pack_layout`. Nothing reaches `Config`, so no
qualification subject digest moves.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SRC = REPO / "src" / "deepreason"

# History records ride in the state under this prefix. No shipped section
# plugin reads a content_ref prefix, so these are invisible to every cell
# except the one whose layout carries the history plugin -- which is what lets
# all four cells share one state and differ only in the brief.
HISTORY_PREFIX = "exp-hist:"

CRITIC_SEAT = "argumentative_critic"
CELL_IDS = ("C00", "C10", "C01", "C11")
CELL_LABELS = {
    "C00": "labels OMITTED, history OMITTED  (today's shipped brief)",
    "C10": "labels PRESENT, history OMITTED",
    "C01": "labels OMITTED, history PRESENT",
    "C11": "labels PRESENT, history PRESENT",
}


def _src_digest() -> str:
    return hashlib.sha256(
        b"".join(p.read_bytes() for p in sorted(SRC.rglob("*.py")))
    ).hexdigest()


def _plugins():
    from deepreason.llm.seat_plugins import NoParams, _Plugin, _supplied
    from deepreason.llm.seat_sections import SectionRenderV1

    # The operator's three F1 labels, mapped onto the two fields the record
    # actually has. `Provenance` carries `role`, `school` and `event_seq` and
    # nothing else, so "origin" is read off the role -- SPEC A1, which also
    # records that every target in this set is conjecturer-authored, so the
    # origin line carries no variance and the school line carries all of it.
    ORIGIN = {
        "seed": "seed (the operator's own question)",
        "conjecturer": "harness-minted (a conjecturer seat proposed it)",
        "critic": "harness-minted (a critic seat filed it)",
        "controller": "harness-minted (the controller emitted it)",
        "import": "capability (admitted from an outside source)",
        "experimenter": "capability (an experiment design produced it)",
        "variator": "harness-minted (a variator seat produced it)",
        "synthesizer": "harness-minted (a synthesizer seat produced it)",
        "user": "seed (supplied by the operator)",
    }

    class Provenance(_Plugin):
        plugin_id = "dr.exp.provenance"
        plugin_version = "1.0.0"
        section_id = "target-provenance"
        requires = ("target_id",)
        parameters_model = NoParams

        def render(self, request, params):
            artifact = request.state.artifacts.get(_supplied(request, "target_id"))
            if artifact is None:
                return None
            mark = artifact.provenance
            return SectionRenderV1(section_id=self.section_id, text="\n".join([
                "TARGET PROVENANCE (who produced this target, and under what"
                " stance):",
                f"- author seat: {mark.role.value}",
                f"- school: {mark.school if mark.school else '(none)'}",
                f"- origin: {ORIGIN.get(mark.role.value, mark.role.value)}",
            ]))

    class History(_Plugin):
        plugin_id = "dr.exp.history-critic"
        plugin_version = "1.0.0"
        section_id = "target-criticism-history"
        requires = ("target_id",)
        parameters_model = NoParams

        def render(self, request, params):
            target_id = _supplied(request, "target_id")
            rows = []
            for artifact in request.state.artifacts.values():
                ref = artifact.content_ref
                if not ref.startswith("inline:" + HISTORY_PREFIX):
                    continue
                record = json.loads(ref[len("inline:") + len(HISTORY_PREFIX):])
                if record.get("target") == target_id:
                    rows.append(record)
            if not rows:
                return None
            lines = ["CRITICISM HISTORY OF THIS TARGET (what has already been"
                     " objected to, and what became of it):"]
            for position, record in enumerate(sorted(rows, key=lambda r: r["seq"]), 1):
                lines.append(f"- objection {position}: {record['objection']}")
                lines.append(f"  outcome: {record['outcome']}")
            return SectionRenderV1(section_id=self.section_id, text="\n".join(lines))

    return Provenance, History


def register() -> dict[str, str]:
    """Register the two plugins and the four layouts. Returns cell -> layout id."""
    from deepreason.llm.seat_layouts import CRITIC_LEGACY_LAYOUT
    from deepreason.llm.seat_sections import (
        SeatPackLayoutEntryV1,
        SeatPackLayoutV1,
        register_seat_pack_layout,
        register_section_plugin,
    )

    # The shipped plugins and layouts seed lazily; the registry must hold
    # them before a cell layout can copy the shipped entries.
    from deepreason.llm.seat_plugins import ensure_seeded
    ensure_seeded()

    provenance_cls, history_cls = _plugins()
    register_section_plugin(provenance_cls())
    register_section_plugin(history_cls())

    base = tuple(CRITIC_LEGACY_LAYOUT.entries)
    # Priorities sit beside the sections each is nearest in kind: provenance
    # beside the target's own declared surface (2), history beside the
    # standing attacks it extends (5). Both inside the declared envelope.
    provenance = SeatPackLayoutEntryV1(plugin_id="dr.exp.provenance", priority=2)
    history = SeatPackLayoutEntryV1(
        plugin_id="dr.exp.history-critic", priority=5,
        droppable=True, compressible=True, min_tokens=48,
    )
    extras = {"C00": (), "C10": (provenance,), "C01": (history,),
              "C11": (provenance, history)}

    layouts = {}
    for cell in CELL_IDS:
        layout_id = f"seat-pack.critic.exp-{cell}"
        register_seat_pack_layout(SeatPackLayoutV1(
            layout_id=layout_id, entries=base + extras[cell]))
        layouts[cell] = layout_id
    return layouts


def select(cell: str, layouts: dict[str, str]) -> None:
    os.environ["DEEPREASON_SEAT_PACK_LAYOUT"] = f"{CRITIC_SEAT}={layouts[cell]}"


def _census_state():
    """One target and one history record, enough to make every difference show."""
    from deepreason.ontology.artifact import (
        Artifact, Interface, Provenance, ProvenanceRole,
    )
    from deepreason.ontology.state import EpistemicState, Status

    body = {
        "claim": "Consensus probability tends to 0 as n grows.",
        "mechanism": "Each majority update strictly increases monochromatic edges.",
        "scope": {"covers": [], "excludes": []},
        "counterconditions": [
            {"case": "If the interface vanishes whp, the claim fails.",
             "eval": "observation", "checker_spec": None}
        ],
    }
    target_id = "c" * 64
    artifacts = {target_id: Artifact(
        id=target_id, content_ref="inline:" + json.dumps(body), codec="utf8",
        interface=Interface(),
        provenance=Provenance(role=ProvenanceRole.CONJECTURER,
                              school="school-2", event_seq=17),
    )}
    record = {"target": target_id, "seq": 1,
              "objection": "The monotone-energy step does not establish absorption.",
              "outcome": "raised and not answered; the target's status did not move"}
    history_id = "d" * 64
    artifacts[history_id] = Artifact(
        id=history_id,
        content_ref="inline:" + HISTORY_PREFIX + json.dumps(record),
        codec="utf8", interface=Interface(),
        provenance=Provenance(role=ProvenanceRole.CRITIC, school=None, event_seq=18),
    )
    return target_id, EpistemicState(artifacts=artifacts,
                                     status={target_id: Status.ACCEPTED})


def census() -> int:
    before = _src_digest()
    layouts = register()
    from deepreason.llm.packs import render_crit_pack
    from deepreason.llm.seat_layouts import CRITIC_LEGACY_LAYOUT
    from deepreason.llm.seat_sections import (
        resolve_section_plugin, resolve_seat_pack_layout,
    )

    target_id, state = _census_state()

    print("CENSUS of seat-pack.critic.legacy-v0 -- the shipped critic brief")
    print(f"{'plugin id':30s} {'section id':28s} {'prio':>4s} {'drop':>5s} {'comp':>5s}")
    for entry in CRITIC_LEGACY_LAYOUT.entries:
        plugin = resolve_section_plugin(entry.plugin_id)
        print(f"{entry.plugin_id:30s} {plugin.section_id:28s} {entry.priority:4d}"
              f" {str(entry.droppable):>5s} {str(entry.compressible):>5s}")
    print(f"entries: {len(CRITIC_LEGACY_LAYOUT.entries)}")

    os.environ.pop("DEEPREASON_SEAT_PACK_LAYOUT", None)
    default = render_crit_pack(target_id, state, {}, None, token_budget=4000)
    renders = {}
    for cell in CELL_IDS:
        select(cell, layouts)
        assert resolve_seat_pack_layout(CRITIC_SEAT).layout_id == layouts[cell]
        renders[cell] = render_crit_pack(target_id, state, {}, None, token_budget=4000)
    os.environ.pop("DEEPREASON_SEAT_PACK_LAYOUT", None)

    print()
    print(f"default == C00: {default == renders['C00']}")
    for cell in CELL_IDS:
        text = renders[cell]
        print(f"  {cell}  bytes={len(text):5d}"
              f"  provenance={'TARGET PROVENANCE' in text}"
              f"  history={'CRITICISM HISTORY' in text}"
              f"   {CELL_LABELS[cell]}")
    print(f"all four distinct: {len(set(renders.values())) == 4}")
    print(f"src/ bytes unchanged: {before == _src_digest()}")
    print()
    print("=== the shipped brief, rendered (C00) ===")
    print(renders["C00"])
    print("=== what C11 adds ===")
    for block in renders["C11"].split("\n\n"):
        if "PROVENANCE" in block or "HISTORY" in block:
            print(block)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", action="store_true")
    sys.exit(census() if ap.parse_args().census else 0)
