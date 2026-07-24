"""External deterministic HTTP fixture for installed-wheel qualification.

The operational smoke copies this standard-library-only module into its
disposable virtual environment as ``sitecustomize.py``.  When explicitly
enabled through the smoke-only environment below, it starts a loopback
OpenAI-compatible endpoint inside each installed entry-point process.  It is
not a DeepReason module and is excluded from the wheel.
"""

from __future__ import annotations

import functools
import json
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ENABLE_ENV = "DEEPREASON_WHEEL_LOOPBACK_FIXTURE"
PORT_ENV = "DEEPREASON_WHEEL_LOOPBACK_PORT"
STATE_ENV = "DEEPREASON_WHEEL_LOOPBACK_STATE"
READY_ENV = "DEEPREASON_WHEEL_LOOPBACK_READY"
CREDENTIAL_ENV = "DEEPREASON_LOOPBACK_SMOKE_KEY"
CREDENTIAL = "loopback-credential-must-never-appear"
RESUMABLE_STOP_MARKER = "typed resumable stop"
TERMINAL_DIAGNOSTIC_ENABLE_ENV = (
    "DEEPREASON_WHEEL_TERMINAL_PHASE_DIAGNOSTIC"
)
TERMINAL_DIAGNOSTIC_LEDGER_ENV = (
    "DEEPREASON_WHEEL_TERMINAL_PHASE_LEDGER"
)
TERMINAL_DIAGNOSTIC_MAX_RECORDS = 32_768
TERMINAL_PUBLICATION_RECOVERY_SENTINEL = (
    "TERMINAL_PUBLICATION_RECOVERY_REQUIRED"
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
ALLOWED_DIAGNOSTIC_PHASES = frozenset(
    {
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
        TERMINAL_LOCK,
        APPLICATION_INSPECT,
        APPLICATION_RESULT,
    }
)
ALLOWED_DIAGNOSTIC_EDGES = frozenset(
    {"enter", "return", "error", "wait_start", "acquired", "released"}
)
ALLOWED_DIAGNOSTIC_ACTORS = frozenset({"worker", "mcp_server", "other"})
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
ALLOWED_DIAGNOSTIC_ERROR_FAMILIES = frozenset(
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
ALLOWED_WORKER_LIVENESS = frozenset(
    {"alive", "not_alive", "not_registered", "unknown"}
)
TERMINAL_PHASE_WRAPPER_MAP = {
    W1_PRECOMMIT_AUDITS: (
        "deepreason.capabilities.audit.write_tranche_a_audits",
    ),
    W2_PRECOMMIT_VERIFICATION: (
        "deepreason.verification.report.verify_root_report",
    ),
    W3_TERMINAL_AUTHORITY_STATE: (
        "deepreason.application.text_runs.derive_model_execution_summary",
    ),
    W4_TERMINAL_DRAFT_CONSTRUCTION: (
        "deepreason.runtime.terminal_authority._expected_commitment",
    ),
    W5_COMMITMENT_ENSURE: (
        "deepreason.runtime.terminal_authority.ensure_terminal_commitment",
    ),
    W6_PENDING_RESULT_PUBLICATION: (
        "deepreason.runtime.terminal_authority._prepare_terminal_result_locked",
    ),
    W7_FRESH_REPLAY_DERIVATION: (
        "deepreason.runtime.terminal_authority._fresh_replay_validation",
    ),
    W8_POSTCOMMIT_ROOT_VERIFICATION: (
        "deepreason.verification.report.verify_post_commit_report",
    ),
    W9_REPLAY_BINDING_VALIDATION: (
        "deepreason.runtime.terminal_authority._expected_replay_binding",
        "deepreason.runtime.terminal_authority._validate_result_projection_binding",
    ),
    W10_REPLAY_AND_FINAL_RESULT_PUBLICATION: (
        "deepreason.runtime.terminal_authority._publish_current_replay_projection",
        "deepreason.runtime.progress._atomic_json[run-result.json]",
    ),
}
TERMINAL_PHASE_NESTING_EXCLUSIONS = {
    "deepreason.capabilities.audit.write_tranche_a_audits": frozenset(
        {W10_REPLAY_AND_FINAL_RESULT_PUBLICATION}
    ),
    "deepreason.verification.report.verify_root_report": frozenset(
        {W8_POSTCOMMIT_ROOT_VERIFICATION}
    ),
    (
        "deepreason.application.text_runs."
        "derive_model_execution_summary"
    ): frozenset(
        {
            W2_PRECOMMIT_VERIFICATION,
            W8_POSTCOMMIT_ROOT_VERIFICATION,
        }
    ),
    (
        "deepreason.runtime.terminal_authority."
        "_validate_result_projection_binding"
    ): frozenset({W6_PENDING_RESULT_PUBLICATION}),
}


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
        return (
            min(maximum, max(minimum, 0.5))
            if maximum is not None
            else max(minimum, 0.5)
        )
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


def response_for_schema(schema: dict, _prompt: str) -> dict:
    """Return one semantically conservative value for an advertised schema."""

    title = schema.get("title")
    if (
        RESUMABLE_STOP_MARKER in _prompt.casefold()
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
        _prompt,
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
        raise AssertionError(f"provider fixture cannot satisfy schema {title!r}")
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


_DIAGNOSTIC_LEDGER_LOCK = threading.Lock()
_DIAGNOSTIC_LOCAL = threading.local()
_DIAGNOSTIC_LEDGER_PATH: Path | None = None
_DIAGNOSTIC_RECORD_COUNT = 0
_DIAGNOSTIC_OVERFLOW_RECORDED = False
_DIAGNOSTIC_WRITE_FAILED = False
_DIAGNOSTIC_LAST_LIVENESS: str | None = None
_DIAGNOSTIC_WRAPPERS_INSTALLED = False


def _diagnostic_stack() -> list[str]:
    stack = getattr(_DIAGNOSTIC_LOCAL, "phase_stack", None)
    if stack is None:
        stack = []
        _DIAGNOSTIC_LOCAL.phase_stack = stack
    return stack


def _diagnostic_error_overrides() -> dict[int, str]:
    values = getattr(_DIAGNOSTIC_LOCAL, "error_overrides", None)
    if values is None:
        values = {}
        _DIAGNOSTIC_LOCAL.error_overrides = values
    return values


def _diagnostic_actor() -> str:
    current = threading.current_thread()
    try:
        module = __import__(
            "deepreason.application.text_runs",
            fromlist=["TEXT_RUN_WORKERS"],
        )
        registry = module.TEXT_RUN_WORKERS
        if any(thread is current for thread in registry.threads.values()):
            return "worker"
    except BaseException:
        pass
    return "mcp_server" if current is threading.main_thread() else "other"


def _bounded_elapsed_ms(started: float, *, clock=time.perf_counter) -> int:
    try:
        elapsed = int(max(0.0, clock() - started) * 1000)
    except BaseException:
        return 0
    return min(elapsed, 86_400_000)


def _append_diagnostic_record(record: dict[str, object]) -> None:
    """Append one bounded closed record without affecting production flow."""

    global _DIAGNOSTIC_RECORD_COUNT
    global _DIAGNOSTIC_OVERFLOW_RECORDED
    global _DIAGNOSTIC_WRITE_FAILED
    path = _DIAGNOSTIC_LEDGER_PATH
    if path is None or _DIAGNOSTIC_WRITE_FAILED:
        return
    try:
        encoded = (
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode(
                "ascii"
            )
            + b"\n"
        )
    except BaseException:
        return
    with _DIAGNOSTIC_LEDGER_LOCK:
        if _DIAGNOSTIC_WRITE_FAILED:
            return
        if _DIAGNOSTIC_RECORD_COUNT >= TERMINAL_DIAGNOSTIC_MAX_RECORDS - 1:
            if _DIAGNOSTIC_OVERFLOW_RECORDED:
                return
            encoded = b'{"overflow":true}\n'
            _DIAGNOSTIC_OVERFLOW_RECORDED = True
        try:
            with path.open("ab") as stream:
                stream.write(encoded)
        except BaseException:
            _DIAGNOSTIC_WRITE_FAILED = True
            return
        _DIAGNOSTIC_RECORD_COUNT += 1


def _record_diagnostic_phase(
    phase: str,
    edge: str,
    *,
    elapsed_ms: int = 0,
    actor: str | None = None,
    error_family: str = ERROR_NONE,
) -> None:
    if (
        phase not in ALLOWED_DIAGNOSTIC_PHASES
        or edge not in ALLOWED_DIAGNOSTIC_EDGES
        or error_family not in ALLOWED_DIAGNOSTIC_ERROR_FAMILIES
    ):
        return
    fixed_actor = actor or _diagnostic_actor()
    if fixed_actor not in ALLOWED_DIAGNOSTIC_ACTORS:
        fixed_actor = "other"
    _append_diagnostic_record(
        {
            "actor": fixed_actor,
            "edge": edge,
            "elapsed_ms": (
                elapsed_ms
                if type(elapsed_ms) is int and 0 <= elapsed_ms <= 86_400_000
                else 0
            ),
            "error_family": error_family,
            "phase": phase,
        }
    )


def _record_worker_liveness(value: str) -> None:
    global _DIAGNOSTIC_LAST_LIVENESS
    if value not in ALLOWED_WORKER_LIVENESS:
        value = "unknown"
    with _DIAGNOSTIC_LEDGER_LOCK:
        if value == _DIAGNOSTIC_LAST_LIVENESS:
            return
        _DIAGNOSTIC_LAST_LIVENESS = value
    _append_diagnostic_record(
        {"observation": "worker_liveness", "value": value}
    )


def _record_recovery_sentinel() -> None:
    _append_diagnostic_record(
        {
            "observation": "terminal_publication_recovery_required",
            "value": True,
        }
    )


def _safe_diagnostic_actor() -> str:
    try:
        actor = _diagnostic_actor()
    except BaseException:
        return "other"
    return actor if actor in ALLOWED_DIAGNOSTIC_ACTORS else "other"


def _safe_diagnostic_clock(clock) -> float | None:
    try:
        return float(clock())
    except BaseException:
        return None


def _safe_diagnostic_stack() -> list[str] | None:
    try:
        return _diagnostic_stack()
    except BaseException:
        return None


def _safe_record_diagnostic_phase(
    phase: str,
    edge: str,
    *,
    elapsed_ms: int = 0,
    actor: str | None = None,
    error_family: str = ERROR_NONE,
) -> None:
    try:
        _record_diagnostic_phase(
            phase,
            edge,
            elapsed_ms=elapsed_ms,
            actor=actor,
            error_family=error_family,
        )
    except BaseException:
        return


def _safe_record_worker_liveness(value: str) -> None:
    try:
        _record_worker_liveness(value)
    except BaseException:
        return


def _safe_record_recovery_sentinel() -> None:
    try:
        _record_recovery_sentinel()
    except BaseException:
        return


def _worker_liveness(registry, root: Path) -> str:
    try:
        key = str(Path(root).resolve())
        if key not in registry.threads:
            return "not_registered"
        thread = registry.threads[key]
        return "alive" if thread.is_alive() else "not_alive"
    except BaseException:
        return "unknown"


def _closed_error_family(error: BaseException, *, phase: str) -> str:
    override = _diagnostic_error_overrides().get(id(error))
    if override in ALLOWED_DIAGNOSTIC_ERROR_FAMILIES:
        return override
    try:
        from deepreason.locking import ProcessLockBusy

        if isinstance(error, ProcessLockBusy):
            return ERROR_PROCESS_LOCK_BUSY
    except BaseException:
        pass
    try:
        from deepreason.run_manifest import RunManifestError

        if isinstance(error, RunManifestError):
            return ERROR_MANIFEST_ADMISSION
    except BaseException:
        pass
    if isinstance(error, ValueError):
        try:
            message = str(error)
        except BaseException:
            message = ""
        if message.startswith("RUN_RESULT_NOT_READY"):
            return ERROR_RUN_RESULT_NOT_READY
        if phase == W9_REPLAY_BINDING_VALIDATION or message.startswith(
            "TERMINAL_REPLAY_VALIDATION_BINDING"
        ):
            return ERROR_REPLAY_BINDING
        if phase in {
            W7_FRESH_REPLAY_DERIVATION,
            W8_POSTCOMMIT_ROOT_VERIFICATION,
        } or message.startswith("TERMINAL_REPLAY_VALIDATION"):
            return ERROR_REPLAY_VERIFICATION
        if message.startswith("TERMINAL_"):
            return ERROR_TERMINAL_AUTHORITY
        return ERROR_VALUE_OTHER
    if isinstance(error, OSError):
        return ERROR_OS_OTHER
    return ERROR_UNEXPECTED


def _safe_error_family(error: BaseException, *, phase: str) -> str:
    try:
        family = _closed_error_family(error, phase=phase)
    except BaseException:
        return ERROR_UNEXPECTED
    return (
        family
        if family in ALLOWED_DIAGNOSTIC_ERROR_FAMILIES
        else ERROR_UNEXPECTED
    )


def _clear_diagnostic_error_override(error: BaseException) -> None:
    try:
        _diagnostic_error_overrides().pop(id(error), None)
    except BaseException:
        return


def _invoke_diagnostic_phase(
    phase: str,
    function,
    args: tuple,
    kwargs: dict,
    *,
    clock=time.perf_counter,
):
    actor = _safe_diagnostic_actor()
    started = _safe_diagnostic_clock(clock)
    _safe_record_diagnostic_phase(phase, "enter", actor=actor)
    stack = _safe_diagnostic_stack()
    pushed = False
    outermost = False
    if stack is not None:
        try:
            stack.append(phase)
            pushed = True
            outermost = len(stack) == 1
        except BaseException:
            stack = None
    observed_error: BaseException | None = None
    try:
        value = function(*args, **kwargs)
    except BaseException as error:
        observed_error = error
        _safe_record_diagnostic_phase(
            phase,
            "error",
            elapsed_ms=(
                _bounded_elapsed_ms(started, clock=clock)
                if started is not None
                else 0
            ),
            actor=actor,
            error_family=_safe_error_family(error, phase=phase),
        )
        raise
    else:
        _safe_record_diagnostic_phase(
            phase,
            "return",
            elapsed_ms=(
                _bounded_elapsed_ms(started, clock=clock)
                if started is not None
                else 0
            ),
            actor=actor,
        )
        return value
    finally:
        if observed_error is not None and outermost:
            _clear_diagnostic_error_override(observed_error)
        if pushed and stack is not None:
            try:
                if stack and stack[-1] == phase:
                    stack.pop()
            except BaseException:
                pass


def _diagnostic_phase_wrapper(
    function,
    phase: str,
    *,
    clock=time.perf_counter,
    skip_inside: frozenset[str] = frozenset(),
):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        stack = _safe_diagnostic_stack()
        if stack is not None and any(
            value in skip_inside for value in stack
        ):
            return function(*args, **kwargs)
        return _invoke_diagnostic_phase(
            phase,
            function,
            args,
            kwargs,
            clock=clock,
        )

    return wrapped


def _terminal_lock_acquire_wrapper(function, *, clock=time.perf_counter):
    @functools.wraps(function)
    def wrapped(lock, *args, **kwargs):
        if getattr(lock, "owner", None) != "terminal-commitment":
            return function(lock, *args, **kwargs)
        actor = _safe_diagnostic_actor()
        started = _safe_diagnostic_clock(clock)
        _safe_record_diagnostic_phase(
            TERMINAL_LOCK,
            "wait_start",
            actor=actor,
        )
        try:
            value = function(lock, *args, **kwargs)
        except BaseException as error:
            _safe_record_diagnostic_phase(
                TERMINAL_LOCK,
                "error",
                elapsed_ms=(
                    _bounded_elapsed_ms(started, clock=clock)
                    if started is not None
                    else 0
                ),
                actor=actor,
                error_family=_safe_error_family(
                    error,
                    phase=TERMINAL_LOCK,
                ),
            )
            raise
        _safe_record_diagnostic_phase(
            TERMINAL_LOCK,
            "acquired",
            elapsed_ms=(
                _bounded_elapsed_ms(started, clock=clock)
                if started is not None
                else 0
            ),
            actor=actor,
        )
        return value

    return wrapped


def _terminal_lock_release_wrapper(function, *, clock=time.perf_counter):
    @functools.wraps(function)
    def wrapped(lock, *args, **kwargs):
        if getattr(lock, "owner", None) != "terminal-commitment":
            return function(lock, *args, **kwargs)
        actor = _safe_diagnostic_actor()
        started = _safe_diagnostic_clock(clock)
        try:
            value = function(lock, *args, **kwargs)
        except BaseException as error:
            _safe_record_diagnostic_phase(
                TERMINAL_LOCK,
                "error",
                elapsed_ms=(
                    _bounded_elapsed_ms(started, clock=clock)
                    if started is not None
                    else 0
                ),
                actor=actor,
                error_family=_safe_error_family(
                    error,
                    phase=TERMINAL_LOCK,
                ),
            )
            raise
        _safe_record_diagnostic_phase(
            TERMINAL_LOCK,
            "released",
            elapsed_ms=(
                _bounded_elapsed_ms(started, clock=clock)
                if started is not None
                else 0
            ),
            actor=actor,
        )
        return value

    return wrapped


def _application_wrapper(function, phase: str, *, clock=time.perf_counter):
    @functools.wraps(function)
    def wrapped(service, intent, *args, **kwargs):
        try:
            root = getattr(intent, "root", None)
            liveness = (
                _worker_liveness(service.registry, Path(root))
                if root is not None
                else "unknown"
            )
        except BaseException:
            liveness = "unknown"
        _safe_record_worker_liveness(liveness)
        return _invoke_diagnostic_phase(
            phase,
            function,
            (service, intent, *args),
            kwargs,
            clock=clock,
        )

    return wrapped


def _record_worker_exit_after_join(worker: threading.Thread) -> None:
    try:
        worker.join()
        liveness = "alive" if worker.is_alive() else "not_alive"
    except BaseException:
        liveness = "unknown"
    _safe_record_worker_liveness(liveness)


def _worker_wrapper(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        try:
            worker = threading.current_thread()
        except BaseException:
            worker = None
        _safe_record_worker_liveness("alive")
        try:
            return function(*args, **kwargs)
        finally:
            if worker is not None and worker is not threading.main_thread():
                try:
                    threading.Thread(
                        target=_record_worker_exit_after_join,
                        args=(worker,),
                        daemon=True,
                    ).start()
                except BaseException:
                    _safe_record_worker_liveness("unknown")

    return wrapped


def _progress_emit_wrapper(function):
    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        value = function(*args, **kwargs)
        try:
            message = getattr(value, "message", None)
            if message == TERMINAL_PUBLICATION_RECOVERY_SENTINEL:
                _safe_record_recovery_sentinel()
        except BaseException:
            pass
        return value

    return wrapped


def _atomic_json_wrapper(function, *, clock=time.perf_counter):
    @functools.wraps(function)
    def wrapped(path, *args, **kwargs):
        try:
            name = Path(path).name
        except BaseException:
            name = ""
        stack = _safe_diagnostic_stack()
        outer = stack[-1] if stack else None
        explicit_phase = (
            W10_REPLAY_AND_FINAL_RESULT_PUBLICATION
            if name == "run-result.json" and outer is None
            else None
        )
        started = _safe_diagnostic_clock(clock)
        actor = _safe_diagnostic_actor()
        if explicit_phase is not None:
            _safe_record_diagnostic_phase(
                explicit_phase,
                "enter",
                actor=actor,
            )
            if stack is not None:
                try:
                    stack.append(explicit_phase)
                except BaseException:
                    stack = None
        try:
            value = function(path, *args, **kwargs)
        except BaseException as error:
            if name == "REPLAY_VALIDATION.json":
                family = ERROR_REPLAY_SIDECAR_PERSISTENCE
            elif name == "run-result.json":
                family = ERROR_FINAL_RESULT_PERSISTENCE
            else:
                family = ERROR_ATOMIC_PERSISTENCE
            if outer is not None:
                try:
                    _diagnostic_error_overrides()[id(error)] = family
                except BaseException:
                    pass
            if explicit_phase is not None:
                _safe_record_diagnostic_phase(
                    explicit_phase,
                    "error",
                    elapsed_ms=(
                        _bounded_elapsed_ms(started, clock=clock)
                        if started is not None
                        else 0
                    ),
                    actor=actor,
                    error_family=family,
                )
            raise
        else:
            if explicit_phase is not None:
                _safe_record_diagnostic_phase(
                    explicit_phase,
                    "return",
                    elapsed_ms=(
                        _bounded_elapsed_ms(started, clock=clock)
                        if started is not None
                        else 0
                    ),
                    actor=actor,
                )
            return value
        finally:
            if explicit_phase is not None and stack is not None:
                try:
                    if stack and stack[-1] == explicit_phase:
                        stack.pop()
                except BaseException:
                    pass

    return wrapped


def _configure_terminal_diagnostic_ledger(path: Path) -> None:
    global _DIAGNOSTIC_LEDGER_PATH
    global _DIAGNOSTIC_RECORD_COUNT
    global _DIAGNOSTIC_OVERFLOW_RECORDED
    global _DIAGNOSTIC_WRITE_FAILED
    global _DIAGNOSTIC_LAST_LIVENESS
    _DIAGNOSTIC_LEDGER_PATH = Path(path)
    _DIAGNOSTIC_RECORD_COUNT = 0
    _DIAGNOSTIC_OVERFLOW_RECORDED = False
    _DIAGNOSTIC_WRITE_FAILED = False
    _DIAGNOSTIC_LAST_LIVENESS = None


def _install_terminal_diagnostics_if_enabled() -> None:
    global _DIAGNOSTIC_WRAPPERS_INSTALLED
    if (
        os.environ.get(TERMINAL_DIAGNOSTIC_ENABLE_ENV) != "1"
        or not os.environ.get(TERMINAL_DIAGNOSTIC_LEDGER_ENV)
        or _DIAGNOSTIC_WRAPPERS_INSTALLED
    ):
        return
    try:
        ledger = Path(os.environ[TERMINAL_DIAGNOSTIC_LEDGER_ENV])
        _configure_terminal_diagnostic_ledger(ledger)

        from deepreason import locking
        from deepreason.application import models as application_models
        from deepreason.application import text_runs
        from deepreason.capabilities import audit as capability_audit
        from deepreason.runtime import progress, terminal_authority
        from deepreason.verification import report as verification_report

        capability_audit.write_tranche_a_audits = _diagnostic_phase_wrapper(
            capability_audit.write_tranche_a_audits,
            W1_PRECOMMIT_AUDITS,
            skip_inside=TERMINAL_PHASE_NESTING_EXCLUSIONS[
                "deepreason.capabilities.audit.write_tranche_a_audits"
            ],
        )
        verification_report.verify_root_report = _diagnostic_phase_wrapper(
            verification_report.verify_root_report,
            W2_PRECOMMIT_VERIFICATION,
            skip_inside=TERMINAL_PHASE_NESTING_EXCLUSIONS[
                "deepreason.verification.report.verify_root_report"
            ],
        )
        text_runs.derive_model_execution_summary = _diagnostic_phase_wrapper(
            text_runs.derive_model_execution_summary,
            W3_TERMINAL_AUTHORITY_STATE,
            skip_inside=TERMINAL_PHASE_NESTING_EXCLUSIONS[
                "deepreason.application.text_runs."
                "derive_model_execution_summary"
            ],
        )
        application_models.derive_model_execution_summary = (
            text_runs.derive_model_execution_summary
        )
        terminal_authority._expected_commitment = _diagnostic_phase_wrapper(
            terminal_authority._expected_commitment,
            W4_TERMINAL_DRAFT_CONSTRUCTION,
        )
        terminal_authority.ensure_terminal_commitment = (
            _diagnostic_phase_wrapper(
                terminal_authority.ensure_terminal_commitment,
                W5_COMMITMENT_ENSURE,
            )
        )
        terminal_authority._prepare_terminal_result_locked = (
            _diagnostic_phase_wrapper(
                terminal_authority._prepare_terminal_result_locked,
                W6_PENDING_RESULT_PUBLICATION,
            )
        )
        terminal_authority._fresh_replay_validation = (
            _diagnostic_phase_wrapper(
                terminal_authority._fresh_replay_validation,
                W7_FRESH_REPLAY_DERIVATION,
            )
        )
        verification_report.verify_post_commit_report = (
            _diagnostic_phase_wrapper(
                verification_report.verify_post_commit_report,
                W8_POSTCOMMIT_ROOT_VERIFICATION,
            )
        )
        terminal_authority._expected_replay_binding = (
            _diagnostic_phase_wrapper(
                terminal_authority._expected_replay_binding,
                W9_REPLAY_BINDING_VALIDATION,
            )
        )
        terminal_authority._validate_result_projection_binding = (
            _diagnostic_phase_wrapper(
                terminal_authority._validate_result_projection_binding,
                W9_REPLAY_BINDING_VALIDATION,
                skip_inside=TERMINAL_PHASE_NESTING_EXCLUSIONS[
                    "deepreason.runtime.terminal_authority."
                    "_validate_result_projection_binding"
                ],
            )
        )
        terminal_authority._publish_current_replay_projection = (
            _diagnostic_phase_wrapper(
                terminal_authority._publish_current_replay_projection,
                W10_REPLAY_AND_FINAL_RESULT_PUBLICATION,
            )
        )
        locking.ProcessLock.acquire = _terminal_lock_acquire_wrapper(
            locking.ProcessLock.acquire
        )
        locking.ProcessLock.release = _terminal_lock_release_wrapper(
            locking.ProcessLock.release
        )
        text_runs.TextRunApplicationService.inspect = _application_wrapper(
            text_runs.TextRunApplicationService.inspect,
            APPLICATION_INSPECT,
        )
        text_runs.TextRunApplicationService.result = _application_wrapper(
            text_runs.TextRunApplicationService.result,
            APPLICATION_RESULT,
        )
        text_runs.TextRunApplicationService._worker = staticmethod(
            _worker_wrapper(text_runs.TextRunApplicationService._worker)
        )
        progress.ProgressSink.emit = _progress_emit_wrapper(
            progress.ProgressSink.emit
        )
        progress._atomic_json = _atomic_json_wrapper(progress._atomic_json)
        terminal_authority._atomic_json = progress._atomic_json
        _DIAGNOSTIC_WRAPPERS_INSTALLED = True
    except BaseException:
        _append_diagnostic_record(
            {"observation": "instrumentation_failure", "value": True}
        )


_STATE_LOCK = threading.Lock()


def _record_call(
    state_path: Path, *, qualification: bool, schema_title: str | None
) -> None:
    with _STATE_LOCK:
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
        else:
            state = {
                "errors": [],
                "qualification_calls": 0,
                "schema_titles": {},
                "total_calls": 0,
            }
        state["total_calls"] += 1
        state["qualification_calls"] += int(qualification)
        title = schema_title or "<untitled>"
        titles = state.setdefault("schema_titles", {})
        titles[title] = int(titles.get(title, 0)) + 1
        temporary = state_path.with_name(state_path.name + ".tmp")
        temporary.write_text(
            json.dumps(state, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, state_path)


def _record_error(state_path: Path, error: BaseException) -> None:
    with _STATE_LOCK:
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
        else:
            state = {
                "errors": [],
                "qualification_calls": 0,
                "schema_titles": {},
                "total_calls": 0,
            }
        state.setdefault("errors", []).append(
            {"message": str(error), "type": type(error).__name__}
        )
        temporary = state_path.with_name(state_path.name + ".tmp")
        temporary.write_text(
            json.dumps(state, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, state_path)


def _handler(state_path: Path):
    class Handler(BaseHTTPRequestHandler):
        server_version = "DeepReasonLoopback/1"

        def log_message(self, _format, *_args):
            return

        def do_POST(self):  # noqa: N802 - BaseHTTPRequestHandler API
            try:
                if self.path != "/v1/chat/completions":
                    self.send_error(404)
                    return
                if self.headers.get("Authorization") != f"Bearer {CREDENTIAL}":
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
                _record_call(
                    state_path,
                    qualification="Qualification case " in prompt,
                    schema_title=schema.get("title"),
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
                        "total_tokens": max(
                            2, (len(prompt) + len(content)) // 4
                        ),
                    },
                }
                encoded = json.dumps(payload, separators=(",", ":")).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
            except Exception as error:  # fixture failures must fail the real call
                _record_error(state_path, error)
                encoded = json.dumps(
                    {"error": {"type": type(error).__name__, "message": str(error)}}
                ).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

    return Handler


class _ReusableLoopbackServer(ThreadingHTTPServer):
    allow_reuse_address = True


def _start_if_enabled() -> None:
    if os.environ.get(ENABLE_ENV) != "1":
        return
    port = int(os.environ[PORT_ENV])
    state_path = Path(os.environ[STATE_ENV])
    server = _ReusableLoopbackServer(("127.0.0.1", port), _handler(state_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # The global reference keeps the listening socket alive for the process.
    globals()["_ACTIVE_SERVER"] = server
    ready_path = os.environ.get(READY_ENV)
    if ready_path:
        try:
            Path(ready_path).write_bytes(b"ready\n")
        except OSError:
            # Marker absence remains an unknown diagnostic state.  It must not
            # change whether the deterministic fixture can serve requests.
            pass


_start_if_enabled()
_install_terminal_diagnostics_if_enabled()
