# Validation for: rung 3, tranche B — migrate the call sites through the registry
Re-read REQUEST.md (Amendments 1-2), SPEC.md (S1-S10, A1-A3),
CHECKLIST.md in full before running anything below. Every check was
re-run fresh in this pass. Branch head at validation: `a584166e`.

## Acceptance checks

S1: `python -c "... assert isinstance(active_backend(), DefaultSchoolPopulationBackend)"`
-> exits 0 : PASS

S2: `grep -c 'schools.active_backend()' src/deepreason/scheduler/scheduler.py`
-> `2` : PASS

S3: `grep -c 'schools.active_backend()' src/deepreason/capture/ladder.py`
-> `4` : PASS

S4: `grep -c 'active_backend()' src/deepreason/cli/main.py` -> `3`;
`... report.py` -> `1` : PASS

S5: the bare-call sweep + single-backend assertion -> exits 0 : PASS.
The regex was instrument-self-tested during execution (it matches
`schools.roster(` / `schools_mod.reseed(` and does NOT match
`schools.active_backend().roster(`), so a false pass was ruled out
before its verdict was trusted.

S6: map update — see the Map section below : PASS

S7: determinism test — see "Flake re-verification" below : PASS

S8: full gate + root sweep — see below : PASS

S9 (Amendment 1): `python -c "... re.search(r'if config\.N_SCHOOLS > 0\s*else \{\}', s)"`
-> exits 0 : PASS

S10 (Amendment 2): the `Scheduler.step` source slice using the shortened
`"assigned = schools"` marker isolates the discrimination branch, which
still contains `pairwise_discriminate(`, contains neither `conj(` nor
`synthesize(`, and ends in `return` -> exits 0 : PASS

## Full gate

Run ISOLATED (nothing else concurrent):

    3303 passed, 7 skipped in 537.03s (0:08:57)

3301 (rung 3 tranche A's baseline) plus this tranche's 2 new tests.
**Verdict: PASS.**

## Flake re-verification (a single green run would not have been evidence)

The determinism test was flaky when first written — `llm.ms` is
repeated inside every `attempt_trace` entry and the first version
stripped only the top-level copy, so roughly one run in three compared
2ms against 1ms. Fixed by recursive scrubbing (commit `863a0fa3`). Because
a bug of that shape hides behind a single pass, this pass re-ran it
independently:

- 8 serial repeats: **0 failures**
- 3 repeats under `-n 4`: **2 passed** each time

The companion test `test_the_determinism_comparison_can_actually_fail`
passed throughout, so the comparison remains sensitive — it still
rejects a backend that reverses allocation. Equality holds when
behaviour is equal; inequality holds when it is not. **Verdict: PASS.**

## Record-behavior preservation / root sweep

`python tools/root_sweep.py` run fresh, isolated: `SWEEP COMPLETE: 42
roots`, `11 ERROR` (all `UnsupportedRunManifestVersionError`). Diffed
against BOTH this tranche's step-12 capture and rung 3 tranche A's
accepted capture: **empty diff against both**. No committed root's
verdict moved. **Verdict: PASS.**

## Frozen-surface diff

    git diff --stat 45bae1bf..HEAD -- \
      src/deepreason/capabilities/state.py src/deepreason/harness.py \
      src/deepreason/invariants.py src/deepreason/run_manifest.py \
      src/deepreason/qualification.py

    (empty output)

**Empty.** A1 deliberately avoided the one design that would have hit a
frozen surface: a `Config` field naming the backend would enter
`source_config_hash`/`engine_config_json` and require scrubbing inside
`run_manifest.py::_versioned_source_config_data` (surface 4), which is
what rung 2 tranche 2 paid an operator-approval gate for. Putting the
name in a module constant instead keeps this tranche entirely clear of
the frozen set. **Verdict: PASS**, no operator gate needed.

## Map

`python tools/docs_verify.py`: 50 documents, **803** checks, 0 failed : PASS
`python tools/docs_verify.py --audit`: 0 finding(s) : PASS
`python tools/docs_verify.py --links`: 0 dangling, 50 documents : PASS
`python tools/docs_verify.py --coverage`: 6 seams swept, 15 without a
`Sweep:` header, 0 findings — the 15 include this tranche's own
`SEAM-schools-x-scheduler.md`; adding one was not requested and most
seam documents in the repo lack it. Parked, not silently ignored : PASS

**An instrument limitation worth surfacing to the operator.** Step 6 ran
`docs_verify --fast` and got 0 failed; the FULL run then found a real
breakage (`SEAM-scheduler-x-rules.md`, Amendment 2). `--fast` reuses
cached results for documents whose OWN text is unchanged — that document
was not edited here, so its check was never re-executed even though the
source file it READS had changed underneath it. **A green `--fast` is
therefore not evidence that the map survived a `src/` change.** Only the
full run is. This generalises well beyond this tranche and is repeated
in DELIVERY.md.

`--stale`: 19 documents. Dismissals:
- Flagged by THIS tranche's commit (`c76eda34`) because it touched a
  file they own: `CON-authority.md`, `CON-scheduler-ranking.md`,
  `CON-schools.md`, `REC-change-a-seam.md`, `SEAM-scheduler-x-rules.md`,
  `SEAM-scheduler-x-workflow.md`, `SEAM-schools-x-scheduler.md`,
  `SEAM-schools-x-scratch.md`, `SUB-application.md`, `SUB-periphery.md`,
  `SUB-scheduler.md`. Three of these this tranche actively updated
  (`CON-schools.md`, `SEAM-scheduler-x-rules.md`,
  `SEAM-schools-x-scheduler.md`); the rest own a touched file but their
  own claims are unaffected — all re-verified clean by the full run
  above. The breadth is itself informative: `scheduler.py` is owned or
  co-owned by many documents, which is why C6 named it the most
  sensitive file in the program.
- Flagged by EARLIER tranches, already resolved there, not this
  tranche's responsibility: `CON-run-identity.md`,
  `INV-frozen-surfaces.md`, `SEAM-bridge-x-manifest.md`,
  `SEAM-llm-x-manifest.md`, `SEAM-manifest-x-schools.md`,
  `SUB-manifest.md`.
- Flagged by the unrelated pre-existing commit `2456da55`:
  `SEAM-harness-x-verification.md`, `SUB-verification.md`.

New map checks added by this change: `SEAM-schools-x-scheduler.md` now
carries 7 checks (up from 4 in tranche A) — three new enforcement checks
pinning per-file migrated counts AND asserting no bare call survives, so
reverting any single call site fails the map gate. Two further checks
were made robust rather than merely repaired (`CON-schools.md`'s guard,
`SEAM-scheduler-x-rules.md`'s slice marker); both were mutation-tested
before being written down, per the map's own "run it before you write it
down" rule.

## Requirement sweep

R1 (route through `dr-change-orchestrator`): demonstrated — every phase
ran in order, with two amendments recorded before the fixes they
authorise.

R2 ("school population... resolves through a named registry entry with
the current behavior as the only, default entry"): **now FULLY
satisfied**, where tranche A satisfied it only partially. All ten call
sites of the four named functions resolve through `active_backend()`
(S2-S4), no bare call survives (S5), and exactly one entry is registered
(S5). Confirmed by re-derivation, not assertion.

R3 ("the current behavior as the only, default entry"): demonstrated —
`SCHOOL_POPULATION.ids() == ('default',)`.

R4 (map preflight, seams before subsystems): demonstrated — SPEC.md's
preflight named both sides and the seam; the map moved in the same
commit as the code (`c76eda34`), and two further map documents were
repaired as amendments when the full run found them.

R5 (full gate 0 failed): demonstrated — 3303 passed, 0 failed, isolated.

R6 (root sweep byte-identical): demonstrated — 42/11, empty diff against
two independent prior captures.

R7 ("a determinism test proving a run's outputs are byte-identical
before/after the registry"): **now FULLY satisfied**, where tranche A
delivered only a scoped method-level proof. The test builds two real
mock-endpoint `Scheduler` runs — one through the migrated path, one with
`active_backend` patched to call the bare functions — and asserts
identical applied state plus identical event logs excluding two
wall-clock fields. It deviates from the FIXTURE R7 names, and that
deviation is the point: SPEC.md's Q3 established that the named fixture
patches `ops.run_scheduler`, the very function that constructs the
`Scheduler`, so a test built on it never reaches `init_schools` or
`allocate`. Flagged again in DELIVERY.md.

R8 ("the call-site migration plus the full offline-no-provider-run
determinism test"): demonstrated by R2 and R7 together, with the
fixture deviation recorded rather than glossed.

R9 ("proceed"): demonstrated — this tranche did exactly the plan that
word approved (migrate the call sites, add the determinism test), and
nothing wider.

## Assumptions carried

A1 (Q2): the backend name lives in `_ACTIVE_BACKEND_ID` plus one
`active_backend()` helper, NOT a `Config` field — chosen because rung 5
is the rung whose words require configurability, and a `Config` field
would have cost a frozen-surface touch plus an operator gate for zero
rung-3 benefit.

A2 (Q1): all ten call sites migrate, including the two read-only
diagnostic ones (`cli/main.py`'s `schools` display, `report.py`'s
report). The counter-argument — that a diagnostic should arguably read
raw log truth rather than a backend's interpretation — is recorded in
SPEC.md and PARKED.md; it only bites once rung 5 adds a second backend,
and the change is trivially reversible.

A3 (Q3): the determinism test uses the mock-endpoint `Scheduler`
pattern, not the fixture R7 names, because that fixture provably never
reaches the migrated code.

## Verdict: PASS

Every acceptance check (S1-S10), the full gate (3303 passed, 0 failed,
isolated), the root sweep (42/11, byte-identical against two independent
captures), all five `docs_verify` modes, the flake re-verification
(0 failures in 8 serial + 3 parallel runs), and all nine requirements
pass. The frozen-surface diff is empty. Rung 3 is complete across its
two tranches. Ready for `dr-deliver-change`.
