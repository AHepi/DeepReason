# Delivered: four evidence states over the record, and a per-cycle declaration
# that criticism ran in full

Branch: `claude/evidence-states-conjecture-yb1aqd` (pushed, tree clean).
Base: `main` at `33f92e88c7`.

## What changed

The record can now tell a conjecture that survived something from one nobody
ever tested. Until this tranche both carried the label `accepted`, which made
the project's own success criterion — survivors that came through criticism —
unmeasurable from the record.

Every admitted artifact now gets one of four DERIVED readings, computed in
`src/deepreason/views/evidence_states.py` from facts the record already held:
attack edges, the status of each attacker, trial outcomes and status labels.
OPEN means nothing warranted has been brought against it and no trial ruled.
SUPPORTED means it came through a warranted attack or a trial that ruled for
the defence. REFUTED is the label as it stands today. CONTESTED means the
evidence points both ways — the judges split, or one attack was defeated while
another still stands. It is a reading, not a status: nothing admits, ranks,
immunises or refutes on it, and `tests/test_evidence_states_law_line.py`
forbids the scheduler, the adjudicator and the rules from so much as naming it,
with an empty exception list and both a spelling and a behavioural half.

The reading needed a second piece to be honest. "Nothing attacked this" means
two different things — the critics looked and found nothing, or the critics
never got to it — and only the first is evidence. So every criticism pass now
files one `criticism.dispatch.v1` record saying whether it made every call it
planned, or was cut short by a ration, a missing critic, a dropped call, or the
manifest-owned road this instrument does not measure. Only a pass that ran in
full lets an absence be read as a measurement, and only for the artifacts it
names. That record rides the existing notice channel, so no new kind of record
object exists and nothing frozen was touched.

Both surfaces show it: `deepreason results` gains an evidence-states block, a
per-episode breakdown and a per-artifact column on the frontier listing;
`deepreason stop-report` gains a sixth section. Both say plainly, on every
record written before this tranche, that nothing there says whether criticism
ever ran to the end. And both instruments that compare a run against a
no-harness baseline gained `--survivors-only`, off by default, so the
comparison can be made on survivors alone.

Why a warrant and not a critic call: the blind-critic bench of 2026-09-04
measured a critic that attacked every target it was shown, 240 out of 240.
Counting calls would have read a saturated instrument as universal survival.

## The number

`experiments/2026-09-04-change-evidence-states/CENSUS.md`, re-derivable by
`census.py`, which calls the shipped reader rather than reimplementing it.
Across **77 committed run roots** and **8 683 admitted artifacts**:

| reading | artifacts | share |
|---|---|---|
| OPEN — nothing brought against it | **7 713** | 88.8% |
| SUPPORTED — came through something | **47** | 0.5% |
| REFUTED | 844 | 9.7% |
| CONTESTED | 79 | 0.9% |

On the published **frontier** — 941 artifacts, the set a reader of
`deepreason results` actually looks at — **939 OPEN, 1 SUPPORTED, 1
CONTESTED.** Not one of the 77 roots carries a completeness declaration,
because all of them predate it, so none of those 939 is OPEN because a pass ran
in full and found nothing.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "one of OPEN … SUPPORTED … REFUTED … CONTESTED" | done | VALIDATION S1; `tests/test_evidence_states.py` (23) |
| R2 | "Computed from attack edges, warrants, trial outcomes and status labels already in the record" | done | VALIDATION S1; the reader registers nothing and mints no warrant |
| R3 | "changes NO admission, rank, immunity or refutation … RED if scheduler/, adjudication/ or rules/ read it" | done | VALIDATION S3; `tests/test_evidence_states_law_line.py` (7); mutants M6, M7 |
| R4 | "absence … counts toward OPEN only … unless the cycle carries a typed declaration that criticism dispatch ran in full" | done | VALIDATION S2; `test_absence_needs_the_declaration`; mutant M5 |
| R5 | "Design the declaration FIRST in SPEC.md: prefer … `record_measure`" | done | SPEC.md §0, written before any code. The measure channel carries it: no new record object kind, no surface-2 contact, no grant needed and so no STOP |
| R6 | "`deepreason results` … `deepreason stop-report` … counts per state per cycle … a per-artifact column … typed absence" | done | VALIDATION S4, S5, S6 |
| R7 | "`analyse_form_arms.py` and the diversity instrument gain a `--survivors-only` switch" | done-with-assumption **A3** | VALIDATION S7. "The diversity instrument" was traced, not guessed: it is `measure_diversity_per_problem.py`. The other candidate never opens a run root, so the switch would be inert in it |
| R8 | "No default behaviour of either instrument changes" | done | VALIDATION S7 — both default paths byte-identical to a capture taken BEFORE the switch existed |
| R9 | "forecast NO CONTACT … run tools/blast_radius.py … paste the verdict in SPEC.md" | done | SPEC.md Frozen-surface contact forecast, tool output verbatim; re-run after the files existed, still `CLEAR`; frozen diff empty |
| R10 | "Historical roots are never edited; the reading over a root without declarations yields OPEN/REFUTED only and says why" | done-with-assumption **A1** | VALIDATION S6. No root edited. A1 records where the sentence is narrower than R1 and R4 together: a declaration-less root can still show a REAL survival or a REAL split, and what is barred is reading an ABSENCE as survival |
| R11 | "mutation-proven tests for each state … the architecture test … the completeness rule proven RED" | done | VALIDATION S8 — seven mutants, each red then green. R11's named blind-critic fixture does not exist; see Errata-adjacent note below |
| R12 | "Full gate alone, 0 failed; docs_verify FULL; map moves in the same commit" | done | 5 073 passed, 6 skipped, **0 failed**; docs_verify 7 failed, all seven the authorization's own known-not-yours rows; map moved in commits 1-3 |
| R13 | "how many … turn out OPEN versus SUPPORTED, because that number is the point" | done | CENSUS.md and the table above |

No requirement is deferred, and none is not-done.

## Assumptions the operator may override

- **A1.** R10's "OPEN/REFUTED only" is implemented as the ABSENCE road, not a
  ceiling on the whole reading: a record with no declaration can still show
  SUPPORTED where an attacker was itself refuted, and CONTESTED where judges
  really split. The bar that IS enforced: nothing is ever read as having come
  through criticism on the strength of an absence unless a pass that ran in
  full names it.
- **A2.** "Every planned criticism call was made" is measured at the
  argumentative pass. Deterministic upstream criticism is not counted, because
  it cannot be cut by a budget or a missing seat.
- **A3.** "The diversity instrument" is `measure_diversity_per_problem.py`.
- **A4.** Typed absence follows the surfaces' existing convention; two codes
  were added to the closed vocabulary.
- **A5.** The reading lives in the view layer, the declaration's writer beside
  the other runtime recorders, so neither imports the other.
- **A6.** An artifact belongs to the episode it was first registered in;
  anything registered before the first episode opened gets its own bucket
  rather than being folded into episode 0.

Two decisions taken in this window that are not assumptions and should not be
buried:

- **The change is twice the size it was specified at.** The diff-budget gate
  read EXCEEDED at 1 797 against my own estimate of 855. It is disposed in
  SPEC.md Amendment 1 in the standard stop format: a per-file table showing
  every insertion answering to a spec item, three roads priced, and the ceiling
  re-priced to 2 250 (final reading WITHIN 2 029/2 250). No requirement gained
  scope; the estimate was wrong, mostly in tests.
- **A correction the record forced, not code reading.** The reader's first
  version counted every declined or blocked trial as a survival. Run over the
  P-A2 root, it called 39 of 94 artifacts survivors. That root files 16
  `execution-backed`, 11 `ensemble-split` and 4 `referential-integrity`
  declines — guards stopping the trial before it ruled, or the judges splitting.
  The corrected reading gives 8 SUPPORTED and 11 CONTESTED, and the
  first version's number would have overstated survival across the whole census.

## Map delta

created: `docs/map/CON-evidence-states.md` (7 checks, 6 of them
mutation-proven able to fail; one was found VACUOUS on the first pass and
strengthened before it was written down).
changed: `docs/map/INDEX.md` (routing row + concept row),
`docs/map/SUB-scheduler.md` (+1 check: the declaration's emission points and
outcome ordering, mutation-proven), `docs/map/SUB-application.md` (+1 check:
both surfaces show one derivation and stop-report opens no `Harness`,
mutation-proven; plus the `record_*` census row, which moved because a runtime
module now appends a Measure).
new checks: **9**. `docs_verify --links`: 0 dangling across 80 documents.
`Verified-at` advanced on those four documents and only those.

left stale: `docs_verify --stale` lists 20 documents. Five name a commit of
this tranche and each is dismissed with a stated reason in VALIDATION.md —
`SEAM-scheduler-x-rules`, `SEAM-scheduler-x-workflow`,
`SEAM-schools-x-scheduler` and `CON-scheduler-ranking` own `scheduler.py`
but describe rationing, foreign-criticism coverage, school allocation and
problem ranking, none of which moved; `INV-signal-contract` owns
`signals.py`, and adding a signal through the declared channel is what that
contract prescribes rather than a change to it. The other fifteen are
pre-existing staleness carried in from earlier tranches.

## Errata

**`docs/ERRATA.md` E77** (minted as E75; renumbered at merge) — the signal-registry gate does not do what
`docs/map/REC-add-signal.md` step 3 says it does. That recipe, and
`tests/test_signals.py`'s own docstring, promise that an emitted-but-undeclared
signal fails CI. Measured false for a signal emitted through a named constant:
with `criticism.dispatch.v1` undeclared, that test reported 9 passed while
`is_known` returned False. The signal was declared anyway and pinned by an
assertion of its own; the general hole is parked as P1, and E75 also records
this as REC-add-signal's FIRST failure under its own tripwire clause.

One further wrong premise, recorded here because it lives only in this window's
authorization and so has no committed document to correct: R11 names "the
blind-critic roots" as the canonical OPEN case, with "480 attacks and zero
warrants". That experiment committed no run root — it is a bench over direct
provider calls, which is exactly why its 480 attacks carry no warrant: no
harness was there to register one. The property was delivered from a root that
does exist,
`experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847`, whose
criticism ran 11 times and produced no attack at all, and which
`tests/test_adjudication_blindness.py` already pins for that shape. Its whole
population reads OPEN.

## Parked (not done, not promised)

Both entries carry a ready-to-send prompt in
`experiments/2026-09-04-change-evidence-states/PARKED.md`.

- **P1 — the signal-registry gate is blind to a signal emitted through a named
  constant.** Reproduced; ledgered as E77 (minted as E75; renumbered at merge). A defect tranche: widen the scan to
  resolve module-level string constants, then census whatever else turns out to
  be undeclared, treating each as a finding rather than a fixture to update.
- **P2 — the foreign-criticism road files `cut:foreign` and licenses nothing.**
  A run configured with manifest-owned criticism can never read an absence as
  evidence, however exhaustively its critics worked. That is the conservative
  failure and the right one to ship, but the coverage receipts almost certainly
  carry enough to derive a real declaration.

**Recommended next: P1.** It is the cheaper of the two and it protects every
future typed channel, not just this one — the next tranche that adds a signal
through a constant will ship it undeclared with the gate green, exactly as this
one nearly did.
