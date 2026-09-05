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
    assert [s.stage_id for s in flow.stages] == ["mini.stage.conjecture"]
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
        ("mini.stage.conjecture", "mini.conjecturer", False),
        ("mini.stage.criticism", "mini.critic", True),
        ("mini.stage.commitment", "mini.commitment", True),
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


# ------------------------------------------------ the loop walks the flow


def _stage_endpoint(calls):
    """A stub that answers each seat in the form its shell asks for, decided
    from the BRIEF it was shown -- which is the whole point: the stub can tell
    the seats apart only by what they were shown."""

    def endpoint_fn(prompt):
        calls.append(prompt)
        if "You are the critic seat" in prompt:
            target = prompt.split("TARGET CONJECTURE ", 1)[1].split("\n", 1)[0].strip()
            return json.dumps({"objections": [
                {"about": target, "body": f"OBJECTION-SENTINEL-{len(calls)}: the mechanism is asserted, not shown."},
            ]})
        if "You are the commitment seat" in prompt:
            target = prompt.split("TARGET CONJECTURE ", 1)[1].split("\n", 1)[0].strip()
            return json.dumps({"proposals": [
                {"about": target, "body": f"PROPOSAL-SENTINEL-{len(calls)}: it forbids a red sky at noon."},
            ]})
        return json.dumps({"candidates": [
            {"content": f"Free prose conjecture number {len(calls)}: sunlight scatters "
                        f"off molecules much smaller than its wavelength.", "typicality": 0.5},
        ]})

    return MockEndpoint(endpoint_fn)


def test_the_isolation_flow_runs_end_to_end(tmp_path):
    """S8, live against the stub: conjecture -> criticism -> commitment, two
    cycles, commitments off. Every stage's output lands in the record in its
    kind; the critic was never shown a proposal; the record replays and
    verifies; the meter equals the log."""
    from deepreason.invariants import verify_root
    from minireason.log import replay
    from minireason.records import mini_records

    calls: list[str] = []
    root = tmp_path / "iso"
    summary = run([("pi-0", "why does the sky look blue?")], _stage_endpoint(calls),
                  budget=300_000, root=root, vs_k=1, max_cycles=2,
                  flow="mini.flow.isolation.v1")
    session = Session(root)

    assert summary["flow"] == "mini.flow.isolation.v1"
    assert summary["stop"] == "queue-exhausted" and summary["cycles"] == 2
    assert summary["refuted"] == 0 and summary["problems"] == {"pi-0": 2}
    assert summary["meter_equals_log"]

    kinds = [r.kind for r in mini_records(session)]
    assert kinds == ["mini.criticism.v1", "mini.commitment-proposal.v1"] * 2, kinds
    conjectures = session.survivors("pi-0")
    assert all(r.about[0] in conjectures for r in mini_records(session))

    # six calls: (conjecture, criticism, commitment) x 2 cycles, in that order
    assert len(calls) == 6
    assert "You are the conjecture seat" in calls[0]
    assert "You are the critic seat" in calls[1]
    assert "You are the commitment seat" in calls[2]
    # the critic was shown no proposal and no objection, in either cycle
    for prompt in (calls[1], calls[4]):
        assert "PROPOSAL-SENTINEL" not in prompt and "OBJECTION-SENTINEL" not in prompt
    # the second cycle's conjecturer and commitment seat saw the first cycle's
    # criticism and proposal, whole
    assert "OBJECTION-SENTINEL-2" in calls[3] and "PROPOSAL-SENTINEL-3" in calls[3]
    assert "OBJECTION-SENTINEL-2" in calls[5] and "PROPOSAL-SENTINEL-3" in calls[5]
    # the commitments-disabled warning is in the record; no brief was clipped
    markers = [i for e in session.state.events for i in e.inputs if i.startswith("mini:")]
    assert any(m.startswith("mini:commitments-disabled") for m in markers)
    assert not any(m == "mini:brief-clipped" for m in markers)

    assert replay(root).digest() == session.state.digest()
    assert verify_root(root)["violations"] == []


def test_the_legacy_flow_runs_exactly_as_before(tmp_path):
    """C1/C4: selecting nothing walks the legacy flow -- one conjecturer
    stage, the stored form, both channels on -- and the record shows it: no
    mini record of any kind, the skeleton candidates admitted and checked,
    no commitments-disabled warning."""
    from minireason.records import mini_records

    calls: list[str] = []

    def endpoint_fn(prompt):
        calls.append(prompt)
        return json.dumps({"candidates": [{"content": json.dumps(
            {"claim": f"claim {len(calls)}", "mechanism": "m",
             "forbidden": [{"case": "x", "eval": "program:json-wf"}]}
        ), "typicality": 0.5}]})

    root = tmp_path / "legacy"
    summary = run([("pi-0", "why did X happen?")], MockEndpoint(endpoint_fn),
                  budget=200_000, root=root, vs_k=1, max_cycles=2)
    session = Session(root)
    assert summary["flow"] == "mini.flow.legacy-v0"
    assert summary["problems"] == {"pi-0": 2} and summary["refuted"] == 0
    assert mini_records(session) == ()
    assert all("## legacy-prompt\n" in p and "JSON skeleton" in p for p in calls)
    assert "RECENT SURVIVORS" in calls[1]
    markers = [i for e in session.state.events for i in e.inputs if i.startswith("mini:")]
    assert markers == []
