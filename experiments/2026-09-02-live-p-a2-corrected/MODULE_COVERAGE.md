# P-A2 module coverage

**This table is the tranche's headline artifact.** One row per module the
harness owns. Each row carries the typed evidence that the module fired, or
the typed reason it did not. A module that did not fire is a RECORDED RESULT,
not a failure to hide.

P-A1's two columns, plus a third this tranche exists for:

- **CONFIGURED** — did the shipped configuration actually reach this module?
  Evidence: the compiled `run-manifest.json`, the runtime `Config`
  reconstructed from it by `config_from_run_manifest`, and the 61 gates in
  `preflight_pa2.py`. This column is complete before any provider call.
- **FIRED LIVE** — did the module actually do something in the run? Evidence:
  `log.jsonl` event ids, `state_diff` payloads, `llm.role` counts and the
  typed attempt objects, all read by `module_census.py` and
  `monitor_pa2.py`. Never model prose.
- **P-A1 → P-A2** — the before/after this tranche measures. P-A1's number is
  re-derived by running the SAME `module_census.py` against P-A1's committed
  root on the current checkout, so the two sides of every comparison come
  from one instrument and one code version rather than from P-A1's prose.

A module can be CONFIGURED and not FIRED — that is an ordinary outcome and one
of the things this run exists to measure. The reverse would be a defect.

---

## Status

| phase | state |
|---|---|
| design frozen (PREREG.md) | DONE — 2026-09-02, before the first live call |
| configuration compiled and preflighted | DONE — 61/61 gates, 0 failures |
| offline cycle soak on the launch shape (`--case pa2`) | DONE — GREEN, exit 0, 24/24 cycles, verify_root 0 violations |
| offline cycle soak on the grant shape (`--case hv-grant`) | DONE — GREEN, exit 0, 8/8 cycles |
| monitor alerts proved on planted faults + clean control | DONE — 6/6, control silent |
| live run | IN FLIGHT — launched 2026-09-02T17:44:43Z |
| live census | PENDING the terminal |

Manifest `e958a37b33bd3f3c2568289c6b2ea5eca0d129fc060f641939ee89beba3a0ffe`
— byte-identical to the pre-launch probe compile, which is run identity
behaving as designed (deterministic in question + config).

---

## Column 1 — CONFIGURED (complete, measured on the compiled manifest)

Every row was read off the compiled `run-manifest.json` or the runtime
`Config` rebuilt from it, before any provider call.

| module | configured | evidence |
|---|---|---|
| conjecture ensemble | YES | `roles.conjecturer` = 2 seats: `deepseek-v4-pro:0813`, `glm-5.3` |
| argumentative criticism | YES | `roles.argumentative_critic` = `deepseek-v4-pro:0813`; `criticism_policy` STORED with 4 school bindings |
| defended trial | YES | `criticism_policy.authority = "defended_trial"` (explicit compiler argument, not the omitted-policy derivation) |
| defender seat | YES | grant `defender.direct.v1` on `defender[0]` — non-empty |
| judge ensemble | YES | `judge[0]` qwen3.5:397b (`qwen`), `judge[1]` gpt-oss:120b (`openai-gpt`); grant `judgeruling.direct.v1` on both; ≥2 seats across ≥2 families |
| judge dispatch rate | YES | `JUDGE_SEATS_ENABLED=True`, `JUDGE_SUMMONS_PER_CYCLE=2`, cooldown 4 — restored through carriage notices |
| adjudication status authority | YES | `ADJUDICATION_STATUS_AUTHORITY_ENABLED=True`, restored through its carriage notice |
| advisory rubric trials | YES | `ADVISORY_TRIALS_PER_CYCLE=1` while `TEXT_RUBRIC_AUTHORITY` stays `observe_only` |
| variator / hv | YES | grant `variator.direct.v1` on `variator[0]` — non-empty. **And now reachable**: `hv-floor` and `hv-spot-check` both map to the variator role and this contract in `workflow/legacy_phase_contracts.py`, and the deferral gate reads that table instead of `schema_version` literals (5f34e4d00) |
| reach | YES | `PARETO_AXES = ["hv", "reach", "coverage"]`, unchanged from shipped |
| schools | YES | `school_execution.mode = "route_bound"`, 4 bindings round-robin across the two conjecturer seats (school-0/2 → deepseek, school-1/3 → glm-5.3) |
| scratchpad | YES | `scratch_policy.enabled = true`; runtime `Config.scratchpad.enabled = True` |
| successor-question routing | YES | `SUCCESSOR_QUESTION_DESTINATION = "scratchpad.v1"` (the P9 default) |
| successor MINTING | **DELIBERATELY OFF** | `SUCCESSOR_MINTING_ENABLED = False`. Its enablement is an operator launch-time choice carrying the operator's own warning text; this window did not make it |
| simulation capability | YES | `enabled`, toolchain `python@deepreason-public-contained.v1`; containment probed available before launch |
| simulation budget | YES (RAISED) | 12 requests / 12 executions, up from the preset's 2/2. **Every containment bound unchanged**: wall 20000 ms, `network_policy: forbidden`, `filesystem_policy: isolated_no_filesystem` |
| research capability | YES | `enabled`, allowlist `arxiv.org` + `en.wikipedia.org` |
| attached-evidence channel | YES (EMPTY DOSSIER) | `attached_evidence.enabled = true`, **0 sources bound**. The question is self-contained; fabricating sources to make a channel look busy would be the opposite of evidence |
| grounded bridge | YES | `bridge_policy.mode = "grounded_two_stage"`; runtime Config agrees |
| bridge grounding review | YES | `grounding_review = true`, `reviewer_role = "grounding_reviewer"` |
| bridge composition CALL | YES | the ladder calls `deepreason bridge build <problem> --target answer` at terminal |
| config referee | YES | `config_referee.cadence_cycles = 6` (four firings across 24 cycles). Ships OFF; armed through `POLICY_ENVIRON` pinned in the builder, not the shell |
| near-duplicate / anti-relapse gate | YES | `NEAR_DUP_EPS = 0.2608`, calibrated on the configured embedder over three committed live roots |
| school-convergence tripwire | YES | `RESEED_DIST_MIN = 0.0401` alongside the shipped `RESEED_RATIO_MAX = 0.3` |
| discharge channel | YES | `DISCHARGE_POLICY = discharge-required.v1` |
| **split-budget seat protocol** | **DELIBERATELY OFF (C3)** | `SPLIT_BUDGET_SEAT_PROTOCOL = "off"` on the REBUILT runtime Config — the only surface that answers the question, since the field is popped from the manifest's engine-config echo and arrives by carriage notice. P-A1 left it at `auto`, which armed the two-leg split on every glm seat |
| **glm-5.3 reasoning effort (C1/C2)** | **`low`, EXPLICITLY** | all six glm-5.3 seats. P-A1 omitted the field, and omitted is not off: this model defaults to `max` |
| **glm-5.3 completion cap (C4)** | **32768** | all six glm-5.3 seats, the P-C2b-measured ceiling. P-A1 used 49152, an extrapolation |
| **model-profile registry (C5)** | **5 PROFILES** | `count=5`, `problem_count=0`, staged into `$DEEPREASON_HOME/model-profiles` by the ladder before compile. Nothing ships, so an unstaged home stamps ZERO — which is a STOP for this tranche |
| allocation signals | YES | `open_loop_notices(bound_roles) → ()` — zero of the seven policy signals is open-loop on this topology |
| embedder | YES | `nomic-ai/nomic-embed-text-v1.5`, fingerprint `d6e3599ce0377000` (re-verified warm at tranche start — the same fingerprint the two thresholds were calibrated against); `EMBEDDER_FAILURE_POLICY = error` |

**Configured-column verdict: every module the tranche instruction names is
reachable by configuration, and the four corrections are present on the wire
and not merely in the file.** No modularity-law finding is filed. The one
instrument gap that did appear (FINDINGS.md F1) is in the offline soak's
stub, not in the harness, and does not touch what the live run can do.

---

## Column 2 / Column 3 — FIRED LIVE, and P-A1 → P-A2

**Epoch 3 ran.** Qualification passed 23/23 and the run reached a typed
terminal, so this column is real. It is also SHORT: the run died at **cycle 0
of 24** on a defect none of the predictions anticipated (FINDINGS.md F7), so
every "fewer" below means "one cycle instead of five", not "worse".

Run `1b89ed64e050c354…`, 2026-09-03, **cycle 0**, 212 152 / 3 000 000 tokens,
`state: failed`, `stop_reason: operational_failure`, message *"v6 conjecture
context must be planned after durable work preparation"*, **`verify_root`
violations: 0**.

| module | P-A1 | P-A2 | P-A1 → P-A2 |
|---|---|---|---|
| conjecture | FIRED: 7 Conj, 47 calls | **FIRED**: 2 Conj, 4 calls | fewer — died at cycle 0 |
| criticism | FIRED: 5 Crit, 12 calls | **FIRED**: 3 Crit, 4 calls | fewer — cycle 0 |
| defender seat | FIRED: 8 calls | **FIRED**: 7 calls | ≈ same, in 1 cycle not 5 |
| judge ensemble | FIRED: 4 calls | **FIRED**: 18 calls | **4 → 18** |
| defended trial | FIRED: 6 declined, 0 scrutiny | **FIRED**: 7 trials, **0 scrutiny** | holds, more trials |
| adjudication / status authority | FIRED: 25 status_changed | **FIRED**: 12 status_changed | fewer — cycle 0 |
| **variator / hv** | did-not-fire: 0 calls, **19 deferrals** | did-not-fire: **1 call, 0 deferrals** | **deferrals 19 → 0** |
| reach | did-not-fire | did-not-fire | unchanged |
| pairwise discrimination | did-not-fire | did-not-fire | unchanged |
| **scratchpad** | **did-not-fire** | **FIRED: 4 events** | **NEW — and it killed the run (F7)** |
| successor questions | did-not-fire (minting OFF) | did-not-fire (minting OFF) | unchanged, as designed |
| simulation capability | did-not-fire | did-not-fire | unchanged — cycle 0 |
| research capability | FIRED: research-awaiting-agent ×1 | did-not-fire | **lost — died before its period** |
| attached evidence | did-not-fire (empty dossier) | did-not-fire (empty dossier) | unchanged, by design |
| premise channel | FIRED: 7 DECLINED, 6 offers | **FIRED**: 7 DECLINED, 1 offer | same direction |
| discharge channel | FIRED: 6 reask, 19 undischarged | **FIRED**: 2 reask, 18 undischarged | ≈ same |
| near-duplicate gate | FIRED (armed at 0.2608) | **FIRED** (armed at 0.2608) | unchanged |
| school convergence | did-not-fire (healthy) | did-not-fire (healthy) | unchanged |
| allocation controller | FIRED: 5 signal kinds | **FIRED**: 2 signal kinds | fewer — cycle 0 |
| config referee | did-not-fire (died cycle 5 of cadence 6) | did-not-fire (died cycle 0) | unchanged, same cause |
| **split-budget seat protocol** | **FIRED: 36 reason + 36 extract legs** | **did-not-fire: no split_legs** | **C3 CONFIRMED — protocol off** |
| capture / Pareto frontier | FIRED: 7 signals ×6 | **FIRED**: 7 signals ×1 | fewer — cycle 0 |
| grounded bridge | did-not-fire (refused downstream) | did-not-fire (refused downstream) | unchanged — needs a terminal |
| replay validation | FIRED: 0 violations | **FIRED: 0 violations** | unchanged — record intact |

### The four rows that carry the tranche

1. **split-budget seat protocol: FIRED → did-not-fire.** C3 confirmed on the
   live record, not just on the rebuilt Config. P-A1 ran 36 reason + 36
   extraction legs; P-A2 recorded no `split_legs` structure on any attempt.
   One provider call per attempt, as intended.
2. **variator deferrals: 19 → 0, and one variator call actually made.** The
   merged deferral-gate fix (`5f34e4d00`) demonstrably works: the phase is no
   longer refused for being v6. `hv_set` is still 0 — but the run died at
   cycle 0, so this neither confirms nor refutes that `hv` would have been
   measured. It confirms only that the gate stopped blocking it.
3. **scratchpad: did-not-fire → FIRED.** The one module that newly came alive,
   and the reason the run died: the retry path it reaches has a missing v6
   guard (F7). A module switched on by configuration took the run down.
4. **judge calls: 4 → 18** in one fifth of the cycles, with **0 `scrutiny`**
   in both. The criticism circuit is convening far more adjudication per cycle
   than P-A1 managed.
