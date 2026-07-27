# e31-axiom-002 — synthetic axiom domain (Gleiglorl)

Class 1 (instance-fresh): a freshly generated axiomatic system over
uninterpreted symbols, pinned in Lean 4 (`domain.lean`).  Schema
templates are recognizable structure a model may know in the
abstract; every instance (symbols, operator assignments,
orientations) is freshly generated at build time, so this exact
problem cannot appear in any training corpus.
Prove the target theorems from the class hypotheses; the pinned
verification request (`pinned_lean_request.json`) forbids `sorry`.

## Axioms

- `vogrer(vogrer(x)) = x`
- `kreimulp(x, y) = kreimulp(y, x)`
- `kroveil(kroveil(x, y), z) = kroveil(x, kreimulp(y, z))`
- `kroveil(x, skarsnein) = x`
- `vogrer(vogrer(x)) = vogrer(x)`
- `kreimulp(kreimulp(x, y), z) = kreimulp(x, kroveil(y, z))`
- `kroveil(x, kreimulp(x, y)) = kreimulp(x, kroveil(x, y))`

## Targets (graded by bounded canonical rewrite depth — relative
to the build-time bounded prover, not a bound on all proof methods)

- `gleiglorl_d1_t1` (depth grade 1): `forall y. kreimulp(vogrer(vogrer(skarsnein)), y) = kreimulp(skarsnein, y)`
- `gleiglorl_d2_t2` (depth grade 2): `forall y. kreimulp(vogrer(vogrer(skarsnein)), y) = kreimulp(y, skarsnein)`
- `gleiglorl_d3_t3` (depth grade 3): `forall x. vogrer(kroveil(grathrux(x), skarsnein)) = grathrux(x)`
- `gleiglorl_d4_t4` (depth grade 4): `forall y. kroveil(skarsnein, kreimulp(vogrer(y), skarsnein)) = kroveil(skarsnein, y)`

Difficulty certificates and derivations are sealed in the holdout
namespace (digests in the manifest) and revealed only post-hoc.
