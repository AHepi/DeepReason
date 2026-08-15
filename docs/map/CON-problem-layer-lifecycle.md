<!-- DR-CON-problem-layer-lifecycle -->
Verified-at: 6a86a1f0
Verify: python -m pytest tests/test_premise_channel.py tests/test_premise_channel_loop.py -q
Owns: src/deepreason/premises.py, src/deepreason/measures/demarcation.py, src/deepreason/measures/attention.py
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

## The rent battery — how a premise falls without anyone attacking it

A premise pays RENT by carrying at least one SUBSTANTIVE commitment;
`measures/demarcation.py::crit` is §6's predicate and `premises.py::
premise_rent_sweep` is the sweep that registers a DEMONSTRATIVE fail warrant
against a premise that pays none. Demonstrative, so it is status-changing under
every authority mode — it is a machine reading of the artifact's own attack
surface, not an argument anyone made — and its validity node ν is an ordinary
registered artifact, so the verdict is attackable like everything else.

The battery's own commitment carries eval kind `demarcation:crit`, which
`programs.evaluate` does not know. That is the design, twice over. A program is
handed `(text, budget, artifact)` and no commitment registry, so no content-only
program can see whether the interface's OTHER commitments forbid anything. And
because an unknown eval kind is not `evaluable`, `reach._substantive` is False
for it — so **carrying the rent battery can never satisfy the rent battery**.

`check: python -c "from deepreason.premises import PREMISE_RENT; from deepreason.measures.reach import _substantive; from deepreason import programs; assert not programs.evaluable(PREMISE_RENT) and not _substantive(PREMISE_RENT)"`
`check: python -m pytest tests/test_premise_channel.py::test_structural_commitments_do_not_pay_rent tests/test_premise_channel.py::test_the_rent_battery_cannot_satisfy_itself tests/test_premise_channel.py::test_a_premise_falls_by_demarcation_with_no_written_refutation -q`

## The producer, wired

The critic's pack gains an INVITATION when the problem it is working has
accumulated `PREMISE_INVITE_AFTER` refuted candidates and carries no standing
attribution. The critic answers in one optional contract field (`premise`) on
its existing contracts — no new role, no new `contract_id`, so no qualification
subject digest moves. `rules/crit.py::_file_attribution` gates registration on
the INVITATION rather than on the field, so a call cannot file work no producer
offered.

The scheduler's three consults are all attention: a `retired` problem leaves
the candidate pool, a marked problem yields one rank position (after the SEED
term, so the operator's question still wins every tie), and the standing
invitation is recorded as a typed Measure — the receipt that says the mechanism
actually ran.

`check: python -m pytest tests/test_premise_channel_loop.py -q`

## The signals

Three detection signals are declared under the signal contract
(`DR-INV-signal-contract`, `DR-REC-add-signal`) and emitted once per cycle: `problem.thrash.v1`,
`criticism.attack-target-entropy.v1`, `problem.independence-resolution-rate.v1`.
Two process receipts ride beside them: `premise.work-invited.v1` and
`premise.attribution-filed.v1`. All five price attention and none may reach a
label.

`check: python -c "from deepreason.signals import declaration; names=['problem.thrash.v1','criticism.attack-target-entropy.v1','problem.independence-resolution-rate.v1','premise.work-invited.v1','premise.attribution-filed.v1']; ds=[declaration(n) for n in names]; assert all(d is not None and d.unit != 'unspecified' and d.staleness != 'unspecified' for d in ds)"`

## Entry points

`standing_attributions`, `premise_orphaned` (problem → grade), `open_orphans`
(marked and unresolved — the work), `standing_resolutions`, `retired_problems`,
`premise_work_invited` (the producer rule), `file_premise` (registers X and ρ),
`premise_rent_sweep` (the demarcation adjudication),
`independence_resolution_rate` (the over-binding diagnostic).

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
- **A filed premise is prose, so it pays no rent, so filing IS the
  accusation.** Under Rung 2 every premise a critic files falls by demarcation,
  because the harness can see an artifact's attack surface and nothing else.
  That is why the contract field means "a presupposition that forbids nothing"
  and not "a presupposition", and why the recourse is threefold and unchanged:
  attack ρ ("the problem never assumed that"), attack ν (the demarcation
  verdict), or attach a substantive commitment to X. What this does NOT give is
  discrimination between a vacuous premise and a true one nobody has
  formalised — that is D-8, open.
- **The invitation is offered inside the RULE, not passed by the scheduler.**
  `_arg_crit`'s call to `crit_argumentative_batch` is keyword-free by seam
  invariant (`DR-SEAM-scheduler-x-rules`), so the rule computes the invitation
  from the record itself. It reads refuted-candidate counts, never a cycle
  count, a cadence or a cap — a fact about the graph, not about attention.
