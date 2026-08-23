# RESULTS — epoch 3: a second problem lineage

Honest ledger. Each segment says what the record shows and what remains
unproven. "Accepted does not mean true."

---

## 2026-08-23 — attempt 1: qualification refused, one scope violation in 100 cases

**What the record shows.** The operator's credential works. The
production-contract battery executed 80 cases plus a 20-case redraw and
returned `qualified: false` — but not for any reason touching
authentication, the endpoint, or the model's competence at the run's work.
Three of four route/contract pairs qualified outright, 20/20 first pass.

The fourth, `critic.atomic-target.v1` / `argumentative_critic` seat 0:

    first draw   15/20 valid, 5 cases REPAIR_SCOPE_VIOLATION
    redraw       19/20 valid, 1 case VALIDATION_ERROR, scope_violations 1
    qualified    false

`qualification.py::_pair_report` requires `scope_violations == 0` with no
tolerance, so one repair patch aimed outside its authorized pointer failed
the pair even though `eventual_valid` (19) met its own minimum (19). The
doctor allows ONE fresh twenty-case draw per failing pair
(`cli/doctor.py:1210-1226`); it was spent.

**Stochastic, established rather than inferred.** The reach-rich tranche
qualified the SAME four pairs on the SAME route and model 80/80 — and it,
too, had to redraw `critic.atomic-target.v1`. Same pair both times. There
the redraw came back clean; here it came back one case short. Attempt 2 then
passed that pair 20/20 on the FIRST draw with no redraw anywhere in the
battery, which closes the question: draw-to-draw variance in a known-flaky
pair, not an incompatibility.

**No cache was poisoned.** A failed battery writes only a sidecar
`.unqualified-doctor.json`; `write_completed_qualification` runs on success
alone. This tranche's `DEEPREASON_HOME` held no files at all, so attempt 2
re-executed every case.

Attempt 1 is retired by rename with the rename committed first. Nothing in
it is a run root: no `log.jsonl`, no `run-status.json` — it died at
qualification, before a single cycle.

**Correction to a claim made in-session.** Qualification here was described
as taking "roughly 14 minutes". That is CLAUDE.md's figure for the full
battery (~1160 calls). The production-contract doctor this ladder runs is 4
pairs x 20 cases = 80 calls: attempt 1 took 72s (100 calls with the redraw),
attempt 2 took 55s. A fast return is normal and is not a cache hit.

---

## 2026-08-23 — attempt 2: qualified clean, then died at cycle 0 on a budget the tranche itself set too low

**What the record shows.** Qualification passed 80/80, no redraws, zero
scope violations. Phase 1 then ran for eight minutes and terminated typed at
**cycle 0**:

    state            failed
    stop_reason      operational_failure
    error_type       WorkBudgetDenied
    message          token budget denied transactional work sha256:32af1d16...
    cycles completed 0 of 12
    verify_root      0 violations
    reach_set events 0

`verify_root` reporting **0 violations** is a real positive: the record this
run wrote is replay-valid, on a root whose seed problem carries
operator-authored `predicate:` criteria and whose manifest enables attached
evidence — a manifest shape no committed root had before.

**The cause, measured, and it is this tranche's own doing.** Not P7-reach
(seat exhaustion) and not P9-reach (the route-lease `max_tokens`
disagreement); both fixes held. The arithmetic:

    logged LLM calls           56
    logged tokens             165 466
    phase-1 token budget      200 000
    headroom remaining         34 534
    next reservation needed   ~35 700   (32 768 completion bound + ~2 900 prompt bound)

`workflow/transaction_service.py::reserve_dispatch` books the FULL completion
cap up front for each call. The 57th work item's reservation did not fit in
the remaining 34 534 tokens, `meter.reserve` raised `TokenBudgetExceeded`,
and the service wrote a `budget_denied` terminal
(`reason_code: token_budget_denied`, `status: budget_denied`, prompt and
completion tokens 0 — the call never went out).

The phase-1 budget of 200 000 is not the reach-rich design's. That design
carried 400 000. This tranche SPLIT it 200 000 + 200 000 across two phases
to honour the operator's instruction that "PREREG's bound stands", and
recorded the split in PREREG_EPOCH3.md §4 as a deliberate choice. The split
is the cause. Owning it plainly: the frozen design was sound about WHAT to
run and wrong about how much fuel one phase needs.

**The deeper consequence, and why re-splitting is not obviously the fix.**
Phase 2 can only run if phase 1 reaches a stop reason in
`RESUMABLE_STOP_REASONS = {converged, budget_exhausted}`. Exhausting the
token budget does NOT produce `budget_exhausted`: the remainder eventually
becomes smaller than one reservation, and that is `WorkBudgetDenied` —
`operational_failure`, unresumable. A token-bounded run therefore reaches a
resumable terminal only by exhausting its CYCLES first (or converging). At
165 466 tokens for a partial cycle 0, twelve cycles are on the order of
1-2 million tokens, several times the whole frozen bound. The ladder's own
guard behaved correctly and said so:

    AMEND SKIPPED: stop_reason 'operational_failure' does not authorize
    continuation (workflow/lifecycle.py:28) -- phase 2 cannot run

Parked as P5-epoch3; it is a finding about the budget/lifecycle seam, not a
reach defect.

**Typed outcome under PREREG_EPOCH3.md §5: TRUNCATED-BEFORE-CARRIER.** The
census is unambiguous that the hypothesis was never exercised:

    problems_total            1
    artifacts_total          59      artifacts_candidate 21
    addr_pairs               24
    A-skip/unaddr            35      A-skip/status 3
    _full_hit_pairs           0      reach_set events 0
    _crit_kinds   structural:reasoning-envelope-wf 1, substantive-predicate 3

**One problem existed.** `reach_sweep` needs an artifact and a FOREIGN
problem; the run died inside cycle 0, before the connection/integration
cascade spawned a single one. Zero reach here is not a measurement of the
hypothesis — there was nothing to measure it against. This is exactly the
label PREREG_EPOCH3.md §3/§5 registered IN ADVANCE so it would not have to
be invented after the fact, as the reach-rich tranche had to.

**P1-reach continues to hold live.** `reasoning-envelope-wf` is recorded
once, classified `structural`. It entered no qualifying set and vetoed no
pair, so the PRECONDITION-BLOCKED signature is absent again.

**Nothing falls under the P5 rulings.** With zero reach events, no event
involved an artifact with an empty own battery (`E0`) and none landed at
coverage exactly 0.500. `_gate_coverage` and `_qualifying_vocab` are both
empty. Reported as required, not reinterpreted.

**Residue — what remains unproven.**

- **The registered hypothesis is still untested**, exactly as it was before
  the reach-rich tranche and after it. No live run has yet produced an
  accepted artifact addressed to a problem other than the seed's.
- **The second lineage has never existed in a live root.** The amendment was
  correctly skipped, so nothing here tests SPEC.md M1 live; M1's evidence
  remains the offline scratch-copy measurement.
- **Whether 12 cycles are reachable at any budget is unknown.** One partial
  cycle cost 165 466 tokens with the repair path active. Whether that rate
  holds, falls, or rises across later cycles is not established by n=1.
- **The pre-authorised repeat was NOT spent.** A repeat under the same
  budget would fail the same arithmetic; PREREG's repeat exists for
  stochastic misses, and this is deterministic. Spending it blind would burn
  the tranche's one retry on a known outcome. The decision returns to the
  operator with the numbers.

**Scope kept.** `git diff --stat origin/main -- src/ tests/` is empty. No
production code or test was touched at any point in this tranche.

---

## 2026-08-23 — attempt 3: one phase, 400 000 tokens; a THIRD distinct operational death, and the registered prediction refuted

**What the record shows.** Qualification passed 80/80 with no redraw. The
single reasoning phase (R17: `cycles=4 --token-budget 400000`) ran nine
minutes and terminated typed at cycle 2 of 4:

    state            failed
    stop_reason      operational_failure
    error_type       WorkflowAuthorizationError
    message          transactional reservation bound differs from rendered request
    cycles completed 2 of 4
    verify_root      0 violations
    reach_set events 0

**The registered prediction is REFUTED, and it was mine.** PREREG AMENDMENT
1 predicted the token budget would bind first, around cycle 2, producing
`WorkBudgetDenied`. It did not. The run died with **290 025 of 400 000
tokens unspent** (49 calls, 109 975 logged) on a completely different cause.
Recording that plainly: the forecast was registered before launch precisely
so it could be scored, and it was wrong.

**The new cause, narrowed by measurement and NOT fully resolved.**
`llm/adapter.py:1187` re-computes the reservation bound at dispatch as
`conservative_prompt_bound(request) + transport_limits["max_tokens"]` and
refuses if it differs from the amount the transaction service already
booked. Two candidate explanations were eliminated against the record:

- **Not a controller cap re-tune** (the E43 shape). No policy artifact with
  a `knobs`/`cap:` entry exists anywhere in the log, and `max_tokens` appears
  as `32768` and nothing else across every object in the root. All 50
  reservations booked `completion_bound_tokens 32768`.
- **Not prompt drift between reserve and authorize.** Every one of the 50
  dispatch authorizations resolves to its reservation, and
  `prompt_sha256` agrees in **50 of 50** pairs.

What remains is the prompt-bound term computed over two different strings:
the transaction service bounds its `prompt`, the adapter bounds its rendered
`request`. **The record cannot settle it**, and that is itself a finding: the
adapter's rendered request bytes are never stored, only a hash of the
service's prompt, so the two quantities the guard compares cannot both be
recovered afterwards. Parked as P6-epoch3 with that gap named.

**Typed outcome under PREREG_EPOCH3.md §5: TRUNCATED-BEFORE-CARRIER, for the
third time.** Attempt 3 got materially further than attempt 2 — 95 problems
instead of 1, and `reach_sweep` actually evaluated 2 068 pairs (1 584 `E1
no-criteria`, 484 `E4 criterion-fail`, every qualifying pair at coverage
0.33). But the committed `carrier_probe.py` settles whose criteria sat on the
foreign side:

    accepted_artifacts                          55
    accepted_artifacts_addressed                22
    artifacts_that_could_have_seed_as_foreign    0
    pairs_surviving_reach_novelty_gate_against_seed  []
    problems_total                              95

**All 22 accepted, addressed artifacts address the seed problem itself.**
`reach_sweep` skips a problem an artifact already addresses, so the seed was
never on the foreign side of any pair. The 484 `E4` pairs qualified on
`relation-form` alone at coverage 0.33 — the P2-reach form gate, capped below
`REACH_COVERAGE_MIN` and provisional at best. The hypothesis was not tested.

**The pattern across four live runs, which is now the real result.**

| run | died at | accepted+addressed | with seed as foreign |
|---|---|---|---|
| reach-rich epoch 1 | cycle 2 | 14 | **0** |
| reach-rich epoch 2 | cycle 2 | 23 | **0** |
| epoch-3 attempt 2 | cycle 0 | 24 | **0** |
| epoch-3 attempt 3 | cycle 2 | 22 | **0** |

Four runs, four DIFFERENT typed operational causes
(`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`, `ROUTE_LEASE_MISMATCH`,
`WorkBudgetDenied`, `WorkflowAuthorizationError`), and not one has put an
accepted artifact on a spawned problem. Against SPEC.md M9 — a committed
single-seed root that reached **cycle 8** carries 186 such artifacts — the
carrier appears somewhere between cycle 2 and cycle 8, and no run of this
configuration has ever survived past cycle 2.

**P1-reach still holds.** `reasoning-envelope-wf` recorded once, classified
`structural`, vetoing nothing. **Nothing falls under the P5 rulings**: no
`E0` empty-battery event and no pair at coverage exactly 0.500 — the only
coverage observed is 0.33. Reported as required, not reinterpreted.

**verify_root: 0 violations**, a third time, on a root carrying
operator-authored `predicate:` criteria and an attached-evidence manifest.

**Residue.**

- **The hypothesis remains untested after three attempts and four runs.**
- **The pre-authorised repeat is now SPENT.** PREREG_EPOCH3.md §5 authorised
  one; attempts 2 and 3 are it. Under R11 the tranche STOPS here and the
  decision returns to the operator.
- **Whether cycle 2 is a coincidence is unknown.** Four deaths at or before
  cycle 2 from four unrelated causes is either bad luck or a pressure that
  peaks there; n=4 with distinct causes does not separate those.
- **The second lineage has still never existed in a live root.**

**Scope kept.** `git diff --stat origin/main -- src/ tests/` is empty.
