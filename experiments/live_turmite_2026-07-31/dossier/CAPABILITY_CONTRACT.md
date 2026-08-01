# Capability contract for this run

This run grants operator-opted capabilities. Each has a typed proposal
channel, and work that only DESCRIBES using a capability in prose — without
filing the typed proposal — is unverified by construction. Prior recorded runs
left the simulation channel empty while describing simulations at length, and
the record's critics convicted every such candidate. File proposals; do not
narrate them.

This problem cannot be answered without them. The object under study is an
infinite trajectory of a machine defined by a formal grammar. There is no
closed form to manipulate: the only way to learn what a rule string does is to
parse it, implement the semantics exactly, and run it.

## Sandboxed simulation (simulation_mode sandboxed_python_v1)

Contained Python: scratch working directory, scrubbed environment, hard
resource limits, no network. Programs must be deterministic and
self-contained — the program text carries everything it needs, including the
rule strings under test and any candidate classifier. Integer arithmetic only.

The program's shape is fixed and the schema states it: the whole source is
exactly one `def simulate(inputs, rng)` and nothing else, and the mapping it
RETURNS is the only output that is recorded. Printing records nothing. Every
name in `requested_observables` must be a key of that returned mapping, or the
run fails with `declared observable missing`.

Fit for this challenge — in rough order of how decisive it is:

- **Refuting CLAIM H.** It is a universal claim over rule strings, so one
  established counterexample settles it. Enumerate the rule strings, run each
  to a long horizon, and RETURN the ones that show no highway together with
  the evidence that they do not — not a boolean.
- **Establishing a highway rather than observing one.** For a rule string you
  believe builds a highway, return the transient s, the period P, the
  displacement d, AND a verification that the CONFIGURATION at step s + (j+1)P
  equals the configuration at s + jP translated by d, over many j. Position
  alone is not the configuration and a position cycle is not a highway.
- **Checking your implementation against the specified order.** The semantics
  in the dossier fix an order of turn, advance, move. Before any trajectory
  output is used as evidence, return a short trace — the first several
  (position, facing, cell state) triples — from which the order can be read
  off directly, so a reader can confirm the machine is the specified one.
- **Testing a mechanism's prediction.** A claimed classifier for which rule
  strings build highways is refutable. Run it against the trajectory over rule
  strings it was not derived from and return the DISAGREEMENTS.
- **Symmetry as a decision procedure.** If a rule string's trajectory
  preserves a lattice symmetry, that can be measured: return the symmetry
  defect over time. A defect that stays zero to a long horizon is strong
  evidence for an invariant that a highway would have to break, and points at
  the structural argument that would actually settle it.

A simulation that cannot separate rival predictions is weight, not evidence.
Return the discriminating quantity itself — the rule string, the period, the
disagreement, the defect — never a boolean summarising it.

## Scratch workshop

The mechanism in requirement 3 is not going to arrive in one step. The scratch
channel is where a provisional mechanism is written down, linked to the
evidence that suggested it, and revised or abandoned when a simulation
contradicts it. Use it for the half-formed ones: "highways need an odd number
of net quarter-turns per colour cycle" is worth recording and killing, and the
record of a killed conjecture is worth more than silence about it.

Link scratch blocks to the simulations that bear on them. An unlinked block is
a note; a linked one is an argument.

## Directed research (frozen allowlist: en.wikipedia.org)

Where published results would settle a live disagreement, file typed research
proposals for specific https pages. Treat what is fetched as evidence about
what is PUBLISHED, not as established truth: a published claim about these
automata is exactly the kind of thing this run can test in the simulation
channel, and should be. A fetched claim that your own simulation contradicts
is a finding, not an error to be explained away.
