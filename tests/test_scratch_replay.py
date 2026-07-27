"""C2 append-only scratch replay and formal-isolation tests."""

from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from deepreason.bridge.events import BridgeEventPayloadV1
from deepreason.harness import Harness, WellFormednessError
from deepreason.invariants import verify_root
from deepreason.ontology import Commitment, LLMCall, Provenance, Rule, StateDiff
from deepreason.ontology.event import Event
from deepreason.scratch.events import ScratchAction, ScratchEventPayloadV1
from deepreason.scratch.models import (
    AttentionReceiptV1,
    ClusterGuideV1,
    ClusterMembershipV1,
    ClusterSnapshotV1,
    CoverageCycleV1,
    InstanceRef,
    LLMCallRef,
    ScratchBlockBodyV1,
    ScratchBlockV1,
    ScratchClusterV1,
    ScratchLinkBodyV1,
    ScratchLinkV1,
    ScratchProvenanceV1,
    SimilarityHitV1,
    domain_hash,
)
from deepreason.scratch.state import LinkState


RUN_ID = domain_hash("test.run.v1", {"name": "scratch-replay"})


def _instance(harness: Harness) -> InstanceRef:
    return InstanceRef(run_id=RUN_ID, seq=harness._next_seq)


def _payload(
    action: ScratchAction | str,
    *,
    actor: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    reason_ref: str | None = None,
    retrieval_receipt_ref: str | None = None,
    context_ref: str | None = None,
) -> ScratchEventPayloadV1:
    return ScratchEventPayloadV1(
        action=action,
        actor=actor,
        inputs=inputs or [],
        outputs=outputs or [],
        reason_ref=reason_ref,
        retrieval_receipt_ref=retrieval_receipt_ref,
        context_ref=context_ref,
    )


def _create_block(
    harness: Harness,
    content: str,
    *,
    revision_of: str | None = None,
    llm: LLMCall | None = None,
) -> ScratchBlockV1:
    block = ScratchBlockV1.create(
        ScratchBlockBodyV1(content=content),
        _instance(harness),
        ScratchProvenanceV1(actor="llm" if llm else "user", origin="fixture"),
        revision_of=revision_of,
    )
    harness.objects.put("scratch-block", block)
    harness.record_scratch_event(
        _payload(
            "block_revised" if revision_of else "block_created",
            actor="llm" if llm else "user",
            inputs=[revision_of] if revision_of else [],
            outputs=[block.id],
        ),
        llm=llm,
    )
    return block


def _create_link(
    harness: Harness,
    from_id: str,
    to_id: str,
    *,
    relation: str = "may be relevant to",
    supersedes: str | None = None,
) -> ScratchLinkV1:
    link = ScratchLinkV1.create(
        ScratchLinkBodyV1(
            from_=from_id,
            to=to_id,
            relation_hint=relation,
            supersedes=supersedes,
        ),
        _instance(harness),
    )
    harness.objects.put("scratch-link", link)
    harness.record_scratch_event(
        _payload("link_created", actor="user", outputs=[link.id])
    )
    return link


def _create_cluster(harness: Harness, focus: str = "Unfinished region") -> ScratchClusterV1:
    cluster = ScratchClusterV1.create(focus, _instance(harness))
    harness.objects.put("scratch-cluster", cluster)
    harness.record_scratch_event(
        _payload("cluster_created", actor="user", outputs=[cluster.id])
    )
    return cluster


def _membership(
    harness: Harness, cluster_id: str, block_id: str, action: str
) -> ClusterMembershipV1:
    record = ClusterMembershipV1.create(
        cluster_id, block_id, action, _instance(harness), reason=f"fixture {action}"
    )
    harness.objects.put("scratch-membership", record)
    harness.record_scratch_event(
        _payload(
            f"cluster_member_{'added' if action == 'add' else 'removed'}",
            actor="user",
            inputs=[cluster_id, block_id],
            outputs=[record.id],
        )
    )
    return record


def _formal_dump(harness: Harness) -> dict:
    return deepcopy(harness.state.model_dump(mode="json"))


def test_scratch_events_replay_at_every_fence_and_leave_formal_state_unchanged(tmp_path):
    root = tmp_path / "run"
    harness = Harness(root)
    harness.create_artifact("formal claim", provenance=Provenance(role="seed"))
    formal_before = _formal_dump(harness)

    original = _create_block(harness, "A shared vocabulary may cause convergence.")
    left = _create_block(
        harness,
        "Vocabulary may contribute without being sufficient.",
        revision_of=original.id,
    )
    right = _create_block(
        harness,
        "Vocabulary may instead reveal a prior convergence.",
        revision_of=original.id,
    )

    assert harness.scratch_state.revision_children[original.id] == [left.id, right.id]
    assert _formal_dump(harness) == formal_before
    assert Harness(root).scratch_state == harness.scratch_state

    events = list(harness.log.read())
    for event in events:
        historical = Harness.at(root, event.seq)
        expected = {
            block.id
            for block in (original, left, right)
            if block.instance.seq <= event.seq
        }
        assert set(historical.scratch_state.blocks) == expected
        assert _formal_dump(historical) == formal_before


def test_link_use_supersession_retirement_and_history_replay(tmp_path):
    harness = Harness(tmp_path / "run")
    first = _create_block(harness, "first")
    second = _create_block(harness, "second")
    old = _create_link(harness, first.id, second.id)
    harness.record_scratch_event(
        _payload("link_used", actor="harness", inputs=[old.id], context_ref="ctx:fixture")
    )
    assert harness.scratch_state.link_status[old.id] == LinkState.ACTIVE

    clarified = _create_link(
        harness,
        first.id,
        second.id,
        relation="may share an assumption with",
        supersedes=old.id,
    )
    supersession_seq = harness._next_seq - 1
    assert harness.scratch_state.link_status[old.id] == LinkState.SUPERSEDED

    reason_ref = harness.blobs.put(b"The clarification was itself misleading.")
    harness.record_scratch_event(
        _payload(
            "link_retired",
            actor="user",
            inputs=[clarified.id],
            reason_ref=reason_ref,
        )
    )
    assert harness.scratch_state.link_status[clarified.id] == LinkState.RETIRED
    assert harness.scratch_state.link_status[old.id] == LinkState.ACTIVE
    assert Harness.at(harness.root, supersession_seq).scratch_state.link_status[old.id] == (
        LinkState.SUPERSEDED
    )
    assert clarified.id in Harness(harness.root).scratch_state.links


def test_cluster_membership_guide_staleness_similarity_visibility_and_coverage(tmp_path):
    harness = Harness(tmp_path / "run")
    first = _create_block(harness, "semantically central")
    neglected = _create_block(harness, "distant and neglected")
    link = _create_link(harness, first.id, neglected.id)
    cluster = _create_cluster(harness)
    _membership(harness, cluster.id, first.id, "add")

    snapshot = ClusterSnapshotV1.create(cluster.id, [first.id], [link.id])
    harness.objects.put("scratch-cluster-snapshot", snapshot)
    call_ref = LLMCallRef(
        event_seq=harness._next_seq,
        model="scripted",
        endpoint="fixture://offline",
        prompt_ref="prompt-ref",
        raw_ref="raw-ref",
    )
    guide = ClusterGuideV1.create(
        cluster_id=cluster.id,
        based_on_snapshot=snapshot.snapshot_hash,
        working_focus="Keep both causal directions open.",
        authored_by=call_ref,
        instance=_instance(harness),
        entry_points=[first.id],
    )
    harness.objects.put("scratch-guide", guide)
    harness.record_scratch_event(
        _payload(
            "cluster_guide_written",
            actor="llm",
            inputs=[cluster.id],
            outputs=[snapshot.snapshot_hash, guide.id],
        )
    )
    assert harness.scratch_state.guide_state(guide) == "current"
    assert harness.scratch_state.guides_by_snapshot[
        (cluster.id, snapshot.snapshot_hash)
    ] == [guide.id]

    _membership(harness, cluster.id, neglected.id, "add")
    assert harness.scratch_state.guide_state(guide) == "stale"
    _membership(harness, cluster.id, first.id, "remove")
    assert first.id not in harness.scratch_state.current_memberships[cluster.id]
    assert neglected.id in harness.scratch_state.current_memberships[cluster.id]

    similarity = SimilarityHitV1.create(
        block_a=first.id,
        block_b=neglected.id,
        embedder="deterministic-fallback",
        embedder_version="1",
        score=0.92,
        threshold_used=0.8,
        input_body_hash_a=first.body_hash,
        input_body_hash_b=neglected.body_hash,
        instance=_instance(harness),
    )
    harness.objects.put("scratch-similarity", similarity)
    harness.record_scratch_event(
        _payload("similarity_recorded", actor="harness", outputs=[similarity.id])
    )
    assert set(harness.scratch_state.blocks) == {first.id, neglected.id}
    assert harness.scratch_state.similarity_by_pair[
        (first.id, neglected.id, "deterministic-fallback", "1")
    ] == [similarity.id]

    coverage = CoverageCycleV1.create([first.id, neglected.id], _instance(harness))
    harness.objects.put("scratch-coverage-cycle", coverage)
    harness.record_scratch_event(
        _payload("coverage_cycle_started", actor="harness", outputs=[coverage.cycle_id])
    )
    receipt = AttentionReceiptV1.create(
        state_seq=harness._next_seq - 1,
        request_hash=domain_hash("scratch.attention.request.v1", {"coverage": True}),
        selected_by_channel={"coverage": [neglected.id]},
        final_order=[neglected.id],
        excluded_by_global_limit=[],
        excluded_by_channel={},
        deterministic_seed=17,
        coverage_cycle_id=coverage.cycle_id,
        instance=_instance(harness),
    )
    harness.objects.put("scratch-attention-receipt", receipt)
    harness.record_scratch_event(
        _payload(
            "attention_pack_rendered",
            actor="harness",
            outputs=[receipt.receipt_hash],
            retrieval_receipt_ref=receipt.receipt_hash,
        )
    )
    assert harness.scratch_state.visibility[neglected.id].render_count == 1
    assert [channel.value for channel in harness.scratch_state.visibility[
        neglected.id
    ].retrieval_channels_used] == ["coverage"]

    harness.record_scratch_event(
        _payload(
            "coverage_block_rendered",
            actor="harness",
            inputs=[coverage.cycle_id, neglected.id],
            retrieval_receipt_ref=receipt.receipt_hash,
        )
    )
    second_receipt = AttentionReceiptV1.create(
        state_seq=harness._next_seq - 1,
        request_hash=domain_hash("scratch.attention.request.v1", {"coverage": "second"}),
        selected_by_channel={"coverage": [first.id]},
        final_order=[first.id],
        excluded_by_global_limit=[],
        excluded_by_channel={},
        deterministic_seed=18,
        coverage_cycle_id=coverage.cycle_id,
        instance=_instance(harness),
    )
    harness.objects.put("scratch-attention-receipt", second_receipt)
    harness.record_scratch_event(
        _payload(
            "attention_pack_rendered",
            actor="harness",
            outputs=[second_receipt.receipt_hash],
            retrieval_receipt_ref=second_receipt.receipt_hash,
        )
    )
    harness.record_scratch_event(
        _payload(
            "coverage_block_rendered",
            actor="harness",
            inputs=[coverage.cycle_id, first.id],
            retrieval_receipt_ref=second_receipt.receipt_hash,
        )
    )
    harness.record_scratch_event(
        _payload(
            "coverage_cycle_completed", actor="harness", inputs=[coverage.cycle_id]
        )
    )
    progress = harness.scratch_state.coverage_cycles[coverage.cycle_id]
    assert progress.completed and not progress.pending_block_ids
    assert Harness(harness.root).scratch_state == harness.scratch_state


def test_scratch_llm_call_is_logged_and_accounted_exactly_once(tmp_path):
    harness = Harness(tmp_path / "run")
    prompt_ref = harness.blobs.put(b"one bounded scratch task")
    raw_ref = harness.blobs.put(b'{"content":"uncertain"}')
    call = LLMCall(
        role="conjecturer",
        model="scripted",
        endpoint="fixture://offline",
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=7,
        attempts=1,
    )
    _create_block(harness, "uncertain", llm=call)

    events = list(harness.log.read())
    assert sum(event.llm.tokens for event in events if event.llm is not None) == 7
    report = verify_root(harness.root, meter_total=7)
    assert report["violations"] == []
    assert report["stats"]["logged_tokens"] == 7
    assert report["stats"]["scratch_events"] == 1


def test_typed_event_contract_rejects_raw_actions_and_formal_graph_injection():
    block_id = domain_hash("fixture", {"block": 1})
    with pytest.raises(ValidationError):
        ScratchEventPayloadV1(action="invented_action", actor="user")
    with pytest.raises(ValidationError, match="cannot author interpretive"):
        ScratchEventPayloadV1(
            action="block_created", actor="harness", outputs=[block_id]
        )
    payload = ScratchEventPayloadV1(
        action="block_created", actor="user", outputs=[block_id]
    )
    with pytest.raises(ValidationError, match="formal StateDiff"):
        Event(
            seq=0,
            ts="ignored-for-ordering",
            rule=Rule.SCRATCH,
            outputs=[block_id],
            scratch=payload,
            state_diff=StateDiff(a_add=[block_id]),
        )
    with pytest.raises(ValidationError, match="outputs must match"):
        Event(
            seq=0,
            ts="ignored-for-ordering",
            rule=Rule.SCRATCH,
            outputs=[],
            scratch=payload,
        )


def test_legacy_formal_event_json_shape_does_not_gain_null_process_payloads():
    event = Event(seq=0, ts="legacy", rule=Rule.MEASURE)
    encoded = event.model_dump_json(by_alias=True)

    assert '"scratch"' not in encoded
    assert '"bridge"' not in encoded


def test_bridge_process_event_cannot_register_a_formal_object(tmp_path):
    harness = Harness(tmp_path / "run")
    formal_id = domain_hash("fixture.formal", {})
    harness.objects.put("commitment", Commitment(id=formal_id, eval="predicate:True"))
    payload = BridgeEventPayloadV1(
        action="ledger_created", actor="harness", outputs=[formal_id]
    )

    with pytest.raises(WellFormednessError, match="non-bridge schema"):
        harness._commit(
            Rule.BRIDGE,
            inputs=[],
            outputs=[formal_id],
            bridge=payload,
        )

    assert formal_id not in harness.commitments
    assert list(harness.log.read()) == []
