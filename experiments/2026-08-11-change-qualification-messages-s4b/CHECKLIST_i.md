# Checklist for: sub-tranche (i) — error-code catalog (S1+S2)

State: next=done blockers=none
Map ids: `SUB-manifest.md` owns `qualification.py` (frozen surface 5)
— NOT modified this sub-tranche, cited only to confirm the boundary.
`src/deepreason/cli/main.py` and the new `src/deepreason/
error_catalog.py` are not owned by any dedicated `SUB-` document in
`docs/map/INDEX.md` (no CLI-glue subsystem doc exists; consistent with
other top-level utility modules) — no map document created or updated
this sub-tranche; noted explicitly, not an oversight.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per `dr-execute-step` invocation.

- [x] 1. (S2) Write `src/deepreason/error_catalog.py`.
      DONE: file created; `lookup`/`CATALOG` import cleanly.
- [x] 2. (S2) Populate `CATALOG` with 21 `QUALIFICATION_*` codes.
      DONE: confirmed via direct source grep, not from memory.
- [x] 3. (S2) Populate `CATALOG` with 23 `DOCTOR_*` codes (SPEC/
      CHECKLIST said "the 21 DOCTOR_* codes" from the census summary;
      direct extraction from `cli/doctor.py` found 23 unique codes —
      the census's prose total was approximate, the direct count is
      authoritative). `len(CATALOG) == 44` (21+23).
      DONE: `len(CATALOG) == 44` confirmed.
- [x] 4. (S2) [COMMIT] `tests/test_error_catalog.py` — round-trip test.
      DONE: commit `287b27f5a`. First run caught a real regex bug (the
      digit "6" in `QUALIFICATION_V6_REQUIRED`/`DOCTOR_RUN_MANIFEST_
      V6_REQUIRED`/`DOCTOR_REPORT_MANIFEST_V6_REQUIRED` was excluded by
      an `[A-Z_]+` character class) — fixed to `[A-Z0-9_]+`, re-run:
      `6 passed in 0.04s`.
- [x] 5. (S2) `deepreason explain-error CODE` subcommand.
      DONE: `deepreason explain-error QUALIFICATION_TIER_UNQUALIFIED`
      prints 3 non-empty lines, exit 0; `deepreason explain-error
      NOT_A_REAL_CODE` prints the "no catalog entry yet" message, exit
      0 (not a crash).
- [x] 6. (S2) Extend `_print_qualify_failure` with the catalog hook.
      DONE, with one design correction from the checklist's original
      wording: uses the exception's own `.code` attribute directly
      (`getattr(error, "code", "")`), not a `str(error)` prefix-parse
      — `RunManifestError`'s `f"{code} at {pointer}: {message}"` format
      would break a naive colon-split for every `DOCTOR_*` code (which
      all carry a pointer). Verified directly: raw code/message line
      preserved AND `What this means:`/`Next:` lines appended.
- [x] 7. (S2) [COMMIT] CLI hook + subcommand together.
      DONE: commit `5bedb07fc`.
- [x] 8. (all) Subsystem ring: `tests/test_error_catalog.py
      tests/test_cli*.py` -> `137 passed in 87.12s`.
- [x] 9. (all) Full gate: `1 failed, 3443 passed, 7 skipped in 585.60s`
      — the 1 failure is the confirmed pre-existing
      `test_bronze_report.py` census mismatch (same as every prior gate
      run this program); +6 passed vs. the last full-program baseline
      is exactly this sub-tranche's 6 new catalog tests.
- [x] 10. (all) Map check: `docs_verify: 3 failed` — identical to
      baseline (`CON-run-identity.md` shallow-clone, unrelated).
- [x] 11. (all) Push and confirm clean tree.
      DONE: `git status --porcelain` empty, HEAD == origin HEAD
      (`5bedb07fc`).
