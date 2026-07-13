"""Graph bridge for model-scoped simulation results and world claims.

A deterministic simulation receipt describes one executable model under
pinned inputs and a checker.  Relevance to a broader claim is a separate,
ordinary artifact that can be attacked without changing the receipt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from deepreason.canonical import canonical_json
from deepreason.ontology import Interface, Provenance, Ref
from deepreason.ontology.artifact import Artifact, RefRole
from deepreason.verification.simulation import SimulationVerificationResult


class _SimulationModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )


class SimulationClaim(_SimulationModel):
    schema_: Literal["deepreason-simulation-claim-v1"] = Field(
        default="deepreason-simulation-claim-v1", alias="schema"
    )
    statement: str = Field(min_length=1)


class SimulationMismatchTest(_SimulationModel):
    id: str = Field(min_length=1)
    case: str = Field(min_length=1)
    model_expectation: str = Field(min_length=1)
    world_expectation: str = Field(min_length=1)


class SimulationRelevanceRelation(_SimulationModel):
    schema_: Literal["deepreason-simulation-relevance-v1"] = Field(
        default="deepreason-simulation-relevance-v1", alias="schema"
    )
    result_ref: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_claim: str = Field(min_length=1)
    assumptions: tuple[str, ...] = ()
    scope: str = Field(min_length=1)
    counterconditions: tuple[str, ...] = Field(min_length=1)
    mismatch_tests: tuple[SimulationMismatchTest, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_tests(self):
        ids = [item.id for item in self.mismatch_tests]
        if len(ids) != len(set(ids)):
            raise ValueError("simulation mismatch test ids must be unique")
        return self


@dataclass(frozen=True)
class SimulationWorkflowArtifacts:
    result: Artifact
    relation: Artifact
    claim: Artifact


def register_simulation_workflow(
    harness,
    result: SimulationVerificationResult,
    relation: SimulationRelevanceRelation,
    claim: SimulationClaim,
    *,
    explicit_model_dependence: bool = False,
) -> SimulationWorkflowArtifacts:
    """Register result, relevance relation, and an optionally dependent claim."""

    if relation.result_ref != result.output_ref:
        raise ValueError("simulation relation names a different result output")
    if relation.target_claim != claim.statement:
        raise ValueError("simulation relation must name the exact target claim")
    for ref in (result.output_ref, result.diagnostics_ref, result.stdout_ref, result.stderr_ref):
        if ref is not None:
            harness.blobs.get(ref)
    result_artifact = harness.create_artifact(
        canonical_json(result.model_dump(mode="json")),
        codec="json",
        interface=Interface(),
        provenance=Provenance(role="import"),
    )
    relation_artifact = harness.create_artifact(
        canonical_json(relation.model_dump(mode="json", by_alias=True)),
        codec="json",
        interface=Interface(
            refs=[Ref(target=result_artifact.id, role=RefRole.MENTION)]
        ),
        provenance=Provenance(role="user"),
    )
    refs = []
    if explicit_model_dependence:
        refs = [
            Ref(target=result_artifact.id, role=RefRole.DEPENDENCE),
            Ref(target=relation_artifact.id, role=RefRole.DEPENDENCE),
        ]
    claim_artifact = harness.create_artifact(
        claim.statement,
        interface=Interface(refs=refs),
        provenance=Provenance(role="user"),
    )
    return SimulationWorkflowArtifacts(
        result=result_artifact,
        relation=relation_artifact,
        claim=claim_artifact,
    )
