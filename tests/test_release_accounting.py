"""Release Gate D: integrated scratch/bridge LLM accounting."""

from __future__ import annotations

from collections import Counter
import json

from deepreason.bridge.compose import CompositionRequestV1
from deepreason.bridge.events import BridgeAction
from deepreason.bridge.ledger import (
    ClaimLedgerCatalogItemV1,
    ClaimLedgerInputCatalogV1,
)
from deepreason.bridge.workflow import BridgeWorkflow
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.scratch.attention import AttentionPlanner
from deepreason.scratch.authoring import ScratchAuthoringService
from deepreason.scratch.events import ScratchAction
from deepreason.scratch.models import ScratchProvenanceV1
from deepreason.scratch.render import ScratchRenderer
from deepreason.scratch.service import ScratchService
from tests.test_scratch_attention import _policy, _request


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


def _rendered_cluster_context(service: ScratchService, block_id: str):
    planner = AttentionPlanner(service, _policy(coverage_enabled=False))
    pack = planner.plan(_request([block_id], maximum_blocks=1))
    renderer = ScratchRenderer(service)
    rendered = renderer.render_attention_pack(pack)
    planner.commit_render(pack, context_ref="release-accounting")
    return renderer, rendered


def _catalog() -> ClaimLedgerInputCatalogV1:
    return ClaimLedgerInputCatalogV1.create(
        problem_ref="release-accounting-problem",
        formal_seq=0,
        problem_text="What value is recorded by the bounded source?",
        output_target="answer",
        items=[
            ClaimLedgerCatalogItemV1(
                handle="S1",
                kind="source",
                ref="source-1",
                excerpt="The bounded source records a value of seven.",
            )
        ],
    )


def _request_output() -> CompositionRequestV1:
    return CompositionRequestV1(
        output_target="answer",
        formatting_profile="plain",
        desired_length_chars=4_096,
        maximum_sections=8,
    )


def _bridge_object_snapshot(harness: Harness) -> dict[str, bytes]:
    root = harness.objects.root
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.glob("bridge-*/*.json"))
    }


def test_integrated_model_calls_are_counted_once_even_when_objects_deduplicate(
    tmp_path,
):
    harness = Harness(tmp_path / "run")
    service = ScratchService(harness)
    provenance = ScratchProvenanceV1(actor="user", origin="release-accounting")
    block = service.create_block({"content": "cluster member"}, provenance)
    cluster = service.create_cluster("Unresolved local region", provenance)
    service.add_cluster_member(cluster.id, block.id, None, provenance)
    renderer, rendered = _rendered_cluster_context(service, block.id)

    invalid_ledger = json.dumps(
        {
            "entries": [
                {
                    "entry_key": "K1",
                    "claim_class": "source_fact",
                    "claim": "The recorded value is seven.",
                    "source_handles": ["S1"],
                }
            ],
            "invented": "schema-rejected",
        }
    )
    valid_ledger = json.dumps(
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
    composed = json.dumps(
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
    adapter = LLMAdapter(
        {
            "summarizer": MockEndpoint(
                [
                    '{"working_focus":"Still unresolved","entry_points":["B9"]}',
                    '{"working_focus":"Still unresolved"}',
                    invalid_ledger,
                    valid_ledger,
                    invalid_ledger,
                    valid_ledger,
                ],
                name="scripted-summarizer",
            ),
            "thesis": MockEndpoint(
                [composed, composed], name="scripted-thesis"
            ),
            "judge": MockEndpoint(
                [
                    '{"finding":"unsupported","message":"Citation mismatch."}',
                    '{"action":"remove_span"}',
                    '{"finding":"unsupported","message":"Citation mismatch."}',
                    '{"action":"remove_span"}',
                ],
                name="scripted-judge",
            ),
        },
        harness.blobs,
        retry_max=1,
    )

    guide = ScratchAuthoringService(
        service, adapter, renderer=renderer
    ).author_cluster_guide(
        cluster.id,
        rendered,
        task="Create one temporary navigation guide",
    )
    assert guide.working_focus == "Still unresolved"

    def run_bridge():
        return BridgeWorkflow(
            adapter,
            adapter,
            review_adapter=adapter,
            repair_adapter=adapter,
            policy={"max_grounding_repair_attempts": 1},
            sink=_HarnessSink(harness),
        ).run(
            _catalog(),
            _request_output(),
            materials={"source-1": "A different passage with no recorded value."},
        )

    first = run_bridge()
    assert first.successful and first.model_call_count == 4
    first_objects = _bridge_object_snapshot(harness)
    calls_before_repeat = sum(event.llm is not None for event in harness.log.read())

    second = run_bridge()
    assert second.successful and second.model_call_count == 4
    assert first.claim_ledger.id == second.claim_ledger.id
    assert first.bridge_output.id == second.bridge_output.id
    assert first.validation_report.id == second.validation_report.id
    assert first.grounded_review.id == second.grounded_review.id
    assert _bridge_object_snapshot(harness) == first_objects

    events = list(harness.log.read())
    llm_events = [event for event in events if event.llm is not None]
    assert len(llm_events) == calls_before_repeat + 4 == 9

    guide_events = [
        event
        for event in llm_events
        if event.scratch is not None
        and event.scratch.action == ScratchAction.CLUSTER_GUIDE_WRITTEN
    ]
    bridge_call_events = [event for event in llm_events if event.bridge is not None]
    action_counts = Counter(event.bridge.action for event in bridge_call_events)
    assert len(guide_events) == 1
    assert action_counts == {
        BridgeAction.LEDGER_CREATED: 2,
        BridgeAction.OUTPUT_COMPOSED: 2,
        BridgeAction.GROUNDED_REVIEW_ATTEMPTED: 2,
        BridgeAction.REPAIR_ATTEMPTED: 2,
    }

    # The append-only event multiset owns every workflow receipt exactly once,
    # even though the second workflow wrote no new canonical bridge object.
    logged_bridge_calls = Counter(
        event.llm.model_dump_json() for event in bridge_call_events
    )
    returned_bridge_calls = Counter(
        call.model_dump_json()
        for result in (first, second)
        for call in result.model_calls
    )
    assert logged_bridge_calls == returned_bridge_calls
    assert sum(event.llm.tokens for event in llm_events) == (
        guide_events[0].llm.tokens + first.token_count + second.token_count
    )

    repaired_calls = [
        event.llm
        for event in bridge_call_events
        if event.bridge.action == BridgeAction.LEDGER_CREATED
    ]
    assert [attempt.valid for attempt in guide_events[0].llm.attempt_trace] == [
        False,
        True,
    ]
    assert all(
        [attempt.valid for attempt in call.attempt_trace] == [False, True]
        for call in repaired_calls
    )
    assert all(call.attempt_trace[0].diagnostic_ref for call in repaired_calls)
    assert (
        repaired_calls[0].attempt_trace[0].raw_ref
        == repaired_calls[1].attempt_trace[0].raw_ref
    )
    assert all(
        sum(attempt.tokens for attempt in event.llm.attempt_trace)
        == event.llm.tokens
        for event in llm_events
    )

    reopened = Harness(harness.root)
    reopened_calls = [event.llm for event in reopened.log.read() if event.llm]
    assert len(reopened_calls) == 9
    assert sum(call.tokens for call in reopened_calls) == sum(
        event.llm.tokens for event in llm_events
    )
