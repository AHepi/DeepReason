"""The commitment seat: it reads a conjecture and PROPOSES commitments in free
prose, and nothing it writes changes anything.

Implements S4 (R4, R13, R14, C9) of the mini isolation programme. R4 is the
operator's "a new kind of artifact that generates commitments on conjectures,
but does not force a strict format"; the ruling of 2026-09-05 is that within
mini criticism overturns nothing, and Q-A's road E3 -- elimination arriving
with the commitment artifact -- is NOT built.

A proposal is a RECORD, not an artifact: a Measure event carrying the kind,
the conjecture it is about, and a blob with its body. That puts it in the
record (typed, append-only, replayable, spend attached) and outside the one
map every authority path reads (`state.artifacts`). The tests below hold the
writer to exactly that.
"""

import json

import pytest

from deepreason.invariants import verify_root
from minireason.call import MockEndpoint
from minireason.log import replay
from minireason.loop import Session, run


def _skeleton(i: int) -> str:
    return json.dumps(
        {"claim": f"claim {i}", "mechanism": f"mechanism {i}",
         "forbidden": [{"case": "x", "eval": "program:json-wf"}]}
    )


@pytest.fixture
def session(tmp_path):
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        return json.dumps({"candidates": [
            {"content": _skeleton(2 * calls["n"] + i), "typicality": 0.5} for i in range(2)
        ]})

    root = tmp_path / "run"
    run([("pi-0", "why did X happen?")], MockEndpoint(endpoint_fn), budget=200_000,
        root=root, vs_k=2, max_cycles=2)
    return Session(root)


def _proposals(*pairs):
    from minireason.forms import resolve_mini_form

    model = resolve_mini_form("mini.commitment.relaxed.v1").wire_model
    return model.model_validate(
        {"proposals": [{"about": about, "body": body} for about, body in pairs]}
    )


def test_the_only_requirement_is_naming_the_conjecture():
    """SPEC S4's accept, verbatim: the minimum is accepted, and a proposal
    that names nothing is refused by the FORM."""
    import pydantic

    from minireason.forms import resolve_mini_form

    m = resolve_mini_form("mini.commitment.relaxed.v1").wire_model
    m.model_validate({"proposals": [{"about": "a1", "body": "x"}]})
    with pytest.raises(pydantic.ValidationError):
        m.model_validate({"proposals": [{"body": "x"}]})
    # and nothing else is required or bounded: one long paragraph is a proposal
    m.model_validate({"proposals": [{"about": "a1", "body": "prose " * 5000}]})


def test_a_proposal_is_recorded_and_registers_nothing(session):
    """R4 + R13: the proposal reaches the record with its spend, its kind,
    what it is about and its whole body -- and no artifact, no commitment and
    no status moves."""
    from minireason.records import MINI_RECORD_MARKER, mini_records
    from minireason.seats import COMMITMENT_PROPOSAL_KIND, record_commitment_proposals

    target = session.survivors("pi-0")[0]
    artifacts_before = set(session.state.artifacts)
    commitments_before = set(session.state.commitments)
    statuses_before = dict(session.state.statuses)
    events_before = len(session.state.events)

    body = "It must not predict that X happens without Y; if X ever happens with no Y at all, this is wrong."
    events = record_commitment_proposals(session, _proposals((target, body), (target, "and a second, shorter one")))
    assert len(events) == 2 and all(e is not None for e in events)
    assert events[0].inputs[0] == MINI_RECORD_MARKER
    assert f"kind:{COMMITMENT_PROPOSAL_KIND}" in events[0].inputs
    assert f"about:{target}" in events[0].inputs

    records = mini_records(session)
    assert [r.kind for r in records] == [COMMITMENT_PROPOSAL_KIND] * 2
    assert records[0].about == (target,) and records[0].content == body

    assert set(session.state.artifacts) == artifacts_before
    assert set(session.state.commitments) == commitments_before
    assert dict(session.state.statuses) == statuses_before
    assert len(session.state.events) == events_before + 2
    assert replay(session.root).digest() == session.state.digest()
    assert verify_root(session.root)["violations"] == []


def test_a_proposal_about_nothing_in_the_run_is_dropped_typed(session):
    """Disclose, never die: the one requirement, when unmet at the point of
    use, is a typed event in the record rather than a dangling reference."""
    from minireason.records import MINI_RECORD_DROPPED_MARKER, mini_records
    from minireason.seats import record_commitment_proposals

    target = session.survivors("pi-0")[0]
    events = record_commitment_proposals(
        session, _proposals(("not-an-artifact-in-this-run", "x"), (target, "y"))
    )
    assert events[0] is None and events[1] is not None
    dropped = [e for e in session.state.events if e.inputs and e.inputs[0] == MINI_RECORD_DROPPED_MARKER]
    assert len(dropped) == 1
    assert "MINI_RECORD_ABOUT_UNKNOWN" in dropped[0].inputs
    assert "about:not-an-artifact-in-this-run" in dropped[0].inputs
    assert [r.content for r in mini_records(session)] == ["y"]


def test_the_spend_lands_exactly_once(session):
    """G1: the meter and the log agree. One call, two proposals, one spend."""
    from minireason.log import Call
    from minireason.seats import record_commitment_proposals

    target = session.survivors("pi-0")[0]
    before = session.state.logged_tokens()
    spend = Call(role="commitment", model="mock", endpoint="mock", tokens=123,
                 prompt_ref="", raw_ref="")
    record_commitment_proposals(session, _proposals((target, "a"), (target, "b")), spend=spend)
    assert session.state.logged_tokens() == before + 123


def test_the_seats_that_see_everything_see_the_proposal_and_the_critic_does_not(session):
    """The T3 exposure claim, re-proven with the REAL writer rather than a
    planted artifact: R6 for the conjecturer and the commitment seat, R5 for
    the critic, as bytes."""
    from minireason.seats import record_commitment_proposals, render_mini_brief

    target = session.survivors("pi-0")[0]
    body = "PROPOSAL-SENTINEL: it forbids X without Y."
    record_commitment_proposals(session, _proposals((target, body)))
    for seat in ("mini.conjecturer", "mini.commitment"):
        text = render_mini_brief(session, seat, "pi-0", target_id=target, supplied={"vs_k": 2})
        assert body in text and "mini.commitment-proposal.v1" in text and f"about: {target}" in text
    critic = render_mini_brief(session, "mini.critic", "pi-0", target_id=target)
    assert "PROPOSAL-SENTINEL" not in critic and "commitment-proposal" not in critic
