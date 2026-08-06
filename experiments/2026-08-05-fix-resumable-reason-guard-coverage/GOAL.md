# Goal: give the resumable-reason guard a regression the gate runs, on a subject no committed root can supply
Class: regression-risk
Observed: `src/deepreason/workflow/lifecycle.py:273` refuses a
continuation whose terminal receipt names a reason outside
`RESUMABLE_STOP_REASONS`:

    if terminal.deterministic_decision.reason not in RESUMABLE_STOP_REASONS:
        raise ValueError("terminal stop reason does not authorize continuation")

**No test in the gate exercises it, and no committed root can.** The
census in
`experiments/2026-08-05-fix-continue-refusal-coverage/DIAGNOSIS.md`
partitions all 28 git-tracked roots carrying a `run-stop.json`:

    reason='budget_exhausted'     terminal receipt=yes   n=16
    reason='budget_exhausted'     terminal receipt=NO    n=7
    reason='operational_failure'  terminal receipt=NO    n=5

Every root that HOLDS a receipt stopped on `budget_exhausted`, which
`2d4ca2e1` made resumable. So the guard's subject — a receipt present,
its reason not resumable — exists nowhere in the record. Evidence:
`experiments/2026-08-05-fix-continue-refusal-coverage/PARKED.md` X1.

This is the mirror image of the gap W1 just closed, and the two are not
redundant. W1 guards `CONTINUE_TYPED_STOP_REQUIRED`
(`continuation.py:352`), reached when a run holds NEITHER a terminal
lifecycle decision NOR a resume decision. This guard is reached only
when a terminal decision EXISTS — the branch W1's witnesses never enter.
W1's own mutation work proved they are independent: widening
`RESUMABLE_STOP_REASONS` left every one of W1's five witnesses refusing
exactly as before, because on those roots the frozenset is never read.

Consequence, stated plainly: **narrowing `RESUMABLE_STOP_REASONS` today
— reverting owner decision 4a, say — breaks no test in the gate.**

Success criterion (machine-decidable):

    python -m pytest tests/ -q -n 4
    -> ends "0 failed" (3340 today) with at least one NEW test that
       reaches lifecycle.py:273 and asserts the refusal

    # mutation proofs, run before the test is committed, and the
    # ASSERTION THAT FIRES recorded for each -- W1 found two mutations
    # that looked interchangeable and were not
    narrow RESUMABLE_STOP_REASONS (drop "budget_exhausted") -> must FAIL
    neutralise the raise at lifecycle.py:273                -> must FAIL

    python tools/docs_verify.py
    -> "docs_verify: 0 failed"

In scope (3):
- `tests/test_v6_resumed_terminal_revalidation.py` — its
  `build_stopped_lifecycle` scaffolding already constructs typed STOPPED
  receipts, which is the one thing this subject needs and no committed
  root has. Whether the test lands here or in
  `tests/test_continuation.py` beside W1's is a `dr-propose-fix`
  decision, not a goal decision.
- `docs/map/SUB-application.md` — its Traps entry currently records that
  the refusal half is guarded and names what is not. If that changes,
  the entry moves in the same commit.
- The tranche directory.

NOT in scope: **`src/` — nothing.** The guard is correct; what is
missing is a witness. If constructing the subject appears to require a
product change, that is a finding to report, not a licence to make one.
Also not in scope: W1's own test — it guards a different branch and is
not to be extended, generalised or merged with this one. W2, W3, X2, X3
stay parked.

Budget: <=150 changed lines, 1 commit, ~2 hours.
Stop conditions inherited from orchestrator: yes — and per `132bdbb9`
the ceiling is compared against `git diff --stat` immediately before the
commit, not against the plan-time estimate. W1's estimate was low by
~30%; assume this one will be too.

## On the class, and on the approval it needs

`regression-risk`, for the same reason W1 was: nothing is broken, the
behaviour is correct, and what is absent is a guard. Recording it as
`defect` to unlock implementation would be a convenient
misclassification. The approval that class requires is the operator's
"Proceed with X1", against a parked entry that already states the goal,
the scaffolding and the mutation discipline.

## The specific trap this tranche must avoid

W1 could use record replay because its subject existed in the record.
This one cannot, so the test must CONSTRUCT its subject — and a
constructed subject is exactly where a test stops proving anything about
the product and starts proving that a fixture does what the fixture
says. The line to hold: the receipt must be built by the SAME production
helper that builds a real one (`build_stopped_lifecycle`), carrying a
reason the product itself can produce, and the refusal must come from
`prepare_continuation` — the public entry — rather than from calling the
guarded function directly. A test that hand-assembles a
`WorkflowLifecycleSnapshot` and calls `build_resumed_lifecycle` on it
would pass, and would not notice if `prepare_continuation` stopped
consulting the guard at all.

Which reason to use is a real question the diagnosis must answer from
the record rather than assume: it must be one the product can actually
record in a typed receipt, not an invented string.

## Map preflight (resolved ids)

- `DR-SUB-application` — `Owns: … src/deepreason/runtime/`, so it owns
  `continuation.py` and the `prepare_continuation` entry this test must
  drive. Its Traps section carries both halves of this story already.
- `DR-SUB-workflow` — owns `src/deepreason/workflow/`, so it owns
  `lifecycle.py` and therefore the guard itself and
  `RESUMABLE_STOP_REASONS`. **This is the document the Traps entry most
  likely belongs in**, and W1's went to `DR-SUB-application`; read both
  before deciding, and say why.
- `DR-SEAM-harness-x-workflow` — exists, and is the nearest documented
  seam to the lifecycle machinery. Read before either subsystem, per the
  ordering rule.
- `DR-INV-frozen-surfaces` — read. None of the five names
  `workflow/lifecycle.py`, but surface 2 (`harness.py` event application)
  is adjacent: a constructed receipt is APPLIED to a harness, and a
  fixture that writes a malformed one gets `WellFormednessError`, which
  per `CLAUDE.md` means the fixture is wrong, not the harness.

### Carried map findings, still open

`application × periphery` remains an unwritten seam absent from
`INDEX.md`'s matrix; `SUB-application.md`, `SUB-periphery.md` and
`SUB-amendment.md` are on disk but routable from no `INDEX.md` table.
Unchanged since the V1 preflight, still parked.
