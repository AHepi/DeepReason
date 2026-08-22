# Parked — scalarization census, 2026-08-22

This tranche is READ-ONLY on `src/` and `tests/` by operator instruction. Every
finding below is a ready-to-send prompt for a LATER tranche. Nothing here was
fixed, and nothing here should be fixed inside this tranche.

One prompt per SELECTION-BY-SCORE finding (P1) and per finding-grade scalar note
(P2), plus the map gap the preflight turned up (P3).

---

## P1 — SELECTION-BY-SCORE: the evidence pack ranks survivors by `hv` and truncates

**WHAT:** `bridge/evidence_pack.py:757` sorts the ACCEPTED partition by
`-hv` and `:766` truncates it to `MAX_EVIDENCE_PACK_ITEMS`, so when survivors
exceed the cap a scalar — not partition membership plus a typed tie-break —
decides which survivors reach the delivered grounded-application evidence pack.
An unmeasured survivor sorts below an `hv = 0.0` one (`-1.0` default), and `hv`
is a lazy one-per-cycle spot-check that only runs when the run has a `variator`
role, so pack membership can turn on an attention fact.

```
Route: dr-change-orchestrator (this is a design change, not a defect —
nothing violates a documented guarantee; the shape is what is in question).

ONE GOAL: decide, and implement, what the grounded-application evidence pack
does when the ACCEPTED survivor set exceeds MAX_EVIDENCE_PACK_ITEMS — so that
which survivors reach a delivered answer is decided by partition membership
plus a TYPED tie-break, never by a scalar, and so that any truncation is
RECORDED rather than silent.

Read first, in this order:
  - experiments/2026-08-22-audit-scalarization/CENSUS.md section 4 (the
    finding, with the reason it is medium and not severe)
  - docs/RESEARCH_SHAPE_CRITIQUE_2026-08-22.md section 2(A) — the -10pp /
    +16.7 result that motivates the whole question
  - docs/map/SUB-adjudication.md (the partition is the product)
  - docs/map/SUB-bridge.md and SEAM-bridge-x-manifest.md BEFORE either side
  - src/deepreason/easy.py::pick_survivor — the repo's own model of a lawful
    best-candidate selection: partition membership, then (event_seq, aid)
  - src/deepreason/scheduler/scheduler.py::_select_problem — the operator-seed
    tie-break law, the same shape applied to problems

Evidence pointers:
  src/deepreason/bridge/evidence_pack.py:744-766 (survivors) and :849
    (refutations, same shape)
  src/deepreason/measures/hv.py — contains NO reference to Status, so hv is
    adjudication-independent; this is why the finding is medium, and the fix
    must not accidentally make it adjudication-dependent
  src/deepreason/scheduler/scheduler.py::_lazy_hv — one measurement per cycle,
    variator-gated: the reason many survivors carry no hv at all

Candidate roads to price for the operator (do not pick one before SPEC.md):
  (a) replace the sort key with a purely typed one — e.g. (event_seq, ref),
      matching pick_survivor's "longest-standing survivor" rationale
  (b) keep hv as an ordering but emit a typed truncation record naming what
      was dropped and by which key, so the pack never silently omits survivors
  (c) both

End state: SPEC.md with per-requirement acceptance checks; the change; a
regression test that FAILS on the current sort-and-truncate and passes after;
full gate 0 failed; map moved in the same commit.

Do NOT widen this into a general measures review, and do NOT touch
adjudication/ — the partition itself is correct and is not the subject.
```

---

## P2 — Compensatory scalar over an adjudication result: the appellate docket

**WHAT:** `informal/appellate.py:22-57` builds one summed `score` in which an
adjudication-derived term (`+2` when a discrimination problem has ≥2 ACCEPTED
rivals) is added to non-adjudication terms (ensemble-split `+3`, audit-hit `+2`,
guard-block `+1`), sorts by `-score`, and truncates to `USER_RULINGS_BUDGET`.
This is the only compensatory weighted sum in the codebase with an adjudication
result as an addend. It is lawful today because it allocates ATTENTION only and
its sole caller is the operator-facing `deepreason` CLI (`cli/main.py:1238`) —
all three of which a later change could remove without anyone noticing.

```
Route: dr-change-orchestrator.

ONE GOAL: decide whether the appellate docket's ranking should stay a
compensatory weighted sum with an adjudication-derived addend, or become a
lexicographic/stratified rank in which the adjudication term can order WITHIN a
stratum but never trade against non-adjudication evidence — and record the
decision either way, so a future reader knows it was chosen rather than
inherited.

Read first:
  - experiments/2026-08-22-audit-scalarization/CENSUS.md section 5b (the full
    list of nine label-to-scalar conversions; this is the only compensatory one)
  - docs/RESEARCH_SHAPE_CRITIQUE_2026-08-22.md section 2(A), in particular
    "any scheme that eventually recombines the channels into one scalar
    reinherits the conflation it was built to remove"
  - src/deepreason/informal/appellate.py (whole file — it is 100 lines)
  - src/deepreason/informal/standards.py:88-99 — precedent_slice, and its
    "pack ordering is the only authority a user ruling has (N1: never status
    privilege)", which is the constraint any redesign must preserve

Evidence pointers:
  src/deepreason/informal/appellate.py:24-27 (bump), :41-46 (the adjudication
    addend), :48 (the sort), :57 (the cap)
  src/deepreason/cli/main.py:1238 (the sole caller — confirm it is still sole)
  src/deepreason/config.py:294 (USER_RULINGS_BUDGET default 2 — the cap is
    small, which is what makes the ranking decisive)

The operator's judge-suspicion law applies here (CLAUDE.md: judges "prosecute
without any discernable discrimination"): the docket spends the operator's own
attention, which is scarcer than any judge seat, so the bar for what may
reorder it is higher, not lower.

End state: SPEC.md, the change or a recorded decision NOT to change with its
reason, regression test, full gate 0 failed, map moved in the same commit.

Do NOT touch the docket's non-adjudication signals — they are out of scope.
```

---

## P3 — Map gap: three SUB- documents are absent from INDEX.md's routing table

**WHAT:** `docs/map/` holds 18 `SUB-*.md` files; `docs/map/INDEX.md`'s
Subsystems table has 15 rows. `SUB-application.md`, `SUB-amendment.md` and
`SUB-periphery.md` exist but cannot be reached by routing — this census reached
`SUB-application.md` by filename, which is exactly what `INDEX.md` says the map
exists to prevent. Verified: `ls docs/map/SUB-*.md | wc -l` = 18;
`grep -c '^| `SUB-' docs/map/INDEX.md` = 15.

```
Route: dr-change-orchestrator (a map change, small).

ONE GOAL: add the three missing rows to docs/map/INDEX.md's Subsystems table
(SUB-application.md, SUB-amendment.md, SUB-periphery.md), each with an
accurate one-line "Covers" cell derived from the document's own Owns: header,
and add a check that would FAIL if a SUB- document is added without a routing
row.

Read first: docs/map/SCHEMA.md (the contract for writing map documents),
docs/map/INDEX.md.

Evidence: ls docs/map/SUB-*.md | wc -l  -> 18
          grep -c '^| `SUB-' docs/map/INDEX.md -> 15

The check is the point — a routing table that can silently fall behind is the
same failure the map's re-derivation discipline exists to prevent. Something
like:
  check: python -c "import pathlib,re; d=pathlib.Path('docs/map'); files={p.name for p in d.glob('SUB-*.md')}; rows=set(re.findall(r'`(SUB-[a-z-]+\\.md)`', (d/'INDEX.md').read_text())); assert files==rows, sorted(files^rows)"
(run it before writing it down — SCHEMA.md's rule.)

End state: INDEX.md updated with the new check passing, python
tools/docs_verify.py 0 failed, one commit.
```
