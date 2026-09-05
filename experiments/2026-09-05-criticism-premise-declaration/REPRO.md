# Reproduction

Form: in-memory (the diagnosis's falsifiable prediction), paired with the
form-2 regression artifact `dr-implement-fix` will commit — the existing
end-to-end trial scaffolding in
`tests/test_prose_refutation_boundaries.py::test_a_single_model_run_refutes_by_prose_end_to_end`
already drives `crit_argumentative` → `_argument_trial_steps` → a minted
ARGUMENTATIVE warrant against a mock critic/defender/judge set, so the
regression test reuses `_single_family_trial_adapter` rather than inventing
scaffolding.

Artifact: `experiments/2026-09-05-criticism-premise-declaration/repro_nu_evidence.py`

Current output (offline, no run root, no key):

```
$ python experiments/2026-09-05-criticism-premise-declaration/repro_nu_evidence.py
A  §0 DEPENDENCE, nu declares nothing   ('refuted', 'suspended_unsupported')
B  §0 EVIDENCE,   nu declares nothing   ('accepted', 'refuted')
C  DEPENDENCE, nu declares k EVIDENCE   ('accepted', 'refuted')

DIAGNOSIS CONFIRMED: one EVIDENCE ref on the validity node is the whole
difference. The mint site is the fix site; adjudication/ is not.
rc=0
```

Confirms diagnosis: yes — arm C changes exactly one thing against arm A (the
criticism's validity node declares the premise as `EVIDENCE`; the criticism's
own `DEPENDENCE` ref stays where §0 put it) and the target reinstates in the
same fixpoint pass. So the behaviour the goal asks for is already reachable
from the ontology, and what is missing is a producer at the mint site plus a
wire field to feed it. `adjudication/` needs no edit, which is what GOAL.md
required for the tranche to proceed.

What arm C does NOT show, stated so the fix is not over-credited: it changes
the graph by hand, not through a critic's declaration. It proves the closure
would fire; it does not prove any code path can be made to build that graph.
That is the regression test's job, not this script's.

Post-fix expectation:

- `repro_nu_evidence.py` keeps printing all three lines unchanged and exits 0.
  It is a statement about the ontology, not about the fix, so the fix must not
  move it. Arm A staying `('refuted', 'suspended_unsupported')` after the fix
  is CORRECT and required: a criticism that declares nothing keeps today's
  behaviour exactly (the formalism-optional law).
- The new artifact `s0_wire.py` — the same scenario driven through the wire,
  with the critic DECLARING the premise essential — prints `('accepted',
  'refuted')`, i.e. the EVIDENCE tuple, where today no wire input can reach it.
- `tests/test_criticism_premises.py` passes, and removing the ν-registration in
  the mint site turns it red (mutation proof recorded in VERIFY.md).

Production code untouched by this phase.
