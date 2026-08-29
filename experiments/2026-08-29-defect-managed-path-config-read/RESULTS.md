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
