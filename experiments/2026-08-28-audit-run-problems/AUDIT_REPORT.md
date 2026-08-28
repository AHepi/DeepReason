# AUDIT — why the P-T1 technique run showed problems

**Read-only forensic audit, 2026-08-28.** Authority: the operator, verbatim —
*"ok so the last run shpwed problems. I need an audit to figure out why."*

Subject: the six-epoch P-T1 technique run on branch
`claude/spec-to-code-technique-k5209o`, read and never modified. This window
changed nothing outside its own directory:

```
$ git diff --stat origin/main -- src tests docs
$                                     (empty)
```

Every claim below carries a record pointer (root, event seq, or file:line).
Model prose — including the run's own RESULTS prose — is never used as
evidence for a claim, only as the subject of one.

**Roots read** (epochs 3 and 4 are not committed on that branch):

| root | state | stop_reason | cycles | token_spend |
|---|---|---|---|---|
| `failed-epoch0-run-19c2ff74…` | failed | operational_failure | 2 | **0** |
| `completed-epoch1-run-92e63dcb…` | completed | budget_exhausted | 12 | 413,631 |
| `failed-epoch5-run-456885c5…` | failed | operational_failure | 2 | **0** |
| `run/` (= epoch 6, `456885c5…`) | completed | budget_exhausted | 24 | 772,482 |

---

## VERDICT TABLE

Ranked by what blocks the mission or violates a ledgered operator law.

| # | Question | Finding | Verdict |
|---|---|---|---|
| **1** | Q2 | The judge road is severed one layer below an ON flag, and the manifest compiled **zero notices** about it | **CAUSE LOCATED** |
| **2** | Q3 | Epoch 6 did **4 working cycles, not 24** — 19 cycles were budget-denied no-ops on one dead package | **CAUSE LOCATED** |
| **3** | Q4b | Every committed root is **unresumable while reporting resumable** (P6), confirmed on the newest root | **CAUSE ESTABLISHED**, extended |
| **4** | Q1 | The critic has **no citation channel attached to criticism** — only to an optional premise behind a gate that reached 4 prompts in 98 critic calls | **CAUSE LOCATED** |
| **5** | Q4a | One budget-denial condition has **at least four distinct dispositions**, not two | **CAUSE LOCATED**, extends P2 |
| **6** | Q3b | The wander cap's "every cycle" disclosure is bypassed by capability cycles; `_cycles` grows where `_seed_cycles` cannot | **CAUSE LOCATED** |
| **7** | Q4a | `token_spend: 0` on a run that spent its budget (P3) — confirmed on two roots | **CAUSE ESTABLISHED** |
| **8** | Q5a | `SpawnTrigger.SUCCESSOR` **exists and was deliberately decommissioned** — the capability P9 wants was removed, not absent | **CAUSE LOCATED**, sharpens P9 |
| **9** | Q5b | P7's parked claim "no typed backoff bound exists" is **wrong**; a bound exists at `endpoints.py:15,51-70` | **CAUSE LOCATED**, corrects P7 |
| **10** | Q1 | The anti-E28 receipt `premise.work-invited.v1` reports **0** on a run where the mechanism fired and completed | **CAUSE LOCATED** |
| **11** | Q5c | P8 repair-mode death: still a two-run control | **UNDETERMINED** |

---

# Q1 — why no critic has ever cited the record through the byte-checked channel

## Verdict: CAUSE LOCATED

Not model behaviour, and not a wiring fault in the checker. It is a
**contract-shape defect**: the critic's output contract has no citation field
attached to its *case*, and the one citation field it does have is bolted to a
different object behind a gate that fired twice in six epochs.

### (a) Is the channel structurally reachable from the critic seat?

Barely. The critic-side checker exists and is wired —
`rules/crit.py:1378-1392` calls `check_candidate_citations` and records a
`premise-citation:{code}` Measure per outcome. But reaching it requires all of:

1. `_file_attribution` (`rules/crit.py:1401-1430`) is called, which
2. requires `_premise_invited_problem` (`:1268-1281`) to return non-None, which
3. requires `premise_work_invited` (`premises.py:625-645`) — **a problem with
   ≥ 2 REFUTED candidates (`PREMISE_INVITE_AFTER = 2`, `premises.py:68`) and no
   standing attribution already filed**, and
4. the citation clause is only *shown* when the pack also carries citable
   blocks (`llm/packs.py:94-125`, the `citable` branch).

Contrast the conjecturer: `ConjectureCandidate.evidence_refs`
(`llm/contracts.py:96`, `max_length=8`) is present on **every** candidate,
ungated, and `rules/conj.py:2551-2585` checks it whenever it is non-empty.

The asymmetry is structural. `ArgumentativeCriticOutput`
(`llm/contracts.py:112-137`) carries `attack`, `case`, `counterexample`,
`premise`, `premise_evidence` — and **`premise_evidence` is bound to
`premise`**, a presupposition *of the problem* that "FORBIDS NOTHING". The
critic's actual argument, `case`, is a bare string with no evidence sibling.

**So a critic arguing "T1 overclaims — see the record's 59/3 masking failure"
has no field in which to file that citation.** M2 asks for something the
contract cannot express.

### (b) Attempted-and-rejected, or never attempted?

**Never attempted.** Census of `premise-citation:*` Measures:

| root | `evidence-citation:*` (conjecturer) | `premise-citation:*` (critic) |
|---|---|---|
| epoch 0 | 9, all VERIFIED | **0** |
| epoch 1 | 8, all VERIFIED | **0** |
| epoch 5 | 2, all VERIFIED | **0** |
| epoch 6 | 1 VERIFIED + 1 `EVIDENCE_REF_UNKNOWN_BLOCK` | **0** |

Every outcome of the critic-side checker is a Measure, verified or not
(`crit.py:1367-1372`, deliberately: "a critic that quoted bytes it was never
shown is a fact the record should carry"). Zero events therefore means the
checker was never entered — not that it rejected anything.

### (c) What is the critic actually shown at generation time?

| root | prompt blobs carrying `PREMISE INVITATION` | critic calls | exposure |
|---|---|---|---|
| epoch 0 | **0** | 29 | **0 %** |
| epoch 1 | **0** | 15 | **0 %** |
| epoch 5 | 2 | 10 | 20 % |
| epoch 6 | 2 | 44 | **4.5 %** |

In epochs 0 and 1 the critic was **never once told the channel existed**,
across 44 calls. Epoch 6's two invitation blobs
(`run/blobs/98/98e3b56d…`, `run/blobs/20/20c3f7b6…`) *do* carry the full
citable clause and both name the seed problem
`question-9e8800977c3e1deaf5b034b93db38959`.

And on the epoch 6 invitation **the critic accepted**: a critic-role
premise + attribution pair (`09cff5b9abfa…`, `b38afbf002e6…`, both
`ProvenanceRole.CRITIC`, both `ACCEPTED`) stands on the seed problem.
Standing attributions across the roots: epoch 0 = 0, epoch 1 = 0,
epoch 5 = 0, **epoch 6 = 1**.

So the critic took the channel up and filed **no citation with it** —
`premise_evidence` was empty, so `_check_premise_citations` returned at its
`if not refs` guard (`crit.py:1369-1370`) and emitted nothing.

### What this settles

M2's six-epoch silence is **a contract-shape defect with a prompt-surface
defect on top**, not a wiring defect. The channel works — it verified 20
conjecture-side citations across four roots. It is simply not attached to the
thing critics do.

Stated with the precision the evidence supports, the six epochs split:

- **Epochs 0 and 1: structurally unreachable.** The critic was never once
  shown the channel across 44 calls. Nothing a model did or did not do can
  explain those two epochs.
- **Epoch 5: shown twice (distinct blobs `a5be92a35660…`, `4c510fb93879…`),
  then the run died at cycle 2** with no attribution filed — inconclusive.
- **Epoch 6: reachable twice, taken up once, cited zero times.** This is **one
  observation** of the channel being available and unused for citation — not a
  pattern, and not enough to attribute the silence to model reluctance.

The honest verdict is therefore that M2 is **currently unmeetable by
construction for criticism proper** (no field exists on `case`), and that the
one narrow road that does exist was open for roughly 4.5 % of one epoch's
critic calls.

### A second finding, found while checking the first: the receipt lies

`scheduler.py:2065-2072` emits a `premise.work-invited.v1` Measure whenever
the premise invitation is live, and its comment states exactly why it exists:
*"The anti-E28 receipt: a mechanism nobody triggers is a mechanism that never
runs, and this harness has shipped two of those."*

**It recorded 0 in all four roots** — including epoch 6, where the invitation
reached two critic prompts (blobs referenced at seq 141 and 180) and produced
a standing attribution.

The receipt samples `premise_work_invited(selected_problem)` at cycle START.
The pack computes the invitation per criticism TARGET mid-cycle
(`rules/crit.py:1477`, `:1641`). In epoch 6 both fell inside cycle 0: the
refuted count crossed `PREMISE_INVITE_AFTER = 2` *after* selection, and the
attribution filed in that same cycle then flipped the predicate False
(`premises.py:638-639`) before the next selection boundary. The receipt's
window was never open at a moment it was read.

So an instrument built precisely to prove this mechanism fires reports that it
never did, on a run where it fired and completed. **This is why the audit's
own first reading of Census 4 was wrong**, and it is corrected above.

Recurrence check: this is the same shape as
`DR-INV-evidence-channels`' recorded trap — *"An enabled channel can still be a
severed ROAD one layer down"* — the trap written for epoch 4's
`runner_profile_mismatch`. Third instance of that pattern in this tranche.

Map: `DR-CON-criticism-source`, `DR-CON-problem-layer-lifecycle`,
`DR-INV-evidence-channels`, `DR-SEAM-llm-x-rules`.

---

# Q2 — why the judges were never called

## Verdict: CAUSE LOCATED — unreachable by construction, two independent sufficient reasons

Not "reachable but never approached". **There was no threshold any epoch
could have approached.**

### What the ladder asked for
`run-config.yaml:157-168` (technique branch):

```yaml
JUDGE_SEATS_ENABLED: true
ADJUDICATION_STATUS_AUTHORITY_ENABLED: true
ARGUMENTATIVE_AUTHORITY: observe_only      # deliberate; see its own comment
ENGAGED_CRITICISM_AUTHORITY: defended_trial
```

The comment states the tranche's belief plainly: *"Real status-changing
authority for this run comes through the engaged criticism engine below,
which that wall never inspects."* **That belief was false for this run.**

### Reason 1 — `criticism_policy` is null, so `ENGAGED_CRITICISM_AUTHORITY` is inert

All three surviving manifests carry `criticism_policy: null`.
`build_manifest_pt1.py` never constructs one (no `criticism_policy`, no
`CriticismPolicy` anywhere in the file).

`ENGAGED_CRITICISM_AUTHORITY` is consumed at **exactly one site** —
`preparation.py:499-511`, which builds `criticism_policy` on the MANAGED
path. A hand-built manifest bypasses that site entirely, so the knob had no
consumer.

The decisive branch is `scheduler/scheduler.py:1430-1449`:

```python
criticism_policy = (
    self.run_manifest.criticism_policy
    if self.run_manifest is not None and ...schema_version in {4,5,6}
    else None
)
...
if criticism_policy is not None:
    self._foreign_arg_crit()   # the ONLY caller passing
    return                     # argumentative_authority=policy.authority (:1650)
eligible = [...]
...
crit_argumentative_batch(harness, batch, self.adapter, config)   # :1488
```

The fallback at `:1488` passes no `argumentative_authority`, no
`critic_school_id`, no `coverage_observer` → `policy_call=False`
(`rules/crit.py:1673-1678`).

### Reason 2 — the fallback reads a knob the ladder deliberately set to observe_only

`_resolve_authority` with `policy_call=False` returns `_authority(config)`
(`rules/crit.py:101-104`), which is `argumentative_authority_mode(config)`
reading **`ARGUMENTATIVE_AUTHORITY`** (`authority.py:95`) = `observe_only`.
`_authority` also applies a master gate at `rules/crit.py:61-62` that would
force `observe_only` anyway if `ADJUDICATION_STATUS_AUTHORITY_ENABLED` were
missing.

`observe_only` routes to `_observe_case`. `_TRIAL_MODES` — the sole path to
`run_argument_trial_from_case` — is never entered, in either the single-target
(`rules/crit.py:1608-1620`) or the batch (`:2189-2200`) path.

### The nearest recorded approach: none, in any epoch
The only occurrence of the string "judge" in epoch 6's `log.jsonl` is a
seat-steerability list naming `judge#0`, `judge#1` as steerable seats. Zero
trial events. All 11 warrants in epoch 6 are `type: demonstrative`
(mechanical commitment checks); none is argumentative.

### The part that is a law violation, not just a misconfiguration

`docs/map/CON-criticism-source.md`'s Traps section gives the exact diagnostic
for this symptom: *"If you are diagnosing 'the criticism policy compiled but
nothing was criticised', read `compile_notices` on the manifest FIRST — the
answer is usually already recorded there."*

**It was not recorded there. The manifest carries no `compile_notices` at
all** (key absent; `run_manifest.py:1351-1355` pops it when empty).

So a manifest that declares `rubric_policy: "require_cross_family"` — a
cross-family JUDGE requirement — while carrying no criticism policy through
which any judge could ever be reached, compiled **silently**. The
all-configurations law (2026-08-12) requires that what used to be a
compile-time refusal *"becomes a typed disclosure recorded alongside the
compiled result"*. Here there is neither refusal nor disclosure.

Note on a tempting false lead, ruled out: the absence of the four Config keys
from `engine_config_json` is **not** evidence they were unset. They are
dropped deliberately (`run_manifest.py:2378-2400`) so qualification subject
digests do not move — `docs/ERRATA.md` E44 records exactly this.

Map: `DR-CON-criticism-source`, `DR-CON-authority`,
`DR-SEAM-adjudication-x-authority`, `DR-SEAM-llm-x-manifest`.

---

# Q3 — why on-subject survivors collapsed

## Verdict: CAUSE LOCATED — and the tranche's own explanation is refuted by the record

### First: the wander cap IS present and DID engage

`Config.SEED_PROBLEM_BUDGET_FLOOR = 0.5` (`config.py:295`), default, not
overridden by the ladder; `wander.py` present on the technique branch.

| root | share readings | throttle events | last share/floor |
|---|---|---|---|
| epoch 0 | 3 | 0 | 0.500000 / 0.500000 |
| epoch 1 | 12 | 5 | 0.454545 / 0.500000 |
| epoch 5 | 3 | 0 | 0.500000 / 0.500000 |
| epoch 6 | **4** | 1 | 0.333333 / 0.500000 |

Epoch 6 seq 648-649: `share 0.3333 below floor 0.5000` → throttled. So the cap
bound. It simply had almost nothing to bind over — see below.

### Off-subject work descends ENTIRELY from spawned problems

Accepted CONJECTURES only (import-role admission records excluded, per the
CLAUDE.md invariant and the correction RESULTS.md §7 already had to make),
addressed by problem lineage via `Harness(read_only=True).state.addr`:

| epoch | SEED lineage | `conn:` lineage | total | tranche's reported on-subject |
|---|---|---|---|---|
| 0 | **2** | 12 | 14 | 2 of 14 ✓ |
| 1 | **2** | 6 | 8 | 2 of 8 ✓ |
| 6 | **3** | 10 | 13 | 3 of 13 ✓ |

Exact match on all three. **"Off-subject" is precisely "descends from a
`conn:` problem"; not one off-subject survivor descends from the seed
question.** This confirms PARKED P9's correction — the scheduler
*commissions* rather than competes — at artifact-addressing level rather than
problem-count level.

### The actual cause of epoch 6's collapse: a budget-denial spin

Per-cycle attribution of epoch 6's 24 registered cycles, from the `cycle`
heartbeat Measures and the `llm` fields between consecutive heartbeats:

| cycle | heartbeat label | llm calls | tokens |
|---|---|---|---|
| 0 | `question-9e8800977c3e…` (seed) | 26 | 259,995 |
| 1 | `disc:question-9e8800977c3e…` | 0 | 0 |
| 2 | `conn:0a89b2b812ae` | 40 | 272,699 |
| 3 | `question-9e8800977c3e…` (seed) | 19 | 239,788 |
| 4 | `simulation-request:sha256:295ce6b0…` | 0 | 0 |
| **5–23** | `simulation-result:sha256:b5a7f812…` — the SAME crashed package, **19 times** | **0** | **0** |

Every one of cycles 5–23 has an identical five-event shape (seq 835-842 is
representative):

```
Measure  ["cycle","5","simulation-result:sha256:b5a7f812…"]
Control  [<work sha>, "conjecture:911d52d009af…"]
Control  [<work sha>, "budget-denied:token-budget"]
Measure  ["dropped-call","token budget denied transactional work <work sha>"]
Measure  ["allocation.seat-truncation.v1", …] ×4
```

Census: epoch 6 carries **19 `dropped-call` events and 40
`budget-denied:token-budget` occurrences**. Epoch 0 carries 2 budget-denied
and 0 dropped-call.

**Epoch 6 did 4 working cycles, not 24.** It spent its token budget in cycles
0–3 (772,482 of 800,000), then burned 19 cycles re-attempting one conjecture
call against a dead simulation package, each denied at the reservation, until
the CYCLE budget reached 24 and the run terminated `budget_exhausted`.

The mechanism is `scheduler/scheduler.py:1822-1824`:

```python
except (SchemaRepairError, EndpointError, WorkBudgetDenied) as error:
    self._drop(error)
    return True          # "a capability step happened" -> cycle consumed
```

`return True` sends control back to `:2052-2053`
(`if self._simulation_capability_step(): self._cycles += 1; return`), which
increments the cycle and returns **before** `_select_problem()` at `:2055`.
Nothing breaks the loop, because a denied reservation is not a stop condition
on this path.

### What this refutes

`RESULTS_EPOCH6.md` §3 reads the on-subject fall (47 % → 23 %) as the run
*"spending itself on whether the experiment was worth running rather than on
producing more variants."* The record does not support that: the run spent
cycles 5–23 producing nothing at all, with zero provider calls. The fall in
survivors is a consequence of having four working cycles, not of deliberation.

`RESULTS_EPOCH3.md` and `RESULTS_EPOCH6.md` both report **"24 of 24 cycles"**
as a headline. For epoch 6 that number counts 19 no-op cycles. Every
per-cycle comparison in the tranche between epoch 3 and epoch 6 is affected.
(Epoch 3's root is not committed, so whether it has the same shape is
UNDETERMINED — see the residue.)

Epoch 1, by contrast, is clean: 12 heartbeats, all naming real problems.

### The secondary finding: the cap cannot see capability cycles

`_disclose_wander`'s docstring (`scheduler.py:1229`) promises *"the reading
every cycle"*. Epoch 6 recorded 4 readings across 24 cycles — exactly the 4
cycles that reached `_select_problem`. The capability paths emit their own
`cycle` heartbeat (`scheduler.py:1802`, `:1950`, `:2030`) and return before
selection, so:

- the cap is **not consulted** on capability cycles, and
- `_cycles` increments on them (`:2053`) while `_seed_cycles` (`:1226`) cannot,

so the seed-lineage share is computed against a denominator counting cycles
the seed lineage could never have won. On this record the bias is
conservative (it makes the cap throttle sooner), but the reading is not the
quantity the cap's own documentation describes.

Map: `DR-CON-scheduler-ranking`, `DR-SEAM-capabilities-x-rules`,
`DR-INV-signal-contract`, `DR-SEAM-llm-x-scheduler`.

---

# Q4 — the two terminals, the zero-token surface, and the lifecycle contradiction

## Q4a — P2/P3: CAUSE LOCATED, and P2 understates the problem

### P2's diagnosis is confirmed, and is narrower than the truth

P2 says "one condition, two terminals". The record and the code say **one
condition, at least four in-run dispositions**, producing two terminals plus a
silent spin.

`WorkBudgetDenied` is raised once, at `workflow/transaction_service.py:402`
(defined `workflow/transaction.py:691-696`, message *"token budget denied
transactional work {work_id}"*). Its handlers disagree:

| site | disposition | observed outcome |
|---|---|---|
| `rules/crit.py:471-472` | `except WorkBudgetDenied: raise` | **epoch 0's death** |
| `scheduler.py:1822-1824` | `_drop(error); return True` | **epoch 6's 19-cycle spin** |
| `scheduler.py:2350-2364` | record diagnostic; `continue` | problem skipped |
| `scheduler.py:768-771` | `return` | advisory review skipped |

Others exist at `rules/conj.py:1908`, `informal/trial.py:174`,
`workflow/repair_transaction.py:382`.

**Both terminals confirmed against the roots that exhibit them:**

- Epoch 0, seq 536-537: the denial lands on a **criticism** work item
  (`criticism:32cc19d8…`), hits the `raise` at `crit.py:471`, and becomes
  `run-stop.json` `reason: operational_failure` at cycle 2 (seq 538).
- Epoch 6: the denial lands on **conjecture** work items inside the
  simulation-result path, is caught at `scheduler.py:1822`, and the run ends
  `budget_exhausted` at cycle 24.

So which terminal you get depends on **which seat's work item happens to
request the next reservation** — not on anything about the budget condition
itself. P2's parked prompt asks the right design question ("is a denied
reservation on an exhausted budget an OPERATIONAL failure at all?") but is
scoped to two paths and does not know about the spin, which is the more
expensive failure of the two: it silently converts a token-exhausted run into
a run that *reports a full cycle count*.

### P3 confirmed on two roots

`run-status.json` carries `token_spend: 0` on **both** failure-terminal roots
(epoch 0, budget 600,000; epoch 5, budget 800,000), while the completed roots
carry real figures. `application/results.py:172` reads the stored total
(`status.get("token_spend", …)`) and `:510` prints it. P3's prompt already
names the fix pattern (`_adjudication` in the same file derives its counts by
walking the log) and the boundary (fix the reader, never back-fill a committed
root). **P3's existing prompt fully covers what I found.**

### Do P2/P3's parked prompts cover it?

- **P3 — yes, fully.**
- **P2 — partially.** It covers the two-terminal disagreement. It does not
  cover the swallow-and-spin path, which needs its own end state: a denied
  reservation must not be able to consume a cycle indefinitely. New prompt
  filed as **A2** in this tranche's PARKED.md.

## Q4b — P5/P6: CAUSE ESTABLISHED, and it implicates the operations-parity law

Measured directly on all three roots via
`Harness(root, read_only=True).workflow_state`:

| root | `terminal_lifecycle_decision` | `lifecycle_decisions` |
|---|---|---|
| epoch 0 | `None` | 0 |
| epoch 1 | `None` | 0 |
| **epoch 6** | `None` | **0** |

`runtime/continuation.py:364` raises `CONTINUE_TYPED_STOP_REQUIRED` in the
`else` of `if terminal is not None: … elif current_resume is not None:` — so
it fires exactly on this state.

Meanwhile `deepreason results` on a **copy** of the epoch 6 root prints:

```
stands at a valid typed terminal: yes (terminal epoch 0)
stop reason is resumable: yes
ready for `deepreason amend` / `deepreason continue`: yes
```

`results` computes readiness from the stop record's reason against
`RESUMABLE_STOP_REASONS` (`workflow/lifecycle.py:28`), a different source
from the one `continue` consults. Neither surface reads the other.

**Extension to P6:** P6 measured this on epoch 1 and P-R1. It holds on
**epoch 6, the newest and cleanest root in the tranche** — 24 cycles,
`verify_root` 0 violations, `state: completed`. The operator's 2026-08-13 law
("every configuration that compiles gets the same lifecycle") is therefore
false in practice for every root this tranche produced, including the one it
delivered. P6 already carries the offline reproduction and the correct
end state; it remains the highest-value parked prompt and needs no rewrite.

**P5 is real and unchanged**, and P6's fix shrinks its blast radius exactly as
P5 already states. I did not re-run P5's amend probe: it is a WRITE, and
RESUME_PROBE.md already established it experimentally. Cited, not re-derived.

Map: `DR-SEAM-harness-x-workflow`, `DR-SEAM-llm-x-workflow`,
`DR-SUB-application`, `DR-CON-run-identity`.

---

# Q5 — the design gap, and the two cite-only items

## Q5a — P9: CAUSE LOCATED, and sharper than P9 states

**Confirmed: no path exists.** `run-stop.json` carries `new_problems: 0` in
**all four roots**. Every problem in every root is `seed`, `conn:`,
`research:` or `disc:`, spawned mechanically from an existing artifact by
`rules/spawn.py`, whose entire problem vocabulary is fixed at authoring time
(`spawn.py:80, 104, 141, 172, 186, 222`). No rule takes a criticism and emits
a reformulated question. Amendment epochs reshape a question only by operator
act. P9's census is correct.

**What P9 does not say, and it matters for the fix:** the ontology *already
has* the trigger. `ontology/problem.py:20-30`:

```python
class SpawnTrigger(str, Enum):
    SEED = "seed"
    # INERT VOCABULARY: producers = 0. No code path mints a problem with
    # this trigger -- `scan_spawns` stopped on refutation (H1, Rung 3a) ...
    # The member is retained only so pre-v2 roots still parse on replay;
    # its presence asserts no producer and licenses no new one.
    SUCCESSOR = "successor"                    # retained for replay only
```

So the capability P9 wants was **built, then deliberately decommissioned**,
and the decommission is guarded by a source scan
(`tests/test_decommissioned_pipeline_stays_out.py`). This changes the shape of
the work: the smallest seam is not "invent a new problem kind" but "re-arm
`SpawnTrigger.SUCCESSOR` with a producer, and satisfy the H1 reason it was
removed" — H1 being *a failure redirects attention, it does not spawn*, the
same principle `premises.py:630-633` cites for the premise channel.

That is a finding, not a design. The design question P9's prompt already
poses first — what is the TRIGGER, given that attacks target artifacts and
not problems — is unchanged and still has to be answered before any producer
can be written.

Map: `DR-CON-problem-layer-lifecycle`, `DR-SUB-ontology`, `DR-SUB-rules`,
`DR-INV-frozen-surfaces` (problem identity feeds run identity).

## Q5b — P7: the retry policy, and a correction to the parked claim

**Located:** `llm/endpoints.py:15` — `_RETRYABLE_HTTP = {429, 500, 502, 503,
504}`. A 429 quota refusal is classified as a transient transport fault.

**Correction — P7's parked text says "confirm no typed backoff bound
exists". A bound does exist.** `llm/endpoints.py:16` defines
`_BACKOFFS = (2, 4, 8)` and `request_with_retries` (`:51-70`) is a bounded
ladder: at most 4 attempts, ~14 s of sleep, then
`EndpointError("transport failed after retries: …")`.

The arithmetic confirms this is the whole explanation: 80 cases × ~14 s ≈ 19
minutes, against the 18 minutes epoch 2's qualification actually took
(10:43:39 → 11:01:55). **The 18 minutes is the bounded per-call retry
multiplied across the battery, not an unbounded ladder.**

So P7's defect is exactly two things, both already in its prompt: the
**classification** (an account-level refusal treated as transient, with no
battery-level short-circuit) and the **legibility** (`:59-60` preserves the
HTTP code for *non*-retryable errors; the retry-exhaustion message at `:70`
stringifies it into prose, and the typed record stores `ENDPOINT_ERROR`).
P7's prompt should drop the "no bound exists" premise; a one-line amendment,
filed as **A3**.

## Q5c — P8: UNDETERMINED, as the record already says

Confirmed at `workflow/nonconjecture_recovery.py:1001-1002`:

```python
mode = payload.get("mode")
_authority(mode in {"patch", "full"}, "repair mode is invalid")
```

Epoch 5 `run-status.json`: `state: failed`, `stop_reason:
operational_failure`, `cycle: 2`, `message: "repair mode is invalid"`.
Epoch 6 exercised the repair path heavily on the same code — 85 `repair_scope`
and 32 `repair-authorization-is-single-leg` occurrences in its log — and
survived.

The record stands where P8 left it: **stochastic, two-run control.**

**The third observation that would settle it**, and its cost: the two runs
differ in nothing but chance, so a third *live* run is the expensive way to
learn it. The cheap way is offline and deterministic — drive
`scripts/cycle_soak.py` on the pt1 case with the repair path forced through
the discharge-pointer shape that killed epoch 5
(`/candidates/0/discharges/7/kind`), and assert `mode` at the
`nonconjecture_recovery.py:1001` boundary. If a payload can reach that line
with `mode` unset or outside `{patch, full}`, the death is a real defect and
"stochastic" is the wrong reading; if no reachable payload can, the two-run
control stands and the epoch 5 death needs a different explanation. Cost:
one soak run (~90 s offline, no provider, no credential) plus the
instrumentation to capture the payload — cheaper than any live epoch.

---

# HONEST RESIDUE — what remains UNDETERMINED

**1. Whether epoch 3 and epoch 4 also spun.** Their roots are not committed
on the technique branch, so the per-cycle attribution that exposed epoch 6's
19 no-op cycles cannot be run on them. This matters because
`RESULTS_EPOCH3.md`'s per-cycle cost comparison (the 62 % critic reduction)
and its 24-of-24 claim rest on cycles being working cycles.
*Cheapest measurement:* if those two roots exist anywhere on disk or in a
later commit of that branch, one `grep -c dropped-call` and one heartbeat
census settles both in under a minute. If they are gone, it is unrecoverable
and the epoch-3/4 per-cycle figures should carry the caveat.

**2. Whether the spin is reachable outside the capability path.** I traced one
`return True` handler (`scheduler.py:1822`) and one live instance. Whether
the other `WorkBudgetDenied` handlers can also consume cycles without
progress is a code question I did not exhaust.
*Cheapest measurement:* a soak with a token budget deliberately set below one
cycle's burn, asserting that the cycle count does not advance without
provider calls. Offline, ~90 s.

**3. Whether the critic would cite if the channel were attached to `case`.**
Q1 establishes the channel is unreachable from criticism, and that the critic
declined the two invitations it did receive. It does not establish what a
critic would do with an `evidence_refs` field on `case` — a contract change,
so this is unmeasurable without one.
*Cheapest measurement:* none offline. This is a change-tranche question, and
the honest statement is that M2 is currently unmeetable by construction, not
that models will not cite.

**4. Whether epoch 6's 19 spun cycles cost anything beyond the cycle count.**
Zero provider calls and zero tokens are on the record for them. Wall-clock
cost is not separable from the run's total from the log alone.

**5. P8, per Q5c above.**

---

## What I did NOT do, by scope

No fix, anywhere. No `src/`, `tests/` or `docs/` change (diff pasted at the
top). No run edited, amended, continued or relaunched. No provider call and no
credential requested. One probe was blocked by the environment's classifier —
running `deepreason continue` against a *copy* of the epoch 6 root — and I did
not work around it; the code trace at `continuation.py:364` plus the measured
`terminal_lifecycle_decision=None` plus RESUME_PROBE.md's existing experiment
settle that point without it.
