# Checklist for: sub-tranche (i) — error-code catalog (S1+S2)

State: next=1 blockers=none
Map ids: `SUB-manifest.md` owns `qualification.py` (frozen surface 5)
— NOT modified this sub-tranche, cited only to confirm the boundary.
`src/deepreason/cli/main.py` and the new `src/deepreason/
error_catalog.py` are not owned by any dedicated `SUB-` document in
`docs/map/INDEX.md` (no CLI-glue subsystem doc exists; consistent with
other top-level utility modules) — no map document created or updated
this sub-tranche; noted explicitly, not an oversight.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per `dr-execute-step` invocation.

- [ ] 1. (S2) Write `src/deepreason/error_catalog.py`: an
      `ErrorCatalogEntry(BaseModel)` (fields: `code: str`,
      `summary: str`, `what_it_means: str`, `next_action: str`) and a
      `CATALOG: dict[str, ErrorCatalogEntry]` module-level constant,
      plus a `lookup(code: str) -> ErrorCatalogEntry | None` accessor.
      done-when: `python -c "from deepreason.error_catalog import
      CATALOG, lookup; assert callable(lookup)"` exits 0.
- [ ] 2. (S2) Populate `CATALOG` with the 21 `QUALIFICATION_*` codes
      from `ERROR_CENSUS.md`'s qualification-specific list, each entry
      written from that file's pasted raw text (summary = the raw
      message, reworded plain; what_it_means = one sentence of
      context; next_action = the remediation the code implies, or
      "retry `deepreason qualify`" as the safe default when no
      specific remediation is knowable).
      done-when: `python -c "from deepreason.error_catalog import
      CATALOG; assert len(CATALOG) >= 21"`.
- [ ] 3. (S2) Populate `CATALOG` with the 21 `DOCTOR_*` codes from
      `ERROR_CENSUS.md`'s doctor-code list, same entry shape.
      done-when: `python -c "from deepreason.error_catalog import
      CATALOG; assert len(CATALOG) >= 44"`.
- [ ] 4. (S2) [COMMIT] Write `tests/test_error_catalog.py`: one
      round-trip test asserting every `CATALOG` key is a
      byte-identical match to a real raise-site code string (grep
      `qualification.py` and `cli/doctor.py` for `"QUALIFICATION_`/
      `"DOCTOR_` string literals, assert the set of found strings is a
      SUPERSET of `CATALOG`'s keys — proves no silent respelling).
      done-when: `python -m pytest tests/test_error_catalog.py -q`
      passes; commit + push.
- [ ] 5. (S2) Add `deepreason explain-error CODE` subcommand: a new
      `explain_cmd = sub.add_parser("explain-error", ...)` near
      `status_cmd` (cli/main.py, alongside the other top-level
      subparsers) taking one positional `code` argument, and a
      `_cmd_explain_error(args)` function that looks up `args.code` in
      `error_catalog.lookup`, prints summary/what_it_means/next_action
      if found, or a plain "no catalog entry for CODE yet" if not
      (never an exception for an uncataloged code — the catalog is
      explicitly partial, per S2's own residue).
      done-when: `deepreason explain-error
      QUALIFICATION_TIER_UNQUALIFIED` prints non-empty output and
      exits 0; `deepreason explain-error NOT_A_REAL_CODE` exits 0 with
      the "no catalog entry" message (not a crash).
- [ ] 6. (S2) Extend `_print_qualify_failure` (cli/main.py) to consult
      `error_catalog.lookup` for the error's code (parse the leading
      `CODE:` token from `str(error)`) and print the catalog entry's
      `what_it_means`/`next_action` when found, IN ADDITION TO the
      existing raw `str(error)` line (never replacing it) — the
      existing hardcoded `QUALIFICATION_EXECUTION_FAILED`/`DOCTOR_`
      prefix-match remains as a fallback for any code not yet in the
      catalog.
      done-when: a `QualificationError` raised with a cataloged code,
      caught and passed to `_print_qualify_failure`, prints both the
      raw code/message line and the catalog's `next_action` line.
- [ ] 7. (S2) [COMMIT] Commit the CLI hook + subcommand together.
      done-when: `git push` succeeds.
- [ ] 8. (all) Subsystem test ring: `python -m pytest
      tests/test_error_catalog.py tests/test_cli*.py -q`
      done-when: 0 failed (paste the summary line).
- [ ] 9. (all) Full gate: `python -m pytest tests/ -q -n 4`
      done-when: output ends "N passed, M failed" with M equal to the
      pre-existing baseline (1: `test_bronze_report.py`, confirmed
      unrelated) — paste the full line.
- [ ] 10. (all) Map check: `python tools/docs_verify.py`
      done-when: failure count unchanged from baseline (3, all
      `CON-run-identity.md`, confirmed pre-existing/unrelated).
- [ ] 11. (all) [COMMIT] Push and confirm clean tree.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD` equals `git rev-parse origin/<branch>`.
