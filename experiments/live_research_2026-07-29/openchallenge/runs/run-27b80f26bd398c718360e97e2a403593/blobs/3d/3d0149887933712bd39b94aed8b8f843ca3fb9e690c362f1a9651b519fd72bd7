# Open challenge: the rank of the 3x3 matrix multiplication tensor

## The problem

Multiplying two 3x3 matrices by the schoolbook method costs 27 scalar
multiplications. The question is how few scalar multiplications suffice.

Formally: the multiplication of n x n matrices is a bilinear map, and is
encoded by a tensor `<n,n,n>` in `F^(n^2) (x) F^(n^2) (x) F^(n^2)`. Its
TENSOR RANK R(n,n,n) is the least r such that the tensor can be written
as a sum of r simple (rank-one) triples. Rank r means an algorithm using
exactly r scalar multiplications between entries of the two inputs,
with additions and scalar scaling free.

**R(3,3,3) is unknown.** The best construction anyone has found uses 23
multiplications. The best proved lower bound is 19. Whether 22, 21, or
20 is achievable is open, and has been open since the 1970s.

## Bounds table (attackable; check it)

| case | lower bound | best known upper | status |
|---|---|---|---|
| 2x2 | 7 | 7 | SETTLED. Strassen 1969 gives 7; Winograd proved 7 optimal. |
| 3x3 | 19 | 23 | OPEN. Laderman 1976 gives 23; Smirnov and later AlphaTensor also reach 23, none below. Lower bound 19 attributed to Blaeser (2003). |
| 4x4 | 34 | 49 (=7^2, Strassen recursion) | OPEN. AlphaTensor reported 47 over F_2 only. |

This table is compiled from memory at dossier-authoring time and is NOT
authoritative. Two numbers in particular deserve checking against
published sources: the 19 lower bound for 3x3, and whether any published
construction below 23 exists for 3x3 over any field. If research
contradicts this table, the contradiction is a finding — record it.

## Why 22 is the interesting target

23 has stood since 1976 despite: decades of hand construction; numerical
alternating-least-squares searches; SAT and Groebner-basis attacks; and
a large reinforcement-learning search (AlphaTensor) that rediscovered 23
without beating it. Either 22 exists and every method so far has missed
it, or something structural forbids it and no lower-bound technique yet
proves it. Those are rival explanations of the same evidence, and they
predict different things.

## Exact verification (this is the decisive property)

Any candidate answer is checkable exactly, in milliseconds, with integer
arithmetic and no floating point.

A rank-r decomposition is r triples `(U_k, V_k, W_k)`, k = 1..r, each a
3x3 matrix of coefficients. The claim is the tensor identity

    sum_k  U_k[i,j] * V_k[l,m] * W_k[p,q]  ==  T[(i,j),(l,m),(p,q)]

where the 3x3 matrix multiplication tensor T has entries

    T[(i,j),(l,m),(p,q)] = 1  if  j == l  and  m == p  and  q == i
    T[...]                = 0  otherwise

Equivalently, and easier to test directly: the decomposition yields the
algorithm

    P_k = ( sum_{i,j} U_k[i,j] * A[i,j] ) * ( sum_{l,m} V_k[l,m] * B[l,m] )
    C[p,q] = sum_k W_k[q,p] * P_k          (note the index order)

and correctness means C == A @ B identically as polynomials in the 18
input variables. Checking the 729 tensor entries is a complete decision
procedure: 729 integer comparisons. There is no sampling, no tolerance,
no ambiguity.

Sanity anchor: Strassen's 2x2 algorithm is the r=7 case of exactly this
format and can be verified by the same routine over the 64 entries of
the `<2,2,2>` tensor. Any verifier proposed for 3x3 should be shown to
accept Strassen at 2x2 and reject a deliberately corrupted Strassen.

## Live positions to attack or defend

These are the rival explanations currently on the table. They are not
settled and are offered as targets, not as accepted claims.

1. **Symmetry obstruction.** The `<3,3,3>` tensor has a large symmetry
   group. If every rank-22 decomposition would have to break that
   symmetry in a way that forces a contradiction, 22 is impossible.
   Rival prediction: symmetry-restricted searches should provably
   exclude 22 in their restricted class.
2. **Lower-bound technique ceiling.** The substitution method and the
   laser method may simply be incapable of proving anything above ~19-20
   for this format, so the gap is evidence about our tools, not about
   the tensor. Rival prediction: no technique in the current family will
   close the gap regardless of effort.
3. **Field dependence.** Rank can differ over different fields. A
   22-term solution might exist over a small finite field and fail to
   lift to Q or Z. Rival prediction: searches mod small primes should
   find solutions that do not lift.
4. **Border rank gap.** Border rank (where the decomposition is a limit
   of approximations) is known to be strictly less than rank for some
   tensors. If `<3,3,3>` has border rank well below 23, numerical
   searches would be expected to converge to near-solutions that never
   become exact. Rival prediction: ALS residuals should approach zero
   without ever reaching it, with coefficients diverging.
5. **Search inadequacy.** 22 exists and is merely rare. Rival
   prediction: a search method calibrated to reliably find rank 7 at
   2x2 should, given proportionate budget, find 23 at 3x3 from scratch —
   and if it cannot even do THAT, its failure at 22 says nothing.

Position 5 supplies the sharpest available experiment, because 2x2 has a
known answer: a method that cannot rediscover Strassen has not earned
the right to be cited as evidence that 22 does not exist.

## What would count as progress, in order of ambition

1. A verified 3x3 decomposition with 22 or fewer multiplications. This
   would be a genuine mathematical result. Verify it in the sandbox
   before claiming it.
2. A verified, structurally novel 23 — for example one with a symmetry
   the published constructions lack.
3. A simulation-discriminated account of WHICH of the rival positions
   above best explains the 47-year stall at 23, where the simulation
   actually distinguishes them rather than illustrating one.
4. A correct negative: a demonstration, with exhaustive search at a
   decidable smaller format, that a proposed structural lemma is FALSE.
   A refuted conjecture recorded honestly is worth more than an
   unrefuted one asserted.
