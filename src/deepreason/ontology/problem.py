"""Problem schema (spec §1, Def 3.2).

Conj is gated on a nonempty problem frontier (D1 made structural): no
problem, no conjecture. The Popper battery is auto-pinned into criteria.
"""

from enum import Enum

from pydantic import ConfigDict, Field, field_validator

from deepreason.ontology.frozen import FrozenList, FrozenRecord


# Popper battery (spec §1): commitment-schema ids auto-pinned into every
# problem's criteria at registration. The pinning mechanism is structural
# from P0; the battery's contents (demarcation checks etc.) land with P1/P2.
POPPER_BATTERY: tuple[str, ...] = ()


class SpawnTrigger(str, Enum):
    SEED = "seed"
    # INERT VOCABULARY: producers = 0. No code path mints a problem with
    # this trigger -- `scan_spawns` stopped on refutation (H1, Rung 3a) and
    # `easy.py::seed_component` stopped on staged-pipeline repair (Rung 3d,
    # the website pipeline's decommissioning). The member is retained only
    # so pre-v2 roots still parse on replay; its presence asserts no
    # producer and licenses no new one. The invariant is enforced by a
    # source scan, not by this list -- see
    # tests/test_decommissioned_pipeline_stays_out.py.
    SUCCESSOR = "successor"                    # retained for replay only
    DISCRIMINATION = "discrimination"          # >=2 surviving rivals for one pi
    REMOVE_ARBITRARINESS = "remove-arbitrariness"  # accepted with low HV
    EXPLANATION_DEBT = "explanation-debt"      # reach event
    AUDIT_CRITIC = "audit-critic"              # critic-gaming signal
    CONNECTION = "connection"                  # iso(a) > 0 (§7)
    INTEGRATION = "integration"                # overlapping accepted, no declared relation
    RESEARCH = "research"                      # observation-valued, no covering evidence (§12)
    # §9.4. Promotion is purchase of exposure: an ordinary Conj->Crit->Adj pass
    # whose problem is the one a frame assertion must address to be consulted
    # at all (Def 9.2). Rung 4 defines what such a problem IS, because the
    # consult predicate is undefined without it; Rung 5 owns WHEN one is
    # spawned -- nomination is a measure-rule that detects and never decides.
    PROMOTION = "promotion"


class ProblemProvenance(FrozenRecord):
    trigger: SpawnTrigger
    from_: list[str] = Field(default_factory=FrozenList, alias="from")

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    @field_validator("from_", mode="after")
    @classmethod
    def _freeze_sources(cls, value):
        return FrozenList(value)


class Problem(FrozenRecord):
    id: str
    description: str
    # Commitment-schema ids, instantiated per candidate; Popper battery auto-pinned.
    criteria: list[str] = Field(default_factory=FrozenList)
    provenance: ProblemProvenance

    @field_validator("criteria", mode="after")
    @classmethod
    def _freeze_criteria(cls, value):
        return FrozenList(value)
