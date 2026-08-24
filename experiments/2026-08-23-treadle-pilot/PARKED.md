# PARKED — noticed during the treadle tranche, not fixed here

## P1 — `INV-frozen-surfaces.md` still presents the retired root sweep as the instrument

**What.** `docs/map/INV-frozen-surfaces.md` says "the 42-root sweep below is
the instrument" (line 27) and carries a `### The root sweep` section (line 217)
prescribing `python tools/root_sweep.py` before any reader, guard or authority
change. The sweep was RETIRED by operator ruling on 2026-08-22 ("it just
wastes time"), recorded in CLAUDE.md line 161 and `docs/AUDIT_BASELINES.md`
line 52. The map document contains **zero** mentions of the retirement
(`grep -c "RETIRED\|retired 2026-08-22\|wastes time"` → 0). So the document a
change author is told to read FIRST still instructs them to run a retired
instrument.

Found by the external consistency reviewer in this tranche's rung T5, cell A
(the TRUE packet) — a pre-existing drift, not caused by this tranche, and
verified against the sources before parking.

**Ready-to-send prompt:**

```
Route: dr-change-orchestrator (documentation defect; no code changes expected).

One goal: docs/map/INV-frozen-surfaces.md must stop instructing readers to run
the retired root sweep, without losing the historical record of what the sweep
proved.

Evidence:
- docs/map/INV-frozen-surfaces.md:27 "Measure the difference rather than
  assuming it — the 42-root sweep below is the instrument."
- docs/map/INV-frozen-surfaces.md:217 "### The root sweep" — a full section
  prescribing `python tools/root_sweep.py <output.txt>` "Before and after any
  change to a reader, a guard, or an authority rule".
- CLAUDE.md:161 "The root sweep is RETIRED as an instrument (operator ruling
  2026-08-22: 'it just wastes time')."
- docs/AUDIT_BASELINES.md:52 "root_sweep — RETIRED as an instrument ... no
  audit, gate, or grant runs it anymore; reader changes are proven by targeted
  regression tests instead. The historical baseline below is kept only so old
  tranche artifacts that cite it remain interpretable."
- grep -c "RETIRED\|retired 2026-08-22\|wastes time" docs/map/INV-frozen-surfaces.md
  -> 0

Note the precedent for HOW to retire without deleting: AUDIT_BASELINES.md keeps
the old row struck through with a stated reason. Two granted-contact sections in
INV-frozen-surfaces itself cite sweep evidence (the 107-root sweep at Rung 1b-ii);
those citations must remain interpretable, so this is a rewrite that marks the
instrument retired and keeps the historical proofs readable — not a deletion.

End state: the document's `Verified-at:` advanced only if its checks were
actually re-run; `python tools/docs_verify.py` still at its 3 baseline
failures; an ERRATA entry if any claim it made is now known wrong.
```
