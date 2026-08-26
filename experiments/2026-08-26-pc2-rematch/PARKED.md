# PARKED — P-C2

Defects and questions this tranche FOUND and did not fix. Each carries a
ready-to-send prompt. Nothing here is a promise; it is a record of what was
seen and deliberately not done, so the next tranche starts from what is
known rather than re-finding it.

---

## F-A — REBUILD F1's discharge channel is not reachable as configuration

**Status: OPEN. P-C2 works around it; it does not close it.**

**What was seen.** Proven by compiling a manifest, not by reading code:

    source config DISCHARGE_POLICY = discharge-required.v1
    engine_config_json has DISCHARGE_POLICY: False
    RUNTIME config DISCHARGE_POLICY = off

`run_manifest.py` pops `DISCHARGE_POLICY` from the manifest's config echo —
deliberately, and the reason recorded there is sound: the field postdates
every schema version's frozen wire-byte goldens, and echoing it would move
every qualification subject digest. But the one run path
(`application/text_runs.py::start_manifest_run`, the operations-parity law's
single entry) rebuilds Config with `config_from_run_manifest`, so the field
falls back to its CODE DEFAULT whatever any YAML says. `Config` is a plain
`BaseModel` with no environment source, so there is no env road either.

**Why this is a defect and not a limitation.** The modularity law (operator,
2026-08-26) says every behaviour a run can vary is reachable as
CONFIGURATION or a REGISTERED VERSIONED ARTIFACT, never by editing code.
F1's DELIVERY.md R13 claims exactly that for this toggle — "toggle and cap
both pure configuration" — and its architecture test proves the POLICY
RESOLVER is configuration-driven, which is true and is not the same claim.
Nothing tested the toggle END TO END, from a YAML file to a running
scheduler. That gap is the defect.

**What P-C2 did instead.** Deviation D1: changed the code default. That
turns the channel ON for every run and OFF for none — the opposite half of
the same problem. A run that wants the channel OFF now cannot express that
through a manifest either.

**Ready-to-send prompt:**

    Defect: REBUILD F1's discharge channel cannot be selected by any run's
    configuration. `run_manifest.py` pops DISCHARGE_POLICY from the config
    echo (correctly — echoing it would move every qualification subject
    digest), and `config_from_run_manifest` therefore rebuilds Config with
    the CODE DEFAULT, so the field a YAML sets never reaches the scheduler.
    Config is a plain BaseModel, so there is no environment road. Evidence:
    experiments/2026-08-26-pc2-rematch/PREREG.md §3 FINDING F-A and
    preflight_pc2.json's S3 check, which reads the reconstructed runtime
    Config exactly as the run path does.

    Route: dr-change-orchestrator. The design question is where a
    GENERATION-side policy selection lives when the manifest cannot carry it
    without moving a digest — a second, digest-excluded policy channel
    alongside engine_config_json is one road; widening the echo behind a
    schema bump is another. Whatever the answer, the acceptance check is an
    END-TO-END one: a YAML that names a policy, through the real
    `start_manifest_run`, reaching a scheduler that resolves that policy —
    the test F1's R13 is missing.

    Do NOT simply revert P-C2's deviation D1 without providing the road; the
    channel would go dark again and F1 would ship unusable a second time.

---

## F-B — FIXED IN THIS TRANCHE, recorded because the class recurs

**Status: FIXED. Kept here because the FAILURE CLASS is the tranche's own
subject and this is the second member of it found in two days.**

**What was seen.** With the channel on, `test_chaos_invariants.py::
test_disagreeing_ensemble_and_weak_defender` failed with

    meter says 7674 tokens, log accounts for 6674 (delta 1000)

F1's discharge re-ask (`rules/conj.py`, `screen_submission` → `reask`)
returns from `conj` EARLY — before both sites that persist `llm_call`, the
registration event and the `conj-noregister` fallback. The re-asked call's
tokens were metered and never logged, which `verify_root`'s accounting check
reports as a violation.

**Why it mattered here specifically.** Every ratio in this tranche has ARM
H2's logged token total as its denominator, and PREREG §5's matched-budget
rule sets ARM S2's budget from it. An under-logged `T_H` would have given
ARM S2 a smaller budget than ARM H2 actually spent — flattering the harness,
which is the wrong direction to err in — and `verify_root` would have
reported a violation on the P-C2 root.

**The fix.** One keyword argument: the `discharge-reask` Measure carries the
call, conditional on `source_call_seq is None` (the v6 and v4/work-order
paths have already logged it and a second record would double-count).
Proven by the failing test going green with no assertion weakened.

---

## P1 — F1's own parked four-arm A/B is not superseded

PREREG §9 states this as an honesty line and RESULTS.md repeats it. P-C2 has
two arms and its ARM H2 moves three organs at once plus a deviation, so no
P-C2 outcome attributes itself to any single organ. F1's PARKED.md P2 — the
four-arm A/B (no-critique / vacuous-critique / real-as-advice /
real-in-context) — remains the proof neither F1 nor P-C2 substitutes for.

---

## P2 — P-C1's residue items are inherited, not addressed

Named so nobody re-finds them:

- P-C1 P2: `deepreason results`' token counter read 0 after 292 provider
  calls. P-C2 does not use it; every token figure comes from W6's committed
  flow scan over the log. The counter is still wrong.
- P-C1 residue 4: qualification on this configuration is intermittently red,
  always at the same contract (five batteries ran fail/void/pass/fail/pass).
  P-C2 uses the same shape and inherits the same intermittency.
- P-C1 residue 6: survivor counts were unusable (`NO_SURVIVOR_RECORD` after
  a failed run). Whether P-C2 produces a survivor record is unknown until it
  terminates.
