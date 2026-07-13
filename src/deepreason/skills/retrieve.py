"""Logged deterministic retrieval over a run-local skill snapshot."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.llm.embedder import HashingEmbedder, cosine
from deepreason.skills.models import (
    RankedSkill,
    RawEmbedding,
    RevoicedSkill,
    SchoolSkillSlice,
    SkillLibrarySnapshot,
    SkillRetrievalReceipt,
)
from deepreason.skills.revoice import revoice_capsule
from deepreason.skills.snapshot import load_capsule


def _retrieval_text(capsule) -> str:
    return "\n".join(
        (
            capsule.problem_signature,
            *capsule.accepted_source_structure,
            *capsule.scope,
            *capsule.source_owned_counterconditions,
            *capsule.unresolved_conditions,
            *capsule.overturn_conditions,
        )
    )


def _fingerprint(embedder) -> tuple[str, ...]:
    if hasattr(embedder, "fingerprint"):
        values = embedder.fingerprint()
        return tuple(f"{key}={values[key]}" for key in sorted(values))
    return (
        f"model={getattr(embedder, 'model', type(embedder).__name__)}",
        f"version={getattr(embedder, 'version', '-')}",
    )


def _school_slices(
    ranking: tuple[RankedSkill, ...],
    schools: tuple[str, ...],
    *,
    problem_id: str,
    fanout: bool,
    per_school: int,
) -> tuple[SchoolSkillSlice, ...]:
    if not schools:
        return ()
    blind = None
    if fanout:
        index = int.from_bytes(hashlib.sha256(problem_id.encode()).digest()[:8], "big")
        blind = schools[index % len(schools)]
    active = tuple(school for school in schools if school != blind)
    buckets: dict[str, list[str]] = {school: [] for school in active}
    if active:
        for index, item in enumerate(ranking):
            school = active[index % len(active)]
            if len(buckets[school]) < per_school:
                buckets[school].append(item.capsule_id)
    return tuple(
        SchoolSkillSlice(
            school_id=school,
            blind=school == blind,
            capsule_ids=() if school == blind else tuple(buckets[school]),
        )
        for school in schools
    )


def retrieve_skills(
    snapshot: SkillLibrarySnapshot,
    query: str,
    schools: Iterable[str],
    blobs,
    *,
    problem_id: str,
    fanout: bool = True,
    top_k: int = 12,
    per_school: int = 3,
    embedder=None,
    summarizer: Callable[[str], str] | None = None,
    summarizer_version: str = "none",
    harness=None,
) -> SkillRetrievalReceipt:
    """Rank capsules, partition genuinely distinct slices, and pin a receipt."""

    if not query.strip():
        raise ValueError("skill retrieval query must be nonempty")
    if top_k <= 0 or per_school <= 0:
        raise ValueError("skill retrieval bounds must be positive")
    if blobs.get(snapshot.catalog_ref) is None:  # also proves catalog bytes remain pinned
        raise ValueError("skill catalog snapshot is missing")
    engine = embedder or HashingEmbedder()
    query_vec = tuple(float(value) for value in engine.embed(query))
    loaded = [(entry, load_capsule(entry, blobs)) for entry in snapshot.catalog]
    vectors = [
        (entry, capsule, tuple(float(value) for value in engine.embed(_retrieval_text(capsule))))
        for entry, capsule in loaded
    ]
    scored = sorted(
        (
            (round(1_000_000 * cosine(list(query_vec), list(vector))), entry.capsule_id)
            for entry, _capsule, vector in vectors
        ),
        key=lambda item: (-item[0], item[1]),
    )[:top_k]
    ranking = tuple(
        RankedSkill(capsule_id=capsule_id, score_ppm=score, rank=index + 1)
        for index, (score, capsule_id) in enumerate(scored)
    )
    school_ids = tuple(sorted(set(schools)))
    slices = _school_slices(
        ranking,
        school_ids,
        problem_id=problem_id,
        fanout=fanout,
        per_school=per_school,
    )
    selected_ids = {
        capsule_id for item in slices for capsule_id in item.capsule_ids
    }
    entries = {entry.capsule_id: entry for entry in snapshot.catalog}
    selected = tuple(entries[item] for item in sorted(selected_ids))
    capsule_by_id = {capsule.id: capsule for _entry, capsule in loaded}
    summaries: tuple[RevoicedSkill, ...] = ()
    if summarizer is not None:
        summaries = tuple(
            revoice_capsule(
                capsule_by_id[item],
                summarizer,
                blobs,
                summarizer_version=summarizer_version,
            )
            for item in sorted(selected_ids)
        )
    raw_embeddings = (
        RawEmbedding(item_id="query", vector=query_vec),
        *(
            RawEmbedding(item_id=entry.capsule_id, vector=vector)
            for entry, _capsule, vector in vectors
        ),
    )
    receipt = SkillRetrievalReceipt.create(
        snapshot_digest=snapshot.snapshot_digest,
        query=query,
        query_ref=blobs.put(query.encode()),
        embedder_fingerprint=_fingerprint(engine),
        raw_embeddings=raw_embeddings,
        ranking=ranking,
        school_slices=slices,
        selected_bytes=selected,
        summaries=summaries,
    )
    receipt_ref = blobs.put(canonical_json(receipt.model_dump(mode="json", by_alias=True)))
    if harness is not None:
        harness.record_measure(
            inputs=["skills-retrieval", receipt.receipt_digest, receipt_ref]
        )
    return receipt


def replay_retrieval(receipt: SkillRetrievalReceipt, blobs) -> dict[str, bytes]:
    """Recover selected prompt inputs without embeddings or external storage."""

    if sha256_hex(blobs.get(receipt.query_ref)) != receipt.query_ref:
        raise ValueError("retrieval query bytes do not match their receipt")
    selected: dict[str, bytes] = {}
    for entry in receipt.selected_bytes:
        encoded = blobs.get(entry.content_ref)
        if len(encoded) != entry.byte_length:
            raise ValueError(f"selected skill bytes changed: {entry.capsule_id}")
        selected[entry.capsule_id] = encoded
    for summary in receipt.summaries:
        if sha256_hex(blobs.get(summary.summary_ref)) != summary.summary_digest:
            raise ValueError(f"re-voiced skill bytes changed: {summary.capsule_id}")
    return selected


def render_school_slice(
    receipt: SkillRetrievalReceipt,
    school_id: str,
    blobs,
) -> str:
    """Render re-voiced advice only; capsule prose and verdicts never enter."""

    school = next(
        (item for item in receipt.school_slices if item.school_id == school_id), None
    )
    if school is None:
        raise KeyError(f"school is absent from skill receipt: {school_id}")
    if school.blind:
        return ""
    summaries = {item.capsule_id: item for item in receipt.summaries}
    rows: list[str] = []
    for capsule_id in school.capsule_ids:
        summary = summaries.get(capsule_id)
        if summary is None:
            raise ValueError("skill prose must be re-voiced before generator rendering")
        text = blobs.get(summary.summary_ref).decode("utf-8", errors="strict")
        rows.append(f"Skill {capsule_id[:12]} (advisory only):\n{text}")
    return "\n\n".join(rows)
