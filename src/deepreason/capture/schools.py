"""Schools (spec §11.1) and allocation (§11.2) — islands in conjecture,
panmixia in criticism.

A school is a persistent conditioning regime for gamma-calls, registered as
an attackable school-policy artifact (Refl). Constitution = lineage
inheritance: school k's packs draw exemplars from accepted artifacts with
provenance.school == k — curation-free by construction. Reseed is
succession, not deletion (D8): a new policy artifact + a Reseed event; the
roster is a deterministic function of the log. Schools never touch att/dep,
adjudication, or statuses.
"""

import json

from deepreason.ontology import Provenance, Rule, SpawnTrigger

# One-time global curation, declared (§11.1 cold start; §17 residue).
STANCE_LIBRARY = {
    "mechanist": "demand a causal mechanism",
    "skeptic": "counterexample first",
    "unifier": "seek the covering principle",
    "empiric": "anchor in cases",
    "formalist": "derivation first",
    "historicist": "precedent and succession",
    "adversary": "strongest attack on the incumbent",
    "minimalist": "parsimony pressure",
}
_STANCES = list(STANCE_LIBRARY)


def _policy_content(school_id: str, stance: str, reseed_of: str | None = None) -> str:
    body = {"school_policy": {"school": school_id, "stance": stance}}
    if reseed_of:
        body["school_policy"]["reseed_of"] = reseed_of
    return json.dumps(body, sort_keys=True)


def roster(harness) -> dict[str, dict]:
    """Latest policy per school, in event order — deterministic from the log."""
    out: dict[str, dict] = {}
    for aid, artifact in harness.state.artifacts.items():
        if artifact.codec != "json" or not artifact.content_ref.startswith("inline:"):
            continue
        try:
            body = json.loads(artifact.content_ref[len("inline:"):])
        except ValueError:
            continue
        policy = body.get("school_policy")
        if isinstance(policy, dict) and "school" in policy:
            out[policy["school"]] = {**policy, "artifact_id": aid}
    return out


def init_schools(harness, config) -> dict[str, dict]:
    """Seed N_SCHOOLS from the stance library (idempotent across reloads)."""
    existing = roster(harness)
    for i in range(config.N_SCHOOLS):
        school_id = f"school-{i}"
        if school_id in existing:
            continue
        stance = _STANCES[i % len(_STANCES)]
        harness.create_artifact(
            _policy_content(school_id, stance),
            codec="json",
            provenance=Provenance(role="seed", school=school_id),
            rule=Rule.REFL,
        )
    return roster(harness)


def reseed(harness, school_id: str, current: dict, reason: str) -> dict:
    """Rotate the laggard's stance seed; logged as a Reseed event. The prior
    policy artifact persists (D8) — succession, not deletion."""
    next_stance = _STANCES[(_STANCES.index(current["stance"]) + 1) % len(_STANCES)]
    harness.create_artifact(
        _policy_content(school_id, next_stance, reseed_of=current["artifact_id"]),
        codec="json",
        provenance=Provenance(role="seed", school=school_id),
        rule=Rule.RESEED,
    )
    harness.record_measure(inputs=["intervention:reseed", f"school:{school_id}", reason])
    return roster(harness)[school_id]


def lineage_size(harness, school_id: str) -> int:
    return sum(
        1
        for a in harness.state.artifacts.values()
        if a.provenance.school == school_id
        and a.provenance.role.value in ("conjecturer", "synthesizer")
    )


def stance_weight(harness, school_id: str, config) -> float:
    """Identity migrates from seed to lineage (STANCE_DECAY schedule)."""
    decay = float(config.STANCE_DECAY) if config.STANCE_DECAY else 20.0
    return max(0.0, 1.0 - lineage_size(harness, school_id) / decay)


def allocate(harness, problem, schools: dict[str, dict], config) -> list[str]:
    """Deterministic function of (log, config) — no per-problem curation."""
    if not schools:
        return []
    everyone = sorted(schools)
    trigger = problem.provenance.trigger
    # Fan-out classes: exactly where rival programmes should compete.
    if trigger in (SpawnTrigger.SEED, SpawnTrigger.DISCRIMINATION, SpawnTrigger.INTEGRATION):
        return everyone
    # Ownership by provenance: lineages follow through on their problem-shifts.
    if trigger in (SpawnTrigger.SUCCESSOR, SpawnTrigger.REMOVE_ARBITRARINESS):
        for fid in problem.provenance.from_:
            artifact = harness.state.artifacts.get(fid)
            if artifact is not None and artifact.provenance.school in schools:
                return [artifact.provenance.school]
        return everyone
    # Other triggers: owner if known, else fan out.
    for fid in problem.provenance.from_:
        artifact = harness.state.artifacts.get(fid)
        if artifact is not None and artifact.provenance.school in schools:
            return [artifact.provenance.school]
    return everyone
