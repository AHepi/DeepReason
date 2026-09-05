"""The mini source adapter: a read-only projection of mini's record into the
request the shipped section plugins already expect.

Implements S5 (R5, R6, R12) of the mini isolation programme -- the half that
makes the seat-shell machinery reachable from a mini session at all.

WHY AN ADAPTER AND NOT A SECOND RENDERER. Measured before any design
(`experiments/2026-09-05-change-mini-isolation-programme/proof/
m3_seat_shell_reach.txt`): the shipped walk runs from a live mini session and
renders `dr.problem` once its dict is adapted, and fails on `dr.neighbourhood`
with `'dict' object has no attribute 'content_ref'`, because mini's `State`
hands out dict projections while the plugins read ontology objects. So the
whole gap between mini and the seat shell is ONE read-only projection. The
first test below is that measurement, committed rather than left in a proof
file; the rest are the adapter.
"""

import json

import pytest

from minireason.call import MockEndpoint
from minireason.loop import Session, run


def _skeleton(i: int) -> str:
    return json.dumps(
        {
            "claim": f"claim {i}",
            "mechanism": f"mechanism {i}",
            "forbidden": [{"case": "x", "eval": "program:json-wf"}],
        }
    )


def _endpoint():
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        return json.dumps(
            {
                "candidates": [
                    {"content": _skeleton(2 * calls["n"]), "typicality": 0.5},
                    {"content": _skeleton(2 * calls["n"] + 1), "typicality": 0.5},
                ]
            }
        )

    return MockEndpoint(endpoint_fn)


@pytest.fixture
def session(tmp_path):
    """A live mini session with two cycles of admitted, standing conjectures."""
    root = tmp_path / "run"
    run(
        [("pi-0", "why did X happen?")],
        _endpoint(),
        budget=200_000,
        root=root,
        vs_k=2,
        max_cycles=2,
    )
    return Session(root)


def _neighbourhood_layout():
    from deepreason.llm.seat_sections import (
        SeatPackLayoutEntryV1,
        SeatPackLayoutV1,
        register_seat_pack_layout,
    )

    return register_seat_pack_layout(
        SeatPackLayoutV1(
            layout_id="seat-pack.mini.sources-probe.v0",
            entries=(
                SeatPackLayoutEntryV1(plugin_id="dr.problem", priority=1),
                SeatPackLayoutEntryV1(
                    plugin_id="dr.neighbourhood",
                    priority=8,
                    droppable=True,
                    compressible=True,
                    min_tokens=32,
                ),
            ),
        )
    )


def test_the_dict_view_alone_cannot_feed_the_shipped_plugins(session):
    """The BEFORE, committed: mini's dict `State` is not what the plugins read.

    Reproduces `proof/m3_seat_shell_reach.txt` ARM A: `dr.problem` renders once
    its dict is adapted by hand, and `dr.neighbourhood` fails on the very first
    artifact it touches. This is the measurement the adapter exists to answer,
    so it stays here as the statement of the gap rather than in a proof file.
    """
    from deepreason.llm.layout import resolve_layout_policy
    from deepreason.llm.packs import _walk_seat_layout
    from deepreason.llm.seat_sections import SectionRequestV1
    from deepreason.ontology import Problem

    layout = _neighbourhood_layout()
    pid = "pi-0"
    accepted = session.survivors(pid)
    assert accepted, "the fixture must leave standing conjectures to show"
    request = SectionRequestV1(
        problem=Problem.model_validate(session.state.problems[pid]),
        state=session.state,  # the dict view, unadapted
        commitments=dict(session.harness.commitments),
        blobs=session.blobs,
        layout=resolve_layout_policy(),
        supplied={"accepted": tuple(accepted)},
    )
    with pytest.raises(AttributeError, match="content_ref"):
        _walk_seat_layout("mini.conjecturer", layout.layout_id, request, [])


def test_the_adapter_lets_the_shipped_neighbourhood_render(session):
    """S5: one read-only projection, and the shipped walk renders from a live
    mini session -- `dr.problem` AND `dr.neighbourhood`, the section the raw
    dict view could not feed."""
    from deepreason.llm.packs import _walk_seat_layout
    from minireason.sources import mini_section_request

    layout = _neighbourhood_layout()
    pid = "pi-0"
    accepted = session.survivors(pid)
    request = mini_section_request(
        session, pid, supplied={"accepted": tuple(accepted)}
    )
    receipts: list = []
    sections, receipts = _walk_seat_layout(
        "mini.conjecturer", layout.layout_id, request, receipts
    )
    rendered = {r.section_id: r.disposition for r in receipts}
    assert rendered == {"problem": "rendered", "neighbourhood": "rendered"}, rendered
    texts = {s.id: s.text_ref for s in sections}
    assert "why did X happen?" in texts["problem"]
    for aid in accepted:
        assert aid in texts["neighbourhood"], aid
