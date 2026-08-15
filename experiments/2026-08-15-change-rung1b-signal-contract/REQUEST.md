# REQUEST — Rung 1b: the signal contract (part i, the declaration side)

Route: `dr-change-orchestrator`. **Rung 1b of the v2 calculus program**
(`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`).

Date: 2026-08-15. Branch: `claude/calculus-reconciliation-v2-qqghvn`.

## 1. Authority

Operator, verbatim, after the Rung 1 delivery report (which stated "Next is
Rung 1b, the signal contract — unblocked"):

> Do it

The substantive authority is the operator's six-clause design, ledgered verbatim
at `experiments/2026-08-14-change-calculus-reconciliation-v2/REQUEST.md`
Amendment 2 (R29–R36), reconciled as drift rows SC-1 … SC-6, and now also a
standing design law in CLAUDE.md (landed by Rung 1).

## 2. Requirements (inherited, renumbered local)

| # | Requirement | v2 row |
|---|---|---|
| L1 | The registry is a CONTRACT: every signal declares **name, unit, producer-agnostic semantics, staleness bound**. New setups add signals **by declaration through this channel**. | SC-1 |
| L2 | The existing registry is **included, not superseded** — the operator's clause (1) says so explicitly. | SC-1 |
| L3 | The allocation controller consumes **only** the signal interface, pinned by an architecture test that FAILS if `controller.py` imports schools / rules / criticism internals. | SC-3 |
| L4 | Ledger as an **INV- map document with checks** and **two REC- recipes** (`add-signal`, `revise-allocation-policy`). | SC-6 |
| L5 | **No new skill or workflow** until two recorded recipe failures. | SC-6 / R35 |
| L6 | The map moves in the SAME commit as the code. | program-wide |
| L7 | Every committed root replays byte-unchanged. | program-wide |

## 3. Scope decision: 1b is split, and this is part i

`LADDER.md` estimated Rung 1b at 450–650 lines across six clauses. Scoping found
a clean seam inside it, and the tranche is split along that seam rather than
delivered as one oversized rung:

| Part | Clauses | What it is |
|---|---|---|
| **1b-i (this tranche)** | SC-1, SC-3, SC-6 | the **declaration side** — the contract itself, the boundary that keeps consumption interface-only, and the governing documents |
| **1b-ii (next)** | SC-2, SC-4, SC-5 | the **consumption side** — seat-instance keying, the compiled topology matrix, and the `allocation open-loop for signal X` notice |

**Why here.** Every clause in 1b-ii changes what the allocation controller
*does*; every clause in 1b-i changes what a signal *is* and who may read it.
The declaration side is also the half the rest of the v2 program depends on —
Rung 2 onward emit new signals, and they must have a channel to declare
themselves through. Splitting the other way would leave that dependency unmet.

**Honest note on the split:** it is a decision made by this tranche, not by the
operator, and it means Rung 1b is complete only when 1b-ii lands. It is recorded
here and in the LADDER rather than absorbed silently.

## 4. Map preflight

- `DR-INV-frozen-surfaces` — read first. **Forecast: zero contact.**
- `DR-CON-standing-and-background` — minted by Rung 1; unaffected.
- `DR-SUB-scheduler` — owns `controller.py`, which L3's test pins.
- **New:** `DR-INV-signal-contract` (L4), minted here, plus
  `DR-REC-add-signal` and `DR-REC-revise-allocation-policy`.

## 5. Amendments

### Amendment 1 — 2026-08-15, the mid-flight rider (cross-version compatibility retired)

Appended verbatim BEFORE acting on it, per the ledger rule.

> MID-FLIGHT RIDER (append to REQUEST.md as an amendment before acting on
> it, per the ledger rule): new standing law on main, CLAUDE.md 2026-08-14
> — "old runs do not need to be valid or returnable... new versions are
> optimised for new functions." Cross-version compatibility is retired.
> Effect on this program: finish Rung 1 as specified (its scope is
> documentation/vocabulary and gains nothing from the law), then REVISE
> LADDER.md at the rung boundary before Rung 2 opens: drop every
> replay-byte-unchanged proof obligation, old-root sweep gate, and
> reader-widening-only design constraint from all remaining rungs; where a
> rung chose an awkward additive shape only for old-root compatibility,
> re-choose the clean shape the calculus is better served by. Scope
> boundary, not to be over-read: a current-version run's record stays
> typed, append-only, and replayable by the code that wrote it.
> docs/AUDIT_BASELINES.md already records the sweep's narrowed scope.

The law itself is on `main` at `003d57ffa`, and supersedes the sentence that
previously closed the frozen-surfaces list.

**Effect on THIS tranche (1b-i):**

| Local requirement | Status under the law |
|---|---|
| **L7** — "every committed root replays byte-unchanged" | **RETIRED.** No old-root sweep is owed. Acceptance check A7 keeps only its `blast_radius` half, which discloses frozen-surface contact for the CURRENT version and is unaffected |
| L1–L6 | unchanged — none of them existed for cross-version reasons |

**Did this tranche choose an awkward shape for old-root compatibility?**
Checked, and no. The one design that looks like a compatibility concession —
`SIGNALS`/`PREFIXES` kept as DERIVED views rather than replaced — was chosen so
that the three CURRENT consumers (`report.py`, `cli/main.py`,
`tests/test_signals.py`) read one source of truth instead of two. That is
within-version cohesion, which the law explicitly does not touch. The
`unspecified` debt marker is an honesty device, not a migration shim. Nothing
here is re-chosen.

The LADDER revision the rider orders is a separate act at the rung boundary,
after this tranche closes.
