"""Formal submission binding for E3.1 axiom-domain problems.

A submission is a ``{theorem_name: proof_body}`` mapping — never a full Lean
source file.  The verifiable Lean source is reconstructed SERVER-SIDE from
the immutable stored skeleton: imports, options, the axiom ``class``
declaration, and every theorem statement come ONLY from the skeleton bytes
whose digest the stored :class:`PinnedLeanRequest` pins.  A submitter can
therefore only ever fill proof holes; there is no channel through which it
can restate a target as ``True``, weaken an axiom, add an axiom, or flip a
request option.

Defense in depth: after reconstruction the source is re-parsed and the
non-proof regions are hash-compared against the skeleton's non-proof
regions.  ANY non-proof mutation — e.g. a proof body that escapes its
indented tactic block with column-0 content — is rejected before any
verification is attempted.  ``source_ref`` is computed only after the
reconstructed source passes that comparison, so the pinned request a
verifier sees can only ever point at a skeleton-faithful source.

No Lean toolchain is invoked here; this is the binding layer in front of
kernel verification, not the verifier itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.workloads.formal import PinnedLeanRequest

SKELETON_PLACEHOLDER_MARKER = "E31-SKELETON"

_THEOREM_LINE = re.compile(r"^theorem\s+(\S+)")
_PROOF_HEADER_SUFFIX = ":= by"
_SORRY_TOKEN = re.compile(r"(?<![A-Za-z0-9_'])sorry(?![A-Za-z0-9_'])")


class SubmissionError(ValueError):
    """A submission (or a tampered skeleton) that must not reach a verifier."""


@dataclass(frozen=True)
class SourceRegions:
    """A Lean source split into immutable text and per-theorem proof regions."""

    theorem_names: tuple[str, ...]
    proofs: dict[str, str]
    non_proof_fingerprint: str  # sha256 over the canonical non-proof segments


@dataclass(frozen=True)
class Skeleton:
    """The immutable problem skeleton: pinned bytes plus its parsed regions."""

    source: str
    request: PinnedLeanRequest
    regions: SourceRegions


@dataclass(frozen=True)
class BoundSubmission:
    """A reconstructed, skeleton-faithful source ready for kernel verification."""

    source: str
    source_ref: str
    request: PinnedLeanRequest
    non_proof_fingerprint: str


def split_regions(source: str) -> SourceRegions:
    """Split Lean source into non-proof segments and per-theorem proof regions.

    A proof region starts on the line after a theorem's ``:= by`` header and
    extends over the following lines that are blank or indented; the first
    non-blank column-0 line ends it (matching Lean 4 block structure, where
    column-0 content terminates the tactic block).  Everything else —
    comments, ``universe``/``open`` commands, the class declaration with its
    axioms, and every theorem statement header — is non-proof text.
    """

    lines = source.split("\n")
    names: list[str] = []
    proofs: dict[str, str] = {}
    non_proof_segments: list[Any] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        matched = _THEOREM_LINE.match(line)
        if matched is None:
            non_proof_segments.append(line)
            index += 1
            continue
        name = matched.group(1)
        if name in proofs:
            raise SubmissionError(f"theorem {name!r} declared more than once")
        header = [line]
        index += 1
        while not header[-1].rstrip().endswith(_PROOF_HEADER_SUFFIX):
            if index >= len(lines):
                raise SubmissionError(
                    f"theorem {name!r}: statement never reaches ':= by'"
                )
            header.append(lines[index])
            index += 1
        non_proof_segments.extend(header)
        proof_lines: list[str] = []
        while index < len(lines) and (
            lines[index] == "" or lines[index][0] in (" ", "\t")
        ):
            proof_lines.append(lines[index])
            index += 1
        names.append(name)
        proofs[name] = "\n".join(proof_lines)
        non_proof_segments.append({"proof_hole": name})
    fingerprint = sha256_hex(canonical_json(non_proof_segments))
    return SourceRegions(
        theorem_names=tuple(names),
        proofs=proofs,
        non_proof_fingerprint=fingerprint,
    )


def load_skeleton(source: bytes | str, request: PinnedLeanRequest) -> Skeleton:
    """Bind skeleton bytes to their pinned request; reject any drift.

    The skeleton is only accepted when (a) its bytes hash to the request's
    ``source_ref``, (b) it declares exactly the request's target theorems,
    and (c) every proof region is still the generator's ``sorry``
    placeholder — i.e. this really is the untouched problem skeleton.
    """

    raw = source.encode() if isinstance(source, str) else source
    if sha256_hex(raw) != request.source_ref:
        raise SubmissionError(
            "skeleton bytes do not match the pinned source_ref; refusing to "
            "bind submissions to a mutated skeleton"
        )
    text = raw.decode("utf-8")
    regions = split_regions(text)
    if sorted(regions.theorem_names) != sorted(request.target_theorems):
        raise SubmissionError(
            "skeleton theorems do not match the pinned target_theorems"
        )
    for name, proof in regions.proofs.items():
        if SKELETON_PLACEHOLDER_MARKER not in proof or not _SORRY_TOKEN.search(proof):
            raise SubmissionError(
                f"theorem {name!r}: skeleton proof hole is not the generator "
                "placeholder"
            )
    return Skeleton(source=text, request=request, regions=regions)


def load_skeleton_dir(problem_dir: Path) -> Skeleton:
    """Load a built problem directory (``domain.lean`` +
    ``pinned_lean_request.json``) as an immutable skeleton."""

    problem_dir = Path(problem_dir)
    request = PinnedLeanRequest.model_validate_json(
        (problem_dir / "pinned_lean_request.json").read_text(encoding="utf-8")
    )
    return load_skeleton((problem_dir / "domain.lean").read_bytes(), request)


def _validate_proof_body(name: str, body: str) -> list[str]:
    if not isinstance(body, str) or not body.strip():
        raise SubmissionError(f"theorem {name!r}: empty proof body")
    if _SORRY_TOKEN.search(body):
        raise SubmissionError(f"theorem {name!r}: proof body contains 'sorry'")
    if SKELETON_PLACEHOLDER_MARKER in body:
        raise SubmissionError(
            f"theorem {name!r}: proof body contains the skeleton placeholder "
            "marker"
        )
    return body.split("\n")


def bind_submission(
    skeleton: Skeleton, submission: Mapping[str, str]
) -> BoundSubmission:
    """Reconstruct the Lean source from the skeleton plus proof bodies.

    Proof bodies are inserted VERBATIM into the skeleton's proof holes (they
    must be indented, as in any Lean tactic block).  After reconstruction
    the source is re-parsed: the theorem sequence and the hash of the
    non-proof regions must be identical to the skeleton's, so any body that
    escapes its hole — a column-0 restatement, an injected ``axiom``, a new
    declaration between theorems — changes the non-proof fingerprint and is
    rejected before any verification.  Only then is ``source_ref``
    recomputed for the pinned verification request.
    """

    expected = set(skeleton.regions.theorem_names)
    provided = set(submission)
    if provided != expected:
        missing = sorted(expected - provided)
        unknown = sorted(provided - expected)
        raise SubmissionError(
            f"submission must map exactly the skeleton theorems; missing="
            f"{missing} unknown={unknown}"
        )

    bodies = {
        name: _validate_proof_body(name, submission[name]) for name in expected
    }

    reconstructed_lines: list[str] = []
    lines = skeleton.source.split("\n")
    index = 0
    while index < len(lines):
        line = lines[index]
        matched = _THEOREM_LINE.match(line)
        if matched is None:
            reconstructed_lines.append(line)
            index += 1
            continue
        name = matched.group(1)
        reconstructed_lines.append(line)
        index += 1
        while not reconstructed_lines[-1].rstrip().endswith(_PROOF_HEADER_SUFFIX):
            reconstructed_lines.append(lines[index])
            index += 1
        # Skip the skeleton's placeholder region; splice the proof body in.
        while index < len(lines) and (
            lines[index] == "" or lines[index][0] in (" ", "\t")
        ):
            index += 1
        reconstructed_lines.extend(bodies[name])
        reconstructed_lines.append("")  # keep theorems separated

    reconstructed = "\n".join(reconstructed_lines)

    # Hash-compare the non-proof regions BEFORE any verification: any
    # mutation outside a proof hole is a rejected submission, full stop.
    regions = split_regions(reconstructed)
    if regions.theorem_names != skeleton.regions.theorem_names:
        raise SubmissionError(
            "reconstructed source does not declare exactly the skeleton "
            "theorems in order: a proof body escaped its hole"
        )
    if regions.non_proof_fingerprint != skeleton.regions.non_proof_fingerprint:
        raise SubmissionError(
            "non-proof regions differ from the immutable skeleton "
            "(statement/axiom/declaration mutation); submission rejected "
            "before verification"
        )

    # source_ref is computed only after reconstruction + binding checks.
    source_ref = sha256_hex(reconstructed.encode())
    request = PinnedLeanRequest.model_validate(
        {
            **skeleton.request.model_dump(mode="json", by_alias=True),
            "source_ref": source_ref,
        }
    )
    return BoundSubmission(
        source=reconstructed,
        source_ref=source_ref,
        request=request,
        non_proof_fingerprint=regions.non_proof_fingerprint,
    )
