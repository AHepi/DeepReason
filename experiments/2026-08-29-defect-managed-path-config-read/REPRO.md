# Reproduction — the managed path discards `--config`, offline, in three tests

Form: unit-test (offline; no provider, no network, no run root written).

Artifact: `tests/test_managed_path_config_read.py` (committed RED).
Command:

    PYTHONPATH=src:mini python -m pytest tests/test_managed_path_config_read.py -q

Recorded output on the UNCHANGED tree: `proof/repro_red.out` —
**2 failed, 1 skipped**.

## What each test drives, and why it is the smallest sufficient form

| test | drives | today |
|---|---|---|
| `test_reason_forwards_the_operator_config_to_preparation` | the REAL CLI parser and the REAL `_cmd_reason`, with `RunPreparationService` replaced by a capturing double | FAIL |
| `test_managed_manifest_carries_or_discloses_every_operator_setting` | the REAL `build_preparation_manifest`, given the operator's loaded `Config` | FAIL |
| `test_a_default_valued_operator_config_changes_nothing` | the same, at defaults — the half that must NOT move | SKIP (no route exists to exercise) |

## Current output, trimmed to the two load-bearing lines

    AssertionError: deepreason reason discards --config: nothing about the
    operator's configuration file reached RunPreparationService. Captured:
    {'init_args': (), 'init_kwargs': {},
     'request': RunPreparationRequestV1(
        schema_='deepreason-run-preparation-request.v1',
        question='Why is the sky blue?',
        budget=RunBudgetIntentV1(cycles=6, token_budget=100000),
        profile_path=None, managed_run_id=None, dossier_digest=None),
     'prepare_args': (), 'prepare_kwargs': {}}

    Failed: MANAGED PATH HAS NO CONFIGURATION INPUT:
    build_preparation_manifest cannot be given the operator's Config at all --
    build_preparation_manifest() got an unexpected keyword argument 'config'

The first is the whole defect printed as a data structure: the parser DID
accept `--config` (the test asserts `args.config == str(config_path)` first and
that assertion passes), and every field the preparation service then received
is listed, and none of them is a configuration.

## Confirms diagnosis: yes

DIAGNOSIS.md predicted **0 of N carried and 0 of N disclosed, for every N**.
Measured: 5 operator settings, 0 carried, 0 disclosed. The second failure gives
the mechanism in one sentence — the builder has no parameter — which is the
diagnosis's primary cause stated by the interpreter rather than by me.

## Post-fix expectation

    2 failed, 1 skipped   ->   3 passed

field by field: `config_from_run_manifest(manifest).<FIELD> == configured`, OR
a `compile_notices` entry `ENGINE_CONFIG_FIELD_NOT_CARRIED` at
`/engine_config/<FIELD>`; and the default-valued config compiles
byte-identically (`sha256` and `source_config_hash` both unchanged), so no home
owes a qualification battery for a configuration that asked for nothing.

## The one fix-shape assumption, stated rather than hidden

`_managed_manifest` passes `config=<Config>` to `build_preparation_manifest`.
A fix that instead threads a PATH, or adds a field to
`RunPreparationRequestV1`, satisfies test 1 unchanged (it asserts only that
SOMETHING about the file reaches the service) and needs one helper updated for
tests 2 and 3. That is deliberate: the defect is that no route exists, not that
one particular route is missing, and the test file localises the choice to five
lines so a different fix does not have to argue with three assertions.

## Not reproduced, and deliberately: the live consequence

No live run. Every claim above is a compile-time property of the managed path,
and CLAUDE.md's live-run rules make a ladder launch cost without adding
evidence here — the batch is offline by construction and there is no provider
credential in this container. What a carried switch then DOES inside a running
cycle is the second limb (P15) and belongs to the next tranche.
