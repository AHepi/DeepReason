<!-- tranche: 2026-09-04-defect-dead-seat-retirement -->

# Verification

## Criterion command + output

GOAL.md's success criterion, run verbatim on the pushed tree
(transcript: `proof/verify_green.txt`):

    $ python -m pytest tests/test_dead_seat_retirement.py -q
    15 passed in 37.47s

Its RED transcript before the fix is committed at `proof/repro_red.txt`
(2 failed), and its mutation proofs at `proof/mutation_proofs.txt`.

    $ python -m pytest tests/ -q -n 4
    4976 passed, 6 skipped in 1285.44s (0:21:25)

    $ python tools/docs_verify.py
    docs_verify: 6 failed

**Every one of the six is pre-existing and none is attributable to this
tranche** — measured, not asserted: the same instrument reported **14 failed**
on this tree before the map work, and the eight this change touched are now
green. The six that remain: `SEAM-llm-x-rules.md:54` (an unparseable check
opener), `CON-run-identity.md:211/213/215` (git-history checks against
revisions this container's shallow clone does not carry),
`INV-frozen-surfaces.md:206` (the transport-failure census, a recorded
baseline), `INV-frozen-surfaces.md:876` (a check that reads a branch this
container has not fetched). Each is named in `FIX.md` Amendment 2.

## GOAL.md's seven clauses, each to its test

| clause | test | verdict |
|---|---|---|
| 1. the P-A1 shape reaches a clean terminal on the healthy seat | `test_the_p_a1_shape_runs_on_the_healthy_seat_after_the_dead_one_exhausts` | PASS |
| — and the second road the fixture found | `test_a_dead_seat_does_not_kill_the_run_through_the_atomic_recovery_road` | PASS |
| 2. the retirement is typed, naming seat/endpoint/reason | `test_the_retirement_is_typed_and_names_the_seat_endpoint_and_trigger` | PASS |
| — written once per seat, not once per cycle | `test_the_receipt_is_written_once_per_seat_however_many_cycles_run` | PASS |
| 3. later calls land on seat 0, none on seat 1 | `test_dispatch_moves_to_the_healthy_seat_and_never_returns_to_the_dead_one` | PASS |
| 4. `deepreason results` reports it; typed absence otherwise | `test_deepreason_results_reports_the_retirement_and_a_typed_absence` | PASS |
| 5. all seats dead stops clean, on a reason `continue` accepts | `test_every_seat_dead_stops_clean_on_a_reason_that_permits_continue` | PASS |
| — the terminal writes the record a continuation reads | `test_the_all_dead_stop_writes_the_record_a_continuation_reads` | PASS |
| — and the run carries on when the provider returns | `test_a_recovered_provider_lets_the_stopped_run_carry_on` | PASS |
| 6. the switch is per-run, defaults ON, `off` warns | `test_the_switch_is_per_run_and_off_reproduces_todays_death_with_a_warning` | PASS |
| — an unknown policy falls back and discloses | `test_an_unknown_policy_falls_back_and_discloses_rather_than_refusing` | PASS |
| 7. census row 4 — judge ensemble, predicate NOT relaxed | `test_a_retired_judge_seat_skips_summons_and_does_not_relax_cross_family` | PASS |
| 7. census row 6 — a single-seat role skips, does not raise | `test_a_retired_single_seat_role_skips_its_phase_rather_than_raising` | PASS |
| 7. census row 3 — coverage debt names the uncovered schools | `test_criticism_coverage_debt_names_what_a_retired_critic_left_uncovered` | PASS |
| the design invariant: retirement never renames a seat | `test_retirement_never_changes_a_seat_instance_spelling` | PASS |

## Mutation proofs (`proof/mutation_proofs.txt`)

Each removes one part of the fix and the suite goes red:

| mutation | result |
|---|---|
| `retired_seats()` always returns `{}` | 11 failed, 4 passed |
| the all-dead stop reports `operational_failure` | 3 failed, 12 passed |
| the school loop stops skipping retired schools | 7 failed, 8 passed |
| restored tree | 15 passed |

## Historical roots re-checked

**None re-run, and this is the honest reason rather than an omission.** This
fix changes no reader, no validator, no record format and no digest input; it
changes what a FUTURE run may do. The motivating root
`4565139800f5ca02` was opened READ-ONLY throughout and is byte-unchanged
(`git status experiments/2026-09-01-live-all-modules-p-a1/` is clean). The
2026-08-14 law retires cross-version obligations, and the root sweep was
retired as an instrument by operator ruling 2026-08-22.

Frozen surfaces, measured on the pushed commit rather than asserted:

    $ git diff 643dd8ea1 HEAD --stat -- src/deepreason/qualification.py \
        src/deepreason/harness.py src/deepreason/invariants.py \
        src/deepreason/capabilities/state.py src/deepreason/verification/ \
        src/deepreason/llm/firewall.py
    (no output)

    $ git diff 643dd8ea1 HEAD --stat -- src/deepreason/run_manifest.py
     src/deepreason/run_manifest.py | 7 +++++++
     1 file changed, 7 insertions(+)

Seven insertions, zero deletions: the operator's granted `data.pop` line and
its comment block. Nothing else on any frozen surface moved.

## Live attempt

**None, and it was not skipped for convenience.** The executor instruction
allowed one guarded live check "only if cheap". It is not available: this
container carries no `env` credential file (`ls experiments/*/env` returns
nothing), so a live launch would need the operator's handover first. The
offline proof is the proof, as that instruction states.

What a live run could add, stated so nobody mistakes its absence for coverage:
it would show the retirement firing against a REAL transport wall rather than
a stub that returns invalid output. The mechanism is the same either way — both
triggers read the record, and the transport trigger reuses the derivation that
P-A1's and P-S1's own records already exercised — but "same mechanism" is an
argument, not a measurement.

## Verdict: **PASS** (offline; live not attempted, credentials absent)

## Residue — honest

1. **What CAUSES a seat to exhaust is unchanged.** In P-A1 the seat was
   unreachable, not incapable: 6 transport-failed terminals and 2
   schema-exhausted ones on a seat that had passed qualification 20/20
   first-pass. The ladder still counts a zero-byte transport return as a failed
   attempt, so the record still says "this model cannot satisfy this schema"
   about a model that was never asked. `PARKED.md` P1. This tranche routes
   around an exhausted seat; it does not change what exhausts one.
2. **A retired seat stays retired for the run.** A provider that comes back
   does not get its seat back, because un-retiring needs a liveness probe —
   a provider call spent on a seat the run has decided not to use — and the
   operator has not asked for one. `FIX.md` §7.
3. **The stub exhausts on invalid output, not on a transport wall.** Clause 1
   is proven against a seat whose endpoint returns `not-json`, which walks the
   same ladder to the same typed record. The transport trigger is proven only
   through `provider_health.dead_seats`, whose own derivation was validated
   against both real records by the previous tranche.
4. **The re-aimed map tripwire is coarse.** It can now only fire on the two
   frozen surfaces with no ledgered grant. Stated in the document beside it and
   in `docs/ERRATA.md` E74; what guards a new contact on an already-granted
   file is `tools/blast_radius.py` and the workflow rule that every row it
   prints is disposed in FIX.md before code.
5. **Census rows 3, 4 and 6 are disclosures, not repairs.** A run whose critic
   coverage floor becomes unmeetable, whose judge ensemble loses a seat, or
   whose single-seat role goes dark, carries on with that capability absent and
   says so. Whether an unmeetable coverage floor should itself stop a run is
   not decided here.
6. **`deepreason results` reads receipts, not policy.** A run that stood a seat
   down before this change shipped has no `seat.retired.v1` row, so the block
   prints its typed absence. That is correct — it reports what the run did —
   and it means the block says nothing about historical roots.

## Errata

**`docs/ERRATA.md` E74**, landed in the same commit as this file: two committed
tripwires — one in `docs/map/INV-frozen-surfaces.md`, one in
`tests/test_wire_contract_id_map.py` — asserted a claim about "this tranche"
with only one end of their range pinned, so each turned red on the first
granted contact after its own tranche merged. Both re-aimed, neither relaxed.
