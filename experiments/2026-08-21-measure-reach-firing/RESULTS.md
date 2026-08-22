# RESULTS — reach-firing measurement (2026-08-21 / delivered 2026-08-22)

Honest-ledger segments. What the record shows, and the residue.

---

## 2026-08-22 — reach has never fired on a current-version root, and zero is the correct answer

**Pre-registered question** (`GOAL.md`, committed before any measurement):
across every committed CURRENT-VERSION root, count reach outcomes — full
hits, provisional hits, rejections — and attribute every rejection to one
exit. Then decide between three typed verdicts: (a) zero is correct,
(b) a reader or threshold is wrong, (c) inconclusive.

**Verdict: (a).** `VERDICT.md` carries it in full.

### What the record shows

107 roots carry a `log.jsonl` under `experiments/`. 96 open under the current
reader. 11 refuse with `UnsupportedRunManifestVersionError:
UNSUPPORTED_RUN_MANIFEST` and are recorded out of scope under the operator law
of 2026-08-14, not diagnosed.

On all 96 in-scope roots the RECORDED census — Measure events carrying
`reach_set` or `addr+`, and Measure inputs beginning `reach-provisional`,
parsed straight out of `log.jsonl` — is **zero, everywhere**. Not one reach
event, not one provisional event.

Reach HAS fired in this project's history, twice, and both roots are out of
scope: `gemma4_dna_unattended_2026-07-12` (4 `reach_set` events, 24 `addr+`
pairs) and `gemma4_dna_unattended_3_2026-07-12` (2 and 11). Both predate the
Bronze Age postmortem discipline. The only reach ever recorded came from a
version that had no reach discipline — which is the postmortem's own point,
seen from the other end.

The RE-DERIVED census attributes every candidate pair on those 96 roots:

| exit | pairs |
|---|---|
| `E1 no-criteria` | 285 070 |
| `E2 non-qualifying` | **0** |
| `E3 no-novel` | 308 264 |
| `E4 criterion-fail` | **585 096** |
| `E5 coverage / provisional` | **0** |
| `HIT full` | **0** |
| total | 1 178 430 (sums exactly) |

Every `E4` first non-pass verdict is `fail` — never `overrun`, never an
evaluator error.

### Why

The corpus's entire qualifying vocabulary is **two criteria**, and both are
FORM gates: `relation-form@578e42df713e` (584 303 gate pairs, 86 roots — a
`predicate:` whose own docstring calls it a "Form gate", built from a
CONSTANT expression so its content-addressed id is a singleton shared by
every connection and integration problem ever spawned) and
`reasoning-envelope-wf` (793 gate pairs, 46 roots — a program declared
`class_="structural"` that `_STRUCTURAL_PROGRAMS` does not list).

`reach_sweep` needs a criterion that is NOVEL to the artifact and PASSED by
it. Over every candidate artifact in the corpus, that cell is empty:

| criterion | carries=F passes=F | **carries=F passes=T** | carries=T passes=F | carries=T passes=T |
|---|---|---|---|---|
| `relation-form@578e42df713e` | 2 534 | **0** | 0 | 880 |
| `reasoning-envelope-wf` | 861 | **0** | 79 | 2 296 |

An artifact passes a form gate exactly when it was built carrying it — the
connection/integration spawn prompt tells the conjecturer to name a relation
kind and state a REFUTED IF — and because the gate is a singleton, it is
never novel to such an artifact. Novelty and survival are jointly
unsatisfiable here.

### What was ruled out, with the number that rules it out

- **A suppressing threshold.** `E5` rejected 0 pairs, and 487 912 of 585 096
  gate pairs (83%) already sit at coverage 1.00, above the 0.5 minimum.
  Lowering `REACH_COVERAGE_MIN` would change nothing.
- **An over-aggressive structural filter.** `E2` rejected 0 pairs. It never
  fired as a sole cause anywhere in the corpus.
- **A reader that cannot resolve bytes.** `SUB-evaluation.md` Traps warns
  that a missing blob reads as `""` and yields a confident `fail`. All
  3 528 candidate artifacts resolve to non-empty content, shortest 402
  characters. The failures are about content that exists.
- **A sweep that never runs.** It is called every cycle
  (`scheduler.py:2274`). The real `reach_sweep`, run against copies of four
  roots in a scratch directory — including the largest, 12 991 log lines —
  returns `[]` and appends nothing.

### The residue — what remains unproven

- **The re-derivation reads the FINAL replayed state, not the state at each
  cycle when the sweep actually ran.** Status can move (ACCEPTED → REFUTED)
  and criteria can be added between cycles, so a per-cycle census could
  differ in its exit attribution. It cannot differ in its bottom line: the
  RECORDED census is the authority on whether reach fired, and it is zero on
  every in-scope root, which the four copy-runs independently confirm. What
  is unproven is the exact exit distribution AT EACH CYCLE, not the zero.
- **Zero is correct FOR THESE ROOTS.** It is not evidence that the reach
  mechanism works when a substantive battery does exist. No post-discipline
  root has ever exercised a reach hit, so the mechanism is UNEXERCISED live,
  and the offline regression tests (`tests/test_reflexive_discipline.py`)
  remain the only proof it fires at all.
- **The 11 out-of-scope roots were not diagnosed.** By law, not by
  inability. If a future question needs them, the reader refusal is the
  first thing to price.
- **Two permissive holes were found and left open.** `_STRUCTURAL_PROGRAMS`
  omits five programs `programs.PROGRAMS` declares structural (P1), and a
  form gate spelled as a `predicate:` is substantive by construction (P2).
  Neither causes the zero; both could manufacture a hit from a
  well-formedness gate in a future run. Parked with ready-to-send prompts,
  not fixed — this tranche is read-only on `src/`.
- **Accepted does not mean true.** The census proves that no artifact in the
  corpus passes a foreign criterion it does not already carry. It does not
  prove that no cross-problem survival OCCURRED in these runs — only that
  none was machine-detectable through the criteria those runs happened to
  carry. Reach measures what the batteries can see.

### Consequence for Rung 5

`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md` Rung 5
nominates a promotion problem from "reach events for one subject spanning
>= K_frame distinct problem lineages". On this evidence that nomination
cannot fire on any committed root, so Rung 5 cannot gate on the corpus. It
needs a reach-rich root generated live; `VERDICT.md` states the five
properties such a run must have, and prices a cheaper two-subject
intermediate that would produce the project's first post-discipline
`reach_set` event.

### Instruments

All read-only, all committed in this directory: `census.py` (+
`census.json`, `census-verdicts.json`), `probe_criteria.py`,
`probe_content.py`, `probe_novelty.py`, `probe_immunity.py`,
`verify_sweep_equivalence.py`, each with its JSON. `CENSUS.md` carries the
per-root table. `git diff --stat origin/main` shows changes only under
`experiments/2026-08-21-measure-reach-firing/` — no `src/` or `tests/` file
was touched, so no pytest gate is owed and none was run.
