"""Epistemic state (spec §1, Def 3.3) — materialized view, never ground truth.

S = (A, Pi, carry, att, dep, addr, status, hv, reach, conn). Status is computed by
the two-pass adjudicator (§4), never stored authoritatively; recompute from
the event log at any seq.
"""

from enum import Enum

from pydantic import BaseModel, Field

from deepreason.ontology.artifact import Artifact
from deepreason.ontology.problem import Problem


class Status(str, Enum):
    ACCEPTED = "accepted"
    REFUTED = "refuted"
    SUSPENDED = "suspended"
    # Pass 2: accepted in attack semantics but a dependence is not accepted.
    # Orphaned != false.
    SUSPENDED_UNSUPPORTED = "suspended_unsupported"


class EpistemicState(BaseModel):
    artifacts: dict[str, Artifact] = Field(default_factory=dict)  # A
    problems: dict[str, Problem] = Field(default_factory=dict)  # Pi
    # Explicit warrant carriage (carrier artifact, warrant). Historical logs
    # materialize this relation from Artifact.warrants; new events record it
    # directly so content dedupe cannot erase a second attack.
    carries: list[tuple[str, str]] = Field(default_factory=list)
    att: list[tuple[str, str]] = Field(default_factory=list)  # (attacker, target)
    dep: list[tuple[str, str]] = Field(default_factory=list)  # (dependent, dependency); DAG
    addr: list[tuple[str, str]] = Field(default_factory=list)  # (artifact, problem)
    status: dict[str, Status] = Field(default_factory=dict)  # computed, §4
    hv: dict[str, float] = Field(default_factory=dict)  # lazy spot-check estimates (§6)
    reach: dict[str, float] = Field(default_factory=dict)  # §6
    conn: dict[str, int] = Field(default_factory=dict)  # §7
