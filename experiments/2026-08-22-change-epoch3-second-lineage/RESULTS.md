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


---

## 2026-08-24 — attempt 4: the run survived to cycle 8, and the registered hypothesis FIRED

**What the record shows. SUCCESS by PREREG_EPOCH3.md §5**, on all three
required conditions and nothing softened:

    state             completed
    stop_reason       budget_exhausted        (the CYCLE budget bound, as predicted)
    cycles completed  8 of 8
    tokens            371 169 of 1 200 000    (31 percent)
    verify_root       0 violations            (violations: [])
    REPLAY_VALIDATION valid: true
    reach_set events  1                       (reach_nonzero_entries 1, zero entries 0)

This is the first live run of this configuration ever to reach a healthy
typed terminal. The four before it — reach-rich epochs 1 and 2, epoch-3
attempts 2 and 3 — died at or before cycle 2 on four unrelated typed
operational causes. Attempt 4 recorded none.

**The reach hit, in full, because it is the whole point of the tranche.**
One Measure event, `seq=1539`:

    reach_set  {dd15f0da59cbec86c1bf837221740c10f30b07808345087941bc627a7866a7ed: 1.0}
    addr+      [(dd15f0da59cb…, question-4dd62735b90864a75220e09b302500bc)]

Read it exactly: the `1.0` is a COUNT of full hits for that artifact, not a
coverage fraction (`reach.py:157`, `reach_counts[aid] = float(count)`). The
mechanism, re-derived from the record:

- The artifact `dd15f0da59cb…` was conjectured under school-2
  (`provenance role=conjecturer school=school-2 event_seq=1484`) and was
  ACCEPTED and addressed to `conn:0793267d0d4d` — a SPAWNED connection
  problem, not the seed.
- Its own battery is that problem's: `hv-floor@2a45b7988522`,
  `lineage-ref@41981e2f67d3`, `relation-form@578e42df713e`. None of the
  three subject predicates is in it, so all three are NOVEL to it —
  `reach_sweep`'s "at least one qualifying foreign criterion must be novel
  to its own battery" is satisfied three times over.
- The seed problem was FOREIGN to it (`pid not in addressed[aid]`), and the
  seed carries four criteria of which three are substantive:
  `uhi-energy-balance@v1`, `uhi-nocturnal-release@v1`,
  `uhi-cross-city-modulator@v1` (the fourth, `reasoning-envelope-wf`, is
  structural and never enters the qualifying set).
- All three qualifying criteria evaluated PASS. Coverage 3/4 = **0.75**,
  above the 0.5 floor, so this is a FULL hit rather than provisional, and
  the artifact now also addresses the seed.

That is the registered hypothesis, unmodified since the reach-rich tranche
registered it, firing live: *a run whose problems carry at least one
subject-substantive machine-evaluable criterion that the candidate
conjecturer is NOT instructed to satisfy will move pairs out of `E4` and
produce non-zero `reach_set` events.* The conjecturer working on
`conn:0793267d0d4d` was instructed to propose a substantive relation. It was
never instructed to satisfy the seed's energy-balance, nocturnal-release and
cross-city-modulator predicates. It satisfied all three anyway, and the
sweep found it.

**The carrier finally existed, which is what the previous four runs lacked.**
The committed `carrier_probe.py`, run unmodified on this root:

    accepted_artifacts                              190
    accepted_artifacts_addressed                     62
    artifacts_that_could_have_seed_as_foreign        15
    pairs_surviving_reach_novelty_gate_against_seed  15
    problems_total                                  210

Against the table this tranche has been keeping:

| run | died/ended at | accepted+addressed | with seed as foreign |
|---|---|---|---|
| reach-rich epoch 1 | cycle 2 | 14 | **0** |
| reach-rich epoch 2 | cycle 2 | 23 | **0** |
| epoch-3 attempt 2 | cycle 0 | 24 | **0** |
| epoch-3 attempt 3 | cycle 2 | 22 | **0** |
| **epoch-3 attempt 4** | **cycle 8, completed** | **62** | **15** |

Fifteen candidates, one full hit. The other fourteen sat at coverage 0.75
and failed the `all(PASS)` test on at least one predicate — visible in the
census as `_gate_coverage {"0.75": 15}` against a single `_full_hit_pairs`.

**The census, whole.** `pairs 12 957`, of which `E1 no-criteria 8 618`,
`E4 criterion-fail 3 235`, `E3 no-novel 1 104`, `A-skip/unaddr 128`,
`A-skip/status 26`. Criterion kinds reaching the verdict gate:
`substantive-predicate 73`, `structural:lineage_ref 46`,
`unknown-program:hv_floor 46`, `structural:reasoning-envelope-wf 1`.

**P1-reach holds, a fourth time.** `reasoning-envelope-wf` is recorded once
and classified `structural`, so `_substantive` excludes it from every
qualifying set and it vetoed nothing. **PRECONDITION-BLOCKED is absent.**

**Reporting the P5 rulings as required, not reinterpreting them.** No `E0`
empty-own-battery exit appears anywhere in the census — the vocabulary knows
the exit and recorded none. No reach event landed at coverage exactly 0.500:
the single hit is at 0.75, and the observed gate coverages are 0.33 (2 116
pairs), 0.75 (15) and 1.00 (1 104). Neither P5 signature occurred, which is
stated here because the ruling requires saying so either way.

**Attempt 4a: a qualification refusal that never became a run.** The first
launch was refused by the production-contract battery before cycle 0, on the
same pair that refused attempt 1 — `critic.atomic-target.v1` /
`argumentative_critic` seat 0, first draw 19/20 with one scope violation,
its single permitted redraw 18/20 with two more. The doctor failed closed as
designed (`doctor.py:41-48`: one fresh draw per failing pair, unqualified
after two consecutive failing blocks). The root carries no `log.jsonl` and
no `run-status.json`; it is retired as
`unqualified-attempt4a-run-bb045538…` with the rename committed first. The
relaunch (4b) qualified 80/80, zero scope violations, zero redraws. Six
batteries have now run this pair: two refused, four passed. Note for future
readers of the JSON: `pair_re_exercise_limit: 3` caps how many PAIRS may
redraw in a battery, not how many draws a pair gets.

**The budget prediction was right this time, and the burn estimate was
low.** PREREG AMENDMENT 2 registered ~55 000 tokens per completed cycle and
predicted the cycle budget would bind. Measured: 371 169 tokens over 8
cycles, ~46 000 per cycle — lower than the estimate, and the estimate's
direction (cycle budget binds, terminal is `budget_exhausted`, root stays
resumable) was correct on every point. AMENDMENT 1's prediction, by
contrast, was refuted; both are now scored.

**The root is amendable.** `stop reason is resumable: yes`, `stands at a
valid typed terminal: yes (terminal epoch 0)`, `amendment epochs: 0`. The
second problem lineage — R1, deferred since attempt 3 — can still be added
to THIS root by a follow-up tranche without minting anything new. Every
previous attempt ended unresumable, which is why R1 kept being deferred
permanently rather than postponed.

**Named as Rung 5's gate fixture**, per PREREG_EPOCH3.md §5's SUCCESS
clause: `experiments/2026-08-22-change-epoch3-second-lineage/run`, run id
`bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4`,
manifest sha256 identical, committed with its full record.

**Residue — what remains unproven, and it is not small.**

- **n=1 for the hit.** ONE reach event in 12 957 pairs. The hypothesis is
  now supported by a single live firing, not by a rate. Whether a rerun
  produces one, none, or ten is unknown, and capability/spawn behaviour is
  stochastic across identical runs by the record's own standing caution.
- **The 14 near-misses are not analysed here.** Fifteen artifacts could have
  had the seed as foreign; fourteen failed at least one predicate. Which
  predicate, and whether the failures share a cause, is not measured in this
  tranche.
- **The second lineage still has never existed in a live root.** SPEC.md M1
  remains proven only on an offline scratch copy. This run makes it
  reachable; it does not deliver it.
- **The run left typed work undone**, in non-authority channels that do not
  affect validity (`integrity` and `security` are both empty, which is why
  `verify_root` is clean): `completion` carries 86 findings — 80 of them
  `variator` phases (`hv-spot-check`, `premise-demarcation-variation`)
  DEFERRED with `transaction-contract-unavailable`, 5 conjecture work items
  abandoned `context_capability_not_granted`, and 1 outstanding completion
  debt — and `operational` carries 31, all repair/criticism work terminated
  `rejected` or `schema_exhausted`. A run can be replay-valid and still have
  left a role structurally idle. PARKED, not diagnosed here.
- **Whether cycle 2 was ever a real barrier is now answerable and not
  answered.** Four deaths at or before it came from four unrelated causes;
  this run passed it without incident once both were fixed. That is
  consistent with "two bugs, both now fixed" and does not by itself rule out
  a pressure that peaks there.

**Scope kept.** `git diff --stat origin/main -- src/ tests/` is empty. No
production code or test was touched at any point in this attempt, and the
other tranches' committed artifacts (`2026-08-22-live-reach-rich-run`,
`2026-08-21-measure-reach-firing`) are clean after their tooling was read.
