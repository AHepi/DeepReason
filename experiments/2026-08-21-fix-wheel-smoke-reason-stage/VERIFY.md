# Verification

Verdict: **PASS**

## Criterion command + output

GOAL.md's success criterion, run verbatim. Every instrument was run ALONE on
an otherwise idle box (`dr-drive-harness` §5b), sequenced by a single driver
so no two fanned out at once.

### 1. The instrument under repair — `python -u scripts/wheel_operational_smoke.py`

    repeat2  rc=0   started 13:24:10, ~25 min
    op3      rc=0   started 14:13:08, ~25 min
    op4      rc=0   started 14:37:57, ~25 min

    wheel operational smoke passed: installed setup, explicit qualification
    (80 qualification calls; 410 total calls), readiness, question-only
    reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP
    restart, budget ceiling, and pre-V6 fail-closed admission

**3 of 3 post-fix runs pass end to end.** The smoke now reaches every stage
past `reason`, including the continuation, restart-recovery, replay-
validation, budget-rejection, second MCP-request, manifest-rejection and
disclosure-check stages it has not reached on this container since
2026-08-15.

### 2. Repeat count on the flakiness question — stated as the goal demanded

| # | When | Tree | Reached the assertion? | Result |
|---|---|---|---|---|
| 1 | 2026-08-16 | changed tree (embedder tranche run 1) | **no** — died at line 3447, `STAGE_MCP_REQUEST` | silent |
| 2 | 2026-08-16 | changed tree (run 2) | yes | FAIL |
| 3 | 2026-08-16 | clean worktree at `d52c739ff` | yes | FAIL |
| 4 | 2026-08-21 | `c7e605553`, `--keep` | yes | FAIL |
| 5 | 2026-08-21 | `c7e605553` (repeat1) | yes | FAIL |
| 6 | 2026-08-21 | fixed tree (repeat2) | yes | PASS |
| 7 | 2026-08-21 | fixed tree (op3) | yes | PASS |
| 8 | 2026-08-21 | fixed tree (op4) | yes | PASS |

**Pre-fix: 4 evaluations, 4 failures. Post-fix: 3 evaluations, 3 passes.**
The stage was never flaky. Observation 1 — the sole basis for the "flaky"
label — never evaluated `_assert_resumable_terminal`; four separate
sub-stages set `stage = STAGE_REASON`, so the failure envelope's
`"stage":"reason"` did not identify which assertion ran. Recorded as
`docs/ERRATA.md` E34.

### 3. Full gate

    $ python -m pytest tests/ -q -n 4
    3755 passed, 6 skipped in 934.76s (0:15:34)          rc=0

**0 failed.** No test was weakened; the five known-flaky MCP-thread tests
did not need isolating on this run.

### 4. Map

    $ python tools/docs_verify.py
    docs_verify [full]: 60 documents, 923 checks, 4 workers
      FAIL CON-run-identity.md:200 / :202 / :204   (shallow-clone git history)
    docs_verify: 3 failed                          <- the recorded baseline

    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)              rc=0

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 60 document(s)   rc=0

Exactly the three pre-existing `CON-run-identity.md` shallow-clone failures
named in `docs/AUDIT_BASELINES.md`, and nothing else. The new
`SUB-verification.md` check is not refused by `--audit` as unfailable, and
was additionally mutation-proved directly: renaming
`_declared_model_phase_deferrals` turns it red.

An intermediate `docs_verify` run reported **4** failed — the fourth was
mine, and it is recorded rather than quietly fixed: the new check named
`test_a_malformed_deferral_marker_is_not_declared_debt`, a test the same
commit's compression pass had folded into the parametrized table. Repaired
in `95814d9e9` to name the table and to grep for the malformed row's own
parameter wiring, so a table that loses that case fails the check instead of
passing over its absence.

### 5. `python scripts/wheel_smoke.py`

    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas   rc=0

No pin moved: the fix touches neither console entry points, nor the MCP tool
set or schema sha, nor the wheel layout.

## Historical roots re-checked

The fix changes an instrument, not a reader of the record, so no committed
root's verdict can move by construction — `scripts/` is not imported by
anything under `src/`. The claim was not left to construction: the reader it
mirrors (`verification/report.py::_deferred_model_phase_findings`) is
untouched, and the full gate includes `tests/test_r0_terminal_verification.py`
and `tests/test_chaos_invariants.py`, which pin the report's channel
classification.

Census taken during diagnosis, recorded because it is the fact that makes the
old assertion's unsatisfiability concrete: of the 90 committed roots carrying
a `verification.summary.v2` block, **zero stopped `converged`**, and the 5
reporting `completion_satisfied: true` all stopped `operational_failure` with
`finding_counts.completion == 0` — they died before any phase could defer.

## Live attempt

None beyond the smokes themselves. GOAL.md demanded no live provider ladder,
and the smoke IS a live end-to-end run against a loopback provider — it built
a wheel, installed it into a fresh venv, qualified it (80 qualification calls)
and drove four real reasoning runs to typed terminals. Judged only on typed
outcomes: process exit status and the smoke's own typed assertions over
`run-result.json`, `REPLAY_VALIDATION.json` and `log.jsonl`.

## What the fix does NOT claim

It does not claim the run's completion debt is harmless, only that it is
DECLARED. `run-e9d4bb16796b8aa4b560c632b33d6500` converged carrying one
deliberately deferred model phase, and the harness said so in its log at seq
34. Accepted does not mean true, and green does not mean debt-free: the
narrowed assertion asserts the debt matches the declaration, and nothing
about whether the deferred phase should have been deferrable at all. That
question is PARKED (P2), not answered.

## Residue (honest)

1. **P1 — `docs/map/` still owns nothing under `scripts/`.** The same defect
   has now occurred twice (2026-08-05, 2026-08-15) and this tranche closed
   only the second instance. The recurrence is recorded in
   `SUB-application.md`'s Traps; the routing gap it names is parked with three
   priced roads and a recommendation, because deciding what the map covers is
   a scoping decision, not a defect fix.
2. **P2 — `_premise_rent_step` skips its free half when the variator is
   seated but uncontracted.** Recorded as a QUESTION, not a finding. This
   tranche did not test it and must not be read as having done so.
3. **Diff budget EXCEEDED — surfaced, and RESOLVED by the operator.** `tools/diff_budget.py` reports
   276 insertions against this tranche's own 150-line estimate (53 of them
   the semantic change; 186 the regression fixture and 14-case mutation
   table; 37 the map entries and baseline line CLAUDE.md requires in the same
   commit). One compression pass removed 28 with no case lost; nothing further
   comes out without removing proof, and no option reaches 150 without
   deleting obligations CLAUDE.md makes mandatory. Surfaced to the operator as
   a STOP rather than absorbed — the recorded failure mode is absorbing it
   (2026-08-05 V1 tranche: 193 insertions against <=150, no stop). Presented
   to the operator with three priced roads; the operator chose to KEEP IT AS
   IS, so no trim and no split were taken. The verdict stays on the record as
   EXCEEDED at 278 — accepted deliberately, not absorbed. The estimate itself
   remains a recorded miss (~145 predicted, 278 actual); see FIX.md's operator
   ruling for the lesson.
4. **Coverage this fix does not add.** The continuation half of the
   `RESUMABLE_STOP_REASONS` contract still has the smoke as its only
   end-to-end witness (`SUB-application.md` Traps, "Still true and NOT
   fixed"). Unchanged by this tranche, restated so it is not assumed closed
   by a green smoke.
5. **One container, one platform.** Every observation above is `linux` on one
   cloud container. The determinism claim rests on the mechanism being
   unconditional in the cycle body, not on the sample size.

## Errata

`docs/ERRATA.md` **E34** — the wheel operational smoke's `reason`-stage
failure was recorded as FLAKY in two committed 2026-08-16 tranches and was
deterministic; the one contrary observation never evaluated the assertion.
Both source artifacts left verbatim per the append-don't-rewrite rule;
nothing either tranche concluded changes.
