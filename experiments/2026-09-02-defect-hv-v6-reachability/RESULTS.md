# hv v6 reachability — results

Dated, honest-ledger segments. What the record shows, and the residue — what
remains unproven. Accepted does not mean true.

---

## 2026-09-02 · Segment 1 — the defect is on `main`, and it is larger than the brief said

**What the record shows.** The tranche was commissioned on evidence from three
roots, two of which live on another branch. It did not need them. `main` alone
carries the whole contradiction, and joining two files of one root is the whole
reproduction.

Census over every committed v6 run root, read-only
(`repro_record.py`): **50 roots, 56 501 log events, 2 661 `hv` deferral records,
0 `hv_set` measurements.** No v6 root in this repository has ever measured `hv`.
The only roots that carry an `hv_set` event at all have `schema_version` 1 or 2.

The decisive row is `experiments/2026-08-12-live-grounded-extension-expansion/run`
— grounded-extension run `8e22d0431fd2b98d`:

| | |
|---|---|
| state / stop_reason | `completed` / `budget_exhausted` — not an early death |
| `criticism_policy.authority` | `defended_trial` |
| `variator[0]` behavioural grant | `['variator.direct.v1']` — **the exact contract the gate stands in for** |
| `hv` deferral records | **336** (`hv-spot-check` 241, `hv-floor` 95) |
| `hv_set` events | **0** |

Grant present, gate closed anyway. The other 46 deferring roots hold no grant,
and their deferrals are CORRECT — they are the control, and the fix leaves them
untouched.

**The mechanism, read only after the record named it.**
`Scheduler._defer_untransactional_v6_phase` (`scheduler.py:696-752`) computed
its whole answer from `manifest.schema_version != 6` and then returned `True`
unconditionally. Its only other branch was `schema_version != 6`, which
operations parity (2026-08-13, one run path) forecloses. Eleven optional model
phases sat behind it with run-config knobs — `HV_K`, `HV_MIN`, `AUDIT_PERIOD`,
`GEN_*`, `PROP_*`, `VISION_CRIT_PER_CYCLE`, `ADVISORY_TRIALS_PER_CYCLE` — that
parse, compile and appear in the manifest over behaviour that cannot fire.

**Two corrections to the commissioning brief, both measured.** *Eleven* call
sites, not twelve — the twelfth `grep` hit is the `def`. And *eleven* phases,
not twelve: `premise-rent` is the `target_ref` at `scheduler.py:2582-2585`, not
a phase name. The record settles the second independently of the code, because
the deferral marker's own `inputs` tuple is
`[marker, phase, role, target_ref, obligation_ref, reason]` and `premise-rent`
sits in the fourth slot. Both the 2026-09-01 P-A1 write-up and this tranche's
own instruction carried the twelve-name list; `docs/ERRATA.md` E68 records it so
the count is not carried forward again.

**One correction to this tranche's own first artifact.** GOAL.md and the first
draft of DIAGNOSIS.md said P-R1 carries 5 414 log events. It carries **2 707**
(`wc -l`). The error was a census script summing a `Counter` that held two keys
per event. Corrected in place, with the amendment recorded; every other figure
came from later scripts and reproduces. `repro_record.py`, written independently,
printed 2707 for that root from the start.

**Residue.** A deferral RECORD is not a deferral CALL — the marker deduplicates
by `(phase, role, target_ref, obligation_ref)`, so 2 661 under-states the
requests and the true rate is not recoverable from the record. The direction is
safe (the defect is at least as large as stated), but no number here is a call
count.

---

## 2026-09-02 · Segment 2 — the fix, and the two things that make it not obvious

**What shipped.** `workflow/legacy_phase_contracts.py` declares a VERSIONED
table of phase → (role, authorizing contracts, dispatch); the gate consults it
before recording debt and returns `False` when the seat holds a listed contract.
`measures/hv.py` self-detects the bound manifest and routes its variator call
through `informal/trial.py`'s existing v6 bracket, generalised by three keyword
parameters rather than copied. `hv-spot-check` is converted here, and
`hv-floor` after the operator ruling in Segment 5; the other nine rows are not.

**The deferral branch is byte-identical.** Same marker string, same six-element
`inputs`, same `transaction-contract-unavailable` reason, same dedup set. A
grant-less run's log after the fix is the log it would have written before. That
is the property the 46 control roots demand, and it is asserted element by
element rather than as a set.

**Two design points the code cannot show, and both were proven by mutation
rather than argued.**

*The `dispatch` field, not the grant, is what converts a phase.* Nine rows have
no dispatch written. Opening the gate on the grant alone would send them to a
provider unbound and trip the fail-closed adapter guard the gate exists to
respect — turning a silent inertness into a killed root. Mutation M8 (revert
hv's dispatch, leave the gate open) raises exactly
`WorkflowAuthorizationError: RunManifest v6 provider dispatch requires a bound
transaction`. The gate's original author was right; only its decision was wrong.

*`llm_call` is `None` under v6 because the transaction is the accounting.*
`Harness.record_llm_calls`'s own docstring states the rule — every call reaches
the log exactly once, or replay and `eval_report` silently under-count. Mutation
M9 (re-attach the call) raises `WellFormednessError: transactional provider call
lacks live issued authority`. Returning `None` makes all five downstream record
sites correct with no edit to any of them.

**Frozen surfaces: CLEAR, measured not asserted.**
`python tools/blast_radius.py --files …` returns
`"frozen_surface_contacts": []`, `"frozen_adjacent_contacts": []`,
`"qualification_digest": []`, `"wheel_smoke_pins": []`,
`"frozen_surface_verdict": "CLEAR"`. No new contract id (both variator
contracts already exist and are already granted), no new work kind
(`informal/trial.py` already dispatches the identical variator call under
`DEFENDED_TRIAL_STEP`), no battery change (the fix reads the plan and grants
nothing).

The writer-side alternative — widening the grant compiler so v6 runs get the
variator grant by default — is closed on its own evidence, and this is worth
recording because it was the more obvious road: the behavioural plan is
RE-DERIVED and compared on every manifest reload
(`run_manifest.py:1595-1604`, raising
`V6_ROUTE_SEAT_BEHAVIORAL_CAPABILITY_PLAN_MISMATCH`), so a compiler change would
invalidate every committed v6 root on load. Reader-side is not merely preferred
here; it is the only road that does not break the corpus.

---

## 2026-09-02 · Segment 3 — the soak is green and cannot see the thing it was asked to see

**What the record shows.** Two soaks, differing in exactly three config lines,
both clean:

| | grant-bearing (`--case hv-grant`) | control (`--case reach-rich`) |
|---|---|---|
| terminal | `completed` / `budget_exhausted` | `completed` / `budget_exhausted` |
| cycles | 8 of 8 | 8 of 8 |
| `verify_root` | 0 violations | 0 violations |
| `hv_set` events | 0 | 0 |
| deferral records | 1 (`premise-demarcation-variation`) | 1 (`premise-demarcation-variation`) |
| ACCEPTED artifacts | 15 | 15 |
| `state.addr` pairs | 1 | 1 |
| ACCEPTED **and** addressed | **0** | **0** |

That last row is the finding. `_lazy_hv` requires an artifact that is both
`ACCEPTED` **and** present in `state.addr` (`scheduler.py:2942-2949`), and an
8-cycle single-problem stub run produces none: `addr` holds one pair, the seed's
own. P-R1, by contrast, carries 435 ACCEPTED artifacts, 186 `addr` pairs and 82
that are both — which is why P-R1 recorded 74 `hv-spot-check` deferrals and the
soak records none. **The soak never reaches the gate, so it cannot discriminate
on `hv` in either direction.**

**What the soaks DO prove, and it is not nothing.** The grant-bearing shape —
the one no committed soak case could previously express, because
`run_manifest.py:2059-2065` mints the variator grant only under a
`defended_trial` criticism policy and all five committed cases lack one — drives
eight clean cycles to a typed terminal with a clean `verify_root`, identically
to its control. No regression. And the one deferral both runs record is
`premise-demarcation-variation`, an UNCONVERTED row, deferring identically with
and without the grant: a recorded control for the nine-phase safety property
that no unit test could supply.

**What proves the dispatch instead.**
`tests/test_hv_v6_reachability.py::test_hv_measures_end_to_end_through_a_real_v6_transaction`
drives a real `Harness` and a real `InquiryTransactionService`: the granted seat
opens the gate, the variator call goes out under contract `variator.direct.v1`
and work kind `DEFENDED_TRIAL_STEP` with payload schema `hv-variation-step.v1`,
exactly one `hv_set` event lands in the log, and that event's `llm` is `None`.
Reverting either half of the fix breaks it (mutations M7, M8, M9).

**Honest correction to GOAL.md's own success criterion.** Criterion 1 asked the
cycle soak on a grant-bearing shape to produce ≥1 `hv_set` within 8 cycles. That
criterion is not satisfiable by any 8-cycle soak on the deterministic stub, and
the reason has nothing to do with the fix. It was written before anyone had
measured `_lazy_hv`'s precondition. The criterion it should have named is the
end-to-end transaction test; the soak's honest job here is the no-regression
half, which it did.

---

## 2026-09-02 · Segment 4 — residue

Stated as residue rather than buried, because two of these bound what the
tranche may be read to have proven.

- **`hv-floor` is NOT converted, and `hv` is therefore only half-reachable.**
  `run_hv_floor` is not a ranking measure: on `hv < hv_min` it calls
  `register_fail_warrant` and REFUTES its target, and `rules/spawn.py:150-172`
  pins its criterion onto every connection problem the harness mints. Converting
  it changes refutation outcomes with no configuration having asked. Priced from
  the record: 53 connection problems and 95 distinct deferred `hv-floor` targets
  on the grant-bearing root alone. Parked P7 with the prompt written; the code
  change is one table row and the evidence question is the whole tranche.
- **Reachable does not mean reached.** `hv` is now reachable by configuration —
  but only through a `criticism_policy` whose authority is `defended_trial`,
  because that is what mints the grant. Of 50 committed v6 roots, exactly 4 hold
  a variator grant and all 4 are `defended_trial`. Whether that minting
  condition is itself too narrow — the solo-run law says sole-model operation
  must not be locked out of a capability, and `hv` invokes no judge — is parked
  as P5, and it is a `run_manifest.py` question (frozen surface 4), not a gate
  question.
- **Ten of eleven phases still defer**, by design.
  `REC-give-a-legacy-phase-v6-transactional-dispatch.md` is the path, one phase
  per tranche; P1 carries the prompt. Two of the ten (`property-design`,
  `vision-criticism`) cannot be converted at all until some compiler mints a
  grant for their roles — their rows carry an empty contract set to say so.
- **No live run.** GOAL.md's optional live check was not taken: the offline
  end-to-end test proves the dispatch on the real transaction machinery, and a
  live run would add an observation, not a proof. The API key was not requested.
- **The diff exceeded its own budget.** `tools/diff_budget.py` returns
  `EXCEEDED`: 210 insertions against GOAL.md's 150-line ceiling. Measured
  composition: ~95 lines are executable, the remainder module and function
  docstrings and blanks. One paragraph of the registry's docstring was moved to
  the map during implementation, because it narrated history — which CLAUDE.md's
  own comment convention forbids — but that was a correctness fix worth two
  lines, not a route to the ceiling. The overshoot is real and is reported
  rather than shaved.
- **`reach` untouched**, as instructed. Its zeros are empirical, not structural;
  parked P3.


---

## 2026-09-02 · Segment 5 — the operator overturns the stop, and `hv-floor` goes on

**What happened.** VERIFY.md handed the operator the `hv-floor` road with both
options priced and Road B (leave it off) recommended. They ruled the other way,
verbatim:

> "It used to be on. And it's absolutely necessary. So switch it on. And you can
> test whether it works as intended"

**The first sentence is a correction, and it is the important part.** This
tranche framed converting `hv-floor` as INTRODUCING refutation that no
configuration had asked for. That framing was wrong. `hv-floor` dispatched on
every pre-v6 run; it stopped only when operations parity (2026-08-13) made v6
the only path and the gate's `schema_version` escape went dead — while
`rules/spawn.py` went on pinning its criterion onto every connection problem the
harness minted. The 95 deferred targets on the grant-bearing root were not 95
artifacts spared a new test. They were 95 criteria pinned and never evaluated.
Restoring the evaluation is the fix, not a widening of it.

**What shipped.** `LEGACY_PHASE_CONTRACTS["hv-floor"].dispatch` becomes
`TRANSACTIONAL` and `run_hv_floor` self-detects the bound manifest exactly as
`hv_spot_check` does. Two of eleven phases are now converted; nine remain.

**The obligation the ruling carried — "test whether it works as intended" — is
not the dispatch test.** Four offline tests drive the criterion to each of its
verdicts through a real transaction: FAIL refutes and mints exactly one warrant
with `s_hat` in its trace; PASS records the estimate and leaves the target
ACCEPTED with no warrant; zero samples return OVERRUN rather than passing
vacuously from no evidence (the trap `DR-SUB-evaluation` records); and no status
moves on an artifact that carries no `hv-floor` commitment. Eleven mutations now
go RED, including flipping the row back and reverting `run_hv_floor`'s dispatch.

**FIX.md §4's blanket claim is retired and replaced, not quietly dropped.**
"Nothing in this change may alter what counts as accepted, refuted, or
warranted" held for `hv_spot_check` and cannot hold for `hv-floor` — refuting is
the point. The claim that replaces it is bounded and testable: a status moves
ONLY for an artifact carrying an `hv-floor` commitment, and only from that
commitment's own verdict.

---

## 2026-09-02 · Segment 6 — the live check, and what one live run can say

**What the record shows.** Against glm-5.2 on Ollama Cloud, with the variator
seat holding `variator.direct.v1`, five live transactional variator calls across
two runs — every one under contract `variator.direct.v1`, work kind
`DEFENDED_TRIAL_STEP`, payload schema `hv-variation-step.v1` — and **`verify_root`
clean, 0 violations, on both roots**. Both producers reached typed outcomes:
`hv_spot_check` recorded an `hv_set` event carrying no `llm` (the transaction is
the accounting, as designed), and `run_hv_floor` reached FAIL with a minted
warrant in one run and PASS with a recorded estimate in the other.

**The value is sample-dependent, and that is inherent.** `hv` samples k edits
from a live variator and scores their survival, so a different sample is a
different number — which is why `hv_spot_check`'s own docstring calls it "a
spot-check, re-estimable later". One live run is evidence that the path works
and is not a measurement of any particular artifact's `hv`. A tranche that reads
a single live `hv` as a verdict on a claim has over-read it.

**The disagreement had a cause, and finding it is the useful part of this
segment.** Runs 1 and 2 ran WITHOUT warming the neural embedder, so
`_equivalent` fell back to hashing. An edit survives only if it passes the
battery AND is judged INEQUIVALENT to the original, so the equivalence surrogate
decides half of every verdict — and on the hashing fallback it decides it badly.
A third run with `deepreason embedder-warmup` done first
(`NeuralEmbedder`, `nomic-ai/nomic-embed-text-v1.5`) gets both cases right and is
the run to read:

| target | verdict | status | hv |
|---|---|---|---|
| easy-to-vary relation, no battery | **fail** (`s_hat` 1.0, 8 live edits, all survived) | REFUTED, 1 warrant | — |
| hard-to-vary relation, `k-energy` battery | **pass** | ACCEPTED | **0.5** |
| `hv_spot_check` target | — | — | 0.0, one `hv_set` event, `llm` not attached |

`verify_root`: 0 violations. That is `hv` behaving as spec §16 intends, live: the
relation any edit can imitate falls, the relation whose battery the edits break
survives, and the surviving one's `hv` is an intermediate 0.5 rather than a
degenerate 0.0 or 1.0.

**The rule this establishes, and it generalises past this tranche:** a live `hv`
number taken without warming the embedder is not a measurement. CLAUDE.md
already says to warm it in the setup phase of any session that runs the harness.
This is what skipping it costs — no error, no fallback notice anyone would
chase, just verdicts that quietly flip.

**What the live check does NOT show.** It drives the two producers directly. It
does not show a live SCHEDULER reaching `_lazy_hv` or the `hv-floor` arm on its
own, which needs a run deep enough to produce an ACCEPTED-and-addressed artifact
or a connection problem. That remains unproven live, and the offline soaks
established why no stub-driven soak can supply it.

**A scaffold trap worth keeping, because it cost this check a run and reads
exactly like a defect.** A root whose `run-manifest.json` is not ON DISK makes
`verify_root` return early with an empty controller-v3 context, so every
transactional call fails `workflow-call-pairing` with "transaction call is not
its durable provider result". Three violations, all meaningless. The root must
be built properly — run input first, manifest compiled against its digest, both
bound — before `verify_root` says anything about a transaction at all.

**Credential hygiene.** The operator's key was written to
`experiments/2026-09-02-defect-hv-v6-reachability/env`, confirmed matched by
`.gitignore:47` (`experiments/*/env`) with `git check-ignore` before use, and
never committed.
