# REPRO — the silent revert, offline, in one script

Artifact: `probe/repro_silent_revert.py` (committed).
Run: `PYTHONPATH=. python experiments/2026-08-28-defect-manifest-config-disclosure/probe/repro_silent_revert.py`
Exit 0 = the defect is present. Exit 1 = every reverted switch is disclosed.
Output before the fix: `probe/repro_before.out`.

## What it drives

`build_manifest_pt1.py:307-333`'s EXACT `compile_run_manifest` call shape —
`schema_version=6`, `workload_profile="text"`,
`rubric_policy="require_cross_family"`, `concurrency=2`, an engaged v3 control
plane, and **no `criticism_policy` argument** — from a `Config` carrying P-T1's
five "everything on" switches (`run-config.yaml:157-169` on
`claude/spec-to-code-technique-k5209o`), then reconstructs the run-time `Config`
through `config_from_run_manifest`, which is what `run_scheduler` is handed.

## Recorded output (before any fix)

```
manifest.criticism_policy = None
manifest.compile_notices  = (CompileNoticeV1(code='SECOND_JUDGE_FAMILY_REQUIRED', ...),)

  REVERTED JUDGE_SEATS_ENABLED                      configured=True             run time=False
  REVERTED ADJUDICATION_STATUS_AUTHORITY_ENABLED    configured=True             run time=False
  REVERTED ENGAGED_CRITICISM_AUTHORITY              configured='defended_trial' run time='observe_only'
  REVERTED LEGACY_CRITICISM_ENABLED                 configured=False            run time=True
  REVERTED SCHOOL_SEATS_ENABLED                     configured=True             run time=False

  reverted: 5 of 5
  disclosed in compile_notices: 0
```

The one notice present is `SECOND_JUDGE_FAMILY_REQUIRED`, about the rubric
gate and the single test profile — unrelated to the five switches, and its
presence is what shows the notice CHANNEL works and simply has nothing to say
about them.

## What this confirms and what it does not

CONFIRMS the diagnosis's primary cause on the one run path: the five switches
are reverted, and `compile_notices` names none of them.

DOES NOT confirm anything about the committed P-T1 root itself — that root is
evidence of its own version and is never recompiled. It is read from disk, and
loading a manifest emits no notices (the after-validator's notice sink is a
different one, and the disclosure this tranche adds lives only in
`compile_run_manifest`). See DELIVERY's P-T1 paragraph.

## A separate finding this reproduction surfaced — PARKED, not fixed

`deepreason reason` never reads the operator's `run-config.yaml` at all.
`RunPreparationService().prepare` → `preparation.build_preparation_manifest`
→ `preparation._config_for_profile` (`preparation.py:308-352`), which
CONSTRUCTS a fresh `Config` from the provider profile. The global `--config`
file reaches `compile_run_manifest` only through `deepreason config compile`
and through hand-written builders. So on the managed path the five switches are
not merely dropped by the echo — they are never read. Parked as **P14** in this
tranche's `PARKED.md`; it is a strictly larger goal than this one and the
disclosure lands first.
