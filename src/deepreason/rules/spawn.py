"""Spawn (spec §3): register a new problem with provenance.

Triggers (all of them):
- failed verdict            => successor problem (P2)
- >=2 surviving rivals      => discrimination problem (informal: comparative, §10.2)
- accepted with low HV      => remove-arbitrariness problem
- reach event               => explanation-debt problem
- critic-gaming signal      => audit-the-critic problem (ensemble disagreement,
                               guard-block streaks, calibration error > JUDGE_ERR_MAX,
                               paraphrase-flip hits, adjudication-ritual flags §11.3)
- iso(a) > 0                => connection problem (§7; pins hv-floor criterion)
- overlapping accepted, no declared relation => integration problem (§7)

Brake 2 (§7): abstraction pays rent on introduction — gates Spawn only,
never statuses.
"""

from deepreason.ontology.problem import SpawnTrigger


def spawn(trigger: SpawnTrigger, from_ids: list[str], state):
    """Register a problem with provenance. TODO(P2)."""
    raise NotImplementedError
