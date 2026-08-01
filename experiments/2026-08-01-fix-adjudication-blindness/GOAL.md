# Goal: a run that never attacked anything must not be reported epistemically clean

Class: defect

Observed: `run-b4d6dfda0c20676a864a051fbc97bda4` (jolt epoch 3, `completed`,
851 events, 72 artifacts) has `len(state.att) == 0`, `len(state.carries) == 0`
and `len(harness.warrants) == 0` — not one attack was ever attempted — and all
72 artifacts are ACCEPTED. Its `run-result.json` reports
`epistemic_checks_passed: true` with `finding_counts.epistemic: 0`.

This contradicts `docs/harness-spec-v1.3.md` §11.3, verbatim:

  - adjudicator surface: "**validity-node attack rate** (if no test is ever
    attacked, D3 has died in practice while remaining true on paper)"
  - "**Adjudication ritual** = any two of {attack-entropy < floor, criticism
    debt > ceiling, reinstatement outside band, validity-attack rate ≈ 0}
    sustained"

The spec names zero-attack as a death of D3 in practice and as one of the four
ritual conditions. The implementation reports such a run epistemically clean.

Measured blast radius, over every root under `experiments/` that today's
`Harness` can open (31 of 42; 11 raise `UnsupportedRunManifestVersionError`,
all pre-v6):

    5 roots DO have attacks and warrants — 25 warrants total:
        bronze_flat_2026-07-13/deepseek-v4-pro          att=11  warrants=11
        bronze_flat_2026-07-13/qwen3_5_397b             att= 8  warrants= 8
        bronze_flat_2026-07-13/kimi-k2_6                att= 4  warrants= 4
        live_compare_2026-07-28/.../shallow-dc6fe3f9    att= 1  warrants= 1
        live_engaged_2026-07-27/run-f4fa6663e5412d64    att= 1  warrants= 1
    26 roots have none, including the jolt root.

So the harness CAN attack; this is not universal blindness. Any detector that
fires here must NOT fire on those five.

(Correction of record: an earlier probe this session reported "31 of 31 roots
have zero attacks". That was wrong — it read `state.attacks`, which does not
exist, so `getattr(..., {})` returned empty everywhere. The attribute is
`state.att`. The jolt root's zero is real and was re-measured; the corpus claim
was not. Recorded here because the same probe shape produced the numbers the
operator was given earlier.)

A prior investigation (`experiments/live_jolt_2026-07-31/INVESTIGATION.md`)
points at `src/deepreason/capture/detection.py:319-327`,
`MIN_ATTACKS_FOR_RITUAL=5`, and a measured
`ritual_conditions == [False, False, False, False]`. That is a POINTER for
`dr-diagnose` to re-derive, not an established cause, and this goal does not
adopt it.

Success criterion (machine-decidable):

    (a) For the jolt root, the typed record must name the condition:
        python -c "from deepreason.verification.report import verify_root_report; ...
                   r=verify_root_report(<jolt root>); print(len(r.epistemic))"
        expected: >= 1, and the finding's detail names the zero-attack condition.

    (b) The five roots that DO have attacks must NOT gain that finding:
        same command over each
        expected: the zero-attack finding absent from all five.

    (c) No previously-valid root becomes invalid. A verdict sweep over all 31
        openable roots, captured before and after:
        expected: every root's `valid` field unchanged. If the new finding
        flips any root's validity, that is a frozen-surface violation
        (CLAUDE.md: "a change that invalidates existing replay-valid roots is
        wrong by definition") and the tranche STOPS for operator approval
        rather than proceeding.

    (d) pytest tests/ -q -n 4
        expected: 0 failed. No assertion weakened.

In scope:
  - `src/deepreason/capture/detection.py` (the ritual/blindness detector)
  - `src/deepreason/verification/report.py` (the epistemic channel that reports it)
  - `tests/` (one regression test naming this run)

NOT in scope: `src/deepreason/authority.py`. It is the nearest tempting
neighbour — `authority.py:97-101` hard-returns `OBSERVE_ONLY` for every text
workload, which is WHY there are no attacks, so "just let text runs mint
warrants" looks like the real fix. It is a design decision the operator has not
made, and changing what a run is permitted to do is a different tranche from
making the harness honest about what it did.

Also NOT in scope, parked: emitting a typed record at SEEDING time when the
registered commitment set contains nothing capable of returning FAIL
(capability-gap, own tranche); and the nine items already in
`experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md`.

Budget: <=150 changed lines, 1 commit, ~3 hours

Stop conditions inherited from orchestrator: yes
