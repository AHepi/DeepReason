---
name: dr-audit-docs-drift
description: Audit dimension - find where documentation deviates from code, using the executable doc checks plus a staleness and unchecked-claims census. Invoked by dr-audit-orchestrator when docs-drift.md is missing.
---

# Audit: documentation vs code

Entry: `LEDGER.md` exists, `docs-drift.md` missing. Exit:
`docs-drift.md` written, LEDGER rows added, proofs in `proof/`.

The primary instrument already exists: every load-bearing map claim
carries an executable `check:` line. This worker runs the instrument,
then censuses what the instrument cannot see.

## Operations

1. `python tools/docs_verify.py > proof/docs-full.txt` — non-baseline
   failing check → verdict `drifted` (doc says X, tree says not-X),
   one row per check.
2. `python tools/docs_verify.py --audit > proof/docs-audit.txt` — any
   finding → verdict `toothless-check` (a check that cannot fail
   guards nothing), one row each.
3. `python tools/docs_verify.py --links > proof/docs-links.txt` — any
   dangling `DR-` reference → verdict `drifted`.
4. `python tools/docs_verify.py --stale > proof/docs-stale.txt` —
   table the stale list as verdict `stale-stamp` rows (advisory:
   `Verified-at` behind the code it describes; not proof of drift,
   proof nobody has looked).
5. Unchecked-claims census, docs outside the map (they carry no
   `check:` lines): for each file in `docs/*.md` (top level only),
   `rg -c 'check:' <file>`. Zero checks AND the file's header/Status
   line asserts a current-state claim → verify that one claim by
   grep against the tree; broken → verdict `drifted` (the
   RESEARCH_BACKEND header precedent, ledgered as E20). Row only the
   header/Status claim — deep prose audit is a spec-drift or manual
   tranche, not this pass.
6. Write `docs-drift.md`: one table, columns as the LEDGER, plus the
   count line. All clean → the table plus `all doc instruments at
   baseline` with the five proof files (G2).

## GATE

Pass: five proof files exist; every non-baseline instrument delta has
a row; every `drifted` row's disposition is `parked`. Verdict labels:
`drifted` | `toothless-check` | `stale-stamp` | `baseline`.

## Activation plant (first run)

Change one numeral inside one map document's prose claim (not its
`check:` line), run step 1 scoped
(`python tools/docs_verify.py <file>` if supported, else full),
confirm the check catches it OR row the miss as a `toothless-check`
finding against that document; `git checkout --` the file, paste the
clean status. Either outcome is a valid activation (the plant proves
the instrument's edge, red or blind).

## Outlets

| Situation | Outlet |
|---|---|
| Impulse to fix the doc now | PARK — doc-fix prompt, route dr-change-orchestrator |
| Check fails because the CODE regressed | verdict `drifted`, note `code-side`, PARK with route deepreason-orchestrator |
| Stale stamp on a passing doc | verdict `stale-stamp`, disposition `baseline` — re-stamping without re-running is the one forbidden move |
