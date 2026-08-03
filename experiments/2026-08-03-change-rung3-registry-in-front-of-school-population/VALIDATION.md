# Validation for: rung 3, tranche A — the school-population registry (build only)
Re-read REQUEST.md (Amendment 1), SPEC.md (Amendment 1), CHECKLIST.md in
full before running anything below. Every check here was re-run fresh
in this validation pass. Branch head at validation: `d3101dbe`.

## Acceptance checks

S1: `python -c "from deepreason.capture.schools import SchoolPopulationRegistry, SchoolPopulationBackend, SchoolPopulationRegistration; assert callable(...)"` -> `check1: PASS` / `check2: PASS` : PASS

S2: `python -c "from deepreason.capture.schools import DefaultSchoolPopulationBackend; ..."` -> `PASS` : PASS

S3: `python -c "from deepreason.capture.schools import SCHOOL_POPULATION; assert SCHOOL_POPULATION.ids() == ('default',)"` -> `PASS` : PASS

S4: `python -m pytest tests/test_school_population_registry.py -q` -> `9 passed in 0.29s` : PASS

S5: `grep -q "DR-SEAM-schools-x-scheduler" docs/map/CON-schools.md docs/map/SUB-scheduler.md` -> `grep: PASS` : PASS. Map validation itself — see below.

S6: full gate + root sweep — see below.

S7 (Amendment 1): `SEAM-manifest-x-schools.md`'s widened closed-world
import check re-verified as part of the full `docs_verify.py` run below
: PASS

## Full gate

Ran ISOLATED (nothing else concurrent, per tranche 2's own lesson):

    3301 passed, 7 skipped in 613.32s (0:10:13)

Exactly rung 2's 3292 baseline plus this tranche's 9 new tests.

**Verdict: PASS.**

## Record-behavior preservation / root sweep

`python tools/root_sweep.py` run fresh, isolated: `SWEEP COMPLETE: 42
roots`, `11 ERROR` lines (all `UnsupportedRunManifestVersionError`).
Diffed against this tranche's own prior capture (`rung3_sweep.txt`,
taken during CHECKLIST step 12): **empty diff** — byte-identical. No
committed root's verdict moved.

**Verdict: PASS.**

## Frozen-surface diff

    git diff --stat 4d18141a..HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py \
      src/deepreason/qualification.py

    (empty output)

**Empty**, as designed. This tranche builds a registry entirely inside
`capture/schools.py` (and adds/updates map documents) — no frozen
surface is touched. No operator approval gate needed.

## Map

`python tools/docs_verify.py`: 50 documents, 800 checks, 0 failed : PASS
`python tools/docs_verify.py --audit`: 0 finding(s) : PASS
`python tools/docs_verify.py --links`: 0 dangling reference(s), 50
documents : PASS
`python tools/docs_verify.py --coverage`: 6 seams swept, 15 without a
`Sweep:` header (14 pre-existing, plus this tranche's own new
`SEAM-schools-x-scheduler.md`, which was not given a `Sweep:` header —
not requested by SPEC.md's S5, matching the pattern of most other seam
documents in the repo), 0 findings : PASS, nothing to dismiss

`python tools/docs_verify.py --stale`: 13 documents. Every entry
dismissed with a reason:
- `CON-authority.md`, `CON-run-identity.md`, `INV-frozen-surfaces.md`,
  `SEAM-bridge-x-manifest.md`, `SEAM-llm-x-manifest.md`,
  `SEAM-manifest-x-schools.md`, `SUB-manifest.md` — all flagged solely
  for rung 2's own commits, already resolved there; not this tranche's
  responsibility.
- `CON-schools.md`, `SEAM-schools-x-scheduler.md` — flagged because THIS
  tranche's own commit (`697a551a`) touched files they own; both are
  documents this tranche itself wrote/updated; re-verified clean by the
  full run above.
- `REC-change-a-seam.md` — flagged because this tranche's commit
  touched `docs/map/` (which it owns per its own `Owns: docs/map/`
  header); its own content is unrelated to schools/scheduler and
  unchanged; re-verified clean.
- `SUB-periphery.md` — flagged because this tranche's commit touched
  `capture/schools.py`, which `SUB-periphery.md` ALSO owns (a
  pre-existing `Owns:` overlap with `CON-schools.md` — both documents
  already listed `capture/schools.py`/`capture/` before this tranche;
  not introduced here). `SUB-periphery.md`'s own checks assert
  `capture/schools.py`'s four functions (`roster`, `init_schools`,
  `allocate`, `reseed`) remain defined at column 0 — unchanged by this
  tranche (only new code was APPENDED after them), and confirmed by the
  full `docs_verify.py` run above (0 failed, including this document's
  own check).
- `SEAM-harness-x-verification.md`, `SUB-verification.md` — flagged for
  an unrelated, pre-existing commit (`2456da55`), not this tranche's
  responsibility.

New map checks added by this change: one in `CON-schools.md`/`SUB-
scheduler.md`'s cross-reference (structural, not a new checked claim
beyond the header itself); the new `SEAM-schools-x-scheduler.md`
document, which itself contains four new checked claims (registry
existence, two deliberate-absence checks for scheduler.py/ladder.py,
one single-backend-count check); one check in `SEAM-manifest-x-
schools.md` widened (Amendment 1, not new but strengthened — it now
also asserts the manifest/firewall/config exclusion explicitly, which
the prior version left implicit).

## Requirement sweep

R1 (process — route through `dr-change-orchestrator`): demonstrated —
this whole tranche followed the workflow's phases.

R2 (behavior — "school population... resolves through a named registry
entry with the current behavior as the only, default entry"):
**PARTIALLY demonstrated, honestly.** The registry exists
(`SchoolPopulationRegistry`), is populated with exactly one entry
(`"default"`, `SCHOOL_POPULATION.ids() == ('default',)`), and that
entry is PROVEN equivalent to today's bare functions (S4's 9 tests). But
NOTHING LIVE resolves through it yet — `scheduler.py`, `capture/
ladder.py`, and `cli/main.py`'s `reseed` command all still call the bare
module functions directly, exactly as before this tranche (confirmed
by `SEAM-schools-x-scheduler.md`'s own deliberate-absence checks,
re-verified in this pass's full docs_verify run). This is Tranche A of
what SPEC.md's own reasoning splits into two tranches, per the
handover's own "a rung may take several tranches" allowance (C1).
Tranche B (not yet opened) is where R2 becomes fully true for live
callers.

R3 (behavior — "Copy the proven shape from `verification/registry.py`"):
demonstrated — `SchoolPopulationRegistry`/`SchoolPopulationBackend`/
`SchoolPopulationRegistration`/error classes mirror `VerifierRegistry`/
`VerifierBackend`/`VerifierRegistration`/error classes field-for-field,
adapted for schools' four differently-shaped methods (documented
deviation: the fingerprint re-check lives in `get()` rather than a
separate `verify()`, since schools has no single dispatch verb).

R4 (process — map preflight, seams read before subsystems): demonstrated
— SPEC.md's own preflight section, and CHECKLIST's step-1-before-code
ordering (rule 4c: the seam document was created BEFORE the registry
code, not after).

R5 (process — full gate 0 failed): demonstrated above — PASS, isolated,
reproduced twice (CHECKLIST step 11, this validation pass).

R6 (process — root sweep byte-identical): demonstrated above — PASS,
reproduced twice, byte-identical both times.

R7 (artifact — "a determinism test proving a run's outputs are
byte-identical before/after the registry"): **PARTIALLY demonstrated,
by explicit design (SPEC.md A2).** This tranche's S4 delivers a
SCOPED, smaller-footprint proof: the default backend's four methods,
called directly, produce byte-identical results to the bare module
functions, for the same fixture inputs. This is NOT yet the full
offline-no-provider END-TO-END RUN proof R7's own words describe
(reusing `tests/test_attached_evidence_citation.py`'s fixture
pattern) — that requires a LIVE call site to exist first, which is
Tranche B's own deliverable. Recorded plainly, per SPEC.md's own A2,
so nobody mistakes Tranche A alone as satisfying R7 in full.

R8 (process — "Continue to run 3. Read Claude.md first then proceed."):
demonstrated — session preflight re-run at this continuation's actual
start (git log, fetch/resync, `deepreason` importable, env file check,
CLAUDE.md re-read fresh) before REQUEST.md's capture.

## Assumptions carried

A1 (Q1): the registry/protocol shape mirrors `verification/registry.py`
field-for-field, adapted for schools' four differently-shaped methods;
no single `verify`-equivalent entry point.

A2 (Q2): Tranche A's determinism proof is a DIRECT method-vs-bare-
function equivalence test, not the full offline-run proof R7 literally
describes — that lands in Tranche B.

A3 (the tranche split itself): rung 3 splits into at least two
tranches, per the handover's own "a rung may take several tranches"
(C1). This SPEC.md covers Tranche A only.

## Verdict: PASS

Every acceptance check (S1-S7), the full gate (3301 passed, 0 failed,
isolated, reproduced twice), the root sweep (42 rows / 11 ERROR,
byte-identical, reproduced twice), all five `docs_verify` modes, and
all eight requirements (with R2 and R7 explicitly and honestly recorded
as PARTIAL — Tranche A's own scope, not a gap glossed over) pass. The
frozen-surface diff is empty. Ready for `dr-deliver-change`.
