"""Negative atlas / refuted index (spec §11.5).

The refuted-artifact embedding index that powers anti-relapse stage 2 IS the
negative atlas. It feeds the gate and the scheduler and is NEVER rendered
into packs (negative conditioning primes the very content it bans). Enforce
tabu at the door, not in the prompt. Rebuilt deterministically from state
(itself a deterministic function of the log, §14). Entries are
model-version-specific: revalidate on embedder upgrade.
"""

from deepreason.llm.embedder import distance
from deepreason.ontology.state import Status
from deepreason.programs import content_text


class RefutedIndex:
    def __init__(self, embedder) -> None:
        self.embedder = embedder
        self._entries: list[tuple[str, list[float]]] = []

    def rebuild(self, harness) -> None:
        self._entries = [
            (aid, self.embedder.embed(content_text(harness.state.artifacts[aid], harness.blobs)))
            for aid, status in harness.state.status.items()
            if status == Status.REFUTED
        ]

    def nearest(self, vector: list[float], eps: float) -> list[str]:
        """Refuted ids within eps, closest first; deterministic tiebreak."""
        hits = [
            (distance(vector, emb), aid)
            for aid, emb in self._entries
            if distance(vector, emb) <= eps
        ]
        return [aid for _, aid in sorted(hits)]
