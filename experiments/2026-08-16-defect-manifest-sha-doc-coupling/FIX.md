# Fix: pin the configuration against the committed record, not the evidence against the working tree

Hypothesis (a) is decided (`DIAGNOSIS.md`, `REPRO.md`). The builder is
correct and is **not touched**. The two tests are fixed, and the
behaviour they misread gets a regression asserting it is CORRECT.

Guarantee restored: a test may pin a run's identity only against inputs
that test owns — the configuration half against the committed run root,
the evidence half against bytes frozen inside the test — so editing a
document the run bound as EVIDENCE moves the digest (correct) without
turning any gate red.

## Change sites (exhaustive)

- `tests/test_single_run_path.py:56-61` — `GROUNDED_MANIFEST_SHA256`
  stops being a pin against a live compile. It is re-anchored to the
  committed run root: a one-line assertion that the constant equals
  `experiments/2026-08-12-live-grounded-extension-expansion/run/run-manifest.sha256`.
  That file is inside a committed root and is immutable, so the
  historical anchor survives with zero coupling to `docs/`.
- `tests/test_single_run_path.py:299-336`
  (`test_the_grounded_tranche_config_enters_through_the_new_door`) —
  `assert summary["manifest_sha256"] == GROUNDED_MANIFEST_SHA256` is
  replaced by the property that assertion was standing in for, and that
  it stated less precisely: the compiled `run-manifest.json` equals the
  live run's committed `run-manifest.json` in **every field except
  `run_input_digest`**, and `run_input_digest` equals the digest of the
  dossier the builder just admitted. Measured, not assumed: on a clean
  tree the two manifests differ in ZERO top-level keys; with one comment
  line appended to `docs/map/SUB-adjudication.md` they differ in exactly
  `['run_input_digest']`. This is a STRONGER acceptance check than the
  sha — a mismatch names the field that drifted instead of printing two
  hex strings — and it is immune to evidence edits by construction.
- `tests/test_single_run_path.py:570-614`
  (`test_run_identity_is_deterministic_through_the_one_road`) — the two
  constant comparisons become self-comparisons:
  `assert recorded == {first["manifest_sha256"]}`, and the
  `== GROUNDED_MANIFEST_SHA256` line is deleted. R10 is "same
  configuration, same run id, through the surviving path" — compiling
  twice must agree, and the root must carry the digest **it** compiled.
  Neither half ever needed a constant, so nothing is weakened. Its
  docstring's claim that "the manifest digest is a pure function of the
  compiled configuration" is corrected in the same edit (it is a
  function of the compiled configuration AND the bound evidence).
- `tests/test_single_run_path.py` (new)
  `test_manifest_sha_sensitivity_to_bound_evidence_is_correct_behaviour`
  — the mutation-proof regression. Copies the builder's six declared
  `DOSSIER_PATHS` into `tmp_path` (frozen for the test's lifetime),
  monkeypatches `builder.DOSSIER_PATHS` onto the copies, then asserts:
  (i) two compiles over the frozen copies agree — determinism;
  (ii) appending one byte to the copy of `SUB-adjudication.md` MUST move
  `evidence_dossier_digest`, `run_input_digest` and `manifest_sha256`
  together; (iii) every other manifest field stays equal. Named so
  `-k sensitivity` selects it. Its docstring states in one sentence that
  this is identity working, with a pointer to this tranche, so the next
  reader cannot re-diagnose it as a bug.
- `docs/map/CON-run-identity.md` — new `Traps` entry (the map moves in
  the same commit): "a test that pins a manifest digest compiled from
  live repository paths is pinning documentation". Carries an executable
  `check:` that fails if the constant pin returns.
- `docs/ERRATA.md` — E32, per the tranche's stated errata checkpoint.
- `experiments/2026-08-15-change-rung3d-website-remnant/PARKED.md` —
  APPENDED addendum (never rewritten) recording the settled verdict and
  superseding that prompt's road (a).

## Regression artifact

- Must invert: `python -m pytest tests/test_single_run_path.py -q` →
  all passed with `docs/map/SUB-adjudication.md` edited (today: 2 failed).
- Must stay unchanged: `python experiments/2026-08-16-defect-manifest-sha-doc-coupling/probe_digests.py`
  → same verdict, rc=0. The builder's behaviour is not being altered.
- New condition this fix must be tested against: the sensitivity test
  above must FAIL if someone later severs the evidence→identity link
  (that is what makes it mutation-proof rather than decorative).

## Existing tests at risk

From `grep -rn "build_manifest\|_load_grounded_builder\|GROUNDED_TRANCHE" tests/`,
the grounded builder is imported by `tests/test_single_run_path.py` and
by nothing else (the only other hit is a stale `.pyc`).
`tests/test_lifecycle_operation_parity.py` and
`tests/test_controller_steering_parity.py` mention run `8e22d0431fd2b98d`
in prose only — no digest assertion, no builder import; both must keep
passing untouched (both do today: 19 passed alongside the 2 failures).
No fixture in this tranche depended on defective behaviour, so none is
weakened.

## Explicitly not changed

- `src/deepreason/run_manifest.py` — `run_input_digest` is a manifest
  field and `INV-frozen-surfaces.md` §4 makes the schema and its
  validators frozen. Hypothesis (b) is refuted, so there is nothing here
  to fix; touching it would be changing correct code to satisfy a test.
- `experiments/2026-08-12-live-grounded-extension-expansion/build_manifest.py`
  and its `DOSSIER_PATHS` — the tranche's committed record of what that
  live run actually bound. The rung3d parked prompt's road (a) ("freeze
  the dossier by copying those bytes into the tranche directory") would
  edit it, which would make the committed script disagree with the
  committed `evidence-dossier.json` it produced. Superseded; the freeze
  belongs in the test's `tmp_path`, where it costs nothing and rots
  nothing.
- The `manifest x run-identity` seam document — parked as P1.

## Estimated diff

~125 lines across 4 files (tests 75, map 15, errata 20, parked-append 15).
Class `defect`, ≤150 lines, no frozen surface touched → proceed to
`dr-implement-fix`.
