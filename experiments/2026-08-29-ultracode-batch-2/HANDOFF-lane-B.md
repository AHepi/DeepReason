# HANDOFF — lane B (successor questions, P9 law)

Recorded 2026-08-30 at the operator's instruction, mid-batch: lane B is
REMOVED from this session's stack and handed to a fresh window. This file
exists so that window needs nothing from this conversation.

## State at handoff — measured, not asserted

    branch   claude/b2-lane-B
    tip      fdfe8a6e4          (PUSHED to origin; local == remote)
    tree     clean (git status --porcelain empty)
    base     origin/main 84514a028, via batch commit 152c7e204
    cone     45 paths; NO frozen surface contact
    tranche  experiments/2026-08-30-change-successor-questions/

The lane found a LAWFUL ROAD that avoids `run_manifest.py` entirely, so the
frozen-surface-4 grant it forecast in SPEC.md was requested but NOT NEEDED for
what shipped. The branch diff touches none of the seven frozen paths.

## What is DONE

Full dr-change-orchestrator artifact set is committed: REQUEST.md (the
operator's verbatim words, split into numbered requirements), SPEC.md,
CHECKLIST.md, VALIDATION.md (every acceptance check with its real output),
DELIVERY.md, PARKED.md, `blast_radius.json`, and seven mutation transcripts
under `proof/`.

Built and tested: the OPTIONAL `successor_question` field on the criticism
contracts and wire models; the architecture test pinning the never-penalized
half; the versioned, registered destination registry under
`src/deepreason/successor/`; the scratchpad route; the gated minting road; the
signal declarations; the seed rank-tie proof; and the map moved in the same
commits (a NEW `docs/map/CON-successor-questions.md` plus five amended
documents).

## What is NOT done — read this before trusting anything above

1. **NO ADVERSARIAL SKEPTIC PASS RAN.** Every other lane in this batch was
   re-verified by three independent skeptics who RE-RAN its claims, and every
   one of them found real defects — including tests that were VACUOUS and
   claims whose own cited transcripts did not contain the measurement. Lane B's
   claims are the lane's own and have NOT been independently re-run. Treat
   the whole tranche as unverified until that pass is done. This is the single
   most important thing on this page.
2. **ONE TEST IS RED, by design and prediction.**
   `tests/test_decommissioned_pipeline_stays_out.py::test_no_source_file_produces_a_successor_problem`
   fails with `AssertionError: ['src/deepreason/successor/mint.py:88']`.
   Baseline before the tranche was `10 passed`; after, `1 failed, 9 passed`.
   It was PREDICTED in SPEC.md as P-FIX-1 before any code existed, and its
   four-line rewrite is committed ready-to-apply as PARKED.md P9B-7 — but it is
   GATED on operator question Q5. **The branch cannot be integrated while it is
   red** (0 failed is the only acceptable gate result).
3. **Nothing in production calls `route` or `mint`.** The channel is built,
   tested and mutation-proved, but its dispatch site is question Q3's decision
   and the granted cone gives `rules/crit.py` OUTPUT SCHEMA ONLY. A live run
   today records the field and routes nothing. The lane's own words: this is
   "the single largest gap between delivered and working, and it is one call
   site wide."
4. **Diff budget EXCEEDED** — 2486 insertions against SPEC.md's 1169 ceiling.
   The lane argues it is density (mutation transcripts and the new map
   document), not scope creep, and that no path outside the declared cone was
   touched. Recorded rather than trimmed; a reviewer may disagree.
5. **`minting_notices` is reachable but not in `__all__`** — a tension between
   two SPEC accepts, flagged rather than resolved by editing either.
6. **The full gate was never run in this lane**, deliberately: this batch runs
   ONE gate at fan-in on an idle box.

## The five open operator questions

PARKED.md P9B-1..P9B-5 carry the shortest answerable form of each, with both
roads priced and a recommendation. In brief: Q1 the frozen-surface-4 grant
(only needed if the Config-field road is taken); Q2 where the enablement
warning is printed; Q3 whether the criticism dispatch may write to the
workshop — the one that stands between a proven channel and a firing one;
Q4 how strong "never outrank the seed" must be; Q5 the scope of the superseded
2026-08-15 ruling, which gates the red test.

P9B-6 (strict domination) is a future tranche, live only if Q4 answers STRICT.

## Batch context the next window should know

- Lanes D and E are DELIVERED and integrated into
  `claude/deepreason-ultracode-batch-2-l9vj55`. Lane C is PARKED on
  `claude/b2-lane-C` (built but deliberately not integrated — it carries an
  operator fork). Lane A is in adversarial verification.
- `docs/AUDIT_BASELINES.md` moved in lane D's own commit: the expected
  docs_verify failure list was reduced. Judge docs_verify against the CURRENT
  baseline, not a remembered one.
- A STOP is a phase boundary: push the moment anything is parked. Batch 1 lost
  two finished lanes to a reclaimed container
  (`experiments/2026-08-29-ultracode-batch-1/LOSS.md`).
