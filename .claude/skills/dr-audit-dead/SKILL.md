---
name: dr-audit-dead
description: Audit dimension - find code that is no longer used, via a reference census over every top-level symbol, one package per invocation. Invoked by dr-audit-orchestrator when dead.md is missing or has pending package rows.
---

# Audit: dead code

Entry: `LEDGER.md` exists; `dead.md` missing or contains a package
row marked `pending`. Exit for one invocation: ONE package's census
complete, its row flipped to `done`. The router re-invokes until no
`pending` rows remain (S1: the loop lives in the router).

On first invocation, write the package list into `dead.md`:
`ls -d src/deepreason/*/ src/deepreason/*.py`, one row each, all
`pending`.

## Operations (for the next pending package P)

1. Symbol census:
   `rg -n '^(def|class) [A-Za-z_]' <P> --type py > proof/dead-<P>-symbols.txt`
2. For each symbol NAME, count referencing files outside its defining
   file:
   `rg -l -w 'NAME' src/ tests/ scripts/ tools/ | grep -v <defining-file>`
   Hits ≥ 1 → verdict `referenced` (no LEDGER row; tally only).
   Hits = 0 → step 3.
3. String-reference scan (dynamic dispatch, registries, config
   strings):
   `rg -l "['\"]NAME['\"]" src/ tests/ scripts/ tools/`
   Hits ≥ 1 → verdict `dynamic-ref`, row it with the hit file (these
   are load-bearing but invisible to imports — worth a row, not a
   prompt). Hits = 0 → step 4.
4. Entry-point scan: `rg -l 'NAME' pyproject.toml`. Hit → verdict
   `entry-point`. No hit → verdict `candidate-dead`, row it,
   disposition `parked`, both scan outputs saved to
   `proof/dead-<id>.txt`.
5. Append the package's tally line to `dead.md`
   (`P: S symbols, R referenced, D dynamic-ref, C candidate-dead`)
   and flip its row to `done`.

## GATE

Pass for the invocation: the package row is `done`, its tally line
exists, and every `candidate-dead` row cites a proof file containing
BOTH empty scans (G2 — "dead" is only sayable with the two searches
pasted). Verdict labels: `referenced` | `dynamic-ref` |
`entry-point` | `candidate-dead`.

`candidate-dead` is the strongest claim this worker may make (X3).
Deletion needs a dr-change-orchestrator tranche; the PARKED prompt
says so and names the symbol, file, and proof.

## Activation plant (first run)

Row a symbol that step 2 provably finds referenced (pick any imported
name) as if it were a candidate; the GATE's proof-file check must
refuse the row (no empty-scan proof exists). Remove the planted row,
paste the refusal and the removal.

## Outlets

| Situation | Outlet |
|---|---|
| Impulse to delete now | PARK — removal prompt, route dr-change-orchestrator |
| Symbol used only by tests | verdict `referenced`, note `tests-only` in the row — parked prompt optional |
| Census too large for one window | flip the package back to `pending` with a `resume-at: NAME` note; the LEDGER carries the position |
