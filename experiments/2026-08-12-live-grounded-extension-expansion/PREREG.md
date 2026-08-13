# PREREG.md — grounded-extension expansion, live run (third launch attempt)

Frozen before any provider call. Map preflight: this tranche is a live
research run over the grounded-extension semantics (DR-CON-warrants-and-
attacks, DR-SUB-adjudication per `docs/map/INDEX.md`) driven through the
engaged criticism authority road (DR-CON-schools, `docs/map/CON-schools.md`)
and the defended-trial mechanism landed by PR #13
(`InquiryTransactionService`, `src/deepreason/informal/trial.py`). No
production code changes in scope; `docs/map/INV-frozen-surfaces.md`
consulted, nothing in this tranche touches a frozen surface.

## Question (seed, verbatim)

> Propose innovative ways to expand and strengthen DeepReason's grounded
> extension — the skeptical fixed-point semantics (spec §4, Pass 1) by
> which conjectures are accepted, refuted, or suspended — such that each
> proposal preserves the existing guarantees: determinism of the fixed
> point, polynomial cost, reinstatement as a derived property, and the
> validity of every committed root.

## Budget

- `--token-budget 1000000`, `--cycles 24` (equivalently `--budget cycles=24`
  on the low-level `deepreason run` entry point this ladder uses — see
  "Launch mechanics").
- Fresh `DEEPREASON_HOME` (`experiments/2026-08-12-live-grounded-extension-
  expansion/home`), isolating the admission store from any other tranche's
  state. This run's qualification step is not the subject-digest-cached
  `deepreason qualify` battery, so "fresh home" here buys isolation, not a
  cache-miss guarantee — see "Launch mechanics" for why.
- One qualification battery for the pinned 4-model combination
  (glm-5.2, deepseek-v4-flash:0731, qwen3.5:397b, mistral-large-3:675b);
  ~14 minutes / ~1160 calls is CLAUDE.md's figure for the subject-digest
  battery under `deepreason qualify` — this run's actual qualification
  mechanism (production-contract doctor) exercises a different, smaller
  inventory (one case block per route/contract pair actually reachable by
  the compiled manifest); its size is reported in `qualify.json` at
  qualify time, not assumed here.

## Dossier (admission imports)

Frozen evidence, bound via `admit_attachment_paths` into the run's
`evidence-dossier.json`/`run-input.json` (V6 attached-evidence envelope,
`inquiry_capability_policy.attached_evidence.enabled=true`), not fetched by
the research backend (`RESEARCH_BACKEND: null` — off by the config's own
declaration):

1. `docs/STATE_OF_THE_THEORY.md`
2. `docs/harness-spec-v1.3.md` (§4, bounded prefix)
3. `docs/proposals/GROUNDED_OVERLAY_PREPLAN.md`
4. `experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md`
5. `docs/map/CON-warrants-and-attacks.md`
6. `docs/map/SUB-adjudication.md`

## Catalog metadata (retrieved 2026-08-13, ollama.com/library)

Ollama Cloud's `/models` endpoint (`llm/endpoints.py:list_models`) returns
only model ids, no parameter/quantization/context metadata — the figures
below come from each model's `ollama.com/library/<name>` page, fetched
today. Per `docs/OLLAMA_CLOUD_OPERATIONS.md` §6, a model id is not a stable
referent across retirements; this is why the tag, not just the family, is
pinned and dated here.

| Role(s) | Tag | Params | Quantization | Context |
|---|---|---|---|---|
| argumentative_critic, defender, summarizer, synthesizer, vision_critic, property_designer, thesis, grounding_reviewer | `glm-5.2` (cloud) | 756B | not published on the library page | 976K (page describes it as "a truly usable 1M-token context window") |
| conjecturer, variator | `deepseek-v4-flash:0731` (cloud) | 284B total / 13B activated (Mixture-of-Experts) | not published for this tag specifically | 1M |
| judge[0] | `qwen3.5:397b` (cloud) | 397B (cloud tag; page does not restate this figure directly per-tag, only lists local sizes up to 122B) | not published for the cloud tag | 256K |
| judge[1] | `mistral-large-3:675b` (cloud) | 675B | not published on the library page | 256K |

`[UNKNOWN]` per `docs/OLLAMA_CLOUD_OPERATIONS.md` §8 discipline: exact
quantization format for every cloud tag above. Not invented; not load-
bearing for this run (routing is by exact tag string, not by these
figures).

## Reasoning-mode field dispatched

`deepseek-v4-flash:0731` (`conjecturer`, `variator`) carries
`reasoning: "medium"` in `run-config.yaml`'s route spec — moderate
(non-zero, non-maximal) thinking effort. Every other role carries
`reasoning: "none"` (the provider-realized knob switched fully off,
`_reasoning_disabled_refusal`'s target state — moot here since this ladder
never calls the friendly `deepreason reason` entry point that check gates,
but the manifest's own per-route `reasoning` field is what the adapter
actually dispatches, and it agrees: `none` everywhere except the two
deepseek routes).

## Launch mechanics (revised)

`run-config.yaml`'s own header names three things the CLI's
`config compile` subcommand cannot express (verified against
`cli/main.py:795-863`: its exposed flags are `judge_family`,
`blind_same_model_judges`, `rubric_policy`, `concurrency`,
`engine_profile`/`profile`/`single_model`, `workload_profile`,
`pack_profile`, `output_profile`, and a `--control-plane-policy` FILE
argument — no flag accepts a `criticism_policy`, and no flag builds a
route-bound multi-school topology from a plain boolean): a two-seat judge
ensemble (`Config.roles["judge"]` is a two-entry list, `qwen3.5:397b` +
`mistral-large-3:675b`), school-routed conjecture AND criticism wired to
the run's own existing routes (no new model diversity), and an explicit
`CriticismPolicyV1` at `defended_trial` authority.

Investigation (this session) found the friendly `deepreason reason` CLI
path is unusable for a second, independent reason beyond what the
config's header names: `RunPreparationService.prepare` (`preparation.py`)
is built around ONE `ProviderProfileV1` broadcast to every role, with
`seat_bindings`/`school_seats`/`criticism_seats` as per-role overrides onto
OTHER single profiles — it has no path to a Config carrying four
genuinely distinct model routes plus a two-member judge list. So this
ladder does not call `deepreason reason` at all. It uses the CLI's
lower-level `run` entry point (`cli/main.py:457-465`,
`--run-manifest <path>`), which accepts a precompiled, root-bound
`RunManifest` directly and has no such restriction:

1. **`build_manifest.py <root>`** (this tranche's compile shim) —
   `load_config(run-config.yaml)`, admits the six dossier files
   (`admit_attachment_paths`), stages their bytes into `<root>/blobs`
   (`BlobStore`, the same two-step `RunPreparationService.prepare` itself
   performs at `preparation.py:816-826` before its own `bind_run_input` —
   `admit_attachment_paths` only persists source bytes into the global
   admission store, keyed by dossier digest, not into `--root`), binds
   the run input (`bind_run_input`), builds `control_plane_policy` as
   `engaged_control_plane_policy_v3()` with `school_execution` replaced by
   `route_bound_school_execution_policy(conjecturer_endpoint_id)` (every
   one of `Config.N_SCHOOLS`'s 4 default schools shares seat 0 / the
   conjecturer's one configured route — `PUBLIC_SCHOOL_COUNT=4` in
   `v6_policy.py` agrees with `Config.N_SCHOOLS`'s own default of 4, so no
   binding is left incomplete), builds `criticism_policy` as
   `engaged_criticism_policy(critic_endpoint_id, authority="defended_trial")`
   (gated exactly as `preparation.py:493-505` gates it: only because
   `LEGACY_CRITICISM_ENABLED=false`, and only using `defended_trial` rather
   than falling back to `observe_only` because
   `ADJUDICATION_STATUS_AUTHORITY_ENABLED=true`), then
   `compile_run_manifest(..., concurrency=2, ...)` and
   `bind_run_manifest`. Writes `<root>/problem.json`
   (`deepreason-text-workload-v1`) with `sources` taken directly from the
   bound dossier's own source ids, so it cannot drift from what
   `_require_v6_workload_match` will check.
2. **`deepreason doctor --run-manifest <root>/run-manifest.json
   --production-contracts --out <root>/production-contract-qualification.json`**
   — the QUALIFY step for a manifest the friendly qualify-cache path never
   sees: `run_production_contract_doctor` exercises every route/contract
   pair the compiled manifest actually has (`production_contract_pairs`),
   writing the fixed-name report `require_v6_production_qualification`
   later reads back from `<root>/production-contract-qualification.json`
   (`ProductionQualificationPolicyV1.report_filename`, confirmed a frozen
   literal in `run_manifest.py:1109`). `DEEPREASON_QUALIFY_CONCURRENCY=2`
   (provider rules: explicit concurrency 2 everywhere, including
   qualification — `cli/doctor.py:_qualification_concurrency` reads this
   env var when the caller passes no explicit value, which
   `run_production_contract_doctor_cli` never does).
3. **`deepreason run --root <root> --run-manifest <root>/run-manifest.json
   --problem <root>/problem.json --budget cycles=24
   --token-budget 1000000`** — the REASON step. `_cmd_run` re-admits the
   root (`_admit_v6_root`), checks the passed `--run-manifest` against the
   one already bound (must be byte-identical — `RUN_MANIFEST_CONFLICT`
   otherwise), enforces `require_v6_production_qualification` against the
   file qualify just wrote, then dispatches `run_scheduler`.
4. **Audit**: `verify_root(<root>)` (read-only open — replay/invariant
   check only, never a writable open) and
   `deepreason --root <root> findings --json`.

Verified end-to-end before any provider call: `build_manifest.py` run
twice against a scratch root produced byte-identical
`manifest_sha256`/`run_input_digest`/`evidence_dossier_digest`
(idempotency — a second `bind_run_manifest`/`bind_run_input` call is a
no-op when canonical bytes agree, a crash-recovery guarantee, not
something this run relies on for correctness). `deepreason config inspect
--run-manifest` against the compiled manifest confirmed all eleven
`V3_CANONICAL_ROLES` populated with the exact routes above, `judge` as a
two-entry list of genuinely distinct families, `concurrency: 2`,
`school_execution.mode="route_bound"` with exactly 4 bindings all pointing
at the one conjecturer route, `criticism_policy.authority="defended_trial"`
with exactly 4 bindings all pointing at the one critic route, and
`inquiry_capability_policy.attached_evidence.enabled=true`.
`deepreason run --run-manifest ... --problem ... --dry-run` against the
same scratch root completed with no error (role matrix printed, no
provider call), confirming `_require_v6_workload_match` and
`_admit_v6_root` both accept what `build_manifest.py` writes.

## Compile notices (all-configs-allowed law — every one recorded verbatim, none block)

**Zero.** `manifest.compile_notices` was empty on the scratch-root dry
compile. Nothing in `run-config.yaml` triggered `JUDGE_FAMILY_AND_
BLIND_SAME_MODEL_CONFLICT` or any other typed disclosure this session's
reading of `compile_run_manifest` found — the yaml passes neither
`judge_family` nor `blind_same_model_judges` (the ensemble is expressed
directly as two distinct `Config.roles["judge"]` entries, which is not a
notice-generating path). If the real qualify/reason run surfaces a notice
`build_manifest.py`'s scratch compile did not, it is recorded in
RESULTS.md, not silently absorbed.

## Provider rules (docs/OLLAMA_CLOUD_OPERATIONS.md, binding)

- Concurrency 2 everywhere: baked into the compiled manifest
  (`concurrency=2`) for the reason phase, and set via
  `DEEPREASON_QUALIFY_CONCURRENCY=2` for the qualify phase.
- 429 backoff 2s/4s/8s/16s, cap 4 attempts; >4 consecutive = quota
  exhaustion → stop typed and report. This run trusts the harness's own
  retry/backoff machinery (not reimplemented in the ladder script); attempt
  counts are on the log (`LLMCall.attempts`) and reported in RESULTS.md.
- HTTP 200 ≠ success — only the typed recorded outcome counts (run state,
  stop_reason, `verify_root`, defended-trial verdict counts from typed
  records). Judgment in RESULTS.md will not cite model prose as evidence.
- No §5 probing in this run.

## Rails

- Leftover root: none found for this tranche (`experiments/2026-08-12-
  live-grounded-extension-expansion/` held only `run-config.yaml` before
  this session; confirmed via `find . -iname "run-*"` and `git log --all
  --oneline | grep -i grounded`, no prior root artifacts anywhere in the
  repo history for this exact tranche).
- A defect found mid-run is PARKED with a ready-to-send prompt, never
  fixed in this window — cross-routing per CLAUDE.md.
- Question reshaping → `deepreason amend`, never a new root — not
  applicable to the low-level `run` entry point directly (amend is part of
  the friendly managed-run surface); if a reshape becomes necessary this
  ladder does not use, it is escalated to the operator before any action.
- `deepseek-v4-flash` battery failure → stop typed, fallback road
  conjecturer glm-5.2 on the operator's word (not applied unilaterally).
- Cycle-0 death → read the diagnostic blob (`<root>/blobs/`) before
  theorising, per CLAUDE.md's hard-won-invariants list.
