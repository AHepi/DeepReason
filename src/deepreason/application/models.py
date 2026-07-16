"""Strict, transport-neutral intents and results for text-run operations.

The intent vocabulary contains no provider route, graph status, event payload,
guard override, or raw controller field.  CLI and MCP may select an immutable
manifest document, budgets, and user workload content; the application service
owns every lifecycle and scheduler decision after that boundary.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)

from deepreason.canonical import canonical_json, sha256_hex

from deepreason.workloads.text import ReasoningWorkloadSpec


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RunBudgetIntentV1(_StrictModel):
    cycles: StrictInt | Literal["unlimited"]
    token_budget: StrictInt | Literal["unlimited"]

    @field_validator("cycles")
    @classmethod
    def _positive_cycles(cls, value):
        if isinstance(value, int) and value < 1:
            raise ValueError("cycles must be positive or unlimited")
        return value

    @field_validator("token_budget")
    @classmethod
    def _nonnegative_tokens(cls, value):
        if isinstance(value, int) and value < 0:
            raise ValueError("token_budget cannot be negative")
        return value


class StartTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.start.v1"] = Field(
        "application.text-run.start.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)
    workload: ReasoningWorkloadSpec
    run_manifest_ref: str = Field(min_length=1, max_length=4_096)
    budget: RunBudgetIntentV1

    @field_validator("root", "run_manifest_ref")
    @classmethod
    def _safe_path_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("path text cannot contain NUL")
        return value


class ContinueTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.continue.v1"] = Field(
        "application.text-run.continue.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)
    budget: RunBudgetIntentV1
    expected_manifest_digest: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )


class InspectTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.inspect.v1"] = Field(
        "application.text-run.inspect.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)
    since_seq: StrictInt = Field(default=-1, ge=-1)


class WatchTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.watch.v1"] = Field(
        "application.text-run.watch.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)
    interval: float = Field(default=0.25, gt=0)
    once: bool = False


class CancelTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.cancel.v1"] = Field(
        "application.text-run.cancel.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)


class RunStartedV1(_StrictModel):
    schema_: Literal["application.text-run.started.v1"] = Field(
        "application.text-run.started.v1", alias="schema"
    )
    lifecycle: Literal["running"] = "running"
    root: str
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    workload: Literal["text"] = "text"

    def presentation_payload(self) -> dict[str, Any]:
        return {
            "state": self.lifecycle,
            "root": self.root,
            "manifest_sha256": self.manifest_digest,
            "workload": self.workload,
            "status_operation": "run_status",
            "result_operation": "run_result",
        }


class RunProgressResultV1(_StrictModel):
    schema_: Literal["application.text-run.progress.v1"] = Field(
        "application.text-run.progress.v1", alias="schema"
    )
    lifecycle: str
    payload: dict[str, Any]

    def presentation_payload(self) -> dict[str, Any]:
        return dict(self.payload)


class OutstandingWorkItemProjectionV1(_StrictModel):
    work_order_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    recovery: str
    role: str
    seat: StrictInt = Field(ge=0)
    endpoint_id: str
    route_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    contract_id: str
    reserved_tokens: StrictInt = Field(ge=0)
    provider_calls_used: StrictInt = Field(ge=0)
    provider_calls_limit: StrictInt = Field(ge=1)
    local_repairs_used: StrictInt = Field(ge=0)
    local_repairs_limit: StrictInt = Field(ge=0)
    context_expansions_used: StrictInt = Field(ge=0)
    context_expansions_limit: StrictInt = Field(ge=0)


class OutstandingWorkResultV1(_StrictModel):
    schema_: Literal["application.text-run.outstanding-work.v1"] = Field(
        "application.text-run.outstanding-work.v1", alias="schema"
    )
    process_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    last_control_seq: StrictInt = Field(ge=-1)
    work: tuple[OutstandingWorkItemProjectionV1, ...] = ()

    def presentation_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True)


class TextRunTerminalResultV1(_StrictModel):
    schema_: Literal["application.text-run.terminal.v1"] = Field(
        "application.text-run.terminal.v1", alias="schema"
    )
    lifecycle: Literal["completed", "cancelled", "failed"]
    payload: dict[str, Any]

    def presentation_payload(self) -> dict[str, Any]:
        return dict(self.payload)


class RunCancellationAcceptedV1(_StrictModel):
    schema_: Literal["application.text-run.cancellation-accepted.v1"] = Field(
        "application.text-run.cancellation-accepted.v1", alias="schema"
    )
    lifecycle: Literal["cancellation-requested"] = "cancellation-requested"
    root: str
    safe_boundary: Literal["completed-cycle"] = "completed-cycle"

    def presentation_payload(self) -> dict[str, Any]:
        return {
            "state": self.lifecycle,
            "root": self.root,
            "safe_boundary": self.safe_boundary,
        }


class OperatorCancellationIntentV1(_StrictModel):
    """Durable operator request; the controller still owns terminalization."""

    schema_: Literal["application.operator-cancellation-intent.v1"] = Field(
        "application.operator-cancellation-intent.v1", alias="schema"
    )
    id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    sequence: StrictInt = Field(ge=0)
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    process_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    last_control_seq: StrictInt = Field(ge=-1)
    safe_boundary: Literal["completed-cycle"] = "completed-cycle"

    @classmethod
    def create(cls, **values):
        payload = {
            "schema": "application.operator-cancellation-intent.v1",
            "safe_boundary": "completed-cycle",
            **values,
        }
        record_id = "sha256:" + sha256_hex(
            b"application.operator-cancellation-intent.v1\x00"
            + canonical_json(payload)
        )
        return cls(id=record_id, **values)

    @model_validator(mode="after")
    def _canonical_id(self):
        payload = self.model_dump(
            mode="json", by_alias=True, exclude={"id"}
        )
        expected = "sha256:" + sha256_hex(
            b"application.operator-cancellation-intent.v1\x00"
            + canonical_json(payload)
        )
        if self.id != expected:
            raise ValueError("operator cancellation intent ID is not canonical")
        return self


__all__ = [
    "CancelTextRunIntentV1",
    "ContinueTextRunIntentV1",
    "InspectTextRunIntentV1",
    "OutstandingWorkItemProjectionV1",
    "OutstandingWorkResultV1",
    "OperatorCancellationIntentV1",
    "RunBudgetIntentV1",
    "RunCancellationAcceptedV1",
    "RunProgressResultV1",
    "RunStartedV1",
    "StartTextRunIntentV1",
    "TextRunTerminalResultV1",
    "WatchTextRunIntentV1",
]
