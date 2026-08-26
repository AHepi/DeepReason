# Parked — found while specifying F1, deliberately not fixed here

One tranche, one goal (`dr-change-orchestrator`, scope contract item 2). Each
entry is written for its FUTURE runner: one line of WHAT, then a ready-to-send
prompt. Nothing here is a defect this tranche introduced.

---

## P1 — `workflow-semantic-admission-v1.admitted_refs` resolve to nothing on disk

**What.** W2 measured that a criticism dispatch's own record pointer to the
artifact it produced does not resolve: 0 of 163 in P-R1. W2 worked around it by
matching on a 120-character normalized content prefix (86 of 89 in P-R1, 110 of
111 in P-C1), reporting the misses as `unlocatable-in-log` rather than dropping
them. F1 does NOT depend on this pointer — `open_criticisms` reads the critic
ARTIFACT and the `["scrutiny", target, critic]` Measure, both of which resolve —
so the defect is untouched and unfixed here.

**Evidence.** `experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`
segment 2, residue item 4.

```
Route: deepreason-orchestrator (this is a defect, not a change).
Goal, one sentence: workflow-semantic-admission-v1.admitted_refs must resolve
to the artifact the dispatch registered, so a criticism case can be linked to
its artifact by the record's own pointer instead of a content-prefix match.
Evidence to start from, in this order:
  1. experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md segment 2,
     residue item 4 (the finding, with its counts: 0 of 163 in P-R1).
  2. experiments/2026-08-26-run-anatomy-w2-criticism/census.py — the
     committed reader that had to work around it; its fallback is the
     120-character normalized prefix match.
  3. The writer: grep for "workflow-semantic-admission-v1" in
     src/deepreason/workflow/ and read what it puts in admitted_refs.
Map preflight first: DR-SEAM-rules-x-workflow, then DR-SUB-workflow.
Read docs/map/INV-frozen-surfaces.md before designing — replay-validation
record formats are frozen, and this may be a READER fix rather than a writer
change; establish which before proposing anything.
End state: a regression test that goes RED on the unfixed tree, a fix, and
W2's census.py re-run showing the pointer path resolving where the prefix
match previously carried it. Full gate 0 failed.
```

---

## P2 — the live A/B this tranche cannot substitute for

**What.** F1's S9 gate proves the CHANNEL DELIVERS (a responsive writer couples
above placebo iff the channel is on). It does not prove a real provider model
responds to what the channel shows it. Q1's own finding says that must not be
assumed: a pack's claim to have honoured a standing instruction is the least
reliable artifact in the trajectory. W2 parked this as its own P2 for the same
reason — the 35 roots that DID feed criticism back have no scalar score either.

**Evidence.** `experiments/2026-08-26-run-anatomy-w2-criticism/RESULTS.md`
segment 2, residue item 9; `docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q1, Q5.

```
Route: a MEASUREMENT tranche (read-only on src/ and tests/), not a change.
Goal, one sentence: on a live run with a run-owned scalar score, measure
whether F1's discharge-required criticism channel moves R1_mechanical
placebo-corrected coupling and the run's own score, channel on vs off, at
matched budget.
Preconditions: F1 delivered and merged; Config.DISCHARGE_POLICY selectable;
a green cycle soak on the launch config (python -u scripts/cycle_soak.py
--case <case>) before ANY ladder launch.
Design it as Q5's FOUR-arm ablation, not three (docs/RESEARCH_FINDINGS_
Q1Q10_2026-08-22.md Q5, "The three-arm ablation should become four"):
no-critique / vacuous-critique (form only) / real-critique-as-advice /
real-critique-in-context. Arm 2 is what separates a working critic from
argument-shaped text; without it the result is uninterpretable.
Instruments: reuse experiments/2026-08-26-run-anatomy-w2-criticism/census.py
and q5.py UNMODIFIED. Report R1_mechanical placebo-corrected only; W2's own
residue item 1 rules R2_prose-quote inadmissible as a rate.
End state: RESULTS.md with the four arms, each rate beside its placebo, and
an honest residue section. A negative or inconclusive result is recorded as
one.
```

---

## P3 — F1's own stated modularity boundary

**What.** A discharge KIND may declare requirements over the DECLARED FIELD SET
(`note`, `where`). A kind needing a field OUTSIDE that set is a wire change, not
a declaration (SPEC.md A8). That is the honest edge of F1's modularity claim,
recorded here so a future reader meets it as a stated limit rather than a
surprise. Not a defect. Widening it would mean a typed per-kind payload on
`DischargeWireV1`, which nothing has asked for and no evidence yet demands.
