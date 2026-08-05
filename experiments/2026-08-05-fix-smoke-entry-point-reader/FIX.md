# Fix: teach the entry-point reader about sections, and refresh the two pins it has been blocking

Guarantee restored: **the wheel smoke compares each entry-point group
against what that group is supposed to contain — console scripts to the
console-script pin, adapters to the adapter pin — so a new group can
never read as an unexpected console script, and a vanished group can
never pass unnoticed.**

## Change sites (exhaustive)

1. `scripts/wheel_smoke.py`, `inspect_wheel` — the `observed = {...}`
   comprehension and the `observed != required_entries` comparison.
   Replace the flat, section-blind parse with one that switches on
   `[group]` headers and returns a mapping, then assert
   `groups["console_scripts"] == required_entries`.
2. `scripts/wheel_smoke.py`, same function — ADD an assertion for
   `deepreason.admission.adapters` (`epub`, `pdf`), so the fix does not
   trade one blind spot for another (DIAGNOSIS.md's second finding). A
   reader taught about sections must pin both groups it knows about.
3. `scripts/wheel_smoke.py`, `EXPECTED_MCP_TOOLS` — add `amend_run` and
   `run_findings`; 18 → 20.
4. `scripts/wheel_smoke.py`, `EXPECTED_MCP_SCHEMA_SHA256` —
   `7520ea29…` → `39d73561…`.
5. `scripts/wheel_operational_smoke.py`, `EXPECTED_MCP_TOOLS` — same two
   additions. It carries its OWN copy of both pins, byte-identical to
   wheel_smoke's and identically stale.
6. `scripts/wheel_operational_smoke.py`, `EXPECTED_MCP_SCHEMA_SHA256` —
   same update.

Sites 3-6 are pin refreshes, not logic changes, and they are in scope
because the operator's instruction names them ("update any stale pins
they surface — the MCP tool set and schema sha haven't been verified
since 2026-07-26") and because sites 1-2 are what unblocks reaching
them.

**Contingency, declared rather than discovered:**
`scripts/wheel_operational_smoke.py` is still running for the first time
in this session as this is written. If it surfaces a stale pin beyond
sites 5-6, that is a NEW change site and this FIX.md is amended in its
own commit before implementation continues, per `dr-implement-fix` rule
1. It will not be quietly added.

## Why the pin refresh is not rubber-stamping

The smoke exists to catch UNINTENDED drift of the public surface, so
updating a pin to match reality is only correct if reality is intended.
Verified for both additions before accepting them:

- `amend_run` — added by `0a946726` ("Implement amendment epochs"), and
  documented in `README.md`: "Amendment is narrower still: `amend_run`
  carries exactly the CLI `amend`…".
- `run_findings` — added by `73e05bdc` ("Add findings command"), and
  documented in `README.md`'s MCP tool table: "Read a replay-derived
  findings summary…".

Nothing was REMOVED from the tool set (`only pinned: []`), so this is
purely additive drift from two documented features. The pin was last
touched at `82c73367` ("WIP: checkpoint blocked clean-wheel
qualification"), which predates both.

## Regression artifact

`experiments/2026-08-05-fix-smoke-entry-point-reader/repro.py` continues
to print both parses on real wheel bytes (it measures the two
algorithms, so it does not invert). The inversion to demonstrate is the
instrument's own exit code: `python scripts/wheel_smoke.py` from rc=1 to
rc=0.

New conditions this fix must be tested against:

1. **The sectioned parse must reject a console-script change.** Adding,
   removing or renaming a console script must still fail — the equality
   is preserved, only its input is narrowed.
2. **The adapters assertion must have teeth.** Removing the adapters
   group must now FAIL, where today it would pass. Mutation-prove it.
3. **Both smokes must be run to completion**, not merely past line 146
   — GOAL.md's criterion, and the operator's instruction.

## Existing tests at risk

`grep -rln "wheel_smoke\|wheel_operational_smoke" tests/` → one file
(named in the monitoring session's DELIVERY.md census as "the one
existing smoke-asserting test file"). Re-checked at implementation
time; the two scripts are not imported by `src/`, so no production code
path can be affected. No fixture is being updated to accommodate
defective behaviour.

## Explicitly not changed

- **`pyproject.toml`.** The packaging is correct; the operator excluded
  it and GOAL.md puts it out of scope. Removing or renaming the adapters
  group would make the smoke green by deleting a shipped capability.
- **`src/` — nothing.** The MCP facade is correct; only the pins that
  describe it were stale.
- **The duplicated pin itself.** Both scripts hold byte-identical copies
  of `EXPECTED_MCP_TOOLS` and `EXPECTED_MCP_SCHEMA_SHA256`, which is a
  latent drift hazard — two copies can disagree. De-duplicating them
  into one shared module is a refactor, not this defect, and touching a
  third file to do it would widen the tranche. PARKED.
- **A map document for `scripts/`.** None exists; the fix changes no
  `src/` file, so nothing the map describes moves. Noted in GOAL.md as
  a finding.

## Estimated diff

~35 lines across 2 files (≈25 in `wheel_smoke.py` for the parser plus
two pins, ≈10 in `wheel_operational_smoke.py` for two pins). Well under
the 150-line budget.

## Approval gate

GOAL.md class is `defect`; estimate ≤150 lines; no frozen surface — the
five surfaces are all under `src/`, and this fix touches only
`scripts/`. **Proceeds to `dr-implement-fix`**, subject to the
contingency above.
