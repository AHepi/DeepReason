<!-- DR-SEAM-evaluation-x-scheduler -->
Verified-at: 5f34e4d00
Verify: python -m pytest tests/test_coverage_pending_commitments.py tests/test_formalism_optional_rank.py -q
Owns:
Seams:
Seams-undocumented:

# evaluation × scheduler — what a verdict MEANS to the thing that ranks on it

## What this seam is

`DR-SUB-evaluation` produces VERDICTS about content. `DR-SUB-scheduler` turns
verdicts into RANK. The whole agreement is one question — *what may a ranking
reader conclude from each verdict?* — and for four months the two sides
answered it differently, in silence, because nothing made the disagreement
visible.

**Measured coupling: 11, and the pair is absent from `INDEX.md`'s seam matrix
anyway.** Counted the way that table counts — directed `deepreason.*` imports
between the files each side declares it `Owns:`, summed both ways — this pair
scores 11, entirely one-directional: `scheduler/scheduler.py` names the
evaluation side eleven times and `programs.py`, `oracle.py`, `measures/` and
`informal/` name the scheduler NOWHERE. Eleven is not a low score. It ties
`harness × workflow` and `rules × scheduler`, both of which have rows. This
pair simply has none — so the omission is a gap in the table, not a verdict of
the metric.

**And the crossing this seam is really about is a TWELFTH one the metric cannot
count at all.** `pareto_scores` reaches the evaluation side by importing the
PACKAGE and attribute-accessing it:

    from deepreason import programs      # then programs.evaluable(...), programs.PASS

A census keyed on `deepreason.<owned-module>` sees `deepreason` and stops. So
the single crossing on which the ranking agreement lives is invisible to the
instrument twice over — function-local AND package-form. That is the third
recorded instance of the shape `INDEX.md` warns about (`llm × verification`,
scored one, and `capabilities × channels`, scored zero) and the third to cost a
live run before anyone wrote the seam down.
`check: python -c "
import re, pathlib
src = pathlib.Path('src/deepreason/scheduler/scheduler.py').read_text()
assert 'from deepreason import programs' in src, 'the package-form import is gone; re-check the census claim'
assert not re.search(r'^from deepreason\.programs import', src, re.M), 'now module-form: the invisibility claim needs rewriting'
own = re.findall(r'^\s*(?:from|import)\s+(deepreason\.(?:programs|oracle|oracle_sandbox|measures|informal)[A-Za-z0-9_.]*)', src, re.M)
assert len(own) == 11, f'coupling moved: {len(own)} crossings, document says 11'
"`

## The two crossing families

**1. Criticism dispatch (eleven crossings, three of them module-level).** The
scheduler calls the evaluation side to DO work: `measures.hv.run_hv_floor`,
`measures.reach.reach_sweep`, `measures.attention`, `informal.trial.run_trial`
and `pairwise_discriminate`, `informal.audits.paraphrase_invariance_audit`,
`oracle.EXEC_PROGRAMS` and `PROPERTY_PROGRAM`. Ordinary collaboration: the
scheduler decides WHEN and HOW OFTEN, evaluation decides WHAT THE ANSWER IS.

**2. Ranking (one crossing, invisible).** Three symbols, all inside
`pareto_scores`, reached through the package-form import above. This is the
family that carries the agreement, because here the scheduler does not
dispatch work — it INTERPRETS a verdict.

| symbol | from | what the scheduler does with it |
|---|---|---|
| `programs.evaluable(commitment)` | `programs.py:533-537` | decides whether a commitment can enter the coverage battery at all |
| `programs.evaluate(commitment, artifact, blobs)` | `programs.py:540-...` | obtains the verdict, freshly, on every report |
| `programs.PASS` / `programs.OVERRUN` | `programs.py:24` | the numerator, and what leaves the denominator |

## The agreement, in one sentence each

- **`PASS` and `FAIL` are DECISIONS about the content.** They may be counted
  for or against the artifact.
- **`OVERRUN` is the ABSENCE of a decision** — a sandbox kill, a watchdog, an
  unusable checker, a missing spec, an observation awaiting registered
  evidence, a Lean proof deferred to its external verifier. `DR-SUB-evaluation`
  states it as "no `fail` warrant may be minted from one". The scheduler side
  of that same sentence is: **no rank penalty may be derived from one either.**
  A verdict that says nothing must move no coordinate.
- **The scheduler re-evaluates rather than reading a stored verdict.** Verdicts
  are pure functions of content (`programs.py` §0 determinism), so recomputing
  is safe; but it also means the ranking plane sees every verdict the
  evaluation plane can produce, including ones no warrant path ever consumes.
  A new OVERRUN site therefore reaches rank immediately, with no event, no
  schema change and no test that mentions the scheduler.
`check: python -c "
import inspect
from deepreason.scheduler.scheduler import pareto_scores
src = inspect.getsource(pareto_scores)
assert 'programs.OVERRUN' in src, 'the ranking side no longer names the absent-verdict case'
assert 'programs.PASS' in src
"`

## Which fraction of each side is involved

Small, and that is why it hid. Of `DR-SUB-evaluation`'s surface only the
verdict vocabulary and two functions cross; of `DR-SUB-scheduler`'s only
`pareto_scores` (about 20 lines of a 3 000-line module) reads them. Everything
else in both subsystems is untouched by this agreement — which is exactly the
condition under which a seam gets no document and then breaks.

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| add a program that can return `OVERRUN` | `programs.py` `PROGRAMS`/`BLOB_PROGRAMS`, or the delegate module | `tests/test_coverage_pending_commitments.py` — confirm the new OVERRUN leaves the denominator rather than depressing rank |
| change what `coverage` divides by | `scheduler/scheduler.py::pareto_scores` only | `tests/test_coverage_pending_commitments.py`, `tests/test_formalism_optional_rank.py` |
| add a Pareto axis | `config.py` `PARETO_AXES` **and** `tests/test_formalism_optional_rank.py`'s `COMMITMENT_FREE_CAN_REACH_THE_FLOOR` table, which goes red until the new axis is annotated | both files above |
| add a fourth verdict | **do not** — `DR-SEAM-evaluation-x-ontology`'s check forbids `programs.py` from naming `Verdict` and pins the three values against `ontology.Verdict` | — |

## Invariants

- `DR-INV-frozen-surfaces` — neither side of this seam is frozen. No frozen
  path names `pareto`, and the coverage number enters no manifest, no
  qualification subject and no replay rule: `verification/report.py` checks
  `run-result.json` for schema and bounds only and never mentions `frontier`,
  `pareto` or `survivors`.
`check: ! grep -rlq "pareto" src/deepreason/run_manifest.py src/deepreason/qualification.py src/deepreason/invariants.py src/deepreason/verification/ src/deepreason/capabilities/state.py src/deepreason/harness.py && ! grep -qE "frontier|pareto|survivors" src/deepreason/verification/report.py`
- Ranking is EFFICIENCY, never EVIDENCE. Nothing crossing this seam may move a
  Status, a warrant or an admission — only which artifact gets attention next.
`check: python -m pytest tests/test_coverage_pending_commitments.py::test_status_unchanged_by_the_coverage_axis -q`

## Traps

- **The ranking plane escaped a rule that was stated only in the warrant
  plane.** `DR-SUB-evaluation` had said since its writing that "no `fail`
  warrant may be minted from an `overrun`". `pareto_scores` minted one anyway,
  arithmetically: it kept OVERRUN in the coverage denominator while counting
  only `PASS` in the numerator, so an artifact was charged for every
  countercondition awaiting evidence and every Lean commitment awaiting its
  verifier. Because the rule named WARRANTS, no check on either side covered
  the ranking consumer. Live cost, measured on three committed roots — P-S1
  `9e48a36b1dec91ee` (98 survivors / 58 on the frontier), P-A1
  `4565139800f5ca02` (11 / 7), P-R1
  `experiments/2026-08-25-poietics-program/run` (58 / 40): the Pareto frontier
  was **100% harness-minted and 0% seed-answering on all three**, with zero
  FAIL verdicts anywhere to explain it. FIXED 2026-09-02
  (`experiments/2026-09-02-defect-coverage-pending-commitments/`). The enduring
  rule: when a subsystem states a rule about one KIND of consumer, ask which
  other kinds exist — an arithmetic consumer breaks a rule phrased for a
  semantic one without ever naming it.
`check: python -m pytest tests/test_coverage_pending_commitments.py -q`
- **A regression test that builds its own fixture can pin a shape the harness
  rewrites away.** `tests/test_formalism_optional_rank.py` guarded this exact
  axis and stayed green for four months while three live roots inverted,
  because it constructed its pending commitment as `eval="observation"` — which
  `programs.evaluable` screens out BEFORE the battery — while
  `workloads/text.py` rewrites every live declaration into
  `program:reasoning_observation_pending`, which it does not. Two spellings of
  one idea, one protected road and one penalised road, and the test took the
  road no artifact travels. When guarding a value the harness NORMALISES,
  construct the fixture through the normalising function, or assert both
  spellings; that test now does the latter.
`check: python -m pytest "tests/test_coverage_pending_commitments.py::test_the_minted_spelling_is_the_one_scored_here" -q`
