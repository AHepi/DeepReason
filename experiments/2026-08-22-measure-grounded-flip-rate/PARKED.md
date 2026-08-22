# PARKED — noticed during the flip-rate measurement, deliberately not acted on

This tranche is read-only on `src/` and `tests/`. Nothing below was fixed.
Each entry is written for its future runner: one line of WHAT, then a
ready-to-send prompt.

---

## P1 — `docs/map/INV-frozen-surfaces.md` still states two retired laws

**What.** Its "The governing principle" section still reads *"fix READERS so
old roots stay valid; a change that invalidates existing replay-valid roots is
wrong by definition"* and calls the 42-root sweep "the instrument". CLAUDE.md
marks the first SUPERSEDED by the operator's 2026-08-14 law (old runs owe the
future nothing) and the second RETIRED by the 2026-08-22 ruling ("it just
wastes time"). A reader following the map's own ordering rule — read
`INV-frozen-surfaces.md` before designing — is handed two obligations the
operator has abolished. Noticed while doing exactly that. This tranche relies
on the retirement (11 roots are excluded for refusing to open) and the map
would have forbidden it.

```
Route: dr-audit-orchestrator (docs-drift dimension), then dr-change-orchestrator.

One goal: bring docs/map/INV-frozen-surfaces.md's "The governing principle"
section and its 42-root-sweep instrument into agreement with the two operator
laws that superseded them — the 2026-08-14 law ("old runs do not need to be
valid or returnable ... new versions are optimised for new functions") and the
2026-08-22 sweep retirement ("it just wastes time"), both ledgered in CLAUDE.md.
Preserve the SCOPE BOUNDARY CLAUDE.md states: within-version integrity (a
current run's record stays typed, append-only, replayable by the code that
wrote it) is untouched by either law and must remain stated as frozen.

Evidence pointers:
  - CLAUDE.md, "Operator design laws", the 2026-08-14 entry (states the
    superseded text verbatim) and "Build and test", the sweep retirement.
  - docs/map/INV-frozen-surfaces.md lines 15-28 and the "instruments" section.
  - docs/ERRATA.md — check whether this is already ledgered before writing.
  - This tranche excluded 11 roots under the 2026-08-14 law:
    experiments/2026-08-22-measure-grounded-flip-rate/inventory.json.

End state: the document's checks still pass (python tools/docs_verify.py), the
retired obligations no longer read as binding, Verified-at advanced only if the
checks were actually re-run, and an ERRATA entry if one is owed.
```

---

## P2 — 76 of 96 current-version roots have an empty attack relation

**What.** Corpus-scale adjudication blindness. `verification/report.py`'s
`_adjudication_blindness_findings` fires per root; nobody has run the census.
6 370 artifacts across 96 roots carry **60** attack edges in total, and every
attack relation is a depth-1 matching — no defence chain longer than one hop
exists anywhere in the corpus. This is not a defect on its face (a run whose
criticism genuinely found nothing to warrant is entitled to an empty `att`),
but it means every offline claim about this harness's argumentation behaviour
— including §9 of this tranche's RESULTS.md — rests on graphs that barely have
the structure being reasoned about.

```
Route: dr-audit-orchestrator (broken dimension), read-only.

One goal: produce the corpus-wide adjudication-blindness census — for each of
the 96 current-version roots, whether verify_root_report's
adjudication-blindness finding fires, how many warrants were minted, how many
criticism events ran, and the ratio between them. Report the distribution and
name the roots where criticism ran and warranted nothing. Do not fix anything.

Evidence pointers:
  - experiments/2026-08-22-measure-grounded-flip-rate/inventory.json — the
    96-root list with per-root att/dep/node counts already computed.
  - experiments/2026-08-22-measure-grounded-flip-rate/graphs.json — cached
    relations and provenance roles; no replay needed.
  - docs/map/SUB-adjudication.md, Traps, first entry ("No warrant, no attack
    edge, no REFUTED — and a run where that happened end to end looks
    perfect"), and its committed demonstration run-6472629d.
  - src/deepreason/verification/report.py::_adjudication_blindness_findings

End state: a census table committed as JSON plus a one-paragraph verdict on
whether the empty-att majority is expected behaviour or a live defect. If it
is a defect, hand it to deepreason-orchestrator as a fresh tranche.
```

---

## P3 — warrant-level perturbation is unmeasured

**What.** This tranche perturbs the `att` relation directly, at the point
`label0` consumes it, because that is the level Q10 measures Attack-F1 at.
It therefore does not exercise `build_att`'s closure rules — validity-node
lifting onto every carrier, `rubric:` case-law closure, `source_artifact`
unwinding, evidence lineage. A single warrant-level extraction error passes
through those rules and can become several attack edges before adjudication
sees it, so the true blast radius of an upstream error is bounded below, not
above, by the numbers in RESULTS.md.

```
Route: deepreason-orchestrator, measurement tranche, read-only on src/ and tests/.

One goal: measure the edge-multiplication factor of build_att's closure rules
on the committed corpus — for each existing warrant, how many att edges does
it produce, and how many would a single spurious warrant produce if attached to
each candidate target? Then re-run this tranche's Battery A at the warrant
level and compare blast-radius distributions against the att-level ones.

Evidence pointers:
  - experiments/2026-08-22-measure-grounded-flip-rate/ — GOAL.md's prereg
    records the att-level modelling assumption this tranche is lifting;
    RESULTS.md §2 and §8 state it as residue. perturb.py and battery_a.py are
    directly reusable; only the perturbation site changes.
  - docs/map/SUB-adjudication.md, "Where to change what" (the four closure
    branches) and Traps (the mention-on-a-rubric-nu trap, evidence lineage).
  - src/deepreason/adjudication/edges.py::build_att, the fixpoint body.

End state: RESULTS.md in a new tranche directory carrying both distributions
side by side, and a statement of whether the att-level measurement understates
the exposure and by how much. No src/ or tests/ change.
```
