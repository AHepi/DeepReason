"""The pluggable flow: stage order and the SET of artifact kinds are data the
loop walks and never names.

Implements S8 (R9, R10, C1, C8) of the mini isolation programme. R9 is the
operator's "The mini flow also needs to be adjustable in a pluggable way";
R10 is "add new artifact types on the fly if I can see it might help"; C1 is
"Proposal set up that is not permanent" -- every piece behind a registered id
or a per-run switch, OFF for the full harness and OFF by default for mini.

The two flows that ship are the whole of what a caller who selects nothing
gets (legacy, today's loop) and what the isolation programme runs
(conjecturer -> critic -> commitment, commitments off). The registration
proof -- a FOURTH artifact kind and its seat, declared only in this test file
and run end to end with no edit under `mini/minireason/` -- is
`test_a_new_artifact_kind_is_a_registration` (step 41).
"""

import json
import pathlib

import pytest

from minireason.call import MockEndpoint
from minireason.loop import Session, run

GOLDEN = pathlib.Path(__file__).parent / "goldens" / "mini_legacy_prompt.txt"


def test_two_flows_ship_and_the_default_is_legacy(monkeypatch):
    from minireason.flow import (
        DEFAULT_MINI_FLOW_ID,
        MINI_FLOW_ENV,
        MiniFlowError,
        mini_flow_ids,
        resolve_mini_flow,
        select_mini_flow,
    )

    assert {"mini.flow.legacy-v0", "mini.flow.isolation.v1"} <= set(mini_flow_ids())
    assert DEFAULT_MINI_FLOW_ID == "mini.flow.legacy-v0"
    monkeypatch.delenv(MINI_FLOW_ENV, raising=False)
    assert select_mini_flow().flow_id == "mini.flow.legacy-v0"
    assert select_mini_flow("mini.flow.isolation.v1").flow_id == "mini.flow.isolation.v1"
    monkeypatch.setenv(MINI_FLOW_ENV, "mini.flow.isolation.v1")
    assert select_mini_flow().flow_id == "mini.flow.isolation.v1"
    # the flow itself is an argument too, so a test-registered one needs no id lookup
    assert select_mini_flow(resolve_mini_flow("mini.flow.legacy-v0")).flow_id == "mini.flow.legacy-v0"
    with pytest.raises(MiniFlowError) as refused:
        select_mini_flow("mini.flow.nonesuch")
    assert refused.value.code == "MINI_FLOW_UNKNOWN"


def test_the_legacy_flow_is_todays_loop():
    """C1/C4: one conjecturer stage under the legacy shell, whose form is the
    STORED one (R-stored), with both commitment channels ON."""
    from deepreason.llm.seat_sections import resolve_seat_shell
    from minireason.flow import resolve_mini_flow
    from minireason.seats import form_for_seat

    flow = resolve_mini_flow("mini.flow.legacy-v0")
    assert [s.stage_id for s in flow.stages] == ["conjecture"]
    (stage,) = flow.stages
    assert stage.seat_id == "mini.conjecturer" and not stage.per_target
    assert flow.artifact_kinds == ("mini.conjecture.v1",)
    assert flow.commitment_policy.mandatory_skeleton_wf is True
    assert flow.commitment_policy.model_authored_forbidden is True
    shell = resolve_seat_shell(stage.seat_id, stage.shell_id)
    assert shell.shell_id == "seat.mini.conjecturer.legacy-v0"
    assert form_for_seat(stage.seat_id, shell_id=stage.shell_id).form_id == "mini.conjecturer.legacy-v0"
    # and it is NOT the seat's default shell: selecting nothing on the seat
    # still gives the relaxed one; the legacy flow names its shell explicitly
    assert resolve_seat_shell("mini.conjecturer").shell_id == "seat.mini.conjecturer.v0"


def test_the_isolation_flow_is_conjecturer_critic_commitment_with_both_channels_off():
    from minireason.flow import resolve_mini_flow

    flow = resolve_mini_flow("mini.flow.isolation.v1")
    assert [(s.stage_id, s.seat_id, s.per_target) for s in flow.stages] == [
        ("conjecture", "mini.conjecturer", False),
        ("criticism", "mini.critic", True),
        ("commitment", "mini.commitment", True),
    ]
    assert [s.produces_kind for s in flow.stages] == [
        "mini.conjecture.v1", "mini.criticism.v1", "mini.commitment-proposal.v1",
    ]
    assert all(s.reads_kinds == ("mini.conjecture.v1",) for s in flow.stages[1:])
    assert set(flow.artifact_kinds) == {
        "mini.conjecture.v1", "mini.criticism.v1", "mini.commitment-proposal.v1",
    }
    assert flow.commitment_policy.disabled_channels == ("skeleton-wf", "model-authored-forbidden")
    assert flow.calibration_hook_id == "mini.calibration.noop.v1"


def test_a_stage_naming_an_undeclared_kind_is_refused_typed():
    """The SET of artifact kinds is data the flow declares; a stage that names
    a kind outside it is refused at construction, never carried silently."""
    from minireason.flow import MiniFlowError, MiniFlowV1, MiniStageV1

    with pytest.raises(MiniFlowError) as refused:
        MiniFlowV1(
            flow_id="mini.flow.probe",
            flow_version="0.0.1",
            stages=(MiniStageV1("s", "mini.conjecturer", "seat.mini.conjecturer.v0", "mini.other.v1"),),
            artifact_kinds=("mini.conjecture.v1",),
        )
    assert refused.value.code == "MINI_FLOW_KIND_UNDECLARED"
    with pytest.raises(MiniFlowError) as empty:
        MiniFlowV1(flow_id="mini.flow.empty", flow_version="0", stages=(), artifact_kinds=())
    assert empty.value.code == "MINI_FLOW_EMPTY"


def _cases():
    text = GOLDEN.read_text(encoding="utf-8")
    cases = []
    for block in text.split("=== CASE ")[1:]:
        header, body = block.split("\n", 1)
        body = body[: body.index("\n=== END\n")]
        cases.append((header, body))
    return cases


@pytest.mark.parametrize("header,body", _cases())
def test_the_legacy_brief_is_todays_prompt_byte_for_byte(tmp_path, header, body):
    """C4 for the reduced engine's own default: the legacy shell renders
    TODAY's conjecturer prompt exactly, pinned by a golden captured from the
    loop's own prompt builder before anything moved. The one visible
    difference is the section header the shared allocator prefixes, and it
    is asserted rather than glossed."""
    import ast
    import re

    from minireason.seats import CONJECTURER_LEGACY_SHELL, render_mini_brief

    match = re.fullmatch(
        r"description=(.*?) stance=(.*?) neighbourhood=(.*?) vs_k=(\d+)", header
    )
    assert match, header
    parts = {
        "description": ast.literal_eval(match.group(1)),
        "stance": ast.literal_eval(match.group(2)),
        "neighbourhood": ast.literal_eval(match.group(3)),
        "vs_k": int(match.group(4)),
    }

    def endpoint_fn(prompt):
        return json.dumps({"candidates": [{"content": json.dumps(
            {"claim": "c", "mechanism": "m", "forbidden": [{"case": "x", "eval": "program:json-wf"}]}
        ), "typicality": 0.5}]})

    root = tmp_path / "run"
    run([("pi-0", parts["description"])], MockEndpoint(endpoint_fn), budget=100_000,
        root=root, vs_k=1, max_cycles=1)
    brief = render_mini_brief(
        Session(root), "mini.conjecturer", "pi-0",
        shell_id=CONJECTURER_LEGACY_SHELL.shell_id,
        supplied={"vs_k": parts["vs_k"], "stance_directive": parts["stance"],
                  "legacy_neighbourhood": parts["neighbourhood"]},
    )
    assert brief.startswith("## legacy-prompt\n")
    assert brief[len("## legacy-prompt\n"):] == body
