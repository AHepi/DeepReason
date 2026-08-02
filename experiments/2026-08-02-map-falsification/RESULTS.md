# Map falsification — 2026-08-02

Ten Opus 5 agents, one per seam document that had not yet been adversarially
verified, each instructed to BREAK its document: mutate `src/` until every
`check:` demonstrably fails, rewrite checks that cannot, verify every table
symbol, revert every mutation, end with a clean tree.

## Tally (from the ten agents' reports; each report is the evidence)

- ~160 checks proved failable under ~590 reverted mutations
- 44 checks rewritten or added (were vacuous, evadable, dead, or absent)
- 3 false claims corrected, 1 false Traps entry deleted, ~15 factual
  corrections; beyond those, no claims deleted — the documents' substance held
- 2 previously unnamed enforcement sites found and added
  (runtime/terminal_authority.py; ontology/event.py record-level guards)
- 0 stranded mutations; frozen-surface reverts hash-verified
- Six recurring check-defect classes extracted into docs/map/SCHEMA.md

Residue: 14 of 19 seams still carry no `Sweep:` header (ratchet: added when
next touched). "Accepted does not mean true" — the checks prove structure,
not completeness; `--coverage` is the completeness instrument and only five
seams are swept.

## The finding that outranks the map

Falsification stopped finding documentation defects and started finding REPO
defects: guards whose death no test detects. Parked below; each is a
defect-tranche candidate, not fixed here (cross-routing rule).
