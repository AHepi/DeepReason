"""User as appellate court (spec §10.6).

Disagreement-ranked docket (ensemble splits, guard-block streaks, audit hits,
maximum-entropy rivalries), never round-robin, capped at
USER_RULINGS_BUDGET per session. Each ruling registers as a precedent
artifact (provenance.role: user): ranked first in precedent slices, yet an
ordinary artifact — attackable, reinstateable (N1). Appellate, not oracle.
"""


def docket(state) -> list:
    """Disagreement-ranked queue of cases for the user. TODO(P5)."""
    raise NotImplementedError


def rule(case_id: str, holding: str, standard_id: str, state):
    """Register a user ruling as a precedent artifact. TODO(P5)."""
    raise NotImplementedError
