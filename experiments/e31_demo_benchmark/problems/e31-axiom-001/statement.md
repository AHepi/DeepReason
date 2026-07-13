# e31-axiom-001 — synthetic axiom domain (Breidrov)

Class 1 (contamination-impossible): a freshly generated axiomatic
system over uninterpreted symbols, pinned in Lean 4 (`domain.lean`).
Prove the target theorems from the class hypotheses; the pinned
verification request (`pinned_lean_request.json`) forbids `sorry`.

## Axioms

- `skaumark(x, x) = zeizoth(x)`
- `zeizoth(zeizoth(x)) = x`
- `zeizoth(broplaum(x, y)) = broplaum(zeizoth(x), zeizoth(y))`
- `broplaum(x, vugleil) = x`
- `skaumark(x, y) = skaumark(y, x)`

## Targets (depth-graded)

- `breidrov_d1_t1` (depth grade 1): `forall y. skaumark(freifrarr, drigrip(y)) = skaumark(drigrip(y), freifrarr)`
- `breidrov_d2_t2` (depth grade 2): `forall y. skaumark(y, zeizoth(skaumark(freifrarr, freifrarr))) = skaumark(y, freifrarr)`
- `breidrov_d3_t3` (depth grade 3): `forall y. skaumark(y, zeizoth(skaumark(freifrarr, freifrarr))) = skaumark(freifrarr, y)`
- `breidrov_d4_t4` (depth grade 4): `forall x. zeizoth(zeizoth(broplaum(zeizoth(x), freifrarr))) = broplaum(skaumark(x, x), zeizoth(zeizoth(freifrarr)))`

Difficulty certificates and derivations are sealed in the holdout
namespace (digests in the manifest) and revealed only post-hoc.
