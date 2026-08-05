# Diagnosis: four readers assert a root CENSUS where they meant to assert a PROPERTY, and a census expires every time a tranche commits a root

Primary cause: each of the four failing instruments pins an exact count
of committed run roots as the evidence for a claim that does not depend
on the count. A census is a fact with an expiry date — any tranche that
commits a run root falsifies it — while the claims underneath
(*absence of the stamp is valid on roots written before the feature*;
*some roots are expected to refuse*; *"raising" and "no manifest" are
different sets*) are invariants that survive the census moving. On the
test side the defect is a SINGLE assertion inside a shared
`functools.lru_cache`d helper, which is why one wrong claim fails two
tests. On the map side it is two `check:` lines that pin `45/28/14/3`
and `42/11/3` directly. Rung 4 shipped the stamp WRITER and the
absence assertion in the same tranche, so the first live run committed
afterwards was guaranteed to falsify it; rung 5's A/B arms were that
run.

Evidence:

- **Bisect (non-code).** `tests/test_module_fingerprints.py` reports
  `20 passed` at `a4c52c5b` ("run roots deferred until the ladder
  exits") and `2 failed, 18 passed` at `f6d41bff` ("rung 5 A/B arm A"),
  measured in a clean detached worktree. Both tests still fail at
  `2cc3fd50`, which contains none of the rung-7 work.
- **The test contradicts its own docstring (record of intent).**
  `tests/test_module_fingerprints.py:52` asserts
  `recorded_module_fingerprints(harness) == ()` for EVERY committed
  root. The module docstring states the claim as "absence of the
  fingerprint must be valid for every root recorded **before the
  feature**", and
  `test_every_committed_root_reads_as_having_no_module_fingerprints`'s
  own docstring repeats it: "absence is the VALID answer on every root
  written **before this feature**". The implemented assertion says
  something strictly stronger and time-limited: *no committed root
  anywhere carries a stamp*.
- **Recurrence, recorded in the map by the very document that failed.**
  `docs/map/SEAM-harness-x-verification.md`'s prose above its check
  already says: "(This check itself went stale-false for one day when
  the stress-triplet roots were committed without re-running it: 42/25
  → 45/28 on 2026-08-02, corrected 2026-08-03 — see `docs/ERRATA.md`.)"
  That correction updated the NUMERALS, which is what guaranteed the
  second occurrence. `docs/ERRATA.md` E3 is the first occurrence.
- **The census today, by both instruments.** git-tracked (`git ls-files`
  + `/log.jsonl`): `total=47 v6=30 raising=14 no-manifest=3`.
  Under `experiments/` only: `total=44 v6=30 raising=11 no-manifest=3`.
  The checks pin 45/28/14/3 and 42/11/3 respectively.
- **The properties survive; only the counts moved.** Measured on
  today's tree: some roots still refuse (`raising=14 > 0`), and
  `raising (11)` still differs from `raising + no-manifest (14)` under
  `experiments/` — the two claims the checks exist to protect are both
  still TRUE while both checks are RED.

Implicated code (3 sites):

- `tests/test_module_fingerprints.py:52` — the one wrong assertion,
  inside `_sweep_committed_roots`, an `lru_cache(maxsize=1)` helper
  shared by both failing tests.
- `docs/map/SEAM-harness-x-verification.md:253` — pins `len(R)==45`,
  `28/14/3`.
- `docs/map/SEAM-manifest-x-schools.md:271` — pins `len(roots)==42`,
  `(11,3)`.

Falsifiable prediction (what `dr-reproduce` must show):

    # Deleting ONLY line 52's assertion from the cached helper, changing
    # nothing else in the file, must make BOTH failing tests pass:
    python -m pytest tests/test_module_fingerprints.py -q
    -> 20 passed

If that holds, `test_the_census_of_committed_roots_is_unchanged` is
collateral damage rather than a second defect — its own three
assertions (`len(read) + len(refused) == len(_committed_roots())`,
`refused` non-empty, `len(read) > 20`) are a partition identity, an
existence claim and a FLOOR, none of which can expire — and the fix on
the test side is confined to restating one assertion.

Ruled out: **that the rung-5 roots are bad evidence to be retired,
gitignored or deleted.** Measured — both A/B arms open cleanly and
carry exactly one correct `module-fingerprints.v1` stamp naming the
backend that built them:

    arm=default      stamps=1 registry=school-population module_id=default      verify_root violations=0
    arm=round-robin  stamps=1 registry=school-population module_id=round-robin  verify_root violations=1

That is precisely the evidence rung 5's R7 needed, and the single
`round-robin` violation is the separately-parked P7. Removing or
editing them to satisfy a mis-specified reader would destroy correct
evidence — the inverse of `DR-INV-frozen-surfaces`' governing
principle ("fix READERS so old roots stay valid"). The operator's
instruction says the same thing independently.

## Second finding — PARKED, not this tranche's cause

`docs/ERRATA.md` E5 states: "The three no-manifest calibration roots
under `runs/jolt_positive_headroom_v3_1/` are outside its glob."
Measured, that association is **wrong in both directions**: the three
roots under `runs/jolt_positive_headroom_v3_1/calibration/` all RAISE
`UnsupportedRunManifestVersionError`, and the three genuinely
no-manifest roots are `experiments/bronze_flat_2026-07-13/{deepseek-v4-pro,
kimi-k2_6, qwen3_5_397b}` — inside `root_sweep.py`'s glob, not outside
it. E5's headline conclusion (the 45-root baseline is not reproducible;
the instrument scans `experiments/` only) is unaffected and still
correct; only the sentence identifying WHICH roots are the extras is
wrong. Recorded in PARKED.md; `docs/ERRATA.md` is not in this tranche's
scope, but the prose this tranche rewrites around both checks must not
repeat the false association.
