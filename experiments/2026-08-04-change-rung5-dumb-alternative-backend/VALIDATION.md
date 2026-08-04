# Validation for: rung 5 — one deliberately dumb alternative, swapped in

Run 2026-08-04 against branch head `47a6cc35`, tranche base `494a8213`
(rung 4's close).

## Verdict: **PASS** for the offline work, with the R13 stop OUTSTANDING

Every acceptance check for the offline module work passes. The live A/B
is NOT validated and NOT attempted: R13 makes stopping before it
mandatory, and the tranche stops there by design, not by failure.

## Acceptance checks

**S1 (R1, R11) — routed through `dr-change-orchestrator`.** REQUEST.md →
SPEC.md → CHECKLIST.md → steps → this file, in phase order. **PASS**

**S2 (R3, R4, C9) — a second backend under a NEW name.**
`SCHOOL_POPULATION.ids() == ("default", "round-robin")`;
`fingerprint_is_pinned("round-robin")` true; `register` still refuses to
displace either name. **PASS**

**S3 (R3, M2a) — allocation deterministic from (log, config).** Repeat
calls agree, a fresh instance agrees, and the call-order variant
demonstrably fails the same comparison. **PASS**

**S4 (R5, M3) — scoped selection, no `Config`.**

    outside scope : DefaultSchoolPopulationBackend
    inside scope  : RoundRobinSchoolPopulationBackend
    after scope   : DefaultSchoolPopulationBackend
    unknown name  : refused, selection untouched
    after raise   : DefaultSchoolPopulationBackend

`schools.py` imports neither `deepreason.config` nor `os`, asserted by a
map check. **PASS**

**S5 (R5, R10, A4) — offline run completes and verifies.**
`verify_root(root)["violations"] == []` with `stats["events"] > 0`.
Epistemic quality deliberately not asserted. **PASS**

**S6 (R5) — the root records its own builder.** Alternative run reports
`module_id == "round-robin"`, default run `"default"`, digests differ.
**PASS**

**S7 (R6, A3, C11) — the default path is unchanged.**
`git diff --stat tests/test_school_population_determinism.py` is EMPTY
and the file passes. **PASS**

**S8 (R8) — full gate.**

    3338 passed, 7 skipped in 592.79s (0:09:52)
    rc=0

**PASS**

**S9 (R9) — root sweep byte-identical.**

    42 rows, 11 ERROR, EMPTY DIFF
    sha256: 6d6c3366c821d4555a8a4866c6a208c2b5d08db704e8f13c1611c7c5a74fd525

Unchanged from rung 4's committed 5-field baseline. **PASS**

**S10 (C8) — FULL `docs_verify` + `--audit`.**

    docs_verify [full]: 0 failed
    docs_verify --audit: 0 finding(s)

**PASS**

**S11 (C10) — the seam's `active_backend()` counts unmoved.** This
tranche adds no call site; it changes what the existing ones resolve to.
The three count checks pass inside the full `docs_verify`. **PASS**

**S12 (C12) — no new observable, so no new probe owed.**
`git diff 494a8213..HEAD -- tools/` is EMPTY; no `Event` field, no record
type, no `verify_root` finding. Rung 5 is the first CONSUMER of rung 4's
observable, and rung 4's `modules=` probe already reads it. **PASS**

**S13 (R2, R7, R13) — the credential stop.** NOT YET DISCHARGED; it is
the tranche's final step and belongs to delivery. No credential file was
created, read, or committed; no live run was started; `git log -p` for
this tranche contains no key material. **PASS on the prohibitions,
OUTSTANDING on the ask.**

## Full gate

    3338 passed, 7 skipped in 592.79s (0:09:52)   : PASS

Rung 4 closed at 3323; +15 are this tranche's new tests. No test deleted.
One test UPDATED — see *Deviations*. C5's known flake did not fire.

## Record-behavior preservation

No committed root moved: the 42-root sweep is byte-identical, and the
tranche touches no reader, no validator and no frozen surface.

## Frozen-surface diff (4a2)

    git diff --stat 494a8213..HEAD -- capabilities/state.py harness.py \
      invariants.py run_manifest.py qualification.py verification/ config.py
    (empty)

**Empty on ALL five surfaces plus `verification/` and `config.py`.**
Unlike rung 4, this tranche holds no operator authorization for any
frozen surface and needed none. Total `src/` change: one file,
`capture/schools.py`, 69 insertions and 1 deletion.

## Map

    docs_verify [full]:      0 failed                                  : PASS
    docs_verify --audit:     0 finding(s)                              : PASS
    docs_verify --links:     0 dangling, 50 documents                  : PASS
    docs_verify --coverage:  6 seams swept, 15 without Sweep:, 0 finds : PASS

**new checks added by this change:** three at column 0 in
`SEAM-schools-x-scheduler` — the two-entry registry identity, the
round-robin determinism/difference proof, and the scoped-selection
proof (no `Config`, no `os`, select/restore/refuse).

**map documents changed:** `SEAM-schools-x-scheduler.md` (its "no second
backend" section was this change's own precondition and is rewritten; its
single-entry check updated rather than deleted; its identity check widened
to name both backends; its NAME row extended), `CON-schools.md` (two new
rows), `SEAM-manifest-x-schools.md` (its EXACT import-set pin gains
`contextlib`).

**A correction made in passing:** `SEAM-schools-x-scheduler`'s fingerprint
row still said the stamp fires "at construction". Rung 4 moved it to
`run(cycles > 0)` and added a check asserting it does NOT fire at
construction — two lines below a sentence saying it does. Rung 5 fixed the
prose. Recorded because it shows a check can pass while the prose beside
it is false.

**docs_verify --stale: 23 documents.** This tranche's entries —
`CON-schools.md`, `SEAM-schools-x-scheduler.md`,
`SEAM-manifest-x-schools.md`, `SUB-scheduler.md` — are DISMISSED on the
same ground as rung 4's: `Verified-at:` stamps were not advanced because
this tranche did not re-run those documents' full check sets, and nothing
they assert is false (the full run passes). The remaining entries predate
this tranche.

**record observables added vs sweep probes:** none added; rung 4's probe
covers the one this rung consumes.

## Requirement sweep

| R | Demonstrated by |
|---|---|
| R1 | S1 — phase artifacts in order |
| R2 | S13 — no credential file created, read or committed |
| R3 | S2, S3 — round-robin backend, deterministic, genuinely different |
| R4 | S2 — registered as `"round-robin"`, never `"default"` |
| R5 | S5, S6 — the offline run completes, verifies, and names its builder |
| R6 | S7 — the determinism instrument passes UNMODIFIED |
| R7 | not exercised; the live A/B is optional and R13 supersedes it here |
| R8 | S8 — 3338 passed, 0 failed |
| R9 | S9 — sweep byte-identical |
| R10 | S5 — `verify_root` violations empty on the alternative's root |
| R11 | S1 |
| R12 | the offline work is complete before the stop |
| R13 | **OUTSTANDING BY DESIGN** — discharged by delivery's credential ask |

No requirement is not-done. R7 is not-exercised rather than deferred: the
handover makes it optional and the operator's R13 makes stopping
mandatory, so the two agree.

## Assumptions carried

- **A1** — the alternative differs in `allocate` ONLY; the other four
  operations delegate. Pinned by a test.
- **A2** — the offline run root is built in `tmp_path` and NOT committed,
  so the sweep census stays at 42 and the baseline does not move. The root
  is re-created and re-verified on every gate run.
- **A3** — R6 proven as "a run that does not select the alternative is
  unchanged", because rung 4 made the literal reading false for any
  non-default backend.
- **A4** — "completes and verifies" is judged on completion plus empty
  `verify_root` violations; epistemic quality is not judged.

## Deviations

1. **One existing test updated, unpredicted by SPEC.md** (recorded as M6
   during execution, before the edit).
   `test_module_singleton_holds_exactly_one_default_backend` pinned
   `ids() == ("default",)` — the state rung 5 exists to change, and the
   seam document said so in the same words. Updated to the claim that
   survives: `"default"` is still registered, still the default
   implementation, and still what an unscoped `active_backend()` resolves
   to. That checks strictly MORE than the assertion it replaced, because
   it now also pins that an alternative does not displace the default.
   **Two tranches running, the fixture-drift forecast has been the weakest
   part of both specs.**
2. **A claim the fixture cannot support, recorded rather than asserted.**
   The offline runs do NOT diverge in conjecturer provenance at 2 or 6
   cycles — both produce school-0 conjectures, because a mock endpoint
   returns one candidate. The divergence this fixture can see is in how
   much work each run does (20 vs 23 events at 2 cycles, 30 vs 42 at 6).
   The test asserts that and says why in its docstring.
3. **Budget:** 69 `src/` lines against an estimated 60-90 — inside the
   estimate, unlike rung 4's 3.5x overrun.

## Verdict: **PASS** (offline work). R13's stop is outstanding and is
delivery's first obligation.
