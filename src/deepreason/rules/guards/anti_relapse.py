"""Anti-relapse gate (spec §3, §11.5) — mandatory before Conj commit.

Three stages, cheap first:
1. Hash: candidate id matches an existing refuted artifact => block.
2. Semantic trigger (P2): embedding NN against the refuted index within
   NEAR_DUP_EPS narrows which priors face stage 3. Until the embedder lands,
   P1 runs stage 3 against every refuted prior (correct, just less cheap).
3. Battery equivalence: verdict-vector over the active battery matches a
   refuted prior's (~=_B, Def 3.5) => block UNLESS the candidate carries a
   warrant against that prior's refuter. Verdicts differ => admit; the
   near-miss is a capture diagnostic (§11.3).

Near-duplicates of ACCEPTED artifacts are never blocked — attention-deduped
only (blocking them would be a diversity gate adjudicating, forbidden §0).
Negative case law lives here, at the gate — never rendered into packs.
"""

from collections.abc import Iterable

from deepreason import programs
from deepreason.ontology.artifact import Artifact
from deepreason.ontology.state import Status
from deepreason.ontology.warrant import Warrant


def _battery(candidate: Artifact, prior: Artifact, commitments) -> list[str]:
    """Active battery: evaluable commitments across both interfaces."""
    ids = dict.fromkeys(candidate.interface.commitments + prior.interface.commitments)
    return sorted(
        cid for cid in ids if cid in commitments and programs.evaluable(commitments[cid])
    )


def verdict_vector(artifact: Artifact, battery: list[str], harness) -> tuple[str, ...]:
    return tuple(
        programs.evaluate(harness.commitments[cid], artifact, harness.blobs)[0]
        for cid in battery
    )


def check(
    candidate: Artifact,
    warrants: Iterable[Warrant],
    harness,
    embedder=None,
    near_dup_eps: float | None = None,
) -> tuple[bool, str]:
    """(admit, reason). Blocks ONLY relapse onto refuted-equivalents (§0)."""
    status = harness.state.status
    # Stage 1 — hash.
    if status.get(candidate.id) == Status.REFUTED:
        return False, f"hash: {candidate.id[:12]} is a refuted artifact"
    counter_targets = {w.target for w in warrants}
    att = set(harness.state.att)
    # Stage 2 — semantic trigger (§11.5): with an embedder, only refuted
    # priors within NEAR_DUP_EPS face the battery check; without one, every
    # refuted prior does (correct, just less cheap).
    if embedder is not None and near_dup_eps is not None:
        from deepreason.capture.atlas import RefutedIndex
        from deepreason.programs import content_text

        index = RefutedIndex(embedder)
        index.rebuild(harness)
        candidate_vec = embedder.embed(content_text(candidate, harness.blobs))
        prior_ids = index.nearest(candidate_vec, near_dup_eps)
    else:
        prior_ids = [aid for aid, s in status.items() if s == Status.REFUTED]
    for prior_id in prior_ids:
        if prior_id == candidate.id:
            continue
        prior = harness.state.artifacts[prior_id]
        battery = _battery(candidate, prior, harness.commitments)
        if not battery:
            continue  # no shared evaluable battery => no equivalence claim
        # Stage 3 — battery equivalence (~=_B).
        if verdict_vector(candidate, battery, harness) != verdict_vector(
            prior, battery, harness
        ):
            continue  # verdicts differ => admit; near-miss logged by caller
        refuters = {
            x for x, t in att if t == prior_id and status.get(x) == Status.ACCEPTED
        }
        if counter_targets & refuters:
            continue  # carries a warrant against the prior's refuter => admit
        return False, f"battery-equivalent (~=_B) to refuted {prior_id[:12]}"
    return True, "admitted"
