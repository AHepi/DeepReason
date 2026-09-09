# VERIFY — PASS on both halves of the goal, with one honest residue in the gate

Verified 2026-09-06 against GOAL.md's success criterion. No live run: the
goal's criterion is about how a stop is CLASSIFIED, and the classification is
decided offline by quantities the meter holds. The committed root that
motivated the tranche is evidence and was never touched, relaunched, or
continued.

## The success criterion, both sides

**1. Exhausted → clean.** PASS.

`tests/test_budget_exhausted_classification.py::
test_a_denial_on_a_spent_ceiling_publishes_a_clean_budget_exhausted_stop`
drives `deepreason run --run-manifest` — the one run path — through the real
`ops.run_scheduler`, the real meter, the real adapter and the real
`Scheduler`, replacing only `Scheduler.step` so nothing but the cycle loop's
own exception arm decides the outcome. The published terminal is
`state: completed`, `stop_reason: budget_exhausted`, in both
`run-status.json` and `run-result.json`.

**The checkpoint obligation of the same law, asserted on the new road.** PASS.
`::test_the_clean_budget_stop_leaves_what_a_relaunch_needs` reads what a
relaunch actually needs rather than the stop reason alone: `checkpoint.json`
present and pointing at the stop record's own digest; a typed STOPPED
lifecycle decision in the workflow state carrying `budget_exhausted`; and
`prepare_continuation` accepting a copy of the root. A stop that cannot assure
continuability is the operator's "corrupted stop", so this is asserted, not
assumed.

**2. Not exhausted → unchanged.** PASS.

`::test_a_denial_with_budget_remaining_stays_an_operational_failure` runs the
identical path with a denial the ceiling could still have afforded: the CLI
exits nonzero and the terminal stays `state: failed`,
`stop_reason: operational_failure` — today's behaviour, unmoved.

**The rule that separates them.** Six tests pin it at the meter, including the
observed root's own arithmetic: ceiling 500 000, spend 495 362, seat cap
8 192 → `budget_remaining` 4 638, `budget_booking` 9 192, `budget_exhausted`
True. The edge is pinned on both sides, both fail-closed shapes are covered,
and an error carrying no verdict reads True so no pre-existing raise site is
silently reclassified.

Nine tests, all green.

## Mutation proof — five mutations, none vacuous

`proof/mutations.py`, output at `proof/mutations.txt`:

| mutation | tests that went red |
|---|---|
| M1: the loop's arm no longer names `WorkBudgetDenied` | both exhausted end-to-end tests |
| M2: the guard is removed — every denial reads as spent | the not-exhausted test |
| M3: the rule says every refusal is a spent ceiling | the unservable-booking test and the edge test |
| M4: an unmeasurable refusal reads as spent | the fail-closed test |
| M5: the denial stops carrying the meter's verdict | the carrier test and both exhausted end-to-end tests |

Every piece of the fix has a test that notices its absence.

## Instruments

**Full gate** (`pytest tests/ -q -n 4`, 21:50): **3 failed, 5153 passed,
6 skipped.** The three are `tests/test_organiser_seat.py`, and they are NOT
this tranche's: the same three fail identically on `origin/main` in a clean
worktree (`3 failed, 9 passed`), on a fixture-digest mismatch and two
block-count mismatches in an attached dossier. Nothing in them touches a
budget, a meter, a stop reason or a scheduler arm. Parked as P2 rather than
fixed — the organiser is explicitly out of this window's scope.

The honest reading: **0 failed attributable to this tranche, and the gate is
not at 0 overall.** That is a weaker statement than "the gate is green" and it
is the true one.

**docs_verify**: **8 failed**, down from 9 before the seam-check repair.
Every one reproduces on `origin/main`:

| where | disposition |
|---|---|
| `SEAM-llm-x-rules.md:54` | documented baseline — malformed check, parked P3 |
| `INV-frozen-surfaces.md:206` | documented baseline — the rotted `transport_failure` census |
| `INV-frozen-surfaces.md:876` | documented baseline — a branch this container never fetched |
| `CON-run-identity.md:211`, `:213`, `:215` | documented baseline — shallow clone, all three pass after `--unshallow` |
| `INV-frozen-surfaces.md:1241` | **not in the baseline list**: reads run root `run-36d9a22c…`, which is not committed (`no run-status.json (not a run root)` on `origin/main` too) |
| `INV-seat-section-plugins.md:179` | **not in the baseline list**: runs the same three organiser tests the gate reports |

The last two arrived with the merged organiser tranche, after
`docs/AUDIT_BASELINES.md` was last re-baselined. Recorded here as findings for
whoever holds that file; not fixed, because both belong to the tranche this
window was told to stay out of.

`SEAM-rules-x-workflow.md:350` was MINE and is fixed: it pinned the denial's
raise as a one-line literal, and the raise now spans lines because it carries
the meter's verdict. The check pins both halves instead.

**Ring**, while iterating: 167 passed / 1 skipped across every budget, meter
and token test in the suite; 72 passed across the referee, checkpoint,
lifecycle-parity, policy-preset, stop-policy, text-run and progress files.

**Lint**: `ruff` reports the same count per file before and after, on all four
changed source files; the new test file is clean.

**Frozen surfaces**: `tools/blast_radius.py` returns
`"frozen_surface_verdict": "CLEAR"` over the four changed files with the new
symbol declared. Declaring the generic names `run` and `check` returns eight
`SYMBOL_INDIRECT` rows — the tool's own grep-collision tier — and the
disposal is checkable: no frozen file names `TokenMeter`,
`TokenBudgetExceeded`, `deepreason.llm.budget`, `Scheduler.run` or
`TokenMeter.check`. No grant was needed and none was asked for.

## What this does NOT show

- It does not show the observed root would now stop clean. That root is
  frozen evidence of the version that wrote it; it was not relaunched, and
  under the operator's law of 2026-08-14 it owes the new code nothing. What is
  shown is that a run of the same shape, driven through the same CLI, now
  publishes `budget_exhausted`.
- It does not decide ARM R's disposition under that tranche's PREREG. The
  classification defect is fixed; whether a sealed rule may be re-read after
  the fact is the operator's ruling, and this window did not take it.
- It shows nothing about a denial that arrives from OUTSIDE `Scheduler.run` —
  none exists on the text-run path today (`ops.run_scheduler` calls the loop
  and then only reads the log), but that is an argument from the current call
  graph, not a test.
- The rule is not measured against a live run. It is arithmetic over the
  meter's own numbers, and the observed root's numbers are the only real ones
  it has been applied to.
- The gate is not at 0 failed, for a reason that predates this branch. Someone
  has to fix the organiser tests before the next tranche can read its own gate
  cleanly.

## Verdict

**PASS.** Both halves of GOAL.md's criterion are proven by committed,
mutation-proven regression tests; the map moved in the same commits as the
code, with a `Traps` entry naming
`run-c3f3bf10bc57d63e224a9f1c68bf1057`; no frozen surface was contacted.
