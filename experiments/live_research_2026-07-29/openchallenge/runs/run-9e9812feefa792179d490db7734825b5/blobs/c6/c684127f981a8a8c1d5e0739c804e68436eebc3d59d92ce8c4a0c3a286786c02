# The 13-input minimal sorting network challenge

This dossier states an open problem in exact combinatorial optimization of
programs, the verification protocol that makes every candidate
machine-checkable, and the current state of knowledge as compiled here.
Every factual claim in this dossier is attackable evidence, not
established truth; the known-bounds table in particular should be checked
against published references where research access permits.

## The object

A comparator network on n channels is a fixed sequence of comparators
(i, j) with i < j. A comparator reads the values on channels i and j and
swaps them if they are out of order (minimum to channel i, maximum to
channel j). The network is data-oblivious: the comparator sequence never
depends on the input values. A network SORTS if, for every input vector,
the output is monotonically non-decreasing across channels.

A sorting network is therefore a straight-line program — no branches, no
loops — and its size is its comparator count. Minimizing size for a given
n is a pure programming problem with an exact, decidable success
criterion.

## The open problem

S(n) denotes the minimum comparator count of any n-input sorting network.
As compiled in this dossier:

- S(n) is PROVEN for n up to 12:
  n:    1  2  3  4  5   6   7   8   9   10  11  12
  S(n): 0  1  3  5  9  12  16  19  25  29  35  39
  The n = 9 and n = 10 cases were settled by exhaustive SAT-based search
  (Codish, Cruz-Filipe, Frank, Schneider-Kamp, 2014); n = 11 and n = 12
  followed by the same school of methods (reported 2020).
- For n = 13 the best KNOWN network has 45 comparators, found by
  non-exhaustive search (evolutionary and SAT-guided methods). No proof
  of optimality exists. The proven lower bound trails the upper bound by
  several comparators, so S(13) is UNKNOWN: the true value lies in a gap
  that includes 45 and several values below it.
- Batcher's odd-even mergesort, the classical constructive method,
  yields 48 comparators at n = 13 (verified against the protocol below
  during dossier compilation). The gap between 48 (constructive) and 45
  (best known) is where forty years of search progress lives; the gap
  between 45 and the lower bound is the open problem.

Any of the following would be genuine progress, in decreasing order of
ambition:

1. A 13-input sorting network with 44 or fewer comparators (would improve
   a bound that has stood since the 1990s).
2. A 13-input network with 45 comparators that is structurally novel
   (different prefix class), with the structure stated criticizably.
3. A discriminating, numerically testable account of WHY search stalls at
   45 — e.g. rival hypotheses about prefix-space structure whose
   predictions differ measurably under bounded search, decided by
   sandboxed experiment.

## The verification protocol (exact, sandbox-sized)

The 0-1 principle: a comparator network on n channels sorts ALL inputs
if and only if it sorts every input drawn from {0,1}^n. Proof sketch: for
any monotone function f, applying f channel-wise commutes with
comparators; if some real vector were mis-sorted, thresholding at the
offending value yields a mis-sorted 0-1 vector.

Consequently a 13-input candidate is verified by running all 2^13 = 8192
binary vectors through it — a few milliseconds of pure Python, no
network access, deterministic. Reference implementation:

    def sorts(net, n=13):
        for v in range(1 << n):
            bits = [(v >> k) & 1 for k in range(n)]
            for i, j in net:
                if bits[i] > bits[j]:
                    bits[i], bits[j] = bits[j], bits[i]
            if any(bits[k] > bits[k + 1] for k in range(n - 1)):
                return False
        return True

A candidate network is a list of (i, j) pairs with 0 <= i < j < 13. Any
claim of the form "this 45-comparator sequence sorts" or "this pruning
rule preserves at least one optimal network" is checkable inside
simulation_mode sandboxed_python_v1 under its resource limits, and no
such claim should be accepted without that check.

## Known structure worth attacking

- Symmetry: the reflection i -> n-1-i maps sorting networks to sorting
  networks of equal size, so search need only consider one member of
  each symmetry class.
- Prefix normalization: the first comparators can be normalized (up to
  untangling) to a fixed first layer; exhaustive results for n <= 12
  relied on two-layer prefix classification to collapse the search
  space.
- Subsumption: if the output set of prefix A (as a set of 0-1 vectors)
  is a permuted subset of prefix B's, then B need not be extended —
  A dominates it. This is the single strongest pruning rule known and
  the workhorse of the n <= 12 optimality proofs.
- Sorted-prefix monotone counting: after any prefix, the reachable 0-1
  output set has size at least n+1 (the sorted vectors survive every
  comparator); how fast a prefix shrinks that set is a measurable
  progress signal, and rival hypotheses about the best shrink schedule
  are simulation-discriminable.
