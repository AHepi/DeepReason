# Diagnosis: mechanism (b) — the controller is constructed and stepped, but every knob it could move is silently skipped, because the envelope table does not cover the roles or the cap magnitudes a compiled v6 manifest binds

Primary cause: `ops.run_scheduler` DOES build `Controller(harness, adapter)`
(ops.py:408-411) and `Scheduler` DOES call `self.controller.step()` once per
cycle (scheduler.py:1886-1887). The controller then proposes nothing, on
every cycle, through two independent silent `continue`s inside
`Controller._propose`, and the run's compiled manifest hits BOTH. First,
`if knob not in self.envelopes or role not in caps: continue`
(controller.py:259) drops any role with no `cap:<role>` entry in the
`ENVELOPES` table — the table names six roles
(`conjecturer, argumentative_critic, defender, variator, synthesizer,
judge`), and the grounded manifest binds eleven. Second,
`if not envelope["min"] <= cur <= envelope["max"]: continue`
(controller.py:270) holds any role whose CURRENT cap sits outside its
envelope — deliberate behaviour, added so a compiled route is not
"normalized" downward, and covered by
`tests/test_controller.py::test_controller_does_not_normalize_an_explicit_cap_outside_its_envelope`
(a 7,000-token website cap). But every role in a real compiled manifest
pins `max_tokens=16384`, and the LARGEST envelope max in the table is 5,000
(`cap:conjecturer`). So the deliberate hold, written for one unusual route,
now fires for 100% of roles on 100% of production runs. Net: 11 of 11
manifest-bound roles are unsteerable, `deltas` is always empty, `step()`
returns `None` at controller.py:367-368, and NOTHING is written to the
record — the controller is ON, has authority over zero knobs, and says so
nowhere. Silent inertness, the embedder-fallback failure shape.

Evidence:

  - `experiments/2026-08-12-live-grounded-extension-expansion/run/log.jsonl`
    (12,991 events, run `8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d`)
    -> substring counts `cap:`=0, `envelope`=0, `referee`=0, `steer`=0,
    `policy_eval`=0, `knob`=0. `knob`=0 is decisive for `_emit_policy`,
    whose artifact body always contains the literal key `"knobs"`
    (controller.py:408). Zero policy artifacts were emitted in 24+ cycles.

  - Same log, rule census: `Measure` 6,556 / `Control` 3,380 / `Spawn`
    2,894 / `Register` 85 / `Conj` 42 / `Crit` 16 / `Scratch` 14 / `Refl` 4.
    The 4 `Refl` events are at seq 3, 4, 5, 6 — school seeding, before any
    cycle ran; `_emit_policy` writes `Rule.REFL`, so had the controller
    fired even once there would be a fifth. The operator's trap is
    confirmed and re-derived: the 3,380 `Control` events are
    `control.event.v3` workflow transactions (2,702 `work_transition`,
    666 `provider_result`, 3 `contract_decomposition_activated`, 3
    `contract_decomposition_completed`, 2 `lifecycle_stopped`, 2
    `terminal_committed`, 1 `classification_bound`, 1 `lifecycle_resumed`)
    and are unrelated to steering.

  - Same root, `run-manifest.json` `roles` -> all 11 bound roles pin
    `max_tokens: 16384`. Cross-referenced against
    `deepreason.controller.ENVELOPES`:

        ROLE                     max_tokens   envelope       steerable?
        argumentative_critic         16384    [800,3500]     NO (out of range)
        conjecturer                  16384    [800,5000]     NO (out of range)
        defender                     16384    [500,2000]     NO (out of range)
        judge (2 endpoints)          16384    [600,2500]     NO (out of range)
        synthesizer                  16384    [600,2500]     NO (out of range)
        variator                     16384    [800,4000]     NO (out of range)
        grounding_reviewer           16384    -- none --     NO (no envelope)
        property_designer            16384    -- none --     NO (no envelope)
        summarizer                   16384    -- none --     NO (no envelope)
        thesis                       16384    -- none --     NO (no envelope)
        vision_critic                16384    -- none --     NO (no envelope)

  - Same log, process-signal census over the 666 `event.llm` records:
    `judge` 342, `argumentative_critic` 123, `defender` 122,
    `conjecturer` 49, `variator` 30 — and `truncated`=0, `attempts>1`=0
    for EVERY role. Five roles cleared `MIN_SAMPLES=2` with a
    `_clean_streak` far past `CLEAN_WINDOWS=3`, so `_propose`'s efficiency
    branch (controller.py:276-282) would have narrowed all five had the
    range guard not skipped them first. The controller had abundant valid
    signal and still moved nothing. `dropped-call` events = 0, so the
    `timeout:transport` knob correctly had no trigger.

Implicated code:
  - `src/deepreason/controller.py:259` — role with no envelope entry,
    silent `continue`
  - `src/deepreason/controller.py:270` — cap outside envelope, silent
    `continue`
  - `src/deepreason/controller.py:367` — `if not deltas: return None`,
    the exit that writes no record

Falsifiable prediction (what dr-reproduce must show):

    Build an offline harness + LLMAdapter whose endpoints mirror the
    grounded manifest — the same 11 role names, every one at
    max_tokens=16384 — append >= MIN_SAMPLES clean LLMCall events per
    role, then:

      (1) Controller(h, adapter).step() returns None on every cycle, and
          h.log gains no artifact whose body contains "knobs" and no
          controller-hold record.       [the defect]
      (2) With ONE endpoint re-pinned to 3000 (inside cap:conjecturer's
          [800,5000]) and the same clean signal, step() returns
          {"cap:conjecturer": 1875} and emits a Refl policy artifact.
                                        [proves the envelope bound, not
                                         the wiring, is the gate]

Ruled out — mechanism (a), "CONTROLLER did not survive the compiled-config
road": it survived. The committed `run-manifest.json` carries
`engine_config_json` with `"CONTROLLER": true`, and
`ops.run_scheduler` reads `config.CONTROLLER` at ops.py:408 to construct.
`tests/test_controller.py::test_run_scheduler_wires_controller_by_default`
already pins both directions of that construction. Attachment is not the
defect.

Ruled out — mechanism (c), "construction is conditional on something else
the manifest path does not provide": ops.py:407-411 has exactly one
condition, `config.CONTROLLER`, and no manifest-derived guard. Since
`experiments/2026-08-13-change-single-run-path-unification` there is one
run path, so no second door can skip the construction.

## Not a defect — recorded so it is not re-diagnosed

**Zero `config_referee` reviews is CORRECT for this root.** The referee is
default-OFF and operator-opted:
`v6_policy.py:411 engaged_config_referee_policy` returns `None` unless the
environment names `DEEPREASON_CONFIG_REFEREE` (a cadence in cycles). The
grounded ladder's `build_manifest.py:161` calls
`engaged_inquiry_capability_policy(...)` without setting it, so the
compiled manifest carries `inquiry_capability_policy.config_referee: null`,
and `Scheduler._maybe_config_referee` (scheduler.py:710-712) returns before
any call. The absence is RECORDED in the manifest, not silent, so it is
configuration rather than inertness. GOAL.md's success criterion (2) is
therefore satisfied by the typed nothing-to-steer record; no referee change
is needed and none is in scope.

## Second cause found — PARKED, not fixed

The scheduler-side debt-vs-spawn selection asymmetry is a real second
finding, independent of the controller. It is in `PARKED.md` (P1) with a
ready-to-send prompt. One tranche, one goal.

NUMBER CORRECTION while parking it: the tranche brief said "380
criticism-coverage-debt records". The committed log holds **5,026**
`criticism.coverage-debt.v1` records over **469** distinct subject digests
(`grep -o 'criticism.coverage-debt.v1' log.jsonl | wc -l` -> 5026). 380
matches neither count. The finding is real and larger than stated; the
parked prompt carries the measured figures.
