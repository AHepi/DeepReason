# Why Only One Agent Has Driven This Pipeline

*2026-07-05. Question under investigation: the pipeline has been driven
successfully by one operating agent (Fable-class sessions); other models
struggle. Why? Evidence: (a) the repository's own documents and commit
history, (b) this session's operational record, (c) live operator probes
of four engine models (transcripts: experiments/results/operator_probes.json
— three scenarios x {deepseek-v4-flash, v4-pro, laguna-m.1, laguna-xs.2}).*

## Ranked causes

### 1. Until the remediation, the pipeline was not drivable end-to-end
The shipped config could not complete a run through its own entry points:
`model: auto` was unresolved outside one script (every call rejected, "run
completes with zero conjectures and no clear error"); `token_budget=0`
disabled metering; a `content: null` response crashed the scheduler; 85%
of trial spend was invisible to the log; one transient malformed-200
killed whole collections. An agent driving the pre-remediation pipeline
experienced failures that LOOK like success (exit 0, empty frontier) and
successes that look like failures (budget stops), with the truth only in
the log. The single successful driver is the agent that stopped driving
and fixed the road first (30+ commits on this branch). Any model gets
materially further today than any model could have gotten before.

### 2. The failure modes are silent; the success criteria are inverted
Demonstrated live during the probes themselves: with default settings,
the two STRONGEST engine models (v4-flash, v4-pro) returned EMPTY strings
— default reasoning burned the entire completion budget before any
content, and nothing errored. Operating this pipeline means treating
surface signals as unreliable: empty frontiers can be correct outcomes
(occult suite), refutation is progress, budget stops are graceful, and
accounting truth requires reconciling the meter against the log (which is
how three real bugs were found). Models act on the surface signal.
`narrate()` (views/narrate.py) was added precisely to close this gap.

### 3. The load-bearing mechanics are unwritten
Probe A (your favorite artifact is REFUTED by a critic you believe is
wrong): with AGENT.md's rules IN CONTEXT, all four models still missed
the harness's central mechanic — **a wrong critic is answered by
criticizing the critic** (attack its validity node; fund cycles; the
grounded adjudication reinstates the target). Zero of four mentioned it.
Two (flash, pro) used `appellate_rule` with calibration-flavored wording
but expected the ruling to re-adjudicate the existing verdict (it only
calibrates FUTURE trials via the precedent slice). AGENT.md documents
prohibitions — fossils of past operator failures ("there is no tool that
overrides them — do not look for one") — but not the positive playbook.
The "what to do instead" lives in a 1,300-line normative spec and in
commit history.

### 4. The epistemology cuts against assistant instincts
The harness strips the operator of the two moves tuned assistants reach
for first: making the preferred answer win, and cleaning up "mistakes."
laguna-m.1's probe-A answer is the instinct verbatim:
`appellate_rule(case_id, holding="refuted", ...)` — "formally challenge
the critic's case by asserting that its refutation is incorrect." Notably
the SMALLEST model (laguna-xs.2) complied best on this probe — it defers
to the provided rules where mid-tier models assert judgment. Capability
does not monotonically improve operator compliance; it increases the
willingness to fight the harness before the context to understand it.

### 5. Driving is a long-horizon discipline, not a chat skill
The successful operating pattern was: pre-register -> run in background ->
reconcile accounting -> triage -> amend the registration -> resume
checkpoints across failures, over hours, on one branch, with idempotent
roots. Much of "models struggle" is harness-of-the-operator, not weights:
an agent without persistence, resumable background jobs, and the habit of
auditing its own results cannot drive this pipeline regardless of model
quality.

## What the probes got RIGHT (the encouraging part)
When the answer is written in the rules the models follow it: all four
correctly read a budget stop as graceful/consistent/same-root, and all
four correctly read an empty frontier on a hostile problem as SUCCESS.
Compliance is a documentation problem more than a capability problem —
except for the unwritten mechanics (cause 3) and the instinct to
relitigate verdicts (cause 4).

## Recommendations (not yet applied)
1. AGENT.md: add the positive playbook — "if you think a critic is wrong:
   read `why`, then fund cycles / register criticism against the critic's
   validity node; reinstatement is computed, never granted" — plus one
   worked example of an appellate ruling and what it does NOT do.
2. Surface truth in-band: `run_cycles` responses should carry the
   meter-vs-log reconciliation and a short `narrate` tail so silent
   failure modes become visible in the tool result itself.
3. Operator-facing configs/examples should pin `reasoning` and generous
   `max_tokens` for engine calls made by operators (the empty-string
   failure is entirely preventable).
4. Re-run these probes after (1)-(3); the deltas measure whether the gap
   was documentation or capability.
