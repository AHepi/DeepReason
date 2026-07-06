"""M1 — dedupe + refuted-equivalence gate + orbit detector (MINI_PLAN §3.3).

Gate refusals are logged Measure inputs in the parent's ``gate:<reason>``
format, so the orbit counter here AND the parent's detection/invariants
tooling both read them. NO embeddings in v0: the parent's embedding
detector is scale-blind (within/cross medians 0.645 vs 0.671); the
gate-rate detector separated healthy from orbiting perfectly on all 15
parent roots (healthy: 0 blocks ever; orbiting: 7-14 per window).
"""

import re


def normalize(text: str) -> frozenset[str]:
    """Normalized-token-set equivalence — the v0 stand-in for battery
    equivalence (~=_B). If live smoke shows paraphrase orbiting slipping
    this, the parent's verdict-vector check goes behind a flag (MINI_PLAN
    §6 risk 1)."""
    return frozenset(re.findall(r"[a-z0-9]+", text.lower()))


def check(candidate_id: str, candidate_text: str, state) -> tuple[bool, str]:
    """(admit, reason). Blocks ONLY relapse onto refuted-equivalents;
    duplicates of LIVE artifacts are deduped by the caller, never gated
    (blocking them would be a diversity gate adjudicating)."""
    refuted = state.refuted
    if candidate_id in refuted:
        return False, f"hash: {candidate_id[:12]} is a refuted artifact"
    tokens = normalize(candidate_text)
    for prior_id in sorted(refuted):
        prior = state.artifacts.get(prior_id)
        if prior is None or not prior.get("content_ref", "").startswith("inline:"):
            continue
        if tokens == normalize(prior["content_ref"][len("inline:"):]):
            return False, f"battery-equivalent (~=_B) to refuted {prior_id[:12]}"
    return True, "admitted"


def gate_blocks(events, window: int = 20) -> list[str]:
    """gate:<reason> inputs across the recent event window."""
    return [
        i
        for e in events[-window:]
        for i in e.inputs
        if isinstance(i, str) and i.startswith("gate:")
    ]


def orbit(events, artifacts: dict[str, dict], window: int = 20, floor: int = 5) -> str | None:
    """Refuted-attractor orbiting: gate-block rate over the window reaches
    the floor => return the school (stance) whose refuted attractor is being
    orbited — majority school across the refuted targets named by the
    blocks, deterministic tiebreak. None => healthy (measured rate: exactly
    zero in every healthy arm; 4.3x token burn when ignored)."""
    blocks = gate_blocks(events, window)
    if len(blocks) < floor:
        return None
    counts: dict[str, int] = {}
    for reason in blocks:
        # Both refusal shapes name the refuted prior: the parent's detector
        # matches the "to refuted <id>" form; hash relapses count here too.
        m = re.search(r"(?:to refuted|hash:) ([0-9a-f]{8,})", reason)
        if not m:
            continue
        prefix = m.group(1)
        for aid, a in artifacts.items():
            school = (a.get("provenance") or {}).get("school")
            if aid.startswith(prefix) and school:
                counts[school] = counts.get(school, 0) + 1
                break
    if not counts:
        return None
    return max(sorted(counts), key=lambda s: counts[s])
