# Delivered: T6 — regression, goldens, the record (S10)
Sub-tranche T6 of the mini isolation programme, run 2026-09-06 on the
operator's "Do T6" (REQUEST.md Amendment 2).
Branch: `claude/mini-isolation-t3-t5-7tsc6d` (pushed, tree clean; head in the step-51 commit).
Validation: `T6/VALIDATION.md`, PASS.

## What changed

Nothing in code. T6 is the programme's own regression boundary: it records,
once, the five instruments SPEC S10 names, on the tree as T3, T4 and T5 left
it. Every one is green.

- The documented gate on an idle box: 5084 passed, 6 skipped, 0 failed, the
  same count as before the programme's T3 began.
- Mini's own suite, explicitly, because the documented gate never collects
  it: 164 passed (95 when the programme was designed).
- The full harness's two briefs: byte-identical to before the programme.
- A mini isolation run of three cycles, conjecture then criticism then
  commitment with commitments off, against the deterministic stub: six
  free-prose conjectures standing, six criticisms and six proposals in the
  record, the verifier reporting nothing, and the replayed digest equal to
  the live session's.
- Both wheel smokes, which no gate runs: green, no pin moved.

The whole window's reach into the full harness's code is one file and 29
lines, the two public entries in the pack renderer. No frozen surface moved.

## Reconciliation

Every requirement's disposition is T5/DELIVERY.md's, re-confirmed here by
the instruments rather than restated. The one new row:

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R15 (Amdt 2) | "Do T6" | **done** — steps 46–51 in this window; T7 stays with the last window | commit `c66aad16b`; `T6/VALIDATION.md` |

## Assumptions the operator may override

None new. T5/DELIVERY.md's three stand: a proposal is a record, not an
artifact; every mini call's role names the leased route; the legacy prompt
gains one header line.

## Map delta

No map change: T6 changed no behaviour and no document, so it owes no check.
The full map run T5 recorded covers this tree exactly (only two stamp lines
moved since). left stale: 22 documents, none of them this programme's.

## Errata

errata: none. No committed document was found to state something false.

## Parked (not done, not promised)

No new entry. P1 (mini's tests outside the gate) was felt again here and
stands; P8 disposed in T5; P9 stands.

**recommended next: T7 (steps 52–57), the measure, in the last window.** It
is the only thing left in the programme, and the only thing that can say
whether any of this is better than a single call: a pre-registered blind
comparison, criteria sealed before an arm runs, length held constant, per-
seat spend reported, and an inconclusive result recorded as inconclusive.
Before it launches: a green soak on the launch configuration, and a key,
which this window did not have.
