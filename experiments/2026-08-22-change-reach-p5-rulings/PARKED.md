# PARKED — noticed during the P5-reach ruling tranche, deliberately not done

One tranche, one goal. Nothing below was fixed here.

---

## P5b — the committed reach census still speaks the pre-E0 vocabulary

**What:** `experiments/2026-08-21-measure-reach-firing/census.py` now knows the
`E0 empty-own-battery` exit, but `census.json` and `census-verdicts.json` were
measured on 2026-08-21, before E0 existed. Pairs a post-E0 reader would put at
E0 are distributed across E1..E5/HIT in those files. How many, over 96 roots,
is unknown. Deliberate (SPEC.md A4): re-deriving is a measurement, not a
vocabulary update, and this tranche was asked for the second.

Whether it is worth measuring is genuinely open, and the honest answer may be
"no": the sweep is retired as an instrument, and E0's blast radius on
committed roots is bounded to attribution — no root's stored verdict, replay
or `verify_root` result moves, because `reach_sweep` is called only by the live
scheduler (SPEC.md M4).

```
Route: dr-change-orchestrator (change, measurement-only -- expect to stop at
SPEC.md and report the price before running anything).

One goal: decide whether the 08-21 reach census is re-derived under the E0
vocabulary, and if so record the new attribution table, so a reader is never
comparing a pre-E0 census against post-E0 code without knowing it.

Evidence, already committed:
  - experiments/2026-08-21-measure-reach-firing/census.py -- the exit ladder
    now carries E0 first, with a note saying the committed JSON predates it.
  - experiments/2026-08-21-measure-reach-firing/census.json,
    census-verdicts.json -- the 2026-08-21 measurement, byte-unchanged.
  - experiments/2026-08-22-change-reach-p5-rulings/SPEC.md A4 and M4 -- why it
    was skipped, and why no root's verdict can move.

Read first: CLAUDE.md's retired-sweep ruling (2026-08-22, "it just wastes
time") -- it is the argument AGAINST doing this, and it should be answered
before any roots are opened. The cheap alternative is a single counter: how
many artifacts across the 96 roots carry an empty interface at all. If that
number is near zero, the question dissolves and the answer is a one-line note.

End state: either the census outputs are re-derived and committed with a
dated segment saying what moved, or a one-line note in census.py records the
decision not to, with the cheap counter as its evidence. Do not re-run the
full verdicts pass without pricing it first.
```

---

## Carried forward, untouched by this tranche

- **P2-reach** (a `predicate:` form gate is substantive by construction) --
  still open at `experiments/2026-08-22-reach-structural-programs-fix/
  PARKED.md`. Re-confirmed open here: rehearsal S5 and S6 still exit `E4
  criterion-fail` on `relation-form@578e42df713e` alone.
- **P6-reach** (`SEAM-evaluation-x-warrants-and-attacks` does not exist) --
  still open at the same place. This tranche read
  `DR-SEAM-evaluation-x-rules` for the same boundary and it served, which is
  one more data point for the "duplicate rather than gap" reading that parked
  prompt asks someone to decide.
