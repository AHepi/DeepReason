"""Text-first explanatory workload and compact-v2 semantic compilation."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from deepreason.llm.contracts import EvidenceRefClaimV1
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
    # Dual-mode conjecture (D2 rev 2, R33/M24): the model-authored checker
    # source + fixed tests for eval == "program:candidate_checker" — the
    # SAME coupling ForbiddenCase.checker_spec enforces on the
    # ConjectureCandidate path (informal/skeleton.py).
    checker_spec: dict | None = None

    @model_validator(mode="after")
    def _checker_spec_matches_kind(self):
        is_candidate_checker = self.eval == "program:candidate_checker"
        v = self.checker_spec
        if is_candidate_checker and not (v and v.get("source") and v.get("entry") and v.get("tests")):
            raise ValueError(
                "program:candidate_checker counterconditions require "
                "checker_spec = {source, entry, tests}")
        if not is_candidate_checker and v is not None:
            raise ValueError(
                "checker_spec is only meaningful for "
                "eval == 'program:candidate_checker'")
        return self


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
    # Item-level min_length mirrors Countercondition.case so that a
    # wire-valid proposal is always envelope-constructible: a live
    # gpt-oss:120b reply carried an empty countercondition string, passed
    # this schema as it stood, and crashed proposal_envelope outside the
    # repair loop (live_smoke_v1 finding F1). Rejecting it here routes the
    # reply through ordinary schema repair instead.
    counterconditions: tuple[Annotated[str, StringConstraints(min_length=1)], ...] = Field(
        min_length=1, max_length=32
    )
    # Dual-mode conjecture (D2 rev 2, R33/step 6): additive and optional so
    # counterconditions' own wire TYPE never changes — paired by index, empty
    # entries mean "eval=observation" as before. A new required/typed field
    # on counterconditions itself would be a wire-breaking change needing a
    # contract-version bump; this is the narrower alternative that doesn't.
    checker_specs: tuple[dict | None, ...] = ()
    typicality: float = Field(ge=0.0, le=1.0)
    optional_refs: tuple[str, ...] = ()
    # Claimed groundings in admitted evidence blocks (admission §4); checked
    # deterministically after admission, never trusted on arrival.
    evidence_refs: tuple[EvidenceRefClaimV1, ...] = Field(default=(), max_length=8)
    analogy: AnalogyClaim | None = None
    sidecar: OperationalSidecar = Field(default_factory=OperationalSidecar)

    @model_validator(mode="after")
    def _checker_specs_pair_with_counterconditions(self):
        if self.checker_specs and len(self.checker_specs) != len(self.counterconditions):
            raise ValueError(
                "checker_specs, if given, must have one entry per "
                "countercondition (use null for entries without a checker)")
        return self


class ReasoningConjecturerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidates: tuple[ReasoningCandidateProposal, ...] = Field(min_length=1)


def proposal_envelope(candidate: ReasoningCandidateProposal) -> ReasoningEnvelopeV1:
    specs = candidate.checker_specs or (None,) * len(candidate.counterconditions)
    return ReasoningEnvelopeV1(
        claim=candidate.claim,
        mechanism=candidate.mechanism,
        counterconditions=tuple(
            Countercondition(case=case, eval="program:candidate_checker", checker_spec=spec)
            if spec is not None
            else Countercondition(case=case, eval="observation")
            for case, spec in zip(candidate.counterconditions, specs)
        ),
        analogy=candidate.analogy,
    )


def envelope_json(envelope: ReasoningEnvelopeV1) -> str:
    return json.dumps(
        envelope.model_dump(mode="json", by_alias=True),
        sort_keys=True,
        separators=(",", ":"),
    )


def draft_countercondition_commitments(envelope: ReasoningEnvelopeV1) -> list[Commitment]:
    """Pure construction of safe, bounded countercondition Commitments.

    No registry writes: two-phase compilation (RC5) gates on these drafts
    and registers them only after admission."""
    from deepreason import programs
    from deepreason.ontology.commitment import Budget

    drafts: list[Commitment] = []
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
                {
                    "case": countercondition.case,
                    "eval": evaluation,
                    "checker_spec": countercondition.checker_spec,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        budget = Budget()
        if countercondition.checker_spec is not None:
            # Same {source, entry, tests, step_limit} convention as
            # ForbiddenCase.checker_spec (informal/skeleton.py) — the
            # checker source lives in the budget since the carrying
            # artifact's own content is the reasoning envelope's prose.
            budget = Budget(extra={"spec": json.dumps(countercondition.checker_spec, sort_keys=True)})
        drafts.append(
            Commitment(
                id=f"reason-counter@{digest[:24]}",
                eval=evaluation,
                observation_valued=observation_valued,
                budget=budget,
            )
        )
    return drafts


def compile_countercondition_commitments(harness, envelope: ReasoningEnvelopeV1) -> list[str]:
    """Compile safe, bounded current-run counterconditions before identity."""
    compiled: list[str] = []
    for commitment in draft_countercondition_commitments(envelope):
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
