"""Presentation labels for statuses without changing ontology values.

The stored vocabulary and the rendered vocabulary are deliberately different.
Stored labels are frozen: every committed root holds ``accepted`` and readers
of those roots must keep meaning what those roots meant. Rendered labels follow
the calculus (COMPUTABLE_CALCULUS §6), which names the label ``unrefuted`` on
purpose -- membership in the grounded extension means every attack so far is
defeated, and nothing stronger. A reader who sees "accepted" supplies the
stronger reading unbidden, which is the misreading the ``adjudication-blindness``
check (spec v1.7 §E) exists to warn about.

The line that decides every case: a string WRITTEN INTO A ROOT stays
``accepted``; a string RENDERED TO A READER says ``unrefuted``.
"""

from __future__ import annotations

from collections import Counter

from deepreason.ontology import Status


# Rendered vocabulary. Only ACCEPTED moves: the other three labels are already
# the calculus's own words. Never consult this map to interpret a stored value.
_DISPLAY: dict[str, str] = {Status.ACCEPTED.value: "unrefuted"}

_GLOSS: dict[str, str] = {
    Status.ACCEPTED.value: (
        "every attack so far is defeated -- survival, not endorsement"
    ),
    Status.REFUTED.value: "a warranted attack stands",
    Status.SUSPENDED.value: "under unresolved attack",
    Status.SUSPENDED_UNSUPPORTED.value: (
        "orphaned, not false -- it lost its ground, it was not shown wrong"
    ),
}


def _status_value(status: Status | str) -> str:
    return status.value if isinstance(status, Status) else str(status)


def display_status(
    status: Status | str,
    workload_profile: str | None = None,
    authority_policy=None,
) -> str:
    """Return the user-facing label for one internal status.

    ``workload_profile`` and ``authority_policy`` are intentionally accepted at
    this seam so later display distinctions can remain policy-aware without
    mutating the enum. Neither has an effect today: the rendered vocabulary is
    the calculus's, and the calculus does not vary it by workload.
    """

    value = _status_value(status)
    return _DISPLAY.get(value, value)


def status_gloss(status: Status | str) -> str:
    """Plain-language meaning of one status, for surfaces with room for it.

    Rendered alongside the label, never instead of it: the gloss is what stops a
    reader from supplying a stronger reading than the label carries.
    """

    return _GLOSS.get(_status_value(status), "")


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
