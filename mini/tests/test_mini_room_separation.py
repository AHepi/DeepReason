"""R4, enforced (writer's-room tranche S3): commitments exist OUTSIDE
conjecture artifacts.

The operator's condition on the room forms (2026-09-06): "only if the
commitments exist outside conjecture artifacts." Verified on the D8 root
before any change; this test makes it a property that goes red the moment
it stops holding. `assert_separated` is the check; the planted mutation in
the tranche's proof (a proposal body written into its target artifact) turns
it red -- see CHECKLIST step 8.
"""

import json

from deepreason.ontology.artifact import Artifact
from minireason.call import MockEndpoint
from minireason.flow import ROOM_FLOW_ID
from minireason.loop import Session, run
from minireason.records import mini_records

RECORD_KINDS = {"mini.criticism.v1", "mini.commitment-proposal.v1"}


def assert_separated(session) -> dict:
    state = session.harness.state
    conjectures = {
        aid: art for aid, art in state.artifacts.items()
        if getattr(art.provenance.role, "value", art.provenance.role) == "conjecturer"
    }
    records = [r for r in mini_records(session) if r.kind in RECORD_KINDS]
    assert conjectures and records, "the run produced no conjecture or no record"

    # 1. a conjecture artifact IS its content: the id recomputes from what it
    #    holds now, so nothing was written into it after registration
    for aid, art in conjectures.items():
        assert Artifact.compute_id(art.content_ref, art.codec, art.interface) == aid, aid
    # 2. no conjecture carries a warrant or a canonical commitment from the room
    assert all(not art.warrants for art in conjectures.values())
    assert not getattr(state, "commitments", {}), "the room registered a canonical commitment"
    # 3. every record is its own object ABOUT a conjecture that exists ...
    assert all(r.about and r.about[0] in conjectures for r in records)
    # 4. ... and no conjecture's content contains any record's body
    for r in records:
        head = r.content.strip()[:80]
        assert head and not any(head in art.content_ref for art in conjectures.values()), (
            f"record {r.ref[:8]} text found inside a conjecture artifact")
    # 5. every record was written AFTER the artifact it is about
    registered = {}
    for e in session.state.events:  # the log view; the harness state holds no event list
        for out in e.outputs:
            registered.setdefault(out, e.seq)
    for r in records:
        assert r.seq > registered[r.about[0]], (r.ref[:8], r.seq, registered[r.about[0]])
    return {"conjectures": len(conjectures), "records": len(records)}


def _endpoint(calls):
    def endpoint_fn(prompt):
        calls.append(prompt)
        n = len(calls)
        schema = prompt.split("SYNTAX EXAMPLE", 1)[0]
        if "CRITIC SEAT" in schema:
            t = prompt.split("TARGET CONJECTURE ", 1)[1].split("\n", 1)[0].strip()
            return json.dumps({"objections": [{"about": t, "body": f"objection {n}: the mechanism is asserted, not shown."}]})
        if "COMMITMENT SEAT" in schema:
            t = prompt.split("TARGET CONJECTURE ", 1)[1].split("\n", 1)[0].strip()
            return json.dumps({"proposals": [{"about": t, "body": f"proposal {n}: it is refuted if the sky is red at noon.", "kind": "refuted-if"}]})
        return json.dumps({"candidates": [
            {"content": f"conjecture {n}a: sunlight scatters off molecules smaller than its wavelength."},
            {"content": f"conjecture {n}b: the horizon whitens under multiple scattering."},
        ]})
    return MockEndpoint(endpoint_fn)


def test_commitments_and_criticisms_live_outside_conjecture_artifacts(tmp_path):
    calls: list[str] = []
    run([("pi-0", "why does the sky look blue?")], _endpoint(calls),
        budget=600_000, root=tmp_path / "room", vs_k=2, max_cycles=2, flow=ROOM_FLOW_ID)
    counts = assert_separated(Session(tmp_path / "room"))
    assert counts == {"conjectures": 4, "records": 8}, counts
