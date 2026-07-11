"""Harness-owned website workflow state machine.

The state machine selects every transition.  Models only ever see the pack
for the currently selected problem and return their existing bounded role
value; no model output can name a state or choose a retry.  Generated plans,
designs, component fragments and assembled pages continue through the same
commitments, criticism, guards, adjudication and append-only event log used
before this extraction.

``easy.make`` delegates its chunked compatibility path here.  The module is
intentionally independent of CLI/config compilation and endpoint routing.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shlex
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from deepreason.llm.budget import TokenBudgetExceeded
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.repair import SchemaRepairError


_COMPACT_CALL_ERRORS = (SchemaRepairError, EndpointError, TokenBudgetExceeded)
# ``CompactDesignOutline`` itself permits at most twelve components.  Keep an
# explicit executor ceiling here as a defence-in-depth bound for library
# callers that invoke the batch helper with hand-built objects.
_MAX_COMPONENT_WORKERS = 12


@dataclass(frozen=True)
class _CompactCallResult:
    """One model exchange collected before the event-log writer sees it."""

    label: str
    output: Any | None = None
    raw_ref: str | None = None
    llm_call: Any | None = None
    spend_call: Any | None = None
    tokens: int = 0
    error: Exception | None = None


class _LockedBlobStore:
    """Serialize content-addressed writes without serializing model calls.

    ``BlobStore.put`` uses a process-scoped temporary filename.  Concurrent
    identical model outputs could otherwise race on that temporary path even
    though the final blobs are immutable.  Reads remain ordinary immutable
    reads; only the very short filesystem mutation is fenced.
    """

    def __init__(self, store, lock: threading.Lock):
        self._store = store
        self._lock = lock

    def put(self, data: bytes) -> str:
        with self._lock:
            return self._store.put(data)

    def get(self, ref: str) -> bytes:
        return self._store.get(ref)

    def __getattr__(self, name: str):
        return getattr(self._store, name)


class WebsiteStage(str, Enum):
    PLAN = "PLAN"
    DESIGN_OUTLINE = "DESIGN_OUTLINE"
    COMPONENT_CONTRACTS = "COMPONENT_CONTRACTS"
    MANIFEST_COMPILE = "MANIFEST_COMPILE"
    MANIFEST_VALIDATE = "MANIFEST_VALIDATE"
    COMPONENT_BUILD = "COMPONENT_BUILD"
    ASSEMBLE = "ASSEMBLE"
    INTEGRATION_VALIDATE = "INTEGRATION_VALIDATE"
    EXPORT = "EXPORT"


class StageOutcome(str, Enum):
    SUCCESS = "success"
    RETRYABLE_FAILURE = "retryable_failure"
    TERMINAL_FAILURE = "terminal_failure"


class NextAction(str, Enum):
    ADVANCE = "advance"
    RETRY_STAGE = "retry_stage"
    REPAIR_COMPONENT_CONTRACT = "repair_component_contract"
    REPAIR_COMPONENT = "repair_component"
    TERMINATE = "terminate"
    COMPLETE = "complete"


class StageResult(BaseModel):
    """Typed operational result; it carries no epistemic status."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    stage: WebsiteStage
    outcome: StageOutcome
    canonical_outputs: list[str] = Field(default_factory=list)
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)
    next_action: NextAction
    attempt: int = Field(default=1, ge=1)


class TerminalSummary(BaseModel):
    """Machine-readable failure report; never an invalid page export."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    failed_stage: WebsiteStage
    direct_calls: int = Field(default=0, ge=0)
    compact_calls: int = Field(default=0, ge=0)
    schema_failures_by_path: dict[str, int] = Field(default_factory=dict)
    manifest_wf_failures_by_code: dict[str, int] = Field(default_factory=dict)
    critic_refutations: int = Field(default=0, ge=0)
    last_valid_intermediate: str | None = None
    checkpoint_ref: str
    manifest_sha256: str | None = None
    resume_command: str
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)


class WorkflowCheckpoint(BaseModel):
    """Process-only restart evidence; never enters the artifact graph."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    run_root: str
    out_dir: str
    description: str
    manifest_sha256: str | None = None
    stage: WebsiteStage
    complete: bool = False
    attempts: dict[str, int] = Field(default_factory=dict)
    history: list[StageResult] = Field(default_factory=list)
    event_seq: int = Field(default=0, ge=0)
    token_budget: int | None = Field(default=None, ge=0)
    spent_tokens: int = Field(default=0, ge=0)
    remaining_tokens: int | None = Field(default=None, ge=0)
    direct_calls: int = Field(default=0, ge=0)
    compact_calls: int = Field(default=0, ge=0)
    schema_failures_by_path: dict[str, int] = Field(default_factory=dict)
    manifest_wf_failures_by_code: dict[str, int] = Field(default_factory=dict)
    last_valid_intermediate: str | None = None
    canonical_intermediates: dict[str, Any] = Field(default_factory=dict)


class WebsiteCheckpointError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


_NEXT_STAGE = {
    WebsiteStage.PLAN: WebsiteStage.DESIGN_OUTLINE,
    WebsiteStage.DESIGN_OUTLINE: WebsiteStage.COMPONENT_CONTRACTS,
    WebsiteStage.COMPONENT_CONTRACTS: WebsiteStage.MANIFEST_COMPILE,
    WebsiteStage.MANIFEST_COMPILE: WebsiteStage.MANIFEST_VALIDATE,
    WebsiteStage.MANIFEST_VALIDATE: WebsiteStage.COMPONENT_BUILD,
    WebsiteStage.COMPONENT_BUILD: WebsiteStage.ASSEMBLE,
    WebsiteStage.ASSEMBLE: WebsiteStage.INTEGRATION_VALIDATE,
    WebsiteStage.INTEGRATION_VALIDATE: WebsiteStage.EXPORT,
}


class WebsiteStateMachine:
    """Pure deterministic transition controller.

    Callers supply facts (success or typed failure); this object alone chooses
    the resulting action and state.  Responses from an endpoint are never
    accepted as ``next_action`` input.
    """

    def __init__(self):
        self.stage = WebsiteStage.PLAN
        self.attempts: dict[WebsiteStage, int] = {self.stage: 1}
        self.history: list[StageResult] = []
        self.complete = False

    @property
    def attempt(self) -> int:
        return self.attempts.get(self.stage, 1)

    def success(self, canonical_outputs: list[str] | None = None) -> StageResult:
        if self.complete:
            raise RuntimeError("website workflow is already complete")
        current = self.stage
        final = current == WebsiteStage.EXPORT
        result = StageResult(
            stage=current,
            outcome=StageOutcome.SUCCESS,
            canonical_outputs=list(canonical_outputs or []),
            next_action=NextAction.COMPLETE if final else NextAction.ADVANCE,
            attempt=self.attempt,
        )
        self.history.append(result)
        if final:
            self.complete = True
        else:
            self.stage = _NEXT_STAGE[current]
            self.attempts.setdefault(self.stage, 1)
        return result

    def retryable_failure(
        self,
        diagnostics: list[dict[str, Any]],
        *,
        component_contract: bool = False,
        component: bool = False,
    ) -> StageResult:
        if self.complete:
            raise RuntimeError("website workflow is already complete")
        if component_contract:
            action = NextAction.REPAIR_COMPONENT_CONTRACT
        elif component:
            action = NextAction.REPAIR_COMPONENT
        else:
            action = NextAction.RETRY_STAGE
        result = StageResult(
            stage=self.stage,
            outcome=StageOutcome.RETRYABLE_FAILURE,
            diagnostics=diagnostics,
            next_action=action,
            attempt=self.attempt,
        )
        self.history.append(result)
        self.attempts[self.stage] = self.attempt + 1
        return result

    def terminal_failure(self, diagnostics: list[dict[str, Any]]) -> StageResult:
        if self.complete:
            raise RuntimeError("website workflow is already complete")
        result = StageResult(
            stage=self.stage,
            outcome=StageOutcome.TERMINAL_FAILURE,
            diagnostics=diagnostics,
            next_action=NextAction.TERMINATE,
            attempt=self.attempt,
        )
        self.history.append(result)
        self.complete = True
        return result


class WebsiteWorkflow:
    """Run the existing chunked website process through explicit states."""

    def __init__(
        self,
        harness,
        cfg,
        description: str,
        out_dir: Path,
        cycles: int,
        token_budget: int | None,
        echo,
        *,
        config_path: Path | None = None,
        run_manifest=None,
    ):
        self.harness = harness
        self.cfg = cfg
        self.description = description
        self.out_dir = Path(out_dir)
        self.cycles = cycles
        self.token_budget = token_budget
        self.echo = echo
        self.config_path = config_path
        self.run_manifest = self._resolve_run_manifest(run_manifest)
        self.machine = WebsiteStateMachine()
        self.spent = 0
        self.direct_calls = 0
        self.compact_calls = 0
        self.schema_failures_by_path: dict[str, int] = {}
        self.manifest_wf_failures_by_code: dict[str, int] = {}
        self.last_valid_intermediate: str | None = None
        self.plan_id: str | None = None
        self.design_id: str | None = None
        self.manifest = None
        self.resolved_imports = None
        self.chosen: dict[str, str] = {}
        self.assembled = None
        self.compact_outline = None
        self.compact_contracts: list[Any] = []
        self.compact_art_direction = None
        self.imports_resolved = False
        self.integration_implicated: list[str] = []
        self.integration_repaired: list[str] = []
        self.integration_reassembled = False
        self._compact_adapter_instance = None
        self._compact_meter = None
        self._blob_write_lock = threading.Lock()
        self._resumed_from_checkpoint = False
        self._load_checkpoint_if_present()

    def _resolve_run_manifest(self, explicit):
        """Use the immutable run-root manifest when the facade has one.

        ``easy.make`` receives a materialized Config for compatibility, so
        concurrency is intentionally not copied into Config's epistemic knob
        surface.  The canonical persisted RunManifest remains the authority.
        Direct library calls without one retain profile defaults.
        """
        if explicit is not None:
            return explicit
        from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

        path = Path(self.harness.root) / MANIFEST_NAME
        return load_run_manifest(path) if path.exists() else None

    def _manifest_sha256(self) -> str | None:
        return getattr(self.run_manifest, "sha256", None) if self.run_manifest else None

    @staticmethod
    def _replay_checkpoint_machine(checkpoint: WorkflowCheckpoint) -> WebsiteStateMachine:
        machine = WebsiteStateMachine()
        for index, saved in enumerate(checkpoint.history):
            if saved.outcome == StageOutcome.SUCCESS:
                actual = machine.success(saved.canonical_outputs)
            elif saved.outcome == StageOutcome.RETRYABLE_FAILURE:
                actual = machine.retryable_failure(
                    saved.diagnostics,
                    component_contract=(
                        saved.next_action == NextAction.REPAIR_COMPONENT_CONTRACT
                    ),
                    component=saved.next_action == NextAction.REPAIR_COMPONENT,
                )
            else:
                actual = machine.terminal_failure(saved.diagnostics)
            if actual != saved:
                raise WebsiteCheckpointError(
                    "CHECKPOINT_HISTORY_INVALID", "transition replay mismatch"
                )
            if (
                saved.outcome == StageOutcome.TERMINAL_FAILURE
                and index < len(checkpoint.history) - 1
            ):
                machine.complete = False
                machine.attempts[machine.stage] = saved.attempt + 1
        attempts = {stage.value: count for stage, count in machine.attempts.items()}
        if (
            machine.stage != checkpoint.stage
            or machine.complete != checkpoint.complete
            or attempts != checkpoint.attempts
        ):
            raise WebsiteCheckpointError(
                "CHECKPOINT_STATE_INVALID", "cursor disagrees with history"
            )
        if (
            checkpoint.complete and checkpoint.history
            and checkpoint.history[-1].outcome == StageOutcome.TERMINAL_FAILURE
        ):
            machine.complete = False
            machine.attempts[machine.stage] = checkpoint.history[-1].attempt + 1
        return machine

    @staticmethod
    def _restore_imports(value):
        if value is None:
            return None
        if not isinstance(value, dict) or set(value) == {"type"}:
            raise WebsiteCheckpointError(
                "CHECKPOINT_INTERMEDIATE_INVALID", "incomplete resolved imports"
            )
        from deepreason.imports import ResolvedImportSet
        from deepreason.manifest import DependencyRequest

        restored = dict(value)
        restored["requests"] = tuple(
            DependencyRequest.model_validate(item)
            for item in restored.get("requests", [])
        )
        for field in (
            "capsule_ids", "alias_ids", "archive_ids", "packages", "evidence_ids"
        ):
            restored[field] = tuple(restored.get(field, []))
        return ResolvedImportSet(**restored)

    def _restore_intermediates(self, checkpoint: WorkflowCheckpoint) -> None:
        from deepreason.manifest import Manifest
        from deepreason.ontology import Status
        from deepreason.workflows.manifest_compiler import (
            CompactArtDirection, CompactComponentContract, CompactDesignOutline,
        )

        value = checkpoint.canonical_intermediates
        try:
            self.plan_id = value.get("plan_id")
            self.design_id = value.get("design_id")
            self.compact_outline = (
                CompactDesignOutline.model_validate(value["outline"])
                if value.get("outline") is not None else None
            )
            self.compact_contracts = [
                CompactComponentContract.model_validate(item)
                for item in value.get("component_contracts", [])
            ]
            self.compact_art_direction = (
                CompactArtDirection.model_validate(value["art_direction"])
                if value.get("art_direction") is not None else None
            )
            self.manifest = (
                Manifest.model_validate(value["manifest"])
                if value.get("manifest") is not None else None
            )
            self.chosen = {
                str(name): str(aid)
                for name, aid in (value.get("chosen_components") or {}).items()
            }
            assembled_id = value.get("assembled_id")
            self.assembled = (
                self.harness.state.artifacts[assembled_id] if assembled_id else None
            )
            self.resolved_imports = self._restore_imports(value.get("resolved_imports"))
            self.imports_resolved = bool(value.get(
                "imports_resolved",
                checkpoint.stage in {
                    WebsiteStage.COMPONENT_BUILD, WebsiteStage.ASSEMBLE,
                    WebsiteStage.INTEGRATION_VALIDATE, WebsiteStage.EXPORT,
                },
            ))
            self.integration_implicated = sorted(value.get("integration_implicated", []))
            self.integration_repaired = sorted(value.get("integration_repaired", []))
            self.integration_reassembled = bool(value.get("integration_reassembled", False))
        except (KeyError, TypeError, ValueError) as error:
            if isinstance(error, WebsiteCheckpointError):
                raise
            raise WebsiteCheckpointError(
                "CHECKPOINT_INTERMEDIATE_INVALID", str(error)
            ) from error
        referenced = [
            *(item for item in (self.plan_id, self.design_id) if item),
            *self.chosen.values(),
            *(item for item in (
                str(self.assembled.id) if self.assembled is not None else None,
            ) if item),
        ]
        missing = [aid for aid in referenced if aid not in self.harness.state.artifacts]
        if missing:
            raise WebsiteCheckpointError("CHECKPOINT_ARTIFACT_MISSING", ", ".join(missing))
        invalid = [
            aid for aid in referenced
            if self.harness.state.status.get(aid) != Status.ACCEPTED
        ]
        if invalid:
            raise WebsiteCheckpointError(
                "CHECKPOINT_FOUNDATION_INVALID", ", ".join(invalid)
            )
        if (
            checkpoint.complete and checkpoint.history
            and checkpoint.history[-1].outcome == StageOutcome.SUCCESS
        ):
            return
        required = {
            WebsiteStage.DESIGN_OUTLINE: (self.plan_id,),
            WebsiteStage.COMPONENT_CONTRACTS: (self.plan_id,),
            WebsiteStage.MANIFEST_COMPILE: (
                self.plan_id, self.manifest or self.compact_outline,
            ),
            WebsiteStage.MANIFEST_VALIDATE: (
                self.plan_id, self.design_id, self.manifest,
            ),
            WebsiteStage.COMPONENT_BUILD: (
                self.plan_id, self.design_id, self.manifest,
            ),
            WebsiteStage.ASSEMBLE: (self.plan_id, self.design_id, self.manifest),
            WebsiteStage.INTEGRATION_VALIDATE: (
                self.plan_id, self.design_id, self.manifest, self.assembled,
            ),
            WebsiteStage.EXPORT: (
                self.plan_id, self.design_id, self.manifest, self.assembled,
            ),
        }
        if any(item is None for item in required.get(checkpoint.stage, ())):
            raise WebsiteCheckpointError(
                "CHECKPOINT_INTERMEDIATE_MISSING", checkpoint.stage.value
            )
        if (
            checkpoint.stage in {
                WebsiteStage.ASSEMBLE,
                WebsiteStage.INTEGRATION_VALIDATE,
                WebsiteStage.EXPORT,
            }
            and self.manifest is not None
            and set(self.chosen) != {item.name for item in self.manifest.ordered()}
        ):
            raise WebsiteCheckpointError(
                "CHECKPOINT_INTERMEDIATE_MISSING", "component survivor set"
            )

    def _load_checkpoint_if_present(self) -> None:
        path = self.checkpoint_path
        if not path.exists():
            return
        try:
            raw = json.loads(path.read_text())
            checkpoint = WorkflowCheckpoint.model_validate(raw)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            raise WebsiteCheckpointError("CHECKPOINT_INVALID", str(error)) from error
        expected = {
            "run_root": str(Path(self.harness.root).resolve()),
            "out_dir": str(self.out_dir.resolve()),
            "description": self.description,
            "manifest_sha256": self._manifest_sha256(),
        }
        mismatch = [
            field for field, expected_value in expected.items()
            if getattr(checkpoint, field) != expected_value
        ]
        if mismatch:
            raise WebsiteCheckpointError("CHECKPOINT_INCOMPATIBLE", ", ".join(mismatch))
        if checkpoint.event_seq != self.harness._next_seq:
            raise WebsiteCheckpointError(
                "CHECKPOINT_EVENT_FENCE_MISMATCH",
                f"{checkpoint.event_seq} != {self.harness._next_seq}",
            )
        self.machine = self._replay_checkpoint_machine(checkpoint)
        self.spent = checkpoint.spent_tokens
        self.direct_calls = checkpoint.direct_calls
        self.compact_calls = checkpoint.compact_calls
        self.schema_failures_by_path = dict(checkpoint.schema_failures_by_path)
        self.manifest_wf_failures_by_code = dict(checkpoint.manifest_wf_failures_by_code)
        self.last_valid_intermediate = checkpoint.last_valid_intermediate
        if "token_budget" not in raw and checkpoint.remaining_tokens is not None:
            self.token_budget = checkpoint.spent_tokens + (
                self.token_budget or checkpoint.remaining_tokens
            )
        self._restore_intermediates(checkpoint)
        self._resumed_from_checkpoint = True

    def _model_profile(self) -> str:
        if self.run_manifest is not None:
            return self.run_manifest.model_profile
        return getattr(self.cfg, "model_profile", "standard")

    def _component_concurrency(self, task_count: int) -> int:
        """Return the harness-owned, bounded number of transport workers."""
        from deepreason.llm.profiles import get_profile

        profile = get_profile(self._model_profile())
        requested = (
            self.run_manifest.concurrency
            if self.run_manifest is not None
            else profile.default_concurrency
        )
        # Compact/standard default to one.  A compiled RunManifest may make a
        # deliberate higher choice; it is still capped by both the finite
        # outline and the harness-owned executor ceiling.
        return max(
            1,
            min(int(requested), max(1, int(task_count)), _MAX_COMPONENT_WORKERS),
        )

    def _direct_recovery_reason(self, first_seq: int) -> str | None:
        """Return a stable reason only for measured direct-contract failure.

        A merely unpopular/refuted design is not a transport failure and must
        not silently buy a second generation strategy.  Compact recovery is
        enabled only when the direct conjecturer exhausted schema repair or a
        direct candidate demonstrably failed ``manifest_wf``.
        """
        manifest_commitments = {
            commitment_id
            for commitment_id, commitment in self.harness.commitments.items()
            if commitment.eval == "program:manifest_wf"
        }
        if manifest_commitments:
            design_targets = {
                artifact_id
                for artifact_id, artifact in self.harness.state.artifacts.items()
                if manifest_commitments.intersection(artifact.interface.commitments)
                and artifact.provenance.event_seq >= first_seq
            }
            if any(
                warrant.target in design_targets
                and warrant.commitment in manifest_commitments
                and warrant.verdict == "fail"
                for warrant in self.harness.warrants.values()
            ):
                return "manifest-wf-failed"

        for event in self.harness.log.read():
            if event.seq < first_seq or event.llm is None:
                continue
            call = event.llm
            if call.role != "conjecturer":
                continue
            trace = list(getattr(call, "attempt_trace", ()) or ())
            if (
                trace
                and not any(attempt.valid for attempt in trace)
                and not any(attempt.usage_unknown for attempt in trace)
                and any(attempt.diagnostic_ref for attempt in trace)
            ):
                return "schema-repair-exhausted"
            # Compatibility for an older event produced before attempt_trace
            # existed.  The drop label is process-only and cannot be supplied
            # by a model response.
            if any("no schema-valid output" in str(value) for value in event.inputs):
                return "schema-repair-exhausted"
        return None

    def remaining(self) -> int | None:
        return None if self.token_budget is None else max(0, self.token_budget - self.spent)

    def spend(self, accounting: dict[str, Any]) -> None:
        self.spent += (
            accounting.get("metered_tokens")
            or accounting.get("logged_tokens_this_run")
            or 0
        )

    def _record(self, result: StageResult) -> None:
        diagnostics = json.dumps(result.diagnostics, sort_keys=True, separators=(",", ":"))
        self.harness.record_measure(inputs=[
            "website-stage",
            result.stage.value,
            result.outcome.value,
            result.next_action.value,
            str(result.attempt),
            diagnostics,
        ])
        self._write_checkpoint()

    @property
    def checkpoint_path(self) -> Path:
        return Path(self.harness.root) / "website-checkpoint.json"

    @staticmethod
    def _checkpoint_value(value):
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")
        if is_dataclass(value):
            return WebsiteWorkflow._checkpoint_value(asdict(value))
        if isinstance(value, dict):
            return {
                str(key): WebsiteWorkflow._checkpoint_value(item)
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            }
        if isinstance(value, (list, tuple)):
            return [WebsiteWorkflow._checkpoint_value(item) for item in value]
        if hasattr(value, "id"):
            return {"id": str(value.id)}
        return {"type": type(value).__name__}

    def _checkpoint(self) -> WorkflowCheckpoint:
        manifest_sha256 = (
            getattr(self.run_manifest, "sha256", None)
            if self.run_manifest is not None
            else None
        )
        intermediates = {
            "plan_id": self.plan_id,
            "design_id": self.design_id,
            "outline": self._checkpoint_value(self.compact_outline),
            "component_contracts": self._checkpoint_value(self.compact_contracts),
            "art_direction": self._checkpoint_value(self.compact_art_direction),
            "manifest": self._checkpoint_value(self.manifest),
            "chosen_components": self._checkpoint_value(self.chosen),
            "assembled_id": (
                str(self.assembled.id) if self.assembled is not None else None
            ),
            "resolved_imports": self._checkpoint_value(self.resolved_imports),
            "imports_resolved": self.imports_resolved,
            "integration_implicated": list(self.integration_implicated),
            "integration_repaired": list(self.integration_repaired),
            "integration_reassembled": self.integration_reassembled,
        }
        return WorkflowCheckpoint(
            run_root=str(Path(self.harness.root).resolve()),
            out_dir=str(self.out_dir.resolve()),
            description=self.description,
            manifest_sha256=manifest_sha256,
            stage=self.machine.stage,
            complete=self.machine.complete,
            attempts={stage.value: count for stage, count in self.machine.attempts.items()},
            history=list(self.machine.history),
            event_seq=int(getattr(self.harness, "_next_seq", 0)),
            token_budget=self.token_budget,
            spent_tokens=max(0, int(self.spent)),
            remaining_tokens=self.remaining(),
            direct_calls=max(0, int(self.direct_calls)),
            compact_calls=max(0, int(self.compact_calls)),
            schema_failures_by_path=dict(sorted(self.schema_failures_by_path.items())),
            manifest_wf_failures_by_code=dict(
                sorted(self.manifest_wf_failures_by_code.items())
            ),
            last_valid_intermediate=self.last_valid_intermediate,
            canonical_intermediates=intermediates,
        )

    def _write_checkpoint(self) -> Path:
        """Atomically persist restart state outside the epistemic graph."""
        checkpoint = self._checkpoint()
        target = self.checkpoint_path
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        payload = (
            json.dumps(
                checkpoint.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
        ).encode("utf-8")
        with open(temporary, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        return target

    def _success(self, outputs: list[str] | None = None) -> None:
        result = self.machine.success(outputs)
        if outputs:
            self.last_valid_intermediate = outputs[-1]
        self._record(result)

    def _retryable(self, diagnostics: list[dict[str, Any]], **kwargs: Any) -> None:
        for diagnostic in diagnostics:
            path = str(diagnostic.get("path") or "")
            if path:
                self.schema_failures_by_path[path] = self.schema_failures_by_path.get(path, 0) + 1
        self._record(self.machine.retryable_failure(diagnostics, **kwargs))

    def _resume_command(self) -> str:
        from deepreason.run_manifest import MANIFEST_NAME

        root = Path(self.harness.root).resolve()
        parts = ["deepreason", "--root", str(root)]
        parts.extend([
            "make",
            self.description.strip(),
            "--out",
            str(self.out_dir.resolve()),
            "--cycles",
            str(self.cycles + 4),
            "--run-manifest",
            str(root / MANIFEST_NAME),
        ])
        if self.token_budget is None:
            parts.extend(["--token-budget", "0"])
        else:
            parts.extend(["--token-budget", str(self.token_budget)])
        return " ".join(shlex.quote(part) for part in parts)

    def _critic_refutations(self) -> int:
        from deepreason.ontology import Status

        return sum(
            1 for status in self.harness.state.status.values()
            if status == Status.REFUTED
        )

    def _terminal(self, diagnostics: list[dict[str, Any]], message: str) -> list[Path]:
        result = self.machine.terminal_failure(diagnostics)
        self._record(result)
        summary = TerminalSummary(
            failed_stage=result.stage,
            direct_calls=self.direct_calls,
            compact_calls=self.compact_calls,
            schema_failures_by_path=dict(sorted(self.schema_failures_by_path.items())),
            manifest_wf_failures_by_code=dict(sorted(self.manifest_wf_failures_by_code.items())),
            critic_refutations=self._critic_refutations(),
            last_valid_intermediate=self.last_valid_intermediate,
            checkpoint_ref=str(self.checkpoint_path.resolve()),
            manifest_sha256=(
                getattr(self.run_manifest, "sha256", None)
                if self.run_manifest is not None
                else None
            ),
            resume_command=self._resume_command(),
            diagnostics=diagnostics,
        )
        self.harness.record_measure(inputs=[
            "website-terminal",
            summary.model_dump_json(),
        ])
        # Refresh the checkpoint after the terminal-summary event so its
        # sequence fence names the complete durable prefix.
        self._write_checkpoint()
        self.harness.root.mkdir(parents=True, exist_ok=True)
        (self.harness.root / "website-terminal.json").write_text(
            json.dumps(summary.model_dump(mode="json"), sort_keys=True, indent=2) + "\n"
        )
        self.echo(message)
        self.echo("Terminal diagnostics: " + summary.model_dump_json())
        return []

    def _run_stage(self, **kwargs: Any) -> dict[str, Any]:
        from deepreason import easy

        llm_before = sum(1 for event in self.harness.log.read() if event.llm)
        accounting = easy._run_stage(
            self.harness,
            self.cfg,
            token_budget=self.remaining(),
            echo=self.echo,
            run_manifest=self.run_manifest,
            **kwargs,
        )
        llm_after = sum(1 for event in self.harness.log.read() if event.llm)
        calls = llm_after - llm_before
        if self._model_profile() == "compact":
            self.compact_calls += calls
        else:
            self.direct_calls += calls
        self.spend(accounting)
        return accounting

    def _compact_adapter(self):
        """One frozen adapter/meter for all compact design micro-calls."""
        if self._compact_adapter_instance is None:
            from deepreason.llm.adapter import build_adapter
            from deepreason.llm.budget import TokenMeter

            self._compact_meter = TokenMeter(budget=self.remaining())
            self._compact_adapter_instance = build_adapter(
                self.cfg,
                self.harness.blobs,
                meter=self._compact_meter,
                only_roles={"conjecturer", "argumentative_critic"},
                run_manifest=self.run_manifest,
            )
            if not self._compact_adapter_instance.has_role("conjecturer"):
                raise ValueError("compact website design requires the conjecturer role")
        return self._compact_adapter_instance

    @staticmethod
    def _wire_contract(template_role: str, output_model):
        from deepreason.llm.wire import WireContract

        contract_ids = {
            "website_outline": "website_outline.compact.v1",
            "website_component_contract": "component_contract.compact.v1",
            "website_art_direction": "website_art_direction.compact.v1",
        }
        return WireContract(
            contract_ids[template_role],
            output_model,
            output_model,
            variant="compact",
        )

    def _compact_call(self, *, label: str, pack: str, output_model, template_role: str):
        """Run and log one state-local compact value on the frozen route."""
        adapter = self._compact_adapter()
        before = self._compact_meter.total
        self.compact_calls += 1
        wire_contract = self._wire_contract(template_role, output_model)
        try:
            output, llm_call = adapter.call(
                "conjecturer",
                pack,
                output_model,
                template_role=template_role,
                wire_contract=wire_contract,
                model_profile="compact",
            )
        except _COMPACT_CALL_ERRORS as error:
            # Adapter errors carry any already-spent exchange so nothing is
            # lost merely because the bounded repair path exhausted.
            spend = getattr(error, "spend", None)
            if spend is not None:
                self.harness.record_llm_calls(
                    [spend], "website-compact-dropped", label, str(error)[:120]
                )
            self.spent += self._compact_meter.total - before
            raise
        self.spent += self._compact_meter.total - before
        self.harness.record_measure(
            inputs=["website-compact-call", label],
            llm=llm_call,
        )
        return output, llm_call.raw_ref

    def _collect_compact_call(
        self,
        *,
        label: str,
        pack: str,
        output_model,
        template_role: str,
        budget: int | None,
    ) -> _CompactCallResult:
        """Execute transport in a worker without touching harness state/logs."""
        from deepreason.llm.adapter import build_adapter
        from deepreason.llm.budget import TokenMeter

        meter = TokenMeter(budget=budget)
        try:
            adapter = build_adapter(
                self.cfg,
                _LockedBlobStore(self.harness.blobs, self._blob_write_lock),
                meter=meter,
                only_roles={"conjecturer"},
                run_manifest=self.run_manifest,
            )
            if not adapter.has_role("conjecturer"):
                raise ValueError("compact website design requires the conjecturer role")
            output, llm_call = adapter.call(
                "conjecturer",
                pack,
                output_model,
                template_role=template_role,
                wire_contract=self._wire_contract(template_role, output_model),
                model_profile="compact",
            )
            return _CompactCallResult(
                label=label,
                output=output,
                raw_ref=llm_call.raw_ref,
                llm_call=llm_call,
                tokens=meter.total,
            )
        except Exception as error:
            return _CompactCallResult(
                label=label,
                spend_call=getattr(error, "spend", None),
                tokens=meter.total,
                error=error,
            )

    def _commit_compact_results(self, results: list[_CompactCallResult]) -> None:
        """Single-writer append in caller-supplied deterministic order."""
        for result in results:
            self.compact_calls += 1
            self.spent += result.tokens
            if result.error is None:
                self.harness.record_measure(
                    inputs=["website-compact-call", result.label],
                    llm=result.llm_call,
                )
            elif result.spend_call is not None:
                self.harness.record_llm_calls(
                    [result.spend_call],
                    "website-compact-dropped",
                    result.label,
                    str(result.error)[:120],
                )
            else:
                # A pre-transport budget stop or construction failure still
                # belongs in the process log even though it has no LLMCall.
                self.harness.record_measure(inputs=[
                    "website-compact-dropped",
                    result.label,
                    str(result.error)[:120],
                ])

        # The persistent sequential adapter handled the outline/art calls.
        # Parallel meters are accounted above, so shrink its remaining
        # absolute ceiling before it can run the optional design critic.
        if self._compact_meter is not None and self.token_budget is not None:
            self._compact_meter.budget = self._compact_meter.total + self.remaining()

    @staticmethod
    def _component_order(component) -> tuple[int, str]:
        alias = str(component.alias)
        try:
            return int(alias[1:]), alias
        except (TypeError, ValueError):
            return 1 << 30, alias

    @staticmethod
    def _partition_budget(total: int | None, count: int) -> list[int | None]:
        if total is None:
            return [None] * count
        quotient, remainder = divmod(max(0, total), count)
        return [quotient + (index < remainder) for index in range(count)]

    def _compact_outline_call(self, plan_text: str, diagnostic: dict | None = None):
        from deepreason.workflows.manifest_compiler import CompactDesignOutline

        repair = ""
        if diagnostic:
            repair = "\nLOCAL DIAGNOSTIC:\n" + json.dumps(diagnostic, sort_keys=True)
        pack = (
            "WEBSITE DESIGN OUTLINE\n"
            f"Task: {self.description.strip()}\n"
            "Return 2 to 8 components in page order. Use aliases C1, C2, ... "
            "without gaps. Give only each component's purpose.\n"
            f"ADJUDICATED PLAN:\n{plan_text}{repair}"
        )
        return self._compact_call(
            label="design-outline",
            pack=pack,
            output_model=CompactDesignOutline,
            template_role="website_outline",
        )

    def _compact_art_call(self, plan_text: str, diagnostic: dict | None = None):
        from deepreason.workflows.manifest_compiler import CompactArtDirection

        repair = ""
        if diagnostic:
            repair = "\nLOCAL DIAGNOSTIC:\n" + json.dumps(diagnostic, sort_keys=True)
        pack = (
            "WEBSITE ART DIRECTION\n"
            f"Task: {self.description.strip()}\n"
            "Specify one coherent visual and motion system, including palette, "
            "typography, spacing, responsive behavior, and interaction/state. "
            "Reduced-motion and static fallback fields must describe complete "
            "usable alternatives.\n"
            f"ADJUDICATED PLAN:\n{plan_text}{repair}"
        )
        return self._compact_call(
            label="art-direction",
            pack=pack,
            output_model=CompactArtDirection,
            template_role="website_art_direction",
        )

    def _compact_contract_batch(
        self,
        components,
        outline,
        art_direction,
        *,
        diagnostics: dict[str, dict] | None = None,
        previous: dict[str, Any] | None = None,
    ) -> list[tuple[Any, str]]:
        """Call independent contracts concurrently, then register serially.

        Worker completion order is deliberately discarded.  Every response
        (including bounded failures) is collected before the first Measure
        event is appended, and results are committed in canonical ``C<n>``
        component-id order by the calling thread.
        """
        from deepreason.workflows.manifest_compiler import CompactComponentContract

        ordered = sorted(list(components), key=self._component_order)
        diagnostics = diagnostics or {}
        previous = previous or {}
        jobs: list[dict[str, Any]] = []
        neighbours = [
            {"alias": item.alias, "purpose": item.purpose}
            for item in outline.components
        ]
        for component in ordered:
            repair = ""
            diagnostic = diagnostics.get(component.alias)
            if diagnostic:
                repair = (
                    "\nREPAIR ONLY THIS CONTRACT. LOCAL DIAGNOSTIC:\n"
                    + json.dumps(diagnostic, sort_keys=True)
                )
                prior = previous.get(component.alias)
                if prior is not None:
                    repair += "\nPREVIOUS CONTRACT:\n" + prior.model_dump_json()
            pack = (
                "WEBSITE COMPONENT CONTRACT\n"
                f"Task: {self.description.strip()}\n"
                f"Target: {component.alias} — {component.purpose}\n"
                "All components (dependencies may use only these aliases):\n"
                + json.dumps(neighbours, sort_keys=True)
                + "\nUse slots=[\"root\"]. owned_dom_ids must start with one unique "
                  "root id. exports are local callable names. motion_requirement "
                  "is full, limited, or static. Return only this target contract.\n"
                + "GLOBAL ART DIRECTION:\n"
                + art_direction.model_dump_json()
                + repair
            )
            jobs.append({
                "label": f"component-contract:{component.alias}",
                "pack": pack,
                "output_model": CompactComponentContract,
                "template_role": "website_component_contract",
            })

        worker_count = self._component_concurrency(len(jobs))
        if worker_count == 1:
            # Preserve compact/standard's established one-adapter, one-meter
            # behavior when their compiled concurrency remains at the
            # default of one.
            return [self._compact_call(**job) for job in jobs]

        budgets = self._partition_budget(self.remaining(), len(jobs))
        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="deepreason-component-contract",
        ) as executor:
            futures = [
                executor.submit(
                    self._collect_compact_call, **job, budget=budget
                )
                for job, budget in zip(jobs, budgets, strict=True)
            ]
            # Consume every Future before touching the append-only log.
            results = [future.result() for future in futures]

        self._commit_compact_results(results)
        failures = [result.error for result in results if result.error is not None]
        if failures:
            raise failures[0]
        return [(result.output, result.raw_ref) for result in results]

    @staticmethod
    def _compiled_design_document(outline, contracts, art_direction, manifest) -> str:
        """Deterministic ordinary design artifact for the canonical graph."""
        art = art_direction.model_dump()

        def short(name: str, limit: int = 160) -> str:
            return str(art.get(name) or "")[:limit]

        component_synopsis = "; ".join(
            f"{component.alias} {component.purpose[:80]}"
            for component in outline.components
        )
        lines = [
            "# Design specification",
            "",
            "This single-document website follows the adjudicated product plan. "
            "The harness assigned component identifiers and integration order; "
            "the following model-authored local values remain criticizable.",
            "",
            "## Required-design synopsis",
            "- Layout: one responsive scrolling page in order "
            + " → ".join(component.alias for component in outline.components)
            + ".",
            f"- Visual system: palette {short('palette', 120)}; typography "
            f"{short('typography', 120)}; spacing {short('spacing_strategy', 120)}.",
            f"- Components: {component_synopsis[:520]}.",
            f"- Interaction and state: {short('interaction_state_model', 220)}.",
            f"- Responsive behavior: {short('responsive_strategy', 220)}.",
            f"- Motion behavior: {short('motion_language', 180)}.",
            f"- Reduced-motion behavior: {short('reduced_motion_version', 240)}.",
            f"- Static alternative: {short('static_fallback', 200)}.",
            "",
            "## Page layout",
            "One responsive scrolling page in this order: "
            + " → ".join(component.alias for component in outline.components)
            + ".",
            "",
            "## Component inventory",
        ]
        by_alias = {contract.alias: contract for contract in contracts}
        for component in outline.components:
            contract = by_alias[component.alias]
            requirements = "; ".join(contract.content_requirements) or "none beyond purpose"
            dependencies = ", ".join(contract.depends_on) or "none"
            lines.append(
                f"- {component.alias}: {component.purpose}. Requirements: "
                f"{requirements}. Dependencies: {dependencies}. Motion: "
                f"{contract.motion_requirement}."
            )
        lines.extend(["", "## Visual direction"])
        for name, value in art_direction.model_dump().items():
            lines.append(f"- {name.replace('_', ' ')}: {value}")
        lines.extend([
            "",
            "## Interaction, state, and responsive strategy",
            "Each component owns its declared DOM root and lifecycle exports. "
            "The page is assembled in manifest order as one responsive local "
            "document. Motion follows the shared art direction; reduced-motion "
            "and static modes preserve the complete narrative without requiring "
            "animation or JavaScript-only content.",
            "",
            "```manifest",
            json.dumps(manifest.model_dump(), sort_keys=True, indent=2),
            "```",
            "",
        ])
        return "\n".join(lines)

    def _register_compact_design(self, outline, contracts, art_direction, manifest):
        """Register generator output through ordinary Conj gates and critics."""
        from deepreason.ontology import Artifact, Interface, Provenance, Ref, Rule, Status
        from deepreason.rules.crit import crit_argumentative, crit_program
        from deepreason.rules.guards import anti_relapse

        problem = self.harness.state.problems["pi-design"]
        content = self._compiled_design_document(
            outline, contracts, art_direction, manifest
        )
        interface = Interface(
            commitments=[
                commitment for commitment in problem.criteria
                if commitment in self.harness.commitments
            ],
            refs=[Ref(target=self.plan_id, role="dependence")],
        )
        content_ref = f"inline:{content}"
        artifact = Artifact(
            id=Artifact.compute_id(content_ref, "utf8", interface),
            content_ref=content_ref,
            codec="utf8",
            interface=interface,
            provenance=Provenance(
                role="conjecturer",
                event_seq=self.harness._next_seq,
            ),
        )
        admitted, reason = anti_relapse.check(
            artifact,
            [],
            self.harness,
            near_dup_eps=self.cfg.NEAR_DUP_EPS,
        )
        if not admitted:
            self.harness.record_measure(
                inputs=[f"gate:{reason}", artifact.id, "pi-design"]
            )
            return None
        self.harness.register_batch(
            [(artifact, [])],
            problem_id="pi-design",
            rule=Rule.CONJ,
        )
        crit_program(self.harness, artifact.id)
        adapter = self._compact_adapter()
        if (
            self.harness.state.status.get(artifact.id) == Status.ACCEPTED
            and adapter.has_role("argumentative_critic")
        ):
            before = self._compact_meter.total
            llm_before = sum(1 for event in self.harness.log.read() if event.llm)
            try:
                crit_argumentative(self.harness, artifact.id, adapter, self.cfg)
            except _COMPACT_CALL_ERRORS as error:
                spend = getattr(error, "spend", None)
                if spend is not None:
                    self.harness.record_llm_calls(
                        [spend], "website-compact-critic-dropped", str(error)[:120]
                    )
            finally:
                self.spent += self._compact_meter.total - before
                llm_after = sum(1 for event in self.harness.log.read() if event.llm)
                self.compact_calls += llm_after - llm_before
        return (
            artifact
            if self.harness.state.status.get(artifact.id) == Status.ACCEPTED
            else None
        )

    def _component_problem_for_attempt(self, spec) -> tuple[str, str, str | None]:
        base = f"pi-comp-{spec.name}"
        if self.machine.attempt <= 1 or base not in self.harness.state.problems:
            return base, "", None
        suffix = f"-resume-{self.machine.attempt}"
        problem_id = base + suffix
        existing = self.harness.state.problems.get(problem_id)
        if existing is not None:
            source = existing.provenance.from_[0] if existing.provenance.from_ else None
            return problem_id, suffix, source
        candidates = [
            aid for aid, pid in self.harness.state.addr
            if pid == base or pid.startswith(base + "-resume-")
        ]
        repair_of = max(candidates, key=lambda aid: (
            self.harness.state.artifacts[aid].provenance.event_seq, aid
        )) if candidates else None
        return problem_id, suffix, repair_of

    def run(self) -> list[Path]:
        from deepreason import assets, easy
        from deepreason.manifest import manifest_wf, parse_manifest
        from deepreason.ontology import Status
        from deepreason.ontology.commitment import Budget
        from deepreason.programs import content_text
        from deepreason.views.export import export_run

        if self.machine.complete:
            if self.machine.history[-1].outcome == StageOutcome.SUCCESS:
                return [Path(item) for item in self.machine.history[-1].canonical_outputs]
            return []

        plan_cycles = max(2, self.cycles // 5)
        design_cycles = max(2, self.cycles // 5)
        self.echo(
            f"Stages: planning (up to {plan_cycles} rounds) -> designing a "
            f"component manifest (up to {design_cycles}) -> building each "
            "component -> assembling deterministically -> integration checks\n"
        )

        # PLAN
        if self.machine.stage == WebsiteStage.PLAN:
            easy.seed_plan(self.harness, self.description)
            self._run_stage(
                label="planning", root_pid="pi-plan", cycles=plan_cycles,
                stop_on_survivor=True,
            )
            self.plan_id = easy.pick_survivor(self.harness, "pi-plan")
            if self.plan_id is None:
                return self._terminal(
                    [{"code": "NO_PLAN_SURVIVOR", "path": "/plan"}],
                    "\nNo plan survived criticism.",
                )
            self.harness.record_measure(inputs=["stage-pick", "plan", self.plan_id])
            self._success([self.plan_id])

        # DESIGN_OUTLINE. Compact profiles never ask for a nested canonical
        # manifest. Standard tries exactly one direct cycle. Standard and
        # frontier can enter compact recovery only after a measured schema or
        # manifest-conformance failure; a normal critic refutation alone does
        # not select a different generation strategy. Frontier therefore pays
        # no compact micro-call overhead on its successful fast path.
        profile = self._model_profile()
        use_compact = profile == "compact" or self.compact_outline is not None
        plan_text = None
        if self.machine.stage == WebsiteStage.DESIGN_OUTLINE:
            easy.seed_design_chunked(self.harness, self.description, self.plan_id)
            if not use_compact:
                direct_start_seq = self.harness._next_seq
                self._run_stage(
                    label="designing", root_pid="pi-design",
                    cycles=1 if profile == "standard" else design_cycles,
                    stop_on_survivor=True,
                )
                self.design_id = easy.pick_survivor(self.harness, "pi-design")
                if self.design_id is None:
                    recovery_reason = self._direct_recovery_reason(direct_start_seq)
                    if recovery_reason is not None:
                        use_compact = True
                        self.harness.record_measure(inputs=[
                            "website-design-mode", profile, "compact-recovery",
                            recovery_reason,
                        ])
            if not use_compact:
                if self.design_id is None:
                    return self._terminal(
                        [{"code": "NO_DESIGN_SURVIVOR", "path": "/design_outline"}],
                        "\nA plan survived but no design with a valid component manifest did.",
                    )
                self.harness.record_measure(inputs=["stage-pick", "design", self.design_id])
                self._success([self.design_id])
        if self.machine.stage == WebsiteStage.DESIGN_OUTLINE and use_compact:
            plan_text = content_text(
                self.harness.state.artifacts[self.plan_id], self.harness.blobs
            )
            try:
                self.compact_outline, outline_ref = self._compact_outline_call(plan_text)
            except _COMPACT_CALL_ERRORS as error:
                return self._terminal(
                    [{
                        "code": "DESIGN_OUTLINE_CALL_FAILED",
                        "path": "/design_outline",
                        "message": str(error)[:500],
                    }],
                    "\nCompact design-outline generation exhausted bounded repair.",
                )
            self._success([outline_ref])
        use_compact = self.compact_outline is not None
        if use_compact and plan_text is None:
            plan_text = content_text(
                self.harness.state.artifacts[self.plan_id], self.harness.blobs
            )
        if self.machine.stage == WebsiteStage.COMPONENT_CONTRACTS and use_compact:
            # COMPONENT_CONTRACTS contains one independent art-direction call
            # and exactly one initial call per outlined component.
            contract_refs: list[str] = []
            try:
                self.compact_art_direction, art_ref = self._compact_art_call(plan_text)
                contract_refs.append(art_ref)
                contract_results = self._compact_contract_batch(
                    self.compact_outline.components,
                    self.compact_outline,
                    self.compact_art_direction,
                )
                self.compact_contracts = [item[0] for item in contract_results]
                contract_refs.extend(item[1] for item in contract_results)
            except _COMPACT_CALL_ERRORS as error:
                return self._terminal(
                    [{
                        "code": "COMPONENT_CONTRACT_CALL_FAILED",
                        "path": "/component_contracts",
                        "message": str(error)[:500],
                    }],
                    "\nA compact component-contract call exhausted bounded repair.",
                )
            self._success(contract_refs)
        if self.machine.stage == WebsiteStage.MANIFEST_COMPILE and use_compact:
            # MANIFEST_COMPILE is deterministic. Compiler diagnostics can
            # trigger only affected component/art-direction calls; all
            # untouched values survive byte-for-byte and the complete
            # manifest is recompiled and revalidated after every repair.
            from deepreason.workflows.manifest_compiler import ManifestCompiler

            compiler = ManifestCompiler(
                known_libs=assets.catalog_names(),
                import_policy=self.cfg.IMPORT_POLICY,
            )
            compiled = compiler.compile(
                self.compact_outline,
                self.compact_contracts,
                art_direction=self.compact_art_direction,
                title=self.description.strip()[:160],
            )
            local_round = 0
            while not compiled.ok and local_round < min(2, max(0, self.cfg.RETRY_MAX)):
                diagnostics = [
                    diagnostic.model_dump(mode="json")
                    for diagnostic in compiled.diagnostics
                ]
                self._retryable(diagnostics, component_contract=True)
                by_alias = {
                    component.alias: component
                    for component in self.compact_outline.components
                }
                contracts = {
                    contract.alias: contract
                    for contract in self.compact_contracts
                }
                repair_targets = sorted({
                    diagnostic.component_alias
                    for diagnostic in compiled.diagnostics
                    if diagnostic.component_alias in by_alias
                })
                repair_art = any(
                    diagnostic.repair_scope == "/art_direction"
                    for diagnostic in compiled.diagnostics
                )
                if not repair_targets and not repair_art:
                    break
                try:
                    if repair_art:
                        diagnostic = next(
                            item.model_dump(mode="json")
                            for item in compiled.diagnostics
                            if item.repair_scope == "/art_direction"
                        )
                        self.compact_art_direction, _ = self._compact_art_call(
                            plan_text, diagnostic
                        )
                    if repair_targets:
                        diagnostic_by_alias = {
                            alias: next(
                                item.model_dump(mode="json")
                                for item in compiled.diagnostics
                                if item.component_alias == alias
                            )
                            for alias in repair_targets
                        }
                        replacements = self._compact_contract_batch(
                            [by_alias[alias] for alias in repair_targets],
                            self.compact_outline,
                            self.compact_art_direction,
                            diagnostics=diagnostic_by_alias,
                            previous=contracts,
                        )
                        for replacement, _ in replacements:
                            contracts[replacement.alias] = replacement
                except _COMPACT_CALL_ERRORS as error:
                    return self._terminal(
                        [{
                            "code": "LOCAL_MANIFEST_REPAIR_CALL_FAILED",
                            "path": "/component_contracts",
                            "message": str(error)[:500],
                        }],
                        "\nLocalized manifest repair exhausted.",
                    )
                self.compact_contracts = [
                    contracts[component.alias]
                    for component in self.compact_outline.components
                ]
                compiled = compiler.compile(
                    self.compact_outline,
                    self.compact_contracts,
                    art_direction=self.compact_art_direction,
                    title=self.description.strip()[:160],
                )
                local_round += 1

            if not compiled.ok:
                diagnostics = [
                    diagnostic.model_dump(mode="json")
                    for diagnostic in compiled.diagnostics
                ]
                for diagnostic in diagnostics:
                    code = str(diagnostic["code"])
                    self.manifest_wf_failures_by_code[code] = (
                        self.manifest_wf_failures_by_code.get(code, 0) + 1
                    )
                return self._terminal(
                    diagnostics,
                    "\nCompact manifest compilation exhausted localized repair.",
                )
            self.manifest = compiled.manifest
            design = self._register_compact_design(
                self.compact_outline,
                self.compact_contracts,
                self.compact_art_direction,
                self.manifest,
            )
            if design is None:
                return self._terminal(
                    [{
                        "code": "COMPILED_DESIGN_DID_NOT_SURVIVE",
                        "path": "/manifest",
                    }],
                    "\nThe compiled design did not survive ordinary gates and criticism.",
                )
            self.design_id = design.id
            self.harness.record_measure(inputs=["stage-pick", "design", self.design_id])
            self.echo(f"  compact design registered: {self.design_id[:12]}")
            names = [component.name for component in self.manifest.ordered()]
            self.echo(f"  components: {', '.join(names)}\n")
            self._success([self.design_id])
        if self.machine.stage == WebsiteStage.COMPONENT_CONTRACTS and not use_compact:
            # COMPONENT_CONTRACTS: direct mode extracts the nested contracts
            # from the already criticized canonical design artifact.
            self.manifest, error = parse_manifest(
                content_text(
                    self.harness.state.artifacts[self.design_id], self.harness.blobs
                ),
                known_libs=assets.catalog_names(),
            )
            if self.manifest is None:
                diagnostic = {
                    "code": "MANIFEST_SCHEMA_INVALID",
                    "path": "/manifest",
                    "message": error,
                }
                self._retryable([diagnostic], component_contract=True)
                self.manifest_wf_failures_by_code[diagnostic["code"]] = 1
                return self._terminal(
                    [diagnostic], "\nThe chosen design's manifest failed to parse."
                )
            names = [component.name for component in self.manifest.ordered()]
            self.echo(f"  components: {', '.join(names)}\n")
            self._success(names)
        if self.machine.stage == WebsiteStage.MANIFEST_COMPILE and not use_compact:
            # Direct/frontier input converges on the same deterministic
            # compiler/validator used by compact input.
            from deepreason.workflows.manifest_compiler import ManifestCompiler

            names = [component.name for component in self.manifest.ordered()]
            compiled = ManifestCompiler(
                known_libs=assets.catalog_names(),
                import_policy=self.cfg.IMPORT_POLICY,
            ).validate_manifest(self.manifest, aliases=names)
            if not compiled.ok:
                diagnostics = [
                    diagnostic.model_dump(mode="json")
                    for diagnostic in compiled.diagnostics
                ]
                self._retryable(diagnostics, component_contract=True)
                for diagnostic in diagnostics:
                    code = str(diagnostic["code"])
                    self.manifest_wf_failures_by_code[code] = (
                        self.manifest_wf_failures_by_code.get(code, 0) + 1
                    )
                return self._terminal(diagnostics, "\nManifest compilation failed.")
            self.manifest = compiled.manifest
            self._success(names)

        # MANIFEST_VALIDATE: invoke the existing replay-stable program again,
        # independently of admission, before any component build can begin.
        names = [component.name for component in self.manifest.ordered()]
        if self.machine.stage == WebsiteStage.MANIFEST_VALIDATE:
            text = (
                "```manifest\n"
                + json.dumps(self.manifest.model_dump(), sort_keys=True)
                + "\n```"
            )
            verdict, trace = manifest_wf(
                text,
                Budget(extra={"libs": ",".join(sorted(assets.catalog_names()))}),
            )
            if verdict != "pass":
                diagnostic = {
                    "code": "MANIFEST_WF_FAILED", "path": "/manifest",
                    "message": str(trace.get("reason") or "manifest_wf failed"),
                }
                self.manifest_wf_failures_by_code[diagnostic["code"]] = 1
                self._retryable([diagnostic], component_contract=True)
                return self._terminal([diagnostic], "\nManifest validation failed.")
            self._success(names)

        # COMPONENT_BUILD: resolve the accepted import plan before component
        # problems are seeded, then work components in canonical order.
        component_cycles = max(
            1,
            (self.cycles - plan_cycles - design_cycles) // max(1, len(names)),
        )
        if self.machine.stage == WebsiteStage.COMPONENT_BUILD:
            from deepreason.imports import resolve_for_design

            has_runtime = any(
                item.preferred_provider != "native" for item in self.manifest.dependencies
            )
            if not self.imports_resolved:
                self.resolved_imports = resolve_for_design(
                    self.harness, self.design_id, self.manifest, self.cfg
                )
                if has_runtime and self.resolved_imports is None:
                    code = (
                        "IMPORT_PLAN_REFUTED"
                        if self.harness.state.status.get(self.design_id) == Status.REFUTED
                        else "IMPORT_RESOLUTION_DEFERRED"
                    )
                    return self._terminal(
                        [{"code": code, "path": "/manifest/dependencies"}],
                        "  The accepted dependency plan could not be resolved.",
                    )
                self.imports_resolved = True
                self._write_checkpoint()
            for spec in self.manifest.ordered():
                if spec.name in self.chosen:
                    continue
                problem_id, suffix, repair_of = self._component_problem_for_attempt(spec)
                easy.seed_component(
                    self.harness, self.description, self.design_id, self.manifest,
                    spec, self.cfg.CHUNK_MAX_CHARS, suffix=suffix,
                    repair_of=repair_of, resolved_imports=self.resolved_imports,
                )
                self._run_stage(
                    label=f"component {spec.name}", root_pid=problem_id,
                    cycles=component_cycles, stop_on_survivor=True,
                )
                survivor = easy.pick_survivor(self.harness, problem_id)
                if survivor is None:
                    return self._terminal([{
                        "code": "NO_COMPONENT_SURVIVOR",
                        "path": f"/components/{spec.name}", "component": spec.name,
                    }], f"\nComponent {spec.name!r} produced no surviving fragment.")
                self.chosen[spec.name] = survivor
                self.harness.record_measure(
                    inputs=["stage-pick", f"component:{spec.name}", survivor]
                )
                self._write_checkpoint()
            self._success([self.chosen[name] for name in sorted(self.chosen)])

        # ASSEMBLE: repository composition only, with all dependence refs and
        # existing browser/integration commitments.
        from deepreason.imports import (
            ImportPlanError,
            OperationalImportError,
            register_epistemic_import_failure,
        )

        if self.machine.stage == WebsiteStage.ASSEMBLE:
            try:
                self.assembled = easy.register_assembly(
                    self.harness, self.design_id, self.manifest, self.chosen,
                    self.resolved_imports, self.cfg.IMPORT_POLICY,
                )
            except OperationalImportError as error:
                self.harness.record_measure(
                    inputs=["import-deferred", self.design_id, error.code]
                )
                return self._terminal(
                    [{"code": error.code, "path": "/assembly/imports"}],
                    "  Bundling was deferred after an operational toolchain failure.",
                )
            except ImportPlanError as error:
                register_epistemic_import_failure(self.harness, self.design_id, error)
                return self._terminal(
                    [{"code": error.code, "path": "/assembly/imports"}],
                    "  Bundled imports failed an accepted size or export commitment.",
                )
            self.echo("  assembled deterministically from the accepted fragments")
            self._success([self.assembled.id])

        # INTEGRATION_VALIDATE: normal program/browser criticism followed by
        # one bounded, implicated-component successor round.
        if self.machine.stage == WebsiteStage.INTEGRATION_VALIDATE:
            browser_backend = None
            if importlib.util.find_spec("playwright") is not None:
                from deepreason.browser import PlaywrightBrowser

                browser_backend = PlaywrightBrowser()
            implicated = easy.integration_criticism(
                self.harness, self.assembled.id, self.manifest, self.cfg,
                browser_backend,
            )
            if implicated:
                diagnostics = [{
                    "code": "INTEGRATION_COMPONENT_FAILURE",
                    "path": f"/components/{name}", "component": name,
                } for name in sorted(implicated)]
                self._retryable(diagnostics, component=True)
                for spec in self.manifest.ordered():
                    if spec.name not in implicated:
                        continue
                    easy.seed_component(
                        self.harness, self.description, self.design_id, self.manifest,
                        spec, self.cfg.CHUNK_MAX_CHARS, suffix="-r2",
                        repair_of=self.chosen[spec.name],
                        resolved_imports=self.resolved_imports,
                    )
                    self._run_stage(
                        label=f"repairing {spec.name}",
                        root_pid=f"pi-comp-{spec.name}-r2",
                        cycles=component_cycles, stop_on_survivor=True,
                    )
                    fixed = easy.pick_survivor(
                        self.harness, f"pi-comp-{spec.name}-r2"
                    )
                    if fixed is not None:
                        self.chosen[spec.name] = fixed
                try:
                    self.assembled = easy.register_assembly(
                        self.harness, self.design_id, self.manifest, self.chosen,
                        self.resolved_imports, self.cfg.IMPORT_POLICY,
                    )
                except OperationalImportError as error:
                    self.harness.record_measure(
                        inputs=["import-deferred", self.design_id, error.code]
                    )
                    return self._terminal(
                        [{"code": error.code, "path": "/integration/imports"}],
                        "  Repair assembly was deferred after an operational failure.",
                    )
                except ImportPlanError as error:
                    register_epistemic_import_failure(
                        self.harness, self.design_id, error
                    )
                    return self._terminal(
                        [{"code": error.code, "path": "/integration/imports"}],
                        "  Repair assembly failed an import commitment.",
                    )
                implicated = easy.integration_criticism(
                    self.harness, self.assembled.id, self.manifest, self.cfg,
                    browser_backend,
                )
                if implicated:
                    return self._terminal([{
                        "code": "INTEGRATION_REPAIR_EXHAUSTED",
                        "path": f"/components/{name}", "component": name,
                    } for name in sorted(implicated)],
                    "\nTargeted integration repair was exhausted; no invalid page was exported.")
            self._success([self.assembled.id])

        # EXPORT only sees artifacts that survived the canonical status path.
        if self.machine.stage == WebsiteStage.EXPORT:
            self.echo(f"\nDone thinking ({self.spent:,} tokens).")
            paths = export_run(self.harness, self.out_dir)
            for stage, artifact_id in (("plan", self.plan_id), ("design", self.design_id)):
                document = self.out_dir / f"{stage}-{artifact_id[:12]}.md"
                document.write_text(content_text(
                    self.harness.state.artifacts[artifact_id], self.harness.blobs
                ))
                paths.append(document)
            pages = [path for path in paths if path.suffix == ".html"]
            if not pages:
                return self._terminal(
                    [{"code": "NO_EXPORT_SURVIVOR", "path": "/export"}],
                    "\nComponents survived but the assembled page did not pass "
                    "integration criticism.",
                )
            self._success([str(path) for path in paths])
            self.echo(
                f"\nYour website is ready — assembled from {len(names)} component(s) "
                "that each survived criticism:"
            )
            for path in pages:
                self.echo(f"  {path.resolve()}")
            return paths
        raise RuntimeError(f"unhandled website stage: {self.machine.stage.value}")


def run_website_workflow(
    harness,
    cfg,
    description: str,
    out_dir: Path,
    cycles: int,
    token_budget: int | None,
    echo,
    *,
    config_path: Path | None = None,
    run_manifest=None,
) -> list[Path]:
    """Compatibility entry point used by :func:`deepreason.easy.make`."""
    return WebsiteWorkflow(
        harness,
        cfg,
        description,
        out_dir,
        cycles,
        token_budget,
        echo,
        config_path=config_path,
        run_manifest=run_manifest,
    ).run()
