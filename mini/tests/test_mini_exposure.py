"""Who sees what, as bytes: a critic in mini never sees a commitment proposal,
a conjecturer and the commitment seat see everything, and no mini brief
carries a status label of any kind.

Implements S5 (R5, R6) of the mini isolation programme and the ruling of
2026-09-05 that within mini a criticism overturns nothing. R5 is the
operator's "critics see the conjecture artifact, not the proposed
commitments"; R6 is "conjecturers see everything generated so far and so do
commitment artifacts".

THE ASSERTIONS ARE ON BYTES, NOT COUNTS. A filter that stripped proposal text
from a rendered section would pass a count of sections and fail here; a
present-but-blank slot would pass here and fail the structural test, which is
why both exist. The proposals are PLANTED into a live root through the
harness's own registration road, because T4 builds the seat that writes them
and this test must not wait for it: what the critic is shown depends on the
layout, not on who wrote the artifact.

The status-label test plants a REFUTED artifact deliberately: the point is
that a refuted conjecture is still shown to the seats that see everything --
whole, unlabelled -- and that the critic's brief names no verdict either.
"""

import json

import pytest

from deepreason.invariants import verify_root
from deepreason.ontology import Interface, Provenance, Ref, Rule
from minireason.call import MockEndpoint
from minireason.loop import Session, run

_PROSE = (
    "Sunlight scatters off molecules much smaller than its wavelength, and the "
    "short-wavelength end scatters far more strongly. "
)
_LABELS = ("accepted", "refuted", "suspended", "status", "sustained", "verdict:")


def _mixed_endpoint():
    """Alternates one skeleton candidate (survives the mandatory check) with
    one free-prose candidate (refuted on arrival under the default policy)."""
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": json.dumps(
                            {
                                "claim": f"claim {calls['n']}",
                                "mechanism": f"mechanism {calls['n']}",
                                "forbidden": [{"case": "x", "eval": "program:json-wf"}],
                            }
                        ),
                        "typicality": 0.5,
                    },
                    {"content": f"{_PROSE}(prose variation {calls['n']})", "typicality": 0.5},
                ]
            }
        )

    return MockEndpoint(endpoint_fn)


def _plant(session, *, about, body):
    """A commitment proposal written to the record the way any artifact is:
    the harness's own road, a MENTION ref to the conjecture it is about, and
    free prose. Returns its id."""
    artifact = session.harness.create_artifact(
        json.dumps({"about": about, "body": body}),
        codec="json",
        interface=Interface(refs=[Ref(target=about, role="mention")]),
        provenance=Provenance(role="user", event_seq=session.harness._next_seq),
        problem_id="pi-0",
        rule=Rule.REGISTER,
    )
    return artifact.id


@pytest.fixture
def planted(tmp_path):
    """A live root: 2 standing conjectures, 2 refuted prose conjectures, and
    three commitment proposals about the first standing one."""
    root = tmp_path / "run"
    run([("pi-0", "why does the sky look blue?")], _mixed_endpoint(),
        budget=200_000, root=root, vs_k=2, max_cycles=2)
    session = Session(root)
    standing = session.survivors("pi-0")
    refuted = sorted(session.state.refuted)
    assert len(standing) == 2 and len(refuted) == 2, (standing, refuted)
    target = standing[0]
    bodies = [
        f"PROPOSAL-SENTINEL-{i}: it must not predict a red sky at noon, and it "
        f"fails if any measurement shows long wavelengths scatter more."
        for i in range(3)
    ]
    ids = [_plant(session, about=target, body=body) for body in bodies]
    assert verify_root(root)["violations"] == []
    return session, target, refuted, bodies, ids


def _brief(session, seat, target, **kw):
    from minireason.seats import render_mini_brief

    receipts = []
    text = render_mini_brief(session, seat, "pi-0", target_id=target,
                             supplied={"vs_k": 2}, receipts=receipts, **kw)
    return text, receipts


def test_critic_brief_carries_no_proposal_bytes(planted):
    """R5, as a byte assertion: not one character of any proposal body, and
    not one proposal id, reaches the critic's brief -- while the target
    conjecture it is asked about is there whole."""
    from deepreason.programs import content_text

    session, target, _refuted, bodies, ids = planted
    text, receipts = _brief(session, "mini.critic", target)
    for body in bodies:
        assert body not in text
        assert "PROPOSAL-SENTINEL" not in text
    for pid in ids:
        assert pid not in text
    assert content_text(session.harness.state.artifacts[target], session.blobs) in text
    assert {r.section_id for r in receipts} == {"problem", "target-conjecture", "directive"}


def test_the_critic_layout_has_no_slot_a_proposal_could_fill(planted):
    """The structural half of R5: the blinding is an OMISSION from the layout,
    not a filter over a section. Every receipt is a rendered section; none is
    an absent or dropped one that a proposal might have filled."""
    session, target, _refuted, _bodies, _ids = planted
    _text, receipts = _brief(session, "mini.critic", target)
    assert all(r.disposition == "rendered" for r in receipts), [
        (r.section_id, r.disposition) for r in receipts
    ]
    assert "everything-so-far" not in {r.section_id for r in receipts}


@pytest.mark.parametrize("seat", ["mini.conjecturer", "mini.commitment"])
def test_the_seats_that_see_everything_see_every_proposal_whole(planted, seat):
    """R6: conjecturers and the commitment seat see everything generated so
    far -- every proposal, every conjecture, whole, with the proposal's
    `about` link visible."""
    session, target, refuted, bodies, ids = planted
    text, _receipts = _brief(session, seat, target)
    for body, pid in zip(bodies, ids):
        assert body in text
        assert pid in text
    assert f"about: {target}" in text
    for aid in session.survivors("pi-0") + refuted:
        assert aid in text


def test_no_mini_brief_renders_a_status_label(planted):
    """The audit of 2026-09-05 (row 3) found the full harness's default critic
    brief printing status labels. Mini's three briefs print none -- and the
    refuted conjectures are still SHOWN to the seats that see everything,
    whole and unlabelled, because within mini a criticism overturns nothing
    and a label would be the verdict arriving by the back door."""
    from deepreason.programs import content_text

    session, target, refuted, _bodies, _ids = planted
    for seat in ("mini.conjecturer", "mini.critic", "mini.commitment"):
        text, _receipts = _brief(session, seat, target)
        lowered = text.lower()
        for label in _LABELS:
            assert label not in lowered, (seat, label)
        if seat != "mini.critic":
            for aid in refuted:
                assert content_text(session.harness.state.artifacts[aid], session.blobs) in text


def test_rendering_every_brief_appends_nothing(planted):
    session, target, _refuted, _bodies, _ids = planted
    before = session.state.digest()
    seq = session.harness._next_seq
    for seat in ("mini.conjecturer", "mini.critic", "mini.commitment"):
        _brief(session, seat, target)
    assert session.state.digest() == before
    assert session.harness._next_seq == seq
    assert verify_root(session.root)["violations"] == []
