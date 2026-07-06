"""Response ladder (spec §11.4) — logged scheduler rules with hysteresis;
attention only, never status. Policy is FIXED in v1 (a learned controller
is a meta-attractor risk, §17). Every intervention is logged as a Measure
event with its trigger, so escape efficacy is measured, not vibes.
"""

from deepreason.capture import detection, schools
from deepreason.ontology import SpawnTrigger, Status
from deepreason.rules.crit import crit_program
from deepreason.rules.spawn import spawn


def respond(scheduler, active_flags: dict[str, bool]) -> list[str]:
    harness, config = scheduler.harness, scheduler.config
    applied: list[str] = []

    if active_flags.get("lineage_stagnation"):
        scheduler.activate_interventions([
            "recruit_all",     # fan-out recruitment (§11.2.4)
            "tail_weighted",   # VS tail-weighted selection (§11.6)
            "complement",      # complement directives in packs
            "spec_injection",  # Level-2 spec injection (llm/specs.py)
        ])
        harness.record_measure(inputs=["intervention:stagnation-recruit"])
        applied.append("stagnation-recruit")

    if active_flags.get("school_convergence"):
        current = schools.roster(harness)
        novelty = detection.school_novelty(harness, scheduler.embedder, config.CAPTURE_W)
        laggard = min(
            sorted(current),
            key=lambda s: (novelty.get(s, -1.0), s),  # deterministic tiebreak
        )
        new_policy = schools.reseed(
            harness, laggard, current[laggard], reason="school-convergence"
        )
        # Refresh the live roster the scheduler renders packs from — otherwise
        # the reseed is a logged no-op: _school_dict keeps serving the old
        # stance and the flag just re-fires each cooldown.
        scheduler.schools[laggard] = new_policy
        applied.append(f"reseed:{laggard}")

    if active_flags.get("adjudication_ritual"):
        # Criticism-debt sweep: evaluate never-evaluated commitments.
        for aid, status in list(harness.state.status.items()):
            if status == Status.ACCEPTED and harness.state.artifacts[aid].interface.commitments:
                crit_program(harness, aid)
        spawn(
            harness,
            SpawnTrigger.AUDIT_CRITIC,
            [],
            "audit the critic: adjudication-ritual flags sustained (§11.3)",
            problem_id="audit:ritual",
        )
        harness.record_measure(inputs=["intervention:debt-sweep"])
        applied.append("debt-sweep")

    if active_flags.get("attractor_orbiting"):
        # Basin study (docs/BASIN_REPORT.md): hard circling = the generator
        # re-proposing battery-equivalents of a refuted artifact, measured
        # at 4.3x token cost per registered conjecture. The measured
        # antidote is stance rotation — reseed the school that owns the
        # refuted attractor (fast decay beat permanence on both novelty
        # and separation). Without schools, fall back to tail-weighted
        # selection + spec injection so SOMETHING rotates the proposal
        # distribution; attention only, never status.
        current = schools.roster(harness)
        target = detection.orbit_attractor_school(harness, config.CAPTURE_W)
        if current:
            if target not in current:
                novelty = detection.school_novelty(
                    harness, scheduler.embedder, config.CAPTURE_W)
                target = min(sorted(current),
                             key=lambda s: (novelty.get(s, -1.0), s))
            new_policy = schools.reseed(
                harness, target, current[target], reason="attractor-orbiting")
            scheduler.schools[target] = new_policy
            applied.append(f"orbit-reseed:{target}")
        else:
            scheduler.activate_interventions(["tail_weighted", "spec_injection"])
            harness.record_measure(inputs=["intervention:orbit-rotate"])
            applied.append("orbit-rotate")

    if active_flags.get("grounding_decay"):
        # Exogenous brake: research machinery is P4; the intervention and the
        # priority raise are logged now so the ladder is complete and audited.
        scheduler.activate_interventions(["research_priority"])
        harness.record_measure(inputs=["intervention:exogenous-brake"])
        applied.append("exogenous-brake")
    return applied
