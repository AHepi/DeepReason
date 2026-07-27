"""Release gates that span the formal, scratch, and grounded-bridge histories."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from deepreason.bridge.state import rebuild_bridge_state
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance, Provenance
from deepreason.scratch.attention import (
    AttentionPlanner,
    AttentionPolicyV1,
    AttentionRequestV1,
)
from deepreason.scratch.authoring import ScratchAuthoringService
from deepreason.scratch.models import (
    AttentionReceiptV1,
    RetrievalChannel,
    ScratchProvenanceV1,
    SimilarityHitV1,
    domain_hash,
)
from deepreason.scratch.render import ScratchRenderer
from deepreason.scratch.service import ScratchService
from deepreason.scratch.state import LinkState, rebuild_scratch_state


_CHANNELS = [
    RetrievalChannel.FOCUS,
    RetrievalChannel.LINK,
    RetrievalChannel.CLUSTER,
    RetrievalChannel.KEYWORD,
    RetrievalChannel.SEMANTIC,
    RetrievalChannel.RECENT,
    RetrievalChannel.LOOSE,
    RetrievalChannel.DORMANT,
    RetrievalChannel.UNDEREXPOSED,
    RetrievalChannel.EXPLORATORY,
    RetrievalChannel.COVERAGE,
]


def _attention_policy() -> AttentionPolicyV1:
    return AttentionPolicyV1(
        max_blocks_per_pack=8,
        max_guides_per_pack=1,
        semantic_retrieval=True,
        keyword_retrieval=True,
        coverage_enabled=False,
        coverage_slot_every_n_packs=1,
        exploratory_fraction=0,
        underexposed_fraction=0,
        dormant_after_events=100,
        similarity_top_k=4,
        similarity_threshold=0.5,
        guide_max_open_threads=8,
        guide_max_entry_points=8,
        channel_priority=_CHANNELS,
        per_channel_limits={channel: 8 for channel in _CHANNELS},
    )


def _object_corpus(root: Path) -> dict[str, bytes]:
    objects = root / "objects"
    return {
        path.relative_to(objects).as_posix(): path.read_bytes()
        for path in sorted(objects.rglob("*"))
        if path.is_file()
    }


def test_integrated_canonical_replay_rebuilds_every_derived_state(tmp_path):
    """One heterogeneous run must be reconstructed solely from log + objects."""

    root = tmp_path / "run"
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-release-replay",
            description="Which surviving idea may explain the bounded record?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    survivor = harness.create_artifact(
        "A feedback mechanism may explain the bounded record.",
        provenance=Provenance(role="conjecturer"),
        problem_id="problem-release-replay",
    )

    service = ScratchService(harness)
    user = ScratchProvenanceV1(actor="user", origin="release-replay-fixture")
    original = service.create_block(
        {"content": "A shared vocabulary may cause convergence."}, user
    )
    left = service.revise_block(
        original.id,
        {"content": "Vocabulary may contribute without being sufficient."},
        user,
    )
    right = service.revise_block(
        original.id,
        {"content": "Vocabulary may instead reveal prior convergence."},
        user,
    )
    retired = service.create_link(
        {
            "from": original.id,
            "to": left.id,
            "relation_hint": "may provide a provisional causal refinement",
        },
        user,
    )
    service.mark_link_used(retired.id, "release-replay:initial-use")
    service.retire_link(retired.id, "The direction remains unsupported.", user)

    cluster = service.create_cluster("Competing causal directions", user)
    service.add_cluster_member(cluster.id, original.id, "starting point", user)
    service.add_cluster_member(cluster.id, right.id, "contrary branch", user)

    planner = AttentionPlanner(service, _attention_policy())
    guide_pack = planner.plan(
        AttentionRequestV1(
            focus_blocks=[original.id],
            focus_clusters=[cluster.id],
            maximum_blocks=3,
            maximum_cluster_guides=0,
            include_nearby=True,
            include_recent=False,
            include_loose=False,
            include_dormant=False,
            include_underexposed=False,
            include_exploratory=False,
            deterministic_seed=7,
        )
    )
    renderer = ScratchRenderer(service)
    rendered = renderer.render_attention_pack(guide_pack)
    planner.commit_render(guide_pack, context_ref="release-replay:guide")
    guide_adapter = LLMAdapter(
        {
            "summarizer": MockEndpoint(
                [
                    json.dumps(
                        {
                            "working_focus": "Keep both causal directions visible.",
                            "entry_points": ["B1"],
                        }
                    )
                ],
                name="scripted-guide",
                model="scripted",
            )
        },
        harness.blobs,
    )
    guide = ScratchAuthoringService(
        service, guide_adapter, renderer=renderer
    ).author_cluster_guide(
        cluster.id,
        rendered,
        task="Write one snapshot-bound navigation guide.",
    )

    first, second = sorted((left, right), key=lambda block: block.id)
    similarity = SimilarityHitV1.create(
        block_a=first.id,
        block_b=second.id,
        embedder="scripted",
        embedder_version="1",
        score=0.91,
        threshold_used=0.5,
        input_body_hash_a=first.body_hash,
        input_body_hash_b=second.body_hash,
        output_ref="fixture:scripted-vector",
        instance=service._instance(),
    )
    service.record_similarity(similarity)

    cycle = service.start_coverage_cycle()
    covered = sorted(service.state.blocks)
    coverage_receipt = AttentionReceiptV1.create(
        state_seq=harness._next_seq - 1,
        request_hash=domain_hash("release.coverage.request.v1", {"all": covered}),
        selected_by_channel={RetrievalChannel.COVERAGE: covered},
        final_order=covered,
        excluded_by_global_limit=[],
        excluded_by_channel={},
        deterministic_seed=11,
        coverage_cycle_id=cycle.id,
        instance=service._instance(),
    )
    service.record_attention_receipt(
        coverage_receipt, context_ref="release-replay:coverage"
    )
    for block_id in covered:
        service.record_coverage_render(cycle.id, block_id, coverage_receipt.id)
    service.complete_coverage_cycle(cycle.id)

    bridge_adapter = LLMAdapter(
        {
            "summarizer": MockEndpoint(
                [
                    json.dumps(
                        {
                            "entries": [
                                {
                                    "entry_key": "K1",
                                    "claim_class": "surviving_conjecture",
                                    "claim": "A feedback mechanism remains a viable explanation.",
                                    "formal_artifact_handles": ["A1"],
                                }
                            ]
                        }
                    )
                ],
                name="scripted-stage-a",
                model="scripted",
            ),
            "thesis": MockEndpoint(
                [
                    json.dumps(
                        {
                            "sections": [
                                {
                                    "span_id": "S1",
                                    "text": "Conjecture: a feedback mechanism may explain the record.",
                                    "rendering_mode": "conjecture",
                                    "ledger_entry_handles": ["E1"],
                                }
                            ],
                            "resolution": "partially_answered",
                            "resolution_reason": (
                                "The formal record retains a conjecture, not a fact."
                            ),
                        }
                    )
                ],
                name="scripted-stage-b",
                model="scripted",
            ),
        },
        harness.blobs,
    )
    terminal = harness.build_bridge(
        "problem-release-replay",
        "answer",
        {"grounding_review": False, "max_grounding_repair_attempts": 0},
        run_manifest_digest="c" * 64,
        stage_a_adapter=bridge_adapter,
    )

    assert survivor.id in harness.state.artifacts
    assert set(service.state.revision_children[original.id]) == {left.id, right.id}
    assert service.state.link_status[retired.id] == LinkState.RETIRED
    assert guide.based_on_snapshot in service.state.snapshots
    assert service.state.guide_state(guide) == "current"
    assert service.state.similarity_hits[similarity.id] == similarity
    assert service.state.attention_receipts[coverage_receipt.id] == coverage_receipt
    progress = service.state.coverage_cycles[cycle.id]
    assert progress.completed and progress.pending_block_ids == []
    assert terminal.claim_ledger_id in harness.bridge_state.ledgers
    assert terminal.bridge_output_id in harness.bridge_state.outputs

    live_formal = harness.state.model_dump(mode="json")
    live_commitments = deepcopy(harness.commitments)
    live_warrants = deepcopy(harness.warrants)
    live_scratch = deepcopy(harness.scratch_state)
    live_bridge = deepcopy(harness.bridge_state)
    corpus_before = _object_corpus(root)
    log_before = (root / "log.jsonl").read_bytes()

    del bridge_adapter, guide_adapter, planner, renderer, service, harness
    reopened = Harness(root)
    events = tuple(reopened.log.read())
    rebuilt_scratch = rebuild_scratch_state(reopened.objects, events)
    rebuilt_bridge = rebuild_bridge_state(reopened.objects, events)

    assert reopened.state.model_dump(mode="json") == live_formal
    assert reopened.commitments == live_commitments
    assert reopened.warrants == live_warrants
    assert reopened.scratch_state == live_scratch == rebuilt_scratch
    assert reopened.bridge_state == live_bridge == rebuilt_bridge
    assert _object_corpus(root) == corpus_before
    assert (root / "log.jsonl").read_bytes() == log_before
