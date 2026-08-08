# Reproduction

Two forms, both confirming DIAGNOSIS.md's mechanism exactly, neither
touching a live provider or the committed fixture's own bytes.

## Form 1: record replay

Artifact: `experiments/2026-08-08-fix-l1-continue-resumable-crash/
repro_fixture_replay.py <scratch-copy-of-fixture>`

Reproduces the crash by invoking `Scheduler.run(0)` directly (its own
first action, `_recover_workflow_prefixes`, is what crashes on
`deepreason continue` in production) against a throwaway copy of the
committed fixture root, with a mock provider endpoint that raises if
ever called (proving recovery never redispatches). No credentials, no
network, no CLI service layer (which requires `OLLAMA_API_KEY` even
for the recovery-only path, since it bootstraps a full live provider
adapter before ever reaching recovery — this script bypasses that
bootstrap, not the mechanism under test).

Setup:
```
cp -r experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949 /tmp/scratch-copy
python3 experiments/2026-08-08-fix-l1-continue-resumable-crash/repro_fixture_replay.py /tmp/scratch-copy
```

Current output:
```
CRASHED as predicted: NonConjectureRecoveryAuthorityError: unknown critic task
```

Confirms diagnosis: yes — identical error type and message to the
fixture's own `run-status.json` (`"message":"unknown critic task"`),
reproduced from TODAY's code against the frozen record, with no live
run and no code changed. `git status --porcelain
experiments/2026-08-08-live-two-seat-ab-s6/` stays empty after every
run — the original committed fixture is never touched, only its
throwaway copy.

Post-fix expectation: the same command against a fresh scratch copy
either (a) prints something other than a crash (recovery completes,
`Scheduler.run(0)` returns normally) if FIX.md chooses resume-and-
continue semantics, or (b) still raises, but a NEW, single, typed,
actionable error distinct from `NonConjectureRecoveryAuthorityError`
if FIX.md chooses refuse-typed semantics — never the current bare
`NonConjectureRecoveryAuthorityError("unknown critic task")`, and
never a second, different crash class.

## Form 2: offline unit reproduction

Artifact: `experiments/2026-08-08-fix-l1-continue-resumable-crash/
repro_synthetic_atomic_child.py`

Builds a minimal synthetic root from scratch, through the harness's
own real construction seams (no live provider, no hand-forged
records): a schema-exhausted BATCH criticism source item, a genuine
`activate_contract_decomposition` transition (the harness's own
write-time replay validator refuses an atomic-child preparation
without one — confirmed live while building this artifact, see
below), one atomic child shaped exactly as `rules/crit.py`'s own
`execute_atomic_transition` builds it (`contract_id=
"critic.atomic-target.v1"`, payload `schema=
"contract-decomposition-child.v1"`) — admitted and terminalized, i.e.
ALREADY fully resolved, no pending work anywhere in the root. Reuses
`tests/test_v6_nonconjecture_recovery.py`'s own
`_manifest`/`_config`/`_lease`/`_provider_prefix` helpers (dr-reproduce's
"do not invent new scaffolding when a helper exists" rule) rather than
hand-rolling manifest/config construction.

Current output:
```
CRASHED as predicted: NonConjectureRecoveryAuthorityError: unknown critic task
```

Confirms diagnosis: yes — isolates the mechanism to exactly one
admitted, already-completed criticism atomic child and nothing else;
no pending work, no live provider, no batch-level incompleteness.
This DIRECTLY falsifies the narrower reading of P3's own hypothesis
("must still be in flight") that DIAGNOSIS.md's "Ruled out" section
already flagged from the static record alone — this artifact proves
it a second, independent way, by construction rather than
observation.

**A finding surfaced while building this artifact, recorded here
rather than left implicit:** `activate_contract_decomposition`'s own
write-time validator (`harness.py`, invoked through
`workflow/replay.py::_validate_preparation_decomposition_authority`)
DOES require a real decomposition transition to exist before it will
accept an atomic child's preparation — an earlier, simpler draft of
this script tried to construct the atomic child directly, without a
matching `activate_contract_decomposition` call, and was correctly
refused with `WellFormednessError("atomic child preparation lacks
prior exact decomposition")`. This confirms the crash mechanism lives
purely in the SWEEP/DISPATCH layer (`scheduler.py`'s
`_recover_workflow_prefixes`, `nonconjecture_recovery.py`'s
`_criticism_contract`) — neither of which reads
`contract_decomposition_by_source_work` at all — and not in any gap
in the harness's own write-time authority checks, which are already
correctly strict about atomic-child provenance.

Post-fix expectation: the same script, unmodified, either prints "NO
CRASH -- recovery completed cleanly" (resume-and-continue semantics)
or raises a single, new, typed, actionable error distinct from
`NonConjectureRecoveryAuthorityError` (refuse-typed semantics) —
whichever FIX.md chooses; the assertion `str(error) == "unknown critic
task"` must no longer be the observed behavior either way.

## Production code untouched

```
git status --porcelain src/ tests/
```
(empty — both artifacts live only under this tranche's own directory,
neither imports nor modifies anything under `src/` or `tests/`.)
