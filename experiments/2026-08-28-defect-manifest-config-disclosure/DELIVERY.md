# DELIVERY — P10 / audit finding F-A

Tranche: `experiments/2026-08-28-defect-manifest-config-disclosure/`.
Branch: `claude/seat-config-gates-audit-1o0mu8`, merged from `main` at
`90b1347f4` (render-layout tranche; cones do not overlap).
Route: `deepreason-orchestrator` (defect), all six phases.

## What was wrong, and what is true now

A `run-config.yaml` set five "everything on" switches; the run executed with
all five at their OFF defaults and `compile_notices` was `[]`. Two seats were
qualified, at real cost, for a road closed four times over.

A manifest compiled from a `Config` that sets any of 25 dropped fields away
from its default now carries one typed `ENGINE_CONFIG_FIELD_NOT_CARRIED`
compile notice per field, naming the configured value and the value the run
will take. `deepreason config compile` already printed `compile_notices`;
`deepreason run` now does too, so a manifest compiled by someone else warns at
the point of launch.

## The operator law this answers, and the half it does not

> "Gates are always optional: with warnings." (2026-08-28)

The warning half is delivered. The other half — a configuration being able to
turn those gates ON — is NOT, and is parked rather than quietly dropped:
22 of the 25 dropped fields are consumed at sites inside a running cycle and no
route carries them into a manifest-launched run. `PARKED.md` P15 states the
gap, prices it, and writes down the one design that would close it. Silence was
the defect; the absence is a design question the operator owns.

## The diagnosis that corrected the audit

`AUDIT_REPORT.md` §F-A reads as a `--run-manifest` problem. Every fact it
states is right and the framing is too narrow: since the single-run-path
unification (2026-08-13) `run_scheduler` is always handed
`config_from_run_manifest(manifest)`, so the echo is the ONLY carrier of
run-time `Config` and the loss is universal — `deepreason reason` included.
That settles `AUDIT_REPORT.md` residue item 4: **not** "only builders that omit
`criticism_policy`". Omitting `criticism_policy` is a second, independent loss
stacked on the first.

Census over every committed `run-config.yaml` and `run-manifest.json` on `main`
(`probe/census_dropped_fields.py`, output `probe/census.out`):

- 25 fields dropped at schema v6 — **22 BEHAVIOURAL** (consumed at run time),
  **3 IDENTITY-ONLY** (`ENGAGED_CRITICISM_AUTHORITY`,
  `LEGACY_CRITICISM_ENABLED`, `SCHOOL_SEATS_ENABLED` — their effect is a
  compile-time decision the manifest records in its own policy fields).
- **7 of 8** committed `run-config.yaml` lose at least one; all seven lose
  `ADJUDICATION_STATUS_AUTHORITY_ENABLED`, which is behavioural.
- **0 of 79** committed manifests carry a dropped field or a single notice.

The drop list's own comments were read before designing, as the brief
required. Their first justification ("its effect is already visible in the
compiled manifest's own `criticism_policy`") is TRUE, for exactly the three
identity-only fields, and the disclosure honours it: those three stay silent
when the manifest demonstrably expresses the choice. Their second ("it lives on
`Config` only, consulted at dispatch sites") is the one that fails: on the
single run path `Config` IS the echo, so "lives on Config only" means "is
lost". Twenty-two fields rested on it.

## Design: the third road, evaluated first as instructed

Priced in `FIX.md` before any code: (1) carrying the fields in the echo was
rejected on the recorded price — every subject digest and 22 wire-byte goldens,
`docs/ERRATA.md` E44; (2) a new typed disclosure block on the manifest was
measured digest-neutral and rejected as the larger of two viable designs;
(3) the existing `CompileNoticeV1` / `compile_notices` channel was chosen —
no new field, model, validator, schema guard or serializer branch. No `data.pop`
line was added, removed or made conditional, so `source_config_hash` is
byte-identical at every schema version.

## Frozen surfaces — two contacts, both granted, both recorded

**Surface 4** (`run_manifest.py`), forecast and granted conditionally by the
monitor. Named in `FIX.md` before implementation; recorded in
`docs/map/INV-frozen-surfaces.md` §4 with re-runnable checks. Insertions only;
no model, validator, serializer or record format touched.

**Surface 5** (`qualification.py`), requested in `FIX.md` Amendment 1 after
measurement surfaced the need, and GRANTED by the monitor on those
measurements. Recorded in `INV-frozen-surfaces.md` §5 to the same standard,
with the digest table and three re-runnable checks. Seven inserted lines
excluding `ENGINE_CONFIG_FIELD_NOT_CARRIED` notices from the qualification
subject, so a disclosure cannot defeat the exclusion it describes.

**Why no committed root changes verdict — categorically.** A committed
manifest is READ (`model_validate_json`), never recompiled, and the disclosure
is emitted only inside `compile_run_manifest`, which no read path calls. Same
object, same canonical bytes, same `sha256`, same subject payload, same
`verify_root` inputs. The root sweep is retired (operator ruling 2026-08-22);
`test_loading_a_committed_manifest_adds_no_notice` makes the argument fail if
it stops being true.

## Digest movement: zero

| config | base | delivered |
|---|---|---|
| default | `02ee7e098bb9…` | identical |
| `JUDGE_SEATS_ENABLED=True` | `02ee7e098bb9…` | identical |
| `ADJUDICATION_STATUS_AUTHORITY_ENABLED=True` | `02ee7e098bb9…` | identical |
| `SCHOOL_SEATS_ENABLED=True` | `02ee7e098bb9…` | identical |
| P-T1's five switches | `02ee7e098bb9…` | identical |
| a pre-existing notice-bearing manifest | `061efe5bdf7e…` | identical |

`source_config_hash`: `6c2d01f6b8cbe65e…` (v1/v2), `2624603035bc335e…` (v3-v6),
byte-identical. No cache invalidated, no battery owed, no pin re-pinned.

## The P-T1 manifest, after this fix

**It is an artifact of the pre-fix version and it does NOT read as carrying a
disclosure — permanently, by design.** `experiments/2026-08-27-change-technique-run/run/run-manifest.json`
(branch `claude/spec-to-code-technique-k5209o`) is read, never recompiled:
loading it under this code attaches no notice, so its `compile_notices` stays
`[]`, its canonical bytes and `sha256` are unchanged, and its replay verdict is
untouched. Per the old-runs-owe-nothing law (2026-08-14) that is correct and
owes nothing — a committed root is evidence of its own version, and the record
of what P-T1 actually lost lives in `AUDIT_REPORT.md` §F-A and in this
tranche's `probe/census.out`, not retro-fitted into that file. Re-running
`build_manifest_pt1.py` today would mint a DIFFERENT manifest — the same config,
plus five `ENGINE_CONFIG_FIELD_NOT_CARRIED` notices and therefore different
bytes and a different `sha256` — which is the fix working, not a conflict with
the committed root. The nearest committed analogue is already pinned as a test:
recompiling `experiments/2026-08-12-live-grounded-extension-expansion`'s
config now yields exactly two notices (its two behavioural switches; the three
identity-only ones are silent because that builder re-expressed them), asserted
in `tests/test_single_run_path.py`.

## Instruments

| instrument | result | baseline | delta |
|---|---|---|---|
| `python -m pytest tests/ -q -n 4` |  **4412 passed, 0 failed**, 6 skipped | 4403 passed, 0 failed (main `90b1347f4`) | +9, exactly this tranche's new regression file |
| `python tools/docs_verify.py` | **5 failed** (`probe/docs_verify_merged.out`) | 4 failed (3 shallow-clone, 1 pre-existing) | **+1, reported as a finding — see below** |
| `probe/repro_silent_revert.py` | exit 1, "no silent revert" | exit 0, defect present | inverted |

Mutation proof: `probe/regression_red.out` (three disclosure tests RED on a
tree carrying only the derived drop-set helper) → `probe/regression_green.out`.
Two fixture updates, both predicted in `FIX.md` before the edit (Amendments 2
and 3); neither weakens an assertion — each records MORE than it did.

## The one docs_verify delta, reported rather than removed

`docs_verify` is 5 failed against a stated baseline of 4. The fifth is
`INV-frozen-surfaces.md:297`, a tripwire that arrived with the merge from main
(`925b17f62`, in `90b1347f4`):

```
! git diff --name-only origin/main...HEAD | grep -qE "...|/run_manifest\.py|/qualification\.py|..."
```

It is green on `main` only because `origin/main...HEAD` is empty there, and it
is red on ANY branch that touches a frozen-surface file — a granted contact and
an ungranted one alike, because it cannot tell them apart. This branch turns it
red with exactly the two contacts the monitor granted on the record. Six of the
seven granted contacts already recorded in that same document would each have
turned it red on their own branch.

It was not edited and not worked around. A tripwire another tranche landed
yesterday is not something to file down because it caught you, and a check that
forbids contact outright contradicts the section it sits in rather than being
satisfied by a better diff. PARKED as **P16** with the shape of a fix that
would keep it a real tripwire.

The other four are the stated baseline exactly: three shallow-clone failures in
`CON-run-identity.md` (200, 202, 204) and the pre-existing falsified census at
`INV-frozen-surfaces.md:181` (parked P7, execution-safety).

## Map moved in the same commits

`docs/map/INV-frozen-surfaces.md` (both granted contacts, with checks),
`docs/map/SUB-manifest.md` (two Traps entries), `docs/map/CON-authority.md`
(one Traps entry: both master gates are invisible to the run that executes
them).

## Residue — honest ledger

1. **The disclosure warns; it does not carry.** 22 behavioural gates remain
   unreachable from any configuration. PARKED as **P15**, priced, with the one
   designed road written down.
2. **`deepreason reason` never reads the operator's config file at all** —
   `preparation._config_for_profile` synthesises a fresh `Config` from the
   provider profile. Found here, PARKED as **P14**; a larger goal than this one.
3. **No live run.** Every claim is a compile-time or read-time property; a
   ladder launch would add cost without adding evidence.
4. **The map has no `manifest × scheduler` or `manifest × application` seam**
   and no `SUB-application.md` row in `INDEX.md` — yet this whole defect lives
   on that agreement. Recorded in `GOAL.md`; closing it was not this goal.

**Accepted does not mean true.** Everything above is read from the committed
record, two instruments, 79 committed manifests and 8 committed run configs.
