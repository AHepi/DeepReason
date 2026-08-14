# Parked — found during this tranche, deliberately NOT worked

This was a design-and-stop tranche with no code (REQUEST.md R2), so everything
below is an observation, not a deferred fix. Items already parked elsewhere are
named and left where they are rather than duplicated.

---

## P1 — `EXPLANATION_DEBT` has never fired on any measured root

**What.** The reach ⇒ explanation-debt spawn trigger exists in both authorities
(calculus §5, spec v1.3 §3) and in the tree (`SpawnTrigger.EXPLANATION_DEBT`,
`rules/spawn.py`), and on the one root with a full trigger census — grounded
extension `8e22d0431fd2b98d`, 2 894 problems — it fired **zero** times
(census recorded in
`experiments/2026-08-13-change-lifecycle-operation-parity/PARKED.md` P5).

Why it matters to the v2 program specifically: reach is the promotion signal
(`RECONCILIATION.md` M-4, S-8). Rung 5 nominates frame assertions from reach
events spanning ≥ `K_frame` problem lineages. If reach events are so rare that
the *existing* reach-driven trigger never fires, nomination will never fire
either, and Rung 5 would ship a mechanism that cannot be reached in practice.

Parked rather than worked because it is a measurement question with its own
evidence, and this tranche was forbidden to run code. It is NOT necessarily a
defect: `measures/reach.py` is deliberately stricter than either document (the
Bronze Age postmortem discipline — no reach from an empty, trivial or unguarded
battery, plus a coverage floor below which hits are logged as provisional), so
zero hits may be correct behaviour on a root whose problems are 2 814
integration problems carrying one criterion each.

### Ready-to-send prompt

```
Measurement tranche: does reach ever fire, and if not, why? Route through
deepreason-orchestrator; diagnosis from the typed record BEFORE code.

WHY NOW: the v2 calculus program (experiments/2026-08-14-change-calculus-
reconciliation-v2/LADDER.md Rung 5) nominates background frame assertions
from reach events spanning >= K_frame problem lineages. If reach never
fires, nomination never fires and Rung 5 ships an unreachable mechanism.

EVIDENCE (already measured -- verify, do not re-derive): on root
8e22d0431fd2b98d, 2894 problems, EXPLANATION_DEBT spawned 0 times.
Trigger census in experiments/2026-08-13-change-lifecycle-operation-
parity/PARKED.md P5. Criterion families on that root: relation-form
x2875, hv-floor x61, lineage-ref x61.

START by counting reach outcomes across every committed root: full hits,
provisional hits (reach-provisional), and rejections, with the reason
each rejection carried. src/deepreason/measures/reach.py documents three
distinct rejection paths (non-qualifying criteria, no novel criterion,
coverage below coverage_min) -- attribute every rejection to one.

THE QUESTION TO ANSWER: is zero the CORRECT answer for these roots (the
problems really do carry only structural criteria, so no substantive
foreign battery exists to survive), or is a reader/threshold wrong?
Answer it with the census, not with a reading of the code.

DO NOT loosen the reach discipline to make hits appear. The Bronze Age
postmortem is why the strictness exists; weakening it to manufacture a
promotion signal would be the same defect in a new coat.

GATE: full gate at the boundary, root_sweep zero verdict drift,
docs_verify full. Commit and push at every phase boundary.
```

---

## P2 — `refl` is flagged unreferenced, and P6 (no authority) leans on it

**What.** `rules/refl.py::refl` appears in the 2026-08-13 dead-code census as
one of 15 symbols with zero references anywhere in the tree
(`experiments/2026-08-13-audit/PARKED.md` P2). `Refl` is the transition rule by
which the calculus's own rules, standards, render policies and guard procedures
are registered artifacts and therefore attackable — P6 (no authority), which
`RECONCILIATION.md` P-6 and D-14 both depend on.

**Not re-parked.** It is already parked, with a ready-to-send prompt, in the
audit tranche. Recorded here only so the connection is visible: whoever picks up
that symbol should know that the v2 program's new rule-objects
(`presupposition-wf`, promotion criteria, scope predicates, render policy) are
supposed to enter through this door, and Rung 1 owes an answer to how they do if
`refl` itself is inert.

---

## P3 — the map has no document for the problem-layer lifecycle

Recorded in REQUEST.md §3 as a map gap. Rung 2 mints it (LADDER.md). Not a park
so much as a scheduled piece of work; listed here so it is not lost if the rung
order changes.
