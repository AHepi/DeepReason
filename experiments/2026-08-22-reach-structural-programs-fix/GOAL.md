# Goal: make `measures/reach.py::_substantive` agree with the structural class `programs.PROGRAMS` already declares

Class: defect

Observed: `programs.PROGRAMS` declares 14 programs `class_="structural"`;
`measures/reach.py::_STRUCTURAL_PROGRAMS` hand-lists 9 of them, so
`_substantive` classifies the other five — `component_wf`, `generator_wf`,
`integration_wf`, `manifest_wf`, `reasoning-envelope-wf` — as SUBSTANTIVE.
Re-derived at HEAD `0e8e0f6a6`:

    python -c "from deepreason.programs import programs_by_class; from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; d=set(programs_by_class()['structural']); print(sorted(d-S))"
    -> ['component_wf', 'generator_wf', 'integration_wf', 'manifest_wf', 'reasoning-envelope-wf']

Record evidence that this is load-bearing rather than cosmetic:

  - `experiments/2026-08-22-live-reach-rich-run/rehearsal.json` S8a / S8b /
    S8c: the SAME prose `conn:` candidate against the SAME seed criteria
    takes exit `E4 criterion-fail` as shipped (S8a, `reasoning-envelope-wf`
    verdict `fail`), records one full reach hit with the five names counted
    structural (S8b, coverage 2/3, `recorded_reach_events` = 1), and an
    on-form but OFF-SUBJECT control still takes `E4` under the same
    treatment (S8c). Nothing is manufactured: the fix grounds reach on
    subject, not on form.
  - `experiments/2026-08-21-measure-reach-firing/CENSUS.md`, "The qualifying
    vocabulary": `reasoning-envelope-wf` is a QUALIFYING foreign criterion
    in 793 gate pairs across 46 roots.
  - `experiments/2026-08-21-measure-reach-firing/probe_immunity.json`:
    `backed_only_by_declared_structural` = 0 over 3 528 candidate
    artifacts, so no committed root's `formally_backed` verdict rests
    solely on a declared-structural gate and none can move.

The documented guarantee this contradicts is stated in three committed
places: `measures/reach.py`'s own module docstring ("structural
well-formedness programs ... never ground reach"),
`docs/map/SUB-evaluation.md` Traps ("Structural well-formedness protects
nothing and proves nothing"), and `docs/map/CON-warrants-and-attacks.md`
("Evaluable is not enough — the commitment must be SUBSTANTIVE").

Success criterion (machine-decidable):

    1) python -c "from deepreason.programs import programs_by_class; from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; d=set(programs_by_class()['structural']); raise SystemExit(0 if d == set(S) else 1)"
       -> exit 0 (the two sets agree; today it exits 1)

    2) python experiments/2026-08-22-live-reach-rich-run/rehearsal.py   # with no in-process rebind
       -> S8a exit == "HIT full", recorded_reach_events == 1, agreeing with S8b
       -> S8c exit == "E4 criterion-fail", recorded_reach_events == 0

    3) python -m pytest tests/test_reflexive_discipline.py tests/test_prose_refutation_boundaries.py tests/test_oracle.py -q
       -> 0 failed, including a new regression test that a DECLARED-structural
          program never satisfies `_substantive` (mutation-proven)

    4) python -m pytest tests/ -q -n 4        -> 0 failed
       python tools/docs_verify.py            -> no NEW failures beyond the 3
          known pre-existing CON-run-identity.md shallow-clone failures

In scope:
  - `src/deepreason/measures/reach.py` (`_STRUCTURAL_PROGRAMS`, `_substantive`,
    and the module docstring's exit enumeration)
  - `tests/` — targeted regressions only
  - `docs/map/SUB-evaluation.md` and `docs/map/CON-warrants-and-attacks.md`
    (the checks over this pair, plus a Traps entry naming this tranche)

NOT in scope:
  - **P2** from `experiments/2026-08-21-measure-reach-firing/PARKED.md`: a
    `predicate:` form gate is substantive by construction and no program-class
    list can catch it. Explicitly parked forward, not fixed here.
  - `REACH_COVERAGE_MIN`, the qualifying vocabulary, and
    `rules/warrants.py::formally_backed`'s own logic — the census already
    ruled all three out (E5 coverage rejected 0 pairs, E2 non-qualifying
    rejected 0 pairs).
  - Frames / standing / `calculus/` — a parallel window owns Rung 4. If the
    fix reaches frame or standing code, STOP.
  - The retired root sweep (CLAUDE.md operator ruling 2026-08-22).

Also in scope IF the diagnosis confirms it, as its own finding:
  - **P3** from the same PARKED.md: `reach.py`'s module docstring names three
    rejection exits; `reach_sweep` takes five. Documentation-only.

Map preflight (ids resolved before any design):
  - `DR-SUB-evaluation` — `Owns: src/deepreason/measures/`; carries the
    "Which criteria are too weak to ground reach" row and the Traps entry
    "Structural well-formedness protects nothing and proves nothing".
  - `DR-CON-warrants-and-attacks` — owns "What counts as substantive rather
    than structural"; its line-142 check already asserts over this pair.
  - `DR-INV-frozen-surfaces` — READ. `measures/reach.py` is on NONE of the
    five frozen surfaces (state digests, harness event application,
    replay-validation formats, manifest schemas, qualification subjects).
    The reach measure writes a Measure event through the existing
    `record_measure` surface, which this tranche does not touch.
  - SEAM finding, recorded not blocking: the pair `evaluation x
    warrants-and-attacks` is listed `undocumented` in `SUB-evaluation.md`'s
    seams table, and it is exactly the seam this defect sits on
    (`rules/warrants.py` imports `measures.reach._substantive`). Both sides
    already carry the load-bearing claim and an executable check over it, so
    this tranche extends those checks rather than authoring a new seam
    document; authoring `SEAM-evaluation-x-warrants-and-attacks.md` is
    parked forward.

Budget: <=150 changed lines, commits at every phase boundary
Stop conditions inherited from orchestrator: yes
