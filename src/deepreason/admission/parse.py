"""The deterministic admission pipeline: fingerprint, extract, segment, mint.

Every stage is a pure function of the input bytes and the frozen constants
below.  No model, no network, no clock, no environment reads.  Media types
are decided by content sniffing, never by filename.  Admitted text is
untrusted data; nothing here interprets it.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

from deepreason.canonical import sha256_hex
from deepreason.evidence.models import (
    AdmissionBlockV1,
    AdmissionRefusalV1,
    AttachedSourceProvenanceV1,
    AttachedSourceV1,
    EvidenceDossierV2,
)


# A single monotonic identifier covering the sniffing rules, the
# segmentation constants, and the projection formats below.  Any change to
# any of them requires a new version; two parser versions never share a
# dossier digest.
PARSER_VERSION = "admission-parser.v1"

# Frozen segmentation and budget constants of PARSER_VERSION.
MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_BLOCK_BYTES = 4_096
MAX_BLOCKS_PER_SOURCE = 400
MAX_TOTAL_BLOCKS = 4_000
MAX_SOURCES = 1_000
CSV_SNIFF_LINES = 50
CSV_MAX_STAT_COLUMNS = 32
CSV_SAMPLE_ROWS = 10
_HEADING = re.compile(r"^(#{1,6})[ \t]+(?P<title>.+?)[ \t]*#*[ \t]*$")
_TABLE_ROW = re.compile(r"^[ \t]*\|.*\|[ \t]*$")

# Content signatures for adapter-claimed formats with no registered or
# runnable adapter.  The refusal names the adapter and the extra so an
# unadmittable format is a typed pointer, not a dead end.
_ADAPTER_SIGNATURES: tuple[tuple[bytes, str, str], ...] = (
    (b"%PDF-", "application/pdf", "pdf (install deepreason[admit])"),
    (b"PK\x03\x04", "application/zip-container", "epub (install deepreason[admit])"),
)


class AdmissionError(ValueError):
    """A typed, whole-invocation admission failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class AdmissionInput:
    """One supplied artifact: a locator label plus its exact raw bytes."""

    locator: str
    data: bytes


@dataclass
class AdmissionReport:
    """Operator-facing summary; the dossier itself is the durable record."""

    dossier_digest: str = ""
    source_count: int = 0
    block_counts: dict[str, int] = field(default_factory=dict)
    tier_counts: dict[str, int] = field(default_factory=dict)
    refusals: list[dict] = field(default_factory=list)


def sniff_media_type(data: bytes) -> tuple[str, str | None]:
    """Return (media_type, adapter_hint) from content alone.

    ``adapter_hint`` is set when the format belongs to a plugin adapter;
    the core parser refuses it by name.  Text subtypes are decided on the
    strict-UTF-8 decoded text: CSV/TSV first (structure), then markdown
    (markers), then plain text.
    """

    for signature, media_type, adapter in _ADAPTER_SIGNATURES:
        if data.startswith(signature):
            return media_type, adapter
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "application/octet-stream", None
    if "\x00" in text:
        # NUL bytes decode as UTF-8 but never occur in admissible text.
        return "application/octet-stream", None
    lines = [line for line in text.split("\n") if line.strip()][:CSV_SNIFF_LINES]
    for delimiter, media_type in (("\t", "text/tab-separated-values"), (",", "text/csv")):
        if len(lines) >= 2:
            widths = set()
            parseable = True
            for line in lines:
                try:
                    row = next(csv.reader(io.StringIO(line), delimiter=delimiter))
                except (csv.Error, StopIteration):
                    parseable = False
                    break
                widths.add(len(row))
            if parseable and widths == {next(iter(widths))} and next(iter(widths)) >= 2:
                return media_type, None
    if any(_HEADING.match(line) for line in text.split("\n")):
        return "text/markdown", None
    return "text/plain", None


def _line_offsets(data: bytes) -> list[int]:
    """Byte offset of each line start; lines split on b'\\n' exactly."""

    offsets = [0]
    for index, byte in enumerate(data):
        if byte == 0x0A:
            offsets.append(index + 1)
    return offsets


def _mint_span_block(
    *,
    data: bytes,
    source_sha256: str,
    kind: str,
    start: int,
    end: int,
    title: str | None,
) -> AdmissionBlockV1:
    text = data[start:end].decode("utf-8")
    return AdmissionBlockV1.create(
        parser_version=PARSER_VERSION,
        source_sha256=source_sha256,
        kind=kind,
        tier="evidence",
        span_start=start,
        span_end=end,
        text_sha256=sha256_hex(text.encode("utf-8")),
        title=title,
    )


def _segment_text(
    data: bytes, source_sha256: str, *, markdown: bool
) -> list[AdmissionBlockV1]:
    """Heading-aware paragraph segmentation with exact byte spans.

    Segmentation walks physical lines.  A run of non-blank lines is one
    paragraph candidate; consecutive pipe-table lines form a table
    candidate; a markdown heading closes the current run, mints a
    ``section`` boundary title, and titles following blocks.  Runs are
    accumulated up to MAX_BLOCK_BYTES and never split mid-line.
    """

    text = data.decode("utf-8")
    lines = text.split("\n")
    offsets = _line_offsets(data)

    def line_span(first: int, last: int) -> tuple[int, int]:
        start = offsets[first]
        end = (
            offsets[last + 1] - 1
            if last + 1 < len(offsets)
            else len(data)
        )
        return start, max(end, start + 1)

    blocks: list[AdmissionBlockV1] = []
    title: str | None = None
    run_start: int | None = None
    run_kind = "paragraph"

    def close_run(last_line: int) -> None:
        nonlocal run_start
        if run_start is None:
            return
        start, end = line_span(run_start, last_line)
        if data[start:end].strip():
            span_start = start
            while span_start < end:
                span_end = min(span_start + MAX_BLOCK_BYTES, end)
                if span_end < end:
                    newline = data.rfind(b"\n", span_start + 1, span_end)
                    if newline > span_start:
                        span_end = newline
                blocks.append(
                    _mint_span_block(
                        data=data,
                        source_sha256=source_sha256,
                        kind=run_kind,
                        start=span_start,
                        end=span_end,
                        title=title,
                    )
                )
                span_start = span_end
        run_start = None

    for index, line in enumerate(lines):
        heading = _HEADING.match(line) if markdown else None
        is_table = bool(_TABLE_ROW.match(line)) if markdown else False
        if heading is not None:
            close_run(index - 1)
            title = heading.group("title")[:256] or None
            start, end = line_span(index, index)
            blocks.append(
                _mint_span_block(
                    data=data,
                    source_sha256=source_sha256,
                    kind="section",
                    start=start,
                    end=end,
                    title=title,
                )
            )
            continue
        if not line.strip():
            close_run(index - 1)
            continue
        kind = "table" if is_table else "paragraph"
        if run_start is None:
            run_start = index
            run_kind = kind
        elif kind != run_kind:
            close_run(index - 1)
            run_start = index
            run_kind = kind
    close_run(len(lines) - 1)
    return blocks


def _format_number(value: float | int) -> str:
    if isinstance(value, int):
        return str(value)
    return repr(value)


def _csv_projections(
    data: bytes, source_sha256: str, delimiter: str
) -> list[AdmissionBlockV1]:
    """Deterministic schema, per-column statistics, and head-sample blocks."""

    text = data.decode("utf-8")
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    if not rows:
        return []
    header, body = rows[0], rows[1:]
    columns = len(header)

    def column_values(index: int) -> list[str]:
        return [row[index] if index < len(row) else "" for row in body]

    def dtype_of(values: list[str]) -> str:
        non_null = [item for item in values if item.strip()]
        if not non_null:
            return "empty"
        try:
            for item in non_null:
                int(item)
            return "int"
        except ValueError:
            pass
        try:
            for item in non_null:
                float(item)
            return "float"
        except ValueError:
            return "text"

    schema_lines = [f"columns: {columns}", f"rows: {len(body)}"]
    stats_lines: list[str] = []
    for index in range(min(columns, CSV_MAX_STAT_COLUMNS)):
        values = column_values(index)
        non_null = [item for item in values if item.strip()]
        dtype = dtype_of(values)
        name = header[index]
        schema_lines.append(
            f"column {index}: name={name!r} dtype={dtype} "
            f"nulls={len(values) - len(non_null)}"
        )
        if dtype in {"int", "float"}:
            numbers = sorted(
                int(item) if dtype == "int" else float(item) for item in non_null
            )
            middle = len(numbers) // 2
            median = (
                numbers[middle]
                if len(numbers) % 2
                else (numbers[middle - 1] + numbers[middle]) / 2
            )
            stats_lines.append(
                f"column {index} ({name!r}): count={len(numbers)} "
                f"min={_format_number(numbers[0])} "
                f"max={_format_number(numbers[-1])} "
                f"median={_format_number(median)}"
            )
        else:
            distinct = sorted(set(non_null))
            preview = ", ".join(repr(item[:64]) for item in distinct[:8])
            stats_lines.append(
                f"column {index} ({name!r}): count={len(non_null)} "
                f"distinct={len(distinct)} values=[{preview}]"
            )
    if columns > CSV_MAX_STAT_COLUMNS:
        schema_lines.append(
            f"(+{columns - CSV_MAX_STAT_COLUMNS} columns beyond the "
            "frozen statistics ceiling)"
        )

    def projection_block(kind: str, lines: list[str]) -> AdmissionBlockV1:
        body_text = "\n".join(lines)[:MAX_BLOCK_BYTES]
        return AdmissionBlockV1.create(
            parser_version=PARSER_VERSION,
            source_sha256=source_sha256,
            kind=kind,
            tier="evidence",
            span_start=0,
            span_end=len(data),
            text_sha256=sha256_hex(body_text.encode("utf-8")),
            text=body_text,
            title=None,
        )

    blocks = [
        projection_block("csv_schema", schema_lines),
        projection_block("csv_stats", stats_lines),
    ]
    offsets = _line_offsets(data)
    sample_rows = min(CSV_SAMPLE_ROWS + 1, len(offsets) - 1, len(rows))
    if sample_rows >= 1:
        end = (
            offsets[sample_rows] - 1
            if sample_rows < len(offsets)
            else len(data)
        )
        if end > 0:
            blocks.append(
                _mint_span_block(
                    data=data,
                    source_sha256=source_sha256,
                    kind="csv_sample",
                    start=0,
                    end=end,
                    title=None,
                )
            )
    return blocks


def _first_heading(data: bytes) -> str | None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    for line in text.split("\n"):
        heading = _HEADING.match(line)
        if heading is not None:
            return heading.group("title")[:256] or None
    return None


def _adapter_blocks(
    manifest,
    data: bytes,
    digest: str,
) -> list[AdmissionBlockV1]:
    """Run one registered adapter in its sandbox and mint tier-capped blocks."""

    from deepreason.admission.adapters import run_adapter

    result = run_adapter(manifest, data)
    blocks: list[AdmissionBlockV1] = []
    for wire in result.blocks:
        blocks.append(
            AdmissionBlockV1.create(
                parser_version=PARSER_VERSION,
                source_sha256=digest,
                kind="extracted",
                # §3a.3: only exact_spans admits to the evidence tier; the
                # extracted kind itself refuses evidence, so any adapter
                # below exact fidelity lands here, capped at workshop.
                tier="workshop",
                span_start=0,
                span_end=len(data),
                text_sha256=sha256_hex(wire.text.encode("utf-8")),
                text=wire.text,
                title=wire.title,
            )
        )
    return blocks


def admit_sources(
    inputs: list[AdmissionInput],
    *,
    problem_ref: str,
    provenance: AttachedSourceProvenanceV1,
    allow_partial: bool = False,
    adapters: tuple = (),
) -> tuple[EvidenceDossierV2, AdmissionReport]:
    """Run the full pipeline and compile one frozen EvidenceDossierV2.

    Refusals are per-source: one unadmittable input does not sink the
    corpus, but its absence is a typed record inside the dossier.  A
    breach of a block budget refuses the source unless ``allow_partial``,
    in which case the bounded prefix is admitted and the truncation is
    recorded — never silent.
    """

    if not inputs:
        raise AdmissionError("ADMISSION_NO_SOURCES", "no inputs were supplied")
    if len(inputs) > MAX_SOURCES:
        raise AdmissionError(
            "ADMISSION_TOTAL_TOO_LARGE", f"more than {MAX_SOURCES} sources"
        )

    sources: dict[str, AttachedSourceV1] = {}
    blocks: list[AdmissionBlockV1] = []
    refusals: list[AdmissionRefusalV1] = []
    adapter_bindings: list = []
    admitted_bytes = 0

    def refuse(code: str, detail: str, *, digest: str | None, locator: str) -> None:
        refusals.append(
            AdmissionRefusalV1(
                code=code,
                detail=detail[:2_048],
                source_sha256=digest,
                source_locator=locator[:4_096],
            )
        )

    for item in inputs:
        data = item.data
        digest = sha256_hex(data) if data else None
        if not data:
            refuse(
                "ADMISSION_SOURCE_EMPTY",
                "source is empty",
                digest=None,
                locator=item.locator,
            )
            continue
        assert digest is not None
        if digest in sources:
            continue
        if len(data) > MAX_SOURCE_BYTES:
            refuse(
                "ADMISSION_SOURCE_TOO_LARGE",
                f"{len(data)} bytes exceeds the {MAX_SOURCE_BYTES} ceiling",
                digest=digest,
                locator=item.locator,
            )
            continue
        if admitted_bytes + len(data) > MAX_TOTAL_BYTES:
            refuse(
                "ADMISSION_TOTAL_TOO_LARGE",
                "admitting this source would exceed the total byte ceiling",
                digest=digest,
                locator=item.locator,
            )
            continue
        from deepreason.admission.adapters import AdapterError, adapter_for

        media_type, adapter_hint = sniff_media_type(data)
        adapter_binding = None
        manifest = adapter_for(data, injected=tuple(adapters))
        if manifest is not None:
            try:
                source_blocks = _adapter_blocks(manifest, data, digest)
            except AdapterError as error:
                refuse(
                    "ADMISSION_MEDIA_UNSUPPORTED",
                    str(error),
                    digest=digest,
                    locator=item.locator,
                )
                continue
            media_type = manifest.media_type
            adapter_binding = manifest
        elif adapter_hint is not None:
            refuse(
                "ADMISSION_MEDIA_UNSUPPORTED",
                f"{media_type} requires the {adapter_hint} adapter",
                digest=digest,
                locator=item.locator,
            )
            continue
        elif media_type == "application/octet-stream":
            refuse(
                "ADMISSION_SOURCE_UNREADABLE",
                "bytes are not strict UTF-8 and no adapter claims them",
                digest=digest,
                locator=item.locator,
            )
            continue

        if adapter_binding is not None:
            pass
        elif media_type in {"text/csv", "text/tab-separated-values"}:
            delimiter = "\t" if media_type == "text/tab-separated-values" else ","
            source_blocks = _csv_projections(data, digest, delimiter)
        else:
            source_blocks = _segment_text(
                data, digest, markdown=media_type == "text/markdown"
            )
        if len(source_blocks) > MAX_BLOCKS_PER_SOURCE or (
            len(blocks) + len(source_blocks) > MAX_TOTAL_BLOCKS
        ):
            if not allow_partial:
                refuse(
                    "ADMISSION_BLOCK_BUDGET_EXCEEDED",
                    f"{len(source_blocks)} blocks exceeds the frozen budget; "
                    "re-run with --allow-partial to admit a bounded prefix",
                    digest=digest,
                    locator=item.locator,
                )
                continue
            keep = min(
                MAX_BLOCKS_PER_SOURCE,
                max(0, MAX_TOTAL_BLOCKS - len(blocks)),
            )
            refuse(
                "ADMISSION_BLOCK_BUDGET_EXCEEDED",
                f"admitted the first {keep} of {len(source_blocks)} blocks "
                "under --allow-partial",
                digest=digest,
                locator=item.locator,
            )
            source_blocks = source_blocks[:keep]

        title = _first_heading(data) or f"untitled source {digest[:12]}"
        sources[digest] = AttachedSourceV1(
            id=f"src-{digest[:40]}",
            title=title,
            source_locator=item.locator[:4_096],
            source_class="other",
            media_type=media_type,
            content_ref=digest,
            content_sha256=digest,
            byte_count=len(data),
            provenance=provenance,
        )
        if adapter_binding is not None:
            from deepreason.evidence.models import SourceAdapterBindingV1

            adapter_bindings.append(
                SourceAdapterBindingV1(
                    source_sha256=digest,
                    adapter_id=adapter_binding.adapter_id,
                    adapter_version=adapter_binding.adapter_version,
                    span_fidelity=adapter_binding.span_fidelity,
                )
            )
        blocks.extend(source_blocks)
        admitted_bytes += len(data)

    if not sources and not allow_partial:
        first = refusals[0] if refusals else None
        raise AdmissionError(
            first.code if first else "ADMISSION_NO_SOURCES",
            (first.detail if first else "every supplied source was refused"),
        )

    dossier = EvidenceDossierV2.create(
        problem_ref=problem_ref,
        parser_version=PARSER_VERSION,
        sources=tuple(sorted(sources.values(), key=lambda source: source.id)),
        blocks=tuple(sorted(blocks, key=lambda block: block.id)),
        refusals=tuple(refusals),
        adapters=tuple(
            sorted(adapter_bindings, key=lambda item: item.source_sha256)
        ),
        total_byte_count=admitted_bytes,
        creation_provenance=provenance,
    )
    report = AdmissionReport(
        dossier_digest=dossier.dossier_digest,
        source_count=len(dossier.sources),
    )
    for block in dossier.blocks:
        report.block_counts[block.kind] = report.block_counts.get(block.kind, 0) + 1
        report.tier_counts[block.tier] = report.tier_counts.get(block.tier, 0) + 1
    report.refusals = [
        refusal.model_dump(mode="json", by_alias=True, exclude_none=True)
        for refusal in refusals
    ]
    return dossier, report
