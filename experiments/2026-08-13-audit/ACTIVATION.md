# ACTIVATION — 2026-08-13 audit, model claude-sonnet-5

First `dr-audit-orchestrator` run in this clone for this model id. Per
each worker's `Activation plant` section, one planted violation was
run through the worker's own GATE, seen red (or, where the worker's
own rules say either outcome is valid, seen blind) once, then
restored. `git status --porcelain` is clean after every restore
(pasted below each row).

## 1. dr-audit-broken

Plant: `tests/test_error_catalog.py::test_catalog_covers_46_entries`
edited to assert `len(CATALOG) == 999999` (was `46`). Scoped run:
`python -m pytest tests/test_error_catalog.py -q`.

Red output (`proof/activation-broken-red.txt`):

    ..F....
    FAILED tests/test_error_catalog.py::test_catalog_covers_46_entries
    AssertionError: assert 46 == 999999
    1 failed, 6 passed in 0.32s

Restore: `git checkout -- tests/test_error_catalog.py`.
`git status --porcelain -- tests/test_error_catalog.py` →
`proof/activation-broken-restore.txt` (empty — clean).

## 2. dr-audit-dead

Plant: attempted to row `lookup` (an imported symbol from
`error_catalog.py`, used in `qualification.py`, `cli/main.py`,
`rules/conj.py`, tests, etc.) as `candidate-dead`, i.e. without doing
the two required empty scans first.

Refusal proof (`proof/activation-dead.txt`): the step-2 reference scan
(`rg -l -w 'lookup' src/ tests/ scripts/ tools/`, excluding the
defining file) returns 13 hits — non-empty. Per the worker's GATE, a
`candidate-dead` row is only sayable with both scans empty and pasted
(G2); this symbol's proof file cannot show that, so the planted row is
refused. Verdict is `referenced`, not `candidate-dead`.

Removal: no row was added to (the not-yet-existing) `dead.md`; nothing
to restore in the tree.

## 3. dr-audit-docs-drift

Plant: changed one numeral inside prose (not inside a `check:` line)
in `docs/map/SUB-scheduler.md` line 97 — "roughly thirty branch
points read its `schema_version`" → "roughly three hundred branch
points". The nearby `check:` line (verifying
`grep -c "self\.run_manifest" ... -ge 25`) tests a *count in code*,
not this English word, so it cannot catch a change to the word itself.
Ran `python tools/docs_verify.py` (full — no single-file scoping is
supported; see `--help`).

Result (`proof/activation-docs-drift.txt`): `docs_verify: 3 failed`,
all three the baseline `CON-run-identity.md` git-history checks (§
Instruments in `docs/AUDIT_BASELINES.md` — unshallowed-clone
prerequisite). No new failure — the plant is **blind**, a valid
activation outcome per the worker's own instructions ("Either outcome
is a valid activation... red or blind"). This edge case (a `check:`
line whose numeral is looser than the prose sentence next to it) is
carried forward as a candidate `docs-drift` finding for the real
`dr-audit-docs-drift` pass, not fixed here.

Restore: `git checkout -- docs/map/SUB-scheduler.md`.
`git status --porcelain` → clean (confirmed below).

## 4. dr-audit-spec-drift

Plant: fabricated SPEC term `FAKE_NONEXISTENT_SPEC_TERM_XYZ` appended
to a scratch copy of the term census (not the real `spec-terms.txt`,
which the real worker pass will produce). Step-2 scan:
`rg -l -w 'FAKE_NONEXISTENT_SPEC_TERM_XYZ' src/deepreason/`.

Result (`proof/activation-spec-drift.txt`): zero hits (exit 1) → the
GATE correctly produces verdict `spec-orphan` for the fabricated term,
as expected.

Removal: fabricated row deleted from the scratch copy; nothing carried
into (the not-yet-existing) `spec-drift.md`.

## 5. dr-audit-goal-trace

Plant: fabricated law "all conjectures must rhyme" appended to a
scratch copy of the law census (not the real `goal-laws.txt`, which
the real worker pass will produce from CLAUDE.md § "Operator design
laws"). Scans: `rg -l -i 'must rhyme' src/deepreason/` and
`rg -l -i 'must rhyme' tests/`.

Result (`proof/activation-goal-trace.txt`): both scans empty (exit 1)
→ the GATE correctly produces verdict `unenforced` for the fabricated
law, as expected.

Removal: fabricated row deleted from the scratch copy; nothing carried
into (the not-yet-existing) `goal-trace.md`.

## Final clean-tree confirmation

    git status --porcelain
    ?? experiments/2026-08-13-audit/

(only the tranche directory itself — no tracked file left modified by
any plant).

All five workers' GATEs proven red-or-blind-per-spec once. Activation
complete; proceeding to the five audit dimensions.
