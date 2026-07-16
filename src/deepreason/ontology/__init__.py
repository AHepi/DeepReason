"""Ontology — the one schema (spec §1).

Artifacts are untyped (no ``kind`` field, ever). Dispatch is on interface
structure only: a warrant against a target contributes an attack edge; a
``dependence`` ref contributes a support edge. ``dep`` must remain a DAG.
"""

from deepreason.ontology.artifact import Artifact, Interface, Provenance, Ref
from deepreason.ontology.commitment import Budget, Commitment
from deepreason.ontology.event import (
    Event,
    LLMAttempt,
    LLMCall,
    Rule,
    SchoolRouteReceiptV1,
    StateDiff,
)
from deepreason.ontology.problem import Problem, ProblemProvenance, SpawnTrigger
from deepreason.ontology.state import EpistemicState, Status
from deepreason.ontology.warrant import Warrant, WarrantType

__all__ = [
    "Artifact",
    "Budget",
    "Commitment",
    "EpistemicState",
    "Event",
    "Interface",
    "LLMCall",
    "LLMAttempt",
    "Problem",
    "ProblemProvenance",
    "Provenance",
    "Ref",
    "Rule",
    "SchoolRouteReceiptV1",
    "SpawnTrigger",
    "StateDiff",
    "Status",
    "Warrant",
    "WarrantType",
]
