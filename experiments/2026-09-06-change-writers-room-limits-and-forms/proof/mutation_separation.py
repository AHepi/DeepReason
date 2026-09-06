"""Planted mutation for CHECKLIST step 8: the commitment stage writes its
proposal INTO the conjecture space -- a conjecture-role artifact whose content
is the target's content plus the proposal -- through the record, so a fresh
Session replays it. The check must go red."""
import sys, tempfile, pathlib
sys.path.insert(0, "mini"); sys.path.insert(0, "mini/tests")
import minireason.records as records
import minireason.loop as loop
from minireason.loop import Session, run
from minireason.flow import ROOM_FLOW_ID
from test_mini_room_separation import _endpoint, assert_separated

original = records.record_mini_output
def mutated(session, kind, *, body, about=None, named=None, spend=None):
    event = original(session, kind, body=body, about=about, named=named, spend=spend)
    if kind == "mini.commitment-proposal.v1" and about in session.harness.state.artifacts:
        target = session.harness.state.artifacts[about]
        pid = next(iter(session.state.problems))
        art = session.build_candidate(target.content_ref[len("inline:"):] + "\n" + body, [], "mutation")
        session.register_candidates([(art, [])], pid, None)
    return event
records.record_mini_output = mutated
loop.record_mini_output = mutated
with tempfile.TemporaryDirectory() as td:
    run([("pi-0", "q?")], _endpoint([]), budget=600_000, root=pathlib.Path(td) / "m", vs_k=2, max_cycles=2, flow=ROOM_FLOW_ID)
    try:
        assert_separated(Session(pathlib.Path(td) / "m"))
    except AssertionError as e:
        print("MUTATION CAUGHT (red as required):", str(e)[:140]); sys.exit(0)
    print("MUTATION NOT CAUGHT"); sys.exit(1)
