# Verification

## Criterion command + output

GOAL.md's four criteria, run verbatim against the pushed fix (`72d0d4b9c`).

    # 1. clean tree
    $ python -m pytest tests/test_single_run_path.py -q
    11 passed in 28.24s

    # 2. the reproduction, verbatim
    $ printf '\n<!-- reproduction probe -->\n' >> docs/map/SUB-adjudication.md
    $ python -m pytest tests/test_single_run_path.py -q
    11 passed in 26.92s          # before the fix: 2 failed, 8 passed
    $ git checkout docs/map/SUB-adjudication.md

    # 3. the behaviour is asserted as CORRECT, not merely tolerated
    $ python -m pytest tests/test_single_run_path.py -q -k sensitivity
    1 passed, 10 deselected in 4.68s

    # 4. boundary
    $ python -m pytest tests/ -q -n 4
    3683 passed, 7 skipped in 1044.81s (0:17:24)      # 0 failed
    $ python tools/docs_verify.py
    docs_verify [full]: 60 documents, 917 checks, 4 workers
    docs_verify: 3 failed
      -- all three CON-run-identity.md git-history checks, which require an
         unshallowed clone.  This IS the recorded baseline
         (docs/AUDIT_BASELINES.md: "3 pre-existing failures, all
         CON-run-identity.md git-history checks").  This tranche's own new
         check on that document PASSES.
    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)
    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 60 document(s)

GOAL.md wrote "-> 10 passed" for criteria 1 and 2. The count is 11: the
fix adds one test (the sensitivity regression). Recorded rather than
quietly re-stated — the criterion's substance was "0 failed under both
tree states", which holds.

## Historical roots re-checked

None, and none were required: the fix changed no reader, validator or
record format. `src/` is byte-identical to the tranche base
(`git diff ae869296d..HEAD --stat` touches only `tests/`, `docs/` and two
experiment directories). The full gate (3683 passed) covers the committed
roots the suite already exercises.

## Live attempt

None. GOAL.md demands no live proof, and the mechanism at issue is offline
compile-time identity — a provider run could not observe it.

## Verdict

**PASS.** Hypothesis (a): the builder is correct, the tests were brittle.
The digest trace that decided it, from the compiled manifest's own recorded
digests:

| tree state | evidence_dossier_digest | run_input_digest | manifest_sha256 |
|---|---|---|---|
| clean | `3155b3d7…` | `f6e488fd…` | `8e22d043…` |
| `SUB-scheduler.md` edited (NOT bound) | `3155b3d7…` | `f6e488fd…` | `8e22d043…` |
| `SUB-adjudication.md` edited (BOUND) | `4d59971c…` | `66ea2aed…` | `b92f5d47…` |
| same edit, recompiled | `4d59971c…` | `66ea2aed…` | `b92f5d47…` |

Evidence moves all three together; non-evidence moves none; a fixed input
recompiles bit-identically. Hypothesis (b) — undeclared ingestion of map
bytes — is refuted, not merely unfavoured.

## Recorded deviation: the diff budget was EXCEEDED

The mechanized gate, run before the fix commit:

    $ python tools/diff_budget.py ae869296d --ceiling 150 --paths <FIX.md's sites>
    {"total_insertions": 213, "ceiling": 150, "verdict": "EXCEEDED",
     "areas": {"tests/test_single_run_path.py": 114,
               "docs/map/CON-run-identity.md": 24,
               "docs/ERRATA.md": 38,
               "experiments/2026-08-15-change-rung3d-website-remnant/PARKED.md": 37}}

Stated plainly rather than as a footnote, per `dr-implement-fix` step 8.
The executable change is 114 lines in one test file, inside the ceiling on
its own; `src/` is untouched. The 99-line overage is entirely prose the
tranche prompt required — the errata entry (38) and the appended correction
to the rung3d parked prompt (37) — plus the map `Traps` entry (24) that
repo law requires ship in the fix's own commit. The ceiling was this
tranche's own estimate in GOAL.md/FIX.md, not an operator constraint, and
it under-priced mandated documentation. The gate did its job; the estimate
was wrong, not the work. Recorded here so the next tranche budgets prose
separately from code.

## Residue (honest)

- **The seam is still undocumented.** `manifest x run-identity` remains on
  `CON-run-identity.md`'s `Seams-undocumented:` line. Its coupling is now
  written into that document's prose and Traps with a check, which is
  enough for the next reader, but no `SEAM-manifest-x-run-identity.md`
  exists. Parked as P1 with a ready-to-send prompt.
- **`build_manifest.py` still resolves live paths.** That is correct for
  the committed live tranche it belongs to — it records what that run
  bound — but it means anyone importing that script for a NEW purpose
  inherits the same live-path behaviour. The map Traps entry is what
  warns them; no code guard exists, and none was in scope.
- **Only `docs/map/SUB-adjudication.md` was probed as the moving input.**
  The dossier's other five documents are covered by the same mechanism and
  the same test, but were not individually edited. The B-probe covers the
  negative direction with one non-dossier document, not all of them.
- **The `Verified-at:` stamp on `CON-run-identity.md` is `ae869296`**, the
  tranche base — the commit its checks were re-run against — not the fix
  commit, whose sha could not be known before it existed. Understated on
  purpose: SCHEMA.md's rule is that a stale stamp is honest and a false one
  is not.

## Errata

`docs/ERRATA.md` **E32**, landed in the fix commit `72d0d4b9c`: the
`test_run_identity_is_deterministic_through_the_one_road` docstring's claim
that the manifest digest is "a pure function of the compiled configuration"
was false — it is a function of the configuration AND the evidence that
configuration binds — and that sentence is why the same failure was
misdiagnosed twice as something else. E32 also supersedes the rung3d parked
prompt's road (a). Its cache framing is NOT corrected: that prompt already
said the cache hypothesis was refuted, and it was right; what is superseded
is its open verdict and its recommended road, corrected by an APPENDED
addendum in that file rather than a rewrite.
