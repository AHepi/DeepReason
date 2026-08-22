# PARKED — found during the reach structural-set fix, deliberately not fixed

One tranche, one goal. Everything below is a ready-to-send prompt.

---

## P2-reach (CARRIED FORWARD, still open) — a form gate written as `predicate:` is substantive by construction

Carried verbatim in substance from
`experiments/2026-08-21-measure-reach-firing/PARKED.md` P2, and re-confirmed
open at commit `e732d3141`: `_substantive` returns True for EVERY `predicate:`
commitment, so the structural exclusion — now derived from the declared
program class and therefore complete for `program:` evals — still cannot reach
a form gate spelled as a predicate. `relation_form_commitment()`
(`unification/isolation.py:43`) calls itself "Form gate for RELATION
candidates" in its own docstring and carries 584 303 of 585 096 gate pairs
across 86 roots.

**What this tranche adds to the finding.** Two live data points, both from
`experiments/2026-08-22-live-reach-rich-run/rehearsal.json` re-run against the
FIXED code, which the 08-21 census could not produce:

  - S5 and S6 still exit `E4 criterion-fail` on `relation-form@578e42df713e`
    alone. So `relation-form` is doing exactly what a form gate does — being
    the sole qualifying criterion of a connection/integration problem, and
    deciding the pair on shape. Fixing P1 did not touch it, as predicted.
  - S6's coverage is 1/3, below `REACH_COVERAGE_MIN`, so a conn: problem can
    only ever be PROVISIONAL anyway. That bounds P2's blast radius: on
    auto-spawned CONNECTION problems the form gate cannot ground a full hit
    even if it passed. On INTEGRATION problems (S5, coverage 1/1) it can.

```
Route: deepreason-orchestrator (defect, design-first -- expect to stop at
FIX.md and report rather than implement).

One goal: decide and record whether a `predicate:` commitment can be a FORM
gate, and if so how the substantive/structural boundary recognises one, so
reach and prose immunity cannot be grounded on a criterion that checks shape
rather than subject.

Evidence, already committed:
  - experiments/2026-08-21-measure-reach-firing/CENSUS.md, "The qualifying
    vocabulary": relation-form@578e42df713e carries 584 303 of 585 096 gate
    pairs across 86 roots, and its docstring calls it a form gate.
  - probe_novelty.json: the carries x passes 2x2. The hit cell is empty for
    both qualifying criteria -- today's protection is an accident of prompt
    wording, not a mechanism.
  - experiments/2026-08-22-live-reach-rich-run/rehearsal.json (re-run against
    the FIXED code): S5 exits E4 on relation-form alone at coverage 1/1 -- an
    integ: problem whose whole qualifying battery is a form gate. S6 shows
    the conn: case is bounded to PROVISIONAL by coverage 1/3.
  - src/deepreason/measures/reach.py::_substantive -- `kind == "predicate"` is
    never excluded, and after the 2026-08-22 fix the program-class exclusion
    is COMPLETE, so a predicate form gate is now the only remaining hole.

Read first: docs/map/CON-warrants-and-attacks.md, docs/map/SUB-evaluation.md
Traps (the two entries the 2026-08-22 tranche rewrote), docs/map/
SEAM-evaluation-x-rules.md Traps, and the operator law "Formalism is an
option, never an obligation" (CLAUDE.md) -- any design that penalises a
conjecture for its KIND violates it, so a fix must key on what the criterion
CHECKS, not on how the artifact was written.

Do NOT lower any reach threshold as part of this. The Bronze Age postmortem
is why the strictness exists, and the 2026-08-22 census/rehearsal evidence
shows the strictness is not what suppresses hits.

End state: FIX.md naming one mechanism (a declared class on Commitment? a
form-gate marker at mint time? leaving it as-is with the reason recorded),
its blast radius over reach AND formally_backed, and the measurement that
would prove it. Implementation only on explicit operator approval.
```

---

## P5-reach — a prose artifact with an EMPTY own battery now reaches at coverage exactly 0.5

**What:** re-running the rehearsal against the fixed code moved a SECOND
scenario that the fix's pre-registration did not name. `rehearsal.json` S2 — a
prose artifact whose own battery is EMPTY, against a seed problem carrying
`reasoning-envelope-wf` plus one subject predicate — went from `E4
criterion-fail` to `HIT full`, one recorded reach event, coverage exactly
0.500 against a `REACH_COVERAGE_MIN` of 0.5.

This is the SAME mechanism as the fix's target (S8a) and is not a defect on
the evidence available: the criterion it survives is a subject predicate, not
a form gate, and it is genuinely novel to the artifact. It is parked because
two properties of it are unexamined rather than wrong:

  1. **The Bronze Age discipline guards the FOREIGN battery, not the
     artifact's own.** `reach.py`'s docstring says "no reach from an empty,
     trivial, or unguarded battery", and every guard in `reach_sweep` reads
     `problem.criteria`. Whether an artifact carrying NO commitments of its
     own should be able to reach at all is a question the discipline's wording
     raises and the code does not answer. S2's shape may also be a rehearsal
     artefact rather than a shape a live run produces — a real `conn:`
     candidate carries the three auto-spawn commitments (that is S8a).
  2. **Coverage lands exactly ON the floor**, and `reach_sweep` compares with
     `<` (`if len(qualifying) / len(problem.criteria) < coverage_min`), so 0.5
     is a full hit rather than provisional. That boundary is deliberate as
     written; it has simply never been exercised before, because no pair in
     96 committed roots ever reached the coverage gate at all (`E5` = 0).

```
Route: deepreason-orchestrator (defect-or-not, design-first -- expect to stop
at DIAGNOSIS.md and report; it may well be correct as written).

One goal: decide and record whether an artifact carrying an EMPTY own
commitment battery may ground reach, and whether coverage exactly equal to
REACH_COVERAGE_MIN should be a full hit or provisional -- so both answers are
deliberate rather than inherited.

Evidence, already committed:
  - experiments/2026-08-22-live-reach-rich-run/rehearsal.json S2 (post-fix):
    carried=[], qualifying=['uhi-energy-balance@r1'], coverage 0.5, exit
    "HIT full", recorded_reach_events 1.
  - experiments/2026-08-22-reach-structural-programs-fix/rehearsal-as-shipped.json
    S2: the same pair at "E4 criterion-fail" before the fix. The delta is
    entirely the structural reclassification.
  - experiments/2026-08-21-measure-reach-firing/census-verdicts.json: E5
    coverage rejected 0 of 1 178 430 pairs, so the floor has never decided
    anything on a committed root and both readings are currently untested.

Read first: src/deepreason/measures/reach.py (the module docstring's five
exits and the `< coverage_min` comparison), docs/map/SUB-evaluation.md's
"Where to change what" row for the reach coverage threshold, and the Bronze
Age postmortem's wording "no reach from an empty, trivial, or unguarded
battery" -- the question is which battery that sentence is about.

Do NOT change REACH_COVERAGE_MIN's VALUE as part of this. The question is the
comparison and the empty-own-battery case, not the number.

End state: DIAGNOSIS.md recording one of -- (a) correct as written, with the
reason and a regression test pinning both boundaries so they stay deliberate;
(b) the empty-own-battery case should be guarded, with the guard named; (c)
coverage == floor should be provisional. Implementation only on explicit
operator approval.
```

---

## P6-reach — `SEAM-evaluation-x-warrants-and-attacks` does not exist, and this defect sat on it

**What:** `docs/map/SUB-evaluation.md` lists `evaluation x
warrants-and-attacks` under `Seams-undocumented:`, describing it as "real and
already partly evidenced: `rules/warrants.py` imports `oracle.EXEC_PROGRAMS`
and `measures.reach._substantive` directly". That import is precisely the seam
this tranche's defect crossed. The documented seam that DID catch it,
`SEAM-evaluation-x-rules.md`, owns the same files from the rules side, so the
pair may be a duplicate rather than a gap — that is the thing to decide, and
it is cheap.

Not done here because authoring or retiring a map document is a change
tranche, and this was a defect tranche with one goal.

```
Route: dr-change-orchestrator (change, documentation-only).

One goal: decide whether `evaluation x warrants-and-attacks` needs its own
SEAM document or should be struck from SUB-evaluation.md's
Seams-undocumented: line as covered by DR-SEAM-evaluation-x-rules -- so a
future reader doing the map preflight is routed to exactly one document for
the `_substantive` / `EXEC_PROGRAMS` boundary.

Evidence, already committed:
  - docs/map/SEAM-evaluation-x-rules.md `Owns:` names
    src/deepreason/rules/warrants.py, src/deepreason/measures/reach.py and
    src/deepreason/programs.py -- all three files of that boundary.
  - docs/map/SUB-evaluation.md Seams table still lists the pair as
    undocumented.
  - experiments/2026-08-22-reach-structural-programs-fix/FIX.md Amendment 1:
    a tranche read the two subsystem/concept documents, recorded the
    undocumented pair as a finding, and MISSED the documented seam that had
    the whole diagnosis in its Traps section. One boundary described in two
    places, one of them a stub, cost that tranche a phase.

Read first: docs/map/SCHEMA.md (what a seam document must contain and when a
pair is a duplicate), docs/map/INDEX.md's seam matrix.

End state: either SEAM-evaluation-x-warrants-and-attacks.md exists with its
own checks and INDEX.md's matrix row, or SUB-evaluation.md's
Seams-undocumented: line drops the pair with a one-line pointer to
DR-SEAM-evaluation-x-rules and INDEX.md's matrix says so. docs_verify full
and --links both clean either way.
```
