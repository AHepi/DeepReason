# Parked — found during this tranche, not fixed here

## P1 — `docs/map/INV-frozen-surfaces.md`'s own `Owns:` header names four paths for five surfaces

**What.** While auditing every registry row against its document (DIAGNOSIS.md's
census), a SECOND hand-maintained list of the same surfaces turned up, in the
document's own header:

    Owns: src/deepreason/capabilities/state.py, src/deepreason/harness.py,
          src/deepreason/invariants.py, src/deepreason/run_manifest.py

Four paths. The document below it declares five surfaces spanning seven paths.
Missing: `src/deepreason/qualification.py` (surface 5, which has its own
section, its own `check:` and a granted contact recorded on 2026-08-28) and
`src/deepreason/verification/` (surface 3's other half, the one this tranche
just put into the blast-radius registry).

**Why it matters, and why it is NOT the same finding.** The `Owns:` line feeds
a different consumer — `docs_verify`'s ownership map and the map's own routing,
not the disclosure gate — so no verdict is wrong today because of it. But it is
the same failure SHAPE this tranche just fixed: a hand-maintained list of the
frozen surfaces, spelled narrower than the document it heads, with nothing that
goes red when the two disagree. This tranche did not touch it, because widening
a second list with a different consumer is a second goal.

**The general question worth settling with it, not before it:** whether the
three lists that name the frozen surfaces (this `Owns:` header, the document's
own section headings, and `tools/blast_radius.py`'s registry) should be
derivable from one source, or should stay three and gain a check that fails
when they disagree. This tranche's fix makes the third one right; it does not
make the three agree by construction.

**Ready-to-send prompt.**

```
Route through deepreason-orchestrator (dr-set-goal first). One goal: the three
lists that name DeepReason's frozen surfaces agree, and a check goes red when
they do not.

Evidence, all read-only:
- docs/map/INV-frozen-surfaces.md, the `Owns:` header line -- four paths.
- The same document's five `### N.` section headings -- five surfaces, seven
  paths, one of them a directory (`verification/`).
- tools/blast_radius.py, FROZEN_SURFACES -- fixed 2026-09-10 to carry all
  seven; the G6 subsection of the map document now checks its ANSWER, not its
  list.
- experiments/2026-09-10-defect-blast-radius-surface-3-registry/ -- the tranche
  that fixed the third list, its DIAGNOSIS.md census of all six registry rows,
  and docs/ERRATA.md E88/E89.

Settle the shape before coding: one source with the other two derived, or three
sources with a check that fails on disagreement. Price both. The `Owns:` line
feeds docs_verify's ownership map and the registry feeds the disclosure gate,
so a single source has to serve two consumers with different needs -- that is
the part to design, not the string editing.

tools/ and docs/map/ are not frozen surfaces, so this needs no grant.
```

## Not parked here, because this tranche settled them

- **The frozen-ADJACENT `route_fingerprint` row.** The goal asked whether the
  registry carries it narrower than its document. It does not — it carries it
  WIDER (the whole file, where the document freezes one function's output
  format), which for a disclosure gate is the safe direction. Left unchanged
  with the reason recorded in `FIX.md` and in a comment above the entry, so a
  later reader does not read the mismatch as an oversight.
- **Every other registry row.** DIAGNOSIS.md's census compared all six against
  their sections; surfaces 1, 2, 4 and 5 match their documents exactly. Nothing
  was widened beyond the one path the finding names.

## P2 — `docs_verify` reports 10 failed where `docs/AUDIT_BASELINES.md` predicts 5 or 6; four rows are a delta this tranche did not cause

**What.** The boundary run of `python tools/docs_verify.py` on this tranche's
tree reported **10 failed** (`proof/DOCS_VERIFY.txt`). The living baseline says
5 or 6 on a shallow clone. Six rows match the baseline exactly and are disposed
as `baseline`; FOUR are a delta, and each was probed individually rather than
waved through:

  - `CON-successor-questions.md:305` and `SEAM-scratch-x-workflow.md:51` — both
    fail on the SAME clause, a census asserting 50 modules under
    `src/deepreason/scratch` that also mention `workflow`. The tree has **51**.
    A count rotted when some other tranche added a module; two documents carry
    the same pinned number and both went stale together.
  - `INV-frozen-surfaces.md:1569` — the writers-room `record_claims` pin reads
    `experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/
    runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092`, which **does not exist in this
    checkout**. The check dies on empty JSON, which reads like a claim failure
    and is a missing-evidence failure.
  - `CON-run-identity.md:313` — TIMEOUT at `docs_verify`'s own 300 s per-check
    ceiling. Run alone on a quiet box the same command **passes in 356 s**
    (9 passed), so the claim holds and the CHECK is too expensive — the same
    class as the `SUB-application.md` row retired on 2026-08-31 for costing
    54-71% of that ceiling before contending for CPU.

**Not this tranche's, and shown rather than asserted:** `git diff <base>
--name-only` lists no file under `src/`. The two count checks census `.py`
files under `src/deepreason` only; the record-claims check reads a run root;
the timeout is instrument cost. Nothing here reads
`tools/blast_radius.py`, `docs/ERRATA.md`, or the parts of
`docs/map/INV-frozen-surfaces.md` this tranche edited.

**Ready-to-send prompt.**

```
Route through dr-audit-orchestrator (docs-drift dimension) or, if you prefer a
single fix tranche, deepreason-orchestrator (dr-set-goal first). One goal:
`python tools/docs_verify.py` returns to its recorded baseline, or
docs/AUDIT_BASELINES.md is re-baselined with each new row disposed by class.

Evidence, all read-only:
- experiments/2026-09-10-defect-blast-radius-surface-3-registry/proof/DOCS_VERIFY.txt
  -- the 10-failure run, with each check's own command and error.
- experiments/2026-09-10-defect-blast-radius-surface-3-registry/PARKED.md P2 --
  the four-row delta, each probed individually, with the probes' output.
- docs/AUDIT_BASELINES.md, the docs_verify entry -- the 5-or-6 baseline, its
  expected-failure table, and the CONTAINER-CONDITIONAL rows.

Three different repairs are needed and they should not be conflated: a rotted
COUNT pinned in two documents at once (50 vs the tree's 51), a check whose
evidence is a run root missing from the checkout, and a check that exceeds
docs_verify's own 300 s ceiling while its claim is true. The third has a
precedent to copy: docs/ERRATA.md E67 and the 2026-08-31 narrowing of the
SUB-application.md row.

docs/map/ is not a frozen surface, so this needs no grant.
```
