"""Sealed-holdout wiring for the E3.1 benchmark (harness-spec-v1.3 §10.5/§14).

Each problem's verifier and answer key are written as content-addressed blobs
into a ``holdout/`` namespace (spec §14: "Sealed holdout blobs live in a
`holdout/` namespace excluded from pack rendering until their `Reveal`
event").  Per §10.5 the digests stay visible — a manifest lists problem ids,
classes, seeds, and certificate digests — while the bytes are withheld from
any future run loop and revealed only post-hoc.

This module also provides the sealing audit used at build time and in tests:
no problem-facing file may contain the bytes of any sealed blob.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.storage.blobs import BlobStore

HOLDOUT_MANIFEST_SCHEMA = "e31-holdout-manifest-v1"
REVEAL_POLICY = "post_hoc_reveal_only"


@dataclass(frozen=True)
class SealedProblem:
    """One problem's withheld material: named blobs (verifier, answer key,
    difficulty certificate), all sealed together.

    ``generator_metadata`` carries generator-internal facts (e.g. which
    schema templates produced a domain's axioms) that must stay out of
    every problem-facing rendering; it is recorded on the sealed holdout
    manifest, inside the ``holdout/`` namespace."""

    problem_id: str
    problem_class: str
    seed: str
    blobs: dict[str, bytes] = field(repr=False)
    certificate_blob: str = "certificate.json"
    generator_metadata: dict[str, Any] | None = None

    def refs(self) -> dict[str, str]:
        """Content addresses (hash-visible per §10.5) without storing bytes."""

        return {name: sha256_hex(data) for name, data in sorted(self.blobs.items())}

    @property
    def certificate_digest(self) -> str:
        if self.certificate_blob not in self.blobs:
            raise KeyError(
                f"{self.problem_id}: sealed material must include "
                f"{self.certificate_blob!r}"
            )
        return sha256_hex(self.blobs[self.certificate_blob])


def seal_holdout(holdout_root: Path, sealed: list[SealedProblem]) -> dict[str, Any]:
    """Write sealed blobs into ``<holdout_root>/blobs`` (content-addressed via
    the repo BlobStore) and the holdout manifest; return the manifest."""

    holdout_root = Path(holdout_root)
    store = BlobStore(holdout_root / "blobs")
    entries: list[dict[str, Any]] = []
    for problem in sorted(sealed, key=lambda item: item.problem_id):
        refs: dict[str, str] = {}
        for name, data in sorted(problem.blobs.items()):
            ref = store.put(data)
            if ref != sha256_hex(data):
                raise RuntimeError(f"blob store returned a non-content digest for {name}")
            refs[name] = ref
        entry: dict[str, Any] = {
            "id": problem.problem_id,
            "class": problem.problem_class,
            "seed": problem.seed,
            "certificate_digest": problem.certificate_digest,
            "sealed_refs": refs,
        }
        if problem.generator_metadata is not None:
            entry["generator_metadata"] = problem.generator_metadata
        entries.append(entry)
    manifest = {
        "schema": HOLDOUT_MANIFEST_SCHEMA,
        "namespace": "holdout/",
        "reveal_policy": REVEAL_POLICY,
        "spec": "docs/harness-spec-v1.3.md §10.5, §14",
        "note": (
            "Digests are visible; bytes are excluded from every problem-facing "
            "rendering until a Reveal event.  Verifiers and answer keys are "
            "withheld from any run loop and revealed only post-hoc."
        ),
        "problems": entries,
    }
    manifest_bytes = json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"
    (holdout_root / "manifest.json").write_bytes(manifest_bytes)
    return manifest


def sealing_violations(
    problem_facing_root: Path, sealed: list[SealedProblem], *, min_probe_bytes: int = 24
) -> list[str]:
    """Audit: return every (problem-facing file, sealed blob) pair where the
    sealed bytes leak into a problem-facing file.

    Probes shorter than ``min_probe_bytes`` are skipped as substring-match
    noise; every real sealed artifact in this benchmark is far larger.
    """

    probes: list[tuple[str, bytes]] = []
    for problem in sealed:
        for name, data in sorted(problem.blobs.items()):
            if len(data) >= min_probe_bytes:
                probes.append((f"{problem.problem_id}/{name}", data))
    violations: list[str] = []
    root = Path(problem_facing_root)
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        content = path.read_bytes()
        for label, probe in probes:
            if probe in content:
                violations.append(f"{path.relative_to(root)} contains sealed {label}")
    return violations


def load_sealed_blob(holdout_root: Path, ref: str) -> bytes:
    """Post-hoc Reveal path: fetch sealed bytes by content address."""

    return BlobStore(Path(holdout_root) / "blobs", read_only=True).get(ref)


def certificate_digest(certificate: Any) -> str:
    """Digest of a certificate object over canonical JSON bytes."""

    return sha256_hex(canonical_json(certificate))
