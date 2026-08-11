# Delivered: sub-tranche (i) — error-code catalog (S1+S2)

Branch: `claude/operator-program-seven-items-zpur05` @ `0dc76741f`
(pushed, tree clean)

## What changed

A new file, `src/deepreason/error_catalog.py`, gives 44 typed error
codes (every `QUALIFICATION_*` and `DOCTOR_*` code in the codebase — the
qualification-failure codes the operator's complaint was about) a
plain-language summary, an explanation of what the failure means, and
a concrete next action. Nothing about the underlying codes changed:
the catalog only reads existing `.code` strings, never edits a raise
site. Two ways to reach it: a new `deepreason explain-error CODE`
command for looking one up directly, and an automatic addition to the
existing qualification-failure printout, so a caller who hits a
qualification error sees the plain-language gloss immediately, right
next to the raw code, without asking for it. `tests/
test_error_catalog.py` proves every catalog entry's key is a real,
byte-identical raise-site code string — no entry can silently drift
from the code it describes.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "per role with added error messages" | done-with-resolution (Amendment 1: "message only") | commit `5bedb07fc`, VALIDATION_i.md S1/S2 |
| R2 | "fully kitted human readable surface" | done-with-assumption A1 (44/572 codes; residue explicit, not silent) | commit `287b27f5a`, VALIDATION_i.md S2 |

## Assumptions the operator may override

A1: "fully kitted" is read as every typed error code across the whole
public surface (not just qualification) — this sub-tranche covers the
44 most directly relevant (qualification/doctor); the other ~528 are
queued, not silently declared done (see Parked below).
A2: the catalog is purely additive — confirmed by an empty
frozen-surface diff; nothing in `qualification.py` was touched.

## Map delta

changed: none. created: none (no `docs/map/` document — `cli/main.py`
and the new `error_catalog.py` have no dedicated map document, per
CHECKLIST_i.md's header note). new checks: 0 (behavior proven by
`tests/test_error_catalog.py`, not a `docs_verify` check — this file
sits outside the map's own scope).
left stale: none — `docs_verify --stale` reports 0.

## Errata

errata: none. One internal inconsistency was found and fixed in this
tranche's OWN still-open `SPEC.md` (its S2 accept criterion cited an
example code, `ADMISSION_DOSSIER_INVALID`, that predated the same
document's later scope-narrowing to 44 QUALIFICATION_*/DOCTOR_* entries
— corrected in place since this tranche is not yet closed, per
`VALIDATION_i.md`'s finding). This is a tranche-internal working
document, not one of the documents `docs/ERRATA.md`'s own scope note
names (handovers, map, RESULTS, the harness spec series) — no
`docs/ERRATA.md` entry is owed for it.

## Parked (not done, not promised)

`PARKED.md` Residue 1 (already recorded, confirmed still accurate at
delivery): ~528 of 572 typed error codes remain uncataloged, grouped by
family (BRIDGE_* 121, TERMINAL_* 59, SCRATCH_* 54, JOLT_* 43, and
~36 more families) — each is its own bounded future tranche, never one
giant catalog-everything pass. Ready-to-send prompt in `PARKED.md`.

recommended next: sub-tranche (ii), the schema-first intake tool (S3,
already spec'd, "default for everyone" per Amendment 1) — already
in progress in this same tranche directory.
