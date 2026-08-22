# PARKED — found while designing epoch 3, deliberately not fixed

This tranche is READ-ONLY on `src/` and `tests/` by operator instruction
(REQUEST.md C1) and may not build harness features inside a live-run tranche
(C2). Everything below is a finding with a ready-to-send prompt, not open
work for this window.

---

## P1-epoch3 — `amend --reshape-question` without `--attach` produces a root `continue` always refuses

**What:** a question-only amendment leaves the epoch's evidence dossier
pointing at the SUPERSEDED problem, and the continuation's own agreement
check compares that pointer against the SUCCESSOR problem id, so every
question-only amendment ends in `RUN_INPUT_MISMATCH`. Measured on a scratch
copy of the reach-rich epoch-2 root (SPEC.md M4): of the five conditions at
`application/text_runs.py:1184-1194` only `epoch_dossier.problem_ref !=
spec.problem.id` is true. The one covering gate test always passes
`attach=`, which is why the path is untested.

This bears directly on the operator law "Operations are available to every
configuration" (CLAUDE.md, 2026-08-13): `amend` offers `--reshape-question`
as a standalone operation and the lifecycle then refuses the continuation
that operation exists to enable.

```
Route: deepreason-orchestrator (defect).

One goal: make `deepreason amend --reshape-question` (with no --attach)
produce a root `deepreason continue` accepts, so a question-only amendment
epoch is a usable operation rather than a dead end.

Evidence, already committed:
  - experiments/2026-08-22-change-epoch3-second-lineage/SPEC.md M4 -- the
    five-condition isolation, showing c5 alone is true:
      c5 dossier problem_ref mismatch True question-4dd62735b90864a75220e09b302500bc
    Re-derive on a scratch COPY of
    experiments/2026-08-22-live-reach-rich-run/run (never the committed
    root):
      python -m deepreason --root <copy> amend --reshape-question "<Q2>"
      python -m deepreason --root <copy> continue --budget cycles=1
      -> RUN_INPUT_MISMATCH: text request differs from the frozen v6 run input
  - src/deepreason/amendment/apply.py, the else branch of the attach block:
    `successor_dossier = parent_dossier` with the comment "A question-only
    amendment cites exactly the dossier its parent did".
  - src/deepreason/application/text_runs.py:1184-1194 -- the check that
    reads `epoch_dossier.problem_ref != spec.problem.id`.
  - tests/test_amendment_epochs.py::
    test_continuation_runs_the_reshaped_question_under_the_same_root --
    the covering test, which passes attach= and therefore never exercises
    this path.

Read first: docs/map/SUB-amendment.md, docs/map/SUB-application.md, and
docs/map/INV-frozen-surfaces.md (the replay-validation record formats and
the manifest schemas are frozen; a dossier's problem_ref is part of the
evidence record, so decide FIRST whether the fix belongs on the writer or
the reader side). CLAUDE.md's operations-parity law is the standard the
outcome is judged against.

Design question the tranche must answer, not assume: whether the successor
dossier of a question-only amendment should be RE-EMITTED with the
successor problem_ref (writer side, changes an evidence record's bytes), or
whether the continuation check should compare against the epoch's own run
input rather than the dossier (reader side, changes nothing in the record).
The reader-side answer is the smaller one and does not move any committed
root; establish which is correct before writing either.

Do NOT respond by making --attach mandatory. That would remove an operation
the CLI advertises and would contradict the operations-parity law rather
than satisfy it.

End state: DIAGNOSIS.md naming one cause and one side (writer or reader); a
regression test that performs amend --reshape-question WITHOUT attach and
then continues, naming this tranche in its docstring; verify_root clean on
the resulting root; full gate 0 failed.
```

---

## P2-epoch3 — `amend` accepts a root whose stop reason `continue` will refuse

**What:** `deepreason results` reports `amend_ready: false` for the
reach-rich epoch-2 root because its `stop_reason` is `operational_failure`,
which is not in `workflow/lifecycle.py`'s
`RESUMABLE_STOP_REASONS = {"converged", "budget_exhausted"}`. `amend`
nevertheless SUCCEEDS on that root, writing epoch 1, a new seed problem and
a chain record — and only the later `continue` refuses. The typed record
therefore gains an amendment epoch that can never be continued, on a root
the retrieval surface had already flagged as not amend-ready.

Not a data-loss defect and not this tranche's blocker (SPEC.md's chosen
vehicle avoids it by construction, phase 1 ending `budget_exhausted`). It is
a disagreement between two components about one precondition.

```
Route: deepreason-orchestrator (defect, design-first -- expect to stop at
DIAGNOSIS.md; the answer may legitimately be "correct as written").

One goal: decide and record whether `deepreason amend` should refuse a root
whose stop reason does not authorize continuation, or whether writing an
un-continuable amendment epoch is intended -- so `results`' amend_ready
verdict and `amend`'s own behaviour state the same precondition.

Evidence, already committed:
  - experiments/2026-08-22-change-epoch3-second-lineage/SPEC.md M3 --
      python -m deepreason results experiments/2026-08-22-live-reach-rich-run/run --json
      "terminal": {"amend_ready": false, "stop_reason_resumable": false,
                   "valid_typed_terminal": true}
    and M1 -- the same root amending successfully on a scratch copy, rc=0,
    epoch 1, problem_id question-07d84c43d59d17282fef7db6ba7adaff.
  - src/deepreason/workflow/lifecycle.py:28 (the resumable set) and :273
    (the refusal that fires only at continuation).
  - src/deepreason/application/results.py:398-420 -- the amend_ready
    computation that already knows the answer before amend runs.

Read first: docs/map/SUB-amendment.md, docs/map/SUB-application.md, and
CLAUDE.md's operator law "All configurations should be allowed" (2026-08-12)
WITH its stated boundary -- that law abolishes COMPILE-time denial and
explicitly leaves runtime failing typed at the point of use. An amendment is
not a compile, so the law does not settle this on its own; the question is
which point of use is the right one.

Constraint the design must respect: whatever is decided, an amendment that
is refused must be refused BEFORE it writes an epoch, and one that is
written must remain replay-valid. A half-applied amendment is the outcome
neither answer may produce.

End state: DIAGNOSIS.md naming one of -- (a) amend should refuse a
non-resumable terminal with a typed code, with the code named; (b) writing
the epoch is correct and `results` should say so differently, with the
wording named; (c) correct as written, with the reason recorded. A
regression test pinning whichever answer is chosen.
```

---

## P3-epoch3 — the map has no `SEAM-amendment-x-application.md`, and the pair is where both defects above live

**What:** `docs/map/INDEX.md`'s matrix carries `SUB-amendment.md` and
`SUB-application.md` but no seam document between them, so a change spanning
the amendment machinery and the single run path has no document naming the
small fraction of each side actually involved. Both P1-epoch3 and P2-epoch3
are precisely seam defects: a precondition one side writes and the other
side enforces. Per `docs/map/INDEX.md`'s own convention an absent seam means
"not yet written up", never "these two do not interact" — and this tranche
had to re-derive the interaction from source to design around it.

```
Route: dr-change-orchestrator (change, documentation only -- one new map
document, no src/ or tests/ involvement).

One goal: write docs/map/SEAM-amendment-x-application.md so the amendment /
run-path pair is navigable from INDEX.md, with executable checks over the
preconditions the two sides share.

Evidence, already committed:
  - experiments/2026-08-22-change-epoch3-second-lineage/SPEC.md M1, M3, M4,
    M5 -- four measured facts about this exact seam, each re-derivable by
    the command pasted with it.
  - src/deepreason/amendment/apply.py::_apply_ledger_chain (registers the
    reshaped question as a trigger="seed" problem) and
    src/deepreason/application/text_runs.py:1184-1194 (the continuation's
    request/spec/dossier agreement check) -- the two sides.
  - src/deepreason/workflow/lifecycle.py:28 RESUMABLE_STOP_REASONS -- the
    precondition the seam turns on.

Read first: docs/map/SCHEMA.md (the contract for writing a map document,
including the `check:` discipline at column 0 and the Verified-at stamp
rule) and docs/map/REC-change-a-seam.md.

The document must carry at least these checks, each exiting 0 and each able
to FAIL if the behaviour regressed:
  - RESUMABLE_STOP_REASONS is exactly {"converged", "budget_exhausted"};
  - a question-only amendment's successor dossier problem_ref, against what
    the continuation compares it to (whatever P1-epoch3 settles);
  - `amend` registering the reshaped question with trigger="seed".
Write the checks and RUN them before writing the prose they support.

End state: the document exists, INDEX.md's matrix lists it, `python
tools/docs_verify.py` passes with the new checks included, and
`--audit` does not refuse any of them as unfailable.
```

---

## P4-epoch3 — in this container `docs_verify` reports three failures that say nothing about the tree

**What:** the cloud container checks the repository out SHALLOW. Measured
during this tranche's step 13:

    $ git rev-parse --is-shallow-repository   -> true
    $ git log --oneline | wc -l               -> 142

`docs/map/CON-run-identity.md` carries three `check:` commands at lines 200,
202 and 204 that address commits by hash (`1637e808`, `f304fec1`,
`6a8758a5`) and walk rename history under
`experiments/live_research_2026-07-29/selfstudy/runs/`. Outside the shallow
window those objects do not exist, so the checks fail with
`fatal: ambiguous argument '<hash>': unknown revision`, and
`docs_verify` reports `3 failed` on a tree where nothing is wrong. After
`git fetch --unshallow` (2223 commits) the same command reports
`0 failed`.

This is an ENVIRONMENT trap, not a defect in the document — the checks are
correct and they do fail when the claim stops being true. But a session that
runs `docs_verify` on a fresh container will see three red lines at a
commit boundary and has no cheap way to know they are noise.

```
Route: dr-change-orchestrator (change, documentation only -- CLAUDE.md's
"Environment (cloud container)" section, or docs/map/SCHEMA.md's guidance on
history checks; no src/ or tests/ involvement).

One goal: make a shallow-clone docs_verify failure legible at the moment it
appears, so a session does not either chase it or -- worse -- learn to
ignore docs_verify failures generally.

Evidence, already committed:
  - experiments/2026-08-22-change-epoch3-second-lineage/CHECKLIST.md step 13
    -- the three FAIL lines, the shallow-clone measurement, and the 0-failed
    rerun after --unshallow.
  - docs/map/CON-run-identity.md lines 200/202/204 -- the three checks, each
    addressing a commit by hash.

Read first: docs/map/SCHEMA.md (the check: contract -- in particular whether
a check MAY depend on git history depth), and CLAUDE.md's "Environment
(cloud container -- read first, every session)" section, which already
carries the resync recipe and is where a reader would look.

Design question the tranche must answer, not assume: whether the fix is
(a) one line in CLAUDE.md's environment section -- "run git fetch
--unshallow before docs_verify; history checks fail on a shallow clone with
'unknown revision'"; (b) a guard inside tools/docs_verify.py that detects a
shallow clone and reports history checks as SKIPPED-SHALLOW rather than
FAILED; or (c) rewriting the three checks so they do not need history
outside a shallow window. (b) is the most useful and the most work; (a) is
one line and loses nothing. Price them before choosing.

Do NOT respond by deleting or weakening the three checks. They pin the
rename discipline that CLAUDE.md's "Live runs" section makes law, and the
--unshallow rerun proves they pass on a complete clone.

End state: a session on a fresh container either does not see the three
false failures, or reads why it is seeing them in the first place it would
look. Whatever lands, docs_verify still reports 0 failed on a complete
clone.
```
