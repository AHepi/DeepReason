# REPRO — both defects demonstrated offline, on this tree, from main

Tranche: `experiments/2026-08-27-defect-split-leg-recording/`
Phase: dr-reproduce. Base `ba4720a95`, no production code changed.

## The instrument

`scripts/cycle_soak.py --case split-legs` drives the managed run path
against the deterministic stub. Its config,
`experiments/2026-08-27-defect-split-leg-recording/run-config.yaml`, is
the committed P-C1 ARM H config with **exactly one line deleted** —
`reasoning: "none"` — and its builder is P-C1's own
`build_manifest_pc1`, imported rather than copied. One deleted line is
the whole instrument, deliberately: anything else that differed would
make a green soak ambiguous about which change bought it.

That one line is the entire wiring. `reasoning_disabled` treats UNSET
as NOT OFF, and `llm/split.py`'s `auto` mode (the `Config` default)
splits exactly the seats whose route says they think.

## Result 1 — the record is replay-invalid (defect A)

    python -u scripts/cycle_soak.py --case split-legs      → exit 1

    [PASS] A1-typed-terminal      state='completed' stop_reason='converged'
    [PASS] A2-no-operational-failure
    [FAIL] A3-verify-root-clean   260 violation(s)
    [PASS] A4-cycles-reached      reached cycle 13 of 24

The run CONVERGED and still cannot be replayed. That is the finding in
its sharpest form: nothing about the reasoning went wrong; only the
record of it did.

The first violation is **byte-identical** to the one the P-C2b soak
recorded on a different branch, from a differently-authored case:

    attempt-accounting  event seq=27: trace tokens=15573 but call tokens=10001

## Result 2 — the crash, placed by experiment (defect B)

DIAGNOSIS.md §B predicted that the `LLMAttempt.prompt_ref=None` crash
needs a stand-down at dispatch, and that pc2b hit it because its
PREREG budget (200 000) leaves the meter no headroom to book the
emission leg. Predicted before it was run, then run:

    python -u scripts/cycle_soak.py --case split-legs --token-budget 200000
                                                          → exit 1

    [FAIL] A2-no-operational-failure  message='1 validation error for
        LLMAttempt\nprompt_ref\n  Input should be a valid string
        [type=string_type, input_value=None, input_type=NoneType]'
    [FAIL] A4-cycles-reached          reached cycle 2 of 24

Byte-identical to the pc2b soak's A2 message, and dead at the same
cycle depth (2). The only variable moved was the token budget, which
is what selects the `NOTICE_NO_HEADROOM` stand-down at
`adapter.py:1046` — the return whose sixth element is `None` and whose
`None` reaches `prompt_ref` at `adapter.py:1581`.

`verify_root` over that root, re-derived directly rather than read off
the soak's summary line:

    TOTAL 55
       11  attempt-accounting
       11  attempt-blobs
       11  attempt-order
       22  repair-metadata

The same four checks the BLOCKER named, in the same 1:1:1:2
proportions it recorded (10/10/10/20 = 50 there, 11/11/11/22 = 55
here). The ratio is structural: `repair-metadata` fires twice per
split call — once for the missing `DIAGNOSTIC:` and once for the
missing `complete corrected JSON value` — and the other three fire
once each.

## What this establishes

1. The defect is on `main`, not on the P-C2b branch. It has nothing to
   do with that tranche's experimental design; that tranche was merely
   the first thing ever to turn thinking on.
2. Two independent instruments, authored separately, produce the same
   violation bytes. The diagnosis is confirmed, not merely repeated.
3. Defect B is a distinct failure on a distinct path — an armed plan
   that stands down at dispatch — and is now reproducible on demand by
   moving one CLI flag.
4. **A run can converge and still be inadmissible.** Result 1 is the
   whole reason this is worth fixing before P-C2b spends its budget.

## Baseline re-derived at this base (not assumed)

    python -m pytest tests/ -q -n 4
    4328 passed, 6 skipped in 964.63s          (0 failed)

The tranche instruction carried 4231 from an earlier reading; the
re-derived number at `ba4720a95` is 4328 passed / 6 skipped / 0 failed,
and that is the number this tranche is measured against.

## Raw output preserved

`soak-before.out`, `soak-before-200k.out` (both committed beside this
file).
