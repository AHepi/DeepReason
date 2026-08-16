# DELIVERY — Rung 3d: the website-pipeline remnant

Operator authority: ADDENDUM v2 and its correction (v2 program `REQUEST.md`
Amendment 9, R66–R71), plus the operator's own concurrence with the Road A
result on the enum.

## Requirement-by-requirement

| # | Requirement (operator's words, condensed) | State | Where |
|---|---|---|---|
| R66 | The website pipeline stays decommissioned; its successor production is a REMNANT — remove it, leave nothing that could quietly revive the pipeline | **DONE, with one measured deviation** | `easy.py::seed_component` no longer stamps successor provenance — **producers = 0**. `SpawnTrigger.SUCCESSOR` is RETAINED as inert vocabulary; see below |
| R67 | Tests asserting the decommissioned behaviour are RETIRED with docstrings citing the ruling; retirement is correct, not weakening | **DONE** | nine tests retired or re-founded, each citing the ruling: `test_h1_no_spawn_from_refutation` (2), `test_reflexive_discipline`, `test_review_fixes`, `test_schools`, `test_guards`, `test_website_state_machine`, `test_jolt_trigger_pilot`, `test_runtime_workload_integration`, `test_thesis` |
| R68 | PROTECTED-LIVE, four channels, fully functional | **HELD** | `tests/test_decommissioned_pipeline_stays_out.py`, one green cited row each |
| R69 | THREE of the four mint evidence; scratch is protected-LIVE but ADVISORY | **HELD** | see the per-channel close below |
| R70 | Every proposed deletion carries a two-scan non-reachability proof from each of the four channels; overlap = contradiction-stop | **DONE — eight scans, zero hits, no overlap**, so no stop was triggered | pasted in `VALIDATION.md` |
| R71 | One green cited test row per channel; the delivery states per channel that it compiles, dispatches and mints | **DONE** | below |

## The four protected channels, per channel, post-deletion

| Channel | Compiles | Dispatches | Mints |
|---|---|---|---|
| **Code testing / execution** | `candidate_checker` and every member of `EXEC_PROGRAMS` resolve in the program registry (`PROGRAMS` + `BLOB_PROGRAMS`) | `try_counterexample` is intact and callable | **Mints evidence.** None of the execution programs is in `_STRUCTURAL_PROGRAMS`, so they remain SUBSTANTIVE — execution-grade evidence, grounding reach and immunity as before |
| **Simulation** | `CompiledSimulationV1` and `CapabilityReplayState` import clean | the simulation controller module is intact | **Mints evidence.** Typed proposals through receipts, replayed from the capability state, unchanged |
| **Research backend** | `research.backends` imports clean | the fetch path is untouched | **Mints evidence.** `research-fetch:*` and `research-evidence-registered` still resolve through the signal contract — every attempt reaches the log, and registered evidence stays citable |
| **Scratch pad** | `scratch.service` imports clean | the workshop path is untouched | **Mints NO evidence, by its own law.** `advisory_non_grounding` is still a manifest literal, and the boundary holds structurally: neither criticism renderer takes a scratch parameter |

## The one deviation, measured rather than assumed

**`SpawnTrigger.SUCCESSOR` is retained as inert vocabulary.** The addendum said
to delete it once producers reached zero. Producers ARE zero — and deleting the
member was then measured (Road A) rather than assumed:

- it fixes nothing (the remnant is already gone with its producer), and
- it breaks four tests that replay pre-v2 roots, which stop parsing.

That cost is permitted by the 2026-08-14 law but buys nothing here. What keeps
the pipeline decommissioned is **zero producers**, not a shorter enum, and the
regression that guards it now asserts exactly that — a source scan that fails if
any file starts producing successors again, before any enum check would.
Operator concurred with this reading when the measurement was reported.

## The false trail, recorded because the correction is the useful part

Six gate failures were reported as one problem and were two. Four were the enum
(pre-v2 roots). Two were a **map document being an evidence-dossier input to a
pinned manifest golden** — I had edited `docs/map/SUB-adjudication.md`, and the
compiled manifest is a content address over it. Not a cache: two builds in one
process agreed every time, which is what a stale-artifact cache could not do.
That coupling is a real defect and is **PARKED** with its diagnosis, not fixed
here.

## Gate

Full gate **3668 passed, 7 skipped, 0 failed**. The DO-NOT-MERGE marker is
lifted.
