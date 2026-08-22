# Fix: derive reach's structural set from the class `programs.PROGRAMS` declares, instead of keeping a second hand-written copy of it

Guarantee restored: a program that declares itself `class_="structural"` can
never ground reach and can never confer prose immunity — with no second list
that has to be remembered.

## The design question the tranche had to answer

`PARKED.md` P1 named two candidate shapes and forbade assuming one:

  **(a) DERIVE** `_STRUCTURAL_PROGRAMS` from `programs_by_class()["structural"]`
  — one source of truth, but a future program is then classified by its own
  declaration with no separate review step.

  **(b) ADD THE FIVE NAMES** and add a gate test asserting the two sets agree
  — explicit, but still two sources, so the test is the only thing standing
  between them and the next drift.

**Chosen: (a) DERIVE.** The reasons are evidence, not preference:

  1. The defect IS the second source. `hand - declared` is empty and
     `declared - hand` is five (REPRO.md R1): a strict subset, the exact
     signature of a copy that was never updated. (b) leaves that failure mode
     in place and only shortens the time to detection; (a) removes the class
     of defect.
  2. The registry is already the authority for the classification's other
     consumer with teeth — `rules/guards/anti_relapse.py` reads
     `programs.program_class(...) == "structural"`, not a list.
     `measures/reach.py` was the only place holding a copy.
  3. The one genuine cost of (a) is that declaring a new program `structural`
     silently narrows what can ground reach. That direction is SAFE: it makes
     the harness stricter, and permissiveness — a form gate grounding reach —
     is the Bronze Age failure mode the discipline exists to prevent. A
     mis-declaration under (a) costs a missed hit; the same mistake under
     today's code costs a manufactured one.
  4. `src/deepreason/calculus/programs.py` already documents its own programs
     as "STRUCTURAL in the exact sense `measures/reach.py::_STRUCTURAL_PROGRAMS`
     means", so the declaration and the reach set were always intended to be
     the same set. (a) makes the code say what the docs already say.

A pinned name-list assertion in a test was CONSIDERED AND REJECTED: it would
fail whenever any window registers a new structural program (a parallel window
owns Rung 4 and `calculus/`), turning a correct registration into a broken
gate in someone else's tranche. The check that replaces it can only fail if a
second source is reintroduced, which is the thing actually being prevented.

## Change sites (exhaustive)

  - `src/deepreason/measures/reach.py:34-48` — `_STRUCTURAL_PROGRAMS` becomes
    `frozenset(programs.programs_by_class()["structural"])`. The NAME is kept:
    four committed consumers read it (`docs/map/CON-warrants-and-attacks.md`
    line 142's check, `docs/map/SUB-evaluation.md` line 177's check,
    `tests/test_decommissioned_pipeline_stays_out.py:74`, and
    `experiments/2026-08-21-measure-reach-firing/probe_immunity.py`), and
    renaming it would break them for no gain. `_substantive` itself is
    unchanged — its input set was stale, not its logic.
    Import-time derivation is safe: `PROGRAMS` is never mutated after import
    (grep over `src/` and `tests/` finds no `update`/`pop`/`setitem`).
    The per-name rationale comments are PRESERVED, restated as properties of
    the class rather than as a list — including the `frame_assertion_wf` one
    (an artifact that could ground reach by being a well-formed frame
    assertion would let the standing axis buy its own promotion case), which
    belongs to the parallel Rung-4 window and is not mine to drop.

  - `src/deepreason/programs.py:39-41` (`ProgramSpec` docstring) and
    `:366-367` (`programs_by_class` docstring) — `class_` acquires a SECOND
    consumer with teeth. The current text ("reporting and scheduling facts …
    never feeds adjudication") becomes false the moment reach derives from it,
    and a docstring that is false is worse than one that is narrow. Both are
    rewritten to name both consumers. No behaviour, no signature, no
    registration changes.

  - `tests/test_reflexive_discipline.py` — two regressions:
      1. `test_declared_structural_programs_are_never_substantive` — every
         program in `programs_by_class()["structural"]` fails `_substantive`,
         and the two sets are equal. Written over the DECLARATION, so
         registering a new structural program keeps it passing.
      2. `test_a_well_formedness_gate_cannot_veto_a_reach_hit` — the REPRO R2
         shape end-to-end through the real `reach_sweep`: a prose candidate on
         a structural-only home battery, a foreign problem carrying
         `reasoning-envelope-wf` plus two subject predicates it satisfies,
         asserting one full hit, the addressing record, and — the control —
         that an OFF-SUBJECT candidate against the identical batteries still
         does not hit.

  - `tests/test_prose_refutation_boundaries.py` — one regression:
    `test_a_declared_structural_program_confers_no_formal_backing` — the
    second consumer (REPRO R3): an artifact whose only commitment is a PASSING
    `program:reasoning-envelope-wf` is not `formally_backed`. The file's
    existing `test_a_structural_program_confers_no_formal_backing` covers
    `json-wf`, a name the hand list already had; this covers the declaration.

  - `docs/map/SUB-evaluation.md` — the Traps entry "`ProgramSpec.class_` and
    `external_toolchain` are reporting facts only" is rewritten to name both
    consumers with teeth, and its check updated to the new docstring text; the
    "Structural well-formedness protects nothing" Traps entry gains the trap
    for THIS tranche (the two-sources recurrence, with its run-free evidence
    pointers) and a check that the sets agree by construction.

  - `docs/map/CON-warrants-and-attacks.md:142` — the existing check over
    `_substantive` / `_STRUCTURAL_PROGRAMS` / `EXEC_PROGRAMS` is extended to
    assert set equality with the declared class and that a declared-structural
    commitment is not substantive. Extended, not replaced: every assertion it
    already makes still runs.

  - `src/deepreason/measures/reach.py:1-25` (module docstring) — **P3, its own
    commit.** The docstring names three rejection paths; `reach_sweep` takes
    five. Rewritten to enumerate all five in the order the code takes them,
    using `CENSUS.md`'s recorded taxonomy (E1 no-criteria, E2 non-qualifying,
    E3 no-novel, E4 criterion-fail, E5 coverage/provisional), plus a check in
    `SUB-evaluation.md` that fails if a sixth exit is added without being
    documented. No behaviour change.

## Regression artifact

  - `experiments/2026-08-22-reach-structural-programs-fix/repro.py` must
    invert: exit 0, all three of R1/R2/R3 `HOLDS`.
  - `experiments/2026-08-22-live-reach-rich-run/rehearsal.py` re-run with the
    `wf_structural` parameter and its two call-sites DELETED — S8a must become
    `"HIT full"` / 1 event and agree row-for-row with S8b, S8c must stay
    `"E4 criterion-fail"` / 0 events. The pre-fix `rehearsal.json` is copied
    to this tranche as `rehearsal-as-shipped.json` before the re-run so the
    before/after sit side by side in the working tree, not only in git history.
  - `immunity_delta.py after` must report `formally_backed` = 903 over 3 528
    candidates, unchanged from `immunity_before.json`, and
    `declared_minus_reach` = `[]`.
  - Mutation proof for both new discipline tests: restore the old hand list in
    a SCRATCH copy of `reach.py`, watch each go RED, restore, paste both runs
    into VERIFY.md.

## Existing tests at risk

From `grep -rln` over `tests/` for the five names, plus every consumer of
`_substantive` / `formally_backed`:

  - `tests/test_decommissioned_pipeline_stays_out.py:74-76` — asserts
    `EXEC_PROGRAMS` and `_STRUCTURAL_PROGRAMS` are disjoint. MUST KEEP
    PASSING, and does by construction: `exec_oracle`/`property_oracle` declare
    `class_="execution"` and `dataset_oracle` is in `BLOB_PROGRAMS`, not
    `PROGRAMS`. Verified before the change.
  - `tests/test_prose_refutation_boundaries.py` (whole file) — the immunity
    surface. MUST KEEP PASSING; the fix only removes protection, never adds it.
  - `tests/test_reflexive_discipline.py` (whole file) — the reach surface.
    MUST KEEP PASSING.
  - `tests/test_oracle.py`, `tests/test_experiment.py`, `tests/test_imports.py`,
    `tests/test_chunked.py`, `tests/test_website_concurrency.py`,
    `tests/test_compat_eval.py`, `tests/test_replay_reasoning.py`,
    `tests/test_workload_text.py` — these reference the five programs, but each
    asserts a program's OWN verdict, not `_substantive` or `formally_backed`.
    Expected to keep passing unchanged; all are in the iteration ring and any
    failure is a finding, not a fixture to edit.

No fixture is expected to need updating. If one does, it is a defect-dependent
fixture and FIX.md did not predict it — that is a STOP, not a quiet edit.

## Explicitly not changed

  - **P2** (`experiments/2026-08-21-measure-reach-firing/PARKED.md`): a form
    gate spelled `predicate:` is substantive by construction, and no
    program-class list can catch it. `relation_form_commitment()` carries
    584 303 of 585 096 gate pairs. Untouched, re-confirmed open, parked forward
    in this tranche's PARKED.md. Fixing P1 does not touch P2 and must not
    pretend to.
  - `REACH_COVERAGE_MIN`, the qualifying vocabulary, and `reach_sweep`'s
    novelty/survival logic. The census rejected 0 pairs at both E2 and E5;
    there is nothing there to fix, and loosening either is the Bronze Age
    mistake.
  - `rules/warrants.py` — it consumes `_substantive` and is corrected by the
    same change. Editing it too would be two fixes for one cause.
  - `calculus/`, frames, standing — the parallel Rung-4 window owns them.
    `frame_assertion_wf` is already in BOTH sets at HEAD, so this fix does not
    move it.

## Approval gate

Class `defect` (GOAL.md). No frozen surface: `INV-frozen-surfaces.md` lists
five (state digests, harness event application, replay-validation formats,
manifest schemas + validators, qualification subjects) and `measures/reach.py`
is on none. The record FORMAT is untouched — the fix changes which Measure
events get written, which is the measure's purpose, not its wire contract.

Estimated diff: ~125 lines across 6 files (2 src, 2 tests, 2 map), plus this
tranche's own artifacts. Under the 150-line budget. Proceed to
`dr-implement-fix`.

---

## Amendment 1 (during dr-implement-fix): a change site FIX.md missed

`python tools/docs_verify.py` failed on a FOURTH document beyond the three
this FIX.md named:

    FAIL SEAM-evaluation-x-rules.md:259
      assert _STRUCTURAL_PROGRAMS < reg; gap=sorted(reg-_STRUCTURAL_PROGRAMS);
      assert gap==['component_wf','generator_wf','integration_wf','manifest_wf',
                   'reasoning-envelope-wf']
      -> AssertionError

`docs/map/SEAM-evaluation-x-rules.md` `Owns:` exactly the three files this
tranche touches — `rules/warrants.py`, `measures/reach.py`, `programs.py` —
and its `Traps` section already carries this defect, written up on
2026-07-10/11 with the drift dated to commit `1634b35f`. Its check ASSERTS THE
DIVERGENCE deliberately: "The check below asserts the divergence as it stands
today, so closing the gap fails it and forces this paragraph to be rewritten."
The check did its job.

**Owning the miss plainly:** GOAL.md's map preflight read `SUB-evaluation.md`,
`CON-warrants-and-attacks.md` and `INV-frozen-surfaces.md`, and recorded the
undocumented `evaluation x warrants-and-attacks` pair as a finding. It never
read `SEAM-evaluation-x-rules.md`, which is the DOCUMENTED seam owning all
three files. `dr-drive-harness` §4 step 3 says to read the seam document
BEFORE either subsystem, and that is the step that was skipped. The trap had
the whole diagnosis in it — the five names, the two-consumer split, the
originating commit — a day of work before this tranche started.

**The additional change site:**

  - `docs/map/SEAM-evaluation-x-rules.md` Traps, the entry "The registry's
    'structural' and the seam's 'structural' are two different sets" — rewritten
    to say it WAS true and when it was fixed, per the map rule that a Traps
    entry is never deleted. Its check is inverted from asserting the divergence
    to asserting the agreement, so the entry cannot silently rot back.

**The one substantive question the trap raises, answered:** it recorded a
residue — "whether these five *should* be structural for backing is an
operator's call, not an implementer's" — and correctly refused to decide it.
That call has since been made, by the operator, in this tranche's own brief:
"make measures/reach.py::_substantive agree with the structural class that
programs.PROGRAMS already declares, so a well-formedness gate can never ground
reach or confer prose immunity." The residue is discharged by authority, not by
an implementer's judgement, and the rewritten entry records that it was.

The trap's other residue — "no recorded root has been shown to carry a passing
`manifest_wf` that then defeated a prose case" — is now measured rather than
open: `immunity_before.json` puts `backed_only_by_declared_structural` at 0
over 3 528 candidate artifacts on every root carrying a `log.jsonl`. It never
happened, and after the fix it cannot.

Revised estimated diff: ~140 lines across 7 files (2 src, 2 tests, 3 map).
Still under the 150-line budget; re-checked mechanically with
`tools/diff_budget.py` before the commit.
