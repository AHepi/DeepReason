---
name: dr-audit-goal-trace
description: Audit dimension - verify every ledgered operator design law is actually enforced somewhere in code or gates, so stated goals and shipped behavior cannot silently diverge. Invoked by dr-audit-orchestrator when goal-trace.md is missing.
---

# Audit: operator goals vs enforcement

Entry: `LEDGER.md` exists, `goal-trace.md` missing. Exit:
`goal-trace.md` written, one row per law, proofs in `proof/`.

The operator's goals live in two ledgers: CLAUDE.md §"Operator design
laws" (standing, verbatim-quoted) and each tranche's REQUEST.md (per
change). This worker traces the STANDING laws; a per-tranche trace is
dr-validate-change's job, not this one.

A law counts as ENFORCED only when a mechanism would visibly fail if
the law were violated — a test, a typed refusal/notice, a gate. Prose
restating the law enforces nothing.

## Operations

1. Law census: extract every bolded law heading from CLAUDE.md
   §"Operator design laws" into `proof/goal-laws.txt`, one row each,
   with its date and verbatim kernel.
2. For each law, three scans, outputs saved to `proof/goal-<n>.txt`:
   a. Mechanism scan: `rg -l -i '<law key terms>' src/deepreason/`
   b. Test scan: `rg -l -i '<law key terms>' tests/`
   c. Notice/refusal scan: `rg -n '<law's typed string, if any>' src/`
3. Verdict per law, exactly one of:
   - `enforced` — row names the mechanism file AND the test that goes
     red on violation (both cited from the scans).
   - `partially-enforced` — mechanism exists, no test pins it; the
     row names which half is missing.
   - `unenforced` — scans empty; the law lives only in prose. The
     pasted empty scans are the proof (G2).
   - `process-law` — governs agent/operator behavior, not code (e.g.
     a working-style rule); code enforcement is not expected. Saying
     `process-law` requires one sentence naming WHO enforces it
     instead (the workflow file that carries it).
4. For every `unenforced` and `partially-enforced` row: PARK a prompt
   proposing the smallest mechanism that would make violation visible
   (a regression test, a typed notice), route dr-change-orchestrator.
   Proposing is this worker's ceiling — choosing is the operator's.
5. Write `goal-trace.md`: the table, a count line, and one closing
   list: laws added since the last audit (diff `proof/goal-laws.txt`
   against the previous audit tranche's copy, if one exists).

## GATE

Pass: every law in `proof/goal-laws.txt` has exactly one verdict row;
every `enforced` row cites file + test; every `unenforced` row cites
empty scans. Verdict labels: `enforced` | `partially-enforced` |
`unenforced` | `process-law`.

## Activation plant (first run)

Add a fabricated law line to the copy in `proof/goal-laws.txt`; the
scans must come back empty and the row must read `unenforced`. Remove
the fabricated row, note the plant in ACTIVATION.md.

## Outlets

| Situation | Outlet |
|---|---|
| Impulse to build the missing enforcement now | PARK — mechanism prompt, route dr-change-orchestrator |
| A law reads ambiguous against the code | row `partially-enforced`, note the ambiguity in one sentence; the parked prompt asks the operator to word the law's testable form |
| Two laws conflict | row both, note the conflict, PARK a reconciliation question for the operator — never pick the winner here |
