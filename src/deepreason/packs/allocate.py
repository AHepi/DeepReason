"""Deterministic per-section allocation; never prefix-clips a whole pack."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass

from deepreason.packs.ir import PackIR, PackSection


def approximate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def _bounded_view(text: str, tokens: int) -> str:
    chars = max(0, tokens * 4)
    if len(text) <= chars:
        return text
    if chars < 40:
        return text[:chars]
    marker = "\n…[section compressed]…\n"
    remaining = max(0, chars - len(marker))
    head = remaining * 2 // 3
    return text[:head] + marker + text[-(remaining - head) :]


@dataclass(frozen=True)
class AllocatedSection:
    id: str
    text: str
    tokens: int
    source_tokens: int
    dropped: bool
    digest: str
    cache_group: str


@dataclass(frozen=True)
class AllocationResult:
    text: str
    sections: tuple[AllocatedSection, ...]
    target_tokens: int
    allocated_tokens: int
    mandatory_overflow: int

    def accounting(self) -> dict:
        return {
            "target_tokens": self.target_tokens,
            "allocated_tokens": self.allocated_tokens,
            "mandatory_overflow": self.mandatory_overflow,
            "sections": {
                section.id: {
                    "tokens": section.tokens,
                    "source_tokens": section.source_tokens,
                    "dropped": section.dropped,
                    "cache_group": section.cache_group,
                }
                for section in self.sections
            },
        }


def _resolve(section: PackSection, resolver: Callable[[str], str] | None) -> str:
    if section.text_ref.startswith("inline:"):
        return section.text_ref.removeprefix("inline:")
    if resolver is None:
        raise ValueError(f"no resolver for pack text ref {section.text_ref!r}")
    return resolver(section.text_ref)


def allocate_pack(
    ir: PackIR,
    resolver: Callable[[str], str] | None = None,
) -> AllocationResult:
    """Allocate mandatory minima first, then expand in declared priority.

    A non-droppable, non-compressible section is retained in full even when it
    exceeds its declared target.  This is how criteria and output contracts
    remain exact without permitting an infinite operation.
    """

    ordered = sorted(ir.sections, key=lambda section: (section.priority, section.id))
    source = {section.id: _resolve(section, resolver) for section in ordered}
    source_tokens = {
        section.id: approximate_tokens(source[section.id]) for section in ordered
    }
    allocation: dict[str, int] = {}
    for section in ordered:
        available = source_tokens[section.id]
        if not section.droppable and not section.compressible:
            allocation[section.id] = available
        elif not section.droppable:
            allocation[section.id] = min(available, section.min_tokens)
        else:
            allocation[section.id] = 0

    mandatory = sum(allocation.values())
    remaining = max(0, ir.target_tokens - mandatory)
    for section in ordered:
        available = source_tokens[section.id]
        current = allocation[section.id]
        if section.droppable and current == 0:
            minimum = min(section.min_tokens, available)
            if minimum > remaining:
                continue
            allocation[section.id] = minimum
            current = minimum
            remaining -= minimum
        ceiling = min(section.max_tokens, available)
        extra = min(max(0, ceiling - current), remaining)
        allocation[section.id] += extra
        remaining -= extra

    rendered: list[str] = []
    results: list[AllocatedSection] = []
    for section in ordered:
        raw = source[section.id]
        take = allocation[section.id]
        dropped = take == 0
        if dropped:
            view = ""
        elif take >= source_tokens[section.id]:
            view = raw
        elif section.compressible:
            view = _bounded_view(raw, take)
        else:
            # Exact mandatory sections are never clipped; optional exact
            # sections were admitted only when their whole minimum fit.
            view = raw
            take = source_tokens[section.id]
        if view:
            rendered.append(f"## {section.id}\n{view}")
        results.append(
            AllocatedSection(
                id=section.id,
                text=view,
                tokens=take,
                source_tokens=source_tokens[section.id],
                dropped=dropped,
                digest=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                cache_group=section.cache_group,
            )
        )
    total = sum(section.tokens for section in results)
    return AllocationResult(
        text="\n\n".join(rendered),
        sections=tuple(results),
        target_tokens=ir.target_tokens,
        allocated_tokens=total,
        mandatory_overflow=max(0, mandatory - ir.target_tokens),
    )
