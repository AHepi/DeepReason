# VERIFY — PASS on both of the operator's sentences

Verified 2026-09-06 against GOAL.md. No live run: nothing here is decided by a
provider, and everything the criterion asks about is decided offline by the
meter's arithmetic and the scheduler's own reading of a `Config` field.

## R1 — a refused batch no longer ends the run

**PASS.** `proof/repro_before.txt` → `proof/repro_after.txt`, same script:

| | before | after |
|---|---|---|
| refusal with budget REMAINING | `run ended: WorkBudgetDenied` | **`cycle continued`** |
| refusal on a SPENT ceiling | `run ended: WorkBudgetDenied` | `run ended: WorkBudgetDenied` |
| `Config` carries the knob | `False` | `True` |

The second row is the boundary, and it holding is as much the result as the
first row changing.

Pinned by `tests/test_criticism_budget_denial_policy.py`:
`::test_a_refusal_with_budget_remaining_leaves_the_cycle_alive`, and
`::test_the_record_says_what_the_token_budget_cut`, which reads the
`criticism.dispatch.v1` declaration back off the record and asserts
`cut:token-budget` — so no reader can mistake "nobody attacked it" for "the
critics looked and found nothing".

## The boundary the fix may not cross

**PASS.** `::test_a_spent_ceiling_still_ends_the_pass_under_every_policy` is
parameterised over all three policy values. A refusal on an exhausted budget
leaves the pass under every one of them, so the cycle loop above still turns it
into the clean `budget_exhausted` terminal the operator's law of 2026-08-29
requires. The law is not a configuration option, and mutation M2 proves the
test would notice if it became one.

## R2 — the knob is configuration, and it is LIVE

**PASS, and held to a number rather than a branch.**
`::test_the_knob_changes_what_the_run_spends` drives ONE real `TokenMeter`
through ONE scenario under two settings of the one field. Only the provider
call is stubbed; the reservation, the refusal and the verdict on whether the
ceiling is spent are the meter's own arithmetic.

| `CRITICISM_BUDGET_DENIAL_POLICY` | tokens spent | targets criticised | declared outcome |
|---|---|---|---|
| `drop-the-batch.v1` | **0** | **0** | `cut:token-budget` |
| `shrink-the-batch.v1` | **1 200** | **4** | `complete` |

The batch of four is priced beyond the whole ceiling, so it can never be served
and is correctly NOT exhaustion; halves of two fit. `drop` abandons the work;
`shrink` re-plans the same targets into calls the budget can cover. Same
scenario, same meter, one field — different allocation.

Three further tests make the surface honest rather than nominal:

- `::test_every_value_is_reachable_and_an_unknown_one_never_refuses` — the
  all-configurations law: an unknown id falls back to the default and
  discloses what it fell back from.
- `::test_stop_the_run_keeps_the_old_behaviour_and_warns_about_it` — the
  ungated-seats law: the setting that can kill a run emits a typed warning
  carrying the operator-facing text, once per run.
- `::test_the_scheduler_reads_the_policy_and_hard_codes_no_behaviour` — the
  modularity law's "enforced" clause: the dispatch helper must resolve the
  policy and must contain none of the three literals. It goes red the moment
  a behaviour is written back into the code.

And the knob is reachable from a real run, not only from the scheduler's own
reading: `tests/test_manifest_config_disclosure.py` asserts every dropped
`Config` field round-trips through the managed path's carriage notice, and this
tranche extended it from 30 fields to 31.

## R2 — the knob costs no digest

**PASS, measured.** `proof/digests_before.txt` vs `proof/digests_after.txt`
differ on ONE line — the line that says the field now exists. The manifest's
`source_config_hash` (`76e35e16…`) and its own `sha256` (`de66096f…`) are
byte-identical, so no qualification subject digest moves and no home owes a
~14-minute battery.

Pinned in the gate by `::test_the_field_reaches_no_manifest_and_moves_no_digest`,
which also asserts the `data.pop` sits at FOUR spaces and unconditional — the
`ENGAGED_CRITICISM_AUTHORITY` trap, where an eight-space guard-scoped pop
passed a substring check while the hash had already moved.

## Mutation proof — eight mutations, none vacuous

`proof/mutations.txt`:

| mutation | tests that went red |
|---|---|
| M1: the criticism road stops absorbing the refusal (P1 restored) | four, including both record tests |
| M2: a spent ceiling is absorbed too — the law becomes configurable | the parameterised boundary test, at two settings |
| M3: the policy is ignored — nothing shrinks | the shrink test and the spend measurement |
| M4: the pass stops declaring that money cut it short | the record test and the spend measurement |
| M5: the declaration guesses its targets again | the partly-refused test |
| M6: switching the gate to `stop-the-run` goes silent | the warning test |
| M7: the versioned-source drop is lost | the digest test |
| M8: an unknown policy id refuses instead of falling back | the reachability test |

## Instruments

**Full gate**: **3 failed, 5166 passed, 6 skipped in 19:13.** The three are
`tests/test_organiser_seat.py`, pre-existing on `origin/main` and measured
there in a clean worktree by the predecessor tranche (parked as its P2).
Against the previous boundary run (3 failed, 5153 passed) the count moved by
exactly the 13 tests this tranche adds, and no failure moved.

The honest reading, again: **0 failed attributable to this tranche, and the
gate is not at 0 overall.**

**docs_verify**: **8 failed, all pre-existing.** This change caused FOUR
regressions and they were fixed rather than explained away:

| check | what broke it | how it was repaired |
|---|---|---|
| `SUB-scheduler.md:155` | the signal census reads the LITERAL at a `record_measure` site; the warning's name arrived in a variable | the literal is spelled at the emit site, and `criticism.budget-stop-the-run.v1` is declared in `deepreason/signals.py` like every other signal a run can emit |
| `SEAM-scheduler-x-rules.md` | it pinned the keyword-free local dispatch INSIDE `_arg_crit`; the call moved to the helper | the check follows the CALL rather than the method name, and still asserts the local dispatch carries no keywords — which is what makes "the rule reads the config" true by construction |
| `SEAM-scheduler-x-workflow.md:299` | it pinned two absorbing arms; there are three | updated to three, with the new arm's shape pinned too |
| `SEAM-scheduler-x-workflow.md:399` | it pinned the ordering of `_arg_crit`'s exits through the moved call | repointed through the helper |

A fifth attempt failed for a reason worth recording: the repaired
`SEAM-scheduler-x-rules` check carried an apostrophe inside a single-quoted
`python -c`, which `/bin/sh` rejected with a syntax error — a check that fails
for a shell reason looks exactly like a claim that rotted. The message was
rewritten without the apostrophe.

**Ring**, while iterating: 171 passed across the criticism, budget, scheduler,
evidence-state, config-disclosure and qualification files.

**Lint**: `ruff` clean on both new files; unchanged counts elsewhere.

## What this does NOT show

- Nothing about a live run. The shrink road has never been exercised against a
  provider, so what a re-planned batch COSTS in practice — and whether smaller
  batches criticise as well as one large one — is unmeasured. The claim proved
  here is narrower: the knob changes where the tokens go.
- Nothing about the other four roads. Conjecture, the bridge, scratch
  authoring and the referee still handle a budget refusal their own way; this
  field is named for criticism because it governs criticism only. Parked.
- It does not show `shrink` is the right default. It is defended by an
  argument — more work from money already spent, and it subsumes `drop` — not
  by a measurement of run quality, and the operator can move it with one field.
- The gate is not at 0 failed, for a reason that predates this branch.

## Verdict

**PASS.** Both of the operator's sentences are proven by committed,
mutation-proven tests; the map moved in the same commits as the code, with
`Traps`-level entries in three documents; the one frozen-surface contact took
the documented recipe and cost no digest, measured.
