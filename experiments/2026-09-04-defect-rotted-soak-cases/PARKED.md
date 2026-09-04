# PARKED — observed in this tranche, deliberately not fixed here

## P1 — three experiment directories define bare `question.py` / `criteria.py`

    experiments/2026-08-25-change-constructive-frontier/question.py   64b724c411832098
    experiments/2026-09-01-live-all-modules-p-a1/question.py          933313a5d9ca6dd8
    experiments/2026-09-02-live-p-a2-corrected/question.py            933313a5d9ca6dd8

(digests are `_question_digest` of each module's QUESTION; `criteria.py`
collides the same way)

Builders import these by bare name. That is what made D-C reachable: a cached
`sys.modules['question']` served the wrong experiment's bytes to the next case
built in the same process.

**Why it is parked, not fixed.** The loader is fixed, so the collision is no
longer reachable, and `tests/test_cycle_soak_runs_everything.py` asserts that
it stays unreachable. Renaming the modules would edit three committed
experiment directories to work around a defect that has already been fixed at
its cause — a wider change with no property the loader fix does not already
have.

**What would reopen it.** Any future consumer that imports these builders
WITHOUT going through `_case_module`. Such a consumer inherits the original
defect and gets no protection from the loader fix. If one is written, rename
the modules then.

## P2 — the soak still cannot reach three recorded deaths

Transport faults, completion truncation, and continuability are absent from
the instrument — see
`experiments/2026-09-04-review-judge-seat-matrix-soak/VERDICT.md`, death table
rows 5, 6 and 8, and the ready-to-send prompt at that tranche's `PROMPTS.md`
P2. That is a CHANGE tranche (new mechanisms), not this defect repair, and it
is the operator's call.

Nothing in this repair makes the soak catch a death it could not catch
yesterday. It makes the soak run the assertions it already declared.
