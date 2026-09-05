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
    # `dr.neighbourhood` distils everything BEFORE the layout policy's live
    # tail, which `dr.neighbourhood.live` renders whole; the split is the
    # policy's, so it is read from the request rather than assumed.
    live = request.layout.live_verbatim_n
    distilled = accepted[:-live] if live else accepted
    assert distilled, accepted
    for aid in distilled:
        assert aid in texts["neighbourhood"], aid


def test_the_adapter_writes_nothing(session):
    """`DR-INV-seat-section-sources`' NEVER APPEND clause, owed by mini's
    adapter too: after building requests and walking a layout with them, the
    log's bytes, the next event sequence, the state digest and `verify_root`
    are exactly what they were."""
    from deepreason.invariants import verify_root
    from deepreason.llm.packs import _walk_seat_layout
    from minireason.log import replay
    from minireason.sources import mini_section_request

    layout = _neighbourhood_layout()
    log_path = session.root / "log.jsonl"
    before_bytes = log_path.read_bytes()
    before_seq = session.harness._next_seq
    before_digest = session.state.digest()
    assert verify_root(session.root)["violations"] == []

    for _ in range(2):
        request = mini_section_request(
            session, "pi-0", supplied={"accepted": tuple(session.survivors("pi-0"))}
        )
        _walk_seat_layout("mini.conjecturer", layout.layout_id, request, [])

    assert log_path.read_bytes() == before_bytes
    assert session.harness._next_seq == before_seq
    assert session.state.digest() == before_digest
    assert replay(session.root).digest() == before_digest
    assert verify_root(session.root)["violations"] == []


def test_the_frozen_criteria_reach_the_request_only_from_the_standard_input(tmp_path):
    """R12: a root started from the STANDARD frozen input shows its criteria;
    a root started from a bare question -- mini's constant process root -- has
    none to show and gets an empty tuple, never an error."""
    from deepreason.evidence import (
        AttachedSourceProvenanceV1,
        EvidenceDossierV1,
        RunInputCommitmentV1,
        RunInputManifestV2,
        RunInputProblemV2,
    )
    from minireason.sources import mini_section_request

    dossier = EvidenceDossierV1.create(
        problem_ref="frozen-1",
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="test", acquisition_method="none", note="empty"
        ),
    )
    frozen = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id="frozen-1",
            description="why did X happen?",
            criteria=(
                RunInputCommitmentV1(id="c-mechanism", eval="program:json-wf"),
                RunInputCommitmentV1(id="c-refutable", eval="program:nonempty"),
            ),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    root = tmp_path / "frozen"
    run(
        [("frozen-1", "why did X happen?")],
        _endpoint(),
        budget=200_000,
        root=root,
        vs_k=2,
        max_cycles=1,
        run_input=frozen,
        dossier=dossier,
    )
    request = mini_section_request(Session(root), "frozen-1")
    assert request.supplied["criteria"] == (
        ("c-mechanism", "program:json-wf"),
        ("c-refutable", "program:nonempty"),
    )
    assert request.problem is not None and request.problem.id == "frozen-1"

    bare = tmp_path / "bare"
    run([("pi-0", "why?")], _endpoint(), budget=200_000, root=bare, vs_k=2, max_cycles=1)
    assert mini_section_request(Session(bare), "pi-0").supplied["criteria"] == ()


# ----------------------------------------------- the mini plugins (step 26)


_LONG = (
    "Sunlight scatters off molecules much smaller than its wavelength, and the "
    "short-wavelength end scatters far more strongly, so the sky away from the "
    "sun is dominated by blue; toward the horizon the path is longer and "
    "multiple scattering washes the colour toward white. "
) * 3  # ~700 characters: well past the 300 the legacy neighbourhood cut at


def _prose_endpoint(per_cycle=3):
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        return json.dumps(
            {
                "candidates": [
                    {"content": f"{_LONG}(variation {calls['n']}.{i})", "typicality": 0.5}
                    for i in range(per_cycle)
                ]
            }
        )

    return MockEndpoint(endpoint_fn)


@pytest.fixture
def prose_session(tmp_path):
    """Twelve long free-prose conjectures, all standing (commitments off)."""
    from minireason.policy import MiniCommitmentPolicyV1

    root = tmp_path / "prose"
    run(
        [("pi-0", "why does the sky look blue?")],
        _prose_endpoint(),
        budget=400_000,
        root=root,
        vs_k=3,
        max_cycles=4,
        commitment_policy=MiniCommitmentPolicyV1(
            mandatory_skeleton_wf=False, model_authored_forbidden=False
        ),
    )
    return Session(root)


def _everything(session, **params):
    from deepreason.llm.seat_sections import (
        SeatPackLayoutEntryV1,
        SeatPackLayoutV1,
        register_seat_pack_layout,
    )
    from deepreason.llm.packs import render_seat_brief
    from minireason.sources import mini_section_request

    key = "-".join(f"{k}={v}" for k, v in sorted(params.items())) or "default"
    layout = register_seat_pack_layout(
        SeatPackLayoutV1(
            layout_id=f"seat-pack.mini.everything-probe.{key}",
            entries=(
                SeatPackLayoutEntryV1(
                    plugin_id="mini.everything-so-far", priority=2, params=params
                ),
            ),
        )
    )
    sections, receipts = render_seat_brief(
        "mini.conjecturer", layout.layout_id, mini_section_request(session, "pi-0"), []
    )
    assert len(sections) == 1 and receipts[0].disposition == "rendered"
    return sections[0].text_ref[len("inline:"):]


def test_everything_so_far_shows_every_artifact_in_full(prose_session):
    """R6 and the third limit of R2: every artifact generated so far, whole.

    The legacy loop showed the last 8 survivors at 300 characters each. Here
    twelve artifacts of ~700 characters are all present, byte for byte, and
    none carries a status.
    """
    from deepreason.programs import content_text

    state = prose_session.harness.state
    pool = [a for a in state.artifacts.values() if a.provenance.role.value == "conjecturer"]
    assert len(pool) == 12, len(pool)
    text = _everything(prose_session)
    for artifact in pool:
        assert content_text(artifact, prose_session.blobs) in text, artifact.id
        assert artifact.id in text
    assert "WITHHELD" not in text
    for label in ("accepted", "refuted", "suspended", "status"):
        assert label not in text.lower(), label


def test_the_retention_rule_withholds_oldest_first_and_says_so(prose_session):
    """Retention is a RULE, not a verdict (operator, 2026-09-05): a declared
    budget withholds the OLDEST whole entries, names them, and never empties
    the section."""
    state = prose_session.harness.state
    ordered = [a.id for a in state.artifacts.values() if a.provenance.role.value == "conjecturer"]

    text = _everything(prose_session, budget_chars=2500)
    shown = [aid for aid in ordered if f"] conjecturer {aid}" in text]
    withheld = [aid for aid in ordered if aid not in shown]
    assert shown and withheld, (len(shown), len(withheld))
    # oldest first: everything withheld precedes everything shown
    assert ordered.index(withheld[-1]) < ordered.index(shown[0])
    assert "WITHHELD UNDER RULE mini.retention.everything.v1" in text
    for aid in withheld:
        assert aid in text, "a withheld entry must still be NAMED"
    assert f"{len(withheld)} earlier entr" in text

    # a budget smaller than any single entry still shows the newest one
    tiny = _everything(prose_session, budget_chars=1)
    assert f"] conjecturer {ordered[-1]}" in tiny
    assert f"{len(ordered) - 1} earlier entries" in tiny


def test_the_recency_rule_keeps_the_last_n_and_needs_its_window(prose_session):
    from deepreason.llm.seat_sections import SeatSectionError
    from minireason.sources import MiniSourceError, mini_retention_rule_ids

    assert set(mini_retention_rule_ids()) >= {
        "mini.retention.everything.v1",
        "mini.retention.recency.v1",
    }
    state = prose_session.harness.state
    ordered = [a.id for a in state.artifacts.values() if a.provenance.role.value == "conjecturer"]
    text = _everything(prose_session, retention_rule="mini.retention.recency.v1", keep_last=4)
    assert all(f"] conjecturer {aid}" in text for aid in ordered[-4:])
    assert not any(f"] conjecturer {aid}" in text for aid in ordered[:-4])
    assert "WITHHELD UNDER RULE mini.retention.recency.v1: 8 earlier entries" in text

    with pytest.raises(MiniSourceError) as refused:
        _everything(prose_session, retention_rule="mini.retention.recency.v1")
    assert refused.value.code == "MINI_RETENTION_PARAMETER_MISSING"
    with pytest.raises(MiniSourceError) as unknown:
        _everything(prose_session, retention_rule="mini.retention.merit.v9")
    assert unknown.value.code == "MINI_RETENTION_RULE_UNKNOWN"
    assert SeatSectionError is not MiniSourceError


def test_no_mini_source_reads_an_artifacts_status():
    """The audit of 2026-09-05 (row 3) found the full harness's default critic
    brief printing status labels. Mini's sources may not read one at all:
    checked over the AST rather than a grep, so a renamed local cannot hide
    an attribute read, and every seat file mini renders through is covered."""
    import ast
    import pathlib

    banned_attrs = {"status", "statuses", "accepted", "refuted", "survivors", "canonical_status"}
    offenders = []
    for name in ("sources.py", "seats.py"):
        path = pathlib.Path(__file__).resolve().parents[1] / "minireason" / name
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in banned_attrs:
                offenders.append(f"{name}:{node.lineno}: .{node.attr}")
            if isinstance(node, ast.ImportFrom) and any(a.name == "Status" for a in node.names):
                offenders.append(f"{name}:{node.lineno}: imports Status")
            if isinstance(node, ast.Name) and node.id == "Status":
                offenders.append(f"{name}:{node.lineno}: Status")
    assert not offenders, offenders
