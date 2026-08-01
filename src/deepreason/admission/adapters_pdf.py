"""First-party PDF adapter: proves the §3a plugin contract on itself.

PDF text extraction cannot map extracted text back to exact source byte
spans, so this adapter declares ``approximate`` span fidelity and every
block it produces is capped at the ``workshop`` tier — retrievable and
advisory, never grounding.  The dependency lives behind the
``deepreason[admit]`` extra; a missing dependency is a typed refusal
naming the extra, never a crash.
"""

from __future__ import annotations

from deepreason.admission.adapters import (
    AdapterBlockWireV1,
    AdapterManifestV1,
    AdapterResultWireV1,
)

ADAPTER_ID = "pdf"
ADAPTER_VERSION = "pdf-adapter.v1"
_MAX_BLOCK_CHARS = 4_096

MANIFEST = AdapterManifestV1(
    adapter_id=ADAPTER_ID,
    adapter_version=ADAPTER_VERSION,
    content_signatures=("255044462d",),  # b"%PDF-"
    media_type="application/pdf",
    span_fidelity="approximate",
    requires="pypdf",
    extra_hint="deepreason[admit]",
    entry="deepreason.admission.adapters_pdf:extract",
)


def extract(data: bytes) -> AdapterResultWireV1:
    """Deterministically extract per-page text blocks from one PDF."""

    import io

    from pypdf import PdfReader

    blocks: list[AdapterBlockWireV1] = []
    reader = PdfReader(io.BytesIO(data))
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        title = f"page {page_number}"
        remaining = text
        while remaining:
            piece = remaining[:_MAX_BLOCK_CHARS]
            if len(remaining) > _MAX_BLOCK_CHARS:
                split = piece.rfind("\n")
                if split > 0:
                    piece = piece[:split]
            blocks.append(AdapterBlockWireV1(text=piece, title=title))
            remaining = remaining[len(piece) :].lstrip("\n")
    return AdapterResultWireV1(
        adapter_id=ADAPTER_ID,
        adapter_version=ADAPTER_VERSION,
        blocks=tuple(blocks),
    )
