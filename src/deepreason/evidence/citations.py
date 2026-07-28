"""Citation checks (admission §4): candidate claims about admitted blocks.

A conjecture citing admitted evidence names dossier block ids and may carry
quotes. Nothing here is trusted on arrival: every citation resolves against
the frozen dossier and every quote is byte-checked against the block's
canonical text. The result is one durable, typed check per citation —
verification and failure are both recorded outcomes, never silence.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from deepreason.evidence.models import AdmissionBlockV1, EvidenceDossier


EVIDENCE_CITATION_VERIFIED = "EVIDENCE_CITATION_VERIFIED"
EVIDENCE_REFS_UNBOUND = "EVIDENCE_REFS_UNBOUND"
EVIDENCE_REF_UNKNOWN_BLOCK = "EVIDENCE_REF_UNKNOWN_BLOCK"
EVIDENCE_REF_AMBIGUOUS = "EVIDENCE_REF_AMBIGUOUS"
EVIDENCE_REF_TIER_INELIGIBLE = "EVIDENCE_REF_TIER_INELIGIBLE"
EVIDENCE_QUOTE_MISMATCH = "EVIDENCE_QUOTE_MISMATCH"
EVIDENCE_BLOCK_UNRECOVERABLE = "EVIDENCE_BLOCK_UNRECOVERABLE"


class CitationIntegrityError(ValueError):
    """A block's canonical text cannot be recovered as recorded."""


class EvidenceCitationCheckV1(BaseModel):
    """The deterministic outcome of checking one claimed citation."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_: Literal["evidence-citation-check.v1"] = Field(
        "evidence-citation-check.v1", alias="schema"
    )
    code: Literal[
        "EVIDENCE_CITATION_VERIFIED",
        "EVIDENCE_REFS_UNBOUND",
        "EVIDENCE_REF_UNKNOWN_BLOCK",
        "EVIDENCE_REF_AMBIGUOUS",
        "EVIDENCE_REF_TIER_INELIGIBLE",
        "EVIDENCE_QUOTE_MISMATCH",
        "EVIDENCE_BLOCK_UNRECOVERABLE",
    ]
    block_ref: str = Field(min_length=1, max_length=64)
    block_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    quoted: bool = False
    detail: str = Field(min_length=1, max_length=512)

    @property
    def verified(self) -> bool:
        return self.code == EVIDENCE_CITATION_VERIFIED


def canonical_block_text(block: AdmissionBlockV1, source_bytes: bytes) -> str:
    """Recover a block's canonical text, verifying it against the dossier.

    Projection and extracted blocks inline their text (already pinned by the
    block's identity); span blocks are the exact byte slice of the admitted
    source. Any divergence from the recorded ``text_sha256`` is an integrity
    error, never a silently different text.
    """

    if block.text is not None:
        return block.text
    window = source_bytes[block.span_start : block.span_end]
    if hashlib.sha256(window).hexdigest() != block.text_sha256:
        raise CitationIntegrityError(
            f"block {block.id[:12]} span bytes do not match the admitted text digest"
        )
    try:
        return window.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CitationIntegrityError(
            f"block {block.id[:12]} span bytes are not valid UTF-8"
        ) from error


def _resolve(
    reference: str, blocks: tuple[AdmissionBlockV1, ...]
) -> tuple[AdmissionBlockV1 | None, str | None]:
    exact = [block for block in blocks if block.id == reference]
    if exact:
        return exact[0], None
    matched = [block for block in blocks if block.id.startswith(reference)]
    if not matched:
        return None, EVIDENCE_REF_UNKNOWN_BLOCK
    if len(matched) > 1:
        return None, EVIDENCE_REF_AMBIGUOUS
    return matched[0], None


def check_candidate_citations(
    refs, dossier: EvidenceDossier | None, blobs, *, extra_blocks=()
) -> tuple[EvidenceCitationCheckV1, ...]:
    """Check every claimed citation of one candidate; one outcome per claim.

    ``refs`` are ``EvidenceRefClaimV1`` values from an admitted candidate;
    ``dossier`` is the run-bound dossier (or None when no dossier is bound);
    ``blobs`` resolves admitted source bytes by content digest;
    ``extra_blocks`` extends the citable universe with blocks admitted
    mid-run under capability authority (consumed research fetches) — the
    same content-addressed identity and quote byte-checks apply.
    """

    checks: list[EvidenceCitationCheckV1] = []
    blocks = (
        tuple(getattr(dossier, "blocks", ()) if dossier is not None else ())
        + tuple(extra_blocks)
    )
    for ref in refs:
        quoted = ref.quote is not None
        if dossier is None and not extra_blocks:
            checks.append(
                EvidenceCitationCheckV1(
                    code=EVIDENCE_REFS_UNBOUND,
                    block_ref=ref.block,
                    quoted=quoted,
                    detail="candidate cites evidence but no dossier is bound to this run",
                )
            )
            continue
        block, failure = _resolve(ref.block, blocks)
        if block is None:
            assert failure is not None
            checks.append(
                EvidenceCitationCheckV1(
                    code=failure,
                    block_ref=ref.block,
                    quoted=quoted,
                    detail=(
                        "cited reference matches more than one admitted block"
                        if failure == EVIDENCE_REF_AMBIGUOUS
                        else "cited reference matches no admitted block"
                    ),
                )
            )
            continue
        if block.tier != "evidence":
            checks.append(
                EvidenceCitationCheckV1(
                    code=EVIDENCE_REF_TIER_INELIGIBLE,
                    block_ref=ref.block,
                    block_id=block.id,
                    quoted=quoted,
                    detail=(
                        f"block is admitted at the {block.tier} tier and cannot "
                        "ground a citation"
                    ),
                )
            )
            continue
        if ref.quote is not None:
            try:
                source_bytes = (
                    b"" if block.text is not None else blobs.get(block.source_sha256)
                )
                canonical = canonical_block_text(block, source_bytes)
            except (CitationIntegrityError, KeyError, OSError):
                checks.append(
                    EvidenceCitationCheckV1(
                        code=EVIDENCE_BLOCK_UNRECOVERABLE,
                        block_ref=ref.block,
                        block_id=block.id,
                        quoted=True,
                        detail="the cited block's canonical text cannot be recovered as admitted",
                    )
                )
                continue
            if ref.quote.encode("utf-8") not in canonical.encode("utf-8"):
                checks.append(
                    EvidenceCitationCheckV1(
                        code=EVIDENCE_QUOTE_MISMATCH,
                        block_ref=ref.block,
                        block_id=block.id,
                        quoted=True,
                        detail=(
                            "quote is not an exact byte sub-span of the block's "
                            "canonical text"
                        ),
                    )
                )
                continue
        checks.append(
            EvidenceCitationCheckV1(
                code=EVIDENCE_CITATION_VERIFIED,
                block_ref=ref.block,
                block_id=block.id,
                quoted=quoted,
                detail=(
                    "citation resolved and quote byte-verified"
                    if quoted
                    else "citation resolved to an admitted evidence block"
                ),
            )
        )
    return tuple(checks)


__all__ = [
    "EVIDENCE_BLOCK_UNRECOVERABLE",
    "EVIDENCE_CITATION_VERIFIED",
    "EVIDENCE_QUOTE_MISMATCH",
    "EVIDENCE_REF_AMBIGUOUS",
    "EVIDENCE_REF_TIER_INELIGIBLE",
    "EVIDENCE_REF_UNKNOWN_BLOCK",
    "EVIDENCE_REFS_UNBOUND",
    "CitationIntegrityError",
    "EvidenceCitationCheckV1",
    "canonical_block_text",
    "check_candidate_citations",
]
