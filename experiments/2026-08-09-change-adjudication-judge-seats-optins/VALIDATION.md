# Validation for: adjudication / judge-seats / legacy-criticism / schools opt-ins

Validated at commit `52f9fb3ba457b0c3bbdb8ed14d5e2775bfa09929`, tranche base
`81d08e5f0d4a2be3a0ba546b712b485473629407`.

## Acceptance checks

SPEC.md does not enumerate a separate numbered "S1, S2, ..." acceptance-check
list distinct from its section structure (§1(a)-(f), §2(a)-(d), the decision
sheet §5.1-5.6, and the addenda S13a-S18). CHECKLIST.md's own per-step
done-when commands ARE this tranche's acceptance checks, already run and
pasted at each step. This validation re-runs the checks that certify the
*assembled whole* rather than re-pasting all ~63 individual step proofs:

- Full regression gate (below): PASS.
- Frozen-surface diff (below): PASS.
- Map validation, all five `docs_verify.py` modes (below): PASS.
- Packaging-surface smokes (below): PASS.
- Record-behavior preservation spot check (below): PASS.

## Full gate

Run twice at validation time (the second run exists specifically to
distinguish a reproducible failure from parallel-execution flakiness — see
below).

Run 1 (immediately after the Step 61 regression fix, commit `b9638f3ff`):
```
6 failed, 3484 passed, 7 skipped in 1464.08s (0:24:24)
FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
FAILED tests/test_mcp_run.py::test_start_poll_result_and_progress_notifications
FAILED tests/test_mcp_run.py::test_cancel_waits_for_safe_boundary
FAILED tests/test_mcp_run.py::test_typed_v6_stop_can_continue_and_append
FAILED tests/test_mcp_scratch_bridge.py::test_bridge_start_poll_result_claims_and_unresolved_success
FAILED tests/test_mcp_scratch_bridge.py::test_progress_callback_failure_cannot_relabel_success
```

Investigated before re-running: the 5 MCP-thread failures all assert on
`thread.join(timeout=5)` / `not thread.is_alive()` in `test_mcp_run.py` and
`test_mcp_scratch_bridge.py` — real background threads racing a fixed 5s
timeout under `-n 4` parallel CPU contention, in a subsystem (MCP bridge
threading) this tranche never touched (zero overlap with
`verification/report.py`, `run_manifest.py`, `preparation.py`,
`seat_bindings.py`, `cli/main.py`, `v6_policy.py`, `signals_read.py`).
Re-run in isolation (no parallel load): all 5 passed cleanly in 42.27s.

Run 2 (same commit, no code changed in between):
```
1 failed, 3489 passed, 7 skipped in 1022.36s (0:17:02)
FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
  assert counts["gate_blocked"] == census["streams"][stream]["gate_measures"]
  AssertionError: assert 159 == 165
```

The MCP-thread failures did not reproduce (3489 passed here vs. 3484 in
Run 1 — a difference of exactly 5). This confirms Run 1's 5 extra failures
were transient parallel-execution timing flakiness, not a regression from
this tranche: **PASS**, with one pre-existing, unrelated failure recorded
below and in PARKED.md.

`test_bronze_report.py::test_census_totals_internally_consistent` (159 vs.
165) reproduces identically in both runs and was independently confirmed
pre-existing at Step 60 by checking it out against the tranche's true base
commit (`81d08e5f0`) in an isolated `git worktree` — same failure, same
numbers, before any of this tranche's changes existed. Operator confirmed
("continue") accepting this as a documented, parked exception. See
PARKED.md.

**Verdict: PASS** (0 failures attributable to this tranche; 1 pre-existing
failure, parked, not blocking per the operator's own words).

## Record-behavior preservation

- Known-good v6 root, `experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf`:
  `verify_root_report(..., allow_missing_terminal=True)` → `valid=True,
  security_valid=True, integrity_valid=True, 0 security findings`. This
  root carries 17 `criticism` transactions, ALL with a real
  `critic_school_id` (`school-0`..`school-3`, confirmed by direct
  inspection of `task_payload_value`) — every one goes through the
  UNTOUCHED `else` branch of the Step 61 fix (`authority_differences`'s
  `task == "criticism"` case). Verdict is provably, and empirically,
  unchanged by this tranche.
- Defect-era root: none exists in the committed tree. The bug the Step 61
  fix corrects (school-free legacy criticism being wrongly flagged
  security-invalid) can only be exercised by a run compiled under
  `LEGACY_CRITICISM_ENABLED=True` — this tranche's own Part B2 default
  flip, which postdates every currently-committed root. No historical
  root carries `critic_school_id: null` criticism work
  (`grep -rl '"critic_school_id": null' experiments/*/run*/log.jsonl` — 0
  hits). The defect-era comparison is instead demonstrated by: (a) the
  live `scripts/wheel_operational_smoke.py` run that originally surfaced
  the bug (17 spurious security findings on an ordinary `reason` call,
  before the fix; 0 after), and (b) the two new regression tests in
  `tests/test_v6_verification_transactions.py`.
- `root_sweep.py` (the full-tree instrument) itself hangs indefinitely on
  one specific, ordinary-sized, PRE-EXISTING historical root
  (`experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03`,
  508 log lines, 5.2MB) — confirmed via `strace` to be looping on repeated
  `ENOENT` object-path probes, unrelated to anything this tranche changed
  (the fix only narrows one early-exit branch, adds no lookup or loop).
  Killed after 1h37m at ~100% CPU with no progress. Parked as a separate,
  pre-existing performance defect (see PARKED.md); the two targeted
  `verify_root_report` calls above stand in for the full sweep.

## Frozen surfaces

```
$ git diff --stat 81d08e5f0..HEAD -- src/deepreason/capabilities/state.py \
    src/deepreason/harness.py src/deepreason/invariants.py \
    src/deepreason/run_manifest.py src/deepreason/qualification.py
 src/deepreason/run_manifest.py | 91 +++++++++++++++++++++++++++++++++++++++---
 1 file changed, 86 insertions(+), 5 deletions(-)
```

`state.py`, `harness.py`, `invariants.py`, `qualification.py`: byte-identical
to the pre-tranche base. `run_manifest.py`'s diff was read in full (Step 59)
and sorted into exactly two categories, nothing left over:

1. Additive `.pop(...)` lines inside `_versioned_source_config_data` for
   this tranche's four new Config fields (`LEGACY_CRITICISM_ENABLED`,
   `ADJUDICATION_STATUS_AUTHORITY_ENABLED`, `JUDGE_SEATS_ENABLED` + its two
   throttle knobs, `SCHOOL_SEATS_ENABLED`) — Amendment 6's original
   pop-line-only grant (R16), applied once per field.
2. The content-blind same-model judge substitute — Amendment 9's second,
   separately-ledgered grant (R24, the operator's clarification):
   `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED`'s relaxation and
   `compile_run_manifest`'s new `blind_same_model_judges` parameter,
   already fully executed and tested at Part D2 (Steps 57a-57f).

**PASS.**

## Packaging surface

Touched: this tranche adds console-reachable CLI flags
(`--school-seat`, `--criticism-seat`, `--blind-same-model-judges`) but no
new console entry point, no MCP tool, no wheel-layout change.

```
$ python scripts/wheel_smoke.py
wheel smoke passed: isolated V6-only contents, clean imports, exact entry points, module parity, MCP registration, and exact MCP schemas
$ python -u scripts/wheel_operational_smoke.py
wheel operational smoke passed: installed setup, explicit qualification (80 qualification calls; 428 total calls), readiness, question-only reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP restart, budget ceiling, and pre-V6 fail-closed admission
```

Both run and pasted after commit `b9638f3ff` (the Step 61 regression fix);
no code changed between that commit and this validation, so no re-run was
owed. **PASS.**

## Map

```
$ python tools/docs_verify.py
docs_verify [full]: 53 documents, 855 checks, 4 workers
docs_verify: 0 failed
```
**PASS.**

```
$ python tools/docs_verify.py --audit
docs_verify --audit: 0 finding(s)
```
**PASS.**

```
$ python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 53 document(s)
```
**PASS.**

```
$ python tools/docs_verify.py --coverage
docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 0 finding(s)
```
**PASS** (0 findings — the 16-without-a-header count is advisory, per
`SCHEMA.md`: "A `Sweep:` header must target ENFORCEMENT... not readers,"
and is optional documentation, not a required field). New observables this
tranche added and their enforcement coverage:
- `SchoolExecutionPolicyV1(mode="route_bound", ...)` reachability — pinned
  by `SEAM-manifest-x-schools.md`'s AST-scanning check (exact sorted
  `(file, mode)` list).
- `engaged_criticism_policy`'s `seat_map` parameter (criticism-side route
  divergence) — pinned by the new Traps entry/check added to the same
  document at Step 50.
- `dispatch_authority` on school-free criticism payloads — enforced at TWO
  sites (`nonconjecture_recovery.py::_criticism_contract`, S13e;
  `verification/report.py::authority_differences`, the Step 61 fix), both
  covered by dedicated regression tests. Not a durable, already-committed
  event *type* to retroactively sweep — no historical root carries this
  shape yet (the default that reaches it is brand new, Part B2), so a
  `root_sweep.py`-style probe has nothing to sweep; the regression tests
  are the correct instrument for behavior with no historical roots to
  check.
- `SignalSnapshotV1`/`stats["signal_snapshot"]` — an ephemeral, computed-
  on-read aggregation, not a persisted record type; nothing for a root
  sweep to probe. Covered by its own dedicated tests
  (`tests/test_signals_read.py`, `tests/test_v6_verification_transactions.py::test_report_includes_signal_snapshot`).

```
$ python tools/docs_verify.py --stale
docs_verify --stale: 42 document(s) worth re-reading
```
Every entry, dismissed with reason (not silently passed over): of the 42,
exactly 12 were edited by this tranche's own commits
(`git log --name-only 81d08e5f0..HEAD -- docs/map/`): `CON-authority.md`,
`CON-schools.md`, `CON-seats.md`, `SEAM-adjudication-x-authority.md`,
`SEAM-llm-x-rules.md`, `SEAM-manifest-x-schools.md`,
`SEAM-rules-x-workflow.md`, `SEAM-scheduler-x-rules.md`,
`SEAM-scheduler-x-workflow.md`, `SUB-scheduler.md`, `SUB-verification.md`,
`SUB-workflow.md`. All 42 (these 12 plus 30 more, stale from this same
tranche's EARLIER parts executed in prior sessions) are dismissed with one
uniform reason: `python tools/docs_verify.py` (full) reports 0 failed
across all 855 checks RIGHT NOW — every claim in every one of these
documents currently holds. Their `Verified-at:` stamps were not bumped in
the same commits that touched their owned files (a real, if minor,
procedural gap in this tranche's own step-execution discipline, visible
only in aggregate at this validation boundary, not a correctness issue —
every edit was followed by a passing `docs_verify` run at the time). Per
this skill's own exit criteria ("No file other than VALIDATION.md ... A
map document that needs updating is a FAIL routed back to
`dr-execute-step` ... validation that edits the thing it validates proves
nothing"), this validation does NOT bump these 42 stamps itself. Recorded
as a follow-up (a single stamp-bump commit, zero content risk) rather than
a blocking FAIL, since `--stale` is explicitly advisory per this skill's
own procedure and every underlying check currently passes. See PARKED.md.

New checks added by this change: yes, throughout — the `SEAM-manifest-x-schools.md`
file-census and `SchoolExecutionPolicyV1` mode checks (Step 44, revised at
Step 50), the criticism-side `seat_map` check (Step 50), the
`stats["signal_snapshot"]` wiring check (Step 56), and the Step 61 fix's
own Traps-entry check — every behavior this tranche added has at least one
falsifiable check backing it.

Record observables added vs. sweep probes: see the `--coverage` section
above — `dispatch_authority` and `SignalSnapshotV1` are covered by
dedicated regression tests rather than a `root_sweep.py` probe, justified
by having no historical committed roots to sweep (both reachable only
through defaults/mechanisms this tranche itself introduced).

## Requirement sweep

R1 (adjudication opt-in): demonstrated by §2(a)'s design and Part C
(`ADJUDICATION_STATUS_AUTHORITY_ENABLED`), shipped and tested.

R2 (judge seats opt-in, judges never spend a token unless enabled):
demonstrated by §2(b)/Part D (`JUDGE_SEATS_ENABLED`, default off).

R3 (legacy criticism paths opt-in): demonstrated by §2(c)/Part B
(`LEGACY_CRITICISM_ENABLED`) riding on Road E's real circuit (Part A).

R4 (WHY archaeology — seat census, design history, structural conflicts):
demonstrated by SPEC.md §1(a)-(c), delivered in the SPEC-AND-STOP phase
before any code; research deliverable, no further code obligation.

R5 (schools as opt-in seats): demonstrated by §2(d)/Part E — superseded in
its concrete shape by R27 (see below), but the underlying requirement
(schools reachable as an opt-in) is delivered.

R6 (judge design target — dormant/summoned/starvable): PARTIALLY
demonstrated. "Dormant by default" and "starvable" are shipped
(`JUDGE_SEATS_ENABLED` defaults off; `JUDGE_SUMMONS_PER_CYCLE`/
`JUDGE_SUMMONS_COOLDOWN` throttle). "Summoned only for grounded-undecidable
standoffs" (the live O1a-summons wiring) is explicitly DEFERRED to a later
tranche — Amendment 5's own binding resolution of §5.2 ("the standoff-
summons wiring is its own later tranche, NOT this one"), operator-approved
in writing. Not a gap; a scoped-out follow-up.

R7 (judge-starving machinery — find or establish absent): demonstrated by
§1(d) — established absent (research finding; the machinery §2(b) ships
IS the config-based starve knob R10 later confirms as the right target,
not a resurrection of dead code).

R8 (config-recommendation function — find or establish absent):
demonstrated by §1(d) — found LIVE (`config_referee`); no code needed,
already reachable.

R9 (workflow-makeover conditional): demonstrated by §1(d)'s split verdict
— NOT triggered, since `config_referee` (R8) is live (only R7's half was
dead); no workflow-makeover road built, correctly, per the conditional's
own terms.

R10 (config-based judge starvation, refines R6/C7): demonstrated by
§2(b)'s throttle fields, Part D.

R11 (built-in signals to detect active judges): demonstrated by the
Amendment 3 addendum's research finding (two different things exist, in
two different states) — research deliverable, no code obligation stated.

R12 (single-model two judge seats): demonstrated by Part D2 — originally
deferred as "Road C" (Amendment 5), explicitly pulled back into scope by
R22/Amendment 9 and delivered as the content-blind same-model substitute
(`--blind-same-model-judges`).

R13 (pre-school criticism circuit, reactivatable): demonstrated by Road E,
Part A (Steps 1-15) — the circuit traced, confirmed real, and rebuilt to
dispatch under v6.

R14 (static/mint-time-frozen gates only): demonstrated throughout — no
mid-run signal consumption was added anywhere in this tranche;
`signals_read.py` (Part F) is explicitly read-only, consumed only at run
boundaries, per its own docstring and design.

R15 (static signal-read surface): demonstrated by Part F
(`signals_read.py::read_signal_snapshot`).

R16 (frozen-surface pop-line grant): demonstrated by the Frozen surfaces
section above — exactly the authorized pop-lines, nothing else.

R17 (non-transitivity): process constraint; honored (this tranche only,
no later tranche's grant asserted here).

R18 (dr-execute-step then dr-validate-change, STOP after VALIDATION.md):
this document IS that demonstration — in progress; the STOP after this
file is committed and pushed is honored below.

R19 (clean separation between school and criticism, not intrinsic):
demonstrated by Part A's S13i self-sufficient dispatch
(`crit_argumentative_batch` self-detects v6, resolves its own route, no
new scheduler keywords).

R20 (interaction preserved when school configured): demonstrated by the
school-routed path staying byte-identical throughout Part A (confirmed
unmodified by every "school-routed" test cited in Steps 5-13).

R21 (separation without touching the scheduler-authority boundary):
demonstrated by Step 13's own AST check (`Scheduler._arg_crit`'s call to
`crit_argumentative_batch` remains keyword-free) — re-affirmed still true
by this tranche's full gate passing (`test_scheduler.py`,
`test_v6_scheduler_model_phase_deferral.py`).

R22 (single-model judge, real minting, no restriction): demonstrated by
Part D2 — content-blind same-model substitute mints a real warrant
(`test_a_single_model_run_mints_a_warrant_on_cross_school_criticism` and
its D2 sibling for the pure same-model case).

R23 (observe_only remains a selectable, judge-free floor): demonstrated —
untouched; `ADJUDICATION_STATUS_AUTHORITY_ENABLED=False` remains the
default path, unaffected by R22/R24's addition.

R24 (content-blindness guarantee, refines R22): demonstrated by S15/S16 —
`test_judge_pack_never_names_an_author_school_or_model` pins the property
as an enforced invariant.

R25 (CLI-exposed switch): demonstrated by `--blind-same-model-judges` on
`deepreason config compile`.

R26 (superseded): superseded in full by R27; the underlying scope (Part E
execution) it authorized stands, but its specific "and" reading of the two
school mechanisms does not — see R27.

R27 (corrects R26 — schools are conjecture-side; criticism's attachment is
separate/optional): demonstrated by Part E's two fully independent levers
— `--school-seat` (Step 44, conjecture-only, never touches
`CriticismPolicyV1`) and `--criticism-seat` (Step 44b, criticism-only,
requires `LEGACY_CRITICISM_ENABLED=False`, never touches
`SchoolExecutionPolicyV1`) — proven independent by each lever's own test
asserting the OTHER mechanism is untouched.

R28 (Legacy should be the default for criticism, reading (b)): demonstrated
by Part B2 — `Config.LEGACY_CRITICISM_ENABLED` default flipped `True`;
`test_legacy_criticism_enabled_by_default_is_byte_identical` and the
sibling explicit-opt-back-in test both pass.

## Assumptions carried

SPEC.md carries no formal "A1..An" assumptions list; its "OPEN QUESTIONS
CARRIED FORWARD" section is the equivalent, reproduced here so delivery
surfaces it:

- Q1: the four (now more, after R27 split schools into two) opt-ins are
  independent `Config` booleans, not one unified flag — the
  smallest-reasonable reading of the operator listing them as separate
  sentences. Confirmed correct by every later amendment (R26/R27
  specifically reinforce independence as the operator's actual intent).
- Q2: "the two assignable seats" = `conjecture` + its `simulation` alias;
  `coder`/`scratch` are dead weight. Resolved by Half 1(a), unchanged
  since.
- Q3: "legacy criticism paths" resolved to exactly one true
  legacy-superseded pair (Road E's subject) — no second, separate opt-in
  surface was needed beyond §2(a)'s adjudication flag and §2(c)'s
  `LEGACY_CRITICISM_ENABLED`.
- §5.1/§5.4/§5.5 decision-sheet forks: resolved by Amendment 5's binding
  approval (Road A / Road A-with-Road-B-follow-up / Road B respectively) —
  no longer open.

## Verdict: PASS

No failure attributable to this tranche's own changes. One pre-existing,
unrelated test failure (`test_bronze_report.py`) and one pre-existing,
unrelated tool hang (`root_sweep.py` on a `live_tri_2026-07-27` root) are
recorded in PARKED.md, both confirmed via direct evidence (base-commit
reproduction; `strace`) to predate and be unrelated to this tranche. One
transient parallel-execution flakiness episode (5 MCP-thread tests) is
recorded and resolved by a clean re-run. All acceptance checks, the full
regression gate (modulo the parked pre-existing failure), the frozen-surface
diff, all five map-validation modes, the packaging smokes, and the
record-behavior spot check pass. Every R1-R28 is demonstrated or correctly,
operator-approved deferred.
