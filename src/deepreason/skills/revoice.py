"""Mandatory source-prose re-voicing with a deterministic overlap guard."""

from __future__ import annotations

import re
from collections.abc import Callable

from pydantic import BaseModel

from deepreason.canonical import sha256_hex
from deepreason.skills.distill import validate_positive_material
from deepreason.skills.models import RevoicedSkill, SkillCapsule


class RevoiceOverlapError(ValueError):
    """The summarizer preserved too much of the source voice."""


class _SummaryMaterial(BaseModel):
    text: str


def _words(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", text.casefold()))


def _voice_text(capsule: SkillCapsule) -> str:
    # IDs, commitment definitions, and toolchain coordinates are structural
    # and may render directly.  Only authored prose enters the voice guard.
    fields = (
        (capsule.problem_signature,),
        capsule.accepted_source_structure,
        capsule.scope,
        capsule.source_owned_counterconditions,
        capsule.unresolved_conditions,
        capsule.overturn_conditions,
    )
    return "\n".join(text for group in fields for text in group if text.strip())


def _overlap(source: str, output: str, n: int = 5) -> tuple[int, int]:
    left, right = _words(source), _words(output)
    source_ngrams = {
        left[index : index + n] for index in range(max(0, len(left) - n + 1))
    }
    output_ngrams = [
        right[index : index + n] for index in range(max(0, len(right) - n + 1))
    ]
    matched = sum(item in source_ngrams for item in output_ngrams)
    ppm = round(1_000_000 * matched / max(1, len(output_ngrams)))

    positions: dict[str, list[int]] = {}
    for index, word in enumerate(left):
        positions.setdefault(word, []).append(index)
    previous: dict[int, int] = {}
    longest = 0
    for word in right:
        current: dict[int, int] = {}
        for index in positions.get(word, ()):
            current[index] = previous.get(index - 1, 0) + 1
            longest = max(longest, current[index])
        previous = current
    return ppm, longest


def revoice_capsule(
    capsule: SkillCapsule,
    summarizer: Callable[[str], str],
    blobs,
    *,
    summarizer_version: str,
    max_overlap_ppm: int = 250_000,
    max_contiguous_words: int = 12,
) -> RevoicedSkill:
    source = _voice_text(capsule)
    summary = summarizer(source)
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("skill summarizer must return nonempty text")
    validate_positive_material(_SummaryMaterial(text=summary))
    overlap_ppm, longest = _overlap(source, summary)
    same_short_text = _words(source) == _words(summary) and len(_words(summary)) >= 3
    if same_short_text or overlap_ppm > max_overlap_ppm or longest > max_contiguous_words:
        raise RevoiceOverlapError(
            f"re-voiced skill overlaps source voice: {overlap_ppm} ppm, "
            f"{longest} contiguous words"
        )
    encoded = summary.strip().encode()
    summary_ref = blobs.put(encoded)
    return RevoicedSkill(
        capsule_id=capsule.id,
        source_digest=sha256_hex(source.encode()),
        summary_ref=summary_ref,
        summary_digest=sha256_hex(encoded),
        overlap_ppm=overlap_ppm,
        longest_overlap_words=longest,
        summarizer_version=summarizer_version,
    )
