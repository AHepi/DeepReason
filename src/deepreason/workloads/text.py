"""Text-first explanatory workload and compact-v2 semantic compilation."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepreason.ontology import Commitment, Problem, ProblemProvenance


class WorkloadProblem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    description: str = Field(min_length=1)


class BrainRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = False
    query: str | None = None


class ReasoningWorkloadSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_: Literal["deepreason-text-workload-v1"] = Field(
        default="deepreason-text-workload-v1", alias="schema"
    )
    problem: WorkloadProblem
    criteria: tuple[Commitment, ...] = ()
    sources: tuple[str, ...] = ()
    allow_rubric: bool = True
    allow_formalization: bool = True
    allow_simulation: bool = True
    brain: BrainRequest = Field(default_factory=BrainRequest)


class Definition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    term: str
    meaning: str


class Premise(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    claim: str
    refs: tuple[str, ...] = ()


class DerivationStep(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    from_: tuple[str, ...] = Field(default=(), alias="from")
    step: str


class Scope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    covers: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()


class Countercondition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    case: str = Field(min_length=1)
    eval: str = Field(pattern=r"^(program:[A-Za-z0-9_.@-]+|rubric:[A-Za-z0-9_.@-]+|observation)$")


class AnalogyClaim(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_memory_refs: tuple[str, ...] = Field(min_length=1, max_length=32)
    shared_structure: tuple[str, ...] = Field(min_length=1, max_length=32)
    disanalogies: tuple[str, ...] = Field(min_length=1, max_length=32)
    transfer_claims: tuple[str, ...] = Field(min_length=1, max_length=32)
    adopted_commitment_refs: tuple[str, ...] = ()
    overturn_conditions: tuple[str, ...] = Field(min_length=1, max_length=32)


class ReasoningEnvelopeV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_: Literal["deepreason-reasoning-envelope-v1"] = Field(
        default="deepreason-reasoning-envelope-v1", alias="schema"
    )
    claim: str = Field(min_length=1, max_length=8000)
    definitions: tuple[Definition, ...] = Field(default=(), max_length=64)
    premises: tuple[Premise, ...] = Field(default=(), max_length=64)
    mechanism: str = Field(default="", max_length=8000)
    derivation: tuple[DerivationStep, ...] = Field(default=(), max_length=128)
    scope: Scope = Field(default_factory=Scope)
    counterconditions: tuple[Countercondition, ...] = Field(default=(), max_length=64)
    analogy: AnalogyClaim | None = None
    formalization_refs: tuple[str, ...] = ()
    simulation_refs: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = Field(default=(), max_length=64)

    @model_validator(mode="after")
    def _attack_surface_and_local_refs(self):
        if not (self.mechanism.strip() or self.premises or self.counterconditions):
            raise ValueError("reasoning envelope requires a nonempty attack surface")
        local = {f"P{index}" for index in range(1, len(self.premises) + 1)}
        for step in self.derivation:
            unknown = set(step.from_) - local
            if unknown:
                raise ValueError(f"unknown local premise references: {sorted(unknown)}")
        return self


class OperationalSidecar(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    search_signal: Literal[
        "productive", "need_context", "stuck", "capability_mismatch"
    ] = "productive"
    requested_context_aliases: tuple[str, ...] = ()


class ReasoningCandidateProposal(BaseModel):
    """Gemma-safe semantic proposal; mandatory interfaces are absent by design."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    claim: str = Field(min_length=1)
    mechanism: str = Field(min_length=1)
    counterconditions: tuple[str, ...] = Field(min_length=1, max_length=32)
    typicality: float = Field(ge=0.0, le=1.0)
    optional_refs: tuple[str, ...] = ()
    analogy: AnalogyClaim | None = None
    sidecar: OperationalSidecar = Field(default_factory=OperationalSidecar)


class ReasoningConjecturerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidates: tuple[ReasoningCandidateProposal, ...] = Field(min_length=1)


def proposal_envelope(candidate: ReasoningCandidateProposal) -> ReasoningEnvelopeV1:
    return ReasoningEnvelopeV1(
        claim=candidate.claim,
        mechanism=candidate.mechanism,
        counterconditions=tuple(
            Countercondition(case=case, eval="observation")
            for case in candidate.counterconditions
        ),
        analogy=candidate.analogy,
    )


def envelope_json(envelope: ReasoningEnvelopeV1) -> str:
    return json.dumps(
        envelope.model_dump(mode="json", by_alias=True),
        sort_keys=True,
        separators=(",", ":"),
    )


def compile_countercondition_commitments(harness, envelope: ReasoningEnvelopeV1) -> list[str]:
    """Compile safe, bounded current-run counterconditions before identity."""
    from deepreason import programs

    compiled: list[str] = []
    for countercondition in envelope.counterconditions:
        evaluation = countercondition.eval
        observation_valued = evaluation == "observation"
        if observation_valued:
            evaluation = "program:reasoning_observation_pending"
        elif evaluation.startswith("program:"):
            program = evaluation.partition(":")[2]
            if program not in programs.PROGRAMS:
                raise ValueError(f"countercondition uses unknown program: {program}")
        digest = hashlib.sha256(
            json.dumps(
                {"case": countercondition.case, "eval": evaluation},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        commitment = Commitment(
            id=f"reason-counter@{digest[:24]}",
            eval=evaluation,
            observation_valued=observation_valued,
        )
        harness.register_commitment(commitment)
        compiled.append(commitment.id)
    return compiled


def reasoning_wf_program(text: str, budget, artifact=None) -> tuple[str, dict]:
    try:
        envelope = ReasoningEnvelopeV1.model_validate_json(text)
    except ValueError as error:
        return "fail", {"error": str(error)[:500]}
    encoded = envelope_json(envelope)
    max_chars = int(budget.extra.get("max_chars", 64_000))
    if len(encoded) > max_chars:
        return "overrun", {"chars": len(encoded), "limit": max_chars}
    return "pass", {
        "claim": envelope.claim[:160],
        "premises": len(envelope.premises),
        "counterconditions": len(envelope.counterconditions),
    }


def seed_reasoning_workload(harness, spec: ReasoningWorkloadSpec) -> Problem:
    from deepreason.ontology.commitment import Budget

    for commitment in spec.criteria:
        if commitment.eval.startswith("rubric:") and not spec.allow_rubric:
            raise ValueError("workload forbids rubric commitments")
        harness.register_commitment(commitment)
    wf = Commitment(
        id="reasoning-envelope-wf",
        eval="program:reasoning-envelope-wf",
        budget=Budget(steps=10_000, time_ms=2_000, extra={"max_chars": 64_000}),
    )
    harness.register_commitment(wf)
    criteria = list(dict.fromkeys([wf.id, *(item.id for item in spec.criteria)]))
    return harness.register_problem(
        Problem(
            id=spec.problem.id,
            description=spec.problem.description,
            criteria=criteria,
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def spec_from_text(text: str) -> ReasoningWorkloadSpec:
    normalized = re.sub(r"\s+", " ", text).strip()
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    return ReasoningWorkloadSpec(
        problem=WorkloadProblem(id=f"reason:{digest}", description=normalized)
    )


class TextWorkloadAdapter:
    profile = "text"
    pack_profile = "reasoning.text.v1"
    progress_phases = (
        "retrieve",
        "conjecture",
        "deterministic-checks",
        "criticism",
        "discrimination",
        "capture",
        "convergence",
    )

    @staticmethod
    def completion(root) -> bool:
        from pathlib import Path

        return (Path(root) / "run-result.json").exists()


TEXT_WORKLOAD = TextWorkloadAdapter()
