# The repair loop can oscillate forever between two invalid states

Notes for the operator. Diagnosed from `run-bc3e8797b3e0609eddb324299c8257bd`
(turmite ladder, glm-5.2, thinking off). Two fixes landed — the specific
instance and a general cycle detector — and two larger options remain open at
the end of this note.

## First, a correction

I initially recorded the completion-token sequence

    2735, 7151, 7150, 78, 38, 25, 67, 19, 32, 38

as the model "collapsing toward empty" under accumulating repair prompts, and
wrote that into RESULTS.md. **That was wrong.** The small responses are JSON
patches, which is exactly what `RepairPatchWireContract` requests; 19-78 tokens
is the right size for one. Nothing degraded. The raw blobs say so directly and
I should have read them before characterising the pattern.

## What actually happens

The model's `to_ref` values, in attempt order:

    attempt 1   "2469e57fb1b8d91d"   rejected: outside the SCR/NEW namespace
    attempt 2   "NEW_001"            rejected: self-link (from_ref is NEW_001)
    attempt 3   "2469e57fb1b8d91d"   rejected: namespace
    attempt 4   "NEW_001"            rejected: self-link  -> schema_exhausted

Two invalid states, alternating. The patches themselves are well formed and
correctly targeted — the model is doing exactly what it is asked, competently.

The reason it cannot escape is structural. That proposal declared exactly ONE
new block, `NEW_001`. A link's `to_ref` must be either a visible `SCR_###`
handle or a `NEW_###` key declared in the same response. With one block and no
visible scratch handles, **every possible value is invalid**: any other key is
undeclared, and the only declared key makes a self-link. The field is
unsatisfiable, and the sole correct repair is to REMOVE the link.

The model never tries that, and cannot be expected to. Each diagnostic reports
the violation of the state the document is currently in, so patching away the
violation it is told about lands it in the other one. Nothing in the repair
channel can express "no value works here; delete this element". It is not a
capability gap — the model used `remove` on `/simulation_proposals/1` in the
same run, so it knows the operation exists and when to reach for it.

## Cost

The run died at cycle 0 having already written a correct answer. The discarded
candidate says:

> CLAIM H is false. The rule string LR provides a structural refutation. Under
> the (c+1) stride, the rules {L, R} are exact inverses.

`oracle_table.txt` agrees. It also avoided the recall trap the question was
built around. All of that was thrown away over a self-referential scratch link.

## What is fixed

Self-links are now dropped deterministically at the scratch-proposal container
rather than refusing the turn. A self-link is inert — it adds no edge between
distinct blocks — so removing it cannot change what the graph says.

Two implementation notes worth keeping, because the obvious versions are wrong:

- **It cannot be a `mode="before"` validator.** The first attempt was, and it
  broke JSON-boundary coercion for the whole model: `ConjecturerTurnWireV6`
  validates via `model_validate_json`, and adding a before-validator made
  unrelated tuple fields (`new_blocks`, `unresolved_questions`) start rejecting
  JSON arrays. Eight tests caught it. It is a `mode="after"` validator on the
  container.
- **The link model can no longer RAISE.** A raise from a nested item aborts the
  whole model before any container validator runs, which is the behaviour being
  removed. The judgement stays on the link as `is_self_link`; the disposal
  lives on the container, which is the only place an element can be removed.

Ordering is checked: the drop runs before `_local_namespace_is_closed`, and a
self-link naming an undeclared key is dropped rather than becoming a route to
smuggle unknown keys past admission.

## The class, and what cycle detection does and does not do

Any repair diagnostic that is **locally satisfiable but globally
unsatisfiable** will loop until exhaustion. Self-links were one instance. The
general shape is: field F has a constraint set whose intersection is empty
given the rest of the document, and the protocol reports one member of that set
at a time.

Other places the same shape can arise, none of them investigated:

- a `premise_keys` entry that must name an EARLIER entry when no earlier entry
  of the right class exists;
- a ledger `claim_class` whose grounding channels are all bound to
  `maxItems: 0` (the satisfiability narrowing added in this tranche removes the
  advertised class, so this specific one should now be unreachable — untested
  in a live run);
- a `decisive_point_alias` when the alias table is empty.

## Fixed: cycle detection (records the loop; does not cut attempts short)

Implemented in `V6PatchRepairSession`. Every rejected candidate's canonical
form is digested; a repeated digest is recorded as an oscillation and leads the
exhaustion reason.

    attempt 0  outside namespace   rejected
    attempt 1  self-link           rejected
    attempt 2  outside namespace   rejected  <- repeat of attempt 0, recorded
    attempt 3  self-link           rejected
    attempt 4  outside namespace   rejected  -> exhausted, reason now reads:
      repair_oscillation: attempt 2 restored the candidate already rejected at
      attempt 0 while repairing /links/0/to_ref; the authorized value is likely
      unsatisfiable by patching; last error: ...

**A design correction, and the test that forced it.** My first implementation
STOPPED as soon as a state repeated, on the reasoning that the loop was proven.
That broke `test_doctor_two_ceiling_allows_second_required_repair`, which
scripts precisely the counterexample:

    attempt 0  {"finding":"supported","message":""}     rejected
    attempt 1  patch replaces /message with ""          same document, rejected
    attempt 2  patch removes /message                   VALID

A no-op patch reproduces the rejected document and the NEXT attempt succeeds.
So a repeated state is evidence of non-convergence, NOT proof of it — the model
is stochastic, and stopping would forfeit a granted repair that demonstrably
works. The test was right and the implementation was wrong; it was not
weakened.

What the loop actually costs is legibility, and that is what detection buys
back. Before, exhaustion recorded whichever validation error came last, leaving
the oscillation to be reconstructed from blobs — which is how this defect was
found, by hand, after the run had already died. Now the loop and its pointer
lead the recorded reason and the last error is kept after it.

The detection guesses nothing: the equality is exact, over the canonical form
of the whole candidate, so a repair converging through distinct states is never
flagged — a test pins that four different rejected values in a row do not trip
it.

## The two larger fixes, still not implemented

1. **Report the whole violation set, not one member.** If the diagnostic for
   attempt 2 had said "self-link AND the only alternative is undeclared", the
   model has enough to conclude the field is unsatisfiable. This is the smaller
   change and stays inside the existing protocol.
2. **Let a diagnostic mark a pointer unsatisfiable**, so the repair prompt can
   direct a `remove` explicitly. This is a protocol change to
   `RepairDiagnosticEnvelopeV2` and a larger commitment.

Both remain open. Cycle detection stops the bleeding — it makes the failure
immediate and legible instead of silent — but neither of these is subsumed by
it, because neither is about detecting the loop: they are about giving the
model enough information to avoid entering it. Of the two, (1) is the smaller
commitment and would likely have let this run finish.

---

## Unrelated, parked: two load-flaky MCP tests

Noticed while gating this change, not caused by it.

`tests/test_mcp_run.py` waits on the run thread with a hardcoded
`join(timeout=2)` at four sites (lines 222, 328, 350, 363). Under `pytest -n 4`
that budget is occasionally missed, and the two assertions that depend on the
thread having finished then fail:

    test_start_poll_result_and_progress_notifications
      assert status["state"] == "completed"   ->  'running'
    test_typed_v6_stop_can_continue_and_append
      run_result  ->  ValueError: RUN_RESULT_NOT_READY

Not caused by this tranche: both tests monkeypatch `run_scheduler` outright, so
neither the repair session nor the scratch proposal models are on their path.
They pass in isolation (7 passed), passed in the two preceding full gates, and
failed only in the one run — the signature of a wall-clock budget, not a logic
change.

The fix is to wait on the run's own terminal state rather than a fixed
two-second sleep-equivalent, or to raise the budget substantially. Left alone
here because it is outside this tranche and touching it would mix an unrelated
change into a gate that exists to verify something else.
