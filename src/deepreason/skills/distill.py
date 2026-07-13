"""Positive-only deterministic skill and lesson distillation boundaries."""

from __future__ import annotations

import re
from collections.abc import Iterable

from deepreason.harness import Harness
from deepreason.ontology import Status
from deepreason.programs import content_text
from deepreason.skills.models import (
    CapsuleDraft,
    LessonMemory,
    SkillCapsule,
    VerifiedDistillationSource,
)


class NegativeCaseLawError(ValueError):
    """A proposed capsule would expose failed-rival or critic prose."""


_FORBIDDEN_MARKERS = (
    "decisive_point",
    "decisive point:",
    "negative-atlas",
    "negative atlas",
    "refuted rival",
    "criticism transcript",
    "anti-relapse exemplar",
)
_BODY_MARKERS = (
    "<!doctype html",
    "<html",
    "<script",
    "<style",
    "document.queryselector",
    "window.addeventlistener",
)


def _semantic_texts(value) -> tuple[str, ...]:
    data = value.model_dump(mode="json", by_alias=True)
    out: list[str] = []

    def walk(item) -> None:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(data)
    return tuple(out)


def _words(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", text.casefold()))


def _ngrams(text: str, size: int = 8) -> set[tuple[str, ...]]:
    words = _words(text)
    return {words[index : index + size] for index in range(len(words) - size + 1)}


def _negative_ngrams(source: VerifiedDistillationSource) -> set[tuple[str, ...]]:
    harness = Harness.at(source.source_root, source.source_event_seq)
    out: set[tuple[str, ...]] = set()
    for artifact_id, artifact in harness.state.artifacts.items():
        is_failed = harness.state.status.get(artifact_id) == Status.REFUTED
        is_critic = artifact.provenance.role.value == "critic"
        if is_failed or is_critic:
            out.update(_ngrams(content_text(artifact, harness.blobs)))
    return out


def validate_positive_material(
    material,
    *,
    source: VerifiedDistillationSource | None = None,
) -> None:
    """Reject obvious negative-atlas/body leakage and verbatim case law.

    The distiller is intentionally shown only the accepted positive closure.
    This guard is defense in depth for malformed imports: it blocks named
    transcript fields and any eight-word span copied from a refuted artifact
    or critic in the verified source run.  It does not ban source-owned limits
    or overturn conditions, which are constructive attack surfaces.
    """

    texts = _semantic_texts(material)
    for text in texts:
        folded = text.casefold()
        if any(marker in folded for marker in _FORBIDDEN_MARKERS):
            raise NegativeCaseLawError("negative case-law marker is forbidden in skills")
        if any(marker in folded for marker in _BODY_MARKERS):
            raise NegativeCaseLawError("HTML/CSS/JS bodies are forbidden in skills")
    if source is None:
        return
    forbidden = _negative_ngrams(source)
    if forbidden and any(_ngrams(text) & forbidden for text in texts):
        raise NegativeCaseLawError(
            "skill material overlaps verbatim with refuted or critic source prose"
        )


def distill_capsule(
    source: VerifiedDistillationSource,
    draft: CapsuleDraft,
) -> SkillCapsule:
    """Create one content-addressed capsule from a verified accepted source."""

    # Reopening at the exact fence prevents a forged/stale source record from
    # being accepted merely because its JSON has the right shape.
    from deepreason.skills.validate import validate_distillation_source

    checked = validate_distillation_source(
        source.source_root,
        source_event_seq=source.source_event_seq,
        accepted_artifact_id=source.accepted_artifact_id,
        distiller_version=source.distiller_version,
    )
    if checked != source:
        raise ValueError("verified distillation source no longer matches its pinned closure")
    validate_positive_material(draft, source=source)
    return SkillCapsule.create(
        problem_signature=draft.problem_signature,
        accepted_source_structure=draft.accepted_source_structure,
        scope=draft.scope,
        source_owned_counterconditions=draft.source_owned_counterconditions,
        passed_commitments=source.passed_commitments,
        toolchains=source.toolchains,
        packages=source.packages,
        dependency_topology=source.dependency_topology,
        unresolved_conditions=draft.unresolved_conditions,
        overturn_conditions=draft.overturn_conditions,
        source_artifact_id=source.accepted_artifact_id,
        source_event_seq=source.source_event_seq,
        source_snapshot_digest=source.source_snapshot_digest,
        source_config_provenance=source.source_config_provenance,
        distiller_version=source.distiller_version,
    )


def distill_lesson(
    capsule: SkillCapsule,
    *,
    claim: str,
    conditions: Iterable[str],
    procedure: Iterable[str],
    checks: Iterable[str] = (),
    limits: Iterable[str] = (),
    overturn_conditions: Iterable[str],
) -> LessonMemory:
    """Create constructive advisory memory; it carries only source IDs."""

    lesson = LessonMemory(
        claim=claim,
        conditions=tuple(conditions),
        procedure=tuple(procedure),
        checks=tuple(checks),
        limits=tuple(limits),
        overturn_conditions=tuple(overturn_conditions),
        source_refs=(capsule.id,),
    )
    validate_positive_material(lesson)
    return lesson
