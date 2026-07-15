"""Dependency-free deterministic literal search over immutable blocks."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from deepreason.scratch.models import ScratchBlockV1


def normalize_search_text(value: str) -> str:
    """Normalize for retrieval only; canonical block identity is untouched."""

    return " ".join(value.casefold().split())


def search_tokens(value: str) -> tuple[str, ...]:
    return tuple(normalize_search_text(value).split())


@dataclass(frozen=True)
class LiteralSearchHit:
    block: ScratchBlockV1
    score: int
    matched_tokens: tuple[str, ...]


def literal_search(
    blocks: list[ScratchBlockV1], query: str, *, limit: int
) -> list[LiteralSearchHit]:
    """Return stable literal matches ranked by evidence in the block text.

    A whole normalized phrase match ranks above token-only matches, followed
    by token coverage and occurrence count. The canonical block ID is the
    final tie-break, so filesystem order and wall-clock time are irrelevant.
    """

    normalized_query = normalize_search_text(query)
    tokens = tuple(normalized_query.split())
    if not tokens:
        return []
    unique_tokens = tuple(dict.fromkeys(tokens))
    ranked: list[tuple[tuple[int, int, int, str], LiteralSearchHit]] = []
    for block in blocks:
        fields = (
            block.body.content,
            block.body.why_keep_this or "",
            block.body.unfinished or "",
            block.body.possible_next_move or "",
        )
        haystack = normalize_search_text(" ".join(fields))
        haystack_tokens = Counter(haystack.split())
        counts = {token: haystack_tokens[token] for token in unique_tokens}
        matched = tuple(token for token in unique_tokens if counts[token] > 0)
        if not matched:
            continue
        phrase = int(normalized_query in haystack)
        coverage = len(matched)
        occurrences = sum(counts[token] for token in matched)
        score = phrase * 1_000_000 + coverage * 1_000 + occurrences
        hit = LiteralSearchHit(block=block, score=score, matched_tokens=matched)
        ranked.append(((-phrase, -coverage, -occurrences, block.id), hit))
    ranked.sort(key=lambda item: item[0])
    return [hit for _, hit in ranked[:limit]]


__all__ = ["LiteralSearchHit", "literal_search", "normalize_search_text", "search_tokens"]
