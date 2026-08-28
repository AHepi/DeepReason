# PARKED — the run-problems audit

This audit fixes nothing, anywhere. Each entry below is a ready-to-send prompt
for a future runner. Numbering continues the technique-run tranche's own
`PARKED.md` (P1-P9 live there, on branch
`claude/spec-to-code-technique-k5209o`); P10-P13 are new here, and the four
amendments correct or extend prompts that already exist there.

**Suggested order.** P10 first — it is the reason the run was not running the
operator's configuration, and every later measurement of "what this config
does" is suspect until it lands. Then P6+P6-A (a lifecycle operation is
disabled on every current run), then P13 (a deterministic run-killer), then
P11, then P3+P3-A, P12, P7+P7-A, P9+P9-A.

---

## P10 — five "everything on" switches never reach a manifest-launched run, and nothing says so

**What.** `run-config.yaml` set `JUDGE_SEATS_ENABLED: true`,
`ADJUDICATION_STATUS_AUTHORITY_ENABLED: true`,
`ENGAGED_CRITICISM_AUTHORITY: defended_trial`,
`LEGACY_CRITICISM_ENABLED: false` and `SCHOOL_SEATS_ENABLED: true`. The run
executed with all five at their OFF defaults, because the ladder launches with
`--run-manifest` and no `--config`, and `config_from_run_manifest` rebuilds the
Config from the manifest's engine-config echo — which drops all five by design.
`compile_notices` is empty. Two seats were qualified, at cost, for a road
closed four times over.

This is the fifth recorded instance of the shape `RUN_ANATOMY_SYNTHESIS` §3.2
item 6 named. It implicates the 2026-08-12 all-configurations law (a silent
revert is neither a refusal nor a typed disclosure) and the 2026-08-13
operations-parity law (a "rendering shell" that changes six behavioural
switches is not rendering the same run).

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect). Take this one FIRST: until it lands,
no measurement of "what this configuration does" can be trusted, because the
configuration under test is not the one that ran.

Goal, one sentence: make a manifest-launched run either carry the Config
switches its builder set, or DISCLOSE in a typed compile notice exactly which
ones it dropped and what value they will take at run time -- so that a
configuration can never silently become a different configuration.

Evidence, all committed:
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md section F-A
  experiments/2026-08-28-audit-run-problems/probes/q2_judge_reachability.json
      -> the reconstructed run-time Config beside the builder's, field by field
  branch claude/spec-to-code-technique-k5209o:
    experiments/2026-08-27-change-technique-run/run-config.yaml:157-169
      -> the five switches, all set ON
    experiments/2026-08-27-change-technique-run/run/run-manifest.json
      -> no criticism_policy key; engine_config_json carries 71 keys and none
         of the five; compile_notices []
    experiments/2026-08-27-change-technique-run/pt1_run.sh:120-124
      -> the launch: --run-manifest, no --config
    experiments/2026-08-27-change-technique-run/launch-epoch6.out:45-46
      -> "ok judge seat 0 / seat 1", two seats qualified for a closed road

Code:
  src/deepreason/run_manifest.py:4287 config_from_run_manifest
      -> Config.model_validate(json.loads(manifest.engine_config_json));
         every absent field takes its DEFAULT
  src/deepreason/run_manifest.py:2363-2432 _versioned_source_config_data
      -> the drop list, and its own justification for each pop
  src/deepreason/preparation.py:499-511
      -> the path that DOES wire criticism_policy from the same Config
  experiments/2026-08-27-change-technique-run/build_manifest_pt1.py:307-333
      -> the compile_run_manifest call that omits criticism_policy

Read the drop list's comments BEFORE designing. They are careful and they are
not wrong: each pop exists so that adding a Config knob does not move every
frozen manifest golden and every qualification subject digest. Two
justifications recur -- "its effect is already visible in the compiled
manifest's own criticism_policy" and "it lives on Config only, consulted at
dispatch sites". Both hold for a --config launch. Establish first, in writing,
whether both fail for a --run-manifest launch, and say which of the ~14 popped
fields are BEHAVIOURAL (change what the run does) versus IDENTITY-ONLY.

The design question to answer first, because it decides everything after: is
the echo the right carrier at all? A third road exists and may be the cheapest
-- leave the echo untouched (so no digest moves) and add a SEPARATE typed
disclosure block to the manifest naming every behavioural Config field that
was not carried and the default it will take. That preserves every golden and
still makes the silence impossible.

Do NOT fix this by adding the five fields to the echo without pricing the
digest movement first: that changes every qualification subject digest and
costs every home a ~14-minute battery.

Also settle, because it decides the blast radius (residue item 4 of the audit
report): does this affect every manifest-launched run, or only builders that
omit criticism_policy? Reconstruct the Config from every committed manifest on
main and diff it against its builder's Config. It is ~30 minutes offline.

End state: a manifest whose builder set a behavioural switch either carries it
or names it in a typed compile notice; a regression test drives
build_manifest_pt1.py's exact shape and asserts the notice; the P-T1 manifest
digest situation is stated explicitly rather than discovered at the gate; full
gate 0 failed; map moved in the same commit.
```

---

## P11 — the critic's citation channel is open on 5 of 98 dispatches and latches shut after one use

**What.** M2 ("criticism using the record's own numbers as ammunition") has
been UNMET in every epoch of two tranches. It was not missed; it was
unmeetable. The critic's only byte-checked citation path is a premise filing,
gated on a problem having accumulated >= 2 REFUTED candidates AND no
attribution already standing. Across four committed roots: 98 critic
dispatches, **5** carried the invitation, **5** carried the citable-block
legend. On the other 93 the seat was handed a wire field requiring a
12-64-character hex block id and shown no block ids anywhere in the prompt --
so null was the only lawful answer.

Worse than the threshold is the LATCH. In epoch 6 the invitation fired twice
(seqs 141, 180), an attribution was filed at seq 186, and the gate was shut for
the remaining 803 events. The run then established at **seq 779**, in surviving
conjecture `aadd39655456...`, that its own question was malformed -- 593 events
after the only channel for saying so had closed.

A registered live probe (16 calls, 60 769 tokens, `PREREG_LITE.md`) replayed
the one dispatch that saw the whole channel: 0/8 filled `premise_evidence` on
the verbatim prompt and 0/8 with a worked exemplar appended. So the prompt
surface is not the whole story either -- but the wiring is where the 93 live.

**Ready-to-send prompt:**

```
Route: dr-change-orchestrator (a design change, not a defect -- nothing is
broken; a channel is gated so tightly it cannot be exercised). Sequence AFTER
P10: the criticism authority this run executed under was not the one its config
named, and that must be settled before anyone tunes a criticism channel.

Goal, one sentence: make the critic seat's byte-checked citation channel
reachable often enough to be measurable, and stop it latching permanently shut
on the first premise filed.

Evidence, all committed:
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md section F-B
  experiments/2026-08-28-audit-run-problems/probes/q1_prompt_surface.json
      -> 98 critic dispatches, 5 shown the invitation, 5 shown the legend
  experiments/2026-08-28-audit-run-problems/probes/q1_invite_gate.py output
      -> max REFUTED on one problem: 1, 1, 3, 6 across the four roots
  experiments/2026-08-28-audit-run-problems/probes/q1_invited_replies.json
      -> what the seat returned on each of the 5
  experiments/2026-08-28-audit-run-problems/probes/live/SUMMARY.json
      -> the registered live probe: 0/8 control, 0/8 exemplar
  experiments/2026-08-28-audit-run-problems/PREREG_LITE.md
      -> frozen before the probe ran, including what it CANNOT establish

Code:
  src/deepreason/premises.py:625-645 premise_work_invited -- the gate
  src/deepreason/premises.py:68     PREMISE_INVITE_AFTER = 2
  src/deepreason/premises.py:638    the latch: any standing attribution closes
                                    the problem to further invitations forever
  src/deepreason/rules/crit.py:1268 _premise_invited_problem
  src/deepreason/rules/crit.py:1368 _check_premise_citations -- the ONLY
                                    producer of the premise-citation Measure,
                                    and it records NOTHING when refs is empty
  src/deepreason/rules/crit.py:1401 _file_attribution -- returns None uninvited
  src/deepreason/rules/crit.py:1283 _citable_blocks -- the legend, rendered
                                    only under the invitation

Read DR-CON-criticism-source and DR-SEAM-scheduler-x-rules before designing,
and DR-INV-frozen-surfaces first.

Three questions to answer explicitly, in this order:

(1) THE LATCH. premises.py:638 closes a problem to further invitations the
moment one attribution stands. On the evidence that is the binding constraint,
not the threshold: the run proved its own question malformed 593 events after
the channel closed. Should the gate reopen -- on a new refutation, on a new
attribution being refuted, on nothing at all? Say why, and price the cost of
re-asking (each invitation is a rendered legend in a critic pack).

(2) THE EMPTY-REFS SILENCE. crit.py:1368 returns () without a Measure when
premise_evidence is empty, so the record cannot distinguish "the seat was
invited and declined" from "the seat was never invited". Both read as zero.
The invited-and-declined case is real evidence about a seat and should be
typed. This is cheap and is probably worth doing even if nothing else here is.

(3) THE UNINVITED SCHEMA FIELD. On 93 of 98 dispatches premise_evidence sits in
the wire contract with no legend and no legal value. RUN_ANATOMY_SYNTHESIS
section 2.5 measured what models do with a required field they cannot satisfy
(255 of 257 fabricated); this field is nullable so they nulled it instead,
which is the good outcome. Decide whether the field should be ABSENT from the
contract when the invitation is absent, rather than present-and-unfillable.

Do NOT lower PREMISE_INVITE_AFTER as the whole fix. A threshold change without
(1) still gives one invitation per problem per run, and this audit's evidence
is that one is not enough to catch a criticism that arrives late.

Do NOT treat the live probe as showing the seat "will not cite". A null premise
is legal when the seat sees no malformed presupposition, and the probe cannot
separate that from refusal -- PREREG_LITE.md says so in advance. If you want
that separated, the audit's residue item 2 names the experiment: the same
replay with a deliberately malformed presupposition planted in the problem
text, ~40k tokens, where a correct seat MUST fill premise.

End state: a problem can invite premise work more than once under a stated
rule; an invited-and-declined dispatch is typed on the record; a regression
test drives a run where the channel opens after a late refutation; full gate
0 failed; map moved in the same commit.
```

---

## P12 — capability cycles bypass the wander cap while still moving its denominator

**What.** The wander cap (F3, 2026-08-26) was present in the P-T1 run and DID
bind -- 5 times in epoch 1, once in epoch 6. But in epoch 6 it was consulted on
**4 of 24 cycles**. `scheduler.py:2052-2054` returns from the cycle body when
`_simulation_capability_step()` handles the cycle, which is BEFORE
`_select_problem()` (where `wander.decide` runs) and before `_disclose_wander()`
-- while still doing `self._cycles += 1`.

So each of epoch 6's 20 simulation cycles advanced the seed-lineage share's
DENOMINATOR without advancing `_seed_cycles` and without consulting the policy.
Work that IS the operator's own experiment therefore dilutes the floor meant to
protect the operator's question, invisibly, and the run's last recorded reading
is 20 cycles stale.

Second, smaller: the same drop list P10 covers removes
`SEED_PROBLEM_BUDGET_FLOOR` and `ATTENTION_ALLOCATION_POLICY` from the manifest
echo (`run_manifest.py:2386-2387`). This run got the cap only because its
DEFAULTS are on. A configuration that deliberately set a different floor would
have lost it exactly as P10's five switches were lost.

**Ready-to-send prompt:**

```
Route: dr-change-orchestrator (a design question first, then a small change).

Goal, one sentence: decide how a capability cycle counts toward the seed
lineage share, and make the wander cap's reading reflect every cycle that
advanced the cycle counter.

Evidence, all committed:
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md section F-F
  experiments/2026-08-28-audit-run-problems/probes/q3_cycle_accounting.json
      -> epoch 6: 24 heartbeats = 19 simulation-result + 1 simulation-request
         + 2 seed + 1 disc: + 1 conn:, against exactly 4 wander readings
  experiments/2026-08-28-audit-run-problems/probes/q3_wander.json
      -> epoch 1's full share trajectory (12 readings, 5 throttles) beside
         epoch 6's four readings and single throttle

Code:
  src/deepreason/scheduler/scheduler.py:2052-2054  the early return
  src/deepreason/scheduler/scheduler.py:1802,1950,2030  the capability step's
      own cycle heartbeats -- which is why the bypass is invisible in a
      heartbeat census unless you read the problem id
  src/deepreason/scheduler/scheduler.py:1130-1149  wander.decide, stashed
  src/deepreason/scheduler/scheduler.py:1214-1222  _count_lineage
  src/deepreason/wander.py  the policy and its registry
  src/deepreason/run_manifest.py:2386-2387  the two knobs dropped from the echo

Read DR-INV-signal-contract and DR-CON-scheduler-ranking before designing.
wander.py's own module docstring states the strictest row of the contract it
lives under -- allocation touches EFFICIENCY, NEVER EVIDENCE -- and nothing in
this change may weaken it.

The design question to answer FIRST, because it decides the whole shape: a
simulation cycle is work on a proposal that was made under some problem. Should
it count as that problem's lineage, as neither, or not advance self._cycles at
all? Each answer is defensible and they are not equivalent:
  - count it to the proposing lineage: the floor then protects seed-lineage
    EXPERIMENTS as well as seed-lineage conjecture, which is arguably what the
    operator's question wanted;
  - count it to neither and do not advance the denominator: the share then
    measures scheduler cycles only, and reads honestly, but a run can spend 20
    cycles elsewhere with the floor none the wiser;
  - leave it as today: the denominator moves and the numerator cannot, which
    is the only option the audit can say is wrong, because it makes the reading
    mean something nobody chose.
Answer it as a policy question and record the answer, per
DR-REC-revise-allocation-policy -- a new policy in the registry may be the
right shape rather than an edit to wander_cap_v1.

Whatever you decide, the reading must be emitted on every cycle that advanced
the counter, so a reader can plot it. Today's record goes silent for 20 cycles
and a reader cannot tell silence from stability.

Sequence with P10: if P10 makes the two attention knobs reachable in a
manifest-launched run, say so here, because this change's testability depends
on being able to SET a floor rather than inherit one.

End state: every cycle that advances self._cycles either consults the policy or
is excluded from its denominator, by a stated rule; the disclosure is emitted
per cycle; a regression test drives a run with capability cycles and asserts
the share; full gate 0 failed; map moved in the same commit.
```

---

## P13 — the repair `mode` producer and its checker do not share a vocabulary (SUPERSEDES P8's prompt)

**What.** P8 parked "repair mode is invalid" as *stochastic, 2-run control*.
That reading is refuted. The producer's type
(`llm/repair.py:1505 V6RepairTurn.mode`) is
`Literal["initial", "whole_object_syntax", "patch"]`; the checker
(`workflow/nonconjecture_recovery.py:1002`) admits `{"patch", "full"}`. They
intersect in `patch` alone. `full` is accepted and emitted **nowhere** in
`src/`; `whole_object_syntax` is emitted constantly -- 36 of the 56 repair
payloads across three committed roots -- and accepted nowhere.

The check is reached for every repair-kind child recovered through
`atomic_recovery.py:68-71` and `nonconjecture_recovery.py:1194`. So the death
is DETERMINISTIC on payload shape: any `whole_object_syntax` repair child that
reaches a recovery path raises. What varies run to run is only whether a
recovery path is taken over such a child.

**Ready-to-send prompt:**

```
Route: deepreason-orchestrator (defect). P8's "stochastic" framing on branch
claude/spec-to-code-technique-k5209o is SUPERSEDED by this entry; read P8 for
the run history and this one for the cause.

Goal, one sentence: make the repair `mode` vocabulary a single shared type, so
a value the producer can emit cannot be a value the checker rejects.

Evidence, all committed:
  experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md section F-D
  experiments/2026-08-28-audit-run-problems/probes/q5_repair_vocabulary.py
      -> asserts both vocabularies against the live source AND all three
         records; exits 0 today and goes red if either moves. Run it first.
  experiments/2026-08-28-audit-run-problems/probes/q5_repair_payloads.json
      -> every repair payload in every root, with its mode and terminal
  branch claude/spec-to-code-technique-k5209o:
    .../failed-epoch5-run-456885c5.../run-result.json
      -> error_type NonConjectureRecoveryAuthorityError, "repair mode is invalid"

Code:
  src/deepreason/llm/repair.py:1505   the producer Literal
  src/deepreason/llm/repair.py:1612   where whole_object_syntax is emitted
  src/deepreason/workflow/nonconjecture_recovery.py:1002  the checker set
  src/deepreason/workflow/atomic_recovery.py:68-71  the live path that reaches
      the check (if preparation.task_kind.value == "repair")
  src/deepreason/workflow/nonconjecture_recovery.py:1194  the recovery path

Do NOT simply add "whole_object_syntax" to the set. That makes the symptom go
away and leaves two hand-maintained vocabularies that will drift again -- and
it leaves "full", a value nothing emits, sitting in an authority boundary. The
question to answer is which of the two is right: is the checker meant to admit
only the modes that carry authorized pointers (in which case
whole_object_syntax children should not reach it at all, and the caller is
wrong), or every mode the producer can emit (in which case the set should BE
the producer's Literal, imported, not retyped)? The payload evidence bears on
it: every whole_object_syntax payload in the record carries
authorized_pointers == [] and repair_index == 1, while every patch payload
carries a non-empty canonical pointer list. That is a real structural
difference and it probably decides the answer.

Also settle, cheaply, which call site epoch 5 took (audit residue item 3): a
stub-driven repro that forces a whole_object_syntax child through
recover_atomic_child_output, ~1 hour offline. That repro IS the regression test.

Related, and worth fixing in the same tranche: cycle_soak.py's D1 seam is
PARTIAL on every run because the deterministic stub always returns
schema-valid responses, so no gate has ever exercised the repair path at all.
A stub mode returning a schema-INVALID response on demand makes this whole
class reachable offline -- which is the same gap P4 names for budgets.

End state: one vocabulary, shared by type rather than by copy; "full" is either
emitted by something or gone; a regression test drives a whole_object_syntax
child through the recovery path; the soak can provoke at least one repair;
full gate 0 failed; map moved in the same commit.
```

---

## P3-A — amendment: the zero-spend defect is in the WRITER, not the reader

**Correcting the parked prompt, not the finding.** P3 (branch
`claude/spec-to-code-technique-k5209o`) is right that `deepreason results`
prints 0 for a run that spent 580 016 tokens. Its prompt sends the fixer to
`src/deepreason/application/results.py` and says *"the fix belongs in the
READER, not in the record."* Following that alone would leave the defect in
place.

The chain, confirmed end to end (AUDIT_REPORT.md F-E):

- `application/text_runs.py:1435-1447` — the SUCCESS terminal passes
  `token_spend=sum(event.llm.tokens for event in harness.log.read() if event.llm)`.
  It already walks the log, correctly.
- `application/text_runs.py:1466-1475`, `1479-1490`, `1533-1541` — the three
  FAILURE emits pass `token_limit` and **no `token_spend`**.
- `runtime/progress.py:55` — `token_spend: int = Field(default=0, ge=0)`.
  Omitting the kwarg ASSERTS zero; it does not leave a gap for a reader to
  detect.
- `application/results.py:172` — reads `status.get("token_spend", _absent(...))`;
  the key is present, so the absence sentinel never fires.

So the reader behaves correctly on a status file that states a false fact. Add
to P3's prompt:

```
Both halves, and say which is which:
  (a) WRITER. The three failure-path progress.emit calls in
      src/deepreason/application/text_runs.py (1466-1475, 1479-1490,
      1533-1541) omit token_spend, which runtime/progress.py:55 defaults to 0.
      The correct value is computed three lines away at text_runs.py:1442 on
      the success path. This is the fix that stops NEW roots lying.
  (b) READER. results.py cannot recover the truth for roots ALREADY committed
      with token_spend: 0, because 0 is indistinguishable from a real zero in
      the status file. For those, derive from the log -- the pattern
      _adjudication in the same file already uses.
P3's boundary still holds: do not back-fill token_spend into a committed root.
A root is evidence and is never edited.

This is a recurrence, and the prior measurement belongs in the docstring:
docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md organ 10 records 18 of 54 roots
reporting token_spend: 0 while the log and the accounting agree on a real
figure.
```

---

## P6-A — amendment: P6 is not fixed, and the swallow has an address

P6 (branch `claude/spec-to-code-technique-k5209o`) named the cause correctly.
Three additions:

1. **A fresh instance on today's `main`.** Epoch 6 (`run/`, run
   `456885c5...`) completed 24 of 24 cycles on 2026-08-28, after the
   execution-safety tranche merged, and reproduces exactly: `budget_exhausted`,
   `results` says resumable, **zero lifecycle decisions**, so `continue` would
   raise `CONTINUE_TYPED_STOP_REQUIRED`.
   Evidence: `experiments/2026-08-28-audit-run-problems/probes/q4_lifecycle_surfaces.json`.

2. **Outstanding-work counts, measured.** P6 reported 3 for epoch 1 and 0 for
   the P-R1 control. Epoch 6 carries **9**. The condition is not shrinking.

3. **The swallow's address.** P6 says the refusal "is SWALLOWED" without
   naming the line. It is `application/text_runs.py:245-246`:

   ```python
   except ValueError:
       return None
   ```

   catching `workflow/lifecycle.py:217`'s
   `ValueError("STOPPED refuses unfinished workflow authority")`, then falling
   through to the bare stop record. A `ValueError` is also what a dozen other
   things raise, so this handler cannot tell the lifecycle refusal from a bug —
   which is worth saying in the fix: a typed refusal deserves a typed except.

---

## P7-A — amendment: a backoff bound DOES exist, and P7's evidence pointer is dead

Two corrections to P7 (branch `claude/spec-to-code-technique-k5209o`).

1. **A typed backoff bound exists.** `llm/endpoints.py:15`
   `_RETRYABLE_HTTP = {429, 500, 502, 503, 504}` and `endpoints.py:52-71
   request_with_retries` apply a bounded `2s/4s/8s` ladder per call. What is
   missing is one level up: `cli/doctor.py:535-560` runs 80 cases × 4 pairs,
   each exhausting its own bounded ladder, with **no cross-case
   circuit-breaker** on an account-level condition. The 18 minutes is 80
   bounded ladders, not one unbounded one — which changes the fix from "add a
   bound" to "add a breaker".

   Worth deciding in the same tranche: whether 429 belongs in `_RETRYABLE_HTTP`
   unconditionally. A rate limit clears in seconds; a session usage limit does
   not, and both arrive as 429.

2. **The legibility half is confirmed, with an address.**
   `cli/doctor.py:415-425 _failure_code` reads `getattr(error, "code", "")`
   first; `EndpointError` (`endpoints.py:42`) carries no `code`, so the
   function normalises the CLASS NAME to `ENDPOINT_ERROR`, and
   `ProductionContractCaseResultV1` has no field for the provider's message at
   all. The status and body are not lost late — they are never captured.

3. **P7's cited evidence no longer resolves.**
   `experiments/2026-08-27-change-technique-run/qualify.json` was overwritten
   by a later successful battery and now reads `eventual_valid_count: 80,
   qualified: true`. Use this committed instance on `main` instead:

   ```
   experiments/2026-08-25-change-constructive-frontier/qualify-attempt2-VOID-agent-error.json
       -> case_count 80, eventual_valid_count 0, re_exercised_pair_count 3,
          140 failure_code ENDPOINT_ERROR
   ```

---

## P9-A — amendment: the ontology already has the slot, and the seam has a name

P9's census and conclusion stand, re-confirmed: `rules/spawn.py`'s whole
problem vocabulary is `disc:` (80), `ra:` (104), `debt:` (141), `conn:` (172),
`research:` (186), `integ:` (222), and none consumes a criticism's content.

Two things P9 did not have, both of which change the shape of the change:

1. **`SUCCESSOR` already exists, with zero producers.**
   `src/deepreason/ontology/problem.py:20-37` declares
   `SUCCESSOR = "successor"` and comments it as *"INERT VOCABULARY: producers
   = 0 … its presence asserts no producer and licenses no new one"*, enforced
   by a source scan (`tests/test_decommissioned_pipeline_stays_out.py`). So a
   successor rule is a REVIVAL of a declared trigger, not a new kind — which
   matters, because P9's warning that "problem ids participate in run identity"
   applies differently to a trigger that already exists in the enum.

2. **`AUDIT_CRITIC` is the near-miss worth studying first.**
   `problem.py:34` declares `AUDIT_CRITIC = "audit-critic"` — the one trigger
   that reacts to criticism behaviour. It audits the CRITIC, not the QUESTION,
   and it is the trigger that took 41.2% of P-C1's budget
   (`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` §2.1). Any successor rule should
   be designed against that precedent, including its cost.

3. **The smallest seam, map ids only.** `DR-SEAM-ontology-x-rules` is where the
   trigger vocabulary meets the minting rules and is the smallest attachment
   point. Read with `DR-CON-problem-layer-lifecycle`;
   `DR-CON-scheduler-ranking` owns the seed's rank guarantee;
   `DR-CON-criticism-source` owns what a criticism may address;
   `DR-CON-run-identity` because problem ids feed run identity; and
   `DR-INV-frozen-surfaces` first.

4. **P11 is the same wound from the citation side.** In epoch 6 the run
   established at seq 779 that its question was malformed, 593 events after the
   premise channel — the only typed way to say so — had latched shut at seq
   186. Sequence P11 and P9 together, or at least read each before designing
   the other.
