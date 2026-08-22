# Results — reach's structural set derived from the declared program class

## 2026-08-22 — what was observed, what was fixed, what the record now shows

**Observed.** `programs.PROGRAMS` declares fourteen programs
`class_="structural"`. `measures/reach.py::_STRUCTURAL_PROGRAMS` was an
independently hand-written frozenset naming nine of them. `hand - declared`
was empty and `declared - hand` was five — `component_wf`, `generator_wf`,
`integration_wf`, `manifest_wf`, `reasoning-envelope-wf` — the signature of a
copy that was never updated rather than of a deliberate disagreement. Two
consumers read the wrong answer: `reach_sweep` and
`rules/warrants.py::formally_backed`, which imports `_substantive` directly.

**Why it was load-bearing, and in the direction nobody wrote down.** The
misclassification is PERMISSIVE in form — it counts a weak criterion as
strong — so the 08-21 census tranche parked it as latent, and the map's own
Traps entry called it "not an observed live failure". On the prose-immunity
side that was right and remains right. On the reach side it was the opposite:
a qualifying criterion must PASS for a hit, and `reasoning-envelope-wf` fails
on prose by construction, so counting it substantive VETOED hits rather than
manufacturing them. It was the single reason no current-version root ever
recorded a reach event.

**Fixed** by DERIVING the set from `ProgramSpec.class_`
(`_STRUCTURAL_PROGRAMS = frozenset(programs.programs_by_class()["structural"])`)
rather than by adding the five names. The design question `PARKED.md` P1
posed — derive, or hand-list plus an asserting test — was answered on
evidence: the defect IS the second source; the registry is already the
authority for the classification's other consumer with teeth
(`rules/guards/anti_relapse.py` reads `program_class`); and a mis-declaration
under derivation costs a MISSED hit where the same mistake under the old code
costs a MANUFACTURED one. The safe failure direction decided it.

**What the record now shows.**

| scenario (`rehearsal.json`, same script, no rebind) | before | after | reach events |
|---|---|---|---|
| S8a prose conn: candidate vs seed | `E4 criterion-fail` | **`HIT full`** | 0 -> 1 |
| S8b the same pair, fix formerly simulated | `HIT full` | `HIT full` | 1 -> 1 |
| S8c off-SUBJECT control, same batteries | `E4 criterion-fail` | `E4 criterion-fail` | 0 -> 0 |
| S2 prose artifact, EMPTY own battery | `E4 criterion-fail` | **`HIT full`** | 0 -> 1 |
| S1, S3, S4, S5, S6, S7 | unchanged | unchanged | unchanged |

S8a and S8b are now identical on every recorded field but their label and
note — which is the decisive regression, because S8b was previously produced
only by rebinding the module constant in-process and S8a is produced by the
shipped code.

Two exits moved, not one. S2 was NOT pre-registered and is recorded as a
finding rather than folded into the result: it is the same mechanism (a
subject predicate, novel, passing) but it exercises two boundaries nothing in
96 committed roots ever reached — an artifact with an empty own battery, and
coverage landing exactly ON `REACH_COVERAGE_MIN`. Parked as P5-reach for a
deliberate ruling.

**No committed root's adjudication moved.** `immunity_delta.py`, driving the
08-21 tranche's `probe_immunity.probe` verbatim over all 107 roots carrying a
`log.jsonl`: `formally_backed` = 903 of 3 528 candidates before AND after, and
zero roots moved when compared per root rather than in aggregate. Eleven roots
return `open_error` (old-version readers refusing them) identically in both
runs, so none is masked by the change.

**Second finding, fixed in its own commit (P3).** `reach.py`'s module
docstring enumerated three rejection paths; `reach_sweep` takes five plus the
hit. The two it never named carry 870 166 of 1 178 430 census pairs, so every
reader who trusted it misattributed the bulk of what it described. All six
exits are now documented in the order the code takes them, with a
mutation-proved check that fails if a sixth is added undocumented.

## Residue — what remains unproven

- **Nothing live has been run.** This tranche made no provider call. The
  offline regressions and the rehearsal are the proof of CORRECTNESS; they do
  not show how often a real `glm-5.2` connection candidate would survive a
  seed problem's subject predicates. That frequency is what the frozen
  reach-rich run measures, and it stays unknown.
- **The reach-rich run's precondition is cleared, not its hypothesis.**
  `experiments/2026-08-22-live-reach-rich-run/PREREG.md` §4 recorded
  PRECONDITION-BLOCKED. That block is lifted. Whether a live run produces a
  reach event is a separate, still-open question, and Rung 5's nomination
  additionally needs reach across DISTINCT problem lineages, which P4-reach in
  that tranche says a text run cannot currently seed.
- **P2 is untouched and now the only remaining hole of its kind.** A form gate
  spelled `predicate:` is substantive by construction. With the program-class
  exclusion complete, that is the last route by which a shape check can ground
  reach. The rehearsal's S5 shows an integration problem whose entire
  qualifying battery is one such gate.
- **`ProgramSpec.class_` now has teeth in two places.** Declaring a new
  program `structural` silently narrows what can ground reach and what confers
  prose immunity. That direction is safe — it withholds, never grants — but it
  is a real change in what registering a program means, and it is recorded in
  the `ProgramSpec` docstring and `SUB-evaluation.md` Traps rather than left
  implicit.
- **Accepted does not mean true.** The fix makes the harness stricter about
  what may ground reach and produces a hit in a rehearsal. It does not
  establish that any artifact in any run genuinely explains a foreign
  problem — only that a well-formedness check is no longer the thing deciding.
