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

## P7 — three docs_verify rows fail that the recorded baseline does not expect

**What.** `python tools/docs_verify.py` returns 9 failed on this container.
Six match `docs/AUDIT_BASELINES.md`'s expected list exactly. Three do not, and
the tranche base carries all three, so they belong to some commit between the
2026-08-30 re-baselining and now:

- `CON-successor-questions.md:305` and `SEAM-scratch-x-workflow.md:51` both
  assert the same file census `-eq 50`. It reads **51** — measured at HEAD and
  again in a worktree at base `de4d7abd4`, identical. One source file under
  `src/deepreason` gained a mention that puts it in the set, or the set's
  intended membership changed and the two checks were not updated with it.
- `INV-frozen-surfaces.md:1414` runs `tools/record_claims.py` against
  `experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092`,
  which is absent from this checkout. Same environment class as the
  judge-canary row the baseline already lists separately, and it should be
  rowed there rather than left looking like a claim that rotted.

```
Route: dr-audit-orchestrator, dimension docs-drift (the operator asks what is
out of date), or dr-orchestrator (defect) if the census turns out to be
protecting a real boundary that a commit crossed.
Goal: for each of the three rows, say whether the CLAIM moved or the
ENVIRONMENT is missing, and either re-pin the count with the reason it moved
or row the check as container-conditional in docs/AUDIT_BASELINES.md. Name the
51st file and the commit that added it.
Evidence: experiments/2026-09-10-defect-managed-path-host-owned-overrides/
probe/docs_verify.out (the full run); docs/AUDIT_BASELINES.md lines 40-110
(the failure LIST a delta is measured against, and the rule that a delta from
it IS a finding); the census command itself, which is in both failing checks
verbatim. Re-derive with:
  for f in $(grep -rl scratch src/deepreason --include=*.py); do \
    grep -ql workflow "$f" && echo "$f"; done | sort
and diff that against the same list at the 2026-08-30 baseline commit.
End state: either two re-pinned checks with the reason recorded, or a defect
tranche if a consumer crossed a boundary the census exists to hold. Plus one
new container-conditional row in docs/AUDIT_BASELINES.md for the missing run
root, so the next reader is not misled the way this one nearly was.
```
