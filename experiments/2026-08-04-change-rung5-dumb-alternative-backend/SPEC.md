# Spec for: rung 5 — one deliberately dumb alternative, swapped in
Traces: every item cites R/C numbers. Untraceable items are bugs.

**VERDICT: PROCEED for the offline module work; MANDATORY STOP before
the live A/B (R13).** No frozen-surface contact is expected on any part
of the offline design — forecast below, checked rather than assumed.
The stop at the end is the operator's, not a design failure.

## What was verified against the real tree this phase (C7 requires the
## named mechanism be checked for reachability, not adopted)

**M1 — the socket is five methods and a backend must supply all five.**
`SchoolPopulationBackend` (`capture/schools.py:214-227`) declares
`fingerprint`, `init_schools`, `roster`, `allocate`, `reseed`;
`SchoolPopulationRegistry.register` (`:240-247`) raises `TypeError` for a
backend missing any, refuses a duplicate name, and pins the fingerprint
at registration. So R3's "one trivial alternative" cannot be a lone
function — it is a whole backend that DIFFERS in at least one operation
(Q1 answered).

**M2 — round-robin allocation is reachable, and is genuinely dumb.**
`allocate` (`capture/schools.py:171-197`) is documented "Deterministic
function of (log, config) — no per-problem curation" and encodes three
real rules: fan-out for SEED/DISCRIMINATION/INTEGRATION triggers,
ownership-by-provenance for SUCCESSOR/REMOVE_ARBITRARINESS, and a
cross-examination floor (`_with_cross_examiner`) so ownership cannot
starve a rival school. A round-robin that ignores all three is a
faithful "deliberately dumb" alternative rather than a cosmetic one.
**C7 discharged: the named mechanism reaches the code and is adopted on
that evidence, not on the handover's say-so.**

**M2a — the dumb backend must still be DETERMINISTIC FROM THE LOG.** The
obvious round-robin — an instance counter incremented per call — would
break replay: `verify_root` opens the root twice and compares, and a
Scheduler rebuilt on reopen would restart its counter. The alternative
therefore rotates on a stable function of the problem id, not on call
order. This is the one place where "dumb" must not become "broken", and
R10's replay-validity is what would catch it.

**M3 — selection can avoid `Config` entirely, so Q2's frozen-surface
question does NOT recur.** Measured, not assumed:
- `capture/schools.py` imports neither `deepreason.config` nor `os`, and
  a map check pins the first (`DR-SEAM-schools-x-scheduler`:
  `assert 'deepreason.config' not in s`). A Config-driven selection read
  inside `schools.py` is therefore already forbidden by the map.
- `run_manifest.py::_versioned_source_config_data` scrubs exactly one
  Config key today, `ENGAGED_CRITICISM_AUTHORITY` (`run_manifest.py:2151`),
  added by rung 2 tranche 2 under explicit operator approval. A new
  `Config` field would need a second scrub line on frozen surface 4 —
  the exact touch rung 4's R15 refused to treat as transitive.
- `_ACTIVE_BACKEND_ID`'s own comment (`capture/schools.py:326-328`) names
  the sanctioned design: "A run-selected name (rung 5's 'a run configured
  with the alternative') would replace this constant's value, not the
  call sites."

So the selection is a scoped override of that constant, supplied by the
caller that starts the run. **Zero `Config` field, zero manifest field,
zero frozen-surface contact.** Q2 answered without an operator question.

**M4 — rung 4 already makes the choice VISIBLE IN THE RECORD, at no
cost to this rung.** `Scheduler.run` stamps
`schools.active_backend().fingerprint()` into the log. A run under the
alternative therefore records `module_id="round-robin"` rather than
`"default"`, and `tools/root_sweep.py`'s `modules=` column reads it.
Rung 5 needs no new observable and no new sweep probe (C12) — it is the
first consumer of rung 4's, and that is written down here rather than
left as a silent omission.

**M5 — R6's "byte-identical" cannot mean what it literally says, because
rung 4 changed the instrument (Q3).**
`tests/test_school_population_determinism.py` is C11's named instrument,
and rung 4 modified it: `_comparable_log` now EXCLUDES the
module-fingerprint stamp, and the test asserts separately that a
substitute backend's stamp DIFFERS. A rung-5 alternative is exactly such
a substitute, so "the two runs' logs match in every byte" is false by
design for any non-default backend. R6's readable meaning is therefore:
**a run that does not select the alternative is unchanged.** The spec
proves that reading and says so, rather than quietly proving the easier
one.

## Items

S1 (R1, R11): route through `dr-change-orchestrator`, phase by phase.
    accept: this tranche's artifacts exist in phase order.

S2 (R3, R4, C9, M1, M2): a second backend
`RoundRobinSchoolPopulationBackend` registered under a NEW name
(`"round-robin"`), never `"default"`. It differs in `allocate` ONLY and
delegates `init_schools`/`roster`/`reseed` to the same module functions
`DefaultSchoolPopulationBackend` delegates to, so the difference under
test is exactly one operation.
    accept: `SCHOOL_POPULATION.ids() == ("default", "round-robin")`, and
    a test asserting the registry refuses re-registering either name.

S3 (R3, M2a): the alternative's `allocate` is deterministic from
(log, config) — it rotates on a stable function of the problem id, never
on call order or instance state.
    accept: a test calling `allocate` twice on one problem returns the
    same list, and a fresh backend instance returns the same list as a
    used one.

S4 (R5, Q2, M3): a run is CONFIGURED with the alternative through a
scoped selection in `capture/schools.py` that overrides
`_ACTIVE_BACKEND_ID` for the duration of a run and restores it after —
refusing an unregistered name BEFORE mutating anything. No `Config`
field, no manifest field, no environment read.
    accept: inside the scope `active_backend()` resolves the
    alternative; outside it resolves `"default"`; an unknown name raises
    `UnknownSchoolPopulationBackend` and leaves the selection untouched;
    the selection is restored even when the body raises.

S5 (R5, R10, Q5): offline, a run configured with the alternative
COMPLETES and its root VERIFIES. Judged on typed outcomes only — the
run reaches its cycles without raising, and `verify_root` returns no
violations. Epistemic quality is explicitly NOT judged: "deliberately
dumb" predicts worse reasoning, and a completed run with poor outcomes
is a SUCCESS for this rung (Q5 answered).
    accept: a test runs a mock-endpoint `Scheduler` under the
    alternative, asserts the run completes, and asserts
    `verify_root(root)["violations"] == []`.

S6 (R5, M4): the alternative's root RECORDS that the alternative built
it — rung 4's stamp read back through `recorded_module_fingerprints`.
    accept: the offline run's root reports
    `modules[0].module_id == "round-robin"`, and a default run reports
    `"default"`.

S7 (R6, M5, C11): the DEFAULT path is unchanged. Proven in the reading
M5 establishes: a run that does not select the alternative is
byte-identical to one on the pre-change tree.
    accept: `tests/test_school_population_determinism.py` passes
    UNMODIFIED, and the full-gate count moves only by this tranche's new
    tests.

S8 (R8): full gate.
    accept: `python -m pytest tests/ -q -n 4` -> "0 failed".

S9 (R9): root sweep byte-identical.
    accept: `python tools/root_sweep.py` -> 42 rows, 11 ERROR, empty
    diff against the accepted 5-field baseline
    `6d6c3366c821d4555a8a4866c6a208c2b5d08db704e8f13c1611c7c5a74fd525`.

S10 (C8): FULL `docs_verify` before any commit touching `src/`, never
`--fast` alone; plus `--audit`.
    accept: full run 0 failed and `--audit` 0 findings, pasted.

S11 (C10): the seam's per-file `active_backend()` counts still hold.
This tranche adds NO new call site — it changes what the existing ones
resolve to — so the counts (3, 4, 3+1) must be unmoved.
    accept: `docs_verify` full passes, which runs those three checks.

S12 (C12, M4): no new typed-record observable, therefore no new sweep
probe is owed. Rung 5 is the first CONSUMER of rung 4's observable.
    accept: `git diff` adds no field to `Event`, no record type, and no
    `verify_root` finding; `tools/root_sweep.py` unchanged.

S13 (R2, R7, R13): the tranche STOPS before the live A/B and asks the
operator for credentials. No credential file is created, read, or
committed.
    accept: DELIVERY.md ends with the credential request; `git log -p`
    for this tranche contains no key material; no `env` file added.

## Assumptions (operator may override)

A1 (Q1): the alternative differs in `allocate` ONLY. Smallest change
that makes the socket's difference observable, and it matches R3's own
example. The other four operations delegate to the same module functions
the default uses, so any behavioural difference in the offline run is
attributable to allocation alone.

A2 (Q4): the alternative's offline run root is built in `tmp_path` by a
test and NOT committed. Committing it would add a 43rd root to the sweep
census and move the sweep baseline for every future tranche — the same
baseline-reset C12 exists to prevent riding along invisibly. The root is
still real evidence: the test creates it, runs it, and calls
`verify_root` on it every gate run, which is stronger than a committed
root nobody re-verifies. Durable-test rule 1 governs roots a test OPENS
as fixed evidence, not roots a test CREATES.

A3 (Q3/M5): R6 is proven in the "a run that does not select the
alternative is unchanged" reading. The literal reading is false by
rung 4's design and cannot be what R6 asks for.

A4 (Q5): "completes and its root verifies" is judged on run completion
plus empty `verify_root` violations, and epistemic quality is not
judged at all.

## Questions for operator (STOP if non-empty)

**EMPTY for the offline work.** Q1-Q5 are all resolved above by
measurement or by the smallest-reading rule, and none needs an operator
sentence before `dr-plan-steps`.

**One MANDATORY stop at the end, and it is R13's, not a design
failure:** the live A/B needs operator-supplied credentials. The tranche
delivers the offline module work, then asks. Per R2 credentials are
gitignored and are never committed.

## Out of scope (explicit)

- Rungs 6-7 — not requested; C1 forbids touching a second rung here.
- The live A/B run itself — R13 stops before it.
- Any `Config` or manifest field for backend selection — M3 shows it is
  unnecessary, and it would need a surface-4 touch this tranche has no
  authorization for.
- A third backend, or extending selection to `VerifierRegistry` /
  `WORKLOADS` — the operator confirmed those stay parked.
- Making the default allocation configurable — rung 5 adds an
  alternative, it does not parameterize the default.

## Frozen-surface contact forecast

**None expected — checked against `docs/map/INV-frozen-surfaces.md`'s
five surfaces, not assumed.** Planned target files are
`src/deepreason/capture/schools.py` and tests.

- **Surface 1** (`capabilities/state.py`): no contact.
- **Surface 2** (`harness.py` event application): no contact. The run
  records through rung 4's existing appender; nothing new is appended.
- **Surface 3** (`invariants.py`, `verification/`): no contact. No new
  finding, no new channel; `verify_root` is CALLED, not changed.
- **Surface 4** (`run_manifest.py`): no contact — M3 is the measurement
  that keeps it so. This is the surface the design was shaped to avoid.
- **Surface 5** (`qualification.py`): no contact; no `Config` field, so
  no subject digest moves and no cached qualification is invalidated.
- Frozen-adjacent `route_fingerprint` (`llm/firewall.py`): no contact.

If implementation discovers contact, C10's rule applies and the tranche
stops for the operator's words at that point.

## Budget

~60-90 lines of `src/` in `capture/schools.py` (the backend, its
`allocate`, and the scoped selection), plus ~120 lines of tests, plus a
map update to `DR-SEAM-schools-x-scheduler` and `DR-CON-schools`.
2 commits: backend+selection+tests+map, then gate/sweep evidence.
Well under the 300-line guideline. **Rung 4's estimate was 3x low; this
one is deliberately wider and will still be reconciled against the
actual at validation.**
Frozen surfaces touched: **none forecast.**
