# Checklist for: docs/ reorganization steps 3-4

Each step: one done-criterion, pasted output required before checking.

- [ ] **CS1** (S1, S2, S3 — one commit, per R2's "same commit as each
  move"): `git mv docs/PATROL_DETERMINISM_REPORT.md
  experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md`;
  fix the stranded reference in
  `docs/HANDOVER_MONITOR_2026-08-10.md:101`; update `docs/INDEX.md`'s
  Explanation section (new path for the moved report; explicit
  "stayed because ..." line for each of BASIN_REPORT.md,
  CAN_LLMS_EXPLORE.md, MINI_STRESS_REPORT.md, AUTONOMICS_REPORT.md).
  Done-criterion: `git status --porcelain` shows the move as `R`
  (rename); `grep -rn "docs/PATROL_DETERMINISM_REPORT"` across the
  whole tree returns zero hits outside this tranche's own
  REQUEST.md/SPEC.md and `DOCS_REORG_PROPOSAL.md`'s dated inventory
  (A2); `python tools/docs_verify.py` shows no NEW failures beyond the
  3 known shallow-clone baseline failures.

- [ ] **CS2** (S4, S5 — one commit): new file
  `docs/proposals/README.md` stating the new-file-forward
  `ADR-NNNN-<slug>.md` convention (new proposals only, no renames of
  existing files); update `docs/INDEX.md`'s Decisions section to name
  the convention and link to the new README. Done-criterion:
  `test -f docs/proposals/README.md`; `grep -c "ADR-NNNN"
  docs/proposals/README.md docs/INDEX.md` both non-zero; `git status
  --porcelain docs/proposals/` shows only the new README as `A`
  (added) — zero renames under `docs/proposals/`.

- [ ] **CS3** (C2 boundary gate): run `pytest tests/ -q -n 4` (full
  gate) and confirm the only failure is the known pre-existing
  `test_bronze_report` baseline (or fewer). Done-criterion: pasted
  pytest summary line matching "1 failed" (the known
  `test_bronze_report` baseline) or "0 failed", with the failing test
  name confirmed to be the known baseline if any failure exists.

- [ ] **CS4** (C3 errata checkpoint): review whether CS1-CS2's moves
  and edits surfaced any document claim already known to be wrong
  (candidate for `docs/ERRATA.md`) versus a plain path-currency fix
  (not an errata-worthy factual correction). Done-criterion: one line
  recorded in DELIVERY.md — "errata: none" or a new `docs/ERRATA.md`
  entry with its own done-criterion.
