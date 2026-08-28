# DIAGNOSIS — the echo is the only carrier, and it carries 25 fields less than the Config

Tranche: `experiments/2026-08-28-defect-manifest-config-disclosure/`.
Evidence: `probe/census_dropped_fields.py`, output `probe/census.out`
(re-runnable: `PYTHONPATH=. python .../probe/census_dropped_fields.py`).
Read alongside `experiments/2026-08-28-audit-run-problems/AUDIT_REPORT.md` §F-A,
which located the cause; this document measures its blast radius and settles the
design question the parked prompt P10 asks first.

## Primary cause (one sentence)

`run_scheduler` is handed `config_from_run_manifest(manifest)` — the manifest's
engine-config echo is the ONLY carrier of run-time `Config` — and
`_versioned_source_config_data` deliberately pops 25 fields out of that echo, so
`Config.model_validate` restores each of them at its DEFAULT with nothing
recorded anywhere that a different value was set.

`src/deepreason/application/text_runs.py:1417`
```python
result, _meter, accounting = run_scheduler(
    harness, config_from_run_manifest(manifest), scheduler_cycles, ...
)
```
`src/deepreason/run_manifest.py:4287-4293`
```python
def config_from_run_manifest(manifest: RunManifest):
    data = json.loads(manifest.engine_config_json)      # 25 fields absent
    ...
    return apply_profile_to_config(Config.model_validate(data), ...)
```
`apply_profile_to_config` (`llm/profiles.py:131-147`) updates only
`PACK_TOKEN_BUDGET`, and `VS_K`/`CRIT_BATCH_K` on the compact profile — none of
the 25 — so a dropped field's run-time value is EXACTLY its `Config` default.

## Correction to the audit's framing, stated plainly

`AUDIT_REPORT.md` §F-A reads as a `--run-manifest` problem: *"the ladder
launches with `--run-manifest` and no `--config`"*. That is where the audit
found it, and every fact it states is right, but the loss is not conditional on
the launch verb. Since the single-run-path unification (2026-08-13, CLAUDE.md's
operations-parity law, ERRATA E26) there is exactly one run path, and it rebuilds
`Config` from the manifest for `deepreason reason` as much as for `deepreason
run --run-manifest`. The managed path appears to keep the criticism switches only
because `preparation.py:499-511` re-expresses them as a `criticism_policy` on the
manifest before the echo is written; the `Config` fields themselves are lost
there too.

**Blast-radius verdict (AUDIT_REPORT.md residue item 4): universal.** Not "only
builders that omit `criticism_policy`". Omitting `criticism_policy` is a
SECOND, INDEPENDENT loss stacked on the first.

## The two limbs, kept separate because they have different fixes

| | limb 1 — the echo | limb 2 — the builder |
|---|---|---|
| what is lost | 22 behavioural `Config` fields, on every run, on every path | the compile-time effect of the 3 identity-only fields, when a builder does not re-express them |
| why | `_versioned_source_config_data` pops them; `Config.model_validate` defaults them | `compile_run_manifest(criticism_policy=None)`; `build_manifest_pt1.py:307-333` never passes one |
| who can fix it | `run_manifest.py` | the builder, or a compile-time disclosure telling the builder |
| in scope here | disclosure only (carriage prices every subject digest — GOAL.md scope contract) | disclosure only (synthesising a policy is a behaviour change, PARKED) |

## Census result 1 — the 25 dropped fields, classified

Measured at schema v6, the only version any live run uses. RUN = the
consumption site is reached with `config_from_run_manifest(manifest)`;
COMPILE = the site only ever sees the builder's own `Config`.

**BEHAVIOURAL — 22.** Consumed at run time, so the drop silently changes what
the run does:

`ADJUDICATION_STATUS_AUTHORITY_ENABLED` (authority.py, rules/crit.py,
rules/experiment.py, signals.py, imports.py) · `ATTENTION_ALLOCATION_POLICY`,
`SEED_PROBLEM_BUDGET_FLOOR` (wander.py) · `CAPTURE14_AGE_FLOOR`,
`CAPTURE14_ENTER_K`, `CAPTURE14_EXIT_K`, `CAPTURE14_PRECISION`,
`CAPTURE14_SC_CEILING`, `CAPTURE14_WINDOW`, `FRAME_SLICE_ATTACKERS`,
`FRAME_SLICE_DEPARTURES` (capture/) · `CHANNELS_DISABLED` (channels.py) ·
`DISCHARGE_POLICY` (discharge/policy.py) · `JUDGE_SEATS_ENABLED`,
`JUDGE_SUMMONS_PER_CYCLE`, `JUDGE_SUMMONS_COOLDOWN` (scheduler/scheduler.py,
authority.py) · `K_FRAME`, `PROMOTION_ENVIRONMENT_MAX`, `SCOPE_MAX_DEPTH`,
`SCOPE_MAX_NODES` (calculus/nomination.py) · `SPLIT_BUDGET_SEAT_PROTOCOL`,
`SPLIT_BUDGET_EXTRACTION_TOKENS` (llm/adapter.py).

**IDENTITY-ONLY — 3.** No run-time consumer exists; their whole effect is a
compile-time decision that the manifest records in its own typed policy fields:

`ENGAGED_CRITICISM_AUTHORITY` and `LEGACY_CRITICISM_ENABLED` →
`criticism_policy` (present/absent, and its `authority`);
`SCHOOL_SEATS_ENABLED` → `control_plane_policy.school_execution`.

**This classification vindicates the drop list's own comments, and convicts
them at the same time.** Its two recurring justifications are *"its effect is
already visible in the compiled manifest's own `criticism_policy`"* and *"it
lives on Config only, consulted at dispatch sites"*. The first is TRUE, for
exactly the three identity-only fields — and only when the builder actually
compiles that policy. The second is the one that fails: "lives on `Config`
only" was written as a reason the echo need not carry the field, but on the
single run path `Config` IS the echo, so "lives on Config only" means "is
lost". Twenty-two fields rest on it.

## Census result 2 — how many committed configurations lose something

Seven of the eight committed `run-config.yaml` files on `main` set at least one
dropped field away from its default. Every one of the seven sets
`ADJUDICATION_STATUS_AUTHORITY_ENABLED: true`, which is BEHAVIOURAL, so every
one of the seven ran, or would run, with a status authority it did not ask for:

| config | behavioural loss | identity-only loss |
|---|---|---|
| 2026-08-12-live-grounded-extension-expansion | ADJUDICATION…, JUDGE_SEATS_ENABLED | ENGAGED_CRITICISM_AUTHORITY, LEGACY_CRITICISM_ENABLED, SCHOOL_SEATS_ENABLED |
| 2026-08-13-defect-controller-steering-inert | ADJUDICATION…, JUDGE_SEATS_ENABLED | same three |
| 2026-08-22-live-reach-rich-run | — | — |
| 2026-08-25-change-constructive-frontier | ADJUDICATION… | same three |
| 2026-08-25-poietics-program | ADJUDICATION…, JUDGE_SEATS_ENABLED | same three |
| 2026-08-26-pc2-rematch | ADJUDICATION… | same three |
| 2026-08-27-defect-split-leg-recording | ADJUDICATION… | same three |
| 2026-08-27-pc2b-symmetric-reasoning | ADJUDICATION… | same three |

The three identity-only losses are only REAL where the builder failed to
re-express them; `probe/census.out` §3 shows which committed manifests carry a
`criticism_policy` and which do not.

## Census result 3 — nothing said so, anywhere, ever

Across all 79 committed `run-manifest.json` files on `main`, at schema versions
1 through 6: **zero** carry any dropped field in their echo, and **zero** carry
a single `compile_notice`. The silence is total and it is not an accident of one
builder.

## Why this is a defect and not a design choice

CLAUDE.md, the seat-config-ungated law (2026-08-28): *"Gates are always
optional: with warnings."* A gate that reverts with neither warning nor refusal
is neither optional nor on. The all-configurations law (2026-08-12) already
converted every compile-time refusal into *"a typed disclosure recorded
alongside the compiled result"*; `CompileNoticeV1` and `compile_notices` are
that channel, built for exactly this, and it is empty on every manifest ever
compiled.

## Traps this recurrence belongs to

`docs/RUN_ANATOMY_SYNTHESIS_2026-08-26.md` §3.2 item 6 recorded the shape; P-T1
is the fifth instance. `docs/ERRATA.md` E44 records the digest incident that
motivated the unconditional pops — the reason the fix must not simply undo them.
