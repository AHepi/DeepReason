"""P6 eval report (spec §16 P6) — a deterministic function of (log, state).

Reports: valid-JSON rate per role, attack-validity rate, survivor HV/reach
distributions, trial-guard survival, paraphrase-flip and planted-flaw and
bias measures, per-school novelty contribution, and escape efficacy per
response rule (stream diversity before vs after each logged intervention).

Honest limits: cycles dropped on schema-repair exhaustion never reach the
log (they live in scheduler diagnostics), so the valid-JSON rate here is
conditioned on eventual success; escape efficacy compares the conjecture
stream around the intervention seq and is correlational, not causal.
"""

from deepreason.capture import detection, schools
from deepreason.llm.embedder import HashingEmbedder, distance
from deepreason.ontology import Rule, Status
from deepreason.programs import content_text


def _distribution(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
    }


def _mean_pairwise_texts(texts: list[str], embedder) -> float | None:
    if len(texts) < 2:
        return None
    vectors = [embedder.embed(t) for t in texts]
    dists = [
        distance(vectors[i], vectors[j])
        for i in range(len(vectors))
        for j in range(i + 1, len(vectors))
    ]
    return sum(dists) / len(dists)


def _latest_tagged(events, prefix: str) -> float | None:
    value = None
    for event in events:
        for tag in event.inputs:
            if tag.startswith(prefix):
                try:
                    value = float(tag[len(prefix):])
                except ValueError:
                    pass
    return value


def eval_report(harness, config, embedder=None) -> dict:
    embedder = embedder or HashingEmbedder()
    state = harness.state
    events = list(harness.log.read())
    window = config.CAPTURE_W

    # --- LLM reliability: valid-JSON rate per role (P6) ---------------- #
    per_role: dict[str, dict] = {}
    for event in events:
        if event.llm is None:
            continue
        row = per_role.setdefault(
            event.llm.role, {"calls": 0, "attempts": 0, "total_ms": 0}
        )
        row["calls"] += 1
        row["attempts"] += event.llm.attempts
        row["total_ms"] += event.llm.ms
    for row in per_role.values():
        row["valid_json_rate"] = row["calls"] / row["attempts"] if row["attempts"] else None

    # --- Attack validity: do registered attacks stand? ----------------- #
    attackers = [a for a in state.artifacts.values() if a.warrants]
    standing = sum(
        1 for a in attackers if state.status.get(a.id) == Status.ACCEPTED
    )
    attack_validity = standing / len(attackers) if attackers else None

    # --- Survivor HV / reach ------------------------------------------- #
    addressed = {aid for aid, _ in state.addr}
    survivors = [
        aid for aid in addressed if state.status.get(aid) == Status.ACCEPTED
    ]
    survivor_hv = _distribution([state.hv[a] for a in survivors if a in state.hv])
    survivor_reach = _distribution(
        [state.reach[a] for a in survivors if a in state.reach]
    )

    # --- Trial-guard survival ------------------------------------------ #
    blocked: dict[str, int] = {}
    for event in events:
        for tag in event.inputs:
            if tag.startswith("trial-blocked:"):
                reason = tag[len("trial-blocked:"):]
                blocked[reason] = blocked.get(reason, 0) + 1
    rubric_warrants = sum(
        1
        for w in harness.warrants.values()
        if w.commitment
        and w.commitment in harness.commitments
        and harness.commitments[w.commitment].eval.startswith("rubric:")
    )
    total_blocked = sum(blocked.values())
    trial_survival = (
        rubric_warrants / (rubric_warrants + total_blocked)
        if (rubric_warrants + total_blocked)
        else None
    )

    # --- Audit measures (latest logged values) -------------------------- #
    audit_hits = sum(
        1 for e in events for t in e.inputs if t.startswith("audit-hit:")
    )
    judge_error_rate = _latest_tagged(events, "judge-error-rate:")
    self_preference = _latest_tagged(events, "judge-self-preference:")
    verbosity_bias = _latest_tagged(events, "judge-verbosity-bias:")

    # --- Schools -------------------------------------------------------- #
    roster = schools.roster(harness)
    novelty = detection.school_novelty(harness, embedder, window)
    school_rows = {
        sid: {
            "stance": policy["stance"],
            "lineage": schools.lineage_size(harness, sid),
            "stance_weight": schools.stance_weight(harness, sid, config),
            "novelty_contribution": novelty.get(sid),
        }
        for sid, policy in sorted(roster.items())
    }
    reseeds = sum(1 for e in events if e.rule == Rule.RESEED)

    # --- Escape efficacy per response rule (§11.4: measured, not vibes) - #
    stream = [
        (a.provenance.event_seq, content_text(a, harness.blobs))
        for a in state.artifacts.values()
        if a.provenance.role.value in ("conjecturer", "synthesizer")
    ]
    stream.sort()

    def _stream_dist(seq: int, after: bool) -> float | None:
        if after:
            texts = [t for s, t in stream if s > seq][:window]
        else:
            texts = [t for s, t in stream if s <= seq][-window:]
        return _mean_pairwise_texts(texts, embedder)

    interventions = []
    for event in events:
        for tag in event.inputs:
            if not tag.startswith("intervention:"):
                continue
            before = _stream_dist(event.seq, after=False)
            after = _stream_dist(event.seq, after=True)
            interventions.append(
                {
                    "seq": event.seq,
                    "rule": tag[len("intervention:"):],
                    "stream_dist_before": before,
                    "stream_dist_after": after,
                    "diversity_delta": (
                        after - before if before is not None and after is not None else None
                    ),
                }
            )

    return {
        "totals": {
            "events": len(events),
            "artifacts": len(state.artifacts),
            "problems": len(state.problems),
            "warrants": len(harness.warrants),
            "survivors": len(survivors),
        },
        "llm": per_role,
        "attack_validity_rate": attack_validity,
        "survivor_hv": survivor_hv,
        "survivor_reach": survivor_reach,
        "trial_guard": {
            "rubric_warrants": rubric_warrants,
            "blocked": blocked,
            "survival_rate": trial_survival,
        },
        "audits": {
            "hits": audit_hits,
            "planted_flaw_error_rate": judge_error_rate,
            "self_preference": self_preference,
            "verbosity_bias": verbosity_bias,
        },
        "schools": {"roster": school_rows, "reseeds": reseeds},
        "interventions": interventions,
        "capture": {
            "generator": detection.generator_metrics(harness, embedder, window),
            "adjudicator": detection.adjudicator_metrics(harness, window),
            "lambda": detection.grounding_lambda(harness, window),
        },
    }
