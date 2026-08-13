---
name: dr-audit-spec-drift
description: Audit dimension - find where the code deviates from the spec series and where shipped surface is spec-silent, by a two-direction term census. Invoked by dr-audit-orchestrator when spec-drift.md is missing.
---

# Audit: code vs spec

Entry: `LEDGER.md` exists, `spec-drift.md` missing. Exit:
`spec-drift.md` written, LEDGER rows added, proofs in `proof/`.

Two directions, both mechanical:
- SPEC→TREE: a term the spec names that the tree no longer honors =
  the code deviates from spec.
- TREE→SPEC: a shipped public surface the spec never mentions = the
  spec is behind the code.

The spec series is every `docs/harness-spec-*.md` (base + all
amendments — read ALL amendments; later files supersede earlier ones
on conflict, so verify a term against the newest file naming it).

## Operations

1. SPEC term census:
   `rg -o -N '\x60[A-Za-z_][A-Za-z0-9_.:-]*\x60' docs/harness-spec-*.md | sort -u > proof/spec-terms.txt`
   plus every `##`-level heading noun phrase. This is the SPEC list.
2. For each SPEC term: `rg -l -w '<term>' src/deepreason/` (identifiers)
   or `rg -l '<term>' src/ docs/map/` (concept phrases). Zero hits →
   verdict `spec-orphan` (spec names it, tree does not have it), one
   row each with the scan saved. Hits → tally only.
3. TREE surface census, three lists with proofs:
   a. CLI flags: `rg -o -N '"--[a-z][a-z0-9-]*"' src/deepreason/cli/main.py | sort -u`
   b. Config fields: `rg -o -N '^    [A-Z][A-Z0-9_]*:' src/deepreason/config.py | sort -u`
   c. Typed error/refusal strings: `rg -o -N '"[A-Z][A-Z0-9_]{6,}"' src/deepreason/run_manifest.py src/deepreason/preparation.py | sort -u`
4. For each TREE surface item: `rg -l -F '<item>' docs/harness-spec-*.md`.
   Zero hits → verdict `spec-silent` (shipped, undocumented in spec),
   one row each. Batch rows by feature, not per flag, when one tranche
   shipped them together (the row names the batch and lists members).
5. Write `spec-drift.md`: two tables (one per direction) with count
   lines. The `spec-silent` table's parked prompt is a spec-amendment
   draft request (append-only amendment file, never an edit to
   existing spec text), route dr-change-orchestrator.

## GATE

Pass: proofs exist for both censuses; every `spec-orphan` and every
`spec-silent` row cites its scan file; count lines match row counts.
Verdict labels: `spec-orphan` | `spec-silent` | `covered`.

## Activation plant (first run)

Append a fabricated term row to the SPEC list copy in
`proof/spec-terms.txt`; step 2 must produce a `spec-orphan` verdict
for it (zero hits). Delete the fabricated row, note the plant in
ACTIVATION.md.

## Outlets

| Situation | Outlet |
|---|---|
| Impulse to draft the amendment now | PARK — amendment prompt, route dr-change-orchestrator |
| A spec term superseded by a newer amendment | verdict `covered`, row notes the superseding file |
| Term ambiguous between identifier and concept | run both scan shapes, row the weaker result, save both proofs |
