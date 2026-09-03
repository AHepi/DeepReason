# P-A1 module coverage

**This table is the tranche's headline artifact.** One row per module the
harness owns. Each row carries the typed evidence that the module fired, or
the typed reason it did not. A module that did not fire is a RECORDED RESULT,
not a failure to hide.

Two columns, because they answer two different questions and only the second
is about the live run:

- **CONFIGURED** — did the shipped configuration actually reach this module?
  Evidence: the compiled `run-manifest.json`, the runtime `Config`
  reconstructed from it by `config_from_run_manifest`, and the 49 gates in
  `preflight_pa1.py`. This column is complete before any provider call.
- **FIRED LIVE** — did the module actually do something in the run? Evidence:
  `log.jsonl` event ids, `state_diff` payloads, `llm.role` counts, and the
  capability state, all read by `module_census.py`. Never model prose.

A module can be CONFIGURED and not FIRED — that is an ordinary outcome and one
of the things this run exists to measure. The reverse would be a defect.

---

## Status

| phase | state |
|---|---|
| design frozen (PREREG.md) | DONE — 2026-09-01 |
| configuration compiled and preflighted | DONE — 50/50 gates, 0 failures |
| offline cycle soak on the launch shape | DONE — GREEN, exit 0, 24/24 cycles |
| live run | DONE — 5 cycles, `failed` / `operational_failure`, verify_root 0 violations |
| live census | DONE — 13 modules FIRED, 11 did-not-fire, each with its typed reason |

---

## Column 1 — CONFIGURED (complete, measured on the compiled manifest)

Every row below was read off the compiled `run-manifest.json` or the runtime
`Config` rebuilt from it, on a throwaway probe root, before any provider call.

| module | configured | evidence |
|---|---|---|
| conjecture ensemble | YES | `roles.conjecturer` = 2 seats: `deepseek-v4-pro:0813`, `glm-5.3` |
| argumentative criticism | YES | `roles.argumentative_critic` = `deepseek-v4-pro:0813`; `criticism_policy` STORED with 4 school bindings |
| defended trial | YES | `criticism_policy.authority = "defended_trial"` (explicit compiler argument, not the omitted-policy derivation) |
| defender seat | YES | grant `defender.direct.v1` on `defender[0]` — **non-empty**, the P-S1 cause closed |
| judge ensemble | YES | `judge[0]` qwen3.5:397b (`qwen`), `judge[1]` gpt-oss:120b (`openai-gpt`); grant `judgeruling.direct.v1` on both seats; ≥2 seats across ≥2 families |
| judge dispatch rate | YES | `JUDGE_SEATS_ENABLED=True`, `JUDGE_SUMMONS_PER_CYCLE=2` — both restored through carriage notices |
| adjudication status authority | YES | `ADJUDICATION_STATUS_AUTHORITY_ENABLED=True`, restored through its carriage notice |
| advisory rubric trials | YES | `ADVISORY_TRIALS_PER_CYCLE=1` while `TEXT_RUBRIC_AUTHORITY` stays `observe_only` |
| variator / hv | YES | grant `variator.direct.v1` on `variator[0]` — **non-empty**. P-S1 had none, deferred `transaction-contract-unavailable` 171 times, and never measured hv |
| reach | YES | `PARETO_AXES = ["hv", "reach", "coverage"]`, unchanged from shipped |
| schools | YES | `school_execution.mode = "route_bound"`, 4 bindings round-robin across the two conjecturer seats (school-0/2 → deepseek, school-1/3 → glm-5.3) |
| scratchpad | YES | `scratch_policy.enabled = true`; runtime `Config.scratchpad.enabled = True` |
| successor-question routing | YES | `SUCCESSOR_QUESTION_DESTINATION = "scratchpad.v1"` (the P9 default) |
| successor MINTING | **DELIBERATELY OFF** | `SUCCESSOR_MINTING_ENABLED = False`. Its enablement is an operator launch-time choice carrying the operator's own warning text; this window did not make it |
| simulation capability | YES | `enabled`, `runner_profile = simulation.container.v1`, toolchain `python@deepreason-public-contained.v1`; containment probed available on this host |
| simulation budget | YES (RAISED) | 12 requests / 12 executions, up from the preset's 2/2. **Every containment bound unchanged**: wall 20000 ms, memory 512 MiB, steps 2e6, samples 64, code 64 KiB, `network_policy: forbidden`, `filesystem_policy: isolated_no_filesystem` |
| research capability | YES | `enabled`, `backend_identity = web.contained.v1`, allowlist `arxiv.org` + `en.wikipedia.org`, 6 requests / 3 sources |
| attached-evidence channel | YES (EMPTY DOSSIER) | `attached_evidence.enabled = true`, 16 sources / 8 MiB envelope, **0 sources bound**. The question is self-contained; fabricating sources to make a channel look busy would be the opposite of evidence |
| grounded bridge | YES | `bridge_policy.mode = "grounded_two_stage"` (ships `legacy_thesis`, under which composition refuses `GROUNDED_BRIDGE_POLICY_REQUIRED`); runtime Config agrees |
| bridge grounding review | YES | `grounding_review = true`, `reviewer_role = "grounding_reviewer"` — the only source of behavioural authority for that seat |
| bridge composition CALL | YES | the ladder calls `deepreason bridge build <problem> --target answer` at terminal. P-S1's ladder never did, which is the other half of its `bridge_events: 0` |
| config referee | YES | `config_referee.enabled`, `cadence_cycles = 6` (four firings across 24 cycles). Ships OFF; armed through `POLICY_ENVIRON` pinned in the builder, not the shell |
| near-duplicate / anti-relapse gate | YES | `NEAR_DUP_EPS = 0.2608`, calibrated on the configured embedder over three committed live roots. Ships `None`, under which the gate fails open to hash-only — 100% of P-S1's candidates went unscreened |
| school-convergence tripwire | YES | `RESEED_DIST_MIN = 0.0401` (calibrated) alongside the shipped `RESEED_RATIO_MAX = 0.3` |
| discharge channel | YES | `DISCHARGE_POLICY = discharge-required.v1` (the code default; the YAML line states intent at the place an operator looks) |
| split-budget seat protocol | YES | `reasoning` OMITTED on every seat, which arms `llm/split.py`'s `auto` two-leg protocol |
| allocation signals | YES | `open_loop_notices(bound_roles) → ()` — **zero of the seven policy signals is open-loop on this topology**; `allocation.policy-contested.v1` has its `argumentative_critic` producer |
| embedder | YES | `nomic-ai/nomic-embed-text-v1.5`, fingerprint `d6e3599ce0377000`; `EMBEDDER_FAILURE_POLICY = error` so a missing backend fails before the first model call rather than silently swapping the geometry the two thresholds are calibrated against |

**Configured-column verdict: every module the tranche instruction names is
reachable by configuration. No modularity-law finding is filed.** The one
instrument gap that did appear (FINDINGS.md F1) is in the offline soak's stub,
not in the harness, and does not touch what the live run can do.

---

## Column 2 — FIRED LIVE

Run `4565139800f5ca020e2b74acff45355c1277a9d510068a8e8b4ed65813f1a49c`,
2026-09-01, 5 cycles, 1 093 086 / 3 000 000 tokens, `state: failed`,
`stop_reason: operational_failure`, **`verify_root` violations: 0**.
Read by `module_census.py` from the typed record; the machine-readable form is
`module_census.json`.

**13 FIRED · 11 did-not-fire.** Every "did-not-fire" below carries the typed
reason, and four of them trace to one line of code (F2).

| module | live | typed evidence |
|---|---|---|
| conjecture | **FIRED** | 7 `Conj` events, 47 conjecturer calls across BOTH seats (deepseek 30, glm-5.3 17) |
| criticism | **FIRED** | 5 `Crit` events, 12 argumentative_critic calls |
| defender seat | **FIRED** | 8 `defender.direct.v1` calls on glm-5.3 |
| judge ensemble | **FIRED** | 4 `judgeruling.direct.v1` calls — 2 on qwen3.5:397b, 2 on gpt-oss:120b, cross-family |
| **defended trial** | **FIRED** | 6 `trial-declined`, **0 `scrutiny`**, first trial seqs 359/404/405. Declines: ensemble-split 2, execution-backed 4 |
| adjudication / status authority | **FIRED** | 25 events carry `status_changed` |
| research capability | **FIRED** | `research-awaiting-agent` ×1; 8 research problems on the frontier |
| premise channel | **FIRED** | `premise.batch-translation-offered.v1` ×6, `premise.work-invited.v1` ×2, `premise-answer:DECLINED` ×7 |
| discharge channel | **FIRED** | `discharge-reask` ×6, `discharge-undischarged` ×19 |
| near-duplicate / anti-relapse gate | **FIRED** | `relapse.log.jsonl` written — the gate ran armed at the calibrated eps, where P-S1 left 100% unscreened |
| allocation controller / signals | **FIRED** | `seat-truncation` ×17, `seat-repair` ×17, `seed-lineage-share` ×6, `wander-throttled` ×1, `controller-authority` ×1 |
| split-budget seat protocol | **FIRED** | 36 `reason` legs + 36 `extract` legs |
| capture / Pareto frontier | **FIRED** | seven `capture14.*` signals ×6 each |
| replay validation | **FIRED** | `verify_root` — **0 violations** on a failed run |
| variator / hv | did-not-fire | **NO `hv_set`. 0 variator calls, 19 deferrals** (`hv-floor` 8, `hv-spot-check` 10, `premise-demarcation-variation` 1). F2 |
| reach | did-not-fire | NO `reach_set`. Not deferred — `reach_sweep` ran every cycle and no artifact passed a foreign problem's qualifying criteria. An empirical zero, not a structural one |
| pairwise discrimination | did-not-fire | no `pairwise-observation`; 1 `pairwise-discrimination/judge` deferral. F2 |
| simulation capability | did-not-fire | no `simulation-*` signal. The channel compiled ON with a contained runner and a 12/12 budget; 5 cycles produced no typed simulation proposal |
| scratchpad | did-not-fire | no event carries a scratch payload |
| successor questions | did-not-fire | no `successor-*` signal. Expected: `SUCCESSOR_MINTING_ENABLED` is OFF by the operator's own default |
| attached evidence / dossier | did-not-fire | channel OPEN, dossier EMPTY by design (PREREG §4 R6). Nothing to cite is the typed reason, not a malfunction |
| school convergence / reseed | did-not-fire | tripwires armed at calibrated thresholds and did not fire — the healthy reading |
| config referee | did-not-fire | armed at cadence 6; the run died at cycle 5, one cycle short of its first firing |
| grounded bridge | did-not-fire | `BRIDGE_REASONING_NOT_COMPLETED: canonical run state is failed`. The mode was `grounded_two_stage` and the ladder DID call the composition step — the refusal is downstream of the run's failure, not of P-S1's missing configuration. F4 |

### What this column settles

**The two P-S1 failures the tranche was built to close are closed, and the
record says so with typed events rather than with configuration.** P-S1 filed
140 criticisms as `scrutiny` observations and never summoned a judge. This run
filed **zero** scrutiny, ran the defended-trial circuit six times, and summoned
both cross-family judges. The explicit criticism policy is what did it.

**And the live result is more interesting than "it worked".** All six trials
DECLINED — two on ensemble split (the two judges disagreed), four on
execution-backed grounds. Zero verdicts. That is the frozen cross-family
unanimous configuration behaving exactly as the amended judge law
(CLAUDE.md, 2026-08-28) says it does: under-convicting rather than
prosecuting indiscriminately. Six trials is far too small a sample to confirm
anything, and it is recorded as an observation, not a measurement.

---

## The three known-open defects this run MEASURES and does not fix

| # | defect | P-S1 baseline | **P-A1 measured** |
|---|---|---|---|
| D1 | coverage charging counterconditions — the frontier inversion | frontier sorted on coverage alone | **14 frontier members: 1 seed (7%), 13 harness-minted (93%) — 8 research, 3 connection, 2 discrimination.** The inversion is NOT diluted: `hv` was absent (F2) and `reach` measured zero, so the frontier sorted on coverage alone here too |
| D2 | criticism → new-problem trigger rate | 0 of 1,293 | **0 of 5 `Crit` events / 12 critic calls.** All 14 spawns were harness-minted (conn/research/disc); none successor-triggered. Expected — `SUCCESSOR_MINTING_ENABLED` is OFF by the operator's default — so this run neither confirms nor refutes the defect |
| D3 | premise-channel citation rate | 1 CITED vs 122 DECLINED | **0 CITED, 0 UNCITED, 7 DECLINED** of 2 invitations and 6 batch-translation offers. Same direction as P-S1, smaller sample |

A second, independent confirmation of the D1 mechanism is on the record:
`module_census.py` against the committed P-R1 root reports 117 variator
deferrals and zero `hv_set` / `reach_set` events. P-S1 was not a one-off, and
neither is P-A1 — three roots now show the same shape, and F2 explains all
three with one unconditional line.
