"""First-party EPUB adapter under the identical §3a plugin contract.

EPUB text extraction cannot map extracted text back to exact source byte
spans (content lives in compressed XHTML entries), so this adapter
declares ``approximate`` span fidelity and every block it produces is
capped at the ``workshop`` tier — retrievable and advisory, never
grounding.  Extraction is stdlib-only (zipfile, html.parser,
ElementTree): there is no dependency to miss, but the adapter still runs
inside the same sandbox as every other plugin — purity is enforced, not
attested.
"""

from __future__ import annotations

from html.parser import HTMLParser

from deepreason.admission.adapters import (
    AdapterBlockWireV1,
    AdapterManifestV1,
    AdapterResultWireV1,
)

ADAPTER_ID = "epub"
ADAPTER_VERSION = "epub-adapter.v1"
_MAX_BLOCK_CHARS = 4_096
_MAX_ENTRY_BYTES = 16 * 1024 * 1024
_MAX_BLOCKS = 4_000
_DOCUMENT_SUFFIXES = (".xhtml", ".html", ".htm")
_BREAK_TAGS = frozenset(
    {
        "p",
        "div",
        "li",
        "br",
        "tr",
        "section",
        "article",
        "blockquote",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    }
)
_HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6", "title"})

MANIFEST = AdapterManifestV1(
    adapter_id=ADAPTER_ID,
    adapter_version=ADAPTER_VERSION,
    content_signatures=("504b0304",),  # b"PK\x03\x04"
    media_type="application/epub+zip",
    span_fidelity="approximate",
    requires=None,
    extra_hint="deepreason[admit]",
    entry="deepreason.admission.adapters_epub:extract",
)


class _TextCollector(HTMLParser):
    """Deterministic text and first-heading extraction from one document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pieces: list[str] = []
        self.heading: str | None = None
        self._suppressed = 0
        self._heading_depth = 0
        self._heading_pieces: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._suppressed += 1
        if tag in _HEADING_TAGS and self.heading is None:
            self._heading_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self._suppressed:
            self._suppressed -= 1
        if tag in _HEADING_TAGS and self._heading_depth:
            self._heading_depth -= 1
            if not self._heading_depth and self.heading is None:
                heading = " ".join("".join(self._heading_pieces).split())
                if heading:
                    self.heading = heading[:256]
        if tag in _BREAK_TAGS:
            self.pieces.append("\n")

    def handle_data(self, data):
        if self._suppressed:
            return
        self.pieces.append(data)
        if self._heading_depth:
            self._heading_pieces.append(data)

    def text(self) -> str:
        lines = "".join(self.pieces).splitlines()
        collapsed = [" ".join(line.split()) for line in lines]
        return "\n".join(line for line in collapsed if line)


def _spine_order(archive) -> list[str]:
    """Reading order from the OPF spine; sorted entry names as fallback."""

    import posixpath
    import xml.etree.ElementTree as ElementTree

    documents = sorted(
        name
        for name in archive.namelist()
        if name.lower().endswith(_DOCUMENT_SUFFIXES)
    )
    try:
        container = ElementTree.fromstring(archive.read("META-INF/container.xml"))
        opf_name = next(
            element.get("full-path")
            for element in container.iter()
            if element.tag.endswith("rootfile") and element.get("full-path")
        )
        opf = ElementTree.fromstring(archive.read(opf_name))
        base = posixpath.dirname(opf_name)
        hrefs = {
            element.get("id"): element.get("href")
            for element in opf.iter()
            if element.tag.endswith("item")
        }
        ordered = []
        for element in opf.iter():
            if not element.tag.endswith("itemref"):
                continue
            href = hrefs.get(element.get("idref"))
            if not href:
                continue
            name = posixpath.normpath(posixpath.join(base, href)) if base else href
            if name in documents:
                ordered.append(name)
        remainder = [name for name in documents if name not in ordered]
        return [*ordered, *remainder]
    except Exception:  # noqa: BLE001 - a malformed spine degrades to name order
        return documents


def extract(data: bytes) -> AdapterResultWireV1:
    """Deterministically extract per-document text blocks from one EPUB."""

    import io
    import zipfile

    archive = zipfile.ZipFile(io.BytesIO(data))
    mimetype = archive.read("mimetype").decode("ascii", errors="strict").strip()
    if mimetype != "application/epub+zip":
        raise ValueError("container is a zip archive but not an EPUB")

    blocks: list[AdapterBlockWireV1] = []
    for index, name in enumerate(_spine_order(archive), start=1):
        if archive.getinfo(name).file_size > _MAX_ENTRY_BYTES:
            continue
        collector = _TextCollector()
        collector.feed(archive.read(name).decode("utf-8", errors="replace"))
        text = collector.text().strip()
        if not text:
            continue
        title = collector.heading or f"document {index}"
        remaining = text
        while remaining and len(blocks) < _MAX_BLOCKS:
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
