"""Negative atlas / refuted index (spec §11.5).

The refuted-artifact embedding index that powers anti-relapse stage 2 IS the
negative atlas. Refuted-region records are ordinary artifacts feeding the
gate and the scheduler — NEVER rendered into packs (negative conditioning
primes the very content it bans). Enforce tabu at the door, not in the
prompt. Entries are model-version-specific: revalidate on endpoint upgrade.
Rebuilt deterministically from the log (§14).
"""


class RefutedIndex:
    def rebuild(self, log) -> None:
        raise NotImplementedError

    def nearest(self, embedding: list[float], eps: float):
        """NN within NEAR_DUP_EPS, or None. TODO(P2)."""
        raise NotImplementedError
