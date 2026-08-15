# Parked — found during Rung 1, deliberately NOT worked

## P1 — `Config.RECRIT_STANDING` and `_standing_recrit_pool` still use "standing" in a third sense

**What.** Rung 1 freed the word "standing" at two of its three sites. The third
is the scheduler's: `_standing_recrit_pool` and `Config.RECRIT_STANDING` mean
*the pool of still-standing survivors to re-criticize*, not frame role.

**Why parked, not fixed.** `RECRIT_STANDING` is a `Config` FIELD NAME. It is
pinned by a check in `DR-SUB-scheduler`, it is readable from profile YAML, and
`_versioned_source_config_data` in `run_manifest.py` has to be told about config
keys explicitly (the `ENGAGED_CRITICISM_AUTHORITY` trap in
`INV-frozen-surfaces.md`). Renaming it is a compatibility decision, not
vocabulary work, and Rung 1's whole point was to be the cheapest possible rung.

**Where it goes.** Rung 4 of the v2 program, where the calculus's standing axis
actually arrives and the collision stops being cosmetic. Recorded in the Traps
section of `docs/map/CON-standing-and-background.md` so a reader meeting the word
in the scheduler meanwhile reads it correctly.

---

## P2 — `tools/root_sweep.py` cannot finish on this tree, and loses everything when it doesn't

**What.** Two independent defects, both hit during this rung's A4:

1. **Write-once at the end.** The tool accumulates every row in memory and calls
   `out.write_text(...)` after the loop. A run killed by a timeout produces an
   empty file, so 25 minutes of work yields nothing. Measured twice here.
2. **It cannot complete inside a reasonable timeout.** With the baseline's
   known-hang root (`experiments/live_tri_2026-07-27/
   run-c5ab654afd1b4aa131aede83bdca0f03`) and the generally degraded per-root
   throughput already parked in
   `experiments/2026-08-13-change-smoke-currency-audit/PARKED.md` P1, the full
   107-root sweep took **two passes of ~50 minutes each**. `AUDIT_BASELINES.md`
   already tells the reader to "run the sweep under `timeout` and exclude this
   root" — but the tool has **no exclude flag** (the CLI gap parked as
   `experiments/2026-08-13-audit/PARKED.md` P3), so following the documented
   advice requires editing a copy of the script.

**How A4 was actually obtained** (recorded so the next rung does not rediscover
it): a scratchpad copy of the same script with exactly two changes — skip the
known-hang root with a `SKIPPED` row, and write the output file after every root
so a timeout costs progress instead of everything — run in two passes, the second
skipping roots already present in the first.

### Ready-to-send prompt

```
Fix tranche: tools/root_sweep.py loses all progress on timeout and cannot
complete on the current tree. Route through deepreason-orchestrator.

EVIDENCE (measured 2026-08-14, experiments/2026-08-14-change-rung1-
vocabulary-groundwork/VALIDATION.md A4 and PARKED.md P2): the tool writes
its output once, after the loop, so two separate runs killed at 25 and 50
minutes produced empty files. The full 107-root sweep required two ~50
minute passes from a patched copy. AUDIT_BASELINES.md instructs the reader
to exclude the known-hang root, but the tool takes only an output path --
no exclude flag (already parked as experiments/2026-08-13-audit/PARKED.md
P3, the CLI gap).

SCOPE, three parts:
(1) write incrementally -- one row per root, flushed, so a killed run
    leaves usable partial evidence;
(2) add the exclude/skip surface AUDIT_BASELINES.md already assumes exists,
    and a --resume that skips roots already present in the output file;
(3) decide whether the per-root slowdown is worth its own diagnosis or
    whether (1)+(2) make it tolerable -- the throughput defect is parked
    separately at experiments/2026-08-13-change-smoke-currency-audit/
    PARKED.md P1 and should NOT be silently absorbed here.

GUARDRAIL: this tool is the instrument that protects every committed root.
Its OUTPUT FORMAT is compared across tranches (committed sweep files exist
in at least six tranche directories) -- adding a column or reordering
fields breaks those comparisons. Change how it writes, not what it writes.

TESTS: a sweep killed mid-run leaves a valid partial file; --resume over
that file produces the same total set as an uninterrupted run; the output
of an unpatched full run is byte-identical to today's for the same roots.
GATE: full gate at the boundary, docs_verify full. Map moves in the same
commit. Commit and push at every phase boundary.
```

---

## P3 — the CLAUDE.md design law and its INV document are split across two rungs

**What.** The operator's signal-contract design law is ledgered in CLAUDE.md by
this rung; its `INV-` map document and two `REC-` recipes belong to Rung 1b,
because `docs_verify --audit` refuses checks that cannot fail and an INV document
about an unbuilt mechanism would ship vacuous ones.

**Not a defect** — a deliberate split argued in `RECONCILIATION.md` §2L. Recorded
here only so that a reader who finds the law without the document knows the
document is scheduled rather than missing.
