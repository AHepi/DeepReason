# Capability contract for this run

This run grants the operator-opted simulation capability. It has a typed
proposal channel, and work that only DESCRIBES running a simulation in
prose -- without filing the typed proposal -- is unverified by
construction. File the proposal; do not narrate it.

This problem cannot be answered without it: the exact face-count
distribution of a specific pseudorandom sequence has no closed form to
evaluate by hand at n=10000 terms. The only way to learn the actual
counts is to run the exact recurrence, in code, and tally the results.

## Sandboxed simulation (simulation_mode sandboxed_python_v1)

Contained Python: scratch working directory, scrubbed environment,
hard resource limits, no network. The program must be deterministic
and self-contained -- the program text carries everything it needs.
Integer arithmetic only.

The program's shape is fixed and the schema states it: the whole
source is exactly one `def simulate(inputs, rng)` and nothing else,
and the mapping it RETURNS is the only output that is recorded.
Printing records nothing. Every name in `requested_observables` must
be a literal top-level key of that returned mapping, or the run fails
with `declared observable missing` -- keep the observable set FLAT
(no nested structures) and each name a single identifier segment
(e.g. `count_1`, not `counts.one`).

Fit for this question, in order of how decisive it is:

- **Establishing the exact counts.** Implement the recurrence exactly
  as specified, run it for the full n, and RETURN the six face counts
  as flat observables (`count_1` .. `count_6`) plus `total`, not a
  prose description of what the counts "should" look like.
- **Calibrating the implementation before it is trusted as evidence.**
  Before any tally is used as evidence, return a short trace -- the
  first ten `(x_n, die_n)` pairs -- from which the recurrence and the
  face-mapping can be checked by hand against the specification.
- **Testing fairness as a decision procedure.** A claim that the
  generator is "fair" over this horizon is refutable by the actual
  counts falling outside the stated tolerance around the uniform
  expectation; return the counts and let the criticism cycle apply
  the tolerance, not a boolean verdict baked into the proposal.

A simulation that only asserts a verdict is weight, not evidence.
Return the discriminating quantity itself -- the six counts, the
calibration trace -- never a boolean summarizing them.
