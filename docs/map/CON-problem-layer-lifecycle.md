<!-- DR-CON-problem-layer-lifecycle -->
Verified-at: f34cefe4
Verify: python -m pytest tests/test_premise_channel.py -q
Owns: src/deepreason/premises.py
Seams: 
Seams-undocumented: rules x problem-layer-lifecycle, scheduler x problem-layer-lifecycle

# The problem layer — how a question is criticised, marked, and replaced

## What it is

A problem is not an artifact. It has no status, it is never in `att` or `dep`,
and nothing can attack one. What can be criticised is what a problem takes for
granted; the problem's consequence is a MARK, and a mark has three legal
answers rather than a truth value.

Three ordinary artifacts carry the whole layer. A **premise** is the claim the
problem assumes. An **attribution** says "problem π has premise X". A
**resolution** is one of retire / translate / independence. None is a type: an
artifact is an attribution because it carries `program:presupposition_wf`, which
is dispatch on interface structure, the same move `skeleton_wf` already makes.

`check: python -c "from deepreason.premises import ATTRIBUTION_EVAL, RESOLUTION_EVAL; assert ATTRIBUTION_EVAL == 'program:presupposition_wf' and RESOLUTION_EVAL == 'program:premise_resolution_wf'"`

## The two locks

A problem is marked only when the attribution **stands unrefuted** AND the
premise **has fallen**. Either alone moves nothing: filing an attribution is not
criticising the premise, and refuting a claim does not orphan every problem that
might arguably have rested on it. Attacking the attribution releases the problem
without anyone rescuing the premise.

`check: python -m pytest tests/test_premise_channel.py::test_an_attribution_alone_marks_nothing tests/test_premise_channel.py::test_a_refuted_premise_alone_marks_nothing tests/test_premise_channel.py::test_attacking_the_attribution_releases_the_problem -q`

## State it owns

**None that persists.** `premise_orphaned` is a pure function of replayed state
(C4), which is also what makes the cascade lazy: a premise shared by a thousand
problems costs nothing when it falls until someone asks about a given problem —
§9.8's "its thousandfold consequence is paid as the frontier is touched, not all
at once". Support propagation would be eager and was rejected for that reason.

## Entry points

`standing_attributions`, `premise_orphaned` (problem → grade), `open_orphans`
(marked and unresolved — the work), `standing_resolutions`, `retired_problems`,
`premise_work_invited` (the producer rule).

## Invariants

- **N1/N3.** Every step is reversible because every step is an artifact:
  attacking a retirement returns its problem to the frontier; defeating the
  premise's critic un-marks the problem by the same computed predicate. No
  resolution asserts insolubility.
- **H1.** Nothing here mints a problem from a conjecture's failure. `translate`
  is the only path that mints a problem, and it fires from an adjudicated
  resolution, not from a refutation.
- **C5.** The producer redirects attention only, and carries no penalty for a
  critic who declines.

`check: python -m pytest tests/test_premise_channel.py::test_the_siren_case_end_to_end tests/test_premise_channel.py::test_translate_is_the_only_replacement -q`

## Traps

- **The mention law is the whole separation.** An attribution that
  `dependence`-refs its premise falls with it, so the cascade would disarm
  itself at exactly the moment it is needed. `presupposition_wf` rejects it.
`check: python -m pytest tests/test_premise_channel.py::test_an_attribution_may_not_depend_on_its_premise -q`
- **Both programs are STRUCTURAL.** They prove an attribution or resolution is
  well formed, never that its claim holds — so they are in
  `measures/reach.py::_STRUCTURAL_PROGRAMS`, ground no reach, and confer no
  prose immunity. Were they substantive, an artifact could immunise itself by
  attaching one.
`check: python -c "from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; assert {'presupposition_wf','premise_resolution_wf'} <= S"`
- **Independence does not un-mark.** It closes the orphan as WORK; the mark
  itself is still computed from the log, because the problem's own record is
  never mutated. Read `open_orphans`, not `premise_orphaned`, when asking what
  is outstanding.
