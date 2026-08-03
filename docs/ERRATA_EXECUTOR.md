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

Numbering rule (added 2026-08-03 after the X5 collision, operator-
directed — see X6): the two writers use disjoint id spaces. The
MONITORING session writes `X<n>` (this file's original sequence). The
EXECUTOR session writes `XE<n>`, starting at XE1, numbered off the ledger
tail in its OWN checkout. Neither renumbers the other's entries, ever;
on merge, both sequences stand as written. The executor's one
pre-rule colliding entry (commit `4e4c26e8`, "X5" in its branch) is
cited as **X5-E** everywhere, including after merge.

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
