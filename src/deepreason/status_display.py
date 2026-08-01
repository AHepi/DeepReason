"""Presentation labels for statuses without changing ontology values."""

from __future__ import annotations

from collections import Counter

from deepreason.ontology import Status


def _status_value(status: Status | str) -> str:
    return status.value if isinstance(status, Status) else str(status)


def display_status(
    status: Status | str,
    workload_profile: str | None,
    authority_policy=None,
) -> str:
    """Return the user-facing label for one internal status.

    ``authority_policy`` is intentionally accepted at this seam so later
    display distinctions can remain policy-aware without mutating the enum.
    It has no effect in this first tranche.
    """

    value = _status_value(status)
    if workload_profile == "text" and value == Status.ACCEPTED.value:
        return "standing"
    return value


def display_status_counts(
    harness,
    manifest=None,
    *,
    workload_profile: str | None = None,
    authority_policy=None,
) -> dict[str, int]:
    """Count statuses using display labels, without touching harness state."""

    workload = workload_profile
    if workload is None and manifest is not None:
        workload = getattr(manifest, "workload_profile", None)
    counts = Counter(
        display_status(status, workload, authority_policy)
        for status in harness.state.status.values()
    )
    return dict(sorted(counts.items()))
