# Parked — rung 4 (module fingerprints)

Noticed during this tranche, deliberately NOT done here. C2 requires this
file to hold everything observed but not acted on; nothing below is a
licence to act on it in this tranche.

## Scope deliberately left for a later tranche

P1. **The other two registries.** `VerifierRegistry`
(`verification/registry.py:30`) and `WORKLOADS`
(`workloads/registry.py:30`) both pin a fingerprint at registration and
re-check on resolve, exactly as `SCHOOL_POPULATION` does (M4), and
neither writes it into the run's record. A1 was not overridden by
Amendment 4, so this tranche stamps `SCHOOL_POPULATION` only. Extending
the same payload to the other two is mechanical — `ModuleFingerprintV1`
already carries a `registry` field precisely so the list can grow
without a schema change — but it is a second decision and it is the
operator's, not mine.

## Observations about the framework, recorded per C3 (not written to
## docs/ERRATA_EXECUTOR.md — that ledger has one writer)

P2. **`DR-INV-frozen-surfaces`' `Owns:` line and its numbered surface
list disagree about scope, and this rung is where it bit.** The `Owns:`
header names four whole FILES; surface 2's own heading narrows to
"event application and well-formedness". A change touching the
`record_*` seam is inside the file and outside the named behaviour, and
the document does not say which reading governs. This tranche needed an
operator sentence (R18) to resolve what a one-line addition to the
document could resolve permanently. Evidence: `docs/map/
INV-frozen-surfaces.md` header vs. its `### 2.` heading; this tranche's
SPEC.md D6.

P3. **The `Config` precedent in `INV-frozen-surfaces` still reads as an
unqualified invitation.** "Where authority is allowed to live instead"
says "A `Config` value costs nothing to add and is invisible to replay",
and only the final `Traps` entry — 200 lines later — records that this
is false without an explicit `_versioned_source_config_data` line.
Rung 4's M1 re-measured it independently and found the damage is WIDER
than the Traps entry records: the qualification SUBJECT digest moves,
not only the manifest sha. A reader who stops at the invitation gets a
surface-5 violation. Evidence: this tranche's SPEC.md M1/M2.

P4. **`Scheduler.__init__` gates school initialization on
`config.N_SCHOOLS > 0` (`scheduler/scheduler.py:272-276`), so a run with
zero schools resolves no backend at all.** Not a defect and not fixed
here — this tranche's writer deliberately fires outside that gate (D7)
so the record is honest for such runs — but it means "which modules
built this run" and "which modules this run USED" are different
questions, and only the first is answered by rung 4.

P6. **`pytest` was absent from a fresh container and CLAUDE.md's
environment preflight does not mention it.** The preflight lists
`which deepreason || pip install -e . --break-system-packages -q` and
the gitignored `env` file, but not the test runner. A fresh container
this session had `deepreason` installed and no `pytest`, so the FIRST
full `docs_verify` reported **292 failed**, every one of them
`-> /usr/local/bin/python: No module named pytest` — a green-looking
docs failure that has nothing to do with the documents. Cost: one
misleading 292-failure report. Fixed by
`python -m pip install pytest pytest-xdist --break-system-packages`.
**CORRECTION (2026-08-04, after rung 4 was delivered): P6 and P6a below
are largely a REDISCOVERY, not a finding.** `docs/HANDOVER_2026-08-03.md`
already carried this under "Environment facts that bite" — naming
`pytest`, `pytest-xdist` AND `jsonschema` by name, and warning that a
missing `jsonschema` produces spurious `docs_verify` failures. Verified
against the tranche base (`git show 75783d11:docs/HANDOVER_2026-08-03.md`
matches "jsonschema" twice), so it predates this session and was not
added in response to it. The cost was mine: I did not read the handover's
environment-facts section before starting, and paid for it with one
292-failure report and one 2-failure report I had to diagnose from
scratch. What remains true and unrecorded elsewhere is narrower —
CLAUDE.md's own preflight still omits the test dependencies, and
`pyproject.toml`'s `dev` extra still cannot produce a runnable gate.
Recorded per C3, with the overclaim corrected rather than left standing.

P6a. **The same gap again, one layer down: `jsonschema` is imported by
the gate and declared nowhere.** After `pytest` was installed the full
`docs_verify` fell from 292 failures to 2, and both were one test —
`tests/test_schema_carries_every_prose_rule.py::
test_alias_bearing_fields_name_their_legal_values_in_the_schema` —
failing at its own `import jsonschema` line. `pyproject.toml`'s `dev`
extra is `["pytest>=8.0", "ruff>=0.4"]`: it names neither `jsonschema`
nor `pytest-xdist`, though the documented gate command (`-n 4`) cannot
run without the latter and this test cannot run without the former.
So `pip install -e ".[dev]"` does NOT produce a runnable gate. Both
installed by hand this session; the two checks then passed (5 passed).
Not fixed here — `pyproject.toml` is outside this tranche's scope and
outside every S-item — but it is a real defect in the declared
environment, and the failure it produces (a docs/test failure with no
relation to the documents or the code under change) is expensive to
read correctly.

P7. **`recorded_module_fingerprints` is absence-tolerant; opening a
pre-v6 root is not, and that is a harness property, not a reader one.**
14 of the 45 git-tracked roots raise `UnsupportedRunManifestVersionError`
before any reader runs (the documented census). Any probe or test over
"all roots" must therefore catch at open, exactly as `tools/root_sweep.py`
already does. Not a defect — recorded because the distinction is easy to
misread as the new reader failing on old roots when it is the harness
declining to open them at all.

P5. **`tools/root_sweep.py` compares four fields and no more.** Its
byte-identity guarantee is therefore exactly as strong as its field
list, which is the gap C13 exists to close. Rung 4 closes it for one new
observable (S6/S12); every observable added before C13 existed remains
unprobed. Whether any of them is worth a retrospective probe is a
question for the operator, not a defect claim.
