# PARKED — found during the reach-firing measurement, deliberately not fixed

This tranche is READ-ONLY on `src/` and `tests/` by operator instruction.
Every finding below is a ready-to-send prompt for a future window.

---

## P1 — `_STRUCTURAL_PROGRAMS` hand-lists 8 of the 13 programs `programs.PROGRAMS` declares structural

**What:** `programs.PROGRAMS` carries a declared `class_` per program;
13 are declared `"structural"`. `measures/reach.py::_STRUCTURAL_PROGRAMS`
is a hand-maintained frozenset naming 8 of them. Five declared-structural
programs are missing from it — `component_wf`, `generator_wf`,
`integration_wf`, `manifest_wf`, `reasoning-envelope-wf` — so `_substantive`
classifies all five as SUBSTANTIVE. Two consumers read that verdict:
`reach_sweep` (a substantive criterion can ground reach and register
addressing) and `rules/warrants.py::formally_backed` (prose immunity). The
direction of this defect is PERMISSIVE — it is the Bronze Age failure mode,
not the cause of the zero. Measured effect in the committed corpus:
`reasoning-envelope-wf` was treated as a qualifying foreign criterion in
793 gate pairs across 46 roots, and 0 artifacts currently gain prose immunity
solely from a declared-structural program (`probe_immunity.json`:
`backed_only_by_declared_structural` = 0). Latent, not yet active.

```
Route: deepreason-orchestrator (defect).

One goal: make measures/reach.py::_substantive agree with the structural
class programs.PROGRAMS already declares, so a well-formedness gate can
never ground reach or confer prose immunity.

Evidence, already committed:
  - experiments/2026-08-21-measure-reach-firing/CENSUS.md, section "The
    qualifying vocabulary": reasoning-envelope-wf appears as a QUALIFYING
    foreign criterion in 793 gate pairs across 46 roots.
  - Re-derive the divergence in one command:
      python -c "from deepreason.programs import programs_by_class; from
      deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S;
      d=set(programs_by_class()['structural']); print(sorted(d-S))"
    prints ['component_wf','generator_wf','integration_wf','manifest_wf',
    'reasoning-envelope-wf'].
  - experiments/2026-08-21-measure-reach-firing/probe_immunity.json:
    backed_only_by_declared_structural = 0 over 3528 candidate artifacts,
    so no committed root's adjudication moves if this is fixed. Re-run that
    probe as the before/after measurement.

Read first: docs/map/CON-warrants-and-attacks.md (the "What counts as
substantive rather than structural" row and its check), docs/map/
SUB-evaluation.md Traps ("Structural well-formedness protects nothing"),
docs/map/INV-frozen-surfaces.md.

Design question the tranche must answer, not assume: whether the fix is to
DERIVE _STRUCTURAL_PROGRAMS from programs_by_class()['structural'] (single
source of truth, but it silently re-classifies any future program by its
declaration) or to add the five names and add a gate test asserting the two
sets agree (explicit, but still two sources). CON-warrants-and-attacks.md
line 142 already carries a check over this pair — extend it either way.

End state: the two sets agree by construction or by an asserting test; the
map document's check is extended so a future divergence fails
docs_verify; a regression test names this measurement tranche in its
docstring; probe_immunity.py re-run shows no committed root's
formally_backed verdict moved; full gate 0 failed.
```

---

## P2 — a form gate written as `predicate:` is substantive by construction, and no program-class list can catch it

**What:** `relation_form_commitment()`
(`unification/isolation.py:43`) calls itself "Form gate for RELATION
candidates" in its own docstring, and is spelled
`predicate:'refuted if' in content.lower() and any(...)`. `_substantive`
returns True for EVERY `predicate:` commitment — the structural exclusion
list can only reach `program:` evals. So the single most common criterion in
the corpus (584 303 of 585 096 gate pairs, 86 roots) is a form gate that the
reach discipline treats as substantive. It grounds no reach today only
because passing it is equivalent to carrying it (`probe_novelty.json`:
`carries=False passes=True` = 0), which is a coincidence of how the spawn
prompt is written, not a guard. P1 and P2 are the same hole seen from two
sides; fixing P1 does not touch P2.

```
Route: deepreason-orchestrator (defect, design-first — expect to stop at
FIX.md and report rather than implement).

One goal: decide and record whether a `predicate:` commitment can be a FORM
gate, and if so how the substantive/structural boundary recognises one, so
reach and prose immunity cannot be grounded on a criterion that checks
shape rather than subject.

Evidence, already committed:
  - experiments/2026-08-21-measure-reach-firing/CENSUS.md, "The qualifying
    vocabulary": relation-form@578e42df713e carries 584 303 of 585 096 gate
    pairs across 86 roots, and its docstring calls it a form gate.
  - probe_novelty.json: the carries x passes 2x2. The hit cell is empty for
    both qualifying criteria — today's protection is an accident of prompt
    wording, not a mechanism.
  - src/deepreason/measures/reach.py::_substantive — `kind == "predicate"`
    is never excluded.

Read first: docs/map/CON-warrants-and-attacks.md, docs/map/SUB-evaluation.md,
and the operator law "Formalism is an option, never an obligation" (CLAUDE.md)
— any design that penalises a conjecture for its KIND violates it, so a fix
must key on what the criterion CHECKS, not on how the artifact was written.

Do NOT lower any reach threshold as part of this. The Bronze Age postmortem
is why the strictness exists.

End state: FIX.md naming one mechanism (a declared class on Commitment? a
form-gate marker at mint time? leaving it as-is with the reason recorded),
its blast radius over reach AND formally_backed, and the measurement that
would prove it. Implementation only on explicit operator approval.
```

---

## P3 — `reach.py`'s module docstring enumerates three rejection paths; the code has five

**What:** the docstring documents non-qualifying criteria, no novel
criterion, and coverage below `coverage_min`. The implementation also exits
on `not problem.criteria` (285 070 pairs in this census) and on a qualifying
criterion failing (585 096 pairs — every rejection that is not one of the
other two). A reader who trusts the docstring attributes the census wrongly.
Documentation-only.

```
Route: deepreason-orchestrator (defect, docs-only — expect a one-paragraph
diff).

One goal: make measures/reach.py's module docstring enumerate the five
pair-level exits reach_sweep actually takes, in the order it takes them.

Evidence: experiments/2026-08-21-measure-reach-firing/CENSUS.md, the exits
table and the per-root census — E1 (285 070) and E4 (585 096) together carry
870 166 of 1 178 430 pairs and neither is named in the docstring.

End state: docstring matches the code; the map document covering
measures/reach.py gains a check that would fail if a sixth exit were added
without documenting it; no behaviour change; full gate 0 failed.
```
