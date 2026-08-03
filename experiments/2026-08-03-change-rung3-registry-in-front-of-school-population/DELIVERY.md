# Delivered: rung 3, tranche A — the school-population registry (build only)
Branch: `claude/delivery-rungs-handover-m22sdy` @ `62b8c189` (pushed,
tree clean).

## What changed

`src/deepreason/capture/schools.py` gained a `SchoolPopulationBackend`
protocol, a `SchoolPopulationRegistry` class, and a
`DefaultSchoolPopulationBackend` — mirroring `verification/registry.py`'s
proven shape (named registration, fingerprint pinned at registration,
re-checked on resolve) — plus a module-level singleton,
`SCHOOL_POPULATION`, pre-populated with exactly one entry, `"default"`.
The default backend delegates unchanged to today's existing
`init_schools`/`roster`/`allocate`/`reseed` functions; a new test file
(`tests/test_school_population_registry.py`, 9 tests) proves this
delegation is byte-for-byte equivalent to calling the bare functions
directly, plus the registry's own mechanics (registration,
duplicate/unknown-name errors, fingerprint pinning). A new map document,
`docs/map/SEAM-schools-x-scheduler.md`, records the agreement — including
an explicit "What is deliberately absent" section — and `docs/map/CON-
schools.md`/`docs/map/SUB-scheduler.md` now reference it.

**This is Tranche A of rung 3, not the whole rung.** The full rung
(build the registry AND migrate every live call site AND prove a
full end-to-end determinism run) was split into two tranches during
`dr-spec-change`, per the handover's own explicit allowance ("a rung
may take several tranches," `docs/HANDOVER_2026-08-03.md`'s Executor
calibration section) — not an operator amendment, a pre-existing option
in the source document itself, exercised because the full scope was
right at the ~300-line guideline and included the live scheduler, the
single most sensitive file in the codebase. **Nothing live resolves
through the registry yet**: `scheduler/scheduler.py`, `capture/
ladder.py`, and `cli/main.py`'s `reseed` command all still call
`capture.schools`'s bare module functions directly, exactly as before
this tranche — proven by two checked claims in the new seam document
itself (`! grep -q "SCHOOL_POPULATION" src/deepreason/scheduler/
scheduler.py`, same for `capture/ladder.py`). Tranche B, not opened
here, is the call-site migration plus the full offline-no-provider-run
determinism test the operator's own words describe.

One mid-flight discovery: adding the registry's imports to `schools.py`
broke a THIRD map document's check (`docs/map/SEAM-manifest-x-
schools.md:179`, a closed-world assertion on that file's exact import
set). The invariant the check protects — `schools.py` can never reach
the manifest, the firewall, or `Config`'s type — held throughout; only
the literal enumerated set needed widening to include the six new,
harmless imports (`copy`, `typing`, `collections.abc`, `dataclasses`,
`deepreason.canonical`, `deepreason.ontology.frozen`). Fixed in the
same commit, with the check's exclusion assertion made MORE explicit
than before, not weaker.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Route: dr-change-orchestrator" | done | this whole tranche followed the workflow's phases |
| R2 | "school population... resolves through a named registry entry with the current behavior as the only, default entry" | **done-with-amendment** (Tranche-A-scoped) | the registry exists, is populated with exactly one proven-equivalent entry (S1-S4), but NO live caller resolves through it yet — that is Tranche B; VALIDATION.md's R2 sweep states this plainly |
| R3 | "Copy the proven shape from verification/registry.py" | done | `SchoolPopulationRegistry`/`SchoolPopulationBackend`/`SchoolPopulationRegistration` mirror `VerifierRegistry`/`VerifierBackend`/`VerifierRegistration` field-for-field, adapted for schools' four differently-shaped methods |
| R4 | "Map preflight will name the seams — read them BEFORE the subsystems" | done | SPEC.md's own preflight; CHECKLIST step 1 (seam document) landed before any code step, per rule 4c |
| R5 | "full gate 0 failed" | done | 3301 passed, 0 failed, isolated, reproduced twice; VALIDATION.md |
| R6 | "root sweep byte-identical" | done | 42 rows, 11 ERROR, byte-identical, reproduced twice; VALIDATION.md |
| R7 | "a determinism test proving a run's outputs are byte-identical before/after the registry" | **done-with-amendment** (Tranche-A-scoped) | S4 delivers a direct method-vs-bare-function equivalence proof (9 tests) — smaller-footprint than the full offline-run test R7's words describe, which needs a live call site to exist first (Tranche B); SPEC.md's own A2 records this choice explicitly |
| R8 | "Continue to run 3. Read Claude.md first then proceed." | done | session preflight re-run at this continuation's actual start, CLAUDE.md re-read fresh, before REQUEST.md's capture |

## Assumptions the operator may override

A1: the registry/protocol shape mirrors `verification/registry.py`
field-for-field, adapted for schools' four differently-shaped methods
(no single `verify`-equivalent entry point; the fingerprint re-check
lives inside `get()` instead of a separate call).
A2: Tranche A's determinism proof is the scoped equivalence test
described above, not the full end-to-end run R7 literally asks for —
that lands in Tranche B.
A3: rung 3 splits into at least two tranches (this SPEC.md covers
Tranche A only), per the handover's own "a rung may take several
tranches" allowance.

## Map delta

Changed: `docs/map/CON-schools.md`, `docs/map/SUB-scheduler.md` (header
cross-references), `docs/map/SEAM-manifest-x-schools.md` (Amendment 1's
widened check). Created: `docs/map/SEAM-schools-x-scheduler.md` (four
new checked claims: registry existence, two deliberate-absence checks
for `scheduler.py`/`capture/ladder.py`, one single-backend-count check).
New checks: 5 total (4 new in the seam document, 1 strengthened in
`SEAM-manifest-x-schools.md`).

Left stale (advisory `--stale`, all dismissed in VALIDATION.md with
reasons): `CON-authority.md`, `CON-run-identity.md`, `INV-frozen-
surfaces.md`, `SEAM-bridge-x-manifest.md`, `SEAM-llm-x-manifest.md`,
`SEAM-manifest-x-schools.md`, `SUB-manifest.md` (all rung 2's own
commits, already resolved there); `SEAM-harness-x-verification.md`,
`SUB-verification.md` (an unrelated, pre-existing commit). One worth
naming explicitly: `SUB-periphery.md` — a pre-existing `Owns:` overlap
with `CON-schools.md` on `capture/schools.py` (both already listed it
before this tranche); its own checks on that file's function names
re-verified clean by the full gate.

## Parked (not done, not promised)

See `PARKED.md`. Summary: Tranche B (call-site migration — `scheduler.py`
definite, `capture/ladder.py`/`cli/main.py`'s `reseed` plausible,
`report.py`/`cli/main.py`'s read-only display probably not — SPEC.md's
own Q3, undecided here on purpose) and the full end-to-end determinism
test it needs; rung 5's second-backend work; the new seam document's
missing `Sweep:` header; the pre-existing `CON-schools.md`/`SUB-
periphery.md` `Owns:` overlap, noticed but not resolved.

Rung 3's remainder (Tranche B) is not opened here — the operator's call.
