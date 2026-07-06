"""Basin diagnostics (view, spec §8): when does conjecture circle a basin
— low variation, little novelty — and which mechanism is pulling it there?

Everything here is a deterministic function of (log, embedder, config);
nothing writes. The series is per-conjecture, in creation order, so onset
("when") is a curve, not a flag. The candidate mechanisms measured:

  stance decay   — stance_weight hits 0 at lineage STANCE_DECAY; packs
                   lose the school identity section (packs.py) and all
                   schools converge on the generator's modal answer.
  neighbourhood  — packs show up to 8 accepted artifacts; the generator
    echo           is conditioned on its own past output every call. The
                   logged prompt blob names the exemplars, so echo is
                   directly measurable: distance of each new conjecture
                   to what its own pack displayed.
  monopoly       — successor ownership is rich-get-richer (64:1 observed
                   live); run diversity collapses to one school's.
  survivorship   — adjudication keeps a narrow subset of a wide pool.
  embedder scale — hashing-embedder distances run hot; thresholds like
                   RESEED_DIST_MIN mean nothing until calibrated against
                   within-problem vs cross-problem reference pairs.
"""

import re
from statistics import mean, median

from deepreason.llm.embedder import distance
from deepreason.ontology import Status

_EXEMPLAR = re.compile(r"^- ([0-9a-f]{16,}): ", re.M)


def _conjectures(harness) -> list:
    arts = [
        a for a in harness.state.artifacts.values()
        if a.provenance.role.value in ("conjecturer", "synthesizer")
        and a.provenance.event_seq is not None
    ]
    return sorted(arts, key=lambda a: a.provenance.event_seq)


def _pack_exemplars(harness, log: list, seq: int) -> list[str]:
    """Artifact ids the creating event's prompt actually displayed."""
    e = log[seq] if seq < len(log) else None
    if e is None or e.llm is None or not e.llm.prompt_ref:
        return []
    try:
        pack = harness.blobs.get(e.llm.prompt_ref).decode(errors="replace")
    except KeyError:
        return []
    head, _, _ = pack.partition("DIRECTIVE:")
    return [m for m in _EXEMPLAR.findall(head) if m in harness.state.artifacts]


def conjecture_series(harness, embedder, stance_decay: float = 20.0) -> list[dict]:
    """One row per conjecture, in creation order: novelty (distance to the
    nearest PRIOR conjecture, global and within-school), echo (distance to
    the nearest exemplar its own pack displayed), stance weight at
    creation, surprisal, school."""
    log = list(harness.log.read())
    addr: dict[str, str] = {}
    for aid, pid in harness.state.addr:
        addr.setdefault(aid, pid)
    rows: list[dict] = []
    seen: list[tuple[str, str, list[float]]] = []  # (aid, school, vec)
    lineage_count: dict[str, int] = {}
    problem_age: dict[str, int] = {}
    for a in _conjectures(harness):
        vec = harness.embed_artifact(embedder, a.id)
        school = a.provenance.school or ""
        pid = addr.get(a.id, "")
        prior_global = [(distance(vec, v), x) for x, _, v in seen]
        prior_within = [distance(vec, v) for _, s, v in seen if s == school]
        exemplars = {x for x in _pack_exemplars(harness, log, a.provenance.event_seq)
                     if x != a.id}
        echo = [
            distance(vec, harness.embed_artifact(embedder, x)) for x in exemplars
        ]
        novelty, nearest = min(prior_global) if prior_global else (None, None)
        e = log[a.provenance.event_seq]
        rows.append({
            "seq": a.provenance.event_seq,
            "id": a.id[:12],
            "school": school,
            "problem": pid,
            "problem_age": problem_age.get(pid, 0),
            "novelty_global": novelty,
            "novelty_within": min(prior_within) if prior_within else None,
            # The causal fingerprint of pack echo: is the nearest prior
            # artifact one the pack actually DISPLAYED to the generator?
            "nearest_was_shown": (nearest in exemplars) if nearest else None,
            "echo_min": min(echo) if echo else None,
            "echo_n_exemplars": len(echo),
            "stance_weight": max(0.0, 1.0 - lineage_count.get(school, 0) / stance_decay),
            "surprisal": e.llm.mean_surprisal if e.llm else None,
            "status": harness.state.status.get(a.id).value
                      if a.id in harness.state.status else None,
        })
        seen.append((a.id, school, vec))
        lineage_count[school] = lineage_count.get(school, 0) + 1
        problem_age[pid] = problem_age.get(pid, 0) + 1
    return rows


def windowed(series: list[dict], harness, embedder, w: int = 12) -> list[dict]:
    """Rolling views: within-school diversity, inter-school centroid
    distance, top-school generation share, novelty median."""
    conjs = _conjectures(harness)
    vecs = [harness.embed_artifact(embedder, a.id) for a in conjs]
    out = []
    for end in range(w, len(conjs) + 1):
        rows = series[end - w:end]
        chunk = list(zip(conjs[end - w:end], vecs[end - w:end]))
        by_school: dict[str, list] = {}
        for a, v in chunk:
            by_school.setdefault(a.provenance.school or "", []).append(v)
        within = []
        for vs in by_school.values():
            if len(vs) >= 2:
                within += [distance(vs[i], vs[j])
                           for i in range(len(vs)) for j in range(i + 1, len(vs))]
        cents = {s: [sum(c) / len(c) for c in zip(*vs)]
                 for s, vs in by_school.items() if vs}
        ids = sorted(cents)
        inter = [distance(cents[a], cents[b])
                 for i, a in enumerate(ids) for b in ids[i + 1:]]
        share = max(len(v) for v in by_school.values()) / len(chunk)
        novelty = [r["novelty_global"] for r in rows if r["novelty_global"] is not None]
        out.append({
            "end_index": end,
            "within_school_diversity": mean(within) if within else None,
            "inter_school_min": min(inter) if inter else None,
            "top_school_share": share,
            "novelty_median": median(novelty) if novelty else None,
            "n_schools_active": len(by_school),
        })
    return out


def survivorship(harness, embedder) -> dict:
    """Does adjudication narrow the basin? Compare the diversity of ALL
    conjectures vs the ACCEPTED subset (mean pairwise distance)."""
    conjs = _conjectures(harness)
    vecs = {a.id: harness.embed_artifact(embedder, a.id) for a in conjs}

    def _div(ids: list[str]) -> float | None:
        if len(ids) < 2:
            return None
        ds = [distance(vecs[a], vecs[b])
              for i, a in enumerate(ids) for b in ids[i + 1:]]
        return sum(ds) / len(ds)

    all_ids = [a.id for a in conjs]
    acc_ids = [a.id for a in conjs
               if harness.state.status.get(a.id) == Status.ACCEPTED]
    return {"n_all": len(all_ids), "n_accepted": len(acc_ids),
            "diversity_all": _div(all_ids), "diversity_accepted": _div(acc_ids)}


def embedder_calibration(harness, embedder, cap: int = 400) -> dict:
    """Reference distance scales for THIS corpus: within-problem pairs vs
    cross-problem pairs. If the two distributions overlap heavily, the
    embedder cannot see topical convergence and any threshold (e.g.
    RESEED_DIST_MIN) is uninterpretable on its scale."""
    conjs = _conjectures(harness)[:cap]
    by_problem: dict[str, list] = {}
    addr = {}
    for a, p in harness.state.addr:
        addr.setdefault(a, p)
    for a in conjs:
        pid = addr.get(a.id)
        if pid:
            by_problem.setdefault(pid, []).append(
                harness.embed_artifact(embedder, a.id))
    within, cross = [], []
    pids = sorted(by_problem)
    for i, p in enumerate(pids):
        vs = by_problem[p]
        within += [distance(vs[i2], vs[j]) for i2 in range(len(vs))
                   for j in range(i2 + 1, len(vs))][:cap]
        for q in pids[i + 1:]:
            cross += [distance(u, v) for u in vs[:8] for v in by_problem[q][:8]]

    def _stats(xs):
        if not xs:
            return None
        xs = sorted(xs)
        return {"n": len(xs), "p10": xs[len(xs) // 10], "median": xs[len(xs) // 2],
                "p90": xs[(len(xs) * 9) // 10]}

    return {"within_problem": _stats(within), "cross_problem": _stats(cross)}


def basin_onset(series: list[dict], w: int = 8, floor_frac: float = 0.5) -> dict:
    """WHEN: first conjecture index where rolling-median novelty falls
    below floor_frac x the early-run baseline and never recovers. Returns
    the onset index, the baseline, and the floor actually used."""
    nov = [r["novelty_global"] for r in series if r["novelty_global"] is not None]
    if len(nov) < 2 * w:
        return {"onset_index": None, "reason": f"only {len(nov)} conjectures"}
    baseline = median(nov[:w])
    floor = baseline * floor_frac
    rolling = [median(nov[i:i + w]) for i in range(len(nov) - w + 1)]
    onset = None
    for i, m in enumerate(rolling):
        if m < floor:
            if all(r < baseline for r in rolling[i:]):
                onset = i + w  # index of the last conjecture in the window
                break
    half = len(nov) // 2
    return {"onset_index": onset, "baseline_novelty": round(baseline, 4),
            "floor": round(floor, 4), "final_rolling_median": round(rolling[-1], 4),
            # Basin depth as a continuous quantity: late-run novelty as a
            # fraction of early-run novelty (1.0 = no pull, 0 = collapsed).
            "late_over_early": round(mean(nov[half:]) / mean(nov[:half]), 3)
                               if mean(nov[:half]) else None,
            "n_conjectures": len(nov)}
