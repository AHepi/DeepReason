"""Problem schema (spec §1, Def 3.2).

Conj is gated on a nonempty problem frontier (D1 made structural): no
problem, no conjecture. The Popper battery is auto-pinned into criteria.
"""

from enum import Enum

from pydantic import BaseModel, Field


# Popper battery (spec §1): commitment-schema ids auto-pinned into every
# problem's criteria at registration. The pinning mechanism is structural
# from P0; the battery's contents (demarcation checks etc.) land with P1/P2.
POPPER_BATTERY: tuple[str, ...] = ()


class SpawnTrigger(str, Enum):
    SEED = "seed"
    SUCCESSOR = "successor"                    # failed verdict (P2)
    DISCRIMINATION = "discrimination"          # >=2 surviving rivals for one pi
    REMOVE_ARBITRARINESS = "remove-arbitrariness"  # accepted with low HV
    EXPLANATION_DEBT = "explanation-debt"      # reach event
    AUDIT_CRITIC = "audit-critic"              # critic-gaming signal
    CONNECTION = "connection"                  # iso(a) > 0 (§7)
    INTEGRATION = "integration"                # overlapping accepted, no declared relation


class ProblemProvenance(BaseModel):
    trigger: SpawnTrigger
    from_: list[str] = Field(default_factory=list, alias="from")

    model_config = {"populate_by_name": True}


class Problem(BaseModel):
    id: str
    description: str
    # Commitment-schema ids, instantiated per candidate; Popper battery auto-pinned.
    criteria: list[str] = Field(default_factory=list)
    provenance: ProblemProvenance
