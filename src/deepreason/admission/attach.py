"""One shared local-file admission path for every end-user surface.

The CLI (``admit``, ``reason --attach``), the MCP facade, and the local
web app all admit user-supplied files through this exact function, so a
document behaves identically no matter which door it entered by: the
same deterministic parser, the same typed refusals, the same managed
store, and the same dossier digest for the same bytes and question.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from deepreason.admission.parse import (
    AdmissionError,
    AdmissionInput,
    AdmissionReport,
    admit_sources,
)
from deepreason.admission.store import admission_store
from deepreason.evidence.models import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV2,
)

MAX_ATTACHMENT_FILES = 64


@dataclass(frozen=True)
class AdmittedAttachments:
    """The durable outcome of admitting one attachment set for a question."""

    dossier: EvidenceDossierV2
    report: AdmissionReport

    @property
    def dossier_digest(self) -> str:
        return self.dossier.dossier_digest

    def summary(self) -> dict:
        """A bounded, secret-free description safe for any caller surface."""

        return {
            "evidence_dossier_digest": self.dossier.dossier_digest,
            "sources_admitted": self.report.source_count,
            "blocks": dict(self.report.block_counts),
            "tiers": dict(self.report.tier_counts),
            "refusals": list(self.report.refusals),
        }


def collect_attachment_inputs(paths) -> list[AdmissionInput]:
    """Deterministically expand files and directories into admission inputs.

    An unreadable or missing path is a typed whole-invocation failure —
    silently admitting a subset of what the user pointed at would
    misrepresent the evidence base.
    """

    inputs: list[AdmissionInput] = []
    for supplied in paths:
        path = Path(supplied)
        if path.is_dir():
            candidates = sorted(item for item in path.rglob("*") if item.is_file())
            if not candidates:
                raise AdmissionError(
                    "ADMISSION_PATH_UNAVAILABLE",
                    f"directory contains no files: {supplied}",
                )
        elif path.is_file():
            candidates = [path]
        else:
            raise AdmissionError(
                "ADMISSION_PATH_UNAVAILABLE", f"no such file: {supplied}"
            )
        for item in candidates:
            try:
                inputs.append(
                    AdmissionInput(locator=str(item), data=item.read_bytes())
                )
            except OSError as error:
                raise AdmissionError(
                    "ADMISSION_PATH_UNAVAILABLE", f"{item}: {error}"
                ) from error
    if len(inputs) > MAX_ATTACHMENT_FILES:
        raise AdmissionError(
            "ADMISSION_TOO_MANY_SOURCES",
            f"{len(inputs)} files exceed the {MAX_ATTACHMENT_FILES}-file "
            "attachment ceiling",
        )
    return inputs


def admit_attachments(
    question: str,
    inputs: list[AdmissionInput],
    *,
    supplied_by: str,
    allow_partial: bool = False,
) -> AdmittedAttachments:
    """Admit prepared inputs for one exact question and store the dossier.

    The dossier's ``problem_ref`` is derived from the question the same
    way run preparation derives it, so the minted digest binds cleanly
    into that question's run identity and no other.
    """

    from deepreason.preparation import _question_digest

    if not question or not question.strip():
        raise AdmissionError(
            "ADMISSION_PROBLEM_REQUIRED",
            "attachments must be admitted for one exact question",
        )
    if not inputs:
        raise AdmissionError(
            "ADMISSION_NO_SOURCES", "supply at least one file to attach"
        )
    provenance = AttachedSourceProvenanceV1(
        supplied_by=supplied_by,
        acquisition_method="operator-supplied local files",
        note=None,
    )
    dossier, report = admit_sources(
        inputs,
        problem_ref=f"question-{_question_digest(question)[:32]}",
        provenance=provenance,
        allow_partial=allow_partial,
    )
    import hashlib

    by_digest = {
        hashlib.sha256(item.data).hexdigest(): item.data
        for item in inputs
        if item.data
    }
    admission_store().save(
        dossier,
        {
            source.content_sha256: by_digest[source.content_sha256]
            for source in dossier.sources
        },
    )
    return AdmittedAttachments(dossier=dossier, report=report)


def admit_attachment_paths(
    question: str,
    paths,
    *,
    supplied_by: str,
    allow_partial: bool = False,
) -> AdmittedAttachments:
    """Expand paths and admit them for one question in a single step."""

    return admit_attachments(
        question,
        collect_attachment_inputs(paths),
        supplied_by=supplied_by,
        allow_partial=allow_partial,
    )


__all__ = [
    "MAX_ATTACHMENT_FILES",
    "AdmittedAttachments",
    "admit_attachment_paths",
    "admit_attachments",
    "collect_attachment_inputs",
]
