# Parked — found during this tranche, deliberately NOT fixed here

A defect found mid-change is PARKED, not fixed (`dr-change-orchestrator`
scope contract). Each entry is written for its future runner at park time: one
line of WHAT, then a ready-to-send prompt, so the follow-up costs the operator
a paste rather than an authoring session.

---

## P1 — a 1-cycle run stops un-continuable, while its own record says it is resumable

**What.** `deepreason reason --cycles 1` terminates `budget_exhausted` carrying
`terminal_lifecycle_refusal: STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`
("2 outstanding work items, 0 unconsumed bound calls"), and every subsequent
`deepreason --root R continue --budget cycles=1` is refused
`CONTINUE_TYPED_STOP_REQUIRED`. The same `results --json` payload reports
`"stop_reason_resumable": true`. So one record says the stop is resumable and
the operation that would resume it refuses.

**Why it is not cosmetic.** The operator's law of 2026-08-29 (CLAUDE.md,
verbatim: "clean stop. with an assurance that continuing is possible. Too often
an operational failure overlooks securing enough checkpoints to allow relaunches
or forgets to ensure continuing is possible that trigger corrupted stops") makes
"every terminal leaves checkpoints sufficient for relaunch" a law, and makes a
stop that cannot assure continuability a defect in itself. This looks like
exactly that case, on the ordinary managed path, with no exotic configuration.

**Evidence, committed in this tranche.**

- root: `experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/retired-1cycle-run-292f964edb58e58ef0e7d957f29bac55`
  (retired by rename, contents never edited)
- `progress.jsonl` last line: `cycle 1`, `state completed`,
  `token_spend 94361` against `token_limit 400000`, `accepted 0`, `refuted 0`,
  `stop_reason budget_exhausted`,
  `terminal_lifecycle_refusal STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`
- driver log: `runs/m1_h0.log`, the three `CONTINUE_TYPED_STOP_REQUIRED` / `rc=1`
  lines at 01:12:57, 01:13:10, 01:13:25
- the cycle itself SUCCEEDED: 40 artifact objects, 18 claim-bearing conjectures
  on the seed problem, 3 schools, D4 0.936, D5 0.276

**What it cost here.** The M1/M3 arms were designed as `reason --cycles 1` plus
three `continue` steps so history could be re-rendered between cycles. That
design does not run. The arms were redesigned to a single `--cycles 4` call with
the history seeded once beforehand from a completed control root — which is
closer to the window instruction's own wording ("rendered OFFLINE from the
record") and is what `runs/arm.sh` now does. No harness code was touched.

**Not investigated, and stated so the next runner does not inherit a guess.**
Whether the refusal is correct and the `stop_reason_resumable: true` is the bug,
or the reverse; and whether `--cycles 1` specifically leaves the two work items
outstanding or whether any cycle count does.

**ONE SUB-QUESTION IS NOW ANSWERED, from this tranche's own evidence.** The
third open item asked whether a four-cycle run terminates the way the one-cycle
run did. IT DOES. The completed M1-H0 control
(`home-default/runs/run-fe00609058e10605590206d51ab2b7a0`) ran all four cycles,
reached `state: completed` with `stop_reason: budget_exhausted` and exit code
0 — a clean, successful run by every other measure, 47 admitted conjectures —
and its terminal STILL carries
`terminal_lifecycle_refusal: STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`.

So the refusal is NOT an artifact of a truncated one-cycle run. It attaches to
an ordinary successful managed run at its natural budget terminal. That
narrows the fork sharply and raises the stakes: under the operator's 2026-08-29
law every terminal must leave checkpoints sufficient for relaunch, and this is
the ordinary case, not an edge one.

### Ready-to-send prompt

```
Route: deepreason-orchestrator (defect).

GOAL: one bounded question — does a managed `deepreason reason --cycles N` run
leave a terminal that `deepreason continue` will accept, and if not, which of
the two typed records is wrong?

The record says both things at once. On run
experiments/2026-09-03-change-provenance-history-channel/runs/home-default/runs/
retired-1cycle-run-292f964edb58e58ef0e7d957f29bac55 (committed, read-only;
open it with Harness(root, read_only=True) — a writable open repairs and so
destroys the evidence):

  - run-status/progress: state=completed, stop_reason=budget_exhausted,
    terminal_lifecycle_refusal=STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY,
    detail "2 outstanding work items, 0 unconsumed bound calls"
  - `deepreason results --json` on the same root: "stop_reason_resumable": true
  - three `continue --budget cycles=1` attempts: CONTINUE_TYPED_STOP_REQUIRED,
    rc=1 each (runs/m1_h0.log, 01:12:57 / 01:13:10 / 01:13:25)

Start at dr-diagnose and READ THE RECORD BEFORE THE CODE. The two outstanding
work items are the thing to identify first: which work items, issued in which
cycle, and why the stop did not drain or finalize them.

Frame it as a fork the record can decide, not as a fix to apply:
  W — the stop is genuinely corrupt (work items left outstanding that a clean
      terminal should have drained), and `stop_reason_resumable` is lying;
  R — the stop is legitimate and `continue` over-refuses, in which case the
      refusal predicate is the defect and the record is honest.

Then check whether this tranche's FOUR-cycle roots in the same directory
terminate the same way; if they do not, the cycle count is part of the cause
and that narrows W/R sharply.

AUTHORITY: the operator's 2026-08-29 law in CLAUDE.md — "clean stop. with an
assurance that continuing is possible ... checkpoints need to be hardned" —
makes a stop that cannot assure continuability a defect, so this is in scope
for a fix rather than a documentation note. Do NOT weaken the continue-side
integrity gate to get green: the same law says a tampered record must not buy
a resumable run.

END STATE: DIAGNOSIS.md naming one primary cause with record pointers, REPRO.md
with the smallest offline artifact, and either a FIX.md or a recorded finding
that the behaviour is correct and the resumable flag is what must change.
```

---

## P2 — `deepreason config` does not echo every `Config` field (minor, unblocked)

**What.** `deepreason --config <yaml> config` echoes `PACK_TOKEN_BUDGET`
correctly, which is what let this tranche's M2 guard work. Noted here only
because the guard was written after discovering that the OBVIOUS mechanism —
an environment variable — reaches nothing: `Config` carries no env reader, so
`DEEPREASON_PACK_TOKEN_BUDGET=12345` leaves `Config().PACK_TOKEN_BUDGET` at
2500 silently.

**Why it is worth a line.** Nothing is broken; the YAML path is the supported
one. But an operator or agent reaching for an env override gets no error, no
warning, and a run at the default — and in a sweep that produces arms which are
all secretly the control. Under the 2026-08-28 gates-with-warnings law, a knob
that is silently ignored is the shape the law exists to prevent, even though
this is a non-existent knob rather than a disabled gate.

**Disposition.** Not a defect in shipped behaviour; a documentation and
ergonomics finding. Folded into the next audit rather than given its own
tranche.


---

## P3 — NOT a defect: the 429 that cost M3-C0 its qualification was self-inflicted

Recorded here so a later reader does not mistake it for a harness fault, and so
the cost is not written off.

**What happened.** M3-C0's first attempt qualified at tier `shallow`, and
`deepreason reason` then correctly refused with `QUALIFICATION_TIER_SHALLOW`,
rc=1, producing no run root at all. The arm's log says "finished" while having
produced nothing.

**Why, from the record rather than from theory.** The retired doctor record
(`evidence-429/c0-unqualified-doctor.json`, kept by copy; the tier cache retired
by rename to `evidence-429/RETIRED-c0.tier.json`) gives the summary directly:

```
case_count 300, eventual_valid_count 283, pair_count 15,
qualified false, qualified_pair_count 11
```

and every one of the 17 failures across the 4 short pairs carries the same
failure code: **`ENDPOINT_HTTP_429`**. Not a capability failure, not a schema
failure, not a repair failure — `repair_count` is 0 and `alias_failures` is 0.
The shallow-fitness battery that ran afterwards passed 6 of 6 first-pass, which
is why the tier landed at `shallow` rather than `unqualified`.

**Cause, owned rather than attributed.** Five provider workloads were running
against one endpoint at that moment: two intended arms plus three
`deepreason qualify` processes orphaned from the first arm design, one of which
was qualifying `home-c0` — the very home whose qualification failed — at the
same time as the legitimate one. That is the monitor's error in launching eight
arms concurrently and then not reaping the children when the drivers were
killed.

**Disposition: no fix, no tranche.** The harness behaved correctly at every
step. It rate-limited, recorded the typed failure code per case, degraded to a
tier the evidence supported, and REFUSED to run full reasoning on a shallow
qualification instead of quietly running something weaker. That last part is the
system working exactly as designed.

**What it cost, stated as a cost.** One full qualification battery on `home-c0`,
plus the four partial M2 batteries stopped at 268/271/270/262 of 360. All of it
attributable to over-concurrency, none of it to the code under study.

**What changed as a result.** `chain.sh` runs the remaining arms FULLY SERIAL —
one `deepreason` process at a time, verified by a wait-for-idle gate between
every step — which removes the cause rather than hoping a lower concurrency
number is low enough. The operator's cap of 3 is an upper bound; the chain uses
1.

**The transferable lesson, which is not about this tranche.** A qualification
degraded by transport pressure is INDISTINGUISHABLE, at the tier level, from a
model that genuinely cannot do the work: both produce `tier: shallow`. Only the
per-case `failure_code` separates them. Any future run that lands on an
unexpected shallow tier should read the doctor record's failure codes before
concluding anything about the model.


---

## P4 — NOT a defect either: M1-H0's operational_failure was the same 429 storm

Second casualty of the same cause as P3, recorded separately because the
SYMPTOM is completely different and a later reader chasing "atomic child is
terminally failed" would not think to look at P3.

**What happened.** M1-H0 ran cycles 0-2 successfully (73 accepted, 4 refuted at
cycle 3) and then died: `state failed`, `stop_reason operational_failure`,
message "atomic child is terminally failed", at 236,524 tokens of a 600,000
budget. `deepreason reason` exited 4. The terminal carries
`lifecycle_refusal: TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL` and
`stop_reason_resumable: false` — correctly, this time; the run really is not
resumable.

**Why, from the record.** In that root's own
`workflow-provider-attempt-v1` objects: **7 of 71 attempts have
`outcome: transport_failure`** with `usage_status: unknown`, and the string
`429` appears in 52 files of the root including `run-result.json`. The run was
in flight during exactly the window in which five provider workloads were
hitting one endpoint. Same cause as P3, different symptom: P3's victim was
mid-qualification so it degraded a tier; this one was mid-reasoning so it
exhausted a work item's repair ladder and terminated.

**Why it is not a defect.** `verify_root` on the failed root reports
`integrity_valid: true`, `security_valid: true`, `valid: true` — the record of
the failure is itself intact. The harness took transport failures, tried,
exhausted the ladder, and terminated with a typed operational failure rather
than pretending to have an answer. The one thing worth noting for a future
tranche is that `operational_checks_passed: false` with 18 operational findings
sits alongside `valid: true`, which is correct but easy to misread at a glance.

**Disposition.** Root retired by rename to
`home-default/runs/failed-429-run-fe00609058e10605590206d51ab2b7a0`, contents
never edited, and H0 re-run serially. The failed root is kept because it is the
evidence for this entry and for P1's open question about whether four-cycle runs
terminate the way one-cycle runs do.

**The judgement call, stated so it can be overruled.** The 3-cycle partial
record could have been used as M1's control rather than paying for a re-run.
It was not, because H0 is the CONTROL: comparing a control that died at cycle 3
against a treatment that completes 4 cycles measures the crash, not the
history. Under the operator's "prefer a run complete", a re-run that yields one
valid measurement beats two arms that cannot be compared. The cost is one extra
full run.


---

## P5 — every run in this tranche used the HASHING embedder, and CLAUDE.md says it should not have

**What.** `deepreason results` on the completed M1-H0 root prints
`embedder: hashing (hashing-128)`. The run's whole internal geometry — novelty,
similarity, scratch retrieval — ran on the zero-dependency hashing default
rather than the neural embedder.

**Why that is surprising rather than routine.** Four facts, each checked rather
than assumed:

1. `deepreason embedder-warmup` ran in this tranche's setup and reported
   `ready in 17.6s — nomic-ai/nomic-embed-text-v1.5`.
2. The weights are present: `/tmp/fastembed_cache` is 523 MB right now.
3. The embedder builds on demand right now: `build_embedder(Config().EMBEDDER_MODEL)`
   returns a `NeuralEmbedder` with dim 768.
4. `Config().EMBEDDER_MODEL` defaults to `nomic-ai/nomic-embed-text-v1.5`.

CLAUDE.md states the consequence those four should have: "`pip install -e .`
carries fastembed (core since 2026-08-16), so `EMBEDDER_MODEL`'s neural default
is armed by the ordinary install."

**Where it actually diverges, from the record.** The run's own compiled manifest
carries `EMBEDDER_MODEL: None` inside `engine_config_json` — the key is
PRESENT and its value is NULL, not the `Config` default. So
`ops.make_embedder`'s first branch fires (`if not config.EMBEDDER_MODEL: return
None`) and the Scheduler builds the hashing default.

**This is why NO `embedder-fallback` was recorded, and that part is correct.**
`make_embedder` records `embedder-fallback` only on the "set but unavailable"
path. This run took the "unset, so use the documented zero-dependency default"
path, which is silent by design. The log carries zero `embedder-fallback`
entries, which is the honest record of what happened — the degradation is
visible through `deepreason results`, as CLAUDE.md promises, just not as a log
measure.

**The fork, unresolved, and stated as a fork rather than a conclusion.**
  W — the compile path is wrong to null out `EMBEDDER_MODEL`, and the neural
      default should reach a managed run as CLAUDE.md says it does;
  R — nulling it is deliberate (determinism, or keeping a ~523 MB dependency
      off the qualification subject), and CLAUDE.md's sentence is the thing
      that has drifted.
Not investigated here. Which one holds decides whether this is a code defect or
a documentation defect, and they need opposite fixes.

**Effect on this tranche's measurements: none on the comparison, some on
interpretation.** Every arm compiles the same way, so H0/H1 and C0/C1 are
affected identically and the M1/M3 contrasts stand. Two things must be said in
RESULTS.md rather than left implicit: the harness's own novelty and
scratch-similarity behaviour in these runs is hashing-based, so anything the
runs did that depends on semantic geometry was done with the weaker
instrument; and the D5 figures reported by
`measure_diversity_per_problem.py` are computed OFFLINE with the neural
embedder, so D5 measures a geometry the runs themselves never used. That is not
wrong — D5 is a post-hoc measure of the claims — but the two must not be
described as if they were the same instrument.

### Ready-to-send prompt

```
Route: deepreason-orchestrator (defect) OR the docs lane, depending on which
fork survives — that is the first thing to settle, not something to assume.

GOAL: does a managed `deepreason reason` run get the neural embedder that
Config() defaults to, and that CLAUDE.md says the ordinary install arms?

Evidence to start from, all committed in
experiments/2026-09-03-change-provenance-history-channel/:
  - runs/home-default/runs/run-fe00609058e10605590206d51ab2b7a0/run-manifest.json
    -> json.loads(engine_config_json)["EMBEDDER_MODEL"] is None, key present
  - the same run's `deepreason results` output: "embedder: hashing (hashing-128)"
  - that run's log.jsonl: ZERO "embedder-fallback" measures (correct for the
    unset path, so do not treat their absence as a bug on its own)
  - /tmp/fastembed_cache present at 523 MB; build_embedder(Config().EMBEDDER_MODEL)
    returns NeuralEmbedder dim 768 on this container

Decide between:
  W — the compile path nulls EMBEDDER_MODEL wrongly; managed runs should get the
      neural default. Fix the compile path, and check the qualification subject
      digest price BEFORE changing anything, the compile-gap way.
  R — nulling is deliberate and CLAUDE.md's "armed by the ordinary install"
      sentence has drifted. Then this is a docs fix plus an ERRATA entry, and
      the code is correct.

Find WHERE the null is introduced first (compile_run_manifest and its config
echo), then decide. Do not "fix" it by defaulting the value at read time in
ops.make_embedder — that would hide the compile behaviour rather than settle it.

END STATE: DIAGNOSIS.md naming which fork the record supports, and either a
FIX.md with the digest price measured, or a docs/ERRATA.md entry correcting
CLAUDE.md.
```


---

## P6 — the scratch channel CANNOT deliver history to a multi-cycle run without code

Not a defect, and not a workaround-in-waiting: a structural fact that blocks the
window instruction's own prototype method. Established by three measurements,
each with its typed refusal.

**The instruction.** The M1 H1 and M3 C1 arms were to render a history section
offline and inject it "via the existing scratch channel or a pre-built pack
file", with no code under `src/`.

**Why the scratch channel cannot do it.**

1. **Before the run: no root, no scratch.** `deepreason scratch add` operates on
   a RUN ROOT. Against a home with no run yet it fails
   `MANIFEST_FILE_UNAVAILABLE at /run-manifest.json`. So a home cannot be
   pre-seeded.
2. **During the run: the root is locked.** `deepreason --root <root> scratch
   add` against a live run fails `SCRATCH_ROOT_BUSY: another operator owns this
   run root`. The reasoning process holds the operator lock for the run's
   duration.
3. **Between cycles: continue is refused.** The remaining route is
   `reason --cycles 1` (lock released, injection then works — verified rc=0 on
   an idle root), inject, `continue`. That is exactly the design PARKED P1
   killed: `CONTINUE_TYPED_STOP_REQUIRED`, and P1's update shows the blocking
   refusal attaches to four-cycle runs too, not just truncated ones.

So the three routes close in sequence, and they close for good reasons rather
than by oversight: a home is not a record, a live record has one writer, and a
stop that cannot assure continuation refuses to be resumed. Each refusal is the
system protecting the record.

**What this does NOT mean.** It says nothing about whether provenance history
helps a conjecturer. That question is untouched and still open. It says the
OFFLINE PROTOTYPE ROUTE is unavailable, so the question cannot be answered
without either a different channel or the Phase 2 implementation the spec
already describes.

**The one channel that does work pre-run, and its cost.** `deepreason reason
--attach FILE` admits a text or markdown document as EVIDENCE and binds it into
the run in one step. It works before the root exists, so no lock is involved.
Its cost is epistemic and not small: the scratchpad is declared
`advisory_non_grounding`, evidence is not. A history section admitted as
evidence can ground a claim, which is precisely what R1's "another type of
scratchpad" says it must not do. It also changes run identity via the dossier
digest, so a control arm would need a matched placebo attachment or the two
arms would differ in two ways rather than one.

**Disposition: STOPPED AND PUT TO THE OPERATOR.** The remaining choices spend
real tokens on a changed design, and the operator has said the budget is at
risk and that they prefer complete runs to many partial ones. Choosing
unilaterally between "re-run both M1 arms through the evidence channel with a
placebo control" and "report M1/M3 as not run" is a budget decision, not a
technical one.


---

## P7 — a NOT-LANDED attack leaves no trace in `att`, so two of the design's
## measures and one of its query limbs cannot be sourced the way SPEC.md says

Found by testing `measure_criticism.py` against committed roots BEFORE the M3
arms finished, so this is recorded ahead of the evidence rather than after it.

**The measurement.** Sustain rate — the share of attacked targets that end
REFUTED — is **1.000 on 6 of 6 roots**, across 630+ attacked targets:

| root | attacked targets | ending REFUTED | sustain rate |
|---|---|---|---|
| pc2-rematch | 220 | 220 | 1.000 |
| constructive-frontier | 163 | 163 | 1.000 |
| poietics-program | 104 | 104 | 1.000 |
| epoch3-second-lineage | 26 | 26 | 1.000 |
| this tranche's H0 | 6 | 6 | 1.000 |
| this tranche's M1 control | 7 | 7 | 1.000 |

**Why, from the map rather than from the numbers.**
`DR-CON-warrants-and-attacks` states the chain: an artifact carries a
registered `Warrant` naming a target, that carriage materializes an edge in
`att`, and the grounded extension refutes the target if the attacker is itself
accepted. So an edge is minted only by a WARRANTED attack. Criticism that fails
to warrant anything produces no edge at all — it is not recorded as a failed
attack, it is simply absent from `att`.

Stated precisely, because the difference matters: an edge does not GUARANTEE
refutation — the attacker must itself survive — so 1.000 is an empirical
saturation, not a theorem. But it is saturated in every committed record this
tree holds.

**Three consequences, one of which is a SPEC correction.**

1. **M3's sustain rate cannot discriminate.** Both arms will report 1.000. It
   is a saturated measure, and no critic configuration can move it.
2. **M3's re-raise rate is structurally n/a.** `PREREG.md` §3 defines a
   re-raise over objections against a target that was NOT sustained. There are
   no such targets. The measure is undefined wherever the sustain rate is 1.
3. **SPEC.md §2's `attacks(X)` limb is wrong as written.** It promises
   "objections raised against it, each with landed/not-landed". The
   not-landed half CANNOT be sourced from `att`, because a not-landed attack
   never enters `att`. Same for the anti-attractor render's second limb,
   "ATTACKS THAT WERE TRIED AND DID NOT LAND", which printed "(no failed
   attacks yet)" on every root — that was never a data quirk, it was the
   design asking `att` for something `att` does not hold.

**What SPEC.md must do about it.** Either source not-landed objections from the
criticism records themselves (which exist as artifacts whether or not they
warrant anything — `rules/crit.py` output survives as the raw completion and as
non-warranting artifacts), or drop the not-landed half from the vocabulary and
say so. The first is the useful one: an objection that was tried and failed is
exactly the anti-attractor information R8 asks for, and it is precisely what is
missing today. Not decided here.

**Effect on M1, stated so it is not over-read.** M1's treatment arm carried a
history whose "failed attacks" section was empty for this reason. Its measured
effect therefore comes from the REFUTED-claims limb alone. The anti-attractor
hypothesis was tested at half strength, and the half that was missing is the
half R8 most directly names.
