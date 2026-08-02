<!-- DR-INV-frozen-surfaces -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: src/deepreason/capabilities/state.py, src/deepreason/harness.py, src/deepreason/invariants.py, src/deepreason/run_manifest.py
Seams: 
Seams-undocumented: harness x verification, llm x manifest

# Frozen surfaces — what you may not change, and why

Read this BEFORE scoping any change. Some surfaces are not yours to change, and
discovering that after the code is written is the expensive order to discover it
in. Everything here is enforced by the gate, by an existing recorded root, or by
both — none of it is style.

## The governing principle

> The append-only record itself: fix READERS so old roots stay valid; a change
> that invalidates existing replay-valid roots is wrong by definition.

A committed run root is evidence. Evidence that changes meaning when the code
changes is not evidence. So the asymmetry is deliberate: readers may be fixed
freely, writers and formats may not.

**The operational consequence:** a change that alters what a FUTURE run may do
is ordinary work. A change that alters how a PAST run verifies is a defect,
whatever its motivation. Measure the difference rather than assuming it — the
42-root sweep below is the instrument.

## The five frozen surfaces

### 1. `capabilities/state.py` — digests and event application

Capability state digests are content addresses over proposal and work-order
maps. Changing what is digested, or the order of application, changes the digest
of every recorded capability transition.

`check: grep -q "def " src/deepreason/capabilities/state.py`

### 2. `harness.py` — event application and well-formedness

The append-only log's write path and the state materialization that replays it.
`verify_root` re-derives state from the log; if application order changes,
re-derivation of an old log produces a state its own record never held.

`check: grep -q "class Harness" src/deepreason/harness.py`

### 3. Replay-validation record formats — `invariants.py`, `verification/`

`verify_root` and the epistemic-check report. Their output shape is compared
across runs and across time; a format change silently reinterprets every stored
verdict.

`check: grep -q "def verify_root" src/deepreason/invariants.py`

### 4. Manifest schemas AND their validators — `run_manifest.py`

Not only the Pydantic models: the validators too. Admitting a value a validator
previously rejected widens what counts as a valid manifest, and every
qualification subject digest derives from the manifest.

This is a live example rather than a hypothetical. `CriticismPolicyV1.authority`
is a closed two-value Literal, and the v4 validator additionally rejects any
criticism binding whose role is not `argumentative_critic`:

`check: grep -q 'V4_CRITICISM_ROLE_UNSUPPORTED' src/deepreason/run_manifest.py`
`check: grep -rq 'V4_CRITICISM_ROLE_UNSUPPORTED\|role == .judge' experiments/2026-08-01-change-prose-can-refute/SPEC.md`

The tranche in `experiments/2026-08-01-change-prose-can-refute/` wanted
school-bound JUDGE seats. The Pydantic model permits
`role="judge"`; the validator forbids it. The change was redesigned to avoid the
manifest entirely rather than widen the validator. **Reading the model and not
the validator is the specific mistake to avoid here.**

### 5. Anything altering qualification subject digests — `qualification.py`

The qualification cache keys on a subject digest built from the manifest, the
pair inventory and the provider profile. Change what enters that digest and
every cached "qualified" verdict refers to a subject that no longer exists.

`check: grep -q "def qualification_subject_payload" src/deepreason/qualification.py`

## Where authority is allowed to live instead

When a change needs a new per-run mode, put it on `Config` (`config.py`), never
on the manifest. This is the codebase's own precedent: `ARGUMENTATIVE_AUTHORITY`
is a `Config` field, while `require_distinct_families` is a manifest field
governing the proposing side only.

`check: grep -q "ARGUMENTATIVE_AUTHORITY" src/deepreason/config.py`
`check: ! grep -q "ARGUMENTATIVE_AUTHORITY" src/deepreason/run_manifest.py`

A `Config` value costs nothing to add and is invisible to replay. A manifest
field is permanent.

## The two instruments that prove you did not break anything

### The full gate

    python -m pytest tests/ -q -n 4

`0 failed` is the only acceptable result. Never weaken an assertion to get
green — that converts a caught defect into an uncaught one. A fixture that
depended on defective behaviour may be minimally updated ONLY when the change's
design document predicted the update in advance.

Use `python -m pytest`; bare `pytest` may resolve to a tool shim that cannot see
the editable install.

### The root sweep

Before and after any change to a reader, a guard, or an authority rule, sweep
every openable run root and diff. The instrument is committed, not per-session:

    python tools/root_sweep.py <output.txt>    # ~10 min over 42 roots

`check: python -c "import ast; ast.parse(open('tools/root_sweep.py').read())"`
`check: grep -q "verify_root_report" tools/root_sweep.py`

Fields compared:

    valid, epistemic_checks_passed, len(state.att), adjudication-blindness count

No root's `valid` and no root's `att` may change. The two sweeps should compare
byte-identical. 11 of the 42 recorded roots are pre-v6 and raise
`UnsupportedRunManifestVersionError` — that is the expected baseline, not a
failure.

`check: python -c "from deepreason.verification.report import verify_root_report"`

A worked example of both instruments, including the sweep script and its output
before and after a change that widened what prose may refute, is in
`experiments/2026-08-01-change-prose-can-refute/CHECKLIST.md` steps 1, 15 and 24.

## Traps

- **Reading a model and not its validator.** Surface 4 above. Pydantic permits
  what the validator refuses; only the validator decides admissibility.
- **Assuming a guard is where you would have put it.** The prose-immunity guard
  sits in `informal/trial.py`, not in the criticism rule, because the criticism
  rule's own guard also governs whether a case is RECORDED. Widening the wrong
  one deletes scrutiny evidence for every target carrying a passing problem
  criterion — the criteria are instantiated into every candidate's interface.
- **A count call that is also a guarantee call.** `require_cross_family_judges`
  was used to obtain a seat COUNT, which meant a path could not ask how many
  seats it had without asserting a guarantee it did not use. `judge_seats()`
  now separates the two.
`check: grep -q "def judge_seats" src/deepreason/llm/adapter.py`
- **Renaming a typed reason string.** Decline reasons and Measure inputs are
  compared against recorded roots. `execution-backed` kept its spelling when its
  guard widened to `formally_backed`, because the string's meaning in old roots
  must not shift.
`check: grep -q '"execution-backed"' src/deepreason/informal/trial.py`
