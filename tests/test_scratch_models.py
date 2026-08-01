"""Canonical identity and immutability checks for scratchpad records."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from deepreason.canonical import canonical_json
from deepreason.scratch.models import (
    AdvisoryContextV1,
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
    VisibilityRecordV1,
    RetrievalChannel,
    domain_hash,
)


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


RUN_ID = _hash("a")


def _instance(seq: int) -> InstanceRef:
    return InstanceRef(run_id=RUN_ID, seq=seq)


def _provenance() -> ScratchProvenanceV1:
    return ScratchProvenanceV1(actor="user", origin="author")


def _block(content: str, seq: int, *, revision_of: str | None = None) -> ScratchBlockV1:
    return ScratchBlockV1.create(
        body=ScratchBlockBodyV1(content=content),
        instance=_instance(seq),
        provenance=_provenance(),
        revision_of=revision_of,
    )


def _call(seq: int = 20) -> LLMCallRef:
    return LLMCallRef(
        event_seq=seq,
        model="scripted-model",
        endpoint="scripted://offline",
        prompt_ref=_hash("b"),
        raw_ref=_hash("c"),
    )


def test_minimal_block_omits_optional_body_fields_from_canonical_form():
    body = ScratchBlockBodyV1(content="Maybe compression, rather than agreement, converges.")

    assert body.model_dump(mode="json", exclude_none=True) == {
        "content": "Maybe compression, rather than agreement, converges."
    }
    assert canonical_json(body.model_dump(mode="json", exclude_none=True)) == (
        b'{"content":"Maybe compression, rather than agreement, converges."}'
    )


@pytest.mark.parametrize(
    "field",
    ["content", "why_keep_this", "unfinished", "possible_next_move"],
)
def test_empty_block_text_is_rejected_consistently(field: str):
    values = {"content": "kept", field: "   "}
    with pytest.raises(ValidationError):
        ScratchBlockBodyV1(**values)


def test_duplicate_bodies_share_body_hash_but_instances_remain_distinct():
    first = _block("same thought", 1)
    second = _block("same thought", 2)

    assert first.body_hash == second.body_hash
    assert first.id != second.id


def test_provenance_participates_in_block_instance_identity():
    body = ScratchBlockBodyV1(content="same thought")
    first = ScratchBlockV1.create(body=body, instance=_instance(1), provenance=_provenance())
    second = ScratchBlockV1.create(
        body=body,
        instance=_instance(1),
        provenance=ScratchProvenanceV1(actor="llm", origin="conjecturer"),
    )

    assert first.id != second.id


def test_caller_supplied_block_ids_and_body_hashes_are_verified():
    valid = _block("identity is checked", 1)
    record = valid.model_dump(mode="json", by_alias=True)

    with pytest.raises(ValidationError, match="body_hash"):
        ScratchBlockV1.model_validate({**record, "body_hash": _hash("d")})
    with pytest.raises(ValidationError, match="canonical scratch block identity"):
        ScratchBlockV1.model_validate({**record, "id": _hash("e")})


def test_domain_separation_prevents_cross_type_identity_collisions():
    payload = {"same": "payload"}
    domains = [
        "scratch.block.body.v1",
        "scratch.block.instance.v1",
        "scratch.link.instance.v1",
        "scratch.cluster.instance.v1",
        "scratch.cluster.membership.v1",
        "scratch.cluster.snapshot.v1",
        "scratch.cluster.guide.v1",
        "scratch.similarity.v1",
        "scratch.attention.receipt.v1",
        "scratch.coverage.cycle.v1",
        "scratch.advisory.context.v1",
    ]

    identities = {domain_hash(domain, payload) for domain in domains}
    assert len(identities) == len(domains)
    assert all(identity.startswith("sha256:") and len(identity) == 71 for identity in identities)


def test_revisions_are_immutable_and_may_branch():
    original = _block("Vocabulary causes convergence.", 1)
    left = _block("Vocabulary may contribute to convergence.", 2, revision_of=original.id)
    right = _block("Vocabulary may instead reveal convergence.", 3, revision_of=original.id)

    assert left.revision_of == right.revision_of == original.id
    assert left.id != right.id
    assert original.revision_of is None
    with pytest.raises(ValidationError):
        original.body.content = "edited"


def test_directed_and_symmetric_links_preserve_open_inert_relation_text():
    first = _block("first", 1)
    second = _block("second", 2)
    directed_body = ScratchLinkBodyV1(
        from_=first.id,
        to=second.id,
        relation_hint="might share a hidden compression attractor with",
        because="This is merely a provisional interpretation.",
        holds_when="The vocabulary shift predates convergence.",
        weakens_when="The ideas converged before the vocabulary shifted.",
        direction="directed",
    )
    symmetric_body = ScratchLinkBodyV1(
        from_=first.id,
        to=second.id,
        relation_hint="rhymes unexpectedly with",
        direction="symmetric",
    )
    directed = ScratchLinkV1.create(body=directed_body, instance=_instance(3))
    symmetric = ScratchLinkV1.create(body=symmetric_body, instance=_instance(4))

    assert directed.body.direction == "directed"
    assert symmetric.body.direction == "symmetric"
    assert directed.body.holds_when == "The vocabulary shift predates convergence."
    assert directed.body.weakens_when == "The ideas converged before the vocabulary shifted."
    assert directed.id != symmetric.id


def test_link_supersession_is_provisional_data_not_mutation():
    first = _block("first", 1)
    second = _block("second", 2)
    old = ScratchLinkV1.create(
        body=ScratchLinkBodyV1(from_=first.id, to=second.id, relation_hint="may relate"),
        instance=_instance(3),
    )
    new = ScratchLinkV1.create(
        body=ScratchLinkBodyV1(
            from_=first.id,
            to=second.id,
            relation_hint="may share an assumption",
            supersedes=old.id,
        ),
        instance=_instance(4),
    )

    assert new.body.supersedes == old.id
    assert old.body.supersedes is None


def test_cluster_identity_is_independent_of_membership():
    cluster = ScratchClusterV1.create(seed_focus="Representation collapse", instance=_instance(5))
    first = _block("first", 1)
    second = _block("second", 2)
    add_first = ClusterMembershipV1.create(
        cluster_id=cluster.id,
        block_id=first.id,
        action="add",
        reason="possible mechanism",
        instance=_instance(6),
    )
    add_second = ClusterMembershipV1.create(
        cluster_id=cluster.id,
        block_id=second.id,
        action="add",
        instance=_instance(7),
    )

    assert add_first.cluster_id == add_second.cluster_id == cluster.id
    assert add_first.id != add_second.id
    assert cluster.id == ScratchClusterV1.compute_id(cluster.seed_focus, cluster.instance)


def test_snapshot_hash_changes_with_membership_or_live_links():
    cluster = ScratchClusterV1.create(seed_focus="Region", instance=_instance(3))
    first = _block("first", 1)
    second = _block("second", 2)
    link = ScratchLinkV1.create(
        body=ScratchLinkBodyV1(from_=first.id, to=second.id, relation_hint="may relate"),
        instance=_instance(4),
    )
    base = ClusterSnapshotV1.create(
        cluster_id=cluster.id, member_ids=[first.id], live_link_ids=[]
    )
    changed_members = ClusterSnapshotV1.create(
        cluster_id=cluster.id, member_ids=[second.id, first.id], live_link_ids=[]
    )
    changed_links = ClusterSnapshotV1.create(
        cluster_id=cluster.id, member_ids=[first.id], live_link_ids=[link.id]
    )

    assert len({base.snapshot_hash, changed_members.snapshot_hash, changed_links.snapshot_hash}) == 3
    assert list(changed_members.member_ids) == sorted([first.id, second.id])
    assert base.id == base.snapshot_hash


def test_guide_binds_to_exact_snapshot_and_freezes_lists():
    cluster = ScratchClusterV1.create(seed_focus="Region", instance=_instance(3))
    block = _block("entry", 1)
    snapshot = ClusterSnapshotV1.create(
        cluster_id=cluster.id, member_ids=[block.id], live_link_ids=[]
    )
    guide = ClusterGuideV1.create(
        cluster_id=cluster.id,
        based_on_snapshot=snapshot.snapshot_hash,
        working_focus="An unresolved region",
        open_threads=["Does the direction reverse?"],
        entry_points=[block.id],
        local_summary=None,
        authored_by=_call(),
        instance=_instance(21),
    )

    assert guide.based_on_snapshot == snapshot.snapshot_hash
    with pytest.raises(TypeError):
        guide.open_threads.append("mutate")  # type: ignore[union-attr]


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_similarity_values_are_rejected(value: float):
    with pytest.raises((ValidationError, ValueError), match="finite"):
        SimilarityHitV1.create(
            block_a=_hash("1"),
            block_b=_hash("2"),
            embedder="fallback",
            embedder_version="v1",
            score=value,
            threshold_used=0.8,
            input_body_hash_a=_hash("3"),
            input_body_hash_b=_hash("4"),
            instance=_instance(1),
        )


def test_similarity_factory_normalizes_integer_numeric_inputs_before_hashing():
    hit = SimilarityHitV1.create(
        block_a=_hash("1"),
        block_b=_hash("2"),
        embedder="fallback",
        embedder_version="v1",
        score=1,
        threshold_used=0,
        input_body_hash_a=_hash("3"),
        input_body_hash_b=_hash("4"),
        instance=_instance(1),
    )

    assert hit.score == 1.0
    assert hit.threshold_used == 0.0


def test_receipts_visibility_coverage_and_advisory_context_are_immutable():
    block = _block("unsettled", 1)
    request_hash = domain_hash("scratch.attention.request.v1", {"focus": [block.id]})
    receipt = AttentionReceiptV1.create(
        state_seq=3,
        request_hash=request_hash,
        selected_by_channel={"focus": [block.id], "coverage": []},
        final_order=[block.id],
        excluded_by_global_limit=[],
        excluded_by_channel={},
        deterministic_seed=7,
        coverage_cycle_id=None,
        instance=_instance(3),
    )
    visibility = VisibilityRecordV1.create(
        block_id=block.id,
        first_created_seq=1,
        render_count=1,
        last_rendered_seq=3,
        retrieval_channels_used=["focus"],
        contexts_rendered_into=[receipt.receipt_hash],
        instance=_instance(3),
    )
    coverage = CoverageCycleV1.create(live_ids=[block.id], instance=_instance(4))
    advisory = AdvisoryContextV1.create(
        warning="Scratch material is non-authoritative.",
        blocks=[block],
        links=None,
        guides=None,
        retrieval_receipt=receipt.receipt_hash,
        instance=_instance(5),
    )

    assert receipt.receipt_hash.startswith("sha256:")
    assert receipt.id == receipt.receipt_hash
    assert visibility.id.startswith("sha256:")
    assert coverage.pending_block_ids == [block.id]
    assert coverage.id == coverage.cycle_id
    assert advisory.blocks == [block]
    with pytest.raises(TypeError):
        receipt.final_order.append(_hash("9"))
    with pytest.raises(TypeError):
        receipt.selected_by_channel["focus"].append(_hash("9"))
    with pytest.raises(TypeError):
        advisory.blocks.clear()


def test_empty_advisory_context_is_valid_for_runs_without_scratch_material():
    receipt_ref = _hash("0")
    context = AdvisoryContextV1.create(
        warning="Scratch material is non-authoritative and may be incomplete.",
        blocks=[],
        retrieval_receipt=receipt_ref,
        instance=_instance(9),
    )

    assert context.blocks == []
    with pytest.raises(ValidationError, match="non-authoritative"):
        AdvisoryContextV1.create(
            warning="Everything below is established.",
            blocks=[],
            retrieval_receipt=receipt_ref,
            instance=_instance(9),
        )


def test_attention_receipt_hash_is_stable_for_string_or_enum_channel_keys():
    block = _block("unsettled", 1)
    common = {
        "state_seq": 3,
        "request_hash": domain_hash("scratch.attention.request.v1", {"focus": [block.id]}),
        "final_order": [block.id],
        "excluded_by_global_limit": [],
        "excluded_by_channel": {},
        "deterministic_seed": 7,
        "coverage_cycle_id": None,
        "instance": _instance(3),
    }

    string_key = AttentionReceiptV1.create(
        selected_by_channel={"focus": [block.id]}, **common
    )
    enum_key = AttentionReceiptV1.create(
        selected_by_channel={RetrievalChannel.FOCUS: [block.id]}, **common
    )

    assert string_key.receipt_hash == enum_key.receipt_hash


def test_all_scratch_models_forbid_extra_fields():
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ScratchBlockBodyV1(content="valid", workflow_authority="route elsewhere")
    with pytest.raises(ValidationError, match="extra_forbidden"):
        InstanceRef(run_id=RUN_ID, seq=1, wall_clock="now")


def test_canonical_bytes_are_stable_under_mapping_key_order_variation():
    left = {"z": 1, "a": {"second": 2, "first": 1}}
    right = {"a": {"first": 1, "second": 2}, "z": 1}

    assert canonical_json(left) == canonical_json(right)
    assert domain_hash("test.domain", left) == domain_hash("test.domain", right)


def test_explicit_canonical_ids_cannot_be_spoofed_for_other_records():
    cluster = ScratchClusterV1.create(seed_focus="Region", instance=_instance(1))
    dumped = cluster.model_dump(mode="json")

    with pytest.raises(ValidationError, match="canonical scratch cluster identity"):
        ScratchClusterV1.model_validate({**dumped, "id": _hash("f")})
