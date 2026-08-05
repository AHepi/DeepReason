# Verification

## Verdict: **PASS on the tranche's named question; FAIL on the goal's
## full criterion, blocked by V1**

GOAL.md asked exactly one question — "what changed in the contract-pair
inventory since the 840/280 pins were written, and is that change
correct behaviour from the rung program or a regression?" — and stated
that everything else follows from the answer. That question is answered,
proven, and shipped. The end state it also demanded (`exit 0` from the
operational smoke) is not reached, because clearing the qualify stage
exposed a distinct defect two stages later.

Reporting this as a partial is the point. A tranche that claimed PASS
here would be claiming the operational surface is verified when it still
has not run end to end in this container.

## Criterion commands + output, run at `31480e5f`

    $ python tools/docs_verify.py
    docs_verify [full]: 51 documents, 815 checks, 4 workers
    docs_verify: 0 failed
    -> PASS

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact
    entry points, module parity, MCP registration, and exact MCP schemas
    rc=0
    -> PASS

    $ python -m pytest tests/ -q -n 4
    3338 passed, 7 skipped in 759.48s (0:12:39)
    -> PASS (0 failed)
    At the parent commit 228b2ce6 this was 3 failed, 3335 passed -- the
    three the revert addresses. Nothing else moved: 3335 + 3 = 3338.

    $ python -u scripts/wheel_operational_smoke.py
    {"schema":"deepreason-wheel-operational-failure-v4",
     "stage":"continuation_rejection","failure_kind":"assertion_failed",
     "timeout":false,"mcp_liveness":"alive","cleanup_completed":true, ...}
    rc=1
    -> FAIL, blocked by V1 (PARKED.md). Not caused by this change.

Both were re-measured at this commit rather than carried from the
parent, because the revert changed the failure-reporting path and
carrying either forward would be reporting output this commit did not
produce.

Two things the re-measurement establishes beyond the verdict:

1. **The qualify fix holds.** The run reaches
   `continuation_rejection` -- four stages past `qualify` -- with
   `mcp_liveness: alive`. Sites 1-3 pass against the live 15-pair
   inventory without naming a numeral, and site 4's tool order is
   accepted by the running server.
2. **V4 is now concrete rather than argued.** The record above is the
   ENTIRE output of the failing run. It names a stage and a kind and
   locates no line, and with site 5 reverted there is no diagnostic
   block beside it. That is exactly the gap V4 describes, observed.

Run one instrument at a time, per U3: the two quick instruments together
and the gate alone, because three earlier gate measurements in this
session were corrupted by self-inflicted parallel load.

## What the tranche proves

**The inventory diagnosis.** Both numerals derive from one source, and
that source moved twice on 2026-07-27 in commits that postdate the pins:
`9fabac69` grew the inventory 14 -> 15 pairs, and `f49dc48a` added a
bounded re-exercise allowance to
`production_qualification_maximum_provider_calls`. The arithmetic closes
exactly — `840 + 40 + 260 = 1140`, and `15 x 20 = 300` is what the
fixture recorded, with `errors = []` and `tier: full, state: ready`.
**Not a regression.** No `src/` change was owed and none was made;
frozen surface 5 (qualification subject digests) is untouched.

**The fix.** The qualify stage now names no numeral at all. It asserts
the property the numerals stood in for: qualification announces a
positive maximum, spends no more than it announced, makes exactly one
clean pass (`total_calls == qualified_pairs * cases_per_pair`, both read
at run time — the pair count from the bundle the run just wrote, the
per-pair case count from the INSTALLED wheel's own constant), still
carries the qualification-case marker, and records zero provider errors.

**Same-commit pin rule.** No numeric pin survives in this stage, so
nothing is left needing to name what it derives from. The one pin that
does survive elsewhere in the file — `EXPECTED_MCP_TOOLS` — is the
declared public facade, deliberately updated when the surface changes,
not a fact with an expiry date. GOAL.md's fifth criterion is met.

**A correction shipped with it.** The previous tranche read two bridge
contracts as taking "2 calls per case" and flagged a possible
regression. Wrong: the fixture counts by WIRE TITLE and two pairs share
one title. With `errors = 0` and `300 = 15 x 20`, no pair repairs at
all.

## What the tranche got wrong, and what that cost

Two amendments were defects I introduced, both recorded in FIX.md rather
than typed in silently:

| amendment | what | outcome |
|---|---|---|
| 2 | site 5 — traceback reporting for typed failures | **REVERTED** |
| 1 | site 4 — `EXPECTED_MCP_TOOLS` order, my own pin error from the preceding tranche | stands, verified |

Site 5 is the one worth stating plainly. It shipped as `228b2ce6` and
the gate came back **3 failed, 3335 passed**, all three in
`tests/test_wheel_operational.py`, all three
`json.decoder.JSONDecodeError`. On a failing run stderr must be EXACTLY
the annotation record and stdout must be empty; both public streams are
reserved, so there is no room beside the record for a human channel.
FIX.md's "Existing tests at risk" had predicted those 108 tests would
pass unedited. Per `dr-implement-fix` rule 5 the fix was wrong as
implemented, and weakening `_annotation_record` was not available — it
is the assertion that proves the record is payload-free on the wire.
Reverted at `31480e5f`; that file is back to 108 passed.

The need it addressed is real and survives the revert: a payload-free
record names a stage and a kind and cannot name a line. Parked as **V4**
with a proposed destination (a file under `temp_root`, retained on
failure by T2's `--keep` fix) rather than redesigned unilaterally,
because it revises T2's delivered design.

## Record-behaviour preservation

No run root, reader or validator is touched. The tranche's whole diff
lives under `scripts/`, which `src/` never imports, plus experiment
prose. `docs_verify: 0 failed` and `docs/map/` unchanged.

## Residue (honest)

- **V1 blocks the end state.** `continue_run` over MCP returns a
  non-error for a completed non-resumable run, where the smoke expects
  `CONTINUE_TYPED_STOP_REQUIRED`. Two readings — product regression vs.
  surface-shape change — need one measurement to separate, and they need
  different fixes. Neither is established here.
- **V1's evidence is now harder to re-derive.** The traceback that
  located it was captured while `228b2ce6` was in the tree. The
  measurement is real; the mechanism that produced it is gone.
- **Stages beyond `continuation_rejection` remain unexercised.** The
  operational smoke has never run end to end in this container. Reaching
  `exit 0` may take more than one more fix, and each should be diagnosed
  on its own evidence rather than assumed to share a cause.
- **V4** — the diagnostic channel with no legal destination.
- **V2** — two instruments pinning one surface with different comparison
  semantics; the weaker gives false assurance. S2 would dissolve it.
- **Carried, untouched**: U1 (parked by the operator), U3, T3, T4, S2,
  S3, P1a, P1b, P1e, P7.
