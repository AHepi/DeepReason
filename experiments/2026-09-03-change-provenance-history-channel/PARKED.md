# Parked — found during this tranche, deliberately NOT fixed here

A defect found mid-change is PARKED, not fixed (`dr-change-orchestrator`
scope contract). Each entry is written for its future runner at park time: one
line of WHAT, then a ready-to-send prompt, so the follow-up costs the operator
a paste rather than an authoring session.

---

## P1 — a 1-cycle run stops un-continuable, while its own record says it is resumable

**What.** `deepreason reason --cycles 1` terminates `budget_exhausted` carrying
`terminal_lifecycle_refusal: STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`
("2 outstanding work items, 0 unconsumed bound calls"), and every subsequent
`deepreason --root R continue --budget cycles=1` is refused
`CONTINUE_TYPED_STOP_REQUIRED`. The same `results --json` payload reports
`"stop_reason_resumable": true`. So one record says the stop is resumable and
the operation that would resume it refuses.

**Why it is not cosmetic.** The operator's law of 2026-08-29 (CLAUDE.md,
verbatim: "clean stop. with an assurance that continuing is possible. Too often
an operational failure overlooks securing enough checkpoints to allow relaunches
or forgets to ensure continuing is possible that trigger corrupted stops") makes
"every terminal leaves checkpoints sufficient for relaunch" a law, and makes a
stop that cannot assure continuability a defect in itself. This looks like
exactly that case, on the ordinary managed path, with no exotic configuration.

**Evidence, committed in this tranche.**

- root: `experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/retired-1cycle-run-292f964edb58e58ef0e7d957f29bac55`
  (retired by rename, contents never edited)
- `progress.jsonl` last line: `cycle 1`, `state completed`,
  `token_spend 94361` against `token_limit 400000`, `accepted 0`, `refuted 0`,
  `stop_reason budget_exhausted`,
  `terminal_lifecycle_refusal STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`
- driver log: `runs/m1_h0.log`, the three `CONTINUE_TYPED_STOP_REQUIRED` / `rc=1`
  lines at 01:12:57, 01:13:10, 01:13:25
- the cycle itself SUCCEEDED: 40 artifact objects, 18 claim-bearing conjectures
  on the seed problem, 3 schools, D4 0.936, D5 0.276

**What it cost here.** The M1/M3 arms were designed as `reason --cycles 1` plus
three `continue` steps so history could be re-rendered between cycles. That
design does not run. The arms were redesigned to a single `--cycles 4` call with
the history seeded once beforehand from a completed control root — which is
closer to the window instruction's own wording ("rendered OFFLINE from the
record") and is what `runs/arm.sh` now does. No harness code was touched.

**Not investigated, and stated so the next runner does not inherit a guess.**
Whether the refusal is correct and the `stop_reason_resumable: true` is the bug,
or the reverse; whether `--cycles 1` specifically leaves the two work items
outstanding or whether any cycle count does; and whether the four-cycle run now
in flight terminates the same way. The last of these will be answerable from
this tranche's own committed roots once the arms finish.

### Ready-to-send prompt

```
Route: deepreason-orchestrator (defect).

GOAL: one bounded question — does a managed `deepreason reason --cycles N` run
leave a terminal that `deepreason continue` will accept, and if not, which of
the two typed records is wrong?

The record says both things at once. On run
experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/
retired-1cycle-run-292f964edb58e58ef0e7d957f29bac55 (committed, read-only;
open it with Harness(root, read_only=True) — a writable open repairs and so
destroys the evidence):

  - run-status/progress: state=completed, stop_reason=budget_exhausted,
    terminal_lifecycle_refusal=STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY,
    detail "2 outstanding work items, 0 unconsumed bound calls"
  - `deepreason results --json` on the same root: "stop_reason_resumable": true
  - three `continue --budget cycles=1` attempts: CONTINUE_TYPED_STOP_REQUIRED,
    rc=1 each (runs/m1_h0.log, 01:12:57 / 01:13:10 / 01:13:25)

Start at dr-diagnose and READ THE RECORD BEFORE THE CODE. The two outstanding
work items are the thing to identify first: which work items, issued in which
cycle, and why the stop did not drain or finalize them.

Frame it as a fork the record can decide, not as a fix to apply:
  W — the stop is genuinely corrupt (work items left outstanding that a clean
      terminal should have drained), and `stop_reason_resumable` is lying;
  R — the stop is legitimate and `continue` over-refuses, in which case the
      refusal predicate is the defect and the record is honest.

Then check whether this tranche's FOUR-cycle roots in the same directory
terminate the same way; if they do not, the cycle count is part of the cause
and that narrows W/R sharply.

AUTHORITY: the operator's 2026-08-29 law in CLAUDE.md — "clean stop. with an
assurance that continuing is possible ... checkpoints need to be hardned" —
makes a stop that cannot assure continuability a defect, so this is in scope
for a fix rather than a documentation note. Do NOT weaken the continue-side
integrity gate to get green: the same law says a tampered record must not buy
a resumable run.

END STATE: DIAGNOSIS.md naming one primary cause with record pointers, REPRO.md
with the smallest offline artifact, and either a FIX.md or a recorded finding
that the behaviour is correct and the resumable flag is what must change.
```

---

## P2 — `deepreason config` does not echo every `Config` field (minor, unblocked)

**What.** `deepreason --config <yaml> config` echoes `PACK_TOKEN_BUDGET`
correctly, which is what let this tranche's M2 guard work. Noted here only
because the guard was written after discovering that the OBVIOUS mechanism —
an environment variable — reaches nothing: `Config` carries no env reader, so
`DEEPREASON_PACK_TOKEN_BUDGET=12345` leaves `Config().PACK_TOKEN_BUDGET` at
2500 silently.

**Why it is worth a line.** Nothing is broken; the YAML path is the supported
one. But an operator or agent reaching for an env override gets no error, no
warning, and a run at the default — and in a sweep that produces arms which are
all secretly the control. Under the 2026-08-28 gates-with-warnings law, a knob
that is silently ignored is the shape the law exists to prevent, even though
this is a non-existent knob rather than a disabled gate.

**Disposition.** Not a defect in shipped behaviour; a documentation and
ergonomics finding. Folded into the next audit rather than given its own
tranche.
