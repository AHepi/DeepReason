"""P6 eval report (spec §16 P6) — a deterministic function of (log, state).

Reports: valid-JSON rate per role, attack-validity rate, survivor HV/reach
distributions, trial-guard survival, paraphrase-flip and planted-flaw and
bias measures, per-school novelty contribution, and escape efficacy per
response rule (stream diversity before vs after each logged intervention).

Schema-exhausted and transport-dropped calls are retained as process-only
Measure events with per-attempt traces.  ``valid_json_rate`` remains the
legacy completions metric; the report also exposes first-pass, eventual,
schema-exhausted, and transport-dropped counts separately. Escape efficacy
compares the conjecture stream around an intervention and is correlational,
not causal.
"""

from deepreason.application.models import derive_model_execution_summary
from deepreason.capture import detection, schools
from deepreason.llm.embedder import HashingEmbedder, distance
from deepreason.ontology import Rule, SpawnTrigger, Status
from deepreason.programs import content_text
from deepreason.research.backends import covered
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest, role_matrix


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


def _program_grounding_breakdown(harness) -> dict:
    """Classify recorded verdict warrants without rerunning any evaluator.

    These are diagnostic shares of the warrant-producing verdict stream. They
    do not replace the normative ``grounding_lambda`` or grant evidence credit.
    In particular, structural well-formedness remains visibly separate from
    execution, simulation, formal verification, and observation.
    """

    from deepreason.programs import PROGRAMS

    classes = {
        "structural": 0,
        "execution": 0,
        "simulation": 0,
        "formal": 0,
        "observation": 0,
    }
    rubric = 0
    predicate = 0
    total = 0
    for warrant in harness.warrants.values():
        commitment = harness.commitments.get(warrant.commitment)
        if commitment is None:
            continue
        total += 1
        kind, _, name = commitment.eval.partition(":")
        if kind == "program" and name in PROGRAMS:
            classes[PROGRAMS[name].class_] += 1
        elif kind == "rubric":
            rubric += 1
        elif kind == "predicate":
            predicate += 1
    program_total = sum(classes.values())

    def share(count: int) -> float | None:
        return (count / total) if total else None

    return {
        "verdict_warrants": total,
        "program_warrants": program_total,
        "structural_program_fraction": (
            classes["structural"] / program_total if program_total else None
        ),
        "execution_lambda": share(classes["execution"]),
        "simulation_lambda": share(classes["simulation"]),
        "formal_lambda": share(classes["formal"]),
        "observation_lambda": share(classes["observation"]),
        "rubric_fraction": share(rubric),
        "predicate_fraction": share(predicate),
        "counts": classes,
        "note": "diagnostic verdict shares only; evidence_lambda is reported separately",
    }


def _process_report(harness, events) -> dict:
    """Replay-derived compatibility metrics, isolated from epistemic state.

    A v6 run has one manifest-default profile and may have distinct frozen
    route-seat base profiles. Legacy roots without a manifest are reported as
    ``unprofiled`` rather than guessed from model names or prompt shapes. This
    function reads event transport fields and the persisted run manifest only;
    none of its values feed labels, warrants, or acceptance.
    """

    manifest_path = harness.root / MANIFEST_NAME
    manifest = None
    manifest_error = ""
    if manifest_path.exists():
        try:
            manifest = load_run_manifest(manifest_path)
        except Exception as error:  # noqa: BLE001 - corruption belongs in the report
            manifest_error = f"{type(error).__name__}: {error}"[:400]

    calls = [event.llm for event in events if event.llm is not None]
    profile = manifest.model_profile if manifest is not None else "unprofiled"
    traced_calls = [call for call in calls if call.attempt_trace]
    transport_profiles: dict[str, int] = {}
    contract_counts: dict[str, int] = {}
    compact_recovery_calls = 0
    for call in traced_calls:
        first = call.attempt_trace[0]
        transport = (
            first.transport_profile or first.model_profile or "unprofiled"
        )
        transport_profiles[transport] = transport_profiles.get(transport, 0) + 1
        contract_counts[first.contract_id] = contract_counts.get(first.contract_id, 0) + 1
        compact_recovery_calls += int(
            first.model_profile in {"standard", "frontier"}
            and transport == "compact"
        )
    def call_totals(selected_calls):
        selected_traced = [call for call in selected_calls if call.attempt_trace]
        attempt_distribution: dict[str, int] = {}
        for call in selected_calls:
            key = str(call.attempts)
            attempt_distribution[key] = attempt_distribution.get(key, 0) + 1
        first_pass_valid = sum(
            1 for call in selected_traced if call.attempt_trace[0].valid
        )
        eventual_valid = sum(
            1 for call in selected_traced if any(a.valid for a in call.attempt_trace)
        )
        transport_dropped = sum(
            1
            for call in selected_traced
            if not any(a.valid for a in call.attempt_trace)
            and any(a.usage_unknown for a in call.attempt_trace)
        )
        schema_exhausted = sum(
            1
            for call in selected_traced
            if not any(a.valid for a in call.attempt_trace)
            and not any(a.usage_unknown for a in call.attempt_trace)
        )
        return {
            "calls": len(selected_calls),
            "attempts": sum(max(0, call.attempts) for call in selected_calls),
            "repair_attempts": sum(
                max(0, call.attempts - 1) for call in selected_calls
            ),
            "repaired_calls": sum(
                1 for call in selected_calls if call.attempts > 1
            ),
            "truncated_calls": sum(1 for call in selected_calls if call.truncated),
            "tokens": sum(call.tokens for call in selected_calls),
            "attempt_distribution": dict(sorted(attempt_distribution.items())),
            "traced_calls": len(selected_traced),
            "trace_coverage": (
                len(selected_traced) / len(selected_calls)
                if selected_calls
                else None
            ),
            "first_pass_valid": first_pass_valid,
            "first_pass_valid_rate": (
                first_pass_valid / len(selected_traced) if selected_traced else None
            ),
            "eventual_valid": eventual_valid,
            "eventual_valid_rate": (
                eventual_valid / len(selected_traced) if selected_traced else None
            ),
            "schema_exhausted": schema_exhausted,
            "transport_dropped": transport_dropped,
            "usage_unknown_attempts": sum(
                int(attempt.usage_unknown)
                for call in selected_traced
                for attempt in call.attempt_trace
            ),
            "provider_transport_attempts": sum(
                attempt.transport_attempts
                for call in selected_traced
                for attempt in call.attempt_trace
            ),
        }

    calls_by_profile: dict[str, list] = {}
    for call in calls:
        call_profile = (
            call.attempt_trace[0].model_profile
            if call.attempt_trace
            else profile
        ) or "unprofiled"
        calls_by_profile.setdefault(call_profile, []).append(call)
    if not calls_by_profile:
        calls_by_profile[profile] = []
    profile_totals = {
        key: call_totals(value)
        for key, value in sorted(calls_by_profile.items())
    }
    model_execution = (
        derive_model_execution_summary(harness, manifest).model_dump(
            mode="json", by_alias=True
        )
        if manifest is not None and manifest.schema_version == 6
        else None
    )
    return {
        "manifest_present": manifest_path.exists(),
        "manifest_valid": manifest is not None,
        "manifest_error": manifest_error,
        "manifest_sha256": manifest.sha256 if manifest is not None else None,
        "engine_profile": manifest.engine_profile if manifest is not None else None,
        "model_profile": manifest.model_profile if manifest is not None else None,
        "pack_profile": manifest.pack_profile if manifest is not None else None,
        "output_profile": manifest.output_profile if manifest is not None else None,
        "profile_totals": profile_totals,
        "transport_totals": {
            "profiles": dict(sorted(transport_profiles.items())),
            "contracts": dict(sorted(contract_counts.items())),
            "compact_recovery_calls": compact_recovery_calls,
        },
        "model_execution": model_execution,
        "frozen_routes": role_matrix(manifest) if manifest is not None else [],
        "note": (
            "process/reporting metadata only; excluded from artifacts, warrants, "
            "graph labels, and acceptance"
        ),
    }


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
            event.llm.role,
            {
                "calls": 0,
                "attempts": 0,
                "total_ms": 0,
                "tokens": 0,
                "traced_calls": 0,
                "first_pass_valid": 0,
                "eventual_valid": 0,
                "schema_exhausted": 0,
                "transport_dropped": 0,
                "usage_unknown_attempts": 0,
                "provider_transport_attempts": 0,
                "transport_profiles": {},
                "contract_counts": {},
                "compact_recovery_calls": 0,
            },
        )
        row["calls"] += 1
        row["attempts"] += event.llm.attempts
        row["total_ms"] += event.llm.ms
        row["tokens"] += event.llm.tokens
        total_tokens += event.llm.tokens
        trace = list(event.llm.attempt_trace)
        if trace:
            row["traced_calls"] += 1
            row["first_pass_valid"] += int(trace[0].valid)
            has_valid = any(attempt.valid for attempt in trace)
            has_unknown = any(attempt.usage_unknown for attempt in trace)
            row["eventual_valid"] += int(has_valid)
            row["schema_exhausted"] += int(not has_valid and not has_unknown)
            row["transport_dropped"] += int(not has_valid and has_unknown)
            row["usage_unknown_attempts"] += sum(
                int(attempt.usage_unknown) for attempt in trace
            )
            row["provider_transport_attempts"] += sum(
                attempt.transport_attempts for attempt in trace
            )
            first = trace[0]
            transport = (
                first.transport_profile or first.model_profile or "unprofiled"
            )
            row["transport_profiles"][transport] = (
                row["transport_profiles"].get(transport, 0) + 1
            )
            row["contract_counts"][first.contract_id] = (
                row["contract_counts"].get(first.contract_id, 0) + 1
            )
            row["compact_recovery_calls"] += int(
                first.model_profile in {"standard", "frontier"}
                and transport == "compact"
            )
        if event.llm.mean_surprisal is not None:
            surprisal_sums.setdefault(event.llm.role, []).append(event.llm.mean_surprisal)
    for role, row in per_role.items():
        row["valid_json_rate"] = row["calls"] / row["attempts"] if row["attempts"] else None
        traced = row["traced_calls"]
        row["trace_coverage"] = traced / row["calls"] if row["calls"] else None
        row["first_pass_valid_rate"] = (
            row["first_pass_valid"] / traced if traced else None
        )
        row["eventual_valid_rate"] = (
            row["eventual_valid"] / traced if traced else None
        )
        values = surprisal_sums.get(role)
        row["mean_surprisal"] = sum(values) / len(values) if values else None
        row["transport_profiles"] = dict(sorted(row["transport_profiles"].items()))
        row["contract_counts"] = dict(sorted(row["contract_counts"].items()))

    # --- Attack validity: do registered attacks stand? ----------------- #
    carrier_ids = {carrier for carrier, _ in state.carries}
    attackers = [a for a in state.artifacts.values() if a.id in carrier_ids]
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
        "process": _process_report(harness, events),
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
            "program_grounding": _program_grounding_breakdown(harness),
        },
    }
