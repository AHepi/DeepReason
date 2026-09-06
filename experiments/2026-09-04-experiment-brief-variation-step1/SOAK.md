# SOAK — R20's green gate, one soak per arm, before any provider call

`CLAUDE.md`, Live runs: *"No live launch without a green soak on the launch
config."* R20 repeats it. This document is that gate's output.

## Which case, and why it is the right one

`scripts/cycle_soak.py --case reach-rich`. The nine committed cases are
manifest shapes; `reach-rich` is the one closest to what these arms compile — a
SOLO model across the canonical roles with attached evidence disabled, which is
what `deepreason reason` produces here. The soak drives
`TextRunApplicationService` (the one run path) for 8 cycles against the
deterministic stub, so what it gates is the thing these arms actually change:
whether an arm's LAYOUT survives a deep managed run.

**One soak per arm, not one soak.** A layout that resolves at cycle 0 can still
refuse at cycle 6, when the section it names first has content to render.

## Results — all five green

| arm | exit | cycles | assertions |
|---|---|---|---|
| `A0` | **0 (clean)** | 8 of 8 | 8 PASS, 0 FAIL |
| `A1` | **0 (clean)** | 8 of 8 | 8 PASS, 0 FAIL |
| `A1P` | **0 (clean)** | 8 of 8 | 8 PASS, 0 FAIL |
| `A2` | **0 (clean)** | 8 of 8 | 8 PASS, 0 FAIL |
| `A3` | **0 (clean)** | 8 of 8 | 8 PASS, 0 FAIL |

A3's own assertions, verbatim from `soak/A3.log`:

    [PASS] A1-typed-terminal        state='completed' stop_reason='budget_exhausted'
    [PASS] A2-no-operational-failure stop_reason='budget_exhausted'
    [PASS] A3-verify-root-clean      0 violation(s)
    [PASS] A4-cycles-reached         reached cycle 8 of 8 requested
    [PASS] A7-record-fully-read      0 record(s) … could not be parsed
    [PASS] D2-route-lease            lease-checked routes with tuning
    [PASS] D3-budget-auth            budget authorization
    [PASS] D4-reservation-bound      reservation/dispatch bounds

## The guard fired before it was needed, which is the point

A3's first two attempts exited 1, and neither was a bug in the arm:

1. The command that WRITES the template was itself an arm process, so the rig
   demanded the template that command had not yet created. Fixed by running
   the bootstrap with `env -u DR_ARM`: the process that creates what an arm
   needs is not itself an arm.
2. The soak OWNS `DEEPREASON_HOME` — it points it at `<workdir>/home` and
   overrides the caller's — and `sitecustomize` runs at interpreter START,
   before the soak's `main()` sets it. So the template was written where the
   arm looked and the soak looked somewhere else. Fixed with `--out` plus an
   exported home, so both agree before the interpreter starts.

Both failures were LOUD, at cost zero, exactly as designed: *"An A3 that
silently fell back to the shipped neighbourhood would be A0 wearing A3's
label."* An arm that had failed this way quietly would have cost a full
battery and four cycles and reported the control's numbers under the
treatment's name.

## What the soak proved that the offline diff could not

`prove_arms.py` shows the arms differ on committed golden fixtures. The soak's
own record shows an arm differing IN A RUN. `verify_arms.py` over A3's kept
root (`SOAK_A3_RECEIPTS.txt`):

    op.neighbourhood.v1      rendered        n=  63  bytes=  40670   dropped=0
    dr.neighbourhood         never rendered  n=   0  bytes=      0   dropped=0
    dr.history.v1            never rendered  n=   0  bytes=      0   dropped=63
    dr.active-properties     never rendered  n=   0  bytes=      0   dropped=63

Three things follow, and none is a claim about prose:

1. **The operator's `.tmpl` really reaches the seats.** 63 conjecturer
   dispatches, 40,670 bytes of brief written by a text file the operator
   authored — through the loader that no shipped code path calls (`PARKED.md`
   F1). The arm is real.
2. **`dr.neighbourhood` is gone, not merely quiet** — 0 rendered AND 0
   dropped, because A3 removed it from the layout rather than silencing it.
3. **`dr.history.v1` and `dr.active-properties` never render** — 63 dispatches,
   zero bytes each. That is `PREREG.md` §3.1 and §3.2 confirmed from a run's
   own typed record rather than from reading source: the shipped default shows
   no history, and the active-properties section has nothing to widen.

## Reproducing

    python -u scripts/cycle_soak.py --case reach-rich          # A0
    DR_ARM=A1 PYTHONPATH=<tranche>/rig python -u scripts/cycle_soak.py --case reach-rich
    ./soak_arms.sh                                             # A1, A1P, A2, A3
    python verify_arms.py /tmp/soak-a3/run                     # the receipts
