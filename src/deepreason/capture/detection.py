"""Capture detection (spec §11.3) — replay programs over the event log.

All metrics are deterministic functions of (log, embedder, config); the
default HashingEmbedder is itself deterministic, so no raw-log round-trip
is needed. Flags are CONJUNCTIONS — similarity alone is ambiguous (healthy
convergence looks identical); flat progress alone is ambiguous (healthy
exploration looks flat). Hysteresis lives in the scheduler (§11.4).

Honest limit (§17): this detects STALLED dynamics, not wrong-but-stable
ones; only the exogenous anchors bear on those, hence LAMBDA_FLOOR.
"""

import math

from deepreason.llm.embedder import distance
from deepreason.ontology import Status


def _conjecture_stream(harness) -> list[str]:
    return [
        aid
        for aid, a in harness.state.artifacts.items()
        if a.provenance.role.value in ("conjecturer", "synthesizer")
    ]


def _mean_pairwise(vectors: list[list[float]]) -> float | None:
    if len(vectors) < 2:
        return None
    dists = [
        distance(vectors[i], vectors[j])
        for i in range(len(vectors))
        for j in range(i + 1, len(vectors))
    ]
    return sum(dists) / len(dists)


def generator_metrics(harness, embedder, window: int) -> dict:
    stream = _conjecture_stream(harness)[-window:]
    vectors = [harness.embed_artifact(embedder, aid) for aid in stream]
    mean_dist = _mean_pairwise(vectors)
    half = len(vectors) // 2
    first, second = _mean_pairwise(vectors[:half]), _mean_pairwise(vectors[half:])
    slope = (second - first) if (first is not None and second is not None) else None

    by_school: dict[str, list[list[float]]] = {}
    for aid, vec in zip(stream, vectors):
        school = harness.state.artifacts[aid].provenance.school
        if school:
            by_school.setdefault(school, []).append(vec)
    centroids = {
        s: [sum(col) / len(col) for col in zip(*vecs)] for s, vecs in by_school.items()
    }
    ids = sorted(centroids)
    inter = [
        distance(centroids[a], centroids[b])
        for i, a in enumerate(ids)
        for b in ids[i + 1 :]
    ]
    inter_min = min(inter) if inter else None
    # Scale-normalized school separation: inter_school_min_dist relative to the
    # within-stream spread. Embedder-AGNOSTIC (~1.0 = schools as separated as
    # the stream at large, ->0 = converged), unlike inter_school_min_dist whose
    # absolute scale depends on the embedder. The school_convergence flag
    # compares the ABSOLUTE distance to RESEED_DIST_MIN, so that knob must be
    # calibrated to the embedder in use: with the default HashingEmbedder,
    # pairwise distances run "hot" (~0.6-0.9), so a small absolute
    # RESEED_DIST_MIN (e.g. the shipped 0.15) can never fire on real content.
    # Read this ratio (or views/basin.embedder_calibration) to set
    # RESEED_DIST_MIN on-scale.
    inter_ratio = (
        (inter_min / mean_dist) if (inter_min is not None and mean_dist) else None
    )
    # Token-level uncertainty (docs/research: alignment tax) — response
    # diversity can collapse while token surprisal stays informative, so
    # this catches contraction the embedding metrics can miss.
    surprisals = [
        e.llm.mean_surprisal
        for e in harness.recent_events(window)
        if e.llm is not None
        and e.llm.role in ("conjecturer", "synthesizer")
        and e.llm.mean_surprisal is not None
    ]
    half_s = len(surprisals) // 2

    def _avg(xs):
        return sum(xs) / len(xs) if xs else None

    surprisal_mean = _avg(surprisals)
    first_s, second_s = _avg(surprisals[:half_s]), _avg(surprisals[half_s:])
    surprisal_slope = (
        (second_s - first_s) if (first_s is not None and second_s is not None) else None
    )
    return {
        "stream_len": len(stream),
        "mean_pairwise_dist": mean_dist,
        "dist_slope": slope,
        "inter_school_min_dist": inter_min,
        "inter_school_dist_ratio": inter_ratio,
        "mean_token_surprisal": surprisal_mean,
        "surprisal_slope": surprisal_slope,
    }


def school_novelty(harness, embedder, window: int) -> dict[str, float]:
    """Per-school novelty contribution: mean distance of the school's recent
    output to the global recent centroid (laggard selection, §11.4)."""
    stream = _conjecture_stream(harness)[-window:]
    vectors = {aid: harness.embed_artifact(embedder, aid) for aid in stream}
    if not vectors:
        return {}
    all_vecs = list(vectors.values())
    centroid = [sum(col) / len(col) for col in zip(*all_vecs)]
    out: dict[str, list[float]] = {}
    for aid, vec in vectors.items():
        school = harness.state.artifacts[aid].provenance.school
        if school:
            out.setdefault(school, []).append(distance(vec, centroid))
    return {s: sum(d) / len(d) for s, d in out.items()}


def adjudicator_metrics(harness, window: int) -> dict:
    events = harness.recent_events(window)
    # Attack-target entropy: probing new commitments or re-litigating?
    targets = [t for e in events for _, t in e.state_diff.att_add]
    entropy = None
    if len(targets) > 1:
        counts: dict[str, int] = {}
        for t in targets:
            counts[t] = counts.get(t, 0) + 1
        h = -sum((c / len(targets)) * math.log(c / len(targets)) for c in counts.values())
        entropy = h / math.log(len(targets))
    # Criticism debt: accepted artifacts carrying never-evaluated commitments.
    warranted: dict[str, set[str]] = {}
    for w in harness.warrants.values():
        if w.commitment:
            warranted.setdefault(w.target, set()).add(w.commitment)
    from deepreason import programs

    accepted = [
        aid for aid, s in harness.state.status.items()
        if s == Status.ACCEPTED and harness.state.artifacts[aid].interface.commitments
    ]
    indebted = sum(
        1
        for aid in accepted
        if any(
            cid in harness.commitments
            and not programs.evaluable(harness.commitments[cid])
            and cid not in warranted.get(aid, set())
            for cid in harness.state.artifacts[aid].interface.commitments
        )
    )
    debt = (indebted / len(accepted)) if accepted else 0.0
    # G-churn and reinstatement from the transitions replay program.
    transitions = [t for t in harness.transitions() if t[2] is not None]
    recent_seqs = {e.seq for e in events}
    recent = [t for t in transitions if t[0] in recent_seqs]
    churn = len(recent)
    reinstatements = sum(1 for _, _, old, new in recent if old == "refuted" and new == "accepted")
    refutations = sum(1 for _, _, _, new in recent if new == "refuted")
    # Validity-node attack rate: if no test is ever attacked, D3 has died.
    nus = {w.validity_node for w in harness.warrants.values()}
    attacked_nus = {t for _, t in harness.state.att if t in nus}
    return {
        "attack_target_entropy": entropy,
        "criticism_debt": debt,
        "g_churn": churn,
        "reinstatement_rate": (reinstatements / refutations) if refutations else None,
        "refutations": refutations,
        "validity_attack_rate": (len(attacked_nus) / len(nus)) if nus else None,
        "n_attacks": len(targets),
    }


def grounding_lambda(harness, window: int) -> float:
    """Windowed fraction of verdicts from program/observation evals vs
    rubric. No verdicts in window => 1.0 (nothing rode on a rubric)."""
    events = harness.recent_events(window)
    recent_warrants = [
        harness.warrants[oid]
        for e in events
        for oid in e.outputs
        if oid in harness.warrants
    ]
    verdicts = [w for w in recent_warrants if w.commitment]
    if not verdicts:
        return 1.0
    exogenous = sum(
        1
        for w in verdicts
        if w.commitment in harness.commitments
        and not harness.commitments[w.commitment].eval.startswith("rubric:")
    )
    return exogenous / len(verdicts)


def gate_block_count(harness, window: int) -> int:
    """Anti-relapse refusals in the recent event window. The basin study
    (docs/BASIN_REPORT.md) measured this as the clean circling signal:
    0 in every healthy arm, 54/36 in the two refuted-attractor-orbiting
    arms — scale-free, free, and already on the log."""
    return sum(
        1
        for e in harness.recent_events(window)
        for i in e.inputs
        if isinstance(i, str) and i.startswith("gate:")
    )


def orbit_attractor_school(harness, window: int) -> str | None:
    """The school whose refuted attractor the generator is orbiting:
    majority school across the refuted targets named by recent gate
    blocks (deterministic tiebreak by school id)."""
    import re

    counts: dict[str, int] = {}
    for e in harness.recent_events(window):
        for i in e.inputs:
            if not (isinstance(i, str) and i.startswith("gate:")):
                continue
            m = re.search(r"to refuted ([0-9a-f]{8,})", i)
            if not m:
                continue
            prefix = m.group(1)
            for aid, a in harness.state.artifacts.items():
                if aid.startswith(prefix) and a.provenance.school:
                    counts[a.provenance.school] = counts.get(a.provenance.school, 0) + 1
                    break
    if not counts:
        return None
    return max(sorted(counts), key=lambda s: counts[s])


def raw_flags(harness, embedder, config) -> dict[str, bool]:
    """Un-hysteresized conjunction flags for one window (§11.3)."""
    window = config.CAPTURE_W
    gen = generator_metrics(harness, embedder, window)
    adj = adjudicator_metrics(harness, window)
    lam = grounding_lambda(harness, window)

    contraction = gen["dist_slope"] is not None and gen["dist_slope"] < 0.0
    flat = adj["g_churn"] == 0
    stagnation = contraction and flat

    convergence = (
        config.RESEED_DIST_MIN is not None
        and gen["inter_school_min_dist"] is not None
        and gen["inter_school_min_dist"] < config.RESEED_DIST_MIN
    )

    ritual_conditions = [
        adj["attack_target_entropy"] is not None
        and adj["attack_target_entropy"] < config.ATTACK_ENTROPY_FLOOR,
        adj["criticism_debt"] > config.CRIT_DEBT_CEILING,
        adj["refutations"] >= config.MIN_ATTACKS_FOR_RITUAL
        and (adj["reinstatement_rate"] or 0.0) == 0.0,
        adj["n_attacks"] >= config.MIN_ATTACKS_FOR_RITUAL
        and (adj["validity_attack_rate"] or 0.0) == 0.0,
    ]
    ritual = sum(ritual_conditions) >= 2

    grounding_decay = config.LAMBDA_FLOOR is not None and lam < config.LAMBDA_FLOOR

    # Refuted-attractor orbiting (basin study): the generator keeps
    # re-proposing battery-equivalents of a refuted artifact and the gate
    # keeps refusing them. Unlike the embedding flags this needs no
    # calibrated scale — a healthy run's rate is exactly zero.
    orbiting = (
        config.GATE_ORBIT_MIN is not None
        and gate_block_count(harness, window) >= config.GATE_ORBIT_MIN
    )
    return {
        "lineage_stagnation": stagnation,
        "school_convergence": convergence,
        "adjudication_ritual": ritual,
        "grounding_decay": grounding_decay,
        "attractor_orbiting": orbiting,
    }
