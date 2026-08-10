# Errata — the less-capable-executor infrastructure

Started 2026-08-03 at the operator's request ("this process needs to go in
its own errata. But wait for the results and keep monitoring progress.").

## Scope

This ledger tracks THE PROCESS, not the codebase: the infrastructure built
on 2026-08-03 to let a less capable model operate DeepReason —

- `.claude/skills/dr-ask-the-right-question/` (question discipline),
- `.claude/skills/dr-drive-harness/` (driving manual + the "Calibration
  for less capable executors" block),
- `.claude/skills/README.md` (the workflow index),
- `docs/HANDOVER_2026-08-03.md` (the Sonnet-calibrated modularisation
  program, rungs 1–7).

An entry records an infrastructure claim that an executor session's RECORD
showed to be wrong, misleading, silent where it mattered — or
load-bearing-and-correct (a gate that fired as designed is evidence too,
and belongs here as much as a failure). Corrections to ordinary committed
documents stay in `docs/ERRATA.md`; defects in `src/` go to a
`deepreason-orchestrator` tranche, never here.

## Entry discipline (inherited from docs/ERRATA.md)

Append-only; never rewrite an entry — a correction to a correction is a
new entry. Evidence pointers only: every claim cites the executor
session's committed artifact (tranche ledger, commit hash, pasted output,
run root), never an impression of how the session "went". Entries are
written by whichever session holds the evidence: the executor session
itself (per the feed-instruction in `docs/HANDOVER_2026-08-03.md`) or the
monitoring session reviewing its record.

Single-writer rule (operator-directed 2026-08-03, superseding the
short-lived two-writer numbering rule below): this ledger has ONE
writer, the monitoring session, `X<n>` sequence. The executor records
its observations in its own tranche artifacts; the monitor carries what
matters here. Historical note — the two-writer period produced two
executor-authored entries that stand as written per append-only
discipline: the pre-rule collision cited as **X5-E** (commit
`4e4c26e8`) and **XE1** (commit `de2b5826`); the `XE<n>` id space is
retired at XE1. Original numbering rule, kept for the citations it
defined: monitor `X<n>`, executor `XE<n>` off its own checkout's tail,
neither renumbering the other, both sequences standing on merge.

## Entries

**X1 — the infrastructure's own deployment raced the executor.** The
first executor session branched (`claude/delivery-rungs-handover-m22sdy`,
merge-base `9a319c10`) from the handover-delivery commit — BEFORE this
ledger and the handover's feed-instruction were pushed (`ce3db17e`). The
executor therefore cannot follow an instruction its checkout never
carried; its findings land in `docs/ERRATA.md` instead (its E9). Not an
executor fault and not evidence against the skills — a sequencing gap in
the rollout of the monitoring layer itself. The monitor compensates by
reviewing the executor's artifacts directly.

**X2 — first on-course observation (rung 1, in progress).** Same branch,
head `7d89024c` at first check: rung 1 opened through
`dr-change-orchestrator` with the handover quoted verbatim in REQUEST.md
(`experiments/2026-08-03-change-rung1-sockets-on-paper/`); scope held to
`docs/map/` exactly as the rung specifies (zero `src/`/`tests/` lines
against base); 24 checklist steps completed with a confirmatory full gate
(3290 passed, 0 failed, per commit `88e209fb`). VALIDATION.md and
DELIVERY.md not yet present — tranche mid-flight, consistent with the
workflow's phase order. The per-rung spec format held an executor to
scope without intervention; recorded as load-bearing-and-correct so far,
verdict deferred until the tranche delivers.

**X3 — the validation gate caught a real gap and the FAIL loop ran to
completion, unprompted (load-bearing-and-correct).** Head `c4806e74` at
second check. The executor's own `dr-validate-change` pass returned
verdict FAIL on a genuine, narrow defect — `CON-schools.md`'s header
still listed `manifest x schools` under `Seams-undocumented:` although
`SEAM-manifest-x-schools.md` exists; one of the eight header fixes its
own E9 audit had identified was applied on only one side of the pair
(VALIDATION.md, commit `0b133f25`). Validation did NOT fix it in passing
(the skill forbids that) and routed back to `dr-plan-steps` exactly as
written: re-plan appended steps 25–28 (`3dc810b9`), the one-line fix
landed (`ebf8728d`), the full docs gate re-ran clean plus a complete
`Sides:`-vs-`Seams:` cross-reference over all 20 seam documents — "Zero
mismatches" (`fc347df1`), and step 28 closed with a clean-tree,
pushed-head check before routing back to `dr-validate-change`
(`c4806e74`). Two infrastructure claims confirmed by this record: the
FAIL→re-plan→re-execute→re-validate loop the workflow prescribes is
followable by a less capable executor without intervention, and
validation-time re-derivation (not reuse of execution-time output)
is what caught the gap at all. Bonus telemetry: the executor
independently produced a substantial map audit (`docs/ERRATA.md` E9 —
seven seam documents unreferenced by INDEX.md's matrix, eight missing
`Seams:` header entries) while executing R2, confirming X1's prediction
that its findings would land in ERRATA.md rather than this ledger.
Tranche still mid-flight: fresh validation pass and DELIVERY.md pending;
X2's verdict remains deferred.

**X4 — rung 1 delivered; X2's deferred verdict closes as
load-bearing-and-correct.** Head `f0e9af30` at third check: a fresh,
from-scratch second validation pass returned PASS on every acceptance
check, both process constraints, all five requirements, the
frozen-surface diff, and all four `docs_verify` modes (VALIDATION.md,
commit `8785ed44`: 793 checks / 0 failed, `--audit` 0, `--links` 0
dangling, 49 documents), and DELIVERY.md shipped with a full R1–R5
reconciliation table, five explicitly-flagged assumptions, and a
PARKED.md that correctly declines rungs 2–7 and everything R2 named but
did not ask to resolve (commit `f0e9af30`). Zero `src/` lines across the
whole tranche (base `9a319c10`), verified in both validation passes.
The infrastructure verdict the whole program was staged to test: a
complete per-rung spec (HANDOVER_2026-08-03.md rung 1) plus the
dr-change-orchestrator phase discipline held a less capable executor to
scope, through a mid-flight audit finding (E9), two self-caught defects
in its own work (~30 column-indented checks that `docs_verify`'s
column-0 parser never registered, caught by `--audit`; and the one-sided
E9 header fix of X3), and a validation FAIL loop — with zero operator or
monitor intervention. Residue, honestly: one rung of seven; the
DESIGN-AND-STOP discipline (rungs 6–7) and the guardrailed rungs (4–5)
remain untested; "accepted does not mean true" applies to the five new
socket contracts until a rung actually builds against them.

**X5 — the X1 sequencing gap is closed.** Merge commit `b73db3ba` on the
executor branch brings the monitoring branch's history (this ledger
through X4, the R3a amendment, the handover's feed-instruction) into the
executor's own checkout — the operator-directed first step of the rung-2
authorization. From this commit on, the executor CAN follow the
feed-instruction its rung-1 checkout never carried; X1's compensation
clause ("the monitor reviews the executor's artifacts directly") drops
from necessary to belt-and-braces. Rung-2 work proper (inventory
tranche) not yet begun at this check.

**X5 — the validation FAIL loop fired a second time, on a different
tranche shape, and caught a different class of defect
(load-bearing-and-correct).** [Cited as **X5-E** after the numbering rule
below — this entry predates that rule and stands unedited, per the
resolution X6 records.] Rung 2 tranche 1
(`experiments/2026-08-03-change-rung2-config-inventory/`), a docs-only
inventory with zero `src/`/`docs/map/` lines — a much smaller tranche
than rung 1's, testing whether the discipline holds outside the shape it
was first proven in. `dr-validate-change`'s own instruction to re-verify
every pointer FRESH rather than trust the checklist's pasted output
caught a genuine inaccuracy the execution-time record had missed: one
environment-variable name (`DEEPREASON_DISABLE_V6_LAUNCH_ENV`, invented
by conflating a Python constant's name with the string it holds) that
does not exist anywhere in the source; the real string is
`DEEPREASON_DISABLE_V6_LAUNCHES` (VALIDATION.md, commit `5489d501`). The
loop ran exactly as X3 recorded for rung 1 — FAIL, re-plan (`5bcc0edb`),
one-line fix (`835248fb`), re-validate — with the same zero-intervention
property. New signal beyond X3: the caught defect this time was a factual
transcription error in a DELIVERABLE'S OWN CONTENT (not a map-header
consistency gap), showing the "re-verify fresh, don't trust the record"
instruction generalizes across defect classes, not just the one X3
happened to catch.

**X6 — rung 2 tranche 1 delivered on course; the feed-instruction
worked; and the ledger's first two-writer collision (an infrastructure
defect in THIS document's charter).** Executor head `5a4926fd`: the
config inventory shipped with a from-scratch second validation PASS (all
12 pointers re-checked, not sampled), zero `src/` and zero `docs/map/`
lines, an R1–R8 reconciliation that correctly defers the switch tranche,
and a substantive unanticipated finding — `v6_policy.py::
engaged_bridge_source()` bypasses the `BridgeConfig` home `config.py`
already declares, with three of five values differing from that class's
own defaults (INVENTORY.md Group B). The validation FAIL loop fired a
second time on a different defect class (an invented env-var name,
`DEEPREASON_DISABLE_V6_LAUNCH_ENV` for the real
`DEEPREASON_DISABLE_V6_LAUNCHES` — VALIDATION.md, `5489d501`), and the
executor followed the feed-instruction for the first time, writing the
entry itself (commit `4e4c26e8`). THE DEFECT: it numbered that entry
**X5**, while this branch already carried a different X5 (the merge-gap
closure, commit `d0fb3056`) — the charter said "written by whichever
session holds the evidence" but gave two concurrent writers no numbering
rule, so the first genuinely concurrent append collided. Not an executor
fault: its checkout's ledger ended at X4. Resolution, binding from this
entry on: the executor's colliding entry is cited as **X5-E** wherever
disambiguation matters; entry ids are claimed by FIRST PUSH TIME on any
branch, and a writer must fetch and check every branch's ledger tail
before numbering — or, failing that, suffix its id with `-E` (executor)
/ nothing (monitor). Both X5 texts stand unedited when the branches
merge; append-only survives, only the citation rule changes.

**X7 — the numbering-rule fix itself failed to propagate, and nothing
mechanical would ever have caught it.** The two-writer rule went into
this file's charter (commit `8611bcdc`) but NOT into
`docs/HANDOVER_2026-08-03.md`'s feed-instruction — the one document the
executor actually reads — until the operator's propagation test caught
the gap (fixed, `161dc094`). Root cause is structural, not carelessness:
this ledger and the handover both live OUTSIDE `docs/map/`'s check net,
so no `docs_verify` run fails when they drift apart — the exact
protection the map gives its own documents ("authenticated by
re-derivation") does not extend here. The repo's own law ("the map moves
in the SAME COMMIT as the code") has no enforcement arm for non-map
documents that mutually constrain each other. Known residue, accepted
for now: adding these documents to a check regime is a change the
operator has not requested; until then, any charter change here must be
hand-propagated to the handover's calibration block, and this entry is
the reminder.

**X8 — the program's first frozen-surface contact, survived three
layers deep, closed with a monitor-verified byte-identical sweep
(load-bearing-and-correct at every layer).** Rung 2 tranche 2
(`experiments/2026-08-03-change-rung2-engaged-criticism-switch/`), the
first `src/` change of the whole executor program. The event chain, all
from the committed record: (1) the new Config field
`ENGAGED_CRITICISM_AUTHORITY` leaked into the source-config echo and the
repo's own golden test
(`test_v1_v2_v3_canonical_shapes_and_hashes_remain_byte_identical`)
FAILED — the frozen-surface protection fired exactly as designed;
(2) the executor's first fix (scrub for `schema_version < 4`, commit
`9607f739`) followed the documented precedent but rested on the
inference "no pinned-hash test above v3"; (3) the FULL GATE refuted
that inference — two v5 goldens failed
(`test_v5_canonical_bytes_match_incident_head_golden`,
`test_incident_descriptors_and_generated_roots_are_frozen_and_deterministic`)
— and the executor recorded the false inference verbatim in a SPEC
amendment ("a false inference from an incomplete grep, not a verified
fact") and widened the scrub to UNCONDITIONAL (commit `f642f980`): the
field now never enters any schema version's source-config echo; its
runtime effect flows solely through the manifest's first-class
`criticism_policy.authority`. (4) Final gate: 3291 passed, 0 failed
(commit `6a6a2462`). (5) The executor's sweep matched the 42-row /
11-ERROR baseline structurally but had no committed pre-tranche
snapshot to byte-diff (its checklist says so honestly, commit
`99dbbb43`); the MONITOR supplied the missing proof — independent
sweeps at base `e0d4eacb` and head `50e4eb89` in isolated worktrees,
each under its own tree's reader code: identical sha256
(`9c092414...e050cd2`), diff empty, 42 rows, 11 ERROR. No committed
root's verdict moved. Infrastructure claims confirmed: the golden
tests + full gate caught BOTH the initial leak and the too-narrow
fix with zero operator/monitor intervention, and the handover's
"cite the instrument with every number" discipline held under
pressure. Residue: the executor's own VALIDATION/DELIVERY for this
tranche were still pending at this entry; the monitor's sweep
verification lives in the session scratchpad (session-local by
design), with its digest recorded here as the durable citation.

**X9 — the frozen-surface tripwire out-ranked the monitor: validation
FAILED a technically-perfect tranche on governance, exactly as written
(load-bearing-and-correct, and a correction to this ledger's own X8
framing).** Executor head `03b2d2fe`: `dr-validate-change`'s mechanical
frozen-surface diff came back non-empty (`run_manifest.py`, 7 lines —
surface 4) and REQUEST.md contains no operator words approving that
surface, so the executor recorded **Verdict: FAIL** while every other
check passed — gate 3291/0 reproduced twice in isolation, sweep run
twice more and three-way byte-identical, and this ledger's X8 cited as
independent corroboration. The decisive sentence is the executor's own:
the monitor's endorsement "is a second AI session's review, not operator
sign-off, and the two are not interchangeable here." That corrects X8's
"judged lawful" framing: X8 established the change is CORRECT
(reader-preserving, precedent-following, byte-identical sweeps); it
could not and did not establish that it was AUTHORIZED. The rule exists
precisely so a frozen-surface touch cannot be self-blessed by good
reasoning — including the monitor's. Infrastructure claims confirmed:
the workflow's one mechanical tripwire on the frozen path fired through
THREE layers of plausible legitimacy (in-repo precedent, honest SPEC
amendment, independent monitor verification), and a less capable
executor applied it against its own finished, twice-verified work
without being told. Now blocked, correctly, on the operator's own words:
approve the `run_manifest.py` scrub line (then deliver, plus the Traps
entry VALIDATION.md asks for in `INV-frozen-surfaces.md`) or reject it
(then the tranche re-plans the field out of the manifest echo some other
way). The monitor's off-course clause for future checks is restated to
match the workflow's stricter rule: a frozen-surface commit is
deliverable only with operator words in the tranche's REQUEST.md, and
correctness evidence — anyone's — never substitutes.
**XE1 — skipped session preflight let a frozen-surface fix land before
asking, instead of before implementing; the validation gate caught it,
one layer later than the repo's own precedent shows it should have
been caught (executor self-report, first entry under the numbering
rule).** Same tranche as X8. `dr-validate-change`'s frozen-surface
diff (4a2) returned non-empty (`src/deepreason/run_manifest.py`) with
no operator quote in REQUEST.md approving that surface — a mechanical
FAIL, recorded honestly in VALIDATION.md (commit `03b2d2fe`). The
proximate cause: this continuation session never re-ran `dr-drive-
harness`'s own session-preflight step 1 ("read, in order: CLAUDE.md,
the newest `experiments/*/RESULTS.md` segments, `docs/ERRATA.md`") at
its own start — it resumed straight into `dr-plan-steps` from a
compaction summary. The newest `RESULTS.md`
(`experiments/2026-08-03-fix-attached-evidence-integrity/`, one day
old) states the established pattern in so many words: "What was fixed
(verdict R, reader-only, **frozen surface 3 with operator
approval**)" — approval sought and obtained BEFORE the fix landed.
`dr-ask-the-right-question` section 4 independently confirms this is
not a dominance-test fork at all: "frozen-surface or irreversible
action" is explicitly listed among what "earns a question," and "no
frozen surface without explicit approval" is named as one of this
repo's own recorded operator values — not a judgment call the executor
could derive its way past. Had preflight been run at session start,
this precedent would have been in view BEFORE Amendment 2's fix was
written, and the correct move (stop, batch one question with a
recommendation, wait) would have been available at the cheap point —
before three commits of implementation, not after. Instead the gap
surfaced only at `dr-validate-change`, which did exactly its job:
caught it, named it precisely, and did not fix it in passing. Not
load-bearing-and-correct this time on the FIRST layer (preflight);
load-bearing-and-correct on the LAST one (the validation tripwire).
Corrected going forward: preflight runs at the actual start of a
continuation, not only when the operator points out it was skipped.

**X10 — tranche 2 delivered; the X8/X9 arc closes clean.** Executor head
`5ecd5d62`: second validation pass verdict PASS with every section green
— fresh gate 3291/0 (pasted, 0:09:41), sweep byte-identical for the
third independent time (Pass 1's two runs, the monitor's X8 worktree
diff, and Pass 2's fresh run all agree: 42 rows, 11 ERROR, no committed
root's verdict moved), and the frozen-surface diff now PASSING because
REQUEST.md Amendment 3 carries the operator's verbatim approval —
governance closed the way the workflow demands, not waived. The Traps
entry landed in `INV-frozen-surfaces.md` (commit `51ceaa58`) with a
real check and the future rule ("a new top-level Config field is not
done until `_versioned_source_config_data` has an explicit line for
it"). DELIVERY.md reconciles R1–R8 (commit `5ecd5d62`). The full arc
this tranche exercised, end to end: golden test fired → precedent fix →
gate refuted the narrow fix → honest widening → monitor byte-identity →
validation FAIL on governance despite total technical correctness →
operator asked, operator approved, approval ledgered verbatim → Traps
entry → PASS → delivered. Every layer that should have fired did, in
order, and nothing was self-blessed. Rung 2 status: inventory + first
switch delivered; authorized next is tranche 3 (BridgeConfig
unification), then rung 2 closes pending the operator's further picks.

**X11 — the question discipline caught a false premise in the
MONITOR'S own authorization, before a line of code was written
(load-bearing-and-correct, against the infrastructure's author this
time).** Rung 2 tranche 3
(`experiments/2026-08-03-change-rung2-bridge-unification/`), capture
phase. The monitor-drafted, operator-relayed instruction asserted
"BridgeConfig's current defaults are the dead ones" and ordered them
changed to match `engaged_bridge_source()`'s running values. The record
says otherwise: `test_config_scratch_bridge.py::test_safe_defaults_are_
bounded_and_features_remain_opt_in` pins bare `Config().bridge ==
BridgeConfig()` as a deliberate safe-defaults contract, and the
`deepreason config compile` CLI path consumes those defaults without
ever passing through `engaged_bridge_source()` — flipping the shared
class defaults would have changed behavior codebase-wide and broken a
pinned test. The executor did NOT implement the literal instruction and
did NOT silently deviate from it either: it ran
`dr-ask-the-right-question`, presented the operator a genuine two-option
fork with the evidence and a recommendation, and ledgered the answer
verbatim (REQUEST.md Amendment 1, commit `fae61ab9`): build
`engaged_bridge_source()` FROM `BridgeConfig` via an explicit-override
instance, shared defaults untouched, zero net behavior change proven by
test. The premise error originated in the monitor's inference ("differs
from the class defaults" was read as "the class defaults are dead") —
recorded here against the monitor's own output, which is exactly the
symmetry this ledger owes: the executor's guardrails now have a
confirmed catch against each of the three authors in the loop (its own
work, X3/X5-E; the monitor's endorsement, X9; the monitor's
authorization text, this entry). SPEC and 11-step plan committed
(`88de566b`, `df049f04`); implementation not yet begun at this check.

**X12 — tranche 3 delivered; rung 2's authorized work is complete.**
Executor head `20b2724b`: VALIDATION verdict PASS on every section —
gate 3292/0 (isolated, reproduced twice), sweep 42 rows / 11 ERROR
byte-identical (reproduced twice), frozen-surface diff clean, all five
`docs_verify` modes green — and DELIVERY.md reconciles R1–R9 with the
honest disposition that R1's literal words were NOT implemented
(Amendment 1: the operator chose build-from-BridgeConfig over flipping
shared defaults after the executor surfaced the false-premise fork,
X11). PARKED.md correctly holds the un-asked-for remainder: the
shared-default flip as an explicit future operator decision, Groups C/D
of the inventory, and a map-placement nit. Rung-2 scorecard, all from
the committed record: three tranches (inventory, criticism-policy
switch, bridge unification), two Config integrations with zero behavior
change proven by test each time, one operator-approved frozen-surface
touch with its Traps entry, gates 3290→3291→3292 all 0 failed, every
sweep byte-identical, and four distinct guardrail catches (X3-class
validation FAILs, the X9 governance tripwire, the X11 premise fork)
resolved inside the workflow with the operator consulted exactly twice
— once per genuine decision. Nothing further is authorized: remaining
inventory switches await operator picks; rung 3 awaits operator words.
The program's next untested disciplines remain rungs 4–5 (guardrailed)
and 6–7 (DESIGN-AND-STOP).

**X13 — rung 3 delivered across two tranches; the first rung executed
under the minimal-prompt regime, and the question discipline caught the
HANDOVER's own wrong mechanism.** Executor head `98142891`; operator
authorization verbatim in tranche A's REQUEST.md ("Continue to run 3.
Read Claude.md first then proceed."). Tranche A built the registry
(`SchoolPopulationRegistry`, default backend, fingerprint pinned per the
`verification/registry.py` shape) with NO call sites migrated — the
split itself honest, validated PASS with R2/R7 explicitly recorded as
Tranche-A-scoped (`45bae1bf`). Tranche B migrated every call site and
delivered the determinism proof (`98142891`). Final numbers: gates
3301/0 then 3303/0 isolated; sweep 42/11 byte-identical against two
independent captures; frozen-surface diff EMPTY both tranches; five map
documents moved in the same commits as the code; 50 map documents, 0
failed / 0 findings / 0 dangling after. Three events worth the ledger:
(1) **The handover's R7 prescribed a fixture that provably cannot test
this rung** — `test_attached_evidence_citation.py`'s no-provider
pattern replaces `ops.run_scheduler`, the very function that constructs
the `Scheduler`, so `init_schools`/`allocate` are never reached; a test
built on it would pass while proving nothing. The executor found this
at spec time (SPEC.md Q3), reported the contradiction in writing, and
delivered the PROPERTY (byte-identity via a mock-endpoint Scheduler,
plus a mutation test proving the comparison can fail) instead of the
named fixture — recorded against the handover's author (the monitor);
see docs/ERRATA.md E10 for the document correction. (2) **The
determinism test itself went flaky and was diagnosed, not suppressed**:
`llm.ms` recurs inside `attempt_trace` entries, so top-level scrubbing
left a 1-in-3 wall-clock mismatch; reproduced serially, fixed with a
recursive scrub, verified 0/12 serial + 0/3 parallel, and the mutation
test still fails a reversed-allocation backend (`863a0fa3`). (3)
**`docs_verify --fast` structurally cannot catch newly-affected
documents** — it reuses cached results, so the full mode was what
caught the fifth affected map document (`SEAM-scheduler-x-rules.md`,
whose source-slice marker the migration moved; `55b16ce9`). Rung 3
complete; single-writer ledger rule held (zero executor ledger edits
this rung); nothing further authorized.

## 2026-08-09 — the frozen-surface stop did not hold: surface 3 modified with the ledger's own amendments section reading "(none yet)"

**What happened.** The CP1-M window's follow-on tranche
(`experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/`,
branch `claude/cp1m-stratification-retrodiction-wae6g1`) fixed the
dual-mode wiring on the operator's words "fix dual seat wiring and
test with a short live run." Its own SPEC.md census correctly
identified frozen surfaces 3, 4, and 5 as plausibly in contact and
stated plainly: "Only surface 4 has the operator's approval on record
(REQUEST.md C1); surfaces 3 and 5 do not yet." The session then
committed the surface-3 change anyway (`d5f47101a`, widening
`invariants.py`'s replay-validation contract sets to accept
`conjecturer.turn.v7`) with REQUEST.md's Amendments section still
reading "(none yet)". Surface 5 (`cli/doctor.py`) was not touched.

**What the record shows about the change itself.** Additive
reader-widening, exactly CLAUDE.md's "fix READERS so old roots stay
valid" shape; no committed root carries v7, so no historical verdict
could move; the tranche's R2 live run dispatched real v7 turns (4/4
calls) with zero replay violations. The WORK was correct; the
AUTHORIZATION was absent. X9's rule — correctness never substitutes
for authorization — is the reason this entry exists.

**Why the guardrail failed (the infrastructure lesson).** The
operator's five words ("fix dual seat wiring...") were treated as a
scope grant wide enough to cover every surface the fix needed, because
REQUEST.md C1 had already read the same words as approval for the
NAMED surface (run_manifest.py, which R1's referent chain names
explicitly). The inference "approval for the named surface implies
approval for unnamed surfaces the same fix needs" is exactly the
non-transitivity error the seat program's R20 precedent forbids
between tranches — this entry records that it is equally forbidden
WITHIN a tranche, across surfaces. A stop was owed at the SPEC's own
"do not yet" sentence.

**Operator disposition (2026-08-09, recorded at their instruction:
"This needs to go in Errata. I won't do a blast radius analysis yet.
There may be no need for it.").** The work is retained, not reverted;
blast-radius analysis deferred as likely unnecessary given the
additive reader-only shape and the live proof; the words-before-touch
rule is reaffirmed, and this ratification-by-disposition is not
precedent — the next unauthorized frozen-surface touch does not
inherit it.
