"""Section SOURCES — the bridge between the record and a seat's brief.

A PACKAGE of its own, and not a module inside `llm/`, because of a law that
predates it: `llm/` never imports the harness, the scheduler, the rules, the
adjudicator or the amendment machinery, so that a transport bug cannot become
an adjudication bug (`DR-SUB-llm`, whose check enforces the arrow). A source's
whole reason to exist is that it READS the record -- the dossier union across
amendment epochs, the fence sequence, the open criticisms -- so a source inside
`llm/` would have inverted that arrow on its first line.

The arrow this package points is the safe one: `seat_sources` reads the record
and imports `llm/` for the allocated-pack marker; nothing in `llm/` imports
this package. `rules/` runs the sources and hands their output to the renderer,
which is why the renderer still knows nothing about where its content came
from.

`registry.py` holds the protocol, the registries and the runner; `shipped.py`
holds the thirteen sources the tree ships and the conjecturer's default bundle.
This module is the interface: consumers import from here.
"""

from deepreason.seat_sources.registry import (
    POST_ALLOCATION_STAGES,
    SEAT_SOURCE_BUNDLE_ENV,
    SECTION_SOURCE_REGISTRY,
    SOURCE_DISPOSITIONS,
    SOURCE_SCHEMA_VERSION,
    STAGE_POST_ALLOCATION,
    STAGE_POST_ALLOCATION_AFTER_ALIASES,
    STAGE_POST_ALLOCATION_CONTEXT,
    STAGE_PRE_CONTRACT,
    STAGE_RENDER,
    STAGES,
    SeatSectionSourceV1,
    SeatSourceBundleEntryV1,
    SeatSourceBundleV1,
    SeatSourceError,
    SectionSourceReceiptV1,
    SectionSourceRequestV1,
    SectionSourceResultV1,
    SourceAssemblyV1,
    apply_post_allocation,
    assemble_sources,
    register_seat_source_bundle,
    register_section_source,
    resolve_seat_source_bundle,
    resolve_section_source,
    seat_source_bundle_ids,
    section_source_ids,
)
from deepreason.seat_sources.shipped import (
    CONJECTURER_SEAT,
    CONJECTURER_SOURCE_BUNDLE,
    ensure_sources_seeded,
)

__all__ = [
    "CONJECTURER_SEAT",
    "CONJECTURER_SOURCE_BUNDLE",
    "POST_ALLOCATION_STAGES",
    "SEAT_SOURCE_BUNDLE_ENV",
    "SECTION_SOURCE_REGISTRY",
    "SOURCE_DISPOSITIONS",
    "SOURCE_SCHEMA_VERSION",
    "STAGES",
    "STAGE_POST_ALLOCATION",
    "STAGE_POST_ALLOCATION_AFTER_ALIASES",
    "STAGE_POST_ALLOCATION_CONTEXT",
    "STAGE_PRE_CONTRACT",
    "STAGE_RENDER",
    "SeatSectionSourceV1",
    "SeatSourceBundleEntryV1",
    "SeatSourceBundleV1",
    "SeatSourceError",
    "SectionSourceReceiptV1",
    "SectionSourceRequestV1",
    "SectionSourceResultV1",
    "SourceAssemblyV1",
    "apply_post_allocation",
    "assemble_sources",
    "ensure_sources_seeded",
    "register_seat_source_bundle",
    "register_section_source",
    "resolve_seat_source_bundle",
    "resolve_section_source",
    "seat_source_bundle_ids",
    "section_source_ids",
]
