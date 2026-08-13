# Delivered: lifecycle-operation parity — "The flags and operations available to the newer reason runs should be available to all configurations"

Branch: `claude/lifecycle-operation-parity-zwzjar` (pushed, tree clean)

## What changed

A run started by `deepreason run --run-manifest` used to end as a root no
operation could touch. The bare CLI path called the scheduler and then
printed; the managed `TEXT_RUN_SERVICE` path called the same scheduler and
then wrote ten further records — the stop receipt, the run fence, the
capability audits, the terminal commitment, the replay validation, the
published result. Nothing shared those ninety lines, so nothing propagated
them. That is why the grounded-extension root (`8e22d0431fd2b98d`)
completed 24 real cycles and then refused `AMEND_NOT_AT_TERMINAL`,
`CONTINUE_STOP_REQUIRED` and `RUN_RESULT_NOT_READY`.

Those ninety lines are now one module-level function,
`application/text_runs.py::terminalize_text_run`, which both paths call.
`cli/main.py::_execute_bound_run` additionally writes the two lifecycle
documents a continuation reads, opens a progress stream, and renders the
bound dossier into source records before the scheduler dispatches — so a
compiled-config run is a full lifecycle citizen from its first cycle. A
new verb, `deepreason finalize`, brings a root that stopped BEFORE this
fix to its terminal by appending records only; it never opens an existing
byte for modification. `amendment/apply.py` was narrowed so a source that
was BOUND into a run's identity but never INTRODUCED to its models can be
admitted by an amendment — the refusal keeps its exact force wherever a
first introduction actually exists. `CLAUDE.md` gains the standing
operator design law that requires all of this, in the same commit as the
code enforcing it.

Proven on the real subject: the grounded-extension root now stands at
`current_valid_committed` and carries amendment epoch 1 with all six of
its bound documents admitted — and `git diff --numstat` over both
operations reports `log.jsonl  20  0`. Twenty appended lines, zero
deletions, on a committed root.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "every operation available to managed reason runs … works on runs launched from ANY configuration path" | done-with-assumption **A2** | `6f7bc6cd7`, `d0771479c`, `2c45193c1`; VALIDATION S1/S2/S7 |
| R2 | "OPERATION INVENTORY: table every lifecycle operation … works / broken / never-wired, with proof" | done | `1e73e7e86` — `INVENTORY.md`, 17 rows, each proved against the real root |
| R3 | "FIX: close every gap so the operations work on manifest-launched roots" | done | `6f7bc6cd7`, `d0771479c`, `2c45193c1`, `0c429676b`; VALIDATION S1–S6 |
| R4 | "the path to amendable MUST be appended typed records … the committed root's existing bytes are never edited" | done | `c28d1be59`; `git diff --numstat` → `log.jsonl 20 0` |
| R5 | "DIAGNOSE FROM THE RECORD FIRST … name the exact missing or unrecognized record" | done | `INVENTORY.md` "Diagnosis first" — ten records named in a table |
| R6 | "Two hypotheses to separate with the record … The fix differs; the root decides" | done | (a) CONFIRMED, (b) REFUTED — the reader is correct, there was nothing to read |
| R7 | "finalize … then `deepreason amend` … then `deepreason continue`" | **finalize + amend done; continue BLOCKED** | `LIVE.md`; `finalize.json`, `amend.json`. Continuation needs `OLLAMA_API_KEY`, removed by a container rebuild — stated, not skipped |
| R8 | "Expected end state (typed outcomes only) … 6 attached source records … zero NEW violations … RESULTS.md gains a dated segment" | done, **one prediction measured differently** | 6 admitted / 0 refusals; `verify_root` → `[]` (not the predicted "6 remain") — SPEC A4 named this in advance; RESULTS.md segment appended |
| R9 | "Ledger the last sentence as a standing operator design law … same commit as the fix" | done | `d0771479c` — `git show --stat` names both `CLAUDE.md` and `cli/main.py` |
| R10 | "regression pair … Tests asserting the old gap flip with SPEC.md's prediction" | done | `737a709fd` (RED) → 11 passing; prediction CONFIRMED — no existing test asserted the old gap |
| R11 | "ring while iterating; full gate at the boundary; docs_verify full" | done | full gate `1 failed, 3552 passed` = baseline; docs_verify `3 failed` = baseline |
| R12 | "Map moves in the same commits" | done | 4 documents, each in its code's commit — see Map delta |
| R13 | "Errata check … next free number" | done | `docs/ERRATA.md` **E25** |
| R14 | "Every committed root replays byte-unchanged: targeted verify_root_report … pasted" | done | no replay reader changed; targeted check pasted in VALIDATION S8 |
| R15 | "Qualification-digest drift: REPORT the cost, don't stop" | done | blast-radius `"qualification_digest": []` — **cost zero**, no battery re-runs |
| R16 | "Commit and push every phase boundary … Deliver R-by-R with pasted PROOF" | done | 13 commits, each pushed; this table |

No row is `not-done`.

## Assumptions the operator may override

- **A1** — "append" names the amendment's evidence append (`amend
  --attach`), not a `deepreason append` subcommand. There is no such
  subcommand in `cli/main.py`, and the operator's own sentence paired the
  word with the `AMEND_NOT_AT_TERMINAL` evidence.
- **A2** — parity is delivered by making the compiled-config launch path
  (`deepreason run --run-manifest`) lifecycle-complete, rather than adding
  `--run-manifest` to `deepreason reason`. The second surface is PARKED as
  P1, not dropped. **This is the assumption most worth your attention** —
  if you meant `reason` itself should take the compiled config, P1 is the
  tranche that does it.
- **A3** — continuation concurrency is not settable at continue time; the
  bound manifest freezes it for the run's life.
- **A4** — an amendment epoch's appended source records CAN satisfy the
  attached-evidence check. Verified rather than trusted: they did, and the
  six violations cleared.

## Map delta

changed: `docs/map/SUB-application.md`, `docs/map/SUB-amendment.md`,
`docs/map/SUB-scheduler.md`, `docs/map/CON-run-identity.md`
created: none
new checks: 6 executable `check:` commands, plus 5 new `Traps` entries
(the printing bare-run path; finalize appends and never edits; deriving a
report must not construct a Scheduler; terminalization is not atomic so a
killed process must be COMPLETED not restarted; the narrowed duplicate
refusal). Every one names the grounded-extension run.
left stale: none. `docs_verify` full mode is back to its recorded
baseline of 3 failures, all `CON-run-identity.md` git-history checks that
need an unshallowed clone.

**Finding worth your attention:** the map gate caught four breakages of
mine, and two of those four were defective CHECKS I had just written — a
check whose own explanatory comment tripped it, and a test-name harvest
that did not cover the file its new check cites. Both would have rotted
silently. Fixed in `09a45bd58`.

## Errata

**E25** added — `README.md`'s "`deepreason amend` adds to a stopped run"
was true of managed runs only; a run stopped by `deepreason run
--run-manifest` could not be amended at all. The census behind the entry
found no committed document that stated the launch-path dependency and
none that denied it: the gap was silence, not a false sentence, which is
why it survived. The claim is now true as written.

## Parked (not done, not promised)

- **P1 — `deepreason reason` cannot take a compiled run manifest.** The
  other half of your sentence ("doesn't recognise the new config style").
  Ready-to-send prompt in `PARKED.md`.
- **P2 — no seam document covers application × amendment, application ×
  verification, or amendment × verification**, and `INDEX.md`'s subsystem
  table omits `SUB-application.md` and `SUB-amendment.md` entirely,
  though both exist and are stamped. Ready-to-send prompt in `PARKED.md`.
- **P3 — operator lock files are committed inside run roots.** After a
  legitimate lock acquire, `git status` shows `.run-operator.lock` and
  `.make-operator.lock` as modified beside `log.jsonl 1 0`, so a reader
  auditing whether a committed root was edited cannot tell control from
  record at a glance. Ready-to-send prompt in `PARKED.md`.

**recommended next: P1.** It is the remaining half of the sentence that
opened this tranche, the operator has already stated the authority for it
verbatim, and this tranche's `INVENTORY.md` row 17 already carries the
proof of the gap — so the follow-up starts from evidence rather than
re-deriving it. P3 is second: it is small, and it protects the
append-only law's own legibility, which every future live tranche leans
on.

## The one thing still owed

`deepreason continue` on the grounded root — 8 cycles, 500 000 tokens.
It needs the credential the container rebuild removed:

    printf 'OLLAMA_API_KEY=<key>\\n' > experiments/2026-08-12-live-grounded-extension-expansion/env
    cd experiments/2026-08-13-change-lifecycle-operation-parity && setsid nohup ./live_parity.sh & disown

**Correction to an earlier claim in this document's first version:** the
OPERATIONS are exactly-once, but the DRIVER was not resumable — it treated
`finalize`'s and `amend`'s typed already-done refusals as failures and
exited on them. Fixed: the driver now reads
`FINALIZE_ALREADY_TERMINAL` and `AMEND_SOURCE_ALREADY_ADMITTED` as "this
stage already succeeded" and carries on to the continuation, and skips the
5-minute post-amend `verify_root` replay when it has already been
measured.
