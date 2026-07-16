"""Deterministic bounded selection from one immutable evidence dossier."""

from __future__ import annotations

from collections.abc import Mapping
import re
from pathlib import Path

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.evidence.models import (
    DossierExcerptV1,
    DossierPackReceiptV1,
    EvidenceDossierV1,
    RunInputManifestV1,
)
from deepreason.storage.blobs import BlobStore


_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+/-]{1,127}")
_ALGORITHM = "dossier-pack.literal-underexposure.v1"


def _tokens(text: str) -> frozenset[str]:
    return frozenset(match.group(0).casefold() for match in _TOKEN.finditer(text))


def _bounded_prefix(body: bytes, maximum: int) -> bytes:
    prefix = body[:maximum]
    # Prefer a valid UTF-8 boundary for textual material while retaining a
    # deterministic raw-byte fallback for non-text sources.
    while prefix:
        try:
            prefix.decode("utf-8")
            return prefix
        except UnicodeDecodeError as error:
            if error.start < len(prefix) - 4:
                return prefix
            prefix = prefix[: error.start]
    return body[:maximum]


def pack_dossier(
    *,
    root: Path | str,
    run_input: RunInputManifestV1,
    dossier: EvidenceDossierV1,
    work_order_ref: str,
    query: str,
    state_fence: str,
    maximum_sources: int,
    maximum_excerpt_bytes_per_source: int,
    maximum_total_excerpt_bytes: int,
    exposure_counts: Mapping[str, int] | None = None,
) -> DossierPackReceiptV1:
    """Select and materialize one replayable advisory evidence pack.

    Ranking uses only frozen source cards, the explicit query, and supplied
    exposure counts. No source is admitted as true by this operation.
    """

    if not query.strip():
        raise ValueError("dossier query must be nonblank")
    if not state_fence.strip():
        raise ValueError("dossier state fence must be nonblank")
    if not 1 <= maximum_sources <= 1_000:
        raise ValueError("maximum dossier sources must be finite and positive")
    if not 1 <= maximum_excerpt_bytes_per_source <= 262_144:
        raise ValueError("per-source excerpt bound must be finite and positive")
    if not 1 <= maximum_total_excerpt_bytes <= 4 * 1024 * 1024:
        raise ValueError("total excerpt bound must be finite and positive")
    if run_input.evidence_dossier_digest != dossier.dossier_digest:
        raise ValueError("run input does not bind the supplied evidence dossier")

    exposures = dict(exposure_counts or {})
    known_ids = {source.id for source in dossier.sources}
    if any(
        source_id not in known_ids
        or not isinstance(count, int)
        or isinstance(count, bool)
        or count < 0
        for source_id, count in exposures.items()
    ):
        raise ValueError("exposure counts must be nonnegative integers for dossier sources")

    query_tokens = _tokens(query)
    scored = []
    for source in dossier.sources:
        literal_text = " ".join(
            (
                source.title,
                source.source_locator,
                *source.declared_entities,
                *source.declared_facets,
            )
        )
        overlap = len(query_tokens & _tokens(literal_text))
        deterministic_exploration = sha256_hex(
            canonical_json(
                {
                    "algorithm": _ALGORITHM,
                    "run_input_digest": run_input.run_input_digest,
                    "query": query,
                    "source_id": source.id,
                }
            )
        )
        scored.append(
            (
                -overlap,
                exposures.get(source.id, 0),
                deterministic_exploration,
                source.id,
                source,
            )
        )
    scored.sort(key=lambda item: item[:4])

    store = BlobStore(Path(root) / "blobs")
    selected_sources = []
    excerpts = []
    remaining = maximum_total_excerpt_bytes
    for *_score, source in scored:
        if len(selected_sources) >= maximum_sources or remaining <= 0:
            break
        body = store.get(source.content_ref)
        maximum = min(maximum_excerpt_bytes_per_source, remaining, len(body))
        if maximum <= 0:
            continue
        excerpt = _bounded_prefix(body, maximum)
        if not excerpt:
            continue
        ref = store.put(excerpt)
        selected_sources.append(source)
        excerpts.append(
            DossierExcerptV1(
                source_id=source.id,
                excerpt_ref=ref,
                excerpt_sha256=ref,
                byte_count=len(excerpt),
            )
        )
        remaining -= len(excerpt)

    candidate_ids = tuple(source.id for source in dossier.sources)
    selected_ids = tuple(source.id for source in selected_sources)
    selected_set = set(selected_ids)
    excluded_ids = tuple(source_id for source_id in candidate_ids if source_id not in selected_set)
    policy_digest = sha256_hex(
        canonical_json(
            {
                "algorithm": _ALGORITHM,
                "maximum_excerpt_bytes_per_source": maximum_excerpt_bytes_per_source,
                "maximum_sources": maximum_sources,
                "maximum_total_excerpt_bytes": maximum_total_excerpt_bytes,
            }
        )
    )
    return DossierPackReceiptV1.create(
        run_input_digest=run_input.run_input_digest,
        work_order_ref=work_order_ref,
        query=query,
        candidate_source_ids=candidate_ids,
        selected_source_ids=selected_ids,
        excerpts=tuple(excerpts),
        excluded_source_ids=excluded_ids,
        policy_digest=policy_digest,
        state_fence=state_fence,
    )


__all__ = ["pack_dossier"]


def commit_dossier_pack_receipt(harness, receipt: DossierPackReceiptV1) -> None:
    """Make one pack receipt reachable without assigning epistemic status."""

    receipt = DossierPackReceiptV1.model_validate(
        receipt.model_dump(mode="python", by_alias=True)
    )
    harness.record_dossier_pack_receipt(receipt)


def dossier_exposure_counts(harness) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in harness.log.read():
        if not event.inputs or event.inputs[0] != "dossier-pack-receipt.v1":
            continue
        for source_id in event.inputs[2:]:
            counts[source_id] = counts.get(source_id, 0) + 1
    return counts


__all__ = [
    "commit_dossier_pack_receipt",
    "dossier_exposure_counts",
    "pack_dossier",
]
