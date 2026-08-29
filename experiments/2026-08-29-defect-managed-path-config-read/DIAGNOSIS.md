# Diagnosis: the managed path has no INPUT for a configuration, so there is nothing to lose

Tranche: `experiments/2026-08-29-defect-managed-path-config-read/` (P14).
Read alongside `experiments/2026-08-28-defect-manifest-config-disclosure/DIAGNOSIS.md`,
which diagnosed the ECHO's loss. This one is upstream of that and different in
kind.

## Primary cause (one paragraph)

`RunPreparationRequestV1` — the only input to the managed path — has five
fields (`question`, `budget`, `profile_path`, `managed_run_id`,
`dossier_digest`) and none of them is a configuration
(`preparation.py:108-130`). `_cmd_reason` constructs one from `args` and never
reads `args.config` (`cli/main.py:2456-2462`), even though `--config` is a
GLOBAL argument that eleven other commands do read (`cli/main.py:854`, `869`,
`1177`, `1197`, `1216`, `1234`, `1278`, `1293`, `1628`, `1742`). Downstream,
`build_preparation_manifest` calls `_config_for_profile`
(`preparation.py:308-354`), which CONSTRUCTS `Config(...)` from scratch with
seven arguments — `engine_profile`, `model_profile`, `scratchpad`, `bridge`,
`EMBEDDER_MODEL`, `CHANNELS_DISABLED`, `roles` — all derived from the provider
profile, leaving every other field at its `Config()` default. The compiled
manifest is therefore a function of (provider profile, question, budget) and of
nothing the operator wrote.

The distinguishing feature, and the reason this is a different defect from the
one already fixed: **the 2026-08-28 disclosure cannot fire here.**
`ENGINE_CONFIG_FIELD_NOT_CARRIED` is emitted for each dropped field whose value
DIFFERS from its default (`run_manifest.py:2539` `_emit_uncarried_config_notices`).
On the managed path no field ever differs from its default, so the notice
channel is correct and silent, and the silence is indistinguishable from
"nothing was configured". A warning system reports what it is shown; this path
shows it nothing.

## Evidence

### 1. The record — 41 committed managed-path run roots, ONE engine-config echo

Re-runnable: `sh probe/echo_census_managed_roots.sh`, output `probe/echo_census.out`.
Every committed run root carrying a `run-preparation.json` (i.e. minted by
`RunPreparationService`, the managed path) was measured:

    roots=41  distinct_echo_digests=1  distinct_source_config_hashes=9

**41 roots, 8 experiments, 5 weeks, 9 distinct provider configurations — and
one single engine-config echo**, 2208 bytes, `sha256[:16] = 832432e39e26790e`.
The nine `source_config_hash` values differ only because that hash covers
`roles`, which the echo redacts to `{}`. Everything a configuration file could
have said is identical in all 41. That is the defect visible in the record
rather than in the code: a run's configuration on this path is a CONSTANT.

This is the strongest available non-code evidence, and it is what the parked
brief could not yet show — P14 was found by reading the call chain, and the
record now agrees with the reading.

### 2. The record — 0 of 41 carry any disclosure

Same probe: no managed-path manifest carries `compile_notices` (`notices=False`
in every row of the census run). Consistent with §1 and with the primary cause:
the disclosure fires on a difference from default, and there is never one.

### 3. The input model — the absence, in the type

`preparation.py:108-130`. `RunPreparationRequestV1` is `extra="forbid"`,
`frozen=True`, `strict=True`. There is no field a caller could pass a
configuration in, and passing one raises rather than being ignored. The absence
is structural, not accidental.

### 4. The prior tranche's own finding, committed

`experiments/2026-08-28-defect-manifest-config-disclosure/REPRO.md`, section "A
separate finding this reproduction surfaced": *"`deepreason reason` never reads
the operator's `run-config.yaml` at all."* Parked there as P14; `DELIVERY.md`
residue item 2 repeats it.

### 5. The map's own Traps entry, one step short of this

`docs/map/CON-authority.md:239-260`, "Both master gates are invisible to the run
that executes them", with a re-runnable check. It records the ECHO's loss and
ends *"To learn the latter, read the manifest's `compile_notices`."* On the
managed path that instruction returns nothing, because of the cause above. The
Traps entry is true and incomplete; completing it is part of this tranche's fix.

## Implicated code (three sites, exactly)

| site | what it does |
|---|---|
| `src/deepreason/cli/main.py:2456` | `RunPreparationService().prepare(RunPreparationRequestV1(...))` — `args.config` is in scope and unused |
| `src/deepreason/preparation.py:108-130` | `RunPreparationRequestV1` — no configuration field exists to carry one |
| `src/deepreason/preparation.py:308-354` | `_config_for_profile` — constructs a fresh `Config`, seven profile-derived arguments, everything else default |

## Falsifiable prediction (what `dr-reproduce` must show)

Given an operator configuration file that sets N fields away from their
defaults, the manifest the managed path prepares must satisfy, FIELD BY FIELD,
either
  - CARRIED: `config_from_run_manifest(manifest).<FIELD> == configured`, or
  - DISCLOSED: a `compile_notices` entry with code
    `ENGINE_CONFIG_FIELD_NOT_CARRIED` and pointer `/engine_config/<FIELD>`.

Prediction: on the unchanged tree **0 of N** are carried and **0 of N** are
disclosed, for every N and every field — because the file is never opened.
Command:

    python -m pytest tests/test_managed_path_config_read.py -q
    expected on the unchanged tree: FAILED, reporting 0 carried / 0 disclosed

## Ruled out — the one alternative I checked

**"The managed path reads the config and the echo then drops it"** — i.e. that
P14 is just P10 seen again on a different launch verb. FALSIFIED by the
isolation measurement in `PRICE.md`: if the config were being read and dropped,
carrying `RESEARCH_BACKEND` (an ECHOED field, set by three committed configs)
would already be visible in the echo of a managed root. It is not: the echo is
identical in all 41 roots including the ones from homes whose experiment
directory carries a `run-config.yaml`. And the disclosure that P10 landed would
already be firing on the managed path; `probe/echo_census.out` shows it never
has. The two defects stack: this one is that nothing is read, P10's was that
what IS read is not all carried.

## Second cause found and PARKED, not pursued

Run identity does not cover configuration (`_request_digest(request, profile)`
at `preparation.py:722` over a request that has no configuration field). Today
that is harmless because configuration cannot vary; it becomes a run-id
collision the moment this defect is fixed. Recorded as **P18** in `PARKED.md`,
with the disposition the fix tranche must make in writing before code.
