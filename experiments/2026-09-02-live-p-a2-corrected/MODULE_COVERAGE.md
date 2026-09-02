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

**Column 2 is EMPTY, and that is the tranche's result rather than a gap in
it.** Neither epoch reached a reasoning cycle:

| epoch | manifest | what happened | cycles run |
|---|---|---|---|
| 1 | `e958a37b` | qualification refused after 96 min: 22/23 pairs, the single failure `groundingrepairwirev1.direct.v1` on glm-5.3 at 5/20 (FINDINGS.md F4) | **0** |
| 2 | *(amended shape)* | qualification refused after 26 min: 5/23 pairs, `ENDPOINT_HTTP_429` throughout — the account's session usage limit (FINDINGS.md F5) | **0** |

So there is no `log.jsonl`, no `state_diff`, no `llm.role` count and no
capability state for P-A2. **Every row below would be a fabrication if it
carried a P-A2 verdict**, and the honest table is the one that says so once,
loudly, rather than twenty-four times in a column of dashes.

What CAN be said, and is said in Column 1 above, is that every module is
CONFIGURED and reachable — read off the compiled manifest and the runtime
Config, which are complete before any provider call and were verified at
62/62 preflight checks on the amended shape.

### The P-A1 baseline, re-derived on this checkout

Column 3 needs P-A1's side to come from the SAME instrument and the SAME code
version as P-A2's would have, so `module_census.py` was run against P-A1's
committed root here rather than quoting P-A1's prose. That side is real and is
recorded now, so a later window resuming this tranche starts with the
comparison half-built instead of re-deriving it:

| module | P-A1 (re-derived) | evidence |
|---|---|---|
| conjecture (rules/conj) | **FIRED** | Conj events=7, conjecturer calls=47 |
| criticism (rules/crit) | **FIRED** | Crit events=5, argumentative_critic calls=12 |
| defender seat | **FIRED** | defender calls=8 |
| judge ensemble | **FIRED** | judge calls=4 |
| defended trial (status-changing criticism) | **FIRED** | {"first trial seqs": [359, 404, 405], "judge calls": 4, "scrutiny (observe-only filings)": 0,... |
| pairwise discrimination | **did-not-fire** | no pairwise-observation event (F2: the pairwise-discrimination phase is one of the eleven def... |
| adjudication / status authority | **FIRED** | 25 events carry status_changed; first seqs [6, 7, 8] |
| variator / hv measurement | **did-not-fire** | NO hv_set in the record; variator calls=0; deferrals=19 |
| reach measurement | **did-not-fire** | NO reach_set in the record |
| scratchpad (advisory workshop) | **did-not-fire** | no event carries a scratch payload |
| successor questions | **did-not-fire** | no successor-* signal in the record |
| simulation capability | **did-not-fire** | no simulation-* signal; deferrals={('premise-demarcation-variation', 'variator'): 1, ('hv-spo... |
| research capability | **FIRED** | {"research-awaiting-agent": 1} |
| attached evidence / dossier | **did-not-fire** | the channel is OPEN but the dossier is EMPTY by design (PREREG §4 R6): nothing to cite is the... |
| premise channel | **FIRED** | {"premise-answer:DECLINED": 7, "premise.batch-translation-offered.v1": 6, "premise.work-invit... |
| discharge channel | **FIRED** | {"discharge-reask": 6, "discharge-undischarged": 19} |
| near-duplicate / anti-relapse gate | **FIRED** | {"relapse.log.jsonl": true, "signals": {}} |
| school convergence / reseed | **did-not-fire** | no school-convergence or reseed signal (the tripwires are armed and did not fire) |
| allocation controller / signals | **FIRED** | {"allocation.seat-repair.v1": 17, "allocation.seat-truncation.v1": 17, "allocation.seed-linea... |
| config referee | **did-not-fire** | no config-referee signal in the record |
| split-budget seat protocol | **FIRED** | {"extract": 36, "reason": 36} |
| capture / Pareto frontier | **FIRED** | {"capture14.attack-target-entropy.v1": 6, "capture14.criticism-debt.v1": 6, "capture14.exogen... |
| grounded bridge (ledger + composition) | **did-not-fire** | bridge build produced no readable JSON -- see bridge-build.stderr.log |
| replay validation (verify_root) | **did-not-fire** | verify_root produced no readable JSON |

**P-A1: 13 FIRED · 11 did-not-fire** (the two extra `did-not-fire` rows here
versus P-A1's own table are `grounded bridge` and `replay validation`, which
the census reads from ladder-written sibling JSON files that live in P-A1's
tranche directory rather than inside its root — an artifact of re-deriving
from the root alone, not a disagreement about what P-A1 did).

### What the third column would have measured

Recorded so the question is not lost, and so a resumed tranche knows exactly
which rows carry the weight:

- `variator / hv` — P-A1: **NO `hv_set`, 0 variator calls, 19 deferrals.**
  The row P3 turns on, and the one most likely to move: `hv-floor` and
  `hv-spot-check` both map to `variator.direct.v1` in
  `workflow/legacy_phase_contracts.py`, the deferral gate now consults that
  table rather than `schema_version` literals, and this manifest holds the
  grant.
- `defended trial` — P-A1: 6 `trial-declined`, **0 `scrutiny`**, only 2 of
  the 6 reaching judges. The row P1 turns on.
- `grounded bridge` — P-A1: did-not-fire, refused
  `BRIDGE_REASONING_NOT_COMPLETED` downstream of the run's failure. It needs a
  run that reaches a terminal at all.
- `simulation capability`, `scratchpad`, `config referee` — P-A1: did-not-fire,
  each for a different typed reason (no proposal in 5 cycles; no scratch
  payload; died at cycle 5, one short of the referee's first firing at cadence
  6). All three are cycle-depth questions that 24 cycles could answer and 5
  could not.

The five pre-registered predictions P1–P5, and Amendment 1's P6, are all
**UNSCORED**. That is recorded as an unscored outcome, never as a negative
one: an unrun prediction is not a refuted prediction.
