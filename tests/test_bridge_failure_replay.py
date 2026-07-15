"""Replay authority for full-harness terminal bridge failures."""

from __future__ import annotations

import json

from deepreason.bridge.events import BridgeAction
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance


def test_stage_a_failure_is_canonical_and_replay_backed(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-failure-replay",
            description="What answer is supported?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    adapter = LLMAdapter(
        {
            "summarizer": MockEndpoint([], name="exhausted-summarizer"),
            "thesis": MockEndpoint([], name="unused-thesis"),
        },
        harness.blobs,
        retry_max=0,
    )

    terminal = harness.build_bridge(
        "problem-failure-replay",
        "answer",
        {"grounding_review": False, "max_grounding_repair_attempts": 0},
        run_manifest_digest="a" * 64,
        stage_a_adapter=adapter,
    )

    assert terminal.process_status == "failure"
    assert terminal.failure_id is not None
    failure = harness.bridge_state.failures[terminal.failure_id]
    assert failure.run_manifest_digest == "a" * 64
    assert failure.problem_ref == terminal.problem_id
    assert failure.output_target == terminal.target
    assert failure.formal_seq == terminal.formal_seq
    assert failure.evidence_pack_id == terminal.evidence_pack_id
    assert failure.error_code == terminal.error_code
    assert failure.error_message == terminal.error_message
    assert failure.catalog_id in harness.bridge_state.catalogs
    assert failure.evidence_pack_id in harness.bridge_state.evidence_packs
    event = list(harness.log.read())[-1]
    assert event.bridge.action == BridgeAction.FAILED
    assert event.outputs[-1] == failure.id
    assert Harness(root).bridge_state == harness.bridge_state


def test_stage_a_bounded_repair_exhaustion_is_a_typed_terminal_failure(tmp_path):
    root = tmp_path / "stage-a-repair-exhausted"
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-stage-a-repair-exhausted",
            description="What answer is supported?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    invalid = "model output that never satisfies the claim-ledger contract"
    summarizer = MockEndpoint([invalid, invalid, invalid], name="invalid-summarizer")
    thesis = MockEndpoint([], name="unused-thesis")
    adapter = LLMAdapter(
        {"summarizer": summarizer, "thesis": thesis},
        harness.blobs,
        retry_max=2,
    )

    terminal = harness.build_bridge(
        "problem-stage-a-repair-exhausted",
        "answer",
        {"grounding_review": False, "max_grounding_repair_attempts": 0},
        run_manifest_digest="d" * 64,
        stage_a_adapter=adapter,
    )

    assert terminal.process_status == "failure"
    assert terminal.error_code == "BRIDGE_LEDGER_REPAIR_EXHAUSTED"
    assert terminal.claim_ledger_id in harness.bridge_state.ledgers
    assert terminal.validation_report_id in harness.bridge_state.validation_reports
    assert terminal.bridge_output_id is None
    ledger = harness.bridge_state.ledgers[terminal.claim_ledger_id]
    assert [entry.claim_class.value for entry in ledger.entries] == ["unknown"]
    failure = harness.bridge_state.failures[terminal.failure_id]
    assert failure.phase == "stage_a"
    assert failure.claim_ledger_id == terminal.claim_ledger_id
    assert failure.validation_report_id == terminal.validation_report_id
    assert failure.diagnostics[0].code == "BRIDGE_LEDGER_REPAIR_EXHAUSTED"
    events = list(harness.log.read())
    ledger_event = next(
        event
        for event in events
        if event.bridge is not None
        and event.bridge.action == BridgeAction.LEDGER_CREATED
    )
    assert ledger_event.llm.attempts == 3
    assert [attempt.valid for attempt in ledger_event.llm.attempt_trace] == [
        False,
        False,
        False,
    ]
    assert events[-1].bridge.action == BridgeAction.FAILED
    assert len([event for event in events if event.llm is not None]) == 1
    assert thesis.last_transport_attempts == 0
    assert Harness(root).bridge_state == harness.bridge_state


def test_late_failure_preserves_exact_partial_objects_and_replays(tmp_path):
    root = tmp_path / "late-run"
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-late-failure",
            description="What answer is supported?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    adapter = LLMAdapter(
        {
            "summarizer": MockEndpoint(
                [
                    json.dumps(
                        {
                            "entries": [
                                {
                                    "entry_key": "K1",
                                    "claim_class": "unknown",
                                    "claim": "The answer is not established.",
                                }
                            ]
                        }
                    )
                ],
                name="scripted-summarizer",
            ),
            "thesis": MockEndpoint([], name="exhausted-thesis"),
        },
        harness.blobs,
        retry_max=0,
    )

    terminal = harness.build_bridge(
        "problem-late-failure",
        "answer",
        {"grounding_review": False, "max_grounding_repair_attempts": 0},
        run_manifest_digest="b" * 64,
        stage_a_adapter=adapter,
    )

    state = harness.bridge_state
    failure = state.failures[terminal.failure_id]
    assert terminal.process_status == "failure"
    assert terminal.claim_ledger_id in state.ledgers
    assert terminal.bridge_output_id is None
    assert terminal.validation_report_id is None
    assert terminal.review_id is None
    assert list(failure.terminal_inputs) == [terminal.claim_ledger_id]
    terminal_event = list(harness.log.read())[-1]
    assert list(terminal_event.inputs) == list(failure.terminal_inputs)
    assert terminal_event.outputs == [failure.id]
    assert Harness(root).bridge_state == state


def test_bounded_repair_failure_preserves_replayable_diagnostics(tmp_path):
    root = tmp_path / "repair-run"
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-repair-failure",
            description="What answer is supported?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    adapter = LLMAdapter(
        {
            "summarizer": MockEndpoint(
                [
                    json.dumps(
                        {
                            "entries": [
                                {
                                    "entry_key": "K1",
                                    "claim_class": "unknown",
                                    "claim": "The answer is not established.",
                                }
                            ]
                        }
                    )
                ],
                name="scripted-summarizer",
            ),
            "thesis": MockEndpoint(
                [
                    json.dumps(
                        {
                            "sections": [
                                {
                                    "span_id": "S1",
                                    "text": "The answer remains unknown.",
                                    "rendering_mode": "unknown",
                                    "ledger_entry_handles": ["E1"],
                                }
                            ],
                            "resolution": "insufficient_evidence",
                        }
                    )
                ],
                name="scripted-thesis",
            ),
            "judge": MockEndpoint(
                [json.dumps({"finding": "unsupported"})],
                name="exhausted-after-review",
            ),
        },
        harness.blobs,
        retry_max=0,
    )

    terminal = harness.build_bridge(
        "problem-repair-failure",
        "answer",
        {"grounding_review": True, "max_grounding_repair_attempts": 1},
        run_manifest_digest="c" * 64,
        stage_a_adapter=adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
    )

    assert terminal.process_status == "failure"
    assert terminal.error_code == "BRIDGE_GROUNDING_REPAIR_BOUNDED_FAILURE"
    failure = harness.bridge_state.failures[terminal.failure_id]
    assert failure.diagnostics
    assert failure.diagnostics[0].code.startswith("BRIDGE_")
    assert failure.diagnostics[0].span_id == "S1"
    assert terminal.bridge_output_id in harness.bridge_state.outputs
    assert terminal.validation_report_id in harness.bridge_state.validation_reports
    assert terminal.review_id in harness.bridge_state.grounding_reviews
    assert Harness(root).bridge_state == harness.bridge_state
