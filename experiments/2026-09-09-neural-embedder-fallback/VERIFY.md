# Verification

## Criterion command + output

GOAL.md's success criterion had three parts. All three, verbatim:

    (1) python -m pytest tests/test_embedder.py tests/test_results_command.py -q
        47 passed in 52.23s

The new tests are mutation-proven. Reverting the emission in
`ops.make_embedder` fails three of them; reverting the reader's quotation of
the recorded cause fails a fourth; restored, 22 of 22 pass in
`tests/test_embedder.py`. Recorded in GATE.md with the counts.

    (2) python -u experiments/2026-09-09-neural-embedder-fallback/repro_embedder_drop.py
        pre-fix : exit 0, VERDICT: defect PRESENT   (REPRO_OUTPUT.txt)
        post-fix: exit 1, VERDICT: defect ABSENT    (REPRO_OUTPUT_POSTFIX.txt)

    (3) python -m pytest tests/ -q -n 4
        5178 passed, 6 skipped in 1362.84s   # the fix
        5178 passed, 6 skipped in 1354.94s   # after the E87 correction below

0 failed both times.

## Above the criterion: a real run root, offline, with a control

The goal asks that a RUN say why. A unit test proves the record is written; it
does not prove the run writes it. So the tranche drove the offline cycle soak
(`scripts/cycle_soak.py`, case `pc1`, the deterministic stub, no provider and
no live call) twice, over configurations differing in exactly one value —
the engine config's `EMBEDDER_MODEL`. Driver:
`verify_root_level.py`; full output in `VERIFY_ROOT_LEVEL.txt`.

    == treatment ==  (the arms' condition: no embedder model)
      engine_config.EMBEDDER_MODEL  : None
      log seq 6  : embedder-unconfigured
            nomic-ai/nomic-embed-text-v1.5
            no embedder model in the compiled run configuration, though a
            default one names this model: it was dropped before the manifest
            (run-manifest.json engine_config.EMBEDDER_MODEL)
      log seq 12 : embedder
            hashing-128 / 1 / 4226e035204776db
      deepreason results : hashing (hashing-128) — <the recorded cause>
      verify_root violations : 0

    == control ==  (the same case, its model kept)
      engine_config.EMBEDDER_MODEL  : 'nomic-ai/nomic-embed-text-v1.5'
      log seq 11 : embedder
            nomic-ai/nomic-embed-text-v1.5
            fastembed-0.8.0+onnxruntime-1.29.0
            d6e3599ce0377000
      deepreason results : neural (nomic-ai/nomic-embed-text-v1.5)
      verify_root violations : 0

Two things this pair establishes that no unit test could. The treatment's
hashing sentinel `4226e035204776db` is the same one all five brief-variation
arms carry, so the treatment is the arms' condition and not a lookalike. And
the control's fingerprint `d6e3599ce0377000` is exactly what this session's own
`deepreason embedder-warmup` printed at setup — so the neural backend does
build and stamp correctly in this container, which retires the last version of
the cache hypothesis. A run that gets its embedder records nothing extra.

Both soak runs report `A4-cycles-reached` failed: "reached cycle 2 of 2
requested". That is `--cycles 2` against an instrument that wants cycle 8, not
a finding. Every other check is green in both, including `A3-verify-root-clean`
at 0 violations.

## Historical roots re-checked

The fix changed a reader (`embedder_summary`, `embedder_line`), so the five
committed arm roots were re-read under it:

    A0  -> hashing (hashing-128)    (before: hashing (hashing-128))
    A1  -> hashing (hashing-128)    (unchanged)
    A1P -> hashing (hashing-128)    (unchanged)
    A2  -> hashing (hashing-128)    (unchanged)
    A3  -> hashing (hashing-128)    (unchanged)

Byte-identical. The reader change is additive: a root carrying no
`embedder-unconfigured` record reads exactly as it did. Nothing was written to
any committed root.

## Live attempt

None, and none was needed. The goal's proof is a run that records its
geometry decision, and the stub-driven soak produces a real root with a real
log and a clean `verify_root` at zero provider cost. Spending a live provider
run to re-observe a record the offline root already carries would have bought
nothing the record does not already hold.

## Verdict: PASS

The record now answers "why is this run's geometry hashing?" in every case.
Three typed records, one per cause: the `embedder` stamp when a neural backend
built, `embedder-fallback` when one was asked for and could not be built, and
`embedder-unconfigured` when nothing asked. `deepreason results` quotes the
recorded text rather than composing its own.

## One correction this verification produced

Verification found an error in what the implementation phase shipped, and it
was corrected before the tranche closed rather than reported as residue.

The cause `make_embedder` recorded told a reader to check
`run-manifest.json scratch_policy.embedder_model`. The two soak roots above
show that field is `null` in the NEURAL root and the hashing root alike —
along with `embedder_backend = "disabled"` and
`fallback_embedder = "deterministic_hashing"`, identical in both. The field
`config_from_run_manifest` actually reads back is the manifest's
`engine_config_json` echo. A pointer that is null in working and broken runs
alike sends half its readers to the opposite of the truth, which is worse than
no pointer at all.

Corrected: the cause names `run-manifest.json engine_config.EMBEDDER_MODEL`
(see the errata line below for the exact text as shipped), a regression test
pins that it does, and `docs/map/SUB-llm.md`'s Traps entry states the
distinction with the two-root evidence. DIAGNOSIS.md's own wording is NOT
edited — it records what that phase concluded on the evidence it had.

## Residue (honest)

1. **The managed path still cannot USE a configured embedder.** This tranche
   makes the decision visible; it does not change it.
   `preparation._config_for_profile` owns `EMBEDDER_MODEL` and forces it to
   None on every `deepreason reason`. So `deepreason embedder-warmup`, which
   CLAUDE.md tells every session to run at setup, still buys a managed run
   nothing: the weights are fetched and never consulted. That is a design
   decision with a stated reason in the code, and it is the operator's to
   revisit. PARKED.md P3 prices three roads.
2. **The five sealed arm roots are unchanged and stay on the hashing scale.**
   Their M2 and novelty readings are what they were. PARKED.md P2.
3. **The other six host-owned values were not examined.** Whether any of them
   also drops an operator value silently is a separate question. PARKED.md P1.
4. **docs_verify has nine failures this tranche did not cause and did not
   investigate.** `docs/AUDIT_BASELINES.md` records 5 or 6 on this container's
   shallow clone as of 2026-08-31, so roughly four post-date that baseline. All
   nine are in documents this tranche does not touch; the new `SUB-llm.md`
   check is in neither the failure list nor the `--audit` finding. Reported,
   not absorbed — re-baselining belongs to the audit family.
5. **Not proven: that a LIVE managed run behaves as the stub-driven one does.**
   The soak drives the same run path against a deterministic stub, and the
   record it produces is a real record; a live provider would change what the
   seats say, not how the embedder is chosen. The claim is bounded to that.

## Errata

`docs/ERRATA.md` E87 — the field a run-manifest carries its embedder in is
`engine_config`, not `scratch_policy.embedder_model`. Committed in the same
commit as the correction. Recorded cause as shipped:
"no embedder model in the compiled run configuration, though a default one
names this model: it was dropped before the manifest (run-manifest.json
engine_config.EMBEDDER_MODEL)".
