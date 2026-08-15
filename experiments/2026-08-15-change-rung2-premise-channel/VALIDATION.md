# VALIDATION — Rung 2 step 2

Verdict: **PASS on everything that could be exercised in this container.
A19 (the guarded live run) is BLOCKED, not failed** — see below.

Instruments, run idle, one at a time:

| Instrument | Result |
|---|---|
| `python -m pytest tests/ -q -n 4` | **3640 passed, 7 skipped, 0 failed** (783 s) |
| `python tools/docs_verify.py` (full) | 898 checks, **3 failed — all `CON-run-identity`**, the recorded shallow-clone baseline |
| `python tools/docs_verify.py --links` | 0 dangling references, 58 documents |
| `tools/diff_budget.py` accounting | **EXCEEDED and disclosed** — production 458/320, tests 352/300, map docs 107/120 (SPEC.md carries the per-file breakdown) |

## Acceptance checks

| # | Check | Verdict | Evidence |
|---|---|---|---|
| A13 | `crit()` False for structural-only and rent-only interfaces | PASS | `test_structural_commitments_do_not_pay_rent`, `test_the_rent_battery_cannot_satisfy_itself` |
| A14 | A rentless premise is REFUTED with no hand-written attack | PASS | `test_a_premise_falls_by_demarcation_with_no_written_refutation` |
| A15 | The producer fires in an offline run of the ACTUAL `Scheduler` loop | PASS | `test_the_producer_fires_in_the_real_loop` — invitation Measure → premise + attribution → rent refutation → mark, all through `Scheduler.step` |
| A16 | Marked deprioritised, retired never selected, both modes | PASS | `test_a_retired_problem_is_not_selected[True/False]`, `test_a_marked_problem_yields_to_unmarked_work[True/False]` |
| A17 | Three signals emitted by the loop, none `unspecified` | PASS | `test_the_three_detection_signals_are_emitted_and_declared` |
| A18 | An uninvited `premise` registers nothing | PASS | `test_an_uninvited_premise_registers_nothing` |
| A19 | ONE guarded live run | **BLOCKED** | No credential: `experiments/*/env` absent, `OLLAMA_API_KEY` unset. Not a MISS — a miss requires a run that happened. |
| A20 | A prose premise that varies into something different survives | PASS | `test_a_prose_premise_that_varies_into_something_different_survives`, `..._with_a_variation_surface_survives_the_loop` |
| A21 | A prose premise whose variations are the same claim falls; ν declares the sample | PASS | `test_a_premise_falls_by_demarcation_with_no_written_refutation` (now through both readings) |
| A22 | No variator seat ⇒ nothing falls, recorded once per premise | PASS | `test_without_a_variator_nothing_falls_and_the_record_says_why`, `test_a_run_with_no_variator_seat_fells_no_premise` |

## Hard constraints, checked rather than asserted

| Constraint | How it holds |
|---|---|
| H1 — no problem minted from a conjecture's failure | The producer emits an INVITATION and a Measure. `translate` remains the only path that mints a problem, and it fires from an adjudicated resolution. Nothing in this change calls `spawn`. |
| Nothing ranks/admits/accepts a conjecture on carrying an attribution | The attribution is an ordinary artifact addressed to no problem; admission, rank and acceptance never read it. `test_an_uninvited_premise_registers_nothing` pins the one place the field could have leaked into behaviour. |
| No new LLM role | `argumentative_critic` gained one optional field; `variator` is an existing qualified seat. `contract_id` values are untouched, and the qualification subject digests `contract_id` rather than the rendered schema. |
| Allocation touches efficiency, never evidence | All five new signals are Measures. None is read by anything that assigns a status, a warrant or an edge; the allocation consumer does not exist yet (Rung 1b-ii). |
| Attention only | The scheduler filters and ranks; it registers no warrant and assigns no status. The one status change in this tranche is the rent battery's DEMONSTRATIVE warrant, which is registered inside `rules/warrants.py` on the ordinary path. |
| No cross-version proof owed | None attempted. No old-root sweep was run as a gate obligation (2026-08-14 law). |

## Residue

- **A19 is unexercised, and no offline result substitutes for it.** Whether a
  real critic ever takes the invitation is a question only a live run can
  answer, and one live miss would still be inconclusive.
- **`mod` is a sample.** A premise's survival or fall through the second
  reading rests on one variator draw. ν says so; a caller reading the verdict
  as a proof is reading it wrong.
- **D-8 remains open.** A premise that is contentful and wrong BY ARGUMENT
  alone still needs argumentative status authority, which no solo
  configuration has today.
