# AUDIT REPORT — why the P-T1 technique run showed problems

Forensic audit, 2026-08-28. Read-only: this tranche modified no `src/`, no
`tests/`, no `docs/`, and no committed run root.
`git diff --stat origin/main -- src tests docs` is empty.

**Authority.** Operator, 2026-08-28, verbatim: *"ok so the last run shpwed
problems. I need an audit to figure out why."* And, governing method: *"tokens
are cheap. You are not. So any experiments with token spend that can settle
things is preferred."*

**Evidence base.** Four committed roots on branch
`claude/spec-to-code-technique-k5209o`, read and never written:

| epoch | root | state / stop_reason | cycles | `token_spend` in status |
|---|---|---|---|---|
| 0 | `failed-epoch0-run-19c2ff74…` | failed / `operational_failure` | 2 | **0** (log: 580 016) |
| 1 | `completed-epoch1-run-92e63dcb…` | completed / `budget_exhausted` | 12 | 413 631 |
| 5 | `failed-epoch5-run-456885c5…` | failed / `operational_failure` | 2 | **0** |
| 6 | `run/` | completed / `budget_exhausted` | 24 | 772 482 |

Epochs 3 and 4 ran on a second credential and their roots were never
committed; every figure about them below is QUOTED from `RESULTS_EPOCH3.md` /
`RESULTS_EPOCH4.md` and is never re-derived. That is a limit on this audit,
recorded here rather than discovered later.

---

## The verdict table

| # | question | verdict | the finding in one line |
|---|---|---|---|
| **F-A** | Q2 | **CAUSE LOCATED** | Five "everything on" switches never reached the run: the builder omits `criticism_policy` and the manifest's config echo drops the rest, so a `--run-manifest` launch silently rebuilds them at their OFF defaults. `compile_notices: []`. |
| **F-B** | Q1 | **CAUSE LOCATED** | The critic's byte-checked citation channel was rendered on 5 of 98 critic dispatches, and latches shut permanently after one use. M2 was unmeetable, not unmet. |
| **F-C** | Q4 (P6) | **CAUSE LOCATED** | Both completed roots report themselves resumable and would refuse `continue`. The lifecycle refusal is caught and discarded at `text_runs.py:245-246`. |
| **F-D** | Q5 (P8) | **CAUSE LOCATED** — parked diagnosis REFUTED | The repair-`mode` producer and its checker share exactly one value. The death is deterministic on payload shape, not stochastic. |
| **F-E** | Q4 (P2/P3) | **CAUSE LOCATED** — parked fix location CORRECTED | The zero-spend surface is a WRITER defect: the failure-path `progress.emit` calls omit `token_spend`, which defaults to 0. |
| **F-F** | Q3 | **CAUSE LOCATED** | The wander cap was present and DID bind — and was consulted on 4 of epoch 6's 24 cycles, while the other 20 still advanced its denominator. |
| **F-G** | Q5 (P9) | **CAUSE ESTABLISHED**, sharpened | No rule turns a criticism into a successor problem. The ontology already declares a `SUCCESSOR` trigger with zero producers. |
| **F-H** | Q5 (P7) | **CAUSE LOCATED** — parked claim PARTLY WRONG | A typed backoff bound DOES exist (`endpoints.py:15,52`). What is missing is a cross-case circuit-breaker and HTTP-status preservation. P7's cited evidence file no longer resolves. |

**Live token spend: 60 769 tokens, one probe, 16 calls** (Q1 only; every other
question was settled offline). Detail in §1.4.

`python tools/docs_verify.py` → **4 failed**, exactly the stated baseline
(3 shallow-clone `CON-run-identity.md`, 1 pre-existing `INV-frozen-surfaces.md:181`).
No delta. Output at `probes/docs_verify.out`.

---

## F-A — Q2: why the judges were never called

**Verdict: CAUSE LOCATED. Four independent closures, none disclosed. This is
the audit's largest finding and it is not about judges.**

`RESULTS.md` §3 explains the zero as *"they were never called, because the run
died at cycle 2 and adjudication had not been reached."* **That explanation is
wrong.** Epoch 6 ran 24 of 24 cycles to a clean terminal and also recorded zero
judge calls. The cause is upstream of anything the run did.

### What the operator configured, and what the run received

`run-config.yaml` is consumed ONLY by `build_manifest_pt1.py:71`. The ladder
launches with `--run-manifest` and no `--config` (`pt1_run.sh:120-124`), so at
run time the Config is rebuilt by
`run_manifest.py::config_from_run_manifest` (4287) as
`Config.model_validate(json.loads(manifest.engine_config_json))` — and every
field the echo does not carry takes its **default**.

Measured by reconstructing that Config from the committed manifest
(`probes/q2_judge_reachability.json`):

| Config field | `run-config.yaml` | in manifest echo | **effective at run time** |
|---|---|---|---|
| `JUDGE_SEATS_ENABLED` | `true` | no | **`false`** |
| `ADJUDICATION_STATUS_AUTHORITY_ENABLED` | `true` | no | **`false`** |
| `ENGAGED_CRITICISM_AUTHORITY` | `defended_trial` | no | **`observe_only`** |
| `LEGACY_CRITICISM_ENABLED` | `false` | no | **`true`** |
| `SCHOOL_SEATS_ENABLED` | `true` | no | **`false`** |
| `JUDGE_SUMMONS_PER_CYCLE` | (unset) | no | **`0`** |

Each drop is deliberate and documented — `run_manifest.py:2363-2432` pops them
from the versioned-source echo so that adding a knob does not move every frozen
manifest golden and every qualification subject digest. The justification given
for each is one of two sentences: *"its effect is already visible in the
compiled manifest's own `criticism_policy`"*, or *"it lives on Config only,
consulted at dispatch sites."*

**Both justifications hold for a `--config` launch and fail for a
`--run-manifest` launch.** "Lives on Config only" means "is lost" when the
Config is rebuilt from the echo. And the first justification fails for a
second, independent reason:

### The manifest carries no criticism policy at all

`build_manifest_pt1.py:307-333` calls `compile_run_manifest(...)` and **never
passes `criticism_policy`**. It defaults to `None` (`run_manifest.py:1251`) and
is popped from the payload (`1362-1363`). The compiled
`run-manifest.json` has no `criticism_policy` key. So the value is in neither
the policy nor the echo.

Compare `preparation.py:499-511`, which is the path that DOES wire it:
```python
criticism_policy=(None if config.LEGACY_CRITICISM_ENABLED
                  else engaged_criticism_policy(..., authority=(
                      config.ENGAGED_CRITICISM_AUTHORITY
                      if config.ADJUDICATION_STATUS_AUTHORITY_ENABLED
                      else "observe_only"), ...))
```

### The four closures, any one of which is sufficient

1. `criticism_policy` absent → `crit.py:1476` resolves authority from Config.
2. `ARGUMENTATIVE_AUTHORITY = observe_only` → `crit.py:1600-1607` returns
   `_observe_case`; `_TRIAL_MODES` (`crit.py:79`) is never entered.
3. `JUDGE_SEATS_ENABLED = false` → `scheduler.py:1346` `continue`s.
4. `JUDGE_SUMMONS_PER_CYCLE = 0` → `scheduler.py:1060-1077`, whose own
   docstring says it defaults *"to preserve exactly zero judge activity … even
   with JUDGE_SEATS_ENABLED on."*

### Nothing said so

`compile_notices` is `[]` on the committed manifest and in
`launch-epoch6.out:4`. The doctor meanwhile printed
`ok judge seat 0 glm-5.3-flash` / `ok judge seat 1 qwen3.5:397b`
(`launch-epoch6.out:45-46`) — two seats qualified, at real cost, for a road
closed four times over.

**Recurrence.** `docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` §3.2 item 6 recorded
this exact shape: *"Four run configs asked for `defended_trial`; three of the
four builders after the one that worked dropped the line, and compile emits no
notice when a config asking for it compiles to a manifest with no criticism
policy."* P-T1 is the next instance.

**Operator law implicated.** The 2026-08-12 all-configurations law says a
configuration that parses compiles, and that what used to be a refusal becomes
*"a typed disclosure recorded alongside the compiled result … never a stop."*
Here there is neither refusal nor disclosure — a silent revert to a different
configuration. The 2026-08-13 operations-parity law's mechanism is ONE RUN
PATH, with `deepreason run --run-manifest` as *"a rendering shell"*; a shell
that changes six behavioural switches is not rendering the same run.

New parked prompt: **P10**.

---

## F-B — Q1: why no critic ever cited the record

**Verdict: CAUSE LOCATED. The channel was structurally closed on 93 of 98
critic dispatches; on the 5 where it opened, the seat declined it.**

### (a) Is the channel reachable from the critic seat?

The critic's ONLY byte-checked citation path is a PREMISE filing.
`rules/crit.py:1401 _file_attribution` calls `_check_premise_citations`
(`1367`), the sole producer of the `premise-citation:<CODE>` Measure that
`milestone_census.py` counts for M2. `_file_attribution` returns `None` — and
files and checks nothing — unless `_premise_invited_problem` (`crit.py:1268`)
finds a problem standing an invitation, which is
`premises.py::premise_work_invited` (`625-645`):

```python
if any(pid == problem_id for _, pid, _ in standing_attributions(harness)):
    return False                       # latches shut after ONE attribution
refuted = <artifacts under this problem with status REFUTED>
return refuted >= PREMISE_INVITE_AFTER          # == 2   (premises.py:68)
```

Measured per root (`probes/q1_invite_gate.py`):

| root | max REFUTED on one problem | gate could open |
|---|---|---|
| epoch 0 | 1 | **no** |
| epoch 1 | 1 | **no** |
| epoch 5 | 3 | yes |
| epoch 6 | 6 | yes |

### (b) Attempted and rejected, or never attempted?

Never attempted — and the record separates the two cleanly, because
`_check_premise_citations` returns `()` without recording anything when `refs`
is empty, so a zero count is consistent with two worlds. Reading the raw
responses of every invited dispatch (`probes/q1_invited_replies.json`) settles
it: four returned `premise: null, premise_evidence: null`, one (epoch 6 seq
180) returned a substantive `premise` with `premise_evidence: null`. No
`premise_evidence` array was ever submitted, so nothing was ever rejected.

Citation Measures across the four roots (`probes/q1_citation_census.py`):
conjecture-side verified 9 / 8 / 2 / 1; **critic-side verified 0 / 0 / 0 / 0.**

### (c) What is the critic actually shown?

Read from the prompt bytes each call was made on
(`probes/q1_prompt_surface.json`):

| root | critic dispatches | invitation shown | citable-block legend shown | `premise_evidence` in the schema |
|---|---|---|---|---|
| epoch 0 | 29 | **0** | **0** | 25 |
| epoch 1 | 15 | **0** | **0** | 15 |
| epoch 5 | 10 | 3 | 3 | 10 |
| epoch 6 | 44 | 2 | 2 | 43 |
| **total** | **98** | **5** | **5** | **93** |

**This is the shape of the defect.** On 93 dispatches the seat is handed a wire
field requiring `{"block": "^[0-9a-f]{12,64}$", "quote": ...}` — verified at
epoch 0 seq 111 — and is shown **no block ids anywhere in the prompt**. The
only lawful value is null. Even a guessed hex id would fail
`_exposed_block_ids_for_call` (`crit.py:1341`), as the invited prompt's own
words say: *"a citation of a block this call was not shown does not verify."*

Consistent with `RUN_ANATOMY_SYNTHESIS` §2.5: where an escape exists in the
TYPE, models take it; the field is nullable with default null, and it was
nulled 98 times out of 98.

### The latch, and why it matters more than the threshold

In epoch 6 the invitation fired at seqs 141 and 180. At seq 180 the seat filled
`premise`; at seqs 185-186 the premise and its attribution were registered; and
from seq 187 to the run's end at seq 989 the gate was shut, because
`premise_work_invited` returns `False` once any attribution stands.

The run then established, at **seq 779**, in surviving conjecture
`aadd39655456…`, that its own question was malformed. **The run proved its
question was wrong 593 events after the only channel for saying so had
permanently closed.** The invitation fires on a refuted-count trigger that has
nothing to do with whether anyone believes the question is wrong, and it closes
before the evidence arrives. This is the same wound P9 names, seen from the
citation side.

### The live probe

Registered in `PREREG_LITE.md` before the credential was used. Replayed epoch 6
seq 180's verbatim prompt bytes against `kimi-k3` at `reasoning_effort=low`,
8 reps control and 8 reps with a worked exemplar of a filled `premise_evidence`
entry appended.

| arm | n | `premise_evidence` filled | `premise` filled | tokens |
|---|---|---|---|---|
| A control | 8 | **0** | **0** | 29 968 |
| B + exemplar | 8 | **0** | **0** | 30 801 |

Per the frozen decision rule (`A ≤ 1/8 and B ≤ 2/8`) the behavioural half is
**MODEL BEHAVIOUR**: shown the channel and shown how to use it, the seat
declines. Raw responses and both prompt arms at `probes/live/`.

**Honest limit, and it cuts against the strong reading.** The invitation says
*"Leave it null otherwise; declining costs you nothing."* A null premise is a
legal and possibly correct answer when the seat sees no malformed
presupposition, and this probe cannot distinguish that from refusing the
channel. What it does establish is that the epoch-6 filled premise was the
outlier: 1 of 17 observations, not the norm. And it cannot touch the structural
half — 93 of 98 dispatches never saw the channel at all.

**So the answer to Q1 is: wiring first, prompt surface second, model behaviour
third.** M2 was not missed. It was unmeetable in epochs 0 and 1, and open for
5 dispatches in epochs 5 and 6.

New parked prompt: **P11**.

---

## F-C — Q4 (P5/P6): amend accepts what continue refuses

**Verdict: CAUSE LOCATED. P6 confirmed, with a fresh instance on today's
`main`, and the swallow site named.**

Measured on all four roots (`probes/q4_lifecycle_surfaces.json`):

| root | stop reason | in `RESUMABLE_STOP_REASONS` (what `results` reads) | terminal lifecycle decision (what `continue` reads) | surfaces disagree |
|---|---|---|---|---|
| epoch 0 | `operational_failure` | no | absent | no |
| epoch 1 | `budget_exhausted` | **yes** | **absent** | **yes** |
| epoch 5 | `operational_failure` | no | absent | no |
| epoch 6 | `budget_exhausted` | **yes** | **absent** | **yes** |

All four carry **zero lifecycle decisions of any kind** and a valid terminal
commitment. Epoch 6 completed on 2026-08-28, after the execution-safety tranche
merged, so **P6 is not fixed and now has a fresh instance.**

**The mechanism, confirmed end to end.**
`workflow/lifecycle.py:210-217` builds the outstanding-work snapshot and raises
`ValueError("STOPPED refuses unfinished workflow authority")` when it is
non-empty. Measured outstanding work at stop: **epoch 1 = 3 items, epoch 6 = 9
items** — so the refusal is correct. `text_runs.py:229-246` then does:

```python
try:
    observation, snapshot, lifecycle = build_stopped_lifecycle(...)
except ValueError:
    return None
```

`return None` falls through to the bare stop record, and the run publishes
`state=completed`, `stop_reason=budget_exhausted`, `ready for continue: yes` —
with no trace that its terminal transition was rejected. **The swallow is the
defect**, and it is one bare `except ValueError` at
`application/text_runs.py:245-246`.

P5's separate claim (`amend` succeeds where `continue` refuses) rests on
`amend` not consulting the predicate `results.py` already computes; the roots
above supply the population, and this audit did not re-run the CLI sequence
because P6's fix changes which roots can reach it.

Existing prompt **P6** covers this; **amendment P6-A** below adds the fresh
instance, the outstanding-work counts and the exact swallow line.

---

## F-D — Q5 (P8): the repair-mode death is deterministic, not stochastic

**Verdict: CAUSE LOCATED. The parked "stochastic, 2-run control" reading is
REFUTED.**

The producer and the checker do not share a vocabulary:

| | value set | source |
|---|---|---|
| producer | `initial`, `whole_object_syntax`, `patch` | `llm/repair.py:1505` (`V6RepairTurn.mode`), emitting `whole_object_syntax` at `1612` |
| checker | `patch`, `full` | `workflow/nonconjecture_recovery.py:1002` |

They intersect in **`patch` alone**. `full` is accepted by the checker and
emitted nowhere in `src/`. `whole_object_syntax` is emitted constantly and
accepted nowhere.

Every repair payload in the record (`probes/q5_repair_payloads.json`):

| root | repair payloads | `patch` | `whole_object_syntax` | illegal |
|---|---|---|---|---|
| epoch 1 | 6 | 2 | 4 | 4 |
| epoch 5 | 18 | 6 | 12 | 12 |
| epoch 6 | 32 | 12 | 20 | 20 |

The check is reached for EVERY repair-kind child recovered through
`atomic_recovery.py:68-71` (`if preparation.task_kind.value == "repair"`) and
`nonconjecture_recovery.py:1194`. So **any `whole_object_syntax` repair child
that reaches a recovery path raises `NonConjectureRecoveryAuthorityError` and
kills the run** — confirmed as epoch 5's `error_type` in its own
`run-result.json`. What varies between runs is only whether a recovery path is
taken over such a child; the failure itself is deterministic on shape.

`probes/q5_repair_vocabulary.py` asserts both halves against the live source
and all three records and exits 0 — it would go red the moment either
vocabulary moved.

Note the second-order reading, which matters for the fix: P8 warns *"Do NOT
widen the accepted mode set to make the error go away."* Correct, and now
sharper — the accepted set contains a value nothing emits and omits one
everything emits, so it was written against a vocabulary that is not the
producer's. The repair is to make the two share a type, not to add a string.

**Replacement parked prompt: P13** (P8's own prompt is superseded).

---

## F-E — Q4 (P2/P3): one condition, two terminals; and the zero-spend surface

**Verdict: CAUSE LOCATED. Both confirmed; P3's fix location CORRECTED.**

### P2 — the two terminals

| terminal | site | resumable |
|---|---|---|
| `budget_exhausted` | `text_runs.py:317-341` via `_record_exhaustion_lifecycle_stop` | yes (`lifecycle.py:28`) |
| `operational_failure` | `text_runs.py:1485-1541`, the bare `except (Exception, SystemExit)` | no |

`WorkBudgetDenied` (`workflow/transaction.py:691-696`) appends a **durable
typed `budget_denied` terminal before it raises**, and `atomic_recovery.py:35-39`
re-raises it with the comment *"so the standard typed-stop path handles it
instead of failing the run"* — which is precisely what does not happen. It
escapes (`crit.py:471` re-raises it deliberately) and lands in the generic
handler. Confirmed at the record level: epoch 0's `run-result.json` carries
`error_type: "WorkBudgetDenied"` with `stop_reason: operational_failure`, while
epochs 1 and 6 reached `budget_exhausted` on the same underlying condition.

The design question P2 poses — *is a denied reservation on an exhausted budget
an operational failure at all?* — is unchanged by this audit, and the evidence
now favours "no": the denial is typed, durable, and recorded before the raise.

### P3 — the zero-spend surface, and where the fix belongs

The chain, end to end:

- `text_runs.py:1435-1447` — the SUCCESS terminal passes
  `token_spend=sum(event.llm.tokens for event in harness.log.read() if event.llm)`.
  Correct: it walks the log.
- `text_runs.py:1466-1475`, `1479-1490`, `1533-1541` — the three FAILURE
  emits pass `token_limit=token_budget` and **no `token_spend` at all**.
- `runtime/progress.py:55` — `token_spend: int = Field(default=0, ge=0)`.
  Omitting the kwarg asserts 0; it does not leave a gap.
- `progress.py:119` writes that event to `run-status.json`.
- `application/results.py:172` reads `status.get("token_spend", _absent(...))`.
  The key IS present, so the absence sentinel never fires, and `results.py:510`
  prints `tokens spent vs budget: 0 / 600000`.

**The parked P3 prompt sends the fixer to `results.py` and says "the fix
belongs in the READER, not in the record." That is half right and would leave
the defect in place.** The reader is behaving correctly on a status file that
asserts a false fact; the writer three lines from the correct call omits an
argument it already knows how to compute. Both roots that failed report 0; both
roots that completed report correctly.

This is also a **recurrence**: `RUN_ANATOMY_SYNTHESIS` organ 10 records *"18 of
54 roots report `token_spend: 0`"* while the log carries a real figure.

**Amendment P3-A** below; P2's prompt stands as written.

---

## F-F — Q3: the on-subject collapse

**Verdict: CAUSE LOCATED — cap present, cap BOUND, and cap unconsulted for 83%
of epoch 6's cycles. Off-subject descent traced to `conn:`-commissioned
problems.**

Stated in the terms the research note's interpretation discipline requires:
narrowing is presumed generator-intrinsic until control arms say otherwise, so
nothing below claims criticism caused or cured anything.

### Was the cap present and engaged?

Yes — **by default, and only by accident of the same echo drop as F-A.**
`SEED_PROBLEM_BUDGET_FLOOR` and `ATTENTION_ALLOCATION_POLICY` are popped from
the echo at `run_manifest.py:2386-2387`, so the run rebuilt them at their
defaults `0.5` and `wander-cap.v1` (`config.py:295, 310`). A configuration that
had deliberately SET a different floor would have lost it exactly as F-A's
switches were lost.

### Did it bind?

Yes. From the emitted signals (`probes/q3_wander.json`):

- **Epoch 1** — 12 readings over 12 cycles, throttle engaged **5 times**,
  share trajectory `1.0, 1.0, 0.5, 0.333, 0.5, 0.4, 0.5, 0.429, 0.5, 0.444,
  0.5, 0.455`. The cap pulled the share back to the floor each time it dipped.
  This is the mechanism working as designed.
- **Epoch 6** — **4 readings over 24 cycles**, throttle engaged once, at
  cycle 3 (`share 0.3333 below floor 0.5000`), and never consulted again.

### Why it stopped being consulted

`scheduler.py:2052-2054`:

```python
if self._simulation_capability_step():
    self._cycles += 1
    return
```

The capability step emits its own `cycle` heartbeat (`scheduler.py:1802, 1950,
2030`) and returns **before** `_select_problem()` (2056), where `wander.decide`
runs, and before `_disclose_wander()` (2061). Epoch 6's 24 heartbeats
(`probes/q3_cycle_accounting.json`):

| heartbeat problem | cycles |
|---|---|
| `simulation-result:sha256:b5a7f812…` | **19** |
| `simulation-request:sha256:295ce6b0…` | **1** |
| the seed question | 2 |
| `disc:` on the seed | 1 |
| `conn:0a89b2b812ae` | 1 |

20 + 4 = 24, and there are exactly 4 wander readings. **Each of those 20 cycles
advanced `self._cycles` — the denominator of the seed-lineage share — without
advancing `_seed_cycles` and without consulting the policy.** So work that IS
the operator's own experiment dilutes the very floor meant to protect the
operator's question, and does so invisibly.

### Where does off-subject work descend from?

Not from drift inside the seed lineage. Every off-subject accepted conjecture
in both completed roots is addressed to a `conn:` problem
(`probes/q3_survivor_descent.json`):

| root | accepted conjectures | addressed to the seed | addressed to `conn:` |
|---|---|---|---|
| epoch 1 | 8 | 2 | **6** |
| epoch 6 | 13 | **3** | **10** |

These reconcile exactly with the tranche's own reported "2 of 8" and "3 of 13",
and they confirm P9's correction: the scheduler does not compete with the seed
question, it **commissions** 14-15 `conn:` problems per run from a fixed
template in `rules/spawn.py:172`.

### The verdict on the collapse

Epoch 4's 9-of-19 cannot be re-derived (root not committed). What the committed
record supports is narrower and does not need the epoch-4 number: **epoch 6
gave the scheduler 4 of its 24 cycles**, and of those 4 it worked the seed
twice, `disc:` once and `conn:` once. Fewer conjecture-producing cycles, fewer
on-subject survivors. That is a budget fact about where cycles went, not a
finding about criticism, and it is stated as such.

New parked prompt: **P12**.

---

## F-G — Q5 (P9): criticism cannot become a question

**Verdict: CAUSE ESTABLISHED (already on the record), sharpened by one
locator.**

Confirmed: `rules/spawn.py`'s entire problem vocabulary is six templates —
`disc:` (80), `ra:` (104), `debt:` (141), `conn:` (172), `research:` (186),
`integ:` (222). None consumes a criticism's content.

**The locator P9 did not have.** `ontology/problem.py:20-37` already declares
the trigger the successor rule would need:

```python
SUCCESSOR = "successor"          # retained for replay only
```

with a comment stating *"INERT VOCABULARY: producers = 0. No code path mints a
problem with this trigger … its presence asserts no producer and licenses no
new one."* So the ontology has the slot, the enforcement is a source scan
(`tests/test_decommissioned_pipeline_stays_out.py`), and reviving it is a
deliberate act rather than a new kind — which changes the shape of the change
P9 asks for.

Also worth naming: `AUDIT_CRITIC = "audit-critic"` is the one trigger that
reacts to criticism behaviour, and it audits the CRITIC, not the QUESTION. It
is the trigger that spent 41.2% of P-C1's budget (`RUN_ANATOMY_SYNTHESIS` §2.1).

**Smallest seam where a successor rule attaches — map ids only, no design:**
`DR-SEAM-ontology-x-rules` (the trigger vocabulary meets the minting rules),
then `DR-CON-problem-layer-lifecycle`, with `DR-CON-scheduler-ranking` owning
the seed's rank guarantee, `DR-CON-criticism-source` owning what a criticism
may address, `DR-CON-run-identity` because problem ids feed run identity, and
`DR-INV-frozen-surfaces` read first.

Existing prompt **P9** stands; **amendment P9-A** adds the `SUCCESSOR` locator
and the seam ids.

---

## F-H — Q5 (P7): the quota retry

**Verdict: CAUSE LOCATED, and P7's framing is PARTLY WRONG.**

Q5 asked to "confirm no typed backoff bound exists." **One does.**
`llm/endpoints.py:15` `_RETRYABLE_HTTP = {429, 500, 502, 503, 504}` and
`endpoints.py:52-71 request_with_retries` applies a bounded `2s/4s/8s` ladder,
three retries, then `EndpointError`. So each individual call is bounded at
~14 s of sleep.

What is actually missing is two other things:

1. **No cross-case circuit-breaker.** `cli/doctor.py:535-560` runs the battery
   case by case; each case exhausts its own bounded ladder independently, and
   nothing notices that an account-level condition has already failed every
   case. 80 cases × 4 pairs of bounded ladders is how 18 minutes is spent
   arriving at a conclusion available from the first response. The bound exists
   per call and there is none above it.
2. **The HTTP status never reaches the record.**
   `cli/doctor.py:415-425 _failure_code` reads `getattr(error, "code", "")`
   first; `EndpointError` (`endpoints.py:42`) carries no `code` attribute, so
   the function falls through to normalising the CLASS NAME —
   `EndpointError` → `ENDPOINT_ERROR`. Every transport condition (network
   fault, provider outage, 429 quota refusal) collapses to one code, and the
   `ProductionContractCaseResultV1` has no field carrying the provider's
   message at all.

Also worth questioning in the fix: whether 429 belongs in `_RETRYABLE_HTTP`
unconditionally. A rate limit clears in seconds; a session usage limit does
not, and both arrive as 429.

**P7's evidence pointer does not resolve.** It cites
`experiments/2026-08-27-change-technique-run/qualify.json` → *"every case
failure_code ENDPOINT_ERROR"*. That file was overwritten by a later successful
battery and now reads `eventual_valid_count: 80, qualified: true`. A live
committed instance of the same failure does exist on `main`:
`experiments/2026-08-25-change-constructive-frontier/qualify-attempt2-VOID-agent-error.json`
— 80 cases, **140 `ENDPOINT_ERROR`**, 3 pairs re-exercised, `eventual_valid_count: 0`.

**Amendment P7-A** below.

---

## Residue — what is still open, and what settling it would cost

1. **Epochs 3 and 4 are unauditable.** Their roots were never committed, so the
   trend table `14% → 25% → 30% → 47% → 23%` rests on two re-derivable points
   and three quoted ones. Cost to settle: nothing recoverable — those roots are
   gone. Cost to prevent recurrence: commit every root, including
   second-credential ones.

2. **Whether the critic would ever cite, on a better prompt.** The live probe
   tested ONE prompt, one target, one model, at `reasoning_effort=low`. A null
   `premise` is legal when the seat sees no malformed presupposition, so 0/16
   is consistent with both "will not use the channel" and "correctly saw
   nothing to say." Cost to settle: ~40k tokens — the same replay with a
   deliberately malformed presupposition planted in the problem text, where a
   correct seat MUST fill `premise`. Worth doing inside the P11 fix tranche,
   not before it.

3. **Which recovery path epoch 5 actually took.** F-D proves the vocabulary
   mismatch and that the check is deterministic on shape; it does not identify
   which of the two call sites recovered the offending child. Cost: ~1 hour
   offline, a stub-driven repro that forces a `whole_object_syntax` child
   through `recover_atomic_child_output`. Belongs in the P13 fix tranche, where
   it is the regression test.

4. **Whether F-A's echo drop affects every manifest-launched run or only
   builders that omit `criticism_policy`.** This audit measured one builder.
   Cost: ~30 minutes offline — reconstruct the Config from every committed
   manifest on `main` and diff against its builder's Config. Named in P10.

5. **The wander cap's correct treatment of capability cycles is a design
   question, not a bug.** Whether 20 simulation cycles should count as seed
   work, as other work, or not be counted at all is not settled by the record —
   only that they currently count as neither while still moving the
   denominator. P12 asks the question rather than assuming the answer.

**Accepted does not mean true.** Everything above is read from four committed
roots, one live probe of sixteen calls, and the source at `29e33f702`. Where a
figure could not be re-derived it is quoted and labelled. Where a parked
diagnosis turned out to be wrong, the correction is stated in the same breath
as the finding it corrects.
