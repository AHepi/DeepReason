"""Text-workload acceptance: real registration, replay, and root verification."""

from __future__ import annotations

import json
from pathlib import Path

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Rule, Status
from deepreason.rules.conj import conj
from deepreason.workloads.text import (
    ReasoningEnvelopeV1,
    ReasoningWorkloadSpec,
    WorkloadProblem,
    seed_reasoning_workload,
)


def _persisted_bytes(root: Path) -> dict[str, bytes]:
    """Snapshot every persisted run file without interpreting its contents."""

    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_reasoning_conj_replays_byte_for_byte_and_verifies_root(tmp_path):
    root = tmp_path / "run"
    live = Harness(root)
    problem = seed_reasoning_workload(
        live,
        ReasoningWorkloadSpec(
            problem=WorkloadProblem(
                id="reason:replay-feedback",
                description="Why can delayed negative feedback oscillate?",
            )
        ),
    )

    response = json.dumps(
        {
            "candidates": [
                {
                    "claim": "A delayed correction can overshoot its target.",
                    "mechanism": (
                        "The controller reacts to an earlier error, so its correction "
                        "continues after the current error has changed sign."
                    ),
                    "counterconditions": [
                        "the delay is removed while the controller gain is held fixed"
                    ],
                    "typicality": 0.37,
                    "optional_refs": [],
                    "sidecar": {
                        "search_signal": "productive",
                        "requested_context_aliases": [],
                    },
                }
            ]
        },
        sort_keys=True,
    )

    def deterministic_completion(prompt: str) -> str:
        # This is a contract fixture, not a model/toolchain simulation.  The
        # assertion proves the fixture is reached through the rendered pack.
        assert problem.description in prompt
        return response

    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(deterministic_completion)},
        live.blobs,
        model_profile="compact",
    )
    registered = conj(
        live,
        problem.id,
        adapter,
        Config(VS_K=1, model_profile="compact"),
    )

    assert len(registered) == 1
    artifact = registered[0]
    envelope = ReasoningEnvelopeV1.model_validate_json(
        artifact.content_ref.removeprefix("inline:")
    )
    assert envelope.claim == "A delayed correction can overshoot its target."
    assert live.state.status[artifact.id] == Status.ACCEPTED
    assert "reasoning-envelope-wf" in artifact.interface.commitments
    assert any(
        commitment.startswith("reason-counter@")
        for commitment in artifact.interface.commitments
    )
    assert "typicality" not in artifact.content_ref
    assert "search_signal" not in artifact.content_ref

    events = list(live.log.read())
    conjecture_event = next(event for event in events if event.rule == Rule.CONJ)
    assert conjecture_event.outputs == [artifact.id]
    assert conjecture_event.llm is not None
    assert conjecture_event.llm.role == "conjecturer"
    assert conjecture_event.llm.attempts == 1

    live_state_bytes = live.state.model_dump_json().encode()
    live_event_bytes = tuple(event.model_dump_json().encode() for event in events)
    persisted_before_replay = _persisted_bytes(root)

    first_replay = Harness(root)
    second_replay = Harness(root)
    assert first_replay.state.model_dump_json().encode() == live_state_bytes
    assert second_replay.state.model_dump_json().encode() == live_state_bytes
    assert tuple(
        event.model_dump_json().encode() for event in first_replay.log.read()
    ) == live_event_bytes

    report = verify_root(root)
    assert report["violations"] == []
    assert report["stats"]["problems"] == 1
    assert report["stats"]["accepted"] == 1
    assert report["stats"]["process"]["profile_totals"]["compact"][
        "eventual_valid"
    ] == 1

    # Replay and verification may read the run but must not rewrite its log,
    # blobs, objects, or operational sidecars.
    assert _persisted_bytes(root) == persisted_before_replay
