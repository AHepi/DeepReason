# Diagnosis: the STOPPED receipt refuses on outstanding work the run's own recovery machinery exists to close — and the failure terminal never asks for the receipt at all

## Stop report, section 4 (pasted verbatim, before anything of mine)

Four roots, three shapes. Section 4 is reproduced verbatim for each, and
section 5 (CONTINUABILITY) with it, because on three of the four roots
section 4 rules every box OUT and section 5 is where the defect is visible.

Commands, re-runnable:

    deepreason stop-report experiments/2026-09-01-live-all-modules-p-a1/run
    deepreason stop-report experiments/2026-09-02-live-p-a2-corrected/run
    deepreason stop-report experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/retired-1cycle-run-292f964edb58e58ef0e7d957f29bac55
    deepreason stop-report experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/run-fe00609058e10605590206d51ab2b7a0

### Shape 1 — P-A1, failed terminal (`4565139800…`)

```
## 4. THE STOP, CLASSIFIED

Stop message: `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at /workflow/insufficient_capability_by_route_seat: route seat has terminally exhausted its smallest authorized contract`

Boxes ranked by evidence:

### 1. ENVIRONMENT — SUPPORTED

- evidence FOR: transport wall: 41 RemoteDisconnected on endpoint ollama-glm-5.3

### 2. HARNESS — NO EVIDENCE EITHER WAY

- note: not claimable: ENVIRONMENT, MODEL still holds evidence. A harness verdict requires the other three to be ruled out.

### 3. CONFIGURATION — RULED OUT

- evidence RULING IT OUT: 6 field(s) were restored at run time from notices (listed below), but the stop names none of them; no run-config was supplied to diff against the manifest, so a mismatch there cannot be ruled out — re-run with --config to close that gap
- note: ADJUDICATION_STATUS_AUTHORITY_ENABLED = true was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/ADJUDICATION_STATUS_AUTHORITY_ENABLED)
- note: ENGAGED_CRITICISM_AUTHORITY = "defended_trial" was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/ENGAGED_CRITICISM_AUTHORITY)
- note: JUDGE_SEATS_ENABLED = true was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/JUDGE_SEATS_ENABLED)
- note: JUDGE_SUMMONS_PER_CYCLE = 2 was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/JUDGE_SUMMONS_PER_CYCLE)
- note: LEGACY_CRITICISM_ENABLED = false was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/LEGACY_CRITICISM_ENABLED)
- note: SCHOOL_SEATS_ENABLED = true was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/SCHOOL_SEATS_ENABLED)
- note: reasoning omitted → provider default on: argumentative_critic#0 (deepseek-v4-pro:0813), conjecturer#0 (deepseek-v4-pro:0813), conjecturer#1 (glm-5.3), defender#0 (glm-5.3), grounding_reviewer#0 (glm-5.3), judge#0 (qwen3.5:397b), judge#1 (gpt-oss:120b), property_designer#0 (deepseek-v4-pro:0813), summarizer#0 (glm-5.3), synthesizer#0 (glm-5.3), thesis#0 (deepseek-v4-pro:0813), variator#0 (deepseek-v4-pro:0813), vision_critic#0 (glm-5.3) — an omitted knob is the provider's DEFAULT, not 'off'. NO PROFILE ENTRY consulted: whether these models need an explicit value is a model-profile question
- note: split protocol armed on: argumentative_critic#0, conjecturer#0, conjecturer#1, defender#0, judge#0, judge#1 — the split arms on an omitted knob

### 4. MODEL — SUPPORTED

- evidence FOR: the stop names seat exhaustion: "V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at /workflow/insufficient_capability_by_route_seat: route seat has terminally exhausted its smallest authorized contract"
- evidence FOR: argumentative_critic#0: 1 rejected completion(s) truncated at the cap
- evidence FOR: conjecturer#0: 1 attempt(s) rejected at /candidates/0/discharges/1/kind
- evidence FOR: conjecturer#0: 1 attempt(s) rejected at /candidates/2/counterconditions
- evidence FOR: conjecturer#0: 12 rejected completion(s) truncated at the cap
- evidence FOR: conjecturer#1: 3 rejected completion(s) truncated at the cap
- evidence FOR: defender#0: 2 rejected completion(s) truncated at the cap
- note: argumentative_critic#0 passed qualification 20/20 first-pass on batch-critic.v2 with 0 repairs
- note: argumentative_critic#0 passed qualification 20/20 first-pass on config-referee.v1 with 0 repairs
- note: argumentative_critic#0 passed qualification 20/20 first-pass on critic.atomic-target.v1 with 0 repairs
- note: conjecturer#0 passed qualification 20/20 first-pass on conjecturer.atomic-candidate.v1 with 0 repairs
- note: conjecturer#0 passed qualification 20/20 first-pass on conjecturer.turn.v6 with 0 repairs
- note: conjecturer#0 passed qualification 20/20 first-pass on scratch.block.compact.v1 with 0 repairs
- note: conjecturer#0 passed qualification 20/20 first-pass on scratch.block.minimal.v1 with 0 repairs
- note: conjecturer#1 passed qualification 20/20 first-pass on conjecturer.atomic-candidate.v1 with 0 repairs
- note: conjecturer#1 passed qualification 20/20 first-pass on conjecturer.turn.v6 with 0 repairs
- note: defender#0 passed qualification 20/20 first-pass on defender.direct.v1 with 0 repairs
- note: judge#0 passed qualification 20/20 first-pass on judgeruling.direct.v1 with 0 repairs
- note: judge#1 passed qualification 20/20 first-pass on judgeruling.direct.v1 with 0 repairs
- note: a seat that passed its form at full marks did not lose the ability between qualification and the run — look to CONFIGURATION or ENVIRONMENT first

## 5. CONTINUABILITY

- state: failed
- stop_reason: operational_failure
- terminal_lifecycle_refusal: TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL
- verify_root: {"checks": [], "source": "stored", "violations": 0}
- continue: **REFUSED** — the record carries TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL
- amend: **REFUSED** — the record carries TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL
```

### Shape 2 — P-A2 epoch 4, killed run (`63e48f5741…`)

```
## 4. THE STOP, CLASSIFIED

Stop message: `(none recorded)`

Boxes ranked by evidence:

### 1. HARNESS — NO EVIDENCE EITHER WAY

- note: not claimable: MODEL still holds evidence. A harness verdict requires the other three to be ruled out.

### 2. CONFIGURATION — RULED OUT

- evidence RULING IT OUT: 7 field(s) were restored at run time from notices (listed below), but the stop names none of them; no run-config was supplied to diff against the manifest, so a mismatch there cannot be ruled out — re-run with --config to close that gap
- note: ADJUDICATION_STATUS_AUTHORITY_ENABLED = true was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/ADJUDICATION_STATUS_AUTHORITY_ENABLED)
- note: ENGAGED_CRITICISM_AUTHORITY = "defended_trial" was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/ENGAGED_CRITICISM_AUTHORITY)
- note: JUDGE_SEATS_ENABLED = true was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/JUDGE_SEATS_ENABLED)
- note: JUDGE_SUMMONS_PER_CYCLE = 2 was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/JUDGE_SUMMONS_PER_CYCLE)
- note: LEGACY_CRITICISM_ENABLED = false was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/LEGACY_CRITICISM_ENABLED)
- note: SCHOOL_SEATS_ENABLED = true was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/SCHOOL_SEATS_ENABLED)
- note: SPLIT_BUDGET_SEAT_PROTOCOL = "off" was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/SPLIT_BUDGET_SEAT_PROTOCOL)
- note: reasoning omitted → provider default on: argumentative_critic#0 (deepseek-v4-pro:0813), conjecturer#0 (deepseek-v4-pro:0813), grounding_reviewer#0 (glm-5.3), judge#0 (qwen3.5:397b), judge#1 (gpt-oss:120b), property_designer#0 (deepseek-v4-pro:0813), thesis#0 (deepseek-v4-pro:0813), variator#0 (deepseek-v4-pro:0813) — an omitted knob is the provider's DEFAULT, not 'off'. NO PROFILE ENTRY consulted: whether these models need an explicit value is a model-profile question

### 3. ENVIRONMENT — RULED OUT

- evidence RULING IT OUT: no HTTP 429, no transport-fault streak, and no qualification case carrying an environment failure code

### 4. MODEL — SUPPORTED

- evidence FOR: argumentative_critic#0: 1 rejected completion(s) truncated at the cap
- evidence FOR: conjecturer#0: 1 rejected completion(s) truncated at the cap
- note: argumentative_critic#0 passed qualification 20/20 first-pass on batch-critic.v2 with 0 repairs
- note: argumentative_critic#0 passed qualification 20/20 first-pass on config-referee.v1 with 0 repairs
- note: argumentative_critic#0 passed qualification 20/20 first-pass on critic.atomic-target.v1 with 0 repairs
- note: conjecturer#0 passed qualification 20/20 first-pass on conjecturer.atomic-candidate.v1 with 0 repairs
- note: conjecturer#0 passed qualification 20/20 first-pass on conjecturer.turn.v6 with 0 repairs
- note: conjecturer#1 passed qualification 20/20 first-pass on conjecturer.atomic-candidate.v1 with 0 repairs
- note: conjecturer#1 passed qualification 20/20 first-pass on conjecturer.turn.v6 with 0 repairs
- note: defender#0 passed qualification 20/20 first-pass on defender.direct.v1 with 0 repairs
- note: variator#0 passed qualification 20/20 first-pass on variator.direct.v1 with 0 repairs
- note: a seat that passed its form at full marks did not lose the ability between qualification and the run — look to CONFIGURATION or ENVIRONMENT first

## 5. CONTINUABILITY

- state: running
- stop_reason: None
- terminal_lifecycle_refusal: (none)
- verify_root: {"checks": [], "source": "stored", "violations": 0}
- continue: **UNKNOWN** — the run is in state 'running', not at a terminal
- amend: **UNKNOWN** — the run is in state 'running', not at a terminal
```

### Shape 3a — the one-cycle clean run (`292f964edb…`)

```
## 4. THE STOP, CLASSIFIED

Stop message: `(none recorded)`

Boxes ranked by evidence:

### 1. CONFIGURATION — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

### 2. ENVIRONMENT — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

### 3. MODEL — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

### 4. HARNESS — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

## 5. CONTINUABILITY

- state: completed
- stop_reason: budget_exhausted
- terminal_lifecycle_refusal: STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
- verify_root: {"checks": [], "source": "stored", "violations": 0}
- continue: **REFUSED** — the record carries STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
- amend: **REFUSED** — the record carries STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
```

### Shape 3b — the four-cycle clean control (`fe00609058…`)

```
## 4. THE STOP, CLASSIFIED

Stop message: `(none recorded)`

Boxes ranked by evidence:

### 1. CONFIGURATION — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

### 2. ENVIRONMENT — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

### 3. MODEL — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

### 4. HARNESS — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

## 5. CONTINUABILITY

- state: completed
- stop_reason: budget_exhausted
- terminal_lifecycle_refusal: STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
- verify_root: {"checks": [], "source": "stored", "violations": 0}
- continue: **REFUSED** — the record carries STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
- amend: **REFUSED** — the record carries STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
```

---

## What the four reports establish before any code is opened

Every one of the four roots reports, in section 5:

    verify_root: {"checks": [], "source": "stored", "violations": 0}

So on the record's own instrument NO root is corrupt, and the integrity gate
the 2026-08-29 security clause installed (`CONTINUE_RECORD_NOT_VERIFIED` /
`AMEND_RECORD_NOT_VERIFIED`, `runtime/continuation.py:494`,
`amendment/apply.py:533`) is not what refuses any of them. Every refusal is a
LIFECYCLE refusal. That is the whole defect in one line: the gate designed to
refuse tampered records is silent, and a different predicate refuses intact
ones.

Read across the four, section 5 says:

| root | state | stop_reason | terminal_lifecycle_refusal | continue |
|---|---|---|---|---|
| P-A1 `4565139800…` | failed | operational_failure | TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL | REFUSED |
| P-A2 e4 `63e48f5741…` | running | None | (none) | UNKNOWN — not at a terminal |
| 1-cycle `292f964edb…` | completed | budget_exhausted | STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY | REFUSED |
| 4-cycle `fe00609058…` | completed | budget_exhausted | STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY | REFUSED |

Note what section 4 says about the two clean roots: **all four boxes RULED
OUT**, with the report's own words — "the run reached a clean terminal
(state='completed', stop_reason='budget_exhausted'); there is no failure to
attribute." A run with nothing to attribute and nothing wrong with its record
cannot be continued. That is the defect, stated by the instrument.

P-A2 epoch 4's section 5 reads `state: running` because `run-status.json` is
`progress.jsonl`'s last line and the container kill left it there; `finalize`
appends the terminal to the LOG without re-emitting progress. The finalize
attempt and its refusal are recorded in that tranche's own
`finalize_epoch4.log` / `continue_epoch4.log`, and its RESULTS.md Segment 8
(F8) states the outcome: a clean `budget_exhausted` terminal was written and
`continue` was still refused STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY on
"10 outstanding work items".

## Primary cause

**One predicate, evaluated in the wrong place, refuses a receipt that the
run's own recovery machinery is built to make earnable — and a second site
declines to ask for the receipt at all.**

`workflow/lifecycle.py:236-238` — `build_stopped_lifecycle` takes an
`outstanding_work_snapshot` and raises `UnfinishedWorkflowAuthorityError`
whenever

    if snapshot.outstanding_work or snapshot.unconsumed_bound_call_seqs:

The second disjunct is the real protection: an *unconsumed bound call* is a
provider call whose result nobody has read, and closing a stop over one either
double-spends it on resume or drops a recorded result. The first disjunct is
much wider than that protection, and on all four roots it is the ONLY one that
fires — measured, not inferred (`proof/outstanding_census.py`, below):

| root | outstanding work items | unconsumed (orphaned) provider call seqs |
|---|---|---|
| P-A1 `4565139800…` | 6 | **0** |
| P-A2 e4 `63e48f5741…` | 10 | **0** |
| 1-cycle `292f964edb…` | 2 | **0** |
| 4-cycle `fe00609058…` | 6 | **0** |

Zero everywhere. And `outstanding_work_snapshot` itself already guarantees
this is not luck: `lifecycle.py:136-138` raises
`"unconsumed provider call is not represented as outstanding work"` unless the
orphaned-call set equals the represented set, so `unconsumed_bound_call_seqs`
is by construction the complete inventory of unread provider authority.

What the outstanding items actually ARE. On the four-cycle clean control, 144
of its 150 transactional work items closed normally and these 6 did not:

    sha256:2c02510 kind=CONJECTURE outcome=provider_result admissions=[] terminal=None
    sha256:4e90f08 kind=CONJECTURE outcome=provider_result admissions=[] terminal=None
    sha256:6afc02c kind=CONJECTURE outcome=provider_result admissions=[] terminal=None
    sha256:8984177 kind=CONJECTURE outcome=provider_result admissions=[] terminal=None
    sha256:91a35d7 kind=CONJECTURE outcome=provider_result admissions=[] terminal=None
    sha256:a09905e kind=CONJECTURE outcome=provider_result admissions=[] terminal=None

Across all four roots the census finds THREE sub-shapes, not one, and the
distinction is load-bearing for the fix, so it is stated here rather than
smoothed over:

| sub-shape | where | count | recoverable by the existing path? |
|---|---|---|---|
| `CONJECTURE`, `outcome=provider_result`, no admission | all four roots | 21 | YES — `recover_conjecture_admission` |
| `REPAIR`, `outcome=provider_result`, no admission | P-A1 only | 5 | YES — `recover_nonconjecture_admission` |
| `CRITICISM`, `outcome=None` (issued, no provider attempt) | P-A2 e4 only | 1 | **NO** — there is no result to admit |

23 of the 24 outstanding items across the four roots carry a completed
provider result awaiting admission — EXACTLY the selection predicate of the
run's own crash-recovery path. `scheduler/scheduler.py:429-499`
`_recover_workflow_prefixes` runs before the first scheduler cycle is
authorized, calls `InquiryTransactionService.recover_incomplete()`, routes
each recovered attempt through `recover_conjecture_admission` or
`recover_nonconjecture_admission` by task kind, and then asserts its own
success:

    if self.harness.workflow_state.outstanding_work_order_ids:
        raise RuntimeError("transaction recovery left unfinished authority")

So for 23 of 24 items the machinery to re-enter this work already exists,
already runs on every resumed scheduler, and already fails loudly if it
cannot finish. The stop refuses before it can ever be reached. The receipt is
withheld for a condition whose designated remedy is the very operation the
withheld receipt blocks.

**The twenty-fourth item is the honest exception, and the fix must answer it
rather than hide it.** P-A2 epoch 4's `sha256:93672cb` is a CRITICISM work
order that was ISSUED and whose provider call never produced an attempt
record — the container kill landed between dispatch and the atomic
attempt append. It carries no unconsumed call seq (the census reads 0), so
it is not unread provider authority; it is a work order with nothing behind
it. `recover_incomplete()` will not close it, because there is no result to
admit. That single item is why the fix cannot be "relax the predicate and
trust recovery": it needs a typed ABANDONMENT road for outstanding work with
no provider attempt, or the resumed scheduler's own
`"transaction recovery left unfinished authority"` assertion will fire on
exactly the killed-run shape this tranche exists to make resumable. Whether
that road can be built without a new record kind (frozen surface 3, a PRICED
STOP under the window instruction) is the first question dr-propose-fix must
answer, and it is answered there, not here.

Shape 1 is the same defect at a second site, in its declarative form:
`application/text_runs.py:1618-1631` writes the run-stop record and the
checkpoint for an `operational_failure` terminal and then deliberately takes
no receipt at all, recording `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`;
its own comment states that 16 committed roots stand in that state.
`workflow/lifecycle.py:28` `RESUMABLE_STOP_REASONS = frozenset({"converged",
"budget_exhausted"})` closes the same door from the other side.

Shapes 2 and 3 are provably ONE code path, not two that resemble each other:
`finalize_stopped_root` (`text_runs.py:583`) calls `terminalize_text_run`, the
same function the ordinary clean stop calls (`text_runs.py:414`), which calls
`_record_exhaustion_lifecycle_stop` (`text_runs.py:233`), which calls
`build_stopped_lifecycle` and converts `UnfinishedWorkflowAuthorityError` into
the recorded refusal at `text_runs.py:308-319`. This is why the killed run and
the clean run produce the same refusal code on the same count of the same kind
of item.

**The three shapes are ONE defect.** The window instruction required a STOP
and a proposed split if the record showed otherwise. It does not: shapes 2 and
3 share a call path literally, and shape 1 is the same missing receipt taken
by declaration instead of by predicate. No split is proposed.

## Evidence

- `experiments/2026-09-01-live-all-modules-p-a1/run/run-status.json` →
  `state: failed`, `stop_reason: operational_failure`,
  `terminal_lifecycle_refusal: TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`,
  cycle 5, 1 093 086 of 3 000 000 tokens spent. Section 5 of its report:
  `continue: REFUSED`, `amend: REFUSED`, `verify_root … "violations": 0`.
- Section 5 of all four reports → `verify_root … "violations": 0` on every
  root. No refusal in this tranche is an integrity refusal.
- Section 4 of both clean roots → all four boxes RULED OUT, "there is no
  failure to attribute".
- `proof/outstanding_census.py` (committed, re-runnable) → the table above:
  6 / 10 / 2 / 6 outstanding work items and 0 unconsumed provider call seqs
  across the four roots, plus the six-item dump showing every one is
  `outcome=provider_result, admissions=[], terminal=None`.
- `experiments/2026-09-02-live-p-a2-corrected/RESULTS.md` Segment 8 (F8) →
  `finalize` wrote a clean `budget_exhausted` terminal and `continue` was
  still refused STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY, 10 outstanding
  work items.
- `experiments/2026-09-03-change-provenance-history-channel/PARKED.md` P1 →
  `stop_reason_resumable: true` published beside a `continue` that refuses.
  `application/results.py:512` computes that field as
  `stop["reason"] in RESUMABLE_STOP_REASONS`, which is TRUE for
  `budget_exhausted` regardless of whether the receipt was taken; the
  companion `_continuation_authority` reader (`results.py:462`) reports the
  other half. The two are not contradictory as code, but the pair is
  unreadable as a report, and after the fix both must read the same way.

## Implicated code (three sites, matching GOAL.md's in-scope list)

- `src/deepreason/workflow/lifecycle.py:236` — the over-wide STOPPED refusal;
  and `:28` `RESUMABLE_STOP_REASONS`; and `:317` / `:330`, the two symmetric
  refusals inside `build_resumed_lifecycle` that must move with it.
- `src/deepreason/application/text_runs.py:1618` — the failure terminal that
  takes no receipt by declaration.
- `src/deepreason/runtime/continuation.py:423` — `CONTINUE_TYPED_STOP_REQUIRED`,
  the refusal the withheld receipt produces at the operator's end.

## Falsifiable prediction (what dr-reproduce must show)

Against the deterministic stub, with no live provider:

1. Drive a managed run to a clean `budget_exhausted` terminal that leaves at
   least one outstanding transactional work item. Predicted:
   `run-result.json` carries
   `terminal_lifecycle_refusal.code == "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"`,
   `deepreason continue` exits non-zero with `CONTINUE_TYPED_STOP_REQUIRED`,
   and `outstanding_work_snapshot(...).unconsumed_bound_call_seqs == ()`
   on that root — the refusal fires on the first disjunct alone.
2. Drive a run to an `operational_failure` terminal. Predicted:
   `terminal_lifecycle_refusal.code ==
   "TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL"` and `continue` refuses.
3. Kill a run mid-work, then `deepreason finalize`. Predicted: the finalize
   succeeds, and the resulting terminal carries the SAME
   `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY` as case 1 — the shared
   `terminalize_text_run` path, demonstrated rather than asserted.
4. On the case-1 root, `record_verification_refusal(root)` returns `None`
   (the integrity gate is satisfied), and returns a non-`None` SECURITY-channel
   refusal after one byte of `log.jsonl` is altered. This pins that the gate
   which SHOULD decide continuation is working and is simply never consulted,
   because the lifecycle refusal fires first.

If (1) shows a non-empty `unconsumed_bound_call_seqs`, this diagnosis is WRONG
and the refusal is protecting real unread provider authority; the tranche
returns to dr-diagnose.

## Ruled out

**"The runs are corrupt, and the refusal is the integrity gate doing its
job."** Ruled out by section 5 of all four reports: `verify_root` reports
`"violations": 0` on every root, and every observed refusal code
(`TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`,
`STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`,
`CONTINUE_TYPED_STOP_REQUIRED`, `CONTINUE_STOP_REQUIRED`) is raised before
`record_verification_refusal` is ever called — that call sits at
`continuation.py:494`, after the stop, checkpoint and fence preconditions.
The security gate installed 2026-08-31 is intact and untouched by this
diagnosis.

**Also checked and NOT the cause: a recurrence of a recorded trap.**
`DR-SUB-workflow`'s Traps carry a `RESUMABLE_STOP_REASONS` entry, but it
concerns test COVERAGE of the guard, not the guard's width, and its census
finding ("all 16 stopped on budget_exhausted") is consistent with what is
measured here. `DR-CON-run-identity`'s "a root that ran real cycles cannot be
continued" trap is the 2026-08-13 `run --run-manifest` defect, FIXED by path
unification; these four roots all came through the unified managed path, so
that trap is not recurring — this is a new failure mode and earns a new Traps
entry in the fix commit.
