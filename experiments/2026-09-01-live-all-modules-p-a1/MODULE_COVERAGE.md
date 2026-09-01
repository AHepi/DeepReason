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
| configuration compiled and preflighted | DONE — 49/49 gates, 0 failures |
| offline cycle soak on the launch shape | see FINDINGS.md F1 |
| live run | pending |
| live census | pending |

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

*Pending the live run. `module_census.py` fills this from the typed record;
`module_census.json` is the machine-readable form and this table is its
reading.*

---

## The three known-open defects this run MEASURES and does not fix

*Pending the live run. Baselines from P-S1, for comparison:*

| # | defect | P-S1 baseline | P-A1 |
|---|---|---|---|
| D1 | coverage charging counterconditions — the frontier inversion | frontier sorted on coverage alone (hv and reach never measured) | pending |
| D2 | criticism → new-problem trigger rate | 0 of 1,293 | pending |
| D3 | premise-channel citation rate | 1 CITED vs 122 DECLINED | pending |

A second, independent confirmation of the D1 mechanism is already on the
record: running `module_census.py` against the committed P-R1 root
(`experiments/2026-08-25-poietics-program/run`) reports 117 variator
deferrals — `hv-floor` 42, `hv-spot-check` 74,
`premise-demarcation-variation` 1 — and **zero** `hv_set` and **zero**
`reach_set` events. P-S1 was not a one-off; the same null criticism policy
produced the same starved frontier on a different tranche.
