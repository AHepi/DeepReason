"""Full-harness integration for fixed-fence grounded final views."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from deepreason.bridge.compose import CompositionRequestV1
from deepreason.bridge.evidence_pack import (
    EvidencePackV1,
    assemble_evidence_pack,
    build_claim_ledger_catalog,
)
from deepreason.bridge.events import BridgeAction
from deepreason.bridge.models import BridgeResolution
from deepreason.bridge.workflow import (
    BridgePersistenceBatch,
    BridgeWorkflow,
    BridgeWorkflowPolicy,
    BridgeWorkflowResultV1,
)
from deepreason.ontology.frozen import FrozenList, FrozenRecord
from deepreason.runtime.progress import _atomic_json
from deepreason.scratch.service import ScratchService


BRIDGE_RESULT_NAME = "bridge-result.json"
BRIDGE_STATUS_NAME = "bridge-status.json"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class BridgeTerminalResultV1(FrozenRecord):
    """Fixed, machine-readable pointer record for one terminal bridge run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_: Literal["deepreason-bridge-result-v1"] = Field(
        "deepreason-bridge-result-v1", alias="schema"
    )
    run_manifest_digest: str
    formal_seq: int = Field(ge=0)
    terminal_event_seq: int = Field(ge=0)
    problem_id: str = Field(min_length=1, max_length=512)
    target: Literal["thesis", "summary", "answer"]
    evidence_pack_id: str
    claim_ledger_id: str | None = None
    bridge_output_id: str | None = None
    validation_report_id: str | None = None
    review_id: str | None = None
    resolution: BridgeResolution | None = None
    output_paths: list[str] = Field(default_factory=FrozenList, max_length=32)
    process_status: Literal["success", "failure"]
    error_code: str | None = None
    error_message: str | None = Field(default=None, max_length=16_384)

    @field_validator("run_manifest_digest")
    @classmethod
    def _manifest_digest(cls, value):
        if _SHA256.fullmatch(value) is None:
            raise ValueError("run_manifest_digest must be 64 lowercase hex characters")
        return value

    @field_validator("output_paths", mode="after")
    @classmethod
    def _safe_output_paths(cls, value):
        for item in value:
            path = PurePosixPath(item)
            if (
                not item
                or len(item) > 512
                or path.is_absolute()
                or ".." in path.parts
                or "\\" in item
            ):
                raise ValueError("output_paths must be bounded relative POSIX paths")
        return FrozenList(value)

    @model_validator(mode="after")
    def _terminal_shape(self):
        if self.terminal_event_seq <= self.formal_seq:
            raise ValueError("terminal event must follow the fixed formal fence")
        if self.process_status == "success":
            if any(
                value is None
                for value in (
                    self.claim_ledger_id,
                    self.bridge_output_id,
                    self.validation_report_id,
                    self.resolution,
                )
            ):
                raise ValueError("successful terminal result requires bridge object IDs")
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("successful terminal result cannot carry an error")
        elif self.error_code is None or self.error_message is None:
            raise ValueError("failed terminal result requires a typed error")
        return self


class _HarnessBridgeSink:
    def __init__(self, harness, evidence_pack: EvidencePackV1) -> None:
        self.harness = harness
        self.evidence_pack = evidence_pack
        self._pack_written = False

    def persist_bridge_batch(self, batch: BridgePersistenceBatch) -> None:
        records = list(batch.records)
        if batch.action == BridgeAction.LEDGER_CREATED:
            if self._pack_written:
                raise RuntimeError("one bridge workflow cannot create two initial ledgers")
            records.insert(0, ("bridge-evidence-pack", self.evidence_pack))
            self._pack_written = True
        self.harness.record_bridge_event(
            batch.action,
            actor=batch.actor,
            inputs=batch.inputs,
            records=records,
            llm=batch.llm,
            finding_ref=batch.finding_ref,
            error_code=batch.error_code,
        )


def _bound_manifest_digest(root, supplied: str) -> str:
    if _SHA256.fullmatch(supplied) is None:
        raise ValueError("run_manifest_digest must be 64 lowercase hex characters")
    path = root / "run-manifest.sha256"
    if path.is_file():
        bound = path.read_text(encoding="utf-8").strip()
        if bound != supplied:
            raise ValueError("BRIDGE_MANIFEST_MISMATCH")
    return supplied


def _terminal_record(
    *,
    result: BridgeWorkflowResultV1,
    evidence_pack: EvidencePackV1,
    manifest_digest: str,
    problem_id: str,
    target: str,
    terminal_event_seq: int,
) -> BridgeTerminalResultV1:
    output = result.bridge_output
    return BridgeTerminalResultV1(
        run_manifest_digest=manifest_digest,
        formal_seq=evidence_pack.formal_seq,
        terminal_event_seq=terminal_event_seq,
        problem_id=problem_id,
        target=target,
        evidence_pack_id=evidence_pack.id,
        claim_ledger_id=(result.claim_ledger.id if result.claim_ledger is not None else None),
        bridge_output_id=(output.id if output is not None else None),
        validation_report_id=(
            result.validation_report.id if result.validation_report is not None else None
        ),
        review_id=(
            result.grounded_review.id if result.grounded_review is not None else None
        ),
        resolution=(output.resolution if output is not None else None),
        process_status=result.process_status,
        error_code=result.error_code,
        error_message=result.error_message,
    )


def build_grounded_bridge(
    harness,
    problem_id: str,
    target: Literal["thesis", "summary", "answer"],
    policy: BridgeWorkflowPolicy | dict,
    *,
    run_manifest_digest: str,
    stage_a_adapter,
    composition_adapter=None,
    review_adapter=None,
    repair_adapter=None,
    attention_pack=None,
    evidence_budget_chars: int = 24_000,
    desired_length_chars: int = 16_384,
    maximum_sections: int = 32,
    formatting_profile: str = "plain",
) -> BridgeTerminalResultV1:
    """Build and persist one grounded final view without touching formal state."""

    harness._ensure_writable()
    if problem_id not in harness.state.problems:
        raise KeyError(f"unknown problem {problem_id!r}")
    if target not in {"thesis", "summary", "answer"}:
        raise ValueError("target must be thesis, summary, or answer")
    manifest_digest = _bound_manifest_digest(harness.root, run_manifest_digest)
    workflow_policy = BridgeWorkflowPolicy.model_validate(policy)

    context = None
    if attention_pack is not None:
        context = ScratchService(harness).create_advisory_context(attention_pack)

    formal_seq = harness._next_seq - 1
    frozen = harness.at(harness.root, formal_seq)
    formal_before = harness.state.model_dump_json()
    commitments_before = dict(harness.commitments)
    warrants_before = dict(harness.warrants)
    evidence_pack = assemble_evidence_pack(
        frozen,
        problem_id,
        budget_chars=evidence_budget_chars,
        formal_seq=formal_seq,
    )
    if context is not None:
        frozen_context = frozen.scratch_state.advisory_contexts.get(context.id)
        if frozen_context != context:
            raise RuntimeError("advisory context is not present at the bridge fence")
    catalog = build_claim_ledger_catalog(
        evidence_pack,
        target,
        advisory_context=context,
    )
    # Review receives exact excerpts from this closed, harness-authored catalog.
    # Scratch excerpts are deliberately omitted: provenance cannot ground a span.
    materials = {
        item.ref: item.excerpt for item in catalog.items if item.kind != "scratch"
    }
    workflow = BridgeWorkflow(
        stage_a_adapter,
        composition_adapter or stage_a_adapter,
        review_adapter=review_adapter,
        repair_adapter=repair_adapter,
        policy=workflow_policy,
        sink=_HarnessBridgeSink(harness, evidence_pack),
    )
    result = workflow.run(
        catalog,
        CompositionRequestV1(
            output_target=target,
            formatting_profile=formatting_profile,
            desired_length_chars=desired_length_chars,
            maximum_sections=maximum_sections,
        ),
        materials=materials,
    )

    if (
        harness.state.model_dump_json() != formal_before
        or harness.commitments != commitments_before
        or harness.warrants != warrants_before
    ):
        raise RuntimeError("bridge workflow altered formal materialized state")
    terminal_seq = harness._next_seq - 1
    terminal = _terminal_record(
        result=result,
        evidence_pack=evidence_pack,
        manifest_digest=manifest_digest,
        problem_id=problem_id,
        target=target,
        terminal_event_seq=terminal_seq,
    )
    payload = terminal.model_dump(mode="json", by_alias=True, exclude_none=True)
    _atomic_json(harness.root / BRIDGE_RESULT_NAME, payload)
    _atomic_json(
        harness.root / BRIDGE_STATUS_NAME,
        {
            "schema": "deepreason-bridge-status-v1",
            "state": "completed" if terminal.process_status == "success" else "failed",
            "process_status": terminal.process_status,
            "formal_seq": terminal.formal_seq,
            "terminal_event_seq": terminal.terminal_event_seq,
            "resolution": (
                terminal.resolution.value if terminal.resolution is not None else None
            ),
            "error_code": terminal.error_code,
        },
    )
    return terminal


__all__ = [
    "BRIDGE_RESULT_NAME",
    "BRIDGE_STATUS_NAME",
    "BridgeTerminalResultV1",
    "build_grounded_bridge",
]
