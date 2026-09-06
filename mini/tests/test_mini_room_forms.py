"""The writer's-room forms (tranche S2): three forms, three shells, one flow,
registered beside the stored ones and selectable by id; the seat's task is
on the wire in the schema itself; optional labels ride with the prose.
"""

import json

from minireason.call import MockEndpoint
from minireason.flow import ROOM_FLOW_ID, resolve_mini_flow
from minireason.forms import mini_form_ids, resolve_mini_form
from minireason.loop import Session, run
from minireason.records import mini_records

ROOM_FORMS = ("mini.conjecturer.room.v1", "mini.critic.room.v1", "mini.commitment.room.v1")


def test_the_room_forms_and_flow_are_registered_beside_the_stored_ones():
    ids = set(mini_form_ids())
    assert set(ROOM_FORMS) <= ids
    # the stored default and the relaxed set are untouched (R-stored)
    assert {"mini.conjecturer.legacy-v0", "mini.conjecturer.relaxed.v1",
            "mini.critic.relaxed.v1", "mini.commitment.relaxed.v1"} <= ids
    flow = resolve_mini_flow(ROOM_FLOW_ID)
    assert [s.shell_id for s in flow.stages] == [
        "seat.mini.conjecturer.room.v1", "seat.mini.critic.room.v1", "seat.mini.commitment.room.v1"]
    assert flow.brief_budget_chars == 12_000
    assert len(flow.commitment_policy.disabled_channels) == 2
    # the isolation flow still binds the relaxed forms, not the room ones
    iso = resolve_mini_flow("mini.flow.isolation.v1")
    assert all(".room." not in s.shell_id for s in iso.stages)


def test_the_seats_task_travels_in_the_schema():
    """The schema is prepended AFTER the call layer's clip, so a description
    there survives any cut. Each room form's top-level description states the
    seat and its job; the commitment seat's says what a proposal is NOT."""
    conj = resolve_mini_form("mini.conjecturer.room.v1").contract.model_json_schema()
    crit = resolve_mini_form("mini.critic.room.v1").contract.model_json_schema()
    comm = resolve_mini_form("mini.commitment.room.v1").contract.model_json_schema()
    assert conj["description"].startswith("CONJECTURE SEAT.")
    assert crit["description"].startswith("CRITIC SEAT.") and "overturns nothing" in crit["description"]
    assert comm["description"].startswith("COMMITMENT SEAT.")
    assert "do not answer the problem" in comm["description"]
    # nothing required beyond content / about+body; labels optional
    assert comm["$defs"]["MiniRoomProposal"]["required"] == ["about", "body"]
    assert crit["$defs"]["MiniRoomObjection"]["required"] == ["about", "body"]
    assert conj["$defs"]["MiniRoomCandidate"]["required"] == ["content"]
    for schema in (conj, crit, comm):
        assert "maxLength" not in json.dumps(schema)


def _room_endpoint(calls):
    def endpoint_fn(prompt):
        calls.append(prompt)
        n = len(calls)
        schema = prompt.split("SYNTAX EXAMPLE", 1)[0]
        if "CRITIC SEAT" in schema:
            target = prompt.split("TARGET CONJECTURE ", 1)[1].split("\n", 1)[0].strip()
            return json.dumps({"objections": [
                {"about": target, "body": f"OBJ-{n}: the mechanism is asserted, not shown.",
                 "would_settle": "a measured spectrum at the horizon"},
                {"about": target, "body": f"OBJ-{n}b: it explains too much."},
            ]})
        if "COMMITMENT SEAT" in schema:
            target = prompt.split("TARGET CONJECTURE ", 1)[1].split("\n", 1)[0].strip()
            return json.dumps({"proposals": [
                {"about": target, "body": f"PROP-{n}: it is refuted if the sky is red at noon.", "kind": "refuted-if"},
                {"about": target, "body": f"PROP-{n}b: it forbids a green sunset."},
            ]})
        assert "CONJECTURE SEAT" in schema
        return json.dumps({"candidates": [
            {"content": f"CONJ-{n}a: sunlight scatters off molecules smaller than its wavelength.", "angle": "mechanism"},
            {"content": f"CONJ-{n}b: the horizon whitens under multiple scattering."},
        ]})
    return MockEndpoint(endpoint_fn)


def test_the_room_flow_runs_end_to_end_and_keeps_the_labels(tmp_path):
    calls: list[str] = []
    root = tmp_path / "room"
    summary = run([("pi-0", "why does the sky look blue?")], _room_endpoint(calls),
                  budget=600_000, root=root, vs_k=2, max_cycles=2, flow=ROOM_FLOW_ID)
    session = Session(root)
    assert summary["flow"] == ROOM_FLOW_ID and summary["cycles"] == 2
    assert summary["refuted"] == 0 and summary["problems"] == {"pi-0": 4}
    assert summary["meter_equals_log"]
    recs = list(mini_records(session))
    kinds = {r.kind for r in recs}
    assert kinds == {"mini.criticism.v1", "mini.commitment-proposal.v1"}
    # every objection and proposal is about a conjecture that exists
    conjectures = session.survivors("pi-0")
    assert all(r.about[0] in conjectures for r in recs)
    # the optional labels rode with the prose, appended, prose intact
    props = [r.content for r in recs if r.kind == "mini.commitment-proposal.v1"]
    assert any(c.endswith("\n[kind: refuted-if]") and c.startswith("PROP-") for c in props)
    assert any("[kind:" not in c for c in props)
    objs = [r.content for r in recs if r.kind == "mini.criticism.v1"]
    assert any(c.endswith("\n[would settle: a measured spectrum at the horizon]") for c in objs)
    # a candidate's angle rides with its content
    arts = [a.content_ref for a in session.harness.state.artifacts.values()
            if getattr(a.provenance.role, "value", a.provenance.role) == "conjecturer"]
    assert any(c.endswith("\n[angle: mechanism]") for c in arts)
    # the seat's task was on every wire, in the schema, before any brief text
    assert all(("SEAT." in p.split("SYNTAX EXAMPLE", 1)[0]) for p in calls)
    # no brief was clipped under the room's own limit
    assert not [i for e in session.state.events for i in e.inputs if i == "mini:brief-clipped"]
    # the critic saw no proposal and no objection (who sees what is unchanged)
    for p in calls:
        if "CRITIC SEAT" in p.split("SYNTAX EXAMPLE", 1)[0]:
            assert "PROP-" not in p and "OBJ-" not in p.split("## target-conjecture", 1)[1]
