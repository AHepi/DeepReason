"""Replayable scratch similarity observations.

Embedding proximity is one retrieval signal.  It never establishes identity,
truth, support, attack, duplication, deletion, or a scratch link.  The raw
vectors and exact embedder fingerprint are stored as an immutable blob before
the canonical :class:`SimilarityHitV1` is recorded through ``ScratchService``.
Replay reads that receipt and the hit; it never calls the embedder again.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from pydantic import Field

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.llm import embedder as embedder_module
from deepreason.scratch.models import (
    HashRef,
    InstanceRef,
    ScratchBlockBodyV1,
    ScratchBlockV1,
    ScratchRecord,
    SimilarityHitV1,
)
from deepreason.scratch.service import ScratchService


_MAX_VECTOR_DIMENSION = 65_536
_MAX_IDENTITY_LENGTH = 512
_MAX_FINGERPRINT_BYTES = 65_536


class ScratchSimilarityError(ValueError):
    """A stable, local validation failure at the similarity boundary."""

    def __init__(self, code: str, message: str, pointer: str = "") -> None:
        self.code = code
        self.pointer = pointer
        location = f" at {pointer}" if pointer else ""
        super().__init__(f"{code}{location}: {message}")


@dataclass(frozen=True)
class EmbedderSelection:
    """The actual local embedder plus visible fallback provenance."""

    engine: Any
    requested_model: str | None = None
    fallback: bool = False
    fallback_reason: str | None = None


class ScratchEmbeddingInputV1(ScratchRecord):
    """Strict immutable input derived only from a canonical block body."""

    schema_: Literal["scratch.embedding.input.v1"] = Field(
        "scratch.embedding.input.v1", alias="schema"
    )
    block_id: HashRef
    body_hash: HashRef
    body: ScratchBlockBodyV1

    @classmethod
    def from_block(cls, block: ScratchBlockV1) -> ScratchEmbeddingInputV1:
        return cls(block_id=block.id, body_hash=block.body_hash, body=block.body)

    def render(self) -> str:
        sections = [("content", self.body.content)]
        for name in ("why_keep_this", "unfinished", "possible_next_move"):
            value = getattr(self.body, name)
            if value is not None:
                sections.append((name, value))
        return "\n\n".join(f"{name}:\n{value}" for name, value in sections)


def select_embedder(
    *,
    embedder: Any | None = None,
    model: str | None = None,
) -> EmbedderSelection:
    """Select an existing embedder or the repository's deterministic fallback.

    Supplying both an object and a configured model is ambiguous and rejected.
    An unavailable optional neural backend degrades to ``HashingEmbedder`` with
    an explicit receipt flag and identity label.  No provider or LLM is called.
    """

    if embedder is not None and model is not None:
        raise ScratchSimilarityError(
            "SCRATCH_EMBEDDER_SELECTION_INVALID",
            "provide embedder or model, not both",
            "/embedder",
        )
    if embedder is not None:
        fallback = isinstance(embedder, embedder_module.HashingEmbedder)
        return EmbedderSelection(
            engine=embedder,
            fallback=fallback,
            fallback_reason="deterministic_hashing_backend" if fallback else None,
        )
    if not model:
        return EmbedderSelection(
            engine=embedder_module.HashingEmbedder(),
            fallback=True,
            fallback_reason="zero_dependency_default",
        )
    if not isinstance(model, str) or not model.strip() or len(model) > 512:
        raise ScratchSimilarityError(
            "SCRATCH_EMBEDDER_SELECTION_INVALID",
            "model must be non-blank text of at most 512 characters",
            "/model",
        )
    try:
        engine = embedder_module.build_embedder(model)
    except embedder_module.EmbedderUnavailable:
        return EmbedderSelection(
            engine=embedder_module.HashingEmbedder(),
            requested_model=model,
            fallback=True,
            fallback_reason="configured_backend_unavailable",
        )
    return EmbedderSelection(engine=engine, requested_model=model)


def embedding_text(block: ScratchBlockV1) -> str:
    """Render all canonical body content for embedding without changing it."""

    return ScratchEmbeddingInputV1.from_block(block).render()


def _json_safe(value: Any, pointer: str = "/fingerprint") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ScratchSimilarityError(
                "SCRATCH_EMBEDDER_FINGERPRINT_INVALID",
                "fingerprint contains a non-finite number",
                pointer,
            )
        return value
    if isinstance(value, Enum):
        return _json_safe(value.value, pointer)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item, f"{pointer}/{key}")
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item, f"{pointer}/{index}") for index, item in enumerate(value)]
    raise ScratchSimilarityError(
        "SCRATCH_EMBEDDER_FINGERPRINT_INVALID",
        f"unsupported fingerprint value {type(value).__name__}",
        pointer,
    )


def _finite_vector(raw: Sequence[Any], pointer: str) -> list[float]:
    if isinstance(raw, (str, bytes)):
        raise ScratchSimilarityError(
            "SCRATCH_EMBEDDING_INVALID", "embedding must be a numeric sequence", pointer
        )
    try:
        vector = [float(value) for value in raw]
    except (TypeError, ValueError, OverflowError) as error:
        raise ScratchSimilarityError(
            "SCRATCH_EMBEDDING_INVALID", "embedding must be a numeric sequence", pointer
        ) from error
    if not vector or len(vector) > _MAX_VECTOR_DIMENSION:
        raise ScratchSimilarityError(
            "SCRATCH_EMBEDDING_INVALID",
            f"embedding dimension must be from 1 through {_MAX_VECTOR_DIMENSION}",
            pointer,
        )
    if any(not math.isfinite(value) for value in vector):
        raise ScratchSimilarityError(
            "SCRATCH_EMBEDDING_INVALID", "embedding contains a non-finite value", pointer
        )
    return vector


def _engine_fingerprint(engine: Any) -> dict[str, Any]:
    method = getattr(engine, "fingerprint", None)
    if callable(method):
        raw = method()
        if not isinstance(raw, Mapping):
            raise ScratchSimilarityError(
                "SCRATCH_EMBEDDER_FINGERPRINT_INVALID",
                "fingerprint() must return a mapping",
                "/fingerprint",
            )
        fingerprint = _json_safe(raw)
    else:
        fingerprint = {
            "model": str(getattr(engine, "model", type(engine).__name__)),
            "version": str(getattr(engine, "version", "unknown")),
            "sentinel": "unavailable",
        }
    encoded = canonical_json(fingerprint)
    if len(encoded) > _MAX_FINGERPRINT_BYTES:
        raise ScratchSimilarityError(
            "SCRATCH_EMBEDDER_FINGERPRINT_INVALID",
            f"fingerprint exceeds {_MAX_FINGERPRINT_BYTES} canonical bytes",
            "/fingerprint",
        )
    return fingerprint


def _identity(selection: EmbedderSelection, fingerprint: Mapping[str, Any]) -> tuple[str, str]:
    engine = selection.engine
    model = str(getattr(engine, "model", type(engine).__name__)).strip()
    name = str(getattr(engine, "name", type(engine).__name__)).strip()
    version = str(getattr(engine, "version", "unknown")).strip()
    if selection.fallback:
        identity = f"deterministic-fallback:{model}"
    else:
        identity = f"{name}:{model}"
    if not identity.strip(":") or len(identity) > _MAX_IDENTITY_LENGTH:
        raise ScratchSimilarityError(
            "SCRATCH_EMBEDDER_IDENTITY_INVALID",
            f"embedder identity must be at most {_MAX_IDENTITY_LENGTH} characters",
            "/embedder",
        )
    fingerprint_hash = sha256_hex(canonical_json(fingerprint))[:16]
    stamped_version = f"{version}+fp:{fingerprint_hash}"
    if len(stamped_version) > _MAX_IDENTITY_LENGTH:
        raise ScratchSimilarityError(
            "SCRATCH_EMBEDDER_IDENTITY_INVALID",
            f"embedder version must be at most {_MAX_IDENTITY_LENGTH} characters",
            "/embedder_version",
        )
    return identity, stamped_version


class ScratchSimilarityService:
    """Compute and persist pairwise proximity without granting it authority."""

    def __init__(
        self,
        service: ScratchService,
        *,
        embedder: Any | None = None,
        model: str | None = None,
    ) -> None:
        self.service = service
        self.selection = select_embedder(embedder=embedder, model=model)

    @classmethod
    def from_config(cls, service: ScratchService, config) -> ScratchSimilarityService:
        """Reuse the repository fallback seam so degradation lands on the log."""

        from deepreason.ops import make_embedder

        engine = make_embedder(service.harness, config)
        requested = getattr(config, "EMBEDDER_MODEL", None)
        if engine is None:
            instance = cls(service, embedder=embedder_module.HashingEmbedder())
            instance.selection = EmbedderSelection(
                engine=instance.selection.engine,
                requested_model=requested,
                fallback=True,
                fallback_reason=(
                    "configured_backend_unavailable"
                    if requested
                    else "zero_dependency_default"
                ),
            )
            return instance
        return cls(service, embedder=engine)

    def record_pair(
        self,
        block_a: str,
        block_b: str,
        *,
        threshold_used: float,
    ) -> SimilarityHitV1:
        """Record one canonical pair observation and its raw vector receipt."""

        self.service._ensure_writable()
        try:
            threshold = float(threshold_used)
        except (TypeError, ValueError, OverflowError) as error:
            raise ScratchSimilarityError(
                "SCRATCH_SIMILARITY_THRESHOLD_INVALID",
                "threshold_used must be finite",
                "/threshold_used",
            ) from error
        if not math.isfinite(threshold):
            raise ScratchSimilarityError(
                "SCRATCH_SIMILARITY_THRESHOLD_INVALID",
                "threshold_used must be finite",
                "/threshold_used",
            )

        first = self.service.get_block(block_a)
        second = self.service.get_block(block_b)
        if first.id == second.id:
            raise ScratchSimilarityError(
                "SCRATCH_SIMILARITY_SAME_INSTANCE",
                "similarity requires two distinct block instances",
                "/block_b",
            )
        left, right = sorted((first, second), key=lambda block: block.id)

        engine = self.selection.engine
        left_input = ScratchEmbeddingInputV1.from_block(left)
        right_input = ScratchEmbeddingInputV1.from_block(right)
        left_vector = _finite_vector(engine.embed(left_input.render()), "/vectors/0")
        if left.body_hash == right.body_hash:
            # Exact canonical bodies remain distinct instances.  Reusing the
            # one vector is a deterministic computation saving, not a merge.
            right_vector = list(left_vector)
        else:
            right_vector = _finite_vector(engine.embed(right_input.render()), "/vectors/1")
        if len(left_vector) != len(right_vector):
            raise ScratchSimilarityError(
                "SCRATCH_EMBEDDING_INVALID",
                "pair embeddings have different dimensions",
                "/vectors",
            )

        score = float(embedder_module.cosine(left_vector, right_vector))
        if not math.isfinite(score):
            raise ScratchSimilarityError(
                "SCRATCH_EMBEDDING_INVALID", "similarity score is non-finite", "/score"
            )
        # Floating dot products may overshoot by a few ulps.  The clamped
        # value remains a retrieval observation in the documented cosine range.
        score = max(-1.0, min(1.0, score))
        fingerprint = _engine_fingerprint(engine)
        embedder_id, embedder_version = _identity(self.selection, fingerprint)
        vectors = [left_vector, right_vector]
        receipt = {
            "schema": "scratch.embedding.receipt.v1",
            "block_ids": [left.id, right.id],
            "body_hashes": [left.body_hash, right.body_hash],
            "embedder": embedder_id,
            "embedder_version": embedder_version,
            "fingerprint": fingerprint,
            "requested_model": self.selection.requested_model,
            "fallback": self.selection.fallback,
            "fallback_reason": self.selection.fallback_reason,
            "metric": "cosine_similarity",
            "score": score,
            "threshold_used": threshold,
            "vectors": vectors,
            "vector_fingerprint": sha256_hex(canonical_json(vectors)),
        }
        output_ref = self.service.harness.blobs.put(canonical_json(receipt))
        hit = SimilarityHitV1.create(
            block_a=left.id,
            block_b=right.id,
            embedder=embedder_id,
            embedder_version=embedder_version,
            score=score,
            threshold_used=threshold,
            input_body_hash_a=left.body_hash,
            input_body_hash_b=right.body_hash,
            output_ref=output_ref,
            instance=InstanceRef(
                run_id=self.service.run_id,
                seq=self.service.harness._next_seq,
            ),
        )
        return self.service.record_similarity(hit)


# Compact aliases/convenience function for callers that do not need to retain
# a configured boundary object.
SimilarityService = ScratchSimilarityService


def record_similarity_pair(
    service: ScratchService,
    block_a: str,
    block_b: str,
    *,
    threshold_used: float,
    embedder: Any | None = None,
    model: str | None = None,
) -> SimilarityHitV1:
    return ScratchSimilarityService(
        service, embedder=embedder, model=model
    ).record_pair(block_a, block_b, threshold_used=threshold_used)


__all__ = [
    "EmbedderSelection",
    "ScratchSimilarityError",
    "ScratchSimilarityService",
    "SimilarityService",
    "embedding_text",
    "record_similarity_pair",
    "select_embedder",
]
