# PARKED — found while preparing the reach-rich run, deliberately not fixed

This tranche is READ-ONLY on `src/` and `tests/` by operator instruction.

---

## P1-reach — `_STRUCTURAL_PROGRAMS` omitting `reasoning-envelope-wf` is what blocks reach in every text run

This is not a new finding. It is
`experiments/2026-08-21-measure-reach-firing/PARKED.md` **P1**, upgraded:
that tranche measured P1 as *latent* ("the direction of this defect is
PERMISSIVE ... Latent, not yet active"). This tranche's rehearsal shows it
is **load-bearing** — it is the single reason a text run cannot produce a
reach event, and fixing it makes one fire on the first attempt.

**The new evidence** (`rehearsal.json`, committed here):

- **S8a** `E4 criterion-fail` — a prose `conn:` candidate carrying novel
  subject criteria is rejected by `reasoning-envelope-wf` before any
  subject criterion is read.
- **S8b** **HIT**, 1 recorded `reach_set` event — the same candidate, same
  criteria, with `reasoning-envelope-wf` counted structural (as
  `programs.PROGRAMS` already declares it). Coverage 2/3.
- **S8c** `E4` — an on-form but off-SUBJECT candidate still does not hit,
  so the fix grounds reach on subject, not on form.

The fix TIGHTENS the substantive/structural boundary. It lowers no
threshold and widens no vocabulary, so it does not relax the Bronze Age
discipline — it applies it to a gate the discipline already names.

```
Route: deepreason-orchestrator (defect).

One goal: make measures/reach.py::_substantive agree with the structural
class programs.PROGRAMS already declares, so a well-formedness gate can
never ground reach or confer prose immunity.

Why this is now urgent rather than latent: reach is Rung 5's nomination
signal, and this defect is the sole reason no text run can produce one.
  - experiments/2026-08-22-live-reach-rich-run/rehearsal.json, scenarios
    S8a / S8b / S8c: the same prose connection candidate against the same
    seed criteria takes exit E4 as shipped and records a full reach hit
    with the fix applied, while an off-subject control still takes E4.
    rehearsal.py simulates the fix by rebinding _STRUCTURAL_PROGRAMS
    in-process; re-run it after the real fix and S8a must become a HIT
    with no in-process rebind (delete the wf_structural argument and the
    two scenarios must agree).
  - experiments/2026-08-21-measure-reach-firing/CENSUS.md, "The qualifying
    vocabulary": reasoning-envelope-wf appears as a QUALIFYING foreign
    criterion in 793 gate pairs across 46 roots.
  - Re-derive the divergence in one command:
      python -c "from deepreason.programs import programs_by_class; from
      deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S;
      d=set(programs_by_class()['structural']); print(sorted(d-S))"
    prints ['component_wf','generator_wf','integration_wf','manifest_wf',
    'reasoning-envelope-wf'].
  - experiments/2026-08-21-measure-reach-firing/probe_immunity.json:
    backed_only_by_declared_structural = 0 over 3528 candidate artifacts,
    so no committed root's adjudication moves. Re-run that probe as the
    before/after measurement.

Read first: docs/map/CON-warrants-and-attacks.md (the "What counts as
substantive rather than structural" row and its check), docs/map/
SUB-evaluation.md Traps ("Structural well-formedness protects nothing"),
docs/map/INV-frozen-surfaces.md.

Design question the tranche must answer, not assume: whether the fix is to
DERIVE _STRUCTURAL_PROGRAMS from programs_by_class()['structural'] (single
source of truth, but it silently re-classifies any future program by its
declaration) or to add the five names and add a gate test asserting the two
sets agree (explicit, but still two sources). CON-warrants-and-attacks.md
line 142 already carries a check over this pair -- extend it either way.

Do NOT lower REACH_COVERAGE_MIN, widen the qualifying vocabulary, or
reclassify any predicate as part of this. The census
(experiments/2026-08-21-measure-reach-firing/DIAGNOSIS.md) already ruled
all three out: E5 coverage rejected 0 pairs and E2 non-qualifying rejected
0 pairs.

End state: the two sets agree by construction or by an asserting test; the
map document's check is extended so a future divergence fails docs_verify;
a regression test names this tranche in its docstring; probe_immunity.py
re-run shows no committed root's formally_backed verdict moved; full gate
0 failed. Then re-run
experiments/2026-08-22-live-reach-rich-run/reach_run.sh to mint the
reach-rich root Rung 5's gate needs.
```

---

## P4-reach — a text run cannot seed a second problem with its own criteria

**What:** `workloads/text.py::seed_reasoning_workload` seeds exactly one
problem, and every route that could add a second with DIFFERENT criteria is
closed: `deepreason amend` copies `criteria=parent_input.problem.criteria`
verbatim (`amendment/apply.py:465-470`), `deepreason input freeze` binds one
run input per root, `deepreason merge` refuses any source carrying `Control`
events (`storage/merge.py:70-78`) and every v6 run is full of them, and
`deepreason run` refuses a non-`text` workload profile, so the multi-problem
`website` decomposition — the only structure that ever recorded reach
(`experiments/gemma4_dna_unattended_2026-07-12`: `pi-plan` / `pi-design` /
`pi-comp-*`, each with its own criteria) — has no launch path.

This is not the blocker for THIS tranche (P1-reach is, and fixing it makes
a single-seed run fire). It is parked because Rung 5 counts reach events
across **distinct problem lineages**, and one seed gives one lineage plus
its own spawn cascade. If `K_frame >= 3`, nomination needs independently
seeded problems and none can be seeded.

```
Route: dr-change-orchestrator (change, design-first -- expect to stop at
SPEC.md and report rather than implement).

One goal: decide and record whether a text run may seed more than one
independent problem, each with its own criteria, and if so through which
surface -- so Rung 5's lineage count can exceed one.

Evidence, already committed:
  - experiments/2026-08-22-live-reach-rich-run/rehearsal.json S3: two
    problems that both carry reasoning-envelope-wf but differ in their
    subject predicates produce a full reach hit. That is the shape a
    multi-seed run would have.
  - experiments/gemma4_dna_unattended_2026-07-12 (out of scope for the
    current reader, kept as an artifact of its own version): the only
    roots that ever recorded reach did it across pi-plan / pi-design /
    pi-comp-* -- separately seeded problems with per-problem criteria.
  - experiments/2026-08-21-measure-reach-firing/VERDICT.md, item 5:
    "the run must seed independent problems rather than rely on the
    connection/integration spawn cascade to manufacture them".

Read first: docs/map/SUB-workloads.md, docs/map/SUB-application.md (the
single run path), docs/map/INV-frozen-surfaces.md, and the operator law
"Operations are available to every configuration" (CLAUDE.md, 2026-08-13):
whatever surface this lands on, it must be ONE run path, not a second one
kept in agreement.

Constraint the tranche must respect, not design around: run identity is
deterministic from question + config, and qualification caches by subject
digest. A multi-problem workload changes what "the question" is, so the
design must say what the run id and the subject digest are functions of.

End state: SPEC.md naming one mechanism (a workload spec carrying several
problems? a typed seed operation on the running root? nothing, with the
reason recorded), its effect on run identity and the qualification subject
digest, and the measurement that would prove it. Implementation only on
explicit operator approval.
```
