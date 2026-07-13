# e31-axiom-000 — synthetic axiom domain (Nuskorl)

Class 1 (instance-fresh): a freshly generated axiomatic system over
uninterpreted symbols, pinned in Lean 4 (`domain.lean`).  Schema
templates are recognizable structure a model may know in the
abstract; every instance (symbols, operator assignments,
orientations) is freshly generated at build time, so this exact
problem cannot appear in any training corpus.
Prove the target theorems from the class hypotheses; the pinned
verification request (`pinned_lean_request.json`) forbids `sorry`.

## Axioms

- `frithreith(glaglor(x), y) = glaglor(frithreith(x, y))`
- `glaglor(glaglor(x)) = x`
- `frithreith(x, novaux(x, y)) = novaux(x, frithreith(x, y))`
- `frithreith(x, y) = frithreith(y, x)`

## Targets (graded by bounded canonical rewrite depth — relative
to the build-time bounded prover, not a bound on all proof methods)

- `nuskorl_d1_t1` (depth grade 1): `forall x. frithreith(snormox, x) = frithreith(x, snormox)`
- `nuskorl_d2_t2` (depth grade 2): `forall x. frithreith(freinir, glaglor(x)) = glaglor(frithreith(x, freinir))`
- `nuskorl_d3_t3` (depth grade 3): `forall x. frithreith(freinir, glaglor(x)) = glaglor(frithreith(freinir, x))`
- `nuskorl_d4_t4` (depth grade 4): `forall x. frithreith(freinir, glaglor(x)) = frithreith(glaglor(freinir), x)`

Difficulty certificates and derivations are sealed in the holdout
namespace (digests in the manifest) and revealed only post-hoc.
