# LOSS.md — the withheld lanes' work did not survive the container

Recorded 2026-08-29 by the resume session, as its FIRST act, before any
other work. Written plainly because the alternative — quietly redoing the
work and reporting it as a resume — would misstate what this session did.

## What was lost

Lane C (`2026-08-29-defect-qualification-circuit-breaker`, P7-A) and lane
B2 (`2026-08-29-change-config-carriage`, P15) were both WITHHELD on operator
stops at the end of the ultracode batch. Their branches, tranche directories,
`STOP.md` briefs and `proof/implementation.patch` were never pushed to
`origin`. The container was reclaimed before they were.

## The evidence that they are gone

    $ git ls-remote --heads origin | grep -E "circuit-breaker|config-carriage"
    (no output)

    $ ls -d experiments/2026-08-29-defect-qualification-circuit-breaker \
            experiments/2026-08-29-change-config-carriage
    ls: cannot access ...: No such file or directory

    $ git reflog
    facea8f81 HEAD@{0}: checkout: moving from facea8f81 to claude/deepreason-batch-lanes-c-b2-kqogay
    facea8f81 HEAD@{1}:
    4269aa3e4 HEAD@{2}: checkout: moving from 4269aa3e4 to main
    4269aa3e4 HEAD@{3}:

    $ git stash list
    (empty)

A fresh clone, an empty reflog, no worktrees under `/home/user/dr-lanes/`,
and no local branches but `main` and this session's own. There is nothing
to recover. `proof/implementation.patch`, which lane B2 produced precisely
so one command could restore its uncommitted implementation, is gone with
the container that held it.

## What survived, and is therefore the basis for the redo

Everything committed to `main` at `facea8f81`:

- `BATCH.md` §1 (the manifest rows), §2 (both STOP briefs and the priced
  three-road carriage table), §4 (Lane C's six findings), §5 (the
  correction Lane C generated offline, with its measured 429/401 table)
- `experiments/2026-08-28-audit-run-problems/PARKED.md` P7-A and
  `AUDIT_REPORT.md` F-H — Lane C's dispatch
- `experiments/2026-08-28-defect-manifest-config-disclosure/` — P15's
  dispatch (`PARKED.md` P15), its `DIAGNOSIS.md`, `MEASUREMENTS.md` and
  re-runnable `probe/census_dropped_fields.py`
- the P10 disclosure machinery itself, in `run_manifest.py`, which road A
  builds on

The two tranches are REDONE from those, under the monitor's rulings, which
are recorded verbatim in each tranche's `FIX.md`/`SPEC.md` before its code
lands. Every conclusion the batch reached still stands; what was lost is the
implementation, not the reasoning that justified it.

## The lesson, stated where the next session will hit it

`CLAUDE.md` already says to commit and push at every phase boundary. The
batch obeyed that for the three lanes it delivered and did NOT obey it for
the two it withheld — because a withheld lane feels like work in progress.
It is not. **A STOP is a phase boundary.** Work parked for an operator
decision is finished work awaiting a verdict, and it must be pushed at the
moment it is parked, not at the moment the verdict arrives. A patch file
preserved inside a container preserves nothing.
