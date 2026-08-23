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

---

## P5-epoch3 — a token-bounded run cannot reach a resumable terminal, because the last reservation never fits

**What:** `deepreason continue` accepts only
`RESUMABLE_STOP_REASONS = {"converged", "budget_exhausted"}`
(`workflow/lifecycle.py:28`). Exhausting a token budget does not produce
`budget_exhausted`. `workflow/transaction_service.py::reserve_dispatch`
books the FULL completion cap up front for every call, so as the budget
drains the remainder eventually becomes smaller than one reservation;
`meter.reserve` then raises `TokenBudgetExceeded` and the service writes a
`budget_denied` terminal, which surfaces as `WorkBudgetDenied` and
`stop_reason=operational_failure` — unresumable.

Measured on epoch-3 attempt 2 (root
`bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4`):

    logged LLM calls           56
    logged tokens             165 466
    phase-1 token budget      200 000
    headroom remaining         34 534
    next reservation needed   ~35 700  (32 768 completion bound + ~2 900 prompt)
    terminal                  status budget_denied, reason_code
                              token_budget_denied, prompt/completion tokens 0

The consequence is general, not particular to this budget: ANY finite token
budget ends this way unless the run first exhausts its CYCLES or converges.
A run whose token budget binds before its cycle budget can therefore never
be amended or continued, however healthy its record — this one's
`verify_root` reports 0 violations.

Whether that is correct as written is a real question, not a rhetorical
one. A denied reservation IS impossibility at the point of use, which the
all-configurations law explicitly leaves as a typed runtime failure. But
"the operator's token budget ran out" and "the seat cannot do its job" are
different facts wearing one stop reason, and only the second should cost
the run its resumability.

```
Route: deepreason-orchestrator (defect, design-first -- expect to stop at
DIAGNOSIS.md; the answer may legitimately be "correct as written").

One goal: decide and record whether a run that stops because its TOKEN
budget is spent should reach a resumable terminal, so an operator who
budgets tokens rather than cycles is not locked out of amend and continue.

Evidence, already committed:
  - experiments/2026-08-22-change-epoch3-second-lineage/RESULTS.md, the
    attempt-2 segment -- the arithmetic above, re-derivable in one command:
      python -c "import json;
      t=sum((e.get('llm') or {}).get('tokens',0) for e in
      map(json.loads, open('<root>/log.jsonl')) if e.get('llm')); print(t)"
    -> 165466 against a 200000 budget.
  - <root>/run-result.json -- error_type WorkBudgetDenied, completion_status
    incomplete, cycles completed 0 of 12.
  - <root>/objects/workflow-work-terminal-v1/ -- the budget_denied terminal
    for work sha256:32af1d16..., reason_code token_budget_denied, prompt and
    completion tokens 0 (the call never went out).
  - <root>/objects/workflow-token-reservation-v2/ -- 56 reservations, each
    booking completion_bound_tokens 32768 plus a prompt bound.
  - src/deepreason/workflow/lifecycle.py:28 and :273 -- the resumable set
    and the refusal it drives.
  - src/deepreason/workflow/transaction_service.py:364-396 -- reserve_dispatch
    and the budget_denied terminal it writes.

Read first: docs/map/INDEX.md for the workflow-transaction and scheduler
subsystems and the seam between them; docs/map/INV-frozen-surfaces.md (the
workflow v6 transaction record formats are not to be reshaped); and
CLAUDE.md's operator law "Operations are available to every configuration"
(2026-08-13), which is the standard this is judged against -- a run launched
with a token budget must reach the same typed terminal and accept the same
operations as one launched with a cycle budget.

Design question the tranche must answer, not assume: whether (a) a
reservation denial caused by budget exhaustion should terminalize as
`budget_exhausted` rather than `operational_failure`, since the run is
complete-as-far-as-it-got rather than broken; (b) the scheduler should stop
cleanly BEFORE issuing a reservation it can see will not fit, leaving the
remainder unspent and the stop reason resumable; or (c) correct as written,
and a token-bounded run is simply not amendable, with the reason recorded
and the CLI saying so at launch. (b) is the most honest to the record --
nothing is denied, the run just stops -- and is probably the smallest.

Do NOT respond by telling operators to budget cycles instead of tokens. That
is the workaround this finding exists to remove, and it silently makes one
of two documented budget forms second-class.

Constraint the design must respect: whatever is decided, the denial must
remain a TYPED outcome in the record. Silently retrying a denied reservation,
or shrinking one to fit the remaining headroom, would trade a recorded
refusal for an unrecorded one and would let a seat's completion cap be
violated by budget pressure.

End state: DIAGNOSIS.md naming one cause and one of (a)/(b)/(c); a
regression test pinning whichever answer is chosen and naming run
bb0455384ea09b5b... in its docstring; verify_root clean on the resulting
root; full gate 0 failed.
```

---

## P6-epoch3 — the dispatch guard compares two quantities the record cannot both recover

**What:** `llm/adapter.py:1176-1187` re-computes a work item's reservation
bound at dispatch as `conservative_prompt_bound(request) +
transport_limits["max_tokens"]` and raises
`WorkflowAuthorizationError("transactional reservation bound differs from
rendered request")` when it disagrees with the amount
`workflow/transaction_service.py::reserve_dispatch` already booked from
`conservative_prompt_bound(prompt) + max_tokens`. Epoch-3 attempt 3 died on
that guard at cycle 2 of 4 with 290 025 of 400 000 tokens unspent (root
`bb0455384ea09b5b…`, retired as `failed-attempt3-run-…`).

Two candidate causes are ELIMINATED against the record, so a fix tranche
does not re-derive them:

- **Not a controller cap re-tune** (the E43 shape): no policy artifact
  carrying a `knobs`/`cap:` entry exists in `log.jsonl`, and `max_tokens`
  appears as `32768` and no other value across every object in the root. All
  50 reservations booked `completion_bound_tokens 32768`.
- **Not prompt drift between reserve and authorize**: all 50 dispatch
  authorizations resolve to their reservation and `prompt_sha256` agrees in
  50 of 50.

**The gap that makes this hard, and which is the finding's real content.**
The guard compares a bound over the service's `prompt` with a bound over the
adapter's rendered `request`. The record stores a hash of the FORMER only;
the rendered request bytes are never persisted. So the two quantities the
guard exists to compare cannot both be recovered from a committed root, and
a post-hoc diagnosis cannot say which string was longer or why. A guard
whose failure is not reconstructible from the record is in tension with the
repo's own epistemology — the record is the only admissible evidence.

Note the shape it shares with `docs/ERRATA.md` E42: there, a census joined a
repair response to the WRONG authority because the convenient key was not
the frozen one. Here there is no wrong key — there is no key at all for one
side.

```
Route: deepreason-orchestrator (defect).

One goal: establish why a work item's dispatch-time reservation bound can
differ from the bound its transaction booked, and make that difference
reconstructible from the record when it happens -- so the guard's own
failure is diagnosable without re-running the model.

Evidence, already committed:
  - experiments/2026-08-22-change-epoch3-second-lineage/RESULTS.md, the
    attempt-3 segment, and .../failed-attempt3-run-bb0455384ea09b5b.../
    run-result.json -- error_type WorkflowAuthorizationError, message
    "transactional reservation bound differs from rendered request",
    cycles 2 of 4, verify_root 0 violations.
  - The two eliminations, re-derivable in one command each over that root:
      python -c "import pathlib,re,collections; v=collections.Counter();
      [v.update(int(m.group(1)) for m in
      re.finditer(r'\"max_tokens\"\s*:\s*([0-9]+)', f.read_text()))
      for f in pathlib.Path('<root>').rglob('*.json')]; print(dict(v))"
      -> {32768: 11}   (no re-tuned cap anywhere)
    and the reservation/authorization prompt_sha256 join over
    objects/workflow-token-reservation-v2/ and
    objects/workflow-dispatch-authorization-v1/ -> 50 of 50 agree.
  - src/deepreason/llm/adapter.py:1160-1190 -- transport_limits, the
    reservation_bound arithmetic, and the raise.
  - src/deepreason/workflow/transaction_service.py:364-396 --
    reserve_dispatch, where prompt_sha256 and prompt_bound are computed.

Read first: docs/map/INDEX.md for the llm and workflow-transaction
subsystems and docs/map/SEAM-llm-x-workflow.md -- this is exactly that seam.
Then docs/map/INV-frozen-surfaces.md (the workflow v6 transaction record
formats are frozen; ADDING a field to a record is a format change and needs
the operator's word), and docs/ERRATA.md E42/E43, both of which are prior
corrections on this same reserve-vs-dispatch agreement.

Design question the tranche must answer, not assume: whether (a) the two
call sites should bound the SAME string, with the divergence named and one
of them corrected; (b) the guard should compare a value the record already
carries (the prompt hash) rather than a recomputed length; or (c) the
failure envelope should record both bounds and both string lengths so the
next occurrence is diagnosable, which is the smallest change that makes the
OTHER two decidable. Consider doing (c) FIRST regardless: without it, a fix
for (a) cannot be verified against a live recurrence.

Do NOT respond by relaxing the guard to a tolerance window. It exists so
concurrent dispatchers cannot jointly push the logged total past the
ceiling; a fuzzy bound reintroduces exactly the overspend it prevents.

Constraint the design must respect: reservation booking happens BEFORE
dispatch by design (llm/budget.py reserve-settle). Any fix that moves the
booking after rendering must show it still fails closed on an unboundable
call.

End state: DIAGNOSIS.md naming one cause and one of (a)/(b)/(c); whatever
lands, a recurrence of this error must be diagnosable from the committed
root alone. A regression test naming run bb0455384ea09b5b... in its
docstring; full gate 0 failed.
```
