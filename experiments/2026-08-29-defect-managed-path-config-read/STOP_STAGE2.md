# STOP (stage 2) — the design is complete and priced; the spend and one call site are the operator's

Tranche: `experiments/2026-08-29-defect-managed-path-config-read/` (defect P14).
Raised at the end of stage 2 (`dr-propose-fix`), with `FIX.md` committed and
**no production code changed**, per the batch disposition:

> IF carriage moves ANY QUALIFICATION SUBJECT DIGEST, that is a PRICED STOP,
> NOT a grant. The operator decides that spend, not you.

A digest moves. §3 of `FIX.md` proves no design avoids it while delivering
carriage. The lane stops. Nothing was worked around, no gate was weakened, no
frozen surface was touched (`proof/blast_radius.out`:
`"frozen_surface_verdict": "CLEAR"`).

## The decision, in one sentence

Authorise `deepreason reason --config F` to compile the run from `F` — which
costs one qualification battery per home per configuration that actually changes
what the run does, and requires `deepreason qualify` to learn the same `--config`
in the same commit or the configured run can never start at all?

## What is NOT at risk, said first

- **No committed run root changes.** Every one is read, never recompiled.
- **No home pays anything for the ability to configure.** A defaults-only
  configuration compiles byte-identically (`PRICE.md` control: manifest
  `37e3fa54edb75346…`, subject `7c0ba0a174fdc2d9…`, both unchanged), and
  `deepreason reason` with no `--config` is byte-for-byte what it is today.
- **No frozen surface is contacted**, including the surface-4 grant this batch
  forecast for tranche B2: it is not used and not requested here.

## What changed since stage 1's stop — three measurements

1. **Stage 1's price was too low, not too high** (`probe/lifecycle_gap.out`).
   `deepreason reason` prepares with no qualification executor, so a moved
   subject is a REFUSAL, not an automatic battery; and `deepreason qualify`
   builds its subject with no configuration parameter at all. On a home that has
   fully qualified, **8 of 8 committed `run-config.yaml` files are refused
   `QUALIFICATION_NOT_CONFIGURED`, and no committed command can clear it.**
   Carriage without the qualify wiring is not expensive — it is impossible.

2. **A flag already gates a seat-configuration path, and cannot be turned on**
   (`probe/school_seat_deadlock.out`). `reason --school-seat` and
   `--criticism-seat` are refused `SCHOOL_SEATS_DISABLED` for every provider
   profile, because the managed path's `SCHOOL_SEATS_ENABLED` is always the
   default `False`. The shipped help text says the gate "is still set via
   `--config`" — the file P14 shows is never read. The documented workflow is
   broken end to end.

3. **Stage 1's recommendation was wrong and I am withdrawing it.** `STOP.md`
   recommended road A (carry only the echo-dropped fields) as "the law's second
   limb for every switch the law names, at zero cost for all but one". A dropped
   field is absent from `engine_config_json`, and `config_from_run_manifest` is
   the only source of a run's `Config`, so carrying a dropped field cannot make
   it reach the run. Road A's 23 free fields are free precisely because they
   deliver nothing. Road A minus its priced field IS road C.

## The two roads, priced

| road | what the operator gets | price |
|---|---|---|
| **CARRIAGE** (`FIX.md`) | the configuration changes the run; the record discloses every field the manifest cannot carry; `--school-seat` starts working | one battery per home per configuration that changes the run — measured: 3 of 8 committed configs via `RESEARCH_BACKEND`, 5 of 8 via `LEGACY_CRITICISM_ENABLED=False`; ~14 min, ~1160 calls, once, then cached |
| **DISCLOSE ONLY** | the record says, field by field, that the setting was not honoured | zero — and no gate can be turned on, which is the half of the 2026-08-28 law still undelivered |

## Recommendation: CARRIAGE

- Every priced move corresponds to a genuine change in what the run is
  contracted to do. Nothing is priced for bookkeeping: 22 of the 25
  echo-dropped switches are disclosed and cost nothing, and the three committed
  subject-exclusion guarantees for `JUDGE_SEATS_ENABLED`,
  `ADJUDICATION_STATUS_AUTHORITY_ENABLED` and `SCHOOL_SEATS_ENABLED` stay green
  untouched.
- The product's own surface already declares this cost as normal: the
  `--school-seat` help text says moving a seat "changes the qualification
  subject digest — this is a cache miss, not a routing tweak, and reruns the
  full battery (minutes, hundreds of provider calls)".
- Disclose-only was already rejected once, by the P10 tranche, on the ground
  that still holds: a warning that carries nothing cannot turn a gate on.

## What a "go" authorises, precisely

1. The qualification spend above.
2. **One extra call site**: `deepreason qualify` reads the same global
   `--config` and threads it into `qualification_subject_manifest`
   (`FIX.md` change site 7). The lane cone says `cli/main.py (only the
   reason/config wiring)`; this is config wiring in that file, and without it
   the fix ships a permanent refusal. Named here rather than assumed.
3. The disposition of P18 written into `FIX.md` §6: the configuration enters run
   identity conditionally, exactly as `dossier_digest` did, so every historical
   question-only run id stays byte-identical (pinned at
   `7ea3afd5a387993d19999918ea26698529245bbf1c1ba23dc5ac6a22e03c93e9`).

Not authorised by a "go", and parked with drafted grant requests: the typed
record-level disclosure of profile-owned overrides (**P21**, needs surfaces 4
AND 5), `deepreason status`'s config-blind projection (**P20**), and MCP's
`reason` (**P22**).

## Everything stage 2 owed is committed

`FIX.md` (design, laws, change sites, eight regression tests with the mutation
that reddens each), three new re-runnable probes, the blast-radius verdict, and
three new parked prompts. No production file changed:
`git diff --name-only origin/main...HEAD -- src/` is empty.
