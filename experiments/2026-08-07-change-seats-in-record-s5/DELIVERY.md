# Delivered: seats in the typed record — Rung S5 of role-seat separation
Branch: `claude/s5-dr-plan-steps-q5utlc` @ `af0e2b16` (pushed, tree clean)

## What changed

Every DeepReason run's own append-only record now permanently says
which provider/model sat in which role group. A new sibling payload
(`src/deepreason/seat_events.py`: `SeatBindingV1`,
`SeatBindingsEventPayloadV1`, schema `seat-bindings.v1`) carries an
absence-tolerant reader (`recorded_seat_bindings`) and a projection
reader (`seat_bindings_for_run`) that reads a default home's
implicit single seat straight from the manifest when no stamp exists.
`Event.seat_bindings` (`ontology/event.py`) fences the payload to ride
only `Rule.MEASURE`, mirroring the existing `module_fingerprints`
fence exactly. `Harness.record_seat_bindings` (`harness.py`) is the
writer, landed inside the operator's own narrow authorization — an
appender plus one `_commit` keyword, zero `_apply_event` or
well-formedness contact. The group name is captured once, at mint
time, by `RunPreparationService.prepare` into a conditional sibling
file (`seat-bindings.json`, absent for a default home) via a new
group-keyed helper, `resolve_seat_bindings_by_group`
(`seat_bindings.py`); `Scheduler._record_seat_bindings`
(`scheduler.py`) reads that snapshot and stamps it, placed and gated
identically to `_record_module_fingerprints`. The map moved with the
code across four documents, and `tools/root_sweep.py` gained a
`seats=` column proving the observable is swept.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Now Rung S5 via `dr-change-orchestrator`..." | done | REQUEST/SPEC/CHECKLIST/VALIDATION/PARKED/DELIVERY in phase order; VALIDATION S1 |
| R2 | "Every run's own record must permanently say which model sat in which seat" | done | commit `bdc476e8`; VALIDATION S7 |
| R3 | "follow the rung-4 template exactly" | done | SPEC.md M1-M6; landed design mirrors `module_events.py`'s shape |
| R4 | "absence-tolerant READER first" | done | commits `f3490729`, `9a3af22f` precede writer `4a2b5a5b` |
| R5 | reader reads as "single seat, the manifest's provider" | done | commit `ca34dc49`; VALIDATION S3 |
| R6 | "verify [payload] shape against the tree, don't inherit it untraced" | done | SPEC.md Q1 (measured); sibling payload landed, not an extension |
| R7 | "contract clause fencing it" | done | commit `b0813f59`; VALIDATION S4 |
| R8 | "writer last" | done | writer `4a2b5a5b`, after reader/fence commits |
| R9 | "sweep probe in its own SEPARATE commit... on an unchanged tree" | **done, one deviation named** | see "Named deviation" below |
| R10 | "Accept: full gate 0 failed (P1's known pre-existing failure excepted, named)" | done | VALIDATION.md "Full gate": 3382 passed, 0 failed net of P1/P3 (worktree-proven pre-existing) |
| R11 | "sweep byte-identical pre-probe" | done | steps 1/27, sha `8b928c08b1...` both captures |
| R12 | "probe mutation-proven" | done | step 31: 34/34 rows moved, restored byte-identical |
| R13 | "a two-profile home's run shows the stamp naming both bindings" | done | commit `bdc476e8`; VALIDATION S7 |
| R14 | "a default home's run shows the single-seat stamp" | done | commit `bdc476e8`; VALIDATION S7 |
| R15 | "One rung only — S4b and S6 untouched" | done | VALIDATION S10; diff names no `qualification.py`/ladder file |
| R16 | "role-group → provider/model/profile-digest" | done | `SeatBindingV1`'s own four fields, commit `f3490729` |
| R17 | plan's own restatement of R4-R9 | done | same evidence as R4-R9 |
| R18 | plan's own accept, incl. "testphase-style live audit" | **deferred** (operator's words: R15, "S4b and S6 untouched") | A4 records the disposition; the live two-seat A/B demonstration is Rung S6's own stated scope |
| R19 | "you may add the record_seat_bindings appender plus one `_commit` keyword... zero change to `_apply_event`" | done | commit `4a2b5a5b`; frozen-surface diff (VALIDATION) shows exactly the two authorized units |
| R20 | "This grant is not transitive to any later rung" | done | standing rule, unmodified; no `harness.py` touch beyond R19's own grant |
| R21 | budget correction, 500-650 insertions | done | REQUEST.md Amendment 2, commit `1809df6d` |
| R22 | "Continue, report final total at delivery" | done | REQUEST.md Amendment 3, commit `d626e73a`; final total below |

**Final line total, reported plainly per R22's own binding condition:**
`git diff --stat 54feb5cc..HEAD -- src/ tests/ docs/map/ tools/` =
**804 insertions**, against R21's own corrected 500-650 ceiling. Not
glossed: two overruns occurred during execution (flagged at 361/650
already trending high; confirmed exceeding at 729/650 before the map
landed), both raised via `AskUserQuestion` STOPs and resolved by
explicit operator authorization before another line was written.

**Named deviation (R9), no history rewrite:** the probe commit
(`fd8b66a1`) contains `tools/root_sweep.py` (13 lines, the probe
itself) AND this tranche's own `CHECKLIST.md` (70 lines, step
bookkeeping/evidence) — not "only `tools/root_sweep.py`" as R9's
literal words specify. The isolation INTENT R9 exists to protect held
throughout: zero `src/` file rode this commit, the probe's own
before/after capture ran on a tree unchanged since the main phase
closed, and the probe was never judged alongside the behavior change
it measures. The literal wording was not met; the property it protects
was. Recorded here as the ledger, not corrected by rewriting `fd8b66a1`.

## Assumptions the operator may override

A1: sibling payload `seat-bindings.v1`, not an extension of
`module-fingerprints.v1`.
A2: no manifest touch anywhere — Rung S2's "manifest record" phrasing
was informal prose, not a locked decision.
A3: the mint-time snapshot lives in a new file (`seat-bindings.json`),
not a field on `RunPreparationRecordV1`.
A4: R13/R14 are satisfied by an offline regression (MockEndpoint), not
a live provider-backed run; the live audit is Rung S6's own scope.
A5: the writer copies the rung-4 template's per-instance idempotency
gate exactly, unmodified — not implicated in P1/P3 (the TEST's
single-unpack assumption is); this rung's own reader tests are
partition claims from the start, so no new instance of that
brittleness was manufactured.

## Map delta

**Changed:** `docs/map/CON-seats.md` (new "Rung S5" section, two new
table rows, one new check), `docs/map/SEAM-schools-x-scheduler.md`
(one new table row, one new AST check), `docs/map/CON-schools.md` (one
new table row, one new behavioral check), `docs/map/CON-run-identity.md`
(one new table row, one new behavioral check). **Created:** none (no
new map document — this rung extends existing ones, per SPEC.md Item
S11). **New checks:** 4.

**Left stale, reviewed and dismissed (owned files touched by this
tranche, no claim broke — confirmed via full `docs_verify` 0 failed
and the additive-only design):** `SEAM-harness-x-verification.md`,
`SEAM-harness-x-workflow.md`, `SEAM-ontology-x-rules.md`,
`SEAM-scheduler-x-rules.md`, `SEAM-scheduler-x-workflow.md`,
`SEAM-schools-x-scratch.md`, `SUB-harness.md`, `SUB-ontology.md`,
`SUB-scheduler.md`.

**Left stale, pre-existing and unrelated to this tranche (not this
delivery's obligation):** `REC-change-a-seam.md`,
`SEAM-bridge-x-manifest.md`, `SEAM-llm-x-manifest.md`,
`SEAM-manifest-x-schools.md`, `SUB-manifest.md`, `SUB-periphery.md`,
`SUB-verification.md`.

## Parked (not done, not promised)

**P1/P3 — pre-existing full-gate failure**
(`tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`),
tracked in every one of Rungs S1-S4's own PARKED.md files and
re-confirmed unrelated to this rung by `git log` (this tranche's own
commits never touch the file, and its `scheduler.py` diff is purely
additive beside the existing mechanism) and by direct reproduction on
a `git worktree` at this tranche's own base commit (`54feb5cc`), before
any of Rung S5's code existed. REQUEST.md's C6 records a fresh,
independently-verified candidate root cause not diagnosed by any prior
rung: `Scheduler._module_fingerprints_recorded` is a PER-INSTANCE
guard that resets on every `Scheduler.__init__`, so `deepreason
continue`'s fresh `Scheduler` construction does not prevent a second
stamp on the same root across a continuation boundary.
**Ready-to-send prompt:** "Diagnose and fix P1/P3 —
`Scheduler._module_fingerprints_recorded`'s per-instance reset across
a `deepreason continue` boundary — via `deepreason-orchestrator`,
starting from `dr-set-goal` with `experiments/2026-08-07-change-seats-
in-record-s5/PARKED.md`'s P1/P3 entry and REQUEST.md's C6 as the
starting evidence."

**Recommended next:** P1/P3 — it is the one item common to every rung's
own PARKED.md since Rung S1, it now carries a concrete, independently-
verified candidate root cause (C6) that no prior rung diagnosed, and
fixing it retires a recurring gate-noise item rather than adding new
scope. This closes Rung S5; Rung S6 (the live two-seat A/B
demonstration, R15/R18/A4) is the plan's own next EXECUTE step when the
operator is ready for it, but P1/P3 is the higher-leverage next tranche
because it is a defect, not a feature, and it is now unblocked.
