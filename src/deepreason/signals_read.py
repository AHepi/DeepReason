"""Part F (R15): a pure, read-only aggregation over already-existing,
already-live signals.

Strictly a READ surface: no new event/record type, and every field is
derived from records the harness already writes for other purposes
(config-referee critiques, deferred-v6-phase markers, provider-call token
usage). No mid-run consumption -- callers read a run's log at a boundary
(``report``/``audit``/CLI tooling), never during scheduling.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_DEFERRED_PHASE_DETAIL = re.compile(r"^phase '([^']*)' for role '[^']*' was deferred")


class SignalSnapshotV1(BaseModel):
    """One point-in-time read of a run's already-recorded signals."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["deepreason-signal-snapshot.v1"] = Field(
        "deepreason-signal-snapshot.v1", alias="schema"
    )
    config_critique: dict | None
    deferred_model_phase_counts: dict[str, int]
    token_spend: dict


def _deferred_model_phase_counts(root: Path) -> dict[str, int]:
    """Per-phase counts of well-formed `v6-model-phase-deferred` markers.

    A pure reader over `verification.report._deferred_model_phase_findings`'s
    existing output -- that function's `VerificationFindingV2` records carry
    no structured `phase` field, only prose (`detail`), so this parses the
    phase back out of the fixed `f"phase {phase!r} for role {role!r} was
    deferred..."` shape rather than re-scanning the log a second time.
    Malformed markers (`channel == "integrity"`) have a different detail
    shape and are correctly excluded -- they carry no recoverable phase.
    """

    from deepreason.verification.report import _deferred_model_phase_findings

    counts: dict[str, int] = {}
    for finding in _deferred_model_phase_findings(root):
        if finding.channel != "completion" or finding.check != "model-phase-deferred":
            continue
        match = _DEFERRED_PHASE_DETAIL.match(finding.detail)
        if match is None:
            continue
        phase = match.group(1)
        counts[phase] = counts.get(phase, 0) + 1
    return counts


def _token_spend(root: Path) -> dict:
    """Sum every logged provider call's usage into a `TokenMeter.snapshot()`-
    shaped dict.

    `TokenMeter.snapshot()` itself is live-process-only state (no run root
    persists it); `budget`/`reserved` have no after-the-fact equivalent and
    are correctly absent here. `prompt_tokens`/`completion_tokens`/`total`/
    `calls` are exactly what the harness's own `record_llm_calls` docstring
    names as the durable source of token accounting: `event.llm`.
    """

    from deepreason.harness import Harness

    try:
        events = tuple(Harness(root, read_only=True).log.read())
    except Exception:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total": 0, "calls": 0}
    calls = [event.llm for event in events if event.llm is not None]
    return {
        "prompt_tokens": sum(call.prompt_tokens or 0 for call in calls),
        "completion_tokens": sum(call.completion_tokens or 0 for call in calls),
        "total": sum(call.tokens for call in calls),
        "calls": len(calls),
    }


def read_signal_snapshot(root: Path | str) -> SignalSnapshotV1:
    """Aggregate a run root's already-live signals into one typed snapshot.

    Pure read, no mid-run wiring -- consumable from `report`/`audit`/CLI
    tooling at run boundaries only (Amendment 5's benching holds).
    """

    from deepreason.harness import Harness
    from deepreason.referee import latest_config_critique

    root = Path(root)
    try:
        harness = Harness(root, read_only=True)
        config_critique = latest_config_critique(harness)
    except Exception:
        config_critique = None
    return SignalSnapshotV1(
        config_critique=config_critique,
        deferred_model_phase_counts=_deferred_model_phase_counts(root),
        token_spend=_token_spend(root),
    )
