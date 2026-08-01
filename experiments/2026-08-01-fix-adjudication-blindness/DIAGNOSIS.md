# Diagnosis: verification calls the detector only to prove it does not raise, and throws the flags away

Primary cause: `invariants.py:4040-4048` invokes the capture detector purely as
a totality check —

    # 7. Detection stays a total function over a messy log.
    try:
        from deepreason.capture.detection import raw_flags
        ...
        raw_flags(h, HashingEmbedder(), Config())
    except Exception as e:
        fail("detection-total", repr(e))

The return value is discarded. `raw_flags` computes every §11.3 flag, including
`ritual`, and none of them reaches any finding. The verification report's
epistemic channel is fed only by `_EPISTEMIC_CHECKS`
(`verification/report.py:131-137`), which is exactly
`{"bridge-epistemic", "bridge-grounding", "grounding-review"}` — no detection
flag is a member. So no adjudication-ritual flag can appear in the epistemic
channel, at any threshold, for any run. `MIN_ATTACKS_FOR_RITUAL` is downstream
of a value nothing reads.

Evidence:

  - **No `capture`/`detection` object kind exists in ANY of the 42 roots under
    `experiments/`.** A full scan of every `objects/` directory returns 55
    kinds; the closest is `workflow-stop-metrics-observation` (12 roots), which
    is the stop controller, not the detector. The detector has never written a
    typed record in the project's history.
  - `run-b4d6dfda…/run-result.json` — `finding_counts.epistemic: 0` and
    `epistemic_checks_passed: true`, on a run with `len(state.att) == 0`,
    `len(state.carries) == 0`, `len(warrants) == 0` and 72 ACCEPTED artifacts.
  - The run's only four `Refl` events (seq 12-15) resolve through
    `harness.state.artifacts` to school-policy registrations
    (`{"school_policy": {"school": "school-0", "stance": "mechanist"}}` etc.),
    not detector output. Nothing else in 851 events is detector-shaped.
  - `workflow-stop-metrics-observation` (the one detector-adjacent record)
    carries `criticism_debt`, `status_churn`, `gate_orbit`, `frontier_delta` —
    stop-controller metrics. It carries no ritual, stagnation or lambda flag.

Implicated code:
  - `src/deepreason/invariants.py:4040-4048` — the discarding call.
  - `src/deepreason/verification/report.py:131-137` — `_EPISTEMIC_CHECKS`,
    which no detection flag can join.
  - `src/deepreason/capture/detection.py:318-326` — the ritual conditions
    (dependent sub-cause, below).

Dependent sub-cause, in scope because the success criterion cannot be met
without it: even once the flags are read, the ritual condition the spec writes
as "validity-attack rate ≈ 0" is implemented as

    adj["n_attacks"] >= config.MIN_ATTACKS_FOR_RITUAL
      and (adj["validity_attack_rate"] or 0.0) == 0.0

with `MIN_ATTACKS_FOR_RITUAL = 5` (`config.py:322`). At `n_attacks == 0` this is
False, and so is the sibling `refutations >= 5` clause. Two of the four
conditions are therefore unreachable precisely when blindness is TOTAL, so the
worse the run, the fewer conditions fire. `attack_target_entropy` is `None` with
no attacks, killing a third. Only `criticism_debt > 0.5` remains, and `ritual`
needs two. This is not a separate tranche: criterion (a) asks for a finding on a
zero-attack run, which requires both the flag to be readable AND able to fire.

Falsifiable prediction (for dr-reproduce):

    Build a harness with artifacts, zero attacks and zero warrants, then:
      (i)  raw_flags(h, HashingEmbedder(), Config())["ritual"] is False
      (ii) forcing ritual True (monkeypatched) leaves
           verify_root_report(root).epistemic EMPTY

    (ii) is the load-bearing half: it shows the threshold is not the barrier.
    If (ii) shows a finding appearing, this diagnosis is wrong and the cause is
    the threshold alone.

Ruled out: **"the detector never runs."** The corpus scan showing no detection
records suggested it, and it is false. `scheduler/scheduler.py:2421` calls
`detection.raw_flags(self.harness, self.embedder, self.config)` and `:2499`
calls `detection.adjudicator_metrics`; `harness.py:183` states "capture
detection runs EVERY cycle". The detector runs, feeds the response ladder
(attention only, per spec §11.4), and writes nothing durable. The absence of
records is a reporting fact, not an execution fact.

Correction to the prior investigation's framing
(`experiments/live_jolt_2026-07-31/INVESTIGATION.md`): it attributed the silence
to the detector being unable to fire — `MIN_ATTACKS_FOR_RITUAL=5`,
`ritual_conditions == [False, False, False, False]`. That measurement is
reproducible and the threshold problem is real, but it is not why the run
reported clean. Even a firing detector would have changed nothing observable,
because verification discards the result. Fixing only the threshold would have
left `epistemic_checks_passed: true` exactly as it is.
