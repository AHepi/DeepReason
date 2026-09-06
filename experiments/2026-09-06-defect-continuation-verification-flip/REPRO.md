# Reproduction: the flip, offline, in fifteen events

`repro.py` builds ONE canonical v6 root through the real machinery
(`tests/test_v6_controller3_replay_verification._canonical_root`: two
conjecturer calls, both admitted, 15 events) and verifies three states of it.
No provider, no key, no committed root touched.

| state | what it is |
|---|---|
| `admitted` | the root as the run wrote it |
| `abandoned` | the log truncated immediately after the second provider result — the work order is open, no admission, no terminal, exactly as ARM R's three were when it died |
| `closed` | `abandoned` plus the closure a no-op continuation writes: a semantic admission `schema_exhausted` and a work terminal `recovered_schema_exhausted` naming the SAME attempt, committed with its compact-recovery authority, appended after the old tail |

## Output, pasted

    admitted   violations=0  outstanding_work_orders=[]
    abandoned  violations=0  outstanding_work_orders=['sha256:08d73cf5d4b8ae5df29bfa1933431aaeaa927864e98c029c6ee07dad0d00b57a']
    closed     violations=1  outstanding_work_orders=[]
               attempt-validity: event seq=11: failed call must contain no valid attempt, got [0]

    REPRODUCED - the same wire-valid call verifies clean while its work order is
    open and violates once the work order is honestly closed

The violation's wording is identical to the three the real root carries
(`event seq=142/215/295: failed call must contain no valid attempt, got [0]`),
and it arrives the same way: not by changing the call, but by completing the
record around it.

## What the reproduction pins that the diagnosis could only argue

1. **The call is untouched across the flip.** The `closed` root's event 11 is
   the `abandoned` root's event 11, byte for byte; only events 12 and 13 were
   appended.
2. **An open work order is invisible to the verdict.** `abandoned` reports 0
   violations while naming the open work id in its own stats — the same
   asymmetry the real root shows (`outstanding_work_orders` listed all three
   and `valid` stayed true).
3. **The closure is well-formed.** It passes every other replay rule — the
   canonical `[compact-recovery-transition, work-terminal]` record shape, the
   admission's durable provider-result pairing, the route-seat recovery key.
   The record the resume writes is legal in every respect except the one
   `attempt-validity` invents for it.

## What it does NOT show

- It does not show the real root's three closures are byte-identical in
  construction to this stub's; they reference a compact-recovery authority
  written earlier in the same run, where the stub commits its own. The shape
  that matters — a non-admitted admission over a wire-valid attempt — is the
  same, and it is what the check reads.
- It does not decide whether an open work order SHOULD invalidate a record.
  That is the second, narrower question the diagnosis raises and parks.

## How to run

    python experiments/2026-09-06-defect-continuation-verification-flip/repro.py
    -> exit 0 and "REPRODUCED" on the unfixed tree

This script is the scaffold, not the regression. The committed test that
guards the fix is written in the implement phase, from this shape, with the
mutation proof the workflow requires.
