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
from deepreason.ontology import Rule, SpawnTrigger, Status
from deepreason.programs import content_text
from deepreason.research.backends import covered


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
    surprisal_sums: dict[str, list[float]] = {}
    total_tokens = 0
    for event in events:
        if event.llm is None:
            continue
        row = per_role.setdefault(
            event.llm.role, {"calls": 0, "attempts": 0, "total_ms": 0, "tokens": 0}
        )
        row["calls"] += 1
        row["attempts"] += event.llm.attempts
        row["total_ms"] += event.llm.ms
        row["tokens"] += event.llm.tokens
        total_tokens += event.llm.tokens
        if event.llm.mean_surprisal is not None:
            surprisal_sums.setdefault(event.llm.role, []).append(event.llm.mean_surprisal)
    for role, row in per_role.items():
        row["valid_json_rate"] = row["calls"] / row["attempts"] if row["attempts"] else None
        values = surprisal_sums.get(role)
        row["mean_surprisal"] = sum(values) / len(values) if values else None

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
    # Level-2 spec transmission (llm/specs.py): did injected specifications
    # bind? 1.0 = every candidate realized its own spec.
    spec_scores = []
    for event in events:
        for tag in event.inputs:
            if tag.startswith("spec-transmission:"):
                try:
                    spec_scores.append(float(tag[len("spec-transmission:"):]))
                except ValueError:
                    pass
    spec_transmission = _distribution(spec_scores)
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

    # --- Research grounding: uncovered research problems are silently pending #
    # (no backend configured, or no fetch yet). Surfacing the count turns a
    # silent-failure mode (an empirical claim waiting forever on evidence that
    # never arrives) into a visible signal (§12; docs/OPERATOR_DIAGNOSIS.md).
    research_problems = [
        p for p in state.problems.values()
        if p.provenance.trigger == SpawnTrigger.RESEARCH
    ]
    uncovered_research = [p for p in research_problems if not covered(harness, p.id)]

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

    from deepreason.signals import event_signal, family

    signal_counts: dict[str, int] = {}
    for e in events:
        signal = event_signal(e)
        if signal is not None:
            key = family(signal)
            signal_counts[key] = signal_counts.get(key, 0) + 1

    return {
        "totals": {
            "events": len(events),
            "artifacts": len(state.artifacts),
            "problems": len(state.problems),
            "warrants": len(harness.warrants),
            "survivors": len(survivors),
            "llm_tokens": total_tokens,
        },
        # Every measure signal, normalized to its registry family — the log's
        # own table of contents (see src/deepreason/signals.py for meanings).
        "signals": dict(sorted(signal_counts.items())),
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
        "spec_transmission": spec_transmission,
        "schools": {"roster": school_rows, "reseeds": reseeds},
        "interventions": interventions,
        "research": {
            "problems": len(research_problems),
            "uncovered": len(uncovered_research),
            "note": (
                "uncovered research problems have no accepted evidence — configure a "
                "research_backend or they stay scheduled-pending indefinitely (§12)"
            ) if uncovered_research else "",
        },
        "capture": {
            "generator": detection.generator_metrics(harness, embedder, window),
            "adjudicator": detection.adjudicator_metrics(harness, window),
            "lambda": detection.grounding_lambda(harness, window),
            "evidence_lambda": detection.evidence_lambda(harness),
        },
    }
