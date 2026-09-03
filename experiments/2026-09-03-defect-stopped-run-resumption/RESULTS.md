# Stopped-run resumption — results

Honest-ledger segments. What the record shows, and the residue: what remains
unproven. Accepted does not mean true.

---

## 2026-09-03 — Segment 1: three terminal shapes, one defect, fixed

**What was observed.** Three committed roots refused `deepreason continue`
while their own records reported nothing wrong with them:

| root | shape | refusal |
|---|---|---|
| `4565139800f5ca020e2b74acff45355c1277a9d510068a8e8b4ed65813f1a49c` | FAILED terminal (P-A1, cycle 5, 1 093 086 of 3 000 000 tokens spent) | `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL` |
| `63e48f57415d05323b608a84f138ee5c22c274d7d8ebccc2e219b613d7c3a722` | KILLED mid-work, then `finalize` (P-A2 epoch 4) | `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`, 10 items |
| `run-fe00609058e10605590206d51ab2b7a0` | CLEAN four-cycle completion, exit 0, 47 admitted conjectures | same, 6 items |

`deepreason stop-report` section 4 ruled ALL FOUR boxes out on the clean roots
in the instrument's own words — "the run reached a clean terminal ...; there is
no failure to attribute" — and section 5 reported `verify_root` violations: 0
on every root. A run with nothing wrong with it, and nothing to attribute,
could not be picked up again.

**What the record showed.** One predicate, `workflow/lifecycle.py:236`:

    if snapshot.outstanding_work or snapshot.unconsumed_bound_call_seqs:
        raise UnfinishedWorkflowAuthorityError(snapshot)

Only the second disjunct is a safety property. An unconsumed bound call is a
provider result nobody has read, so closing a stop over one forces a resume to
re-issue the call — two calls recorded for one authority — or to drop a result
the record already holds. The first disjunct is work in progress.

The census settled which one was firing, and it was not close.
`proof/outstanding_census.py`, over four committed roots, and
`proof/three_shapes.py`, over three stub roots driven to the three shapes:

    outstanding work items:   6, 10, 2, 6   and   31, 3, 11
    unconsumed provider calls: 0,  0, 0, 0   and    0, 0,  0

**Zero, everywhere.** The refusal has never once fired for the reason it
exists. And 23 of the 24 outstanding items across the committed roots were
`outcome=provider_result, admissions=[], terminal=None` — precisely the
selection predicate of `Scheduler._recover_workflow_prefixes`, which runs
before the first cycle of every scheduler including a resumed one, admits each
pending result, and then asserts its own completeness. The receipt was withheld
for a condition whose designated remedy is the operation the withheld receipt
blocks.

Shapes 2 and 3 were proven ONE code path rather than two that resemble each
other: `finalize_stopped_root` calls `terminalize_text_run`, which is what the
ordinary clean stop calls. Shape 1 was the same missing receipt taken by
declaration instead of by predicate. No split was proposed.

**What was fixed.** The predicate narrows to
`snapshot.unconsumed_bound_call_seqs` at FIVE sites at once — build and apply,
STOPPED and RESUMED — because a receipt granted by one and refused by another
produces a root that terminates and then refuses one layer later. The failure
terminal now calls the same `_record_lifecycle_stop` the clean path calls,
carrying `operational_failure` into its own receipt rather than borrowing a
clean reason to buy continuability; `RESUMABLE_STOP_REASONS` admits it. A
sibling `COMPOSABLE_STOP_REASONS` holds the OLD value for the bridge's
post-terminal composition, so widening resumption did not silently widen what
may be composed from a failed terminal. `finalize` emits a progress record, so
a finalized root stops reporting `running`.

**What the record now shows.** The same script, before and after:

| shape | before | after |
|---|---|---|
| clean | `continue rc=1 CONTINUE_TYPED_STOP_REQUIRED`, cycle 8 → 8 | `rc=0`, cycle **8 → 10** |
| failed | `rc=1`, cycle 1 → 1 | `rc=0`, cycle **1 → 3** |
| killed | `rc=1`, state stuck at `running`, cycle 2 → 2 | `rc=0`, state `completed`, cycle **3 → 5** |

And the control, unchanged character for character: one byte of `log.jsonl`
altered, and `continue` refuses `CONTINUE_RECORD_NOT_VERIFIED: ...
attempt-route, frozen-route`. That pairing is the operator's law in both its
halves — a run whose record verifies resumes, a run whose record was tampered
with does not — and it is why nothing in `runtime/continuation.py` moved.

Full gate 4720 passed, 0 failed. `diff_budget` verdict WITHIN (149 of 150).
Committed roots re-derived on copies: no verdict moved, by class or by count.

**Residue — what this segment does NOT show.**

1. **One sub-shape is unproven end to end.** P-A2 epoch 4 carries a CRITICISM
   work order ISSUED with no provider attempt. It correctly no longer vetoes
   the receipt, but `recover_incomplete()` cannot close it either, so a resume
   on such a root would reach
   `RuntimeError("transaction recovery left unfinished authority")`. The stub
   cannot produce that sub-shape — every stub item is result-bearing — so it is
   covered at unit level only. Parked as P5 with its three roads priced. **A
   killed run is resumable in the shape measured here; it is not proven
   resumable in every shape a kill can produce.**
2. **The practical stake is relieved, not measured.** P-A2's F8 priced the
   problem at ~9 h for a 24-cycle run against ~2 h container restarts. That
   resumption now works offline across three shapes makes carrying a long live
   run across restarts plausible; **no live run has been carried across a
   restart**, and this tranche attempted none. The first long live run is the
   test.
3. **Old roots gained nothing.** The 16 committed roots, P-A1 and P-A2 are not
   rewritten and still refuse — correctly, since their logs contain no receipt
   and nothing may write one into a committed root. They are now the witness
   set for `CONTINUE_TYPED_STOP_REQUIRED`.
4. **Exposure to a known residue is wider.** Roads closed for lifecycle reasons
   now reach the SECURITY gate, which becomes their sole guard. The residue
   (`experiments/2026-08-31-defect-jailbreak-gate-closure/` P2, a record too
   corrupt to replay passing the gate) is unchanged in size; more traffic meets
   it. Declared in FIX.md before the first edit, parked as P3.
5. **Two instruments disagree about P-A2 epoch 4** — `stop-report` says 0
   violations, `verify_root` and `REPLAY_VALIDATION.json` say 1
   (`foreign-criticism`). Immaterial to this verdict under either reading, but
   `stop-report` is what `dr-diagnose` gates on. Parked as P6.

**What this tranche corrected in a committed document.** `docs/ERRATA.md` E61:
"failure terminals stay non-resumable" was a design decision the operator
reversed on 2026-08-29, and three committed documents plus one gate test still
stated it as settled — the test as a *guarantee* ("this terminal really cannot
be continued") rather than as the half-measure its own tranche said in writing
it was. The generalisable lesson recorded there: when a tranche knowingly ships
half of a law, its tests should assert the half it shipped, not the half it
did not.
