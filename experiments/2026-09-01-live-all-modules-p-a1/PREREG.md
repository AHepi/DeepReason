# P-A1 — pre-registration: every module firing, on a genuinely novel problem

Frozen 2026-09-01, BEFORE any provider call. Nothing below may be revised
after the launch; a design that turns out wrong is corrected in RESULTS.md as
a dated segment, never by editing this file.

This is a RUN tranche. It has NO authority to edit source code, tests, or
frozen surfaces. Under the modularity law (2026-08-26) every behaviour this
run needs must be reachable as CONFIGURATION or ladder scripting; a module
that cannot be turned on without a code edit is a recorded FINDING (a
modularity-law violation), never something this window patches.

---

## §1 Map preflight

Resolved before any design, per CLAUDE.md's MAP PREFLIGHT rule. Read in this
order: `INV-frozen-surfaces.md` first, then the seams, then the subsystems.

**Invariants (read first).**
`DR-INV-frozen-surfaces` · `DR-INV-evidence-channels` · `DR-INV-signal-contract`

**Seams (read before the subsystems they join).**
`DR-SEAM-capabilities-x-channels` — does a channel that says ON actually
reach the capability it enables · `DR-SEAM-bridge-x-manifest` ·
`DR-SEAM-llm-x-manifest` · `DR-SEAM-scheduler-x-workflow` ·
`DR-SEAM-evaluation-x-rules`

**Subsystems.**
`DR-SUB-manifest` (frozen) · `DR-SUB-capabilities` (state digests frozen) ·
`DR-SUB-bridge` · `DR-SUB-scheduler` · `DR-SUB-llm` · `DR-SUB-scratch` ·
`DR-SUB-rules` · `DR-SUB-evaluation` · `DR-SUB-workflow` ·
`DR-SUB-verification` (frozen) · `DR-SUB-evidence`

**Concepts.**
`DR-CON-seats` · `DR-CON-capability-lifecycle` · `DR-CON-schools` ·
`DR-CON-authority` · `DR-CON-criticism-source` ·
`DR-CON-successor-questions` · `DR-CON-run-identity` ·
`DR-CON-scheduler-ranking`

**Frozen-surface disposition.** NONE OF THE FIVE IS CONTACTED. This tranche
writes only inside `experiments/2026-09-01-live-all-modules-p-a1/`, plus ONE
additive row in `scripts/cycle_soak.py`'s `CASES` registry (§7 below prices
that contact and argues it is the instrument's documented extension point,
not a behaviour change). `capabilities/state.py`, `harness.py`,
`invariants.py`, `verification/`, `run_manifest.py` and `qualification.py`
are untouched, as is the frozen-adjacent `route_fingerprint` in
`llm/firewall.py`.

---

## §2 The question, frozen by digest

The operator supplied the seed question verbatim in the tranche instruction.
It lives in `question.py` and is imported, never restated.

```
question_sha256 = 933313a5d9ca6dd86f3052aec6e1f05f395ad00586e08096bd40d1be733d7560
problem_id      = question-933313a5d9ca6dd86f3052aec6e1f05f
```

`build_manifest_pa1.py` refuses to build if those bytes drift, and
`preflight_pa1.py` asserts the digest again before the ladder pays for
qualification.

**Why this question is the right instrument.** It is genuinely open, it is
cheap to attack from several directions at once, and — this is the part that
matters for a module-coverage run — its natural moves EXERCISE the
capabilities under test rather than merely mentioning them. Small-n
exhaustive checks and Monte Carlo on modest n are correct simulation
proposals here, not decoration; the literature on majority dynamics on random
regular graphs is real and reachable through the research allowlist; and the
three clauses of the question (a limit verdict, a structural
characterisation, a quantitative scaling law) give the criteria battery
something to discriminate ON.

**Criteria.** Three ordinary `predicate:` commitments over the artifact's own
bytes, in `criteria.py`, one per clause. They are deliberately lexical and
generous: a predicate over content cannot decide whether a proof sketch is
CORRECT, only whether an artifact addressed the demand. Their discrimination
table is proven before the launch, and the ladder refuses to qualify if it
does not hold:

| text | limit-verdict | obstruction-structure | scaling-law |
|---|---|---|---|
| on-target answer | pass | pass | pass |
| verdict + structure, no law | pass | pass | **fail** |
| verdict + law, no structure | pass | **fail** | pass |
| generic waffle | **fail** | **fail** | **fail** |
| empty | **fail** | **fail** | **fail** |

A malformed `predicate:` is a REFUTATION, not an error — `programs.evaluate`
catches every exception and returns `fail`. A typo would silently refute
every artifact the run ever produces and the finished record would read
exactly like "the models could not construct anything". That is why the table
above is a launch gate and not a comment.

---

## §3 Seats — the operator's assignment, verbatim

> "deepseek-v4-pro:0813 and glm-5.3 hold ALL generation-side seats: both as
> conjecturers, deepseek-v4-pro:0813 as argumentative critic, glm-5.3 as
> defender. Distribute conjecturer seat instances across both models.
> Judges: qwen3.5:397b as judge:0 and gpt-oss:120b as judge:1, cross-family."

| role | seat 0 | seat 1 |
|---|---|---|
| conjecturer | deepseek-v4-pro:0813 | glm-5.3 |
| argumentative_critic | deepseek-v4-pro:0813 | — |
| defender | glm-5.3 | — |
| variator | deepseek-v4-pro:0813 | — |
| property_designer | deepseek-v4-pro:0813 | — |
| thesis (bridge Stage-B composer) | deepseek-v4-pro:0813 | — |
| summarizer (bridge Stage-A ledger) | glm-5.3 | — |
| synthesizer | glm-5.3 | — |
| vision_critic | glm-5.3 | — |
| grounding_reviewer (bridge reviewer) | glm-5.3 | — |
| judge | qwen3.5:397b (`qwen`) | gpt-oss:120b (`openai-gpt`) |

All four model ids were resolved against the LIVE Ollama Cloud catalogue on
2026-09-01 (19 models; all four present). Compile no longer refuses an
unreachable model (operator law 2026-08-12), so a wrong id would not surface
until mid-run.

**Thinking is ON everywhere.** The `reasoning` field is OMITTED, not set to
`"none"`: P-S1 measured that `reasoning_effort: "none"` does NOT disable
reasoning on glm-5.3 — it only merges the trace into content. Omitting it
also arms `llm/split.py`'s `auto` two-leg split-budget protocol, which is the
mechanism that stops hidden reasoning from consuming a seat's whole
completion cap.

`max_tokens` is 49152 on the generation seats (P-C2b used 32768) and
`timeout_s` is 1800. **Residue:** 1800 is an extrapolation from P-C2b's
measured 737s / 420s / 460s at ceiling 32768, not a measurement at 49152.

---

## §4 The seven configuration requirements, and the mechanism for each

Each row names the requirement, the configuration value that satisfies it,
and how the launch PROVES it before spending a token. Every mechanism is a
configuration value or a ladder call. **No requirement needed a code edit,
so no modularity-law finding is filed under this section.**

### R1 — Defended trials, under an EXPLICIT criticism policy

Four Config fields plus one explicit compiler argument:

```
JUDGE_SEATS_ENABLED: true                     ADJUDICATION_STATUS_AUTHORITY_ENABLED: true
ENGAGED_CRITICISM_AUTHORITY: defended_trial   LEGACY_CRITICISM_ENABLED: false
JUDGE_SUMMONS_PER_CYCLE: 2                    ADVISORY_TRIALS_PER_CYCLE: 1
```

and `build_manifest_pa1.py` passes `criticism_policy=` EXPLICITLY to
`compile_run_manifest` rather than relying on the derivation the judge-canary
tranche shipped on 2026-09-01. Measured on the compiled manifest:
`criticism_policy.authority = "defended_trial"`, 4 school bindings.

`ARGUMENTATIVE_AUTHORITY` stays `observe_only` deliberately: declaring
`trial_required` trips `CALIBRATION_RECEIPT_REQUIRED` for any text workload
against a verifier that is a permanent stub and can never pass. Status-changing
authority arrives through the engaged criticism engine, which that wall never
inspects.

### R2 — Simulation AND research ON, with real budgets

`CHANNELS_DISABLED: []`, `RESEARCH_BACKEND: agent`, and the builder passes
`engaged_inquiry_capability_policy(POLICY_ENVIRON, attached_evidence=True,
config=config)`.

**A measured near-miss, recorded because it would have produced a green-looking
dead run.** The first probe compile passed the compiler's OWN derived
capability policy (read back from a probe manifest) and reported
`simulation_enabled: false`, `research_enabled: false` with every switch in
`run-config.yaml` already set — the exact shape P-S1 ran in. Compiling without
an explicit `inquiry_capability_policy` derives an ALL-DISABLED policy. The
fix is the explicit engaged preset; `preflight_pa1.py` asserts both flags so
this cannot regress silently.

Simulation runs the CONTAINED runner (`DEEPREASON_SIMULATION_RUNNER` unset =
contained), under which model-authored `sandboxed_python_v1` programs actually
execute. Containment was probed available on this host before the launch.

**Declared deviation from the engaged preset.** The preset meters TWO
simulation requests and TWO executions PER RUN (`capabilities/simulation.py`
:586,595 — over the whole capability state, not per cycle). Across 24 cycles
that is a smoke-test budget, and the tranche instruction asks for "real
budgets". This run raises requests 2→12, executions 2→12, proposals-per-turn
1→2. **Every containment bound stays exactly as the 2026-08-27 safety verdict
froze it**: `maximum_wall_ms` 20000, `maximum_memory_bytes` 512 MiB,
`maximum_steps` 2 000 000, `maximum_samples` 64, `maximum_generated_code_bytes`
65536, `network_policy: forbidden`, `filesystem_policy:
isolated_no_filesystem`, `fixed_seed_set (7,)`, contained runner profile. What
moves is HOW MANY of the same audited operation may run, which is a budget and
not a safety property.

Research stays at the audited preset — 6 requests, 3 sources, allowlist
`arxiv.org` + `en.wikipedia.org` — which is already proportionate to
`RESEARCH_PERIOD: 5` over 24 cycles.

### R3 — The bridge composes instead of refusing

P-S1 ended with `bridge_events: 0` for two independent reasons and this run
closes both. The mode ships `legacy_thesis`, under which
`application/bridge.py` refuses with `GROUNDED_BRIDGE_POLICY_REQUIRED`; it IS
a configuration value:

```yaml
bridge:
  mode: grounded_two_stage
  reviewer_role: grounding_reviewer
  grounding_review: true
```

and the ladder CALLS the composition step at terminal —
`deepreason --root <root> bridge build <problem> --target answer --json` —
which P-S1's ladder never did. Measured on the compiled manifest:
`bridge_policy.mode = grounded_two_stage`, and the runtime Config rebuilt from
that manifest agrees.

`reviewer_role` is `grounding_reviewer`, not the shipped `judge`: the operator
named qwen3.5 and gpt-oss as JUDGES (adjudication), and `grounding_review` is
the only source of behavioural authority for the reviewer seat — pointed
elsewhere, that seat qualifies `inactive_no_authorized_contract` and every
phase needing it defers `transaction-contract-unavailable`.

### R4 — The Pareto axes: hv and reach must be able to measure

P-S1 sorted on coverage alone because the variator seat was denied a
transaction contract 171 times. **The cause is the same null criticism policy
as R1**, and one fix closes both: `_route_seat_behavioral_contract_assignments`
(`run_manifest.py:2059-2077`) grants defender / judge / variator contracts
exactly when a STORED policy has `authority == "defended_trial"`. With no
stored policy the set is empty, the variator has nothing to dispatch under,
and `Scheduler._defer_v6_model_phase` files
`transaction-contract-unavailable` instead.

Measured on the compiled manifest — the grants are non-empty:

```
defender: ["defender.direct.v1"]   judge: ["judgeruling.direct.v1"]   variator: ["variator.direct.v1"]
```

`PARETO_AXES` stays at its shipped `["hv", "reach", "coverage"]`.
**Launch gate:** the soak must show hv and reach emitting non-`none` signals
before any live call.

### R5 — The near-duplicate gate, armed against a MEASURED threshold

`NEAR_DUP_EPS: 0.2608`. It ships `None` and the gate then fails open to
hash-only — 100% of P-S1's candidates went unscreened. An ABSOLUTE distance
must be calibrated to the embedder; the `runs/embedder_design` record refuted
every blind distribution-mapping shortcut.

Measured 2026-09-01 with `deepreason --root <root> calibrate` on the neural
embedder this run configures (fingerprint `d6e3599ce0377000`,
`nomic-ai/nomic-embed-text-v1.5`, fastembed-0.8.0+onnxruntime-1.29.0), over
THREE independent committed live roots:

| corpus | planted-dup max | within-problem p10 | within median | recommended |
|---|---|---|---|---|
| poietics P-R1 (n=721) | 0.2608 | 0.0401 | 0.0813 | 0.2608 |
| reach-rich (n=276) | 0.2608 | 0.0322 | 0.0564 | 0.2608 |
| epoch-3 (n=440) | 0.2608 | 0.0359 | 0.0700 | 0.2608 |

0.2608 is the instrument's own recommendation and is re-derivable by that
command, which is why it is preferred to any hand-picked number. **Residue:**
`separable` is FALSE — planted-duplicate distances overlap the sibling tail —
so this is the duplicate-CEILING fallback, not a midpoint between separated
classes. The consequence is bounded: stage 2 only NARROWS which refuted priors
face the stage-3 battery check, and a BLOCK still requires verdict-vector
equivalence, so a wide eps costs compute rather than admissions.

`RESEED_DIST_MIN: 0.0401` is armed from the same calibration (the richest
corpus's within-problem p10). Its ratio-shaped companion `RESEED_RATIO_MAX`
already ships armed at 0.3; leaving this at None would leave half the
school-convergence detector off while calling the run "everything on".

### R6 — Scratchpad, dossier channel, successor questions

`scratchpad: {enabled: true}` (ships disabled; every pack/channel bound stays
at its audited default). The attached-evidence channel is ON
(`attached_evidence=True`, 16 sources / 8 MiB envelope) **carrying an EMPTY
dossier**: the question is self-contained and fabricating source documents to
make a channel look busy would be the opposite of evidence. MODULE_COVERAGE.md
records that as the typed reason, not as a firing.

`SUCCESSOR_QUESTION_DESTINATION: scratchpad.v1` — the P9 default routing,
written out. `SUCCESSOR_MINTING_ENABLED: false` — **the minting flag stays OFF.
Its enablement is an operator launch-time choice carrying the operator's own
warning text, and this window does not make it.** The routing destination
registry HAS landed on main (`SUCCESSOR_QUESTION_DESTINATION` is real Config
surface, `successor/mint.py` is the one gated producer), so there is no
known-open gap to record under R6.

### R7 — Signals: which of the seven can emit, and what is open-loop

`allocation.POLICY_SIGNALS` names seven, and one producer predicate per signal
decides from the BOUND ROLES alone whether this topology contains anything
that could emit it. Measured on the compiled manifest:

```
allocation.seat-truncation.v1      producer: any seat            OK
allocation.seat-repair.v1          producer: any seat            OK
dropped-call                       producer: any seat            OK
allocation.policy-authorized.v1    producer: any seat            OK
allocation.policy-contested.v1     producer: argumentative_critic OK (deepseek seat bound)
allocation.seed-lineage-share.v1   producer: any seat            OK
allocation.wander-throttled.v1     producer: any seat            OK

open_loop_notices(bound_roles) -> ()   ZERO open loops
```

So this run carries NO `ALLOCATION_OPEN_LOOP` notice, and that is itself the
recorded result for R7. The topology binding no `argumentative_critic` is the
live open-loop case; this one binds it.

### The compile notices this configuration carries

Six, all `ENGINE_CONFIG_FIELD_NOT_CARRIED`, one per switch the manifest's
engine-config echo drops:
`ADJUDICATION_STATUS_AUTHORITY_ENABLED`, `ENGAGED_CRITICISM_AUTHORITY`,
`JUDGE_SEATS_ENABLED`, `JUDGE_SUMMONS_PER_CYCLE`, `LEGACY_CRITICISM_ENABLED`,
`SCHOOL_SEATS_ENABLED`.

These are the P10 defect's REPAIR working, not the defect: each notice carries
the configured value, and `_carried_config_values` restores it into the Config
the run actually runs on. `preflight_pa1.py` reconstructs that runtime Config
and asserts every one of the six, so a silent revert cannot reach a launch.
The `LEGACY_CRITICISM_ENABLED` notice prices its own consequence — engaging
the criticism policy changes the qualification subject, so this home
requalifies once (~14 minutes). That price was accepted by the operator on
2026-09-01.

**Schools are ROUTE-BOUND, not conditioning-only.** `engaged_control_plane_
policy_v3` ships `school_execution` at `conditioning_only` on the stated
ground that routing diversity is a provider-topology question. This run IS
that question: the four seeded schools are bound round-robin across the two
conjecturer seats (school-0/2 → deepseek, school-1/3 → glm-5.3). One field of
the public preset moves; everything else stays as frozen.

---

## §5 Budgets, depth, and the launch shape

| | value | why |
|---|---|---|
| cycles | 24 | P-C1/P-C2b's depth; the CYCLE budget is meant to bind first — a token-bound stop truncates mid-cycle, a cycle-bound stop does not |
| token budget | 3 000 000 | P-C1/P-R1's value. "Tokens are cheap; the agent is not" |
| concurrency | 2 | Ollama Cloud limits are per ACCOUNT and plan-gated: own the limit client-side |
| DEEPREASON_HOME | the tranche's own `home/` | isolates this tranche's admission store and qualification cache |
| qualification | FULL battery expected | new subject (four models, new config, engaged criticism policy). ~14 min minimum, likely more with four providers. Priced and accepted by the operator on 2026-09-01; not to be dodged by trimming the config |

---

## §6 The three known-open defects this run MEASURES and does not fix

Queued as their own tranches. Touching any of them here destroys attribution.

1. **Coverage charging counterconditions** (`capture/programs.py` OVERRUN) —
   the frontier inversion. With hv and reach live it is diluted, not gone.
   **To record:** the final frontier's composition — how many members answer
   the operator's seed question versus harness-minted problems.
2. **Criticism → new-problem trigger rate.** P-S1: 0 of 1,293.
   **To record:** the rate on this run.
3. **Premise-channel citation rate.** P-S1: 1 CITED against 122 DECLINED.
   **To record:** the rate on this run.

---

## §7 What counts as evidence, and the one instrument contact

**Evidence is typed only:** run state, `stop_reason`, the audit JSON,
`verify_root`, `progress.jsonl`, the compiled manifest, and the `log.jsonl`
event ids MODULE_COVERAGE.md cites. Model prose — including this window's —
is never evidence.

**The one file outside this tranche directory that this window touches** is
`scripts/cycle_soak.py`, and only to add one row to its `CASES` registry.
That registry is the instrument's documented extension point: `pr1`, `pc1`,
`pc2`, `pc2b` and `split-legs` were each added the same way by their own
tranche, and a case is explicitly "a REAL config shape, not a synthetic one".
The row reads this tranche's committed `run-config.yaml` and delegates root
construction to this tranche's committed builder, so it cannot drift from the
launch. It changes no existing case and no soak logic. It is not a frozen
surface and not a behaviour change; recorded here so the contact is visible
rather than discovered in the diff.

---

## §8 Launch gates — the run does not start until all of these hold

1. `python -u scripts/cycle_soak.py --case pa1` exits GREEN.
2. The soak shows `hv` and `reach` emitting non-`none` signals (R4).
3. The soak shows zero unexpected `ALLOCATION_OPEN_LOOP` notices (R7).
4. `preflight_pa1.py` passes: question digest, criteria discrimination table,
   the six carriage assertions, defended-trial authority, non-empty
   defender/judge/variator grants, grounded bridge, both capability channels
   enabled, `NEAR_DUP_EPS` armed, cross-family judge families distinct.
5. Every seat's model is present in the live provider catalogue.
6. `deepreason embedder-warmup` has been run in the setup phase.

**Stop-and-ask conditions, bubbled to the operator and never resolved by this
window:** any frozen-surface contact, any needed code edit, any `REFUSED_*`
or typed stop that configuration cannot route around, and the
successor-minting flag decision.
