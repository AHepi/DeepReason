"""Reader-facing findings report, rendered deterministically from the record.

Everything an end user needs to know — what was established, what remains
contested, what is hedged or unverified, and what evidence was fetched,
refused, cited, or wasted — already exists in the append-only log as typed
records. This module translates that record into plain language with no
model in the loop, so the report can never claim more than the record
holds. Hashes are demoted to bracketed footnote handles.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


_CLAIM_CHARS = 600


def _clip(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= _CLAIM_CHARS:
        return text
    return text[:_CLAIM_CHARS] + "…"


def _claim_text(artifact) -> str:
    content = artifact.content_ref.removeprefix("inline:")
    try:
        value = json.loads(content)
    except (TypeError, ValueError):
        return _clip(str(content))
    if isinstance(value, dict):
        # Process bookkeeping is not a position a reader should weigh.
        if "school_policy" in value or value.get("schema") in {
            "attached-source-record.v1",
        }:
            return ""
        for key in ("claim", "content", "statement"):
            text = value.get(key)
            if isinstance(text, str) and text.strip():
                return _clip(text)
    return _clip(str(content))


def _atomic_write(path: Path, body: str) -> None:
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(body, encoding="utf-8")
    os.replace(temporary, path)


def write_findings_report(root: Path | str) -> Path | None:
    """Write FINDINGS.md beside the run's other reader files.

    Purely replay-derived; returns None (writing nothing) when the root is
    not a bound v5/v6 run. Never raises into its caller — a reporting
    failure must not fail a run's publication.
    """

    from deepreason.capabilities.models import (
        ResearchConsumptionV1,
        ResearchExecutionReceiptV1,
    )
    from deepreason.harness import Harness
    from deepreason.ontology import Status
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    root = Path(root)
    try:
        manifest = load_run_manifest(root / MANIFEST_NAME)
        if manifest.schema_version not in {5, 6}:
            return None
        harness = Harness(root, read_only=True)
    except Exception:  # noqa: BLE001 - reporting never fails publication
        return None

    lines: list[str] = ["# Findings", ""]
    try:
        from deepreason.evidence.state import load_run_input

        question = load_run_input(root).problem.description
        lines += ["## Question", "", question, ""]
    except Exception:  # noqa: BLE001
        pass

    # Evidence bookkeeping (candidate evidence carrying fetched text and
    # its reliability nodes) is provenance, not a position to weigh.
    evidence_bookkeeping: set[str] = set()
    for consumption in harness.capability_state.consumptions.values():
        if not isinstance(consumption, ResearchConsumptionV1):
            continue
        for evidence_ref in consumption.evidence_refs:
            evidence_bookkeeping.add(evidence_ref)
            evidence = harness.state.artifacts.get(evidence_ref)
            if evidence is not None:
                evidence_bookkeeping.update(
                    ref.target for ref in evidence.interface.refs
                )

    accepted: list[tuple[str, str]] = []
    refuted: list[tuple[str, str]] = []
    for artifact_id, artifact in harness.state.artifacts.items():
        if artifact_id in evidence_bookkeeping:
            continue
        text = _claim_text(artifact)
        if not text:
            continue
        status = harness.state.status.get(artifact_id)
        if status == Status.ACCEPTED:
            accepted.append((artifact_id, text))
        elif status == Status.REFUTED:
            refuted.append((artifact_id, text))

    lines += ["## Positions the record accepts", ""]
    if not accepted:
        lines += ["No formally accepted position survived criticism.", ""]
    else:
        if len(accepted) > 1:
            lines += [
                f"{len(accepted)} positions stand formally accepted. Where "
                "they answer the same question differently they are "
                "unresolved rivals: the record deliberately preserves the "
                "disagreement rather than merging it.",
                "",
            ]
        for artifact_id, text in accepted:
            lines.append(f"- {text} `[{artifact_id[:12]}]`")
        lines.append("")
    if refuted:
        lines += ["## Positions the record refuted", ""]
        for artifact_id, text in refuted:
            lines.append(f"- {text} `[{artifact_id[:12]}]`")
        lines.append("")

    # The latest composed view, when one exists, in its own words.
    try:
        from deepreason.application.bridge import load_snapshot

        snapshot = load_snapshot(root)
        output = snapshot.output
        if output is not None:
            lines += [
                "## Latest composed view",
                "",
                f"Resolution: **{output.resolution.value}** "
                f"(composed at formal sequence {snapshot.terminal.formal_seq}; "
                "supersedable — no answer is final).",
                "",
            ]
            for section in output.sections:
                lines.append(f"> {' '.join(section.text.split())}")
            if output.resolution_reason:
                lines += ["", f"Why not fully answered: {output.resolution_reason}"]
            unresolved = getattr(output, "unresolved_items", ()) or ()
            if unresolved:
                lines += ["", "Open items the composer refused to smooth over:", ""]
                for item in unresolved:
                    lines.append(f"- {getattr(item, 'description', item)}")
            lines.append("")
    except Exception:  # noqa: BLE001 - a bridge-free run still reports
        pass

    events = list(harness.log.read())
    citation_counts: dict[str, int] = {}
    for event in events:
        signal = str(event.inputs[0]) if event.inputs else ""
        if signal.startswith("evidence-citation:"):
            code = signal.split(":", 1)[1]
            citation_counts[code] = citation_counts.get(code, 0) + 1
    receipts = [
        receipt
        for receipt in harness.capability_state.receipts.values()
        if isinstance(receipt, ResearchExecutionReceiptV1)
    ]
    consumptions = [
        consumption
        for consumption in harness.capability_state.consumptions.values()
        if isinstance(consumption, ResearchConsumptionV1)
    ]

    hedges: list[str] = []
    for receipt in receipts:
        for attempt in receipt.attempts:
            if attempt.outcome != "FETCHED":
                hedges.append(
                    f"- Fetch refused (`{attempt.outcome}`): {attempt.url} — "
                    "any claim needing this source stayed unverified."
                )
    verified = citation_counts.get("EVIDENCE_CITATION_VERIFIED", 0)
    failed_citations = sum(
        count
        for code, count in citation_counts.items()
        if code != "EVIDENCE_CITATION_VERIFIED"
    )
    if failed_citations:
        detail = ", ".join(
            f"{count}× {code}"
            for code, count in sorted(citation_counts.items())
            if code != "EVIDENCE_CITATION_VERIFIED"
        )
        hedges.append(
            f"- {failed_citations} claimed citation(s) failed their "
            f"deterministic check ({detail}); those groundings are NOT "
            "established."
        )
    if hedges:
        lines += ["## Hedged and unverified", "", *hedges, ""]

    if receipts or consumptions or verified:
        lines += ["## Evidence trail", ""]
        for receipt in receipts:
            for attempt in receipt.attempts:
                if attempt.outcome == "FETCHED":
                    lines.append(
                        f"- Fetched: {attempt.url} "
                        f"({attempt.byte_count} bytes, content "
                        f"`{(attempt.content_sha256 or '')[:12]}`)"
                    )
        for consumption in consumptions:
            lines.append(
                f"- Consumed into {len(consumption.evidence_refs)} candidate "
                "evidence record(s) with byte-checkable citable blocks."
            )
        lines.append(
            f"- Byte-verified citations of admitted evidence: {verified}."
        )
        lines.append("")

    lines += [
        "---",
        "Every statement above is derived from the append-only run record; "
        "nothing was generated by a model for this report. Accepted does "
        "not mean true — it means the position survived recorded criticism "
        "so far, and the run remains continuable.",
        "",
    ]
    target = root / "FINDINGS.md"
    try:
        _atomic_write(target, "\n".join(lines))
    except OSError:
        return None
    return target


__all__ = ["write_findings_report"]
