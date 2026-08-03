# Parked — noticed or deferred during this tranche, deliberately not done

- **Rungs 2-7 of the modularisation ladder** (`docs/HANDOVER_2026-08-03.md`).
  This tranche is rung 1 only, per C1/A2. Rung 2 (buried choices become
  visible switches) is the natural next tranche when the operator wants to
  proceed.
- **The `INDEX.md` Subsystems-table gap for `amendment`/`application`/
  `periphery`.** All three have real `SUB-*.md` documents (and got their
  `## Seams` section in this tranche) but are not listed in `INDEX.md`'s
  routing table. Out of scope per SPEC.md ("not requested"); a one-line
  addition if the operator wants it fixed.
- **Every `Seams-undocumented:` pair this tranche glossed as "not yet
  analyzed" rather than "real" or "deliberately absent"** — roughly 30
  pairs across the 16 `SUB-*.md` files (e.g. `bridge x scratch`,
  `capabilities x llm`, `manifest x verification`, `ontology x scratch`,
  `application x verification`). R2 asked only that these be named and
  honestly glossed, not resolved; a dedicated tranche could investigate
  each and either confirm "deliberately absent" (like several this tranche
  DID confirm directly from existing checks) or write the seam document.
- **14 of 20 `SEAM-*.md` documents have no `Sweep:` header**
  (`docs_verify --coverage`). SCHEMA.md's own rule: this is advisory,
  ratcheting in only "the next time the document is edited" — this
  tranche never edited a `SEAM-*.md` document's body, so it doesn't
  trigger the ratchet. Noted for whoever next touches one of those 14.
- **Writing the SEAM documents themselves** for any `Seams-undocumented`
  pair, including the ones this tranche's own audit confirmed real
  (e.g. `harness x scratch`, `llm x schools`, `manifest x scratch`). R2
  asked for naming and glossing in prose, not full seam documents — SPEC.md
  called this out explicitly as out of scope.
- **`bridge × ontology` stays genuinely unwritten** in `INDEX.md`'s seam
  matrix (coupling 15, no file) — the only row this tranche's INDEX.md
  fix (ERRATA E9) left as "not yet written" because it is actually true;
  everything else previously marked that way already had a real document.
