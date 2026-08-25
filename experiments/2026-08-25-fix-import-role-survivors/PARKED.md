# PARKED — found in this tranche, deliberately not fixed here

One tranche, one goal (CLAUDE.md cross-routing). Each item is a finding, not a
task for this tranche, and carries a ready-to-send prompt so the follow-up
costs a paste rather than an authoring session.

---

## P1 — two further survivor derivations exist, and neither consumes the authority

**What.** Beside `run_report` (fixed here) and `Scheduler._select_problem`
(already correct), two more sites derive a survivor set of their own:

    src/deepreason/report.py:353   eval_report -> survivor_hv / survivor_reach
    src/deepreason/loop.py:40      run_problem -> the P1 minimal loop's result

Both use the same shape `run_report` used — ACCEPTED and addressed, no role
clause.

**Why it is not fixed here.** Neither is the results surface, which is what
GOAL.md bounds this tranche to, and on the P-R1 root neither number moves:
measured over the committed root, **0 of the 24 IMPORT survivors carries an
`hv` or a `reach` entry**, so `eval_report`'s two distributions already exclude
them by absence rather than by rule. `loop.py::run_problem` is the spec §16 P1
minimal loop and is reachable only from `tests/test_loop.py` — nothing in
`cli/`, `application/` or `runtime/` calls it.

**Why it is worth recording anyway.** "Excluded by absence" is not the same
guarantee as "excluded by rule": an import record that ever acquired an `hv`
would silently enter a distribution the invariant says it may not enter. The
whole point of this tranche's fix is one authority rather than several kept in
agreement, and these two are the remaining several.

**Ready-to-send prompt:**

> Route through `deepreason-orchestrator` (a defect, the same one). Goal: make
> `src/deepreason/report.py::eval_report` and `src/deepreason/loop.py::
> run_problem` consume `deepreason.scheduler.scheduler.counts_as_survivor`,
> the single membership authority installed by
> `experiments/2026-08-25-fix-import-role-survivors/`, instead of each
> re-deriving `status == ACCEPTED and addressed`.
>
> No live run is needed. The fixture is committed:
> `experiments/2026-08-25-poietics-program/run`, whose 82-strong stored
> survivor set is 58 CONJECTURER + 24 IMPORT. Note before you start that
> today the change moves NO number on that root — 0 of the 24 IMPORT
> survivors carries an `hv` or a `reach` entry, so `eval_report`'s
> distributions already exclude them by absence. That makes this a
> guarantee-hardening change, not a number-changing one, and the regression
> must therefore be a MUTATION proof (drop the role clause, show RED) rather
> than a before/after count.
>
> Check `docs/map/SUB-scheduler.md`'s "Where authority lives" table and
> `DR-CON-scheduler-ranking`'s socket contract in the same commit: both name
> the authority, and a third and fourth consumer is a row, not a rewrite.

---

## P2 — `application/` imports from `scheduler/` with no seam document

**What.** `docs/map/INDEX.md`'s seam matrix does not list the pair
`application x scheduler` **at all** — which the INDEX's own prose says means
"a pair with no measured import traffic". There is traffic:
`src/deepreason/application/text_runs.py:531` imports `run_report` from
`deepreason.scheduler.scheduler`, and this tranche adds a second such import
(`application/results.py` importing the survivor authority).

**Why it matters.** The matrix is a routing instrument, and the ordering rule
("read the SEAM before the subsystems") cannot fire for a pair the matrix says
does not exist. A future change spanning the run-report writer and the results
reader gets no warning that the two are joined.

**Why it is not fixed here.** Authoring a seam document is its own tranche
under `docs/map/SCHEMA.md`, and `REC-change-a-seam.md` is the recipe. This
tranche records the traffic in `DR-SUB-application` and `DR-SUB-scheduler`
instead, which is the smallest honest thing.

**Ready-to-send prompt:**

> Route through `dr-change-orchestrator`. Goal: write
> `docs/map/SEAM-application-x-scheduler.md` per `docs/map/SCHEMA.md`, and add
> its row to `DR-INDEX`'s seam matrix, because the pair carries real import
> traffic the matrix currently shows as nonexistent.
>
> The measured traffic today: `application/text_runs.py` imports `run_report`
> (function-local, so the coupling metric cannot see it — the same blind spot
> `DR-INDEX` already documents for periphery x verification and calculus x
> rules), and `application/results.py` imports the survivor-membership
> authority added by
> `experiments/2026-08-25-fix-import-role-survivors/`. The agreement to
> document is: the scheduler owns what a survivor IS; the application layer
> owns how a run's outcome is PUBLISHED and RETRIEVED, and must never
> re-derive the first.

---

## P3 — a root's STORED finding-family breakdown and a fresh re-derivation disagree

**What.** On `experiments/2026-08-25-poietics-program/run`:

    run-result.json  verification.finding_counts   completion 120, operational 22
    verify_root_report(<root>) re-derived           completion 121, operational 23

**Not caused by this tranche, and measured rather than assumed.** The
re-derivation returns **121/23 at the tranche base `43f408506` and at HEAD
alike** — identical — so the gap predates this work and no part of this fix
touches it. `valid` is True and violations are 0 in both.

**Why it is worth recording.** `deepreason results` reports the STORED
breakdown by default and the RE-DERIVED one under `--verify`, and the two
disagree by one in two channels on the same root without saying so. A reader
comparing a `--verify` run against a quoted figure (RESULTS.md quotes 120/22,
correctly, from the stored payload) will see a discrepancy with nothing typed
to explain it. Either the writer counted at a different seq than the reader
re-derives from, or one channel gained a finding class after the payload was
written; the record here does not separate those.

**Ready-to-send prompt:**

> Route through `deepreason-orchestrator` (a defect: two instruments disagree
> about one root and neither says so). Goal: establish why
> `run-result.json`'s stored `verification.finding_counts` and a fresh
> `verify_root_report` over the same root differ by one in the `completion`
> and `operational` channels.
>
> No live run. The fixture is committed:
> `experiments/2026-08-25-poietics-program/run` — stored 120/22, re-derived
> 121/23, and the re-derivation is IDENTICAL at `43f408506` and at the head
> of `experiments/2026-08-25-fix-import-role-survivors/`, so the cause is
> older than either. Check other committed roots for the same gap before
> designing anything: if it is universal it is a writer/reader seq mismatch;
> if it is one root it is that root's history.
>
> Note the surface consequence, which is what makes it worth fixing rather
> than documenting: `deepreason results` prints the stored breakdown by
> default and the re-derived one under `--verify`, with no typed statement
> that the two can differ.
