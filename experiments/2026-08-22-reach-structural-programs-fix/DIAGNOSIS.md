# Diagnosis: `_STRUCTURAL_PROGRAMS` is a hand-kept second copy of a class `programs.PROGRAMS` already declares, and it has drifted by five names

Primary cause: `programs.PROGRAMS` is the registry where every program
declares its own `class_`; fourteen declare `"structural"`.
`measures/reach.py::_STRUCTURAL_PROGRAMS` is an independently hand-maintained
frozenset that names nine of them. `_substantive` consults only the hand list,
so the five names the hand list never gained — `component_wf`, `generator_wf`,
`integration_wf`, `manifest_wf`, `reasoning-envelope-wf` — are classified
SUBSTANTIVE despite declaring themselves structural. The drift is one-way (the
hand list is a strict subset of the declaration, `hand - declared` is empty),
which is the signature of a copy that was never updated when programs were
added, not of a deliberate disagreement. Two consumers read the wrong answer:
`reach_sweep`, where a declared-structural gate enters the QUALIFYING set and
must therefore be passed for a hit — so a well-formedness gate can both ground
reach and, by failing on prose, veto it; and `rules/warrants.py::formally_backed`
(line 96 imports `_substantive` directly), where a passing declared-structural
gate can confer prose immunity. Both are exactly what the module's own docstring
says must never happen: "structural well-formedness programs ... qualify anything
well-formed and prove nothing about the foreign problem's subject — they never
ground reach."

Evidence:

  - **Re-derived at HEAD `0e8e0f6a6` (not inherited):**

        python -c "from deepreason.programs import programs_by_class; from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; d=set(programs_by_class()['structural']); print('declared-hand', sorted(d-S)); print('hand-declared', sorted(S-d))"
        declared-hand ['component_wf', 'generator_wf', 'integration_wf', 'manifest_wf', 'reasoning-envelope-wf']
        hand-declared []

    and the classification itself, per name:

        reasoning-envelope-wf    declared_class=structural   _substantive=True
        manifest_wf              declared_class=structural   _substantive=True
        component_wf             declared_class=structural   _substantive=True
        generator_wf             declared_class=structural   _substantive=True
        integration_wf           declared_class=structural   _substantive=True
        json-wf                  declared_class=structural   _substantive=False   <- the nine that are listed

  - **`experiments/2026-08-22-live-reach-rich-run/rehearsal.json` (committed,
    typed, this is the load-bearing pointer).** Three scenarios over the REAL
    `reach_sweep` against a real `Harness` root, same candidate and same
    criteria throughout:
      - `S8a prose conn: candidate vs seed (as shipped)` — `exit`
        `"E4 criterion-fail"`, `recorded_reach_events` 0,
        `verdicts["reasoning-envelope-wf"] == "fail"`, `qualifying` contains
        the wf gate. The gate is read BEFORE any subject criterion decides
        anything, and both subject predicates PASS in the same row.
      - `S8b ... (P1 applied)` — `exit` `"HIT full"`,
        `recorded_reach_events` 1, `qualifying` is exactly the two subject
        predicates, `coverage` 0.667.
      - `S8c prose OFF-subject candidate ... (P1 applied)` — `exit`
        `"E4 criterion-fail"`, `recorded_reach_events` 0, both subject
        predicates `fail`. The control proves the fix grounds reach on
        SUBJECT, not on form.

  - **`experiments/2026-08-21-measure-reach-firing/CENSUS.md`, "The qualifying
    vocabulary":** `reasoning-envelope-wf` appears as a QUALIFYING foreign
    criterion in 793 gate pairs across 46 committed roots — the misclassification
    is exercised at corpus scale, not hypothetically.

  - **Consequence baseline re-measured today** (`immunity_before.json`, produced
    by `immunity_delta.py before`, which imports the committed
    `probe_immunity.probe` verbatim rather than copying it): over 3 528
    candidate artifacts on every root carrying a `log.jsonl`,
    `formally_backed` = 903 and `backed_only_by_declared_structural` = 0.
    No committed root's prose-immunity verdict rests solely on a
    declared-structural gate, so narrowing `_substantive` moves none of them.
    This reproduces the committed `probe_immunity.json` totals exactly.

  - **The registry is already the authority for the other consumer with
    teeth.** `rules/guards/anti_relapse.py` reads
    `programs.program_class(...) == "structural"` — the declaration — rather
    than a second list. `measures/reach.py` is the only place that keeps a
    copy.

Implicated code:
  - `src/deepreason/measures/reach.py:37-54` — `_STRUCTURAL_PROGRAMS` and
    `_substantive`. The predicate itself is correct as written; its input set
    is stale.
  - `src/deepreason/rules/warrants.py:96,106` — the second consumer, which
    imports `_substantive` and inherits the same stale set.
  - `src/deepreason/programs.py:337-347` — where the five missing names declare
    `class_="structural"`.

Falsifiable prediction: with the two sets made to agree, and with NO in-process
rebind, re-running `experiments/2026-08-22-live-reach-rich-run/rehearsal.py`
must move S8a from `"E4 criterion-fail"` / 0 events to `"HIT full"` / 1 event,
agreeing row-for-row with S8b (`qualifying` = the two subject predicates,
`coverage` 0.667), while S8c stays `"E4 criterion-fail"` / 0 events; and
re-running `immunity_delta.py after` must report `formally_backed` = 903
unchanged over the same 3 528 candidates.

Ruled out:
  - **"The strictness is what blocks reach; loosen a threshold."** The
    08-21 census re-derived 1 178 430 pairs over 96 roots: `E5 coverage`
    rejected **0** pairs and `E2 non-qualifying` rejected **0** pairs. Neither
    `REACH_COVERAGE_MIN` nor the qualifying filter rejects anything anywhere,
    so lowering either changes nothing. The fix here TIGHTENS the boundary and
    still produces the hit, because the wf gate's removal takes it out of the
    ALL-must-pass set rather than out of a threshold.
  - **"This is the same hole as P2."** It is not, and P2 is not fixed here.
    P2 (`relation_form_commitment`, a form gate spelled `predicate:`) is
    substantive by construction — `_substantive` returns True for EVERY
    `predicate:` commitment and no program-class list can reach it. Confirmed
    still open at HEAD; parked forward in this tranche's PARKED.md.

## Second finding, confirmed, in scope as its own commit (P3)

`reach.py`'s module docstring enumerates three rejection paths (non-qualifying
criteria, no novel criterion, coverage below `coverage_min`). `reach_sweep`
takes five pair-level exits. `CENSUS.md`'s exits table names all five against
the code lines that take them, and the two the docstring omits are the two that
carry most of the corpus: `E1 no-criteria` (`or not problem.criteria`, 285 070
pairs) and `E4 criterion-fail` (the all-PASS check, 585 096 pairs — 100% of
everything reaching the verdict gate). Together 870 166 of 1 178 430 pairs are
rejected by exits the docstring does not mention, so a reader who trusts it
misattributes the census. Documentation-only; no behaviour depends on it.
