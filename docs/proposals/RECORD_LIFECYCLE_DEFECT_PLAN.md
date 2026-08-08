# Defect program: the log — a run's record can end invalid, and the repair path can crash

Status: PROPOSED. Written 2026-08-08 by the monitor session on the
operator's instruction ("there's a big problem that needs fixing. The
log. Come up with the plan"), from Rung S6's live evidence
(`experiments/2026-08-08-live-two-seat-ab-s6/`, RESULTS.md failure
ledger and PARKED.md P1-P3). Each rung below routes through
`deepreason-orchestrator` (defect family) as its own tranche — one
tranche, one goal, offline reproduction before any fix.

## The problem, stated from the record

A live run that stops at its budget ceiling can leave its own
append-only record (`log.jsonl`) in a state `verify_root` judges
INVALID — and the tool that exists to repair that state can crash.
Rung S6 hit every part of this live:

1. **Invalid at the natural stop.** Both two-seat runs ended
   `budget_exhausted` with `replay_valid: false` — 9 `foreign-criticism`
   violations at 6 cycles, 15 at 10 cycles (run
   `run-6995cd12124d2697030bb4b9e48f79bd`, pre-continuation audit):
   accepted conjectures that never received their mandatory
   foreign-school criticism before the budget died. MORE budget made it
   WORSE (154 accepted artifacts vs 95), because the bound conjecturer
   (gemma4:31b) out-produced the critic (glm-5.2) every cycle. The
   single-model run (`run-79900e7847544b09bfb266518e2d8484`) was clean
   at its stop — the imbalance is throughput-ratio-dependent, which is
   why multi-seat runs (the future of this harness) will hit it MORE,
   not less.
2. **The repair path can crash.** `deepreason continue` — the intended
   remedy for exactly that debt — died 4 events in with
   `NonConjectureRecoveryAuthorityError("unknown critic task")` when
   the run had stopped mid-decomposition of a `schema_exhausted`
   criticism batch (PARKED P3, `workflow/nonconjecture_recovery.py:644`:
   the atomic-child payload routed through the batch-contract handler).
   The crashed root is committed as a reproduction fixture:
   `failed-epoch1-run-8c77c6588485304d1f73416318c62949`.
3. **Two adjacent identity defects** compound operator pain when
   re-running to work around 1-2: run identity omits seat bindings
   entirely (PARKED P2, `_request_digest`, preparation.py:249-265 — same
   question + different `--seat` collides with the earlier root), and
   the `coder` seat group's only role is unreachable from the public
   surface (PARKED P1, property-oracle bootstrap circularity,
   oracle.py:431/395).

Severity order: (2) makes recovery unreliable, (1) makes every
budget-limited multi-seat run end red until repaired, (3) are
identity-layer traps. The plan fixes in that order — the repair tool
first, because rung L2's own fix cannot be trusted until `continue` is.

## Rung L1 — `continue` must never crash on a resumable record  [FIX]

The defect: resuming a run stopped mid-decomposition of a criticism
batch crashes with a typed authority error instead of resuming or
refusing typed. Everything needed is already committed:
- GOAL: `deepreason continue` on the retired fixture root either
  resumes the in-flight decomposition correctly or refuses with a
  typed, actionable reason — never `state: "failed"` /
  `operational_failure`.
- DIAGNOSIS: PARKED P3's trace is the starting hypothesis
  (`_criticism_contract` asserts the batch schema
  `criticism.semantic-task.v1` against an atomic child's payload),
  to be CONFIRMED against the fixture's own `log.jsonl`/
  `run-result.json` before any code is read further — record first.
- REPRO: offline, free — copy the committed fixture root to a scratch
  home and run `continue` against it; the crash is deterministic from
  the frozen record. Then the minimal regression: a synthetic root
  stopped mid-decomposition (the S5-era mock-endpoint Scheduler
  pattern can build one without a provider).
- FIX shape (dr-propose-fix decides, not this plan): route each
  recovery item to the handler its OWN recorded schema names. Frozen
  surfaces: `workflow/` is not frozen; expect zero contact with the
  five frozen surfaces — any contact is a STOP for operator words.
- Accept: regression red-before/green-after on both the fixture and
  the synthetic root; full gate 0 failed net of the named P1/P3
  test-dependency failure; the fixture root itself stays byte-frozen
  (it is committed evidence — the REPRO copies it, never edits it).

## Rung L2 — a budget stop must not strand an invalid record  [DIAGNOSE, then DESIGN-AND-STOP]

The phenomenon: the scheduler keeps accepting new conjectures to the
end of the budget, so mandatory foreign-criticism coverage loses the
race exactly when the budget dies. Two genuinely different framings —
this rung MEASURES before choosing (the fork is real, so it is priced,
not assumed):

- (a) **Scheduling flaw**: as remaining budget approaches the cost of
  criticizing what is already accepted, criticism debt should outrank
  new conjecture — a landing pattern: stop taking on new obligations
  you can no longer afford to check. Fix lives in scheduler policy
  (budget-aware rank re-weighting or a terminal criticism-drain
  phase).
- (b) **Verdict-semantics flaw**: an artifact that has not met
  `minimum_foreign_school_coverage` should not be in an
  ACCEPTED-looking state at all when the run stops — the stop should
  leave it in a typed pending/uncriticized state that `verify_root`
  recognizes as VALID-but-open rather than a violation. Fix lives in
  state semantics and the verifier's reading — which touches frozen
  surface territory (replay-validation semantics) and old committed
  roots, so (b) is the expensive road and (a) is the presumptive one.

Measurement first (offline, free): across ALL committed roots, at each
root's final recorded state, compute accepted-artifact criticism
coverage vs stop reason — how common is invalid-at-stop today, does it
correlate with budget size, cycle count, model throughput ratio (S6's
two runs give the first two-seat data points). Then dr-propose-fix
prices (a) vs (b) with numbers, and STOPS for operator words —
scheduler selection policy is operator-approval territory by this
repo's own conventions (the seed-question rank invariant lives there).
- Accept for the eventual fix: a two-seat mock-endpoint run with a
  deliberately fast conjecturer and slow critic ends its budget with
  `replay_valid: true` and zero foreign-criticism violations at the
  NATURAL stop (no continuation needed); existing committed roots'
  verdicts unchanged (the 42-root sweep byte-identical — a fix that
  flips an old root is wrong by definition).

## Rung L3 — run identity must see seat bindings  [DESIGN-AND-STOP, frozen-adjacent]

The defect: `_request_digest` hashes question, budget, provider
profile, policy — not seat bindings. Two runs that differ ONLY in
`--seat` are epistemically different runs (a different model authors
the conjectures) yet collide on identity, refusing with
`PREPARATION_QUALIFICATION_BUNDLE_MISMATCH`. CLAUDE.md's own law says
"same question + config → same run id"; seat bindings ARE config, so
including them RESTORES the stated invariant rather than changing it.
But the touch is frozen-adjacent (preparation/replay record formats,
manifest schemas — surface territory), and the change must be
mint-forward only: committed roots keep the ids they minted; only runs
prepared AFTER the fix incorporate the seat-bindings digest. So:
SPEC-only first, with the exact digest-input change, blast radius over
every `_request_digest` consumer, and explicit operator words before
any code. The S6 work-around (vary the question text) remains the
documented operational road until then.
- Accept for the eventual fix: same question + different `--seat` →
  two distinct roots, no mismatch refusal; same question + same
  bindings → same id as before the fix for unbound configs
  (byte-identical digest inputs when no seat is bound — existing
  homes must not notice); full gate; sweep byte-identical.

## Rung L4 — decide the fate of the dead coder seat  [OPERATOR DECISION]

PARKED P1: `property_designer` (the `coder` group's sole role) can
never fire — the only code that mints its triggering property-oracle
commitment requires one to already exist. Not a code rung yet; a
decision with three priced roads: (a) wire a public mint path
(question/CLI surface gains a way to declare an executable property
oracle — real feature, real design work, makes the coder seat mean
something); (b) re-point the `coder` group at roles that exist on the
public path today (cheap, honest, but shrinks the seat vocabulary);
(c) document the group as experiment-only (cheapest, leaves a labeled
dead limb). Recommendation deferred to the measurement: L4 starts
with a half-day census of what the property-oracle machinery would
give a live run if it could fire (its adjudication pipeline is fully
built — crit_program, fuzz, relevance trials — all reachable only
from `lambda_run`). If the machinery is valuable, (a); if ornamental,
(b) with (c)'s documentation.

## Order, cost, and what this program does not touch

L1 (one tranche, fixture committed, offline repro — days not weeks) →
L2 measurement (offline, free) → L2 design STOP (operator words) →
L2 fix (one tranche) → L3 spec STOP (operator words) → L3 fix (one
tranche) → L4 decision (half-day census + one operator word). L1 and
the L2 measurement can run in parallel windows — different files,
different tranches. Nothing in this program touches the append-only
record's committed bytes: every fix is reader/scheduler/workflow-side,
every old root keeps its verdict, and the 42-root sweep is the
tripwire at every rung. The S6 tranche's three PARKED entries carry
the ready-to-send diagnosis pointers; this plan sequences them and
adds the acceptance bars.
