"""C8 deterministic two-stage bridge orchestration and accounting."""

from __future__ import annotations

import json

import pytest

import deepreason.bridge.harness as bridge_harness
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
from deepreason.scratch.attention import (
    AttentionPlanner,
    AttentionPolicyV1,
    AttentionRequestV1,
)
from deepreason.scratch.models import RetrievalChannel, ScratchProvenanceV1
from deepreason.scratch.service import ScratchService


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


def test_exhausted_ledger_amendment_is_terminal_and_retains_prior_ledger(tmp_path):
    harness = Harness(tmp_path / "run")
    initial = json.dumps(
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
    invalid = "not a valid additions-only claim-ledger amendment"
    adapter = _adapter(
        harness,
        summarizer=[initial, invalid, invalid, invalid],
        thesis=[
            json.dumps(
                {
                    "sections": [],
                    "resolution": "underdetermined",
                    "resolution_reason": "An inference would require amendment.",
                    "ledger_amendment_request": {
                        "requested_class": "supported_inference",
                        "proposed_claim": "The answer is therefore seven.",
                        "reason": "The conclusion must name its premise.",
                    },
                }
            )
        ],
        retry_max=2,
    )

    result = BridgeWorkflow(
        adapter,
        adapter,
        policy={"grounding_review": False, "max_grounding_repair_attempts": 0},
        sink=_HarnessSink(harness),
    ).run(_catalog(_source_item()), _request())

    assert result.process_status == "failure"
    assert result.phase == "ledger_amendment"
    assert result.error_code == "BRIDGE_LEDGER_REPAIR_EXHAUSTED"
    assert result.amendment_count == 1
    assert result.bridge_output is None
    assert result.claim_ledger is not None
    assert len(result.claim_ledger.entries) == 1
    assert result.validation_report is not None and result.validation_report.valid
    assert result.model_call_count == 3
    actions = _actions(harness)
    assert actions[-2:] == [
        BridgeAction.LEDGER_AMENDMENT_ATTEMPTED,
        BridgeAction.FAILED,
    ]
    amendment_event = list(harness.log.read())[-2]
    failed_event = list(harness.log.read())[-1]
    assert amendment_event.llm is None
    assert failed_event.llm.attempts == 3
    assert not any(attempt.valid for attempt in failed_event.llm.attempt_trace)
    assert BridgeAction.OUTPUT_COMPOSED not in actions
    assert Harness(harness.root).bridge_state == harness.bridge_state


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


def test_grounding_repair_exception_writes_typed_failed_event(tmp_path, monkeypatch):
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
        judge=[json.dumps({"finding": "unsupported"})],
        retry_max=0,
    )
    monkeypatch.setattr(
        "deepreason.bridge.workflow.GroundingRepairService.repair",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("injected repair failure")
        ),
    )

    result = BridgeWorkflow(
        adapter,
        adapter,
        review_adapter=adapter,
        repair_adapter=adapter,
        policy={"max_grounding_repair_attempts": 1},
        sink=_HarnessSink(harness),
    ).run(
        _catalog(_source_item()),
        _request(),
        materials={"source-1": "A different passage."},
    )

    assert result.process_status == "failure"
    assert result.error_code == "BRIDGE_GROUNDING_REPAIR_FAILED"
    assert _actions(harness)[-1] == BridgeAction.FAILED
    terminal_event = list(harness.log.read())[-1]
    assert terminal_event.bridge.error_code == "BRIDGE_GROUNDING_REPAIR_FAILED"
    assert set(terminal_event.inputs) == {
        result.claim_ledger.id,
        result.bridge_output.id,
        result.validation_report.id,
        result.grounded_review.id,
    }


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


def test_post_plan_pre_call_failure_does_not_commit_attention_state(
    tmp_path, monkeypatch
):
    """Deterministic bridge preparation must finish before render is recorded."""

    harness = Harness(tmp_path / "run")
    harness.register_problem(
        Problem(
            id="problem-attention-failure",
            description="Can the bounded scratch context help?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    service = ScratchService(harness)
    block = service.create_block(
        {"content": "A provisional scratch thought."},
        ScratchProvenanceV1(actor="user", origin="bridge-attention-test"),
    )
    cycle = service.start_coverage_cycle()
    channels = [
        channel
        for channel in RetrievalChannel
        if channel != RetrievalChannel.DIRECT_OPEN
    ]
    planner = AttentionPlanner(
        service,
        AttentionPolicyV1(
            max_blocks_per_pack=1,
            max_guides_per_pack=0,
            semantic_retrieval=False,
            keyword_retrieval=False,
            coverage_enabled=True,
            coverage_slot_every_n_packs=1,
            exploratory_fraction=0,
            underexposed_fraction=0,
            dormant_after_events=100,
            similarity_top_k=1,
            guide_max_open_threads=0,
            guide_max_entry_points=0,
            channel_priority=channels,
            per_channel_limits={channel: 1 for channel in channels},
        ),
    )
    pack = planner.plan(
        AttentionRequestV1(
            focus_blocks=[block.id],
            maximum_blocks=1,
            maximum_cluster_guides=0,
            include_nearby=False,
            include_recent=False,
            include_loose=False,
            include_dormant=False,
            include_underexposed=False,
            include_exploratory=False,
            deterministic_seed=7,
        )
    )
    endpoint = MockEndpoint(["must not be consumed"], name="unused-summarizer")
    adapter = LLMAdapter(
        {
            "summarizer": endpoint,
            "thesis": MockEndpoint([], name="unused-thesis"),
        },
        harness.blobs,
        retry_max=0,
    )
    before_seq = harness._next_seq
    before_pending = list(
        harness.scratch_state.coverage_cycles[cycle.id].pending_block_ids
    )

    def fail_catalog(*_args, **_kwargs):
        raise RuntimeError("injected deterministic catalog failure")

    monkeypatch.setattr(bridge_harness, "build_claim_ledger_catalog", fail_catalog)
    with pytest.raises(RuntimeError, match="injected deterministic catalog failure"):
        harness.build_bridge(
            "problem-attention-failure",
            "answer",
            {"grounding_review": False, "max_grounding_repair_attempts": 0},
            run_manifest_digest="c" * 64,
            stage_a_adapter=adapter,
            attention_pack=pack,
        )

    assert harness._next_seq == before_seq
    assert harness.scratch_state.attention_receipts == {}
    assert harness.scratch_state.advisory_contexts == {}
    assert harness.scratch_state.visibility == {}
    progress = harness.scratch_state.coverage_cycles[cycle.id]
    assert progress.pending_block_ids == before_pending
    assert progress.rendered_block_ids == []
    assert not progress.completed
    assert endpoint.last_transport_attempts == 0
