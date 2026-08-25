# PARKED — found in this tranche, deliberately not fixed here

One tranche, one goal (CLAUDE.md cross-routing). Each item is a finding,
not a task for this tranche, and each carries a ready-to-send prompt so the
follow-up costs a paste rather than an authoring session.

---

## P1 — qualification is intermittently red at one seat contract

**What.** The production-contract battery on the P-C1 manifest fails about
half the time, always at the same place: `critic.atomic-target.v1`
(`argumentative_critic`, glm-5.2) returns one schema-invalid first pass in
20, and the repair path then edits outside its permitted scope —
`REPAIR_SCOPE_VIOLATION`. One such case disqualifies the entire battery.
Observed across five batteries on identical inputs: FAIL, VOID (agent
error), PASS, FAIL, PASS. Evidence: `qualify.json`,
`qualify-attempt1-report.json`, `qualify-attempt3.json`,
`qualify-retry-1.json`.

**Why it matters.** It costs ~3 minutes and a full battery per attempt, it
makes every launch a coin flip, and it is exactly the seam the cycle soak
declares it CANNOT cover offline (`D1-seat-contract` returns `[PART]`:
"the deterministic stub always returns a schema-valid response, so
attempt_index never advances past 0 offline"). The instrument named its own
blind spot and the live run failed there. It is plausibly the same defect
family as P3 below.

```
Route: deepreason-orchestrator (defect).
Goal: one bounded tranche — decide whether REPAIR_SCOPE_VIOLATION on
critic.atomic-target.v1 is a defect in the repair path's scope computation
or correct enforcement against a genuinely out-of-scope model edit.
Evidence, all committed: experiments/2026-08-25-change-constructive-frontier/
{qualify.json, qualify-attempt1-report.json, qualify-attempt3.json,
qualify-retry-1.json} — five batteries, identical manifest, ~50% pass rate,
failure always on the same contract_id. Start from the typed record, not
code: the failing case carries failure_code REPAIR_SCOPE_VIOLATION and
scope_violations=2 against repair_count=2, i.e. BOTH repair attempts
violated scope, which is what makes "the model wandered" a weak
explanation. Read docs/map/SEAM-llm-x-workflow.md before either subsystem.
End state: DIAGNOSIS.md naming one cause, plus a REPRO against the
committed reports. Do not change the soak; its D1 [PART] is honest.
```

---

## P2 — a run's own token counter reads zero after 292 provider calls

**What.** `deepreason results` printed `tokens spent vs budget: 0 /
3000000` for run `1950b3d0ee228113…`, which had made 292 provider calls
totalling 702 789 tokens by the log's own `llm.tokens` fields.
`run-status.json` carries `"token_spend": 0` and every `progress.jsonl`
line carries `"token_spend": 0`.

**Why it matters.** More than cosmetic. If that counter is what a
budget-bound stop consults, a run can never stop on `budget_exhausted` — it
would run to its cycle bound or to an operational failure regardless of
spend. This tranche's matched-budget rule had to be re-pointed at the log
to be enforceable at all (`score_run.py::_tokens`).

```
Route: deepreason-orchestrator (defect).
Goal: one bounded tranche — determine why token_spend stays 0 in
run-status.json and progress.jsonl while log.jsonl's llm blocks carry real
per-call token counts, and whether any budget-bound stop path reads the
zeroed field.
Evidence, committed: experiments/2026-08-25-change-constructive-frontier/
run/{run-status.json,progress.jsonl,log.jsonl} and results.txt. Note the
soak reaches stop_reason='budget_exhausted' offline, so the stub path DOES
increment something — compare the two.
End state: DIAGNOSIS.md naming one cause and stating explicitly whether
budget-bound stopping is affected. If it is, that is a severity escalation,
not a reporting bug.
```

---

## P3 — V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY ended a healthy run at cycle 15

**What.** Run `1950b3d0ee228113…` terminated `failed` /
`operational_failure` at cycle 15 of 24 with
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
/workflow/insufficient_capability_by_route_seat`: "route seat has
terminally exhausted its smallest authorized contract". `verify_root` is
clean and a terminal was committed, so the record is sound — but the run
had spent only 702 789 of 3 000 000 tokens and was still producing
artifacts.

**Why it matters.** A run that stops at 23% of its token budget on a seat
capability exhaustion, with no repair exhaustion recorded
(`run-stop.json` carries `"repair_exhausted": false`), loses most of the
depth it was configured for. R20's "cycles sized deep" cannot be delivered
if a seat exhausts at cycle 15.

```
Route: deepreason-orchestrator (defect).
Goal: one bounded tranche — explain why a route seat terminally exhausted
its smallest authorized contract at cycle 15 while run-stop.json records
repair_exhausted=false, and say whether the two are consistent.
Evidence, committed: experiments/2026-08-25-change-constructive-frontier/
run/{run-status.json,run-stop.json,log.jsonl}. The terminal is at seq 3199
(control action terminal_committed); the stop Measure event is seq 3198.
Search the Control events for the workflow decision that set
insufficient_capability_by_route_seat — it is NOT in the log as a plain
string, so start from the control event payloads.
Likely related to P1 (same seat-contract family, same critic route).
End state: DIAGNOSIS.md naming one cause.
```

---

## P4 — a failed run writes no survivor record, so survivor figures vanish

**What.** `deepreason results` reports `survivors ... — not recorded
(NO_SURVIVOR_RECORD)` and `frontier ... — not recorded
(NO_FRONTIER_RECORD)` for a run that reached a committed terminal with a
clean `verify_root` and 909 accepted artifacts.

**Why it matters.** This is NOT the poietics P4 inflation defect (import-role
records counted as survivors); it is the opposite failure. R31 told this
tranche to quote conjecture-only survivor figures, and there were none to
quote — both the raw and the filtered count came back 0. A run that
terminates on an operational failure therefore says nothing at all about
survivors, which is a large hole in what a failed-but-valid record can be
asked.

```
Route: deepreason-orchestrator (defect).
Goal: one bounded tranche — decide whether a run terminating with
stop_reason=operational_failure SHOULD write a survivor/frontier record,
and if so why this one did not, given verify_root is clean and a terminal
was committed.
Evidence, committed: experiments/2026-08-25-change-constructive-frontier/
{results.txt, run/run-result.json (absent or empty), run/run-status.json}.
Contrast with the poietics P-R1 root, which DID write survivors.
Note the related-but-distinct poietics P4 (survivor inflation from
import-role records) is still open; do not conflate them.
End state: DIAGNOSIS.md, and an explicit statement of which terminal states
are supposed to carry a survivor record.
```

---

## P5 — the criteria preflight cannot catch a wire-format shape error

**What.** `preflight_criteria.py` passed cleanly while the battery it was
guarding matched **0 of 1509 artifacts** in a live run, because every
fixture it tested was in the plain-text shape the criteria assumed, not the
JSON-envelope shape the seats actually emit. Fixed WITHIN this tranche
(fixture M9 now pins the envelope), so this entry is a note about the
GENERAL gap, not about the specific bug.

**Why it matters.** The preflight exists to catch
`DR-SEAM-evaluation-x-ontology`'s "a malformed `predicate:` is a REFUTATION,
not an error". It catches malformed EXPRESSIONS. It cannot catch a
well-formed expression pointed at the wrong SHAPE, and that failure looks
identical in the record: everything refuted, no error anywhere. Any future
tranche writing `predicate:` criteria over model output inherits this.

```
Route: dr-change-orchestrator (change, not defect).
Goal: one bounded tranche — make it impossible for a predicate battery to
ship untested against the shape its seats actually emit. Smallest viable
form: a shared fixture helper that wraps any plain-text candidate in the
seat's real envelope (output_mode json_object), so every criteria preflight
tests BOTH shapes by construction rather than by the author remembering.
Evidence: experiments/2026-08-25-change-constructive-frontier/PREREG.md's
appendix records the full incident with measured numbers (0 of 1509 vs 183
of 1509). checker.py's fixture M9 is a worked example of the wrapping.
Bound it: this is a test-helper change, NOT a change to programs.py or to
any frozen surface.
```
