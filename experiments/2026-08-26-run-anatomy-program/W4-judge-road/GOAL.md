# GOAL — W4, the judge-road autopsy (RUN ANATOMY PROGRAM)

**Tranche dir.** `experiments/2026-08-26-run-anatomy-program/W4-judge-road/`
**Dimensions.** D5 (judge activity), D6 (judge form filling), and the
adjudication end of D8 (were commitments attacked correctly).
**Route.** `deepreason-orchestrator`, measurement variant: GOAL → record
census (the `dr-diagnose` slot) → RESULTS.md honest ledger. **READ-ONLY on
`src/` and `tests/`.** No fix phase exists here; defects become PARKED.md
prompts. **Date.** 2026-08-26. **Branch.**
`claude/w4-judge-road-autopsy-754boo`. **Base.** `origin/main` at
`00e3f8afc`.

## Class

capability-gap plus (suspected) defect. Nothing crashed. A configured,
qualified, paid-for adjudication path has never executed, and the
P-R1 tranche's own PARKED P5 says the reason has never been established.

## The three questions

1. **THE STANDING FACT.** Confirm from the records that **no defended
   trial has ever run in this repository** — zero judge calls, zero trial
   observations, zero declines, zero guard blocks — across every committed
   root, not only the roots that report the field. The P5 census covered
   the roots that "report the field"; this one covers all 54 in W1's
   inventory, by re-deriving `_adjudication`'s own counters from
   `log.jsonl` directly.

2. **THE ROAD.** Map the path from "a criticism exists" to "a defended
   trial convenes" as the CODE defines it, gate by gate. Then walk every
   criticism in the two roots the program routes here — P-R1
   (`experiments/2026-08-25-poietics-program/run`) and the
   grounded-extension root
   (`experiments/2026-08-12-live-grounded-extension-expansion/run`, the
   only root W1's inventory marks D5/D6-measurable) — and record where
   each road ended, with the typed reason. Deliverable: a funnel table,
   `N criticisms → N eligible → N sustained → N escalated → 0 trials`,
   with the BINDING GATE named at each stage and the dominant terminator
   identified.

3. **DESIGN OR DEFECT.** For the dominant terminator, say which of three
   it is, with code and record citations:
   - **design** — a threshold nobody crossed (working as specced; the spec
     may still be mis-tuned);
   - **defect** — a gate that cannot be satisfied by any configuration;
   - **gap** — a road never wired end to end.
   Do not fix. A defect becomes a PARKED prompt.

4. **ADJUDICATION QUALITY.** W2 counted 118 mechanical commitment verdicts
   in P-R1 and 345 in P-C1 ARM H
   (`experiments/2026-08-25-change-constructive-frontier/run`) and
   re-derived them with the harness's own evaluator, 463/463 correct. That
   check is CIRCULAR by construction: it re-ran the same evaluator that
   produced the verdict. This tranche checks 30 per root BY HAND against
   the artifact's own bytes — correct / incorrect / ambiguous — stratified
   across criterion families, with verbatim exemplars. 60 rows.

## Success criterion (machine-decidable)

(a) `python3 road_census.py` exits 0 and writes `road_census.json` carrying,
    per root: every criticism dispatch, its parsed cases, the gate each case
    terminated at (one of a CLOSED enumeration derived from
    `rules/crit.py::crit_argumentative`), and the typed evidence for that
    gate from `log.jsonl` / `run-manifest.json` — no gate assigned by
    reading prose.
(b) `python3 trial_sweep.py` exits 0 and writes `trial_sweep.json` proving
    the standing fact over all 54 roots by re-deriving the `_adjudication`
    counters.
(c) `python3 verdict_sample.py` exits 0 and writes `verdict_sample.json`:
    30 verdicts per root, stratified by commitment id, each with the
    artifact's own content bytes, the commitment's `eval` expression, the
    recorded verdict, and the fields a HUMAN needs to rule on it. The hand
    ruling is recorded in `ADJUDICATION_SAMPLE.md`, one row per verdict,
    and is mine, not the script's.
(d) `git diff --stat origin/main -- src/ tests/` prints nothing.

The tranche FAILS honestly if a stage of the road cannot be reconstructed
from the record — e.g. if the log does not distinguish "case declined to
attack" from "case never parsed". An unmeasurable stage is recorded as
unmeasurable, not estimated.

## Map preflight (ids resolved before any measurement)

Per CLAUDE.md MAP PREFLIGHT, seam before subsystems, frozen surfaces before
design:

- `docs/map/INDEX.md` — routing.
- `DR-INV-frozen-surfaces` — read FIRST. **Not applicable by construction**:
  this tranche writes no code under `src/` or `tests/`; the gate is
  `git diff --stat origin/main`.
- `DR-SEAM-adjudication-x-authority` — the seam, read before either side.
  It owns the load-bearing rule this autopsy must not violate in its own
  reasoning: *authority may be consulted where a warrant is MINTED, and
  never where a label is COMPUTED.* Labels are recomputed on every open, so
  a policy consulted at label time retroactively changes what a committed
  root means. Consequence for this census: the road's gates all live at
  MINT sites (`rules/crit.py`, `informal/trial.py`), and `adjudication/`
  imports no authority symbol — so "why no trial" is answerable only
  upstream of `build_att`, never from the label counts.
- `DR-CON-authority` — the authority modes and the master gates.
- `DR-CON-criticism-source` — the socket that attacks a target.
- `DR-SUB-adjudication` — warrants → attack edges → status labels.
- `DR-SEAM-adjudication-x-rules` — the seam the census reads across.
- `DR-CON-warrants-and-attacks` — owns the definition of refutation this
  census must not invent.
- `DR-SUB-evaluation` — the commitment evaluator, for question 4.

## Scope contract

- READ-ONLY on `src/` and `tests/`. Gate: `git diff --stat origin/main`
  names no path under either.
- Committed run roots are never modified; every root is opened
  `read_only=True`.
- **Write ONLY under this directory.** W5 and W6 run concurrently on the
  same branch family; coordination is by directory, never by file.
  `PROGRAM.md` is W1's; a later window appends a dated amendment rather
  than editing it, and this tranche appends nothing.
- Do not re-measure W1/W2/W3. W2 owns the criticism census (targets,
  causal work, label work); this tranche consumes its counts and measures
  only the judge road and the hand-checked adjudication sample.
- One tranche, one goal. Anything else noticed → `PARKED.md` with a
  ready-to-send prompt.
- Model prose is not evidence. Every count traces to `log.jsonl`,
  `objects/`, `run-manifest.json`, `progress.jsonl` or `run-status.json`.
