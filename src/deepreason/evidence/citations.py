"""Citation checks (admission §4): candidate claims about admitted blocks.

A conjecture citing admitted evidence names dossier block ids and may carry
quotes. Nothing here is trusted on arrival: every citation resolves against
the frozen dossier and every quote is checked against the block's canonical
text, with whitespace folded on both sides so that the source author's line
wrapping cannot decide the verdict while every non-whitespace character must
still appear, contiguously and in order. The result is one durable, typed
check per citation — verification and failure are both recorded outcomes,
never silence.
"""

from __future__ import annotations

import hashlib
import re
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


_WHITESPACE = re.compile(r"\s+")


def _whitespace_folded(text: str) -> str:
    """Collapse every run of whitespace to one space, and strip.

    Admitted text is the source author's bytes, carrying their hard line
    wrapping and any alignment padding; a model reproduces the passage as
    running text. Layout is not part of what a citation claims, so both
    sides are folded before the fallback comparison. Folding never
    inserts whitespace where the source had none, so a quote that joins
    words the source separated still fails.
    """

    return _WHITESPACE.sub(" ", text).strip()


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
    refs,
    dossier: EvidenceDossier | None,
    blobs,
    *,
    extra_blocks=(),
    dossiers=(),
) -> tuple[EvidenceCitationCheckV1, ...]:
    """Check every claimed citation of one candidate; one outcome per claim.

    ``refs`` are ``EvidenceRefClaimV1`` values from an admitted candidate;
    ``dossier`` is the run-bound dossier (or None when no dossier is bound);
    ``blobs`` resolves admitted source bytes by content digest;
    ``extra_blocks`` extends the citable universe with blocks admitted
    mid-run under capability authority (consumed research fetches) — the
    same content-addressed identity and quote byte-checks apply.
    ``dossiers`` names every dossier bound to the run when amendment epochs
    have made evidence cumulative; each was loaded and checked against its
    own digest, so a citation verified against the first dossier verifies
    identically after any number of later ones.
    """

    checks: list[EvidenceCitationCheckV1] = []
    bound = tuple(dossiers) or ((dossier,) if dossier is not None else ())
    blocks: list[AdmissionBlockV1] = []
    known: set[str] = set()
    for item in bound:
        for block in getattr(item, "blocks", ()):
            if block.id not in known:
                known.add(block.id)
                blocks.append(block)
    for block in extra_blocks:
        if block.id not in known:
            known.add(block.id)
            blocks.append(block)
    blocks = tuple(blocks)
    for ref in refs:
        quoted = ref.quote is not None
        quote_detail = ""
        if not bound and not extra_blocks:
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
            folded_quote = _whitespace_folded(ref.quote)
            if ref.quote.encode("utf-8") in canonical.encode("utf-8"):
                quote_detail = "citation resolved and quote byte-verified"
            # The emptiness guard is load-bearing: a quote of only whitespace
            # folds to "", which is a sub-span of every block's folded text.
            elif folded_quote and folded_quote in _whitespace_folded(canonical):
                quote_detail = (
                    "citation resolved and quote verified against the block's "
                    "canonical text after folding whitespace; the admitted line "
                    "breaks and alignment are not required to be reproduced"
                )
            else:
                checks.append(
                    EvidenceCitationCheckV1(
                        code=EVIDENCE_QUOTE_MISMATCH,
                        block_ref=ref.block,
                        block_id=block.id,
                        quoted=True,
                        detail=(
                            "quote is not a sub-span of the block's canonical "
                            "text under any rendering of its whitespace"
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
                    quote_detail
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
