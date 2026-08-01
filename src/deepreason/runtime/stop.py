"""Deterministic operational completion, convergence, and stuck policy."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from deepreason.runtime.progress import _atomic_json


StopReason = Literal[
    "completed",
    "converged",
    "stuck",
    "budget_exhausted",
    "operator_cancelled",
    "operational_failure",
    "workload_terminal",
]


class StopPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = True
    min_cycles: int = Field(default=6, ge=0)
    window: int = Field(default=8, gt=0)
    stable_windows: int = Field(default=2, gt=0)
    frontier_delta_max: int = Field(default=0, ge=0)
    status_churn_max: int = Field(default=0, ge=0)
    new_problem_max: int = Field(default=0, ge=0)
    new_admission_max: int = Field(default=0, ge=0)
    pending_deterministic_checks_must_be_zero: bool = True
    criticism_debt_max: float = Field(default=0.1, ge=0.0)
    open_research_blocks_completion: bool = True
    stuck_signal_window: int = Field(default=3, gt=0)
    escape_attempts: int = Field(default=3, ge=0)

    @property
    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(
                self.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()


class StopMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cycle: int = Field(ge=0)
    workload_complete: bool = False
    frontier_delta: int = Field(default=0, ge=0)
    status_churn: int = Field(default=0, ge=0)
    new_problems: int = Field(default=0, ge=0)
    new_admissions: int = Field(default=0, ge=0)
    pending_deterministic_checks: int = Field(default=0, ge=0)
    criticism_debt: float = Field(default=0.0, ge=0.0)
    open_research: int = Field(default=0, ge=0)
    stuck_signal: bool = False
    gate_orbit: bool = False
    repair_exhausted: bool = False


class StopDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    stop: bool
    reason: StopReason | None = None
    escape_action: str | None = None


class StopControllerStateV1(BaseModel):
    """Replayable internal state of the existing deterministic controller.

    This is a serialization boundary, not a second stopping policy.  It lets a
    v4 lifecycle receipt prove the exact window/counters that were supplied to
    :class:`StopController` and lets continuation rehydrate those counters
    without inferring them from model prose or rebuilding them from formal
    ontology events.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["stop-controller-state.v1"] = Field(
        "stop-controller-state.v1", alias="schema"
    )
    policy_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    window: tuple[StopMetrics, ...] = Field(default=(), max_length=4_096)
    stable_windows: int = Field(default=0, ge=0)
    escapes: int = Field(default=0, ge=0)

    @property
    def last_cycle(self) -> int | None:
        return self.window[-1].cycle if self.window else None


ESCAPE_LADDER = (
    "expand_requested_context",
    "rotate_conditioning_slice",
    "complement_tail_variation",
    "criticism_debt_or_discrimination_sweep",
    "increase_remaining_aggregate_budget",
)


class StopController:
    def __init__(
        self,
        policy: StopPolicy,
        *,
        state: StopControllerStateV1 | dict[str, Any] | None = None,
    ) -> None:
        self.policy = policy
        self._window: deque[StopMetrics] = deque(maxlen=policy.window)
        self._stable_windows = 0
        self._escapes = 0
        if state is not None:
            self.restore(state)

    def snapshot(self) -> StopControllerStateV1:
        """Return the canonical state needed for exact deterministic resume."""

        return StopControllerStateV1(
            policy_digest=self.policy.digest,
            window=tuple(self._window),
            stable_windows=self._stable_windows,
            escapes=self._escapes,
        )

    def restore(
        self, state: StopControllerStateV1 | dict[str, Any]
    ) -> None:
        """Rehydrate a controller only when the frozen policy still matches."""

        if isinstance(state, StopControllerStateV1):
            state = state.model_dump(mode="python", by_alias=True)
        normalized = StopControllerStateV1.model_validate(state)
        if normalized.policy_digest != self.policy.digest:
            raise ValueError("stop controller state belongs to another policy")
        if len(normalized.window) > self.policy.window:
            raise ValueError("stop controller state exceeds the policy window")
        cycles = tuple(metric.cycle for metric in normalized.window)
        if any(right <= left for left, right in zip(cycles, cycles[1:])):
            raise ValueError("stop controller metrics must have increasing cycles")
        allowed_escapes = max(self.policy.escape_attempts, len(ESCAPE_LADDER))
        if normalized.escapes > allowed_escapes:
            raise ValueError("stop controller state exceeds its escape ceiling")
        self._window = deque(normalized.window, maxlen=self.policy.window)
        self._stable_windows = normalized.stable_windows
        self._escapes = normalized.escapes

    def _stable(self) -> bool:
        if len(self._window) < self.policy.window:
            return False
        return all(
            item.frontier_delta <= self.policy.frontier_delta_max
            and item.status_churn <= self.policy.status_churn_max
            and item.new_problems <= self.policy.new_problem_max
            and item.new_admissions <= self.policy.new_admission_max
            and (
                not self.policy.pending_deterministic_checks_must_be_zero
                or item.pending_deterministic_checks == 0
            )
            and item.criticism_debt <= self.policy.criticism_debt_max
            and (not self.policy.open_research_blocks_completion or item.open_research == 0)
            for item in self._window
        )

    def evaluate(self, metrics: StopMetrics) -> StopDecision:
        if not self.policy.enabled:
            return StopDecision(stop=False)
        self._window.append(metrics)
        mandatory_clear = metrics.pending_deterministic_checks == 0
        research_clear = not self.policy.open_research_blocks_completion or metrics.open_research == 0
        if metrics.workload_complete and mandatory_clear and research_clear:
            return StopDecision(stop=True, reason="completed")
        stable = metrics.cycle >= self.policy.min_cycles and self._stable()
        self._stable_windows = self._stable_windows + 1 if stable else 0
        if self._stable_windows >= self.policy.stable_windows:
            return StopDecision(stop=True, reason="converged")

        stuck_recent = list(self._window)[-self.policy.stuck_signal_window :]
        repeated_signal = (
            len(stuck_recent) == self.policy.stuck_signal_window
            and all(item.stuck_signal for item in stuck_recent)
        )
        corroborated = metrics.gate_orbit or metrics.repair_exhausted
        no_progress = all(
            item.frontier_delta == 0
            and item.status_churn == 0
            and item.new_problems == 0
            and item.new_admissions == 0
            for item in stuck_recent
        )
        if repeated_signal and corroborated and no_progress:
            allowed = max(self.policy.escape_attempts, len(ESCAPE_LADDER))
            if self._escapes < allowed:
                action = ESCAPE_LADDER[min(self._escapes, len(ESCAPE_LADDER) - 1)]
                self._escapes += 1
                return StopDecision(stop=False, escape_action=action)
            return StopDecision(stop=True, reason="stuck")
        return StopDecision(stop=False)


def write_stop_record(
    root: Path | str,
    *,
    reason: StopReason,
    policy: StopPolicy,
    metrics: StopMetrics,
    event_seq: int,
) -> dict:
    record = build_stop_record(
        reason=reason,
        policy=policy,
        metrics=metrics,
        event_seq=event_seq,
    )
    return persist_stop_record(root, record)


def build_stop_record(
    *,
    reason: StopReason,
    policy: StopPolicy,
    metrics: StopMetrics,
    event_seq: int,
) -> dict:
    """Build the unchanged v1 stop payload without publishing its latest pointer."""

    policy = StopPolicy.model_validate(policy)
    metrics = StopMetrics.model_validate(metrics)
    if type(event_seq) is not int or event_seq < 0:
        raise ValueError("stop event sequence must be a nonnegative integer")
    record = {
        "schema": "deepreason-run-stop-v1",
        "reason": reason,
        "policy_digest": policy.digest,
        "metrics": metrics.model_dump(mode="json"),
        "event_seq": event_seq,
    }
    digest = hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    record["digest"] = digest
    return record


def persist_stop_record(root: Path | str, record: dict) -> dict:
    """Validate and atomically publish a prebuilt v1 stop record.

    Separating construction from publication lets the v4 scheduler bind the
    digest in a durable Control event before ``run-stop.json`` becomes the
    mutable latest-stop pointer.  Existing callers of :func:`write_stop_record`
    retain byte-for-byte output.
    """

    record = validate_stop_record(record)

    root_path = Path(root)
    digest = record["digest"]
    event_seq = record["event_seq"]
    history = root_path / "run-stops" / f"{event_seq:012d}-{digest}.json"
    if not history.exists():
        _atomic_json(history, record)
    _atomic_json(root_path / "run-stop.json", record)
    return dict(record)


def validate_stop_record(record: dict) -> dict:
    """Return one canonical typed v1 stop without writing mutable pointers."""

    if not isinstance(record, dict):
        raise ValueError("stop record must be an object")
    required = {
        "schema",
        "reason",
        "policy_digest",
        "metrics",
        "event_seq",
        "digest",
    }
    if set(record) != required or record.get("schema") != "deepreason-run-stop-v1":
        raise ValueError("stop record has an invalid schema")
    reason = record.get("reason")
    if reason not in StopReason.__args__:
        raise ValueError("stop record has an invalid reason")
    policy_digest = record.get("policy_digest")
    if (
        not isinstance(policy_digest, str)
        or len(policy_digest) != 64
        or any(character not in "0123456789abcdef" for character in policy_digest)
    ):
        raise ValueError("stop record has an invalid policy digest")
    normalized_metrics = StopMetrics.model_validate(record.get("metrics"))
    if normalized_metrics.model_dump(mode="json") != record.get("metrics"):
        raise ValueError("stop record metrics are not in canonical typed form")
    event_seq = record.get("event_seq")
    if type(event_seq) is not int or event_seq < 0:
        raise ValueError("stop record has an invalid event sequence")
    unsigned = {key: value for key, value in record.items() if key != "digest"}
    expected = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if record.get("digest") != expected:
        raise ValueError("stop record digest does not match its canonical payload")
    return dict(record)
