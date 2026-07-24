"""Qualify and operate the installed DeepReason wheel against loopback HTTP.

The deterministic OpenAI-compatible provider in this file is an external
qualification fixture.  It uses only the standard library, is never imported
by :mod:`deepreason`, and is excluded from the wheel by the package layout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import venv
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

EXPECTED_MCP_SCHEMA_SHA256 = (
    "7520ea29fa8efba50c98a9ffa76adfbe0c59c66f51541dfe609dee7736bf82e1"
)
EXPECTED_MCP_TOOLS = (
    "get_readiness",
    "start_run",
    "run_status",
    "run_result",
    "continue_run",
    "cancel_run",
    "scratch_map",
    "scratch_search",
    "scratch_open",
    "scratch_related",
    "scratch_attention",
    "start_bridge",
    "bridge_status",
    "bridge_result",
    "bridge_claims",
    "get_capabilities",
    "get_help_topic",
    "get_request_requirements",
)
TEST_CREDENTIAL_ENV = "DEEPREASON_LOOPBACK_SMOKE_KEY"
TEST_CREDENTIAL = "loopback-credential-must-never-appear"
LOOPBACK_READY_ENV = "DEEPREASON_WHEEL_LOOPBACK_READY"
TERMINAL_DIAGNOSTIC_ENABLE_ENV = (
    "DEEPREASON_WHEEL_TERMINAL_PHASE_DIAGNOSTIC"
)
TERMINAL_DIAGNOSTIC_LEDGER_ENV = (
    "DEEPREASON_WHEEL_TERMINAL_PHASE_LEDGER"
)
TERMINAL_DIAGNOSTIC_MAX_RECORDS = 32_768
TERMINAL_DIAGNOSTIC_MAX_BYTES = 8 * 1024 * 1024
TERMINAL_PUBLICATION_RECOVERY_SENTINEL = (
    "TERMINAL_PUBLICATION_RECOVERY_REQUIRED"
)
RESUMABLE_STOP_QUESTION = (
    "What makes a typed resumable stop preserve continuation authority?"
)
FAILURE_SCHEMA = "deepreason-wheel-operational-failure-v4"
CONTINUATION_DEADLINE_SECONDS = 600
POLL_INTERVAL_SECONDS = 0.05
DIAGNOSTIC_INSPECTION_TIMEOUT_SECONDS = 10
PLATFORM_WINDOWS = "windows"
PLATFORM_MACOS = "macos"
PLATFORM_LINUX = "linux"
PLATFORM_OTHER = "other"
ALLOWED_PLATFORM_FAMILIES = frozenset(
    {
        PLATFORM_WINDOWS,
        PLATFORM_MACOS,
        PLATFORM_LINUX,
        PLATFORM_OTHER,
    }
)
STAGE_BUILD_WHEEL = "build_wheel"
STAGE_CREATE_ENVIRONMENT = "create_environment"
STAGE_INSTALL_WHEEL = "install_wheel"
STAGE_SETUP_PROFILE = "setup_profile"
STAGE_QUALIFY = "qualify"
STAGE_READINESS = "readiness"
STAGE_REASON = "reason"
STAGE_MCP_INITIALIZE = "mcp_initialize"
STAGE_MCP_REQUEST = "mcp_request"
STAGE_CONTINUATION_REJECTION = "continuation_rejection"
STAGE_CONTINUATION_RESUME = "continuation_resume"
STAGE_REPLAY_VALIDATION = "replay_validation"
STAGE_RESTART_RECOVERY = "restart_recovery"
STAGE_BUDGET_REJECTION = "budget_rejection"
STAGE_MANIFEST_REJECTION = "manifest_rejection"
STAGE_DISCLOSURE_CHECK = "disclosure_check"
STAGE_CLEANUP = "cleanup"
ALLOWED_FAILURE_STAGES = frozenset(
    {
        STAGE_BUILD_WHEEL,
        STAGE_CREATE_ENVIRONMENT,
        STAGE_INSTALL_WHEEL,
        STAGE_SETUP_PROFILE,
        STAGE_QUALIFY,
        STAGE_READINESS,
        STAGE_REASON,
        STAGE_MCP_INITIALIZE,
        STAGE_MCP_REQUEST,
        STAGE_CONTINUATION_REJECTION,
        STAGE_CONTINUATION_RESUME,
        STAGE_REPLAY_VALIDATION,
        STAGE_RESTART_RECOVERY,
        STAGE_BUDGET_REJECTION,
        STAGE_MANIFEST_REJECTION,
        STAGE_DISCLOSURE_CHECK,
        STAGE_CLEANUP,
    }
)
FAILURE_COMMAND = "command_failed"
FAILURE_TIMEOUT = "timeout"
FAILURE_ASSERTION = "assertion_failed"
FAILURE_UNEXPECTED = "unexpected_failure"
FAILURE_CLEANUP = "cleanup_failed"
ALLOWED_FAILURE_KINDS = frozenset(
    {
        FAILURE_COMMAND,
        FAILURE_TIMEOUT,
        FAILURE_ASSERTION,
        FAILURE_UNEXPECTED,
        FAILURE_CLEANUP,
    }
)
DETAIL_CHILD_EXIT_NONZERO = "child_exit_nonzero"
DETAIL_CHILD_LAUNCH_FAILED = "child_launch_failed"
DETAIL_CHILD_TIMEOUT = "child_timeout"
DETAIL_EXECUTABLE_RESOLUTION_FAILED = "executable_resolution_failed"
DETAIL_FILESYSTEM_ACCESS_DENIED = "filesystem_access_denied"
DETAIL_UNKNOWN_REASON_FAILURE = "unknown_reason_failure"
TYPED_REASON_RUN_WORKER_NOT_FOUND = "RUN_WORKER_NOT_FOUND"
ALLOWED_TYPED_REASON_CODES = frozenset({TYPED_REASON_RUN_WORKER_NOT_FOUND})
ALLOWED_DETAIL_CODES = frozenset(
    {
        DETAIL_CHILD_EXIT_NONZERO,
        DETAIL_CHILD_LAUNCH_FAILED,
        DETAIL_CHILD_TIMEOUT,
        DETAIL_EXECUTABLE_RESOLUTION_FAILED,
        DETAIL_FILESYSTEM_ACCESS_DENIED,
        DETAIL_UNKNOWN_REASON_FAILURE,
        *ALLOWED_TYPED_REASON_CODES,
    }
)
DURABLE_PREPARATION_ABSENT = "preparation_absent"
DURABLE_RUN_ROOT_PRESENT = "run_root_present"
DURABLE_PREPARATION_PRESENT = "preparation_present"
DURABLE_MANAGED_REGISTRATION_PRESENT = "managed_registration_present"
DURABLE_EVENT_LOG_PRESENT = "event_log_present"
DURABLE_TERMINAL_RESULT_PRESENT = "terminal_result_present"
DURABLE_STATE_INSPECTION_UNAVAILABLE = "state_inspection_unavailable"
ALLOWED_DURABLE_PROGRESS = frozenset(
    {
        DURABLE_PREPARATION_ABSENT,
        DURABLE_RUN_ROOT_PRESENT,
        DURABLE_PREPARATION_PRESENT,
        DURABLE_MANAGED_REGISTRATION_PRESENT,
        DURABLE_EVENT_LOG_PRESENT,
        DURABLE_TERMINAL_RESULT_PRESENT,
        DURABLE_STATE_INSPECTION_UNAVAILABLE,
    }
)
STATE_RUN_ROOT_PRESENT = "run_root_present"
STATE_PREPARATION_PRESENT = "preparation_present"
STATE_MANIFEST_PRESENT = "manifest_present"
STATE_MANAGED_REGISTRATION_PRESENT = "managed_registration_present"
STATE_PROGRESS_LOG_PRESENT = "progress_log_present"
STATE_EVENT_LOG_PRESENT = "event_log_present"
STATE_TERMINAL_RESULT_PRESENT = "terminal_result_present"
STATE_LOOPBACK_START_PRESENT = "loopback_start_present"
ALLOWED_STATE_PRESENCE_FIELDS = frozenset(
    {
        STATE_RUN_ROOT_PRESENT,
        STATE_PREPARATION_PRESENT,
        STATE_MANIFEST_PRESENT,
        STATE_MANAGED_REGISTRATION_PRESENT,
        STATE_PROGRESS_LOG_PRESENT,
        STATE_EVENT_LOG_PRESENT,
        STATE_TERMINAL_RESULT_PRESENT,
        STATE_LOOPBACK_START_PRESENT,
    }
)
DIAGNOSTIC_INSPECTION_NOT_ATTEMPTED = "not_attempted"
DIAGNOSTIC_INSPECTION_SUCCEEDED = "succeeded"
DIAGNOSTIC_INSPECTION_FAILED = "failed"
ALLOWED_DIAGNOSTIC_INSPECTION_STATUSES = frozenset(
    {
        DIAGNOSTIC_INSPECTION_NOT_ATTEMPTED,
        DIAGNOSTIC_INSPECTION_SUCCEEDED,
        DIAGNOSTIC_INSPECTION_FAILED,
    }
)
LIFECYCLE_NOT_OBSERVED = "not_observed"
LIFECYCLE_NOT_STARTED = "not_started"
LIFECYCLE_STARTING = "starting"
LIFECYCLE_RUNNING = "running"
LIFECYCLE_PAUSED = "paused"
LIFECYCLE_COMPLETED = "completed"
LIFECYCLE_FAILED = "failed"
LIFECYCLE_CANCELLED = "cancelled"
LIFECYCLE_UNKNOWN = "unknown"
ALLOWED_DIAGNOSTIC_LIFECYCLES = frozenset(
    {
        LIFECYCLE_NOT_OBSERVED,
        LIFECYCLE_NOT_STARTED,
        LIFECYCLE_STARTING,
        LIFECYCLE_RUNNING,
        LIFECYCLE_PAUSED,
        LIFECYCLE_COMPLETED,
        LIFECYCLE_FAILED,
        LIFECYCLE_CANCELLED,
        LIFECYCLE_UNKNOWN,
    }
)
_LIFECYCLE_MAP = {
    "not-started": LIFECYCLE_NOT_STARTED,
    "starting": LIFECYCLE_STARTING,
    "running": LIFECYCLE_RUNNING,
    "paused": LIFECYCLE_PAUSED,
    "completed": LIFECYCLE_COMPLETED,
    "failed": LIFECYCLE_FAILED,
    "cancelled": LIFECYCLE_CANCELLED,
}
PHASE_NOT_OBSERVED = "not_observed"
PHASE_MANIFEST = "manifest"
PHASE_RESUME = "resume"
PHASE_WORKLOAD = "workload"
PHASE_REASONING = "reasoning"
PHASE_STOP = "stop"
PHASE_UNKNOWN = "unknown"
ALLOWED_DIAGNOSTIC_PHASES = frozenset(
    {
        PHASE_NOT_OBSERVED,
        PHASE_MANIFEST,
        PHASE_RESUME,
        PHASE_WORKLOAD,
        PHASE_REASONING,
        PHASE_STOP,
        PHASE_UNKNOWN,
    }
)
_PHASE_MAP = {
    "manifest": PHASE_MANIFEST,
    "resume": PHASE_RESUME,
    "workload": PHASE_WORKLOAD,
    "reasoning": PHASE_REASONING,
    "stop": PHASE_STOP,
}
MCP_LIVENESS_NOT_STARTED = "not_started"
MCP_LIVENESS_ALIVE = "alive"
MCP_LIVENESS_EXITED = "exited"
MCP_LIVENESS_UNKNOWN = "unknown"
ALLOWED_MCP_LIVENESS = frozenset(
    {
        MCP_LIVENESS_NOT_STARTED,
        MCP_LIVENESS_ALIVE,
        MCP_LIVENESS_EXITED,
        MCP_LIVENESS_UNKNOWN,
    }
)
RESULT_BINDING_ABSENT = "absent"
RESULT_BINDING_PRIOR = "prior_commitment"
RESULT_BINDING_CURRENT = "current_commitment"
RESULT_BINDING_UNBOUND = "unbound"
RESULT_BINDING_UNKNOWN = "unknown"
ALLOWED_RESULT_BINDINGS = frozenset(
    {
        RESULT_BINDING_ABSENT,
        RESULT_BINDING_PRIOR,
        RESULT_BINDING_CURRENT,
        RESULT_BINDING_UNBOUND,
        RESULT_BINDING_UNKNOWN,
    }
)
W1_PRECOMMIT_AUDITS = "W1_PRECOMMIT_AUDITS"
W2_PRECOMMIT_VERIFICATION = "W2_PRECOMMIT_VERIFICATION"
W3_TERMINAL_AUTHORITY_STATE = "W3_TERMINAL_AUTHORITY_STATE"
W4_TERMINAL_DRAFT_CONSTRUCTION = "W4_TERMINAL_DRAFT_CONSTRUCTION"
W5_COMMITMENT_ENSURE = "W5_COMMITMENT_ENSURE"
W6_PENDING_RESULT_PUBLICATION = "W6_PENDING_RESULT_PUBLICATION"
W7_FRESH_REPLAY_DERIVATION = "W7_FRESH_REPLAY_DERIVATION"
W8_POSTCOMMIT_ROOT_VERIFICATION = "W8_POSTCOMMIT_ROOT_VERIFICATION"
W9_REPLAY_BINDING_VALIDATION = "W9_REPLAY_BINDING_VALIDATION"
W10_REPLAY_AND_FINAL_RESULT_PUBLICATION = (
    "W10_REPLAY_AND_FINAL_RESULT_PUBLICATION"
)
TERMINAL_LOCK = "TERMINAL_LOCK"
APPLICATION_INSPECT = "APPLICATION_INSPECT"
APPLICATION_RESULT = "APPLICATION_RESULT"
TERMINALIZATION_NOT_OBSERVED = "not_observed"
TERMINALIZATION_PHASES = (
    W1_PRECOMMIT_AUDITS,
    W2_PRECOMMIT_VERIFICATION,
    W3_TERMINAL_AUTHORITY_STATE,
    W4_TERMINAL_DRAFT_CONSTRUCTION,
    W5_COMMITMENT_ENSURE,
    W6_PENDING_RESULT_PUBLICATION,
    W7_FRESH_REPLAY_DERIVATION,
    W8_POSTCOMMIT_ROOT_VERIFICATION,
    W9_REPLAY_BINDING_VALIDATION,
    W10_REPLAY_AND_FINAL_RESULT_PUBLICATION,
)
DIAGNOSTIC_LEDGER_PHASES = (
    *TERMINALIZATION_PHASES,
    TERMINAL_LOCK,
    APPLICATION_INSPECT,
    APPLICATION_RESULT,
)
ALLOWED_LEDGER_PHASES = frozenset(DIAGNOSTIC_LEDGER_PHASES)
ALLOWED_TERMINALIZATION_OBSERVATIONS = frozenset(
    {TERMINALIZATION_NOT_OBSERVED, *TERMINALIZATION_PHASES, TERMINAL_LOCK}
)
ALLOWED_LEDGER_EDGES = frozenset(
    {"enter", "return", "error", "wait_start", "acquired", "released"}
)
ALLOWED_LEDGER_ACTORS = frozenset({"worker", "mcp_server", "other"})
ERROR_NONE = "none"
ERROR_RUN_RESULT_NOT_READY = "run_result_not_ready"
ERROR_MANIFEST_ADMISSION = "manifest_admission"
ERROR_PROCESS_LOCK_BUSY = "process_lock_busy"
ERROR_TERMINAL_AUTHORITY = "terminal_authority"
ERROR_REPLAY_VERIFICATION = "replay_verification"
ERROR_REPLAY_BINDING = "replay_binding"
ERROR_ATOMIC_PERSISTENCE = "atomic_persistence"
ERROR_REPLAY_SIDECAR_PERSISTENCE = "replay_sidecar_persistence"
ERROR_FINAL_RESULT_PERSISTENCE = "final_result_persistence"
ERROR_VALUE_OTHER = "value_error_other"
ERROR_OS_OTHER = "operating_system_error_other"
ERROR_UNEXPECTED = "unexpected_error"
ALLOWED_LEDGER_ERROR_FAMILIES = frozenset(
    {
        ERROR_NONE,
        ERROR_RUN_RESULT_NOT_READY,
        ERROR_MANIFEST_ADMISSION,
        ERROR_PROCESS_LOCK_BUSY,
        ERROR_TERMINAL_AUTHORITY,
        ERROR_REPLAY_VERIFICATION,
        ERROR_REPLAY_BINDING,
        ERROR_ATOMIC_PERSISTENCE,
        ERROR_REPLAY_SIDECAR_PERSISTENCE,
        ERROR_FINAL_RESULT_PERSISTENCE,
        ERROR_VALUE_OTHER,
        ERROR_OS_OTHER,
        ERROR_UNEXPECTED,
    }
)
WORKER_LIVENESS_ALIVE = "alive"
WORKER_LIVENESS_NOT_ALIVE = "not_alive"
WORKER_LIVENESS_NOT_REGISTERED = "not_registered"
WORKER_LIVENESS_UNKNOWN = "unknown"
ALLOWED_WORKER_LIVENESS = frozenset(
    {
        WORKER_LIVENESS_ALIVE,
        WORKER_LIVENESS_NOT_ALIVE,
        WORKER_LIVENESS_NOT_REGISTERED,
        WORKER_LIVENESS_UNKNOWN,
    }
)
RESULT_ERROR_RUN_RESULT_NOT_READY = "run_result_not_ready"
RESULT_ERROR_MANIFEST_ADMISSION = "manifest_admission_failure"
RESULT_ERROR_TERMINAL_RECOVERY = "terminal_recovery_failure"
RESULT_ERROR_OTHER_SAFE = "other_safe_failure"
RESULT_ERROR_CODE_KEYS = (
    RESULT_ERROR_RUN_RESULT_NOT_READY,
    RESULT_ERROR_MANIFEST_ADMISSION,
    RESULT_ERROR_TERMINAL_RECOVERY,
    RESULT_ERROR_OTHER_SAFE,
)
ALLOWED_RESULT_ERROR_CODES = frozenset(RESULT_ERROR_CODE_KEYS)
MCP_TIMING_FIELDS = frozenset(
    {
        "call_count",
        "total_ms",
        "maximum_ms",
        "timeout_count",
        "error_count",
        "baseline_call_count",
        "baseline_total_ms",
        "baseline_maximum_ms",
        "baseline_timeout_count",
        "baseline_error_count",
    }
)
CONTINUATION_DIAGNOSTIC_FIELDS = frozenset(
    {
        "diagnostic_inspection_status",
        "first_lifecycle_state",
        "last_lifecycle_state",
        "status_observation_count",
        "last_progress_sequence",
        "last_progress_phase",
        "stale_epoch0_result_observation_count",
        "result_read_error_count",
        "status_read_error_count",
        "provider_call_delta",
        "loopback_provider_error_count",
        "mcp_liveness",
        "opening_resume_decision_present",
        "durable_terminal_epoch",
        "terminal_draft_count",
        "terminal_commitment_count",
        "latest_commitment_epoch",
        "commitment_inclusive_replay_binding_present",
        "durable_result_binding",
        "terminalization_last_entered_phase",
        "terminalization_last_returned_phase",
        "terminalization_last_error_phase",
        "terminalization_last_error_family",
        "terminalization_phase_entry_counts",
        "terminalization_phase_return_counts",
        "terminalization_phase_error_counts",
        "terminalization_phase_total_ms",
        "terminalization_ledger_overflow",
        "terminal_lock_acquire_count",
        "terminal_lock_wait_total_ms",
        "terminal_lock_wait_max_ms",
        "worker_liveness",
        "terminal_publication_recovery_required_observed",
        "result_error_code_counts",
        "mcp_status_timing",
        "mcp_result_timing",
        "continuation_elapsed_ms",
        "application_recovery_interference_observed",
        "application_recovery_last_entered_phase",
    }
)
FAILURE_RECORD_FIELDS = frozenset(
    {
        "schema",
        "platform_family",
        "stage",
        "failure_kind",
        "timeout",
        "cleanup_completed",
        "exit_status",
        "detail_code",
        "durable_progress",
        *ALLOWED_STATE_PRESENCE_FIELDS,
        *CONTINUATION_DIAGNOSTIC_FIELDS,
    }
)


def _nonnegative_integer_or_none(value, *, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TypeError(f"{field} must be a non-negative integer or null")
    return value


def _zero_phase_mapping() -> dict[str, int]:
    return {phase: 0 for phase in DIAGNOSTIC_LEDGER_PHASES}


def _zero_result_error_counts() -> dict[str, int]:
    return {key: 0 for key in RESULT_ERROR_CODE_KEYS}


def _empty_mcp_timing() -> dict[str, int]:
    return {field: 0 for field in sorted(MCP_TIMING_FIELDS)}


def _default_continuation_diagnostic() -> dict[str, object]:
    return {
        "diagnostic_inspection_status": (
            DIAGNOSTIC_INSPECTION_NOT_ATTEMPTED
        ),
        "first_lifecycle_state": LIFECYCLE_NOT_OBSERVED,
        "last_lifecycle_state": LIFECYCLE_NOT_OBSERVED,
        "status_observation_count": 0,
        "last_progress_sequence": None,
        "last_progress_phase": PHASE_NOT_OBSERVED,
        "stale_epoch0_result_observation_count": 0,
        "result_read_error_count": 0,
        "status_read_error_count": 0,
        "provider_call_delta": None,
        "loopback_provider_error_count": None,
        "mcp_liveness": MCP_LIVENESS_NOT_STARTED,
        "opening_resume_decision_present": None,
        "durable_terminal_epoch": None,
        "terminal_draft_count": None,
        "terminal_commitment_count": None,
        "latest_commitment_epoch": None,
        "commitment_inclusive_replay_binding_present": None,
        "durable_result_binding": RESULT_BINDING_UNKNOWN,
        "terminalization_last_entered_phase": (
            TERMINALIZATION_NOT_OBSERVED
        ),
        "terminalization_last_returned_phase": (
            TERMINALIZATION_NOT_OBSERVED
        ),
        "terminalization_last_error_phase": (
            TERMINALIZATION_NOT_OBSERVED
        ),
        "terminalization_last_error_family": ERROR_NONE,
        "terminalization_phase_entry_counts": _zero_phase_mapping(),
        "terminalization_phase_return_counts": _zero_phase_mapping(),
        "terminalization_phase_error_counts": _zero_phase_mapping(),
        "terminalization_phase_total_ms": _zero_phase_mapping(),
        "terminalization_ledger_overflow": False,
        "terminal_lock_acquire_count": 0,
        "terminal_lock_wait_total_ms": 0,
        "terminal_lock_wait_max_ms": 0,
        "worker_liveness": WORKER_LIVENESS_UNKNOWN,
        "terminal_publication_recovery_required_observed": False,
        "result_error_code_counts": _zero_result_error_counts(),
        "mcp_status_timing": _empty_mcp_timing(),
        "mcp_result_timing": _empty_mcp_timing(),
        "continuation_elapsed_ms": None,
        "application_recovery_interference_observed": False,
        "application_recovery_last_entered_phase": (
            TERMINALIZATION_NOT_OBSERVED
        ),
    }


def _validated_continuation_diagnostic(
    values: dict[str, object] | None,
) -> dict[str, object]:
    diagnostic = _default_continuation_diagnostic()
    if values is not None:
        if set(values) != CONTINUATION_DIAGNOSTIC_FIELDS:
            raise ValueError("continuation diagnostic field inventory drifted")
        diagnostic.update(values)
    if (
        diagnostic["diagnostic_inspection_status"]
        not in ALLOWED_DIAGNOSTIC_INSPECTION_STATUSES
    ):
        raise ValueError("invalid diagnostic inspection status")
    if diagnostic["first_lifecycle_state"] not in ALLOWED_DIAGNOSTIC_LIFECYCLES:
        raise ValueError("invalid first lifecycle state")
    if diagnostic["last_lifecycle_state"] not in ALLOWED_DIAGNOSTIC_LIFECYCLES:
        raise ValueError("invalid last lifecycle state")
    if diagnostic["last_progress_phase"] not in ALLOWED_DIAGNOSTIC_PHASES:
        raise ValueError("invalid progress phase")
    if diagnostic["mcp_liveness"] not in ALLOWED_MCP_LIVENESS:
        raise ValueError("invalid MCP liveness")
    if diagnostic["durable_result_binding"] not in ALLOWED_RESULT_BINDINGS:
        raise ValueError("invalid durable result binding")
    for field in (
        "terminalization_last_entered_phase",
        "terminalization_last_returned_phase",
        "terminalization_last_error_phase",
        "application_recovery_last_entered_phase",
    ):
        if diagnostic[field] not in ALLOWED_TERMINALIZATION_OBSERVATIONS:
            raise ValueError(f"invalid {field}")
    if (
        diagnostic["terminalization_last_error_family"]
        not in ALLOWED_LEDGER_ERROR_FAMILIES
    ):
        raise ValueError("invalid terminalization error family")
    for field in (
        "terminalization_phase_entry_counts",
        "terminalization_phase_return_counts",
        "terminalization_phase_error_counts",
        "terminalization_phase_total_ms",
    ):
        mapping = diagnostic[field]
        if not isinstance(mapping, dict) or set(mapping) != set(
            DIAGNOSTIC_LEDGER_PHASES
        ):
            raise ValueError(f"{field} inventory drifted")
        for phase, value in mapping.items():
            mapping[phase] = _nonnegative_integer_or_none(
                value, field=f"{field}.{phase}"
            )
            assert mapping[phase] is not None
    result_errors = diagnostic["result_error_code_counts"]
    if not isinstance(result_errors, dict) or set(result_errors) != set(
        RESULT_ERROR_CODE_KEYS
    ):
        raise ValueError("result error code inventory drifted")
    for code, value in result_errors.items():
        result_errors[code] = _nonnegative_integer_or_none(
            value, field=f"result_error_code_counts.{code}"
        )
        assert result_errors[code] is not None
    for field in ("mcp_status_timing", "mcp_result_timing"):
        timing = diagnostic[field]
        if not isinstance(timing, dict) or set(timing) != MCP_TIMING_FIELDS:
            raise ValueError(f"{field} inventory drifted")
        for key, value in timing.items():
            timing[key] = _nonnegative_integer_or_none(
                value, field=f"{field}.{key}"
            )
            assert timing[key] is not None
        if timing["maximum_ms"] > timing["total_ms"]:
            raise ValueError(f"{field} maximum exceeds total")
        if timing["baseline_maximum_ms"] > timing["baseline_total_ms"]:
            raise ValueError(f"{field} baseline maximum exceeds total")
        if timing["error_count"] > timing["call_count"]:
            raise ValueError(f"{field} error count exceeds calls")
        if timing["timeout_count"] > timing["error_count"]:
            raise ValueError(f"{field} timeout count exceeds errors")
        if timing["baseline_error_count"] > timing["baseline_call_count"]:
            raise ValueError(f"{field} baseline errors exceed calls")
        if timing["baseline_timeout_count"] > timing["baseline_error_count"]:
            raise ValueError(f"{field} baseline timeouts exceed errors")
    if diagnostic["worker_liveness"] not in ALLOWED_WORKER_LIVENESS:
        raise ValueError("invalid worker liveness")
    for field in (
        "status_observation_count",
        "last_progress_sequence",
        "stale_epoch0_result_observation_count",
        "result_read_error_count",
        "status_read_error_count",
        "provider_call_delta",
        "loopback_provider_error_count",
        "durable_terminal_epoch",
        "terminal_draft_count",
        "terminal_commitment_count",
        "latest_commitment_epoch",
        "terminal_lock_acquire_count",
        "terminal_lock_wait_total_ms",
        "terminal_lock_wait_max_ms",
        "continuation_elapsed_ms",
    ):
        diagnostic[field] = _nonnegative_integer_or_none(
            diagnostic[field], field=field
        )
    if (
        diagnostic["terminal_lock_wait_max_ms"]
        > diagnostic["terminal_lock_wait_total_ms"]
    ):
        raise ValueError("terminal lock maximum exceeds total")
    for field in (
        "opening_resume_decision_present",
        "commitment_inclusive_replay_binding_present",
    ):
        if diagnostic[field] is not None and type(diagnostic[field]) is not bool:
            raise TypeError(f"{field} must be boolean or null")
    for field in (
        "terminalization_ledger_overflow",
        "terminal_publication_recovery_required_observed",
        "application_recovery_interference_observed",
    ):
        if type(diagnostic[field]) is not bool:
            raise TypeError(f"{field} must be boolean")
    return diagnostic


class ContinuationObservations:
    """Payload-free in-memory observations from one accepted continuation."""

    def __init__(self) -> None:
        self.first_lifecycle_state = LIFECYCLE_NOT_OBSERVED
        self.last_lifecycle_state = LIFECYCLE_NOT_OBSERVED
        self.status_observation_count = 0
        self.last_progress_sequence: int | None = None
        self.last_progress_phase = PHASE_NOT_OBSERVED
        self.stale_epoch0_result_observation_count = 0
        self.result_read_error_count = 0
        self.status_read_error_count = 0
        self.result_error_code_counts = _zero_result_error_counts()
        self.mcp_status_timing = _empty_mcp_timing()
        self.mcp_result_timing = _empty_mcp_timing()
        self.continuation_accepted_at: float | None = None
        self.continuation_elapsed_ms: int | None = None
        self.terminal_publication_recovery_required_observed = False
        self.diagnostic_collection_failed = False

    def mark_continuation_accepted(self, observed_at: float) -> None:
        if isinstance(observed_at, bool) or not isinstance(
            observed_at, (int, float)
        ):
            raise TypeError("continuation acceptance time must be numeric")
        self.continuation_accepted_at = float(observed_at)
        self.continuation_elapsed_ms = None

    def finish_continuation(self, observed_at: float) -> None:
        if self.continuation_accepted_at is None:
            self.mark_continuation_accepted(observed_at)
        elapsed = max(0.0, float(observed_at) - self.continuation_accepted_at)
        self.continuation_elapsed_ms = min(
            int(elapsed * 1000),
            86_400_000,
        )

    def observe_call(
        self,
        operation: str,
        *,
        elapsed_ms: int,
        baseline: bool,
        error: bool,
        timeout: bool,
    ) -> None:
        if operation == "run_status":
            timing = self.mcp_status_timing
        elif operation == "run_result":
            timing = self.mcp_result_timing
        else:
            raise ValueError("unsupported timed MCP operation")
        elapsed = _nonnegative_integer_or_none(
            elapsed_ms, field="MCP call elapsed time"
        )
        assert elapsed is not None
        prefix = "baseline_" if baseline else ""
        timing[f"{prefix}call_count"] += 1
        timing[f"{prefix}total_ms"] += elapsed
        maximum = f"{prefix}maximum_ms"
        timing[maximum] = max(timing[maximum], elapsed)
        timing[f"{prefix}error_count"] += int(error)
        timing[f"{prefix}timeout_count"] += int(timeout)

    def observe_result_error(self, classification: str) -> None:
        if classification not in ALLOWED_RESULT_ERROR_CODES:
            classification = RESULT_ERROR_OTHER_SAFE
        self.result_read_error_count += 1
        self.result_error_code_counts[classification] += 1

    def observe_status(self, status: dict) -> None:
        lifecycle = _LIFECYCLE_MAP.get(
            status.get("state"), LIFECYCLE_UNKNOWN
        )
        if self.status_observation_count == 0:
            self.first_lifecycle_state = lifecycle
        self.last_lifecycle_state = lifecycle
        self.status_observation_count += 1
        sequence = status.get("seq")
        if (
            isinstance(sequence, int)
            and not isinstance(sequence, bool)
            and sequence >= 0
        ):
            self.last_progress_sequence = sequence
        self.last_progress_phase = _PHASE_MAP.get(
            status.get("phase"), PHASE_UNKNOWN
        )

    def snapshot(self) -> dict[str, object]:
        values = _default_continuation_diagnostic()
        values.update(
            {
                "diagnostic_inspection_status": (
                    DIAGNOSTIC_INSPECTION_FAILED
                    if self.diagnostic_collection_failed
                    else DIAGNOSTIC_INSPECTION_NOT_ATTEMPTED
                ),
                "first_lifecycle_state": self.first_lifecycle_state,
                "last_lifecycle_state": self.last_lifecycle_state,
                "status_observation_count": self.status_observation_count,
                "last_progress_sequence": self.last_progress_sequence,
                "last_progress_phase": self.last_progress_phase,
                "stale_epoch0_result_observation_count": (
                    self.stale_epoch0_result_observation_count
                ),
                "result_read_error_count": self.result_read_error_count,
                "status_read_error_count": self.status_read_error_count,
                "result_error_code_counts": dict(
                    self.result_error_code_counts
                ),
                "mcp_status_timing": dict(self.mcp_status_timing),
                "mcp_result_timing": dict(self.mcp_result_timing),
                "continuation_elapsed_ms": self.continuation_elapsed_ms,
                "terminal_publication_recovery_required_observed": (
                    self.terminal_publication_recovery_required_observed
                ),
            }
        )
        return _validated_continuation_diagnostic(values)


class ContinuationDiagnosticContext:
    """Private inputs for one bounded, read-only continuation inspection."""

    def __init__(
        self,
        *,
        python: Path,
        work: Path,
        env: dict[str, str],
        run_root: Path,
        prior_terminal_commitment_ref: str,
        provider_state_path: Path,
        provider_call_baseline: int,
        observations: ContinuationObservations,
        terminal_phase_ledger_path: Path | None = None,
    ) -> None:
        self.python = Path(python)
        self.work = Path(work)
        self.env = dict(env)
        self.run_root = Path(run_root)
        self.prior_terminal_commitment_ref = prior_terminal_commitment_ref
        self.provider_state_path = Path(provider_state_path)
        self.provider_call_baseline = _nonnegative_integer_or_none(
            provider_call_baseline, field="provider call baseline"
        )
        assert self.provider_call_baseline is not None
        self.observations = observations
        self.terminal_phase_ledger_path = (
            None
            if terminal_phase_ledger_path is None
            else Path(terminal_phase_ledger_path)
        )


class OperationalSmokeFailure(Exception):
    """Fixed, payload-free operational failure."""

    def __init__(
        self,
        *,
        stage: str,
        failure_kind: str,
        exit_status: int | None = None,
        timeout: bool = False,
        detail_code: str | None = None,
        durable_progress: str | None = None,
        state_presence: dict[str, bool] | None = None,
        continuation_diagnostic: dict[str, object] | None = None,
    ) -> None:
        if stage not in ALLOWED_FAILURE_STAGES:
            raise ValueError("invalid fixed operational stage")
        if failure_kind not in ALLOWED_FAILURE_KINDS:
            raise ValueError("invalid fixed operational failure kind")
        exit_status = _nonnegative_integer_or_none(
            exit_status, field="operational exit status"
        )
        if not isinstance(timeout, bool):
            raise TypeError("operational timeout status must be boolean")
        if detail_code is not None and detail_code not in ALLOWED_DETAIL_CODES:
            raise ValueError("invalid fixed operational detail code")
        if (
            durable_progress is not None
            and durable_progress not in ALLOWED_DURABLE_PROGRESS
        ):
            raise ValueError("invalid fixed durable progress")
        fixed_state = dict(state_presence or {})
        if not set(fixed_state) <= ALLOWED_STATE_PRESENCE_FIELDS:
            raise ValueError("invalid fixed state-presence field")
        if any(type(value) is not bool for value in fixed_state.values()):
            raise TypeError("state-presence values must be boolean")
        self.stage = stage
        self.failure_kind = failure_kind
        self.exit_status = exit_status
        self.timeout = timeout
        self.detail_code = detail_code
        self.durable_progress = durable_progress
        self.state_presence = {
            key: fixed_state[key] for key in sorted(fixed_state)
        }
        self.continuation_diagnostic = _validated_continuation_diagnostic(
            continuation_diagnostic
        )
        super().__init__(
            json.dumps(
                _diagnostic_record(self, cleanup_completed=None),
                sort_keys=True,
                separators=(",", ":"),
            )
        )

    def attach_continuation_diagnostic(
        self, diagnostic: dict[str, object]
    ) -> None:
        self.continuation_diagnostic = _validated_continuation_diagnostic(
            diagnostic
        )
        self.args = (
            json.dumps(
                _diagnostic_record(self, cleanup_completed=None),
                sort_keys=True,
                separators=(",", ":"),
            ),
        )


def _classify_result_error_text(text: object) -> str:
    """Reduce one MCP-safe error to a fixed result-read classification."""

    if not isinstance(text, str) or len(text) > 512:
        return RESULT_ERROR_OTHER_SAFE
    matched = re.fullmatch(
        r"([A-Za-z_][A-Za-z0-9_]{0,127}): ([A-Z][A-Z0-9_]{2,127})",
        text,
    )
    if matched is None:
        return RESULT_ERROR_OTHER_SAFE
    error_type, code = matched.groups()
    if code == "RUN_RESULT_NOT_READY":
        return RESULT_ERROR_RUN_RESULT_NOT_READY
    if error_type in {
        "RunManifestError",
        "UnsupportedRunManifestVersionError",
    } or code.startswith(
        (
            "RUN_MANIFEST_",
            "MANIFEST_",
            "V6_RUN_MANIFEST_",
            "RUN_INPUT_",
        )
    ):
        return RESULT_ERROR_MANIFEST_ADMISSION
    if code.startswith("TERMINAL_"):
        return RESULT_ERROR_TERMINAL_RECOVERY
    return RESULT_ERROR_OTHER_SAFE


class _MCPToolResponseError(OperationalSmokeFailure):
    """Payload-free signal for an expected MCP tool error response."""

    def __init__(
        self,
        *,
        stage: str,
        result_error_classification: str = RESULT_ERROR_OTHER_SAFE,
    ) -> None:
        if result_error_classification not in ALLOWED_RESULT_ERROR_CODES:
            result_error_classification = RESULT_ERROR_OTHER_SAFE
        self.result_error_classification = result_error_classification
        super().__init__(
            stage=stage,
            failure_kind=FAILURE_ASSERTION,
        )


def _resolve_ref(schema: dict, root: dict) -> dict:
    reference = schema.get("$ref")
    if not reference:
        return schema
    value = root
    for component in reference.removeprefix("#/").split("/"):
        value = value[component]
    return value


def _schema_value(schema: dict, root: dict, *, field: str = "value"):
    schema = _resolve_ref(schema, root)
    if "const" in schema:
        return schema["const"]
    if schema.get("enum"):
        return schema["enum"][0]
    alternatives = schema.get("anyOf") or schema.get("oneOf")
    if alternatives:
        selected = next(
            (item for item in alternatives if item.get("type") != "null"),
            alternatives[0],
        )
        return _schema_value(selected, root, field=field)
    if schema.get("allOf"):
        return _schema_value(schema["allOf"][0], root, field=field)
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        return {
            name: _schema_value(properties[name], root, field=name)
            for name in schema.get("required", [])
        }
    if kind == "array":
        count = max(0, int(schema.get("minItems", 0)))
        return [
            _schema_value(schema.get("items", {}), root, field=field)
            for _ in range(count)
        ]
    if kind == "boolean":
        return False
    if kind == "integer":
        return int(schema.get("minimum", 0))
    if kind == "number":
        minimum = float(schema.get("minimum", 0.0))
        maximum = schema.get("maximum")
        return min(maximum, max(minimum, 0.5)) if maximum is not None else max(minimum, 0.5)
    if kind == "null":
        return None
    pattern = str(schema.get("pattern") or "")
    if "sha256" in pattern:
        return "sha256:" + "1" * 64
    if "[0-9a-f]{64}" in pattern:
        return "1" * 64
    if "NEW" in pattern:
        return "NEW_001"
    if "SCR" in pattern:
        return "SCR_001"
    if field == "values_json":
        return "{}"
    return "deterministic fixture value"


def response_for_schema(schema: dict, prompt: str) -> dict:
    """Return one semantically conservative value for an advertised schema."""

    title = schema.get("title")
    if (
        "typed resumable stop" in prompt.casefold()
        and title in {"ConjecturerTurnWireV6", "ReasoningConjecturerTurnWireV6"}
    ):
        return {
            "candidates": [],
            "context_request": None,
            "abstention": {
                "search_signal": "stuck",
                "note": "No further proposal is warranted for this bounded fixture.",
            },
        }
    if title == "BatchCriticWireV2":
        case_schema = schema["$defs"]["BatchCriticCaseWireV2"]
        aliases = case_schema["properties"]["target_alias"].get("enum", [])
        return {
            "cases": [
                {"target_alias": alias, "attack": False, "case": ""}
                for alias in aliases
            ]
        }
    if title == "AtomicConjectureCandidateWireV1":
        return {
            "candidate": {
                "content": "A deterministic, criticizable loopback explanation.",
                "typicality": 0.5,
                "neighbours": [],
            },
            "abstention": None,
        }
    if title == "AtomicReasoningConjectureCandidateWireV1":
        return {
            "candidate": {
                "claim": "A deterministic, criticizable loopback explanation.",
                "mechanism": "Recorded causes expose a bounded test surface.",
                "counterconditions": ["A contradictory durable record."],
                "typicality": 0.5,
            },
            "abstention": None,
        }
    exact = re.search(
        r"return exactly\s+([0-9]+)\s+diverse candidates",
        prompt,
        flags=re.IGNORECASE,
    )
    candidate_count = int(exact.group(1)) if exact else 1
    candidates = [
        {
            "content": (
                "A deterministic, criticizable loopback explanation "
                f"with test surface {index + 1}."
            ),
            "typicality": max(0.1, 0.8 - index * 0.1),
            "neighbours": [],
        }
        for index in range(candidate_count)
    ]
    reasoning_candidates = [
        {
            "claim": (
                "A deterministic, criticizable loopback claim "
                f"with test surface {index + 1}."
            ),
            "mechanism": "Recorded causes expose a bounded test surface.",
            "counterconditions": ["A contradictory durable record."],
            "typicality": max(0.1, 0.8 - index * 0.1),
        }
        for index in range(candidate_count)
    ]
    if title == "ConjecturerTurnWireV6":
        return {
            "candidates": candidates,
            "context_request": None,
            "abstention": None,
        }
    if title == "ReasoningConjecturerTurnWireV6":
        return {
            "candidates": reasoning_candidates,
            "context_request": None,
            "abstention": None,
        }
    if title == "BoundCompactCritic":
        target = schema["properties"]["target_alias"]["const"]
        return {
            "attack": False,
            "target_alias": target,
            "claim": "",
            "grounds": "",
            "cited_input_aliases": [],
        }
    if title in {"ConjecturerOutput", "CompactConjecturerOutput"}:
        return {"candidates": candidates}
    if title == "ReasoningConjecturerOutput":
        return {"candidates": reasoning_candidates}
    value = _schema_value(schema, schema)
    if not isinstance(value, dict):
        raise AssertionError("provider fixture cannot satisfy advertised schema")
    return value


def _schema_from_request(body: dict, prompt: str) -> dict:
    response_format = body.get("response_format") or {}
    advertised = response_format.get("json_schema") or {}
    schema = advertised.get("schema")
    if isinstance(schema, dict):
        return schema
    marker_at = max(prompt.find("JSON Schema"), prompt.find("closed schema"))
    schema_at = prompt.find("{", marker_at)
    if marker_at < 0 or schema_at < 0:
        raise ValueError("loopback request did not advertise an output schema")
    decoded, _end = json.JSONDecoder().raw_decode(prompt[schema_at:])
    if not isinstance(decoded, dict):
        raise ValueError("loopback request output schema is not an object")
    return decoded


class ProviderState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.requests: list[dict[str, object]] = []

    def record(self, *, prompt: str, model: str, max_tokens: int | None) -> None:
        with self.lock:
            self.requests.append(
                {
                    "qualification": "Qualification case " in prompt,
                    "model": model,
                    "max_tokens": max_tokens,
                }
            )

    @property
    def qualification_calls(self) -> int:
        with self.lock:
            return sum(bool(item["qualification"]) for item in self.requests)

    @property
    def total_calls(self) -> int:
        with self.lock:
            return len(self.requests)


def _provider_server(state: ProviderState):
    class Handler(BaseHTTPRequestHandler):
        server_version = "DeepReasonLoopback/1"

        def log_message(self, _format, *_args):
            return

        def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
            try:
                if self.path != "/v1/chat/completions":
                    self.send_error(404)
                    return
                if self.headers.get("Authorization") != f"Bearer {TEST_CREDENTIAL}":
                    self.send_error(401)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length))
                prompt = body["messages"][0]["content"]
                if not isinstance(prompt, str):
                    raise ValueError("loopback fixture accepts text requests only")
                schema = _schema_from_request(body, prompt)
                response = response_for_schema(schema, prompt)
                content = json.dumps(response, sort_keys=True, separators=(",", ":"))
                state.record(
                    prompt=prompt,
                    model=str(body.get("model")),
                    max_tokens=body.get("max_tokens"),
                )
                payload = {
                    "id": "chatcmpl-deepreason-loopback",
                    "object": "chat.completion",
                    "created": 0,
                    "model": body.get("model"),
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": content},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": max(1, len(prompt) // 4),
                        "completion_tokens": max(1, len(content) // 4),
                        "total_tokens": max(2, (len(prompt) + len(content)) // 4),
                    },
                }
                encoded = json.dumps(payload, separators=(",", ":")).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
            except Exception:  # fixture failures must fail the real call
                encoded = json.dumps(
                    {
                        "error": {
                            "type": "loopback_fixture_failure",
                            "message": "loopback fixture request failed",
                        }
                    }
                ).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _environment(
    home: Path, *, provider_port: int, provider_state_path: Path
) -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop(LOOPBACK_READY_ENV, None)
    environment.pop(TERMINAL_DIAGNOSTIC_ENABLE_ENV, None)
    environment.pop(TERMINAL_DIAGNOSTIC_LEDGER_ENV, None)
    environment["HOME"] = str(home)
    environment["USERPROFILE"] = str(home)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment[TEST_CREDENTIAL_ENV] = TEST_CREDENTIAL
    environment["DEEPREASON_WHEEL_LOOPBACK_FIXTURE"] = "1"
    environment["DEEPREASON_WHEEL_LOOPBACK_PORT"] = str(provider_port)
    environment["DEEPREASON_WHEEL_LOOPBACK_STATE"] = str(provider_state_path)
    environment["NO_PROXY"] = "127.0.0.1,localhost"
    environment["no_proxy"] = "127.0.0.1,localhost"
    environment.pop("DEEPREASON_PROFILE", None)
    environment.pop("DEEPREASON_HOME", None)
    return environment


def _unused_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _provider_counts(path: Path) -> dict[str, int]:
    if not path.exists():
        return {"qualification_calls": 0, "total_calls": 0}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "qualification_calls": int(payload["qualification_calls"]),
        "total_calls": int(payload["total_calls"]),
    }


def _assert_no_incremental_provider_calls(path: Path, before: int) -> None:
    if _provider_counts(path)["total_calls"] != before:
        raise AssertionError("zero-call operation dispatched to the provider")


def _install_loopback_fixture(
    *,
    repo: Path,
    python: Path,
    work: Path,
    env: dict[str, str],
    stage: str,
) -> Path:
    purelib = Path(
        _run(
            [
                str(python),
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ],
            cwd=work,
            env=env,
            stage=stage,
        ).stdout.strip()
    )
    target = purelib / "sitecustomize.py"
    shutil.copyfile(repo / "scripts" / "wheel_loopback_sitecustomize.py", target)
    return target


def _venv_executable(root: Path, name: str) -> Path:
    directory = root / ("Scripts" if os.name == "nt" else "bin")
    suffix = ".exe" if os.name == "nt" else ""
    return directory / f"{name}{suffix}"


def _is_regular_file(path: Path) -> bool:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(observed.st_mode)


def _managed_run_roots(home: Path) -> frozenset[Path]:
    runs = home / ".deepreason" / "runs"
    try:
        entries = tuple(runs.iterdir())
    except FileNotFoundError:
        return frozenset()
    roots = []
    for entry in entries:
        observed = entry.lstat()
        if stat.S_ISDIR(observed.st_mode) and not entry.name.startswith("."):
            roots.append(entry)
    return frozenset(roots)


def _reason_state_presence(
    *,
    home: Path,
    ready_marker: Path,
    roots_before: frozenset[Path] | None,
) -> tuple[dict[str, bool], str]:
    if roots_before is None:
        raise OSError("reason state baseline was unavailable")
    roots = _managed_run_roots(home) - roots_before
    state = {
        STATE_RUN_ROOT_PRESENT: bool(roots),
        STATE_PREPARATION_PRESENT: any(
            _is_regular_file(root / "run-preparation.json") for root in roots
        ),
        STATE_MANIFEST_PRESENT: any(
            _is_regular_file(root / "run-manifest.json") for root in roots
        ),
        STATE_MANAGED_REGISTRATION_PRESENT: any(
            _is_regular_file(root / "run-request.json") for root in roots
        ),
        STATE_PROGRESS_LOG_PRESENT: any(
            _is_regular_file(root / "progress.jsonl") for root in roots
        ),
        STATE_EVENT_LOG_PRESENT: any(
            _is_regular_file(root / "log.jsonl") for root in roots
        ),
        STATE_TERMINAL_RESULT_PRESENT: any(
            _is_regular_file(root / "run-result.json") for root in roots
        ),
        STATE_LOOPBACK_START_PRESENT: _is_regular_file(ready_marker),
    }
    if state[STATE_TERMINAL_RESULT_PRESENT]:
        durable = DURABLE_TERMINAL_RESULT_PRESENT
    elif state[STATE_EVENT_LOG_PRESENT]:
        durable = DURABLE_EVENT_LOG_PRESENT
    elif (
        state[STATE_MANAGED_REGISTRATION_PRESENT]
        or state[STATE_PROGRESS_LOG_PRESENT]
    ):
        durable = DURABLE_MANAGED_REGISTRATION_PRESENT
    elif state[STATE_PREPARATION_PRESENT] or state[STATE_MANIFEST_PRESENT]:
        durable = DURABLE_PREPARATION_PRESENT
    elif state[STATE_RUN_ROOT_PRESENT]:
        durable = DURABLE_RUN_ROOT_PRESENT
    else:
        durable = DURABLE_PREPARATION_ABSENT
    return state, durable


def _typed_reason_code(stdout: str, stderr: str) -> str | None:
    for captured in (stderr, stdout):
        candidate = captured.strip()
        if candidate in ALLOWED_TYPED_REASON_CODES:
            return candidate
    return None


def _reason_failure(
    *,
    failure_kind: str,
    home: Path,
    ready_marker: Path,
    roots_before: frozenset[Path] | None,
    exit_status: int | None = None,
    stdout: str = "",
    stderr: str = "",
    timeout: bool = False,
    fixed_detail_code: str | None = None,
) -> OperationalSmokeFailure:
    typed_code = _typed_reason_code(stdout, stderr)
    detail_code = fixed_detail_code or typed_code
    try:
        state_presence, durable_progress = _reason_state_presence(
            home=home,
            ready_marker=ready_marker,
            roots_before=roots_before,
        )
    except PermissionError:
        state_presence = {}
        durable_progress = DURABLE_STATE_INSPECTION_UNAVAILABLE
        if detail_code is None:
            detail_code = DETAIL_FILESYSTEM_ACCESS_DENIED
    except OSError:
        state_presence = {}
        durable_progress = DURABLE_STATE_INSPECTION_UNAVAILABLE
        if detail_code is None:
            detail_code = DETAIL_UNKNOWN_REASON_FAILURE
    if detail_code is None:
        detail_code = (
            DETAIL_UNKNOWN_REASON_FAILURE
            if stdout or stderr
            else DETAIL_CHILD_EXIT_NONZERO
        )
    return OperationalSmokeFailure(
        stage=STAGE_REASON,
        failure_kind=failure_kind,
        exit_status=exit_status,
        timeout=timeout,
        detail_code=detail_code,
        durable_progress=durable_progress,
        state_presence=state_presence,
    )


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stage: str,
    expected: tuple[int, ...] = (0,),
    timeout: int = 600,
    _reason_context: tuple[Path, Path, frozenset[Path] | None] | None = None,
) -> subprocess.CompletedProcess[str]:
    if (stage == STAGE_REASON) != (_reason_context is not None):
        raise ValueError("reason stage must use the fixed diagnostic wrapper")
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        if _reason_context is not None:
            home, ready_marker, roots_before = _reason_context
            raise _reason_failure(
                failure_kind=FAILURE_TIMEOUT,
                home=home,
                ready_marker=ready_marker,
                roots_before=roots_before,
                timeout=True,
                fixed_detail_code=DETAIL_CHILD_TIMEOUT,
            ) from None
        raise OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_TIMEOUT,
            timeout=True,
        ) from None
    except FileNotFoundError:
        if _reason_context is None:
            raise
        home, ready_marker, roots_before = _reason_context
        raise _reason_failure(
            failure_kind=FAILURE_UNEXPECTED,
            home=home,
            ready_marker=ready_marker,
            roots_before=roots_before,
            fixed_detail_code=DETAIL_EXECUTABLE_RESOLUTION_FAILED,
        ) from None
    except OSError:
        if _reason_context is None:
            raise
        home, ready_marker, roots_before = _reason_context
        raise _reason_failure(
            failure_kind=FAILURE_UNEXPECTED,
            home=home,
            ready_marker=ready_marker,
            roots_before=roots_before,
            fixed_detail_code=DETAIL_CHILD_LAUNCH_FAILED,
        ) from None
    if completed.returncode not in expected:
        if _reason_context is not None:
            home, ready_marker, roots_before = _reason_context
            raise _reason_failure(
                failure_kind=FAILURE_COMMAND,
                home=home,
                ready_marker=ready_marker,
                roots_before=roots_before,
                exit_status=int(completed.returncode),
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        raise OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_COMMAND,
            exit_status=int(completed.returncode),
        )
    return completed


def _run_reason(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    home: Path,
    ready_marker: Path,
    expected: tuple[int, ...] = (0,),
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    try:
        roots_before: frozenset[Path] | None = _managed_run_roots(home)
    except OSError:
        roots_before = None
    reason_env = dict(env)
    reason_env[LOOPBACK_READY_ENV] = str(ready_marker)
    return _run(
        command,
        cwd=cwd,
        env=reason_env,
        stage=STAGE_REASON,
        expected=expected,
        timeout=timeout,
        _reason_context=(home, ready_marker, roots_before),
    )


class MCPClient:
    def __init__(
        self,
        executable: Path,
        *,
        cwd: Path,
        env: dict[str, str],
        stage: str = STAGE_MCP_INITIALIZE,
    ) -> None:
        try:
            self.process = subprocess.Popen(
                [str(executable)],
                cwd=cwd,
                env=env,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
            )
        except OSError:
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_UNEXPECTED,
            ) from None
        self._next_id = 1
        self.transcript: list[str] = []
        self._closed = False
        self.terminal_publication_recovery_required_observed = False

    def _raise_process_failure(self, *, stage: str) -> None:
        returncode = self.process.poll()
        if returncode is None:
            try:
                returncode = self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                raise OperationalSmokeFailure(
                    stage=stage,
                    failure_kind=FAILURE_TIMEOUT,
                    timeout=True,
                ) from None
        raise OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_COMMAND,
            exit_status=int(returncode),
        ) from None

    @staticmethod
    def _response_text(
        response: dict,
        *,
        stage: str,
    ) -> tuple[bool, str]:
        try:
            result = response["result"]
            text = result["content"][0]["text"]
        except (IndexError, KeyError, TypeError):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            ) from None
        if not isinstance(result, dict) or not isinstance(text, str):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            )
        is_error = result.get("isError", False)
        if not isinstance(is_error, bool):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            )
        return is_error, text

    def _observe_progress_notification(self, response: object) -> None:
        try:
            if not isinstance(response, dict) or response.get("method") != (
                "notifications/progress"
            ):
                return
            params = response.get("params")
            if (
                isinstance(params, dict)
                and params.get("message")
                == TERMINAL_PUBLICATION_RECOVERY_SENTINEL
            ):
                self.terminal_publication_recovery_required_observed = True
        except Exception:
            return

    def request(
        self,
        method: str,
        params: dict | None = None,
        *,
        stage: str = STAGE_MCP_REQUEST,
        deadline: float | None = None,
    ) -> dict:
        assert self.process.stdin is not None and self.process.stdout is not None
        request_id = self._next_id
        self._next_id += 1
        message = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        try:
            self.process.stdin.write(
                json.dumps(message, separators=(",", ":")) + "\n"
            )
            self.process.stdin.flush()
        except (BrokenPipeError, OSError, ValueError):
            self._raise_process_failure(stage=stage)
        while True:
            line = self._readline(stage=stage, deadline=deadline)
            if not line:
                self._raise_process_failure(stage=stage)
            self.transcript.append(line)
            try:
                response = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                raise OperationalSmokeFailure(
                    stage=stage,
                    failure_kind=FAILURE_ASSERTION,
                ) from None
            if not isinstance(response, dict):
                raise OperationalSmokeFailure(
                    stage=stage,
                    failure_kind=FAILURE_ASSERTION,
                )
            self._observe_progress_notification(response)
            if response.get("id") == request_id:
                return response

    def _readline(self, *, stage: str, deadline: float | None) -> str:
        assert self.process.stdout is not None
        if deadline is None:
            try:
                return self.process.stdout.readline()
            except (OSError, ValueError):
                self._raise_process_failure(stage=stage)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_TIMEOUT,
                timeout=True,
            )
        channel: queue.Queue[tuple[bool, str]] = queue.Queue(maxsize=1)

        def read_one_line() -> None:
            try:
                observed = self.process.stdout.readline()
            except (OSError, ValueError):
                outcome = (False, "")
            else:
                outcome = (True, observed)
            try:
                channel.put_nowait(outcome)
            except queue.Full:
                return

        threading.Thread(target=read_one_line, daemon=True).start()
        try:
            readable, line = channel.get(timeout=remaining)
        except queue.Empty:
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_TIMEOUT,
                timeout=True,
            ) from None
        if not readable:
            self._raise_process_failure(stage=stage)
        return line

    def tool(
        self,
        name: str,
        arguments: dict,
        *,
        stage: str = STAGE_MCP_REQUEST,
        deadline: float | None = None,
    ) -> dict:
        response = self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
            stage=stage,
            deadline=deadline,
        )
        is_error, text = self._response_text(response, stage=stage)
        if is_error:
            raise _MCPToolResponseError(
                stage=stage,
                result_error_classification=(
                    _classify_result_error_text(text)
                    if name == "run_result"
                    else RESULT_ERROR_OTHER_SAFE
                ),
            ) from None
        try:
            payload = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            ) from None
        if not isinstance(payload, dict):
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            )
        return payload

    def tool_error(
        self,
        name: str,
        arguments: dict,
        *,
        stage: str = STAGE_MCP_REQUEST,
        deadline: float | None = None,
    ) -> str:
        response = self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
            stage=stage,
            deadline=deadline,
        )
        is_error, text = self._response_text(response, stage=stage)
        if not is_error:
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_ASSERTION,
            )
        return text

    def close(self, *, stage: str = STAGE_MCP_REQUEST) -> None:
        if self._closed:
            return
        failure: OperationalSmokeFailure | None = None
        if self.process.stdin:
            try:
                self.process.stdin.close()
            except (OSError, ValueError):
                failure = OperationalSmokeFailure(
                    stage=stage,
                    failure_kind=FAILURE_UNEXPECTED,
                )
        returncode = self.process.poll()
        try:
            if returncode is None:
                try:
                    returncode = self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    if failure is None:
                        failure = OperationalSmokeFailure(
                            stage=stage,
                            failure_kind=FAILURE_TIMEOUT,
                            timeout=True,
                        )
                    try:
                        self.process.terminate()
                        returncode = self.process.wait(timeout=10)
                    except (
                        AttributeError,
                        OSError,
                        subprocess.TimeoutExpired,
                    ):
                        try:
                            self.process.kill()
                            returncode = self.process.wait(timeout=2)
                        except (
                            AttributeError,
                            OSError,
                            subprocess.TimeoutExpired,
                        ):
                            returncode = None
            if returncode is not None and returncode != 0 and failure is None:
                failure = OperationalSmokeFailure(
                    stage=stage,
                    failure_kind=FAILURE_COMMAND,
                    exit_status=(
                        int(returncode) if int(returncode) >= 0 else None
                    ),
                )
        finally:
            for stream_name in ("stdout", "stderr"):
                stream = getattr(self.process, stream_name, None)
                close_stream = getattr(stream, "close", None)
                if close_stream is None:
                    continue
                try:
                    close_stream()
                except (OSError, ValueError):
                    if failure is None:
                        failure = OperationalSmokeFailure(
                            stage=stage,
                            failure_kind=FAILURE_UNEXPECTED,
                        )
            try:
                self._closed = self.process.poll() is not None
            except Exception:
                self._closed = False
        if failure is not None:
            raise failure


def _build_wheel(repo: Path, temp_root: Path) -> Path:
    wheelhouse = temp_root / "wheelhouse"
    wheelhouse.mkdir()
    build_home = temp_root / "build home"
    build_home.mkdir()
    build_env = dict(os.environ)
    build_env.pop("PYTHONPATH", None)
    build_env["HOME"] = str(build_home)
    build_env["USERPROFILE"] = str(build_home)
    build_env["PYTHONNOUSERSITE"] = "1"
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                ".",
                "--no-deps",
                "--wheel-dir",
                str(wheelhouse),
            ],
            cwd=repo,
            env=build_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        raise OperationalSmokeFailure(
            stage=STAGE_BUILD_WHEEL,
            failure_kind=FAILURE_TIMEOUT,
            timeout=True,
        ) from None
    if completed.returncode:
        raise OperationalSmokeFailure(
            stage=STAGE_BUILD_WHEEL,
            failure_kind=FAILURE_COMMAND,
            exit_status=int(completed.returncode),
        )
    wheels = sorted(wheelhouse.glob("deepreason-*.whl"))
    if len(wheels) != 1:
        raise AssertionError("wheel build did not produce exactly one wheel")
    return wheels[0]


def _inspect_operational_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = {name.casefold() for name in archive.namelist()}
    required = {
        "deepreason/__main__.py",
        "deepreason/readiness.py",
        "deepreason/provider_profile.py",
        "deepreason/qualification.py",
        "deepreason/preparation.py",
        "deepreason/mcp_registration.py",
    }
    if not required <= names:
        raise AssertionError("operational wheel omits required installed modules")
    if any(
        name.startswith(("mini/", "minireason/", "tests/", "scripts/"))
        or "deterministic_provider" in name
        for name in names
    ):
        raise AssertionError("repository-only fixture, tests, or Mini entered the wheel")


def _assert_resumable_terminal(payload: dict) -> None:
    _assert_committed_terminal(payload)
    verification = payload.get("verification") or {}
    required = (
        "completion_satisfied",
        "epistemic_checks_passed",
        "operational_checks_passed",
    )
    if not all(verification.get(name) is True for name in required):
        raise AssertionError("terminal verification is incomplete")
    if payload.get("completion_status") != "satisfied":
        raise AssertionError("terminal completion was not satisfied")
    stop = payload.get("stop") or {}
    if stop.get("reason") != "converged":
        raise AssertionError("terminal is not a resumable convergence stop")


def _assert_non_resumable_rejection(text: str) -> None:
    if text.strip() not in {
        "CONTINUE_TYPED_STOP_REQUIRED",
        "ValueError: CONTINUE_TYPED_STOP_REQUIRED",
    }:
        raise AssertionError("completed non-resumable run was not rejected")


def _assert_committed_terminal(payload: dict) -> None:
    if payload.get("schema") != "deepreason-run-result-v2":
        raise AssertionError("terminal result schema is not V6")
    if payload.get("state") != "completed":
        raise AssertionError("reasoning did not complete")
    verification = payload.get("verification") or {}
    for field in ("valid", "integrity_valid", "security_valid"):
        if verification.get(field) is not True:
            raise AssertionError("terminal verification failed")
    if not str(payload.get("terminal_commitment_ref", "")).startswith("sha256:"):
        raise AssertionError("terminal result lacks durable terminal authority")


def _assert_durable_replay(home: Path, run_id: str) -> None:
    replay_path = home / ".deepreason" / "runs" / run_id / "REPLAY_VALIDATION.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    if replay.get("schema") != "replay-validation.v1" or replay.get("valid") is not True:
        raise AssertionError("durable replay verification failed")
    if not re.fullmatch(r"[0-9a-f]{64}", str(replay.get("manifest_digest", ""))):
        raise AssertionError("durable replay omitted its exact manifest digest")


def _tool_list(client: MCPClient) -> list[dict]:
    initialized = client.request("initialize", {}, stage=STAGE_MCP_INITIALIZE)
    if initialized["result"]["serverInfo"]["name"] != "deepreason":
        raise AssertionError("installed MCP server identity drifted")
    return client.request(
        "tools/list",
        stage=STAGE_MCP_INITIALIZE,
    )["result"]["tools"]


def _assert_exact_tools(tools: list[dict]) -> None:
    names = tuple(tool["name"] for tool in tools)
    if names != EXPECTED_MCP_TOOLS:
        raise AssertionError("MCP tool inventory drifted")
    encoded = json.dumps(tools, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != EXPECTED_MCP_SCHEMA_SHA256:
        raise AssertionError("MCP schemas differ from the accepted public facade")
    lowered = encoded.decode().casefold()
    for forbidden in (
        '"root"',
        "run_manifest_ref",
        "manifest_path",
        "provider_profile",
        "credential_env",
        "api_key",
    ):
        if forbidden in lowered:
            raise AssertionError("MCP schema exposes forbidden authority")


def _timed_mcp_tool(
    client: MCPClient,
    operation: str,
    arguments: dict,
    *,
    stage: str,
    observations: ContinuationObservations,
    baseline: bool,
    deadline: float | None = None,
    _timer=None,
) -> dict:
    timer = _timer or time.perf_counter
    try:
        started = timer()
    except BaseException:
        started = None
        observations.diagnostic_collection_failed = True

    def observe(*, error: bool, timeout: bool) -> None:
        try:
            elapsed = (
                max(0, int((timer() - started) * 1000))
                if started is not None
                else 0
            )
            observations.observe_call(
                operation,
                elapsed_ms=elapsed,
                baseline=baseline,
                error=error,
                timeout=timeout,
            )
        except BaseException:
            try:
                observations.diagnostic_collection_failed = True
            except BaseException:
                pass

    try:
        payload = client.tool(
            operation,
            arguments,
            stage=stage,
            deadline=deadline,
        )
    except OperationalSmokeFailure as error:
        observe(error=True, timeout=error.timeout)
        raise
    except BaseException:
        observe(error=True, timeout=False)
        raise
    observe(error=False, timeout=False)
    return payload


def _poll_terminal(
    client: MCPClient,
    run_id: str,
    *,
    prior_terminal_commitment_ref: str | None = None,
    stage: str = STAGE_MCP_REQUEST,
    observations: ContinuationObservations | None = None,
    _clock=None,
    _sleep=None,
    _timer=None,
) -> tuple[dict, dict]:
    clock = _clock or time.monotonic
    sleep = _sleep or time.sleep
    observed = observations or ContinuationObservations()
    started = clock()
    deadline = started + CONTINUATION_DEADLINE_SECONDS
    if observed.continuation_accepted_at is None:
        observed.mark_continuation_accepted(started)
    while True:
        now = clock()
        if now >= deadline:
            observed.finish_continuation(now)
            raise OperationalSmokeFailure(
                stage=stage,
                failure_kind=FAILURE_TIMEOUT,
                timeout=True,
            )
        try:
            status = _timed_mcp_tool(
                client,
                "run_status",
                {"run_id": run_id},
                stage=stage,
                observations=observed,
                baseline=False,
                deadline=deadline,
                _timer=_timer,
            )
        except _MCPToolResponseError:
            observed.status_read_error_count += 1
            observed.finish_continuation(clock())
            raise
        except BaseException:
            observed.finish_continuation(clock())
            raise
        observed.observe_status(status)
        if status.get("state") in {"completed", "failed", "cancelled"}:
            try:
                result = _timed_mcp_tool(
                    client,
                    "run_result",
                    {"run_id": run_id},
                    stage=stage,
                    observations=observed,
                    baseline=False,
                    deadline=deadline,
                    _timer=_timer,
                )
            except _MCPToolResponseError as error:
                observed.observe_result_error(
                    error.result_error_classification
                )
                sleep(POLL_INTERVAL_SECONDS)
                continue
            except BaseException:
                observed.finish_continuation(clock())
                raise
            if (
                prior_terminal_commitment_ref is not None
                and result.get("terminal_commitment_ref")
                == prior_terminal_commitment_ref
            ):
                observed.stale_epoch0_result_observation_count += 1
                sleep(POLL_INTERVAL_SECONDS)
                continue
            observed.finish_continuation(clock())
            return status, result
        sleep(POLL_INTERVAL_SECONDS)


_DURABLE_SNAPSHOT_FIELDS = frozenset(
    {
        "opening_resume_decision_present",
        "durable_terminal_epoch",
        "terminal_draft_count",
        "terminal_commitment_count",
        "latest_commitment_epoch",
        "commitment_inclusive_replay_binding_present",
        "durable_result_binding",
    }
)
_DURABLE_INSPECTION_PROGRAM = r"""
import json
from pathlib import Path
import stat
import sys

try:
    from deepreason.application.models import RunResultV2
    from deepreason.harness import Harness
    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
    from deepreason.runtime.terminal_authority import (
        TerminalReplayValidationBindingV1,
        _read_current_result,
        _read_replay_validation,
        _replay_validation_base,
        _validate_result_projection_binding,
    )
    from deepreason.workflow.models import (
        RunTerminalCommitmentV1,
        RunTerminalResultDraftV1,
    )

    request = json.loads(sys.stdin.read())
    if set(request) != {"root", "prior_terminal_commitment_ref"}:
        raise ValueError
    root = Path(request["root"])
    prior_ref = request["prior_terminal_commitment_ref"]
    if not isinstance(prior_ref, str):
        raise ValueError
    manifest = load_run_manifest(root / MANIFEST_NAME)
    harness = Harness(root, read_only=True)
    state = harness.workflow_state
    epoch = state.current_terminal_epoch
    if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 0:
        raise ValueError
    opening_ref = state.terminal_epoch_opening_resume_ref.get(epoch)
    if opening_ref is not None and opening_ref not in state.resume_decisions:
        raise ValueError
    opening_present = opening_ref is not None

    def typed_objects(schema, model):
        directory = Path(harness.objects.root) / schema
        try:
            observed = directory.lstat()
        except FileNotFoundError:
            return []
        if not stat.S_ISDIR(observed.st_mode):
            raise ValueError
        paths = sorted(directory.glob("*.json"))
        if len(paths) > 64:
            raise ValueError
        values = []
        for path in paths:
            item = path.lstat()
            if not stat.S_ISREG(item.st_mode) or item.st_size > 4 * 1024 * 1024:
                raise ValueError
            found_schema, value, _record = harness.objects._read_record(path)
            if found_schema != schema or not isinstance(value, model):
                raise ValueError
            if (
                value.manifest_sha256 == manifest.sha256
                and value.run_id == manifest.sha256
            ):
                values.append(value)
        return values

    drafts = typed_objects(
        "workflow-run-terminal-result-draft-v1",
        RunTerminalResultDraftV1,
    )
    commitments = typed_objects(
        "workflow-run-terminal-commitment-v1",
        RunTerminalCommitmentV1,
    )
    latest_epoch = (
        max(item.terminal_epoch for item in commitments)
        if commitments
        else None
    )
    current_refs = [
        item.id for item in commitments if item.terminal_epoch == epoch
    ]
    current_items = [
        item for item in commitments if item.terminal_epoch == epoch
    ]
    if len(current_items) == 1 and epoch > 0:
        current = current_items[0]
        if (
            current.parent_terminal_commitment_ref != prior_ref
            or current.opening_resume_ref != opening_ref
        ):
            raise ValueError

    result = _read_current_result(root)
    if result is None:
        typed_result = None
        result_binding = "absent"
    else:
        typed_result = RunResultV2.model_validate(result)
        result_ref = typed_result.terminal_commitment_ref
        if result_ref is None:
            result_binding = "unbound"
        elif result_ref == prior_ref:
            result_binding = "prior_commitment"
        elif len(current_refs) == 1 and result_ref == current_refs[0]:
            result_binding = "current_commitment"
        else:
            result_binding = "unknown"

    replay = _read_replay_validation(root)
    replay_binding_present = False
    if replay is not None and replay.get("terminal_binding") is not None:
        TerminalReplayValidationBindingV1.model_validate(
            replay["terminal_binding"]
        )
        _replay_validation_base(replay)
        if len(current_items) == 1 and typed_result is not None:
            try:
                _validate_result_projection_binding(
                    harness,
                    manifest,
                    current_items[0],
                    result,
                )
            except (TypeError, ValueError):
                pass
            else:
                replay_binding_present = True

    payload = {
        "opening_resume_decision_present": opening_present,
        "durable_terminal_epoch": epoch,
        "terminal_draft_count": len(drafts),
        "terminal_commitment_count": len(commitments),
        "latest_commitment_epoch": latest_epoch,
        "commitment_inclusive_replay_binding_present": (
            replay_binding_present
        ),
        "durable_result_binding": result_binding,
    }
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
except BaseException:
    raise SystemExit(2)
"""


def _read_loopback_diagnostic_state(path: Path) -> tuple[int, int]:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return 0, 0
    if not stat.S_ISREG(observed.st_mode) or not 2 <= observed.st_size <= 1024 * 1024:
        raise ValueError("loopback diagnostic state is unavailable")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("loopback diagnostic state is unavailable")
    total_calls = _nonnegative_integer_or_none(
        payload.get("total_calls"), field="loopback total calls"
    )
    errors = payload.get("errors")
    if total_calls is None or not isinstance(errors, list):
        raise ValueError("loopback diagnostic state is unavailable")
    return total_calls, len(errors)


def _validate_durable_snapshot(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict) or set(payload) != _DURABLE_SNAPSHOT_FIELDS:
        raise ValueError("durable diagnostic field inventory drifted")
    for field in (
        "durable_terminal_epoch",
        "terminal_draft_count",
        "terminal_commitment_count",
        "latest_commitment_epoch",
    ):
        payload[field] = _nonnegative_integer_or_none(
            payload[field], field=field
        )
    for field in (
        "opening_resume_decision_present",
        "commitment_inclusive_replay_binding_present",
    ):
        if type(payload[field]) is not bool:
            raise TypeError(f"{field} must be boolean")
    if payload["durable_result_binding"] not in ALLOWED_RESULT_BINDINGS:
        raise ValueError("invalid durable result binding")
    return payload


def _run_durable_inspection(
    context: ContinuationDiagnosticContext,
) -> dict[str, object]:
    inspection_env = dict(context.env)
    inspection_env.pop("DEEPREASON_WHEEL_LOOPBACK_FIXTURE", None)
    inspection_env.pop(LOOPBACK_READY_ENV, None)
    request = json.dumps(
        {
            "root": str(context.run_root),
            "prior_terminal_commitment_ref": (
                context.prior_terminal_commitment_ref
            ),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    completed = subprocess.run(
        [str(context.python), "-c", _DURABLE_INSPECTION_PROGRAM],
        cwd=context.work,
        env=inspection_env,
        input=request,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=DIAGNOSTIC_INSPECTION_TIMEOUT_SECONDS,
    )
    if (
        completed.returncode != 0
        or not isinstance(completed.stdout, str)
        or len(completed.stdout.encode("utf-8")) > 4096
    ):
        raise ValueError("durable diagnostic inspection failed")
    return _validate_durable_snapshot(json.loads(completed.stdout))


def _empty_terminal_phase_snapshot() -> dict[str, object]:
    return {
        "terminalization_last_entered_phase": (
            TERMINALIZATION_NOT_OBSERVED
        ),
        "terminalization_last_returned_phase": (
            TERMINALIZATION_NOT_OBSERVED
        ),
        "terminalization_last_error_phase": (
            TERMINALIZATION_NOT_OBSERVED
        ),
        "terminalization_last_error_family": ERROR_NONE,
        "terminalization_phase_entry_counts": _zero_phase_mapping(),
        "terminalization_phase_return_counts": _zero_phase_mapping(),
        "terminalization_phase_error_counts": _zero_phase_mapping(),
        "terminalization_phase_total_ms": _zero_phase_mapping(),
        "terminalization_ledger_overflow": False,
        "terminal_lock_acquire_count": 0,
        "terminal_lock_wait_total_ms": 0,
        "terminal_lock_wait_max_ms": 0,
        "worker_liveness": WORKER_LIVENESS_UNKNOWN,
        "terminal_publication_recovery_required_observed": False,
        "application_recovery_interference_observed": False,
        "application_recovery_last_entered_phase": (
            TERMINALIZATION_NOT_OBSERVED
        ),
    }


def _read_terminal_phase_ledger(path: Path) -> dict[str, object]:
    """Read the bounded smoke ledger without interpreting dynamic content."""

    try:
        observed = path.lstat()
    except FileNotFoundError as error:
        raise ValueError("terminal phase ledger is missing") from error
    if (
        not stat.S_ISREG(observed.st_mode)
        or observed.st_size > TERMINAL_DIAGNOSTIC_MAX_BYTES
    ):
        raise ValueError("terminal phase ledger is unavailable")
    raw = path.read_bytes()
    lines = raw.splitlines(keepends=True)
    if lines and not lines[-1].endswith(b"\n"):
        lines.pop()
    if len(lines) > TERMINAL_DIAGNOSTIC_MAX_RECORDS:
        raise ValueError("terminal phase ledger exceeds its record bound")

    snapshot = _empty_terminal_phase_snapshot()
    entries = snapshot["terminalization_phase_entry_counts"]
    returns = snapshot["terminalization_phase_return_counts"]
    errors = snapshot["terminalization_phase_error_counts"]
    totals = snapshot["terminalization_phase_total_ms"]
    assert isinstance(entries, dict)
    assert isinstance(returns, dict)
    assert isinstance(errors, dict)
    assert isinstance(totals, dict)
    current_liveness = WORKER_LIVENESS_UNKNOWN
    worker_publication_depth = 0
    overflow_seen = False
    for line in lines:
        if overflow_seen:
            raise ValueError("terminal phase ledger continued after overflow")
        if len(line) > 1024:
            raise ValueError("terminal phase ledger record is oversized")
        try:
            record = json.loads(line)
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("terminal phase ledger is malformed") from error
        if not isinstance(record, dict):
            raise ValueError("terminal phase ledger record is not an object")
        if set(record) == {"overflow"}:
            if record["overflow"] is not True:
                raise ValueError("terminal phase overflow marker is invalid")
            snapshot["terminalization_ledger_overflow"] = True
            overflow_seen = True
            continue
        if set(record) == {"observation", "value"}:
            observation = record["observation"]
            value = record["value"]
            if observation == "worker_liveness":
                if value not in ALLOWED_WORKER_LIVENESS:
                    raise ValueError("terminal phase liveness is invalid")
                current_liveness = value
                snapshot["worker_liveness"] = value
                continue
            if observation == (
                "terminal_publication_recovery_required"
            ):
                if value is not True:
                    raise ValueError("terminal recovery sentinel is invalid")
                snapshot[
                    "terminal_publication_recovery_required_observed"
                ] = True
                continue
            if observation == "instrumentation_failure":
                raise ValueError("terminal phase instrumentation failed")
            raise ValueError("terminal phase observation is unknown")
        if set(record) != {
            "phase",
            "edge",
            "elapsed_ms",
            "actor",
            "error_family",
        }:
            raise ValueError("terminal phase record inventory drifted")
        phase = record["phase"]
        edge = record["edge"]
        actor = record["actor"]
        family = record["error_family"]
        elapsed = record["elapsed_ms"]
        if (
            phase not in ALLOWED_LEDGER_PHASES
            or edge not in ALLOWED_LEDGER_EDGES
            or actor not in ALLOWED_LEDGER_ACTORS
            or family not in ALLOWED_LEDGER_ERROR_FAMILIES
            or isinstance(elapsed, bool)
            or not isinstance(elapsed, int)
            or not 0 <= elapsed <= 86_400_000
        ):
            raise ValueError("terminal phase record value is invalid")
        if edge in {"enter", "wait_start"}:
            entries[phase] += 1
        elif edge in {"return", "acquired"}:
            returns[phase] += 1
            totals[phase] += elapsed
        elif edge == "error":
            errors[phase] += 1
            totals[phase] += elapsed
        if phase == TERMINAL_LOCK and edge == "acquired":
            snapshot["terminal_lock_acquire_count"] += 1
            snapshot["terminal_lock_wait_total_ms"] += elapsed
            snapshot["terminal_lock_wait_max_ms"] = max(
                snapshot["terminal_lock_wait_max_ms"],
                elapsed,
            )
        terminalization_specific = (
            phase in TERMINALIZATION_PHASES or phase == TERMINAL_LOCK
        )
        if actor == "worker" and terminalization_specific:
            if edge in {"enter", "wait_start"}:
                snapshot["terminalization_last_entered_phase"] = phase
            elif edge in {"return", "acquired"}:
                snapshot["terminalization_last_returned_phase"] = phase
        if terminalization_specific and edge == "error":
            snapshot["terminalization_last_error_phase"] = phase
            snapshot["terminalization_last_error_family"] = family
        if (
            actor == "worker"
            and phase == W10_REPLAY_AND_FINAL_RESULT_PUBLICATION
        ):
            if edge == "enter":
                worker_publication_depth += 1
            elif edge in {"return", "error"}:
                worker_publication_depth = max(
                    0,
                    worker_publication_depth - 1,
                )
        if (
            actor == "mcp_server"
            and phase in TERMINALIZATION_PHASES
            and edge == "enter"
        ):
            snapshot["application_recovery_last_entered_phase"] = phase
            if (
                current_liveness == WORKER_LIVENESS_ALIVE
                and worker_publication_depth > 0
            ):
                snapshot[
                    "application_recovery_interference_observed"
                ] = True
    return snapshot


def _mcp_liveness(clients: list[MCPClient]) -> str:
    if not clients:
        return MCP_LIVENESS_NOT_STARTED
    states = []
    try:
        for client in clients:
            states.append(client.process.poll() is None)
    except Exception:
        return MCP_LIVENESS_UNKNOWN
    return MCP_LIVENESS_ALIVE if any(states) else MCP_LIVENESS_EXITED


def _capture_continuation_diagnostic(
    context: ContinuationDiagnosticContext | None,
    *,
    clients: list[MCPClient],
) -> dict[str, object]:
    diagnostic = (
        context.observations.snapshot()
        if context is not None
        else _default_continuation_diagnostic()
    )
    diagnostic["mcp_liveness"] = _mcp_liveness(clients)
    if any(
        bool(
            getattr(
                client,
                "terminal_publication_recovery_required_observed",
                False,
            )
        )
        for client in clients
    ):
        diagnostic[
            "terminal_publication_recovery_required_observed"
        ] = True
    if context is None:
        return _validated_continuation_diagnostic(diagnostic)
    inspection_succeeded = (
        diagnostic["diagnostic_inspection_status"]
        != DIAGNOSTIC_INSPECTION_FAILED
    )
    try:
        total_calls, error_count = _read_loopback_diagnostic_state(
            context.provider_state_path
        )
        delta = total_calls - context.provider_call_baseline
        if delta < 0:
            raise ValueError("loopback provider count moved backwards")
    except Exception:
        inspection_succeeded = False
    else:
        diagnostic.update(
            {
                "provider_call_delta": delta,
                "loopback_provider_error_count": error_count,
            }
        )
    try:
        diagnostic.update(_run_durable_inspection(context))
    except Exception:
        inspection_succeeded = False
    if context.terminal_phase_ledger_path is not None:
        try:
            ledger = _read_terminal_phase_ledger(
                context.terminal_phase_ledger_path
            )
        except Exception:
            inspection_succeeded = False
        else:
            sentinel_observed = bool(
                diagnostic[
                    "terminal_publication_recovery_required_observed"
                ]
            )
            diagnostic.update(ledger)
            diagnostic[
                "terminal_publication_recovery_required_observed"
            ] = sentinel_observed or bool(
                ledger[
                    "terminal_publication_recovery_required_observed"
                ]
            )
    diagnostic["diagnostic_inspection_status"] = (
        DIAGNOSTIC_INSPECTION_SUCCEEDED
        if inspection_succeeded
        else DIAGNOSTIC_INSPECTION_FAILED
    )
    return _validated_continuation_diagnostic(diagnostic)


def _assert_no_disclosure(
    *, repo: Path, home: Path, outputs: list[str], transcripts: list[str]
) -> None:
    forbidden = (str(repo.resolve()), TEST_CREDENTIAL)
    combined = "\n".join([*outputs, *transcripts])
    for value in forbidden:
        if value.casefold() in combined.casefold():
            raise AssertionError("command or MCP output disclosed repository/credential data")
    for path in home.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        payload = path.read_bytes()
        for value in forbidden:
            if value.encode() in payload:
                raise AssertionError("run/state record disclosed forbidden data")


def _platform_family() -> str:
    if sys.platform == "win32":
        return PLATFORM_WINDOWS
    if sys.platform == "darwin":
        return PLATFORM_MACOS
    if sys.platform.startswith("linux"):
        return PLATFORM_LINUX
    return PLATFORM_OTHER


def _diagnostic_record(
    failure: OperationalSmokeFailure,
    *,
    cleanup_completed: bool | None,
) -> dict[str, object]:
    if cleanup_completed is not None and type(cleanup_completed) is not bool:
        raise TypeError("cleanup status must be boolean or null")
    record: dict[str, object] = {
        "cleanup_completed": cleanup_completed,
        "detail_code": failure.detail_code,
        "durable_progress": failure.durable_progress,
        "exit_status": failure.exit_status,
        "failure_kind": failure.failure_kind,
        "platform_family": _platform_family(),
        "schema": FAILURE_SCHEMA,
        "stage": failure.stage,
        "timeout": failure.timeout,
    }
    record.update(
        {
            field: failure.state_presence.get(field)
            for field in ALLOWED_STATE_PRESENCE_FIELDS
        }
    )
    record.update(failure.continuation_diagnostic)
    if set(record) != FAILURE_RECORD_FIELDS:
        raise ValueError("failure diagnostic field inventory drifted")
    return record


def _emit_failure_diagnostic(
    failure: OperationalSmokeFailure,
    *,
    cleanup_completed: bool,
) -> None:
    """Emit one fixed-schema, payload-free Actions annotation."""

    try:
        encoded = json.dumps(
            _diagnostic_record(
                failure, cleanup_completed=cleanup_completed
            ),
            sort_keys=True,
            separators=(",", ":"),
        )
        print(
            "::error title=DeepReason installed-wheel operational smoke failed::"
            f"{encoded}",
            file=sys.stderr,
            flush=True,
        )
    except Exception:
        return


def _failure_exit_status(failure: OperationalSmokeFailure) -> int:
    if failure.exit_status is not None and 1 <= failure.exit_status <= 255:
        return failure.exit_status
    return 1


def _cleanup_temp_root(temp_root: Path | None) -> bool:
    if temp_root is None:
        return True
    try:
        shutil.rmtree(temp_root)
        return not temp_root.exists()
    except OSError:
        return False


def _new_mcp_client(
    clients: list[MCPClient],
    executable: Path,
    *,
    cwd: Path,
    env: dict[str, str],
    stage: str = STAGE_MCP_INITIALIZE,
) -> MCPClient:
    client = MCPClient(executable, cwd=cwd, env=env, stage=stage)
    clients.append(client)
    return client


def _shutdown_mcp_clients(
    clients: list[MCPClient],
) -> tuple[bool, OperationalSmokeFailure | None]:
    first_failure: OperationalSmokeFailure | None = None
    for client in reversed(clients):
        try:
            client.close(stage=STAGE_CLEANUP)
        except OperationalSmokeFailure as error:
            if first_failure is None:
                first_failure = error
        except Exception:
            if first_failure is None:
                first_failure = OperationalSmokeFailure(
                    stage=STAGE_CLEANUP,
                    failure_kind=FAILURE_CLEANUP,
                )
    try:
        stopped = all(client.process.poll() is not None for client in clients)
    except Exception:
        stopped = False
    return stopped, first_failure


def _finalize_operational_smoke(
    failure: OperationalSmokeFailure | None,
    *,
    temp_root: Path | None,
    mcp_clients: list[MCPClient] | None = None,
    diagnostic_context: ContinuationDiagnosticContext | None = None,
) -> int:
    clients = list(mcp_clients or ())
    diagnostic: dict[str, object] | None = None
    if clients and (
        failure is not None
        or any(not getattr(client, "_closed", False) for client in clients)
    ):
        try:
            diagnostic = _capture_continuation_diagnostic(
                diagnostic_context,
                clients=clients,
            )
        except Exception:
            diagnostic = (
                diagnostic_context.observations.snapshot()
                if diagnostic_context is not None
                else _default_continuation_diagnostic()
            )
            diagnostic["diagnostic_inspection_status"] = (
                DIAGNOSTIC_INSPECTION_FAILED
            )
            diagnostic["mcp_liveness"] = _mcp_liveness(clients)
            diagnostic = _validated_continuation_diagnostic(diagnostic)
        if failure is not None:
            failure.attach_continuation_diagnostic(diagnostic)
    mcp_cleanup_completed, shutdown_failure = _shutdown_mcp_clients(clients)
    if failure is None and shutdown_failure is not None:
        failure = shutdown_failure
        if diagnostic is not None:
            failure.attach_continuation_diagnostic(diagnostic)
    root_cleanup_completed = _cleanup_temp_root(temp_root)
    cleanup_completed = (
        mcp_cleanup_completed and root_cleanup_completed
    )
    if failure is None and not cleanup_completed:
        failure = OperationalSmokeFailure(
            stage=STAGE_CLEANUP,
            failure_kind=FAILURE_CLEANUP,
            continuation_diagnostic=diagnostic,
        )
    if failure is not None:
        _emit_failure_diagnostic(
            failure,
            cleanup_completed=cleanup_completed,
        )
        return _failure_exit_status(failure)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[1]
    temp_root: Path | None = None
    failure: OperationalSmokeFailure | None = None
    mcp_clients: list[MCPClient] = []
    diagnostic_context: ContinuationDiagnosticContext | None = None
    succeeded = False
    stage = STAGE_CREATE_ENVIRONMENT
    try:
        temp_root = Path(tempfile.mkdtemp(prefix="deepreason-wheel-operational-"))
        provider_port = _unused_loopback_port()
        provider_state_path = temp_root / "loopback-provider-counts.json"
        terminal_phase_ledger_path = (
            temp_root / "terminal-phase-ledger.jsonl"
        )
        outputs: list[str] = []
        transcripts: list[str] = []
        stage = STAGE_BUILD_WHEEL
        wheel = _build_wheel(repo, temp_root)
        _inspect_operational_wheel(wheel)
        stage = STAGE_CREATE_ENVIRONMENT
        environment = temp_root / "installed environment with spaces"
        venv.EnvBuilder(
            with_pip=True,
            clear=True,
            system_site_packages=False,
        ).create(environment)
        if "include-system-site-packages = false" not in (
            environment / "pyvenv.cfg"
        ).read_text(encoding="utf-8").casefold():
            raise AssertionError("operational venv inherited system site packages")
        python = _venv_executable(environment, "python")
        deepreason = _venv_executable(environment, "deepreason")
        mcp = _venv_executable(environment, "deepreason-mcp")
        home = temp_root / "blank home"
        work = temp_root / "unrelated empty directory"
        home.mkdir()
        work.mkdir()
        if (
            home.resolve() in terminal_phase_ledger_path.resolve().parents
            or environment.resolve()
            in terminal_phase_ledger_path.resolve().parents
        ):
            raise AssertionError(
                "terminal phase ledger entered managed or package storage"
            )
        clean_env = _environment(
            home,
            provider_port=provider_port,
            provider_state_path=provider_state_path,
        )
        stage = STAGE_INSTALL_WHEEL
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                str(wheel),
            ],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        _run(
            [str(python), "-m", "pip", "check"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        fixture_path = _install_loopback_fixture(
            repo=repo,
            python=python,
            work=work,
            env=clean_env,
            stage=stage,
        )
        if environment.resolve() not in fixture_path.resolve().parents:
            raise AssertionError("external provider fixture escaped the disposable venv")

        stage = STAGE_INSTALL_WHEEL
        imported = json.loads(
            _run(
                [
                    str(python),
                    "-c",
                    (
                        "import deepreason,json,sys;"
                        "print(json.dumps({'file':deepreason.__file__,'path':sys.path}))"
                    ),
                ],
                cwd=work,
                env=clean_env,
                stage=stage,
            ).stdout
        )
        module_file = Path(imported["file"]).resolve()
        if environment.resolve() not in module_file.parents or repo.resolve() in module_file.parents:
            raise AssertionError("installed import escaped the clean venv")
        if any(str(repo.resolve()).casefold() in str(item).casefold() for item in imported["path"]):
            raise AssertionError("repository path appears in installed sys.path")

        stage = STAGE_READINESS
        bare = _run(
            [str(deepreason)],
            cwd=work,
            env=clean_env,
            stage=stage,
            expected=(1,),
        )
        outputs.extend((bare.stdout, bare.stderr))
        if "Next action: deepreason setup" not in bare.stdout:
            raise AssertionError("bare deepreason did not report setup readiness")

        endpoint = f"http://127.0.0.1:{provider_port}/v1"
        stage = STAGE_SETUP_PROFILE
        setup = _run(
            [
                str(deepreason),
                "setup",
                "--provider",
                "generic",
                "--endpoint",
                endpoint,
                "--model",
                "deepreason-loopback-v6",
                "--model-revision",
                "fixture-1",
                "--family",
                "deterministic-loopback",
                "--context-window-tokens",
                "1000000",
                "--maximum-completion-tokens",
                "512",
                "--credential-env",
                TEST_CREDENTIAL_ENV,
            ],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((setup.stdout, setup.stderr))
        stage = STAGE_READINESS
        calls_before_status = _provider_counts(provider_state_path)["total_calls"]
        unqualified = _run(
            [str(deepreason), "status", "--json"],
            cwd=work,
            env=clean_env,
            stage=stage,
            expected=(1,),
        )
        outputs.extend((unqualified.stdout, unqualified.stderr))
        unqualified_payload = json.loads(unqualified.stdout)
        if unqualified_payload["qualification_state"] != "unqualified":
            raise AssertionError("setup did not transition readiness to unqualified")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_status,
        )

        stage = STAGE_QUALIFY
        qualified = _run(
            [str(deepreason), "qualify", "--yes"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((qualified.stdout, qualified.stderr))
        notice = re.search(
            r"maximum expected provider calls: ([0-9]+)", qualified.stderr
        )
        if notice is None or int(notice.group(1)) != 240:
            raise AssertionError("qualification did not announce the frozen maximum")
        counts = _provider_counts(provider_state_path)
        if counts != {"qualification_calls": 80, "total_calls": 80}:
            raise AssertionError(
                "qualification did not make exactly 80 loopback calls"
            )

        stage = STAGE_READINESS
        calls_before_status = counts["total_calls"]
        ready = _run(
            [str(deepreason), "status", "--json"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((ready.stdout, ready.stderr))
        ready_payload = json.loads(ready.stdout)
        if not ready_payload["ready"] or ready_payload["product_mode"] != "v6-only":
            raise AssertionError("installed status did not become V6 ready")
        module_status = _run(
            [str(python), "-m", "deepreason", "status", "--json"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((module_status.stdout, module_status.stderr))
        if json.loads(module_status.stdout) != ready_payload:
            raise AssertionError("python -m status differs from the console")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_status,
        )

        stage = STAGE_QUALIFY
        calls_before_cache = _provider_counts(provider_state_path)["total_calls"]
        cached = _run(
            [str(deepreason), "qualify", "--yes", "--json"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((cached.stdout, cached.stderr))
        cached_payload = json.loads(cached.stdout)
        if not cached_payload["cache_reused"] or cached_payload["maximum_expected_provider_calls"] != 0:
            raise AssertionError("completed qualification cache was not reused")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_cache,
        )

        stage = STAGE_REASON
        first = _run_reason(
            [str(deepreason), "reason", "Why can layered explanations remain testable?"],
            cwd=work,
            env=clean_env,
            home=home,
            ready_marker=temp_root / ".initial-reason-loopback-ready",
            expected=(0, 5),
            timeout=600,
        )
        outputs.extend((first.stdout, first.stderr))
        first_result = json.loads(first.stdout)
        _assert_committed_terminal(first_result)
        first_run_id = first_result["run_id"]
        if _provider_counts(provider_state_path)["qualification_calls"] != 80:
            raise AssertionError("question preparation silently requalified")

        stage = STAGE_MCP_INITIALIZE
        calls_before_retrieval = _provider_counts(provider_state_path)["total_calls"]
        registration = _run(
            [str(deepreason), "mcp-registration"],
            cwd=work,
            env=clean_env,
            stage=stage,
        )
        outputs.extend((registration.stdout, registration.stderr))
        registration_payload = json.loads(registration.stdout)
        registered = registration_payload["mcpServers"]["deepreason"]
        if registered != {"command": str(mcp.resolve()), "args": []} or " " not in registered["command"]:
            raise AssertionError("generic MCP registration mishandled the installed spaced path")

        stage = STAGE_MCP_INITIALIZE
        first_client = _new_mcp_client(
            mcp_clients, mcp, cwd=work, env=clean_env
        )
        _assert_exact_tools(_tool_list(first_client))
        stage = STAGE_MCP_REQUEST
        first_status = first_client.tool(
            "run_status",
            {"run_id": first_run_id},
            stage=stage,
        )
        first_retrieved = first_client.tool(
            "run_result",
            {"run_id": first_run_id},
            stage=stage,
        )
        _assert_committed_terminal(first_retrieved)
        if first_retrieved != {key: value for key, value in first_result.items()}:
            raise AssertionError("durable CLI result changed when retrieved through MCP")
        if first_status.get("state") != "completed":
            raise AssertionError("restarted process did not recover CLI run status")
        stage = STAGE_CONTINUATION_REJECTION
        calls_before_rejection = _provider_counts(provider_state_path)["total_calls"]
        rejected_continuation = first_client.tool_error(
            "continue_run",
            {
                "run_id": first_run_id,
                "budget": {"cycles": 6, "token_budget": 100000},
            },
            stage=stage,
        )
        _assert_non_resumable_rejection(rejected_continuation)
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_rejection,
        )
        if first_client.tool(
            "run_result",
            {"run_id": first_run_id},
            stage=stage,
        ) != first_retrieved:
            raise AssertionError("rejected continuation changed the terminal result")
        transcripts.extend(first_client.transcript)
        first_client.close(stage=stage)
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_retrieval,
        )

        stage = STAGE_REASON
        resumable = _run_reason(
            [
                str(deepreason),
                "reason",
                RESUMABLE_STOP_QUESTION,
                "--cycles",
                "12",
                "--token-budget",
                "200000",
            ],
            cwd=work,
            env=clean_env,
            home=home,
            ready_marker=temp_root / ".resumable-reason-loopback-ready",
            expected=(0, 5),
            timeout=600,
        )
        outputs.extend((resumable.stdout, resumable.stderr))
        resumable_result = json.loads(resumable.stdout)
        _assert_resumable_terminal(resumable_result)
        resumable_run_id = resumable_result["run_id"]
        stage = STAGE_CONTINUATION_RESUME
        calls_before_resumable_retrieval = _provider_counts(provider_state_path)[
            "total_calls"
        ]
        baseline_client = _new_mcp_client(
            mcp_clients, mcp, cwd=work, env=clean_env
        )
        _assert_exact_tools(_tool_list(baseline_client))
        continuation_observations = ContinuationObservations()
        resumable_retrieved = _timed_mcp_tool(
            baseline_client,
            "run_result",
            {"run_id": resumable_run_id},
            stage=stage,
            observations=continuation_observations,
            baseline=True,
        )
        resumable_baseline_status = _timed_mcp_tool(
            baseline_client,
            "run_status",
            {"run_id": resumable_run_id},
            stage=stage,
            observations=continuation_observations,
            baseline=True,
        )
        if resumable_retrieved != resumable_result:
            raise AssertionError("resumable CLI result changed when retrieved through MCP")
        if resumable_baseline_status.get("state") != "completed":
            raise AssertionError("resumable baseline status was not terminal")
        transcripts.extend(baseline_client.transcript)
        baseline_client.close(stage=stage)
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_resumable_retrieval,
        )
        diagnostic_env = dict(clean_env)
        diagnostic_env[TERMINAL_DIAGNOSTIC_ENABLE_ENV] = "1"
        diagnostic_env[TERMINAL_DIAGNOSTIC_LEDGER_ENV] = str(
            terminal_phase_ledger_path
        )
        continuation_client = _new_mcp_client(
            mcp_clients, mcp, cwd=work, env=diagnostic_env
        )
        _assert_exact_tools(_tool_list(continuation_client))
        provider_call_baseline = _provider_counts(provider_state_path)[
            "total_calls"
        ]
        continued = continuation_client.tool(
            "continue_run",
            {
                "run_id": resumable_run_id,
                "budget": {"cycles": 6, "token_budget": 100000},
            },
            stage=stage,
        )
        if continued.get("run_id") != resumable_run_id:
            raise AssertionError("continuation changed the opaque managed identity")
        continuation_observations.mark_continuation_accepted(
            time.monotonic()
        )
        diagnostic_context = ContinuationDiagnosticContext(
            python=python,
            work=work,
            env=clean_env,
            run_root=(
                home / ".deepreason" / "runs" / resumable_run_id
            ),
            prior_terminal_commitment_ref=resumable_result[
                "terminal_commitment_ref"
            ],
            provider_state_path=provider_state_path,
            provider_call_baseline=provider_call_baseline,
            observations=continuation_observations,
            terminal_phase_ledger_path=terminal_phase_ledger_path,
        )
        _continued_status, final_resumable_result = _poll_terminal(
            continuation_client,
            resumable_run_id,
            prior_terminal_commitment_ref=resumable_result[
                "terminal_commitment_ref"
            ],
            stage=stage,
            observations=continuation_observations,
        )
        _assert_resumable_terminal(final_resumable_result)
        transcripts.extend(continuation_client.transcript)
        continuation_client.close(stage=stage)
        continued_durable = _run_durable_inspection(diagnostic_context)
        if continued_durable != {
            "opening_resume_decision_present": True,
            "durable_terminal_epoch": 1,
            "terminal_draft_count": 2,
            "terminal_commitment_count": 2,
            "latest_commitment_epoch": 1,
            "commitment_inclusive_replay_binding_present": True,
            "durable_result_binding": RESULT_BINDING_CURRENT,
        }:
            raise AssertionError(
                "continued terminal authority or replay binding drifted"
            )
        continued_phase_snapshot = _read_terminal_phase_ledger(
            terminal_phase_ledger_path
        )
        if (
            continued_phase_snapshot[
                "terminalization_phase_entry_counts"
            ][W6_PENDING_RESULT_PUBLICATION]
            == 0
            or continued_phase_snapshot[
                "terminalization_phase_error_counts"
            ][W9_REPLAY_BINDING_VALIDATION]
            != 0
        ):
            raise AssertionError(
                "expected W6 freshness probe produced false W9 evidence"
            )

        stage = STAGE_RESTART_RECOVERY
        calls_before_restart = _provider_counts(provider_state_path)["total_calls"]
        restarted_first = _new_mcp_client(
            mcp_clients, mcp, cwd=work, env=clean_env
        )
        _assert_exact_tools(_tool_list(restarted_first))
        restarted_first_status = restarted_first.tool(
            "run_status",
            {"run_id": resumable_run_id},
            stage=stage,
        )
        restarted_first_result = restarted_first.tool(
            "run_result",
            {"run_id": resumable_run_id},
            stage=stage,
        )
        transcripts.extend(restarted_first.transcript)
        restarted_first.close(stage=stage)
        if (
            restarted_first_status.get("state") != "completed"
            or restarted_first_result != final_resumable_result
        ):
            raise AssertionError("continued CLI run did not survive process restart")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_restart,
        )
        stage = STAGE_REPLAY_VALIDATION
        _assert_durable_replay(home, first_run_id)
        _assert_durable_replay(home, resumable_run_id)

        stage = STAGE_BUDGET_REJECTION
        before_roots = {path.name for path in (home / ".deepreason" / "runs").iterdir() if path.is_dir()}
        before_calls = _provider_counts(provider_state_path)["total_calls"]
        over_budget = _run(
            [str(deepreason), "reason", "This must not start", "--cycles", "13"],
            cwd=work,
            env=clean_env,
            stage=stage,
            expected=(1,),
        )
        outputs.extend((over_budget.stdout, over_budget.stderr))
        after_roots = {path.name for path in (home / ".deepreason" / "runs").iterdir() if path.is_dir()}
        if (
            before_roots != after_roots
            or before_calls != _provider_counts(provider_state_path)["total_calls"]
        ):
            raise AssertionError("over-ceiling reasoning mutated state or called the provider")

        stage = STAGE_REASON
        second = _run_reason(
            [
                str(deepreason),
                "reason",
                "How can deterministic records make disagreement inspectable?",
                "--cycles",
                "1",
            ],
            cwd=work,
            env=clean_env,
            home=home,
            ready_marker=temp_root / ".second-reason-loopback-ready",
            timeout=180,
        )
        outputs.extend((second.stdout, second.stderr))
        _assert_committed_terminal(json.loads(second.stdout))
        if _provider_counts(provider_state_path)["qualification_calls"] != 80:
            raise AssertionError("second preparation made qualification calls")

        stage = STAGE_MCP_REQUEST
        mcp_client = _new_mcp_client(
            mcp_clients, mcp, cwd=work, env=clean_env
        )
        _assert_exact_tools(_tool_list(mcp_client))
        started = mcp_client.tool(
            "start_run",
            {
                "question": "What makes a new explanation robust under criticism?",
                "budget": {"cycles": 1, "token_budget": 50000},
            },
            stage=stage,
        )
        mcp_run_id = started["run_id"]
        _status, mcp_result = _poll_terminal(
            mcp_client,
            mcp_run_id,
            stage=stage,
        )
        transcripts.extend(mcp_client.transcript)
        mcp_client.close(stage=stage)
        _assert_committed_terminal(mcp_result)
        if _provider_counts(provider_state_path)["qualification_calls"] != 80:
            raise AssertionError("MCP preparation initiated qualification")

        stage = STAGE_RESTART_RECOVERY
        calls_before_restart = _provider_counts(provider_state_path)["total_calls"]
        restarted = _new_mcp_client(
            mcp_clients, mcp, cwd=work, env=clean_env
        )
        _assert_exact_tools(_tool_list(restarted))
        restarted_status = restarted.tool(
            "run_status",
            {"run_id": mcp_run_id},
            stage=stage,
        )
        restarted_result = restarted.tool(
            "run_result",
            {"run_id": mcp_run_id},
            stage=stage,
        )
        transcripts.extend(restarted.transcript)
        restarted.close(stage=stage)
        if restarted_status.get("state") != "completed" or restarted_result != mcp_result:
            raise AssertionError("managed MCP identity did not survive server restart")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_restart,
        )

        stage = STAGE_MANIFEST_REJECTION
        calls_before_manifest_rejection = _provider_counts(provider_state_path)[
            "total_calls"
        ]
        runs_before_history = {
            path.name for path in (home / ".deepreason" / "runs").iterdir() if path.is_dir()
        }
        for version in range(1, 6):
            raw = work / f"historical-v{version}.json"
            raw.write_text(json.dumps({"schema_version": version, "nested": TEST_CREDENTIAL}))
            rejected = _run(
                [
                    str(deepreason),
                    "config",
                    "inspect",
                    "--run-manifest",
                    str(raw),
                ],
                cwd=work,
                env=clean_env,
                stage=stage,
                expected=(1,),
            )
            outputs.extend((rejected.stdout, rejected.stderr))
            if "UNSUPPORTED_RUN_MANIFEST_VERSION" not in rejected.stderr:
                raise AssertionError("historical manifest was not rejected")
            if TEST_CREDENTIAL in rejected.stdout + rejected.stderr:
                raise AssertionError("historical rejection echoed nested payload content")
        runs_after_history = {
            path.name for path in (home / ".deepreason" / "runs").iterdir() if path.is_dir()
        }
        if runs_before_history != runs_after_history:
            raise AssertionError("historical manifest rejection created a managed run root")
        _assert_no_incremental_provider_calls(
            provider_state_path,
            calls_before_manifest_rejection,
        )

        stage = STAGE_DISCLOSURE_CHECK
        _assert_no_disclosure(
            repo=repo,
            home=home,
            outputs=outputs,
            transcripts=transcripts,
        )
        final_provider_counts = _provider_counts(provider_state_path)
        print(
            "wheel operational smoke passed: installed setup, explicit qualification "
            f"({final_provider_counts['qualification_calls']} qualification calls; "
            f"{final_provider_counts['total_calls']} total calls), "
            "readiness, question-only "
            "reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP "
            "restart, budget ceiling, and pre-V6 fail-closed admission"
        )
        succeeded = True
    except OperationalSmokeFailure as error:
        failure = error
    except AssertionError:
        failure = OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_ASSERTION,
        )
    except Exception:
        failure = OperationalSmokeFailure(
            stage=stage,
            failure_kind=FAILURE_UNEXPECTED,
        )

    if succeeded and args.keep:
        print(f"retained: {temp_root}")
        return 0

    return _finalize_operational_smoke(
        failure,
        temp_root=temp_root,
        mcp_clients=mcp_clients,
        diagnostic_context=diagnostic_context,
    )


if __name__ == "__main__":
    raise SystemExit(main())
