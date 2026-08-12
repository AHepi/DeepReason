# Parked: follow-on scope from the all-configs-allowed tranche

Not defects — deliberate scope boundaries this tranche's SPEC.md drew and
VALIDATION.md disclosed (see VALIDATION.md's "Known gaps"). Each is a
ready-to-paste prompt for a fresh `dr-change-orchestrator` tranche, not a
promise this session made.

## P1 — convert the remaining CONVERT-SPEC'D denials

> Route through dr-change-orchestrator. REQUEST.md context: the
> 2026-08-12 all-configs-allowed tranche
> (`experiments/2026-08-12-change-all-configs-allowed/`) converted a
> tier-1 subset of compile-time semantic denials to typed compile
> notices (bridge-route requirements, judge-family conflicts,
> seat-binding conflicts, grounded-bridge unresolved-success-safety,
> INTAKE_SEAT_CONFLICT, validate-intake advisory). Its SPEC.md §3
> census table marks ~20 more sites CONVERT-SPEC'D: fully designed
> (conversion rule stated per row) but not implemented. Goal: implement
> as many of the remaining rows as budget allows, in this priority
> order — (a) the V4 school/criticism topology cluster
> (`_validate_v4_control_plane_policy`/`_validate_v4_criticism_policy`,
> ~12 codes) after verifying `capture/schools.py`/`rules/crit.py` fail
> TYPED (not with an untyped crash) under an under-specified topology;
> (b) V5/V6 capability-profile mismatches (resolution: control-plane
> policy wins, notice records the overwrite); (c)
> `preflight_payload`'s `RUBRIC_INPUT_FORBIDDEN`/`SECOND_JUDGE_FAMILY_REQUIRED`
> (needs a signature change — this function currently returns `None`,
> no notice-carrying return value exists on the frozen `RunManifest` it
> receives); (d) the scratch-embedder fallback. End state: each
> conversion ships with its own rewritten pinned test, full gate green
> at the pre-existing baseline, docs_verify clean.

## P2 — schema v6 behavioral-plan compiler gap

> Route through dr-change-orchestrator. The all-configs-allowed
> tranche's SPEC.md §1 "Known gap" and VALIDATION.md's gap #1: a
> grounded-bridge config missing its judge/reviewer route compiles
> clean with a notice at `schema_version` 2 and 3, but the IDENTICAL
> missing-role config still hits an unconverted site,
> `V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED` in
> `_compile_route_seat_behavioral_capability_plan`
> (`src/deepreason/run_manifest.py`), at `schema_version=6` — found by
> actually running the scenario, not from the original census. Goal:
> either convert this site the same way (notice + proceed, verifying
> what downstream actually happens when the v6 behavioral plan is
> missing a contract-to-role assignment), or make an explicit, recorded
> decision that v6's behavioral-plan compilation is exempt from R2 by
> design (with the operator's confirmation) — do not leave it silently
> inconsistent with schema 2/3's behavior.

## P3 — V6 launch kill-switch: confirm or convert

> Route through dr-change-orchestrator (or ask the operator directly
> first — this one genuinely needs a decision, not just implementation
> effort). The all-configs-allowed tranche's SPEC.md §3.5 left
> `require_v6_launch_allowed`'s two `V6_LAUNCH_DISABLED` sources
> (`runtime/launch_policy.py`) as hard errors — an environment-variable
> rollback switch and a central release-policy file that can disable
> ALL v6 launches during an incident. The tranche's own reasoning: this
> reads as an emergency operational valve, not one of the operator's
> named denial categories (family requirements, role conflicts,
> backend-identity gates, ceiling checks, combination restrictions),
> and converting it changes what "compile-time denial abolished" means
> in a way the operator may not have intended. Ask: should this convert
> too, or does the operator want it to stay a hard block regardless of
> "all configurations are allowed"?

## P4 — seat-binding resolutions into compile_notices

> Route through dr-change-orchestrator. SPEC.md §3.3's addendum: the
> three converted seat-binding conflicts (`SEAT_BINDING_ROLE_CONFLICT`,
> `SEAT_BINDING_GROUP_DUPLICATED`, `SCHOOL_SEAT_DUPLICATED`) resolve
> deterministically (R4 satisfied) but record no `CompileNoticeV1`
> anywhere (R3 not yet satisfied for this family) — `deepreason
> setup`'s seat-binding resolution runs before any
> `compile_run_manifest` call. Goal: thread the resolution outcome from
> `seat_bindings.py` through `preparation.py` into a future manifest's
> `compile_notices`, OR land it as a sibling disclosure at `setup` time
> (printed, not silently applied) if wiring it into the manifest proves
> too invasive. Scope this properly with its own SPEC.md before
> implementing — the blast radius through `preparation.py` was not
> measured in the original tranche.
