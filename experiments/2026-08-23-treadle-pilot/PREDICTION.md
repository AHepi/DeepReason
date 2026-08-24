# Pre-registration — pilot rung T4

Written and committed BEFORE T4 is run. `git log` order is the proof; if this
file's commit is not an ancestor of the T4 run's commit, the pre-registration
is void and T4's result must be reported as unregistered.

## What T4 asks

Whether one CLAUDE.md claim — "Per-capability budgets meter only their own
capability's records — the shared capability-state maps pool ALL capabilities'
proposals and work orders; always filter by type" — still holds of
`src/deepreason/capabilities/simulation.py`, and by what mechanism.

The correct answer, established by the monitor from the code before the run
and recorded here so the grading cannot drift:

1. Verdict: **HOLDS**.
2. The filter is `isinstance`, applied at **two** sites, not one:
   `isinstance(item, SimulationProposalV1)` over
   `capability_state.proposals`, and `isinstance(order,
   SimulationWorkOrderV1)` over `capability_state.work_orders`.
3. The request budget is checked by **ORDINAL** — the proposal's position in a
   deterministically sorted list (`ordered_requests.index(proposal) + 1`),
   compared against `maximum_simulation_requests`.
4. The execution budget is checked by **COUNT** — `sum(1 for order in ...)`,
   compared against `maximum_simulation_executions`.

Points 3 and 4 are the discriminating pair. They are adjacent in the same
function and read alike; distinguishing them requires reading what each
expression computes, and no instrument in this repository reports it. That is
the whole point of the rung: no command can be run to get this answer.

## The prediction (falsifiable, recorded before the evidence)

**T4 is where this lane breaks.** Specifically:

- **P-a.** The driver will not produce a first-attempt acceptance pass. The
  acceptance command requires all four facts above; the model is expected to
  return the verdict and the two type names — which are lexically present in
  the excerpt — and to get the ORDINAL/COUNT pair wrong, or to omit it.
- **P-b.** The failure mode will be **refine then escalate then BLOCKED**, in
  that order, exhausting `max_refinements = 2` and the one escalation to
  `deepseek-v4-pro:0813`, because the refinement prompt feeds back only the
  acceptance command's output, which says a grep failed — it does not say
  which reading was wrong. A judgment task gives the refinement loop nothing
  to converge on.
- **P-c.** The recorded worst case, and the one this pilot is watching for, is
  a **confident wrong PASS**: the model asserting HOLDS with a fluent
  justification that happens to satisfy every grep while the ORDINAL/COUNT
  reading is wrong. A clean BLOCKED is the system working. A wrong PASS is the
  finding, and would mean a deterministic acceptance command is not a
  sufficient acceptor for judgment work.

## How this is graded

On typed outcomes only: the board state for `PIL-SpecDriftJudgment`, the
acceptance command's exit code, the `.swarm/log.jsonl` events, and the
`.treadle/calls.jsonl` records. The model's prose is read only to classify
WHICH failure mode occurred, never as evidence that the answer was right.
