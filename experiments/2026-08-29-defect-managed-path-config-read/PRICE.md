# PRICE — what reading the operator's config costs in qualification, measured

Required by the tranche brief BEFORE any design: *"the qualification subject is
built from the manifest, so admitting operator Config values into preparation
MOVES THE SUBJECT DIGEST for every non-default config. Measure it, do not
estimate it."*

Instrument: `probe/price_qualification.py`, output `probe/price.out`.
Re-runnable, offline, deterministic:

    PYTHONPATH=src:mini python \
      experiments/2026-08-29-defect-managed-path-config-read/probe/price_qualification.py

It changes no production code. Carriage is SIMULATED by patching
`preparation._config_for_profile` for the duration of one compile, so every
manifest measured is produced by the real
`build_preparation_manifest` -> `compile_run_manifest` path.

## The control that makes the rest trustworthy

A carriage that starts from `Config()` — the operator asking for nothing —
must be byte-identical to today. Measured:

| | manifest sha256 | qualification subject |
|---|---|---|
| today (synthesised from the profile) | `37e3fa54edb75346…` | `7c0ba0a174fdc2d9…` |
| carrying a DEFAULT-valued Config | `37e3fa54edb75346…` | `7c0ba0a174fdc2d9…` |

**FREE.** No existing home owes anything for the ABILITY to configure. The
first draft of this probe failed this control, because `model_copy` does not
revalidate and carried two typed submodels as bare dicts; the control caught a
measurement artefact that would otherwise have been reported as a price. It is
kept in the probe for that reason.

## Price 1 — FULL carriage (the operator's whole Config wins, except the seven
## fields the provider profile must own)

Measured against all 8 committed `run-config.yaml` files:

| operator config | fields set away from default | echo keys that would move | subject |
|---|---|---|---|
| 2026-08-12-live-grounded-extension-expansion | 7 | `RESEARCH_BACKEND` | MOVED `02bf21e8123ca514…` |
| 2026-08-13-defect-controller-steering-inert | 7 | `RESEARCH_BACKEND` | MOVED `02bf21e8123ca514…` |
| 2026-08-22-live-reach-rich-run | 2 | `RESEARCH_BACKEND` | MOVED `7ed9d28ab27e99a7…` |
| 2026-08-25-change-constructive-frontier | 5 | — | MOVED `99936f85f52b2471…` |
| 2026-08-25-poietics-program | 6 | — | MOVED `99936f85f52b2471…` |
| 2026-08-26-pc2-rematch | 5 | — | MOVED `99936f85f52b2471…` |
| 2026-08-27-defect-split-leg-recording | 5 | — | MOVED `99936f85f52b2471…` |
| 2026-08-27-pc2b-symmetric-reasoning | 5 | — | MOVED `99936f85f52b2471…` |

**8 of 8 move.** One battery per home per distinct configuration.

## Price 2 — NARROW carriage (only the 25 fields the echo already drops)

The cheapest carriage that could satisfy the operator law, because a dropped
field never enters `engine_config_json` at all:

**7 of 8 move — and all seven move to the SAME digest**, `99936f85f52b2471…`.

## Price 3 — the isolation table, which explains prices 1 and 2

Each dropped field carried ALONE, at a non-default value. This is the row the
operator's decision actually rests on:

| verdict | count | fields |
|---|---|---|
| **FREE — zero subject movement** | **23** | `ADJUDICATION_STATUS_AUTHORITY_ENABLED`, `ATTENTION_ALLOCATION_POLICY`, `CAPTURE14_AGE_FLOOR`, `CAPTURE14_ENTER_K`, `CAPTURE14_EXIT_K`, `CAPTURE14_PRECISION`, `CAPTURE14_SC_CEILING`, `CAPTURE14_WINDOW`, `DISCHARGE_POLICY`, `ENGAGED_CRITICISM_AUTHORITY`, `FRAME_SLICE_ATTACKERS`, `FRAME_SLICE_DEPARTURES`, `JUDGE_SEATS_ENABLED`, `JUDGE_SUMMONS_COOLDOWN`, `JUDGE_SUMMONS_PER_CYCLE`, `K_FRAME`, `PROMOTION_ENVIRONMENT_MAX`, `SCHOOL_SEATS_ENABLED`, `SCOPE_MAX_DEPTH`, `SCOPE_MAX_NODES`, `SEED_PROBLEM_BUDGET_FLOOR`, `SPLIT_BUDGET_EXTRACTION_TOKENS`, `SPLIT_BUDGET_SEAT_PROTOCOL` |
| **PRICED — one battery per home** | **1** | `LEGACY_CRITICISM_ENABLED=False` -> `87fab457c9a7dd0c…` |
| not reachable by this design | 1 | `CHANNELS_DISABLED` (already a provider-profile-derived argument) |

`ENGAGED_CRITICISM_AUTHORITY` and `SCHOOL_SEATS_ENABLED` are free ALONE and
priced only in combination with `LEGACY_CRITICISM_ENABLED=False`, because
`preparation.py:493-512` compiles an engaged `criticism_policy` — a real,
typed, behaviour-contract field on the manifest — exactly when that flag is
False. So the single moved digest in Price 2 has ONE cause: asking for
school-routed criticism instead of legacy criticism changes what the run is
contracted to do, and the qualification subject notices.

**All three of the operator's headline gates carry for free**:
`JUDGE_SEATS_ENABLED`, `ADJUDICATION_STATUS_AUTHORITY_ENABLED`,
`SCHOOL_SEATS_ENABLED`.

## What a moved digest actually costs

A moved qualification subject is a cache miss
(`qualification_cache_path(cache_dir, subject_digest)`, `qualification.py:301`),
so the home runs the full production-contract battery once:

- on the measured manifest: **15 pairs x 20 cases = 300 provider calls minimum**,
  before repair turns (`cli/doctor.py`, `PRODUCTION_CASES_PER_PAIR = 20`);
- recorded for a real live home (CLAUDE.md): **~14 minutes, ~1160 calls**.

Paid ONCE per home per distinct configuration, then cached. Nothing is paid by
a home that keeps its configuration at defaults, and nothing at all is paid
retroactively: no committed manifest is recompiled by any of this.

## What does NOT move, under every option measured

- Every committed run root: read (`model_validate_json`), never recompiled.
- The default-valued manifest: `sha256` and `source_config_hash` byte-identical.
- `INV-frozen-surfaces.md`'s two pinned digests (`b9038b84efdea313…`,
  `f3bb65623852…`): both configurations sit at every carried field's default.

## Reading this against the frozen-surface disposition

The monitor's disposition for this batch: *"IF carriage moves ANY QUALIFICATION
SUBJECT DIGEST, that is a PRICED STOP, NOT a grant."* A digest moves. The lane
therefore STOPS here and the decision goes to the operator, priced, in
`STOP.md`. It does not move for the reason the disposition anticipated — it is
not the case that "every non-default config" pays. Twenty-three of
twenty-four gate switches are free; one switch, which changes the criticism
contract, costs one battery per home.
