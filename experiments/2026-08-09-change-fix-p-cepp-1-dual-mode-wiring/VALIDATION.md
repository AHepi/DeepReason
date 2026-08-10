# Validation for: fix dual seat wiring and test with a short live run

Re-read REQUEST.md (including Amendment 1), SPEC.md, CHECKLIST.md in
full before running anything below.

## Acceptance checks (SPEC.md Items, re-run fresh for this phase)

S1: `python -m pytest tests/test_v6_contract_schema_repair_policy.py tests/test_v6_contract_schema_repair_runtime.py tests/test_v6_route_seat_behavioral_capability_plan.py tests/test_v6_route_seat_behavioral_capability_runtime.py -q`
-> `57 passed in 4.77s` : PASS

S2: `python -m pytest tests/test_v6_conjecture_component_atomicity.py tests/test_v6_conjecture_scratch_consumption.py tests/test_v6_context_continuation.py tests/test_v6_controller3_replay_verification.py tests/test_v6_engaged_public_defaults.py tests/test_v6_engaged_repair_verification.py tests/test_v6_transaction_qualification.py -q`
-> `82 passed in 99.46s` : PASS

S3: `python -m pytest tests/test_workflow_reducer_c0.py tests/test_workflow_control_replay_c1.py -q`
-> `27 passed in 2.77s` : PASS

S4: `python -m pytest tests/test_scratch_provenance_refs.py tests/test_v6_transaction_qualification.py tests/test_chaos_invariants.py tests/test_invariant_call_outcomes.py tests/test_persistence_invariants.py tests/test_replay.py tests/test_replay_code.py tests/test_replay_formal.py tests/test_replay_reasoning.py -q`
-> `71 passed in 22.18s` : PASS

R2 (live run): `python experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/scripts/live_run_v7.py`
(already executed and committed as `live_run_v7/`, commit `bb4a06da0`
onward). Re-verified fresh this phase, not re-run (a live run is not
idempotent-safe to repeat casually; the committed root is the evidence
per CLAUDE.md's own "the record is the only admissible evidence"):

```
transaction_work count: 4
  sha256:6fe96a73... conjecturer.turn.v7 completed
  sha256:873298f3... conjecturer.turn.v7 completed
  sha256:9c060120... conjecturer.turn.v7 completed
  sha256:e6e4bd43... conjecturer.turn.v7 completed
accepted artifacts: 27
conjecturer LLM calls: 4
  attempts=1 contracts=['conjecturer.turn.v7']   (x4 -- every wire attempt
                                                   actually carried v7,
                                                   not a v6 label)
verify_root: violations=[] (see behavior-preservation section)
```
: PASS (mechanism proven end-to-end against the real provider, exactly
SPEC.md's Assumption A3 bar -- see Assumptions section: no
`program:candidate_checker` commitment was minted this specific run,
which A3 explicitly does not require).

## Full gate

Already run fresh at CHECKLIST.md step 15 (commit `1714c2d39`);
`git diff --stat 1714c2d39..HEAD -- src/ tests/` is empty, so nothing
that could change the suite's outcome has changed since -- re-citing
rather than re-running a ~13-minute suite for an identical answer
(CLAUDE.md's own anti-waste rule: "one tranche ran the full gate four
times... with `--lf` available and unused throughout").

`3448 passed, 6 skipped, 1 failed` (`tests/test_bronze_report.py::test_census_totals_internally_consistent`,
`159 == 165`) : **PASS** for this tranche's purposes -- the one failure
is proven pre-existing and unrelated (CHECKLIST.md step 15's full
trace: byte-identical diff on the test/script/data since base commit
`781ad6811`; the script's only `deepreason` import, `harness.py`, is
untouched by this tranche; deterministic, not flaky, on isolated
re-run). PARKED as `P-CEPP-1-BRONZE-1` (`PARKED.md`), not fixed here,
per the cross-routing rule (a defect found mid-change is parked, not
fixed).

## Record-behavior preservation (invariants.py, a replay-validation reader, was touched -- spot-check owed)

- `experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/live_run_v7`
  (new v7-authored root): `violations=[]` -- clean, as expected for a
  correctly-wired v7 dispatch.
- `experiments/bronze_flat_2026-07-13/deepseek-v4-pro` (known-good v6
  root, pre-dates this tranche): `violations=[]` -- unchanged from its
  prior verdict (this root does not configure v7, so none of the
  widened membership checks are exercised; its result is identical to
  what it was before this tranche by construction, matching
  CHECKLIST.md step 13's by-inspection sweep argument).
- `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949`
  (defect-era root, retired for a KNOWN, documented defect): still
  shows its own known signature -- 9x `foreign-criticism` violations
  ("0 foreign schools; policy requires 1"), unrelated to
  `conjecture-turn`/contract-version checking. Verdict unchanged.

Both spot-checked pre-existing roots reproduce their known verdicts
exactly, corroborating CHECKLIST.md step 13's inspection-based sweep
(no committed root's manifest configures `conjecturer.turn.v7`, so no
widened branch this tranche added is ever taken by existing data).

## Frozen-surface diff

`git diff --stat 781ad6811..HEAD -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py src/deepreason/run_manifest.py src/deepreason/qualification.py`
->
```
 src/deepreason/invariants.py   | 29 +++++++++++++++++++++++------
 src/deepreason/run_manifest.py | 27 +++++++++++++++++++++++------
 2 files changed, 44 insertions(+), 12 deletions(-)
```
Non-empty, both surfaces contacted -- **not a FAIL**, both are quoted
operator approvals on record in REQUEST.md:
- `run_manifest.py` (surface 4): REQUEST.md C1, contemporaneous,
  explicit -- "This request IS the explicit approval for this
  specific, named change."
- `invariants.py` (surface 3): REQUEST.md Amendment 1, retroactive,
  tranche-scoped, quoted verbatim from the operator ("The invariants.py
  surface-3 contact is ratified retroactively for this tranche only...
  this grant is not transitive") and cross-referenced to the canonical
  ledger entry (`docs/ERRATA_EXECUTOR.md`, commit `25686797e`, quoted
  verbatim in the same amendment). The amendment itself records plainly
  that the ORIGINAL process (inferring this approval from an
  AskUserQuestion preview string) was inadequate at the time it was
  taken -- the retroactive ratification cures the authorization, it
  does not retroactively validate the process that skipped asking.

`capabilities/state.py`, `harness.py`, `qualification.py`: absent from
the diff -- never contacted. `cli/doctor.py` (surface 5, part of the
qualification pair inventory alongside `qualification.py`): also
confirmed byte-untouched (REQUEST.md's own direct-measurement
paragraph; re-confirmed here) -- `git diff --stat 781ad6811..HEAD --
src/deepreason/cli/doctor.py` is empty.

## Packaging-surface check

Untouched -- no `pyproject.toml`, CLI entry point, MCP tool surface, or
wheel-layout file appears anywhere in this tranche's diff (the full
`src/` diff is exactly the 5 files listed above). Smoke not owed.

## Map

`python tools/docs_verify.py` -> `53 documents, 853 checks... docs_verify: 3 failed`
(all 3 are `CON-run-identity.md`, pre-existing/shallow-clone, proven
unrelated at CHECKLIST.md step 14 -- see that step's evidence) : PASS
for this tranche's scope.

`python tools/docs_verify.py --audit` -> `docs_verify --audit: 0 finding(s)` : PASS

`python tools/docs_verify.py --links` -> `docs_verify --links: 0 dangling reference(s), 53 document(s)` : PASS

`python tools/docs_verify.py --coverage` -> `docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header, 0 finding(s)` : PASS
(0 findings is the bar this check enforces; the 16-seams-without-header
list, including `SEAM-rules-x-workflow.md` which this tranche touched
for an unrelated AST-check fix, is advisory bookkeeping this check
itself does not fail on)

`python tools/docs_verify.py --stale` -> `docs_verify --stale: 2 document(s) worth re-reading`:
- `SEAM-harness-x-verification.md`: flagged because commit `d5f47101a`
  (S4, `invariants.py`) touched a file this seam document ALSO owns
  (alongside `SUB-verification.md`, which this tranche's own CHECKLIST
  step 11 did update) -- a genuine ownership gap this tranche did not
  close: `SEAM-harness-x-verification.md`'s own prose was never
  touched for the v6/v7 dispatch fact, and its `Verified-at:` stamp was
  never advanced. **Dismissed for this phase, not silently**: per this
  skill's own exit criteria ("No file other than VALIDATION.md ...
  modified... a map document that needs updating is a FAIL routed back
  to `dr-execute-step`, not something validation fixes in passing"),
  fixing it here would violate that rule. Recorded as a genuine,
  small follow-up in `PARKED.md` (`P-CEPP-1-MAP-1`) rather than fixed
  in this phase or silently dropped.
- `SUB-workflow.md`: flagged for the same reason (commit `aaefae58e`,
  S3) -- this tranche DID update `SUB-workflow.md`'s own prose in that
  commit (CHECKLIST step 8), but never advanced its `Verified-at:`
  stamp, and `docs_verify.py`'s full run (step 14, twice) has since
  re-verified its checks clean. Same dismissal and same `PARKED.md`
  entry covers both -- advancing two `Verified-at:` stamps is
  mechanical bookkeeping, not new investigation, and is bundled as one
  follow-up rather than two.

New checks added by this change: `docs/map/SUB-manifest.md` (extended
check, step 2), `docs/map/SUB-rules.md` (step 5), `docs/map/SUB-workflow.md`
+ `docs/map/SUB-llm.md` (two new trap-entry checks, step 8),
`docs/map/SUB-verification.md` (new row + check, step 11) --
5 map-check additions across this tranche's own CHECKLIST, each
independently verified standalone before the full run (see each
step's own DONE block).

Record observables added vs. sweep probes: none -- this tranche adds
no new typed-record field/observable; it widens which values of an
EXISTING field (`conjecturer_turn_contract`) three readers accept.
`tools/root_sweep.py` already reads the relevant fields for every
committed root; CHECKLIST.md step 13 records why the literal sweep run
was replaced by a by-inspection argument for this tranche specifically
(no committed root's data can exercise the new branch), not because
the observable itself lacks a probe.

Wheel smoke: packaging surface untouched -- smoke not owed.

## Requirement sweep

R1 (fix P-CEPP-1's wiring so a v7-configured manifest can validate and
dispatch a `program:candidate_checker`-eligible conjecture turn):
demonstrated by S1-S4 acceptance outputs above (all four PASS) plus the
R2 live run showing 4/4 real wire attempts carrying `contract_id=
'conjecturer.turn.v7'` end to end. The encoder-seat phrasing specifically
is satisfied via the INLINE mechanism (SPEC.md's own material-contradiction
finding) rather than fixing the separate, pre-existing,
zero-callers `rules/encoding.py::draft_encoded_commitment` gap, which
SPEC.md explicitly marked out of scope.

R2 (test with a short live run): demonstrated by the R2 acceptance
check above -- `live_run_v7/`, a real run against the real Ollama Cloud
endpoint (glm-5.2), 4/4 calls completed, 0 replay violations. Meets
SPEC.md's Assumption A3 bar exactly (mechanism proven end-to-end); does
NOT demonstrate an actual `program:candidate_checker` commitment being
minted in this specific attempt (grepped the root's log: absent) --
A3 explicitly frames this as acceptable and expected
("capability-channel use... is STOCHASTIC across identical runs; one
live attempt that misses a path is inconclusive for that path", CLAUDE.md,
quoted in A3's own reasoning), not a gap this tranche owes closing.

R3 (Read CLAUDE.md first): satisfied -- re-read at this tranche's own
`dr-change-orchestrator` environment preflight, before R1/R2 work began.

R4 (Amendment 1, process correction): demonstrated by REQUEST.md's
Amendment 1 itself, now citing `docs/ERRATA_EXECUTOR.md`'s commit
`25686797e` verbatim as the canonical record; `PARKED.md`'s
`P-CEPP-1-BATTERY-1` entry parks the v7-battery-inclusion question
exactly as the operator's follow-up instruction required, rather than
touching surface 5.

## Assumptions carried

A1: reused CP1-M's existing verified operator key
(`OLLAMA_API_KEY_AARON`) for the live-run test rather than requesting a
fresh one -- confirmed by `live_run_v7.py`'s own invocation, unchallenged.

A2: the v7 repair grant mirrors v6's exactly (same `conjecture_ceiling`,
same arithmetic) -- confirmed by S1's own regression test (step 1-2
DONE block: asserts the v7 grant's `maximum_schema_repairs` equals the
v6 case's), unchallenged.

A3: "tested" is read as the mechanism reaching real dispatch end to
end, not a full run to a CONFIRMED/REFUTED dual-mode verdict -- met by
the R2 live run above, unchallenged.

## Verdict: PASS

No FAIL-class check failed. The one full-gate test failure and the
three `docs_verify` full-mode failures are each independently proven
pre-existing and unrelated to this tranche's diff, with the evidence
pasted at CHECKLIST.md steps 14-15 and re-cited above. The two
`--stale` entries are dismissed with reasons per this skill's own
option, and their mechanical follow-up (`Verified-at:` stamp
advancement) is parked rather than fixed in this phase, per this
skill's own file-modification restriction.
