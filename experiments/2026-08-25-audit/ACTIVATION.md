# ACTIVATION — 2026-08-25 audit, model `claude-opus-5`

The prior `ACTIVATION.md` in this clone
(`experiments/2026-08-13-audit/ACTIVATION.md`) was recorded for
`claude-sonnet-5`. This run is `claude-opus-5` — a model change, so per
`dr-audit-orchestrator`'s activation rule every worker GATE is re-proven
before its findings are trusted.

`git status --porcelain` is clean outside this tranche directory after
every restore.

## 1. dr-audit-broken

Plant: `tests/test_error_catalog.py:24`, `assert len(CATALOG) == 48` →
`== 999999`. Scoped run: `python -m pytest tests/test_error_catalog.py -q`.

Red (`proof/activation-broken.txt`):

    E       AssertionError: assert 48 == 999999
    FAILED tests/test_error_catalog.py::test_catalog_covers_48_entries
    1 failed, 7 passed in 0.27s

Restore: `git checkout --`; status clean; re-run `8 passed in 0.24s`.

Note in passing: the catalog holds **48** entries now, against the 46 the
2026-08-13 plant used. Growth, not a finding.

## 2. dr-audit-docs-drift — BLIND, and that is a valid outcome

Plant: `docs/map/SEAM-harness-x-verification.md:147`, the PROSE numeral
`a 1083-file committed one` → `a 9999-file committed one`. The `check:`
line 3 lines below, which independently asserts `len(c)==1083` against the
real root, was left untouched. Scoped run: `python tools/docs_verify.py --fast`.

Result (`proof/activation-docs-drift.txt`): **not red — blind.** 1069
checks reused, 3 failed, and those three are the same `CON-run-identity`
git-history baseline failures, unrelated to the plant.

The worker's own rule admits this: "confirm the check catches it OR row
the miss as a `toothless-check` finding … Either outcome is a valid
activation (the plant proves the instrument's edge, red or blind)."

**The edge it proves.** A `check:` line authenticates a CLAIM against the
tree. Line 150 reads the filesystem, finds 1083 files, and passes. It
never reads line 147. So a checked number is authenticated, and *the same
number restated in the sentence beside it is not*. Full mode would be
blind here too — derivable from the check's own text rather than needing
a second nine-minute run, since that command reads the filesystem and
nothing else.

**Not rowed as `toothless-check`:** `--audit` returned 0 findings, and
the line-150 check genuinely can fail — it would, the moment that root
changed. An unguarded prose restatement is a known property of the
`check:` mechanism, not a defect in this document.

**Incidental finding, worth more than the plant.** `--fast` reported
`1069 reused` — it re-ran *nothing*, despite the edited file. It keys on
the files a check touches, not on the document's own mtime. That
independently confirms CLAUDE.md's warning that `--fast` "CANNOT catch a
document your `src/` change just broke", and shows it also cannot catch a
change to the document itself.

## 3. dr-audit-spec-drift

Plant: `ZzFabricatedSpecTermQqq` appended to a COPY of
`proof/spec-terms.txt`. Scan: `grep -rqIw -F` over `src/` and `docs/map/`
→ zero hits → verdict `spec-orphan`, as the worker requires.
`proof/spec-terms.txt` itself was never edited
(`proof/activation-spec-drift.txt`).

## 4. dr-audit-goal-trace

Plant: fabricated law "Every conjecture must rhyme" added to a COPY of
`proof/goal-laws.txt`. Both scans (mechanism over `src/deepreason/`, test
over `tests/`) returned empty → verdict `unenforced`, as required.
`proof/goal-laws.txt` holds 8 rows and no L9
(`proof/activation-goal-trace.txt`).

## 5. dr-audit-dead

Plant: attempt to row `verify_root` — an exported symbol imported across
the tree — as `candidate-dead`. Step 2's scan returned 8+ referencing
files outside its defining file, so the worker's own step 2 REFUSES the
row and returns `referenced`. Read-only plant, nothing to restore
(`proof/activation-dead.txt`).
