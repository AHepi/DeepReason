"""Schools (spec §11.1) and allocation (§11.2) — islands in conjecture,
panmixia in criticism.

A school = (endpoint/family, stance_seed, lineage exemplar slice, render
weights), registered as an attackable school-policy artifact (Refl).
Constitution = lineage inheritance: school k conditions on its own accepted
descendants. Cold start from the shipped stance library; stance weight
decays (STANCE_DECAY) as lineage grows.

Allocation is a deterministic function of (event log, config):
ownership-by-provenance for successor/remove-arbitrariness; full fan-out for
seed/discrimination/integration; XEXAM_SHARE to the most-foreign school;
recruitment on stagnation; optional user pinning.
"""

# One-time global curation, declared (§11.1 cold start / §17 residue).
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


def allocate(problem_id: str, state, config) -> list[str]:
    """School ids assigned to work a problem (§11.2). TODO(P2)."""
    raise NotImplementedError


def reseed(school_id: str, state, config):
    """Reseed the laggard: rotate stance/exemplar slice/family; log a
    Reseed event. Succession, not deletion (D8). TODO(P2)."""
    raise NotImplementedError
