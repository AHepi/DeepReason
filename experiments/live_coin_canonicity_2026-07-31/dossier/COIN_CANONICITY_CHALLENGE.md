# Challenge: deciding whether a coin system is canonical

This dossier states the problem and the rules under which a claim about
it counts as established. It deliberately states NO bounds, NO example
systems, and NO prior results. Everything of that kind must be derived,
or fetched from the research allowlist, or established by simulation —
and cited as whichever it is.

## The objects

A **coin system** is a strictly decreasing tuple of positive integers

    C = (c_1 > c_2 > ... > c_n),  with  c_n = 1.

Because c_n = 1, every non-negative integer amount has at least one
representation as a multiset of coin values summing to it.

The **greedy representation** of an amount w takes, repeatedly, the
largest coin not exceeding the amount that remains:

    G(w) = 0                      if w = 0
    G(w) = 1 + G(w - c_i)         otherwise, where c_i is the largest
                                  coin with c_i <= w

The **optimal count** OPT(w) is the minimum number of coins, counted
with multiplicity, in any representation of w.

C is **canonical** when G(w) = OPT(w) for every non-negative integer w.
A **counterexample** is an amount w with G(w) > OPT(w). Note G(w) is
never less than OPT(w), so those are the only two cases.

## The task

Produce a decision procedure that, given C, decides canonicity, and when
C is not canonical also returns the SMALLEST counterexample amount. The
procedure must be stated precisely enough to implement, proved correct,
and its worst-case running time stated as a function of n — the number
of coins, not the magnitude of any coin.

## Why this is not trivially decidable

Canonicity quantifies over infinitely many amounts. Any procedure that
terminates must therefore justify a finite search: either a bound W such
that a counterexample above W implies a counterexample at or below W, or
a structural characterisation that avoids enumerating amounts at all.
That justification is the mathematical content of the problem. A
procedure that checks "enough" amounts without proving the bound has not
solved it — it has guessed a constant.

Two distinct complexity classes are available and must not be conflated:

  - Time polynomial in the MAGNITUDE of the coins (e.g. proportional to
    c_1). This is pseudo-polynomial: c_1 is written in log c_1 bits, so
    such a procedure is exponential in the size of its input.
  - Time polynomial in n ALONE, independent of the coin magnitudes.

A claim that a procedure is polynomial must say which of these it means.

## What counts as established here

**A bound is a conjecture until a simulation attacks it.** Any claimed
search bound W(C) — any formula for how far a procedure must look — is
a refutable claim with a cheap, decisive test: search coin systems for
one whose smallest counterexample exceeds the claimed bound. A single
such system refutes the bound outright, and the procedure built on it
returns "canonical" for a system that is not. Bounds are therefore to be
attacked before they are relied on, not after.

**Brute force is exactly available as an oracle.** For any specific coin
system and any amount limit, OPT is computable by dynamic programming in
time proportional to the limit times n, and G by direct simulation.
Comparing them over a large range is a complete decision procedure for
"is there a counterexample below this limit", and it is exact integer
arithmetic with no tolerance and no sampling. So a candidate procedure
can be differentially tested against the oracle over many systems, and
a claimed smallest counterexample can be confirmed or refuted outright.

**Calibrate the oracle before trusting it.** An oracle that reports no
counterexample for every system it is given proves nothing. Before its
verdicts are offered as evidence, show it separates the two cases: that
it reports a counterexample for at least one system, with the amount,
and reports none for at least one system, and that its G and OPT agree
on amounts that both can be checked by hand.

**Search is available and is stronger than assertion.** The space of
small coin systems is enumerable — all strictly decreasing tuples ending
in 1 with values under a modest limit — and every one is decidable by
the oracle. A structural claim about which systems are non-canonical, or
about where their smallest counterexamples sit, can therefore be tested
against the entire small-format space rather than argued from examples.

## Provenance of this dossier

This dossier contains definitions and rules of evidence only. It asserts
no bound, names no prior author, and reports no experimental result, so
there is nothing in it to cite as a fact about the answer. Attachment
establishes provenance, never truth; here it establishes only what the
words mean.
