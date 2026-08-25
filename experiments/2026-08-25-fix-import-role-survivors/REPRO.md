# Reproduction

Form: **record-replay** — the defect is already captured in a committed run
root. No live run, no provider call, nothing to launch.

Artifact: `experiments/2026-08-25-fix-import-role-survivors/repro.py`, read-only
over `experiments/2026-08-25-poietics-program/run`.

Current output (verbatim, unfixed tree at base `43f408506`):

    deepreason results        survivor_count = 82
                              frontier       = 40
    stored survivor set       82 ids -> 58 conjecturer, 24 import
    IMPORT members registered at log seqs 5-40; first LLM-bearing event is seq 85
                              -> all 24 were accepted BEFORE any model was consulted
    IMPORT members address    {'question-aa835741bebc4b4cb189f4b08bef649a': 24}

    DEFECT: the invariant says import-role admission records never count as survivors.
            The surface counts 24 of them, reporting 82 where the record supports 58.

A second measurement, over the tranche's own committed milestone census
(`experiments/2026-08-25-poietics-program/milestones.json`, M1
`survivors_passing`), reproduces RESULTS.md's per-criterion split without
re-running anything:

    34 survivors pass poietics-installation-mechanism@v1
       -> Counter({'conjecturer': 26, 'import': 8})

which is exactly the "26 conjectures and 8 imported record sections" RESULTS.md
quotes.

Confirms diagnosis: **yes.** The count `deepreason results` prints (82) is the
length of `run-result.json`'s stored survivor set, and that set contains 24
artifacts whose `provenance.role` is `IMPORT` — the exact class
`Scheduler._select_problem` already refuses to count. The seq evidence rules out
any reading in which those 24 "survived" something: they were registered and
accepted at seqs 5–40 and the log's first LLM-bearing event is seq 85.

Post-fix expectation:

    deepreason results        survivor_count = 58
    stored survivor set       82 ids -> 58 conjecturer, 24 import
    ...
    (the DEFECT paragraph becomes: the surface counts 0 of them)

Note what does NOT move, and why it must not: the **stored** set stays 82 ids.
A committed root's bytes are evidence and are never edited (CLAUDE.md; the
orchestrator's hard prohibitions). The fix changes what the READER counts, not
what the record holds. `frontier` also stays 40: all 40 are `CONJECTURER`, and
no IMPORT survivor carries an `hv` or `reach` entry, so every one of them is a
dominated point — and dropping dominated points cannot move a Pareto front.

Production code untouched by this phase.
