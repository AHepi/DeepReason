# P-A2 pre-registration — P-A1 re-run on the corrected configuration

**Frozen before the first live provider call.** Everything below is written
in advance so that the run's outcome cannot be re-described after the fact.
Where a prediction is refuted, the refutation is recorded as the result; a
negative result is a result. "Accepted does not mean true."

Status of this document at freeze time: written after the offline gates
(§7) and BEFORE `qualify` or `reason` dispatched anything.

---

## §1 What this run is, and what it is not

P-A1 (branch `claude/live-reasoning-p-a1-bv65kl`,
`experiments/2026-09-01-live-all-modules-p-a1/`, READ-ONLY here, plus
`MONITOR_REVIEW.md` on main) ran every module the harness owns on a seed
question, and died at cycle 5 with `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`
on a glm-5.3 seat that had been dropping connections all run.

Since then main merged five changes:

| commit | what merged |
|---|---|
| `85bf02ee0` | an omitted criticism policy now DERIVES defended trials |
| `971860c42` | `continue`/`amend` gated on security-channel replay validation |
| `660cf7192` | model-profile registry: per-model `agent.md`, no hard-coded `none` |
| `5f34e4d00` | `hv` measurable on v6; the hv-floor refuting again (operator ruling) |
| `2d84a86cd` | unevaluated commitments no longer lower coverage |

**P-A2 asks exactly one question: with the SAME seed question and the SAME
seats, what does the record show now that P-A1's record could not?** Every
claim in the delivery is a before/after against P-A1's typed counts. Model
prose is not evidence on either side.

**What this run is NOT.** It is not a fix tranche: no source is edited, and
anything that would need a code edit is recorded as a FINDING and parked. It
is not a fair test of every merged commit either — `85bf02ee0` (the derived
policy) is deliberately NOT exercised, because this run passes its criticism
policy EXPLICITLY exactly as P-A1 did, and changing that would be a fifth
difference. What P-A2 measures is the merged set as it presents itself to a
run of P-A1's shape.

---

## §2 The seed question — identical, byte for byte

Not reworded, not reformatted, not re-indented. It is imported from
`question.py`, which was taken verbatim from P-A1's file, and its digest is
asserted by `build_manifest_pa2.py` before any provider call:

    QUESTION_SHA256 = 933313a5d9ca6dd86f3052aec6e1f05f395ad00586e08096bd40d1be733d7560

Verified equal to P-A1's frozen value at tranche start. The three scoring
criteria (`criteria.py`) are likewise P-A1's, unchanged:
`pa1-limit-verdict@v1`, `pa1-obstruction-structure@v1`,
`pa1-scaling-law@v1`.

Run identity is deterministic in question + config. Because the config moves
(§3), the run id differs from P-A1's by construction — this is a new run, not
a relaunch of a retired root, and no `RUN_ALREADY_STARTED` refusal is
expected or worked around.

---

## §3 The configuration deltas — four fields, each with its reason

The parsed-config diff against P-A1's `run-config.yaml` is **13 leaves**, and
every one belongs to a correction the tranche instruction names. Measured, not
asserted, by diffing the two parsed YAML documents:

| # | field | P-A1 | P-A2 | why |
|---|---|---|---|---|
| C1 | `reasoning` on all 6 glm-5.3 seats | *(omitted)* | `"low"` | Omitted is NOT off. Ollama's glm-5.3 page documents `low`/`high`/`max` **defaulting to `max`**, so P-A1 ran its reason legs at max effort. That is what pushed those calls past the ~300 s transport wall (`MONITOR_REVIEW.md` MR-A). P-S1 measured 8 trials per setting: `none` 0/8 clean content at a median 64 completion tokens, `low` 8/8 clean at a median 7. |
| C2 | `reasoning` value chosen | — | `"low"`, never `"none"` | `none` is not in this model's documented set; on this model it does not stop the thinking, it stops the SEPARATION, moving the trace into `message.content`. Gated explicitly in preflight across *every* seat, not only glm. |
| C3 | `SPLIT_BUDGET_SEAT_PROTOCOL` | *(unset → `auto`)* | `"off"` | Under `auto` an explicit `low` still ARMS the two-leg split. Its extraction leg is now profile-driven (`660cf7192`) and would send glm-5.3's `extraction_value: low` rather than the old hard-coded `none` — a real fix, deliberately not the thing measured here. The leg's **512-token budget** is a SECOND, UNFIXED defect: it cut the conjecturer schema in 10 of 13 cases on **deepseek**, where the `none` leak never applied at all. Off removes both legs and leaves one provider call per attempt, which is what makes P2's zero-token count comparable to P-A1's. |
| C4 | `max_tokens` on all 6 glm-5.3 seats | `49152` | `32768` | The P-C2b-**measured** ceiling (planner output B_r=32256 / B_a=512 at ceiling 32768, all three legs valid with a natural stop). 49152 was an extrapolation from it and P-A1's own config header said so. At max effort P-A1's glm calls crossed the transport wall; at `low` they should not, and **the transport fix has not merged**, so this run does not invite the wall by asking for a cap nothing has measured. |

Plus one non-YAML change, staged by the ladder before compile:

| # | change | why |
|---|---|---|
| C5 | `docs/model-profiles/*` copied into `$DEEPREASON_HOME/model-profiles/` | Nothing ships (`docs/model-profiles/README.md`: *"Home directory only, nothing ships"*), so a fresh container stamps a registry of **zero** profiles — the designed state, and useless here. Five profiles staged; **a zero-profile stamp is a STOP**, per the tranche instruction. |

**Two traps caught by probe before launch, both recorded because a reader
would not see them:**

1. **YAML 1.1 resolves a bare `off` to the boolean `False`**, and the field
   is `Literal["auto","on","off"]`. The value is QUOTED in the config, with
   the reason written at the line.
2. **`SPLIT_BUDGET_SEAT_PROTOCOL` is POPPED from the manifest's engine-config
   echo** (`run_manifest.py:2469`), so the YAML line proves nothing on its
   own. It reaches the run only through a CARRIAGE NOTICE, which the compile
   emits verbatim: `SPLIT_BUDGET_SEAT_PROTOCOL='off' is not carried by this
   manifest's engine config and is restored at run time from this notice`.
   `preflight_pa2.py` asserts the value on the **rebuilt runtime Config**,
   not on the YAML.

### AMENDMENT 1 — 2026-09-02, after epoch 1 refused qualification

**Frozen before epoch 2's first live call; epoch 1's own text above is
unchanged.** A pre-registration that is quietly edited after a failure is
worth nothing, so this is recorded as an amendment with its cause, its
evidence and its cost.

**What happened.** Epoch 1 (manifest `e958a37b`, root retired as
`unqualified-epoch1-run-e958a37b`) never reached a reasoning cycle. The
ladder stopped at the qualification gate after 96 minutes: **22 of 23 pairs
qualified**, and the single failure was
`grounding_reviewer / groundingrepairwirev1.direct.v1 / glm-5.3` at **5 of
20** against a threshold of 19, where P-A1 scored 20 of 20. Every other pair
was 20/20 in both runs.

**What the isolation measured** (`isolate_grounding_repair.py`, 6 cells ×
10 cases = 60 live calls on that one pair, through the doctor's own per-case
entry point):

| reasoning | cap | split | valid |
|---|---|---|---|
| `low` | 32768 | off | 2/10 |
| `low` | 32768 | auto | 3/10 |
| `low` | 49152 | off | 4/10 |
| unset (`max`) | 49152 | auto | 10/10 |
| unset (`max`) | 49152 | off | 10/10 |
| unset (`max`) | 32768 | off | 10/10 |

Perfect separation on the reasoning knob; the cap and the split protocol vary
freely within each group and change nothing. **C3 and C4 are exonerated for
this contract; C1 is the sole cause.**

**The amendment (operator ruling, 2026-09-02).** C1 now reads: *the five
GENERATION glm-5.3 seats carry `reasoning: "low"`; the `grounding_reviewer`
seat runs at the model's default effort.* C2, C3, C4 and C5 are unchanged,
and the cap stays 32768 on all six seats because the measurement says the cap
is irrelevant here and moving it would be an unmeasured second difference.

**What this costs the comparison, stated plainly.** The correction is no
longer uniform across glm-5.3 seats, so P-A2 no longer tests "glm-5.3 at
`low`" as a single proposition. It tests the narrower and now better-evidenced
one: **`low` on the seats that generate, default effort on the seat whose
contract `low` cannot satisfy.** P2's transport prediction is unaffected in
substance — the ~300 s wall was measured on the conjecturer and defender
seats, both of which keep `low` — but it gains one seat that may legitimately
run long, and the delivery must not count a slow `grounding_reviewer` call as
a refutation of C1 on the generation seats.

**A new prediction, registered now rather than claimed later.**

> **P6 — the exception qualifies.** Epoch 2's qualification reaches
> **23 of 23 pairs**, and `groundingrepairwirev1.direct.v1` on glm-5.3
> returns to ≥19 of 20.
>
> Refuted if any pair fails. If the grounding-repair pair fails again at
> default effort, the isolation was wrong and the cause is not the reasoning
> knob — that would be a finding against F4 and a STOP, not a third attempt.

**Cost of the amendment:** the route change mints a new qualification subject
digest, so the full ~96-minute battery re-runs; nothing is cached from
epoch 1. Epoch 1's own artifacts are preserved unedited.

---

### What is held CONSTANT from P-A1 (and gated, so it cannot drift)

Seats (deepseek-v4-pro:0813 + glm-5.3 on all generation seats, deepseek
critic, glm-5.3 defender, qwen3.5:397b judge:0, gpt-oss:120b judge:1);
deepseek's `max_tokens` 49152 and both judges' 32768, all with `reasoning`
unset; `timeout_s` 1800/1200; the EXPLICIT `defended_trial` criticism policy
with 4 school bindings; `JUDGE_SUMMONS_PER_CYCLE` 2 / cooldown 4;
`ADVISORY_TRIALS_PER_CYCLE` 1; `ARGUMENTATIVE_AUTHORITY` observe_only;
simulation 12/12 with **every containment bound unchanged**; research
`web.contained.v1`; the grounded two-stage bridge with the composition call
at terminal; `NEAR_DUP_EPS` 0.2608 and `RESEED_DIST_MIN` 0.0401 on embedder
fingerprint `d6e3599ce0377000` (re-verified warm at tranche start); scratchpad
on; config referee at cadence 6; **successor minting OFF**; 24 cycles;
3 000 000 token budget.

---

## §4 The five predictions

Each is falsifiable against a **typed count**, with P-A1's own number beside
it. None is scored on prose.

### P1 — the criticism circuit convenes defended trials, and files nothing as `scrutiny`

> **Predict:** zero criticisms recorded as `scrutiny`, AND at least one
> defended trial CONVENED (a trial that reaches the defender or the judges,
> not a preflight decline).

- **P-A1 baseline:** 0 `scrutiny` (already closed by the explicit policy);
  6 `trial-declined` of which only **2 reached judges** (both split: qwen
  `pass`/gpt-oss `fail`, then the reverse — each judge convicted once, the
  unanimity rule zeroed both), **4 were `execution-backed` formal-supremacy
  preflight declines** where no seat was called at all, and **2 further
  targets died on defender transport** with no typed trial outcome.
- **Measured by:** `grep -c scrutiny log.jsonl`; `trial-declined` events by
  reason; `judgeruling.direct.v1` call count; `defender.direct.v1` call count.
- **Refuted if:** any `scrutiny` appears, or zero trials reach a seat.
- **Honest note:** P-A1's 2 defender-transport deaths were a glm-5.3 fault,
  so C1/C4 bear directly on this. A trial count that RISES is the expected
  direction; a count that rises is not by itself evidence the judges are
  discriminating — n is far too small, and `docs/RESEARCH_JUDGE_BLINDING`
  already measures 11.9% sensitivity in this frozen configuration.

### P2 — the transport faults are gone

> **Predict:** zero zero-token provider calls, and no `RemoteDisconnected`
> on any seat.

- **P-A1 baseline (re-derived by `monitor_pa2.py` against P-A1's committed
  record, and agreeing with `MONITOR_REVIEW.md` MR-A):** **10 zero-token
  attempts of 71**; **40 transport diagnostics** (39 `RemoteDisconnected` +
  1 `HTTPError`), **all on glm-5.3, zero on every other model**; typed as
  **10 `workflow-provider-attempt-v1` `transport_failure`** (6 conjecturer
  seat 1, 4 defender seat 0) plus **4 `criticism-attempt-v1`
  `transport_failure`**; 66% of a 4.94 h wall clock.
- **Measured by:** `monitor_pa2.py` — provider/criticism attempt objects by
  `outcome`, and `attempt_trace` rows by `tokens == 0` / `usage_unknown` /
  `transport_diagnostics`.
- **Refuted if:** any zero-token attempt or any transport diagnostic appears.
- **This is the prediction most likely to be REFUTED, and it is registered
  anyway.** The ~300 s transport wall is a KNOWN-OPEN defect with its own
  window; C1/C4 are a MITIGATION (keep the calls far inside the wall), not a
  fix. If diagnostics appear at `low` and a 32768 cap, that is a real and
  useful result: it would show the wall is not effort-dependent, which is the
  opposite of the current hypothesis.

### P3 — `hv` becomes measurable

> **Predict:** at least one `hv_set` event AND at least one hv-floor verdict
> (pass or fail) on a connection-problem artifact.

- **P-A1 baseline:** **0 `hv_set`**, **0 hv-floor verdicts**, **19 variator
  deferrals** (`hv-floor` 8, `hv-spot-check` 10,
  `premise-demarcation-variation` 1). Independently confirmed on the P-R1
  root: 117 variator deferrals, zero `hv_set`.
- **Why it could now hold:** `5f34e4d00` makes the v6 deferral gate consult
  the SEAT'S GRANT rather than `schema_version`, and this manifest's
  `variator[0]` holds `variator.direct.v1` (asserted in preflight, and the
  reason the `hv-grant` soak case is run as well).
- **Measured by:** `state_diff.hv_set` event count; hv-floor verdicts in the
  variator's typed records; `v6-model-phase-deferred.v1` signal count.
- **Refuted if:** zero `hv_set` events, or deferrals continue at P-A1's rate.
- **Residue registered in advance:** capability-channel use is STOCHASTIC
  across identical runs. One live run that misses this path is INCONCLUSIVE
  for that path, not a refutation of the merged fix; the offline `hv-grant`
  soak remains the proof that the granted path is reachable at all.

### P4 — a seed-answering artifact reaches the Pareto frontier

> **Predict:** the ARTIFACT Pareto frontier contains at least one
> seed-answering artifact.

- **Computed with `rescore.py` from
  `experiments/2026-09-02-defect-coverage-pending-commitments/`, NOT the
  `frontier` CLI** — the CLI prints the PROBLEM registry (14 rows on P-A1),
  which is a different object and would answer a different question.
- **P-A1 baseline, re-derived at tranche start:** artifacts 33, survivors 11.
  Frontier under the formula P-A1 actually ran: **7 of 11, all `connection`,
  ZERO seed-answering**; the 4 seed artifacts were dominated, each carrying
  2–3 `OVERRUN` commitments that lowered coverage to 0.57–0.67.
- **Why it could now hold:** `2d84a86cd` leaves an unevaluated commitment out
  of the coverage denominator. Re-scored under it, P-A1's own root gives
  **11 of 11 on the frontier, all four seed artifacts moved on**, each at
  coverage 1.0000. The OVERRUN census names one reason for all 10:
  `observation requires registered evidence`.
- **Measured by:** `rescore.py <root>` on P-A2's root, reported as the same
  before/after table.
- **Refuted if:** the frontier contains no seed-answering artifact.
- **Honest note:** the P-A1 re-score above is a RETROSPECTIVE application of
  the fix to a committed root, which is weaker than it looks — it shows the
  formula moves those artifacts, not that a live run under the fix produces
  them. P-A2's contribution is a run whose OWN shipped `pareto_scores` does
  it live.

### P5 — the run reaches a typed terminal without a seat-capability death

> **Predict:** the run reaches a typed terminal WITHOUT
> `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`.

- **P-A1 baseline:** `state: failed`, `stop_reason: operational_failure`,
  `workflow-route-seat-insufficient-capability-v1` on seat 1 glm-5.3
  (`smallest_authorized_contract_schema_exhausted`) at cycle 5 of 24;
  deepseek seat 0 healthy throughout; `verify_root` **0 violations** —
  intact and unusable, refusing `AMEND` with
  `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`.
- **HONEST RISK, STATED IN ADVANCE:** **F4 is NOT fixed.** One seat's
  exhaustion still kills the whole run, and that terminal is still not
  resumable — a window is on it, and this run does not touch it. C1/C4
  address the transport streak that PRECEDED the exhaustion, not the
  exhaustion rule itself.
- **If it fires: record it as the second live instance and STOP. Do not
  relaunch.** A relaunch after a typed failure is one of this tranche's
  named STOP conditions.
- **Measured by:** `run-status.json` state + `stop_reason`; the presence of a
  `workflow-route-seat-insufficient-capability-v1` object; `verify_root`.
- **The monitor is armed for the precursor**, not only the death:
  `schema_exhausted` semantic admissions and a 2-consecutive-failure seat
  streak both alert (P-A1's record carries 2 of the former).

---

## §5 Known-open — measured, NOT fixed

Recorded here so that finding them again is a confirmation and not a
discovery, and so no reader mistakes an unfixed thing for a regression:

- **F4**, one seat's exhaustion kills the run and the terminal is not
  resumable (a window is on it).
- **The ~300 s transport wall and the blind identical retries** — four
  attempts, each spending the same ~300 s (a window is on it).
- **The nine legacy phases still deferred.**
- **The premise-channel decline rate** (P-A1: 0 CITED, 7 DECLINED).
- **The criticism→problem trigger rate** — `SUCCESSOR_MINTING_ENABLED` is
  OFF by the operator's own default, so this run can NEITHER confirm NOR
  refute it. Registered so the delivery does not claim otherwise.
- **The successor field routing to the scratchpad** (P-A1: no scratch payload
  on any event).
- **The split extraction leg's 512-token budget** — sidestepped by C3, not
  fixed, and still live for anyone running under `auto`.

---

## §6 What would make this run UNINTERPRETABLE

Written down in advance so it cannot be rationalised later:

- A zero-profile registry stamp (STOP — the C5 staging silently failed).
- `SPLIT_BUDGET_SEAT_PROTOCOL` reading `auto` at runtime (C3 did not happen;
  every glm seat is two legs and P2 is not comparable).
- Any glm-5.3 seat dispatching at a `reasoning` other than `low`.
- A run that dies before cycle 1, which measures the launch and not the
  configuration.

---

## §7 Launch gates — all offline, all before the first provider call

1. `preflight_pa2.py <root>` — **60 checks, 0 failures**, over the compiled
   manifest and the runtime Config rebuilt from it, including every P-A1 gate
   plus §3's corrections and the profile registry.
2. `python -u soak_pa2.py --case pa2` GREEN — the managed path driven on
   THIS configuration's own shape against the deterministic stub. The case is
   registered from this tranche's script against `cycle_soak`'s module-global
   `CASES`, so **no source file is edited**.
3. `python -u soak_pa2.py --case hv-grant` GREEN — confirms the grant shape
   P3 depends on.
4. `plant_monitor_fixture.py` — every alert fires on a planted fault AND the
   clean control stays SILENT; plus the monitor re-derives P-A1's real 40
   diagnostics / 10 zero-token calls, which P-A1's own monitor reported as
   `provider calls FAILED: none`.
5. The catalogue check (`--catalogue`): every seat names a model the provider
   actually lists.

A green soak is NOT full coverage: it reproduces one of the four 2026-08-22
operational deaths and asserts the other three
(`experiments/2026-08-23-change-cycle-soak-instrument/`).

---

## §8 Residue, stated before the fact

- The soak drives the deterministic stub, so it can prove a contract is
  DISPATCHABLE and cannot prove a live model fills it. Only the live run
  speaks to that.
- P-A2 measures the merged set **as a set**. Five commits landed together and
  a single run cannot attribute an improvement to one of them. Where a
  prediction holds, the delivery says which commit is the plausible cause and
  says that it is an attribution, not a measurement.
- n=1. P-A1 is a single run and so is P-A2; a difference between them is a
  difference between two runs, and capability-channel use is stochastic
  across identical configurations.
- This run measures the profile registry's EXISTENCE and its stamp, not its
  `extraction_value` in flight — C3 turns off the leg that would have used it.
