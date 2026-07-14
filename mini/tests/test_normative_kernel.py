"""W7: MiniReason is a reduced scheduler over one normative kernel."""

import json

import pytest

from deepreason.harness import Harness, WellFormednessError
from deepreason.ontology import Artifact, Commitment, Event, Status, Warrant
from minireason.call import MockEndpoint
from minireason.checks import compile_checks
from minireason.loop import RUBRIC_POLICY_ERROR, Session, run


def _candidate(session: Session, content: str, pid: str = "pi-0") -> str:
    checks = compile_checks(content)
    commitment_ids = session.register_commitments(checks)
    assert commitment_ids
    artifact = session.build_candidate(content, commitment_ids, "mechanist")
    return session.register_candidates(
        [(artifact, [])], pid, None
    )[0]


def test_session_projects_canonical_objects_events_and_computed_ids(tmp_path):
    session = Session(tmp_path / "run")
    session.spawn_problem("pi-0", "why?")
    content = json.dumps(
        {
            "claim": "c",
            "mechanism": "m",
            "forbidden": [{"case": "valid json", "eval": "program:json-wf"}],
        }
    )
    checks = compile_checks(content)
    commitment_ids = session.register_commitments(checks)
    artifact = session.build_candidate(content, commitment_ids, "mechanist")
    [actual_id] = session.register_candidates(
        [(artifact, [])],
        "pi-0",
        None,
    )

    assert actual_id == Artifact.compute_id(
        f"inline:{content}",
        "utf8",
        session.harness.state.artifacts[actual_id].interface,
    )
    assert all(isinstance(value, Artifact) for value in session.harness.state.artifacts.values())
    assert all(isinstance(value, Commitment) for value in session.harness.commitments.values())
    assert all(isinstance(event, Event) for event in session.state.events)
    assert session.state.statuses == session.harness.state.status


def test_attack_on_validity_node_reinstates_via_parent_adjudicator(tmp_path):
    root = tmp_path / "run"
    session = Session(root)
    session.spawn_problem("pi-0", "why?")
    doomed = json.dumps(
        {
            "claim": "doomed",
            "mechanism": "wrong",
            "forbidden": [{"case": "valid json", "eval": "program:json-wf"}],
        }
    )
    target = _candidate(session, doomed)
    session.refute(
        target,
        [{"commitment": "skeleton-wf", "eval": "program:skeleton_wf", "verdict": "fail"}],
    )
    warrant = next(value for value in session.harness.warrants.values() if value.target == target)
    assert isinstance(warrant, Warrant)
    assert session.state.canonical_status(target) == Status.REFUTED

    session.register_commitments(
        [{"id": "validity-check", "eval": "program:json-wf", "budget": {"extra": {}}}]
    )
    session.refute(
        warrant.validity_node,
        [{"commitment": "validity-check", "eval": "program:json-wf", "verdict": "fail"}],
    )

    replayed = Harness(root)
    assert session.state.statuses == replayed.state.status
    assert session.state.canonical_status(target) == Status.ACCEPTED
    assert target in session.survivors("pi-0")


def test_rubric_candidate_is_logged_and_never_registered(tmp_path):
    content = json.dumps(
        {
            "claim": "requires a judge",
            "mechanism": "subjective comparison",
            "forbidden": [{"case": "quality", "eval": "rubric:std-quality"}],
        }
    )
    root = tmp_path / "run"
    summary = run(
        [("pi-0", "why?")],
        MockEndpoint(
            [json.dumps({"candidates": [{"content": content, "typicality": 0.5}]})]
        ),
        budget=100_000,
        root=root,
        vs_k=1,
        max_cycles=1,
    )
    session = Session(root)

    assert summary["problems"] == {"pi-0": 0}
    assert session.state.artifacts == {}
    assert not any(c.eval.startswith("rubric:") for c in session.harness.commitments.values())
    assert any(RUBRIC_POLICY_ERROR in event.inputs for event in session.state.events)
    assert not any(event.rule.value == "Conj" for event in session.state.events)
    assert summary["meter_equals_log"]


def test_direct_rubric_commitment_batch_is_atomic_process_drop(tmp_path):
    session = Session(tmp_path / "run")
    accepted = session.register_commitments(
        [
            {"id": "safe", "eval": "program:json-wf"},
            {"id": "judge-only", "eval": "rubric:std-quality"},
        ]
    )

    assert accepted == []
    assert session.harness.commitments == {}
    assert session.state.events[-1].rule.value == "Measure"
    assert RUBRIC_POLICY_ERROR in session.state.events[-1].inputs


def test_blocked_model_candidate_leaves_no_commitment_residue(tmp_path):
    root = tmp_path / "run"
    session = Session(root)
    session.spawn_problem("pi-0", "why?")
    prior = json.dumps(
        {
            "claim": "prior",
            "mechanism": "same program verdicts",
            "forbidden": [
                {"case": "prior case", "eval": "program:json-wf"}
            ],
        }
    )
    prior_checks = compile_checks(prior)
    prior_ids = session.register_commitments(prior_checks)
    prior_artifact = session.build_candidate(prior, prior_ids, "mechanist")
    session.register_candidates([(prior_artifact, [])], "pi-0", None)
    session.refute(
        prior_artifact.id,
        [
            {
                "commitment": prior_ids[0],
                "eval": "program:skeleton_wf",
                "verdict": "fail",
            }
        ],
    )

    # Contract change (bronze flat v1 repair): a structural-only battery no
    # longer blocks, so the only reachable block in mini's check vocabulary
    # is stage-1 exact hash - the model re-emitting the refuted prior. The
    # invariant under test is unchanged: a blocked candidate must leave the
    # commitment registry and artifact set untouched.
    blocked = prior
    commitments_before = set(session.harness.commitments)

    summary = run(
        [("pi-0", "why?")],
        MockEndpoint(
            [
                json.dumps(
                    {
                        "candidates": [
                            {"content": blocked, "typicality": 0.5}
                        ]
                    }
                )
            ]
        ),
        budget=100_000,
        root=root,
        vs_k=1,
        max_cycles=1,
    )

    reopened = Session(root)
    assert summary["gate_blocks"] == 1
    assert set(reopened.harness.commitments) == commitments_before
    assert [
        artifact.content_ref.removeprefix("inline:")
        for artifact in reopened.harness.state.artifacts.values()
    ].count(blocked) == 1  # the prior itself, never a second registration


def test_problem_identity_conflict_uses_parent_well_formedness(tmp_path):
    session = Session(tmp_path / "run")
    session.spawn_problem("pi-0", "first")
    event_count = len(session.state.events)
    session.spawn_problem("pi-0", "first")
    assert len(session.state.events) == event_count

    with pytest.raises(WellFormednessError, match="conflicts"):
        session.spawn_problem("pi-0", "different")
