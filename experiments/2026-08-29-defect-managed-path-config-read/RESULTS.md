# RESULTS — the managed path and the operator's configuration (defect P14)

Honest ledger. Dated segments; what the record shows, and the residue.

---

## 2026-08-29 — segment 1: the defect, priced, then fixed

**What was observed.** `deepreason reason --config F` parsed `F` and then
discarded it. `_cmd_reason` built a `RunPreparationRequestV1` with no
configuration field at all, and `preparation._config_for_profile` synthesised a
fresh `Config` from the provider profile with every field at its default except
seven. Consequence, measured rather than argued: 41 committed managed-path run
roots share ONE engine-config echo and carry zero compile notices
(`probe/echo_census.out`). The 2026-08-28 disclosure
(`ENGINE_CONFIG_FIELD_NOT_CARRIED`) could not fire on this path, because the
`Config` handed to the compiler never differed from its defaults in any dropped
field.

**Two things stage 2 measured that changed the fix's shape.**

1. *Carriage alone would have made every committed configuration unrunnable.*
   `deepreason reason` prepares with `qualification_executor=None`, so a subject
   the cache does not hold is a typed REFUSAL, not an automatic battery; and
   `qualification_subject_manifest` had no `config` parameter, so no committed
   command could address a configured subject. On a home that had fully
   qualified, 8 of 8 committed `run-config.yaml` files came back REFUSED
   `QUALIFICATION_NOT_CONFIGURED` (`probe/lifecycle_gap.out`). The `qualify`
   wiring is therefore part of the fix, not an extra — otherwise the tranche
   would have shipped exactly the operations-parity failure the 2026-08-13 law
   was written about.
2. *A flag gated a seat-configuration path and could not be turned on.*
   `reason --school-seat` and `--criticism-seat` were refused
   `SCHOOL_SEATS_DISABLED` for EVERY provider profile, while the shipped help
   text for that flag said the master gate "is still set via `--config`" — the
   file that was never read (`probe/school_seat_deadlock.out`).

**A correction this tranche made to itself.** Stage 1's `STOP.md` recommended
"road A": carry only the 25 fields the manifest echo drops, on the ground that
this bought the law's second limb at almost no qualification cost. Stage 2
measured that road A is incoherent. `config_from_run_manifest` rebuilds a run's
`Config` from `engine_config_json` and nothing else, and a DROPPED field is by
definition absent from `engine_config_json` — so carrying a dropped field cannot
make it reach the run. Road A's "free" fields were free precisely because they
delivered nothing. The real fork was binary (carriage vs disclose-only) and is
stated as such in `FIX.md` §2.

**What was fixed.** Seven additive change sites across two files, 75 insertions
against a 150 ceiling. `RunPreparationRequestV1` gains `config_path`;
`_config_for_profile` gains `base=`, merging the operator's configuration under
the seven values the host owns; `build_preparation_manifest` and
`qualification_subject_manifest` gain `config=`; `prepare` loads the file
(typed `CONFIG_PROFILE_INVALID` for a file that is not a configuration at all)
and admits it into run identity CONDITIONALLY, exactly as `dossier_digest` was
admitted; and both public verbs pass the same global `--config`. Commit
`a82872b38`.

**What the record now shows.** `tests/test_managed_path_config_read.py`:
7 failed + 1 skipped before, 8 passed after. Seven planted mutations, seven
caught red (`proof/mutation_matrix.out`). 683 tests green across every consumer
of every changed symbol, with no fixture edited. `docs_verify` at the stated
batch baseline of 4 failures and no fifth; the P16 frozen-surface tripwire did
not fire; `blast_radius` `CLEAR`. Four map documents moved in the same commit,
each with a new check that goes red if the behaviour regresses.

**Residue — what remains unproven.**

- *What a carried switch DOES inside a running cycle.* Nothing here is live
  evidence. The batch is offline by construction and there is no provider
  credential in the container; every claim is a compile-time or read-time
  property of committed code and committed records. Accepted does not mean true.
- *The second limb (P15).* For the 22 dispatch-site switches the echo drops,
  this tranche delivers DISCLOSURE, not carriage — the law's "never silence",
  not its "at will". Carrying them moves every pinned manifest digest and is
  tranche B2's question.
- *The price is now reachable, not paid.* No home owes anything for this fix; a
  defaults-only configuration compiles byte-identically. A configuration that
  changes what the run does is a different thing to certify and costs one
  battery — which is the architecture speaking, not an implementation flaw
  (`FIX.md` §3 proves no cheaper design exists), and which the product's own
  `--school-seat` help text already declared as normal.
- *The profile-owned override is silent.* All 8 committed configurations set
  `roles`; the profile wins and the run still compiles, but no typed notice
  records the resolution, because emitting one needs frozen surfaces 4 AND 5
  together. Parked (P21) rather than fudged.
- *Three surfaces still address the unconfigured subject*: `deepreason status`
  and the web page (P20), `reason` over MCP (P22).
- *One ERRATA entry is earned and unwritten* (P23): `docs/ERRATA.md` is outside
  this lane's file cone.

---

## 2026-08-29 — the mutation proof was incomplete, and the two holes are now closed

**What the record shows.** An independent adversarial verifier reviewing this
tranche found two guarantees the suite claimed and did not have. Both reproduce
here, on `lane/b1-only` at base `a4f0d3ce2`, with `tests/` untouched.

The central behaviour had NO protection. `return None` as the first statement
of `preparation._load_operator_config` reinstates P14 exactly — `prepare()`
stores `config_path` on the request and then ignores it, which is the defect
this tranche exists to fix. Under that mutation `pytest
tests/test_managed_path_config_read.py tests/test_run_preparation_service.py -q`
gave 23 passed, and the whole blast-radius ring gave 217 passed, 1 skipped —
byte-identical to the clean run. The cause is structural: R1 monkeypatches
`RunPreparationService` wholesale, so it can only prove the config path REACHES
the request object; R2–R8 call the manifest builders directly and never enter
`prepare()`. The join between the two halves — the thing the fix actually is —
was the thing no test crossed.

Change site 7 had no test at all. Deleting the single
`config=load_config(Path(args.config)) …` line from
`cli/main.py::_qualify_one_profile` left this file at 8 passed, and `grep -rln
"_qualify_one_profile" tests/` returned nothing. That is the limb the fix commit
itself calls load-bearing: without it, all 8 committed `run-config.yaml` files
are permanently unrunnable (`probe/lifecycle_gap.out`'s 8-of-8 refusal).

**What was done.** Two tests, no production change. `R9
test_prepare_compiles_the_run_from_the_operator_config_file` drives the real
`RunPreparationService.prepare()` — nothing monkeypatched but the offline
battery executor — against a real `run-config.yaml` on disk, and asserts both
limbs of GOAL.md's disjunction on the manifest as WRITTEN to the run root, with
an unconfigured control through the same service. `R10
test_qualify_addresses_the_subject_the_configured_run_needs` calls
`_qualify_one_profile` through a real parsed `--config F --provider-profile P
qualify` namespace on a home whose cache holds only the configured subject.
Each goes RED under its own mutation and is the ONLY test in the file that
does; the ring that was byte-identical now reports 1 failed, 218 passed, 1
skipped under each, and 219 passed, 1 skipped clean
(`proof/mutation_matrix_gap_closure.out`).

`proof/mutation_matrix.out` is corrected in place: its M4 row claimed "sites
4/7" and all of its redness came from site 4. A per-row statement of what each
of the seven original mutations actually proves is appended there rather than
substituted for the original transcript, which is a true record of seven runs
that happened. `VERIFY.md` gains §8 saying the same.

One map claim moved with it. `docs/map/SUB-application.md:213` asserted that
`_qualify_one_profile` passes the loaded `Config` into the subject builder and
cited a check that stayed green with that line deleted — a check that could not
fail, which is the one property re-derivation must have. The check now names R9
and R10; it passes clean (4 passed) and fails under the site-7 deletion (1
failed, 3 passed). `Verified-at:` was left where it was: that document's other
checks were not re-run in this lane.

**Residue — what remains unproven.**

- *Coverage of the other five change sites is unaudited.* M1 still proves site
  6 only through a monkeypatched capture, and M2/M3/M5/M6/M7 still exercise the
  builders directly rather than through a public verb. These two tests close
  the two holes that were MEASURED; they are not a coverage claim about the
  rest, and no one has looked.
- *The gap was found by a reviewer, not by the tranche.* Seven planted
  mutations, seven caught, and the number sounded like coverage. It was a count
  of tests that can fail, never a count of behaviours that cannot silently
  regress — and nothing in the workflow forced the difference to be stated.
- *Still offline.* No live evidence is added here. Every claim is a
  compile-time or read-time property of committed code.
