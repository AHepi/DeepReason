# Generalized ant automata: definitions and rules of evidence

This dossier states definitions ONLY. It contains no bounds, no worked
examples, no trajectory lengths, and no results. Everything below is
definitional; every claim about behaviour is yours to establish.

## 1. The rule-string grammar

A rule string is a word in this grammar. Parse it exactly as written; do not
assume a form it does not have.

    <rule>   ::= <turn> | <turn> <rule>
    <turn>   ::= "L" | "R" | "N" | "U"

The LENGTH of a rule string is its number of `<turn>` symbols, written k. A
rule string of length k defines an automaton over k cell states, numbered
0..k-1. Rule strings of length 0 are not well formed. There is no separator,
no whitespace, and no case folding: `RL` and `rl` are not the same input, and
only the upper-case forms above are well formed.

## 2. Operational semantics

The lattice is the set of integer pairs Z x Z. Every cell holds a state in
0..k-1. Initially every cell holds state 0.

The automaton has a position p in Z x Z and a facing f in {0,1,2,3}, where

    0 = +y      1 = -x      2 = -y      3 = +x

Initially p = (0,0) and f = 0.

Write `rule[c]` for the c-th symbol of the rule string, zero-indexed. Each
symbol denotes a rotation applied to the facing, measured in quarter turns
counterclockwise:

    L  ->  f := (f + 1) mod 4
    R  ->  f := (f + 3) mod 4
    N  ->  f unchanged
    U  ->  f := (f + 2) mod 4

One STEP is exactly the following, in this order:

  1. Let c be the state of the cell at p.
  2. Apply the rotation denoted by `rule[c]` to f.
  3. Set the state of the cell at p to (c + 1) mod k.
  4. Move p forward by a STRIDE of (c + 1) units in the direction now denoted
     by f. That is, p := p + (c + 1) * dir(f).

Two things about step 4 are easy to get wrong and both change the automaton.

The stride is (c + 1), where c is the state the cell held ON ARRIVAL — the
value read in step 1, not the value written in step 3. A cell found in state 0
gives a stride of 1; a cell found in state 2 gives a stride of 3.

The stride is a single jump, not a sequence of unit moves. The cells passed
OVER are not visited: their states are not read and not changed. Only the cell
at the arrival position is ever read or written.

Note the order carefully: the turn is decided by the state found on arrival,
the cell is then advanced, and the move happens last, using the NEW facing and
the stride set by the OLD state. A different order, or a unit stride, gives a
different automaton and answers a different question.

## 3. Highways

Fix a rule string. The trajectory is the infinite sequence of configurations
produced by iterating STEP from the initial configuration.

The automaton BUILDS A HIGHWAY if there exist a step index s, a period P >= 1,
and a displacement vector d != (0,0) such that for every j >= 0 the
configuration at step s + (j+1)P is exactly the configuration at step
s + jP translated by d, with the same facing.

Equivalently and more usefully for testing: from step s onward the automaton
repeats a fixed finite sequence of P moves that returns it to the same facing
having advanced by d, laying the same pattern in a strip that extends forever.

s is the TRANSIENT LENGTH. P is the HIGHWAY PERIOD. d is the HIGHWAY
DISPLACEMENT.

An automaton that does not build a highway may still be perfectly regular; not
building a highway is not the same as being chaotic, and you should not treat
the two as interchangeable.

## 4. Rules of evidence

- A trajectory claim is a claim about an infinite object. Running an automaton
  for a finite number of steps and observing no highway does NOT establish that
  no highway exists; it establishes only that none was found within that
  horizon. Say which of the two you have.
- Conversely, exhibiting s, P and d and verifying the translation property over
  many periods IS a proof that a highway exists, provided the verification is
  of the configuration, not merely of the position.
- A universal claim over rule strings is refuted outright by ONE rule string
  that violates it, provided the violation is established rather than observed
  at too short a horizon.
- Symmetry arguments are admissible and can be decisive. If a rule string's
  trajectory provably preserves a symmetry of the lattice that a highway would
  have to break, that is a proof of non-existence and is worth more than any
  amount of simulation.
