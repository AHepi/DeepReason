# Parked — found while diagnosing the managed path's host-owned overrides, not worked here

## P4 — `config.apply_overrides` reports every field as explicitly set

**What.** `config.apply_overrides` rebuilds the configuration with
`Config.model_validate(config.model_dump(...))`, so its result reports all 106
fields as explicitly set (`c.model_fields_set` has 106 entries after a
one-field override; measured). Any code asking "did the operator state this?"
gets `yes` for everything. It has NO caller in `src/` today — only
`tests/test_config.py`, `tests/test_imports.py` and
`tests/test_manifest_integration.py` — so nothing in the shipped CLI is wrong
because of it, and this tranche's fix is safe. It becomes a live defect the
moment a `--set KEY=VALUE` road reaches preparation, which is a natural next
step under the maximum-configurable-surface law.

```
Route: dr-change-orchestrator if a `--set` road is wanted, dr-orchestrator
(defect) if one already exists by the time this is picked up.
Goal: make `apply_overrides` preserve the explicitly-stated set — the union of
the input configuration's own stated fields and the top-level keys the call
overrides — so "the operator stated this" survives a command-line override the
way it survives a YAML file.
Evidence: src/deepreason/config.py:853-896 (the rebuild);
src/deepreason/config.py:823-834 (`load`, which DOES preserve it);
experiments/2026-09-10-defect-managed-path-host-owned-overrides/DIAGNOSIS.md,
"Second, independent finding"; the fix in this tranche reads
`model_fields_set` on the loaded configuration and would silently widen if
apply_overrides ever fed it.
End state: `apply_overrides(Config(), {"SCOPE_MAX_NODES": 41}).model_fields_set
== {"SCOPE_MAX_NODES"}`, with a test that fails on the current implementation.
```

## P5 — six of the seven stay disclosure-only, and one of them is a real capability gap

**What.** This tranche carries `EMBEDDER_MODEL` and DISCLOSES the other six.
Disclosure closes the silence, which is what the 2026-08-28 law requires, but
it does not make `engine_profile`, `scratchpad`, `bridge` or
`CHANNELS_DISABLED` reachable from a managed run's configuration — and unlike
`roles` and `model_profile`, none of those four is the endpoint-redirection
boundary the override exists to hold. Whether the managed preset should be a
STARTING POINT the operator's configuration refines, rather than a value that
wins, is a design question the modularity law (2026-08-26) and the
ungated-seats law (2026-08-28) both bear on, and it is the operator's to
decide.

```
Route: dr-change-orchestrator (the operator suggests a change), not the defect
family — after this tranche nothing is silent, so nothing is broken against a
documented guarantee; four settings are simply unreachable from the managed
door.
Goal: decide, per value, whether the managed preset is a default the
operator's configuration may refine or a value the host keeps. `roles` and
`model_profile` are the security boundary and should stay host-owned; the
question is the other four.
Evidence: src/deepreason/preparation.py, the `owned` dict and its stated
reason; experiments/2026-09-10-defect-managed-path-host-owned-overrides/
probe/seven_values.out (all seven, before the fix) and VERIFY.md (the four
that remain disclosure-only after it); docs/map/CON-seats.md, which already
names the seven; the price of carrying each is one qualification battery per
home for any value in the engine-config echo.
End state: an operator ruling ledgered in CLAUDE.md, and either a change
tranche per value or a note in CON-seats.md recording that the four stay
host-owned by decision rather than by accident.
```

## P6 — the sealed managed roots' distance readings are on the hashing scale

**What.** All 63 committed managed roots compiled `deterministic_hashing`
(`probe/census.out`). Every embedding-distance reading any of them carries —
the brief-variation step-1 M2 and novelty numbers among them — is on that
scale. Nothing in this tranche changes them and nothing may: a committed
root's contents are never edited. This restates P2 of the 2026-09-09 tranche
with the census behind it, and VERIFY.md says which committed measurements
this tranche changes the reading of.

```
Route: none needed unless the operator wants a managed number on the neural
scale, in which case it is a new live tranche with its own pre-registration.
Goal: if wanted — re-run a chosen managed arm on a configuration that now
carries the neural embedder and compare against the sealed hashing readings.
Evidence: probe/census.out; experiments/2026-09-04-experiment-brief-variation-
step1/RESULTS.md §5 item 4 (the fallback was held CONSTANT across arms, so the
between-arm comparison is unaffected); the noise-floor finding (d_noise =
1.312 of 15) — read it first, because a scale change may not be the binding
limit.
End state: either a decision that the sealed readings stand, or a new live
tranche.
```
