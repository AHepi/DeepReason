# Reproduction

Form: **record-replay** (form 1 — committed evidence only, zero live
cost, deterministic), plus a worktree mutation that tests DIAGNOSIS.md's
falsifiable prediction.

Artifact: `experiments/2026-08-05-fix-expired-census-readers/repro.py`

## Current output

    $ python experiments/2026-08-05-fix-expired-census-readers/repro.py
    committed roots (git ls-files + /log.jsonl): 47
      census: v6=30 raising=14 no-manifest=3
      openable: 33   refused: 14

    THE DEFECT -- tests/test_module_fingerprints.py:52 asserts
        recorded_module_fingerprints(harness) == ()   for EVERY committed root
      roots WITHOUT a stamp (assertion holds): 31
      roots WITH a stamp (assertion FAILS):    2
          .../rung5-dumb-alternative-backend/ab-home/runs/run-9a6be78e...  registry=school-population module_id=default
          .../rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e...  registry=school-population module_id=round-robin

    THE PROPERTIES the four instruments exist to protect -- all still TRUE:
      P-a  absence is valid on roots written before the feature : True
      P-b  presence is valid on roots written after it          : True
      P-c  some roots are expected to refuse to open            : True
      P-d  'raising' and 'no manifest' are different sets       : True

Confirms diagnosis: **yes** — every instrument is red while every claim
underneath it is true, which is the signature of a census assertion
rather than a broken guarantee. The two roots that fail the assertion
are exactly the two that SHOULD carry a stamp: they were recorded after
rung 4's writer landed, and each names the backend that built it
(`default` / `round-robin`), which is rung 5's whole result.

## The falsifiable prediction, tested

DIAGNOSIS.md predicted that deleting ONLY the line-52 assertion, with no
other change, makes both failing tests pass — which would prove the
census test is collateral damage rather than a second defect. Tested in
a clean detached worktree at `HEAD`, so the working tree was never
mutated:

    removed exactly 1 line; no other edit
    $ python -m pytest tests/test_module_fingerprints.py -q
    ....................                                     [100%]
    20 passed in 75.92s (0:01:15)

**Prediction holds.** One assertion, inside the `lru_cache`d helper both
tests share, is the entire test-side defect. The worktree was discarded;
no production or test file has been modified by this phase.

## Post-fix expectation

- `repro.py` prints the same partition (31 unstamped / 2 stamped / 14
  refused, or larger numbers as more roots are committed) and all four
  properties still `True` — the script is a measurement, not an
  assertion, so it does not change meaning after the fix.
- `python -m pytest tests/test_module_fingerprints.py -q` → `0 failed`,
  with the absence claim RESTATED (pre-feature roots read absent,
  post-feature roots read present) rather than deleted. Deleting it
  would make the suite green by asserting nothing, which
  `docs_verify --audit`'s doctrine forbids for checks and
  `dr-execute-step`'s durable-test rules forbid for tests.
- `python tools/docs_verify.py` → `0 failed`, with both census checks
  restated in a form that cannot expire: P-c for
  `SEAM-harness-x-verification`, P-d for `SEAM-manifest-x-schools`.
- No root's `verify_root` verdict moves; the 2 stamped roots stay
  exactly as committed.
