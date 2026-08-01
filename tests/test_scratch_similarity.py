"""Similarity remains a replayable retrieval observation, never authority."""

from __future__ import annotations

import json
import math

import pytest

from deepreason.harness import Harness
from deepreason.llm import embedder as embedder_module
from deepreason.scratch.models import ScratchBlockBodyV1, ScratchProvenanceV1, domain_hash
from deepreason.scratch.service import ScratchService
from deepreason.scratch.similarity import (
    ScratchEmbeddingInputV1,
    ScratchSimilarityError,
    ScratchSimilarityService,
    select_embedder,
)
from deepreason.config import Config


RUN_ID = domain_hash("test.scratch.similarity.run.v1", {"fixture": True})
PROVENANCE = ScratchProvenanceV1(actor="user", origin="similarity fixture")


class ScriptedEmbedder:
    name = "scripted"
    model = "scripted-vectors"
    version = "1"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        if "orthogonal" in text:
            return [0.0, 1.0]
        return [1.0, 0.0]

    def fingerprint(self) -> dict[str, str]:
        return {"model": self.model, "version": self.version, "sentinel": "scripted"}


def _service(tmp_path) -> ScratchService:
    return ScratchService(Harness(tmp_path / "run"), run_id=RUN_ID)


def _blocks(service: ScratchService, first: str, second: str):
    return (
        service.create_block(ScratchBlockBodyV1(content=first), PROVENANCE),
        service.create_block(ScratchBlockBodyV1(content=second), PROVENANCE),
    )


def _receipt(service: ScratchService, output_ref: str) -> dict:
    return json.loads(service.harness.blobs.get(output_ref))


def test_pair_orientation_and_raw_receipt_are_canonical_and_replayable(tmp_path):
    service = _service(tmp_path)
    first, second = _blocks(service, "alpha mechanism", "orthogonal mechanism")
    engine = ScriptedEmbedder()
    similarity = ScratchSimilarityService(service, embedder=engine)

    forward = similarity.record_pair(first.id, second.id, threshold_used=0.7)
    reverse = similarity.record_pair(second.id, first.id, threshold_used=0.7)

    assert [forward.block_a, forward.block_b] == sorted([first.id, second.id])
    assert (reverse.block_a, reverse.block_b) == (forward.block_a, forward.block_b)
    assert reverse.output_ref == forward.output_ref
    receipt = _receipt(service, forward.output_ref)
    assert receipt["block_ids"] == sorted([first.id, second.id])
    expected_vectors = {
        first.id: [1.0, 0.0],
        second.id: [0.0, 1.0],
    }
    assert receipt["vectors"] == [
        expected_vectors[block_id] for block_id in receipt["block_ids"]
    ]
    assert len(receipt["vector_fingerprint"]) == 64
    assert receipt["fingerprint"]["sentinel"] == "scripted"

    reopened = Harness(service.harness.root)
    assert set(reopened.scratch_state.similarity_hits) == {forward.id, reverse.id}
    assert reopened.blobs.get(forward.output_ref) == service.harness.blobs.get(
        forward.output_ref
    )


def test_embedding_input_is_strict_immutable_and_body_derived(tmp_path):
    service = _service(tmp_path)
    block = service.create_block(
        ScratchBlockBodyV1(content="content", unfinished="open qualification"),
        PROVENANCE,
    )
    value = ScratchEmbeddingInputV1.from_block(block)
    assert value.block_id == block.id
    assert value.body_hash == block.body_hash
    assert "open qualification" in value.render()
    with pytest.raises(Exception):
        value.body_hash = domain_hash("forged", {})


def test_high_similarity_never_links_merges_deletes_or_changes_formal_state(tmp_path):
    service = _service(tmp_path)
    first, second = _blocks(service, "same lexical region", "same lexical region with detail")
    formal_before = service.harness.state.model_dump(mode="json")

    hit = ScratchSimilarityService(service, embedder=ScriptedEmbedder()).record_pair(
        first.id, second.id, threshold_used=0.5
    )

    assert hit.score == 1.0
    assert hit.score >= hit.threshold_used
    assert set(service.state.blocks) == {first.id, second.id}
    assert first.id != second.id
    assert service.state.links == {}
    assert service.harness.state.model_dump(mode="json") == formal_before


def test_exact_duplicate_bodies_remain_distinct_and_embed_only_once(tmp_path):
    service = _service(tmp_path)
    first, second = _blocks(service, "identical canonical body", "identical canonical body")
    engine = ScriptedEmbedder()

    hit = ScratchSimilarityService(service, embedder=engine).record_pair(
        second.id, first.id, threshold_used=0.99
    )

    assert first.id != second.id
    assert first.body_hash == second.body_hash
    assert len(service.state.block_instances_by_body_hash[first.body_hash]) == 2
    assert len(engine.calls) == 1
    assert hit.score == 1.0
    assert service.state.links == {}
    receipt = _receipt(service, hit.output_ref)
    assert receipt["vectors"][0] == receipt["vectors"][1]


def test_threshold_changes_only_the_observation_and_retrieval_interpretation(tmp_path):
    service = _service(tmp_path)
    first, second = _blocks(service, "alpha mechanism", "orthogonal mechanism")
    similarity = ScratchSimilarityService(service, embedder=ScriptedEmbedder())

    strict = similarity.record_pair(first.id, second.id, threshold_used=0.8)
    permissive = similarity.record_pair(first.id, second.id, threshold_used=-0.1)

    assert strict.score == permissive.score == 0.0
    assert strict.threshold_used == 0.8
    assert permissive.threshold_used == -0.1
    assert strict.id != permissive.id
    assert len(service.state.blocks) == 2
    assert service.state.links == {}


def test_unavailable_optional_backend_uses_visibly_identified_deterministic_fallback(
    tmp_path, monkeypatch
):
    def unavailable(_model):
        raise embedder_module.EmbedderUnavailable("offline fixture")

    monkeypatch.setattr(embedder_module, "build_embedder", unavailable)
    selection = select_embedder(model="configured-neural-model")
    assert isinstance(selection.engine, embedder_module.HashingEmbedder)
    assert selection.fallback is True
    assert selection.fallback_reason == "configured_backend_unavailable"

    service = _service(tmp_path)
    first, second = _blocks(service, "fallback alpha", "fallback beta")
    hit = ScratchSimilarityService(
        service, model="configured-neural-model"
    ).record_pair(first.id, second.id, threshold_used=0.5)
    receipt = _receipt(service, hit.output_ref)

    assert hit.embedder.startswith("deterministic-fallback:")
    assert receipt["fallback"] is True
    assert receipt["fallback_reason"] == "configured_backend_unavailable"
    assert receipt["requested_model"] == "configured-neural-model"
    assert receipt["embedder"] == hit.embedder


def test_configured_fallback_reuses_visible_repository_measure_seam(tmp_path, monkeypatch):
    def unavailable(_model):
        raise embedder_module.EmbedderUnavailable("offline fixture")

    monkeypatch.setattr(embedder_module, "build_embedder", unavailable)
    service = _service(tmp_path)
    first, second = _blocks(service, "alpha", "beta")
    similarity = ScratchSimilarityService.from_config(
        service, Config(EMBEDDER_MODEL="configured-neural-model")
    )
    hit = similarity.record_pair(first.id, second.id, threshold_used=0.5)

    assert hit.embedder.startswith("deterministic-fallback:")
    assert any(
        event.inputs and event.inputs[0] == "embedder-fallback"
        for event in service.harness.log.read()
    )


@pytest.mark.parametrize("threshold", [math.nan, math.inf, -math.inf])
def test_non_finite_threshold_is_rejected_before_embedding(tmp_path, threshold):
    service = _service(tmp_path)
    first, second = _blocks(service, "first", "second")
    engine = ScriptedEmbedder()

    with pytest.raises(ScratchSimilarityError) as raised:
        ScratchSimilarityService(service, embedder=engine).record_pair(
            first.id, second.id, threshold_used=threshold
        )

    assert raised.value.code == "SCRATCH_SIMILARITY_THRESHOLD_INVALID"
    assert raised.value.pointer == "/threshold_used"
    assert engine.calls == []
    assert service.state.similarity_hits == {}


def test_same_instance_and_invalid_vectors_fail_without_similarity_event(tmp_path):
    service = _service(tmp_path)
    first, second = _blocks(service, "first", "second")

    with pytest.raises(ScratchSimilarityError) as same:
        ScratchSimilarityService(service, embedder=ScriptedEmbedder()).record_pair(
            first.id, first.id, threshold_used=0.5
        )
    assert same.value.code == "SCRATCH_SIMILARITY_SAME_INSTANCE"

    class InvalidEmbedder(ScriptedEmbedder):
        def embed(self, text: str) -> list[float]:
            return [math.nan]

    with pytest.raises(ScratchSimilarityError) as invalid:
        ScratchSimilarityService(service, embedder=InvalidEmbedder()).record_pair(
            first.id, second.id, threshold_used=0.5
        )
    assert invalid.value.code == "SCRATCH_EMBEDDING_INVALID"
    assert service.state.similarity_hits == {}
