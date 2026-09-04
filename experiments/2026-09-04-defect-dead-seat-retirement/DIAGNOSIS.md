<!-- tranche: 2026-09-04-defect-dead-seat-retirement -->

# Diagnosis: a typed per-seat exhaustion is answered by a fail-closed WHOLE-RUN exit, because the school loop has no arm that skips a seat

## Stop report, section 4 (pasted verbatim, before anything of mine)

Command, run 2026-09-04 on this branch; full transcript at `proof/stop_report.txt`:

    deepreason stop-report experiments/2026-09-01-live-all-modules-p-a1/run

    ## 4. THE STOP, CLASSIFIED
    
    Stop message: `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at /workflow/insufficient_capability_by_route_seat: route seat has terminally exhausted its smallest authorized contract`
    
    Boxes ranked by evidence:
    
    ### 1. ENVIRONMENT — SUPPORTED
    
    - evidence FOR: transport wall: 41 RemoteDisconnected on endpoint ollama-glm-5.3
    
    ### 2. HARNESS — NO EVIDENCE EITHER WAY
    
    - note: not claimable: ENVIRONMENT, MODEL still holds evidence. A harness verdict requires the other three to be ruled out.
    
    ### 3. CONFIGURATION — RULED OUT
    
    - evidence RULING IT OUT: 6 field(s) were restored at run time from notices (listed below), but the stop names none of them; no run-config was supplied to diff against the manifest, so a mismatch there cannot be ruled out — re-run with --config to close that gap
    - note: ADJUDICATION_STATUS_AUTHORITY_ENABLED = true was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/ADJUDICATION_STATUS_AUTHORITY_ENABLED)
    - note: ENGAGED_CRITICISM_AUTHORITY = "defended_trial" was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/ENGAGED_CRITICISM_AUTHORITY)
    - note: JUDGE_SEATS_ENABLED = true was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/JUDGE_SEATS_ENABLED)
    - note: JUDGE_SUMMONS_PER_CYCLE = 2 was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/JUDGE_SUMMONS_PER_CYCLE)
    - note: LEGACY_CRITICISM_ENABLED = false was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/LEGACY_CRITICISM_ENABLED)
    - note: SCHOOL_SEATS_ENABLED = true was NOT carried by the compiled manifest; restored at run time from notice (/engine_config/SCHOOL_SEATS_ENABLED)
    - note: reasoning omitted → provider default on: argumentative_critic#0 (deepseek-v4-pro:0813), conjecturer#0 (deepseek-v4-pro:0813), conjecturer#1 (glm-5.3), defender#0 (glm-5.3), grounding_reviewer#0 (glm-5.3), judge#0 (qwen3.5:397b), judge#1 (gpt-oss:120b), property_designer#0 (deepseek-v4-pro:0813), summarizer#0 (glm-5.3), synthesizer#0 (glm-5.3), thesis#0 (deepseek-v4-pro:0813), variator#0 (deepseek-v4-pro:0813), vision_critic#0 (glm-5.3) — an omitted knob is the provider's DEFAULT, not 'off'. NO PROFILE ENTRY consulted: whether these models need an explicit value is a model-profile question
    - note: split protocol armed on: argumentative_critic#0, conjecturer#0, conjecturer#1, defender#0, judge#0, judge#1 — the split arms on an omitted knob
    
    ### 4. MODEL — SUPPORTED
    
    - evidence FOR: the stop names seat exhaustion: "V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at /workflow/insufficient_capability_by_route_seat: route seat has terminally exhausted its smallest authorized contract"
    - evidence FOR: argumentative_critic#0: 1 rejected completion(s) truncated at the cap
    - evidence FOR: conjecturer#0: 1 attempt(s) rejected at /candidates/0/discharges/1/kind
    - evidence FOR: conjecturer#0: 1 attempt(s) rejected at /candidates/2/counterconditions
    - evidence FOR: conjecturer#0: 12 rejected completion(s) truncated at the cap
    - evidence FOR: conjecturer#1: 3 rejected completion(s) truncated at the cap
    - evidence FOR: defender#0: 2 rejected completion(s) truncated at the cap
    - note: argumentative_critic#0 passed qualification 20/20 first-pass on batch-critic.v2 with 0 repairs
    - note: argumentative_critic#0 passed qualification 20/20 first-pass on config-referee.v1 with 0 repairs
    - note: argumentative_critic#0 passed qualification 20/20 first-pass on critic.atomic-target.v1 with 0 repairs
    - note: conjecturer#0 passed qualification 20/20 first-pass on conjecturer.atomic-candidate.v1 with 0 repairs
    - note: conjecturer#0 passed qualification 20/20 first-pass on conjecturer.turn.v6 with 0 repairs
    - note: conjecturer#0 passed qualification 20/20 first-pass on scratch.block.compact.v1 with 0 repairs
    - note: conjecturer#0 passed qualification 20/20 first-pass on scratch.block.minimal.v1 with 0 repairs
    - note: conjecturer#1 passed qualification 20/20 first-pass on conjecturer.atomic-candidate.v1 with 0 repairs
    - note: conjecturer#1 passed qualification 20/20 first-pass on conjecturer.turn.v6 with 0 repairs
    - note: defender#0 passed qualification 20/20 first-pass on defender.direct.v1 with 0 repairs
    - note: judge#0 passed qualification 20/20 first-pass on judgeruling.direct.v1 with 0 repairs
    - note: judge#1 passed qualification 20/20 first-pass on judgeruling.direct.v1 with 0 repairs
    - note: a seat that passed its form at full marks did not lose the ability between qualification and the run — look to CONFIGURATION or ENVIRONMENT first
    

---

## Primary cause

**The run already knows, typed and durably, that one route seat is finished
— and the only thing it can do with that knowledge is die.** When
`conjecturer#1` (glm-5.3) walked its contract ladder to the smallest
authorized contract and exhausted that too, `TransactionService.terminate`
minted a `RouteSeatInsufficientCapabilityV1` record and replay put it in
`WorkflowReplayState.insufficient_capability_by_route_seat`, keyed by
`(role, seat, endpoint_id, route_sha256)` — a **per-seat** map, not a
run-wide flag. Four sites then refuse any further dispatch on that key: three
in `workflow/transaction_service.py` raise `RunManifestError`
("V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY"), and `llm/adapter.py`'s live
pre-dispatch recheck raises `WorkflowAuthorizationError`. Those refusals are
correct and must stay. What is missing is a caller that treats a per-seat
refusal as a per-SEAT event. `Scheduler._conjecture`'s school loop
(`scheduler.py:2347-2530`) has exactly three exception arms: `WorkBudgetDenied`
→ record a diagnostic and `continue` to the next school;
`(SchemaRepairError, EndpointError)` → drop and `continue`; and
`(RouteFirewallError, TokenBudgetExceeded, WorkflowAuthorizationError)` →
**re-raise as a fail-closed scheduler exit**. `RunManifestError` matches no arm
at all, so it propagates untouched to `application/text_runs.py`'s terminalizer
and becomes `state: failed`, `stop_reason: operational_failure`. The
run-result names the exact class: `"error_type": "RunManifestError"`. That is
why one seat's death is the run's death — not because the harness cannot tell
the seats apart, but because the only two dispositions the loop offers a seat
refusal are "skip this school" (which nothing selects) and "end the run"
(which the absence of an arm selects by default).

The school→seat table is what makes the loss concrete. P-A1's manifest binds
`school-0` and `school-2` to `conjecturer#0` (deepseek) and `school-1` and
`school-3` to `conjecturer#1` (glm-5.3), while all four schools' critic
bindings point at the healthy deepseek seat. Half the conjecture capacity and
all of the criticism capacity were alive when the run stopped at cycle 5, with
1 093 086 of 3 000 000 tokens spent.

## Evidence

- **`proof/stop_report.txt` §3** (non-code) — every fault in the run is on the
  one endpoint: `conjecturer#1 ollama-glm-5.3` 17 attempts / 6 zero-token /
  `RemoteDisconnected ×23`; `defender#0 ollama-glm-5.3` 8 / 4 / `×18`;
  `conjecturer#0 ollama-deepseek-v4-pro-0813` **30 attempts, 0 zero-token,
  faults `none`**; `argumentative_critic#0` on the same deepseek endpoint,
  12 attempts, faults `none`. The healthy half of the run never faulted once.
- **`proof/stop_report.txt` §4** (non-code) — ENVIRONMENT SUPPORTED on
  "transport wall: 41 RemoteDisconnected on endpoint ollama-glm-5.3";
  CONFIGURATION RULED OUT; and the report's own closing note, "a seat that
  passed its form at full marks did not lose the ability between qualification
  and the run". §2 records both conjecturer seats at 20/20 first-pass, 0
  repairs, on every form.
- **`objects/workflow-route-seat-insufficient-capability-v1/6d38272…json`**
  (non-code) — ONE record for the whole run:
  `route_lease {"endpoint_id": "ollama-glm-5.3", "role": "conjecturer",
  "seat": 1}`, `reason "smallest_authorized_contract_schema_exhausted"`,
  `contract_id "conjecturer.atomic-candidate.v1"`,
  `attempted_contract_ids` = `conjecturer.turn.v6` ×5 → `.atomic-candidate.v1`
  ×2. The typed fact naming ONE seat already exists in the record.
- **Work-terminal census over `objects/`** (non-code, `proof/terminal_census.txt`)
  — per route seat: `conjecturer#0` 9 completed / 15 rejected / 1 abandoned,
  **0 transport_failed, 0 schema_exhausted**; `conjecturer#1` 2 completed /
  7 rejected / **6 transport_failed / 2 schema_exhausted**; `defender#0`
  2 completed / 2 rejected / 4 transport_failed. Only the glm-5.3 seats have
  a transport or exhaustion terminal anywhere in the run.
- **Log position** (non-code) — the exhaustion record enters the log at
  **seq 636**; the run's `run-stop` is at **seq 659** and the log ends at 660.
  The run survived 23 further events after the seat died and then hit the
  refusal on the next dispatch to that same seat. It did not stop deciding to
  stop; it stopped by raising.
- **`run-result.json`** (non-code) — `"error_type": "RunManifestError"`,
  `"error": "V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
  /workflow/insufficient_capability_by_route_seat: …"`, `"state": "failed"`.
  A `RunManifestError` is what the school loop does not catch.
- **`run-manifest.json`** (non-code) — `control_plane_policy.school_execution`
  is `route_bound` with bindings school-0→seat 0, school-1→seat 1,
  school-2→seat 0, school-3→seat 1; `criticism_policy.bindings` put all four
  schools' critics on seat 0. The surviving capacity is not hypothetical: it
  is two of four conjecture schools and all four criticism bindings.

## Implicated code (three sites)

- `src/deepreason/scheduler/scheduler.py:2481-2523` — the school loop's three
  exception arms. `RunManifestError` matches none of them; the third arm
  re-raises `WorkflowAuthorizationError` by design, which is the same death by
  the adapter's road.
- `src/deepreason/workflow/transaction_service.py:196, 263, 556` —
  `_require_open_preparation`, `prepare`, `record_provider_attempt`: the three
  per-seat refusals. Correct as refusals; they have no caller that can absorb
  one.
- `src/deepreason/workflow/replay.py:2690-2696` +
  `transaction_service.py:645-667` — where the per-seat exhaustion becomes
  durable state. **This is the fact a retirement would be built on, and it
  already exists**; the design question FIX.md must answer is whether a new
  typed event kind is needed at all, or whether this record plus a notice is
  the retirement.

## Falsifiable prediction (what `dr-reproduce` must show)

Against the deterministic offline stub, a v6 run with two conjecturer seats —
seat 1's endpoint always faulting, seat 0's always answering — and
`route_bound` school execution binding at least one school to each seat:

    python -m pytest tests/test_dead_seat_retirement.py::test_p_a1_shape_dies_on_the_healthy_seat_today -q

must FAIL on the pre-fix tree with a `RunManifestError` whose message contains
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`, on a run whose seat-0 schools had
completed work and whose token budget was not exhausted. If instead the stub
run stops for any other reason, or the exception is `WorkflowAuthorizationError`
rather than `RunManifestError`, this diagnosis is wrong about which road the
death takes and must be rewritten before any fix.

## Ruled out

**"The glm-5.3 seat was mis-qualified, so the run was right to stop."** The
record refuses it twice. Stop report §2 records `conjecturer#1` at 20/20
first-pass with 0 repairs on both `conjecturer.turn.v6` and
`conjecturer.atomic-candidate.v1`, and §4's own closing note states the
inference. And the exhaustion is downstream of transport, not of capability:
6 of that seat's 17 attempts returned zero tokens after `RemoteDisconnected`,
which the schema-repair ladder counts as a failed attempt like any other. The
seat did not lose the ability to fill the form; it lost the ability to reach
the provider. Whether the ladder SHOULD count a transport fault against the
repair budget is a second, independent question — parked, not diagnosed here
(`PARKED.md` P1 of this tranche).

## Not a recurrence, but the map has watched it happen three times

`docs/map/SUB-llm.md:240`, `docs/map/SUB-scratch.md:179` and
`docs/map/SEAM-llm-x-rules.md:287` each record "the seat exhausted its smallest
authorized contract and the run died" — twice as the tail of a repair-loop
trap, once as the last item in a "what breaks first" list. In all three the
death is written down as the CONSEQUENCE of some other defect and never as a
defect itself. No `Traps` entry anywhere says a run holding a healthy seat
should have survived. This is a new failure mode by that test, and
`dr-implement-fix` owes it a `Traps` entry naming run `4565139800f5ca02`.
