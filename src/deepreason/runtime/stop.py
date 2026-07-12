"""Deterministic operational completion, convergence, and stuck policy."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Literal

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


ESCAPE_LADDER = (
    "expand_requested_context",
    "rotate_conditioning_slice",
    "complement_tail_variation",
    "criticism_debt_or_discrimination_sweep",
    "increase_remaining_aggregate_budget",
)


class StopController:
    def __init__(self, policy: StopPolicy) -> None:
        self.policy = policy
        self._window: deque[StopMetrics] = deque(maxlen=policy.window)
        self._stable_windows = 0
        self._escapes = 0

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
    root_path = Path(root)
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
    history = root_path / "run-stops" / f"{event_seq:012d}-{digest}.json"
    if not history.exists():
        _atomic_json(history, record)
    _atomic_json(root_path / "run-stop.json", record)
    return record
