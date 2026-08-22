# Goal: does the reach measure ever fire on committed current-version roots, and if not, which exit rejects every candidate pair?

Class: capability-gap
  (measurement tranche. If the census convicts a reader or threshold the
  class becomes `defect` — but this tranche is READ-ONLY on src/ and
  tests/ by operator instruction, so that outcome is delivered as a
  parked, ready-to-send deepreason-orchestrator prompt, never as a fix.)

Observed: across all 107 committed run roots under `experiments/`, a
first-pass scan of the typed logs finds reach recorded in exactly two —
`experiments/gemma4_dna_unattended_2026-07-12` (4 Measure events carrying
`reach_set`, 3 carrying `addr+`) and
`experiments/gemma4_dna_unattended_3_2026-07-12` (2 and 2) — both dated
2026-07-12, i.e. before the Bronze Age postmortem discipline
(`_STRUCTURAL_PROGRAMS`, `coverage_min`) existed. Zero
`reach-provisional` Measure events exist anywhere in the corpus. On
`8e22d0431fd2b98d` (2894 problems) EXPLANATION_DEBT spawned 0 times
(`experiments/2026-08-13-change-lifecycle-operation-parity/PARKED.md`
P5), and its criterion families are relation-form x2875, hv-floor x61,
lineage-ref x61.

Map ids resolved (per CLAUDE.md map preflight):
  - DR-SUB-evaluation — owns `measures/`, the home of `reach.py`
  - DR-CON-warrants-and-attacks — owns the substantive/structural
    boundary (`_substantive`, `_STRUCTURAL_PROGRAMS`) that decides which
    criteria can carry reach
  - DR-CON-problem-layer-lifecycle — owns the premise/attribution
    programs added to `_STRUCTURAL_PROGRAMS`
  - DR-SUB-scheduler — owns the two `reach_sweep` call sites
    (`scheduler/scheduler.py:2024`, `:2274`)
  - DR-INV-frozen-surfaces — read before designing; this tranche
    designs nothing and touches nothing under `src/`.

Success criterion (machine-decidable):

    python experiments/2026-08-21-measure-reach-firing/census.py

    Prints, for every committed run root under `experiments/`:
      (a) whether the root OPENS under the current reader
          (`Harness(root, read_only=True)`); a root that does not open is
          recorded OUT OF SCOPE per the operator law of 2026-08-14 ("old
          runs owe the future nothing"), not diagnosed;
      (b) for every openable root, the recorded reach census straight
          from the log (Measure events carrying `reach_set` / `addr+`,
          and `reach-provisional` inputs);
      (c) for every openable root, a re-derived census over the replayed
          final state in which EVERY (accepted artifact, foreign problem)
          pair is attributed to exactly one outcome — full hit,
          provisional hit, or one named rejection exit — and the exits
          sum to the pair count;
      (d) totals across roots.

    And:

    git diff --stat origin/main

    shows changed files ONLY under
    `experiments/2026-08-21-measure-reach-firing/`.

In scope:
  - `experiments/2026-08-21-measure-reach-firing/` (the only writable path)
  - read-only reads of committed roots under `experiments/`
  - read-only reads of `src/deepreason/measures/reach.py` and its two
    scheduler call sites, AFTER the record pass

NOT in scope: `src/deepreason/measures/reach.py` itself — no threshold is
tuned, no program is removed from `_STRUCTURAL_PROGRAMS`, no
`coverage_min` is lowered. Manufacturing a hit by loosening the
discipline is the Bronze Age defect in a new coat. Also NOT in scope:
Rung 1b-ii's files (controller, signals, `invariants.py`) — a concurrent
window owns them.

Budget: 0 changed lines under `src/` or `tests/`; artifacts + one census
script under the tranche directory; commits at every phase boundary.
Stop conditions inherited from orchestrator: yes
