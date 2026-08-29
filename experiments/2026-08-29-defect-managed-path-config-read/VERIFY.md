# Verification — P14, `deepreason reason` now reads the operator's configuration

Tranche: `experiments/2026-08-29-defect-managed-path-config-read/`.
Phase: `dr-verify-outcome`, stage 3. Fix commit: `a82872b38`.
Offline by construction: this batch has no provider credential, so every claim
below is a compile-time or read-time property of committed code plus committed
records. No live run was attempted, and GOAL.md does not demand one.

---

## 1. Criterion command + output

GOAL.md's success criterion, run verbatim:

    PYTHONPATH=src:mini python -m pytest tests/test_managed_path_config_read.py -q
    ........                                                                 [100%]
    8 passed in 33.22s

(`proof/criterion_green.out`, re-run on the committed fix at `a82872b38`.)

Before the fix, on the same file at the same commit-minus-one:
`proof/repro_red_stage3.out` — **7 failed, 1 skipped**.

The criterion's substance, restated from GOAL.md, is a disjunction held FIELD BY
FIELD, not in aggregate: for every `Config` field an operator file sets away
from its default, either `config_from_run_manifest(manifest).<FIELD>` equals the
configured value, or a `compile_notices` entry `ENGINE_CONFIG_FIELD_NOT_CARRIED`
stands at `/engine_config/<FIELD>`. That is
`test_managed_manifest_carries_or_discloses_every_operator_setting`, and it is
green.

## 2. Mutation proof — every regression test can fail

`proof/mutation_matrix.out`. Seven planted mutations, each the smallest revert
of one change site; each was applied to the fixed tree, its named tests run, and
the tree restored. **7 of 7 caught RED.**

| mutation | tests it must turn red | verdict |
|---|---|---|
| M1 drop `config_path=args.config` (site 6) | R1 | RED |
| M2 stop threading `base=config` (sites 2-3) | R2, R8 | RED |
| M3 `model_copy` instead of `model_validate` (site 2) | R3 | RED |
| M4 drop `config=` from the qualification subject (sites 4/7) | R4, R5 | RED |
| M5 omit `config_digest` from run identity (site 5) | R6 | RED |
| M6 admit `config_digest` UNCONDITIONALLY (site 5) | R6 | RED |
| M7 let the operator's `roles` win (site 2) | R7 | RED |

M5 and M6 are opposite mutations caught by one test: that is the two-sided
guarantee P18 needed — a configuration must enter run identity, and a
question-only request must not move. The pinned historical digest
`7ea3afd5a387993d19999918ea26698529245bbf1c1ba23dc5ac6a22e03c93e9`
(`probe/request_identity_baseline.out`) is unchanged.

## 3. Nothing else moved

- **Consumer census, complete.** Every test file naming any changed symbol
  (`build_preparation_manifest`, `qualification_subject_manifest`,
  `_config_for_profile`, `RunPreparationRequestV1`, `_request_digest`,
  `RunPreparationService`), plus the CLI-admission and lifecycle-parity files:
  **683 passed, 0 failed** across 29 files — `proof/ring_blast_radius_green.out`
  (342) and the second ring (341). **Not one fixture was edited**, which is the
  load-bearing fact: every change site is additive with a `None` default, so the
  13 `test_run_preparation_service.py` tests and the four
  `*_excluded_from_subject_digest` guarantees in `test_reusable_qualification.py`
  — which the 2026-08-28 surface-5 grant calls "a guarantee, not a fixture" —
  pass unchanged.
- **Full gate** (`python -m pytest tests/ -q -n 4`, run once at this phase
  boundary on an otherwise idle box): **4441 passed, 6 skipped, 0 failed** in
  15:47 — `proof/gate_full.out`. Stated plainly because the fix commit's own
  message says otherwise: `a82872b38` was written before this run and records
  "no full gate run in this lane". The gate was then run, and this line is the
  measurement. (`--lf` was the lane brief's instrument, but `.pytest_cache`'s
  `lastfailed` was empty — nothing had failed — so `--lf` selected all 4446
  collected tests, i.e. the full suite. Verified by `--lf --collect-only`.)
- **`tools/blast_radius.py`** over the implemented diff:
  `"frozen_surface_verdict": "CLEAR"`, `frozen_surface_contacts: []`,
  `frozen_adjacent_contacts: []` (`proof/blast_radius_after_fix.out`). The
  conditional grant for SURFACE 4 (`run_manifest.py`) that this batch forecast
  for tranche B2 was **not used and not requested**: this fix only CONSUMES the
  disclosure machinery that already lives there.
- **`tools/diff_budget.py`**: `"verdict": "WITHIN"` — 75 insertions against
  FIX.md's 150 ceiling, 68 in `preparation.py` and 7 in `cli/main.py`
  (`proof/diff_budget.out`).
- **`python tools/docs_verify.py`** (full, idle box): 69 documents, 1154 checks,
  **4 failed — exactly the stated batch baseline** (3 checks on
  `CON-run-identity.md` naming git revisions this shallow clone does not
  contain; 1 falsified census at `INV-frozen-surfaces.md:181`). No fifth
  failure. `proof/docs_verify_after_fix.out`.
- **The P16 tripwire did NOT fire.** `INV-frozen-surfaces.md:297` matches a
  branch diff containing any frozen path; this branch's diff contains none, so
  it stayed green. Reported because the batch brief asked for it either way.
- **`python tools/docs_verify.py --audit`**: `0 finding(s)`. Each of the four
  new checks can fail if the behaviour regresses, and each was run before it was
  written down.

## 4. What the map now records (same commit as the code, `a82872b38`)

| document | Traps | new single-line check |
|---|---|---|
| `CON-authority.md` | REWRITTEN, never deleted: the 2026-08-28 disclosure could not fire on the managed path at all until this tranche | the `config` parameter exists AND a non-default config produces the notice |
| `CON-seats.md` | NEW: a flag gated a seat-configuration path and no configuration could turn it on | R7 + R8 node ids |
| `CON-run-identity.md` | NEW: `--config` is inside the run id, so changing a switch mints a different root | R6 node id |
| `SUB-application.md` | NEW: `reason` accepted `--config` and threw it away; `qualify` could not address a configured subject either | R4 + R5 node ids |

`Verified-at:` advanced on the three documents whose checks ALL passed.
`CON-run-identity.md`'s stamp was deliberately LEFT WHERE IT WAS: three of its
checks reference git revisions absent from this shallow clone and could not be
re-derived here, and a stale stamp is honest where a false one is not.

## 5. Verdict

**PASS (offline).** GOAL.md's criterion is met, its failure criteria are all
clear — no committed manifest's canonical bytes or `sha256` moved, no
qualification subject digest moved for a default-valued config (R3), no
committed digest pin was re-pinned, and no frozen surface was contacted.

## 6. Residue — honest

1. **The priced decision is delivered as a CAPABILITY, not as a charge.** No
   home pays anything for this fix: a defaults-only configuration compiles
   byte-identically (R3), and no committed manifest is recompiled. The battery
   cost STOP_STAGE2.md priced is paid by an operator who supplies a
   configuration that changes what the run does — 3 of the 8 committed
   `run-config.yaml` files via `RESEARCH_BACKEND`, 5 of 8 via
   `LEGACY_CRITICISM_ENABLED: false`. That charge is now REACHABLE (before this
   fix it was not payable at all, because `qualify` could not address a
   configured subject) and it is still the operator's to authorise per run.
2. **The second limb is not delivered and was never in scope.** For the 22
   dispatch-site switches the echo drops, this tranche delivers the DISCLOSURE
   limb — the record now says, in typed form, that `JUDGE_SEATS_ENABLED: true`
   was not carried. That is the 2026-08-28 law's "never silence", not its "at
   will". Carrying them requires changing the manifest's engine-config echo,
   which moves every pinned digest: P15, tranche B2.
3. **What a carried switch DOES inside a running cycle is unproven here.** Every
   claim in this document is a compile-time or read-time property. There is no
   live evidence and no provider in this container.
4. **The profile-owned override is deterministic and documented but not typed.**
   All 8 committed configurations set `roles`; the profile wins, the run still
   compiles, and `CON-seats.md` now says so — but no manifest notice records it,
   because emitting one needs frozen surfaces 4 AND 5 together. Parked as P21.
5. **Three surfaces still address the unconfigured subject**: `deepreason
   status` and the web page (P20), and `reason` over MCP (P22). All outside this
   lane's file cone.
6. **A numbering slip in FIX.md, stated so the register is not misread.**
   FIX.md §7 cites "P22" for the surface-4-and-5 park and §8 cites "P23" for the
   MCP one; `PARKED.md` is the register and numbers them P21 and P22
   respectively. P23 is the new entry added by this stage.

## 7. Errata

**errata: one entry earned, NOT written — parked as P23.**
`docs/map/CON-authority.md` claimed, before this tranche, that "Since 2026-08-28
the compile DISCLOSES each one it does not carry". True of the compiler, false
of the managed path, where no configuration was ever read. The Traps entry
itself was rewritten in the fix commit, so the map no longer carries the wrong
reading; the append-only `docs/ERRATA.md` entry is missing because
`docs/ERRATA.md` is outside this lane's file cone and other windows are live in
this repository. A ready-to-send prompt is in `PARKED.md` under P23, and it also
covers this tranche's own withdrawn stage-1 "road A" recommendation.
