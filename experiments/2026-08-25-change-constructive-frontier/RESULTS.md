# RESULTS — P-C1, the first constructive-frontier run

Dated honest-ledger segments. Every number below comes from a typed
artifact or from `checker.py`'s exact-rational output (REQUEST.md R4).
"Accepted does not mean true" — and on this instance it does not even mean
good, which is the whole finding.

---

## 2026-08-25 — P-C1: the sampling baseline wins, decisively

**Headline: ARM S beat ARM H by a factor of 33 at matched budget.** This
is the outcome PREREG.md §5 registered as the honest prior, and it is
recorded as a real result rather than a failure.

| | ARM H (harness) | ARM S (blind sampling) |
|---|---|---|
| best valid score | **0.0004075** | **0.0135949364055** |
| exact | `163/400000` | `27189872811/2000000000000` |
| measured tokens | **702 789** | **709 454** |
| valid constructions | 15 | 23 |
| candidates / samples | 132 | 54 |
| terminal | `failed` / `operational_failure`, cycle 15 of 24 | ran to budget |

**Budget match: `T_S / T_H = 1.009`** — above PREREG §4's 0.95 floor, so
the comparison is ADMISSIBLE and the margin may be quoted.

**Margin: −0.0132 (ARM S ahead). PREREG §5's condition for the harness to
claim value — `best_H > best_S` — is NOT met.** The harness claims no value
on this instance. `milestones.json` records `harness_claims_value: false`.

### Scale of the gap, stated plainly

ARM S's third sample already scored 0.0136, at roughly **5% of the budget**.
ARM H spent its entire 702 789 tokens and never exceeded 0.0004075 — which
is below the best of 2000 *random uniform* draws (0.002824,
`instance_probe.out`). The harness's best construction was worse than
chance-with-2000-tries; the sampler's was 4.8× better than chance.

### What ARM S actually found

Its valid scores cluster hard:

    0.0135949364055   <- best
    0.013307751281
    0.013307723273
    0.0133077088625
    0.013307680842    <- the regular 13-gon, hit four times exactly

`0.013307680842` is the plain circle of 13 that `instance_probe.py`
computed before either arm ran. One-shot glm-5.2 finds the regular 13-gon
**reliably**, and occasionally nudges it a little better. That is the
baseline's whole strategy, and on this instance it is a good one.

### Milestones (PREREG §6)

- **M1 — MET.** Both arms produced valid checker-confirmed constructions
  (ARM H 15, ARM S 23). The REQUIRED clause is that ARM H produced at least
  one; it did.
- **M2 — MET, and this is the interesting number.** ARM H's criticism did
  **117 checker-refutations**: 114 `CLAIM_INFLATED`, 3 `WRONG_COUNT`. A
  further **15 valid constructions fell below the registered 0.005 floor**.
  So of 132 attempted constructions, **every single one was refuted** —
  117 for breaking the rules or overclaiming, 15 for obeying the rules and
  losing. Criticism did countable work; it just never produced a survivor
  worth having.
- **M3 — REPORTED, NOT SCORED** (R24c). Vocabulary across ARM H's 15 valid
  candidates: `avoid-collinearity` 15, `perturbed-lattice` 11,
  `rings-or-shells` 6, `boundary-loading` 4, `golden-or-irrational` 1,
  and **zero** mentions of `greedy-or-local`, `symmetry-breaking`, or
  `min-triangle-targeting`. Read carefully: the run named the TRAP
  (collinearity, in every valid candidate) and never named a SEARCH
  (nothing about targeting the binding triple, nothing about local
  refinement). It diagnosed the problem and did not attack it. No threshold
  attaches to this; it is reported because it is the most legible thing the
  record says about what "imagination" looked like here.

### The claim-inflation finding

**114 of 132 constructions overclaimed their own score.** The model states
a configuration and a number, and the number is usually wrong — not
marginally, but in a way an exact checker catches immediately. This is
independent of which arm ran and is the single most reproducible behaviour
in the tranche: the same pattern appears in the void run (147 of 183). A
model asked to construct AND to score its construction is reliably
competent at the first and unreliable at the second.

### ARM H's typed failure

`state: failed`, `stop_reason: operational_failure` at cycle 15 of 24.
Message: `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
/workflow/insufficient_capability_by_route_seat` — "route seat has
terminally exhausted its smallest authorized contract". The run committed a
terminal (`terminal_committed`, seq 3199) and **`verify_root` reports 0
violations**, so the record is well-formed and the failure is typed, not a
crash. 0 judge calls, as designed.

**Does the early stop explain the gap? No, and the record says why.** ARM H
reached 0.0004075 by cycle 10 and did not improve for the remaining five
cycles. It also spent its whole matched budget — the stop was a seat
exhaustion, not a budget exhaustion, and ARM S was matched against the
tokens ARM H actually burned, not against a fuller run it did not have. A
9-cycle continuation would have to have improved by 33× to change the
verdict, having improved by 0× over the previous five. The honest statement
is therefore: **the margin is not an artifact of the early stop**, but ARM
H did not complete its registered 24 cycles, and a completed run remains
unmeasured.

### What this does and does not settle

**It does settle**, on our own machine, at matched measured budget, on this
instance: conjecture–criticism with an exact demonstrative checker lost to
blind repeated sampling scored by that same checker, by 33×. This is a
direct instance of `RESEARCH_FINDINGS` Q4's pre-registered law — "at matched
budget, criticism loses to resampling wherever a counting baseline exists" —
reproduced here with a checker standing in for the counting baseline. Q4's
scope limit said that baseline normally does not exist for open-ended work;
this tranche shows that when you CAN build one, it wins.

**It does not settle**: anything about other instances, other N, other
models, or other problem families. One instance, one model, one run per arm.
There is **no repeat** — PREREG §7 pre-authorized one, and it was not spent
(see Residue). Per R25 the comparison is therefore quoted as a single-run
margin, **with both arms' spread stated**:

| | spread of VALID scores |
|---|---|
| ARM S (23 valid) | 0.000125 – 0.0135949364055 |
| ARM H (15 valid) | 0.0 – 0.0004075 — and **fourteen of the fifteen are exactly 0.0** |

Two things follow, and the second is the one that matters.

**The distributions overlap at the bottom, not the top.** ARM S's worst
valid sample (0.000125) is BELOW ARM H's best (0.0004075) — sampling
produces duds too. But **22 of ARM S's 23 valid samples are strictly above
everything ARM H produced in its entire run.**

**ARM H produced exactly one non-degenerate construction in 132 attempts.**
Fourteen of its fifteen valid constructions scored 0.0 — collinear, i.e.
they obeyed every rule and were worth nothing. The single exception is the
0.0004075 quoted as its best. So the honest characterisation of ARM H is
not "it scored lower"; it is that it essentially never escaped the
collinearity trap at all, while the sampler escaped it in most samples.

### Residue — what remains unproven

1. **No repeat was run.** PREREG §7 authorized one. The session's budget
   went to a void run and four qualification batteries instead. The margin
   is one run per arm, and R23's "sustained on the one pre-authorized
   repeat" is therefore UNTESTED. Since the harness is not claiming value,
   the repeat would only test whether the LOSS is stable — worth doing, and
   not done.
2. **ARM H never completed 24 cycles.** Argued above to be non-decisive;
   not proven so.
3. **A whole run was voided by my own defect.** The first launch reached
   cycle 11 with an inert battery (anchored regexes against a JSON
   envelope). It is retained at `void-inert-battery-run-6913328037a61ca6/`
   and is never quoted as an ARM H result. It is unintentionally a third
   condition — the harness WITHOUT checker feedback — and it scored
   **0.0 best, 183 candidates, 147 inflated claims**. Compared against
   ARM H's 0.0004075 WITH feedback, the checker signal moved the harness
   from 0 to 0.0004: real, and still 33× short of doing nothing clever.
4. **Qualification on this configuration is intermittently red**, always at
   the same contract. Parked as P1; five batteries ran fail/void/pass/fail/
   pass. The run that produced these numbers qualified on a retry, and a
   green obtained on a retry is not the same fact as a green obtained
   first time.
5. **The run's own token counter read zero.** `deepreason results` printed
   `tokens spent vs budget: 0 / 3000000` after 292 provider calls. Every
   token figure here is summed from the log's `llm` blocks instead. Parked
   as P2 — if that counter is what a budget stop consults, a run could
   never stop on budget.
6. **Survivor counts are unusable here, in a new way.** Both the raw and
   the conjecture-only figures came back **0**, because the run failed
   before writing a survivor record (`NO_SURVIVOR_RECORD`). R31's
   instruction to quote conjecture-only figures is honoured vacuously: there
   were no figures to quote. This is not the P4 inflation defect; it is a
   different absence, and it means this run says nothing about survivors.
7. **"Accepted" was cheap.** The run recorded 909 accepted artifacts and
   163 refuted while every one of its 132 actual constructions failed the
   checker. Acceptance in this harness is survival of the criticism that
   happened to be generated — it is not, and here demonstrably is not, a
   statement that the artifact is any good.

---

## Program status

    P-C1  construction  RUN. Typed terminal, verify_root clean. ARM S beat
                        ARM H 0.0136 vs 0.0004 at matched budget (1.009).
                        The harness claims NO value on this instance.
                        Repeat: NOT RUN.
