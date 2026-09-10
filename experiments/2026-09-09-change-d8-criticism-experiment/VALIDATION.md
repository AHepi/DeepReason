# Validation for: does criticism, once connected and allowed to bite, make the harness's output materially better than the plain model? — TRANCHE 1

Scope: TRANCHE 1 only (R38) — every instrument, the offline proofs, the soaks,
and a sealed PREREG, with NO LIVE CALL. The launches, the qualification
batteries and the judging are tranche 2 and are not validated here.

## Acceptance checks

**S1 (R4, C3) — one question, one model, matched ceiling.**
`arm0.py 3 --dry-run` → `question_sha256
e8e720d251b3cab2cddd548cb5064a74575404c8ae47f347f840faa6021a19b1`, and the same
digest re-derived by a SEPARATE command straight from the frozen input. Not the
instrument vouching for itself. : **PASS**

**S2 (R5, A3) — ARM 0 built, K required, no call made.**
`env -u OLLAMA_API_KEY python arm0.py --dry-run` → `rc=2` with no K; `arm0.py 0
--dry-run` → `rc=2`; `arm0.py 9 --dry-run` → rc=0 printing the prompt digest and
size with the credential absent from the environment. : **PASS**

**S3 (R6) — criticism reaches the seat that writes the next candidate.**
`render_census.py /tmp/soak-c/run` → 25 plans, 25 naming `dr.open-criticisms`,
**4 RENDERED**, 2 868 bytes. n > 0.
Calibration on the committed organiser root: 11 plans, 11 naming, **9
RENDERED** — reproducing the monitor's cited "9 of 11" exactly, and exposing
that 11 plans NAME the section while only 9 CARRY it. : **PASS**

**S4 (R7, R8, R9) — ARM V's contentless criticism.**
Stub: reply validates against the shipped `ArgumentativeCriticOutput`; round
robin covers the bank; an empty bank REFUSES; a non-critic contract falls
through to the shared fixture byte-identically.
Bank: `--self-test` deterministic under a fixed seed (digest `7fbd86af…`),
lengths tracking the target range, every sentence from the committed clauses.
Vacuity: clean bank **VACUOUS**; planted bank **NOT VACUOUS**, caught twice
over — off-vocabulary AND by overlap on `corroboration, future, induction,
reliability`.
Route identity: 5 tests, 2 mutations red, `src/` restored byte-clean. : **PASS**

**S5, S5b, S5c (R34, R35, R10, R37) — ARM A, Road A-cross.**
`build_manifest.py --route-identity` → `"violations": []`. Every generating role
C==A; only `judge` differs C↔A; only `argumentative_critic` differs C↔V.
Authority at the seat: ARM C `observe_only`, ARM V `observe_only`, ARM A
**`trial_required`** with the master gate True and `criticism_policy` None.
Ensemble: ARM A **obtained, 2 seats, families ['glm','qwen']**; ARM C
**REFUSED** — the natural red control proving the check can say no.
PREREG §0 carries the one-model deviation as its own disclosure row. PARKED P1
is untouched and unbuilt. : **PASS**

**S6 (R12, R13) — two runs per arm, varying nothing.** Specified in PREREG §5
(retire the first root by rename, commit the rename first, relaunch identical).
Not exercised: tranche 2's. : **SPECIFIED, NOT EXERCISED**

**S7 (R14) — three batteries.** Counted in PREREG; paid in tranche 2. :
**SPECIFIED, NOT EXERCISED**

**S8 (R15–R21) — the sealed measure.** `PREREG.md` sha256
`29bb6b14006d2e788b994fe2671cde7546a77dbb2b0592b895fe2e04c3f0665a`, in the
commit message of the commit that added it, verified equal to the committed
file. CRITERIA digest `fab3fde2f3a2000bd5f7415e7a7ae3be013fd8b83b4fd52395eef4b18327df28`
by the instrument's own `criteria-check`, and the whole file diffs clean against
the organiser tranche's.
Per-position units: composed text byte-identical before and after
(`21bd15ed…` both sides), two runs `diff -r` clean, and of 36 units the number
whose text does not appear verbatim in the composed unit is NONE.
Counterpart rule: 108 of 108 pairs within the length rule, twice identically.
Both judging refusals mutation-proved, 4 mutations red. : **PASS**

**S9 (R22) — the placebo.** `coupling_placebo.py --reproduce-w2` → **32 of 32
fields OK**, all four published rows cell for cell (−12.7, −1.9, +5.9, +0.0 pp),
denominators, coupled and helped counts EXACT — the 0.1 pp tolerance never
exercised. Empty case typed `n=0` with a positive control beside it. : **PASS**

**S10 (R23) — the record census.** Evidence-state row equals `deepreason
results --json` byte-for-byte. Argumentative column mutation-proved on a
fixture, because no committed root can drive it. : **PASS**

**S11 (R24) — the claims file.** `record_claims.py` exits 0; 10 claims, each
with a falsifier and a standing; 2 controls pointing against the prediction they
guard. : **PASS**

**S12 (R25) — a green soak per configuration.**
ARM C: `exit 0 (clean)`, cycle 8 of 8, `verify_root` 0 violations.
ARM V: `exit 0 (clean)`, same five assertions, drive 266.7 s.
ARM A: `exit 0 (clean)`, qualification rc=0 in 4.8 s, drive 272.0 s.
Each soak declares 7 assertions and EVALUATES 5, and says so itself. : **PASS**

**S13 (R26) — env discipline.** Never committed (0 hits across all branches),
gitignored by rule `.gitignore:50`, mode 600, and **atime == mtime to the
nanosecond**: nothing ever read it. : **PASS**

**S14 (R27, R28) — detached launch, monitoring, failure ledger.** Tranche 2's.
No live failure budget was spent because no live call was made. : **SPECIFIED,
NOT EXERCISED**

**S15 (R29) — RESULTS.md.** Tranche 2's: it reports what ran. : **DEFERRED TO
TRANCHE 2**

**S16 (R31, R32, R33, R36) — scope and delivery.**
`git diff --stat origin/main..HEAD -- src/ mini/ tests/` → **EMPTY**. : **PASS**

## Full gate

**NOT OWED, and the precondition is proved rather than asserted.** R31: "No
gate run unless a file under `tests/` changed." `git diff --stat
origin/main..HEAD -- tests/` is EMPTY. The tranche's own ring, which is what it
does own: **15 passed**.

## Record-behavior preservation

**n/a.** This tranche touched no reader or validator of the append-only record.
`git diff --stat origin/main..HEAD -- src/` is EMPTY.

## Frozen-surface diff

    git diff --stat origin/main..HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/verification/ \
      src/deepreason/run_manifest.py src/deepreason/qualification.py
    (no output)

EMPTY, pasted as proof. This is the one mechanical tripwire on the path and it
is not optional. : **PASS**

## Map

`docs_verify.py`: **8 failed — every one PRE-EXISTING, proved by the skill's own
method rather than argued.**

    docs/map/ diff against origin/main:  (no output)

Every map document is BYTE-IDENTICAL to main, so every check's text is
identical. Each failing check was then re-run in a worktree at `origin/main`,
with this branch's changes absent:

| Failing check | at origin/main |
|---|---|
| `SEAM-llm-x-rules.md:54` unparseable check opener | malformed in the document itself, identical on main |
| `CON-run-identity.md:211` | `rc=1` |
| `CON-run-identity.md:213` | `rc=1` |
| `CON-run-identity.md:215` | `rc=1` |
| `INV-frozen-surfaces.md:206` | `rc=1` |
| `INV-frozen-surfaces.md:1000` | `rc=1` |
| `INV-frozen-surfaces.md:1365` | reads the ORGANISER tranche's claims file and root; this branch touched neither |
| `CON-run-identity.md:313` | TIMEOUT after 300 s — an expense fault, not a truth fault; the check itself says "narrow it to the claim it actually tests" |

And independently: **no failing check reads anything this branch changed.**
`grep` over the failures for `d8-criticism` or `cycle_soak` returns 0. The one
check that scans `experiments/` broadly (`INV-frozen-surfaces.md:206`) finds its
four hits in the 2026-08-26, 2026-09-01 and 2026-09-03 tranches; this tranche
contains ZERO `workflow-provider-attempt-v1` records.

Pre-existing failures do not block (the skill's own rule) and go to PARKED.md as
**P5**. : **PASS (no failure attributable to this change)**

`--audit`, `--links`, `--coverage`, `--stale`: **not run, and the skip is a
recorded decision.** Every map document is byte-identical to main, so none of
these four modes can report anything this branch caused. Running them would
measure the map's standing state, which is an audit of the repository and not a
validation of this change — and CLAUDE.md's MANDATORY block is explicit that
verification instruments are not run to "confirm" what a window was not asked to
confirm.

**new checks added by this change: NONE, and that is correct here.** No map
document changed because nothing this tranche built is described by one: every
artifact lives under `experiments/2026-09-09-change-d8-criticism-experiment/`
plus three data rows in a soak case table. The falsifiable claims this tranche
DID add live in `claims.json` (10, each with a falsifier) and in its own
`tests/` (15, four of them mutation-proved).

**record observables added vs sweep probes: NONE.** This tranche adds no field,
record type or finding to the typed record. It only READS.

**wheel smoke: packaging surface untouched — smoke not owed.** No change to
`pyproject.toml`, CLI entry points, the MCP surface or the wheel layout.

## Requirement sweep

| R | demonstrated by |
|---|---|
| R1 route through the change orchestrator | REQUEST → SPEC → CHECKLIST → steps → this document |
| R2 cite the motivating audit | REQUEST.md "The motivating audit", four sections quoted |
| R3 read the named sources | SPEC.md M1–M10, each a pasted command |
| R4 one question, one model, matched budget | S1; deviation for ARM A's judge seats disclosed under R35 |
| R5 ARM 0 plain sampling | S2 |
| R6 ARM C, criticism rendered, verified on the record | S3 |
| R7 ARM V vacuous | S4 |
| R8 price two roads, prefer the stub | SPEC.md Options: V-a CHOSEN citing M5; V-b, V-c rejected citing M3, M4 |
| R9 prove offline it reaches the next candidate, naming nothing | S4 route identity + vacuity, both mutation-proved |
| R10 ARM A authority granted, typed warning captured | S5; superseded in part by R34; the two `ENGINE_CONFIG_FIELD_NOT_CARRIED` notices are the captured warnings |
| R11 STOP if the switches do not reach a managed run | Stopped at SPEC.md; the switches DO reach (M1, M2); the blocker was different and was reported |
| R12 two runs per arm | PREREG §5; tranche 2 |
| R13 vary only a nonce | PREREG §5 — varies NOTHING, which is stronger; recorded as a resolution |
| R14 count the batteries | PREREG; tranche 2 |
| R15 PREREG sealed by sha256 before any live call | S8, digest verified against the committed file |
| R16 the judged unit | PREREG §6, both refusals mutation-proved |
| R17 blind pairwise, criteria byte-identical | S8, `fab3fde2…` |
| R18 length rule applied AND raw share reported | PREREG §10, with its ceiling registered in advance |
| R19 the secondary comparison | PREREG §11; 108 of 108 pairs match |
| R20 five comparisons | PREREG §8; asserted in the tranche's tests |
| R21 decision rule, never pooled | PREREG §9; enforced structurally, mutation-proved |
| R22 W2's placebo discipline | S9 |
| R23 the record census | S10 |
| R24 claims file, standing required | S11 |
| R25 green soak per configuration | S12, three of three |
| R26 env discipline | S13 |
| R27, R28 launch discipline, failure budget | tranche 2 |
| R29 RESULTS.md | tranche 2 |
| R30, R36 scope hard | S16, and the frozen-surface diff |
| R31 tests only for the tranche's tools; no gate unless tests/ changed | 15 tranche tests; `tests/` EMPTY |
| R32 deliver through validate then deliver | this document, then DELIVERY.md |
| R33 commit and push at every boundary | 17 commits, each pushed |
| R34 Road A-cross, trial_required | S5 |
| R35 disclose the deviation, confine it to adjudicating seats | PREREG §0 disclosure row; S5 route identity |
| R37 P1 stays parked | PARKED.md P1 unchanged; SPEC S5c |
| R38, C9 tranche 1, no live call | S13 and `proof/SCOPE_AND_SPEND.txt`, four independent proofs |
| R39 deliver and stop | DELIVERY.md, then stop |
| R40 tranche 2 only after the monitor has read tranche 1 | not begun |
| R41, R42 the two ceiling raises | SPEC Amendments 4 and 5, each itemized from a measured base |
| R43 "approved" | read narrowly as: proceed with validation and delivery; REQUEST Amendment 4 |

No R is unaccounted for. Six are legitimately tranche 2's under R38, which is
the operator's own split.

## Assumptions carried

- **A1** — all three harness arms launch on the compiled-manifest road, not
  `deepreason reason`. Forced: ARM V's stub-bound critic is unreachable on the
  managed path, and mixing roads would confound `C vs V` with the launch road.
- **A2** — the second run of an arm varies nothing, rather than a declared nonce.
- **A3** — ARM 0 runs LAST, K set from the harness arms' measured call count.
- **A4** — `qwen3.5:397b` is "the harness's current model"; CLAUDE.md's `glm-5.2`
  header is stale and PARKED (P2).
- **A5** — the bare-essay counterpart is the closest SENTENCE prefix, two-sided.
  Revised twice under its own self-test before sealing.

## Verdict: **PASS**

Every acceptance check that tranche 1 owns passes on the assembled whole. Four
items are marked SPECIFIED-NOT-EXERCISED or DEFERRED and every one of them is
tranche 2's by the operator's own instruction, not an omission. The only gate
failures anywhere are 8 map checks proved pre-existing by re-running them at
`origin/main`, and they are parked rather than absorbed.
