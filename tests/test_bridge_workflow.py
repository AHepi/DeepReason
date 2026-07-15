"""C8 deterministic two-stage bridge orchestration and accounting."""

from __future__ import annotations

import json

from deepreason.bridge.compose import CompositionRequestV1
from deepreason.bridge.events import BridgeAction
from deepreason.bridge.ledger import (
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV1,
)
from deepreason.bridge.workflow import BridgeWorkflow, BridgeWorkflowPolicy
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance, Provenance


class _HarnessSink:
    def __init__(self, harness: Harness) -> None:
        self.harness = harness

    def persist_bridge_batch(self, batch) -> None:
        self.harness.record_bridge_event(
            batch.action,
            actor=batch.actor,
            inputs=batch.inputs,
            records=batch.records,
            llm=batch.llm,
            finding_ref=batch.finding_ref,
            error_code=batch.error_code,
        )


def _catalog(*items, formal_seq=0):
    return ClaimLedgerInputCatalogV1.create(
        problem_ref="problem-1",
        formal_seq=formal_seq,
        problem_text="What conclusion is justified by this bounded record?",
        output_target="answer",
        items=list(items),
    )


def _source_item():
    return ClaimLedgerCatalogItemV1(
        handle="S1",
        kind="source",
        ref="source-1",
        excerpt="The bounded source records a value of seven.",
    )


def _request():
    return CompositionRequestV1(
        output_target="answer",
        formatting_profile="plain",
        desired_length_chars=4_096,
        maximum_sections=8,
    )


def _adapter(harness, *, summarizer, thesis, judge=None, retry_max=1):
    endpoints = {
        "summarizer": MockEndpoint(summarizer, name="scripted-summarizer"),
        "thesis": MockEndpoint(thesis, name="scripted-thesis"),
    }
    if judge is not None:
        endpoints["judge"] = MockEndpoint(judge, name="scripted-judge")
    return LLMAdapter(endpoints, harness.blobs, retry_max=retry_max)


def _actions(harness):
    return [event.bridge.action for event in harness.log.read()]


def test_unresolved_terminal_is_success_and_every_call_is_counted_once(tmp_path):
    harness = Harness(tmp_path / "run")
    adapter = _adapter(
        harness,
        summarizer=[
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "K1",
                            "claim_class": "unknown",
                            "claim": "The requested conclusion is not established.",
                        }
                    ],
                    "uncovered_requirements": [
                        {
                            "requirement": "A source that establishes the conclusion.",
                            "reason": "The bounded catalog is empty.",
                        }
                    ],
                }
            )
        ],
        thesis=[
            json.dumps(
                {
                    "sections": [
                        {
                            "span_id": "S1",
                            "text": "The requested conclusion remains unknown.",
                            "rendering_mode": "unknown",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    "resolution": "insufficient_evidence",
                    "resolution_reason": "The bounded record supplies no grounding.",
                }
            )
        ],
    )
    formal_before = harness.state.model_dump_json()
    result = BridgeWorkflow(
        adapter,
        adapter,
        policy=BridgeWorkflowPolicy(
            grounding_review=False,
            max_grounding_repair_attempts=0,
        ),
        sink=_HarnessSink(harness),
    ).run(_catalog(), _request())

    assert result.successful
    assert result.bridge_output.resolution.value == "insufficient_evidence"
    assert result.model_call_count == 2
    assert result.token_count == sum(call.tokens for call in result.model_calls)
    assert len([event for event in harness.log.read() if event.llm is not None]) == 2
    assert _actions(harness) == [
        BridgeAction.LEDGER_CREATED,
        BridgeAction.LEDGER_VALIDATED,
        BridgeAction.OUTPUT_COMPOSED,
        BridgeAction.OUTPUT_VALIDATED,
        BridgeAction.COMPLETED,
    ]
    assert harness.state.model_dump_json() == formal_before
    assert Harness(harness.root).bridge_state == harness.bridge_state


def test_stage_b_new_inference_uses_one_explicit_additions_only_amendment(tmp_path):
    harness = Harness(tmp_path / "run")
    adapter = _adapter(
        harness,
        summarizer=[
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "K1",
                            "claim_class": "source_fact",
                            "claim": "The recorded value is seven.",
                            "source_handles": ["S1"],
                        }
                    ]
                }
            ),
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "K2",
                            "claim_class": "supported_inference",
                            "claim": "The answer is therefore seven.",
                            "premise_keys": ["P1"],
                        }
                    ]
                }
            ),
        ],
        thesis=[
            json.dumps(
                {
                    "sections": [],
                    "resolution": "underdetermined",
                    "resolution_reason": "The required inference is not in the ledger.",
                    "ledger_amendment_request": {
                        "requested_class": "supported_inference",
                        "proposed_claim": "The answer is therefore seven.",
                        "reason": "The conclusion must name its recorded premise.",
                    },
                }
            ),
            json.dumps(
                {
                    "sections": [
                        {
                            "span_id": "S1",
                            "text": "From the record, the answer is seven.",
                            "rendering_mode": "inference",
                            "ledger_entry_handles": ["E2"],
                        }
                    ],
                    "resolution": "answered",
                }
            ),
        ],
    )
    result = BridgeWorkflow(
        adapter,
        adapter,
        policy={
            "grounding_review": False,
            "max_grounding_repair_attempts": 0,
        },
        sink=_HarnessSink(harness),
    ).run(_catalog(_source_item()), _request())

    assert result.successful and result.amendment_count == 1
    assert result.model_call_count == 4
    assert len(result.claim_ledger.entries) == 2
    inference = result.claim_ledger.entries[-1]
    assert inference.premise_refs == [result.claim_ledger.entries[0].id]
    assert _actions(harness).count(BridgeAction.LEDGER_AMENDMENT_REQUESTED) == 1
    assert _actions(harness).count(BridgeAction.LEDGER_AMENDED) == 1
    assert len([event for event in harness.log.read() if event.llm is not None]) == 4


def test_failed_fact_review_is_removed_and_returns_safe_unresolved_success(tmp_path):
    harness = Harness(tmp_path / "run")
    adapter = _adapter(
        harness,
        summarizer=[
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "K1",
                            "claim_class": "source_fact",
                            "claim": "The recorded value is seven.",
                            "source_handles": ["S1"],
                        }
                    ]
                }
            )
        ],
        thesis=[
            json.dumps(
                {
                    "sections": [
                        {
                            "span_id": "S1",
                            "text": "The value is seven.",
                            "rendering_mode": "fact",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    "resolution": "answered",
                }
            )
        ],
        judge=[
            json.dumps({"finding": "unsupported", "message": "Citation mismatch."}),
            json.dumps({"action": "remove_span"}),
        ],
    )
    result = BridgeWorkflow(
        adapter,
        adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
        policy={"max_grounding_repair_attempts": 2},
        sink=_HarnessSink(harness),
    ).run(
        _catalog(_source_item()),
        _request(),
        materials={"source-1": "A different source passage with no value."},
    )

    assert result.successful
    assert result.bridge_output.sections == []
    assert result.bridge_output.resolution.value == "insufficient_evidence"
    assert result.grounded_review is not None and not result.grounded_review.passed
    assert result.model_call_count == 4
    assert _actions(harness).count(BridgeAction.GROUNDED_REVIEW_ATTEMPTED) == 1
    assert _actions(harness).count(BridgeAction.REPAIR_ATTEMPTED) == 2
    assert _actions(harness)[-1] == BridgeAction.COMPLETED


def test_corrected_wording_must_pass_a_second_grounded_review(tmp_path):
    harness = Harness(tmp_path / "run")
    adapter = _adapter(
        harness,
        summarizer=[
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "K1",
                            "claim_class": "source_fact",
                            "claim": "The source says approximately seven.",
                            "source_handles": ["S1"],
                        }
                    ]
                }
            )
        ],
        thesis=[
            json.dumps(
                {
                    "sections": [
                        {
                            "span_id": "S1",
                            "text": "The exact value is seven.",
                            "rendering_mode": "fact",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    "resolution": "answered",
                }
            )
        ],
        judge=[
            json.dumps({"finding": "overstated", "message": "Too exact."}),
            json.dumps(
                {
                    "action": "correct_wording",
                    "replacement_text": "The source says approximately seven.",
                }
            ),
            json.dumps({"finding": "supported"}),
        ],
    )
    result = BridgeWorkflow(
        adapter,
        adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
        policy={"max_grounding_repair_attempts": 2},
        sink=_HarnessSink(harness),
    ).run(
        _catalog(_source_item()),
        _request(),
        materials={"source-1": "The source says approximately seven."},
    )

    assert result.successful
    assert result.bridge_output.sections[0].text == "The source says approximately seven."
    assert result.grounded_review is not None and result.grounded_review.passed
    assert _actions(harness).count(BridgeAction.GROUNDED_REVIEW_ATTEMPTED) == 2
    assert _actions(harness).count(BridgeAction.GROUNDED_REVIEWED) == 2
    assert result.model_call_count == 5


def test_harness_build_bridge_uses_fixed_fence_and_writes_typed_terminal(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_problem(
        Problem(
            id="problem-bridge",
            description="Which surviving idea should be presented?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    survivor = harness.create_artifact(
        "A genuinely novel surviving conjecture.",
        provenance=Provenance(role="conjecturer"),
        problem_id="problem-bridge",
    )
    fence = harness._next_seq - 1
    formal_before = harness.state.model_dump_json()
    adapter = _adapter(
        harness,
        summarizer=[
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "K1",
                            "claim_class": "surviving_conjecture",
                            "claim": "A novel conjecture survives the formal record.",
                            "formal_artifact_handles": ["A1"],
                        }
                    ]
                }
            )
        ],
        thesis=[
            json.dumps(
                {
                    "sections": [
                        {
                            "span_id": "S1",
                            "text": "Conjecture: the surviving idea may explain the result.",
                            "rendering_mode": "conjecture",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    "resolution": "partially_answered",
                    "resolution_reason": "The record supports a conjecture, not a fact.",
                }
            )
        ],
    )

    terminal = harness.build_bridge(
        "problem-bridge",
        "answer",
        {
            "grounding_review": False,
            "max_grounding_repair_attempts": 0,
        },
        run_manifest_digest="a" * 64,
        stage_a_adapter=adapter,
    )

    assert terminal.process_status == "success"
    assert terminal.formal_seq == fence
    assert terminal.resolution.value == "partially_answered"
    assert terminal.terminal_event_seq > fence
    assert terminal.evidence_pack_id in harness.bridge_state.evidence_packs
    pack = harness.bridge_state.evidence_packs[terminal.evidence_pack_id]
    assert pack.formal_seq == fence
    assert [item.artifact_ref for item in pack.survivors] == [survivor.id]
    assert harness.state.model_dump_json() == formal_before
    assert json.loads((harness.root / "bridge-result.json").read_text()) == terminal.model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    status = json.loads((harness.root / "bridge-status.json").read_text())
    assert status["process_status"] == "success"
    assert status["resolution"] == "partially_answered"
    reopened = Harness(harness.root)
    assert reopened.bridge_state == harness.bridge_state


def test_harness_composer_cannot_launder_conjecture_into_fact(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_problem(
        Problem(
            id="problem-laundering",
            description="What can the surviving idea establish?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    harness.create_artifact(
        "A surviving idea, not an established fact.",
        provenance=Provenance(role="conjecturer"),
        problem_id="problem-laundering",
    )
    adapter = _adapter(
        harness,
        summarizer=[
            json.dumps(
                {
                    "entries": [
                        {
                            "entry_key": "K1",
                            "claim_class": "surviving_conjecture",
                            "claim": "The idea remains conjectural.",
                            "formal_artifact_handles": ["A1"],
                        }
                    ]
                }
            )
        ],
        thesis=[
            json.dumps(
                {
                    "sections": [
                        {
                            "span_id": "S1",
                            "text": "The idea is established fact.",
                            "rendering_mode": "fact",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    "resolution": "answered",
                }
            ),
            json.dumps(
                {
                    "sections": [
                        {
                            "span_id": "S1",
                            "text": "The idea remains a conjecture.",
                            "rendering_mode": "conjecture",
                            "ledger_entry_handles": ["E1"],
                        }
                    ],
                    "resolution": "partially_answered",
                    "resolution_reason": "No factual grounding is present.",
                }
            ),
        ],
    )

    terminal = harness.build_bridge(
        "problem-laundering",
        "answer",
        {
            "grounding_review": False,
            "max_grounding_repair_attempts": 0,
        },
        run_manifest_digest="b" * 64,
        stage_a_adapter=adapter,
    )
    output = harness.bridge_state.outputs[terminal.bridge_output_id]

    assert terminal.process_status == "success"
    assert all(section.rendering_mode.value != "fact" for section in output.sections)
    compose_event = next(
        event
        for event in harness.log.read()
        if event.bridge is not None
        and event.bridge.action == BridgeAction.OUTPUT_COMPOSED
    )
    assert compose_event.llm.attempts == 2
    assert not compose_event.llm.attempt_trace[0].valid
