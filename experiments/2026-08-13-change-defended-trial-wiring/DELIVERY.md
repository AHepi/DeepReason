# Delivered: defended_trial criticism authority wired into v6
Branch: `claude/v6-defended-trial-wiring-07hs1u` @ `8d924ade1` (pushed, tree clean)

## What changed

The defended trial (a defender argues back, a cross-model panel of
judges rules — the harness's toughest criticism mode) can now run on
RunManifest v6 (the current transactional run format). Before this
change it was compile-refused for every v6 run, because its two
provider calls (defender, judge) never carried the authorization token
every other v6 model call requires — deleting that refusal without
fixing the calls would have turned a free pre-run rejection into a paid
mid-run crash the first time a defender spoke.

`informal/trial.py`'s defender and judge calls now go through the same
authorization pipeline (`InquiryTransactionService`) the ordinary critic
call already uses, via a new helper (`_v6_transactional_trial_call`)
mirroring the existing critic-call and bridge-call wiring exactly — no
new contract shape invented. `run_manifest.py` grants the defender/judge
seats the wire authority they need, narrowly (only when the run's
criticism authority is actually set to `defended_trial`), so that no
already-recorded run is retroactively broken. The v6 compile-time
refusal (`V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`) is retired
outright — the wiring makes it moot.

Separately: if a run crashes mid-criticism and gets resumed, the
recovery code used to force every criticism authority down to
"observe only" (record-but-don't-rule) regardless of what the run was
actually authorized to do. That is fixed too — a resumed run keeps its
real authority. A case that would need the actual trial to resolve (and
crash-recovery has no live model to run one with) is now left open for
the next live cycle to reconsider, rather than silently answered under
the wrong rule.

A regression was found and fixed mid-tranche, before delivery: the first
version of the manifest grant broke replay of an already-committed,
unrelated v6 run — caught by the documentation-verification tool, not by
the test suite. Full account below and in VALIDATION.md.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | Wire defender/judge calls through `InquiryTransactionService` the way the ordinary critic call already is | done | commits `d2cfd2846`, `1247a1766`; VALIDATION.md R1 |
| R2 | Recovery must resolve the run's real criticism authority instead of hardcoding observe_only | done | commit `d2cfd2846`; VALIDATION.md R2 |
| R3 | Convert `V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED` — retire or notice, only after R1 is green | done (retired outright, wiring made it moot) | commit `d2cfd2846`; VALIDATION.md R3 |
| R4 | Regression tests for both recovery directions | done | commit `d2cfd2846`; VALIDATION.md R4 |
| R5 | Offline regression proving R1 (mock endpoint, dispatch_authorization present) | done | commit `d2cfd2846`; VALIDATION.md R5 |
| R6 | One guarded live attempt; offline regression remains the proof either way | not attempted, no operator authority to skip needed — REQUEST.md's own text already accepts this outcome | VALIDATION.md R6; no `OLLAMA_API_KEY`/provider credentials present in this container (checked `env` and every `experiments/*/env` handover path) |
| R7 | Pre-granted surface census (4, 3, 2, 5) | done, one addendum found during execution | commit `d2cfd2846`; see "Surface census, reconciled" below |
| R8 | Enumerate every surface contact with its grant line | done | SPEC.md §4, extended below |
| R9 | Map documents move in the same commits as the code | done | commits `d2cfd2846` (SUB-workflow.md initial pass), `733e37db0` (14 checks `docs_verify.py` caught after the diff, plus the SEAM-rules-x-workflow.md Trap rewritten FIXED) |
| R10 | Errata entry if any committed doc claims defended_trial already works | done — none needed | see Errata section below |
| R11 | Gate discipline (ring while iterating, full gate at boundary) | done | VALIDATION.md; full gate 3539 passed/7 skipped/1 failed (documented baseline) |
| R12 | Commit/push every phase boundary, R-by-R reconciliation at delivery | done | five commits this tranche, all pushed; this table |

No amendments were made to REQUEST.md; no requirement is deferred.

## Surface census, reconciled against SPEC.md §4

SPEC.md's original census (§4) named surface 4 (manifest schemas +
validators, both the gate conversion and the behavioral-plan widening)
and surface 5 (qualification digest drift) as the only real contacts,
with surfaces 2 and 3 explicitly found NOT touched. Execution confirmed
2 and 3 stayed untouched, and found **one surface-5-adjacent contact the
original census missed**: `cli/doctor.py::ProductionContractPairV1.
contract_id` — a closed `Literal` enumerating every contract id the
offline qualification battery (the ~14-minute, ~1,100-call test that
certifies a model can fill each role before a real run may use it) knows
how to probe. Granting defender/judge/variator seats a wire contract on
the manifest side (surface 4) meant the qualification doctor now had to
recognize and probe those same three contracts, or qualification itself
would crash on any run that configures them. Widened additively (both
`.direct.v1` and `.compact.v1` variants, for future-proofing against
either model-profile choice) plus three new probe-pack branches. Every
touched test in `test_cli_production_doctor_v6.py` and
`test_v6_contract_schema_repair_policy.py` passes.

## The regression found and fixed mid-tranche

The manifest grant's first version was **too wide**: it granted the new
defender/judge/variator contracts to any route configured for those
roles, regardless of why. `judge` is also the rubric-trial role
(unrelated to criticism authority), so many already-committed v6 runs
have a judge route configured under `observe_only` criticism authority.
The manifest's behavioral-authority plan is re-derived and compared
against its own stored copy every time an existing run is re-opened —
that is the mechanism that catches a manifest schema drifting out from
under old evidence — so the wider grant made every such historical run
fail to re-open at all (`INVALID_RUN_MANIFEST`, discovered against
`experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf`).
This is exactly the one law the harness treats as non-negotiable: an
already-recorded run must never be invalidated by a later code change.

Found by `python tools/docs_verify.py` (the tool that re-derives and
checks every claim in the documentation, some of which open real
committed runs to prove themselves) — not by the test suite, which
never happened to open that specific run. Fixed by narrowing the grant
to fire only when a run's criticism authority is actually set to
`defended_trial` (the same condition the retired compile-time refusal
itself used). Verified two ways: every one of the 106 committed runs in
this repository now re-opens without error, and the dedicated replay
sweep tool (`root_sweep.py`) reports its documented, unchanged baseline
across all 103 runs it covers. Full account in VALIDATION.md.

## Map delta

Changed: `docs/map/SUB-workflow.md` (new Traps entry — why
`DEFENDED_TRIAL_STEP` deliberately has no crash-recovery admission path;
one stale test-name fix), `docs/map/SEAM-manifest-x-schools.md` (three
rows — the retired gate, the widened recovery authority check, the
qualification-inventory row), `docs/map/SEAM-harness-x-workflow.md`,
`docs/map/SEAM-llm-x-manifest.md`, `docs/map/SEAM-llm-x-workflow.md`
(four checks — a new module crossed several documented coupling
thresholds), `docs/map/SEAM-rules-x-workflow.md` (one coupling count,
one Trap entry documenting R2's own defect rewritten FIXED),
`docs/map/SEAM-scratch-x-workflow.md` (one coupling count). Created:
none. New checks added: 2 (the two new Traps entries in SUB-workflow.md
and SEAM-rules-x-workflow.md each carry their own `check:` line). Left
stale: none found — `python tools/docs_verify.py` full run passes at
its documented pre-existing baseline (3 `CON-run-identity.md`
shallow-clone failures, unrelated to this tranche).

## Errata

None. No committed document was found claiming defended_trial already
worked on v6 — every map document that (correctly, at the time)
documented the refusal was updated in the same commit as the code that
retired it, which is ordinary map maintenance, not a correction to a
claim that was wrong when made. `docs/ERRATA.md` tail re-read through
E24; next free number would be E25 if this tranche ever needed one.

## Parked (not done, not promised)

None. No defect was found mid-tranche that fell outside this change's
scope, and no change was wished for that fell outside diagnosis. The
one thing this tranche deliberately leaves undone — rubric trial and
pairwise discrimination staying unwired to v6 — is not parked because it
is not broken: both are already safely deferred under v6 by
`Scheduler._defer_untransactional_v6_phase` (typed completion debt,
never an unauthorized dispatch), and REQUEST.md's own compile-gate scope
(`criticism_policy.authority`) never reached either path. If the
operator ever wants those wired too, that is a fresh, separately-scoped
change request — the pattern this tranche built
(`_v6_transactional_trial_call`) is the direct template for it.

## PROOF (gate output, not the word "done")

```
python -m pytest tests/ -q -n 4
3539 passed, 7 skipped, 1 failed in 707.92s (0:11:47)
FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
  (documented pre-existing baseline — CLAUDE.md: "1 pre-existing
  test_bronze_report failure")

python tools/docs_verify.py
docs_verify: 3 failed
  (all CON-run-identity.md — documented pre-existing baseline —
  CLAUDE.md: "3 pre-existing CON-run-identity.md shallow-clone failures")

python tools/root_sweep.py
SWEEP COMPLETE: 103 roots
  11 ERROR (all UnsupportedRunManifestVersionError, documented baseline)
  84 valid=True, 8 valid=False (pre-existing deliberately-invalid fixtures)
  no anomaly

python -c "... load every committed root as a Harness ..."
  106 roots, 0 errors (confirms the mid-tranche regression is fully fixed)

python -m pytest tests/test_v6_defended_trial_transaction_wiring.py \
  tests/test_v6_nonconjecture_recovery.py \
  tests/test_v6_manifest_defended_trial.py -q
41 passed
```

Everything above is reproducible from the branch head; full detail in
VALIDATION.md.
