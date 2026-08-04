# Validation for: rung 4 — every run records which modules built it

Run 2026-08-04 against branch head `6b79df7f`, tranche base `75783d11`.

## Verdict: **FAIL**

Everything green except one thing, and it is not a green-able one: the
new typed payload has **no clause in `Event._process_payload_contract`**,
which every other typed payload has. `docs/map/SUB-ontology.md:81` states
the requirement in its own change recipe — "attach a new typed process
payload to events | a new optional field on `Event` with `exclude_if`,
**plus a clause in `Event._process_payload_contract`**" — and this tranche
did the first half only. Detail in *FAIL detail* below. Per this phase's
contract nothing here was patched; it routes back to `dr-plan-steps`.

## Acceptance checks

**S1 (R1, R12) — route through `dr-change-orchestrator`, phase by phase.**
`ls experiments/2026-08-04-change-rung4-module-fingerprints/` ->
`REQUEST.md SPEC.md CHECKLIST.md PARKED.md VALIDATION.md`, created in
phase order across 13 commits. **PASS**

**S2 (R2, R3, M3, M4) — a fingerprint from the registered population
backend reaches the record on an ORDINARY run.**
`tests/test_module_fingerprints.py::test_an_ordinary_run_records_the_population_backend`
asserts a mock-endpoint `Scheduler` run carries the backend fingerprint
with `not any(e.capability is not None ...)`, and that the recorded
mapping equals `SCHOOL_POPULATION.fingerprint("default")`. Companion
`test_a_run_with_no_schools_still_records_which_module_built_it` covers
`N_SCHOOLS=0`. 18 passed. **PASS**

**S3 (R8, C12) — the READER lands before the writer; absence is valid.**
`verify_root` on three committed roots spanning all three census arms
(v6 / raises / no-manifest), canonical JSON sorted keys:

    sha256 BEFORE field: 62614bfcdbf494b2f3997c363a9a83ce024307ebc4718cbdea2ebeb16ac11f67
    sha256  AFTER field: 62614bfcdbf494b2f3997c363a9a83ce024307ebc4718cbdea2ebeb16ac11f67
    sha256  AFTER appender: 62614bfcdbf494b2f3997c363a9a83ce024307ebc4718cbdea2ebeb16ac11f67

Plus `test_every_committed_root_reads_as_having_no_module_fingerprints`
over all 31 openable roots. The reader was committed at step 2/4, the
`Event` field at step 5-8, the writer not until step 12. **PASS**

**S4 (R9) — full gate.**

    3321 passed, 7 skipped in 570.38s (0:09:30)
    rc=0

**PASS**

**S5 (R10, C13) — root sweep byte-identical.**

    SWEEP COMPLETE: 42 roots
    EMPTY DIFF - byte-identical
    rows: 42  ERROR: 11
    sha256 before: 9c092414321e12b97f631b59b98aa007e9505a289014a38c3a57b5bd9e050cd2
    sha256 after : 9c092414321e12b97f631b59b98aa007e9505a289014a38c3a57b5bd9e050cd2

Run with `tools/root_sweep.py` UNCHANGED. **PASS**

**S6 (R10, C13) — sweep probe, separate commit, no `src/` file.**
Probe commit `6b79df7f`; `git show --stat` lists `tools/root_sweep.py`
and `CHECKLIST.md`, and **0 `src/` files**. Own before/after capture on
an unchanged tree byte-identical (`sha 6d6c3366...a74fd525` both).
**PASS**

**S7 (R4, R5, R6, C10) — frozen-surface diff.**

    git diff --stat 75783d11..HEAD -- capabilities/state.py harness.py \
      invariants.py run_manifest.py qualification.py
     src/deepreason/harness.py | 25 +++++++++++++++++++++++++
     1 file changed, 25 insertions(+)

The four unauthorized surfaces are EMPTY. `harness.py` is non-empty and
is covered by S7's own alternative accept — the operator's approving
words, REQUEST.md Amendment 4 / R18. `config.py`, `verification/` and
`llm/firewall.py` also untouched. **PASS**

**S8 (C9) — FULL `docs_verify` before each `src/`-touching commit.**
Run in full mode (never `--fast`) before the step-2, step-8, step-11 and
step-18 commits. The full mode earned its cost: it caught two
PRE-EXISTING map checks (`SEAM-scheduler-x-workflow.md:80`,
`SUB-scheduler.md:200`) that `--fast` would have served from cache.
**PASS**

**S9 (R16, M5) — no new typed channel, so no `report.py` entry owed.**

    Rule members at tranche base: 15
    Rule members now            : 15
    new Rule members            : NONE
    (verification/ untouched)

R16 satisfied by its own "or not exist yet". **PASS**

**S10 (R17, D1-D8) — the approved design is what got built.**

    src/deepreason/harness.py             |  25 ++
    src/deepreason/module_events.py       | 105 ++++
    src/deepreason/ontology/event.py      |   4 ++
    src/deepreason/scheduler/scheduler.py |  57 ++++
    4 files changed, 191 insertions(+)

No `config.py`, `run_manifest.py` or `qualification.py` hunk: Options A
and C are closed as R17 requires. **PASS** — with the budget note under
*Deviations* below.

**S11 (R18, D6) — the `harness.py` diff is the declared hunks only.**

    functions ADDED  : ['record_module_fingerprints']
    functions CHANGED: ['_commit']
    functions REMOVED: []
      _apply_event       byte-identical to tranche base: True
      _ensure_writable   byte-identical to tranche base: True
      _reset             byte-identical to tranche base: True
      _adjudicate        byte-identical to tranche base: True

The operator's two explicit exclusions hold byte-identically. **PASS** —
with the declared three-hunks-not-two correction under *Deviations*.

**S12 (R20, C13, D8) — the probe READS the new observable.**

    modules= distribution over openable roots:  31 modules=-
    MUTATED:                                    31 modules=MUTANT
    changed rows vs baseline capture: 31

Absence proven tolerated by an instrument that looks, and the probe
mutation-proved non-vacuous. **PASS**

**S13 (D9, R9) — predicted fixture drift bounded to counts, not content.**
**PARTIAL — recorded honestly rather than claimed.** Of the six tests
that moved: three were count/position assertions as D9 predicted; two
were REAL DEFECTS escalated to SPEC.md as D7a/D7b and fixed in code (both
then passed UNEDITED, which is the proof they were defects and not
fixtures); one, `test_school_population_determinism`, was a CONTENT test
that moved *because the change works* — it compares the real registry
against a substitute backend whose fingerprints should now differ.
D9's prediction was too narrow. See *Deviations*.

## Full gate

    3321 passed, 7 skipped in 570.38s (0:09:30)   : PASS

Pre-writer baseline was 3303 passed; +18 are this tranche's new tests. No
test deleted, none weakened. C5's known flake did not fire.

## Record-behavior preservation

- `experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752` (v6): unchanged
- `experiments/bronze_feedback_v1_superseded_2026-07-14/observe_only` (raises `UnsupportedRunManifestVersionError`): unchanged
- `experiments/bronze_flat_2026-07-13/deepseek-v4-pro` (no manifest): unchanged
- All 42 sweep roots: unchanged (`valid`, `epistemic_checks_passed`, `att`, blindness count)

## Map

    docs_verify [full]: 50 documents, 805 checks, 4 workers -> 0 failed  : PASS
    docs_verify --audit: 0 finding(s)                                    : PASS
    docs_verify --links: 0 dangling reference(s), 50 document(s)         : PASS
    docs_verify --coverage: 6 seams swept, 15 without a Sweep: header,
                            0 finding(s)                                 : PASS

**new checks added by this change:** two, both at column 0 —
`CON-schools.md` (a mock-endpoint run's recorded fingerprint equals the
registry's pinned one) and `SEAM-schools-x-scheduler.md` (the stamp does
not fire at construction, fires once per `run` under `cycles > 0`, and
lands after workflow recovery). `SEAM-schools-x-scheduler.md`'s
`active_backend()` count moved 2 -> 3.

**record observables added vs sweep probes:** one observable —
`Event.module_fingerprints` / `module-fingerprints.v1` — probed by
`tools/root_sweep.py`'s `modules=` column in its own separate commit
`6b79df7f`. C13 satisfied.

**docs_verify --stale: 23 documents.** Disposition of every one:

- **Attributable to this tranche, DISMISSED:** `SUB-harness.md`,
  `SUB-ontology.md`, `SUB-scheduler.md`, `SEAM-schools-x-scratch.md`.
  Their `Verified-at:` stamps were deliberately NOT advanced, because
  this tranche did not re-run those documents' full check sets — the
  skill permits advancing a stamp only if you did. Nothing they assert
  is false: the full run passes all 805 checks. The new behaviour is
  documented at the CONCEPT and SEAM level (`CON-schools`,
  `SEAM-schools-x-scheduler`), which is where the map's own
  seam-before-subsystem ordering rule puts it.
  **One exception is NOT dismissed — see FAIL detail: `SUB-ontology.md`
  turns out to assert a requirement this tranche did not meet.**
- **Pre-existing, not this tranche's:** `SUB-manifest.md` (rung 2
  commits `f642f980`, `9607f739`), `SUB-periphery.md` (rung 3 commits
  `c76eda34`, `697a551a`), `SUB-verification.md` (`2456da55`),
  `SUB-application.md` (`c76eda34`), and the remainder listed by
  `--stale`. All predate this tranche's base and belong to the rungs
  that touched them; recorded in PARKED.md rather than adopted here.

## Requirement sweep

| R | Demonstrated by |
|---|---|
| R1 (route via `dr-change-orchestrator`) | S1 — phase artifacts in order |
| R2 (modules stamp into the TYPED RECORD) | S2 — ordinary-run test, no capability |
| R3 (`CONTAINED_WORKER_SHA256` precedent) | Advisory per C8/C11. SHAPE adopted (`ModuleFingerprintV1`); LOCATION rejected with reasons (SPEC M3/D2). Deviation recorded in writing, not silent. |
| R4 (rides Config and typed log/object records) | **Partially superseded by R17.** The Config half is CLOSED by the operator's choice of Option B; the typed-log half is S2/S10. Recorded, not quietly dropped. |
| R5 (NEVER a new manifest field) | S7 — `run_manifest.py` empty diff |
| R6 (NEVER into the qualification subject digest) | S7 — `qualification.py` empty diff; no `Config` field added |
| R7 (DESIGN-AND-STOP if it needs the manifest) | Honoured: the tranche DID stop, and Amendment 4 resolved it |
| R8 (reader before writer, absence valid) | S3 — reader committed at steps 2-4, writer at step 12 |
| R9 (full gate) | S4 — 3321 passed, 0 failed |
| R10 (sweep byte-identical) | S5 + S12 — identical, and non-trivially so |
| R11 (one rung only) | Rungs 5-7 untouched; `VerifierRegistry`/`WORKLOADS` parked (P1) |
| R12 (proceed to dr-spec-change) | SPEC.md resolution appendix |
| R13 (verify Q5 against the real write path) | SPEC M1-M5, measured not reasoned |
| R14 (prefer zero frozen-surface contact) | Honoured as a preference: Option C was zero-contact, priced, and rejected on the record for not delivering R2; the operator chose B knowingly |
| R15 (DESIGN-AND-STOP; rung 2's approval not transitive) | Honoured — no appeal to rung 2's precedent; Amendment 4 is this tranche's own authorization |
| R16 (new channel lands report.py entry, or no channel) | S9 — no new `Rule`, no channel, `verification/` untouched |
| R17 (Option B approved) | S10 — no `config.py`/`run_manifest.py` hunk |
| R18 (narrow appender-only surface-2 touch) | S11 — `_apply_event` and well-formedness byte-identical |
| R19 (ledger then plan and proceed) | Amendment 4 committed before any spec/plan work |
| R20 (include the sweep probe) | S6 + S12 — probe exists, in its own commit |

Every R is demonstrated or explicitly accounted for. No R is deferred
without the operator's words.

## Assumptions carried

- **A1** — "registered modules" = `SCHOOL_POPULATION` only. NOT overridden
  by Amendment 4 (which was silent on SPEC.md's direct question), so the
  smallest reading stands. `VerifierRegistry` and `WORKLOADS` are parked
  (P1), not dropped. **The operator should confirm or widen this.**
- **A2** — the fingerprint rides an optional payload on an existing record
  rather than a new channel. Confirmed correct by R16/S9.
- **A3** — C13's rule adopted as written: a byte-identical sweep does not
  by itself prove absence-tolerance. Confirmed by S12's mutation.

## Deviations from SPEC.md, all declared in writing before the fact

1. **Three `harness.py` hunks, not the two D6 predicted.** `_commit`'s
   type annotation needs a module-level import. Declared in CHECKLIST
   step 9 before the commit. R18's exclusions still hold byte-identically.
2. **D7a / D7b — two placement corrections**, both escalated to SPEC.md
   before the code changed. The stamp moved `__init__` ->
   `run(cycles > 0)`, after workflow recovery.
3. **Budget overrun ~3x.** SPEC.md estimated "~40-60 lines of `src/`";
   actual 191 across four files. Under the 300-line stop condition, so no
   stop fired, but the estimate was wrong.
4. **D9's fixture-drift prediction was too narrow** — see S13.

## FAIL detail

**Check:** `docs/map/SUB-ontology.md:81`, the map's own recipe for this
exact change: *"attach a new typed process payload to events | a new
optional field on `Event` with `exclude_if`, plus a clause in
`Event._process_payload_contract`"*. And `:140` — *"Rule and typed
payload are mutually implying."*

**What the tree does:** `Event._process_payload_contract`
(`ontology/event.py:434`) binds every other typed payload to its Rule and
constrains its inputs/outputs — `scratch`, `bridge`, `conjecture_turn`,
`control`, `capability`, five clauses. `module_fingerprints` has none. It
is the only typed payload on `Event` without one.

**Real output demonstrating the gap:**

    An Event pairing the fingerprint payload with Rule.CONJ was ACCEPTED: Rule.CONJ
    ...and with unconstrained inputs: []

So a forged or `model_copy`-mutated event can carry a module-fingerprint
payload on ANY rule, with inputs that do not describe it — while the
appender's own contract is `Rule.MEASURE` with
`inputs=[schema, digest]`. Nothing in the record would refuse it, and the
reader would report it as a genuine stamp.

**Why this is a FAIL and not a nit.** The gap is invisible to every
instrument that passed: the gate is green, all 805 map checks pass, the
sweep is byte-identical, and no committed root moves — because no
existing test constructs such an event. It is precisely the class of
defect `_process_payload_contract` exists to prevent, and the class the
map warned about in advance. Shipping it would leave the one new typed
payload as the only unfenced one.

**Suspected step:** step 5 (the `Event` field). CHECKLIST step 5 said
"Nothing else in that file", which was correct about not over-reaching
and wrong about what the payload owed. The plan never had a step for the
contract clause because SPEC.md D3 did not name one.

**Not fixed here.** Validation does not patch what it validates. Routes
to `dr-plan-steps` for a partial re-plan: one step adding the
mutual-implication clause plus its regression test, then re-run the gate,
`docs_verify`, and this validation.
