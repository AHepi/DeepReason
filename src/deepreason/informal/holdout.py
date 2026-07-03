"""Holdout + Reveal (spec §10.5).

Sealed evidence: content-addressed (hash visible; bytes live in the
``holdout/`` namespace, unreadable by the blob store), so the deterministic
pack renderer cannot leak it. Sealed evidence does not count as covering
pre-reveal — commitments are scheduled-pending, not failed, and no
premature research Spawn fires. At Reveal (a logged, replayable event) the
bytes enter the blob store; a subsequent pass on held-out material is a
reach hit with the strongest provenance the informal side produces: the
log timestamps prove the artifact predates the evidence (Lakatos's
novel-fact criterion, mechanized).
"""

from deepreason.canonical import sha256_hex
from deepreason.ontology import Artifact, Interface, Provenance, Rule


def seal(harness, data: bytes, *, codec: str = "utf8", problem_id: str | None = None) -> Artifact:
    """Register evidence sealed: hash visible, bytes withheld."""
    ref = sha256_hex(data)
    holdout_dir = harness.root / "holdout"
    holdout_dir.mkdir(parents=True, exist_ok=True)
    (holdout_dir / ref).write_bytes(data)
    interface = Interface()
    artifact = Artifact(
        id=Artifact.compute_id(ref, codec, interface),
        content_ref=ref,
        codec=codec,
        interface=interface,
        provenance=Provenance(role="import"),
    )
    return harness.register_artifact(artifact, problem_id=problem_id)


def is_sealed(harness, artifact: Artifact) -> bool:
    if artifact.content_ref.startswith("inline:"):
        return False
    try:
        harness.blobs.get(artifact.content_ref)
        return False
    except KeyError:
        return (harness.root / "holdout" / artifact.content_ref).exists()


def reveal(harness, artifact_id: str) -> None:
    """Scheduled Reveal event: bytes become readable; replay reproduces it."""
    harness._commit(Rule.REVEAL, inputs=[artifact_id], outputs=[])
