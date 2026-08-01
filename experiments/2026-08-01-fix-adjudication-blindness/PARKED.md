# Parked

One line each. Noticed during this tranche, not worked in it. Sources:
`experiments/live_jolt_2026-07-31/INVESTIGATION.md`.

- `run-status.json` reports `accepted`/`refuted`/`suspended` as pydantic
  defaults the terminal emit never populates (`application/text_runs.py:1095-1108`),
  so the file contradicts its own `display_status_counts` — this is what caused
  the run's outcome to be misreported to the operator.
- `run-stop.json` writes a fresh `StopMetrics` rather than measurements
  (`text_runs.py:1031-1032`); `queued_criticism` has no writer anywhere in `src/`.
- `budget_exhausted` is a fall-through label applied when the scheduler returned
  no stop reason (`text_runs.py:1022-1027`), not a measured cause.
- Text workloads hard-return `TrialAuthority.OBSERVE_ONLY` (`authority.py:97-101`)
  pending a calibration-receipt verifier that does not exist, so no text run can
  mint a warrant or attack anything.
- The ritual detector cannot fire in the zero-attack case that
  `docs/harness-spec-v1.3.md:446` names as the pathology: two of its four
  conditions sit behind `MIN_ATTACKS_FOR_RITUAL=5` and `attack_target_entropy`
  is `None` with no attacks.
- `run-result.json` reported `epistemic_checks_passed: true` for a run that
  could not falsify anything.
- The supported v6 text launch path cannot seed a failable criterion:
  `preparation.py` hardcodes `criteria=()` at five sites and `spec_from_text`
  supplies none. Needs an operator design decision, not a fix.
- 11 of 42 roots under `experiments/` cannot be opened by the current `Harness`
  (`UnsupportedRunManifestVersionError`, all pre-v6). CLAUDE.md says old roots
  stay valid; whether these are deliberately retired is unestablished.
- The simulation contract says "math is available and nothing else may be
  imported", which glm-5.2 read as permission to `import math`; the AST guard
  refuses it and denied the run's only simulation as `invalid_model_program`.

Added this tranche:

- Emit a typed record at SEEDING time when the registered commitment set
  contains no commitment capable of returning FAIL. Capability-gap, own
  tranche. This is the one that would have told the operator at cycle 0 what
  took a 14-agent investigation to establish.
- `state.attacks` does not exist (the attribute is `state.att`), so any probe
  written as `getattr(state, "attacks", {})` silently reports zero for every
  root. Not a product defect, but it produced a false corpus-wide claim this
  session and would do so again.
- `adjudication_ritual` cannot fire when blindness is TOTAL: two of its four
  conditions are gated behind `MIN_ATTACKS_FOR_RITUAL=5` and a third
  (`attack_target_entropy`) is `None` with no attacks, so the worse the run the
  fewer conditions trip. Real, measured, and separate from the flag this
  tranche adds.
- `lineage_stagnation` is already `True` on a real fixture today and reaches
  nothing. This tranche routes only `adjudication_blind` to the epistemic
  channel; the other four flags stay discarded.
- `invariants.py:4040-4048` still calls `raw_flags` purely as a totality check
  and discards it. Left deliberately, so the finding is not emitted twice.
