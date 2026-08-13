# VALIDATION.md — defended_trial criticism authority wired into v6

Verdict: **PASS**

Validates every acceptance check in SPEC.md §5, plus the full DeepReason
gate. Validation only — no code changed in this phase.

## SPEC.md §5 acceptance checks

- **R1** (trial calls carry `dispatch_authorization`): PASS.
  `tests/test_v6_defended_trial_transaction_wiring.py::
  test_defender_and_judge_calls_carry_dispatch_authorization_under_v6`
  drives `run_argument_trial_from_case` end to end under a v6-bound
  adapter and asserts three `WorkflowTaskKind.DEFENDED_TRIAL_STEP` work
  items (one defender, two judge seats), each `.authorization is not
  None`, each `.terminal.status == "completed"`, and that every
  `LLMCall`'s `dispatch_authorization_ref` matches its work item's
  authorization id.
  `test_unbound_trial_defender_call_is_refused_by_the_global_v6_guard`
  proves the precondition the fix satisfies (the unconditional guard
  still refuses an unbound call) rather than bypassing it.
- **R2** (recovery resolves real authority, never downgrades silently):
  PASS. `test_recovered_observe_only_criticism_resumes_observe_only`
  (unaffected direction) and
  `test_recovered_defended_trial_criticism_defers_an_attacking_case_
  instead_of_downgrading_to_observe_only` (the fixed direction — asserts
  no `_observe_case`-shaped critic artifact and exactly one typed
  `"defended-trial-deferred"` Measure, idempotent under re-recovery)
  both pass.
- **R3** (compile gate retired, not converted to a notice):
  PASS. `tests/test_v6_manifest_defended_trial.py`'s two tests compile a
  `defended_trial`-authorized v6 manifest successfully and assert the
  granted behavioral contracts by name.
- **R4** (both recovery directions regression-tested): PASS, same tests
  as R2.
- **R5** (offline regression is the primary proof): PASS, same as R1.
- **R6** (guarded live attempt): NOT ATTEMPTED — no provider credentials
  in this container (checked and recorded in CHECKLIST.md step 15). Per
  REQUEST.md R6's own text this does not block validation; R5 is the
  proof either way.
- **R7/R8** (surface census): PASS, with one addendum the original
  census in SPEC.md §4 did not anticipate — found and fixed during
  execution, recorded in CHECKLIST.md step 9 and DELIVERY.md's own
  section below: `cli/doctor.py::ProductionContractPairV1.contract_id`
  (a closed Literal enumerating the offline qualification battery's
  known contracts) needed the same three additive entries as the
  manifest-side grant, plus new probe-pack branches to actually exercise
  them. This is surface-5-adjacent (qualification), additive only,
  verified by the full `test_cli_production_doctor_v6.py` suite passing.
- **R9** (map docs move with the code): PASS — see CHECKLIST.md step 10;
  `docs_verify.py` full run confirms currency (see below).
- **R10** (errata check): PASS — no entry needed, recorded in
  CHECKLIST.md step 16.

## The full gate

```
python -m pytest tests/ -q -n 4
3539 passed, 7 skipped, 1 failed in 707.92s (0:11:47)

FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
```

This is the exact, documented pre-existing baseline failure (CLAUDE.md:
"1 pre-existing test_bronze_report failure"). No MCP-thread flakes
surfaced in this run. **0 unexplained failures.**

## docs_verify full

```
python tools/docs_verify.py
docs_verify: 3 failed
```

All three are `CON-run-identity.md` (shallow-clone `git log`/`git show`
checks over commits this container's clone does not carry) — the exact
documented pre-existing baseline (CLAUDE.md: "3 pre-existing
CON-run-identity.md shallow-clone failures"). **0 unexplained failures.**

Getting to this baseline required fixing 14 map-doc checks that this
tranche's own diff moved (coupling counts, exact synthetic error
messages) — see CHECKLIST.md step 10 and the commit history. None of
those 14 were defects; each is `docs_verify.py` doing its job (a
document that no longer matches the code is a document that lies).

## Root sweep

```
python tools/root_sweep.py /tmp/root-sweep-after-fix.txt
SWEEP COMPLETE: 103 roots
```

11 ERROR (all `UnsupportedRunManifestVersionError`, the documented
baseline), 84 `valid=True`, 8 `valid=False` (pre-existing, deliberately
invalid fixture roots — e.g. the rung5 "rr-home" alternative-backend
test root). No anomaly.

**This is where a real regression was caught before delivery**, not
after: the FIRST version of the manifest-side fix (R7) granted
defender/judge/variator contracts unconditionally by route presence.
`docs_verify.py`'s own re-derivation checks (which open committed roots
as part of proving several `DR-SEAM` documents' claims) failed with
`INVALID_RUN_MANIFEST` on `experiments/live_engaged_2026-07-27/
run-f4fa6663e5412d64df943a5a22342baf` — an already-committed v6 root
whose `judge` route exists for the (unrelated) rubric-trial feature,
under `criticism_policy.authority == "observe_only"`. The behavioral
capability plan is recomputed and compared against the stored plan on
every reload (`_production_routes_are_concrete`), so the wider grant
retroactively demanded repair authority no historical manifest's frozen
`contract_schema_repair_policy` carried — the root stopped loading
entirely. Fixed by narrowing the grant to `criticism_policy.authority ==
"defended_trial"` (the same scope the retired compile gate itself used).
Verified two ways: (1) a direct load of all 106 committed roots
(`Harness(root, read_only=True)` in a loop) with zero exceptions, and (2)
the root sweep above.

## Verdict

PASS. Every acceptance check in SPEC.md §5 either passed with pasted
proof or is honestly recorded as not attempted (R6, credentials
unavailable) with its accepted fallback (R5) standing. The gate, sweep,
and docs battery all match their documented pre-existing baselines with
zero unexplained deviation.
